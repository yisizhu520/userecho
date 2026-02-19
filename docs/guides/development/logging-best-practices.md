# 日志打印最佳实践指南

## Linus 的日志哲学

> "Talk is cheap. Show me the code." - 但日志是代码说话的方式。

**核心原则：**
1. **记录事实，不记录废话** - 每条日志必须有实际价值
2. **在失败点记录，不在成功路径上喊口号** - 成功是常态，不需要庆祝
3. **记录上下文，不记录"出错了"** - `log.error("error")` 是垃圾

---

## 一、快速开始

### 导入日志

```python
from backend.common.log import log
```

**就这一行。** 不要 `import logging`，不要自己创建 logger，不要搞花里胡哨的东西。

### 基本使用

```python
# ✅ 好的实践
log.info(f'Starting Excel import for tenant: {tenant_id}')
log.error(f'Failed to create feedback: {e}')

# ❌ 垃圾代码
log.info('operation started')  # 什么操作？
log.error('error occurred')    # 什么错误？
```

---

## 二、日志级别使用指南

### DEBUG - 调试信息

**用途：** 帮助开发者理解代码执行流程，生产环境通常关闭

**场景：**
- 函数参数和返回值
- 中间计算结果
- 条件分支判断

```python
# ✅ 合理使用
log.debug(f'接口摘要：[{summary}]')
log.debug(f'请求参数：{args}')
log.debug(f'Calculated similarity score: {score:.4f}')

# ❌ 滥用
log.debug('function called')  # 废话
log.debug(f'{x=}')           # Python 3.8+ 的 f-string 调试够了
```

**原则：** DEBUG 日志可以多，但不能是废话。

---

### INFO - 关键节点

**用途：** 记录业务流程的关键节点，生产环境应该看到

**场景：**
- 服务启动/停止
- 重要业务操作开始/结束
- 外部服务调用（API、数据库、消息队列）
- 定时任务执行

```python
# ✅ 好的实践
log.info(f'{ctx.ip: <15} | {method: <8} | {code!s: <6} | {path} | {elapsed:.3f}ms')
log.info(f'DEEPSEEK AI client initialized')
log.info(f'Starting batch clustering for {len(feedbacks)} feedbacks')
log.info(f'Default provider unavailable, switched to {self.current_provider}')

# ❌ 垃圾日志
log.info('processing data')          # 什么数据？
log.info('user logged in')           # 哪个用户？
log.info('operation completed')      # 什么操作？耗时多久？
```

**格式建议：**
```python
# 操作开始：[动作] for [对象]
log.info(f'Starting Excel import for tenant: {tenant_id}')

# 操作完成：[动作] completed: [关键指标]
log.info(f'Clustering completed: {len(clusters)} clusters, {processing_time:.2f}s')

# 状态变化：[对象] [状态变化] [原因]
log.info(f'Topic {topic_id} archived by {user_id}')
```

---

### WARNING - 可恢复的异常情况

**用途：** 系统遇到问题但可以继续运行

**场景：**
- 降级处理（fallback）
- 配置缺失使用默认值
- 资源接近限制
- 可重试的失败

```python
# ✅ 好的实践
log.warning(f'Failed to initialize {provider_name} client: {e}')
log.warning('VOLCENGINE_EMBEDDING_ENDPOINT not configured')
log.warning(f'Rate limit approaching: {current_count}/{limit}')
log.warning(f'Retry {attempt}/{max_retries} for API call to {endpoint}')

# ❌ 误用
log.warning('something wrong')       # 什么事情？
log.warning(f'user not found: {id}') # 这应该是业务逻辑，不是警告
```

**原则：** WARNING 意味着需要人类注意，但不需要立即处理。

---

### ERROR - 操作失败

**用途：** 记录导致功能失败的错误

**场景：**
- 数据库操作失败
- 外部 API 调用失败（重试后仍失败）
- 数据验证失败
- 业务逻辑异常

```python
# ✅ 好的实践
log.error(f'Failed to create feedback: {e}')
log.error(f'Failed to update topic status: {e}')
log.error(f'Database connection failed after {retries} retries: {e}')
log.error(f'请求异常: {msg}')

# ❌ 垃圾日志
log.error('error')                   # 什么错误？
log.error(f'{e}')                    # 缺少上下文
```

**最佳实践：**

