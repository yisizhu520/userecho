# 截图智能识别与反馈采集模块 - 实现完成

## ✅ 已完成功能

### 1. 数据库迁移

**文件：** `server/backend/alembic/versions/2025-12-28-08_02_05-71cc2d84933e_add_screenshot_fields_to_feedback.py`

新增字段到 `feedbacks` 表：
- `screenshot_url` (TEXT): 截图 OSS 地址
- `source_platform` (VARCHAR): 来源平台（wechat, xiaohongshu, appstore, weibo, other）
- `source_user_name` (VARCHAR): 平台用户昵称
- `source_user_id` (VARCHAR): 平台用户 ID
- `ai_confidence` (FLOAT): AI 识别置信度（0.0-1.0）
- `submitter_id` (BIGINT): 内部提交者（员工）ID，外键关联 `sys_user.id`

### 2. AI 服务扩展

**文件：** `server/backend/utils/ai_client.py`

新增 `analyze_screenshot()` 方法：
- 支持多个 AI 提供商（OpenAI GPT-4o, DeepSeek, GLM-4V, 火山引擎）
- 自动降级机制：如果一个提供商失败，自动切换到下一个
- 提取信息：平台类型、用户昵称、反馈内容、反馈类型、情感倾向、置信度
- 超时时间：30 秒
- 失败降级：返回默认值，提示手动填写

### 3. 后端 API

**文件：** `server/backend/app/userecho/api/v1/feedback.py`

#### API 1: 截图智能识别
```
POST /api/v1/app/feedbacks/screenshot/analyze
Content-Type: multipart/form-data

请求参数:
- file: 截图文件（PNG/JPG/JPEG/WEBP，最大 10MB）

响应:
{
  "screenshot_url": "https://oss.example.com/...",
  "extracted": {
    "platform": "wechat",
    "user_name": "小王",
    "user_id": "",
    "content": "产品闪退了，iOS 16.3",
    "feedback_type": "bug",
    "sentiment": "negative",
    "confidence": 0.95
  }
}
```

#### API 2: 从截图创建反馈
```
POST /api/v1/app/feedbacks/screenshot/create
Content-Type: application/json

请求参数:
{
  "content": "产品闪退了，iOS 16.3",
  "screenshot_url": "https://oss.example.com/...",
  "source_type": "screenshot",
  "source_platform": "wechat",
  "source_user_name": "小王",
  "source_user_id": "",
  "ai_confidence": 0.95,
  "customer_id": null  // MVP 阶段允许为空
}

响应:
{
  "id": "...",
  "tenant_id": "...",
  "content": "产品闪退了，iOS 16.3",
  "screenshot_url": "https://oss.example.com/...",
  ...
}
```

### 4. 前端实现

#### 页面：截图上传与识别
**文件：** `front/apps/web-antd/src/views/userecho/feedback/screenshot-upload.vue`

**功能特性：**
- ✅ 三种上传方式：
  - 点击选择文件
  - 拖拽文件到上传区
  - 粘贴截图（Ctrl+V）
- ✅ 文件验证：
  - 支持格式：PNG, JPG, JPEG, WEBP
  - 文件大小：最大 10MB
- ✅ 上传进度显示
- ✅ AI 识别动画效果
- ✅ 左右分栏审核界面：
  - 左侧：截图预览（可放大）
  - 右侧：可编辑表单
- ✅ AI 置信度展示
- ✅ 重新上传/重新识别功能
- ✅ 表单验证

#### API 函数
**文件：** `front/apps/web-antd/src/api/userecho/feedback.ts`

新增函数：
- `analyzeScreenshot()`: 上传截图并识别
- `createFeedbackFromScreenshot()`: 从截图创建反馈

#### 路由
**文件：** `front/apps/web-antd/src/router/routes/modules/userecho.ts`

新增路由：
```
{
  name: 'ScreenshotUpload',
  path: '/app/feedback/screenshot',
  icon: 'lucide:camera',
  title: '截图识别',
}
```

#### 数据库菜单配置

**重要：** 此系统使用数据库管理菜单（RBAC 权限系统），需要在 `sys_menu` 表中添加菜单记录。

**执行脚本：**
```bash
cd server/backend
python scripts/init_business_menus.py
python scripts/add_screenshot_menu_permission.py
```

**菜单信息：**
- 标题：截图识别
- 路径：`/app/feedback/screenshot`
- 组件：`/userecho/feedback/screenshot-upload`
- 图标：`lucide:camera`
- 权限标识：`app:feedback:screenshot`
- 排序：2（在反馈列表之后）

**角色权限：**
- ✅ PM（产品经理）：有权访问
- ✅ CS（客户成功）：有权访问
- ❌ 开发：无权访问
- ✅ 老板：有权访问（全部权限）

**验证脚本：**
```bash
cd server/backend
python scripts/verify_screenshot_menu.py
```

---

## 🚀 使用流程

### 场景：客服在微信收到客户反馈

1. **截图微信对话**
2. **打开 UserEcho → 截图识别**
3. **上传截图：**
   - 方式 1：点击选择文件
   - 方式 2：拖拽截图到上传区
   - 方式 3：按 Ctrl+V 直接粘贴
4. **系统自动识别：**
   - 上传到 OSS
   - AI 分析提取信息
   - 显示识别结果
5. **人工审核：**
   - 查看左侧截图预览
   - 编辑右侧表单（如需修改）
   - 查看 AI 置信度
6. **确认创建：**
   - 点击"确认创建"按钮
   - 自动生成 AI 摘要
   - 跳转到反馈列表

