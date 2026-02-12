#!/usr/bin/env python3
"""
创建测试用户脚本

用于测试路由隔离功能的不同角色用户
"""
import asyncio
import sys
from pathlib import Path

import bcrypt
from sqlalchemy import insert, select

# 添加项目根目录到 Python 路径
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from backend.app.admin.model.role import Role
from backend.app.admin.model.user import User
from backend.app.admin.utils.password_security import get_hash_password
from backend.app.admin.model.m2m import user_role
from backend.database.db import async_db_session


async def create_test_users():
    """创建测试用户"""
    print('🚀 开始创建测试用户...\n')
    
    async with async_db_session() as db:
        # 1. 查询现有角色
        role_result = await db.execute(select(Role))
        roles = {role.name: role for role in role_result.scalars().all()}
        
        print(f'📋 现有角色列表:')
        for name, role in roles.items():
            print(f'  - {name} (ID: {role.id}, type: {role.role_type})')
        print()
        
        # 2. 获取部门 ID（使用默认的测试部门）
        dept_id = 1
        
        # 3. 定义测试用户
        test_users = [
            {
                'username': 'sysadmin',
                'nickname': '系统管理员',
                'password': 'Admin123456',
                'email': 'sysadmin@feedalyze.com',
                'roles': ['系统管理员'] if '系统管理员' in roles else [],
                'description': '只能看到 /admin/* 系统管理菜单',
            },
            {
                'username': 'pm',
                'nickname': '产品经理',
                'password': 'PM123456',
                'email': 'pm@feedalyze.com',
                'roles': ['PM'] if 'PM' in roles else [],
                'description': '只能看到 /app/* 业务功能菜单（全权限）',
            },
            {
                'username': 'cs',
                'nickname': '客户成功',
                'password': 'CS123456',
                'email': 'cs@feedalyze.com',
                'roles': ['CS'] if 'CS' in roles else [],
                'description': '只能看到 /app/* 部分业务菜单（反馈+客户）',
            },
            {
                'username': 'dev',
                'nickname': '开发人员',
                'password': 'Dev123456',
                'email': 'dev@feedalyze.com',
                'roles': ['开发'] if '开发' in roles else [],
                'description': '只能看到 /app/* 部分业务菜单（只读需求）',
            },
            {
                'username': 'boss',
                'nickname': '租户管理员',
                'password': 'Boss123456',
                'email': 'boss@feedalyze.com',
                'roles': ['老板'] if '老板' in roles else [],
                'description': '可以看到 /app/* 全部业务功能',
            },
            {
                'username': 'hybrid',
                'nickname': '混合角色用户',
                'password': 'Hybrid123456',
                'email': 'hybrid@feedalyze.com',
                'roles': ['系统管理员', 'PM'] if all(r in roles for r in ['系统管理员', 'PM']) else [],
                'description': '同时拥有系统+业务角色，能看到全部菜单',
            },
        ]
        
        created_count = 0
        skipped_count = 0
        
        for user_data in test_users:
            username = user_data['username']
            
            # 检查用户是否已存在
            existing_user = await db.execute(
                select(User).where(User.username == username)
            )
            if existing_user.scalar_one_or_none():
                print(f'⏭️  跳过：用户 {username} 已存在')
                skipped_count += 1
                continue
            
            # 检查角色是否存在
            if not user_data['roles']:
                print(f'⚠️  警告：角色不存在，跳过用户 {username}')
                skipped_count += 1
                continue
            
            # 生成密码哈希
            salt = bcrypt.gensalt()
            hashed_password = get_hash_password(user_data['password'], salt)
            
            # 创建用户
            new_user = User(
                username=username,
                nickname=user_data['nickname'],
                password=hashed_password,
                salt=salt,
                email=user_data['email'],
                dept_id=dept_id,
                status=1,
                is_superuser=False,
                is_staff=True,
                is_multi_login=True,
            )
            db.add(new_user)
            await db.flush()
            
            # 关联角色
            role_ids = [roles[role_name].id for role_name in user_data['roles']]
            user_role_data = [
                {'user_id': new_user.id, 'role_id': role_id}
                for role_id in role_ids
            ]
            user_role_stmt = insert(user_role)
            await db.execute(user_role_stmt, user_role_data)
            
            print(f'✅ 创建用户：{username}')
            print(f'   昵称：{user_data["nickname"]}')
            print(f'   密码：{user_data["password"]}')
            print(f'   邮箱：{user_data["email"]}')
            print(f'   角色：{", ".join(user_data["roles"])}')
            print(f'   说明：{user_data["description"]}')
            print()
            
            created_count += 1
        
        await db.commit()
        
        print(f'\n📊 统计信息：')
        print(f'   ✅ 成功创建：{created_count} 个用户')
        print(f'   ⏭️  跳过：{skipped_count} 个用户')
        print(f'\n🎉 测试用户创建完成！')
        
        # 打印登录信息表格
        print('\n' + '='*80)
        print('📝 测试账号清单')
        print('='*80)
        print(f'{"账号":<15} {"密码":<15} {"角色":<20} {"说明":<30}')
        print('-'*80)
        for user_data in test_users:
            roles_str = ', '.join(user_data['roles']) if user_data['roles'] else '无角色'
            print(
                f'{user_data["username"]:<15} '
                f'{user_data["password"]:<15} '
                f'{roles_str:<20} '
                f'{user_data["description"]:<30}'
            )
        print('='*80)
        print('\n💡 提示：')
        print('  1. 使用上述账号密码登录前端测试菜单显示')
        print('  2. 如果看不到角色，需要先执行：python scripts/init_business_menus.py')
        print('  3. 超级管理员账号：admin / Admin123456 (可以看到全部菜单)')


if __name__ == '__main__':
    asyncio.run(create_test_users())
