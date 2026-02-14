#!/usr/bin/env bash

# ================================================================
# 全文搜索索引安装脚本
# ================================================================
# 功能：为反馈表添加 pg_trgm 全文搜索索引
# 性能：关键词搜索提升 10-20 倍
# 时间：< 1 分钟（小数据量），1-5 分钟（大数据量）
# ================================================================

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================================================${NC}"
echo -e "${BLUE}   全文搜索索引安装程序${NC}"
echo -e "${BLUE}================================================================${NC}"
echo ""

# 检查是否在正确的目录（server 或 backend）
if [ -f "backend/alembic.ini" ]; then
    # 在 server 目录，需要进入 backend
    echo -e "${BLUE}🔧 进入 backend 目录...${NC}"
    cd backend
elif [ ! -f "alembic.ini" ]; then
    # 既不在 server 也不在 backend
    echo -e "${RED}❌ 错误：请在 server 或 backend 目录下运行此脚本${NC}"
    echo -e "${YELLOW}   cd server && bash scripts/install_fulltext_index.sh${NC}"
    echo -e "${YELLOW}   或${NC}"
    echo -e "${YELLOW}   cd server/backend && bash ../scripts/install_fulltext_index.sh${NC}"
    exit 1
fi

# 检查虚拟环境（在 server 目录）
if [ ! -d "../.venv" ] && [ ! -d ".venv" ]; then
    echo -e "${RED}❌ 错误：虚拟环境不存在${NC}"
    echo -e "${YELLOW}   请先创建虚拟环境：cd server && python -m venv .venv${NC}"
    exit 1
fi

# 激活虚拟环境
echo -e "${BLUE}🔧 激活虚拟环境...${NC}"
if [ -f "../.venv/Scripts/activate" ]; then
    # Windows Git Bash (从 backend 目录)
    source ../.venv/Scripts/activate
elif [ -f "../.venv/bin/activate" ]; then
    # Linux/Mac (从 backend 目录)
    source ../.venv/bin/activate
elif [ -f ".venv/Scripts/activate" ]; then
    # Windows Git Bash (从 server 目录)
    source .venv/Scripts/activate
elif [ -f ".venv/bin/activate" ]; then
    # Linux/Mac (从 server 目录)
    source .venv/bin/activate
else
    echo -e "${RED}❌ 错误：无法激活虚拟环境${NC}"
    exit 1
fi

echo -e "${GREEN}✅ 虚拟环境已激活${NC}"
echo ""

# 检查数据库连接
echo -e "${BLUE}🔍 检查数据库连接...${NC}"
python -c "
from sqlalchemy import text
from backend.database.db import async_engine
import asyncio

async def test_connection():
    async with async_engine.begin() as conn:
        result = await conn.execute(text('SELECT 1'))
        return result.scalar()

try:
    result = asyncio.run(test_connection())
    print('✅ 数据库连接成功')
except Exception as e:
    print(f'❌ 数据库连接失败: {e}')
    exit(1)
"

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ 数据库连接失败，请检查配置${NC}"
    exit 1
fi

echo ""

# 询问用户确认
echo -e "${YELLOW}⚠️  准备执行数据库迁移，将创建以下索引：${NC}"
echo -e "   - ${GREEN}idx_feedbacks_content_gin${NC}    (content 字段全文索引)"
echo -e "   - ${GREEN}idx_feedbacks_ai_summary_gin${NC} (ai_summary 字段全文索引)"
echo ""
echo -e "${YELLOW}📊 预计时间：${NC}"
echo -e "   - 小数据量（< 1,000 条）：  5-10 秒"
echo -e "   - 中等数据量（1,000-10,000）：10-30 秒"
echo -e "   - 大数据量（> 10,000 条）：  1-5 分钟"
echo ""

read -p "$(echo -e ${YELLOW}是否继续？[y/N]: ${NC})" -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}⏸️  已取消安装${NC}"
    exit 0
fi

echo ""

# 执行迁移
echo -e "${BLUE}🚀 执行数据库迁移...${NC}"
echo ""

alembic upgrade head

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}================================================================${NC}"
    echo -e "${GREEN}✅ 全文搜索索引安装成功！${NC}"
    echo -e "${GREEN}================================================================${NC}"
    echo ""
    echo -e "${BLUE}📊 已创建索引：${NC}"
    echo -e "   - idx_feedbacks_content_gin"
    echo -e "   - idx_feedbacks_ai_summary_gin"
    echo ""
    echo -e "${BLUE}🚀 性能提升：${NC}"
    echo -e "   - 关键词搜索速度提升 ${GREEN}10-20 倍${NC}"
    echo -e "   - ILIKE 查询优化为索引扫描"
    echo ""
    echo -e "${BLUE}📖 验证方法：${NC}"
    echo -e "   1. 打开前端反馈列表页面"
    echo -e "   2. 输入搜索关键词（例如：登录）"
    echo -e "   3. 查看 Network 面板，响应时间应 < 100ms"
    echo ""
    echo -e "${BLUE}📚 详细文档：${NC}"
    echo -e "   docs/development/fulltext-search-index-guide.md"
    echo ""
else
    echo ""
    echo -e "${RED}================================================================${NC}"
    echo -e "${RED}❌ 索引安装失败${NC}"
    echo -e "${RED}================================================================${NC}"
    echo ""
    echo -e "${YELLOW}🔍 可能的原因：${NC}"
    echo -e "   1. 数据库不是 PostgreSQL（不支持 pg_trgm）"
    echo -e "   2. 数据库权限不足（无法创建扩展或索引）"
    echo -e "   3. 迁移版本冲突（请检查 alembic_version 表）"
    echo ""
    echo -e "${YELLOW}📖 解决方案：${NC}"
    echo -e "   查看详细文档：docs/development/fulltext-search-index-guide.md"
    echo ""
    exit 1
fi
