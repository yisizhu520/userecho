# 产品需求文档 (PRD)：截图智能识别与反馈采集模块

**项目名称：** 回响 (UserEcho)

**文档版本：** V1.0 (MVP)

**模块：** 截图智能识别与反馈采集

**最后更新：** 2025-01-15

---

## 1. 产品概述

### 1.1 背景

中小企业大量真实反馈散落在微信聊天、小红书评论、App Store 评价中。手动整理成本极高，信息容易丢失。

### 1.2 MVP 目标

**核心价值：将截图转化为结构化反馈数据，降低反馈录入成本。**

- ✅ 极简上传：支持剪贴板粘贴、拖拽、选择文件
- ✅ AI 提取：自动识别平台、昵称、反馈内容
- ✅ 快速入库：左图右文审核，一键保存

**不在 MVP 范围：**
- ❌ 自动关联客户（V2）
- ❌ 自动生成回复话术（V2）
- ❌ 闭环状态通知（V2）

---

## 2. 核心用户场景

### 场景 A：私域客服
```
客服小李正在微信和客户聊天：
客户：你们产品闪退了 [发送截图]

客服操作：
1. 截图微信对话
2. 在 UserEcho 按 Ctrl+V 粘贴
3. AI 自动识别平台和内容
4. 点击"确认创建"
5. 完成 ✅
```

### 场景 B：运营人员
```
运营在小红书发现用户吐槽：
1. 截图评论区
2. 拖拽到上传区
3. AI 提取昵称和内容
4. 手动补充标签
5. 保存为反馈
```

### 场景 C：批量导入
```
PM 收集了 20 张 App Store 评论截图：
1. 批量选择文件上传
2. AI 并发处理
3. 逐个审核确认
4. 批量入库
```

---

## 3. 功能需求

### 3.1 截图上传入口

**交互方式：**
- 剪贴板粘贴（Ctrl+V）
- 拖拽文件到上传区
- 点击选择本地文件
- 支持单张和多张（最多 10 张）

**支持格式：** PNG, JPG, JPEG, WEBP

**文件大小：** 单张不超过 10MB

---

### 3.2 AI 智能识别

**输入：** 截图文件

**输出：** 结构化 JSON
```json
{
  "platform": "wechat",           // 平台类型
  "platform_confidence": 0.95,    // 识别置信度
  "user_name": "小王",             // 用户昵称
  "user_id": "",                   // 平台 ID（如果有）
  "content": "产品闪退了，iOS 16.3", // 提取的核心内容
  "feedback_type": "bug",          // bug | feature | complaint | other
  "sentiment": "negative"          // positive | neutral | negative
}
```

**支持的平台：**
- 微信（个人/企业微信）
- 小红书
- App Store
- 微博
- 其他（通用 OCR）

**AI 调用：**
- 默认模型：火山引擎（豆包 Vision Pro）
- 备用模型：GPT-4o / GLM-4V / DeepSeek
- 超时时间：30 秒
- 失败处理：自动降级到其他 Provider，最终返回空表单

---

### 3.3 审核与编辑界面

**布局：** 左右分栏

**左侧：** 截图预览
- 支持缩放、旋转
- 显示识别状态（识别中/成功/失败）

**右侧：** 提取信息表单
```
[平台] ⬇️ 微信
[昵称] 小王
[内容] (富文本编辑框，可修改)
产品闪退了，iOS 16.3

[标签] + 添加标签
[类型] ⬇️ Bug

[操作按钮]
[取消]  [重新识别]  [确认创建]
```

**字段可编辑性：**
- ✅ 平台类型（下拉选择）
- ✅ 昵称（文本输入）
- ✅ 内容（富文本编辑）
- ✅ 标签（多选）
- ✅ 类型（单选）

---

### 3.4 反馈保存

**保存内容：**
- 反馈内容（必填）
- 截图 URL（OSS 存储）
- 来源平台（必填）
- 用户昵称（可选）
- 平台用户 ID（可选）
- 反馈类型（自动识别 + 可修改）
- 提交者（当前登录用户）
- 创建时间

**保存后跳转：**
- 默认：回到反馈列表
- 可选：继续上传下一张

---

## 4. 数据模型

### 4.1 数据库变更

**扩展 `feedback` 表：**

