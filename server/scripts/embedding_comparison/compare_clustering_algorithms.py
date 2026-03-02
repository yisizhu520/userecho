"""聚类算法对比实验

对比不同聚类算法的效果：
1. 旧方案：DBSCAN（固定阈值）
2. 方案1：HDBSCAN（自适应阈值）
3. 方案2：HDBSCAN + LLM 校验

运行方式:
    cd server
    python scripts/embedding_comparison/compare_clustering_algorithms.py
"""

import asyncio
import json
from pathlib import Path
from typing import Any

import numpy as np
from sqlalchemy import select

from backend.app.userecho.model.feedback import Feedback
from backend.app.userecho.service.clustering_validator import ClusteringValidator
from backend.common.log import log
from backend.core.conf import settings
from backend.database.db import async_db_session
from backend.utils.ai_client import AIClient
from backend.utils.clustering import FeedbackClustering


async def cluster_with_dbscan(feedbacks_data: list[dict], embeddings: list[list[float]]) -> dict:
    """
    使用旧方案 DBSCAN 进行聚类

    Args:
        feedbacks_data: 反馈数据列表
        embeddings: embedding 向量列表

    Returns:
        聚类结果
    """
    print(f"\n{'=' * 80}")
    print("方案0：DBSCAN（旧方案，固定阈值）".center(80))
    print(f"{'=' * 80}\n")

    threshold = float(getattr(settings, "CLUSTERING_SIMILARITY_THRESHOLD", 0.90))
    min_samples = int(getattr(settings, "CLUSTERING_MIN_SAMPLES", 3))

    print("📊 配置参数:")
    print(f"   - 相似度阈值: {threshold}")
    print(f"   - 最小样本数: {min_samples}")

    # 使用 DBSCAN 聚类
    clustering = FeedbackClustering(similarity_threshold=threshold, min_samples=min_samples)
    embeddings_array = np.array(embeddings)
    cluster_labels = clustering.cluster(embeddings_array)

    # 统计聚类结果
    clusters_dict: dict[int, list[int]] = {}
    noise_indices = []

    for idx, label in enumerate(cluster_labels):
        if label == -1:
            noise_indices.append(idx)
        else:
            if label not in clusters_dict:
                clusters_dict[label] = []
            clusters_dict[label].append(idx)

    clusters = list(clusters_dict.values())

    print("\n✅ 聚类完成:")
    print(f"   - 聚类数: {len(clusters)}")
    print(f"   - 已聚类反馈: {sum(len(c) for c in clusters)}")
    print(f"   - 噪声点: {len(noise_indices)}")

    return _build_result(
        "DBSCAN",
        feedbacks_data,
        embeddings,
        clusters,
        {
            "algorithm": "dbscan",
            "threshold": threshold,
            "min_samples": min_samples,
        },
    )


async def cluster_with_hdbscan(feedbacks_data: list[dict], embeddings: list[list[float]]) -> dict:
    """
    使用方案1 HDBSCAN 进行聚类

    Args:
        feedbacks_data: 反馈数据列表
        embeddings: embedding 向量列表

    Returns:
        聚类结果
    """
    print(f"\n{'=' * 80}")
    print("方案1：HDBSCAN（自适应阈值）".center(80))
    print(f"{'=' * 80}\n")

    min_cluster_size = int(getattr(settings, "CLUSTERING_HDBSCAN_MIN_CLUSTER_SIZE", 3))
    min_samples = int(getattr(settings, "CLUSTERING_HDBSCAN_MIN_SAMPLES", 2))

    print("📊 配置参数:")
    print(f"   - 最小聚类大小: {min_cluster_size}")
    print(f"   - 最小样本数: {min_samples}")

    # 使用 HDBSCAN 聚类
    clustering = FeedbackClustering()
    embeddings_array = np.array(embeddings)
    cluster_labels = clustering.cluster_hdbscan(
        embeddings_array, min_cluster_size=min_cluster_size, min_samples=min_samples
    )

    # 统计聚类结果
    clusters_dict: dict[int, list[int]] = {}
    noise_indices = []

    for idx, label in enumerate(cluster_labels):
        if label == -1:
            noise_indices.append(idx)
        else:
            if label not in clusters_dict:
                clusters_dict[label] = []
            clusters_dict[label].append(idx)

    clusters = list(clusters_dict.values())

    print("\n✅ 聚类完成:")
    print(f"   - 聚类数: {len(clusters)}")
    print(f"   - 已聚类反馈: {sum(len(c) for c in clusters)}")
    print(f"   - 噪声点: {len(noise_indices)}")

    return _build_result(
        "HDBSCAN",
        feedbacks_data,
        embeddings,
        clusters,
        {
            "algorithm": "hdbscan",
            "min_cluster_size": min_cluster_size,
            "min_samples": min_samples,
        },
    )


