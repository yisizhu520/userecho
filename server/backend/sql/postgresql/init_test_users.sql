-- 创建测试用户脚本
-- 用于测试路由隔离功能的不同角色用户
-- 
-- 使用方法：
-- psql -U your_user -d your_database -f init_test_users.sql

-- 密码说明：所有密码都是 Test123456
-- 密码哈希：$2b$12$VEwQ5h9Z8jZ4YjEQNxJX8.RGPxLhNkL7YT2YfEqXqKvZxW7XvQYPy
-- 盐值：24326224313224564577513568395a386a5a344a6a45514e784a583865

-- ================================================================================
-- 1. 创建系统角色（如果不存在）
-- ================================================================================

-- 检查并创建 "系统管理员" 角色
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM sys_role WHERE name = '系统管理员') THEN
        INSERT INTO sys_role (name, status, is_filter_scopes, role_type, remark, created_time)
        VALUES ('系统管理员', 1, true, 'system', '系统管理员角色，只能访问系统管理菜单', now());
    END IF;
END $$;

-- ================================================================================
-- 2. 创建业务角色（如果不存在）
-- ================================================================================

DO $$
BEGIN
    -- PM 角色
    IF NOT EXISTS (SELECT 1 FROM sys_role WHERE name = 'PM') THEN
        INSERT INTO sys_role (name, status, is_filter_scopes, role_type, remark, created_time)
        VALUES ('PM', 1, true, 'business', '产品经理，可管理全部反馈功能', now());
    END IF;
    
    -- CS 角色
    IF NOT EXISTS (SELECT 1 FROM sys_role WHERE name = 'CS') THEN
        INSERT INTO sys_role (name, status, is_filter_scopes, role_type, remark, created_time)
        VALUES ('CS', 1, true, 'business', '客户成功，可查看反馈和客户', now());
    END IF;
    
    -- 开发 角色
    IF NOT EXISTS (SELECT 1 FROM sys_role WHERE name = '开发') THEN
        INSERT INTO sys_role (name, status, is_filter_scopes, role_type, remark, created_time)
        VALUES ('开发', 1, true, 'business', '开发人员，只读需求主题', now());
    END IF;
    
    -- 老板 角色
    IF NOT EXISTS (SELECT 1 FROM sys_role WHERE name = '老板') THEN
        INSERT INTO sys_role (name, status, is_filter_scopes, role_type, remark, created_time)
        VALUES ('老板', 1, true, 'business', '租户管理员，查看全部', now());
    END IF;
END $$;

-- ================================================================================
-- 3. 创建测试用户
-- ================================================================================
-- 注意：使用统一密码 Test123456

DO $$
DECLARE
    v_dept_id INT;
    v_sysadmin_role_id INT;
    v_pm_role_id INT;
    v_cs_role_id INT;
    v_dev_role_id INT;
    v_boss_role_id INT;
    v_user_id INT;
