#!/usr/bin/env python3
"""测试不同的查询条件"""

import asyncio
import io
import sys

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, '.')

from sqlalchemy import select

from backend.app.userecho.model import Board
from backend.database.db import async_db_session


async def test_queries() -> None:
    """测试不同的查询条件"""
    async with async_db_session() as db:
        print('=' * 80)
        print('🧪 测试不同的查询条件')
        print('=' * 80)
        print()

        tenant_id = 'default-tenant'

        # 1. 查询所有看板（无过滤）
        print('1️⃣ 查询所有看板（无过滤）:')
        stmt1 = select(Board)
        result1 = await db.execute(stmt1)
        boards1 = result1.scalars().all()
        print(f'   结果: {len(boards1)} 个看板')
        for b in boards1:
            print(f'   - {b.name}: tenant_id={b.tenant_id!r}, is_archived={b.is_archived}')
        print()

        # 2. 只过滤 tenant_id
        print(f'2️⃣ 只过滤 tenant_id={tenant_id!r}:')
        stmt2 = select(Board).where(Board.tenant_id == tenant_id)
        result2 = await db.execute(stmt2)
        boards2 = result2.scalars().all()
        print(f'   结果: {len(boards2)} 个看板')
        for b in boards2:
            print(f'   - {b.name}: is_archived={b.is_archived}')
        print()

        # 3. 使用 not Board.is_archived（API 当前的写法）
        print(f'3️⃣ tenant_id={tenant_id!r} AND not Board.is_archived:')
        stmt3 = select(Board).where(Board.tenant_id == tenant_id).where(not Board.is_archived)
        result3 = await db.execute(stmt3)
        boards3 = result3.scalars().all()
        print(f'   结果: {len(boards3)} 个看板')
        for b in boards3:
            print(f'   - {b.name}')
        print()

        # 4. 使用 Board.is_archived == False（推荐写法）
        print(f'4️⃣ tenant_id={tenant_id!r} AND Board.is_archived == False:')
        stmt4 = (
            select(Board).where(Board.tenant_id == tenant_id).where(Board.is_archived == False)  # noqa: E712
        )
        result4 = await db.execute(stmt4)
        boards4 = result4.scalars().all()
        print(f'   结果: {len(boards4)} 个看板')
        for b in boards4:
            print(f'   - {b.name}')
        print()

        # 5. 使用 ~Board.is_archived（位运算符）
        print(f'5️⃣ tenant_id={tenant_id!r} AND ~Board.is_archived:')
        stmt5 = select(Board).where(Board.tenant_id == tenant_id).where(~Board.is_archived)
        result5 = await db.execute(stmt5)
        boards5 = result5.scalars().all()
        print(f'   结果: {len(boards5)} 个看板')
        for b in boards5:
            print(f'   - {b.name}')
        print()

        # 诊断
        print('=' * 80)
        print('📊 诊断结果:')
        print('=' * 80)
        if len(boards3) == 0 and len(boards4) > 0:
            print('❌ 问题确认: `not Board.is_archived` 语法有问题')
            print('✅ 解决方案: 改用 `Board.is_archived == False`')
        elif len(boards2) == 0:
            print('❌ 问题: tenant_id 过滤有问题')
        else:
            print('✅ 查询正常')


if __name__ == '__main__':
    asyncio.run(test_queries())
