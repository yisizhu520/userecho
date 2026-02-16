# Feedalyze 数据库重构设计文档 v2

> **重构目标**: 采用 Board-Feedback-Vote 架构,对标 Canny,优化用户模型,简化数据结构。

---

## 一、核心设计理念

### 1.1 设计原则
1. **Feedback 是核心**: 所有用户反馈(内部/外部)都是 Feedback
2. **投票驱动优先级**: 通过 Vote 表记录用户投票
3. **AI 辅助去重**: AI 检测重复,提醒 Admin 合并
4. **Board 多维度组织**: 支持多看板,灵活的访问控制
5. **统一用户模型**: 合并 sys_user, end_user, customer 为单一 User 表

### 1.2 用户模型设计思路

#### Canny 的用户模型
根据调研,Canny 采用**单一 User 表 + 角色区分**的设计:
- **User**: 统一的用户实体,包含所有用户(Admin, 终端用户, 客户)
- **Role/Permission**: 通过角色和权限区分用户类型
- **Company**: 关联用户所属公司(B2B 场景)

#### 我们的现状问题
- `sys_user`: 内部管理员(Admin)
- `end_user`: C 端用户(公开门户注册)
- `customer`: B 端客户(CRM 导入)

**问题:**
1. 三张表数据冗余,难以维护
2. 一个人可能既是 Admin 又是 Customer
3. 关联查询复杂(`author_type` + `author_id`)

#### 优化方案: **统一 User 表 + 角色标签**
```sql
-- 单一 User 表
CREATE TABLE users (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) REFERENCES tenants(id),
    
    -- 基础信息
    email VARCHAR(255) UNIQUE,
    name VARCHAR(100),
    avatar_url VARCHAR(500),
    
    -- 角色标签 (一个用户可以有多个角色)
    roles TEXT[],  -- ['admin', 'customer', 'end_user']
    
    -- 客户相关 (仅 customer 角色需要)
    customer_type VARCHAR(20),  -- normal, paid, vip
    business_value INTEGER,     -- 商业价值权重
    mrr DECIMAL(10,2),          -- 月收入
    
    -- 第三方登录
    wechat_openid VARCHAR(100),
    
    -- 统计
    vote_count INTEGER DEFAULT 0,
    feedback_count INTEGER DEFAULT 0,
    
    created_time TIMESTAMPTZ DEFAULT NOW()
);
```

**优势:**
- ✅ 单表查询,性能更好
- ✅ 一个用户可以有多个角色
- ✅ 简化 Feedback.author_id 关联

---

## 二、核心表设计

### 2.1 Board (反馈看板)

```sql
CREATE TABLE boards (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    
    -- 基础信息
    name VARCHAR(100) NOT NULL,                    -- 看板名称,如 "功能需求"
    url_name VARCHAR(100) NOT NULL,                -- URL slug,如 "feature-requests"
    description TEXT,                              -- 看板描述
    
    -- 访问控制 (优化点 1: 合并 is_private 和 is_public)
    access_mode VARCHAR(20) DEFAULT 'public',      -- public, private, restricted
    allowed_user_ids TEXT[],                       -- restricted 模式下允许访问的用户 ID 列表
    
    -- 统计
    feedback_count INTEGER DEFAULT 0,
    
    -- 排序与显示
    sort_order INTEGER DEFAULT 0,
    
    -- 时间戳
    created_time TIMESTAMPTZ DEFAULT NOW(),
    updated_time TIMESTAMPTZ,
    
    UNIQUE(tenant_id, url_name)
);

CREATE INDEX idx_boards_tenant ON boards(tenant_id);
CREATE INDEX idx_boards_access ON boards(access_mode);
```

**字段说明:**

#### access_mode (访问模式)
- `public`: 完全公开,所有人可访问
- `private`: 私有,仅团队成员可访问
- `restricted`: 受限,仅 `allowed_user_ids` 中的用户可访问

