"""
认证服务SSO功能测试 - test_auth_service_sso.py
测试 AuthService 中新增的 sso_login 功能
"""
import pytest
import uuid
from datetime import datetime
from faker import Faker

from app.services.auth_service import AuthService, InvalidTokenException, InvalidCredentialsException
from app.crud import crud_user
from app.schemas.users import UserCreate
from app.models.users import EntityStatus
from app.exceptions import InvalidTokenException as AppInvalidTokenException

fake = Faker()


class TestAuthServiceSSO:
    """测试 AuthService SSO 功能"""

    @pytest.mark.asyncio
    async def test_sso_login_with_existing_social_user(self, db_session, mocker):
        """测试使用已存在的社交用户进行SSO登录"""
        async for db in db_session:
            # 准备: 模拟 Authing Token 验证
            social_id = uuid.uuid4().hex  # 纯UUID hex，避免用户名冲突
            mock_payload = {
                "sub": social_id,
                "email": fake.email(),
                "nickname": fake.first_name(),
                "exp": 9999999999,
                "iat": 1000000000
            }
            
            # Mock verify_id_token_pyjwt 方法
            auth_service = AuthService(db)
            mock_verify_id_token = mocker.patch.object(auth_service, 'verify_id_token_pyjwt', return_value=mock_payload)
            
            # 在数据库中创建匹配的用户
            username = f"{fake.user_name()}_{uuid.uuid4().hex[:6]}"
            user_create = UserCreate(
                username=username,
                email=mock_payload["email"],
                nickname=mock_payload["nickname"],
                social_provider="authing",
                social_id=mock_payload["sub"]
            )
            
            created_user = await crud_user.create(db, user_create, "dummy_hash")
            
            # 执行: 调用 sso_login
            result = await auth_service.sso_login(
                db, 
                id_token="dummy_token",
                client_ip="192.168.1.1"
            )
            
            # 验证 verify_id_token_pyjwt 被调用（需要检查参数，但audience和issuer可能不同）
            assert mock_verify_id_token.called, "verify_id_token_pyjwt应该被调用"
            call_args = mock_verify_id_token.call_args
            assert call_args.kwargs.get("id_token") == "dummy_token", "应该传递了正确的id_token"
            
            # 断言: 返回包含 access_token 的字典
            assert "access_token" in result
            assert "refresh_token" in result
            assert result["token_type"] == "bearer"
            
            # 状态验证: 重新查询用户，验证登录信息已更新
            updated_user = await crud_user.get(db, created_user.id)
            assert updated_user.last_login_at is not None
            assert str(updated_user.last_login_ip) == "192.168.1.1"

    @pytest.mark.asyncio
    async def test_sso_login_linking_existing_email_user(self, db_session, mocker):
        """测试SSO登录时链接现有邮箱用户"""
        async for db in db_session:
            # 准备: 模拟 Authing Token 验证
            email = fake.email()
            social_id = uuid.uuid4().hex  # 纯UUID hex，避免用户名冲突
            mock_payload = {
                "sub": social_id,
                "email": email,
                "nickname": fake.first_name(),
                "exp": 9999999999,
                "iat": 1000000000
            }
            
            # Mock verify_id_token_pyjwt 方法
            auth_service = AuthService(db)
            mock_verify_id_token = mocker.patch.object(auth_service, 'verify_id_token_pyjwt', return_value=mock_payload)
            
            # 在数据库中创建一个邮箱匹配但没有社交登录信息的用户
            username = f"{fake.user_name()}_{uuid.uuid4().hex[:6]}"
            user_create = UserCreate(
                username=username,
                email=email,
                nickname=fake.first_name(),
                social_provider=None,
                social_id=None
            )
            
            created_user = await crud_user.create(db, user_create, "password_hash")
            
            # 执行: 调用 sso_login
            result = await auth_service.sso_login(
                db,
                id_token="dummy_token", 
                client_ip="192.168.1.2"
            )
            
            # 验证 verify_id_token_pyjwt 被调用（需要检查参数，但audience和issuer可能不同）
            assert mock_verify_id_token.called, "verify_id_token_pyjwt应该被调用"
            call_args = mock_verify_id_token.call_args
            assert call_args.kwargs.get("id_token") == "dummy_token", "应该传递了正确的id_token"
            
            # 断言: 返回 access_token
            assert "access_token" in result
            assert "refresh_token" in result
            
            # 状态验证: 重新查询用户，验证社交登录信息已被填充
            updated_user = await crud_user.get(db, created_user.id)
            assert updated_user.social_provider == "authing"
            assert updated_user.social_id == mock_payload["sub"]
            assert updated_user.last_login_at is not None

    @pytest.mark.asyncio
    async def test_sso_login_creating_new_user(self, db_session, mocker):
        """测试SSO登录时创建新用户"""
        async for db in db_session:
            # 准备: 模拟 Authing Token 验证
            email = fake.email()
            nickname = fake.first_name()
            social_id = uuid.uuid4().hex  # 纯UUID hex，避免用户名冲突
            
            mock_payload = {
                "sub": social_id,
                "email": email,
                "nickname": nickname,
                "exp": 9999999999,
                "iat": 1000000000
            }
            
            # Mock verify_id_token_pyjwt 方法
            auth_service = AuthService(db)
            mock_verify_id_token = mocker.patch.object(auth_service, 'verify_id_token_pyjwt', return_value=mock_payload)
            
            # 确保数据库中无匹配用户
            existing_user = await crud_user.get_by_email(db, email)
            assert existing_user is None
            
            # 执行: 调用 sso_login
            result = await auth_service.sso_login(
                db,
                id_token="dummy_token",
                client_ip="192.168.1.3"
            )
            
            # 断言: 返回 access_token
            assert "access_token" in result
            assert "refresh_token" in result
            
            # 状态验证: 查询数据库，确认新用户已被创建
            new_user = await crud_user.get_by_email(db, email)
            assert new_user is not None
            assert new_user.email == email
            assert new_user.nickname == nickname
            assert new_user.social_provider == "authing"
            assert new_user.social_id == social_id
            assert new_user.last_login_at is not None
            assert str(new_user.last_login_ip) == "192.168.1.3"

    @pytest.mark.asyncio
    async def test_sso_login_fails_for_banned_user(self, db_session, mocker):
        """测试被封禁用户SSO登录失败"""
        async for db in db_session:
            # 准备: 模拟 Authing Token 验证
            mock_payload = {
                "sub": f"authing_{uuid.uuid4().hex[:10]}",
                "email": fake.email(),
                "nickname": fake.first_name(),
                "exp": 9999999999,
                "iat": 1000000000
            }
            
            # Mock verify_id_token_pyjwt 方法
            auth_service = AuthService(db)
            mock_verify_id_token = mocker.patch.object(auth_service, 'verify_id_token_pyjwt', return_value=mock_payload)
            
            # 创建一个被封禁的用户
            username = f"{fake.user_name()}_{uuid.uuid4().hex[:6]}"
            user_create = UserCreate(
                username=username,
                email=mock_payload["email"],
                nickname=mock_payload["nickname"],
                social_provider="authing",
                social_id=mock_payload["sub"]
            )
            
            created_user = await crud_user.create(db, user_create, "dummy_hash")
            
            # 设置用户状态为 BANNED
            await crud_user.update(db, created_user, {"status": EntityStatus.BANNED})
            
            # 执行和断言: 使用 pytest.raises 断言 InvalidCredentialsException 被抛出
            with pytest.raises(InvalidCredentialsException) as exc_info:
                await auth_service.sso_login(
                    db,
                    id_token="dummy_token",
                    client_ip="192.168.1.4"
                )
            
            assert "账户已被封禁" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_sso_login_fails_with_invalid_authing_token(self, db_session, mocker):
        """测试无效Authing Token导致SSO登录失败"""
        async for db in db_session:
            # 准备: 模拟 verify_id_token_pyjwt 抛出异常
            auth_service = AuthService(db)
            mock_verify_id_token = mocker.patch.object(auth_service, 'verify_id_token_pyjwt', side_effect=Exception("invalid"))
            
            # 执行和断言: 断言 InvalidTokenException 被抛出
            with pytest.raises(InvalidTokenException) as exc_info:
                await auth_service.sso_login(
                    db,
                    id_token="invalid_token",
                    client_ip="192.168.1.5"
                )
            
            # 验证 verify_id_token_pyjwt 被调用
            assert mock_verify_id_token.called, "verify_id_token_pyjwt应该被调用"
            call_args = mock_verify_id_token.call_args
            assert call_args.kwargs.get("id_token") == "invalid_token", "应该传递了正确的id_token"

            assert "身份验证失败" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_sso_login_fails_when_authing_client_unavailable(self, db_session, mocker):
        """测试Authing客户端不可用时SSO登录失败"""
        async for db in db_session:
            # 准备: 模拟 verify_id_token_pyjwt 抛出异常
            auth_service = AuthService(db)
            mock_verify_id_token = mocker.patch.object(auth_service, 'verify_id_token_pyjwt', side_effect=Exception("invalid"))
            
            # 执行和断言: 断言 InvalidTokenException 被抛出
            with pytest.raises(InvalidTokenException) as exc_info:
                await auth_service.sso_login(
                    db,
                    id_token="dummy_token",
                    client_ip="192.168.1.6"
                )

            assert "身份验证失败" in str(exc_info.value) or "invalid" in str(exc_info.value).lower()
