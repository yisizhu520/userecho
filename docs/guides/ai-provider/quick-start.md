# AI Provider 配置快速指南

## 🚀 快速开始

### 1. 选择一个提供商

| 提供商 | 推荐度 | 理由 | Embedding | Chat |
|--------|-------|------|-----------|------|
| **DeepSeek** | ⭐⭐⭐⭐⭐ | 性价比最高，国内访问快 | ❌ | ✅ |
| **GLM (智谱)** | ⭐⭐⭐⭐ | 国内服务，中文优化 | ✅ | ✅ |
| **OpenAI** | ⭐⭐⭐ | 质量最高，但需国际支付 | ✅ | ✅ |
| **Volcengine** | ⭐⭐⭐ | 字节服务，配置复杂 | ✅ | ✅ |

> **重要**：DeepSeek 不支持 Embedding API，只能用于 Chat。如需完整功能，请配合其他提供商使用。

### 2. 配置环境变量

编辑 `server/backend/.env` 文件：

#### Option A: DeepSeek + OpenAI 组合（推荐）

```bash
# DeepSeek 用于 Chat（便宜），OpenAI 用于 Embedding
DEEPSEEK_API_KEY=sk-your-deepseek-key-here
OPENAI_API_KEY=sk-your-openai-key-here
AI_DEFAULT_PROVIDER=deepseek
```

**获取 API Key**: 
- DeepSeek: [https://platform.deepseek.com](https://platform.deepseek.com)
- OpenAI: [https://platform.openai.com](https://platform.openai.com)

> **说明**：DeepSeek 只支持 Chat，不支持 Embedding。系统会自动使用 OpenAI 进行 Embedding。

#### Option B: 智谱 GLM

```bash
GLM_API_KEY=your-glm-api-key-here
AI_DEFAULT_PROVIDER=glm
```

**获取 API Key**: [https://open.bigmodel.cn](https://open.bigmodel.cn)

#### Option C: OpenAI

```bash
OPENAI_API_KEY=sk-your-openai-key-here
AI_DEFAULT_PROVIDER=openai
```

**获取 API Key**: [https://platform.openai.com](https://platform.openai.com)

#### Option D: 火山引擎

```bash
VOLCENGINE_API_KEY=your-volcengine-api-key-here
VOLCENGINE_EMBEDDING_ENDPOINT=ep-20241221xxx-xxxxx
VOLCENGINE_CHAT_ENDPOINT=ep-20241221xxx-xxxxx
AI_DEFAULT_PROVIDER=volcengine
```

**获取配置**: [https://console.volcengine.com](https://console.volcengine.com)

### 3. 安装测试脚本依赖（可选）

测试脚本只需要两个轻量级包：

```bash
pip install openai python-dotenv
```

或使用 uv（推荐）：

```bash
cd server
uv add openai python-dotenv
```

### 4. 测试配置

**Linux/Mac:**
```bash
cd server/backend
./test_ai.sh
```

**Windows:**
```bash
cd server/backend
test_ai.bat
```

**或直接运行 Python 脚本:**
```bash
cd server/backend
python scripts/test_ai_providers.py
```

看到 `🎉 所有测试完成！` 就说明配置成功。

> 💡 **提示**：测试脚本是独立的，不依赖整个 backend 框架，只需要 `openai` 和 `python-dotenv` 两个包。

---

## 💡 高级配置

### 多提供商 + 自动降级

配置多个提供商，系统会在失败时自动切换：

```bash
# 主用 DeepSeek，备用 GLM
DEEPSEEK_API_KEY=sk-your-deepseek-key
GLM_API_KEY=your-glm-key
AI_DEFAULT_PROVIDER=deepseek
```

**降级流程**：DeepSeek → GLM → 降级方案（简单规则）

---

## 📊 价格对比

| 提供商 | Embedding (1M tokens) | Chat (1M tokens) |
|--------|----------------------|------------------|
| DeepSeek | ¥0.7 | ¥1.4 |
| GLM | ¥0.5 | ¥5 |
| OpenAI | ~¥0.14 | ~¥3.5 |

> 💰 **结论**: DeepSeek 综合性价比最高

---

## 🔧 常见问题

### Q: 如何知道配置成功了？

运行测试脚本，看到这些就说明 OK：

```
✅ 已初始化的提供商: ['deepseek']
✅ Embedding 成功
✅ 主题生成成功
✅ 摘要生成成功
```

### Q: 可以不配置 AI 吗？

可以。系统会使用降级方案（简单规则），但功能会受限：
- Embedding: 返回 None（聚类功能不可用）
- 主题生成: 使用关键词匹配
- 摘要生成: 简单截断

### Q: 配置了多个提供商，如何切换？

修改 `AI_DEFAULT_PROVIDER` 的值即可：

```bash
AI_DEFAULT_PROVIDER=glm  # 切换到智谱
```

### Q: 火山引擎的 Endpoint ID 怎么获取？

1. 登录火山引擎控制台
2. 进入"机器学习平台" → "推理服务"
3. 创建推理服务，获取 Endpoint ID（格式：`ep-20241221xxx-xxxxx`）

### Q: 测试失败怎么办？

1. **检查 API Key** 是否正确
2. **检查网络** 是否能访问提供商 API
3. **查看日志** 了解具体错误信息

---

## 📚 详细文档

- **完整配置指南**: [`docs/ai-provider-configuration.md`](./ai-provider-configuration.md)
- **更新日志**: [`docs/ai-provider-update-log.md`](./ai-provider-update-log.md)
- **测试说明**: [`server/backend/scripts/README.md`](../server/backend/scripts/README.md)

---

## 🎯 推荐方案

### 个人开发者（性价比优先）

```bash
# Chat 用 DeepSeek（便宜），Embedding 用 OpenAI
DEEPSEEK_API_KEY=sk-xxx
OPENAI_API_KEY=sk-xxx
AI_DEFAULT_PROVIDER=deepseek
```

### 国内企业（全国内服务）

```bash
# 全部使用 GLM（国内服务，全功能）
GLM_API_KEY=xxx
AI_DEFAULT_PROVIDER=glm
```

### 国际企业（质量优先）

```bash
# 全部使用 OpenAI（质量最高）
OPENAI_API_KEY=sk-xxx
AI_DEFAULT_PROVIDER=openai
```

> **提示**：
> - DeepSeek 不支持 Embedding，需配合其他提供商
> - GLM 和 OpenAI 支持 Embedding + Chat 全功能
> - 可以配置多个提供商实现自动降级

---

**就这么简单！** 🚀
