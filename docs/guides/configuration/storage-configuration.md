# 对象存储配置文档

## 概述

项目支持多种对象存储方案：
- **本地存储**（默认）：适合开发环境
- **阿里云 OSS**：国内首选，速度快
- **腾讯云 COS**：国内备选方案
- **AWS S3**：国际化部署

## 配置方式

### 1. 本地存储（开发环境）

在 `.env` 文件中：

```bash
# 存储类型
STORAGE_TYPE=local
```

文件将保存在 `server/backend/static/upload/` 目录。

访问地址：`http://localhost:8000/static/upload/{path}`

---

### 2. 阿里云 OSS

#### 2.1 安装依赖

```bash
pip install oss2
```

#### 2.2 配置 .env

```bash
# 存储类型
STORAGE_TYPE=aliyun_oss

# 阿里云 OSS 配置
ALIYUN_OSS_ACCESS_KEY_ID=your_access_key_id
ALIYUN_OSS_ACCESS_KEY_SECRET=your_access_key_secret
ALIYUN_OSS_ENDPOINT=oss-cn-hangzhou.aliyuncs.com
ALIYUN_OSS_BUCKET_NAME=your-bucket-name
ALIYUN_OSS_BASE_PATH=userecho
ALIYUN_OSS_CDN_DOMAIN=https://cdn.yourdomain.com  # 可选
```

#### 2.3 配置说明

- `ALIYUN_OSS_ENDPOINT`：访问域名（不包含 https://）
  - 杭州：`oss-cn-hangzhou.aliyuncs.com`
  - 北京：`oss-cn-beijing.aliyuncs.com`
  - 上海：`oss-cn-shanghai.aliyuncs.com`
  - 深圳：`oss-cn-shenzhen.aliyuncs.com`

- `ALIYUN_OSS_BASE_PATH`：存储根目录（可选）
  - 不设置：文件直接存在 bucket 根目录
  - 设置为 `userecho`：文件存在 `userecho/` 目录下

- `ALIYUN_OSS_CDN_DOMAIN`：CDN 加速域名（可选）
  - 如果配置了 CDN，返回 CDN 地址
  - 否则返回 OSS 默认地址

#### 2.4 创建 OSS Bucket

