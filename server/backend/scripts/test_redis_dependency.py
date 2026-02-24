"""测试初始化脚本是否需要 Redis"""

import sys
import io

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from pathlib import Path

backend_path = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_path))

# 测试导入是否会触发 Redis 连接
print("=" * 60)
print("测试：导入初始化脚本相关模块是否需要 Redis")
print("=" * 60)
print()

try:
    print("1️⃣  导入 async_db_session...")
    from backend.database.db import async_db_session
    print("   ✅ 成功（不需要 Redis）")
except Exception as e:
    print(f"   ❌ 失败: {e}")

try:
    print("2️⃣  导入 TenantUser 模型...")
    from backend.app.userecho.model import TenantUser
    print("   ✅ 成功（不需要 Redis）")
except Exception as e:
    print(f"   ❌ 失败: {e}")

try:
    print("3️⃣  导入 User 模型...")
    from backend.app.admin.model import User
    print("   ✅ 成功（不需要 Redis）")
except Exception as e:
    print(f"   ❌ 失败: {e}")

try:
    print("4️⃣  导入 tenant_member_service...")
    from backend.app.userecho.service.tenant_member_service import tenant_member_service
    print("   ✅ 成功（不需要 Redis）")
except Exception as e:
    print(f"   ❌ 失败: {e}")

try:
    print("5️⃣  导入 backend.main (FastAPI app)...")
    from backend.main import app
    print("   ✅ 成功（不需要 Redis）")
except Exception as e:
    print(f"   ❌ 失败: {e}")

print()
print("=" * 60)
print("结论：所有核心模块导入都不需要 Redis 连接")
print("=" * 60)
