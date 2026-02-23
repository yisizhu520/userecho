# Dokploy 部署指南

本文档说明如何通过 GitHub Actions + Dokploy 部署回响应用。

## 架构概览

```
GitHub Push → GitHub Actions → GHCR (镜像仓库) → Dokploy (Webhook) → 容器部署
```

## 前置条件

1. **外部服务**：
   - PostgreSQL 数据库（如 Supabase、Neon、RDS）
   - Redis（如 Upstash、Render Redis）
   - RabbitMQ（如 CloudAMQP）

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

1. 登录 Dokploy 面板
2. 创建新项目（Project）
3. 添加 **Compose** 类型应用
4. 选择 GitHub 仓库，指定 `docker-compose.dokploy.yml` 文件
5. 复制 **Webhook URL** 到 GitHub Secrets

### 3. 配置环境变量

在 Dokploy 应用的 Environment 页面添加以下变量：

```env
# GitHub Repository（用于拉取镜像）
GITHUB_REPOSITORY=yisizhu520/userecho

# 运行环境
ENVIRONMENT=prod

# 数据库配置
DATABASE_TYPE=postgresql
DATABASE_HOST=your-db.supabase.co
DATABASE_PORT=5432
DATABASE_USER=postgres
DATABASE_PASSWORD=your-password

# Redis 配置
REDIS_HOST=your-redis.upstash.io
REDIS_PORT=6379
REDIS_PASSWORD=your-redis-password
REDIS_DATABASE=0

# RabbitMQ 配置
CELERY_RABBITMQ_HOST=your-rabbitmq.cloudamqp.com
CELERY_RABBITMQ_PORT=5672
CELERY_RABBITMQ_USERNAME=guest
CELERY_RABBITMQ_PASSWORD=guest
CELERY_BROKER_REDIS_DATABASE=1

# 安全密钥（使用随机生成的字符串）
TOKEN_SECRET_KEY=your-jwt-secret-key
OPERA_LOG_ENCRYPT_SECRET_KEY=your-encrypt-key
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

1. 检查 RabbitMQ 连接配置
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

## Demo 演示环境部署

Demo 环境是一个独立的演示实例，具有以下特性：
- **DEMO_MODE 启用**：角色快速切换、禁用注册
- **Turnstile 保护**：AI 接口人机验证防滥用
- **每日数据重置**：凌晨 2 点自动重置数据

### 额外的 GitHub Secret

| Secret 名称 | 说明 |
|------------|------|
| `DOKPLOY_DEMO_WEBHOOK_URL` | Demo 应用的 Dokploy Webhook URL |

### Demo 专用环境变量

除了标准环境变量外，还需配置：

```env
# Demo 模式
DEMO_MODE=true
ALLOW_REGISTRATION=false

# Turnstile 保护
TURNSTILE_ENABLED=true
TURNSTILE_SECRET_KEY=0x4AAAxxxxxxxxxxxxxxxx

# 数据重置
DEMO_DATA_RESET_ENABLED=true
DEMO_DATA_RESET_CRON=0 2 * * *
```

### 相关文件

| 文件 | 作用 |
|------|------|
| `.github/workflows/deploy-demo.yml` | Demo 部署 Workflow |
| `docker-compose.demo.yml` | Demo docker-compose |
| `front/Dockerfile.demo` | Demo 前端 Dockerfile |
| `docs/demo-environment-guide.md` | 完整的 Demo 配置指南 |
