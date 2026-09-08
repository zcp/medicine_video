"""
健康检查模块的 Service 层 (学院派)
职责：
- 调用CRUD层进行数据库连接测试
"""
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud import health as crud_health
import logging

logger = logging.getLogger(__name__)

class HealthService:
    """健康检查Service"""
    
    def __init__(self):
        pass
    
    async def check_readiness(
        self,
        db: AsyncSession
    ) -> dict:
        """
        检查服务就绪状态（包含数据库连接测试）
        
        Args:
            db: 数据库会话
        
        Returns:
            dict: 包含状态信息的字典
                {
                    "status": "ready" | "not_ready",
                    "database": "connected" | "disconnected",
                    "error": str | None
                }
        """
        # 调用CRUD层测试数据库连接
        is_connected = await crud_health.check_database_connection(db)
        
        if is_connected:
            return {
                "status": "ready",
                "database": "connected",
                "error": None
            }
        else:
            return {
                "status": "not_ready",
                "database": "disconnected",
                "error": "连接数据库失败"
            }

