# Feedalyze 实施进度报告

> **更新时间:** 2025-12-21  
> **状态:** 后端核心基础设施已完成 ✅

---

## 📊 总体进度

- [x] 阶段一：环境准备与配置
- [x] 阶段二：数据库模型开发
- [x] 阶段三：Pydantic Schema 开发
- [x] 阶段四：CRUD 层开发
- [x] 阶段五：AI 工具模块开发
- [ ] 阶段六：Service 层开发 (待完成)
- [ ] 阶段七：API 路由开发 (待完成)
- [ ] 阶段八：前端开发 (待完成)

**完成率:** 约 60%

---

## ✅ 已完成的工作

### 1. 环境配置

**文件修改:**
- `server/backend/core/conf.py` - 添加 Feedalyze 配置项
- `server/backend/.env.example` - 创建环境变量模板

**新增配置:**
```python
# AI 配置
DEEPSEEK_API_KEY: str
OPENAI_API_KEY: str
AI_DEFAULT_PROVIDER: str = 'deepseek'

# 聚类配置
CLUSTERING_SIMILARITY_THRESHOLD: float = 0.75
CLUSTERING_MIN_SAMPLES: int = 2

# 导入配置
IMPORT_MAX_FILE_SIZE: int = 10485760
IMPORT_ALLOWED_EXTENSIONS: list[str] = ['.xlsx', '.xls', '.csv']
```

---

### 2. 数据库模型 (7 个模型)

**目录:** `server/backend/app/userecho/model/`

| 模型 | 文件 | 描述 |
|------|------|------|
| Tenant | `tenant.py` | 租户表 |
| Customer | `customer.py` | 客户表 |
| Feedback | `feedback.py` | 反馈表（核心） |
| Topic | `topic.py` | 需求主题表（聚类结果） |
| PriorityScore | `priority_score.py` | 优先级评分表 |
| StatusHistory | `status_history.py` | 状态变更历史表 |
| ManualAdjustment | `manual_adjustment.py` | 人工调整记录表 |

**关键特性:**
- ✅ 多租户支持（tenant_id）
- ✅ 软删除（deleted_at）
- ✅ 自动时间戳（created_time, updated_time）
- ✅ 业务约束（CHECK CONSTRAINT）

**User 模型改造:**
- `server/backend/app/admin/model/user.py` - 添加 `tenant_id` 字段

---

### 3. Pydantic Schema (6 个模块)

**目录:** `server/backend/app/userecho/schema/`

每个模块包含：
- `{Model}Base` - 基础字段
- `{Model}Create` - 创建参数
- `{Model}Update` - 更新参数
- `{Model}Out` - 输出模型

**特殊 Schema:**
- `FeedbackImportRow` - Excel 导入数据格式
- `FeedbackListParams` - 反馈列表查询参数
- `TopicDetailOut` - 主题详情（包含关联数据）
- `TopicListParams` - 主题列表查询参数
- `TopicStatusUpdateParam` - 状态更新参数

---

### 4. CRUD 层 (基类 + 6 个业务 CRUD)

**目录:** `server/backend/app/userecho/crud/`

**基类:** `base.py` - `TenantAwareCRUD`
- 自动过滤租户（tenant_id）
- 自动过滤软删除（deleted_at IS NULL）
- 支持创建、更新、删除、查询、计数

**业务 CRUD:**
| CRUD | 文件 | 特殊方法 |
|------|------|----------|
| CRUDTenant | `crud_tenant.py` | - |
| CRUDCustomer | `crud_customer.py` | `get_by_name()` (导入去重) |
| CRUDFeedback | `crud_feedback.py` | `get_unclustered()`, `batch_update_topic()`, `get_list_with_relations()` |
| CRUDTopic | `crud_topic.py` | `get_with_feedbacks()`, `update_status()`, `increment_feedback_count()`, `get_list_sorted()` |
| CRUDPriorityScore | `crud_priority.py` | `get_by_topic()`, `upsert()` (自动计算总分) |
| CRUDStatusHistory | `crud_status_history.py` | `create_history()`, `get_by_topic()` |

---

### 5. AI 工具模块

**文件:** `server/backend/utils/ai_client.py`

**功能:**
- ✅ 多模型支持（DeepSeek + OpenAI）
- ✅ 自动降级（DeepSeek 失败 → OpenAI）
- ✅ 重试机制
- ✅ 三大核心功能：
  - `get_embedding()` - 获取文本向量（768维）
  - `generate_topic_title()` - 生成主题标题和分类
  - `generate_summary()` - 生成20字摘要

**使用示例:**
```python
from backend.utils.ai_client import ai_client

# 获取 embedding
embedding = await ai_client.get_embedding("用户反馈内容")

# 生成主题
topic_data = await ai_client.generate_topic_title([
    "登录太慢了",
    "希望登录速度能快一些"
])
# 返回: {'title': '登录速度优化', 'category': 'performance', 'is_urgent': False}
```

---

### 6. 聚类算法模块

**文件:** `server/backend/utils/clustering.py`

**算法:** DBSCAN (基于密度的聚类)

**核心方法:**
- `cluster()` - 对 embedding 向量进行聚类
- `find_similar_feedbacks()` - 查找最相似的反馈
- `calculate_cluster_quality()` - 计算聚类质量指标

**参数配置:**
- `similarity_threshold` - 相似度阈值 (默认 0.75)
- `min_samples` - 最小样本数 (默认 2)

