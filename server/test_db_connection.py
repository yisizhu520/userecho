"""测试数据库连接"""

import asyncio
import sys
from backend.database.db import async_db_session
from sqlalchemy import text


async def test():
    try:
        async with async_db_session() as db:
            result = await db.execute(text("SELECT version()"))
            version = result.scalar()  # scalar() 不是异步方法
            print("✅ 数据库连接成功")
            print(f"PostgreSQL 版本: {version}")
            return True
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test())
    sys.exit(0 if success else 1)
