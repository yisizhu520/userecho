from datetime import datetime

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.common.model import MappedBase, TimeZone
from backend.database.db import uuid4_str
from backend.utils.timezone import timezone


class Customer(MappedBase):
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
    
    # 手动添加时间戳字段（避免 dataclass 顺序问题）
    created_time: Mapped[datetime] = mapped_column(TimeZone, default=timezone.now, comment='创建时间')
    updated_time: Mapped[datetime | None] = mapped_column(TimeZone, onupdate=timezone.now, default=None, comment='更新时间')
