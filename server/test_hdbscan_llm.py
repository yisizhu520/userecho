"""测试 HDBSCAN + LLM 校验聚类

验证配置是否生效：
1. CLUSTERING_USE_HDBSCAN=True
2. CLUSTERING_LLM_VALIDATION_ENABLED=True
"""

import asyncio

from backend.app.userecho.service.clustering_service import ClusteringService
from backend.common.log import log
from backend.core.conf import settings
from backend.database.db import async_db_session


async def main():
    """测试 HDBSCAN + LLM 校验"""

    print("\n" + "=" * 80)
    print("HDBSCAN + LLM 校验配置检查".center(80))
    print("=" * 80 + "\n")

    # 1. 检查配置
    print("📊 当前配置:")
    print(f"   - CLUSTERING_USE_HDBSCAN: {settings.CLUSTERING_USE_HDBSCAN}")
    print(f"   - CLUSTERING_HDBSCAN_MIN_CLUSTER_SIZE: {settings.CLUSTERING_HDBSCAN_MIN_CLUSTER_SIZE}")
    print(f"   - CLUSTERING_HDBSCAN_MIN_SAMPLES: {settings.CLUSTERING_HDBSCAN_MIN_SAMPLES}")
    print(f"   - CLUSTERING_LLM_VALIDATION_ENABLED: {settings.CLUSTERING_LLM_VALIDATION_ENABLED}")
    print(f"   - CLUSTERING_LLM_VALIDATION_MIN_SIZE: {settings.CLUSTERING_LLM_VALIDATION_MIN_SIZE}")

    if not settings.CLUSTERING_USE_HDBSCAN:
        print("\n❌ HDBSCAN 未启用！请设置 CLUSTERING_USE_HDBSCAN=True")
        return

    if not settings.CLUSTERING_LLM_VALIDATION_ENABLED:
        print("\n⚠️  LLM 校验未启用！建议设置 CLUSTERING_LLM_VALIDATION_ENABLED=True")

    print("\n✅ 配置检查通过")

    # 2. 触发聚类
    print("\n" + "=" * 80)
    print("触发聚类任务".center(80))
    print("=" * 80 + "\n")

    TENANT_ID = "default-tenant"
    MAX_FEEDBACKS = 200

    try:
        service = ClusteringService()

        async with async_db_session.begin() as db:
            result = await service.trigger_clustering(
                db=db,
                tenant_id=TENANT_ID,
                max_feedbacks=MAX_FEEDBACKS,
                force_recluster=False,
            )

        print("\n📊 聚类结果:")
        print(f"   - 状态: {result.get('status')}")
        print(f"   - 反馈数: {result.get('feedbacks_count', 0)}")
        print(f"   - 聚类数: {result.get('clusters_count', 0)}")
        print(f"   - 创建主题: {result.get('topics_created', 0)}")
        print(f"   - 失败主题: {result.get('topics_failed', 0)}")

        if "quality_metrics" in result:
            metrics = result["quality_metrics"]
            print("\n📈 质量指标:")
            print(f"   - 轮廓系数: {metrics.get('silhouette', 0):.4f}")
            print(f"   - 噪声比例: {metrics.get('noise_ratio', 0):.2%}")

        if result.get("topics_created", 0) > 0:
            print(f"\n✅ 成功创建 {result['topics_created']} 个主题")
            if "topics" in result:
                for i, topic in enumerate(result["topics"][:5], 1):
                    print(f"   {i}. {topic.get('title', 'N/A')} ({topic.get('feedback_count', 0)} 条反馈)")
        else:
            print(f"\n⚠️  本次聚类未创建主题: {result.get('message', 'N/A')}")

    except Exception as e:
        log.error(f"聚类测试失败: {e}")
        print(f"\n❌ 聚类测试失败: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
