# UserEcho 路由设计规范

> **版本:** v1.0  
> **更新日期:** 2025-12-22  
> **核心原则:** 通过路由前缀隔离系统管理和业务功能

---

## 一、路由前缀规范

### 核心设计

```text
/admin/*  - 系统管理区（平台管理员）
/app/*    - 业务功能区（租户用户）
```

**为什么这样设计？**
- ✅ **简洁** - 只需判断 2 个前缀，消除复杂的路径列表维护
- ✅ **清晰** - 一眼看出这是系统功能还是业务功能
- ✅ **扩展性强** - 新增功能只需加在对应前缀下
- ✅ **安全** - 后端通过前缀强制过滤，前端无法绕过

---

## 二、完整路由映射表

### 2.1 系统管理路由 (`/admin/*`)

**适用角色：** 超级管理员、系统管理员

| 路由路径 | 组件路径 | 菜单名称 | 权限标识 |
|---------|---------|---------|---------|
| `/admin/system/dept` | `/views/system/dept/index.vue` | 部门管理 | `sys:dept:view` |
| `/admin/system/user` | `/views/system/user/index.vue` | 用户管理 | `sys:user:view` |
| `/admin/system/role` | `/views/system/role/index.vue` | 角色管理 | `sys:role:view` |
| `/admin/system/menu` | `/views/system/menu/index.vue` | 菜单管理 | `sys:menu:view` |
| `/admin/system/data-scope` | `/views/system/data-permission/scope/index.vue` | 数据范围 | `sys:data:scope:view` |
| `/admin/system/data-rule` | `/views/system/data-permission/rule/index.vue` | 数据规则 | `sys:data:rule:view` |
| `/admin/system/plugin` | `/views/system/plugin/index.vue` | 插件管理 | `sys:plugin:view` |
| `/admin/log/login` | `/views/log/login/index.vue` | 登录日志 | `sys:log:login:view` |
| `/admin/log/opera` | `/views/log/opera/index.vue` | 操作日志 | `sys:log:opera:view` |
| `/admin/monitor/online` | `/views/monitor/online/index.vue` | 在线用户 | `sys:monitor:online:view` |
| `/admin/monitor/redis` | `/views/monitor/redis/index.vue` | Redis 监控 | `sys:monitor:redis:view` |
| `/admin/monitor/server` | `/views/monitor/server/index.vue` | 服务器监控 | `sys:monitor:server:view` |
| `/admin/scheduler/manage` | `/views/scheduler/manage/index.vue` | 任务管理 | `sys:scheduler:manage` |
| `/admin/scheduler/record` | `/views/scheduler/record/index.vue` | 任务记录 | `sys:scheduler:record` |

---

### 2.2 业务功能路由 (`/app/*`)

**适用角色：** PM、CS、开发、老板（租户用户）

#### 仪表盘模块

| 路由路径 | 组件路径 | 菜单名称 | 适用角色 |
|---------|---------|---------|---------|
| `/app/dashboard/analytics` | `/views/dashboard/analytics/index.vue` | 数据分析 | 全部 |
| `/app/dashboard/workspace` | `/views/dashboard/workspace/index.vue` | 工作台 | 全部 |

#### 反馈管理模块

| 路由路径 | 组件路径 | 菜单名称 | 适用角色 |
|---------|---------|---------|---------|
| `/app/feedback/list` | `/views/userecho/feedback/list.vue` | 反馈列表 | PM, CS, 老板 |
| `/app/feedback/import` | `/views/userecho/feedback/import.vue` | 导入反馈 | PM, 老板 |
| `/app/topic/list` | `/views/userecho/topic/list.vue` | 需求主题 | PM, 开发, 老板 |
| `/app/topic/detail/:id` | `/views/userecho/topic/detail.vue` | 主题详情 | PM, 开发, 老板 |
| `/app/customer` | `/views/userecho/customer/index.vue` | 客户管理 | PM, CS, 老板 |

---

## 三、角色与路由权限矩阵

### 3.1 系统角色

| 角色 | role_type | 可见路由 | 说明 |
|-----|-----------|---------|------|
| 超级管理员 | system | `/admin/*` + `/app/*` | 所有权限 |
| 系统管理员 | system | `/admin/*` | 只管理系统 |

### 3.2 业务角色

| 角色 | role_type | 可见路由 | 说明 |
|-----|-----------|---------|------|
| PM (产品经理) | business | `/app/dashboard/*`<br>`/app/feedback/*`<br>`/app/topic/*`<br>`/app/customer/*` | 全部业务功能 |
| CS (客户成功) | business | `/app/dashboard/*`<br>`/app/feedback/list`<br>`/app/customer/*` | 反馈+客户 |
| 开发 | business | `/app/dashboard/*`<br>`/app/topic/*` (只读) | 需求主题 |
| 老板 | business | `/app/*` | 全部业务功能 |

---

