"""
对象存储工具模块
支持：本地存储、阿里云 OSS、腾讯云 COS、AWS S3
"""

import hashlib
import os
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import BinaryIO

from fastapi import UploadFile

from backend.common.exception import errors
from backend.common.log import log
from backend.core.conf import settings
from backend.core.path_conf import UPLOAD_DIR


class StorageBackend(ABC):
    """存储后端抽象基类"""

    @abstractmethod
    async def upload(
        self,
        file: UploadFile | BinaryIO,
        path: str,
        content_type: str | None = None,
    ) -> str:
        """
        上传文件

        :param file: 文件对象
        :param path: 存储路径（相对路径）
        :param content_type: 文件 MIME 类型
        :return: 文件访问 URL
        """
        pass

    @abstractmethod
    async def delete(self, path: str) -> bool:
        """
        删除文件

        :param path: 文件路径
        :return: 是否成功
        """
        pass

    @abstractmethod
    async def get_url(self, path: str, expire_seconds: int = 3600) -> str:
        """
        获取文件访问 URL

        :param path: 文件路径
        :param expire_seconds: 过期时间（秒）
        :return: 访问 URL
        """
        pass

    @abstractmethod
    async def exists(self, path: str) -> bool:
        """
        检查文件是否存在

        :param path: 文件路径
        :return: 是否存在
        """
        pass


class LocalStorage(StorageBackend):
    """本地存储"""

    def __init__(self):
        self.base_dir = UPLOAD_DIR
        self.base_url = settings.STORAGE_LOCAL_BASE_URL or '/static/upload'

    async def upload(
        self,
        file: UploadFile | BinaryIO,
        path: str,
        content_type: str | None = None,
    ) -> str:
        """上传到本地"""
        full_path = self.base_dir / path
        full_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            if isinstance(file, UploadFile):
                with open(full_path, 'wb') as f:
                    while chunk := await file.read(settings.UPLOAD_READ_SIZE):
                        f.write(chunk)
            else:
                with open(full_path, 'wb') as f:
                    f.write(file.read())

            return f'{self.base_url}/{path}'
        except Exception as e:
            log.error(f'本地上传文件失败 {path}: {e}')
            raise errors.ServerError(msg='文件上传失败')

    async def delete(self, path: str) -> bool:
        """删除本地文件"""
        full_path = self.base_dir / path
        try:
            if full_path.exists():
                full_path.unlink()
                return True
            return False
        except Exception as e:
            log.error(f'删除本地文件失败 {path}: {e}')
            return False

    async def get_url(self, path: str, expire_seconds: int = 3600) -> str:
        """获取本地文件 URL（无过期时间）"""
        return f'{self.base_url}/{path}'

    async def exists(self, path: str) -> bool:
        """检查本地文件是否存在"""
        return (self.base_dir / path).exists()


class AliyunOSSStorage(StorageBackend):
    """阿里云 OSS 存储"""

    def __init__(self):
        try:
            import oss2
        except ImportError:
            raise ImportError('请安装 oss2: pip install oss2')

        self.access_key_id = settings.ALIYUN_OSS_ACCESS_KEY_ID
        self.access_key_secret = settings.ALIYUN_OSS_ACCESS_KEY_SECRET
        self.endpoint = settings.ALIYUN_OSS_ENDPOINT
        self.bucket_name = settings.ALIYUN_OSS_BUCKET_NAME
        self.base_path = settings.ALIYUN_OSS_BASE_PATH or ''

        auth = oss2.Auth(self.access_key_id, self.access_key_secret)
        self.bucket = oss2.Bucket(auth, self.endpoint, self.bucket_name)

    async def upload(
        self,
        file: UploadFile | BinaryIO,
        path: str,
        content_type: str | None = None,
    ) -> str:
        """上传到阿里云 OSS"""
        oss_path = f'{self.base_path}/{path}'.lstrip('/')

        try:
            if isinstance(file, UploadFile):
                content = await file.read()
            else:
                content = file.read()

            headers = {}
            if content_type:
                headers['Content-Type'] = content_type

            self.bucket.put_object(oss_path, content, headers=headers)

            # 返回 CDN 域名或 OSS 域名
            if hasattr(settings, 'ALIYUN_OSS_CDN_DOMAIN') and settings.ALIYUN_OSS_CDN_DOMAIN:
                return f'{settings.ALIYUN_OSS_CDN_DOMAIN}/{oss_path}'
            else:
                return f'https://{self.bucket_name}.{self.endpoint}/{oss_path}'
        except Exception as e:
            log.error(f'上传到阿里云 OSS 失败 {oss_path}: {e}')
            raise errors.ServerError(msg='文件上传失败')

    async def delete(self, path: str) -> bool:
        """删除 OSS 文件"""
        oss_path = f'{self.base_path}/{path}'.lstrip('/')
        try:
            self.bucket.delete_object(oss_path)
            return True
        except Exception as e:
            log.error(f'删除 OSS 文件失败 {oss_path}: {e}')
            return False

    async def get_url(self, path: str, expire_seconds: int = 3600) -> str:
        """获取签名 URL"""
        oss_path = f'{self.base_path}/{path}'.lstrip('/')
        try:
            return self.bucket.sign_url('GET', oss_path, expire_seconds)
        except Exception as e:
            log.error(f'生成 OSS 签名 URL 失败 {oss_path}: {e}')
            raise errors.ServerError(msg='生成访问链接失败')

    async def exists(self, path: str) -> bool:
        """检查 OSS 文件是否存在"""
        oss_path = f'{self.base_path}/{path}'.lstrip('/')
        try:
            return self.bucket.object_exists(oss_path)
        except Exception:
            return False


