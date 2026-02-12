from datetime import datetime

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.common.model import MappedBase as Base, TimeZone
from backend.database.db import uuid4_str


class Customer(Base):
    """客户表"""

    __tablename__ = 'customers'

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4_str, comment='客户ID'
    )
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey('tenants.id', ondelete='CASCADE'), index=True, comment='租户ID'
    )
    name: Mapped[str] = mapped_column(String(100), comment='客户名称')
    customer_type: Mapped[str] = mapped_column(String(20), default='normal', comment='客户类型: normal, paid, major, strategic'
    )
    business_value: Mapped[int] = mapped_column(default=1, comment='商业价值权重 (1-10)')
    deleted_at: Mapped[datetime | None] = mapped_column(TimeZone, default=None, comment='软删除时间')