## 四、后端 API 路由规范

### 4.1 系统管理 API

**前缀：** `/api/v1/admin/`

```text
/api/v1/admin/auth/login           # 登录
/api/v1/admin/auth/logout          # 登出
/api/v1/admin/sys/user             # 用户管理
/api/v1/admin/sys/role             # 角色管理
/api/v1/admin/sys/menu             # 菜单管理
/api/v1/admin/sys/dept             # 部门管理
/api/v1/admin/log/login            # 登录日志
/api/v1/admin/log/opera            # 操作日志
/api/v1/admin/monitor/redis        # Redis 监控
/api/v1/admin/monitor/server       # 服务器监控
```

### 4.2 业务功能 API

**前缀：** `/api/v1/app/`

```text
/api/v1/app/feedbacks              # 反馈管理
/api/v1/app/feedbacks/import       # 导入反馈
/api/v1/app/topics                 # 需求主题
/api/v1/app/topics/:id/score       # 主题评分
/api/v1/app/customers              # 客户管理
/api/v1/app/clustering/trigger     # 触发聚类
/api/v1/app/priority               # 优先级管理
```

---

## 五、前端路由文件结构

```
front/apps/web-antd/src/router/routes/modules/
├── dashboard.ts      # /app/dashboard/*      (业务)
├── userecho.ts      # /app/feedback/*       (业务)
│                     # /app/topic/*          (业务)
│                     # /app/customer/*       (业务)
├── system.ts         # /admin/system/*       (系统)
├── log.ts            # /admin/log/*          (系统)
├── monitor.ts        # /admin/monitor/*      (系统)
└── scheduler.ts      # /admin/scheduler/*    (系统)
```

---

## 六、数据库菜单初始化 SQL

### 6.1 系统管理菜单（更新路径）

```sql
-- 更新现有系统菜单路径
UPDATE sys_menu SET path = REPLACE(path, '/system/', '/admin/system/') WHERE path LIKE '/system/%';
UPDATE sys_menu SET path = REPLACE(path, '/log/', '/admin/log/') WHERE path LIKE '/log/%';
UPDATE sys_menu SET path = REPLACE(path, '/monitor/', '/admin/monitor/') WHERE path LIKE '/monitor/%';
UPDATE sys_menu SET path = REPLACE(path, '/scheduler/', '/admin/scheduler/') WHERE path LIKE '/scheduler/%';
```

### 6.2 业务功能菜单（新增）

```sql
-- 1. 反馈管理目录
INSERT INTO sys_menu (title, name, path, icon, type, sort, parent_id, status, display) 
VALUES ('反馈管理', 'UserEcho', '/app/userecho', 'lucide:messages-square', 0, 100, NULL, 1, 1);

SET @userecho_id = LAST_INSERT_ID();

-- 2. 反馈列表
INSERT INTO sys_menu (title, name, path, component, icon, type, sort, parent_id, status, display, perms) 
VALUES ('反馈列表', 'FeedbackList', '/app/feedback/list', '/userecho/feedback/list', 'lucide:inbox', 1, 1, @userecho_id, 1, 1, 'app:feedback:view');

-- 3. 导入反馈
INSERT INTO sys_menu (title, name, path, component, icon, type, sort, parent_id, status, display, perms) 
VALUES ('导入反馈', 'FeedbackImport', '/app/feedback/import', '/userecho/feedback/import', 'lucide:upload', 1, 2, @userecho_id, 1, 1, 'app:feedback:import');

-- 4. 需求主题
INSERT INTO sys_menu (title, name, path, component, icon, type, sort, parent_id, status, display, perms) 
VALUES ('需求主题', 'TopicList', '/app/topic/list', '/userecho/topic/list', 'lucide:lightbulb', 1, 3, @userecho_id, 1, 1, 'app:topic:view');

-- 5. 客户管理
INSERT INTO sys_menu (title, name, path, component, icon, type, sort, parent_id, status, display, perms) 
VALUES ('客户管理', 'CustomerManage', '/app/customer', '/userecho/customer/index', 'lucide:users', 1, 4, @userecho_id, 1, 1, 'app:customer:view');

-- 6. 更新仪表盘路径
UPDATE sys_menu SET path = REPLACE(path, '/dashboard/', '/app/dashboard/') WHERE path LIKE '/dashboard/%';
```

---

## 七、菜单过滤逻辑（后端）

