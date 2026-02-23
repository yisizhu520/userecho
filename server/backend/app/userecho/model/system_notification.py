from datetime import datetime

from sqlalchemy import JSON, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.common.model import MappedBase, TimeZone
from backend.database.db import uuid4_str
from backend.utils.timezone import timezone


class SystemNotification(MappedBase):
    """系统提醒表（右上角 Bell 图标显示的通知）"""

    __tablename__ = 'system_notifications'

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4_str, comment='通知ID')
    tenant_id: Mapped[str] = mapped_column(
        String(36), ForeignKey('tenants.id', ondelete='CASCADE'), index=True, comment='租户ID'
    )
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey('sys_user.id', ondelete='CASCADE'),
        index=True,
        default=None,
        comment='接收用户ID（NULL表示发送给租户所有用户）',
    )

    # 通知内容
    type: Mapped[str] = mapped_column(
        String(50),
        index=True,
        comment='通知类型: topic_completed/notification_pending/feedback_imported/clustering_completed',
    )
    title: Mapped[str] = mapped_column(String(200), comment='通知标题')
    message: Mapped[str] = mapped_column(Text, comment='通知内容')
    avatar: Mapped[str | None] = mapped_column(String(500), default=None, comment='头像URL')

    # 跳转和元数据
    action_url: Mapped[str | None] = mapped_column(String(500), default=None, comment='点击跳转URL')
    extra_data: Mapped[dict | None] = mapped_column(JSON, default=None, comment='额外元数据')

    # 状态
    is_read: Mapped[bool] = mapped_column(default=False, index=True, comment='是否已读')
    read_at: Mapped[datetime | None] = mapped_column(TimeZone, default=None, comment='阅读时间')

    # 时间戳
    created_time: Mapped[datetime] = mapped_column(TimeZone, default=timezone.now, comment='创建时间')
