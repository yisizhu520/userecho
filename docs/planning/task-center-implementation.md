# 任务中心实现进度

## 实现概述

基于 [unified-task-center.md](./unified-task-center.md) 的技术方案，实现了统一任务中心功能，将批量任务和单任务统一到一个界面中展示。
## 两个任务中心的区别

系统中现在有两个任务中心，服务于不同的用户群体：

### 1. 用户任务中心（我的任务）
- **路由名称**: `UserTaskCenter`
- **访问路径**: `/app/tasks`
- **菜单标题**: "我的任务"
- **服务对象**: 普通租户用户
- **功能范围**: 
  - 查看当前租户的批量任务（批量截图识别、批量AI聚类、批量导出）
  - 查看当前租户的单任务（Excel导入、AI聚类、截图识别）
  - 支持筛选、查看详情、取消、重试
- **数据源**: `batch_job` 和 `task_record` 表（按 tenant_id 过滤）
- **组件位置**: `front/apps/web-antd/src/views/userecho/batch-jobs/index.vue`

### 2. 系统任务中心（管理员）
- **路由名称**: `TaskCenter`
- **访问路径**: `/system/task-center`
- **菜单标题**: "任务中心"
- **服务对象**: 系统管理员
- **功能范围**:
  - 查看所有租户的 task_record 记录
  - 系统级任务监控和统计
  - 任务执行情况分析
- **数据源**: `task_record` 表（不过滤 tenant_id）
- **组件位置**: `front/apps/web-antd/src/views/userecho/task-center/index.vue`

**命名规范**：
- 用户的任务中心称为 **"我的任务"**，避免与系统任务中心混淆
- 路由名称使用 `UserTaskCenter` 避免与系统的 `TaskCenter` 冲突

## 实现阶段

### Phase 1: 后端适配层 ✅ 已完成

#### 1.1 创建统一任务 DTO schema ✅
- **文件**: `server/backend/app/task/schema/unified_task.py`
- **内容**:
  - `TaskType` enum: 定义6种任务类型
    - 批量任务: `batch_screenshot_recognition`, `batch_ai_clustering`, `batch_export`
    - 单任务: `excel_import`, `clustering`, `screenshot_recognition`
  - `TaskStatus` enum: 定义5种任务状态
    - `pending`, `processing`, `completed`, `failed`, `cancelled`
  - `UnifiedTask` DTO: 20+字段的统一任务抽象
  - `UnifiedTaskList`: 分页列表响应

#### 1.2 实现 BatchJobAdapter ✅
- **文件**: `server/backend/app/task/adapter/task_adapter.py`
- **内容**:
  - `TaskAdapter` 抽象基类
  - `BatchJobAdapter`: 将 `batch_job` 表转换为 `UnifiedTask`
    - 类型映射: `task_type` → `TaskType`
    - 状态映射: `pending/processing/completed/failed/cancelled` → `TaskStatus`
    - 字段映射: `batch_id` → `task_id`, `is_batch=True`

#### 1.3 实现 TaskRecordAdapter ✅
- **文件**: `server/backend/app/task/adapter/task_adapter.py`
- **内容**:
  - `TaskRecordAdapter`: 将 `task_record` 表转换为 `UnifiedTask`
    - 类型映射: `task_type` → `TaskType`
    - 状态映射: `pending/running/success/failure/revoked` → `TaskStatus`
    - 字段映射: `id` → `task_id`, `is_batch=False`
    - 进度计算: 基于 `status` 计算 `progress` (0%/50%/100%)

#### 1.4 实现 unified_task_service ✅
- **文件**: `server/backend/app/task/service/unified_task_service.py`
- **内容**:
  - `get_unified_tasks()`: 聚合两表查询，支持过滤、分页、排序
  - `get_unified_task_by_id()`: 根据 task_id 查询单个任务
  - `cancel_unified_task()`: 取消任务（委托给原有 service）
  - `retry_unified_task()`: 重试任务（委托给原有 service）

#### 1.5 实现统一任务 API ✅
- **文件**: `server/backend/app/task/api/v1/unified_tasks.py`
- **路由**: `/api/v1/app/tasks`
- **端点**:
  - `GET /tasks`: 获取统一任务列表
  - `GET /tasks/{task_id}`: 获取任务详情
  - `POST /tasks/{task_id}/cancel`: 取消任务
  - `POST /tasks/{task_id}/retry`: 重试任务

#### 1.6 注册路由 ✅
- **文件**: `server/backend/app/userecho/api/router.py`
- **内容**: 添加 `unified_tasks.router` 到 v1 路由

