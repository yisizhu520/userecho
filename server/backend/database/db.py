import sys

from collections.abc import AsyncGenerator
from typing import Annotated
from uuid import uuid4

from fastapi import Depends
from sqlalchemy import URL
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from backend.common.enums import DataBaseType
from backend.common.log import log
from backend.common.model import MappedBase
from backend.core.conf import settings


def create_database_url(*, unittest: bool = False) -> URL:
    """
    创建数据库链接

    :param unittest: 是否用于单元测试
    :return:
    """
    url = URL.create(
        drivername="mysql+asyncmy" if DataBaseType.mysql == settings.DATABASE_TYPE else "postgresql+asyncpg",
        username=settings.DATABASE_USER,
        password=settings.DATABASE_PASSWORD,
        host=settings.DATABASE_HOST,
        port=settings.DATABASE_PORT,
        database=settings.DATABASE_SCHEMA if not unittest else f"{settings.DATABASE_SCHEMA}_test",
    )
    if DataBaseType.mysql == settings.DATABASE_TYPE:
        url.update_query_dict({"charset": settings.DATABASE_CHARSET})
    return url


def create_async_engine_and_session(url: str | URL) -> tuple[AsyncEngine, async_sessionmaker[AsyncSession]]:
    """
    创建数据库引擎和 Session

    :param url: 数据库连接 URL
    :return:
    """
    try:
        log.info(f"[DB Engine] Creating async engine with URL: {url}")
        # 数据库引擎
        engine = create_async_engine(
            url,
            echo=settings.DATABASE_ECHO,
            echo_pool=settings.DATABASE_POOL_ECHO,
            future=True,
            # 中等并发
            pool_size=10,  # 低：- 高：+
            max_overflow=20,  # 低：- 高：+
            pool_timeout=30,  # 低：+ 高：-
            pool_recycle=3600,  # 低：+ 高：-
            pool_pre_ping=True,  # 低：False 高：True
            pool_use_lifo=False,  # 低：False 高：True
        )
        log.info("[DB Engine] Async engine created successfully")
    except Exception as e:
        log.error("❌ 数据库链接失败 {}", e)
        sys.exit()
    else:
        db_session = async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            autoflush=False,  # 禁用自动刷新
            expire_on_commit=True,  # ✅ 提交后自动过期对象，避免 StaleDataError
        )
        return engine, db_session


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    获取数据库会话（自动提交事务）

    - 请求成功：自动 commit()
    - 抛出异常：自动 rollback()

    这是默认的依赖注入方式，适用于99.9%的场景
    """
    from backend.common.log import log

    log.debug("[DB] get_db() called, starting transaction...")
    try:
        async with async_db_session.begin() as session:
            log.debug(f"[DB] Transaction started, in_transaction={session.in_transaction()}")
            try:
                yield session
                log.debug("[DB] Yielded session, will auto-commit on exit")
            except Exception as e:
                log.error(f"[DB] Exception during request: {e}")
                raise
        log.debug("[DB] Transaction committed (context manager exited)")
    except Exception as e:
        import traceback

        log.error(f"[DB] ❌ CRITICAL: Transaction commit FAILED: {e}")
        log.error(f"[DB] Traceback: {traceback.format_exc()}")
        raise
    finally:
        log.debug("[DB] get_db() exiting")


async def get_db_no_transaction() -> AsyncGenerator[AsyncSession, None]:
    """
    获取数据库会话（不自动提交，用于只读操作或手动控制事务）

    注意：大部分情况下不需要使用这个，除非有特殊需求
    """
    async with async_db_session() as session:
        yield session


async def create_tables() -> None:
    """创建数据库表"""
    async with async_engine.begin() as coon:
        await coon.run_sync(MappedBase.metadata.create_all)


async def drop_tables() -> None:
    """丢弃数据库表"""
    async with async_engine.begin() as conn:
        await conn.run_sync(MappedBase.metadata.drop_all)


def uuid4_str() -> str:
    """数据库引擎 UUID 类型兼容性解决方案"""
    return str(uuid4())


# SQLA 数据库链接
SQLALCHEMY_DATABASE_URL = create_database_url()

# SALA 异步引擎和会话
async_engine, async_db_session = create_async_engine_and_session(SQLALCHEMY_DATABASE_URL)

# Session Annotated
CurrentSession = Annotated[AsyncSession, Depends(get_db)]  # ✅ 自动提交/回滚
CurrentSessionNoTransaction = Annotated[AsyncSession, Depends(get_db_no_transaction)]  # 只读或手动控制

# 向后兼容：保留旧名称作为别名
CurrentSessionTransaction = CurrentSession  # ✅ 现在和 CurrentSession 一样，都自动提交
