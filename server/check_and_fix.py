"""
检查 boards 表的约束和索引
"""

import os
import asyncio
from pathlib import Path

# 加载 .env 文件
from dotenv import load_dotenv

backend_path = Path(__file__).parent / "backend"
env_path = backend_path / ".env"
load_dotenv(env_path)

import asyncpg


async def main():
    """检查 boards 表的约束和索引"""

    # 从环境变量读取数据库配置
    db_host = os.getenv("DATABASE_HOST", "localhost")
    db_port = os.getenv("DATABASE_PORT", "5432")
    db_user = os.getenv("DATABASE_USER", "postgres")
    db_password = os.getenv("DATABASE_PASSWORD", "")
    db_name = os.getenv("DATABASE_SCHEMA", "userecho")

    print(f"正在连接数据库: {db_user}@{db_host}:{db_port}/{db_name}\n")

    # 创建连接
    conn = await asyncpg.connect(
        host=db_host,
        port=int(db_port),
        user=db_user,
        password=db_password,
        database=db_name,
    )

    try:
        print("=" * 80)
        print("【检查 boards 表的主键约束】")
        print("=" * 80)

        constraints = await conn.fetch("""
            SELECT 
                con.conname AS constraint_name,
                con.contype AS constraint_type,
                pg_get_constraintdef(con.oid) AS constraint_definition
            FROM pg_constraint con
            JOIN pg_class rel ON rel.oid = con.conrelid
            JOIN pg_namespace nsp ON nsp.oid = rel.relnamespace
            WHERE rel.relname = 'boards'
        """)

        print(f"\n📊 找到 {len(constraints)} 个约束:\n")
        for constraint in constraints:
            print(f"约束名: {constraint['constraint_name']}")
            print(f"  类型: {constraint['constraint_type']}")
            print(f"  定义: {constraint['constraint_definition']}")
            print()

        print("=" * 80)
        print("【检查 boards 表的索引】")
        print("=" * 80)

        indexes = await conn.fetch("""
            SELECT
                indexname,
                indexdef
            FROM pg_indexes
            WHERE tablename = 'boards'
        """)

        print(f"\n📊 找到 {len(indexes)} 个索引:\n")
        for index in indexes:
            print(f"索引名: {index['indexname']}")
            print(f"  定义: {index['indexdef']}")
            print()

        print("=" * 80)
        print("【尝试删除 ctid=(18,24) 的记录】")
        print("=" * 80)

        print("\n尝试直接删除...")
        try:
            result = await conn.execute("DELETE FROM boards WHERE ctid = '(18,24)'::tid")
            print(f"✅ 删除成功！结果: {result}")
        except Exception as e:
            print(f"❌ 删除失败: {e}")

        print("\n" + "=" * 80)
        print("【验证删除结果】")
        print("=" * 80)

        all_boards = await conn.fetch("""
            SELECT ctid::text, id, name
            FROM boards
            ORDER BY created_time ASC
        """)

        print(f"\n📊 当前有 {len(all_boards)} 条 board 记录\n")

        default_count = 0
        for board in all_boards:
            if board["id"] == "default-board":
                default_count += 1
                print(f"  default-board 记录 {default_count}:")
                print(f"    ctid: {board['ctid']}")
                print(f"    name: {board['name']}")

        if default_count == 1:
            print("\n✅ 清理成功！")
        elif default_count == 2:
            print("\n❌ 还是有 2 条记录，删除失败")
        else:
            print(f"\n⚠️  有 {default_count} 条 default-board 记录")

    finally:
        await conn.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback

        traceback.print_exc()
