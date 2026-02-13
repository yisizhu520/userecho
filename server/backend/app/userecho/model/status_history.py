from datetime import datetime

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.common.model import MappedBase, TimeZone
from backend.utils.timezone import timezone


class StatusHistory(MappedBase):
    """状态变更历史表"""

    __tablename__ = 'status_histories'

    id: Mapped[str] = mapped_column(String(36), primary_key=True, comment='历史ID'
    )
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey('tenants.id', ondelete='CASCADE'), index=True, comment='租户ID'
    )
    topic_id: Mapped[str] = mapped_column(String(36), ForeignKey('topics.id', ondelete='CASCADE'), index=True, comment='主题ID'
    )
    from_status: Mapped[str] = mapped_column(String(20), comment='原状态')
    to_status: Mapped[str] = mapped_column(String(20), comment='新状态')
    reason: Mapped[str | None] = mapped_column(Text, default=None, comment='变更原因')
    changed_by: Mapped[int] = mapped_column(comment='操作人用户ID')
    changed_at: Mapped[datetime] = mapped_column(TimeZone, default=timezone.now, comment='变更时间')
    
    # 时间戳字段
    created_time: Mapped[datetime] = mapped_column(TimeZone, default=timezone.now, comment='创建时间')
    updated_time: Mapped[datetime | None] = mapped_column(TimeZone, onupdate=timezone.now, default=None, comment='更新时间')
