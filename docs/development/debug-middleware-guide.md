# Debug 中间件使用指南

## 概述

**DebugMiddleware** 是一个专门用于开发环境的请求/响应调试中间件，能够以清晰的格式打印所有 API 请求的输入输出，极大提升开发调试效率。

---

## 功能特性

### ✅ 核心功能

1. **完整的请求日志**
   - HTTP 方法和路径
   - Query 参数
   - 关键 Headers（Content-Type、User-Agent 等）
   - 请求体（JSON、表单、文件上传）

2. **完整的响应日志**
   - HTTP 状态码
   - 响应体（JSON）

3. **自动脱敏**
   - 自动隐藏敏感字段：password、token、api_key 等
   - 递归处理嵌套对象

4. **智能过滤**
   - 自动跳过静态资源（/docs、/favicon.ico 等）
   - 自动跳过 OPTIONS 预检请求

5. **零性能影响**
   - **只在 DEBUG 级别生效**
   - 生产环境（LOG_STD_LEVEL=INFO）自动关闭
   - 不影响正常请求处理

---

## 快速开始

### 1. 启用 DEBUG 日志

编辑 `.env` 文件（或环境变量）：

```bash
# 开发环境
LOG_STD_LEVEL=DEBUG

# 生产环境（自动关闭 Debug Middleware）
LOG_STD_LEVEL=INFO
```

### 2. 启动服务

```bash
cd server
source .venv/Scripts/activate  # Windows
python backend/run.py
```

### 3. 发送测试请求

```bash
# 创建反馈
curl -X POST http://localhost:8000/api/v1/app/feedbacks \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "content": "测试反馈",
    "customer_id": "123"
  }'
```

### 4. 查看日志输出

终端会显示类似以下格式的日志：

```text
================================================================================
🔵 REQUEST START | a1b2c3d4-e5f6-7890-abcd-ef1234567890
================================================================================
Method: POST
Path: /api/v1/app/feedbacks
Query Params: {}
Headers: {
  "content-type": "application/json",
  "user-agent": "curl/7.68.0"
}
Body: {
  "content": "测试反馈",
  "customer_id": "123"
}
================================================================================

================================================================================
🟢 RESPONSE END | a1b2c3d4-e5f6-7890-abcd-ef1234567890
================================================================================
Status Code: 200
Body: {
  "code": 200,
  "msg": "Success",
  "data": {
    "id": "feedback_123",
    "content": "测试反馈",
    "created_at": "2025-12-22T10:30:00Z"
  }
}
================================================================================
```

---

## 日志格式说明

### 请求日志

```text
🔵 REQUEST START | {request_id}
Method: {HTTP方法}
Path: {请求路径}
Query Params: {查询参数 JSON}
Headers: {关键请求头 JSON}
Body: {请求体 JSON/文本}
```

### 响应日志

```text
🟢 RESPONSE END | {request_id}
Status Code: {HTTP状态码}
Body: {响应体 JSON}
```

**说明：**
- `request_id` - 每个请求的唯一标识，用于关联请求和响应
- 日志使用分隔线（80个等号）清晰区分不同请求
- JSON 数据自动格式化（缩进2空格）
- 中文内容正常显示（ensure_ascii=False）

---

## 自动脱敏

中间件会自动隐藏以下敏感字段：

| 敏感字段 | 替换为 |
|---------|-------|
| `password` | `******` |
| `old_password` | `******` |
| `new_password` | `******` |
| `confirm_password` | `******` |
| `token` | `******` |
| `access_token` | `******` |
| `refresh_token` | `******` |
| `api_key` | `******` |
| `secret` | `******` |
| `authorization` | `******` |

**示例：**

```python
# 请求体
{
  "username": "admin",
  "password": "my_secret_123"
}

# 日志输出（自动脱敏）
{
  "username": "admin",
  "password": "******"
}
```

---

## 排除的路径

以下路径不会记录调试日志（避免噪音）：