**扩展性:**
- 未来可增加 `team_only`, `paid_users_only` 等模式
- `allowed_user_ids` 支持动态权限控制

**示例:**
```json
{
  "id": "board_001",
  "name": "VIP 客户反馈",
  "url_name": "vip-feedback",
  "access_mode": "restricted",
  "allowed_user_ids": ["user_123", "user_456"]  // 仅这两个用户可访问
}
```

---

### 2.2 Feedback (用户反馈)

```sql
CREATE TABLE feedbacks (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    board_id VARCHAR(36) NOT NULL REFERENCES boards(id) ON DELETE CASCADE,
    
    -- 作者信息 (优化点 3: 简化为单一 user_id)
    author_id VARCHAR(36) REFERENCES users(id),    -- 统一关联 users 表
    author_name VARCHAR(100),                      -- 匿名用户名称
    author_email VARCHAR(255),                     -- 匿名用户邮箱
    is_anonymous BOOLEAN DEFAULT FALSE,            -- 是否匿名提交
    
    -- 反馈内容
    title VARCHAR(400) NOT NULL,
    details TEXT,
    
    -- 分类与状态
    category VARCHAR(50),
    status VARCHAR(20) DEFAULT 'open',
    
    -- 来源信息
    source VARCHAR(20) DEFAULT 'web',
    
    -- 截图相关 (优化点 2: 支持多张截图)
    screenshot_urls TEXT[],                        -- 截图 URL 数组
    
    -- 截图解析元数据
    screenshot_metadata JSONB,                     -- 存储解析结果
    /*
    示例:
    {
      "screenshots": [
        {
          "url": "https://oss.com/img1.jpg",
          "platform": "wechat",
          "user_name": "张三",
          "confidence": 0.95
        },
        {
          "url": "https://oss.com/img2.jpg",
          "platform": "xiaohongshu",
          "user_name": "李四",
          "confidence": 0.88
        }
      ]
    }
    */
    
    -- 投票与互动统计
    vote_count INTEGER DEFAULT 0,
    comment_count INTEGER DEFAULT 0,
    
    -- AI 相关
    embedding VECTOR(4096),
    ai_summary VARCHAR(200),
    ai_confidence FLOAT,
    duplicate_of_id VARCHAR(36) REFERENCES feedbacks(id),
    
    -- 情感分析
    sentiment VARCHAR(20),
    sentiment_score FLOAT,
    
    -- 公开访问
    slug VARCHAR(200) UNIQUE,
    is_public BOOLEAN DEFAULT TRUE,
    
    -- 优先级
    priority VARCHAR(20),
    
    -- 关联客户信息 (从 users 表获取)
    -- customer_mrr 等字段通过 JOIN users 获取,不冗余存储
    
    -- 时间戳
    submitted_at TIMESTAMPTZ DEFAULT NOW(),
    created_time TIMESTAMPTZ DEFAULT NOW(),
    updated_time TIMESTAMPTZ,
    deleted_at TIMESTAMPTZ,
    
    CONSTRAINT chk_author CHECK (
        (is_anonymous = TRUE AND author_name IS NOT NULL) OR
        (is_anonymous = FALSE AND author_id IS NOT NULL)
    )
);

-- 索引
CREATE INDEX idx_feedbacks_tenant ON feedbacks(tenant_id);
CREATE INDEX idx_feedbacks_board ON feedbacks(board_id);
CREATE INDEX idx_feedbacks_status ON feedbacks(status);
CREATE INDEX idx_feedbacks_author ON feedbacks(author_id);
CREATE INDEX idx_feedbacks_public ON feedbacks(is_public, deleted_at) WHERE is_public = TRUE AND deleted_at IS NULL;
CREATE INDEX idx_feedbacks_slug ON feedbacks(slug) WHERE slug IS NOT NULL;
CREATE INDEX idx_feedbacks_duplicate ON feedbacks(duplicate_of_id) WHERE duplicate_of_id IS NOT NULL;

-- 向量索引
CREATE INDEX idx_feedbacks_embedding ON feedbacks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- GIN 索引 (用于 JSONB 查询)
CREATE INDEX idx_feedbacks_screenshot_metadata ON feedbacks USING gin (screenshot_metadata);
```

