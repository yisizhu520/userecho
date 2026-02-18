# userecho 数据库设计 - 中国版（降本增效 + 辅助决策）

> **版本**: v3.0  
> **更新日期**: 2025-12-31  
> **设计理念**: 符合中国国情，专注内部效率提升和商业决策支持，最大化复用现有代码

---

## 一、核心定位变化

### 1.1 从 Canny 模式到决策中台

| 维度 | Canny 模式 | 我们的新定位 |
|------|-----------|------------|
| **核心用户** | 外部用户（C端） | 内部员工（销售/客服/产品） |
| **数据来源** | 用户主动提交 | 员工录入客户反馈 |
| **优先级机制** | 投票数 | 客户价值 × 影响范围 |
| **核心价值** | 社区透明化 | 降本增效 + 辅助决策 |
| **公开性** | 公开看板 | 内部私有 |

### 1.2 保留的核心优势

✅ **截图识别**：微信/小红书/App Store 截图自动解析  
✅ **AI 聚类**：自动合并相似反馈，生成主题  
✅ **Excel 导入**：快速迁移历史数据  
✅ **情感分析**：识别客户情绪，优先处理负面反馈  
✅ **多租户架构**：支持 SaaS 模式

---

## 二、数据库设计原则

### 2.1 复用现有代码

**最小化改动策略**：
- ✅ 保留现有表结构：`feedbacks`, `customers`, `topics`, `tenants`
- ✅ 保留现有字段：`embedding`, `ai_summary`, `sentiment`
- ✅ 仅做增量优化：新增必要字段，不删除现有字段

### 2.2 新增核心能力

1. **客户价值权重**：关联 CRM 数据，按客户重要性排序
2. **需求进度透明**：内部看板，销售可查看需求状态
3. **决策辅助评分**：自动计算优先级 = 客户价值 × 影响范围 / 开发成本
4. **AI 周报生成**：自动生成产品情报周报

---

## 三、核心表设计（基于现有代码优化）

### 3.1 Feedbacks 表（增量优化）

**现有字段保持不变**，仅新增以下字段：

```sql
-- 现有表：feedbacks
-- 新增字段：

ALTER TABLE feedbacks ADD COLUMN IF NOT EXISTS 
    -- 关联客户价值
    customer_mrr DECIMAL(10,2) DEFAULT NULL COMMENT '客户月收入（冗余字段，便于排序）';

ALTER TABLE feedbacks ADD COLUMN IF NOT EXISTS
    -- 影响范围评估
    impact_scope INTEGER DEFAULT NULL COMMENT '影响范围评分 (1-10)，由产品经理标注';

ALTER TABLE feedbacks ADD COLUMN IF NOT EXISTS
    -- 开发成本预估
    dev_cost_estimate INTEGER DEFAULT NULL COMMENT '开发成本评分 (1-10)，由技术负责人标注';

ALTER TABLE feedbacks ADD COLUMN IF NOT EXISTS
    -- 优先级自动计算
    priority_score DECIMAL(10,2) GENERATED ALWAYS AS (
        COALESCE(customer_mrr, 0) * COALESCE(impact_scope, 1) / NULLIF(COALESCE(dev_cost_estimate, 5), 0)
    ) STORED COMMENT '优先级分数 = 客户价值 × 影响范围 / 成本';

ALTER TABLE feedbacks ADD COLUMN IF NOT EXISTS
    -- 需求状态（内部流转）
    internal_status VARCHAR(20) DEFAULT 'pending' COMMENT 'pending, evaluating, approved, rejected, in_dev, released';

ALTER TABLE feedbacks ADD COLUMN IF NOT EXISTS
    -- 关联的销售/客服人员
    reporter_id INTEGER REFERENCES sys_user(id) COMMENT '录入人（销售/客服）';

ALTER TABLE feedbacks ADD COLUMN IF NOT EXISTS
    -- 产品负责人
    product_owner_id INTEGER REFERENCES sys_user(id) COMMENT '产品负责人';

CREATE INDEX idx_feedbacks_priority ON feedbacks(priority_score DESC NULLS LAST);
CREATE INDEX idx_feedbacks_internal_status ON feedbacks(internal_status);
CREATE INDEX idx_feedbacks_reporter ON feedbacks(reporter_id);
```

