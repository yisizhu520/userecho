"""临时降低聚类质量门槛"""
import asyncio
from backend.database.db import async_db_session
from backend.app.userecho.service.clustering_config_service import clustering_config_service


async def lower_quality_threshold():
    async with async_db_session.begin() as db:
        # 获取当前配置
        current_config = await clustering_config_service.get_clustering_config(db, "default-tenant")
        
        print("当前配置：")
        print(f"  preset_mode: {current_config.get('preset_mode')}")
        print(f"  min_silhouette: {current_config.get('min_silhouette')}")
        print(f"  max_noise_ratio: {current_config.get('max_noise_ratio')}")
        
        # 降低质量门槛
        new_params = {
            "min_silhouette": 0.1,  # 从 0.3 降低到 0.1
            "max_noise_ratio": 0.6,  # 从 0.5 提高到 0.6
        }
        
        await clustering_config_service.update_custom_params(
            db=db,
            tenant_id="default-tenant",
            params=new_params,
        )
        
        print("\n✅ 已更新配置：")
        print(f"  min_silhouette: 0.3 -> 0.1")
        print(f"  max_noise_ratio: 0.5 -> 0.6")
        print("\n现在可以重新触发聚类任务了")


if __name__ == "__main__":
    asyncio.run(lower_quality_threshold())
