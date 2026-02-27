# Celery 任务调试指南

本指南帮助你通过 debug 日志排查 Celery worker 任务不被消费的问题。

## 日志流程说明

### 1. 任务注册阶段（应用启动时）

当 Celery app 初始化时，你应该看到：

```
[Celery Init] CELERY_BROKER=redis
[Celery Init] REDIS_HOST=...
[Celery Init] REDIS_PORT=...
[Celery Init] Searching for tasks in: .../backend/app/task/tasks
[Celery Init] ✅ Found tasks package: backend.app.task.tasks
[Celery Init] ✅ Found tasks package: backend.app.task.tasks.db_log
[Celery Init] ✅ Found tasks package: backend.app.task.tasks.userecho
[Celery Init] Total task packages found: 3
[Celery Init] ✅ Registered 11 user tasks: [...]
```

**检查点：**
- ✅ 如果看到 11 个任务注册成功，说明任务定义没问题
- ❌ 如果任务数量不对，检查 `tasks.py` 文件是否使用了 `@shared_task` 装饰器

### 2. Worker 启动阶段

当 worker 进程启动时，你应该看到：

```
[Celery Worker] 🔧 Worker initializing...
[Celery Worker] 🚀 Worker READY! Waiting for tasks...
[Celery Worker] Broker: redis://...
[Celery Worker] Concurrency: 4
```

**检查点：**
- ✅ 如果看到 "Worker READY!"，说明 worker 已经启动并连接到 broker
- ❌ 如果没看到这些日志，说明 worker 没有正常启动，检查：
  - Redis/RabbitMQ 是否运行？
  - Broker URL 配置是否正确？
  - 网络连接是否正常？

### 3. 任务发送阶段（发起任务时）

当调用 `task.delay()` 或 `task.apply_async()` 时，你应该看到：

```
[Celery Publish] 📤 Publishing task: userecho_clustering_batch (id=abc12345...)
[Celery Publish] ✅ Published task: userecho_clustering_batch (id=abc12345...)
```

**检查点：**
- ✅ 如果看到 "Published task"，说明任务已成功发送到 broker
- ❌ 如果没看到，检查：
  - 发送任务的代码是否执行了？
  - Broker 连接是否正常？

### 4. 任务接收阶段（worker 收到任务）

当 worker 从队列中拿到任务时，你应该看到：

```
[Celery Worker] 📥 Received task: userecho_clustering_batch (id=abc12345...)
```

**检查点：**
- ✅ 如果看到 "Received task"，说明 worker 成功从 broker 获取任务
- ❌ 如果没看到，说明任务没有被 worker 接收，检查：
  - Worker 是否真的在运行？
  - Broker 是否正确？（Redis database 是否一致？）
  - 任务是否发送到了不同的队列？

### 5. 任务执行阶段

当任务开始执行时，你应该看到：

```
[Celery Worker] ▶️  Starting task: userecho_clustering_batch (id=abc12345...)
```

任务执行过程中，你会看到任务内部的日志（如果有的话）。

任务执行完成后，你应该看到：

```
[Celery Worker] ⏹️  Finished task: userecho_clustering_batch (id=abc12345..., state=SUCCESS)
[Celery Worker] ✅ Task succeeded: userecho_clustering_batch
```

如果任务失败：

```
[Celery Worker] ❌ Task failed: abc12345... - <exception>
```

如果任务重试：

```
[Celery Worker] 🔄 Task retrying: abc12345... - <reason>
```

## 常见问题排查

### 问题 0: 本地能运行，部署后不工作（最常见！）

**现象：** 本地执行 `start_celery_worker.ps1` 一切正常，但 Dokploy/Docker 环境中任务不被消费

**原因：** Worker Pool 类型不匹配

**本地 vs 生产环境差异：**
- 本地：`-P custom` + `CELERY_CUSTOM_WORKER_POOL=AsyncIOPool` ✅
- 生产：`-P gevent` ❌ (不支持 async def)

**检查方法：**
```bash
# 在服务器上执行
bash verify_worker_config.sh
```

