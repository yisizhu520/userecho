# HDBSCAN + LLM 校验启用文档

## 📋 修改清单

### 1. ✅ 修改 `clustering_service.py`

**位置**: `backend/app/userecho/service/clustering_service.py`

**改动**:
1. 导入 `ClusteringValidator` 和 `settings`
2. 根据 `CLUSTERING_USE_HDBSCAN` 配置选择算法：
   - `True`: 使用 HDBSCAN（自适应层次聚类）
   - `False`: 使用 DBSCAN（固定阈值）
3. 新增 LLM 校验流程（当 `CLUSTERING_LLM_VALIDATION_ENABLED=True`）：
   - 对 size >= `CLUSTERING_LLM_VALIDATION_MIN_SIZE` 的聚类进行语义校验
   - 如果 LLM 判断语义一致，保留原聚类
   - 如果 LLM 判断语义混杂，按建议拆分为子聚类
   - 如果 LLM 无法拆分，标记为噪声点

### 2. ✅ 更新配置文件

**位置**: `backend/core/conf.py`

**改动**:
```python
CLUSTERING_LLM_VALIDATION_ENABLED: bool = True  # ✅ 启用 LLM 验证
```

**完整聚类配置**:
```python
# DBSCAN 基础配置（当 CLUSTERING_USE_HDBSCAN=False 时使用）
CLUSTERING_SIMILARITY_THRESHOLD: float = 0.85  # 相似度阈值
CLUSTERING_MIN_SAMPLES: int = 2               # 最小聚类大小

# 质量门槛
CLUSTERING_MIN_SILHOUETTE: float = 0.3        # 最低轮廓系数
CLUSTERING_MAX_NOISE_RATIO: float = 0.5       # 最高噪声率

# HDBSCAN 配置
CLUSTERING_USE_HDBSCAN: bool = True           # ✅ 启用 HDBSCAN
CLUSTERING_HDBSCAN_MIN_CLUSTER_SIZE: int = 3  # 最小聚类大小
CLUSTERING_HDBSCAN_MIN_SAMPLES: int = 2       # 核心点要求

# LLM 校验配置
CLUSTERING_LLM_VALIDATION_ENABLED: bool = True # ✅ 启用 LLM 校验
CLUSTERING_LLM_VALIDATION_MIN_SIZE: int = 5    # LLM 校验阈值
```

### 3. ✅ 创建测试脚本

**位置**: `server/test_hdbscan_llm.py`

**用途**: 验证 HDBSCAN + LLM 校验是否正常工作

## 🔄 工作流程

### 阶段 1: HDBSCAN 聚类
```
待聚类反馈 (48 条)
    ↓
获取 embeddings (VOLCENGINE)
    ↓
HDBSCAN 自适应聚类
    ↓
初始聚类结果 (N 个聚类 + 噪声点)
```

### 阶段 2: LLM 语义校验（可选）
```
对每个 size >= 5 的聚类：
    ↓
提交给 LLM 判断语义一致性
    ↓
    ├─ 一致 → 保留原聚类
    ├─ 混杂 → 拆分为子聚类（如果有建议）
    └─ 无法拆分 → 标记为噪声
```

### 阶段 3: 质量门槛检查
```
计算质量指标：
  - silhouette (轮廓系数)
  - noise_ratio (噪声比例)
    ↓
    ├─ 通过 → 创建 Topic
    └─ 不通过 → 延期（等待更多数据）
```

## 🧪 测试步骤

### 1. 检查配置
```bash
cd server
python test_hdbscan_llm.py
```

预期输出：
```
📊 当前配置:
   - CLUSTERING_USE_HDBSCAN: True
   - CLUSTERING_HDBSCAN_MIN_CLUSTER_SIZE: 3
   - CLUSTERING_HDBSCAN_MIN_SAMPLES: 2
   - CLUSTERING_LLM_VALIDATION_ENABLED: True
   - CLUSTERING_LLM_VALIDATION_MIN_SIZE: 5

✅ 配置检查通过
```

