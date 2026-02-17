"""删除无用的 UserEcho 父路由

这个脚本用于删除数据库中的 /app/userecho 父路由，因为我们已经改成平铺路由结构。
执行方式: python scripts/remove_userecho_parent.py
"""

import asyncio
import sys

from pathlib import Path

# 添加项目根目录到 Python 路径
backend_path = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_path))

from sqlalchemy import select

from backend.app.admin.model import Menu
from backend.database.db import async_db_session


async def remove_userecho_parent() -> None:
    """删除 /app/userecho 父路由"""
    async with async_db_session.begin() as db:
        print('🗑️  开始删除 /app/userecho 父路由...')

        # 查找父路由
        userecho_menu = await db.scalar(select(Menu).where(Menu.path == '/app/userecho'))

        if not userecho_menu:
            print('   ⏭️  /app/userecho 路由不存在，跳过')
            return

        print(f'   找到父路由: {userecho_menu.title} (ID: {userecho_menu.id})')

        # 将子菜单的 parent_id 设置为 None
        child_menus = await db.scalars(select(Menu).where(Menu.parent_id == userecho_menu.id))
        child_list = list(child_menus)

        if child_list:
            print(f'   更新 {len(child_list)} 个子菜单的 parent_id...')
            for child in child_list:
                child.parent_id = None
                print(f'     - {child.title} ({child.path})')

        # 删除父路由
        await db.delete(userecho_menu)
        await db.commit()

        print('   ✅ 删除成功！')


if __name__ == '__main__':
    print('=' * 60)
    print('🚀 删除 UserEcho 父路由脚本')
    print('=' * 60)

    try:
        asyncio.run(remove_userecho_parent())
        print('\n' + '=' * 60)
        print('✅ 操作成功！')
        print('=' * 60)
    except Exception as e:
        print(f'\n❌ 操作失败: {e}')
        import traceback

        traceback.print_exc()
        sys.exit(1)
