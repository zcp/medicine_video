"""
用户服务 - AuthService 单元测试

测试 app/services/auth_service.py 中的 AuthService 类的所有业务逻辑，
使用 mocker fixture 模拟所有外部依赖。
"""

import pytest
import uuid
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
import redis.exceptions

from app.services.auth_service import (
    AuthService,
    CaptchaErrorException,
    RateLimitException,
    UserAlreadyExistsException,
    InvalidCredentialsException,
    InvalidTokenException,
    InvalidResetTokenException,
    WeakPasswordException
)
from app import schemas
from app.models.users import EntityStatus


class TestAuthService:
    """AuthService 测试类"""

    @pytest.fixture
    def mock_db_session(self):
        """Mock 数据库会话"""
        mock_db = AsyncMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        return mock_db

    @pytest.fixture  
    def mock_redis_client(self):
        """Mock Redis 客户端"""
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock()
        mock_redis.set = AsyncMock()
        mock_redis.delete = AsyncMock()
        mock_redis.incr = AsyncMock()
        mock_redis.expire = AsyncMock()
        return mock_redis

    @pytest.fixture
    def auth_service(self, mock_db_session, mock_redis_client):
        """创建 AuthService 实例"""
        return AuthService(db=mock_db_session, redis_client=mock_redis_client)

    @pytest.fixture
    def mock_user(self):
        """Mock 用户对象"""
        user = MagicMock()
        user.id = 1
        user.username = "testuser"
        user.email = "test@example.com"
        user.status = EntityStatus.NORMAL
        user.password_hash = "hashed_password"
        user.last_login_at = None
        user.last_login_ip = None
        return user

    @pytest.fixture
    def mock_login_request(self):
        """Mock 登录请求"""
        return schemas.LoginRequest(
            username="testuser",
            password="password123",
            captcha_id="test-captcha-id",
            captcha_solution="12345",
            agreed_to_terms=True,
        )

    @pytest.fixture
    def mock_otp_request(self):
        """Mock OTP 请求"""
        return schemas.VerificationCodeRequest(
            channel="EMAIL",
            recipient="test@example.com",
            scenario="REGISTER",
            captcha_id="test-captcha-id",
            captcha_solution="12345"
        )

    @pytest.fixture
    def mock_password_reset_request(self):
        """Mock 密码重置请求"""
        return schemas.PasswordResetRequest(
            email="test@example.com",
            captcha_id="test-captcha-id",
            captcha_solution="12345"
        )

    @pytest.fixture
    def mock_password_reset_confirm_request(self):
        """Mock 密码重置确认请求"""
        return schemas.PasswordResetConfirmRequest(
            reset_token="test_reset_token",
            new_password="new_strong_password"
        )

    # ========================================================================
    # 登录相关测试
    # ========================================================================

    @pytest.mark.asyncio
    async def test_login_user_success(self, auth_service, mock_login_request, mock_user, mocker):
        """测试用户登录成功"""
        # Arrange
        mock_verify_captcha = mocker.patch.object(auth_service, '_verify_captcha', return_value=True)
        mock_crud_get_by_login_identifier = mocker.patch('app.crud.crud_user.get_by_login_identifier', return_value=mock_user)
        mock_verify_password = mocker.patch.object(auth_service, '_verify_password', return_value=True)
        mock_create_access_token = mocker.patch.object(auth_service, '_create_access_token', return_value='access_token_123')
        mock_create_refresh_token = mocker.patch.object(auth_service, '_create_refresh_token', return_value='refresh_token_123')

        # Act
        result = await auth_service.login_user(mock_login_request, "192.168.1.1")

        # Assert
        assert result == {
            "access_token": "access_token_123",
            "refresh_token": "refresh_token_123",
            "token_type": "bearer"
        }
        mock_verify_captcha.assert_called_once_with(mock_login_request.captcha_id, mock_login_request.captcha_solution)
        mock_crud_get_by_login_identifier.assert_called_once_with(auth_service.db,
                                                                  identifier=mock_login_request.username)
        mock_verify_password.assert_called_once_with(mock_login_request.password, mock_user.password_hash)
        mock_create_access_token.assert_called_once_with(str(mock_user.public_id), mock_user.role.value, username=mock_user.username, nickname=mock_user.nickname)
        mock_create_refresh_token.assert_called_once_with(str(mock_user.public_id))
        auth_service.db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_login_user_fails_if_user_not_found(self, auth_service, mock_login_request, mocker):
        """测试用户不存在时登录失败"""
        # Arrange
        mocker.patch.object(auth_service, '_verify_captcha', return_value=True)
        mocker.patch('app.crud.crud_user.get_by_login_identifier', return_value=None)

        # Act & Assert
        with pytest.raises(InvalidCredentialsException) as exc_info:
            await auth_service.login_user(mock_login_request)
        
        assert "用户名或密码错误" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_login_user_fails_if_password_is_wrong(self, auth_service, mock_login_request, mock_user, mocker):
        """测试密码错误时登录失败"""
        # Arrange
        mocker.patch.object(auth_service, '_verify_captcha', return_value=True)
        mocker.patch('app.crud.crud_user.get_by_login_identifier', return_value=mock_user)
        mocker.patch.object(auth_service, '_verify_password', return_value=False)

        # Act & Assert
        with pytest.raises(InvalidCredentialsException) as exc_info:
            await auth_service.login_user(mock_login_request)
        
        assert "用户名或密码错误" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_login_user_fails_if_user_is_banned(self, auth_service, mock_login_request, mock_user, mocker):
        """测试用户被封禁时登录失败"""
        # Arrange
        mock_user.status = EntityStatus.BANNED
        mocker.patch.object(auth_service, '_verify_captcha', return_value=True)
        mocker.patch('app.crud.crud_user.get_by_login_identifier', return_value=mock_user)
        mocker.patch.object(auth_service, '_verify_password', return_value=True)

        # Act & Assert
        with pytest.raises(InvalidCredentialsException) as exc_info:
            await auth_service.login_user(mock_login_request)
        
        assert "账户状态异常" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_login_user_fails_if_captcha_is_wrong(self, auth_service, mock_login_request, mocker):
        """测试验证码错误时登录失败"""
        # Arrange
        mocker.patch.object(auth_service, '_verify_captcha', return_value=False)

        # Act & Assert
        with pytest.raises(CaptchaErrorException) as exc_info:
            await auth_service.login_user(mock_login_request)
        
        assert "图形验证码错误或已过期" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_login_user_fails_if_terms_not_agreed(self, auth_service, mocker):
        """未同意服务条款时密码登录应被拒绝"""
        login_request = schemas.LoginRequest(
            username="testuser",
            password="password123",
            captcha_id="test-captcha-id",
            captcha_solution="12345",
            agreed_to_terms=False,
        )
        with pytest.raises(InvalidCredentialsException) as exc_info:
            await auth_service.login_user(login_request)
        assert "请先同意服务条款和隐私政策" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_login_by_phone_fails_if_terms_not_agreed(self, auth_service):
        """未同意服务条款时手机验证码登录应被拒绝"""
        login_request = schemas.PhoneLoginRequest(
            login_ticket="dummy-ticket",
            agreed_to_terms=False,
        )
        with pytest.raises(InvalidCredentialsException) as exc_info:
            await auth_service.login_by_phone_ticket(login_request)
        assert "请先同意服务条款和隐私政策" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_one_tap_login_direct_fails_if_terms_not_agreed(self, auth_service):
        """未同意服务条款时云函数一键登录应被拒绝"""
        with pytest.raises(InvalidCredentialsException) as exc_info:
            await auth_service.one_tap_login_direct(
                phone="+8613800138000",
                sign="x",
                timestamp="1",
                agreed_to_terms=False,
            )
        assert "请先同意服务条款和隐私政策" in str(exc_info.value)

    # ========================================================================
    # OTP 验证码相关测试
    # ========================================================================

    @pytest.mark.asyncio
    async def test_send_otp_code_success_for_register(self, auth_service, mock_otp_request, mocker):
        """测试注册场景下发送 OTP 验证码成功"""
        # Arrange
        mocker.patch.object(auth_service, '_verify_captcha', return_value=True)
        mocker.patch('app.crud.crud_user.get_by_email', return_value=None)
        mock_generate_otp = mocker.patch.object(auth_service, '_generate_otp', return_value='123456')
        mock_mask_recipient = mocker.patch.object(auth_service, '_mask_recipient', return_value='te**@example.com')

        # Act
        result = await auth_service.send_otp_code(mock_otp_request, "192.168.1.1")

        # Assert
        assert result["message"] == "验证码已发送，请注意查收。"
        assert result["recipient_masked"] == "te**@example.com"
        assert result["cooldown_seconds"] == 60
        
        auth_service.redis_client.set.assert_called_once()
        call_args = auth_service.redis_client.set.call_args
        assert call_args[0][0] == f"otp:{mock_otp_request.scenario}:{mock_otp_request.recipient}"
        assert call_args[0][1] == "123456"
        assert call_args[1]["ex"] == 300

    @pytest.mark.asyncio
    async def test_send_otp_code_fails_if_email_exists_for_register(self, auth_service, mock_otp_request, mock_user, mocker):
        """测试注册场景下邮箱已存在时发送失败"""
        # Arrange
        mocker.patch.object(auth_service, '_verify_captcha', return_value=True)
        mocker.patch('app.crud.crud_user.get_by_email', return_value=mock_user)

        # Act & Assert
        with pytest.raises(UserAlreadyExistsException) as exc_info:
            await auth_service.send_otp_code(mock_otp_request, "192.168.1.1")
        
        assert "该邮箱已被注册" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_send_otp_code_fails_if_captcha_is_wrong(self, auth_service, mock_otp_request, mocker):
        """测试验证码错误时发送失败"""
        # Arrange
        mocker.patch.object(auth_service, '_verify_captcha', return_value=False)

        # Act & Assert
        with pytest.raises(CaptchaErrorException) as exc_info:
            await auth_service.send_otp_code(mock_otp_request)
        
        assert "图形验证码错误或已过期" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_send_otp_code_fails_if_rate_limit_exceeded(self, auth_service, mock_otp_request, mocker):
        """测试频率限制超限时发送失败"""
        # Arrange
        mocker.patch.object(auth_service, '_verify_captcha', return_value=True)
        auth_service.redis_client.get.return_value = "5"  # 已达到限制

        # Act & Assert
        with pytest.raises(RateLimitException) as exc_info:
            await auth_service.send_otp_code(mock_otp_request, "192.168.1.1")
        
        assert "请求过于频繁" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_send_otp_code_reset_password_returns_success_even_if_user_not_exists(self, auth_service, mocker):
        """测试重置密码场景下，即使用户不存在也返回成功（安全考虑）"""
        # Arrange
        reset_otp_request = schemas.VerificationCodeRequest(
            channel="EMAIL",  # 新增必需字段
            recipient="nonexistent@example.com",
            scenario="RESET_PASSWORD",
            captcha_id="test-captcha-id",
            captcha_solution="12345"
        )
        mocker.patch.object(auth_service, '_verify_captcha', return_value=True)
        mocker.patch('app.crud.crud_user.get_by_email', return_value=None)
        mock_mask_recipient = mocker.patch.object(auth_service, '_mask_recipient', return_value='non**@example.com')

        # Act
        result = await auth_service.send_otp_code(reset_otp_request)

        # Assert
        assert result["message"] == "验证码已发送，请注意查收。"
        assert result["recipient_masked"] == "non**@example.com"
        # 确保没有实际发送验证码（Redis set 不应被调用）
        auth_service.redis_client.set.assert_not_called()

    # ========================================================================
    # Token 刷新相关测试
    # ========================================================================

    @pytest.mark.asyncio
    async def test_refresh_access_token_success(self, auth_service, mocker):
        """测试刷新访问令牌成功"""
        # Arrange
        import uuid
        test_user_uuid = str(uuid.uuid4())
        mock_payload = {"user_id": test_user_uuid, "type": "refresh", "exp": 1234567890}
        mock_verify_token = mocker.patch.object(auth_service, '_verify_token', return_value=mock_payload)
        mock_is_blacklisted = mocker.patch.object(auth_service, '_is_token_blacklisted', return_value=False)
        mock_create_access_token = mocker.patch.object(auth_service, '_create_access_token', return_value='new_access_token')
        mock_crud_get_by_uuid = mocker.patch('app.crud.crud_user.get_by_uuid', return_value=MagicMock(role=MagicMock(value="REGULAR")))

        # Act
        result = await auth_service.refresh_access_token('refresh_token_123')

        # Assert
        assert result == {
            "access_token": "new_access_token",
            "token_type": "bearer"
        }
        mock_verify_token.assert_called_once_with('refresh_token_123', token_type="refresh")
        mock_is_blacklisted.assert_called_once_with('refresh_token_123')
        mock_create_access_token.assert_called_once_with(test_user_uuid, "REGULAR")

    @pytest.mark.asyncio
    async def test_refresh_access_token_fails_if_token_is_blacklisted(self, auth_service, mocker):
        """测试刷新令牌在黑名单中时刷新失败"""
        # Arrange
        mock_payload = {"user_id": 1, "type": "refresh"}
        mocker.patch.object(auth_service, '_verify_token', return_value=mock_payload)
        mocker.patch.object(auth_service, '_is_token_blacklisted', return_value=True)

        # Act & Assert
        with pytest.raises(InvalidTokenException) as exc_info:
            await auth_service.refresh_access_token('refresh_token_123')
        
        assert "凭证无效或已过期" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_refresh_access_token_fails_if_token_is_invalid(self, auth_service, mocker):
        """测试无效令牌时刷新失败"""
        # Arrange
        mocker.patch.object(auth_service, '_verify_token', return_value=None)

        # Act & Assert
        with pytest.raises(InvalidTokenException) as exc_info:
            await auth_service.refresh_access_token('invalid_token')
        
        assert "凭证无效或已过期" in str(exc_info.value)

    # ========================================================================
    # 登出相关测试
    # ========================================================================

    @pytest.mark.asyncio
    async def test_logout_user_success(self, auth_service, mocker):
        """测试用户登出成功"""
        # Arrange
        exp_time = int((datetime.utcnow() + timedelta(hours=1)).timestamp())
        mock_payload = {"user_id": 1, "type": "access", "exp": exp_time}
        mock_verify_token = mocker.patch.object(auth_service, '_verify_token', return_value=mock_payload)
        mock_blacklist_token = mocker.patch.object(auth_service, '_blacklist_token', return_value=True)

        # Act
        await auth_service.logout_user('access_token_123')

        # Assert
        mock_verify_token.assert_called_once_with('access_token_123', token_type="access")
        mock_blacklist_token.assert_called_once_with('access_token_123', expire_time=3600)

    @pytest.mark.asyncio
    async def test_logout_user_fails_if_token_is_invalid(self, auth_service, mocker):
        """测试无效令牌时登出失败"""
        # Arrange
        mocker.patch.object(auth_service, '_verify_token', return_value=None)

        # Act & Assert
        with pytest.raises(InvalidTokenException) as exc_info:
            await auth_service.logout_user('invalid_token')
        
        assert "认证凭证格式无效" in str(exc_info.value)

    # ========================================================================
    # 密码重置相关测试
    # ========================================================================

    @pytest.mark.asyncio
    async def test_request_password_reset_success(self, auth_service, mock_password_reset_request, mock_user, mocker):
        """测试请求密码重置成功"""
        # Arrange
        mocker.patch.object(auth_service, '_verify_captcha', return_value=True)
        mock_crud_get_by_email = mocker.patch('app.crud.crud_user.get_by_email', return_value=mock_user)
        mock_token_urlsafe = mocker.patch('secrets.token_urlsafe', return_value='test_reset_token')
        mock_send_reset = mocker.patch.object(
            auth_service.email_provider,
            'send_password_reset',
            new_callable=AsyncMock,
            return_value=True,
        )

        # Act
        await auth_service.request_password_reset(mock_password_reset_request)

        # Assert
        mock_crud_get_by_email.assert_called_once_with(auth_service.db, mock_password_reset_request.email)
        auth_service.redis_client.set.assert_called_once()
        call_args = auth_service.redis_client.set.call_args
        assert call_args[0][0] == "password_reset:test_reset_token"
        assert call_args[0][1] == str(mock_user.id)
        assert call_args[1]["ex"] == 900
        mock_send_reset.assert_awaited_once_with(
            to=mock_password_reset_request.email,
            reset_token='test_reset_token',
            expires_minutes=15,
            subject="密码重置",
        )
        auth_service.redis_client.delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_request_password_reset_does_nothing_if_user_not_found(self, auth_service, mock_password_reset_request, mocker):
        """测试用户不存在时不执行任何操作（安全考虑）"""
        # Arrange
        mocker.patch.object(auth_service, '_verify_captcha', return_value=True)
        mock_crud_get_by_email = mocker.patch('app.crud.crud_user.get_by_email', return_value=None)
        mock_send_reset = mocker.patch.object(
            auth_service.email_provider,
            'send_password_reset',
            new_callable=AsyncMock,
        )

        # Act
        await auth_service.request_password_reset(mock_password_reset_request)

        # Assert
        mock_crud_get_by_email.assert_called_once_with(auth_service.db, mock_password_reset_request.email)
        auth_service.redis_client.set.assert_not_called()
        mock_send_reset.assert_not_called()

    @pytest.mark.asyncio
    async def test_request_password_reset_fails_if_email_send_fails(
        self, auth_service, mock_password_reset_request, mock_user, mocker
    ):
        """测试发信失败时作废 token 并抛错"""
        mocker.patch.object(auth_service, '_verify_captcha', return_value=True)
        mocker.patch('app.crud.crud_user.get_by_email', return_value=mock_user)
        mocker.patch('secrets.token_urlsafe', return_value='test_reset_token')
        mocker.patch.object(
            auth_service.email_provider,
            'send_password_reset',
            new_callable=AsyncMock,
            return_value=False,
        )

        with pytest.raises(RuntimeError, match="邮件服务发送失败"):
            await auth_service.request_password_reset(mock_password_reset_request)

        auth_service.redis_client.delete.assert_awaited_once_with("password_reset:test_reset_token")

    @pytest.mark.asyncio
    async def test_request_password_reset_fails_if_captcha_is_wrong(self, auth_service, mock_password_reset_request, mocker):
        """测试验证码错误时请求失败"""
        # Arrange
        mocker.patch.object(auth_service, '_verify_captcha', return_value=False)

        # Act & Assert
        with pytest.raises(CaptchaErrorException) as exc_info:
            await auth_service.request_password_reset(mock_password_reset_request)
        
        assert "图形验证码错误或已过期" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_perform_password_reset_success(self, auth_service, mock_password_reset_confirm_request, mock_user, mocker):
        """测试执行密码重置成功"""
        # Arrange
        auth_service.redis_client.get.return_value = str(mock_user.id)
        mocker.patch.object(auth_service, '_validate_password_strength', return_value=True)
        mocker.patch.object(auth_service, '_hash_password', return_value='new_hashed_password')
        mock_crud_get = mocker.patch('app.crud.crud_user.get', return_value=mock_user)
        mock_crud_update = mocker.patch('app.crud.crud_user.update')

        # Act
        await auth_service.perform_password_reset(mock_password_reset_confirm_request)

        # Assert
        auth_service.redis_client.delete.assert_called_once_with('password_reset:test_reset_token')
        mock_crud_update.assert_called_once()
        call_args = mock_crud_update.call_args
        obj_in = call_args[1]['obj_in']
        assert obj_in['password_hash'] == 'new_hashed_password'

    @pytest.mark.asyncio
    async def test_perform_password_reset_fails_if_token_is_invalid(self, auth_service, mock_password_reset_confirm_request, mocker):
        """测试无效令牌时重置失败"""
        # Arrange
        auth_service.redis_client.get.return_value = None

        # Act & Assert
        with pytest.raises(InvalidResetTokenException) as exc_info:
            await auth_service.perform_password_reset(mock_password_reset_confirm_request)
        
        assert "密码重置链接无效或已过期" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_perform_password_reset_fails_if_password_is_weak(self, auth_service, mock_password_reset_confirm_request, mocker):
        """测试密码强度不足时重置失败"""
        # Arrange
        auth_service.redis_client.get.return_value = "1"
        mocker.patch.object(auth_service, '_validate_password_strength', return_value=False)

        # Act & Assert
        with pytest.raises(WeakPasswordException) as exc_info:
            await auth_service.perform_password_reset(mock_password_reset_confirm_request)
        
        assert "新密码不符合强度要求" in str(exc_info.value)

    # ========================================================================
    # 验证码生成相关测试
    # ========================================================================

    @pytest.mark.asyncio
    async def test_generate_captcha_success(self, auth_service, mocker):
        """测试生成验证码成功"""
        # Arrange
        mock_uuid = MagicMock()
        mock_uuid.__str__ = MagicMock(return_value='test-uuid-123')
        mocker.patch('uuid.uuid4', return_value=mock_uuid)
        mocker.patch.object(auth_service, '_generate_captcha_solution', return_value='test')
        mocker.patch('base64.b64encode', return_value=b'dGVzdF9pbWFnZQ==')
        
        # Mock ImageCaptcha
        mock_image_captcha = MagicMock()
        mock_image_data = MagicMock()
        mock_image_data.getvalue.return_value = b'test_image_data'
        mock_image_captcha.generate.return_value = mock_image_data
        mocker.patch('app.services.auth_service.ImageCaptcha', return_value=mock_image_captcha)

        # Act
        result = await auth_service.generate_captcha()

        # Assert
        assert auth_service.redis_client.set.call_count == 2
        call_args = auth_service.redis_client.set.call_args
        assert call_args[0][0] == "captcha:image:test-uuid-123"
        assert call_args[0][1] == b'test_image_data'
        assert call_args[1]["ex"] == 180

        assert result["captcha_id"] == "test-uuid-123"
        assert result["image_base64"] == "data:image/png;base64,dGVzdF9pbWFnZQ=="

    @pytest.mark.asyncio
    async def test_generate_captcha_handles_redis_exception(self, auth_service, mocker):
        """测试 Redis 异常时抛出异常"""
        # Arrange
        mocker.patch('uuid.uuid4')
        mocker.patch.object(auth_service, '_generate_captcha_solution', return_value='test')
        auth_service.redis_client.set.side_effect = redis.exceptions.RedisError("Redis connection failed")

        # Act & Assert
        with pytest.raises(Exception):
            await auth_service.generate_captcha()

    # ========================================================================
    # 内部工具方法测试
    # ========================================================================

    def test_hash_password(self, auth_service):
        """测试密码哈希"""
        password = "test_password"
        hashed = auth_service._hash_password(password)
        
        assert isinstance(hashed, str)
        assert len(hashed) == 64  # SHA256 hex length
        assert hashed != password

    def test_verify_password(self, auth_service):
        """测试密码验证"""
        password = "test_password"
        correct_hash = auth_service._hash_password(password)
        wrong_hash = "wrong_hash"
        
        assert auth_service._verify_password(password, correct_hash) is True
        assert auth_service._verify_password(password, wrong_hash) is False

    def test_validate_password_strength(self, auth_service):
        """测试密码强度验证"""
        assert auth_service._validate_password_strength("123456") is False
        assert auth_service._validate_password_strength("12345") is False
        assert auth_service._validate_password_strength("") is False

    def test_mask_recipient_email(self, auth_service):
        """测试邮箱掩码"""
        result = auth_service._mask_recipient("test@example.com")
        assert result == "t**t@example.com"

    def test_mask_recipient_phone(self, auth_service):
        """测试手机号掩码"""
        result = auth_service._mask_recipient("13812345678")
        assert result == "138*****678"

    def test_generate_captcha_solution(self, auth_service):
        """测试验证码生成"""
        solution = auth_service._generate_captcha_solution(5)
        assert len(solution) == 5
        assert solution.isalnum()

    def test_generate_otp(self, auth_service):
        """测试 OTP 生成"""
        otp = auth_service._generate_otp(6)
        assert len(otp) == 6
        assert otp.isdigit()

    @pytest.mark.asyncio
    async def test_verify_captcha_success(self, auth_service):
        """测试验证码校验成功"""
        # Arrange
        auth_service.redis_client.get.return_value = "12345"
        
        # Act
        result = await auth_service._verify_captcha("test-id", "12345")
        
        # Assert
        assert result is True
        auth_service.redis_client.delete.assert_called_once_with("captcha:solution:test-id")

    @pytest.mark.asyncio
    async def test_verify_captcha_failure(self, auth_service):
        """测试验证码校验失败"""
        # Arrange
        auth_service.redis_client.get.return_value = "54321"
        
        # Act
        result = await auth_service._verify_captcha("test-id", "12345")
        
        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_is_token_blacklisted_true(self, auth_service):
        """测试令牌在黑名单中"""
        # Arrange
        auth_service.redis_client.get.return_value = "1"
        
        # Act
        result = await auth_service._is_token_blacklisted("test_token")
        
        # Assert
        assert result is True

    @pytest.mark.asyncio
    async def test_is_token_blacklisted_false(self, auth_service):
        """测试令牌不在黑名单中"""
        # Arrange
        auth_service.redis_client.get.return_value = None
        
        # Act
        result = await auth_service._is_token_blacklisted("test_token")
        
        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_blacklist_token_success(self, auth_service):
        """测试将令牌加入黑名单成功"""
        # Arrange
        auth_service.redis_client.set.return_value = True
        
        # Act
        result = await auth_service._blacklist_token("test_token", 3600)
        
        # Assert
        assert result is True
        auth_service.redis_client.set.assert_called_once_with("blacklist:token:test_token", "1", ex=3600) 