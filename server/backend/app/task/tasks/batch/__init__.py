"""批量任务 Celery 任务"""

from backend.app.task.tasks.batch.tasks import process_batch_job_task

__all__ = ["process_batch_job_task"]
