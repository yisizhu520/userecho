<div align="center">

<h1>userecho</h1>

<p>开源的用户反馈管理与洞察平台 · An Open-Source User Feedback Analytics Platform</p>

[![License](https://img.shields.io/github/license/yisizhu520/userecho)](./LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![Vue](https://img.shields.io/badge/Vue-3.x-42b883?logo=vuedotjs)](https://vuejs.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16%2B-336791?logo=postgresql)](https://www.postgresql.org)
[![Docker](https://img.shields.io/badge/Docker-ready-2496ED?logo=docker)](./docker-compose.dokploy.yml)

[English](#english) | [中文](#中文)

</div>

---

## 中文

### 简介

**userecho** 是一个开源的用户反馈收集与分析平台，帮助产品团队：

- 📥 **收集反馈** — 通过嵌入式 Widget 或 API 收集用户反馈
- 🤖 **AI 聚类** — 自动将相似反馈聚合成主题，发现高优先级需求
- 📊 **洞察分析** — 可视化反馈趋势，量化用户需求的影响范围
- 🏢 **多租户** — 支持多工作空间，适合 SaaS 场景

### 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | FastAPI · SQLAlchemy 2.0 · PostgreSQL + pgvector · Redis · Celery |
| 前端 | Vue 3 · Vben Admin · Ant Design Vue · TypeScript |
| AI   | OpenAI / DeepSeek / 智谱 GLM / 火山引擎 (Embedding + Chat) |
| 部署 | Docker · Nginx (单镜像 Monolithic) |

### 快速开始

#### 前置要求

- Docker & Docker Compose
- PostgreSQL 16+ (with pgvector extension)
- Redis 6+

#### 1. 克隆仓库

```bash
git clone https://github.com/yisizhu520/userecho.git
cd userecho
```

#### 2. 配置环境变量

```bash
cp server/backend/.env.example server/backend/.env
# 编辑 .env，填写数据库、Redis、AI API Key 等配置
```

关键配置项说明：

```env
# 数据库
DATABASE_HOST=localhost
DATABASE_PASSWORD=your_password

# AI 提供商（选择一个或多个）
DEEPSEEK_API_KEY=sk-your-key        # 仅支持 Chat
OPENAI_API_KEY=sk-your-key          # 支持 Embedding + Chat
AI_DEFAULT_PROVIDER=deepseek        # deepseek / openai / glm / volcengine
```

> 完整配置说明见 [docs/guides/ai-provider/configuration.md](docs/guides/ai-provider/configuration.md)

#### 3. 一键启动（开发环境）

```bash
cd server
docker compose up -d
```

#### 4. 初始化数据库

```bash
cd server
python db_migrate.py upgrade head
```

访问 `http://localhost:8000/api/v1/docs` 查看 API 文档。

### 项目结构

```
userecho/
├── front/          # Vue 3 前端（Vben Admin + Ant Design Vue）
│   ├── apps/       # 应用入口
│   └── packages/   # 通用组件
├── server/         # Python 后端
│   ├── backend/    # FastAPI 应用代码
│   │   ├── app/    # 业务模块（admin / userecho）
│   │   ├── alembic/# 数据库迁移
│   │   └── plugin/ # 插件（email / oauth2）
│   └── deploy/     # 部署配置
├── docs/           # 项目文档
└── deploy/         # 生产部署配置
```

### 文档

详细文档见 [docs/](./docs/README.md)：

- [架构设计](docs/architecture/) — 数据库 ER 图、多租户模型、插件系统
- [AI 提供商配置](docs/guides/ai-provider/) — 各 AI 服务商接入指南
- [部署指南](docs/guides/deployment/) — Dokploy / Docker 部署
- [开发指南](docs/development/) — 本地开发、代码规范

### 贡献

欢迎提交 Issue 和 Pull Request！请先阅读 [CONTRIBUTING.md](./server/CONTRIBUTING.md)。

### 安全

发现安全漏洞？请阅读 [SECURITY.md](./SECURITY.md) 了解负责任披露流程，**不要**直接创建公开 Issue。

### 许可证

[MIT License](./LICENSE)

---

## English

### Introduction

**userecho** is an open-source user feedback collection and analytics platform that helps product teams:

- 📥 **Collect Feedback** — via embeddable Widget or API
- 🤖 **AI Clustering** — automatically group similar feedback into topics, surface high-priority needs
- 📊 **Insights** — visualize feedback trends and quantify user demand
- 🏢 **Multi-tenant** — multiple workspaces, built for SaaS

### Tech Stack

| Layer    | Technology |
|----------|-----------|
| Backend  | FastAPI · SQLAlchemy 2.0 · PostgreSQL + pgvector · Redis · Celery |
| Frontend | Vue 3 · Vben Admin · Ant Design Vue · TypeScript |
| AI       | OpenAI / DeepSeek / GLM / Volcengine (Embedding + Chat) |
| Deploy   | Docker · Nginx (Monolithic single image) |

### Quick Start

#### Prerequisites

- Docker & Docker Compose
- PostgreSQL 16+ (with pgvector extension)
- Redis 6+

#### 1. Clone the repo

```bash
git clone https://github.com/yisizhu520/userecho.git
cd userecho
```

#### 2. Configure environment variables

```bash
cp server/backend/.env.example server/backend/.env
# Edit .env: fill in DB, Redis, AI API Key, etc.
```

#### 3. Start (development)

```bash
cd server
docker compose up -d
```

#### 4. Run database migrations

```bash
cd server
python db_migrate.py upgrade head
```

### Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](./server/CONTRIBUTING.md) first.

### Security

If you discover a security vulnerability, please see [SECURITY.md](./SECURITY.md) for our responsible disclosure process. Do **not** open a public Issue.

### License

[MIT License](./LICENSE)
