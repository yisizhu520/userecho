# Feedback 去重与聚类策略对比分析

> **创建日期**: 2025-12-31  
> **目的**: 对比 Canny 的实时去重模式与我们的异步聚类模式，给出最佳实践建议

---

## 一、两种模式对比

### 1.1 Canny 模式：实时去重 + 手动合并

#### 工作流程
```
用户输入反馈
    ↓
实时检索相似 Post（右侧显示）
    ↓
用户选择：
    ├─ 给已有 Post 投票（不创建新 Post）
    └─ 创建新 Post
    ↓
Admin 手动 Merge 重复 Post
```

#### 数据模型
```sql
-- Canny 只有一层抽象
posts (类似我们的 feedbacks)
    ├─ id
    ├─ title
    ├─ details
    ├─ vote_count
    ├─ merged_into_id  -- 指向被合并到的 Post
    └─ status
```

#### 核心特点
- ✅ **用户参与去重**：用户在提交前就能看到相似反馈
- ✅ **减少冗余数据**：用户倾向于投票而非重复提交
- ✅ **简单直观**：只有一层抽象（Post）
- ❌ **依赖用户主动性**：用户可能懒得搜索，直接提交
- ❌ **手动合并成本高**：Admin 需要逐个审核并合并

---

### 1.2 我们的模式：自由录入 + AI 异步聚类

#### 工作流程
```
员工自由录入 Feedback
    ↓
AI 异步检测相似 Feedback
    ↓
AI 自动聚类 → 生成 Topic
    ↓
Admin 审核聚类结果
    ├─ 确认聚类
    ├─ 手动调整（移动 Feedback 到其他 Topic）
    └─ 拆分/合并 Topic
```

#### 数据模型
```sql
-- 我们有两层抽象
feedbacks (原始反馈)
    ├─ id
    ├─ content
    ├─ embedding
    ├─ topic_id  -- 关联到聚类主题
    └─ clustering_status

topics (聚类主题)
    ├─ id
    ├─ title (AI 生成)
    ├─ description (AI 生成)
    ├─ centroid (主题中心向量)
    └─ feedback_count
```

#### 核心特点
- ✅ **录入零门槛**：员工无需搜索，直接录入
- ✅ **AI 自动化**：减少人工合并工作量
- ✅ **两层抽象**：Topic 可以作为需求管理单元
- ❌ **数据冗余**：大量重复 Feedback 占用存储
- ❌ **异步延迟**：聚类结果不是实时的
- ❌ **复杂度高**：需要维护 Feedback ↔ Topic 的关系

---

## 二、场景适配性分析

### 2.1 Canny 模式适用场景

✅ **适合以下情况**：
1. **外部用户主动提交**：用户有动力搜索并投票
2. **公开透明**：用户可以看到所有反馈
3. **社区驱动**：依赖用户参与去重
4. **数据量可控**：手动合并成本可接受

❌ **不适合以下情况**：
1. **内部员工录入**：员工没有动力搜索（赶时间）
2. **批量导入**：Excel 导入无法实时去重
3. **截图识别**：AI 识别的反馈无法让用户参与去重
4. **高频录入**：销售/客服每天录入几十条，无暇搜索

---

### 2.2 我们的模式适用场景

✅ **适合以下情况**：
1. **内部员工录入**：销售/客服快速录入，不打断工作流
2. **多渠道录入**：手动、Excel、截图、API 等
3. **批量处理**：AI 异步聚类，不影响录入速度
4. **需求管理**：Topic 作为需求单元，关联多个 Feedback

❌ **不适合以下情况**：
1. **实时反馈**：用户期望立即看到去重结果
2. **存储敏感**：大量冗余 Feedback 占用存储
3. **简单场景**：不需要复杂的聚类分析

---

## 三、核心问题与解决方案

### 3.1 问题 1：数据冗余

**现状**：
- 10 个客户提同一个需求 → 产生 10 条 Feedback
- 占用存储，查询效率低

**Canny 的解决方案**：
- 用户在提交前看到相似 Post，选择投票而非重复提交
- 结果：只有 1 条 Post，10 个 Vote

**我们的解决方案（现有）**：
- 10 条 Feedback 都保留，聚类到 1 个 Topic
- 优势：保留原始数据，便于追溯
- 劣势：数据冗余

