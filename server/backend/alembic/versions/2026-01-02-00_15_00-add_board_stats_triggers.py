"""add board stats triggers

Revision ID: 20260102a
Revises: 2025-12-31-22_00_00-add_boards_and_complete_schema
Create Date: 2026-01-02 00:15:00.000000

添加 Board 统计字段的自动更新触发器：
1. boards.feedback_count - 自动统计关联的反馈数量
2. boards.topic_count - 自动统计关联的主题数量
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '20260102a'
down_revision: str | None = '20251231b'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """添加 Board 统计触发器"""

    print('🔧 开始添加 Board 统计触发器...')

    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        print('   ├─ [1/3] 创建 Board Feedback 统计触发器函数...')

        # 创建更新 Board feedback_count 的触发器函数
        op.execute("""
            CREATE OR REPLACE FUNCTION update_board_feedback_count()
            RETURNS TRIGGER AS $$
            DECLARE
                v_board_id VARCHAR(36);
            BEGIN
                -- 确定需要更新的 board_id
                IF TG_OP = 'DELETE' THEN
                    v_board_id := OLD.board_id;
                ELSIF TG_OP = 'UPDATE' THEN
                    -- 更新时需要处理新旧两个 board
                    IF OLD.board_id IS NOT NULL AND OLD.board_id != COALESCE(NEW.board_id, '') THEN
                        -- 更新旧 board 的统计
                        UPDATE boards SET
                            feedback_count = (
                                SELECT COUNT(*) FROM feedbacks
                                WHERE board_id = OLD.board_id AND deleted_at IS NULL
                            ),
                            updated_time = NOW()
                        WHERE id = OLD.board_id;
                    END IF;
                    v_board_id := NEW.board_id;
                ELSE
                    v_board_id := NEW.board_id;
                END IF;

                -- 更新新 board 的统计
                IF v_board_id IS NOT NULL THEN
                    UPDATE boards SET
                        feedback_count = (
                            SELECT COUNT(*) FROM feedbacks
                            WHERE board_id = v_board_id AND deleted_at IS NULL
                        ),
                        updated_time = NOW()
                    WHERE id = v_board_id;
                END IF;

                IF TG_OP = 'DELETE' THEN
                    RETURN OLD;
                ELSE
                    RETURN NEW;
                END IF;
            END;
            $$ LANGUAGE plpgsql;
        """)

        print('   ├─ [2/3] 创建 Board Topic 统计触发器函数...')

        # 创建更新 Board topic_count 的触发器函数
        op.execute("""
            CREATE OR REPLACE FUNCTION update_board_topic_count()
            RETURNS TRIGGER AS $$
            DECLARE
                v_board_id VARCHAR(36);
            BEGIN
                -- 确定需要更新的 board_id
                IF TG_OP = 'DELETE' THEN
                    v_board_id := OLD.board_id;
                ELSIF TG_OP = 'UPDATE' THEN
                    -- 更新时需要处理新旧两个 board
                    IF OLD.board_id IS NOT NULL AND OLD.board_id != COALESCE(NEW.board_id, '') THEN
                        -- 更新旧 board 的统计
                        UPDATE boards SET
                            topic_count = (
                                SELECT COUNT(*) FROM topics
                                WHERE board_id = OLD.board_id AND deleted_at IS NULL
                            ),
                            updated_time = NOW()
                        WHERE id = OLD.board_id;
                    END IF;
                    v_board_id := NEW.board_id;
                ELSE
                    v_board_id := NEW.board_id;
                END IF;

                -- 更新新 board 的统计
                IF v_board_id IS NOT NULL THEN
                    UPDATE boards SET
                        topic_count = (
                            SELECT COUNT(*) FROM topics
                            WHERE board_id = v_board_id AND deleted_at IS NULL
                        ),
                        updated_time = NOW()
                    WHERE id = v_board_id;
                END IF;

                IF TG_OP = 'DELETE' THEN
                    RETURN OLD;
                ELSE
                    RETURN NEW;
                END IF;
            END;
            $$ LANGUAGE plpgsql;
        """)

        print('   ├─ [3/3] 创建触发器...')

        # 先删除旧触发器（如果存在）
        op.execute('DROP TRIGGER IF EXISTS trigger_update_board_feedback_count ON feedbacks')
        op.execute('DROP TRIGGER IF EXISTS trigger_update_board_topic_count ON topics')

        # 在 feedbacks 表上创建触发器
        op.execute("""
            CREATE TRIGGER trigger_update_board_feedback_count
            AFTER INSERT OR UPDATE OF board_id, deleted_at OR DELETE ON feedbacks
            FOR EACH ROW
            EXECUTE FUNCTION update_board_feedback_count()
        """)

        # 在 topics 表上创建触发器
        op.execute("""
            CREATE TRIGGER trigger_update_board_topic_count
            AFTER INSERT OR UPDATE OF board_id, deleted_at OR DELETE ON topics
            FOR EACH ROW
            EXECUTE FUNCTION update_board_topic_count()
        """)

        print('✅ Board 统计触发器创建完成！')
        print()
        print('🔄 触发器：')
        print('   - trigger_update_board_feedback_count: 自动更新 Board 的 feedback_count')
        print('   - trigger_update_board_topic_count: 自动更新 Board 的 topic_count')
    else:
        print('   ⚠️  触发器仅支持 PostgreSQL，已跳过')


def downgrade() -> None:
    """回滚：删除 Board 统计触发器"""

    print('🔧 开始回滚 Board 统计触发器...')

    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        # 删除触发器
        print('   ├─ 删除触发器...')
        op.execute('DROP TRIGGER IF EXISTS trigger_update_board_feedback_count ON feedbacks')
        op.execute('DROP TRIGGER IF EXISTS trigger_update_board_topic_count ON topics')

        # 删除函数
        print('   ├─ 删除触发器函数...')
        op.execute('DROP FUNCTION IF EXISTS update_board_feedback_count')
        op.execute('DROP FUNCTION IF EXISTS update_board_topic_count')

        print('✅ 回滚完成！')
