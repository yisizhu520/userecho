#!/usr/bin/env python3
"""
全文搜索索引验证脚本

功能：
1. 检查 pg_trgm 扩展是否启用
2. 检查 GIN 索引是否创建
3. 测试搜索性能
4. 验证索引是否被使用
"""

import asyncio
import sys
import time
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from backend.database.db import async_engine
from backend.common.log import log


class Colors:
    """终端颜色"""
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    BOLD = '\033[1m'
    NC = '\033[0m'  # No Color


def print_section(title: str):
    """打印章节标题"""
    print(f"\n{Colors.BLUE}{'=' * 60}{Colors.NC}")
    print(f"{Colors.BOLD}{title}{Colors.NC}")
    print(f"{Colors.BLUE}{'=' * 60}{Colors.NC}\n")


async def check_pg_trgm_extension():
    """检查 pg_trgm 扩展是否启用"""
    print_section("1. 检查 pg_trgm 扩展")
    
    async with async_engine.begin() as conn:
        result = await conn.execute(text("""
            SELECT extname, extversion 
            FROM pg_extension 
            WHERE extname = 'pg_trgm'
        """))
        row = result.first()
        
        if row:
            print(f"{Colors.GREEN}✅ pg_trgm 扩展已启用{Colors.NC}")
            print(f"   版本: {row.extversion}")
            return True
        else:
            print(f"{Colors.RED}❌ pg_trgm 扩展未启用{Colors.NC}")
            print(f"{Colors.YELLOW}   请执行：CREATE EXTENSION IF NOT EXISTS pg_trgm;{Colors.NC}")
            return False


async def check_gin_indexes():
    """检查 GIN 索引是否创建"""
    print_section("2. 检查 GIN 索引")
    
    async with async_engine.begin() as conn:
        result = await conn.execute(text("""
            SELECT 
                indexname,
                indexdef
            FROM pg_indexes
            WHERE tablename = 'feedbacks'
              AND indexname LIKE '%gin%'
            ORDER BY indexname
        """))
        rows = result.all()
        
        if not rows:
            print(f"{Colors.RED}❌ 未找到 GIN 索引{Colors.NC}")
            print(f"{Colors.YELLOW}   请运行迁移：alembic upgrade head{Colors.NC}")
            return False
        
        print(f"{Colors.GREEN}✅ 找到 {len(rows)} 个 GIN 索引：{Colors.NC}\n")
        
        expected_indexes = {
            'idx_feedbacks_content_gin',
            'idx_feedbacks_ai_summary_gin'
        }
        found_indexes = set()
        
        for row in rows:
            found_indexes.add(row.indexname)
            print(f"   📊 {row.indexname}")
            print(f"      定义: {row.indexdef[:100]}...")
            print()
        
        missing = expected_indexes - found_indexes
        if missing:
            print(f"{Colors.YELLOW}⚠️  缺少索引: {', '.join(missing)}{Colors.NC}")
            return False
        
        return True


async def get_feedback_count():
    """获取反馈数量"""
    async with async_engine.begin() as conn:
        result = await conn.execute(text("SELECT COUNT(*) FROM feedbacks WHERE deleted_at IS NULL"))
        return result.scalar()


async def test_search_performance():
    """测试搜索性能"""
    print_section("3. 测试搜索性能")
    
    count = await get_feedback_count()
    print(f"数据量: {count} 条反馈\n")
    
    if count == 0:
        print(f"{Colors.YELLOW}⚠️  暂无反馈数据，跳过性能测试{Colors.NC}")
        return True
    
    # 测试查询
    test_cases = [
        ("搜索 content 字段", "SELECT * FROM feedbacks WHERE content ILIKE '%登录%' AND deleted_at IS NULL LIMIT 10"),
        ("搜索 ai_summary 字段", "SELECT * FROM feedbacks WHERE ai_summary ILIKE '%登录%' AND deleted_at IS NULL LIMIT 10"),
        ("搜索 content OR ai_summary", "SELECT * FROM feedbacks WHERE (content ILIKE '%登录%' OR ai_summary ILIKE '%登录%') AND deleted_at IS NULL LIMIT 10"),
    ]
    
    all_passed = True
    
    for test_name, query in test_cases:
        print(f"📋 {test_name}")
        
        async with async_engine.begin() as conn:
            # 执行查询并计时
            start_time = time.time()
            result = await conn.execute(text(query))
            rows = result.fetchall()
            elapsed_ms = (time.time() - start_time) * 1000
            
            # 评估性能
            if elapsed_ms < 100:
                status = f"{Colors.GREEN}✅ 优秀{Colors.NC}"
            elif elapsed_ms < 500:
                status = f"{Colors.YELLOW}⚠️  一般{Colors.NC}"
            else:
                status = f"{Colors.RED}❌ 较慢{Colors.NC}"
                all_passed = False
            
            print(f"   {status} 执行时间: {elapsed_ms:.2f}ms")
            print(f"   结果数: {len(rows)} 条\n")
    
    return all_passed