**改进方案 A：软合并（推荐）**
```sql
-- 保留所有 Feedback，但标记为"已合并"
ALTER TABLE feedbacks ADD COLUMN merged_into_id VARCHAR(36) REFERENCES feedbacks(id);
ALTER TABLE feedbacks ADD COLUMN is_primary BOOLEAN DEFAULT TRUE;

-- 查询时只显示主 Feedback
SELECT * FROM feedbacks 
WHERE topic_id = $topic_id 
  AND is_primary = TRUE;

-- 查看所有原始 Feedback（包括被合并的）
SELECT * FROM feedbacks 
WHERE topic_id = $topic_id;
```

**改进方案 B：硬合并（不推荐）**
```sql
-- 删除重复 Feedback，只保留一条
-- ❌ 丢失原始数据，无法追溯
```

---

### 3.2 问题 2：录入体验 vs 数据质量

**Canny 的权衡**：
- 牺牲录入速度（用户需要搜索）
- 换取数据质量（减少冗余）

**我们的权衡**：
- 牺牲数据质量（允许冗余）
- 换取录入速度（员工快速录入）

**最佳实践：混合模式**

#### 方案：实时建议 + 异步聚类

```
员工录入 Feedback
    ↓
【实时】AI 检索相似 Feedback/Topic（右侧显示）
    ↓
员工选择：
    ├─ 关联到已有 Topic（推荐）
    ├─ 关联到已有 Feedback（合并）
    └─ 创建新 Feedback（允许）
    ↓
【异步】AI 聚类未关联的 Feedback
    ↓
Admin 审核聚类结果
```

**实现细节**：
```javascript
// 前端：员工输入时实时搜索
async function onFeedbackInput(content) {
    const suggestions = await api.searchSimilar(content);
    
    // 右侧显示相似内容
    showSuggestions([
        {
            type: 'topic',
            title: '支持暗黑模式',
            similarity: 0.92,
            feedback_count: 15,
            action: '关联到此主题'
        },
        {
            type: 'feedback',
            content: '希望增加夜间模式',
            similarity: 0.88,
            customer: '某银行',
            action: '合并到此反馈'
        }
    ]);
}
```

**优势**：
- ✅ 保留快速录入（员工可以忽略建议）
- ✅ 减少冗余（员工有动力关联已有 Topic）
- ✅ AI 兜底（未关联的 Feedback 异步聚类）

---

### 3.3 问题 3：Topic 抽象的必要性

**Canny 为什么不需要 Topic？**
1. **单层抽象足够**：Post 本身就是需求单元
2. **用户参与去重**：重复 Post 被合并到一起
3. **简单直观**：Admin 直接管理 Post 状态

**我们为什么需要 Topic？**
1. **多对一关系**：多个 Feedback → 1 个 Topic
2. **需求管理**：Topic 作为需求单元，关联 Jira/Tapd
3. **AI 聚类**：Topic 是聚类结果的载体
4. **优先级评分**：Topic 聚合多个客户的价值

**Topic 的价值**：
```sql
-- 示例：Topic "支持暗黑模式"
SELECT 
    t.title,
    COUNT(f.id) AS feedback_count,
    COUNT(DISTINCT f.customer_id) AS affected_customers,
    SUM(c.mrr) AS total_mrr,
    t.priority_score
FROM topics t
JOIN feedbacks f ON t.id = f.topic_id
JOIN customers c ON f.customer_id = c.id
WHERE t.id = 'topic_001'
GROUP BY t.id;

-- 结果：
-- | 主题 | 反馈数 | 客户数 | 总 MRR | 优先级 |
-- | 支持暗黑模式 | 15 | 12 | 500,000 | 125.5 |
```

**结论**：
- ✅ **保留 Topic 抽象**：对于内部需求管理非常有价值
- ✅ **但优化 Feedback 去重**：减少冗余数据

---

## 四、推荐方案：混合模式

### 4.1 核心设计

