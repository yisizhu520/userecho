from fastapi import APIRouter

from backend.app.admin.api.v1.auth import router as auth_router
from backend.app.admin.api.v1.credits import router as credits_router
from backend.app.admin.api.v1.demo import router as demo_router
from backend.app.admin.api.v1.email_blacklist import router as email_blacklist_router
from backend.app.admin.api.v1.invitation import router as invitation_router
from backend.app.admin.api.v1.log import router as log_router
from backend.app.admin.api.v1.monitor import router as monitor_router
from backend.app.admin.api.v1.subscription import router as subscription_router
from backend.app.admin.api.v1.sys import router as sys_router
from backend.app.userecho.api.v1.auth_public import router as auth_public_router
from backend.app.userecho.api.v1.invitation_public import router as invitation_public_router
from backend.core.conf import settings

v1 = APIRouter(prefix=settings.FASTAPI_API_V1_PATH)

v1.include_router(auth_router)
v1.include_router(auth_public_router)
v1.include_router(sys_router)
v1.include_router(subscription_router)
v1.include_router(invitation_router)
v1.include_router(invitation_public_router)
v1.include_router(email_blacklist_router)
v1.include_router(log_router)
v1.include_router(monitor_router)
v1.include_router(demo_router)
v1.include_router(credits_router)
