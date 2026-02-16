# 中国版 Canny 技术改造方案

> **目标**: 在现有架构基础上,以最小改动实现公开反馈门户、路线图和更新日志功能。

---

## 一、现状分析

### 1.1 当前技术栈

#### 前端
- **框架**: Vue 3 + Vite
- **UI 库**: Ant Design Vue (Vben Admin)
- **状态管理**: Pinia
- **路由**: Vue Router
- **构建工具**: Turbo (Monorepo)

#### 后端
- **框架**: FastAPI (Python)
- **数据库**: PostgreSQL + pgvector
- **ORM**: SQLAlchemy 2.0
- **认证**: JWT
- **任务队列**: Celery

#### 部署
- **容器化**: Docker + Docker Compose
- **数据库迁移**: Alembic

### 1.2 现有模块结构

```
userecho/
├── front/
│   ├── apps/
│   │   └── web-antd/          # Admin 管理后台
│   └── packages/              # 共享组件库
└── server/
    └── backend/
        └── app/
            ├── admin/         # Admin API
            └── userecho/      # 核心业务逻辑
                ├── api/       # 现有 API 路由
                ├── model/     # 数据模型
                ├── schema/    # Pydantic Schema
                ├── crud/      # 数据库操作
                └── service/   # 业务逻辑
```

### 1.3 核心痛点
1. **无公开访问入口**: 现有前端完全是 Admin 后台,无法对外开放
2. **认证体系单一**: 仅支持 Admin JWT,无 C 端用户认证
3. **数据隔离不足**: Topic 无「公开/私有」标识
4. **缺少 Changelog**: 无产品更新日志模块

---

## 二、技术改造方案

### 2.1 整体架构设计

采用 **「双应用 + 单后端」** 架构:

```
┌─────────────────────────────────────────────────────┐
│                    前端层 (Frontend)                  │
├─────────────────────────────────────────────────────┤
│  web-antd (Admin)          │  web-portal (Public)   │
│  - Ant Design Vue          │  - TailwindCSS         │
│  - 内部管理功能             │  - 公开访问页面         │
│  - Admin JWT 认证          │  - 微信/邮箱登录        │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│                   后端层 (Backend)                    │
├─────────────────────────────────────────────────────┤
│  /api/admin/*              │  /api/public/*         │
│  - 需要 Admin 权限          │  - 公开/可选认证        │
│  - 完整 CRUD 操作          │  - 只读为主             │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│                  数据层 (Database)                    │
│  PostgreSQL + pgvector                              │
│  - topics (新增 is_public, public_slug)             │
│  - changelogs (新表)                                │
│  - end_users (新表,C 端用户)                         │
└─────────────────────────────────────────────────────┘
```

---

## 三、前端改造方案

### 3.1 新建 `web-portal` 应用

#### 技术选型
- **框架**: Vue 3 + Vite (与 web-antd 保持一致)
- **UI**: **TailwindCSS**(区别于 Ant Design,打造 Canny 风格)
- **路由**: Vue Router
- **状态**: Pinia
- **SEO**: 
  - 方案 A: Vite SSG (推荐,静态生成)
  - 方案 B: Nuxt.js (完整 SSR,成本高)

#### 目录结构
```
front/apps/web-portal/
├── src/
│   ├── assets/           # 静态资源
│   ├── components/       # 公共组件
│   │   ├── RoadmapCard.vue
│   │   ├── ChangelogItem.vue
│   │   └── VoteButton.vue
│   ├── layouts/          # 布局
│   │   └── PublicLayout.vue
│   ├── pages/            # 页面
│   │   ├── Roadmap.vue
│   │   ├── Changelog.vue
│   │   ├── FeedbackBoard.vue  # Phase 2
│   │   └── Login.vue          # Phase 2
│   ├── router/           # 路由配置
│   ├── stores/           # Pinia Store
│   ├── api/              # API 调用
│   └── main.ts
├── index.html
├── vite.config.ts
├── tailwind.config.js
└── package.json
```

#### 核心页面设计

**1. 公开路线图 (`/roadmap`)**
```vue
<template>
  <PublicLayout>
    <div class="roadmap-container">
      <!-- 筛选器 -->
      <FilterBar v-model:category="category" />
      
      <!-- Kanban 看板 -->
      <div class="kanban-board">
        <KanbanColumn title="计划中" :topics="plannedTopics" />
        <KanbanColumn title="进行中" :topics="inProgressTopics" />
        <KanbanColumn title="已完成" :topics="completedTopics" />
      </div>
    </div>
  </PublicLayout>
</template>
```

