"""临时脚本：删除 feedbacks.title 字段"""

import sys

from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text

from backend.database.db_postgres import get_db

db = next(get_db())

# 检查是否有 title 列
result = db.execute(
    text("""
    SELECT column_name
    FROM information_schema.columns
    WHERE table_name = 'feedbacks' AND column_name = 'title'
""")
)

if result.fetchone():
    print('✅ 找到 title 列，开始迁移...')

    # 1. 合并 title 到 content
    result = db.execute(
        text("""
        UPDATE feedbacks
        SET content = CONCAT('【标题】', title, E'\n\n', content)
        WHERE title IS NOT NULL AND title != ''
    """)
    )
    affected = result.rowcount
    print(f'   ├─ 已合并 {affected} 条记录的 title 到 content')

    # 2. 删除 title 列
    db.execute(text('ALTER TABLE feedbacks DROP COLUMN title'))
    print('   ├─ 已删除 title 列')

    db.commit()
    print('✅ 迁移完成！')
else:
    print('ℹ️  title 列不存在，无需迁移')

db.close()