**字段说明:**

#### 作者信息简化
- 废弃 `author_type` 字段
- 统一使用 `author_id` 关联 `users` 表
- `is_anonymous` 标识是否匿名提交

#### 多截图支持
- `screenshot_urls`: 字符串数组,存储多个 OSS URL
- `screenshot_metadata`: JSONB 格式,存储每张截图的解析元数据

**示例数据:**
```json
{
  "id": "feedback_001",
  "author_id": "user_123",
  "is_anonymous": false,
  "title": "支持暗黑模式",
  "screenshot_urls": [
    "https://oss.com/screenshot1.jpg",
    "https://oss.com/screenshot2.jpg"
  ],
  "screenshot_metadata": {
    "screenshots": [
      {
        "url": "https://oss.com/screenshot1.jpg",
        "platform": "wechat",
        "user_name": "张三",
        "confidence": 0.95
      }
    ]
  }
}
```

---

### 2.3 Users (统一用户表)

```sql
CREATE TABLE users (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    
    -- 基础信息
    email VARCHAR(255),
    name VARCHAR(100),
    nickname VARCHAR(100),                         -- 显示名称
    avatar_url VARCHAR(500),
    
    -- 角色标签 (一个用户可以有多个角色)
    roles TEXT[] DEFAULT ARRAY['end_user'],        -- ['admin', 'customer', 'end_user']
    
    -- 客户相关字段 (仅 'customer' 角色需要)
    customer_type VARCHAR(20),                     -- normal, paid, vip, strategic
    business_value INTEGER DEFAULT 1,              -- 商业价值权重 (1-10)
    mrr DECIMAL(10,2),                             -- 月收入 (Monthly Recurring Revenue)
    company_name VARCHAR(200),                     -- 公司名称
    
    -- 第三方登录
    wechat_openid VARCHAR(100) UNIQUE,
    wechat_unionid VARCHAR(100),
    
    -- 统计
    vote_count INTEGER DEFAULT 0,
    comment_count INTEGER DEFAULT 0,
    feedback_count INTEGER DEFAULT 0,
    
    -- 状态
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    
    -- 时间戳
    created_time TIMESTAMPTZ DEFAULT NOW(),
    last_login_time TIMESTAMPTZ,
    updated_time TIMESTAMPTZ,
    
    UNIQUE(tenant_id, email) WHERE email IS NOT NULL
);

-- 索引
CREATE INDEX idx_users_tenant ON users(tenant_id);
CREATE INDEX idx_users_email ON users(email) WHERE email IS NOT NULL;
CREATE INDEX idx_users_roles ON users USING gin (roles);  -- GIN 索引支持数组查询
CREATE INDEX idx_users_wechat ON users(wechat_openid) WHERE wechat_openid IS NOT NULL;
```

**字段说明:**

#### roles (角色数组)
- 使用 PostgreSQL 数组类型,一个用户可以有多个角色
- 常见角色:
  - `admin`: 管理员,可管理所有数据
  - `customer`: B 端客户,有 MRR 等商业字段
  - `end_user`: C 端用户,公开门户注册

**查询示例:**
```sql
-- 查询所有管理员
SELECT * FROM users WHERE 'admin' = ANY(roles);

-- 查询既是客户又是管理员的用户
SELECT * FROM users WHERE roles @> ARRAY['admin', 'customer'];
```

#### 客户字段
- `customer_type`, `business_value`, `mrr`: 仅当 `'customer' IN roles` 时有值
- 避免创建单独的 `customers` 表

