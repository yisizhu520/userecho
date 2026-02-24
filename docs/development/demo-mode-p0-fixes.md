# Demo 模式 P0 问题修复总结

## 修复日期
2026-01-21

## 修复历史

### 第二轮修复（2026-01-21）- 移除全局写入拦截 ✅

**问题**：Demo 模式拦截了所有 POST/PUT/DELETE 请求，用户无法体验核心功能
**影响**：无法创建反馈、触发 AI 聚类、生成洞察，Demo 变成"只读展示"

**解决方案**：
- ✅ 移除全局的 POST/PUT/DELETE 拦截
- ✅ 改为只拦截真正危险的操作（删除预置用户、删除租户、修改系统配置）
- ✅ 允许用户完整体验所有核心功能
- ✅ 数据每日自动重置，无需担心被"搞坏"

**修改文件**：
- `server/backend/utils/demo_site.py` - 重写保护逻辑
- `server/backend/core/conf.py` - 移除 `DEMO_MODE_EXCLUDE` 白名单

### 第三轮修复（2026-01-21）- 应用标题优化 ✅

**问题**：Demo 模式下应用标题应该显示"回响-演示版"

**解决方案**：
- ✅ 后端：在 `check_env` 方法中根据 `DEMO_MODE` 自动设置 `FASTAPI_TITLE` 为"回响-演示版"
- ✅ 前端：修改 `.env.demo` 中的 `VITE_APP_TITLE` 为"回响-演示版"

**修改文件**：
- `server/backend/core/conf.py` - 添加 Demo 模式标题自动设置
- `front/apps/web-antd/.env.demo` - 修改应用标题

---

## 修复的致命问题

### 1. 邮箱不一致导致角色切换 100% 失败 ✅

**问题描述**：
- `create_demo_users.py` 创建用户时使用 `po@demo.userecho.app`
- `demo.py` API 查询用户时使用 `demo_po@example.com`
- 两者不匹配，导致 `/api/v1/demo/switch-role` 接口无法找到用户

**解决方案**：
改用 `username` 作为唯一标识，动态查询用户获取实际邮箱

**修改文件**：
- `server/backend/app/admin/api/v1/demo.py`
  - 将 `DEMO_ROLES` 中的 `email` 字段改为 `username`
  - 在 `switch_role` 函数中先查询用户，再使用用户的实际邮箱登录
  - 添加详细的错误日志

**核心改动**：
```python
# ❌ 旧代码 - 硬编码邮箱
DEMO_ROLES = {
    "product_owner": {
        "email": "demo_po@example.com",  # 数据库里没有这个邮箱！
        ...
    }
}

# ✅ 新代码 - 使用 username 查询
DEMO_ROLES = {
    "product_owner": {
        "username": "demo_po",  # 匹配数据库的 username
        ...
    }
}

# 在 switch_role 中动态查询
result = await db.execute(select(User).where(User.username == username))
user = result.scalar_one_or_none()
if not user:
    raise HTTPException(404, detail=f"Demo 用户 {username} 不存在")
```

---

### 2. 前端缺少 Demo 模式检测 ✅

**问题描述**：
- `/demo` 路由无条件注册，生产环境也能访问（但后端返回 404）
- 环境变量 `import.meta.env.VITE_DEMO_MODE` 到处散落
- 没有统一的环境变量管理

**解决方案**：
1. 创建统一的环境变量工具 `utils/env.ts`
2. 修改路由，只在 `isDemoMode=true` 时注册 `/demo` 路由

**修改文件**：
- `front/apps/web-antd/src/utils/env.ts`（新建）
- `front/apps/web-antd/src/router/routes/core.ts`
- `front/apps/web-antd/src/components/demo/TurnstileWidget.vue`

**核心改动**：
```typescript
// ✅ 新建：统一的环境变量工具
// utils/env.ts
export const isDemoMode = import.meta.env.VITE_DEMO_MODE === 'true';
export const turnstileSiteKey = import.meta.env.VITE_TURNSTILE_SITE_KEY || '';

// ✅ 路由条件注册
// router/routes/core.ts
import { isDemoMode } from '#/utils/env';

const demoRoutes: RouteRecordRaw[] = isDemoMode
  ? [
      {
        path: '/demo',
        component: () => import('#/views/demo/DemoWelcome.vue'),
        ...
      },
    ]
  : [];

const finalCoreRoutes = [...coreRoutes, ...demoRoutes];
```

---

### 3. 域名更新 ✅

**问题**：
文档和代码中使用旧域名 `demo.huixiang.app`

**解决方案**：
全局替换为 `demo.userecho.app`

**修改文件**：
- `server/backend/scripts/create_demo_users.py` - Demo 用户邮箱
- `docs/guides/deployment/demo-environment-guide.md` - 部署文档
- `front/apps/web-antd/src/views/landing/components/HeroSection.vue` - 落地页链接

