"""演示模式专用 API"""

from fastapi import APIRouter, HTTPException, Response
from starlette.background import BackgroundTasks

from backend.app.admin.schema.user import AuthLoginParam
from backend.app.admin.service.auth_service import auth_service
from backend.common.response.response_schema import response_base
from backend.common.security.depends import DependsTurnstile
from backend.core.conf import settings
from backend.database.db import CurrentSessionTransaction

router = APIRouter(prefix='/demo', tags=['演示模式'])

# 预置角色映射（3 角色方案）
DEMO_ROLES = {
    'product_owner': {
        'username': 'demo_po',
        'name': '产品负责人',
        'description': '查看优先级看板、AI 洞察、审批议题',
        'icon': 'Target',
    },
    'user_ops': {
        'username': 'demo_ops',
        'name': '用户运营',
        'description': '录入反馈、管理客户、触发聚类',
        'icon': 'Headphones',
    },
    'admin': {
        'username': 'demo_admin',
        'name': '系统管理员',
        'description': '用户管理、权限配置、看板设置',
        'icon': 'Settings',
    },
}

# Demo 统一密码
DEMO_PASSWORD = 'demo123456'


@router.get('/roles', summary='获取可切换的角色列表')
async def get_demo_roles():
    """获取 Demo 模式下可切换的角色"""
    if not settings.DEMO_MODE:
        raise HTTPException(status_code=404, detail='接口不存在')

    roles = [
        {
            'key': key,
            'name': info['name'],
            'description': info['description'],
            'icon': info['icon'],
        }
        for key, info in DEMO_ROLES.items()
    ]
    return response_base.success(data=roles)


@router.post('/switch-role', summary='切换演示角色', dependencies=[DependsTurnstile])
async def switch_role(
    db: CurrentSessionTransaction,
    role_key: str,
):
    """
    快速切换到指定角色

    直接返回新角色的 JWT Token，前端无需重新登录
    """
    if not settings.DEMO_MODE:
        raise HTTPException(status_code=404, detail='接口不存在')

    if role_key not in DEMO_ROLES:
        raise HTTPException(status_code=400, detail='无效的角色')

    role_info = DEMO_ROLES[role_key]
    username = role_info['username']

    try:
        # 构造登录参数
        login_param = AuthLoginParam(
            username=username,
            password=DEMO_PASSWORD,
            captcha=None,
        )

        response = Response()
        background_tasks = BackgroundTasks()

        data = await auth_service.login(
            db=db,
            response=response,
            obj=login_param,
            background_tasks=background_tasks,
        )

        return response_base.success(
            data={
                'access_token': data.access_token,
                'token_type': 'Bearer',
                'role': {
                    'key': role_key,
                    'name': role_info['name'],
                },
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'角色切换失败: {e!s}')
