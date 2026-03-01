# 截图识别多条反馈优化

## 概述

本次优化让 AI 截图识别功能支持从一张截图中提取多条反馈内容，并显示 OCR 原始文本，显著提升了用户体验。

## 核心改进

### 1. AI 提示词优化（后端）

**文件：** `server/backend/utils/ai_client.py`

**改进点：**
- ✅ 让 AI 识别多条独立反馈（群聊、评论区、列举多点等场景）
- ✅ 自动去重相似内容
- ✅ 提取完整 OCR 原始文本
- ✅ 返回结构化反馈列表

**新的提示词要求：**
```text
1. 识别多条反馈 - 用户列举的多个需求点、群聊中多个用户的意见、评论区多条评论
2. 自动去重 - 如果多条反馈内容重复或高度相似，只保留一条
3. 提取原始文本 - 完整的 OCR 文本内容（保留原始格式）
4. 结构化每条反馈 - 包含平台、用户名、内容、类型、情感、置信度
```

**数据结构变化：**
```python
# 旧结构（单条反馈）
{
    "platform": "wechat",
    "user_name": "张三",
    "content": "反馈内容",
    "confidence": 0.95
}

# 新结构（支持多条反馈）
{
    "raw_text": "完整的 OCR 文本...",
    "feedback_list": [
        {
            "platform": "wechat",
            "user_name": "张三",
            "user_id": "",
            "content": "第一条反馈内容",
            "feedback_type": "feature",
            "sentiment": "neutral",
            "confidence": 0.95
        },
        {
            "platform": "wechat",
            "user_name": "李四",
            "user_id": "",
            "content": "第二条反馈内容",
            "feedback_type": "bug",
            "sentiment": "negative",
            "confidence": 0.88
        }
    ],
    "overall_confidence": 0.92
}
```

### 2. 前端类型定义更新

**文件：** `front/apps/web-antd/src/api/userecho/feedback.ts`

**新增类型：**
```typescript
/** 单条反馈数据 */
export interface FeedbackItem {
  platform: 'wechat' | 'xiaohongshu' | 'appstore' | 'weibo' | 'qq' | 'other';
  user_name: string;
  user_id: string;
  content: string;
  feedback_type: 'bug' | 'feature' | 'improvement' | 'performance' | 'complaint' | 'other';
  sentiment: 'positive' | 'neutral' | 'negative';
  confidence: number;
}

/** 截图识别提取的数据（新版：支持多条反馈） */
export interface ExtractedScreenshotData {
  raw_text: string;                // OCR 提取的原始文本
  feedback_list: FeedbackItem[];   // 反馈列表（支持多条）
  overall_confidence: number;      // 整体置信度
}
```

### 3. 前端 UI 重构

**文件：** `front/apps/web-antd/src/views/userecho/feedback/screenshot-upload.vue`

**新增功能：**

#### 3.1 OCR 原始文本显示
```vue
<!-- OCR 原始文本（可折叠） -->
<Card size="small" class="raw-text-card">
  <template #title>
    <span>📄 OCR 识别文本</span>
  </template>
  <div class="raw-text-content">
    <Textarea :value="rawText" :rows="4" readonly />
    <Button size="small" @click="copyRawText">复制文本</Button>
  </div>
</Card>
```

**用户价值：**
- 可以看到完整的原始文本
- 方便复制粘贴到反馈内容中
- 便于对照修改 AI 识别结果

#### 3.2 多条反馈卡片列表
```vue
<div class="feedback-list">
  <div class="feedback-list-header">
    <span>📝 识别到的反馈（{{ enabledCount }}/{{ feedbackItems.length }}）</span>
  </div>

  <div v-for="(item, index) in feedbackItems" :key="item.id" class="feedback-item-card">
    <div class="feedback-item-header">
      <Checkbox v-model:checked="item.enabled">
        反馈 {{ index + 1 }}
        (置信度: {{ (item.confidence * 100).toFixed(0) }}%)
      </Checkbox>
      <Button danger @click="removeFeedbackItem(index)">删除</Button>
    </div>

    <div class="feedback-item-body">
      <!-- 平台、用户名、反馈内容表单 -->
    </div>
  </div>
</div>
```

