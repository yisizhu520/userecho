"""
手动执行 SQL 脚本来添加 Board 统计触发器
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from backend.database.db import async_engine


async def execute_sql_file():
    """执行 SQL 文件"""
    sql_file = 'backend/alembic/versions/manual_add_board_stats_triggers.sql'
    
    print(f'📖 读取 SQL 文件: {sql_file}')
    with open(sql_file, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    # 分割 SQL 语句（按分号分割，但跳过函数定义内的分号）
    statements = []
    current_stmt = []
    in_function = False
    
    for line in sql_content.split('\n'):
        line_stripped = line.strip()
        
        # 跳过注释
        if line_stripped.startswith('--'):
            continue
            
        # 检测函数定义的开始和结束
        if '$$' in line:
            in_function = not in_function
        
        current_stmt.append(line)
        
        # 如果不在函数内且遇到分号，则认为是一个完整语句
        if not in_function and line_stripped.endswith(';'):
            stmt = '\n'.join(current_stmt).strip()
            if stmt and not stmt.startswith('--'):
                statements.append(stmt)
            current_stmt = []
    
    print(f'✅ 解析完成，共 {len(statements)} 条 SQL 语句\n')
    
    # 执行 SQL 语句
    async with async_engine.begin() as conn:
        for i, stmt in enumerate(statements, 1):
            # 显示简短的语句描述
            first_line = stmt.split('\n')[0][:80]
            print(f'[{i}/{len(statements)}] 执行: {first_line}...')
            
            try:
                result = await conn.execute(text(stmt))
                
                # 如果是 SELECT 语句，显示结果
                if stmt.strip().upper().startswith('SELECT'):
                    rows = result.fetchall()
                    if rows:
                        print(f'    📊 查询结果 ({len(rows)} 行):')
                        for row in rows:
                            print(f'       {dict(row._mapping)}')
                    else:
                        print('    📊 查询结果: 无数据')
                else:
                    print('    ✅ 执行成功')
                    
            except Exception as e:
                print(f'    ❌ 执行失败: {e}')
                raise
    
    print('\n🎉 所有 SQL 语句执行完成！')


if __name__ == '__main__':
    asyncio.run(execute_sql_file())
