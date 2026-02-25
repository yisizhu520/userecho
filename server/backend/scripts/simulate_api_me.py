"""模拟 /sys/users/me API 调用"""

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
from backend.app.userecho.service.tenant_member_service import tenant_member_service
from backend.database.db import async_db_session


async def simulate_api():
    async with async_db_session() as db:
        # 模拟获取当前用户
        user = await db.scalar(select(User).where(User.username == "demo_admin"))
        if not user:
            print("❌ 用户不存在")
            return

        print(f"👤 当前用户: {user.username} (ID: {user.id})")
        print(f"   tenant_id: {user.tenant_id}")
        print()

        # 模拟 API 逻辑
        tenant_permissions: list[str] = []
        tenant_id = user.tenant_id

        print(f"🔍 Getting tenant permissions for user {user.id}, tenant_id: {tenant_id}")

        if tenant_id:
            tenant_permissions = await tenant_member_service.get_user_permission_codes(db, tenant_id, user.id)
            print(f"✅ Got tenant permissions: {tenant_permissions}")
        else:
            print("⚠️  tenant_id is None, skipping permission query")

        print()
        print("📊 最终结果:")
        print(f"   tenantPermissions: {tenant_permissions}")
        print(f"   权限数量: {len(tenant_permissions)}")


asyncio.run(simulate_api())
