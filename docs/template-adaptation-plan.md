# Feedalyze 模板改造方案

> **版本:** v1.0  
> **更新日期:** 2025-12-21  
> **策略:** 增量开发，最小化改动现有模板

---

## 一、改造原则 (Linus 式思考)

### 核心判断
✅ **保留现有 RBAC 架构** - 后期会扩展角色（开发、CS、PM、老板）  
✅ **增量添加业务模块** - 在现有框架上新增 `userecho` 业务  
✅ **最小化改动** - 不删除 plugin，不重构路由，只做必要调整

### 数据结构关系
```
现有系统                    新增业务
┌─────────────┐           ┌─────────────┐
│   Tenant    │◀─────────▶│  Feedback   │
│  (租户)     │           │  (反馈)     │
└──────┬──────┘           └──────┬──────┘
       │                         │
       │ 1:N                     │ N:1
       ↓                         ↓
┌─────────────┐           ┌─────────────┐
│    User     │           │    Topic    │
│  (用户)     │           │  (需求主题) │
│            │           │            │
│  + tenant_id│◀──────────│  + tenant_id│
└──────┬──────┘           └──────┬──────┘
       │                         │
       │ N:M                     │ 1:1
       ↓                         ↓
┌─────────────┐           ┌─────────────┐
│    Role     │           │   Priority  │
│  (角色)     │           │   Score     │
└─────────────┘           └─────────────┘
```

**关键洞察：**
- 现有 User 表需要添加 `tenant_id` 字段
- RBAC 系统与 Feedalyze 业务完全解耦
- 通过 `tenant_id` 实现数据隔离

---

## 二、改造策略总览

### 不改动的部分 (保持原样)
✅ RBAC 系统（用户/角色/部门/菜单/数据权限）  
✅ Plugin 系统（保留所有现有 plugin）  
✅ Task 系统（Celery 任务调度）  
✅ 认证系统（JWT/登录日志/操作日志）  
✅ 监控系统（Redis/Server 监控）  
✅ 前端 Vben Admin 架构

### 需要小改的部分 (最小化)
🔧 `sys_user` 表：添加 `tenant_id` 字段  
🔧 数据库配置：添加 Feedalyze 业务表  
🔧 前端路由：添加 Feedalyze 菜单项  
🔧 API 路由：注册 Feedalyze 业务接口

### 需要新增的部分 (核心工作)
➕ 后端 `app/userecho/` 业务模块  
➕ 前端 `views/userecho/` 业务页面  
➕ AI 工具模块 `utils/ai_client.py`  
➕ 向量搜索工具 `utils/clustering.py`

---

## 三、数据库改造方案

### 3.1 现有表改造

#### 修改 `sys_user` 表 (添加租户关联)
```sql
-- 迁移脚本: server/backend/alembic/versions/001_add_tenant_to_user.py
ALTER TABLE sys_user ADD COLUMN tenant_id VARCHAR(36) DEFAULT 'default-tenant';
ALTER TABLE sys_user ADD INDEX idx_tenant_id (tenant_id);
ALTER TABLE sys_user ADD CONSTRAINT fk_user_tenant 
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE;
```

**为什么要改？**
- 实现多租户数据隔离
- 用户登录后自动关联到其所属租户
- 租户管理员只能看到本租户的反馈数据

---

### 3.2 新增业务表

创建迁移脚本目录结构：
```
server/backend/alembic/versions/
├── 001_add_tenant_to_user.py       (修改现有表)
├── 002_create_tenants.py           (新建租户表)
├── 003_create_customers.py         (新建客户表)
├── 004_create_feedbacks.py         (新建反馈表)
├── 005_create_topics.py            (新建主题表)
├── 006_create_priority_scores.py   (新建评分表)
└── 007_create_audit_tables.py      (新建审计表)
```

**详细 SQL 参考：** 参见 `database-design.md` 第三章节

---

## 四、后端改造方案

### 4.1 目录结构 (新增部分)

```
server/backend/
├── app/
│   ├── admin/                    ✅ 保持不变
│   ├── task/                     ✅ 保持不变
│   └── userecho/                ➕ 新增业务模块
│       ├── __init__.py
│       ├── model/
│       │   ├── __init__.py
│       │   ├── tenant.py
│       │   ├── customer.py
│       │   ├── feedback.py
│       │   ├── topic.py
│       │   ├── priority_score.py
│       │   ├── status_history.py
│       │   └── manual_adjustment.py
│       ├── schema/
│       │   ├── __init__.py
│       │   ├── tenant.py
│       │   ├── customer.py
│       │   ├── feedback.py
│       │   ├── topic.py
│       │   └── priority.py
│       ├── crud/
│       │   ├── __init__.py
│       │   ├── crud_tenant.py
│       │   ├── crud_customer.py
│       │   ├── crud_feedback.py
│       │   ├── crud_topic.py
│       │   └── crud_priority.py
│       ├── service/
│       │   ├── __init__.py
│       │   ├── feedback_service.py
│       │   ├── customer_service.py
│       │   ├── topic_service.py
│       │   ├── clustering_service.py
│       │   ├── priority_service.py
│       │   └── import_service.py
│       ├── api/
│       │   ├── __init__.py
│       │   ├── router.py
│       │   └── v1/
│       │       ├── __init__.py
│       │       ├── tenant.py
│       │       ├── customer.py
│       │       ├── feedback.py
│       │       ├── topic.py
│       │       ├── clustering.py
│       │       └── priority.py
│       └── tests/
│           └── __init__.py
│
├── utils/
│   ├── ai_client.py              ➕ AI 客户端封装
│   └── clustering.py             ➕ 聚类算法
│
└── plugin/                       ✅ 保持不变 (保留所有现有 plugin)
```

