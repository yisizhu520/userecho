# 快速开始: Embedding 模型对比实验

> "Talk is cheap. Show me the data." - Linus Torvalds

## 1. 背景

当前聚类使用 Volcengine Embedding，存在误判问题（相似度 0.87 但语义不相关）。

本实验对比 **Volcengine、OpenAI、GLM** 三个模型，选出最优。

## 2. 准备工作（5分钟）

### 2.1 配置 API Keys

编辑 `server/backend/.env`：

```bash
# Volcengine（已有）
VOLCENGINE_API_KEY=your-key
VOLCENGINE_EMBEDDING_ENDPOINT=ep-xxx

# OpenAI（需要配置）
OPENAI_API_KEY=sk-xxx...  # https://platform.openai.com/api-keys

# GLM（需要配置）
GLM_API_KEY=your-glm-key  # https://bigmodel.cn/
```

### 2.2 验证配置

```bash
cd server
python scripts/embedding_comparison/00_verify_config.py
```

**预期输出**：
```
✅ VOLCENGINE_API_KEY: 已配置
✅ OPENAI_API_KEY: 已配置
✅ GLM_API_KEY: 已配置
✅ DASHSCOPE_API_KEY: 已配置

🔍 测试 API 连通性:
  ✅ VOLCENGINE: ✅ volcengine API working
     - Embedding 维度: 1024
  ✅ OPENAI: ✅ openai API working
     - Embedding 维度: 1536
  ✅ GLM: ✅ glm API working
     - Embedding 维度: 1024
  ✅ QWEN: ✅ qwen API working
     - Embedding 维度: 1024
```

## 3. 实验步骤

### 步骤 1: 准备标注数据（30-60分钟）

```bash
cd server
python scripts/embedding_comparison/01_prepare_annotation_dataset.py
```

**流程**：
1. 自动导出可疑高相似度对
2. 人工标注每对是否真正相似（y/n）
3. 保存 100 对标注数据

**标注示例**：
```
反馈1: "希望能有公开路线图功能..."
反馈2: "希望能看到反馈趋势图..."
相似度: 0.8787

是否相似?(y/n/s/q): n  ← 输入 n（不相似）
```

**输出**：`scripts/embedding_comparison/data/annotation_dataset.json`

---

### 步骤 2: 对比模型（10-20分钟）

```bash
cd server
python scripts/embedding_comparison/02_compare_embedding_models.py
```

**自动评估**：
- Precision、Recall、F1 Score、AUC
- 可疑对数量（误判数）
- 相似度分布

**输出**：
- `data/model_comparison_results.json`
- `data/comparison_report.md` ← **重点查看**

---

### 步骤 3: 真实聚类测试（可选，5-10分钟）

```bash
cd server
python scripts/embedding_comparison/03_test_clustering_quality.py
```

**验证**：在真实反馈数据上测试聚类质量

**输出**：`data/clustering_quality_report.md`

---

## 4. 查看结果

```bash
# 查看对比报告
cat server/scripts/embedding_comparison/data/comparison_report.md
```

**示例报告**：
```
| 模型         | Precision | Recall | F1 Score | AUC   | 可疑对数量 |
|-------------|-----------|--------|----------|-------|-----------|
| volcengine  | 0.720     | 0.850  | 0.780    | 0.820 | 24        |
| openai      | 0.880     | 0.920  | 0.900    | 0.910 | 8         |
| glm         | 0.850     | 0.900  | 0.875    | 0.895 | 12        |
| qwen        | 0.890     | 0.910  | 0.900    | 0.915 | 7         |

🏆 最佳模型: openai
   - F1 Score: 0.900
   - 可疑对数量: 8
   - 相比 Volcengine 基线:
     * F1 Score 提升: +15.4%
     * 可疑对减少: -66.7%
```

---

## 5. 切换模型

如果实验证明 OpenAI 或 GLM 明显更好，更新配置：

```bash
# server/backend/.env

# 切换到 OpenAI
AI_DEFAULT_PROVIDER=openai

# 或切换到 GLM
AI_DEFAULT_PROVIDER=glm

# 或切换到 Qwen
AI_DEFAULT_PROVIDER=qwen
```

重启服务后生效。

---

## 6. 常见问题

**Q: 需要标注多少数据？**  
A: 100 对（50 相似 + 50 不相似）足够判断模型差异。

**Q: 如果所有模型都不理想？**  
A: 说明问题不在模型，而在数据质量或阈值设置。

**Q: 切换模型后如何重新聚类？**  
A: 调用聚类 API 时设置 `force_recluster=true`。

---

## 7. 联系人

有问题联系项目负责人或查看详细文档：
- `server/scripts/embedding_comparison/README.md`
- `docs/features/clustering/clustering-quality-analysis.md`
