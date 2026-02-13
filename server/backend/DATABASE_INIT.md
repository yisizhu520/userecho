# 数据库初始化指南

> **适用场景**：全新数据库或需要重置数据库时使用

## 🚀 快速开始（一键初始化）

### Windows 用户

#### 方式 1：双击运行（推荐）
```
双击 server/backend/init_database.bat 文件
```

#### 方式 2：命令行运行
```cmd
cd server\backend
init_database.bat
```

#### 方式 3：使用 Git Bash
```bash
cd server/backend
./init_database.sh
```

---

### Linux/Mac 用户

```bash
cd server/backend
chmod +x init_database.sh  # 首次需要添加执行权限
./init_database.sh
```

---

## 📋 初始化内容

一键脚本会自动完成以下操作：

### 1️⃣ **创建数据库表结构**
- 执行 Alembic 数据库迁移
- 创建所有系统表（用户、角色、菜单、反馈、主题等）
- 创建索引和约束

### 2️⃣ **初始化业务菜单和角色**
- 创建反馈管理目录 (`/app/userecho`)
- 创建 5 个功能菜单：
  - 📥 反馈列表
  - ✨ AI 发现中心
  - 📤 导入反馈
  - 💡 需求主题
  - 👥 客户管理
- 创建设置目录及子菜单（聚类策略）
- 创建 4 个业务角色：PM、CS、开发、老板
- 自动关联角色和菜单权限

### 3️⃣ **创建测试用户**
- 创建 6 个测试账号（统一密码：`Test123456`）
- 自动关联用户和角色

### 4️⃣ **验证初始化结果**
- 检查菜单数量
- 检查角色数量
- 检查测试用户数量

---

## 📝 测试账号清单

| 账号 | 密码 | 角色 | 菜单权限 | 用途 |
|------|------|------|----------|------|
| `sysadmin` | Test123456 | 系统管理员 | `/admin/*` 菜单 | 测试系统管理功能 |
| `pm` | Test123456 | PM | `/app/*` 全部菜单 | 测试完整业务权限 |
| `cs` | Test123456 | CS | `/app/*` 部分菜单 | 测试部分权限 |
| `dev` | Test123456 | 开发 | `/app/*` 只读菜单 | 测试只读权限 |
| `boss` | Test123456 | 老板 | `/app/*` 全部菜单 | 测试租户管理员 |
| `hybrid` | Test123456 | 混合角色 | 全部菜单 | 测试混合角色 |

**超级管理员账号**（需要单独创建）：
- 账号：`admin`
- 密码：`Admin123456`
- 权限：所有菜单和功能

---

## ⚙️ 前置要求

### 1. 数据库配置

确保 `.env` 文件中的数据库配置正确：

```env
# 数据库配置
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=your_password
DB_DATABASE=userecho
```

### 2. Python 环境

- Python 3.10+
- 虚拟环境（脚本会自动创建）
- 依赖包（脚本会自动安装）

### 3. 数据库准备

确保 PostgreSQL 数据库已创建：

```sql
CREATE DATABASE userecho;
```

---

## 🔍 手动执行（如果一键脚本失败）

如果一键脚本失败，可以手动按顺序执行：

### 步骤 1：进入目录并激活虚拟环境

```bash
cd server/backend
source .venv/Scripts/activate  # Windows Git Bash
# 或
source .venv/bin/activate      # Linux/Mac
```

### 步骤 2：执行数据库迁移

```bash
alembic upgrade head
```

### 步骤 3：初始化业务菜单和角色

```bash
python scripts/init_business_menus.py
```

### 步骤 4：创建测试用户

**方式 1：使用 SQL 脚本（推荐）**
```bash
psql -h localhost -U postgres -d userecho -f sql/postgresql/init_test_users.sql
```

**方式 2：使用 Shell 脚本**
```bash
./create_test_users.sh
```

### 步骤 5：验证结果

```bash
python scripts/update_role_menus.py
```

---

