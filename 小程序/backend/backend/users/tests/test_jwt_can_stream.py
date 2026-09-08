"""V2 P0: JWT can_stream 签发单测"""

import uuid
from unittest.mock import MagicMock

import jwt
import pytest


def test_create_access_token_includes_can_stream():
    from app.services.auth_service import AuthService
    from app.core.config import settings

    service = AuthService(db=MagicMock(), redis_client=MagicMock())
    uid = str(uuid.uuid4())
    token = service._create_access_token(
        uid,
        "REGULAR",
        username="u1",
        nickname="n1",
        can_stream=True,
        avatar_url="/uploads/avatars/a.jpg",
    )
    payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    assert payload["can_stream"] is True
    assert payload["role"] == "REGULAR"
    assert payload["user_id"] == uid
    assert payload["avatar_url"] == "/uploads/avatars/a.jpg"


def test_create_access_token_default_can_stream_true():
    from app.services.auth_service import AuthService
    from app.core.config import settings

    service = AuthService(db=MagicMock(), redis_client=MagicMock())
    uid = str(uuid.uuid4())
    token = service._create_access_token(uid, "REGULAR")
    payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    assert payload["can_stream"] is True
    assert "avatar_url" not in payload


def test_create_access_token_can_stream_false_explicit():
    from app.services.auth_service import AuthService
    from app.core.config import settings

    service = AuthService(db=MagicMock(), redis_client=MagicMock())
    uid = str(uuid.uuid4())
    token = service._create_access_token(uid, "REGULAR", can_stream=False)
    payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    assert payload["can_stream"] is False
