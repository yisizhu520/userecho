"""创建测试用户脚本

用于测试路由隔离功能的不同角色用户
执行方式: python scripts/create_test_users.py
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

import bcrypt
from sqlalchemy import select
from backend.app.admin.model import User, Role, Dept, user_role
from backend.database.db import async_db_session
from backend.app.admin.utils.password_security import get_hash_password


# 测试用户配置
TEST_USERS = [
    {
        'username': 'sysadmin',
        'nickname': '系统管理员',
        'email': 'sysadmin@userecho.com',
        'role': '系统管理员',
        'description': '系统管理员角色，只能访问系统管理菜单',
    },
    {
        'username': 'pm',
        'nickname': '产品经理',
        'email': 'pm@userecho.com',
        'role': 'PM',
        'description': 'PM角色，可管理全部反馈功能',
    },
    {
        'username': 'cs',
        'nickname': '客户成功',
        'email': 'cs@userecho.com',
        'role': 'CS',
        'description': 'CS角色，可查看反馈和客户',
    },
    {
        'username': 'dev',
        'nickname': '开发人员',
        'email': 'dev@userecho.com',
        'role': '开发',
        'description': '开发角色，只读需求主题',
    },
    {
        'username': 'boss',
        'nickname': '租户管理员',
        'email': 'boss@userecho.com',
        'role': '老板',
        'description': '老板角色，查看全部',
    },
    {
        'username': 'hybrid',
        'nickname': '混合角色用户',
        'email': 'hybrid@userecho.com',
        'role': ['系统管理员', 'PM'],
        'description': '混合角色，同时拥有系统管理员和PM权限',
    },
]

# 统一密码
TEST_PASSWORD = 'Test123456'


async def create_test_users():
    """创建测试用户"""
    async with async_db_session.begin() as db:
        print('=' * 60)
        print('🚀 测试用户创建脚本')
        print('=' * 60)
        print()
        
        # 获取默认部门
        default_dept = await db.scalar(
            select(Dept).where(Dept.name == '测试').limit(1)
        )
        if not default_dept:
            default_dept = await db.scalar(select(Dept).limit(1))
        
        dept_id = default_dept.id if default_dept else 1
        
        # 获取所有角色
        roles = await db.scalars(select(Role))
        role_map = {role.name: role for role in roles}
        
        created_count = 0
        skipped_count = 0
        
        for user_config in TEST_USERS:
            username = user_config['username']
            
            # 检查用户是否已存在
            existing_user = await db.scalar(
                select(User).where(User.username == username)
            )
            
            if existing_user:
                print(f'⏭️  跳过: 用户 {username} 已存在')
                skipped_count += 1
                continue
            
            # 创建用户
            salt = bcrypt.gensalt()
            password_hash = get_hash_password(TEST_PASSWORD, salt)
            
            user = User(
                username=username,
                nickname=user_config['nickname'],
                password=password_hash,
                salt=salt,
                email=user_config['email'],
                status=1,
                is_superuser=False,
                is_staff=True,
                is_multi_login=True,
                dept_id=dept_id,
            )
            
            db.add(user)
            await db.flush()
            
            # 关联角色
            role_names = user_config['role'] if isinstance(user_config['role'], list) else [user_config['role']]
            assigned_roles = []
            
            for role_name in role_names:
                role = role_map.get(role_name)
                if role:
                    await db.execute(
                        user_role.insert().values(user_id=user.id, role_id=role.id)
                    )
                    assigned_roles.append(role_name)
            
            print(f'✅ 创建用户: {username} ({", ".join(assigned_roles)})')
            created_count += 1
        
        await db.commit()
        
        print()
        print('=' * 60)
        print(f'✅ 测试用户创建完成！')
        print(f'   创建: {created_count} 个')
        print(f'   跳过: {skipped_count} 个')
        print('=' * 60)
        print()
        print('📝 测试账号清单 - 统一密码：Test123456')
        print('=' * 60)
        print(f'{"账号":<12} {"角色":<20} {"菜单权限"}')
        print('-' * 60)
        print(f'{"sysadmin":<12} {"系统管理员":<20} /admin/* 菜单')
        print(f'{"pm":<12} {"PM":<20} /app/* 全部菜单')
        print(f'{"cs":<12} {"CS":<20} /app/* 部分菜单')
        print(f'{"dev":<12} {"开发":<20} /app/* 只读菜单')
        print(f'{"boss":<12} {"老板":<20} /app/* 全部菜单')
        print(f'{"hybrid":<12} {"混合角色":<20} 全部菜单')
        print()
        print('💡 提示：使用上述账号登录前端测试菜单显示功能')
        print()


async def verify_users():
    """验证测试用户"""
    async with async_db_session() as db:
        print('🔍 验证测试用户...')
        print()
        
        for user_config in TEST_USERS:
            username = user_config['username']
            user = await db.scalar(
                select(User).where(User.username == username)
            )
            
            if user:
                # 查询用户的角色
                roles = await db.scalars(
                    select(Role)
                    .join(user_role, Role.id == user_role.c.role_id)
                    .where(user_role.c.user_id == user.id)
                )
                role_names = [role.name for role in roles]
                print(f'  ✅ {username:<12} - {", ".join(role_names)}')
            else:
                print(f'  ❌ {username:<12} - 不存在')
        
        print()


async def main():
    """主函数"""
    await create_test_users()
    await verify_users()


if __name__ == '__main__':
    print('=' * 60)
    print('测试用户创建脚本')
    print('=' * 60)
    print()
    
    try:
        asyncio.run(main())
        print('=' * 60)
        print('✅ 初始化成功！')
        print('=' * 60)
    except Exception as e:
        print(f'\n❌ 初始化失败: {e}')
        import traceback
        traceback.print_exc()
        sys.exit(1)
