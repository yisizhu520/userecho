#!/usr/bin/env python3
"""验证邀请管理菜单是否创建成功"""

import asyncio
import io
import sys

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

sys.path.insert(0, ".")

from sqlalchemy import select

from backend.app.admin.model import Menu
from backend.database.db import async_db_session


async def verify():
    async with async_db_session() as db:
        # 查找邀请管理菜单
        menu = await db.scalar(select(Menu).where(Menu.name == "SysInvitation"))

        print("\n" + "=" * 80)
        if menu:
            print("✅ 邀请管理菜单已成功创建")
            print("=" * 80)
            print(f"  标题: {menu.title}")
            print(f"  名称: {menu.name}")
            print(f"  路径: {menu.path}")
            print(f"  排序: {menu.sort}")
            print(f"  图标: {menu.icon}")
            print(f"  组件: {menu.component}")
            print(f"  备注: {menu.remark}")
            print(f"  父级ID: {menu.parent_id}")
            print(f"  状态: {'启用' if menu.status == 1 else '禁用'}")
            print(f"  显示: {'显示' if menu.display == 1 else '隐藏'}")

            # 查找父级菜单
            if menu.parent_id:
                parent = await db.get(Menu, menu.parent_id)
                if parent:
                    print(f"  父级菜单: {parent.title} ({parent.path})")
        else:
            print("❌ 邀请管理菜单未找到")
        print("=" * 80 + "\n")


asyncio.run(verify())
