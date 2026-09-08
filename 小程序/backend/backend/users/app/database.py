"""
数据库配置和连接管理
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import logging

# 导入配置
from app.core.config import settings

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建数据库引擎
# 使用配置模块的连接URL
logger.info("正在初始化数据库连接...")

# 同步引擎（用于初始化）
engine = create_engine(
    settings.SYNC_DATABASE_URL,
    echo=settings.DEBUG  # 根据DEBUG模式决定是否打印SQL
)

# 异步引擎（用于应用）
async_engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG  # 根据DEBUG模式决定是否打印SQL
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建异步会话工厂
AsyncSessionLocal = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False
)

# 创建基类
Base = declarative_base()

# 获取数据库会话（同步）
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 获取异步数据库会话
async def get_async_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            if session.is_active:
                await session.commit()  # 显式提交事务
        except Exception as e:
            if session.is_active:
                await session.rollback()
            raise
        finally:
            await session.close()

# 为了保持兼容性，将get_db指向异步版本
get_db = get_async_db 