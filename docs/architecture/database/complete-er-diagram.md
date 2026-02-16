# Feedalyze 完整 ER 图设计

> **版本**: v2.0  
> **更新日期**: 2025-12-31  
> **设计理念**: MVP 最佳实践,无历史包袱,架构清晰简洁

---

## 一、完整 ER 图

```mermaid
erDiagram
    %% ========================================
    %% 租户与基础架构
    %% ========================================
    TENANTS ||--o{ TENANT_USERS : "has members"
    TENANTS ||--o{ BOARDS : "owns"
    TENANTS ||--o{ FEEDBACKS : "manages"
    TENANTS ||--o{ TOPICS : "tracks"
    TENANTS ||--o{ INSIGHTS : "generates"
    TENANTS ||--o{ USERECHO_TENANT_CONFIG : "has configs"
    
    %% ========================================
    %% 用户与权限系统 (多租户架构)
    %% ========================================
    USERS ||--o{ TENANT_USERS : "joins tenants"
    TENANT_USERS ||--o{ TENANT_USER_ROLES : "has roles"
    SYS_ROLE ||--o{ TENANT_USER_ROLES : "assigned to"
    SYS_ROLE ||--o{ SYS_ROLE_MENU : "grants menu access"
    SYS_ROLE ||--o{ SYS_ROLE_SCOPE : "grants data scope"
    SYS_MENU ||--o{ SYS_ROLE_MENU : "associated with"
    SYS_DEPT ||--o{ TENANT_USERS : "organizes"
    
    %% ========================================
    %% 核心业务逻辑 (Board-Feedback-Vote)
    %% ========================================
    BOARDS ||--o{ FEEDBACKS : "contains"
    BOARDS ||--o{ CATEGORIES : "has categories"
    USERS ||--o{ FEEDBACKS : "submits"
    USERS ||--o{ VOTES : "casts"
    USERS ||--o{ COMMENTS : "writes"
    FEEDBACKS ||--o{ VOTES : "receives"
    FEEDBACKS ||--o{ COMMENTS : "has discussions"
    FEEDBACKS ||--o{ FEEDBACK_MERGES : "merged from"
    FEEDBACKS ||--o{ FEEDBACK_MERGES : "merged to"
    FEEDBACKS ||--o{ STATUS_HISTORY : "status tracked"
    
    %% ========================================
    %% AI 聚类与主题管理
    %% ========================================
    TOPICS ||--o{ FEEDBACKS : "aggregates"
    TOPICS ||--|| PRIORITY_SCORES : "evaluated by"
    TOPICS ||--o{ STATUS_HISTORIES : "lifecycle tracked"
    FEEDBACKS ||--o{ MANUAL_ADJUSTMENTS : "adjusted in"
    
    %% ========================================
    %% 公开门户功能
    %% ========================================
    TENANTS ||--o{ CHANGELOGS : "publishes"
    CHANGELOGS ||--o{ CHANGELOG_TOPICS : "references"
    TOPICS ||--o{ CHANGELOG_TOPICS : "featured in"
    
    %% ========================================
    %% 日志与审计
    %% ========================================
    USERS ||--o{ LOGIN_LOG : "generates"
    USERS ||--o{ OPERA_LOG : "performs actions"
    
    %% ========================================
    %% 表结构定义
    %% ========================================
    
    TENANTS {
        varchar36 id PK "租户 UUID"
        varchar100 name "租户名称"
        varchar20 status "状态: active|suspended|deleted"
        timestamptz created_time
        timestamptz updated_time
    }
    
    USERS {
        varchar36 id PK "全局用户 UUID"
        varchar255 email UK "全局唯一邮箱"
        varchar20 phone
        varchar100 name "真实姓名"
        varchar100 nickname "显示昵称"
        varchar500 avatar_url
        varchar100 wechat_openid UK "微信 OpenID"
        varchar100 wechat_unionid
        varchar100 google_id UK "Google ID"
        boolean is_active "账号是否激活"
        boolean is_verified "是否已验证"
        timestamptz created_time
        timestamptz last_login_time
        timestamptz updated_time
    }
    
    TENANT_USERS {
        varchar36 id PK
        varchar36 tenant_id FK "所属租户"
        varchar36 user_id FK "全局用户 ID"
        varchar20 user_type "用户类型: admin|member|customer|end_user"
        varchar20 customer_type "客户类型: normal|vip|strategic"
        decimal10_2 customer_mrr "月经常性收入"
        varchar200 company_name "公司名称"
        integer vote_count "投票数(租户内)"
        integer feedback_count "反馈数(租户内)"
        integer comment_count "评论数(租户内)"
        varchar20 status "状态: active|suspended|left"
        timestamptz joined_at "加入时间"
        timestamptz last_active_at "最后活跃时间"
    }
    
    TENANT_USER_ROLES {
        varchar36 id PK
        varchar36 tenant_user_id FK "租户用户 ID"
        bigint role_id FK "角色 ID"
        timestamptz assigned_at "分配时间"
        varchar36 assigned_by FK "分配人"
    }
    
    SYS_ROLE {
        bigint id PK "角色 ID"
        varchar64 name "角色名称"
        varchar64 code "角色代码"
        integer sort "排序"
        varchar20 status "状态"
        varchar255 remark "备注"
        timestamptz created_time
        timestamptz updated_time
    }
    
    SYS_MENU {
        bigint id PK "菜单 ID"
        varchar64 name "菜单名称"
        bigint parent_id FK "父菜单 ID"
        varchar20 type "类型: menu|button"
        varchar128 path "路由路径"
        varchar128 component "组件路径"
        varchar128 perms "权限标识"
        varchar128 icon "图标"
        integer sort "排序"
        boolean visible "是否可见"
        timestamptz created_time
    }
    
    SYS_ROLE_MENU {
        bigint role_id FK PK "角色 ID"
        bigint menu_id FK PK "菜单 ID"
    }
    
    SYS_ROLE_SCOPE {
        bigint id PK
        bigint role_id FK "角色 ID"
        varchar20 scope_type "数据范围类型"
        varchar255 scope_value "数据范围值"
    }
    
    SYS_DEPT {
        bigint id PK "部门 ID"
        varchar64 name "部门名称"
        bigint parent_id FK "父部门 ID"
        integer sort "排序"
        varchar20 status "状态"
        timestamptz created_time
    }
    
    BOARDS {
        varchar36 id PK "看板 UUID"
        varchar36 tenant_id FK "所属租户"
        varchar100 name "看板名称"
        varchar100 url_name UK "URL slug"
        text description "看板描述"
        varchar20 access_mode "访问模式: public|private|restricted"
        text_array allowed_user_ids "受限模式下的允许用户列表"
        integer feedback_count "反馈总数"
        integer sort_order "排序"
        timestamptz created_time
        timestamptz updated_time
    }
    
    CATEGORIES {
        varchar36 id PK "分类 UUID"
        varchar36 board_id FK "所属看板"
        varchar100 name "分类名称"
        varchar100 slug "URL slug"
        text description "分类描述"
        varchar36 parent_id FK "父分类 ID"
        integer feedback_count "反馈数"
        integer sort_order "排序"
        timestamptz created_time
    }
    
    FEEDBACKS {
        varchar36 id PK "反馈 UUID"
        varchar36 tenant_id FK "所属租户"
        varchar36 board_id FK "所属看板"
        varchar36 author_id FK "作者(全局用户)"
        boolean is_anonymous "是否匿名"
        varchar100 author_name "匿名用户名"
        varchar255 author_email "匿名用户邮箱"
        varchar400 title "反馈标题"
        text details "反馈详情"
        varchar50 category "分类"
        varchar20 status "状态: open|planned|in_progress|completed|closed"
        varchar20 source "来源: web|api|screenshot|import"
        jsonb screenshots "截图数组(含元数据)"
        integer vote_count "投票数"
        integer comment_count "评论数"
        vector4096 embedding "内容向量(4096维)"
        varchar200 ai_summary "AI 摘要"
        float ai_confidence "AI 置信度"
        varchar36 duplicate_of_id FK "重复反馈 ID"
        varchar20 sentiment "情感: positive|negative|neutral"
        float sentiment_score "情感分数"
        varchar200 slug UK "公开访问 slug"
        boolean is_public "是否公开"
        varchar20 priority "优先级"
        timestamptz submitted_at "提交时间"
        timestamptz created_time
        timestamptz updated_time
        timestamptz deleted_at "软删除时间"
    }
    
    VOTES {
        varchar36 id PK "投票 UUID"
        varchar36 feedback_id FK "反馈 ID"
        varchar36 voter_id FK "投票者(全局用户)"
        varchar255 voter_email "投票者邮箱"
        integer weight "投票权重"
        varchar20 priority "优先级: nice_to_have|important|must_have"
        timestamptz created_time
    }
    
    COMMENTS {
        varchar36 id PK "评论 UUID"
        varchar36 feedback_id FK "反馈 ID"
        varchar36 author_id FK "评论者(全局用户)"
        text content "评论内容"
        boolean is_internal "是否内部评论"
        varchar36 parent_id FK "父评论 ID"
        timestamptz created_time
        timestamptz updated_time
        timestamptz deleted_at
    }
    
    TOPICS {
        varchar36 id PK "主题 UUID"
        varchar36 tenant_id FK "所属租户"
        varchar100 title "主题标题"
        text description "主题描述"
        varchar20 category "分类: bug|feature|performance|other"
        varchar20 status "状态: pending|planned|in_progress|completed|ignored"
        vector4096 centroid "主题中心向量"
        integer feedback_count "关联反馈数"
        boolean is_public "是否公开"
        varchar200 slug UK "公开访问 slug"
        timestamptz created_time
        timestamptz updated_time
    }
    
    PRIORITY_SCORES {
        varchar36 topic_id FK PK "主题 ID"
        integer impact_scope "影响范围(1-10)"
        integer business_value "业务价值(1-10)"
        integer dev_cost "开发成本(1-10)"
        float total_score "总分"
        timestamptz calculated_at "计算时间"
    }
    
    STATUS_HISTORIES {
        varchar36 id PK
        varchar36 topic_id FK "主题 ID"
        varchar20 from_status "原状态"
        varchar20 to_status "新状态"
        varchar36 changed_by FK "变更人"
        text change_reason "变更原因"
        timestamptz changed_at
    }
    
    MANUAL_ADJUSTMENTS {
        varchar36 id PK
        varchar36 feedback_id FK "反馈 ID"
        varchar36 from_topic_id FK "原主题 ID"
        varchar36 to_topic_id FK "新主题 ID"
        varchar36 adjusted_by FK "调整人"
        text reason "调整原因"
        timestamptz adjusted_at
    }
    
    FEEDBACK_MERGES {
        varchar36 id PK
        varchar36 source_feedback_id FK "源反馈 ID"
        varchar36 target_feedback_id FK "目标反馈 ID"
        varchar36 merged_by FK "合并人"
        text merge_reason "合并原因"
        float ai_similarity "AI 相似度"
        timestamptz merged_at
    }
    
    STATUS_HISTORY {
        varchar36 id PK
        varchar36 feedback_id FK "反馈 ID"
        varchar20 from_status "原状态"
        varchar20 to_status "新状态"
        varchar36 changed_by FK "变更人"
        text change_reason "变更原因"
        timestamptz changed_at
    }
    
    CHANGELOGS {
        varchar36 id PK "更新日志 UUID"
        varchar36 tenant_id FK "所属租户"
        varchar200 title "标题"
        text content "内容(Markdown)"
        varchar20 type "类型: feature|improvement|bugfix|announcement"
        boolean is_published "是否已发布"
        varchar200 slug UK "URL slug"
        timestamptz published_at "发布时间"
        timestamptz created_time
        timestamptz updated_time
    }
    
    CHANGELOG_TOPICS {
        varchar36 changelog_id FK PK "更新日志 ID"
        varchar36 topic_id FK PK "主题 ID"
    }
    
    INSIGHTS {
        varchar36 id PK "洞察 UUID"
        varchar36 tenant_id FK "所属租户"
        varchar20 insight_type "类型: trend|anomaly|recommendation"
        text content "洞察内容"
        jsonb metadata "元数据"
        timestamptz generated_at
    }
    
    USERECHO_TENANT_CONFIG {
        varchar36 id PK
        varchar36 tenant_id FK "所属租户"
        varchar100 config_key "配置键"
        text config_value "配置值"
        timestamptz created_time
        timestamptz updated_time
    }
    
    LOGIN_LOG {
        bigint id PK
        varchar36 user_id FK "用户 ID"
        varchar128 ip_address "IP 地址"
        varchar255 user_agent "用户代理"
        varchar20 login_status "登录状态: success|failed"
        text error_msg "错误信息"
        timestamptz login_time
    }
    
    OPERA_LOG {
        bigint id PK
        varchar36 user_id FK "用户 ID"
        varchar36 tenant_id FK "租户 ID"
        varchar64 module "模块名称"
        varchar20 operation "操作类型: create|update|delete"
        varchar255 description "操作描述"
        text request_params "请求参数"
        text response_data "响应数据"
        varchar128 ip_address "IP 地址"
        timestamptz created_time
    }
```

