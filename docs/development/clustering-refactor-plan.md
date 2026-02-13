# 聚类功能重构方案

> **作者**：Linus Torvalds 视角  
> **日期**：2025-12-23  
> **基于**：clustering-implementation-review.md + clustering_uiux_design.md  
> **原则**：Never break userspace | 简洁执念 | 实用主义

---

## 🎯 核心判断

### ✅ 值得做的理由

1. **真实问题**：100 条反馈手动分类需要 1 小时，AI 聚类只需 5 秒
2. **数据结构清晰**：Feedback → Embedding → Cluster → Topic，数据流向明确
3. **零破坏性**：异步处理不影响现有功能，`topic_id=NULL` 是合理的中间状态

### ❌ 不做的事情

1. **不做实时聚类**：100 条反馈聚类需要 5 秒，用户上传时立即返回，后台异步处理
2. **不做增量聚类**：MVP 阶段不需要，复杂度太高，收益不明显（后期可做）
3. **不做自动合并 Topic**：让 PM 手动决策，AI 只提供建议（人类最终负责）

---

## 📊 数据结构设计

### 核心原则

> "Bad programmers worry about the code. Good programmers worry about data structures."

**数据流向**：
```
Feedback (content) → Embedding (768 维向量) → DBSCAN → Cluster Labels → Topic (centroid)
                                                    ↓
                                              Noise Points (保持 NULL)
```

### 1. Feedback 表改造

**新增字段**：

```python
class Feedback(MappedBase):
    # ... 现有字段 ...
    
    # ✅ 已有 embedding 字段（无需改动）
    embedding: Mapped[list[float] | None] = mapped_column(
        Vector(768), default=None, comment='Embedding向量(pgvector)'
    )
    
    # ✅ 已有 topic_id 字段（无需改动）
    topic_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey('topics.id', ondelete='SET NULL'), 
        index=True, comment='关联主题ID'
    )
    
    # 🆕 新增：聚类状态
    clustering_status: Mapped[str] = mapped_column(
        String(20), 
        default='pending',  # pending, processing, clustered, failed
        index=True,
        comment='聚类状态: pending(待处理), processing(处理中), clustered(已聚类), failed(失败)'
    )
    
    # 🆕 新增：聚类元数据（可选，用于调试和质量追踪）
    clustering_metadata: Mapped[dict | None] = mapped_column(
        JSON, 
        default=None, 
        comment='聚类元数据: {cluster_label: int, similarity: float, clustered_at: datetime}'
    )
```

**状态流转**：
```
pending (初始状态)
   ↓
processing (Celery 任务开始)
   ↓
clustered (已分配到 Topic) ← topic_id != NULL
   ↓
noise (噪声点，不分配 Topic) ← topic_id == NULL, clustering_status = 'clustered'
```

**为什么需要 `clustering_status`？**
- **问题识别**：区分"未处理"和"处理失败"和"噪声点"
- **幂等性**：避免重复聚类同一批反馈
- **调试**：快速定位问题反馈

### 2. Topic 表改造

**新增字段**：

```python
from pgvector.sqlalchemy import Vector

class Topic(MappedBase):
    # ... 现有字段 ...
    
    # ✅ 已有 status 字段（无需改动）
    status: Mapped[str] = mapped_column(
        String(20), 
        default='pending',  # pending, planned, in_progress, completed, ignored
        comment='状态'
    )
    
    # 🆕 新增：Topic 中心向量（用于增量匹配）
    centroid: Mapped[list[float] | None] = mapped_column(
        Vector(768), 
        default=None, 
        comment='主题中心向量(所有反馈 embedding 的平均值)'
    )
    
    # 🆕 新增：聚类质量指标
    cluster_quality: Mapped[dict | None] = mapped_column(
        JSON, 
        default=None, 
        comment='聚类质量: {silhouette: float, noise_ratio: float, confidence: float}'
    )
    
    # 🆕 新增：是否为噪声 Topic（用于标记低质量 Topic）
    is_noise: Mapped[bool] = mapped_column(
        default=False, 
        comment='是否为噪声主题（仅单条反馈或低质量聚类）'
    )
```

**为什么需要 `centroid`？**
- **增量匹配**：新反馈到来时，计算与所有 Topic centroid 的相似度
- **Topic 合并**：计算两个 Topic 的相似度，提示 PM 合并
- **质量追踪**：重新计算聚类质量时不需要重新聚类

**为什么需要 `cluster_quality`？**
- **透明度**：PM 可以看到"这个 Topic 是 90% 置信度"还是"50% 置信度"
- **过滤**：前端可以默认隐藏低质量 Topic