---

### 4.2 核心模型设计

#### 模型基类继承关系
```python
# 复用现有基类
from backend.common.model import Base, id_key

class Tenant(Base):
    """租户表 - 继承 Base 自动获得 created_time/updated_time"""
    __tablename__ = 'tenants'
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4_str)
    name: Mapped[str] = mapped_column(String(100), comment='租户名称')
    status: Mapped[str] = mapped_column(String(20), default='active', comment='状态')
    deleted_at: Mapped[datetime | None] = mapped_column(TimeZone, default=None)
```

**为什么继承 Base？**
- 自动获得 `created_time` / `updated_time` 字段
- 符合现有模板规范
- 便于后续审计日志记录

#### 关键字段说明

**Feedback 表（核心）：**
```python
class Feedback(Base):
    __tablename__ = 'feedbacks'
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4_str)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey('tenants.id'), index=True)
    customer_id: Mapped[str | None] = mapped_column(String(36), ForeignKey('customers.id'))
    anonymous_author: Mapped[str | None] = mapped_column(String(100))  # 匿名作者
    anonymous_source: Mapped[str | None] = mapped_column(String(50))   # 来源平台
    topic_id: Mapped[str | None] = mapped_column(String(36), ForeignKey('topics.id'))
    content: Mapped[str] = mapped_column(Text, comment='反馈内容')
    source: Mapped[str] = mapped_column(String(20), default='manual')
    ai_summary: Mapped[str | None] = mapped_column(String(50))
    is_urgent: Mapped[bool] = mapped_column(default=False)
    ai_metadata: Mapped[dict | None] = mapped_column(JSON)
    submitted_at: Mapped[datetime] = mapped_column(TimeZone, default_factory=timezone.now)
    deleted_at: Mapped[datetime | None] = mapped_column(TimeZone, default=None)
    
    # 业务约束
    __table_args__ = (
        CheckConstraint(
            'customer_id IS NOT NULL OR anonymous_author IS NOT NULL',
            name='chk_author_exists'
        ),
    )
```

**为什么用 String(36) 而不是 id_key？**
- 租户数据量可控，不需要雪花 ID
- UUID 更适合分布式场景
- 便于跨系统集成

---

### 4.3 API 路由注册

#### 修改主路由 `app/router.py`
```python
# server/backend/app/router.py
from backend.app.admin.api.router import admin_router
from backend.app.task.api.router import task_router
from backend.app.userecho.api.router import userecho_router  # ➕ 新增

v1 = APIRouter(prefix='/v1')
v1.include_router(admin_router)
v1.include_router(task_router)
v1.include_router(userecho_router)  # ➕ 新增
```

#### Feedalyze 业务路由
```python
# server/backend/app/userecho/api/router.py
from fastapi import APIRouter
from backend.app.userecho.api.v1 import (
    tenant,
    customer,
    feedback,
    topic,
    clustering,
    priority,
)

userecho_router = APIRouter(prefix='/userecho', tags=['Feedalyze'])

userecho_router.include_router(tenant.router, prefix='/tenants')
userecho_router.include_router(customer.router, prefix='/customers')
userecho_router.include_router(feedback.router, prefix='/feedbacks')
userecho_router.include_router(topic.router, prefix='/topics')
userecho_router.include_router(clustering.router, prefix='/clustering')
userecho_router.include_router(priority.router, prefix='/priority')
```

---

### 4.4 多租户中间件 (最小化改动)

#### 新增中间件
```python
# server/backend/middleware/tenant.py
from starlette.middleware.base import BaseHTTPMiddleware

class TenantContextMiddleware(BaseHTTPMiddleware):
    """从 JWT 中提取租户 ID 并注入 request.state"""
    
    async def dispatch(self, request: Request, call_next):
        # 从 JWT token 中提取 tenant_id
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if token:
            try:
                payload = jwt.decode(token, settings.TOKEN_SECRET_KEY, algorithms=[settings.TOKEN_ALGORITHM])
                request.state.tenant_id = payload.get('tenant_id', 'default-tenant')
            except:
                request.state.tenant_id = None
        else:
            request.state.tenant_id = None
        
        return await call_next(request)
```

#### 注册中间件 `main.py`
```python
# server/backend/main.py
from backend.middleware.tenant import TenantContextMiddleware

app.add_middleware(TenantContextMiddleware)  # ➕ 新增
```

---

### 4.5 CRUD 基类增强

#### 创建租户感知 CRUD 基类
```python
# server/backend/app/userecho/crud/base.py
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

class TenantAwareCRUD:
    """多租户 CRUD 基类 - 所有查询自动过滤租户"""
    
    def __init__(self, model):
        self.model = model
    
    async def get_multi(
        self, 
        db: AsyncSession, 
        tenant_id: str,
        skip: int = 0,
        limit: int = 100,
        **filters
    ):
        """获取列表 (自动过滤租户)"""
        query = select(self.model).where(
            self.model.tenant_id == tenant_id,
            self.model.deleted_at.is_(None)  # 软删除过滤
        )
        
        # 添加额外过滤条件
        for key, value in filters.items():
            if hasattr(self.model, key):
                query = query.where(getattr(self.model, key) == value)
        
        result = await db.execute(query.offset(skip).limit(limit))
        return result.scalars().all()
    
    async def create(self, db: AsyncSession, tenant_id: str, **data):
        """创建记录 (自动注入 tenant_id)"""
        obj = self.model(tenant_id=tenant_id, **data)
        db.add(obj)
        await db.commit()
        await db.refresh(obj)
        return obj
```

