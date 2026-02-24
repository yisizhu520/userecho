#!/bin/bash
# Demo 模式启动脚本
# 使用 .env.demo 配置启动后端服务

# 获取脚本所在目录的绝对路径
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "📂 工作目录: $SCRIPT_DIR"

# 使用虚拟环境的 Python（直接使用可执行文件，无需 activate）
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

# 验证 uvicorn 是否安装
if ! "$VENV_PYTHON" -c "import uvicorn" 2>/dev/null; then
    echo "❌ uvicorn 未安装"
    echo "请先运行: cd server && uv sync"
    exit 1
fi

echo "✅ uvicorn 已安装"
echo ""
echo "🚀 启动 Demo 模式后端服务..."
echo "-----------------------------------"
echo ""

# 切换到 backend 目录（run.py 要求在 backend 目录下运行）
cd "$SCRIPT_DIR/backend"

# 使用 .env.demo 配置启动服务（直接使用虚拟环境的 Python）
ENV_FILE=.env.demo "$VENV_PYTHON" run.py
