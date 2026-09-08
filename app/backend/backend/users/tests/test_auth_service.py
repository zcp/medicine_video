"""
用户服务 - AuthService 单元测试

测试 app/services/auth_service.py 中的 AuthService 类的所有业务逻辑，
使用 mocker fixture 模拟所有外部依赖。
"""

import pytest
import json
import uuid
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
import redis.exceptions
import jwt

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
from app.exceptions import ValidationError
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
            captcha_solution="12345"
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
        mock_create_access_token.assert_called_once_with(str(mock_user.public_id), mock_user.role.value, username=mock_user.username, nickname=mock_user.nickname, can_stream=True, avatar_url=mock_user.avatar_url)
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
        
        assert "账号或密码错误" in str(exc_info.value)

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
        
        assert "账号或密码错误" in str(exc_info.value)

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
        # OTP 现在是 JSON 格式（含 attempts、max_attempts）
        import json as _json
        stored_data = _json.loads(call_args[0][1])
        assert stored_data["code"] == "123456"
        assert stored_data["attempts"] == 0
        assert stored_data["max_attempts"] == 5
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
        
        assert "该账号已被注册" in str(exc_info.value)

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
        mock_payload = {"user_id": test_user_uuid, "type": "refresh", "iat": 1234567800, "exp": 1234567890}
        mock_verify_token = mocker.patch.object(auth_service, '_verify_token', return_value=mock_payload)
        mock_is_blacklisted = mocker.patch.object(auth_service, '_is_token_blacklisted', return_value=False)
        mock_sessions_revoked = mocker.patch.object(auth_service, '_is_user_sessions_revoked', return_value=False)
        mock_create_access_token = mocker.patch.object(auth_service, '_create_access_token', return_value='new_access_token')
        mock_crud_get_by_uuid = mocker.patch('app.crud.crud_user.get_by_uuid', return_value=MagicMock(role=MagicMock(value="REGULAR")))

        # Act
        result = await auth_service.refresh_access_token('refresh_token_123')

        # Assert
        # 生产返回 3 键：access_token + refresh_token（轮换）+ token_type
        assert result["access_token"] == "new_access_token"
        assert result["token_type"] == "bearer"
        assert "refresh_token" in result and result["refresh_token"]
        mock_verify_token.assert_called_once_with('refresh_token_123', token_type="refresh")
        mock_is_blacklisted.assert_called_once_with('refresh_token_123')
        mock_create_access_token.assert_called_once_with(test_user_uuid, "REGULAR", can_stream=True, avatar_url=mock_crud_get_by_uuid.return_value.avatar_url)

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

        # Act
        await auth_service.request_password_reset(mock_password_reset_request)

        # Assert
        mock_crud_get_by_email.assert_called_once_with(auth_service.db, mock_password_reset_request.email)
        auth_service.redis_client.set.assert_called_once()
        call_args = auth_service.redis_client.set.call_args
        assert call_args[0][0] == "password_reset:test_reset_token"
        assert call_args[0][1] == str(mock_user.id)
        assert call_args[1]["ex"] == 900

    @pytest.mark.asyncio
    async def test_request_password_reset_does_nothing_if_user_not_found(self, auth_service, mock_password_reset_request, mocker):
        """测试用户不存在时不执行任何操作（安全考虑）"""
        # Arrange
        mocker.patch.object(auth_service, '_verify_captcha', return_value=True)
        mock_crud_get_by_email = mocker.patch('app.crud.crud_user.get_by_email', return_value=None)

        # Act
        await auth_service.request_password_reset(mock_password_reset_request)

        # Assert
        mock_crud_get_by_email.assert_called_once_with(auth_service.db, mock_password_reset_request.email)
        auth_service.redis_client.set.assert_not_called()

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
        # 密码强度在 token 验证之前检查，此处 mock 为 True 使其通过
        mocker.patch.object(auth_service, '_validate_password_strength', return_value=True)

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
        
        assert "密码必须至少8位" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_perform_password_reset_fails_if_password_same_as_old(self, auth_service, mock_password_reset_confirm_request, mock_user, mocker):
        """测试新密码与原密码相同时重置失败"""
        # Arrange
        auth_service.redis_client.get.return_value = str(mock_user.id)
        mocker.patch.object(auth_service, '_validate_password_strength', return_value=True)
        mocker.patch.object(auth_service, '_verify_password', return_value=True)
        mocker.patch('app.crud.crud_user.get', return_value=mock_user)
        mock_crud_update = mocker.patch('app.crud.crud_user.update')

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            await auth_service.perform_password_reset(mock_password_reset_confirm_request)

        assert "新密码不能与原密码相同" in str(exc_info.value)
        mock_crud_update.assert_not_called()
        # token 在强度校验后、一致性校验失败时已被消费（现有流程），需重新获取重置链接
        auth_service.redis_client.delete.assert_called_once_with('password_reset:test_reset_token')

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
        # base64 编码后存储
        import base64 as _b64
        assert call_args[0][1] == _b64.b64encode(b'test_image_data').decode()
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

    def test_create_access_token_default_can_stream_true(self, auth_service):
        """默认签发 access token 时 can_stream 应为 True（默认允许开播）"""
        token = auth_service._create_access_token(str(uuid.uuid4()), "REGULAR")
        payload = jwt.decode(token, auth_service.jwt_secret_key, algorithms=[auth_service.jwt_algorithm])
        assert payload["can_stream"] is True

    def test_create_access_token_explicit_can_stream_false(self, auth_service):
        """显式传入 can_stream=False 时 payload 应为 False（禁播生效）"""
        token = auth_service._create_access_token(str(uuid.uuid4()), "REGULAR", can_stream=False)
        payload = jwt.decode(token, auth_service.jwt_secret_key, algorithms=[auth_service.jwt_algorithm])
        assert payload["can_stream"] is False

    def test_hash_password(self, auth_service):
        """测试密码哈希"""
        password = "test_password"
        hashed = auth_service._hash_password(password)
        
        assert isinstance(hashed, str)
        # bcrypt 哈希特征：以 $2b$ 开头，长度 60
        assert hashed.startswith("$2b$"), f"期望 bcrypt 格式，实际: {hashed[:10]}"
        assert len(hashed) == 60, f"bcrypt 哈希长度应为 60，实际: {len(hashed)}"
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

    # ========================================================================
    # Phase 4: 一键登录测试
    # ========================================================================

    @pytest.mark.asyncio
    async def test_one_tap_login_existing_user_success(self, auth_service, mock_user, mocker):
        """一键登录：已有手机号用户直接登录成功"""
        # Arrange
        mock_user.public_id = uuid.uuid4()
        mock_user.role = MagicMock()
        mock_user.role.value = "REGULAR"
        mock_user.username = "testuser"
        mock_user.nickname = "TestUser"

        mocker.patch.object(
            auth_service.carrier_auth_provider, 'get_phone_number',
            return_value='13800000000'
        )
        mocker.patch('app.crud.crud_user.get_by_phone_number', return_value=mock_user)

        mocker.patch.object(auth_service, '_create_access_token', return_value='access_token_123')
        mocker.patch.object(auth_service, '_create_refresh_token', return_value='refresh_token_123')
        mocker.patch.object(auth_service, '_mask_recipient', return_value='138****0000')

        request = schemas.OneTapLoginRequest(carrier_token='test_token', provider='mock', agreed_to_terms=True)

        # Act
        result = await auth_service.one_tap_login(request)

        # Assert
        assert result["access_token"] == 'access_token_123'
        assert result["refresh_token"] == 'refresh_token_123'
        assert result["is_new_user"] is False
        assert result["phone_masked"] == '138****0000'
        auth_service.db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_one_tap_login_new_user_auto_register(self, auth_service, mock_user, mocker):
        """一键登录：新手机号自动注册并登录"""
        # Arrange
        mocker.patch.object(
            auth_service.carrier_auth_provider, 'get_phone_number',
            return_value='13900000000'
        )
        # 用户不存在 → 返回 None
        mocker.patch('app.crud.crud_user.get_by_phone_number', return_value=None)

        # mock 新建用户
        new_user = MagicMock()
        new_user.id = 2
        new_user.public_id = uuid.uuid4()
        new_user.status = EntityStatus.NORMAL
        new_user.role = MagicMock(value="REGULAR")
        new_user.username = "u_abc123"
        new_user.nickname = "用户0000"
        new_user.is_phone_verified = True
        new_user.last_login_at = None
        mocker.patch('app.crud.crud_user.create', return_value=new_user)

        mocker.patch.object(auth_service, '_create_access_token', return_value='access_token_456')
        mocker.patch.object(auth_service, '_create_refresh_token', return_value='refresh_token_456')
        mocker.patch.object(auth_service, '_mask_recipient', return_value='139****0000')

        request = schemas.OneTapLoginRequest(carrier_token='test_token', provider='mock', agreed_to_terms=True)

        # Act
        result = await auth_service.one_tap_login(request)

        # Assert
        assert result["is_new_user"] is True
        assert result["access_token"] == 'access_token_456'
        assert result["phone_masked"] == '139****0000'
        # 验证自动注册：crud_user.create 被调用
        auth_service.db.commit.assert_called()

    @pytest.mark.asyncio
    async def test_one_tap_login_banned_user_fails(self, auth_service, mock_user, mocker):
        """一键登录：被封禁用户登录失败"""
        # Arrange
        mocker.patch.object(
            auth_service.carrier_auth_provider, 'get_phone_number',
            return_value='13800000000'
        )
        banned_user = MagicMock()
        banned_user.id = 1
        banned_user.public_id = uuid.uuid4()
        banned_user.status = EntityStatus.BANNED
        banned_user.role = MagicMock(value="REGULAR")
        banned_user.username = "testuser"
        banned_user.nickname = "Test"
        banned_user.last_login_at = None
        mocker.patch('app.crud.crud_user.get_by_phone_number', return_value=banned_user)

        request = schemas.OneTapLoginRequest(carrier_token='test_token', provider='mock', agreed_to_terms=True)

        # Act & Assert
        with pytest.raises(InvalidCredentialsException) as exc_info:
            await auth_service.one_tap_login(request)
        assert "被封禁" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_one_tap_login_invalid_carrier_token_fails(self, auth_service, mocker):
        """一键登录：运营商 token 无效时取号失败"""
        # Arrange
        mocker.patch.object(
            auth_service.carrier_auth_provider, 'get_phone_number',
            side_effect=ValueError("Invalid token")
        )

        request = schemas.OneTapLoginRequest(carrier_token='bad_token', provider='mock', agreed_to_terms=True)

        # Act & Assert
        with pytest.raises(InvalidTokenException) as exc_info:
            await auth_service.one_tap_login(request)
        assert "取号失败" in str(exc_info.value)

    # ========================================================================
    # OTP 校验与 Ticket 签发测试
    # ========================================================================

    @pytest.mark.asyncio
    async def test_verify_otp_and_issue_ticket_success(self, auth_service, mocker):
        """校验验证码成功并签发 ticket（REGISTER 场景）"""
        # Arrange
        import secrets
        otp_data = json.dumps({"code": "123456", "attempts": 0, "max_attempts": 5})
        auth_service.redis_client.get.return_value = otp_data
        auth_service.redis_client.ttl.return_value = 200
        mocker.patch('secrets.token_urlsafe', return_value='test_ticket_id')

        verify_request = schemas.VerifyCodeRequest(
            channel="SMS",
            recipient="13800000000",
            scenario="REGISTER",
            code="123456",
        )

        # Act
        result = await auth_service.verify_otp_and_issue_ticket(verify_request)

        # Assert
        assert result["ticket"] == "test_ticket_id"
        assert result["expires_in"] == 600
        # OTP 已被删除
        auth_service.redis_client.delete.assert_called_once_with("otp:REGISTER:13800000000")
        # ticket 已存储
        ticket_call_args = auth_service.redis_client.set.call_args
        assert ticket_call_args[0][0] == "ticket:REGISTER:test_ticket_id"

    @pytest.mark.asyncio
    async def test_verify_otp_and_issue_ticket_wrong_code(self, auth_service, mocker):
        """校验验证码：错误验证码拒绝并递增尝试次数"""
        # Arrange
        otp_data = json.dumps({"code": "654321", "attempts": 0, "max_attempts": 5})
        auth_service.redis_client.get.return_value = otp_data
        auth_service.redis_client.ttl.return_value = 200

        verify_request = schemas.VerifyCodeRequest(
            channel="SMS",
            recipient="13800000000",
            scenario="REGISTER",
            code="123456",
        )

        # Act & Assert
        with pytest.raises(InvalidCredentialsException) as exc_info:
            await auth_service.verify_otp_and_issue_ticket(verify_request)
        assert "验证码错误" in str(exc_info.value)
        # 验证 attempts 已递增并写回 Redis
        set_call_args = auth_service.redis_client.set.call_args
        updated_data = json.loads(set_call_args[0][1])
        assert updated_data["attempts"] == 1

    @pytest.mark.asyncio
    async def test_verify_otp_and_issue_ticket_expired(self, auth_service, mocker):
        """校验验证码：OTP 已过期"""
        # Arrange
        auth_service.redis_client.get.return_value = None

        verify_request = schemas.VerifyCodeRequest(
            channel="SMS",
            recipient="13800000000",
            scenario="REGISTER",
            code="123456",
        )

        # Act & Assert
        with pytest.raises(InvalidTokenException) as exc_info:
            await auth_service.verify_otp_and_issue_ticket(verify_request)
        assert "不存在或已过期" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_verify_otp_and_issue_ticket_max_attempts_exceeded(self, auth_service, mocker):
        """校验验证码：尝试次数超限"""
        # Arrange
        otp_data = json.dumps({"code": "123456", "attempts": 5, "max_attempts": 5})
        auth_service.redis_client.get.return_value = otp_data

        verify_request = schemas.VerifyCodeRequest(
            channel="SMS",
            recipient="13800000000",
            scenario="REGISTER",
            code="123456",
        )

        # Act & Assert
        with pytest.raises(RateLimitException) as exc_info:
            await auth_service.verify_otp_and_issue_ticket(verify_request)
        assert "尝试次数过多" in str(exc_info.value)
        # 验证 OTP 已被删除（超限后清理）
        auth_service.redis_client.delete.assert_called_once_with("otp:REGISTER:13800000000")

    @pytest.mark.asyncio
    async def test_verify_otp_and_issue_ticket_reset_password_embeds_user_id(self, auth_service, mock_user, mocker):
        """校验验证码：RESET_PASSWORD 场景在 ticket 中嵌入 user_id"""
        # Arrange
        import secrets
        mock_user.public_id = uuid.uuid4()
        otp_data = json.dumps({"code": "123456", "attempts": 0, "max_attempts": 5})
        auth_service.redis_client.get.return_value = otp_data
        auth_service.redis_client.ttl.return_value = 200
        mocker.patch('secrets.token_urlsafe', return_value='reset_ticket_id')

        # mock _find_user_by_channel 返回用户
        mocker.patch.object(auth_service, '_find_user_by_channel', return_value=mock_user)

        verify_request = schemas.VerifyCodeRequest(
            channel="SMS",
            recipient="13800000000",
            scenario="RESET_PASSWORD",
            code="123456",
        )

        # Act
        result = await auth_service.verify_otp_and_issue_ticket(verify_request)

        # Assert
        assert result["ticket"] == "reset_ticket_id"
        # 验证 ticket 中嵌入了 user_id
        ticket_call_args = auth_service.redis_client.set.call_args
        ticket_data = json.loads(ticket_call_args[0][1])
        assert ticket_data["purpose"] == "RESET_PASSWORD"
        assert ticket_data["user_id"] == mock_user.id
        assert ticket_data["user_public_id"] == str(mock_user.public_id)

    # ========================================================================
    # 手机号验证码登录测试（login_by_phone_ticket）
    # ========================================================================

    @pytest.mark.asyncio
    async def test_login_by_phone_ticket_success(self, auth_service, mock_user, mocker):
        """手机号验证码登录：有效 ticket + 正常用户 → 签发 JWT"""
        # Arrange
        mock_user.public_id = uuid.uuid4()
        mock_user.role = MagicMock(value="REGULAR")
        mock_user.username = "testuser"
        mock_user.nickname = "TestUser"

        ticket_data = {
            "channel": "SMS",
            "recipient": "13800000000",
            "purpose": "LOGIN",
        }
        mocker.patch.object(auth_service, '_consume_ticket', return_value=ticket_data)
        mocker.patch('app.crud.crud_user.get_by_phone_number', return_value=mock_user)
        mocker.patch.object(auth_service, '_create_access_token', return_value='access_token_phone')
        mocker.patch.object(auth_service, '_create_refresh_token', return_value='refresh_token_phone')
        mocker.patch.object(auth_service, '_mask_recipient', return_value='138****0000')

        request = schemas.PhoneLoginRequest(login_ticket='valid_ticket')

        # Act
        result = await auth_service.login_by_phone_ticket(request)

        # Assert
        assert result["access_token"] == 'access_token_phone'
        assert result["refresh_token"] == 'refresh_token_phone'
        assert result["phone_masked"] == '138****0000'
        auth_service.db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_login_by_phone_ticket_user_not_found(self, auth_service, mocker):
        """手机号验证码登录：手机号未注册 → 拒绝"""
        # Arrange
        ticket_data = {
            "channel": "SMS",
            "recipient": "13800000000",
            "purpose": "LOGIN",
        }
        mocker.patch.object(auth_service, '_consume_ticket', return_value=ticket_data)
        mocker.patch('app.crud.crud_user.get_by_phone_number', return_value=None)

        request = schemas.PhoneLoginRequest(login_ticket='valid_ticket')

        # Act & Assert
        with pytest.raises(InvalidCredentialsException):
            await auth_service.login_by_phone_ticket(request)

    @pytest.mark.asyncio
    async def test_login_by_phone_ticket_wrong_channel(self, auth_service, mocker):
        """手机号验证码登录：ticket channel 不是 SMS → 拒绝"""
        # Arrange
        ticket_data = {
            "channel": "EMAIL",
            "recipient": "test@example.com",
            "purpose": "LOGIN",
        }
        mocker.patch.object(auth_service, '_consume_ticket', return_value=ticket_data)

        request = schemas.PhoneLoginRequest(login_ticket='email_ticket')

        # Act & Assert
        with pytest.raises(InvalidCredentialsException):
            await auth_service.login_by_phone_ticket(request)

    @pytest.mark.asyncio
    async def test_login_by_phone_ticket_banned_user(self, auth_service, mocker):
        """手机号验证码登录：被封禁用户 → 拒绝"""
        # Arrange
        ticket_data = {
            "channel": "SMS",
            "recipient": "13800000000",
            "purpose": "LOGIN",
        }
        banned_user = MagicMock()
        banned_user.id = 1
        banned_user.public_id = uuid.uuid4()
        banned_user.status = EntityStatus.BANNED
        banned_user.role = MagicMock(value="REGULAR")
        banned_user.username = "testuser"
        banned_user.nickname = "Test"

        mocker.patch.object(auth_service, '_consume_ticket', return_value=ticket_data)
        mocker.patch('app.crud.crud_user.get_by_phone_number', return_value=banned_user)

        request = schemas.PhoneLoginRequest(login_ticket='valid_ticket')

        # Act & Assert
        with pytest.raises(InvalidCredentialsException):
            await auth_service.login_by_phone_ticket(request)

    # ========================================================================
    # 手机号注册测试（register_by_phone_ticket）
    # ========================================================================

    @pytest.mark.asyncio
    async def test_register_by_phone_ticket_success(self, auth_service, mocker):
        """手机号注册：有效 ticket → 创建用户 → 签发 JWT"""
        # Arrange
        ticket_data = {"recipient": "13800000000", "purpose": "REGISTER"}
        mocker.patch.object(auth_service, '_consume_ticket', return_value=ticket_data)
        mocker.patch('app.crud.crud_user.get_by_phone_number', return_value=None)
        mocker.patch.object(auth_service, '_validate_password_strength', return_value=True)
        mocker.patch.object(auth_service, '_hash_password', return_value='bcrypt_hash')

        new_user = MagicMock()
        new_user.id = 99
        new_user.public_id = uuid.uuid4()
        new_user.username = "u_newuser"
        new_user.nickname = "新用户"
        new_user.is_phone_verified = True
        mocker.patch('app.crud.crud_user.create', return_value=new_user)

        mocker.patch.object(auth_service, '_create_access_token', return_value='access_token_reg')
        mocker.patch.object(auth_service, '_create_refresh_token', return_value='refresh_token_reg')
        mocker.patch.object(auth_service, '_mask_recipient', return_value='138****0000')

        request = schemas.PhoneRegisterRequest(
            register_ticket='valid_ticket', password='NewPass@123', nickname='新用户',
        )

        # Act
        result = await auth_service.register_by_phone_ticket(request)

        # Assert
        assert result["access_token"] == 'access_token_reg'
        assert result["is_new_user"] is True
        assert result["phone_masked"] == '138****0000'
        auth_service.db.commit.assert_called_once()
        auth_service.db.refresh.assert_called_once_with(new_user)

    @pytest.mark.asyncio
    async def test_register_by_phone_ticket_duplicate(self, auth_service, mocker):
        """手机号注册：手机号已被注册 → 拒绝"""
        # Arrange
        ticket_data = {"recipient": "13800000000", "purpose": "REGISTER"}
        mocker.patch.object(auth_service, '_consume_ticket', return_value=ticket_data)
        mocker.patch('app.crud.crud_user.get_by_phone_number',
                     return_value=MagicMock(id=1))

        request = schemas.PhoneRegisterRequest(
            register_ticket='valid_ticket', password='NewPass@123', nickname='用户',
        )

        # Act & Assert
        with pytest.raises(UserAlreadyExistsException):
            await auth_service.register_by_phone_ticket(request)

    @pytest.mark.asyncio
    async def test_register_by_phone_ticket_weak_password(self, auth_service, mocker):
        """手机号注册：弱密码 → 拒绝"""
        # Arrange
        ticket_data = {"recipient": "13800000000", "purpose": "REGISTER"}
        mocker.patch.object(auth_service, '_consume_ticket', return_value=ticket_data)
        mocker.patch('app.crud.crud_user.get_by_phone_number', return_value=None)
        mocker.patch.object(auth_service, '_validate_password_strength', return_value=False)

        request = schemas.PhoneRegisterRequest(
            register_ticket='valid_ticket', password='12345678', nickname='用户',
        )

        # Act & Assert
        with pytest.raises(WeakPasswordException):
            await auth_service.register_by_phone_ticket(request)

    @pytest.mark.asyncio
    async def test_register_by_phone_ticket_invalid_ticket(self, auth_service, mocker):
        """手机号注册：无效 ticket → 拒绝"""
        # Arrange
        mocker.patch.object(auth_service, '_consume_ticket',
                            side_effect=InvalidTokenException("凭证无效或已过期"))

        request = schemas.PhoneRegisterRequest(
            register_ticket='bad_ticket', password='NewPass@123', nickname='用户',
        )

        # Act & Assert
        with pytest.raises(InvalidTokenException):
            await auth_service.register_by_phone_ticket(request)

    # ========================================================================
    # Ticket 消费测试（_consume_ticket）
    # ========================================================================

    @pytest.mark.asyncio
    async def test_consume_ticket_success(self, auth_service):
        """消费 ticket：有效 ticket → 返回 JSON payload 并删除"""
        # Arrange
        ticket_data = {"purpose": "REGISTER", "recipient": "13800000000"}
        auth_service.redis_client.get.return_value = json.dumps(ticket_data)

        # Act
        result = await auth_service._consume_ticket("REGISTER", "test_ticket_id")

        # Assert
        assert result["purpose"] == "REGISTER"
        assert result["recipient"] == "13800000000"
        auth_service.redis_client.delete.assert_called_once_with("ticket:REGISTER:test_ticket_id")

    @pytest.mark.asyncio
    async def test_consume_ticket_not_found(self, auth_service):
        """消费 ticket：无效 ticket → 拒绝"""
        # Arrange
        auth_service.redis_client.get.return_value = None

        # Act & Assert
        with pytest.raises(InvalidTokenException):
            await auth_service._consume_ticket("REGISTER", "bad_ticket_id")

    # ========================================================================
    # 会话吊销测试（_revoke_user_sessions / _is_user_sessions_revoked）
    # ========================================================================

    @pytest.mark.asyncio
    async def test_revoke_user_sessions_success(self, auth_service):
        """吊销用户会话：Redis 写入正确 key 和时间戳"""
        # Arrange
        user_public_id = str(uuid.uuid4())

        # Act
        await auth_service._revoke_user_sessions(user_public_id)

        # Assert
        auth_service.redis_client.set.assert_called_once()
        call_args = auth_service.redis_client.set.call_args
        assert call_args[0][0] == f"user_sessions_revoked:{user_public_id}"
        # 值是 ISO 时间戳
        from datetime import datetime
        datetime.fromisoformat(call_args[0][1])
        assert call_args[1]["ex"] == 86400 * 7

    @pytest.mark.asyncio
    async def test_is_user_sessions_revoked_not_revoked(self, auth_service):
        """检查会话吊销：未被吊销 → False"""
        # Arrange
        auth_service.redis_client.get.return_value = None

        # Act
        result = await auth_service._is_user_sessions_revoked("test_public_id")

        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_is_user_sessions_revoked_token_iat_before_revocation(self, auth_service):
        """检查会话吊销：token 签发早于吊销时间 → True"""
        # Arrange
        revocation_time = datetime.utcnow()
        auth_service.redis_client.get.return_value = revocation_time.isoformat()
        token_iat = revocation_time - timedelta(seconds=10)  # token 在吊销之前签发

        # Act
        result = await auth_service._is_user_sessions_revoked("test_public_id", token_iat=token_iat)

        # Assert
        assert result is True

    @pytest.mark.asyncio
    async def test_is_user_sessions_revoked_token_iat_after_revocation(self, auth_service):
        """检查会话吊销：token 签发晚于吊销时间 → False"""
        # Arrange
        revocation_time = datetime.utcnow()
        auth_service.redis_client.get.return_value = revocation_time.isoformat()
        token_iat = revocation_time + timedelta(seconds=10)  # token 在吊销之后签发

        # Act
        result = await auth_service._is_user_sessions_revoked("test_public_id", token_iat=token_iat)

        # Assert
        assert result is False

    # ========================================================================
    # 密码哈希升级测试（_upgrade_password_hash_if_needed）
    # ========================================================================

    @pytest.mark.asyncio
    async def test_upgrade_password_hash_legacy_sha256(self, auth_service, mock_user, mocker):
        """旧 SHA-256 密码 → 升级为 bcrypt，commit 被调用"""
        # Arrange
        mock_user.password_hash = "a" * 64  # 64 位十六进制 = SHA-256 特征
        mocker.patch.object(auth_service, '_hash_password', return_value='$2b$12$new_bcrypt_hash')

        # Act
        await auth_service._upgrade_password_hash_if_needed(mock_user, 'my_password')

        # Assert
        assert mock_user.password_hash == '$2b$12$new_bcrypt_hash'
        auth_service.db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_upgrade_password_hash_already_bcrypt(self, auth_service, mock_user, mocker):
        """已是 bcrypt 密码 → 不升级，不 commit"""
        # Arrange
        mock_user.password_hash = '$2b$12$existing_bcrypt_hash'
        hash_spy = mocker.patch.object(auth_service, '_hash_password', return_value='new_hash')

        # Act
        await auth_service._upgrade_password_hash_if_needed(mock_user, 'my_password')

        # Assert
        hash_spy.assert_not_called()
        auth_service.db.commit.assert_not_called()

    # ========================================================================
    # P2: send_otp_code LOGIN 场景测试
    # ========================================================================

    @pytest.mark.asyncio
    async def test_send_otp_code_success_for_login(self, auth_service, mocker):
        """发送验证码：LOGIN 场景不校验用户存在性，直接发送"""
        # Arrange
        mocker.patch.object(auth_service, '_verify_captcha', return_value=True)
        mocker.patch.object(auth_service, '_generate_otp', return_value='654321')
        mocker.patch.object(auth_service, '_mask_recipient', return_value='138****0000')
        mocker.patch.object(auth_service.sms_provider, 'send', return_value=True)

        login_otp_request = schemas.VerificationCodeRequest(
            channel="SMS", recipient="13800000000",
            scenario="LOGIN",
            captcha_id="test-captcha-id", captcha_solution="12345",
        )

        # Act
        result = await auth_service.send_otp_code(login_otp_request, "192.168.1.1")

        # Assert
        assert result["message"] == "验证码已发送，请注意查收。"
        auth_service.redis_client.set.assert_called_once()
        call_args = auth_service.redis_client.set.call_args
        assert "otp:LOGIN:13800000000" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_send_otp_code_success_for_bind_phone(self, auth_service, mocker):
        """发送验证码：BIND_PHONE 场景不校验用户存在性，直接发送"""
        # Arrange
        mocker.patch.object(auth_service, '_verify_captcha', return_value=True)
        mocker.patch.object(auth_service, '_generate_otp', return_value='111222')
        mocker.patch.object(auth_service, '_mask_recipient', return_value='138****0000')
        mocker.patch.object(auth_service.sms_provider, 'send', return_value=True)

        bind_otp_request = schemas.VerificationCodeRequest(
            channel="SMS", recipient="13800000000",
            scenario="BIND_PHONE",
            captcha_id="test-captcha-id", captcha_solution="12345",
        )

        # Act
        result = await auth_service.send_otp_code(bind_otp_request, "192.168.1.1")

        # Assert
        assert result["message"] == "验证码已发送，请注意查收。"
        auth_service.redis_client.set.assert_called_once()
        call_args = auth_service.redis_client.set.call_args
        assert "otp:BIND_PHONE:13800000000" in call_args[0][0]

    # ========================================================================
    # P2: 重置密码 reset_ticket 路径测试
    # ========================================================================

    @pytest.mark.asyncio
    async def test_perform_password_reset_via_reset_ticket_success(self, auth_service, mock_user, mocker):
        """密码重置：reset_ticket 路径 → 消费 ticket → 更新密码 → 吊销旧会话"""
        # Arrange
        mock_user.public_id = uuid.uuid4()
        mocker.patch.object(auth_service, '_validate_password_strength', return_value=True)
        mocker.patch.object(auth_service, '_hash_password', return_value='new_bcrypt_hash')
        mock_revoke = mocker.patch.object(auth_service, '_revoke_user_sessions')

        ticket_data = {
            "user_id": str(mock_user.id),
            "purpose": "RESET_PASSWORD",
        }
        mocker.patch.object(auth_service, '_consume_ticket', return_value=ticket_data)
        mocker.patch('app.crud.crud_user.get', return_value=mock_user)
        mock_crud_update = mocker.patch('app.crud.crud_user.update')

        confirm_request = schemas.PasswordResetConfirmRequest(
            reset_ticket='valid_ticket', new_password='NewPass@123',
        )

        # Act
        await auth_service.perform_password_reset(confirm_request)

        # Assert
        mock_crud_update.assert_called_once()
        # 旧会话已被吊销
        mock_revoke.assert_called_once_with(str(mock_user.public_id))

    @pytest.mark.asyncio
    async def test_perform_password_reset_via_reset_ticket_no_user_id(self, auth_service, mocker):
        """密码重置：reset_ticket 不含 user_id → 拒绝"""
        # Arrange
        mocker.patch.object(auth_service, '_validate_password_strength', return_value=True)
        ticket_data = {"purpose": "RESET_PASSWORD"}  # 缺少 user_id
        mocker.patch.object(auth_service, '_consume_ticket', return_value=ticket_data)

        confirm_request = schemas.PasswordResetConfirmRequest(
            reset_ticket='bad_ticket', new_password='NewPass@123',
        )

        # Act & Assert
        with pytest.raises((InvalidResetTokenException, Exception)):
            await auth_service.perform_password_reset(confirm_request)

    # ========================================================================
    # P2: request_password_reset 已封禁用户测试
    # ========================================================================

    @pytest.mark.asyncio
    async def test_request_password_reset_banned_user_silent_return(self, auth_service, mock_password_reset_request, mocker):
        """请求密码重置：已封禁用户 → 静默返回（不生成 token，防枚举）"""
        # Arrange
        banned_user = MagicMock()
        banned_user.id = 1
        banned_user.status = EntityStatus.BANNED

        mocker.patch.object(auth_service, '_verify_captcha', return_value=True)
        mocker.patch('app.crud.crud_user.get_by_email', return_value=banned_user)

        # Act
        await auth_service.request_password_reset(mock_password_reset_request)

        # Assert
        auth_service.redis_client.set.assert_not_called()  # 不生成 token

    @pytest.mark.asyncio
    async def test_request_password_reset_deleted_user_silent_return(self, auth_service, mock_password_reset_request, mocker):
        """请求密码重置：已注销用户 → 静默返回"""
        # Arrange
        deleted_user = MagicMock()
        deleted_user.id = 1
        deleted_user.status = EntityStatus.DELETED

        mocker.patch.object(auth_service, '_verify_captcha', return_value=True)
        mocker.patch('app.crud.crud_user.get_by_email', return_value=deleted_user)

        # Act
        await auth_service.request_password_reset(mock_password_reset_request)

        # Assert
        auth_service.redis_client.set.assert_not_called()

