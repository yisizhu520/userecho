"""修复 Alembic 迁移状态

当数据库中已有表但 alembic_version 表不存在时使用此脚本
"""

import asyncio
import sys

from sqlalchemy import text

sys.path.insert(0, ".")
from backend.database.db import async_engine


async def check_and_fix_alembic() -> None:
    """检查并修复 Alembic 状态"""
    async with async_engine.begin() as conn:
        # 检查 alembic_version 表是否存在
        result = await conn.execute(
            text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name = 'alembic_version'
            )
        """)
        )

        alembic_exists = result.scalar()

        if alembic_exists:
            # 获取当前版本
            version_result = await conn.execute(text("SELECT version_num FROM alembic_version"))
            version = version_result.scalar()
            print(f"✓ Alembic 版本表已存在，当前版本: {version}")
            return

        print("⚠️  alembic_version 表不存在")
        print()

        # 检查关键表是否存在
        tables_to_check = [
            "tenants",
            "boards",
            "customers",
            "feedbacks",
            "topics",
            "insights",
            "sys_user",
            "sys_role",
            "sys_menu",
        ]

        existing_tables = []
        missing_tables = []

        for table in tables_to_check:
            result = await conn.execute(
                text(f"""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name = '{table}'
                )
            """)
            )

            if result.scalar():
                existing_tables.append(table)
            else:
                missing_tables.append(table)

        print("📊 数据库状态:")
        print(f"   已存在的表: {len(existing_tables)}/{len(tables_to_check)}")
        print(f"   缺失的表: {len(missing_tables)}/{len(tables_to_check)}")
        print()

        if missing_tables:
            print(f"⚠️  缺失的表: {', '.join(missing_tables)}")
            print()

        # 根据情况给出建议
        if len(existing_tables) == 0:
            print("💡 建议操作:")
            print("   数据库是空的，可以直接运行迁移:")
            print("   alembic upgrade head")
        elif len(missing_tables) == 0:
            print("💡 建议操作:")
            print("   所有表都已存在，需要将 Alembic 标记为最新版本:")
            print("   alembic stamp head")
            print()
            print("   这将创建 alembic_version 表并标记为最新版本，不会修改现有表")
        else:
            print("💡 建议操作:")
            print("   数据库处于不一致状态，建议:")
            print("   1. 备份现有数据")
            print("   2. 删除所有表: python scripts/drop_all_tables.py")
            print("   3. 重新运行迁移: alembic upgrade head")


async def main() -> int | None:
    try:
        await check_and_fix_alembic()
        return 0
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
