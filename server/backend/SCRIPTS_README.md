# 数据库脚本使用指南

## 📁 可用脚本列表

### 🚀 一键初始化脚本

用于全新数据库的完整初始化。

**Linux/Mac/Git Bash:**
```bash
./init_database.sh
```

**Windows CMD:**
```cmd
init_database.bat
```

**功能：**
- 自动检查环境（虚拟环境、依赖、数据库连接）
- 执行数据库迁移
- 创建业务菜单和角色
- 创建测试用户
- 验证初始化结果

---

### 🔍 验证脚本

快速检查数据库初始化状态。

**Linux/Mac/Git Bash:**
```bash
./verify_database.sh
```

**Windows CMD:**
```cmd
verify_database.bat
```

**输出：**
- 数据库连接状态
- 菜单、角色、用户统计
- 测试用户详情
- 下一步建议

---

### 🔌 数据库连接测试

测试数据库配置是否正确。

```bash
source ../.venv/Scripts/activate
python test_db_connection_simple.py
```

**输出：**
- .env 文件检查
- 数据库配置信息
- 连接测试结果
- PostgreSQL/MySQL 版本

---

### 📋 Python 脚本

#### 1. 初始化业务菜单和角色

```bash
source ../.venv/Scripts/activate
python scripts/init_business_menus.py
```

**创建内容：**
- 反馈管理目录和子菜单
- 设置目录和子菜单
- 4 个业务角色（PM、CS、开发、老板）
- 角色菜单权限关联

---

#### 2. 创建测试用户

```bash
source ../.venv/Scripts/activate
python scripts/create_test_users.py
```

**创建用户：**
- sysadmin（系统管理员）
- pm（产品经理）
- cs（客户成功）
- dev（开发人员）
- boss（租户管理员）
- hybrid（混合角色）

**统一密码：** `Test123456`

---

#### 3. 更新角色菜单权限

```bash
source ../.venv/Scripts/activate
python scripts/update_role_menus.py
```

**功能：**
- 更新现有角色的菜单权限
- 重新分配菜单关联
- 验证权限设置

---

## 📊 使用场景

### 场景 1：全新数据库初始化

```bash
cd server/backend
./init_database.sh
```

一键完成所有初始化。

---

### 场景 2：验证数据库状态

```bash
cd server/backend
./verify_database.sh
```

快速检查初始化是否完成。

---

### 场景 3：仅更新菜单权限

```bash
cd server/backend
source ../.venv/Scripts/activate
python scripts/update_role_menus.py
```

不改动数据库，只更新角色菜单关联。

---

### 场景 4：测试数据库连接

```bash
cd server/backend
source ../.venv/Scripts/activate
python test_db_connection_simple.py
```

诊断数据库连接问题。

---

## 🛠️ 故障排查

### 问题 1：数据库连接失败

```bash
# 运行诊断
python test_db_connection_simple.py

# 检查 .env 文件
cat .env | grep DATABASE
```

---

### 问题 2：脚本执行失败

```bash
# 检查虚拟环境
source ../.venv/Scripts/activate
python --version

# 检查依赖
pip list | grep alembic
```

---

### 问题 3：部分初始化

```bash
# 验证状态
./verify_database.sh

# 重新运行特定步骤
python scripts/init_business_menus.py
python scripts/create_test_users.py
```

---

## 📚 相关文档

- [QUICK_START.md](./QUICK_START.md) - 快速开始指南
- [DATABASE_INIT.md](./DATABASE_INIT.md) - 完整初始化指南
- [DATABASE_INIT_SUMMARY.md](./DATABASE_INIT_SUMMARY.md) - 初始化总结

---

## ⚡ 快速命令参考

```bash
# 进入目录
cd server/backend

# 激活虚拟环境
source ../.venv/Scripts/activate    # Linux/Mac/Git Bash
call ..\.venv\Scripts\activate.bat  # Windows CMD

# 一键初始化
./init_database.sh                  # Linux/Mac/Git Bash
init_database.bat                   # Windows CMD

# 验证状态
./verify_database.sh                # Linux/Mac/Git Bash
verify_database.bat                 # Windows CMD

# 测试连接
python test_db_connection_simple.py

# 更新权限
python scripts/update_role_menus.py
```

---

**提示：** 所有脚本都是幂等的，可以安全地多次运行。
