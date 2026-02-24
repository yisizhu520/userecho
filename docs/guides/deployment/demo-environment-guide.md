# 回响演示环境部署指南

本文档详细说明如何部署和维护「回响」的演示环境 (Demo Mode)。

## 目录

1. [概述](#概述)
2. [架构设计](#架构设计)
3. [前置准备](#前置准备)
4. [后端部署](#后端部署)
5. [前端部署](#前端部署)
6. [数据初始化](#数据初始化)
7. [定时重置配置](#定时重置配置)
8. [验证清单](#验证清单)
9. [故障排查](#故障排查)

---

## 概述

演示环境是一个独立部署的系统实例，允许潜在用户无需注册即可体验「回响」的全部功能。

### 核心特性

| 特性 | 说明 |
|------|------|
| **角色快速切换** | 3 种预置角色，一键切换体验不同视角 |
| **禁用注册** | 仅允许使用预置账号登录 |
| **每日数据重置** | 凌晨 2 点自动重置，保证数据整洁 |
| **Turnstile 保护** | AI 功能接口添加人机验证，防滥用 |

### 预置角色

| 角色 | 账号 | 密码 | 核心功能 |
|------|------|------|---------|
| 产品负责人 | `demo_po` | `demo123456` | 看板、洞察、审批议题 |
| 用户运营 | `demo_ops` | `demo123456` | 反馈录入、客户管理、聚类 |
| 系统管理员 | `demo_admin` | `demo123456` | 用户管理、权限配置 |

---

## 架构设计

```
┌──────────────────────────────────────────────────────────┐
│                    demo.userecho.app                      │
├──────────────────────────────────────────────────────────┤
│ Cloudflare (DNS + Turnstile)                             │
├───────────────────────┬──────────────────────────────────┤
│   前端 (Nginx)        │        后端 (FastAPI)            │
│   front/.env.demo     │        server/.env.demo          │
├───────────────────────┴──────────────────────────────────┤
│                    基础设施                               │
│   ┌────────────────┐  ┌────────────────┐                 │
│   │ PostgreSQL     │  │ Redis          │                 │
│   │ userecho_demo  │  │ db=1           │                 │
│   └────────────────┘  └────────────────┘                 │
└──────────────────────────────────────────────────────────┘
```

---

## 前置准备

### 1. 创建 Cloudflare Turnstile

1. 登录 [Cloudflare Dashboard](https://dash.cloudflare.com/)
2. 进入 **Turnstile** 服务
3. 创建新站点，填写：
   - 站点名称：`回响-演示`
   - 域名：`demo.userecho.app`
   - Widget 模式：`Managed`
4. 记录生成的：
   - **Site Key**（前端使用）
   - **Secret Key**（后端使用）

### 2. 准备数据库

```bash
# 创建 Demo 专用数据库
psql -U postgres
CREATE DATABASE userecho_demo;
CREATE USER demo_user WITH PASSWORD 'your-secure-password';
GRANT ALL PRIVILEGES ON DATABASE userecho_demo TO demo_user;
```

### 3. 准备 Redis

Demo 环境建议使用独立的 Redis 数据库（如 db=1）以隔离数据。

---

## 后端部署

### 步骤 1：配置环境变量

编辑 `server/.env.demo`：

```bash
# ==================== 应用配置 ====================
DEMO_MODE=true
ENVIRONMENT=demo
FASTAPI_TITLE=回响-演示版

# ==================== 安全配置 ====================
ALLOW_REGISTRATION=false

# Cloudflare Turnstile（从 Cloudflare 控制台获取）
TURNSTILE_ENABLED=true
TURNSTILE_SECRET_KEY=0x4AAAAAAxxxxxxxxxxxxxxxxxxxxxxxx

# ==================== 数据库配置 ====================
DATABASE_TYPE=postgresql
DATABASE_HOST=your-db-host
DATABASE_PORT=5432
DATABASE_USER=demo_user
DATABASE_PASSWORD=your-secure-password
DATABASE_SCHEMA=userecho_demo

# ==================== Redis 配置 ====================
REDIS_URL=redis://:password@your-redis-host:6379/1

# ==================== 数据重置配置 ====================
DEMO_DATA_RESET_ENABLED=true
DEMO_DATA_RESET_CRON=0 2 * * *
```

### 步骤 2：执行数据库迁移

```bash
cd server/backend

# 激活虚拟环境
source ../.venv/Scripts/activate  # Windows
# source ../.venv/bin/activate    # Linux/Mac

# 使用 Demo 环境配置
export ENV_FILE=.env.demo

# 执行迁移
alembic upgrade head
```

### 步骤 3：初始化 Demo 环境（一键完成）

```bash
# 一键完成所有初始化步骤（推荐）
./setup_demo_full.sh
```

此脚本会自动完成：
- ✅ 系统基础数据初始化（角色、菜单、部门）
- ✅ 默认租户创建
- ✅ 业务菜单和权限初始化
- ✅ Demo 预置账号和示例数据创建

### 步骤 4：手动初始化（可选）

如果需要手动控制每个步骤：

```bash
# 4.1 初始化系统数据
echo "y" | fba init

# 4.2 初始化默认租户和业务菜单
python scripts/init_default_tenant.py
python scripts/init_business_menus.py

# 4.3 初始化 Demo 数据
./init_demo_data_only.sh
```

### 步骤 5：启动服务

```bash
# 使用 Demo 环境配置启动
ENV_FILE=.env.demo uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

---

## 前端部署

### 步骤 1：配置环境变量

编辑 `front/apps/web-antd/.env.demo`：

```bash
NODE_ENV=production
VITE_APP_TITLE=回响-演示版
VITE_GLOB_API_URL=https://demo-api.userecho.app
VITE_APP_NAMESPACE=userecho-demo
VITE_DEMO_MODE=true
VITE_TURNSTILE_SITE_KEY=0x4AAAAAAxxxxxxxxxxxxxxxxxxxxxxxx
VITE_DEVTOOLS=false
```

### 步骤 2：构建项目

```bash
cd front

# 安装依赖
pnpm install

# 使用 Demo 配置构建
pnpm build:demo
# 或手动指定：
# NODE_ENV=production VITE_MODE=demo pnpm --filter @vben/web-antd build
```

### 步骤 3：配置 Nginx

```nginx
server {
    listen 80;
    server_name demo.userecho.app;

    root /var/www/demo/dist;
    index index.html;

    # 前端路由支持
    location / {
        try_files $uri $uri/ /index.html;
    }

    # API 代理
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## 数据初始化

### 首次初始化（推荐）

```bash
cd server/backend

# 一键完成所有步骤
./setup_demo_full.sh
```

此脚本会自动完成：
1. ✅ 数据库表结构迁移
2. ✅ 系统基础数据（角色、菜单、部门）
3. ✅ 业务基础数据（租户、看板、权限）
4. ✅ Demo 预置账号和示例数据

### 仅重置 Demo 数据

```bash
cd server/backend

# 仅重置账号和数据（不动系统表）
./init_demo_data_only.sh --reset
```

### 手动分步初始化

```bash
# 步骤 1: 仅创建账号
python scripts/create_demo_users.py

# 步骤 2: 仅初始化数据
python scripts/init_demo_data.py

# 步骤 3: 重置模式
python scripts/create_demo_users.py --reset
python scripts/init_demo_data.py --reset
```

---

## 定时重置配置

### 方式 1：Cron（推荐）

```bash
# 编辑 crontab
crontab -e

# 添加每日凌晨 2 点重置任务
0 2 * * * cd /path/to/server/backend && ./init_demo_data_only.sh --reset --silent >> /var/log/demo-reset.log 2>&1
```

### 方式 2：Celery Beat（可选）

在 `celery_config.py` 中添加：

```python
CELERY_BEAT_SCHEDULE = {
    'reset-demo-data': {
        'task': 'demo.reset_data',
        'schedule': crontab(hour=2, minute=0),
    },
}
```

---

## 验证清单

部署完成后，按以下清单逐项验证：

### 功能验证

- [ ] 访问 `https://demo.userecho.app/demo` 显示欢迎页
- [ ] 三个角色都能成功登录
- [ ] 角色切换浮动组件正常工作
- [ ] Demo Banner 显示"演示模式"提示
- [ ] 注册入口已隐藏

### 安全验证

- [ ] AI 聚类接口触发 Turnstile 验证
- [ ] 洞察生成接口触发 Turnstile 验证
- [ ] 直接访问 `/auth/register` 返回友好提示

### 数据验证

- [ ] 预置客户数据显示正常
- [ ] 预置反馈数据显示正常
- [ ] 预置议题数据显示正常

---

## 故障排查

### 问题 1：Turnstile 验证失败

**症状**：调用 AI 接口返回 403

**排查**：
1. 检查 `TURNSTILE_SECRET_KEY` 是否正确
2. 检查域名是否与 Cloudflare 配置一致
3. 查看后端日志中的验证错误信息

### 问题 2：角色切换失败

**症状**：点击角色后无响应

**排查**：
1. 检查 Demo 用户是否创建成功
2. 检查 `/api/v1/demo/switch-role` 接口响应
3. 确认用户密码与 `DEMO_PASSWORD` 一致

### 问题 3：数据重置失败

**症状**：cron 任务未执行

**排查**：
1. 检查脚本执行权限：`chmod +x init_demo_environment.sh`
2. 检查日志文件：`/var/log/demo-reset.log`
3. 手动执行验证：`./init_demo_environment.sh --reset`

---

## 相关文件

| 类型 | 路径 |
|------|------|
| **后端配置** | `server/.env.demo` |
| **前端配置** | `front/apps/web-antd/.env.demo` |
| **Turnstile 模块** | `server/backend/common/security/turnstile.py` |
| **Demo API** | `server/backend/app/admin/api/v1/demo.py` |
| **完整初始化脚本** | `server/backend/setup_demo_full.sh` |
| **数据重置脚本** | `server/backend/init_demo_data_only.sh` |
| **账号初始化** | `server/backend/scripts/create_demo_users.py` |
| **数据初始化** | `server/backend/scripts/init_demo_data.py` |
| **欢迎页组件** | `front/apps/web-antd/src/views/demo/DemoWelcome.vue` |
| **角色切换组件** | `front/apps/web-antd/src/components/demo/DemoRoleSwitcher.vue` |
