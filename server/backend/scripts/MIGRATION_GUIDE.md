# 后端路由隔离迁移 - 执行指南

> **执行日期:** 2025-12-22  
> **目标:** 将系统管理和业务功能路由隔离（/admin/* 和 /app/*）

---

## 📋 执行前检查清单

- [ ] 数据库服务正在运行
- [ ] 数据库连接配置正确（检查 `.env` 文件）
- [ ] **停止后端服务**（避免数据库锁定）
- [ ] 已备份数据库（推荐）

---

## 🚀 执行步骤

### 方式一：一键执行（推荐）

```bash
cd server/backend
python scripts/run_route_migration.py
```

脚本会自动执行：
1. 数据库迁移（添加 `role_type` 字段并更新菜单路径）
2. 初始化业务菜单和角色
3. 验证迁移结果

---

### 方式二：分步执行

#### Step 1: 执行数据库迁移

```bash
cd server/backend
alembic upgrade head
```

**预期输出：**
```
INFO  [alembic.runtime.migration] Running upgrade 9a2de98df5fb -> 2025122201, add role_type and update menu paths
```

#### Step 2: 初始化业务菜单

```bash
python scripts/init_business_menus.py
```

**预期输出：**
```
✅ 业务菜单和角色初始化完成！

📝 创建的资源：
   - 反馈管理目录
   - 4 个子菜单（反馈列表、导入反馈、需求主题、客户管理）
   - 4 个业务角色（PM、CS、开发、老板）
```

#### Step 3: 验证迁移

启动后端服务并测试：

```bash
cd server/backend
python run.py
```

登录系统，检查：
- [ ] 超级管理员能看到所有菜单
- [ ] 系统角色只能看到 `/admin/*` 菜单
- [ ] 业务角色只能看到 `/app/*` 菜单

---

## 🔍 验证清单

### 数据库检查

```sql
-- 1. 检查 role_type 字段
SELECT id, name, role_type FROM sys_role;

-- 2. 检查系统管理菜单路径
SELECT id, title, path FROM sys_menu WHERE path LIKE '/admin/%' ORDER BY sort;

-- 3. 检查业务功能菜单路径
SELECT id, title, path FROM sys_menu WHERE path LIKE '/app/%' ORDER BY sort;

-- 4. 检查是否还有旧路径（应该返回空）
SELECT id, title, path FROM sys_menu 
WHERE path LIKE '/system/%' 
   OR path LIKE '/log/%' 
   OR path LIKE '/monitor/%';
```

### 前端检查

1. **超级管理员登录：**
   - 应该看到所有菜单（`/admin/*` + `/app/*`）

2. **创建测试角色：**
   ```sql
   -- 创建系统管理员角色（如果不存在）
   INSERT INTO sys_role (name, role_type, status, remark)
   VALUES ('测试系统管理员', 'system', 1, '仅用于测试');
   
   -- 分配 /admin/system/user 菜单权限
   INSERT INTO sys_role_menu (role_id, menu_id)
   SELECT r.id, m.id
   FROM sys_role r, sys_menu m
   WHERE r.name = '测试系统管理员'
     AND m.path LIKE '/admin/%';
   ```

3. **分配测试角色给用户并登录：**
   - 系统角色用户：只能看到 `/admin/*` 菜单
   - PM 角色用户：只能看到 `/app/*` 菜单

---

## 🔧 已修改的文件清单

### 后端文件

| 文件 | 修改内容 |
|------|---------|
| `app/admin/model/role.py` | ✅ 添加 `role_type` 字段 |
| `app/admin/service/menu_service.py` | ✅ 添加菜单过滤逻辑 |
| `app/feedalyze/api/router.py` | ✅ 更新 API 路由前缀为 `/app` |
| `alembic/versions/2025-12-22-01_*.py` | ✅ 新增迁移脚本 |
| `scripts/init_business_menus.py` | ✅ 新增初始化脚本 |
| `scripts/run_route_migration.py` | ✅ 新增一键执行脚本 |

### 待修改的前端文件（需单独执行）

前端 API 路径需要从 `/feedalyze/*` 更新为 `/app/*`：

```bash
cd front/apps/web-antd/src/api/feedalyze

# 批量替换（Linux/Mac）
sed -i "s|'/feedalyze/|'/app/|g" *.ts

# 批量替换（Windows PowerShell）
Get-ChildItem *.ts | ForEach-Object {
    (Get-Content $_) -replace "'/feedalyze/", "'/app/" | Set-Content $_
}
```

---

## 🔄 回滚方案

如果迁移后出现问题：

```bash
cd server/backend
alembic downgrade -1
```

这将：
1. 删除 `role_type` 字段
2. 恢复所有菜单路径到原始状态

---

## ⚠️ 常见问题

### Q1: 执行迁移时报错 "Another program is using this file"

**A:** 后端服务仍在运行，请先停止服务再执行迁移。

### Q2: 执行后菜单显示不正常

**A:** 
1. 清除浏览器缓存
2. 检查用户的角色 `role_type` 是否正确
3. 检查菜单路径是否已更新

### Q3: 旧的 API 路径无法访问

**A:** 
- 后端 API 已从 `/api/v1/feedalyze/*` 改为 `/api/v1/app/*`
- 需要同步更新前端 API 调用路径

### Q4: 如何给现有用户分配业务角色？

**A:**
```sql
-- 查看现有角色
SELECT * FROM sys_role WHERE role_type = 'business';

-- 给用户分配 PM 角色
INSERT INTO sys_user_role (user_id, role_id)
SELECT u.id, r.id
FROM sys_user u, sys_role r
WHERE u.username = 'test_user'  -- 替换为实际用户名
  AND r.name = 'PM';
```

---

## ✅ 执行后清单

完成迁移后，请确认：

- [ ] 数据库迁移成功执行
- [ ] 业务菜单和角色已创建
- [ ] 后端服务正常启动
- [ ] 超级管理员能看到所有菜单
- [ ] 系统角色只能看到 `/admin/*` 菜单
- [ ] 业务角色只能看到 `/app/*` 菜单
- [ ] API 路径访问正常（`/api/v1/app/*`）
- [ ] 前端菜单显示正常
- [ ] 已更新项目文档

---

## 📞 技术支持

如有问题，请参考：
- [route-design.md](../../docs/route-design.md) - 路由设计规范
- [route-isolation-summary.md](../../docs/route-isolation-summary.md) - 改造总结文档
- [template-adaptation-plan.md](../../docs/template-adaptation-plan.md) - 模板改造方案

---

**文档维护者:** 技术团队  
**最后更新:** 2025-12-22  
**状态:** 准备执行