**示例数据:**
```json
{
  "id": "user_001",
  "email": "zhang@company.com",
  "name": "张三",
  "roles": ["admin", "customer"],  // 既是管理员又是客户
  "customer_type": "vip",
  "mrr": 5000.00,
  "company_name": "某科技公司"
}
```

---

### 2.4 Vote (投票记录)

```sql
CREATE TABLE votes (
    id VARCHAR(36) PRIMARY KEY,
    feedback_id VARCHAR(36) NOT NULL REFERENCES feedbacks(id) ON DELETE CASCADE,
    
    -- 投票者信息 (优化点 3: 简化为单一 user_id)
    voter_id VARCHAR(36) NOT NULL REFERENCES users(id),
    voter_email VARCHAR(255),                      -- 用于通知
    
    -- 投票权重
    weight INTEGER DEFAULT 1,
    
    -- 优先级标记
    priority VARCHAR(20),                          -- nice_to_have, important, must_have
    
    -- 时间戳
    created_time TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(feedback_id, voter_id)                  -- 一人一票
);

CREATE INDEX idx_votes_feedback ON votes(feedback_id);
CREATE INDEX idx_votes_voter ON votes(voter_id);
CREATE INDEX idx_votes_created ON votes(created_time DESC);
```

**简化说明:**
- 废弃 `voter_type` 字段
- 统一使用 `voter_id` 关联 `users` 表

---

### 2.5 Comment (评论)

```sql
CREATE TABLE comments (
    id VARCHAR(36) PRIMARY KEY,
    feedback_id VARCHAR(36) NOT NULL REFERENCES feedbacks(id) ON DELETE CASCADE,
    
    -- 评论者信息 (优化点 3: 简化)
    author_id VARCHAR(36) NOT NULL REFERENCES users(id),
    
    -- 评论内容
    content TEXT NOT NULL,
    
    -- 评论类型
    is_internal BOOLEAN DEFAULT FALSE,
    
    -- 回复关系
    parent_id VARCHAR(36) REFERENCES comments(id) ON DELETE CASCADE,
    
    -- 时间戳
    created_time TIMESTAMPTZ DEFAULT NOW(),
    updated_time TIMESTAMPTZ,
    deleted_at TIMESTAMPTZ,
    
    CONSTRAINT chk_no_self_reply CHECK (id != parent_id)
);

CREATE INDEX idx_comments_feedback ON comments(feedback_id, created_time);
CREATE INDEX idx_comments_author ON comments(author_id);
CREATE INDEX idx_comments_parent ON comments(parent_id) WHERE parent_id IS NOT NULL;
```

---

### 2.6 Category (分类,可选)

```sql
CREATE TABLE categories (
    id VARCHAR(36) PRIMARY KEY,
    board_id VARCHAR(36) NOT NULL REFERENCES boards(id) ON DELETE CASCADE,
    
    name VARCHAR(100) NOT NULL,
    slug VARCHAR(100) NOT NULL,
    description TEXT,
    
    -- 层级关系
    parent_id VARCHAR(36) REFERENCES categories(id) ON DELETE CASCADE,
    
    -- 统计
    feedback_count INTEGER DEFAULT 0,
    
    -- 排序
    sort_order INTEGER DEFAULT 0,
    
    created_time TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(board_id, slug)
);

CREATE INDEX idx_categories_board ON categories(board_id);
CREATE INDEX idx_categories_parent ON categories(parent_id) WHERE parent_id IS NOT NULL;
```

---

## 三、辅助表设计

### 3.1 FeedbackMerge (合并记录)

```sql
CREATE TABLE feedback_merges (
    id VARCHAR(36) PRIMARY KEY,
    
    source_feedback_id VARCHAR(36) NOT NULL REFERENCES feedbacks(id),
    target_feedback_id VARCHAR(36) NOT NULL REFERENCES feedbacks(id),
    
    merged_by VARCHAR(36) NOT NULL REFERENCES users(id),
    merge_reason TEXT,
    ai_similarity FLOAT,
    
    merged_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT chk_no_self_merge CHECK (source_feedback_id != target_feedback_id)
);

CREATE INDEX idx_merges_source ON feedback_merges(source_feedback_id);
CREATE INDEX idx_merges_target ON feedback_merges(target_feedback_id);
```

