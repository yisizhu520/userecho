# 数据库设计补充说明

> **版本:** v1.1  
> **更新日期:** 2025-12-21  
> **变更类型:** 核心设计调整

---

## 变更概述

基于真实业务场景的反馈，对数据库设计进行两处关键调整：

1. ✅ **确认使用 PostgreSQL + pgvector**（不引入额外向量数据库）
2. ✅ **支持匿名反馈**（解决未登录用户、社交媒体评论等场景）

---

## 变更一：向量存储方案确认

### 原设计
```
方案 A：PostgreSQL + pgvector（成本低，适合 MVP）
方案 B：独立向量数据库（Milvus/Qdrant）
决策依据：10 万条反馈的查询性能测试
```

### 最终决策
**✅ 确定使用 PostgreSQL + pgvector**

**理由：**
- MVP 阶段数据量 < 10 万条，pgvector 性能足够
- 减少技术栈复杂度，统一使用 PostgreSQL
- 避免引入 Elasticsearch/Milvus 等外部依赖
- 降低运维成本和学习曲线

**性能指标：**
- 768 维向量相似度查询 < 100ms
- IVFFlat 索引支持 10 万级数据
- 如需扩展，可升级为 HNSW 索引

---

## 变更二：支持匿名反馈

### 问题场景

**真实业务场景：**
1. 小红书用户 "夏天的风" 评论说产品太卡
2. 知乎匿名用户反馈登录失败
3. 官网未登录访客留言
4. 微博评论、抖音评论、APP Store 评价

**这些反馈的特点：**
- ❌ 没有对应的客户记录（customer_id）
- ✅ 有作者名称（昵称、匿名ID）
- ✅ 有来源平台（xiaohongshu、zhihu、weibo）
- ✅ 同样需要 AI 聚类和优先级评分

### 原设计的问题

```sql
-- ❌ 强制要求客户ID
customer_id VARCHAR(36) NOT NULL
```

**这会导致：**
- 无法导入社交媒体评论
- 无法处理未登录用户反馈
- 要么创建虚拟"匿名客户"（数据污染）
- 要么丢弃这些宝贵的反馈

### 新设计方案

#### feedbacks 表结构变更

