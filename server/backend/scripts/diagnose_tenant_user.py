#!/usr/bin/env python3
"""诊断 TenantUser 重复数据问题"""

import asyncio
import io
import sys

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, '.')

from sqlalchemy import select

from backend.app.admin.model import User
from backend.app.userecho.model import TenantUser
from backend.database.db import async_db_session


async def diagnose_tenant_user():
    """诊断 TenantUser 重复数据"""
    async with async_db_session() as db:
        print('=' * 80)
        print('🔍 诊断 TenantUser 数据')
        print('=' * 80)
        print()

        # 1. 查找 boss 用户
        boss = await db.scalar(select(User).where(User.username == 'boss'))
        if not boss:
            print('❌ boss 用户不存在')
            return

        print(f'✅ boss 用户: ID={boss.id}, tenant_id={boss.tenant_id!r}')
        print()

        # 2. 查找 boss 的所有 TenantUser 记录
        print('📋 boss 用户的 TenantUser 记录:')
        print('-' * 80)
        
        stmt = select(TenantUser).where(TenantUser.user_id == boss.id)
        result = await db.execute(stmt)
        tenant_users = result.scalars().all()

        if not tenant_users:
            print('❌ 没有 TenantUser 记录')
        else:
            for i, tu in enumerate(tenant_users, 1):
                print(f'{i}. tenant_id={tu.tenant_id!r}, user_type={tu.user_type}, status={tu.status}')
        
        print()

        # 3. 查找所有用户的重复 TenantUser 记录
        print('🔍 检查所有用户的 TenantUser 重复记录:')
        print('-' * 80)
        
        all_tenant_users = await db.scalars(select(TenantUser))
        user_tenant_map = {}
        
        for tu in all_tenant_users:
            key = (tu.user_id, tu.status)
            if key not in user_tenant_map:
                user_tenant_map[key] = []
            user_tenant_map[key].append(tu)
        
        duplicates_found = False
        for (user_id, status), records in user_tenant_map.items():
            if len(records) > 1:
                duplicates_found = True
                user = await db.scalar(select(User).where(User.id == user_id))
                username = user.username if user else f'Unknown(ID={user_id})'
                print(f'⚠️  用户 {username} (status={status}) 有 {len(records)} 条记录:')
                for record in records:
                    print(f'   - tenant_id={record.tenant_id!r}, user_type={record.user_type}')
        
        if not duplicates_found:
            print('✅ 没有发现重复记录')
        
        print()


if __name__ == '__main__':
    asyncio.run(diagnose_tenant_user())