---

## 🔄 核心流程设计

### 原则：**实时响应 + 异步处理 + 状态透明**

### 流程 1：手动添加单条反馈

```
1. 用户提交反馈
   ↓
2. FastAPI 立即返回：{"id": "xxx", "status": "pending"}
   ↓ (异步)
3. Celery 任务：
   - 生成 embedding
   - 查找相似 Topic (余弦相似度 > 0.8)
     - 命中 → 直接归入，更新 centroid
     - 未命中 → 保持 pending，等待批量聚类
```

**代码骨架**：

```python
# api/v1/feedback.py
@router.post('/feedbacks')
async def create_feedback(
    db: AsyncSession,
    obj: FeedbackCreate,
    background_tasks: BackgroundTasks  # FastAPI 内置
):
    # 1. 立即插入数据库
    feedback = await crud_feedback.create(db, obj)
    
    # 2. 异步处理 embedding + 匹配
    background_tasks.add_task(
        process_single_feedback,
        feedback_id=feedback.id,
        tenant_id=feedback.tenant_id
    )
    
    return feedback
```

### 流程 2：Excel 批量导入

```
1. 用户上传 Excel (500 条)
   ↓
2. FastAPI 验证格式，插入数据库
   ↓
3. 返回：{"imported": 500, "status": "processing", "task_id": "xxx"}
   ↓ (Celery 异步任务)
4. 批量生成 embedding (批量 API, 50条/批)
   ↓
5. 批量聚类 (DBSCAN)
   ↓
6. 创建 Topic + 更新 feedback.topic_id
   ↓
7. 推送完成通知 (WebSocket 或轮询)
```

**Celery 任务**：

```python
# app/task/tasks/clustering_tasks.py
from backend.app.task.celery import celery_app

@celery_app.task(name='clustering.batch_cluster')
async def batch_cluster_feedbacks(tenant_id: str, feedback_ids: list[str] = None):
    """批量聚类任务"""
    async with get_async_session() as db:
        # 1. 获取待聚类的反馈
        if feedback_ids:
            feedbacks = await crud_feedback.get_by_ids(db, tenant_id, feedback_ids)
        else:
            feedbacks = await crud_feedback.get_pending_clustering(db, tenant_id)
        
        # 2. 更新状态为 processing
        await crud_feedback.update_clustering_status(
            db, tenant_id, 
            [f.id for f in feedbacks], 
            'processing'
        )
        
        # 3. 执行聚类（复用现有 clustering_service）
        result = await clustering_service.trigger_clustering(
            db, tenant_id, 
            feedbacks=feedbacks
        )
        
        # 4. 更新状态为 clustered
        await crud_feedback.update_clustering_status(
            db, tenant_id, 
            result['clustered_feedback_ids'], 
            'clustered'
        )
        
        return result
```

### 流程 3：定时批量聚类

```
每天凌晨 2 点 (Celery Beat)
   ↓
1. 查询所有 clustering_status='pending' 的反馈
   ↓
2. 按租户分组，逐个聚类
   ↓
3. 更新 Topic 和 Feedback 状态
```

**Celery Beat 配置**：

```python
# app/task/tasks/beat.py
from celery.schedules import crontab

beat_schedule = {
    'daily-clustering': {
        'task': 'clustering.daily_cluster_all_tenants',
        'schedule': crontab(hour=2, minute=0),  # 每天凌晨 2 点
    },
}
```

---

## 🎨 交互设计方案

### 原则：**透明化 > 智能化**

> "给用户一个明确的心理预期，而不是黑盒魔法"

### 1. 反馈列表页

**UI 元素**：

```
┌────────────────────────────────────────────────────────┐
│  反馈列表                   [+ 添加] [导入 Excel]       │
├────────────────────────────────────────────────────────┤
│  过滤器：                                              │
│  [全部] [已分类] [未分类] [噪声点]                     │
│                                                        │
│  ID   内容                 主题       状态    操作     │
│  ─────────────────────────────────────────────────────│
│  001  登录按钮点不了       登录问题   ✅ 已分类        │
│  002  注册卡住了           NULL       🔄 处理中        │
│  003  导出 Excel 格式错    NULL       ⏳ 待处理        │
│  004  页面加载慢           NULL       🎲 噪声点        │
└────────────────────────────────────────────────────────┘
```

**状态映射**：
- `clustering_status='clustered' AND topic_id != NULL` → ✅ 已分类
- `clustering_status='processing'` → 🔄 处理中
- `clustering_status='pending'` → ⏳ 待处理
- `clustering_status='clustered' AND topic_id == NULL` → 🎲 噪声点