async def cluster_with_hdbscan_llm(feedbacks_data: list[dict], embeddings: list[list[float]]) -> dict:
    """
    使用方案2 HDBSCAN + LLM 校验进行聚类

    Args:
        feedbacks_data: 反馈数据列表
        embeddings: embedding 向量列表

    Returns:
        聚类结果
    """
    print(f"\n{'=' * 80}")
    print("方案2：HDBSCAN + LLM 语义校验".center(80))
    print(f"{'=' * 80}\n")

    min_cluster_size = int(getattr(settings, "CLUSTERING_HDBSCAN_MIN_CLUSTER_SIZE", 3))
    min_samples = int(getattr(settings, "CLUSTERING_HDBSCAN_MIN_SAMPLES", 2))
    llm_min_size = int(getattr(settings, "CLUSTERING_LLM_VALIDATION_MIN_SIZE", 5))

    print("📊 配置参数:")
    print(f"   - 最小聚类大小: {min_cluster_size}")
    print(f"   - 最小样本数: {min_samples}")
    print(f"   - LLM 校验阈值: {llm_min_size}")

    # 使用 HDBSCAN 聚类
    clustering = FeedbackClustering()
    embeddings_array = np.array(embeddings)
    cluster_labels = clustering.cluster_hdbscan(
        embeddings_array, min_cluster_size=min_cluster_size, min_samples=min_samples
    )

    # 统计初始聚类结果
    clusters_dict: dict[int, list[int]] = {}
    noise_indices = []

    for idx, label in enumerate(cluster_labels):
        if label == -1:
            noise_indices.append(idx)
        else:
            if label not in clusters_dict:
                clusters_dict[label] = []
            clusters_dict[label].append(idx)

    initial_clusters = list(clusters_dict.values())

    print("\n✅ HDBSCAN 聚类完成:")
    print(f"   - 聚类数: {len(initial_clusters)}")
    print(f"   - 已聚类反馈: {sum(len(c) for c in initial_clusters)}")
    print(f"   - 噪声点: {len(noise_indices)}")

    # LLM 校验
    print(f"\n🤖 LLM 语义校验（聚类大小 >= {llm_min_size}）...")
    validator = ClusteringValidator()
    refined_clusters = []
    validation_count = 0
    split_count = 0
    sub_cluster_count = 0

    for cluster_indices in initial_clusters:
        if len(cluster_indices) >= llm_min_size:
            # 需要 LLM 校验
            validation_count += 1
            cluster_feedbacks = [feedbacks_data[i] for i in cluster_indices]

            try:
                # 转换为 Feedback 对象（LLM validator 需要）
                from backend.app.userecho.model.feedback import Feedback as FeedbackModel

                feedback_objs = []
                for f_data in cluster_feedbacks:
                    feedback_obj = FeedbackModel()
                    feedback_obj.id = f_data["id"]
                    feedback_obj.content = f_data["content"]
                    # created_time 是只读属性，不需要设置
                    feedback_objs.append(feedback_obj)

                result = await validator.validate_cluster_with_llm(feedback_objs)
            except Exception as e:
                log.error(f"LLM 校验失败: {e}")
                print(f"   ⚠️  聚类 {validation_count}: {len(cluster_indices)} 条反馈 - LLM 校验失败，保留原聚类")
                refined_clusters.append(cluster_indices)
                continue

            if result.is_valid:
                # 保持原聚类
                refined_clusters.append(cluster_indices)
                print(f"   ✓ 聚类 {validation_count}: {len(cluster_indices)} 条反馈 - 语义一致")
                print(f"      主题: {result.common_theme}")
            elif result.sub_clusters and len(result.sub_clusters) > 0:
                # LLM 建议拆分为子聚类
                split_count += 1
                print(
                    f"   🔄 聚类 {validation_count}: {len(cluster_indices)} 条反馈 - 拆分为 {len(result.sub_clusters)} 个子聚类"
                )
                print(f"      原因: {result.reason}")

                # 根据 LLM 建议创建子聚类
                for sub_cluster in result.sub_clusters:
                    # feedback_indices 是从 1 开始的，需要转换为实际索引
                    sub_indices = [
                        cluster_indices[i - 1] for i in sub_cluster.feedback_indices if 0 < i <= len(cluster_indices)
                    ]

                    # 只保留至少 2 条反馈的子聚类
                    if len(sub_indices) >= 2:
                        refined_clusters.append(sub_indices)
                        sub_cluster_count += 1
                        print(f"         → {sub_cluster.theme}: {len(sub_indices)} 条反馈")
                    else:
                        # 单条反馈标记为噪声
                        noise_indices.extend(sub_indices)
            else:
                # 无法拆分，标记为噪声
                split_count += 1
                for idx in cluster_indices:
                    noise_indices.append(idx)
                print(f"   ✗ 聚类 {validation_count}: {len(cluster_indices)} 条反馈 - 语义不一致，无法拆分，标记为噪声")
                print(f"      原因: {result.reason}")
        else:
            # 小聚类直接保留
            refined_clusters.append(cluster_indices)
            refined_clusters.append(cluster_indices)

    print("\n✅ LLM 校验完成:")
    print(f"   - 校验聚类数: {validation_count}")
    print(f"   - 拆分聚类数: {split_count}")
    print(f"   - 生成子聚类数: {sub_cluster_count}")
    print(f"   - 最终聚类数: {len(refined_clusters)}")
    print(f"   - 已聚类反馈: {sum(len(c) for c in refined_clusters)}")
    print(f"   - 噪声点: {len(noise_indices)}")

    return _build_result(
        "HDBSCAN+LLM",
        feedbacks_data,
        embeddings,
        refined_clusters,
        {
            "algorithm": "hdbscan+llm",
            "min_cluster_size": min_cluster_size,
            "min_samples": min_samples,
            "llm_min_size": llm_min_size,
            "validation_count": validation_count,
            "split_count": split_count,
            "sub_cluster_count": sub_cluster_count,
        },
    )


