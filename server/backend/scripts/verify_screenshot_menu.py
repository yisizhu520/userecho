"""
验证截图识别菜单配置

检查项：
1. sys_menu 表中是否有截图识别菜单
2. 角色权限是否正确分配
3. 菜单排序是否正确
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


async def verify_screenshot_menu() -> bool:
    """验证截图识别菜单配置"""
    async with async_db_session() as db:
        print("=" * 70)
        print("📋 验证截图识别菜单配置")
        print("=" * 70)

        # 1. 检查菜单是否存在
        print("\n1️⃣  检查菜单配置...")
        screenshot_menu = await db.scalar(select(Menu).where(Menu.path == "/app/feedback/screenshot"))

        if not screenshot_menu:
            print("❌ 截图识别菜单不存在！")
            return False

        print("\n✅ 菜单已配置：")
        print(f"   ID: {screenshot_menu.id}")
        print(f"   标题: {screenshot_menu.title}")
        print(f"   名称: {screenshot_menu.name}")
        print(f"   路径: {screenshot_menu.path}")
        print(f"   图标: {screenshot_menu.icon}")
        print(f"   组件: {screenshot_menu.component}")
        print(f"   权限标识: {screenshot_menu.perms}")
        print(f"   排序: {screenshot_menu.sort}")
        print(f"   状态: {'启用' if screenshot_menu.status == 1 else '禁用'}")
        print(f"   显示: {'是' if screenshot_menu.display == 1 else '否'}")

        # 2. 检查父菜单
        if screenshot_menu.parent_id:
            parent = await db.scalar(select(Menu).where(Menu.id == screenshot_menu.parent_id))
            if parent:
                print(f"   父菜单: {parent.title} ({parent.path})")

        # 3. 检查角色权限
        print("\n2️⃣  检查角色权限...")
        result = await db.execute(
            select(Role)
            .join(role_menu, role_menu.c.role_id == Role.id)
            .where(role_menu.c.menu_id == screenshot_menu.id)
        )
        roles = result.scalars().all()

        if roles:
            print(f"\n✅ 有权访问的角色（共 {len(roles)} 个）：")
            for role in roles:
                print(f"   - {role.name} ({role.role_type}): {role.remark}")
        else:
            print("⚠️  没有角色有权访问此菜单！")

        # 4. 查看所有业务菜单排序
        print("\n3️⃣  业务菜单排序...")
        all_menus = await db.execute(
            select(Menu)
            .where(
                Menu.path.like("/app/%"),
                Menu.type == 1,  # 菜单类型
            )
            .order_by(Menu.sort)
        )
        menu_list = all_menus.scalars().all()

        print(f"\n共 {len(menu_list)} 个业务菜单：")
        for menu in menu_list:
            highlight = "👉 " if menu.id == screenshot_menu.id else "   "
            print(f"{highlight}{menu.sort}. {menu.title} ({menu.path})")

        print("\n" + "=" * 70)
        print("✅ 验证完成！截图识别菜单配置正确。")
        print("=" * 70)

        return True


async def main():
    """主函数"""
    try:
        return await verify_screenshot_menu()
    except Exception as e:
        print(f"\n❌ 验证失败: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())

    if success:
        print("\n💡 下一步：")
        print("   1. 重启前端开发服务器（如果正在运行）")
        print("   2. 清除浏览器缓存并刷新页面")
        print('   3. 查看左侧菜单，应该能看到"截图识别"菜单项')
        print('   4. 点击"截图识别"进入截图上传页面')

    sys.exit(0 if success else 1)
