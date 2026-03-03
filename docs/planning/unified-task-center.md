# 统一任务中心技术方案

## 背景

当前系统存在两类异步任务：
1. **批处理任务**（`batch_job` 表）：批量截图识别、批量导入等
2. **单任务**（`task_record` 表）：Excel 导入、AI 聚类等

两者都可能耗时很长，用户需要一个统一的地方查看所有任务的状态和结果。

## 业界最佳实践

### GitHub Actions / GitLab CI/CD
- 统一的 Runs/Pipelines 列表展示所有任务
- 视图层统一，存储层分离
- 不同类型任务点击进入不同的详情页

### AWS Step Functions / Azure Logic Apps
- Executions 列表统一展示所有执行
- 统一的状态机模型
- 统一的任务抽象

### 关键启示
✅ **视图层统一** - 用户界面统一展示所有任务  
✅ **存储层分离** - 不同类型任务可以存储在不同表  
✅ **适配器模式** - 通过适配器转换为统一格式  
✅ **类型区分** - 通过类型字段区分不同任务，展示不同详情

---

## 核心设计

### 1. 统一任务抽象（DTO）

```python
# backend/app/task/schema/unified_task.py

from datetime import datetime
from enum import Enum
from pydantic import BaseModel


class TaskType(str, Enum):
    """任务类型"""
    # 批处理任务
    BATCH_SCREENSHOT_RECOGNITION = "batch_screenshot_recognition"
    BATCH_EXCEL_IMPORT = "batch_excel_import"
    BATCH_DATA_EXPORT = "batch_data_export"
    
    # 单任务
    EXCEL_IMPORT = "excel_import"
    CLUSTERING = "clustering"
    TOPIC_MERGE = "topic_merge"


class TaskStatus(str, Enum):
    """统一的任务状态"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class UnifiedTask(BaseModel):
    """统一的任务 DTO"""
    
    # 基础字段
    id: str
    type: TaskType
    name: str
    description: str | None = None
    
    # 状态字段
    status: TaskStatus
    progress: float  # 0-100
    
    # 时间字段
    created_time: datetime
    started_time: datetime | None = None
    completed_time: datetime | None = None
    
    # 执行信息
    celery_task_id: str | None = None
    
    # 统计信息（批处理任务专用）
    total_count: int | None = None
    completed_count: int | None = None
    failed_count: int | None = None
    pending_count: int | None = None
    
    # 结果信息（单任务专用）
    result_summary: dict | None = None
    error_message: str | None = None
    
    # 操作权限
    can_cancel: bool = False
    can_retry: bool = False
    can_view_detail: bool = True
    
    # 详情链接
    detail_url: str | None = None


class UnifiedTaskList(BaseModel):
    """统一的任务列表响应"""
    total: int
    items: list[UnifiedTask]
```

### 2. 适配器层