async def verify_index_usage():
    """验证索引是否被使用"""
    print_section("4. 验证索引使用情况")
    
    count = await get_feedback_count()
    
    query = """
        SELECT * FROM feedbacks 
        WHERE content ILIKE '%登录%' 
          AND deleted_at IS NULL 
        LIMIT 10
    """
    
    async with async_engine.begin() as conn:
        # 执行 EXPLAIN ANALYZE
        result = await conn.execute(text(f"EXPLAIN ANALYZE {query}"))
        explain_output = '\n'.join([row[0] for row in result.fetchall()])
        
        print("📊 执行计划：\n")
        print(explain_output)
        print()
        
        # 检查是否使用了索引
        if 'idx_feedbacks_content_gin' in explain_output:
            print(f"{Colors.GREEN}✅ 索引已被使用: idx_feedbacks_content_gin{Colors.NC}")
            return True
        elif 'Seq Scan' in explain_output:
            if count < 100:
                print(f"{Colors.YELLOW}ℹ️  使用了全表扫描（Seq Scan）- 这是正常的{Colors.NC}")
                print(f"{Colors.YELLOW}   原因：数据量较少（{count} 条），PostgreSQL 认为全表扫描更快{Colors.NC}")
                print(f"{Colors.YELLOW}   说明：当数据量增长到 100+ 条时，索引会自动生效{Colors.NC}")
                return True  # 小数据量不算失败
            else:
                print(f"{Colors.YELLOW}⚠️  使用了全表扫描（Seq Scan）{Colors.NC}")
                print(f"{Colors.YELLOW}   可能原因：{Colors.NC}")
                print(f"   - 数据量（{count} 条）仍较少，PostgreSQL 认为全表扫描更快")
                print(f"   - 索引未创建或损坏")
                return False
        else:
            print(f"{Colors.YELLOW}⚠️  无法确定是否使用索引{Colors.NC}")
            return False


async def print_summary(results: dict):
    """打印总结"""
    print_section("✨ 验证总结")
    
    all_passed = all(results.values())
    
    for test_name, passed in results.items():
        status = f"{Colors.GREEN}✅ 通过{Colors.NC}" if passed else f"{Colors.RED}❌ 失败{Colors.NC}"
        print(f"   {status} {test_name}")
    
    print()
    
    if all_passed:
        print(f"{Colors.GREEN}{Colors.BOLD}🎉 全文搜索索引工作正常！{Colors.NC}\n")
        print(f"{Colors.BLUE}📚 使用建议：{Colors.NC}")
        print(f"   - 关键词搜索性能已优化")
        print(f"   - 前端搜索响应时间应 < 100ms")
        print(f"   - 支持中文、英文模糊搜索")
    else:
        print(f"{Colors.RED}{Colors.BOLD}⚠️  部分检查未通过{Colors.NC}\n")
        print(f"{Colors.YELLOW}📖 解决方案：{Colors.NC}")
        print(f"   1. 确保数据库是 PostgreSQL")
        print(f"   2. 运行迁移：alembic upgrade head")
        print(f"   3. 查看文档：docs/development/fulltext-search-index-guide.md")


async def main():
    """主函数"""
    print(f"\n{Colors.BOLD}全文搜索索引验证程序{Colors.NC}")
    
    try:
        results = {
            'pg_trgm 扩展': await check_pg_trgm_extension(),
            'GIN 索引': await check_gin_indexes(),
            '搜索性能': await test_search_performance(),
            '索引使用': await verify_index_usage(),
        }
        
        await print_summary(results)
        
        # 返回退出码
        sys.exit(0 if all(results.values()) else 1)
        
    except Exception as e:
        print(f"\n{Colors.RED}❌ 验证过程出错: {e}{Colors.NC}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())
