"""
批次二认证API集成测试 - 用户功能服务
对批次二新增认证端点进行集成测试：refresh、logout、password-reset流程
"""

import pytest
import uuid
from unittest.mock import patch, AsyncMock

from .conftest import create_test_user, create_captcha_mock_data


class TestRefreshToken:
    """测试令牌刷新API"""
    
    async def login_user(self, client, db, username="testuser", email="test@example.com"):
        """辅助函数：登录用户并返回tokens"""
        user = await create_test_user(db, username, email)
        captcha_data = create_captcha_mock_data()
        
        login_data = {
            "username": username,
            "password": "testpassword123",
            "captcha_id": captcha_data["captcha_id"],
            "captcha_solution": captcha_data["captcha_solution"]
        }
        
        response = await client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 200
        return response.json()["data"], user
    
    @pytest.mark.asyncio
    async def test_refresh_token_success(self, async_client, db_session, mock_redis_captcha_success):
        """
        测试刷新令牌成功
        - 先登录获取refresh_token
        - 使用refresh_token请求新的access_token
        - 验证返回新的access_token
        """
        assert mock_redis_captcha_success is not None, "Mock fixture应该被激活"
        
        async for client in async_client:
            async for db in db_session:
                # 准备 - 登录获取tokens（使用唯一标识符避免冲突）
                unique_id = uuid.uuid4().hex[:8]
                tokens, user = await self.login_user(client, db, f"refreshuser_{unique_id}", f"refresh_{unique_id}@example.com")
                refresh_token = tokens["refresh_token"]
                original_access_token = tokens["access_token"]
                
                # 执行 - 刷新令牌
                refresh_data = {"refresh_token": refresh_token}
                response = await client.post("/api/v1/auth/refresh", json=refresh_data)
                
                # 断言 API 响应
                assert response.status_code == 200, "HTTP状态码应该是200"
                
                response_data = response.json()
                assert response_data["code"] == 200, "业务状态码应该是200"
                assert response_data["message"] == "success", "消息应该是success"
                
                # 验证返回新的access_token
                data = response_data["data"]
                assert "access_token" in data, "响应应该包含access_token"
                assert "token_type" in data, "响应应该包含token_type"
                assert data["token_type"] == "bearer", "token_type应该是bearer"
                
                new_access_token = data["access_token"]
                assert new_access_token != original_access_token, "新的access_token应该与原来的不同"
                assert len(new_access_token) > 0, "新的access_token不应该为空"
    
    @pytest.mark.asyncio
    async def test_refresh_token_fails_with_invalid_token(self, async_client):
        """
        测试使用无效refresh_token刷新失败
        - 使用伪造的refresh_token
        - 验证返回401错误
        """
        async for client in async_client:
            # 执行 - 使用无效token
            refresh_data = {"refresh_token": "invalid_fake_token_12345"}
            response = await client.post("/api/v1/auth/refresh", json=refresh_data)
            
            # 断言 API 响应
            assert response.status_code == 401, "HTTP状态码应该是401"
            
            response_data = response.json()
            assert response_data["code"] == 3003, "业务状态码应该是3003"


class TestLogout:
    """测试用户登出API"""
    
    async def login_user(self, client, db, username="testuser", email="test@example.com"):
        """辅助函数：登录用户并返回tokens"""
        user = await create_test_user(db, username, email)
        captcha_data = create_captcha_mock_data()
        
        login_data = {
            "username": username,
            "password": "testpassword123",
            "captcha_id": captcha_data["captcha_id"],
            "captcha_solution": captcha_data["captcha_solution"]
        }
        
        response = await client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 200
        return response.json()["data"], user
    

    @pytest.mark.asyncio
    async def test_logout_success_and_token_is_blacklisted(self, async_client, db_session, mock_redis_with_blacklist):
        """
        测试登出成功并验证token被加入黑名单
        - 登录获取access_token
        - 使用token请求logout
        - 验证logout成功
        - 验证token被加入黑名单（再次使用该token访问受保护接口失败）
        """
        assert mock_redis_with_blacklist is not None, "Mock fixture应该被激活"

        async for client in async_client:
            async for db in db_session:
                # 准备 - 登录获取tokens（使用唯一标识符避免冲突）
                unique_id = uuid.uuid4().hex[:8]
                tokens, user = await self.login_user(client, db, f"logoutuser_{unique_id}", f"logout_{unique_id}@example.com")
                access_token = tokens["access_token"]

                # 执行 - 登出
                headers = {"Authorization": f"Bearer {access_token}"}
                response = await client.post("/api/v1/auth/logout", headers=headers)

                # 断言 API 响应
                assert response.status_code == 200, "HTTP状态码应该是200"

                response_data = response.json()
                assert response_data["code"] == 200, "业务状态码应该是200"
                assert response_data["data"] is None, "data应该为null"

                # 验证副作用 - token已被加入黑名单
                # 尝试使用同一个access_token访问受保护的接口
                protected_response = await client.get("/api/v1/users/me", headers=headers)
                assert protected_response.status_code == 401, "使用已登出的token应该返回401"


