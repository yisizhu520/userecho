"""测试数据库连接"""

import asyncio

from sqlalchemy import text

from backend.core.conf import settings


async def test_connection() -> bool | None:
    print('🔍 测试数据库连接...')
    print(f'   类型: {settings.DATABASE_TYPE}')
    print(f'   主机: {settings.DATABASE_HOST}')
    print(f'   端口: {settings.DATABASE_PORT}')
    print(f'   数据库: {settings.DATABASE_SCHEMA}')

    try:
        from backend.database.db import async_engine

        async with async_engine.begin() as conn:
            await conn.execute(text('SELECT 1'))
        print('✅ 数据库连接成功！')
        return True
    except Exception as e:
        print(f'❌ 数据库连接失败: {e}')
        import traceback

        traceback.print_exc()
        return False


if __name__ == '__main__':
    asyncio.run(test_connection())
