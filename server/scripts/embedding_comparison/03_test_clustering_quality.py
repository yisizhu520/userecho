"""步骤 3: 真实聚类质量测试

在真实反馈数据上测试不同模型的聚类效果（可选验证步骤）

运行方式：
    cd server
    python scripts/embedding_comparison/03_test_clustering_quality.py
"""

import asyncio
import json
from pathlib import Path

import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.metrics import silhouette_score
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy import select

from backend.app.userecho.model.feedback import Feedback
from backend.common.log import log
from backend.core.conf import settings
from backend.database.db import async_db_session
from backend.utils.ai_client import AIClient


async def test_clustering_with_model(
    model_provider: str,
    tenant_id: str,
    board_id: str | None = None,
    limit: int = 100,
    threshold: float = 0.90,
    min_samples: int = 3,
) -> dict:
    """
    使用指定模型测试聚类效果

    Args:
        model_provider: 模型提供商
        tenant_id: 租户ID
        board_id: 看板ID（可选）
        limit: 最多处理的反馈数量
        threshold: 相似度阈值
        min_samples: 最小聚类大小

    Returns:
        聚类质量指标
    """
    print(f"\n{'=' * 80}")
    print(f"测试模型: {model_provider}".center(80))
    print(f"{'=' * 80}\n")

    # 1. 获取反馈数据
    async with async_db_session.begin() as db:
        query = select(Feedback).where(
            Feedback.tenant_id == tenant_id,
            Feedback.deleted.is_(False),
        )

        if board_id:
            query = query.where(Feedback.board_id == board_id)

        query = query.limit(limit)
        result = await db.execute(query)
        feedbacks = result.scalars().all()

    if len(feedbacks) < min_samples:
        return {
            "model": model_provider,
            "status": "failed",
            "error": f"Not enough feedbacks: {len(feedbacks)} < {min_samples}",
        }

    print(f"Loaded {len(feedbacks)} feedbacks")

    # 2. 获取 embeddings (✅ 使用 provider 参数)
    client = AIClient()

    texts = [f.content for f in feedbacks]
    embeddings_raw = await client.get_embeddings_batch(texts, batch_size=50, provider=model_provider)

    # 过滤失败的
    valid_indices = [i for i, emb in enumerate(embeddings_raw) if emb is not None]
    embeddings = np.array([embeddings_raw[i] for i in valid_indices])

    if len(embeddings) < min_samples:
        return {
            "model": model_provider,
            "status": "failed",
            "error": f"Not enough valid embeddings: {len(embeddings)}",
        }

    print(f"Valid embeddings: {len(embeddings)}/{len(feedbacks)}")

    # 3. 执行 DBSCAN 聚类
    similarity_matrix = cosine_similarity(embeddings)
    distance_matrix = 1 - similarity_matrix

    dbscan = DBSCAN(
        eps=1 - threshold,
        min_samples=min_samples,
        metric="precomputed",
    )
    labels = dbscan.fit_predict(distance_matrix)

    # 4. 统计聚类结果
    unique_labels = set(labels)
    clusters_count = len(unique_labels - {-1})  # 排除噪声点（-1）
    noise_count = list(labels).count(-1)
    noise_ratio = noise_count / len(labels) if len(labels) > 0 else 1.0

    # 5. 计算 Silhouette Score（排除噪声点）
    if clusters_count > 0 and noise_count < len(labels):
        # 只对非噪声点计算
        non_noise_mask = labels != -1
        if sum(non_noise_mask) >= 2 and len(set(labels[non_noise_mask])) > 1:
            silhouette = silhouette_score(
                distance_matrix[non_noise_mask][:, non_noise_mask],
                labels[non_noise_mask],
                metric="precomputed",
            )
        else:
            silhouette = 0.0
    else:
        silhouette = 0.0

    # 6. 计算可疑对（高相似度但语义不相关）
    suspicious_pairs = []
    n = len(embeddings)

    for i in range(n):
        for j in range(i + 1, n):
            sim = similarity_matrix[i][j]

            if sim >= threshold:
                text1 = texts[valid_indices[i]]
                text2 = texts[valid_indices[j]]
                suspicious_pairs.append(
                    {
                        "text1": text1[:50] + "...",
                        "text2": text2[:50] + "...",
                        "similarity": float(sim),
                    }
                )

    result = {
        "model": model_provider,
        "status": "success",
        "parameters": {
            "threshold": threshold,
            "min_samples": min_samples,
            "feedbacks_count": len(feedbacks),
        },
        "clustering_results": {
            "clusters_count": int(clusters_count),
            "noise_count": int(noise_count),
            "noise_ratio": float(noise_ratio),
            "silhouette_score": float(silhouette),
        },
        "quality_indicators": {
            "suspicious_pairs_count": len(suspicious_pairs),
            "suspicious_pairs_sample": suspicious_pairs[:5],
        },
    }

    # 打印结果
    print(f"模型: {model_provider}")
    print(f"聚类数量: {clusters_count}")
    print(f"噪声点: {noise_count} ({noise_ratio:.1%})")
    print(f"Silhouette Score: {silhouette:.3f}")
    print(f"可疑对数量: {len(suspicious_pairs)}")

    return result


