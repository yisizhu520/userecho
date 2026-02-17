# 🚀 一键数据库初始化脚本使用指南

## 📋 优化特性

### ✨ 新增自动化功能

优化后的脚本已支持：

1. **自动创建数据库** - 如果 `userecho` 数据库不存在，自动创建
2. **自动安装 pgvector 扩展** - 自动检查并安装 vector 扩展
3. **智能 Redis 配置** - 本地 Redis 不可用时自动切换到 Upstash
4. **UTF-8 编码支持** - 完美支持 Windows 中文输出

### 🎯 使用场景

- ✅ 首次安装系统
- ✅ 重置数据库（清空所有数据）
- ✅ 开发环境快速搭建
- ✅ 测试环境准备

---

## 🚀 快速开始

### 步骤 1：准备配置文件

确保 `server/backend/.env` 文件已配置数据库连接信息：

```bash
DATABASE_TYPE=postgresql
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_USER=postgres
DATABASE_PASSWORD=your_password
DATABASE_SCHEMA=userecho
```

**注意：**
- 数据库 `userecho` 可以不存在，脚本会自动创建
- pgvector 扩展可以未安装，脚本会自动安装

### 步骤 2：运行初始化脚本

```bash
cd server/backend

# Linux/Mac/Git Bash
chmod +x init_complete_database.sh
./init_complete_database.sh

# Windows CMD/PowerShell
init_complete_database.bat
```

### 步骤 3：等待完成

脚本将自动执行以下步骤：

```
【环境准备】（自动）
  ✅ 检查并创建数据库（如果不存在）
  ✅ 安装 pgvector 扩展
  ✅ 配置 Redis 连接

【数据初始化】
  1️⃣ fba init - 初始化系统基础数据
  2️⃣ 创建默认租户（default-tenant）
  3️⃣ 创建业务菜单和角色
  4️⃣ 创建测试用户
  5️⃣ 验证初始化结果
```

---

## 📊 初始化结果

### 最终数据统计

```
🏢 默认租户: 默认租户 (default-tenant)
🏢 部门数量: 1
📋 系统菜单数量: 8
📱 业务菜单数量: 12
👥 角色数量: 5
🧑 用户数量: 8
```

### 可用账号

#### 🔐 超级管理员
```
账号: admin
密码: Admin123456
权限: 全部系统管理功能
```

#### 👥 业务测试账号（密码：`Test123456`）
```
账号       角色         菜单权限
────────────────────────────────────────
sysadmin  系统管理员    /admin/* 菜单
pm        PM          /app/* 全部菜单
cs        CS          /app/* 部分菜单
dev       开发         /app/* 只读菜单
boss      老板         /app/* 全部菜单
hybrid    混合角色      全部菜单
```

---

## 🔧 技术细节

### 环境准备脚本

脚本使用 `scripts/setup_database_environment.py` 自动处理：

1. **数据库创建**
   ```python
   # 连接 postgres 默认数据库
   # 检查目标数据库是否存在
   # 不存在则创建
   ```

2. **pgvector 扩展安装**
   ```python
   # 连接目标数据库
   # 检查 vector 扩展是否存在
   # 不存在则执行 CREATE EXTENSION vector
   ```

3. **Redis 配置**
   ```python
   # 检查 REDIS_URL 环境变量
   # 测试本地 Redis 连接
   # 失败则切换到 Upstash Redis
   ```

### 支持的 Redis 配置

脚本智能识别以下 Redis 配置：

1. **REDIS_URL** - 优先使用（Upstash、云 Redis 等）
2. **本地 Redis** - REDIS_HOST + REDIS_PORT
3. **自动切换** - 本地不可用时启用注释的 REDIS_URL

---

## ⚠️ 注意事项

### 数据清空警告

**脚本会清空数据库所有数据！**

执行前确认：
- ✅ 当前数据库可以清空
- ✅ 重要数据已备份
- ✅ 这是开发/测试环境

### 权限要求

数据库用户需要以下权限：
- `CREATE DATABASE` - 创建数据库
- `CREATE EXTENSION` - 安装扩展
- 完整的表操作权限

### Redis 配置

如果本地 Redis 不可用且未配置 Upstash：
- 脚本会警告但继续执行
- `fba init` 可能会失败
- 建议先配置 Redis

---

## 🛠️ 故障排查

### 问题 1：数据库连接失败

**可能原因：**
- PostgreSQL 服务未启动
- 数据库配置错误
- 防火墙阻止连接

**解决方案：**
```bash
# 检查 PostgreSQL 服务状态
# Windows: services.msc 查找 PostgreSQL
# Linux: systemctl status postgresql
# Mac: brew services list

# 测试连接
python test_db_connection_simple.py
```

### 问题 2：pgvector 扩展安装失败

**可能原因：**
- PostgreSQL 未安装 pgvector 扩展包
- 用户没有 CREATE EXTENSION 权限

**解决方案：**
```bash
# 使用超级用户手动安装
psql -U postgres -d userecho -c "CREATE EXTENSION vector;"
```

### 问题 3：Redis 连接失败

**可能原因：**
- Redis 服务未启动
- Redis 配置错误

**解决方案：**
```bash
# 启用 Upstash Redis（推荐）
# 在 .env 中取消注释 REDIS_URL

# 或启动本地 Redis
# Windows: redis-server.exe
# Linux/Mac: redis-server
```

### 问题 4：Windows 编码问题

**表现：**
- 乱码输出
- Emoji 显示异常

**解决方案：**
脚本已自动处理，如果仍有问题：
```bash
# 在终端执行前设置
set PYTHONIOENCODING=utf-8
```

---

## 📚 相关文档

- [完整初始化指南](INIT_COMPLETE_DATABASE.md)
- [数据库初始化详解](DATABASE_INIT.md)
- [菜单权限系统](../../docs/development/menu-permission-guide.md)
- [租户配置系统](../../docs/development/tenant-config-system.md)

---

## 🎉 完成后

数据库初始化完成后，您可以：

1. **启动后端服务**
   ```bash
   cd server/backend
   fba run
   ```

2. **启动前端服务**
   ```bash
   cd front
   pnpm dev
   ```

3. **访问系统**
   - 后端 API: http://localhost:8000
   - 前端界面: http://localhost:5555

4. **使用测试账号登录**
   - 超级管理员: admin / Admin123456
   - 业务账号: pm / Test123456

祝您使用愉快！ 🎊
