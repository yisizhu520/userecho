#!/usr/bin/env python3
"""依赖检查脚本 - 扫描所有 Python 文件的 import 并检查是否在 pyproject.toml 中声明"""

import ast
import sys
from pathlib import Path
from typing import Set

try:
    import tomllib  # Python 3.11+
except ImportError:
    import tomli as tomllib  # Python 3.10


def extract_imports(file_path: Path) -> Set[str]:
    """从 Python 文件中提取所有顶级导入的包名"""
    try:
        with open(file_path, encoding='utf-8') as f:
            tree = ast.parse(f.read(), filename=str(file_path))
    except (SyntaxError, UnicodeDecodeError) as e:
        print(f"⚠️  无法解析 {file_path}: {e}")
        return set()
    
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                # 提取顶级包名，例如 "numpy.core" -> "numpy"
                imports.add(alias.name.split('.')[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.level == 0:  # 只处理绝对导入
                imports.add(node.module.split('.')[0])
    
    return imports


def get_declared_dependencies() -> Set[str]:
    """从 pyproject.toml 读取已声明的依赖"""
    pyproject_path = Path(__file__).parent / 'pyproject.toml'
    
    with open(pyproject_path, 'rb') as f:
        data = tomllib.load(f)
    
    dependencies = set()
    
    # 从 project.dependencies 获取
    if 'project' in data and 'dependencies' in data['project']:
        for dep in data['project']['dependencies']:
            # 提取包名，例如 "numpy>=1.26.0" -> "numpy"
            # 处理 "package[extra]>=version" 格式
            pkg_name = dep.split('[')[0].split('>=')[0].split('==')[0].split('<')[0].split('>')[0].strip()
            dependencies.add(pkg_name.lower())
    
    # 从 dependency-groups 获取
    if 'dependency-groups' in data:
        for group_deps in data['dependency-groups'].values():
            for dep in group_deps:
                pkg_name = dep.split('[')[0].split('>=')[0].split('==')[0].split('<')[0].split('>')[0].strip()
                dependencies.add(pkg_name.lower())
    
    return dependencies


def is_stdlib_or_local(package: str) -> bool:
    """判断是否是标准库或本地包"""
    stdlib_and_local = {
        # 标准库
        '__future__', 'abc', 'asyncio', 'atexit', 'collections', 'contextlib', 
        'dataclasses', 'datetime', 'decimal', 'email', 'enum', 'functools', 
        'glob', 'hashlib', 'hmac', 'importlib', 'inspect', 'io', 'itertools',
        'json', 'logging', 'math', 'multiprocessing', 'operator', 'os', 'pathlib', 
        'pickle', 'platform', 'random', 're', 'secrets', 'shutil', 'socket', 
        'string', 'subprocess', 'sys', 'tempfile', 'threading', 'time', 'traceback',
        'typing', 'urllib', 'uuid', 'warnings', 'weakref', 'xml', 'zipfile', 'zoneinfo',
        # 本地包
        'backend', 'app', 'common', 'core', 'database', 'middleware', 'plugin',
        'utils', 'alembic',
    }
    return package.lower() in stdlib_and_local


# 包名映射：import名 -> pyproject.toml中的包名
PACKAGE_MAPPING = {
    'dotenv': 'python-dotenv',
    'jose': 'python-jose',
    'socketio': 'python-socketio',
    'yaml': 'pyyaml',
    'sklearn': 'scikit-learn',
    'cv2': 'opencv-python',
    'PIL': 'pillow',
}

# 这些包是其他依赖的子依赖，不需要显式声明
SUB_DEPENDENCIES = {
    'aiosmtplib',  # 可能是某个插件的依赖
    'anyio',  # httpx 的依赖
    'fastapi_oauth20',  # 可能是插件依赖
    'httpx',  # fastapi[standard] 包含
    'opentelemetry',  # opentelemetry-* 包的命名空间
    'packaging',  # 很多包的依赖
    'pydantic_core',  # pydantic 的依赖
    'rich',  # 已在依赖中但可能被识别为子依赖
    'starlette',  # fastapi 的依赖
    'uvicorn',  # fastapi[standard] 包含
    'watchfiles',  # uvicorn 的依赖
}


def main():
    print("🔍 开始扫描 Python 文件的导入语句...\n")
    
    # 扫描所有 Python 文件
    backend_path = Path(__file__).parent / 'backend'
    all_imports = set()
    file_count = 0
    
    for py_file in backend_path.rglob('*.py'):
        if '__pycache__' in str(py_file) or '.venv' in str(py_file):
            continue
        file_count += 1
        imports = extract_imports(py_file)
        all_imports.update(imports)
    
    print(f"📁 扫描了 {file_count} 个 Python 文件")
    print(f"📦 发现 {len(all_imports)} 个不同的导入包\n")
    
    # 读取已声明的依赖
    declared = get_declared_dependencies()
    print(f"✅ pyproject.toml 中声明了 {len(declared)} 个依赖\n")
    
    # 找出未声明的第三方依赖
    missing = []
    for pkg in sorted(all_imports):
        if not is_stdlib_or_local(pkg):
            # 跳过子依赖
            if pkg in SUB_DEPENDENCIES:
                continue
            
            # 先检查是否有包名映射
            actual_pkg = PACKAGE_MAPPING.get(pkg, pkg)
            
            # 规范化包名用于比较
            pkg_normalized = actual_pkg.lower().replace('_', '-')
            declared_normalized = {d.replace('_', '-') for d in declared}
            
            if pkg_normalized not in declared_normalized and actual_pkg.lower() not in declared:
                missing.append(f"{pkg} (实际包名: {actual_pkg})" if pkg != actual_pkg else pkg)
    
    if missing:
        print("❌ 发现未声明的第三方依赖:\n")
        for pkg in missing:
            print(f"   - {pkg}")
        print(f"\n总计 {len(missing)} 个缺失依赖")
        print("\n建议在 pyproject.toml 的 dependencies 中添加:")
        for pkg in missing:
            print(f'    "{pkg}>=x.x.x",')
        return 1
    else:
        print("✅ 所有第三方依赖都已正确声明!")
        return 0


if __name__ == '__main__':
    sys.exit(main())
