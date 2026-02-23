# Celery Worker 日志配置

## 问题描述

在之前的配置中，Celery worker 的日志只输出到控制台（stdout），没有写入文件。这导致：
- 后台运行时难以排查问题
- 日志无法持久化保存
- 凌晨崩溃无法回溯

## 解决方案

### 核心修改

在 `backend/app/task/celery.py` 的 `init_celery()` 函数中，增加了 loguru 文件日志初始化：

```python
# 配置 loguru 文件日志（确保 Celery worker 的日志也能写入文件）
# 只在 worker 进程中配置，beat 和 flower 不需要
import sys
if 'worker' in sys.argv:
    from backend.common.log import setup_logging, set_custom_logfile
    setup_logging()
    set_custom_logfile()
```

### 为什么有效？

1. **复用现有日志配置**：使用 FastAPI 应用相同的 `backend.common.log` 配置
2. **自动初始化**：Celery worker 启动时自动调用 `set_custom_logfile()`
3. **进程隔离**：只在 worker 进程中配置，不影响 beat 和 flower

### 日志文件位置

```
server/logs/
├── fba_access.log      # INFO/DEBUG 级别日志
└── fba_error.log       # WARNING/ERROR/CRITICAL 级别日志
```

### 日志轮转规则

- **轮转时间**：每天 00:00
- **保留期限**：7 天
- **压缩规则**：自动重命名为 `fba_access_YYYY-MM-DD.log`

## 验证方法

### 方法 1：自动测试（推荐）

```bash
cd server/backend
bash test_celery_logging.sh
```

脚本会：
1. 清空旧日志
2. 启动 worker
3. 检查日志文件是否生成
4. 显示日志内容
5. 停止 worker

### 方法 2：手动测试

```bash
# 1. 启动 worker
cd server
bash start_celery_worker.sh

# 2. 在另一个终端触发任务（任意方式）
# - 创建反馈
# - 执行聚类
# - 上传截图识别

# 3. 检查日志文件
tail -f logs/fba_error.log
tail -f logs/fba_access.log

# 4. 停止 worker
# Ctrl+C 或 kill <PID>
```

### 预期结果

✅ **成功标志：**
- `logs/fba_access.log` 文件存在且有内容
- `logs/fba_error.log` 文件存在
- 任务的 `log.info()` 日志能在 `fba_access.log` 中找到
- 任务的 `log.error()` 日志能在 `fba_error.log` 中找到

❌ **失败标志：**
- `logs/` 目录为空
- 日志文件不存在
- 任务日志只在控制台显示，文件中没有

## 技术细节

### 为什么要检查 `sys.argv`？

```python
if 'worker' in sys.argv:
```

因为 `celery.py` 会被多个进程导入：
- **worker 进程**：`celery -A backend.app.task.celery worker ...`
- **beat 进程**：`celery -A backend.app.task.celery beat ...`
- **flower 进程**：`celery -A backend.app.task.celery flower ...`
- **FastAPI 进程**：导入 `celery_app` 用于发送任务

只有 worker 进程需要文件日志，其他进程：
- **beat**：有自己的日志配置（`supervisor/fba_celery_beat.conf`）
- **flower**：有自己的日志配置（`supervisor/fba_celery_flower.conf`）
- **FastAPI**：已通过 `backend/main.py` 配置过日志

### 日志级别过滤

`backend/common/log.py` 中的配置：

```python
# 标准输出文件（INFO/DEBUG）
logger.add(
    str(log_access_file),
    level=settings.LOG_FILE_ACCESS_LEVEL,
    filter=lambda record: record['level'].no <= 25,  # <= INFO
    ...
)

# 标准错误文件（WARNING/ERROR/CRITICAL）
logger.add(
    str(log_error_file),
    level=settings.LOG_FILE_ERROR_LEVEL,
    filter=lambda record: record['level'].no >= 30,  # >= WARNING
    ...
)
```

这样可以快速定位错误：
- 正常流程看 `fba_access.log`
- 排查问题看 `fba_error.log`

## 注意事项

1. **不要使用 `print()`**
   - ❌ `print('something')`
   - ✅ `log.info('something')`

2. **确保虚拟环境正确**
   ```bash
   cd server && source .venv/Scripts/activate
   ```

3. **Windows 环境**
   - 使用 Git Bash 执行 `.sh` 脚本
   - 或使用 `start_celery_worker.bat`/`start_celery_worker.ps1`

4. **生产环境**
   - 使用 supervisor 管理 Celery 进程
   - 日志会自动写入 `logs/` 目录
   - 定期清理过期日志（已配置 7 天自动清理）

## 相关文件

- `backend/app/task/celery.py` - Celery 应用初始化
- `backend/common/log.py` - 日志配置
- `backend/test_celery_logging.sh` - 日志测试脚本
- `server/start_celery_worker.sh` - Worker 启动脚本
- `docs/development/logging-best-practices.md` - 日志最佳实践

## 日志最佳实践

参考用户规则中的 "日志打印规范"：

- ✅ **记录失败**，不记录成功
- ✅ 所有 `except` 块都要记录，包含完整上下文
- ✅ 外部服务调用失败都有日志
- ✅ 关键业务节点记录（批量操作、定时任务、状态变更）
- ❌ 不要在正常流程记录 INFO（成功不需要庆祝）
- ❌ 不要在循环中滥用日志
- ❌ 不要记录敏感信息（密码、Token、API Key）

详细指南：`docs/development/logging-best-practices.md`
