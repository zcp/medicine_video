"""
认证SSO API端点测试 - test_auth_sso.py
测试 POST /api/v1/auth/sso-login 端点的集成测试
"""
import pytest
import uuid
from faker import Faker

from app.services.auth_service import InvalidTokenException, InvalidCredentialsException

fake = Faker()


class TestAuthSSOAPI:
    """测试认证SSO API端点"""

    @pytest.mark.asyncio
    async def test_sso_login_api_success(self, async_client, db_session, mocker):
        """测试SSO登录API成功响应"""
        async for client in async_client:
            async for db in db_session:
                # 准备: 模拟 AuthService.sso_login 成功返回
                mock_tokens = {
                    "access_token": f"access_{uuid.uuid4().hex}",
                    "refresh_token": f"refresh_{uuid.uuid4().hex}",
                    "token_type": "bearer"
                }

                # 正确的做法：patch 类，然后设置实例的方法
                mock_auth_service_class = mocker.patch("app.api.v1.endpoints.auth.AuthService")
                mock_auth_service_instance = mock_auth_service_class.return_value
                mock_auth_service_instance.sso_login = mocker.AsyncMock(return_value=mock_tokens)

                # 准备请求数据
                request_data = {
                    "id_token": f"dummy_id_token_{uuid.uuid4().hex}"
                }

                # 执行: 向 SSO 登录端点发送请求
                response = await client.post(
                    "/api/v1/auth/sso-login",
                    json=request_data
                )

                # 断言: 验证响应（标准响应格式）
                assert response.status_code == 200
                response_data = response.json()
                
                assert response_data["code"] == 200
                assert "data" in response_data
                assert "message" in response_data
                assert "timestamp" in response_data
                
                # 验证返回的token信息
                tokens = response_data["data"]
                assert tokens == mock_tokens
                assert "access_token" in tokens
                assert "refresh_token" in tokens
                assert tokens["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_sso_login_api_authing_failure(self, async_client, db_session, mocker):
        """测试SSO登录API Authing验证失败"""
        async for client in async_client:
            async for db in db_session:
                # 准备: 模拟 AuthService.sso_login 抛出 InvalidTokenException
                mock_auth_service = mocker.patch("app.api.v1.endpoints.auth.AuthService")
                mock_auth_service.return_value.sso_login.side_effect = InvalidTokenException("认证凭证无效")
                
                # 准备请求数据
                request_data = {
                    "id_token": "invalid_token"
                }
                
                # 执行: 发送POST请求
                response = await client.post(
                    "/api/v1/auth/sso-login",
                    json=request_data
                )
                
                # 断言: 验证错误响应
                assert response.status_code == 401
                response_data = response.json()
                assert response_data["code"] == 3005
                assert response_data["message"] == "认证凭证无效"

    @pytest.mark.asyncio
    async def test_sso_login_api_user_status_error(self, async_client, db_session, mocker):
        """测试SSO登录API用户状态异常"""
        async for client in async_client:
            async for db in db_session:
                # 准备: 模拟 AuthService.sso_login 抛出 InvalidCredentialsException
                mock_auth_service = mocker.patch("app.api.v1.endpoints.auth.AuthService")
                mock_auth_service.return_value.sso_login.side_effect = InvalidCredentialsException("账户状态异常")
                
                # 准备请求数据
                request_data = {
                    "id_token": f"dummy_token_{uuid.uuid4().hex}"
                }
                
                # 执行: 发送POST请求
                response = await client.post(
                    "/api/v1/auth/sso-login",
                    json=request_data
                )
                
                # 断言: 验证错误响应
                assert response.status_code == 401
                response_data = response.json()
                assert response_data["code"] == 3004
                assert response_data["message"] == "账户状态异常"

    @pytest.mark.asyncio
    async def test_sso_login_api_server_error(self, async_client, db_session, mocker):
        """测试SSO登录API服务器内部错误"""
        async for client in async_client:
            async for db in db_session:
                # 准备: 模拟 AuthService.sso_login 抛出通用异常
                mock_auth_service = mocker.patch("app.api.v1.endpoints.auth.AuthService")
                mock_auth_service.return_value.sso_login.side_effect = Exception("数据库连接失败")
                
                # 准备请求数据
                request_data = {
                    "id_token": f"dummy_token_{uuid.uuid4().hex}"
                }
                
                # 执行: 发送POST请求
                response = await client.post(
                    "/api/v1/auth/sso-login",
                    json=request_data
                )
                
                # 断言: 验证服务器错误响应
                assert response.status_code == 500
                response_data = response.json()
                assert response_data["code"] == 1002
                assert response_data["message"] == "服务器内部错误"

    @pytest.mark.asyncio
    async def test_sso_login_api_invalid_request_data(self, async_client, db_session):
        """测试SSO登录API请求数据无效"""
        async for client in async_client:
            async for db in db_session:
                # 执行: 发送缺少必需字段的请求
                response = await client.post(
                    "/api/v1/auth/sso-login",
                    json={}  # 缺少 id_token 字段
                )
                
                # 断言: 验证请求参数错误
                assert response.status_code == 422  # FastAPI validation error

    @pytest.mark.asyncio
    async def test_sso_login_api_with_client_ip(self, async_client, db_session, mocker):
        """测试SSO登录API正确传递客户端IP"""
        async for client in async_client:
            async for db in db_session:
                # 准备: 模拟 AuthService.sso_login 成功返回
                mock_tokens = {
                    "access_token": f"access_{uuid.uuid4().hex}",
                    "refresh_token": f"refresh_{uuid.uuid4().hex}",
                    "token_type": "bearer"
                }
                
                mock_auth_service = mocker.patch("app.api.v1.endpoints.auth.AuthService")
                mock_auth_service_instance = mock_auth_service.return_value
                mock_auth_service_instance.sso_login = mocker.AsyncMock(return_value=mock_tokens)
                
                # 准备请求数据
                request_data = {
                    "id_token": f"dummy_token_{uuid.uuid4().hex}"
                }
                
                # 执行: 发送请求
                response = await client.post(
                    "/api/v1/auth/sso-login",
                    json=request_data
                )
                
                # 断言: 验证响应成功
                assert response.status_code == 200
                
                # 验证 sso_login 被正确调用，包含客户端IP
                mock_auth_service_instance.sso_login.assert_called_once()
                call_args = mock_auth_service_instance.sso_login.call_args
                
                # 验证调用参数
                assert call_args[1]["id_token"] == request_data["id_token"]
                assert "client_ip" in call_args[1]  # 确保传递了客户端IP
