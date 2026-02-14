-- 手动添加截图相关字段到 feedbacks 表
-- 执行时间：2025-12-28

BEGIN;

-- 添加新字段
ALTER TABLE feedbacks 
    ADD COLUMN IF NOT EXISTS screenshot_url TEXT,
    ADD COLUMN IF NOT EXISTS source_platform VARCHAR(50),
    ADD COLUMN IF NOT EXISTS source_user_name VARCHAR(255),
    ADD COLUMN IF NOT EXISTS source_user_id VARCHAR(255),
    ADD COLUMN IF NOT EXISTS ai_confidence FLOAT,
    ADD COLUMN IF NOT EXISTS submitter_id BIGINT;

-- 添加外键约束
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'feedbacks_submitter_id_fkey'
    ) THEN
        ALTER TABLE feedbacks 
        ADD CONSTRAINT feedbacks_submitter_id_fkey 
        FOREIGN KEY (submitter_id) REFERENCES sys_user(id) ON DELETE SET NULL;
    END IF;
END$$;

-- 添加注释
COMMENT ON COLUMN feedbacks.screenshot_url IS '截图 OSS 地址';
COMMENT ON COLUMN feedbacks.source_platform IS '来源平台: wechat, xiaohongshu, appstore, weibo, other';
COMMENT ON COLUMN feedbacks.source_user_name IS '来源平台用户昵称';
COMMENT ON COLUMN feedbacks.source_user_id IS '来源平台用户 ID';
COMMENT ON COLUMN feedbacks.ai_confidence IS 'AI 识别置信度 (0.00-1.00)';
COMMENT ON COLUMN feedbacks.submitter_id IS '内部提交者（员工）ID';

-- 更新 source 字段的注释
COMMENT ON COLUMN feedbacks.source IS '来源: manual, import, api, screenshot';

COMMIT;
