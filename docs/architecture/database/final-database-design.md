# userecho 最终数据库设计方案

> **版本**: v4.0 - Final  
> **更新日期**: 2025-12-31  
> **核心理念**: Feedback 不可合并，保留原始数据；Topic 作为聚合层，承载权重计算

---

## 一、核心设计原则

### 1.1 数据模型清晰度

```
原始数据层（Feedback）
    ├─ 保留所有原始信息
    ├─ 记录来源（谁录入、从哪来）
    ├─ 记录客户信息（为权重计算提供数据）
    └─ 不可合并、不可删除（软删除）
         ↓
聚合层（Topic）
    ├─ AI 自动聚类生成
    ├─ 聚合多个 Feedback
    ├─ 计算权重（基于关联的 Feedback）
    └─ 作为需求管理单元
```

### 1.2 核心决策

✅ **Feedback 不可合并**
- 原始数据是权重计算的基础
- 保留溯源信息（谁录入、哪个客户、什么渠道）
- 数据模型更清晰

✅ **用户输入时全文检索 Topic**
- 只检索 Topic（不检索 Feedback）
- 用户选择关联到已有 Topic
- 如果没有合适的 Topic，创建新 Feedback，等待 AI 聚类

✅ **Topic 权重基于关联的 Feedback**
- 聚合所有关联 Feedback 的客户价值
- 统计受影响的客户数量
- 自动计算优先级

---

## 二、核心表设计

### 2.1 Feedbacks 表（原始数据层）

**设计理念**：保留所有原始信息，不可合并

```sql
CREATE TABLE feedbacks (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id VARCHAR(36) NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    
    -- 关联 Topic（可为空，等待 AI 聚类）
    topic_id VARCHAR(36) REFERENCES topics(id) ON DELETE SET NULL,
    
    -- 客户信息（权重计算基础）
    customer_id VARCHAR(36) REFERENCES customers(id) ON DELETE SET NULL,
    customer_mrr DECIMAL(10,2) COMMENT '客户月收入（冗余字段，便于聚合）',
    customer_tier VARCHAR(20) COMMENT '客户等级（冗余字段）',
    
    -- 录入信息（溯源）
    reporter_id INTEGER REFERENCES sys_user(id) COMMENT '录入人（销售/客服/产品）',
    source VARCHAR(20) DEFAULT 'manual' COMMENT 'manual, import, screenshot, api',
    
    -- 反馈内容
    content TEXT NOT NULL,
    ai_summary VARCHAR(200) COMMENT 'AI 生成的摘要',
    
    -- 截图识别相关
    screenshot_url TEXT,
    source_platform VARCHAR(50) COMMENT 'wechat, xiaohongshu, appstore, etc.',
    source_user_name VARCHAR(255),
    ai_confidence FLOAT,
    
    -- AI 相关
    embedding VECTOR(4096) COMMENT '内容向量',
    sentiment VARCHAR(20) COMMENT 'positive, neutral, negative',
    sentiment_score FLOAT,
    
    -- 聚类状态
    clustering_status VARCHAR(20) DEFAULT 'pending' COMMENT 'pending, clustered, manual_linked',
    clustering_metadata JSONB,
    
    -- 时间戳
    submitted_at TIMESTAMPTZ DEFAULT NOW(),
    created_time TIMESTAMPTZ DEFAULT NOW(),
    updated_time TIMESTAMPTZ,
    deleted_at TIMESTAMPTZ COMMENT '软删除',
    
    -- 索引
    INDEX idx_feedbacks_tenant (tenant_id),
    INDEX idx_feedbacks_topic (topic_id),
    INDEX idx_feedbacks_customer (customer_id),
    INDEX idx_feedbacks_reporter (reporter_id),
    INDEX idx_feedbacks_status (clustering_status),
    INDEX idx_feedbacks_embedding USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)
);

COMMENT ON TABLE feedbacks IS '用户反馈表（原始数据层，不可合并）';
COMMENT ON COLUMN feedbacks.customer_mrr IS '冗余字段，便于 Topic 聚合计算权重';
COMMENT ON COLUMN feedbacks.clustering_status IS 'pending: 待聚类, clustered: AI已聚类, manual_linked: 用户手动关联';
```