**2. 更新日志 (`/changelog`)**
```vue
<template>
  <PublicLayout>
    <div class="changelog-container">
      <!-- 时间线视图 -->
      <div v-for="log in changelogs" :key="log.id" class="changelog-item">
        <h2>{{ log.title }}</h2>
        <div v-html="renderMarkdown(log.content)"></div>
        <div class="related-topics">
          <TopicTag v-for="topic in log.related_topics" :key="topic.id" />
        </div>
      </div>
    </div>
  </PublicLayout>
</template>
```

### 3.2 设计系统 (TailwindCSS)

#### 配置文件 `tailwind.config.js`
```js
export default {
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#f0f9ff',
          500: '#3b82f6',
          600: '#2563eb',
        },
        success: '#10b981',
        warning: '#f59e0b',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
}
```

#### 核心组件样式
```css
/* 投票按钮 */
.vote-button {
  @apply flex items-center gap-2 px-4 py-2 rounded-lg 
         bg-gray-100 hover:bg-primary-50 
         transition-all duration-200;
}

/* Topic 卡片 */
.topic-card {
  @apply p-6 bg-white rounded-xl shadow-sm 
         hover:shadow-md transition-shadow;
}
```

### 3.3 Monorepo 集成

#### 修改 `front/package.json`
```json
{
  "scripts": {
    "dev:portal": "pnpm -F @vben/web-portal run dev",
    "build:portal": "pnpm run build --filter=@vben/web-portal"
  }
}
```

#### 新增 `front/apps/web-portal/package.json`
```json
{
  "name": "@vben/web-portal",
  "version": "1.0.0",
  "scripts": {
    "dev": "vite",
    "build": "vite build"
  },
  "dependencies": {
    "vue": "catalog:",
    "vue-router": "catalog:",
    "pinia": "catalog:",
    "axios": "catalog:"
  },
  "devDependencies": {
    "tailwindcss": "catalog:",
    "autoprefixer": "catalog:"
  }
}
```

---

## 四、后端改造方案

### 4.1 数据模型扩展

#### 1. 修改 `Topic` 模型
**文件**: `server/backend/app/userecho/model/topic.py`

```python
class Topic(MappedBase):
    # ... 现有字段 ...
    
    # 新增字段
    is_public: Mapped[bool] = mapped_column(
        default=False,
        comment='是否公开显示'
    )
    public_slug: Mapped[str | None] = mapped_column(
        String(200),
        default=None,
        unique=True,
        comment='公开访问的 URL Slug (如: improve-search-performance)'
    )
```

#### 2. 新建 `Changelog` 模型
**文件**: `server/backend/app/userecho/model/changelog.py`

```python
from datetime import datetime
from sqlalchemy import ForeignKey, String, Text, Table, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship

# 多对多关联表
changelog_topic_association = Table(
    'changelog_topics',
    MappedBase.metadata,
    Column('changelog_id', String(36), ForeignKey('changelogs.id', ondelete='CASCADE')),
    Column('topic_id', String(36), ForeignKey('topics.id', ondelete='CASCADE')),
)

class Changelog(MappedBase):
    """产品更新日志"""
    __tablename__ = 'changelogs'
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey('tenants.id'))
    
    title: Mapped[str] = mapped_column(String(200), comment='标题')
    content: Mapped[str] = mapped_column(Text, comment='内容 (Markdown)')
    slug: Mapped[str | None] = mapped_column(String(200), comment='URL Slug')
    
    is_published: Mapped[bool] = mapped_column(default=False)
    published_at: Mapped[datetime | None] = mapped_column(TimeZone, default=None)
    
    view_count: Mapped[int] = mapped_column(default=0)
    
    created_time: Mapped[datetime] = mapped_column(TimeZone, default=timezone.now)
    updated_time: Mapped[datetime | None] = mapped_column(TimeZone, onupdate=timezone.now)
    
    # 关联 Topics
    related_topics: Mapped[list['Topic']] = relationship(
        'Topic',
        secondary=changelog_topic_association,
        backref='mentioned_in_changelogs'
    )
```

#### 3. 新建 `EndUser` 模型 (Phase 2)
**文件**: `server/backend/app/userecho/model/end_user.py`

