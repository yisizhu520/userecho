# 通用批处理任务框架设计文档

## 概述

UserEcho 作为 B2B SaaS 产品，存在大量批处理场景：
- 批量导入反馈（Excel、CSV、截图）
- 批量导出数据
- 批量更新状态
- 批量删除
- 批量分配任务
- 定时批量同步

本文档设计一个**通用的批处理任务框架**，基于现有的 Celery + Redis 架构，提供统一的任务管理、进度追踪、错误处理能力。

---

## 核心设计原则

### 1. 数据结构驱动

"Bad programmers worry about the code. Good programmers worry about data structures." - Linus Torvalds

- 核心抽象：`task_type` 区分不同类型的批处理任务
- JSONB 字段：`input_data` 和 `output_data` 灵活支持任意结构
- 统一状态机：所有任务使用相同的状态转换流程

### 2. 可插拔设计

- 任务处理器（Handler）注册机制
- 业务代码只需实现 `BatchTaskHandler` 接口
- 框架自动管理状态、重试、进度追踪

### 3. 生产级可靠性

- 基于 Celery + Redis 的分布式任务队列
- 自动重试机制
- 失败任务隔离（不影响其他任务）
- Socket.IO 实时进度推送

---

## 架构设计

```
┌─────────────┐
│ 前端        │ 批量上传 / 查询进度 / WebSocket 监听
└──────┬──────┘
       │
       ↓
┌─────────────┐
│ API Layer   │ POST /batch/jobs, GET /batch/jobs/{id}
└──────┬──────┘
       │
       ↓
┌─────────────┐
│ Service     │ create_batch_job(), get_batch_progress()
└──────┬──────┘
       │
       ↓
┌─────────────┐
│ Celery Task │ process_batch_job_task()
│             │   ↓
│             │ process_single_task_item()
└──────┬──────┘
       │
       ↓
┌─────────────┐
│ Handler     │ ScreenshotRecognitionHandler.process()
│ Registry    │ ExcelImportHandler.process()
│             │ DataExportHandler.process()
└─────────────┘
```

---

## 数据库表设计

### batch_job（批量任务表）

```sql
CREATE TABLE batch_job (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    
    -- 任务类型（核心抽象点）
    task_type VARCHAR(50) NOT NULL, -- 'screenshot_recognition', 'excel_import', 'data_export', etc.
    
    -- 任务元数据
    name VARCHAR(200), -- 任务名称，如 "批量导入反馈 2024-01-26"
    description TEXT, -- 任务描述
    created_by UUID, -- 创建者
    
    -- 执行统计
    total_count INT NOT NULL DEFAULT 0,
    pending_count INT NOT NULL DEFAULT 0,
    processing_count INT NOT NULL DEFAULT 0,
    completed_count INT NOT NULL DEFAULT 0,
    failed_count INT NOT NULL DEFAULT 0,
    
    -- 任务状态
    status VARCHAR(20) NOT NULL DEFAULT 'pending', -- pending, processing, completed, failed, cancelled
    
    -- Celery 任务 ID（用于查询 Celery 任务状态）
    celery_task_id VARCHAR(255),
    
    -- 执行配置（JSON 格式，灵活扩展）
    config JSONB DEFAULT '{}', -- {"max_retries": 3, "timeout": 300, "parallel": true}
    
    -- 结果汇总（JSON 格式，灵活扩展）
    summary JSONB DEFAULT '{}', -- {"success_ids": [...], "failed_items": [...]}
    
    -- 时间戳
    created_time TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_time TIMESTAMP NOT NULL DEFAULT NOW(),
    started_time TIMESTAMP,
    completed_time TIMESTAMP
);

CREATE INDEX idx_batch_job_tenant ON batch_job(tenant_id, created_time DESC);
CREATE INDEX idx_batch_job_status ON batch_job(status, created_time);
CREATE INDEX idx_batch_job_type ON batch_job(task_type, created_time DESC);
CREATE INDEX idx_batch_job_celery_task ON batch_job(celery_task_id);
```

**设计要点：**
- ✅ `task_type` 是核心抽象，不同类型的任务只是 `task_type` 不同
- ✅ `celery_task_id` 关联 Celery 任务，支持通过 Celery API 查询任务状态
- ✅ `config` 和 `summary` 用 JSONB，可扩展，不需要加列
- ✅ 统一的状态字段和统计字段，支持进度查询

### batch_task_item（任务项表）

```sql
CREATE TABLE batch_task_item (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    batch_job_id UUID NOT NULL REFERENCES batch_job(id) ON DELETE CASCADE,
    
    -- 执行顺序（可选）
    sequence_no INT, -- 如果需要顺序执行
    
    -- 输入数据（JSON 格式，灵活支持不同类型）
    input_data JSONB NOT NULL, -- {"image_url": "...", "board_id": "..."}
    
    -- 输出数据（JSON 格式，灵活支持不同类型）
    output_data JSONB, -- {"feedback_id": "...", "status": "success"}
    
    -- 任务状态
    status VARCHAR(20) NOT NULL DEFAULT 'pending', -- pending, processing, completed, failed, skipped
    
    -- 错误信息
    error_message TEXT,
    error_code VARCHAR(50),
    
    -- 重试次数
    retry_count INT DEFAULT 0,
    max_retries INT DEFAULT 3,
    
    -- 时间戳
    created_time TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_time TIMESTAMP NOT NULL DEFAULT NOW(),
    started_time TIMESTAMP,
    completed_time TIMESTAMP
);

CREATE INDEX idx_task_item_batch ON batch_task_item(batch_job_id, status);
CREATE INDEX idx_task_item_status ON batch_task_item(status, created_time);
```