### 2. 前端触发聚类

1. 确保有至少 48 条待聚类反馈
2. 在前端点击"开始聚类"按钮
3. 观察 Worker 日志

预期日志：
```
Using HDBSCAN: min_cluster_size=3, min_samples=2
HDBSCAN clustering completed: X clusters, Y noise points
LLM validation enabled: validating clusters with size >= 5
Cluster #0 validated: 5 feedbacks - 邮件通知功能
Cluster #1 split into 2 sub-clusters: 包含两个独立主题
  → Sub-cluster: 数据导出功能 (3 feedbacks)
  → Sub-cluster: 搜索优化 (2 feedbacks)
LLM validation completed: validated=N, split=M, final_clusters=X
```

### 3. 对比测试（可选）

切换配置测试不同算法：

```python
# 测试 1: 仅 HDBSCAN
CLUSTERING_USE_HDBSCAN=True
CLUSTERING_LLM_VALIDATION_ENABLED=False

# 测试 2: HDBSCAN + LLM
CLUSTERING_USE_HDBSCAN=True
CLUSTERING_LLM_VALIDATION_ENABLED=True

# 测试 3: 旧方案 DBSCAN
CLUSTERING_USE_HDBSCAN=False
CLUSTERING_LLM_VALIDATION_ENABLED=False
```

## 📊 预期效果

### HDBSCAN 优势
- ✅ 自适应阈值：不同密度的聚类都能识别
- ✅ 层次结构：能发现嵌套的主题关系
- ✅ 更少噪声：比 DBSCAN 更智能地判断孤立点

### LLM 校验优势
- ✅ 语义准确：拆分混杂主题（如"导出+通知"）
- ✅ 质量提升：避免不相关反馈被聚在一起
- ✅ 成本可控：只验证大聚类（size >= 5）

### 潜在问题
- ⚠️ LLM 成本：每个大聚类需要 1 次 API 调用
- ⚠️ 处理时间：LLM 校验增加 2-5 秒延迟
- ⚠️ 拆分过细：可能产生更多小聚类

## 🔧 微调建议

### 如果聚类太多（过拟合）
```python
# 提高 HDBSCAN 门槛
CLUSTERING_HDBSCAN_MIN_CLUSTER_SIZE = 4  # 改为 4-5

# 降低 LLM 校验触发阈值
CLUSTERING_LLM_VALIDATION_MIN_SIZE = 8   # 只验证更大的聚类
```

### 如果聚类太少（欠拟合）
```python
# 降低 HDBSCAN 门槛
CLUSTERING_HDBSCAN_MIN_CLUSTER_SIZE = 2

# 提高 LLM 校验触发阈值
CLUSTERING_LLM_VALIDATION_MIN_SIZE = 3
```

### 如果 LLM 成本太高
```python
# 关闭 LLM 校验
CLUSTERING_LLM_VALIDATION_ENABLED = False

# 或者只验证超大聚类
CLUSTERING_LLM_VALIDATION_MIN_SIZE = 10
```

## 🎯 Linus 的评价

> "现在这才像个聪明的系统：
> 
> 1. HDBSCAN 自适应聚类 - 消除了固定阈值的特殊情况
> 2. LLM 语义校验 - 解决了 embedding 相似但语义不同的问题
> 3. 配置开关清晰 - 不想用就关掉，没有垃圾代码
> 
> 但记住：LLM 不是银弹，它只是个工具。
> 真正重要的是你的 embedding 质量和聚类算法。
> LLM 只是最后的保险，不要过度依赖它。"

---

**生成时间**: 2026-02-05  
**修改文件**:
- ✅ `backend/app/userecho/service/clustering_service.py`
- ✅ `backend/core/conf.py`
- ✅ `server/test_hdbscan_llm.py`
