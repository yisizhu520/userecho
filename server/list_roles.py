#!/usr/bin/env python3
"""
查询所有角色信息
"""

import asyncio
import io
import sys

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

sys.path.insert(0, ".")

from sqlalchemy import select, text

from backend.app.admin.model import Role
from backend.database.db import async_db_session


async def list_all_roles():
    """列出所有角色"""
    async with async_db_session() as db:
        print("=" * 80)
        print("🔍 查询所有角色")
        print("=" * 80)
        print()

        # 查询所有角色
        roles = await db.scalars(select(Role).order_by(Role.id))

        roles_list = list(roles)
        print(f"📋 数据库中的角色（{len(roles_list)}个）：")
        print()

        for role in roles_list:
            print(f"ID: {role.id}")
            print(f"  名称: {role.name}")
            print(f"  角色类型: {role.role_type}")
            print(f"  状态: {role.status}")
            print(f"  备注: {role.remark}")
            print()

        # 检查菜单关联
        result = await db.execute(
            text("""
                SELECT r.id, r.name, r.role_type, COUNT(rm.menu_id) as menu_count
                FROM sys_role r
                LEFT JOIN sys_role_menu rm ON r.id = rm.role_id
                GROUP BY r.id, r.name, r.role_type
                ORDER BY r.id
            """)
        )

        print("=" * 80)
        print("📊 角色菜单关联统计：")
        print("=" * 80)
        for row in result.all():
            print(f"ID={row.id}, 名称={row.name}, 类型={row.role_type}, 菜单数量={row.menu_count}")
        print()


if __name__ == "__main__":
    asyncio.run(list_all_roles())
