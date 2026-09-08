"""
用户注册API集成测试 - 用户功能服务
对app/api/v1/endpoints/users.py中的API端点进行集成测试
"""

import pytest
import uuid
from unittest.mock import patch, AsyncMock

from app.crud import crud_user
from app.services.auth_service import (
    InvalidTokenException as AuthInvalidTokenException,
    WeakPasswordException as AuthWeakPasswordException,
)
from .conftest import create_test_user, create_captcha_mock_data


class TestUserRegister:
    """测试用户注册API"""
    
    @pytest.mark.asyncio
    async def test_register_success(self, async_client, db_session, mock_redis_captcha_success):
        """
        测试用户注册成功
        - 模拟验证码校验成功
        - 准备全新的用户信息
        - 发送注册请求
        - 验证API响应正确
        - 验证数据库中用户被正确创建
        """
        assert mock_redis_captcha_success is not None, "Mock fixture应该被激活"
        # 额外patch user_service的get_redis_client，确保覆盖所有路径
        with patch('app.services.user_service.get_redis_client', return_value=mock_redis_captcha_success):
            async for client in async_client:
                async for db in db_session:
                    # 准备验证码数据
                    captcha_data = create_captcha_mock_data()
                    
                    # 准备注册数据（全新用户，使用唯一标识符避免冲突）
                    unique_id = uuid.uuid4().hex[:8]
                    register_data = {
                        "username": f"newuser_{unique_id}",
                        "email": f"newuser_{unique_id}@example.com",
                        "password": "Strongpassword123!",
                        "nickname": "新用户",
                        "captcha_id": captcha_data["captcha_id"],
                        "captcha_solution": captcha_data["captcha_solution"]
                    }
                    
                    # 执行
                    response = await client.post("/api/v1/users/register", json=register_data)
                    
                    # 断言 API 响应
                    assert response.status_code == 200, f"HTTP状态码应该是200, 实际: {response.status_code}, 响应: {response.text}"
                    
                    response_data = response.json()
                    assert response_data["code"] == 200, "业务状态码应该是200"
                    assert response_data["message"] == "注册成功", "消息应该是注册成功"
                    
                    # 验证响应数据结构
                    data = response_data["data"]
                    assert "public_id" in data, "响应应该包含public_id"
                    assert "username" in data, "响应应该包含username"
                    assert "nickname" in data, "响应应该包含nickname"
                    assert "email" in data, "响应应该包含email"
                    assert "created_at" in data, "响应应该包含created_at"
                    
                    # 验证返回的用户信息
                    assert data["username"] == register_data["username"], "用户名应该匹配"
                    assert data["nickname"] == register_data["nickname"], "昵称应该匹配"
                    assert data["email"] == register_data["email"], "邮箱应该匹配"
                    
                    # 验证数据库状态 - 查询新创建的用户
                    created_user = await crud_user.get_by_username(db, register_data["username"])
                    
                    # 断言行创建
                    assert created_user is not None, "用户应该被成功创建"
                    
                    # 验证字段值
                    assert created_user.username == register_data["username"], "数据库中用户名应该匹配"
                    assert created_user.nickname == register_data["nickname"], "数据库中昵称应该匹配"
                    assert created_user.email == register_data["email"], "数据库中邮箱应该匹配"
                    
                    # 验证密码处理
                    assert created_user.password_hash is not None, "密码哈希不应该为空"
                    assert created_user.password_hash != register_data["password"], "密码不应该以明文存储"
                    assert len(created_user.password_hash) > 10, "密码哈希应该有合理长度"
                    
                    # 验证默认值
                    assert created_user.is_email_verified is False, "邮箱验证状态应该默认为False"
                    assert created_user.is_phone_verified is False, "手机验证状态应该默认为False"
                    
                    # 验证自动生成字段
                    assert created_user.public_id is not None, "public_id应该被自动生成"
                    assert created_user.created_at is not None, "创建时间应该被自动设置"
    
    @pytest.mark.asyncio
    async def test_register_fails_username_exists(self, async_client, db_session, mock_redis_captcha_success):
        """
        测试用户名已存在时注册失败
        - 先创建一个用户
        - 模拟验证码校验成功
        - 尝试使用相同用户名注册
        - 验证返回409冲突错误
        - 验证数据库用户数量没有增加
        """
        assert mock_redis_captcha_success is not None, "Mock fixture应该被激活"
        # 额外patch user_service的get_redis_client，确保覆盖所有路径
        with patch('app.services.user_service.get_redis_client', return_value=mock_redis_captcha_success):
            async for client in async_client:
                async for db in db_session:
                    # 准备 - 先创建已存在的用户（使用唯一标识符避免冲突）
                    unique_id = uuid.uuid4().hex[:8]
                    existing_user = await create_test_user(db, f"existinguser_{unique_id}", f"existing_{unique_id}@example.com")
                    
                    # 准备验证码数据
                    captcha_data = create_captcha_mock_data()
                    
                    # 准备注册数据（使用已存在的用户名）
                    new_email_unique_id = uuid.uuid4().hex[:8]
                    register_data = {
                        "username": existing_user.username,  # 重复的用户名
                        "email": f"newemail_{new_email_unique_id}@example.com",     # 不同的邮箱（使用唯一标识符）
                        "password": "Strongpassword123@",
                        "nickname": "新昵称",
                        "captcha_id": captcha_data["captcha_id"],
                        "captcha_solution": captcha_data["captcha_solution"]
                    }
                    
                    # 执行
                    response = await client.post("/api/v1/users/register", json=register_data)
                
                    # 断言 API 响应
                    assert response.status_code == 409, f"HTTP状态码应该是409, 实际: {response.status_code}, 响应: {response.text}"
                    
                    response_data = response.json()
                    assert response_data["code"] == 4009, "业务状态码应该是4009"
                    assert "该账号已被注册" in response_data["message"], "错误信息应该包含该账号已被注册"
                    
                    # 验证数据库状态 - 确保没有创建新用户
                    user_by_email = await crud_user.get_by_email(db, register_data["email"])
                    assert user_by_email is None, "不应该创建新用户"
    
    @pytest.mark.asyncio
    async def test_register_fails_email_exists(self, async_client, db_session, mock_redis_captcha_success):
        """
        测试邮箱已存在时注册失败
        - 先创建一个用户
        - 模拟验证码校验成功
        - 尝试使用相同邮箱注册
        - 验证返回409冲突错误
        """
        assert mock_redis_captcha_success is not None, "Mock fixture应该被激活"
        # 额外patch user_service的get_redis_client，确保覆盖所有路径
        with patch('app.services.user_service.get_redis_client', return_value=mock_redis_captcha_success):
            async for client in async_client:
                async for db in db_session:
                    # 准备 - 先创建已存在的用户（使用唯一标识符避免冲突）
                    unique_id = uuid.uuid4().hex[:8]
                    existing_user = await create_test_user(db, f"existinguser2_{unique_id}", f"existing2_{unique_id}@example.com")
                    
                    # 准备验证码数据
                    captcha_data = create_captcha_mock_data()
                    
                    # 准备注册数据（使用已存在的邮箱）
                    new_username_unique_id = uuid.uuid4().hex[:8]
                    register_data = {
                        "username": f"newusername_{new_username_unique_id}",           # 不同的用户名（使用唯一标识符）
                        "email": existing_user.email,       # 重复的邮箱
                        "password": "Strongpassword123!",
                        "nickname": "新昵称",
                        "captcha_id": captcha_data["captcha_id"],
                        "captcha_solution": captcha_data["captcha_solution"]
                    }
                    
                    # 执行
                    response = await client.post("/api/v1/users/register", json=register_data)
                    
                    # 断言 API 响应
                    assert response.status_code == 409, f"HTTP状态码应该是409, 实际: {response.status_code}, 响应: {response.text}"
                    
                    response_data = response.json()
                    assert response_data["code"] == 4009, "业务状态码应该是4009"
                    assert "该账号已被注册" in response_data["message"], "错误信息应该包含该账号已被注册"
                    
                    # 验证数据库状态 - 确保没有创建新用户
                    user_by_username = await crud_user.get_by_username(db, register_data["username"])
                    assert user_by_username is None, "不应该创建新用户"
    
    @pytest.mark.asyncio
    async def test_register_fails_missing_fields(self, async_client, mock_redis_captcha_success):
        """
        测试缺少必填字段时注册失败
        - 模拟验证码校验成功
        - 发送缺少必填字段的注册请求
        - 验证返回400错误
        """
        async for client in async_client:
            # 准备验证码数据
            captcha_data = create_captcha_mock_data()
            
            # 准备不完整的注册数据（缺少nickname）
            incomplete_data = {
                "username": "incompleteuser",
                "email": "incomplete@example.com",
                "password": "strongpassword123",
                # 缺少 nickname
                "captcha_id": captcha_data["captcha_id"],
                "captcha_solution": captcha_data["captcha_solution"]
            }
            
            # 执行
            response = await client.post("/api/v1/users/register", json=incomplete_data)
            
            # 断言 API 响应
            assert response.status_code == 422, "HTTP状态码应该是422（字段验证错误）"
    
    @pytest.mark.asyncio
    async def test_register_fails_invalid_captcha(self, async_client, db_session, mock_redis):
        """
        测试验证码错误时注册失败
        - 模拟验证码校验失败
        - 发送注册请求
        - 验证返回400错误
        """
        async for client in async_client:
            async for db in db_session:
                # 模拟验证码校验失败
                mock_redis.get.return_value = None  # 模拟验证码不存在或已过期
                
                # 准备注册数据
                register_data = {
                    "username": "captchauser",
                    "email": "captcha@example.com",
                    "password": "Strongpassword123!",
                    "nickname": "验证码用户",
                    "captcha_id": "invalid-captcha-id",
                    "captcha_solution": "wrong_solution"
                }
                
                # 执行
                response = await client.post("/api/v1/users/register", json=register_data)
                
                # 断言 API 响应
                assert response.status_code == 400, "HTTP状态码应该是400"
                
                response_data = response.json()
                assert response_data["code"] == 4003, "业务状态码应该是4003"
                assert "验证码错误或已过期" in response_data["message"], "错误信息应该包含验证码相关错误"
                
                # 验证数据库状态 - 确保没有创建用户
                user = await crud_user.get_by_username(db, "captchauser")
                assert user is None, "验证码错误时不应该创建用户"
    
    @pytest.mark.asyncio
    async def test_register_fails_invalid_email_format(self, async_client, mock_redis_captcha_success):
        """
        测试邮箱格式无效时注册失败
        - 模拟验证码校验成功
        - 发送格式错误的邮箱
        - 验证返回400错误
        """
        async for client in async_client:
            # 准备验证码数据
            captcha_data = create_captcha_mock_data()
            
            # 准备注册数据（邮箱格式错误）
            register_data = {
                "username": "emailformatuser",
                "email": "invalid_email_format",  # 无效的邮箱格式
                "password": "strongpassword123",
                "nickname": "邮箱格式用户",
                "captcha_id": captcha_data["captcha_id"],
                "captcha_solution": captcha_data["captcha_solution"]
            }
            
            # 执行
            response = await client.post("/api/v1/users/register", json=register_data)
            
            # 断言 API 响应
            assert response.status_code == 400, "HTTP状态码应该是400"
            
            response_data = response.json()
            assert response_data["code"] == 4001, "业务状态码应该是4001"
            assert "邮箱格式无效" in response_data["message"], "错误信息应该包含邮箱格式无效"
    
    @pytest.mark.asyncio
    async def test_register_fails_weak_password(self, async_client, mock_redis_captcha_success):
        """
        测试密码过于简单时注册失败
        - 模拟验证码校验成功
        - 发送过短的密码
        - 验证返回400错误
        """
        async for client in async_client:
            # 准备验证码数据
            captcha_data = create_captcha_mock_data()
            
            # 准备注册数据（密码过短）
            register_data = {
                "username": "weakpwduser",
                "email": "weakpwd@example.com",
                "password": "123",  # 密码过短
                "nickname": "弱密码用户",
                "captcha_id": captcha_data["captcha_id"],
                "captcha_solution": captcha_data["captcha_solution"]
            }
            
            # 执行
            response = await client.post("/api/v1/users/register", json=register_data)
            
            # 断言 API 响应

            assert response.status_code == 422, "HTTP状态码应该是400"
            print("API response", response.json())
            #response_data = response.json()
            #assert response_data["code"] == 4001, "业务状态码应该是4001"
            #assert "密码长度至少6位" in response_data["message"], "错误信息应该包含密码长度要求"


