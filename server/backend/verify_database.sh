#!/bin/bash
# 快速验证数据库初始化状态
# 执行方式：./verify_database.sh

set -e

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}============================================================${NC}"
echo -e "${BLUE}🔍 数据库初始化状态验证${NC}"
echo -e "${BLUE}============================================================${NC}"
echo

# 激活虚拟环境
if [ -f "../.venv/Scripts/activate" ]; then
    source ../.venv/Scripts/activate
elif [ -f "../.venv/bin/activate" ]; then
    source ../.venv/bin/activate
else
    echo -e "${YELLOW}⚠️  未找到虚拟环境${NC}"
    exit 1
fi

# 运行验证
python test_db_connection_simple.py

echo
echo "---"
echo

python -c "
import asyncio, io, sys
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, '.')
from sqlalchemy import select, func
from backend.app.admin.model import User, Role, Menu, user_role
from backend.database.db import async_db_session

async def verify():
    async with async_db_session() as db:
        menus = await db.scalar(select(func.count(Menu.id)))
        business_menus = await db.scalar(select(func.count(Menu.id)).where(Menu.path.like('/app/%')))
        roles = await db.scalar(select(func.count(Role.id)))
        business_roles = await db.scalar(select(func.count(Role.id)).where(Role.role_type == 'business'))
        users = await db.scalar(select(func.count(User.id)))
        test_users = await db.scalar(select(func.count(User.id)).where(User.username.in_(['sysadmin','pm','cs','dev','boss','hybrid'])))
        
        print('📊 数据库统计:')
        print(f'   菜单总数: {menus} (业务菜单: {business_menus})')
        print(f'   角色总数: {roles} (业务角色: {business_roles})')
        print(f'   用户总数: {users} (测试用户: {test_users}/6)')
        print()
        
        # 检查测试用户详情
        print('📝 测试用户状态:')
        test_usernames = ['sysadmin', 'pm', 'cs', 'dev', 'boss', 'hybrid']
        for username in test_usernames:
            user = await db.scalar(select(User).where(User.username == username))
            if user:
                roles = await db.scalars(
                    select(Role)
                    .join(user_role, Role.id == user_role.c.role_id)
                    .where(user_role.c.user_id == user.id)
                )
                role_list = list(roles)
                status = '✅' if role_list else '⚠️ '
                role_names = ', '.join([r.name for r in role_list]) if role_list else '(无角色)'
                print(f'   {status} {username:<12} - {role_names}')
            else:
                print(f'   ❌ {username:<12} - 不存在')
        print()
        
        # 总体评估
        if menus >= 8 and roles >= 5 and test_users == 6:
            print('✅ 数据库已完全初始化，可以直接使用！')
            print()
            print('💡 下一步:')
            print('   1. 启动后端: cd server/backend && python run.py')
            print('   2. 启动前端: cd front && pnpm dev')
            print('   3. 使用测试账号登录 (密码: Test123456)')
            return True
        else:
            print('⚠️  数据库部分初始化，建议重新运行初始化脚本:')
            print('   ./init_database.sh')
            return False

asyncio.run(verify())
"

echo
echo -e "${BLUE}============================================================${NC}"