```sql
-- 新增字段
ALTER TABLE feedback 
    -- 允许 customer_id 为 NULL（MVP 阶段不做客户关联）
    ALTER COLUMN customer_id DROP NOT NULL,
    
    -- 来源信息
    ADD COLUMN source_type VARCHAR(50) DEFAULT 'manual',  -- manual | screenshot | api
    ADD COLUMN source_platform VARCHAR(50),               -- wechat | xiaohongshu | appstore | weibo | other
    ADD COLUMN source_user_name VARCHAR(255),             -- 平台昵称
    ADD COLUMN source_user_id VARCHAR(255),               -- 平台用户 ID
    
    -- 截图
    ADD COLUMN screenshot_url TEXT,                       -- OSS 地址
    
    -- 提交者
    ADD COLUMN submitter_id INT REFERENCES "user"(id),    -- 内部员工 ID
    
    -- AI 元数据
    ADD COLUMN ai_confidence DECIMAL(3,2);                -- AI 识别置信度

-- 索引
CREATE INDEX idx_feedback_source_platform ON feedback(source_platform);
CREATE INDEX idx_feedback_submitter ON feedback(submitter_id);
CREATE INDEX idx_feedback_unlinked ON feedback(tenant_id, customer_id) WHERE customer_id IS NULL;
```

### 4.2 数据示例

**场景 A：微信截图反馈（暂不关联客户）**
```json
{
  "id": 12345,
  "tenant_id": 1,
  "customer_id": null,                // MVP 阶段允许为空
  "content": "产品闪退了，iOS 16.3",
  "source_type": "screenshot",
  "source_platform": "wechat",
  "source_user_name": "小王",
  "source_user_id": "",
  "screenshot_url": "https://oss.example.com/screenshots/abc123.jpg",
  "submitter_id": 10,                 // 客服小李
  "ai_confidence": 0.95,
  "created_at": "2025-01-15T10:30:00Z"
}
```

**场景 B：用户在产品内直接提交（原有逻辑）**
```json
{
  "id": 12346,
  "tenant_id": 1,
  "customer_id": 123,                 // 已登录用户
  "content": "希望增加导出功能",
  "source_type": "manual",
  "source_platform": null,
  "screenshot_url": null,
  "submitter_id": null,               // 用户自己提交
  "created_at": "2025-01-15T11:00:00Z"
}
```

---

## 5. 技术方案

### 5.1 前端（Vue3 + Ant Design Vue）

**关键组件：**

```
/views/feedback/screenshot-upload.vue
  ├─ ScreenshotUploader.vue       # 上传区域
  ├─ ScreenshotPreview.vue        # 左侧预览
  └─ FeedbackForm.vue             # 右侧表单
```

**技术要点：**
- 使用 `ClipboardEvent` 监听粘贴
- `FileReader` 读取图片预览
- `FormData` 上传文件到 OSS
- WebSocket 推送 AI 识别进度

---

### 5.2 后端（FastAPI + PostgreSQL）

**API 端点：**

```python
# 1. 上传截图并 AI 识别
POST /api/v1/feedback/screenshot/analyze
Request: multipart/form-data
  - file: 图片文件
  - tenant_id: int
Response:
{
  "screenshot_url": "https://...",
  "extracted": {
    "platform": "wechat",
    "user_name": "小王",
    "content": "产品闪退了",
    "feedback_type": "bug",
    "confidence": 0.95
  }
}

# 2. 创建反馈
POST /api/v1/feedback
Request:
{
  "content": "产品闪退了，iOS 16.3",
  "source_type": "screenshot",
  "source_platform": "wechat",
  "source_user_name": "小王",
  "screenshot_url": "https://...",
  "customer_id": null,  // MVP 阶段允许为 null
  "submitter_id": 10
}

# 3. 批量上传（V1.1 支持）
POST /api/v1/feedback/screenshot/batch
Request: multipart/form-data
  - files[]: 多个图片文件
Response: 
{
  "results": [
    { "id": 1, "status": "success", "screenshot_url": "..." },
    { "id": 2, "status": "processing", "task_id": "..." }
  ]
}
```

**AI 识别逻辑：**

```python
async def analyze_screenshot(image_file: UploadFile) -> ExtractedData:
    # 1. 上传到 OSS
    screenshot_url = await upload_to_oss(image_file)
    
    # 2. 调用多模态大模型
    prompt = """
    分析这张截图，提取以下信息：
    1. 来源平台（微信/小红书/App Store/微博/其他）
    2. 用户昵称
    3. 反馈内容（提取核心问题，去除寒暄）
    4. 反馈类型（Bug/功能需求/投诉/其他）
    
    返回 JSON 格式。
    """
    
    # 使用配置的 AI Provider（默认火山引擎）
    result = await ai_client.analyze_screenshot(
        image_url=screenshot_url
    )
    
    return ExtractedData(**result)
```