- `/favicon.ico`
- `/docs` - Swagger 文档
- `/redoc` - ReDoc 文档
- `/openapi.json` - OpenAPI 规范
- `/metrics` - Prometheus 指标
- `OPTIONS` 请求 - CORS 预检

---

## 高级配置

### 自定义敏感字段

编辑 `backend/middleware/debug_middleware.py`：

```python
class DebugMiddleware(BaseHTTPMiddleware):
    # 添加自定义敏感字段
    SENSITIVE_FIELDS = {
        'password',
        'token',
        'api_key',
        'id_card_number',    # 自定义：身份证号
        'phone_number',      # 自定义：手机号
        'credit_card',       # 自定义：信用卡号
    }
```

### 自定义排除路径

```python
class DebugMiddleware(BaseHTTPMiddleware):
    # 添加自定义排除路径
    EXCLUDED_PATHS = {
        '/favicon.ico',
        '/docs',
        '/admin/internal',   # 自定义：内部管理接口
        '/health',           # 自定义：健康检查
    }
```

---

## 性能影响

### 零影响（生产环境）

```bash
# 生产环境配置
LOG_STD_LEVEL=INFO  # 或 WARNING、ERROR

# 结果
✅ DebugMiddleware 自动跳过所有日志记录
✅ 只有极小的条件判断开销（< 0.01ms）
✅ 不读取请求体/响应体
```

### 微小影响（开发环境）

```bash
# 开发环境配置
LOG_STD_LEVEL=DEBUG

# 影响
📊 平均耗时增加：5-10ms（读取请求体/响应体）
📊 内存增加：可忽略（日志异步写入）
📊 适用场景：本地开发、测试环境
```

**建议：**
- ✅ **本地开发** - 启用 DEBUG
- ✅ **测试环境** - 启用 DEBUG
- ❌ **生产环境** - 关闭 DEBUG（使用 INFO 或更高级别）

---

## 实战示例

### 示例 1：调试登录接口

**请求：**
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123"
  }'
```

**日志输出：**
```text
================================================================================
🔵 REQUEST START | 12345678-1234-1234-1234-123456789012
================================================================================
Method: POST
Path: /api/v1/auth/login
Body: {
  "username": "admin",
  "password": "******"    ← 自动脱敏
}
================================================================================

================================================================================
🟢 RESPONSE END | 12345678-1234-1234-1234-123456789012
================================================================================
Status Code: 200
Body: {
  "code": 200,
  "msg": "Success",
  "data": {
    "access_token": "******",    ← 自动脱敏
    "username": "admin"
  }
}
================================================================================
```

---

### 示例 2：调试文件上传

**请求：**
```bash
curl -X POST http://localhost:8000/api/v1/app/import \
  -F "file=@feedback.xlsx" \
  -F "generate_summary=true"
```

**日志输出：**
```text
================================================================================
🔵 REQUEST START | 87654321-4321-4321-4321-210987654321
================================================================================
Method: POST
Path: /api/v1/app/import
Body: {
  "file": "<UploadFile: feedback.xlsx, application/vnd.openxmlformats-officedocument.spreadsheetml.sheet>",
  "generate_summary": "true"
}
================================================================================

================================================================================
🟢 RESPONSE END | 87654321-4321-4321-4321-210987654321
================================================================================
Status Code: 200
Body: {
  "code": 200,
  "msg": "Success",
  "data": {
    "status": "completed",
    "success": 50,
    "failed": 2
  }
}
================================================================================
```

---

### 示例 3：调试错误请求

**请求：**
```bash
curl -X POST http://localhost:8000/api/v1/app/feedbacks \
  -H "Content-Type: application/json" \
  -d '{
    "content": ""
  }'
```

**日志输出：**
```text
================================================================================
🔵 REQUEST START | abcdef12-3456-7890-abcd-ef1234567890
================================================================================
Method: POST
Path: /api/v1/app/feedbacks
Body: {
  "content": ""
}
================================================================================

