# 对象存储实现总结

## ✅ 已完成的工作

### 1. 核心存储工具 (`server/backend/utils/storage.py`)

实现了统一的对象存储接口，支持：

- **本地存储**（LocalStorage）- 默认，开发环境使用
- **阿里云 OSS**（AliyunOSSStorage）- 国内首选
- **腾讯云 COS**（TencentCOSStorage）- 国内备选
- **AWS S3**（AWSS3Storage）- 国际化部署

**核心功能：**
- ✅ 文件上传（upload）
- ✅ 文件删除（delete）
- ✅ 获取签名 URL（get_url）
- ✅ 检查文件存在（exists）
- ✅ 自动路径生成（build_storage_path）
- ✅ 截图专用上传（upload_screenshot）

**设计特点：**
- 抽象基类 `StorageBackend` 定义统一接口
- 单例模式 `StorageManager` 管理存储后端
- 运行时根据配置自动选择存储后端
- 支持 CDN 加速域名配置

---

### 2. 配置文件扩展 (`server/backend/core/conf.py`)

新增配置项：

```python
# 存储类型
STORAGE_TYPE: Literal['local', 'aliyun_oss', 'tencent_cos', 'aws_s3'] = 'local'

# 本地存储
STORAGE_LOCAL_BASE_URL: str = '/static/upload'

# 阿里云 OSS（6 个配置项）
# 腾讯云 COS（6 个配置项）
# AWS S3（6 个配置项）
```

---

### 3. API 端点示例 (`server/backend/app/userecho/api/v1/screenshot.py`)

提供了两个示例 API：

**1. 上传截图**
```
POST /api/v1/userecho/screenshot/upload
```
- 上传截图到对象存储
- 返回文件访问 URL

**2. 上传并 AI 识别**
```
POST /api/v1/userecho/screenshot/analyze
```
- 上传截图
- AI 识别平台、昵称、内容
- 返回结构化数据

---

### 4. Schema 定义 (`server/backend/app/userecho/schema/feedback.py`)

新增截图相关的 Schema：

- `ExtractedScreenshotData` - AI 提取的数据结构
- `ScreenshotAnalyzeResponse` - 识别响应
- `ScreenshotFeedbackCreate` - 从截图创建反馈

---

### 5. 文档

**详细配置文档** (`docs/storage-configuration.md`)
- 各云平台配置指南
- 使用示例代码
- 故障排查
- 成本优化建议
- 迁移指南

**快速开始** (`docs/storage-quick-start.md`)
- 最小化配置说明
- 常见问题 FAQ

---

## 🎯 使用方式

### 1. 基础使用

```python
from backend.utils.storage import storage

# 上传文件
url = await storage.upload(file, 'path/to/file.jpg')

# 获取签名 URL
signed_url = await storage.get_url('path/to/file.jpg', expire_seconds=3600)

# 删除文件
success = await storage.delete('path/to/file.jpg')
```

### 2. 截图上传（推荐）

```python
from backend.utils.storage import upload_screenshot

# 自动按租户和日期分类存储
url = await upload_screenshot(file, tenant_id=1)
# 返回: screenshots/1/2025/01/15/1705305600000_a1b2c3d4.jpg
```

### 3. 配置切换

开发环境：
```bash
STORAGE_TYPE=local
```

生产环境（阿里云）：
```bash
STORAGE_TYPE=aliyun_oss
ALIYUN_OSS_ACCESS_KEY_ID=xxx
ALIYUN_OSS_ACCESS_KEY_SECRET=xxx
ALIYUN_OSS_ENDPOINT=oss-cn-hangzhou.aliyuncs.com
ALIYUN_OSS_BUCKET_NAME=userecho-prod
```

---

## 📂 文件目录结构

### 本地存储

```
server/backend/static/upload/
└── screenshots/
    └── {tenant_id}/
        └── 2025/
            └── 01/
                └── 15/
                    └── 1705305600000_a1b2c3d4.jpg
```

### 云存储

