"""检查管理员账号是否存在"""

import asyncio

from sqlalchemy import select, text

from backend.app.admin.model.user import User
from backend.database.db import async_db_session


async def check_admin() -> None:
    async with async_db_session() as db:
        # 方法1: 通过 ORM 查询
        result = await db.execute(select(User).where(User.username == 'admin'))
        user = result.scalar_one_or_none()

        if user:
            print('✅ 找到管理员账号（ORM 查询）')
            print(f'   ID: {user.id}')
            print(f'   UUID: {user.uuid}')
            print(f'   用户名: {user.username}')
            print(f'   昵称: {user.nickname}')
            print(f'   邮箱: {user.email}')
            print(f'   状态: {user.status}')
            print(f'   超级管理员: {user.is_superuser}')
            print(f'   部门ID: {user.dept_id}')
        else:
            print('❌ 未找到管理员账号（ORM 查询）')

        # 方法2: 直接 SQL 查询（验证数据库层面）
        result2 = await db.execute(text("SELECT id, username, nickname, email FROM sys_user WHERE username = 'admin'"))
        row = result2.first()

        if row:
            print('\n✅ 找到管理员账号（原生 SQL 查询）')
            print(f'   ID: {row[0]}')
            print(f'   用户名: {row[1]}')
            print(f'   昵称: {row[2]}')
            print(f'   邮箱: {row[3]}')
        else:
            print('\n❌ 未找到管理员账号（原生 SQL 查询）')

        # 统计 sys_user 表中的总用户数
        result3 = await db.execute(text('SELECT COUNT(*) FROM sys_user'))
        count = result3.scalar()
        print(f'\n📊 sys_user 表中共有 {count} 个用户')


if __name__ == '__main__':
    try:
        asyncio.run(check_admin())
    except Exception as e:
        print(f'\n❌ 检查失败: {e}')
        import traceback

        traceback.print_exc()
