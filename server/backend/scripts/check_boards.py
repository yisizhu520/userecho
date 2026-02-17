#!/usr/bin/env python3
"""检查 Board 数据"""

import asyncio
import io
import sys

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, '.')

from sqlalchemy import select

from backend.app.userecho.model import Board
from backend.database.db import async_db_session


async def check_boards():
    """检查 Board 数据"""
    async with async_db_session() as db:
        print('=' * 80)
        print('🔍 检查 Board 数据')
        print('=' * 80)
        print()

        # 查询所有看板
        boards = await db.scalars(select(Board))
        board_list = list(boards)

        print(f'总共 {len(board_list)} 个看板:')
        print('-' * 80)
        
        for board in board_list:
            print(f'ID: {board.id}')
            print(f'  名称: {board.name}')
            print(f'  tenant_id: {board.tenant_id}')
            print(f'  is_archived: {board.is_archived}')
            print()

        # 按租户分组
        print('=' * 80)
        print('按租户分组:')
        print('=' * 80)
        
        tenant_boards = {}
        for board in board_list:
            if board.tenant_id not in tenant_boards:
                tenant_boards[board.tenant_id] = []
            tenant_boards[board.tenant_id].append(board)
        
        for tenant_id, boards in tenant_boards.items():
            active_boards = [b for b in boards if not b.is_archived]
            print(f'\n租户: {tenant_id}')
            print(f'  总看板数: {len(boards)}')
            print(f'  活跃看板数: {len(active_boards)}')
            if len(active_boards) > 1:
                print(f'  ⚠️  警告: 有 {len(active_boards)} 个活跃看板，可能导致查询错误')
                for board in active_boards:
                    print(f'    - {board.name} (ID: {board.id})')


if __name__ == '__main__':
    asyncio.run(check_boards())
