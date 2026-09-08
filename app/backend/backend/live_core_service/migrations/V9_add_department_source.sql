-- 分类优化 V9：expert_departments 表新增来源追踪字段
-- 背景：自动创建的 is_verified=false 科室无法追溯来源（审查报告问题 8）
-- 前置条件：V8 已执行（非严格依赖，但建议按顺序执行）
-- 幂等性：所有 DDL 使用 IF NOT EXISTS

-- 1) 新增 source 字段
ALTER TABLE expert_departments
ADD COLUMN IF NOT EXISTS source VARCHAR(50);

COMMENT ON COLUMN expert_departments.source IS
'科室创建来源：auto_match=自适应匹配, csv_import=CSV批量导入, manual_create=手动创建专家, admin_api=管理员API直接创建, seed_v4=V4种子, seed_s4=S4种子扩展, unknown_legacy=无法追溯的历史数据';

-- 2) 新增 created_by 字段
ALTER TABLE expert_departments
ADD COLUMN IF NOT EXISTS created_by UUID;

COMMENT ON COLUMN expert_departments.created_by IS
'创建人 user_id。自适应匹配时为 NULL（无用户上下文），管理员手动创建时记录';

-- 3) 索引
CREATE INDEX IF NOT EXISTS idx_expert_departments_source ON expert_departments(source);
CREATE INDEX IF NOT EXISTS idx_expert_departments_created_by ON expert_departments(created_by);

-- 4) 回填历史数据：所有现有 is_verified=true 的标记为种子数据
UPDATE expert_departments
SET source = 'seed_v4'
WHERE source IS NULL
  AND is_verified = true;

-- is_verified=false 的历史数据标记为 unknown（无法追溯）
UPDATE expert_departments
SET source = 'unknown_legacy'
WHERE source IS NULL
  AND is_verified = false;
