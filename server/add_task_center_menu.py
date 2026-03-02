#!/usr/bin/env python3
"""
添加"任务中心"菜单到"系统设置"下
"""

import asyncio
import io
import sys

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

sys.path.insert(0, ".")

from sqlalchemy import select, text

from backend.app.admin.model import Menu
from backend.database.db import async_db_session


async def add_task_center_menu():
    """添加任务中心菜单"""
    async with async_db_session() as db:
        print("=" * 80)
        print("🔧 添加任务中心菜单到系统设置")
        print("=" * 80)
        print()

        # 查找"系统设置"父菜单（可能是 Settings 或 System）
        # 先尝试 Settings
        settings_menu = await db.scalar(select(Menu).where(Menu.name == "Settings"))
        
        if not settings_menu:
            # 如果没有 Settings，尝试 System
            settings_menu = await db.scalar(select(Menu).where(Menu.name == "System"))
        
        if not settings_menu:
            print("❌ 未找到系统设置父菜单！")
            print("提示：请检查数据库中是否存在 name='Settings' 或 'System' 的菜单")
            
            # 列出所有顶级菜单
            print("\n当前顶级菜单：")
            top_menus = await db.scalars(
                select(Menu).where(Menu.parent_id == None).order_by(Menu.sort)
            )
            for menu in top_menus:
                print(f"  - {menu.title} (name={menu.name}, id={menu.id})")
            return

        parent_id = settings_menu.id
        parent_name = settings_menu.title
        print(f"✅ 找到父菜单: {parent_name} (ID: {parent_id})")
        print()

        # 检查"任务中心"是否已存在
        existing = await db.scalar(
            select(Menu).where(
                Menu.name == "TaskCenter"
            )
        )

        if existing:
            print(f"⏭️  任务中心菜单已存在 (ID: {existing.id})")
            
            # 检查是否在正确的父菜单下
            if existing.parent_id != parent_id:
                print(f"   当前父菜单: {existing.parent_id} (应为: {parent_id})")
                print("   正在更新父菜单...")
                existing.parent_id = parent_id
                await db.commit()
                print("   ✅ 已更新父菜单")
            else:
                print("   父菜单正确，无需更新")
            return

        # 获取当前该父菜单下最大的 sort 值
        max_sort = await db.scalar(
            select(text("COALESCE(MAX(sort), 0)"))
            .select_from(Menu.__table__)
            .where(Menu.parent_id == parent_id)
        )
        new_sort = (max_sort or 0) + 1

        # 添加"任务中心"菜单
        menu_data = {
            "title": "任务中心",
            "name": "TaskCenter",
            "path": "/app/settings/tasks",
            "sort": new_sort,
            "icon": "lucide:activity",
            "type": 1,  # 菜单
            "component": "/src/views/userecho/task-center/index",
            "perms": None,
            "status": 1,
            "display": 1,
            "cache": 1,
            "link": "",
            "remark": "Celery 任务追踪中心，查看所有异步任务执行状态",
            "parent_id": parent_id,
        }

        await db.execute(
            text(
                """
            INSERT INTO sys_menu (
                title, name, path, sort, icon, type, component,
                perms, status, display, cache, link, remark, parent_id, created_time
            )
            VALUES (
                :title, :name, :path, :sort, :icon, :type, :component,
                :perms, :status, :display, :cache, :link, :remark, :parent_id, NOW()
            )
        """
            ),
            menu_data,
        )

        await db.commit()

        print(f"✅ 已添加: 任务中心 (排序: {new_sort})")
        print()
        print("=" * 80)
        print("✅ 完成！刷新前端页面即可看到菜单")
        print("=" * 80)


if __name__ == "__main__":
    asyncio.run(add_task_center_menu())
