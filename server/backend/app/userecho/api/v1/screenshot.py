"""
截图上传 API 示例
演示如何使用对象存储工具
"""

from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile

from backend.app.userecho.schema.feedback import ScreenshotAnalyzeResponse
from backend.common.response.response_schema import ResponseSchemaModel, response_base
from backend.common.security.jwt import DependsJwtAuth
from backend.common.security.rbac import DependsRBAC
from backend.utils.file_ops import upload_file_verify
from backend.utils.storage import upload_screenshot

router = APIRouter()


@router.post(
    '/screenshot/upload',
    summary='上传截图',
    description='上传反馈截图到对象存储',
    dependencies=[DependsJwtAuth, DependsRBAC],
)
async def upload_feedback_screenshot(
    file: Annotated[UploadFile, File(description='截图文件')],
    tenant_id: int,
) -> ResponseSchemaModel[dict]:
    """
    上传反馈截图

    **文件要求：**
    - 格式：JPG, JPEG, PNG, GIF, WEBP
    - 大小：最大 10MB
    - 类型：图片

    **返回：**
    - screenshot_url: 截图访问地址
    """
    # 验证文件
    upload_file_verify(file)

    # 上传到对象存储
    screenshot_url = await upload_screenshot(file, tenant_id)

    return response_base.success(data={'screenshot_url': screenshot_url})


@router.post(
    '/screenshot/analyze',
    summary='上传并 AI 识别截图',
    description='上传截图后使用 AI 自动识别平台和内容',
    dependencies=[DependsJwtAuth, DependsRBAC],
)
async def analyze_feedback_screenshot(
    file: Annotated[UploadFile, File(description='截图文件')],
    tenant_id: int,
) -> ResponseSchemaModel[ScreenshotAnalyzeResponse]:
    """
    上传并识别截图

    **流程：**
    1. 上传截图到对象存储
    2. 调用 AI 识别平台、昵称、内容
    3. 返回结构化数据

    **返回：**
    - screenshot_url: 截图 URL
    - extracted: AI 提取的信息
      - platform: 平台类型
      - user_name: 用户昵称
      - content: 反馈内容
      - feedback_type: 反馈类型
      - confidence: 识别置信度
    """
    # 验证文件
    upload_file_verify(file)

    # 1. 上传到对象存储
    screenshot_url = await upload_screenshot(file, tenant_id)

    # 2. AI 识别（TODO: 实现 AI 识别逻辑）
    # from backend.utils.ai_client import analyze_screenshot_with_ai
    # extracted = await analyze_screenshot_with_ai(screenshot_url)

    # 临时返回示例数据
    extracted = {
        'platform': 'wechat',
        'user_name': '小王',
        'user_id': '',
        'content': '产品闪退了，iOS 16.3',
        'feedback_type': 'bug',
        'sentiment': 'negative',
        'confidence': 0.95,
    }

    return response_base.success(
        data={
            'screenshot_url': screenshot_url,
            'extracted': extracted,
        }
    )
