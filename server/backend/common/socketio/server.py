import urllib.parse

import socketio

from backend.common.log import log
from backend.common.security.jwt import jwt_authentication
from backend.core.conf import settings
from backend.database.redis import redis_client


def get_redis_url_for_socketio() -> str:
    """获取 Socket.IO 使用的 Redis URL"""
    if settings.REDIS_URL:
        return settings.REDIS_URL

    # 构造 Redis URL
    password = urllib.parse.quote(settings.REDIS_PASSWORD) if settings.REDIS_PASSWORD else ''
    auth = f':{password}' if password else ''
    if settings.REDIS_USERNAME:
        auth = f'{settings.REDIS_USERNAME}:{password}'

    return f'redis://{auth}@{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DATABASE}'


def get_redis_manager_kwargs() -> dict:
    """获取 Redis Manager 的连接参数（包含 SSL 配置）"""
    redis_url = get_redis_url_for_socketio()
    kwargs = {'url': redis_url}

    # TLS 连接跳过证书验证（与 redis.py、celery.py 保持一致）
    if redis_url.startswith('rediss://'):
        kwargs['redis_options'] = {'ssl_cert_reqs': None}

    return kwargs


# 创建 Socket.IO 服务器实例
sio = socketio.AsyncServer(
    client_manager=socketio.AsyncRedisManager(**get_redis_manager_kwargs()),
    async_mode='asgi',
    cors_allowed_origins=settings.CORS_ALLOWED_ORIGINS,
    cors_credentials=True,
    namespaces=['/ws'],
)


@sio.event
async def connect(sid, environ, auth) -> bool:
    """Socket 连接事件"""
    if not auth:
        log.error('WebSocket 连接失败：无授权')
        return False

    session_uuid = auth.get('session_uuid')
    token = auth.get('token')
    if not token or not session_uuid:
        log.error('WebSocket 连接失败：授权失败，请检查')
        return False

    # 免授权直连
    if token == settings.WS_NO_AUTH_MARKER:
        await redis_client.sadd(settings.TOKEN_ONLINE_REDIS_PREFIX, session_uuid)
        return True

    try:
        await jwt_authentication(token)
    except Exception as e:
        log.info(f'WebSocket 连接失败：{e!s}')
        return False

    await redis_client.sadd(settings.TOKEN_ONLINE_REDIS_PREFIX, session_uuid)
    return True


@sio.event
async def disconnect(sid) -> None:
    """Socket 断开连接事件"""
    await redis_client.spop(settings.TOKEN_ONLINE_REDIS_PREFIX)
