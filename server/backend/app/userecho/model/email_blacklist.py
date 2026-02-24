"""邮箱黑名单表模型"""

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from backend.common.model import Base
from backend.database.db import uuid4_str


class EmailBlacklist(Base):
    """邮箱黑名单表"""

    __tablename__ = "email_blacklist"

    id: Mapped[str] = mapped_column(sa.String(36), primary_key=True, init=False, default_factory=uuid4_str)

    # 必填字段（无默认值）
    domain: Mapped[str] = mapped_column(sa.String(256), unique=True, index=True, comment="邮箱域名")

    # 可选字段（有默认值）
    type: Mapped[str] = mapped_column(sa.String(20), default="disposable", comment="类型: disposable/spam/banned")
    reason: Mapped[str | None] = mapped_column(sa.Text, default=None, comment="加入黑名单的原因")

    # 管理信息
    added_by: Mapped[int | None] = mapped_column(sa.BigInteger, default=None, comment="添加人ID")
    is_active: Mapped[bool] = mapped_column(default=True, index=True, comment="是否启用")

    # DateTimeMixin (created_time, updated_time) will be added via Base
