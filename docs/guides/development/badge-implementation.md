# AI 发现中心 Badge 实现方案

## 📋 当前实现（✅ 已完成）

已为 AI 发现中心添加**动态数字 badge**，实时显示待确认主题数量。

### 实现架构

```
后端统计 → API 接口 → Pinia Store → 路由配置 → 菜单显示
    ↓           ↓           ↓            ↓
 数据库      REST API    状态管理      动态 Badge
```

### 后端实现

**1. 统计接口**

```python
# server/backend/app/userecho/api/v1/topic.py

# ⚠️ 重要：具体路径必须在参数化路径之前定义
@router.get('/stats/pending-count', summary='获取待确认主题数量')
async def get_pending_count(
    db: CurrentSession,
    tenant_id: str = CurrentTenantId,
):
    """获取待确认主题数量（用于 badge 显示）"""
    count = await topic_service.get_pending_count(db=db, tenant_id=tenant_id)
    return response_base.success(data={'count': count})

# ✅ 参数化路径在后面
@router.get('/{topic_id}', summary='获取主题详情')
async def get_topic_detail(topic_id: str, ...):
    ...
```

**⚠️ 关键点：路由顺序问题**

FastAPI 按定义顺序匹配路由：

```python
# ❌ 错误：参数化路径在前，会匹配所有路径
@router.get('/{topic_id}')           # 会匹配 /stats/pending-count！
@router.get('/stats/pending-count')   # 永远不会被匹配

# ✅ 正确：具体路径在前
@router.get('/stats/pending-count')   # 先匹配具体路径
@router.get('/{topic_id}')           # 再匹配参数化路径
```

**2. Service 层**

```python
# server/backend/app/userecho/service/topic_service.py
async def get_pending_count(self, db: AsyncSession, tenant_id: str) -> int:
    """获取待确认主题数量"""
    return await crud_topic.count(
        db=db,
        tenant_id=tenant_id,
        status='pending'
    )
```

### 前端实现

**1. API 调用**

```typescript
// front/apps/web-antd/src/api/userecho/topic.ts
export async function getPendingTopicCount() {
  return requestClient.get<{ count: number }>('/api/v1/app/topics/stats/pending-count');
}
```

**2. Pinia Store**

```typescript
// front/apps/web-antd/src/store/topic.ts
export const useTopicStore = defineStore('topic', () => {
    const pendingCount = ref<number>(0);

    async function refreshPendingCount() {
        const result = await getPendingTopicCount();
        pendingCount.value = result.count;
    }

    return { pendingCount, refreshPendingCount };
});
```

**3. 路由配置**

```typescript
// front/apps/web-antd/src/router/routes/modules/userecho.ts
import { useTopicStore } from '#/store';

{
  name: 'AIDiscovery',
  path: '/app/ai/discovery',
  meta: {
    icon: 'lucide:sparkles',
    order: 1,
    title: $t('page.userecho.discovery.title'),
    // ⚠️ 重要：使用 getter 懒加载 store，避免 Pinia 初始化时机问题
    get badge() {
      const topicStore = useTopicStore();
      const count = topicStore.pendingCount;
      return count > 0 ? String(count) : undefined;
    },
    badgeType: 'normal',        // 数字类型
    badgeVariants: 'destructive', // 红色
  },
}
```

**⚠️ 关键点：为什么使用 getter？**

```typescript
// ❌ 错误：模块加载时就调用，Pinia 还没初始化
const topicStore = useTopicStore();
const pendingBadge = computed(() => topicStore.pendingCount);

// ✅ 正确：使用 getter 懒加载，在访问时才调用
get badge() {
  const topicStore = useTopicStore();  // 此时 Pinia 已初始化
  return topicStore.pendingCount > 0 ? String(topicStore.pendingCount) : undefined;
}
```

**4. 初始化和刷新**

```typescript
// front/apps/web-antd/src/store/auth.ts
// 登录后初始化
async function authLogin() {
  // ... 登录逻辑
  const topicStore = useTopicStore();
  topicStore.refreshPendingCount(); // ✅ 初始化 badge
}

// front/apps/web-antd/src/views/userecho/discovery/index.vue
// 用户操作后刷新
async function confirmTopic(t: Topic) {
  await updateTopicStatus(t.id, { status: 'planned' });
  await topicStore.refreshPendingCount(); // ✅ 更新 badge
}
```

## 🎨 Badge 类型说明

项目支持两种 badge 展示方式：

### 1. 小红点 (dot)
```typescript
meta: {
  badgeType: 'dot',
  badgeVariants: 'destructive', // 红色 | 'primary' | 'default' 等
}
```
- 显示一个带动画的小红点（ping 效果）
- 适合提示"有新内容"或"需要关注"

### 2. 数字/文本 (normal) - ✅ 当前使用
```typescript
meta: {
  badge: '5',                   // 显示的文本或数字
  badgeType: 'normal',
  badgeVariants: 'destructive', // 背景颜色
}
```
- 显示具体的数字或文本
- 适合显示具体数量

