#!/usr/bin/env python3
"""
数据库环境准备脚本
自动完成：创建数据库、安装 pgvector 扩展、配置 Redis
"""
import sys
import io
import asyncpg
import asyncio
from dotenv import load_dotenv
import os

# Windows 平台 UTF-8 输出支持
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 加载 .env 文件
load_dotenv()


async def create_database_if_not_exists():
    """创建数据库（如果不存在）"""
    host = os.getenv('DATABASE_HOST', 'localhost')
    port = int(os.getenv('DATABASE_PORT', '5432'))
    user = os.getenv('DATABASE_USER', 'postgres')
    password = os.getenv('DATABASE_PASSWORD', '')
    db_name = os.getenv('DATABASE_SCHEMA', 'userecho')
    
    print(f'📦 检查数据库是否存在...')
    
    try:
        # 连接到 postgres 默认数据库
        conn = await asyncpg.connect(
            host=host, port=port, user=user, password=password, database='postgres'
        )
        
        # 检查数据库是否存在
        existing = await conn.fetchval(
            'SELECT 1 FROM pg_database WHERE datname = $1', db_name
        )
        
        if existing:
            print(f'   ✅ 数据库 {db_name} 已存在')
        else:
            await conn.execute(f'CREATE DATABASE "{db_name}"')
            print(f'   ✅ 数据库 {db_name} 创建成功')
        
        await conn.close()
        return True
    except Exception as e:
        print(f'   ❌ 数据库检查/创建失败: {e}')
        return False


async def install_pgvector():
    """安装 pgvector 扩展"""
    host = os.getenv('DATABASE_HOST', 'localhost')
    port = int(os.getenv('DATABASE_PORT', '5432'))
    user = os.getenv('DATABASE_USER', 'postgres')
    password = os.getenv('DATABASE_PASSWORD', '')
    db_name = os.getenv('DATABASE_SCHEMA', 'userecho')
    
    print(f'🔌 检查 pgvector 扩展...')
    
    try:
        conn = await asyncpg.connect(
            host=host, port=port, user=user, password=password, database=db_name
        )
        
        # 检查扩展是否已安装
        existing = await conn.fetchval(
            'SELECT 1 FROM pg_extension WHERE extname = $1', 'vector'
        )
        
        if existing:
            version = await conn.fetchval(
                'SELECT extversion FROM pg_extension WHERE extname = $1', 'vector'
            )
            print(f'   ✅ pgvector 扩展已安装 (版本: {version})')
        else:
            await conn.execute('CREATE EXTENSION IF NOT EXISTS vector')
            version = await conn.fetchval(
                'SELECT extversion FROM pg_extension WHERE extname = $1', 'vector'
            )
            print(f'   ✅ pgvector 扩展安装成功 (版本: {version})')
        
        await conn.close()
        return True
    except Exception as e:
        print(f'   ❌ pgvector 扩展安装失败: {e}')
        print()
        print('   可能的原因：')
        print('   1. PostgreSQL 服务器未安装 pgvector 扩展包')
        print('   2. 当前用户没有 CREATE EXTENSION 权限')
        return False


def configure_redis():
    """配置 Redis"""
    print(f'🔧 检查 Redis 配置...')
    
    # 检查 REDIS_URL 是否已配置
    redis_url = os.getenv('REDIS_URL', '').strip()
    if redis_url and not redis_url.startswith('#'):
        print(f'   ✅ Redis 已配置（使用 REDIS_URL）')
        return True
    
    # 检查本地 Redis 是否可用
    try:
        import redis
        host = os.getenv('REDIS_HOST', 'localhost')
        port = int(os.getenv('REDIS_PORT', '6379'))
        password = os.getenv('REDIS_PASSWORD', '')
        
        r = redis.Redis(
            host=host,
            port=port,
            password=password if password else None,
            socket_connect_timeout=2
        )
        r.ping()
        print(f'   ✅ 本地 Redis 可用 ({host}:{port})')
        return True
    except:
        print(f'   ⚠️  本地 Redis 不可用')
        
        # 检查是否有 Upstash Redis URL（注释状态）
        env_file = '.env'
        if os.path.exists(env_file):
            with open(env_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            has_upstash = False
            for line in lines:
                if line.strip().startswith('# REDIS_URL='):
                    has_upstash = True
                    break
            
            if has_upstash:
                print(f'   ℹ️  检测到 Upstash Redis 配置')
                print(f'   ℹ️  正在切换到 Upstash Redis...')
                
                # 修改配置
                new_lines = []
                for line in lines:
                    # 注释本地 Redis 配置
                    if line.strip().startswith('REDIS_HOST='):
                        new_lines.append(f'# {line}')
                    # 启用 Upstash Redis URL
                    elif line.strip().startswith('# REDIS_URL='):
                        new_lines.append(line[2:])  # 移除前面的 '#'
                    else:
                        new_lines.append(line)
                
                with open(env_file, 'w', encoding='utf-8') as f:
                    f.writelines(new_lines)
                
                print(f'   ✅ 已切换到 Upstash Redis')
                return True
            else:
                print(f'   ⚠️  未找到可用的 Redis 配置')
                print(f'   ⚠️  继续执行可能会失败，建议配置 Redis')
                return False
        
        return False


async def main():
    """主函数"""
    print('=' * 80)
    print('🔧 数据库环境准备')
    print('=' * 80)
    print()
    
    success = True
    
    # 1. 创建数据库
    if not await create_database_if_not_exists():
        success = False
    print()
    
    # 2. 安装 pgvector 扩展
    if not await install_pgvector():
        success = False
    print()
    
    # 3. 配置 Redis
    if not configure_redis():
        # Redis 配置失败不影响整体流程（fba init 会再次检查）
        pass
    print()
    
    if success:
        print('=' * 80)
        print('✅ 数据库环境准备完成')
        print('=' * 80)
        return 0
    else:
        print('=' * 80)
        print('❌ 数据库环境准备失败')
        print('=' * 80)
        return 1


if __name__ == '__main__':
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

