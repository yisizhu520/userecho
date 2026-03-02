"""remove_board_count_triggers_and_columns

Revision ID: 0eb2e0b8cbe5
Revises: 202602050100
Create Date: 2026-02-05 09:58:51.361039

说明：
- 删除看板表的 feedback_count 和 topic_count 字段
- 删除相关的触发器和触发器函数
- 改用应用层实时 COUNT 查询（简单、准确、无维护成本）

Linus: "触发器是过度设计。数据量小的时候，实时 COUNT 就够了。"
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "0eb2e0b8cbe5"
down_revision = "202602050100"
branch_labels = None
depends_on = None


def upgrade():
    """
    升级：删除触发器和计数字段

    顺序很重要：
    1. 先删除触发器（依赖函数）
    2. 再删除触发器函数
    3. 最后删除字段
    """
    # 1. 删除触发器（如果存在）
    op.execute("DROP TRIGGER IF EXISTS update_board_feedback_count_trigger ON feedbacks CASCADE")
    op.execute("DROP TRIGGER IF EXISTS update_board_topic_count_trigger ON topics CASCADE")

    # 2. 删除触发器函数（如果存在）
    op.execute("DROP FUNCTION IF EXISTS update_board_feedback_count() CASCADE")
    op.execute("DROP FUNCTION IF EXISTS update_board_topic_count() CASCADE")

    # 3. 删除字段（如果存在）
    op.execute("ALTER TABLE boards DROP COLUMN IF EXISTS feedback_count")
    op.execute("ALTER TABLE boards DROP COLUMN IF EXISTS topic_count")


def downgrade():
    """
    回滚：恢复字段和触发器

    虽然我们不推荐回滚（因为实时 COUNT 更好），但还是提供完整的回滚逻辑
    """
    # 1. 重新添加字段
    op.execute("""
        ALTER TABLE boards 
        ADD COLUMN IF NOT EXISTS feedback_count INTEGER DEFAULT 0 NOT NULL
    """)

    op.execute("""
        ALTER TABLE boards 
        ADD COLUMN IF NOT EXISTS topic_count INTEGER DEFAULT 0 NOT NULL
    """)

    # 2. 重新创建触发器函数
    op.execute("""
        CREATE OR REPLACE FUNCTION update_board_feedback_count()
        RETURNS TRIGGER AS $$
        BEGIN
            IF TG_OP = 'INSERT' THEN
                UPDATE boards 
                SET feedback_count = feedback_count + 1 
                WHERE id = NEW.board_id;
            ELSIF TG_OP = 'DELETE' THEN
                UPDATE boards 
                SET feedback_count = feedback_count - 1 
                WHERE id = OLD.board_id;
            ELSIF TG_OP = 'UPDATE' AND OLD.board_id != NEW.board_id THEN
                UPDATE boards 
                SET feedback_count = feedback_count - 1 
                WHERE id = OLD.board_id;
                
                UPDATE boards 
                SET feedback_count = feedback_count + 1 
                WHERE id = NEW.board_id;
            END IF;
            
            RETURN COALESCE(NEW, OLD);
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        CREATE OR REPLACE FUNCTION update_board_topic_count()
        RETURNS TRIGGER AS $$
        BEGIN
            IF TG_OP = 'INSERT' THEN
                UPDATE boards 
                SET topic_count = topic_count + 1 
                WHERE id = NEW.board_id;
            ELSIF TG_OP = 'DELETE' THEN
                UPDATE boards 
                SET topic_count = topic_count - 1 
                WHERE id = OLD.board_id;
            ELSIF TG_OP = 'UPDATE' AND OLD.board_id != NEW.board_id THEN
                UPDATE boards 
                SET topic_count = topic_count - 1 
                WHERE id = OLD.board_id;
                
                UPDATE boards 
                SET topic_count = topic_count + 1 
                WHERE id = NEW.board_id;
            END IF;
            
            RETURN COALESCE(NEW, OLD);
        END;
        $$ LANGUAGE plpgsql;
    """)

    # 3. 重新创建触发器
    op.execute("""
        CREATE TRIGGER update_board_feedback_count_trigger
        AFTER INSERT OR UPDATE OR DELETE ON feedbacks
        FOR EACH ROW
        EXECUTE FUNCTION update_board_feedback_count()
    """)

    op.execute("""
        CREATE TRIGGER update_board_topic_count_trigger
        AFTER INSERT OR UPDATE OR DELETE ON topics
        FOR EACH ROW
        EXECUTE FUNCTION update_board_topic_count()
    """)

    # 4. 重新计算现有数据的计数（保证数据一致性）
    op.execute("""
        UPDATE boards b
        SET feedback_count = (
            SELECT COUNT(*) 
            FROM feedbacks f 
            WHERE f.board_id = b.id AND f.deleted_at IS NULL
        )
    """)

    op.execute("""
        UPDATE boards b
        SET topic_count = (
            SELECT COUNT(*) 
            FROM topics t 
            WHERE t.board_id = b.id AND t.deleted_at IS NULL
        )
    """)