```python
# backend/app/task/adapter/task_adapter.py

from abc import ABC, abstractmethod
from backend.app.batch.model.batch_job import BatchJob
from backend.app.task.model.task_record import TaskRecord
from backend.app.task.schema.unified_task import UnifiedTask, TaskType, TaskStatus


class TaskAdapter(ABC):
    """任务适配器基类"""
    
    @abstractmethod
    def to_unified_task(self, source: any) -> UnifiedTask:
        """转换为统一的任务格式"""
        pass


class BatchJobAdapter(TaskAdapter):
    """批处理任务适配器"""
    
    def to_unified_task(self, batch_job: BatchJob) -> UnifiedTask:
        # 映射任务类型
        type_mapping = {
            "screenshot_recognition": TaskType.BATCH_SCREENSHOT_RECOGNITION,
            "excel_import": TaskType.BATCH_EXCEL_IMPORT,
            "data_export": TaskType.BATCH_DATA_EXPORT,
        }
        
        # 映射状态
        status_mapping = {
            "pending": TaskStatus.PENDING,
            "processing": TaskStatus.PROCESSING,
            "completed": TaskStatus.COMPLETED,
            "failed": TaskStatus.FAILED,
            "cancelled": TaskStatus.CANCELLED,
        }
        
        return UnifiedTask(
            id=batch_job.id,
            type=type_mapping.get(batch_job.task_type, batch_job.task_type),
            name=batch_job.name or f"批处理任务 - {batch_job.task_type}",
            description=batch_job.description,
            status=status_mapping[batch_job.status],
            progress=batch_job.progress if hasattr(batch_job, 'progress') else self._calculate_progress(batch_job),
            created_time=batch_job.created_time,
            started_time=batch_job.started_time,
            completed_time=batch_job.completed_time,
            celery_task_id=batch_job.celery_task_id,
            total_count=batch_job.total_count,
            completed_count=batch_job.completed_count,
            failed_count=batch_job.failed_count,
            pending_count=batch_job.pending_count,
            can_cancel=batch_job.status in ["pending", "processing"],
            can_retry=batch_job.status == "failed" or batch_job.failed_count > 0,
            can_view_detail=True,
            detail_url=f"/app/tasks/batch/{batch_job.id}",
        )
    
    def _calculate_progress(self, batch_job: BatchJob) -> float:
        """计算进度百分比"""
        if batch_job.total_count == 0:
            return 0
        return (batch_job.completed_count + batch_job.failed_count) / batch_job.total_count * 100


class TaskRecordAdapter(TaskAdapter):
    """单任务适配器"""
    
    def to_unified_task(self, task_record: TaskRecord) -> UnifiedTask:
        # 映射任务类型
        type_mapping = {
            "excel_import": TaskType.EXCEL_IMPORT,
            "clustering": TaskType.CLUSTERING,
            "topic_merge": TaskType.TOPIC_MERGE,
        }
        
        # 映射状态
        status_mapping = {
            "pending": TaskStatus.PENDING,
            "running": TaskStatus.PROCESSING,
            "success": TaskStatus.COMPLETED,
            "failure": TaskStatus.FAILED,
            "revoked": TaskStatus.CANCELLED,
        }
        
        # 计算进度
        progress = self._calculate_progress(task_record)
        
        return UnifiedTask(
            id=task_record.id,
            type=type_mapping.get(task_record.task_name, task_record.task_name),
            name=self._get_task_display_name(task_record),
            description=task_record.task_args.get('description') if task_record.task_args else None,
            status=status_mapping.get(task_record.status, TaskStatus.PENDING),
            progress=progress,
            created_time=task_record.created_time,
            started_time=task_record.started_time,
            completed_time=task_record.updated_time if task_record.status in ["success", "failure"] else None,
            celery_task_id=task_record.task_id,
            result_summary=task_record.result if task_record.result else None,
            error_message=task_record.traceback if task_record.status == "failure" else None,
            can_cancel=task_record.status in ["pending", "running"],
            can_retry=task_record.status == "failure",
            can_view_detail=True,
            detail_url=f"/app/tasks/single/{task_record.id}",
        )
    
    def _calculate_progress(self, task_record: TaskRecord) -> float:
        """计算单任务进度"""
        if task_record.status == "success":
            return 100
        elif task_record.status == "failure":
            return 100
        elif task_record.status == "running":
            # 如果有进度信息，从 result 中读取
            if task_record.result and 'progress' in task_record.result:
                return task_record.result['progress']
            return 50  # 默认进行中显示 50%
        return 0
    
    def _get_task_display_name(self, task_record: TaskRecord) -> str:
        """获取任务显示名称"""
        name_mapping = {
            "excel_import": "Excel 导入",
            "clustering": "AI 聚类",
            "topic_merge": "需求合并",
        }
        
        base_name = name_mapping.get(task_record.task_name, task_record.task_name)
        
        # 如果有额外信息，附加到名称后
        if task_record.task_args and 'filename' in task_record.task_args:
            return f"{base_name} - {task_record.task_args['filename']}"
        
        return base_name
```

