import json
import uuid

from datetime import timedelta
from typing import Any

from fastapi import Depends, Request
from fastapi.security import HTTPBearer
from fastapi.security.utils import get_authorization_scheme_param
from jose import ExpiredSignatureError, JWTError, jwt
from pydantic_core import from_json
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.admin.model import User
from backend.app.admin.schema.user import GetUserInfoWithRelationDetail
from backend.common.dataclasses import AccessToken, NewToken, RefreshToken, TokenPayload
from backend.common.exception import errors
from backend.common.log import log
from backend.core.conf import settings
from backend.database.db import async_db_session
from backend.database.redis import redis_client
from backend.utils.timezone import timezone

# JWT dependency injection
DependsJwtAuth = Depends(HTTPBearer())


def jwt_encode(payload: dict[str, Any]) -> str:
    """
    生成 JWT token

    :param payload: 载荷
    :return:
    """
    return jwt.encode(payload, settings.TOKEN_SECRET_KEY, settings.TOKEN_ALGORITHM)


def jwt_decode(token: str) -> TokenPayload:
    """
    解析 JWT token

    :param token: JWT token
    :return:
    """
    try:
        payload = jwt.decode(
            token,
            settings.TOKEN_SECRET_KEY,
            algorithms=[settings.TOKEN_ALGORITHM],
            options={"verify_exp": True},
        )
        session_uuid = payload.get("session_uuid")
        user_id = payload.get("sub")
        expire = payload.get("exp")
        if not session_uuid or not user_id or not expire:
            raise errors.TokenError(msg="Token 无效")
    except ExpiredSignatureError:
        raise errors.TokenError(msg="Token 已过期")
    except (JWTError, Exception):
        raise errors.TokenError(msg="Token 无效")
    return TokenPayload(
        id=int(user_id),
        session_uuid=session_uuid,
        expire_time=timezone.from_datetime(timezone.to_utc(expire)),
    )


async def create_access_token(user_id: int, *, multi_login: bool, **kwargs) -> AccessToken:
    """
    生成加密 token

    :param user_id: 用户 ID
    :param multi_login: 是否允许多端登录
    :param kwargs: token 额外信息
    :return:
    """
    expire = timezone.now() + timedelta(seconds=settings.TOKEN_EXPIRE_SECONDS)
    session_uuid = str(uuid.uuid4())
    access_token = jwt_encode(
        {
            "session_uuid": session_uuid,
            "exp": timezone.to_utc(expire).timestamp(),
            "sub": str(user_id),
        }
    )

    if not multi_login:
        await redis_client.delete_prefix(f"{settings.TOKEN_REDIS_PREFIX}:{user_id}")

    await redis_client.setex(
        f"{settings.TOKEN_REDIS_PREFIX}:{user_id}:{session_uuid}",
        settings.TOKEN_EXPIRE_SECONDS,
        access_token,
    )

    # Token 附加信息单独存储
    if kwargs:
        await redis_client.setex(
            f"{settings.TOKEN_EXTRA_INFO_REDIS_PREFIX}:{user_id}:{session_uuid}",
            settings.TOKEN_EXPIRE_SECONDS,
            json.dumps(kwargs, ensure_ascii=False),
        )

    return AccessToken(access_token=access_token, access_token_expire_time=expire, session_uuid=session_uuid)


async def create_refresh_token(session_uuid: str, user_id: int, *, multi_login: bool) -> RefreshToken:
    """
    生成加密刷新 token，仅用于创建新的 token

    :param session_uuid: 会话 UUID
    :param user_id: 用户 ID
    :param multi_login: 是否允许多端登录
    :return:
    """
    expire = timezone.now() + timedelta(seconds=settings.TOKEN_REFRESH_EXPIRE_SECONDS)
    refresh_token = jwt_encode(
        {
            "session_uuid": session_uuid,
            "exp": timezone.to_utc(expire).timestamp(),
            "sub": str(user_id),
        }
    )

    if not multi_login:
        await redis_client.delete_prefix(f"{settings.TOKEN_REFRESH_REDIS_PREFIX}:{user_id}")

    await redis_client.setex(
        f"{settings.TOKEN_REFRESH_REDIS_PREFIX}:{user_id}:{session_uuid}",
        settings.TOKEN_REFRESH_EXPIRE_SECONDS,
        refresh_token,
    )
    return RefreshToken(refresh_token=refresh_token, refresh_token_expire_time=expire)


