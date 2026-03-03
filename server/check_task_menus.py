"""检查任务中心菜单配置"""

import asyncio

from sqlalchemy import select, text

from backend.app.admin.model.menu import Menu
from backend.database.db import async_db_session


async def check_task_menus():
    async with async_db_session.begin() as db:
        result = await db.execute(
            select(Menu).where(text("name LIKE '%Task%' OR title LIKE '%任务%'")).order_by(Menu.path)
        )
        menus = result.scalars().all()

        print("找到的任务相关菜单：")
        print("=" * 80)
        for menu in menus:
            print(f"ID: {menu.id}")
            print(f"名称: {menu.name}")
            print(f"标题: {menu.title}")
            print(f"路径: {menu.path}")
            print(f"组件: {menu.component}")
            print(f"父菜单ID: {menu.parent_id}")
            print(f"状态: {menu.status} | 显示: {menu.display}")
            print("-" * 80)


if __name__ == "__main__":
    asyncio.run(check_task_menus())
