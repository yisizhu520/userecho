"""检查看板排序情况"""

import asyncio
import sys
from pathlib import Path

# 添加 backend 到 sys.path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from sqlalchemy import select
from backend.app.userecho.model.board import Board
from backend.database.db import async_db_session


async def check_board_order():
    """检查看板的 sort_order 和实际排序"""
    async with async_db_session() as db:
        # 查询所有看板，按实际 API 的排序逻辑
        stmt = (
            select(Board)
            .where(Board.is_archived == False)  # noqa: E712
            .where(Board.deleted_at.is_(None))
            .order_by(Board.sort_order, Board.created_time.desc())
        )
        result = await db.execute(stmt)
        boards = result.scalars().all()

        print("\n========== 当前看板排序情况 ==========")
        print(f"{'序号':<4} {'ID':<38} {'名称':<20} {'sort_order':<12} {'创建时间':<20}")
        print("-" * 100)

        for idx, board in enumerate(boards, 1):
            print(
                f"{idx:<4} {board.id:<38} {board.name:<20} "
                f"{board.sort_order:<12} {board.created_time.strftime('%Y-%m-%d %H:%M:%S'):<20}"
            )

        print("\n========== 排序规则 ==========")
        print("1. 优先按 sort_order 升序（数值小的在前）")
        print("2. sort_order 相同时，按创建时间降序（新的在前）")

        # 检查是否所有 sort_order 都相同
        sort_orders = [board.sort_order for board in boards]
        if len(set(sort_orders)) == 1:
            print(f"\n⚠️  警告：所有看板的 sort_order 都是 {sort_orders[0]}，完全按创建时间排序")
        else:
            print("\n✅ 看板的 sort_order 有差异，排序生效")


if __name__ == "__main__":
    asyncio.run(check_board_order())