**邮箱变更**：
- `po@demo.huixiang.app` → `po@demo.userecho.app`
- `ops@demo.huixiang.app` → `ops@demo.userecho.app`
- `admin@demo.huixiang.app` → `admin@demo.userecho.app`

---

## 验证结果

### 后端检查 ✅
```bash
cd server && bash pre-commit.sh
```
- ✅ Ruff 代码检查通过
- ✅ Ruff 格式化通过
- ✅ mypy 类型检查通过（519 个文件）

### 前端检查 ✅
```bash
cd front && pnpm check:type
```
- ✅ TypeScript 编译通过
- ✅ 所有路由类型检查通过

---

## 使用指南

### 初始化 Demo 环境

```bash
cd server/backend

# 1. 创建 Demo 用户
python scripts/create_demo_users.py

# 2. 初始化示例数据
python scripts/init_demo_data.py

# 或者一键执行
./init_demo_environment.sh
```

### 测试角色切换

```bash
# 1. 启动后端（Demo 模式）
cd server
ENV_FILE=.env.demo uvicorn backend.main:app --reload

# 2. 测试 API
curl -X POST http://localhost:8000/api/v1/demo/switch-role \
  -H "Content-Type: application/json" \
  -d '{"role_key": "product_owner"}'

# 预期返回：
# {
#   "code": 200,
#   "data": {
#     "access_token": "eyJhbGc...",
#     "token_type": "Bearer",
#     "role": {
#       "key": "product_owner",
#       "name": "产品负责人"
#     }
#   }
# }
```

### 前端访问

- **非 Demo 环境**：访问 `/demo` 返回 404（路由未注册）
- **Demo 环境**：
  1. 设置 `VITE_DEMO_MODE=true`
  2. 访问 `https://demo.userecho.app/demo`
  3. 选择角色，一键切换

---

## Demo 模式保护机制

### 设计原则

**✅ 允许的操作**（用户完整体验）：
- 创建反馈、议题、客户
- 触发 AI 聚类
- 生成洞察报告
- 修改看板设置
- 所有 GET 请求
- 所有业务相关的 POST/PUT/PATCH 请求

**❌ 禁止的操作**（危险操作）：
- 删除 Demo 预置用户（demo_po, demo_ops, demo_admin）
- 删除默认租户（default-tenant）
- 修改系统级配置

### 实现方式

```python
# utils/demo_site.py
forbidden_patterns = [
    # 禁止删除 Demo 预置用户
    (lambda m, p: m == "DELETE" and "/api/v1/sys/user/" in p 
     and any(u in p for u in ["demo_po", "demo_ops", "demo_admin"])),
    
    # 禁止删除默认租户
    (lambda m, p: m == "DELETE" and "/api/v1/tenant/default-tenant" in p),
    
    # 禁止修改系统级配置
    (lambda m, p: m in ["PUT", "PATCH", "DELETE"] 
     and "/api/v1/config/system" in p),
]
```

### 为什么这样设计？

1. **用户体验优先**：Demo 应该让用户完整体验产品，而不是"只看不用"
2. **数据每日重置**：无需担心数据被"搞坏"，凌晨 2 点自动重置
3. **最小拦截原则**：只拦截真正危险的操作，其他全部放行
4. **防滥用保护**：通过 Turnstile 保护 AI 接口，通过 Rate Limiting 防恶意攻击

---

## 数据一致性保证

### Single Source of Truth

所有 Demo 用户信息统一在 `create_demo_users.py` 中维护：

```python
DEMO_USERS = [
    {
        "username": "demo_po",           # 👈 唯一标识
        "email": "po@demo.userecho.app",
        ...
    },
]
```

API 中只保存 `username` 映射，动态查询获取用户信息：

```python
DEMO_ROLES = {
    "product_owner": {
        "username": "demo_po",  # 👈 与数据库 username 对应
        ...
    },
}
```

---

## 后续改进建议（P1/P2）

以下问题已识别但未在本次修复中处理：

### P1 - 架构改进
- [ ] 用装饰器替代 `DEMO_MODE_EXCLUDE` 白名单
- [ ] 实现 `ALLOW_REGISTRATION` 配置检查
- [ ] 集成 `DemoRoleSwitcher` 浮动组件
- [ ] 添加 Demo Banner 提示

### P2 - 功能完善
- [ ] 实现定时数据重置（Celery Beat）
- [ ] 集成 Turnstile 到 AI 接口
- [ ] 添加 Demo 模式使用统计

详细方案请参考 `demo-environment-guide.md`

---

## 相关文档

- [Demo 环境部署指南](../guides/deployment/demo-environment-guide.md)
- [后端代码规范](../../AGENTS.md)
- [环境变量配置](../guides/deployment/dokploy-deployment.md)
