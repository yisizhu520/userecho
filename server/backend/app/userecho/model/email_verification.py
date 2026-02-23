"""邮箱验证记录表模型"""

from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from backend.common.model import Base, TimeZone, id_key
from backend.database.db import uuid4_str
from backend.utils.timezone import timezone


class EmailVerification(Base):
    """邮箱验证记录表"""

    __tablename__ = "email_verifications"

    id: Mapped[id_key] = mapped_column(sa.String(36), init=False, default_factory=uuid4_str)
    
    # 必填字段（无默认值）
    user_id: Mapped[int] = mapped_column(
        sa.BigInteger,
        sa.ForeignKey("sys_user.id", ondelete="CASCADE"),
        index=True,
        comment="用户ID"
    )
    email: Mapped[str] = mapped_column(sa.String(256), index=True, comment="邮箱")
    verification_code: Mapped[str] = mapped_column(sa.String(64), index=True, comment="验证码/token")
    expires_at: Mapped[datetime] = mapped_column(TimeZone, comment="验证链接过期时间")
    
    # 可选字段（有默认值）
    is_verified: Mapped[bool] = mapped_column(default=False, comment="是否已验证")
    verified_at: Mapped[datetime | None] = mapped_column(TimeZone, default=None, comment="验证时间")
    send_count: Mapped[int] = mapped_column(default=1, comment="发送次数")
    last_sent_at: Mapped[datetime] = mapped_column(TimeZone, init=False, default_factory=timezone.now, comment="上次发送时间")
    
    # 时间戳
    created_at: Mapped[datetime] = mapped_column(TimeZone, init=False, default_factory=timezone.now, comment="创建时间")
    updated_at: Mapped[datetime | None] = mapped_column(
        TimeZone, init=False, onupdate=timezone.now, default=None, comment="更新时间"
    )
