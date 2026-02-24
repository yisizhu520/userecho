#!/usr/bin/env python3
import asyncio
import io
import sys

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

sys.path.insert(0, ".")

from sqlalchemy import func, select

from backend.app.admin.model import Menu
from backend.database.db import async_db_session


async def check():
    async with async_db_session() as db:
        total = await db.scalar(select(func.count(Menu.id)))
        system_count = await db.scalar(select(func.count(Menu.id)).where(Menu.path.like("/system/%")))
        admin_count = await db.scalar(select(func.count(Menu.id)).where(Menu.path.like("/admin/%")))
        invitation_count = await db.scalar(select(func.count(Menu.id)).where(Menu.path.like("%invitation%")))

        print("\n" + "=" * 60)
        print("菜单统计:")
        print("=" * 60)
        print(f"总菜单数: {total}")
        print(f"/system/* 路径: {system_count}")
        print(f"/admin/* 路径: {admin_count}")
        print(f"包含 invitation 的菜单: {invitation_count}")
        print("=" * 60 + "\n")

        # 列出前 20 个菜单
        stmt = select(Menu).limit(20)
        result = await db.execute(stmt)
        menus = result.scalars().all()

        if menus:
            print("前 20 个菜单:")
            print("-" * 80)
            for menu in menus:
                print(f"  {menu.id:3} | {menu.title:20} | {menu.path:30}")
            print("-" * 80)


asyncio.run(check())
