-- V15: live_sessions 新增 source_type 字段
-- 用途：区分场次直播来源——push（推流，SRS 回调驱动状态）/ external（外部流，用户手动切换状态）
-- 默认 'push'，存量场次零影响

-- 1. 新增 source_type 字段
ALTER TABLE live_sessions
    ADD COLUMN source_type VARCHAR(16) NOT NULL DEFAULT 'push';

-- 2. 字段注释
COMMENT ON COLUMN live_sessions.source_type
    IS '直播来源：push=推流（SRS 回调驱动状态）；external=外部流（用户手动切换状态）';

-- 3. 回滚语句（如需）
-- ALTER TABLE live_sessions DROP COLUMN source_type;
