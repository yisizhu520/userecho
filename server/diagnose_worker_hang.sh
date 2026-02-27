#!/bin/bash
# Celery Worker 深度诊断脚本
# 用于排查 worker 进程运行但无日志输出的问题

echo "=========================================="
echo "Celery Worker 深度诊断"
echo "=========================================="
echo ""

# 测试 1: 检查 Python 和模块导入
echo "1️⃣  测试 Python 环境和模块导入..."
/fba/.venv/bin/python -c "
import sys
print('Python 版本:', sys.version)
print('开始导入 celery...')
import celery
print('✅ celery 导入成功，版本:', celery.__version__)
print('开始导入 backend.app.task.celery...')
from backend.app.task.celery import celery_app
print('✅ celery_app 导入成功')
print('Broker URL:', celery_app.conf.broker_url)
print('Result Backend:', celery_app.conf.result_backend)
"
if [ $? -ne 0 ]; then
    echo "❌ 模块导入失败！"
    exit 1
fi
echo ""

# 测试 2: 检查 Redis 连接
echo "2️⃣  测试 Redis 连接..."
/fba/.venv/bin/python -c "
import redis
import os

redis_host = os.getenv('REDIS_HOST', 'localhost')
redis_port = int(os.getenv('REDIS_PORT', '6379'))
redis_password = os.getenv('REDIS_PASSWORD', '')

print(f'连接到 Redis: {redis_host}:{redis_port}')
r = redis.Redis(host=redis_host, port=redis_port, password=redis_password, db=1, socket_connect_timeout=5)
r.ping()
print('✅ Redis 连接成功')

# 检查 broker 键
keys = r.keys('celery*')
print(f'找到 {len(keys)} 个 celery 相关的键')
"
if [ $? -ne 0 ]; then
    echo "❌ Redis 连接失败！"
    exit 1
fi
echo ""

# 测试 3: 检查数据库连接
echo "3️⃣  测试数据库连接（result_backend）..."
/fba/.venv/bin/python -c "
import psycopg
import os

db_host = os.getenv('DATABASE_HOST', 'localhost')
db_port = int(os.getenv('DATABASE_PORT', '5432'))
db_user = os.getenv('DATABASE_USER', 'postgres')
db_password = os.getenv('DATABASE_PASSWORD', '')
db_name = os.getenv('DATABASE_SCHEMA', 'postgres')

print(f'连接到数据库: {db_host}:{db_port}/{db_name}')
conn = psycopg.connect(
    host=db_host,
    port=db_port,
    user=db_user,
    password=db_password,
    dbname=db_name,
    connect_timeout=10
)
print('✅ 数据库连接成功')
conn.close()
"
if [ $? -ne 0 ]; then
    echo "❌ 数据库连接失败！"
    exit 1
fi
echo ""

# 测试 4: 尝试启动 worker (前台运行，10秒后自动退出)
echo "4️⃣  尝试启动 worker (前台运行 10 秒)..."
echo "如果这里卡住，说明 worker 启动时挂起了"
timeout 10 /fba/.venv/bin/python -m celery -A backend.app.task.celery worker --loglevel=DEBUG -P threads -c 1 &
WORKER_PID=$!
sleep 2

# 检查进程是否还在运行
if ps -p $WORKER_PID > /dev/null 2>&1; then
    echo "⏸️  Worker 进程正在运行 (PID: $WORKER_PID)"
    echo "等待 8 秒查看输出..."
    wait $WORKER_PID
else
    echo "❌ Worker 进程已退出"
    wait $WORKER_PID
    exit 1
fi

echo ""
echo "=========================================="
echo "诊断完成"
echo "=========================================="
