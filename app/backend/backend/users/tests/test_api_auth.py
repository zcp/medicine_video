"""
认证API集成测试 - 用户功能服务
对app/api/v1/endpoints/auth.py中的API端点进行集成测试
"""

import pytest
import uuid
import base64
from datetime import datetime, timedelta
from unittest.mock import AsyncMock

from .conftest import create_test_user, create_captcha_mock_data
from app.services.auth_service import InvalidCredentialsException, InvalidTokenException


class TestGetCaptcha:
    """测试获取图形验证码API"""
    
    @pytest.mark.asyncio
    async def test_get_captcha_success(self, async_client, mock_redis):
        """
        测试成功获取图形验证码
        - 发送GET请求到/api/v1/auth/captcha
        - 验证HTTP状态码为200
        - 验证响应格式和数据完整性
        """
        async for client in async_client:
            # 执行
            response = await client.get("/api/v1/auth/captcha")
            
            # 断言 API 响应
            assert response.status_code == 200, "HTTP状态码应该是200"
            
            response_data = response.json()
            assert response_data["code"] == 200, "业务状态码应该是200"
            assert response_data["message"] == "success", "消息应该是success"
            
            # 验证data字段结构
            data = response_data["data"]
            assert "captcha_id" in data, "响应应该包含captcha_id"
            assert "image_base64" in data, "响应应该包含image_base64"
            
            # 验证captcha_id是UUID格式的字符串
            captcha_id = data["captcha_id"]
            assert isinstance(captcha_id, str), "captcha_id应该是字符串"
            assert len(captcha_id) > 0, "captcha_id不应该为空"
            
            # 验证image_base64是非空字符串且有正确前缀
            image_base64 = data["image_base64"]
            assert isinstance(image_base64, str), "image_base64应该是字符串"
            assert image_base64.startswith("data:image/png;base64,"), "应该有正确的base64图片前缀"
            assert len(image_base64) > 30, "base64数据应该有合理长度"

    @pytest.mark.asyncio
    async def test_get_captcha_image_success(self, async_client, mock_redis):
        """P0: 测试通过 captcha_id 获取验证码图片成功"""
        image_bytes = b"fake_png_data"
        mock_redis.get.return_value = base64.b64encode(image_bytes).decode("utf-8")

        async for client in async_client:
            response = await client.get("/api/v1/auth/captcha/image/test-captcha-id")

            assert response.status_code == 200
            assert response.headers["content-type"] == "image/png"
            assert response.content == image_bytes

    @pytest.mark.asyncio
    async def test_get_captcha_image_not_found(self, async_client, mock_redis):
        """P0: 验证码图片不存在或过期时返回 404"""
        mock_redis.get.return_value = None

        async for client in async_client:
            response = await client.get("/api/v1/auth/captcha/image/missing-captcha-id")

            assert response.status_code == 404
            assert response.json()["code"] == 4004


