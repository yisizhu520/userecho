# 数据库快速开始指南

## ✅ 您的数据库已初始化完成！

当前状态：
- ✅ 菜单: 8 个
- ✅ 角色: 5 个
- ✅ 测试用户: 6 个

---

## 🚀 启动服务

### 1. 启动后端

```bash
cd server/backend
source ../.venv/Scripts/activate  # Windows Git Bash
# 或
source ../.venv/bin/activate      # Linux/Mac

python run.py
```

### 2. 启动前端

```bash
cd front
pnpm dev
```

---

## 🔑 测试账号

**统一密码**: `Test123456`

| 账号 | 角色 | 用途 |
|------|------|------|
| `pm` | PM | 产品经理，全部业务功能 |
| `cs` | CS | 客户成功，部分功能 |
| `dev` | 开发 | 开发人员，只读 |
| `boss` | 老板 | 租户管理员 |
| `sysadmin` | 系统管理员 | 系统管理 |
| `hybrid` | 混合角色 | 系统+业务 |

---

## 🛠️ 常用脚本

### 验证数据库状态

```bash
cd server/backend
./verify_database.sh      # Linux/Mac/Git Bash
verify_database.bat       # Windows CMD
```

### 测试数据库连接

```bash
cd server/backend
source ../.venv/Scripts/activate
python test_db_connection_simple.py
```

### 重新初始化数据库

```bash
cd server/backend
./init_database.sh        # Linux/Mac/Git Bash
init_database.bat         # Windows CMD
```

### 更新角色菜单权限

```bash
cd server/backend
source ../.venv/Scripts/activate
python scripts/update_role_menus.py
```

---

## 📚 详细文档

- [DATABASE_INIT.md](./DATABASE_INIT.md) - 完整初始化指南
- [DATABASE_INIT_SUMMARY.md](./DATABASE_INIT_SUMMARY.md) - 本次初始化总结

---

## 🎯 下一步

1. ✅ 数据库已就绪
2. 🚀 启动后端和前端服务
3. 🔑 使用测试账号登录
4. 🎨 开始开发

---

**快速帮助**：
- 如果忘记密码：所有测试账号密码都是 `Test123456`
- 如果需要重置：运行 `./init_database.sh` 重新初始化
- 如果遇到问题：查看 [DATABASE_INIT.md](./DATABASE_INIT.md)
