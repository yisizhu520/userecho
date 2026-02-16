# 租户配置系统设计文档

## 系统概述

租户配置系统是一个通用的、可扩展的租户级配置管理框架，支持多种业务功能的配置需求。

**核心设计理念**：

> "一个表解决所有租户配置问题"  
> ——  使用分组 JSON 存储，避免为每个功能创建独立配置表

## 架构设计

### 前端菜单结构

```
回响 (UserEcho)
├─ 反馈列表          /app/feedback/list
├─ AI 发现中心       /app/ai/discovery
├─ 导入反馈          /app/feedback/import
├─ 需求主题          /app/topic/list
├─ 客户管理          /app/customer
└─ 设置              /app/settings
   └─ 聚类策略       /app/settings/clustering
```

**设计原则**：
- 业务功能（反馈、主题、客户）平铺在一级菜单，快速访问
- 配置功能（聚类、通知等）归入"设置"分组，避免与业务菜单混淆
- 所有文本使用多语言配置（`$t()`），消除硬编码

### 系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│                        前端层 (Vue 3)                         │
├─────────────────────────────────────────────────────────────┤
│  - 聚类配置页面 (clustering-config.vue)                      │
│  - 未来：通知配置页面、展示配置页面...                        │
└───────────────────────────┬─────────────────────────────────┘
                            │ API 调用