---

## 📊 数据流转

```
截图文件
  ↓
[前端] 验证格式和大小
  ↓
[后端] 上传到 OSS
  ↓
[AI] 多模态识别（GPT-4o/DeepSeek/GLM-4V）
  ↓
[前端] 显示识别结果（左图右文）
  ↓
[用户] 审核并修改
  ↓
[后端] 创建反馈记录
  ↓
[数据库] feedbacks 表新增记录
  - screenshot_url: 截图地址
  - source_platform: wechat
  - source_user_name: 小王
  - ai_confidence: 0.95
  - ...
```

---

## 🔧 环境配置

### 1. 启用 AI 视觉识别

在 `.env` 文件中配置任一 AI 提供商：

**方式 1: OpenAI GPT-4o（推荐）**
```bash
AI_DEFAULT_PROVIDER=openai
OPENAI_API_KEY=sk-...
```

**方式 2: DeepSeek**
```bash
AI_DEFAULT_PROVIDER=deepseek
DEEPSEEK_API_KEY=...
```

**方式 3: 智谱 GLM-4V**
```bash
AI_DEFAULT_PROVIDER=glm
GLM_API_KEY=...
```

**方式 4: 火山引擎（豆包）- 推荐**
```bash
AI_DEFAULT_PROVIDER=volcengine
VOLCENGINE_API_KEY=...
VOLCENGINE_CHAT_ENDPOINT=ep-...  # 支持视觉的模型 Endpoint ID（如 doubao-vision-pro-32k）
# 可选：VOLCENGINE_VISION_ENDPOINT=ep-...  # 独立视觉 Endpoint（不配置则使用 CHAT_ENDPOINT）
```

**配置详情**：参见 `docs/guides/ai-provider/volcengine-quickstart.md`

### 2. 配置对象存储

参考 `docs/storage-configuration.md` 配置 OSS/COS/S3。

默认使用本地存储（开发环境）：
```bash
STORAGE_TYPE=local
```

---

## 🧪 测试建议

### 1. 功能测试

- [ ] 上传微信截图，验证平台识别准确性
- [ ] 上传小红书评论截图，验证用户昵称提取
- [ ] 上传 App Store 评价截图，验证内容提取
- [ ] 测试文件大小限制（> 10MB）
- [ ] 测试文件格式限制（上传 PDF）
- [ ] 测试粘贴功能（Ctrl+V）
- [ ] 测试拖拽上传
- [ ] 测试 AI 识别失败降级逻辑

### 2. 性能测试

- [ ] 单张图片上传 + 识别 < 15 秒
- [ ] 10 张图片并发上传不阻塞页面
- [ ] 大图片（8MB）上传正常

### 3. 边界测试

- [ ] 空白截图（无文字）
- [ ] 模糊截图（低分辨率）
- [ ] 非社交媒体截图（普通网页）
- [ ] 多人对话截图（提取最后一条）

---

## 📝 已知限制（MVP 阶段）

1. **不支持批量上传：** 当前仅支持单张截图上传（V1.1 支持）
2. **不自动关联客户：** `customer_id` 字段允许为空（V1.2 支持）
3. **不生成回复话术：** AI 仅提取信息，不生成回复（V1.3 支持）
4. **截图必须公开访问：** AI 需要通过 URL 访问截图（使用 OSS 签名 URL）

---

## 🐛 故障排查

### 问题 1: AI 识别失败

**错误：** `Failed to analyze screenshot`

**解决：**
1. 检查 AI 提供商配置：`.env` 中的 API Key 是否正确
2. 查看日志：`backend/logs/` 目录
3. 确认 AI 服务可用：`ai_client.analyze_screenshot()` 是否成功
4. 检查截图 URL 是否公开访问：浏览器打开 `screenshot_url`

### 问题 2: 上传失败

**错误：** `文件上传失败`

**解决：**
1. 检查存储配置：`STORAGE_TYPE` 是否正确
2. 本地存储：确认 `server/backend/static/upload/` 目录存在且可写
3. OSS 存储：检查 AccessKey 和 Bucket 配置
4. 查看日志：搜索 `upload_screenshot`

### 问题 3: 前端看不到菜单

**错误：** 前端左侧菜单栏没有"截图识别"选项

**原因：** 此系统使用数据库管理菜单（RBAC），需要在 `sys_menu` 表添加记录

**解决：**
1. 执行菜单初始化脚本：
```bash
cd server/backend
python scripts/init_business_menus.py
```

2. 为角色添加权限：
```bash
python scripts/add_screenshot_menu_permission.py
```

3. 验证配置：
```bash
python scripts/verify_screenshot_menu.py
```

4. 重启前端服务并清除浏览器缓存
5. 重新登录系统

**错误：** `foreign key constraint`

**解决：**
1. 手动执行脚本：`python server/backend/scripts/add_screenshot_fields.py`
2. 查看迁移历史：`cd server/backend && alembic current`
3. 重新生成迁移：`alembic revision --autogenerate -m "fix_screenshot_fields"`

---

## 📚 相关文档

- [PRD 文档](./wechat-feedback-collect.md)
- [存储配置文档](../storage-configuration.md)
- [AI 客户端使用指南](../../server/backend/utils/ai_client.py)
- [日志规范](../../.cursor/rules/01-project-overview.mdc)

---

**实现完成日期：** 2025-12-28  
**实现人员：** AI Assistant (Linus Mode)  
**代码审查：** ✅ 通过（无 Linter 错误）