```python
# ✅ 标准模式：在 except 块中记录并重新抛出
try:
    result = await some_operation(tenant_id, data)
    return result
except Exception as e:
    log.error(f'Failed to [操作描述] for tenant {tenant_id}: {e}')
    raise  # 重新抛出，让上层处理

# ❌ 不要吞掉异常
try:
    result = await some_operation()
except Exception as e:
    log.error(f'Error: {e}')
    return None  # 静默失败，调用者不知道出错了

# ❌ 不要重复记录
try:
    await create_feedback()  # 内部已经 log.error
except Exception as e:
    log.error(f'Failed: {e}')  # 重复了
    raise
```

---

### CRITICAL - 系统级故障

**用途：** 记录可能导致系统不可用的严重问题

**场景：**
- 数据库连接池耗尽
- 内存溢出
- 关键配置错误
- 依赖服务完全不可用

```python
# ✅ 合理使用
log.critical('All database connections exhausted')
log.critical(f'Redis connection failed: {e}. System may be unstable')
log.critical('JWT secret key not configured. Authentication disabled!')

# ❌ 滥用
log.critical('user password incorrect')  # 这不是系统级问题
```

**原则：** CRITICAL 应该触发告警，立即唤醒运维人员。慎用。

---

## 三、实战场景

### 场景 1：Service 层 - 业务逻辑

```python
class FeedbackService:
    async def create_with_ai_processing(
        self,
        db: AsyncSession,
        tenant_id: str,
        data: FeedbackCreate,
        generate_summary: bool = True,
    ):
        """创建反馈（自动生成 AI 摘要）"""
        try:
            # ❌ 不要在正常流程记录
            # log.info('Creating feedback...')
            
            # ✅ 只在关键节点记录
            ai_summary = None
            if generate_summary and data.content:
                # 外部服务调用 - 值得记录
                log.debug(f'Generating AI summary for feedback content: {len(data.content)} chars')
                ai_summary = await ai_client.generate_summary(data.content, max_length=20)
            
            feedback = await crud_feedback.create(
                db=db,
                tenant_id=tenant_id,
                id=uuid4_str(),
                customer_id=data.customer_id,
                content=data.content,
                ai_summary=ai_summary
            )
            
            # ❌ 不要记录成功 - 成功是预期行为
            # log.info(f'Feedback {feedback.id} created successfully')
            
            return feedback

        except Exception as e:
            # ✅ 失败才需要记录
            log.error(f'Failed to create feedback for tenant {tenant_id}: {e}')
            raise
```

---

### 场景 2：外部服务调用 - API/数据库

```python
class AIClient:
    async def get_embedding(self, text: str, max_retries: int = 2) -> list[float] | None:
        """获取文本 embedding"""
        
        for attempt in range(max_retries + 1):
            try:
                # ✅ 记录关键参数
                log.debug(f'Getting embedding (attempt {attempt + 1}/{max_retries + 1}): '
                         f'provider={self.current_provider}, text_len={len(text)}')
                
                response = await self.clients[self.current_provider].embeddings.create(
                    model=embedding_model,
                    input=text
                )
                
                # ❌ 不记录成功
                # log.info('Embedding generated successfully')
                
                return response.data[0].embedding
                
            except Exception as e:
                if attempt < max_retries:
                    # ✅ WARNING：可恢复的错误
                    log.warning(f'Embedding request failed (attempt {attempt + 1}/{max_retries + 1}): {e}')
                    await asyncio.sleep(1)
                else:
                    # ✅ ERROR：最终失败
                    log.error(f'Failed to get embedding after {max_retries + 1} attempts: {e}')
                    return None
```

---

### 场景 3：批量操作 - 导入/导出

