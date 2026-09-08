"""
健康检查端点模块

提供应用健康状态、就绪状态和配置验证的API端点，用于监控和运维。
"""
import logging
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.database import get_db
from app.core.redis_client import get_redis_client

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", summary="基础健康检查", tags=["health"])
async def health_check() -> Dict[str, str]:
    """
    基础健康检查端点
    
    返回应用的基本运行状态，不进行深度检查。
    适用于负载均衡器的快速健康检查。
    
    Returns:
        包含状态信息的字典
    
    Example:
        >>> GET /api/v1/health
        {"status": "ok", "service": "user-service"}
    """
    return {
        "status": "ok",
        "service": "user-service",
        "environment": settings.ENVIRONMENT
    }


@router.get("/ready", summary="就绪检查", tags=["health"])
async def readiness_check(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """
    就绪检查端点
    
    检查应用的关键依赖服务（数据库、Redis）是否可用。
    适用于Kubernetes等容器编排系统的就绪探针。
    
    Args:
        db: 数据库会话（通过依赖注入）
    
    Returns:
        包含详细检查结果的字典
    
    Raises:
        HTTPException: 当任何依赖服务不可用时返回503
    
    Example:
        >>> GET /api/v1/health/ready
        {
            "status": "ready",
            "checks": {
                "database": "ok",
                "redis": "ok"
            }
        }
    """
    checks = {}
    all_healthy = True
    
    # 1. 数据库连接检查
    try:
        # 执行简单查询验证数据库连接
        result = await db.execute(text("SELECT 1"))
        await result.scalar()
        checks["database"] = "ok"
        logger.debug("数据库健康检查通过")
    except Exception as e:
        checks["database"] = f"error: {str(e)}"
        all_healthy = False
        logger.error(f"数据库健康检查失败: {e}")
    
    # 2. Redis连接检查
    try:
        redis_client = await get_redis_client()
        # 执行ping命令验证Redis连接
        await redis_client.ping()
        checks["redis"] = "ok"
        logger.debug("Redis健康检查通过")
    except Exception as e:
        checks["redis"] = f"error: {str(e)}"
        all_healthy = False
        logger.error(f"Redis健康检查失败: {e}")
    
    # 如果有任何检查失败，返回503状态码
    if not all_healthy:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "not_ready",
                "checks": checks
            }
        )
    
    return {
        "status": "ready",
        "checks": checks,
        "environment": settings.ENVIRONMENT
    }


@router.get("/config", summary="配置验证", tags=["health"])
async def config_check() -> Dict[str, Any]:
    """
    配置验证端点
    
    验证应用的关键配置项是否正确设置。
    **注意：生产环境禁止访问此端点以防信息泄露。**
    
    Returns:
        包含配置验证结果的字典（开发环境）
    
    Raises:
        HTTPException: 
            - 403: 生产环境禁止访问
            - 500: 配置验证失败
    
    Example:
        >>> GET /api/v1/health/config (开发环境)
        {
            "status": "ok",
            "environment": "development",
            "config_checks": {
                "database": "configured",
                "jwt": "configured",
                "authing": "configured",
                "cors": "configured"
            }
        }
    """
    # 生产环境禁止访问配置检查端点
    if settings.ENVIRONMENT == "production":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="配置检查端点在生产环境不可用"
        )
    
    config_checks = {}
    errors = []
    
    # 1. 数据库配置检查
    try:
        db_url = settings.DATABASE_URL
        if db_url and "postgresql" in db_url:
            config_checks["database"] = "configured"
        else:
            config_checks["database"] = "missing or invalid"
            errors.append("数据库配置无效")
    except Exception as e:
        config_checks["database"] = f"error: {str(e)}"
        errors.append(f"数据库配置检查失败: {e}")
    
    # 2. JWT配置检查
    try:
        if settings.JWT_SECRET_KEY:
            # 检查密钥长度（生产环境应>=32字符）
            key_length = len(settings.JWT_SECRET_KEY)
            if key_length >= 32:
                config_checks["jwt"] = "configured (secure)"
            else:
                config_checks["jwt"] = f"configured (weak: {key_length} chars)"
                if settings.ENVIRONMENT == "production":
                    errors.append(f"JWT密钥长度不足（当前{key_length}字符，建议>=32字符）")
        else:
            config_checks["jwt"] = "missing"
            errors.append("JWT密钥未配置")
    except Exception as e:
        config_checks["jwt"] = f"error: {str(e)}"
        errors.append(f"JWT配置检查失败: {e}")
    
    # 3. Authing SSO配置检查
    try:
        if settings.VITE_CLIENT_ID and settings.USER_POOL_SECRET:
            config_checks["authing"] = "configured"
        else:
            config_checks["authing"] = "partially configured or missing"
            # Authing是可选的，只记录warning而不是error
            logger.warning("Authing SSO配置不完整，SSO登录功能可能不可用")
    except Exception as e:
        config_checks["authing"] = f"error: {str(e)}"
        logger.warning(f"Authing配置检查失败: {e}")
    
    # 4. CORS配置检查
    try:
        cors_origins = settings.BACKEND_CORS_ORIGINS
        if cors_origins:
            if "*" in cors_origins:
                config_checks["cors"] = "wildcard (development only)"
                if settings.ENVIRONMENT == "production":
                    errors.append("生产环境不允许使用通配符CORS")
            else:
                config_checks["cors"] = f"configured ({len(cors_origins)} origins)"
        else:
            config_checks["cors"] = "missing"
            errors.append("CORS配置未设置")
    except Exception as e:
        config_checks["cors"] = f"error: {str(e)}"
        errors.append(f"CORS配置检查失败: {e}")
    
    # 如果有配置错误，返回500状态码
    if errors:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "configuration_error",
                "errors": errors,
                "config_checks": config_checks
            }
        )
    
    return {
        "status": "ok",
        "environment": settings.ENVIRONMENT,
        "config_checks": config_checks
    }