## ⚠️ 注意事项

### 1. 重复执行安全

所有脚本都是**幂等的（idempotent）**，多次执行不会重复创建数据：
- 已存在的菜单会被跳过或更新
- 已存在的角色会被跳过
- 已存在的用户会被跳过

### 2. 数据库重置

如果需要完全重置数据库：

```sql
-- ⚠️ 危险操作：删除所有数据
DROP DATABASE userecho;
CREATE DATABASE userecho;
```

然后重新运行初始化脚本。

### 3. 虚拟环境

脚本会自动激活虚拟环境。如果虚拟环境不存在，会自动创建。

### 4. 依赖安装

脚本会自动检查并安装缺失的依赖包。

---

## 🐛 故障排查

### 问题 1：数据库连接失败

**错误提示**：
```
❌ 数据库连接失败
```

**解决方法**：
1. 检查 `.env` 文件中的数据库配置
2. 确保 PostgreSQL 服务已启动
3. 确保数据库已创建

### 问题 2：Alembic 迁移失败

**错误提示**：
```
❌ 数据库迁移失败
```

**解决方法**：
1. 检查数据库用户是否有创建表的权限
2. 查看 Alembic 错误日志
3. 尝试手动执行：`alembic upgrade head`

### 问题 3：脚本执行权限不足（Linux/Mac）

**错误提示**：
```
Permission denied
```

**解决方法**：
```bash
chmod +x init_database.sh
```

### 问题 4：虚拟环境激活失败

**错误提示**：
```
❌ 虚拟环境激活失败
```

**解决方法**：
1. 删除现有虚拟环境：`rm -rf .venv`
2. 重新创建：`python -m venv .venv`
3. 重新运行脚本

### 问题 5：测试用户创建失败

**错误提示**：
```
⚠️  测试用户创建失败
```

**解决方法**：
1. 确保角色已创建（步骤 2 成功）
2. 手动执行 SQL 脚本：
   ```bash
   psql -U postgres -d userecho -f sql/postgresql/init_test_users.sql
   ```

---

## 📊 验证初始化结果

初始化完成后，可以使用以下 SQL 检查：

```sql
-- 检查所有表
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
ORDER BY table_name;

-- 检查业务菜单
SELECT id, title, path, sort 
FROM sys_menu 
WHERE path LIKE '/app/%' 
ORDER BY sort;

-- 检查业务角色
SELECT id, name, role_type, remark 
FROM sys_role 
WHERE role_type = 'business';

-- 检查测试用户
SELECT u.username, u.nickname, u.email, r.name as role_name
FROM sys_user u
LEFT JOIN sys_user_role ur ON u.id = ur.user_id
LEFT JOIN sys_role r ON ur.role_id = r.id
WHERE u.username IN ('sysadmin', 'pm', 'cs', 'dev', 'boss', 'hybrid')
ORDER BY u.username;
```

---

## 🔄 更新现有数据库

如果只需要更新菜单权限（不重置数据库）：

```bash
cd server/backend
source .venv/Scripts/activate
python scripts/update_role_menus.py
```

---

## 📚 相关文档

- [测试用户指南](../../docs/test-users-guide.md)
- [菜单权限指南](../../docs/development/menu-permission-guide.md)
- [数据库设计](../../docs/design/database-design.md)

---

## 📝 脚本说明

| 脚本文件 | 说明 | 适用系统 |
|---------|------|---------|
| `init_database.sh` | 一键初始化脚本 | Linux/Mac/Git Bash |
| `init_database.bat` | 一键初始化脚本 | Windows CMD/PowerShell |
| `scripts/init_business_menus.py` | 初始化业务菜单和角色 | 所有系统 |
| `scripts/update_role_menus.py` | 更新角色菜单权限 | 所有系统 |
| `sql/postgresql/init_test_users.sql` | 创建测试用户 SQL | 所有系统 |

---

**文档维护者：** 技术团队  
**最后更新：** 2025-12-26  
**状态：** 可用

