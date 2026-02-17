#!/usr/bin/env python3
"""
分析 Alembic 迁移链完整性
找出版本链断裂、重复定义、命名混乱等问题
"""
import os
import re
from pathlib import Path
from typing import Dict, List, Set, Optional

# 迁移脚本目录
VERSIONS_DIR = Path(__file__).parent / 'backend' / 'alembic' / 'versions'


class Migration:
    def __init__(self, filepath: Path):
        self.filepath = filepath
        self.filename = filepath.name
        self.revision: Optional[str] = None
        self.down_revision: Optional[str] = None
        self.description: str = ''
        self.creates_functions: List[str] = []
        self.creates_triggers: List[str] = []
        self.creates_tables: List[str] = []
        self.parse()
    
    def parse(self):
        """解析迁移文件内容"""
        content = self.filepath.read_text(encoding='utf-8')
        
        # 提取 revision - 匹配两种格式
        if match := re.search(r"""revision(?:\s*:\s*str)?\s*=\s*['"]([^'"]+)['"]""", content):
            self.revision = match.group(1)
        
        # 提取 down_revision
        if match := re.search(r"""down_revision(?:\s*:\s*str\s*\|\s*None)?\s*=\s*['"]([^'"]+)['"]""", content):
            self.down_revision = match.group(1)
        elif 'down_revision = None' in content or 'down_revision: str | None = None' in content:
            self.down_revision = None
        
        # 提取描述
        lines = content.split('\n')
        if len(lines) > 0 and '"""' in lines[0]:
            desc_lines = []
            for i, line in enumerate(lines[1:], 1):
                if '"""' in line:
                    break
                desc_lines.append(line.strip())
            self.description = ' '.join(desc_lines)[:100]
        
        # 提取创建的函数
        self.creates_functions = re.findall(r'CREATE (?:OR REPLACE )?FUNCTION\s+(\w+)\s*\(', content, re.IGNORECASE)
        
        # 提取创建的触发器
        self.creates_triggers = re.findall(r'CREATE TRIGGER\s+(\w+)', content, re.IGNORECASE)
        
        # 提取创建的表
        self.creates_tables = re.findall(r"op\.create_table\(\s*['\"](\w+)['\"]", content)
    
    def __repr__(self):
        return f"Migration({self.filename}, rev={self.revision}, down={self.down_revision})"


