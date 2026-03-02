"""批量任务 Celery 任务实现"""

import asyncio
from contextlib import asynccontextmanager
from typing import Any

from celery import shared_task
from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from backend.app.batch.handler.base import get_task_handler
from backend.app.batch.model.batch_job import BatchJob, BatchJobStatus, BatchTaskItem, TaskItemStatus
from backend.common.log import log
from backend.core.conf import settings
from backend.database.db import create_database_url
from backend.utils.timezone import timezone


# Celery Worker 专用的异步数据库引擎（每个 worker 一个）
_celery_async_engine: AsyncEngine | None = None
_celery_async_session: async_sessionmaker[AsyncSession] | None = None


def get_celery_db_session() -> async_sessionmaker[AsyncSession]:
    """
    获取 Celery Worker 专用的异步数据库 Session Factory

    为每个 Celery Worker 进程创建独立的异步引擎，避免跨 loop 冲突
    """
    global _celery_async_engine, _celery_async_session

    if _celery_async_engine is None:
        db_url = create_database_url()

        _celery_async_engine = create_async_engine(
            db_url,
            echo=settings.DATABASE_ECHO,
            pool_size=5,
            max_overflow=10,
            pool_timeout=30,
            pool_recycle=3600,
            pool_pre_ping=True,
        )

        _celery_async_session = async_sessionmaker(
            bind=_celery_async_engine,
            class_=AsyncSession,
            autoflush=False,
            expire_on_commit=True,
        )

        log.info("[Celery] Created async database engine for worker")

    return _celery_async_session


@asynccontextmanager
async def local_db_session():
    """创建本地数据库会话（用于 Celery 任务）"""
    session_factory = get_celery_db_session()
    async with session_factory() as session:
        async with session.begin():
            yield session


