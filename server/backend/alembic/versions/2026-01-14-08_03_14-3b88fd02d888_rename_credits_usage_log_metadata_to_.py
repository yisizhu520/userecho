"""rename_credits_usage_log_metadata_to_extra_data

Revision ID: 3b88fd02d888
Revises: 4f5g6h7i8j9k
Create Date: 2026-01-14 08:03:14.293116

"""
from alembic import op
import sqlalchemy as sa
import backend.common.model


# revision identifiers, used by Alembic.
revision = '3b88fd02d888'
down_revision = '4f5g6h7i8j9k'
branch_labels = None
depends_on = None


def upgrade():
    # 重命名列: metadata -> extra_data
    op.alter_column(
        'credits_usage_log',
        'metadata',
        new_column_name='extra_data',
        existing_type=sa.dialects.postgresql.JSONB(),
        existing_nullable=True,
    )


def downgrade():
    # 回滚: extra_data -> metadata
    op.alter_column(
        'credits_usage_log',
        'extra_data',
        new_column_name='metadata',
        existing_type=sa.dialects.postgresql.JSONB(),
        existing_nullable=True,
    )
