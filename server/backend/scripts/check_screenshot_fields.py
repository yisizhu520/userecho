"""
验证 feedbacks 表的截图字段是否正确添加
"""

import asyncio
import sys

from pathlib import Path

backend_path = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_path))

from sqlalchemy import text

from backend.database.db import async_engine


async def check_schema() -> bool | None:
    """检查表结构"""
    print("=" * 70)
    print("📊 检查 feedbacks 表结构")
    print("=" * 70)

    sql = """
    SELECT
        column_name,
        data_type,
        is_nullable,
        column_default,
        character_maximum_length
    FROM information_schema.columns
    WHERE table_name = 'feedbacks'
        AND column_name IN (
            'screenshot_url',
            'source_platform',
            'source_user_name',
            'source_user_id',
            'ai_confidence',
            'submitter_id'
        )
    ORDER BY column_name;
    """

    try:
        async with async_engine.connect() as conn:
            result = await conn.execute(text(sql))
            rows = result.fetchall()

            if not rows:
                print("❌ 字段不存在！")
                return False

            print("\n✅ 字段已存在：\n")
            print(f"{'字段名':<25} {'类型':<20} {'可空':<10} {'长度':<10}")
            print("-" * 70)

            for row in rows:
                col_name, data_type, is_null, _default, max_len = row
                print(f"{col_name:<25} {data_type:<20} {is_null:<10} {max_len!s:<10}")

            # 检查外键约束
            fk_sql = """
            SELECT
                tc.constraint_name,
                kcu.column_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage AS ccu
                ON ccu.constraint_name = tc.constraint_name
                AND ccu.table_schema = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY'
                AND tc.table_name = 'feedbacks'
                AND kcu.column_name = 'submitter_id';
            """

            result = await conn.execute(text(fk_sql))
            fk_rows = result.fetchall()

            print("\n✅ 外键约束：\n")
            if fk_rows:
                for row in fk_rows:
                    constraint_name, col, foreign_table, foreign_col = row
                    print(f"  {constraint_name}: {col} -> {foreign_table}({foreign_col})")
            else:
                print("  无外键约束")

        print("\n" + "=" * 70)
        print("✅ 字段检查完成！所有字段正确添加。")
        print("=" * 70)
        return True

    except Exception as e:
        print(f"❌ 检查失败: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(check_schema())
    sys.exit(0 if success else 1)