```python
# server/backend/app/admin/service/menu_service.py

class MenuService:
    # 路由前缀常量
    BUSINESS_PREFIX = '/app'      # 业务功能前缀
    SYSTEM_PREFIX = '/admin'      # 系统管理前缀
    
    @staticmethod
    def _filter_menus_by_role_type(
        menus: Sequence[Menu], 
        has_system_role: bool, 
        has_business_role: bool
    ) -> list[Menu]:
        """根据角色类型过滤菜单"""
        
        # 拥有系统+业务角色：看全部
        if has_system_role and has_business_role:
            return list(menus)
        
        filtered_menus = []
        for menu in menus:
            path = menu.path or ''
            
            # 根菜单或空路径：保留
            if not path or path == '/':
                filtered_menus.append(menu)
                continue
            
            # 🔥 关键逻辑：只判断 2 个前缀
            if has_system_role and path.startswith(MenuService.SYSTEM_PREFIX):
                filtered_menus.append(menu)
            elif has_business_role and path.startswith(MenuService.BUSINESS_PREFIX):
                filtered_menus.append(menu)
        
        return filtered_menus
```

---

## 八、测试用例

### 8.1 前端路由测试

```typescript
// front/apps/web-antd/src/router/routes/__tests__/route-prefix.spec.ts
import { describe, expect, it } from 'vitest';
import systemRoutes from '../modules/system';
import userechoRoutes from '../modules/userecho';

describe('Route Prefix Validation', () => {
  it('系统管理路由应该以 /admin 开头', () => {
    const routes = systemRoutes[0];
    expect(routes.path).toMatch(/^\/admin\//);
    
    routes.children?.forEach((child) => {
      expect(child.path).toMatch(/^\/admin\//);
    });
  });
  
  it('业务功能路由应该以 /app 开头', () => {
    const routes = userechoRoutes[0];
    expect(routes.path).toMatch(/^\/app\//);
    
    routes.children?.forEach((child) => {
      expect(child.path).toMatch(/^\/app\//);
    });
  });
});
```

### 8.2 后端菜单过滤测试

```python
# server/backend/tests/test_menu_filter.py
import pytest
from backend.app.admin.service.menu_service import MenuService

@pytest.mark.asyncio
async def test_system_admin_only_see_admin_routes(db, system_admin_user):
    """系统管理员只能看到 /admin/* 路由"""
    request = mock_request(user=system_admin_user)
    menus = await MenuService.get_sidebar(db=db, request=request)
    
    for menu in menus:
        path = menu.get('path', '')
        if path:
            assert path.startswith('/admin/'), f"系统管理员看到了非系统菜单: {path}"

@pytest.mark.asyncio
async def test_business_user_only_see_app_routes(db, pm_user):
    """业务用户只能看到 /app/* 路由"""
    request = mock_request(user=pm_user)
    menus = await MenuService.get_sidebar(db=db, request=request)
    
    for menu in menus:
        path = menu.get('path', '')
        if path:
            assert path.startswith('/app/'), f"业务用户看到了系统菜单: {path}"
```

---

## 九、迁移清单

### 9.1 数据库迁移

```bash
# 1. 添加 role_type 字段
alembic revision -m "Add role_type to sys_role"

# 2. 更新现有菜单路径
alembic revision -m "Update menu paths with prefixes"

# 3. 初始化业务菜单
python scripts/init_business_menus.py
```

### 9.2 前端迁移

```bash
# 已完成：
✅ front/apps/web-antd/src/router/routes/modules/system.ts     (/admin/system/*)
✅ front/apps/web-antd/src/router/routes/modules/log.ts        (/admin/log/*)
✅ front/apps/web-antd/src/router/routes/modules/monitor.ts    (/admin/monitor/*)
✅ front/apps/web-antd/src/router/routes/modules/scheduler.ts  (/admin/scheduler/*)
✅ front/apps/web-antd/src/router/routes/modules/dashboard.ts  (/app/dashboard/*)
✅ front/apps/web-antd/src/router/routes/modules/userecho.ts  (/app/*)

# 待测试：
⏳ 运行前端开发服务器测试路由
⏳ 测试菜单权限过滤
```

---

## 十、FAQ

**Q: 为什么用 `/app` 而不是 `/userecho`？**  
A: 
- `userecho` 是产品名，不应该出现在路由里
- `/app` 是通用的业务功能前缀，扩展性更强
- 未来可能有其他业务模块（CRM、工单系统等）

**Q: 如果新增业务模块（如工单系统），路由怎么设计？**  
A: 
```text
/app/ticket/list      # 工单列表
/app/ticket/detail    # 工单详情
/app/ticket/create    # 创建工单
```
继续放在 `/app/*` 下，菜单过滤逻辑无需修改。

**Q: Dashboard 为什么归到 `/app/*` 而不是独立？**  
A: 
- Dashboard 主要服务业务用户（查看数据、工作台）
- 系统管理员通常不需要 Dashboard
- 如果系统管理员需要，可以给他分配业务角色

**Q: 前端路由改了，后端 API 需要同步改吗？**  
A: 
- 前端路由：`/app/feedback/list` （用户访问的 URL）
- 后端 API：`/api/v1/app/feedbacks` （接口路径）
- 两者独立，但建议保持一致的前缀约定（`/app` vs `/admin`）

---

**文档维护者:** 技术团队  
**最后更新:** 2025-12-22  
**状态:** 已实施
