"""统一任务服务层 - 聚合批处理任务和单任务"""

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.batch.model.batch_job import BatchJob
from backend.app.task.adapter.task_adapter import BatchJobAdapter, TaskRecordAdapter
from backend.app.task.model.task_record import TaskRecord
from backend.app.task.schema.unified_task import TaskStatus, TaskType, UnifiedTask, UnifiedTaskList
from backend.common.log import log


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
            TaskType.BATCH_AI_CLUSTERING: "ai_clustering",
            TaskType.BATCH_EXPORT: "export",
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

    batch_query = batch_query.order_by(desc(BatchJob.create_time))

    batch_result = await db.execute(batch_query)
    batch_jobs = batch_result.scalars().all()

    for batch_job in batch_jobs:
        all_tasks.append(batch_adapter.to_unified_task(batch_job))

    # 2. 查询单任务
    task_query = select(TaskRecord).where(TaskRecord.tenant_id == tenant_id)

    # 类型过滤
    if task_type and not task_type.value.startswith("batch_"):
        task_category_mapping = {
            TaskType.EXCEL_IMPORT: "excel_import",
            TaskType.CLUSTERING: "clustering",
            TaskType.SCREENSHOT_RECOGNITION: "screenshot_recognition",
            TaskType.AI_SCREENSHOT: "ai_screenshot",
            TaskType.BATCH: "batch",
        }
        if task_type in task_category_mapping:
            task_query = task_query.where(TaskRecord.task_category == task_category_mapping[task_type])

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

    # 先尝试从 batch_job 查询（UUID 格式）
    batch_job = await db.get(BatchJob, task_id)
    if batch_job:
        adapter = BatchJobAdapter()
        return adapter.to_unified_task(batch_job)

    # 再尝试从 task_record 查询（整数 ID）
    try:
        task_record_id = int(task_id)
        task_record = await db.get(TaskRecord, task_record_id)
        if task_record:
            adapter = TaskRecordAdapter()
            return adapter.to_unified_task(task_record)
    except ValueError:
        # task_id 不是有效的整数，跳过 task_record 查询
        pass

    return None


async def cancel_unified_task(
    db: AsyncSession,
    task_id: str,
) -> bool:
    """取消统一任务"""

    # 尝试取消批处理任务（UUID 格式）
    batch_job = await db.get(BatchJob, task_id)
    if batch_job:
        from backend.app.batch.service.batch_service import cancel_batch_job

        await cancel_batch_job(db, task_id)
        return True

    # 尝试取消单任务（整数 ID）
    try:
        task_record_id = int(task_id)
        task_record = await db.get(TaskRecord, task_record_id)
        if task_record:
            from backend.app.task.celery import celery_app

            celery_app.control.revoke(task_record.task_id, terminate=True)
            task_record.status = "revoked"
            log.info(f"Cancelled task {task_id} (celery_task_id: {task_record.task_id})")
            return True
    except ValueError:
        # task_id 不是有效的整数，跳过 task_record 查询
        pass

    return False


async def retry_unified_task(
    db: AsyncSession,
    task_id: str,
) -> str | None:
    """重试统一任务"""

    # 尝试重试批处理任务（UUID 格式）
    batch_job = await db.get(BatchJob, task_id)
    if batch_job:
        from backend.app.batch.service.batch_service import enqueue_batch_job

        celery_task_id = await enqueue_batch_job(task_id)
        log.info(f"Retried batch job {task_id}, new celery_task_id: {celery_task_id}")
        return celery_task_id

    # 尝试重试单任务（整数 ID）
    try:
        task_record_id = int(task_id)
        task_record = await db.get(TaskRecord, task_record_id)
        if task_record:
            # 根据任务类型重新提交
            # 注意：这里需要根据实际的任务提交逻辑来实现
            # 简化处理：复制原任务参数，创建新任务
            from backend.app.task.model.task_record import TaskRecord as NewTaskRecord
            from backend.common import timezone
            from backend.common.uuid import uuid4_str

            new_task = NewTaskRecord(
                id=uuid4_str(),
                tenant_id=task_record.tenant_id,
                task_name=task_record.task_name,
                task_args=task_record.task_args,
                status="pending",
                created_time=timezone.now(),
                updated_time=timezone.now(),
            )
            db.add(new_task)

            log.info(f"Retried task {task_id}, new task_id: {new_task.id}")
            return new_task.id
    except ValueError:
        # task_id 不是有效的整数，跳过 task_record 查询
        pass

    return None
