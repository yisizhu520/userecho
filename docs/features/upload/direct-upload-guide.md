# 通用直传上传模块使用指南

## 概述

通用上传模块提供了统一的对象存储直传能力，支持多种上传场景（截图、头像、文档、附件等）。前端通过获取签名直接上传到对象存储（腾讯云 COS），避免后端中转，减少上传耗时和带宽开销。

## 架构设计

### 流程图

```
前端                     后端                    对象存储(COS)
  |                       |                           |
  |--1. 获取签名--------->|                           |
  |<--2. 返回签名---------|                           |
  |                       |                           |
  |--3. 直传文件---------------------------->|
  |<-4. 上传成功--------------------------|
  |                       |                           |
  |--5. 回传 URL--------->|                           |
  |<--6. 业务处理---------|                           |
```

### 核心组件

- **后端签名接口**: `POST /api/v1/app/upload/sign`
- **前端上传 API**: `#/api/core/upload`
- **配置管理**: `backend/app/admin/schema/upload.py`

## 后端实现

### 1. Schema 定义

**文件**: `server/backend/app/admin/schema/upload.py`

```python
class UploadSignRequest(SchemaBase):
    """获取上传签名请求"""
    filename: str = Field(description="原始文件名")
    upload_type: Literal["screenshot", "avatar", "document", "attachment"] = Field(
        default="screenshot",
        description="上传类型: screenshot=截图, avatar=头像, document=文档, attachment=附件",
    )
    content_type: str | None = Field(None, description="文件 MIME 类型")
```

### 2. 上传类型配置

每种上传类型有独立的配置：

| 类型 | 允许扩展名 | 最大大小 | 路径前缀 |
|------|-----------|----------|----------|
| **screenshot** | png, jpg, jpeg, webp | 10MB | `screenshots/{tenant_id}` |
| **avatar** | png, jpg, jpeg, webp | 2MB | `avatars/{tenant_id}` |
| **document** | pdf, doc, docx, xls, xlsx, ppt, pptx, txt, md | 50MB | `documents/{tenant_id}` |
| **attachment** | zip, rar, 7z, tar, gz, pdf, png, jpg, jpeg, webp | 100MB | `attachments/{tenant_id}` |

**扩展配置**:

```python
class UploadTypeConfig:
    # 添加新的上传类型
    CUSTOM = {
        "allowed_extensions": {"custom"},
        "max_size": 20 * 1024 * 1024,  # 20MB
        "path_prefix": "custom",
    }
```

### 3. 签名接口实现

**文件**: `server/backend/app/admin/api/v1/sys/file.py`

```python
@router.post("/upload/sign", summary="获取对象存储直传签名")
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
    """
    from backend.utils.storage import build_storage_path_from_filename, get_upload_signature
    
    # 1. 验证文件名
    filename = data.filename.strip()
    if not filename:
        return response_base.fail(res=CustomResponse(code=400, msg="文件名不能为空"))
    
    # 2. 获取上传类型配置
    config = UploadTypeConfig.get_config(data.upload_type)
    allowed_extensions = config["allowed_extensions"]
    path_prefix = config["path_prefix"]
    
    # 3. 验证文件扩展名
    file_ext = filename.split(".")[-1].lower() if "." in filename else ""
    if file_ext not in allowed_extensions:
        return response_base.fail(
            res=CustomResponse(code=400, msg=f"不支持的文件格式，仅支持: {', '.join(sorted(allowed_extensions))}")
        )
    
    # 4. 构建存储路径
    path = build_storage_path_from_filename(filename, prefix=f"{path_prefix}/{tenant_id}")
    
    # 5. 获取签名
    sign = get_upload_signature(path, content_type=data.content_type, expire_seconds=300)
    
    return response_base.success(data=sign)
```

### 4. 签名响应格式

```json
{
  "code": 200,
  "data": {
    "upload_url": "https://bucket.cos.region.myqcloud.com/path?sign=...",
    "method": "PUT",
    "headers": {
      "Content-Type": "image/png"
    },
    "cdn_url": "https://cdn.yourdomain.com/path",
    "object_key": "screenshots/tenant-123/2026/01/27/1738048800000_a1b2c3d4.png",
    "expires_in": 300
  }
}
```

## 前端实现

### 1. API 封装

**文件**: `front/apps/web-antd/src/api/core/upload.ts`

