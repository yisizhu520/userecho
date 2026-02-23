#!/usr/bin/env python3
"""
刷新 Board 统计数据

问题：Board 的 topic_count/feedback_count 显示为 0
原因：触发器仅在增删改时更新，历史数据需要手动修复

使用方式：
    cd server && source .venv/Scripts/activate
    python -m backend.scripts.refresh_board_stats
"""

import asyncio

from sqlalchemy import text

from backend.database.db import async_engine


async def refresh_board_stats() -> None:
    """刷新所有 Board 的统计数据"""
    async with async_engine.begin() as conn:
        # 先检查触发器是否存在
        trigger_check = await conn.execute(
            text("""
                SELECT tgname
                FROM pg_trigger
                WHERE tgname IN ('trigger_update_board_feedback_count', 'trigger_update_board_topic_count')
            """)
        )
        triggers = [row[0] for row in trigger_check.fetchall()]
        print(f'触发器状态: {triggers or "⚠️  未找到触发器！"}')

        # 1. 修复 Topic 的 board_id（从关联的 Feedback 推断）
        result0 = await conn.execute(
            text("""
                UPDATE topics
                SET board_id = (
                    SELECT board_id FROM feedbacks
                    WHERE feedbacks.topic_id = topics.id
                      AND feedbacks.board_id IS NOT NULL
                      AND feedbacks.deleted_at IS NULL
                    GROUP BY board_id
                    ORDER BY COUNT(*) DESC
                    LIMIT 1
                )
                WHERE board_id IS NULL AND deleted_at IS NULL
            """)
        )
        print(f'✅ 已修复 {result0.rowcount} 个 Topic 的 board_id')

        # 2. 更新 feedback_count
        result1 = await conn.execute(
            text("""
                UPDATE boards
                SET feedback_count = (
                    SELECT COUNT(*) FROM feedbacks
                    WHERE feedbacks.board_id = boards.id AND feedbacks.deleted_at IS NULL
                )
            """)
        )
        print(f'✅ 已更新 {result1.rowcount} 个 Board 的 feedback_count')

        # 3. 更新 topic_count
        result2 = await conn.execute(
            text("""
                UPDATE boards
                SET topic_count = (
                    SELECT COUNT(*) FROM topics
                    WHERE topics.board_id = boards.id AND topics.deleted_at IS NULL
                )
            """)
        )
        print(f'✅ 已更新 {result2.rowcount} 个 Board 的 topic_count')

        # 4. 验证结果
        boards = await conn.execute(
            text("""
                SELECT id, name, feedback_count, topic_count
                FROM boards
                WHERE deleted_at IS NULL
                ORDER BY name
            """)
        )
        print('\n📊 当前 Board 统计:')
        for row in boards.fetchall():
            print(f'   {row[1]}: feedback={row[2]}, topic={row[3]}')


if __name__ == '__main__':
    asyncio.run(refresh_board_stats())
