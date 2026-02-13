"""add timestamps to userecho tables

Revision ID: 2025122218
Revises: 2025122201
Create Date: 2025-12-22 18:50:00.000000

"""
from alembic import op
import sqlalchemy as sa
import backend.common.model


# revision identifiers, used by Alembic.
revision = '2025122218'
down_revision = '2025122201'
branch_labels = None
depends_on = None


def upgrade():
    """添加时间戳字段到 userecho 表"""
    
    # 定义要添加时间戳的表
    tables = [
        'topics',
        'feedbacks',
        'customers',
        'status_histories',
        'manual_adjustments',
        'priority_scores',
        'tenants'
    ]
    
    # 为每个表添加 created_time 和 updated_time
    for table in tables:
        # 添加 created_time
        op.add_column(
            table,
            sa.Column(
                'created_time',
                backend.common.model.TimeZone(timezone=True),
                nullable=False,
                server_default=sa.text('CURRENT_TIMESTAMP'),
                comment='创建时间'
            )
        )
        
        # 添加 updated_time
        op.add_column(
            table,
            sa.Column(
                'updated_time',
                backend.common.model.TimeZone(timezone=True),
                nullable=True,
                comment='更新时间'
            )
        )


def downgrade():
    """移除时间戳字段"""
    
    tables = [
        'topics',
        'feedbacks',
        'customers',
        'status_histories',
        'manual_adjustments',
        'priority_scores',
        'tenants'
    ]
    
    for table in tables:
        op.drop_column(table, 'updated_time')
        op.drop_column(table, 'created_time')


