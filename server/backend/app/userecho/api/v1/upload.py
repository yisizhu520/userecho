"""通用上传 API"""

from typing import Any

from fastapi import APIRouter

from backend.app.admin.schema.upload import UploadSignRequest, UploadTypeConfig
from backend.common.log import log
from backend.common.response.response_code import CustomResponse
from backend.common.response.response_schema import response_base
from backend.common.security.jwt import CurrentTenantId

router = APIRouter(prefix="/upload", tags=["通用上传"])


@router.post("/sign", summary="获取对象存储直传签名", name="userecho_get_upload_sign")
async def get_upload_sign(
    data: UploadSignRequest,
    tenant_id: str = CurrentTenantId,
) -> Any:
    """
    获取对象存储直传签名

    支持的上传类型：
    - screenshot: 截图（PNG/JPG/JPEG/WEBP，最大 10MB）
    - avatar: 头像（PNG/JPG/JPEG/WEBP，最大 2MB）
    - document: 文档（PDF/DOC/DOCX/XLS/XLSX/PPT/PPTX/TXT/MD，最大 50MB）
    - attachment: 附件（ZIP/RAR/7Z/TAR/GZ/PDF/图片，最大 100MB）

    权限要求：仅需登录（CurrentTenantId 已鉴权）
    """
    from backend.utils.storage import build_storage_path_from_filename, get_upload_signature

    filename = data.filename.strip()
    if not filename:
        return response_base.fail(res=CustomResponse(code=400, msg="文件名不能为空"))

    # 获取上传类型配置
    config = UploadTypeConfig.get_config(data.upload_type)
    allowed_extensions = config["allowed_extensions"]
    path_prefix = config["path_prefix"]

    # 验证文件扩展名
    file_ext = filename.split(".")[-1].lower() if "." in filename else ""
    if file_ext not in allowed_extensions:
        return response_base.fail(
            res=CustomResponse(code=400, msg=f"不支持的文件格式，仅支持: {', '.join(sorted(allowed_extensions))}")
        )

    try:
        # 构建存储路径
        path = build_storage_path_from_filename(filename, prefix=f"{path_prefix}/{tenant_id}")

        # 获取签名
        sign = get_upload_signature(path, content_type=data.content_type, expire_seconds=300)

        log.info(f"Generated upload sign for tenant {tenant_id}: type={data.upload_type}, path={path}")
        return response_base.success(data=sign)
    except Exception as e:
        log.error(f"Failed to generate upload sign for tenant {tenant_id}: {e}")
        return response_base.fail(res=CustomResponse(code=500, msg=f"生成上传签名失败: {e!s}"))
