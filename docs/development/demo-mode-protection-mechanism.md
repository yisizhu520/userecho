# Demo 模式保护机制设计

## 设计哲学

> "Demo 环境应该让用户**完整体验产品**，而不是只能'看'不能'用'。"

### 核心原则

1. **用户体验优先** - 允许所有正常业务操作
2. **最小拦截原则** - 只拦截真正危险的操作
3. **数据可恢复性** - 数据每日自动重置
4. **防滥用保护** - Turnstile + Rate Limiting

---

## 允许的操作 ✅

用户在 Demo 模式下可以**完整体验**以下功能：

### 核心业务功能
- ✅ 创建、编辑、删除反馈
- ✅ 创建、编辑、删除议题
- ✅ 创建、编辑、删除客户
- ✅ 触发 AI 聚类分析
- ✅ 生成 AI 洞察报告
- ✅ 修改看板配置
- ✅ 管理标签和分类
- ✅ 导入导出数据

### 账号操作
- ✅ 登录、登出
- ✅ 角色快速切换
- ✅ 修改个人信息
- ✅ 查看所有数据

---

## 禁止的操作 ❌

只拦截**真正危险**的操作：

### 删除预置数据
- ❌ 删除 Demo 预置用户（demo_po, demo_ops, demo_admin）
- ❌ 删除默认租户（default-tenant）

### 系统级配置
- ❌ 修改系统级配置（如数据库、邮件服务等）

**仅此而已！** 其他所有操作都允许。

---

## 实现细节

### 代码实现

```python
# server/backend/utils/demo_site.py

async def demo_site(request: Request) -> None:
    """
    Demo 模式保护中间件
    
    设计原则：
    1. 允许用户完整体验所有核心功能
    2. 只拦截真正危险的操作
    3. 数据每日自动重置，无需担心被"搞坏"
    """
    if not settings.DEMO_MODE:
        return

    method = request.method
    path = request.url.path

    # Demo 模式下禁止的危险操作（黑名单）
    forbidden_patterns = [
        # 禁止删除 Demo 预置用户
        (lambda m, p: m == "DELETE" 
         and "/api/v1/sys/user/" in p 
         and any(u in p for u in ["demo_po", "demo_ops", "demo_admin"])),
        
        # 禁止删除默认租户
        (lambda m, p: m == "DELETE" 
         and "/api/v1/tenant/default-tenant" in p),
        
        # 禁止修改系统级配置
        (lambda m, p: m in ["PUT", "PATCH", "DELETE"] 
         and "/api/v1/config/system" in p),
    ]

    for pattern in forbidden_patterns:
        if pattern(method, path):
            raise errors.ForbiddenError(
                msg="演示环境下禁止删除预置数据或修改系统配置"
            )
```

### 关键设计

#### 1. 黑名单 vs 白名单

```python
# ❌ 旧方案：白名单（维护地狱）
DEMO_MODE_EXCLUDE = {
    ("POST", "/api/v1/auth/login"),
    ("POST", "/api/v1/auth/logout"),
    ("POST", "/api/v1/feedback/create"),  # 需要手动添加
    ("POST", "/api/v1/topic/create"),     # 需要手动添加
    ("POST", "/api/v1/clustering/run"),   # 需要手动添加
    # ... 数百个端点需要维护
}

# ✅ 新方案：黑名单（极简维护）
forbidden_patterns = [
    # 只需维护 3-5 个真正危险的操作
    (lambda m, p: m == "DELETE" and "demo_" in p),
    (lambda m, p: m == "DELETE" and "default-tenant" in p),
]
```

#### 2. 使用 Lambda 表达式

**优点**：
- 灵活的模式匹配
- 易于扩展
- 可读性好

```python
# 使用 lambda 匹配多个用户名
(lambda m, p: any(u in p for u in ["demo_po", "demo_ops", "demo_admin"]))

# 匹配多种 HTTP 方法
(lambda m, p: m in ["PUT", "PATCH", "DELETE"])
```

---

## 数据重置机制

### 定时重置

```bash
# 每日凌晨 2 点自动重置
0 2 * * * cd /path/to/server/backend && ./init_demo_environment.sh --reset --silent
```

### 重置内容

1. 删除并重建 Demo 用户
2. 删除所有业务数据（反馈、议题、客户等）
3. 重新初始化示例数据
4. 保留系统基础配置

---

## 防滥用保护

### 1. Turnstile 人机验证

保护 AI 相关接口：

```python
@router.post("/clustering/run", dependencies=[DependsTurnstile])
async def run_clustering(...):
    ...

@router.post("/insight/generate", dependencies=[DependsTurnstile])
async def generate_insight(...):
    ...
```

### 2. Rate Limiting

限制请求频率：

```python
@router.post("/feedback/create", dependencies=[RateLimiter(times=10, minutes=1)])
async def create_feedback(...):
    ...
```

### 3. 日志监控

记录所有 Demo 环境的操作：

```python
log.info(f"Demo user {username} performed {method} {path}")
```

---

## 最佳实践

### ✅ 推荐做法

1. **默认允许** - 新增业务端点无需手动添加到白名单
2. **明确禁止** - 只在真正危险的操作上添加拦截
3. **用户体验** - 让用户自由探索，不要过度限制
4. **数据隔离** - Demo 环境使用独立的数据库和 Redis

### ❌ 避免陷阱

1. **不要使用白名单** - 维护成本太高，容易遗漏
2. **不要拦截所有写操作** - Demo 变成"只读展示"
3. **不要担心数据被破坏** - 数据每日重置
4. **不要过度保护** - 信任用户

---

## 扩展保护规则

如果需要添加新的保护规则：

```python
# 在 forbidden_patterns 中添加新模式
forbidden_patterns = [
    # 现有规则...
    
    # 示例：禁止导出超过 1000 条数据
    (lambda m, p: "export" in p and request.query_params.get("limit", 0) > 1000),
    
    # 示例：禁止批量删除操作
    (lambda m, p: m == "DELETE" and "batch" in p),
    
    # 示例：禁止修改 Demo 用户的角色
    (lambda m, p: m in ["PUT", "PATCH"] 
     and "/api/v1/sys/user/" in p 
     and "role" in p
     and any(u in p for u in ["demo_po", "demo_ops", "demo_admin"])),
]
```

---

## 测试清单

部署前验证：

- [ ] 用户可以创建反馈
- [ ] 用户可以创建议题
- [ ] 用户可以触发 AI 聚类
- [ ] 用户可以生成洞察
- [ ] 用户可以修改看板配置
- [ ] 用户**无法**删除 Demo 预置用户
- [ ] 用户**无法**删除默认租户
- [ ] Turnstile 验证正常工作
- [ ] 数据每日自动重置

---

## 相关文档

- [Demo 环境部署指南](../guides/deployment/demo-environment-guide.md)
- [P0 问题修复总结](./demo-mode-p0-fixes.md)
- [后端代码规范](../../AGENTS.md)
