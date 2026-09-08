-- 管理端数据面板: 为 experts 表新增 is_verified 审核状态字段
-- 创建日期: 2026-07-23
-- 执行方式: psql -U postgres -d live_core_test -f migrations/add_experts_is_verified.sql

-- Step 1: 新增 is_verified 列（幂等）
ALTER TABLE experts
  ADD COLUMN IF NOT EXISTS is_verified BOOLEAN NOT NULL DEFAULT FALSE;

COMMENT ON COLUMN experts.is_verified IS '审核状态: False=待审批, True=已审批';

-- Step 2: 将现有已启用(is_active=True)的专家标记为已审批
-- 避免存量专家数据全部变为待审批，影响运营
UPDATE experts SET is_verified = TRUE WHERE is_active = TRUE AND is_verified = FALSE;
