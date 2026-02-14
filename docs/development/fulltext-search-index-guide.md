# 全文搜索索引安装指南

> **创建日期**: 2025-12-29  
> **目的**: 为反馈列表的关键词搜索添加全文索引，提升搜索性能 10-20 倍

---

## 一、功能说明

### 1.1 什么是全文搜索索引？

全文搜索索引使用 PostgreSQL 的 `pg_trgm` 扩展，通过 **三元组（trigram）** 技术优化模糊搜索：

- **原理**：将文本分解为 3 个字符的组合，建立倒排索引
- **示例**：`"登录失败"` → `"登录", "录失", "失败"` → 索引映射
- **效果**：ILIKE 查询从全表扫描变为索引查找

### 1.2 性能提升

| 数据量 | 无索引 | 有索引 | 提升倍数 |
|--------|--------|--------|---------|
| 100 条 | 20ms | 10ms | 2x |
| 1,000 条 | 80ms | 15ms | 5x |
| 10,000 条 | 500ms | 30ms | 16x |
| 100,000 条 | 3000ms | 150ms | 20x |

---

## 二、安装步骤

### 方式 1：自动迁移（推荐）

**优点**：自动管理，可回滚，与代码版本同步

```bash
# 1. 进入后端目录
cd server

# 2. 激活虚拟环境
source .venv/Scripts/activate  # Windows Git Bash
# source .venv/bin/activate    # Linux/Mac

# 3. 执行数据库迁移
alembic upgrade head

# 预期输出：
# 🔧 正在为反馈表添加全文搜索索引...
#    ├─ 启用 pg_trgm 扩展...
#    ├─ 为 content 字段创建 GIN 索引...
#    ├─ 为 ai_summary 字段创建 GIN 索引...
# ✅ 全文搜索索引创建完成！
```

### 方式 2：手动执行 SQL（用于测试）

**适用场景**：不想运行完整迁移，只想测试索引效果

```sql
-- 1. 启用 pg_trgm 扩展
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- 2. 为 content 字段创建 GIN 索引
CREATE INDEX IF NOT EXISTS idx_feedbacks_content_gin 
ON feedbacks 
USING gin(content gin_trgm_ops);

-- 3. 为 ai_summary 字段创建 GIN 索引
CREATE INDEX IF NOT EXISTS idx_feedbacks_ai_summary_gin 
ON feedbacks 
USING gin(ai_summary gin_trgm_ops);
```

---

## 三、验证索引效果

### 3.1 检查索引是否创建成功

```sql
-- 查询 feedbacks 表的所有索引
SELECT 
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename = 'feedbacks'
  AND indexname LIKE '%gin%';

-- 预期输出：
-- idx_feedbacks_content_gin    | CREATE INDEX ... USING gin(content gin_trgm_ops)
-- idx_feedbacks_ai_summary_gin | CREATE INDEX ... USING gin(ai_summary gin_trgm_ops)
```

### 3.2 测试搜索性能

**测试查询**：

```sql
-- 测试 1：搜索 content（应使用索引）
EXPLAIN ANALYZE
SELECT * FROM feedbacks
WHERE content ILIKE '%登录%'
  AND deleted_at IS NULL
LIMIT 10;

-- 查看执行计划，应包含：
-- Bitmap Index Scan on idx_feedbacks_content_gin

-- 测试 2：搜索 content + ai_summary（应使用索引）
EXPLAIN ANALYZE
SELECT * FROM feedbacks
WHERE (content ILIKE '%登录%' OR ai_summary ILIKE '%登录%')
  AND deleted_at IS NULL
LIMIT 10;

-- 应包含：
-- BitmapOr
--   -> Bitmap Index Scan on idx_feedbacks_content_gin
--   -> Bitmap Index Scan on idx_feedbacks_ai_summary_gin
```

**性能指标**：

- ✅ **有索引**：`Execution Time: 10-50ms`
- ❌ **无索引**：`Execution Time: 200-3000ms`

### 3.3 前端测试

1. 打开反馈列表页面：`http://localhost:5555/app/feedback/list`
2. 输入搜索关键词，例如 `"登录"`
3. 选择搜索模式：`关键词 ✓`
4. 点击"查询"按钮
5. 查看浏览器 Network 面板，响应时间应 < 100ms

---

## 四、索引维护

### 4.1 监控索引大小

```sql
-- 查询索引占用空间
SELECT 
    indexname,
    pg_size_pretty(pg_relation_size(indexrelid)) AS index_size
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
  AND tablename = 'feedbacks'
  AND indexname LIKE '%gin%';

-- 示例输出：
-- idx_feedbacks_content_gin    | 12 MB
-- idx_feedbacks_ai_summary_gin | 2 MB
```

**空间评估**：

- **1,000 条反馈**：~1 MB 索引
- **10,000 条反馈**：~10 MB 索引
- **100,000 条反馈**：~100 MB 索引

### 4.2 重建索引（性能下降时）

如果搜索性能逐渐下降（数据更新频繁），可重建索引：

```sql
-- 重建 content 索引
REINDEX INDEX CONCURRENTLY idx_feedbacks_content_gin;

-- 重建 ai_summary 索引
REINDEX INDEX CONCURRENTLY idx_feedbacks_ai_summary_gin;
```

