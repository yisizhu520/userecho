"""add menu fields to tenant permissions

Revision ID: b2c3d4e5f6g7
Revises: a1b2c3d4e5f6
Create Date: 2026-01-16 07:40:00

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6g7'
down_revision: str | None = 'a1b2c3d4e5f6'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 为 tenant_permissions 表添加菜单相关字段
    op.add_column('tenant_permissions', sa.Column('menu_path', sa.String(256), nullable=True, comment='关联的菜单路径'))
    op.add_column('tenant_permissions', sa.Column('menu_icon', sa.String(64), nullable=True, comment='菜单图标'))


def downgrade() -> None:
    op.drop_column('tenant_permissions', 'menu_icon')
    op.drop_column('tenant_permissions', 'menu_path')
