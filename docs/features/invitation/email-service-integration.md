# 邀请系统 - 邮件服务集成总结

> **完成日期**: 2026-01-19  
> **状态**: ✅ 已完成

---

## 🎉 重要发现

项目**已有完整的邮件服务**！基于 `aiosmtplib` 的 SMTP 邮件发送系统，支持 Jinja2 模板渲染。

---

## 📧 邮件服务架构

### 现有基础设施

```
server/backend/plugin/email/
├── utils/
│   └── send.py                    # 邮件发送核心函数
├── templates/
│   ├── captcha.html               # 验证码模板（已有）
│   ├── weekly_report.html         # 周报模板（已有）
│   └── email_verification.html   # 邮箱验证模板（新增）
└── api/v1/
    └── email.py                   # 邮件 API
```

### 核心功能

1. **异步 SMTP 发送**：基于 `aiosmtplib`
2. **模板渲染**：使用 Jinja2 渲染 HTML 邮件
3. **动态配置加载**：从数据库加载邮件配置
4. **错误处理**：完善的日志记录

---

## ✅ 本次集成内容

### 1. 创建邮箱验证模板

**文件**：`server/backend/plugin/email/templates/email_verification.html`

**特性**：
- 🎨 现代化 UI 设计
- 📱 响应式布局
- 🔘 一键验证按钮
- 🔢 备用验证码输入
- 📋 权益说明卡片
- 💡 友好的提示信息

**模板变量**：
```python
{
    "nickname": "用户昵称",
    "code": "验证码",
    "verify_url": "验证链接",
    "plan_name": "套餐名称",
    "trial_days": 试用天数
}
```

### 2. 修改邮件验证服务

**文件**：`server/backend/app/userecho/service/email_verification_service.py`

**变更**：
```python
# 1. 新增导入
from backend.core.conf import settings
from backend.plugin.email.utils.send import send_email

# 2. 更新函数签名，支持传递邮件参数
async def create_verification(
    self, db: AsyncSession, 
    user_id: int, 
    email: str, 
    nickname: str = "", 
    plan_name: str = "专业版", 
    trial_days: int = 90
) -> EmailVerification:

# 3. 新增私有方法：发送验证邮件
async def _send_verification_email(
    self,
    db: AsyncSession,
    email: str,
    verification_code: str,
    nickname: str = "",
    plan_name: str = "专业版",
    trial_days: int = 90,
) -> None:
    """发送验证邮件（内部方法）"""
    verify_url = f"{settings.FRONTEND_URL}/auth/verify-email?code={verification_code}"
    
    await send_email(
        db,
        recipients=email,
        subject="验证邮箱 - 回响 UserEcho",
        content={
            "nickname": nickname or "用户",
            "code": verification_code,
            "verify_url": verify_url,
            "plan_name": plan_name or "专业版",
            "trial_days": trial_days or 90,
        },
        template="email_verification.html",
    )
```

**调用时机**：
1. 注册时创建验证记录 → 自动发送
2. 用户重发验证邮件 → 自动发送

### 3. 修改认证服务

**文件**：`server/backend/app/userecho/service/auth_service.py`

**变更**：
```python
# 注册时传递邮件参数
plan_name = "专业版" if invitation.plan_code == "pro" else "启航版"
verification = await email_verification_service.create_verification(
    db, user.id, email, nickname, plan_name, invitation.trial_days
)
```

### 4. 添加配置项

**文件**：`server/backend/core/conf.py`

**变更**：
```python
# 前端 URL（用于生成邮件中的验证链接）
FRONTEND_URL: str = "http://localhost:5173"
```

---

## 🔧 环境变量配置

需要在 `.env` 文件中配置以下变量：

```bash
# 邮件服务配置
EMAIL_USERNAME=your-email@example.com
EMAIL_PASSWORD=your-smtp-password
EMAIL_HOST=smtp.example.com
EMAIL_PORT=465
EMAIL_SSL=True

# 前端 URL（生产环境需修改）
FRONTEND_URL=https://userecho.example.com
```

### 支持的邮件服务商

| 服务商 | SMTP 服务器 | 端口 | SSL |
|--------|------------|------|-----|
| QQ邮箱 | smtp.qq.com | 465 | ✅ |
| 163邮箱 | smtp.163.com | 465 | ✅ |
| Gmail | smtp.gmail.com | 465 | ✅ |
| 阿里云邮件推送 | smtpdm.aliyun.com | 465 | ✅ |
| SendGrid | smtp.sendgrid.net | 587 | ❌ (TLS) |
| Resend | smtp.resend.com | 587 | ❌ (TLS) |

---

## 📧 邮件发送流程

### 注册流程

```
用户提交注册表单
  ↓
后端创建用户（email_verified=false）
  ↓
调用 email_verification_service.create_verification()
  ↓
生成验证码和过期时间
  ↓
保存到 email_verifications 表
  ↓
调用 _send_verification_email()
  ↓
构建验证链接和邮件内容
  ↓
调用 send_email() 发送邮件
  ↓
记录日志
  ↓
返回注册成功响应
```

### 重发流程

```
用户点击"重新发送"
  ↓
后端检查限流（1分钟）
  ↓
获取现有验证记录
  ↓
增加发送次数
  ↓
调用 _send_verification_email()
  ↓
发送邮件
  ↓
返回成功响应
```

---

## 📊 邮件内容示例

### 邮件主题
```
验证邮箱 - 回响 UserEcho
```

