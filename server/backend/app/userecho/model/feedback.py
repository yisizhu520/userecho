from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import CheckConstraint, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.common.model import MappedBase, TimeZone
from backend.database.db import uuid4_str
from backend.utils.timezone import timezone


class Feedback(MappedBase):
    """用户反馈表"""

    __tablename__ = 'feedbacks'

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=uuid4_str, comment='反馈ID'
    )
    tenant_id: Mapped[str] = mapped_column(
        String(36), ForeignKey('tenants.id', ondelete='CASCADE'), index=True, comment='租户ID'
    )
    customer_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey('customers.id', ondelete='SET NULL'), comment='客户ID'
    )
    anonymous_author: Mapped[str | None] = mapped_column(
        String(100), default=None, comment='匿名作者名称'
    )
    anonymous_source: Mapped[str | None] = mapped_column(
        String(50), default=None, comment='匿名来源平台'
    )
    topic_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey('topics.id', ondelete='SET NULL'), index=True, comment='关联主题ID'
    )
    content: Mapped[str] = mapped_column(Text, comment='反馈内容')
    source: Mapped[str] = mapped_column(
        String(20), default='manual', comment='来源: manual, import, api, screenshot'
    )
    ai_summary: Mapped[str | None] = mapped_column(
        String(50), default=None, comment='AI生成的20字摘要'
    )
    is_urgent: Mapped[bool] = mapped_column(default=False, comment='是否紧急')
    ai_metadata: Mapped[dict | None] = mapped_column(
        JSON, default=None, comment='AI相关元数据(embedding等)'
    )
    
    # 截图识别相关字段
    screenshot_url: Mapped[str | None] = mapped_column(
        Text, default=None, comment='截图 OSS 地址'
    )
    source_platform: Mapped[str | None] = mapped_column(
        String(50), default=None, comment='来源平台: wechat, xiaohongshu, appstore, weibo, other'
    )
    source_user_name: Mapped[str | None] = mapped_column(
        String(255), default=None, comment='来源平台用户昵称'
    )
    source_user_id: Mapped[str | None] = mapped_column(
        String(255), default=None, comment='来源平台用户 ID'
    )
    ai_confidence: Mapped[float | None] = mapped_column(
        default=None, comment='AI 识别置信度 (0.00-1.00)'
    )
    submitter_id: Mapped[int | None] = mapped_column(
        ForeignKey('sys_user.id', ondelete='SET NULL'), default=None, comment='内部提交者（员工）ID'
    )
    embedding: Mapped[list[float] | None] = mapped_column(
        Vector(4096), default=None, comment='Embedding向量(pgvector, 火山引擎 4096维)'
    )

    # 情感分析字段
    sentiment: Mapped[str | None] = mapped_column(
        String(20), default=None, index=True, comment='情感倾向: positive | neutral | negative'
    )
    sentiment_score: Mapped[float | None] = mapped_column(
        default=None, comment='情感分数 (-1.0 to 1.0)'
    )
    sentiment_reason: Mapped[str | None] = mapped_column(
        Text, default=None, comment='AI 情感分析理由'
    )

    # 聚类状态与元数据（用于避免 topic_id=NULL 的噪声点被反复聚类）
    clustering_status: Mapped[str] = mapped_column(
        String(20),
        default='pending',  # pending, processing, clustered, failed
        index=True,
        comment='聚类状态: pending(待处理), processing(处理中), clustered(已聚类), failed(失败)',
    )
    clustering_metadata: Mapped[dict | None] = mapped_column(
        JSON,
        default=None,
        comment='聚类元数据: {cluster_label: int, clustered_at: datetime, quality: dict, reason: str}',
    )
    submitted_at: Mapped[datetime] = mapped_column(
        TimeZone, default=timezone.now, comment='提交时间'
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        TimeZone, default=None, comment='软删除时间'
    )
    
    # 时间戳字段
    created_time: Mapped[datetime] = mapped_column(TimeZone, default=timezone.now, comment='创建时间')
    updated_time: Mapped[datetime | None] = mapped_column(TimeZone, onupdate=timezone.now, default=None, comment='更新时间')

    __table_args__ = (
        CheckConstraint(
            'customer_id IS NOT NULL OR anonymous_author IS NOT NULL',
            name='chk_author_exists'
        ),
    )