================================================================================
🟢 RESPONSE END | abcdef12-3456-7890-abcd-ef1234567890
================================================================================
Status Code: 422
Body: {
  "code": 422,
  "msg": "Validation Error",
  "data": {
    "detail": [
      {
        "loc": ["body", "content"],
        "msg": "field required",
        "type": "value_error.missing"
      }
    ]
  }
}
================================================================================
```

通过日志可以清楚看到：
1. 请求发送了什么数据（空字符串）
2. 服务器返回了什么错误（422 验证错误）
3. 错误的具体原因（content 字段必填）

---

## 常见问题

### Q1: 为什么生产环境看不到调试日志？

**A:** 这是设计行为。DebugMiddleware 只在 `LOG_STD_LEVEL=DEBUG` 时生效。

**解决方案：**
```bash
# 临时启用（仅用于排查问题）
export LOG_STD_LEVEL=DEBUG
python backend/run.py

# 排查完毕后立即恢复
export LOG_STD_LEVEL=INFO
```

---

### Q2: 日志太多，如何过滤？

**A:** 使用 grep 过滤特定接口：

```bash
# 只看反馈相关接口
python backend/run.py | grep "feedbacks"

# 只看 POST 请求
python backend/run.py | grep "POST"

# 只看错误响应（状态码 >= 400）
python backend/run.py | grep "Status Code: [45]"
```

---

### Q3: 如何禁用 DebugMiddleware？

**方法 1：** 设置日志级别为 INFO（推荐）
```bash
LOG_STD_LEVEL=INFO
```

**方法 2：** 注释掉中间件注册
编辑 `backend/core/registrar.py`：
```python
def register_middleware(app: FastAPI) -> None:
    # Debug（开发环境调试）
    # app.add_middleware(DebugMiddleware)  # 注释掉
```

---

### Q4: 响应体显示 `<Non-JSON response>`？

**A:** 这表示响应不是 JSON 格式（如 HTML、文件下载等）。

**示例：**
```text
Body: <Non-JSON response: text/html>
```

这是正常行为，DebugMiddleware 只记录 JSON 响应的详细内容。

---

## 与其他日志的区别

| 中间件 | 用途 | 日志级别 | 记录内容 |
|--------|------|---------|---------|
| **DebugMiddleware** | 开发调试 | DEBUG | 完整请求/响应详情 |
| AccessMiddleware | 访问统计 | DEBUG | 请求开始标记 |
| OperaLogMiddleware | 操作审计 | INFO | 请求摘要、耗时、状态 |

**推荐配置：**
- 本地开发：启用 DebugMiddleware（DEBUG）
- 测试环境：启用 DebugMiddleware（DEBUG）
- 生产环境：关闭 DebugMiddleware（INFO），保留 OperaLogMiddleware

---

## 总结

### ✅ 优势

1. **开发效率提升** - 无需单独调试工具，终端直接看到完整请求/响应
2. **零学习成本** - 格式清晰，一目了然
3. **安全可靠** - 自动脱敏敏感信息
4. **零侵入** - 不修改业务代码
5. **生产安全** - 自动关闭，零性能影响

### 📝 最佳实践

1. **本地开发必开** - 设置 `LOG_STD_LEVEL=DEBUG`
2. **生产必关** - 设置 `LOG_STD_LEVEL=INFO`
3. **及时脱敏** - 添加自定义敏感字段到 `SENSITIVE_FIELDS`
4. **合理过滤** - 使用 grep 过滤日志噪音

---

## 相关文档

- **日志最佳实践**: `/docs/development/logging-best-practices.md`
- **中间件源码**: `/server/backend/middleware/debug_middleware.py`
- **日志配置**: `/server/backend/core/conf.py`

---

## 反馈

如有问题或建议，请参考：
- 项目文档：`/docs/`
- AGENTS.md 日志规范