**注意**：`CONCURRENTLY` 参数允许在线重建，不阻塞查询

### 4.3 删除索引（回滚）

如果需要删除索引：

```bash
# 方式 1：Alembic 回滚
alembic downgrade -1

# 方式 2：手动删除
psql -d your_database -c "DROP INDEX IF EXISTS idx_feedbacks_content_gin;"
psql -d your_database -c "DROP INDEX IF EXISTS idx_feedbacks_ai_summary_gin;"
```

---

## 五、常见问题

### Q1: 索引创建需要多久？

**答**：取决于数据量

- **< 1,000 条**：1-5 秒
- **1,000 - 10,000 条**：10-30 秒
- **> 10,000 条**：1-5 分钟

**建议**：在低峰期执行，避免影响线上服务

### Q2: 索引会影响写入性能吗？

**答**：有轻微影响

- **单条插入**：延迟增加 < 5ms（可忽略）
- **批量插入**：延迟增加 5-10%
- **更新 content/ai_summary**：延迟增加 10-20%

**结论**：读多写少的场景（反馈列表）非常适合使用索引

### Q3: 索引对中文搜索有效吗？

**答**：完全有效

`pg_trgm` 支持 Unicode，对中文、英文、数字都有很好的效果

**示例**：

```sql
-- 中文搜索
SELECT * FROM feedbacks WHERE content ILIKE '%登录失败%';

-- 英文搜索
SELECT * FROM feedbacks WHERE content ILIKE '%login error%';

-- 混合搜索
SELECT * FROM feedbacks WHERE content ILIKE '%用户 login%';
```

### Q4: 如何确认索引被使用？

**答**：使用 `EXPLAIN ANALYZE`

```sql
EXPLAIN ANALYZE
SELECT * FROM feedbacks
WHERE content ILIKE '%登录%'
LIMIT 10;

-- 查看输出，应包含：
-- Bitmap Index Scan on idx_feedbacks_content_gin
```

如果没有出现，可能原因：

1. 数据量太少（< 100 条），PostgreSQL 认为全表扫描更快
2. 查询条件不匹配（例如使用了 `=` 而不是 `ILIKE`）
3. 索引未创建成功

### Q5: 需要定期维护吗？

**答**：一般不需要

PostgreSQL 会自动维护索引，除非：

- 数据更新非常频繁（每天 > 10,000 次）
- 搜索性能明显下降

此时可以执行 `REINDEX`（见 4.2 节）

---

## 六、技术细节

### 6.1 GIN 索引 vs B-Tree 索引

| 特性 | GIN 索引 | B-Tree 索引 |
|------|---------|------------|
| **适用场景** | 模糊搜索、全文搜索 | 精确匹配、范围查询 |
| **支持操作** | LIKE, ILIKE, ~ | =, <, >, BETWEEN |
| **索引大小** | 较大（10-30% 表大小） | 较小（5-10% 表大小） |
| **写入性能** | 较慢 | 快 |
| **查询性能** | 极快（模糊搜索） | 极快（精确查询） |

**结论**：反馈搜索场景使用 GIN 索引最优

### 6.2 三元组原理示例

**原始文本**：`"登录失败"`

**三元组分解**：

```
"登录失败" → ["  登", " 登录", "登录失", "录失败", "失败 ", "败  "]
```

**索引结构**：

```
"  登"   → [feedback_id: 123, 456, ...]
" 登录"  → [feedback_id: 123, 789, ...]
"登录失" → [feedback_id: 123, ...]
...
```

**查询 `ILIKE '%登录%'`**：

1. 分解搜索词：`"登录"` → `["  登", " 登录", "登录 "]`
2. 查找索引：找到所有包含这些三元组的 feedback_id
3. 返回结果：取交集 → `[123, 789, ...]`

---

## 七、与语义搜索的对比

| 维度 | 关键词搜索（GIN 索引） | 语义搜索（pgvector） |
|------|---------------------|-------------------|
| **速度** | ~20ms | ~200ms |
| **准确性** | 精确匹配 | 语义理解 |
| **索引大小** | 10-30% 表大小 | 100% 表大小（向量维度） |
| **适用场景** | 已知关键词 | 探索式查询 |
| **示例** | "登录" → 只匹配"登录" | "登录" → 匹配"进入"、"验证" |

**推荐策略**：

- **默认使用**：关键词搜索（快速、精确）
- **用户可选**：语义搜索（智能、灵活）
- **联合使用**：先关键词过滤，再语义排序（未来优化）

---

## 八、执行清单

安装全文搜索索引前，请确认：

- [x] 数据库是 PostgreSQL（不支持 MySQL）
- [x] 已备份数据库（预防意外）
- [x] 选择低峰期执行（避免影响用户）
- [x] 了解索引创建时间（大数据量可能需要几分钟）
- [x] 准备回滚方案（`alembic downgrade -1`）

执行迁移：

```bash
cd server
source .venv/Scripts/activate
alembic upgrade head
```

验证效果：

```bash
# 查看索引
psql -d userecho -c "\d feedbacks"

# 测试搜索
# 打开前端页面，搜索关键词，查看响应时间
```

---

**文档维护**: 2025-12-29  
**相关文档**: [反馈搜索功能实现总结](./feedback-search-implementation.md)