```sql
CREATE TABLE feedbacks (
    id VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
    tenant_id VARCHAR(36) NOT NULL,
    
    -- 【核心变更】已知客户 vs 匿名反馈
    customer_id VARCHAR(36) NULL COMMENT '已知客户ID,匿名反馈时为NULL',
    anonymous_author VARCHAR(100) NULL COMMENT '匿名作者名称(如"小红书用户夏天")',
    anonymous_source VARCHAR(50) NULL COMMENT '匿名来源平台(xiaohongshu/zhihu/weibo等)',
    
    topic_id VARCHAR(36) NULL COMMENT 'NULL表示未聚类',
    content TEXT NOT NULL,
    source ENUM('manual', 'excel_import', 'api', 'social_media') DEFAULT 'manual',
    ai_summary VARCHAR(50) NULL COMMENT 'AI生成的20字摘要',
    is_urgent BOOLEAN DEFAULT FALSE,
    
    -- 【核心变更】向量直接存储在 PostgreSQL
    embedding VECTOR(768) NULL COMMENT 'pgvector向量字段',
    ai_metadata JSON NULL COMMENT '存储AI处理元数据',
    
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL,
    
    INDEX idx_tenant_id (tenant_id),
    INDEX idx_customer_id (customer_id),
    INDEX idx_topic_id (topic_id),
    INDEX idx_is_urgent (is_urgent),
    INDEX idx_submitted_at (submitted_at),
    INDEX idx_deleted_at (deleted_at),
    INDEX idx_anonymous_source (anonymous_source),
    
    -- pgvector 向量索引 (IVFFlat 适合 MVP)
    INDEX idx_embedding USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100),
    
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE,
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE SET NULL,
    FOREIGN KEY (topic_id) REFERENCES topics(id) ON DELETE SET NULL,
    
    -- 【业务约束】要么有客户ID，要么有匿名作者名
    CONSTRAINT chk_author_exists CHECK (
        customer_id IS NOT NULL OR anonymous_author IS NOT NULL
    )
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

#### 关键设计解释

**1. 三个关键字段**
```sql
customer_id       -- 已知客户时填写（如：付费用户 "小米科技"）
anonymous_author  -- 匿名用户时填写（如："小红书用户夏天"）
anonymous_source  -- 匿名来源平台（如："xiaohongshu"）
```

**2. 业务约束**
```sql
CONSTRAINT chk_author_exists CHECK (
    customer_id IS NOT NULL OR anonymous_author IS NOT NULL
)
```
- **必须二选一**：要么是已知客户，要么是匿名作者
- 防止数据不完整（不知道反馈来自谁）

**3. 外键约束调整**
```sql
FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE SET NULL
```
- 从 `ON DELETE RESTRICT` 改为 `ON DELETE SET NULL`
- 客户删除后，反馈不丢失，只是变成"来自已删除客户"

**4. 向量字段**
```sql
embedding VECTOR(768) NULL
```
- 直接使用 pgvector 的 `VECTOR` 类型
- 不再存储在 `ai_metadata` JSON 中
- 支持高效的向量索引和相似度查询

---

## 数据示例

### 已知客户的反馈
```json
{
  "id": "fb-001",
  "tenant_id": "tenant-123",
  "customer_id": "cust-xiaomi",
  "anonymous_author": null,
  "anonymous_source": null,
  "content": "登录按钮点击无反应",
  "source": "manual",
  "submitted_at": "2025-12-21T10:00:00Z"
}
```

### 社交媒体匿名反馈
```json
{
  "id": "fb-002",
  "tenant_id": "tenant-123",
  "customer_id": null,
  "anonymous_author": "小红书用户夏天的风",
  "anonymous_source": "xiaohongshu",
  "content": "APP太卡了，打开要10秒",
  "source": "social_media",
  "submitted_at": "2025-12-21T10:05:00Z"
}
```

### 官网未登录用户反馈
```json
{
  "id": "fb-003",
  "tenant_id": "tenant-123",
  "customer_id": null,
  "anonymous_author": "访客_192.168.1.1",
  "anonymous_source": "website",
  "content": "希望支持微信登录",
  "source": "manual",
  "submitted_at": "2025-12-21T10:10:00Z"
}
```

---

## 业务逻辑影响

### 优先级评分计算

**原逻辑：**
```
商业价值 = customer.business_value (1/3/5/10)
```

**新逻辑：**
```typescript
function getBusinessValue(feedback: Feedback): number {
  if (feedback.customer_id) {
    // 已知客户：使用客户的商业价值
    return feedback.customer.business_value; // 1/3/5/10
  } else {
    // 匿名反馈：统一使用基础值
    return 1; // 默认普通用户价值
  }
}
```

**特殊情况处理：**
- 如果某个社交媒体反馈来自已知的大客户（人工确认）
- PM 可以手动创建客户记录并关联反馈
- 系统记录这个操作到 `manual_adjustments` 表

---

## AI 聚类影响

**无影响！**

聚类只依赖于反馈内容的语义相似度：
```sql
-- AI 聚类查询（不区分已知客户 vs 匿名）
SELECT 
    id, 
    content,
    COALESCE(
        (SELECT name FROM customers WHERE id = customer_id),
        anonymous_author
    ) AS author_display,
    1 - (embedding <=> $1::vector) AS similarity
FROM feedbacks
WHERE tenant_id = $2
    AND deleted_at IS NULL
    AND embedding IS NOT NULL
ORDER BY embedding <=> $1::vector
LIMIT 10;
```

**摘要生成变化：**
```typescript
// 原格式：[客户名称] 反馈 [核心问题]
// 新格式：[作者名称] 反馈 [核心问题]

function generateSummary(feedback: Feedback): string {
  const author = feedback.customer_id 
    ? feedback.customer.name 
    : feedback.anonymous_author;
  
  return `[${author}] 反馈 ${extractKeyIssue(feedback.content)}`;
}
```

---

## 前端展示变化

### 反馈列表

**原显示：**
```
客户：小米科技 (战略客户)
内容：登录按钮无反应
```

**新显示：**
```
作者：小米科技 (战略客户)        ← 已知客户
内容：登录按钮无反应

作者：小红书用户夏天的风          ← 匿名用户
来源：小红书
内容：APP太卡了
```

### Excel 导入模板

**原模板：**
```
反馈内容 | 提交时间 | 客户名称 | 客户类型
```

**新模板（向后兼容）：**
```
反馈内容 | 提交时间 | 客户名称(可选) | 客户类型 | 作者名(可选) | 来源平台(可选)
```

**填写规则：**
- 已知客户：填写"客户名称"和"客户类型"，其他留空
- 匿名反馈：填写"作者名"和"来源平台"，客户字段留空
- 系统自动验证：至少有一组数据（客户 or 作者）

---

## pgvector 技术细节

### 安装 pgvector 插件

**Docker 镜像（推荐）：**
```dockerfile
FROM pgvector/pgvector:pg16

