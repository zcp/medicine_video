"""
用户服务新功能测试 - test_user_service_new.py
测试 UserService 的手机号绑定逻辑和增强的密码验证
"""
import pytest
import uuid
from faker import Faker

from app.services.user_service import UserService, ValidationError
from app.crud import crud_user
from app.schemas.users import UserCreate
from app.models.users import User

fake = Faker()


class TestUserServiceNew:
    """测试 UserService 新增功能"""

    @pytest.mark.asyncio
    async def test_bind_phone_number_success(self, db_session, mocker):
        """测试手机号绑定成功"""
        async for db in db_session:
            # 准备: 创建一个用户
            username = f"{fake.user_name()}_{uuid.uuid4().hex[:6]}"
            email = fake.email()
            user_create = UserCreate(
                username=username,
                email=email,
                nickname=fake.first_name()
            )
            
            created_user = await crud_user.create(db, user_create, "dummy_hash")
            
            # 模拟 Redis 操作
            phone_number = f"+86{fake.random_int(min=13000000000, max=19999999999)}"
            verification_code = "123456"
            
            mock_redis_client = mocker.AsyncMock()
            mock_redis_client.get.return_value = verification_code
            mock_redis_client.delete.return_value = True
            
            # 创建 UserService 实例并模拟 redis_client
            user_service = UserService(db)
            user_service.redis_client = mock_redis_client
            
            # 执行: 调用 bind_phone_number
            await user_service.bind_phone_number(
                db,
                current_user=created_user,
                phone_number=phone_number,
                verification_code=verification_code
            )
            
            # 断言: redis_client.delete 被调用一次
            mock_redis_client.delete.assert_called_once_with(f"otp:BIND_PHONE:{phone_number}")
            
            # 状态验证: 重新查询用户，验证手机号已更新
            updated_user = await crud_user.get(db, created_user.id)
            assert updated_user.phone_number == phone_number
            assert updated_user.is_phone_verified is True

    @pytest.mark.asyncio
    async def test_bind_phone_number_fails_with_wrong_code(self, db_session, mocker):
        """测试验证码错误导致手机号绑定失败"""
        async for db in db_session:
            # 准备: 创建用户
            username = f"{fake.user_name()}_{uuid.uuid4().hex[:6]}"
            email = fake.email()
            user_create = UserCreate(
                username=username,
                email=email,
                nickname=fake.first_name()
            )
            
            created_user = await crud_user.create(db, user_create, "dummy_hash")
            
            # 模拟 Redis 返回 None 或错误的验证码
            phone_number = f"+86{fake.random_int(min=13000000000, max=19999999999)}"
            
            mock_redis_client = mocker.AsyncMock()
            mock_redis_client.get.return_value = None  # 模拟验证码不存在
            
            user_service = UserService(db)
            user_service.redis_client = mock_redis_client
            
            # 执行和断言: 断言 ValidationError 被抛出
            with pytest.raises(ValidationError) as exc_info:
                await user_service.bind_phone_number(
                    db,
                    current_user=created_user,
                    phone_number=phone_number,
                    verification_code="wrong_code"
                )
            
            assert "手机验证码错误或已过期" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_bind_phone_number_fails_when_phone_is_taken(self, db_session, mocker):
        """测试手机号已被占用导致绑定失败"""
        async for db in db_session:
            # 准备: 创建两个用户
            username1 = f"{fake.user_name()}_{uuid.uuid4().hex[:6]}"
            email1 = fake.email()
            phone_number = f"+86{fake.random_int(min=13000000000, max=19999999999)}"
            
            user_create1 = UserCreate(
                username=username1,
                email=email1,
                nickname=fake.first_name(),
                #phone_number=phone_number
            )
            
            user1 = await crud_user.create(db, user_create1, "dummy_hash")
            
            username2 = f"{fake.user_name()}_{uuid.uuid4().hex[:6]}"
            email2 = fake.email()
            user_create2 = UserCreate(
                username=username2,
                email=email2,
                nickname=fake.first_name()
            )
            
            user2 = await crud_user.create(db, user_create2, "dummy_hash")
            
            # 模拟 Redis 返回正确的验证码
            verification_code = "123456"
            mock_redis_client = mocker.AsyncMock()
            mock_redis_client.get.return_value = verification_code
            
            user_service = UserService(db)
            user_service.redis_client = mock_redis_client

            await user_service.bind_phone_number(
                    db,
                    current_user=user1,
                    phone_number=phone_number,
                    verification_code=verification_code
            )

            # 执行和断言: 第二个用户尝试绑定已被占用的手机号
            with pytest.raises(ValidationError) as exc_info:
                await user_service.bind_phone_number(
                    db,
                    current_user=user2,
                    phone_number=phone_number,
                    verification_code=verification_code
                )
            
            assert "该手机号已被其他账号绑定" in str(exc_info.value)

    @pytest.mark.parametrize("password,expected", [
        # 强密码：包含大小写、数字、特殊字符且长度足够
        ("Password123!", True),
        ("MyStr0ng@Pass", True),
        ("Complex1#Pass", True),
        # 弱密码：缺少大写字母
        ("password123!", False),
        # 弱密码：缺少小写字母
        ("PASSWORD123!", False),
        # 弱密码：缺少数字
        ("Password!", False),
        # 弱密码：缺少特殊字符
        ("Password123", False),
        # 弱密码：长度不足
        ("Pass1!", False),
        # 弱密码：只有字母
        ("Password", False),
        # 弱密码：只有数字
        ("12345678", False),
    ])
    @pytest.mark.asyncio
    async def test_password_strength_validation(self, db_session, password, expected):
        """测试密码强度验证"""
        async for db in db_session:
            # 准备: 创建 UserService 实例
            user_service = UserService(db)
            
            # 执行: 调用 _validate_password_strength
            result = user_service._validate_password_strength(password)
            
            # 断言: 验证结果符合预期
            assert result == expected

    @pytest.mark.asyncio
    async def test_register_user_with_weak_password_fails(self, db_session, mocker):
        """测试使用弱密码注册用户失败"""
        async for db in db_session:
            # 准备: 模拟验证码验证成功
            mock_redis_client = mocker.AsyncMock()
            mock_redis_client.get.return_value = "captcha_solution"
            mock_redis_client.delete.return_value = True
            
            user_service = UserService(db)
            user_service.redis_client = mock_redis_client
            
            # 创建注册请求对象
            register_request = mocker.Mock()
            register_request.username = f"{fake.user_name()}_{uuid.uuid4().hex[:8]}"
            register_request.email = fake.email()
            register_request.nickname = fake.first_name()
            register_request.password = "weak"  # 弱密码
            register_request.captcha_id = "dummy_captcha_id"
            register_request.captcha_solution = "captcha_solution"
            register_request.agreed_to_terms = True
            
            # 执行和断言: 使用弱密码注册应该失败
            with pytest.raises(ValidationError) as exc_info:
                await user_service.register_user(register_request)

            error_msg = str(exc_info.value)

            assert "密码必须至少8位" in error_msg
            assert "大写字母" in error_msg
            assert "小写字母" in error_msg
            assert "数字" in error_msg
            assert "特殊字符" in error_msg

    @pytest.mark.asyncio
    async def test_bind_phone_number_code_is_destroyed_after_use(self, db_session, mocker):
        """测试验证码在使用后被销毁"""
        async for db in db_session:
            # 准备: 创建用户
            username = f"{fake.user_name()}_{uuid.uuid4().hex[:6]}"
            email = fake.email()
            user_create = UserCreate(
                username=username,
                email=email,
                nickname=fake.first_name()
            )
            
            created_user = await crud_user.create(db, user_create, "dummy_hash")
            
            # 模拟 Redis 操作
            phone_number = f"+86{fake.random_int(min=13000000000, max=19999999999)}"
            verification_code = "123456"
            
            mock_redis_client = mocker.AsyncMock()
            mock_redis_client.get.return_value = verification_code
            mock_redis_client.delete.return_value = True
            
            user_service = UserService(db)
            user_service.redis_client = mock_redis_client
            
            # 执行: 绑定手机号
            await user_service.bind_phone_number(
                db,
                current_user=created_user,
                phone_number=phone_number,
                verification_code=verification_code
            )
            
            # 断言: 验证码立即被删除（确保只能使用一次）
            expected_redis_key = f"otp:BIND_PHONE:{phone_number}"
            mock_redis_client.get.assert_called_once_with(expected_redis_key)
            mock_redis_client.delete.assert_called_once_with(expected_redis_key)
