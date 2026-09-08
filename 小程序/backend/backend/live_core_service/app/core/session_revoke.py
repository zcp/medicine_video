"""会话吊销校验（与 user_service 共用 Redis Key: user_sessions_revoked:{user_id}）"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import HTTPException

from app.core.redis_cache import get_redis

logger = logging.getLogger(__name__)


async def is_user_sessions_revoked(
    user_public_id: str, token_iat: Optional[datetime] = None
) -> bool:
    """iat 早于吊销时间则视为已吊销。Redis 不可用时不误杀（降级）。"""
    try:
        client = await get_redis()
        if not client:
            return False
        revocation_time_str = await client.get(f"user_sessions_revoked:{user_public_id}")
        if not revocation_time_str:
            return False
        if token_iat is None:
            return True
        revocation_time = datetime.fromisoformat(revocation_time_str)
        return token_iat < revocation_time
    except Exception as e:
        logger.error("检查用户会话吊销失败: user_id=%s, error=%s", user_public_id, e)
        return False


async def ensure_session_not_revoked(payload: Dict[str, Any]) -> None:
    """强制鉴权路径：已吊销会话返回 401。"""
    user_id = payload.get("user_id")
    if not user_id:
        return
    iat_timestamp = payload.get("iat")
    token_iat = (
        datetime.utcfromtimestamp(iat_timestamp) if iat_timestamp else None
    )
    if await is_user_sessions_revoked(str(user_id), token_iat=token_iat):
        logger.warning("用户会话已吊销: user_id=%s", user_id)
        raise HTTPException(status_code=401, detail="认证凭证已失效")
