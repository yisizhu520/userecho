# Feedalyze 最终完整数据库设计

> **版本**: v6.0 - Final Complete  
> **更新日期**: 2025-12-31  
> **核心定位**: 企业内部反馈管理平台（To B SaaS）

---

## 一、核心概念澄清

### 1.1 用户角色定义

```
平台用户（Users）
    ├─ 定义：我们平台的用户（企业内部员工）
    ├─ 角色：产品经理、销售、客服、技术负责人等
    ├─ 权限：登录平台、录入反馈、管理需求
    └─ 存储：users 表 + tenant_users 表
         
客户（Customers）
    ├─ 定义：Tenant 的终端用户（不是平台用户）
    ├─ 角色：使用 Tenant 产品的客户
    ├─ 权限：无（不登录我们的平台）
    └─ 存储：customers 表（由 Tenant 管理）
```

**示例**：
```
Tenant A（某 SaaS 公司）:
  ├─ 平台用户：
  │   ├─ 张三（产品经理）→ users 表
  │   ├─ 李四（销售）→ users 表
  │   └─ 王五（客服）→ users 表
  │
  └─ 客户（Tenant A 的终端用户）：
      ├─ 某银行（VIP 客户，MRR=50000）→ customers 表
      ├─ 某保险（付费客户，MRR=20000）→ customers 表
      └─ 某证券（免费客户）→ customers 表
```

---

## 二、核心表设计

### 2.1 租户与平台用户

#### Tenants（租户表）

```sql
CREATE TABLE tenants (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- 租户基础信息
    name VARCHAR(100) NOT NULL COMMENT '租户名称，如 "某科技公司"',
    slug VARCHAR(100) UNIQUE NOT NULL COMMENT 'URL slug，如 "acme-corp"',
    
    -- 租户状态
    status VARCHAR(20) DEFAULT 'active' COMMENT 'active, suspended, deleted',
    
    -- 配置
    settings JSONB DEFAULT '{}' COMMENT '租户配置',
    
    -- 时间戳
    created_time TIMESTAMPTZ DEFAULT NOW(),
    updated_time TIMESTAMPTZ,
    
    INDEX idx_tenants_slug (slug),
    INDEX idx_tenants_status (status)
);

COMMENT ON TABLE tenants IS '租户表（SaaS 多租户架构）';
```

---

#### Users（平台用户表 - 全局）

**定义**：我们平台的用户（企业内部员工），不包含 tenant_id

```sql
CREATE TABLE users (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- 全局唯一标识
    email VARCHAR(255) UNIQUE NOT NULL COMMENT '全局唯一邮箱',
    phone VARCHAR(20),
    
    -- 基础信息
    name VARCHAR(100) COMMENT '真实姓名',
    nickname VARCHAR(100) COMMENT '显示昵称',
    avatar_url VARCHAR(500),
    
    -- 第三方登录
    wechat_openid VARCHAR(100) UNIQUE,
    wechat_unionid VARCHAR(100),
    google_id VARCHAR(100) UNIQUE,
    
    -- 账号状态
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    
    -- 时间戳
    created_time TIMESTAMPTZ DEFAULT NOW(),
    last_login_time TIMESTAMPTZ,
    updated_time TIMESTAMPTZ,
    
    INDEX idx_users_email (email),
    INDEX idx_users_wechat (wechat_openid) WHERE wechat_openid IS NOT NULL
);

COMMENT ON TABLE users IS '平台用户表（企业内部员工，全局表，无 tenant_id）';
```

---

#### TenantUsers（租户-用户关联表）

**定义**：一个平台用户可以在多个租户中扮演不同角色

