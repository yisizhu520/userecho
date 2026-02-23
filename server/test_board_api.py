#!/usr/bin/env python3
"""测试 Board API"""

import asyncio
import sys

sys.path.insert(0, ".")

from sqlalchemy import select

from backend.app.userecho.model.board import Board
from backend.database.db import async_db_session


async def test_board_api() -> None:
    """测试 Board API"""
    async with async_db_session() as db:
        # 查询所有 Board
        stmt = select(Board).where(not Board.is_archived)
        result = await db.execute(stmt)
        boards = result.scalars().all()

        print(f"找到 {len(boards)} 个看板:")
        for board in boards:
            print(f"  - ID: {board.id}")
            print(f"    名称: {board.name}")
            print(f"    URL: {board.url_name}")
            print(f"    租户: {board.tenant_id}")
            print(f"    反馈数: {board.feedback_count}")
            print()


if __name__ == "__main__":
    asyncio.run(test_board_api())
