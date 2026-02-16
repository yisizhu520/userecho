# Canny vs Feedalyze 数据模型深度对比分析

> **调研目的**: 深入分析 Canny 的 Board-Post-Vote 架构,找出我们 Feedback-Topic 设计的缺陷与优化空间。

---

## 一、Canny 数据模型架构

### 1.1 核心实体关系

```
Tenant (公司)
  ├── Board (反馈看板) ← 核心组织单元
  │     ├── Category (分类,可选)
  │     └── Post (用户提交的需求/反馈)
  │           ├── Vote (投票)
  │           ├── Comment (评论)
  │           └── Status (状态)
  └── User (终端用户)
```

### 1.2 详细模型设计

#### **Board (看板)**
```json
{
  "id": "board_123",
  "name": "Feature Requests",
  "urlName": "feature-requests",  // URL slug
  "postCount": 156,
  "isPrivate": false,
  "token": "abc123"  // 用于嵌入式小部件
}
```

**核心特点:**
- **多 Board 架构**: 一个公司可以有多个 Board (如「功能需求」「Bug 反馈」「移动端」)
- **独立 URL**: 每个 Board 有独立的公开访问地址
- **分类隔离**: 不同类型的反馈物理隔离,避免混乱

#### **Post (需求/反馈)**
```json
{
  "id": "post_456",
  "board": { "id": "board_123" },
  "author": { "id": "user_789", "name": "张三" },
  "title": "支持暗黑模式",
  "details": "希望能在设置中切换暗黑模式...",
  "category": { "id": "cat_001", "name": "UI/UX" },
  "status": "planned",  // open, under_review, planned, in_progress, complete, closed
  "score": 42,  // 投票数
  "commentCount": 8,
  "created": "2024-01-15T10:00:00Z",
  "url": "https://feedback.company.com/feature-requests/p/dark-mode-support"
}
```

**核心特点:**
- **用户直接创建**: Post 是用户在公开门户直接提交的,不是 Admin 聚类生成的
- **一对一关系**: 1 个 Post = 1 个用户需求 (不是多个 Feedback 聚合)
- **投票驱动**: `score` 字段直接反映社区热度
- **公开 URL**: 每个 Post 有独立的公开链接,可分享

#### **Vote (投票)**
```json
{
  "id": "vote_101",
  "post": { "id": "post_456" },
  "voter": { "id": "user_999", "email": "user@example.com" },
  "created": "2024-01-16T14:30:00Z"
}
```

**核心特点:**
- **一人一票**: 每个用户对每个 Post 只能投一票
- **可撤回**: 用户可以取消投票
- **自动订阅**: 投票后自动订阅该 Post 的状态更新通知

#### **Comment (评论)**
```json
{
  "id": "comment_202",
  "post": { "id": "post_456" },
  "author": { "id": "user_888" },
  "value": "强烈支持!我们团队也需要这个功能",
  "created": "2024-01-17T09:15:00Z",
  "isInternal": false  // 是否为内部评论(仅团队可见)
}
```

---

## 二、Feedalyze 当前数据模型

### 2.1 核心实体关系

```
Tenant (租户)
  ├── Customer (客户)
  ├── Feedback (原始反馈) ← 数据源
  │     └── Topic (AI 聚类生成的主题)
  └── PriorityScore (优先级评分)
```

### 2.2 详细模型设计

#### **Feedback (反馈)**
```python
{
  "id": "feedback_123",
  "tenant_id": "tenant_001",
  "customer_id": "customer_456",  # 或 anonymous_author
  "content": "希望能支持暗黑模式",
  "source": "screenshot",  # manual, import, api, screenshot
  "topic_id": "topic_789",  # AI 聚类后关联
  "embedding": [0.123, 0.456, ...],  # 4096维向量
  "clustering_status": "clustered",
  "submitted_at": "2024-01-15T10:00:00Z"
}
```

