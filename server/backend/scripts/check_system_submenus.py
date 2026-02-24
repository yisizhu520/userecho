#!/usr/bin/env python3
"""检查邀请管理菜单的数据库记录"""

import asyncio
import io
import sys

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

sys.path.insert(0, ".")

from sqlalchemy import select

from backend.app.admin.model import Menu
from backend.database.db import async_db_session


async def check():
    async with async_db_session() as db:
        # 查找所有 System 的子菜单，按 sort 排序
        stmt = select(Menu).where(Menu.parent_id == 4).order_by(Menu.sort)
        result = await db.execute(stmt)
        menus = result.scalars().all()

        print("\n" + "=" * 100)
        print(f"System 菜单的所有子菜单（parent_id=4）: 共 {len(menus)} 个")
        print("=" * 100)
        for menu in menus:
            status_str = "启用" if menu.status == 1 else "禁用"
            display_str = "显示" if menu.display == 1 else "隐藏"
            print(
                f"  {menu.id:3} | {menu.name:20} | {menu.path:30} | sort={menu.sort:2} | {status_str} | {display_str}"
            )
        print("=" * 100 + "\n")

        # 单独检查邀请管理
        invitation_menu = await db.scalar(select(Menu).where(Menu.name == "SysInvitation"))
        if invitation_menu:
            print("邀请管理菜单详情:")
            print("-" * 100)
            print(f"  ID: {invitation_menu.id}")
            print(f"  名称: {invitation_menu.name}")
            print(f"  标题: {invitation_menu.title}")
            print(f"  路径: {invitation_menu.path}")
            print(f"  父级ID: {invitation_menu.parent_id}")
            print(f"  排序: {invitation_menu.sort}")
            print(f"  类型: {invitation_menu.type}")
            print(f"  组件: {invitation_menu.component}")
            print(f"  状态: {invitation_menu.status} ({'启用' if invitation_menu.status == 1 else '禁用'})")
            print(f"  显示: {invitation_menu.display} ({'显示' if invitation_menu.display == 1 else '隐藏'})")
            print(f"  缓存: {invitation_menu.cache}")
            print(f"  图标: {invitation_menu.icon}")
            print("-" * 100)
        else:
            print("❌ 未找到邀请管理菜单")


asyncio.run(check())
