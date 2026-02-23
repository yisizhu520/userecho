#!/usr/bin/env python3
"""
添加额外的系统管理菜单（积分管理、订阅管理）
这些菜单是后来添加的，不在 fba init 的基础数据中
"""

import asyncio
import io
import sys

# Windows 平台 UTF-8 输出支持
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

sys.path.insert(0, ".")

from sqlalchemy import select, text

from backend.app.admin.model import Menu
from backend.database.db import async_db_session


async def add_extra_system_menus() -> None:
    """添加额外的系统管理菜单"""
    async with async_db_session() as db:
        # 获取 System 菜单的 ID
        stmt = select(Menu).where(Menu.name == "System")
        system_menu = await db.scalar(stmt)

        if not system_menu:
            print("❌ 未找到 System 菜单，跳过添加额外菜单")
            return

        system_menu_id = system_menu.id
        print(f"✅ 找到 System 菜单 (ID: {system_menu_id})")

        # 检查菜单是否已存在
        existing_credits = await db.scalar(select(Menu).where(Menu.name == "SysCredits"))
        existing_subscription = await db.scalar(select(Menu).where(Menu.name == "SysSubscription"))

        menus_added = 0

        # 1. 添加"订阅管理"（优先级更高，sort=10）
        if not existing_subscription:
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
                {
                    "title": "订阅管理",
                    "name": "SysSubscription",
                    "path": "/system/subscription",
                    "sort": 10,
                    "icon": "lucide:credit-card",
                    "type": 1,
                    "component": "/src/views/system/subscription/index",
                    "perms": None,
                    "status": 1,
                    "display": 1,
                    "cache": 1,
                    "link": "",
                    "remark": "系统订阅套餐管理",
                    "parent_id": system_menu_id,
                },
            )
            print("  ✅ 已添加: 订阅管理")
            menus_added += 1
        else:
            print("  ⏭️  订阅管理菜单已存在，跳过")

        # 2. 添加"积分管理"
        if not existing_credits:
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
                {
                    "title": "积分管理",
                    "name": "SysCredits",
                    "path": "/system/credits",
                    "sort": 11,
                    "icon": "carbon:user-certification",
                    "type": 1,
                    "component": "/src/views/system/credits/index",
                    "perms": None,
                    "status": 1,
                    "display": 1,
                    "cache": 1,
                    "link": "",
                    "remark": "系统积分配置管理",
                    "parent_id": system_menu_id,
                },
            )
            print("  ✅ 已添加: 积分管理")
            menus_added += 1
        else:
            print("  ⏭️  积分管理菜单已存在，跳过")

        # 提交事务
        if menus_added > 0:
            await db.commit()
            print(f"\n✅ 成功添加 {menus_added} 个额外系统菜单")
        else:
            print("\n✅ 所有额外系统菜单已存在，无需添加")


async def main() -> int:
    """主函数"""
    print("=" * 80)
    print("🔧 添加额外系统管理菜单")
    print("=" * 80)
    print()

    try:
        await add_extra_system_menus()
        print()
        print("✅ 完成！")
        return 0
    except Exception as e:
        print()
        print(f"❌ 失败: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
