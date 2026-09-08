-- ============================================================
-- V12_content_safety_unified.sql
-- content_safety 表结构统一（main 与 wechat-v1 融合，C1 Critical）
--
-- 目标结构（以 wechat-v1 20260703_content_safety.sql 为基底）：
--   - id UUID DEFAULT gen_random_uuid()
--   - enabled（替代旧 is_active）
--   - matched_rule_ids / matched_rule_names JSONB（替代旧 TEXT）
--   - 5 个 CHECK 约束（rules: action/severity/match_type/binding_level，logs: decision）
--   - 医学合规三列 binding_level / rule_category / regulation_ref
--
-- 幂等性：
--   - 新库：直接 CREATE TABLE IF NOT EXISTS
--   - 旧库（is_active 结构）：自动备份数据到 *_legacy 临时表 → DROP 旧表 → 建新表 → 回填数据
--   - 可重复执行
--
-- 适用库：live_core_service 与 users_service 双库
-- ============================================================

-- ========== 0. 旧结构检测与数据备份（幂等） ==========
DO $$
DECLARE
    v_legacy_exists BOOLEAN;
BEGIN
    SELECT EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_name = 'content_safety_rules'
    ) INTO v_legacy_exists;

    IF v_legacy_exists THEN
        -- 仅当旧结构（有 is_active 列）时才迁移；新结构直接跳过
        IF EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name = 'content_safety_rules' AND column_name = 'is_active'
        ) AND NOT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name = 'content_safety_rules' AND column_name = 'enabled'
        ) THEN
            -- 备份旧数据（规则 + 日志）
            DROP TABLE IF EXISTS content_safety_rules_legacy;
            DROP TABLE IF EXISTS content_safety_logs_legacy;
            CREATE TABLE content_safety_rules_legacy AS SELECT * FROM content_safety_rules;
            CREATE TABLE content_safety_logs_legacy AS SELECT * FROM content_safety_logs;
            -- 先删 logs（有 FK 指向 rules），再删 rules
            DROP TABLE IF EXISTS content_safety_logs;
            DROP TABLE IF EXISTS content_safety_rules;
        END IF;
    END IF;
END $$;

-- ========== 1. content_safety_rules（新结构） ==========
CREATE TABLE IF NOT EXISTS content_safety_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rule_name VARCHAR(100) NOT NULL,
    scene VARCHAR(50) NOT NULL,
    target_field VARCHAR(50) NOT NULL,
    match_type VARCHAR(30) NOT NULL,
    pattern TEXT NOT NULL,
    action VARCHAR(20) NOT NULL DEFAULT 'block',
    severity VARCHAR(20) NOT NULL DEFAULT 'high',
    priority INTEGER NOT NULL DEFAULT 100,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    remark VARCHAR(500),
    binding_level VARCHAR(20) NOT NULL DEFAULT 'platform',
    rule_category VARCHAR(50) NOT NULL DEFAULT 'general',
    regulation_ref VARCHAR(200),
    created_by UUID,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_content_safety_rules_action CHECK (action IN ('block', 'warn', 'allow')),
    CONSTRAINT chk_content_safety_rules_severity CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    CONSTRAINT chk_content_safety_rules_match_type CHECK (
        match_type IN ('keyword', 'regex', 'url', 'contact', 'html', 'political', 'porn', 'gambling', 'fraud', 'image_meta')
    ),
    CONSTRAINT chk_content_safety_rules_binding_level CHECK (binding_level IN ('statutory', 'platform'))
);

CREATE INDEX IF NOT EXISTS idx_content_safety_rules_scene_enabled_priority
    ON content_safety_rules (scene, enabled, priority);
CREATE INDEX IF NOT EXISTS idx_content_safety_rules_target_field
    ON content_safety_rules (target_field);
CREATE INDEX IF NOT EXISTS idx_content_safety_rules_created_by
    ON content_safety_rules (created_by);
CREATE INDEX IF NOT EXISTS idx_content_safety_rules_category_enabled
    ON content_safety_rules (rule_category, enabled);
CREATE UNIQUE INDEX IF NOT EXISTS uq_content_safety_rules_rule_name
    ON content_safety_rules (rule_name);

