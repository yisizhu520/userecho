"""任务适配器 - 将不同来源的任务转换为统一格式"""

from abc import ABC, abstractmethod

from backend.app.batch.model.batch_job import BatchJob
from backend.app.task.model.task_record import TaskRecord
from backend.app.task.schema.unified_task import TaskStatus, TaskType, UnifiedTask


class TaskAdapter(ABC):
    """任务适配器基类"""

    @abstractmethod
    def to_unified_task(self, source: any) -> UnifiedTask:
        """转换为统一的任务格式"""


class BatchJobAdapter(TaskAdapter):
    """批处理任务适配器"""

    def to_unified_task(self, batch_job: BatchJob) -> UnifiedTask:
        # 映射任务类型
        type_mapping = {
            "screenshot_recognition": TaskType.BATCH_SCREENSHOT_RECOGNITION,
            "ai_clustering": TaskType.BATCH_AI_CLUSTERING,
            "export": TaskType.BATCH_EXPORT,
        }

        # 映射状态
        status_mapping = {
            "pending": TaskStatus.PENDING,
            "processing": TaskStatus.PROCESSING,
            "completed": TaskStatus.COMPLETED,
            "failed": TaskStatus.FAILED,
            "cancelled": TaskStatus.CANCELLED,
        }

        # 计算进度
        progress = self._calculate_progress(batch_job)

        # 获取任务类型，如果映射不到则使用原值（需要确保是有效的 TaskType）
        task_type = type_mapping.get(batch_job.task_type)
        if not task_type:
            # 如果找不到映射，尝试直接使用（添加 batch_ 前缀）
            try:
                task_type = TaskType(f"batch_{batch_job.task_type}")
            except ValueError:
                # 如果还是不行，使用默认值
                task_type = TaskType.BATCH_SCREENSHOT_RECOGNITION

        return UnifiedTask(
            id=batch_job.id,
            type=task_type,
            name=batch_job.name or f"批处理任务 - {batch_job.task_type}",
            description=None,
            status=status_mapping[batch_job.status],
            progress=progress,
            created_time=batch_job.create_time,
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
        # 映射任务类型（直接使用 task_category）
        type_mapping = {
            "excel_import": TaskType.EXCEL_IMPORT,
            "clustering": TaskType.CLUSTERING,
            "screenshot_recognition": TaskType.SCREENSHOT_RECOGNITION,
            "ai_screenshot": TaskType.AI_SCREENSHOT,
            "batch": TaskType.BATCH,
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

        # 获取任务类型，如果映射不到则尝试直接使用
        task_type = type_mapping.get(task_record.task_category)
        if not task_type:
            try:
                task_type = TaskType(task_record.task_category)
            except ValueError:
                # 如果还是不行，使用默认值
                task_type = TaskType.BATCH

        return UnifiedTask(
            id=str(task_record.id),
            type=task_type,
            name=task_record.task_display_name,
            description=task_record.context.get("description") if task_record.context else None,
            status=status_mapping.get(task_record.status, TaskStatus.PENDING),
            progress=progress,
            created_time=task_record.created_time,
            started_time=task_record.started_time,
            completed_time=task_record.completed_time,
            celery_task_id=task_record.celery_task_id,
            result_summary=task_record.result_summary,
            error_message=task_record.error_message,
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
            # 如果有进度信息，从 result_summary 中读取
            if (
                task_record.result_summary
                and isinstance(task_record.result_summary, dict)
                and "progress" in task_record.result_summary
            ):
                return task_record.result_summary["progress"]
            return 50  # 默认进行中显示 50%
        return 0
