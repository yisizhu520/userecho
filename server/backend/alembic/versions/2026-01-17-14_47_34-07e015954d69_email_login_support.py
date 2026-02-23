"""email_login_support

Revision ID: 07e015954d69
Revises: 03e4ac7514e6
Create Date: 2026-01-17 14:47:34.866504

"""
from alembic import op
import sqlalchemy as sa
import backend.common.model


# revision identifiers, used by Alembic.
revision = '07e015954d69'
down_revision = '03e4ac7514e6'
branch_labels = None
depends_on = None


def upgrade():
    """支持 Email 登录：email 改为必填，username 改为可选"""
    
    # 1. 为没有 email 的用户生成默认邮箱
    op.execute("""
        UPDATE sys_user 
        SET email = CONCAT('user', id, '@default.local') 
        WHERE email IS NULL OR email = ''
    """)
    
    # 2. 修改 email 字段为 NOT NULL
    op.alter_column('sys_user', 'email',
                    existing_type=sa.String(256),
                    nullable=False,
                    existing_nullable=True)
    
    # 3. 修改 username 字段为可选（保留用于显示）
    op.alter_column('sys_user', 'username',
                    existing_type=sa.String(64),
                    nullable=True,
                    existing_nullable=False)


def downgrade():
    """回滚：恢复 email 可空，username 必填"""
    
    # 1. 恢复 username 为必填
    # 为没有 username 的用户生成默认值
    op.execute("""
        UPDATE sys_user 
        SET username = CONCAT('user_', id) 
        WHERE username IS NULL OR username = ''
    """)
    
    op.alter_column('sys_user', 'username',
                    existing_type=sa.String(64),
                    nullable=False,
                    existing_nullable=True)
    
    # 2. 恢复 email 为可选
    op.alter_column('sys_user', 'email',
                    existing_type=sa.String(256),
                    nullable=True,
                    existing_nullable=False)