**所有业务 CRUD 继承此基类：**
```python
# server/backend/app/userecho/crud/crud_feedback.py
class CRUDFeedback(TenantAwareCRUD):
    def __init__(self):
        super().__init__(Feedback)
    
    async def get_unclustered(self, db: AsyncSession, tenant_id: str):
        """获取未聚类的反馈"""
        return await self.get_multi(db, tenant_id, topic_id=None)
```

---

### 4.6 AI 工具模块

#### AI 客户端封装
```python
# server/backend/utils/ai_client.py
from openai import AsyncOpenAI
from typing import List

class AIClient:
    """AI 客户端 - 支持多模型降级"""
    
    def __init__(self):
        self.clients = {
            'deepseek': AsyncOpenAI(
                base_url='https://api.deepseek.com',
                api_key=settings.DEEPSEEK_API_KEY
            ),
            'openai': AsyncOpenAI(api_key=settings.OPENAI_API_KEY),
        }
        self.current_provider = 'deepseek'
    
    async def get_embedding(self, text: str) -> List[float]:
        """获取文本 embedding 向量"""
        try:
            response = await self.clients[self.current_provider].embeddings.create(
                model='deepseek-embedding',
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            log.warning(f'DeepSeek embedding failed: {e}, fallback to OpenAI')
            return await self._fallback_embedding(text)
    
    async def generate_topic_title(self, feedbacks: List[str]) -> dict:
        """根据反馈列表生成需求主题"""
        prompt = f"""
你是一个产品经理助手，请分析以下用户反馈，提取核心需求主题。

用户反馈内容：
{chr(10).join(f'{i+1}. {f}' for i, f in enumerate(feedbacks[:10]))}

要求：
1. 生成一个15字以内的主题标题
2. 判断类别：bug/improvement/feature/performance/other
3. 判断是否紧急（包含"崩溃"、"无法使用"等词）

返回 JSON 格式：
{{"title": "标题", "category": "分类", "is_urgent": true/false}}
"""
        
        response = await self.clients[self.current_provider].chat.completions.create(
            model='deepseek-chat',
            messages=[{'role': 'user', 'content': prompt}],
            response_format={'type': 'json_object'}
        )
        
        return json.loads(response.choices[0].message.content)
    
    async def generate_summary(self, content: str) -> str:
        """生成 20 字摘要"""
        if len(content) <= 50:
            return content
        
        prompt = f"将以下反馈概括为20字以内的摘要：\n{content}"
        response = await self.clients[self.current_provider].chat.completions.create(
            model='deepseek-chat',
            messages=[{'role': 'user', 'content': prompt}],
            max_tokens=50
        )
        return response.choices[0].message.content.strip()

# 全局单例
ai_client = AIClient()
```

#### 聚类算法
```python
# server/backend/utils/clustering.py
import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.metrics.pairwise import cosine_similarity

class FeedbackClustering:
    """反馈聚类算法 - MVP 简化版"""
    
    def __init__(self, similarity_threshold: float = 0.75):
        self.threshold = similarity_threshold
    
    def cluster(self, embeddings: np.ndarray) -> np.ndarray:
        """
        使用 DBSCAN 聚类
        
        Args:
            embeddings: shape (n_samples, embedding_dim)
        
        Returns:
            labels: shape (n_samples,) 聚类标签，-1 表示噪声点
        """
        # 计算余弦相似度矩阵
        similarity_matrix = cosine_similarity(embeddings)
        
        # 转换为距离矩阵 (1 - similarity)
        distance_matrix = 1 - similarity_matrix
        
        # DBSCAN 聚类
        clustering = DBSCAN(
            eps=1 - self.threshold,  # 距离阈值
            min_samples=2,            # 最小聚类大小
            metric='precomputed'
        )
        
        labels = clustering.fit_predict(distance_matrix)
        return labels
    
    def find_similar_feedbacks(
        self, 
        query_embedding: np.ndarray,
        all_embeddings: np.ndarray,
        top_k: int = 10
    ) -> List[int]:
        """查找最相似的反馈"""
        similarities = cosine_similarity([query_embedding], all_embeddings)[0]
        top_indices = np.argsort(similarities)[::-1][:top_k]
        return top_indices.tolist()

# 全局单例
clustering_engine = FeedbackClustering()
```

---

### 4.7 核心服务实现

