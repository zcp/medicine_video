-- 医学合规文本违禁词库 — content_safety_rules 增量 DDL
-- 适用：live_core_test / users_service_test（结构一致）

ALTER TABLE content_safety_rules
    ADD COLUMN IF NOT EXISTS binding_level VARCHAR(20) NOT NULL DEFAULT 'platform',
    ADD COLUMN IF NOT EXISTS rule_category VARCHAR(50) NOT NULL DEFAULT 'general',
    ADD COLUMN IF NOT EXISTS regulation_ref VARCHAR(200);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'chk_content_safety_rules_binding_level'
    ) THEN
        ALTER TABLE content_safety_rules
            ADD CONSTRAINT chk_content_safety_rules_binding_level
                CHECK (binding_level IN ('statutory', 'platform'));
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_content_safety_rules_category_enabled
    ON content_safety_rules (rule_category, enabled);

CREATE UNIQUE INDEX IF NOT EXISTS uq_content_safety_rules_rule_name
    ON content_safety_rules (rule_name);

COMMENT ON COLUMN content_safety_rules.binding_level IS
    '强制级别：statutory=国家法定词库（禁止运营关闭）；platform=平台自主词库';
COMMENT ON COLUMN content_safety_rules.rule_category IS
    '违禁词分类编码，见 add-docs/13 §2';
COMMENT ON COLUMN content_safety_rules.regulation_ref IS
    '法规/规范溯源，如 广告法§16；多条用分号分隔';
