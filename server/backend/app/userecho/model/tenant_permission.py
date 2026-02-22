from datetime import datetime

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from backend.common.model import MappedBase, TimeZone
from backend.database.db import uuid4_str
from backend.utils.timezone import timezone


class TenantPermission(MappedBase):
    """租户权限表（功能权限点，全局定义）"""

    __tablename__ = 'tenant_permissions'

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4_str, comment='权限ID')
    parent_id: Mapped[str | None] = mapped_column(String(36), default=None, index=True, comment='父权限ID')
    name: Mapped[str] = mapped_column(String(64), comment='权限名称')
    code: Mapped[str] = mapped_column(String(64), unique=True, comment='权限代码，如 feedback:view')
    type: Mapped[str] = mapped_column(String(20), default='module', comment='类型: module, action')
    sort: Mapped[int] = mapped_column(default=0, comment='排序')

    created_time: Mapped[datetime] = mapped_column(TimeZone, default=timezone.now, comment='创建时间')

    __table_args__ = ({'comment': '租户权限表（全局定义，所有租户共享权限点）'},)


class TenantRolePermission(MappedBase):
    """租户角色-权限关联表"""

    __tablename__ = 'tenant_role_permissions'

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4_str, comment='关联ID')
    role_id: Mapped[str] = mapped_column(
        String(36), ForeignKey('tenant_roles.id', ondelete='CASCADE'), index=True, comment='角色ID'
    )
    permission_id: Mapped[str] = mapped_column(
        String(36), ForeignKey('tenant_permissions.id', ondelete='CASCADE'), index=True, comment='权限ID'
    )
    assigned_at: Mapped[datetime] = mapped_column(TimeZone, default=timezone.now, comment='分配时间')

    __table_args__ = (
        UniqueConstraint('role_id', 'permission_id', name='uq_tenant_role_permission'),
        {'comment': '租户角色-权限关联表'},
    )