class TestLogin:
    """测试用户登录API"""
    
    @pytest.mark.asyncio
    async def test_login_success(self, async_client, db_session, mock_redis_captcha_success):
        """
        测试用户登录成功
        - 创建测试用户
        - 模拟验证码校验成功
        - 发送正确的登录请求
        - 验证响应包含token信息
        - 验证数据库中登录信息更新
        """
        # ✅ 显式使用mock fixture激活Mock
        assert mock_redis_captcha_success is not None, "Mock fixture应该被激活"
        
        async for client in async_client:
            async for db in db_session:
                # 准备 - 创建测试用户（使用唯一标识符避免与之前测试数据冲突）
                unique_id = uuid.uuid4().hex[:8]
                username = f"loginuser_{unique_id}"
                email = f"login_{unique_id}@example.com"
                user = await create_test_user(db, username, email)
                
                # 准备验证码数据
                captcha_data = create_captcha_mock_data()
                
                # 准备登录请求
                login_data = {
                    "username": username,
                    "password": "testpassword123",  # 这是create_test_user中使用的密码
                    "captcha_id": captcha_data["captcha_id"],
                    "captcha_solution": captcha_data["captcha_solution"]
                }
                
                # 执行
                response = await client.post("/api/v1/auth/login", json=login_data)
                
                # 断言 API 响应
                assert response.status_code == 200, "HTTP状态码应该是200"
                
                response_data = response.json()
                assert response_data["code"] == 200, "业务状态码应该是200"
                assert response_data["message"] == "success", "消息应该是success"
                
                # 验证token数据
                data = response_data["data"]
                assert "access_token" in data, "响应应该包含access_token"
                assert "refresh_token" in data, "响应应该包含refresh_token"
                assert "token_type" in data, "响应应该包含token_type"
                assert data["token_type"] == "bearer", "token_type应该是bearer"
                
                # 验证tokens不为空
                assert len(data["access_token"]) > 0, "access_token不应该为空"
                assert len(data["refresh_token"]) > 0, "refresh_token不应该为空"
                
                # 验证数据库状态 - 重新查询用户
                await db.refresh(user)
                assert user.last_login_at is not None, "last_login_at应该被更新"
                assert user.last_login_ip is not None, "last_login_ip应该被更新"

    
    @pytest.mark.asyncio
    async def test_login_fails_wrong_password(self, async_client, db_session, mock_redis_captcha_success):
        """
        测试密码错误时登录失败
        - 创建测试用户
        - 模拟验证码校验成功
        - 发送错误密码的登录请求
        - 验证返回401错误和正确的错误信息
        """
        # ✅ 显式使用mock fixture激活Mock
        assert mock_redis_captcha_success is not None, "Mock fixture应该被激活"
        
        async for client in async_client:
            async for db in db_session:
                # 准备 - 创建测试用户（使用唯一标识符避免与之前测试数据冲突）
                unique_id = uuid.uuid4().hex[:8]
                username = f"wrongpwduser_{unique_id}"
                email = f"wrongpwd_{unique_id}@example.com"
                await create_test_user(db, username, email)
                
                # 准备验证码数据
                captcha_data = create_captcha_mock_data()
                
                # 准备登录请求（使用错误密码）
                login_data = {
                    "username": "wrongpwduser",
                    "password": "wrong_password",  # 错误密码
                    "captcha_id": captcha_data["captcha_id"],
                    "captcha_solution": captcha_data["captcha_solution"]
                }
                
                # 执行
                response = await client.post("/api/v1/auth/login", json=login_data)
                
                # 断言 API 响应
                assert response.status_code == 401, "HTTP状态码应该是401"
                
                response_data = response.json()
                assert response_data["code"] == 3001, "业务状态码应该是3001"
                assert "用户名或密码错误" in response_data["message"], "错误信息应该包含用户名或密码错误"

    @pytest.mark.asyncio
    async def test_login_success_with_email(self, async_client, db_session, mock_redis_captcha_success):
        """测试使用邮箱登录成功"""
        assert mock_redis_captcha_success is not None
        async for client in async_client:
            async for db in db_session:
                unique_id = uuid.uuid4().hex[:8]
                username = f"loginuser_{unique_id}"
                email = f"login_{unique_id}@example.com"
                user = await create_test_user(db, username, email)
                
                captcha_data = create_captcha_mock_data()
                login_data = {
                    "username": email,  # 使用邮箱登录
                    "password": "testpassword123",
                    "captcha_id": captcha_data["captcha_id"],
                    "captcha_solution": captcha_data["captcha_solution"]
                }
                
                response = await client.post("/api/v1/auth/login", json=login_data)
                assert response.status_code == 200
                assert "access_token" in response.json()["data"]

    @pytest.mark.asyncio
    async def test_login_success_with_phone(self, async_client, db_session, mock_redis_captcha_success):
        """测试使用已验证手机号登录成功"""
        assert mock_redis_captcha_success is not None
        async for client in async_client:
            async for db in db_session:
                unique_id = uuid.uuid4().hex[:8]
                username = f"loginuser_{unique_id}"
                email = f"login_{unique_id}@example.com"
                user = await create_test_user(db, username, email)
                
                # 设置手机号并验证
                from app.crud import crud_user
                phone_number = f"+86138{unique_id[:8]}"
                await crud_user.update(db, user, {"phone_number": phone_number, "is_phone_verified": True})
                
                captcha_data = create_captcha_mock_data()
                login_data = {
                    "username": phone_number,  # 使用手机号登录
                    "password": "testpassword123",
                    "captcha_id": captcha_data["captcha_id"],
                    "captcha_solution": captcha_data["captcha_solution"]
                }
                
                response = await client.post("/api/v1/auth/login", json=login_data)
                assert response.status_code == 200
                assert "access_token" in response.json()["data"]

    @pytest.mark.asyncio
    async def test_login_fails_with_nickname(self, async_client, db_session, mock_redis_captcha_success):
        """测试使用昵称登录失败"""
        assert mock_redis_captcha_success is not None
        async for client in async_client:
            async for db in db_session:
                unique_id = uuid.uuid4().hex[:8]
                username = f"loginuser_{unique_id}"
                email = f"login_{unique_id}@example.com"
                user = await create_test_user(db, username, email)
                
                captcha_data = create_captcha_mock_data()
                login_data = {
                    "username": user.nickname,  # 使用昵称登录
                    "password": "testpassword123",
                    "captcha_id": captcha_data["captcha_id"],
                    "captcha_solution": captcha_data["captcha_solution"]
                }
                
                response = await client.post("/api/v1/auth/login", json=login_data)
                assert response.status_code == 401
                assert "用户名或密码错误" in response.json()["message"]

    @pytest.mark.asyncio
    async def test_login_phone_success(self, async_client, db_session, mocker):
        """P0: 手机号验证码登录 API 成功响应"""
        async for client in async_client:
            async for db in db_session:
                mock_tokens = {
                    "access_token": f"access_{uuid.uuid4().hex}",
                    "refresh_token": f"refresh_{uuid.uuid4().hex}",
                    "token_type": "bearer",
                }
                mock_auth_service = mocker.patch("app.api.v1.endpoints.auth.AuthService")
                mock_auth_service.return_value.login_by_phone_ticket = mocker.AsyncMock(return_value=mock_tokens)

                response = await client.post(
                    "/api/v1/auth/login/phone",
                    json={"login_ticket": "login-ticket-abc"}
                )

                assert response.status_code == 200
                response_data = response.json()
                assert response_data["code"] == 200
                assert response_data["data"] == mock_tokens
                mock_auth_service.return_value.login_by_phone_ticket.assert_called_once()

    @pytest.mark.asyncio
    async def test_login_phone_invalid_ticket(self, async_client, db_session, mocker):
        """P0: 手机号验证码登录 ticket 无效时返回 400"""
        async for client in async_client:
            async for db in db_session:
                mock_auth_service = mocker.patch("app.api.v1.endpoints.auth.AuthService")
                mock_auth_service.return_value.login_by_phone_ticket.side_effect = InvalidTokenException("凭证无效或已过期")

                response = await client.post(
                    "/api/v1/auth/login/phone",
                    json={"login_ticket": "bad-ticket"}
                )

                assert response.status_code == 400
                assert response.json()["code"] == 4004

    @pytest.mark.asyncio
    async def test_login_phone_invalid_credentials(self, async_client, db_session, mocker):
        """P0: 手机号验证码登录凭证不匹配时返回 401"""
        async for client in async_client:
            async for db in db_session:
                mock_auth_service = mocker.patch("app.api.v1.endpoints.auth.AuthService")
                mock_auth_service.return_value.login_by_phone_ticket.side_effect = InvalidCredentialsException("登录凭证无效")

                response = await client.post(
                    "/api/v1/auth/login/phone",
                    json={"login_ticket": "wrong-ticket"}
                )

                assert response.status_code == 401
                assert response.json()["code"] == 3001