**设计理由**：
- ✅ 保留所有现有字段（`content`, `embedding`, `ai_summary`, `sentiment` 等）
- ✅ 新增字段支持决策辅助（优先级评分）
- ✅ 新增字段支持内部协作（录入人、负责人）

---

### 3.2 Customers 表（增量优化）

**现有字段保持不变**，新增以下字段：

```sql
-- 现有表：customers
-- 新增字段：

ALTER TABLE customers ADD COLUMN IF NOT EXISTS
    -- CRM 关联
    crm_id VARCHAR(100) DEFAULT NULL COMMENT '外部 CRM 系统客户 ID';

ALTER TABLE customers ADD COLUMN IF NOT EXISTS
    -- 月经常性收入
    mrr DECIMAL(10,2) DEFAULT NULL COMMENT '月经常性收入（Monthly Recurring Revenue）';

ALTER TABLE customers ADD COLUMN IF NOT EXISTS
    -- 客户等级（更细化）
    customer_tier VARCHAR(20) DEFAULT 'normal' COMMENT 'free, normal, paid, vip, strategic';

ALTER TABLE customers ADD COLUMN IF NOT EXISTS
    -- 流失风险
    churn_risk VARCHAR(20) DEFAULT 'low' COMMENT 'low, medium, high';

ALTER TABLE customers ADD COLUMN IF NOT EXISTS
    -- 合同到期时间
    contract_end_date DATE DEFAULT NULL COMMENT '合同到期日期';

ALTER TABLE customers ADD COLUMN IF NOT EXISTS
    -- 客户标签
    tags TEXT[] DEFAULT '{}' COMMENT '客户标签数组，如 ["信创", "金融", "重点客户"]';

CREATE INDEX idx_customers_mrr ON customers(mrr DESC NULLS LAST);
CREATE INDEX idx_customers_tier ON customers(customer_tier);
CREATE INDEX idx_customers_churn_risk ON customers(churn_risk);
CREATE INDEX idx_customers_tags ON customers USING gin(tags);
```

**设计理由**：
- ✅ 支持按 MRR 排序（高价值客户优先）
- ✅ 支持流失风险预警（优先处理高风险客户反馈）
- ✅ 支持客户分群（按标签筛选）

---

### 3.3 Topics 表（增量优化）

**现有字段保持不变**，新增以下字段：

```sql
-- 现有表：topics
-- 新增字段：

ALTER TABLE topics ADD COLUMN IF NOT EXISTS
    -- 商业价值评分
    business_value_score DECIMAL(10,2) DEFAULT NULL COMMENT '商业价值总分（所有关联反馈的客户 MRR 之和）';

ALTER TABLE topics ADD COLUMN IF NOT EXISTS
    -- 影响客户数
    affected_customer_count INTEGER DEFAULT 0 COMMENT '受影响的客户数量';

ALTER TABLE topics ADD COLUMN IF NOT EXISTS
    -- 开发成本预估
    dev_cost_estimate INTEGER DEFAULT NULL COMMENT '开发成本评分 (1-10)';

ALTER TABLE topics ADD COLUMN IF NOT EXISTS
    -- 优先级自动计算
    priority_score DECIMAL(10,2) GENERATED ALWAYS AS (
        COALESCE(business_value_score, 0) * COALESCE(affected_customer_count, 1) / NULLIF(COALESCE(dev_cost_estimate, 5), 0)
    ) STORED COMMENT '优先级 = 商业价值 × 客户数 / 成本';

ALTER TABLE topics ADD COLUMN IF NOT EXISTS
    -- 内部状态
    internal_status VARCHAR(20) DEFAULT 'pending' COMMENT 'pending, evaluating, approved, rejected, planned, in_dev, released';

ALTER TABLE topics ADD COLUMN IF NOT EXISTS
    -- 产品负责人
    product_owner_id INTEGER REFERENCES sys_user(id) COMMENT '产品负责人';

ALTER TABLE topics ADD COLUMN IF NOT EXISTS
    -- 预计发布时间
    estimated_release_date DATE DEFAULT NULL COMMENT '预计发布日期';

CREATE INDEX idx_topics_priority ON topics(priority_score DESC NULLS LAST);
CREATE INDEX idx_topics_internal_status ON topics(internal_status);
```