---

## 二、核心设计亮点

### 2.1 多租户用户模型

**设计理念**: 全局用户 + 租户关联

```
用户张三 (users.id = 'user_001')
  ├── Tenant A (tenant_users)
  │     ├── user_type: 'admin'
  │     └── roles: [SuperAdmin]
  ├── Tenant B (tenant_users)
  │     ├── user_type: 'end_user'
  │     └── roles: []
  └── Tenant C (tenant_users)
        ├── user_type: 'customer'
        ├── customer_mrr: 5000
        └── roles: [ProductManager]
```

**优势**:
- ✅ 一个用户可以在多个租户中扮演不同角色
- ✅ 真正的多租户 SaaS 架构
- ✅ 租户级数据隔离与权限控制
- ✅ 支持跨租户协作场景

### 2.2 Board-Feedback-Vote 架构

**核心流程**:
```
1. 用户提交 Feedback → Board
2. 其他用户对 Feedback 投票 (Vote)
3. 用户在 Feedback 下评论 (Comment)
4. AI 聚类相似 Feedback → Topic
5. Admin 管理 Topic 状态 → Roadmap
6. Topic 完成后发布 Changelog
```

### 2.3 截图存储优化

**纯 JSONB 设计**:
```json
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
```

**优势**:
- ✅ 消除数据冗余
- ✅ 灵活的元数据扩展
- ✅ 利用 PostgreSQL JSONB 强大查询能力

