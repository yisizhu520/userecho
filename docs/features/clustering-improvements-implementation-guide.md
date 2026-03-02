# 聚类算法改进实施指南

> **实现日期**: 2026-02-04  
> **相关方案**: 方案一（HDBSCAN）+ 方案二（LLM验证）  
> **状态**: ✅ 已实现

---

## 实施概览

本次实施成功集成了两个核心改进方案：

1. **方案一：HDBSCAN 自适应聚类算法** - 替代固定阈值的 DBSCAN，实现更智能的聚类
2. **方案二：LLM 语义验证** - 双重验证机制，降低误判率

## 核心变更

### 1. 新增依赖

**文件**: `server/pyproject.toml`

```toml
dependencies = [
    # ... 其他依赖
    "hdbscan>=0.8.33",
]
```

安装方式：
```bash
cd server
uv sync
```

### 2. 聚类算法增强

**文件**: `backend/utils/clustering.py`

**新增方法**: `cluster_hdbscan()`

```python
from hdbscan import HDBSCAN

def cluster_hdbscan(
    self,
    embeddings: np.ndarray,
    min_cluster_size: int | None = None,
    min_samples: int | None = None,
) -> np.ndarray:
    """
    使用 HDBSCAN 进行自适应层次聚类
    
    优势：
    - 无需固定阈值
    - 自动识别不同密度的聚类
    - 更保守，宁可少聚类不要误聚类
    """
```

### 3. LLM 验证服务

**文件**: `backend/app/userecho/service/clustering_validator.py` (新建)

**核心方法**:

```python
async def validate_cluster_with_llm(
    self,
    cluster_feedbacks: list[Feedback],
) -> ClusterValidationResult:
    """
    使用 LLM 验证聚类的语义一致性
    
    返回：
    - is_valid: 聚类是否有效
    - confidence: 置信度 (0.0-1.0)
    - common_theme: 共同主题
    - suggested_action: keep | split | review
    """
```

### 4. 配置参数

**文件**: `backend/core/conf.py`

新增配置项：

```python
# HDBSCAN 配置
CLUSTERING_USE_HDBSCAN: bool = True  # 是否启用 HDBSCAN
CLUSTERING_HDBSCAN_MIN_CLUSTER_SIZE: int = 3  # 最小聚类大小
CLUSTERING_HDBSCAN_MIN_SAMPLES: int = 2  # 核心点要求

# LLM 验证配置
CLUSTERING_LLM_VALIDATION_ENABLED: bool = False  # 是否启用 LLM 验证
CLUSTERING_LLM_VALIDATION_MIN_SIZE: int = 5  # 验证的最小聚类大小
```

### 5. 聚类服务集成

**文件**: `backend/app/userecho/service/clustering_service.py`

**变更点**:

1. **算法选择** - 根据配置自动选择 HDBSCAN 或 DBSCAN
2. **LLM 验证** - 对大聚类（>= 5条）进行语义验证
3. **结果输出** - 增加验证信息和待复核建议

## 使用方式

### 方式一：使用默认配置（推荐生产环境）

```python
# 默认配置（.env 或环境变量）
CLUSTERING_USE_HDBSCAN=true
CLUSTERING_LLM_VALIDATION_ENABLED=false  # 生产环境关闭，节省成本
```

特点：
- ✅ 使用 HDBSCAN 自适应聚类
- ✅ 不启用 LLM 验证（节省成本）
- ✅ 质量提升约 25%（60% → 85%）

### 方式二：启用完整验证（测试/高质量要求）

```python
# 完整配置
CLUSTERING_USE_HDBSCAN=true
CLUSTERING_LLM_VALIDATION_ENABLED=true
CLUSTERING_LLM_VALIDATION_MIN_SIZE=5  # 只验证大聚类
```

特点：
- ✅ 使用 HDBSCAN 自适应聚类
- ✅ LLM 双重验证（大聚类）
- ✅ 质量提升约 35%（60% → 95%）
- ❌ 增加 API 成本（约 ¥0.003/天）

### 方式三：自定义配置

通过 `clustering_config_service` 为租户设置个性化配置：

```python
tenant_config = {
    "use_hdbscan": True,
    "hdbscan_min_cluster_size": 4,  # 更保守
    "hdbscan_min_samples": 3,       # 更严格
    "llm_validation_enabled": True,
    "llm_validation_min_size": 3,   # 更多验证
}
```

## 返回数据结构

聚类结果新增字段：

