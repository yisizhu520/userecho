from datetime import date, datetime
from decimal import Decimal

from pgvector.sqlalchemy import Vector
from sqlalchemy import JSON, Date, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.common.model import MappedBase, TimeZone
from backend.utils.timezone import timezone


class Topic(MappedBase):
    """需求主题表（聚类结果）"""

    __tablename__ = 'topics'

    id: Mapped[str] = mapped_column(String(36), primary_key=True, comment='主题ID')
    tenant_id: Mapped[str] = mapped_column(
        String(36), ForeignKey('tenants.id', ondelete='CASCADE'), index=True, comment='租户ID'
    )
    board_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey('boards.id', ondelete='CASCADE'), index=True, default=None, comment='看板ID'
    )

    # Topic 基础信息
    title: Mapped[str] = mapped_column(String(200), comment='主题标题')
    category: Mapped[str] = mapped_column(
        String(50), default='other', comment='分类: bug, improvement, feature, performance, other'
    )
    status: Mapped[str] = mapped_column(
        String(20), default='pending', comment='状态: pending, planned, in_progress, completed, ignored'
    )
    description: Mapped[str | None] = mapped_column(Text, default=None, comment='详细描述')
    ai_generated: Mapped[bool] = mapped_column(default=True, comment='是否AI生成')
    ai_confidence: Mapped[float | None] = mapped_column(default=None, comment='AI置信度 (0-1)')
    feedback_count: Mapped[int] = mapped_column(default=0, comment='关联反馈数量')

    # 权重聚合字段（基于关联的 Feedback 自动计算，通过触发器更新）
    affected_customer_count: Mapped[int] = mapped_column(default=0, comment='受影响客户数量（去重）')
    total_mrr: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0, comment='关联客户 MRR 总和')
    total_arr: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0, comment='关联客户 ARR 总和')
    avg_sentiment_score: Mapped[float | None] = mapped_column(default=None, comment='平均情感分数')
    high_risk_customer_count: Mapped[int] = mapped_column(default=0, comment='高流失风险客户数量')

    # 产品经理评估字段
    impact_scope: Mapped[int | None] = mapped_column(default=None, comment='影响范围评分 (1-10)')
    dev_cost_estimate: Mapped[int | None] = mapped_column(default=None, comment='开发成本评分 (1-10)')
    product_owner_id: Mapped[int | None] = mapped_column(
        ForeignKey('sys_user.id', ondelete='SET NULL'), default=None, comment='产品负责人'
    )
    tech_lead_id: Mapped[int | None] = mapped_column(
        ForeignKey('sys_user.id', ondelete='SET NULL'), default=None, comment='技术负责人'
    )
    estimated_release_date: Mapped[date | None] = mapped_column(Date, default=None, comment='预计发布日期')
    actual_release_date: Mapped[date | None] = mapped_column(Date, default=None, comment='实际发布日期')

    # 外部集成
    jira_issue_key: Mapped[str | None] = mapped_column(String(50), default=None, comment='Jira Issue Key')
    tapd_story_id: Mapped[str | None] = mapped_column(String(50), default=None, comment='Tapd Story ID')

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

    # 公开访问（可选）
    slug: Mapped[str | None] = mapped_column(String(200), unique=True, default=None, comment='公开访问 slug')
    is_public: Mapped[bool] = mapped_column(default=False, comment='是否公开')

    deleted_at: Mapped[datetime | None] = mapped_column(TimeZone, default=None, comment='软删除时间')

    # 时间戳字段
    created_time: Mapped[datetime] = mapped_column(TimeZone, default=timezone.now, comment='创建时间')
    updated_time: Mapped[datetime | None] = mapped_column(
        TimeZone, onupdate=timezone.now, default=None, comment='更新时间'
    )

    # 关联关系
    priority_score: Mapped['PriorityScore'] = relationship(
        'PriorityScore',
        back_populates='topic',
        uselist=False,
        lazy='joined',
    )
