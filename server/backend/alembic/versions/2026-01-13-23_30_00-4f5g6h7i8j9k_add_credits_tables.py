"""add credits tables

Revision ID: 4f5g6h7i8j9k
Revises: 8c9d0e1f2a3b
Create Date: 2026-01-13
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '4f5g6h7i8j9k'
down_revision: str | None = '8c9d0e1f2a3b'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 租户积分配置表
    op.create_table(
        'tenant_credits',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('tenant_id', sa.String(36), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('plan_type', sa.String(20), nullable=False, server_default='starter'),
        sa.Column('monthly_quota', sa.Integer(), nullable=False, server_default='500'),
        sa.Column('current_balance', sa.Integer(), nullable=False, server_default='500'),
        sa.Column('total_used', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_refresh_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('next_refresh_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.UniqueConstraint('tenant_id', name='uq_tenant_credits_tenant'),
    )
    op.create_index('idx_tenant_credits_refresh', 'tenant_credits', ['next_refresh_at'])

    # 积分消耗记录表
    op.create_table(
        'credits_usage_log',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('tenant_id', sa.String(36), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', sa.String(36), nullable=True),
        sa.Column('operation_type', sa.String(50), nullable=False),
        sa.Column('credits_cost', sa.Integer(), nullable=False),
        sa.Column('description', sa.String(255), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
    )
    op.create_index('idx_credits_usage_tenant_date', 'credits_usage_log', ['tenant_id', 'created_at'])
    op.create_index('idx_credits_usage_type', 'credits_usage_log', ['operation_type'])

    # 积分配置表（系统级）
    op.create_table(
        'credits_config',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('config_key', sa.String(50), unique=True, nullable=False),
        sa.Column('config_value', sa.Integer(), nullable=False),
        sa.Column('config_type', sa.String(20), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
    )
    op.create_index('idx_credits_config_type', 'credits_config', ['config_type'])

    # 插入默认配置
    op.execute("""
        INSERT INTO credits_config (id, config_key, config_value, config_type, description) VALUES
        -- 操作消耗配置
        (gen_random_uuid()::text, 'cost_clustering', 10, 'operation_cost', 'AI 聚类每次消耗积分'),
        (gen_random_uuid()::text, 'cost_screenshot', 5, 'operation_cost', '截图识别每张消耗积分'),
        (gen_random_uuid()::text, 'cost_summary', 2, 'operation_cost', 'AI 摘要每条消耗积分'),
        (gen_random_uuid()::text, 'cost_embedding', 1, 'operation_cost', '向量化每条消耗积分'),
        (gen_random_uuid()::text, 'cost_insight', 20, 'operation_cost', '洞察报告每份消耗积分'),
        -- 套餐额度配置
        (gen_random_uuid()::text, 'quota_starter', 500, 'plan_quota', '启航版月度积分额度'),
        (gen_random_uuid()::text, 'quota_pro', 2000, 'plan_quota', '专业版月度积分额度'),
        (gen_random_uuid()::text, 'quota_team', 10000, 'plan_quota', '团队版月度积分额度'),
        (gen_random_uuid()::text, 'quota_enterprise', -1, 'plan_quota', '企业版月度积分额度（-1=无限制）')
    """)


def downgrade() -> None:
    op.drop_table('credits_config')
    op.drop_table('credits_usage_log')
    op.drop_table('tenant_credits')
