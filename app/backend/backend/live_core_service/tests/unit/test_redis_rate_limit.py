"""留言限流（redis_cache.check_message_rate_limit）单元测试

覆盖：首次放行 / 窗口内拒绝 / Redis 不可用降级放行 / Redis 异常降级放行。
纯 mock 实现，不依赖 Redis 实例。
"""

from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.core.redis_cache import MESSAGE_RATE_LIMIT_SECONDS, check_message_rate_limit


class TestMessageRateLimit:
    @pytest.mark.asyncio
    async def test_first_message_allowed(self):
        """首次发送：原子 SET 成功（nx 抢占）→ 放行"""
        client = AsyncMock()
        client.set.return_value = True
        with patch("app.core.redis_cache.get_redis", new=AsyncMock(return_value=client)):
            assert await check_message_rate_limit(uuid4(), uuid4()) is True
        client.set.assert_awaited_once()
        _, kwargs = client.set.call_args
        assert kwargs.get("nx") is True, "必须使用原子 nx，防止并发穿透"
        assert kwargs.get("ex") == MESSAGE_RATE_LIMIT_SECONDS

    @pytest.mark.asyncio
    async def test_second_message_blocked_within_window(self):
        """窗口内再次发送：SET nx 返回 False → 拒绝"""
        client = AsyncMock()
        client.set.return_value = False
        with patch("app.core.redis_cache.get_redis", new=AsyncMock(return_value=client)):
            assert await check_message_rate_limit(uuid4(), uuid4()) is False

    @pytest.mark.asyncio
    async def test_degrade_allow_when_redis_unavailable(self):
        """Redis 不可用（连接失败）→ 降级放行，不影响业务"""
        with patch("app.core.redis_cache.get_redis", new=AsyncMock(return_value=None)):
            assert await check_message_rate_limit(uuid4(), uuid4()) is True

    @pytest.mark.asyncio
    async def test_degrade_allow_on_redis_error(self):
        """Redis 运行时异常 → 降级放行（限流失败不阻断留言）"""
        client = AsyncMock()
        client.set.side_effect = Exception("redis down")
        with patch("app.core.redis_cache.get_redis", new=AsyncMock(return_value=client)):
            assert await check_message_rate_limit(uuid4(), uuid4()) is True
