#!/usr/bin/env python3
"""
检查并分配 boss 用户的系统角色

用法:
    python assign_boss_system_role.py
"""

import asyncio
import sys

from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import insert, select

from backend.app.admin.crud.crud_user import user_dao
from backend.app.admin.model import Role, user_role  # 导入多对多关系表
from backend.database.db import async_db_session, async_engine


async def check_and_assign_boss_role() -> None:
    """检查并为 boss 用户分配系统角色"""
    async with async_db_session.begin() as db:
        print('📋 检查并分配 boss 用户的系统角色')
        print('=' * 60)

        # 1. 查找 boss 用户
        boss_user = await user_dao.get_by_username(db, 'boss')
        if not boss_user:
            print('❌ 用户 boss 不存在')
            return

        print('\n✅ 用户信息:')
        print(f'   - 用户名: {boss_user.username}')
        print(f'   - ID: {boss_user.id}')
        print(f'   - 是否超级管理员: {boss_user.is_superuser}')

        # 2. 检查当前的系统角色
        print('\n2️⃣  检查当前系统角色...')
        stmt = select(user_role).where(user_role.c.user_id == boss_user.id)
        result = await db.execute(stmt)
        current_roles = result.all()

        if current_roles:
            print(f'   找到 {len(current_roles)} 个角色关联:')
            for role_relation in current_roles:
                # 获取角色详情
                role = await db.get(Role, role_relation.role_id)
                if role:
                    print(f'   - {role.name} (ID: {role.id}, 类型: {role.role_type or "business"})')
        else:
            print('   ❌ 没有分配任何系统角色!')

        # 3. 查找 "老板" 角色
        print('\n3️⃣  查找 "老板" 系统角色...')
        stmt = select(Role).where(Role.name == '老板')
        result = await db.execute(stmt)
        boss_role = result.scalar_one_or_none()

        if not boss_role:
            print('   ❌ 未找到 "老板" 角色!')
            print('   💡 请先运行 init_business_menus.py 创建业务角色')
            return

        print(f'   ✅ 找到角色: {boss_role.name} (ID: {boss_role.id}, 类型: {boss_role.role_type or "business"})')

        # 4. 检查是否已经有该角色
        already_has_role = any(r.role_id == boss_role.id for r in current_roles)

        if already_has_role:
            print('\n   ✅ boss 用户已经拥有 "老板" 角色')
        else:
            print('\n4️⃣  为 boss 用户分配 "老板" 角色...')
            # 插入角色关联
            stmt = insert(user_role).values(user_id=boss_user.id, role_id=boss_role.id)
            await db.execute(stmt)
            print('   ✅ 成功分配 "老板" 角色')

        # 5. 验证最终结果
        print('\n5️⃣  验证最终结果...')
        stmt = select(user_role).where(user_role.c.user_id == boss_user.id)
        result = await db.execute(stmt)
        final_roles = result.all()

        print(f'   boss 用户现在拥有 {len(final_roles)} 个系统角色:')
        for role_relation in final_roles:
            role = await db.get(Role, role_relation.role_id)
            if role:
                print(f'   - {role.name} (ID: {role.id})')


async def main() -> int | None:
    """主函数"""
    try:
        await check_and_assign_boss_role()

        print('\n' + '=' * 60)
        print('✅ 完成!')
        print('=' * 60)
        print('\n💡 现在请刷新浏览器,应该可以看到系统设置菜单了!')

        return 0
    except Exception as e:
        print(f'\n❌ 执行失败: {e}')
        import traceback

        traceback.print_exc()
        return 1
    finally:
        await async_engine.dispose()


if __name__ == '__main__':
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
