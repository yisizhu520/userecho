# 批量截图识别功能文档

## 功能概述

批量截图识别功能允许用户一次性上传多张反馈截图（最多 50 张），通过预设配置后自动识别并创建反馈，无需逐个审核。

## 使用场景

1. **批量导入社交媒体反馈**：从微信、小红书等平台收集了大量用户反馈截图
2. **快速录入**：需要快速批量录入，无需逐个审核内容
3. **统一来源**：所有反馈来源和目标看板相同，可统一配置

## 技术架构

### 整体流程

```
步骤1：前端并发上传截图到 OSS
    ↓ 用户选择图片（支持拖拽）
    ↓ 前端并发直传到阿里云 OSS
    ↓ 收集所有 CDN URL
    
步骤2：配置默认信息
    ↓ 目标看板（必选）
    ↓ 来源类型：内部客户 / 外部用户
    ↓ 平台/用户名（根据类型）
    
步骤3：创建批量任务
    ↓ 后端创建批量任务记录
    ↓ Celery 异步处理队列
    
步骤4：AI 批量识别
    ↓ 并发识别所有截图内容
    ↓ 提取：反馈内容 + 用户名 + 平台
    ↓ 使用预设配置 + AI 识别结果
    
步骤5：自动创建反馈
    ✓ 高置信度：直接创建
    ✓ 低置信度：标记待审核（待实现）
```

### 关键技术点

#### 1. 前端直传 OSS

**优势**：
- 减轻后端压力
- 提高上传速度（并发上传）
- 节省后端带宽

**实现**：
```typescript
// 并发上传所有文件
const uploadPromises = fileList.value.map(async (fileItem) => {
  const url = await uploadScreenshot(fileItem.originFileObj as File)
  uploadedUrls.value.push(url)
  uploadedCount.value++
  uploadProgress.value = Math.round((uploadedCount.value / fileList.value.length) * 100)
  return url
})

await Promise.all(uploadPromises)
```

#### 2. 批量任务框架

**数据库表**：
- `batch_jobs`: 批量任务主表
- `batch_task_items`: 任务项明细表

**状态流转**：
```
pending → processing → completed/failed/cancelled
```

**进度追踪**：
- 前端每 2 秒轮询任务进度
- 实时显示：总数、已完成、处理中、失败

#### 3. AI 识别 + 预设配置

**配置优先级**：
```python
# 反馈内容：使用 AI 识别结果
content = ai_result.get("description", "")

# 用户名：AI 识别 > 预设默认值
user_name = ai_user_name or default_user_name or "匿名用户"

# 平台：AI 识别 > 预设平台
platform = ai_platform or source_platform
```

## API 接口

### 1. 批量截图识别

**接口**: `POST /api/v1/app/batch/feedbacks/screenshot-batch-upload`

**请求体**:
```json
{
  "image_urls": [
    "https://cdn.example.com/screenshot1.png",
    "https://cdn.example.com/screenshot2.png"
  ],
  "board_id": "board_xxx",
  "author_type": "external",
  "source_platform": "wechat",
  "default_user_name": "微信用户"
}
```

**响应**:
```json
{
  "code": 0,
  "msg": "success",
  "data": {
    "batch_id": "batch_xxx",
    "celery_task_id": "task_xxx",
    "total_count": 20
  }
}
```

### 2. 查询批量任务进度

**接口**: `GET /api/v1/app/batch/jobs/{batch_id}`

**响应**:
```json
{
  "code": 0,
  "data": {
    "batch_id": "batch_xxx",
    "task_type": "screenshot_recognition",
    "name": "批量截图识别 2024-01-26 14:30",
    "status": "processing",
    "total_count": 20,
    "pending_count": 5,
    "processing_count": 3,
    "completed_count": 10,
    "failed_count": 2,
    "progress": 60.0,
    "created_time": "2024-01-26T14:30:00",
    "started_time": "2024-01-26T14:30:05"
  }
}
```

### 3. 取消批量任务

**接口**: `DELETE /api/v1/app/batch/jobs/{batch_id}`

**响应**:
```json
{
  "code": 0,
  "msg": "success"
}
```

## 前端实现

### 页面路由

- 路径: `/app/feedback/screenshot-batch`
- 组件: `screenshot-batch-upload.vue`

### 入口

反馈列表工具栏 → "批量截图" 按钮

### 核心组件

```vue
<template>
  <!-- 步骤 1: 上传截图 -->
  <a-upload
    multiple
    :max-count="50"
    accept="image/png,image/jpeg,image/jpg,image/webp"
    :before-upload="handleBeforeUpload"
  />

  <!-- 步骤 2: 配置信息 -->
  <a-form>
    <a-form-item label="目标看板" required />
    <a-form-item label="来源类型" required />
    <a-form-item label="来源平台" required />
  </a-form>

  <!-- 步骤 3: 批量识别中 -->
  <a-progress type="circle" :percent="batchProgress" />

  <!-- 步骤 4: 完成 -->
  <a-statistic-group>
    <a-statistic title="总计" :value="total" />
    <a-statistic title="成功" :value="success" />
    <a-statistic title="失败" :value="failed" />
  </a-statistic-group>
</template>
```

