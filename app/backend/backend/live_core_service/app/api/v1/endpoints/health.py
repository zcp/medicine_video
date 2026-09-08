"""
健康检查模块的 API 端点层 (学院派)
"""
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone
from typing import Dict, Any
import logging

from app.core.deps import get_db
from app.core.response import success_response, error_response
from app.core.config import settings
from app.services.health_service import HealthService

logger = logging.getLogger(__name__)

health_router = APIRouter(tags=["健康检查"])

# Service实例
health_service = HealthService()

def get_current_timestamp() -> str:
    """获取当前UTC时间戳字符串"""
    return datetime.now(timezone.utc).isoformat()

def sanitize_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    脱敏配置信息，移除敏感字段
    
    Args:
        config: 原始配置字典
    
    Returns:
        dict: 脱敏后的配置字典
    """
    sensitive_keys = [
        "password", "secret", "key", "token", "api_key",
        "jwt_secret_key", "database_password"
    ]
    
    sanitized = {}
    for key, value in config.items():
        # 跳过包含敏感关键词的字段
        if any(sensitive in key.lower() for sensitive in sensitive_keys):
            continue
        
        # 如果是字典，递归处理
        if isinstance(value, dict):
            sanitized[key] = sanitize_config(value)
        else:
            sanitized[key] = value
    
    return sanitized

@health_router.get("/health")
async def health_check():
    """
    基础健康检查端点
    
    返回：
        - 200: 服务正常运行
    """
    try:
        # 直接返回硬编码的状态信息
        data = {
            "status": "healthy",
            "service": "live-core-service",
            "version": getattr(settings, "VERSION", "2.1.0"),
            "timestamp": get_current_timestamp()
        }
        
        logger.debug("基础健康检查请求")
        return success_response(data=data)
        
    except Exception as e:
        logger.error(f"基础健康检查失败: error={str(e)}")
        return JSONResponse(
            status_code=500,
            content=error_response(
                code=1002,
                message="服务内部错误",
                data={"reason": str(e)}
            )
        )

@health_router.get("/health/ready")
async def readiness_check(
    db: AsyncSession = Depends(get_db)
):
    """
    就绪检查端点（包含数据库连接测试）
    
    返回：
        - 200: 服务就绪（数据库连接正常）
        - 503: 服务未就绪（数据库连接失败）
    """
    try:
        # 调用Service层检查就绪状态
        readiness_status = await health_service.check_readiness(db)
        
        # 根据状态返回不同的HTTP状态码
        if readiness_status["status"] == "ready":
            data = {
                "status": readiness_status["status"],
                "service": "live-core-service",
                "database": readiness_status["database"],
                "timestamp": get_current_timestamp()
            }
            logger.info("就绪检查：服务就绪")
            return success_response(data=data)
        else:
            data = {
                "status": readiness_status["status"],
                "service": "live-core-service",
                "database": readiness_status["database"],
                "error": readiness_status["error"],
                "timestamp": get_current_timestamp()
            }
            logger.warning(f"就绪检查：服务未就绪 - {readiness_status['error']}")
            return JSONResponse(
                status_code=503,
                content=success_response(data=data)
            )
            
    except Exception as e:
        logger.error(f"就绪检查失败: error={str(e)}")
        data = {
            "status": "not_ready",
            "service": "live-core-service",
            "database": "unknown",
            "error": f"检查失败: {str(e)}",
            "timestamp": get_current_timestamp()
        }
        return JSONResponse(
            status_code=503,
            content=success_response(data=data)
        )

@health_router.get("/health/config")
async def config_check():
    """
    配置检查端点（返回非敏感配置信息）
    
    返回：
        - 200: 配置正常加载
    """
    try:
        # 从settings对象读取配置
        config_dict = {
            "environment": getattr(settings, "ENVIRONMENT", "unknown"),
            "debug": getattr(settings, "DEBUG", False),
            "database": {
                "server": getattr(settings, "DATABASE_HOST", "unknown"),
                "port": getattr(settings, "DATABASE_PORT", "unknown"),
                "database": getattr(settings, "DATABASE_NAME", "unknown")
            },
            "cors_origins": getattr(settings, "CORS_ORIGINS", []),
            "jwt_algorithm": getattr(settings, "JWT_ALGORITHM", "HS256")
        }
        
        # 脱敏处理
        sanitized_config = sanitize_config(config_dict)
        
        data = {
            "status": "configured",
            "service": "live-core-service",
            "config": sanitized_config,
            "timestamp": get_current_timestamp()
        }
        
        logger.debug("配置检查请求")
        return success_response(data=data)
        
    except Exception as e:
        logger.error(f"配置检查失败: error={str(e)}")
        return JSONResponse(
            status_code=500,
            content=error_response(
                code=1002,
                message="配置读取失败",
                data={"reason": str(e)}
            )
        )
