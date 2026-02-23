-- 添加积分管理和订阅管理菜单到系统管理
-- 说明：这两个功能已有后端API和前端页面，但缺少菜单记录

-- 1. 获取"System"菜单的ID（parent_id）
-- 假设 System 菜单的 ID 是 4（从之前的查询结果可知）

-- 2. 添加"积分管理"菜单
INSERT INTO sys_menu (
    title, 
    name, 
    path, 
    sort, 
    icon, 
    type, 
    component, 
    perms, 
    status, 
    display, 
    cache, 
    link, 
    remark, 
    parent_id,
    created_time
)
VALUES (
    '积分管理',                              -- title
    'SysCredits',                            -- name
    '/system/credits',                       -- path
    11,                                      -- sort (放在订阅管理之后)
    'carbon:user-certification',             -- icon
    1,                                       -- type: 1=菜单
    '/src/views/system/credits/index',       -- component（需要创建对应的Vue文件）
    NULL,                                    -- perms
    1,                                       -- status: 1=启用
    1,                                       -- display: 1=显示
    1,                                       -- cache: 1=缓存
    '',                                      -- link
    '系统积分配置管理',                       -- remark
    4,                                       -- parent_id: System菜单
    NOW()                                    -- created_time
)
ON CONFLICT DO NOTHING;

-- 3. 添加"订阅管理"菜单
INSERT INTO sys_menu (
    title, 
    name, 
    path, 
    sort, 
    icon, 
    type, 
    component, 
    perms, 
    status, 
    display, 
    cache, 
    link, 
    remark, 
    parent_id,
    created_time
)
VALUES (
    '订阅管理',                              -- title
    'SysSubscription',                       -- name
    '/system/subscription',                  -- path
    10,                                      -- sort
    'eos-icons:subscription-management-outlined', -- icon
    1,                                       -- type: 1=菜单
    '/src/views/system/subscription/index',  -- component
    NULL,                                    -- perms
    1,                                       -- status: 1=启用
    1,                                       -- display: 1=显示
    1,                                       -- cache: 1=缓存
    '',                                      -- link
    '系统订阅套餐管理',                       -- remark
    4,                                       -- parent_id: System菜单
    NOW()                                    -- created_time
)
ON CONFLICT DO NOTHING;

-- 4. 重置序列（确保下一个ID正确）
SELECT setval(pg_get_serial_sequence('sys_menu', 'id'), COALESCE(MAX(id), 0) + 1, true) FROM sys_menu;