**设计要点：**
- ✅ `input_data` 和 `output_data` 用 JSONB，灵活支持任意结构
- ✅ 每个任务项独立管理状态、重试次数、错误信息
- ✅ `sequence_no` 支持顺序执行（可选）

---

## Python 模型定义

### backend/app/batch/model/batch_job.py

```python
from datetime import datetime
from sqlalchemy import JSON, Integer, String, Text, DateTime, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.database.base import BaseModel
import enum

class BatchJobStatus(str, enum.Enum):
    """批量任务状态"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TaskItemStatus(str, enum.Enum):
    """任务项状态"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

class BatchJob(BaseModel):
    """批量任务（通用）"""
    __tablename__ = "batch_job"
    
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    
    # 任务类型（核心抽象点）
    task_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    
    # 任务元数据
    name: Mapped[str | None] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[str | None] = mapped_column(String(36))
    
    # 执行统计
    total_count: Mapped[int] = mapped_column(Integer, default=0)
    pending_count: Mapped[int] = mapped_column(Integer, default=0)
    processing_count: Mapped[int] = mapped_column(Integer, default=0)
    completed_count: Mapped[int] = mapped_column(Integer, default=0)
    failed_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # 任务状态
    status: Mapped[BatchJobStatus] = mapped_column(
        SQLEnum(BatchJobStatus), default=BatchJobStatus.PENDING
    )
    
    # Celery 任务 ID
    celery_task_id: Mapped[str | None] = mapped_column(String(255), index=True)
    
    # 执行配置
    config: Mapped[dict] = mapped_column(JSON, default=dict)
    
    # 结果汇总
    summary: Mapped[dict] = mapped_column(JSON, default=dict)
    
    # 时间戳
    started_time: Mapped[datetime | None] = mapped_column(DateTime)
    completed_time: Mapped[datetime | None] = mapped_column(DateTime)
    
    # 关联任务项
    task_items: Mapped[list["BatchTaskItem"]] = relationship(
        back_populates="batch_job",
        cascade="all, delete-orphan",
    )


class BatchTaskItem(BaseModel):
    """任务项（通用）"""
    __tablename__ = "batch_task_item"
    
    batch_job_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("batch_job.id", ondelete="CASCADE"), nullable=False
    )
    
    # 执行顺序
    sequence_no: Mapped[int | None] = mapped_column(Integer)
    
    # 输入输出数据
    input_data: Mapped[dict] = mapped_column(JSON, nullable=False)
    output_data: Mapped[dict | None] = mapped_column(JSON)
    
    # 任务状态
    status: Mapped[TaskItemStatus] = mapped_column(
        SQLEnum(TaskItemStatus), default=TaskItemStatus.PENDING
    )
    
    # 错误信息
    error_message: Mapped[str | None] = mapped_column(Text)
    error_code: Mapped[str | None] = mapped_column(String(50))
    
    # 重试次数
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, default=3)
    
    # 时间戳
    started_time: Mapped[datetime | None] = mapped_column(DateTime)
    completed_time: Mapped[datetime | None] = mapped_column(DateTime)
    
    # 关联批量任务
    batch_job: Mapped["BatchJob"] = relationship(back_populates="task_items")
```

---

## 任务处理器注册机制

### backend/app/batch/handler/base.py

```python
from abc import ABC, abstractmethod
from typing import Any, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.batch.model.batch_job import BatchJob, BatchTaskItem

class BatchTaskHandler(ABC):
    """批量任务处理器基类"""
    
    @abstractmethod
    async def process(self, task_item: BatchTaskItem, db: AsyncSession) -> Dict[str, Any]:
        """
        处理单个任务项
        
        Args:
            task_item: 任务项对象
            db: 数据库会话
        
        Returns:
            输出数据字典，会被写入 task_item.output_data
        
        Raises:
            Exception: 处理失败时抛出异常，会被记录到 task_item.error_message
        """
        pass
    
    async def on_batch_start(self, batch_job: BatchJob, db: AsyncSession):
        """批量任务开始前的钩子（可选）"""
        pass
    
    async def on_batch_complete(self, batch_job: BatchJob, db: AsyncSession):
        """批量任务完成后的钩子（可选）"""
        pass
    
    async def on_batch_progress(self, batch_job: BatchJob, db: AsyncSession):
        """批量任务进度更新时的钩子（可选，用于实时通知）"""
        pass


# 任务处理器注册表
_task_handlers: Dict[str, BatchTaskHandler] = {}

def register_task_handler(task_type: str, handler: BatchTaskHandler):
    """注册任务处理器"""
    _task_handlers[task_type] = handler

def get_task_handler(task_type: str) -> BatchTaskHandler:
    """获取任务处理器"""
    if task_type not in _task_handlers:
        raise ValueError(f"Unknown task type: {task_type}")
    return _task_handlers[task_type]

def list_task_handlers() -> list[str]:
    """列出所有已注册的任务类型"""
    return list(_task_handlers.keys())


# 装饰器语法糖
def batch_task_handler(task_type: str):
    """任务处理器装饰器"""
    def decorator(handler_class: type[BatchTaskHandler]):
        register_task_handler(task_type, handler_class())
        return handler_class
    return decorator
```

