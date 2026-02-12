"""反馈聚类算法

使用 DBSCAN 进行基于相似度的聚类
"""

import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.metrics.pairwise import cosine_similarity

from backend.common.log import log
from backend.core.conf import settings


class FeedbackClustering:
    """反馈聚类引擎 - MVP 简化版"""

    def __init__(
        self,
        similarity_threshold: float | None = None,
        min_samples: int | None = None
    ):
        """
        初始化聚类引擎

        Args:
            similarity_threshold: 相似度阈值 (0-1)，越高越严格
            min_samples: 最小样本数，一个聚类至少需要的样本数
        """
        self.threshold = similarity_threshold or settings.CLUSTERING_SIMILARITY_THRESHOLD
        self.min_samples = min_samples or settings.CLUSTERING_MIN_SAMPLES

    def cluster(self, embeddings: np.ndarray) -> np.ndarray:
        """
        使用 DBSCAN 聚类

        Args:
            embeddings: shape (n_samples, embedding_dim) 的 embedding 矩阵

        Returns:
            labels: shape (n_samples,) 聚类标签，-1 表示噪声点
        """
        if embeddings.shape[0] < self.min_samples:
            log.warning(f'Too few samples for clustering: {embeddings.shape[0]} < {self.min_samples}')
            return np.full(embeddings.shape[0], -1)

        try:
            # 计算余弦相似度矩阵
            similarity_matrix = cosine_similarity(embeddings)

            # 转换为距离矩阵 (1 - similarity)
            # clip 确保相似度在 [-1, 1] 范围内，距离非负
            similarity_matrix = np.clip(similarity_matrix, -1.0, 1.0)
            distance_matrix = 1 - similarity_matrix

            # DBSCAN 聚类
            clustering = DBSCAN(
                eps=1 - self.threshold,  # 距离阈值
                min_samples=self.min_samples,  # 最小聚类大小
                metric='precomputed'
            )

            labels = clustering.fit_predict(distance_matrix)

            # 统计聚类结果
            n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
            n_noise = list(labels).count(-1)

            log.info(f'Clustering completed: {n_clusters} clusters, {n_noise} noise points')

            return labels

        except Exception as e:
            log.error(f'Clustering failed: {e}')
            return np.full(embeddings.shape[0], -1)

    def find_similar_feedbacks(
        self,
        query_embedding: np.ndarray,
        all_embeddings: np.ndarray,
        top_k: int = 10
    ) -> list[tuple[int, float]]:
        """
        查找最相似的反馈

        Args:
            query_embedding: 查询向量 shape (embedding_dim,)
            all_embeddings: 所有向量 shape (n_samples, embedding_dim)
            top_k: 返回前 K 个最相似的

        Returns:
            [(index, similarity), ...] 相似度从高到低排序
        """
        try:
            # 计算相似度
            similarities = cosine_similarity([query_embedding], all_embeddings)[0]

            # 获取 top-k 索引
            top_indices = np.argsort(similarities)[::-1][:top_k]

            # 返回 (索引, 相似度) 元组列表
            return [(int(idx), float(similarities[idx])) for idx in top_indices]

        except Exception as e:
            log.error(f'Failed to find similar feedbacks: {e}')
            return []

    def calculate_cluster_quality(
        self,
        embeddings: np.ndarray,
        labels: np.ndarray
    ) -> dict[str, float]:
        """
        计算聚类质量指标

        Args:
            embeddings: embedding 矩阵
            labels: 聚类标签

        Returns:
            包含质量指标的字典
        """
        try:
            from sklearn.metrics import silhouette_score, davies_bouldin_score

            # 过滤噪声点
            mask = labels != -1
            if mask.sum() < 2:
                return {'silhouette': 0.0, 'davies_bouldin': float('inf'), 'noise_ratio': 1.0}

            filtered_embeddings = embeddings[mask]
            filtered_labels = labels[mask]

            # 轮廓系数 (-1 到 1，越接近 1 越好)
            silhouette = silhouette_score(filtered_embeddings, filtered_labels, metric='cosine')

            # Davies-Bouldin 指数 (越小越好)
            davies_bouldin = davies_bouldin_score(filtered_embeddings, filtered_labels)

            # 噪声比例
            noise_ratio = (labels == -1).sum() / len(labels)

            return {
                'silhouette': float(silhouette),
                'davies_bouldin': float(davies_bouldin),
                'noise_ratio': float(noise_ratio)
            }

        except Exception as e:
            log.error(f'Failed to calculate cluster quality: {e}')
            return {'silhouette': 0.0, 'davies_bouldin': float('inf'), 'noise_ratio': 1.0}


# 全局单例
clustering_engine = FeedbackClustering()
