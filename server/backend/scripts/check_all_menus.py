#!/usr/bin/env python3
"""检查所有/system和/admin路径菜单"""

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
        # 查看所有 /system/* 菜单
        print("\n" + "=" * 80)
        stmt = select(Menu).where(Menu.path.like("/system/%")).order_by(Menu.sort)
        result = await db.execute(stmt)
        system_menus = result.scalars().all()
        print(f"/system/* 菜单: 共 {len(system_menus)} 个")
        print("=" * 80)
        for menu in system_menus:
            parent_name = ""
            if menu.parent_id:
                parent = await db.get(Menu, menu.parent_id)
                parent_name = f" [父级: {parent.title if parent else '未知'}]"
            print(f"  {menu.title:20} | {menu.path:35} | sort={menu.sort:2}{parent_name}")

        # 查看是否有 invitation 相关菜单
        print("\n" + "=" * 80)
        stmt = select(Menu).where(Menu.path.like("%invitation%"))
        result = await db.execute(stmt)
        invitation_menus = result.scalars().all()
        print(f"invitation 相关菜单: 共 {len(invitation_menus)} 个")
        print("=" * 80)
        for menu in invitation_menus:
            print(f"  {menu.title:20} | {menu.path:35} | name={menu.name}")

        # 查看 System 父级菜单
        print("\n" + "=" * 80)
        stmt = select(Menu).where(Menu.name == "System")
        result = await db.execute(stmt)
        system_parent = result.scalar_one_or_none()
        if system_parent:
            print(f"System 父级菜单: {system_parent.title} (ID={system_parent.id}, path={system_parent.path})")
        else:
            print("未找到 System 父级菜单")
        print("=" * 80 + "\n")


asyncio.run(check_menus())
