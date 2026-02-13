"""简单的数据库连接测试脚本

用于快速验证数据库配置是否正确
执行方式: python test_db_connection_simple.py
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
backend_path = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_path))


async def test_connection():
    """测试数据库连接"""
    try:
        print('=' * 60)
        print('数据库连接测试')
        print('=' * 60)
        print()
        
        # 1. 检查 .env 文件
        env_file = backend_path / '.env'
        if not env_file.exists():
            print('❌ 错误：.env 文件不存在')
            print(f'   期望路径: {env_file}')
            print()
            print('请在 server/backend/ 目录下创建 .env 文件')
            return False
        
        print(f'✅ .env 文件存在: {env_file}')
        print()
        
        # 2. 读取配置
        print('📋 读取数据库配置...')
        from backend.core.conf import settings
        
        print(f'   DATABASE_TYPE: {settings.DATABASE_TYPE}')
        print(f'   DATABASE_HOST: {settings.DATABASE_HOST}')
        print(f'   DATABASE_PORT: {settings.DATABASE_PORT}')
        print(f'   DATABASE_USER: {settings.DATABASE_USER}')
        print(f'   DATABASE_SCHEMA: {settings.DATABASE_SCHEMA}')
        print()
        
        # 3. 测试连接
        print('🔌 测试数据库连接...')
        from sqlalchemy import text
        from backend.database.db import async_db_session
        
        async with async_db_session() as db:
            result = await db.execute(text('SELECT 1 as test'))
            row = result.fetchone()
            if row and row[0] == 1:
                print('✅ 数据库连接成功！')
                print()
                
                # 4. 检查数据库版本
                if settings.DATABASE_TYPE == 'postgresql':
                    version_result = await db.execute(text('SELECT version()'))
                    version = version_result.fetchone()[0]
                    print(f'📊 PostgreSQL 版本:')
                    print(f'   {version.split(",")[0]}')
                elif settings.DATABASE_TYPE == 'mysql':
                    version_result = await db.execute(text('SELECT VERSION()'))
                    version = version_result.fetchone()[0]
                    print(f'📊 MySQL 版本: {version}')
                
                print()
                print('=' * 60)
                print('✅ 数据库配置正确，可以继续初始化')
                print('=' * 60)
                return True
            else:
                print('❌ 数据库连接测试失败')
                return False
                
    except ModuleNotFoundError as e:
        print(f'❌ 缺少依赖模块: {e}')
        print()
        print('请安装依赖:')
        print('  pip install -r ../../requirements.txt')
        return False
        
    except Exception as e:
        print(f'❌ 数据库连接失败: {e}')
        print()
        print('可能的原因：')
        print('  1. 数据库服务未启动')
        print('  2. 数据库配置错误（主机、端口、用户名、密码）')
        print('  3. 数据库不存在（需要先创建数据库）')
        print('  4. 防火墙阻止连接')
        print()
        print('创建数据库命令（PostgreSQL）：')
        print('  psql -U postgres -c "CREATE DATABASE your_database_name;"')
        print()
        print('创建数据库命令（MySQL）：')
        print('  mysql -u root -p -e "CREATE DATABASE your_database_name;"')
        return False


if __name__ == '__main__':
    try:
        success = asyncio.run(test_connection())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print('\n\n⚠️  测试被用户中断')
        sys.exit(1)
    except Exception as e:
        print(f'\n❌ 发生未预期的错误: {e}')
        import traceback
        traceback.print_exc()
        sys.exit(1)