BEGIN
    -- 获取默认部门 ID
    SELECT id INTO v_dept_id FROM sys_dept WHERE name = '测试' LIMIT 1;
    IF v_dept_id IS NULL THEN
        v_dept_id := 1;
    END IF;

    -- 获取角色 ID
    SELECT id INTO v_sysadmin_role_id FROM sys_role WHERE name = '系统管理员';
    SELECT id INTO v_pm_role_id FROM sys_role WHERE name = 'PM';
    SELECT id INTO v_cs_role_id FROM sys_role WHERE name = 'CS';
    SELECT id INTO v_dev_role_id FROM sys_role WHERE name = '开发';
    SELECT id INTO v_boss_role_id FROM sys_role WHERE name = '老板';

    -- ============================================================================
    -- 用户 1: sysadmin - 系统管理员
    -- ============================================================================
    IF NOT EXISTS (SELECT 1 FROM sys_user WHERE username = 'sysadmin') THEN
        INSERT INTO sys_user (
            uuid, username, nickname, password, salt, email, 
            status, is_superuser, is_staff, is_multi_login, 
            dept_id, join_time, last_login_time, last_password_changed_time, created_time
        )
        VALUES (
            gen_random_uuid(),
            'sysadmin',
            '系统管理员',
            '$2b$12$VEwQ5h9Z8jZ4YjEQNxJX8.RGPxLhNkL7YT2YfEqXqKvZxW7XvQYPy',
            decode('24326224313224564577513568395a386a5a344a6a45514e784a583865', 'hex'),
            'sysadmin@feedalyze.com',
            1, false, true, true,
            v_dept_id, now(), now(), now(), now()
        )
        RETURNING id INTO v_user_id;
        
        -- 关联角色
        IF v_sysadmin_role_id IS NOT NULL THEN
            INSERT INTO sys_user_role (user_id, role_id) VALUES (v_user_id, v_sysadmin_role_id);
        END IF;
        
        RAISE NOTICE '✅ 创建用户: sysadmin (系统管理员角色)';
    ELSE
        RAISE NOTICE '⏭️  跳过: 用户 sysadmin 已存在';
    END IF;

    -- ============================================================================
    -- 用户 2: pm - 产品经理
    -- ============================================================================
    IF NOT EXISTS (SELECT 1 FROM sys_user WHERE username = 'pm') THEN
        INSERT INTO sys_user (
            uuid, username, nickname, password, salt, email, 
            status, is_superuser, is_staff, is_multi_login, 
            dept_id, join_time, last_login_time, last_password_changed_time, created_time
        )
        VALUES (
            gen_random_uuid(),
            'pm',
            '产品经理',
            '$2b$12$VEwQ5h9Z8jZ4YjEQNxJX8.RGPxLhNkL7YT2YfEqXqKvZxW7XvQYPy',
            decode('24326224313224564577513568395a386a5a344a6a45514e784a583865', 'hex'),
            'pm@feedalyze.com',
            1, false, true, true,
            v_dept_id, now(), now(), now(), now()
        )
        RETURNING id INTO v_user_id;
        
        IF v_pm_role_id IS NOT NULL THEN
            INSERT INTO sys_user_role (user_id, role_id) VALUES (v_user_id, v_pm_role_id);
        END IF;
        
        RAISE NOTICE '✅ 创建用户: pm (PM角色)';
    ELSE
        RAISE NOTICE '⏭️  跳过: 用户 pm 已存在';
    END IF;

    -- ============================================================================
    -- 用户 3: cs - 客户成功
    -- ============================================================================
    IF NOT EXISTS (SELECT 1 FROM sys_user WHERE username = 'cs') THEN
        INSERT INTO sys_user (
            uuid, username, nickname, password, salt, email, 
            status, is_superuser, is_staff, is_multi_login, 
            dept_id, join_time, last_login_time, last_password_changed_time, created_time
        )
        VALUES (
            gen_random_uuid(),
            'cs',
            '客户成功',
            '$2b$12$VEwQ5h9Z8jZ4YjEQNxJX8.RGPxLhNkL7YT2YfEqXqKvZxW7XvQYPy',
            decode('24326224313224564577513568395a386a5a344a6a45514e784a583865', 'hex'),
            'cs@feedalyze.com',
            1, false, true, true,
            v_dept_id, now(), now(), now(), now()
        )
        RETURNING id INTO v_user_id;
        
        IF v_cs_role_id IS NOT NULL THEN
            INSERT INTO sys_user_role (user_id, role_id) VALUES (v_user_id, v_cs_role_id);
        END IF;
        
        RAISE NOTICE '✅ 创建用户: cs (CS角色)';
    ELSE
        RAISE NOTICE '⏭️  跳过: 用户 cs 已存在';
    END IF;

    -- ============================================================================
    -- 用户 4: dev - 开发人员
    -- ============================================================================
    IF NOT EXISTS (SELECT 1 FROM sys_user WHERE username = 'dev') THEN
        INSERT INTO sys_user (
            uuid, username, nickname, password, salt, email, 
            status, is_superuser, is_staff, is_multi_login, 
            dept_id, join_time, last_login_time, last_password_changed_time, created_time
        )
        VALUES (
            gen_random_uuid(),
            'dev',
            '开发人员',
            '$2b$12$VEwQ5h9Z8jZ4YjEQNxJX8.RGPxLhNkL7YT2YfEqXqKvZxW7XvQYPy',
            decode('24326224313224564577513568395a386a5a344a6a45514e784a583865', 'hex'),
            'dev@feedalyze.com',
            1, false, true, true,
            v_dept_id, now(), now(), now(), now()
        )
        RETURNING id INTO v_user_id;
        
        IF v_dev_role_id IS NOT NULL THEN
            INSERT INTO sys_user_role (user_id, role_id) VALUES (v_user_id, v_dev_role_id);
        END IF;
        
        RAISE NOTICE '✅ 创建用户: dev (开发角色)';
    ELSE
        RAISE NOTICE '⏭️  跳过: 用户 dev 已存在';
    END IF;

    -- ============================================================================
    -- 用户 5: boss - 租户管理员
    -- ============================================================================
    IF NOT EXISTS (SELECT 1 FROM sys_user WHERE username = 'boss') THEN
        INSERT INTO sys_user (
            uuid, username, nickname, password, salt, email, 
            status, is_superuser, is_staff, is_multi_login, 
            dept_id, join_time, last_login_time, last_password_changed_time, created_time
        )
        VALUES (
            gen_random_uuid(),
            'boss',
            '租户管理员',
            '$2b$12$VEwQ5h9Z8jZ4YjEQNxJX8.RGPxLhNkL7YT2YfEqXqKvZxW7XvQYPy',
            decode('24326224313224564577513568395a386a5a344a6a45514e784a583865', 'hex'),
            'boss@feedalyze.com',
            1, false, true, true,
            v_dept_id, now(), now(), now(), now()
        )
        RETURNING id INTO v_user_id;
        
        IF v_boss_role_id IS NOT NULL THEN
            INSERT INTO sys_user_role (user_id, role_id) VALUES (v_user_id, v_boss_role_id);
        END IF;
        
        RAISE NOTICE '✅ 创建用户: boss (老板角色)';
    ELSE
        RAISE NOTICE '⏭️  跳过: 用户 boss 已存在';
    END IF;

    -- ============================================================================
    -- 用户 6: hybrid - 混合角色用户（同时拥有系统+业务角色）
    -- ============================================================================
    IF NOT EXISTS (SELECT 1 FROM sys_user WHERE username = 'hybrid') THEN
        INSERT INTO sys_user (
            uuid, username, nickname, password, salt, email, 
            status, is_superuser, is_staff, is_multi_login, 
            dept_id, join_time, last_login_time, last_password_changed_time, created_time
        )
        VALUES (
            gen_random_uuid(),
            'hybrid',
            '混合角色用户',
            '$2b$12$VEwQ5h9Z8jZ4YjEQNxJX8.RGPxLhNkL7YT2YfEqXqKvZxW7XvQYPy',
            decode('24326224313224564577513568395a386a5a344a6a45514e784a583865', 'hex'),
            'hybrid@feedalyze.com',
            1, false, true, true,
            v_dept_id, now(), now(), now(), now()
        )
        RETURNING id INTO v_user_id;
        
        -- 关联系统管理员角色
        IF v_sysadmin_role_id IS NOT NULL THEN
            INSERT INTO sys_user_role (user_id, role_id) VALUES (v_user_id, v_sysadmin_role_id);
        END IF;
        
        -- 关联 PM 角色
        IF v_pm_role_id IS NOT NULL THEN
            INSERT INTO sys_user_role (user_id, role_id) VALUES (v_user_id, v_pm_role_id);
        END IF;
        
        RAISE NOTICE '✅ 创建用户: hybrid (系统管理员+PM角色)';
    ELSE
        RAISE NOTICE '⏭️  跳过: 用户 hybrid 已存在';
    END IF;

