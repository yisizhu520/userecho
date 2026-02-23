#!/usr/bin/env python3
"""修复 boss 用户的租户归属"""

import asyncio
import io
import sys

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

sys.path.insert(0, ".")

from sqlalchemy import select, update

from backend.app.admin.model import User
from backend.app.userecho.model import TenantUser
from backend.database.db import async_db_session


async def fix_boss_tenant() -> None:
    """将 boss 用户切换到 userecho 租户"""
    async with async_db_session.begin() as db:
        print("=" * 80)
        print("🔧 修复 boss 用户租户归属")
        print("=" * 80)
        print()

        # 1. 更新 User 表的 tenant_id
        await db.execute(
            update(User).where(User.username == "boss").values(tenant_id="79a2fd29-36f0-4d94-9999-e35ad6e66031")
        )
        print("✅ 更新 User.tenant_id 为 79a2fd29-36f0-4d94-9999-e35ad6e66031")

        # 2. 更新 TenantUser 表的 tenant_id
        boss = await db.scalar(select(User).where(User.username == "boss"))
        if boss:
            await db.execute(
                update(TenantUser)
                .where(TenantUser.user_id == boss.id)
                .values(tenant_id="79a2fd29-36f0-4d94-9999-e35ad6e66031")
            )
            print("✅ 更新 TenantUser.tenant_id 为 79a2fd29-36f0-4d94-9999-e35ad6e66031")

        await db.commit()
        print()
        print("✅ 修复完成！请重新登录以刷新 JWT token")
        print()


if __name__ == "__main__":
    asyncio.run(fix_boss_tenant())