#### **Topic (主题)**
```python
{
  "id": "topic_789",
  "tenant_id": "tenant_001",
  "title": "暗黑模式支持",
  "category": "feature",
  "status": "pending",
  "ai_generated": true,
  "feedback_count": 15,  # 聚合了 15 条 Feedback
  "centroid": [0.234, 0.567, ...],  # 中心向量
  "cluster_quality": {"silhouette": 0.72},
  "created_time": "2024-01-20T08:00:00Z"
}
```

---

## 三、核心差异对比

| 维度 | Canny (Board-Post-Vote) | Feedalyze (Feedback-Topic) | 影响 |
|------|------------------------|---------------------------|------|
| **数据来源** | 用户直接在公开门户提交 Post | Admin 导入/录入 Feedback,AI 聚类生成 Topic | 🔴 **致命差异** |
| **聚合方式** | 用户手动搜索 + 投票已有 Post | AI 自动聚类相似 Feedback | 🟡 技术优势,但用户无感知 |
| **投票对象** | 直接投票给 Post | ❌ 无投票机制 | 🔴 **缺失核心功能** |
| **公开访问** | 每个 Post 有公开 URL | ❌ Topic 无公开 URL | 🔴 **无法对外开放** |
| **用户参与** | 用户可创建/投票/评论 Post | ❌ 用户无法参与 | 🔴 **单向数据流** |
| **去重机制** | 用户搜索 + Admin 手动合并 | AI 自动聚类 | 🟢 我们更智能 |
| **多维度组织** | Board (看板) + Category (分类) | 仅 Category (分类) | 🟡 缺少 Board 层级 |

---

## 四、我们设计的核心缺陷

### 🔴 缺陷 1: **Topic 不是用户可见的实体**

**问题:**
- Topic 是 AI 聚类的**内部产物**,不是用户主动创建的
- 用户无法直接「提交一个 Topic」或「投票给 Topic」
- Topic 的标题/描述是 AI 生成的,可能不符合用户表达习惯

**Canny 的做法:**
- Post 是用户直接提交的,标题/描述都是用户原话
- 即使有重复,用户也能清晰看到「我的 Post」

**影响:**
- ❌ 无法建立「用户 → Topic」的归属感
- ❌ 用户不知道自己的反馈被聚类到哪个 Topic
- ❌ Topic 标题可能过于抽象 (如「优化搜索性能」vs 用户原话「搜索太慢了」)

---

### 🔴 缺陷 2: **缺少投票机制**

**问题:**
- 我们只有 `feedback_count` (反馈数量),没有 `vote_count` (投票数)
- 无法区分「15 个客户各提了 1 次」vs「1 个客户提了 15 次」
- 无法让用户表达「我也需要这个功能」

**Canny 的做法:**
- 每个 Post 有独立的 `score` (投票数)
- 用户可以投票给别人的 Post,而不是重复提交
- 投票数 = 真实需求热度

**影响:**
- ❌ 无法准确衡量需求优先级 (feedback_count 会被刷)
- ❌ 用户无法参与优先级决策
- ❌ 无法实现「社区驱动」的产品路线图

---

### 🔴 缺陷 3: **Feedback 与 Topic 的关系混乱**

**问题:**
- Feedback 是「原始数据」,Topic 是「聚类结果」
- 用户看到的应该是 Topic,但 Topic 的内容是 AI 生成的摘要,不是原文
- 如果用户想看「这个 Topic 下有哪些具体反馈」,需要展示 15 条 Feedback,体验差

**Canny 的做法:**
- Post 本身就是用户提交的完整内容
- Comment 是补充讨论,不是「原始数据」
- 没有「聚类」的概念,靠用户自己搜索去重

**影响:**
- ❌ Topic 详情页展示困难 (是展示 AI 摘要还是原始 Feedback?)
- ❌ 用户无法直接看到「谁提了这个需求」
- ❌ Feedback 与 Topic 的一对多关系增加复杂度

---

### 🟡 缺陷 4: **缺少 Board 层级**

**问题:**
- 我们只有一个扁平的 Topic 列表,靠 `category` 分类
- 无法隔离不同产品线/平台的反馈 (如「Web 端」vs「移动端」)

