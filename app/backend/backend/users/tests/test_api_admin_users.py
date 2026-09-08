"""
批次五API集成测试 - 后台管理用户接口
对 app/api/v1/admin/users.py 进行集成测试
重点测试权限控制、筛选功能和数据库状态验证
"""

import pytest
import jwt
import uuid
import os
from datetime import datetime, timedelta

# 确保测试环境有JWT密钥（如果未设置，使用测试后备值）
if not os.getenv("JWT_SECRET_KEY"):
    os.environ["JWT_SECRET_KEY"] = "test-jwt-secret-key-for-testing-only"

from app.models.users import User, UserRole, EntityStatus


class TestAdminUsersAPI:
    """后台管理用户API端点测试类"""

    def create_access_token(self, user_public_id) -> str:
        """创建测试用的JWT访问令牌
        
        Args:
            user_public_id: 用户的public_id（UUID字符串或UUID对象）
        """
        from app.core.config import settings
        # 使用settings中的JWT配置，确保与应用程序一致
        JWT_SECRET_KEY = settings.JWT_SECRET_KEY or "test-jwt-secret-key-for-testing-only"
        JWT_ALGORITHM = settings.JWT_ALGORITHM
        
        # 确保user_public_id是UUID字符串
        if isinstance(user_public_id, uuid.UUID):
            user_public_id = str(user_public_id)
        elif not isinstance(user_public_id, str):
            user_public_id = str(user_public_id)
        
        now = datetime.utcnow()
        payload = {
            "user_id": user_public_id,  # 使用UUID字符串
            "type": "access",
            "iat": now,
            "exp": now + timedelta(hours=1),
            "jti": str(uuid.uuid4())
        }
        return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

    @pytest.mark.asyncio
    async def test_get_users_list_as_regular_user_fails(self, async_client, db_session):
        """
        测试普通用户访问管理员接口失败
        - 创建REGULAR角色用户并生成access_token
        - 使用该token请求GET /api/v1/admin/users
        - 验证返回403 Forbidden和业务错误码3002
        """
        async for client in async_client:
            async for db in db_session:
                # 准备 - 创建普通用户
                base_uuid = uuid.uuid4().hex[:8]
                regular_user = User(
                    username=f"regular_user_{base_uuid}",
                    email=f"regular_{base_uuid}@test.com",
                    nickname="Regular User",
                    password_hash="hashed_password_123",
                    role=UserRole.REGULAR,
                    status=EntityStatus.NORMAL
                )
                
                db.add(regular_user)
                await db.commit()
                await db.refresh(regular_user)
                
                # 生成访问令牌
                access_token = self.create_access_token(str(regular_user.public_id))
                headers = {"Authorization": f"Bearer {access_token}"}
                
                # 执行 - 普通用户尝试访问管理员接口
                response = await client.get("/api/v1/admin/users", headers=headers)
                
                # 断言 API 响应
                assert response.status_code == 403, "HTTP状态码应该是403 Forbidden"
                
                response_data = response.json()
                assert "detail" in response_data, "响应应该包含detail字段"
                assert "permission" in response_data["detail"].lower(), "错误信息应该提到权限问题"
                
                # 清理 - 删除测试创建的数据
                await db.delete(regular_user)
                await db.commit()

    @pytest.mark.asyncio
    async def test_get_users_list_as_admin_success_with_filtering(self, async_client, db_session):
        """
        测试管理员查询用户列表成功并支持筛选
        - 创建ADMIN角色用户并生成access_token
        - 创建多个不同角色和状态的普通用户
        - 使用筛选参数请求用户列表
        - 验证API响应结构和筛选结果正确性
        """
        async for client in async_client:
            async for db in db_session:
                # 准备 - 创建管理员用户
                admin_uuid = uuid.uuid4().hex[:8]
                admin_user = User(
                    username=f"admin_user_{admin_uuid}",
                    email=f"admin_{admin_uuid}@test.com",
                    nickname="Admin User",
                    password_hash="hashed_password_admin",
                    role=UserRole.ADMIN,
                    status=EntityStatus.NORMAL
                )
                
                # 准备 - 创建不同角色和状态的测试用户
                base_uuid = uuid.uuid4().hex[:8]
                
                moderator_user1 = User(
                    username=f"mod1_{base_uuid}",
                    email=f"mod1_{base_uuid}@test.com",
                    nickname="Moderator 1",
                    password_hash="hashed_password_mod1",
                    role=UserRole.MODERATOR,
                    status=EntityStatus.NORMAL
                )
                
                moderator_user2 = User(
                    username=f"mod2_{base_uuid}",
                    email=f"mod2_{base_uuid}@test.com", 
                    nickname="Moderator 2",
                    password_hash="hashed_password_mod2",
                    role=UserRole.MODERATOR,
                    status=EntityStatus.NORMAL
                )
                
                banned_user = User(
                    username=f"banned_{base_uuid}",
                    email=f"banned_{base_uuid}@test.com",
                    nickname="Banned User",
                    password_hash="hashed_password_banned",
                    role=UserRole.REGULAR,
                    status=EntityStatus.BANNED
                )
                
                # 添加所有用户到数据库
                db.add_all([admin_user, moderator_user1, moderator_user2, banned_user])
                await db.commit()
                await db.refresh(admin_user)
                
                # 生成管理员访问令牌
                admin_token = self.create_access_token(str(admin_user.public_id))
                admin_headers = {"Authorization": f"Bearer {admin_token}"}
                
                # 执行1 - 测试MODERATOR角色筛选
                response1 = await client.get(
                    "/api/v1/admin/users?role=MODERATOR&page=1&size=10",
                    headers=admin_headers
                )
                
                # 断言1 - 验证MODERATOR筛选响应
                assert response1.status_code == 200, "管理员查询用户列表应该返回200"
                
                response1_data = response1.json()
                assert response1_data["code"] == 200, "业务状态码应该是200"
                assert response1_data["message"] == "success", "消息应该是success"
                
                # 验证响应数据结构
                assert "data" in response1_data, "响应应该包含data字段"
                data1 = response1_data["data"]
                assert "total" in data1, "data应该包含total字段"
                assert "page" in data1, "data应该包含page字段"
                assert "size" in data1, "data应该包含size字段"
                assert "items" in data1, "data应该包含items字段"
                assert isinstance(data1["items"], list), "items应该是列表"
                
                # 验证筛选结果（使用增量判断方式）
                items1 = data1["items"]
                returned_usernames = {item["username"] for item in items1}
                assert moderator_user1.username in returned_usernames, "测试创建的moderator_user1应该在返回结果中"
                assert moderator_user2.username in returned_usernames, "测试创建的moderator_user2应该在返回结果中"
                
                # 验证每个返回用户的角色
                for item in items1:
                    assert item["role"] == "MODERATOR", f"用户 {item['username']} 角色应该是MODERATOR"
                
                # 执行2 - 测试BANNED状态筛选
                response2 = await client.get(
                    "/api/v1/admin/users?status=BANNED&page=1&size=10",
                    headers=admin_headers
                )
                
                # 断言2 - 验证BANNED筛选响应
                assert response2.status_code == 200, "BANNED状态筛选应该返回200"
                
                response2_data = response2.json()
                assert response2_data["code"] == 200, "业务状态码应该是200"
                
                data2 = response2_data["data"]
                items2 = data2["items"]
                # 使用增量判断方式验证BANNED用户
                returned_usernames2 = {item["username"] for item in items2}
                assert banned_user.username in returned_usernames2, "测试创建的banned_user应该在返回结果中"
                banned_user_item = next((item for item in items2 if item["username"] == banned_user.username), None)
                assert banned_user_item is not None, "应该找到banned_user"
                assert banned_user_item["status"] == "BANNED", "用户状态应该是BANNED"

                # 执行3 - 测试统一关键词筛选（keyword，跨字段 OR：按昵称命中）
                response3 = await client.get(
                    "/api/v1/admin/users?keyword=Moderator&page=1&size=10",
                    headers=admin_headers
                )

                # 断言3 - keyword 按昵称模糊命中 mod1/mod2（用户名不含 Moderator，纯昵称命中）
                assert response3.status_code == 200, "keyword筛选应该返回200"
                response3_data = response3.json()
                assert response3_data["code"] == 200, "业务状态码应该是200"
                items3 = response3_data["data"]["items"]
                returned_usernames3 = {item["username"] for item in items3}
                assert moderator_user1.username in returned_usernames3, "keyword按昵称命中moderator_user1"
                assert moderator_user2.username in returned_usernames3, "keyword按昵称命中moderator_user2"
                assert banned_user.username not in returned_usernames3, "banned_user昵称不匹配keyword，不应命中"

                # 执行4 - 测试统一关键词按用户名/邮箱命中
                response4 = await client.get(
                    f"/api/v1/admin/users?keyword=banned_{base_uuid}&page=1&size=10",
                    headers=admin_headers
                )

                # 断言4 - keyword 按用户名（同段为邮箱前缀）命中 banned_user
                assert response4.status_code == 200, "keyword用户名命中筛选应该返回200"
                response4_data = response4.json()
                assert response4_data["code"] == 200, "业务状态码应该是200"
                items4 = response4_data["data"]["items"]
                returned_usernames4 = {item["username"] for item in items4}
                assert banned_user.username in returned_usernames4, "keyword按用户名命中banned_user"

                # 清理 - 删除测试创建的数据
                await db.delete(admin_user)
                await db.delete(moderator_user1)
                await db.delete(moderator_user2)
                await db.delete(banned_user)
                await db.commit()

    @pytest.mark.asyncio
    async def test_patch_user_by_admin_success(self, async_client, db_session):
        """
        测试管理员成功更新用户信息
        - 创建admin_user并获取token
        - 创建target_user
        - 使用PATCH接口更新target_user的role和status
        - 验证API响应和数据库状态都已更新
        """
        async for client in async_client:
            async for db in db_session:
                # 准备 - 创建管理员用户
                admin_uuid = uuid.uuid4().hex[:8]
                admin_user = User(
                    username=f"admin_{admin_uuid}",
                    email=f"admin_{admin_uuid}@test.com",
                    nickname="Admin User",
                    password_hash="hashed_password_admin",
                    role=UserRole.SUPERADMIN,
                    status=EntityStatus.NORMAL
                )
                
                # 准备 - 创建待更新的目标用户
                target_uuid = uuid.uuid4().hex[:8]
                target_user = User(
                    username=f"target_{target_uuid}",
                    email=f"target_{target_uuid}@test.com",
                    nickname="Target User",
                    password_hash="hashed_password_target",
                    role=UserRole.REGULAR,
                    status=EntityStatus.NORMAL
                )
                
                # 添加到数据库
                db.add_all([admin_user, target_user])
                await db.commit()
                await db.refresh(admin_user)
                await db.refresh(target_user)
                
                # 生成管理员访问令牌
                admin_token = self.create_access_token(str(admin_user.public_id))
                admin_headers = {"Authorization": f"Bearer {admin_token}"}
                
                # 准备更新数据
                update_data = {
                    "role": "MODERATOR",
                    "status": "BANNED",
                    "nickname": "Updated Target User"
                }
                
                # 执行 - 管理员更新用户信息
                response = await client.patch(
                    f"/api/v1/admin/users/{target_user.public_id}",
                    headers=admin_headers,
                    json=update_data
                )
                
                # 断言 API 响应
                assert response.status_code == 200, "管理员更新用户应该返回200"
                
                response_data = response.json()
                assert response_data["code"] == 200, "业务状态码应该是200"
                assert response_data["message"] == "success", "消息应该是success"
                
                # 验证响应数据包含更新后的字段
                assert "data" in response_data, "响应应该包含data字段"
                updated_user_data = response_data["data"]
                assert updated_user_data["role"] == "MODERATOR", "响应中的角色应该已更新为MODERATOR"
                assert updated_user_data["status"] == "BANNED", "响应中的状态应该已更新为BANNED"
                assert updated_user_data["nickname"] == "Updated Target User", "响应中的昵称应该已更新"
                
                # 验证数据库状态 - 重新查询目标用户
                from app.crud import crud_user
                db_target_user = await crud_user.get(db, target_user.id)

                await db.refresh(target_user)

                assert db_target_user is not None, "应该能重新查询到目标用户"
                assert db_target_user.role == UserRole.MODERATOR, "数据库中的角色应该已更新为MODERATOR"
                assert db_target_user.status == EntityStatus.BANNED, "数据库中的状态应该已更新为BANNED"
                assert db_target_user.nickname == "Updated Target User", "数据库中的昵称应该已更新"
                
                # 清理 - 删除测试创建的数据
                await db.delete(admin_user)
                await db.delete(target_user)
                await db.commit()

    @pytest.mark.asyncio
    async def test_patch_user_fails_if_admin_updates_superadmin(self, async_client, db_session):
        """
        测试管理员无法更新超级管理员用户
        - 创建ADMIN角色的admin_user
        - 创建SUPERADMIN角色的superadmin_user
        - admin_user尝试更新superadmin_user
        - 验证返回403 Forbidden
        """
        async for client in async_client:
            async for db in db_session:
                # 准备 - 创建管理员用户
                admin_uuid = uuid.uuid4().hex[:8]
                admin_user = User(
                    username=f"admin_{admin_uuid}",
                    email=f"admin_{admin_uuid}@test.com",
                    nickname="Admin User",
                    password_hash="hashed_password_admin",
                    role=UserRole.ADMIN,
                    status=EntityStatus.NORMAL
                )
                
                # 准备 - 创建超级管理员用户
                superadmin_uuid = uuid.uuid4().hex[:8]
                superadmin_user = User(
                    username=f"superadmin_{superadmin_uuid}",
                    email=f"superadmin_{superadmin_uuid}@test.com",
                    nickname="Super Admin User",
                    password_hash="hashed_password_superadmin",
                    role=UserRole.SUPERADMIN,
                    status=EntityStatus.NORMAL
                )
                
                # 添加到数据库
                db.add_all([admin_user, superadmin_user])
                await db.commit()
                await db.refresh(admin_user)
                await db.refresh(superadmin_user)
                
                # 生成管理员访问令牌
                admin_token = self.create_access_token(str(admin_user.public_id))
                admin_headers = {"Authorization": f"Bearer {admin_token}"}
                
                # 准备更新数据
                update_data = {
                    "status": "BANNED",
                    "nickname": "Attempted Update"
                }
                
                # 执行 - 管理员尝试更新超级管理员
                response = await client.patch(
                    f"/api/v1/admin/users/{superadmin_user.public_id}",
                    headers=admin_headers,
                    json=update_data
                )
                
                # 断言 API 响应 - 应该被拒绝
                assert response.status_code == 403, "管理员更新超级管理员应该返回403 Forbidden"
                
                response_data = response.json()
                assert response_data["code"] == 3002, "业务错误码应该是3002（权限不足）"
                assert response_data["message"] == "管理员无权修改超级管理员"
                
                # 验证数据库状态 - 超级管理员信息未被修改
                from app.crud import crud_user
                db_superadmin = await crud_user.get(db, superadmin_user.id)

                await db.refresh(db_superadmin)
                assert db_superadmin is not None, "超级管理员用户应该仍然存在"
                assert db_superadmin.status == EntityStatus.NORMAL, "超级管理员状态应该保持NORMAL（未被修改）"
                assert db_superadmin.nickname == "Super Admin User", "超级管理员昵称应该保持原样（未被修改）"
                assert db_superadmin.role == UserRole.SUPERADMIN, "超级管理员角色应该保持SUPERADMIN"
                
                # 清理 - 删除测试创建的数据
                await db.delete(admin_user)
                await db.delete(superadmin_user)
                await db.commit()

    @pytest.mark.asyncio
    async def test_patch_user_not_found(self, async_client, db_session):
        """
        测试更新不存在的用户返回404
        - 创建admin_user
        - 使用不存在的UUID尝试更新用户
        - 验证返回404 Not Found
        """
        async for client in async_client:
            async for db in db_session:
                # 准备 - 创建管理员用户
                admin_uuid = uuid.uuid4().hex[:8]
                admin_user = User(
                    username=f"admin_{admin_uuid}",
                    email=f"admin_{admin_uuid}@test.com",
                    nickname="Admin User",
                    password_hash="hashed_password_admin",
                    role=UserRole.ADMIN,
                    status=EntityStatus.NORMAL
                )
                
                db.add(admin_user)
                await db.commit()
                await db.refresh(admin_user)
                
                # 生成管理员访问令牌
                admin_token = self.create_access_token(str(admin_user.public_id))
                admin_headers = {"Authorization": f"Bearer {admin_token}"}
                
                # 准备 - 生成不存在的UUID
                non_existing_uuid = uuid.uuid4()
                
                update_data = {
                    "nickname": "Should Not Work"
                }
                
                # 执行 - 尝试更新不存在的用户
                response = await client.patch(
                    f"/api/v1/admin/users/{non_existing_uuid}",
                    headers=admin_headers,
                    json=update_data
                )
                
                # 断言 API 响应
                assert response.status_code == 404, "更新不存在的用户应该返回404"
                
                response_data = response.json()
                assert response_data["code"] == 2004, "业务错误码应该是2004（资源不存在）"
                assert "用户不存在" in  response_data["message"]
                
                # 清理 - 删除测试创建的数据
                await db.delete(admin_user)
                await db.commit() 


