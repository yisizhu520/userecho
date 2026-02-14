# 火山引擎截图识别配置 - 快速上手

## 📋 3 步完成配置

### Step 1: 获取火山引擎凭证

1. 访问：[https://console.volcengine.com](https://console.volcengine.com)
2. 开通"豆包大模型"服务
3. 创建推理服务，选择模型：`doubao-vision-pro-32k`（推荐）
4. 记录以下信息：
   - **API Key**：在"API 密钥管理"获取
   - **Endpoint ID**：创建服务后获取（格式：`ep-20241221xxx-xxxxx`）

---

### Step 2: 配置环境变量

编辑 `server/backend/.env`，添加：

```bash
# 火山引擎配置
VOLCENGINE_API_KEY=your-api-key-here
VOLCENGINE_CHAT_ENDPOINT=ep-20241221xxx-xxxxx
AI_DEFAULT_PROVIDER=volcengine
```

> **重要**：`VOLCENGINE_CHAT_ENDPOINT` 必须使用支持视觉的模型（如 doubao-vision-pro-32k）

---

### Step 3: 验证配置

```bash
cd server
python check_volcengine_config.py
```

看到 `✅ 所有配置正确！` 即表示配置成功。

---

## ✅ 配置完成后

### 重启服务

```bash
cd server
source .venv/Scripts/activate
uvicorn backend.main:app --reload
```

### 测试功能

1. 登录 UserEcho 系统
2. 进入"反馈管理" → "截图上传"
3. 上传一张微信/小红书/App Store 截图
4. 查看 AI 是否自动识别：
   - ✅ 平台类型（微信/小红书...）
   - ✅ 用户昵称
   - ✅ 反馈内容
   - ✅ 反馈类型（Bug/需求/投诉）

---

## 🔧 常见问题

### Q: 如何选择合适的模型？

**推荐模型**：
1. **doubao-vision-pro-32k**（首选）- 最新视觉模型，识别准确
2. **doubao-pro-32k** - 通用模型，也支持图像
3. **glm-4v**（如果火山代理）- 智谱 GLM-4V

### Q: VISION_ENDPOINT 和 CHAT_ENDPOINT 有什么区别？

- **CHAT_ENDPOINT**：必填，用于对话和多模态（图像+文本）
- **VISION_ENDPOINT**：可选，专门用于图像识别

**推荐配置**：只配置 `CHAT_ENDPOINT`（使用支持视觉的模型），系统会自动使用它进行截图识别。

### Q: 提示"VOLCENGINE_VISION_ENDPOINT not configured"

**原因**：代码已更新，会自动回退到 `CHAT_ENDPOINT`，这个警告可以忽略。

**彻底解决**：确保配置了 `VOLCENGINE_CHAT_ENDPOINT` 即可。

### Q: 成本如何？

**单次识别成本**：约 ¥0.003（不到 1 分钱）

**月度成本估算**：
- 每天 100 张截图 × 30 天 = ¥9/月
- 每天 500 张截图 × 30 天 = ¥45/月

**对比**：
- OpenAI GPT-4o：约贵 6 倍
- 智谱 GLM-4V：约贵 5 倍

---

## 📚 详细文档

- **详细配置指南**：[volcengine-vision-setup.md](./volcengine-vision-setup.md)
- **配置示例**：[volcengine-config-example.md](./volcengine-config-example.md)
- **PRD 文档**：[wechat-feedback-collect.md](../../design/wechat-feedback-collect.md)
- **技术实现**：[screenshot-recognition-implementation.md](../../design/screenshot-recognition-implementation.md)

---

## 🎯 核心配置参数总结

| 参数 | 必填 | 说明 | 示例 |
|------|------|------|------|
| `VOLCENGINE_API_KEY` | ✅ | 火山引擎 API Key | `your-api-key` |
| `VOLCENGINE_CHAT_ENDPOINT` | ✅ | 支持视觉的模型 Endpoint | `ep-20241221xxx-xxxxx` |
| `VOLCENGINE_VISION_ENDPOINT` | ❌ | 独立视觉 Endpoint（可选） | `ep-20241221yyy-yyyyy` |
| `VOLCENGINE_EMBEDDING_ENDPOINT` | ❌ | Embedding Endpoint（可选） | `ep-20241221zzz-zzzzz` |
| `AI_DEFAULT_PROVIDER` | ✅ | 默认 Provider | `volcengine` |

---

**🎉 配置完成！现在可以开始使用截图智能识别功能了。**
