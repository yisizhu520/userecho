# 聚类配置系统测试指南

## 测试概述

本指南用于验证租户配置系统和聚类配置功能的正确性。

## 前置准备

### 1. 数据库迁移

```bash
cd server
source .venv/Scripts/activate
alembic upgrade head
```

确认 `userecho_tenant_config` 表创建成功。

### 2. 启动服务

```bash
# 后端服务
cd server
python run.py

# 前端服务
cd front
pnpm dev
```

## 测试场景

### 场景 1：新租户使用默认配置

**目标**：验证新租户在没有配置时使用系统默认配置（standard 预设）

**步骤**：
1. 使用新租户账号登录
2. 触发聚类任务：`POST /api/v1/app/clustering/trigger`
3. 检查日志输出

**预期结果**：
- 日志显示：`Using clustering config for tenant xxx: preset=standard`
- 聚类使用以下参数：
  - `similarity_threshold`: 0.85
  - `min_samples`: 2
  - `min_silhouette`: 0.3
  - `max_noise_ratio`: 0.5

### 场景 2：查看预设模式列表

**目标**：验证 API 返回正确的预设模式信息

**步骤**：
```bash
GET /api/v1/app/config/clustering/presets
```

**预期结果**：
```json
{
  "code": 200,
  "data": {
    "strict": {
      "display_name": "严格聚类",
      "description": "只将高度相似的反馈聚在一起...",
      "use_case": "适用于：产品初期..."
    },
    "standard": {
      "display_name": "标准聚类",
      "description": "平衡聚类质量和覆盖范围...",
      "use_case": "适用于：日常使用..."
    },
    "relaxed": {
      "display_name": "宽松聚类",
      "description": "尽可能将相似反馈聚在一起...",
      "use_case": "适用于：反馈量大..."
    }
  }
}
```

### 场景 3：获取当前配置

**目标**：验证租户配置读取功能

**步骤**：
```bash
GET /api/v1/app/config/clustering
```

**预期结果（首次调用）**：
```json
{
  "code": 200,
  "data": {
    "preset_mode": "standard",
    "similarity_threshold": 0.85,
    "min_samples": 2,
    "min_silhouette": 0.3,
    "max_noise_ratio": 0.5
  }
}
```

### 场景 4：切换到严格模式

**目标**：验证预设模式切换功能

**步骤**：
```bash
POST /api/v1/app/config/clustering/preset
Content-Type: application/json

{
  "preset_mode": "strict"
}
```

**预期结果**：
```json
{
  "code": 200,
  "data": {
    "preset_mode": "strict",
    "similarity_threshold": 0.90,
    "min_samples": 3,
    "min_silhouette": 0.4,
    "max_noise_ratio": 0.6
  }
}
```

**验证**：
1. 再次调用 `GET /api/v1/app/config/clustering`，确认配置已更新
2. 触发聚类任务，检查日志显示使用 strict 预设
3. 检查数据库 `userecho_tenant_config` 表，确认记录存在

### 场景 5：预览配置效果

**目标**：验证预览功能

**前提**：租户至少有 2 条未聚类的反馈

**步骤**：
```bash
POST /api/v1/app/config/clustering/preview
Content-Type: application/json

{
  "preset_mode": "relaxed"
}
```

**预期结果（数据充足时）**：
```json
{
  "code": 200,
  "data": {
    "status": "success",
    "test_samples": 20,
    "preview": {
      "clusters_count": 3,
      "clusters_range": "2-5",
      "coverage_rate": 0.75,
      "coverage_percentage": "75%",
      "quality_rating": "良好",
      "silhouette_score": 0.45,
      "noise_ratio": 0.25
    },
    "config": {
      "similarity_threshold": 0.75,
      "min_samples": 2,
      "min_silhouette": 0.2,
      "max_noise_ratio": 0.7
    }
  }
}
```

**预期结果（数据不足时）**：
```json
{
  "code": 200,
  "data": {
    "status": "insufficient_data",
    "message": "测试数据不足（至少需要2条反馈）",
    "test_samples": 0
  }
}
```

### 场景 6：前端配置页面测试

**目标**：验证前端配置界面的完整流程

**步骤**：
1. 访问 `http://localhost:5173/app/settings/clustering`
2. 检查页面是否正确显示当前配置和三个预设模式
3. 选择不同的预设模式（如 "严格聚类"）
4. 点击"预览效果"按钮
5. 确认预览结果正确显示
6. 点击"保存设置"按钮
7. 确认显示成功消息："配置已更新"
8. 刷新页面，确认配置已持久化

