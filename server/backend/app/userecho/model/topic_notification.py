from datetime import datetime

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.common.model import MappedBase, TimeZone
from backend.database.db import uuid4_str
from backend.utils.timezone import timezone


class TopicNotification(MappedBase):
    """需求通知记录表（Topic 完成后通知反馈提交人）"""

    __tablename__ = 'topic_notifications'

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4_str, comment='通知记录ID')
    tenant_id: Mapped[str] = mapped_column(
        String(36), ForeignKey('tenants.id', ondelete='CASCADE'), index=True, comment='租户ID'
    )
    topic_id: Mapped[str] = mapped_column(
        String(36), ForeignKey('topics.id', ondelete='CASCADE'), index=True, comment='关联议题ID'
    )
    feedback_id: Mapped[str] = mapped_column(
        String(36), ForeignKey('feedbacks.id', ondelete='CASCADE'), index=True, comment='关联反馈ID'
    )
    customer_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey('customers.id', ondelete='SET NULL'), default=None, comment='关联客户ID'
    )

    # 收件人信息
    recipient_name: Mapped[str] = mapped_column(String(100), comment='收件人名称')
    recipient_contact: Mapped[str | None] = mapped_column(String(255), default=None, comment='联系方式')
    recipient_type: Mapped[str] = mapped_column(String(20), default='customer', comment='收件人类型: customer/external')

    # AI 回复相关
    ai_reply: Mapped[str | None] = mapped_column(Text, default=None, comment='AI 生成的回复内容')
    reply_tone: Mapped[str] = mapped_column(String(20), default='friendly', comment='回复语气: formal/friendly/concise')
    reply_language: Mapped[str] = mapped_column(String(10), default='zh-CN', comment='回复语言')

    # 通知状态
    status: Mapped[str] = mapped_column(
        String(20), default='pending', index=True, comment='状态: pending/generated/copied/sent'
    )
    notified_at: Mapped[datetime | None] = mapped_column(TimeZone, default=None, comment='标记为已通知的时间')
    notified_by: Mapped[int | None] = mapped_column(
        ForeignKey('sys_user.id', ondelete='SET NULL'), default=None, comment='操作人员ID'
    )
    notification_channel: Mapped[str | None] = mapped_column(
        String(50), default=None, comment='通知渠道: manual/wechat/email/sms'
    )
    notes: Mapped[str | None] = mapped_column(Text, default=None, comment='备注')

    # 时间戳
    created_time: Mapped[datetime] = mapped_column(TimeZone, default=timezone.now, comment='创建时间')
    updated_time: Mapped[datetime | None] = mapped_column(
        TimeZone, onupdate=timezone.now, default=None, comment='更新时间'
    )
    deleted_at: Mapped[datetime | None] = mapped_column(TimeZone, default=None, comment='软删除时间')
