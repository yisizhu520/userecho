from datetime import datetime

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.common.model import MappedBase, TimeZone
from backend.utils.timezone import timezone


class ManualAdjustment(MappedBase):
    """人工调整记录表"""

    __tablename__ = 'manual_adjustments'

    id: Mapped[str] = mapped_column(String(36), primary_key=True, comment='调整ID')
    tenant_id: Mapped[str] = mapped_column(
        String(36), ForeignKey('tenants.id', ondelete='CASCADE'), index=True, comment='租户ID'
    )
    feedback_id: Mapped[str] = mapped_column(
        String(36), ForeignKey('feedbacks.id', ondelete='CASCADE'), index=True, comment='反馈ID'
    )
    original_topic_id: Mapped[str | None] = mapped_column(String(36), default=None, comment='原主题ID')
    new_topic_id: Mapped[str | None] = mapped_column(String(36), default=None, comment='新主题ID')
    adjustment_type: Mapped[str] = mapped_column(String(20), comment='调整类型: move, merge, split')
    reason: Mapped[str | None] = mapped_column(Text, default=None, comment='调整原因')
    adjusted_by: Mapped[int] = mapped_column(comment='操作人用户ID')
    adjusted_at: Mapped[datetime] = mapped_column(TimeZone, default=timezone.now, comment='调整时间')

    # 时间戳字段
    created_time: Mapped[datetime] = mapped_column(TimeZone, default=timezone.now, comment='创建时间')
    updated_time: Mapped[datetime | None] = mapped_column(
        TimeZone, onupdate=timezone.now, default=None, comment='更新时间'
    )