```sql
CREATE TABLE tenant_users (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id VARCHAR(36) NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- 用户类型（在该租户中的角色）
    user_type VARCHAR(20) NOT NULL COMMENT 'admin, product_manager, sales, customer_success, developer',
    
    -- 部门信息
    department_id BIGINT REFERENCES sys_dept(id),
    
    -- 统计（租户内）
    feedback_count INTEGER DEFAULT 0 COMMENT '录入的反馈数',
    
    -- 状态
    status VARCHAR(20) DEFAULT 'active' COMMENT 'active, suspended, left',
    
    -- 时间戳
    joined_at TIMESTAMPTZ DEFAULT NOW(),
    last_active_at TIMESTAMPTZ,
    
    UNIQUE(tenant_id, user_id),
    INDEX idx_tenant_users_tenant (tenant_id),
    INDEX idx_tenant_users_user (user_id),
    INDEX idx_tenant_users_type (user_type)
);

COMMENT ON TABLE tenant_users IS '租户-用户关联表（支持一个用户在多个租户中有不同角色）';
COMMENT ON COLUMN tenant_users.user_type IS 'admin: 管理员, product_manager: 产品经理, sales: 销售, customer_success: 客服, developer: 开发';

-- 示例数据
-- 用户张三 (user_001):
--   ├─ Tenant A: user_type='product_manager'
--   ├─ Tenant B: user_type='admin'
--   └─ Tenant C: user_type='sales'
```

---

#### TenantUserRoles（租户用户角色关联表）

```sql
CREATE TABLE tenant_user_roles (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_user_id VARCHAR(36) NOT NULL REFERENCES tenant_users(id) ON DELETE CASCADE,
    role_id BIGINT NOT NULL REFERENCES sys_role(id) ON DELETE CASCADE,
    
    -- 分配信息
    assigned_by VARCHAR(36) REFERENCES users(id),
    assigned_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(tenant_user_id, role_id),
    INDEX idx_tenant_user_roles_tenant_user (tenant_user_id),
    INDEX idx_tenant_user_roles_role (role_id)
);

COMMENT ON TABLE tenant_user_roles IS '租户用户角色关联表（RBAC 权限系统）';
```

---

### 2.2 客户管理

#### Customers（客户表）

**定义**：Tenant 的终端用户（不是平台用户），由 Tenant 自己管理

```sql
CREATE TABLE customers (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id VARCHAR(36) NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    
    -- 客户基础信息
    name VARCHAR(100) NOT NULL COMMENT '客户名称',
    company_name VARCHAR(200) COMMENT '公司名称',
    contact_email VARCHAR(255) COMMENT '联系邮箱',
    contact_phone VARCHAR(50) COMMENT '联系电话',
    
    -- 客户分类
    customer_type VARCHAR(20) DEFAULT 'normal' COMMENT 'normal, paid, vip, strategic',
    customer_tier VARCHAR(20) DEFAULT 'normal' COMMENT 'free, normal, paid, vip, strategic',
    business_value INTEGER DEFAULT 1 COMMENT '商业价值权重 (1-10)',
    
    -- 商业数据
    mrr DECIMAL(10,2) COMMENT '月经常性收入（Monthly Recurring Revenue）',
    arr DECIMAL(10,2) COMMENT '年经常性收入（Annual Recurring Revenue）',
    churn_risk VARCHAR(20) DEFAULT 'low' COMMENT 'low, medium, high',
    contract_start_date DATE COMMENT '合同开始日期',
    contract_end_date DATE COMMENT '合同结束日期',
    
    -- 客户标签
    tags TEXT[] DEFAULT '{}' COMMENT '客户标签数组，如 ["信创", "金融", "重点客户"]',
    
    -- 客户来源
    source VARCHAR(50) COMMENT '客户来源：direct, referral, marketing, etc.',
    
    -- 备注
    notes TEXT COMMENT '客户备注',
    
    -- 时间戳
    created_time TIMESTAMPTZ DEFAULT NOW(),
    updated_time TIMESTAMPTZ,
    deleted_at TIMESTAMPTZ COMMENT '软删除',
    
    INDEX idx_customers_tenant (tenant_id),
    INDEX idx_customers_mrr (mrr DESC NULLS LAST),
    INDEX idx_customers_tier (customer_tier),
    INDEX idx_customers_churn_risk (churn_risk),
    INDEX idx_customers_tags USING gin(tags)
);

COMMENT ON TABLE customers IS '客户表（Tenant 的终端用户，不是平台用户，由 Tenant 管理）';
COMMENT ON COLUMN customers.mrr IS '月经常性收入，用于计算 Topic 优先级';
COMMENT ON COLUMN customers.churn_risk IS '流失风险，用于优先处理高风险客户的反馈';
```