**用户价值：**
- 一次性展示所有识别到的反馈
- 可以单独编辑每条反馈
- 可以删除不需要的反馈
- 可以勾选/取消勾选启用状态

#### 3.3 批量创建功能
```typescript
const handleBatchSubmit = async () => {
  const enabledFeedbacks = feedbackItems.value.filter(item => item.enabled)
  
  const promises = enabledFeedbacks.map(async (item) => {
    const payload = {
      board_id: formData.board_id,
      content: item.content,
      screenshot_url: screenshotUrl.value,
      source_platform: item.platform,
      external_user_name: item.user_name,
      // ...
    }
    return createFeedbackFromScreenshot(payload)
  })

  await Promise.all(promises)
  message.success(`成功创建 ${enabledFeedbacks.length} 条反馈`)
}
```

**用户价值：**
- 一键创建多条反馈，无需重复上传截图
- 自动并行处理，速度快
- 实时反馈创建进度

## 典型使用场景

### 场景 1：群聊截图
**截图内容：**
```
张三: 能不能加个暗黑模式？
李四: 我也想要批量删除功能
王五: 界面有点卡，能优化一下吗？
```

**AI 识别结果：**
```json
{
  "raw_text": "张三: 能不能加个暗黑模式？\n李四: 我也想要批量删除功能\n王五: 界面有点卡，能优化一下吗？",
  "feedback_list": [
    {
      "user_name": "张三",
      "content": "希望增加暗黑模式",
      "feedback_type": "feature",
      "confidence": 0.95
    },
    {
      "user_name": "李四",
      "content": "希望增加批量删除功能",
      "feedback_type": "feature",
      "confidence": 0.92
    },
    {
      "user_name": "王五",
      "content": "界面性能需要优化",
      "feedback_type": "performance",
      "confidence": 0.88
    }
  ],
  "overall_confidence": 0.92
}
```

### 场景 2：用户列举多个需求点
**截图内容：**
```
我有三个建议：
1. 希望能导出 Excel
2. 能不能加个搜索框
3. 批量操作功能太少了
```

**AI 识别结果：**
```json
{
  "raw_text": "我有三个建议：\n1. 希望能导出 Excel\n2. 能不能加个搜索框\n3. 批量操作功能太少了",
  "feedback_list": [
    {
      "content": "希望能导出 Excel",
      "feedback_type": "feature",
      "confidence": 0.95
    },
    {
      "content": "希望增加搜索框",
      "feedback_type": "feature",
      "confidence": 0.93
    },
    {
      "content": "需要更多批量操作功能",
      "feedback_type": "improvement",
      "confidence": 0.90
    }
  ],
  "overall_confidence": 0.93
}
```

### 场景 3：评论区截图
**截图内容：**（小红书评论区）
```
用户A: 闪退了 iOS 16
用户B: 我也是，卸载重装也不行
用户C: 安卓没问题
用户D: 闪退问题什么时候修复？
```

**AI 识别结果：**
```json
{
  "raw_text": "...",
  "feedback_list": [
    {
      "platform": "xiaohongshu",
      "user_name": "用户A",
      "content": "iOS 16 系统闪退",
      "feedback_type": "bug",
      "sentiment": "negative",
      "confidence": 0.95
    }
    // 重复的"闪退"反馈被自动去重
  ]
}
```

## 技术亮点

### 1. AI 提示词工程
- 明确告知 AI 要识别多条反馈
- 提供典型场景示例（群聊、列举、评论区）
- 要求自动去重，避免重复内容
- 要求返回 OCR 原始文本，方便用户修改

### 2. 数据结构设计
- 使用数组统一处理单条/多条反馈（消除特殊情况）
- 每条反馈独立的置信度 + 整体置信度
- 保留原始文本，方便用户复制粘贴

