"""已注销用户标记（16-D2 写入 / 16-D3 读路径覆盖展示）

优先 Redis Set：`deactivated_users`。Redis 不可用时降级（读失败不阻断）。
"""

from __future__ import annotations

import logging
from typing import Iterable, Set
from uuid import UUID

from app.core.redis_cache import get_redis

logger = logging.getLogger(__name__)

DEACTIVATED_USERS_KEY = "deactivated_users"
DEACTIVATED_DISPLAY_NAME = "账号已注销"


async def mark_user_deactivated(user_public_id: UUID) -> bool:
    """写入已注销标记。成功 True；Redis 不可用 False（调用方仍继续清理）。"""
    try:
        client = await get_redis()
        if client is None:
            logger.warning("无法写入已注销标记：Redis 不可用 user_id=%s", user_public_id)
            return False
        await client.sadd(DEACTIVATED_USERS_KEY, str(user_public_id))
        return True
    except Exception as e:
        logger.warning("写入已注销标记失败 user_id=%s error=%s", user_public_id, e)
        return False


async def filter_deactivated_user_ids(user_ids: Iterable[UUID]) -> Set[UUID]:
    """
    返回 user_ids 中已打注销标记的子集。
    Redis 失败时返回空集（D3 降级为快照展示）。
    """
    unique = list({uid for uid in user_ids if uid is not None})
    if not unique:
        return set()
    try:
        client = await get_redis()
        if client is None:
            logger.warning("查询已注销标记降级：Redis 不可用")
            return set()
        pipe = client.pipeline()
        for uid in unique:
            pipe.sismember(DEACTIVATED_USERS_KEY, str(uid))
        results = await pipe.execute()
        return {uid for uid, hit in zip(unique, results) if hit}
    except Exception as e:
        logger.warning("查询已注销标记失败，降级快照: %s", e)
        return set()
