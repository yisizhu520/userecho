#!/usr/bin/env python3
"""
创建系统管理员角色并关联系统菜单
"""

import asyncio
import io
import sys

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

sys.path.insert(0, ".")

from sqlalchemy import select, text

from backend.app.admin.model import Menu, Role
from backend.database.db import async_db_session


async def create_system_admin_role():
    """创建系统管理员角色"""
    async with async_db_session.begin() as db:
        print("=" * 80)
        print("🔧 创建系统管理员角色")
        print("=" * 80)
        print()

        # 1. 检查是否已存在系统管理员角色
        existing_role = await db.scalar(
            select(Role).where(
                Role.name == "系统管理员",
                Role.role_type == "system"
            )
        )

        if existing_role:
            print(f"✅ 系统管理员角色已存在（ID={existing_role.id}）")
            role_id = existing_role.id
        else:
            # 创建系统管理员角色
            new_role = Role(
                name="系统管理员",
                role_type="system",
                status=1,
                remark="拥有所有系统管理权限的超级管理员角色"
            )
            db.add(new_role)
            await db.flush()
            
            role_id = new_role.id
            print(f"✅ 已创建系统管理员角色（ID={role_id}）")
        print()

        # 2. 获取所有系统菜单（/system/*）
        system_menus = await db.scalars(
            select(Menu).where(
                Menu.status == 1,
                Menu.path.like("/system%")
            )
        )

        system_menu_ids = [m.id for m in system_menus]
        print(f"📋 找到 {len(system_menu_ids)} 个系统菜单")
        print()

        # 3. 关联所有系统菜单到系统管理员角色
        if system_menu_ids:
            # 删除旧的关联
            await db.execute(
                text("DELETE FROM sys_role_menu WHERE role_id = :role_id"),
                {"role_id": role_id}
            )

            # 插入新的关联
            for menu_id in system_menu_ids:
                await db.execute(
                    text("""
                        INSERT INTO sys_role_menu (role_id, menu_id)
                        VALUES (:role_id, :menu_id)
                        ON CONFLICT DO NOTHING
                    """),
                    {"role_id": role_id, "menu_id": menu_id}
                )

            print(f"✅ 已关联 {len(system_menu_ids)} 个系统菜单到系统管理员角色")
        print()

        # 4. 验证任务中心菜单是否已关联
        task_menu = await db.scalar(
            select(Menu).where(Menu.name == "TaskCenter")
        )

        if task_menu:
            is_associated = await db.scalar(
                text("""
                    SELECT 1 FROM sys_role_menu
                    WHERE role_id = :role_id AND menu_id = :menu_id
                """),
                {"role_id": role_id, "menu_id": task_menu.id}
            )

            if is_associated:
                print(f"✅ 任务中心菜单（ID={task_menu.id}）已关联到系统管理员角色")
            else:
                print(f"❌ 任务中心菜单（ID={task_menu.id}）未关联！")
        print()

        print("=" * 80)
        print("💡 下一步：")
        print("1. 将用户分配到系统管理员角色（使用后台管理界面）")
        print("2. 或者直接插入用户角色关联：")
        print()
        print("   INSERT INTO sys_user_role (user_id, role_id)")
        print(f"   VALUES (<用户ID>, {role_id});")
        print()
        print("3. 清除浏览器缓存并重新登录")
        print("=" * 80)


if __name__ == "__main__":
    asyncio.run(create_system_admin_role())
