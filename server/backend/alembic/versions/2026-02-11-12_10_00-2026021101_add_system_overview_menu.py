"""add_system_overview_menu

Revision ID: 2026021101
Revises: a3f7b8c9d0e1
Create Date: 2026-02-11 12:10:00.000000

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "2026021101"
down_revision = "a3f7b8c9d0e1"
branch_labels = None
depends_on = None


def upgrade():
    """新增系统概览菜单并关联到系统角色。
    
    兼容新旧路径格式：
    - 新格式: /admin/system (已执行路径迁移)
    - 旧格式: /system (未执行路径迁移)
    """
    # 1) 新增菜单（幂等，兼容新旧路径）
    op.execute(
        """
        INSERT INTO sys_menu (
            title, name, path, sort, icon, type, component, perms,
            status, display, cache, link, remark, parent_id, created_time
        )
        SELECT
            'page.menu.sysOverview',
            'SysOverview',
            CASE 
                WHEN parent.path = '/admin/system' THEN '/admin/system/overview'
                ELSE '/system/overview'
            END,
            0,
            'lucide:layout-dashboard',
            1,
            '/src/views/system/overview/index',
            'sys:overview:view',
            1,
            1,
            1,
            '',
            '系统管理概览页',
            parent.id,
            NOW()
        FROM sys_menu parent
        WHERE (parent.path = '/admin/system' OR parent.path = '/system')
          AND parent.type = 0
          AND NOT EXISTS (
              SELECT 1
              FROM sys_menu m
              WHERE m.path IN ('/admin/system/overview', '/system/overview')
          )
        LIMIT 1
        """
    )

    # 2) 关联到所有 system 角色（幂等）
    op.execute(
        """
        INSERT INTO sys_role_menu (role_id, menu_id)
        SELECT r.id, m.id
        FROM sys_role r
        JOIN sys_menu m ON m.path IN ('/admin/system/overview', '/system/overview')
        WHERE r.role_type = 'system'
          AND NOT EXISTS (
              SELECT 1
              FROM sys_role_menu rm
              WHERE rm.role_id = r.id
                AND rm.menu_id = m.id
          )
        """
    )


def downgrade():
    """回滚系统概览菜单和角色关联（兼容新旧路径）。"""
    # 1) 先删除角色菜单关联
    op.execute(
        """
        DELETE FROM sys_role_menu
        WHERE menu_id IN (
            SELECT id
            FROM sys_menu
            WHERE path IN ('/admin/system/overview', '/system/overview')
        )
        """
    )

    # 2) 再删除菜单本身
    op.execute(
        """
        DELETE FROM sys_menu
        WHERE path IN ('/admin/system/overview', '/system/overview')
          AND name = 'SysOverview'
        """
    )
