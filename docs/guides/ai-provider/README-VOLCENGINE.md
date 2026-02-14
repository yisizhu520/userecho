# 火山引擎 AI 配置文档索引

## 🚀 快速开始

**如果你只想快速配置，直接看这个**：

👉 [火山引擎快速上手（3 步配置）](./volcengine-quickstart.md)

---

## 📚 完整文档

### 配置指南

1. **[volcengine-quickstart.md](./volcengine-quickstart.md)** - 🔥 快速上手（推荐）
   - 3 步完成配置
   - 常见问题解答
   - 配置验证方法

2. **[volcengine-config-example.md](./volcengine-config-example.md)** - 📋 配置示例
   - 完整配置清单
   - 配置说明
   - 成本估算

3. **[volcengine-vision-setup.md](./volcengine-vision-setup.md)** - 📖 详细配置指南
   - 详细配置步骤
   - 使用场景说明
   - 监控和日志
   - 故障排查

### 通用文档

4. **[quick-start.md](./quick-start.md)** - 所有 Provider 快速入门
5. **[configuration.md](./configuration.md)** - 所有 Provider 详细配置
6. **[volcengine-endpoint-setup.md](./volcengine-endpoint-setup.md)** - 火山引擎 Endpoint 创建指南

---

## 🎯 根据需求选择文档

### 我想快速配置火山引擎
👉 **[volcengine-quickstart.md](./volcengine-quickstart.md)**（3 分钟上手）

### 我想了解详细配置选项
👉 **[volcengine-vision-setup.md](./volcengine-vision-setup.md)**（完整指南）

### 我想看配置示例
👉 **[volcengine-config-example.md](./volcengine-config-example.md)**（配置模板）

### 我不知道如何创建 Endpoint
👉 **[volcengine-endpoint-setup.md](./volcengine-endpoint-setup.md)**（创建指南）

### 我想对比不同 Provider
👉 **[quick-start.md](./quick-start.md)**（对比表）

### 我遇到问题了
👉 **[volcengine-vision-setup.md](./volcengine-vision-setup.md#-常见问题)**（故障排查）

---

## 🔧 配置验证工具

运行以下命令验证配置：

```bash
cd server
python check_volcengine_config.py
```

---

## 💡 核心要点

### 必填配置

```bash
VOLCENGINE_API_KEY=your-api-key-here
VOLCENGINE_CHAT_ENDPOINT=ep-20241221xxx-xxxxx  # 必须使用支持视觉的模型
AI_DEFAULT_PROVIDER=volcengine
```

### 模型选择

**推荐模型**：
- `doubao-vision-pro-32k`（首选）
- `doubao-pro-32k`（备选）

### 成本

- 单次识别：¥0.003（不到 1 分钱）
- 月度（100 张/天）：¥9

---

## 📞 获取帮助

- **技术问题**：查看 [常见问题](./volcengine-vision-setup.md#-常见问题)
- **配置问题**：运行 `check_volcengine_config.py` 验证
- **PRD 文档**：[wechat-feedback-collect.md](../../design/wechat-feedback-collect.md)
