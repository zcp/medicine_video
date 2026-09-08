"""废弃 brand_members / brand_products（产品仅保留品牌主体）"""

import logging

from sqlalchemy import text

from app.database import engine

logger = logging.getLogger(__name__)

_STATEMENTS = [
    "DROP TABLE IF EXISTS brand_members CASCADE",
    "DROP TABLE IF EXISTS brand_products CASCADE",
]


def migrate_brand_commerce_schema() -> None:
    with engine.begin() as conn:
        for stmt in _STATEMENTS:
            conn.execute(text(stmt))
    logger.info("brand_members / brand_products 已废弃并 DROP")