---

### 3.2 StatusHistory (状态变更历史)

```sql
CREATE TABLE status_history (
    id VARCHAR(36) PRIMARY KEY,
    feedback_id VARCHAR(36) NOT NULL REFERENCES feedbacks(id) ON DELETE CASCADE,
    
    from_status VARCHAR(20),
    to_status VARCHAR(20) NOT NULL,
    
    changed_by VARCHAR(36) REFERENCES users(id),
    change_reason TEXT,
    
    changed_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_status_history_feedback ON status_history(feedback_id, changed_at DESC);
```

---

## 四、数据迁移方案

### 4.1 合并用户表

```sql
-- 1. 创建统一 users 表 (已在上面定义)

-- 2. 迁移 sys_user (Admin)
INSERT INTO users (id, tenant_id, email, name, roles, created_time)
SELECT 
    id::VARCHAR, 
    'default_tenant',  -- 需要关联到具体 tenant
    email, 
    username,
    ARRAY['admin'],
    created_time
FROM sys_user;

-- 3. 迁移 customers
INSERT INTO users (
    id, tenant_id, email, name, roles, 
    customer_type, business_value, created_time
)
SELECT 
    id, tenant_id, NULL, name,
    ARRAY['customer'],
    customer_type, business_value, created_time
FROM customers;

-- 4. 迁移 end_users (如果已有)
INSERT INTO users (
    id, tenant_id, email, nickname, roles,
    wechat_openid, vote_count, feedback_count, created_time
)
SELECT 
    id, tenant_id, email, nickname,
    ARRAY['end_user'],
    wechat_openid, vote_count, feedback_count, created_time
FROM end_users;

-- 5. 处理重复用户 (同一个 email 在多个表中)
-- 需要手动合并,将 roles 数组合并
UPDATE users u1
SET roles = ARRAY(
    SELECT DISTINCT unnest(u1.roles || u2.roles)
)
FROM users u2
WHERE u1.email = u2.email AND u1.id != u2.id;

-- 删除重复记录,保留第一条
DELETE FROM users u1
WHERE EXISTS (
    SELECT 1 FROM users u2
    WHERE u1.email = u2.email 
      AND u1.created_time > u2.created_time
);
```

### 4.2 迁移 Feedback 表

```sql
-- 1. 创建默认 Board
INSERT INTO boards (id, tenant_id, name, url_name, access_mode)
VALUES ('default_board', 'tenant_001', '所有反馈', 'all-feedback', 'public');

-- 2. 迁移 Feedback
INSERT INTO feedbacks (
    id, tenant_id, board_id,
    author_id, author_name, is_anonymous,
    title, details,
    screenshot_urls, screenshot_metadata,
    embedding, ai_summary, ai_confidence,
    sentiment, sentiment_score,
    submitted_at, created_time, updated_time, deleted_at
)
SELECT 
    id, tenant_id, 'default_board',
    CASE 
        WHEN customer_id IS NOT NULL THEN customer_id
        WHEN submitter_id IS NOT NULL THEN submitter_id::VARCHAR
        ELSE NULL
    END,
    anonymous_author,
    (anonymous_author IS NOT NULL),
    COALESCE(ai_summary, LEFT(content, 100)),
    content,
    CASE 
        WHEN screenshot_url IS NOT NULL THEN ARRAY[screenshot_url]
        ELSE ARRAY[]::TEXT[]
    END,
    CASE 
        WHEN screenshot_url IS NOT NULL THEN 
            jsonb_build_object(
                'screenshots', jsonb_build_array(
                    jsonb_build_object(
                        'url', screenshot_url,
                        'platform', source_platform,
                        'user_name', source_user_name,
                        'confidence', ai_confidence
                    )
                )
            )
        ELSE NULL
    END,
    embedding, ai_summary, ai_confidence,
    sentiment, sentiment_score,
    submitted_at, created_time, updated_time, deleted_at
FROM feedbacks_old;
```

