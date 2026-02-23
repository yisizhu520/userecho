"""
为现有角色添加截图识别菜单权限

执行: python scripts/add_screenshot_menu_permission.py
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

from sqlalchemy import select

from backend.app.admin.model import Menu, Role, role_menu
from backend.database.db import async_db_session


async def add_screenshot_permission() -> bool:
    """为业务角色添加截图识别菜单权限"""
    async with async_db_session.begin() as db:
        print("=" * 60)
        print("🔐 为业务角色添加截图识别菜单权限")
        print("=" * 60)

        # 1. 查找截图识别菜单
        screenshot_menu = await db.scalar(select(Menu).where(Menu.path == "/app/feedback/screenshot"))

        if not screenshot_menu:
            print("❌ 截图识别菜单不存在！请先运行 init_business_menus.py")
            return False

        print(f"\n✅ 找到截图识别菜单: ID={screenshot_menu.id}, 标题={screenshot_menu.title}")

        # 2. 查找需要授权的角色（PM 和 CS）
        roles_to_grant = ["PM", "CS"]

        print(f"\n📋 为以下角色添加权限: {', '.join(roles_to_grant)}")

        updated_count = 0
        for role_name in roles_to_grant:
            role = await db.scalar(select(Role).where(Role.name == role_name))

            if not role:
                print(f"   ⚠️  角色 {role_name} 不存在，跳过")
                continue

            # 检查是否已有权限
            existing = await db.scalar(
                select(role_menu.c.role_id).where(
                    role_menu.c.role_id == role.id, role_menu.c.menu_id == screenshot_menu.id
                )
            )

            if existing:
                print(f"   ⏭️  角色 {role_name} 已有权限，跳过")
                continue

            # 添加权限
            await db.execute(role_menu.insert().values(role_id=role.id, menu_id=screenshot_menu.id))
            print(f"   ✅ 为角色 {role_name} (ID={role.id}) 添加权限")
            updated_count += 1

        await db.commit()

        print(f"\n✅ 权限添加完成！共更新 {updated_count} 个角色")
        print("=" * 60)

        return True


async def verify_permissions() -> None:
    """验证权限是否正确添加"""
    async with async_db_session() as db:
        print("\n🔍 验证权限...\n")

        screenshot_menu = await db.scalar(select(Menu).where(Menu.path == "/app/feedback/screenshot"))

        if not screenshot_menu:
            return

        # 查询有此菜单权限的所有角色
        result = await db.execute(
            select(Role)
            .join(role_menu, role_menu.c.role_id == Role.id)
            .where(role_menu.c.menu_id == screenshot_menu.id)
        )
        roles = result.scalars().all()

        print(f'有权访问"截图识别"的角色（共 {len(roles)} 个）：')
        for role in roles:
            print(f"   - {role.name} ({role.role_type})")


async def main():
    """主函数"""
    success = await add_screenshot_permission()
    if success:
        await verify_permissions()
    return success


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ 执行失败: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