```typescript
import { requestClient } from '#/api/request';

/** 上传类型 */
export type UploadType = 'screenshot' | 'avatar' | 'document' | 'attachment';

/** 上传签名请求 */
export interface UploadSignRequest {
  filename: string;
  upload_type: UploadType;
  content_type?: string;
}

/** 上传签名响应 */
export interface UploadSignResponse {
  upload_url: string;
  method: 'PUT';
  headers: Record<string, string>;
  cdn_url: string;
  object_key: string;
  expires_in: number;
}

/**
 * 获取上传签名
 */
export async function getUploadSign(data: UploadSignRequest) {
  return requestClient.post<UploadSignResponse>('/api/v1/app/upload/sign', data);
}

/**
 * 直传到对象存储
 */
export async function uploadToSignedUrl(sign: UploadSignResponse, file: File) {
  const headers = new Headers(sign.headers || {});
  if (!headers.has('Content-Type') && file.type) {
    headers.set('Content-Type', file.type);
  }

  const response = await fetch(sign.upload_url, {
    method: sign.method || 'PUT',
    headers,
    body: file,
  });

  if (!response.ok) {
    throw new Error(`直传失败: ${response.status}`);
  }
}

/**
 * 完整上传流程（获取签名 + 直传）
 */
export async function uploadFile(file: File, uploadType: UploadType): Promise<string> {
  const sign = await getUploadSign({
    filename: file.name,
    upload_type: uploadType,
    content_type: file.type,
  });

  await uploadToSignedUrl(sign, file);

  return sign.cdn_url;
}
```

### 2. 便捷方法

```typescript
/**
 * 上传截图（便捷方法）
 */
export async function uploadScreenshot(file: File): Promise<string> {
  return uploadFile(file, 'screenshot');
}

/**
 * 上传头像（便捷方法）
 */
export async function uploadAvatar(file: File): Promise<string> {
  return uploadFile(file, 'avatar');
}

/**
 * 上传文档（便捷方法）
 */
export async function uploadDocument(file: File): Promise<string> {
  return uploadFile(file, 'document');
}

/**
 * 上传附件（便捷方法）
 */
export async function uploadAttachment(file: File): Promise<string> {
  return uploadFile(file, 'attachment');
}
```

## 使用示例

### 示例 1: 上传头像

```typescript
import { uploadAvatar } from '#/api/core/upload';
import { message } from 'ant-design-vue';

async function handleAvatarUpload(file: File) {
  try {
    // 1. 直传到 COS
    const avatarUrl = await uploadAvatar(file);
    
    // 2. 更新用户头像
    await updateUserAvatar({ avatar_url: avatarUrl });
    
    message.success('头像上传成功');
  } catch (error) {
    message.error('头像上传失败');
    console.error(error);
  }
}
```

### 示例 2: 上传文档（带进度）

```typescript
import { getUploadSign, uploadToSignedUrl } from '#/api/core/upload';
import { ref } from 'vue';

const uploadProgress = ref(0);

async function handleDocumentUpload(file: File) {
  try {
    uploadProgress.value = 10;
    
    // 1. 获取签名
    const sign = await getUploadSign({
      filename: file.name,
      upload_type: 'document',
      content_type: file.type,
    });
    
    uploadProgress.value = 30;
    
    // 2. 直传文件（可以添加 XMLHttpRequest 监听进度）
    await uploadToSignedUrl(sign, file);
    
    uploadProgress.value = 100;
    
    // 3. 使用 CDN URL
    console.log('Document URL:', sign.cdn_url);
  } catch (error) {
    console.error('Upload failed:', error);
  }
}
```

### 示例 3: 批量上传附件

```typescript
import { uploadAttachment } from '#/api/core/upload';

async function handleBatchUpload(files: File[]) {
  const results = await Promise.allSettled(
    files.map(file => uploadAttachment(file))
  );
  
  const successUrls = results
    .filter((r): r is PromiseFulfilledResult<string> => r.status === 'fulfilled')
    .map(r => r.value);
  
  const failedCount = results.filter(r => r.status === 'rejected').length;
  
  console.log(`成功: ${successUrls.length}, 失败: ${failedCount}`);
  
  return successUrls;
}
```

### 示例 4: 带回退的上传（兼容性最佳）

```typescript
import { uploadScreenshot } from '#/api/core/upload';

async function uploadWithFallback(file: File): Promise<string> {
  try {
    // 优先直传
    return await uploadScreenshot(file);
  } catch (error) {
    console.warn('直传失败，回退到后端中转上传', error);
    
    // 回退到后端上传
    const formData = new FormData();
    formData.append('file', file);
    const response = await requestClient.post('/api/v1/app/feedbacks/upload-image', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    
    return response.url;
  }
}
```

## 配置要求

### 1. 腾讯云 COS 配置

确保 `.env` 文件中配置了腾讯云 COS：

