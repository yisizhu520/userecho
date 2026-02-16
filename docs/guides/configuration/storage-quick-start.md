# 对象存储快速配置指南

## 1. 本地存储（默认，无需配置）

适合开发环境，无需额外配置，文件保存在本地。

```bash
# 在 .env 文件中（或不配置，使用默认值）
STORAGE_TYPE=local
```

## 2. 阿里云 OSS

### 安装依赖

```bash
cd server
pip install oss2
```

### 配置 .env

在 `server/backend/.env` 文件中添加：

```bash
# 存储类型
STORAGE_TYPE=aliyun_oss

# 阿里云 OSS 必填项
ALIYUN_OSS_ACCESS_KEY_ID=LTAI5t***************
ALIYUN_OSS_ACCESS_KEY_SECRET=mN9v*********************
ALIYUN_OSS_ENDPOINT=oss-cn-hangzhou.aliyuncs.com
ALIYUN_OSS_BUCKET_NAME=userecho-prod

# 可选项
ALIYUN_OSS_BASE_PATH=screenshots
ALIYUN_OSS_CDN_DOMAIN=https://cdn.yourdomain.com
```

## 3. 腾讯云 COS

### 安装依赖

```bash
cd server
pip install cos-python-sdk-v5
```

### 配置 .env

```bash
# 存储类型
STORAGE_TYPE=tencent_cos

# 腾讯云 COS 必填项
TENCENT_COS_SECRET_ID=AKIDz8***************
TENCENT_COS_SECRET_KEY=Gu5t*********************
TENCENT_COS_REGION=ap-guangzhou
TENCENT_COS_BUCKET_NAME=userecho-1234567890

# 可选项
TENCENT_COS_BASE_PATH=screenshots
TENCENT_COS_CDN_DOMAIN=https://cdn.yourdomain.com
```

## 4. AWS S3

### 安装依赖

```bash
cd server
pip install boto3
```

### 配置 .env

```bash
# 存储类型
STORAGE_TYPE=aws_s3

# AWS S3 必填项
AWS_S3_ACCESS_KEY_ID=AKIA***************
AWS_S3_SECRET_ACCESS_KEY=wJal*********************
AWS_S3_REGION=us-east-1
AWS_S3_BUCKET_NAME=userecho-prod

# 可选项
AWS_S3_BASE_PATH=screenshots
AWS_S3_CDN_DOMAIN=https://d1234567890.cloudfront.net
```

## 快速测试

启动服务后，访问 Swagger 文档测试上传：

```
http://localhost:8000/docs
```

找到 `/api/v1/userecho/screenshot/upload` 接口，上传一张图片测试。

## 常见问题

### Q: 如何切换存储？

A: 修改 `.env` 中的 `STORAGE_TYPE`，重启服务即可。

### Q: 本地存储的文件在哪里？

A: `server/backend/static/upload/screenshots/{tenant_id}/{year}/{month}/{day}/`

### Q: 云存储的 URL 是什么？

A: 
- 阿里云：`https://{bucket}.{endpoint}/{path}`
- 腾讯云：`https://{bucket}.cos.{region}.myqcloud.com/{path}`
- AWS S3：`https://{bucket}.s3.{region}.amazonaws.com/{path}`

如果配置了 CDN，则返回 CDN 地址。

## 更多文档

详细配置和故障排查请查看：`docs/storage-configuration.md`
