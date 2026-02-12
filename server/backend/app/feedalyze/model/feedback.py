from datetime import datetime

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
        String(20), default='manual', comment='来源: manual, import, api'
    )
    ai_summary: Mapped[str | None] = mapped_column(
        String(50), default=None, comment='AI生成的20字摘要'
    )
    is_urgent: Mapped[bool] = mapped_column(default=False, comment='是否紧急')
    ai_metadata: Mapped[dict | None] = mapped_column(
        JSON, default=None, comment='AI相关元数据(embedding等)'
    )
    embedding: Mapped[str | None] = mapped_column(
        Text, default=None, comment='Embedding向量(pgvector VECTOR(768),存储为文本)'
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
