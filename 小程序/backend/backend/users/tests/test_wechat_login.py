"""
微信小程序一键授权登录（V4）单元测试

覆盖 Mock Provider 与 wechat_login 主路径。
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.wechat_auth_provider import (
    MockWeChatAuthProvider,
    OfficialWeChatAuthProvider,
)
from app.services.auth_service import (
    AuthService,
    InvalidCredentialsException,
    InvalidTokenException,
)
from app.schemas.auth import WeChatLoginRequest
from app.models.users import EntityStatus


class TestMockWeChatAuthProvider:
    @pytest.mark.asyncio
    async def test_exchange_valid_mock_code(self):
        provider = MockWeChatAuthProvider()
        openid = await provider.exchange_code("mock:oxMOCK_OPENID_001")
        assert openid == "oxMOCK_OPENID_001"

    @pytest.mark.asyncio
    async def test_exchange_empty_openid_raises(self):
        provider = MockWeChatAuthProvider()
        with pytest.raises(ValueError):
            await provider.exchange_code("mock:")

    @pytest.mark.asyncio
    async def test_exchange_non_mock_prefix_raises(self):
        provider = MockWeChatAuthProvider()
        with pytest.raises(ValueError):
            await provider.exchange_code("081xYzRealCode")


class TestOfficialWeChatAuthProvider:
    @pytest.mark.asyncio
    async def test_exchange_success_returns_openid(self):
        provider = OfficialWeChatAuthProvider(appid="wxAPP", secret="secret")
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {"openid": "oxREAL001", "session_key": "sk"}

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_resp)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_cls.return_value = mock_client

            openid = await provider.exchange_code("real-js-code")
            assert openid == "oxREAL001"

    @pytest.mark.asyncio
    async def test_exchange_errcode_raises(self):
        provider = OfficialWeChatAuthProvider(appid="wxAPP", secret="secret")
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {"errcode": 40029, "errmsg": "invalid code"}

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_resp)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_cls.return_value = mock_client

            with pytest.raises(ValueError, match="微信登录失败"):
                await provider.exchange_code("bad-code")


class TestWeChatLoginService:
    def _make_service(self):
        db = AsyncMock()
        db.commit = AsyncMock()
        db.rollback = AsyncMock()
        with patch.object(AuthService, "_build_sms_provider"), \
             patch.object(AuthService, "_build_email_provider"), \
             patch.object(AuthService, "_build_carrier_auth_provider"), \
             patch.object(AuthService, "_build_wechat_auth_provider", return_value=MockWeChatAuthProvider()):
            service = AuthService(db)
        service.jwt_secret_key = "test-secret-key-at-least-32-chars!!"
        service.jwt_algorithm = "HS256"
        return service

    @pytest.mark.asyncio
    async def test_agreed_to_terms_required(self):
        service = self._make_service()
        req = WeChatLoginRequest(code="mock:ox1", agreed_to_terms=False)
        with pytest.raises(InvalidCredentialsException, match="服务条款"):
            await service.wechat_login(req)

    @pytest.mark.asyncio
    async def test_invalid_mock_code(self):
        service = self._make_service()
        req = WeChatLoginRequest(code="not-mock", agreed_to_terms=True)
        with pytest.raises(InvalidTokenException):
            await service.wechat_login(req)

    @pytest.mark.asyncio
    async def test_new_user_auto_register(self):
        service = self._make_service()
        req = WeChatLoginRequest(code="mock:oxNEWUSER001", agreed_to_terms=True)

        new_user = MagicMock()
        new_user.id = 101
        new_user.public_id = "550e8400-e29b-41d4-a716-446655440000"
        new_user.status = EntityStatus.NORMAL
        new_user.role = MagicMock(value="REGULAR")
        new_user.can_stream = True
        new_user.nickname = "微信用户0001"
        new_user.phone_number = None

        with patch("app.services.auth_service.crud_user") as mock_crud:
            mock_crud.get_by_social_id = AsyncMock(return_value=None)
            mock_crud.create = AsyncMock(return_value=new_user)

            result = await service.wechat_login(req)

        assert result["is_new_user"] is True
        assert result["user_public_id"] == str(new_user.public_id)
        assert result["access_token"]
        assert result["refresh_token"]
        assert result["phone_masked"] is None

    @pytest.mark.asyncio
    async def test_existing_user_login(self):
        service = self._make_service()
        req = WeChatLoginRequest(code="mock:oxEXISTING001", agreed_to_terms=True)

        existing = MagicMock()
        existing.id = 202
        existing.public_id = "660e8400-e29b-41d4-a716-446655440099"
        existing.status = EntityStatus.NORMAL
        existing.role = MagicMock(value="REGULAR")
        existing.can_stream = False
        existing.username = "u_olduser001"
        existing.nickname = "微信用户0001"
        existing.phone_number = None

        with patch("app.services.auth_service.crud_user") as mock_crud:
            mock_crud.get_by_social_id = AsyncMock(return_value=existing)

            result = await service.wechat_login(req)

        assert result["is_new_user"] is False
        assert result["user_public_id"] == str(existing.public_id)

    @pytest.mark.asyncio
    async def test_banned_user_rejected(self):
        service = self._make_service()
        req = WeChatLoginRequest(code="mock:oxBANNED001", agreed_to_terms=True)

        banned = MagicMock()
        banned.id = 303
        banned.public_id = "770e8400-e29b-41d4-a716-446655440088"
        banned.status = EntityStatus.BANNED
        banned.role = MagicMock(value="REGULAR")
        banned.can_stream = False
        banned.username = "u_banned001"
        banned.nickname = "微信用户0001"
        banned.phone_number = None

        with patch("app.services.auth_service.crud_user") as mock_crud:
            mock_crud.get_by_social_id = AsyncMock(return_value=banned)

            with pytest.raises(InvalidCredentialsException, match="封禁"):
                await service.wechat_login(req)
