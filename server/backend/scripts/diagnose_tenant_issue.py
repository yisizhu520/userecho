#!/usr/bin/env python3
"""诊断租户数据问题"""

import asyncio
import io
import sys

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, '.')

from sqlalchemy import select

from backend.app.admin.model import User
from backend.app.userecho.model import Board, Tenant, TenantUser
from backend.database.db import async_db_session


async def diagnose() -> None:
    """诊断租户数据"""
    async with async_db_session() as db:
        print('=' * 80)
        print('🔍 租户数据诊断')
        print('=' * 80)
        print()

        # 1. 检查 boss 用户
        print('1️⃣ 检查 boss 用户')
        print('-' * 80)
        boss = await db.scalar(select(User).where(User.username == 'boss'))
        if boss:
            print('   ✅ boss 用户存在')
            print(f'   User ID: {boss.id}')
            print(f'   User.tenant_id: {boss.tenant_id!r}')
        else:
            print('   ❌ boss 用户不存在')
        print()

        # 2. 检查 TenantUser 关联
        print('2️⃣ 检查 TenantUser 关联')
        print('-' * 80)
        if boss:
            tenant_user = await db.scalar(select(TenantUser).where(TenantUser.user_id == boss.id))
            if tenant_user:
                print('   ✅ TenantUser 关联存在')
                print(f'   TenantUser.tenant_id: {tenant_user.tenant_id!r}')
                print(f'   TenantUser.user_type: {tenant_user.user_type}')
            else:
                print('   ❌ TenantUser 关联不存在')
        print()

        # 3. 检查 Tenant 表
        print('3️⃣ 检查 Tenant 表')
        print('-' * 80)
        tenants = await db.scalars(select(Tenant))
        tenant_list = list(tenants)
        if tenant_list:
            for tenant in tenant_list:
                print(f'   ✅ Tenant: {tenant.id!r} - {tenant.name}')
        else:
            print('   ❌ 没有租户数据')
        print()

        # 4. 检查 Board 表
        print('4️⃣ 检查 Board 表')
        print('-' * 80)
        boards = await db.scalars(select(Board))
        board_list = list(boards)
        if board_list:
            for board in board_list:
                print(f'   ✅ Board: {board.id!r}')
                print(f'      名称: {board.name}')
                print(f'      tenant_id: {board.tenant_id!r}')
                print(f'      is_archived: {board.is_archived}')
        else:
            print('   ❌ 没有看板数据')
        print()

        # 5. 模拟 API 查询
        print('5️⃣ 模拟 API 查询（使用 boss 的 tenant_id）')
        print('-' * 80)
        if boss:
            tenant_id = boss.tenant_id or 'default-tenant'
            print(f'   查询条件: tenant_id={tenant_id!r}, is_archived=False')

            stmt = (
                select(Board)
                .where(Board.tenant_id == tenant_id)
                .where(not Board.is_archived)
                .order_by(Board.sort_order, Board.created_time.desc())
            )
            result = await db.execute(stmt)
            api_boards = result.scalars().all()

            if api_boards:
                print(f'   ✅ 查询到 {len(api_boards)} 个看板:')
                for board in api_boards:
                    print(f'      - {board.name} (ID: {board.id})')
            else:
                print('   ❌ 查询结果为空')
        print()

        # 6. 诊断结论
        print('=' * 80)
        print('📋 诊断结论')
        print('=' * 80)

        if boss and board_list:
            boss_tenant = boss.tenant_id or 'default-tenant'
            board_tenants = {b.tenant_id for b in board_list}

            if boss_tenant in board_tenants:
                print('✅ 数据正常：boss 的 tenant_id 与看板的 tenant_id 匹配')
            else:
                print('❌ 数据不一致：')
                print(f'   boss.tenant_id = {boss_tenant!r}')
                print(f'   board.tenant_id = {board_tenants}')
                print()
                print('💡 解决方案：')
                print('   1. 更新 boss 用户的 tenant_id 为 "default-tenant"')
                print('   2. 或者更新看板的 tenant_id 为 boss 的 tenant_id')
        print()


if __name__ == '__main__':
    asyncio.run(diagnose())