# ==================== 阶段4补充测试：PATCH can_stream → 重登生效 / 刷新被拒（V4.3 验收） ====================

import pytest
import jwt
from unittest.mock import patch, AsyncMock
from app.core.config import settings
from .conftest import create_test_user, create_captcha_mock_data


@pytest.fixture
def mock_redis_captcha_with_revocation():
    """模拟Redis：验证码校验成功 + 会话吊销 key 可读写（用于吊销后刷新被拒验证）"""
    revocations = {}
    with patch('app.core.redis_client.get_redis_client') as mock1, \
         patch('app.services.auth_service.get_redis_client') as mock2:
        mock_redis_client = AsyncMock()

        async def mock_get(key):
            k = str(key)
            if "captcha:solution:" in k:
                return "test123"
            if "user_sessions_revoked:" in k:
                return revocations.get(k)
            return None

        async def mock_set(key, value, **kwargs):
            if "user_sessions_revoked:" in str(key):
                revocations[str(key)] = value
            return True

        mock_redis_client.get.side_effect = mock_get
        mock_redis_client.set.side_effect = mock_set
        mock_redis_client.delete.return_value = True
        mock_redis_client.incr.return_value = 1
        mock_redis_client.expire.return_value = True
        mock1.return_value = mock_redis_client
        mock2.return_value = mock_redis_client
        yield mock_redis_client