**关键设计点**：
1. ❌ **删除 `merged_into_id` 字段**：Feedback 不可合并
2. ✅ **保留 `topic_id`**：关联到 Topic（可为空）
3. ✅ **冗余 `customer_mrr`**：便于 Topic 聚合计算（避免多次 JOIN）
4. ✅ **记录 `reporter_id`**：溯源信息，知道谁录入的
5. ✅ **`clustering_status` 区分来源**：AI 聚类 vs 用户手动关联

---

### 2.2 Topics 表（聚合层）

**设计理念**：聚合多个 Feedback，计算权重，作为需求管理单元

```sql
CREATE TABLE topics (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id VARCHAR(36) NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    
    -- Topic 基础信息
    title VARCHAR(200) NOT NULL COMMENT 'AI 生成或人工编辑',
    description TEXT COMMENT 'AI 生成或人工编辑',
    category VARCHAR(50) COMMENT 'bug, feature, improvement, etc.',
    
    -- AI 聚类相关
    centroid VECTOR(4096) COMMENT 'Topic 中心向量（所有 Feedback embedding 的平均）',
    ai_generated BOOLEAN DEFAULT TRUE COMMENT '是否由 AI 生成',
    
    -- 权重计算（基于关联的 Feedback）
    feedback_count INTEGER DEFAULT 0 COMMENT '关联的 Feedback 数量',
    affected_customer_count INTEGER DEFAULT 0 COMMENT '受影响的客户数量（去重）',
    total_mrr DECIMAL(10,2) DEFAULT 0 COMMENT '所有关联客户的 MRR 总和',
    avg_sentiment_score FLOAT COMMENT '平均情感分数',
    
    -- 优先级评分
    impact_scope INTEGER COMMENT '影响范围评分 (1-10)，产品经理标注',
    dev_cost_estimate INTEGER COMMENT '开发成本评分 (1-10)，技术负责人标注',
    priority_score DECIMAL(10,2) GENERATED ALWAYS AS (
        COALESCE(total_mrr, 0) * COALESCE(impact_scope, 5) / NULLIF(COALESCE(dev_cost_estimate, 5), 0)
    ) STORED COMMENT '优先级 = 总MRR × 影响范围 / 成本',
    
    -- 需求管理
    internal_status VARCHAR(20) DEFAULT 'pending' COMMENT 'pending, evaluating, approved, rejected, planned, in_dev, released',
    product_owner_id INTEGER REFERENCES sys_user(id) COMMENT '产品负责人',
    estimated_release_date DATE COMMENT '预计发布日期',
    
    -- 外部集成
    jira_issue_key VARCHAR(50) COMMENT 'Jira Issue Key',
    tapd_story_id VARCHAR(50) COMMENT 'Tapd Story ID',
    
    -- 时间戳
    created_time TIMESTAMPTZ DEFAULT NOW(),
    updated_time TIMESTAMPTZ,
    deleted_at TIMESTAMPTZ,
    
    -- 索引
    INDEX idx_topics_tenant (tenant_id),
    INDEX idx_topics_status (internal_status),
    INDEX idx_topics_priority (priority_score DESC NULLS LAST),
    INDEX idx_topics_centroid USING ivfflat (centroid vector_cosine_ops) WITH (lists = 50)
);

COMMENT ON TABLE topics IS '需求主题表（聚合层，承载权重计算）';
COMMENT ON COLUMN topics.feedback_count IS '实时统计，通过触发器更新';
COMMENT ON COLUMN topics.total_mrr IS '聚合所有关联 Feedback 的客户 MRR';
```

**关键设计点**：
1. ✅ **权重字段基于 Feedback 聚合**：`total_mrr`, `affected_customer_count`
2. ✅ **优先级自动计算**：基于聚合数据
3. ✅ **支持人工调整**：`impact_scope`, `dev_cost_estimate`
4. ✅ **需求管理字段**：`internal_status`, `product_owner_id`

---

### 2.3 触发器：自动更新 Topic 权重

**问题**：当 Feedback 关联到 Topic 时，如何自动更新 Topic 的权重字段？

**解决方案**：使用 PostgreSQL 触发器

