#!/usr/bin/env python
"""验证数据库初始化结果"""

import asyncio
import sys
import io
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import select, func
from backend.database.db import async_db_session
from backend.app.admin.model import Menu, Role, User, Dept
from backend.app.userecho.model import Tenant, Board, TenantUser, SubscriptionPlan


async def verify():
    async with async_db_session() as db:
        print("=" * 80)
        print("数据库初始化结果验证")
        print("=" * 80)
        print()

        # 检查租户
        tenant_count = await db.scalar(select(func.count(Tenant.id)))
        print(f"  租户数量: {tenant_count}")

        # 检查看板
        board_count = await db.scalar(select(func.count(Board.id)))
        print(f"  看板数量: {board_count}")

        # 检查用户
        user_count = await db.scalar(select(func.count(User.id)))
        print(f"  用户数量: {user_count}")

        # 检查角色
        role_count = await db.scalar(select(func.count(Role.id)))
        print(f"  角色数量: {role_count}")

        # 检查部门
        dept_count = await db.scalar(select(func.count(Dept.id)))
        print(f"  部门数量: {dept_count}")

        # 检查订阅套餐
        plan_count = await db.scalar(select(func.count(SubscriptionPlan.id)))
        print(f"  订阅套餐数量: {plan_count}")

        # 检查租户用户关联
        tenant_user_count = await db.scalar(select(func.count(TenantUser.id)))
        print(f"  租户用户关联数量: {tenant_user_count}")

        # 检查系统菜单
        sys_menu_count = await db.scalar(select(func.count(Menu.id)).where(Menu.path.like("/system/%")))
        print(f"  系统菜单数量: {sys_menu_count}")

        print()
        print("=" * 80)
        print("验证完成！")
        print("=" * 80)


if __name__ == "__main__":
    asyncio.run(verify())