---

### 2.3 Board 组织系统

#### Boards（看板表）

```sql
CREATE TABLE boards (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id VARCHAR(36) NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    
    -- Board 基础信息
    name VARCHAR(100) NOT NULL COMMENT '看板名称，如 "移动端反馈"',
    url_name VARCHAR(100) NOT NULL COMMENT 'URL slug，如 "mobile-feedback"',
    description TEXT COMMENT '看板描述',
    
    -- 访问控制
    access_mode VARCHAR(20) DEFAULT 'private' COMMENT 'public, private, restricted',
    allowed_user_ids TEXT[] DEFAULT '{}' COMMENT 'restricted 模式下允许访问的用户 ID 列表',
    
    -- 分类/标签
    category VARCHAR(50) COMMENT '看板分类，如 "mobile", "web", "api"',
    tags TEXT[] DEFAULT '{}' COMMENT '看板标签',
    
    -- 统计
    feedback_count INTEGER DEFAULT 0,
    topic_count INTEGER DEFAULT 0,
    
    -- 配置
    settings JSONB DEFAULT '{}' COMMENT 'Board 特定配置',
    /*
    示例：
    {
        "allow_anonymous_feedback": false,
        "require_approval": true,
        "auto_clustering": true,
        "clustering_schedule": "daily"
    }
    */
    
    -- 排序与显示
    sort_order INTEGER DEFAULT 0,
    is_archived BOOLEAN DEFAULT FALSE,
    
    -- 时间戳
    created_time TIMESTAMPTZ DEFAULT NOW(),
    updated_time TIMESTAMPTZ,
    
    UNIQUE(tenant_id, url_name),
    INDEX idx_boards_tenant (tenant_id),
    INDEX idx_boards_category (category),
    INDEX idx_boards_archived (is_archived)
);

COMMENT ON TABLE boards IS '看板表（支持多维度组织：移动端/Web端/不同产品线）';
COMMENT ON COLUMN boards.access_mode IS 'private: 仅内部员工可见（默认）, public: 公开, restricted: 指定用户可见';
```

---

### 2.4 核心业务表

#### Feedbacks（反馈表）

**定义**：原始数据层，记录所有反馈，不可合并

