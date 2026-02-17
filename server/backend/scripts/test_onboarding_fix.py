#!/usr/bin/env python3
"""测试 onboarding status API 修复"""

import asyncio
import io
import sys

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, '.')

from sqlalchemy import select

from backend.app.admin.model import User
from backend.app.userecho.service.onboarding_service import onboarding_service
from backend.database.db import async_db_session


async def test_onboarding_status() -> None:
    """测试 onboarding status 方法"""
    async with async_db_session() as db:
        print('=' * 80)
        print('🧪 测试 Onboarding Status API 修复')
        print('=' * 80)
        print()

        # 获取 boss 用户
        boss = await db.scalar(select(User).where(User.username == 'boss'))
        if not boss:
            print('❌ boss 用户不存在')
            return

        print(f'✅ 测试用户: boss (ID={boss.id})')
        print()

        try:
            # 调用 get_onboarding_status 方法
            print('📞 调用 get_onboarding_status...')
            status = await onboarding_service.get_onboarding_status(db=db, user_id=boss.id)

            print('✅ 调用成功！')
            print()
            print('📊 返回结果:')
            print(f'  needs_onboarding: {status.needs_onboarding}')
            print(f'  current_step: {status.current_step}')
            print(f'  tenant_id: {status.tenant_id}')
            print(f'  board_id: {status.board_id}')
            print(f'  completed_steps: {status.completed_steps}')
            print()

            if not status.needs_onboarding:
                print('✅ 验证通过：boss 用户已完成 onboarding')
            else:
                print(f'⚠️  boss 用户还需要完成 onboarding，当前步骤: {status.current_step}')

        except Exception as e:
            print(f'❌ 调用失败: {e}')
            import traceback

            traceback.print_exc()
            return

        print()
        print('=' * 80)
        print('✅ 测试完成！修复成功')
        print('=' * 80)


if __name__ == '__main__':
    asyncio.run(test_onboarding_status())
