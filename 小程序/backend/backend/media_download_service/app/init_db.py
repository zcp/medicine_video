import logging
from app.database import engine, Base
# 导入所有模型类，确保它们被注册到 Base.metadata 中
from app.models.download import DownloadTask, DownloadFailure, DownloadedVideo
from app.models.crawl_import_status import CrawlImportStatus

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_db():
    """初始化数据库，创建所有表"""
    try:
        # 创建所有表
        print("当前 metadata 中的表名列表：", Base.metadata.tables.keys())
        Base.metadata.create_all(bind=engine)
        logger.info("数据库表创建成功")
    except Exception as e:
        logger.error(f"数据库表创建失败: {str(e)}")
        raise

if __name__ == "__main__":
    logger.info("开始创建数据库表...")
    init_db()
    logger.info("数据库表创建完成") 