```python
async def import_from_excel(
    self,
    db: AsyncSession,
    tenant_id: str,
    file: UploadFile,
) -> dict:
    """从 Excel 导入反馈"""
    
    # ✅ 记录批量操作开始
    log.info(f'Starting Excel import for tenant: {tenant_id}, file: {file.filename}')
    
    try:
        # 验证文件
        if not file.filename:
            # ✅ 业务验证失败 - WARNING
            log.warning(f'Invalid file upload: empty filename for tenant {tenant_id}')
            return {'status': 'error', 'message': '文件名不能为空'}
        
        # 读取 Excel
        try:
            df = pd.read_excel(file.file)
            # ✅ 记录关键指标
            log.info(f'Excel file loaded: {len(df)} rows, columns: {list(df.columns)}')
        except Exception as e:
            log.error(f'Failed to read Excel file {file.filename}: {e}')
            return {'status': 'error', 'message': f'文件读取失败: {str(e)}'}
        
        # 批量创建
        success_count = 0
        error_count = 0
        
        for idx, row in df.iterrows():
            try:
                feedback = await self.create_feedback(db, tenant_id, row)
                success_count += 1
            except Exception as e:
                error_count += 1
                # ✅ 单条失败 - DEBUG 就够了
                log.debug(f'Failed to import row {idx}: {e}')
        
        # ✅ 记录最终结果
        log.info(f'Excel import completed for tenant {tenant_id}: '
                f'success={success_count}, failed={error_count}, total={len(df)}')
        
        return {
            'status': 'success',
            'success_count': success_count,
            'error_count': error_count,
        }
        
    except Exception as e:
        log.error(f'Excel import failed for tenant {tenant_id}: {e}')
        raise
```

---

### 场景 4：定时任务/后台任务

```python
async def cluster_feedbacks_task():
    """定时聚类反馈任务"""
    
    # ✅ 任务开始
    log.info('Starting feedback clustering task')
    start_time = time.time()
    
    try:
        tenants = await get_all_tenants()
        
        for tenant_id in tenants:
            try:
                feedbacks = await get_unclustered_feedbacks(tenant_id)
                
                if not feedbacks:
                    # ✅ DEBUG：跳过空租户
                    log.debug(f'No unclustered feedbacks for tenant {tenant_id}, skipping')
                    continue
                
                # ✅ INFO：处理进度
                log.info(f'Clustering {len(feedbacks)} feedbacks for tenant {tenant_id}')
                
                clusters = await cluster_feedbacks(feedbacks)
                
                # ✅ INFO：结果统计
                log.info(f'Tenant {tenant_id} clustering completed: {len(clusters)} clusters created')
                
            except Exception as e:
                # ✅ ERROR：单个租户失败，继续处理其他租户
                log.error(f'Failed to cluster feedbacks for tenant {tenant_id}: {e}')
                continue
        
        # ✅ 任务完成
        elapsed = time.time() - start_time
        log.info(f'Feedback clustering task completed: {len(tenants)} tenants, {elapsed:.2f}s')
        
    except Exception as e:
        # ✅ CRITICAL：整个任务失败
        log.critical(f'Feedback clustering task crashed: {e}')
        raise
```

---

## 四、常见错误与反模式

### ❌ 反模式 1：过度记录

```python
# ❌ 垃圾代码
def process_feedback(feedback_id: str):
    log.info('Starting process_feedback')
    log.info(f'Getting feedback {feedback_id}')
    feedback = get_feedback(feedback_id)
    log.info('Feedback retrieved')
    log.info('Validating feedback')
    if not feedback.content:
        log.info('Feedback content is empty')
        return False
    log.info('Feedback validated')
    log.info('Processing content')
    result = process_content(feedback.content)
    log.info('Content processed')
    return result

# ✅ 正确写法
def process_feedback(feedback_id: str):
    try:
        feedback = get_feedback(feedback_id)
        
        if not feedback.content:
            log.warning(f'Feedback {feedback_id} has empty content, skipping')
            return False
        
        return process_content(feedback.content)
        
    except Exception as e:
        log.error(f'Failed to process feedback {feedback_id}: {e}')
        raise
```

**原则：** 如果一个函数有 5 条以上的日志，重新审视你的设计。

---

### ❌ 反模式 2：缺少上下文

```python
# ❌ 垃圾日志
log.error(f'Error: {e}')
log.error('Operation failed')
log.warning('Invalid data')

# ✅ 好日志
log.error(f'Failed to update topic {topic_id} status to {new_status}: {e}')
log.error(f'Database operation failed for tenant {tenant_id}, query: {query_type}')
log.warning(f'Invalid feedback data from source {source}: missing required field "content"')
```

**原则：** 日志应该回答 5W：Who、What、When（自动时间戳）、Where、Why

---

### ❌ 反模式 3：记录敏感信息

```python
# ❌ 安全隐患
log.info(f'User login: username={username}, password={password}')
log.debug(f'JWT token: {token}')
log.info(f'API key: {api_key}')

# ✅ 正确做法
log.info(f'User login attempt: username={username}')
log.debug(f'JWT token length: {len(token)}')
log.info(f'API key configured: {api_key[:8]}***')
```