### 3. 统一任务服务

```python
# backend/app/task/service/unified_task_service.py

from sqlalchemy import select, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.batch.model.batch_job import BatchJob
from backend.app.task.model.task_record import TaskRecord
from backend.app.task.adapter.task_adapter import BatchJobAdapter, TaskRecordAdapter
from backend.app.task.schema.unified_task import UnifiedTask, UnifiedTaskList, TaskType, TaskStatus


async def get_unified_tasks(
    db: AsyncSession,
    tenant_id: str,
    task_type: TaskType | None = None,
    status: TaskStatus | None = None,
    page: int = 1,
    page_size: int = 20,
) -> UnifiedTaskList:
    """获取统一的任务列表（聚合 batch_job 和 task_record）"""
    
    batch_adapter = BatchJobAdapter()
    task_adapter = TaskRecordAdapter()
    
    # 收集所有任务
    all_tasks: list[UnifiedTask] = []
    
    # 1. 查询批处理任务
    batch_query = select(BatchJob).where(BatchJob.tenant_id == tenant_id)
    
    # 类型过滤
    if task_type and task_type.value.startswith("batch_"):
        # 批处理任务类型映射
        batch_type_mapping = {
            TaskType.BATCH_SCREENSHOT_RECOGNITION: "screenshot_recognition",
            TaskType.BATCH_EXCEL_IMPORT: "excel_import",
            TaskType.BATCH_DATA_EXPORT: "data_export",
        }
        if task_type in batch_type_mapping:
            batch_query = batch_query.where(BatchJob.task_type == batch_type_mapping[task_type])
    
    # 状态过滤
    if status:
        status_mapping = {
            TaskStatus.PENDING: "pending",
            TaskStatus.PROCESSING: "processing",
            TaskStatus.COMPLETED: "completed",
            TaskStatus.FAILED: "failed",
            TaskStatus.CANCELLED: "cancelled",
        }
        batch_query = batch_query.where(BatchJob.status == status_mapping[status])
    
    batch_query = batch_query.order_by(desc(BatchJob.created_time))
    
    batch_result = await db.execute(batch_query)
    batch_jobs = batch_result.scalars().all()
    
    for batch_job in batch_jobs:
        all_tasks.append(batch_adapter.to_unified_task(batch_job))
    
    # 2. 查询单任务
    task_query = select(TaskRecord).where(TaskRecord.tenant_id == tenant_id)
    
    # 类型过滤
    if task_type and not task_type.value.startswith("batch_"):
        task_name_mapping = {
            TaskType.EXCEL_IMPORT: "excel_import",
            TaskType.CLUSTERING: "clustering",
            TaskType.TOPIC_MERGE: "topic_merge",
        }
        if task_type in task_name_mapping:
            task_query = task_query.where(TaskRecord.task_name == task_name_mapping[task_type])
    
    # 状态过滤
    if status:
        status_mapping = {
            TaskStatus.PENDING: "pending",
            TaskStatus.PROCESSING: "running",
            TaskStatus.COMPLETED: "success",
            TaskStatus.FAILED: "failure",
            TaskStatus.CANCELLED: "revoked",
        }
        task_query = task_query.where(TaskRecord.status == status_mapping[status])
    
    task_query = task_query.order_by(desc(TaskRecord.created_time))
    
    task_result = await db.execute(task_query)
    task_records = task_result.scalars().all()
    
    for task_record in task_records:
        all_tasks.append(task_adapter.to_unified_task(task_record))
    
    # 3. 按创建时间排序
    all_tasks.sort(key=lambda t: t.created_time, reverse=True)
    
    # 4. 分页
    total = len(all_tasks)
    start = (page - 1) * page_size
    end = start + page_size
    items = all_tasks[start:end]
    
    return UnifiedTaskList(total=total, items=items)


async def get_unified_task_by_id(
    db: AsyncSession,
    task_id: str,
) -> UnifiedTask | None:
    """根据 ID 获取统一的任务详情"""
    
    # 先尝试从 batch_job 查询
    batch_job = await db.get(BatchJob, task_id)
    if batch_job:
        adapter = BatchJobAdapter()
        return adapter.to_unified_task(batch_job)
    
    # 再尝试从 task_record 查询
    task_record = await db.get(TaskRecord, task_id)
    if task_record:
        adapter = TaskRecordAdapter()
        return adapter.to_unified_task(task_record)
    
    return None


async def cancel_unified_task(
    db: AsyncSession,
    task_id: str,
) -> bool:
    """取消统一任务"""
    
    # 尝试取消批处理任务
    batch_job = await db.get(BatchJob, task_id)
    if batch_job:
        from backend.app.batch.service.batch_service import cancel_batch_job
        await cancel_batch_job(db, task_id)
        return True
    
    # 尝试取消单任务
    task_record = await db.get(TaskRecord, task_id)
    if task_record:
        from backend.app.task.celery import celery_app
        celery_app.control.revoke(task_record.task_id, terminate=True)
        task_record.status = "revoked"
        await db.flush()
        return True
    
    return False


async def retry_unified_task(
    db: AsyncSession,
    task_id: str,
) -> str | None:
    """重试统一任务"""
    
    # 尝试重试批处理任务
    batch_job = await db.get(BatchJob, task_id)
    if batch_job:
        from backend.app.batch.service.batch_service import enqueue_batch_job
        celery_task_id = await enqueue_batch_job(task_id)
        return celery_task_id
    
    # 尝试重试单任务
    task_record = await db.get(TaskRecord, task_id)
    if task_record:
        # 根据任务类型重新提交
        from backend.app.task.tasks import submit_task
        new_task_id = await submit_task(task_record.task_name, task_record.task_args)
        return new_task_id
    
    return None
```

