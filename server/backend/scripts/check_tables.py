"""检查数据库中的表"""
import asyncio
import sys
from sqlalchemy import text

sys.path.insert(0, '.')
from backend.database.db import async_engine


async def check_tables():
    """检查数据库中存在的表"""
    async with async_engine.connect() as conn:
        # 查询所有表
        result = await conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """))
        
        tables = [row[0] for row in result]
        
        print(f"\n数据库中共有 {len(tables)} 个表:")
        for table in tables:
            print(f"  - {table}")
        
        # 检查 insights 表是否存在
        if 'insights' in tables:
            print("\n✓ insights 表存在")
        else:
            print("\n✗ insights 表不存在")
        
        # 检查 alembic_version 表
        if 'alembic_version' in tables:
            version_result = await conn.execute(text("SELECT version_num FROM alembic_version"))
            version = version_result.scalar()
            print(f"\n当前 Alembic 版本: {version}")


if __name__ == "__main__":
    asyncio.run(check_tables())
