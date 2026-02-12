# Feedalyze 数据库迁移 SQL

> **创建时间:** 2025-12-21  
> **用途:** 手动执行数据库迁移（如果 Alembic 迁移不可用）

## 1. 修改 sys_user 表（添加租户关联）

### PostgreSQL

```sql
-- 添加 tenant_id 列
ALTER TABLE sys_user 
ADD COLUMN tenant_id VARCHAR(36) DEFAULT 'default-tenant';

-- 添加索引
CREATE INDEX idx_sys_user_tenant_id ON sys_user(tenant_id);

-- 添加外键约束（需要先创建 tenants 表）
-- ALTER TABLE sys_user 
-- ADD CONSTRAINT fk_sys_user_tenant 
-- FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE;
```

### MySQL

```sql
-- 添加 tenant_id 列
ALTER TABLE sys_user 
ADD COLUMN tenant_id VARCHAR(36) DEFAULT 'default-tenant';

-- 添加索引
ALTER TABLE sys_user 
ADD INDEX idx_sys_user_tenant_id (tenant_id);

-- 添加外键约束（需要先创建 tenants 表）
-- ALTER TABLE sys_user 
-- ADD CONSTRAINT fk_sys_user_tenant 
-- FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE;
```

---

## 2. 创建 Feedalyze 核心表

### 2.1 租户表 (tenants)

```sql
CREATE TABLE tenants (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    status VARCHAR(20) DEFAULT 'active' NOT NULL,
    deleted_at TIMESTAMP WITH TIME ZONE DEFAULT NULL,
    created_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- 创建索引
CREATE INDEX idx_tenants_status ON tenants(status);
CREATE INDEX idx_tenants_deleted_at ON tenants(deleted_at);

-- 创建默认租户
INSERT INTO tenants (id, name, status, created_time, updated_time) 
VALUES ('default-tenant', '默认租户', 'active', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);
```

### 2.2 客户表 (customers)

```sql
CREATE TABLE customers (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL,
    name VARCHAR(100) NOT NULL,
    customer_type VARCHAR(20) DEFAULT 'normal' NOT NULL,
    business_value INTEGER DEFAULT 1 NOT NULL,
    deleted_at TIMESTAMP WITH TIME ZONE DEFAULT NULL,
    created_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    
    CONSTRAINT fk_customers_tenant 
        FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE
);

-- 创建索引
CREATE INDEX idx_customers_tenant_id ON customers(tenant_id);
CREATE INDEX idx_customers_deleted_at ON customers(deleted_at);
```

### 2.3 需求主题表 (topics)

```sql
CREATE TABLE topics (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL,
    title VARCHAR(100) NOT NULL,
    category VARCHAR(20) DEFAULT 'other' NOT NULL,
    status VARCHAR(20) DEFAULT 'pending' NOT NULL,
    description TEXT DEFAULT NULL,
    ai_generated BOOLEAN DEFAULT TRUE NOT NULL,
    ai_confidence REAL DEFAULT NULL,
    feedback_count INTEGER DEFAULT 0 NOT NULL,
    deleted_at TIMESTAMP WITH TIME ZONE DEFAULT NULL,
    created_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    
    CONSTRAINT fk_topics_tenant 
        FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE
);

-- 创建索引
CREATE INDEX idx_topics_tenant_id ON topics(tenant_id);
CREATE INDEX idx_topics_status ON topics(status);
CREATE INDEX idx_topics_category ON topics(category);
CREATE INDEX idx_topics_deleted_at ON topics(deleted_at);
```

### 2.4 反馈表 (feedbacks)

```sql
CREATE TABLE feedbacks (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL,
    customer_id VARCHAR(36) DEFAULT NULL,
    anonymous_author VARCHAR(100) DEFAULT NULL,
    anonymous_source VARCHAR(50) DEFAULT NULL,
    topic_id VARCHAR(36) DEFAULT NULL,
    content TEXT NOT NULL,
    source VARCHAR(20) DEFAULT 'manual' NOT NULL,
    ai_summary VARCHAR(50) DEFAULT NULL,
    is_urgent BOOLEAN DEFAULT FALSE NOT NULL,
    ai_metadata JSON DEFAULT NULL,
    submitted_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    deleted_at TIMESTAMP WITH TIME ZONE DEFAULT NULL,
    created_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    
    CONSTRAINT fk_feedbacks_tenant 
        FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE,
    CONSTRAINT fk_feedbacks_customer 
        FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE SET NULL,
    CONSTRAINT fk_feedbacks_topic 
        FOREIGN KEY (topic_id) REFERENCES topics(id) ON DELETE SET NULL,
    CONSTRAINT chk_author_exists 
        CHECK (customer_id IS NOT NULL OR anonymous_author IS NOT NULL)
);

-- 创建索引
CREATE INDEX idx_feedbacks_tenant_id ON feedbacks(tenant_id);
CREATE INDEX idx_feedbacks_topic_id ON feedbacks(topic_id);
CREATE INDEX idx_feedbacks_customer_id ON feedbacks(customer_id);
CREATE INDEX idx_feedbacks_source ON feedbacks(source);
CREATE INDEX idx_feedbacks_is_urgent ON feedbacks(is_urgent);
CREATE INDEX idx_feedbacks_deleted_at ON feedbacks(deleted_at);
CREATE INDEX idx_feedbacks_submitted_at ON feedbacks(submitted_at);
```

### 2.5 优先级评分表 (priority_scores)

