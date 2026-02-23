from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from backend.app.admin.model.user import User
    from backend.app.userecho.model.tenant_role import TenantRole

from backend.common.model import MappedBase, TimeZone
from backend.database.db import uuid4_str
from backend.utils.timezone import timezone


class TenantUser(MappedBase):
    """租户-用户关联表（支持一个用户在多个租户中有不同角色）"""

    __tablename__ = 'tenant_users'

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4_str, comment='关联ID')
    tenant_id: Mapped[str] = mapped_column(
        String(36), ForeignKey('tenants.id', ondelete='CASCADE'), index=True, comment='租户ID'
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey('sys_user.id', ondelete='CASCADE'), index=True, comment='平台用户ID'
    )
    user: Mapped['User'] = relationship('backend.app.admin.model.user.User', lazy='selectin')

    # RBAC 角色关联
    roles: Mapped[list['TenantRole']] = relationship(
        'TenantRole',
        secondary='tenant_user_roles',
        primaryjoin='TenantUser.id == TenantUserRole.tenant_user_id',
        secondaryjoin='TenantRole.id == TenantUserRole.role_id',
        viewonly=True,
    )

    # 用户类型（在该租户中的角色）
    user_type: Mapped[str] = mapped_column(
        String(20),
        default='member',
        comment='用户类型: admin, product_manager, sales, customer_success, developer, member',
    )

    # 部门信息
    department_id: Mapped[int | None] = mapped_column(
        ForeignKey('sys_dept.id', ondelete='SET NULL'), default=None, comment='部门ID'
    )

    # 统计（租户内）
    feedback_count: Mapped[int] = mapped_column(default=0, comment='录入的反馈数')

    # 状态
    status: Mapped[str] = mapped_column(String(20), default='active', comment='状态: active, suspended, left')

    # 时间戳
    joined_at: Mapped[datetime] = mapped_column(TimeZone, default=timezone.now, comment='加入时间')
    last_active_at: Mapped[datetime | None] = mapped_column(TimeZone, default=None, comment='最后活跃时间')

    __table_args__ = (
        UniqueConstraint('tenant_id', 'user_id', name='uq_tenant_user'),
        {'comment': '租户-用户关联表（支持一个用户在多个租户中有不同角色）'},
    )


class TenantUserRole(MappedBase):
    """租户用户角色关联表（RBAC 权限系统）"""

    __tablename__ = 'tenant_user_roles'

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4_str, comment='关联ID')
    tenant_user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey('tenant_users.id', ondelete='CASCADE'), index=True, comment='租户用户ID'
    )
    # 关联到租户角色表（租户隔离的角色）
    role_id: Mapped[str] = mapped_column(
        String(36), ForeignKey('tenant_roles.id', ondelete='CASCADE'), index=True, comment='租户角色ID'
    )

    # 分配信息
    assigned_by: Mapped[int | None] = mapped_column(
        ForeignKey('sys_user.id', ondelete='SET NULL'), default=None, comment='分配人'
    )
    assigned_at: Mapped[datetime] = mapped_column(TimeZone, default=timezone.now, comment='分配时间')

    __table_args__ = (
        UniqueConstraint('tenant_user_id', 'role_id', name='uq_tenant_user_role'),
        {'comment': '租户用户角色关联表（RBAC 权限系统）'},
    )


def _get_user_attr(self, attr: str):
    return getattr(self.user, attr) if self.user else None


# Monkey patch properties to TenantUser for Pydantic serialization
TenantUser.username = property(lambda self: _get_user_attr(self, 'username'))
TenantUser.nickname = property(lambda self: _get_user_attr(self, 'nickname'))
TenantUser.email = property(lambda self: _get_user_attr(self, 'email'))
