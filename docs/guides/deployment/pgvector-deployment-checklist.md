# pgvector 部署检查清单

> **快速开始**：将 Embedding 缓存升级为 pgvector VECTOR 字段

---

## ✅ 准备工作

### 1️⃣ 数据库要求

**必须使用 PostgreSQL**（MySQL 不支持 VECTOR 类型）

#### 选项 A：Docker 部署（推荐开发环境）

```bash
# 使用带 pgvector 的 PostgreSQL 镜像
docker run -d \
  --name userecho-postgres \
  -p 5432:5432 \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=your_password \
  -e POSTGRES_DB=userecho \
  ankane/pgvector:latest
```

#### 选项 B：本地 PostgreSQL

```bash
# Ubuntu/Debian
sudo apt install postgresql-16 postgresql-16-pgvector

# macOS
brew install postgresql@16
brew install pgvector

# 启动 PostgreSQL
sudo systemctl start postgresql  # Linux
brew services start postgresql@16  # macOS
```

### 2️⃣ 创建数据库

```sql
-- 连接到 PostgreSQL
psql -U postgres

-- 创建数据库
CREATE DATABASE userecho;

-- 切换到数据库
\c userecho

-- 启用 pgvector 扩展
CREATE EXTENSION IF NOT EXISTS vector;

-- 验证扩展
SELECT * FROM pg_extension WHERE extname = 'vector';
```

### 3️⃣ 配置环境变量

编辑 `server/.env`：

```bash
# 修改数据库连接为 PostgreSQL
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=your_password
DB_DATABASE=userecho

# 或者使用完整 URL
DATABASE_URL=postgresql+asyncpg://postgres:your_password@localhost:5432/userecho
```

---

## 🚀 部署步骤

### Step 1: 检查代码变更

```bash
cd server/backend

# 检查待执行的 migration
alembic current  # 查看当前版本
alembic history  # 查看历史记录
```

### Step 2: 运行 Migration

```bash
# 激活虚拟环境
cd server
source .venv/Scripts/activate  # Windows Git Bash
# source .venv/bin/activate    # Linux/macOS

# 执行 migration
cd backend
alembic upgrade head
```

**预期输出**：
```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade xxx -> add_embedding_vector, add embedding vector field
```

### Step 3: 验证部署

```sql
-- 连接到数据库
psql -U postgres -d userecho

-- 检查 embedding 字段
\d feedbacks

-- 应该看到：
-- embedding | vector(768) | | |
```

### Step 4: 创建向量索引（可选，数据量 > 1000）

```sql
-- IVFFlat 索引（适合百万级数据）
CREATE INDEX idx_feedbacks_embedding
ON feedbacks
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- 查看索引
\di idx_feedbacks_embedding
```

---

## 🧪 测试验证

### 1. 测试 Embedding 缓存

```bash
cd server
python backend/scripts/test_embedding_cache.py
```

**预期输出**：
```
【测试 1】单条反馈缓存读写
  测试反馈: abc-123
  缓存状态: ✗ 未缓存
  正在生成 embedding...
  生成成功: 768 维
  缓存保存: ✓ 成功
  缓存验证: ✓ 成功
```

### 2. 测试聚类服务

```bash
# 触发聚类（通过 API 或脚本）
# 观察日志中的缓存命中率

# 预期日志：
# Embedding cache hit: 0/100 (0.0%)      # 首次：无缓存
# Batch embedding completed: 100/100     # 批量获取
# Cached 100 new embeddings to database  # 写入缓存

# 第二次触发聚类：
# Embedding cache hit: 100/100 (100.0%)  # 全部命中缓存
```

### 3. 测试向量搜索

