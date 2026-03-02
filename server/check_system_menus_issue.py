#!/usr/bin/env python3
"""
检查系统菜单问题
"""

import asyncio
import io
import sys

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

sys.path.insert(0, ".")

from sqlalchemy import select, text

from backend.app.admin.model import Menu, User
from backend.database.db import async_db_session


async def check_system_menus():
    """检查系统菜单配置"""
    async with async_db_session() as db:
        print("=" * 80)
        print("🔍 检查系统菜单问题")
        print("=" * 80)
        print()

        # 1. 查找 sysadmin 用户
        user = await db.scalar(select(User).where(User.username == "sysadmin"))
        if not user:
            print("❌ 未找到 sysadmin 用户")
            return

        print(f"👤 用户: {user.username}")
        print(f"   is_superuser: {user.is_superuser}")
        print(f"   is_staff: {user.is_staff}")
        print()

        # 2. 查询所有系统菜单
        result = await db.execute(
            text("""
            SELECT id, title, name, path, parent_id, status, display, type
            FROM sys_menu 
            WHERE path LIKE '/system%' OR name = 'System'
            ORDER BY parent_id NULLS FIRST, sort
        """)
        )
        menus = result.all()

        print(f"=== 系统菜单列表 (共 {len(menus)} 个) ===")
        for menu in menus:
            parent = f"父ID:{menu[4]}" if menu[4] else "顶级"
            status = "启用" if menu[5] == 1 else "禁用"
            display = "显示" if menu[6] == 1 else "隐藏"
            type_name = {0: "目录", 1: "菜单", 2: "按钮"}.get(menu[7], "未知")
            print(
                f"  {menu[0]:3d} | {menu[1]:20s} | {parent:10s} | {status:4s} | {display:4s} | {type_name}"
            )
        print()

        # 3. 检查 System 父菜单
        system_menu = await db.scalar(select(Menu).where(Menu.name == "System"))
        if system_menu:
            print(f"✅ System 父菜单存在 (ID: {system_menu.id})")
            print(f"   title: {system_menu.title}")
            print(f"   status: {system_menu.status}")
            print(f"   display: {system_menu.display}")
        else:
            print("❌ System 父菜单不存在！")
        print()

        # 4. 检查子菜单
        if system_menu:
            children = await db.scalars(select(Menu).where(Menu.parent_id == system_menu.id))
            children_list = list(children)
            print(f"📋 System 下的子菜单 (共 {len(children_list)} 个):")
            for child in children_list:
                status = "启用" if child.status == 1 else "禁用"
                display = "显示" if child.display == 1 else "隐藏"
                print(f"  - {child.title:20s} ({child.name:30s}) | {status} | {display}")
        print()

        # 5. 检查用户能看到的菜单
        if user.is_superuser:
            print("✅ sysadmin 是超级管理员，应该能看到所有菜单")
        else:
            print("⚠️  sysadmin 不是超级管理员")
            print("   用户的角色:")
            for role in user.roles:
                print(f"   - {role.name} (role_type: {getattr(role, 'role_type', 'N/A')})")


if __name__ == "__main__":
    asyncio.run(check_system_menus())
