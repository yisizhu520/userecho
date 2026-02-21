"""add_reply_template

Revision ID: 008f26350dd0
Revises: ea767bb5a3c5
Create Date: 2026-01-14 08:54:43.481375

"""
from alembic import op
import sqlalchemy as sa
import backend.common.model

# revision identifiers, used by Alembic.
revision = '008f26350dd0'
down_revision = 'ea767bb5a3c5'
branch_labels = None
depends_on = None


def upgrade():
    # ### 创建 reply_templates 表 ###
    op.create_table('reply_templates',
    sa.Column('id', sa.String(length=36), nullable=False, comment='模板ID'),
    sa.Column('tenant_id', sa.String(length=36), nullable=False, comment='租户ID'),
    sa.Column('name', sa.String(length=100), nullable=False, comment='模板名称'),
    sa.Column('description', sa.String(length=255), nullable=True, comment='模板描述'),
    sa.Column('content', sa.Text(), nullable=False, comment='模板内容'),
    sa.Column('category', sa.String(length=50), nullable=False, comment='分类: general/bug_fix/feature/improvement'),
    sa.Column('tone', sa.String(length=20), nullable=False, comment='语气: formal/friendly/concise'),
    sa.Column('language', sa.String(length=10), nullable=False, comment='语言'),
    sa.Column('is_system', sa.Boolean(), nullable=False, comment='是否系统预置模板'),
    sa.Column('is_active', sa.Boolean(), nullable=False, comment='是否启用'),
    sa.Column('usage_count', sa.Integer(), nullable=False, comment='使用次数'),
    sa.Column('created_by', sa.BigInteger(), nullable=True, comment='创建人ID'),
    sa.Column('created_time', backend.common.model.TimeZone(timezone=True), nullable=False, comment='创建时间'),
    sa.Column('updated_time', backend.common.model.TimeZone(timezone=True), nullable=True, comment='更新时间'),
    sa.ForeignKeyConstraint(['created_by'], ['sys_user.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    comment='回复模板表'
    )
    op.create_index(op.f('ix_reply_templates_category'), 'reply_templates', ['category'], unique=False)
    op.create_index(op.f('ix_reply_templates_is_active'), 'reply_templates', ['is_active'], unique=False)
    op.create_index(op.f('ix_reply_templates_tenant_id'), 'reply_templates', ['tenant_id'], unique=False)


def downgrade():
    # ### 删除 reply_templates 表 ###
    op.drop_index(op.f('ix_reply_templates_tenant_id'), table_name='reply_templates')
    op.drop_index(op.f('ix_reply_templates_is_active'), table_name='reply_templates')
    op.drop_index(op.f('ix_reply_templates_category'), table_name='reply_templates')
    op.drop_table('reply_templates')

    # ### end Alembic commands ###
