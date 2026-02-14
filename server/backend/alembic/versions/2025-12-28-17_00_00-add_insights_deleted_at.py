"""add insights deleted_at

Revision ID: add_insights_deleted_at
Revises: add_insights_sentiment
Create Date: 2025-12-28 17:00:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_insights_deleted_at'
down_revision = 'add_insights_sentiment'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # 给 insights 表添加 deleted_at 字段（软删除支持）
    op.add_column('insights', sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))


def downgrade():
    # 删除 deleted_at 字段
    op.drop_column('insights', 'deleted_at')
