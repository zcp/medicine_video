"""users.can_stream 幂等增量迁移

V2 P0：新增列（历史默认 false）。
后续产品切换：默认人人可播；false 表示运营禁止开播。
"""

import logging

from sqlalchemy import text

from app.database import engine

logger = logging.getLogger(__name__)

_MIGRATION_STATEMENTS = [
    # 兼容从未跑过旧迁移的库；已存在则跳过
    """
    ALTER TABLE users
      ADD COLUMN IF NOT EXISTS can_stream BOOLEAN NOT NULL DEFAULT TRUE
    """,
    """
    ALTER TABLE users
      ALTER COLUMN can_stream SET DEFAULT TRUE
    """,
    # 产品切换：存量未授出（false）一次性开通；禁止开播由运营事后再设 false
    """
    UPDATE users SET can_stream = TRUE WHERE can_stream = FALSE
    """,
    """
    COMMENT ON COLUMN users.can_stream IS
      '默认 true 可开播；false 表示被禁止开播；与 role 正交'
    """,
    # 索引改为筛「被禁开播」用户（默认可播后 true 占绝大多数）
    """
    DROP INDEX IF EXISTS idx_users_can_stream
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_users_can_stream
      ON users(can_stream)
      WHERE can_stream = FALSE
    """,
]


def migrate_can_stream_schema() -> None:
    """幂等：确保 can_stream 默认 true、存量回填、注释与索引就绪"""
    with engine.begin() as conn:
        for stmt in _MIGRATION_STATEMENTS:
            conn.execute(text(stmt))
    logger.info("users.can_stream 默认开通迁移已就绪")
