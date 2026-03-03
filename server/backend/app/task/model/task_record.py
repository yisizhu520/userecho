"""统一任务追踪记录模型

所有 Celery 异步任务（单任务 + 批量任务）的审计日志。
解决 Celery task_result 表缺乏业务上下文（tenant_id、任务分类、可读名称）的问题。
"""

from datetime import datetime

from sqlalchemy import JSON, BigInteger, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.common.model import MappedBase, TimeZone
from backend.utils.timezone import timezone


class TaskRecord(MappedBase):
    """统一任务追踪记录"""

    __tablename__ = "task_record"
    __table_args__ = (
        Index("idx_task_record_tenant_time", "tenant_id", "created_time", postgresql_ops={}),
        Index("idx_task_record_category_time", "task_category", "created_time", postgresql_ops={}),
        Index(
            "idx_task_record_status_pending",
            "status",
            postgresql_where="status NOT IN ('success')",
        ),
        {"comment": "统一任务追踪记录"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="自增主键")

    # 业务上下文
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True, comment="租户ID")
    task_category: Mapped[str] = mapped_column(String(50), nullable=False, comment="任务分类")
    task_display_name: Mapped[str] = mapped_column(String(100), nullable=False, comment="任务可读名称")

    # Celery 关联
    celery_task_id: Mapped[str] = mapped_column(String(155), nullable=False, unique=True, comment="Celery任务ID")
    celery_task_name: Mapped[str] = mapped_column(String(155), nullable=False, comment="Celery任务注册名")

    # 状态
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending", comment="任务状态")

    # 业务参数（关键上下文，不是全量参数）
    context: Mapped[dict | None] = mapped_column(JSON, default=None, comment="业务上下文")

    # 结果摘要
    result_summary: Mapped[dict | None] = mapped_column(JSON, default=None, comment="结果摘要")

    # 关联批量任务
    batch_job_id: Mapped[str | None] = mapped_column(String(36), default=None, index=True, comment="关联批量任务ID")

    # 性能追踪
    duration_ms: Mapped[int | None] = mapped_column(Integer, default=None, comment="执行耗时(ms)")

    # 错误信息
    error_message: Mapped[str | None] = mapped_column(Text, default=None, comment="错误信息")

    # 时间戳
    created_time: Mapped[datetime] = mapped_column(TimeZone, nullable=False, default=timezone.now, comment="创建时间")
    started_time: Mapped[datetime | None] = mapped_column(TimeZone, default=None, comment="开始时间")
    completed_time: Mapped[datetime | None] = mapped_column(TimeZone, default=None, comment="完成时间")
