from datetime import datetime

from sqlalchemy import JSON, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.common.model import MappedBase, TimeZone
from backend.utils.timezone import timezone


class PriorityScore(MappedBase):
    """优先级评分表"""

    __tablename__ = 'priority_scores'

    id: Mapped[str] = mapped_column(String(36), primary_key=True, comment='评分ID')
    tenant_id: Mapped[str] = mapped_column(
        String(36), ForeignKey('tenants.id', ondelete='CASCADE'), index=True, comment='租户ID'
    )
    topic_id: Mapped[str] = mapped_column(
        String(36), ForeignKey('topics.id', ondelete='CASCADE'), index=True, comment='主题ID'
    )
    impact_scope: Mapped[int] = mapped_column(default=1, comment='影响范围 (1-10)')
    business_value: Mapped[int] = mapped_column(default=1, comment='商业价值 (1-10)')
    dev_cost: Mapped[int] = mapped_column(default=1, comment='开发成本 (1-10)')
    urgency_factor: Mapped[float] = mapped_column(default=1.0, comment='紧急系数 (1.0-2.0)')
    total_score: Mapped[float] = mapped_column(default=0.0, comment='总分: (影响 × 价值) / 成本 × 紧急系数')
    details: Mapped[dict | None] = mapped_column(JSON, default=None, comment='详细计算结果')

    # 时间戳字段
    created_time: Mapped[datetime] = mapped_column(TimeZone, default=timezone.now, comment='创建时间')
    updated_time: Mapped[datetime | None] = mapped_column(
        TimeZone, onupdate=timezone.now, default=None, comment='更新时间'
    )

    # 关联关系
    topic: Mapped['Topic'] = relationship(
        'Topic',
        back_populates='priority_score',
    )