```sql
CREATE TABLE feedbacks (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id VARCHAR(36) NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    board_id VARCHAR(36) NOT NULL REFERENCES boards(id) ON DELETE CASCADE,
    
    -- 关联 Topic（可为空，等待 AI 聚类）
    topic_id VARCHAR(36) REFERENCES topics(id) ON DELETE SET NULL,
    
    -- 客户信息（权重计算基础）
    customer_id VARCHAR(36) REFERENCES customers(id) ON DELETE SET NULL,
    customer_mrr DECIMAL(10,2) COMMENT '客户月收入（冗余字段，便于聚合）',
    customer_tier VARCHAR(20) COMMENT '客户等级（冗余字段）',
    
    -- 录入信息（溯源 - 平台用户）
    reporter_id VARCHAR(36) REFERENCES users(id) COMMENT '录入人（销售/客服/产品）',
    source VARCHAR(20) DEFAULT 'manual' COMMENT 'manual, import, screenshot, api',
    
    -- 匿名反馈（可选）
    is_anonymous BOOLEAN DEFAULT FALSE,
    anonymous_author VARCHAR(100) COMMENT '匿名作者名称',
    anonymous_email VARCHAR(255) COMMENT '匿名作者邮箱',
    
    -- 反馈内容
    title VARCHAR(400) COMMENT '反馈标题（可选）',
    content TEXT NOT NULL COMMENT '反馈内容',
    ai_summary VARCHAR(200) COMMENT 'AI 生成的摘要',
    
    -- 图片识别相关（支持多张图片）
    images_metadata JSONB COMMENT '图片元数据数组',
    /*
    示例：
    {
        "images": [
            {
                "url": "https://oss.com/image1.jpg",
                "platform": "wechat",
                "user_name": "张三",
                "user_id": "wx_123456",
                "confidence": 0.95,
                "uploaded_at": "2025-12-31T10:00:00Z"
            },
            {
                "url": "https://oss.com/image2.jpg",
                "platform": "xiaohongshu",
                "user_name": "李四",
                "confidence": 0.88,
                "uploaded_at": "2025-12-31T10:01:00Z"
            }
        ]
    }
    */
    
    -- AI 相关
    embedding VECTOR(4096) COMMENT '内容向量（用于相似度检索）',
    sentiment VARCHAR(20) COMMENT 'positive, neutral, negative',
    sentiment_score FLOAT COMMENT '情感分数 (-1.0 to 1.0)',
    sentiment_reason TEXT COMMENT 'AI 情感分析理由',
    
    -- 聚类状态
    clustering_status VARCHAR(20) DEFAULT 'pending' COMMENT 'pending, clustered, manual_linked, noise',
    clustering_metadata JSONB,
    /*
    示例：
    {
        "cluster_label": 5,
        "clustered_at": "2025-12-31T10:00:00Z",
        "similarity_score": 0.92,
        "reason": "AI 自动聚类"
    }
    */
    
    -- 优先级
    priority VARCHAR(20) COMMENT 'low, medium, high, urgent',
    is_urgent BOOLEAN DEFAULT FALSE,
    
    -- 时间戳
    submitted_at TIMESTAMPTZ DEFAULT NOW(),
    created_time TIMESTAMPTZ DEFAULT NOW(),
    updated_time TIMESTAMPTZ,
    deleted_at TIMESTAMPTZ COMMENT '软删除',
    
    -- 约束
    CONSTRAINT chk_customer_or_anonymous CHECK (
        customer_id IS NOT NULL OR is_anonymous = TRUE
    ),
    
    -- 索引
    INDEX idx_feedbacks_tenant (tenant_id),
    INDEX idx_feedbacks_board (board_id),
    INDEX idx_feedbacks_topic (topic_id),
    INDEX idx_feedbacks_customer (customer_id),
    INDEX idx_feedbacks_reporter (reporter_id),
    INDEX idx_feedbacks_status (clustering_status),
    INDEX idx_feedbacks_submitted (submitted_at DESC),
    INDEX idx_feedbacks_embedding USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)
);

COMMENT ON TABLE feedbacks IS '用户反馈表（原始数据层，不可合并，保留完整溯源信息）';
COMMENT ON COLUMN feedbacks.customer_mrr IS '冗余字段，便于 Topic 聚合计算，避免多次 JOIN';
COMMENT ON COLUMN feedbacks.reporter_id IS '录入人（平台用户），用于溯源和绩效统计';
```

---

#### Topics（主题表）

**定义**：聚合层，承载权重计算，作为需求管理单元