#### 聚类服务
```python
# server/backend/app/userecho/service/clustering_service.py
from backend.utils.ai_client import ai_client
from backend.utils.clustering import clustering_engine

class ClusteringService:
    """AI 聚类服务"""
    
    async def trigger_clustering(
        self, 
        db: AsyncSession, 
        tenant_id: str
    ) -> dict:
        """触发聚类任务（异步后台任务）"""
        
        # 1. 获取未聚类的反馈
        feedbacks = await crud_feedback.get_unclustered(db, tenant_id)
        
        if len(feedbacks) < 2:
            return {"message": "反馈数量不足，至少需要 2 条"}
        
        # 2. 批量获取 embedding
        embeddings = []
        for feedback in feedbacks:
            emb = await ai_client.get_embedding(feedback.content)
            embeddings.append(emb)
        
        embeddings_array = np.array(embeddings)
        
        # 3. 执行聚类
        labels = clustering_engine.cluster(embeddings_array)
        
        # 4. 为每个聚类生成主题
        clusters = {}
        for idx, label in enumerate(labels):
            if label == -1:  # 噪声点，单独成主题
                label = f'noise_{idx}'
            
            if label not in clusters:
                clusters[label] = []
            clusters[label].append(feedbacks[idx])
        
        # 5. 为每个聚类创建 Topic
        created_topics = []
        for label, cluster_feedbacks in clusters.items():
            # 使用 AI 生成主题标题
            feedback_contents = [f.content for f in cluster_feedbacks]
            topic_data = await ai_client.generate_topic_title(feedback_contents)
            
            # 创建主题
            topic = await crud_topic.create(
                db=db,
                tenant_id=tenant_id,
                title=topic_data['title'],
                category=topic_data['category'],
                ai_generated=True,
                ai_confidence=0.8,  # 简化版，后续可改进
                feedback_count=len(cluster_feedbacks)
            )
            
            # 更新反馈的 topic_id
            for feedback in cluster_feedbacks:
                await crud_feedback.update(
                    db=db,
                    feedback_id=feedback.id,
                    topic_id=topic.id
                )
            
            created_topics.append(topic)
        
        return {
            "status": "completed",
            "clusters_count": len(clusters),
            "topics_created": len(created_topics)
        }
```

#### 导入服务
```python
# server/backend/app/userecho/service/import_service.py
import pandas as pd
from fastapi import UploadFile

class ImportService:
    """Excel 导入服务"""
    
    async def import_excel(
        self, 
        db: AsyncSession,
        tenant_id: str,
        file: UploadFile
    ) -> dict:
        """导入 Excel 文件"""
        
        # 1. 读取文件
        df = pd.read_excel(file.file)
        
        # 2. 校验必填列
        required_cols = ['反馈内容', '客户名称']
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            raise ValueError(f"缺少必填列: {', '.join(missing)}")
        
        # 3. 逐行导入
        success_count = 0
        errors = []
        
        for idx, row in df.iterrows():
            try:
                # 获取或创建客户
                customer = await self._get_or_create_customer(
                    db=db,
                    tenant_id=tenant_id,
                    name=row['客户名称'],
                    customer_type=row.get('客户类型', 'normal')
                )
                
                # 创建反馈
                await crud_feedback.create(
                    db=db,
                    tenant_id=tenant_id,
                    customer_id=customer.id,
                    content=row['反馈内容'],
                    submitted_at=row.get('提交时间', timezone.now())
                )
                
                success_count += 1
                
            except Exception as e:
                errors.append({
                    "row": idx + 2,  # Excel 行号（从1开始，表头占1行）
                    "error": str(e)
                })
        
        return {
            "total": len(df),
            "success": success_count,
            "failed": len(errors),
            "errors": errors[:10]  # 最多返回 10 条错误
        }
    
    async def _get_or_create_customer(
        self,
        db: AsyncSession,
        tenant_id: str,
        name: str,
        customer_type: str
    ):
        """获取或创建客户"""
        # 先查询
        customer = await crud_customer.get_by_name(db, tenant_id, name)
        if customer:
            return customer
        
        # 创建新客户
        business_value_map = {
            'normal': 1, 'paid': 3, 'major': 5, 'strategic': 10
        }
        
        return await crud_customer.create(
            db=db,
            tenant_id=tenant_id,
            name=name,
            customer_type=customer_type,
            business_value=business_value_map.get(customer_type, 1)
        )
```

---

## 五、前端改造方案

### 5.1 目录结构 (新增部分)

```
front/apps/web-antd/src/
├── views/
│   ├── _core/                    ✅ 保持不变
│   ├── dashboard/                ✅ 保持不变
│   ├── system/                   ✅ 保持不变
│   ├── log/                      ✅ 保持不变
│   ├── monitor/                  ✅ 保持不变
│   └── userecho/                ➕ 新增业务页面
│       ├── feedback/
│       │   ├── list.vue
│       │   ├── import.vue
│       │   └── data.ts
│       ├── topic/
│       │   ├── list.vue
│       │   ├── detail.vue
│       │   └── data.ts
│       └── customer/
│           ├── index.vue
│           └── data.ts
│
├── api/
│   ├── core/                     ✅ 保持不变
│   ├── data-permission.ts        ✅ 保持不变
│   └── userecho/                ➕ 新增 API
│       ├── feedback.ts
│       ├── topic.ts
│       ├── customer.ts
│       ├── clustering.ts
│       └── priority.ts
│
├── router/routes/modules/
│   ├── dashboard.ts              ✅ 保持不变
│   ├── system.ts                 ✅ 保持不变
│   └── userecho.ts              ➕ 新增路由
│
├── locales/langs/zh-CN/
│   ├── common.json               ✅ 保持不变
│   ├── page.json                 🔧 添加翻译
│   └── userecho.json            ➕ 新增翻译
│
└── plugins/                      ✅ 保持不变 (保留所有现有 plugin)
```

---

### 5.2 路由配置

