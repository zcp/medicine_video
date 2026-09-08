"""
用户手机号绑定API端点测试 - test_users_phone.py
测试 POST /api/v1/users/me/phone 端点的集成测试
"""
import pytest
import uuid
from faker import Faker

from app.exceptions import ValidationError

fake = Faker()


class TestUsersPhoneAPI:
    """测试用户手机号绑定API端点"""

    @pytest.mark.asyncio
    async def test_bind_phone_api_success(self, async_client, db_session, authenticated_user, mocker):
        """测试手机号绑定API成功响应"""
        async for client in async_client:
            async for db in db_session:
                # 准备: 获取已认证用户的token
                async for user, token in authenticated_user:

                    # 模拟 UserService.bind_phone_number 成功执行
                    mock_user_service = mocker.patch("app.api.v1.endpoints.users.UserService")
                    mock_user_service.return_value.bind_phone_number.return_value = None

                    # 准备请求数据
                    phone_number = f"+86{fake.random_int(min=13000000000, max=19999999999)}"
                    request_data = {
                        "phone_number": phone_number,
                        "verification_code": "123456"
                    }

                    # 准备认证头
                    headers = {"Authorization": f"Bearer {token}"}

                    # 执行: 携带认证头发送POST请求
                    response = await client.post(
                        "/api/v1/users/me/phone",
                        json=request_data,
                        headers=headers
                    )

                    # 断言: 验证响应
                    assert response.status_code == 200
                    response_data = response.json()
                    assert response_data["code"] == 200
                    assert response_data["message"] == "手机号绑定成功"
                    assert response_data["data"] is None

    @pytest.mark.asyncio
    async def test_bind_phone_api_validation_error(self, async_client, db_session, authenticated_user, mocker):
        """测试手机号绑定API验证错误"""
        async for client in async_client:
            async for db in db_session:
                async for user, token in authenticated_user:
                    # 准备: 获取认证token

                    # 模拟 UserService.bind_phone_number 抛出 ValidationError
                    mock_user_service = mocker.patch("app.api.v1.endpoints.users.UserService")
                    mock_user_service.return_value.bind_phone_number.side_effect = ValidationError(
                        "verification_code", "手机验证码错误或已过期"
                    )

                    # 准备请求数据
                    phone_number = f"+86{fake.random_int(min=13000000000, max=19999999999)}"
                    request_data = {
                        "phone_number": phone_number,
                        "verification_code": "wrong_code"
                    }

                    # 准备认证头
                    headers = {"Authorization": f"Bearer {token}"}

                    # 执行: 发送POST请求
                    response = await client.post(
                        "/api/v1/users/me/phone",
                        json=request_data,
                        headers=headers
                    )

                    # 断言: 验证错误响应
                    assert response.status_code == 400
                    response_data = response.json()
                    assert response_data["code"] == 4006

    @pytest.mark.asyncio
    async def test_bind_phone_api_server_error(self, async_client, db_session, authenticated_user, mocker):
        """测试手机号绑定API服务器内部错误"""
        async for client in async_client:
            async for db in db_session:
                # 准备: 获取认证token
                async for user, token in authenticated_user:
                
                    # 模拟 UserService.bind_phone_number 抛出通用异常
                    mock_user_service = mocker.patch("app.api.v1.endpoints.users.UserService")
                    mock_user_service.return_value.bind_phone_number.side_effect = Exception("数据库连接失败")

                    # 准备请求数据
                    phone_number = f"+86{fake.random_int(min=13000000000, max=19999999999)}"
                    request_data = {
                        "phone_number": phone_number,
                        "verification_code": "123456"
                    }

                    # 准备认证头
                    headers = {"Authorization": f"Bearer {token}"}

                    # 执行: 发送POST请求
                    response = await client.post(
                        "/api/v1/users/me/phone",
                        json=request_data,
                        headers=headers
                    )

                    # 断言: 验证服务器错误响应
                    assert response.status_code == 500
                    response_data = response.json()
                    assert response_data["code"] == 1002
                    assert response_data["message"] == "服务器内部错误"

    @pytest.mark.asyncio
    async def test_bind_phone_api_unauthorized(self, async_client, db_session):
        """测试未认证用户无法绑定手机号"""
        async for client in async_client:
            async for db in db_session:
                # 准备请求数据（不提供认证头）
                phone_number = f"+86{fake.random_int(min=13000000000, max=19999999999)}"
                request_data = {
                    "phone_number": phone_number,
                    "verification_code": "123456"
                }
                
                # 执行: 发送未认证的POST请求
                response = await client.post(
                    "/api/v1/users/me/phone",
                    json=request_data
                )
                
                # 断言: 验证未认证错误
                assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_bind_phone_api_invalid_request_data(self, async_client, db_session, authenticated_user):
        """测试手机号绑定API请求数据无效"""
        async for client in async_client:
            async for db in db_session:
                # 准备: 获取认证token
                async for user, token in authenticated_user:

                    # 准备认证头
                    headers = {"Authorization": f"Bearer {token}"}

                    # 测试缺少 phone_number 字段
                    response1 = await client.post(
                        "/api/v1/users/me/phone",
                        json={"verification_code": "123456"},  # 缺少 phone_number
                        headers=headers
                    )
                    assert response1.status_code == 422  # FastAPI validation error

                    # 测试缺少 verification_code 字段
                    response2 = await client.post(
                        "/api/v1/users/me/phone",
                        json={"phone_number": "+8613812345678"},  # 缺少 verification_code
                        headers=headers
                    )
                    assert response2.status_code == 422  # FastAPI validation error

                    # 测试空请求体
                    response3 = await client.post(
                        "/api/v1/users/me/phone",
                        json={},
                        headers=headers
                    )
                    assert response3.status_code == 422  # FastAPI validation error

    @pytest.mark.asyncio
    async def test_bind_phone_api_phone_already_taken(self, async_client, db_session, authenticated_user, mocker):
        """测试手机号已被占用的情况"""
        async for client in async_client:
            async for db in db_session:
                # 准备: 获取认证token
                async for user, token in authenticated_user:

                    # 模拟 UserService.bind_phone_number 抛出手机号已占用错误
                    mock_user_service = mocker.patch("app.api.v1.endpoints.users.UserService")
                    mock_user_service.return_value.bind_phone_number.side_effect = ValidationError(
                        "phone_number", "该手机号已被其他账号绑定"
                    )

                    # 准备请求数据
                    phone_number = f"+86{fake.random_int(min=13000000000, max=19999999999)}"
                    request_data = {
                        "phone_number": phone_number,
                        "verification_code": "123456"
                    }

                    # 准备认证头
                    headers = {"Authorization": f"Bearer {token}"}

                    # 执行: 发送POST请求
                    response = await client.post(
                        "/api/v1/users/me/phone",
                        json=request_data,
                        headers=headers
                    )

                    # 断言: 验证错误响应
                    assert response.status_code == 400
                    response_data = response.json()
                    assert response_data["code"] == 4006
                    assert "该手机号已被其他账号绑定" in str(response_data)

    @pytest.mark.asyncio
    async def test_bind_phone_api_service_call_verification(self, async_client, db_session, authenticated_user, mocker):
        """测试手机号绑定API正确调用服务层方法"""
        async for client in async_client:
            async for db in db_session:
                # 准备: 获取认证token
                async for user, token in authenticated_user:
                
                    # 模拟 UserService.bind_phone_number
                    mock_user_service = mocker.patch("app.api.v1.endpoints.users.UserService")
                    mock_user_service_instance = mock_user_service.return_value
                    mock_user_service_instance.bind_phone_number.return_value = None

                    # 准备请求数据
                    phone_number = f"+86{fake.random_int(min=13000000000, max=19999999999)}"
                    verification_code = "123456"
                    request_data = {
                        "phone_number": phone_number,
                        "verification_code": verification_code
                    }

                    # 准备认证头
                    headers = {"Authorization": f"Bearer {token}"}

                    # 执行: 发送POST请求
                    response = await client.post(
                        "/api/v1/users/me/phone",
                        json=request_data,
                        headers=headers
                    )

                    # 断言: 验证响应成功
                    assert response.status_code == 200

                    # 验证 bind_phone_number 被正确调用
                    mock_user_service_instance.bind_phone_number.assert_called_once()
                    call_args = mock_user_service_instance.bind_phone_number.call_args

                    # 验证调用参数
                    assert call_args[1]["phone_number"] == phone_number
                    assert call_args[1]["verification_code"] == verification_code
                    assert "current_user" in call_args[1]