**Canny 的做法:**
- 多 Board 架构,每个 Board 是独立的反馈空间
- 例如: `feedback.company.com/web` 和 `feedback.company.com/mobile`

**影响:**
- ⚠️ 对于单一产品的中小企业,影响不大
- ⚠️ 对于多产品线的企业,会导致反馈混乱

---

## 五、优化方案建议

### 方案 A: **渐进式改造 (推荐)**

保留现有 Feedback-Topic 架构,增加 Post-Vote 层

#### 新增模型

**1. Post (用户可见的需求)**
```python
class Post(MappedBase):
    """用户提交的需求 (对标 Canny Post)"""
    __tablename__ = 'posts'
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey('tenants.id'))
    board_id: Mapped[str] = mapped_column(ForeignKey('boards.id'))  # 新增 Board
    
    # 用户提交的原始内容
    title: Mapped[str] = mapped_column(String(400))
    details: Mapped[str | None] = mapped_column(Text)
    
    # 作者
    author_id: Mapped[str | None] = mapped_column(ForeignKey('end_users.id'))
    author_name: Mapped[str | None] = mapped_column(String(100))  # 匿名用户
    
    # 分类与状态
    category: Mapped[str | None] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(20), default='open')
    
    # 统计
    vote_count: Mapped[int] = mapped_column(default=0)
    comment_count: Mapped[int] = mapped_column(default=0)
    
    # 公开访问
    slug: Mapped[str] = mapped_column(String(200), unique=True)
    is_public: Mapped[bool] = mapped_column(default=True)
    
    # AI 关联 (可选)
    topic_id: Mapped[str | None] = mapped_column(ForeignKey('topics.id'))
    embedding: Mapped[list[float] | None] = mapped_column(Vector(4096))
    
    created_time: Mapped[datetime] = mapped_column(TimeZone, default=timezone.now)
```

**2. Vote (投票)**
```python
class Vote(MappedBase):
    """投票记录"""
    __tablename__ = 'votes'
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    post_id: Mapped[str] = mapped_column(ForeignKey('posts.id', ondelete='CASCADE'))
    voter_id: Mapped[str] = mapped_column(ForeignKey('end_users.id'))
    
    created_time: Mapped[datetime] = mapped_column(TimeZone, default=timezone.now)
    
    __table_args__ = (
        UniqueConstraint('post_id', 'voter_id', name='uq_post_voter'),
    )
```

**3. Board (看板,可选)**
```python
class Board(MappedBase):
    """反馈看板"""
    __tablename__ = 'boards'
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey('tenants.id'))
    
    name: Mapped[str] = mapped_column(String(100))  # "功能需求"
    url_name: Mapped[str] = mapped_column(String(100))  # "feature-requests"
    is_private: Mapped[bool] = mapped_column(default=False)
```

#### 数据流改造

**旧流程 (仅内部):**
```
Admin 导入 Feedback → AI 聚类 → 生成 Topic → Admin 查看
```

**新流程 (内外结合):**
```
方式 1: 用户在公开门户提交 Post → 生成 embedding → (可选) AI 关联到 Topic
方式 2: Admin 导入 Feedback → AI 聚类 → 生成 Topic → (可选) 创建对应的 Post
```

#### 优势
- ✅ 保留现有 AI 聚类能力
- ✅ 增加用户参与 (Post + Vote)
- ✅ 兼容现有数据 (Feedback 继续存在)
- ✅ 渐进式迁移,风险低

#### 劣势
- ⚠️ 数据模型复杂度增加 (Post vs Topic vs Feedback)
- ⚠️ 需要处理 Post ↔ Topic 的关联逻辑

---

### 方案 B: **彻底重构 (激进)**

废弃 Feedback-Topic,完全采用 Post-Vote 架构

#### 改造方案
1. **废弃 Feedback 表**: 所有用户提交都直接创建 Post
2. **废弃 Topic 表**: 不再做 AI 聚类,靠用户搜索去重
3. **保留 AI 能力**: 
   - 用户提交 Post 时,AI 自动检测重复并提示
   - 用户提交后,AI 自动打标签/分类