async def create_new_token(
    refresh_token: str,
    session_uuid: str,
    user_id: int,
    *,
    multi_login: bool,
    **kwargs,
) -> NewToken:
    """
    生成新的 token

    :param refresh_token: 刷新 token
    :param session_uuid: 会话 UUID
    :param user_id: 用户 ID
    :param multi_login: 是否允许多端登录
    :param kwargs: token 附加信息
    :return:
    """
    redis_refresh_token = await redis_client.get(f"{settings.TOKEN_REFRESH_REDIS_PREFIX}:{user_id}:{session_uuid}")
    if not redis_refresh_token or redis_refresh_token != refresh_token:
        raise errors.TokenError(msg="Refresh Token 已过期，请重新登录")

    await redis_client.delete(f"{settings.TOKEN_REFRESH_REDIS_PREFIX}:{user_id}:{session_uuid}")
    await redis_client.delete(f"{settings.TOKEN_REDIS_PREFIX}:{user_id}:{session_uuid}")

    new_access_token = await create_access_token(user_id, multi_login=multi_login, **kwargs)
    new_refresh_token = await create_refresh_token(new_access_token.session_uuid, user_id, multi_login=multi_login)
    return NewToken(
        new_access_token=new_access_token.access_token,
        new_access_token_expire_time=new_access_token.access_token_expire_time,
        new_refresh_token=new_refresh_token.refresh_token,
        new_refresh_token_expire_time=new_refresh_token.refresh_token_expire_time,
        session_uuid=new_access_token.session_uuid,
    )


async def revoke_token(user_id: int, session_uuid: str) -> None:
    """
    撤销 token

    :param user_id: 用户 ID
    :param session_uuid: 会话 ID
    :return:
    """
    await redis_client.delete(f"{settings.TOKEN_REDIS_PREFIX}:{user_id}:{session_uuid}")
    await redis_client.delete(f"{settings.TOKEN_EXTRA_INFO_REDIS_PREFIX}:{user_id}:{session_uuid}")


def get_token(request: Request) -> str:
    """
    获取请求头中的 token

    :param request: FastAPI 请求对象
    :return:
    """
    authorization = request.headers.get("Authorization")
    scheme, token = get_authorization_scheme_param(authorization)
    if not authorization or scheme.lower() != "bearer":
        raise errors.TokenError(msg="Token 无效")
    return token


async def get_current_user(db: AsyncSession, pk: int) -> User:
    """
    获取当前用户

    :param db: 数据库会话
    :param pk: 用户 ID
    :return:
    """

    from backend.app.admin.crud.crud_user import user_dao
    from backend.app.admin.crud.user_tenant_helper import get_user_primary_tenant_id

    user_result = await user_dao.get_join(db, user_id=pk)
    if not user_result:
        raise errors.TokenError(msg="Token 无效")
    if not user_result.status:
        raise errors.AuthorizationError(msg="用户已被锁定，请联系系统管理员")
    if user_result.dept_id:
        if not user_result.dept:
            log.error(f"User {user_result.id} has dept_id {user_result.dept_id} but dept object is None")
            raise errors.AuthorizationError(msg="用户所属部门数据异常，请联系系统管理员")
        if not user_result.dept.status:
            raise errors.AuthorizationError(msg="用户所属部门已被锁定，请联系系统管理员")
        if user_result.dept.del_flag:
            raise errors.AuthorizationError(msg="用户所属部门已被删除，请联系系统管理员")
    if user_result.roles:
        role_status = [role.status for role in user_result.roles]
        if all(status == 0 for status in role_status):
            raise errors.AuthorizationError(msg="用户所属角色已被锁定，请联系系统管理员")

    tenant_id = await get_user_primary_tenant_id(db, pk)

    user_dict = user_result._asdict()
    user_dict["tenant_id"] = tenant_id

    from collections import namedtuple

    UserWithTenant = namedtuple("Result", list(user_dict.keys()))  # noqa: PYI024
    user = UserWithTenant(**user_dict)

    return user


