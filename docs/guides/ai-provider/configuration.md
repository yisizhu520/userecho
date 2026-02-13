# AI Provider 配置指南

## 概述

UserEcho 支持多个 AI 服务提供商，通过配置驱动的方式实现零硬编码的多模型支持。目前支持：

- **DeepSeek** (推荐：性价比高)
- **OpenAI** (国际标准)
- **GLM (智谱)** (国内服务商)
- **Volcengine (火山引擎/豆包)** (国内服务商)

## 支持的 AI 提供商

### 1. DeepSeek (推荐用于 Chat)

**优势：**
- 价格便宜（约为 OpenAI 的 1/10）
- API 兼容 OpenAI 格式
- 支持中文优化
- 国内访问速度快

**⚠️ 重要限制：**
- **不支持 Embedding API** - 只提供对话功能
- 如需 Embedding，请配合其他提供商使用（如 OpenAI、GLM）

**配置：**

```bash
DEEPSEEK_API_KEY=sk-your-deepseek-key-here
# DeepSeek 只用于 Chat，Embedding 需要配置其他提供商
OPENAI_API_KEY=sk-your-openai-key-here  # 或 GLM_API_KEY
AI_DEFAULT_PROVIDER=deepseek
```

**获取 API Key：**
1. 访问 [DeepSeek 开放平台](https://platform.deepseek.com)
2. 注册并登录
3. 在"API Keys"页面创建新的密钥

**使用的模型：**
- Embedding: ❌ **不支持**
- Chat: `deepseek-chat`（对应 DeepSeek-V3.2）

**参考文档：**
- [DeepSeek API 官方文档](https://api-docs.deepseek.com/zh-cn/)

---

### 2. OpenAI

**优势：**
- 最成熟的 AI 服务
- 模型质量高
- 生态丰富

**配置：**

```bash
OPENAI_API_KEY=sk-your-openai-key-here
AI_DEFAULT_PROVIDER=openai
```

**获取 API Key：**
1. 访问 [OpenAI Platform](https://platform.openai.com)
2. 注册并登录
3. 在"API Keys"页面创建新的密钥

**使用的模型：**
- Embedding: `text-embedding-3-small`
- Chat: `gpt-3.5-turbo`

---

### 3. GLM (智谱 AI)

**优势：**
- 国内服务商，访问稳定
- 支持中文优化
- 价格适中
- 兼容 OpenAI SDK

**配置：**

```bash
GLM_API_KEY=your-glm-api-key-here
AI_DEFAULT_PROVIDER=glm
```

**获取 API Key：**
1. 访问 [智谱 AI 开放平台](https://open.bigmodel.cn)
2. 注册并登录
3. 在"API Keys"页面创建新的密钥

**使用的模型：**
- Embedding: `embedding-3`
- Chat: `glm-4-flash`

**注意事项：**
- GLM 使用 OpenAI 兼容的 API 格式
- Base URL: `https://open.bigmodel.cn/api/paas/v4`

---

### 4. Volcengine (火山引擎/豆包)

**优势：**
- 字节跳动旗下服务
- 国内访问速度快
- 价格有竞争力
- 支持 Embedding + Chat 全功能

**配置：**

```bash
VOLCENGINE_API_KEY=your-volcengine-api-key-here
VOLCENGINE_EMBEDDING_ENDPOINT=ep-20250317192516-9zhft  # 替换为你的 Endpoint ID
VOLCENGINE_CHAT_ENDPOINT=ep-20250317xxxxxx-xxxxx       # 替换为你的 Endpoint ID
AI_DEFAULT_PROVIDER=volcengine
```

**获取 API Key 和 Endpoint：**
1. 访问 [火山引擎控制台](https://console.volcengine.com)
2. 开通"机器学习平台"或"豆包大模型"服务
3. 创建"推理服务"并获取 Endpoint ID
4. 在"API 密钥"页面获取 API Key（环境变量名：`ARK_API_KEY`）

**示例代码：**
```python
import os
from openai import OpenAI

client = OpenAI(
    api_key=os.environ.get("ARK_API_KEY"),
    base_url="https://ark.cn-beijing.volces.com/api/v3",
)

# Embedding 示例
resp = client.embeddings.create(
    model="ep-20250317192516-9zhft",  # 你的 Embedding Endpoint ID
    input=["花椰菜又称菜花、花菜，是一种常见的蔬菜。"],
    encoding_format="float"
)
print(resp)
```

**使用的模型：**
- Embedding: ✅ 使用你的 Endpoint ID（如 `ep-20250317192516-9zhft`）
- Chat: ✅ 使用你的 Endpoint ID

**注意事项：**
- 火山引擎使用 **Endpoint ID** 而不是模型名称
- 需要分别配置 Embedding 和 Chat 的 Endpoint
- Base URL: `https://ark.cn-beijing.volces.com/api/v3`
- API Key 环境变量可以是 `ARK_API_KEY` 或 `VOLCENGINE_API_KEY`

---

## 配置示例

### 完整配置（.env 文件）

```bash
# ==================== UserEcho AI 配置 ====================
# DeepSeek (推荐：性价比高)
DEEPSEEK_API_KEY=sk-your-deepseek-key-here

# OpenAI
OPENAI_API_KEY=sk-your-openai-key-here

# 智谱 GLM (国内服务商)
GLM_API_KEY=your-glm-api-key-here

# 火山引擎/豆包 (国内服务商，需配置 endpoint ID)
VOLCENGINE_API_KEY=your-volcengine-api-key-here
VOLCENGINE_EMBEDDING_ENDPOINT=ep-20241221xxx-xxxxx
VOLCENGINE_CHAT_ENDPOINT=ep-20241221xxx-xxxxx

# 默认使用的 AI 提供商：deepseek / openai / glm / volcengine
AI_DEFAULT_PROVIDER=deepseek
```

### 最小配置（只配置一个提供商）

```bash
# 只使用 DeepSeek
DEEPSEEK_API_KEY=sk-your-deepseek-key-here
AI_DEFAULT_PROVIDER=deepseek
```

---

## 多模型降级策略

系统支持自动降级到其他可用的 AI 提供商：

1. **初始化时自动检测**：只初始化配置了 API Key 的提供商
2. **默认提供商不可用时自动切换**：如果配置的默认提供商没有 API Key，自动切换到第一个可用的
3. **调用失败时循环降级**：当前提供商调用失败时，自动切换到下一个可用的提供商

**降级流程示例：**

```
1. 尝试使用 DeepSeek (默认)
   ↓ 失败
2. 降级到 OpenAI
   ↓ 失败
3. 降级到 GLM
   ↓ 失败
4. 降级到 Volcengine
   ↓ 失败
5. 返回错误 / 使用降级方案
```

---

## 技术实现

### 配置驱动设计

所有提供商的配置统一管理在 `PROVIDERS_CONFIG` 字典中：

```python
PROVIDERS_CONFIG = {
    'deepseek': {
        'base_url': 'https://api.deepseek.com',
        'embedding_model': 'deepseek-embedding',
        'chat_model': 'deepseek-chat',
        'env_key': 'DEEPSEEK_API_KEY',
    },
    # ... 其他提供商
}
```

**优势：**
- **零硬编码**：添加新提供商只需要在配置字典中添加一项
- **统一初始化**：通过循环配置字典来初始化所有客户端
- **统一调用**：直接查询配置字典获取模型名称，无需 if-elif 链
- **易于维护**：所有配置集中管理，修改方便

### 代码示例

```python
# 初始化客户端
for provider_name, config in self.PROVIDERS_CONFIG.items():
    api_key = getattr(settings, config['env_key'], None)
    if api_key:
        self.clients[provider_name] = AsyncOpenAI(
            base_url=config['base_url'],
            api_key=api_key
        )

# 调用 API
config = self.PROVIDERS_CONFIG[self.current_provider]
response = await self.clients[self.current_provider].embeddings.create(
    model=config['embedding_model'],
    input=text
)
```

---

## 价格对比（参考）

| 提供商 | Embedding (1M tokens) | Chat (1M tokens) | 备注 |
|--------|----------------------|------------------|------|
| DeepSeek | ¥0.7 | ¥1.4 (输入) | 性价比最高 |
| OpenAI | $0.02 (~¥0.14) | $0.50 (~¥3.5) | 需要国际支付 |
| GLM | ¥0.5 | ¥5 | 中文优化 |
| Volcengine | 按量计费 | 按量计费 | 需咨询官方 |

> **注意：** 价格会随时变动，请以官方最新价格为准。

---

## 常见问题

### 1. 如何添加新的 AI 提供商？

只需在 `server/backend/utils/ai_client.py` 的 `PROVIDERS_CONFIG` 中添加配置：

```python
'new_provider': {
    'base_url': 'https://api.example.com',
    'embedding_model': 'embedding-model-name',
    'chat_model': 'chat-model-name',
    'env_key': 'NEW_PROVIDER_API_KEY',
}
```

然后在 `server/backend/core/conf.py` 中添加环境变量：

```python
NEW_PROVIDER_API_KEY: str = ''
```

最后在 `.env` 文件中配置 API Key。

### 2. 可以同时配置多个提供商吗？

可以。系统会自动初始化所有配置了 API Key 的提供商，并在失败时自动降级到其他可用的提供商。

### 3. 如何切换默认提供商？

修改 `.env` 文件中的 `AI_DEFAULT_PROVIDER` 参数：

```bash
AI_DEFAULT_PROVIDER=glm  # 切换到智谱 GLM
```

### 4. 火山引擎的 Endpoint ID 在哪里找？

1. 登录火山引擎控制台
2. 进入"机器学习平台" → "推理服务"
3. 创建或查看现有的推理服务
4. Endpoint ID 格式类似：`ep-20241221xxx-xxxxx`

### 5. 如果所有提供商都失败了会怎样？

系统会使用降级方案：
- **Embedding**：返回 `None`
- **主题生成**：使用简单规则（关键词匹配）
- **摘要生成**：简单截断文本

---

## 推荐配置

### 个人/小团队

```bash
# DeepSeek 用于 Chat（性价比高），OpenAI 用于 Embedding
DEEPSEEK_API_KEY=sk-your-deepseek-key
OPENAI_API_KEY=sk-your-openai-key  # 或使用 GLM_API_KEY
AI_DEFAULT_PROVIDER=deepseek
```

> **说明**：DeepSeek 不支持 Embedding，系统会自动使用 OpenAI 或 GLM 进行 Embedding 操作。

### 企业（国内）

```bash
# 主用智谱 GLM，备用 DeepSeek
GLM_API_KEY=your-key
DEEPSEEK_API_KEY=sk-your-key
AI_DEFAULT_PROVIDER=glm
```

### 企业（国际）

```bash
# 主用 OpenAI，备用 DeepSeek
OPENAI_API_KEY=sk-your-key
DEEPSEEK_API_KEY=sk-your-key
AI_DEFAULT_PROVIDER=openai
```

---

## 更新日志

- **2024-12-21**: 添加智谱 GLM 和火山引擎支持
- **2024-12-XX**: 初始版本，支持 DeepSeek 和 OpenAI
