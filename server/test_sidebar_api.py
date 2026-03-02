#!/usr/bin/env python3
"""
测试侧边栏菜单 API
"""

import asyncio
import io
import sys

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

sys.path.insert(0, ".")

from sqlalchemy import select

from backend.app.admin.model import Menu, Role
from backend.database.db import async_db_session


async def test_sidebar_logic():
    """测试侧边栏逻辑"""
    async with async_db_session() as db:
        print("=" * 80)
        print("🔍 测试侧边栏菜单逻辑")
        print("=" * 80)
        print()

        # 1. 查找任务中心菜单
        task_menu = await db.scalar(
            select(Menu).where(Menu.name == "TaskCenter")
        )

        if not task_menu:
            print("❌ 未找到任务中心菜单！")
            return

        print(f"✅ 找到任务中心菜单：")
        print(f"  ID: {task_menu.id}")
        print(f"  名称: {task_menu.name}")
        print(f"  标题: {task_menu.title}")
        print(f"  路径: {task_menu.path}")
        print(f"  父菜单ID: {task_menu.parent_id}")
        print(f"  状态: {task_menu.status}")
        print(f"  显示: {task_menu.display}")
        print(f"  类型: {task_menu.type}")
        print()

        # 2. 检查过滤逻辑
        SYSTEM_PREFIX = "/system"
        path = task_menu.path or ""
        
        print(f"📋 过滤逻辑检查：")
        print(f"  路径: {path}")
        print(f"  前缀: {SYSTEM_PREFIX}")
        print(f"  startswith: {path.startswith(SYSTEM_PREFIX)}")
        print()

        # 3. 查找系统管理员角色
        system_admin_role = await db.scalar(
            select(Role).where(Role.name == "系统管理员")
        )

        if system_admin_role:
            print(f"✅ 找到系统管理员角色：")
            print(f"  ID: {system_admin_role.id}")
            print(f"  名称: {system_admin_role.name}")
            print(f"  类型: {system_admin_role.role_type}")
            
            # 加载关联的菜单
            await db.refresh(system_admin_role, ["menus"])
            
            menu_ids = [m.id for m in system_admin_role.menus]
            print(f"  关联菜单数量: {len(menu_ids)}")
            print(f"  任务中心菜单ID={task_menu.id} 是否在列表中: {task_menu.id in menu_ids}")
            print()

        # 4. 查询系统菜单（status=1, display=1, path like '/system%'）
        system_menus = await db.scalars(
            select(Menu)
            .where(
                Menu.status == 1,
                Menu.display == 1,
                Menu.path.like("/system%")
            )
            .order_by(Menu.sort)
        )
        
        system_menus_list = list(system_menus)
        print(f"📊 系统菜单列表（{len(system_menus_list)}个）：")
        for menu in system_menus_list:
            marker = "👉" if menu.id == task_menu.id else "  "
            print(f"{marker} ID={menu.id}, 路径={menu.path}, 标题={menu.title}")
        print()

        print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_sidebar_logic())
