"""验证 Demo 环境初始化结果

检查以下数据是否正确初始化：
- 系统基础数据（角色、部门、菜单）
- 租户数据（默认租户、看板）
- Demo 预置账号
- 示例业务数据（客户、议题、反馈）

执行方式: python scripts/verify_demo_data.py
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

from sqlalchemy import func, select

from backend.app.admin.model import Dept, Menu, Role, User
from backend.app.userecho.model import Board, Customer, Feedback, Tenant, Topic
from backend.database.db import async_db_session


async def verify_system_data() -> bool:
    """验证系统基础数据"""
    print("📊 系统数据：")
    all_passed = True

    async with async_db_session() as db:
        # 检查角色
        role_count = await db.scalar(select(func.count(Role.id)))
        print(f"   角色: {role_count} 个")
        if role_count == 0:
            print("   ❌ 警告：未找到系统角色")
            all_passed = False

        # 检查部门
        dept_count = await db.scalar(select(func.count(Dept.id)))
        print(f"   部门: {dept_count} 个")
        if dept_count == 0:
            print("   ❌ 警告：未找到系统部门")
            all_passed = False

        # 检查菜单
        menu_count = await db.scalar(select(func.count(Menu.id)))
        print(f"   菜单: {menu_count} 个")
        if menu_count == 0:
            print("   ❌ 警告：未找到系统菜单")
            all_passed = False

    return all_passed


async def verify_tenant_data() -> bool:
    """验证租户数据"""
    print("")
    print("🏢 租户数据：")
    all_passed = True

    async with async_db_session() as db:
        # 检查默认租户
        tenant = await db.scalar(select(Tenant).where(Tenant.id == "default-tenant"))
        if tenant:
            print(f"   ✅ 默认租户: {tenant.name}")
        else:
            print("   ❌ 错误：未找到默认租户")
            all_passed = False

        # 检查看板
        board_count = await db.scalar(select(func.count(Board.id)).where(Board.tenant_id == "default-tenant"))
        print(f"   看板: {board_count} 个")
        if board_count == 0:
            print("   ⚠️  警告：未找到看板数据")

    return all_passed


async def verify_demo_data() -> bool:
    """验证 Demo 预置数据"""
    print("")
    print("🎭 Demo 数据：")
    all_passed = True

    async with async_db_session() as db:
        # 检查 Demo 用户
        demo_users = await db.scalars(select(User).where(User.username.like("demo_%")).order_by(User.username))
        user_list = list(demo_users)
        print(f"   Demo 用户: {len(user_list)} 个")

        expected_users = {"demo_admin", "demo_ops", "demo_po"}
        found_users = {u.username for u in user_list}

        for u in user_list:
            print(f"      - {u.username} ({u.nickname})")

        missing_users = expected_users - found_users
        if missing_users:
            print(f"   ❌ 错误：缺少 Demo 用户: {missing_users}")
            all_passed = False

        # 检查客户
        customer_count = await db.scalar(select(func.count(Customer.id)).where(Customer.tenant_id == "default-tenant"))
        print(f"   客户: {customer_count} 个")
        if customer_count == 0:
            print("   ⚠️  警告：未找到客户数据")

        # 检查议题
        topic_count = await db.scalar(select(func.count(Topic.id)).where(Topic.tenant_id == "default-tenant"))
        print(f"   议题: {topic_count} 个")
        if topic_count == 0:
            print("   ⚠️  警告：未找到议题数据")

        # 检查反馈
        feedback_count = await db.scalar(select(func.count(Feedback.id)).where(Feedback.tenant_id == "default-tenant"))
        print(f"   反馈: {feedback_count} 条")
        if feedback_count == 0:
            print("   ⚠️  警告：未找到反馈数据")

    return all_passed


async def verify_all() -> bool:
    """执行所有验证"""
    print("=" * 70)
    print("🔍 Demo 环境验证")
    print("=" * 70)
    print()

    system_ok = await verify_system_data()
    tenant_ok = await verify_tenant_data()
    demo_ok = await verify_demo_data()

    print()
    print("=" * 70)

    if system_ok and tenant_ok and demo_ok:
        print("✅ 所有验证通过！")
        return True
    else:
        print("⚠️  部分验证未通过，请检查上述输出")
        return False


if __name__ == "__main__":
    try:
        success = asyncio.run(verify_all())
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ 验证失败: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