### 状态管理

```typescript
type UploadStatus = 'idle' | 'uploading' | 'configuring' | 'processing' | 'success' | 'error'
```

## 后端实现

### 批量任务处理器

**文件**: `server/backend/app/batch/handler/screenshot_recognition.py`

**核心逻辑**:
```python
async def process(self, task_item: BatchTaskItem, db: AsyncSession) -> dict:
    # 1. 获取输入数据
    image_url = task_item.input_data["image_url"]
    board_id = task_item.input_data.get("board_id")
    author_type = task_item.input_data.get("author_type", "external")

    # 2. 调用 AI 识别
    result = await ai_client.analyze_screenshot(image_url)
    ai_content = result.get("description", "")
    ai_user_name = result.get("user_name", "")

    # 3. 构建反馈数据（AI 识别 + 预设配置）
    feedback_data = {
        "content": ai_content,
        "board_id": board_id,
        # ...
    }

    # 4. 根据来源类型设置字段
    if author_type == "customer":
        feedback_data["customer_name"] = ai_user_name or default_customer_name
    else:
        feedback_data["anonymous_author"] = ai_user_name or default_user_name

    # 5. 创建反馈
    feedback = Feedback(**feedback_data)
    db.add(feedback)
```

### Celery 任务

**异步执行**: 批量任务通过 Celery 异步处理，避免阻塞 HTTP 请求

**并发控制**: 使用批量任务框架自动管理并发和重试

## 与单个截图识别的区别

| 特性 | 单个识别 | 批量识别 |
|------|----------|----------|
| **数量** | 1 张 | 最多 50 张 |
| **上传方式** | 前端直传 | 前端并发直传 |
| **人工审核** | ✅ 必须审核 | ❌ 无需审核 |
| **配置方式** | 逐个配置 | 统一预设配置 |
| **处理方式** | 实时处理 | 异步批量处理 |
| **使用场景** | 精细化录入 | 快速批量导入 |

## 待优化功能

### 第一阶段优化

- [ ] 增加 `is_pending_review` 字段标记低置信度反馈
- [ ] 筛选器增加"待审核"选项
- [ ] 批量编辑功能

### 第二阶段优化

- [ ] 批量任务列表页面（查看历史批量任务）
- [ ] 任务详情页面（查看每个任务项的识别结果）
- [ ] 失败任务重试功能
- [ ] WebSocket 实时推送进度（替代轮询）

## 使用限制

1. **数量限制**: 最多 50 张截图/次
2. **文件格式**: PNG, JPG, JPEG, WEBP
3. **文件大小**: 单张最大 10MB
4. **并发限制**: 批量任务同时执行数量受 Celery worker 限制

## 积分消耗

- **操作类型**: `screenshot`
- **消耗数量**: 1 积分/张
- **记录位置**: `credits_transactions` 表
- **关联数据**: 反馈 ID + 批量任务 ID

## 监控与日志

### 关键日志

```python
# 任务开始
log.info(f"Starting screenshot recognition batch: {batch_job.id} ({batch_job.total_count} items)")

# 单个识别
log.info(f"Analyzing screenshot: {image_url}")

# 任务完成
log.info(f"Completed screenshot recognition batch: {batch_job.id} (success={completed}, failed={failed})")
```

### 错误处理

- 单个任务失败不影响其他任务
- 失败任务自动重试（最多 3 次）
- 记录失败原因到 `error_message` 字段

## 测试清单

### 功能测试

- [ ] 上传单张截图
- [ ] 上传 50 张截图（边界值）
- [ ] 上传 51 张截图（应拒绝）
- [ ] 上传不支持的格式（应提示错误）
- [ ] 上传超大文件（>10MB，应提示错误）
- [ ] 取消上传任务
- [ ] 内部客户模式
- [ ] 外部用户模式
- [ ] 查看批量任务进度
- [ ] 批量任务完成后跳转反馈列表

### 性能测试

- [ ] 并发上传速度测试
- [ ] 批量识别速度测试（10张、50张）
- [ ] Celery worker 负载测试

### 异常测试

- [ ] 上传失败重试
- [ ] AI 识别超时处理
- [ ] 数据库写入失败回滚
- [ ] 网络中断后恢复

## 常见问题

### Q: 批量识别失败后如何重试？

A: 目前版本不支持重试，需要重新上传。第二阶段将支持失败任务单独重试。

### Q: 如何查看批量任务的详细结果？

A: 目前只能在反馈列表中筛选。第二阶段将增加批量任务详情页面。

### Q: AI 识别的用户名不准确怎么办？

A: 可以在反馈列表中手动编辑反馈的用户名字段。

### Q: 批量识别消耗多少积分？

A: 1 积分/张截图，与单个识别相同。

## 更新日志

### v1.0.0 (2024-01-26)

- ✅ 前端并发直传到 OSS
- ✅ 批量任务框架集成
- ✅ 预设配置（看板、来源类型、平台）
- ✅ 实时进度追踪
- ✅ 任务取消功能
- ✅ 成功率统计展示
