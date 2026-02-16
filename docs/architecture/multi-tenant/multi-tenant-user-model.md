# 多租户用户模型重新设计

> **核心问题**: 一个用户可以在不同租户中扮演不同角色  
> **场景**: 张三可以是 Tenant A 的 Admin,同时是 Tenant B 的普通用户,还是 Tenant C 的 PM

---

## 一、问题分析

### 1.1 错误的设计 (原方案)

```sql
CREATE TABLE users (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36),  -- ❌ 错误: 一个用户只能属于一个租户
    user_types TEXT[]
);
```

**问题:**
- ❌ `tenant_id` 字段限制了用户只能属于一个租户
- ❌ 无法表达「张三在 Tenant A 是 Admin,在 Tenant B 是普通用户」

### 1.2 正确的理解

**用户 (User)** 是**全局唯一**的实体:
- 用户通过 `email` 或 `wechat_openid` 全局唯一标识
- 用户可以加入多个租户
- 用户在不同租户中有不同的角色和权限

**示例:**
```
张三 (user_001)
  ├── Tenant A: Admin 角色
  ├── Tenant B: End User 角色 (投票者)
  └── Tenant C: Product Manager 角色
```

---

## 二、正确的多租户用户模型

### 2.1 核心表设计

#### **1. Users (全局用户表)**

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
    
    -- 第三方登录 (全局唯一)
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
    
    -- ❌ 不再有 tenant_id 字段
    -- ❌ 不再有 user_types 字段
);

-- 索引
CREATE INDEX idx_users_email ON users(email) WHERE email IS NOT NULL;
CREATE INDEX idx_users_wechat ON users(wechat_openid) WHERE wechat_openid IS NOT NULL;
```

**核心特点:**
- ✅ **全局用户**: 不属于任何租户,是平台级用户
- ✅ **唯一标识**: 通过 email 或第三方登录 ID 全局唯一
- ✅ **无角色信息**: 角色信息在 `tenant_user` 表中

---

#### **2. TenantUser (租户-用户关联表)**

```sql
CREATE TABLE tenant_users (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- 用户在该租户中的类型
    user_type VARCHAR(20) NOT NULL,  -- 'admin', 'member', 'customer', 'end_user'
    
    -- 客户相关字段 (仅 user_type='customer' 时有值)
    customer_type VARCHAR(20),  -- 'normal', 'vip', 'strategic'
    customer_mrr DECIMAL(10,2),
    company_name VARCHAR(200),
    
    -- 统计 (该租户内的统计)
    vote_count INTEGER DEFAULT 0,
    feedback_count INTEGER DEFAULT 0,
    comment_count INTEGER DEFAULT 0,
    
    -- 状态
    status VARCHAR(20) DEFAULT 'active',  -- 'active', 'suspended', 'left'
    
    -- 时间戳
    joined_at TIMESTAMPTZ DEFAULT NOW(),
    last_active_at TIMESTAMPTZ,
    
    UNIQUE(tenant_id, user_id)  -- 一个用户在一个租户中只能有一条记录
);

-- 索引
CREATE INDEX idx_tenant_users_tenant ON tenant_users(tenant_id);
CREATE INDEX idx_tenant_users_user ON tenant_users(user_id);
CREATE INDEX idx_tenant_users_type ON tenant_users(user_type);
```

**核心特点:**
- ✅ **多对多关系**: 一个用户可以属于多个租户
- ✅ **租户内角色**: `user_type` 定义用户在该租户中的身份
- ✅ **租户内统计**: 每个租户独立统计用户活跃度

**user_type 枚举值:**
- `admin`: 租户管理员
- `member`: 团队成员
- `customer`: B 端客户 (有 MRR 等字段)
- `end_user`: C 端用户 (公开门户注册)

---

#### **3. TenantUserRole (租户内的 RBAC 角色)**

```sql
CREATE TABLE tenant_user_roles (
    id VARCHAR(36) PRIMARY KEY,
    tenant_user_id VARCHAR(36) NOT NULL REFERENCES tenant_users(id) ON DELETE CASCADE,
    role_id BIGINT NOT NULL REFERENCES sys_role(id) ON DELETE CASCADE,
    
    -- 时间戳
    assigned_at TIMESTAMPTZ DEFAULT NOW(),
    assigned_by VARCHAR(36) REFERENCES users(id),
    
    UNIQUE(tenant_user_id, role_id)
);

-- 索引
CREATE INDEX idx_tenant_user_roles_tenant_user ON tenant_user_roles(tenant_user_id);
CREATE INDEX idx_tenant_user_roles_role ON tenant_user_roles(role_id);
```

**核心特点:**
- ✅ **租户内权限**: 角色是租户级别的,不是全局的
- ✅ **灵活分配**: 同一个用户在不同租户可以有不同角色

---

### 2.2 完整的关系图

```
users (全局用户)
  └── tenant_users (租户-用户关联)
        ├── tenant_id → tenants
        ├── user_type (admin, member, customer, end_user)
        └── tenant_user_roles (RBAC 角色)
              └── role_id → sys_role
                    ├── sys_role_menu (菜单权限)
                    └── sys_role_scope (数据权限)
