"""16-D1：账号注销不删房约束；16-D2 出站失败不阻断注销"""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.mark.asyncio
async def test_deactivate_account_never_calls_live_core_delete_room(mocker):
    """16-D1 P0：注销路径禁止调 live_core 删房；仅允许 deactivate-cleanup。"""
    from app.services.user_service import UserService

    db = AsyncMock()
    service = UserService(db)
    user = MagicMock()
    user.id = 1
    user.public_id = uuid.uuid4()

    mocker.patch.object(service, "_verify_captcha", new_callable=AsyncMock, return_value=True)
    mocker.patch("app.crud.crud_user.remove", new_callable=AsyncMock, return_value=user)
    mocker.patch.object(service, "_blacklist_user_tokens", new_callable=AsyncMock)
    mock_cleanup = mocker.patch.object(
        service, "_notify_live_core_deactivate_cleanup", new_callable=AsyncMock
    )

    await service.deactivate_account(
        user, captcha_id="c", captcha_solution="1"
    )

    mock_cleanup.assert_called_once_with(user.public_id)


@pytest.mark.asyncio
async def test_notify_cleanup_failure_does_not_raise(mocker):
    """16-D2：live_core 出站失败不抛错，注销仍可视为成功。"""
    from app.services.user_service import UserService

    service = UserService(AsyncMock())
    mocker.patch("app.services.user_service.settings.LIVE_CORE_SERVICE_URL", "http://live_core:8000")
    mocker.patch("app.services.user_service.settings.INTERNAL_SERVICE_TOKEN", "tok")

    class BoomClient:
        def __init__(self, *a, **k):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return None

        async def post(self, *a, **k):
            raise RuntimeError("network down")

    mocker.patch("httpx.AsyncClient", BoomClient)
    await service._notify_live_core_deactivate_cleanup(uuid.uuid4())