### 2. 导入进度页

**Excel 导入流程**：

```
┌────────────────────────────────────────────────────────┐
│  导入进度                                              │
├────────────────────────────────────────────────────────┤
│  [√] 文件解析完成 (500 条)                             │
│  [√] 数据验证通过 (成功 498 条，失败 2 条)              │
│  [Loading...] AI 语义识别 (342/498)                    │
│  [...] 需求主题聚合 (0/10 个主题)                       │
│                                                        │
│  预计剩余时间：约 2 分钟                                │
│  [查看失败记录] [后台运行]                              │
└────────────────────────────────────────────────────────┘
```

**实现方式**：
- 方案 A：轮询任务状态（简单，推荐）
  ```javascript
  setInterval(() => {
    fetch(`/api/v1/tasks/${taskId}/status`)
  }, 2000)  // 每 2 秒查询一次
  ```

- 方案 B：WebSocket 推送（复杂，后期优化）
  ```python
  # FastAPI WebSocket
  @router.websocket('/ws/clustering/{task_id}')
  async def clustering_progress(websocket: WebSocket, task_id: str):
      await websocket.accept()
      while True:
          progress = await get_task_progress(task_id)
          await websocket.send_json(progress)
          await asyncio.sleep(1)
  ```

### 3. AI 发现中心

**入口**：侧边栏/顶部小红点

```
┌────────────────────────────────────────────────────────┐
│  🔔 AI 发现中心                       [标记已读]        │
├────────────────────────────────────────────────────────┤
│  🆕 发现 3 个新主题建议                [全部确认]       │
│                                                        │
│  ┌──────────────────────────────────────────────────┐ │
│  │ 主题建议：登录问题                               │ │
│  │ 包含 12 条反馈，质量评分 85%                     │ │
│  │ "登录按钮点不了"、"登录超时"、"登录失败"...     │ │
│  │ [确认] [编辑] [忽略]                             │ │
│  └──────────────────────────────────────────────────┘ │
│                                                        │
│  ⚠️ 质量警告：以下主题质量较低                         │
│  - "用户反馈 #45" (仅 1 条反馈) → 建议手动归类         │
└────────────────────────────────────────────────────────┘
```

**数据来源**：
```sql
-- 查询新创建的 Topic（24 小时内，PM 未确认）
SELECT * FROM topics
WHERE ai_generated = true
  AND status = 'pending'
  AND created_time > NOW() - INTERVAL '24 hours'
ORDER BY feedback_count DESC
```

### 4. Topic 详情页

```
┌────────────────────────────────────────────────────────┐
│  主题：登录问题                                        │
│  分类：Bug  |  状态：待处理  |  反馈数：12             │
├────────────────────────────────────────────────────────┤
│  AI 质量评分：85% ⓘ                                    │
│  - 聚类紧密度 (Silhouette): 0.72                       │
│  - 噪声率: 15%                                         │
│                                                        │
│  相似主题建议：                                        │
│  - "用户认证问题" (相似度 78%) [合并?]                  │
│                                                        │
│  包含反馈：                                            │
│  1. 登录按钮点不了 (相似度 92%)                         │
│  2. 登录超时 (相似度 88%)                               │
│  ...                                                   │
└────────────────────────────────────────────────────────┘
```

---

## 🔧 技术实现细节

### 1. 噪声点处理（修复 P0 问题）

**当前问题**：每个噪声点创建一个 Topic → 垃圾泛滥

**修复方案**：**跳过噪声点，保持 pending**

```python
# clustering_service.py
for idx, label in enumerate(labels):
    if label == -1:  # 噪声点
        # ✅ 正确做法：标记为已处理，但不创建 Topic
        await crud_feedback.update_clustering_status(
            db, tenant_id, 
            [valid_feedbacks[idx].id], 
            'clustered'  # 状态改为 clustered，但 topic_id 保持 NULL
        )
        noise_feedbacks.append(valid_feedbacks[idx])
        continue  # 跳过，不加入 clusters
    
    # 正常聚类逻辑
    if label not in clusters:
        clusters[label] = []
    clusters[label].append(valid_feedbacks[idx])
```

**噪声点后续处理**：
1. **等待下次聚类**：新反馈到来后，与噪声点一起重新聚类
2. **手动归类**：PM 在"噪声点"页面手动拖拽到某个 Topic
3. **永久忽略**：标记为"无效反馈"

### 2. 质量门槛检查（修复 P1 问题）

