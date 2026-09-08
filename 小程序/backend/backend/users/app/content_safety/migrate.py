"""内容安全表结构增量迁移（医学合规词库 DDL）"""

import logging

from sqlalchemy import text

from app.database import engine

logger = logging.getLogger(__name__)

_MIGRATION_STATEMENTS = [
    """
    ALTER TABLE content_safety_rules
        ADD COLUMN IF NOT EXISTS binding_level VARCHAR(20) NOT NULL DEFAULT 'platform',
        ADD COLUMN IF NOT EXISTS rule_category VARCHAR(50) NOT NULL DEFAULT 'general',
        ADD COLUMN IF NOT EXISTS regulation_ref VARCHAR(200)
    """,
    """
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM pg_constraint WHERE conname = 'chk_content_safety_rules_binding_level'
        ) THEN
            ALTER TABLE content_safety_rules
                ADD CONSTRAINT chk_content_safety_rules_binding_level
                    CHECK (binding_level IN ('statutory', 'platform'));
        END IF;
    END $$
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_content_safety_rules_category_enabled
        ON content_safety_rules (rule_category, enabled)
    """,
    """
    CREATE UNIQUE INDEX IF NOT EXISTS uq_content_safety_rules_rule_name
        ON content_safety_rules (rule_name)
    """,
]


def migrate_content_safety_schema() -> None:
    """幂等执行 content_safety_rules 增量列与索引"""
    with engine.begin() as conn:
        for stmt in _MIGRATION_STATEMENTS:
            conn.execute(text(stmt))
    logger.info("content_safety_rules 医学合规增量 DDL 已就绪")
