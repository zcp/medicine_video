-- V4.2: Complete content_safety table DDL (for fresh deployments)
-- Run this only if tables do not exist yet.

CREATE TABLE IF NOT EXISTS content_safety_rules (
    id VARCHAR(36) PRIMARY KEY,
    scene VARCHAR(50) NOT NULL,
    rule_type VARCHAR(50) NOT NULL DEFAULT 'keyword',
    pattern TEXT NOT NULL,
    action VARCHAR(20) NOT NULL DEFAULT 'block',
    rule_name VARCHAR(100),
    priority INTEGER NOT NULL DEFAULT 0,
    match_type VARCHAR(20) NOT NULL DEFAULT 'keyword',
    target_field VARCHAR(50),
    severity VARCHAR(20) NOT NULL DEFAULT 'high',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_by VARCHAR(36),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_cs_rules_scene_active ON content_safety_rules(scene, is_active);

CREATE TABLE IF NOT EXISTS content_safety_logs (
    id VARCHAR(36) PRIMARY KEY,
    rule_id VARCHAR(36) REFERENCES content_safety_rules(id) ON DELETE SET NULL,
    scene VARCHAR(50) NOT NULL,
    user_id VARCHAR(36),
    content TEXT,
    action VARCHAR(20),
    matched_pattern TEXT,
    resource_type VARCHAR(50),
    decision VARCHAR(20),
    resource_id VARCHAR(36),
    target_field VARCHAR(50),
    input_excerpt TEXT,
    normalized_excerpt TEXT,
    matched_rule_ids TEXT,
    matched_rule_names TEXT,
    reason_code VARCHAR(50),
    reason_message TEXT,
    request_id VARCHAR(64),
    client_ip VARCHAR(45),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_cs_logs_scene_created ON content_safety_logs(scene, created_at);
