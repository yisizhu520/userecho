#!/usr/bin/env python3
"""
初始化租户内置角色脚本

用法：
    python init_tenant_roles.py <tenant_id>
    python init_tenant_roles.py --all  # 为所有租户初始化
"""

import asyncio
import sys

from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.userecho.service.tenant_role_service import tenant_role_service
from backend.common.log import log
from backend.database.db import async_db_session, async_engine


async def init_roles_for_tenant(db: AsyncSession, tenant_id: str) -> None:
    """为指定租户初始化内置角色"""
    log.info(f'Initializing builtin roles for tenant: {tenant_id}')

    try:
        created_roles = await tenant_role_service.init_builtin_roles(db, tenant_id)
        await db.commit()

        if created_roles:
            log.info(f'Created {len(created_roles)} builtin roles for tenant {tenant_id}:')
            for role in created_roles:
                log.info(f'  - {role.name} ({role.code})')
        else:
            log.info(f'Builtin roles already exist for tenant {tenant_id}')
    except Exception as e:
        await db.rollback()
        log.error(f'Failed to initialize roles for tenant {tenant_id}: {e}')
        raise


async def init_all_tenants() -> None:
    """为所有租户初始化内置角色"""
    from sqlalchemy import select

    from backend.app.userecho.model.tenant import Tenant

    async with async_db_session() as db:
        # 获取所有活跃租户
        stmt = select(Tenant).where(Tenant.status == 'active')
        result = await db.execute(stmt)
        tenants = result.scalars().all()

        log.info(f'Found {len(tenants)} active tenants')

        for tenant in tenants:
            await init_roles_for_tenant(db, tenant.id)


async def main() -> None:
    """主函数"""
    if len(sys.argv) < 2:
        print('Usage: python init_tenant_roles.py <tenant_id>')
        print('       python init_tenant_roles.py --all')
        sys.exit(1)

    try:
        if sys.argv[1] == '--all':
            await init_all_tenants()
        else:
            tenant_id = sys.argv[1]
            async with async_db_session() as db:
                await init_roles_for_tenant(db, tenant_id)

        log.info('✅ Initialization completed successfully')
    except Exception as e:
        log.error(f'❌ Initialization failed: {e}')
        sys.exit(1)
    finally:
        await async_engine.dispose()


if __name__ == '__main__':
    asyncio.run(main())
