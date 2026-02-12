# 火山引擎 Endpoint 配置指南

## 🌋 火山引擎特殊说明

火山引擎（字节跳动的豆包大模型服务）使用 **Endpoint ID** 而不是固定的模型名称。这是它与其他提供商的主要区别。

---

## 📋 配置步骤

### 1. 获取 API Key

1. 访问 [火山引擎控制台](https://console.volcengine.com)
2. 注册并登录账户
3. 进入"API 访问密钥"页面
4. 创建新的 API Key（环境变量名：`ARK_API_KEY`）

### 2. 创建推理服务（Endpoint）

#### 对于 Embedding 服务：

1. 进入"机器学习平台" 或 "豆包大模型"
2. 选择"推理服务" → "创建推理服务"
3. 选择 **Embedding 模型**（如：doubao-embedding 等）
4. 创建成功后，获取 **Endpoint ID**

示例格式：`ep-20250317192516-9zhft`

#### 对于 Chat 服务：

1. 同样在"推理服务"中创建
2. 选择 **对话模型**（如：doubao-pro 等）
3. 获取 Chat 的 **Endpoint ID**

示例格式：`ep-20250317xxxxxx-xxxxx`

### 3. 配置环境变量

编辑 `server/backend/.env`：

```bash
# 火山引擎配置
VOLCENGINE_API_KEY=your-ark-api-key-here
VOLCENGINE_EMBEDDING_ENDPOINT=ep-20250317192516-9zhft  # 替换为你的 Embedding Endpoint
VOLCENGINE_CHAT_ENDPOINT=ep-20250317xxxxxx-xxxxx       # 替换为你的 Chat Endpoint
AI_DEFAULT_PROVIDER=volcengine
```

---

## 💻 代码示例

### Embedding 示例

```python
import os
from openai import OpenAI

client = OpenAI(
    api_key=os.environ.get("ARK_API_KEY"),  # 或 VOLCENGINE_API_KEY
    base_url="https://ark.cn-beijing.volces.com/api/v3",
)

# 使用 Endpoint ID 作为 model 参数
resp = client.embeddings.create(
    model="ep-20250317192516-9zhft",  # 你的 Embedding Endpoint ID
    input=["花椰菜又称菜花、花菜，是一种常见的蔬菜。"],
    encoding_format="float"
)
print(resp)
```

### Chat 示例

```python
import os
from openai import OpenAI

client = OpenAI(
    api_key=os.environ.get("ARK_API_KEY"),
    base_url="https://ark.cn-beijing.volces.com/api/v3",
)

# 使用 Chat Endpoint ID
resp = client.chat.completions.create(
    model="ep-20250317xxxxxx-xxxxx",  # 你的 Chat Endpoint ID
    messages=[
        {"role": "user", "content": "你好"}
    ]
)
print(resp.choices[0].message.content)
```

---

## 🔍 如何找到你的 Endpoint ID

### 方法 1: 控制台查看

1. 登录火山引擎控制台
2. 进入"机器学习平台" → "推理服务"
3. 找到你创建的服务
4. 在服务详情中找到 **Endpoint ID** 或 **接入点 ID**

### 方法 2: API 列表

在服务列表中，每个推理服务都会显示其 Endpoint ID，通常格式为：

```
ep-YYYYMMDDHHMMSS-xxxxx
```

其中：
- `YYYYMMDDHHMMSS` 是创建时间戳
- `xxxxx` 是随机标识符

---

## ⚙️ 在 Feedalyze 中的配置

### 完整配置示例

```bash
# .env 文件
VOLCENGINE_API_KEY=your-api-key-here
VOLCENGINE_EMBEDDING_ENDPOINT=ep-20250317192516-9zhft
VOLCENGINE_CHAT_ENDPOINT=ep-20250317123456-abcde
AI_DEFAULT_PROVIDER=volcengine
```

### 系统如何使用

1. **初始化时**：
   ```python
   # 使用 VOLCENGINE_API_KEY 创建 OpenAI 客户端
   client = AsyncOpenAI(
       api_key=settings.VOLCENGINE_API_KEY,
       base_url='https://ark.cn-beijing.volces.com/api/v3'
   )
   ```

2. **调用 Embedding 时**：
   ```python
   # 从环境变量读取 Endpoint ID
   model = settings.VOLCENGINE_EMBEDDING_ENDPOINT  # ep-20250317192516-9zhft
   
   response = await client.embeddings.create(
       model=model,  # 使用 Endpoint ID
       input=text
   )
   ```

3. **调用 Chat 时**：
   ```python
   # 从环境变量读取 Chat Endpoint ID
   model = settings.VOLCENGINE_CHAT_ENDPOINT  # ep-20250317123456-abcde
   
   response = await client.chat.completions.create(
       model=model,
       messages=[...]
   )
   ```

---

## ❓ 常见问题

### Q1: 为什么火山引擎使用 Endpoint ID 而不是模型名称？

**A**: 火山引擎的设计理念是"推理服务化"。每个 Endpoint 是一个独立的推理服务实例，可以配置不同的模型、参数和资源。这样设计的好处是：
- 更灵活的资源管理
- 支持自定义模型部署
- 更好的成本控制

### Q2: Endpoint ID 会变吗？

**A**: 不会。一旦创建，Endpoint ID 是固定的，除非你删除并重新创建推理服务。

### Q3: 可以使用多个 Endpoint 吗？

**A**: 当前实现只支持配置一个 Embedding Endpoint 和一个 Chat Endpoint。如果需要切换，可以修改环境变量。

### Q4: 如何测试 Endpoint 是否可用？

**A**: 运行测试脚本：

```bash
cd server/backend
python scripts/test_ai_providers.py
```

如果看到：
```
✅ Embedding 成功
   - 使用提供商: volcengine
   - 向量维度: 1536
```

说明配置成功！

### Q5: 火山引擎的价格如何？

**A**: 火山引擎采用按量计费，具体价格取决于：
- 选择的模型类型
- 请求次数和 token 消耗
- 服务配置（QPS、实例规格等）

建议在控制台查看实时价格或咨询客服。

---

## 🔗 相关资源

- [火山引擎官网](https://www.volcengine.com/)
- [火山引擎控制台](https://console.volcengine.com)
- [豆包大模型文档](https://www.volcengine.com/docs/82379)
- [Feedalyze AI Provider 配置指南](./ai-provider-configuration.md)

---

## ✅ 配置检查清单

使用火山引擎前，请确认：

- [ ] 已注册火山引擎账户
- [ ] 已获取 API Key（`VOLCENGINE_API_KEY`）
- [ ] 已创建 Embedding 推理服务并获取 Endpoint ID
- [ ] 已创建 Chat 推理服务并获取 Endpoint ID
- [ ] 已在 `.env` 文件中正确配置
- [ ] 已运行测试脚本验证配置

---

**更新时间**: 2024-12-21  
**适用版本**: Feedalyze v1.0.1+
