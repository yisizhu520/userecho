"""批量任务处理器"""

from backend.app.batch.handler.base import (
    BatchTaskHandler,
    batch_task_handler,
    get_task_handler,
    list_task_handlers,
    register_task_handler,
)

__all__ = [
    "BatchTaskHandler",
    "batch_task_handler",
    "get_task_handler",
    "list_task_handlers",
    "register_task_handler",
]
