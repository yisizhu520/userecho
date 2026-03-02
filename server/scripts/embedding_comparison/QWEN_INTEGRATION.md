# ✅ Qwen Embedding 集成完成

## 更新内容

### 1. 核心代码更新

**`backend/utils/ai_client.py`**
- 添加 Qwen (阿里云 DashScope) 配置
- base_url: `https://dashscope.aliyuncs.com/compatible-mode/v1`
- embedding_model: `text-embedding-v3`
- env_key: `DASHSCOPE_API_KEY`

**`backend/.env`**
- 添加 `DASHSCOPE_API_KEY=` 配置项

---

### 2. 实验脚本更新

已更新以下脚本支持 Qwen:
- ✅ `00_verify_config.py` - 配置验证
- ✅ `02_compare_embedding_models.py` - 模型对比
- ✅ `03_test_clustering_quality.py` - 聚类测试

---

### 3. 文档更新

已更新以下文档:
- ✅ `scripts/embedding_comparison/README.md`
- ✅ `scripts/embedding_comparison/QUICKSTART.md`
- ✅ `docs/features/clustering/clustering-quality-analysis.md`

---

## 技术亮点

### Qwen Embedding 特性

**官方信息**:
- **模型**: text-embedding-v3 (1024维)
- **C-MTEB 排名**: Top 3 (中文场景)
- **价格**: ¥0.0007/千Token (~¥0.7/1000条反馈)
- **上下文**: 50+语言支持

**API 兼容性**:
- ✅ 完全兼容 OpenAI SDK (使用 AsyncOpenAI)
- ✅ 零代码修改,只需配置 base_url
- ✅ 支持批量调用 (提升效率)

---

## 现在支持的模型

| 模型 | 提供商 | 维度 | 成本/1000条 | 特点 |
|------|--------|------|------------|------|
| **Volcengine** | 火山引擎 | 1024 | ¥1 | 基线对照 |
| **OpenAI** | OpenAI | 1536 | ¥2 | 多语言强 |
| **GLM** | 智谱AI | 1024 | ¥5 | 中文优化 |
| **Qwen** | 阿里云 | 1024 | ¥0.7 | 性价比最高 |

---

## 下一步操作

### 1. 获取 API Key

访问: https://dashscope.console.aliyun.com/

1. 注册/登录阿里云账号
2. 开通「百炼」服务
3. 创建 API Key

### 2. 配置环境

编辑 `server/backend/.env`:

```bash
DASHSCOPE_API_KEY=sk-xxx...  # 替换为你的 API Key
```

### 3. 验证配置

```bash
cd server
python scripts/embedding_comparison/00_verify_config.py
```

**预期输出**:
```
✅ QWEN: ✅ qwen API working
   - Embedding 维度: 1024
```

### 4. 运行实验

```bash
# 准备标注数据
python scripts/embedding_comparison/01_prepare_annotation_dataset.py

# 对比所有模型 (包括 Qwen)
python scripts/embedding_comparison/02_compare_embedding_models.py
```

---

## 常见问题

**Q: Qwen 为什么叫 DASHSCOPE_API_KEY?**  
A: 阿里云的 AI 服务平台叫「百炼 (DashScope)」,所有通义千问系列模型都使用这个 API。

**Q: Qwen 和 Qwen3 有什么区别?**  
A: 
- **Qwen3 Embedding**: 开源模型,需要本地部署 (Ollama/HuggingFace)
- **Qwen text-embedding-v3**: 云端 API,即开即用,无需部署

我们使用的是云端 API 版本,方便对比。

**Q: 如果实验证明 Qwen 最好,如何切换?**  
A: 编辑 `.env`,设置 `AI_DEFAULT_PROVIDER=qwen`,重启服务即可。

---

## Linus 的评价

> "兼容 OpenAI SDK 是正确的设计。不要重新发明轮子,站在巨人的肩膀上。
> 
> 现在你有 4 个模型可以对比了。用数据说话,别再猜了。"

---

## 更新日志

- **2026-01-31**: 添加 Qwen (阿里云 DashScope) Embedding 支持
- **2026-01-31**: 更新所有实验脚本和文档
