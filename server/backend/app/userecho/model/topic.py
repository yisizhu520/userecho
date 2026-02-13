from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import ForeignKey, JSON, String, Text
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

    # 聚类增量匹配/合并建议的基础：中心向量 + 质量
    centroid: Mapped[list[float] | None] = mapped_column(
        Vector(4096),
        default=None,
        comment='主题中心向量(所有反馈 embedding 的平均值, 火山引擎 4096维)',
    )
    cluster_quality: Mapped[dict | None] = mapped_column(
        JSON,
        default=None,
        comment='聚类质量: {silhouette: float, noise_ratio: float, confidence: float, avg_similarity: float}',
    )
    is_noise: Mapped[bool] = mapped_column(
        default=False,
        comment='是否为噪声主题（低质量 Topic，前端可默认隐藏）',
    )
    deleted_at: Mapped[datetime | None] = mapped_column(TimeZone, default=None, comment='软删除时间')
    
    # 时间戳字段
    created_time: Mapped[datetime] = mapped_column(TimeZone, default=timezone.now, comment='创建时间')
    updated_time: Mapped[datetime | None] = mapped_column(TimeZone, onupdate=timezone.now, default=None, comment='更新时间')