#### 新增 Feedalyze 路由模块
```typescript
// front/apps/web-antd/src/router/routes/modules/userecho.ts
import type { RouteRecordRaw } from 'vue-router';

import { $t } from '#/locales';

const routes: RouteRecordRaw[] = [
  {
    meta: {
      icon: 'lucide:messages-square',
      order: 0,
      title: $t('page.userecho.title'),
    },
    name: 'Feedalyze',
    path: '/userecho',
    children: [
      {
        name: 'FeedbackList',
        path: '/userecho/feedback/list',
        component: () => import('#/views/userecho/feedback/list.vue'),
        meta: {
          icon: 'lucide:inbox',
          title: $t('page.userecho.feedback.list'),
        },
      },
      {
        name: 'FeedbackImport',
        path: '/userecho/feedback/import',
        component: () => import('#/views/userecho/feedback/import.vue'),
        meta: {
          icon: 'lucide:upload',
          title: $t('page.userecho.feedback.import'),
        },
      },
      {
        name: 'TopicList',
        path: '/userecho/topic/list',
        component: () => import('#/views/userecho/topic/list.vue'),
        meta: {
          icon: 'lucide:lightbulb',
          title: $t('page.userecho.topic.list'),
        },
      },
      {
        name: 'TopicDetail',
        path: '/userecho/topic/detail/:id',
        component: () => import('#/views/userecho/topic/detail.vue'),
        meta: {
          hideInMenu: true,
          title: $t('page.userecho.topic.detail'),
        },
      },
      {
        name: 'CustomerManage',
        path: '/userecho/customer',
        component: () => import('#/views/userecho/customer/index.vue'),
        meta: {
          icon: 'lucide:users',
          title: $t('page.userecho.customer.title'),
        },
      },
    ],
  },
];

export default routes;
```

#### 注册路由（自动加载）
```typescript
// front/apps/web-antd/src/router/routes/modules/index.ts
// Vben Admin 会自动加载 modules 目录下的所有路由文件，无需手动注册
```

---

### 5.3 API 封装

#### API 请求工具
```typescript
// front/apps/web-antd/src/api/userecho/feedback.ts
import { requestClient } from '#/api/request';

export namespace FeedbackApi {
  /** 反馈列表查询参数 */
  export interface ListParams {
    page?: number;
    page_size?: number;
    topic_id?: string;
    is_urgent?: boolean;
    source?: string;
  }

  /** 反馈创建参数 */
  export interface CreateParams {
    customer_id?: string;
    anonymous_author?: string;
    anonymous_source?: string;
    content: string;
    is_urgent?: boolean;
  }

  /** 获取反馈列表 */
  export const getList = (params: ListParams) => {
    return requestClient.get<any>('/userecho/feedbacks', { params });
  };

  /** 创建反馈 */
  export const create = (data: CreateParams) => {
    return requestClient.post('/userecho/feedbacks', data);
  };

  /** Excel 导入 */
  export const importExcel = (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return requestClient.post('/userecho/feedbacks/import', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  };

  /** 删除反馈 */
  export const remove = (id: string) => {
    return requestClient.delete(`/userecho/feedbacks/${id}`);
  };
}
```

```typescript
// front/apps/web-antd/src/api/userecho/topic.ts
export namespace TopicApi {
  /** 主题列表查询参数 */
  export interface ListParams {
    page?: number;
    page_size?: number;
    status?: string;
    category?: string;
    sort?: 'priority' | 'created_at';
  }

  /** 获取主题列表 */
  export const getList = (params: ListParams) => {
    return requestClient.get<any>('/userecho/topics', { params });
  };

  /** 获取主题详情 */
  export const getDetail = (id: string) => {
    return requestClient.get(`/userecho/topics/${id}`);
  };

  /** 更新主题状态 */
  export const updateStatus = (id: string, status: string, reason?: string) => {
    return requestClient.patch(`/userecho/topics/${id}/status`, { status, reason });
  };

  /** 评分 */
  export const score = (id: string, data: any) => {
    return requestClient.post(`/userecho/topics/${id}/score`, data);
  };
}
```

```typescript
// front/apps/web-antd/src/api/userecho/clustering.ts
export namespace ClusteringApi {
  /** 触发聚类 */
  export const trigger = () => {
    return requestClient.post('/userecho/clustering/trigger');
  };

  /** 查询聚类状态 */
  export const getStatus = (taskId: string) => {
    return requestClient.get(`/userecho/clustering/status/${taskId}`);
  };
}
```

---

### 5.4 核心页面实现

