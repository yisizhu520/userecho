#!/usr/bin/env python3
"""
将超级管理员用户添加到系统管理员角色
"""

import asyncio
import io
import sys

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

sys.path.insert(0, ".")

from sqlalchemy import select, text

from backend.app.admin.model import Role, User
from backend.database.db import async_db_session


async def assign_system_admin_role():
    """将超级管理员用户添加到系统管理员角色"""
    async with async_db_session.begin() as db:
        print("=" * 80)
        print("🔧 分配系统管理员角色")
        print("=" * 80)
        print()

        # 1. 查找系统管理员角色
        system_admin_role = await db.scalar(select(Role).where(Role.name == "系统管理员", Role.role_type == "system"))

        if not system_admin_role:
            print("❌ 未找到系统管理员角色！请先运行 create_system_admin_role.py")
            return

        print(f"✅ 找到系统管理员角色（ID={system_admin_role.id}）")
        print()

        # 2. 查找所有超级管理员用户
        superusers = await db.scalars(
            select(User).where(User.is_superuser == True)  # noqa: E712
        )

        superusers_list = list(superusers)
        if not superusers_list:
            print("❌ 未找到超级管理员用户！")
            return

        print(f"📋 找到 {len(superusers_list)} 个超级管理员用户：")
        for user in superusers_list:
            print(f"  ID={user.id}, 用户名={user.username}, 邮箱={getattr(user, 'email', 'N/A')}")
        print()

        # 3. 为每个超级管理员添加系统管理员角色
        added_count = 0
        for user in superusers_list:
            # 检查是否已关联
            existing = await db.scalar(
                text("""
                    SELECT 1 FROM sys_user_role
                    WHERE user_id = :user_id AND role_id = :role_id
                """),
                {"user_id": user.id, "role_id": system_admin_role.id},
            )

            if existing:
                print(f"⏭️ 用户 {user.username} 已拥有系统管理员角色，跳过")
            else:
                # 添加角色关联
                await db.execute(
                    text("""
                        INSERT INTO sys_user_role (user_id, role_id)
                        VALUES (:user_id, :role_id)
                    """),
                    {"user_id": user.id, "role_id": system_admin_role.id},
                )
                added_count += 1
                print(f"✅ 已为用户 {user.username} 添加系统管理员角色")

        print()
        print("=" * 80)
        print(f"✅ 完成！共为 {added_count} 个用户添加了系统管理员角色")
        print()
        print("💡 下一步：")
        print("1. 清除浏览器缓存（Ctrl+Shift+Delete）")
        print("2. 重新登录")
        print("3. 检查侧边栏是否显示任务中心菜单")
        print("=" * 80)


if __name__ == "__main__":
    asyncio.run(assign_system_admin_role())
