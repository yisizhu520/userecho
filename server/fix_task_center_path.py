#!/usr/bin/env python3
"""
修正任务中心菜单的路径
"""

import asyncio
import io
import sys

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

sys.path.insert(0, ".")

from sqlalchemy import select

from backend.app.admin.model import Menu
from backend.database.db import async_db_session


async def fix_task_center_path():
    """修正任务中心菜单路径"""
    async with async_db_session() as db:
        print("=" * 80)
        print("🔧 修正任务中心菜单路径")
        print("=" * 80)
        print()

        # 查找任务中心菜单
        task_menu = await db.scalar(
            select(Menu).where(Menu.name == "TaskCenter")
        )

        if not task_menu:
            print("❌ 未找到任务中心菜单！")
            return

        print(f"当前配置：")
        print(f"  路径: {task_menu.path}")
        print(f"  组件: {task_menu.component}")
        print()

        # 修正路径和组件
        old_path = task_menu.path
        old_component = task_menu.component

        new_path = "/system/task-center"
        new_component = "/src/views/userecho/task-center/index"

        task_menu.path = new_path
        task_menu.component = new_component

        await db.commit()

        print(f"✅ 已修正：")
        print(f"  路径: {old_path} → {new_path}")
        print(f"  组件: {old_component} → {new_component}")
        print()
        print("=" * 80)
        print("✅ 完成！清除浏览器缓存并重新登录")
        print("=" * 80)


if __name__ == "__main__":
    asyncio.run(fix_task_center_path())
