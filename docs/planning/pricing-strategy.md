# 回响（Echo）商业化计费策略

> **版本:** v1.0  
> **更新日期:** 2026-01-13  
> **状态:** 规划中

---

## 一、定价方案

### 套餐设计

| 版本 | 席位 | 月付价格 | 年付价格 | 定位 |
|-----|------|---------|---------|------|
| **启航版** | 1 人 | ¥99/月 | ¥79/月（约 ¥948/年） | 个人 PM / 独立创业者 |
| **专业版** | 3 人 | ¥199/月 | ¥159/月（约 ¥1,908/年） | 小型产品团队 |
| **旗舰版** | 10 人 | ¥599/月 | ¥479/月（约 ¥5,748/年） | 中型企业团队 |
| **企业版** | 不限 | 定制报价 | 定制报价 | 大型企业 |

### 各版本功能对比

| 功能 | 启航版 | 专业版 | 旗舰版 | 企业版 |
|-----|-------|-------|-------|-------|
| **席位数** | 1 | 3 | 10 | 不限 |
| **反馈存储** | 1,000 条 | 10,000 条 | 100,000 条 | 不限 |
| **AI 聚类** | ✅ | ✅ | ✅ | ✅ |
| **截图识别** | ✅ | ✅ | ✅ | ✅ |
| **优先级评分** | ✅ | ✅ | ✅ | ✅ |
| **洞察报告** | 基础 | 完整 | 完整 | 高级 |
| **数据导出** | CSV | CSV/Excel | CSV/Excel/API | 完整 |
| **客户管理** | 基础 | 完整 | 高级 | 高级 |
| **专属客服** | ❌ | 邮件 | 工作日响应 | 7×24 |
| **私有部署** | ❌ | ❌ | ❌ | ✅ |
| **SSO/SAML** | ❌ | ❌ | ❌ | ✅ |

---

## 二、AI 额度管理策略

### 核心原则

1. **初期不限制** - MVP 阶段不设硬性限制，鼓励用户充分体验
2. **后台统计** - 记录每个租户的 AI 使用量，为后续计费提供数据支撑
3. **设置软上限** - 当使用量异常时触发告警，防止滥用

### AI 使用量计量单位

| AI 操作 | 计量单位 | 说明 |
|--------|---------|------|
| **反馈聚类** | 1 次 / 批次 | 每次聚类操作计为 1 次 |
| **截图识别** | 1 次 / 张 | 每张截图识别计为 1 次 |
| **主题标题生成** | 1 次 / 主题 | AI 自动生成标题计为 1 次 |
| **洞察报告生成** | 5 次 / 份 | 每份报告计为 5 次 |
| **Embedding 生成** | 0.1 次 / 条 | 10 条反馈的 Embedding 计为 1 次 |

### 各版本额度上限（预留）

| 版本 | 月度 AI 额度上限 | 超额处理 |
|-----|-----------------|---------|
| 启航版 | 500 次 | 提示升级 |
| 专业版 | 2,000 次 | 提示升级 |
| 旗舰版 | 10,000 次 | 提示联系客服 |
| 企业版 | 不限 | - |

> **注意**：初期阶段不强制限制，仅记录使用量并在控制台展示，用户超额后给予友好提示。

---

## 三、技术实现方案

### 3.1 数据模型设计

#### 新增表：`ai_usage_log`

记录每次 AI 调用的详细日志：

```sql
CREATE TABLE ai_usage_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES sys_tenant(id),
    user_id UUID REFERENCES sys_user(id),          -- 操作用户（可选）
    operation_type VARCHAR(50) NOT NULL,           -- 操作类型：clustering, screenshot, embedding, insight
    credits_used DECIMAL(10, 2) NOT NULL,          -- 消耗的额度
    metadata JSONB,                                 -- 额外信息（如处理的反馈数量）
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 索引
CREATE INDEX idx_ai_usage_tenant_date ON ai_usage_log(tenant_id, created_at);
CREATE INDEX idx_ai_usage_operation ON ai_usage_log(operation_type);
```

#### 新增表：`tenant_ai_quota`

记录租户的额度配置和使用汇总：