```sql
-- 触发器函数：更新 Topic 统计信息
CREATE OR REPLACE FUNCTION update_topic_stats()
RETURNS TRIGGER AS $$
BEGIN
    -- 如果 Feedback 关联到了 Topic
    IF NEW.topic_id IS NOT NULL THEN
        UPDATE topics
        SET 
            feedback_count = (
                SELECT COUNT(*) 
                FROM feedbacks 
                WHERE topic_id = NEW.topic_id 
                  AND deleted_at IS NULL
            ),
            affected_customer_count = (
                SELECT COUNT(DISTINCT customer_id) 
                FROM feedbacks 
                WHERE topic_id = NEW.topic_id 
                  AND deleted_at IS NULL
                  AND customer_id IS NOT NULL
            ),
            total_mrr = (
                SELECT COALESCE(SUM(DISTINCT customer_mrr), 0)
                FROM feedbacks 
                WHERE topic_id = NEW.topic_id 
                  AND deleted_at IS NULL
                  AND customer_mrr IS NOT NULL
            ),
            avg_sentiment_score = (
                SELECT AVG(sentiment_score)
                FROM feedbacks 
                WHERE topic_id = NEW.topic_id 
                  AND deleted_at IS NULL
                  AND sentiment_score IS NOT NULL
            ),
            updated_time = NOW()
        WHERE id = NEW.topic_id;
    END IF;
    
    -- 如果 Feedback 从一个 Topic 移动到另一个 Topic
    IF OLD.topic_id IS NOT NULL AND OLD.topic_id != NEW.topic_id THEN
        -- 更新旧 Topic 的统计
        UPDATE topics
        SET 
            feedback_count = (
                SELECT COUNT(*) 
                FROM feedbacks 
                WHERE topic_id = OLD.topic_id 
                  AND deleted_at IS NULL
            ),
            -- ... 其他字段同上
            updated_time = NOW()
        WHERE id = OLD.topic_id;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 创建触发器
CREATE TRIGGER trigger_update_topic_stats
AFTER INSERT OR UPDATE OF topic_id ON feedbacks
FOR EACH ROW
EXECUTE FUNCTION update_topic_stats();
```

---

## 三、用户交互流程

### 3.1 录入 Feedback 时的全文检索

```
┌─────────────────────────────────────────────────────────┐
│  Step 1: 员工输入反馈内容                                 │
├─────────────────────────────────────────────────────────┤
│  Textarea: "希望支持暗黑模式，晚上看屏幕太刺眼了"           │
│  [实时检索中...]                                          │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│  Step 2: 全文检索相似 Topic（右侧显示）                    │
├─────────────────────────────────────────────────────────┤
│  🔍 发现 2 个相似主题：                                    │
│                                                          │
│  ┌────────────────────────────────────────────┐         │
│  │ ⭐ 支持暗黑模式                              │         │
│  │ 相似度: 95% | 15 条反馈 | 12 个客户          │         │
│  │ 总价值: ¥500,000 | 优先级: 125.5            │         │
│  │ [关联到此主题]                               │         │
│  └────────────────────────────────────────────┘         │
│                                                          │
│  ┌────────────────────────────────────────────┐         │
│  │ 夜间模式优化                                 │         │
│  │ 相似度: 78% | 5 条反馈 | 3 个客户            │         │
│  │ 总价值: ¥120,000 | 优先级: 45.2             │         │
│  │ [关联到此主题]                               │         │
│  └────────────────────────────────────────────┘         │
│                                                          │
│  [以上都不合适，创建新反馈]                               │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│  Step 3: 员工选择                                         │
├─────────────────────────────────────────────────────────┤
│  选项 A: 关联到已有 Topic                                 │
│    → Feedback.topic_id = 'topic_001'                    │
│    → Feedback.clustering_status = 'manual_linked'       │
│    → Topic 权重自动更新（触发器）                          │
│                                                          │
│  选项 B: 创建新 Feedback                                  │
│    → Feedback.topic_id = NULL                           │
│    → Feedback.clustering_status = 'pending'             │
│    → 等待 AI 异步聚类                                     │
└─────────────────────────────────────────────────────────┘
```

---

### 3.2 全文检索 API 设计

