"""检查 tenant_user_roles 表数据"""

import asyncio
import sys
import io

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from pathlib import Path

backend_path = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_path))

from sqlalchemy import select, text

from backend.app.admin.model import User
from backend.app.userecho.model import TenantUser, TenantUserRole, TenantRole
from backend.database.db import async_db_session


async def check():
    async with async_db_session() as db:
        print("=" * 70)
        print("📊 检查 tenant_user_roles 表数据")
        print("=" * 70)
        print()

        # 1. 检查表中总记录数
        count_result = await db.execute(text("SELECT COUNT(*) FROM tenant_user_roles"))
        total_count = count_result.scalar()
        print(f"📋 tenant_user_roles 表总记录数: {total_count}")
        print()

        # 2. 查询所有记录
        result = await db.execute(
            select(TenantUserRole, TenantUser, User, TenantRole)
            .join(TenantUser, TenantUserRole.tenant_user_id == TenantUser.id)
            .join(User, TenantUser.user_id == User.id)
            .join(TenantRole, TenantUserRole.role_id == TenantRole.id)
        )

        records = result.all()

        if records:
            print(f"✅ 找到 {len(records)} 条角色分配记录：")
            print()
            for assoc, tenant_user, user, role in records:
                print(f"👤 {user.username} ({user.nickname})")
                print(f"   └─ 租户角色: {role.name} ({role.code})")
                print(f"   └─ tenant_user_id: {tenant_user.id}")
                print(f"   └─ role_id: {role.id}")
                print()
        else:
            print("❌ 表为空！没有任何角色分配记录")
            print()

        # 3. 检查 demo 用户
        print("=" * 70)
        print("🔍 检查 Demo 用户")
        print("=" * 70)
        print()

        demo_users = await db.execute(select(User).where(User.username.in_(["demo_po", "demo_ops", "demo_admin"])))
        demo_users_list = demo_users.scalars().all()

        if demo_users_list:
            print(f"✅ 找到 {len(demo_users_list)} 个 Demo 用户")
            for user in demo_users_list:
                print(f"   - {user.username} (ID: {user.id})")

                # 检查对应的 TenantUser
                tenant_user = await db.scalar(
                    select(TenantUser).where(TenantUser.user_id == user.id, TenantUser.tenant_id == "default-tenant")
                )

                if tenant_user:
                    print(f"     └─ TenantUser 存在: {tenant_user.id}")

                    # 检查角色
                    role_count = await db.scalar(
                        select(text("COUNT(*)"))
                        .select_from(TenantUserRole)
                        .where(TenantUserRole.tenant_user_id == tenant_user.id)
                    )
                    print(f"     └─ 分配的角色数量: {role_count}")
                else:
                    print("     └─ ❌ TenantUser 不存在")
        else:
            print("❌ 未找到任何 Demo 用户")


asyncio.run(check())
