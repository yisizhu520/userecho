from fastapi import Request

from backend.common.exception import errors
from backend.core.conf import settings


async def demo_site(request: Request) -> None:  # noqa: RUF029
    """
    演示站点保护中间件

    Demo 模式设计原则：
    1. 允许用户完整体验所有核心功能（创建反馈、触发 AI、生成洞察等）
    2. 只拦截真正危险的操作（删除预置用户、修改系统配置等）
    3. 数据每日自动重置，无需担心用户"搞坏"数据

    :param request: FastAPI 请求对象
    :return:
    """
    if not settings.DEMO_MODE:
        return

    method = request.method
    path = request.url.path

    # Demo 模式下禁止的危险操作
    forbidden_patterns = [
        # 禁止删除 Demo 预置用户
        (
            lambda m, p: m == "DELETE"
            and "/api/v1/sys/user/" in p
            and any(u in p for u in ["demo_po", "demo_ops", "demo_admin"])
        ),
        # 禁止删除默认租户
        (lambda m, p: m == "DELETE" and "/api/v1/tenant/default-tenant" in p),
        # 禁止修改系统级配置（如果有的话）
        (lambda m, p: m in ["PUT", "PATCH", "DELETE"] and "/api/v1/config/system" in p),
    ]

    for pattern in forbidden_patterns:
        if pattern(method, path):
            raise errors.ForbiddenError(msg="演示环境下禁止删除预置数据或修改系统配置")