```python
@router.post("/topics/search")
async def search_similar_topics(
    query: str,
    tenant_id: str,
    limit: int = 5
) -> List[TopicSuggestion]:
    """
    全文检索相似 Topic
    
    检索策略：
    1. 使用 PostgreSQL 全文搜索（ts_vector）
    2. 结合向量相似度（embedding）
    3. 综合排序
    
    返回：
    [
        {
            "id": "topic_001",
            "title": "支持暗黑模式",
            "description": "用户希望在夜间使用时...",
            "similarity": 0.95,
            "feedback_count": 15,
            "affected_customer_count": 12,
            "total_mrr": 500000,
            "priority_score": 125.5
        }
    ]
    """
    # 1. 生成查询向量
    query_embedding = await ai_service.generate_embedding(query)
    
    # 2. 向量搜索（pgvector）
    vector_results = await db.execute(
        """
        SELECT 
            id, title, description,
            1 - (centroid <=> :embedding) AS similarity,
            feedback_count, affected_customer_count, 
            total_mrr, priority_score
        FROM topics
        WHERE tenant_id = :tenant_id
          AND deleted_at IS NULL
          AND 1 - (centroid <=> :embedding) > 0.7  -- 相似度阈值
        ORDER BY similarity DESC
        LIMIT :limit
        """,
        {"embedding": query_embedding, "tenant_id": tenant_id, "limit": limit}
    )
    
    # 3. 全文搜索（可选，作为补充）
    # fulltext_results = await db.execute(
    #     """
    #     SELECT id, title, ts_rank(search_vector, query) AS rank
    #     FROM topics, to_tsquery('chinese', :query) query
    #     WHERE search_vector @@ query
    #     ORDER BY rank DESC
    #     LIMIT :limit
    #     """
    # )
    
    return vector_results
```

---

### 3.3 创建 Feedback API（支持关联 Topic）

```python
@router.post("/feedbacks")
async def create_feedback(
    data: FeedbackCreate,
    link_to_topic_id: Optional[str] = None
) -> Feedback:
    """
    创建 Feedback
    
    参数：
    - data: Feedback 基础信息
    - link_to_topic_id: 可选，关联到已有 Topic
    
    流程：
    1. 创建 Feedback
    2. 如果指定了 topic_id，关联到 Topic（触发器自动更新 Topic 权重）
    3. 如果未指定 topic_id，标记为 pending，等待 AI 聚类
    """
    # 1. 获取客户信息（用于冗余字段）
    customer = await customer_service.get(data.customer_id)
    
    # 2. 生成 embedding
    embedding = await ai_service.generate_embedding(data.content)
    
    # 3. 创建 Feedback
    feedback = await db.execute(
        """
        INSERT INTO feedbacks (
            tenant_id, customer_id, customer_mrr, customer_tier,
            reporter_id, source, content, embedding,
            topic_id, clustering_status
        ) VALUES (
            :tenant_id, :customer_id, :customer_mrr, :customer_tier,
            :reporter_id, :source, :content, :embedding,
            :topic_id, :clustering_status
        )
        RETURNING *
        """,
        {
            "tenant_id": data.tenant_id,
            "customer_id": data.customer_id,
            "customer_mrr": customer.mrr,  # 冗余字段
            "customer_tier": customer.customer_tier,  # 冗余字段
            "reporter_id": data.reporter_id,
            "source": data.source,
            "content": data.content,
            "embedding": embedding,
            "topic_id": link_to_topic_id,
            "clustering_status": "manual_linked" if link_to_topic_id else "pending"
        }
    )
    
    # 4. 触发器会自动更新 Topic 权重
    
    return feedback
```

---

## 四、AI 异步聚类流程

### 4.1 聚类任务

