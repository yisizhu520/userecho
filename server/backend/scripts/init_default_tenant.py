#!/usr/bin/env python3
"""
初始化默认租户脚本
在 fba init 之后立即执行，创建 default-tenant 租户记录
"""
import asyncio
import io
import sys
from datetime import datetime

# Windows 平台 UTF-8 输出支持
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, '.')

from sqlalchemy import select
from backend.app.userecho.model import Tenant, Board
from backend.database.db import async_db_session
from backend.utils.timezone import timezone


async def create_default_tenant():
    """创建默认租户和默认看板"""
    async with async_db_session() as db:
        # 检查默认租户是否已存在
        existing = await db.scalar(
            select(Tenant).where(Tenant.id == 'default-tenant')
        )
        
        if existing:
            print('✅ 默认租户已存在')
        else:
            # 创建默认租户
            default_tenant = Tenant(
                id='default-tenant',
                name='默认租户',
                slug='default',  # 新增 slug 字段
                status='active',
                created_time=timezone.now(),
            )
            
            db.add(default_tenant)
            await db.flush()
            
            print('✅ 默认租户创建成功')
            print(f'   租户ID: {default_tenant.id}')
            print(f'   租户名称: {default_tenant.name}')
            print(f'   slug: {default_tenant.slug}')
            print(f'   状态: {default_tenant.status}')
        
        # 检查默认看板是否已存在
        existing_board = await db.scalar(
            select(Board).where(Board.id == 'default-board')
        )
        
        if existing_board:
            print('✅ 默认看板已存在')
        else:
            # 创建默认看板
            default_board = Board(
                id='default-board',
                tenant_id='default-tenant',
                name='默认看板',
                url_name='default',
                description='默认反馈看板，用于收集所有产品反馈',
                access_mode='private',
                category='general',
                sort_order=0,
                created_time=timezone.now(),
            )
            
            db.add(default_board)
            print('✅ 默认看板创建成功')
            print(f'   看板ID: {default_board.id}')
            print(f'   看板名称: {default_board.name}')
            print(f'   URL: {default_board.url_name}')
        
        await db.commit()


async def main():
    """主函数"""
    print('=' * 80)
    print('🏢 初始化默认租户')
    print('=' * 80)
    print()
    
    try:
        await create_default_tenant()
        print()
        print('✅ 初始化完成！')
        return 0
    except Exception as e:
        print()
        print(f'❌ 初始化失败: {e}')
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

