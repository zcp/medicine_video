-- ==========================================================
-- 迁移：tags 用户自建溯源（02 标签管理 V2 阶段 2 / 主分支 V18）
-- 说明：不改 name 唯一约束；不 DROP；可重复执行（幂等）
--
-- 常规执行：由 scripts/run_migrations.py 自动收录执行（migration_log 防重放）
--   cd /app && python scripts/run_migrations.py
--
-- 手工执行示例（保留 volume，勿 down -v）:
--   docker exec -i live-streaming-saas-v2-main-postgres-1 \
--     psql -U postgres -d live_core_test < \
--     backend/live_core_service/migrations/V18_tags_user_create_attribution.sql
-- ==========================================================

ALTER TABLE tags
    ADD COLUMN IF NOT EXISTS created_by UUID NULL,
    ADD COLUMN IF NOT EXISTS source VARCHAR(16) NOT NULL DEFAULT 'admin';

COMMENT ON COLUMN tags.created_by IS '创建者 public_id；Admin 手工创建可为 NULL';
COMMENT ON COLUMN tags.source IS '来源：admin=运营创建；user=用户 resolve 创建';

-- 历史数据：视为运营词表
UPDATE tags SET source = 'admin' WHERE source IS NULL OR source = '';

CREATE INDEX IF NOT EXISTS idx_tags_source ON tags(source);
CREATE INDEX IF NOT EXISTS idx_tags_created_by ON tags(created_by);