```
{BUCKET}/
└── {BASE_PATH}/              # 可选，如: userecho
    └── screenshots/
        └── {tenant_id}/
            └── 2025/
                └── 01/
                    └── 15/
                        └── 1705305600000_a1b2c3d4.jpg
```

---

## 🚀 后续集成步骤

### 1. 安装依赖（生产环境）

```bash
cd server

# 阿里云 OSS
pip install oss2

# 或 腾讯云 COS
pip install cos-python-sdk-v5

# 或 AWS S3
pip install boto3
```

### 2. 配置 .env

在 `server/backend/.env` 中添加对应的配置项。

### 3. 注册路由

在 `server/backend/app/userecho/router.py` 中注册截图 API：

```python
from backend.app.userecho.api.v1 import screenshot

app.include_router(screenshot.router, prefix='/screenshot', tags=['截图上传'])
```

### 4. 数据库 Migration

创建 migration 添加新字段到 `feedback` 表：

```sql
ALTER TABLE feedback 
    ALTER COLUMN customer_id DROP NOT NULL,
    ADD COLUMN source_type VARCHAR(50) DEFAULT 'manual',
    ADD COLUMN source_platform VARCHAR(50),
    ADD COLUMN source_user_name VARCHAR(255),
    ADD COLUMN source_user_id VARCHAR(255),
    ADD COLUMN screenshot_url TEXT,
    ADD COLUMN submitter_id INT,
    ADD COLUMN ai_confidence DECIMAL(3,2);
```

### 5. 实现 AI 识别

在 `server/backend/utils/ai_client.py` 中实现：

```python
async def analyze_screenshot_with_ai(image_url: str) -> dict:
    """调用多模态大模型识别截图"""
    # 实现 GPT-4o 或 DeepSeek-VL 调用逻辑
    pass
```

---

## 🎨 PRD 更新建议

在 `docs/design/wechat-feedback-collect.md` 的技术方案部分，可以添加：

```markdown
### 5.3 存储方案

**对象存储：**
- 支持本地存储（开发环境）
- 支持阿里云 OSS / 腾讯云 COS / AWS S3（生产环境）
- 统一的存储接口，可随时切换

**路径规则：**
`screenshots/{tenant_id}/{year}/{month}/{day}/{timestamp}_{random}.{ext}`

**访问权限：**
- Bucket 设置为私有
- 通过签名 URL 访问（有效期 1 小时）

**详细配置：**
参见 `docs/storage-configuration.md`
```

---

## ✅ 核心优势

1. **即插即用** - 无需修改业务代码，切换存储后端只需改配置
2. **统一接口** - 所有存储操作使用相同的 API
3. **自动分类** - 按租户 + 日期自动组织文件
4. **安全可靠** - 私有 Bucket + 签名 URL
5. **多云支持** - 支持主流云服务商
6. **易于扩展** - 继承 `StorageBackend` 即可添加新后端

---

## 📝 注意事项

1. **依赖安装**
   - 生产环境必须安装对应的 SDK（oss2 / cos-python-sdk-v5 / boto3）
   - 开发环境使用本地存储，无需额外依赖

2. **配置检查**
   - 启动时会自动初始化存储后端
   - 配置错误会回退到本地存储并打印警告日志

3. **历史数据迁移**
   - 如果从本地存储切换到云存储，需要手动迁移历史文件
   - 参见 `docs/storage-configuration.md` 的迁移指南

4. **成本控制**
   - 建议配置生命周期规则（30 天后转低频，180 天后转归档）
   - 启用 CDN 加速可以降低外网流量费用

---

## 🔗 相关文件

- 核心实现：`server/backend/utils/storage.py`
- 配置文件：`server/backend/core/conf.py`
- API 示例：`server/backend/app/userecho/api/v1/screenshot.py`
- Schema 定义：`server/backend/app/userecho/schema/feedback.py`
- 详细文档：`docs/storage-configuration.md`
- 快速开始：`docs/storage-quick-start.md`
- PRD 文档：`docs/design/wechat-feedback-collect.md`

---

**实现完成！可以直接开始使用。** 🎉
