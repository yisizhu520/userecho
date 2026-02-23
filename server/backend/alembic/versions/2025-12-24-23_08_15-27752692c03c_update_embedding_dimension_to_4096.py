"""update_embedding_dimension_to_4096

Revision ID: 27752692c03c
Revises: f8b29330fc5d
Create Date: 2025-12-24 23:08:15.952883

修改 embedding 维度从 768 改为 4096（匹配火山引擎 embedding 模型）

注意：此迁移会删除现有 embedding 数据，需要重新计算
"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "27752692c03c"
down_revision = "f8b29330fc5d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    升级：修改 embedding 维度 768 -> 4096

    策略：删除旧列，创建新列（pgvector 不支持直接修改维度）
    """
    bind = op.get_bind()

    if bind.dialect.name == "postgresql":
        # 1. feedbacks.embedding: 768 -> 4096
        op.drop_column("feedbacks", "embedding")
        op.add_column(
            "feedbacks",
            sa.Column(
                "embedding",
                sa.Text(),  # 先用 TEXT 过渡
                nullable=True,
                comment="Embedding向量(pgvector, 火山引擎 4096维)",
            ),
        )
        op.execute("ALTER TABLE feedbacks ALTER COLUMN embedding TYPE vector(4096) USING embedding::vector")

        # 2. topics.centroid: 768 -> 4096
        op.drop_column("topics", "centroid")
        op.add_column(
            "topics",
            sa.Column(
                "centroid",
                sa.Text(),  # 先用 TEXT 过渡
                nullable=True,
                comment="主题中心向量(所有反馈 embedding 的平均值, 火山引擎 4096维)",
            ),
        )
        op.execute("ALTER TABLE topics ALTER COLUMN centroid TYPE vector(4096) USING centroid::vector")

        print("✅ Embedding 维度已更新为 4096。旧数据已清空，需要重新运行聚类任务。")


def downgrade() -> None:
    """
    降级：恢复 embedding 维度 4096 -> 768
    """
    bind = op.get_bind()

    if bind.dialect.name == "postgresql":
        # 1. feedbacks.embedding: 4096 -> 768
        op.drop_column("feedbacks", "embedding")
        op.add_column(
            "feedbacks",
            sa.Column(
                "embedding",
                sa.Text(),
                nullable=True,
                comment="Embedding向量(pgvector)",
            ),
        )
        op.execute("ALTER TABLE feedbacks ALTER COLUMN embedding TYPE vector(768) USING embedding::vector")

        # 2. topics.centroid: 4096 -> 768
        op.drop_column("topics", "centroid")
        op.add_column(
            "topics",
            sa.Column(
                "centroid",
                sa.Text(),
                nullable=True,
                comment="主题中心向量(所有反馈 embedding 的平均值)",
            ),
        )
        op.execute("ALTER TABLE topics ALTER COLUMN centroid TYPE vector(768) USING centroid::vector")