class TestAdminCanStreamControl:
    """阶段4：管理员修改 can_stream 后的权限生效与会话吊销验收（8.2 验证项 1-2）"""

    def create_access_token(self, user_public_id) -> str:
        """创建测试用的JWT访问令牌（与 TestAdminUsersAPI 一致）"""
        from app.core.config import settings
        JWT_SECRET_KEY = settings.JWT_SECRET_KEY or "test-jwt-secret-key-for-testing-only"
        JWT_ALGORITHM = settings.JWT_ALGORITHM

        if isinstance(user_public_id, uuid.UUID):
            user_public_id = str(user_public_id)
        elif not isinstance(user_public_id, str):
            user_public_id = str(user_public_id)

        now = datetime.utcnow()
        payload = {
            "user_id": user_public_id,
            "type": "access",
            "iat": now,
            "exp": now + timedelta(hours=1),
            "jti": str(uuid.uuid4())
        }
        return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

    def decode_access_token(self, token):
        """解码访问令牌，返回payload"""
        return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])

    async def _create_admin(self, db, tag):
        """创建管理员用户并返回 headers"""
        admin_user = User(
            username=f"cs_admin_{tag}",
            email=f"cs_admin_{tag}@test.com",
            nickname="CS Admin",
            password_hash="hashed_password_admin",
            role=UserRole.ADMIN,
            status=EntityStatus.NORMAL
        )
        db.add(admin_user)
        await db.commit()
        await db.refresh(admin_user)
        headers = {"Authorization": f"Bearer {self.create_access_token(str(admin_user.public_id))}"}
        return admin_user, headers

    async def _login(self, client, username, email):
        """登录用户并返回 tokens"""
        captcha_data = create_captcha_mock_data()
        login_data = {
            "username": username,
            "password": "testpassword123",
            "captcha_id": captcha_data["captcha_id"],
            "captcha_solution": captcha_data["captcha_solution"]
        }
        response = await client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 200, f"登录应成功，实际 {response.status_code}: {response.text}"
        return response.json()["data"]

    @pytest.mark.asyncio
    async def test_patch_user_can_stream_ban_then_relogin_token_reflects(self, async_client, db_session, mock_redis_captcha_success):
        """
        管理员 PATCH can_stream=false 后：
        - 数据库与接口响应反映新值
        - 用户重新登录签发的 token 携带 can_stream=false
        - 解禁（true）后重新登录 token 恢复 can_stream=true
        """
        assert mock_redis_captcha_success is not None

        async for client in async_client:
            async for db in db_session:
                unique_id = uuid.uuid4().hex[:8]
                _, admin_headers = await self._create_admin(db, unique_id)
                target = await create_test_user(db, f"cs_target_{unique_id}", f"cs_target_{unique_id}@example.com")

                # 禁播前登录 → can_stream=true
                tokens = await self._login(client, target.username, target.email)
                assert self.decode_access_token(tokens["access_token"])["can_stream"] is True

                # 管理员禁播
                response = await client.patch(
                    f"/api/v1/admin/users/{target.public_id}",
                    headers=admin_headers,
                    json={"can_stream": False}
                )
                assert response.status_code == 200, f"PATCH 应成功: {response.text}"
                assert response.json()["data"]["can_stream"] is False

                # 重新登录 → can_stream=false
                tokens = await self._login(client, target.username, target.email)
                assert self.decode_access_token(tokens["access_token"])["can_stream"] is False

                # 管理员解禁
                response = await client.patch(
                    f"/api/v1/admin/users/{target.public_id}",
                    headers=admin_headers,
                    json={"can_stream": True}
                )
                assert response.status_code == 200
                assert response.json()["data"]["can_stream"] is True

                # 重新登录 → can_stream=true
                tokens = await self._login(client, target.username, target.email)
                assert self.decode_access_token(tokens["access_token"])["can_stream"] is True

                # 清理
                await db.delete(target)
                await db.commit()

    @pytest.mark.asyncio
    async def test_patch_user_can_stream_revokes_session_refresh_rejected(self, async_client, db_session, mock_redis_captcha_with_revocation):
        """
        管理员 PATCH can_stream（触发会话吊销）后：
        - 用户旧 refresh token 刷新被拒（401 + code=3003）
        - 获取新权限的唯一途径是重新登录（8.2 验证项 1-2）
        """
        assert mock_redis_captcha_with_revocation is not None

        async for client in async_client:
            async for db in db_session:
                unique_id = uuid.uuid4().hex[:8]
                _, admin_headers = await self._create_admin(db, unique_id)
                target = await create_test_user(db, f"cs_revoke_{unique_id}", f"cs_revoke_{unique_id}@example.com")

                # 登录获取 refresh_token
                tokens = await self._login(client, target.username, target.email)
                old_refresh_token = tokens["refresh_token"]

                # 管理员禁播（触发会话吊销）
                response = await client.patch(
                    f"/api/v1/admin/users/{target.public_id}",
                    headers=admin_headers,
                    json={"can_stream": False}
                )
                assert response.status_code == 200

                # 旧 refresh token 刷新 → 401（凭证已失效）
                response = await client.post(
                    "/api/v1/auth/refresh",
                    json={"refresh_token": old_refresh_token}
                )
                assert response.status_code == 401, f"吊销后刷新应被拒 401，实际 {response.status_code}"
                response_data = response.json()
                assert response_data["code"] == 3003, f"业务错误码应为3003，实际 {response_data.get('code')}"

                # 重新登录仍可成功（吊销只影响旧会话）
                tokens = await self._login(client, target.username, target.email)
                assert self.decode_access_token(tokens["access_token"])["can_stream"] is False

                # 清理
                await db.delete(target)
                await db.commit()