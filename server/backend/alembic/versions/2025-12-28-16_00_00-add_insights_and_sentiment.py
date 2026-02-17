"""add insights and sentiment

Revision ID: add_insights_sentiment
Revises: 71cc2d84933e
Create Date: 2025-12-28 16:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_insights_sentiment'
down_revision = '71cc2d84933e'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 创建 insights 表
    op.create_table(
        'insights',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('tenant_id', sa.String(36), nullable=False),
        sa.Column('insight_type', sa.String(20), nullable=False),
        sa.Column('time_range', sa.String(20), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('content', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('generated_by', sa.String(20), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('execution_time_ms', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(20), server_default='active', nullable=False),
        sa.Column('dismissed_reason', sa.Text(), nullable=True),
        sa.Column('created_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_time', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
    )

    # 创建索引
    op.create_index('idx_tenant_type_time', 'insights', ['tenant_id', 'insight_type', 'start_date'])
    op.create_index('idx_insight_status', 'insights', ['status'])

    # 给 feedbacks 表添加情感分析字段
    op.add_column('feedbacks', sa.Column('sentiment', sa.String(20), nullable=True))
    op.add_column('feedbacks', sa.Column('sentiment_score', sa.Float(), nullable=True))
    op.add_column('feedbacks', sa.Column('sentiment_reason', sa.Text(), nullable=True))

    # 创建情感字段索引
    op.create_index('idx_feedback_sentiment', 'feedbacks', ['sentiment'])


def downgrade() -> None:
    # 删除 feedbacks 表的情感字段
    op.drop_index('idx_feedback_sentiment', table_name='feedbacks')
    op.drop_column('feedbacks', 'sentiment_reason')
    op.drop_column('feedbacks', 'sentiment_score')
    op.drop_column('feedbacks', 'sentiment')

    # 删除 insights 表
    op.drop_index('idx_insight_status', table_name='insights')
    op.drop_index('idx_tenant_type_time', table_name='insights')
    op.drop_table('insights')
