"""
执行路由隔离迁移脚本

此脚本执行以下操作：
1. 执行数据库迁移（添加 role_type 字段并更新菜单路径）
2. 初始化业务菜单和角色
3. 验证迁移结果

执行前请确保：
- 数据库服务正在运行
- 已配置正确的数据库连接
- 已关闭后端服务（避免锁定）

执行方式: python scripts/run_route_migration.py
"""

import asyncio
import subprocess
import sys

from pathlib import Path

# 添加项目根目录到 Python 路径
backend_path = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_path))


def run_alembic_upgrade() -> bool | None:
    """执行 Alembic 升级"""
    print("=" * 70)
    print("📦 第 1 步：执行数据库迁移")
    print("=" * 70)

    try:
        # 切换到 backend 目录
        backend_dir = Path(__file__).resolve().parent.parent

        # 执行 alembic upgrade head
        result = subprocess.run(
            ["alembic", "upgrade", "head"], cwd=backend_dir, capture_output=True, text=True, check=True
        )

        print(result.stdout)
        if result.stderr:
            print("警告:", result.stderr)

        print("✅ 数据库迁移成功！")
        return True

    except subprocess.CalledProcessError as e:
        print(f"❌ 数据库迁移失败: {e}")
        print("输出:", e.stdout)
        print("错误:", e.stderr)
        return False
    except Exception as e:
        print(f"❌ 执行失败: {e}")
        return False


async def init_business_menus() -> bool | None:
    """初始化业务菜单"""
    print("\n" + "=" * 70)
    print("📋 第 2 步：初始化业务菜单和角色")
    print("=" * 70)

    try:
        # 导入初始化脚本
        from scripts.init_business_menus import init_business_menus as do_init
        from scripts.init_business_menus import verify_initialization

        await do_init()
        await verify_initialization()

        return True
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        import traceback

        traceback.print_exc()
        return False


async def verify_migration() -> bool:
    """验证迁移结果"""
    print("\n" + "=" * 70)
    print("🔍 第 3 步：验证迁移结果")
    print("=" * 70)

    from sqlalchemy import select

    from backend.app.admin.model import Menu, Role
    from backend.database.db import async_db_session

    async with async_db_session() as db:
        # 1. 检查 role_type 字段
        system_roles = await db.scalars(select(Role).where(Role.role_type == "system"))
        system_role_list = list(system_roles)

        business_roles = await db.scalars(select(Role).where(Role.role_type == "business"))
        business_role_list = list(business_roles)

        print("\n✅ Role 表 role_type 字段检查:")
        print(f"   - 系统角色数量: {len(system_role_list)}")
        for role in system_role_list:
            print(f"     • {role.name}")
        print(f"   - 业务角色数量: {len(business_role_list)}")
        for role in business_role_list:
            print(f"     • {role.name}")

        # 2. 检查系统管理菜单路径
        admin_menus = await db.scalars(select(Menu).where(Menu.path.like("/admin/%")))
        admin_menu_list = list(admin_menus)

        print("\n✅ 系统管理菜单路径检查 (/admin/*):")
        print(f"   - 菜单数量: {len(admin_menu_list)}")
        for menu in admin_menu_list[:5]:  # 只显示前 5 个
            print(f"     • {menu.title}: {menu.path}")
        if len(admin_menu_list) > 5:
            print(f"     ... 共 {len(admin_menu_list)} 个菜单")

        # 3. 检查业务功能菜单路径
        app_menus = await db.scalars(select(Menu).where(Menu.path.like("/app/%")))
        app_menu_list = list(app_menus)

        print("\n✅ 业务功能菜单路径检查 (/app/*):")
        print(f"   - 菜单数量: {len(app_menu_list)}")
        for menu in app_menu_list:
            print(f"     • {menu.title}: {menu.path}")

        # 4. 检查是否还有旧路径
        old_paths = await db.scalars(
            select(Menu).where(
                (Menu.path.like("/system/%"))
                | (Menu.path.like("/log/%"))
                | (Menu.path.like("/monitor/%"))
                | (Menu.path.like("/scheduler/%"))
                | (Menu.path == "/system")
                | (Menu.path == "/log")
                | (Menu.path == "/monitor")
                | (Menu.path == "/scheduler")
            )
        )
        old_path_list = list(old_paths)

        if old_path_list:
            print("\n⚠️  发现未迁移的旧路径:")
            for menu in old_path_list:
                print(f"     • {menu.title}: {menu.path}")
            return False
        print("\n✅ 未发现旧路径，迁移完整")

        return True


def main() -> None:
    """主函数"""
    print("\n" + "=" * 70)
    print("🚀 UserEcho 路由隔离迁移脚本")
    print("=" * 70)
    print("\n此脚本将执行以下操作：")
    print("1. 添加 role_type 字段到 sys_role 表")
    print("2. 更新所有菜单路径（/system/* → /admin/system/*，等）")
    print("3. 创建业务菜单和角色")
    print("4. 验证迁移结果")
    print("\n⚠️  请确保：")
    print("   - 数据库服务正在运行")
    print("   - 已配置正确的数据库连接")
    print("   - 后端服务已停止（避免锁定数据库）")

    # 询问用户确认
    response = input("\n是否继续？(y/N): ")
    if response.lower() != "y":
        print("❌ 操作已取消")
        return

    success = True

    # Step 1: 执行数据库迁移
    if not run_alembic_upgrade():
        print("\n❌ 数据库迁移失败，停止执行")
        success = False
        return

    # Step 2: 初始化业务菜单
    if not asyncio.run(init_business_menus()):
        print("\n❌ 业务菜单初始化失败，但迁移已完成")
        success = False

    # Step 3: 验证迁移
    if success and not asyncio.run(verify_migration()):
        print("\n⚠️  迁移验证发现问题")
        success = False

    # 总结
    print("\n" + "=" * 70)
    if success:
        print("✅ 迁移成功完成！")
        print("\n下一步：")
        print("1. 重启后端服务")
        print("2. 登录系统测试菜单权限")
        print("3. 检查不同角色的菜单显示")
    else:
        print("❌ 迁移过程中出现错误")
        print("\n如需回滚，执行: alembic downgrade -1")
    print("=" * 70)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ 操作已中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 执行失败: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