class TestSendVerificationCode:
    """测试发送OTP验证码API"""
    
    @pytest.mark.asyncio
    async def test_send_verification_code_success_for_register(self, async_client, db_session, mock_redis_captcha_success):
        """
        测试注册场景发送验证码成功
        - 确保邮箱不存在于数据库
        - 模拟验证码校验成功
        - 发送注册场景的验证码请求
        - 验证响应成功和掩码邮箱
        """
        # ✅ 显式使用mock fixture激活Mock
        assert mock_redis_captcha_success is not None, "Mock fixture应该被激活"
        
        async for client in async_client:
            async for db in db_session:
                # 准备 - 确保邮箱不存在（使用新邮箱）
                new_email = "test_new_user@example.com"
                
                # 准备验证码数据
                captcha_data = create_captcha_mock_data()
                
                # 准备请求数据
                request_data = {
                    "channel": "EMAIL",
                    "recipient": new_email,
                    "scenario": "REGISTER",
                    "captcha_id": captcha_data["captcha_id"],
                    "captcha_solution": captcha_data["captcha_solution"]
                }
                
                # 执行
                response = await client.post("/api/v1/auth/verification-codes", json=request_data)
                
                # 断言 API 响应
                assert response.status_code == 200, "HTTP状态码应该是200"
                
                response_data = response.json()
                assert response_data["code"] == 200, "业务状态码应该是200"
                assert response_data["message"] == "success", "消息应该是success"
                
                # 验证响应数据
                data = response_data["data"]
                assert "message" in data, "响应应该包含message"
                assert "recipient_masked" in data, "响应应该包含recipient_masked"
                assert "cooldown_seconds" in data, "响应应该包含cooldown_seconds"
                
                assert "验证码已发送" in data["message"], "消息应该包含验证码已发送"
                assert data["cooldown_seconds"] == 60, "冷却时间应该是60秒"
                
                # 验证邮箱掩码格式
                masked_email = data["recipient_masked"]
                assert "*" in masked_email, "掩码邮箱应该包含星号"
                assert "@example.com" in masked_email, "掩码邮箱应该保留域名"
    
    @pytest.mark.asyncio
    async def test_send_verification_code_fails_if_email_exists_for_register(self, async_client, db_session, mock_redis_captcha_success):
        """
        测试已存在邮箱的注册验证码发送失败
        - 创建已存在的用户
        - 模拟验证码校验成功
        - 使用已存在邮箱请求注册验证码
        - 验证返回409冲突错误
        """
        # ✅ 显式使用mock fixture激活Mock
        assert mock_redis_captcha_success is not None, "Mock fixture应该被激活"
        
        async for client in async_client:
            async for db in db_session:
                # 准备 - 创建已存在的用户（使用唯一标识符避免与之前测试数据冲突）
                unique_id = uuid.uuid4().hex[:8]
                username = f"existinguser_{unique_id}"
                email = f"existing_{unique_id}@example.com"
                existing_user = await create_test_user(db, username, email)
                
                # 准备验证码数据
                captcha_data = create_captcha_mock_data()
                
                # 准备请求数据（使用已存在的邮箱）
                request_data = {
                    "channel": "EMAIL",
                    "recipient": existing_user.email,
                    "scenario": "REGISTER",
                    "captcha_id": captcha_data["captcha_id"],
                    "captcha_solution": captcha_data["captcha_solution"]
                }
                
                # 执行
                response = await client.post("/api/v1/auth/verification-codes", json=request_data)
                
                # 断言 API 响应
                assert response.status_code == 409, "HTTP状态码应该是409"
                
                response_data = response.json()
                print("API response:", response_data)
                assert response_data["code"] == 4009, "业务状态码应该是4009"
                assert "邮箱已被注册" in response_data["message"], "错误信息应该包含邮箱已被注册"

    @pytest.mark.asyncio
    async def test_send_verification_code_sms_provider_failure(self, async_client, db_session, mocker):
        """
        P1: SMS provider 发送失败时 API 返回 502 而非 200
        - mock sms_provider.send() 返回 False
        - 验证返回 502 + code 1003，不返回"发送成功"
        """
        async for client in async_client:
            async for db in db_session:
                # 让验证码校验通过
                captcha_data = create_captcha_mock_data()

                # mock AuthService.send_otp_code 抛 RuntimeError
                mock_auth = mocker.patch("app.api.v1.endpoints.auth.AuthService")
                mock_instance = mock_auth.return_value
                mock_instance.send_otp_code = AsyncMock(
                    side_effect=RuntimeError("短信服务发送失败")
                )

                response = await client.post(
                    "/api/v1/auth/verification-codes",
                    json={
                        "channel": "SMS",
                        "recipient": "+8613800138000",
                        "scenario": "REGISTER",
                        "captcha_id": captcha_data["captcha_id"],
                        "captcha_solution": captcha_data["captcha_solution"],
                    }
                )

                assert response.status_code == 502, f"期望 502，实际 {response.status_code}"
                response_data = response.json()
                assert response_data["code"] == 1003, f"期望 code=1003，实际 {response_data.get('code')}"
                assert "发送失败" in response_data["message"], "消息应包含'发送失败'" 
