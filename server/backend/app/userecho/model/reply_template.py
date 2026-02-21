from datetime import datetime

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.common.model import MappedBase, TimeZone
from backend.database.db import uuid4_str
from backend.utils.timezone import timezone


class ReplyTemplate(MappedBase):
    """回复模板表"""

    __tablename__ = 'reply_templates'

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4_str, comment='模板ID')
    tenant_id: Mapped[str] = mapped_column(
        String(36), ForeignKey('tenants.id', ondelete='CASCADE'), index=True, comment='租户ID'
    )

    # 模板内容
    name: Mapped[str] = mapped_column(String(100), comment='模板名称')
    description: Mapped[str | None] = mapped_column(String(255), default=None, comment='模板描述')
    content: Mapped[str] = mapped_column(Text, comment='模板内容')

    # 分类和设置
    category: Mapped[str] = mapped_column(
        String(50), default='general', index=True, comment='分类: general/bug_fix/feature/improvement'
    )
    tone: Mapped[str] = mapped_column(String(20), default='friendly', comment='语气: formal/friendly/concise')
    language: Mapped[str] = mapped_column(String(10), default='zh-CN', comment='语言')

    # 状态
    is_system: Mapped[bool] = mapped_column(default=False, comment='是否系统预置模板')
    is_active: Mapped[bool] = mapped_column(default=True, index=True, comment='是否启用')
    usage_count: Mapped[int] = mapped_column(default=0, comment='使用次数')

    # 创建者
    created_by: Mapped[int | None] = mapped_column(
        ForeignKey('sys_user.id', ondelete='SET NULL'), default=None, comment='创建人ID'
    )

    # 时间戳
    created_time: Mapped[datetime] = mapped_column(TimeZone, default=timezone.now, comment='创建时间')
    updated_time: Mapped[datetime | None] = mapped_column(
        TimeZone, onupdate=timezone.now, default=None, comment='更新时间'
    )
