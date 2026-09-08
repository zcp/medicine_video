"""
依赖注入模块
提供FastAPI依赖注入函数
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Optional
from app.core.auth import JWTAuth, security
from app.core.session_revoke import ensure_session_not_revoked
from app.database import get_db
import time


async def get_current_user(token: Dict = Depends(JWTAuth.get_current_user)) -> Dict:
    """
    强制鉴权依赖注入（Strict Auth）

    Returns:
        用户信息字典 {"user_id": str(UUID), "role": str, "can_stream": bool, ...}

    Raises:
        HTTPException(401): Token缺失、无效或会话已吊销
    """
    await ensure_session_not_revoked(token)
    return token


async def verify_admin_role(current_user: Dict = Depends(get_current_user)) -> Dict:
    """
    管理员角色校验（ADMIN / SUPERADMIN）

    Raises:
        HTTPException(403): 非管理员
    """
    role = (current_user.get("role") or "").upper()
    if role not in ("ADMIN", "SUPERADMIN"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": 3003, "message": "权限不足：仅管理员可执行此操作"},
        )
    return current_user


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[Dict]:
    """
    可选鉴权依赖注入（Optional Auth）

    Returns:
        - None: 匿名用户（无Token）
        - Dict: 用户信息字典（有有效Token）

    Raises:
        HTTPException(401): Token无效或过期（但不能降级为匿名）
    """
    # 场景 A: 无 Token → 返回 None，视为匿名用户
    if not credentials or not credentials.credentials:
        return None

    # 场景 B: 有 Token → 必须验证（含会话吊销）
    try:
        user = JWTAuth.verify_token(credentials.credentials)
        await ensure_session_not_revoked(user)
        return user
    except HTTPException:
        # 场景 C: Token 过期/伪造/已吊销 → 必须报错！
        # 严禁降级为匿名，否则已登录用户看不到自己的私有资源
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


# 为了测试方便，提供一个独立的函数
async def get_current_user_for_test() -> Dict:
    """获取当前认证用户（测试用）"""
    return {
        "user_id": "test-user-id-12345",
        "sub": "test-user-id-12345",
        "email": "test@example.com",
        "exp": int(time.time()) + 3600
    }