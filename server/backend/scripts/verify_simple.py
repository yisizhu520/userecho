#!/usr/bin/env python3
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, func
from backend.database.db import async_db_session
from backend.app.userecho.model.tenant_permission import TenantPermission
from backend.app.userecho.model.tenant_role import TenantRole


async def verify():
    async with async_db_session() as db:
        perm_count = await db.scalar(select(func.count()).select_from(TenantPermission))
        role_count = await db.scalar(select(func.count()).select_from(TenantRole))
        
        print('Tenant Permissions:', perm_count)
        print('Tenant Roles:', role_count)
        
        stmt = select(TenantPermission.code, TenantPermission.name).order_by(TenantPermission.sort)
        result = await db.execute(stmt)
        print('\nPermissions:')
        for code, name in result:
            print(f'  {code}: {name}')
        
        stmt = select(TenantRole.code, TenantRole.name).order_by(TenantRole.sort)
        result = await db.execute(stmt)
        print('\nRoles:')
        for code, name in result:
            print(f'  {code}: {name}')


if __name__ == '__main__':
    asyncio.run(verify())
