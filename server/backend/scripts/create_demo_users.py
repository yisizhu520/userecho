"""创建 Demo 环境预置账号

创建 3 个演示角色账号：
- demo_po: 产品负责人 (product_manager)
- demo_ops: 用户运营 (customer_success)
- demo_admin: 系统管理员 (admin)

执行方式: python scripts/create_demo_users.py
"""

import asyncio
import io
import sys

from pathlib import Path

# 修复 Windows 控制台编码问题
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

# 添加项目根目录到 Python 路径
backend_path = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_path))

import bcrypt

from sqlalchemy import select

from backend.app.admin.model import Dept, Role, User, user_role
from backend.app.admin.utils.password_security import get_hash_password
from backend.app.userecho.model import TenantUser
from backend.database.db import async_db_session

# Demo 预置账号配置
DEMO_USERS = [
    {
        "username": "demo_po",
        "nickname": "张产品",
        "email": "po@demo.userecho.app",
        "role": "PM",  # 系统角色
        "user_type": "product_manager",  # 租户角色
        "avatar": "https://api.dicebear.com/7.x/avataaars/svg?seed=po",
        "description": "产品负责人 - 查看优先级看板、AI 洞察、审批议题",
    },
    {
        "username": "demo_ops",
        "nickname": "李运营",
        "email": "ops@demo.userecho.app",
        "role": "CS",  # 系统角色
        "user_type": "customer_success",  # 租户角色
        "avatar": "https://api.dicebear.com/7.x/avataaars/svg?seed=ops",
        "description": "用户运营 - 录入反馈、管理客户、触发聚类",
    },
    {
        "username": "demo_admin",
        "nickname": "王管理",
        "email": "admin@demo.userecho.app",
        "role": "系统管理员",  # 系统角色
        "user_type": "admin",  # 租户角色
        "avatar": "https://api.dicebear.com/7.x/avataaars/svg?seed=admin",
        "description": "系统管理员 - 用户管理、权限配置、看板设置",
    },
]

# 统一演示密码
DEMO_PASSWORD = "demo123456"
DEFAULT_TENANT_ID = "default-tenant"


async def delete_existing_demo_users() -> int:
    """删除现有的 Demo 用户（用于重置）"""
    async with async_db_session.begin() as db:
        deleted = 0
        for user_config in DEMO_USERS:
            username = user_config["username"]
            user = await db.scalar(select(User).where(User.username == username))
            if user:
                # 删除关联的 TenantUser
                tenant_user = await db.scalar(select(TenantUser).where(TenantUser.user_id == user.id))
                if tenant_user:
                    await db.delete(tenant_user)

                # 删除用户角色关联
                await db.execute(user_role.delete().where(user_role.c.user_id == user.id))

                # 删除用户
                await db.delete(user)
                deleted += 1
                print(f"  🗑️  删除现有用户: {username}")

        await db.commit()
        return deleted


async def create_demo_users() -> None:
    """创建 Demo 预置账号"""
    async with async_db_session.begin() as db:
        print("=" * 60)
        print("🚀 Demo 预置账号创建脚本")
        print("=" * 60)
        print()

        # 获取默认部门（如果不存在则设为 None）
        default_dept = await db.scalar(select(Dept).where(Dept.name == "测试").limit(1))
        if not default_dept:
            default_dept = await db.scalar(select(Dept).limit(1))

        dept_id = default_dept.id if default_dept else None

        # 获取所有角色
        roles = await db.scalars(select(Role))
        role_map = {role.name: role for role in roles}

        created_count = 0

        for user_config in DEMO_USERS:
            username = user_config["username"]

            # 检查用户是否已存在
            existing_user = await db.scalar(select(User).where(User.username == username))

            if existing_user:
                print(f"⏭️  跳过: 用户 {username} 已存在")
                continue

            # 创建用户
            salt = bcrypt.gensalt()
            password_hash = get_hash_password(DEMO_PASSWORD, salt)

            user = User(
                username=username,
                nickname=user_config["nickname"],
                password=password_hash,
                salt=salt,
                email=user_config["email"],
                avatar=user_config.get("avatar"),
                status=1,
                is_superuser=False,
                is_staff=True,
                is_multi_login=True,
                dept_id=dept_id,
                tenant_id=DEFAULT_TENANT_ID,
            )

            db.add(user)
            await db.flush()

            # 关联系统角色
            role_name = user_config["role"]
            role = role_map.get(role_name)
            if role:
                await db.execute(user_role.insert().values(user_id=user.id, role_id=role.id))

            # 创建 TenantUser 关联
            tenant_user = TenantUser(
                tenant_id=DEFAULT_TENANT_ID,
                user_id=user.id,
                user_type=user_config.get("user_type", "member"),
                department_id=dept_id,
                status="active",
            )
            db.add(tenant_user)

            print(f"✅ 创建用户: {username} ({user_config['nickname']}, {user_config['description']})")
            created_count += 1

        await db.commit()

        print()
        print("=" * 60)
        print("✅ Demo 预置账号创建完成！")
        print(f"   创建: {created_count} 个")
        print("=" * 60)


async def main(reset: bool = False) -> None:
    """主函数"""
    if reset:
        print("🔄 重置模式：删除现有 Demo 用户...")
        deleted = await delete_existing_demo_users()
        print(f"   已删除: {deleted} 个")
        print()

    await create_demo_users()

    print()
    print("📝 Demo 账号清单 - 统一密码：demo123456")
    print("=" * 60)
    print(f"{'账号':<15} {'昵称':<10} {'角色':<15} {'说明'}")
    print("-" * 60)
    print(f"{'demo_po':<15} {'张产品':<10} {'产品负责人':<15} 看板、洞察、审批")
    print(f"{'demo_ops':<15} {'李运营':<10} {'用户运营':<15} 反馈、客户、聚类")
    print(f"{'demo_admin':<15} {'王管理':<10} {'系统管理员':<15} 用户、权限、设置")
    print()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="创建 Demo 预置账号")
    parser.add_argument("--reset", action="store_true", help="重置模式：先删除现有账号再重建")
    args = parser.parse_args()

    try:
        asyncio.run(main(reset=args.reset))
        print("=" * 60)
        print("✅ Demo 账号初始化成功！")
        print("=" * 60)
    except Exception as e:
        print(f"\n❌ 初始化失败: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
