# Feedalyze 日志使用指南

## 快速参考

### 导入日志
```python
from backend.common.log import log
```

### 使用规范

#### ✅ 正确使用
```python
# 1. 异常处理 - 包含完整上下文
try:
    result = await some_operation(tenant_id, data)
except Exception as e:
    log.error(f'Failed to [操作] for tenant {tenant_id}: {e}')
    raise

# 2. 关键业务节点 - 批量操作开始/结束
log.info(f'Starting Excel import for tenant: {tenant_id}')
# ... 处理
log.info(f'Excel import completed for tenant {tenant_id}: success={success}, failed={failed}')

# 3. 降级处理 - 使用 WARNING
log.warning(f'Failed to initialize {provider_name} client: {e}')

# 4. 调试信息 - 使用 DEBUG
log.debug(f'Found {len(feedbacks)} unclustered feedbacks for tenant {tenant_id}')
```

#### ❌ 错误使用
```python
# 1. 记录成功 - 不需要
log.info('Operation completed successfully')  # 删除

# 2. 缺少上下文
log.error(f'Failed: {e}')  # 垃圾

# 3. 循环中滥用 INFO
for item in items:
    log.info(f'Processing {item}')  # 改为 DEBUG 或批量记录

# 4. 使用 print
print('debug info')  # 永远不要用
```

---

## 日志级别

| 级别 | 用途 | 示例 |
|------|------|------|
| DEBUG | 调试信息 | `log.debug(f'Embedding shape: {shape}')` |
| INFO | 关键业务节点 | `log.info(f'Clustering started for tenant {tid}')` |
| WARNING | 可恢复的异常 | `log.warning(f'API retry {n}/{max}: {e}')` |
| ERROR | 操作失败 | `log.error(f'Failed to create topic {id}: {e}')` |
| CRITICAL | 系统级故障 | `log.critical('Database connection pool exhausted')` |

---

## 5W 原则

每条 ERROR 日志必须回答：

- **Who** - 哪个租户？ → `tenant_id`
- **What** - 什么操作？ → `Failed to create feedback`
- **When** - 什么时候？ → 自动时间戳
- **Where** - 哪个资源？ → `feedback_id`, `topic_id`, etc.
- **Why** - 为什么失败？ → `{e}`

---

## 检查清单

提交代码前，确认：

- [ ] 所有 `except` 块都有 `log.error()`
- [ ] ERROR 日志包含 `tenant_id` 和资源ID
- [ ] 没有在正常流程记录 INFO
- [ ] 没有在循环中滥用日志
- [ ] 没有记录敏感信息
- [ ] 永远不使用 `print()`

---

## 相关文档

- **完整最佳实践指南**: `/docs/development/logging-best-practices.md`
- **代码审查报告**: `./LOGGING_REVIEW.md`
- **修复总结**: `./LOGGING_FIXES_SUMMARY.md`

---

## 联系

如有疑问，请查看 `docs/development/logging-best-practices.md` 或 `AGENTS.md` 中的日志规范。