```sql
CREATE TABLE topics (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id VARCHAR(36) NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    board_id VARCHAR(36) NOT NULL REFERENCES boards(id) ON DELETE CASCADE,
    
    -- Topic 基础信息
    title VARCHAR(200) NOT NULL COMMENT 'AI 生成或人工编辑',
    description TEXT COMMENT 'AI 生成或人工编辑',
    category VARCHAR(50) COMMENT 'bug, feature, improvement, performance, etc.',
    
    -- AI 聚类相关
    centroid VECTOR(4096) COMMENT 'Topic 中心向量（所有 Feedback embedding 的平均）',
    ai_generated BOOLEAN DEFAULT TRUE COMMENT '是否由 AI 生成',
    
    -- 权重计算（基于关联的 Feedback，通过触发器自动更新）
    feedback_count INTEGER DEFAULT 0 COMMENT '关联的 Feedback 数量',
    affected_customer_count INTEGER DEFAULT 0 COMMENT '受影响的客户数量（去重）',
    total_mrr DECIMAL(10,2) DEFAULT 0 COMMENT '所有关联客户的 MRR 总和',
    total_arr DECIMAL(10,2) DEFAULT 0 COMMENT '所有关联客户的 ARR 总和',
    avg_sentiment_score FLOAT COMMENT '平均情感分数',
    high_risk_customer_count INTEGER DEFAULT 0 COMMENT '高流失风险客户数量',
    
    -- 优先级评分
    impact_scope INTEGER COMMENT '影响范围评分 (1-10)，产品经理标注',
    dev_cost_estimate INTEGER COMMENT '开发成本评分 (1-10)，技术负责人标注',
    priority_score DECIMAL(10,2) GENERATED ALWAYS AS (
        COALESCE(total_mrr, 0) * COALESCE(impact_scope, 5) / NULLIF(COALESCE(dev_cost_estimate, 5), 0)
    ) STORED COMMENT '优先级 = 总MRR × 影响范围 / 成本',
    
    -- 需求管理
    internal_status VARCHAR(20) DEFAULT 'pending' COMMENT 'pending, evaluating, approved, rejected, planned, in_dev, released',
    product_owner_id VARCHAR(36) REFERENCES users(id) COMMENT '产品负责人（平台用户）',
    tech_lead_id VARCHAR(36) REFERENCES users(id) COMMENT '技术负责人（平台用户）',
    estimated_release_date DATE COMMENT '预计发布日期',
    actual_release_date DATE COMMENT '实际发布日期',
    

    
    -- 公开访问（可选）
    slug VARCHAR(200) UNIQUE COMMENT '公开访问 slug',
    is_public BOOLEAN DEFAULT FALSE COMMENT '是否公开',
    
    -- 时间戳
    created_time TIMESTAMPTZ DEFAULT NOW(),
    updated_time TIMESTAMPTZ,
    deleted_at TIMESTAMPTZ,
    
    -- 索引
    INDEX idx_topics_tenant (tenant_id),
    INDEX idx_topics_board (board_id),
    INDEX idx_topics_status (internal_status),
    INDEX idx_topics_priority (priority_score DESC NULLS LAST),
    INDEX idx_topics_owner (product_owner_id),
    INDEX idx_topics_centroid USING ivfflat (centroid vector_cosine_ops) WITH (lists = 50)
);

COMMENT ON TABLE topics IS '需求主题表（聚合层，承载权重计算，作为需求管理单元）';
COMMENT ON COLUMN topics.feedback_count IS '通过触发器自动更新';
COMMENT ON COLUMN topics.total_mrr IS '聚合所有关联 Feedback 的客户 MRR';
COMMENT ON COLUMN topics.priority_score IS '自动计算的优先级分数';
```

---

### 2.5 触发器：自动更新统计

