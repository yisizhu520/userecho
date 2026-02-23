#!/usr/bin/env python3
"""将 web端反馈 看板移动到 default-tenant"""

import asyncio
import io
import sys

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

sys.path.insert(0, ".")

from sqlalchemy import update

from backend.app.userecho.model import Board
from backend.database.db import async_db_session


async def move_board_to_default_tenant() -> None:
    """将 web端反馈 看板移动到 default-tenant"""
    async with async_db_session.begin() as db:
        print("=" * 80)
        print("🔧 将 web端反馈 看板移动到 default-tenant")
        print("=" * 80)
        print()

        # 更新看板的 tenant_id
        result = await db.execute(
            update(Board).where(Board.id == "983bd86b-743e-4f3e-969b-7dcf20fa55c3").values(tenant_id="default-tenant")
        )

        if result.rowcount > 0:
            print("✅ 成功将 web端反馈 看板移动到 default-tenant")
        else:
            print("❌ 看板不存在或已经在 default-tenant 下")

        await db.commit()
        print()
        print("✅ 操作完成！")
        print()


if __name__ == "__main__":
    asyncio.run(move_board_to_default_tenant())
