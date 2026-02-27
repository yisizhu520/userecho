#!/bin/bash

# Celery Worker 配置验证脚本
# 用于检查 Dokploy/Docker 环境中的 worker 配置是否正确

echo "=========================================="
echo "Celery Worker 配置验证"
echo "=========================================="
echo ""

# 1. 检查当前 worker 进程
echo "1️⃣  检查 Worker 进程..."
ps aux | grep -v grep | grep "celery.*worker" | while read line; do
    echo "   进程: $line"
    
    # 检查是否使用了正确的 pool
    if echo "$line" | grep -q "\-P custom"; then
        echo "   ✅ Pool 类型: custom (AsyncIOPool)"
    elif echo "$line" | grep -q "\-P gevent"; then
        echo "   ❌ Pool 类型: gevent (不支持 async def!)"
    else
        echo "   ⚠️  Pool 类型: 未指定 (默认 prefork)"
    fi
    
    # 检查并发数
    concurrency=$(echo "$line" | grep -oP '\-c\s+\K\d+' || echo "未指定")
    echo "   并发数: $concurrency"
done
echo ""

# 2. 检查环境变量
echo "2️⃣  检查环境变量..."
if [ -n "$CELERY_CUSTOM_WORKER_POOL" ]; then
    echo "   ✅ CELERY_CUSTOM_WORKER_POOL=$CELERY_CUSTOM_WORKER_POOL"
else
    echo "   ❌ CELERY_CUSTOM_WORKER_POOL 未设置"
    echo "      这将导致 -P custom 无法工作！"
fi
echo ""

# 3. 检查 celery-aio-pool 是否安装
echo "3️⃣  检查依赖安装..."
if python -c "import celery_aio_pool; print(f'   ✅ celery-aio-pool 版本: {celery_aio_pool.__version__}')" 2>/dev/null; then
    :
else
    echo "   ❌ celery-aio-pool 未安装"
    echo "      请运行: pip install celery-aio-pool"
fi
echo ""

# 4. 检查 Redis 连接
echo "4️⃣  检查 Redis 连接..."
if python -c "
from backend.core.conf import settings
import redis
try:
    r = redis.from_url(f'redis://:{settings.REDIS_PASSWORD}@{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.CELERY_BROKER_REDIS_DATABASE}')
    r.ping()
    print('   ✅ Redis 连接成功')
    print(f'   Database: {settings.CELERY_BROKER_REDIS_DATABASE}')
except Exception as e:
    print(f'   ❌ Redis 连接失败: {e}')
" 2>/dev/null; then
    :
else
    echo "   ⚠️  无法验证 Redis 连接（可能是环境问题）"
fi
echo ""

# 5. 检查 supervisord 配置
echo "5️⃣  检查 Supervisord 配置..."
if [ -f "/etc/supervisor/conf.d/fba_celery_worker.conf" ]; then
    echo "   配置文件: /etc/supervisor/conf.d/fba_celery_worker.conf"
    grep "command=" /etc/supervisor/conf.d/fba_celery_worker.conf | while read line; do
        echo "   $line"
        if echo "$line" | grep -q "\-P custom"; then
            echo "   ✅ 配置使用 AsyncIOPool"
        elif echo "$line" | grep -q "\-P gevent"; then
            echo "   ❌ 配置仍使用 gevent，需要更新！"
        fi
    done
    
    # 检查环境变量配置
    if grep -q "CELERY_CUSTOM_WORKER_POOL" /etc/supervisor/conf.d/fba_celery_worker.conf; then
        echo "   ✅ 环境变量已配置"
    else
        echo "   ❌ 缺少 environment 配置行"
    fi
elif [ -f "/etc/supervisord.conf" ]; then
    echo "   配置文件: /etc/supervisord.conf"
    grep "fba_celery_worker" -A 5 /etc/supervisord.conf
else
    echo "   ⚠️  未找到 supervisord 配置文件"
fi
echo ""

# 6. 建议
echo "=========================================="
echo "📋 配置修复建议："
echo "=========================================="

needs_fix=false

# 检查是否需要修复
if ps aux | grep -v grep | grep "celery.*worker" | grep -q "\-P gevent"; then
    needs_fix=true
    echo ""
    echo "⚠️  发现使用 gevent pool 的 worker 进程！"
    echo ""
    echo "修复步骤："
    echo "  1. 更新配置文件，将 '-P gevent' 改为 '-P custom'"
    echo "  2. 添加环境变量: environment=CELERY_CUSTOM_WORKER_POOL=\"celery_aio_pool.pool:AsyncIOPool\""
    echo "  3. 降低并发数: -c 4 或 -c 8（从原来的 50/1000）"
    echo "  4. 重启 worker:"
    echo "     supervisorctl restart fba_celery_worker"
    echo ""
fi

if [ "$CELERY_CUSTOM_WORKER_POOL" = "" ]; then
    needs_fix=true
    echo ""
    echo "⚠️  环境变量 CELERY_CUSTOM_WORKER_POOL 未设置！"
    echo ""
    echo "在 supervisord.conf 中添加："
    echo "  environment=CELERY_CUSTOM_WORKER_POOL=\"celery_aio_pool.pool:AsyncIOPool\""
    echo ""
fi

if ! $needs_fix; then
    echo ""
    echo "✅ 配置看起来正确！"
    echo ""
    echo "如果任务仍然不被消费，检查："
    echo "  1. Worker 日志中是否有 'Worker READY' 消息"
    echo "  2. 发送任务时是否出现在 Redis 队列中"
    echo "  3. Redis database 配置是否一致"
    echo ""
fi

echo "=========================================="
