"""批量任务处理器"""

from backend.app.batch.handler.base import (
    BatchTaskHandler,
    batch_task_handler,
    get_task_handler,
    list_task_handlers,
    register_task_handler,
)

# 导入所有处理器模块以触发装饰器注册
from backend.app.batch.handler import screenshot_recognition  # noqa: F401

__all__ = [
    "BatchTaskHandler",
    "batch_task_handler",
    "get_task_handler",
    "list_task_handlers",
    "register_task_handler",
]