```python
class EndUser(MappedBase):
    """C 端用户 (区别于 Admin)"""
    __tablename__ = 'end_users'
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey('tenants.id'))
    
    # 基础信息
    nickname: Mapped[str | None] = mapped_column(String(100))
    avatar_url: Mapped[str | None] = mapped_column(String(500))
    email: Mapped[str | None] = mapped_column(String(100), unique=True)
    
    # 微信登录
    wechat_openid: Mapped[str | None] = mapped_column(String(100), unique=True)
    wechat_unionid: Mapped[str | None] = mapped_column(String(100))
    
    # 统计
    vote_count: Mapped[int] = mapped_column(default=0)
    comment_count: Mapped[int] = mapped_column(default=0)
    
    created_time: Mapped[datetime] = mapped_column(TimeZone, default=timezone.now)
    last_login_time: Mapped[datetime | None] = mapped_column(TimeZone)
```

### 4.2 数据库迁移

#### 生成迁移文件
```bash
cd server/backend
alembic revision --autogenerate -m "add_public_fields_and_changelog"
```

#### 迁移文件示例
```python
def upgrade() -> None:
    # 1. 修改 topics 表
    op.add_column('topics', sa.Column('is_public', sa.Boolean(), server_default='false'))
    op.add_column('topics', sa.Column('public_slug', sa.String(200), nullable=True))
    op.create_index('ix_topics_public_slug', 'topics', ['public_slug'], unique=True)
    
    # 2. 创建 changelogs 表
    op.create_table('changelogs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('tenant_id', sa.String(36), sa.ForeignKey('tenants.id')),
        sa.Column('title', sa.String(200)),
        sa.Column('content', sa.Text()),
        # ... 其他字段
    )
    
    # 3. 创建关联表
    op.create_table('changelog_topics',
        sa.Column('changelog_id', sa.String(36), sa.ForeignKey('changelogs.id')),
        sa.Column('topic_id', sa.String(36), sa.ForeignKey('topics.id')),
    )
```

#### 执行迁移
```bash
alembic upgrade head
```

### 4.3 Public API 设计

#### 新建路由模块
**文件**: `server/backend/app/userecho/api/public.py`

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix='/public/v1', tags=['Public API'])

