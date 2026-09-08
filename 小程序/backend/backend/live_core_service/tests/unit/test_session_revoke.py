"""V2 P0: live_core 会话吊销校验单元测试（不依赖 DB conftest）"""

import calendar
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException


@pytest.mark.asyncio
async def test_ensure_session_not_revoked_rejects_old_token(mocker):
    from app.core.session_revoke import ensure_session_not_revoked

    # 使用固定 UTC 时间，避免 Windows 上 utcnow().timestamp() 时区坑
    revoked_at = datetime(2026, 7, 14, 12, 0, 0)
    old_iat = calendar.timegm((revoked_at - timedelta(hours=1)).timetuple())
    mock_redis = MagicMock()
    mock_redis.get = AsyncMock(return_value=revoked_at.isoformat())
    mocker.patch(
        "app.core.session_revoke.get_redis",
        new_callable=AsyncMock,
        return_value=mock_redis,
    )

    payload = {
        "user_id": "550e8400-e29b-41d4-a716-446655440000",
        "iat": old_iat,
    }
    with pytest.raises(HTTPException) as exc:
        await ensure_session_not_revoked(payload)
    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_ensure_session_not_revoked_allows_new_token(mocker):
    from app.core.session_revoke import ensure_session_not_revoked

    revoked_at = datetime(2026, 7, 14, 12, 0, 0)
    new_iat = calendar.timegm((revoked_at + timedelta(minutes=1)).timetuple())
    mock_redis = MagicMock()
    mock_redis.get = AsyncMock(return_value=revoked_at.isoformat())
    mocker.patch(
        "app.core.session_revoke.get_redis",
        new_callable=AsyncMock,
        return_value=mock_redis,
    )

    payload = {
        "user_id": "550e8400-e29b-41d4-a716-446655440000",
        "iat": new_iat,
    }
    await ensure_session_not_revoked(payload)


@pytest.mark.asyncio
async def test_ensure_session_not_revoked_noop_without_key(mocker):
    from app.core.session_revoke import ensure_session_not_revoked

    mock_redis = MagicMock()
    mock_redis.get = AsyncMock(return_value=None)
    mocker.patch(
        "app.core.session_revoke.get_redis",
        new_callable=AsyncMock,
        return_value=mock_redis,
    )

    await ensure_session_not_revoked(
        {"user_id": "550e8400-e29b-41d4-a716-446655440000", "iat": 1}
    )