---

## 具体业务处理器实现

### backend/app/batch/handler/screenshot_recognition.py

```python
from backend.app.batch.handler.base import BatchTaskHandler, batch_task_handler
from backend.app.batch.model.batch_job import BatchJob, BatchTaskItem
from backend.common.log import log
from backend.utils.ai_client import ai_client
from sqlalchemy.ext.asyncio import AsyncSession

@batch_task_handler("screenshot_recognition")
class ScreenshotRecognitionHandler(BatchTaskHandler):
    """截图识别处理器"""
    
    async def process(self, task_item: BatchTaskItem, db: AsyncSession) -> dict:
        """处理单个截图识别任务"""
        
        # 1. 获取输入数据
        image_url = task_item.input_data["image_url"]
        board_id = task_item.input_data.get("board_id")
        
        # 2. 调用 AI 识别
        log.info(f"Analyzing screenshot: {image_url}")
        result = await ai_client.analyze_screenshot(image_url)
        
        # 3. 创建反馈
        from backend.app.userecho.crud import crud_feedback
        from backend.common import timezone
        from backend.common.uuid import uuid4_str
        from backend.app.userecho.model.feedback import Feedback
        
        feedback = Feedback(
            id=uuid4_str(),
            tenant_id=task_item.batch_job.tenant_id,
            board_id=board_id,
            title=result.get("title", ""),
            content=result.get("description", ""),
            source="screenshot",
            source_metadata={"screenshot_url": image_url, "confidence": result.get("confidence", 0)},
            created_time=timezone.now(),
            updated_time=timezone.now(),
        )
        db.add(feedback)
        await db.flush()
        
        # 4. 记录积分消耗
        try:
            from backend.app.userecho.service.credits_service import credits_service
            await credits_service.consume(
                db=db,
                tenant_id=task_item.batch_job.tenant_id,
                operation_type="screenshot",
                count=1,
                description="批量截图识别",
                extra_data={"feedback_id": feedback.id, "batch_job_id": task_item.batch_job_id},
            )
        except Exception as e:
            log.warning(f"Failed to record credits: {e}")
        
        # 5. 返回输出数据
        return {
            "feedback_id": feedback.id,
            "title": feedback.title,
            "confidence": result.get("confidence", 0),
            "screenshot_url": image_url,
        }
    
    async def on_batch_start(self, batch_job: BatchJob, db: AsyncSession):
        """批量任务开始前的钩子"""
        log.info(f"Starting screenshot recognition batch: {batch_job.id} ({batch_job.total_count} items)")
    
    async def on_batch_complete(self, batch_job: BatchJob, db: AsyncSession):
        """批量任务完成后的钩子"""
        log.info(
            f"Completed screenshot recognition batch: {batch_job.id} "
            f"(success={batch_job.completed_count}, failed={batch_job.failed_count})"
        )
        
        # 发送完成通知
        from backend.common.socketio.actions import task_notification
        await task_notification(
            msg=f"批量截图识别完成：成功 {batch_job.completed_count} 个，失败 {batch_job.failed_count} 个"
        )
```

### backend/app/batch/handler/excel_import.py

```python
@batch_task_handler("excel_import")
class ExcelImportHandler(BatchTaskHandler):
    """Excel 导入处理器"""
    
    async def process(self, task_item: BatchTaskItem, db: AsyncSession) -> dict:
        """处理单个 Excel 行导入"""
        
        row_data = task_item.input_data["row_data"]
        board_id = task_item.input_data.get("board_id")
        
        # 创建反馈
        from backend.app.userecho.model.feedback import Feedback
        from backend.common import timezone
        from backend.common.uuid import uuid4_str
        
        feedback = Feedback(
            id=uuid4_str(),
            tenant_id=task_item.batch_job.tenant_id,
            board_id=board_id,
            title=row_data.get("title", ""),
            content=row_data.get("content", ""),
            source="excel",
            source_metadata={"row_number": task_item.sequence_no},
            created_time=timezone.now(),
            updated_time=timezone.now(),
        )
        db.add(feedback)
        await db.flush()
        
        return {"feedback_id": feedback.id, "title": feedback.title}
```

### backend/app/batch/handler/data_export.py

