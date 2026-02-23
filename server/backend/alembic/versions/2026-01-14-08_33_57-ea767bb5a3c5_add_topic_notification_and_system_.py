"""add_topic_notification_and_system_notification

Revision ID: ea767bb5a3c5
Revises: 3b88fd02d888
Create Date: 2026-01-14 08:33:57.671454

"""

import sqlalchemy as sa

from alembic import op

import backend.common.model

# revision identifiers, used by Alembic.
revision = 'ea767bb5a3c5'
down_revision = '3b88fd02d888'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### 创建 system_notifications 表 ###
    op.create_table(
        'system_notifications',
        sa.Column('id', sa.String(length=36), nullable=False, comment='通知ID'),
        sa.Column('tenant_id', sa.String(length=36), nullable=False, comment='租户ID'),
        sa.Column('user_id', sa.BigInteger(), nullable=True, comment='接收用户ID（NULL表示发送给租户所有用户）'),
        sa.Column(
            'type',
            sa.String(length=50),
            nullable=False,
            comment='通知类型: topic_completed/notification_pending/feedback_imported/clustering_completed',
        ),
        sa.Column('title', sa.String(length=200), nullable=False, comment='通知标题'),
        sa.Column('message', sa.Text(), nullable=False, comment='通知内容'),
        sa.Column('avatar', sa.String(length=500), nullable=True, comment='头像URL'),
        sa.Column('action_url', sa.String(length=500), nullable=True, comment='点击跳转URL'),
        sa.Column('extra_data', sa.JSON(), nullable=True, comment='额外元数据'),
        sa.Column('is_read', sa.Boolean(), nullable=False, comment='是否已读'),
        sa.Column('read_at', backend.common.model.TimeZone(timezone=True), nullable=True, comment='阅读时间'),
        sa.Column('created_time', backend.common.model.TimeZone(timezone=True), nullable=False, comment='创建时间'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['sys_user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        comment='系统提醒表（右上角 Bell 图标显示的通知）',
    )
    op.create_index(op.f('ix_system_notifications_is_read'), 'system_notifications', ['is_read'], unique=False)
    op.create_index(op.f('ix_system_notifications_tenant_id'), 'system_notifications', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_system_notifications_type'), 'system_notifications', ['type'], unique=False)
    op.create_index(op.f('ix_system_notifications_user_id'), 'system_notifications', ['user_id'], unique=False)

    # ### 创建 topic_notifications 表 ###
    op.create_table(
        'topic_notifications',
        sa.Column('id', sa.String(length=36), nullable=False, comment='通知记录ID'),
        sa.Column('tenant_id', sa.String(length=36), nullable=False, comment='租户ID'),
        sa.Column('topic_id', sa.String(length=36), nullable=False, comment='关联议题ID'),
        sa.Column('feedback_id', sa.String(length=36), nullable=False, comment='关联反馈ID'),
        sa.Column('customer_id', sa.String(length=36), nullable=True, comment='关联客户ID'),
        sa.Column('recipient_name', sa.String(length=100), nullable=False, comment='收件人名称'),
        sa.Column('recipient_contact', sa.String(length=255), nullable=True, comment='联系方式'),
        sa.Column('recipient_type', sa.String(length=20), nullable=False, comment='收件人类型: customer/external'),
        sa.Column('ai_reply', sa.Text(), nullable=True, comment='AI 生成的回复内容'),
        sa.Column('reply_tone', sa.String(length=20), nullable=False, comment='回复语气: formal/friendly/concise'),
        sa.Column('reply_language', sa.String(length=10), nullable=False, comment='回复语言'),
        sa.Column('status', sa.String(length=20), nullable=False, comment='状态: pending/generated/copied/sent'),
        sa.Column(
            'notified_at', backend.common.model.TimeZone(timezone=True), nullable=True, comment='标记为已通知的时间'
        ),
        sa.Column('notified_by', sa.BigInteger(), nullable=True, comment='操作人员ID'),
        sa.Column(
            'notification_channel', sa.String(length=50), nullable=True, comment='通知渠道: manual/wechat/email/sms'
        ),
        sa.Column('notes', sa.Text(), nullable=True, comment='备注'),
        sa.Column('created_time', backend.common.model.TimeZone(timezone=True), nullable=False, comment='创建时间'),
        sa.Column('updated_time', backend.common.model.TimeZone(timezone=True), nullable=True, comment='更新时间'),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['feedback_id'], ['feedbacks.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['notified_by'], ['sys_user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['topic_id'], ['topics.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        comment='需求通知记录表（Topic 完成后通知反馈提交人）',
    )
    op.create_index(op.f('ix_topic_notifications_feedback_id'), 'topic_notifications', ['feedback_id'], unique=False)
    op.create_index(op.f('ix_topic_notifications_status'), 'topic_notifications', ['status'], unique=False)
    op.create_index(op.f('ix_topic_notifications_tenant_id'), 'topic_notifications', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_topic_notifications_topic_id'), 'topic_notifications', ['topic_id'], unique=False)


def downgrade() -> None:
    # ### 删除 topic_notifications 表 ###
    op.drop_index(op.f('ix_topic_notifications_topic_id'), table_name='topic_notifications')
    op.drop_index(op.f('ix_topic_notifications_tenant_id'), table_name='topic_notifications')
    op.drop_index(op.f('ix_topic_notifications_status'), table_name='topic_notifications')
    op.drop_index(op.f('ix_topic_notifications_feedback_id'), table_name='topic_notifications')
    op.drop_table('topic_notifications')

    # ### 删除 system_notifications 表 ###
    op.drop_index(op.f('ix_system_notifications_user_id'), table_name='system_notifications')
    op.drop_index(op.f('ix_system_notifications_type'), table_name='system_notifications')
    op.drop_index(op.f('ix_system_notifications_tenant_id'), table_name='system_notifications')
    op.drop_index(op.f('ix_system_notifications_is_read'), table_name='system_notifications')
    op.drop_table('system_notifications')
