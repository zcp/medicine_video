-- 专家模块 is_active 增量迁移
-- 执行前请确认 experts 表已存在
-- 已有数据 is_active 默认为 true

-- 新增列（在现有 experts 表上）
ALTER TABLE experts
ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT true;

COMMENT ON COLUMN experts.is_active IS '是否启用（false 表示软删除/下架）';

-- 索引（用于 Admin 列表按 is_active 筛选）
CREATE INDEX IF NOT EXISTS idx_experts_is_active ON experts(is_active);