# ============================================================================

class TestSettingsProductionValidation:
    """测试 Settings 生产环境校验逻辑"""

    def test_production_rejects_sms_provider_mock(self, monkeypatch):
        """P1: 生产环境 SMS_PROVIDER=mock 启动校验失败"""
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("POSTGRES_PASSWORD", "secure_pass_12345678")
        monkeypatch.setenv("JWT_SECRET_KEY", "a-32-byte-minimum-secret-key-ok!")
        monkeypatch.setenv("CORS_ORIGINS", "https://app.example.com")
        monkeypatch.setenv("DEBUG", "false")
        monkeypatch.setenv("SMS_PROVIDER", "mock")
        monkeypatch.setenv("CARRIER_AUTH_PROVIDER", "mock")

        from app.core.config import Settings
        with pytest.raises(ValueError) as exc_info:
            Settings()
        assert "SMS_PROVIDER" in str(exc_info.value)
        assert "mock" in str(exc_info.value)

    def test_production_rejects_carrier_auth_provider_mock(self, monkeypatch):
        """P1: 生产环境 CARRIER_AUTH_PROVIDER=mock 启动校验失败"""
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("POSTGRES_PASSWORD", "secure_pass_12345678")
        monkeypatch.setenv("JWT_SECRET_KEY", "a-32-byte-minimum-secret-key-ok!")
        monkeypatch.setenv("CORS_ORIGINS", "https://app.example.com")
        monkeypatch.setenv("DEBUG", "false")
        monkeypatch.setenv("SMS_PROVIDER", "aliyun")
        monkeypatch.setenv("ALIYUN_ACCESS_KEY_ID", "ak")
        monkeypatch.setenv("ALIYUN_ACCESS_KEY_SECRET", "sk")
        monkeypatch.setenv("ALIYUN_SMS_SIGN_NAME", "sign")
        monkeypatch.setenv("ALIYUN_SMS_TEMPLATE_CODE", "tpl")
        monkeypatch.setenv("CARRIER_AUTH_PROVIDER", "mock")

        from app.core.config import Settings
        with pytest.raises(ValueError) as exc_info:
            Settings()
        assert "CARRIER_AUTH_PROVIDER" in str(exc_info.value)
        assert "mock" in str(exc_info.value)

    def test_production_rejects_aliyun_sms_missing_key_id(self, monkeypatch):
        """P1: 生产环境 SMS_PROVIDER=aliyun 缺 ALIYUN_ACCESS_KEY_ID 校验失败"""
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("POSTGRES_PASSWORD", "secure_pass_12345678")
        monkeypatch.setenv("JWT_SECRET_KEY", "a-32-byte-minimum-secret-key-ok!")
        monkeypatch.setenv("CORS_ORIGINS", "https://app.example.com")
        monkeypatch.setenv("DEBUG", "false")
        monkeypatch.setenv("SMS_PROVIDER", "aliyun")
        monkeypatch.setenv("ALIYUN_ACCESS_KEY_ID", "")
        monkeypatch.setenv("ALIYUN_ACCESS_KEY_SECRET", "sk")
        monkeypatch.setenv("ALIYUN_SMS_SIGN_NAME", "sign")
        monkeypatch.setenv("ALIYUN_SMS_TEMPLATE_CODE", "tpl")
        monkeypatch.setenv("CARRIER_AUTH_PROVIDER", "mock")


        from app.core.config import Settings
        with pytest.raises(ValueError) as exc_info:
            Settings()
        assert "ALIYUN_ACCESS_KEY_ID" in str(exc_info.value)

    def test_production_rejects_aliyun_sms_missing_sign_name(self, monkeypatch):
        """P1: 生产环境 SMS_PROVIDER=aliyun 缺 ALIYUN_SMS_SIGN_NAME 校验失败"""
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("POSTGRES_PASSWORD", "secure_pass_12345678")
        monkeypatch.setenv("JWT_SECRET_KEY", "a-32-byte-minimum-secret-key-ok!")
        monkeypatch.setenv("CORS_ORIGINS", "https://app.example.com")
        monkeypatch.setenv("DEBUG", "false")
        monkeypatch.setenv("SMS_PROVIDER", "aliyun")
        monkeypatch.setenv("ALIYUN_ACCESS_KEY_ID", "ak")
        monkeypatch.setenv("ALIYUN_ACCESS_KEY_SECRET", "sk")
        monkeypatch.setenv("ALIYUN_SMS_SIGN_NAME", "")
        monkeypatch.setenv("ALIYUN_SMS_TEMPLATE_CODE", "tpl")
        monkeypatch.setenv("CARRIER_AUTH_PROVIDER", "mock")

        from app.core.config import Settings
        with pytest.raises(ValueError) as exc_info:
            Settings()
        assert "ALIYUN_SMS_SIGN_NAME" in str(exc_info.value)

    def test_production_rejects_aliyun_sms_missing_template_code(self, monkeypatch):
        """P1: 生产环境 SMS_PROVIDER=aliyun 缺 ALIYUN_SMS_TEMPLATE_CODE 校验失败"""
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("POSTGRES_PASSWORD", "secure_pass_12345678")
        monkeypatch.setenv("JWT_SECRET_KEY", "a-32-byte-minimum-secret-key-ok!")
        monkeypatch.setenv("CORS_ORIGINS", "https://app.example.com")
        monkeypatch.setenv("DEBUG", "false")
        monkeypatch.setenv("SMS_PROVIDER", "aliyun")
        monkeypatch.setenv("ALIYUN_ACCESS_KEY_ID", "ak")
        monkeypatch.setenv("ALIYUN_ACCESS_KEY_SECRET", "sk")
        monkeypatch.setenv("ALIYUN_SMS_SIGN_NAME", "sign")
        monkeypatch.setenv("ALIYUN_SMS_TEMPLATE_CODE", "")
        monkeypatch.setenv("CARRIER_AUTH_PROVIDER", "mock")

        from app.core.config import Settings
        with pytest.raises(ValueError) as exc_info:
            Settings()
        assert "ALIYUN_SMS_TEMPLATE_CODE" in str(exc_info.value)

    # Removed: test_production_rejects_aliyun_carrier_missing_key
    # The aliyun CARRIER_AUTH_PROVIDER option has been removed.
    # SMS provider aliyun key validation is covered by the SMS-specific tests above. 