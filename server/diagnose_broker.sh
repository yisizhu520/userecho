#!/bin/bash

# Celery Broker URL 诊断脚本
# 用于排查为什么 Celery 连接到错误的 broker

echo "=========================================="
echo "Celery Broker URL 诊断"
echo "=========================================="
echo ""

echo "1️⃣  检查环境变量..."
echo "   CELERY_BROKER_URL: ${CELERY_BROKER_URL:-<未设置>}"
echo "   CELERY_RESULT_BACKEND: ${CELERY_RESULT_BACKEND:-<未设置>}"
echo "   CELERY_BROKER: ${CELERY_BROKER:-<未设置>}"
echo "   REDIS_HOST: ${REDIS_HOST:-<未设置>}"
echo "   REDIS_PORT: ${REDIS_PORT:-<未设置>}"
echo "   REDIS_PASSWORD: ${REDIS_PASSWORD:+<已设置>}"
echo "   CELERY_BROKER_REDIS_DATABASE: ${CELERY_BROKER_REDIS_DATABASE:-<未设置>}"
echo ""

if [ -n "$CELERY_BROKER_URL" ]; then
    echo "⚠️  警告: CELERY_BROKER_URL 已设置!"
    echo "   值: $CELERY_BROKER_URL"
    echo ""
    
    if [[ "$CELERY_BROKER_URL" == amqp://* ]]; then
        echo "❌ 错误: 这是 RabbitMQ URL (amqp://)"
        echo "   应该使用 Redis URL (redis://)"
        echo ""
        echo "解决方案 1: 删除环境变量"
        echo "   unset CELERY_BROKER_URL"
        echo ""
        echo "解决方案 2: 在 Dokploy 面板中删除此环境变量"
        echo "   1. 进入 Dokploy 项目设置"
        echo "   2. 找到 Environment Variables"
        echo "   3. 删除 CELERY_BROKER_URL 变量"
        echo "   4. 重新部署"
        echo ""
    elif [[ "$CELERY_BROKER_URL" == redis://* ]]; then
        echo "✅ 这是正确的 Redis URL"
    fi
fi

echo "2️⃣  检查进程环境变量..."
if pgrep -f "celery.*worker" > /dev/null; then
    CELERY_PID=$(pgrep -f "celery.*worker" | head -1)
    echo "   Worker PID: $CELERY_PID"
    
    # 检查进程的环境变量
    if [ -f "/proc/$CELERY_PID/environ" ]; then
        echo ""
        echo "   进程环境变量中的 CELERY 相关配置:"
        cat "/proc/$CELERY_PID/environ" | tr '\0' '\n' | grep -E "CELERY|REDIS|RABBITMQ" || echo "   (无)"
    fi
else
    echo "   ⚠️  Worker 进程未运行"
fi

echo ""
echo "3️⃣  推荐的配置方式..."
echo ""
echo "正确的环境变量配置:"
echo ""
echo "# 在 docker-compose.yml 或 Dokploy 环境变量中设置:"
echo "CELERY_BROKER=redis"
echo "REDIS_HOST=<你的Redis主机>"
echo "REDIS_PORT=6379"
echo "REDIS_PASSWORD=<你的密码>"
echo "CELERY_BROKER_REDIS_DATABASE=1"
echo ""
echo "# 不要设置这些（让代码自动构造）:"
echo "# CELERY_BROKER_URL=<不要设置>"
echo "# CELERY_RESULT_BACKEND=<不要设置>"
echo ""

echo "=========================================="
echo "4️⃣  如何修复..."
echo "=========================================="
echo ""
echo "如果发现 CELERY_BROKER_URL 指向 RabbitMQ:"
echo ""
echo "方法 1: 临时修复（容器内）"
echo "  unset CELERY_BROKER_URL"
echo "  unset CELERY_RESULT_BACKEND"
echo "  supervisorctl restart fba_celery_worker"
echo ""
echo "方法 2: 永久修复（Dokploy 平台）"
echo "  1. 登录 Dokploy 管理面板"
echo "  2. 进入项目 > Settings > Environment Variables"
echo "  3. 删除 CELERY_BROKER_URL 和 CELERY_RESULT_BACKEND"
echo "  4. 确保保留:"
echo "     - CELERY_BROKER=redis"
echo "     - REDIS_HOST=<主机>"
echo "     - REDIS_PORT=6379"
echo "     - CELERY_BROKER_REDIS_DATABASE=1"
echo "  5. 重新部署项目"
echo ""

echo "=========================================="
