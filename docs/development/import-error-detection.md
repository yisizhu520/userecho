# 导入错误检测指南

> "一次性发现所有导入错误,而不是一个个碰到。" - Linus

## 问题背景

在开发新模块时，经常会遇到导入路径错误：
- ❌ `from backend.common.uuid import uuid4_str` (错误)
- ✅ `from backend.database.db import uuid4_str` (正确)

这些错误通常要等到运行时才会发现，导致重复的"修复-重启-再报错"循环。

## 解决方案

### 方法 1: 快速静态检查（推荐）

使用 `quick_check.py` 进行 AST 静态分析，**无需运行代码**：

```bash
cd server

# 检查特定模块
python quick_check.py backend/app/batch/

# 检查整个 app 目录
python quick_check.py backend/app/
```

**优点：**
- ✅ 快速（秒级完成）
- ✅ 无需虚拟环境
- ✅ 检测已知的常见错误
- ✅ 提供修复建议

**输出示例：**

```
[FAIL] 发现 2 个文件有问题:

  backend\app\batch\service\batch_service.py
    Line 8: 错误的模块导入
      错误: from backend.common import timezone
      正确: from backend.utils.timezone import timezone
    
    Line 10: uuid4_str 不在 backend.common.uuid
      正确: from backend.database.db import uuid4_str
```

### 方法 2: 使用 mypy 类型检查

mypy 可以检测导入错误和类型错误：

```bash
cd server/backend

# 检查单个文件
../.venv/Scripts/python.exe -m mypy app/batch/api/v1/batch.py

# 检查整个模块
../.venv/Scripts/python.exe -m mypy app/batch/
```

**优点：**
- ✅ 检测所有导入错误（包括未知的）
- ✅ 同时检查类型错误
- ✅ 项目已配置

**缺点：**
- ❌ 较慢（大模块需要几十秒）
- ❌ 输出冗长

### 方法 3: 使用 Ruff 检查

Ruff 可以检测未使用的导入和导入错误：

```bash
cd server

# 只检查导入相关错误 (F401, F403, F405, E999)
.venv/Scripts/python.exe -m ruff check backend/app/batch/ --select F401,F403,F405,E999
```

**优点：**
- ✅ 极快
- ✅ 检测未使用的导入

**缺点：**
- ❌ 不能检测模块不存在的错误（只检测语法）

## 常见导入错误速查

### 认证相关

| ❌ 错误 | ✅ 正确 |
|--------|--------|
| `from backend.app.auth.deps import CurrentTenantId` | `from backend.common.security.jwt import CurrentTenantId` |
| `from backend.app.auth.deps import CurrentUserId` | `from backend.common.security.jwt import CurrentUserId` |

### 工具函数

| ❌ 错误 | ✅ 正确 |
|--------|--------|
| `from backend.common.uuid import uuid4_str` | `from backend.database.db import uuid4_str` |
| `from backend.common import timezone` | `from backend.utils.timezone import timezone` |
| `from backend.common import response_base` | `from backend.common.response.response_schema import response_base` |
| `from backend.common.log import log` | ✅ 这个是对的 |

### 如何查找正确的导入路径

**方法 1: 使用 grep 搜索**

```bash
cd server

# 搜索某个符号在哪里定义
grep -r "^def uuid4_str" backend/

# 搜索其他文件如何导入
grep -r "from.*import uuid4_str" backend/app/
```

**方法 2: 使用 IDE 的"跳转到定义"功能**

在 Cursor/VSCode 中，按住 Ctrl 点击符号名，IDE 会自动跳转到定义处。

**方法 3: 查看类似文件**

找一个功能类似的文件（如另一个 API 文件），复制它的导入语句。

## 开发工作流建议

### 编写新模块时

1. **先参考现有模块的导入**
   ```bash
   # 查看现有 API 如何导入
   head -20 backend/app/userecho/api/v1/feedback.py
   ```

2. **编写代码时使用 IDE 自动导入**
   - Cursor/VSCode 会自动建议导入路径
   - 使用 Ctrl+Space 触发自动补全

3. **完成后立即检查**
   ```bash
   python quick_check.py backend/app/your_module/
   ```

### 提交代码前

```bash
cd server

# 快速检查导入错误
python quick_check.py backend/app/

# 完整的代码质量检查（如果改动 >50 行）
bash pre-commit.sh
```

## 工具对比

| 工具 | 速度 | 覆盖范围 | 准确性 | 推荐场景 |
|------|------|---------|--------|---------|
| **quick_check.py** | ⚡ 极快 (1-2s) | 已知错误 | 高 | 日常开发、快速检查 |
| **mypy** | 🐢 较慢 (10-30s) | 所有导入 + 类型 | 最高 | 提交前检查 |
| **ruff** | ⚡ 极快 (<1s) | 语法 + 未使用导入 | 中 | 代码格式化时 |
| **pre-commit.sh** | 🐢 慢 (30-60s) | 全面检查 | 最高 | Git 提交前 |

## 常见问题

### Q: 为什么 mypy 这么慢？

A: mypy 需要分析整个项目的类型依赖。可以只检查修改的文件：
```bash
../.venv/Scripts/python.exe -m mypy app/batch/api/v1/batch.py
```

### Q: quick_check.py 检测不到某些错误？

A: 它只检测已知的常见错误。对于新类型的错误，需要添加到 `KNOWN_MODULES` 字典中，或使用 mypy。

### Q: 如何在 Git 提交时自动检查？

A: 项目已配置 pre-commit hook。提交时会自动运行 `pre-commit.sh`，包含所有检查。

## 最佳实践

1. **日常开发**：使用 `quick_check.py` 快速验证
2. **大改动后**：使用 `mypy` 全面检查
3. **提交前**：运行 `pre-commit.sh`
4. **遇到错误时**：先用 grep 搜索正确的导入路径

## 相关文档

- [Python 代码质量检查](./mypy-integration-guide.md)
- [后端开发规范](../../.cursor/rules/03-backend-standards.mdc)
- [常用命令](../../.cursor/rules/07-commands-env.mdc)