```sql
-- 触发器函数：更新 Topic 统计信息
CREATE OR REPLACE FUNCTION update_topic_stats()
RETURNS TRIGGER AS $$
DECLARE
    v_topic_id VARCHAR(36);
BEGIN
    -- 确定要更新的 Topic ID
    IF TG_OP = 'DELETE' THEN
        v_topic_id := OLD.topic_id;
    ELSE
        v_topic_id := NEW.topic_id;
    END IF;
    
    -- 如果有 Topic ID，更新统计
    IF v_topic_id IS NOT NULL THEN
        UPDATE topics
        SET 
            feedback_count = (
                SELECT COUNT(*) 
                FROM feedbacks 
                WHERE topic_id = v_topic_id 
                  AND deleted_at IS NULL
            ),
            affected_customer_count = (
                SELECT COUNT(DISTINCT customer_id) 
                FROM feedbacks 
                WHERE topic_id = v_topic_id 
                  AND deleted_at IS NULL
                  AND customer_id IS NOT NULL
            ),
            total_mrr = (
                SELECT COALESCE(SUM(DISTINCT customer_mrr), 0)
                FROM feedbacks 
                WHERE topic_id = v_topic_id 
                  AND deleted_at IS NULL
                  AND customer_mrr IS NOT NULL
            ),
            avg_sentiment_score = (
                SELECT AVG(sentiment_score)
                FROM feedbacks 
                WHERE topic_id = v_topic_id 
                  AND deleted_at IS NULL
                  AND sentiment_score IS NOT NULL
            ),
            high_risk_customer_count = (
                SELECT COUNT(DISTINCT f.customer_id)
                FROM feedbacks f
                JOIN customers c ON f.customer_id = c.id
                WHERE f.topic_id = v_topic_id 
                  AND f.deleted_at IS NULL
                  AND c.churn_risk = 'high'
            ),
            updated_time = NOW()
        WHERE id = v_topic_id;
    END IF;
    
    -- 如果是 UPDATE 且 topic_id 改变了，也更新旧的 Topic
    IF TG_OP = 'UPDATE' AND OLD.topic_id IS NOT NULL AND OLD.topic_id != COALESCE(NEW.topic_id, '') THEN
        UPDATE topics
        SET 
            feedback_count = (
                SELECT COUNT(*) 
                FROM feedbacks 
                WHERE topic_id = OLD.topic_id 
                  AND deleted_at IS NULL
            ),
            affected_customer_count = (
                SELECT COUNT(DISTINCT customer_id) 
                FROM feedbacks 
                WHERE topic_id = OLD.topic_id 
                  AND deleted_at IS NULL
                  AND customer_id IS NOT NULL
            ),
            total_mrr = (
                SELECT COALESCE(SUM(DISTINCT customer_mrr), 0)
                FROM feedbacks 
                WHERE topic_id = OLD.topic_id 
                  AND deleted_at IS NULL
                  AND customer_mrr IS NOT NULL
            ),
            updated_time = NOW()
        WHERE id = OLD.topic_id;
    END IF;
    
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- 创建触发器
DROP TRIGGER IF EXISTS trigger_update_topic_stats ON feedbacks;
CREATE TRIGGER trigger_update_topic_stats
AFTER INSERT OR UPDATE OF topic_id, deleted_at OR DELETE ON feedbacks
FOR EACH ROW
EXECUTE FUNCTION update_topic_stats();

-- 触发器函数：更新 Board 统计信息
CREATE OR REPLACE FUNCTION update_board_stats()
RETURNS TRIGGER AS $$
DECLARE
    v_board_id VARCHAR(36);
BEGIN
    -- 确定要更新的 Board ID
    IF TG_OP = 'DELETE' THEN
        v_board_id := OLD.board_id;
    ELSE
        v_board_id := NEW.board_id;
    END IF;
    
    -- 更新 Board 统计
    UPDATE boards
    SET 
        feedback_count = (
            SELECT COUNT(*) 
            FROM feedbacks 
            WHERE board_id = v_board_id 
              AND deleted_at IS NULL
        ),
        topic_count = (
            SELECT COUNT(*) 
            FROM topics 
            WHERE board_id = v_board_id 
              AND deleted_at IS NULL
        ),
        updated_time = NOW()
    WHERE id = v_board_id;
    
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- 创建触发器
DROP TRIGGER IF EXISTS trigger_update_board_stats_from_feedbacks ON feedbacks;
CREATE TRIGGER trigger_update_board_stats_from_feedbacks
AFTER INSERT OR UPDATE OF board_id, deleted_at OR DELETE ON feedbacks
FOR EACH ROW
EXECUTE FUNCTION update_board_stats();

DROP TRIGGER IF EXISTS trigger_update_board_stats_from_topics ON topics;
CREATE TRIGGER trigger_update_board_stats_from_topics
AFTER INSERT OR UPDATE OF board_id, deleted_at OR DELETE ON topics
FOR EACH ROW
EXECUTE FUNCTION update_board_stats();
```