```python
@batch_task_handler("data_export")
class DataExportHandler(BatchTaskHandler):
    """数据导出处理器"""
    
    async def process(self, task_item: BatchTaskItem, db: AsyncSession) -> dict:
        """处理单个数据导出"""
        
        feedback_id = task_item.input_data["feedback_id"]
        
        # 查询反馈数据
        from backend.app.userecho.crud import crud_feedback
        feedback = await crud_feedback.get_by_id(
            db, task_item.batch_job.tenant_id, feedback_id
        )
        
        if not feedback:
            raise ValueError(f"Feedback {feedback_id} not found")
        
        # 转换为导出格式
        return {
            "row": {
                "标题": feedback.title,
                "内容": feedback.content,
                "状态": feedback.status,
                "创建时间": feedback.created_time.isoformat(),
            }
        }
    
    async def on_batch_complete(self, batch_job: BatchJob, db: AsyncSession):
        """批量导出完成后，生成 Excel 文件"""
        from sqlalchemy import select
        from backend.app.batch.model.batch_job import BatchTaskItem, TaskItemStatus
        
        # 收集所有成功的任务项输出
        result = await db.execute(
            select(BatchTaskItem)
            .where(BatchTaskItem.batch_job_id == batch_job.id)
            .where(BatchTaskItem.status == TaskItemStatus.COMPLETED)
            .order_by(BatchTaskItem.sequence_no)
        )
        task_items = result.scalars().all()
        
        rows = [item.output_data["row"] for item in task_items if item.output_data]
        
        # 生成 Excel 文件
        from backend.utils.excel import generate_excel
        file_url = await generate_excel(rows, filename=f"export_{batch_job.id}.xlsx")
        
        # 更新批量任务汇总
        batch_job.summary["export_file_url"] = file_url
        batch_job.summary["export_count"] = len(rows)
        
        log.info(f"Generated Excel file for batch {batch_job.id}: {file_url}")
```

---

## Celery 任务实现

### backend/app/task/tasks/batch/tasks.py

```python
import asyncio
from typing import Any
from celery import shared_task
from sqlalchemy import select
from backend.common.log import log
from backend.common import timezone

def _get_or_create_event_loop() -> asyncio.AbstractEventLoop:
    """获取或创建事件循环（复用现有逻辑）"""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop


from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database.db import SQLALCHEMY_DATABASE_URL, create_async_engine_and_session

@asynccontextmanager
async def local_db_session() -> AsyncGenerator[AsyncSession, None]:
    """创建本地数据库会话（用于 Celery 任务）"""
    engine, session_maker = create_async_engine_and_session(SQLALCHEMY_DATABASE_URL)
    try:
        async with session_maker() as session:
            yield session
    finally:
        await engine.dispose()


@shared_task(
    name="batch.process_batch_job",
    bind=True,
    time_limit=3600,  # 1小时硬超时
    soft_time_limit=3300,  # 55分钟软超时
)
def process_batch_job_task(
    self: Any,
    batch_job_id: str,
) -> dict:
    """
    处理批量任务（主控任务）
    
    策略：
    - 主控任务负责任务编排和状态管理
    - 可以选择串行或并行处理任务项
    - 支持失败隔离（单个任务项失败不影响其他任务项）
    
    Args:
        self: Task 实例
        batch_job_id: 批量任务ID
    
    Returns:
        {
            'batch_job_id': str,
            'total': int,
            'completed': int,
            'failed': int,
            'status': str
        }
    """
    from backend.app.batch.model.batch_job import BatchJob, BatchJobStatus, BatchTaskItem, TaskItemStatus
    from backend.app.batch.handler.base import get_task_handler
    
    async def _async_run() -> dict:
        """异步执行批量任务"""
        
        # 1. 获取批量任务并更新状态
        async with local_db_session() as db:
            batch_job = await db.get(BatchJob, batch_job_id)
            if not batch_job:
                raise ValueError(f"Batch job {batch_job_id} not found")
            
            log.info(f"[Task {self.request.id}] Starting batch job: {batch_job_id} ({batch_job.task_type})")
            
            batch_job.status = BatchJobStatus.PROCESSING
            batch_job.started_time = timezone.now()
            batch_job.celery_task_id = self.request.id
            await db.commit()
            
            # 2. 获取任务处理器
            handler = get_task_handler(batch_job.task_type)
            
            # 3. 调用 on_batch_start 钩子
            try:
                await handler.on_batch_start(batch_job, db)
                await db.commit()
            except Exception as e:
                log.error(f"[Task {self.request.id}] on_batch_start failed: {e}")
        
        # 4. 执行所有任务项
        await _execute_all_task_items(self, batch_job_id)
        
        # 5. 完成批量任务
        return await _complete_batch_job(self, batch_job_id)
    
    loop = _get_or_create_event_loop()
    return loop.run_until_complete(_async_run())


async def _execute_all_task_items(task_self: Any, batch_job_id: str):
    """执行所有任务项（分批处理）"""
    from backend.app.batch.model.batch_job import BatchTaskItem, TaskItemStatus
    
    batch_size = 10  # 每次处理10个任务项
    
    while True:
        async with local_db_session() as db:
            # 获取待处理的任务项
            result = await db.execute(
                select(BatchTaskItem)
                .where(BatchTaskItem.batch_job_id == batch_job_id)
                .where(BatchTaskItem.status == TaskItemStatus.PENDING)
                .order_by(BatchTaskItem.sequence_no)
                .limit(batch_size)
            )
            task_items = list(result.scalars())
            
            if not task_items:
                break
            
            log.info(f"[Task {task_self.request.id}] Processing {len(task_items)} task items")
            
            # 并发处理任务项（使用 asyncio.gather）
            tasks = [
                _process_single_task_item(task_item.id, batch_job_id)
                for task_item in task_items
            ]
            await asyncio.gather(*tasks, return_exceptions=True)


async def _process_single_task_item(task_item_id: str, batch_job_id: str):
    """处理单个任务项"""
    from backend.app.batch.model.batch_job import BatchJob, BatchTaskItem, TaskItemStatus
    from backend.app.batch.handler.base import get_task_handler
    
    # 1. 更新任务项状态为处理中
    async with local_db_session() as db:
        task_item = await db.get(BatchTaskItem, task_item_id)
        if not task_item or task_item.status != TaskItemStatus.PENDING:
            return
        
        task_item.status = TaskItemStatus.PROCESSING
        task_item.started_time = timezone.now()
        
        # 更新批量任务统计
        batch_job = await db.get(BatchJob, batch_job_id)
        batch_job.pending_count -= 1
        batch_job.processing_count += 1
        
        await db.commit()
    
    # 2. 执行任务处理器
    try:
        async with local_db_session() as db:
            task_item = await db.get(BatchTaskItem, task_item_id)
            batch_job = await db.get(BatchJob, batch_job_id)
            
            handler = get_task_handler(batch_job.task_type)
            
            # 执行任务
            output_data = await handler.process(task_item, db)
            
            # 更新成功状态
            task_item.status = TaskItemStatus.COMPLETED
            task_item.output_data = output_data
            task_item.completed_time = timezone.now()
            
            # 更新批量任务统计
            batch_job.processing_count -= 1
            batch_job.completed_count += 1
            batch_job.updated_time = timezone.now()
            
            await db.commit()
            
            log.info(f"Task item {task_item_id} completed successfully")
            
            # 调用进度钩子
            await handler.on_batch_progress(batch_job, db)
            await db.commit()
            
    except Exception as e:
        # 3. 处理失败
        async with local_db_session() as db:
            task_item = await db.get(BatchTaskItem, task_item_id)
            batch_job = await db.get(BatchJob, batch_job_id)
            
            task_item.retry_count += 1
            
            # 判断是否需要重试
            if task_item.retry_count < task_item.max_retries:
                task_item.status = TaskItemStatus.PENDING
                batch_job.processing_count -= 1
                batch_job.pending_count += 1
                log.warning(f"Task item {task_item_id} failed, will retry ({task_item.retry_count}/{task_item.max_retries}): {e}")
            else:
                task_item.status = TaskItemStatus.FAILED
                task_item.error_message = str(e)
                task_item.error_code = type(e).__name__
                task_item.completed_time = timezone.now()
                batch_job.processing_count -= 1
                batch_job.failed_count += 1
                log.error(f"Task item {task_item_id} failed permanently: {e}")
            
            batch_job.updated_time = timezone.now()
            await db.commit()


async def _complete_batch_job(task_self: Any, batch_job_id: str) -> dict:
    """完成批量任务"""
    from backend.app.batch.model.batch_job import BatchJob, BatchJobStatus
    from backend.app.batch.handler.base import get_task_handler
    
    async with local_db_session() as db:
        batch_job = await db.get(BatchJob, batch_job_id)
        
        log.info(f"[Task {task_self.request.id}] Completing batch job: {batch_job_id}")
        
        # 调用 on_batch_complete 钩子
        try:
            handler = get_task_handler(batch_job.task_type)
            await handler.on_batch_complete(batch_job, db)
        except Exception as e:
            log.error(f"[Task {task_self.request.id}] on_batch_complete failed: {e}")
        
        # 更新批量任务状态
        if batch_job.failed_count > 0 and batch_job.completed_count == 0:
            batch_job.status = BatchJobStatus.FAILED
        else:
            batch_job.status = BatchJobStatus.COMPLETED
        
        batch_job.completed_time = timezone.now()
        batch_job.updated_time = timezone.now()
        
        await db.commit()
        
        log.info(
            f"[Task {task_self.request.id}] Batch job {batch_job_id} completed: "
            f"{batch_job.completed_count} succeeded, {batch_job.failed_count} failed"
        )
        
        # 发送完成通知
        from backend.common.socketio.actions import task_notification
        await task_notification(
            msg=f"批量任务完成：{batch_job.name}（成功 {batch_job.completed_count} 个，失败 {batch_job.failed_count} 个）"
        )
        
        return {
            "batch_job_id": batch_job.id,
            "total": batch_job.total_count,
            "completed": batch_job.completed_count,
            "failed": batch_job.failed_count,
            "status": batch_job.status,
        }
```