#### 反馈列表页
```vue
<!-- front/apps/web-antd/src/views/userecho/feedback/list.vue -->
<template>
  <div class="feedback-list">
    <PageWrapper>
      <VxeGrid
        ref="gridRef"
        v-bind="gridOptions"
        @toolbar-button-click="handleToolbarClick"
      >
        <!-- 自定义列插槽 -->
        <template #urgent="{ row }">
          <Tag v-if="row.is_urgent" color="red">🔥 紧急</Tag>
          <Tag v-else color="default">📝 常规</Tag>
        </template>

        <template #topic="{ row }">
          <span v-if="row.topic_id">
            <Tag>{{ row.topic_title }}</Tag>
          </span>
          <span v-else class="text-gray-400">未聚类</span>
        </template>

        <template #action="{ row }">
          <Space>
            <Button type="link" size="small" @click="handleEdit(row)">
              编辑
            </Button>
            <Popconfirm title="确认删除?" @confirm="handleDelete(row)">
              <Button type="link" danger size="small">删除</Button>
            </Popconfirm>
          </Space>
        </template>
      </VxeGrid>
    </PageWrapper>

    <!-- 创建/编辑弹窗 -->
    <Modal
      v-model:open="modalVisible"
      title="创建反馈"
      @ok="handleSubmit"
    >
      <Form ref="formRef" :model="formData" :rules="formRules">
        <FormItem label="反馈内容" name="content">
          <Textarea v-model:value="formData.content" :rows="5" />
        </FormItem>
        <FormItem label="客户" name="customer_id">
          <Select
            v-model:value="formData.customer_id"
            :options="customerOptions"
            placeholder="选择客户（可选）"
          />
        </FormItem>
        <FormItem label="匿名作者">
          <Input v-model:value="formData.anonymous_author" placeholder="如：小红书用户123" />
        </FormItem>
        <FormItem label="是否紧急">
          <Switch v-model:checked="formData.is_urgent" />
        </FormItem>
      </Form>
    </Modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue';
import { VxeGrid, type VxeGridProps } from 'vxe-table';
import { FeedbackApi } from '#/api/userecho/feedback';
import { CustomerApi } from '#/api/userecho/customer';

const gridRef = ref();
const modalVisible = ref(false);
const customerOptions = ref([]);

const formData = reactive({
  content: '',
  customer_id: undefined,
  anonymous_author: '',
  is_urgent: false,
});

const gridOptions: VxeGridProps = {
  columns: [
    { field: 'content', title: '反馈内容', minWidth: 300 },
    { field: 'customer_name', title: '客户', width: 120 },
    { field: 'anonymous_author', title: '匿名作者', width: 120 },
    { field: 'topic_title', title: '所属主题', width: 150, slots: { default: 'topic' } },
    { field: 'is_urgent', title: '紧急程度', width: 100, slots: { default: 'urgent' } },
    { field: 'submitted_at', title: '提交时间', width: 180 },
    { field: 'action', title: '操作', width: 150, slots: { default: 'action' } },
  ],
  toolbarConfig: {
    buttons: [
      { code: 'create', name: '新建反馈', icon: 'vxe-icon-add' },
      { code: 'import', name: '导入Excel', icon: 'vxe-icon-upload' },
      { code: 'cluster', name: '触发聚类', icon: 'vxe-icon-refresh', status: 'primary' },
    ],
    refresh: true,
    zoom: true,
  },
  proxyConfig: {
    ajax: {
      query: async ({ page }) => {
        const res = await FeedbackApi.getList({
          page: page.currentPage,
          page_size: page.pageSize,
        });
        return {
          result: res.data.items,
          page: {
            total: res.data.total,
          },
        };
      },
    },
  },
  pagerConfig: {
    pageSize: 20,
  },
};

const handleToolbarClick = ({ code }: any) => {
  if (code === 'create') {
    modalVisible.value = true;
  } else if (code === 'import') {
    router.push('/userecho/feedback/import');
  } else if (code === 'cluster') {
    handleTriggerClustering();
  }
};

const handleTriggerClustering = async () => {
  try {
    await ClusteringApi.trigger();
    message.success('聚类任务已触发，请稍后查看结果');
    gridRef.value?.commitProxy('query');
  } catch (error) {
    message.error('聚类失败');
  }
};

const handleSubmit = async () => {
  try {
    await FeedbackApi.create(formData);
    message.success('创建成功');
    modalVisible.value = false;
    gridRef.value?.commitProxy('query');
  } catch (error) {
    message.error('创建失败');
  }
};

onMounted(async () => {
  // 加载客户列表
  const res = await CustomerApi.getList();
  customerOptions.value = res.data.map((c: any) => ({
    label: c.name,
    value: c.id,
  }));
});
</script>
```