**解决方法：**
1. 修改 `deploy/monolith/supervisord.conf`:
   ```ini
   [program:fba_celery_worker]
   environment=CELERY_CUSTOM_WORKER_POOL="celery_aio_pool.pool:AsyncIOPool"
   command=python -m celery ... worker -P custom -c 4
   ```
2. 重启 worker: `supervisorctl restart fba_celery_worker`

**详细说明：** 参考 `docs/development/celery-local-vs-dokploy.md`

---

### 问题 1: 任务注册了，但 worker 没有 "READY" 日志

**原因：** Worker 进程没有正常启动

**检查：**
```bash
# 测试 broker 连接
cd server
.venv/Scripts/python.exe test_worker_config.py
```

**解决：**
- 检查 Redis 是否运行：`redis-cli ping`
- 检查 Redis 密码、端口是否正确
- 检查防火墙是否阻止连接

### 问题 2: Worker READY 了，但任务没有被接收

**原因：** 任务发送到了不同的 broker database 或队列

**检查：**
1. 发送任务的进程和 worker 使用的 `CELERY_BROKER_REDIS_DATABASE` 是否一致？
   ```bash
   # 发送任务的进程（FastAPI）
   echo $CELERY_BROKER_REDIS_DATABASE
   
   # Worker 进程
   # 检查 worker 启动日志中的 database 编号
   ```

2. 检查 Redis 中是否有任务堆积：
   ```bash
   redis-cli
   > SELECT 1  # 你的 database 编号
   > LLEN celery  # 检查默认队列长度
   > LRANGE celery 0 10  # 查看队列中的任务
   ```

**解决：**
- 确保所有进程使用相同的 `CELERY_BROKER_REDIS_DATABASE`
- 重启 worker 和 FastAPI 应用

### 问题 3: 任务被接收但没有执行

**原因：** 任务执行过程中卡死或崩溃

**检查：**
- 查看 worker 日志中的异常
- 检查任务代码中是否有阻塞操作
- 检查是否有 event loop 相关错误

**解决：**
- 在任务代码中添加更多 debug 日志
- 使用 `time_limit` 和 `soft_time_limit` 防止任务卡死

## 调试工具

### 1. 检查任务注册情况
```bash
cd server
.venv/Scripts/python.exe test_celery_tasks.py
```

### 2. 检查 worker 配置和 broker 连接
```bash
cd server
.venv/Scripts/python.exe test_worker_config.py
```

### 3. 测试发送任务
```bash
cd server
.venv/Scripts/python.exe test_task_send.py
```

### 4. 查看 Celery worker 实时日志
启动 worker 时添加 `-l debug` 参数：
```bash
cd server
.venv/Scripts/python.exe -m celery -A backend.app.task.celery:celery_app worker -P custom -c 4 -l debug
```

### 5. 使用 Flower 监控（可选）
```bash
cd server
.venv/Scripts/python.exe -m celery -A backend.app.task.celery:celery_app flower
# 访问 http://localhost:5555
```

## 完整日志示例

一个正常的任务执行流程应该产生如下日志：

```
# 1. 任务注册
[Celery Init] ✅ Registered 11 user tasks: [...]

# 2. Worker 启动
[Celery Worker] 🔧 Worker initializing...
[Celery Worker] 🚀 Worker READY! Waiting for tasks...

# 3. 发送任务
[Celery Publish] 📤 Publishing task: userecho_clustering_batch (id=abc12345...)
[Celery Publish] ✅ Published task: userecho_clustering_batch (id=abc12345...)

# 4. Worker 接收任务
[Celery Worker] 📥 Received task: userecho_clustering_batch (id=abc12345...)

# 5. 执行任务
[Celery Worker] ▶️  Starting task: userecho_clustering_batch (id=abc12345...)
[Task xyz] Starting clustering for tenant test-tenant-id
...
[Celery Worker] ⏹️  Finished task: userecho_clustering_batch (id=abc12345..., state=SUCCESS)
[Celery Worker] ✅ Task succeeded: userecho_clustering_batch
```

如果你的日志在某一步中断，就能快速定位问题所在。