### 2.4 AI 聚类与去重

**核心机制**:
1. **向量化**: 每个 Feedback 生成 4096 维 embedding
2. **相似度检测**: 使用 pgvector 计算余弦相似度
3. **智能聚类**: AI 自动聚合相似 Feedback → Topic
4. **人工干预**: 通过 `manual_adjustments` 表记录人工调整

---

## 三、表分类与职责

### 3.1 租户与基础架构 (3 张表)
- `tenants`: 租户主表
- `userecho_tenant_config`: 租户配置
- `sys_dept`: 部门组织架构

### 3.2 用户与权限 (7 张表)
- `users`: 全局用户表
- `tenant_users`: 租户-用户关联表
- `tenant_user_roles`: 租户用户角色关联
- `sys_role`: 角色表
- `sys_menu`: 菜单表
- `sys_role_menu`: 角色-菜单关联
- `sys_role_scope`: 角色-数据权限

### 3.3 核心业务 (8 张表)
- `boards`: 反馈看板
- `categories`: 分类
- `feedbacks`: 用户反馈
- `votes`: 投票记录
- `comments`: 评论
- `feedback_merges`: 反馈合并记录
- `status_history`: 反馈状态历史

### 3.4 AI 聚类与主题 (4 张表)
- `topics`: 需求主题
- `priority_scores`: 优先级评分
- `status_histories`: 主题状态历史
- `manual_adjustments`: 人工调整记录

