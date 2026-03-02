import time
from typing import Any

from celery import Task
from sqlalchemy.exc import SQLAlchemyError

from backend.core.conf import settings


class TaskBase(Task):
    """Celery 任务基类 — 自动追踪所有任务执行

    利用 Celery 钩子机制，零侵入地为所有任务写审计日志。
    追踪记录的写入失败绝不影响业务任务执行。
    """

    autoretry_for = (SQLAlchemyError,)
    max_retries = settings.CELERY_TASK_MAX_RETRIES

    # 运行时：记录任务开始时间用于计算 duration
    _started_at: float | None = None

    def before_start(self, task_id: str, args: tuple, kwargs: dict) -> None:
        """任务开始 → 写 task_record"""
        self._started_at = time.time()
        try:
            from backend.app.task.registry import extract_context, extract_tenant_id, get_task_meta
            from backend.app.task.tracker import create_task_record

            meta = get_task_meta(self.name)
            if meta is None:
                return  # 未注册的任务不追踪（demo 等）

            tenant_id = extract_tenant_id(meta, args, kwargs) or "system"
            context = extract_context(meta, args, kwargs)
            batch_job_id = context.pop("batch_job_id", None) if meta.category == "batch" else None

            create_task_record(
                celery_task_id=task_id,
                celery_task_name=self.name,
                task_category=meta.category,
                task_display_name=meta.display_name,
                tenant_id=tenant_id,
                status="started",
                context=context or None,
                batch_job_id=batch_job_id,
            )
        except Exception:
            pass  # 追踪失败不影响业务

    def on_success(self, retval: Any, task_id: str, args: tuple, kwargs: dict) -> None:
        """任务成功 → 更新 task_record"""
        try:
            from backend.app.task.registry import get_task_meta
            from backend.app.task.tracker import update_task_record_success

            meta = get_task_meta(self.name)
            if meta is None:
                return

            update_task_record_success(
                celery_task_id=task_id,
                result_summary=_safe_summarize(retval),
                started_at=self._started_at,
            )
        except Exception:
            pass

    def on_failure(self, exc: Exception, task_id: str, args: tuple, kwargs: dict, einfo: Any) -> None:
        """任务失败 → 更新 task_record"""
        try:
            from backend.app.task.registry import get_task_meta
            from backend.app.task.tracker import update_task_record_failure

            meta = get_task_meta(self.name)
            if meta is None:
                return

            update_task_record_failure(
                celery_task_id=task_id,
                error_message=str(exc),
                result_summary={"error_type": type(exc).__name__},
                started_at=self._started_at,
            )
        except Exception:
            pass

    def on_retry(self, exc: Exception, task_id: str, args: tuple, kwargs: dict, einfo: Any) -> None:
        """任务重试 → 更新 task_record"""
        try:
            from backend.app.task.registry import get_task_meta
            from backend.app.task.tracker import update_task_record_retry

            meta = get_task_meta(self.name)
            if meta is None:
                return

            update_task_record_retry(
                celery_task_id=task_id,
                retry_count=self.request.retries or 0,
                error_message=str(exc),
            )
        except Exception:
            pass


def _safe_summarize(retval: Any) -> dict | None:
    """安全提取返回值摘要，截断大结果"""
    if retval is None:
        return None
    if isinstance(retval, dict):
        # 只保留关键字段，避免存储大量数据
        summary = {}
        for key in ("success", "status", "feedback_id", "topic_id", "batch_job_id", "total", "completed", "failed"):
            if key in retval:
                summary[key] = retval[key]
        # 如果没有匹配的标准字段，取前 5 个键
        if not summary:
            for i, (k, v) in enumerate(retval.items()):
                if i >= 5:
                    break
                summary[k] = str(v)[:200] if not isinstance(v, (int, float, bool)) else v
        return summary
    if isinstance(retval, str):
        return {"result": retval[:200]}
    return {"result": str(retval)[:200]}
