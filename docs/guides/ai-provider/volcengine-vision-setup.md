# 火山引擎截图识别配置指南

## 🎯 使用场景

在**截图智能识别功能**中，火山引擎用于分析用户上传的反馈截图，自动提取：
- 平台类型（微信/小红书/App Store...）
- 用户昵称
- 反馈内容
- 反馈类型（Bug/需求/投诉）
- 情感倾向

---

## 📋 配置步骤

### 方案 A：使用 Chat Endpoint（推荐）

**适用场景**：你的 Chat 模型已支持多模态（如豆包 Pro）

```bash
# .env 配置
VOLCENGINE_API_KEY=your-volcengine-api-key
VOLCENGINE_CHAT_ENDPOINT=ep-20241221xxx-xxxxx  # 你的 Chat Endpoint
AI_DEFAULT_PROVIDER=volcengine
```

**说明**：
- 系统会自动使用 `VOLCENGINE_CHAT_ENDPOINT` 进行图像识别
- 无需额外配置 `VOLCENGINE_VISION_ENDPOINT`
- 确保你的 Endpoint 使用的是**支持视觉的模型**（如豆包 Pro、doubao-vision-pro-32k）

---

### 方案 B：使用独立 Vision Endpoint（可选）

**适用场景**：你有专门的视觉模型 Endpoint，想与 Chat 分离

```bash
# .env 配置
VOLCENGINE_API_KEY=your-volcengine-api-key
VOLCENGINE_CHAT_ENDPOINT=ep-20241221xxx-xxxxx       # 普通对话
VOLCENGINE_VISION_ENDPOINT=ep-20241221yyy-yyyyy     # 图像识别（优先级更高）
AI_DEFAULT_PROVIDER=volcengine
```

**说明**：
- 如果同时配置了 `VISION_ENDPOINT` 和 `CHAT_ENDPOINT`，优先使用 `VISION_ENDPOINT`
- 适合需要精细控制不同任务使用不同模型的场景

---

## 🚀 火山引擎 Endpoint 创建

### 1. 访问火山引擎控制台

访问：[https://console.volcengine.com](https://console.volcengine.com)

### 2. 开通服务

1. 进入"豆包大模型"或"机器学习平台"
2. 点击"推理服务" → "创建推理服务"

### 3. 选择支持视觉的模型

**推荐模型（2025年）：**
- `doubao-vision-pro-32k`：豆包视觉专业版（推荐）
- `doubao-pro-32k`：豆包 Pro（同时支持文本和图像）
- `glm-4v`：智谱 GLM-4V（如果火山代理）

### 4. 获取 Endpoint ID

创建成功后，复制 **Endpoint ID**（格式：`ep-20241221xxx-xxxxx`）

### 5. 获取 API Key

1. 进入"API 密钥管理"
2. 创建或复制现有 API Key（环境变量名：`ARK_API_KEY` 或 `VOLCENGINE_API_KEY`）

---

## ✅ 验证配置

### 方法 1：使用测试脚本

```bash
cd server
source .venv/Scripts/activate
python backend/scripts/test_ai_providers.py volcengine
```

### 方法 2：在产品中测试

1. 登录 UserEcho 系统
2. 进入"反馈管理" → "截图上传"
3. 上传一张微信/小红书的截图
4. 查看 AI 是否正确识别

---

## 🔍 常见问题

### Q1: 提示"VOLCENGINE_VISION_ENDPOINT not configured"

**原因**：未配置任何火山引擎 Endpoint

**解决**：至少配置以下之一：
```bash
VOLCENGINE_CHAT_ENDPOINT=ep-xxx  # 推荐
# 或
VOLCENGINE_VISION_ENDPOINT=ep-yyy
```

### Q2: 提示"API Key 错误"

**原因**：API Key 不正确或未激活

**解决**：
1. 检查 `.env` 中的 `VOLCENGINE_API_KEY` 是否正确
2. 确认 API Key 在火山引擎控制台是否已激活
3. 确认 API Key 有调用推理服务的权限

### Q3: 识别结果不准确

**可能原因**：
1. 使用的模型不支持视觉（如纯文本模型）
2. 图片质量过低（模糊、分辨率不足）
3. 截图内容过于复杂

**解决**：
1. 切换到支持视觉的模型（如 `doubao-vision-pro-32k`）
2. 提供清晰的截图
3. 尝试降级到其他 Provider（系统会自动 fallback）

### Q4: 成本优化建议

**成本对比（2025年参考价）：**
- 火山引擎（豆包）：¥0.003/千token（图像按等效 token 计算）
- OpenAI GPT-4o：$0.005/千token
- 智谱 GLM-4V：¥0.015/千次调用

**优化策略**：
1. 使用火山引擎作为主力（性价比高）
2. 配置 OpenAI 作为备用（质量保障）
3. 设置合理的 `max_tokens` 限制（当前 500）

---

## 📊 监控和日志

### 查看识别日志

```bash
# 在后端日志中搜索
grep "analyze_screenshot" backend/logs/server.log

# 典型输出
[INFO] Analyzing screenshot with AI: https://...
[INFO] Screenshot analysis completed: confidence=0.95
```

### 监控成功率

```sql
-- 查看识别置信度分布
SELECT 
    CASE 
        WHEN ai_confidence >= 0.9 THEN '高(>=0.9)'
        WHEN ai_confidence >= 0.7 THEN '中(0.7-0.9)'
        ELSE '低(<0.7)'
    END as confidence_level,
    COUNT(*) as count
FROM feedback
WHERE source_type = 'screenshot'
GROUP BY confidence_level;
```

---

## 🔗 相关文档

- [火山引擎总体配置](./volcengine-endpoint-setup.md)
- [多 Provider 配置](./configuration.md)
- [截图识别实现文档](../../design/screenshot-recognition-implementation.md)
- [PRD: 截图智能识别](../../design/wechat-feedback-collect.md)
