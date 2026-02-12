from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.common.model import MappedBase as Base


class PriorityScore(Base):
    """优先级评分表"""

    __tablename__ = 'priority_scores'

    id: Mapped[str] = mapped_column(String(36), primary_key=True, comment='评分ID'
    )
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey('tenants.id', ondelete='CASCADE'), index=True, comment='租户ID'
    )
    topic_id: Mapped[str] = mapped_column(String(36), ForeignKey('topics.id', ondelete='CASCADE'), index=True, comment='主题ID'
    )
    impact_scope: Mapped[int] = mapped_column(default=1, comment='影响范围 (1-10)')
    business_value: Mapped[int] = mapped_column(default=1, comment='商业价值 (1-10)')
    dev_cost: Mapped[int] = mapped_column(default=1, comment='开发成本 (1-10)')
    urgency_factor: Mapped[float] = mapped_column(default=1.0, comment='紧急系数 (1.0-2.0)')
    total_score: Mapped[float] = mapped_column(default=0.0, comment='总分: (影响 × 价值) / 成本 × 紧急系数')
