"""add clustering status and topic centroid

Revision ID: 2025122313
Revises: 2025122223
Create Date: 2025-12-23 13:00:00.000000

聚类重构：引入反馈聚类状态与聚类元数据，并为 Topic 增加中心向量与质量指标。

新增字段：
- feedbacks.clustering_status: pending / processing / clustered / failed
- feedbacks.clustering_metadata: JSON（聚类标签、时间、质量等）
- topics.centroid: pgvector vector(768)
- topics.cluster_quality: JSON（silhouette/noise_ratio/confidence 等）
- topics.is_noise: bool（标记低质量/噪声 Topic，前端可默认隐藏）
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = '2025122313'
down_revision: str | None = '2025122223'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()

    # feedbacks: 聚类状态与元数据
    op.add_column(
        'feedbacks',
        sa.Column(
            'clustering_status',
            sa.String(length=20),
            nullable=False,
            server_default='pending',
            comment='聚类状态: pending(待处理), processing(处理中), clustered(已聚类), failed(失败)',
        ),
    )
    op.add_column(
        'feedbacks',
        sa.Column(
            'clustering_metadata',
            sa.JSON(),
            nullable=True,
            comment='聚类元数据: {cluster_label: int, clustered_at: datetime, quality: dict, reason: str}',
        ),
    )
    op.create_index('ix_feedbacks_clustering_status', 'feedbacks', ['clustering_status'])

    # topics: centroid(向量) + 质量 + 噪声标记
    op.add_column(
        'topics',
        sa.Column(
            'cluster_quality',
            sa.JSON(),
            nullable=True,
            comment='聚类质量: {silhouette: float, noise_ratio: float, confidence: float, avg_similarity: float}',
        ),
    )
    op.add_column(
        'topics',
        sa.Column(
            'is_noise',
            sa.Boolean(),
            nullable=False,
            server_default=sa.text('false'),
            comment='是否噪声主题（低质量/仅单条等）',
        ),
    )
    op.create_index('ix_topics_is_noise', 'topics', ['is_noise'])

    # centroid 仅 PostgreSQL + pgvector 支持
    if bind.dialect.name == 'postgresql':
        op.execute('CREATE EXTENSION IF NOT EXISTS vector')

        # 先用 TEXT 过渡，避免在 migration 里依赖 pgvector python 包
        op.add_column(
            'topics',
            sa.Column(
                'centroid',
                sa.Text(),
                nullable=True,
                comment='主题中心向量（pgvector vector(768)）',
            ),
        )
        op.execute('ALTER TABLE topics ALTER COLUMN centroid TYPE vector(768) USING centroid::vector')
    else:
        op.add_column(
            'topics',
            sa.Column(
                'centroid',
                sa.Text(),
                nullable=True,
                comment='主题中心向量（非 PostgreSQL 环境降级为 TEXT，不支持向量运算）',
            ),
        )


def downgrade() -> None:
    op.get_bind()

    # topics
    op.drop_index('ix_topics_is_noise', table_name='topics')
    op.drop_column('topics', 'is_noise')
    op.drop_column('topics', 'cluster_quality')
    op.drop_column('topics', 'centroid')

    # feedbacks
    op.drop_index('ix_feedbacks_clustering_status', table_name='feedbacks')
    op.drop_column('feedbacks', 'clustering_metadata')
    op.drop_column('feedbacks', 'clustering_status')