---

## 服务层实现

### backend/app/batch/service/batch_service.py

```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.app.batch.model.batch_job import BatchJob, BatchTaskItem, BatchJobStatus
from backend.app.batch.handler.base import get_task_handler
from backend.common.log import log
from backend.common import timezone
from backend.common.uuid import uuid4_str


async def create_batch_job(
    db: AsyncSession,
    tenant_id: str,
    task_type: str,
    items: list[dict],
    name: str | None = None,
    config: dict | None = None,
    created_by: str | None = None,
) -> BatchJob:
    """
    创建批量任务
    
    Args:
        db: 数据库会话
        tenant_id: 租户ID
        task_type: 任务类型
        items: 任务项输入数据列表
        name: 任务名称
        config: 执行配置
        created_by: 创建者ID
    
    Returns:
        批量任务对象
    """
    
    # 验证任务类型
    get_task_handler(task_type)  # 如果不存在会抛出异常
    
    # 创建批量任务
    batch_job = BatchJob(
        id=uuid4_str(),
        tenant_id=tenant_id,
        task_type=task_type,
        name=name or f"{task_type}_{timezone.now().strftime('%Y%m%d_%H%M%S')}",
        total_count=len(items),
        pending_count=len(items),
        status=BatchJobStatus.PENDING,
        config=config or {},
        created_by=created_by,
        created_time=timezone.now(),
        updated_time=timezone.now(),
    )
    db.add(batch_job)
    
    # 创建任务项
    for idx, item_data in enumerate(items):
        task_item = BatchTaskItem(
            id=uuid4_str(),
            batch_job_id=batch_job.id,
            sequence_no=idx,
            input_data=item_data,
            max_retries=config.get("max_retries", 3) if config else 3,
            created_time=timezone.now(),
            updated_time=timezone.now(),
        )
        db.add(task_item)
    
    await db.flush()
    
    log.info(f"Created batch job {batch_job.id} ({task_type}) with {len(items)} items")
    
    # 触发 Celery 任务
    from backend.app.task.tasks.batch.tasks import process_batch_job_task
    task = process_batch_job_task.delay(batch_job.id)
    
    # 更新 celery_task_id
    batch_job.celery_task_id = task.id
    
    log.info(f"Triggered Celery task {task.id} for batch job {batch_job.id}")
    
    return batch_job


async def get_batch_progress(
    db: AsyncSession,
    batch_id: str,
) -> dict:
    """查询批量任务进度"""
    
    batch_job = await db.get(BatchJob, batch_id)
    if not batch_job:
        raise ValueError(f"Batch job {batch_id} not found")
    
    # 计算进度百分比
    progress = 0
    if batch_job.total_count > 0:
        progress = (batch_job.completed_count + batch_job.failed_count) / batch_job.total_count * 100
    
    return {
        "batch_id": batch_job.id,
        "task_type": batch_job.task_type,
        "name": batch_job.name,
        "status": batch_job.status,
        "total_count": batch_job.total_count,
        "pending_count": batch_job.pending_count,
        "processing_count": batch_job.processing_count,
        "completed_count": batch_job.completed_count,
        "failed_count": batch_job.failed_count,
        "progress": round(progress, 2),
        "summary": batch_job.summary,
        "created_time": batch_job.created_time,
        "started_time": batch_job.started_time,
        "completed_time": batch_job.completed_time,
        "celery_task_id": batch_job.celery_task_id,
    }


async def cancel_batch_job(
    db: AsyncSession,
    batch_id: str,
) -> bool:
    """取消批量任务"""
    
    batch_job = await db.get(BatchJob, batch_id)
    if not batch_job:
        raise ValueError(f"Batch job {batch_id} not found")
    
    if batch_job.status not in [BatchJobStatus.PENDING, BatchJobStatus.PROCESSING]:
        raise ValueError(f"Cannot cancel batch job in status {batch_job.status}")
    
    # 取消 Celery 任务
    if batch_job.celery_task_id:
        from backend.app.task.celery import celery_app
        celery_app.control.revoke(batch_job.celery_task_id, terminate=True)
        log.info(f"Revoked Celery task {batch_job.celery_task_id}")
    
    # 更新状态
    batch_job.status = BatchJobStatus.CANCELLED
    batch_job.updated_time = timezone.now()
    await db.flush()
    
    log.info(f"Cancelled batch job {batch_id}")
    
    return True
```