#### 主题详情页
```vue
<!-- front/apps/web-antd/src/views/userecho/topic/detail.vue -->
<template>
  <div class="topic-detail">
    <PageWrapper>
      <Card title="主题信息" class="mb-4">
        <Descriptions :column="2">
          <DescriptionsItem label="标题">{{ topic.title }}</DescriptionsItem>
          <DescriptionsItem label="状态">
            <Tag :color="statusColorMap[topic.status]">
              {{ statusTextMap[topic.status] }}
            </Tag>
          </DescriptionsItem>
          <DescriptionsItem label="分类">
            <Tag>{{ categoryTextMap[topic.category] }}</Tag>
          </DescriptionsItem>
          <DescriptionsItem label="反馈数量">
            {{ topic.feedback_count }}
          </DescriptionsItem>
          <DescriptionsItem label="AI 置信度">
            <Progress :percent="topic.ai_confidence * 100" size="small" />
          </DescriptionsItem>
          <DescriptionsItem label="创建时间">
            {{ topic.created_at }}
          </DescriptionsItem>
        </Descriptions>

        <Divider />

        <Space>
          <Button type="primary" @click="handleUpdateStatus('planned')">
            标记为计划中
          </Button>
          <Button @click="handleUpdateStatus('in_progress')">
            标记为进行中
          </Button>
          <Button @click="handleUpdateStatus('completed')">
            标记为已完成
          </Button>
          <Button danger @click="handleUpdateStatus('ignored')">
            忽略此需求
          </Button>
        </Space>
      </Card>

      <Card title="优先级评分" class="mb-4">
        <Form :model="scoreForm" layout="inline">
          <FormItem label="影响范围">
            <Select v-model:value="scoreForm.impact_scope" style="width: 150px">
              <SelectOption :value="1">个别用户</SelectOption>
              <SelectOption :value="3">部分用户</SelectOption>
              <SelectOption :value="5">大多数用户</SelectOption>
              <SelectOption :value="10">全部用户</SelectOption>
            </Select>
          </FormItem>
          <FormItem label="商业价值">
            <Select v-model:value="scoreForm.business_value" style="width: 150px">
              <SelectOption :value="1">普通客户</SelectOption>
              <SelectOption :value="3">付费客户</SelectOption>
              <SelectOption :value="5">大客户</SelectOption>
              <SelectOption :value="10">战略客户</SelectOption>
            </Select>
          </FormItem>
          <FormItem label="开发成本">
            <Select v-model:value="scoreForm.dev_cost" style="width: 150px">
              <SelectOption :value="1">1天</SelectOption>
              <SelectOption :value="3">3天</SelectOption>
              <SelectOption :value="5">1周</SelectOption>
              <SelectOption :value="10">2周+</SelectOption>
            </Select>
          </FormItem>
          <FormItem>
            <Button type="primary" @click="handleScore">计算评分</Button>
          </FormItem>
        </Form>

        <Alert v-if="calculatedScore" type="success" class="mt-4">
          <template #message>
            <div class="text-lg">
              优先级总分: <strong>{{ calculatedScore.toFixed(2) }}</strong>
            </div>
            <div class="text-sm text-gray-500">
              公式: ({{ scoreForm.impact_scope }} × {{ scoreForm.business_value }}) / {{ scoreForm.dev_cost }}
              {{ topic.is_urgent ? ' × 1.5 (紧急)' : '' }}
            </div>
          </template>
        </Alert>
      </Card>

      <Card title="关联反馈">
        <VxeTable :data="feedbacks" :columns="feedbackColumns" />
      </Card>

      <Card title="状态变更历史" class="mt-4">
        <Timeline>
          <TimelineItem
            v-for="history in statusHistory"
            :key="history.id"
          >
            {{ history.changed_at }} - {{ history.from_status }} → {{ history.to_status }}
            <div class="text-sm text-gray-500">操作人: {{ history.changed_by }}</div>
          </TimelineItem>
        </Timeline>
      </Card>
    </PageWrapper>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import { TopicApi } from '#/api/userecho/topic';

const route = useRoute();
const topicId = route.params.id as string;

const topic = ref<any>({});
const feedbacks = ref<any[]>([]);
const statusHistory = ref<any[]>([]);

const scoreForm = reactive({
  impact_scope: 1,
  business_value: 1,
  dev_cost: 1,
});

const calculatedScore = computed(() => {
  const base = (scoreForm.impact_scope * scoreForm.business_value) / scoreForm.dev_cost;
  return topic.value.is_urgent ? base * 1.5 : base;
});

const statusColorMap = {
  pending: 'default',
  planned: 'blue',
  in_progress: 'orange',
  completed: 'green',
  ignored: 'red',
};

const statusTextMap = {
  pending: '待处理',
  planned: '计划中',
  in_progress: '进行中',
  completed: '已完成',
  ignored: '已忽略',
};

const categoryTextMap = {
  bug: 'Bug',
  improvement: '体验优化',
  feature: '新功能',
  performance: '性能问题',
  other: '其他',
};

const feedbackColumns = [
  { field: 'content', title: '反馈内容', minWidth: 300 },
  { field: 'customer_name', title: '客户', width: 120 },
  { field: 'submitted_at', title: '提交时间', width: 180 },
];

const handleUpdateStatus = async (status: string) => {
  try {
    await TopicApi.updateStatus(topicId, status);
    message.success('状态更新成功');
    loadTopicDetail();
  } catch (error) {
    message.error('状态更新失败');
  }
};

const handleScore = async () => {
  try {
    await TopicApi.score(topicId, scoreForm);
    message.success('评分成功');
    loadTopicDetail();
  } catch (error) {
    message.error('评分失败');
  }
};

const loadTopicDetail = async () => {
  const res = await TopicApi.getDetail(topicId);
  topic.value = res.data.topic;
  feedbacks.value = res.data.feedbacks;
  statusHistory.value = res.data.status_history;
  
  // 如果已有评分，填充表单
  if (res.data.priority_score) {
    Object.assign(scoreForm, res.data.priority_score);
  }
};

onMounted(() => {
  loadTopicDetail();
});
</script>
```

---

### 5.5 国际化配置

```json
// front/apps/web-antd/src/locales/langs/zh-CN/page.json
{
  "page": {
    "userecho": {
      "title": "反馈管理",
      "feedback": {
        "list": "反馈列表",
        "import": "导入反馈"
      },
      "topic": {
        "list": "需求主题",
        "detail": "主题详情"
      },
      "customer": {
        "title": "客户管理"
      }
    }
  }
}
```

---

## 六、配置文件调整

### 6.1 后端环境变量

```bash
# server/backend/.env
# 在现有配置基础上添加

# ==================== Feedalyze 配置 ====================
# AI 配置
DEEPSEEK_API_KEY=sk-xxx
OPENAI_API_KEY=sk-xxx
AI_DEFAULT_PROVIDER=deepseek

# 聚类配置
CLUSTERING_SIMILARITY_THRESHOLD=0.75
CLUSTERING_MIN_SAMPLES=2

# 导入配置
IMPORT_MAX_FILE_SIZE=10485760  # 10MB
IMPORT_ALLOWED_EXTENSIONS=.xlsx,.xls,.csv
```

### 6.2 数据库 Schema

```sql
-- 如果使用 MySQL，DATABASE_SCHEMA 保持为 'fba'
-- 如果使用 PostgreSQL，DATABASE_SCHEMA 保持为 'fba'
-- Feedalyze 表与现有表共存于同一 schema
```

