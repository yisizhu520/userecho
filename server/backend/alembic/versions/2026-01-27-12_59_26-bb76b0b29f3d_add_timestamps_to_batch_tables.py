"""add timestamps to batch tables

Revision ID: bb76b0b29f3d
Revises: f9a8b7c6d5e4
Create Date: 2026-01-27 12:59:26.088398

"""
from alembic import op
import sqlalchemy as sa
import backend.common.model


# revision identifiers, used by Alembic.
revision = 'bb76b0b29f3d'
down_revision = 'f9a8b7c6d5e4'
branch_labels = None
depends_on = None


def upgrade():
    # 添加时间戳字段到 batch_job 表
    op.add_column(
        'batch_job',
        sa.Column('create_time', backend.common.model.TimeZone(), nullable=False, server_default=sa.text('NOW()'), comment='创建时间')
    )
    op.add_column(
        'batch_job',
        sa.Column('update_time', backend.common.model.TimeZone(), nullable=False, server_default=sa.text('NOW()'), comment='更新时间')
    )
    
    # 添加时间戳字段到 batch_task_item 表
    op.add_column(
        'batch_task_item',
        sa.Column('create_time', backend.common.model.TimeZone(), nullable=False, server_default=sa.text('NOW()'), comment='创建时间')
    )
    op.add_column(
        'batch_task_item',
        sa.Column('update_time', backend.common.model.TimeZone(), nullable=False, server_default=sa.text('NOW()'), comment='更新时间')
    )


def downgrade():
    # 删除 batch_task_item 表的时间戳字段
    op.drop_column('batch_task_item', 'update_time')
    op.drop_column('batch_task_item', 'create_time')
    
    # 删除 batch_job 表的时间戳字段
    op.drop_column('batch_job', 'update_time')
    op.drop_column('batch_job', 'create_time')
