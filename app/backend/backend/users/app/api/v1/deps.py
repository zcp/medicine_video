"""
用户功能服务 - 依赖注入层
提供可复用的依赖项，特别是用于用户认证的依赖
"""
import logging
import uuid

import jwt
from datetime import datetime
from typing import Optional
from jwt import ExpiredSignatureError, PyJWTError

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_db
from app.core.redis_client import get_redis_client
from app.core.config import settings  # ✅ 导入配置
from app.crud import crud_user
from app.models.users import User, EntityStatus

logger = logging.getLogger(__name__)

# OAuth2方案定义
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# JWT配置 - 从配置模块读取
JWT_SECRET_KEY = settings.JWT_SECRET_KEY
JWT_ALGORITHM = settings.JWT_ALGORITHM


async def verify_token(token: str) -> Optional[dict]:
    """验证JWT令牌"""
    try:
        payload = jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
            leeway=settings.JWT_LEEWAY_SECONDS,
        )
        if payload.get("type") != "access":
            return None
        return payload
    except ExpiredSignatureError:
        logger.warning("JWT令牌已过期")
        return None
    except PyJWTError as e:
        logger.warning(f"JWT令牌验证失败: {e}")
        return None

async def is_token_blacklisted(token: str) -> bool:
    """检查令牌是否在黑名单中"""
    try:
        redis_client = get_redis_client()
        blacklisted = await redis_client.get(f"blacklist:token:{token}")
        return blacklisted is not None
    except Exception as e:
        logger.error(f"检查令牌黑名单失败: {e}")
        return False


async def is_user_sessions_revoked(user_public_id: str, token_iat: Optional[datetime] = None) -> bool:
    """检查用户会话是否已被吊销（封禁/禁播/降权后 access token 即时失效）"""
    try:
        redis_client = get_redis_client()
        revocation_time_str = await redis_client.get(f"user_sessions_revoked:{user_public_id}")
        if not revocation_time_str:
            return False
        if token_iat is None:
            return True
        revocation_time = datetime.fromisoformat(revocation_time_str)
        return token_iat < revocation_time
    except Exception as e:
        logger.error(f"检查用户会话吊销失败: user_id={user_public_id}, error={e}")
        # Redis 故障时放行，由下方 DB status 检查兜底
        return False


async def get_current_user(
    token: str = Depends(oauth2_scheme), 
    db: AsyncSession = Depends(get_async_db)
) -> User:
    """
    获取当前已认证的用户依赖项
    
    Args:
        token: 从Authorization头中提取的JWT令牌
        db: 数据库会话
        
    Returns:
        当前用户对象
        
    Raises:
        HTTPException: 认证失败时抛出异常
    """
    logger.info("开始验证用户认证令牌")
    
    # 验证令牌格式和有效性
    payload = await verify_token(token)
    if not payload:
        logger.warning("令牌验证失败")
        raise HTTPException(
            status_code=401,
            detail="认证凭证无效",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # 检查令牌是否在黑名单中
    if await is_token_blacklisted(token):
        logger.warning("令牌已在黑名单中")
        raise HTTPException(
            status_code=401,
            detail="认证凭证已失效",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # 从令牌载荷中获取用户ID
    user_id = payload.get("user_id")
    if not user_id:
        logger.warning("令牌载荷中缺少用户ID")
        raise HTTPException(
            status_code=401,
            detail="认证凭证格式错误",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # 会话吊销检查：iat 早于吊销时间的 token 一律拒绝（封禁/禁播/降权即时生效）
    iat_timestamp = payload.get("iat")
    token_iat = datetime.utcfromtimestamp(iat_timestamp) if iat_timestamp else None
    if await is_user_sessions_revoked(str(user_id), token_iat=token_iat):
        logger.warning(f"用户会话已吊销: user_id={user_id}")
        raise HTTPException(
            status_code=401,
            detail="认证凭证已失效",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # 从数据库获取用户
    #user = await crud_user.get(db, user_id)
    user = await crud_user.get_by_uuid(db, public_id=uuid.UUID(user_id))
    if not user:
        logger.warning(f"用户不存在: user_id={user_id}")
        raise HTTPException(
            status_code=401,
            detail="用户不存在",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # 检查用户状态
    if user.status != EntityStatus.NORMAL:
        logger.warning(f"用户状态异常: user_id={user_id}, status={user.status}")
        raise HTTPException(
            status_code=401,
            detail="账户状态异常",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    logger.info(f"用户认证成功: user_id={user.id}, username={user.username}")
    return user 


# ============================================================================
# 批次五新增函数 - 后台管理权限验证
# ============================================================================

async def get_current_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """
    获取当前管理员用户依赖项
    
    确保当前用户是管理员（ADMIN或SUPERADMIN角色）
    
    Args:
        current_user: 当前已认证的用户（来自get_current_user依赖）
        
    Returns:
        管理员用户对象
        
    Raises:
        HTTPException: 权限不足时抛出403异常
    """
    logger.info(f"开始验证管理员权限: user_id={current_user.id}, role={current_user.role}")
    
    # 检查用户角色是否为管理员
    from app.models.users import UserRole
    
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPERADMIN]:
        logger.warning(f"用户权限不足: user_id={current_user.id}, role={current_user.role}")
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions"
        )
    
    logger.info(f"管理员权限验证成功: user_id={current_user.id}, role={current_user.role}")
    return current_user 