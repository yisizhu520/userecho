-- 创建 insights 表
-- 用于存储 AI 生成的洞察快照

CREATE TABLE IF NOT EXISTS insights (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL,
    
    -- 分类与时间范围
    insight_type VARCHAR(20) NOT NULL,  -- priority_suggestion | high_risk | weekly_report | sentiment_trend
    time_range VARCHAR(20) NOT NULL,    -- this_week | this_month | custom
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    
    -- 洞察内容（JSON 存储）
    content JSON NOT NULL,
    
    -- 元数据
    generated_by VARCHAR(20) NOT NULL,  -- ai | rule_engine | hybrid
    confidence FLOAT NULL,              -- AI 置信度 (0.0-1.0)
    execution_time_ms INTEGER NULL,     -- 生成耗时（毫秒）
    
    -- 状态
    status VARCHAR(20) NOT NULL DEFAULT 'active',  -- active | archived | dismissed
    dismissed_reason TEXT NULL,
    
    -- 时间戳
    created_time TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_time TIMESTAMP WITH TIME ZONE NULL,
    deleted_at TIMESTAMP WITH TIME ZONE NULL,
    
    -- 外键约束
    CONSTRAINT fk_insights_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_insights_tenant_type_time ON insights (tenant_id, insight_type, start_date);
CREATE INDEX IF NOT EXISTS idx_insights_status ON insights (status);
CREATE INDEX IF NOT EXISTS idx_insights_type ON insights (insight_type);

-- 添加表注释
COMMENT ON TABLE insights IS '洞察实例表（AI 生成的洞察快照）';
COMMENT ON COLUMN insights.id IS '洞察ID';
COMMENT ON COLUMN insights.tenant_id IS '租户ID';
COMMENT ON COLUMN insights.insight_type IS '洞察类型';
COMMENT ON COLUMN insights.time_range IS '时间范围';
COMMENT ON COLUMN insights.start_date IS '开始日期';
COMMENT ON COLUMN insights.end_date IS '结束日期';
COMMENT ON COLUMN insights.content IS '洞察内容（JSON 格式）';
COMMENT ON COLUMN insights.generated_by IS '生成方式';
COMMENT ON COLUMN insights.confidence IS 'AI 置信度';
COMMENT ON COLUMN insights.execution_time_ms IS '生成耗时（毫秒）';
COMMENT ON COLUMN insights.status IS '状态';
COMMENT ON COLUMN insights.dismissed_reason IS '用户忽略的原因';
COMMENT ON COLUMN insights.created_time IS '创建时间';
COMMENT ON COLUMN insights.updated_time IS '更新时间';
COMMENT ON COLUMN insights.deleted_at IS '软删除时间';
