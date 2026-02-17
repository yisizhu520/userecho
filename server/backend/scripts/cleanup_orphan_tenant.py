#!/usr/bin/env python3
"""清理孤立的 userecho 租户"""

import asyncio
import io
import sys

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, '.')

from sqlalchemy import delete, select

from backend.app.userecho.model import Board, Tenant
from backend.database.db import async_db_session


async def cleanup_orphan_tenant() -> None:
    """清理孤立的 userecho 租户"""
    async with async_db_session.begin() as db:
        print('=' * 80)
        print('🧹 清理孤立的 userecho 租户')
        print('=' * 80)
        print()

        tenant_id = '79a2fd29-36f0-4d94-9999-e35ad6e66031'

        # 1. 检查该租户下是否还有看板
        boards = await db.scalars(select(Board).where(Board.tenant_id == tenant_id))
        board_list = list(boards)

        if board_list:
            print(f'⚠️  警告：租户 {tenant_id} 下还有 {len(board_list)} 个看板')
            print('   无法删除，请先迁移或删除这些看板')
            for board in board_list:
                print(f'   - {board.name} (ID: {board.id})')
            return

        # 2. 删除租户
        result = await db.execute(delete(Tenant).where(Tenant.id == tenant_id))

        if result.rowcount > 0:
            print(f'✅ 成功删除租户: {tenant_id}')
        else:
            print(f'ℹ️  租户不存在或已被删除: {tenant_id}')

        await db.commit()
        print()
        print('✅ 清理完成！')
        print()


if __name__ == '__main__':
    asyncio.run(cleanup_orphan_tenant())
