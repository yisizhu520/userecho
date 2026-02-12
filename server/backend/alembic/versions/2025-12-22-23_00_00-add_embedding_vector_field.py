"""add embedding vector field

Revision ID: add_embedding_vector
Revises: 2025-12-22-18_50_00
Create Date: 2025-12-22 23:00:00.000000

添加 pgvector VECTOR 类型字段用于高效向量搜索和缓存

新增功能：
1. 添加 embedding VECTOR(768) 字段
2. 支持高效向量相似度搜索（余弦距离）
3. 支持 IVFFlat 向量索引（可选）
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '2025122223'
down_revision: Union[str, None] = '2025122218'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    添加 embedding VECTOR 字段
    
    注意事项：
    1. 需要先安装 pgvector 扩展：CREATE EXTENSION IF NOT EXISTS vector;
    2. VECTOR 字段只支持 PostgreSQL
    3. 向量索引建议在数据量 > 1000 时手动创建
    """
    
    # 检查是否使用 PostgreSQL
    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        # 1. 确保 pgvector 扩展已安装
        op.execute('CREATE EXTENSION IF NOT EXISTS vector')
        
        # 2. 先添加 TEXT 字段，然后转换为 VECTOR 类型
        # 这样可以避免导入 pgvector Python 包
        op.add_column(
            'feedbacks',
            sa.Column(
                'embedding',
                sa.Text,
                nullable=True,
                comment='Embedding 向量（pgvector VECTOR(768)）'
            )
        )
        
        # 3. 将字段类型改为 VECTOR(768)
        op.execute('ALTER TABLE feedbacks ALTER COLUMN embedding TYPE vector(768) USING embedding::vector')
        
        # 注意：向量索引建议数据量 > 1000 时手动创建，避免首次部署慢
        # 手动创建命令：
        # CREATE INDEX idx_feedbacks_embedding
        # ON feedbacks
        # USING ivfflat (embedding vector_cosine_ops)
        # WITH (lists = 100);
        
    else:
        # MySQL 不支持 VECTOR 类型
        print('⚠️  MySQL does not support VECTOR type')
        print('    Please use PostgreSQL for vector search capabilities')
        pass


def downgrade() -> None:
    """回滚：删除 embedding VECTOR 字段"""
    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        # 删除 VECTOR 字段
        op.drop_column('feedbacks', 'embedding')
