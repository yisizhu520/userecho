"""步骤 1: 准备标注数据集

从真实反馈中导出可疑的高相似度对，进行人工标注。
目标：100对标注数据（50相似 + 50不相似）

运行方式：
    cd server
    python scripts/embedding_comparison/01_prepare_annotation_dataset.py
"""

import asyncio
import json
from pathlib import Path

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy import select

from backend.app.userecho.model.feedback import Feedback
from backend.database.db import async_db_session
from backend.utils.ai_client import ai_client


async def export_suspicious_pairs(
    tenant_id: str,
    board_id: str | None = None,
    min_similarity: float = 0.85,
    limit: int = 150,
) -> list[dict]:
    """
    导出可疑的高相似度对（Volcengine 给出高分但实际可能不相关的）

    Args:
        tenant_id: 租户ID
        board_id: 看板ID（可选）
        min_similarity: 最低相似度阈值
        limit: 最多导出的反馈数量

    Returns:
        可疑对列表
    """
    print(f"Exporting suspicious pairs for tenant: {tenant_id}")

    async with async_db_session.begin() as db:
        # 1. 获取反馈数据
        query = select(Feedback).where(Feedback.tenant_id == tenant_id, Feedback.deleted_at.is_(None))

        if board_id:
            query = query.where(Feedback.board_id == board_id)

        query = query.limit(limit)
        result = await db.execute(query)
        feedbacks = result.scalars().all()

        if len(feedbacks) < 2:
            print(f"Not enough feedbacks: {len(feedbacks)}")
            return []

        print(f"Loaded {len(feedbacks)} feedbacks")

        # 2. 获取所有反馈的 embedding（使用当前默认模型 - Volcengine）
        texts = [f.content for f in feedbacks]
        print("Fetching embeddings from Volcengine...")
        embeddings_raw = await ai_client.get_embeddings_batch(texts)

        # 过滤失败的 embedding
        valid_indices = [i for i, emb in enumerate(embeddings_raw) if emb is not None]
        embeddings = np.array([embeddings_raw[i] for i in valid_indices])
        valid_feedbacks = [feedbacks[i] for i in valid_indices]

        if len(embeddings) < 2:
            print("Not enough valid embeddings")
            return []

        print(f"Valid embeddings: {len(embeddings)}/{len(feedbacks)}")

        # 3. 计算相似度矩阵
        similarity_matrix = cosine_similarity(embeddings)

        # 4. 提取高相似度对
        pairs = []
        n = len(valid_feedbacks)

        for i in range(n):
            for j in range(i + 1, n):
                sim = similarity_matrix[i][j]

                # 只保留高相似度的（可能误判的）
                if sim >= min_similarity:
                    f1 = valid_feedbacks[i]
                    f2 = valid_feedbacks[j]

                    pairs.append(
                        {
                            "feedback1_id": f1.id,
                            "feedback1_content": f1.content,
                            "feedback2_id": f2.id,
                            "feedback2_content": f2.content,
                            "similarity": float(sim),
                            "label": None,  # 待标注
                        }
                    )

        # 按相似度排序
        pairs.sort(key=lambda x: x["similarity"], reverse=True)

        print(f"Found {len(pairs)} high-similarity pairs (>= {min_similarity})")

        return pairs


def interactive_annotation(pairs: list[dict], max_annotations: int = 100) -> list[dict]:
    """
    交互式标注

    Args:
        pairs: 待标注的反馈对
        max_annotations: 最多标注数量

    Returns:
        标注完成的数据集
    """
    annotations = []

    print("\n" + "=" * 80)
    print("开始标注数据集".center(80))
    print("=" * 80)
    print("\n指令说明：")
    print("  y - 相似（同一需求的不同表达）")
    print("  n - 不相似（完全不同的需求）")
    print("  s - 跳过当前对")
    print("  q - 退出标注\n")

    for i, pair in enumerate(pairs):
        if len(annotations) >= max_annotations:
            print(f"\n✅ 已达到目标数量 ({max_annotations})，停止标注")
            break

        print("\n" + "-" * 80)
        print(f"进度: {len(annotations)}/{max_annotations} | 当前: {i + 1}/{len(pairs)}")
        print(f"相似度: {pair['similarity']:.4f}")
        print("-" * 80)
        print(f"\n反馈1: {pair['feedback1_content']}")
        print(f"\n反馈2: {pair['feedback2_content']}")

        while True:
            choice = input("\n是否相似？(y/n/s/q): ").strip().lower()

            if choice == "q":
                print("\n⚠️  用户退出标注")
                return annotations

            if choice == "s":
                print("⏭️  跳过")
                break

            if choice in ["y", "n"]:
                pair["label"] = 1 if choice == "y" else 0
                annotations.append(pair)
                print(f"✅ 标记为: {'相似' if choice == 'y' else '不相似'}")
                break

            print("❌ 无效输入，请输入 y/n/s/q")

    return annotations


async def main():
    """主流程"""
    # 配置
    TENANT_ID = "default-tenant"  # 替换为你的租户ID
    BOARD_ID = None  # 可选：指定看板ID
    MIN_SIMILARITY = 0.85  # 最低相似度
    LIMIT = 150  # 最多加载的反馈数量
    MAX_ANNOTATIONS = 100  # 目标标注数量

    # 输出目录
    output_dir = Path(__file__).parent / "data"
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. 导出可疑对
    print("\n🔍 正在分析反馈数据...")
    pairs = await export_suspicious_pairs(
        tenant_id=TENANT_ID,
        board_id=BOARD_ID,
        min_similarity=MIN_SIMILARITY,
        limit=LIMIT,
    )

    if not pairs:
        print("❌ 没有找到可疑对，请检查数据或降低相似度阈值")
        return

    print(f"\n✅ 找到 {len(pairs)} 对高相似度反馈")

    # 2. 保存原始数据（备份）
    raw_file = output_dir / "suspicious_pairs_raw.json"
    with open(raw_file, "w", encoding="utf-8") as f:
        json.dump(pairs, f, ensure_ascii=False, indent=2)
    print(f"💾 原始数据已保存: {raw_file}")

    # 3. 交互式标注
    print("\n" + "=" * 80)
    print("准备开始人工标注".center(80))
    print("=" * 80)
    input("\n按 Enter 继续...")

    annotations = interactive_annotation(pairs, max_annotations=MAX_ANNOTATIONS)

    if not annotations:
        print("\n❌ 没有完成任何标注")
        return

    # 4. 保存标注结果
    annotation_file = output_dir / "annotation_dataset.json"
    with open(annotation_file, "w", encoding="utf-8") as f:
        json.dump(annotations, f, ensure_ascii=False, indent=2)

    # 5. 统计
    similar_count = sum(1 for a in annotations if a["label"] == 1)
    dissimilar_count = sum(1 for a in annotations if a["label"] == 0)

    print("\n" + "=" * 80)
    print("标注完成".center(80))
    print("=" * 80)
    print(f"\n总标注数: {len(annotations)}")
    print(f"相似对: {similar_count}")
    print(f"不相似对: {dissimilar_count}")
    print(f"\n💾 标注数据已保存: {annotation_file}")
    print("\n✅ 可以运行下一步: 02_compare_embedding_models.py")


if __name__ == "__main__":
    asyncio.run(main())
