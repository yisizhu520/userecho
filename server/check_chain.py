#!/usr/bin/env python3
"""检查所有迁移的详细链条"""
import re
from pathlib import Path

versions_dir = Path('backend/alembic/versions')

# 解析所有迁移
migrations = {}
for f in sorted(versions_dir.glob('*.py')):
    if f.name.startswith('__'):
        continue
    content = f.read_text(encoding='utf-8')
    
    rev_match = re.search(r"""revision\s*[:=]\s*['"]([^'"]+)['"]""", content)
    down_match = re.search(r"""down_revision\s*[:=]\s*['"]([^'"]+)['"]""", content)
    
    if rev_match:
        rev = rev_match.group(1)
        down = down_match.group(1) if down_match else None
        time_match = re.match(r'(\d{4}-\d{2}-\d{2}-\d{2}_\d{2}_\d{2})', f.name)
        timestamp = time_match.group(1) if time_match else '0000'
        migrations[rev] = {'file': f.name, 'down': down, 'time': timestamp}

# 按时间排序显示
print('所有迁移 (按文件时间排序):')
print('=' * 120)
for rev in sorted(migrations.keys(), key=lambda r: migrations[r]['time']):
    m = migrations[rev]
    down_exists = '✅' if m['down'] is None or m['down'] in migrations else '❌'
    print(f"{down_exists} {m['time']} | rev={rev:25s} | down={m['down'] or 'None':25s} | {m['file'][:60]}")

print()
print('断链的迁移:')
print('=' * 120)
broken = []
for rev, m in migrations.items():
    if m['down'] is not None and m['down'] not in migrations:
        broken.append((rev, m))
        print(f"❌ {rev} -> {m['down']} (不存在!)  文件: {m['file']}")

if not broken:
    print("✅ 没有断链")
