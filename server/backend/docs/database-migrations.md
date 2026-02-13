# 数据库 Migrations 管理指南

## ⚠️ 重要：不要使用自动创建表

**从现在开始，应用启动时默认不会自动创建数据库表。**

之前每次启动都执行 `create_tables()`，浪费了 12 秒时间检查已存在的表。

## 正确的表管理方式

### 开发环境

#### 首次设置

```bash
# 1. 进入 server 目录
cd server

# 2. 激活虚拟环境
source .venv/Scripts/activate  # Windows Git Bash
# 或 .venv\Scripts\activate.ps1  # PowerShell

# 3. 运行所有 migrations
cd backend
alembic upgrade head
```

#### 创建新表或修改 schema

```bash
# 1. 修改模型（models）

# 2. 生成 migration
alembic revision --autogenerate -m "描述你的改动"

# 3. 检查生成的 migration 文件
# 位置：backend/alembic/versions/xxx.py

# 4. 应用 migration
alembic upgrade head
```

### 生产环境

**在 CI/CD pipeline 中执行 migrations，而不是应用启动时！**

```yaml
# 示例：GitHub Actions
- name: Run database migrations
  run: |
    cd server/backend
    alembic upgrade head

- name: Start application
  run: |
    cd server
    python -m backend.run
```

## 如果确实需要自动创建表

**仅用于测试/演示环境！**

设置环境变量：

```bash
# .env 文件
AUTO_CREATE_TABLES=true
```

或临时启用：

```bash
AUTO_CREATE_TABLES=true python -m backend.run
```

## 常用命令

```bash
# 查看当前 migration 状态
alembic current

# 查看 migration 历史
alembic history

# 回滚一个 migration
alembic downgrade -1

# 回滚到指定版本
alembic downgrade <revision>

# 查看 SQL（不执行）
alembic upgrade head --sql
```

## 性能对比

| 操作 | 耗时 | 说明 |
|------|------|------|
| `create_tables()` 每次启动 | **12 秒** | ❌ 浪费时间 |
| 跳过表创建 | **0 秒** | ✅ 推荐 |
| `alembic upgrade head` 首次 | 1-2 秒 | ✅ 只运行一次 |

## 故障排查

### 启动报错：表不存在

```bash
# 解决方案：运行 migrations
cd server/backend
alembic upgrade head
```

### Migration 冲突

```bash
# 1. 查看当前状态
alembic current

# 2. 如果有多个 head，合并它们
alembic merge heads -m "merge"

# 3. 应用合并后的 migration
alembic upgrade head
```

---

**原则：表的创建/修改是运维操作，不是应用逻辑的一部分。**


