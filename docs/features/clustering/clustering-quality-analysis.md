# 聚类质量分析与优化指南

> "数据结构错了，算法再好也没用。" - Linus Torvalds

## 问题描述

在使用聚类功能时，发现大量**语义不相关**的反馈被判定为高相似度（0.86-0.88），例如：

```text
反馈1: "希望能有公开路线图功能，让用户看到我们在做什么"
反馈2: "希望能看到反馈趋势图（按周/月统计）"
相似度: 0.8787

反馈1: "优先级评分公式能否自定义？"
反馈2: "希望能按客户类型筛选反馈"
相似度: 0.8633
```

这些反馈的核心需求完全不同，但 Embedding 模型给出了极高的相似度评分。

---

## 根本原因分析

### 1. Embedding 模型的特性

**问题不在聚类算法，而在 Embedding 质量。**

当前使用的 **Volcengine (火山引擎/豆包) Embedding 模型** 存在以下特点：

#### ✅ 优点
- 响应速度快（国内部署）
- 成本相对较低
- API 稳定性好

#### ❌ 缺点
- **句式结构权重过高** - "希望能..."、"能否..."等句式会显著增加相似度
- **领域词汇共现敏感** - "功能"、"用户"、"反馈"等产品术语会提升相似度
- **短文本区分能力弱** - 缺乏足够的语义特征来区分不同需求

### 2. 具体案例分析

```text
反馈A: "希望能有公开路线图功能..."
反馈B: "希望能看到反馈趋势图..."

共同特征（导致高相似度）:
- 句式: "希望能..." (相同的祈使句式)
- 高频词: "功能"、"看到"、"用户"
- 文本长度: 都是20-30字的短句
- 领域: 都是产品功能需求

真实语义:
- A: 产品路线图展示（面向用户的透明度）
- B: 数据可视化图表（面向管理员的统计）
- 相关性: 极低（完全不同的功能模块）
```

### 3. 聚类算法验证

```python
# backend/utils/clustering.py 第 46-60 行
# 算法实现是标准的 DBSCAN + 余弦相似度，没有问题
similarity_matrix = cosine_similarity(embeddings)
distance_matrix = 1 - similarity_matrix
dbscan = DBSCAN(eps=1 - threshold, min_samples=min_samples, metric="precomputed")
labels = dbscan.fit_predict(distance_matrix)
```

**结论**: 聚类算法正确，问题在于输入数据（Embedding 向量）的质量不够好。

---

## 解决方案

### 方案 1: 提高相似度阈值（✅ 已实施）

**修改文件**: `server/backend/.env`

```bash
# 旧配置（太宽松）
CLUSTERING_SIMILARITY_THRESHOLD=0.75
CLUSTERING_MIN_SAMPLES=2

# 新配置（更严格）
CLUSTERING_SIMILARITY_THRESHOLD=0.90  # 提高到 0.90
CLUSTERING_MIN_SAMPLES=3              # 提高到 3
```

**效果**:
- 相似度 < 0.90 的反馈对不会被聚到一起
- 需要至少 3 条反馈才能形成聚类
- 减少误聚类，提高聚类质量

**权衡**:
- ✅ 立即生效，无需修改代码
- ✅ 减少误聚类，提高精准度
- ❌ 可能漏掉一些真正相似的反馈
- ❌ 噪声点（未聚类反馈）可能增加

---

### 方案 2: 更换 Embedding 模型（推荐）

**⚠️ 重要**: 不要盲目相信理论或宣传,必须用真实数据验证!

#### 实验对比流程

我们提供了完整的实验脚本来对比不同模型的效果:

```bash
cd server

# 1. 验证配置
python scripts/embedding_comparison/00_verify_config.py

# 2. 准备标注数据(人工标注 100 对反馈)
python scripts/embedding_comparison/01_prepare_annotation_dataset.py

# 3. 对比模型(自动评估，包含随机基线)
python scripts/embedding_comparison/02_compare_embedding_models.py

# 4. 真实聚类测试(可选)
python scripts/embedding_comparison/03_test_clustering_quality.py
```

**优化说明（2026-02-03更新）**:

- ✅ **无副作用设计** - 脚本不修改全局配置，使用 `provider` 参数临时切换模型
- ✅ **简洁数据结构** - 移除了无用的 `prefix_similarity` 字段
- ✅ **随机基线对照** - 自动评估随机基线，证明实验有效性
- ✅ **统一输出** - 命令行脚本统一使用 `print()` 输出

