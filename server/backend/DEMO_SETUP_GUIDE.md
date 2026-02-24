# Demo 环境初始化指南

本文档说明如何初始化和重置 Demo 环境。

## 📋 脚本说明

| 脚本 | 用途 | 使用场景 |
|------|------|---------|
| `setup_demo_full.sh` | **完整初始化** | 首次部署 Demo 环境 |
| `init_demo_data_only.sh` | **仅重置数据** | 定时重置、手动刷新数据 |

---

## 🚀 首次部署（完整初始化）

### 一键初始化

```bash
cd server/backend

# 一键完成所有步骤（推荐）
./setup_demo_full.sh
```

这个脚本会自动完成：
1. ✅ 数据库表结构迁移（Alembic）
2. ✅ 系统基础数据（角色、菜单、部门）
3. ✅ 业务基础数据（租户、看板、权限）
4. ✅ Demo 预置账号和示例数据

### 可选参数

```bash
# 跳过数据库迁移（如果已手动执行）
./setup_demo_full.sh --skip-migration

# 重置所有数据（危险！）
./setup_demo_full.sh --reset

# 静默模式（配合 cron 使用）
./setup_demo_full.sh --silent
```

---

## 🔄 定时重置（仅刷新 Demo 数据）

### 手动重置

```bash
cd server/backend

# 仅重置 Demo 账号和数据（不动系统表）
./init_demo_data_only.sh --reset
```

### 自动重置（Cron）

添加 cron 任务（每日凌晨 2 点）：

```bash
crontab -e

# 添加以下行
0 2 * * * cd /path/to/server/backend && ./init_demo_data_only.sh --reset --silent >> /var/log/demo-reset.log 2>&1
```

---

## 📊 初始化后验证

### 验证 Demo 账号

```bash
# 查看 Demo 用户
psql -d userecho_demo -c "SELECT username, nickname FROM sys_user WHERE username LIKE 'demo_%';"
```

预期输出：
```
  username  | nickname
------------+----------
 demo_po    | 张产品
 demo_ops   | 李运营
 demo_admin | 王管理
```

### 验证示例数据

```bash
# 查看看板数量
psql -d userecho_demo -c "SELECT COUNT(*) FROM ue_board WHERE tenant_id='default-tenant';"

# 查看反馈数量
psql -d userecho_demo -c "SELECT COUNT(*) FROM ue_feedback WHERE tenant_id='default-tenant';"
```

---

## 🔧 常见问题

### 问题 1：数据库连接失败

**症状**：脚本提示 "数据库连接失败"

**解决**：
1. 检查 `.env` 文件中的数据库配置
2. 确认 PostgreSQL 服务已启动
3. 验证数据库用户权限

```bash
# 测试数据库连接
psql -h localhost -U your_user -d userecho_demo -c "SELECT 1;"
```

### 问题 2：Redis 连接失败

**症状**：脚本提示 "Redis 连接失败"

**解决**：
1. 检查 Redis 服务是否启动：`redis-cli ping`
2. 检查 `.env` 中的 `REDIS_URL` 配置
3. 确认防火墙未阻止 Redis 端口

### 问题 3：系统角色缺失

**症状**：创建 Demo 用户时报错 "KeyError: 'PM'"

**解决**：
```bash
# 重新执行系统数据初始化
echo "y" | fba init
```

### 问题 4：默认租户缺失

**症状**：脚本报错 "未找到默认租户"

**解决**：
```bash
# 手动创建默认租户
python scripts/init_default_tenant.py
```

---

## 📝 手动执行步骤（仅供参考）

如果自动化脚本失败，可以手动执行：

```bash
cd server/backend

# 步骤 1: 数据库迁移
python ../db_migrate.py upgrade head

# 步骤 2: 系统基础数据
echo "y" | fba init

# 步骤 3: 业务基础数据
python scripts/init_default_tenant.py
python scripts/init_business_menus.py

# 步骤 4: Demo 数据
python scripts/create_demo_users.py
python scripts/init_demo_data.py
```

---

## 🎭 Demo 账号清单

| 账号 | 密码 | 角色 | 权限 |
|------|------|------|------|
| `demo_po` | `demo123456` | 产品负责人 | 看板、洞察、审批议题 |
| `demo_ops` | `demo123456` | 用户运营 | 反馈录入、客户管理、触发聚类 |
| `demo_admin` | `demo123456` | 系统管理员 | 用户管理、权限配置、看板设置 |

---

## 📚 相关文档

- [Demo 环境部署指南](../../docs/guides/deployment/demo-environment-guide.md)
- [数据库迁移指南](../../docs/development/mypy-integration-guide.md)
