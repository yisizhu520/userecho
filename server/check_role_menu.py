#!/usr/bin/env python3
"""
检查角色菜单关联
"""

import asyncio
import io
import sys

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

sys.path.insert(0, ".")

from sqlalchemy import select, text

from backend.app.admin.model import Menu, Role
from backend.database.db import async_db_session


async def check_role_menu_relation():
    """检查角色菜单关联"""
    async with async_db_session() as db:
        print("=" * 80)
        print("🔍 检查角色菜单关联")
        print("=" * 80)
        print()

        # 1. 查询任务中心菜单
        task_menu = await db.scalar(select(Menu).where(Menu.name == "TaskCenter"))

        if not task_menu:
            print("❌ 未找到任务中心菜单！")
            return

        print(f"✅ 任务中心菜单 ID: {task_menu.id}")
        print()

        # 2. 查询所有系统角色
        system_roles = await db.scalars(select(Role).where(Role.role_type == "system"))

        system_roles_list = list(system_roles)
        print(f"📋 系统角色列表（{len(system_roles_list)}个）：")
        for role in system_roles_list:
            print(f"  ID={role.id}, 名称={role.name}, 类型={role.role_type}")
        print()

        # 3. 检查任务中心菜单关联的角色
        result = await db.execute(
            text("""
                SELECT r.id, r.name, r.role_type
                FROM sys_role r
                JOIN sys_role_menu rm ON r.id = rm.role_id
                WHERE rm.menu_id = :menu_id
            """),
            {"menu_id": task_menu.id},
        )

        associated_roles = result.all()
        print(f"📌 任务中心菜单关联的角色（{len(associated_roles)}个）：")
        if associated_roles:
            for row in associated_roles:
                print(f"  ID={row.id}, 名称={row.name}, 类型={row.role_type}")
        else:
            print("  ❌ 无关联角色！")
        print()

        # 4. 检查父菜单（系统管理）关联的角色
        if task_menu.parent_id:
            parent_result = await db.execute(
                text("""
                    SELECT r.id, r.name, COUNT(rm.menu_id) as menu_count
                    FROM sys_role r
                    JOIN sys_role_menu rm ON r.id = rm.role_id
                    WHERE rm.menu_id = :parent_id
                    GROUP BY r.id, r.name
                """),
                {"parent_id": task_menu.parent_id},
            )

            parent_roles = parent_result.all()
            print(f"📌 父菜单（ID={task_menu.parent_id}）关联的角色（{len(parent_roles)}个）：")
            for row in parent_roles:
                print(f"  ID={row.id}, 名称={row.name}, 菜单数量={row.menu_count}")
        print()

        # 5. 建议：需要将任务中心菜单关联到系统管理员角色
        print("=" * 80)
        print("💡 解决方案：")
        print("需要将任务中心菜单（ID=89）关联到系统管理员角色")
        print("可以使用以下 SQL 插入关联：")
        print()
        print("INSERT INTO sys_role_menu (role_id, menu_id)")
        print("SELECT r.id, 89")
        print("FROM sys_role r")
        print("WHERE r.role_type = 'system'")
        print("  AND r.name = '系统管理员'")
        print("  AND NOT EXISTS (")
        print("    SELECT 1 FROM sys_role_menu rm")
        print("    WHERE rm.role_id = r.id AND rm.menu_id = 89")
        print("  );")
        print("=" * 80)


if __name__ == "__main__":
    asyncio.run(check_role_menu_relation())
