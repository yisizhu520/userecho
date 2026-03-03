"""修正系统任务中心菜单的组件路径"""

import asyncio

from sqlalchemy import select

from backend.app.admin.model.menu import Menu
from backend.database.db import async_db_session


async def fix_system_task_center_component():
    async with async_db_session.begin() as db:
        # 查找系统任务中心菜单
        task_menu = await db.scalar(select(Menu).where(Menu.name == "TaskCenter"))

        if not task_menu:
            print("❌ 未找到 TaskCenter 菜单！")
            return

        print("当前配置：")
        print(f"  名称: {task_menu.name}")
        print(f"  标题: {task_menu.title}")
        print(f"  路径: {task_menu.path}")
        print(f"  组件: {task_menu.component}")
        print()

        # 修正组件路径
        old_component = task_menu.component
        new_component = "/userecho/task-center/index"

        if old_component == new_component:
            print("✅ 组件路径已经正确，无需修改")
            return

        task_menu.component = new_component
        await db.commit()

        print("✅ 已修正组件路径：")
        print(f"  旧路径: {old_component}")
        print(f"  新路径: {new_component}")
        print()
        print("说明：")
        print("  - 这是系统管理员的任务中心（查看所有租户任务）")
        print("  - 用户的任务中心在 /app/tasks（查看自己租户的任务）")


if __name__ == "__main__":
    asyncio.run(fix_system_task_center_component())
