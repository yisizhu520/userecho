# UserEcho 业务逻辑日志使用审查报告

## 审查时间
2025-12-22

## 总体评价
🟡 **凑合** - 基础使用正确，但缺少关键上下文信息

---

## 详细问题清单

### 1. clustering_service.py

#### 问题 1：循环中记录 INFO（第 137 行）
```python
# ❌ 当前代码
for label, cluster_feedbacks in clusters.items():
    # ...
    log.info(f'Created topic: {topic.title} with {len(cluster_feedbacks)} feedbacks')
```

**问题：** 在循环中记录 INFO，如果有 100 个 cluster，就会打 100 条日志

**修复方案：** 批量记录或使用 DEBUG
```python
# ✅ 改进方案 1：批量记录
for label, cluster_feedbacks in clusters.items():
    # ... 创建 topic
    created_topics.append(...)

log.info(f'Created {len(created_topics)} topics for tenant {tenant_id}')

# ✅ 改进方案 2：使用 DEBUG
for label, cluster_feedbacks in clusters.items():
    # ...
    log.debug(f'Created topic: {topic.title} with {len(cluster_feedbacks)} feedbacks')
```

---

#### 问题 2：记录正常流程（第 54 行）
```python
# ❌ 当前代码
log.info(f'Found {len(feedbacks)} unclustered feedbacks')
```

**问题：** 这是查询结果，属于正常流程，不需要 INFO 级别

**修复方案：** 使用 DEBUG 或删除
```python
# ✅ 改进
log.debug(f'Found {len(feedbacks)} unclustered feedbacks')
# 或者直接删除，后面的 "Starting clustering" 已经足够
```

---

#### 问题 3：缺少上下文（第 157、242 行）
```python
# ❌ 当前代码
log.error(f'Clustering failed: {e}')
log.error(f'Failed to get clustering suggestions: {e}')
```

**问题：** 缺少 tenant_id，无法定位是哪个租户的问题

**修复方案：** 添加完整上下文
```python
# ✅ 改进
log.error(f'Clustering failed for tenant {tenant_id}: {e}')
log.error(f'Failed to get clustering suggestions for feedback {feedback_id}, tenant {tenant_id}: {e}')
```

---

#### 问题 4：记录正常流程（第 79 行）
```python
# ❌ 当前代码
log.info(f'Got {len(embeddings)} valid embeddings, shape: {embeddings_array.shape}')
```

**问题：** 这是中间步骤，不是关键业务节点

**修复方案：** 改为 DEBUG
```python
# ✅ 改进
log.debug(f'Got {len(embeddings)} valid embeddings, shape: {embeddings_array.shape}')
```

---

### 2. import_service.py

#### 问题 1：记录正常流程（第 111 行）
```python
# ❌ 当前代码
log.info(f'Excel loaded: {len(df)} rows, columns: {list(df.columns)}')
```

**问题：** 文件读取成功是正常流程，不需要 INFO

**修复方案：** 改为 DEBUG
```python
# ✅ 改进
log.debug(f'Excel loaded: {len(df)} rows, columns: {list(df.columns)}')
```

---

#### 问题 2：缺少上下文（第 195 行）
```python
# ❌ 当前代码
log.error(f'Import failed: {e}')
```

**问题：** 缺少 tenant_id 和文件名

**修复方案：** 添加完整上下文
```python
# ✅ 改进
log.error(f'Excel import failed for tenant {tenant_id}, file {file.filename}: {e}')
```

---

### 3. topic_service.py

#### 问题：缺少详细上下文（第 58、109 行）
```python
# ❌ 当前代码
log.error(f'Failed to get topic detail: {e}')
log.error(f'Failed to update topic status: {e}')
```

**问题：** 缺少 tenant_id 和 topic_id

**修复方案：** 添加完整上下文
```python
# ✅ 改进
log.error(f'Failed to get topic detail for topic {topic_id}, tenant {tenant_id}: {e}')
log.error(f'Failed to update topic {topic_id} status to {new_status} for tenant {tenant_id}: {e}')
```

---

### 4. priority_service.py

#### 问题：缺少详细上下文（第 47、106 行）
```python
# ❌ 当前代码
log.error(f'Failed to calculate priority score: {e}')
log.error(f'Failed to get priority ranking: {e}')
```

**问题：** 缺少 tenant_id 和 topic_id

**修复方案：** 添加完整上下文
```python
# ✅ 改进
log.error(f'Failed to calculate priority score for topic {data.topic_id}, tenant {tenant_id}: {e}')
log.error(f'Failed to get priority ranking for tenant {tenant_id}: {e}')
```

---

### 5. customer_service.py

#### 问题：缺少上下文（第 45 行）
```python
# ❌ 当前代码
log.error(f'Failed to create customer: {e}')
```

**问题：** 缺少 tenant_id 和 customer name

**修复方案：** 添加完整上下文
```python
# ✅ 改进
log.error(f'Failed to create customer "{data.name}" for tenant {tenant_id}: {e}')
```

---

### 6. feedback_service.py

#### 问题：缺少上下文（第 62 行）
```python
# ❌ 当前代码
log.error(f'Failed to create feedback: {e}')
```

**问题：** 缺少 tenant_id

**修复方案：** 添加完整上下文
```python
# ✅ 改进
log.error(f'Failed to create feedback for tenant {tenant_id}: {e}')
```

---

## 改进优先级

### 🔴 高优先级（必须修复）
1. **所有 ERROR 日志添加完整上下文** - tenant_id、资源ID、操作类型
   - 影响：无法快速定位问题
   - 修复成本：低（只需添加变量）

### 🟡 中优先级（建议修复）
2. **移除正常流程的 INFO 日志** - 改为 DEBUG 或删除
   - 影响：生产日志噪音过多
   - 修复成本：低

3. **循环中的 INFO 改为 DEBUG 或批量记录**
   - 影响：日志洪水
   - 修复成本：低

### 🟢 低优先级（可选）
4. 添加更多 DEBUG 日志帮助开发调试

---

## 最佳实践检查清单

| 检查项 | 状态 | 说明 |
|--------|------|------|
| 所有 except 块都有日志 | ✅ | 已做到 |
| ERROR 日志包含完整上下文 | ❌ | **需要改进** - 缺少 tenant_id、资源ID |
| 没有在正常流程记录 INFO | ❌ | **需要改进** - 有一些成功操作在记录 |
| 没有在循环中滥用日志 | ❌ | **需要改进** - clustering_service.py 第 137 行 |
| 没有记录敏感信息 | ✅ | 未发现 |
| 日志级别使用正确 | 🟡 | 基本正确，部分可改进 |
| 永远不使用 print() | ✅ | 全部使用 log |

---

## 修复建议

### 立即修复的模式
```python
# 模式 1：添加 tenant_id 到所有 ERROR 日志
log.error(f'Failed to [操作] for tenant {tenant_id}: {e}')

# 模式 2：添加资源 ID
log.error(f'Failed to [操作] [资源类型] {resource_id} for tenant {tenant_id}: {e}')

# 模式 3：批量操作记录最终结果，不记录中间步骤
log.info(f'[操作]开始: {count} items for tenant {tenant_id}')
# ... 循环处理 ...
log.info(f'[操作]完成: success={success}, failed={failed}, tenant {tenant_id}')
```

---

## 总结

当前代码的日志使用**基础正确**，但缺少**关键上下文信息**。建议优先修复所有 ERROR 日志的上下文问题，这对生产环境问题排查至关重要。

修复后，日志质量将从 🟡 凑合 提升到 🟢 好品味。
