# AI Provider Embedding 支持说明

## ⚠️ 重要发现：DeepSeek 不支持 Embedding

根据 [DeepSeek 官方 API 文档](https://api-docs.deepseek.com/zh-cn/)，**DeepSeek 只提供对话（Chat）功能，不提供 Embedding API**。

### DeepSeek 支持的功能

| 功能 | 支持情况 | 模型 |
|------|---------|------|
| Chat（对话） | ✅ 支持 | `deepseek-chat` (DeepSeek-V3.2) |
| Reasoner（推理） | ✅ 支持 | `deepseek-reasoner` (DeepSeek-V3.2 思考模式) |
| **Embedding** | ❌ **不支持** | - |

---

## 📊 各提供商 Embedding 支持对比

| 提供商 | Embedding | Chat | 价格（1M tokens） | 推荐用途 |
|--------|-----------|------|-------------------|----------|
| **DeepSeek** | ❌ | ✅ | ¥1.4 | 仅用于 Chat |
| **OpenAI** | ✅ | ✅ | Embedding: ~¥0.14, Chat: ~¥3.5 | 全功能（质量高） |
| **GLM (智谱)** | ✅ | ✅ | Embedding: ¥0.5, Chat: ¥5 | 全功能（国内服务） |
| **Volcengine (火山引擎)** | ✅ | ✅ | 按量计费 | 全功能（字节服务，使用 Endpoint ID） |

---

## 💡 推荐配置方案

### 方案 1：DeepSeek + OpenAI 组合（推荐）

**适合**：个人开发者，追求性价比

**配置**：
```bash
DEEPSEEK_API_KEY=sk-your-deepseek-key      # Chat 用 DeepSeek（便宜）
OPENAI_API_KEY=sk-your-openai-key          # Embedding 用 OpenAI
AI_DEFAULT_PROVIDER=deepseek
```

**优势**：
- Chat 成本低（DeepSeek ¥1.4/M tokens）
- Embedding 质量高（OpenAI）
- 总体性价比最高

---

### 方案 2：GLM 全功能（推荐国内用户）

**适合**：国内企业，需要稳定访问

**配置**：
```bash
GLM_API_KEY=your-glm-api-key
AI_DEFAULT_PROVIDER=glm
```

**优势**：
- 支持 Embedding + Chat 全功能
- 国内服务，访问稳定
- 中文优化

---

### 方案 3：OpenAI 全功能（质量优先）

**适合**：国际企业，追求最高质量

**配置**：
```bash
OPENAI_API_KEY=sk-your-openai-key
AI_DEFAULT_PROVIDER=openai
```

**优势**：
- 模型质量最高
- 功能最全
- 生态最成熟

---

### 方案 4：多提供商混合（最佳容错）

**适合**：生产环境，需要高可用性

**配置**：
```bash
DEEPSEEK_API_KEY=sk-your-deepseek-key      # Chat 主力
GLM_API_KEY=your-glm-api-key               # Embedding 主力
OPENAI_API_KEY=sk-your-openai-key          # 备用
AI_DEFAULT_PROVIDER=deepseek
```

**优势**：
- 自动降级容错
- 成本和质量平衡
- 最高可用性

---

## 🔧 系统如何处理 Embedding

### 自动降级机制

当使用 DeepSeek 作为默认提供商时，系统会自动处理 Embedding 请求：

```python
# 用户配置
AI_DEFAULT_PROVIDER=deepseek  # 默认用 DeepSeek

# 系统行为
Chat 请求 → 使用 DeepSeek ✅
Embedding 请求 → 自动跳过 DeepSeek，使用下一个可用的提供商（OpenAI/GLM）✅
```

### 降级流程示例

```
Embedding 请求:
1. 尝试 DeepSeek → 跳过（不支持）
2. 尝试 OpenAI → 成功 ✅

Chat 请求:
1. 尝试 DeepSeek → 成功 ✅
```

---

## 📝 代码实现

### 配置定义

```python
PROVIDERS_CONFIG = {
    'deepseek': {
        'base_url': 'https://api.deepseek.com',
        'embedding_model': None,  # ❌ 不支持
        'chat_model': 'deepseek-chat',
    },
    'openai': {
        'base_url': None,
        'embedding_model': 'text-embedding-3-small',  # ✅ 支持
        'chat_model': 'gpt-3.5-turbo',
    },
    'glm': {
        'base_url': 'https://open.bigmodel.cn/api/paas/v4',
        'embedding_model': 'embedding-3',  # ✅ 支持
        'chat_model': 'glm-4-flash',
    },
    'volcengine': {
        'base_url': 'https://ark.cn-beijing.volces.com/api/v3',
        'embedding_model': None,  # ✅ 支持，但从环境变量读取 Endpoint ID
        'chat_model': None,
    },
}
```

### 自动跳过和特殊处理逻辑

```python
async def get_embedding(self, text: str):
    config = self.PROVIDERS_CONFIG[self.current_provider]
    embedding_model = config['embedding_model']
    
    # 火山引擎特殊处理：从环境变量读取 endpoint ID
    if self.current_provider == 'volcengine':
        embedding_model = getattr(settings, 'VOLCENGINE_EMBEDDING_ENDPOINT', None)
        if not embedding_model:
            log.warning('VOLCENGINE_EMBEDDING_ENDPOINT not configured')
            self._fallback_to_next_provider()
            return
    
    # 如果不支持 embedding，自动切换
    if embedding_model is None:
        log.info(f'{self.current_provider} does not support embedding')
        self._fallback_to_next_provider()
        # 递归调用，尝试下一个 provider
```

**关键点**：
- DeepSeek 的 `embedding_model` 是 `None` → 不支持
- Volcengine 的 `embedding_model` 也是 `None`，但有特殊处理逻辑从环境变量读取 → 支持

---

## ❓ 常见问题

### Q1: 为什么选择 DeepSeek？

**A**: DeepSeek Chat 性价比极高（¥1.4/M tokens），虽然不支持 Embedding，但配合 OpenAI 的 Embedding（~¥0.14/M tokens），总体成本仍然比全用 OpenAI Chat（~¥3.5/M tokens）便宜很多。

### Q2: 如何验证 Embedding 是否正常工作？

**A**: 运行测试脚本：

```bash
cd server/backend
python scripts/test_ai_providers.py
```

如果看到：
```
⚠️  DEEPSEEK 不支持 embedding API
```

说明系统已正确识别，并会自动使用其他提供商。

### Q3: 只配置了 DeepSeek，Embedding 会失败吗？

**A**: 是的。如果只配置 DeepSeek，Embedding 功能将不可用，反馈聚类等功能会受影响。**必须至少配置一个支持 Embedding 的提供商**（OpenAI、GLM 或 Volcengine）。

### Q4: 可以只用 GLM 吗？

**A**: 可以！GLM 支持 Embedding + Chat 全功能。配置：

```bash
GLM_API_KEY=your-key
AI_DEFAULT_PROVIDER=glm
```

### Q5: 如何选择最适合的方案？

| 场景 | 推荐方案 | 原因 |
|------|---------|------|
| 个人开发、追求性价比 | DeepSeek + OpenAI | 成本最低 |
| 国内企业、需要稳定 | GLM 全功能 | 访问稳定 |
| 国际企业、质量优先 | OpenAI 全功能 | 质量最高 |
| 生产环境、高可用 | 多提供商混合 | 容错最好 |

---

## 📚 相关资源

- [DeepSeek 官方文档](https://api-docs.deepseek.com/zh-cn/)
- [OpenAI Embedding 文档](https://platform.openai.com/docs/guides/embeddings)
- [智谱 GLM 文档](https://open.bigmodel.cn/dev/api)
- [Feedalyze AI Provider 配置指南](./ai-provider-configuration.md)

---

**更新时间**: 2024-12-21  
**重要性**: ⚠️ 高（影响 Embedding 功能）