### 4. 统一任务 API

```python
# backend/app/task/api/v1/unified_tasks.py

from fastapi import APIRouter, HTTPException
from backend.database.db import CurrentSession
from backend.common.security.jwt import CurrentTenantId
from backend.common.response.response_schema import response_base
from backend.app.task.service.unified_task_service import (
    get_unified_tasks,
    get_unified_task_by_id,
    cancel_unified_task,
    retry_unified_task,
)
from backend.app.task.schema.unified_task import TaskType, TaskStatus

router = APIRouter(prefix="/tasks", tags=["统一任务中心"])


@router.get("", summary="获取任务列表")
async def list_tasks(
    db: CurrentSession,
    tenant_id: str = CurrentTenantId,
    task_type: TaskType | None = None,
    status: TaskStatus | None = None,
    page: int = 1,
    page_size: int = 20,
):
    """
    获取所有任务列表（批处理 + 单任务）
    
    - 统一展示批处理任务和单任务
    - 支持按类型和状态筛选
    - 按创建时间倒序排列
    """
    
    tasks = await get_unified_tasks(
        db=db,
        tenant_id=tenant_id,
        task_type=task_type,
        status=status,
        page=page,
        page_size=page_size,
    )
    
    return response_base.success(data=tasks.model_dump())


@router.get("/{task_id}", summary="获取任务详情")
async def get_task(
    task_id: str,
    db: CurrentSession,
):
    """获取任务详情（自动识别批处理任务或单任务）"""
    
    task = await get_unified_task_by_id(db, task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return response_base.success(data=task.model_dump())


@router.post("/{task_id}/cancel", summary="取消任务")
async def cancel_task(
    task_id: str,
    db: CurrentSession,
):
    """取消任务（支持批处理任务和单任务）"""
    
    success = await cancel_unified_task(db, task_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Task not found or cannot be cancelled")
    
    return response_base.success()


@router.post("/{task_id}/retry", summary="重试任务")
async def retry_task(
    task_id: str,
    db: CurrentSession,
):
    """重试失败的任务（支持批处理任务和单任务）"""
    
    new_task_id = await retry_unified_task(db, task_id)
    
    if not new_task_id:
        raise HTTPException(status_code=404, detail="Task not found or cannot be retried")
    
    return response_base.success(data={"new_task_id": new_task_id})
```

