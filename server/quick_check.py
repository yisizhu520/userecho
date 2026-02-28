"""快速检查导入错误 - 使用 AST 静态分析（无需导入模块）"""

import ast
import sys
from pathlib import Path
from collections import defaultdict


# 已知的项目模块映射
KNOWN_MODULES = {
    # 常见的错误导入 -> 正确导入
    "backend.common.uuid": "backend.database.db",
    "backend.common.timezone": "backend.utils.timezone", 
    "backend.app.auth.deps": "backend.common.security.jwt",
}

# 常见的导入符号 -> 正确位置
KNOWN_SYMBOLS = {
    "uuid4_str": "backend.database.db",
    "timezone": "backend.utils.timezone",
    "CurrentTenantId": "backend.common.security.jwt",
    "CurrentUserId": "backend.common.security.jwt",
    "log": "backend.common.log",
    "response_base": "backend.common.response.response_schema",
}


def check_file(file_path: Path) -> list[dict]:
    """检查单个文件的导入"""
    errors = []
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read())
        
        for node in ast.walk(tree):
            # 检查 from X import Y
            if isinstance(node, ast.ImportFrom):
                if node.module and node.module in KNOWN_MODULES:
                    correct_module = KNOWN_MODULES[node.module]
                    errors.append({
                        "line": node.lineno,
                        "type": "wrong_module",
                        "wrong": node.module,
                        "correct": correct_module,
                        "names": [alias.name for alias in node.names],
                    })
                
                # 检查导入的符号是否在正确的模块
                for alias in node.names:
                    if alias.name in KNOWN_SYMBOLS:
                        correct_module = KNOWN_SYMBOLS[alias.name]
                        if node.module != correct_module:
                            errors.append({
                                "line": node.lineno,
                                "type": "wrong_symbol_location",
                                "symbol": alias.name,
                                "wrong": node.module or "(relative import)",
                                "correct": correct_module,
                            })
    
    except SyntaxError as e:
        errors.append({
            "line": e.lineno,
            "type": "syntax_error",
            "error": str(e),
        })
    except Exception as e:
        errors.append({
            "line": 0,
            "type": "parse_error",
            "error": str(e),
        })
    
    return errors


def main():
    target_path = Path(sys.argv[1] if len(sys.argv) > 1 else "backend/app/batch")
    
    if not target_path.exists():
        print(f"[ERROR] 路径不存在: {target_path}")
        sys.exit(1)
    
    print(f"[*] 检查路径: {target_path}")
    print("=" * 70)
    print()
    
    all_errors = defaultdict(list)
    file_count = 0
    
    for py_file in sorted(target_path.rglob("*.py")):
        if "__pycache__" in str(py_file) or "alembic/versions" in str(py_file):
            continue
        
        file_count += 1
        errors = check_file(py_file)
        
        if errors:
            all_errors[py_file] = errors
    
    # 输出结果
    if all_errors:
        print(f"[FAIL] 发现 {len(all_errors)} 个文件有问题:\n")
        
        for file_path, errors in all_errors.items():
            rel_path = file_path.relative_to(target_path.parent.parent)
            print(f"  {rel_path}")
            
            for error in errors:
                if error["type"] == "wrong_module":
                    print(f"    Line {error['line']}: 错误的模块导入")
                    print(f"      错误: from {error['wrong']} import ...")
                    print(f"      正确: from {error['correct']} import ...")
                
                elif error["type"] == "wrong_symbol_location":
                    print(f"    Line {error['line']}: {error['symbol']} 不在 {error['wrong']}")
                    print(f"      正确: from {error['correct']} import {error['symbol']}")
                
                elif error["type"] == "syntax_error":
                    print(f"    Line {error['line']}: 语法错误")
                    print(f"      {error['error']}")
            
            print()
        
        print("=" * 70)
        print(f"[SUMMARY] 检查了 {file_count} 个文件, {len(all_errors)} 个有错误")
        sys.exit(1)
    else:
        print(f"[OK] 所有 {file_count} 个文件检查通过!")
        print("=" * 70)
        sys.exit(0)


if __name__ == "__main__":
    main()
