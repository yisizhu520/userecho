"""检查并执行 Alembic 迁移"""

import asyncio
import sys

from sqlalchemy import text

sys.path.insert(0, ".")
from backend.database.db import async_engine


async def check_alembic_version():
    """检查当前 Alembic 版本"""
    async with async_engine.connect() as conn:
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

        table_exists = result.scalar()

        if not table_exists:
            print("❌ alembic_version 表不存在")
            print("   需要初始化 Alembic 或运行迁移")
            return None

        # 获取当前版本
        version_result = await conn.execute(text("SELECT version_num FROM alembic_version"))
        version = version_result.scalar()

        if version:
            print(f"✓ 当前 Alembic 版本: {version}")
        else:
            print("⚠️  alembic_version 表为空")

        return version


async def main() -> int | None:
    try:
        await check_alembic_version()
        return 0
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
