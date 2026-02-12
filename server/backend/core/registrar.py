import os
import time

from asyncio import create_task
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import socketio

from fastapi import Depends, FastAPI
from fastapi_limiter import FastAPILimiter
from fastapi_pagination import add_pagination
from prometheus_client import make_asgi_app
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles
from starlette_context.middleware import ContextMiddleware
from starlette_context.plugins import RequestIdPlugin

from backend import __version__
from backend.common.exception.exception_handler import register_exception
from backend.common.log import set_custom_logfile, setup_logging
from backend.common.response.response_code import StandardResponseCode
from backend.core.conf import settings
from backend.core.path_conf import STATIC_DIR, UPLOAD_DIR
from backend.database.db import create_tables
from backend.database.redis import redis_client
from backend.middleware.access_middleware import AccessMiddleware
from backend.middleware.debug_middleware import DebugMiddleware
from backend.middleware.i18n_middleware import I18nMiddleware
from backend.middleware.jwt_auth_middleware import JwtAuthMiddleware
from backend.middleware.opera_log_middleware import OperaLogMiddleware
from backend.middleware.state_middleware import StateMiddleware
from backend.plugin.tools import build_final_router
from backend.utils.demo_site import demo_site
from backend.utils.health_check import ensure_unique_route_names, http_limit_callback
from backend.utils.openapi import simplify_operation_ids
from backend.utils.otel import init_otel
from backend.utils.serializers import MsgSpecJSONResponse
from backend.utils.snowflake import snowflake
from backend.utils.trace_id import OtelTraceIdPlugin

# ============= 启动性能监控工具 =============
def _debug_log(msg: str, duration: float = None):
    """输出调试日志"""
    try:
        if duration is not None:
            print(f"[Startup] {msg}: {duration:.3f}s", flush=True)
        else:
            print(f"[Startup] {msg}", flush=True)
    except UnicodeEncodeError:
        # 如果编码失败，使用 ASCII 安全模式
        msg_safe = msg.encode('ascii', errors='replace').decode('ascii')
        if duration is not None:
            print(f"[Startup] {msg_safe}: {duration:.3f}s", flush=True)
        else:
            print(f"[Startup] {msg_safe}", flush=True)