### Phase 2: 前端统一界面 ✅ 已完成

#### 2.1 更新 API 类型和接口 ✅
- **文件**: `front/apps/web-antd/src/api/userecho/batch.ts`
- **内容**:
  - 新增统一任务类型: `TaskType`, `TaskStatus`, `UnifiedTask`, `UnifiedTaskListResponse`
  - 新增统一任务 API: `getUnifiedTasks`, `getUnifiedTask`, `cancelUnifiedTask`, `retryUnifiedTask`
  - 保留旧版批处理任务 API（兼容性）

#### 2.2 修改任务列表页面 ✅
- **文件**: `front/apps/web-antd/src/views/userecho/batch-jobs/index.vue`
- **改动**:
  - 标题: "批处理任务" → "任务中心"
  - 描述: "查看和管理所有批处理任务的执行状态" → "查看和管理所有异步任务的执行状态"
  - 数据源: `getBatchJobs` → `getUnifiedTasks`
  - 任务 ID: `job.batch_id` → `job.task_id`
  - 任务类型选项: 增加6种任务类型
  - 统计数据: 批量任务显示详细统计，单任务显示简单信息
  - TypeScript 类型: `BatchJob` → `UnifiedTask`

#### 2.3 更新路由配置 ✅
- **文件**: `front/apps/web-antd/src/router/routes/modules/userecho.ts`
- **改动**:
  - 路由名称: ~~`BatchJobs`~~ → `UserTaskCenter`（避免与系统的 `TaskCenter` 冲突）
  - 路由路径: ~~`/app/batch-jobs`~~ → `/app/tasks`
  - 菜单标题: ~~"批处理任务"~~ → **"我的任务"**（区分于系统管理员的"任务中心"）
  - 注释: "批处理任务对所有人可见" → "我的任务对所有人可见"
  
#### 2.4 修正系统任务中心配置 ✅
- **问题**: 数据库中已存在系统管理员的 `TaskCenter` 菜单，组件路径不正确
- **解决**: 
  - 修正组件路径: `/src/views/userecho/task-center/index` → `/userecho/task-center/index`
  - 确认路径: `/system/task-center`（系统管理员专用）
  - 与用户任务中心（`/app/tasks`）明确区分

### Phase 3: 单任务详情页（可选）⏸️ 暂缓

**当前状态**: 批量任务详情组件 `BatchJobDetail.vue` 可以处理批量任务，单任务暂时也使用同一组件，后续根据需要创建专门的单任务详情组件。

**待实现内容**:
- [ ] 创建 `TaskDetailSingle.vue` 组件
- [ ] 展示任务参数（`metadata`）
- [ ] 展示任务结果（`summary`）
- [ ] 展示错误信息（`error_message`）
- [ ] 支持取消和重试操作

## 技术要点

### 1. 零破坏性设计

- ✅ 保留 `batch_job` 和 `task_record` 两个表不变
- ✅ 保留原有 batch job API（`/api/v1/app/batch/jobs/*`）
- ✅ 新增统一任务 API（`/api/v1/app/tasks`）
- ✅ 前端兼容性：保留旧 API 类型定义

### 2. 适配器模式

```python
# 架构
batch_job (DB) → BatchJobAdapter → UnifiedTask (DTO) → Frontend
task_record (DB) → TaskRecordAdapter → UnifiedTask (DTO) → Frontend
```

### 3. 类型映射

**TaskType 映射**:
```python
# batch_job.task_type → UnifiedTask.task_type
'screenshot_recognition' → 'batch_screenshot_recognition'
'ai_clustering' → 'batch_ai_clustering'

# task_record.task_type → UnifiedTask.task_type
'excel_import' → 'excel_import'
'clustering' → 'clustering'
```

**TaskStatus 映射**:
```python
# batch_job.status → UnifiedTask.status
pending/processing/completed/failed/cancelled → 保持不变

# task_record.status → UnifiedTask.status
pending → pending
running → processing
success → completed
failure → failed
revoked → cancelled
```

### 4. 进度计算

**批量任务**:
```python
progress = (completed_count / total_count) * 100
```

**单任务**:
```python
progress = {
    'pending': 0,
    'running': 50,
    'success': 100,
    'failure': 100,
    'revoked': 0,
}[status]
```

## 代码质量检查

### 前端 TypeScript 检查 ✅

```bash
cd front && pnpm check:type
```

- ✅ 修复了 `job.total_count` null 检查问题
- ✅ 使用可选链: `(job.total_count ?? 0) - (job.completed_count ?? 0) - (job.failed_count ?? 0)`

### 后端代码检查 ⚠️