@router.get('/roadmap')
async def get_public_roadmap(
    category: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """获取公开路线图"""
    query = select(Topic).where(
        Topic.is_public == True,
        Topic.deleted_at == None
    )
    
    if category:
        query = query.where(Topic.category == category)
    
    topics = await db.execute(query)
    
    # 按状态分组
    return {
        'planned': [t for t in topics if t.status == 'planned'],
        'in_progress': [t for t in topics if t.status == 'in_progress'],
        'completed': [t for t in topics if t.status == 'completed'],
    }

@router.get('/changelog')
async def get_changelogs(
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
):
    """获取更新日志列表"""
    query = select(Changelog).where(
        Changelog.is_published == True
    ).order_by(Changelog.published_at.desc()).limit(limit)
    
    changelogs = await db.execute(query)
    return changelogs.scalars().all()

@router.get('/changelog/{slug}')
async def get_changelog_detail(
    slug: str,
    db: AsyncSession = Depends(get_db),
):
    """获取单个日志详情"""
    changelog = await db.execute(
        select(Changelog).where(Changelog.slug == slug)
    )
    
    if not changelog:
        raise HTTPException(404, "Changelog not found")
    
    # 增加浏览量
    changelog.view_count += 1
    await db.commit()
    
    return changelog
```

#### 注册路由
**文件**: `server/backend/app/userecho/api/__init__.py`

```python
from .public import router as public_router

def register_routers(app):
    app.include_router(public_router)  # 无需认证
    # ... 其他路由
```

### 4.4 认证体系扩展 (Phase 2)

#### 微信登录流程
```python
# server/backend/app/userecho/api/auth.py

@router.get('/auth/wechat/login')
async def wechat_login_url():
    """生成微信登录 URL"""
    redirect_uri = f"{settings.DOMAIN}/api/public/v1/auth/wechat/callback"
    url = (
        f"https://open.weixin.qq.com/connect/qrconnect?"
        f"appid={settings.WECHAT_APPID}&"
        f"redirect_uri={redirect_uri}&"
        f"response_type=code&"
        f"scope=snsapi_login"
    )
    return {"url": url}

@router.get('/auth/wechat/callback')
async def wechat_callback(code: str, db: AsyncSession = Depends(get_db)):
    """微信回调处理"""
    # 1. 用 code 换取 access_token
    token_resp = await wechat_get_access_token(code)
    
    # 2. 获取用户信息
    user_info = await wechat_get_userinfo(token_resp['access_token'])
    
    # 3. 创建或更新 EndUser
    user = await get_or_create_end_user(
        wechat_openid=user_info['openid'],
        nickname=user_info['nickname'],
        avatar_url=user_info['headimgurl']
    )
    
    # 4. 生成 JWT
    token = create_end_user_jwt(user.id)
    
    return {"access_token": token, "user": user}
```

---

## 五、部署方案

### 5.1 开发环境

#### 启动前端
```bash
# Terminal 1: Admin 后台
cd front
pnpm dev:antd

# Terminal 2: 公开门户
pnpm dev:portal
```

#### 启动后端
```bash
cd server/backend
python run.py
```

### 5.2 生产环境

#### Nginx 配置
```nginx
server {
    listen 80;
    server_name yourdomain.com;
    
    # 公开门户
    location / {
        root /var/www/web-portal/dist;
        try_files $uri $uri/ /index.html;
    }
    
    # Admin 后台
    location /admin {
        root /var/www/web-antd/dist;
        try_files $uri $uri/ /admin/index.html;
    }
    
    # API
    location /api {
        proxy_pass http://backend:8000;
    }
}
```

#### Docker Compose
```yaml
services:
  backend:
    build: ./server
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://...
  
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./front/apps/web-portal/dist:/var/www/web-portal/dist
      - ./front/apps/web-antd/dist:/var/www/web-antd/dist
      - ./nginx.conf:/etc/nginx/conf.d/default.conf
```

---

## 六、开发计划

### Week 1: 基础设施
- [ ] 数据库 Schema 变更
- [ ] 初始化 `web-portal` 应用
- [ ] 配置 TailwindCSS
- [ ] 搭建 Public API 路由

### Week 2: 公开路线图
- [ ] 实现 Roadmap 页面
- [ ] Kanban 组件开发
- [ ] API 对接与测试

### Week 3: 更新日志
- [ ] 实现 Changelog 页面
- [ ] Admin 后台增加 Changelog 管理
- [ ] Markdown 渲染与 SEO 优化

---

## 七、技术风险与缓解

| 风险 | 影响 | 缓解方案 |
|------|------|---------|
| Monorepo 构建复杂度增加 | 🟡 中 | 使用 Turbo 缓存,隔离构建 |
| TailwindCSS 学习成本 | 🟢 低 | 参考 Canny 设计,复用组件 |
| 数据库迁移失败 | 🔴 高 | 本地充分测试,备份生产数据 |
| 微信登录审核不通过 | 🟡 中 | 同步开发邮箱登录备选 |
| SEO 效果不佳 | 🟡 中 | 使用 Vite SSG 预渲染 |

---

## 八、性能优化

### 8.1 前端优化
- **代码分割**: 路由懒加载
- **图片优化**: WebP 格式 + CDN
- **缓存策略**: Service Worker

### 8.2 后端优化
- **查询优化**: 使用 `selectinload` 预加载关联数据
- **缓存**: Redis 缓存公开 API 响应
- **限流**: 公开 API 添加 Rate Limit

```python
from slowapi import Limiter

limiter = Limiter(key_func=get_remote_address)

@router.get('/roadmap')
@limiter.limit("30/minute")  # 每分钟最多 30 次
async def get_public_roadmap(...):
    ...
```

---

## 九、监控与日志

### 9.1 关键指标
- 公开页面 PV/UV
- API 响应时间
- 用户注册/登录成功率
- 投票/评论数量

### 9.2 日志收集
```python
import structlog

logger = structlog.get_logger()

@router.get('/roadmap')
async def get_public_roadmap(...):
    logger.info("public_roadmap_accessed", 
                category=category, 
                user_agent=request.headers.get('user-agent'))
    ...
```

---

## 十、总结

### 核心原则
1. **最小改动**: 复用现有架构,避免大规模重构
2. **渐进式**: 先 MVP,再迭代
3. **隔离性**: 公开门户与 Admin 完全隔离

### 技术亮点
1. **双应用架构**: 清晰分离 Admin 与 Public
2. **TailwindCSS**: 快速打造 Canny 风格
3. **微信生态**: 深度适配中国市场

### 下一步
1. Review 本方案
2. 执行数据库迁移
3. 初始化 `web-portal` 应用

---

**文档维护者**: 技术团队  
**最后更新**: 2025-12-30