---

## 七、开发排期

| 阶段 | 任务 | 工期 | 负责人 |
|-----|------|------|--------|
| **Week 1** | 数据库模型 + 迁移脚本 | 3 天 | 后端 |
| **Week 1** | CRUD + Service 层 | 2 天 | 后端 |
| **Week 2** | API 路由 + 多租户中间件 | 2 天 | 后端 |
| **Week 2** | AI 工具模块（embedding + 聚类） | 3 天 | 后端 |
| **Week 3** | 反馈列表页 + 导入页 | 3 天 | 前端 |
| **Week 3** | 主题列表页 + 详情页 | 2 天 | 前端 |
| **Week 4** | 客户管理页 + 联调测试 | 2 天 | 前后端 |
| **Week 4** | Excel 导入功能完善 | 2 天 | 后端 |
| **Week 4** | 聚类功能测试优化 | 1 天 | 后端 |
| **Week 5** | 集成测试 + Bug 修复 | 3 天 | 全员 |
| **Week 5** | 文档完善 + 部署准备 | 2 天 | 全员 |

**总计: 约 5 周**

---

## 八、风险与应对

| 风险 | 影响 | 概率 | 应对措施 |
|-----|------|------|----------|
| AI API 调用失败 | 🔴 高 | 🟡 中 | 多模型降级 + 本地缓存 |
| 聚类质量差 | 🔴 高 | 🟡 中 | 人工调整机制 + 参数调优 |
| 多租户数据泄露 | 🔴 高 | 🟢 低 | CRUD 基类强制过滤 + 测试用例 |
| 前后端接口不一致 | 🟡 中 | 🟡 中 | 使用 OpenAPI 生成 TypeScript 类型 |
| 现有功能被破坏 | 🟡 中 | 🟢 低 | 不删除现有代码 + 回归测试 |

---

## 九、测试策略

### 9.1 单元测试
```bash
# 后端测试
cd server/backend
pytest app/userecho/tests/

# 前端测试
cd front
pnpm test
```

### 9.2 集成测试重点
- [ ] 多租户数据隔离测试
- [ ] AI 聚类准确率测试（至少 80%）
- [ ] Excel 导入异常处理测试
- [ ] 优先级评分计算正确性测试

### 9.3 性能测试
- [ ] 100 条反馈聚类耗时 < 30 秒
- [ ] 列表查询（100 条）< 1 秒
- [ ] Excel 导入 500 条 < 1 分钟

---

## 十、部署清单

### 10.1 数据库迁移
```bash
cd server/backend
alembic upgrade head
```

### 10.2 环境变量检查
```bash
# 确保以下环境变量已配置
- DEEPSEEK_API_KEY
- OPENAI_API_KEY (备用)
- DATABASE_TYPE (postgresql 推荐)
```

### 10.3 依赖安装
```bash
# 后端
cd server
uv sync

# 前端
cd front
pnpm install
```

### 10.4 启动服务
```bash
# 后端开发环境
cd server/backend
python run.py

# 前端开发环境
cd front
pnpm dev:antd
```

---

## 十一、FAQ

**Q: 为什么不删除现有的 plugin 系统？**  
A: 
- 保持模板完整性，避免误删有用功能
- 后期可能需要扩展（如 OAuth2、邮件通知）
- 删除成本高于保留成本

**Q: RBAC 系统与 Feedalyze 如何协同？**  
A: 
- RBAC 管理用户权限（谁能访问哪些页面）
- Feedalyze 管理业务数据（反馈、主题）
- 通过 `tenant_id` 关联：一个租户有多个用户和多个反馈

**Q: 前端路由会不会冲突？**  
A: 
- 不会，Vben Admin 使用路径前缀区分
- 现有路由：`/system/*`, `/log/*`, `/monitor/*`
- 新增路由：`/userecho/*`

**Q: 数据库表会不会混乱？**  
A: 
- 不会，通过表名前缀区分
- 现有表：`sys_*`（系统表）
- 新增表：无前缀（业务表），清晰独立

**Q: 多租户如何初始化？**  
A: 
```sql
-- 创建默认租户
INSERT INTO tenants (id, name, status) VALUES ('default-tenant', '默认租户', 'active');

-- 将现有用户关联到默认租户
UPDATE sys_user SET tenant_id = 'default-tenant' WHERE tenant_id IS NULL;
```

---

## 十二、下一步行动

### 立即可执行的任务（按优先级）

1. **创建数据库模型** (2 天)
   ```bash
   cd server/backend/app
   mkdir -p userecho/{model,schema,crud,service,api/v1}
   touch userecho/model/{tenant,customer,feedback,topic,priority_score,status_history,manual_adjustment}.py
   ```

2. **编写 Alembic 迁移脚本** (1 天)
   ```bash
   cd server/backend
   alembic revision -m "Add tenant_id to sys_user"
   alembic revision -m "Create userecho core tables"
   ```

3. **实现 AI 工具模块** (2 天)
   ```bash
   touch server/backend/utils/{ai_client,clustering}.py
   ```

4. **创建前端页面骨架** (1 天)
   ```bash
   mkdir -p front/apps/web-antd/src/views/userecho/{feedback,topic,customer}
   mkdir -p front/apps/web-antd/src/api/userecho
   ```

---

**文档维护者:** 技术团队  
**最后更新:** 2025-12-21  
**状态:** 待评审
