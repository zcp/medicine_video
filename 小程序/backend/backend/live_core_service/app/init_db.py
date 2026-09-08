import logging
from app.database import engine, Base


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

import app.models  # 确保所有模型被导入

def init_db():
    """初始化数据库，创建所有表"""
    try:
        print("当前 metadata 中的表名列表：", Base.metadata.tables.keys())
        Base.metadata.create_all(bind=engine)
        from app.content_safety.migrate import migrate_content_safety_schema
        from app.migrations.migrate_brand_commerce import migrate_brand_commerce_schema

        migrate_content_safety_schema()
        migrate_brand_commerce_schema()
        logger.info("数据库表创建成功")
    except Exception as e:
        logger.error(f"数据库表创建失败: {str(e)}")
        raise

if __name__ == "__main__":
    logger.info("开始创建数据库表...")
    init_db()
    logger.info("数据库表创建完成")