from datetime import datetime

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.common.model import MappedBase, TimeZone
from backend.utils.timezone import timezone


class Topic(MappedBase):
    """需求主题表（聚类结果）"""

    __tablename__ = 'topics'

    id: Mapped[str] = mapped_column(String(36), primary_key=True, comment='主题ID'
    )
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey('tenants.id', ondelete='CASCADE'), index=True, comment='租户ID'
    )
    title: Mapped[str] = mapped_column(String(100), comment='主题标题')
    category: Mapped[str] = mapped_column(String(20), default='other', comment='分类: bug, improvement, feature, performance, other'
    )
    status: Mapped[str] = mapped_column(String(20), default='pending', comment='状态: pending, planned, in_progress, completed, ignored'
    )
    description: Mapped[str | None] = mapped_column(Text, default=None, comment='详细描述')
    ai_generated: Mapped[bool] = mapped_column(default=True, comment='是否AI生成')
    ai_confidence: Mapped[float | None] = mapped_column(default=None, comment='AI置信度 (0-1)')
    feedback_count: Mapped[int] = mapped_column(default=0, comment='关联反馈数量')
    deleted_at: Mapped[datetime | None] = mapped_column(TimeZone, default=None, comment='软删除时间')
    
    # 时间戳字段
    created_time: Mapped[datetime] = mapped_column(TimeZone, default=timezone.now, comment='创建时间')
    updated_time: Mapped[datetime | None] = mapped_column(TimeZone, onupdate=timezone.now, default=None, comment='更新时间')
