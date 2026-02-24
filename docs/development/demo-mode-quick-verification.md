# Demo 模式快速验证指南

## 验证应用标题显示

### 后端验证

启动 Demo 模式的后端服务：

```bash
cd server
ENV_FILE=.env.demo uvicorn backend.main:app --reload
```

访问 API 文档：
- 打开 http://127.0.0.1:8000/docs
- 页面标题应该显示：**回响-演示版**
- API 文档描述应该显示：**回响 - AI 驱动的用户反馈智能分析平台（演示环境）**

### 前端验证

构建并预览 Demo 版本：

```bash
cd front
pnpm build:demo
pnpm preview
```

或直接运行开发模式：

```bash
cd front/apps/web-antd
cp .env.demo .env
pnpm dev
```

验证点：
- 浏览器标签页标题应该显示：**回响-演示版**
- 应用顶部标题应该显示：**回响-演示版**

## 验证 Demo 模式功能

### 1. 允许的操作 ✅

测试以下操作应该**全部成功**：

```bash
# 假设已获取 JWT Token
TOKEN="your-jwt-token"

# 创建反馈
curl -X POST http://localhost:8000/api/v1/feedback/create \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"content": "测试反馈"}'
# 预期：200 OK

# 创建议题
curl -X POST http://localhost:8000/api/v1/topic/create \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"title": "测试议题"}'
# 预期：200 OK

# 触发聚类（需要 Turnstile token）
curl -X POST http://localhost:8000/api/v1/clustering/run \
  -H "Authorization: Bearer $TOKEN"
# 预期：200 OK（如果配置了 Turnstile）
```

### 2. 禁止的操作 ❌

测试以下操作应该**全部被拦截**：

```bash
# 删除 Demo 预置用户
curl -X DELETE http://localhost:8000/api/v1/sys/user/demo_po \
  -H "Authorization: Bearer $TOKEN"
# 预期：403 Forbidden
# 错误信息：演示环境下禁止删除预置数据或修改系统配置

# 删除默认租户
curl -X DELETE http://localhost:8000/api/v1/tenant/default-tenant \
  -H "Authorization: Bearer $TOKEN"
# 预期：403 Forbidden

# 修改系统配置
curl -X PUT http://localhost:8000/api/v1/config/system \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"key": "value"}'
# 预期：403 Forbidden
```

## 验证角色切换

访问 Demo 欢迎页：

```bash
# 确保前端运行在 Demo 模式
cd front/apps/web-antd
# 确认 .env 文件中 VITE_DEMO_MODE=true
pnpm dev
```

访问 http://localhost:5173/demo：

- [ ] 页面标题显示"回响-演示版"
- [ ] 显示 3 个角色卡片：产品负责人、用户运营、系统管理员
- [ ] 点击任意角色卡片可以成功切换
- [ ] 切换后自动跳转到工作台

## 验证配置自动化

### 后端自动配置

验证 `server/backend/core/conf.py` 中的逻辑：

```python
# 当 DEMO_MODE=true 时，自动设置：
# - FASTAPI_TITLE = "回响-演示版"
# - FASTAPI_DESCRIPTION = "回响 - AI 驱动的用户反馈智能分析平台（演示环境）"
```

### 前端配置

验证 `front/apps/web-antd/.env.demo`：

```bash
cat front/apps/web-antd/.env.demo | grep VITE_APP_TITLE
# 预期输出：VITE_APP_TITLE=回响-演示版
```

## 完整测试流程

### 1. 启动 Demo 环境

```bash
# 终端 1 - 启动后端
cd server
ENV_FILE=.env.demo uvicorn backend.main:app --reload

# 终端 2 - 启动前端
cd front/apps/web-antd
cp .env.demo .env
pnpm dev
```

### 2. 访问欢迎页

打开 http://localhost:5173/demo

### 3. 选择角色

点击"产品负责人"卡片

### 4. 验证功能

- [ ] 成功登录并跳转到工作台
- [ ] 页面标题显示"回响-演示版"
- [ ] 可以查看反馈列表
- [ ] 可以创建新反馈
- [ ] 可以触发 AI 聚类
- [ ] **无法**删除 Demo 用户（demo_po）

### 5. 切换角色

使用角色切换浮动组件（如果已实现）切换到"用户运营"

### 6. 数据重置

手动执行重置脚本：

```bash
cd server/backend
./init_demo_environment.sh --reset
```

验证：
- [ ] Demo 用户重新创建
- [ ] 示例数据重新生成
- [ ] 之前创建的测试数据已清除

## 常见问题

### 问题 1：标题没有更新

**症状**：访问 API 文档时标题仍然显示 "fba"

**解决**：
1. 确认 `.env.demo` 文件中 `DEMO_MODE=true`
2. 重启后端服务
3. 清除浏览器缓存

### 问题 2：前端标题不正确

**症状**：浏览器标签页标题不是"回响-演示版"

**解决**：
1. 确认 `front/apps/web-antd/.env.demo` 中 `VITE_APP_TITLE=回响-演示版`
2. 重新构建前端：`pnpm build:demo`
3. 清除浏览器缓存

### 问题 3：所有操作都被拦截

**症状**：创建反馈、议题等操作返回 403

**解决**：
1. 检查 `server/backend/utils/demo_site.py` 的 `forbidden_patterns`
2. 确认没有意外添加过多的拦截规则
3. 查看后端日志，确认拦截原因

## 相关文档

- [Demo 环境部署指南](../guides/deployment/demo-environment-guide.md)
- [P0 问题修复总结](./demo-mode-p0-fixes.md)
- [Demo 保护机制设计](./demo-mode-protection-mechanism.md)
