#!/usr/bin/env python3
"""精简的链条检查"""
import re
from pathlib import Path

versions_dir = Path('backend/alembic/versions')
migrations = {}

for f in versions_dir.glob('*.py'):
    if f.name.startswith('__'):
        continue
    content = f.read_text()
    
    # 匹配两种格式: revision = '...' 和 revision: str = '...'
    rev_match = re.search(r"""revision(?:\s*:\s*str)?\s*=\s*['"]([^'"]+)['"]""", content)
    down_match = re.search(r"""down_revision(?:\s*:\s*str\s*\|\s*None)?\s*=\s*['"]([^'"]+)['"]""", content)
    
    if rev_match:
        migrations[rev_match.group(1)] = {
            'down': down_match.group(1) if down_match else None,
            'file': f.name
        }

# 找断链
print("检查断链:")
broken_count = 0
for rev, info in migrations.items():
    down = info['down']
    if down and down not in migrations:
        print(f"❌ [{rev}] -> [{down}] (不存在!)  |  {info['file']}")
        broken_count += 1

if broken_count == 0:
    print("✅ 所有迁移链接正常！")
else:
    print(f"\n总计 {broken_count} 个断链")