END $$;

-- ================================================================================
-- 输出账号清单
-- ================================================================================
SELECT 
    '================================================================================';
SELECT 
    '📝 测试账号清单 - 统一密码：Test123456';
SELECT 
    '================================================================================';
SELECT 
    u.username AS "账号",
    u.nickname AS "昵称",
    u.email AS "邮箱",
    STRING_AGG(r.name, ', ' ORDER BY r.name) AS "角色",
    CASE 
        WHEN STRING_AGG(r.role_type, ', ') LIKE '%system%' AND STRING_AGG(r.role_type, ', ') LIKE '%business%' THEN '全部菜单 (/admin/* + /app/*)'
        WHEN STRING_AGG(r.role_type, ', ') LIKE '%system%' THEN '系统管理菜单 (/admin/*)'
        WHEN STRING_AGG(r.role_type, ', ') LIKE '%business%' THEN '业务功能菜单 (/app/*)'
        ELSE '无权限'
    END AS "菜单权限"
FROM 
    sys_user u
    LEFT JOIN sys_user_role ur ON u.id = ur.user_id
    LEFT JOIN sys_role r ON ur.role_id = r.id
WHERE 
    u.username IN ('sysadmin', 'pm', 'cs', 'dev', 'boss', 'hybrid')
GROUP BY 
    u.id, u.username, u.nickname, u.email
ORDER BY 
    u.username;
SELECT 
    '================================================================================';
SELECT 
    '💡 提示：';
SELECT 
    '  1. 使用上述账号登录前端测试菜单显示功能';
SELECT 
    '  2. 超级管理员账号：admin / Admin123456 (可以看到全部菜单)';
SELECT 
    '  3. 如果角色没有关联菜单，需要在前端"系统管理 > 角色管理"中配置';
SELECT 
    '================================================================================';