```python
@celery_app.task
async def cluster_pending_feedbacks(tenant_id: str):
    """
    定时任务：聚类待处理的 Feedback
    
    流程：
    1. 查询 clustering_status = 'pending' 的 Feedback
    2. 使用 DBSCAN 聚类
    3. 为每个聚类创建 Topic
    4. 更新 Feedback.topic_id
    """
    # 1. 查询待聚类的 Feedback
    pending_feedbacks = await db.execute(
        """
        SELECT id, content, embedding
        FROM feedbacks
        WHERE tenant_id = :tenant_id
          AND clustering_status = 'pending'
          AND deleted_at IS NULL
        """,
        {"tenant_id": tenant_id}
    )
    
    if len(pending_feedbacks) < 3:
        return  # 数量太少，不聚类
    
    # 2. DBSCAN 聚类
    from sklearn.cluster import DBSCAN
    
    embeddings = [f.embedding for f in pending_feedbacks]
    clustering = DBSCAN(eps=0.15, min_samples=2, metric='cosine')
    labels = clustering.fit_predict(embeddings)
    
    # 3. 为每个聚类创建 Topic
    for cluster_id in set(labels):
        if cluster_id == -1:
            continue  # 噪声点，跳过
        
        # 获取该聚类的所有 Feedback
        cluster_feedbacks = [
            f for i, f in enumerate(pending_feedbacks) 
            if labels[i] == cluster_id
        ]
        
        # 计算中心向量
        centroid = np.mean([f.embedding for f in cluster_feedbacks], axis=0)
        
        # AI 生成 Topic 标题和描述
        topic_title = await ai_service.generate_topic_title(
            [f.content for f in cluster_feedbacks]
        )
        
        # 创建 Topic
        topic = await db.execute(
            """
            INSERT INTO topics (tenant_id, title, centroid, ai_generated)
            VALUES (:tenant_id, :title, :centroid, TRUE)
            RETURNING id
            """,
            {
                "tenant_id": tenant_id,
                "title": topic_title,
                "centroid": centroid.tolist()
            }
        )
        
        # 更新 Feedback.topic_id
        await db.execute(
            """
            UPDATE feedbacks
            SET topic_id = :topic_id, clustering_status = 'clustered'
            WHERE id = ANY(:feedback_ids)
            """,
            {
                "topic_id": topic.id,
                "feedback_ids": [f.id for f in cluster_feedbacks]
            }
        )
        
        # 触发器会自动更新 Topic 权重
```

---

## 五、核心查询示例

### 5.1 获取优先级最高的 Topic

```sql
SELECT 
    t.id,
    t.title,
    t.description,
    t.priority_score,
    t.feedback_count,
    t.affected_customer_count,
    t.total_mrr,
    t.impact_scope,
    t.dev_cost_estimate,
    t.internal_status,
    u.username AS product_owner,
    -- 关联的客户列表
    (
        SELECT STRING_AGG(DISTINCT c.name, ', ')
        FROM feedbacks f
        JOIN customers c ON f.customer_id = c.id
        WHERE f.topic_id = t.id AND f.deleted_at IS NULL
    ) AS affected_customers
FROM topics t
LEFT JOIN sys_user u ON t.product_owner_id = u.id
WHERE t.tenant_id = $tenant_id
  AND t.deleted_at IS NULL
  AND t.internal_status IN ('pending', 'evaluating', 'approved')
ORDER BY t.priority_score DESC NULLS LAST
LIMIT 20;
```

**输出示例**：
```
| 主题 | 优先级 | 反馈数 | 客户数 | 总MRR | 影响范围 | 成本 | 受影响客户 |
|------|--------|--------|--------|-------|---------|------|-----------|
| 支持暗黑模式 | 125.5 | 15 | 12 | 500,000 | 8 | 6 | 某银行, 某保险, ... |
| 导出Excel | 98.2 | 10 | 8 | 300,000 | 7 | 3 | 某证券, 某基金, ... |
```

---

### 5.2 查看 Topic 的所有原始 Feedback

```sql
SELECT 
    f.id,
    f.content,
    f.ai_summary,
    c.name AS customer_name,
    c.customer_tier,
    c.mrr AS customer_mrr,
    u.username AS reporter,
    f.source,
    f.source_platform,
    f.sentiment,
    f.submitted_at
FROM feedbacks f
LEFT JOIN customers c ON f.customer_id = c.id
LEFT JOIN sys_user u ON f.reporter_id = u.id
WHERE f.topic_id = $topic_id
  AND f.deleted_at IS NULL
ORDER BY f.submitted_at DESC;
```

**使用场景**：
- 产品经理查看某个需求的所有原始反馈
- 了解反馈来源（哪些客户、哪些渠道）
- 评估需求的真实性和紧迫性