---

## 五、查询示例

### 5.1 获取用户的所有角色
```sql
SELECT id, email, name, roles
FROM users
WHERE 'admin' = ANY(roles);  -- 所有管理员
```

### 5.2 获取 VIP 客户的反馈
```sql
SELECT f.*, u.mrr, u.company_name
FROM feedbacks f
JOIN users u ON f.author_id = u.id
WHERE 'customer' = ANY(u.roles)
  AND u.customer_type = 'vip'
ORDER BY u.mrr DESC;
```

### 5.3 检查 Board 访问权限
```sql
-- 检查用户是否可以访问某个 Board
SELECT 
    CASE 
        WHEN b.access_mode = 'public' THEN TRUE
        WHEN b.access_mode = 'private' AND 'admin' = ANY(u.roles) THEN TRUE
        WHEN b.access_mode = 'restricted' AND u.id = ANY(b.allowed_user_ids) THEN TRUE
        ELSE FALSE
    END AS can_access
FROM boards b, users u
WHERE b.id = $1 AND u.id = $2;
```

### 5.4 获取多截图的 Feedback
```sql
SELECT 
    id, title,
    array_length(screenshot_urls, 1) AS screenshot_count,
    screenshot_metadata->'screenshots' AS parsed_screenshots
FROM feedbacks
WHERE array_length(screenshot_urls, 1) > 1;
```

---

## 六、优化总结

### 6.1 三大优化点

| 优化点 | 优化前 | 优化后 | 优势 |
|--------|--------|--------|------|
| **1. Board 访问控制** | `is_private` + `is_public` 两个字段 | `access_mode` 枚举 + `allowed_user_ids` | 更灵活,可扩展 |
| **2. 多截图支持** | `screenshot_url` 单个字符串 | `screenshot_urls` 数组 + `screenshot_metadata` JSONB | 支持多张截图及元数据 |
| **3. 统一用户模型** | `sys_user`, `end_user`, `customer` 三张表 | `users` 单表 + `roles` 数组 | 简化查询,减少冗余 |

### 6.2 与 Canny 对比

| 特性 | Canny | Feedalyze (新设计) |
|------|-------|-------------------|
| 用户模型 | 单一 User 表 | ✅ 单一 Users 表 + roles |
| Board 访问控制 | Public/Private | ✅ Public/Private/Restricted |
| 多截图支持 | ❌ | ✅ 数组 + JSONB |
| AI 去重 | ❌ | ✅ 向量相似度 |

---

## 七、评审记录

### 7.1 评审会议 (2025-12-30)

#### 评审结论 1: 多租户用户模型需要重新设计

**问题:**
- ❌ 原设计中 `users` 表包含 `tenant_id` 字段,限制了用户只能属于一个租户
- ❌ 无法支持「一个用户在多个租户中扮演不同角色」的场景

**决策:**
采用**全局用户 + 租户关联表**的设计:

```sql
-- 全局用户表 (无 tenant_id)
CREATE TABLE users (
    id VARCHAR(36) PRIMARY KEY,
    email VARCHAR(255) UNIQUE,
    name VARCHAR(100),
    -- 不再有 tenant_id 字段
    -- 不再有 roles 数组字段
);

-- 租户-用户关联表
CREATE TABLE tenant_users (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL REFERENCES tenants(id),
    user_id VARCHAR(36) NOT NULL REFERENCES users(id),
    user_type VARCHAR(20) NOT NULL,  -- 'admin', 'customer', 'end_user'
    
    -- 客户相关字段
    customer_type VARCHAR(20),
    customer_mrr DECIMAL(10,2),
    
    -- 统计字段
    vote_count INTEGER DEFAULT 0,
    feedback_count INTEGER DEFAULT 0,
    
    UNIQUE(tenant_id, user_id)
);
```