```python
# 在 Python shell 中测试
from backend.database.db_mysql import async_db_session
from backend.app.userecho.crud import crud_feedback
from backend.utils.ai_client import ai_client
import asyncio

async def test():
    async with async_db_session() as db:
        # 1. 获取查询向量
        query = "登录按钮点不了"
        embedding = await ai_client.get_embedding(query)
        
        # 2. 向量搜索
        results = await crud_feedback.find_similar_feedbacks(
            db=db,
            tenant_id='default-tenant',
            query_embedding=embedding,
            limit=10,
            min_similarity=0.7
        )
        
        # 3. 输出结果
        for feedback, similarity in results:
            print(f'{similarity:.2f} - {feedback.content[:50]}')

asyncio.run(test())
```

---

## 🐛 故障排查

### 问题 1: `ImportError: cannot import name 'VECTOR'`

**原因**：VECTOR 不是 SQLAlchemy 内置类型

**解决**：已修复，模型使用 `Text` 类型，Migration 时转换为 `VECTOR(768)`

---

### 问题 2: `Authentication timed out` 数据库连接超时

**原因**：PostgreSQL 未启动或配置错误

**解决**：
```bash
# 检查 PostgreSQL 是否运行
sudo systemctl status postgresql  # Linux
brew services list | grep postgresql  # macOS

# 测试连接
psql -U postgres -h localhost -p 5432 -d userecho

# 检查环境变量
cat server/.env | grep DB_
```

---

### 问题 3: `CREATE EXTENSION vector` 失败

**原因**：pgvector 扩展未安装

**解决**：
```bash
# Ubuntu/Debian
sudo apt install postgresql-16-pgvector

# macOS
brew install pgvector

# 重启 PostgreSQL
sudo systemctl restart postgresql
```

---

### 问题 4: 索引创建失败

**原因**：数据量太少（< 100 条）

**解决**：
```sql
-- 检查数据量
SELECT COUNT(*) FROM feedbacks WHERE embedding IS NOT NULL;

-- 如果 < 100，跳过索引创建
-- 等数据增长后手动创建
```

---

## 📊 性能监控

### 查看缓存命中率

```bash
# 查看聚类日志
tail -f server/backend/log/fba_access.log | grep "Embedding cache hit"

# 输出示例：
# 2025-12-22 23:00:00 | INFO | Embedding cache hit: 80/100 (80.0%)
```

### 查看数据库统计

```sql
-- 统计 embedding 数量
SELECT 
    COUNT(*) as total,
    COUNT(embedding) as has_embedding,
    COUNT(embedding) * 100.0 / COUNT(*) as cache_rate
FROM feedbacks
WHERE deleted_at IS NULL;

-- 输出示例：
-- total | has_embedding | cache_rate
-- 1000  | 850           | 85.0
```

### 查看索引使用情况

```sql
-- 查看索引大小
SELECT 
    schemaname,
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexrelid)) as index_size
FROM pg_stat_user_indexes
WHERE indexname = 'idx_feedbacks_embedding';

-- 查看索引扫描次数
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan as scan_count,
    idx_tup_read as tuples_read
FROM pg_stat_user_indexes
WHERE indexname = 'idx_feedbacks_embedding';
```

---

## 📝 回滚方案

如果需要回滚：

```bash
# 回滚到上一个版本
alembic downgrade -1

# 或回滚到指定版本
alembic downgrade <revision_id>
```

**注意**：回滚会**删除 embedding 字段**，已缓存的数据会丢失。

---

## ✅ 检查清单

部署前检查：
- [ ] PostgreSQL 已安装并运行
- [ ] pgvector 扩展已安装
- [ ] 数据库已创建
- [ ] 环境变量已配置
- [ ] 虚拟环境已激活

部署后验证：
- [ ] Migration 执行成功
- [ ] `feedbacks` 表有 `embedding` 字段
- [ ] 字段类型为 `vector(768)`
- [ ] 测试脚本运行成功
- [ ] 聚类服务缓存命中率正常

可选优化：
- [ ] 创建向量索引（数据量 > 1000）
- [ ] 配置索引维护计划
- [ ] 设置性能监控告警

---

**总结**：
- ✅ 代码已准备就绪
- ⚠️ 需要 PostgreSQL + pgvector
- ⚠️ 需要先配置数据库才能执行 Migration
- 📖 按照本文档步骤操作即可
