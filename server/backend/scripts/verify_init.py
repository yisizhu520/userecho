#!/usr/bin/env python3
"""验证租户权限和角色初始化结果"""

import asyncio
import sys

from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import func, select

from backend.app.userecho.model.tenant_permission import TenantPermission
from backend.app.userecho.model.tenant_role import TenantRole
from backend.database.db import async_db_session


async def verify() -> None:
    async with async_db_session() as db:
        # 统计权限点
        perm_count = await db.scalar(select(func.count()).select_from(TenantPermission))
        print(f'✅ 租户权限点数量: {perm_count}')

        # 统计角色
        role_count = await db.scalar(select(func.count()).select_from(TenantRole))
        print(f'✅ 租户角色数量: {role_count}')

        # 列出所有权限
        stmt = select(TenantPermission).order_by(TenantPermission.sort)
        result = await db.execute(stmt)
        permissions = result.scalars().all()

        print('\n📋 权限点列表:')
        for perm in permissions:
            parent_info = f' (父级: {perm.parent_id[:8]}...)' if perm.parent_id else ''
            print(f'   - {perm.code}: {perm.name}{parent_info}')

        # 列出所有角色
        stmt = select(TenantRole).order_by(TenantRole.sort)
        result = await db.execute(stmt)
        roles = result.scalars().all()

        print('\n👥 角色列表:')
        for role in roles:
            print(f'   - {role.code}: {role.name} (内置: {role.is_builtin})')


if __name__ == '__main__':
    asyncio.run(verify())