-- ========== 2. content_safety_logs（新结构） ==========
CREATE TABLE IF NOT EXISTS content_safety_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scene VARCHAR(50) NOT NULL,
    resource_type VARCHAR(50) NOT NULL,
    resource_id UUID,
    target_field VARCHAR(50) NOT NULL,
    user_id UUID,
    input_excerpt VARCHAR(500),
    normalized_excerpt VARCHAR(500),
    decision VARCHAR(20) NOT NULL,
    matched_rule_ids JSONB,
    matched_rule_names JSONB,
    reason_code VARCHAR(20),
    reason_message VARCHAR(500),
    request_id VARCHAR(100),
    client_ip VARCHAR(64),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_content_safety_logs_decision CHECK (decision IN ('allow', 'warn', 'block'))
);

CREATE INDEX IF NOT EXISTS idx_content_safety_logs_scene_created
    ON content_safety_logs (scene, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_content_safety_logs_user_created
    ON content_safety_logs (user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_content_safety_logs_resource
    ON content_safety_logs (resource_type, resource_id);
CREATE INDEX IF NOT EXISTS idx_content_safety_logs_decision_created
    ON content_safety_logs (decision, created_at);

-- ========== 3. 旧数据回填（幂等：仅当 legacy 表存在时执行一次） ==========
DO $$
DECLARE
    v_migrated INTEGER;
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_name = 'content_safety_rules_legacy'
    ) THEN
        -- rules 回填：is_active -> enabled，rule_type 丢弃（match_type 已存在）
        INSERT INTO content_safety_rules (
            id, rule_name, scene, target_field, match_type, pattern,
            action, severity, priority, enabled, created_by, created_at, updated_at
        )
        SELECT
            CASE
                WHEN id ~ '^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$'
                THEN id::uuid
                ELSE gen_random_uuid()
            END,
            COALESCE(rule_name, 'rule-' || substr(replace(gen_random_uuid()::text, '-', ''), 1, 8)),
            scene,
            COALESCE(target_field, 'content'),
            COALESCE(match_type, 'keyword'),
            pattern,
            COALESCE(action, 'block'),
            COALESCE(severity, 'high'),
            COALESCE(priority, 100),
            COALESCE(is_active, TRUE),
            CASE
                WHEN created_by ~ '^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$'
                THEN created_by::uuid
                ELSE NULL
            END,
            created_at,
            updated_at
        FROM content_safety_rules_legacy
        ON CONFLICT (id) DO NOTHING;

        GET DIAGNOSTICS v_migrated = ROW_COUNT;
        RAISE NOTICE 'content_safety_rules 迁移完成: % 条', v_migrated;

        -- logs 回填（旧 TEXT 逗号分隔 -> JSONB）
        INSERT INTO content_safety_logs (
            id, scene, resource_type, resource_id, target_field, user_id,
            input_excerpt, normalized_excerpt, decision,
            matched_rule_ids, matched_rule_names,
            reason_code, reason_message, request_id, client_ip, created_at
        )
        SELECT
            CASE
                WHEN id ~ '^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$'
                THEN id::uuid
                ELSE gen_random_uuid()
            END,
            scene,
            COALESCE(resource_type, 'unknown'),
            CASE
                WHEN resource_id ~ '^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$'
                THEN resource_id::uuid
                ELSE NULL
            END,
            COALESCE(target_field, 'content'),
            CASE
                WHEN user_id ~ '^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$'
                THEN user_id::uuid
                ELSE NULL
            END,
            input_excerpt,
            COALESCE(normalized_excerpt, input_excerpt),
            COALESCE(decision, action),
            CASE
                WHEN matched_rule_ids IS NULL THEN NULL
                ELSE to_jsonb(string_to_array(matched_rule_ids, ','))
            END,
            CASE
                WHEN matched_rule_names IS NULL THEN NULL
                ELSE to_jsonb(string_to_array(matched_rule_names, ','))
            END,
            reason_code,
            reason_message,
            request_id,
            client_ip,
            created_at
        FROM content_safety_logs_legacy
        ON CONFLICT (id) DO NOTHING;

        GET DIAGNOSTICS v_migrated = ROW_COUNT;
        RAISE NOTICE 'content_safety_logs 迁移完成: % 条', v_migrated;

        -- 清理 legacy 临时表
        DROP TABLE IF EXISTS content_safety_rules_legacy;
        DROP TABLE IF EXISTS content_safety_logs_legacy;
    END IF;
END $$;