# 或者使用官方 PostgreSQL + 手动安装
FROM postgres:16
RUN apt-get update && apt-get install -y postgresql-16-pgvector
```

**手动安装（Ubuntu）：**
```bash
# PostgreSQL 14+
sudo apt install postgresql-16-pgvector

# 启用插件
psql -U postgres -d userecho -c "CREATE EXTENSION vector;"
```

**验证安装：**
```sql
SELECT * FROM pg_extension WHERE extname = 'vector';
-- 输出：vector | 0.5.1 | ...
```

### 向量索引策略

**IVFFlat 索引（MVP 推荐）：**
```sql
-- lists 参数：sqrt(总行数) 到 总行数/1000 之间
-- 10万条数据：lists = 100-316 之间
CREATE INDEX idx_feedbacks_embedding 
ON feedbacks USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 100);
```

**HNSW 索引（10万+ 数据）：**
```sql
-- m: 每个节点的连接数（越大越准确但内存越高）
-- ef_construction: 构建索引时的搜索深度
CREATE INDEX idx_feedbacks_embedding 
ON feedbacks USING hnsw (embedding vector_cosine_ops) 
WITH (m = 16, ef_construction = 64);
```

### 相似度查询

**Cosine Similarity（推荐）：**
```sql
-- <=> 运算符：cosine distance (1 - cosine similarity)
SELECT 
    id, 
    content,
    1 - (embedding <=> $1::vector) AS similarity
FROM feedbacks
WHERE tenant_id = $2
    AND embedding IS NOT NULL
ORDER BY embedding <=> $1::vector  -- 距离越小越相似
LIMIT 10;
```

**L2 Distance（欧几里得距离）：**
```sql
-- <-> 运算符：L2 distance
SELECT id, content
FROM feedbacks
WHERE tenant_id = ?
ORDER BY embedding <-> $1::vector
LIMIT 10;
```

**Inner Product（点积）：**
```sql
-- <#> 运算符：负内积
SELECT id, content
FROM feedbacks
WHERE tenant_id = ?
ORDER BY embedding <#> $1::vector
LIMIT 10;
```

### 性能优化参数

```sql
-- IVFFlat 查询精度
SET ivfflat.probes = 10;  -- 默认1，越大越准确但越慢

-- HNSW 查询精度
SET hnsw.ef_search = 40;  -- 默认40，越大越准确但越慢

-- 查询示例
BEGIN;
SET ivfflat.probes = 20;  -- 提高精度
SELECT ... FROM feedbacks ORDER BY embedding <=> $1 LIMIT 10;
COMMIT;
```

### 向量维度选择

| 模型 | 维度 | 说明 |
|-----|------|-----|
| OpenAI text-embedding-3-small | 1536 | 精度高，成本高 |
| OpenAI text-embedding-3-large | 3072 | 最高精度，最高成本 |
| **DeepSeek Embedding** | **768** | ✅ MVP 推荐 |
| **Qwen Embedding** | **768** | ✅ MVP 推荐 |
| Sentence-Transformers | 384-768 | 本地部署 |

---

## 迁移步骤

### Step 1: 更新 feedbacks 表结构

```sql
-- 添加新字段
ALTER TABLE feedbacks 
ADD COLUMN anonymous_author VARCHAR(100) NULL AFTER customer_id,
ADD COLUMN anonymous_source VARCHAR(50) NULL AFTER anonymous_author,
ADD COLUMN embedding VECTOR(768) NULL AFTER is_urgent;

-- 修改 customer_id 为可空
ALTER TABLE feedbacks 
MODIFY COLUMN customer_id VARCHAR(36) NULL;

-- 修改外键约束
ALTER TABLE feedbacks 
DROP FOREIGN KEY fk_feedbacks_customer_id;

ALTER TABLE feedbacks 
ADD CONSTRAINT fk_feedbacks_customer_id 
FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE SET NULL;

-- 添加业务约束
ALTER TABLE feedbacks 
ADD CONSTRAINT chk_author_exists CHECK (
    customer_id IS NOT NULL OR anonymous_author IS NOT NULL
);

-- 添加索引
CREATE INDEX idx_anonymous_source ON feedbacks(anonymous_source);

