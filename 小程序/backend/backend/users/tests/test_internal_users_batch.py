"""内部用户批量查询接口单元测试"""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.api.v1.internal.users import (
    InternalUserBatchRequest,
    _verify_internal_token,
    internal_batch_get_users,
)


def test_verify_internal_token_rejects_mismatch(monkeypatch):
    monkeypatch.setattr(
        "app.api.v1.internal.users.settings.INTERNAL_SERVICE_TOKEN",
        "expected-token",
        raising=False,
    )
    with pytest.raises(HTTPException) as exc:
        _verify_internal_token(x_internal_token="wrong")
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_internal_batch_get_users_success():
    uid = uuid.uuid4()
    user = MagicMock()
    user.public_id = uid
    user.username = "zhangsan"
    user.nickname = "张三"
    user.avatar_url = None

    db = AsyncMock()
    with patch(
        "app.api.v1.internal.users.crud_user.get_by_uuids",
        AsyncMock(return_value=[user]),
    ):
        resp = await internal_batch_get_users(
            InternalUserBatchRequest(public_ids=[uid]),
            db=db,
        )

    assert resp["code"] == 200
    assert resp["data"]["items"][0]["username"] == "zhangsan"
    assert resp["data"]["items"][0]["nickname"] == "张三"
    assert resp["data"]["items"][0]["public_id"] == str(uid)
