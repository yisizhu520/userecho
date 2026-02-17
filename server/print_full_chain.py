#!/usr/bin/env python3
"""打印完整迁移链，包括所有分支"""
import re
from pathlib import Path

versions_dir = Path('backend/alembic/versions')
migrations = {}

# 解析所有迁移
for f in versions_dir.glob('*.py'):
    if f.name.startswith('__'):
        continue
    content = f.read_text()
    
    rev_match = re.search(r"""revision(?:\s*:\s*str)?\s*=\s*['"]([^'"]+)['"]""", content)
    down_match = re.search(r"""down_revision(?:\s*:\s*str\s*\|\s*None)?\s*=\s*['"]([^'"]+)['"]""", content)
    
    if rev_match:
        migrations[rev_match.group(1)] = {
            'down': down_match.group(1) if down_match else None,
            'file': f.name
        }

# 找到所有根节点
roots = [rev for rev, info in migrations.items() if info['down'] is None]
print(f"找到 {len(roots)} 个根节点: {roots}")
print()

# 从每个根节点打印链条
for root in roots:
    print(f"=== 从 {root} 开始的链条 ===")
    visited = set()
    current = root
    depth = 1
    
    while current:
        if current in visited:
            print(f"  ❌ 检测到循环！")
            break
        visited.add(current)
        
        file = migrations[current]['file']
        print(f"  {depth:2d}. {current:25s} | {file[:60]}")
        
        # 找下一个
        next_rev = None
        for rev, info in migrations.items():
            if info['down'] == current:
                next_rev = rev
                break
        
        current = next_rev
        depth += 1
    
    print(f"  链长度: {depth - 1}")
    print()

print(f"总计: {len(migrations)} 个迁移，{len(visited)} 个在链上")