def analyze_migrations():
    """分析所有迁移脚本"""
    print("=" * 80)
    print("🔍 Alembic 迁移链完整性分析")
    print("=" * 80)
    print()
    
    # 收集所有迁移
    migrations: List[Migration] = []
    for filepath in sorted(VERSIONS_DIR.glob('*.py')):
        if filepath.name.startswith('__'):
            continue
        migrations.append(Migration(filepath))
    
    print(f"📊 共找到 {len(migrations)} 个迁移脚本\n")
    
    # 建立 revision 索引
    rev_to_migration: Dict[str, Migration] = {}
    for m in migrations:
        if m.revision:
            if m.revision in rev_to_migration:
                print(f"❌ 致命错误：重复的 revision ID: {m.revision}")
                print(f"   文件1: {rev_to_migration[m.revision].filename}")
                print(f"   文件2: {m.filename}")
                print()
            rev_to_migration[m.revision] = m
    
    # 检查1: 版本链完整性
    print("=" * 80)
    print("📋 检查1: 版本链完整性")
    print("=" * 80)
    broken_links = []
    for m in migrations:
        if m.down_revision and m.down_revision not in rev_to_migration:
            broken_links.append(m)
            print(f"❌ 断链: {m.filename}")
            print(f"   revision: {m.revision}")
            print(f"   down_revision: {m.down_revision} (不存在!)")
            print()
    
    if not broken_links:
        print("✅ 版本链完整，无断链\n")
    else:
        print(f"⚠️  发现 {len(broken_links)} 个断链\n")
    
    # 检查2: Revision ID 格式混乱
    print("=" * 80)
    print("📋 检查2: Revision ID 格式一致性")
    print("=" * 80)
    
    formats = {
        'hash': [],      # 类似 9a2de98df5fb
        'date1': [],     # 类似 2025122201
        'date2': [],     # 类似 20251231a
    }
    
    for m in migrations:
        if not m.revision:
            continue
        rev = m.revision
        if re.match(r'^[0-9a-f]{12}$', rev):
            formats['hash'].append(m)
        elif re.match(r'^\d{10}$', rev):
            formats['date1'].append(m)
        elif re.match(r'^\d{8}[a-z]$', rev):
            formats['date2'].append(m)
    
    print(f"格式统计:")
    print(f"  - 哈希格式 (9a2de98df5fb): {len(formats['hash'])} 个")
    print(f"  - 日期格式1 (2025122201): {len(formats['date1'])} 个")
    print(f"  - 日期格式2 (20251231a): {len(formats['date2'])} 个")
    print()
    
    if len([k for k, v in formats.items() if v]) > 1:
        print("⚠️  Revision ID 格式不一致！建议统一格式\n")
    else:
        print("✅ Revision ID 格式一致\n")
    
    # 检查3: 重复功能定义
    print("=" * 80)
    print("📋 检查3: 重复的函数/触发器/表定义")
    print("=" * 80)
    
    all_functions: Dict[str, List[Migration]] = {}
    all_triggers: Dict[str, List[Migration]] = {}
    all_tables: Dict[str, List[Migration]] = {}
    
    for m in migrations:
        for func in m.creates_functions:
            all_functions.setdefault(func, []).append(m)
        for trigger in m.creates_triggers:
            all_triggers.setdefault(trigger, []).append(m)
        for table in m.creates_tables:
            all_tables.setdefault(table, []).append(m)
    
    duplicates_found = False
    
    for func, migs in all_functions.items():
        if len(migs) > 1:
            duplicates_found = True
            print(f"❌ 函数 '{func}' 被创建了 {len(migs)} 次:")
            for m in migs:
                print(f"   - {m.filename}")
            print()
    
    for trigger, migs in all_triggers.items():
        if len(migs) > 1:
            duplicates_found = True
            print(f"❌ 触发器 '{trigger}' 被创建了 {len(migs)} 次:")
            for m in migs:
                print(f"   - {m.filename}")
            print()
    
    for table, migs in all_tables.items():
        if len(migs) > 1:
            duplicates_found = True
            print(f"❌ 表 '{table}' 被创建了 {len(migs)} 次:")
            for m in migs:
                print(f"   - {m.filename}")
            print()
    
    if not duplicates_found:
        print("✅ 未发现重复定义\n")
    
    # 检查4: 手动 SQL 文件
    print("=" * 80)
    print("📋 检查4: 手动执行的 SQL 文件")
    print("=" * 80)
    
    manual_sqls = list(VERSIONS_DIR.glob('manual_*.sql'))
    if manual_sqls:
        print(f"❌ 发现 {len(manual_sqls)} 个手动 SQL 文件 (说明迁移曾经失败):")
        for sql in manual_sqls:
            print(f"   - {sql.name}")
        print()
        print("⚠️  警告：手动执行的 SQL 会导致 Alembic 版本表与实际数据库状态不一致！")
        print()
    else:
        print("✅ 未发现手动 SQL 文件\n")
    
    # 检查5: 打印完整迁移链
    print("=" * 80)
    print("📋 完整迁移链 (从旧到新)")
    print("=" * 80)
    
    # 找到根节点
    root = None
    for m in migrations:
        if m.down_revision is None:
            root = m
            break
    
    if root:
        visited = set()
        current = root
        chain = []
        
        while current:
            if current.revision in visited:
                print("❌ 检测到循环依赖！")
                break
            visited.add(current.revision)
            chain.append(current)
            
            # 找下一个
            next_m = None
            for m in migrations:
                if m.down_revision == current.revision:
                    next_m = m
                    break
            current = next_m
        
        print(f"迁移链长度: {len(chain)} / {len(migrations)}")
        if len(chain) != len(migrations):
            print(f"⚠️  警告：有 {len(migrations) - len(chain)} 个迁移未在主链中！\n")
        
        print("\n迁移顺序:")
        for i, m in enumerate(chain, 1):
            print(f"{i:2d}. {m.revision:15s} ← {m.down_revision or 'None':15s} | {m.filename}")
        print()
    else:
        print("❌ 未找到根节点 (down_revision = None)\n")
    
    # 总结
    print("=" * 80)
    print("📊 问题总结")
    print("=" * 80)
    
    issues = []
    if broken_links:
        issues.append(f"版本链断裂: {len(broken_links)} 处")
    if len([k for k, v in formats.items() if v]) > 1:
        issues.append("Revision ID 格式不一致")
    if duplicates_found:
        issues.append("存在重复的函数/触发器定义")
    if manual_sqls:
        issues.append(f"存在 {len(manual_sqls)} 个手动 SQL 补丁文件")
    
    if issues:
        print("❌ 发现以下问题:")
        for issue in issues:
            print(f"   - {issue}")
        print("\n建议：立即修复迁移脚本，确保幂等性和版本链完整性")
    else:
        print("✅ 迁移脚本健康，未发现明显问题")
    
    print()


if __name__ == '__main__':
    analyze_migrations()
