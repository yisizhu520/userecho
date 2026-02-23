#!/usr/bin/env python3
"""
调试菜单数据脚本
1. 打印所有菜单的 path
2. 清理 Redis 缓存
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
from backend.core.conf import settings
from backend.database.db import async_db_session
from backend.database.redis import redis_client


async def inspect_menus() -> None:
    """检查菜单数据"""
    async with async_db_session() as db:
        # 查询所有菜单
        stmt = select(Menu)
        menus = (await db.scalars(stmt)).all()

        print(f"📊 数据库中共有 {len(menus)} 个菜单")
        print("-" * 60)
        print(f"{'ID':<5} | {'Title':<30} | {'Path':<30}")
        print("-" * 60)

        admin_prefix_count = 0
        system_prefix_count = 0

        for menu in menus:
            path = menu.path or ""
            print(f"{menu.id:<5} | {menu.title:<30} | {path:<30}")

            if path.startswith("/admin"):
                admin_prefix_count += 1
            if path.startswith("/system"):
                system_prefix_count += 1

        print("-" * 60)
        print("统计结果:")
        print(f"  以 /admin 开头的菜单数: {admin_prefix_count}")
        print(f"  以 /system 开头的菜单数: {system_prefix_count}")


async def clear_cache() -> None:
    """清理缓存"""
    print("\n🧹 正在清理 Redis 缓存...")
    try:
        # 清理用户信息缓存
        await redis_client.delete_prefix(f"{settings.JWT_USER_REDIS_PREFIX}:*")
        # 清理菜单缓存 (如果有的业务逻辑用了缓存) - menu_service 似乎没直接用 Redis 存菜单结构，但是 auth_service 用了 JWT USER CACHE
        print("✅ 用户信息缓存已清理")
    except Exception as e:
        print(f"❌ 清理缓存失败: {e}")


async def main() -> int | None:
    """主函数"""
    print("=" * 80)
    print("🔍 菜单数据调试")
    print("=" * 80)
    print()

    try:
        await inspect_menus()
        await clear_cache()
        print()
        print("✅ 调试完成！")
        return 0
    except Exception as e:
        print()
        print(f"❌ 调试失败: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
