"""调试 claim_pending_clustering 的 SQL 查询"""

import asyncio
from sqlalchemy import select
from backend.database.db import async_db_session
from backend.app.userecho.model.feedback import Feedback


async def test_claim_debug():
    async with async_db_session.begin() as db:
        # 1. 模拟 claim_pending_clustering 的查询逻辑
        statuses = ["pending", "failed"]

        # 原始查询（不带 FOR UPDATE）
        query = (
            select(Feedback)
            .where(
                Feedback.tenant_id == "default-tenant",
                Feedback.topic_id.is_(None),
                Feedback.clustering_status.in_(statuses),
                Feedback.deleted_at.is_(None),
                Feedback.board_id == "default-board",
            )
            .order_by(Feedback.updated_time.asc())
            .limit(100)
        )

        result = await db.execute(query)
        feedbacks = list(result.scalars().all())

        print(f"不带 FOR UPDATE 的查询结果: {len(feedbacks)} 条")

        # 2. 带 FOR UPDATE SKIP LOCKED 的查询
        query_locked = (
            select(Feedback)
            .where(
                Feedback.tenant_id == "default-tenant",
                Feedback.topic_id.is_(None),
                Feedback.clustering_status.in_(statuses),
                Feedback.deleted_at.is_(None),
                Feedback.board_id == "default-board",
            )
            .order_by(Feedback.updated_time.asc())
            .limit(100)
            .with_for_update(skip_locked=True)
        )

        result_locked = await db.execute(query_locked)
        feedbacks_locked = list(result_locked.scalars().all())

        print(f"带 FOR UPDATE SKIP LOCKED 的查询结果: {len(feedbacks_locked)} 条")

        if len(feedbacks) > 0 and len(feedbacks_locked) == 0:
            print("\n⚠️ 问题：不带锁能查到数据，带锁查不到！")
            print("可能原因：这些记录已经被其他事务锁定了")

            # 检查第一条记录的状态
            first = feedbacks[0]
            print("\n第一条记录详情：")
            print(f"  id: {first.id}")
            print(f"  clustering_status: {first.clustering_status}")
            print(f"  topic_id: {first.topic_id}")
            print(f"  updated_time: {first.updated_time}")


if __name__ == "__main__":
    asyncio.run(test_claim_debug())