### 5. 前端统一任务中心

**关键改动：**
1. 页面标题：**"批处理任务" → "任务中心"**
2. 任务类型：支持批处理 + 单任务
3. 详情链接：根据任务类型跳转到不同的详情页

```typescript
// 任务类型配置
const taskTypeConfig = {
  // 批处理任务
  batch_screenshot_recognition: {
    name: '批量截图识别',
    icon: 'lucide:images',
    color: 'blue',
  },
  batch_excel_import: {
    name: '批量 Excel 导入',
    icon: 'lucide:file-spreadsheet',
    color: 'green',
  },
  batch_data_export: {
    name: '批量数据导出',
    icon: 'lucide:download',
    color: 'purple',
  },
  
  // 单任务
  excel_import: {
    name: 'Excel 导入',
    icon: 'lucide:file-spreadsheet',
    color: 'green',
  },
  clustering: {
    name: 'AI 聚类',
    icon: 'lucide:sparkles',
    color: 'orange',
  },
  topic_merge: {
    name: '需求合并',
    icon: 'lucide:git-merge',
    color: 'cyan',
  },
};

// 详情链接逻辑
function getDetailUrl(task: UnifiedTask): string {
  if (task.type.startsWith('batch_')) {
    return `/app/tasks/batch/${task.id}`;
  } else {
    return `/app/tasks/single/${task.id}`;
  }
}
```

---

## 实施步骤

### Phase 1: 后端适配层（1-2天）
1. ✅ 创建统一任务 DTO schema
2. ✅ 实现 BatchJobAdapter
3. ✅ 实现 TaskRecordAdapter
4. ✅ 实现 unified_task_service
5. ✅ 实现统一任务 API

### Phase 2: 前端统一界面（1天）
1. ✅ 修改"批处理任务"页面为"任务中心"
2. ✅ 调用统一任务 API
3. ✅ 支持不同类型任务的图标和样式
4. ✅ 根据任务类型跳转不同详情页

### Phase 3: 单任务详情页（1天）
1. ✅ 创建单任务详情页组件
2. ✅ 展示任务参数、结果、错误信息
3. ✅ 支持取消和重试操作

### Phase 4: 测试和优化（0.5天）
1. ✅ 测试批处理任务展示
2. ✅ 测试单任务展示
3. ✅ 测试筛选和分页
4. ✅ 性能优化（如有必要，添加缓存）

---

## 优势总结

### ✅ 对用户友好
- 一个地方查看所有任务
- 统一的交互体验
- 清晰的任务分类

### ✅ 对开发者友好
- 零破坏性修改
- 易于扩展新任务类型
- 符合开闭原则

### ✅ 符合 Linus 哲学
- **数据结构驱动**：统一的 DTO
- **消除特殊情况**：适配器统一转换
- **简洁实用**：视图层聚合，存储层不变

### ✅ 业界最佳实践
- 参考 GitHub Actions / AWS Step Functions
- 视图层统一，存储层分离
- 适配器模式 + 统一接口

---

## 未来扩展

### 新增任务类型只需：
1. 在 `TaskType` 枚举中添加新类型
2. 实现对应的 Adapter（或复用现有 Adapter）
3. 在前端 `taskTypeConfig` 中添加配置
4. **无需修改任务中心页面代码**

### 可能的扩展：
- 任务依赖关系（DAG）
- 任务调度（定时任务）
- 任务模板（快速创建常用任务）
- 任务统计和分析

---

## 结论

**推荐方案：视图层统一 + 适配器模式**

这是 Linus 会认可的设计：
- 简单：用户看到统一的任务列表
- 通用：支持所有异步任务
- 可扩展：新增任务类型无需改页面
- 零破坏：不影响现有代码

> "这才是好的设计：一个地方解决问题，而不是到处打补丁。" - Linus Torvalds