### 3.5 公开门户 (2 张表)
- `changelogs`: 更新日志
- `changelog_topics`: 更新日志-主题关联

### 3.6 日志与审计 (3 张表)
- `login_log`: 登录日志
- `opera_log`: 操作日志
- `insights`: AI 洞察

---

## 四、关键索引设计

### 4.1 高频查询索引
```sql
-- 用户查询
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_wechat ON users(wechat_openid);

-- 租户用户查询
CREATE INDEX idx_tenant_users_tenant ON tenant_users(tenant_id);
CREATE INDEX idx_tenant_users_user ON tenant_users(user_id);
CREATE INDEX idx_tenant_users_type ON tenant_users(user_type);

-- 反馈查询
CREATE INDEX idx_feedbacks_tenant ON feedbacks(tenant_id);
CREATE INDEX idx_feedbacks_board ON feedbacks(board_id);
CREATE INDEX idx_feedbacks_status ON feedbacks(status);
CREATE INDEX idx_feedbacks_author ON feedbacks(author_id);

-- 投票查询
CREATE INDEX idx_votes_feedback ON votes(feedback_id);
CREATE INDEX idx_votes_voter ON votes(voter_id);
```

### 4.2 向量索引
```sql
-- pgvector IVFFlat 索引
CREATE INDEX idx_feedbacks_embedding 
ON feedbacks USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 100);

CREATE INDEX idx_topics_centroid 
ON topics USING ivfflat (centroid vector_cosine_ops) 
WITH (lists = 50);
```

