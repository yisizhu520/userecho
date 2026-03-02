"""检查租户数据

查找有反馈数据的租户
"""

import asyncio
from sqlalchemy import func, select

from backend.app.userecho.model.feedback import Feedback
from backend.database.db import async_db_session


async def check_tenants():
    """检查租户数据"""
    async with async_db_session.begin() as db:
        # 统计每个租户的反馈数量
        query = (
            select(Feedback.tenant_id, func.count(Feedback.id).label("count"))
            .where(Feedback.deleted_at.is_(None))
            .group_by(Feedback.tenant_id)
            .order_by(func.count(Feedback.id).desc())
        )

        result = await db.execute(query)
        tenants = result.all()

        if not tenants:
            print("❌ 没有找到任何反馈数据")
            return

        print(f"\n找到 {len(tenants)} 个租户:\n")
        for tenant_id, count in tenants:
            print(f"  租户: {tenant_id}")
            print(f"  反馈数: {count}")
            print()


if __name__ == "__main__":
    asyncio.run(check_tenants())
