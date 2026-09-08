# test_api_users_real_redis.py
"""
用户注册API真实Redis集成测试
使用真实Redis连接进行完整的集成测试
"""

import pytest
import uuid
from app.crud import crud_user


class TestUserRegisterWithRealRedis:
    """使用真实Redis的用户注册测试"""

    @pytest.mark.asyncio
    @pytest.mark.integration  # 标记为集成测试
    async def test_register_success_with_real_redis(self, async_client, db_session, real_redis_client):
        """
        测试用户注册成功 - 使用真实Redis
        - 真实Redis验证码存储和校验
        - 准备全新的用户信息
        - 发送注册请求
        - 验证API响应正确
        - 验证数据库中用户被正确创建
        - 验证Redis中验证码被正确删除
        """
        async for client in async_client:
            async for db in db_session:
                async for redis_client in real_redis_client:
                    # 手动设置验证码数据
                    captcha_id = "test-captcha-id-success"
                    captcha_solution = "test_solution"
                    cache_key = f"captcha:solution:{captcha_id}"

                    # ✅ 关键：在Redis中设置验证码（这行代码缺失了）
                    await redis_client.set(cache_key, captcha_solution.lower(), ex=180)

                    # 验证验证码确实被设置
                    stored_value = await redis_client.get(cache_key)
                    assert stored_value == captcha_solution.lower(), f"验证码应该被正确存储，实际存储: {stored_value}"


                    # 准备注册数据（使用真实验证码）
                    unique_id = uuid.uuid4().hex[:8]
                    register_data = {
                        "username": f"realredis_user_{unique_id}",
                        "email": f"realredis_user_{unique_id}@example.com",
                        "password": "StrongPassword123!",
                        "nickname": "真实Redis用户",
                        "captcha_id": captcha_id,
                        "captcha_solution": captcha_solution,
                        "agreed_to_terms": True,
                    }

                    # 执行注册请求
                    response = await client.post("/api/v1/users/register", json=register_data)

                    # 断言 API 响应
                    assert response.status_code == 200, f"HTTP状态码应该是200, 实际: {response.status_code}, 响应: {response.text}"

                    response_data = response.json()
                    assert response_data["code"] == 200, f"业务状态码应该是200, 实际响应: {response_data}"
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

                    # 验证验证码被删除（注册时会删除使用过的验证码）
                    stored_value_after = await redis_client.get(cache_key)
                    assert stored_value_after is None, "验证码使用后应该被删除"


    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_register_fails_invalid_captcha_with_real_redis(self, async_client, db_session, real_redis_client):
        """
        测试验证码错误时注册失败 - 使用真实Redis
        - 使用错误的验证码
        - 验证Redis查询和错误处理
        """
        async for client in async_client:
            async for db in db_session:
                # 准备注册数据（使用错误验证码，但密码要符合要求才能测试验证码错误）
                unique_id = uuid.uuid4().hex[:8]
                register_data = {
                    "username": f"failuser_{unique_id}",
                    "email": f"fail_{unique_id}@example.com",
                    "password": "StrongPassword123!",
                    "nickname": "失败用户",
                    "captcha_id": "non-existent-captcha-id",
                    "captcha_solution": "wrong_solution",
                    "agreed_to_terms": True,
                }

                # 执行注册请求
                response = await client.post("/api/v1/users/register", json=register_data)

                # 断言 API 响应
                assert response.status_code == 400, "HTTP状态码应该是400"

                response_data = response.json()
                assert response_data["code"] == 4003, "业务状态码应该是4003"
                assert "验证码错误或已过期" in response_data["message"], "错误信息应该包含验证码相关错误"

                # 验证数据库状态 - 确保没有创建用户
                user = await crud_user.get_by_username(db, "failuser")
                assert user is None, "验证码错误时不应该创建用户"

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_captcha_cleanup_after_use(self, async_client, db_session, real_redis_client):
        """
        测试验证码使用后被正确删除 - Redis清理验证
        """
        async for client in async_client:
            async for db in db_session:
                async for redis_client in  real_redis_client:  # ← 修复：解包redis fixture
                    # 手动在Redis中设置验证码
                    captcha_id = "cleanup-test-captcha-id"
                    captcha_solution = "cleanup_solution"
                    cache_key = f"captcha:solution:{captcha_id}"

                    await redis_client.set(cache_key, captcha_solution.lower(), ex=180)

                    # 验证验证码存在
                    stored_value = await redis_client.get(cache_key)
                    assert stored_value == captcha_solution.lower(), "验证码应该被正确存储"

                    # 准备注册数据
                    unique_id = uuid.uuid4().hex[:8]
                    register_data = {
                        "username": f"cleanup_user_{unique_id}",
                        "email": f"cleanup_{unique_id}@example.com",
                        "password": "StrongPassword123!",
                        "nickname": "清理测试用户",
                        "captcha_id": captcha_id,
                        "captcha_solution": captcha_solution,
                        "agreed_to_terms": True,
                    }

                    # 执行注册请求
                    response = await client.post("/api/v1/users/register", json=register_data)

                    # 验证注册成功
                    assert response.status_code == 200, "注册应该成功"

                    # 验证验证码被删除
                    stored_value_after = await redis_client.get(cache_key)
                    assert stored_value_after is None, "验证码使用后应该被删除"