---

## 三、核心查询示例

### 3.1 获取平台用户在某租户的完整信息

```sql
SELECT 
    u.id,
    u.email,
    u.name,
    tu.user_type,
    tu.department_id,
    tu.feedback_count,
    array_agg(DISTINCT r.name) AS roles,
    array_agg(DISTINCT m.name) AS menus
FROM users u
JOIN tenant_users tu ON u.id = tu.user_id
LEFT JOIN tenant_user_roles tur ON tu.id = tur.tenant_user_id
LEFT JOIN sys_role r ON tur.role_id = r.id
LEFT JOIN sys_role_menu rm ON r.id = rm.role_id
LEFT JOIN sys_menu m ON rm.menu_id = m.id
WHERE u.id = :user_id 
  AND tu.tenant_id = :tenant_id
GROUP BY u.id, u.email, u.name, tu.user_type, tu.department_id, tu.feedback_count;
```

---

### 3.2 获取某 Board 的优先级最高的 Topic

```sql
SELECT 
    t.id,
    t.title,
    t.description,
    t.priority_score,
    t.feedback_count,
    t.affected_customer_count,
    t.total_mrr,
    t.high_risk_customer_count,
    t.internal_status,
    u1.name AS product_owner,
    u2.name AS tech_lead,
    -- 关联的客户列表
    (
        SELECT STRING_AGG(DISTINCT c.name, ', ' ORDER BY c.name)
        FROM feedbacks f
        JOIN customers c ON f.customer_id = c.id
        WHERE f.topic_id = t.id AND f.deleted_at IS NULL
    ) AS affected_customers
FROM topics t
LEFT JOIN users u1 ON t.product_owner_id = u1.id
LEFT JOIN users u2 ON t.tech_lead_id = u2.id
WHERE t.board_id = :board_id
  AND t.deleted_at IS NULL
ORDER BY t.priority_score DESC NULLS LAST
LIMIT 20;
```

---

### 3.3 全文检索某 Board 的 Topic

```sql
SELECT 
    t.id,
    t.title,
    t.description,
    1 - (t.centroid <=> :query_embedding) AS similarity,
    t.feedback_count,
    t.total_mrr,
    t.priority_score,
    t.internal_status
FROM topics t
WHERE t.board_id = :board_id
  AND t.deleted_at IS NULL
  AND 1 - (t.centroid <=> :query_embedding) > 0.7  -- 相似度阈值
ORDER BY similarity DESC
LIMIT 5;
```

---

### 3.4 获取某客户的所有反馈

```sql
SELECT 
    f.id,
    f.content,
    f.ai_summary,
    t.title AS topic_title,
    t.priority_score,
    t.internal_status,
    u.name AS reporter,
    f.source,
    f.sentiment,
    f.submitted_at
FROM feedbacks f
LEFT JOIN topics t ON f.topic_id = t.id
LEFT JOIN users u ON f.reporter_id = u.id
WHERE f.customer_id = :customer_id
  AND f.deleted_at IS NULL
ORDER BY f.submitted_at DESC;
```

---

### 3.5 高流失风险客户预警

```sql
SELECT 
    c.id,
    c.name,
    c.company_name,
    c.customer_tier,
    c.mrr,
    c.churn_risk,
    c.contract_end_date,
    COUNT(f.id) AS total_feedback_count,
    COUNT(f.id) FILTER (WHERE f.sentiment = 'negative') AS negative_feedback_count,
    AVG(f.sentiment_score) AS avg_sentiment_score,
    STRING_AGG(f.ai_summary, '; ' ORDER BY f.submitted_at DESC) AS recent_feedbacks
FROM customers c
LEFT JOIN feedbacks f ON c.id = f.customer_id AND f.deleted_at IS NULL
WHERE c.tenant_id = :tenant_id
  AND c.deleted_at IS NULL
  AND (
      c.churn_risk = 'high'
      OR (c.contract_end_date < NOW() + INTERVAL '30 days' AND c.contract_end_date > NOW())
  )
GROUP BY c.id
HAVING COUNT(f.id) FILTER (WHERE f.sentiment = 'negative') > 0
ORDER BY c.mrr DESC, negative_feedback_count DESC;
```

