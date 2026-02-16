# 优先级评分引擎实现总结

> **完成时间：** 2025-12-28  
> **状态：** ✅ 已完成核心功能

---

## 一、实现内容

### 后端实现

#### 1. 核心服务 (`priority_service.py`)

**文件：** `server/backend/app/userecho/service/priority_service.py`

实现功能：
- ✅ 商业价值自动计算（基于客户等级）
- ✅ 影响范围快速规则判断（聚类时使用）
- ✅ 开发成本快速规则判断（聚类时使用）
- ✅ 默认评分自动生成（聚类后立即生成）
- ✅ 评分创建/更新

**核心算法：**
```python
# 商业价值 = 最高客户等级权重 + 多客户加成 + 大客户加成
商业价值 = max(客户类型分数) + (客户数>=3 ? 1 : 0) + (有大客户 ? 2 : 0)

# 影响范围（快速规则）
if 客户数 >= 10: return 10
elif 客户数 >= 5: return 5
elif 客户数 >= 2: return 3
else: return 1

# 开发成本（快速规则）
if '崩溃' in 标题: return 1天
elif '新增' in 标题: return 5天
else: 根据分类（Bug=1天, 新功能=5天, 其他=3天）
```

---

#### 2. AI 完整分析 (`ai_client.py`)

**文件：** `server/backend/utils/ai_client.py`

新增方法：
- ✅ `suggest_impact_scope_ai()` - AI 分析影响范围（详情页调用）
- ✅ `suggest_dev_cost_ai()` - AI 建议开发成本（详情页调用）

**特点：**
- 关键词匹配作为快速降级方案
- 仅对重要需求（客户数 >= 5）调用 AI
- 失败自动降级到规则判断
- 返回包含置信度和理由

---

#### 3. API 接口 (`priority.py`)

**文件：** `server/backend/app/userecho/api/v1/priority.py`

新增接口：
- ✅ `POST /api/v1/app/topics/{id}/priority/analyze` - AI 完整分析
- ✅ `POST /api/v1/app/topics/{id}/priority` - 保存评分
- ✅ `GET /api/v1/app/topics/{id}/priority` - 获取评分
- ✅ `DELETE /api/v1/app/topics/{id}/priority` - 删除评分

---

#### 4. 聚类集成

**文件：** `server/backend/app/userecho/service/clustering_service.py`

修改内容：
- ✅ 在创建 Topic 后自动生成默认评分
- ✅ 使用快速规则（不调用 AI，节省成本）
- ✅ 评分失败不影响聚类流程

---

#### 5. 数据模型扩展

**文件：** `server/backend/app/userecho/model/topic.py`

- ✅ 添加 `priority_score` relationship（1:1 关联）
- ✅ 使用 `lazy='joined'` 自动加载

**文件：** `server/backend/app/userecho/schema/topic.py`

- ✅ `TopicOut` 添加 `priority_score` 字段
- ✅ 列表 API 返回包含评分

---

### 前端实现

#### 1. API 封装

**文件：** `front/apps/web-antd/src/api/userecho/priority.ts`

新增方法：
- ✅ `analyzePriority()` - AI 分析
- ✅ `createOrUpdatePriorityScore()` - 保存评分
- ✅ `getPriorityScore()` - 获取评分
- ✅ `deletePriorityScore()` - 删除评分

---

#### 2. 详情页评分卡片

**文件：** `front/apps/web-antd/src/views/userecho/topic/components/PriorityScoreCard.vue`

功能：
- ✅ 自动加载已有评分或触发 AI 分析
- ✅ 显示 AI 建议 + 置信度 + 理由
- ✅ 商业价值滑块调整（1-10分）
- ✅ 影响范围下拉选择（1/3/5/10）
- ✅ 开发成本单选按钮（1/3/5/10天）
- ✅ 实时计算总分预览
- ✅ 优先级颜色区分（红/橙/蓝/灰）
- ✅ 一键采纳或手动调整

---

#### 3. 列表页优先级列

**文件：** `front/apps/web-antd/src/views/userecho/topic/list.vue`

功能：
- ✅ 新增「优先级」列
- ✅ 显示总分徽章（带颜色区分）
- ✅ 未评分显示「未评分」提示
- ✅ 点击跳转到详情页

**文件：** `front/apps/web-antd/src/views/userecho/topic/data.ts`

- ✅ 添加 `priority_score` 列配置

---

## 二、数据流

### 聚类时自动生成默认评分

```
1. AI 聚类创建 Topic
   ↓
2. 统计客户数量、反馈数量
   ↓
3. 快速规则判断：
   - 商业价值：自动计算（从客户等级）
   - 影响范围：客户数量映射（不调用 AI）
   - 开发成本：分类 + 关键词匹配（不调用 AI）
   ↓
4. 创建 PriorityScore 记录
   ↓
5. 前端列表显示优先级总分
```

---

### 详情页 AI 重新分析

```
1. PM 打开 Topic 详情页
   ↓
2. 加载已有评分或自动触发 AI 分析
   ↓
3. AI 完整分析（调用 LLM）：
   - 商业价值：自动计算（实时）
   - 影响范围：AI 分析 + 关键词匹配
   - 开发成本：AI 建议 + 分类规则
   ↓
4. 显示 AI 建议 + 置信度 + 理由
   ↓
5. PM 可以：
   - 一键采纳 AI 建议
   - 手动调整各维度分数
   - 点击「AI 重新分析」
   ↓
6. 保存评分 → 更新总分 → 列表显示
```

---

## 三、评分规则

### 计算公式