1. 登录 [阿里云 OSS 控制台](https://oss.console.aliyun.com/)
2. 创建 Bucket
   - 读写权限：**私有**
   - 存储类型：**标准存储**
   - 同城冗余：根据需求选择
3. 创建 RAM 用户
   - 权限：`AliyunOSSFullAccess`
   - 获取 AccessKey ID 和 AccessKey Secret

---

### 3. 腾讯云 COS

#### 3.1 安装依赖

```bash
pip install cos-python-sdk-v5
```

#### 3.2 配置 .env

```bash
# 存储类型
STORAGE_TYPE=tencent_cos

# 腾讯云 COS 配置
TENCENT_COS_SECRET_ID=your_secret_id
TENCENT_COS_SECRET_KEY=your_secret_key
TENCENT_COS_REGION=ap-guangzhou
TENCENT_COS_BUCKET_NAME=your-bucket-name-1234567890
TENCENT_COS_BASE_PATH=userecho
TENCENT_COS_CDN_DOMAIN=https://cdn.yourdomain.com  # 可选
```

#### 3.3 配置说明

- `TENCENT_COS_REGION`：地域
  - 广州：`ap-guangzhou`
  - 北京：`ap-beijing`
  - 上海：`ap-shanghai`
  - 深圳：`ap-shenzhen`

- `TENCENT_COS_BUCKET_NAME`：存储桶名称
  - 格式：`{BucketName}-{APPID}`
  - 例如：`userecho-1234567890`

#### 3.4 创建 COS Bucket

1. 登录 [腾讯云 COS 控制台](https://console.cloud.tencent.com/cos)
2. 创建存储桶
   - 访问权限：**私有读写**
   - 存储类型：**标准存储**
3. 创建 API 密钥
   - 进入 [访问管理控制台](https://console.cloud.tencent.com/cam/capi)
   - 获取 SecretId 和 SecretKey

---

### 4. AWS S3

#### 4.1 安装依赖

```bash
pip install boto3
```

#### 4.2 配置 .env

```bash
# 存储类型
STORAGE_TYPE=aws_s3

# AWS S3 配置
AWS_S3_ACCESS_KEY_ID=your_access_key_id
AWS_S3_SECRET_ACCESS_KEY=your_secret_access_key
AWS_S3_REGION=us-east-1
AWS_S3_BUCKET_NAME=your-bucket-name
AWS_S3_BASE_PATH=userecho
AWS_S3_CDN_DOMAIN=https://d1234567890.cloudfront.net  # 可选
```

#### 4.3 配置说明

- `AWS_S3_REGION`：区域
  - 美东（弗吉尼亚）：`us-east-1`
  - 美西（俄勒冈）：`us-west-2`
  - 亚太（东京）：`ap-northeast-1`
  - 亚太（新加坡）：`ap-southeast-1`

#### 4.4 创建 S3 Bucket

1. 登录 [AWS S3 控制台](https://console.aws.amazon.com/s3/)
2. 创建 Bucket
   - 阻止所有公共访问：**启用**
3. 创建 IAM 用户
   - 权限：`AmazonS3FullAccess`
   - 获取 Access Key ID 和 Secret Access Key

---

## 使用示例

### 基础用法

```python
from fastapi import UploadFile
from backend.utils.storage import storage, build_storage_path

async def upload_file(file: UploadFile):
    # 构建存储路径
    path = build_storage_path(file, prefix='screenshots')
    
    # 上传文件
    url = await storage.upload(file, path)
    
    return url
```

### 专用于反馈截图

```python
from backend.utils.storage import upload_screenshot

async def handle_screenshot(file: UploadFile, tenant_id: int):
    # 自动按租户分类存储
    url = await upload_screenshot(file, tenant_id)
    return url
```

### 获取签名 URL

```python
from backend.utils.storage import storage

# 生成 1 小时有效的签名链接
url = await storage.get_url('screenshots/123/2025/01/15/abc.jpg', expire_seconds=3600)
```

### 删除文件

```python
from backend.utils.storage import storage

success = await storage.delete('screenshots/123/2025/01/15/abc.jpg')
```

---

## 目录结构

### 本地存储

```
server/backend/static/upload/
└── screenshots/
    └── {tenant_id}/
        └── {year}/
            └── {month}/
                └── {day}/
                    └── {timestamp}_{random}.{ext}
```

### 云存储

```
{BASE_PATH}/
└── screenshots/
    └── {tenant_id}/
        └── {year}/
            └── {month}/
                └── {day}/
                    └── {timestamp}_{random}.{ext}
```

例如：
```
userecho/screenshots/1/2025/01/15/1705305600000_a1b2c3d4.jpg
```

---

## 性能优化建议

### 1. CDN 加速

配置 CDN 域名可以显著提升访问速度：

**阿里云 OSS + CDN:**
```bash
ALIYUN_OSS_CDN_DOMAIN=https://cdn.yourdomain.com
```

**腾讯云 COS + CDN:**
```bash
TENCENT_COS_CDN_DOMAIN=https://cdn.yourdomain.com
```

**AWS S3 + CloudFront:**
```bash
AWS_S3_CDN_DOMAIN=https://d1234567890.cloudfront.net
```

### 2. 生命周期管理

对于历史截图，建议配置生命周期规则：

- **30 天后转为低频访问存储**
- **180 天后转为归档存储**
- **365 天后自动删除**

在对象存储控制台配置即可，无需修改代码。

### 3. 图片处理

如果需要缩略图等功能，可以使用云服务商的图片处理服务：

**阿里云 OSS 图片处理:**
```
https://bucket.oss-cn-hangzhou.aliyuncs.com/path/to/image.jpg?x-oss-process=image/resize,w_200
```

**腾讯云 COS 数据万象:**
```
https://bucket.cos.ap-guangzhou.myqcloud.com/path/to/image.jpg?imageView2/1/w/200
```

---

## 故障排查

### 1. 上传失败

**错误：`ImportError: No module named 'oss2'`**

解决：安装对应的 SDK
```bash
pip install oss2  # 阿里云
pip install cos-python-sdk-v5  # 腾讯云
pip install boto3  # AWS
```

**错误：`AccessDenied` 或 `InvalidAccessKeyId`**

解决：检查配置
- AccessKey 是否正确
- RAM 用户/IAM 用户是否有权限
- Bucket 名称是否正确

### 2. 访问失败

**错误：`403 Forbidden`**

解决：
- 确认 Bucket 权限设置为**私有**
- 使用签名 URL 访问：`await storage.get_url(path)`

**错误：`404 Not Found`**

解决：
- 检查文件路径是否正确
- 确认文件已成功上传：`await storage.exists(path)`

### 3. 性能问题

**上传速度慢**

解决：
- 选择就近的地域（Region）
- 使用内网 Endpoint（服务器在同一地域）
- 检查网络带宽

**访问速度慢**

解决：
- 配置 CDN 加速
- 启用图片压缩
- 使用合适的图片格式（WebP）

---

## 安全建议

1. **使用私有 Bucket**
   - 所有文件设置为私有
   - 通过签名 URL 访问

2. **定期轮换密钥**
   - 建议每 90 天轮换一次 AccessKey

3. **最小权限原则**
   - RAM/IAM 用户只授予必要的权限
   - 不使用主账号密钥

4. **启用访问日志**
   - 监控异常访问
   - 审计文件操作

5. **配置 CORS**
   - 限制允许的域名
   - 设置合适的 HTTP 方法

---

## 成本优化

### 阿里云 OSS

- **标准存储**：¥0.12/GB/月
- **低频访问**：¥0.08/GB/月
- **归档存储**：¥0.03/GB/月

### 腾讯云 COS

- **标准存储**：¥0.118/GB/月
- **低频存储**：¥0.08/GB/月
- **归档存储**：¥0.03/GB/月

### AWS S3

- **标准存储**：$0.023/GB/月
- **低频访问**：$0.0125/GB/月
- **冰川存储**：$0.004/GB/月

**优化建议：**
1. 使用生命周期自动转换存储类型
2. 启用压缩减少存储空间
3. 定期清理无用文件
4. 使用对象标签进行成本分析

---

## 迁移指南

### 从本地存储迁移到云存储

1. **准备工作**
   - 创建云存储 Bucket
   - 配置 .env 文件
   - 安装对应 SDK

2. **批量上传现有文件**

```python
import asyncio
from pathlib import Path
from backend.utils.storage import storage

async def migrate_files():
    local_dir = Path('server/backend/static/upload/screenshots')
    
    for file_path in local_dir.rglob('*.*'):
        if file_path.is_file():
            # 保持原有路径结构
            relative_path = file_path.relative_to(local_dir)
            
            with open(file_path, 'rb') as f:
                url = await storage.upload(f, str(relative_path))
                print(f'Migrated: {relative_path} -> {url}')

asyncio.run(migrate_files())
```

3. **更新数据库中的 URL**

```sql
-- 替换域名（根据实际情况修改）
UPDATE feedback 
SET screenshot_url = REPLACE(
    screenshot_url, 
    'http://localhost:8000/static/upload/', 
    'https://cdn.yourdomain.com/userecho/'
)
WHERE screenshot_url LIKE 'http://localhost:8000/static/upload/%';
```

4. **验证**
   - 抽样检查文件访问是否正常
   - 测试新上传功能

5. **清理**
   - 确认迁移成功后删除本地文件
   - 释放服务器存储空间

---

## 常见问题

**Q: 可以同时使用多个存储后端吗？**

A: 目前只支持单一存储后端。如果需要多后端支持，可以扩展 `StorageManager` 类。

**Q: 如何切换存储后端？**

A: 修改 `.env` 中的 `STORAGE_TYPE`，重启服务即可。历史文件需要手动迁移。

**Q: 签名 URL 的有效期是多久？**

A: 默认 1 小时（3600 秒），可以通过 `expire_seconds` 参数自定义。

**Q: 支持断点续传吗？**

A: MVP 阶段暂不支持。如需要可以集成云服务商的分片上传 SDK。

**Q: 如何监控存储使用情况？**

A: 在云服务商控制台查看：
- 存储空间使用量
- 请求次数统计
- 流量消耗
- 费用账单
