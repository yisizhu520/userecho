# Embedding 模型对比实验

> "用数据说话,不要用理论争论。" - Linus Torvalds

## 问题背景

当前聚类功能使用 **Volcengine (火山引擎) Embedding 模型**,存在以下问题:
- 句式结构权重过高 ("希望能..."、"能否..."等句式会显著增加相似度)
- 领域词汇共现敏感 ("功能"、"用户"、"反馈"等产品术语会提升相似度)
- 短文本区分能力弱

**具体案例**:
```text
反馈1: "希望能有公开路线图功能,让用户看到我们在做什么"
反馈2: "希望能看到反馈趋势图(按周/月统计)"
相似度: 0.8787 (实际上完全不相关!)
```

## 实验目标

对比 **Volcengine、OpenAI、GLM、Qwen** 四个模型在中文反馈聚类场景的表现,选出最优模型。

## 实验流程

### 0. 环境准备

#### 0.1 配置 API Keys

编辑 `server/backend/.env`,确保以下配置存在:

```bash
# Volcengine (已有)
VOLCENGINE_API_KEY=your-volcengine-key
VOLCENGINE_EMBEDDING_ENDPOINT=ep-xxx

# OpenAI (需要配置)
OPENAI_API_KEY=sk-xxx...

# GLM 智谱 (需要配置)
GLM_API_KEY=your-glm-key

# Qwen 通义千问 (需要配置)
DASHSCOPE_API_KEY=your-dashscope-key
```

**获取 API Key**:
- **OpenAI**: https://platform.openai.com/api-keys
- **GLM (智谱)**: https://bigmodel.cn/ (注册后在控制台获取)
- **Qwen (阿里云)**: https://dashscope.console.aliyun.com/ (阿里云百炼平台)

#### 0.2 安装依赖

```bash
cd server
uv sync
```

---

### 1. 准备标注数据集

**目标**: 从真实反馈中导出 100 对标注数据 (50 相似 + 50 不相似)

```bash
cd server
python scripts/embedding_comparison/01_prepare_annotation_dataset.py
```

**流程**:
1. 自动分析反馈,导出可疑的高相似度对 (相似度 >= 0.85)
2. 人工标注每一对是否真正相似
3. 保存标注结果到 `scripts/embedding_comparison/data/annotation_dataset.json`

**交互式标注**:
```text
反馈1: "希望能有公开路线图功能..."
反馈2: "希望能看到反馈趋势图..."
相似度: 0.8787

是否相似?(y/n/s/q):
  y - 相似 (同一需求的不同表达)
  n - 不相似 (完全不同的需求)
  s - 跳过当前对
  q - 退出标注
```

**预期耗时**: 30-60 分钟

---

### 2. 对比 Embedding 模型

**目标**: 在标注数据集上评估所有模型的表现

```bash
cd server
python scripts/embedding_comparison/02_compare_embedding_models.py
```

**评估指标**:
- **Precision**: 标记为相似的对中真正相似的比例
- **Recall**: 真正相似的对中被标记出来的比例
- **F1 Score**: 综合指标 (Precision 和 Recall 的调和平均数)
- **AUC**: ROC 曲线下面积
- **Suspicious Pairs**: 误判数量 (高相似度但实际不相关的对)
- **相似度分离度**: 相似对与不相似对的平均相似度差距

**输出**:
- `scripts/embedding_comparison/data/model_comparison_results.json` (原始结果)
- `scripts/embedding_comparison/data/comparison_report.md` (对比报告)

**预期耗时**: 10-20 分钟

---

### 3. 真实聚类质量测试 (可选)

**目标**: 在真实反馈数据上测试聚类效果

```bash
cd server
python scripts/embedding_comparison/03_test_clustering_quality.py
```

**评估指标**:
- **聚类数量**: 自动生成的聚类簇数量
- **噪声率**: 未被聚类的反馈比例
- **Silhouette Score**: 聚类质量评分 (越高越好)
- **Suspicious Pairs**: 可疑高相似度对数量

**输出**:
- `scripts/embedding_comparison/data/clustering_quality_results.json`
- `scripts/embedding_comparison/data/clustering_quality_report.md`

**预期耗时**: 5-10 分钟

---

## 决策标准

**根据实验结果选择最优模型**:

| 决策因素 | 权重 | 说明 |
|---------|------|------|
| **F1 Score** | 40% | 综合考虑精准度和召回率 |
| **Suspicious Pairs 数量** | 30% | 误判越少越好 |
| **成本** | 15% | API 调用费用 |
| **延迟** | 10% | 响应速度 |
| **稳定性/合规** | 5% | 是否需要翻墙、数据合规 |

**推荐决策规则**:
- ✅ 如果 F1 Score 提升 > 20% 且成本可接受 → **立即切换**
- ✅ 如果 Suspicious Pairs 减少 > 50% → **优先考虑**
- ⚠️ 如果延迟 > 100ms → 需评估用户体验影响
- ❌ 如果 F1 Score 提升 < 10% 且成本翻倍 → **不建议切换**

---

## 切换模型

如果实验结果显示某个模型明显优于 Volcengine,更新配置:

```bash
# server/backend/.env

# 方案 1: 切换到 OpenAI
AI_DEFAULT_PROVIDER=openai

# 方案 2: 切换到 GLM
AI_DEFAULT_PROVIDER=glm
```

**注意**: 切换模型后,需要重新生成所有反馈的 embedding。可以通过以下方式实现:
1. 强制重新聚类: `force_recluster=true`
2. 清空 embedding 缓存: `UPDATE feedbacks SET embedding = NULL`

---

## 成本对比

| 模型 | 单次调用成本 | 1000条反馈/月 | 备注 |
|------|-------------|---------------|------|
| **Volcengine** | ¥0.001/次 | ¥1 | 当前使用 |
| **OpenAI small** | ¥0.002/次 | ¥2 | 推荐替代 |
| **GLM Embedding-3** | ¥0.005/次 | ¥5 | 中文优化 |
| **Qwen text-embedding-v3** | ¥0.0007/千Token | ~¥0.7 | 阿里云,性价比高 |

---

## 常见问题

### Q1: 为什么不直接用最先进的模型?

**A**: "不要相信任何宣传材料,用你自己的数据验证。" - Linus

不同场景对 Embedding 的要求不同。我们的场景是:
- **中文短文本** (20-50字)
- **产品反馈领域**
- **句式结构相似但语义不同**

这些特点导致通用的多语言模型不一定表现最好。

### Q2: 100 对标注数据够吗?

**A**: 够了。

100 对标注数据足够判断模型是否在我们的场景下有明显差异。如果需要更精确的评估,可以增加到 200-300 对。

### Q3: 如果所有模型都不理想怎么办?

**A**: 回到数据结构。

如果实验证明 Embedding 模型切换无法解决问题,说明问题不在模型,而在:
- **数据质量**: 反馈文本是否过于简短/模糊
- **阈值设置**: 相似度阈值是否合理
- **聚类算法**: DBSCAN 参数是否需要调整

---

## 更新日志

- **2026-01-31**: 初始版本,创建实验脚本
- **2026-01-31**: 添加 GLM API 支持

---

## Linus 的评价

> "这才是正确的方法。不要相信任何宣传材料,用你自己的数据验证。
> 
> 100 对标注数据听起来少,但已经足够判断模型是不是垃圾了。
> 
> 先用最简单的方式验证,别一上来就写加权算法和预处理补丁。"