```sql
CREATE TABLE tenant_ai_quota (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL UNIQUE REFERENCES sys_tenant(id),
    plan_type VARCHAR(20) NOT NULL DEFAULT 'starter',  -- starter, pro, team, enterprise
    monthly_limit INTEGER NOT NULL DEFAULT 500,         -- 月度额度上限
    current_month_usage DECIMAL(10, 2) DEFAULT 0,       -- 当月已使用额度
    last_reset_at TIMESTAMP WITH TIME ZONE,             -- 上次重置时间
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### 3.2 后端服务设计

#### 额度管理服务：`ai_quota_service.py`

```python
class AIQuotaService:
    """AI 额度管理服务"""

    # 操作类型与额度消耗映射
    CREDIT_COSTS = {
        "clustering": 1.0,       # 每次聚类
        "screenshot": 1.0,       # 每张截图识别
        "topic_title": 1.0,      # 每次标题生成
        "insight_report": 5.0,   # 每份洞察报告
        "embedding": 0.1,        # 每条 Embedding
    }

    async def record_usage(
        self,
        tenant_id: str,
        operation_type: str,
        count: int = 1,
        metadata: dict = None
    ) -> None:
        """记录 AI 使用量"""
        pass

    async def get_usage_summary(
        self,
        tenant_id: str,
        start_date: date = None,
        end_date: date = None
    ) -> dict:
        """获取使用量汇总"""
        pass

    async def check_quota(
        self,
        tenant_id: str,
        operation_type: str,
        count: int = 1
    ) -> tuple[bool, str]:
        """检查额度是否充足（返回是否充足 + 提示信息）"""
        pass
```

### 3.3 需要修改的 AI 调用点

| 文件 | 调用类型 | 改动说明 |
|-----|---------|---------|
| `clustering_service.py` | clustering | 聚类完成后记录 1 次 |
| `clustering_service.py` | embedding | Embedding 生成时按条数记录 |
| `clustering_service.py` | topic_title | 生成标题时记录 |
| `feedback.py` (截图识别) | screenshot | 每张截图识别记录 1 次 |
| `insight_service.py` | insight_report | 生成洞察报告时记录 |

### 3.4 API 设计

#### 获取额度使用情况

```
GET /api/v1/app/ai-quota/usage
```

响应示例：
```json
{
  "plan_type": "pro",
  "monthly_limit": 2000,
  "current_usage": 156.5,
  "remaining": 1843.5,
  "usage_percentage": 7.8,
  "reset_date": "2026-02-01",
  "breakdown": {
    "clustering": 45,
    "screenshot": 23,
    "embedding": 78.5,
    "topic_title": 10
  }
}
```

---

## 四、实施计划

### 阶段一：统计基础设施（本次实现）

1. 创建数据库表 `ai_usage_log` 和 `tenant_ai_quota`
2. 实现 `AIQuotaService` 服务
3. 在 AI 调用点埋点
4. 实现额度查询 API

### 阶段二：前端展示（后续）

1. 设置页面添加额度使用卡片
2. 超额时的友好提示 UI
3. 管理员后台额度管理

### 阶段三：商业化上线（更后续）

1. 接入支付系统
2. 套餐升级/降级流程
3. 账单管理

---

## 五、验证计划

### 自动化测试

1. 单元测试：`AIQuotaService` 的核心方法
2. 集成测试：验证 AI 调用后额度正确记录

### 手动验证

1. 执行聚类操作，检查 `ai_usage_log` 是否有记录
2. 调用额度查询 API，验证返回数据正确
3. 模拟多次调用，验证汇总数据准确

---

## 六、附录

### 竞品定价参考

| 竞品 | 起步价 | 计费模式 |
|-----|-------|---------|
| Canny | $24/月 | 按活跃用户数 |
| UserVoice | $999/月 | 按终端用户数 |
| Productboard | $19/maker/月 | 按席位 |
| 共筑 | ¥199/月 | 固定月费 |

### 定价决策依据

- ¥99 是中国 SMB 用户的心理试错临界点
- 年付 8 折是行业标配
- 席位模式透明度高，企业易于预算

---

**文档维护者:** 产品团队  
**最后更新:** 2026-01-13
