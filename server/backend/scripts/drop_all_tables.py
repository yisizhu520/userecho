#!/usr/bin/env python3
"""
删除所有数据库表（使用 CASCADE）
"""

import asyncio
import io
import sys

from sqlalchemy import text

# Windows 平台 UTF-8 输出支持
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, '.')
from backend.database.db import async_engine


async def drop_all_tables() -> None:
    """删除所有表（使用 CASCADE）"""
    print('🗑️  正在删除所有数据库表...')

    async with async_engine.begin() as conn:
        # 获取所有表名
        result = await conn.execute(
            text("""
            SELECT tablename
            FROM pg_tables
            WHERE schemaname = 'public'
        """)
        )
        tables = [row[0] for row in result]

        if not tables:
            print('   ℹ️  没有找到需要删除的表')
            return

        print(f'   找到 {len(tables)} 个表')

        # 删除所有表（使用 CASCADE）
        for table in tables:
            try:
                await conn.execute(text(f'DROP TABLE IF EXISTS "{table}" CASCADE'))
                print(f'   ✅ 已删除表: {table}')
            except Exception as e:
                print(f'   ⚠️  删除表 {table} 失败: {e}')

        # 删除 alembic_version 表
        try:
            await conn.execute(text('DROP TABLE IF EXISTS alembic_version CASCADE'))
            print('   ✅ 已删除表: alembic_version')
        except Exception as e:
            print(f'   ⚠️  删除表 alembic_version 失败: {e}')

    print('✅ 所有表已删除')


async def main() -> int | None:
    try:
        await drop_all_tables()
        return 0
    except Exception as e:
        print(f'❌ 删除表失败: {e}')
        import traceback

        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