┌───────────────────────────┴─────────────────────────────────┐
│                      API 层 (FastAPI)                        │
├─────────────────────────────────────────────────────────────┤
│  - /api/v1/app/config/clustering/*  (聚类配置 API)           │
│  - 未来：/api/v1/app/config/notification/* ...                │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────┴─────────────────────────────────┐
│                      服务层 (Service)                        │
├─────────────────────────────────────────────────────────────┤
│  ┌───────────────────────────────────────────────────────┐  │
│  │  TenantConfigService (通用配置服务)                    │  │
│  │  - get_config()      │  - set_config()                │  │
│  │  - 内存缓存          │  - 缓存失效                     │  │
│  └───────────────────────┬───────────────────────────────┘  │
│                          │ 继承/调用                         │
│  ┌───────────────────────┴───────────────────────────────┐  │
│  │  ClusteringConfigService (聚类配置专用服务)            │  │
│  │  - get_clustering_config()                            │  │
│  │  - update_preset()                                    │  │
│  │  - preview_config_effect()                            │  │
│  └───────────────────────────────────────────────────────┘  │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────┴─────────────────────────────────┐
│                    数据访问层 (CRUD)                         │
├─────────────────────────────────────────────────────────────┤
│  - TenantConfigDAO                                           │
│    - get_by_group()  (查询指定配置组)                        │
│    - upsert()        (创建或更新配置)                         │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────┴─────────────────────────────────┐
│               数据库层 (PostgreSQL + JSON)                   │
├─────────────────────────────────────────────────────────────┤
│  userecho_tenant_config 表                                   │
│  ┌────────────┬──────────────┬──────────────┐               │
│  │ tenant_id  │ config_group │ config_data  │               │
│  ├────────────┼──────────────┼──────────────┤               │
│  │ tenant-001 │ clustering   │ { JSON }     │               │
│  │ tenant-001 │ notification │ { JSON }     │               │
│  │ tenant-002 │ clustering   │ { JSON }     │               │
│  └────────────┴──────────────┴──────────────┘               │
│  唯一约束: (tenant_id, config_group)                         │
└─────────────────────────────────────────────────────────────┘
```

## 数据库设计

### 表结构

```sql
CREATE TABLE userecho_tenant_config (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    config_group VARCHAR(32) NOT NULL,  -- 配置分组
    config_data JSON NOT NULL,          -- 配置数据
    is_active BOOLEAN DEFAULT TRUE,
    created_time TIMESTAMP DEFAULT NOW(),
    updated_time TIMESTAMP,
    deleted_at TIMESTAMP,               -- 软删除
    del_flag BOOLEAN DEFAULT FALSE,
    
    CONSTRAINT uq_tenant_config UNIQUE (tenant_id, config_group)
);

CREATE INDEX idx_tenant_group_active ON userecho_tenant_config 
    (tenant_id, config_group, is_active);
```

### 配置数据示例

#### 聚类配置 (config_group='clustering')

```json
{
  "preset_mode": "standard",
  "similarity_threshold": 0.85,
  "min_samples": 2,
  "min_silhouette": 0.3,
  "max_noise_ratio": 0.5
}
```

#### 未来的通知配置 (config_group='notification')

```json
{
  "email_enabled": true,
  "webhook_url": "https://hooks.example.com/webhook",
  "notify_on_new_topic": true,
  "digest_frequency": "daily"
}
```

## 聚类配置系统

### 预设模式设计

**设计目标**：让用户通过业务场景选择配置，无需理解算法参数。

#### 预设模式映射表

| 预设模式 | 显示名称 | 技术参数 | 适用场景 |
|---------|---------|---------|---------|
| `strict` | 严格聚类 | threshold=0.90, min_samples=3 | 产品初期，反馈类型明确 |
| `standard` | 标准聚类 | threshold=0.85, min_samples=2 | 日常使用（推荐） |
| `relaxed` | 宽松聚类 | threshold=0.75, min_samples=2 | 反馈量大，需要快速归纳 |

#### 预设模式常量定义

文件：`server/backend/app/userecho/constants.py`

```python
CLUSTERING_PRESETS = {
    'strict': {
        'display_name': '严格聚类',
        'description': '只将高度相似的反馈聚在一起...',
        'use_case': '适用于：产品初期、反馈类型明确...',
        'params': {
            'similarity_threshold': 0.90,
            'min_samples': 3,
            'min_silhouette': 0.4,
            'max_noise_ratio': 0.6,
        }
    },
    # ...
}
```

### 配置读取流程

```
┌──────────────────┐
│  聚类服务启动     │
└────────┬─────────┘
         │
         ▼
┌─────────────────────────────┐
│ 调用 ClusteringConfigService │
│ .get_clustering_config()    │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│ TenantConfigService          │
│ 检查内存缓存                  │
└────────┬────────────────────┘
         │
    ┌────┴────┐
    │ 缓存命中？│
    └────┬────┘
         │
    ┌────┴────┐
    NO        YES
    │         │
    ▼         ▼
┌───────┐ ┌──────────┐
│ 查询DB │ │ 返回缓存  │
└───┬───┘ └──────────┘
    │
    ▼
┌───────────┐
│ 写入缓存   │
└───────────┘
```

### 配置更新流程

```
┌──────────────────┐
│  用户选择预设模式 │
└────────┬─────────┘
         │
         ▼
┌─────────────────────────────┐
│ API: POST /clustering/preset │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│ ClusteringConfigService      │
│ .update_preset()             │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│ 从 CLUSTERING_PRESETS       │
│ 展开技术参数                  │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│ TenantConfigService          │
│ .set_config()                │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│ TenantConfigDAO.upsert()     │
│ 数据库 UPSERT 操作           │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│ 清除内存缓存                 │
└─────────────────────────────┘
```

## API 设计

### 聚类配置 API

#### 1. 获取预设模式列表

```
GET /api/v1/app/config/clustering/presets
```

**响应示例**：

```json
{
  "code": 200,
  "data": {
    "strict": {
      "display_name": "严格聚类",
      "description": "...",
      "use_case": "..."
    },
    "standard": { ... },
    "relaxed": { ... }
  }
}
```

#### 2. 获取当前配置

```
GET /api/v1/app/config/clustering
```

**响应示例**：

```json
{
  "code": 200,
  "data": {
    "preset_mode": "standard",
    "similarity_threshold": 0.85,
    "min_samples": 2,
    "min_silhouette": 0.3,
    "max_noise_ratio": 0.5
  }
}
```

#### 3. 更新预设模式

```
POST /api/v1/app/config/clustering/preset
Content-Type: application/json

{
  "preset_mode": "strict"
}
```

#### 4. 预览配置效果（智能验证）

```
POST /api/v1/app/config/clustering/preview
Content-Type: application/json

{
  "preset_mode": "relaxed"
}
```

**响应示例**：

```json
{
  "code": 200,
  "data": {
    "status": "success",
    "test_samples": 20,
    "preview": {
      "clusters_count": 3,
      "clusters_range": "2-5",
      "coverage_rate": 0.75,
      "coverage_percentage": "75%",
      "quality_rating": "良好",
      "silhouette_score": 0.45,
      "noise_ratio": 0.25
    }
  }
}
```

## 扩展指南

### 添加新的配置模块

假设要添加"通知配置"模块：

#### 步骤 1：定义默认配置

在 `server/backend/app/userecho/constants.py` 添加：

```python
DEFAULT_NOTIFICATION_CONFIG = {
    'email_enabled': True,
    'webhook_url': None,
    'notify_on_new_topic': True,
    'digest_frequency': 'daily'
}
```

#### 步骤 2：创建专用服务

创建 `server/backend/app/userecho/service/notification_config_service.py`：

```python
class NotificationConfigService:
    CONFIG_GROUP = 'notification'
    
    async def get_notification_config(self, db: AsyncSession, tenant_id: str):
        return await tenant_config_service.get_config(
            db=db,
            tenant_id=tenant_id,
            config_group=self.CONFIG_GROUP,
            default=DEFAULT_NOTIFICATION_CONFIG,
        )
    
    async def update_notification_config(self, db, tenant_id, config_data):
        await tenant_config_service.set_config(
            db=db,
            tenant_id=tenant_id,
            config_group=self.CONFIG_GROUP,
            config_data=config_data,
        )

notification_config_service = NotificationConfigService()
```

#### 步骤 3：创建 API 端点

在 `server/backend/app/userecho/api/v1/tenant_config.py` 添加：

```python
@router.get('/notification', summary='获取通知配置')
async def get_notification_config(
    db: CurrentSession,
    tenant_id: str = CurrentTenantId,
):
    config = await notification_config_service.get_notification_config(db, tenant_id)
    return response_base.success(data=config)

@router.put('/notification', summary='更新通知配置')
async def update_notification_config(
    config_data: dict,
    db: CurrentSessionTransaction,
    tenant_id: str = CurrentTenantId,
):
    await notification_config_service.update_notification_config(
        db, tenant_id, config_data
    )
    return response_base.success()
```

#### 步骤 4：创建前端页面

创建 `front/apps/web-antd/src/views/userecho/settings/notification-config.vue`

#### 步骤 5：注册路由

在 `front/apps/web-antd/src/router/routes/modules/userecho.ts` 的 `Settings` 子路由中添加：

```typescript
{
  name: 'NotificationConfig',
  path: '/app/settings/notification',
  component: () => import('#/views/userecho/settings/notification-config.vue'),
  meta: {
    icon: 'lucide:bell',
    title: $t('page.userecho.settings.notification'),
  },
}
```

#### 步骤 6：更新多语言配置

在 `front/apps/web-antd/src/locales/langs/zh-CN/page.json` 和 `en-US/page.json` 中添加：

```json
{
  "page": {
    "userecho": {
      "settings": {
        "title": "设置",
        "clustering": "聚类策略",
        "notification": "通知配置"
      }
    }
  }
}
```

**无需修改数据库表结构！**

### 配置组命名规范

建议使用以下命名约定：

- `clustering` - 聚类相关配置
- `notification` - 通知配置
- `display` - 展示配置
- `export` - 导出配置
- `integration` - 第三方集成配置

使用小写字母和下划线，保持简洁。

## 性能优化

### 缓存策略

**当前实现**：使用 Python 字典作为内存缓存

```python
self._cache[f"{tenant_id}:{config_group}"] = config_data
```

**优点**：
- 简单快速
- 无额外依赖

**缺点**：
- 仅限单机
- 重启丢失

**生产环境建议**：使用 Redis 缓存

```python
async def get_config(self, db, tenant_id, config_group, default=None):
    # 1. 尝试从 Redis 读取
    cache_key = f"tenant_config:{tenant_id}:{config_group}"
    cached = await redis_client.get(cache_key)
    if cached:
        return json.loads(cached)
    
    # 2. 从数据库读取
    config = await tenant_config_dao.get_by_group(db, tenant_id, config_group)
    
    if config:
        # 3. 写入 Redis（TTL 1小时）
        await redis_client.setex(cache_key, 3600, json.dumps(config.config_data))
        return config.config_data
    
    return default or {}
```

### 数据库索引优化

已创建复合索引：

```sql
CREATE INDEX idx_tenant_group_active ON userecho_tenant_config 
    (tenant_id, config_group, is_active);
```

查询性能：O(1) 通过唯一约束和索引。

## 监控与日志

### 关键日志点

1. **配置读取**：
   ```python
   log.info(f'Using clustering config for tenant {tenant_id}: preset={config["preset_mode"]}')
   ```

2. **配置更新**：
   ```python
   log.info(f'Updated config for tenant {tenant_id}, group: {config_group}')
   ```

3. **缓存操作**：
   ```python
   log.debug(f'Cleared cache for {cache_key}')
   ```

### 监控指标

建议监控：
- 配置读取延迟（p50, p95, p99）
- 配置更新频率
- 缓存命中率
- 数据库查询耗时

## 安全考虑

### 权限控制

配置 API 通过 `CurrentTenantId` 依赖自动进行租户隔离：

```python
async def get_clustering_config(
    db: CurrentSession,
    tenant_id: str = CurrentTenantId,  # 自动注入租户ID
):
    ...
```

### 数据验证

预设模式验证：

```python
if preset_mode not in CLUSTERING_PRESETS:
    raise errors.ForbiddenError(msg=f'Invalid preset mode: {preset_mode}')
```

### 审计日志

建议记录配置变更历史：
- 谁（用户 ID）
- 何时（时间戳）
- 改了什么（变更前后对比）

可在 `config_data` 中添加 `updated_by` 和 `updated_at` 字段。

## 故障处理

### 数据库不可用

```python
try:
    config = await tenant_config_dao.get_by_group(...)
except Exception as e:
    log.error(f'Failed to load config: {e}')
    return default  # Fallback 到默认配置
```

### 缓存失效

定期清理过期缓存（如使用 Redis TTL），避免内存泄漏。

## 最佳实践

1. **配置粒度**：按功能模块分组，不要所有配置塞在一个 JSON 中
2. **默认值**：始终提供合理的默认配置
3. **文档化**：为每个配置项添加注释说明
4. **版本控制**：可在 `config_data` 中添加 `version` 字段
5. **迁移策略**：配置结构变更时，提供兼容逻辑

## 常见问题

### Q: 为什么不为每个功能创建独立配置表？

**A**: 
- 避免表膨胀（每个功能一个表 → 随着功能增加，表数量爆炸）
- 通用表 + JSON 提供更好的扩展性
- 简化 CRUD 逻辑（只需一套代码）

### Q: JSON 字段的查询性能如何？

**A**: 
- PostgreSQL 的 JSON 字段支持索引（如 GIN 索引）
- 本系统主要通过 `(tenant_id, config_group)` 查询，不需要 JSON 索引
- 查询性能: O(1) 通过唯一约束

### Q: 如何处理配置迁移（字段变更）？

**A**: 
```python
# 兼容旧配置
config = await get_config(...)
if 'new_field' not in config:
    config['new_field'] = default_value
```

### Q: 缓存何时失效？

**A**: 
- 显式更新配置时，立即清除缓存
- 生产环境使用 Redis TTL 自动过期（建议 1 小时）
- 重启应用时，内存缓存全部清空

## 相关文档

- [菜单权限配置指南](./menu-permission-guide.md) - **重要**：如何让配置页面在左侧菜单栏显示
- [聚类配置测试指南](../testing/clustering-config-test-guide.md)
- [聚类实现详解](./clustering-implementation-review.md)
- [API 文档](http://localhost:8000/docs)

