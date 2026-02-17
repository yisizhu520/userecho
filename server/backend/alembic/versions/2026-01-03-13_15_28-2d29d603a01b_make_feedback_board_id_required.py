"""make_feedback_board_id_required

Revision ID: 2d29d603a01b
Revises: fef12c5bf8a1
Create Date: 2026-01-03 13:15:28.293192

"""
from alembic import op
import sqlalchemy as sa
import backend.common.model


# revision identifiers, used by Alembic.
revision = '2d29d603a01b'
down_revision = 'fef12c5bf8a1'
branch_labels = None
depends_on = None


def upgrade():
    # 1. 为现有的 NULL board_id 设置默认值（如果有的话）
    # 注意：这里假设租户至少有一个 Board，否则需要先创建默认 Board
    op.execute("""
        UPDATE feedbacks 
        SET board_id = (
            SELECT id FROM boards 
            WHERE boards.tenant_id = feedbacks.tenant_id 
            LIMIT 1
        )
        WHERE board_id IS NULL
    """)
    
    # 2. 修改 board_id 为 NOT NULL
    op.alter_column('feedbacks', 'board_id',
                    existing_type=sa.String(36),
                    nullable=False,
                    comment='看板ID (必填)')
    
    # 3. 更新 images_metadata 字段注释
    op.alter_column('feedbacks', 'images_metadata',
                    existing_type=sa.JSON(),
                    nullable=True,
                    comment='图片元数据 JSONB: {"images": [{"url": "...", "platform": "wechat", "user_name": "...", "confidence": 0.95, "uploaded_at": "..."}]}')


def downgrade():
    # 1. 恢复 board_id 为可空
    op.alter_column('feedbacks', 'board_id',
                    existing_type=sa.String(36),
                    nullable=True,
                    comment='看板ID')
    
    # 2. 恢复 images_metadata 注释
    op.alter_column('feedbacks', 'images_metadata',
                    existing_type=sa.JSON(),
                    nullable=True,
                    comment='图片元数据数组')