---

### 5.3 溯源分析：某个客户的所有反馈

```sql
SELECT 
    f.id,
    f.content,
    t.title AS topic_title,
    t.priority_score,
    t.internal_status,
    u.username AS reporter,
    f.source,
    f.submitted_at
FROM feedbacks f
LEFT JOIN topics t ON f.topic_id = t.id
LEFT JOIN sys_user u ON f.reporter_id = u.id
WHERE f.customer_id = $customer_id
  AND f.deleted_at IS NULL
ORDER BY f.submitted_at DESC;
```

**使用场景**：
- 客户成功团队查看某个客户的所有反馈
- 评估客户满意度
- 准备客户续约材料

---

## 六、数据迁移方案

### 6.1 迁移步骤

```sql
-- Step 1: 新增字段（不影响现有数据）
ALTER TABLE feedbacks ADD COLUMN IF NOT EXISTS
    customer_mrr DECIMAL(10,2);

ALTER TABLE feedbacks ADD COLUMN IF NOT EXISTS
    customer_tier VARCHAR(20);

ALTER TABLE feedbacks ADD COLUMN IF NOT EXISTS
    reporter_id INTEGER REFERENCES sys_user(id);

-- Step 2: 回填数据
UPDATE feedbacks f
SET 
    customer_mrr = c.mrr,
    customer_tier = c.customer_tier
FROM customers c
WHERE f.customer_id = c.id;

-- Step 3: 更新 Topics 表
ALTER TABLE topics ADD COLUMN IF NOT EXISTS
    feedback_count INTEGER DEFAULT 0;

ALTER TABLE topics ADD COLUMN IF NOT EXISTS
    affected_customer_count INTEGER DEFAULT 0;

ALTER TABLE topics ADD COLUMN IF NOT EXISTS
    total_mrr DECIMAL(10,2) DEFAULT 0;

-- Step 4: 回填 Topic 统计数据
UPDATE topics t
SET 
    feedback_count = (
        SELECT COUNT(*) 
        FROM feedbacks 
        WHERE topic_id = t.id AND deleted_at IS NULL
    ),
    affected_customer_count = (
        SELECT COUNT(DISTINCT customer_id) 
        FROM feedbacks 
        WHERE topic_id = t.id AND deleted_at IS NULL
    ),
    total_mrr = (
        SELECT COALESCE(SUM(DISTINCT customer_mrr), 0)
        FROM feedbacks 
        WHERE topic_id = t.id AND deleted_at IS NULL
    );

-- Step 5: 创建触发器
CREATE TRIGGER trigger_update_topic_stats
AFTER INSERT OR UPDATE OF topic_id ON feedbacks
FOR EACH ROW
EXECUTE FUNCTION update_topic_stats();
```

---

## 七、总结

### 7.1 核心优势

✅ **数据模型清晰**
- Feedback：原始数据层，不可合并
- Topic：聚合层，承载权重计算

✅ **溯源能力强**
- 每条 Feedback 都保留完整的来源信息
- 支持按客户、录入人、渠道等维度分析

✅ **权重计算准确**
- 基于所有关联 Feedback 的客户价值聚合
- 自动更新（触发器）

✅ **用户体验好**
- 全文检索 Topic（不检索 Feedback）
- 可选关联，不强制
- AI 兜底（异步聚类）

### 7.2 与之前方案的差异

| 维度 | 之前方案 | 最终方案 |
|------|---------|---------|
| Feedback 合并 | ✅ 支持 | ❌ 不支持 |
| 检索对象 | Topic + Feedback | 仅 Topic |
| 数据冗余 | 通过合并减少 | 保留所有原始数据 |
| 溯源能力 | ⚠️ 合并后丢失 | ✅ 完整保留 |
| 权重计算 | 基于主 Feedback | 基于所有 Feedback |

### 7.3 下一步行动

1. ✅ Review 本设计文档
2. ⏳ 生成 Alembic 迁移脚本
3. ⏳ 实现全文检索 API
4. ⏳ 实现触发器
5. ⏳ 前端交互界面

---

**文档维护者**: 技术团队  
**最后更新**: 2025-12-31
