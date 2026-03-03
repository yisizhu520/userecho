"""统一任务 DTO Schema"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class TaskType(str, Enum):
    """任务类型"""

    # 批处理任务
    BATCH_SCREENSHOT_RECOGNITION = "batch_screenshot_recognition"
    BATCH_AI_CLUSTERING = "batch_ai_clustering"
    BATCH_EXPORT = "batch_export"

    # 单任务
    EXCEL_IMPORT = "excel_import"
    CLUSTERING = "clustering"
    SCREENSHOT_RECOGNITION = "screenshot_recognition"
    AI_SCREENSHOT = "ai_screenshot"  # AI截图分析
    BATCH = "batch"  # 通用批处理任务


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
