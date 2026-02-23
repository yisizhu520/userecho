#!/usr/bin/env python3
"""
验证 boss 用户在 default-tenant 中的角色

用法:
    python verify_boss_roles.py
"""

import asyncio
import sys

from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.admin.crud.crud_user import user_dao
from backend.app.userecho.crud.crud_tenant_member import tenant_member_dao
from backend.app.userecho.crud.crud_tenant_role import tenant_role_dao
from backend.database.db import async_db_session, async_engine


async def verify_boss_roles(db: AsyncSession) -> None:
    """验证 boss 用户的角色"""
    tenant_id = 'default-tenant'
    username = 'boss'

    print(f'📋 验证租户 {tenant_id} 中用户 {username} 的角色')
    print('=' * 60)

    # 1. 查找 boss 用户
    boss_user = await user_dao.get_by_username(db, username)
    if not boss_user:
        print(f'❌ 用户 {username} 不存在')
        return

    print('✅ 用户信息:')
    print(f'   - 用户名: {boss_user.username}')
    print(f'   - 昵称: {boss_user.nickname}')
    print(f'   - ID: {boss_user.id}')
    print(f'   - 租户 ID: {boss_user.tenant_id}')
    print()

    # 2. 查找租户成员关联
    tenant_member = await tenant_member_dao.get_by_user_id(db, tenant_id, boss_user.id)

    if not tenant_member:
        print(f'❌ 用户 {username} 不是租户 {tenant_id} 的成员')
        return

    print('✅ 租户成员信息:')
    print(f'   - 成员 ID: {tenant_member.id}')
    print(f'   - 用户类型: {tenant_member.user_type}')
    print(f'   - 状态: {tenant_member.status}')
    print(f'   - 加入时间: {tenant_member.joined_at}')
    print()

    # 3. 获取成员的所有角色
    member_roles = await tenant_member_dao.get_member_roles(db, tenant_member.id)

    if not member_roles:
        print(f'⚠️  用户 {username} 没有分配任何角色')
        return

    print(f'✅ 用户拥有的角色 ({len(member_roles)} 个):')

    for user_role in member_roles:
        # 获取角色详情
        role = await tenant_role_dao.get(db, user_role.role_id)
        if role:
            print(f'   - {role.name} ({role.code})')
            print(f'     • 角色 ID: {role.id}')
            print(f'     • 描述: {role.description or "无"}')
            print(f'     • 是否内置: {"是" if role.is_builtin else "否"}')
            print(f'     • 状态: {role.status}')
            print(f'     • 分配时间: {user_role.assigned_at}')
            print()

    # 4. 检查是否有管理员角色
    admin_role = await tenant_role_dao.get_by_code(db, tenant_id, 'admin')
    if admin_role:
        has_admin = any(r.role_id == admin_role.id for r in member_roles)
        print('=' * 60)
        if has_admin:
            print('🎉 确认: boss 用户已经是租户管理员!')
        else:
            print('⚠️  警告: boss 用户不是租户管理员')
            print(f'   管理员角色 ID: {admin_role.id}')
            print(f'   用户当前角色 ID: {[r.role_id for r in member_roles]}')


async def main() -> int:
    """主函数"""
    try:
        async with async_db_session() as db:
            await verify_boss_roles(db)
    except Exception as e:
        print(f'❌ 验证失败: {e}')
        import traceback

        traceback.print_exc()
        return 1
    finally:
        await async_engine.dispose()

    return 0


if __name__ == '__main__':
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
