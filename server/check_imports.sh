#!/bin/bash
# 检查 Python 模块导入错误的便捷脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=========================================="
echo "检查 Python 导入错误"
echo "=========================================="
echo

# 目标路径（默认检查 backend/app/batch）
TARGET_PATH="${1:-backend/app/batch}"

echo "[*] 目标路径: $TARGET_PATH"
echo

# 方法 1: 使用 Python 编译检查
echo "[1/3] 使用 Python 编译检查..."
echo "----------------------------------------"

ERROR_COUNT=0
SUCCESS_COUNT=0

while IFS= read -r -d '' file; do
    # 跳过 __pycache__ 和 alembic
    if [[ "$file" == *"__pycache__"* ]] || [[ "$file" == *"alembic/versions"* ]]; then
        continue
    fi
    
    # 尝试编译文件
    if .venv/Scripts/python.exe -m py_compile "$file" 2>/dev/null; then
        echo -e "${GREEN}[OK]${NC} $file"
        ((SUCCESS_COUNT++))
    else
        echo -e "${RED}[FAIL]${NC} $file"
        .venv/Scripts/python.exe -m py_compile "$file" 2>&1 | grep -E "SyntaxError|ModuleNotFoundError|ImportError" || true
        ((ERROR_COUNT++))
    fi
done < <(find "$TARGET_PATH" -name "*.py" -print0)

echo
echo "编译检查: 成功 $SUCCESS_COUNT, 失败 $ERROR_COUNT"
echo

# 方法 2: 使用 mypy 检查（可选）
if command -v .venv/Scripts/python.exe -m mypy &> /dev/null; then
    echo "[2/3] 使用 mypy 类型检查..."
    echo "----------------------------------------"
    .venv/Scripts/python.exe -m mypy "$TARGET_PATH" --no-error-summary 2>&1 | head -20 || true
    echo
fi

# 方法 3: 使用 ruff 检查（可选）
if [ -f ".venv/Scripts/python.exe" ]; then
    echo "[3/3] 使用 ruff 检查..."
    echo "----------------------------------------"
    .venv/Scripts/python.exe -m ruff check "$TARGET_PATH" --select F401,F403,F405,E999 2>&1 | head -20 || true
    echo
fi

echo "=========================================="
if [ $ERROR_COUNT -eq 0 ]; then
    echo -e "${GREEN}✓ 所有文件检查通过!${NC}"
else
    echo -e "${RED}✗ 发现 $ERROR_COUNT 个文件有错误${NC}"
    echo
    echo "修复提示:"
    echo "  1. 检查导入路径是否正确"
    echo "  2. 使用 grep 查找正确的导入:"
    echo "     grep -r 'from.*import XXX' backend/"
    echo "  3. 参考其他文件的导入方式"
fi
echo "=========================================="

exit $ERROR_COUNT
