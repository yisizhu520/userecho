# Redis 配置说明

## 两种配置方式

Feedalyze 支持两种 Redis 配置方式，你可以根据实际情况选择：

### 方式 1: 使用完整的 Redis URL (推荐用于托管服务)

适用于 Upstash、Redis Cloud 等提供完整连接字符串的托管服务。

```bash
# 支持 redis:// 或 rediss:// (SSL/TLS)
# 格式: rediss://username:password@host:port/database
REDIS_URL=rediss://default:your_password@your-redis-host.upstash.io:6379
```

**示例 (Upstash)**:
```bash
REDIS_URL="rediss://default:AaDDAAIncDFhM2RmZWI4ZTM0NWY0MWRiYTQ1NGExMzUwODQzZGIxNnAxNDExNTU@funny-kodiak-41155.upstash.io:6379"
```

### 方式 2: 使用独立参数 (本地 Redis)

适用于本地开发或自建 Redis 服务。

```bash
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_USERNAME=default      # 可选，Redis 6.0+ 支持 ACL
REDIS_PASSWORD=your_password
REDIS_DATABASE=0
```

**注意**: 如果同时设置了 `REDIS_URL`，独立参数会被忽略。

## 配置优先级

1. **REDIS_URL** (优先) - 如果设置，将使用完整 URL 连接
2. **独立参数** (备用) - 仅在未设置 REDIS_URL 时使用

## Celery 配置

Celery 需要独立的 Redis 数据库编号（避免和主应用冲突）：

```bash
CELERY_BROKER_REDIS_DATABASE=1
```

## 你的 Upstash 配置示例

```bash
# .env 文件
REDIS_URL="rediss://default:AaDDAAIncDFhM2RmZWI4ZTM0NWY0MWRiYTQ1NGExMzUwODQzZGIxNnAxNDExNTU@funny-kodiak-41155.upstash.io:6379"
CELERY_BROKER_REDIS_DATABASE=1
```

是的，你的 Upstash Redis 连接需要 username (`default`)。

## 技术细节

### Redis URL 格式解析

```
rediss://default:password@host:port/database
  ^       ^       ^        ^    ^    ^
  |       |       |        |    |    └─ 数据库编号 (0-15)
  |       |       |        |    └────── 端口
  |       |       |        └─────────── 主机地址
  |       |       └──────────────────── 密码
  |       └──────────────────────────── 用户名 (Redis 6.0+ ACL)
  └──────────────────────────────────── 协议 (rediss = Redis + SSL/TLS)
```

### 代码实现

项目已更新以下文件以支持 username 和完整 URL：

1. `server/backend/core/conf.py` - 添加 `REDIS_URL` 和 `REDIS_USERNAME` 配置
2. `server/backend/database/redis.py` - 支持从 URL 或独立参数创建连接
3. `server/backend/common/socketio/server.py` - Socket.IO 支持完整 URL
4. `server/backend/app/task/celery.py` - Celery broker 支持完整 URL