**使用示例:**
```python
from backend.utils.clustering import clustering_engine
import numpy as np

# 假设有 10 条反馈的 embedding
embeddings = np.array([[...], [...], ...])  # shape: (10, 768)

# 执行聚类
labels = clustering_engine.cluster(embeddings)
# 返回: [0, 0, 1, 1, 1, -1, 2, 2, 0, -1]
#  0, 1, 2 是聚类标签，-1 是噪声点
```

---

## 📋 待完成的工作

### 7. Service 层 (核心业务逻辑)

**待创建文件:**
- `app/userecho/service/feedback_service.py`
- `app/userecho/service/customer_service.py`
- `app/userecho/service/topic_service.py`
- `app/userecho/service/clustering_service.py` ⭐ 核心
- `app/userecho/service/import_service.py` ⭐ 核心
- `app/userecho/service/priority_service.py`

**关键功能:**
- **clustering_service**: 
  - `trigger_clustering()` - 触发聚类任务
  - 完整流程：获取未聚类反馈 → 获取 embedding → 聚类 → 生成主题 → 更新反馈

- **import_service**:
  - `import_excel()` - 导入 Excel 文件
  - `_get_or_create_customer()` - 获取或创建客户
  - 错误处理和进度追踪

---

### 8. API 路由

**待创建文件:**
- `app/userecho/api/router.py` - 主路由
- `app/userecho/api/v1/tenant.py`
- `app/userecho/api/v1/customer.py`
- `app/userecho/api/v1/feedback.py` ⭐ 核心
- `app/userecho/api/v1/topic.py` ⭐ 核心
- `app/userecho/api/v1/clustering.py` ⭐ 核心
- `app/userecho/api/v1/priority.py`

**路由注册:**
修改 `app/router.py`，添加：
```python
from backend.app.userecho.api.router import userecho_router
v1.include_router(userecho_router)
```

---

### 9. 前端 API 客户端 (TypeScript)

**待创建文件:**
- `front/apps/web-antd/src/api/userecho/feedback.ts`
- `front/apps/web-antd/src/api/userecho/topic.ts`
- `front/apps/web-antd/src/api/userecho/customer.ts`
- `front/apps/web-antd/src/api/userecho/clustering.ts`
- `front/apps/web-antd/src/api/userecho/priority.ts`

**路由配置:**
- `front/apps/web-antd/src/router/routes/modules/userecho.ts`

---

### 10. 前端页面

**待创建页面:**
- `views/userecho/feedback/list.vue` - 反馈列表页
- `views/userecho/feedback/import.vue` - Excel 导入页
- `views/userecho/topic/list.vue` - 主题列表页
- `views/userecho/topic/detail.vue` - 主题详情页
- `views/userecho/customer/index.vue` - 客户管理页

---

## 🔧 数据库迁移

**迁移文档:** `docs/database-migration-sql.md`

**包含:**
1. 修改 `sys_user` 表（添加 tenant_id）
2. 创建 7 张 Feedalyze 业务表
3. 创建索引和外键
4. 验证脚本
5. 回滚脚本

**执行方式:**
```bash
# 方式1：使用 Alembic 自动迁移（推荐）
cd server/backend
alembic revision --autogenerate -m "Create userecho tables"
alembic upgrade head

# 方式2：手动执行 SQL（如果 Alembic 不可用）
psql -U postgres -d fba < docs/database-migration-sql.md
```

---

## 📝 下一步行动

### 立即可执行的任务（按优先级）

1. **创建 Service 层** (2-3 小时)
   - 重点：`clustering_service.py` 和 `import_service.py`
   - 这两个是核心业务逻辑

2. **创建 API 路由** (2-3 小时)
   - 重点：`feedback.py`, `topic.py`, `clustering.py`
   - 测试工具：Postman / curl

3. **前端 API 封装** (1-2 小时)
   - 创建 TypeScript API 客户端
   - 配置路由

4. **前端页面开发** (1-2 天)
   - 反馈列表页
   - 主题详情页
   - 导入功能

5. **联调测试** (1 天)
   - 前后端联调
   - 多租户隔离测试
   - 完整流程测试

---

## 🎯 验收标准

### MVP 目标

- [ ] 导入 100 条反馈 < 5 秒
- [ ] AI 聚类 100 条反馈 < 30 秒
- [ ] 列表加载 < 1 秒
- [ ] 聚类准确率 > 80%

### 功能完整性

- [ ] 用户可以手动创建反馈
- [ ] 用户可以导入 Excel 反馈
- [ ] 系统可以自动聚类反馈
- [ ] 用户可以查看主题详情
- [ ] 用户可以对主题评分
- [ ] 用户可以更新主题状态

---

## ⚠️ 注意事项

### 多租户安全

所有数据查询必须过滤 `tenant_id`，已通过 `TenantAwareCRUD` 基类强制实现。

### AI API 调用

- DeepSeek API Key 需要在 `.env` 中配置
- 如果没有配置，系统会使用降级方案（简单规则）
- 生产环境建议同时配置 DeepSeek 和 OpenAI

### 数据库迁移

- **务必先备份数据库**
- 建议在测试环境先执行迁移
- 检查外键约束是否正确

---

**维护者:** AI 开发助手  
**项目状态:** 🚧 开发中  
**预计完成:** 还需 2-3 天
