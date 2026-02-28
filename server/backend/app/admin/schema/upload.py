"""上传相关 Schema"""

from typing import Literal

from pydantic import Field

from backend.common.schema import SchemaBase


class UploadSignRequest(SchemaBase):
    """获取上传签名请求"""

    filename: str = Field(description="原始文件名")
    upload_type: Literal["screenshot", "avatar", "document", "attachment"] = Field(
        default="screenshot",
        description="上传类型: screenshot=截图, avatar=头像, document=文档, attachment=附件",
    )
    content_type: str | None = Field(None, description="文件 MIME 类型")


class UploadSignResponse(SchemaBase):
    """上传签名响应"""

    upload_url: str = Field(description="直传上传地址")
    method: Literal["PUT"] = Field(default="PUT", description="上传方法")
    headers: dict[str, str] = Field(default_factory=dict, description="上传请求头")
    cdn_url: str = Field(description="上传完成后访问 URL")
    object_key: str = Field(description="对象 Key")
    expires_in: int = Field(description="签名有效期（秒）")


class UploadTypeConfig:
    """上传类型配置"""

    # 截图
    SCREENSHOT = {
        "allowed_extensions": {"png", "jpg", "jpeg", "webp"},
        "max_size": 10 * 1024 * 1024,  # 10MB
        "path_prefix": "screenshots",
    }

    # 头像
    AVATAR = {
        "allowed_extensions": {"png", "jpg", "jpeg", "webp"},
        "max_size": 2 * 1024 * 1024,  # 2MB
        "path_prefix": "avatars",
    }

    # 文档
    DOCUMENT = {
        "allowed_extensions": {"pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx", "txt", "md"},
        "max_size": 50 * 1024 * 1024,  # 50MB
        "path_prefix": "documents",
    }

    # 附件
    ATTACHMENT = {
        "allowed_extensions": {"zip", "rar", "7z", "tar", "gz", "pdf", "png", "jpg", "jpeg", "webp"},
        "max_size": 100 * 1024 * 1024,  # 100MB
        "path_prefix": "attachments",
    }

    @classmethod
    def get_config(cls, upload_type: str) -> dict:
        """根据上传类型获取配置"""
        config_map = {
            "screenshot": cls.SCREENSHOT,
            "avatar": cls.AVATAR,
            "document": cls.DOCUMENT,
            "attachment": cls.ATTACHMENT,
        }
        return config_map.get(upload_type, cls.SCREENSHOT)
