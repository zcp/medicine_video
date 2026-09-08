-- V4.2: Add missing columns to content_safety_rules and content_safety_logs
-- ===== content_safety_rules =====
ALTER TABLE content_safety_rules ADD COLUMN IF NOT EXISTS rule_name VARCHAR(100);
ALTER TABLE content_safety_rules ADD COLUMN IF NOT EXISTS priority INTEGER NOT NULL DEFAULT 0;
ALTER TABLE content_safety_rules ADD COLUMN IF NOT EXISTS match_type VARCHAR(20) NOT NULL DEFAULT 'keyword';
ALTER TABLE content_safety_rules ADD COLUMN IF NOT EXISTS target_field VARCHAR(50);
ALTER TABLE content_safety_rules ADD COLUMN IF NOT EXISTS severity VARCHAR(20) NOT NULL DEFAULT 'high';
COMMENT ON COLUMN content_safety_rules.rule_name IS '规则名称（用于识别和日志）';
COMMENT ON COLUMN content_safety_rules.priority IS '优先级（数值越小优先级越高）';
COMMENT ON COLUMN content_safety_rules.match_type IS '匹配方式：keyword/regex/contact/url/image_meta';
COMMENT ON COLUMN content_safety_rules.target_field IS '目标字段名（content/title/description等）';
COMMENT ON COLUMN content_safety_rules.severity IS '严重级别：low/medium/high/critical';

-- ===== content_safety_logs — 基础字段 =====
ALTER TABLE content_safety_logs ADD COLUMN IF NOT EXISTS resource_type VARCHAR(50);
ALTER TABLE content_safety_logs ADD COLUMN IF NOT EXISTS decision VARCHAR(20);
ALTER TABLE content_safety_logs ADD COLUMN IF NOT EXISTS resource_id VARCHAR(36);
ALTER TABLE content_safety_logs ADD COLUMN IF NOT EXISTS target_field VARCHAR(50);
ALTER TABLE content_safety_logs ADD COLUMN IF NOT EXISTS input_excerpt TEXT;
ALTER TABLE content_safety_logs ADD COLUMN IF NOT EXISTS normalized_excerpt TEXT;
ALTER TABLE content_safety_logs ADD COLUMN IF NOT EXISTS matched_rule_ids TEXT;
ALTER TABLE content_safety_logs ADD COLUMN IF NOT EXISTS matched_rule_names TEXT;
ALTER TABLE content_safety_logs ADD COLUMN IF NOT EXISTS reason_code VARCHAR(50);
ALTER TABLE content_safety_logs ADD COLUMN IF NOT EXISTS reason_message TEXT;
ALTER TABLE content_safety_logs ADD COLUMN IF NOT EXISTS request_id VARCHAR(64);
ALTER TABLE content_safety_logs ADD COLUMN IF NOT EXISTS client_ip VARCHAR(45);
COMMENT ON COLUMN content_safety_logs.resource_type IS '资源类型：message/room/room_tab/search_query等';
COMMENT ON COLUMN content_safety_logs.decision IS '检查结果：allow/block/warn';
COMMENT ON COLUMN content_safety_logs.resource_id IS '被检查的资源ID';
COMMENT ON COLUMN content_safety_logs.target_field IS '被检查的目标字段名';
COMMENT ON COLUMN content_safety_logs.input_excerpt IS '输入内容的摘要/截断';
COMMENT ON COLUMN content_safety_logs.normalized_excerpt IS '标准化后的内容摘要';
COMMENT ON COLUMN content_safety_logs.matched_rule_ids IS '命中规则的ID列表（逗号分隔）';
COMMENT ON COLUMN content_safety_logs.matched_rule_names IS '命中规则的名称列表（逗号分隔）';
COMMENT ON COLUMN content_safety_logs.reason_code IS '原因码';
COMMENT ON COLUMN content_safety_logs.reason_message IS '原因描述';
COMMENT ON COLUMN content_safety_logs.request_id IS '请求ID';
COMMENT ON COLUMN content_safety_logs.client_ip IS '客户端IP';
