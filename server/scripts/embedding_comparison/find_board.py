"""查找默认 board"""

import asyncio
from sqlalchemy import select
from backend.app.userecho.model.board import Board
from backend.database.db import async_db_session


async def main():
    async with async_db_session.begin() as db:
        result = await db.execute(select(Board).where(Board.tenant_id == "default-tenant"))
        boards = result.scalars().all()

        if boards:
            print(f"找到 {len(boards)} 个 board:")
            for board in boards:
                print(f"  - {board.id}: {board.name}")
        else:
            print("没有找到 board")


if __name__ == "__main__":
    asyncio.run(main())
