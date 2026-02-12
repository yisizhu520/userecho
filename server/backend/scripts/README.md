# 测试脚本说明

## AI Provider 配置测试

### 脚本：`test_ai_providers.py`

用于验证 AI 提供商配置是否正确。

**这是一个独立的轻量级测试脚本**，不依赖整个 backend 框架，只需要两个 Python 包：
- `openai` - OpenAI SDK
- `python-dotenv` - 读取 .env 文件

### 安装依赖

如果运行时提示缺少依赖，请安装：

```bash
pip install openai python-dotenv
```

或使用 uv（推荐）：

```bash
cd server
uv add openai python-dotenv
```

### 使用方法

#### 方式 1：使用启动脚本（推荐）

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

#### 方式 2：直接运行 Python 脚本

```bash
# 确保在 server/backend 目录下
cd server/backend
python scripts/test_ai_providers.py
```

### 测试内容

1. **初始化检查**：验证是否成功初始化 AI 客户端
2. **Embedding 测试**：测试文本向量化功能
3. **主题生成测试**：测试根据反馈生成主题的功能
4. **摘要生成测试**：测试文本摘要功能
5. **降级测试**：测试多提供商自动降级功能

### 预期输出

```
============================================================
AI Provider 配置测试
============================================================

✅ 已初始化的提供商: ['deepseek', 'openai']
📌 当前默认提供商: deepseek

============================================================
测试 1: Embedding 功能
============================================================
测试文本: 这是一个测试文本，用于验证 embedding 功能。
✅ Embedding 成功
   - 使用提供商: deepseek
   - 向量维度: 1536
   - 前5个值: [0.123, -0.456, 0.789, ...]

... (其他测试输出)

🎉 所有测试完成！AI Provider 配置正确。
```

### 常见错误

#### 错误 1：没有配置任何提供商

```
❌ 错误：没有配置任何 AI 提供商！
请在 .env 文件中配置至少一个提供商的 API Key。
```

**解决方法**：在 `.env` 文件中添加至少一个提供商的 API Key。

#### 错误 2：API Key 无效

```
❌ Embedding 失败
```

**解决方法**：检查 API Key 是否正确，或者提供商服务是否正常。

#### 错误 3：火山引擎 Endpoint 未配置

```
⚠️  VOLCENGINE_EMBEDDING_ENDPOINT not configured
```

**解决方法**：在 `.env` 文件中配置火山引擎的 Endpoint ID。

## 其他脚本

（待添加）
