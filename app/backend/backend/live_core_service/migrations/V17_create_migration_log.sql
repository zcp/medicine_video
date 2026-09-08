-- 分类优化 V17：migration_log 表（迁移执行记录）
-- 背景：历史迁移全部手动执行、无执行记录，导致各环境执行状态不一致（V8 漏执行、S4 种子部分入库）
-- 目的：migration_log 记录已执行的迁移文件，配合 scripts/run_migrations.py 统一入口，防重放、防遗漏
-- 幂等性：CREATE TABLE IF NOT EXISTS，可重复执行

CREATE TABLE IF NOT EXISTS migration_log (
    id SERIAL PRIMARY KEY,
    migration_name VARCHAR(255) NOT NULL UNIQUE,
    status VARCHAR(20) NOT NULL DEFAULT 'applied',
    detail TEXT,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 索引：按执行时间查询
CREATE INDEX IF NOT EXISTS idx_migration_log_applied_at ON migration_log (applied_at);
