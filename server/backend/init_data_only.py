#!/usr/bin/env python
"""
仅初始化数据脚本
前提：数据库表结构已存在，Alembic 版本已标记
"""

import asyncio
import sys
from pathlib import Path

# 添加项目路径到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


async def main():
    """主函数"""
    print("=" * 80)
    print("🚀 开始初始化数据（仅数据，不涉及表结构）")
    print("=" * 80)
    print()

    # 步骤 1: 创建默认租户和看板
    print("步骤 1/5: 创建默认租户和看板")
    print("-" * 80)
    try:
        from scripts.init_default_tenant import main as init_tenant

        await init_tenant()
        print("✅ 默认租户和看板创建完成")
    except Exception as e:
        print(f"❌ 创建默认租户失败: {e}")
        import traceback

        traceback.print_exc()
        return False
    print()

    # 步骤 2: 初始化业务菜单和角色
    print("步骤 2/5: 初始化业务菜单和角色")
    print("-" * 80)
    try:
        from scripts.init_business_menus import main as init_menus

        await init_menus()
        print("✅ 业务菜单和角色初始化完成")
    except Exception as e:
        print(f"❌ 业务菜单初始化失败: {e}")
        import traceback

        traceback.print_exc()
        # 继续执行，不返回
    print()

    # 步骤 3: 添加额外系统管理菜单
    print("步骤 3/5: 添加额外系统管理菜单")
    print("-" * 80)
    try:
        from scripts.init_system_extra_menus import main as init_extra_menus

        await init_extra_menus()
        print("✅ 额外系统菜单初始化完成")
    except Exception as e:
        print(f"❌ 额外系统菜单初始化失败: {e}")
        import traceback

        traceback.print_exc()
        # 继续执行，不返回
    print()

    # 步骤 4: 初始化订阅套餐
    print("步骤 4/5: 初始化订阅套餐")
    print("-" * 80)
    try:
        from scripts.init_subscription_plans import main as init_plans

        await init_plans()
        print("✅ 订阅套餐初始化完成")
    except Exception as e:
        print(f"⚠️  订阅套餐初始化失败: {e}")
        import traceback

        traceback.print_exc()
        # 继续执行，不返回
    print()

    # 步骤 5: 创建测试用户
    print("步骤 5/5: 创建测试用户")
    print("-" * 80)
    try:
        from scripts.create_test_users import main as create_users

        await create_users()
        print("✅ 测试用户创建完成")
    except Exception as e:
        print(f"⚠️  测试用户创建失败: {e}")
        import traceback

        traceback.print_exc()
        # 继续执行，不返回
    print()

    print("=" * 80)
    print("✅ 数据初始化完成！")
    print("=" * 80)
    print()
    print("📝 登录信息：")
    print("  超级管理员: admin / Admin123456")
    print("  测试账号: sysadmin, pm, cs, dev, boss, hybrid / Test123456")
    print()

    return True


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️  用户中断")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ 初始化失败: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
