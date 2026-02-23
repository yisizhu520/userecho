"""add_deleted_at_to_topic_notifications

Revision ID: e526c5099435
Revises: 008f26350dd0
Create Date: 2026-01-14 23:43:04.384837

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "e526c5099435"
down_revision = "008f26350dd0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 添加 deleted_at 字段（幂等性：如果字段已存在则跳过）
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'topic_notifications'
                AND column_name = 'deleted_at'
            ) THEN
                ALTER TABLE topic_notifications
                ADD COLUMN deleted_at TIMESTAMP WITH TIME ZONE DEFAULT NULL;

                COMMENT ON COLUMN topic_notifications.deleted_at IS '软删除时间';
            END IF;
        END $$;
    """)


def downgrade() -> None:
    # 删除 deleted_at 字段（幂等性：如果字段不存在则跳过）
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'topic_notifications'
                AND column_name = 'deleted_at'
            ) THEN
                ALTER TABLE topic_notifications DROP COLUMN deleted_at;
            END IF;
        END $$;
    """)