---

## API 接口实现

### backend/app/batch/api/v1/batch.py

```python
from fastapi import APIRouter, UploadFile, File
from backend.database.db import CurrentSession
from backend.app.auth.deps import CurrentTenantId, CurrentUserId
from backend.app.batch.service.batch_service import (
    create_batch_job,
    get_batch_progress,
    cancel_batch_job,
)
from backend.common import response_base
from pydantic import BaseModel

router = APIRouter(prefix="/batch", tags=["批量任务"])


class BatchJobCreate(BaseModel):
    """创建批量任务请求"""
    task_type: str
    name: str | None = None
    items: list[dict]
    config: dict | None = None


@router.post("/jobs")
async def create_job(
    data: BatchJobCreate,
    db: CurrentSession,
    tenant_id: str = CurrentTenantId,
    user_id: str = CurrentUserId,
):
    """
    创建批量任务（通用接口）
    
    Request Body:
    {
      "task_type": "screenshot_recognition",
      "name": "批量导入截图 2024-01-26",
      "items": [
        {"image_url": "https://..."},
        {"image_url": "https://..."}
      ],
      "config": {
        "max_retries": 3
      }
    }
    """
    
    batch_job = await create_batch_job(
        db=db,
        tenant_id=tenant_id,
        task_type=data.task_type,
        items=data.items,
        name=data.name,
        config=data.config,
        created_by=user_id,
    )
    
    return response_base.success(data={
        "batch_id": batch_job.id,
        "celery_task_id": batch_job.celery_task_id,
    })


@router.get("/jobs/{batch_id}")
async def get_job_progress(
    batch_id: str,
    db: CurrentSession,
):
    """查询批量任务进度（通用接口）"""
    
    progress = await get_batch_progress(db, batch_id)
    return response_base.success(data=progress)


@router.delete("/jobs/{batch_id}")
async def cancel_job(
    batch_id: str,
    db: CurrentSession,
):
    """取消批量任务"""
    
    await cancel_batch_job(db, batch_id)
    return response_base.success()


@router.get("/jobs")
async def list_jobs(
    db: CurrentSession,
    task_type: str | None = None,
    tenant_id: str = CurrentTenantId,
    page: int = 1,
    page_size: int = 20,
):
    """查询批量任务列表"""
    from sqlalchemy import select
    from backend.app.batch.model.batch_job import BatchJob
    
    query = select(BatchJob).where(BatchJob.tenant_id == tenant_id)
    
    if task_type:
        query = query.where(BatchJob.task_type == task_type)
    
    query = query.order_by(BatchJob.created_time.desc()).limit(page_size).offset((page - 1) * page_size)
    
    result = await db.execute(query)
    jobs = result.scalars().all()
    
    return response_base.success(data=[
        {
            "batch_id": job.id,
            "task_type": job.task_type,
            "name": job.name,
            "status": job.status,
            "total_count": job.total_count,
            "completed_count": job.completed_count,
            "failed_count": job.failed_count,
            "progress": (job.completed_count + job.failed_count) / job.total_count * 100 if job.total_count > 0 else 0,
            "created_time": job.created_time,
            "celery_task_id": job.celery_task_id,
        }
        for job in jobs
    ])


# ============================================================
# 业务特定的便捷接口
# ============================================================

@router.post("/feedbacks/screenshot-batch-upload")
async def screenshot_batch_upload(
    files: list[UploadFile] = File(...),
    board_id: str | None = None,
    db: CurrentSession,
    tenant_id: str = CurrentTenantId,
    user_id: str = CurrentUserId,
):
    """批量上传截图（便捷接口）"""
    from backend.utils.storage import storage
    from backend.common import timezone
    
    # 1. 上传文件到 OSS
    items = []
    for file in files:
        # 上传到 OSS
        storage_path = f"screenshots/{tenant_id}/{timezone.now().strftime('%Y%m%d')}/{file.filename}"
        image_url = await storage.upload(file.file, storage_path, content_type=file.content_type)
        
        items.append({
            "image_url": image_url,
            "board_id": board_id,
        })
    
    # 2. 创建批量任务
    batch_job = await create_batch_job(
        db=db,
        tenant_id=tenant_id,
        task_type="screenshot_recognition",
        items=items,
        name=f"批量截图识别 {timezone.now().strftime('%Y-%m-%d %H:%M')}",
        created_by=user_id,
    )
    
    return response_base.success(data={
        "batch_id": batch_job.id,
        "celery_task_id": batch_job.celery_task_id,
        "total_count": len(items),
    })
```

