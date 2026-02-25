"""显示数据库连接信息和表位置"""

import asyncio
import sys
import io

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from pathlib import Path

backend_path = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_path))

from sqlalchemy import text

from backend.core.conf import settings
from backend.database.db import async_db_session


async def check():
    async with async_db_session() as db:
        print("=" * 70)
        print("🔍 数据库连接信息")
        print("=" * 70)
        print()

        print(f"数据库类型: {settings.DATABASE_TYPE}")
        print(f"主机: {settings.DATABASE_HOST}")
        print(f"端口: {settings.DATABASE_PORT}")
        print(f"用户: {settings.DATABASE_USER}")
        print(f"Schema: {settings.DATABASE_SCHEMA}")
        print()

        # 查询当前数据库名称
        result = await db.execute(text("SELECT current_database()"))
        current_db = result.scalar()
        print(f"✅ 当前连接的数据库: {current_db}")

        # 查询当前 schema
        result = await db.execute(text("SELECT current_schema()"))
        current_schema = result.scalar()
        print(f"✅ 当前使用的 Schema: {current_schema}")
        print()

        print("=" * 70)
        print("📋 tenant_user_roles 表信息")
        print("=" * 70)
        print()

        # 检查表是否存在
        result = await db.execute(
            text(
                """
            SELECT schemaname, tablename 
            FROM pg_tables 
            WHERE tablename = 'tenant_user_roles'
            """
            )
        )
        tables = result.all()

        if tables:
            print("✅ 找到 tenant_user_roles 表:")
            for schema, table in tables:
                print(f"   - Schema: {schema}, 表名: {table}")

                # 查询该表的记录数
                count_result = await db.execute(text(f"SELECT COUNT(*) FROM {schema}.tenant_user_roles"))
                count = count_result.scalar()
                print(f"     记录数: {count}")
        else:
            print("❌ 未找到 tenant_user_roles 表")
        print()

        print("=" * 70)
        print("💡 提示")
        print("=" * 70)
        print()
        print("请在数据库客户端中连接到:")
        print(f"  数据库: {current_db}")
        print(f"  Schema: {current_schema}")
        print()
        print("然后执行查询:")
        print(f"  SELECT * FROM {current_schema}.tenant_user_roles;")
        print()
        print("或者在查询时显式指定 Schema:")
        print("  SELECT * FROM tenant_user_roles;  -- 使用 search_path")
        print()


asyncio.run(check())
