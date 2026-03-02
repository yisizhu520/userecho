"""Embedding Provider 聚类对比

直接对比不同 provider 的聚类效果，无需人工标注

运行方式:
    cd server
    python scripts/embedding_comparison/compare_clustering_providers.py
"""

import asyncio
import json
from pathlib import Path

import numpy as np
from sqlalchemy import select

from backend.app.userecho.model.feedback import Feedback
from backend.common.log import log
from backend.core.conf import settings
from backend.database.db import async_db_session
from backend.utils.ai_client import AIClient


async def cluster_feedbacks(feedbacks_data: list[dict], provider: str) -> dict:
    """
    使用指定 provider 进行聚类

    Args:
        feedbacks_data: 反馈数据列表（字典格式）
        provider: embedding provider

    Returns:
        聚类结果
    """
    print(f"\n{'=' * 80}")
    print(f"使用 {provider.upper()} 进行聚类".center(80))
    print(f"{'=' * 80}\n")

    # 1. 获取 embeddings
    print(f"📊 获取 {len(feedbacks_data)} 条反馈的 embeddings...")
    client = AIClient()
    texts = [f["content"] for f in feedbacks_data]
    embeddings = await client.get_embeddings_batch(texts, provider=provider)

    if not embeddings or len(embeddings) != len(feedbacks_data):
        raise ValueError(f"Failed to get embeddings from {provider}")

    log.info(f"Got {len(embeddings)} embeddings from {provider}")

    # 2. 计算相似度矩阵
    print("🔍 计算相似度矩阵...")
    embeddings_array = np.array(embeddings)
    norms = np.linalg.norm(embeddings_array, axis=1, keepdims=True)
    normalized = embeddings_array / norms
    similarity_matrix = normalized @ normalized.T

    # 统计相似度分布（排除对角线）
    upper_triangle_indices = np.triu_indices_from(similarity_matrix, k=1)
    upper_triangle = similarity_matrix[upper_triangle_indices]
    print("📈 相似度分布:")
    print(
        f"   min={upper_triangle.min():.3f}, max={upper_triangle.max():.3f}, "
        f"mean={upper_triangle.mean():.3f}, median={np.median(upper_triangle):.3f}"
    )
    print(
        f"   > 0.90: {(upper_triangle > 0.90).sum()}/{len(upper_triangle)} "
        f"({100 * (upper_triangle > 0.90).sum() / len(upper_triangle):.1f}%)"
    )
    print(
        f"   > 0.80: {(upper_triangle > 0.80).sum()}/{len(upper_triangle)} "
        f"({100 * (upper_triangle > 0.80).sum() / len(upper_triangle):.1f}%)"
    )
    print(
        f"   > 0.70: {(upper_triangle > 0.70).sum()}/{len(upper_triangle)} "
        f"({100 * (upper_triangle > 0.70).sum() / len(upper_triangle):.1f}%)"
    )

    # 3. 简单聚类：相似度 >= threshold 的归为一组
    threshold = float(getattr(settings, "CLUSTERING_SIMILARITY_THRESHOLD", 0.90))
    print(f"🎯 聚类阈值: {threshold}")

    clusters = []
    clustered = set()

    for i in range(len(feedbacks_data)):
        if i in clustered:
            continue

        # 找出与 i 相似的所有反馈
        cluster = [i]
        for j in range(i + 1, len(feedbacks_data)):
            if j not in clustered and similarity_matrix[i][j] >= threshold:
                cluster.append(j)
                clustered.add(j)

        if len(cluster) >= int(getattr(settings, "CLUSTERING_MIN_SAMPLES", 3)):
            clusters.append(cluster)
            clustered.add(i)

    # 4. 统计结果
    clustered_count = sum(len(c) for c in clusters)
    noise_count = len(feedbacks_data) - clustered_count

    print("\n✅ 聚类完成:")
    print(f"  - 聚类数: {len(clusters)}")
    print(f"  - 已聚类反馈: {clustered_count}")
    print(f"  - 噪声点: {noise_count}")

    # 5. 构建结果
    result = {
        "provider": provider,
        "threshold": threshold,
        "total_feedbacks": len(feedbacks_data),
        "cluster_count": len(clusters),
        "clustered_count": clustered_count,
        "noise_count": noise_count,
        "clusters": [],
    }

    # 添加每个聚类的详细信息
    for cluster_idx, cluster_indices in enumerate(clusters, 1):
        cluster_data = {"cluster_id": cluster_idx, "size": len(cluster_indices), "feedbacks": []}

        for idx in cluster_indices:
            feedback = feedbacks_data[idx]
            cluster_data["feedbacks"].append(
                {
                    "id": feedback["id"],
                    "content": feedback["content"],
                    "created_time": feedback["created_time"].isoformat() if feedback.get("created_time") else None,
                }
            )

        # 计算聚类内平均相似度
        if len(cluster_indices) > 1:
            sims = []
            for i, idx1 in enumerate(cluster_indices):
                for idx2 in cluster_indices[i + 1 :]:
                    sims.append(similarity_matrix[idx1][idx2])
            cluster_data["avg_similarity"] = float(np.mean(sims))
        else:
            cluster_data["avg_similarity"] = 1.0

        result["clusters"].append(cluster_data)

    # 按聚类大小排序
    result["clusters"].sort(key=lambda x: x["size"], reverse=True)

    return result