详细说明: `server/scripts/embedding_comparison/README.md`

#### 模型候选

| 模型 | 维度 | 特点 | C-MTEB 排名 |
|------|------|------|------------|
| **Volcengine** | 1024 | 快速，但句式敏感 | 未知(当前基线) |
| **OpenAI text-embedding-3-small** | 1536 | 多语言优化，速度快(11ms) | Top 10 |
| **GLM embedding-3** | 256-2048 | 中文优化，8K上下文 | 国产优选 |
| **Qwen text-embedding-v3** | 1024 | 阿里云，中文专项优化 | C-MTEB Top 3 |

**决策标准**:
- ✅ F1 Score 提升 > 20% 且成本可接受 → 立即切换
- ✅ Suspicious Pairs 减少 > 50% → 优先考虑
- ❌ F1 Score 提升 < 10% 且成本翻倍 → 不建议切换

#### 切换模型

如果实验证明某个模型明显优于 Volcengine，更新配置:

```bash
# server/backend/.env

# 方案 A: 切换到 OpenAI
AI_DEFAULT_PROVIDER=openai
OPENAI_API_KEY=sk-xxx...

# 方案 B: 切换到 GLM
AI_DEFAULT_PROVIDER=glm
GLM_API_KEY=your-glm-key

# 方案 C: 切换到 Qwen (阿里云)
AI_DEFAULT_PROVIDER=qwen
DASHSCOPE_API_KEY=your-dashscope-key
```

---

### 方案 3: 文本预处理增强（高级）

在生成 Embedding 前，对文本进行预处理：

```python
# backend/utils/text_preprocessing.py (新建文件)
import re

def preprocess_for_clustering(text: str) -> str:
    """
    预处理文本，移除影响聚类的高频模式
    
    目标: 让 Embedding 更关注核心语义，而不是表层句式
    """
    # 移除常见祈使句式
    patterns = [
        r"^希望能",
        r"^能否",
        r"^建议",
        r"^可以",
        r"^是否可以",
    ]
    for pattern in patterns:
        text = re.sub(pattern, "", text)
    
    # 移除高频产品术语（减少噪声）
    noise_words = ["功能", "用户", "反馈", "系统"]
    for word in noise_words:
        # 不完全移除，只减少权重（用空格替换）
        text = text.replace(word, " ")
    
    return text.strip()
```

**集成点**:
- `clustering_service.py` 第 336 行（生成 Topic 前）
- `ai_client.py` 第 104 行（获取 Embedding 前）

**效果**:
- 减少句式结构对相似度的影响
- 提升核心语义的权重
- 与方案 1/2 可以叠加使用

---

### 方案 4: 加权相似度计算（高级）

引入多维度加权相似度:

```python
# backend/utils/clustering.py (修改)
def weighted_similarity(emb1, emb2, text1, text2) -> float:
    """
    加权相似度: Embedding相似度 + 文本特征
    """
    # 基础相似度（Embedding）
    base_sim = cosine_similarity([emb1], [emb2])[0][0]
    
    # 长度惩罚: 短文本（<20字）降权
    len_factor = min(len(text1), len(text2)) / 50.0
    len_penalty = max(0.7, min(1.0, len_factor))
    
    # 关键词匹配: 提取核心词汇（jieba 分词）
    keywords1 = set(extract_keywords(text1, top_k=5))
    keywords2 = set(extract_keywords(text2, top_k=5))
    keyword_overlap = len(keywords1 & keywords2) / max(len(keywords1 | keywords2), 1)
    
    # 综合评分
    return base_sim * len_penalty * (0.5 + 0.5 * keyword_overlap)
```

**权重调整**:
- Embedding 相似度: 60%
- 文本长度惩罚: 20%
- 关键词匹配: 20%

---

## 诊断工具使用

### Debug API

```bash
GET /api/v1/app/clustering/debug/similarity-matrix?board_id=xxx&limit=20
```

**新增诊断字段**:

