"""检查聚类质量指标"""
import asyncio
import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.metrics import silhouette_score
from backend.database.db import async_db_session
from sqlalchemy import select
from backend.app.userecho.model.feedback import Feedback


async def check_clustering_quality():
    async with async_db_session() as db:
        # 获取 pending 状态的反馈
        feedbacks_query = (
            select(Feedback)
            .where(
                Feedback.tenant_id == "default-tenant",
                Feedback.deleted_at.is_(None),
                Feedback.clustering_status == "pending",
                Feedback.board_id == "default-board",
            )
            .limit(100)
        )
        
        result = await db.execute(feedbacks_query)
        feedbacks = list(result.scalars().all())
        
        if not feedbacks:
            print("没有找到 pending 状态的反馈")
            return
        
        print(f"找到 {len(feedbacks)} 条 pending 反馈")
        
        # 提取 embeddings
        embeddings = []
        for f in feedbacks:
            if f.embedding is not None:
                embeddings.append(f.embedding)
        
        if len(embeddings) < 2:
            print(f"Embedding 不足：{len(embeddings)} 条")
            return
        
        embeddings_array = np.array(embeddings)
        print(f"Embeddings shape: {embeddings_array.shape}")
        
        # 执行 DBSCAN 聚类（使用默认配置）
        eps = 0.15  # 默认配置
        min_samples = 2  # 默认配置
        
        dbscan = DBSCAN(eps=eps, min_samples=min_samples, metric="cosine")
        labels = dbscan.fit_predict(embeddings_array)
        
        n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
        n_noise = list(labels).count(-1)
        
        print(f"\n聚类结果：")
        print(f"  聚类数量: {n_clusters}")
        print(f"  噪音点数量: {n_noise}")
        print(f"  噪音比例: {n_noise / len(labels):.2%}")
        
        # 计算质量指标
        if n_clusters > 0 and len(set(labels)) > 1:
            silhouette = silhouette_score(embeddings_array, labels, metric="cosine")
        else:
            silhouette = -1.0
        
        noise_ratio = n_noise / len(labels) if len(labels) > 0 else 1.0
        
        print(f"\n质量指标：")
        print(f"  silhouette: {silhouette:.4f}")
        print(f"  noise_ratio: {noise_ratio:.4f}")
        
        # 检查是否通过质量门槛
        min_silhouette = 0.3
        max_noise_ratio = 0.5
        
        print(f"\n质量门槛：")
        print(f"  要求 silhouette >= {min_silhouette}: {'✅' if silhouette >= min_silhouette else '❌'} (当前: {silhouette:.4f})")
        print(f"  要求 noise_ratio <= {max_noise_ratio}: {'✅' if noise_ratio <= max_noise_ratio else '❌'} (当前: {noise_ratio:.4f})")
        
        if silhouette >= min_silhouette and noise_ratio <= max_noise_ratio:
            print("\n✅ 通过质量门槛，可以创建主题")
        else:
            print("\n❌ 未通过质量门槛，跳过主题创建")
            print("\n建议：")
            if silhouette < min_silhouette:
                print(f"  - silhouette 太低 ({silhouette:.4f} < {min_silhouette})，聚类质量不够好")
                print("  - 可能需要调整 eps 参数或等待更多反馈")
            if noise_ratio > max_noise_ratio:
                print(f"  - noise_ratio 太高 ({noise_ratio:.4f} > {max_noise_ratio})，噪音点太多")
                print("  - 可能需要降低 min_samples 或调整 eps 参数")


if __name__ == "__main__":
    asyncio.run(check_clustering_quality())