**配置说明（使用火山引擎）：**

```bash
# server/backend/.env
VOLCENGINE_API_KEY=your-volcengine-api-key
VOLCENGINE_CHAT_ENDPOINT=ep-20241221xxx-xxxxx  # 支持视觉的模型
AI_DEFAULT_PROVIDER=volcengine
```

**详细配置指南**：参见 `docs/guides/ai-provider/volcengine-vision-setup.md`

---

### 5.3 存储方案

**截图存储：**
- 使用阿里云 OSS / AWS S3
- 路径规则：`/screenshots/{tenant_id}/{year}/{month}/{uuid}.jpg`
- 访问权限：私有（通过签名 URL 访问）
- 过期策略：180 天后自动转冷存储

**数据库：**
- PostgreSQL 13+
- 使用 Alembic 管理 migration

---

## 6. UI/UX 设计

### 6.1 上传状态

```
[上传区域]
┌──────────────────────────┐
│  📋 粘贴截图 (Ctrl+V)    │
│  📁 拖拽文件到这里        │
│  [或点击选择文件]        │
└──────────────────────────┘

上传中：
┌──────────────────────────┐
│  ⬆️ 上传中... 60%        │
│  [取消]                  │
└──────────────────────────┘

识别中：
┌──────────────────────────┐
│  🔍 AI 识别中...         │
│  [━━━━━━━━━━━━] 80%     │
└──────────────────────────┘
```

### 6.2 审核界面

```
┌─────────────────────────────────────────────────────┐
│  截图智能识别              [关闭]                    │
├───────────────┬─────────────────────────────────────┤
│               │  [平台] ⬇️ 微信 ✓                   │
│               │                                     │
│   [截图预览]  │  [昵称] 小王                        │
│               │                                     │
│   [微信对话]  │  [内容] *必填                       │
│   小王：      │  ┌─────────────────────────────┐   │
│   产品闪退了  │  │ 产品闪退了，iOS 16.3        │   │
│   ...         │  │ iPhone 14 Pro              │   │
│               │  └─────────────────────────────┘   │
│   [缩放 100%] │                                     │
│   [← →]       │  [类型] ⬇️ Bug                     │
│               │  [标签] + 添加标签                  │
│               │                                     │
│               │  AI 识别置信度: 95% ✓               │
│               │                                     │
│               │  ──────────────────────────────     │
│               │  [取消]  [重新识别]  [确认创建]    │
└───────────────┴─────────────────────────────────────┘
```

### 6.3 成功提示

```
✅ 反馈创建成功

[查看反馈详情]  [继续上传截图]
```

---

## 7. 非功能需求

### 7.1 性能要求

- 单张图片上传：< 3 秒
- AI 识别响应：< 10 秒
- 并发上传支持：10 张/批次
- 前端预览加载：< 1 秒

### 7.2 安全要求

- 上传文件类型校验（防止上传恶意文件）
- 文件大小限制（10MB）
- OSS 私有访问（签名 URL，7 天有效期）
- 提交者身份验证（JWT Token）

### 7.3 错误处理

| 错误场景 | 处理方式 |
|---------|---------|
| 上传失败 | 自动重试 3 次，失败提示用户 |
| AI 识别超时 | 降级为通用 OCR |
| AI 识别失败 | 返回空表单，用户手动填写 |
| 网络中断 | 本地缓存，恢复后继续 |

---

## 8. 验收标准

### 8.1 功能验收

- [ ] 支持剪贴板粘贴上传
- [ ] 支持拖拽文件上传
- [ ] 支持点击选择文件上传
- [ ] AI 能识别微信、小红书、App Store 截图
- [ ] AI 提取准确率 > 80%（人工抽样 50 张）
- [ ] 用户可手动编辑所有字段
- [ ] 保存后截图可正常查看
- [ ] 反馈列表显示截图来源标识

### 8.2 性能验收

- [ ] 单张上传 + 识别 < 15 秒
- [ ] 前端预览加载 < 1 秒
- [ ] 批量上传 10 张不阻塞页面

### 8.3 兼容性验收

- [ ] Chrome 90+
- [ ] Edge 90+
- [ ] Safari 14+
- [ ] Firefox 88+

---

## 9. 后续迭代计划（V2）

### V1.1 功能增强
- 批量上传优化（队列管理）
- 识别历史记录（缓存常见昵称）
- 更多平台支持（抖音、知乎）

### V1.2 客户关联
- 基于昵称智能推荐客户
- 手动关联客户功能
- 批量认领未关联反馈

