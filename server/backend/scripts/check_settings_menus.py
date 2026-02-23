#!/usr/bin/env python3
"""
检查系统设置菜单是否存在

用法:
    python check_settings_menus.py
"""

import asyncio
import sys

from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select

from backend.app.admin.model import Menu
from backend.database.db import async_db_session, async_engine


async def check_settings_menus() -> None:
    """检查系统设置相关菜单"""
    async with async_db_session() as db:
        print('📋 检查系统设置相关菜单')
        print('=' * 60)

        # 查找所有 /app/settings 相关的菜单
        stmt = select(Menu).where(Menu.path.like('/app/settings%')).order_by(Menu.sort)
        result = await db.execute(stmt)
        menus = result.scalars().all()

        if not menus:
            print('❌ 未找到任何 /app/settings 相关的菜单!')
            print()
            print('💡 需要创建以下菜单:')
            print('   1. /app/settings (系统设置 - 父菜单)')
            print('   2. /app/settings/members (成员管理)')
            print('   3. /app/settings/roles (角色管理)')
            print('   4. /app/settings/credits (积分配置)')
        else:
            print(f'✅ 找到 {len(menus)} 个系统设置菜单:')
            print()
            for menu in menus:
                parent_info = f' (父菜单 ID: {menu.parent_id})' if menu.parent_id else ' (顶级菜单)'
                display_info = '显示' if menu.display == 1 else '隐藏'
                print(f'   - {menu.title}')
                print(f'     路径: {menu.path}')
                print(f'     权限: {menu.perms or "无"}')
                print(f'     状态: {display_info}{parent_info}')
                print()

        # 检查所有 /app/* 菜单
        print('=' * 60)
        print('📋 所有业务菜单:')
        print()
        stmt = select(Menu).where(Menu.path.like('/app/%')).order_by(Menu.sort)
        result = await db.execute(stmt)
        all_menus = result.scalars().all()

        for menu in all_menus:
            print(f'   - {menu.title} ({menu.path})')


async def main() -> int | None:
    """主函数"""
    try:
        await check_settings_menus()
        return 0
    except Exception as e:
        print(f'❌ 检查失败: {e}')
        import traceback

        traceback.print_exc()
        return 1
    finally:
        await async_engine.dispose()


if __name__ == '__main__':
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
