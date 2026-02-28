"""批量任务服务实现"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.batch.handler.base import get_task_handler
from backend.app.batch.model.batch_job import BatchJob, BatchJobStatus, BatchTaskItem, TaskItemStatus
from backend.common import timezone
from backend.common.log import log
from backend.common.uuid import uuid4_str
from backend.database.db import async_db_session


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
        status=BatchJobStatus.PENDING.value,
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

    log.info(f"Created batch job {batch_job.id} ({task_type}) with {len(items)} items")

    return batch_job


async def enqueue_batch_job(batch_job_id: str) -> str:
    """触发 Celery 任务并更新 celery_task_id（在事务提交后调用）"""
    from backend.app.task.tasks.batch.tasks import process_batch_job_task

    task = process_batch_job_task.delay(batch_job_id)

    async with async_db_session() as db:
        batch_job = await db.get(BatchJob, batch_job_id)
        if not batch_job:
            log.error(f"Batch job {batch_job_id} not found when enqueueing")
            return task.id
        batch_job.celery_task_id = task.id
        batch_job.updated_time = timezone.now()
        await db.commit()

    log.info(f"Triggered Celery task {task.id} for batch job {batch_job_id}")
    return task.id


async def get_batch_progress(
    db: AsyncSession,
    batch_id: str,
) -> dict:
    """查询批量任务进度"""

    batch_job = await db.get(BatchJob, batch_id)
    if not batch_job:
        raise ValueError(f"Batch job {batch_id} not found")

    # 计算进度百分比
    progress = 0.0
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

    if batch_job.status not in [BatchJobStatus.PENDING.value, BatchJobStatus.PROCESSING.value]:
        raise ValueError(f"Cannot cancel batch job in status {batch_job.status}")

    # 取消 Celery 任务
    if batch_job.celery_task_id:
        from backend.app.task.celery import celery_app

        celery_app.control.revoke(batch_job.celery_task_id, terminate=True)
        log.info(f"Revoked Celery task {batch_job.celery_task_id}")

    # 标记未开始的任务项为跳过
    result = await db.execute(
        select(BatchTaskItem).where(
            BatchTaskItem.batch_job_id == batch_id,
            BatchTaskItem.status == TaskItemStatus.PENDING.value,
        )
    )
    pending_items = result.scalars().all()
    skipped_count = len(pending_items)
    for item in pending_items:
        item.status = TaskItemStatus.SKIPPED.value
        item.completed_time = timezone.now()

    # 更新状态与统计
    batch_job.status = BatchJobStatus.CANCELLED.value
    batch_job.failed_count += skipped_count
    batch_job.pending_count = max(0, batch_job.pending_count - skipped_count)
    batch_job.updated_time = timezone.now()
    log.info(f"Cancelled batch job {batch_id}")

    return True


async def list_batch_jobs(
    db: AsyncSession,
    tenant_id: str,
    task_type: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> list[dict]:
    """查询批量任务列表"""

    query = select(BatchJob).where(BatchJob.tenant_id == tenant_id)

    if task_type:
        query = query.where(BatchJob.task_type == task_type)

    query = query.order_by(BatchJob.created_time.desc()).limit(page_size).offset((page - 1) * page_size)

    result = await db.execute(query)
    jobs = result.scalars().all()

    return [
        {
            "batch_id": job.id,
            "task_type": job.task_type,
            "name": job.name,
            "status": job.status,
            "total_count": job.total_count,
            "completed_count": job.completed_count,
            "failed_count": job.failed_count,
            "progress": (
                round((job.completed_count + job.failed_count) / job.total_count * 100, 2)
                if job.total_count > 0
                else 0
            ),
            "created_time": job.created_time,
            "celery_task_id": job.celery_task_id,
        }
        for job in jobs
    ]
