"""Redis 缓存与限流工具（留言模块）"""

import json
import logging
from typing import Any, Optional, Tuple, List
from uuid import UUID

import redis.asyncio as aioredis

from app.core.config import settings
from app.exceptions import InvalidParameterException

logger = logging.getLogger(__name__)

_redis_client: Optional[aioredis.Redis] = None

MESSAGE_CACHE_TTL = 60
MESSAGE_RATE_LIMIT_SECONDS = 5


def _get_redis_url() -> str:
    return getattr(settings, "REDIS_URL", None) or settings.CELERY_BROKER_URL


async def get_redis() -> Optional[aioredis.Redis]:
    """获取 Redis 客户端，不可用时返回 None（测试/降级）"""
    global _redis_client
    if _redis_client is not None:
        return _redis_client
    try:
        _redis_client = aioredis.from_url(
            _get_redis_url(),
            encoding="utf-8",
            decode_responses=True,
        )
        await _redis_client.ping()
        return _redis_client
    except Exception as e:
        logger.warning("Redis 不可用，留言缓存/限流将降级: %s", e)
        _redis_client = None
        return None


def _cache_key(room_id: UUID, page: int, size: int) -> str:
    return f"room:{room_id}:messages:recent:p{page}:s{size}"


def _rate_limit_key(user_id: UUID, room_id: UUID) -> str:
    return f"message:rate:{user_id}:{room_id}"


async def get_cached_messages(
    room_id: UUID, page: int, size: int
) -> Optional[Tuple[List[dict], int]]:
    """读取留言列表缓存（API 响应 items 格式）"""
    if page != 1:
        return None
    client = await get_redis()
    if not client:
        return None
    try:
        raw = await client.get(_cache_key(room_id, page, size))
        if not raw:
            return None
        data = json.loads(raw)
        return data["items"], data["total"]
    except Exception as e:
        logger.warning("读取留言缓存失败: %s", e)
        return None


async def set_cached_messages(
    room_id: UUID, page: int, size: int, items: List[dict], total: int
) -> None:
    if page != 1:
        return
    client = await get_redis()
    if not client:
        return
    try:
        payload = json.dumps({"items": items, "total": total}, default=str)
        await client.setex(_cache_key(room_id, page, size), MESSAGE_CACHE_TTL, payload)
    except Exception as e:
        logger.warning("写入留言缓存失败: %s", e)


async def invalidate_message_cache(room_id: UUID) -> None:
    client = await get_redis()
    if not client:
        return
    try:
        pattern = f"room:{room_id}:messages:recent:*"
        async for key in client.scan_iter(match=pattern):
            await client.delete(key)
    except Exception as e:
        logger.warning("清除留言缓存失败: %s", e)


async def invalidate_all_message_caches() -> None:
    """注销等全局事件：清全部留言列表缓存，避免 D3 占位被 60s 缓存拖住。"""
    client = await get_redis()
    if not client:
        return
    try:
        async for key in client.scan_iter(match="room:*:messages:recent:*"):
            await client.delete(key)
    except Exception as e:
        logger.warning("清除全部留言缓存失败: %s", e)


async def check_message_rate_limit(user_id: UUID, room_id: UUID) -> None:
    """每 5 秒最多 1 条留言，超限抛出 InvalidParameterException"""
    client = await get_redis()
    if not client:
        return
    key = _rate_limit_key(user_id, room_id)
    try:
        acquired = await client.set(key, "1", nx=True, ex=MESSAGE_RATE_LIMIT_SECONDS)
        if not acquired:
            raise InvalidParameterException(
                "发送过于频繁，请稍后再试", code=2004
            )
    except InvalidParameterException:
        raise
    except Exception as e:
        logger.warning("留言限流检查失败，降级放行: %s", e)