```
┌─────────────────────────────────────────────────────────┐
│  录入阶段：实时建议（可选）                                │
├─────────────────────────────────────────────────────────┤
│  员工输入 → AI 实时检索 → 显示相似 Topic/Feedback          │
│  员工选择：                                               │
│    ├─ 关联到已有 Topic（推荐，减少冗余）                   │
│    ├─ 合并到已有 Feedback（标记为 merged_into_id）        │
│    └─ 创建新 Feedback（允许，不强制）                      │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│  聚类阶段：AI 异步处理（兜底）                             │
├─────────────────────────────────────────────────────────┤
│  定时任务：                                               │
│    ├─ 检测未关联 Topic 的 Feedback                        │
│    ├─ AI 聚类 → 生成 Topic                               │
│    └─ 标记为 pending_review                              │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│  审核阶段：人工确认                                        │
├─────────────────────────────────────────────────────────┤
│  Admin 审核：                                             │
│    ├─ 确认聚类结果                                        │
│    ├─ 手动调整（移动 Feedback）                           │
│    ├─ 合并 Topic                                         │
│    └─ 拆分 Topic                                         │
└─────────────────────────────────────────────────────────┘
```

### 4.2 数据模型优化

```sql
-- Feedbacks 表（新增字段）
ALTER TABLE feedbacks ADD COLUMN IF NOT EXISTS
    merged_into_id VARCHAR(36) REFERENCES feedbacks(id) 
    COMMENT '合并到的主 Feedback ID';

ALTER TABLE feedbacks ADD COLUMN IF NOT EXISTS
    is_primary BOOLEAN DEFAULT TRUE 
    COMMENT '是否为主 Feedback（未被合并）';

ALTER TABLE feedbacks ADD COLUMN IF NOT EXISTS
    merge_source VARCHAR(20) DEFAULT NULL 
    COMMENT '合并来源: user_manual, ai_auto';

-- 索引
CREATE INDEX idx_feedbacks_merged ON feedbacks(merged_into_id) 
WHERE merged_into_id IS NOT NULL;

CREATE INDEX idx_feedbacks_primary ON feedbacks(is_primary) 
WHERE is_primary = TRUE;
```

### 4.3 API 设计

#### 实时搜索 API
```python
@router.post("/feedbacks/search-similar")
async def search_similar_feedbacks(
    content: str,
    tenant_id: str,
    limit: int = 5
) -> List[SimilarSuggestion]:
    """
    实时搜索相似的 Feedback 和 Topic
    
    返回：
    [
        {
            "type": "topic",
            "id": "topic_001",
            "title": "支持暗黑模式",
            "similarity": 0.92,
            "feedback_count": 15,
            "total_mrr": 500000
        },
        {
            "type": "feedback",
            "id": "feedback_001",
            "content": "希望增加夜间模式",
            "similarity": 0.88,
            "customer_name": "某银行",
            "customer_mrr": 50000
        }
    ]
    """
    # 1. 生成 embedding
    embedding = await ai_service.generate_embedding(content)
    
    # 2. 向量搜索 Topic
    similar_topics = await topic_service.search_by_embedding(
        embedding, limit=3
    )
    
    # 3. 向量搜索 Feedback
    similar_feedbacks = await feedback_service.search_by_embedding(
        embedding, limit=3, is_primary=True
    )
    
    return similar_topics + similar_feedbacks
```

#### 创建 Feedback API（支持关联）
```python
@router.post("/feedbacks")
async def create_feedback(
    data: FeedbackCreate,
    link_to_topic_id: Optional[str] = None,  # 关联到已有 Topic
    merge_into_feedback_id: Optional[str] = None  # 合并到已有 Feedback
) -> Feedback:
    """
    创建 Feedback，支持关联到已有 Topic 或合并到已有 Feedback
    """
    if merge_into_feedback_id:
        # 合并模式：不创建新 Feedback，而是标记为已合并
        return await feedback_service.merge_feedback(
            content=data.content,
            merge_into_id=merge_into_feedback_id,
            merge_source="user_manual"
        )
    
    # 正常创建
    feedback = await feedback_service.create(data)
    
    if link_to_topic_id:
        # 直接关联到已有 Topic
        await feedback_service.link_to_topic(
            feedback.id, link_to_topic_id
        )
    
    return feedback
```

---

## 五、实施建议

### 5.1 渐进式实施路径

#### Phase 1: 优化现有异步聚类（1 周）
- [x] 保持现有流程不变
- [ ] 优化聚类算法（提高准确率）
- [ ] 增加 `merged_into_id` 字段
- [ ] 实现软合并功能

