"""JWT 时钟偏差 leeway：iat 略超前应可通过，超太多仍拒绝。"""

import uuid
from datetime import datetime, timedelta
from unittest.mock import MagicMock

import jwt
import pytest

from app.core.config import settings
from app.api.v1 import deps
from app.services.auth_service import AuthService


def _make_access_token(*, iat_offset_seconds: int) -> str:
    """签发 access token，iat/exp 相对「现在」偏移，用于模拟时钟漂移。"""
    now = datetime.utcnow() + timedelta(seconds=iat_offset_seconds)
    payload = {
        "user_id": str(uuid.uuid4()),
        "type": "access",
        "iat": now,
        "exp": now + timedelta(hours=1),
        "jti": str(uuid.uuid4()),
        "role": "REGULAR",
        "can_stream": False,
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


@pytest.fixture(autouse=True)
def _ensure_leeway():
    """单测假定默认 60s 容差；避免环境变量干扰。"""
    original = settings.JWT_LEEWAY_SECONDS
    settings.JWT_LEEWAY_SECONDS = 60
    yield
    settings.JWT_LEEWAY_SECONDS = original


@pytest.mark.asyncio
async def test_deps_verify_token_allows_iat_within_leeway():
    """容器时钟回拨约 30s 时，iat 仍应通过 deps.verify_token。"""
    token = _make_access_token(iat_offset_seconds=30)
    payload = await deps.verify_token(token)
    assert payload is not None
    assert payload["type"] == "access"


@pytest.mark.asyncio
async def test_deps_verify_token_rejects_iat_beyond_leeway():
    """iat 超前超过 leeway 时仍应失败。"""
    token = _make_access_token(iat_offset_seconds=120)
    payload = await deps.verify_token(token)
    assert payload is None


def test_auth_service_verify_token_allows_iat_within_leeway():
    service = AuthService(db=MagicMock(), redis_client=MagicMock())
    token = _make_access_token(iat_offset_seconds=30)
    payload = service._verify_token(token, token_type="access")
    assert payload is not None
    assert payload["type"] == "access"


def test_auth_service_verify_token_rejects_iat_beyond_leeway():
    service = AuthService(db=MagicMock(), redis_client=MagicMock())
    token = _make_access_token(iat_offset_seconds=120)
    payload = service._verify_token(token, token_type="access")
    assert payload is None


def test_auth_service_verify_refresh_token_allows_iat_within_leeway():
    """refresh 路径同样带 leeway，避免时钟异常时无法救回会话。"""
    service = AuthService(db=MagicMock(), redis_client=MagicMock())
    now = datetime.utcnow() + timedelta(seconds=30)
    payload = {
        "user_id": str(uuid.uuid4()),
        "type": "refresh",
        "iat": now,
        "exp": now + timedelta(days=7),
        "jti": str(uuid.uuid4()),
    }
    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    result = service._verify_token(token, token_type="refresh")
    assert result is not None
    assert result["type"] == "refresh"