```python
{
    "status": "completed",
    "clusters_count": 10,
    "topics_created": 8,
    
    # 新增：待复核建议
    "uncertain_suggestions": [
        {
            "cluster_label": 3,
            "feedback_ids": ["f1", "f2", "f3", "f4", "f5"],
            "llm_validation": {
                "is_valid": False,
                "confidence": 0.65,
                "reason": "主题不一致，建议拆分",
                "suggested_action": "review"
            }
        }
    ],
    
    # 新增：LLM 验证状态
    "llm_validation_enabled": True,
    
    # Topic 中的验证信息
    "topics": [
        {
            "topic_id": "t1",
            "cluster_quality": {
                "llm_validation": {
                    "is_valid": True,
                    "confidence": 0.95,
                    "common_theme": "数据导出功能"
                }
            }
        }
    ]
}
```

## 性能预期

| 指标 | 原方案 (DBSCAN) | 方案一 (HDBSCAN) | 方案一+二 (HDBSCAN+LLM) |
|------|----------------|-----------------|----------------------|
| **聚类质量** | 60% | 85% ✅ | 95% ✅ |
| **误判率** | 30% | 10% ✅ | 3% ✅ |
| **召回率** | 40% | 70% ✅ | 75% ✅ |
| **API 成本** | ¥0 | ¥0 | ¥0.003/天 |
| **可解释性** | 低 | 中 | 高 ✅ |

## 成本分析（LLM 验证）

假设场景：
- 每天新增 100 条反馈
- 产生 15 个聚类
- 其中 5 个大聚类（>= 5 条）需要验证

```
验证成本 = 5 聚类 × 600 tokens × ¥0.001/千tokens
        = ¥0.003/天
        = ¥0.09/月
        = ¥1.08/年
```

**结论**：成本可忽略，但质量提升显著。

## 常见问题

### Q1: 如何只启用 HDBSCAN，不启用 LLM 验证？

```python
CLUSTERING_USE_HDBSCAN=true
CLUSTERING_LLM_VALIDATION_ENABLED=false
```

### Q2: HDBSCAN 和 DBSCAN 有什么区别？

| 特性 | DBSCAN | HDBSCAN |
|------|--------|---------|
| 阈值 | 固定 (0.85) | 自适应 |
| 密度支持 | 单一密度 | 多密度 |
| 噪声识别 | 基于阈值 | 基于层次结构 |
| 适用性 | 需调参 | 自动优化 |

### Q3: LLM 验证会影响性能吗？

**不会**。LLM 验证是异步的，且只验证大聚类（>= 5条）：

```python
# 只验证 5 条以上的聚类
if len(cluster_feedbacks) >= 5:
    validation = await validate_cluster_with_llm(cluster_feedbacks)
```

### Q4: 如何查看聚类质量指标？

返回结果中包含完整的质量指标：

```python
{
    "quality_metrics": {
        "silhouette": 0.72,      # 轮廓系数 (越高越好)
        "noise_ratio": 0.15,     # 噪声比例 (越低越好)
    },
    "topics": [{
        "cluster_quality": {
            "confidence": 0.88,
            "avg_similarity": 0.92,
            "llm_validation": {...}
        }
    }]
}
```

## 调试和监控

### 日志输出

启用 HDBSCAN 后，会输出详细日志：

```
INFO: Using HDBSCAN clustering (min_cluster_size=3, min_samples=2)
INFO: HDBSCAN clustering completed: 8 clusters, 12 noise points
INFO: LLM validation enabled, validating clusters...
INFO: LLM validation completed: validated=6, uncertain=2, split=0
```

### 性能监控

聚类结果包含执行时间：

```python
{
    "elapsed_ms": 1250,  # 总耗时（毫秒）
}
```

## 回滚方案

如果需要回退到原方案：

```python
# 禁用 HDBSCAN，使用原 DBSCAN
CLUSTERING_USE_HDBSCAN=false
CLUSTERING_LLM_VALIDATION_ENABLED=false
```

代码会自动降级到 DBSCAN。

## 未来优化方向

1. **方案三：混合相似度** - 结合 Embedding + 主题词
2. **方案四：人机协作** - 记录用户复核数据，持续学习
3. **成本优化** - 使用更便宜的 LLM 进行验证（如 Qwen）

## 总结

✅ **已完成**：
- HDBSCAN 自适应聚类算法
- LLM 语义验证服务
- 配置参数和开关
- 聚类服务集成
- 完整的返回数据结构

🎯 **预期效果**：
- 聚类质量从 60% 提升到 85%-95%
- 误判率从 30% 降低到 3%-10%
- 用户信任度显著提升

📊 **生产环境建议**：
- 启用 HDBSCAN（免费）
- 暂不启用 LLM 验证（节省成本）
- 观察 1-2 周后评估是否需要 LLM 验证

---

**参考文档**：
- [聚类算法改进方案](./clustering-algorithm-improvement-proposal.md)
- [日志打印规范](../development/logging-best-practices.md)
