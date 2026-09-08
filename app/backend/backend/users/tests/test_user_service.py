"""
用户服务层单元测试 - test_user_service.py
对 app/services/user_service.py 中的 UserService 类进行详细的、隔离的单元测试。
使用 mocker fixture 模拟所有外部依赖。
"""

import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock
from faker import Faker

from app.services.user_service import (
    UserService,
    UsernameAlreadyExistsError,
    EmailAlreadyExistsError,
    InvalidPasswordError,
    WeakPasswordError,
    NoUpdateDataProvidedError,
    ActiveSubscriptionError,
    CaptchaErrorException,
    ValidationError
)
from app.schemas.users import UserCreate, UserUpdateSelf
from app.models.users import User

fake = Faker()


class TestUserService:
    """UserService 测试类"""

    @pytest.fixture
    def mock_db_session(self):
        """Mock 数据库会话"""
        return AsyncMock()

    @pytest.fixture
    def mock_redis_client(self):
        """Mock Redis 客户端"""
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock()
        mock_redis.set = AsyncMock()
        mock_redis.delete = AsyncMock()
        return mock_redis

    @pytest.fixture
    def user_service(self, mock_db_session, mock_redis_client):
        """创建 UserService 实例"""
        return UserService(db=mock_db_session, redis_client=mock_redis_client)

    @pytest.fixture
    def mock_user(self):
        """Mock 用户对象"""
        user = MagicMock()
        user.id = 1
        user.public_id = uuid.uuid4()
        user.username = fake.user_name()
        user.email = fake.email()
        user.nickname = fake.name()
        user.password_hash = "old_hashed_password"
        return user

    @pytest.fixture
    def register_request(self):
        """创建注册请求对象"""
        class RegisterRequest:
            def __init__(self):
                self.username = fake.user_name() + str(uuid.uuid4().hex[:8])
                self.email = fake.email()
                self.password = "StrongPassword123!"  # 使用符合强度要求的密码
                self.nickname = fake.name()
                self.captcha_id = str(uuid.uuid4())
                self.captcha_solution = "12345"
        
        return RegisterRequest()

    @pytest.fixture
    def update_request(self):
        """创建更新请求对象"""
        class UpdateRequest:
            def __init__(self):
                self.nickname = fake.name()
                self.avatar_url = fake.url()
                self.bio = fake.text(max_nb_chars=100)
            
            def model_dump(self, exclude_unset=False):
                return {
                    "nickname": self.nickname,
                    "avatar_url": self.avatar_url,
                    "bio": self.bio
                }
        
        return UpdateRequest()

    @pytest.fixture
    def password_request(self):
        """创建密码修改请求对象"""
        class PasswordRequest:
            def __init__(self):
                self.current_password = "old_password"
                self.new_password = fake.password(length=8)
        
        return PasswordRequest()

    # ========================================================================
    # 用户注册测试
    # ========================================================================

    @pytest.mark.asyncio
    async def test_register_user_success(self, user_service, register_request, mocker):
        """测试用户注册成功"""
        # Arrange
        mock_verify_captcha = mocker.patch.object(user_service, '_verify_captcha', return_value=True)
        mock_crud_get_by_username = mocker.patch('app.crud.crud_user.get_by_username', return_value=None)
        mock_crud_get_by_email = mocker.patch('app.crud.crud_user.get_by_email', return_value=None)
        mock_hash_password = mocker.patch.object(user_service, '_hash_password', return_value='hashed_password')
        
        # 创建模拟的新用户对象
        mock_new_user = MagicMock()
        mock_new_user.id = 1
        mock_new_user.username = register_request.username
        mock_new_user.email = register_request.email
        mock_new_user.nickname = register_request.nickname
        
        mock_crud_create = mocker.patch('app.crud.crud_user.create', return_value=mock_new_user)

        # Act
        result = await user_service.register_user(register_request)

        # Assert
        mock_verify_captcha.assert_called_once_with(register_request.captcha_id, register_request.captcha_solution)
        mock_crud_get_by_username.assert_called_once_with(user_service.db, register_request.username)
        mock_crud_get_by_email.assert_called_once_with(user_service.db, register_request.email)
        mock_hash_password.assert_called_once_with(register_request.password)
        mock_crud_create.assert_called_once()
        
        # 验证数据库字段
        call_args = mock_crud_create.call_args
        user_in = call_args[0][1]  # 第二个参数是 user_in
        password_hash = call_args[0][2]  # 第三个参数是 password_hash
        
        assert user_in.username == register_request.username
        assert user_in.email == register_request.email
        assert user_in.nickname == register_request.nickname
        assert password_hash == 'hashed_password'
        
        assert result == mock_new_user

    @pytest.mark.asyncio
    async def test_register_user_fails_if_username_exists(self, user_service, register_request, mock_user, mocker):
        """测试用户名已存在时注册失败"""
        # Arrange
        mocker.patch.object(user_service, '_verify_captcha', return_value=True)
        mocker.patch('app.crud.crud_user.get_by_username', return_value=mock_user)

        # Act & Assert
        with pytest.raises(UsernameAlreadyExistsError):
            await user_service.register_user(register_request)

    @pytest.mark.asyncio
    async def test_register_user_fails_if_email_exists(self, user_service, register_request, mock_user, mocker):
        """测试邮箱已存在时注册失败"""
        # Arrange
        mocker.patch.object(user_service, '_verify_captcha', return_value=True)
        mocker.patch('app.crud.crud_user.get_by_username', return_value=None)
        mocker.patch('app.crud.crud_user.get_by_email', return_value=mock_user)

        # Act & Assert
        with pytest.raises(EmailAlreadyExistsError):
            await user_service.register_user(register_request)

    @pytest.mark.asyncio
    async def test_register_user_fails_if_captcha_is_wrong(self, user_service, register_request, mocker):
        """测试验证码错误时注册失败"""
        # Arrange
        mocker.patch.object(user_service, '_verify_captcha', return_value=False)

        # Act & Assert
        with pytest.raises(CaptchaErrorException):
            await user_service.register_user(register_request)

    @pytest.mark.asyncio
    async def test_register_user_fails_if_username_invalid(self, user_service, register_request, mocker):
        """测试用户名格式无效时注册失败"""
        # Arrange
        register_request.username = "ab"  # 长度不足
        mocker.patch.object(user_service, '_verify_captcha', return_value=True)

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            await user_service.register_user(register_request)
        
        assert exc_info.value.field == "username"

    @pytest.mark.asyncio
    async def test_register_user_fails_if_email_invalid(self, user_service, register_request, mocker):
        """测试邮箱格式无效时注册失败"""
        # Arrange
        register_request.email = "invalid_email"
        mocker.patch.object(user_service, '_verify_captcha', return_value=True)

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            await user_service.register_user(register_request)
        
        assert exc_info.value.field == "email"

    @pytest.mark.asyncio
    async def test_register_user_fails_if_password_too_short(self, user_service, register_request, mocker):
        """测试密码过短时注册失败"""
        # Arrange
        register_request.password = "12345"  # 长度不足
        mocker.patch.object(user_service, '_verify_captcha', return_value=True)

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            await user_service.register_user(register_request)
        
        assert exc_info.value.field == "password"

    # ========================================================================
    # 用户资料更新测试
    # ========================================================================

    @pytest.mark.asyncio
    async def test_update_profile_success(self, user_service, mock_user, update_request, mocker):
        """测试更新用户资料成功"""
        # Arrange
        updated_user = MagicMock()
        updated_user.id = mock_user.id
        updated_user.nickname = update_request.nickname
        
        mock_crud_update = mocker.patch('app.crud.crud_user.update', return_value=updated_user)

        # Act
        result = await user_service.update_profile(mock_user, update_request)

        # Assert
        mock_crud_update.assert_called_once()
        call_args = mock_crud_update.call_args
        
        # 检查传递给 crud_user.update 的参数
        assert call_args[0][0] == user_service.db  # 第一个参数是 db
        assert call_args[0][1] == mock_user  # 第二个参数是 user_to_update
        
        obj_in = call_args[0][2]  # 第三个参数是 obj_in (update_data)
        assert isinstance(obj_in, dict)
        assert obj_in['nickname'] == update_request.nickname
        
        assert result == updated_user

    @pytest.mark.asyncio
    async def test_update_profile_fails_if_no_data_provided(self, user_service, mock_user, mocker):
        """测试没有提供更新数据时失败"""
        # Arrange
        empty_request = MagicMock()
        empty_request.model_dump.return_value = {}

        # Act & Assert
        with pytest.raises(NoUpdateDataProvidedError):
            await user_service.update_profile(mock_user, empty_request)

    @pytest.mark.asyncio
    async def test_update_profile_fails_if_nickname_too_long(self, user_service, mock_user, mocker):
        """测试昵称过长时更新失败"""
        # Arrange
        long_nickname_request = MagicMock()
        long_nickname_request.model_dump.return_value = {"nickname": "a" * 51}  # 超过50个字符

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            await user_service.update_profile(mock_user, long_nickname_request)
        
        assert exc_info.value.field == "nickname"

    # ========================================================================
    # 密码修改测试
    # ========================================================================

    @pytest.mark.asyncio
    async def test_change_password_success(self, user_service, mock_user, password_request, mocker):
        """测试修改密码成功"""
        # Arrange
        mock_verify_password = mocker.patch.object(user_service, '_verify_password')
        mock_verify_password.side_effect = lambda pwd, hash_val: pwd == 'old_password' and hash_val == 'old_hashed_password'

        mock_validate_password_strength = mocker.patch.object(user_service, '_validate_password_strength',
                                                              return_value=True)
        mock_hash_password = mocker.patch.object(user_service, '_hash_password', return_value='new_hashed_password')
        mock_crud_update = mocker.patch('app.crud.crud_user.update')
        mock_blacklist_tokens = mocker.patch.object(user_service, '_blacklist_user_tokens')

        # Act
        await user_service.change_password(mock_user, password_request)

        # Assert
        # 验证 _verify_password 被调用了两次
        assert mock_verify_password.call_count == 2

        # 检查第一次调用（验证当前密码）
        first_call = mock_verify_password.call_args_list[0]
        assert first_call.args == ('old_password', 'old_hashed_password')

        # 检查第二次调用（检查新旧密码是否相同）
        second_call = mock_verify_password.call_args_list[1]
        assert second_call.args == (password_request.new_password, 'old_hashed_password')

        mock_validate_password_strength.assert_called_once_with(password_request.new_password)
        mock_hash_password.assert_called_once_with(password_request.new_password)
        mock_crud_update.assert_called_once()

        # 检查传递给 crud_user.update 的参数
        call_args = mock_crud_update.call_args
        obj_in = call_args[0][2]  # 第三个参数是 obj_in
        assert obj_in['password_hash'] == 'new_hashed_password'

        mock_blacklist_tokens.assert_called_once_with(mock_user)

    @pytest.mark.asyncio
    async def test_change_password_fails_if_current_password_is_wrong(self, user_service, mock_user, password_request, mocker):
        """测试当前密码错误时修改失败"""
        # Arrange
        mocker.patch.object(user_service, '_verify_password', return_value=False)

        # Act & Assert
        with pytest.raises(InvalidPasswordError):
            await user_service.change_password(mock_user, password_request)

    @pytest.mark.asyncio
    async def test_change_password_fails_if_new_password_is_weak(self, user_service, mock_user, password_request, mocker):
        """测试新密码强度不足时修改失败"""
        # Arrange
        # 第一次调用（current_password 验证）返回 True
        # 第二次调用（新旧密码比对）返回 False（确保不会卡在"新旧密码相同"检查）
        mocker.patch.object(user_service, '_verify_password', side_effect=[True, False])
        mocker.patch.object(user_service, '_validate_password_strength', return_value=False)

        # Act & Assert
        with pytest.raises(WeakPasswordError):
            await user_service.change_password(mock_user, password_request)

    @pytest.mark.asyncio
    async def test_change_password_fails_if_new_password_same_as_current(self, user_service, mock_user, password_request, mocker):
        """测试新密码与当前密码相同时修改失败"""
        # Arrange
        password_request.new_password = "old_password"  # 新密码与旧密码相同
        
        mock_verify_password = mocker.patch.object(user_service, '_verify_password', return_value=True)
        mocker.patch.object(user_service, '_validate_password_strength', return_value=True)

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            await user_service.change_password(mock_user, password_request)
        
        assert exc_info.value.field == "new_password"

    @pytest.mark.asyncio
    async def test_change_password_allows_passwordless_user_to_set_password(self, user_service, mock_user, password_request, mocker):
        """Passwordless users can set an initial password without current_password."""
        # Arrange
        mock_user.password_hash = None
        password_request.current_password = None
        password_request.new_password = "StrongP@ssw0rd!"
        mock_verify_password = mocker.patch.object(user_service, '_verify_password', return_value=False)
        mock_validate_password_strength = mocker.patch.object(user_service, '_validate_password_strength', return_value=True)
        mock_hash_password = mocker.patch.object(user_service, '_hash_password', return_value='new_hashed_password')
        mock_crud_update = mocker.patch('app.crud.crud_user.update')
        mock_blacklist_tokens = mocker.patch.object(user_service, '_blacklist_user_tokens')

        # Act
        await user_service.change_password(mock_user, password_request)

        # Assert
        mock_verify_password.assert_not_called()
        mock_validate_password_strength.assert_called_once_with(password_request.new_password)
        mock_hash_password.assert_called_once_with(password_request.new_password)
        mock_crud_update.assert_called_once()
        obj_in = mock_crud_update.call_args[0][2]
        assert obj_in['password_hash'] == 'new_hashed_password'
        mock_blacklist_tokens.assert_called_once_with(mock_user)

    @pytest.mark.asyncio
    async def test_change_password_requires_current_password_for_existing_password_user(self, user_service, mock_user, password_request, mocker):
        """Users with a password must provide current_password."""
        # Arrange
        password_request.current_password = None
        mock_verify_password = mocker.patch.object(user_service, '_verify_password')
        mock_crud_update = mocker.patch('app.crud.crud_user.update')

        # Act & Assert
        with pytest.raises(InvalidPasswordError):
            await user_service.change_password(mock_user, password_request)

        mock_verify_password.assert_not_called()
        mock_crud_update.assert_not_called()

    @pytest.mark.asyncio
    async def test_bind_phone_number_consumes_ticket_and_updates_user(self, user_service, mock_db_session, mock_user, mocker):
        """Phone binding consumes a BIND_PHONE ticket and updates the current user."""
        # Arrange
        phone_number = "+8613812345678"
        bind_ticket = "ticket_123"
        mock_auth_service = mocker.patch('app.services.auth_service.AuthService')
        mock_auth_service.return_value.consume_ticket = AsyncMock(
            return_value={"recipient": phone_number}
        )
        mock_get_by_phone = mocker.patch('app.crud.crud_user.get_by_phone_number', return_value=None)

        # Act
        await user_service.bind_phone_number(
            mock_db_session,
            current_user=mock_user,
            phone_number=phone_number,
            bind_ticket=bind_ticket,
        )

        # Assert
        mock_auth_service.return_value.consume_ticket.assert_awaited_once_with("BIND_PHONE", bind_ticket)
        mock_get_by_phone.assert_awaited_once_with(mock_db_session, phone_number=phone_number)
        assert mock_user.phone_number == phone_number
        assert mock_user.is_phone_verified is True
        mock_db_session.add.assert_called_once_with(mock_user)
        mock_db_session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_bind_phone_number_fails_if_ticket_phone_mismatch(self, user_service, mock_db_session, mock_user, mocker):
        """A BIND_PHONE ticket cannot be used for a different phone number."""
        # Arrange
        mock_auth_service = mocker.patch('app.services.auth_service.AuthService')
        mock_auth_service.return_value.consume_ticket = AsyncMock(
            return_value={"recipient": "+8613812345678"}
        )
        mock_get_by_phone = mocker.patch('app.crud.crud_user.get_by_phone_number')

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            await user_service.bind_phone_number(
                mock_db_session,
                current_user=mock_user,
                phone_number="+8613912345678",
                bind_ticket="ticket_123",
            )

        assert exc_info.value.field == "phone_number"
        mock_get_by_phone.assert_not_called()
        mock_db_session.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_bind_phone_number_fails_if_ticket_invalid(self, user_service, mock_db_session, mock_user, mocker):
        """Invalid BIND_PHONE tickets are surfaced as bind_ticket validation errors."""
        # Arrange
        from app.services.auth_service import InvalidTokenException

        mock_auth_service = mocker.patch('app.services.auth_service.AuthService')
        mock_auth_service.return_value.consume_ticket = AsyncMock(side_effect=InvalidTokenException())

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            await user_service.bind_phone_number(
                mock_db_session,
                current_user=mock_user,
                phone_number="+8613812345678",
                bind_ticket="bad_ticket",
            )

        assert exc_info.value.field == "bind_ticket"
        mock_db_session.commit.assert_not_called()

    # ========================================================================
    # 账户注销测试
    # ========================================================================

    @pytest.mark.asyncio
    async def test_deactivate_account_success(self, user_service, mock_user, mocker):
        """测试注销账户成功"""
        # Arrange
        deleted_user = MagicMock()
        deleted_user.id = mock_user.id
        
        mock_verify_captcha = mocker.patch.object(user_service, '_verify_captcha', return_value=True)
        mock_crud_remove = mocker.patch('app.crud.crud_user.remove', return_value=deleted_user)
        mock_blacklist_tokens = mocker.patch.object(user_service, '_blacklist_user_tokens')

        # Act
        await user_service.deactivate_account(mock_user, captcha_id="captcha-1", captcha_solution="1234")

        # Assert
        mock_verify_captcha.assert_called_once_with("captcha-1", "1234")
        mock_crud_remove.assert_called_once_with(user_service.db, mock_user.id)
        mock_blacklist_tokens.assert_called_once_with(mock_user)

    @pytest.mark.asyncio
    async def test_deactivate_account_fails_if_captcha_invalid(self, user_service, mock_user, mocker):
        """测试验证码错误时注销失败"""
        from app.services.user_service import CaptchaErrorException

        mock_verify_captcha = mocker.patch.object(user_service, '_verify_captcha', return_value=False)
        mock_crud_remove = mocker.patch('app.crud.crud_user.remove')

        with pytest.raises(CaptchaErrorException):
            await user_service.deactivate_account(mock_user, captcha_id="captcha-1", captcha_solution="wrong")

        mock_verify_captcha.assert_called_once_with("captcha-1", "wrong")
        mock_crud_remove.assert_not_called()

    # ========================================================================
    # 内部工具方法测试
    # ========================================================================

    def test_hash_password(self, user_service):
        """测试密码哈希"""
        password = "test_password"
        hashed = user_service._hash_password(password)
        
        assert isinstance(hashed, str)
        # bcrypt 哈希特征：以 $2b$ 开头，长度 60
        assert hashed.startswith("$2b$"), f"期望 bcrypt 格式，实际: {hashed[:10]}"
        assert len(hashed) == 60, f"bcrypt 哈希长度应为 60，实际: {len(hashed)}"
        assert hashed != password

    def test_verify_password(self, user_service):
        """测试密码验证"""
        password = "test_password"
        correct_hash = user_service._hash_password(password)
        wrong_hash = "wrong_hash"
        
        assert user_service._verify_password(password, correct_hash) is True
        assert user_service._verify_password(password, wrong_hash) is False

    def test_validate_password_strength(self, user_service):
        """测试密码强度验证"""
        assert user_service._validate_password_strength("123456") is False
        assert user_service._validate_password_strength("12345") is False
        assert user_service._validate_password_strength("") is False
        strong_password = "StrongP@ssw0rd!"
        assert user_service._validate_password_strength(strong_password) is True

    def test_validate_username(self, user_service):
        """测试用户名验证"""
        assert user_service._validate_username("validuser123") is True
        assert user_service._validate_username("valid_user") is True
        assert user_service._validate_username("ab") is False  # 太短
        assert user_service._validate_username("a" * 51) is False  # 太长
        assert user_service._validate_username("user@name") is False  # 包含非法字符
        assert user_service._validate_username("") is False  # 空字符串

    def test_validate_email(self, user_service):
        """测试邮箱验证"""
        assert user_service._validate_email("test@example.com") is True
        assert user_service._validate_email("user.name@domain.co.uk") is True
        assert user_service._validate_email("invalid_email") is False  # 缺少@
        assert user_service._validate_email("test@domain") is False  # 缺少.
        assert user_service._validate_email("@domain.com") is False  # 缺少用户名
        assert user_service._validate_email("") is False  # 空字符串

    @pytest.mark.asyncio
    async def test_verify_captcha_success(self, user_service):
        """测试验证码校验成功"""
        # Arrange
        user_service.redis_client.get.return_value = "12345"

        # Act
        result = await user_service._verify_captcha("test-id", "12345")

        # Assert
        assert result is True
        user_service.redis_client.delete.assert_called_once_with("captcha:solution:test-id")

    @pytest.mark.asyncio
    async def test_verify_captcha_failure(self, user_service):
        """测试验证码校验失败"""
        # Arrange
        user_service.redis_client.get.return_value = "54321"

        # Act
        result = await user_service._verify_captcha("test-id", "12345")

        # Assert
        assert result is False
        user_service.redis_client.delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_verify_captcha_not_found(self, user_service):
        """测试验证码不存在时校验失败"""
        # Arrange
        user_service.redis_client.get.return_value = None

        # Act
        result = await user_service._verify_captcha("test-id", "12345")

        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_blacklist_user_tokens_success(self, user_service, mock_user):
        """测试吊销用户会话成功"""
        # Arrange
        user_public_id = str(mock_user.public_id)

        # Act
        await user_service._blacklist_user_tokens(mock_user)

        # Assert
        user_service.redis_client.set.assert_called_once()
        call_args = user_service.redis_client.set.call_args
        key = call_args[0][0]
        assert key == f"user_sessions_revoked:{user_public_id}"
        # value 应为 ISO 格式时间戳
        from datetime import datetime
        datetime.fromisoformat(call_args[0][1])
        assert call_args[1]["ex"] == 86400 * 7

    @pytest.mark.asyncio
    async def test_blacklist_user_tokens_handles_exception(self, user_service, mock_user, mocker):
        """测试吊销用户会话异常处理"""
        # Arrange
        user_service.redis_client.set.side_effect = Exception("Redis error")
        mock_logger = mocker.patch('app.services.user_service.logger')

        # Act
        await user_service._blacklist_user_tokens(mock_user)

        # Assert
        mock_logger.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_active_subscriptions(self, user_service):
        """测试检查活跃订阅（预留方法）"""
        # Act
        result = await user_service._check_active_subscriptions(123)

        # Assert
        assert result is False  # 目前总是返回 False

    # ========================================================================
    # 密码哈希升级测试（_upgrade_password_hash_if_needed）
    # ========================================================================

    @pytest.mark.asyncio
    async def test_upgrade_password_hash_legacy_sha256(self, user_service, mock_user, mocker):
        """旧 SHA-256 密码 → 升级为 bcrypt，commit 被调用"""
        # Arrange
        mock_user.password_hash = "a" * 64  # 64 位十六进制 = SHA-256 特征
        mocker.patch.object(user_service, '_hash_password', return_value='$2b$12$new_bcrypt_hash')

        # Act
        await user_service._upgrade_password_hash_if_needed(mock_user, 'my_password')

        # Assert
        assert mock_user.password_hash == '$2b$12$new_bcrypt_hash'
        user_service.db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_upgrade_password_hash_already_bcrypt(self, user_service, mock_user, mocker):
        """已是 bcrypt 密码 → 不升级，不 commit"""
        # Arrange
        mock_user.password_hash = '$2b$12$existing_bcrypt_hash'
        hash_spy = mocker.patch.object(user_service, '_hash_password', return_value='new_hash')

        # Act
        await user_service._upgrade_password_hash_if_needed(mock_user, 'my_password')

        # Assert
        hash_spy.assert_not_called()
        user_service.db.commit.assert_not_called() 