**预期结果**：
- 页面流畅，无 JavaScript 错误
- 预设模式切换时，按钮状态正确（保存按钮启用/禁用）
- 预览结果以卡片形式显示，包含：
  - 预计形成簇数
  - 预计覆盖率
  - 聚类质量标签（颜色编码）
  - 测试样本数

### 场景 7：多租户隔离测试

**目标**：验证租户配置互不影响

**步骤**：
1. 租户 A 登录，设置为 "严格聚类"
2. 租户 B 登录，设置为 "宽松聚类"
3. 租户 A 再次登录，触发聚类

**预期结果**：
- 租户 A 的聚类使用 strict 配置
- 租户 B 的聚类使用 relaxed 配置
- 两者互不干扰

### 场景 8：配置缓存测试

**目标**：验证配置缓存功能

**步骤**：
1. 租户 A 获取配置（首次，从数据库读取）
2. 租户 A 再次获取配置（应从缓存读取）
3. 租户 A 更新配置
4. 租户 A 再次获取配置（缓存应已清除，重新读取数据库）

**验证**：
- 检查后端日志，确认缓存命中/未命中
- 性能：缓存命中时响应更快

### 场景 9：聚类效果对比

**目标**：验证不同配置对聚类结果的影响

**前提**：准备 20+ 条相似度不同的反馈

**步骤**：
1. 使用 "宽松聚类" 执行聚类，记录结果（簇数、噪声率）
2. 清空聚类状态：将所有反馈的 `clustering_status` 改回 `pending`
3. 切换到 "严格聚类"
4. 再次执行聚类，记录结果

**预期结果**：
- 宽松模式：形成更多簇，噪声率较低
- 严格模式：形成较少簇，噪声率较高（因为阈值更高）

## 回归测试

### 向后兼容性

**目标**：确保现有系统在没有配置时仍能正常工作

**步骤**：
1. 删除测试租户的配置记录：
   ```sql
   DELETE FROM userecho_tenant_config WHERE tenant_id = 'test-tenant-id';
   ```
2. 触发聚类任务

**预期结果**：
- 聚类正常执行
- 使用系统默认配置（standard 预设）
- 不会报错

## 性能测试

### 配置读取性能

**目标**：验证缓存机制的有效性

**步骤**：
1. 并发 100 次调用 `GET /api/v1/app/config/clustering`
2. 测量平均响应时间

**预期结果**：
- 首次调用：< 50ms
- 缓存命中：< 10ms
- 无数据库连接池耗尽错误

## 故障恢复测试

### 数据库不可用

**目标**：验证数据库异常时的降级行为

**步骤**：
1. 停止数据库
2. 触发聚类任务

**预期结果**：
- 聚类任务失败，但不会崩溃
- 日志记录错误信息
- 返回友好的错误消息

## 测试通过标准

- [ ] 所有 API 端点返回正确的状态码和数据结构
- [ ] 预设模式切换生效，聚类参数正确应用
- [ ] 预览功能准确反映配置效果
- [ ] 前端页面无 UI bug，交互流畅
- [ ] 多租户配置隔离正常
- [ ] 配置缓存正常工作
- [ ] 不同配置对聚类结果有可见影响
- [ ] 向后兼容：无配置时使用默认值
- [ ] 数据库迁移脚本执行成功

## 测试完成后

1. 检查日志文件，确认无错误或警告
2. 验证数据库数据一致性
3. 清理测试数据（如需要）
4. 记录测试结果和发现的问题

## 常见问题排查

### 问题 1：预览一直返回 "数据不足"

**原因**：租户没有未聚类的反馈

**解决**：
1. 导入一些测试反馈
2. 或者将现有反馈的 `clustering_status` 改为 `pending`

### 问题 2：配置更新后聚类仍使用旧配置

**原因**：配置缓存未清除

**解决**：
1. 检查 `tenant_config_service._clear_cache()` 是否被正确调用
2. 重启后端服务以清空内存缓存

### 问题 3：前端页面无法加载预设列表

**原因**：API 路由未正确注册

**解决**：
1. 检查 `server/backend/app/userecho/api/router.py` 是否包含 `tenant_config.router`
2. 重启后端服务
