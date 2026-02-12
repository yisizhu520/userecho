"""add role_type and update menu paths

Revision ID: 2025122201
Revises: 9a2de98df5fb
Create Date: 2025-12-22 01:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2025122201'
down_revision = '9a2de98df5fb'
branch_labels = None
depends_on = None


def upgrade():
    """升级：添加 role_type 字段并更新菜单路径"""
    
    # 1. 添加 role_type 字段到 sys_role 表
    op.add_column('sys_role', sa.Column(
        'role_type', 
        sa.String(20), 
        nullable=False, 
        server_default='business',
        comment='角色类型（system=系统角色，business=业务角色）'
    ))
    
    # 2. 更新现有角色为系统角色
    # 将常见的系统管理员角色标记为 system 类型
    op.execute("""
        UPDATE sys_role 
        SET role_type = 'system' 
        WHERE name IN ('超级管理员', '系统管理员', 'admin', 'Admin', 'Administrator')
    """)
    
    # 3. 更新系统管理菜单路径
    # /system/* → /admin/system/*
    op.execute("""
        UPDATE sys_menu 
        SET path = REPLACE(path, '/system/', '/admin/system/') 
        WHERE path LIKE '/system/%'
    """)
    
    # /log/* → /admin/log/*
    op.execute("""
        UPDATE sys_menu 
        SET path = REPLACE(path, '/log/', '/admin/log/') 
        WHERE path LIKE '/log/%'
    """)
    
    # /monitor/* → /admin/monitor/*
    op.execute("""
        UPDATE sys_menu 
        SET path = REPLACE(path, '/monitor/', '/admin/monitor/') 
        WHERE path LIKE '/monitor/%'
    """)
    
    # /scheduler/* → /admin/scheduler/*
    op.execute("""
        UPDATE sys_menu 
        SET path = REPLACE(path, '/scheduler/', '/admin/scheduler/') 
        WHERE path LIKE '/scheduler/%'
    """)
    
    # 4. 更新业务功能菜单路径
    # /dashboard/* → /app/dashboard/*
    op.execute("""
        UPDATE sys_menu 
        SET path = REPLACE(path, '/dashboard/', '/app/dashboard/') 
        WHERE path LIKE '/dashboard/%'
    """)
    
    # 更新根菜单路径（如果存在）
    op.execute("""
        UPDATE sys_menu 
        SET path = '/admin/system' 
        WHERE path = '/system' AND type = 0
    """)
    
    op.execute("""
        UPDATE sys_menu 
        SET path = '/admin/log' 
        WHERE path = '/log' AND type = 0
    """)
    
    op.execute("""
        UPDATE sys_menu 
        SET path = '/admin/monitor' 
        WHERE path = '/monitor' AND type = 0
    """)
    
    op.execute("""
        UPDATE sys_menu 
        SET path = '/admin/scheduler' 
        WHERE path = '/scheduler' AND type = 0
    """)
    
    op.execute("""
        UPDATE sys_menu 
        SET path = '/app/dashboard' 
        WHERE path = '/dashboard' AND type = 0
    """)


def downgrade():
    """降级：回滚更改"""
    
    # 1. 回滚菜单路径
    op.execute("""
        UPDATE sys_menu 
        SET path = REPLACE(path, '/admin/system/', '/system/') 
        WHERE path LIKE '/admin/system/%'
    """)
    
    op.execute("""
        UPDATE sys_menu 
        SET path = REPLACE(path, '/admin/log/', '/log/') 
        WHERE path LIKE '/admin/log/%'
    """)
    
    op.execute("""
        UPDATE sys_menu 
        SET path = REPLACE(path, '/admin/monitor/', '/monitor/') 
        WHERE path LIKE '/admin/monitor/%'
    """)
    
    op.execute("""
        UPDATE sys_menu 
        SET path = REPLACE(path, '/admin/scheduler/', '/scheduler/') 
        WHERE path LIKE '/admin/scheduler/%'
    """)
    
    op.execute("""
        UPDATE sys_menu 
        SET path = REPLACE(path, '/app/dashboard/', '/dashboard/') 
        WHERE path LIKE '/app/dashboard/%'
    """)
    
    # 回滚根菜单
    op.execute("""
        UPDATE sys_menu 
        SET path = '/system' 
        WHERE path = '/admin/system' AND type = 0
    """)
    
    op.execute("""
        UPDATE sys_menu 
        SET path = '/log' 
        WHERE path = '/admin/log' AND type = 0
    """)
    
    op.execute("""
        UPDATE sys_menu 
        SET path = '/monitor' 
        WHERE path = '/admin/monitor' AND type = 0
    """)
    
    op.execute("""
        UPDATE sys_menu 
        SET path = '/scheduler' 
        WHERE path = '/admin/scheduler' AND type = 0
    """)
    
    op.execute("""
        UPDATE sys_menu 
        SET path = '/dashboard' 
        WHERE path = '/app/dashboard' AND type = 0
    """)
    
    # 2. 删除 role_type 字段
    op.drop_column('sys_role', 'role_type')
