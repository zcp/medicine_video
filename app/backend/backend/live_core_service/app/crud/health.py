"""
健康检查模块的 CRUD 层 (学院派)
职责：数据库连接测试
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)

async def check_database_connection(db: AsyncSession) -> bool:
    """
    测试数据库连接是否正常
    
    Args:
        db: 数据库会话
    
    Returns:
        bool: True表示连接正常，False表示连接失败
    """
    try:
        # 执行简单查询测试连接
        result = await db.execute(text("SELECT 1"))
        result.scalar()
        
        logger.debug("数据库连接测试成功")
        return True
        
    except Exception as e:
        # 记录错误日志（不抛出异常，由调用方处理）
        logger.error(
            f"数据库连接测试失败: error={str(e)}, error_type={type(e).__name__}"
        )
        return False