#### 优势
- ✅ 模型简单清晰,完全对标 Canny
- ✅ 用户体验一致

#### 劣势
- ❌ **丢失核心竞争力**: AI 聚类是我们的差异化优势
- ❌ 重构成本高,现有数据迁移困难
- ❌ 去重效果依赖用户主动搜索,不如 AI 聚类

---

### 方案 C: **混合模式 (折中)**

Post 作为 Topic 的「代表性实例」

#### 核心思路
- Topic 依然是 AI 聚类的结果
- 但每个 Topic 自动选择一个「最佳 Feedback」作为 Post 展示
- 用户投票/评论都针对 Post,但实际关联到 Topic

#### 实现
```python
class Topic(MappedBase):
    # ... 现有字段 ...
    
    # 新增: 代表性 Post
    representative_post_id: Mapped[str | None] = mapped_column(
        ForeignKey('posts.id')
    )
```

**逻辑:**
1. AI 聚类生成 Topic 后,自动从 Feedback 中选择最清晰的一条
2. 将该 Feedback 转换为 Post (用户可见)
3. 其他 Feedback 作为「相关反馈」隐藏在详情页

#### 优势
- ✅ 保留 AI 聚类优势
- ✅ 用户看到的是真实反馈,不是 AI 摘要
- ✅ 投票/评论体验与 Canny 一致

#### 劣势
- ⚠️ 「代表性 Post」的选择逻辑复杂
- ⚠️ 用户可能困惑「为什么我的反馈不是 Post」

---

## 六、推荐方案

### 🎯 **方案 A (渐进式改造) + 方案 C (混合模式)**

#### 第一阶段: 增加 Post-Vote 层
1. 新建 `Post`, `Vote`, `Board` 表
2. 用户可在公开门户提交 Post
3. Post 自动生成 embedding,AI 检测重复

#### 第二阶段: 打通 Post ↔ Topic
1. AI 聚类时,自动将相似 Post 关联到同一个 Topic
2. Topic 详情页展示:
   - **主 Post**: 投票数最高的 Post
   - **相关 Post**: 其他被聚类到该 Topic 的 Post
   - **Admin Feedback**: 内部导入的 Feedback (不公开)

#### 第三阶段: 数据迁移
1. 将现有高质量 Topic 转换为 Post (手动或 AI 生成标题/描述)
2. 历史 Feedback 保留,但不公开展示

---

## 七、数据模型对比总结

| 特性 | Canny | Feedalyze (现状) | Feedalyze (优化后) |
|------|-------|-----------------|-------------------|
| 用户提交 | ✅ Post | ❌ 无 | ✅ Post |
| 投票机制 | ✅ Vote | ❌ 无 | ✅ Vote |
| AI 聚类 | ❌ 无 | ✅ Topic | ✅ Topic (内部) |
| 去重方式 | 用户搜索 | AI 自动 | AI 自动 + 用户投票 |
| 公开访问 | ✅ 每个 Post | ❌ 无 | ✅ 每个 Post |
| 多维度组织 | Board + Category | Category | Board + Category |
| 评论系统 | ✅ Comment | ❌ 无 | ✅ Comment |

---

## 八、行动建议

### 立即行动
1. ✅ **确认方案**: Review 本文档,确定采用方案 A + C
2. ⏳ **设计 Post 模型**: 详细设计 Post/Vote/Board 的字段与关系
3. ⏳ **设计 Post ↔ Topic 关联逻辑**: 如何自动将 Post 聚类到 Topic

### 本周完成
- 数据库 Schema 设计
- Post 提交流程设计 (前端 + 后端)
- AI 去重检测逻辑

### 下周完成
- 实现 Post 创建 API
- 实现 Vote API
- 公开门户 Post 列表页

---

**文档维护者**: 产品 + 技术团队  
**最后更新**: 2025-12-30