```

---

## 三、数据示例

### 3.1 场景: 张三的多租户身份

```sql
-- 1. 全局用户
INSERT INTO users (id, email, name) 
VALUES ('user_001', 'zhangsan@example.com', '张三');

-- 2. 张三在 Tenant A 是管理员
INSERT INTO tenant_users (id, tenant_id, user_id, user_type)
VALUES ('tu_001', 'tenant_a', 'user_001', 'admin');

INSERT INTO tenant_user_roles (tenant_user_id, role_id)
VALUES ('tu_001', 1);  -- role_id=1 是 SuperAdmin

-- 3. 张三在 Tenant B 是普通用户
INSERT INTO tenant_users (id, tenant_id, user_id, user_type)
VALUES ('tu_002', 'tenant_b', 'user_001', 'end_user');

-- 4. 张三在 Tenant C 是 PM
INSERT INTO tenant_users (id, tenant_id, user_id, user_type)
VALUES ('tu_003', 'tenant_c', 'user_001', 'member');

INSERT INTO tenant_user_roles (tenant_user_id, role_id)
VALUES ('tu_003', 2);  -- role_id=2 是 ProductManager
```

**查询张三的所有租户:**
```sql
SELECT 
    t.name AS tenant_name,
    tu.user_type,
    array_agg(r.name) AS roles
FROM tenant_users tu
JOIN tenants t ON tu.tenant_id = t.id
LEFT JOIN tenant_user_roles tur ON tu.id = tur.tenant_user_id
LEFT JOIN sys_role r ON tur.role_id = r.id
WHERE tu.user_id = 'user_001'
GROUP BY t.name, tu.user_type;

