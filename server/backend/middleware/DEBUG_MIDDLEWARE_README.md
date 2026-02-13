# Debug Middleware - 快速参考

## 一句话说明

**在开发时以 DEBUG 级别打印所有 API 请求的输入输出，方便调试问题。**

---

## 快速启用

### 1. 设置环境变量

```bash
# .env 文件
LOG_STD_LEVEL=DEBUG
```

### 2. 启动服务

```bash
cd server
source .venv/Scripts/activate
python backend/run.py
```

### 3. 发送请求

```bash
curl -X POST http://localhost:8000/api/v1/app/feedbacks \
  -H "Content-Type: application/json" \
  -d '{"content": "测试"}'
```

### 4. 查看日志

终端自动显示：
```text
================================================================================
🔵 REQUEST START | abc123...
================================================================================
Method: POST
Path: /api/v1/app/feedbacks
Body: {"content": "测试"}
================================================================================

================================================================================
🟢 RESPONSE END | abc123...
================================================================================
Status Code: 200
Body: {"code": 200, "data": {...}}
================================================================================
```

---

## 核心特性

| 特性 | 说明 |
|------|------|
| ✅ **自动脱敏** | 密码、token 等自动隐藏为 `******` |
| ✅ **智能过滤** | 跳过静态资源、OPTIONS 请求 |
| ✅ **零影响** | 生产环境（LOG_STD_LEVEL=INFO）自动关闭 |
| ✅ **格式清晰** | JSON 自动格式化，易读 |
| ✅ **完整信息** | 请求方法、路径、参数、请求体、响应体 |

---

## 生产环境

```bash
# 生产环境配置
LOG_STD_LEVEL=INFO  # 自动关闭 DebugMiddleware

# 结果
✅ 零性能影响
✅ 不记录任何调试日志
✅ 只保留关键业务日志
```

---

## 自动脱敏字段

- `password` / `old_password` / `new_password`
- `token` / `access_token` / `refresh_token`
- `api_key` / `secret`
- `authorization`

---

## 排除的路径

- `/favicon.ico`
- `/docs` / `/redoc` / `/openapi.json`
- `/metrics`
- `OPTIONS` 请求

---

## 常见用法

### 查看特定接口日志

```bash
python backend/run.py | grep "feedbacks"
```

### 只看错误响应

```bash
python backend/run.py | grep "Status Code: [45]"
```

### 临时关闭

```bash
export LOG_STD_LEVEL=INFO
python backend/run.py
```

---

## 完整文档

详细说明请查看：`/docs/development/debug-middleware-guide.md`

---

## Linus 的点评

> **"这才是工程师应该用的调试工具。"**
> 
> "不需要 Postman、不需要 Charles、不需要额外的抓包工具。启动服务，发请求，终端直接看到完整的输入输出。**简单、直接、有效。**"
> 
> "生产环境自动关闭，开发环境自动启用。这就是好品味。"

---

## 代码位置

- **源码**: `backend/middleware/debug_middleware.py`
- **注册**: `backend/core/registrar.py` (Line 225)
- **配置**: `backend/core/conf.py` (LOG_STD_LEVEL)