-- 添加向量索引
CREATE INDEX idx_embedding ON feedbacks 
USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 100);
```

### Step 2: 数据迁移（如果有历史数据）

```sql
-- 将 ai_metadata 中的 embedding 迁移到独立字段
UPDATE feedbacks 
SET embedding = (ai_metadata->>'embedding')::vector
WHERE ai_metadata->>'embedding' IS NOT NULL;

-- 清理 ai_metadata 中的冗余数据
UPDATE feedbacks 
SET ai_metadata = JSON_REMOVE(ai_metadata, '$.embedding')
WHERE ai_metadata->>'embedding' IS NOT NULL;
```

### Step 3: 验证数据完整性

```sql
-- 检查是否有违反约束的数据
SELECT id, customer_id, anonymous_author 
FROM feedbacks 
WHERE customer_id IS NULL AND anonymous_author IS NULL;

-- 检查向量迁移是否完整
SELECT 
    COUNT(*) AS total,
    COUNT(embedding) AS with_embedding,
    COUNT(*) - COUNT(embedding) AS missing_embedding
FROM feedbacks;
```

---

## 测试用例

### Test 1: 已知客户反馈
```sql
INSERT INTO feedbacks (
    id, tenant_id, customer_id, content, source
) VALUES (
    UUID(), 'tenant-123', 'cust-xiaomi', 
    '登录按钮无反应', 'manual'
);
```

### Test 2: 匿名反馈
```sql
INSERT INTO feedbacks (
    id, tenant_id, anonymous_author, anonymous_source,
    content, source
) VALUES (
    UUID(), 'tenant-123', '小红书用户夏天', 'xiaohongshu',
    'APP太卡了', 'social_media'
);
```

### Test 3: 违反约束（应该失败）
```sql
-- ❌ 既没有客户ID，也没有匿名作者
INSERT INTO feedbacks (
    id, tenant_id, content
) VALUES (
    UUID(), 'tenant-123', '测试内容'
);
-- ERROR: Check constraint 'chk_author_exists' is violated.
```

### Test 4: 向量相似度查询
```sql
-- 假设已有 embedding 数据
SELECT 
    id,
    content,
    COALESCE(
        (SELECT name FROM customers WHERE id = customer_id),
        anonymous_author
    ) AS author,
    1 - (embedding <=> '[0.1,0.2,...]'::vector) AS similarity
FROM feedbacks
WHERE tenant_id = 'tenant-123'
    AND embedding IS NOT NULL
ORDER BY embedding <=> '[0.1,0.2,...]'::vector
LIMIT 10;
```

---

## FAQ

**Q1: 匿名反馈的商业价值怎么计算？**

A: 统一使用基础值 `1`（普通用户），除非 PM 手动关联到已知客户。

**Q2: 如果后续发现匿名反馈实际是大客户，怎么办？**

A: PM 可以手动创建/关联客户记录：
```sql
-- 创建客户
INSERT INTO customers (id, tenant_id, name, customer_type)
VALUES ('cust-new', 'tenant-123', '小米科技', 'strategic');

-- 关联反馈
UPDATE feedbacks 
SET customer_id = 'cust-new' 
WHERE id = 'fb-002';

-- 记录人工调整
INSERT INTO manual_adjustments (...)
```

**Q3: pgvector 性能会不会不够？**

A: 
- MVP 阶段 < 10 万条，IVFFlat 足够
- 10 万+ 条，升级为 HNSW 索引
- 100 万+ 条，考虑专用向量数据库

**Q4: 为什么不把 embedding 存 JSON 里？**

A: 
- JSON 字段无法建立向量索引
- 相似度查询会扫全表，性能极差
- pgvector 的 VECTOR 类型是为向量搜索优化的

**Q5: 匿名来源平台的枚举值有哪些？**

A: 建议值（可扩展）：
```
xiaohongshu  - 小红书
zhihu        - 知乎
weibo        - 微博
douyin       - 抖音
appstore     - App Store
website      - 官网
other        - 其他
```

---

## 总结

### 核心变更

1. **向量存储**：确定使用 PostgreSQL + pgvector，减少技术栈复杂度
2. **匿名反馈**：支持无客户记录的反馈，扩展数据来源范围

### 设计哲学

**Linus 式评价：**
- ✅ **好品味**：用 NULL 表达"没有客户"，而不是创建虚拟客户
- ✅ **实用主义**：解决真实业务问题（社交媒体反馈）
- ✅ **简洁性**：业务约束保证数据完整性，不需要应用层判断

**关键原则：**
> "数据结构诚实地反映业务现实，代码自然简单。"

---

**文档维护者:** 技术团队  
**最后更新:** 2025-12-21
