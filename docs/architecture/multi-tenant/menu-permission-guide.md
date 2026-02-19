# 菜单权限配置指南

## 问题现象

前端定义了路由，但在左侧菜单栏没有显示。

## 原因分析

本项目使用 **后端权限控制模式**（`accessMode: 'backend'`），菜单由后端数据库的 `sys_menu` 表控制，而不是由前端路由文件直接决定。

**权限控制流程**：

```
用户登录 
  ↓
获取用户角色 (sys_role)
  ↓  
查询角色关联的菜单 (sys_menu via role_menu)
  ↓
前端匹配路由定义
  ↓
渲染左侧菜单栏
```

**关键点**：
- 前端路由定义（`front/apps/web-antd/src/router/routes/modules/*.ts`）是"候选项"
- 后端菜单表（`sys_menu`）是"权限控制"
- 用户角色（`sys_role`）决定能看到哪些菜单

## 解决方案

### 方法一：运行菜单初始化脚本（推荐）

这个脚本会自动创建所有业务菜单并分配给相应角色。

**Windows**：
```bash
cd server
init_menus.bat
```

**Linux/Mac**：
```bash
cd server
./init_menus.sh
```

**脚本会创建**：
- ✅ 反馈管理目录
- ✅ 5 个功能菜单：反馈列表、AI 发现中心、导入反馈、需求主题、客户管理
- ✅ 设置目录
- ✅ 1 个设置子菜单：聚类策略
- ✅ 4 个业务角色：PM、CS、开发、老板

### 方法二：通过系统管理界面手动添加

1. **登录超级管理员账号**

2. **进入系统管理 → 菜单管理**
   - 路径：`/admin/system/menu`

3. **创建设置目录**
   ```
   菜单标题: 设置
   菜单名称: Settings
   路由地址: /app/settings
   父级菜单: 反馈管理
   菜单类型: 目录 (0)
   图标: lucide:settings
   排序: 6
   状态: 启用
   ```

4. **创建聚类策略菜单**
   ```
   菜单标题: 聚类策略
   菜单名称: ClusteringConfig
   路由地址: /app/settings/clustering
   父级菜单: 设置
   菜单类型: 菜单 (1)
   组件路径: /userecho/settings/clustering-config
   图标: lucide:layers
   权限标识: app:settings:clustering
   排序: 1
   状态: 启用
   ```

5. **创建 AI 发现中心菜单**
   ```
   菜单标题: AI 发现中心
   菜单名称: AIDiscovery
   路由地址: /app/ai/discovery
   父级菜单: 反馈管理
   菜单类型: 菜单 (1)
   组件路径: /userecho/discovery/index
   图标: lucide:sparkles
   权限标识: app:ai:view
   排序: 2
   状态: 启用
   ```

6. **分配菜单给角色**
   - 进入 **系统管理 → 角色管理**
   - 选择对应角色（如 PM、老板）
   - 点击"菜单权限"
   - 勾选新建的菜单
   - 保存

7. **清除缓存并重新登录**
   - 退出登录
   - 重新登录查看效果

## 菜单结构设计

```
回响 (UserEcho)                    /app/userecho
├─ 反馈列表                        /app/feedback/list
├─ AI 发现中心                     /app/ai/discovery
├─ 导入反馈                        /app/feedback/import
├─ 需求主题                        /app/topic/list
├─ 客户管理                        /app/customer
└─ 设置                            /app/settings
   └─ 聚类策略                     /app/settings/clustering
```

## 重要字段说明

### 组件路径 (component)

**规则**：相对于 `front/apps/web-antd/src/views` 的路径，**不要**包含 `.vue` 后缀。

**示例**：
- ✅ `/userecho/settings/clustering-config`
- ❌ `/views/userecho/settings/clustering-config.vue`
- ❌ `#/views/userecho/settings/clustering-config`

**对应关系**：
```
组件路径: /userecho/settings/clustering-config
实际文件: front/apps/web-antd/src/views/userecho/settings/clustering-config.vue
```

### 路由地址 (path)

- 业务功能：以 `/app/` 开头
- 系统管理：以 `/admin/` 开头

### 菜单类型 (type)

- `0` - 目录（可以包含子菜单，无组件路径）
- `1` - 菜单（实际可点击的页面）
- `2` - 按钮（页面内的操作按钮权限）

### 权限标识 (perms)

格式：`模块:功能:操作`

示例：
- `app:feedback:view` - 查看反馈
- `app:settings:clustering` - 聚类配置
- `app:topic:edit` - 编辑主题

## 验证菜单配置

### 1. 数据库检查

```sql
-- 查看所有业务菜单
SELECT id, title, name, path, component, parent_id, sort 
FROM sys_menu 
WHERE path LIKE '/app/%'
ORDER BY parent_id, sort;

-- 查看设置相关菜单
SELECT id, title, name, path, component 
FROM sys_menu 
WHERE path LIKE '/app/settings%';
```

### 2. API 检查

访问：`http://localhost:8000/api/v1/sys/menus/sidebar`

检查返回的菜单树是否包含新增的菜单。

### 3. 前端检查

打开浏览器开发者工具 → Network → 查看 `/api/v1/sys/menus/sidebar` 请求的响应。

## 常见问题

### Q1: 菜单创建了但还是不显示？

**可能原因**：
1. 当前用户角色没有分配该菜单权限
2. 菜单状态为"停用"
3. 父级菜单状态为"停用"
4. 组件路径错误

**解决方法**：
1. 检查角色权限配置
2. 确认菜单和父级菜单都是"启用"状态
3. 验证组件路径是否正确
4. 清除浏览器缓存并重新登录

### Q2: 点击菜单后显示 404？

**原因**：组件路径配置错误或文件不存在。

**检查**：
1. 组件路径是否正确（不要包含 `.vue` 后缀）
2. 文件是否真实存在于 `front/apps/web-antd/src/views/` 目录下
3. 前端路由配置是否正确

### Q3: 菜单顺序不对？

**调整**：修改菜单的 `sort` 字段，数字越小越靠前。

### Q4: 子菜单无法折叠？

**检查**：
1. 父级菜单的 `type` 必须是 `0`（目录）
2. 父级菜单不能设置 `component`
3. 子菜单的 `parent_id` 必须正确指向父级菜单的 `id`

## 扩展指南

添加新配置菜单（如通知配置）：

1. **创建前端页面**
   - `front/apps/web-antd/src/views/userecho/settings/notification-config.vue`

2. **添加路由定义**
   - 在 `front/apps/web-antd/src/router/routes/modules/userecho.ts` 的 `Settings.children` 中添加

3. **更新多语言配置**
   - `front/apps/web-antd/src/locales/langs/zh-CN/page.json`
   - `front/apps/web-antd/src/locales/langs/en-US/page.json`

4. **运行菜单初始化脚本** 或 **手动添加数据库记录**

5. **分配权限给角色**

## 相关文档

- [租户配置系统设计](./tenant-config-system.md)
- [角色权限设计](../../server/backend/docs/rbac.md)
- [前端路由设计](../../docs/design/route-design.md)