def superuser_verify(request: Request, _token: str = DependsJwtAuth) -> bool:
    """
    验证当前用户超级管理员权限

    :param request: FastAPI 请求对象
    :param _token: JWT 令牌
    :return:
    """
    superuser = request.user.is_superuser
    if not superuser or not request.user.is_staff:
        raise errors.AuthorizationError
    return superuser


async def jwt_authentication(token: str) -> GetUserInfoWithRelationDetail:
    """
    JWT 认证

    :param token: JWT token
    :return:
    """
    token_payload = jwt_decode(token)
    user_id = token_payload.id
    redis_token = await redis_client.get(f"{settings.TOKEN_REDIS_PREFIX}:{user_id}:{token_payload.session_uuid}")
    if not redis_token:
        raise errors.TokenError(msg="Token 已过期")

    if token != redis_token:
        raise errors.TokenError(msg="Token 已失效")

    cache_user = await redis_client.get(f"{settings.JWT_USER_REDIS_PREFIX}:{user_id}")
    if not cache_user:
        async with async_db_session() as db:
            current_user = await get_current_user(db, user_id)
            user = GetUserInfoWithRelationDetail.model_validate(current_user)
            await redis_client.setex(
                f"{settings.JWT_USER_REDIS_PREFIX}:{user_id}",
                settings.TOKEN_EXPIRE_SECONDS,
                user.model_dump_json(),
            )
    else:
        # TODO: 在恰当的时机，应替换为使用 model_validate_json
        # https://docs.pydantic.dev/latest/concepts/json/#partial-json-parsing
        user = GetUserInfoWithRelationDetail.model_validate(from_json(cache_user, allow_partial=True))

        if not user.tenant_id:
            from backend.app.admin.crud.user_tenant_helper import get_user_primary_tenant_id

            async with async_db_session() as db:
                user.tenant_id = await get_user_primary_tenant_id(db, user_id)

    return user


def get_current_tenant_id() -> str:
    """
    从上下文获取当前租户 ID

    在 JWT 认证成功后，tenant_id 会自动注入到 ctx
    用于多租户数据隔离

    :return: 租户 ID
    :raises: AuthorizationError 如果租户信息缺失
    """
    from backend.common.context import ctx

    tenant_id = ctx.tenant_id
    if not tenant_id:
        raise errors.AuthorizationError(msg="租户信息缺失")
    return tenant_id


# 租户 ID 依赖注入
CurrentTenantId = Depends(get_current_tenant_id)

# 超级管理员鉴权依赖注入
DependsSuperUser = Depends(superuser_verify)


def get_current_user_id() -> int:
    """
    从上下文获取当前用户 ID

    在 JWT 认证成功后，user_id 会自动注入到 ctx
    用于获取当前操作用户

    :return: 用户 ID
    :raises: AuthorizationError 如果用户信息缺失
    """
    from backend.common.context import ctx

    user_id = ctx.user_id
    if not user_id:
        raise errors.AuthorizationError(msg="用户信息缺失")
    return user_id


# 当前用户 ID 依赖注入
CurrentUserId = Depends(get_current_user_id)


def get_current_user_obj(request: Request) -> GetUserInfoWithRelationDetail:
    """
    获取当前通过中间件认证的用户对象
    """
    user = request.user
    # Starlette 在未登录时会注入 UnauthenticatedUser，需要显式拦截
    if not user or getattr(user, "is_authenticated", True) is False:
        raise errors.TokenError(msg="未登录或 Token 已过期")
    return user


# 用户对象依赖注入
CurrentUser = Depends(get_current_user_obj)