**敏感信息包括：**
- 密码、Token、API Key
- 身份证号、手机号、邮箱
- 信用卡信息
- 完整的用户输入（可能包含 XSS、SQL 注入）

---

### ❌ 反模式 4：在循环中记录

```python
# ❌ 日志洪水
for feedback in feedbacks:
    log.info(f'Processing feedback {feedback.id}')
    process(feedback)

# ✅ 批量记录
log.info(f'Processing {len(feedbacks)} feedbacks')
for feedback in feedbacks:
    process(feedback)
log.info(f'Completed processing {len(feedbacks)} feedbacks')

# ✅ 如果需要详细日志，用 DEBUG
for feedback in feedbacks:
    log.debug(f'Processing feedback {feedback.id}')
    process(feedback)
```

---

### ❌ 反模式 5：使用 print() 代替日志

```python
# ❌ 永远不要这样做
print('Starting process...')
print(f'Error: {e}')

# ✅ 使用日志
log.info('Starting process...')
log.error(f'Process failed: {e}')
```

**原因：**
- print() 不支持日志级别
- print() 不会写入日志文件
- print() 没有时间戳
- print() 没有 request_id

---

## 五、性能考虑

### 延迟求值

```python
# ❌ 浪费性能
log.debug(f'User data: {json.dumps(huge_object, indent=2)}')  # 即使 DEBUG 关闭也会执行

# ✅ 使用条件判断
if log.level('DEBUG').no >= log._core.min_level:
    log.debug(f'User data: {json.dumps(huge_object, indent=2)}')

# ✅ 或者简单判断
if settings.LOG_STD_LEVEL == 'DEBUG':
    log.debug(f'Detailed data: {expensive_operation()}')
```

### 避免过多字符串拼接

```python
# ❌ 每次都拼接
log.debug('value1: ' + str(value1) + ', value2: ' + str(value2))

# ✅ 使用 f-string
log.debug(f'value1: {value1}, value2: {value2}')
```

---

## 六、Linus 式日志清单

在提交代码前，检查这些点：

- [ ] **每条日志都有实际价值** - 能帮助定位问题或理解系统行为
- [ ] **ERROR 日志包含完整上下文** - Who、What、When、Where、Why
- [ ] **没有在正常流程记录 INFO** - 成功不需要庆祝
- [ ] **没有在循环中滥用日志** - 批量操作批量记录
- [ ] **没有记录敏感信息** - 密码、Token、API Key 等
- [ ] **异常被记录并重新抛出** - 不吞掉异常，不重复记录
- [ ] **日志级别使用正确** - DEBUG/INFO/WARNING/ERROR/CRITICAL
- [ ] **没有使用 print()** - 永远使用 log

---

## 七、配置说明

项目日志配置位于 `backend/core/conf.py`：

```python
# 日志格式（自动包含时间、级别、request_id）
LOG_FORMAT: str = (
    '<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</> | '
    '<lvl>{level: <8}</> | '
    '<cyan>{request_id}</> | '
    '<lvl>{message}</>'
)

# 控制台日志级别
LOG_STD_LEVEL: str = 'INFO'  # 开发: DEBUG, 生产: INFO

# 文件日志级别
LOG_FILE_ACCESS_LEVEL: str = 'INFO'   # 访问日志
LOG_FILE_ERROR_LEVEL: str = 'ERROR'   # 错误日志
```

**日志文件：**
- `log/fba_access.log` - INFO 及以下级别
- `log/fba_error.log` - ERROR 及以上级别
- 自动按日切割，保留 7 天

**Request ID：**
- 每个请求自动分配唯一 ID
- 自动注入到所有日志中
- 用于追踪单个请求的完整生命周期

---

## 八、总结：Linus 的建议

> "Keep it simple, stupid." - KISS 原则

1. **记录失败，不记录成功** - 失败才需要调查
2. **记录决策，不记录执行** - "为什么这样做"比"做了什么"重要
3. **记录异常，不记录正常** - 异常才需要关注
4. **记录上下文，不记录事实** - "谁在什么情况下遇到什么问题"
5. **少即是多** - 一条有用的日志胜过十条废话

**记住：日志不是给你自己看的，是给凌晨 3 点被叫醒的运维看的。**

---

## 参考资料

- Loguru 官方文档：https://loguru.readthedocs.io/
- Python Logging 最佳实践：https://docs.python-guide.org/writing/logging/
- 项目日志配置：`backend/common/log.py`
