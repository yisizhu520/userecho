"""add tenant rbac tables

Revision ID: a1b2c3d4e5f6
Revises: e526c5099435
Create Date: 2026-01-15 22:50:00

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: str | None = "e526c5099435"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. 创建租户角色表
    op.create_table(
        "tenant_roles",
        sa.Column("id", sa.String(36), primary_key=True, comment="角色ID"),
        sa.Column(
            "tenant_id",
            sa.String(36),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
            comment="租户ID",
        ),
        sa.Column("name", sa.String(64), nullable=False, comment="角色名称"),
        sa.Column("code", sa.String(64), nullable=False, comment="角色代码"),
        sa.Column("description", sa.Text, nullable=True, comment="角色描述"),
        sa.Column("is_builtin", sa.Boolean, nullable=False, default=False, comment="是否内置角色"),
        sa.Column("sort", sa.Integer, nullable=False, default=0, comment="排序"),
        sa.Column("status", sa.String(20), nullable=False, default="active", comment="状态"),
        sa.Column("created_time", sa.DateTime(timezone=True), nullable=False, comment="创建时间"),
        sa.Column("updated_time", sa.DateTime(timezone=True), nullable=True, comment="更新时间"),
        sa.UniqueConstraint("tenant_id", "code", name="uq_tenant_role_code"),
        comment="租户角色表",
    )

    # 2. 创建租户权限表（全局定义）
    op.create_table(
        "tenant_permissions",
        sa.Column("id", sa.String(36), primary_key=True, comment="权限ID"),
        sa.Column("parent_id", sa.String(36), nullable=True, index=True, comment="父权限ID"),
        sa.Column("name", sa.String(64), nullable=False, comment="权限名称"),
        sa.Column("code", sa.String(64), nullable=False, unique=True, comment="权限代码"),
        sa.Column("type", sa.String(20), nullable=False, default="module", comment="类型"),
        sa.Column("sort", sa.Integer, nullable=False, default=0, comment="排序"),
        sa.Column("created_time", sa.DateTime(timezone=True), nullable=False, comment="创建时间"),
        comment="租户权限表",
    )

    # 3. 创建租户角色-权限关联表
    op.create_table(
        "tenant_role_permissions",
        sa.Column("id", sa.String(36), primary_key=True, comment="关联ID"),
        sa.Column(
            "role_id",
            sa.String(36),
            sa.ForeignKey("tenant_roles.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
            comment="角色ID",
        ),
        sa.Column(
            "permission_id",
            sa.String(36),
            sa.ForeignKey("tenant_permissions.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
            comment="权限ID",
        ),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=False, comment="分配时间"),
        sa.UniqueConstraint("role_id", "permission_id", name="uq_tenant_role_permission"),
        comment="租户角色-权限关联表",
    )

    # 4. 修改 tenant_user_roles 表的 role_id 列
    # 先删除旧的外键约束和列，再添加新的
    op.drop_constraint("tenant_user_roles_role_id_fkey", "tenant_user_roles", type_="foreignkey")
    op.alter_column(
        "tenant_user_roles",
        "role_id",
        existing_type=sa.BigInteger(),
        type_=sa.String(36),
        existing_nullable=False,
        comment="租户角色ID",
    )
    op.create_foreign_key(
        "tenant_user_roles_role_id_fkey", "tenant_user_roles", "tenant_roles", ["role_id"], ["id"], ondelete="CASCADE"
    )

    # 5. 初始化内置权限数据
    from datetime import datetime

    from backend.database.db import uuid4_str

    now = datetime.now()

    permissions = [
        # 反馈管理
        {"id": uuid4_str(), "parent_id": None, "name": "反馈管理", "code": "feedback", "type": "module", "sort": 1},
        # 需求管理
        {"id": uuid4_str(), "parent_id": None, "name": "需求管理", "code": "topic", "type": "module", "sort": 2},
        # 洞察报告
        {"id": uuid4_str(), "parent_id": None, "name": "洞察报告", "code": "insight", "type": "module", "sort": 3},
        # 成员管理
        {"id": uuid4_str(), "parent_id": None, "name": "成员管理", "code": "member", "type": "module", "sort": 4},
        # 角色权限
        {"id": uuid4_str(), "parent_id": None, "name": "角色权限", "code": "role", "type": "module", "sort": 5},
        # 租户设置
        {"id": uuid4_str(), "parent_id": None, "name": "租户设置", "code": "settings", "type": "module", "sort": 6},
    ]

    op.bulk_insert(
        sa.table(
            "tenant_permissions",
            sa.column("id", sa.String(36)),
            sa.column("parent_id", sa.String(36)),
            sa.column("name", sa.String(64)),
            sa.column("code", sa.String(64)),
            sa.column("type", sa.String(20)),
            sa.column("sort", sa.Integer),
            sa.column("created_time", sa.DateTime(timezone=True)),
        ),
        [{**p, "created_time": now} for p in permissions],
    )


def downgrade() -> None:
    # 1. 恢复 tenant_user_roles.role_id 到原类型
    op.drop_constraint("tenant_user_roles_role_id_fkey", "tenant_user_roles", type_="foreignkey")
    op.alter_column(
        "tenant_user_roles",
        "role_id",
        existing_type=sa.String(36),
        type_=sa.BigInteger(),
        existing_nullable=False,
        comment="角色ID",
    )
    op.create_foreign_key(
        "tenant_user_roles_role_id_fkey", "tenant_user_roles", "sys_role", ["role_id"], ["id"], ondelete="CASCADE"
    )

    # 2. 删除新创建的表
    op.drop_table("tenant_role_permissions")
    op.drop_table("tenant_permissions")
    op.drop_table("tenant_roles")