**设计理由**：
- ✅ 自动计算商业价值（聚合所有关联反馈的客户价值）
- ✅ 支持按优先级排序（老板一眼看出该做什么）
- ✅ 支持内部流程管理（评审 → 排期 → 开发 → 发布）

---

### 3.4 新增表：Feedback Progress Tracking（需求进度跟踪）

**解决痛点**：销售不停问 PM "那个需求什么时候做？"

```sql
CREATE TABLE feedback_progress (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4(),
    feedback_id VARCHAR(36) NOT NULL REFERENCES feedbacks(id) ON DELETE CASCADE,
    
    -- 状态变更
    from_status VARCHAR(20),
    to_status VARCHAR(20) NOT NULL,
    
    -- 变更人
    changed_by INTEGER REFERENCES sys_user(id),
    
    -- 变更原因
    change_reason TEXT,
    
    -- 通知相关人员
    notify_users INTEGER[] DEFAULT '{}' COMMENT '需要通知的用户 ID 列表',
    
    -- 时间戳
    changed_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- 索引
    INDEX idx_progress_feedback (feedback_id, changed_at DESC)
);

COMMENT ON TABLE feedback_progress IS '反馈进度跟踪表，记录所有状态变更';
```

**使用场景**：
- 销售在飞书/钉钉中查看自己提交的反馈进度
- 自动通知：需求状态变更时，通知录入人

---

### 3.5 新增表：Weekly Insights（AI 周报）

**解决痛点**：PM 需要手动整理反馈，耗时费力

```sql
CREATE TABLE weekly_insights (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id VARCHAR(36) NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    
    -- 周报时间范围
    week_start_date DATE NOT NULL,
    week_end_date DATE NOT NULL,
    
    -- AI 生成的内容
    summary TEXT NOT NULL COMMENT 'AI 生成的周报摘要',
    
    -- 结构化数据
    top_topics JSONB COMMENT '本周热门主题 Top 5',
    /*
    示例：
    [
        {
            "topic_id": "topic_001",
            "title": "支持暗黑模式",
            "feedback_count": 15,
            "total_mrr": 50000,
            "priority_score": 8.5
        }
    ]
    */
    
    top_customers JSONB COMMENT '本周反馈最多的客户 Top 5',
    sentiment_distribution JSONB COMMENT '情感分布统计',
    
    -- 发布状态
    is_published BOOLEAN DEFAULT FALSE,
    published_at TIMESTAMPTZ,
    
    -- 时间戳
    created_time TIMESTAMPTZ DEFAULT NOW(),
    
    -- 索引
    UNIQUE(tenant_id, week_start_date)
);

CREATE INDEX idx_insights_tenant_week ON weekly_insights(tenant_id, week_start_date DESC);
```

**使用场景**：
- 每周一自动生成上周的产品情报周报
- PM 只需审核并分发给团队

---

### 3.6 新增表：Decision Rules（决策规则配置）

**解决痛点**：不同公司的优先级计算逻辑不同

```sql
CREATE TABLE decision_rules (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id VARCHAR(36) NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    
    -- 规则名称
    rule_name VARCHAR(100) NOT NULL,
    
    -- 规则类型
    rule_type VARCHAR(20) NOT NULL COMMENT 'priority_formula, auto_approval, alert',
    
    -- 规则配置
    rule_config JSONB NOT NULL,
    /*
    示例（优先级公式）：
    {
        "formula": "mrr * impact_scope / dev_cost",
        "weights": {
            "mrr": 1.0,
            "impact_scope": 1.5,
            "dev_cost": 1.0
        },
        "thresholds": {
            "high": 100,
            "medium": 50,
            "low": 0
        }
    }
    
    示例（自动审批）：
    {
        "conditions": [
            {"field": "customer_tier", "operator": "=", "value": "strategic"},
            {"field": "sentiment", "operator": "=", "value": "negative"}
        ],
        "action": "auto_approve"
    }
    */
    
    -- 是否启用
    is_enabled BOOLEAN DEFAULT TRUE,
    
    -- 时间戳
    created_time TIMESTAMPTZ DEFAULT NOW(),
    updated_time TIMESTAMPTZ,
    
    -- 索引
    INDEX idx_rules_tenant_type (tenant_id, rule_type)
);
```

