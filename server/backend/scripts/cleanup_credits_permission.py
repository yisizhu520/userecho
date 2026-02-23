#!/usr/bin/env python3
"""清理 credits 权限点及其关联

此脚本用于从数据库中删除 credits 权限及其所有关联关系。
执行方式: python scripts/cleanup_credits_permission.py
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

from sqlalchemy import delete, select

from backend.app.userecho.model.tenant_permission import TenantPermission, TenantRolePermission
from backend.database.db import async_db_session, async_engine


async def cleanup():
    """清理 credits 权限及其关联"""
    async with async_db_session.begin() as db:
        print('=' * 60)
        print('🗑️  清理 credits 权限点及其关联')
        print('=' * 60)
        
        # 1. 查找 credits 权限
        print('\n1️⃣  查找 credits 权限...')
        stmt = select(TenantPermission).where(TenantPermission.code == 'credits')
        result = await db.execute(stmt)
        credits_perm = result.scalar_one_or_none()
        
        if not credits_perm:
            print('   ✅ credits 权限不存在,无需清理')
            return
        
        print(f'   🔍 找到 credits 权限: {credits_perm.id}')
        print(f'      名称: {credits_perm.name}')
        print(f'      路径: {credits_perm.menu_path}')
        
        # 2. 删除角色权限关联
        print('\n2️⃣  删除角色权限关联...')
        stmt = delete(TenantRolePermission).where(
            TenantRolePermission.permission_id == credits_perm.id
        )
        result = await db.execute(stmt)
        deleted_count = result.rowcount
        if deleted_count > 0:
            print(f'   🗑️  删除 {deleted_count} 条角色权限关联')
        else:
            print('   ⏭️  无角色权限关联需要删除')
        
        # 3. 删除权限点
        print('\n3️⃣  删除权限点...')
        await db.delete(credits_perm)
        print('   🗑️  已删除 credits 权限点')
        
        print('\n' + '=' * 60)
        print('✅ 清理完成!')
        print('=' * 60)


async def verify():
    """验证清理结果"""
    async with async_db_session() as db:
        print('\n\n🔍 验证清理结果...')
        print('=' * 60)
        
        # 检查 credits 权限是否还存在
        stmt = select(TenantPermission).where(TenantPermission.code == 'credits')
        result = await db.execute(stmt)
        perm = result.scalar_one_or_none()
        
        if perm:
            print('❌ credits 权限仍然存在!')
            return False
        else:
            print('✅ credits 权限已成功清理')
            return True


async def main():
    """主函数"""
    try:
        await cleanup()
        success = await verify()
        return 0 if success else 1
    except Exception as e:
        print(f'\n❌ 清理失败: {e}')
        import traceback
        traceback.print_exc()
        return 1
    finally:
        await async_engine.dispose()


if __name__ == '__main__':
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
