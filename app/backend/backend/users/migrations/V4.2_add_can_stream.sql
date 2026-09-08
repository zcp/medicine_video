-- V4.2: Add can_stream column to users table (run against users_service_test DB)
-- 注意：语义已由 V4.3_default_allow_stream.sql 翻转（默认允许开播，false 表示禁播）。
-- 本脚本保留仅作历史记录，勿再单独执行。
ALTER TABLE users ADD COLUMN IF NOT EXISTS can_stream BOOLEAN NOT NULL DEFAULT FALSE;
COMMENT ON COLUMN users.can_stream IS '是否拥有开播资格；与 role 正交';
CREATE INDEX IF NOT EXISTS idx_users_can_stream ON users(can_stream) WHERE can_stream = TRUE;
