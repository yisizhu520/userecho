# mypy 静态类型检查集成指南

## 概述

已成功将 mypy 静态类型检查器集成到项目的代码质量检查工具链中。

## 配置变更

### 1. 依赖添加 (`pyproject.toml`)

```toml
[dependency-groups]
lint = [
    "pre-commit>=4.5.1",
    "prek>=0.2.19",
    "mypy>=1.13.0",           # 新增
    "types-redis>=4.6.0",      # 新增
    "types-pyyaml>=6.0.12",    # 新增
]
```

### 2. mypy 配置 (`pyproject.toml`)

```toml
[tool.mypy]
python_version = "3.10"
warn_return_any = true
warn_unused_configs = true
warn_redundant_casts = true
warn_unused_ignores = true
disallow_untyped_defs = false      # 暂不强制所有函数有类型注解
check_untyped_defs = true          # 但会检查现有类型注解的正确性
no_implicit_optional = true
show_error_codes = true
pretty = true

# 忽略没有类型存根的第三方库
[[tool.mypy.overrides]]
module = [
    "celery.*",
    "sqlalchemy_crud_plus.*",
    "fast_captcha.*",
    "ip2loc.*",
    "user_agents.*",
    "dulwich.*",
    "pwdlib.*",
    "msgspec.*",
    "jieba.*",
    "pgvector.*",
]
ignore_missing_imports = true
```

### 3. pre-commit 配置 (`.pre-commit-config.yaml`)

```yaml
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.13.0
    hooks:
      - id: mypy
        additional_dependencies:
          - types-redis>=4.6.0
          - types-pyyaml>=6.0.12
```

### 4. 脚本更新 (`pre-commit.sh`)

```bash
#!/usr/bin/env bash

.venv/Scripts/python.exe -m pre_commit run --all-files --verbose --show-diff-on-failure
```

## 使用方式

### 手动运行 mypy

```bash
# 检查单个文件
cd server
.venv/Scripts/python.exe -m mypy backend/app/admin/model/user.py

# 检查整个 backend 目录
.venv/Scripts/python.exe -m mypy backend/

# 检查指定模块
.venv/Scripts/python.exe -m mypy backend/app/admin/
```

### 通过 pre-commit 运行

```bash
cd server

# 检查所有文件（包括 mypy）
bash pre-commit.sh

# 或者只运行 mypy hook
.venv/Scripts/python.exe -m pre_commit run mypy --all-files
```

### 自动运行

在 git commit 时，pre-commit 会自动运行所有检查（包括 mypy）。

## 配置说明

### 严格级别

当前配置采用**渐进式严格模式**：

- ✅ **启用**：检查现有类型注解的正确性
- ✅ **启用**：警告返回 `Any` 类型
- ✅ **启用**：警告冗余的类型转换
- ❌ **禁用**：不强制所有函数都有类型注解 (`disallow_untyped_defs = false`)

这样的配置允许项目逐步增加类型注解，而不会一次性产生大量错误。

### 如何提高严格性

如果希望强制所有新函数都有类型注解，修改 `pyproject.toml`：

```toml
[tool.mypy]
disallow_untyped_defs = true  # 改为 true
```

⚠️ **注意**：这会立即产生大量错误，需要为所有函数添加类型注解。

### 忽略特定错误

如果某个文件或某行代码需要忽略 mypy 检查：

```python
# 忽略整个文件
# mypy: ignore-errors

# 忽略某一行
result = some_function()  # type: ignore[error-code]
```

## 与 Ruff 的关系

| 工具 | 作用 | 检查内容 |
|------|------|----------|
| **Ruff** | Linter + Formatter | 代码风格、潜在 bug、类型注解**是否存在** |
| **mypy** | 类型检查器 | 类型注解**是否正确**、类型推导 |

两者互补：
- Ruff 检查你是否写了类型注解（如 `ANN001` 规则）
- mypy 检查你写的类型注解是否正确

## 常见问题

### Q: 为什么 pre-commit 检查发现很多错误？

A: pre-commit 会检查整个项目的依赖链，包括导入的所有模块。这是正常的，说明项目中有一些类型注解不够精确。

可以逐步修复，或临时为特定文件添加忽略规则：

```toml
# pyproject.toml
[tool.mypy]
[[tool.mypy.overrides]]
module = "backend.app.some_module.*"
ignore_errors = true
```

### Q: 第三方库没有类型存根怎么办？

A: 已在配置中为常用的无类型存根库设置了 `ignore_missing_imports`。

如果遇到新的库报错，添加到 `pyproject.toml`：

```toml
[[tool.mypy.overrides]]
module = [
    "some_new_library.*",
]
ignore_missing_imports = true
```

### Q: mypy 检查太慢怎么办？

A: 可以启用缓存（默认已启用）和 daemon 模式：

```bash
# 使用 dmypy（mypy daemon）加速
.venv/Scripts/python.exe -m dmypy run backend/
```

## 最佳实践

1. **新代码强制类型注解**：为新写的函数添加完整的类型注解
2. **逐步迁移**：为重要的核心模块逐步添加类型注解
3. **使用 reveal_type**：调试时使用 `reveal_type(var)` 查看 mypy 推导的类型
4. **关注错误码**：mypy 的错误码（如 `[attr-defined]`）能帮助快速定位问题
5. **不要滥用 `type: ignore`**：尽量修复类型错误而不是忽略

## 验证

运行以下命令验证 mypy 是否正常工作：

```bash
cd server

# 1. 检查 mypy 版本
.venv/Scripts/python.exe -m mypy --version

# 2. 检查单个文件
.venv/Scripts/python.exe -m mypy backend/app/admin/model/user.py

# 3. 运行完整 pre-commit 检查
bash pre-commit.sh
```

## 参考资料

- [mypy 官方文档](https://mypy.readthedocs.io/)
- [mypy 配置选项](https://mypy.readthedocs.io/en/stable/config_file.html)
- [pre-commit 官方文档](https://pre-commit.com/)
