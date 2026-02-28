"""批量任务处理器基类"""

from abc import ABC, abstractmethod
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.batch.model.batch_job import BatchJob, BatchTaskItem


class BatchTaskHandler(ABC):
    """批量任务处理器基类"""

    @abstractmethod
    async def process(self, task_item: BatchTaskItem, db: AsyncSession) -> dict[str, Any]:
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
_task_handlers: dict[str, BatchTaskHandler] = {}


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


def batch_task_handler(task_type: str):
    """任务处理器装饰器"""

    def decorator(handler_class: type[BatchTaskHandler]):
        register_task_handler(task_type, handler_class())
        return handler_class

    return decorator
