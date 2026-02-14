# Badge 显示功能测试指南

## 功能说明

在"AI 发现中心"菜单项右侧显示一个红色数字徽章，实时展示待确认主题的数量（`status='pending'`）。

## 测试步骤

### 1. 后端测试

#### 测试 API 端点

```bash
cd server
source .venv/Scripts/activate  # Windows Git Bash
python test_pending_count_api.py
```

**预期输出：**
```
============================================================
测试待确认主题数量 API
============================================================
🔍 测试获取租户 default_tenant 的待确认主题数量...
✅ 成功获取待确认主题数量: 5
✅ 数据验证通过

============================================================
测试总结
============================================================
✅ 所有测试通过
📊 待确认主题数量: 5
```

#### 测试 HTTP 接口

使用 curl 或 Postman 测试：

```bash
# 获取待确认主题数量
curl -X GET "http://localhost:8000/api/v1/app/topics/stats/pending-count" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Accept: application/json"
```

**预期响应：**
```json
{
  "code": 200,
  "msg": "Success",
  "data": {
    "count": 5
  }
}
```

### 2. 前端测试

#### 2.1 登录测试

1. 启动前端开发服务器：
   ```bash
   cd front
   pnpm dev
   ```

2. 打开浏览器访问 `http://localhost:5555`

3. 使用测试账号登录：
   - 用户名：`admin`
   - 密码：`admin123`

4. **检查点 1：登录后初始化**
   - 打开浏览器控制台（F12）
   - 查看 Network 面板
   - 应该看到一个请求：`GET /api/v1/app/topics/stats/pending-count`
   - 查看左侧菜单栏，"AI 发现中心"项应该显示数字 badge

#### 2.2 数字显示测试

| 待确认数量 | 预期显示 |
|----------|---------|
| 0        | 无 badge（隐藏） |
| 1-99     | 显示具体数字 |
| 100+     | 显示具体数字 |

#### 2.3 动态更新测试

1. 点击左侧菜单的"AI 发现中心"

2. 在待确认主题列表中，对某个主题执行操作：
   - 点击"确认"按钮 → 状态变为 `planned`
   - 或点击"忽略"按钮 → 状态变为 `ignored`

3. **检查点 2：操作后更新**
   - 查看 Network 面板
   - 应该看到新的请求：`GET /api/v1/app/topics/stats/pending-count`
   - 左侧菜单的 badge 数字应该自动减 1

4. 重复步骤 2-3，直到没有待确认主题

5. **检查点 3：数量为 0 时隐藏**
   - 当所有主题都确认或忽略后
   - badge 应该自动消失（不显示 0）

#### 2.4 刷新页面测试

1. 刷新浏览器页面（F5 或 Ctrl+R）

2. **检查点 4：持久化**
   - 重新登录后，badge 应该重新加载并显示正确数量

#### 2.5 多租户测试（如果适用）

1. 使用不同租户的账号登录

2. 每个租户应该看到各自的待确认主题数量

## 验收标准

### ✅ 功能要求

- [ ] 登录后自动显示待确认主题数量
- [ ] 数量为 0 时自动隐藏 badge
- [ ] 确认/忽略主题后自动更新数量
- [ ] 数字显示为红色背景（destructive 变体）
- [ ] 刷新页面后数量依然正确
- [ ] 多租户隔离（每个租户只看到自己的数量）

### ✅ 性能要求

- [ ] API 响应时间 < 100ms
- [ ] 不影响页面加载速度
- [ ] 不产生不必要的重复请求

### ✅ UI/UX 要求

- [ ] badge 位置合理（菜单项右侧）
- [ ] 数字清晰可读
- [ ] 颜色醒目但不刺眼
- [ ] 响应式设计（适配不同屏幕尺寸）

## 常见问题排查

### Q1: Pinia 初始化错误 ⚠️

**错误信息：**
```
Error: [🍍]: "getActivePinia()" was called but there was no active Pinia.
```

**原因：** 在路由配置的模块顶层直接调用了 `useTopicStore()`。

**解决方案：** 使用 getter 懒加载：
```typescript
// front/apps/web-antd/src/router/routes/modules/userecho.ts
meta: {
  get badge() {
    const topicStore = useTopicStore();  // ✅ 在访问时才调用
    return topicStore.pendingCount > 0 ? String(topicStore.pendingCount) : undefined;
  }
}
```

### Q2: Badge 不显示

**可能原因：**
1. 没有待确认的主题（count = 0）
2. API 请求失败
3. Store 未初始化

**排查步骤：**
```javascript
// 在浏览器控制台执行
import { useTopicStore } from '#/store';
const topicStore = useTopicStore();
console.log('Pending count:', topicStore.pendingCount);
```

### Q2: 数量不准确

**可能原因：**
1. 数据库中的 status 字段值不正确
2. 租户 ID 不匹配

**排查步骤：**
```sql
-- 在数据库中直接查询
SELECT COUNT(*) 
FROM topics 
WHERE tenant_id = 'your_tenant_id' 
  AND status = 'pending' 
  AND deleted_at IS NULL;
```

### Q3: 更新后数量未变化

**可能原因：**
1. 忘记调用 `refreshPendingCount()`
2. API 请求被缓存

**排查步骤：**
- 查看 Network 面板，确认是否发送了新的请求
- 查看请求的 Response，确认返回的数量是否正确

## 相关文件

### 后端
- `server/backend/app/userecho/api/v1/topic.py` - API 端点
- `server/backend/app/userecho/service/topic_service.py` - Service 层
- `server/test_pending_count_api.py` - 测试脚本

### 前端
- `front/apps/web-antd/src/api/userecho/topic.ts` - API 调用
- `front/apps/web-antd/src/store/topic.ts` - Pinia Store
- `front/apps/web-antd/src/store/auth.ts` - 登录初始化
- `front/apps/web-antd/src/router/routes/modules/userecho.ts` - 路由配置
- `front/apps/web-antd/src/views/userecho/discovery/index.vue` - Discovery 页面

## 自动化测试（TODO）

未来可以添加：
- E2E 测试（Playwright/Cypress）
- 单元测试（Vitest）
- API 集成测试（pytest）