async def compare_clustering_quality(
    tenant_id: str,
    board_id: str | None = None,
    limit: int = 100,
) -> list[dict]:
    """
    对比所有模型的聚类质量

    Args:
        tenant_id: 租户ID
        board_id: 看板ID（可选）
        limit: 最多处理的反馈数量

    Returns:
        所有模型的聚类质量指标
    """
    # 检查 API Keys
    models_to_test = []

    if getattr(settings, "VOLCENGINE_API_KEY", None):
        models_to_test.append("volcengine")

    if getattr(settings, "OPENAI_API_KEY", None):
        models_to_test.append("openai")

    if getattr(settings, "GLM_API_KEY", None):
        models_to_test.append("glm")

    if getattr(settings, "DASHSCOPE_API_KEY", None):
        models_to_test.append("qwen")

    if not models_to_test:
        log.error("No API keys configured")
        return []

    print(f"\n将测试以下模型: {', '.join(models_to_test)}\n")

    results = []
    for model in models_to_test:
        try:
            result = await test_clustering_with_model(
                model_provider=model,
                tenant_id=tenant_id,
                board_id=board_id,
                limit=limit,
            )
            results.append(result)
        except Exception as e:
            log.error(f"Failed to test {model}: {e}")
            results.append(
                {
                    "model": model,
                    "status": "failed",
                    "error": str(e),
                }
            )

    return results


def generate_clustering_report(results: list[dict], output_file: Path) -> None:
    """生成聚类质量报告"""
    report_lines = [
        "=" * 100,
        "真实聚类质量测试报告".center(100),
        "=" * 100,
        "",
        "## 1. 聚类效果对比",
        "",
        "| 模型 | 聚类数量 | 噪声点 | 噪声率 | Silhouette | 可疑对 |",
        "|------|---------|-------|--------|------------|--------|",
    ]

    for result in results:
        if result["status"] == "success":
            cr = result["clustering_results"]
            qi = result["quality_indicators"]
            model = result["model"]

            report_lines.append(
                f"| {model:<12} | {cr['clusters_count']:>8} | {cr['noise_count']:>6} | "
                f"{cr['noise_ratio']:.1%} | {cr['silhouette_score']:>10.3f} | {qi['suspicious_pairs_count']:>6} |"
            )
        else:
            report_lines.append(f"| {result['model']:<12} | FAILED | - | - | - | - |")

    report_lines.extend(["", "## 2. 推荐结论", ""])

    successful_results = [r for r in results if r["status"] == "success"]
    if successful_results:
        # 综合评分：Silhouette 高 + 可疑对少 + 噪声率合理
        def score_model(r):
            cr = r["clustering_results"]
            qi = r["quality_indicators"]
            return cr["silhouette_score"] * 0.4 - qi["suspicious_pairs_count"] * 0.3 - cr["noise_ratio"] * 0.3

        best_model = max(successful_results, key=score_model)

        report_lines.append(f"🏆 **最佳模型**: {best_model['model']}")
        report_lines.append(f"   - Silhouette Score: {best_model['clustering_results']['silhouette_score']:.3f}")
        report_lines.append(f"   - 可疑对数量: {best_model['quality_indicators']['suspicious_pairs_count']}")
        report_lines.append(f"   - 噪声率: {best_model['clustering_results']['noise_ratio']:.1%}")
        report_lines.append("")

    # 详细指标
    report_lines.extend(["## 3. 详细分析", ""])

    for result in results:
        if result["status"] == "success":
            report_lines.extend(
                [
                    f"### {result['model']}",
                    "",
                    "**可疑对样本**:",
                    "",
                ]
            )

            for i, pair in enumerate(result["quality_indicators"]["suspicious_pairs_sample"], 1):
                report_lines.append(f"{i}. 相似度: {pair['similarity']:.3f}")
                report_lines.append(f"   - {pair['text1']}")
                report_lines.append(f"   - {pair['text2']}")
                report_lines.append("")

    # 保存报告
    report_content = "\n".join(report_lines)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(report_content)

    print("\n" + report_content)


async def main():
    """主流程"""
    # 配置
    TENANT_ID = "02d40e5c-5c8b-4c95-a8b3-3c2f05b11bd1"  # 替换为你的租户ID
    BOARD_ID = None  # 可选：指定看板ID
    LIMIT = 100  # 最多处理的反馈数量

    # 输出目录
    data_dir = Path(__file__).parent / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    # 1. 测试所有模型
    print("\n🚀 开始聚类质量测试...\n")
    results = await compare_clustering_quality(
        tenant_id=TENANT_ID,
        board_id=BOARD_ID,
        limit=LIMIT,
    )

    if not results:
        print("❌ 没有完成任何测试")
        return

    # 2. 保存结果
    results_file = data_dir / "clustering_quality_results.json"
    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n💾 测试结果已保存: {results_file}")

    # 3. 生成报告
    report_file = data_dir / "clustering_quality_report.md"
    generate_clustering_report(results, report_file)

    print(f"📄 测试报告已保存: {report_file}")
    print("\n✅ 测试完成！")


if __name__ == "__main__":
    asyncio.run(main())
