"""fix_system_menu_component_paths

Revision ID: de3ddd4d73c9
Revises: 2d6098f3eae5
Create Date: 2026-01-18 23:19:51.735854

"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "de3ddd4d73c9"
down_revision = "2d6098f3eae5"
branch_labels = None
depends_on = None


def upgrade():
    """Add /src/views prefix to system menu component paths"""
    # 更新所有 /system/* 菜单的 component 路径
    # 从 /system/dept/index -> /src/views/system/dept/index
    op.execute("""
        UPDATE sys_menu
        SET component = '/src/views' || component
        WHERE component IS NOT NULL
          AND component LIKE '/system/%'
          AND component NOT LIKE '/src/views/%'
    """)


def downgrade():
    """Remove /src/views prefix from system menu component paths"""
    # 回滚：移除 /src/views 前缀
    # 从 /src/views/system/dept/index -> /system/dept/index
    op.execute("""
        UPDATE sys_menu
        SET component = REPLACE(component, '/src/views', '')
        WHERE component IS NOT NULL
          AND component LIKE '/src/views/system/%'
    """)
