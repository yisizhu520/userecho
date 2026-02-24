#!/usr/bin/env python3
"""检查系统菜单"""

import asyncio
import io
import sys

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

sys.path.insert(0, ".")

from sqlalchemy import select

from backend.app.admin.model import Menu
from backend.database.db import async_db_session


async def check_menus():
    async with async_db_session() as db:
        # 查看所有系统菜单
        stmt = select(Menu).where(Menu.path.like("/admin/%")).order_by(Menu.sort)
        result = await db.execute(stmt)
        menus = result.scalars().all()

        print("\n" + "=" * 80)
        print(f"系统管理菜单 (/admin/*): 共 {len(menus)} 个")
        print("=" * 80)
        for menu in menus:
            parent_name = ""
            if menu.parent_id:
                parent = await db.get(Menu, menu.parent_id)
                parent_name = f" [父级: {parent.title if parent else '未知'}]"
            print(f"  {menu.title:15} | {menu.path:30} | sort={menu.sort:2}{parent_name}")

        print("\n" + "=" * 80)


asyncio.run(check_menus())