**使用场景**：
- 老板可以自定义优先级计算公式
- 设置自动审批规则（如：战略客户的负面反馈自动标记为高优先级）

---

## 四、核心查询示例

### 4.1 获取优先级最高的需求（决策支持）

```sql
SELECT 
    t.id,
    t.title,
    t.description,
    t.priority_score,
    t.business_value_score,
    t.affected_customer_count,
    t.dev_cost_estimate,
    t.internal_status,
    u.username AS product_owner,
    COUNT(f.id) AS feedback_count,
    STRING_AGG(DISTINCT c.name, ', ') AS affected_customers
FROM topics t
LEFT JOIN feedbacks f ON t.id = f.topic_id
LEFT JOIN customers c ON f.customer_id = c.id
LEFT JOIN sys_user u ON t.product_owner_id = u.id
WHERE t.tenant_id = $tenant_id
  AND t.deleted_at IS NULL
  AND t.internal_status IN ('pending', 'evaluating', 'approved')
GROUP BY t.id, u.username
ORDER BY t.priority_score DESC NULLS LAST
LIMIT 20;
```

**输出示例**：
```
| 主题 | 优先级分数 | 商业价值 | 客户数 | 成本 | 状态 | 负责人 |
|------|-----------|---------|--------|------|------|--------|
| 支持暗黑模式 | 125.5 | 500,000 | 15 | 6 | 待评审 | 张三 |
| 导出 Excel | 98.2 | 300,000 | 12 | 3 | 已批准 | 李四 |
```

---

### 4.2 查看销售录入的反馈进度（降本增效）

```sql
SELECT 
    f.id,
    f.ai_summary AS title,
    f.internal_status,
    c.name AS customer_name,
    c.customer_tier,
    u.username AS reporter,
    fp.changed_at AS last_update,
    fp.change_reason
FROM feedbacks f
JOIN customers c ON f.customer_id = c.id
JOIN sys_user u ON f.reporter_id = u.id
LEFT JOIN LATERAL (
    SELECT changed_at, change_reason
    FROM feedback_progress
    WHERE feedback_id = f.id
    ORDER BY changed_at DESC
    LIMIT 1
) fp ON TRUE
WHERE f.reporter_id = $sales_user_id
  AND f.deleted_at IS NULL
ORDER BY f.created_time DESC;
```

**使用场景**：
- 销售在飞书中查看自己提交的所有反馈状态
- 减少销售主动询问 PM 的次数

---

### 4.3 高风险客户预警（辅助决策）

```sql
SELECT 
    c.id,
    c.name,
    c.customer_tier,
    c.mrr,
    c.churn_risk,
    c.contract_end_date,
    COUNT(f.id) FILTER (WHERE f.sentiment = 'negative') AS negative_feedback_count,
    AVG(f.sentiment_score) AS avg_sentiment_score,
    STRING_AGG(f.ai_summary, '; ' ORDER BY f.created_time DESC) AS recent_feedbacks
FROM customers c
LEFT JOIN feedbacks f ON c.id = f.customer_id
WHERE c.tenant_id = $tenant_id
  AND c.deleted_at IS NULL
  AND (
      c.churn_risk = 'high'
      OR (c.contract_end_date < NOW() + INTERVAL '30 days' AND c.contract_end_date > NOW())
  )
GROUP BY c.id
HAVING COUNT(f.id) FILTER (WHERE f.sentiment = 'negative') > 0
ORDER BY c.mrr DESC, negative_feedback_count DESC;
```