class TencentCOSStorage(StorageBackend):
    """腾讯云 COS 存储"""

    def __init__(self):
        try:
            from qcloud_cos import CosConfig, CosS3Client
        except ImportError:
            raise ImportError('请安装 cos-python-sdk-v5: pip install cos-python-sdk-v5')

        self.secret_id = settings.TENCENT_COS_SECRET_ID
        self.secret_key = settings.TENCENT_COS_SECRET_KEY
        self.region = settings.TENCENT_COS_REGION
        self.bucket_name = settings.TENCENT_COS_BUCKET_NAME
        self.base_path = settings.TENCENT_COS_BASE_PATH or ''

        config = CosConfig(Region=self.region, SecretId=self.secret_id, SecretKey=self.secret_key)
        self.client = CosS3Client(config)

    async def upload(
        self,
        file: UploadFile | BinaryIO,
        path: str,
        content_type: str | None = None,
    ) -> str:
        """上传到腾讯云 COS"""
        cos_path = f'{self.base_path}/{path}'.lstrip('/')

        try:
            if isinstance(file, UploadFile):
                content = await file.read()
            else:
                content = file.read()

            kwargs = {}
            if content_type:
                kwargs['ContentType'] = content_type

            self.client.put_object(Bucket=self.bucket_name, Body=content, Key=cos_path, **kwargs)

            # 返回 CDN 域名或 COS 域名
            if hasattr(settings, 'TENCENT_COS_CDN_DOMAIN') and settings.TENCENT_COS_CDN_DOMAIN:
                return f'{settings.TENCENT_COS_CDN_DOMAIN}/{cos_path}'
            else:
                return f'https://{self.bucket_name}.cos.{self.region}.myqcloud.com/{cos_path}'
        except Exception as e:
            log.error(f'上传到腾讯云 COS 失败 {cos_path}: {e}')
            raise errors.ServerError(msg='文件上传失败')

    async def delete(self, path: str) -> bool:
        """删除 COS 文件"""
        cos_path = f'{self.base_path}/{path}'.lstrip('/')
        try:
            self.client.delete_object(Bucket=self.bucket_name, Key=cos_path)
            return True
        except Exception as e:
            log.error(f'删除 COS 文件失败 {cos_path}: {e}')
            return False

    async def get_url(self, path: str, expire_seconds: int = 3600) -> str:
        """获取签名 URL"""
        cos_path = f'{self.base_path}/{path}'.lstrip('/')
        try:
            url = self.client.get_presigned_url(
                Method='GET',
                Bucket=self.bucket_name,
                Key=cos_path,
                Expired=expire_seconds,
            )
            return url
        except Exception as e:
            log.error(f'生成 COS 签名 URL 失败 {cos_path}: {e}')
            raise errors.ServerError(msg='生成访问链接失败')

    async def exists(self, path: str) -> bool:
        """检查 COS 文件是否存在"""
        cos_path = f'{self.base_path}/{path}'.lstrip('/')
        try:
            self.client.head_object(Bucket=self.bucket_name, Key=cos_path)
            return True
        except Exception:
            return False


