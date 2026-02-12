# AI Provider 故障排查指南

## 常见错误和解决方案

### 1. 测试脚本导入错误

#### 错误 1: `ModuleNotFoundError: No module named 'openai'`

**原因**：缺少 openai 包。

**解决方法**：
```bash
pip install openai python-dotenv
```

或使用 uv：
```bash
cd server
uv add openai python-dotenv
```

---

#### 错误 2: `ModuleNotFoundError: No module named 'backend'`

**原因**：旧版本的测试脚本依赖 backend 框架。

**解决方法**：确保使用最新版本的测试脚本（已修复）。最新版本是**独立的**，不依赖 backend 框架。

---

### 2. API 调用错误

#### 错误 1: `Error code: 404`

**原因**：
- API Key 无效或过期
- API URL 不正确
- 模型名称错误

**解决方法**：

1. **检查 API Key 是否有效**：

登录对应平台确认 API Key：
- DeepSeek: https://platform.deepseek.com
- OpenAI: https://platform.openai.com
- GLM: https://open.bigmodel.cn
- Volcengine: https://console.volcengine.com

2. **检查 .env 配置**：

```bash
# 查看当前配置
cat server/backend/.env | grep API_KEY
```

确保格式正确：
```bash
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxx
```

3. **测试 API Key 是否有效**：

使用 curl 测试（以 DeepSeek 为例）：

```bash
curl https://api.deepseek.com/v1/models \
  -H "Authorization: Bearer YOUR_API_KEY"
```

如果返回 401/403，说明 API Key 无效。

---

#### 错误 2: `Error code: 401 - Unauthorized`

**原因**：API Key 无效或未授权。

**解决方法**：
1. 重新生成 API Key
2. 确认 API Key 已复制完整（没有多余空格）
3. 检查账户是否有足够余额

---

#### 错误 3: `Error code: 429 - Rate Limit Exceeded`

**原因**：请求速率超过限制。

**解决方法**：
1. 等待几分钟后重试
2. 升级账户计划
3. 切换到其他提供商（配置多个 provider）

---

#### 错误 4: `Connection timeout` / `Connection refused`

**原因**：网络问题或防火墙阻止。

**解决方法**：

1. **检查网络连接**：
```bash
ping api.deepseek.com
```

2. **测试 HTTP 连接**：
```bash
curl -I https://api.deepseek.com
```

3. **配置代理**（如果需要）：
```bash
export HTTP_PROXY=http://your-proxy:port
export HTTPS_PROXY=http://your-proxy:port
```

4. **使用国内服务商**：
如果无法访问国际服务，切换到 GLM 或 Volcengine：
```bash
AI_DEFAULT_PROVIDER=glm
```

---

### 3. 火山引擎特殊错误

#### 错误: `VOLCENGINE_EMBEDDING_ENDPOINT not configured`

**原因**：火山引擎需要配置 Endpoint ID，不是模型名称。

**解决方法**：

1. 登录火山引擎控制台
2. 进入"机器学习平台" → "推理服务"
3. 创建推理服务（或查看现有服务）
4. 获取 Endpoint ID（格式：`ep-20241221xxx-xxxxx`）
5. 配置到 .env：

```bash
VOLCENGINE_API_KEY=your-api-key
VOLCENGINE_EMBEDDING_ENDPOINT=ep-20241221xxx-xxxxx
VOLCENGINE_CHAT_ENDPOINT=ep-20241221xxx-xxxxx
```

---

### 4. 配置文件错误

#### 错误: `找不到 .env 文件`

**原因**：.env 文件不存在或位置错误。

**解决方法**：

1. **检查文件是否存在**：
```bash
ls server/backend/.env
```

2. **从模板创建**：
```bash
cp server/backend/.env.example server/backend/.env
```

3. **编辑配置**：
```bash
# Windows
notepad server/backend/.env

# Linux/Mac
nano server/backend/.env
```

---

#### 错误: `No AI clients initialized`

**原因**：没有配置任何有效的 API Key。

**解决方法**：

在 `.env` 文件中至少配置一个提供商：

```bash
# 最简配置
DEEPSEEK_API_KEY=sk-your-key-here
AI_DEFAULT_PROVIDER=deepseek
```

---

## 测试检查清单

在提交问题前，请依次检查：

- [ ] 1. 测试脚本依赖已安装（`pip install openai python-dotenv`）
- [ ] 2. .env 文件存在于 `server/backend/.env`
- [ ] 3. 至少配置了一个提供商的 API Key
- [ ] 4. API Key 格式正确（没有多余空格或换行）
- [ ] 5. API Key 有效（在对应平台验证）
- [ ] 6. 网络能访问对应的 API 地址
- [ ] 7. 账户有足够余额（如果是付费服务）

---

## 调试技巧

### 1. 查看详细错误信息

在 Python 脚本中添加 `-v` 标志（如果支持），或查看完整的 traceback。

### 2. 测试单个提供商

临时修改 `.env`，只保留一个提供商的配置：

```bash
# 只测试 DeepSeek
DEEPSEEK_API_KEY=sk-xxx
AI_DEFAULT_PROVIDER=deepseek

# 注释掉其他
# OPENAI_API_KEY=
# GLM_API_KEY=
```

### 3. 使用 curl 验证 API

在运行 Python 测试前，先用 curl 验证 API 是否可访问：

**DeepSeek:**
```bash
curl https://api.deepseek.com/v1/models \
  -H "Authorization: Bearer YOUR_API_KEY"
```

**OpenAI:**
```bash
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer YOUR_API_KEY"
```

**GLM:**
```bash
curl https://open.bigmodel.cn/api/paas/v4/models \
  -H "Authorization: Bearer YOUR_API_KEY"
```

### 4. 检查环境变量

确认环境变量已正确加载：

```python
import os
from dotenv import load_dotenv
from pathlib import Path

env_file = Path('server/backend/.env')
load_dotenv(env_file)

print(f"DEEPSEEK_API_KEY: {os.getenv('DEEPSEEK_API_KEY')[:10]}...")
print(f"AI_DEFAULT_PROVIDER: {os.getenv('AI_DEFAULT_PROVIDER')}")
```

---

## 获取帮助

如果以上方法都无法解决问题，请提供以下信息：

1. **错误完整输出**（包括 traceback）
2. **Python 版本**：`python --version`
3. **依赖版本**：`pip list | grep -E "openai|dotenv"`
4. **配置情况**（脱敏后）：
   ```bash
   AI_DEFAULT_PROVIDER=deepseek
   DEEPSEEK_API_KEY=sk-xxxx（前几位）
   ```
5. **网络测试结果**：
   ```bash
   curl -I https://api.deepseek.com
   ```

---

## 成功标志

当看到以下输出，说明配置成功：

```
✓ 已加载配置文件: /path/to/.env
✓ DEEPSEEK 客户端初始化成功
✅ 已初始化的提供商: ['deepseek']
📌 当前默认提供商: deepseek
✅ Embedding 成功
✅ Chat 成功
🎉 所有测试完成！
```

---

## 快速修复

### 最常见的问题：API Key 无效

**快速解决**：

1. 登录对应平台
2. 重新生成 API Key
3. 完整复制新的 Key（确保没有空格）
4. 更新 .env 文件
5. 重新运行测试

这能解决 80% 的问题！
