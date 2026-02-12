"""调试中间件

专门用于开发环境的请求/响应调试日志
只在 info 级别记录，生产环境自动关闭
"""

import json
from typing import Any

from asgiref.sync import sync_to_async
from fastapi import Response
from starlette.datastructures import UploadFile
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from backend.common.log import log
from backend.core.conf import settings
from backend.utils.trace_id import get_request_trace_id


class DebugMiddleware(BaseHTTPMiddleware):
    """
    调试中间件 - 记录请求/响应详情
    
    功能：
    1. 记录请求的完整信息（方法、路径、参数、请求体）
    2. 记录响应的状态码和响应体
    3. 只在 DEBUG 级别记录
    4. 自动脱敏敏感信息
    """

    # 需要脱敏的字段
    SENSITIVE_FIELDS = {
        'password',
        'old_password',
        'new_password',
        'confirm_password',
        'token',
        'access_token',
        'refresh_token',
        'api_key',
        'secret',
        'authorization',
    }

    # 排除的路径（不记录调试日志）
    EXCLUDED_PATHS = {
        '/favicon.ico',
        '/docs',
        '/redoc',
        '/openapi.json',
        '/metrics',
    }

    async def dispatch(self, request: Request, call_next: Any) -> Response:
        """
        处理请求并记录调试日志

        :param request: FastAPI 请求对象
        :param call_next: 下一个中间件或路由处理函数
        :return: Response
        """
        path = request.url.path
        
        # 跳过静态资源和文档
        if any(path.startswith(excluded) for excluded in self.EXCLUDED_PATHS):
            return await call_next(request)
        
        # 跳过 OPTIONS 请求
        if request.method == 'OPTIONS':
            return await call_next(request)

        # 只在 DEBUG 级别记录
        if settings.LOG_STD_LEVEL == 'INFO':
            await self._log_request(request)

        # 执行请求
        response = await call_next(request)

        # 只在 DEBUG 级别记录响应
        if settings.LOG_STD_LEVEL == 'INFO':
            await self._log_response(response)

        return response

    async def _log_request(self, request: Request) -> None:
        """
        记录请求详情

        :param request: FastAPI 请求对象
        """
        try:
            request_id = get_request_trace_id()
            method = request.method
            path = request.url.path
            query_params = dict(request.query_params)
            headers = dict(request.headers)

            # 获取请求体
            body_data = await self._get_request_body(request)

            # 构建日志
            log_parts = [
                '=' * 80,
                f'🔵 REQUEST START | {request_id}',
                '=' * 80,
                f'Method: {method}',
                f'Path: {path}',
            ]

            # Query 参数
            if query_params:
                log_parts.append(f'Query Params: {json.dumps(query_params, ensure_ascii=False, indent=2)}')

            # Headers（只记录关键的）
            important_headers = {
                k: v for k, v in headers.items()
                if k.lower() in ['content-type', 'user-agent', 'x-request-id', 'accept']
            }
            if important_headers:
                log_parts.append(f'Headers: {json.dumps(important_headers, ensure_ascii=False, indent=2)}')

            # 请求体
            if body_data:
                log_parts.append(f'Body: {json.dumps(body_data, ensure_ascii=False, indent=2)}')

            log_parts.append('=' * 80)

            # 在日志前后添加空行，提高可读性
            log.info('\n' + '\n'.join(log_parts))

        except Exception as e:
            log.warning(f'Failed to log request details: {e}')

    async def _log_response(self, response: Response) -> None:
        """
        记录响应详情

        :param response: FastAPI 响应对象
        """
        try:
            request_id = get_request_trace_id()
            status_code = response.status_code

            # 获取响应体
            response_body = await self._get_response_body(response)

            # 构建日志
            log_parts = [
                '=' * 80,
                f'🟢 RESPONSE END | {request_id}',
                '=' * 80,
                f'Status Code: {status_code}',
            ]

            # 响应体
            if response_body:
                log_parts.append(f'Body: {json.dumps(response_body, ensure_ascii=False, indent=2)}')

            log_parts.append('=' * 80)

            # 在日志前后添加空行，提高可读性
            log.info('\n' + '\n'.join(log_parts) + '\n')

        except Exception as e:
            log.warning(f'Failed to log response details: {e}')

    async def _get_request_body(self, request: Request) -> dict[str, Any] | str | None:
        """
        获取请求体（自动脱敏）

        :param request: FastAPI 请求对象
        :return: 请求体数据
        """
        try:
            content_type = request.headers.get('Content-Type', '')

            # JSON 请求
            if 'application/json' in content_type:
                body = await request.body()
                if body:
                    try:
                        json_data = json.loads(body)
                        return await self._desensitize(json_data)
                    except json.JSONDecodeError:
                        return body.decode('utf-8', errors='replace')
                return None

            # 表单请求 - 不读取实际数据，避免消费掉 body stream
            elif 'application/x-www-form-urlencoded' in content_type or 'multipart/form-data' in content_type:
                # multipart/form-data 的 body stream 只能被读取一次
                # 如果在这里读取，后续业务代码就拿不到数据了
                # 只记录 Content-Type，不读取实际内容
                return f'<{content_type}>'

            # 其他类型（如 text/plain）
            else:
                body = await request.body()
                if body:
                    # 限制长度，避免打印过长的二进制数据
                    if len(body) > 1000:
                        return f'<Binary data: {len(body)} bytes>'
                    return body.decode('utf-8', errors='replace')
                return None

        except Exception as e:
            log.warning(f'Failed to get request body: {e}')
            return None

    async def _get_response_body(self, response: Response) -> dict | str | None:
        """
        获取响应体

        :param response: FastAPI 响应对象
        :return: 响应体数据
        """
        try:
            # 只记录 JSON 响应
            content_type = response.headers.get('content-type', '')
            if 'application/json' not in content_type:
                return f'<Non-JSON response: {content_type}>'

            # 读取响应体
            if hasattr(response, 'body'):
                body = response.body
                if body:
                    try:
                        json_data = json.loads(body)
                        # 响应体通常不包含敏感信息，但为了安全起见也脱敏
                        return await self._desensitize(json_data)
                    except json.JSONDecodeError:
                        return body.decode('utf-8', errors='replace')[:1000]  # 限制长度

            return None

        except Exception as e:
            log.warning(f'Failed to get response body: {e}')
            return None

    @sync_to_async
    def _desensitize(self, data: Any) -> Any:
        """
        脱敏处理（递归）

        :param data: 需要脱敏的数据
        :return: 脱敏后的数据
        """
        if isinstance(data, dict):
            return {
                key: '******' if key.lower() in self.SENSITIVE_FIELDS else self._desensitize_sync(value)
                for key, value in data.items()
            }
        elif isinstance(data, list):
            return [self._desensitize_sync(item) for item in data]
        else:
            return data

    def _desensitize_sync(self, data: Any) -> Any:
        """
        脱敏处理（同步版本，用于递归）

        :param data: 需要脱敏的数据
        :return: 脱敏后的数据
        """
        if isinstance(data, dict):
            return {
                key: '******' if key.lower() in self.SENSITIVE_FIELDS else self._desensitize_sync(value)
                for key, value in data.items()
            }
        elif isinstance(data, list):
            return [self._desensitize_sync(item) for item in data]
        else:
            return data

