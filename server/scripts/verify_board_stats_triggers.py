"""
验证 Board 统计触发器是否正常工作
"""

import asyncio
import sys

from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text

from backend.database.db import async_engine


async def verify_triggers() -> None:
    """验证触发器"""

    print('🔍 验证 Board 统计触发器...\n')

    async with async_engine.begin() as conn:
        # 1. 检查触发器是否存在
        print('[1/3] 检查触发器是否存在...')
        result = await conn.execute(
            text("""
            SELECT
                trigger_name,
                event_object_table,
                action_statement
            FROM information_schema.triggers
            WHERE trigger_name IN (
                'trigger_update_board_feedback_count',
                'trigger_update_board_topic_count'
            )
            ORDER BY trigger_name;
        """)
        )

        triggers = result.fetchall()
        if triggers:
            print(f'    ✅ 找到 {len(triggers)} 个触发器:')
            for trigger in triggers:
                print(f'       - {trigger.trigger_name} on {trigger.event_object_table}')
        else:
            print('    ❌ 未找到触发器')
            return

        # 2. 检查触发器函数是否存在
        print('\n[2/3] 检查触发器函数是否存在...')
        result = await conn.execute(
            text("""
            SELECT
                routine_name,
                routine_type
            FROM information_schema.routines
            WHERE routine_name IN (
                'update_board_feedback_count',
                'update_board_topic_count'
            )
            ORDER BY routine_name;
        """)
        )

        functions = result.fetchall()
        if functions:
            print(f'    ✅ 找到 {len(functions)} 个触发器函数:')
            for func in functions:
                print(f'       - {func.routine_name} ({func.routine_type})')
        else:
            print('    ❌ 未找到触发器函数')
            return

        # 3. 查看当前 Board 统计数据
        print('\n[3/3] 查看当前 Board 统计数据...')
        result = await conn.execute(
            text("""
            SELECT
                b.id,
                b.name,
                b.feedback_count,
                b.topic_count,
                (SELECT COUNT(*) FROM feedbacks WHERE board_id = b.id AND deleted_at IS NULL) as actual_feedback_count,
                (SELECT COUNT(*) FROM topics WHERE board_id = b.id AND deleted_at IS NULL) as actual_topic_count
            FROM boards b
            WHERE b.is_archived = false
            ORDER BY b.created_time;
        """)
        )

        boards = result.fetchall()
        if boards:
            print(f'    📊 Board 统计数据 ({len(boards)} 个看板):')
            print(f'    {"看板名称":<20} {"统计反馈数":<12} {"实际反馈数":<12} {"统计主题数":<12} {"实际主题数":<12}')
            print(f'    {"-" * 20} {"-" * 12} {"-" * 12} {"-" * 12} {"-" * 12}')

            all_match = True
            for board in boards:
                feedback_match = '✅' if board.feedback_count == board.actual_feedback_count else '❌'
                topic_match = '✅' if board.topic_count == board.actual_topic_count else '❌'

                print(
                    f'    {board.name:<20} {board.feedback_count:<12} {board.actual_feedback_count:<12} {board.topic_count:<12} {board.actual_topic_count:<12}'
                )

                if board.feedback_count != board.actual_feedback_count or board.topic_count != board.actual_topic_count:
                    all_match = False
                    print(f'       ⚠️  数据不匹配: feedback {feedback_match}, topic {topic_match}')

            if all_match:
                print('\n    ✅ 所有 Board 的统计数据都正确！')
            else:
                print('\n    ⚠️  部分 Board 的统计数据不匹配')
        else:
            print('    📊 暂无看板数据')

    print('\n🎉 验证完成！')


if __name__ == '__main__':
    asyncio.run(verify_triggers())
