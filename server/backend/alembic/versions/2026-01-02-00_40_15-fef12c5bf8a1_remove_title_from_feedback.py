"""remove_title_from_feedback

Revision ID: fef12c5bf8a1
Revises: 20260102a
Create Date: 2026-01-02 00:40:15.717520

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "fef12c5bf8a1"
down_revision = "20260102a"  # 正确：这个迁移在 add_board_stats_triggers 之后
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    删除 feedbacks.title 字段

    步骤：
    1. 将现有的 title 合并到 content（如果 title 不为空）
    2. 删除 title 列
    """
    # 步骤 1: 数据迁移 - 合并 title 到 content
    # 格式：如果有 title，则 content = "【标题】title\n\ncontent"
    op.execute("""
        UPDATE feedbacks
        SET content = CONCAT('【标题】', title, E'\n\n', content)
        WHERE title IS NOT NULL AND title != '';
    """)

    # 步骤 2: 删除 title 列
    op.drop_column("feedbacks", "title")


def downgrade() -> None:
    """
    回滚：重新添加 title 列

    注意：无法完全恢复原始数据，因为 title 已经合并到 content 中
    """
    # 重新添加 title 列
    op.add_column("feedbacks", sa.Column("title", sa.String(400), nullable=True, comment="反馈标题（可选）"))

    # 尝试从 content 中提取 title（如果以【标题】开头）
    op.execute("""
        UPDATE feedbacks
        SET title = SUBSTRING(content FROM '【标题】(.+?)\\n\\n'),
            content = REGEXP_REPLACE(content, '^【标题】.+?\\n\\n', '')
        WHERE content LIKE '【标题】%';
    """)
