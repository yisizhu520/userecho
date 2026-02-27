# 本地 vs Dokploy Celery Worker 启动差异分析

## 问题现象

- ✅ **本地**：执行 `start_celery_worker.ps1` 能正常启动 worker，能 receive 和处理 task
- ❌ **Dokploy**：任务注册成功，但任务不被消费，没有 Worker READY 日志

## 根本原因：Pool 类型不匹配

### 关键差异对比

| 项目 | 本地 (Windows) | Dokploy (Linux) | 影响 |
|------|---------------|-----------------|------|
| **Pool 类型** | `AsyncIOPool` (`-P custom`) | `gevent` (`-P gevent`) | ❌ **致命差异** |
| **环境变量** | `CELERY_CUSTOM_WORKER_POOL` 已设置 | 未设置 | ❌ **必须** |
| **并发数** | 4 | 50 | ⚠️ 可能过高 |
| **任务类型** | 支持 `async def` | 不支持原生 `async def` | ❌ **阻塞** |

### 为什么 gevent pool 不工作？

你的任务使用了 **原生 async def**：

```python
# tasks.py
@shared_task
async def generate_insight_report(...):  # ← async def
    async with local_db_session() as db:
        ...
```

**gevent pool 的问题：**
1. **不支持原生 asyncio** - gevent 使用自己的协程系统（greenlets）
2. **事件循环冲突** - gevent 的 monkey patching 会破坏 asyncio 的事件循环
3. **任务会卡死或崩溃** - async/await 语法在 gevent 环境下无法正常工作

**AsyncIOPool 的优势：**
1. ✅ **完全支持 async def** - 原生 asyncio 支持
2. ✅ **事件循环管理** - 自动为每个 worker 创建和管理事件循环
3. ✅ **与代码架构匹配** - 你的代码大量使用 async/await

## 解决方案

### 1. 修改 Dokploy supervisord.conf (已完成)

**修改前：**
```ini
[program:fba_celery_worker]
command=/fba/.venv/bin/python -m celery -A backend.app.task.celery worker --loglevel=INFO -P gevent -c 50
```

**修改后：**
```ini
[program:fba_celery_worker]
# 必须设置环境变量
environment=CELERY_CUSTOM_WORKER_POOL="celery_aio_pool.pool:AsyncIOPool"
# 使用 -P custom 而非 -P gevent
command=/fba/.venv/bin/python -m celery -A backend.app.task.celery worker --loglevel=INFO -P custom -c 4
```

### 2. 重启 Dokploy 容器

```bash
# SSH 到 Dokploy 服务器
ssh user@your-server

# 重启 supervisord 或容器
supervisorctl restart fba_celery_worker

# 或者重启整个容器
docker restart <container_name>
```

### 3. 验证修复

重启后应该看到：

```
[Celery Init] ✅ Registered 11 user tasks: [...]
[Celery Init] Registering signal handlers...
[Celery Worker] 🔧 Worker initializing...
[Celery Worker] 🚀 Worker READY! Waiting for tasks...
```

触发任务后应该看到：

```
[Celery Worker] 📥 Received task: userecho_clustering_batch
[Celery Worker] ▶️  Starting task: userecho_clustering_batch
[Celery Worker] ✅ Task succeeded: userecho_clustering_batch
```

## 其他注意事项

### 并发数调整

- **本地**：`-c 4`（4 个并发任务）
- **Dokploy**：从 50 降低到 4

**原因：**
- AsyncIOPool 的每个 worker 都有完整的事件循环，内存开销比 gevent 大
- 50 个并发可能导致内存溢出（OOM）
- 对于 I/O 密集型任务（AI API 调用、数据库查询），4-8 个并发通常足够

### 依赖确认

确保 Dokploy 环境已安装 `celery-aio-pool`：

```bash
# 在容器内执行
pip list | grep celery-aio-pool

# 如果未安装
pip install celery-aio-pool
```

（应该已经在 `pyproject.toml` 中声明，`uv sync` 会自动安装）

### 监控建议

使用 Flower 监控任务执行情况：

```bash
# 在 supervisord.conf 中添加（可选）
[program:fba_celery_flower]
command=/fba/.venv/bin/python -m celery -A backend.app.task.celery flower --port=5555
```

访问 `http://your-server:5555` 查看实时任务状态。

## 快速诊断清单

部署后检查：

- [ ] Worker 日志中出现 "Worker READY"
- [ ] 发送测试任务后，日志中出现 "Received task"
- [ ] 任务能正常执行完成，出现 "Task succeeded"
- [ ] Redis 中没有任务堆积（`LLEN celery` 返回 0）
- [ ] CPU/内存使用正常（AsyncIOPool 比 gevent 占用略高）

## 总结

| 问题 | 原因 | 解决方案 |
|------|------|---------|
| 任务不被消费 | gevent pool 不支持 async def | 使用 AsyncIOPool |
| Worker 不启动 | 缺少 `CELERY_CUSTOM_WORKER_POOL` 环境变量 | 在 supervisord.conf 中设置 |
| 本地工作但 Dokploy 不工作 | 启动参数不一致 | 统一使用 `-P custom -c 4` |

**核心原则：** 你的代码架构基于 asyncio，必须使用支持 async/await 的 worker pool。gevent 和 asyncio 是两套不兼容的并发模型。
