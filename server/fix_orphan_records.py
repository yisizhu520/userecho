"""
查询 topics 表，找出所有引用不存在的 board_id 的记录
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
    """查询数据不一致问题"""

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
        print("【查找 topics 表中引用不存在 board_id 的记录】")
        print("=" * 80)

        orphan_topics = await conn.fetch("""
            SELECT t.id, t.board_id, t.title
            FROM topics t
            LEFT JOIN boards b ON t.board_id = b.id
            WHERE b.id IS NULL
        """)

        print(f"\n📊 找到 {len(orphan_topics)} 条孤儿 topics 记录\n")

        for topic in orphan_topics:
            print(f"Topic ID: {topic['id']}")
            print(f"  board_id: {topic['board_id']} (不存在！)")
            print(f"  title: {topic['title']}")
            print()

        print("=" * 80)
        print("【查找 feedbacks 表中引用不存在 board_id 的记录】")
        print("=" * 80)

        orphan_feedbacks = await conn.fetch("""
            SELECT f.id, f.board_id, f.content
            FROM feedbacks f
            LEFT JOIN boards b ON f.board_id = b.id
            WHERE b.id IS NULL
        """)

        print(f"\n📊 找到 {len(orphan_feedbacks)} 条孤儿 feedbacks 记录\n")

        for feedback in orphan_feedbacks:
            print(f"Feedback ID: {feedback['id']}")
            print(f"  board_id: {feedback['board_id']} (不存在！)")
            print(f"  content: {feedback['content'][:50] if feedback['content'] else 'None'}...")
            print()

        # 修复方案
        print("=" * 80)
        print("【修复方案】")
        print("=" * 80)

        if len(orphan_topics) > 0 or len(orphan_feedbacks) > 0:
            print("\n数据库有孤儿记录！需要先清理这些记录，才能删除重复的 board。\n")
            print("修复步骤：")
            print("1. 删除所有孤儿 topics 记录")
            print("2. 删除所有孤儿 feedbacks 记录")
            print("3. 再删除重复的 default-board 记录")

            user_input = input("\n是否执行修复？(yes/no): ").strip().lower()

            if user_input == "yes":
                async with conn.transaction():
                    # 删除孤儿 topics
                    if len(orphan_topics) > 0:
                        orphan_ids = [t["id"] for t in orphan_topics]
                        await conn.execute("DELETE FROM topics WHERE id = ANY($1)", orphan_ids)
                        print(f"✅ 已删除 {len(orphan_topics)} 条孤儿 topics")

                    # 删除孤儿 feedbacks
                    if len(orphan_feedbacks) > 0:
                        orphan_ids = [f["id"] for f in orphan_feedbacks]
                        await conn.execute("DELETE FROM feedbacks WHERE id = ANY($1)", orphan_ids)
                        print(f"✅ 已删除 {len(orphan_feedbacks)} 条孤儿 feedbacks")

                    # 删除重复的 default-board (ctid=18,24)
                    print("\n尝试删除重复的 default-board...")
                    await conn.execute("DELETE FROM boards WHERE ctid = '(18,24)'::tid")
                    print("✅ 已删除 ctid=(18,24) 的 default-board")

                print("\n✅ 修复完成！")

                # 验证
                print("\n" + "=" * 80)
                print("【验证修复结果】")
                print("=" * 80)

                default_boards = await conn.fetch("SELECT ctid::text, name FROM boards WHERE id = 'default-board'")
                print(f"\n📊 current default-board 记录数: {len(default_boards)}\n")
                for board in default_boards:
                    print(f"  ctid: {board['ctid']}, name: {board['name']}")

                if len(default_boards) == 1:
                    print("\n✅ 成功！只有一条 default-board 记录了")
            else:
                print("❌ 取消修复")
        else:
            print("\n✅ 没有孤儿记录")

    finally:
        await conn.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback

        traceback.print_exc()