```
优先级总分 = (影响范围 × 商业价值) / 开发成本 × 紧急系数

其中：
- 影响范围：1/3/5/10 (个别/部分/大多数/全部)
- 商业价值：1-10 (自动计算或手动调整)
- 开发成本：1/3/5/10 (1天/3天/5天/10天+)
- 紧急系数：1.0 或 1.5 (有紧急反馈时为 1.5)
```

### 优先级颜色

- **红色** (score >= 15): 高优先级
- **橙色** (score >= 10): 中高优先级
- **蓝色** (score >= 5): 中优先级
- **灰色** (score < 5): 低优先级

---

## 四、使用流程

### 1. 聚类后自动评分

```bash
# 1. 导入反馈
POST /api/v1/app/feedbacks/import

# 2. 触发聚类
POST /api/v1/app/clustering/batch

# 3. 聚类完成后，每个 Topic 自动生成默认评分
# 查看列表时可直接看到优先级
GET /api/v1/app/topics
```

---

### 2. 详情页手动调整

```bash
# 1. 打开详情页（自动加载评分或触发 AI 分析）
GET /app/topic/detail/:id

# 2. 查看 AI 建议（包含置信度和理由）

# 3. PM 可以：
   - 调整商业价值（拖动滑块）
   - 调整影响范围（下拉选择）
   - 调整开发成本（单选按钮）

# 4. 实时预览总分

# 5. 点击「保存评分」
POST /api/v1/app/topics/:id/priority

# 6. 点击「AI 重新分析」（可选）
POST /api/v1/app/topics/:id/priority/analyze
```

---

## 五、边界处理

### 1. 未关联客户的 Topic

**问题：** 如果 Topic 没有关联客户（纯匿名反馈）  
**处理：** 商业价值默认为 1 分，记录警告日志

### 2. AI 调用失败

**问题：** AI 服务不可用或超时  
**处理：**
- 影响范围：降级到客户数量规则判断
- 开发成本：降级到分类 + 关键词匹配
- 商业价值：始终使用规则计算（不依赖 AI）

### 3. 评分并发冲突

**问题：** 多人同时修改评分  
**处理：** 使用 `upsert`，后保存的覆盖前面的（Last Write Wins）

### 4. 聚类评分失败

**问题：** 评分服务异常导致聚类失败  
**处理：** 评分失败仅记录警告，不影响聚类流程继续

---

## 六、性能优化

### 1. 聚类时不调用 AI

**原因：** 聚类一次可能创建 10-20 个 Topic，大量调用 AI 成本高且慢  
**方案：** 使用快速规则生成默认评分，PM 需要时再点「AI 重新分析」

### 2. 列表 API 使用 joinedload

**原因：** 避免 N+1 查询问题  
**方案：** 使用 `joinedload(Topic.priority_score)` 一次性加载所有评分

### 3. AI 分析仅针对重要需求

**原因：** 单个客户的小需求不值得调用 LLM  
**方案：** 仅对客户数 >= 5 的 Topic 调用 AI，其他使用规则

---

## 七、待优化项（V1.1）

### 1. 批量评分

**需求：** 列表页批量选择 Topic 进行快速评分  
**实现：** 弹窗表单 + 批量 API

### 2. 评分历史

**需求：** 记录谁在何时修改了评分  
**实现：** 新建 `priority_score_history` 表

### 3. 按优先级排序

**需求：** 列表页按优先级排序  
**实现：** 后端支持 `sort_by=total_score`

### 4. 评分准确度追踪

**需求：** PM 反馈 AI 建议是否准确  
**实现：** 评分保存时记录「是否采纳 AI 建议」

---

## 八、文件清单

### 后端新建文件
- `server/backend/app/userecho/service/priority_service.py` - 核心服务
- `server/backend/app/userecho/api/v1/priority.py` - API 接口

### 后端修改文件
- `server/backend/utils/ai_client.py` - 扩展 AI 分析方法
- `server/backend/app/userecho/service/clustering_service.py` - 聚类时生成评分
- `server/backend/app/userecho/model/topic.py` - 添加 relationship
- `server/backend/app/userecho/schema/topic.py` - 添加 priority_score 字段
- `server/backend/app/userecho/crud/crud_topic.py` - 列表加载评分

### 前端新建文件
- `front/apps/web-antd/src/views/userecho/topic/components/PriorityScoreCard.vue` - 评分卡片组件

### 前端修改文件
- `front/apps/web-antd/src/api/userecho/priority.ts` - API 方法
- `front/apps/web-antd/src/api/userecho/topic.ts` - 类型定义
- `front/apps/web-antd/src/views/userecho/topic/detail.vue` - 详情页集成
- `front/apps/web-antd/src/views/userecho/topic/list.vue` - 列表页优先级列
- `front/apps/web-antd/src/views/userecho/topic/data.ts` - 表格列配置

---

## 九、测试建议

### 1. 功能测试

- [ ] 聚类后自动生成默认评分
- [ ] 详情页自动触发 AI 分析
- [ ] 商业价值自动计算正确（不同客户等级）
- [ ] 影响范围 AI 建议合理
- [ ] 开发成本 AI 建议合理
- [ ] 手动调整评分并保存成功
- [ ] 列表页显示优先级总分徽章
- [ ] 优先级颜色区分正确

### 2. 边界测试

- [ ] 未关联客户的 Topic 处理
- [ ] AI 调用失败降级方案
- [ ] 并发评分不冲突
- [ ] 聚类评分失败不影响聚类

### 3. 性能测试

- [ ] 列表加载 100 个 Topic < 1秒
- [ ] AI 分析单个 Topic < 10秒
- [ ] 聚类 100 条反馈（含评分）< 30秒

---

**完成状态：✅ 核心功能已全部实现**

剩余工作：功能测试 + Bug 修复