def _build_result(
    method: str,
    feedbacks_data: list[dict],
    embeddings: list[list[float]],
    clusters: list[list[int]],
    params: dict[str, Any],
) -> dict:
    """
    构建聚类结果

    Args:
        method: 方法名称
        feedbacks_data: 反馈数据
        embeddings: embedding 向量
        clusters: 聚类索引列表
        params: 参数信息

    Returns:
        结果字典
    """
    # 计算相似度矩阵
    embeddings_array = np.array(embeddings)
    norms = np.linalg.norm(embeddings_array, axis=1, keepdims=True)
    normalized = embeddings_array / norms
    similarity_matrix = normalized @ normalized.T

    clustered_count = sum(len(c) for c in clusters)
    noise_count = len(feedbacks_data) - clustered_count

    result = {
        "method": method,
        "params": params,
        "total_feedbacks": len(feedbacks_data),
        "cluster_count": len(clusters),
        "clustered_count": clustered_count,
        "noise_count": noise_count,
        "clustering_rate": clustered_count / len(feedbacks_data) * 100,
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
    print("聚类算法对比实验".center(80))
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

    # 2. 获取 embeddings（使用默认 provider）
    default_provider = getattr(settings, "AI_DEFAULT_PROVIDER", "volcengine")
    print(f"📊 使用 {default_provider.upper()} 获取 embeddings...")

    client = AIClient()
    texts = [f["content"] for f in feedbacks_data]
    embeddings = await client.get_embeddings_batch(texts, provider=default_provider)

    if not embeddings or len(embeddings) != len(feedbacks_data):
        print("❌ 获取 embeddings 失败")
        return

    print(f"✅ 获取了 {len(embeddings)} 个 embeddings\n")

    # 过滤掉 None 值（如果有的话）
    valid_embeddings: list[list[float]] = [e for e in embeddings if e is not None]
    if len(valid_embeddings) != len(feedbacks_data):
        print(f"⚠️  警告：有 {len(feedbacks_data) - len(valid_embeddings)} 个无效 embeddings")
        # 同步过滤 feedbacks_data
        valid_feedbacks = []
        filtered_embeddings: list[list[float]] = []
        for i, emb in enumerate(embeddings):
            if emb is not None:
                valid_feedbacks.append(feedbacks_data[i])
                filtered_embeddings.append(emb)
        feedbacks_data = valid_feedbacks
        valid_embeddings = filtered_embeddings

    # 3. 运行三种聚类方法
    results = {}

    # 方案0: DBSCAN（旧方案）
    try:
        results["dbscan"] = await cluster_with_dbscan(feedbacks_data, valid_embeddings)
    except Exception as e:
        log.error(f"DBSCAN 聚类失败: {e}")
        print(f"❌ DBSCAN 聚类失败: {e}\n")

    # 方案1: HDBSCAN
    try:
        results["hdbscan"] = await cluster_with_hdbscan(feedbacks_data, valid_embeddings)
    except Exception as e:
        log.error(f"HDBSCAN 聚类失败: {e}")
        print(f"❌ HDBSCAN 聚类失败: {e}\n")

    # 方案2: HDBSCAN + LLM
    try:
        results["hdbscan_llm"] = await cluster_with_hdbscan_llm(feedbacks_data, valid_embeddings)
    except Exception as e:
        log.error(f"HDBSCAN+LLM 聚类失败: {e}")
        print(f"❌ HDBSCAN+LLM 聚类失败: {e}\n")

    if not results:
        print("❌ 所有方法都失败了")
        return

    # 4. 保存详细结果
    detailed_file = output_dir / "algorithm_comparison_detailed.json"
    with open(detailed_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n💾 详细结果已保存: {detailed_file}")

    # 5. 生成对比报告
    report_file = output_dir / "algorithm_comparison_report.md"
    with open(report_file, "w", encoding="utf-8") as f:
        f.write("# 聚类算法对比报告\n\n")
        f.write(f"**数据集**: {len(feedbacks_data)} 条反馈\n")
        f.write(f"**Embedding Provider**: {default_provider.upper()}\n\n")
        f.write("---\n\n")

        # 5.1 总体对比
        f.write("## 📊 总体对比\n\n")
        f.write("| 方案 | 聚类数 | 已聚类 | 噪声点 | 聚类率 | 说明 |\n")
        f.write("|------|--------|--------|--------|--------|------|\n")

        for key, result in results.items():
            method = result["method"]
            cluster_count = result["cluster_count"]
            clustered = result["clustered_count"]
            noise = result["noise_count"]
            rate = result["clustering_rate"]

            desc = ""
            if key == "dbscan":
                desc = "旧方案，固定阈值"
            elif key == "hdbscan":
                desc = "方案1，自适应阈值"
            elif key == "hdbscan_llm":
                desc = "方案2，语义校验"

            f.write(f"| **{method}** | {cluster_count} | {clustered} | {noise} | {rate:.1f}% | {desc} |\n")

        f.write("\n**指标说明**:\n")
        f.write("- **聚类数**: 形成的聚类数量，越少说明归纳能力越强\n")
        f.write("- **已聚类**: 成功聚类的反馈数量\n")
        f.write("- **噪声点**: 无法归类的反馈（孤立点）\n")
        f.write("- **聚类率**: 已聚类反馈占总数的百分比\n\n")

        # 5.2 参数对比
        f.write("## ⚙️ 参数配置\n\n")
        for key, result in results.items():
            f.write(f"### {result['method']}\n\n")
            f.write("```python\n")
            for param_key, param_value in result["params"].items():
                f.write(f"{param_key} = {param_value}\n")
            f.write("```\n\n")

        # 5.3 聚类详情对比
        f.write("## 🔍 聚类详情对比\n\n")

        for key, result in results.items():
            f.write(f"### {result['method']}\n\n")

            if not result["clusters"]:
                f.write("（未形成任何聚类）\n\n")
                continue

            # 展示前 5 个最大的聚类
            top_clusters = result["clusters"][:5]

            for cluster in top_clusters:
                f.write(
                    f"#### 聚类 #{cluster['cluster_id']} ({cluster['size']} 条, 相似度: {cluster['avg_similarity']:.3f})\n\n"
                )

                # 展示聚类中的所有反馈（不省略）
                for feedback in cluster["feedbacks"]:
                    content = feedback["content"]
                    if len(content) > 100:
                        content = content[:100] + "..."
                    f.write(f"- {content}\n")

                f.write("\n")

            if len(result["clusters"]) > 5:
                f.write(f"（还有 {len(result['clusters']) - 5} 个聚类...）\n\n")

        # 5.4 结论与建议
        f.write("\n---\n\n## 🎯 结论与建议\n\n")

        f.write("### 质量分析\n\n")
        f.write("请人工检查以下方面：\n\n")
        f.write("1. **聚类准确性**: 查看各方案的聚类详情，检查是否有不相关的反馈被错误聚在一起\n")
        f.write("2. **聚类完整性**: 检查是否有明显相似的反馈没有被聚在一起\n")
        f.write("3. **噪声合理性**: 检查噪声点是否确实难以归类\n")
        f.write("4. **聚类粒度**: 聚类是否太细（过拟合）或太粗（欠拟合）\n\n")

        f.write("### 方案对比\n\n")

        # 比较聚类数
        dbscan_count = results.get("dbscan", {}).get("cluster_count", 0)
        hdbscan_count = results.get("hdbscan", {}).get("cluster_count", 0)
        hdbscan_llm_count = results.get("hdbscan_llm", {}).get("cluster_count", 0)

        f.write("- **DBSCAN vs HDBSCAN**: ")
        if hdbscan_count > 0:
            diff = ((hdbscan_count - dbscan_count) / dbscan_count * 100) if dbscan_count > 0 else 0
            f.write(f"聚类数变化 {diff:+.1f}%\n")
        else:
            f.write("HDBSCAN 未执行\n")

        f.write("- **HDBSCAN vs HDBSCAN+LLM**: ")
        if hdbscan_llm_count > 0 and hdbscan_count > 0:
            diff = (hdbscan_llm_count - hdbscan_count) / hdbscan_count * 100
            f.write(f"聚类数变化 {diff:+.1f}%")
            if "hdbscan_llm" in results:
                llm_params = results["hdbscan_llm"]["params"]
                if "split_count" in llm_params:
                    f.write(f"（LLM 拆分了 {llm_params['split_count']} 个聚类）")
            f.write("\n")
        else:
            f.write("HDBSCAN+LLM 未执行\n")

        f.write("\n### 配置建议\n\n")
        f.write("根据对比结果，建议调整配置：\n\n")
        f.write("```bash\n")
        f.write("# server/backend/.env\n\n")
        f.write("# 选择聚类算法（true=HDBSCAN, false=DBSCAN）\n")
        f.write("CLUSTERING_USE_HDBSCAN=true\n\n")
        f.write("# HDBSCAN 参数\n")
        f.write("CLUSTERING_HDBSCAN_MIN_CLUSTER_SIZE=3  # 最小聚类大小\n")
        f.write("CLUSTERING_HDBSCAN_MIN_SAMPLES=2        # 最小样本数\n\n")
        f.write("# LLM 校验（可选，会增加成本）\n")
        f.write("CLUSTERING_LLM_VALIDATION_ENABLED=false  # 是否启用\n")
        f.write("CLUSTERING_LLM_VALIDATION_MIN_SIZE=5     # 多大的聚类需要校验\n")
        f.write("```\n")

    print(f"📄 对比报告已生成: {report_file}\n")

    # 6. 打印摘要
    print("\n" + "=" * 80)
    print("对比摘要".center(80))
    print("=" * 80 + "\n")

    print(f"{'方案':<20} | {'聚类数':>6} | {'聚类率':>8} | {'噪声':>6}")
    print("-" * 60)

    for key, result in results.items():
        method = result["method"]
        cluster_count = result["cluster_count"]
        rate = result["clustering_rate"]
        noise = result["noise_count"]
        print(f"{method:<20} | {cluster_count:>6} | {rate:>7.1f}% | {noise:>6}")

    print("\n✅ 对比完成！请查看报告文件进行人工评估。")
    print(f"\n📄 报告位置: {report_file}")
    print(f"📊 详细数据: {detailed_file}")


if __name__ == "__main__":
    asyncio.run(main())