**当前问题**：先创建 Topic，再评估质量 → 马后炮

**修复方案**：**先评估，不合格就跳过**

```python
# clustering_service.py
# 4. 执行聚类
labels = clustering_engine.cluster(embeddings_array)

# 5. ✅ 先评估质量
quality = clustering_engine.calculate_cluster_quality(embeddings_array, labels)

# 6. 检查质量门槛
if quality['silhouette'] < settings.CLUSTERING_MIN_SILHOUETTE:
    log.warning(f'Clustering quality too low for tenant {tenant_id}: {quality}')
    return {
        'status': 'low_quality',
        'message': '聚类质量不佳，建议收集更多反馈',
        'quality_metrics': quality
    }

# 7. 质量合格，才创建 Topic
for label, feedbacks in clusters.items():
    await create_topic(...)
```

**配置参数**（`core/conf.py`）：

```python
# 聚类质量门槛
CLUSTERING_MIN_SILHOUETTE: float = 0.3  # 最低轮廓系数
CLUSTERING_MAX_NOISE_RATIO: float = 0.5  # 最高噪声率
CLUSTERING_MIN_CLUSTER_SIZE: int = 3  # 最小聚类大小（从 2 改为 3）
```

### 3. Centroid 更新算法

**场景**：新反馈归入已有 Topic，需要更新 centroid

**增量平均公式**（高效，不需要重新计算所有向量）：

```python
# crud/crud_topic.py
async def update_centroid(
    self, 
    db: AsyncSession, 
    topic_id: str, 
    new_embedding: list[float]
) -> None:
    """增量更新 Topic 中心向量"""
    topic = await self.get_by_id(db, topic_id)
    
    if topic.centroid is None:
        # 第一条反馈，直接设为 centroid
        topic.centroid = new_embedding
        topic.feedback_count = 1
    else:
        # 增量平均：new_centroid = (old_centroid * n + new_vec) / (n + 1)
        n = topic.feedback_count
        old_centroid = np.array(topic.centroid)
        new_vec = np.array(new_embedding)
        
        new_centroid = (old_centroid * n + new_vec) / (n + 1)
        topic.centroid = new_centroid.tolist()
        topic.feedback_count = n + 1
    
    await db.commit()
```

### 4. 相似 Topic 检测

**场景**：AI 发现中心提示"Topic A 和 Topic B 高度相似，建议合并"

```python
# service/topic_similarity_service.py
async def find_similar_topics(
    db: AsyncSession,
    tenant_id: str,
    similarity_threshold: float = 0.85
) -> list[dict]:
    """查找相似的 Topic"""
    topics = await crud_topic.get_multi(db, tenant_id)
    
    # 提取所有 centroid
    centroids = []
    valid_topics = []
    for topic in topics:
        if topic.centroid:
            centroids.append(topic.centroid)
            valid_topics.append(topic)
    
    if len(centroids) < 2:
        return []
    
    # 计算两两相似度
    from sklearn.metrics.pairwise import cosine_similarity
    similarity_matrix = cosine_similarity(centroids)
    
    # 找出高相似度的 Topic 对
    suggestions = []
    for i in range(len(valid_topics)):
        for j in range(i + 1, len(valid_topics)):
            similarity = similarity_matrix[i][j]
            if similarity > similarity_threshold:
                suggestions.append({
                    'topic_a': valid_topics[i],
                    'topic_b': valid_topics[j],
                    'similarity': float(similarity),
                    'suggestion': f'建议合并"{valid_topics[i].title}"和"{valid_topics[j].title}"'
                })
    
    return suggestions
```

---

## 📋 实施计划

### 第一阶段：数据库改造 (1 天)

- [ ] **Day 1 上午**：编写 Alembic Migration
  - 新增 `feedback.clustering_status` 字段
  - 新增 `feedback.clustering_metadata` 字段
  - 新增 `topic.centroid` 字段
  - 新增 `topic.cluster_quality` 字段
  - 新增 `topic.is_noise` 字段
  
- [ ] **Day 1 下午**：更新 CRUD 方法
  - `crud_feedback.get_pending_clustering()`
  - `crud_feedback.update_clustering_status()`
  - `crud_topic.update_centroid()`
  - `crud_topic.calculate_quality()`

**验证**：运行测试，确保现有功能不破坏

### 第二阶段：修复核心问题 (2 天)

- [ ] **Day 2**：修复噪声点处理（P0）
  - 修改 `clustering_service.py` 跳过噪声点
  - 新增噪声点查询接口
  - 编写单元测试
  
