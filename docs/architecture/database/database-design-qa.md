# 数据库设计优化问题解答

> **问题 1**: 截图为什么不直接存 JSONB,还要多余存一个 URL 数组?  
> **问题 2**: 用户模型合并对 RBAC 权限控制、菜单权限、Tenant 关联有影响吗?

---

## 问题 1: 截图存储设计优化

### 原设计的问题

**原方案:**
```sql
screenshot_urls TEXT[]  -- URL 数组
screenshot_metadata JSONB  -- 元数据
```

**您的质疑:** 为什么不直接全部存 JSONB?

### 深入分析

#### 方案 A: 分离存储 (原方案)
```sql
screenshot_urls TEXT[] = ['url1.jpg', 'url2.jpg']
screenshot_metadata JSONB = {
  "screenshots": [
    {"url": "url1.jpg", "platform": "wechat", "confidence": 0.95},
    {"url": "url2.jpg", "platform": "xiaohongshu", "confidence": 0.88}
  ]
}
```

**优点:**
- ✅ 快速获取 URL 列表 (不需要解析 JSONB)
- ✅ 数组索引性能好 (`WHERE 'url' = ANY(screenshot_urls)`)

**缺点:**
- ❌ **数据冗余**: URL 存了两次
- ❌ **一致性风险**: 两个字段可能不同步
- ❌ **维护成本**: 更新时需要同时修改两个字段

#### 方案 B: 纯 JSONB (推荐)
```sql
screenshots JSONB = [
  {"url": "url1.jpg", "platform": "wechat", "confidence": 0.95},
  {"url": "url2.jpg", "platform": "xiaohongshu", "confidence": 0.88}
]
```

**优点:**
- ✅ **无冗余**: 单一数据源
- ✅ **扩展性强**: 可随时添加新字段 (如 `ocr_text`, `detected_objects`)
- ✅ **一致性**: 不存在同步问题

**缺点:**
- ⚠️ JSONB 查询稍慢 (但有 GIN 索引可优化)

### 性能对比

#### 查询 URL 列表
```sql
-- 方案 A (数组)
SELECT screenshot_urls FROM feedbacks WHERE id = $1;
-- 性能: ⭐⭐⭐⭐⭐

-- 方案 B (JSONB)
SELECT jsonb_path_query_array(screenshots, '$[*].url') FROM feedbacks WHERE id = $1;
-- 性能: ⭐⭐⭐⭐ (略慢,但可接受)
```

#### 查询包含特定 URL 的 Feedback
```sql
-- 方案 A (数组)
SELECT * FROM feedbacks WHERE 'url1.jpg' = ANY(screenshot_urls);
-- 性能: ⭐⭐⭐⭐⭐ (有索引)

-- 方案 B (JSONB)
SELECT * FROM feedbacks WHERE screenshots @> '[{"url": "url1.jpg"}]';
-- 性能: ⭐⭐⭐⭐ (GIN 索引优化)
```

### 结论: **采用方案 B (纯 JSONB)**

**理由:**
1. **数据一致性 > 性能**: 避免冗余和同步问题
2. **JSONB 性能足够**: PostgreSQL 的 JSONB + GIN 索引性能很好
3. **扩展性**: 未来可能需要存储 OCR 文本、检测到的对象等

**优化后的设计:**
```sql
CREATE TABLE feedbacks (
    -- ... 其他字段 ...
    
    -- 截图数据 (纯 JSONB)
    screenshots JSONB,  -- 数组格式
    /*
    示例:
    [
      {
        "url": "https://oss.com/img1.jpg",
        "platform": "wechat",
        "user_name": "张三",
        "confidence": 0.95,
        "ocr_text": "这个功能太慢了",  // 未来可扩展
        "uploaded_at": "2024-01-15T10:00:00Z"
      },
      {
        "url": "https://oss.com/img2.jpg",
        "platform": "xiaohongshu",
        "user_name": "李四",
        "confidence": 0.88
      }
    ]
    */
);

-- GIN 索引优化 JSONB 查询
CREATE INDEX idx_feedbacks_screenshots ON feedbacks USING gin (screenshots);
```

**常用查询示例:**
```sql
-- 1. 获取所有截图 URL
SELECT jsonb_path_query_array(screenshots, '$[*].url') AS urls
FROM feedbacks WHERE id = $1;

-- 2. 查询包含微信截图的 Feedback
SELECT * FROM feedbacks 
WHERE screenshots @> '[{"platform": "wechat"}]';

-- 3. 统计截图数量
SELECT id, jsonb_array_length(screenshots) AS screenshot_count
FROM feedbacks;

-- 4. 查询高置信度的截图
SELECT * FROM feedbacks
WHERE EXISTS (
    SELECT 1 FROM jsonb_array_elements(screenshots) AS s
    WHERE (s->>'confidence')::float > 0.9
);
```