**输出示例**：
```
| 客户 | MRR | 流失风险 | 合同到期 | 负面反馈数 | 平均情感分 |
|------|-----|---------|---------|-----------|----------|
| 某银行 | 50,000 | 高 | 2025-02-15 | 5 | -0.6 |
```

---

## 五、数据迁移方案

### 5.1 迁移步骤

```sql
-- Step 1: 新增字段（不影响现有数据）
ALTER TABLE feedbacks ADD COLUMN customer_mrr DECIMAL(10,2);
ALTER TABLE feedbacks ADD COLUMN impact_scope INTEGER;
-- ... 其他字段

-- Step 2: 回填数据
UPDATE feedbacks f
SET customer_mrr = c.mrr
FROM customers c
WHERE f.customer_id = c.id;

-- Step 3: 创建新表
CREATE TABLE feedback_progress (...);
CREATE TABLE weekly_insights (...);
CREATE TABLE decision_rules (...);

-- Step 4: 创建索引
CREATE INDEX idx_feedbacks_priority ON feedbacks(priority_score DESC NULLS LAST);
```

### 5.2 兼容性保证

✅ **现有 API 不受影响**：新增字段均为可选字段  
✅ **现有查询不受影响**：不删除任何现有字段  
✅ **渐进式升级**：可以先上线部分功能，逐步完善

---

## 六、与现有代码的集成

### 6.1 复用现有模型

**现有模型保持不变**：
- `app/userecho/model/feedback.py` → 新增字段
- `app/userecho/model/customer.py` → 新增字段
- `app/userecho/model/topic.py` → 新增字段

**新增模型**：
- `app/userecho/model/feedback_progress.py`
- `app/userecho/model/weekly_insights.py`
- `app/userecho/model/decision_rules.py`

### 6.2 复用现有服务

**现有服务保持不变**：
- `app/userecho/service/feedback_service.py` → 新增优先级计算方法
- `app/userecho/service/customer_service.py` → 新增客户价值评估方法

**新增服务**：
- `app/userecho/service/decision_service.py` → 决策辅助服务
- `app/userecho/service/insights_service.py` → AI 周报生成服务

---

## 七、核心功能实现路径

### 7.1 Phase 1: 基础优化（1 周）

- [x] 新增 Feedback/Customer/Topic 表字段
- [x] 实现优先级自动计算
- [x] 实现客户价值排序

### 7.2 Phase 2: 进度透明（1 周）

- [ ] 创建 `feedback_progress` 表
- [ ] 实现状态变更通知
- [ ] 飞书/钉钉集成（销售查看进度）

### 7.3 Phase 3: AI 周报（1 周）

- [ ] 创建 `weekly_insights` 表
- [ ] 实现 AI 周报生成逻辑
- [ ] 自动发送周报到飞书群

### 7.4 Phase 4: 决策规则（1 周）

- [ ] 创建 `decision_rules` 表
- [ ] 实现自定义优先级公式
- [ ] 实现自动审批规则

---

## 八、与竞品对比

| 特性 | Canny | 我们的方案 |
|------|-------|----------|
| **核心用户** | 外部用户 | 内部员工 |
| **数据来源** | 用户主动提交 | 员工录入 + 截图识别 |
| **优先级** | 投票数 | 客户价值 × 影响范围 / 成本 |
| **公开性** | 公开看板 | 内部私有 |
| **决策支持** | ❌ | ✅ AI 周报 + 优先级评分 |
| **中国特色** | ❌ | ✅ 截图识别 + 飞书集成 |

---

## 九、总结

### 9.1 核心优势

✅ **最大化复用现有代码**：仅做增量优化，不推倒重来  
✅ **符合中国国情**：内部驱动，不依赖外部用户参与  
✅ **降本增效**：减少无效沟通，提升协作效率  
✅ **辅助决策**：自动计算优先级，老板一眼看出该做什么  

### 9.2 下一步行动

1. ✅ Review 本设计文档
2. ⏳ 生成 Alembic 迁移脚本
3. ⏳ 更新 Pydantic Schema
4. ⏳ 实现核心 API 接口
5. ⏳ 飞书/钉钉集成

---

**文档维护者**: 技术团队  
**最后更新**: 2025-12-31
