"""租户配置 API"""

from fastapi import APIRouter
from pydantic import BaseModel, Field

from backend.app.userecho.constants import CLUSTERING_PRESETS
from backend.app.userecho.service.clustering_config_service import clustering_config_service
from backend.common.response.response_schema import response_base
from backend.common.security.jwt import CurrentTenantId
from backend.database.db import CurrentSession, CurrentSessionTransaction

router = APIRouter(prefix="/config", tags=["UserEcho - 租户配置"])


# ========================================
# 请求体模型
# ========================================


class UpdatePresetParam(BaseModel):
    """更新预设模式参数"""

    preset_mode: str = Field(description="预设模式名称（strict/standard/relaxed）")


class UpdateParamsParam(BaseModel):
    """更新自定义参数"""

    params: dict = Field(description="要更新的参数字典")


class PreviewConfigParam(BaseModel):
    """预览配置参数"""

    preset_mode: str = Field(description="预设模式名称")


# ========================================
# 聚类配置 API
# ========================================


@router.get("/clustering/presets", summary="获取聚类预设模式")
async def get_clustering_presets():
    """
    获取所有聚类预设模式（不含技术参数）

    用于配置页面的选项展示
    """
    presets = {
        mode: {
            "display_name": config["display_name"],
            "description": config["description"],
            "use_case": config["use_case"],
        }
        for mode, config in CLUSTERING_PRESETS.items()
    }

    return response_base.success(data=presets)


@router.get("/clustering", summary="获取当前聚类配置")
async def get_clustering_config(
    db: CurrentSession,
    tenant_id: str = CurrentTenantId,
):
    """
    获取当前租户的聚类配置

    包含 preset_mode 和所有技术参数
    """
    config = await clustering_config_service.get_clustering_config(db, tenant_id)
    return response_base.success(data=config)


@router.post("/clustering/preset", summary="更新聚类预设模式")
async def update_clustering_preset(
    param: UpdatePresetParam,
    db: CurrentSessionTransaction,
    tenant_id: str = CurrentTenantId,
):
    """
    更新聚类预设模式

    系统会自动展开预设对应的技术参数
    """
    config = await clustering_config_service.update_preset(
        db=db,
        tenant_id=tenant_id,
        preset_mode=param.preset_mode,
    )

    return response_base.success(data=config)


@router.post("/clustering/preview", summary="预览聚类配置效果")
async def preview_clustering_config(
    param: PreviewConfigParam,
    db: CurrentSession,
    tenant_id: str = CurrentTenantId,
):
    """
    预览聚类配置效果（智能验证）

    使用租户最近的未聚类反馈进行试运行，
    返回预估的聚类效果
    """
    result = await clustering_config_service.preview_config_effect(
        db=db,
        tenant_id=tenant_id,
        preset_mode=param.preset_mode,
    )

    return response_base.success(data=result)


@router.put("/clustering/params", summary="微调聚类参数")
async def update_clustering_params(
    param: UpdateParamsParam,
    db: CurrentSessionTransaction,
    tenant_id: str = CurrentTenantId,
):
    """
    微调聚类参数（高级功能）

    允许基于预设进行细粒度调整
    修改后 preset_mode 会变为 'custom'
    """
    config = await clustering_config_service.update_custom_params(
        db=db,
        tenant_id=tenant_id,
        params=param.params,
    )

    return response_base.success(data=config)


# ========================================
# 战略关键词配置 API
# ========================================


class StrategicKeywordsParam(BaseModel):
    """战略关键词参数"""

    keywords: list[str] = Field(description="战略关键词列表")


# 默认战略关键词（用于新租户）
DEFAULT_STRATEGIC_KEYWORDS = ["信创", "国际化", "降本增效", "AI", "安全合规"]


@router.get("/strategic", summary="获取战略关键词配置")
async def get_strategic_keywords(
    db: CurrentSession,
    tenant_id: str = CurrentTenantId,
):
    """
    获取当前租户的战略关键词配置

    用于优先级评分的战略匹配度计算
    """
    from backend.app.userecho.service.tenant_config_service import tenant_config_service

    config = await tenant_config_service.get_config(
        db=db,
        tenant_id=tenant_id,
        config_group="strategic",
        default={"keywords": DEFAULT_STRATEGIC_KEYWORDS},
    )

    return response_base.success(data=config)


@router.put("/strategic", summary="更新战略关键词配置")
async def update_strategic_keywords(
    param: StrategicKeywordsParam,
    db: CurrentSessionTransaction,
    tenant_id: str = CurrentTenantId,
):
    """
    更新战略关键词配置

    老板设置一次，系统自动匹配计算优先级
    """
    from backend.app.userecho.service.tenant_config_service import tenant_config_service

    config_data = {"keywords": param.keywords}

    await tenant_config_service.set_config(
        db=db,
        tenant_id=tenant_id,
        config_group="strategic",
        config_data=config_data,
    )

    return response_base.success(data=config_data)
