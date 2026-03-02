"""检查当前反馈状态分布"""

import asyncio
from backend.database.db import async_db_session
from sqlalchemy import select, func
from backend.app.userecho.model.feedback import Feedback


async def check_status():
    async with async_db_session() as db:
        # 按状态统计
        status_query = (
            select(
                Feedback.clustering_status,
                func.count(Feedback.id),
            )
            .where(
                Feedback.tenant_id == "default-tenant",
                Feedback.deleted_at.is_(None),
                Feedback.topic_id.is_(None),
            )
            .group_by(Feedback.clustering_status)
        )

        result = await db.execute(status_query)
        rows = result.all()

        print("=== 反馈状态分布（topic_id IS NULL）===")
        total = 0
        for status, count in rows:
            print(f"  {status}: {count} 条")
            total += count

        print(f"\n总计: {total} 条")

        # 检查最近更新为 processing 的记录
        recent_processing = (
            select(
                Feedback.id,
                Feedback.clustering_status,
                Feedback.clustering_metadata,
                Feedback.updated_time,
            )
            .where(
                Feedback.tenant_id == "default-tenant",
                Feedback.deleted_at.is_(None),
                Feedback.topic_id.is_(None),
                Feedback.clustering_status == "processing",
            )
            .order_by(Feedback.updated_time.desc())
            .limit(5)
        )

        result2 = await db.execute(recent_processing)
        rows2 = result2.all()

        if rows2:
            print("\n=== 最近标记为 processing 的记录（前5条）===")
            for row in rows2:
                print(f"  ID: {row.id[:8]}...")
                print(f"  Status: {row.clustering_status}")
                print(f"  Metadata: {row.clustering_metadata}")
                print(f"  Updated: {row.updated_time}")
                print()


if __name__ == "__main__":
    asyncio.run(check_status())