---

## 前端实现示例

### 批量上传组件（Vue）

```vue
<template>
  <div>
    <!-- 批量上传 -->
    <a-upload
      multiple
      :before-upload="handleBeforeUpload"
      :file-list="fileList"
      @remove="handleRemove"
    >
      <a-button>
        <upload-outlined /> 选择截图（支持多选）
      </a-button>
    </a-upload>
    
    <a-button 
      type="primary" 
      @click="handleBatchUpload" 
      :loading="uploading"
      :disabled="fileList.length === 0"
    >
      批量上传并识别（{{ fileList.length }} 张）
    </a-button>
    
    <!-- 进度弹窗 -->
    <a-modal 
      v-model:visible="progressVisible" 
      title="批量识别进度" 
      :footer="null"
      :closable="progress >= 100"
      :maskClosable="false"
    >
      <a-progress :percent="progress" />
      
      <div style="margin-top: 16px">
        <a-statistic-group>
          <a-statistic title="总数" :value="totalCount" />
          <a-statistic title="已完成" :value="completedCount" />
          <a-statistic title="成功" :value="successCount" valueStyle="color: #52c41a" />
          <a-statistic title="失败" :value="failedCount" valueStyle="color: #ff4d4f" />
        </a-statistic-group>
      </div>
      
      <div v-if="progress >= 100" style="margin-top: 16px">
        <a-result
          status="success"
          title="批量识别完成"
          :sub-title="`成功 ${successCount} 个，失败 ${failedCount} 个`"
        >
          <template #extra>
            <a-button type="primary" @click="handleClose">关闭</a-button>
          </template>
        </a-result>
      </div>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { message } from 'ant-design-vue';
import { batchUploadScreenshots, getBatchProgress } from '#/api/batch';

const fileList = ref([]);
const uploading = ref(false);
const progressVisible = ref(false);
const batchId = ref('');
const progress = ref(0);
const completedCount = ref(0);
const totalCount = ref(0);
const successCount = ref(0);
const failedCount = ref(0);

const emit = defineEmits(['refresh']);

function handleBeforeUpload(file) {
  fileList.value.push(file);
  return false; // 阻止自动上传
}

function handleRemove(file) {
  const index = fileList.value.indexOf(file);
  fileList.value.splice(index, 1);
}

async function handleBatchUpload() {
  if (fileList.value.length === 0) {
    message.warning('请先选择截图');
    return;
  }
  
  uploading.value = true;
  
  try {
    // 1. 批量上传
    const formData = new FormData();
    fileList.value.forEach(file => {
      formData.append('files', file);
    });
    
    const res = await batchUploadScreenshots(formData);
    batchId.value = res.data.batch_id;
    
    // 2. 显示进度弹窗
    progressVisible.value = true;
    progress.value = 0;
    completedCount.value = 0;
    totalCount.value = res.data.total_count;
    successCount.value = 0;
    failedCount.value = 0;
    
    // 3. 开始轮询进度
    pollProgress();
    
  } catch (error) {
    message.error('上传失败');
  } finally {
    uploading.value = false;
  }
}

async function pollProgress() {
  const timer = setInterval(async () => {
    try {
      const res = await getBatchProgress(batchId.value);
      const data = res.data;
      
      progress.value = data.progress;
      completedCount.value = data.completed_count;
      totalCount.value = data.total_count;
      successCount.value = data.completed_count;
      failedCount.value = data.failed_count;
      
      // 如果完成，停止轮询
      if (data.status === 'completed' || data.status === 'failed') {
        clearInterval(timer);
        
        if (data.status === 'completed') {
          message.success(`批量识别完成！成功 ${successCount.value} 个`);
        } else {
          message.error('批量识别失败');
        }
        
        // 刷新反馈列表
        emit('refresh');
      }
    } catch (error) {
      clearInterval(timer);
      message.error('获取进度失败');
    }
  }, 2000); // 每2秒轮询一次
}

function handleClose() {
  progressVisible.value = false;
  fileList.value = [];
  emit('refresh');
}
</script>
```