- [ ] **Day 3**：修复质量门槛（P1）
  - 调整质量检查位置（先评估再创建）
  - 新增质量配置参数
  - 编写测试脚本

**验证**：聚类 100 条反馈，确保无垃圾 Topic

### 第三阶段：异步任务集成 (2 天)

- [ ] **Day 4**：Celery 任务
  - 编写 `clustering.batch_cluster` 任务
  - 编写 `clustering.process_single_feedback` 任务
  - 配置 Celery Beat 定时任务
  
- [ ] **Day 5**：API 集成
  - 修改 `/feedbacks` 接口，添加后台任务
  - 修改 `/feedbacks/import` 接口，调用 Celery 任务
  - 新增 `/tasks/{task_id}/status` 查询接口

**验证**：导入 500 条反馈，后台任务正常执行

### 第四阶段：前端交互 (3 天)

- [ ] **Day 6**：反馈列表页
  - 新增状态过滤器
  - 新增状态图标
  - 新增"手动归类"拖拽功能
  
- [ ] **Day 7**：导入进度页
  - 进度条组件
  - 轮询任务状态
  - 错误处理
  
- [ ] **Day 8**：AI 发现中心
  - 新主题建议列表
  - 质量警告提示
  - 确认/忽略操作

**验证**：完整流程测试，体验流畅

### 第五阶段：测试与优化 (1 天)

- [ ] **Day 9**：
  - 完整流程测试（单条/批量/定时）
  - 性能测试（1000 条反馈聚类耗时）
  - 边界测试（空文本/超长文本/重复导入）
  - 文档更新

---

## 🎯 技术决策总结

### ✅ 采用的方案

| 决策 | 理由 | 权衡 |
|------|------|------|
| **Celery 异步任务** | 项目已有 Celery，复用基础设施 | 比 FastAPI BackgroundTasks 更适合长任务 |
| **轮询任务状态** | 实现简单，无需 WebSocket 复杂度 | 延迟 2 秒可接受，后期可优化 |
| **噪声点跳过** | 避免垃圾 Topic，用户体验最优 | 需要 PM 手动处理噪声点 |
| **质量门槛检查** | 先评估再创建，避免低质量 Topic | 可能导致反馈长期未聚类 |
| **增量平均 Centroid** | 性能最优，无需重算所有向量 | 精度略低于全量平均（可接受） |

### ❌ 不采用的方案

| 方案 | 理由 |
|------|------|
| **实时聚类** | 100 条反馈需要 5 秒，用户等不了 |
| **增量聚类（MVP）** | 复杂度高，收益不明确，后期再做 |
| **自动合并 Topic** | 让 PM 决策，AI 只提供建议 |
| **WebSocket 推送（MVP）** | 轮询足够简单，无需过度设计 |
| **噪声点合并到"未分类"** | 制造"大杂烩" Topic，质量更差 |

---

## 🔍 关键指标

**性能目标**：
- 单条反馈处理 < 2 秒（embedding + 匹配）
- 100 条反馈聚类 < 10 秒（批量 embedding + DBSCAN）
- 1000 条反馈聚类 < 60 秒

**质量目标**：
- Silhouette 系数 > 0.3（可接受）
- 噪声率 < 50%（正常）
- Topic 数量：反馈数 / 10 ~ 反馈数 / 5（经验值）

**用户体验目标**：
- 导入即返回，无卡顿
- 进度可视化，无黑盒
- 结果可审核，可调整

---

## 📝 Linus 总结

### 做对的事情

1. **数据结构优先**：先设计好 Feedback/Topic 的状态流转，代码自然清晰
2. **异步处理**：用户体验和性能兼顾，聚类不影响界面响应
3. **状态透明**：用户随时知道"AI 在干什么"，而不是黑盒魔法
4. **质量可控**：PM 可以看到质量评分，决定是否采纳 AI 建议

### 避免的坑

1. **过度设计**：MVP 不做增量聚类，不做实时推送，够用就好
2. **噪声点泛滥**：跳过噪声点，而不是给它们创建垃圾 Topic
3. **马后炮质量检查**：先评估再创建，不浪费资源
4. **幂等性缺失**：用 `clustering_status` 避免重复处理

### 下一步

**立即开始**：第一阶段数据库改造（1 天）

**验证标准**：导入 100 条反馈，聚类结果无垃圾 Topic，用户体验流畅

**风险控制**：每个阶段都有独立验证，出问题可以回滚

---

**结论**：这是一个**简洁、实用、可靠**的方案，不是理论完美的方案，但能解决真实问题。

> "Talk is cheap. Show me the code." - 下一步：执行第一阶段。