### 4.3 JSONB 索引
```sql
-- 截图元数据查询
CREATE INDEX idx_feedbacks_screenshots 
ON feedbacks USING gin (screenshots);
```

---

## 六、查询示例

### 6.1 获取用户在某租户的完整信息

```sql
SELECT 
    u.id, u.email, u.name,
    tu.user_type,
    tu.customer_type,
    tu.customer_mrr,
    array_agg(r.name) AS roles,
    array_agg(m.name) AS menus
FROM users u
JOIN tenant_users tu ON u.id = tu.user_id
LEFT JOIN tenant_user_roles tur ON tu.id = tur.tenant_user_id
LEFT JOIN sys_role r ON tur.role_id = r.id
LEFT JOIN sys_role_menu rm ON r.id = rm.role_id
LEFT JOIN sys_menu m ON rm.menu_id = m.id
WHERE u.id = $user_id AND tu.tenant_id = $tenant_id
GROUP BY u.id, u.email, u.name, tu.user_type, tu.customer_type, tu.customer_mrr;
```

### 6.2 获取 Board 的所有 Feedback (含作者信息)

```sql
SELECT 
    f.id, f.title, f.vote_count,
    u.name AS author_name,
    tu.user_type AS author_type,
    tu.customer_mrr,
    array_length(jsonb_path_query_array(f.screenshots, '$.items'), 1) AS screenshot_count
FROM feedbacks f
JOIN users u ON f.author_id = u.id
LEFT JOIN tenant_users tu ON u.id = tu.user_id AND f.tenant_id = tu.tenant_id
WHERE f.board_id = $board_id
  AND f.deleted_at IS NULL
ORDER BY f.vote_count DESC, f.created_time DESC;
```

### 6.3 检查用户对 Board 的访问权限

```sql
SELECT 
    CASE 
        WHEN b.access_mode = 'public' THEN TRUE
        WHEN b.access_mode = 'private' AND tu.user_type IN ('admin', 'member') THEN TRUE
        WHEN b.access_mode = 'restricted' AND u.id = ANY(b.allowed_user_ids) THEN TRUE
        ELSE FALSE
    END AS can_access
FROM boards b
CROSS JOIN users u
LEFT JOIN tenant_users tu ON u.id = tu.user_id AND b.tenant_id = tu.tenant_id
WHERE b.id = $board_id AND u.id = $user_id;
```

### 6.4 AI 相似度查询 (查找重复 Feedback)

```sql
SELECT 
    f.id, f.title,
    1 - (f.embedding <=> $query_embedding) AS similarity
FROM feedbacks f
WHERE f.tenant_id = $tenant_id
  AND f.deleted_at IS NULL
  AND 1 - (f.embedding <=> $query_embedding) > 0.85
ORDER BY similarity DESC
LIMIT 10;
```

---

## 七、设计优势

| 特性 | 实现方式 | 优势 |
|------|---------|------|
| **真正的多租户** | 全局用户 + 租户关联表 | 一个用户可在多个租户中扮演不同角色 |
| **灵活的权限** | 租户级 RBAC | 同一用户在不同租户有不同权限 |
| **AI 原生** | pgvector + 4096维向量 | 高效的语义搜索和聚类 |
| **截图智能识别** | JSONB 元数据存储 | 支持多平台截图解析 |
| **完整审计** | 状态历史 + 操作日志 | 所有变更可追溯 |
| **公开门户** | Board + Changelog | 支持 Canny 式公开反馈 |

### 7.2 核心表统计

- **总表数**: 27 张
- **核心业务表**: 8 张
- **用户权限表**: 7 张
- **AI 相关表**: 4 张
- **日志审计表**: 3 张

### 7.3 下一步行动

- [ ] ✅ Review 本 ER 图设计
- [ ] 生成完整的 DDL 建表脚本
- [ ] 创建 Pydantic Schema 模型
- [ ] 设计 RESTful API 接口
- [ ] 实现核心业务逻辑

---

**文档维护者**: 技术团队  
**最后更新**: 2025-12-31