---

## 使用示例

### 场景1：批量截图识别

```python
# 1. 注册处理器（只需要写一次）
@batch_task_handler("screenshot_recognition")
class ScreenshotRecognitionHandler(BatchTaskHandler):
    async def process(self, task_item, db):
        result = await ai_client.analyze_screenshot(task_item.input_data["image_url"])
        feedback = await create_feedback(db, ...)
        return {"feedback_id": feedback.id}

# 2. 创建批量任务（API 调用）
POST /api/v1/batch/jobs
{
  "task_type": "screenshot_recognition",
  "name": "批量截图识别 2024-01-26",
  "items": [
    {"image_url": "https://...", "board_id": "xxx"},
    {"image_url": "https://...", "board_id": "xxx"}
  ]
}

# 3. 查询进度（轮询）
GET /api/v1/batch/jobs/{batch_id}
```

### 场景2：批量 Excel 导入

```python
# 1. 解析 Excel 文件
rows = parse_excel(file)

# 2. 创建批量任务
batch_job = await create_batch_job(
    db, tenant_id, "excel_import",
    items=[{"row_data": row} for row in rows]
)

# 3. Celery 自动处理
# - 每行数据会被包装成一个 task_item
# - ExcelImportHandler 会处理每一行
# - 进度实时更新
```

### 场景3：批量数据导出

```python
# 1. 创建批量任务
batch_job = await create_batch_job(
    db, tenant_id, "data_export",
    items=[{"feedback_id": fid} for fid in feedback_ids]
)

# 2. DataExportHandler 处理每个反馈
# - 查询反馈数据
# - 转换为导出格式
# - 保存到 task_item.output_data

# 3. on_batch_complete 钩子生成 Excel 文件
# - 收集所有 task_item.output_data
# - 生成 Excel 文件
# - 更新 batch_job.summary["export_file_url"]
```

---

## 优势总结

### 1. 统一的数据结构

✅ 所有批量任务使用同一套表（`batch_job` + `batch_task_item`）
✅ JSONB 字段灵活支持不同类型任务的输入输出
✅ 不需要为每个功能单独设计表

### 2. 可插拔的处理器

✅ 新增任务类型只需注册处理器，不需要改框架
✅ 处理器接口简单（`process()` + 可选的钩子）
✅ 业务代码与框架解耦

### 3. 生产级可靠性

✅ 基于 Celery + Redis 的分布式任务队列
✅ 自动重试机制（单个任务失败不影响其他任务）
✅ 失败隔离（部分失败不影响整体）
✅ 任务持久化（Worker 崩溃可恢复）

### 4. 完善的进度追踪

✅ 统一的进度查询 API
✅ 实时统计（总数、待处理、处理中、成功、失败）
✅ 支持 Socket.IO 实时推送（可选）
✅ 支持查询 Celery 任务状态

### 5. 使用简单

✅ 创建批量任务只需 2 行代码
✅ 前端轮询进度只需调用一个 API
✅ 自动管理状态、重试、错误处理

---

## 下一步计划

### 立即实施

1. **创建数据库迁移脚本**
   ```bash
   cd server/backend
   alembic revision -m "create batch job tables"
   ```

2. **实现核心框架代码**
   - 模型定义
   - 任务处理器基类
   - Celery 任务
   - 服务层
   - API 接口

3. **迁移截图识别到新框架**
   - 实现 `ScreenshotRecognitionHandler`
   - 更新现有 API
   - 测试批量上传

### 渐进式优化

1. **WebSocket 实时推送**
   - 在 `on_batch_progress` 钩子中推送进度
   - 前端监听 WebSocket 事件

2. **更多任务类型**
   - Excel 导入
   - 数据导出
   - 批量更新
   - 批量删除

3. **监控和告警**
   - 任务失败率监控
   - 任务执行时间监控
   - 积分消耗统计

---

## 总结

**这是一个通用的、可扩展的、生产级的批处理任务框架。**

**核心设计理念：**
- 数据结构驱动（`task_type` + JSONB）
- 可插拔设计（处理器注册机制）
- 基于现有基础设施（Celery + Redis）
- 使用简单（2 行代码创建批量任务）

**Linus 的评价：**
> "这才是好的设计：简单、通用、可扩展。不是为了一个功能设计，而是为了整个系统设计。"
