"""任务追踪记录的同步数据库写入器

在 Celery Worker 的 TaskBase 钩子中调用。
钩子是同步的（on_failure 必须是 sync），所以使用 psycopg 同步驱动。

设计原则：
- 追踪记录的写入失败 **绝不** 影响业务任务执行
- 所有操作都包裹在 try/except 中
- 使用独立连接池，不与异步引擎冲突
"""

import time

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from backend.common.log import log
from backend.core.conf import settings

# 模块级同步引擎（延迟初始化，Celery Worker 专用）
_sync_engine: Engine | None = None
_sync_session_factory: sessionmaker[Session] | None = None


def _get_sync_session() -> Session:
    """获取同步数据库会话（延迟初始化）"""
    global _sync_engine, _sync_session_factory

    if _sync_engine is None:
        import urllib.parse

        password = urllib.parse.quote(settings.DATABASE_PASSWORD)
        url = (
            f"postgresql+psycopg://{settings.DATABASE_USER}:{password}"
            f"@{settings.DATABASE_HOST}:{settings.DATABASE_PORT}/{settings.DATABASE_SCHEMA}"
        )
        _sync_engine = create_engine(
            url,
            echo=False,
            pool_size=2,
            max_overflow=3,
            pool_timeout=10,
            pool_recycle=3600,
            pool_pre_ping=True,
        )
        _sync_session_factory = sessionmaker(bind=_sync_engine, expire_on_commit=True)
        log.info("[TaskTracker] Sync database engine initialized")

    return _sync_session_factory()


def create_task_record(
    *,
    celery_task_id: str,
    celery_task_name: str,
    task_category: str,
    task_display_name: str,
    tenant_id: str,
    status: str = "started",
    context: dict | None = None,
    batch_job_id: str | None = None,
) -> None:
    """
    创建任务追踪记录（同步写入，Celery Worker 调用）

    失败不抛异常，只记日志。
    """
    try:
        with _get_sync_session() as session:
            with session.begin():
                session.execute(
                    text("""
                        INSERT INTO task_record (
                            tenant_id, task_category, task_display_name,
                            celery_task_id, celery_task_name, status,
                            context, batch_job_id,
                            created_time, started_time
                        ) VALUES (
                            :tenant_id, :task_category, :task_display_name,
                            :celery_task_id, :celery_task_name, :status,
                            CAST(:context AS jsonb), :batch_job_id,
                            NOW(), NOW()
                        )
                        ON CONFLICT (celery_task_id) DO UPDATE SET
                            status = EXCLUDED.status,
                            started_time = EXCLUDED.started_time
                    """),
                    {
                        "tenant_id": tenant_id,
                        "task_category": task_category,
                        "task_display_name": task_display_name,
                        "celery_task_id": celery_task_id,
                        "celery_task_name": celery_task_name,
                        "status": status,
                        "context": _safe_json(context),
                        "batch_job_id": batch_job_id,
                    },
                )
    except Exception as e:
        log.warning(f"[TaskTracker] Failed to create task record for {celery_task_id}: {e}")


def update_task_record_success(
    *,
    celery_task_id: str,
    result_summary: dict | None = None,
    started_at: float | None = None,
) -> None:
    """更新任务记录为成功状态"""
    try:
        duration_ms = int((time.time() - started_at) * 1000) if started_at else None
        with _get_sync_session() as session:
            with session.begin():
                session.execute(
                    text("""
                        UPDATE task_record SET
                            status = 'success',
                            result_summary = CAST(:result_summary AS jsonb),
                            duration_ms = :duration_ms,
                            completed_time = NOW()
                        WHERE celery_task_id = :celery_task_id
                    """),
                    {
                        "celery_task_id": celery_task_id,
                        "result_summary": _safe_json(result_summary),
                        "duration_ms": duration_ms,
                    },
                )
    except Exception as e:
        log.warning(f"[TaskTracker] Failed to update success for {celery_task_id}: {e}")


def update_task_record_failure(
    *,
    celery_task_id: str,
    error_message: str,
    result_summary: dict | None = None,
    started_at: float | None = None,
) -> None:
    """更新任务记录为失败状态"""
    try:
        duration_ms = int((time.time() - started_at) * 1000) if started_at else None
        with _get_sync_session() as session:
            with session.begin():
                session.execute(
                    text("""
                        UPDATE task_record SET
                            status = 'failure',
                            error_message = :error_message,
                            result_summary = CAST(:result_summary AS jsonb),
                            duration_ms = :duration_ms,
                            completed_time = NOW()
                        WHERE celery_task_id = :celery_task_id
                    """),
                    {
                        "celery_task_id": celery_task_id,
                        "error_message": error_message[:2000],  # 截断避免过长
                        "result_summary": _safe_json(result_summary),
                        "duration_ms": duration_ms,
                    },
                )
    except Exception as e:
        log.warning(f"[TaskTracker] Failed to update failure for {celery_task_id}: {e}")


def update_task_record_retry(
    *,
    celery_task_id: str,
    retry_count: int,
    error_message: str,
) -> None:
    """更新任务记录为重试状态"""
    try:
        with _get_sync_session() as session:
            with session.begin():
                session.execute(
                    text("""
                        UPDATE task_record SET
                            status = 'retry',
                            error_message = :error_message,
                            result_summary = jsonb_build_object('retry_count', :retry_count)
                        WHERE celery_task_id = :celery_task_id
                    """),
                    {
                        "celery_task_id": celery_task_id,
                        "error_message": error_message[:2000],
                        "retry_count": retry_count,
                    },
                )
    except Exception as e:
        log.warning(f"[TaskTracker] Failed to update retry for {celery_task_id}: {e}")


def _safe_json(data: dict | None) -> str | None:
    """安全序列化为 JSON 字符串"""
    if data is None:
        return None
    try:
        import json

        return json.dumps(data, ensure_ascii=False, default=str)
    except Exception:
        return "{}"