---

## 问题 2: 用户模型合并对权限系统的影响

### 现有权限系统架构

根据代码分析,当前系统采用 **RBAC (Role-Based Access Control)** 模型:

```
sys_user (用户)
  ├── sys_user_role (用户-角色关联表)
  │     └── sys_role (角色)
  │           ├── sys_role_menu (角色-菜单关联)
  │           │     └── sys_menu (菜单)
  │           └── sys_role_scope (角色-数据权限)
  └── tenant_id (租户隔离)
```

**核心表:**
- `sys_user`: 内部管理员
- `sys_role`: 角色 (如 Admin, Manager)
- `sys_menu`: 菜单/权限点
- `sys_user_role`: 用户-角色多对多关联

### 合并用户表的影响分析

#### 方案对比

**方案 A: 保持三张表 (现状)**
```
sys_user (Admin)
end_user (C 端用户)
customer (B 端客户)
```

**方案 B: 合并为单表 (建议)**
```
users (统一用户表)
  └── user_types TEXT[]  -- 用户类型标签
```

#### 影响点 1: **菜单权限控制**

**现状:**
```python
# permission.py
if request.user.is_superuser:  # sys_user 的字段
    return or_(1 == 1)

for role in request.user.roles:  # sys_user 关联的 sys_role
    if not role.is_filter_scopes:
        return or_(1 == 1)
```

**合并后的影响:**
- ✅ **无影响**: `users` 表依然可以关联 `sys_role` 表
- ✅ 只需将 `sys_user_role` 改为 `user_role`

**优化方案:**

##### 选项 1: 保留 sys_role 表 (推荐)
```sql
-- 用户表 (合并后)
CREATE TABLE users (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) REFERENCES tenants(id),
    email VARCHAR(255),
    user_types TEXT[],  -- 简单类型标签: ['admin', 'customer', 'end_user']
    
    -- 客户相关字段
    customer_type VARCHAR(20),
    mrr DECIMAL(10,2),
    
    -- 第三方登录
    wechat_openid VARCHAR(100),
);

-- 保留现有 RBAC 系统
CREATE TABLE sys_role (
    id BIGINT PRIMARY KEY,
    name VARCHAR(32),  -- 'SuperAdmin', 'ProductManager'
    -- ... 权限配置
);

-- 用户-角色关联 (改名)
CREATE TABLE user_role (
    user_id VARCHAR(36) REFERENCES users(id),
    role_id BIGINT REFERENCES sys_role(id),
    PRIMARY KEY (user_id, role_id)
);
```

**逻辑:**
- `users.user_types`: 简单的身份标签 (`admin`, `customer`, `end_user`)
- `sys_role`: 复杂的权限角色 (`SuperAdmin`, `ProductManager`)
- 一个用户可以同时有:
  - `users.user_types = ['admin', 'customer']` (身份)
  - `user_role` 关联到 `SuperAdmin` 角色 (权限)

##### 选项 2: 废弃 sys_role,用 user_types 数组 (简化,但功能受限)
```sql
CREATE TABLE users (
    id VARCHAR(36) PRIMARY KEY,
    user_types TEXT[],  -- ['SuperAdmin', 'ProductManager', 'customer']
);

-- 权限配置存在代码中或配置文件
ROLE_PERMISSIONS = {
    'SuperAdmin': ['*'],  # 所有权限
    'ProductManager': ['feedback:read', 'feedback:update'],
    'customer': ['feedback:create', 'vote:create']
}
```

**优点:**
- ✅ 简化数据模型
- ✅ 适合小型团队

**缺点:**
- ❌ 失去动态权限配置能力 (需要改代码)
- ❌ 无法支持复杂的数据权限规则

#### 影响点 2: **Tenant 隔离**

**现状:**
```sql
sys_user.tenant_id  -- 内部用户可能没有 tenant_id (超级管理员)
customer.tenant_id  -- 客户必须属于某个 tenant
```

**合并后:**
```sql
users.tenant_id  -- 所有用户都有 tenant_id
```

**潜在问题:**
- ⚠️ 超级管理员 (跨租户) 如何处理?

**解决方案:**

##### 方案 1: tenant_id 允许 NULL
```sql
CREATE TABLE users (
    tenant_id VARCHAR(36) REFERENCES tenants(id),  -- 允许 NULL
    is_super_admin BOOLEAN DEFAULT FALSE,  -- 超级管理员标识
);

-- 查询时过滤
SELECT * FROM feedbacks 
WHERE tenant_id = $current_user_tenant_id 
   OR $current_user_is_super_admin = TRUE;
```

