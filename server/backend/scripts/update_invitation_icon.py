#!/usr/bin/env python3
"""更新邀请管理菜单图标"""

import asyncio
import io
import sys

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

sys.path.insert(0, ".")

from sqlalchemy import select, update

from backend.app.admin.model import Menu
from backend.database.db import async_db_session


async def update_invitation_icon():
    """
    更新邀请管理菜单的图标

    常用可用的图标方案：
    1. lucide:mail-open (推荐 - 打开的邮件，适合邀请)
    2. lucide:send (发送图标)
    3. ant-design:mail-outlined (邮件图标)
    4. carbon:email (邮件图标)
    5. material-symbols:mail-outline (邮件轮廓)
    """
    async with async_db_session.begin() as db:
        # 先查看当前图标
        menu = await db.scalar(select(Menu).where(Menu.name == "SysInvitation"))

        if not menu:
            print("❌ 未找到邀请管理菜单")
            return False

        print(f"当前图标: {menu.icon}")

        # 更新为可用的图标
        new_icon = "lucide:mail-open"
        await db.execute(update(Menu).where(Menu.name == "SysInvitation").values(icon=new_icon))

        print(f"✅ 已更新图标为: {new_icon}")
        print("\n说明: lucide:mail-open 是一个常用的邮件/邀请图标")
        return True


if __name__ == "__main__":
    success = asyncio.run(update_invitation_icon())
    sys.exit(0 if success else 1)
