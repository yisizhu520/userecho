"""Cloudflare Turnstile 人机验证"""

import httpx

from backend.common.log import log
from backend.core.conf import settings

TURNSTILE_VERIFY_URL = 'https://challenges.cloudflare.com/turnstile/v0/siteverify'


async def verify_turnstile(token: str, remote_ip: str | None = None) -> bool:
    """
    验证 Turnstile token

    Args:
        token: 前端传来的 Turnstile 响应 token
        remote_ip: 可选，用户 IP 地址

    Returns:
        验证是否通过
    """
    if not settings.TURNSTILE_ENABLED:
        return True

    if not token:
        log.warning('Turnstile token is empty')
        return False

    payload = {
        'secret': settings.TURNSTILE_SECRET_KEY,
        'response': token,
    }
    if remote_ip:
        payload['remoteip'] = remote_ip

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(TURNSTILE_VERIFY_URL, data=payload)
            result = response.json()

            if not result.get('success'):
                log.warning(f'Turnstile verification failed: {result.get("error-codes")}')
                return False

            return True
    except Exception as e:
        log.error(f'Turnstile verification error: {e}')
        return False
