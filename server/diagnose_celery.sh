#!/bin/bash

# Celery Worker 诊断脚本
# 帮助排查为什么看不到 Worker READY 日志

echo "=========================================="
echo "Celery Worker 诊断工具"
echo "=========================================="
echo ""

# 1. 检查 Redis 连接
echo "1️⃣  检查 Redis 连接..."
if command -v redis-cli &> /dev/null; then
    if redis-cli -h ${REDIS_HOST:-localhost} -p ${REDIS_PORT:-6379} -a "${REDIS_PASSWORD}" ping &> /dev/null; then
        echo "   ✅ Redis 连接成功"
    else
        echo "   ❌ Redis 连接失败"
        echo "      请检查 REDIS_HOST, REDIS_PORT, REDIS_PASSWORD"
    fi
else
    echo "   ⚠️  redis-cli 未安装，跳过检查"
fi
echo ""

# 2. 检查进程是否运行
echo "2️⃣  检查 Celery Worker 进程..."
if ps aux | grep -v grep | grep "celery.*worker" > /dev/null; then
    echo "   ✅ 发现 Celery Worker 进程:"
    ps aux | grep -v grep | grep "celery.*worker" | head -5
else
    echo "   ❌ 未发现 Celery Worker 进程"
    echo "      Worker 可能没有启动"
fi
echo ""

# 3. 检查 supervisord 状态（如果使用）
echo "3️⃣  检查 Supervisord 状态..."
if command -v supervisorctl &> /dev/null; then
    echo "   Supervisord 进程状态:"
    supervisorctl status | grep celery || echo "   ⚠️  未找到 celery 相关进程"
else
    echo "   ⚠️  supervisorctl 未安装，跳过检查"
fi
echo ""

# 4. 检查 Python 环境
echo "4️⃣  检查 Python 环境..."
if [ -f ".venv/Scripts/python.exe" ] || [ -f ".venv/bin/python" ]; then
    PYTHON_PATH=$(if [ -f ".venv/Scripts/python.exe" ]; then echo ".venv/Scripts/python.exe"; else echo ".venv/bin/python"; fi)
    echo "   ✅ 虚拟环境: $PYTHON_PATH"
    
    # 检查 celery 是否安装
    if $PYTHON_PATH -c "import celery; print(f'   ✅ Celery 版本: {celery.__version__}')" 2>/dev/null; then
        :
    else
        echo "   ❌ Celery 未安装或导入失败"
    fi
else
    echo "   ❌ 虚拟环境不存在"
fi
echo ""

# 5. 测试信号处理器
echo "5️⃣  测试信号处理器注册..."
if [ -f "verify_signals.py" ]; then
    echo "   运行 verify_signals.py..."
    $PYTHON_PATH verify_signals.py 2>&1 | grep -E "\[Celery (Init|Signals)\]" | tail -5
    echo "   （如果上面看到信号注册日志，说明代码没问题）"
else
    echo "   ⚠️  verify_signals.py 不存在"
fi
echo ""

# 6. 建议
echo "=========================================="
echo "📋 建议的下一步操作："
echo "=========================================="
echo ""
echo "如果你使用的是 Docker/Supervisord："
echo "  1. 重启容器/supervisord:"
echo "     supervisorctl restart fba_celery_worker"
echo "     或"
echo "     docker-compose restart celery_worker"
echo ""
echo "  2. 查看实时日志:"
echo "     supervisorctl tail -f fba_celery_worker"
echo "     或"
echo "     docker-compose logs -f celery_worker"
echo ""
echo "如果你手动启动 Worker:"
echo "  1. 确保在正确的目录:"
echo "     cd server"
echo ""
echo "  2. 激活虚拟环境:"
echo "     source .venv/bin/activate  # Linux/Mac"
echo "     .venv\\Scripts\\Activate.ps1  # Windows PowerShell"
echo ""
echo "  3. 启动 worker (使用 debug 级别):"
echo "     python -m celery -A backend.app.task.celery:celery_app worker -P custom -c 4 -l debug"
echo ""
echo "=========================================="
