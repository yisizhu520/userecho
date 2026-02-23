#!/usr/bin/env python3
"""
添加系统设置菜单

用法:
    python add_settings_menus.py
"""

import asyncio
import sys

from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select

from backend.app.admin.model import Menu, Role, role_menu
from backend.database.db import async_db_session, async_engine


async def add_settings_menus() -> None:
    """添加系统设置菜单"""
    async with async_db_session.begin() as db:
        print("📋 开始添加系统设置菜单...")
        print("=" * 60)

        # 1. 创建系统设置父菜单
        print("\n1️⃣  创建系统设置父菜单...")
        settings_parent = await db.scalar(select(Menu).where(Menu.path == "/app/settings"))

        if not settings_parent:
            settings_parent = Menu(
                title="系统设置",
                name="Settings",
                path="/app/settings",
                component="",  # 父菜单不需要 component
                icon="lucide:settings",
                perms="app:settings:view",
                parent_id=None,
                type=0,  # 0=目录, 1=菜单
                status=1,
                display=1,
                sort=199,  # 放在最后
            )
            db.add(settings_parent)
            await db.flush()
            print(f"   ✅ 创建父菜单: 系统设置 (ID: {settings_parent.id})")
        else:
            print(f"   ⏭️  父菜单已存在 (ID: {settings_parent.id})")

        # 2. 创建子菜单
        print("\n2️⃣  创建子菜单...")
        sub_menus = [
            {
                "title": "成员管理",
                "name": "MembersManage",
                "path": "/app/settings/members",
                "component": "/userecho/settings/members",
                "icon": "lucide:users",
                "perms": "app:settings:members",
                "sort": 1,
            },
            {
                "title": "角色管理",
                "name": "RolesManage",
                "path": "/app/settings/roles",
                "component": "/userecho/settings/roles",
                "icon": "lucide:shield",
                "perms": "app:settings:roles",
                "sort": 2,
            },
            {
                "title": "积分配置",
                "name": "CreditsConfig",
                "path": "/app/settings/credits",
                "component": "/userecho/settings/credits-config",
                "icon": "lucide:coins",
                "perms": "app:settings:credits",
                "sort": 3,
            },
        ]

        created_menus = []
        menu_ids = [settings_parent.id]  # 包含父菜单

        for menu_data in sub_menus:
            existing = await db.scalar(select(Menu).where(Menu.path == menu_data["path"]))

            if not existing:
                menu = Menu(
                    **menu_data,
                    parent_id=settings_parent.id,
                    type=1,  # 菜单
                    status=1,
                    display=1,
                )
                db.add(menu)
                await db.flush()
                created_menus.append(menu_data["title"])
                menu_ids.append(menu.id)
                print(f"   ✅ 创建子菜单: {menu_data['title']} (ID: {menu.id})")
            else:
                print(f"   ⏭️  子菜单已存在: {menu_data['title']} (ID: {existing.id})")
                menu_ids.append(existing.id)

        # 3. 为管理员角色分配菜单权限
        print("\n3️⃣  为管理员角色分配菜单权限...")

        # 查找所有管理员相关的角色
        admin_roles = await db.scalars(
            select(Role).where((Role.name == "老板") | (Role.name == "PM") | (Role.name == "Admin"))
        )
        admin_roles_list = list(admin_roles)

        if not admin_roles_list:
            print("   ⚠️  未找到管理员角色,跳过权限分配")
        else:
            for role in admin_roles_list:
                # 检查是否已经有权限
                for menu_id in menu_ids:
                    existing_perm = await db.scalar(
                        select(role_menu).where((role_menu.c.role_id == role.id) & (role_menu.c.menu_id == menu_id))
                    )

                    if not existing_perm:
                        await db.execute(role_menu.insert().values(role_id=role.id, menu_id=menu_id))

                print(f'   ✅ 为角色 "{role.name}" 分配系统设置菜单权限')

        print("\n✅ 系统设置菜单添加完成!")
        print("\n📝 创建的菜单:")
        print("   - 系统设置 (父菜单)")
        print("   - 成员管理")
        print("   - 角色管理")
        print("   - 积分配置")


async def verify_menus() -> None:
    """验证菜单创建结果"""
    async with async_db_session() as db:
        print("\n\n🔍 验证菜单创建结果...")
        print("=" * 60)

        stmt = select(Menu).where(Menu.path.like("/app/settings%")).order_by(Menu.sort)
        result = await db.execute(stmt)
        menus = result.scalars().all()

        if menus:
            print(f"\n✅ 找到 {len(menus)} 个系统设置菜单:")
            for menu in menus:
                parent_info = f" (父菜单 ID: {menu.parent_id})" if menu.parent_id else " (顶级菜单)"
                print(f"   - {menu.title} ({menu.path}){parent_info}")
        else:
            print("\n❌ 未找到系统设置菜单!")


async def main() -> int | None:
    """主函数"""
    try:
        await add_settings_menus()
        await verify_menus()

        print("\n" + "=" * 60)
        print("✅ 完成!")
        print("=" * 60)
        print("\n💡 现在你可以访问 /app/settings/members 页面了!")

        return 0
    except Exception as e:
        print(f"\n❌ 执行失败: {e}")
        import traceback

        traceback.print_exc()
        return 1
    finally:
        await async_engine.dispose()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
