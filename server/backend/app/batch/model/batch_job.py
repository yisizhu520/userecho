"""批量任务模型定义"""

from datetime import datetime
import enum
from sqlalchemy import JSON, Integer, String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.common.model import MappedBase, TimeZone
from backend.utils.uuid import uuid4_str


class BatchJobStatus(str, enum.Enum):
    """批量任务状态"""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskItemStatus(str, enum.Enum):
    """任务项状态"""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class BatchJob(MappedBase):
    """批量任务（通用）"""

    __tablename__ = "batch_job"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4_str, comment="主键ID")

    # 必填字段（没有默认值）
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True, comment="租户ID")
    task_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True, comment="任务类型")

    # 有默认值的字段
    status: Mapped[str] = mapped_column(
        String(20), default=BatchJobStatus.PENDING.value, nullable=False, index=True, comment="任务状态"
    )
    total_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="总任务数")
    pending_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="待处理数")
    processing_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="处理中数")
    completed_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="已完成数")
    failed_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="失败数")
    config: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False, comment="执行配置")
    summary: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False, comment="结果汇总")

    # 可选字段（显式设置 default=None）
    name: Mapped[str | None] = mapped_column(String(200), default=None, comment="任务名称")
    description: Mapped[str | None] = mapped_column(Text, default=None, comment="任务描述")
    created_by: Mapped[str | None] = mapped_column(String(36), default=None, comment="创建者ID")
    celery_task_id: Mapped[str | None] = mapped_column(String(255), default=None, index=True, comment="Celery任务ID")
    started_time: Mapped[datetime | None] = mapped_column(default=None, comment="开始时间")
    completed_time: Mapped[datetime | None] = mapped_column(default=None, comment="完成时间")

    # 时间戳字段（手动添加）
    create_time: Mapped[datetime] = mapped_column(TimeZone, nullable=False, comment="创建时间")
    update_time: Mapped[datetime] = mapped_column(TimeZone, nullable=False, comment="更新时间")

    # 关联任务项
    task_items: Mapped[list["BatchTaskItem"]] = relationship(
        back_populates="batch_job",
        cascade="all, delete-orphan",
    )


class BatchTaskItem(MappedBase):
    """任务项（通用）"""

    __tablename__ = "batch_task_item"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4_str, comment="主键ID")

    # 必填字段（没有默认值）
    batch_job_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("batch_job.id", ondelete="CASCADE"), nullable=False, index=True, comment="批量任务ID"
    )
    input_data: Mapped[dict] = mapped_column(JSON, nullable=False, comment="输入数据")

    # 有默认值的字段
    status: Mapped[str] = mapped_column(
        String(20), default=TaskItemStatus.PENDING.value, nullable=False, index=True, comment="任务状态"
    )
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="重试次数")
    max_retries: Mapped[int] = mapped_column(Integer, default=3, nullable=False, comment="最大重试次数")

    # 可选字段（显式设置 default=None）
    sequence_no: Mapped[int | None] = mapped_column(Integer, default=None, comment="执行顺序")
    output_data: Mapped[dict | None] = mapped_column(JSON, default=None, comment="输出数据")
    error_message: Mapped[str | None] = mapped_column(Text, default=None, comment="错误信息")
    error_code: Mapped[str | None] = mapped_column(String(50), default=None, comment="错误码")
    started_time: Mapped[datetime | None] = mapped_column(default=None, comment="开始时间")
    completed_time: Mapped[datetime | None] = mapped_column(default=None, comment="完成时间")

    # 时间戳字段（手动添加）
    create_time: Mapped[datetime] = mapped_column(TimeZone, nullable=False, comment="创建时间")
    update_time: Mapped[datetime] = mapped_column(TimeZone, nullable=False, comment="更新时间")

    # 关联批量任务
    batch_job: Mapped["BatchJob"] = relationship(back_populates="task_items")
