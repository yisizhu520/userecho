"""rename_anonymous_to_external_user

Revision ID: 8c9d0e1f2a3b
Revises: eb4f2977a7fb
Create Date: 2026-01-10 20:43:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8c9d0e1f2a3b'
down_revision = 'eb4f2977a7fb'
branch_labels = None
depends_on = None


def upgrade():
    # 1. 添加新字段
    op.add_column('feedbacks', sa.Column('author_type', sa.String(20), nullable=True, comment='来源类型: customer=内部客户, external=外部用户'))
    op.add_column('feedbacks', sa.Column('external_user_name', sa.String(100), nullable=True, comment='外部用户名称'))
    op.add_column('feedbacks', sa.Column('external_contact', sa.String(255), nullable=True, comment='外部用户联系方式'))
    
    # 2. 迁移现有数据
    op.execute("""
        UPDATE feedbacks SET author_type = CASE 
            WHEN is_anonymous = true THEN 'external'
            ELSE 'customer'
        END
    """)
    op.execute("""
        UPDATE feedbacks SET external_user_name = COALESCE(anonymous_author, '未知用户')
        WHERE is_anonymous = true
    """)
    op.execute("""
        UPDATE feedbacks SET external_contact = anonymous_email 
        WHERE anonymous_email IS NOT NULL
    """)
    
    # 3. 修复不符合约束的数据
    # 如果 author_type='customer' 但 customer_id IS NULL，改为 external
    op.execute("""
        UPDATE feedbacks 
        SET author_type = 'external', 
            external_user_name = COALESCE(external_user_name, '未知用户')
        WHERE author_type = 'customer' AND customer_id IS NULL
    """)
    # 如果 author_type='external' 但 external_user_name IS NULL，设置默认值
    op.execute("""
        UPDATE feedbacks 
        SET external_user_name = '未知用户'
        WHERE author_type = 'external' AND external_user_name IS NULL
    """)
    
    # 4. 设置 author_type 默认值并设为非空
    op.execute("UPDATE feedbacks SET author_type = 'customer' WHERE author_type IS NULL")
    op.alter_column('feedbacks', 'author_type', nullable=False, server_default='customer')
    
    # 5. 删除旧约束（使用 IF EXISTS）
    op.execute("ALTER TABLE feedbacks DROP CONSTRAINT IF EXISTS chk_author_exists")
    
    # 6. 删除旧字段
    op.drop_column('feedbacks', 'is_anonymous')
    op.drop_column('feedbacks', 'anonymous_author')
    op.drop_column('feedbacks', 'anonymous_email')
    op.drop_column('feedbacks', 'anonymous_source')
    
    # 7. 添加新约束
    op.execute("""
        ALTER TABLE feedbacks ADD CONSTRAINT chk_author_info CHECK (
            (author_type = 'customer' AND customer_id IS NOT NULL) OR 
            (author_type = 'external' AND external_user_name IS NOT NULL)
        )
    """)
    
    # 8. 创建索引
    op.create_index('ix_feedbacks_author_type', 'feedbacks', ['author_type'])


def downgrade():
    # 1. 删除新索引
    op.drop_index('ix_feedbacks_author_type', 'feedbacks')
    
    # 2. 删除新约束
    op.drop_constraint('chk_author_info', 'feedbacks', type_='check')
    
    # 3. 添加旧字段
    op.add_column('feedbacks', sa.Column('is_anonymous', sa.Boolean(), nullable=True, server_default='false', comment='是否匿名反馈'))
    op.add_column('feedbacks', sa.Column('anonymous_author', sa.String(100), nullable=True, comment='匿名作者名称'))
    op.add_column('feedbacks', sa.Column('anonymous_email', sa.String(255), nullable=True, comment='匿名作者邮箱'))
    op.add_column('feedbacks', sa.Column('anonymous_source', sa.String(50), nullable=True, comment='匿名来源平台'))
    
    # 4. 迁移数据回旧字段
    op.execute("""
        UPDATE feedbacks SET is_anonymous = CASE 
            WHEN author_type = 'external' THEN true
            ELSE false
        END
    """)
    op.execute("""
        UPDATE feedbacks SET anonymous_author = external_user_name 
        WHERE external_user_name IS NOT NULL
    """)
    op.execute("""
        UPDATE feedbacks SET anonymous_email = external_contact 
        WHERE external_contact IS NOT NULL
    """)
    op.execute("""
        UPDATE feedbacks SET anonymous_source = source_platform 
        WHERE author_type = 'external' AND source_platform IS NOT NULL
    """)
    
    # 5. 添加旧约束
    op.create_check_constraint(
        'chk_author_exists',
        'feedbacks',
        'customer_id IS NOT NULL OR anonymous_author IS NOT NULL'
    )
    
    # 6. 删除新字段
    op.drop_column('feedbacks', 'author_type')
    op.drop_column('feedbacks', 'external_user_name')
    op.drop_column('feedbacks', 'external_contact')
