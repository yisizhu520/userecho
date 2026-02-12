from datetime import datetime

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from backend.common.model import MappedBase as Base, TimeZone
from backend.database.db import uuid4_str


class Tenant(Base):
    """租户表"""

    __tablename__ = 'tenants'

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4_str, comment='租户ID'
    )
    name: Mapped[str] = mapped_column(String(100), comment='租户名称')
    status: Mapped[str] = mapped_column(String(20), default='active', comment='状态: active, suspended, deleted'
    )
    deleted_at: Mapped[datetime | None] = mapped_column(TimeZone, default=None, comment='软删除时间')