## 🔄 数据流

### 初始化流程
```
用户登录
  → authLogin()
    → topicStore.refreshPendingCount()
      → getPendingTopicCount() API
        → 后端查询 count(status='pending')
          → 返回数量
            → 更新 pendingCount
              → computed 触发
                → badge 显示
```

### 更新流程
```
用户操作（确认/忽略主题）
  → confirmTopic() / ignoreTopic()
    → updateTopicStatus() API
      → topicStore.refreshPendingCount()
        → badge 自动更新
```

## 📝 技术细节

### Badge 组件位置
- `front/packages/@core/ui-kit/menu-ui/src/components/menu-badge.vue`
- `front/packages/@core/ui-kit/menu-ui/src/components/menu-badge-dot.vue`

### 类型定义
- `front/packages/@core/base/typings/src/menu-record.ts`
- `front/packages/@core/base/typings/src/vue-router.d.ts`

### 颜色变体
- `destructive`: 红色（危险/警告）- ✅ 当前使用
- `primary`: 主题色
- `success`: 绿色
- `warning`: 黄色
- `default`: 默认色

## ⚡ 性能优化

### 后端优化
- ✅ 使用 `count()` 查询，而不是获取全部列表
- ✅ 只查询必要的字段（status='pending'）
- ✅ 利用数据库索引（tenant_id, status, deleted_at）

### 前端优化
- ✅ 使用 Pinia Store 集中管理状态
- ✅ 使用 `computed` 自动响应式更新
- ✅ 只在必要时刷新（登录、用户操作）

## 🎯 扩展建议

### 方案 A：定时轮询（可选）
```typescript
// front/apps/web-antd/src/store/topic.ts
let refreshInterval: NodeJS.Timeout | null = null;

function startAutoRefresh(intervalMs: number = 60000) {
  refreshInterval = setInterval(() => {
    refreshPendingCount();
  }, intervalMs);
}

function stopAutoRefresh() {
  if (refreshInterval) {
    clearInterval(refreshInterval);
    refreshInterval = null;
  }
}
```

### 方案 B：WebSocket 实时更新（最佳体验）
```typescript
// front/apps/web-antd/src/store/websocket.ts
function handleMessage(event: MessageEvent) {
  const data = JSON.parse(event.data);
  
  if (data.type === 'topic_status_changed') {
    const topicStore = useTopicStore();
    topicStore.refreshPendingCount(); // ✅ 实时更新
  }
}
```

## 🐛 常见问题

### Q1: API 请求 404 或返回错误 ⚠️

**症状：** 浏览器 Network 面板显示 `/api/v1/app/topics/stats/pending-count` 返回 404 或 "主题不存在"。

**原因：** FastAPI 路由顺序错误，参数化路径 `/{topic_id}` 在具体路径 `/stats/pending-count` 之前。

**解决方案：** 调整路由顺序，具体路径在前：
```python
# ✅ 正确顺序
@router.get('/stats/pending-count')  # 第 61 行
@router.get('/{topic_id}')           # 第 76 行
```

### Q2: Pinia 初始化错误 ⚠️

**错误信息：**
```
Error: [🍍]: "getActivePinia()" was called but there was no active Pinia.
Are you trying to use a store before calling "app.use(pinia)"?
```

**原因：** 在模块顶层调用了 `useTopicStore()`，此时 Pinia 还没初始化。

**解决方案：**
```typescript
// ❌ 错误：在模块加载时就调用
const topicStore = useTopicStore();

// ✅ 正确：使用 getter 懒加载
get badge() {
  const topicStore = useTopicStore();  // 访问时才调用
  return topicStore.pendingCount > 0 ? String(topicStore.pendingCount) : undefined;
}
```

### Q2: Badge 不显示？

**检查以下几点：**
1. 是否登录成功并初始化？
2. 是否有待确认的主题？
3. 浏览器控制台是否有 API 错误？

### Q3: Badge 数量不更新？

**确保在用户操作后调用了：**
```typescript
await topicStore.refreshPendingCount();
```

### Q4: Badge 显示 0？

这是正常的，当没有待确认主题时 badge 会隐藏（返回 `undefined`）

## 📚 相关文件

### 后端
- `server/backend/app/userecho/api/v1/topic.py` - API 端点
- `server/backend/app/userecho/service/topic_service.py` - Service 层
- `server/backend/app/userecho/crud/base.py` - CRUD count 方法

### 前端
- `front/apps/web-antd/src/api/userecho/topic.ts` - API 调用
- `front/apps/web-antd/src/store/topic.ts` - Pinia Store
- `front/apps/web-antd/src/store/auth.ts` - 登录初始化
- `front/apps/web-antd/src/router/routes/modules/userecho.ts` - 路由配置
- `front/apps/web-antd/src/views/userecho/discovery/index.vue` - Discovery 页面
