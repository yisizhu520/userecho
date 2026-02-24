"""测试用户权限查询"""

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
from backend.app.userecho.crud.crud_tenant_member import tenant_member_dao
from backend.app.userecho.service.tenant_member_service import TenantMemberService
from backend.database.db import async_db_session


async def test_permissions():
    async with async_db_session() as db:
        # 测试 demo_admin 用户
        user = await db.scalar(select(User).where(User.username == "demo_admin"))
        if not user:
            print("❌ 用户不存在")
            return

        print(f"👤 用户: {user.username} (ID: {user.id})")
        print(f"   租户ID: {user.tenant_id}")
        print()

        # 1. 查询 TenantUser
        tenant_user = await tenant_member_dao.get_by_user_id(db, user.tenant_id, user.id)
        if not tenant_user:
            print("❌ TenantUser 不存在")
            return

        print(f"✅ TenantUser 找到: {tenant_user.id}")
        print(f"   user_type: {tenant_user.user_type}")
        print()

        # 2. 查询角色
        roles = await tenant_member_dao.get_member_roles(db, tenant_user.id)
        print(f"📋 租户用户角色数量: {len(roles)}")
        for role_assoc in roles:
            print(f"   - role_id: {role_assoc.role_id}")
        print()

        # 3. 查询权限码
        permissions = await TenantMemberService.get_user_permission_codes(db, user.tenant_id, user.id)
        print(f"🔑 权限码列表: {permissions}")
        print(f"   权限数量: {len(permissions)}")


asyncio.run(test_permissions())
