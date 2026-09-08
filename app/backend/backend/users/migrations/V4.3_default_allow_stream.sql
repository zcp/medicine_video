-- V4.3: Flip can_stream default semantics (run against users_service_test DB)
-- 语义变更：默认允许开播，can_stream=false 表示被管理员禁播
-- 幂等设计：已执行过的库重复执行无副作用
ALTER TABLE users ALTER COLUMN can_stream SET DEFAULT true;
UPDATE users SET can_stream = true WHERE can_stream = false;
DROP INDEX IF EXISTS idx_users_can_stream;
CREATE INDEX IF NOT EXISTS idx_users_can_stream ON users(can_stream) WHERE can_stream = FALSE;
COMMENT ON COLUMN users.can_stream IS '是否拥有开播资格；默认允许，false 表示被管理员禁播；与 role 正交';