```bash
# 存储类型
STORAGE_TYPE=tencent_cos

# 腾讯云 COS 配置
TENCENT_COS_SECRET_ID=AKIDz8***************
TENCENT_COS_SECRET_KEY=Gu5t*********************
TENCENT_COS_REGION=ap-guangzhou
TENCENT_COS_BUCKET_NAME=userecho-1234567890
TENCENT_COS_BASE_PATH=userecho
TENCENT_COS_CDN_DOMAIN=https://cdn.yourdomain.com
```

### 2. COS CORS 配置

在腾讯云 COS 控制台配置 CORS 规则：

```json
[
  {
    "AllowedOrigins": ["https://your-domain.com"],
    "AllowedMethods": ["GET", "PUT", "POST"],
    "AllowedHeaders": ["*"],
    "ExposeHeaders": ["ETag"],
    "MaxAgeSeconds": 3600
  }
]
```

## 安全考虑

### 1. 签名有效期

签名默认有效期为 300 秒（5 分钟），足够前端完成上传。过期后签名失效，需要重新获取。

### 2. 租户隔离

所有上传路径都包含 `tenant_id`，确保不同租户的文件隔离存储：

```
screenshots/{tenant_id}/{date}/{filename}
avatars/{tenant_id}/{date}/{filename}
```

### 3. 文件类型验证

后端签名接口会验证文件扩展名，只允许配置的文件类型。

### 4. 文件大小限制

每种上传类型有独立的大小限制，超过限制的文件会被拒绝。

## 迁移指南

### 从旧接口迁移到通用上传

#### 1. 后端接口调整（已完成）

旧接口 `/api/v1/app/feedbacks/upload-image/sign` 已标记为 `deprecated`，但仍然可用（兼容性保留）。

#### 2. 前端代码迁移

**旧代码**:
```typescript
import { getFeedbackImageUploadSign, uploadImageToSignedUrl } from '#/api/userecho/feedback';

const sign = await getFeedbackImageUploadSign({
  filename: file.name,
  content_type: file.type,
});

await uploadImageToSignedUrl(sign, file);
```

**新代码**:
```typescript
import { getUploadSign, uploadToSignedUrl } from '#/api/core/upload';

const sign = await getUploadSign({
  filename: file.name,
  upload_type: 'screenshot',
  content_type: file.type,
});

await uploadToSignedUrl(sign, file);
```

**或使用便捷方法**:
```typescript
import { uploadScreenshot } from '#/api/core/upload';

const url = await uploadScreenshot(file);
```

## 性能优化

### 1. 并行上传

对于批量上传场景，使用 `Promise.all` 并行上传：

```typescript
const urls = await Promise.all(
  files.map(file => uploadAttachment(file))
);
```

### 2. 大文件分片上传

对于超大文件（> 100MB），考虑使用腾讯云 COS 的分片上传 API。

### 3. CDN 加速

使用 `TENCENT_COS_CDN_DOMAIN` 配置 CDN 域名，加速文件访问。

## 故障排查

### 问题 1: 直传失败 (403 Forbidden)

**原因**: CORS 配置不正确  
**解决**: 检查 COS CORS 配置，确保允许前端域名

### 问题 2: 签名过期

**原因**: 前端获取签名后超过 5 分钟才上传  
**解决**: 重新获取签名，或增加 `expire_seconds` 参数

### 问题 3: 文件类型不支持

**原因**: 文件扩展名不在允许列表中  
**解决**: 检查 `UploadTypeConfig` 配置，或选择正确的 `upload_type`

### 问题 4: 直传成功但 AI 识别失败

**原因**: URL 不在允许的 COS/CDN 域名内  
**解决**: 检查 `TENCENT_COS_CDN_DOMAIN` 配置，确保 URL 前缀匹配

## 未来扩展

### 1. 支持阿里云 OSS 和 AWS S3

修改 `get_upload_signature` 函数，根据 `STORAGE_TYPE` 生成不同云存储的签名。

### 2. 支持更多上传类型

在 `UploadTypeConfig` 中添加新的配置：

```python
VIDEO = {
    "allowed_extensions": {"mp4", "avi", "mov"},
    "max_size": 500 * 1024 * 1024,  # 500MB
    "path_prefix": "videos",
}
```

### 3. 添加文件大小客户端验证

前端在获取签名前先验证文件大小，提前拒绝超大文件。

## 参考资料

- [腾讯云 COS 签名文档](https://cloud.tencent.com/document/product/436/7778)
- [腾讯云 COS CORS 配置](https://cloud.tencent.com/document/product/436/13318)
- [Backend Storage Utils](../../server/backend/utils/storage.py)
