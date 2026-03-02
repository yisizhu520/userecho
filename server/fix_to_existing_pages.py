#!/usr/bin/env python3
"""
修复菜单 component 路径，指向正确的已存在页面
"""

import asyncio
import io
import sys

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

sys.path.insert(0, ".")

from sqlalchemy import text

from backend.database.db import async_db_session


async def fix_to_existing_pages():
    """修复 component 路径，指向已存在的页面"""
    async with async_db_session() as db:
        print("=" * 80)
        print("🔧 修复菜单 component 路径（指向已存在的页面）")
        print("=" * 80)
        print()

        # 需要修复的菜单：name -> 正确的 component 路径
        fixes = {
            "SysTask": "/scheduler/manage/index",
            "SysOperaLog": "/log/opera/index",
            "SysLoginLog": "/log/login/index",
            "SysMonitorServer": "/monitor/server/index",
            "SysMonitorRedis": "/monitor/redis/index",
        }

        for menu_name, correct_path in fixes.items():
            result = await db.execute(
                text(
                    """
                UPDATE sys_menu 
                SET component = :new_path
                WHERE name = :menu_name
                RETURNING id, title, name
            """
                ),
                {"menu_name": menu_name, "new_path": correct_path},
            )
            updated = result.fetchone()
            if updated:
                print(f"✅ {updated[1]:20s} ({updated[2]:30s})")
                print(f"   -> {correct_path}")
            else:
                print(f"⏭️  跳过: {menu_name} (不存在)")

        await db.commit()

        print()
        print("=" * 80)
        print("✅ 修复完成！所有菜单现在指向已存在的页面")
        print("=" * 80)


if __name__ == "__main__":
    asyncio.run(fix_to_existing_pages())
