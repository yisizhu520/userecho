#!/usr/bin/env python3
"""生成迁移状态完整报告"""

import sys

sys.path.insert(0, '.')

from analyze_migrations import analyze_migrations

# 重定向 stdout 到文件
with open('migration_report.txt', 'w', encoding='utf-8') as f:
    sys.stdout = f
    analyze_migrations()
    sys.stdout = sys.__stdout__

print('✅ 报告已生成: migration_report.txt')
