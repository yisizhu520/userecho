#!/usr/bin/env python3
"""
添加缺失的系统菜单项
- 积分管理
- 订阅管理
"""

import asyncio
import io
import sys

# Windows 平台 UTF-8 输出支持
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

sys.path.insert(0, ".")

from sqlalchemy import select

from backend.app.admin.model import Menu
from backend.database.db import async_db_session
from backend.utils.timezone import timezone


async def add_missing_menus() -> None:
    """添加缺失的系统菜单"""
    async with async_db_session() as db:
        # 获取 System 菜单的 ID
        stmt = select(Menu).where(Menu.name == "System")
        system_menu = await db.scalar(stmt)

        if not system_menu:
            print("❌ 未找到 System 菜单，无法继续")
            return

        system_menu_id = system_menu.id
        print(f"✅ 找到 System 菜单 (ID: {system_menu_id})")

        # 检查菜单是否已存在
        existing_credits = await db.scalar(select(Menu).where(Menu.name == "SysCredits"))
        existing_subscription = await db.scalar(select(Menu).where(Menu.name == "SysSubscription"))

        menus_to_add = []

        # 1. 添加"积分管理"
        if not existing_credits:
            credits_menu = Menu(
                title="积分管理",
                name="SysCredits",
                path="/system/credits",
                sort=11,
                icon="carbon:user-certification",
                type=1,  # 菜单
                component="/src/views/system/credits/index",
                perms=None,
                status=1,
                display=1,
                cache=1,
                link="",
                remark="系统积分配置管理",
                parent_id=system_menu_id,
                created_time=timezone.now(),
            )
            menus_to_add.append(credits_menu)
            print("  📝 准备添加: 积分管理")
        else:
            print("  ⏭️  积分管理菜单已存在，跳过")

        # 2. 添加"订阅管理"
        if not existing_subscription:
            subscription_menu = Menu(
                title="订阅管理",
                name="SysSubscription",
                path="/system/subscription",
                sort=10,
                icon="eos-icons:subscription-management-outlined",
                type=1,  # 菜单
                component="/src/views/system/subscription/index",
                perms=None,
                status=1,
                display=1,
                cache=1,
                link="",
                remark="系统订阅套餐管理",
                parent_id=system_menu_id,
                created_time=timezone.now(),
            )
            menus_to_add.append(subscription_menu)
            print("  📝 准备添加: 订阅管理")
        else:
            print("  ⏭️  订阅管理菜单已存在，跳过")

        # 批量添加
        if menus_to_add:
            db.add_all(menus_to_add)
            await db.commit()
            print(f"\n✅ 成功添加 {len(menus_to_add)} 个菜单！")
        else:
            print("\n✅ 所有菜单已存在，无需添加")


async def main() -> int | None:
    """主函数"""
    print("=" * 80)
    print("🔧 添加缺失的系统菜单")
    print("=" * 80)
    print()

    try:
        await add_missing_menus()
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
