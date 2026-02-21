#!/usr/bin/env python3
"""
数据库迁移执行脚本
解决 uv run 在 Windows 下的路径问题
"""

import subprocess
import sys
from pathlib import Path

# 获取项目根目录
SERVER_DIR = Path(__file__).parent
BACKEND_DIR = SERVER_DIR / "backend"
VENV_PYTHON = SERVER_DIR / ".venv" / "Scripts" / "python.exe"

def run_alembic(args: list[str]):
    """在 backend 目录下执行 alembic 命令"""
    cmd = [str(VENV_PYTHON), "-m", "alembic"] + args
    
    print(f"🔧 执行命令: {' '.join(args)}")
    print(f"📁 工作目录: {BACKEND_DIR}")
    print()
    
    result = subprocess.run(
        cmd,
        cwd=BACKEND_DIR,
        capture_output=False,
        text=True
    )
    
    return result.returncode

def main():
    if len(sys.argv) < 2:
        print("用法: python db_migrate.py <alembic命令>")
        print()
        print("示例:")
        print("  python db_migrate.py check          # 检查迁移链")
        print("  python db_migrate.py current        # 查看当前版本")
        print("  python db_migrate.py history        # 查看历史")
        print("  python db_migrate.py upgrade head   # 升级到最新")
        print("  python db_migrate.py upgrade +1     # 升级一个版本")
        print("  python db_migrate.py downgrade -1   # 回滚一个版本")
        sys.exit(1)
    
    # 获取 alembic 命令参数
    alembic_args = sys.argv[1:]
    
    # 特殊处理 upgrade 命令
    if alembic_args[0] == "upgrade" and len(alembic_args) > 1:
        print("⚠️  准备升级数据库")
        print("请确认已备份数据库！")
        confirm = input("是否继续? (y/N): ")
        if confirm.lower() != 'y':
            print("已取消升级")
            sys.exit(0)
    
    # 执行命令
    exit_code = run_alembic(alembic_args)
    
    if exit_code == 0:
        print()
        print("✅ 命令执行成功")
    else:
        print()
        print(f"❌ 命令执行失败 (退出码: {exit_code})")
    
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