-- 结果:
-- tenant_name | user_type | roles
-- Tenant A    | admin     | {SuperAdmin}
-- Tenant B    | end_user  | NULL
-- Tenant C    | member    | {ProductManager}
```

---

## 四、核心表更新

### 4.1 Feedbacks 表

```sql
CREATE TABLE feedbacks (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL REFERENCES tenants(id),
    board_id VARCHAR(36) NOT NULL REFERENCES boards(id),
    
    -- 作者信息 (简化)
    author_id VARCHAR(36) REFERENCES users(id),  -- 全局用户 ID
    is_anonymous BOOLEAN DEFAULT FALSE,
    author_name VARCHAR(100),  -- 匿名用户名称
    
    -- 反馈内容
    title VARCHAR(400) NOT NULL,
    details TEXT,
    
    -- 截图 (纯 JSONB)
    screenshots JSONB,
    
    -- 其他字段...
);
```

**关键点:**
- `author_id` 关联全局 `users` 表
- 通过 `tenant_id` 确定是哪个租户的反馈
- 查询时 JOIN `tenant_users` 获取作者在该租户的身份

---

### 4.2 Votes 表

```sql
CREATE TABLE votes (
    id VARCHAR(36) PRIMARY KEY,
    feedback_id VARCHAR(36) NOT NULL REFERENCES feedbacks(id) ON DELETE CASCADE,
    
    -- 投票者 (全局用户)
    voter_id VARCHAR(36) NOT NULL REFERENCES users(id),
    
    -- 投票权重
    weight INTEGER DEFAULT 1,
    priority VARCHAR(20),
    
    created_time TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(feedback_id, voter_id)
);
```

---

### 4.3 Comments 表

```sql
CREATE TABLE comments (
    id VARCHAR(36) PRIMARY KEY,
    feedback_id VARCHAR(36) NOT NULL REFERENCES feedbacks(id) ON DELETE CASCADE,
    
    -- 评论者 (全局用户)
    author_id VARCHAR(36) NOT NULL REFERENCES users(id),
    
    content TEXT NOT NULL,
    is_internal BOOLEAN DEFAULT FALSE,
    parent_id VARCHAR(36) REFERENCES comments(id),
    
    created_time TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 五、查询示例

### 5.1 获取用户在某个租户的角色

```sql
SELECT 
    u.id, u.email, u.name,
    tu.user_type,
    array_agg(r.name) AS roles
FROM users u
JOIN tenant_users tu ON u.id = tu.user_id
LEFT JOIN tenant_user_roles tur ON tu.id = tur.tenant_user_id
LEFT JOIN sys_role r ON tur.role_id = r.id
WHERE u.id = $user_id AND tu.tenant_id = $tenant_id
GROUP BY u.id, u.email, u.name, tu.user_type;
```

### 5.2 检查用户是否有权限访问某个 Board

```sql
SELECT EXISTS (
    SELECT 1 
    FROM tenant_users tu
    WHERE tu.user_id = $user_id 
      AND tu.tenant_id = $tenant_id
      AND tu.status = 'active'
) AS has_access;
```

### 5.3 获取 Feedback 作者在该租户的身份

```sql
SELECT 
    f.id, f.title,
    u.name AS author_name,
    tu.user_type AS author_type,
    tu.customer_mrr
FROM feedbacks f
JOIN users u ON f.author_id = u.id
LEFT JOIN tenant_users tu ON u.id = tu.user_id AND f.tenant_id = tu.tenant_id
WHERE f.id = $feedback_id;
```

### 5.4 获取用户在所有租户的反馈统计

```sql
SELECT 
    t.name AS tenant_name,
    tu.user_type,
    tu.feedback_count,
    tu.vote_count
FROM tenant_users tu
JOIN tenants t ON tu.tenant_id = t.id
WHERE tu.user_id = $user_id
ORDER BY tu.last_active_at DESC;
```

---

## 六、权限控制逻辑

### 6.1 中间件: 获取当前租户用户

```python
from fastapi import Request, HTTPException

async def get_current_tenant_user(request: Request, tenant_id: str):
    """获取用户在当前租户的身份"""
    user = request.user  # 全局用户
    
    # 查询用户在该租户的记录
    tenant_user = await db.execute(
        select(TenantUser)
        .where(TenantUser.user_id == user.id)
        .where(TenantUser.tenant_id == tenant_id)
        .where(TenantUser.status == 'active')
    )
    
    if not tenant_user:
        raise HTTPException(403, "You don't have access to this tenant")
    
    return tenant_user
```

### 6.2 权限检查

```python
async def check_permission(tenant_user: TenantUser, permission: str):
    """检查用户在该租户是否有某个权限"""
    # 1. 检查用户类型
    if tenant_user.user_type == 'admin':
        return True  # 管理员有所有权限
    
    # 2. 检查 RBAC 角色
    roles = await db.execute(
        select(SysRole)
        .join(TenantUserRole)
        .where(TenantUserRole.tenant_user_id == tenant_user.id)
    )
    
    for role in roles:
        if permission in role.permissions:
            return True
    
    return False
```

---

## 七、数据迁移方案

### 7.1 迁移现有用户

```sql
-- 1. 迁移 sys_user (Admin)
-- 先插入全局用户
INSERT INTO users (id, email, name, created_time)
SELECT id::VARCHAR, email, username, created_time
FROM sys_user;

-- 再创建租户关联 (假设所有 sys_user 都属于默认租户)
INSERT INTO tenant_users (id, tenant_id, user_id, user_type, joined_at)
SELECT 
    gen_random_uuid()::VARCHAR,
    'default_tenant',
    id::VARCHAR,
    'admin',
    created_time
FROM sys_user;

-- 迁移角色关联
INSERT INTO tenant_user_roles (id, tenant_user_id, role_id, assigned_at)
SELECT 
    gen_random_uuid()::VARCHAR,
    tu.id,
    sur.role_id,
    NOW()
FROM sys_user_role sur
JOIN tenant_users tu ON tu.user_id = sur.user_id::VARCHAR
WHERE tu.tenant_id = 'default_tenant';

-- 2. 迁移 customers
INSERT INTO users (id, email, name, created_time)
SELECT id, NULL, name, created_time
FROM customers
WHERE NOT EXISTS (SELECT 1 FROM users WHERE users.id = customers.id);

INSERT INTO tenant_users (id, tenant_id, user_id, user_type, customer_type, customer_mrr, joined_at)
SELECT 
    gen_random_uuid()::VARCHAR,
    tenant_id,
    id,
    'customer',
    customer_type,
    NULL,  -- 需要从其他地方获取 MRR
    created_time
FROM customers;
```

---

## 八、总结

### 8.1 核心改进

| 改进点 | 旧设计 | 新设计 |
|--------|--------|--------|
| 用户归属 | 用户属于单一租户 | 用户是全局的,可加入多个租户 |
| 角色管理 | `users.user_types` 数组 | `tenant_users.user_type` + RBAC |
| 权限控制 | 全局角色 | 租户级角色 |
| 数据隔离 | `users.tenant_id` | `tenant_users.tenant_id` |

### 8.2 优势

1. ✅ **真正的多租户**: 一个用户可以在多个租户中有不同身份
2. ✅ **灵活的权限**: 同一用户在不同租户有不同权限
3. ✅ **清晰的数据模型**: 全局用户 + 租户关联
4. ✅ **易于扩展**: 支持未来的跨租户协作场景

### 8.3 典型场景支持

- ✅ 张三是 Tenant A 的 Admin,可以管理所有数据
- ✅ 张三是 Tenant B 的普通用户,只能投票和评论
- ✅ 张三是 Tenant C 的 PM,可以管理反馈但不能修改设置
- ✅ 张三可以在多个租户之间切换,每个租户看到不同的权限

---

**文档维护者**: 技术团队  
**最后更新**: 2025-12-30
