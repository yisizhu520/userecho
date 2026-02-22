from datetime import datetime

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from backend.common.model import MappedBase, TimeZone, UniversalText
from backend.database.db import uuid4_str
from backend.utils.timezone import timezone


class TenantRole(MappedBase):
    """租户角色表"""

    __tablename__ = 'tenant_roles'

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4_str, comment='角色ID')
    tenant_id: Mapped[str] = mapped_column(
        String(36), ForeignKey('tenants.id', ondelete='CASCADE'), index=True, comment='租户ID'
    )
    name: Mapped[str] = mapped_column(String(64), comment='角色名称')
    code: Mapped[str] = mapped_column(String(64), comment='角色代码')
    description: Mapped[str | None] = mapped_column(UniversalText, default=None, comment='角色描述')
    is_builtin: Mapped[bool] = mapped_column(default=False, comment='是否内置角色（不可删除）')
    sort: Mapped[int] = mapped_column(default=0, comment='排序')
    status: Mapped[str] = mapped_column(String(20), default='active', comment='状态: active, disabled')

    created_time: Mapped[datetime] = mapped_column(TimeZone, default=timezone.now, comment='创建时间')
    updated_time: Mapped[datetime | None] = mapped_column(TimeZone, onupdate=timezone.now, default=None, comment='更新时间')

    __table_args__ = (
        UniqueConstraint('tenant_id', 'code', name='uq_tenant_role_code'),
        {'comment': '租户角色表'},
    )