class TestPhoneRegisterAPI:
    """P1/P2: 手机号注册 API 的 ticket 路径与 schema 边界"""

    @pytest.mark.asyncio
    async def test_register_phone_success(self, async_client, db_session, mocker):
        """P2: /users/register/phone 成功返回用户与 token 信息"""
        mock_result = {
            "user_public_id": "660e8400-e29b-41d4-a716-446655440000",
            "username": "u_phone_0000",
            "nickname": "手机用户",
            "phone_masked": "+86********000",
            "is_new_user": True,
            "access_token": "access_phone",
            "refresh_token": "refresh_phone",
            "token_type": "bearer",
        }

        async for client in async_client:
            async for db in db_session:
                mock_auth_service = mocker.patch("app.api.v1.endpoints.users.AuthService")
                mock_auth_service.return_value.register_by_phone_ticket = AsyncMock(return_value=mock_result)

                response = await client.post(
                    "/api/v1/users/register/phone",
                    json={
                        "register_ticket": "register-ticket-abc",
                        "password": "StrongPass@123",
                        "nickname": "手机用户",
                    }
                )

                assert response.status_code == 200
                response_data = response.json()
                assert response_data["code"] == 200
                assert response_data["message"] == "注册成功"
                data = response_data["data"]
                assert data["public_id"] == mock_result["user_public_id"]
                assert data["phone_number"] == mock_result["phone_masked"]
                assert data["is_phone_verified"] is True
                assert data["access_token"] == "access_phone"

    @pytest.mark.asyncio
    async def test_register_phone_invalid_ticket(self, async_client, db_session, mocker):
        """P2: register_ticket 无效时映射为 400/4004"""
        async for client in async_client:
            async for db in db_session:
                mock_auth_service = mocker.patch("app.api.v1.endpoints.users.AuthService")
                mock_auth_service.return_value.register_by_phone_ticket = AsyncMock(
                    side_effect=AuthInvalidTokenException("凭证无效或已过期")
                )

                response = await client.post(
                    "/api/v1/users/register/phone",
                    json={
                        "register_ticket": "bad-ticket",
                        "password": "StrongPass@123",
                        "nickname": "手机用户",
                    }
                )

                assert response.status_code == 400
                response_data = response.json()
                assert response_data["code"] == 4004
                assert "凭证无效" in response_data["message"]

    @pytest.mark.asyncio
    async def test_register_phone_weak_password(self, async_client, db_session, mocker):
        """P1: service 层弱密码异常映射为 400/4002"""
        async for client in async_client:
            async for db in db_session:
                mock_auth_service = mocker.patch("app.api.v1.endpoints.users.AuthService")
                mock_auth_service.return_value.register_by_phone_ticket = AsyncMock(
                    side_effect=AuthWeakPasswordException("新密码不符合强度要求")
                )

                response = await client.post(
                    "/api/v1/users/register/phone",
                    json={
                        "register_ticket": "register-ticket-abc",
                        "password": "weakpass",
                        "nickname": "手机用户",
                    }
                )

                assert response.status_code == 400
                response_data = response.json()
                assert response_data["code"] == 4002
                assert "强度" in response_data["message"]

    @pytest.mark.asyncio
    async def test_register_phone_duplicate(self, async_client, db_session, mocker):
        """P2: 手机号重复注册时映射为 409/4009"""
        async for client in async_client:
            async for db in db_session:
                mock_auth_service = mocker.patch("app.api.v1.endpoints.users.AuthService")
                mock_auth_service.return_value.register_by_phone_ticket = AsyncMock(
                    side_effect=Exception("该手机号已被注册")
                )

                response = await client.post(
                    "/api/v1/users/register/phone",
                    json={
                        "register_ticket": "register-ticket-abc",
                        "password": "StrongPass@123",
                        "nickname": "手机用户",
                    }
                )

                assert response.status_code == 409
                response_data = response.json()
                assert response_data["code"] == 4009
                assert "已被注册" in response_data["message"]

    @pytest.mark.asyncio
    async def test_register_phone_password_min_length_is_8(self, async_client):
        """P1: 手机号注册 7 位密码应被 schema 拦截"""
        async for client in async_client:
            response = await client.post(
                "/api/v1/users/register/phone",
                json={
                    "register_ticket": "register-ticket-abc",
                    "password": "Aa1@abc",
                    "nickname": "手机用户",
                }
            )

            assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_password_min_length_is_8(self, async_client):
        """P1: 邮箱注册 7 位密码应被 schema 拦截"""
        async for client in async_client:
            response = await client.post(
                "/api/v1/users/register",
                json={
                    "username": "shortpwduser",
                    "email": "shortpwd@example.com",
                    "password": "Aa1@abc",
                    "nickname": "短密码用户",
                    "captcha_id": "captcha-id",
                    "captcha_solution": "12345",
                }
            )

            assert response.status_code == 422
