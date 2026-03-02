"""检查数据库触发器状态"""

import asyncio

from sqlalchemy import text

from backend.database.db import async_db_session


async def check_triggers():
    """检查触发器状态"""
    async with async_db_session.begin() as db:
        # 检查触发器
        trigger_query = text("""
            SELECT 
                t.tgname AS trigger_name,
                c.relname AS table_name,
                p.proname AS function_name
            FROM pg_trigger t
            JOIN pg_class c ON t.tgrelid = c.oid
            JOIN pg_proc p ON t.tgfoid = p.oid
            WHERE t.tgname LIKE '%board%'
            ORDER BY c.relname, t.tgname
        """)

        result = await db.execute(trigger_query)
        triggers = result.fetchall()

        print("=" * 80)
        print("数据库触发器状态检查")
        print("=" * 80)
        print()

        if triggers:
            print(f"找到 {len(triggers)} 个相关触发器:")
            print()
            for trigger_name, table_name, function_name in triggers:
                print(f"  - 触发器: {trigger_name}")
                print(f"    表: {table_name}")
                print(f"    函数: {function_name}")
                print()
        else:
            print("未找到相关触发器！")
            print()
            print("建议执行以下命令创建触发器:")
            print("  cd server")
            print("  python db_migrate.py upgrade head")


if __name__ == "__main__":
    asyncio.run(check_triggers())
