-- 清理 board 表中重复的 default-board 记录
-- 问题：有 2 条 id='default-board' 的记录，违反主键唯一性

-- ================================
-- 第一步：查看当前状态
-- ================================

-- 查看重复的 default-board 记录
SELECT * FROM boards WHERE id = 'default-board';

-- 查看有多少 feedbacks 引用了 default-board
SELECT board_id, COUNT(*) as count 
FROM feedbacks 
WHERE board_id = 'default-board' 
GROUP BY board_id;

-- 查看有多少 topics 引用了 default-board
SELECT board_id, COUNT(*) as count 
FROM topics 
WHERE board_id = 'default-board' 
GROUP BY board_id;

-- ================================
-- 第二步：查找要保留哪个记录
-- ================================

-- 通过创建时间判断，保留最早创建的那个
SELECT id, name, created_at, updated_at, display_order, tenant_id
FROM boards 
WHERE id = 'default-board'
ORDER BY created_at ASC;

-- ================================
-- 第三步：执行清理（在事务中执行）
-- ================================

BEGIN;

-- 由于外键设置了 ondelete=CASCADE，理论上删除 board 会级联删除相关数据
-- 但这里有个问题：有 2 个 id='default-board'，这违反了主键唯一性约束
-- PostgreSQL 不应该允许这种情况存在，除非是通过某些特殊方式插入的

-- 解决方案：使用 ctid (PostgreSQL 的物理行标识符) 来精确删除其中一个

-- 查看两条记录的 ctid（物理位置）
SELECT ctid, id, name, created_at, tenant_id
FROM boards 
WHERE id = 'default-board';

-- 删除其中一个（根据上面查询的结果，选择要删除的 ctid）
-- 示例：假设要删除 ctid = '(0,2)' 的那条记录
-- DELETE FROM boards WHERE ctid = '(0,2)';

-- 请根据实际查询结果，选择正确的 ctid 后再执行删除

-- 提交事务
-- COMMIT;

-- 如果出错，回滚
-- ROLLBACK;

-- ================================
-- 第四步：验证清理结果
-- ================================

-- 确认只剩一条 default-board 记录
SELECT COUNT(*) FROM boards WHERE id = 'default-board';

-- 查看保留的记录
SELECT * FROM boards WHERE id = 'default-board';
