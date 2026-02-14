# 已发现的性能问题和修复

> "循环中调用远程数据库 = 性能灾难" - Linus

## 问题总结

**根本原因：** Redis 和 PostgreSQL 部署在远程服务器（23.94.83.70），导致：
- Redis 单次操作延迟: ~350-1000ms（正常 <5ms）
- PostgreSQL 单次查询延迟: ~1400-4500ms（正常 <10ms）

## 已修复的致命性能问题

### ❌ 问题 1: 在线用户监控接口中的循环 Redis 调用

**文件:** `server/backend/app/admin/api/v1/monitor/online.py`

**问题代码:**
```python
for key in token_keys:  # 假设 50 个用户
    token = await redis_client.get(key)  # 350ms × 50 = 17.5秒
    # ...
    extra_info = await redis_client.get(f'...')  # 350ms × 50 = 17.5秒
    # 总计: 35秒（前端必然超时！）
```

**性能影响:**
- 10 个在线用户 = 20 次 Redis 调用 = 7 秒
- 50 个在线用户 = 100 次 Redis 调用 = 35 秒（前端超时）
- 100 个在线用户 = 200 次 Redis 调用 = 70 秒

**修复方案:** 使用 Redis Pipeline 批量获取
```python
# 批量获取所有 token
async with redis_client.pipeline() as pipe:
    for key in token_keys:
        pipe.get(key)
    tokens = await pipe.execute()  # 一次网络往返 = 700ms

# 批量获取所有 extra_info
async with redis_client.pipeline() as pipe:
    for key in extra_info_keys:
        if key:
            pipe.get(key)
    extra_infos = await pipe.execute()  # 一次网络往返 = 700ms

# 总计: 1.4秒（性能提升 25 倍！）
```

**性能对比:**

| 在线用户数 | 修复前 | 修复后 | 性能提升 |
|-----------|-------|-------|---------|
| 10 人 | 7秒 | 0.7秒 | 10x |
| 50 人 | 35秒（超时） | 1.4秒 | 25x |
| 100 人 | 70秒（超时） | 2.1秒 | 33x |

**状态:** ✅ 已修复

## 需要检查的潜在问题

### 🔍 需要审查的代码模式

运行以下搜索找出潜在的性能瓶颈：

```bash
# 查找循环中的 Redis 调用
grep -rn "for.*in.*:" server/backend/app --include="*.py" | grep -A 5 "redis_client"

# 查找循环中的数据库查询
grep -rn "for.*in.*:" server/backend/app --include="*.py" | grep -A 5 "await.*execute"
```

### 常见的性能反模式

#### ❌ 反模式 1: 循环中的 Redis GET
```python
for item_id in item_ids:
    data = await redis_client.get(f'item:{item_id}')
```

#### ✅ 正确做法: 使用 mget
```python
keys = [f'item:{item_id}' for item_id in item_ids]
values = await redis_client.mget(keys)
```

#### ❌ 反模式 2: 循环中的 Redis SET
```python
for item in items:
    await redis_client.set(f'item:{item.id}', item.json())
```

#### ✅ 正确做法: 使用 Pipeline
```python
async with redis_client.pipeline() as pipe:
    for item in items:
        pipe.set(f'item:{item.id}', item.json())
    await pipe.execute()
```

#### ❌ 反模式 3: N+1 查询
```python
users = await session.execute(select(User))
for user in users:
    posts = await session.execute(
        select(Post).where(Post.user_id == user.id)
    )
```

#### ✅ 正确做法: 使用 JOIN 或 selectinload
```python
# 方式 1: JOIN
result = await session.execute(
    select(User, Post)
    .join(Post, User.id == Post.user_id)
)

# 方式 2: selectinload
from sqlalchemy.orm import selectinload
users = await session.execute(
    select(User).options(selectinload(User.posts))
)
```

## 如何检查新代码的性能

### 1. 使用诊断工具测试延迟

```bash
cd server && source .venv/Scripts/activate
python backend/diagnose_connection.py
```

### 2. 计算理论延迟

使用诊断工具得到的单次延迟：
- Redis 单次: ~350ms
- PostgreSQL 单次: ~1400ms

**计算公式:**
```
总延迟 = (Redis调用次数 × 350ms) + (DB查询次数 × 1400ms)
```

