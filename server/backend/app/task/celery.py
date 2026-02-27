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
    print(f"[Celery Init] Searching for tasks in: {task_dir}")
    
    for root, _dirs, files in os.walk(task_dir):
        if "tasks.py" in files:
            package = root.replace(str(BASE_PATH.parent) + os.path.sep, "").replace(os.path.sep, ".")
            print(f"[Celery Init] ✅ Found tasks package: {package}")
            packages.append(package)
    
    print(f"[Celery Init] Total task packages found: {len(packages)}")
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
    print(f"[Celery Init] ENV CELERY_BROKER_URL={os.getenv('CELERY_BROKER_URL')}")
    print(f"[Celery Init] ENV CELERY_RESULT_BACKEND={os.getenv('CELERY_RESULT_BACKEND')}")

    # 如果需要 SSL 配置，添加到配置中
    if broker_use_ssl is not None:
        celery_config["broker_use_ssl"] = broker_use_ssl

    app = celery.Celery("fba_celery", **celery_config)
    print(f"[Celery Init] App conf broker_url: {app.conf.broker_url}")
    print(f"[Celery Init] App conf result_backend: {app.conf.result_backend}")

    # 在 Celery 中设置此参数无效
    # 参数：https://github.com/celery/celery/issues/7270
    app.loader.override_backends = {"db": "backend.app.task.database:DatabaseBackend"}

    # 自动发现任务
    packages = find_task_packages()
    
    # 方式1: 使用 autodiscover_tasks（推荐）
    # autodiscover_tasks 会自动加载每个包下的 tasks 模块
    app.autodiscover_tasks(packages)
    
    # 方式2: 如果方式1不work，手动导入每个 tasks.py
    # 这是一个 fallback 方案
    if len(app.tasks) <= 10:  # 只有内置任务
        print(f"[Celery Init] ⚠️  autodiscover_tasks failed, trying manual import")
        for package in packages:
            try:
                import importlib
                module_name = f"{package}.tasks"
                importlib.import_module(module_name)
            except Exception as e:
                print(f"[Celery Init] ❌ Failed to import {module_name}: {e}")
    
    # 打印用户定义的任务（过滤掉 celery 内置任务）
    user_tasks = [k for k in app.tasks.keys() if not k.startswith('celery.')]
    print(f"[Celery Init] ✅ Registered {len(user_tasks)} user tasks: {user_tasks}")

    # 配置 loguru 文件日志（确保 Celery worker 的日志也能写入文件）
    # 只在 worker 进程中配置，beat 和 flower 不需要
    # 通过检查 argv 判断是否是 worker 进程
    import sys

    if "worker" in sys.argv:
        from backend.common.log import set_custom_logfile, setup_logging

        setup_logging()
        set_custom_logfile()
        
        # 注册 Celery 信号处理器（仅在 worker 进程）
        _register_celery_signals(app)

    return app


def _register_celery_signals(app: celery.Celery) -> None:
    """注册 Celery 信号处理器，用于调试任务执行流程"""
    from celery.signals import (
        after_task_publish,
        before_task_publish,
        task_failure,
        task_postrun,
        task_prerun,
        task_received,
        task_rejected,
        task_retry,
        task_success,
        worker_init,
        worker_ready,
        worker_shutdown,
    )

    @worker_init.connect
    def on_worker_init(**kwargs):
        print("[Celery Worker] 🔧 Worker initializing...")

    @worker_ready.connect
    def on_worker_ready(**kwargs):
        print("[Celery Worker] 🚀 Worker READY! Waiting for tasks...")
        print(f"[Celery Worker] Broker: {app.conf.broker_url}")
        print(f"[Celery Worker] Concurrency: {app.conf.worker_concurrency or 'default'}")

    @worker_shutdown.connect
    def on_worker_shutdown(**kwargs):
        print("[Celery Worker] 🛑 Worker shutting down...")

    @before_task_publish.connect
    def on_before_task_publish(sender=None, headers=None, body=None, **kwargs):
        task_name = headers.get('task', 'unknown') if headers else 'unknown'
        task_id = headers.get('id', 'unknown') if headers else 'unknown'
        print(f"[Celery Publish] 📤 Publishing task: {task_name} (id={task_id[:8]}...)")

    @after_task_publish.connect
    def on_after_task_publish(sender=None, headers=None, body=None, **kwargs):
        task_name = headers.get('task', 'unknown') if headers else 'unknown'
        task_id = headers.get('id', 'unknown') if headers else 'unknown'
        print(f"[Celery Publish] ✅ Published task: {task_name} (id={task_id[:8]}...)")

    @task_received.connect
    def on_task_received(request=None, **kwargs):
        if request:
            print(f"[Celery Worker] 📥 Received task: {request.name} (id={request.id[:8]}...)")

    @task_prerun.connect
    def on_task_prerun(task_id=None, task=None, **kwargs):
        print(f"[Celery Worker] ▶️  Starting task: {task.name} (id={task_id[:8]}...)")

    @task_postrun.connect
    def on_task_postrun(task_id=None, task=None, state=None, **kwargs):
        print(f"[Celery Worker] ⏹️  Finished task: {task.name} (id={task_id[:8]}..., state={state})")

    @task_success.connect
    def on_task_success(sender=None, result=None, **kwargs):
        print(f"[Celery Worker] ✅ Task succeeded: {sender.name}")

    @task_failure.connect
    def on_task_failure(task_id=None, exception=None, traceback=None, **kwargs):
        print(f"[Celery Worker] ❌ Task failed: {task_id[:8]}... - {exception}")

    @task_retry.connect
    def on_task_retry(task_id=None, reason=None, **kwargs):
        print(f"[Celery Worker] 🔄 Task retrying: {task_id[:8]}... - {reason}")

    @task_rejected.connect
    def on_task_rejected(message=None, **kwargs):
        print(f"[Celery Worker] 🚫 Task rejected: {message}")


# 创建 Celery 实例
celery_app: celery.Celery = init_celery()
