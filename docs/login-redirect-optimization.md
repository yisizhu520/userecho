# 登录重定向逻辑优化 - 实施记录

## 实施时间
2026-01-05 22:02

## 实施内容

### 1. 前端修改（方案 C - 快速解决）

**文件**: `front/apps/web-antd/src/preferences.ts`

修改默认首页配置：
```typescript
app: {
  defaultHomePath: '/app/dashboard/workspace',  // 所有用户默认跳转工作台
}
```

**效果**: 当后端未返回 `homePath` 或登录异常时，系统会 fallback 到工作台页面，避免 404。

---

### 2. 后端修改（方案 A - 完整方案）

**文件**: `server/backend/app/admin/schema/user.py`

#### 修改内容

1. **添加 `homePath` 字段**:
   ```python
   homePath: str = Field(description='用户首页路径')
   ```

2. **实现动态计算逻辑**:
   ```python
   # 计算 homePath - 根据角色类型
   if is_superuser:
       # 超级管理员 → 系统管理页
       data['homePath'] = '/admin/system/user'
   elif has_system_role and not has_business_role:
       # 纯系统角色 → 系统管理页
       data['homePath'] = '/admin/system/user'
   else:
       # 业务角色或混合角色 → 工作台
       data['homePath'] = '/app/dashboard/workspace'
   ```

#### 角色类型到首页的映射

| 用户类型 | 角色类型 | 首页路径 | 示例账号 |
|---------|---------|---------|---------|
| 超级管理员 | - | `/admin/system/user` | admin |
| 纯系统角色 | `system` | `/admin/system/user` | sysadmin |
| 纯业务角色 | `business` | `/app/dashboard/workspace` | pm, cs, dev, boss |
| 混合角色 | `system` + `business` | `/app/dashboard/workspace` | hybrid |

#### 逻辑优先级

1. **超级管理员** (`is_superuser=True`) → `/admin/system/user`
2. **纯系统角色** (`has_system_role=True` && `has_business_role=False`) → `/admin/system/user`
3. **其他所有情况** → `/app/dashboard/workspace`

**设计理由**: 混合角色用户更可能需要业务功能，因此优先跳转到工作台。

---

## 测试建议

### 测试账号清单

| 账号 | 预期首页 | 验证目的 |
|------|---------|---------|
| `admin` | `/admin/system/user` | 验证超级管理员 |
| `sysadmin` | `/admin/system/user` | 验证纯系统角色 |
| `pm` | `/app/dashboard/workspace` | 验证业务角色（PM） |
| `cs` | `/app/dashboard/workspace` | 验证业务角色（CS） |
| `dev` | `/app/dashboard/workspace` | 验证业务角色（开发） |
| `boss` | `/app/dashboard/workspace` | 验证业务角色（老板） |
| `hybrid` | `/app/dashboard/workspace` | 验证混合角色优先跳业务 |

### 测试步骤

1. **清除浏览器缓存和 localStorage**
2. **逐个账号登录**，统一密码 `Test123456`
3. **验证跳转路径**是否符合预期
4. **检查是否有 404 错误**

---

## 影响范围

### 前端
- ✅ 所有用户登录后默认跳转到工作台（兜底策略）
- ✅ 路由守卫会优先使用后端返回的 `userInfo.homePath`

### 后端
- ✅ `/api/v1/sys/users/me` 接口返回增加 `homePath` 字段
- ✅ 角色类型判断逻辑集中在 schema validator 中

---

## 回滚方案

如果出现问题，可以快速回滚：

### 前端回滚
```typescript
// 恢复到默认值
app: {
  defaultHomePath: '/analytics',
}
```

### 后端回滚
```python
# 删除 homePath 字段和计算逻辑
class GetCurrentUserInfoWithRelationDetail(GetUserInfoWithRelationDetail):
    dept: str | None = Field(None, description='部门名称')
    roles: list[str] = Field(description='角色名称列表')
    # 删除: homePath: str = Field(...)
```

---

## 后续优化建议

1. **支持用户自定义首页**: 允许用户在个人设置中选择首页
2. **记录用户最后访问页面**: 登录后跳转到上次离开的页面
3. **角色首页配置化**: 在角色管理中配置默认首页，而不是硬编码

---

## 验证结果

- [x] Python 语法检查通过 (`python -m py_compile`)
- [ ] 前端类型检查（需要运行 `pnpm check:type`）
- [ ] 实际登录测试（需要重启后端服务）