---

## 四、数据示例

### 4.1 平台用户示例

```sql
-- 创建平台用户
INSERT INTO users (id, email, name) 
VALUES 
    ('user_001', 'zhang@userecho.com', '张三'),
    ('user_002', 'li@userecho.com', '李四'),
    ('user_003', 'wang@userecho.com', '王五');

-- 张三在 Tenant A 是产品经理
INSERT INTO tenant_users (tenant_id, user_id, user_type)
VALUES ('tenant_a', 'user_001', 'product_manager');

-- 李四在 Tenant A 是销售
INSERT INTO tenant_users (tenant_id, user_id, user_type)
VALUES ('tenant_a', 'user_002', 'sales');

-- 王五在 Tenant A 是客服
INSERT INTO tenant_users (tenant_id, user_id, user_type)
VALUES ('tenant_a', 'user_003', 'customer_success');
```

---

### 4.2 客户示例

```sql
-- Tenant A 的客户
INSERT INTO customers (tenant_id, name, company_name, customer_tier, mrr, churn_risk)
VALUES 
    ('tenant_a', '某银行', '某银行股份有限公司', 'vip', 50000.00, 'low'),
    ('tenant_a', '某保险', '某保险集团', 'paid', 20000.00, 'medium'),
    ('tenant_a', '某证券', '某证券有限公司', 'free', NULL, 'high');
```

---

### 4.3 Board 和 Feedback 示例

```sql
-- 创建 Board
INSERT INTO boards (tenant_id, name, url_name, category)
VALUES ('tenant_a', '移动端反馈', 'mobile-feedback', 'mobile');

-- 销售李四录入客户反馈
INSERT INTO feedbacks (
    tenant_id, board_id, customer_id, customer_mrr, customer_tier,
    reporter_id, content, source
)
VALUES (
    'tenant_a', 'board_mobile', 'customer_001', 50000.00, 'vip',
    'user_002', '某银行反馈移动端启动太慢', 'manual'
);
```

---

## 五、总结

### 5.1 核心设计亮点

✅ **清晰的角色定义**
- **平台用户（Users）**：企业内部员工，登录平台，录入反馈
- **客户（Customers）**：Tenant 的终端用户，不登录平台，由 Tenant 管理

✅ **多租户架构**
- 全局用户表（`users`）+ 租户关联表（`tenant_users`）
- 一个用户可以在多个租户中扮演不同角色

✅ **Board 多维度组织**
- 支持按产品线、平台、功能模块等维度组织
- Feedback 和 Topic 都关联 Board

✅ **Feedback/Topic 双层抽象**
- Feedback：原始数据层，不可合并，保留完整溯源
- Topic：聚合层，承载权重计算，作为需求管理单元

✅ **权重自动计算**
- 通过触发器自动更新 Topic 和 Board 统计
- 优先级基于客户价值聚合

### 5.2 表结构总览

| 分类 | 表名 | 说明 |
|------|------|------|
| **租户与平台用户** | `tenants` | 租户表 |
| | `users` | 平台用户（全局，无 tenant_id） |
| | `tenant_users` | 租户-用户关联 |
| | `tenant_user_roles` | 租户用户角色 |
| **客户管理** | `customers` | 客户表（Tenant 的终端用户） |
| **Board 组织** | `boards` | 看板表 |
| **核心业务** | `feedbacks` | 反馈表（原始数据） |
| | `topics` | 主题表（聚合层） |

---

**文档维护者**: 技术团队  
**最后更新**: 2025-12-31
