"""验证租户用户角色分配"""

import asyncio
import sys
import io

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from pathlib import Path

backend_path = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_path))

from sqlalchemy import select

from backend.app.admin.model import User
from backend.app.userecho.model import TenantRole, TenantUser, TenantUserRole
from backend.database.db import async_db_session


async def check():
    async with async_db_session() as db:
        print("📊 租户用户角色分配情况：")
        print("=" * 60)

        # 查询所有租户用户
        result = await db.execute(
            select(TenantUser, User)
            .join(User, TenantUser.user_id == User.id)
            .where(TenantUser.tenant_id == "default-tenant")
        )

        for tenant_user, user in result:
            print(f"\n👤 {user.username} ({user.nickname})")

            # 查询该用户的租户角色
            roles_result = await db.execute(
                select(TenantRole)
                .join(TenantUserRole, TenantRole.id == TenantUserRole.role_id)
                .where(TenantUserRole.tenant_user_id == tenant_user.id)
            )
            roles = roles_result.scalars().all()

            if roles:
                for role in roles:
                    print(f"   └─ 角色: {role.name} ({role.code})")
            else:
                print("   └─ ❌ 未分配任何租户角色")


asyncio.run(check())