```sql
CREATE TABLE priority_scores (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL,
    topic_id VARCHAR(36) NOT NULL,
    impact_scope INTEGER DEFAULT 1 NOT NULL,
    business_value INTEGER DEFAULT 1 NOT NULL,
    dev_cost INTEGER DEFAULT 1 NOT NULL,
    urgency_factor REAL DEFAULT 1.0 NOT NULL,
    total_score REAL DEFAULT 0.0 NOT NULL,
    created_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    
    CONSTRAINT fk_priority_scores_tenant 
        FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE,
    CONSTRAINT fk_priority_scores_topic 
        FOREIGN KEY (topic_id) REFERENCES topics(id) ON DELETE CASCADE
);

-- 创建索引
CREATE INDEX idx_priority_scores_tenant_id ON priority_scores(tenant_id);
CREATE INDEX idx_priority_scores_topic_id ON priority_scores(topic_id);
CREATE INDEX idx_priority_scores_total_score ON priority_scores(total_score);
```

### 2.6 状态变更历史表 (status_histories)

```sql
CREATE TABLE status_histories (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL,
    topic_id VARCHAR(36) NOT NULL,
    from_status VARCHAR(20) NOT NULL,
    to_status VARCHAR(20) NOT NULL,
    reason TEXT DEFAULT NULL,
    changed_by INTEGER NOT NULL,
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    
    CONSTRAINT fk_status_histories_tenant 
        FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE,
    CONSTRAINT fk_status_histories_topic 
        FOREIGN KEY (topic_id) REFERENCES topics(id) ON DELETE CASCADE
);

-- 创建索引
CREATE INDEX idx_status_histories_tenant_id ON status_histories(tenant_id);
CREATE INDEX idx_status_histories_topic_id ON status_histories(topic_id);
CREATE INDEX idx_status_histories_changed_at ON status_histories(changed_at);
```

### 2.7 人工调整记录表 (manual_adjustments)

```sql
CREATE TABLE manual_adjustments (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL,
    feedback_id VARCHAR(36) NOT NULL,
    original_topic_id VARCHAR(36) DEFAULT NULL,
    new_topic_id VARCHAR(36) DEFAULT NULL,
    adjustment_type VARCHAR(20) NOT NULL,
    reason TEXT DEFAULT NULL,
    adjusted_by INTEGER NOT NULL,
    adjusted_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    
    CONSTRAINT fk_manual_adjustments_tenant 
        FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE,
    CONSTRAINT fk_manual_adjustments_feedback 
        FOREIGN KEY (feedback_id) REFERENCES feedbacks(id) ON DELETE CASCADE
);

-- 创建索引
CREATE INDEX idx_manual_adjustments_tenant_id ON manual_adjustments(tenant_id);
CREATE INDEX idx_manual_adjustments_feedback_id ON manual_adjustments(feedback_id);
CREATE INDEX idx_manual_adjustments_adjusted_at ON manual_adjustments(adjusted_at);
```

---

## 3. 验证迁移

```sql
-- 检查所有表是否创建成功
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public'  -- PostgreSQL
  -- table_schema = 'fba'  -- MySQL
  AND table_name IN (
      'tenants', 
      'customers', 
      'feedbacks', 
      'topics', 
      'priority_scores', 
      'status_histories', 
      'manual_adjustments'
  )
ORDER BY table_name;

-- 检查租户表
SELECT * FROM tenants;

-- 检查 sys_user 表是否添加了 tenant_id
SELECT column_name, data_type, column_default 
FROM information_schema.columns 
WHERE table_name = 'sys_user' AND column_name = 'tenant_id';
```

---

## 4. 回滚脚本（慎用）

```sql
-- 删除 Feedalyze 表（按依赖顺序）
DROP TABLE IF EXISTS manual_adjustments CASCADE;
DROP TABLE IF EXISTS status_histories CASCADE;
DROP TABLE IF EXISTS priority_scores CASCADE;
DROP TABLE IF EXISTS feedbacks CASCADE;
DROP TABLE IF EXISTS topics CASCADE;
DROP TABLE IF EXISTS customers CASCADE;
DROP TABLE IF EXISTS tenants CASCADE;

-- 移除 sys_user 的 tenant_id 列
ALTER TABLE sys_user DROP COLUMN IF EXISTS tenant_id;
```

---

## 5. 注意事项

1. **执行前备份**: 务必先备份现有数据库
   ```bash
   # PostgreSQL
   pg_dump -U postgres -d fba > backup_$(date +%Y%m%d).sql
   
   # MySQL
   mysqldump -u root -p fba > backup_$(date +%Y%m%d).sql
   ```

2. **MySQL vs PostgreSQL 差异**:
   - PostgreSQL 使用 `TIMESTAMP WITH TIME ZONE`
   - MySQL 使用 `TIMESTAMP`（需要设置时区）
   - PostgreSQL 使用 `BOOLEAN`
   - MySQL 使用 `TINYINT(1)`
   - PostgreSQL 使用 `SERIAL` 或 `BIGSERIAL`
   - MySQL 使用 `AUTO_INCREMENT`

3. **JSON 类型支持**:
   - PostgreSQL 原生支持 `JSON` 和 `JSONB`
   - MySQL 5.7+ 支持 `JSON`
   - 如果是 MySQL 5.6，需要使用 `TEXT` 类型

4. **UUID 生成**:
   - PostgreSQL 可使用 `uuid-ossp` 扩展
   - MySQL 使用 `UUID()` 函数
   - 应用层使用 `uuid4_str()` 生成（推荐）

---

**文档维护者:** 技术团队  
**最后更新:** 2025-12-21
