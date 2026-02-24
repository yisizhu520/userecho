#!/usr/bin/env python3
"""修复邀请管理菜单的路径"""

import asyncio
import io
import sys

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

sys.path.insert(0, ".")

from sqlalchemy import select, update

from backend.app.admin.model import Menu
from backend.database.db import async_db_session


async def fix_invitation_menu_path():
    async with async_db_session.begin() as db:
        # 查找邀请管理菜单
        menu = await db.scalar(select(Menu).where(Menu.name == "SysInvitation"))

        if not menu:
            print("❌ 未找到邀请管理菜单")
            return False

        print(f"当前路径: {menu.path}")

        # 更新路径
        await db.execute(update(Menu).where(Menu.name == "SysInvitation").values(path="/system/invitation"))

        print("✅ 已更新路径为: /system/invitation")
        print("\n说明：后端菜单过滤逻辑要求系统管理菜单路径以 /system/ 开头")
        return True


if __name__ == "__main__":
    success = asyncio.run(fix_invitation_menu_path())
    sys.exit(0 if success else 1)