### 邮件内容结构
1. **Logo 和标题**：回响品牌标识
2. **欢迎语**：个性化称呼
3. **权益说明**：试用套餐详情
4. **验证按钮**：一键验证（主要方式）
5. **验证码**：备用验证方式
6. **帮助信息**：操作指南
7. **页脚**：法律声明和联系方式

---

## 🔍 测试方法

### 1. 本地测试（使用 QQ 邮箱）

```bash
# 1. 配置 .env
EMAIL_USERNAME=your-qq-email@qq.com
EMAIL_PASSWORD=your-auth-code  # 授权码，不是密码
EMAIL_HOST=smtp.qq.com
EMAIL_PORT=465
EMAIL_SSL=True
FRONTEND_URL=http://localhost:5173

# 2. 启动后端
cd server
source .venv/Scripts/activate
python run.py

# 3. 注册测试
# 访问前端注册页面：http://localhost:5173/auth/register-invite?invite=<token>
# 填写信息并提交

# 4. 检查邮箱
# 查看 QQ 邮箱收件箱
```

### 2. 日志验证

```bash
# 查看后端日志
tail -f server/logs/app.log

# 成功示例
INFO: Created email verification: user_id=123, email=test@example.com
INFO: Verification email sent to: test@example.com

# 失败示例
ERROR: Failed to send verification email to test@example.com: [Error details]
```

### 3. 数据库验证

```sql
-- 检查验证记录
SELECT * FROM email_verifications 
WHERE email = 'test@example.com' 
ORDER BY created_at DESC 
LIMIT 1;

-- 检查发送次数
SELECT send_count, last_sent_at 
FROM email_verifications 
WHERE user_id = 123;
```

---

## ⚠️ 注意事项

### 1. 邮件服务商限制

| 服务商 | 限制 | 建议 |
|--------|------|------|
| QQ邮箱 | 50封/天 | 仅用于测试 |
| 163邮箱 | 50封/天 | 仅用于测试 |
| Gmail | 500封/天 | 小规模使用 |
| 阿里云邮件推送 | 200封/天（免费） | 生产环境推荐 |
| SendGrid | 100封/天（免费） | 生产环境推荐 |
| Resend | 100封/月（免费） | 生产环境推荐 |

### 2. 授权码 vs 密码

**QQ/163 邮箱**：需要开启 SMTP 服务并生成授权码
- QQ邮箱：设置 → 账户 → POP3/IMAP/SMTP/Exchange/CardDAV/CalDAV服务
- 生成授权码后，用授权码作为 `EMAIL_PASSWORD`

**Gmail**：需要开启"允许不够安全的应用访问"或使用应用专用密码

### 3. 生产环境建议

**推荐方案**：
1. **阿里云邮件推送**
   - 高可靠性
   - 国内访问速度快
   - 价格合理
   - API 完善

2. **Resend**（如你所愿）
   - 现代化 API
   - 开发者友好
   - 免费额度充足
   - 文档完善

**配置示例（Resend）**：
```bash
EMAIL_HOST=smtp.resend.com
EMAIL_PORT=587
EMAIL_SSL=False  # 使用 TLS
EMAIL_USERNAME=resend  # 固定值
EMAIL_PASSWORD=re_xxxxxxxxxxxxx  # Resend API Key
```

### 4. 错误处理

邮件发送失败**不会阻断注册流程**：
- 失败时只记录日志
- 用户可以手动重发验证邮件
- 确保用户体验流畅

---

## 📈 监控指标

### 关键指标

1. **发送成功率**：`成功数 / 总发送数`
2. **平均发送时长**：SMTP 连接 + 发送时间
3. **重发频率**：用户点击重发的次数
4. **验证率**：`验证成功数 / 邮件发送数`

### 日志关键字

```bash
# 成功
grep "Verification email sent" logs/app.log

# 失败
grep "Failed to send verification email" logs/app.log

# 重发
grep "Resent verification email" logs/app.log
```

---

## 🚀 后续优化

### P1 - 短期优化

1. **邮件队列**：使用 Celery 异步发送
2. **发送失败重试**：3次重试机制
3. **邮件追踪**：记录打开率、点击率
4. **模板多语言**：支持英文版

### P2 - 中期优化

1. **邮件统计面板**：管理后台展示发送统计
2. **邮件模板管理**：可视化编辑邮件模板
3. **A/B 测试**：测试不同邮件内容效果
4. **用户偏好**：支持用户选择邮件语言和频率

---

## 📚 相关文档

- [项目邮件服务文档](../../guides/development/logging-best-practices.md)
- [Resend 官方文档](https://resend.com/docs)
- [阿里云邮件推送文档](https://help.aliyun.com/product/29412.html)
- [aiosmtplib 文档](https://aiosmtplib.readthedocs.io/)

---

## ✅ 完成度总结

| 功能 | 状态 | 备注 |
|------|------|------|
| 邮件模板创建 | ✅ 100% | 精美的 HTML 模板 |
| 邮件发送集成 | ✅ 100% | 完全集成到服务层 |
| 配置项添加 | ✅ 100% | FRONTEND_URL 已添加 |
| 错误处理 | ✅ 100% | 完善的日志记录 |
| 重发机制 | ✅ 100% | 1分钟限流 |
| 代码质量 | ✅ 100% | Ruff + Mypy 通过 |

**总体完成度：100%** 🎉

---

**实现者**: Linus  
**版本**: v1.0  
**最后更新**: 2026-01-19
