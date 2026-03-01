#!/bin/bash
# Celery Worker Demo 模式启动脚本
# 使用 .env.demo 配置启动 Celery worker

# 获取脚本所在目录的绝对路径
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "📂 工作目录: $SCRIPT_DIR"

# 使用虚拟环境的 Python
VENV_PYTHON="$SCRIPT_DIR/.venv/Scripts/python.exe"

# 检查虚拟环境 Python 是否存在
if [ ! -f "$VENV_PYTHON" ]; then
    echo "❌ 虚拟环境不存在: $VENV_PYTHON"
    echo "请先运行: cd server && uv sync"
    exit 1
fi

echo "✅ 找到虚拟环境 Python: $VENV_PYTHON"

# 检查 .env.demo 文件是否存在
if [ ! -f "$SCRIPT_DIR/backend/.env.demo" ]; then
    echo "❌ 找不到 backend/.env.demo 文件"
    exit 1
fi

echo "✅ 找到 .env.demo 配置文件"

# 验证 celery 是否安装
if ! "$VENV_PYTHON" -m celery --version >/dev/null 2>&1; then
    echo "❌ celery 未安装"
    echo "请先运行: cd server && uv sync"
    exit 1
fi

echo "✅ celery 已安装"
echo ""
echo "🚀 启动 Demo 模式 Celery Worker..."
echo "-----------------------------------"
echo "环境文件: .env.demo"
echo ""

# 切换到 backend 目录
cd "$SCRIPT_DIR/backend"

# 导出环境变量，让 settings 加载 .env.demo
export ENV_FILE=.env.demo

# 启动 Celery worker
# 参数说明:
#   -A: 指定 Celery 实例
#   worker: 启动 worker 角色
#   -P threads: 使用线程池（兼容 asyncio）
#   -c 4: 并发数
#   -l info: 日志级别
#   --without-gossip --without-mingle: 减少网络开销
"$VENV_PYTHON" -m celery -A backend.app.task.celery:celery_app worker \
  -P threads \
  -c 4 \
  -l info \
  --without-gossip \
  --without-mingle
