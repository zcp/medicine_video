#!/usr/bin/env python3
"""
LiveCore Service - Database Table Creation Script

This script initializes database by creating all tables defined in SQLAlchemy models.
It should be run from project root directory (live_core_service/).

Usage:
    python -m app.scripts.create_tables
"""
import logging
import sys
import os
from pathlib import Path

# 🔧 关键修复：显式加载 .env 文件
# 解决使用 `python -m app.scripts.create_tables` 时环境变量未正确加载的问题
try:
    from dotenv import load_dotenv
    load_dotenv()
    logger = logging.getLogger(__name__)
    logger.info("[SUCCESS] .env 文件已显式加载")
except ImportError:
    logger = logging.getLogger(__name__)
    logger.warning("[WARN] python-dotenv 未安装，尝试手动加载 .env 文件...")
    # 手动加载 .env 文件
    env_file = Path(".env")
    if env_file.exists():
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()
        logger.info("[SUCCESS] .env 文件已手动加载")
    else:
        logger.error("[ERROR] .env 文件不存在")

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('database_init.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)


def init_db():
    """
    初始化数据库，创建所有表
    
    这个函数会：
    1. 导入数据库引擎
    2. 导入所有模型以确保它们被注册到元数据中
    3. 创建所有表
    """
    try:
        logger.info("开始数据库初始化...")
        
        # 导入数据库引擎
        from ..database import engine
        
        # 导入Base和所有模型类
        # 这是关键步骤：必须显式导入所有模型类，以确保SQLAlchemy的元数据能够注册它们
        from ..models.live_core import (
            Base,
            LiveRoom,
            LiveSession,
            SessionStatistics,
            LiveSessionStatus
        )
        from ..models.topic import Topic, TopicCategory, TopicCategoryRoom
        from ..models.live_features import LiveRoomMessage, LiveRoomTab
        from ..models.experts import Expert, UserExpertSubscription, LiveSessionExpert
        from ..models.content_management import Tag, Category, SessionTag
        from ..models.user_preference_notification import UserPreferences, Notification
        from ..models.brand import Brand, BrandTopic, BrandRoom
        from ..models.homepage_search import FeaturedContent
        from ..models.user_behavior import UserFavorite, WatchHistory, UserSubscription, SubscriptionTargetType
        
        logger.info("成功导入数据库引擎和模型")
        
        # 获取所有表名
        table_names = list(Base.metadata.tables.keys())
        logger.info(f"发现 {len(table_names)} 个表需要创建")
        
        # 列出将要创建的表
        for table_name in table_names:
            logger.info(f"  - {table_name}")
        
        # 创建所有表
        logger.info("开始创建数据库表...")
        Base.metadata.create_all(bind=engine)
        
        logger.info("[SUCCESS] 数据库表创建成功！")
        logger.info("已创建的表:")
        for table_name in table_names:
            logger.info(f"  [OK] {table_name}")
            
        return True
        
    except ImportError as e:
        logger.error(f"[ERROR] 导入错误: {str(e)}")
        logger.error("请确保:")
        logger.error("  1. 从项目根目录 (live_core_service/) 运行此脚本")
        logger.error("  2. 使用正确的模块路径: python -m app.scripts.create_tables")
        logger.error("  3. 所有依赖包已正确安装")
        logger.error("  4. 数据库配置文件 (app/database.py) 存在且正确")
        return False
        
    except Exception as e:
        logger.error(f"[ERROR] 数据库初始化失败: {str(e)}")
        logger.error("可能的原因:")
        logger.error("  1. 数据库连接配置错误")
        logger.error("  2. 数据库服务器未运行")
        logger.error("  3. 数据库用户权限不足")
        logger.error("  4. 数据库不存在")
        return False


def check_environment():
    """
    检查运行环境是否正确
    """
    logger.info("检查运行环境...")
    
    # 检查是否在正确的目录中运行
    current_dir = Path.cwd()
    logger.info(f"当前工作目录: {current_dir}")
    
    # 检查必要的文件是否存在
    required_files = [
        "app/database.py",
        "app/models/live_core.py",
    ]
    
    for file_path in required_files:
        if not Path(file_path).exists():
            logger.error(f"[ERROR] 缺少必要文件: {file_path}")
            return False
        else:
            logger.info(f"[OK] 找到文件: {file_path}")
    
    # 检查 .env 文件是否存在
    env_file = Path(".env")
    if not env_file.exists():
        logger.warning("[WARN] .env 文件不存在，将使用默认配置或 .env.example 中的配置")
        logger.warning("💡 提示：请复制 .env.example 为 .env 并填写配置")
    else:
        logger.info("[OK] .env 文件存在")
    
    return True


def main():
    """
    主函数
    """
    logger.info("=" * 60)
    logger.info("LiveCore Service - 数据库初始化脚本")
    logger.info("=" * 60)
    
    # 检查环境
    if not check_environment():
        logger.error("[ERROR] 环境检查失败，退出")
        sys.exit(1)
    
    # 初始化数据库
    if init_db():
        logger.info("=" * 60)
        logger.info("[SUCCESS] 数据库初始化完成！")
        logger.info("=" * 60)
        sys.exit(0)
    else:
        logger.error("=" * 60)
        logger.error("[ERROR] 数据库初始化失败！")
        logger.error("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()
