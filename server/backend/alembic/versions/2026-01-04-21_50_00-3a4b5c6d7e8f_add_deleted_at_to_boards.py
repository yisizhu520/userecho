"""add_deleted_at_to_boards

Revision ID: 3a4b5c6d7e8f
Revises: 2d29d603a01b
Create Date: 2026-01-04 21:50:00.000000

"""

import sqlalchemy as sa

from alembic import op

import backend.common.model

# revision identifiers, used by Alembic.
revision = '3a4b5c6d7e8f'
down_revision = '2d29d603a01b'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 添加 deleted_at 字段到 boards 表
    op.add_column(
        'boards', sa.Column('deleted_at', backend.common.model.TimeZone(), nullable=True, comment='软删除时间')
    )


def downgrade() -> None:
    # 移除 deleted_at 字段
    op.drop_column('boards', 'deleted_at')
