# Dokploy 部署指南

本文档说明如何通过 GitHub Actions + Dokploy 部署回响应用。

## 架构概览

```
GitHub Push → GitHub Actions → GHCR (镜像仓库) → Dokploy (Webhook) → 容器部署
```

## 核心特性

- **统一镜像**：使用同一个 Docker 镜像，通过环境变量切换 demo/prod 模式
- **运行时配置**：前端配置（API URL、Turnstile 密钥等）在容器启动时动态生成
- **环境变量驱动**：所有配置通过环境变量控制，符合 12-Factor 原则

## 前置条件

1. **外部服务**：
   - PostgreSQL 数据库（如 Supabase、Neon、RDS）
   - Redis（如 Upstash、Render Redis）

2. **Dokploy 服务器**：已安装并运行 Dokploy

3. **GitHub Repository 设置**：
   - Settings → Actions → General → Workflow permissions → Read and write permissions

---

## 部署步骤

### 1. 配置 GitHub Secrets

在 GitHub Repository → Settings → Secrets and variables → Actions 中添加：

| Secret 名称 | 说明 |
|------------|------|
| `DOKPLOY_WEBHOOK_URL` | Dokploy 应用的 Webhook URL（见下方说明） |

### 2. 在 Dokploy 创建应用

#### 生产环境

1. 登录 Dokploy 面板
2. 创建新项目（Project），命名如 `userecho-prod`
3. 添加 **Compose** 类型应用
4. 选择 GitHub 仓库，指定 `docker-compose.dokploy.yml` 文件
5. 复制 **Webhook URL** 到 GitHub Secrets（名称：`DOKPLOY_WEBHOOK_URL`）

#### Demo 环境

1. 在同一个或新的项目中创建另一个 Compose 应用
2. 同样选择 `docker-compose.dokploy.yml` 文件
3. 复制 **Webhook URL** 到 GitHub Secrets（名称：`DOKPLOY_DEMO_WEBHOOK_URL`）

### 3. 配置环境变量

在 Dokploy 应用的 Environment 页面添加以下变量：

#### 生产环境配置

```env
# ======= 镜像标签 =======
IMAGE_TAG=master

# ======= 前端配置 =======
VITE_APP_TITLE=回响
VITE_GLOB_API_URL=/
VITE_APP_NAMESPACE=userecho-admin
VITE_DEVTOOLS=false
VITE_DEMO_MODE=false

# ======= 后端环境配置 =======
ENVIRONMENT=prod
DEMO_MODE=false
ALLOW_REGISTRATION=true

# ======= 数据库配置 =======
DATABASE_TYPE=postgresql
DATABASE_HOST=your-db.supabase.co
DATABASE_PORT=5432
DATABASE_USER=postgres
DATABASE_PASSWORD=your-password

# ======= Redis 配置 =======
REDIS_HOST=your-redis.upstash.io
REDIS_PORT=6379
REDIS_PASSWORD=your-redis-password
REDIS_DATABASE=0

# ======= Celery 配置 =======
CELERY_BROKER_REDIS_DATABASE=1

# ======= 安全密钥 =======
TOKEN_SECRET_KEY=your-jwt-secret-key
OPERA_LOG_ENCRYPT_SECRET_KEY=your-encrypt-key
```

#### Demo 环境额外配置

Demo 环境在上述基础上，修改以下变量：

```env
# ======= 镜像标签 =======
IMAGE_TAG=demo

# ======= 前端配置 =======
VITE_APP_TITLE=回响-演示
VITE_DEMO_MODE=true
VITE_TURNSTILE_SITE_KEY=0x4AAAxxxxxxxxxxxxxxxx

# ======= 后端环境配置 =======
ENVIRONMENT=demo
DEMO_MODE=true
ALLOW_REGISTRATION=false

# ======= Turnstile 保护 =======
TURNSTILE_ENABLED=true
TURNSTILE_SECRET_KEY=0x4AAAxxxxxxxxxxxxxxxx

# ======= 数据重置配置 =======
DEMO_DATA_RESET_ENABLED=true
DEMO_DATA_RESET_CRON=0 2 * * *

# ======= 使用独立的 Redis Database =======
REDIS_DATABASE=1
CELERY_BROKER_REDIS_DATABASE=2
```

### 4. 触发部署

推送代码到 `main` 分支即可自动触发部署，或在 GitHub Actions 页面手动触发。

---

## 服务说明

| 服务 | 端口 | 作用 |
|------|------|------|
| `fba_ui` | 80 | Nginx 前端 + API 反向代理 |
| `fba_server` | 8001 | FastAPI 后端主服务 |
| `fba_celery_worker` | - | 异步任务执行器 |
| `fba_celery_beat` | - | 定时任务调度器 |
| `fba_celery_flower` | 8555 | 任务监控面板（可选） |

---

## 常见问题

### Q: 镜像拉取失败 (401 Unauthorized)

确保 GHCR 仓库是 public，或在 Dokploy 配置 GitHub Container Registry 凭证。

### Q: 容器无法连接数据库

1. 检查 `DATABASE_HOST` 是否可从 Dokploy 服务器访问
2. 确认数据库防火墙允许 Dokploy 服务器 IP

### Q: Celery Worker 未执行任务

1. 检查 Redis 连接配置
2. 查看 Worker 容器日志：`docker logs fba_celery_worker`

---

## 数据库迁移

首次部署后需要执行数据库迁移：

```bash
# 进入 server 容器
docker exec -it fba_server bash

# 执行迁移
cd /fba/backend
alembic upgrade head
```

---

## 验证部署

1. **前端**：访问 `http://your-domain.com`
2. **API 健康检查**：`curl http://your-domain.com/api/v1/health`
3. **Flower 面板**：`http://your-domain.com:8555`（如已启用）

---

## 环境变量说明

### 前端环境变量（VITE_*）

这些变量在容器启动时动态生成前端配置文件 `_app.config.js`：

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `VITE_APP_TITLE` | 应用标题 | `回响` |
| `VITE_GLOB_API_URL` | API 基础路径 | `/` |
| `VITE_APP_NAMESPACE` | 应用命名空间 | `userecho-admin` |
| `VITE_DEVTOOLS` | 是否启用开发工具 | `false` |
| `VITE_DEMO_MODE` | 是否为 Demo 模式 | `false` |
| `VITE_TURNSTILE_SITE_KEY` | Cloudflare Turnstile Site Key | 空 |

### 后端环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `ENVIRONMENT` | 运行环境 | `prod` |
| `DEMO_MODE` | 是否启用 Demo 模式 | `false` |
| `ALLOW_REGISTRATION` | 是否允许注册 | `true` |
| `TURNSTILE_ENABLED` | 是否启用 Turnstile | `false` |
| `DEMO_DATA_RESET_ENABLED` | 是否启用数据重置 | `false` |

---

## 相关文件

| 文件 | 作用 |
|------|------|
| `.github/workflows/deploy.yml` | 生产环境部署 Workflow |
| `.github/workflows/deploy-demo.yml` | Demo 环境部署 Workflow |
| `docker-compose.dokploy.yml` | 统一的 docker-compose 配置 |
| `Dockerfile` | 统一的 Dockerfile |
| `deploy/monolith/gen_app_config.sh` | 前端配置生成脚本 |