### V1.3 闭环管理
- 自动生成回复话术
- 反馈状态变更通知
- 提醒客服去平台回复

---

## 10. 附录

### 10.1 火山引擎配置（推荐）

**快速配置（3 步）：**

1. **获取火山引擎凭证**
   - 访问：[https://console.volcengine.com](https://console.volcengine.com)
   - 开通"豆包大模型"服务
   - 创建推理服务，选择模型：`doubao-vision-pro-32k`（推荐）
   - 记录 API Key 和 Endpoint ID

2. **配置环境变量**（编辑 `server/backend/.env`）
   ```bash
   VOLCENGINE_API_KEY=your-api-key-here
   VOLCENGINE_CHAT_ENDPOINT=ep-20241221xxx-xxxxx
   AI_DEFAULT_PROVIDER=volcengine
   ```

3. **验证配置**
   ```bash
   cd server
   python check_volcengine_config.py
   ```

**详细配置指南**：`docs/guides/ai-provider/volcengine-quickstart.md`

---

### 10.2 AI Prompt 模板

```text
你是一个专业的反馈分析助手。分析这张社交媒体截图，提取以下信息：

1. **平台类型** (platform)
   - 观察 UI 特征（气泡样式、导航栏、Logo）
   - 可能值：wechat | xiaohongshu | appstore | weibo | other

2. **用户昵称** (user_name)
   - 提取发表反馈的用户昵称
   - 如果无法识别，返回空字符串

3. **用户 ID** (user_id)
   - 如果截图中有用户 ID（如小红书的 @id），提取
   - 如果没有，返回空字符串

4. **反馈内容** (content)
   - 提取核心反馈内容
   - 去除寒暄语、表情符号
   - 保留关键信息（版本号、设备型号、错误描述）

5. **反馈类型** (feedback_type)
   - bug: 功能异常、闪退、卡顿
   - feature: 功能需求、建议
   - complaint: 投诉、差评
   - other: 其他

6. **情感倾向** (sentiment)
   - positive: 正面评价
   - neutral: 中性反馈
   - negative: 负面反馈

以 JSON 格式返回，不要包含任何其他文字。

示例输出：
{
  "platform": "wechat",
  "user_name": "小王",
  "user_id": "",
  "content": "产品闪退了，iOS 16.3，iPhone 14 Pro",
  "feedback_type": "bug",
  "sentiment": "negative"
}
```

### 10.3 数据库 Migration

```sql
-- Migration: add_screenshot_fields_to_feedback
-- Date: 2025-01-15

BEGIN;

-- 1. 允许 customer_id 为 NULL
ALTER TABLE feedback 
    ALTER COLUMN customer_id DROP NOT NULL;

-- 2. 添加新字段
ALTER TABLE feedback 
    ADD COLUMN source_type VARCHAR(50) DEFAULT 'manual',
    ADD COLUMN source_platform VARCHAR(50),
    ADD COLUMN source_user_name VARCHAR(255),
    ADD COLUMN source_user_id VARCHAR(255),
    ADD COLUMN screenshot_url TEXT,
    ADD COLUMN submitter_id INT,
    ADD COLUMN ai_confidence DECIMAL(3,2);

-- 3. 添加外键约束
ALTER TABLE feedback 
    ADD CONSTRAINT fk_feedback_submitter 
    FOREIGN KEY (submitter_id) REFERENCES "user"(id) 
    ON DELETE SET NULL;

-- 4. 添加索引
CREATE INDEX idx_feedback_source_platform ON feedback(source_platform);
CREATE INDEX idx_feedback_submitter ON feedback(submitter_id);
CREATE INDEX idx_feedback_unlinked ON feedback(tenant_id, customer_id) 
    WHERE customer_id IS NULL;

-- 5. 添加注释
COMMENT ON COLUMN feedback.source_type IS '反馈来源: manual | screenshot | api';
COMMENT ON COLUMN feedback.source_platform IS '社交平台: wechat | xiaohongshu | appstore | weibo | other';
COMMENT ON COLUMN feedback.source_user_name IS '平台用户昵称';
COMMENT ON COLUMN feedback.source_user_id IS '平台用户 ID';
COMMENT ON COLUMN feedback.screenshot_url IS '截图 OSS 地址';
COMMENT ON COLUMN feedback.submitter_id IS '内部提交者（员工）ID';
COMMENT ON COLUMN feedback.ai_confidence IS 'AI 识别置信度 (0.00-1.00)';

COMMIT;
```

---

**文档结束**