class AWSS3Storage(StorageBackend):
    """AWS S3 存储"""

    def __init__(self):
        try:
            import boto3
        except ImportError:
            raise ImportError('请安装 boto3: pip install boto3')

        self.access_key_id = settings.AWS_S3_ACCESS_KEY_ID
        self.secret_access_key = settings.AWS_S3_SECRET_ACCESS_KEY
        self.region = settings.AWS_S3_REGION
        self.bucket_name = settings.AWS_S3_BUCKET_NAME
        self.base_path = settings.AWS_S3_BASE_PATH or ''

        self.client = boto3.client(
            's3',
            aws_access_key_id=self.access_key_id,
            aws_secret_access_key=self.secret_access_key,
            region_name=self.region,
        )

    async def upload(
        self,
        file: UploadFile | BinaryIO,
        path: str,
        content_type: str | None = None,
    ) -> str:
        """上传到 AWS S3"""
        s3_path = f'{self.base_path}/{path}'.lstrip('/')

        try:
            if isinstance(file, UploadFile):
                content = await file.read()
            else:
                content = file.read()

            extra_args = {}
            if content_type:
                extra_args['ContentType'] = content_type

            self.client.put_object(Bucket=self.bucket_name, Key=s3_path, Body=content, **extra_args)

            # 返回 CloudFront 域名或 S3 域名
            if hasattr(settings, 'AWS_S3_CDN_DOMAIN') and settings.AWS_S3_CDN_DOMAIN:
                return f'{settings.AWS_S3_CDN_DOMAIN}/{s3_path}'
            else:
                return f'https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{s3_path}'
        except Exception as e:
            log.error(f'上传到 AWS S3 失败 {s3_path}: {e}')
            raise errors.ServerError(msg='文件上传失败')

    async def delete(self, path: str) -> bool:
        """删除 S3 文件"""
        s3_path = f'{self.base_path}/{path}'.lstrip('/')
        try:
            self.client.delete_object(Bucket=self.bucket_name, Key=s3_path)
            return True
        except Exception as e:
            log.error(f'删除 S3 文件失败 {s3_path}: {e}')
            return False

    async def get_url(self, path: str, expire_seconds: int = 3600) -> str:
        """获取签名 URL"""
        s3_path = f'{self.base_path}/{path}'.lstrip('/')
        try:
            url = self.client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': s3_path},
                ExpiresIn=expire_seconds,
            )
            return url
        except Exception as e:
            log.error(f'生成 S3 签名 URL 失败 {s3_path}: {e}')
            raise errors.ServerError(msg='生成访问链接失败')

    async def exists(self, path: str) -> bool:
        """检查 S3 文件是否存在"""
        s3_path = f'{self.base_path}/{path}'.lstrip('/')
        try:
            self.client.head_object(Bucket=self.bucket_name, Key=s3_path)
            return True
        except Exception:
            return False


class StorageManager:
    """存储管理器（单例）"""

    _instance = None
    _backend: StorageBackend | None = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._backend is None:
            self._init_backend()

    def _init_backend(self):
        """初始化存储后端"""
        storage_type = settings.STORAGE_TYPE.lower()

        if storage_type == 'local':
            self._backend = LocalStorage()
            log.info('Storage backend initialized: Local')
        elif storage_type == 'aliyun_oss':
            self._backend = AliyunOSSStorage()
            log.info('Storage backend initialized: Aliyun OSS')
        elif storage_type == 'tencent_cos':
            self._backend = TencentCOSStorage()
            log.info('Storage backend initialized: Tencent COS')
        elif storage_type == 'aws_s3':
            self._backend = AWSS3Storage()
            log.info('Storage backend initialized: AWS S3')
        else:
            log.warning(f'Unknown storage type: {storage_type}, fallback to local')
            self._backend = LocalStorage()

    @property
    def backend(self) -> StorageBackend:
        """获取当前存储后端"""
        return self._backend

    async def upload(
        self,
        file: UploadFile | BinaryIO,
        path: str,
        content_type: str | None = None,
    ) -> str:
        """上传文件"""
        return await self._backend.upload(file, path, content_type)

    async def delete(self, path: str) -> bool:
        """删除文件"""
        return await self._backend.delete(path)

    async def get_url(self, path: str, expire_seconds: int = 3600) -> str:
        """获取文件访问 URL"""
        return await self._backend.get_url(path, expire_seconds)

    async def exists(self, path: str) -> bool:
        """检查文件是否存在"""
        return await self._backend.exists(path)


# 全局存储管理器实例
storage = StorageManager()


def build_storage_path(
    file: UploadFile,
    prefix: str = '',
    use_hash: bool = False,
) -> str:
    """
    构建存储路径

    :param file: 上传文件
    :param prefix: 路径前缀（如 'screenshots', 'avatars'）
    :param use_hash: 是否使用文件内容哈希作为文件名
    :return: 存储路径
    """
    now = datetime.now()
    date_path = now.strftime('%Y/%m/%d')

    # 提取文件扩展名
    filename = file.filename or 'unnamed'
    file_ext = filename.split('.')[-1].lower() if '.' in filename else 'bin'

    # 生成文件名
    if use_hash:
        # 使用文件内容的 MD5 作为文件名（需要先读取文件）
        content = file.file.read()
        file.file.seek(0)  # 重置文件指针
        file_hash = hashlib.md5(content).hexdigest()
        new_filename = f'{file_hash}.{file_ext}'
    else:
        # 使用时间戳
        timestamp = int(now.timestamp() * 1000)  # 毫秒级时间戳
        new_filename = f'{timestamp}_{os.urandom(4).hex()}.{file_ext}'

    # 组合路径
    parts = [prefix, date_path, new_filename] if prefix else [date_path, new_filename]
    return '/'.join(parts)


async def upload_screenshot(file: UploadFile, tenant_id: int) -> str:
    """
    上传截图（专用于反馈截图）

    :param file: 上传文件
    :param tenant_id: 租户 ID
    :return: 文件访问 URL
    """
    # 构建路径：screenshots/{tenant_id}/{year}/{month}/{day}/{filename}
    path = build_storage_path(file, prefix=f'screenshots/{tenant_id}')

    # 上传
    url = await storage.upload(file, path, content_type=file.content_type)

    log.info(f'Screenshot uploaded: {path} -> {url}')
    return url
