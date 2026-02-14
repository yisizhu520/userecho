# 火山引擎配置示例

## 📋 快速配置清单

### 1. 获取 API Key 和 Endpoint

**访问火山引擎控制台**：[https://console.volcengine.com](https://console.volcengine.com)

1. 开通"豆包大模型"服务
2. 创建推理服务，选择支持视觉的模型：
   - **推荐**：`doubao-vision-pro-32k`（同时支持图像和文本）
   - 备选：`doubao-pro-32k`
3. 获取 **Endpoint ID**（格式：`ep-20241221xxx-xxxxx`）
4. 获取 **API Key**（在"API 密钥管理"页面）

---

### 2. 配置环境变量

编辑 `server/backend/.env`：

```bash
# ==================== 火山引擎配置 ====================

# API Key（必填）
VOLCENGINE_API_KEY=your-volcengine-api-key-here

# Chat Endpoint（必填）
# 用于截图识别和对话生成
VOLCENGINE_CHAT_ENDPOINT=ep-20241221xxx-xxxxx

# Vision Endpoint（可选）
# 如果不配置，会自动使用 CHAT_ENDPOINT
VOLCENGINE_VISION_ENDPOINT=

# Embedding Endpoint（可选）
# 用于文本聚类，不配置则使用其他 Provider
VOLCENGINE_EMBEDDING_ENDPOINT=

# 默认 AI Provider（必填）
AI_DEFAULT_PROVIDER=volcengine
```

---

### 3. 重启服务

```bash
cd server
source .venv/Scripts/activate
uvicorn backend.main:app --reload
```

---

### 4. 验证配置

#### 方法 A：使用测试脚本

```bash
cd server
python backend/scripts/test_ai_providers.py volcengine
```

#### 方法 B：在产品中测试

1. 登录 UserEcho
2. 进入"反馈管理" → "截图上传"
3. 上传一张微信/小红书截图
4. 查看 AI 是否正确识别平台和内容

---

## ⚙️ 配置说明

### VOLCENGINE_CHAT_ENDPOINT vs VOLCENGINE_VISION_ENDPOINT

**区别：**
- `CHAT_ENDPOINT`：用于普通对话和多模态（图像+文本）
- `VISION_ENDPOINT`：专门用于图像识别（可选）

**推荐配置：**

```bash
# 方案 1：只配置 CHAT_ENDPOINT（推荐）
VOLCENGINE_CHAT_ENDPOINT=ep-xxx  # 使用支持视觉的模型
VOLCENGINE_VISION_ENDPOINT=      # 留空，自动使用 CHAT_ENDPOINT

# 方案 2：分离配置（精细控制）
VOLCENGINE_CHAT_ENDPOINT=ep-xxx  # 普通对话模型
VOLCENGINE_VISION_ENDPOINT=ep-yyy  # 视觉专用模型
```

**优先级规则：**
1. 如果配置了 `VISION_ENDPOINT`，优先使用
2. 如果没有 `VISION_ENDPOINT`，回退到 `CHAT_ENDPOINT`
3. 如果都没有，降级到其他 Provider（OpenAI/GLM/DeepSeek）

---

## 🎯 使用场景

### 截图智能识别

**功能**：自动识别用户上传的反馈截图，提取：
- 平台类型（微信/小红书/App Store...）
- 用户昵称
- 反馈内容
- 反馈类型（Bug/需求/投诉）

**使用的 Endpoint**：`VOLCENGINE_VISION_ENDPOINT` 或 `VOLCENGINE_CHAT_ENDPOINT`

### 反馈摘要生成

**功能**：为长反馈生成简短摘要

**使用的 Endpoint**：`VOLCENGINE_CHAT_ENDPOINT`

### 文本聚类

**功能**：将相似反馈聚类，发现共性问题

**使用的 Endpoint**：`VOLCENGINE_EMBEDDING_ENDPOINT`（如果配置）

---

## 💰 成本估算

**火山引擎定价（2025年参考）：**
- Text 输入：¥0.003/千token
- Image 输入：按等效 token 计算（约 500-1000 token/图）
- 输出：¥0.006/千token

**单次截图识别成本：**
- 图像输入：约 700 token × ¥0.003 = ¥0.002
- 文本输出：约 200 token × ¥0.006 = ¥0.001
- **总计**：约 ¥0.003/次（不到 1 分钱）

**月度成本估算：**
- 每天处理 100 张截图 × 30 天 = 3000 次
- 月成本：3000 × ¥0.003 = **¥9**

**对比：**
- OpenAI GPT-4o：约 ¥0.02/次（贵 6 倍）
- 智谱 GLM-4V：约 ¥0.015/次（贵 5 倍）
- DeepSeek：暂不支持图像识别

---

## 🔗 相关文档

- [火山引擎详细配置指南](./volcengine-vision-setup.md)
- [多 Provider 配置对比](./configuration.md)
- [截图识别 PRD](../../design/wechat-feedback-collect.md)
- [截图识别技术实现](../../design/screenshot-recognition-implementation.md)
