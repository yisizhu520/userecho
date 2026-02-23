"""邀请表模型"""

from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from backend.common.model import Base, TimeZone, id_key
from backend.database.db import uuid4_str
from backend.utils.timezone import timezone


class Invitation(Base):
    """邀请表"""

    __tablename__ = "invitations"

    id: Mapped[id_key] = mapped_column(sa.String(36), init=False, default_factory=uuid4_str)
    
    # 必填字段（无默认值）
    token: Mapped[str] = mapped_column(sa.String(64), unique=True, index=True, comment="邀请token（URL中的唯一标识）")
    expires_at: Mapped[datetime] = mapped_column(TimeZone, comment="过期时间")
    
    # 可选字段（有默认值）
    usage_limit: Mapped[int] = mapped_column(default=10, comment="使用次数限制")
    used_count: Mapped[int] = mapped_column(default=0, comment="已使用次数")
    plan_code: Mapped[str] = mapped_column(sa.String(20), default="pro", comment="赋予的套餐代号")
    trial_days: Mapped[int] = mapped_column(default=90, comment="试用天数")
    
    # 来源标识（数据分析用）
    source: Mapped[str | None] = mapped_column(sa.String(50), default=None, comment="来源标签")
    campaign: Mapped[str | None] = mapped_column(sa.String(100), default=None, comment="活动标识")
    
    # 管理信息
    creator_id: Mapped[int | None] = mapped_column(sa.BigInteger, default=None, comment="创建者ID")
    notes: Mapped[str | None] = mapped_column(sa.Text, default=None, comment="管理备注")
    status: Mapped[str] = mapped_column(sa.String(20), default="active", index=True, comment="状态: active/expired/disabled")
    
    # 时间戳
    created_at: Mapped[datetime] = mapped_column(TimeZone, init=False, default_factory=timezone.now, comment="创建时间")
    updated_at: Mapped[datetime | None] = mapped_column(
        TimeZone, init=False, onupdate=timezone.now, default=None, comment="更新时间"
    )