**优势:**
- ✅ 支持一个用户在多个租户中有不同身份
- ✅ 符合真正的多租户架构
- ✅ 与现有 RBAC 系统兼容 (通过 `tenant_user_roles` 表)

**详细设计文档:** 见 `multi-tenant-user-model.md`

---

#### 评审结论 2: 截图存储优化为纯 JSONB

**问题:**
- 原设计同时使用 `screenshot_urls` (数组) 和 `screenshot_metadata` (JSONB)
- 存在数据冗余,URL 在两个字段中重复存储

**决策:**
合并为单一 `screenshots` JSONB 字段:

```sql
CREATE TABLE feedbacks (
    -- ...
    screenshots JSONB,
    /*
    示例:
    {
      "items": [
        {
          "url": "https://oss.com/img1.jpg",
          "platform": "wechat",
          "user_name": "张三",
          "confidence": 0.95,
          "parsed_at": "2025-12-30T10:00:00Z"
        },
        {
          "url": "https://oss.com/img2.jpg",
          "platform": "xiaohongshu",
          "user_name": "李四",
          "confidence": 0.88
        }
      ]
    }
    */
);

-- GIN 索引支持 JSONB 查询
CREATE INDEX idx_feedbacks_screenshots ON feedbacks USING gin (screenshots);
```

**查询示例:**
```sql
-- 查询包含微信截图的反馈
SELECT id, title, screenshots
FROM feedbacks
WHERE screenshots @> '{"items": [{"platform": "wechat"}]}';

-- 提取所有截图 URL
SELECT 
    id,
    jsonb_path_query_array(screenshots, '$.items[*].url') AS screenshot_urls
FROM feedbacks;
```

**优势:**
- ✅ 消除数据冗余
- ✅ 更灵活的元数据扩展
- ✅ 利用 PostgreSQL JSONB 的强大查询能力

---

#### 评审结论 3: 确认与现有 RBAC 系统的兼容性

**现有系统:**
- `sys_user`: 内部管理员
- `sys_role`: 角色表
- `sys_user_role`: 用户-角色关联
- `sys_role_menu`: 角色-菜单权限
- `sys_role_scope`: 角色-数据权限

**兼容性分析:**

| 现有表 | 新设计对应关系 | 迁移方案 |
|--------|----------------|----------|
| `sys_user` | → `users` (全局) + `tenant_users` (租户关联) | 保留 `sys_user`,通过视图兼容 |
| `sys_role` | 保持不变 | 无需修改 |
| `sys_user_role` | → `tenant_user_roles` | 关联 `tenant_users.id` |
| `sys_role_menu` | 保持不变 | 无需修改 |
| `sys_role_scope` | 保持不变 | 无需修改 |

**迁移策略:**
```sql
-- 创建兼容视图,保持现有代码不变
CREATE VIEW sys_user AS
SELECT 
    u.id,
    u.email,
    u.name AS username,
    tu.tenant_id,
    u.created_time
FROM users u
JOIN tenant_users tu ON u.id = tu.user_id
WHERE tu.user_type = 'admin';

-- 权限查询保持不变
SELECT r.* 
FROM sys_role r
JOIN tenant_user_roles tur ON r.id = tur.role_id
JOIN tenant_users tu ON tur.tenant_user_id = tu.id
WHERE tu.user_id = $user_id AND tu.tenant_id = $tenant_id;
```

**结论:**
- ✅ 现有 RBAC 逻辑无需修改
- ✅ 菜单权限系统保持不变
- ✅ 通过视图实现向后兼容

---

### 7.2 核心表设计更新

基于评审结论,核心表设计调整如下:

#### Users (全局用户表)
```sql
CREATE TABLE users (
    id VARCHAR(36) PRIMARY KEY,
    
    -- 全局唯一标识
    email VARCHAR(255) UNIQUE,
    phone VARCHAR(20),
    
    -- 基础信息
    name VARCHAR(100),
    nickname VARCHAR(100),
    avatar_url VARCHAR(500),
    
    -- 第三方登录
    wechat_openid VARCHAR(100) UNIQUE,
    wechat_unionid VARCHAR(100),
    
    -- 账号状态
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    
    -- 时间戳
    created_time TIMESTAMPTZ DEFAULT NOW(),
    last_login_time TIMESTAMPTZ,
    updated_time TIMESTAMPTZ
    
    -- ❌ 移除 tenant_id 字段
    -- ❌ 移除 roles 数组字段
);
```

#### TenantUsers (租户-用户关联表)
```sql
CREATE TABLE tenant_users (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- 用户类型
    user_type VARCHAR(20) NOT NULL,  -- 'admin', 'member', 'customer', 'end_user'
    
    -- 客户相关字段 (仅 user_type='customer' 时有值)
    customer_type VARCHAR(20),
    customer_mrr DECIMAL(10,2),
    company_name VARCHAR(200),
    
    -- 统计 (租户内)
    vote_count INTEGER DEFAULT 0,
    feedback_count INTEGER DEFAULT 0,
    comment_count INTEGER DEFAULT 0,
    
    -- 状态
    status VARCHAR(20) DEFAULT 'active',
    
    -- 时间戳
    joined_at TIMESTAMPTZ DEFAULT NOW(),
    last_active_at TIMESTAMPTZ,
    
    UNIQUE(tenant_id, user_id)
);

CREATE INDEX idx_tenant_users_tenant ON tenant_users(tenant_id);
CREATE INDEX idx_tenant_users_user ON tenant_users(user_id);
CREATE INDEX idx_tenant_users_type ON tenant_users(user_type);
```

#### Feedbacks (更新截图字段)
```sql
CREATE TABLE feedbacks (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL REFERENCES tenants(id),
    board_id VARCHAR(36) NOT NULL REFERENCES boards(id),
    
    -- 作者信息
    author_id VARCHAR(36) REFERENCES users(id),  -- 全局用户 ID
    is_anonymous BOOLEAN DEFAULT FALSE,
    author_name VARCHAR(100),
    author_email VARCHAR(255),
    
    -- 反馈内容
    title VARCHAR(400) NOT NULL,
    details TEXT,
    
    -- 截图 (纯 JSONB)
    screenshots JSONB,
    
    -- 分类与状态
    category VARCHAR(50),
    status VARCHAR(20) DEFAULT 'open',
    
    -- AI 相关
    embedding VECTOR(4096),
    ai_summary VARCHAR(200),
    duplicate_of_id VARCHAR(36) REFERENCES feedbacks(id),
    
    -- 统计
    vote_count INTEGER DEFAULT 0,
    comment_count INTEGER DEFAULT 0,
    
    -- 时间戳
    created_time TIMESTAMPTZ DEFAULT NOW(),
    updated_time TIMESTAMPTZ,
    deleted_at TIMESTAMPTZ
);

CREATE INDEX idx_feedbacks_screenshots ON feedbacks USING gin (screenshots);
```

---

### 7.3 待确认问题

- [ ] 确认默认租户 ID (`default_tenant`) 的生成策略
- [ ] 确认 `sys_user` 视图是否需要包含更多字段
- [ ] 确认数据迁移的回滚方案
- [ ] 确认前端 API 的兼容性改造范围

---

## 八、下一步

1. ✅ Review 本设计文档 (已完成)
2. ✅ 确认用户表合并方案 (采用全局用户 + 租户关联)
3. ⏳ 生成 Alembic 迁移脚本
4. ⏳ 更新 Pydantic Schema
5. ⏳ 更新 API 接口文档

---

**文档维护者**: 技术团队  
**最后更新**: 2025-12-31
