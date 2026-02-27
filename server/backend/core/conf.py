import os
from functools import lru_cache
from re import Pattern
from typing import Any, Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from backend.core.path_conf import BASE_PATH


class Settings(BaseSettings):
    """全局配置"""

    model_config = SettingsConfigDict(
        env_file=os.getenv("ENV_FILE", f"{BASE_PATH}/.env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )

    # .env 当前环境
    ENVIRONMENT: Literal["dev", "prod"]

    # FastAPI
    FASTAPI_API_V1_PATH: str = "/api/v1"
    FASTAPI_TITLE: str = "fba"
    FASTAPI_DESCRIPTION: str = "FastAPI Best Architecture"
    FASTAPI_DOCS_URL: str = "/docs"
    FASTAPI_REDOC_URL: str = "/redoc"
    FASTAPI_OPENAPI_URL: str | None = "/openapi"
    FASTAPI_STATIC_FILES: bool = True

    # .env 数据库
    DATABASE_TYPE: Literal["mysql", "postgresql"]
    DATABASE_HOST: str
    DATABASE_PORT: int
    DATABASE_USER: str
    DATABASE_PASSWORD: str

    # 数据库
    DATABASE_ECHO: bool | Literal["debug"] = False
    DATABASE_POOL_ECHO: bool | Literal["debug"] = False
    DATABASE_SCHEMA: str = "fba"
    DATABASE_CHARSET: str = "utf8mb4"
    DATABASE_PK_MODE: Literal["autoincrement", "snowflake"] = "autoincrement"

    # .env Redis
    # 优先使用 REDIS_URL（完整连接字符串，例如 Upstash 提供的 rediss://... 格式）
    # 如果没有设置 REDIS_URL，则使用以下独立参数
    REDIS_URL: str | None = None
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_USERNAME: str | None = None
    REDIS_PASSWORD: str = ""
    REDIS_DATABASE: int = 0

    # Redis
    REDIS_TIMEOUT: int = 5

    # .env Snowflake
    SNOWFLAKE_DATACENTER_ID: int | None = None
    SNOWFLAKE_WORKER_ID: int | None = None

    # Snowflake
    SNOWFLAKE_REDIS_PREFIX: str = "fba:snowflake"
    SNOWFLAKE_HEARTBEAT_INTERVAL_SECONDS: int = 30
    SNOWFLAKE_NODE_TTL_SECONDS: int = 60

    # .env Token
    TOKEN_SECRET_KEY: str  # 密钥 secrets.token_urlsafe(32)

    # Token
    TOKEN_ALGORITHM: str = "HS256"
    TOKEN_EXPIRE_SECONDS: int = 60 * 60 * 24  # 1 天
    TOKEN_REFRESH_EXPIRE_SECONDS: int = 60 * 60 * 24 * 7  # 7 天
    TOKEN_REDIS_PREFIX: str = "fba:token"
    TOKEN_EXTRA_INFO_REDIS_PREFIX: str = "fba:token_extra_info"
    TOKEN_ONLINE_REDIS_PREFIX: str = "fba:token_online"
    TOKEN_REFRESH_REDIS_PREFIX: str = "fba:refresh_token"
    TOKEN_REQUEST_PATH_EXCLUDE: list[str] = [  # JWT / RBAC 路由白名单
        f"{FASTAPI_API_V1_PATH}/auth/login",
        f"{FASTAPI_API_V1_PATH}/app/landing/trial-application",  # Landing page 试用申请
    ]
    TOKEN_REQUEST_PATH_EXCLUDE_PATTERN: list[Pattern[str]] = [  # JWT / RBAC 路由白名单（正则）
        rf"^{FASTAPI_API_V1_PATH}/monitors/(redis|server)$",
    ]

    # 用户安全
    USER_LOCK_REDIS_PREFIX: str = "fba:user:lock"
    USER_LOCK_THRESHOLD: int = 5  # 用户密码错误锁定阈值，0 表示禁用锁定
    USER_LOCK_SECONDS: int = 60 * 5  # 5 分钟
    USER_PASSWORD_EXPIRY_DAYS: int = 365  # 用户密码有效期，0 表示永不过期
    USER_PASSWORD_REMINDER_DAYS: int = 7  # 用户密码到期提醒，0 表示不提醒
    USER_PASSWORD_HISTORY_CHECK_COUNT: int = 3
    USER_PASSWORD_MIN_LENGTH: int = 6
    USER_PASSWORD_MAX_LENGTH: int = 32
    USER_PASSWORD_REQUIRE_SPECIAL_CHAR: bool = False

    # 登录
    LOGIN_CAPTCHA_ENABLED: bool = False
    LOGIN_CAPTCHA_REDIS_PREFIX: str = "fba:login:captcha"
    LOGIN_CAPTCHA_EXPIRE_SECONDS: int = 60 * 5  # 5 分钟
    LOGIN_FAILURE_PREFIX: str = "fba:login:failure"

    # JWT
    JWT_USER_REDIS_PREFIX: str = "fba:user"

    # RBAC
    RBAC_ROLE_MENU_MODE: bool = True
    RBAC_ROLE_MENU_EXCLUDE: list[str] = [
        "sys:monitor:redis",
        "sys:monitor:server",
    ]

    # Cookie
    COOKIE_REFRESH_TOKEN_KEY: str = "fba_refresh_token"
    COOKIE_REFRESH_TOKEN_EXPIRE_SECONDS: int = 60 * 60 * 24 * 7  # 7 天

    # 数据权限
    DATA_PERMISSION_COLUMN_EXCLUDE: list[str] = [  # 排除允许进行数据过滤的 SQLA 模型列
        "id",
        "sort",
        "del_flag",
        "created_time",
        "updated_time",
    ]

    # Socket.IO
    WS_NO_AUTH_MARKER: str = "internal"

    # CORS
    CORS_ALLOWED_ORIGINS: list[str] = [  # 末尾不带斜杠
        "http://127.0.0.1:8000",
        "http://localhost:5173",
    ]
    CORS_EXPOSE_HEADERS: list[str] = [
        "X-Request-ID",
    ]

    # 中间件配置
    MIDDLEWARE_CORS: bool = True

    # 请求限制配置
    REQUEST_LIMITER_REDIS_PREFIX: str = "fba:limiter"

    # 时间配置
    DATETIME_TIMEZONE: str = "Asia/Shanghai"
    DATETIME_FORMAT: str = "%Y-%m-%d %H:%M:%S"

    # 文件上传
    UPLOAD_READ_SIZE: int = 1024
    UPLOAD_IMAGE_EXT_INCLUDE: list[str] = ["jpg", "jpeg", "png", "gif", "webp"]
    UPLOAD_IMAGE_SIZE_MAX: int = 5 * 1024 * 1024  # 5 MB
    UPLOAD_VIDEO_EXT_INCLUDE: list[str] = ["mp4", "mov", "avi", "flv"]
    UPLOAD_VIDEO_SIZE_MAX: int = 20 * 1024 * 1024  # 20 MB

    # .env 对象存储配置
    STORAGE_TYPE: Literal["local", "aliyun_oss", "tencent_cos", "aws_s3"] = "local"

    # 本地存储（默认）
    STORAGE_LOCAL_BASE_URL: str = "/static/upload"

    # 阿里云 OSS
    ALIYUN_OSS_ACCESS_KEY_ID: str = ""
    ALIYUN_OSS_ACCESS_KEY_SECRET: str = ""
    ALIYUN_OSS_ENDPOINT: str = ""  # 如：oss-cn-hangzhou.aliyuncs.com
    ALIYUN_OSS_BUCKET_NAME: str = ""
    ALIYUN_OSS_BASE_PATH: str = ""  # 存储根路径，如：userecho
    ALIYUN_OSS_CDN_DOMAIN: str = ""  # CDN 加速域名（可选）

    # 腾讯云 COS
    TENCENT_COS_SECRET_ID: str = ""
    TENCENT_COS_SECRET_KEY: str = ""
    TENCENT_COS_REGION: str = ""  # 如：ap-guangzhou
    TENCENT_COS_BUCKET_NAME: str = ""
    TENCENT_COS_BASE_PATH: str = ""
    TENCENT_COS_CDN_DOMAIN: str = ""

    # AWS S3
    AWS_S3_ACCESS_KEY_ID: str = ""
    AWS_S3_SECRET_ACCESS_KEY: str = ""
    AWS_S3_REGION: str = ""  # 如：us-east-1
    AWS_S3_BUCKET_NAME: str = ""
    AWS_S3_BASE_PATH: str = ""
    AWS_S3_CDN_DOMAIN: str = ""  # CloudFront 域名（可选）

    # 演示模式配置
    DEMO_MODE: bool = False
    # 注意：Demo 模式现在默认允许所有操作，只拦截危险操作（删除预置用户、删除租户等）
    # 这样用户可以完整体验所有功能，数据会每日自动重置
    ALLOW_REGISTRATION: bool = True  # Demo 模式下设为 False

    # Cloudflare Turnstile 人机验证
    TURNSTILE_ENABLED: bool = False
    TURNSTILE_SECRET_KEY: str = ""

    # Demo 数据重置
    DEMO_DATA_RESET_ENABLED: bool = False
    DEMO_DATA_RESET_CRON: str = "0 2 * * *"  # 每日凌晨 2 点

    # IP 定位配置
    IP_LOCATION_PARSE: Literal["online", "offline", "false"] = "offline"
    IP_LOCATION_REDIS_PREFIX: str = "fba:ip:location"
    IP_LOCATION_EXPIRE_SECONDS: int = 60 * 60 * 24  # 1 天

    # Trace ID
    TRACE_ID_REQUEST_HEADER_KEY: str = "X-Request-ID"
    TRACE_ID_LOG_LENGTH: int = 32  # UUID 长度，必须小于等于 32
    TRACE_ID_LOG_DEFAULT_VALUE: str = "-"

    # 日志
    LOG_FORMAT: str = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</> | <lvl>{level: <8}</> | <cyan>{request_id}</> | <lvl>{message}</>"
    )

    # 日志（控制台）
    LOG_STD_LEVEL: str = "DEBUG"

    # 日志（文件）
    LOG_FILE_ACCESS_LEVEL: str = "INFO"
    LOG_FILE_ERROR_LEVEL: str = "ERROR"
    LOG_ACCESS_FILENAME: str = "fba_access.log"
    LOG_ERROR_FILENAME: str = "fba_error.log"

    # .env 操作日志
    OPERA_LOG_ENCRYPT_SECRET_KEY: str  # 密钥 os.urandom(32), 需使用 bytes.hex() 方法转换为 str

    # 操作日志
    OPERA_LOG_PATH_EXCLUDE: list[str] = [
        "/favicon.ico",
        "/docs",
        "/redoc",
        "/openapi",
        f"{FASTAPI_API_V1_PATH}/auth/login/swagger",
        f"{FASTAPI_API_V1_PATH}/oauth2/github/callback",
        f"{FASTAPI_API_V1_PATH}/oauth2/google/callback",
        f"{FASTAPI_API_V1_PATH}/oauth2/linux-do/callback",
    ]
    OPERA_LOG_ENCRYPT_TYPE: int = 1  # 0: AES (性能损耗); 1: md5; 2: ItsDangerous; 3: 不加密, others: 替换为 ******
    OPERA_LOG_ENCRYPT_KEY_INCLUDE: list[str] = [  # 将加密接口入参参数对应的值
        "password",
        "old_password",
        "new_password",
        "confirm_password",
    ]
    OPERA_LOG_QUEUE_BATCH_CONSUME_SIZE: int = 100
    OPERA_LOG_QUEUE_TIMEOUT: int = 60  # 1 分钟

    # Plugin 配置
    PLUGIN_PIP_CHINA: bool = True
    PLUGIN_PIP_INDEX_URL: str = "https://mirrors.aliyun.com/pypi/simple/"
    PLUGIN_PIP_MAX_RETRY: int = 3
    PLUGIN_REDIS_PREFIX: str = "fba:plugin"

    # I18n 配置
    I18N_DEFAULT_LANGUAGE: str = "zh-CN"

    # Grafana
    GRAFANA_METRICS: bool = False
    GRAFANA_APP_NAME: str = "fba_server"
    GRAFANA_OTLP_GRPC_ENDPOINT: str = "fba_alloy:4317"

    ##################################################
    # [ App ] UserEcho
    ##################################################
    # .env AI 配置
    DEEPSEEK_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    GLM_API_KEY: str = ""  # 智谱 AI
    VOLCENGINE_API_KEY: str = ""  # 火山引擎（豆包）

    # AI 配置
    AI_DEFAULT_PROVIDER: str = "deepseek"

    # 火山引擎 Endpoint ID（必须配置）
    VOLCENGINE_EMBEDDING_ENDPOINT: str = ""  # embedding endpoint ID，如：ep-20241221xxx-xxxxx
    VOLCENGINE_CHAT_ENDPOINT: str = ""  # chat endpoint ID，如：ep-20241221xxx-xxxxx
    VOLCENGINE_VISION_ENDPOINT: str = ""  # vision endpoint ID（可选，不配置则使用 CHAT_ENDPOINT）

    # 聚类配置
    CLUSTERING_SIMILARITY_THRESHOLD: float = 0.85  # 相似度阈值（0.75太宽松，改为0.85更严格）
    CLUSTERING_MIN_SAMPLES: int = 2  # 最小聚类大小（至少2条相似反馈才能形成聚类）
    CLUSTERING_MIN_SILHOUETTE: float = 0.3  # 最低轮廓系数（越高越好）0.0=测试阶段放开，生产建议 0.3
    CLUSTERING_MAX_NOISE_RATIO: float = 0.5  # 最高噪声率（越低越好）1.0=测试阶段放开，生产建议 0.5

    # 导入配置
    IMPORT_MAX_FILE_SIZE: int = 10485760  # 10MB
    IMPORT_ALLOWED_EXTENSIONS: list[str] = [".xlsx", ".xls", ".csv"]

    ##################################################
    # [ App ] task
    ##################################################
    # .env Redis
    CELERY_BROKER_REDIS_DATABASE: int = 1

    # .env Celery Broker (仅支持 Redis)
    CELERY_BROKER: Literal["redis"] = "redis"
    CELERY_REDIS_PREFIX: str = "fba:celery"
    CELERY_TASK_MAX_RETRIES: int = 5

    ##################################################
    # [ Plugin ] code_generator
    ##################################################
    CODE_GENERATOR_DOWNLOAD_ZIP_FILENAME: str = "fba_generator"

    ##################################################
    # [ Plugin ] oauth2
    ##################################################
    # .env
    OAUTH2_GITHUB_CLIENT_ID: str = ""
    OAUTH2_GITHUB_CLIENT_SECRET: str = ""
    OAUTH2_GOOGLE_CLIENT_ID: str = ""
    OAUTH2_GOOGLE_CLIENT_SECRET: str = ""
    OAUTH2_LINUX_DO_CLIENT_ID: str = ""
    OAUTH2_LINUX_DO_CLIENT_SECRET: str = ""

    # 基础配置
    OAUTH2_STATE_REDIS_PREFIX: str = "fba:oauth2:state"
    OAUTH2_STATE_EXPIRE_SECONDS: int = 60 * 3  # 3 分钟
    OAUTH2_GITHUB_REDIRECT_URI: str = "http://127.0.0.1:8000/api/v1/oauth2/github/callback"
    OAUTH2_GOOGLE_REDIRECT_URI: str = "http://127.0.0.1:8000/api/v1/oauth2/google/callback"
    OAUTH2_LINUX_DO_REDIRECT_URI: str = "http://127.0.0.1:8000/api/v1/oauth2/linux-do/callback"
    OAUTH2_FRONTEND_LOGIN_REDIRECT_URI: str = "http://localhost:5173/oauth2/callback"
    OAUTH2_FRONTEND_BINDING_REDIRECT_URI: str = "http://localhost:5173/profile"

    ##################################################
    # [ Plugin ] email
    ##################################################
    # .env
    EMAIL_USERNAME: str = ""
    EMAIL_PASSWORD: str = ""

    # 基础配置
    EMAIL_HOST: str = "smtp.qq.com"
    EMAIL_PORT: int = 465
    EMAIL_SSL: bool = True
    EMAIL_CAPTCHA_REDIS_PREFIX: str = "fba:email:captcha"
    EMAIL_CAPTCHA_EXPIRE_SECONDS: int = 60 * 3  # 3 分钟

    # 前端 URL（用于生成邮件中的验证链接）
    FRONTEND_URL: str = "http://localhost:5173"

    # 后端 URL（用于生成 API 链接，如二维码）
    BACKEND_URL: str = "http://127.0.0.1:8000"

    @model_validator(mode="before")
    @classmethod
    def check_env(cls, values: Any) -> Any:
        """检查环境变量"""
        # Demo 模式下修改应用标题
        if values.get("DEMO_MODE"):
            values["FASTAPI_TITLE"] = "回响-演示版"
            values["FASTAPI_DESCRIPTION"] = "回响 - AI 驱动的用户反馈智能分析平台（演示环境）"

        return values


@lru_cache
def get_settings() -> Settings:
    """获取全局配置单例"""
    return Settings()  # type: ignore[call-arg]


# 创建全局配置实例
settings = get_settings()
