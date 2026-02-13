# 网络故障排查：Neon 数据库连接超时

## 问题症状

```
[WinError 121] 信号灯超时时间已到
```

所有 API 接口请求超时（30-42秒）

## 根本原因

**Neon Database 在海外（AWS 新加坡），国内网络无法直接访问。**

诊断结果：
- ❌ Ping 丢包 100%
- ❌ PostgreSQL TCP 连接（5432端口）不走系统代理
- ✅ HTTPS 请求可以走代理（但数据库连接不行）

## 解决方案

### 方案 1：使用本地数据库（推荐开发环境）

```bash
# 1. 启动本地 PostgreSQL（Docker）
docker run -d \
  --name feedalyze-postgres \
  -e POSTGRES_USER=feedalyze \
  -e POSTGRES_PASSWORD=feedalyze123 \
  -e POSTGRES_DB=feedalyze \
  -p 5432:5432 \
  pgvector/pgvector:pg17

# 2. 修改 .env
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_USER=feedalyze
DATABASE_PASSWORD=feedalyze123
DATABASE_SCHEMA=feedalyze

# 3. 运行迁移
cd server
source .venv/Scripts/activate
alembic upgrade head
```

### 方案 2：使用 SSH 隧道（保留 Neon）

如果你有能访问海外的跳板机：

```bash
# 在跳板机上建立隧道
ssh -L 5432:ep-icy-glade-a1a4td9q-pooler.ap-southeast-1.aws.neon.tech:5432 your-jump-server

# 修改 .env
DATABASE_HOST=localhost  # 通过本地 5432 端口转发
```

### 方案 3：使用 Socks5 代理

需要 Python 支持 Socks5：

```bash
pip install pysocks

# 设置环境变量（仅对支持的库有效）
export ALL_PROXY=socks5://127.0.0.1:1080
```

**注意**：asyncpg 不原生支持 SOCKS5，需要额外配置。

## 验证修复

```bash
# 测试数据库连接
cd server
source .venv/Scripts/activate
python diagnose_db_connections.py

# 应该看到：
# ✅ 数据库连接正常
# ✅ 连接池状态正常
```

## 预防措施

1. **开发环境使用本地数据库**
   - 不依赖网络
   - 响应快速
   - 可离线工作

2. **生产环境使用云数据库**
   - 部署在同一区域（如都在 AWS ap-southeast-1）
   - 不跨国访问

3. **连接池配置**
   - `pool_timeout` 设置合理（本地 10s，远程 30s）
   - `pool_pre_ping=True` 检测死连接

