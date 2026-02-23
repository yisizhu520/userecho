"""安全相关依赖"""

from typing import Annotated

from fastapi import Depends, HTTPException, Header, Request

from backend.common.security.turnstile import verify_turnstile
from backend.core.conf import settings


async def require_turnstile(
    request: Request,
    x_turnstile_token: Annotated[str | None, Header()] = None,
) -> None:
    """
    Turnstile 验证依赖

    用于保护敏感接口（如 AI 功能）
    """
    if not settings.TURNSTILE_ENABLED:
        return

    if not x_turnstile_token:
        raise HTTPException(status_code=400, detail="请完成人机验证")

    client_ip = request.client.host if request.client else None
    is_valid = await verify_turnstile(x_turnstile_token, client_ip)

    if not is_valid:
        raise HTTPException(status_code=403, detail="人机验证失败，请刷新页面重试")


# 可复用的依赖
DependsTurnstile = Depends(require_turnstile)
