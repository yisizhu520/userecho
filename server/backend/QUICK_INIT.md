# 🚀 数据库一键初始化

## 快速开始

在 `server/backend` 目录下执行：

### Linux/Mac/Git Bash
```bash
./init_complete_database.sh
```

### Windows CMD
```cmd
init_complete_database.bat
```

### Windows PowerShell
```powershell
.\init_complete_database.bat
```

---

## 这个脚本做什么？

一条命令完成**完整数据库初始化**：

1. ✅ **系统基础数据**（`fba init`）
   - 创建表结构（`alembic upgrade head`）
   - 导入部门数据
   - 导入系统管理菜单（`/system/*`, `/log/*`, `/monitor/*`）
   - 创建 admin 超级管理员（密码：`Admin123456`）
   - 创建测试角色（FBA 原生）

2. ✅ **默认租户**
   - 创建 `default-tenant` 租户记录
   - 这是所有用户和业务数据的默认租户

3. ✅ **业务功能数据**
   - 创建业务菜单（`/app/*`）
   - 创建业务角色（PM、CS、开发、老板）

4. ✅ **测试用户**
   - 创建 6 个测试账号（统一密码：`Test123456`）
   - `sysadmin`（系统管理员）
   - `pm`（PM）
   - `cs`（CS）
   - `dev`（开发）
   - `boss`（老板）
   - `hybrid`（混合角色）

---

## ⚠️ 注意事项

- **破坏性操作**：会清空数据库所有数据
- **仅用于开发环境**：不要在生产环境执行
- **确保数据库连接正确**：检查 `.env` 文件配置

---

## 初始化后的账号

### 超级管理员
```
账号: admin
密码: Admin123456
权限: 全部系统管理功能
```

### 业务测试账号
```
账号      角色          密码            菜单权限
───────────────────────────────────────────────
sysadmin  系统管理员    Test123456      /admin/* 菜单
pm        PM            Test123456      /app/* 全部菜单
cs        CS            Test123456      /app/* 部分菜单
dev       开发          Test123456      /app/* 只读菜单
boss      老板          Test123456      /app/* 全部菜单
hybrid    混合角色      Test123456      全部菜单
```

---

## 旧脚本 vs 新脚本

| 脚本 | 系统数据 | 业务数据 | 测试用户 | 结果 |
|------|---------|---------|---------|------|
| `init_database.sh` | ❌ | ✅ | ✅ | 缺少系统管理功能 |
| `init_complete_database.sh` | ✅ | ✅ | ✅ | 完整可用系统 |

**推荐使用** `init_complete_database.sh` 进行完整初始化。

---

## 故障排查

### 数据库连接失败
```bash
# 测试数据库连接
python test_db_connection_simple.py
```

### 依赖缺失
```bash
# 使用 uv 安装依赖（推荐）
cd server && uv sync

# 或使用 pip
pip install -r requirements.txt
```

### 虚拟环境未激活
```bash
# Linux/Mac/Git Bash
source ../.venv/Scripts/activate

# Windows CMD
call ..\.venv\Scripts\activate.bat

# Windows PowerShell
..\.venv\Scripts\Activate.ps1
```

---

## 详细文档

- 完整说明：[INIT_COMPLETE_DATABASE.md](./INIT_COMPLETE_DATABASE.md)
- 数据库设计：[../../docs/design/database-design.md](../../docs/design/database-design.md)
- 测试用户指南：[../../docs/test-users-guide.md](../../docs/test-users-guide.md)
