#!/usr/bin/env python3
"""检查 boss 用户的实际 tenant_id"""

import asyncio
import io
import sys

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

sys.path.insert(0, ".")

from sqlalchemy import select

from backend.app.admin.model import User
from backend.database.db import async_db_session


async def check_boss_tenant() -> None:
    """检查 boss 用户的 tenant_id"""
    async with async_db_session() as db:
        print("=" * 80)
        print("🔍 检查 boss 用户的 tenant_id")
        print("=" * 80)
        print()

        # 查询 boss 用户
        boss = await db.scalar(select(User).where(User.username == "boss"))

        if not boss:
            print("❌ boss 用户不存在")
            return

        print("✅ boss 用户信息:")
        print(f"   ID: {boss.id}")
        print(f"   username: {boss.username}")
        print(f"   tenant_id: {boss.tenant_id!r}")
        print()

        # 提示
        print('💡 如果 tenant_id 是 None 或不是 "default-tenant"，需要更新')
        print("   JWT token 会从 User.tenant_id 读取租户信息")
        print()

        if boss.tenant_id != "default-tenant":
            print('⚠️  警告: boss.tenant_id 不是 "default-tenant"')
            print(f"   当前值: {boss.tenant_id!r}")
            print('   期望值: "default-tenant"')
            print()
            print("🔧 需要执行以下 SQL 修复:")
            print("   UPDATE sys_user SET tenant_id = 'default-tenant' WHERE username = 'boss';")
        else:
            print("✅ boss.tenant_id 正确")
            print()
            print("💡 如果 API 仍然返回空，可能是 JWT token 缓存问题")
            print("   解决方案：重新登录以刷新 token")


if __name__ == "__main__":
    asyncio.run(check_boss_tenant())
