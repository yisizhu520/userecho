"""add insights deleted_at

Revision ID: add_insights_deleted_at
Revises: add_insights_sentiment
Create Date: 2025-12-28 17:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = 'add_insights_deleted_at'
down_revision = 'add_insights_sentiment'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 给 insights 表添加 deleted_at 字段（软删除支持）
    op.add_column('insights', sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    # 删除 deleted_at 字段
    op.drop_column('insights', 'deleted_at')