#### Phase 2: 增加实时建议（2 周）
- [ ] 实现实时搜索 API
- [ ] 前端显示相似建议（右侧面板）
- [ ] 支持关联到已有 Topic
- [ ] 支持合并到已有 Feedback

#### Phase 3: 优化审核流程（1 周）
- [ ] Admin 审核界面优化
- [ ] 批量合并功能
- [ ] 聚类质量评分

### 5.2 关键指标

**录入效率**：
- 平均录入时间 < 30 秒
- 实时搜索响应时间 < 500ms

**数据质量**：
- 重复 Feedback 占比 < 20%
- 聚类准确率 > 85%

**用户体验**：
- 员工采纳建议率 > 30%（说明建议有价值）
- Admin 手动调整率 < 15%（说明 AI 聚类质量高）

---

## 六、最终建议

### ✅ 推荐方案：混合模式

**核心理念**：
1. **不强制员工搜索**：保持快速录入体验
2. **提供智能建议**：实时显示相似内容，引导员工关联
3. **AI 兜底**：异步聚类未关联的 Feedback
4. **保留 Topic 抽象**：作为需求管理单元

**与 Canny 的差异**：
| 维度 | Canny | 我们 |
|------|-------|------|
| 去重时机 | 实时（用户提交前） | 实时建议 + 异步聚类 |
| 去重方式 | 用户投票 | 员工关联 + AI 聚类 |
| 数据模型 | 单层（Post） | 双层（Feedback + Topic） |
| 强制性 | 强（必须搜索） | 弱（可选建议） |

**适用场景**：
- ✅ 内部员工录入（销售/客服）
- ✅ 多渠道录入（手动/Excel/截图）
- ✅ 需求管理（Topic 作为需求单元）
- ✅ 优先级决策（聚合客户价值）

---

## 七、实现示例

### 前端交互流程

```vue
<template>
  <div class="feedback-form">
    <!-- 左侧：录入表单 -->
    <div class="form-panel">
      <textarea 
        v-model="content" 
        @input="onContentChange"
        placeholder="输入客户反馈..."
      />
      <button @click="submit">提交</button>
    </div>
    
    <!-- 右侧：实时建议 -->
    <div class="suggestions-panel" v-if="suggestions.length > 0">
      <h3>🔍 发现相似内容</h3>
      
      <div v-for="item in suggestions" :key="item.id">
        <!-- Topic 建议 -->
        <div v-if="item.type === 'topic'" class="suggestion-card">
          <div class="title">{{ item.title }}</div>
          <div class="meta">
            相似度: {{ (item.similarity * 100).toFixed(0) }}% | 
            {{ item.feedback_count }} 条反馈 | 
            总价值: ¥{{ item.total_mrr.toLocaleString() }}
          </div>
          <button @click="linkToTopic(item.id)">
            关联到此主题
          </button>
        </div>
        
        <!-- Feedback 建议 -->
        <div v-else class="suggestion-card">
          <div class="content">{{ item.content }}</div>
          <div class="meta">
            相似度: {{ (item.similarity * 100).toFixed(0) }}% | 
            客户: {{ item.customer_name }}
          </div>
          <button @click="mergeInto(item.id)">
            合并到此反馈
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      content: '',
      suggestions: [],
      debounceTimer: null
    }
  },
  methods: {
    onContentChange() {
      // 防抖：用户停止输入 500ms 后搜索
      clearTimeout(this.debounceTimer);
      this.debounceTimer = setTimeout(() => {
        this.searchSimilar();
      }, 500);
    },
    
    async searchSimilar() {
      if (this.content.length < 10) return;
      
      const res = await api.post('/feedbacks/search-similar', {
        content: this.content
      });
      this.suggestions = res.data;
    },
    
    async linkToTopic(topicId) {
      await api.post('/feedbacks', {
        content: this.content,
        link_to_topic_id: topicId
      });
      this.$message.success('已关联到主题');
    },
    
    async mergeInto(feedbackId) {
      await api.post('/feedbacks', {
        content: this.content,
        merge_into_feedback_id: feedbackId
      });
      this.$message.success('已合并到已有反馈');
    }
  }
}
</script>
```

---

**总结**：采用混合模式，既保留了快速录入的优势，又通过实时建议减少了数据冗余，同时保留 Topic 抽象用于需求管理。这是最适合您场景的方案。

---

**文档维护者**: 技术团队  
**最后更新**: 2025-12-31