```bash
cd server && bash pre-commit.sh
```

- ✅ Ruff 格式化通过
- ⚠️ 存在其他文件的 mypy 错误（不影响任务中心功能）
  - `server/scripts/embedding_comparison/03_test_clustering_quality.py:143:52` - 未定义变量
  - `server/test_multi_feedback.py:49` - 类型错误

**任务中心相关文件没有错误！**

## 前后端 API 对应

| 前端路径 | 后端路由 | 功能 |
|---------|---------|------|
| `getUnifiedTasks()` | `GET /api/v1/app/tasks` | 获取统一任务列表 |
| `getUnifiedTask(id)` | `GET /api/v1/app/tasks/{id}` | 获取任务详情 |
| `cancelUnifiedTask(id)` | `POST /api/v1/app/tasks/{id}/cancel` | 取消任务 |
| `retryUnifiedTask(id)` | `POST /api/v1/app/tasks/{id}/retry` | 重试任务 |

## UI 展示逻辑

### 任务卡片

**批量任务**:
- 显示进度条
- 显示详细统计（总数、成功、失败、待处理）
- 显示执行时长

**单任务**:
- 显示进度条
- 显示简单信息（描述文本）
- 显示执行时长

### 任务类型图标

| 任务类型 | 标签文字 | 颜色 |
|---------|---------|------|
| `batch_screenshot_recognition` | 批量截图识别 | blue |
| `batch_ai_clustering` | 批量AI聚类 | blue |
| `batch_export` | 批量导出 | blue |
| `excel_import` | Excel导入 | green |
| `clustering` | AI聚类 | purple |
| `screenshot_recognition` | 截图识别 | orange |

### 状态图标

| 状态 | 图标 | 颜色 | 动画 |
|------|------|------|------|
| `pending` | ClockCircleOutlined | default | - |
| `processing` | SyncOutlined | processing | spin + pulse |
| `completed` | CheckCircleOutlined | success | - |
| `failed` | CloseCircleOutlined | error | - |
| `cancelled` | StopOutlined | default | - |

## 文件清单

### 后端新增文件
1. `server/backend/app/task/schema/unified_task.py` - DTO schema
2. `server/backend/app/task/adapter/task_adapter.py` - 适配器
3. `server/backend/app/task/service/unified_task_service.py` - 服务层
4. `server/backend/app/task/api/v1/unified_tasks.py` - API 端点

### 后端修改文件
1. `server/backend/app/userecho/api/router.py` - 路由注册

### 前端修改文件
1. `front/apps/web-antd/src/api/userecho/batch.ts` - API 类型和接口
2. `front/apps/web-antd/src/views/userecho/batch-jobs/index.vue` - 任务列表页
3. `front/apps/web-antd/src/router/routes/modules/userecho.ts` - 路由配置

## 测试建议

### 后端测试
```bash
# 1. 启动后端
cd server
source .venv/Scripts/activate
python -m backend.main

# 2. 测试统一任务 API
curl http://localhost:8000/api/v1/app/tasks

# 3. 创建一些测试数据
# - 批量截图识别任务
# - Excel 导入任务
# - AI 聚类任务
```

### 前端测试
```bash
# 1. 启动前端
cd front
pnpm dev

# 2. 访问任务中心
# http://localhost:5555/app/tasks

# 3. 测试功能
# - 筛选任务类型
# - 筛选任务状态
# - 查看任务详情
# - 取消运行中的任务
# - 重试失败的任务
```

## 已知问题和限制

1. **单任务详情组件**: 暂时复用批量任务详情组件，后续可根据需要创建专门的单任务详情组件
2. **实时更新**: 使用 3 秒轮询，可考虑改用 WebSocket（后续优化）
3. **性能优化**: 当任务量很大时，可考虑增加索引优化查询性能

## 下一步计划

### 短期（可选）
- [ ] 创建专门的单任务详情组件
- [ ] 增加任务类型图标（区分批量/单任务）
- [ ] 优化移动端显示

### 中期
- [ ] 增加任务搜索功能（按名称搜索）
- [ ] 增加任务导出功能（导出任务列表）
- [ ] 增加任务统计面板（今日任务数、成功率等）

### 长期
- [ ] WebSocket 实时推送（替代轮询）
- [ ] 任务执行日志查看
- [ ] 任务链（依赖关系）可视化

## 参考文档

- [统一任务中心技术方案](./unified-task-center.md)
- [批处理任务框架设计](./batch-job-framework.md)

---

**实现时间**: 2024年（估算）
**实现者**: AI Assistant
**版本**: v1.0
