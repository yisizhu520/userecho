#!/bin/bash

# 快速修复：清除 Celery 环境变量冲突
# 适用于容器内临时修复

echo "=========================================="
echo "Celery Broker URL 快速修复"
echo "=========================================="
echo ""

# 检查当前环境变量
echo "当前环境变量状态:"
echo "  CELERY_BROKER_URL: ${CELERY_BROKER_URL:-<未设置>}"
echo "  CELERY_RESULT_BACKEND: ${CELERY_RESULT_BACKEND:-<未设置>}"
echo ""

# 检查是否有问题
HAS_ISSUE=false

if [ -n "$CELERY_BROKER_URL" ]; then
    if [[ "$CELERY_BROKER_URL" == amqp://* ]]; then
        echo "❌ 检测到问题: CELERY_BROKER_URL 指向 RabbitMQ"
        HAS_ISSUE=true
    elif [[ "$CELERY_BROKER_URL" != redis://* ]]; then
        echo "⚠️  警告: CELERY_BROKER_URL 值不符合预期"
        HAS_ISSUE=true
    fi
fi

if [ "$HAS_ISSUE" = true ]; then
    echo ""
    echo "正在修复..."
    echo ""
    
    # 清除环境变量
    if [ -n "$CELERY_BROKER_URL" ]; then
        echo "✓ 删除 CELERY_BROKER_URL"
        unset CELERY_BROKER_URL
    fi
    
    if [ -n "$CELERY_RESULT_BACKEND" ]; then
        echo "✓ 删除 CELERY_RESULT_BACKEND"
        unset CELERY_RESULT_BACKEND
    fi
    
    # 验证必要的环境变量
    echo ""
    echo "验证必要的环境变量:"
    echo "  CELERY_BROKER: ${CELERY_BROKER:-<未设置>}"
    echo "  REDIS_HOST: ${REDIS_HOST:-<未设置>}"
    echo "  REDIS_PORT: ${REDIS_PORT:-<未设置>}"
    echo "  CELERY_BROKER_REDIS_DATABASE: ${CELERY_BROKER_REDIS_DATABASE:-<未设置>}"
    
    if [ "$CELERY_BROKER" != "redis" ]; then
        echo ""
        echo "⚠️  警告: CELERY_BROKER 应该设置为 'redis'"
        echo "   当前值: $CELERY_BROKER"
    fi
    
    # 重启 worker
    echo ""
    echo "重启 Celery Worker..."
    if command -v supervisorctl > /dev/null; then
        supervisorctl restart fba_celery_worker
        echo "✅ Worker 已重启"
        echo ""
        echo "查看日志:"
        echo "  supervisorctl tail -f fba_celery_worker stdout"
    else
        echo "⚠️  supervisorctl 未找到，请手动重启 worker"
    fi
    
    echo ""
    echo "=========================================="
    echo "修复完成！"
    echo "=========================================="
    echo ""
    echo "注意: 这是临时修复。要永久解决问题，请:"
    echo "  1. 在 Dokploy 平台删除 CELERY_BROKER_URL 环境变量"
    echo "  2. 确保只设置 CELERY_BROKER=redis 和 Redis 连接参数"
    echo "  3. 重新部署项目"
    echo ""
    
else
    echo "✅ 未检测到问题，配置看起来正常"
    echo ""
    echo "如果 Worker 仍然无法工作，请检查:"
    echo "  1. Redis 连接是否正常"
    echo "  2. Worker pool 类型是否为 AsyncIOPool"
    echo "  3. 运行 bash diagnose_broker.sh 获取详细诊断"
    echo ""
fi

echo "=========================================="
