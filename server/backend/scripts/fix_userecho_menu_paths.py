"""修复 UserEcho 菜单路径，统一使用 /userecho 前缀

此脚本用于修复已存在的数据库中的菜单路径，确保 path 和 component 的命名空间一致。
执行方式: python scripts/fix_userecho_menu_paths.py
"""

import asyncio
import io
import sys

from pathlib import Path

# 修复 Windows 控制台编码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 添加项目根目录到 Python 路径
backend_path = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_path))

from sqlalchemy import select, update

from backend.app.admin.model import Menu
from backend.database.db import async_db_session


async def fix_menu_paths() -> None:
    """修复菜单路径"""
    async with async_db_session.begin() as db:
        print('=' * 80)
        print('🔧 开始修复 UserEcho 菜单路径')
        print('=' * 80)

        # 路径映射表：旧路径 -> 新路径
        path_mapping = {
            '/userecho': '/app/userecho',
            '/userecho/feedback/list': '/app/feedback/list',
            '/userecho/discovery': '/app/ai/discovery',
            '/userecho/feedback/import': '/app/feedback/import',
            '/userecho/topic/list': '/app/topic/list',
            '/userecho/customer': '/app/customer',
            '/userecho/settings': '/app/settings',
            '/userecho/settings/clustering': '/app/settings/clustering',
        }

        print('\n📋 将要修改的路径：')
        for old_path, new_path in path_mapping.items():
            print(f'   {old_path} → {new_path}')

        # 更新每个路径
        updated_count = 0
        for old_path, new_path in path_mapping.items():
            result = await db.execute(update(Menu).where(Menu.path == old_path).values(path=new_path))
            if result.rowcount > 0:
                print(f'   ✅ 更新 {old_path} → {new_path}')
                updated_count += result.rowcount

        await db.commit()

        print(f'\n✅ 修复完成！共更新 {updated_count} 个菜单')

        # 验证修复结果
        print('\n🔍 验证修复结果...')
        menus = await db.scalars(select(Menu).where(Menu.path.like('/app/%')))
        menu_list = list(menus)
        print(f'\n📊 /app 路径下的菜单（共 {len(menu_list)} 个）：')
        for menu in menu_list:
            print(f'   - {menu.title} ({menu.path})')


if __name__ == '__main__':
    print('⚠️  此脚本将修改数据库中的菜单路径')
    print('⚠️  确保已备份数据库或知道如何回滚')
    print()

    try:
        asyncio.run(fix_menu_paths())
        print('\n' + '=' * 80)
        print('✅ 修复成功！请重启后端服务和前端应用')
        print('=' * 80)
    except Exception as e:
        print(f'\n❌ 修复失败: {e}')
        import traceback

        traceback.print_exc()
        sys.exit(1)
