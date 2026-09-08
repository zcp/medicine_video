-- 内容安全模块表（live_core_test / users_service_test 均可执行）
-- 若使用 SQLAlchemy create_all 建表，本脚本作为增量备份

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
    created_by UUID,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_content_safety_rules_action CHECK (action IN ('block', 'warn', 'allow')),
    CONSTRAINT chk_content_safety_rules_severity CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    CONSTRAINT chk_content_safety_rules_match_type CHECK (
        match_type IN ('keyword', 'regex', 'url', 'contact', 'html', 'political', 'porn', 'gambling', 'fraud', 'image_meta')
    )
);

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

CREATE INDEX IF NOT EXISTS idx_content_safety_rules_scene_enabled_priority
    ON content_safety_rules (scene, enabled, priority);
CREATE INDEX IF NOT EXISTS idx_content_safety_logs_scene_created
    ON content_safety_logs (scene, created_at DESC);

-- 医学合规增量（add-docs/13 §1.1，亦可通过 migrate_content_safety_schema() 执行）
ALTER TABLE content_safety_rules
    ADD COLUMN IF NOT EXISTS binding_level VARCHAR(20) NOT NULL DEFAULT 'platform',
    ADD COLUMN IF NOT EXISTS rule_category VARCHAR(50) NOT NULL DEFAULT 'general',
    ADD COLUMN IF NOT EXISTS regulation_ref VARCHAR(200);

CREATE INDEX IF NOT EXISTS idx_content_safety_rules_category_enabled
    ON content_safety_rules (rule_category, enabled);

CREATE UNIQUE INDEX IF NOT EXISTS uq_content_safety_rules_rule_name
    ON content_safety_rules (rule_name);
