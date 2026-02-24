"""邀请使用记录表模型"""

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from backend.common.model import Base
from backend.database.db import uuid4_str


class InvitationUsage(Base):
    """邀请使用记录表"""

    __tablename__ = "invitation_usage"

    id: Mapped[str] = mapped_column(sa.String(36), primary_key=True, init=False, default_factory=uuid4_str)

    # 必填字段（无默认值）
    invitation_id: Mapped[str] = mapped_column(
        sa.String(36), sa.ForeignKey("invitations.id", ondelete="CASCADE"), index=True, comment="邀请ID"
    )
    user_id: Mapped[int] = mapped_column(
        sa.BigInteger, sa.ForeignKey("sys_user.id", ondelete="CASCADE"), index=True, comment="用户ID"
    )
    registered_email: Mapped[str] = mapped_column(sa.String(256), index=True, comment="注册邮箱")

    # 可选字段（有默认值）
    ip_address: Mapped[str | None] = mapped_column(sa.String(45), default=None, index=True, comment="IPv4/IPv6")
    user_agent: Mapped[str | None] = mapped_column(sa.Text, default=None, comment="浏览器信息")
    completed_onboarding: Mapped[bool] = mapped_column(default=False, comment="是否完成引导")
    created_tenant_id: Mapped[str | None] = mapped_column(sa.String(36), default=None, comment="创建的租户ID")

    # DateTimeMixin (created_time, updated_time) will be added via Base
