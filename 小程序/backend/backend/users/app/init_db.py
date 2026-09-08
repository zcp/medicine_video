"""Users Service - 数据库初始化"""

import logging

from app.database import engine, Base

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

import app.models  # noqa: F401,E402  确保所有模型被导入


def init_db():
    """初始化数据库，创建所有表"""
    try:
        logger.info("当前 metadata 中的表: %s", list(Base.metadata.tables.keys()))
        Base.metadata.create_all(bind=engine)
        from app.content_safety.migrate import migrate_content_safety_schema
        from app.migrations.migrate_can_stream import migrate_can_stream_schema

        migrate_content_safety_schema()
        migrate_can_stream_schema()
        logger.info("数据库表创建成功")
    except Exception as e:
        logger.error("数据库表创建失败: %s", e)
        raise


async def seed_content_safety():
    """异步种子：默认规则"""
    from app.database import AsyncSessionLocal
    from app.content_safety.seed import seed_default_rules

    async with AsyncSessionLocal() as session:
        try:
            await seed_default_rules(session)
            await session.commit()
        except Exception:
            await session.rollback()
            raise


if __name__ == "__main__":
    init_db()