@shared_task(
    name="batch.process_batch_job",
    bind=True,
    time_limit=3600,  # 1小时硬超时
    soft_time_limit=3300,  # 55分钟软超时
)
async def process_batch_job_task(
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

    # 1. 获取批量任务并更新状态
    async with local_db_session() as db:
        batch_job = await db.get(BatchJob, batch_job_id)
        if not batch_job:
            raise ValueError(f"Batch job {batch_job_id} not found")

        log.info(f"[Task {self.request.id}] Starting batch job: {batch_job_id} ({batch_job.task_type})")

        batch_job.status = BatchJobStatus.PROCESSING.value
        batch_job.started_time = timezone.now()
        batch_job.celery_task_id = self.request.id

        # 2. 获取任务处理器
        handler = get_task_handler(batch_job.task_type)

        # 3. 调用 on_batch_start 钩子
        try:
            await handler.on_batch_start(batch_job, db)
        except Exception as e:
            log.error(f"[Task {self.request.id}] on_batch_start failed: {e}")

    # 4. 执行所有任务项
    await _execute_all_task_items(self, batch_job_id)

    # 5. 完成批量任务
    return await _complete_batch_job(self, batch_job_id)


async def _execute_all_task_items(task_self: Any, batch_job_id: str):
    """执行所有任务项（分批处理）"""

    batch_size = 10  # 每次处理10个任务项

    while True:
        task_item_ids = await _claim_task_items(batch_job_id, batch_size)
        if not task_item_ids:
            break

        log.info(f"[Task {task_self.request.id}] Processing {len(task_item_ids)} task items")

        # 并发处理任务项（使用 asyncio.gather）
        tasks = [_process_single_task_item(task_item_id, batch_job_id) for task_item_id in task_item_ids]
        await asyncio.gather(*tasks, return_exceptions=True)


async def _claim_task_items(batch_job_id: str, batch_size: int) -> list[str]:
    """原子领取待处理任务项（避免重复处理）"""
    async with local_db_session() as db:
        result = await db.execute(select(BatchJob).where(BatchJob.id == batch_job_id).with_for_update())
        batch_job = result.scalars().first()
        if not batch_job or batch_job.status == BatchJobStatus.CANCELLED.value:
            return []

        result = await db.execute(
            select(BatchTaskItem)
            .where(BatchTaskItem.batch_job_id == batch_job_id)
            .where(BatchTaskItem.status == TaskItemStatus.PENDING.value)
            .order_by(BatchTaskItem.sequence_no)
            .with_for_update(skip_locked=True)
            .limit(batch_size)
        )
        task_items = list(result.scalars().all())
        if not task_items:
            return []

        now = timezone.now()
        for task_item in task_items:
            task_item.status = TaskItemStatus.PROCESSING.value
            task_item.started_time = now

        claimed = len(task_items)
        batch_job.pending_count = max(0, batch_job.pending_count - claimed)
        batch_job.processing_count += claimed
        batch_job.update_time = now

        return [task_item.id for task_item in task_items]


async def _process_single_task_item(task_item_id: str, batch_job_id: str):
    """处理单个任务项"""

    # 2. 执行任务处理器
    try:
        async with local_db_session() as db:
            task_item = await db.get(BatchTaskItem, task_item_id)
            batch_job = await db.get(BatchJob, batch_job_id)

            if not task_item or not batch_job:
                return

            if batch_job.status == BatchJobStatus.CANCELLED.value:
                previous_status = task_item.status
                if previous_status not in [
                    TaskItemStatus.COMPLETED.value,
                    TaskItemStatus.FAILED.value,
                    TaskItemStatus.SKIPPED.value,
                ]:
                    task_item.status = TaskItemStatus.SKIPPED.value
                    task_item.completed_time = timezone.now()
                    if previous_status == TaskItemStatus.PROCESSING.value:
                        batch_job.processing_count = max(0, batch_job.processing_count - 1)
                    elif previous_status == TaskItemStatus.PENDING.value:
                        batch_job.pending_count = max(0, batch_job.pending_count - 1)
                    batch_job.failed_count += 1
                    batch_job.update_time = timezone.now()
                return

            if task_item.status != TaskItemStatus.PROCESSING.value:
                return

            handler = get_task_handler(batch_job.task_type)

            # 执行任务
            output_data = await handler.process(task_item, db)

            # 更新成功状态
            task_item.status = TaskItemStatus.COMPLETED.value
            task_item.output_data = output_data
            task_item.completed_time = timezone.now()

            # 更新批量任务统计
            batch_job.processing_count -= 1
            batch_job.completed_count += 1
            batch_job.update_time = timezone.now()

            # 调用进度钩子
            try:
                await handler.on_batch_progress(batch_job, db)
            except Exception as e:
                log.warning(f"on_batch_progress failed: {e}")

    except Exception as e:
        # 3. 处理失败
        async with local_db_session() as db:
            task_item = await db.get(BatchTaskItem, task_item_id)
            batch_job = await db.get(BatchJob, batch_job_id)

            if not task_item or not batch_job:
                return

            task_item.retry_count += 1

            # 判断是否需要重试
            if task_item.retry_count < task_item.max_retries:
                task_item.status = TaskItemStatus.PENDING.value
                batch_job.processing_count -= 1
                batch_job.pending_count += 1
                log.warning(
                    f"Task item {task_item_id} failed, will retry "
                    f"({task_item.retry_count}/{task_item.max_retries}): {e}"
                )
            else:
                task_item.status = TaskItemStatus.FAILED.value
                task_item.error_message = str(e)
                task_item.error_code = type(e).__name__
                task_item.completed_time = timezone.now()
                batch_job.processing_count -= 1
                batch_job.failed_count += 1
                log.error(f"Task item {task_item_id} failed permanently: {e}")

            batch_job.update_time = timezone.now()


async def _complete_batch_job(task_self: Any, batch_job_id: str) -> dict:
    """完成批量任务"""

    async with local_db_session() as db:
        batch_job = await db.get(BatchJob, batch_job_id)

        if not batch_job:
            return {
                "batch_job_id": batch_job_id,
                "total": 0,
                "completed": 0,
                "failed": 0,
                "status": "missing",
            }

        log.info(f"[Task {task_self.request.id}] Completing batch job: {batch_job_id}")

        if batch_job.status == BatchJobStatus.CANCELLED.value:
            batch_job.completed_time = timezone.now()
            batch_job.update_time = timezone.now()
            await db.commit()
            return {
                "batch_job_id": batch_job.id,
                "total": batch_job.total_count,
                "completed": batch_job.completed_count,
                "failed": batch_job.failed_count,
                "status": batch_job.status,
            }

        # 调用 on_batch_complete 钩子
        try:
            handler = get_task_handler(batch_job.task_type)
            await handler.on_batch_complete(batch_job, db)
        except Exception as e:
            log.error(f"[Task {task_self.request.id}] on_batch_complete failed: {e}")

        # 更新批量任务状态
        if batch_job.failed_count > 0 and batch_job.completed_count == 0:
            batch_job.status = BatchJobStatus.FAILED.value
        else:
            batch_job.status = BatchJobStatus.COMPLETED.value

        batch_job.completed_time = timezone.now()
        batch_job.update_time = timezone.now()

        log.info(
            f"[Task {task_self.request.id}] Batch job {batch_job_id} completed: "
            f"{batch_job.completed_count} succeeded, {batch_job.failed_count} failed"
        )

        # FIXME: task_notification 在 Celery Worker 中会导致 event loop 冲突
        # 临时注释，后续使用同步 Redis Pub/Sub 实现
        # try:
        #     from backend.common.socketio.actions import task_notification
        #     await task_notification(
        #         msg=f"批量任务完成：{batch_job.name}（成功 {batch_job.completed_count} 个，失败 {batch_job.failed_count} 个）"
        #     )
        # except Exception as e:
        #     log.warning(f"Failed to send task notification: {e}")

        return {
            "batch_job_id": batch_job.id,
            "total": batch_job.total_count,
            "completed": batch_job.completed_count,
            "failed": batch_job.failed_count,
            "status": batch_job.status,
        }
