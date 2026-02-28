#!/usr/bin/env python3
"""检查所有 Python 文件的导入错误（通过实际导入检测）

Usage:
    cd server
    python check_imports.py [path]
    
Examples:
    python check_imports.py backend/app/batch/
    python check_imports.py backend/
"""

import sys
import importlib.util
from pathlib import Path
from typing import Optional


def module_path_from_file(file_path: Path, root_dir: Path) -> str:
    """将文件路径转换为模块路径"""
    relative_path = file_path.relative_to(root_dir.parent)
    parts = list(relative_path.parts[:-1]) + [relative_path.stem]
    return ".".join(parts)


def check_file_imports(file_path: Path, root_dir: Path) -> tuple[bool, Optional[str]]:
    """
    尝试加载文件来检测导入错误
    
    Returns:
        (是否成功, 错误信息)
    """
    try:
        module_name = module_path_from_file(file_path, root_dir)
        
        # 使用 importlib 加载模块
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec is None or spec.loader is None:
            return False, "Failed to create module spec"
        
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        
        return True, None
    except ModuleNotFoundError as e:
        return False, f"ModuleNotFoundError: {e}"
    except ImportError as e:
        return False, f"ImportError: {e}"
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"


def check_imports(root_path: Path) -> tuple[list[str], list[tuple[str, str]]]:
    """
    检查指定路径下所有 Python 文件的导入错误
    
    Returns:
        (成功文件列表, 错误列表: [(文件路径, 错误信息)])
    """
    success_files = []
    errors = []
    
    python_files = sorted(root_path.rglob("*.py"))
    backend_root = root_path
    while backend_root.name != "server" and backend_root.parent != backend_root:
        backend_root = backend_root.parent
    
    # 将 backend 目录添加到 Python 路径
    sys.path.insert(0, str(backend_root))
    
    print(f"[*] 找到 {len(python_files)} 个 Python 文件\n")
    
    for py_file in python_files:
        # 跳过 __pycache__, tests, alembic migrations
        if any(part in str(py_file) for part in ["__pycache__", "alembic/versions"]):
            continue
        
        # 跳过 __init__.py（通常不会有导入错误）
        if py_file.name == "__init__.py":
            continue
        
        success, error = check_file_imports(py_file, backend_root)
        
        rel_path = str(py_file.relative_to(backend_root))
        
        if success:
            success_files.append(rel_path)
            print(f"[OK] {rel_path}")
        else:
            errors.append((rel_path, error))
            print(f"[FAIL] {rel_path}")
            print(f"       {error}")
    
    return success_files, errors


def main():
    # 获取要检查的路径
    if len(sys.argv) > 1:
        target_path = Path(sys.argv[1]).resolve()
    else:
        # 默认检查 backend/app/batch 目录
        target_path = Path(__file__).parent / "backend" / "app" / "batch"
    
    if not target_path.exists():
        print(f"[ERROR] 路径不存在: {target_path}")
        sys.exit(1)
    
    print(f"[*] 检查路径: {target_path}\n")
    print("=" * 60)
    print()
    
    # 执行检查
    success_files, errors = check_imports(target_path)
    
    # 输出汇总
    print()
    print("=" * 60)
    print(f"\n[SUMMARY] 检查完成:")
    print(f"   [OK]   成功: {len(success_files)} 个文件")
    print(f"   [FAIL] 失败: {len(errors)} 个文件")
    
    if errors:
        print(f"\n[TIPS] 修复提示:")
        print(f"   1. 使用 grep 查找正确的导入路径:")
        print(f"      grep -r 'from.*import XXX' backend/app/")
        print(f"   2. 参考项目中其他文件的导入方式")
        print(f"   3. 检查模块是否真的存在")
    
    # 返回错误码
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
