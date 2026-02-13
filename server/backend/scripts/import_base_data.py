"""导入基础数据脚本

只导入缺失的基础数据（部门、系统菜单、admin用户等），不影响已有的业务数据
执行方式: python scripts/import_base_data.py
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

from sqlalchemy import text
from backend.database.db import async_db_session
from backend.core.path_conf import BASE_PATH
from backend.core.conf import settings
from backend.common.enums import DataBaseType


async def import_base_data():
    """导入基础数据"""
    print('=' * 70)
    print('🚀 导入基础数据脚本')
    print('=' * 70)
    print()
    
    # 确定 SQL 文件路径
    db_dir = (
        BASE_PATH / 'sql' / 'mysql'
        if DataBaseType.mysql == settings.DATABASE_TYPE
        else BASE_PATH / 'sql' / 'postgresql'
    )
    sql_file = db_dir / 'init_test_data.sql'
    
    if not sql_file.exists():
        print(f'❌ SQL 文件不存在: {sql_file}')
        return False
    
    print(f'📄 SQL 文件: {sql_file}')
    print()
    
    # 读取 SQL 文件
    with open(sql_file, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    # 分割 SQL 语句
    statements = []
    current_statement = []
    
    for line in sql_content.split('\n'):
        line = line.strip()
        # 跳过注释和空行
        if not line or line.startswith('--'):
            continue
        
        current_statement.append(line)
        
        # 如果行以分号结束，这是一个完整的语句
        if line.endswith(';'):
            stmt = ' '.join(current_statement)
            statements.append(stmt)
            current_statement = []
    
    print(f'📊 共 {len(statements)} 条 SQL 语句')
    print()
    
    # 执行 SQL 语句
    async with async_db_session.begin() as db:
        success_count = 0
        skip_count = 0
        error_count = 0
        
        for i, stmt in enumerate(statements, 1):
            try:
                # 提取表名用于显示
                stmt_lower = stmt.lower()
                if 'insert into' in stmt_lower:
                    table_name = stmt_lower.split('insert into')[1].split()[0].strip()
                    print(f'[{i}/{len(statements)}] 导入 {table_name}...', end=' ')
                else:
                    print(f'[{i}/{len(statements)}] 执行...', end=' ')
                
                await db.execute(text(stmt))
                print('✅')
                success_count += 1
                
            except Exception as e:
                error_str = str(e)
                # 如果是主键冲突或数据已存在，跳过
                if 'duplicate key' in error_str.lower() or 'already exists' in error_str.lower():
                    print('⏭️  (已存在)')
                    skip_count += 1
                else:
                    print(f'❌ {e}')
                    error_count += 1
        
        await db.commit()
    
    print()
    print('=' * 70)
    print('📊 导入结果:')
    print(f'   ✅ 成功: {success_count}')
    print(f'   ⏭️  跳过: {skip_count} (数据已存在)')
    print(f'   ❌ 失败: {error_count}')
    print('=' * 70)
    print()
    
    if error_count == 0:
        print('✅ 基础数据导入完成！')
        print()
        print('💡 建议操作:')
        print('   1. 使用 admin/Admin123456 登录系统')
        print('   2. 检查系统管理菜单是否正常显示')
        print('   3. 如需要，可以在角色管理中给业务角色分配系统管理菜单')
    else:
        print('⚠️  部分数据导入失败，请检查错误信息')
    
    return error_count == 0


async def verify_data():
    """验证导入结果"""
    async with async_db_session() as db:
        from sqlalchemy import select, func
        from backend.app.admin.model import User, Role, Menu, Dept
        
        print()
        print('🔍 验证导入结果...')
        print()
        
        # 检查部门
        dept_count = await db.scalar(select(func.count(Dept.id)))
        print(f'   部门数量: {dept_count}')
        
        # 检查菜单
        total_menus = await db.scalar(select(func.count(Menu.id)))
        system_menus = await db.scalar(select(func.count(Menu.id)).where(
            (Menu.path.like('/system%')) | 
            (Menu.path.like('/log%')) | 
            (Menu.path.like('/monitor%'))
        ))
        app_menus = await db.scalar(select(func.count(Menu.id)).where(Menu.path.like('/app/%')))
        print(f'   菜单总数: {total_menus} (系统: {system_menus}, 业务: {app_menus})')
        
        # 检查用户
        admin = await db.scalar(select(User).where(User.username == 'admin'))
        admin_status = '✅ 存在' if admin else '❌ 不存在'
        print(f'   admin 用户: {admin_status}')
        
        # 检查角色
        role_count = await db.scalar(select(func.count(Role.id)))
        print(f'   角色总数: {role_count}')
        
        print()


async def main():
    """主函数"""
    success = await import_base_data()
    if success:
        await verify_data()


if __name__ == '__main__':
    try:
        asyncio.run(main())
        sys.exit(0)
    except KeyboardInterrupt:
        print('\n\n⚠️  操作被用户中断')
        sys.exit(1)
    except Exception as e:
        print(f'\n❌ 发生错误: {e}')
        import traceback
        traceback.print_exc()
        sys.exit(1)

