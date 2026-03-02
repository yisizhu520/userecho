"""直接测试 claim_pending_clustering 函数"""

import asyncio
from datetime import datetime
from backend.database.db import async_db_session
from backend.app.userecho.crud.crud_feedback import crud_feedback


async def test_claim():
    async with async_db_session.begin() as db:
        started_at = datetime.now()
        feedbacks = await crud_feedback.claim_pending_clustering(
            db=db,
            tenant_id="default-tenant",
            limit=100,
            include_failed=True,
            force_recluster=False,
            board_id="default-board",
            started_at=started_at,
        )
        print(f"领取到的反馈数量: {len(feedbacks)}")

        if feedbacks:
            print(f"第一条反馈: {feedbacks[0]}")
        else:
            print("没有领取到反馈！")


if __name__ == "__main__":
    asyncio.run(test_claim())