class TestPasswordResetFlow:
    """测试密码重置流程"""
    
    @pytest.mark.asyncio
    async def test_password_reset_flow_success(self, async_client, db_session, mock_redis_password_reset):
        """
        测试完整的密码重置流程成功
        - 创建测试用户
        - 请求密码重置（发送邮件）
        - 使用重置令牌执行密码重置
        - 验证新密码可以登录，旧密码不能登录
        """
        assert mock_redis_password_reset is not None, "Mock fixture应该被激活"
        
        async for client in async_client:
            async for db in db_session:
                # 准备 - 创建测试用户（使用唯一标识符避免冲突）
                unique_id = uuid.uuid4().hex[:8]
                username = f"resetuser_{unique_id}"
                email = f"reset_{unique_id}@example.com"
                user_to_reset = await create_test_user(db, username, email)
                original_password_hash = user_to_reset.password_hash
                
                # 步骤1: 请求密码重置
                captcha_data = create_captcha_mock_data()
                reset_request_data = {
                    "email": email,
                    "captcha_id": captcha_data["captcha_id"],
                    "captcha_solution": captcha_data["captcha_solution"]
                }
                
                response = await client.post("/api/v1/auth/password-reset-request", json=reset_request_data)
                
                # 断言步骤1响应
                assert response.status_code == 200, "密码重置请求应该成功"
                response_data = response.json()
                assert response_data["code"] == 200, "业务状态码应该是200"
                assert "邮件已发送" in response_data["data"]["message"] or "已发送" in response_data["data"]["message"], "应该返回邮件发送提示"
                
                # ✅ 从mock中获取生成的reset token
                reset_tokens = mock_redis_password_reset._reset_tokens
                reset_token = None
                for key in reset_tokens.keys():
                    if key.startswith("password_reset:"):
                        reset_token = key.split(":")[-1]
                        break
                
                assert reset_token is not None, "应该生成了reset token"
                
                # 步骤2: 执行密码重置（使用符合强度要求的密码）
                new_password = "NewStrongPassword123!"
                reset_data = {
                    "reset_token": reset_token,  # ✅ 使用真实生成的token
                    "new_password": new_password
                }
                
                response = await client.post("/api/v1/auth/password-reset", json=reset_data)
                
                # 断言步骤2响应
                assert response.status_code == 200, "密码重置执行应该成功"
                response_data = response.json()
                assert response_data["code"] == 200, "业务状态码应该是200"
                assert "密码重置成功" in response_data["message"], "应该返回密码重置成功消息"
                
                # 验证数据库状态 - 密码已更改
                await db.refresh(user_to_reset)
                assert user_to_reset.password_hash != original_password_hash, "密码哈希应该已改变"
                
                # 验证最终效果 - 新密码可以登录
                captcha_data = create_captcha_mock_data()
                login_data = {
                    "username": username,
                    "password": new_password,
                    "captcha_id": captcha_data["captcha_id"],
                    "captcha_solution": captcha_data["captcha_solution"]
                }
                
                login_response = await client.post("/api/v1/auth/login", json=login_data)
                assert login_response.status_code == 200, "使用新密码应该能够登录成功"
                
                # 验证旧密码不能登录
                old_login_data = {
                    "username": username,
                    "password": "testpassword123",  # 旧密码
                    "captcha_id": captcha_data["captcha_id"],
                    "captcha_solution": captcha_data["captcha_solution"]
                }
                
                old_login_response = await client.post("/api/v1/auth/login", json=old_login_data)
                assert old_login_response.status_code == 401, "使用旧密码应该登录失败"
    
    @pytest.mark.asyncio
    async def test_password_reset_request_with_nonexistent_email(self, async_client, mock_redis_captcha_success):
        """
        测试使用不存在的邮箱请求密码重置
        - 使用不存在的邮箱
        - 验证仍返回成功响应（防止邮箱枚举）
        """
        assert mock_redis_captcha_success is not None, "Mock fixture应该被激活"
        
        async for client in async_client:
            # 执行 - 使用不存在的邮箱
            captcha_data = create_captcha_mock_data()
            reset_request_data = {
                "email": "nonexistent@example.com",
                "captcha_id": captcha_data["captcha_id"],
                "captcha_solution": captcha_data["captcha_solution"]
            }
            
            response = await client.post("/api/v1/auth/password-reset-request", json=reset_request_data)
            
            # 断言 API 响应 - 应该返回模糊的成功提示
            assert response.status_code == 200, "应该返回200以防止邮箱枚举"
            response_data = response.json()
            assert response_data["code"] == 200, "业务状态码应该是200"
    
    @pytest.mark.asyncio
    async def test_password_reset_with_invalid_token(self, async_client):
        """
        测试使用无效重置令牌执行密码重置
        - 使用伪造的reset_token
        - 验证返回400错误
        """
        async for client in async_client:
            # 执行 - 使用无效token
            reset_data = {
                "reset_token": "invalid_fake_reset_token",
                # 合规密码（≥8位含大小写/数字/特殊字符），避免先触发密码强度校验（生产先校验强度）
                "new_password": "New_password_123!"
            }
            
            # Mock Redis返回None表示token不存在
            # 注意：auth_service 顶部已 from app.core.redis_client import get_redis_client，
            # 必须 patch auth_service 模块内的引用
            with patch('app.services.auth_service.get_redis_client') as mock_get_redis:
                mock_redis = AsyncMock()
                mock_redis.get.return_value = None  # token不存在
                mock_get_redis.return_value = mock_redis
                
                response = await client.post("/api/v1/auth/password-reset", json=reset_data)
            
            # 断言 API 响应
            assert response.status_code == 400, "HTTP状态码应该是400"
            response_data = response.json()
            assert response_data["code"] == 4005, "业务状态码应该是4005"
            assert "无效的令牌" in response_data["message"], "应该包含无效令牌的错误信息" 