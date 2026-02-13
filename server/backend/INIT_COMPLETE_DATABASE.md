#完整数据库初始化指南

## 📋 当前情况

您的数据库缺少以下基础数据：
- ❌ 部门数据（0 个）
- ❌ 系统管理菜单（0 个）
- ❌ admin 超级管理员
- ❌ 测试角色（FBA 原生角色）

已有数据：
- ✅ 8 个业务功能菜单（`/app/*`）
- ✅ 5 个角色（4 个业务角色 + 1 个系统管理员角色）
- ✅ 6 个测试用户

---

## 🎯 推荐方案：使用 fba init + 重新导入业务数据

### 步骤 1：备份当前业务数据（可选）

如果需要保留当前的业务数据，可以先备份：

```bash
cd server/backend
pg_dump -h 23.94.83.70 -U maoku -d userecho -t sys_menu -t sys_role -t sys_user -t sys_user_role -t sys_role_menu > backup_business_data.sql
```

### 步骤 2：使用 fba init 初始化完整数据库

```bash
cd server/backend
fba init
```

**提示**：
- 选择 `y` 确认初始化
- 这会清空所有数据并重建
- 会创建完整的基础数据（部门、系统菜单、admin用户等）

### 步骤 3：重新创建业务数据

初始化完成后，重新运行我们的业务数据脚本：

```bash
# 激活虚拟环境
source ../.venv/Scripts/activate  # Linux/Mac/Git Bash
# 或
call ..\.venv\Scripts\activate.bat  # Windows CMD

# 创建默认租户（重要！）
python scripts/init_default_tenant.py

# 创建业务菜单和角色
python scripts/init_business_menus.py

# 创建测试用户
python scripts/create_test_users.py
```

---

## 🔄 完整的一键脚本

我为您创建一个完整的初始化脚本：

```bash
#!/bin/bash
# 完整数据库初始化脚本

cd server/backend
source ../.venv/Scripts/activate

echo "步骤 1: 使用 fba init 初始化基础数据..."
fba init

echo ""
echo "步骤 2: 创建默认租户..."
python scripts/init_default_tenant.py

echo ""
echo "步骤 3: 创建业务菜单和角色..."
python scripts/init_business_menus.py

echo ""
echo "步骤 4: 创建测试用户..."
python scripts/create_test_users.py

echo ""
echo "步骤 5: 验证初始化结果..."
python -c "
import asyncio, io, sys
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, '.')
from sqlalchemy import select, func
from backend.app.admin.model import User, Role, Menu, Dept
from backend.database.db import async_db_session

async def verify():
    async with async_db_session() as db:
        dept_count = await db.scalar(select(func.count(Dept.id)))
        menu_count = await db.scalar(select(func.count(Menu.id)))
        role_count = await db.scalar(select(func.count(Role.id)))
        user_count = await db.scalar(select(func.count(User.id)))
        
        print('✅ 初始化完成！')
        print(f'   部门: {dept_count}')
        print(f'   菜单: {menu_count}')
        print(f'   角色: {role_count}')
        print(f'   用户: {user_count}')

asyncio.run(verify())
"

echo ""
echo "✅ 完整数据库初始化完成！"
```

---

## 📝 初始化后您将拥有

### 系统管理数据：
- **admin** 超级管理员（密码：`Admin123456`）
- **test** 测试用户（密码：`Test123456`）
- "测试"部门
- 50+ 个系统管理菜单（`/system/*`, `/log/*`, `/monitor/*` 等）
- "测试"角色（FBA 原生角色）

### 业务数据：
- **6 个测试用户**（密码：`Test123456`）
  - sysadmin（系统管理员）
  - pm（PM）
  - cs（CS）
  - dev（开发）
  - boss（老板）
  - hybrid（混合角色）
- **8 个业务菜单**（`/app/*`）
- **5 个角色**（4 个业务角色 + 1 个系统管理员角色）

---

## ⚡ 快速执行（推荐）

### 🎯 一键完整初始化（推荐）

使用新的统一脚本，一条命令搞定：

```bash
cd server/backend

# Linux/Mac/Git Bash
chmod +x init_complete_database.sh
./init_complete_database.sh

# Windows CMD
init_complete_database.bat

# Windows PowerShell
.\init_complete_database.bat
```

### 📝 手动分步执行

如果需要手动控制每个步骤：

```bash
cd server/backend

# 步骤 1：初始化系统基础数据
fba init  # 选择 y 确认

# 步骤 2：创建默认租户
python scripts/init_default_tenant.py

# 步骤 3：创建业务菜单和角色
python scripts/init_business_menus.py

# 步骤 4：创建测试用户
python scripts/create_test_users.py
```

---

## 🎯 最终结果

完成后您将拥有：
- ✅ 完整的系统管理功能（admin 可以管理）
- ✅ 完整的业务功能菜单（pm/cs/dev/boss 可以使用）
- ✅ 所有测试账号就绪
- ✅ 部门数据完整

---

## 💡 脚本对比说明

### `init_complete_database.sh`（新，推荐）
**完整初始化脚本** - 包含系统数据 + 业务数据

执行内容：
1. ✅ `fba init` - 初始化系统基础数据（部门、系统菜单、admin）
   - 自动执行 `alembic upgrade head`（创建表结构）
   - 自动导入 `sql/postgresql/init_test_data.sql`（系统数据）
2. ✅ `scripts/init_default_tenant.py` - 创建默认租户（`default-tenant`）
3. ✅ `scripts/init_business_menus.py` - 创建业务菜单和角色
4. ✅ `scripts/create_test_users.py` - 创建测试用户

结果：**完整的可用系统**（系统管理 + 租户 + 业务功能）

### `init_database.sh`（旧）
**仅业务数据初始化脚本** - 不含系统基础数据

执行内容：
1. ✅ `alembic upgrade head` - 创建表结构
2. ✅ `scripts/init_business_menus.py` - 创建业务菜单和角色
3. ✅ `scripts/create_test_users.py` - 创建测试用户

结果：**缺少系统管理功能**（无 admin、无部门、无系统菜单）

### 为什么需要新脚本？

旧脚本 `init_database.sh` **没有执行**：
- `sql/postgresql/init_test_data.sql`（系统基础数据）
- `scripts/init_default_tenant.py`（默认租户）

导致缺少：
- 部门数据
- 系统管理菜单（`/system/*`, `/log/*`, `/monitor/*`）
- admin 超级管理员
- 测试角色（FBA 原生）
- **默认租户（`default-tenant`）** - 导致外键约束错误

而 `fba init` 会自动执行系统 SQL 文件。新脚本在 `fba init` 之后立即创建默认租户，确保所有数据完整。

---

## 🛠️ 我来帮您执行吗？

如果您同意，我可以帮您执行完整的初始化流程。请确认：

1. ✅ 可以清空当前数据库（会丢失当前的业务菜单和测试用户）
2. ✅ 重新初始化后会立即重新创建业务数据

请回复 "yes" 我就开始执行。