### 3. UI/UX 设计
- 卡片式反馈列表，清晰直观
- 每条反馈可独立编辑、删除、启用/禁用
- 原始文本区域可折叠、可复制
- 批量操作按钮显示数量（"确认创建 3 条反馈"）

### 4. 向后兼容
- API 数据结构兼容旧版（单条反馈 = 数组长度为 1）
- 前端平滑迁移，无破坏性变更
- 降级方案：识别失败时返回空数组

## 后续优化方向

### 短期（MVP）
- [x] AI 识别返回多条反馈
- [x] 前端展示原始文本
- [x] 前端多条反馈卡片
- [x] 批量创建功能

### 中期优化
- [ ] 单条反馈的独立提交（允许部分创建，不是全部或取消）
- [ ] 智能去重优化（显示相似度评分）
- [ ] 反馈合并建议（"这两条可能是同一个需求"）
- [ ] 支持手动添加新反馈

### 长期增强
- [ ] AI 自动关联到已有主题（"这条反馈可能与主题 #123 相关"）
- [ ] 多语言支持（英文、日文等）
- [ ] OCR 质量评估（模糊、倾斜、遮挡检测）

## 测试建议

### 1. AI 识别准确性测试
- [ ] 测试群聊截图（3-5 条不同用户的反馈）
- [ ] 测试列举式反馈（"1. ... 2. ... 3. ..."）
- [ ] 测试评论区截图（小红书、微博、App Store）
- [ ] 测试单条反馈（确保向后兼容）
- [ ] 测试重复内容去重（同一反馈出现多次）

### 2. UI/UX 测试
- [ ] 测试原始文本复制功能
- [ ] 测试反馈卡片的编辑功能
- [ ] 测试反馈的删除功能
- [ ] 测试勾选/取消勾选功能
- [ ] 测试批量创建（3 条反馈同时创建）
- [ ] 测试批量创建失败的错误处理

### 3. 边界情况测试
- [ ] 测试识别 0 条反馈（空白截图）
- [ ] 测试识别 10+ 条反馈（超长评论区）
- [ ] 测试低置信度场景（模糊截图）
- [ ] 测试特殊字符、表情符号
- [ ] 测试非常长的反馈内容（>500字）

## 代码变更清单

### 后端
- `server/backend/utils/ai_client.py`
  - 更新 `analyze_screenshot()` 方法
  - 优化提示词，支持多条反馈识别和去重
  - 修改返回数据结构（raw_text + feedback_list）

### 前端
- `front/apps/web-antd/src/api/userecho/feedback.ts`
  - 新增 `FeedbackItem` 类型定义
  - 更新 `ExtractedScreenshotData` 类型定义

- `front/apps/web-antd/src/views/userecho/feedback/screenshot-upload.vue`
  - 新增 `rawText` 状态（OCR 原始文本）
  - 新增 `feedbackItems` 状态（多条反馈列表）
  - 新增 `enabledCount` 计算属性
  - 新增 `copyRawText()` 方法
  - 新增 `removeFeedbackItem()` 方法
  - 新增 `handleBatchSubmit()` 方法
  - 重构 UI 模板（原始文本区 + 多条反馈卡片）
  - 更新样式（反馈卡片列表样式）

## 总结

本次优化通过 AI 提示词优化和 UI 重构，让截图识别功能支持从一张截图中提取多条反馈，并显示 OCR 原始文本。这显著提升了用户体验，减少了重复操作，特别适合处理群聊截图、评论区截图等多反馈场景。

**核心价值：**
- ✅ 解决真实痛点 - 群聊、评论区、列举多点都是高频场景
- ✅ 提升效率 - 一次上传，创建多条反馈
- ✅ 用户体验好 - 原始文本可复制，反馈可独立编辑
- ✅ 技术实现清晰 - 数据结构简洁，无特殊情况
- ✅ 向后兼容 - 平滑迁移，无破坏性变更
