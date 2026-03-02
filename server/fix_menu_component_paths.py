#!/usr/bin/env python3
"""
修复新添加菜单的 component 路径格式
从 /src/views/xxx 改为 /xxx（与旧菜单保持一致）
"""

import asyncio
import io
import sys

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

sys.path.insert(0, ".")

from sqlalchemy import text

from backend.database.db import async_db_session


async def fix_component_paths():
    """修复 component 路径"""
    async with async_db_session() as db:
        print("=" * 80)
        print("🔧 修复菜单 component 路径")
        print("=" * 80)
        print()

        # 需要修复的菜单映射：旧路径 -> 新路径
        fixes = {
            "/src/views/system/subscription/index": "/system/subscription/index",
            "/src/views/system/credits/index": "/system/credits/index",
            "/src/views/system/invitation/index": "/system/invitation/index",
            "/src/views/system/task/index": "/system/task/index",
            "/src/views/system/log/opera/index": "/system/log/opera/index",
            "/src/views/system/log/login/index": "/system/log/login/index",
            "/src/views/system/monitor/server/index": "/system/monitor/server/index",
            "/src/views/system/monitor/redis/index": "/system/monitor/redis/index",
        }

        for old_path, new_path in fixes.items():
            result = await db.execute(
                text(
                    """
                UPDATE sys_menu 
                SET component = :new_path
                WHERE component = :old_path
                RETURNING id, title, name
            """
                ),
                {"old_path": old_path, "new_path": new_path},
            )
            updated = result.fetchone()
            if updated:
                print(f"✅ {updated[1]:20s} ({updated[2]:30s})")
                print(f"   {old_path}")
                print(f"   -> {new_path}")
            else:
                print(f"⏭️  跳过: {old_path} (不存在)")

        await db.commit()

        print()
        print("=" * 80)
        print("✅ 修复完成！")
        print("=" * 80)


if __name__ == "__main__":
    asyncio.run(fix_component_paths())
