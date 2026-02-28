"""Demo 模式全局配额限制

防止恶意用户通过轮换账号刷爆 AI 额度
"""

from datetime import datetime
from typing import Literal

from fastapi import Depends, HTTPException, Request

from backend.common.log import log
from backend.core.conf import settings
from backend.database.redis import redis_client

# 配额类型
QuotaType = Literal["clustering", "ai_summary", "screenshot_ocr", "insights"]

# 配额配置映射
QUOTA_CONFIG = {
    "clustering": "DEMO_DAILY_QUOTA_CLUSTERING",
    "ai_summary": "DEMO_DAILY_QUOTA_AI_SUMMARY",
    "screenshot_ocr": "DEMO_DAILY_QUOTA_SCREENSHOT",
    "insights": "DEMO_DAILY_QUOTA_INSIGHTS",
}


async def get_quota_key(operation: QuotaType) -> str:
    """
    生成配额 Redis Key

    格式: demo:quota:{operation}:{date}
    示例: demo:quota:clustering:2026-01-24
    """
    date_str = datetime.now().strftime("%Y-%m-%d")
    return f"demo:quota:{operation}:{date_str}"


async def get_quota_limit(operation: QuotaType) -> int:
    """获取配额限制"""
    config_key = QUOTA_CONFIG.get(operation)
    if not config_key:
        return 0
    return getattr(settings, config_key, 0)


async def check_and_consume_quota(operation: QuotaType) -> None:
    """
    检查并扣减配额

    Args:
        operation: 操作类型

    Raises:
        HTTPException: 配额不足时抛出 403
    """
    # 非 Demo 模式直接放行
    if not settings.DEMO_MODE:
        return

    quota_key = await get_quota_key(operation)
    quota_limit = await get_quota_limit(operation)

    if quota_limit <= 0:
        return

    # 获取当前使用量
    try:
        current_usage = await redis_client.get(quota_key)
        if current_usage is None:
            current_usage = 0
        else:
            current_usage = int(current_usage)

        # 检查是否超限
        if current_usage >= quota_limit:
            log.warning(f"Demo quota exceeded for {operation}: {current_usage}/{quota_limit}")
            raise HTTPException(
                status_code=403,
                detail=f"今日 {operation} 配额已用尽（{current_usage}/{quota_limit}）。每日凌晨 2:00 (UTC+8) 重置。如需继续使用，请注册正式账号。",
            )

        # 扣减配额（原子自增）
        new_usage = await redis_client.incr(quota_key)

        # 首次创建时设置过期时间（48 小时，确保跨日不被误删）
        if new_usage == 1:
            await redis_client.expire(quota_key, 48 * 3600)

        log.info(f"Demo quota consumed: {operation} ({new_usage}/{quota_limit})")

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Failed to check demo quota for {operation}: {e}")
        # 配额检查失败时降级放行，避免影响正常用户
        return


async def require_demo_quota(
    operation: QuotaType,
    request: Request,  # noqa: ARG001
) -> None:
    """
    Demo 配额检查依赖

    用于保护 AI 功能接口
    """
    await check_and_consume_quota(operation)


# 依赖注入接口
def DependsDemoQuota(operation: QuotaType):  # noqa: N802
    """
    创建配额检查依赖

    示例:
        @router.post("/trigger", dependencies=[DependsDemoQuota("clustering")])
        async def trigger_clustering(...):
            ...
    """

    async def _check_quota(request: Request) -> None:
        await require_demo_quota(operation, request)

    return Depends(_check_quota)
