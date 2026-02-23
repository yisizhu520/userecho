# Refactor Member Management UI

## Goal
Update `front/apps/web-antd/src/views/userecho/settings/members.vue` to match the visual style and layout of `feedback/list.vue`.

## Changes

### 1. Layout Structure
**Before:**
```vue
<Page title="Member Management">
  <Table />
</Page>
```

**After:**
```vue
<div class="member-list-container">
  <div class="member-content-wrapper">
    <div class="member-main-content">
      <Grid>
         <template #toolbar-actions>
            <Toolbar />
         </template>
      </Grid>
    </div>
  </div>
</div>
```

### 2. Component Replacement
- Replace `Table` (ant-design-vue) with `Grid` + `useVbenVxeGrid` (vben-admin adapter).
- Implement `proxyConfig.ajax.query` for data fetching.

### 3. Features to Preserve
- **List Display**: ID, Username, Nickname, Type, Status, Feedback Count, Actions.
- **Create User**: Modal with Username, Nickname, Password, Email, Roles.
- **Edit Roles**: Modal to assign roles.
- **Delete User**: Confirmation dialog.

### 4. New Features (to match style)
- **Search Bar**: Client-side filtering (since API is limited).
- **Refresh Support**: Built-in with VxeGrid.

## Implementation Details

### Grid Options
```typescript
const gridOptions: VxeTableGridOptions<TenantMember> = {
  columns: [
    { field: 'user_id', title: 'ID', width: 80 },
    { field: 'username', title: '用户名' },
    { field: 'nickname', title: '昵称' },
    { field: 'user_type', title: '类型', width: 120 },
    { field: 'status', title: '状态', slots: { default: 'status' } },
    { field: 'feedback_count', title: '反馈数', width: 100 },
    { title: '操作', width: 150, slots: { default: 'action' } }
  ],
  toolbarConfig: {
    custom: true,
    refresh: true,
    zoom: true
  },
  proxyConfig: {
    ajax: {
      query: async ({ page }) => {
         // API Call
      }
    }
  }
}
```

### CSS
Copy the `feedback-list-container` styles but simplified (no sidebar).
