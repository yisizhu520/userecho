#!/usr/bin/env python3
"""
初始化业务菜单权限数据

用法：
    python init_business_permissions.py

功能说明：
    业务菜单 (/app/*) 权限由租户角色控制
    此脚本初始化所有业务功能对应的权限点
"""

import asyncio
import sys

from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.userecho.model.tenant_permission import TenantPermission
from backend.common.log import log
from backend.database.db import async_db_session, async_engine, uuid4_str
from backend.utils.timezone import timezone

# 业务权限定义（与前端菜单对应）
BUSINESS_PERMISSIONS = [
    # 工作台（所有人可见，不需要权限控制）
    # 反馈管理
    {
        'code': 'feedback',  # 对应前端 permissionCode: 'feedback'
        'name': '反馈管理',
        'type': 'module',
        'menu_path': '/app/feedback',
        'menu_icon': 'lucide:inbox',
        'sort': 10,
    },
    # AI 发现
    {
        'code': 'discovery',  # 对应前端 permissionCode: 'discovery'
        'name': 'AI 发现',
        'type': 'module',
        'menu_path': '/app/ai/discovery',
        'menu_icon': 'lucide:sparkles',
        'sort': 20,
    },
    # 需求管理
    {
        'code': 'topic',  # 对应前端 permissionCode: 'topic'
        'name': '需求管理',
        'type': 'module',
        'menu_path': '/app/topic/list',
        'menu_icon': 'lucide:lightbulb',
        'sort': 30,
    },
    # 客户管理
    {
        'code': 'customer',  # 对应前端 permissionCode: 'customer'
        'name': '客户管理',
        'type': 'module',
        'menu_path': '/app/customer',
        'menu_icon': 'lucide:users',
        'sort': 40,
    },
    # 洞察报告
    {
        'code': 'insight',  # 对应前端 permissionCode: 'insight'
        'name': '洞察报告',
        'type': 'module',
        'menu_path': '/app/insights/report',
        'menu_icon': 'lucide:file-bar-chart',
        'sort': 50,
    },
    # 系统设置（父级）
    {
        'code': 'settings',  # 对应前端 permissionCode: 'settings'
        'name': '系统设置',
        'type': 'module',
        'menu_path': '/app/settings',
        'menu_icon': 'lucide:settings',
        'sort': 90,
    },
    # 成员管理（设置子菜单）
    {
        'code': 'member',  # 对应前端 permissionCode: 'member'
        'name': '成员管理',
        'type': 'action',
        'parent_code': 'settings',
        'menu_path': '/app/settings/members',
        'menu_icon': 'lucide:users',
        'sort': 91,
    },
    # 角色管理（设置子菜单）
    {
        'code': 'role',  # 对应前端 permissionCode: 'role'
        'name': '角色管理',
        'type': 'action',
        'parent_code': 'settings',
        'menu_path': '/app/settings/roles',
        'menu_icon': 'lucide:shield',
        'sort': 92,
    },
]


async def init_permissions(db: AsyncSession) -> None:
    """初始化业务权限数据"""
    log.info('Starting business permissions initialization...')

    # 获取现有权限
    stmt = select(TenantPermission)
    result = await db.execute(stmt)
    existing_permissions = {p.code: p for p in result.scalars().all()}

    # 用于存储新创建的权限 ID
    permission_ids: dict[str, str] = {code: p.id for code, p in existing_permissions.items()}

    created_count = 0
    updated_count = 0

    for perm_data in BUSINESS_PERMISSIONS:
        code = perm_data['code']
        parent_code = perm_data.get('parent_code')

        # 计算 parent_id
        parent_id = None
        if parent_code and parent_code in permission_ids:
            parent_id = permission_ids[parent_code]

        if code in existing_permissions:
            # 更新现有权限
            existing = existing_permissions[code]
            need_update = False

            if existing.menu_path != perm_data.get('menu_path'):
                existing.menu_path = perm_data.get('menu_path')
                need_update = True
            if existing.menu_icon != perm_data.get('menu_icon'):
                existing.menu_icon = perm_data.get('menu_icon')
                need_update = True
            if existing.parent_id != parent_id:
                existing.parent_id = parent_id
                need_update = True
            if existing.sort != perm_data.get('sort', 0):
                existing.sort = perm_data.get('sort', 0)
                need_update = True

            if need_update:
                updated_count += 1
                log.info(f'Updated permission: {code}')
        else:
            # 创建新权限
            new_perm = TenantPermission(
                id=uuid4_str(),
                parent_id=parent_id,
                name=perm_data['name'],
                code=code,
                type=perm_data.get('type', 'module'),
                menu_path=perm_data.get('menu_path'),
                menu_icon=perm_data.get('menu_icon'),
                sort=perm_data.get('sort', 0),
                created_time=timezone.now(),
            )
            db.add(new_perm)
            permission_ids[code] = new_perm.id
            created_count += 1
            log.info(f'Created permission: {code}')

    await db.flush()
    log.info(f'✅ Permissions initialized: {created_count} created, {updated_count} updated')


async def main() -> None:
    """主函数"""
    try:
        async with async_db_session() as db:
            await init_permissions(db)
            await db.commit()

        log.info('✅ Business permissions initialization completed successfully')
    except Exception as e:
        log.error(f'❌ Initialization failed: {e}')
        sys.exit(1)
    finally:
        await async_engine.dispose()


if __name__ == '__main__':
    asyncio.run(main())
