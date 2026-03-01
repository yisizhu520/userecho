import urllib.parse
from backend.core.conf import settings


def get_redis_url_for_socketio() -> str:
    """获取 Socket.IO 使用的 Redis URL"""
    if settings.REDIS_URL:
        return settings.REDIS_URL

    # 构造 Redis URL
    password = urllib.parse.quote(settings.REDIS_PASSWORD) if settings.REDIS_PASSWORD else ""
    auth = f":{password}" if password else ""
    if settings.REDIS_USERNAME:
        auth = f"{settings.REDIS_USERNAME}:{password}"

    return f"redis://{auth}@{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DATABASE}"


def get_redis_manager_kwargs() -> dict:
    """获取 Redis Manager 的连接参数（包含 SSL 配置）"""
    redis_url = get_redis_url_for_socketio()
    kwargs = {"url": redis_url}

    # TLS 连接跳过证书验证（与 redis.py、celery.py 保持一致）
    if redis_url.startswith("rediss://"):
        kwargs["redis_options"] = {"ssl_cert_reqs": None}

    return kwargs
