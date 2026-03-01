# 截图 URL 字段补充说明

## 问题

用户反馈：创建的多条反馈里，需要加上截图 URL 的数据。

## 分析

### 前端代码

前端在 `screenshot-upload.vue` 的批量提交函数中，**已经正确传入了** `screenshot_url`：

```typescript
const payload: ScreenshotFeedbackCreateParams = {
  board_id: formData.board_id,
  content: item.content,
  screenshot_url: screenshotUrl.value,  // ✅ 已传入
  source_type: 'screenshot',
  // ...
}
```

### 后端 API

后端在 `feedback.py` 的 `create_feedback_from_screenshot()` API 中，**已经正确保存了** `screenshot_url`：

```python
feedback = Feedback(
    # ...
    screenshot_url=data.screenshot_url,  # ✅ 已保存
    source_platform=data.source_platform,
    source_user_name=data.external_user_name,
    source_user_id=data.source_user_id,
    ai_confidence=data.ai_confidence,
    # ...
)
```

### 问题根源

虽然前端传入了，后端也保存了，但 **`FeedbackOut` schema 没有显式声明 `screenshot_url` 字段**，导致 API 返回时可能不包含这个字段。

虽然 `FeedbackOut` 使用了 `from_attributes=True` 可以自动从 ORM 提取字段，但为了确保字段始终返回，应该显式声明。

## 修复方案

在 `FeedbackOut` schema 中显式添加截图相关字段：

**文件：** `server/backend/app/userecho/schema/feedback.py`

```python
class FeedbackOut(FeedbackBase):
    """反馈输出模型"""

    # ... 其他字段
    
    # ✅ 新增：外部用户相关字段
    author_type: str = Field(default="customer", description="来源类型: customer=内部客户, external=外部用户")
    external_user_name: str | None = Field(None, description="外部用户名称")
    external_contact: str | None = Field(None, description="外部用户联系方式")
    
    # ✅ 新增：截图识别相关字段
    screenshot_url: str | None = Field(None, description="截图 URL（单张截图识别）")
    source_platform: str | None = Field(None, description="来源平台: wechat/xiaohongshu/appstore/weibo/other")
    source_user_name: str | None = Field(None, description="来源平台用户昵称")
    source_user_id: str | None = Field(None, description="来源平台用户 ID")
    ai_confidence: float | None = Field(None, description="AI 识别置信度 (0.00-1.00)")
    
    # ... 其他字段
```

## 修复效果

### 之前

```json
{
  "id": "xxx",
  "content": "反馈内容",
  "source": "screenshot",
  // ❌ 缺少 screenshot_url、source_platform 等字段
}
```

### 之后

```json
{
  "id": "xxx",
  "content": "反馈内容",
  "source": "screenshot",
  "author_type": "external",
  "external_user_name": "张三",
  "screenshot_url": "https://xxx.cos.ap-shanghai.myqcloud.com/screenshots/...",
  "source_platform": "wechat",
  "source_user_name": "张三",
  "ai_confidence": 0.95
}
```

## 完整的截图相关字段

现在 `FeedbackOut` 包含以下截图相关字段：

1. **基础字段**
   - `screenshot_url` - 截图 URL（单张）
   - `images_metadata` - 多张截图元数据

2. **来源信息**
   - `source_platform` - 来源平台（wechat/xiaohongshu/appstore/weibo/other）
   - `source_user_name` - 平台用户昵称
   - `source_user_id` - 平台用户 ID

3. **AI 识别**
   - `ai_confidence` - AI 识别置信度（0.00-1.00）
   - `ai_summary` - AI 生成摘要

4. **外部用户模式**
   - `author_type` - 来源类型（customer/external）
   - `external_user_name` - 外部用户名称
   - `external_contact` - 外部用户联系方式

## 验证步骤

1. ✅ 修复 schema（添加 `screenshot_url` 等字段）
2. ✅ 运行 `bash pre-commit.sh` - 代码质量检查通过
3. ✅ 测试创建反馈 API
4. ✅ 验证返回数据包含 `screenshot_url`

## 相关文档

- `docs/development/screenshot-multi-feedback-upgrade.md` - 截图识别多条反馈优化
- `docs/development/screenshot-multi-feedback-bugfix.md` - 错误修复文档
- `docs/development/screenshot-multi-feedback-complete-fix.md` - 完整修复记录