##### 方案 2: 特殊 tenant_id (推荐)
```sql
-- 创建系统租户
INSERT INTO tenants (id, name) VALUES ('system', 'System Tenant');

-- 超级管理员属于 system 租户
INSERT INTO users (id, tenant_id, user_types)
VALUES ('admin_001', 'system', ARRAY['SuperAdmin']);

-- 数据权限过滤时特殊处理
if user.tenant_id == 'system' and 'SuperAdmin' in user.user_types:
    # 可以访问所有租户数据
    pass
```

#### 影响点 3: **数据权限规则**

**现状:**
```python
# permission.py: filter_data_permission
for role in request.user.roles:  # sys_role 对象
    for scope in role.scopes:  # 数据权限规则
        if scope.status:
            data_rules.update(scope.rules)
```

**合并后的影响:**
- ✅ **无影响**: 依然通过 `user_role` 关联到 `sys_role`
- ✅ 数据权限规则逻辑不变

### 推荐方案: **混合模式**

```sql
-- 1. 用户表 (合并三张表)
CREATE TABLE users (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) REFERENCES tenants(id),  -- NULL = 超级管理员
    email VARCHAR(255),
    name VARCHAR(100),
    
    -- 简单类型标签 (用于业务逻辑)
    user_types TEXT[] DEFAULT ARRAY['end_user'],  -- ['admin', 'customer', 'end_user']
    
    -- 客户相关字段
    customer_type VARCHAR(20),
    mrr DECIMAL(10,2),
    
    -- 第三方登录
    wechat_openid VARCHAR(100),
    
    -- 统计
    vote_count INTEGER DEFAULT 0,
    
    created_time TIMESTAMPTZ DEFAULT NOW()
);

-- 2. 保留 RBAC 系统 (用于权限控制)
CREATE TABLE sys_role (
    id BIGINT PRIMARY KEY,
    name VARCHAR(32),
    -- ... 现有字段
);

CREATE TABLE user_role (
    user_id VARCHAR(36) REFERENCES users(id),
    role_id BIGINT REFERENCES sys_role(id),
    PRIMARY KEY (user_id, role_id)
);

-- 3. 保留菜单权限系统
CREATE TABLE sys_menu (
    -- ... 现有字段
);

CREATE TABLE sys_role_menu (
    role_id BIGINT REFERENCES sys_role(id),
    menu_id BIGINT REFERENCES sys_menu(id)
);
```

**字段说明:**
- `user_types`: 简单的身份标签,用于业务逻辑判断
  - 例: 判断是否是客户 (`'customer' IN user_types`)
- `user_role` 关联: 复杂的权限控制
  - 例: 判断是否有「删除反馈」权限

**代码适配:**
```python
# 原代码
if request.user.is_superuser:
    pass

# 新代码
if 'SuperAdmin' in [r.name for r in request.user.roles]:
    pass

# 或者保留 is_superuser 字段
if request.user.is_superuser:  # 计算属性
    pass
```

---

## 总结

### 问题 1: 截图存储

**结论:** ✅ **采用纯 JSONB**

```sql
screenshots JSONB  -- 数组格式,包含 url + 元数据
```

**理由:**
- 避免数据冗余
- 扩展性更强
- JSONB 性能足够 (有 GIN 索引)

---

### 问题 2: 用户模型合并

**结论:** ✅ **可以合并,对权限系统影响很小**

**推荐方案:**
```
users (合并表)
  ├── user_types TEXT[]  -- 业务身份标签
  └── user_role (关联表)
        └── sys_role (保留)  -- RBAC 权限角色
              ├── sys_role_menu
              └── sys_role_scope
```

**关键点:**
1. **分离关注点**:
   - `user_types`: 业务逻辑 (是客户? 是管理员?)
   - `sys_role`: 权限控制 (能删除反馈? 能查看所有数据?)

2. **Tenant 隔离**:
   - `tenant_id` 允许 NULL 或使用特殊 `system` 租户
   - 超级管理员可跨租户访问

3. **代码改动**:
   - 将 `sys_user_role` 改为 `user_role`
   - 将 `request.user.is_superuser` 改为检查角色
   - 其他权限逻辑基本不变

**优势:**
- ✅ 简化数据模型 (3 张表 → 1 张表)
- ✅ 保留完整的 RBAC 能力
- ✅ 代码改动最小

---

**文档维护者**: 技术团队  
**最后更新**: 2025-12-30
