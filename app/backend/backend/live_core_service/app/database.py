from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import logging

# 导入统一配置
from app.core.config import settings

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建数据库引擎
try:
    # 使用统一配置
    DATABASE_URL = settings.SYNC_DATABASE_URL
    ASYNC_DATABASE_URL = settings.DATABASE_URL
    
    # 安全日志：不打印完整连接URL（包含密码）
    logger.info(
        f"尝试连接数据库: "
        f"server={settings.POSTGRES_SERVER}, "
        f"port={settings.POSTGRES_PORT}, "
        f"database={settings.POSTGRES_DB}, "
        f"user={settings.POSTGRES_USER}"
        # 不打印密码
    )

    # 同步引擎（用于初始化）
    engine = create_engine(
        DATABASE_URL,
        echo=True  # 打印 SQL 语句，方便调试
    )

    # 异步引擎（用于应用）
    async_engine = create_async_engine(
        ASYNC_DATABASE_URL,
        echo=True  # 打印 SQL 语句，方便调试
    )

    # 测试连接
    with engine.connect() as conn:
        logger.info("数据库连接成功！")
except Exception as e:
    logger.error(f"数据库连接失败: {str(e)}")
    raise

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
#async def get_async_db() -> AsyncSession:
#    async with AsyncSessionLocal() as session:
#        try:
#            yield session
#        finally:
#            await session.close()

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