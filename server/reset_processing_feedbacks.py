"""重置 processing 状态的记录回 pending"""
import asyncio
from backend.database.db import async_db_session
from sqlalchemy import update
from backend.app.userecho.model.feedback import Feedback


async def reset_processing_to_pending():
    async with async_db_session.begin() as db:
        # 将所有 processing 状态的记录重置为 pending
        stmt = (
            update(Feedback)
            .where(
                Feedback.tenant_id == "default-tenant",
                Feedback.deleted_at.is_(None),
                Feedback.topic_id.is_(None),
                Feedback.clustering_status == "processing",
            )
            .values(
                clustering_status="pending",
                clustering_metadata=None,
            )
        )
        
        result = await db.execute(stmt)
        count = result.rowcount
        
        print(f"✅ 成功重置 {count} 条记录从 processing 到 pending")


if __name__ == "__main__":
    asyncio.run(reset_processing_to_pending())
