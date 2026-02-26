import os
import urllib.parse

import celery
import celery_aio_pool

from backend.app.task.tasks.beat import LOCAL_BEAT_SCHEDULE
from backend.common.enums import DataBaseType
from backend.core.conf import settings
from backend.core.path_conf import BASE_PATH


def find_task_packages() -> list[str]:
    packages = []
    task_dir = BASE_PATH / "app" / "task" / "tasks"
    for root, _dirs, files in os.walk(task_dir):
        if "tasks.py" in files:
            package = root.replace(str(BASE_PATH.parent) + os.path.sep, "").replace(os.path.sep, ".")
            packages.append(package)
    return packages


def init_celery() -> celery.Celery:
    """初始化 Celery 应用"""

    # TODO: Update this work if celery version >= 6.0.0
    # https://github.com/fastapi-practices/fastapi_best_architecture/issues/321
    # https://github.com/celery/celery/issues/7874
    celery.app.trace.build_tracer = celery_aio_pool.build_async_tracer
    celery.app.trace.reset_worker_optimizations()

    # DEBUG: 打印环境变量和配置
    print(f"[Celery Init] CELERY_BROKER={settings.CELERY_BROKER}")
    print(f"[Celery Init] REDIS_HOST={settings.REDIS_HOST}")
    print(f"[Celery Init] REDIS_PORT={settings.REDIS_PORT}")
    print(f"[Celery Init] REDIS_URL={settings.REDIS_URL}")
    print(f"[Celery Init] CELERY_BROKER_REDIS_DATABASE={settings.CELERY_BROKER_REDIS_DATABASE}")

    broker_url = None
    broker_use_ssl = None
    if settings.CELERY_BROKER == "redis":
        if settings.REDIS_URL:
            # 如果使用 REDIS_URL（如 Upstash），需要替换数据库编号
            # rediss://default:password@host:port/0 -> rediss://default:password@host:port/N
            broker_url = settings.REDIS_URL.rsplit("/", 1)[0] + f"/{settings.CELERY_BROKER_REDIS_DATABASE}"

            # TLS 连接跳过证书验证（与 redis.py 保持一致）
            if settings.REDIS_URL.startswith("rediss://"):
                broker_use_ssl = {"ssl_cert_reqs": None}
        else:
            # 构造 Redis URL
            password = urllib.parse.quote(settings.REDIS_PASSWORD) if settings.REDIS_PASSWORD else ""
            auth = f":{password}" if password else ""
            if settings.REDIS_USERNAME:
                auth = f"{settings.REDIS_USERNAME}:{password}"
            broker_url = (
                f"redis://{auth}@{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.CELERY_BROKER_REDIS_DATABASE}"
            )
            print(f"[Celery Init] Constructed broker_url: {broker_url}")
    else:
        # RabbitMQ fallback
        print(f"[Celery Init] Using RabbitMQ broker")
        print(f"[Celery Init] RABBITMQ_HOST={settings.CELERY_RABBITMQ_HOST}")
        print(f"[Celery Init] RABBITMQ_USERNAME={settings.CELERY_RABBITMQ_USERNAME}")
        broker_url = f"amqp://{settings.CELERY_RABBITMQ_USERNAME}:{urllib.parse.quote(settings.CELERY_RABBITMQ_PASSWORD)}@{settings.CELERY_RABBITMQ_HOST}:{settings.CELERY_RABBITMQ_PORT}/{settings.CELERY_RABBITMQ_VHOST}"
        print(f"[Celery Init] Constructed broker_url: {broker_url}")

    result_backend = f"db+postgresql+psycopg://{settings.DATABASE_USER}:{urllib.parse.quote(settings.DATABASE_PASSWORD)}@{settings.DATABASE_HOST}:{settings.DATABASE_PORT}/{settings.DATABASE_SCHEMA}"
    if DataBaseType.mysql == settings.DATABASE_TYPE:
        result_backend = result_backend.replace("postgresql+psycopg", "mysql+pymysql")

    # https://docs.celeryq.dev/en/stable/userguide/configuration.html
    celery_config = {
        "broker_url": broker_url,
        "broker_connection_retry_on_startup": True,
        "result_backend": result_backend,
        "result_extended": True,
        "database_engine_options": {"echo": settings.DATABASE_ECHO},
        "beat_schedule": LOCAL_BEAT_SCHEDULE,
        "beat_scheduler": "backend.app.task.utils.schedulers:DatabaseScheduler",
        "task_cls": "backend.app.task.tasks.base:TaskBase",
        "task_track_started": True,
        "enable_utc": False,
        "timezone": settings.DATETIME_TIMEZONE,
        "worker_send_task_events": True,
        "task_send_sent_event": True,
    }

    print(f"[Celery Init] Final broker_url: {broker_url}")
    print(f"[Celery Init] Final result_backend: {result_backend}")

    # 如果需要 SSL 配置，添加到配置中
    if broker_use_ssl is not None:
        celery_config["broker_use_ssl"] = broker_use_ssl

    app = celery.Celery("fba_celery", **celery_config)

    # 在 Celery 中设置此参数无效
    # 参数：https://github.com/celery/celery/issues/7270
    app.loader.override_backends = {"db": "backend.app.task.database:DatabaseBackend"}

    # 自动发现任务
    packages = find_task_packages()
    app.autodiscover_tasks(packages)

    # 配置 loguru 文件日志（确保 Celery worker 的日志也能写入文件）
    # 只在 worker 进程中配置，beat 和 flower 不需要
    # 通过检查 argv 判断是否是 worker 进程
    import sys

    if "worker" in sys.argv:
        from backend.common.log import set_custom_logfile, setup_logging

        setup_logging()
        set_custom_logfile()

    return app


# 创建 Celery 实例
celery_app: celery.Celery = init_celery()