async def main():
    """主流程"""
    # 配置
    TENANT_ID = "default-tenant"
    LIMIT = 200  # 使用所有反馈

    # 输出目录
    output_dir = Path(__file__).parent / "data"
    output_dir.mkdir(parents=True, exist_ok=True)

    print("\n" + "=" * 80)
    print("Embedding Provider 聚类对比实验".center(80))
    print("=" * 80 + "\n")

    # 1. 加载反馈数据
    print("📥 加载反馈数据...")
    feedbacks_data = []
    async with async_db_session.begin() as db:
        query = select(Feedback).where(Feedback.tenant_id == TENANT_ID, Feedback.deleted_at.is_(None)).limit(LIMIT)
        result = await db.execute(query)
        feedbacks = list(result.scalars().all())

        # 提取数据，避免 Session detached 问题
        for f in feedbacks:
            feedbacks_data.append(
                {
                    "id": f.id,
                    "content": f.content,
                    "created_time": f.created_time,
                }
            )

    if not feedbacks_data:
        print("❌ 没有找到反馈数据")
        return

    print(f"✅ 加载了 {len(feedbacks_data)} 条反馈\n")

    # 2. 检查可用的 providers
    available_providers = []

    if getattr(settings, "VOLCENGINE_API_KEY", None):
        available_providers.append("volcengine")
    if getattr(settings, "OPENAI_API_KEY", None):
        available_providers.append("openai")
    if getattr(settings, "GLM_API_KEY", None):
        available_providers.append("glm")
    if getattr(settings, "DASHSCOPE_API_KEY", None):
        available_providers.append("qwen")

    if len(available_providers) < 2:
        print("❌ 至少需要配置 2 个 provider 才能对比")
        print(f"当前可用: {available_providers}")
        return

    print(f"🎯 将对比以下 providers: {', '.join(available_providers)}\n")

    # 3. 对每个 provider 进行聚类
    results = {}
    for provider in available_providers:
        try:
            result = await cluster_feedbacks(feedbacks_data, provider)
            results[provider] = result
        except Exception as e:
            log.error(f"Failed to cluster with {provider}: {e}")
            print(f"❌ {provider} 聚类失败: {e}\n")

    if not results:
        print("❌ 所有 provider 都失败了")
        return

    # 4. 保存详细结果
    detailed_file = output_dir / "clustering_comparison_detailed.json"
    with open(detailed_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n💾 详细结果已保存: {detailed_file}")

    # 5. 生成对比报告
    report_file = output_dir / "clustering_comparison_report.md"
    with open(report_file, "w", encoding="utf-8") as f:
        f.write("# Embedding Provider 聚类对比报告\n\n")
        f.write(f"**数据集**: {len(feedbacks_data)} 条反馈\n\n")
        f.write("---\n\n")

        # 5.1 总体对比
        f.write("## 📊 总体对比\n\n")
        f.write("| Provider | 聚类数 | 已聚类反馈 | 噪声点 | 聚类率 |\n")
        f.write("|----------|--------|-----------|--------|--------|\n")

        for provider, result in results.items():
            clustering_rate = result["clustered_count"] / result["total_feedbacks"] * 100
            f.write(
                f"| **{provider.upper()}** | {result['cluster_count']} | {result['clustered_count']} | {result['noise_count']} | {clustering_rate:.1f}% |\n"
            )

        f.write("\n**解读**:\n")
        f.write("- **聚类数**: 越少越好（说明归纳能力强）\n")
        f.write("- **聚类率**: 太高可能过度聚类（误判），太低可能欠聚类（漏判）\n")
        f.write("- **噪声点**: 无法归类的反馈，适度噪声是正常的\n\n")

        # 5.2 每个 provider 的详细聚类
        for provider, result in results.items():
            f.write(f"\n---\n\n## 🔍 {provider.upper()} 聚类详情\n\n")

            if not result["clusters"]:
                f.write("（未形成任何聚类）\n\n")
                continue

            # 只展示前 10 个最大的聚类
            top_clusters = result["clusters"][:10]

            for cluster in top_clusters:
                f.write(
                    f"### 聚类 #{cluster['cluster_id']} ({cluster['size']} 条反馈, 平均相似度: {cluster['avg_similarity']:.3f})\n\n"
                )

                # 展示聚类中的反馈
                for feedback in cluster["feedbacks"][:5]:  # 每个聚类最多显示 5 条
                    content = feedback["content"]
                    if len(content) > 100:
                        content = content[:100] + "..."
                    f.write(f"- {content}\n")

                if len(cluster["feedbacks"]) > 5:
                    f.write(f"\n（还有 {len(cluster['feedbacks']) - 5} 条...）\n")

                f.write("\n")

            if len(result["clusters"]) > 10:
                f.write(f"\n（还有 {len(result['clusters']) - 10} 个较小的聚类...）\n\n")

        # 5.3 推荐
        f.write("\n---\n\n## 🎯 推荐\n\n")
        f.write("**人工校验要点**:\n\n")
        f.write("1. 查看各 provider 的聚类详情，看哪个把相似反馈聚得更准\n")
        f.write("2. 检查是否有明显不相似的反馈被错误聚在一起（误判）\n")
        f.write("3. 检查是否有明显相似的反馈没有被聚在一起（漏判）\n")
        f.write("4. 综合考虑聚类数量和质量\n\n")
        f.write("**切换 provider**:\n\n")
        f.write("```bash\n")
        f.write("# 编辑 server/backend/.env\n")
        f.write("AI_DEFAULT_PROVIDER=<provider_name>\n")
        f.write("```\n\n")
        f.write("**可选值**: volcengine | openai | glm | qwen\n")

    print(f"📄 对比报告已生成: {report_file}\n")

    # 6. 打印摘要
    print("\n" + "=" * 80)
    print("对比摘要".center(80))
    print("=" * 80 + "\n")

    for provider, result in results.items():
        clustering_rate = result["clustered_count"] / result["total_feedbacks"] * 100
        print(
            f"{provider.upper():15} | 聚类数: {result['cluster_count']:3} | 聚类率: {clustering_rate:5.1f}% | 噪声: {result['noise_count']:3}"
        )

    print("\n✅ 对比完成！请查看报告文件进行人工校验。")
    print(f"\n📄 报告位置: {report_file}")


if __name__ == "__main__":
    asyncio.run(main())
