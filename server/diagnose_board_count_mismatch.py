"""诊断看板计数和反馈列表数据不一致的问题

问题描述：
- 左侧栏看板筛选显示的数字（board.feedback_count）
- 反馈列表筛选后显示的数据条数
- 两者对不上

可能原因分析：
1. 触发器计数：只统计 deleted_at IS NULL 的反馈
2. 反馈列表：除了 deleted_at IS NULL，还有其他筛选条件（紧急程度、派生状态等）

解决方案：
- 检查是否是筛选条件导致的不一致
- 确认触发器统计逻辑是否符合业务需求
"""

import asyncio

from sqlalchemy import func, select, text


async def diagnose_board_count():
    """诊断看板计数"""
    from backend.database.db import async_db_session

    async with async_db_session.begin() as db:
        # 使用原生 SQL 查询，避免模型循环依赖
        boards_query = text("""
            SELECT id, name, feedback_count
            FROM boards
            WHERE tenant_id = 'default-tenant' AND deleted_at IS NULL
        """)

        boards_result = await db.execute(boards_query)
        boards = boards_result.fetchall()

        print("=" * 80)
        print("看板反馈计数诊断报告")
        print("=" * 80)
        print()

        for board_id, board_name, feedback_count in boards:
            print(f"看板: {board_name} (ID: {board_id})")
            print(f"   触发器统计: {feedback_count} 条")
            print()

            # 实际统计（只统计未删除的）
            actual_count_query = text("""
                SELECT COUNT(*) FROM feedbacks
                WHERE board_id = :board_id AND deleted_at IS NULL
            """)
            actual_result = await db.execute(actual_count_query, {"board_id": board_id})
            actual_count = actual_result.scalar() or 0

            print(f"   实际统计（未删除）: {actual_count} 条")

            if feedback_count != actual_count:
                print(f"   警告: 触发器计数与实际不符！差异: {feedback_count - actual_count}")
            else:
                print(f"   OK: 触发器计数正确")

            # 详细分析：按不同维度统计
            print()
            print("   详细分析：")

            # 1. 按紧急程度统计
            urgent_query = text("""
                SELECT
                    SUM(CASE WHEN is_urgent = TRUE THEN 1 ELSE 0 END) as urgent_count,
                    SUM(CASE WHEN is_urgent = FALSE THEN 1 ELSE 0 END) as normal_count
                FROM feedbacks
                WHERE board_id = :board_id AND deleted_at IS NULL
            """)
            urgent_result = await db.execute(urgent_query, {"board_id": board_id})
            urgent_row = urgent_result.fetchone()
            urgent_true_count = urgent_row[0] or 0
            urgent_false_count = urgent_row[1] or 0

            print(f"      - 紧急: {urgent_true_count} 条")
            print(f"      - 常规: {urgent_false_count} 条")

            # 2. 按派生状态统计
            status_query = text("""
                SELECT
                    SUM(CASE WHEN topic_id IS NULL THEN 1 ELSE 0 END) as pending_count,
                    SUM(CASE WHEN topic_id IS NOT NULL THEN 1 ELSE 0 END) as linked_count
                FROM feedbacks
                WHERE board_id = :board_id AND deleted_at IS NULL
            """)
            status_result = await db.execute(status_query, {"board_id": board_id})
            status_row = status_result.fetchone()
            pending_count = status_row[0] or 0
            linked_count = status_row[1] or 0

            print(f"      - 待处理（未关联主题）: {pending_count} 条")
            print(f"      - 已关联主题: {linked_count} 条")

            print()
            print("-" * 80)
            print()

        print()
        print("诊断完成！")
        print()
        print("总结：")
        print("1. board.feedback_count 统计的是：该看板下所有未删除的反馈")
        print("2. 前端反馈列表可能有额外筛选条件：")
        print("   - 紧急程度（紧急/常规）")
        print("   - 派生状态（待处理/已关联等）")
        print("   - 日期范围")
        print("3. 如果左侧栏数字和列表数据对不上，可能是因为：")
        print("   - 前端默认应用了某些筛选条件")
        print("   - 用户手动选择了筛选条件")
        print()


if __name__ == "__main__":
    asyncio.run(diagnose_board_count())
