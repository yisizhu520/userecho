#!/usr/bin/env python3
"""
检查 boss 用户的系统角色分配情况

用法:
    python check_boss_system_roles.py
"""

import asyncio
import sys

from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select

from backend.app.admin.crud.crud_user import user_dao
from backend.app.admin.model import Menu, Role, role_menu
from backend.database.db import async_db_session, async_engine


async def check_boss_system_roles() -> None:
    """检查 boss 用户的系统角色"""
    async with async_db_session() as db:
        print("📋 检查 boss 用户的系统角色分配")
        print("=" * 60)

        # 1. 查找 boss 用户
        boss_user = await user_dao.get_by_username(db, "boss")
        if not boss_user:
            print("❌ 用户 boss 不存在")
            return

        print("\n✅ 用户信息:")
        print(f"   - 用户名: {boss_user.username}")
        print(f"   - ID: {boss_user.id}")
        print(f"   - 是否超级管理员: {boss_user.is_superuser}")
        print(f"   - 是否员工: {boss_user.is_staff}")

        # 2. 获取系统角色
        # 使用 eager loading 获取 roles
        from sqlalchemy.orm import selectinload

        from backend.app.admin.model import User

        stmt = select(User).where(User.id == boss_user.id).options(selectinload(User.roles))
        result = await db.execute(stmt)
        user_with_roles = result.scalar_one()

        system_roles = user_with_roles.roles

        if not system_roles:
            print("\n❌ boss 用户没有分配任何系统角色!")
            print("\n💡 这就是为什么看不到系统设置菜单的原因:")
            print("   - 前端通过 /api/v1/menus/sidebar 获取菜单")
            print("   - 后端基于 request.user.roles (系统角色) 过滤菜单")
            print("   - boss 用户只有租户角色,没有系统角色")
            print("   - 因此无法获取到任何菜单")

            print("\n🔧 解决方案:")
            print('   需要为 boss 用户分配系统角色,例如 "老板" 或 "PM" 角色')
        else:
            print(f"\n✅ boss 用户拥有 {len(system_roles)} 个系统角色:")
            for role in system_roles:
                print(f"   - {role.name} (ID: {role.id}, 类型: {role.role_type})")

                # 获取该角色的菜单权限
                stmt = select(Menu).join(role_menu).where(role_menu.c.role_id == role.id)
                result = await db.execute(stmt)
                menus = result.scalars().all()

                print(f"     拥有 {len(menus)} 个菜单权限:")
                for menu in menus[:5]:  # 只显示前5个
                    print(f"       • {menu.title} ({menu.path})")
                if len(menus) > 5:
                    print(f"       ... 还有 {len(menus) - 5} 个菜单")

        # 3. 列出所有可用的系统角色
        print("\n\n📋 数据库中所有可用的系统角色:")
        print("=" * 60)
        stmt = select(Role).order_by(Role.role_type, Role.id)
        result = await db.execute(stmt)
        all_roles = result.scalars().all()

        for role in all_roles:
            print(f"   - {role.name} (ID: {role.id}, 类型: {role.role_type or 'business'})")


async def main() -> int | None:
    """主函数"""
    try:
        await check_boss_system_roles()
        return 0
    except Exception as e:
        print(f"\n❌ 检查失败: {e}")
        import traceback

        traceback.print_exc()
        return 1
    finally:
        await async_engine.dispose()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