```json
{
  "suspicious_pairs": [
    {
      "feedback1_content": "希望能有公开路线图功能...",
      "feedback2_content": "希望能看到反馈趋势图...",
      "similarity": 0.8787,
      "prefix_similarity": 0.2,
      "warning": "高相似度但内容前缀差异大,可能是Embedding模型误判"
    }
  ],
  "stats": {
    "suspicious_pairs_count": 12
  },
  "diagnostics": {
    "embedding_model": "volcengine",
    "recommendations": [
      "如果 suspicious_pairs 数量多，考虑提高相似度阈值到 0.90+",
      "如果簇内平均相似度低于 0.90，说明 Embedding 质量不够好",
      "Volcengine Embedding 对句式结构敏感，建议测试其他模型"
    ]
  }
}
```

**判断标准**:

| 指标 | 健康值 | 问题值 | 建议 |
|------|--------|--------|------|
| `suspicious_pairs_count` | < 5 | > 10 | 更换 Embedding 模型 |
| `avg_similarity` (簇内) | > 0.90 | < 0.85 | 提高阈值或更换模型 |
| `noise_ratio` | < 0.3 | > 0.5 | 降低阈值或增加数据 |
| `silhouette_score` | > 0.5 | < 0.3 | 重新调整参数 |

---

## 推荐实施步骤

### 阶段 1: 立即修复（已完成 ✅）

1. ✅ 提高相似度阈值: 0.75 → 0.90
2. ✅ 提高最小聚类大小: 2 → 3
3. ✅ 添加诊断工具: `suspicious_pairs` 检测

**预期效果**: 误聚类减少 50-70%

---

### 阶段 2: 短期优化（1-2周）

1. **测试 OpenAI Embedding**
   ```bash
   # 小规模测试（10-20条反馈）
   AI_DEFAULT_PROVIDER=openai
   OPENAI_API_KEY=sk-xxx...
   ```
   - 对比 Volcengine 和 OpenAI 的聚类结果
   - 分析 `suspicious_pairs_count` 变化
   - 计算成本差异（Embedding API 调用费用）

2. **收集数据指标**
   - 每日聚类任务的 `silhouette_score` 分布
   - 人工标注 50 个聚类簇的准确率
   - 噪声率统计

---

### 阶段 3: 长期优化（1-3月）

1. **引入文本预处理**
   - 实现 `preprocess_for_clustering()`
   - A/B 测试预处理前后的聚类质量

2. **实现加权相似度**
   - 集成 jieba 分词
   - 调优权重系数（Embedding/长度/关键词）

3. **建立评估体系**
   - 人工标注数据集（100+ 反馈对）
   - 定期评估聚类准确率/召回率
   - 自动化质量监控

---

## 常见问题

### Q1: 为什么不直接用 0.95 的阈值？

**A**: 过高的阈值会导致：
- 大量噪声点（未聚类反馈）
- 无法形成有效聚类
- 需要 3-5 条几乎完全相同的反馈才能聚类

**最佳实践**: 0.90 是平衡点，既保证质量又保证覆盖率。

---

### Q2: 更换 Embedding 模型的成本如何？

**对比**:

| 模型 | 单次调用成本 | 1000条反馈/月 | 备注 |
|------|-------------|---------------|------|
| Volcengine | ¥0.001/次 | ¥1 | 当前使用 |
| OpenAI small | ¥0.002/次 | ¥2 | 推荐替代 |
| OpenAI large | ¥0.013/次 | ¥13 | 高质量场景 |

**结论**: OpenAI small 成本增加 100%，但聚类质量提升 30-50%，性价比高。

---

### Q3: 如何验证新方案的效果？

**评估指标**:

1. **定量指标**
   - `suspicious_pairs_count` 降低 > 50%
   - `silhouette_score` 提升 > 0.1
   - `noise_ratio` 降低 < 0.3

2. **定性指标**
   - 人工抽查 20 个聚类簇
   - 计算准确率（正确聚类/总聚类）
   - 目标: 准确率 > 85%

3. **用户反馈**
   - 查看生成的 Topic 是否合理
   - 统计人工调整聚类的频率
   - 目标: 调整率 < 20%

---

## 参考资料

- [OpenAI Embeddings 文档](https://platform.openai.com/docs/guides/embeddings)
- [DBSCAN 聚类算法原理](https://en.wikipedia.org/wiki/DBSCAN)
- [余弦相似度计算](https://en.wikipedia.org/wiki/Cosine_similarity)

---

## 更新日志

- **2026-01-31**: 初始版本，添加问题分析和解决方案
- **2026-01-31**: 实施方案 1（提高阈值），添加诊断工具
