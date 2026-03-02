"""检查聚类数据不一致问题"""

import asyncio
from backend.database.db import async_db_session
from sqlalchemy import select, func
from backend.app.userecho.model.feedback import Feedback


async def check_feedbacks():
    async with async_db_session() as db:
        # 1. 前端API的查询逻辑
        pending_query = select(func.count(Feedback.id)).where(
            Feedback.tenant_id == "default-tenant",
            Feedback.deleted_at.is_(None),
            Feedback.topic_id.is_(None),
            Feedback.clustering_status == "pending",
        )
        pending_count = await db.scalar(pending_query) or 0
        print(f"前端API查询（clustering_status='pending' AND topic_id IS NULL）: {pending_count} 条")

        # 2. Worker的查询逻辑（默认 board_id）
        worker_query = select(func.count(Feedback.id)).where(
            Feedback.tenant_id == "default-tenant",
            Feedback.deleted_at.is_(None),
            Feedback.topic_id.is_(None),
            Feedback.clustering_status.in_(["pending", "failed"]),
            Feedback.board_id == "default-board",  # Worker 有 board_id 过滤
        )
        worker_count = await db.scalar(worker_query) or 0
        print(
            f"Worker查询（clustering_status IN ('pending','failed') AND board_id='default-board'）: {worker_count} 条"
        )

        # 3. 检查所有 topic_id 为空的反馈分布
        all_null_query = (
            select(
                Feedback.board_id,
                Feedback.clustering_status,
                func.count(Feedback.id),
            )
            .where(
                Feedback.tenant_id == "default-tenant",
                Feedback.deleted_at.is_(None),
                Feedback.topic_id.is_(None),
            )
            .group_by(Feedback.board_id, Feedback.clustering_status)
        )

        result = await db.execute(all_null_query)
        rows = result.all()

        print("\n按 board_id 和 clustering_status 分组统计：")
        for board_id, status, count in rows:
            print(f"  board_id={board_id}, status={status}, count={count}")


if __name__ == "__main__":
    asyncio.run(check_feedbacks())
