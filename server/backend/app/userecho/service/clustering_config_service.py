"""聚类配置服务（基于通用配置系统）"""

import numpy as np

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.userecho.constants import CLUSTERING_PRESETS, DEFAULT_CLUSTERING_CONFIG
from backend.app.userecho.crud import crud_feedback
from backend.app.userecho.service.tenant_config_service import tenant_config_service
from backend.common.exception import errors
from backend.common.log import log
from backend.utils.ai_client import ai_client
from backend.utils.clustering import FeedbackClustering


class ClusteringConfigService:
    """聚类配置服务

    基于通用配置系统的聚类配置管理
    提供预设模式和自定义参数调整功能
    """

    CONFIG_GROUP = "clustering"

    async def get_clustering_config(self, db: AsyncSession, tenant_id: str) -> dict:
        """
        获取租户聚类配置

        Args:
            db: 数据库会话
            tenant_id: 租户 ID

        Returns:
            包含 preset_mode 和所有技术参数的字典
        """
        config = await tenant_config_service.get_config(
            db=db,
            tenant_id=tenant_id,
            config_group=self.CONFIG_GROUP,
            default=DEFAULT_CLUSTERING_CONFIG,
        )

        return config

    async def update_preset(
        self,
        db: AsyncSession,
        tenant_id: str,
        preset_mode: str,
    ) -> dict:
        """
        更新预设模式（自动展开技术参数）

        Args:
            db: 数据库会话
            tenant_id: 租户 ID
            preset_mode: 预设模式名称

        Returns:
            更新后的完整配置
        """
        if preset_mode not in CLUSTERING_PRESETS:
            raise errors.ForbiddenError(msg=f"Invalid preset mode: {preset_mode}")

        # 展开预设参数
        preset_config = CLUSTERING_PRESETS[preset_mode]
        config_data = {
            "preset_mode": preset_mode,
            **preset_config["params"],
        }

        await tenant_config_service.set_config(
            db=db,
            tenant_id=tenant_id,
            config_group=self.CONFIG_GROUP,
            config_data=config_data,
        )

        log.info(f"Updated clustering preset to {preset_mode} for tenant {tenant_id}")

        return config_data

    async def update_custom_params(
        self,
        db: AsyncSession,
        tenant_id: str,
        params: dict,
    ) -> dict:
        """
        更新自定义参数（基于预设微调）

        Args:
            db: 数据库会话
            tenant_id: 租户 ID
            params: 要更新的参数（部分更新）

        Returns:
            更新后的完整配置
        """
        # 获取当前配置
        current_config = await self.get_clustering_config(db, tenant_id)

        # 合并更新
        current_config.update(params)

        # 如果修改了技术参数，preset_mode 标记为 'custom'
        if any(k in params for k in ["similarity_threshold", "min_samples", "min_silhouette", "max_noise_ratio"]):
            current_config["preset_mode"] = "custom"

        await tenant_config_service.set_config(
            db=db,
            tenant_id=tenant_id,
            config_group=self.CONFIG_GROUP,
            config_data=current_config,
        )

        log.info(f"Updated custom clustering params for tenant {tenant_id}")

        return current_config

    async def preview_config_effect(
        self,
        db: AsyncSession,
        tenant_id: str,
        preset_mode: str,
    ) -> dict:
        """
        预览配置效果（智能验证）

        使用最近的未聚类反馈进行试运行

        Args:
            db: 数据库会话
            tenant_id: 租户 ID
            preset_mode: 要预览的预设模式

        Returns:
            预览结果（簇数量、覆盖率、质量指标）
        """
        if preset_mode not in CLUSTERING_PRESETS:
            raise errors.ForbiddenError(msg=f"Invalid preset mode: {preset_mode}")

        # 获取测试数据
        test_feedbacks = await crud_feedback.get_pending_clustering(
            db=db,
            tenant_id=tenant_id,
            limit=20,
            include_failed=True,
            force_recluster=False,
        )

        if len(test_feedbacks) < 2:
            return {
                "status": "insufficient_data",
                "message": "测试数据不足（至少需要2条反馈）",
                "test_samples": len(test_feedbacks),
            }

        # 获取 embeddings
        embeddings = []
        for fb in test_feedbacks:
            cached = crud_feedback.get_cached_embedding(fb)
            if cached is not None:
                embeddings.append(cached)
            else:
                emb = await ai_client.get_embedding(fb.content)
                if emb is not None:
                    embeddings.append(emb)

        if len(embeddings) < 2:
            return {
                "status": "embedding_failed",
                "message": "无法获取足够的 embedding",
                "test_samples": len(test_feedbacks),
                "valid_embeddings": len(embeddings),
            }

        # 使用新配置试运行聚类
        preset_params = CLUSTERING_PRESETS[preset_mode]["params"]
        engine = FeedbackClustering(
            similarity_threshold=preset_params["similarity_threshold"],
            min_samples=preset_params["min_samples"],
        )

        embeddings_array = np.array(embeddings)
        labels = engine.cluster(embeddings_array)
        quality = engine.calculate_cluster_quality(embeddings_array, labels)

        # 统计结果
        n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
        n_noise = list(labels).count(-1)
        coverage_rate = 1 - (n_noise / len(labels)) if len(labels) > 0 else 0

        # 质量评级
        silhouette = quality.get("silhouette", 0)
        if silhouette >= 0.5:
            quality_rating = "优秀"
        elif silhouette >= 0.3:
            quality_rating = "良好"
        elif silhouette >= 0.1:
            quality_rating = "一般"
        else:
            quality_rating = "较差"

        return {
            "status": "success",
            "test_samples": len(embeddings),
            "preview": {
                "clusters_count": n_clusters,
                "clusters_range": f"{max(0, n_clusters - 1)}-{n_clusters + 2}",  # 估算范围
                "coverage_rate": round(coverage_rate, 2),
                "coverage_percentage": f"{coverage_rate * 100:.0f}%",
                "quality_rating": quality_rating,
                "silhouette_score": round(silhouette, 3),
                "noise_ratio": round(quality["noise_ratio"], 2),
            },
            "config": preset_params,
        }


# 全局单例
clustering_config_service = ClusteringConfigService()
