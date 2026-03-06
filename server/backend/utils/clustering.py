"""反馈聚类算法

使用 DBSCAN 和 HDBSCAN 进行基于相似度的聚类
"""

import math

import numpy as np

from sklearn.cluster import DBSCAN
from sklearn.metrics.pairwise import cosine_similarity

try:
    from hdbscan import HDBSCAN

    HDBSCAN_AVAILABLE = True
except ImportError:
    HDBSCAN_AVAILABLE = False

from backend.common.log import log
from backend.core.conf import settings


class FeedbackClustering:
    """反馈聚类引擎 - MVP 简化版"""

    def __init__(self, similarity_threshold: float | None = None, min_samples: int | None = None) -> None:
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
            log.warning(f"Too few samples for clustering: {embeddings.shape[0]} < {self.min_samples}")
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
                metric="precomputed",
            )

            labels = clustering.fit_predict(distance_matrix)

            # 统计聚类结果
            n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
            n_noise = list(labels).count(-1)

            log.info(f"Clustering completed: {n_clusters} clusters, {n_noise} noise points")

            return labels

        except Exception as e:
            log.error(f"Clustering failed: {e}")
            return np.full(embeddings.shape[0], -1)

    def find_similar_feedbacks(
        self, query_embedding: np.ndarray, all_embeddings: np.ndarray, top_k: int = 10
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
            log.error(f"Failed to find similar feedbacks: {e}")
            return []

    def calculate_cluster_quality(self, embeddings: np.ndarray, labels: np.ndarray) -> dict[str, float | None]:
        """
        计算聚类质量指标

        Args:
            embeddings: embedding 矩阵
            labels: 聚类标签

        Returns:
            包含质量指标的字典
            - silhouette: 轮廓系数 (-1 到 1，越接近 1 越好)
            - davies_bouldin: Davies-Bouldin 指数 (越小越好，None 表示无法计算)
            - noise_ratio: 噪声比例 (0 到 1)
        """
        try:
            from sklearn.metrics import davies_bouldin_score, silhouette_score

            # 过滤噪声点
            mask = labels != -1
            filtered_labels = labels[mask]

            # 检查是否有足够的聚类用于计算质量指标
            n_unique_labels = len(set(filtered_labels))
            if n_unique_labels < 2:
                # 只有 0 或 1 个聚类，无法计算质量指标
                noise_ratio = (labels == -1).sum() / len(labels)
                return {"silhouette": 0.0, "davies_bouldin": None, "noise_ratio": float(noise_ratio)}

            filtered_embeddings = embeddings[mask]

            # 轮廓系数 (-1 到 1，越接近 1 越好)
            silhouette = silhouette_score(filtered_embeddings, filtered_labels, metric="cosine")

            # Davies-Bouldin 指数 (越小越好)
            davies_bouldin = davies_bouldin_score(filtered_embeddings, filtered_labels)

            # 防止 Infinity 导致 JSON 序列化失败
            davies_bouldin = None if math.isinf(davies_bouldin) or math.isnan(davies_bouldin) else float(davies_bouldin)

            # 噪声比例
            noise_ratio = (labels == -1).sum() / len(labels)

            return {
                "silhouette": float(silhouette),
                "davies_bouldin": davies_bouldin,
                "noise_ratio": float(noise_ratio),
            }

        except Exception as e:
            log.error(f"Failed to calculate cluster quality: {e}")
            return {"silhouette": 0.0, "davies_bouldin": None, "noise_ratio": 1.0}

    def cluster_hdbscan(
        self,
        embeddings: np.ndarray,
        min_cluster_size: int | None = None,
        min_samples: int | None = None,
    ) -> np.ndarray:
        """
        使用 HDBSCAN 进行自适应层次聚类

        Args:
            embeddings: shape (n_samples, embedding_dim) 的 embedding 矩阵
            min_cluster_size: 最小聚类大小（至少 N 条反馈才形成聚类），默认使用配置值
            min_samples: 核心点要求（至少 N 个邻居才是核心点），默认使用配置值

        Returns:
            labels: shape (n_samples,) 聚类标签，-1 表示噪声点
        """
        if not HDBSCAN_AVAILABLE:
            log.warning("HDBSCAN not available, falling back to DBSCAN")
            return self.cluster(embeddings)

        # 使用配置值或传入参数
        _min_cluster_size = min_cluster_size or self.min_samples
        _min_samples = min_samples or max(1, self.min_samples - 1)

        if embeddings.shape[0] < _min_cluster_size:
            log.warning(f"Too few samples for HDBSCAN clustering: {embeddings.shape[0]} < {_min_cluster_size}")
            return np.full(embeddings.shape[0], -1)

        try:
            # 计算余弦相似度矩阵
            similarity_matrix = cosine_similarity(embeddings)

            # 转换为距离矩阵 (1 - similarity)
            # 注意：HDBSCAN 要求 float64，embeddings 通常是 float32，必须显式转换
            similarity_matrix = np.clip(similarity_matrix, -1.0, 1.0)
            distance_matrix = (1.0 - similarity_matrix).astype(np.float64)
            np.fill_diagonal(distance_matrix, 0.0)

            # 初始化 HDBSCAN（使用预计算的距离矩阵）
            clusterer = HDBSCAN(
                min_cluster_size=_min_cluster_size,
                min_samples=_min_samples,
                metric="precomputed",  # 使用预计算的距离矩阵
                cluster_selection_method="eom",  # Excess of Mass (更保守)
                cluster_selection_epsilon=0.1,  # 合并相近聚类的阈值
            )

            # 执行聚类
            labels = clusterer.fit_predict(distance_matrix)

            # 统计聚类结果
            n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
            n_noise = list(labels).count(-1)

            log.info(
                f"HDBSCAN clustering completed: {n_clusters} clusters, {n_noise} noise points "
                f"(min_cluster_size={_min_cluster_size}, min_samples={_min_samples})"
            )

            return labels

        except Exception as e:
            log.error(f"HDBSCAN clustering failed: {e}, falling back to DBSCAN")
            return self.cluster(embeddings)


# 全局单例
clustering_engine = FeedbackClustering()