**示例:**
```python
# 一个接口做了:
# - 2 次 Redis 查询
# - 3 次 DB 查询
总延迟 = (2 × 350ms) + (3 × 1400ms) = 700ms + 4200ms = 4900ms

# 如果前端超时设置是 30s，这个接口勉强能用
# 但如果超时是 5s，就会超时
```

### 3. 优化目标

**远程数据库环境下的优化目标:**

| 接口类型 | Redis 调用 | DB 查询 | 预估延迟 | 是否可接受 |
|---------|-----------|---------|---------|-----------|
| 简单查询 | ≤2 次 | ≤1 次 | ~2s | ✅ 勉强可用 |
| 列表查询 | ≤3 次 | ≤2 次 | ~4s | ⚠️ 慢但能用 |
| 复杂查询 | ≤5 次 | ≤3 次 | ~6s | ❌ 接近超时 |
| **任何情况** | **批量操作** | **批量操作** | **~1-2s** | ✅ 可接受 |

### 4. 代码审查清单

提交代码前，检查以下项目：

- [ ] 没有在 `for` 循环中调用 `redis_client.get()`
- [ ] 没有在 `for` 循环中调用 `redis_client.set()`
- [ ] 没有在 `for` 循环中调用 `session.execute()`
- [ ] 使用 `pipeline()` 批量操作 Redis
- [ ] 使用 `mget()` / `mset()` 批量读写
- [ ] 使用 JOIN 或 `selectinload()` 避免 N+1 查询
- [ ] 批量插入使用 `session.add_all()`

## 临时缓解措施

如果短期内无法迁移到本地数据库，可以使用以下临时方案：

### 1. 增加前端超时时间

```typescript
// 前端 axios 配置
axios.defaults.timeout = 30000; // 从 5000ms 增加到 30000ms
```

### 2. 使用进程内缓存减少 Redis 调用

```python
from functools import lru_cache
from datetime import datetime, timedelta

# 对不常变化的数据使用进程内缓存
_cache: dict[str, tuple[Any, datetime]] = {}
_cache_ttl = timedelta(minutes=1)

async def get_with_cache(key: str) -> Any:
    # L1: 进程内缓存（0ms）
    if key in _cache:
        value, expire_at = _cache[key]
        if datetime.now() < expire_at:
            return value
    
    # L2: Redis（350ms）
    value = await redis_client.get(key)
    _cache[key] = (value, datetime.now() + _cache_ttl)
    return value
```

### 3. 使用后台任务处理耗时操作

```python
from backend.app.task.celery import celery_app

@celery_app.task
def heavy_operation(tenant_id: str):
    """耗时操作放到后台执行"""
    # 大量 Redis/DB 操作
    pass

# 接口立即返回 task_id
@router.post('/start')
async def start_operation():
    task = heavy_operation.delay(tenant_id)
    return {'task_id': task.id}

# 前端轮询任务状态
@router.get('/status/{task_id}')
async def get_status(task_id: str):
    task = celery_app.AsyncResult(task_id)
    return {'status': task.status, 'result': task.result}
```

## 长期解决方案

**唯一正确的解决方案：使用本地或同城数据库**

详见：`docs/performance-optimization-remote-db.md`

## 监控和日志

### 查看慢请求

```bash
# 查看超过 5 秒的请求
grep "elapsed.*[0-9][0-9][0-9][0-9][0-9]\." logs/server.log

# 查看所有请求耗时
grep "elapsed" logs/server.log | sort -k 5 -n
```

### 添加性能日志

在关键路径添加日志：

```python
import time
from backend.common.log import log

start = time.perf_counter()

# ... 业务逻辑 ...

elapsed = (time.perf_counter() - start) * 1000
if elapsed > 1000:  # 超过 1 秒记录警告
    log.warning(f'Slow operation: {operation_name} took {elapsed:.2f}ms')
```

## 总结

1. **已修复:** 在线用户监控接口（性能提升 25 倍）
2. **根本原因:** 远程数据库延迟高（350ms Redis + 1400ms PostgreSQL）
3. **临时方案:** 使用 Pipeline、批量操作、缓存
4. **长期方案:** 迁移到本地或同城数据库（性能提升 100+ 倍）

**记住:** 在远程数据库环境下，**减少网络往返次数**是唯一的优化方向。
