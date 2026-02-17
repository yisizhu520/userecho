#!/usr/bin/env python3
"""模拟 Board API 调用，打印详细的调试信息"""

import asyncio
import io
import sys

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, '.')

from sqlalchemy import select

from backend.app.admin.model import User
from backend.app.userecho.model import Board
from backend.database.db import async_db_session


async def debug_board_api() -> None:
    """调试 Board API"""
    async with async_db_session() as db:
        print('=' * 80)
        print('🔍 调试 Board API')
        print('=' * 80)
        print()

        # 1. 获取 boss 用户
        boss = await db.scalar(select(User).where(User.username == 'boss'))
        if not boss:
            print('❌ boss 用户不存在')
            return

        print('1️⃣ boss 用户信息:')
        print(f'   ID: {boss.id}')
        print(f'   username: {boss.username}')
        print(f'   User.tenant_id: {boss.tenant_id!r}')
        print()

        # 2. 模拟 JWT 中间件的逻辑
        tenant_id = boss.tenant_id or 'default-tenant'
        print('2️⃣ JWT 中间件会使用的 tenant_id:')
        print(f'   tenant_id = {tenant_id!r}')
        print()

        # 3. 查询所有看板（不加过滤）
        print('3️⃣ 数据库中的所有看板:')
        all_boards = await db.scalars(select(Board))
        all_board_list = list(all_boards)
        if all_board_list:
            for board in all_board_list:
                print(f'   - {board.name}')
                print(f'     ID: {board.id}')
                print(f'     tenant_id: {board.tenant_id!r}')
                print(f'     is_archived: {board.is_archived}')
                print()
        else:
            print('   ❌ 没有看板')
        print()

        # 4. 模拟 API 查询
        print(f'4️⃣ 模拟 API 查询（tenant_id={tenant_id!r}, is_archived=False）:')
        stmt = (
            select(Board)
            .where(Board.tenant_id == tenant_id)
            .where(not Board.is_archived)
            .order_by(Board.sort_order, Board.created_time.desc())
        )
        result = await db.execute(stmt)
        boards = result.scalars().all()

        print(f'   查询结果: {len(boards)} 个看板')
        if boards:
            for board in boards:
                print(f'   - {board.name} (ID: {board.id})')
        else:
            print('   ❌ 查询结果为空')
        print()

        # 5. 检查是否有 tenant_id 不匹配的情况
        print('5️⃣ 诊断:')
        if not boards and all_board_list:
            print('   ⚠️  数据库有看板，但查询结果为空')
            print('   可能原因:')
            print(f'   - boss.tenant_id ({boss.tenant_id!r}) 与看板的 tenant_id 不匹配')
            print('   - 或者所有看板都被归档了')

            # 检查每个看板
            for board in all_board_list:
                if board.tenant_id != tenant_id:
                    print(f'   ❌ 看板 "{board.name}" 的 tenant_id ({board.tenant_id!r}) != {tenant_id!r}')
                if board.is_archived:
                    print(f'   ⚠️  看板 "{board.name}" 已归档')
        elif boards:
            print('   ✅ 查询正常，找到看板')
        else:
            print('   ℹ️  数据库中没有看板')


if __name__ == '__main__':
    asyncio.run(debug_board_api())