@asynccontextmanager
async def register_init(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    启动初始化

    :param app: FastAPI 应用实例
    :return:
    """
    _debug_log(">> Lifespan Init Started")
    _init_start = time.time()
    
    # 创建数据库表（仅在明确需要时执行）
    # NOTE: 生产环境应使用 Alembic migrations，不应依赖自动创建
    # 设置环境变量 AUTO_CREATE_TABLES=true 来启用（默认禁用）
    if os.getenv('AUTO_CREATE_TABLES', 'false').lower() == 'true':
        _step_start = time.time()
        _debug_log("  - Creating database tables...")
        await create_tables()
        _debug_log("    [OK] Database tables created", time.time() - _step_start)
    else:
        _debug_log("  - Skipping table creation (use Alembic migrations or set AUTO_CREATE_TABLES=true)")

    # 初始化 redis
    _step_start = time.time()
    _debug_log("  - Initializing Redis connection...")
    await redis_client.open()
    _debug_log("    [OK] Redis connected", time.time() - _step_start)

    # 同步插件配置到 Redis
    _step_start = time.time()
    _debug_log("  - Syncing plugin configs to Redis...")
    from backend.plugin.tools import sync_plugin_config_to_redis
    await sync_plugin_config_to_redis()
    _debug_log("    [OK] Plugin configs synced", time.time() - _step_start)

    # 初始化 limiter
    _step_start = time.time()
    _debug_log("  - Initializing rate limiter...")
    await FastAPILimiter.init(
        redis=redis_client,
        prefix=settings.REQUEST_LIMITER_REDIS_PREFIX,
        http_callback=http_limit_callback,
    )
    _debug_log("    [OK] Rate limiter initialized", time.time() - _step_start)

    # 初始化 snowflake 节点
    _step_start = time.time()
    _debug_log("  - Initializing Snowflake node...")
    await snowflake.init()
    _debug_log("    [OK] Snowflake node initialized", time.time() - _step_start)

    # 创建操作日志任务
    _step_start = time.time()
    _debug_log("  - Creating operation log task...")
    create_task(OperaLogMiddleware.consumer())
    _debug_log("    [OK] Operation log task created", time.time() - _step_start)

    _debug_log(">> Lifespan Init Completed", time.time() - _init_start)

    yield

    _debug_log(">> Lifespan Shutdown Started")
    # 释放 snowflake 节点
    await snowflake.shutdown()

    # 关闭 redis 连接
    await redis_client.aclose()
    _debug_log(">> Lifespan Shutdown Completed")


def register_app() -> FastAPI:
    """注册 FastAPI 应用"""
    _debug_log(">> FastAPI App Registration Started")
    _app_start = time.time()

    _step_start = time.time()
    _debug_log("  - Creating FastAPI instance...")
    app = FastAPI(
        title=settings.FASTAPI_TITLE,
        version=__version__,
        description=settings.FASTAPI_DESCRIPTION,
        docs_url=settings.FASTAPI_DOCS_URL,
        redoc_url=settings.FASTAPI_REDOC_URL,
        openapi_url=settings.FASTAPI_OPENAPI_URL,
        default_response_class=MsgSpecJSONResponse,
        lifespan=register_init,
    )
    _debug_log("    [OK] FastAPI instance created", time.time() - _step_start)

    # 注册组件
    _step_start = time.time()
    _debug_log("  - Registering logger...")
    register_logger()
    _debug_log("    [OK] Logger registered", time.time() - _step_start)

    _step_start = time.time()
    _debug_log("  - Registering Socket.IO...")
    register_socket_app(app)
    _debug_log("    [OK] Socket.IO registered", time.time() - _step_start)

    _step_start = time.time()
    _debug_log("  - Registering static files...")
    register_static_file(app)
    _debug_log("    [OK] Static files registered", time.time() - _step_start)

    _step_start = time.time()
    _debug_log("  - Registering middleware...")
    register_middleware(app)
    _debug_log("    [OK] Middleware registered", time.time() - _step_start)

    _step_start = time.time()
    _debug_log("  - Registering routes...")
    register_router(app)
    _debug_log("    [OK] Routes registered", time.time() - _step_start)

    _step_start = time.time()
    _debug_log("  - Registering pagination...")
    register_page(app)
    _debug_log("    [OK] Pagination registered", time.time() - _step_start)

    _step_start = time.time()
    _debug_log("  - Registering exception handlers...")
    register_exception(app)
    _debug_log("    [OK] Exception handlers registered", time.time() - _step_start)

    if settings.GRAFANA_METRICS:
        _step_start = time.time()
        _debug_log("  - Registering metrics...")
        register_metrics(app)
        _debug_log("    [OK] Metrics registered", time.time() - _step_start)

    _debug_log(">> FastAPI App Registration Completed", time.time() - _app_start)
    return app


def register_logger() -> None:
    """注册日志"""
    setup_logging()
    set_custom_logfile()


def register_static_file(app: FastAPI) -> None:
    """
    注册静态资源服务

    :param app: FastAPI 应用实例
    :return:
    """
    # 上传静态资源
    if not os.path.exists(UPLOAD_DIR):
        os.makedirs(UPLOAD_DIR)
    app.mount('/static/upload', StaticFiles(directory=UPLOAD_DIR), name='upload')

    # 固有静态资源
    if settings.FASTAPI_STATIC_FILES:
        app.mount('/static', StaticFiles(directory=STATIC_DIR), name='static')


def register_middleware(app: FastAPI) -> None:
    """
    注册中间件（执行顺序从下往上）

    :param app: FastAPI 应用实例
    :return:
    """
    # Debug（开发环境调试，只在 DEBUG 级别生效）
    app.add_middleware(DebugMiddleware)

    # Opera log
    app.add_middleware(OperaLogMiddleware)

    # State
    app.add_middleware(StateMiddleware)

    # JWT auth
    app.add_middleware(
        AuthenticationMiddleware,
        backend=JwtAuthMiddleware(),
        on_error=JwtAuthMiddleware.auth_exception_handler,
    )

    # I18n
    app.add_middleware(I18nMiddleware)

    # Access log
    app.add_middleware(AccessMiddleware)

    # ContextVar
    plugins = [OtelTraceIdPlugin()] if settings.GRAFANA_METRICS else [RequestIdPlugin(validate=True)]
    app.add_middleware(
        ContextMiddleware,
        plugins=plugins,
        default_error_response=MsgSpecJSONResponse(
            content={'code': StandardResponseCode.HTTP_400, 'msg': 'BAD_REQUEST', 'data': None},
            status_code=StandardResponseCode.HTTP_400,
        ),
    )

    # CORS
    # https://github.com/fastapi-practices/fastapi_best_architecture/pull/789/changes
    # https://github.com/open-telemetry/opentelemetry-python-contrib/issues/4031
    if settings.MIDDLEWARE_CORS:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.CORS_ALLOWED_ORIGINS,
            allow_credentials=True,
            allow_methods=['*'],
            allow_headers=['*'],
            expose_headers=settings.CORS_EXPOSE_HEADERS,
        )


def register_router(app: FastAPI) -> None:
    """
    注册路由

    :param app: FastAPI 应用实例
    :return:
    """
    dependencies = [Depends(demo_site)] if settings.DEMO_MODE else None

    # API
    _step_start = time.time()
    _debug_log("    - Building router...")
    router = build_final_router()
    _debug_log("      [OK] Router built", time.time() - _step_start)
    
    _step_start = time.time()
    _debug_log("    - Including router...")
    app.include_router(router, dependencies=dependencies)
    _debug_log("      [OK] Router included", time.time() - _step_start)

    # Extra
    _step_start = time.time()
    _debug_log("    - Ensuring unique route names...")
    ensure_unique_route_names(app)
    _debug_log("      [OK] Route names validated", time.time() - _step_start)
    
    _step_start = time.time()
    _debug_log("    - Simplifying operation IDs...")
    simplify_operation_ids(app)
    _debug_log("      [OK] Operation IDs simplified", time.time() - _step_start)


def register_page(app: FastAPI) -> None:
    """
    注册分页查询功能

    :param app: FastAPI 应用实例
    :return:
    """
    add_pagination(app)


def register_socket_app(app: FastAPI) -> None:
    """
    注册 Socket.IO 应用

    :param app: FastAPI 应用实例
    :return:
    """
    from backend.common.socketio.server import sio

    socket_app = socketio.ASGIApp(
        socketio_server=sio,
        other_asgi_app=app,
        # 切勿删除此配置：https://github.com/pyropy/fastapi-socketio/issues/51
        socketio_path='/ws/socket.io',
    )
    app.mount('/ws', socket_app)


def register_metrics(app: FastAPI) -> None:
    """
    注册指标

    :param app: FastAPI 应用实例
    :return:
    """
    metrics_app = make_asgi_app()
    app.mount('/metrics', metrics_app)

    init_otel(app)
