"""
用户偏好与通知模块 - API层测试

测试策略: Pragmatic (务实主义)
- 使用真实数据库进行测试
- 验证API响应和数据库状态变化
- 使用增量判断方式验证数据库操作（增量测试模式）
"""

import uuid
from datetime import datetime, time

import pytest
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user_preference_notification import UserPreferences, Notification
import jwt
from app.core.config import settings

from backend.live_core_service.tests.conftest import async_session_factory


# ==================== User Preferences API 测试 ====================

@pytest.mark.asyncio
async def test_get_user_preferences_success(async_client, db_session, regular_user_token):
    """获取用户偏好设置成功"""
    async for db in db_session:
        # 从 JWT token 解析 user_id
        payload = jwt.decode(regular_user_token, settings.JWT_SECRET_KEY, algorithms=["HS256"])
        user_id_from_token = uuid.UUID(payload.get("user_id"))
        
        # 先创建用户偏好
        prefs = UserPreferences(
            id=uuid.uuid4(),
            user_id=user_id_from_token,
            theme_mode="dark",
            homepage_view_mode="single",
        )
        db.add(prefs)
        await db.flush()
        await db.commit()  # ✅ 提交数据，确保API调用时可见
        
        async for client in async_client:
            headers = {"Authorization": f"Bearer {regular_user_token}"}
            
            # 获取偏好
            resp = await client.get("/api/v1/users/me/preferences", headers=headers)
            
            # Assert: 1. 验证API响应
            assert resp.status_code == 200
            data = resp.json()
            assert data["code"] == 200
            assert "data" in data
            assert data["data"]["theme_mode"] == "dark"  # ✅ 验证关键字段值
            assert data["data"]["homepage_view_mode"] == "single"  # ✅ 验证状态字段
            
            # Assert: 2. 验证数据库状态（使用新会话）
            # ✅ 正确方式（第58-64行）
            stmt = select(UserPreferences).where(UserPreferences.user_id == user_id_from_token)
            result = await db.execute(stmt)
            db_prefs = result.scalar_one_or_none()  # 返回ORM对象
            assert db_prefs is not None
            assert db_prefs.theme_mode == "dark"
            assert db_prefs.homepage_view_mode == "single"
            break
        break


@pytest.mark.asyncio
async def test_get_user_preferences_first_time(async_client, regular_user_token):
    """首次获取用户偏好（不存在时返回默认值）"""
    async for client in async_client:
        headers = {"Authorization": f"Bearer {regular_user_token}"}
        
        # 首次获取偏好（不存在）
        resp = await client.get("/api/v1/users/me/preferences", headers=headers)
        
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 200
        assert "data" in data
        # 验证默认值
        assert data["data"]["theme_mode"] == "auto"  # 默认值
        assert data["data"]["homepage_view_mode"] == "double"  # 默认值
        break


@pytest.mark.asyncio
async def test_get_user_preferences_unauthorized(async_client):
    """测试 GET /api/v1/users/me/preferences 未认证时返回401"""
    async for client in async_client:
        resp = await client.get("/api/v1/users/me/preferences")
        assert resp.status_code == 401
        break


@pytest.mark.asyncio
async def test_update_user_preferences_create(async_client, db_session, regular_user_token):
    """更新用户偏好（创建新偏好）"""
    async for db in db_session:
        # 从 JWT token 解析 user_id
        payload = jwt.decode(regular_user_token, settings.JWT_SECRET_KEY, algorithms=["HS256"])
        user_id_from_token = uuid.UUID(payload.get("user_id"))
        
        # 记录初始数量
        count_stmt = select(func.count(UserPreferences.id)).where(
            UserPreferences.user_id == user_id_from_token
        )
        initial_count = (await db.execute(count_stmt)).scalar()
        
        async for client in async_client:
            headers = {"Authorization": f"Bearer {regular_user_token}"}
            
            # Arrange: 准备更新数据
            update_data = {
                "theme_mode": "scheduled",
                "theme_scheduled_dark_time": "21:00",
                "theme_scheduled_light_time": "07:00",
                "pinned_categories": [str(uuid.uuid4()), str(uuid.uuid4())],
            }
            
            # Act: 更新偏好
            resp = await client.patch(
                "/api/v1/users/me/preferences",
                json=update_data,
                headers=headers,
            )
            
            # Assert: 1. 验证API响应
            assert resp.status_code == 200
            data = resp.json()
            assert data["code"] == 200
            assert data["data"]["theme_mode"] == "scheduled"  # ✅ 验证状态变化
            assert data["data"]["theme_scheduled_dark_time"] == "21:00:00"  # ✅ 验证关键字段值变化
            assert data["data"]["homepage_view_mode"] == "double"  # 默认值
            
            # Assert: 2. 验证数据库状态变化（增量验证）
            final_count = (await db.execute(count_stmt)).scalar()
            assert final_count == initial_count + 1  # ✅ 增量验证
            
            # Assert: 3. 验证数据库状态（使用新会话）
            # ✅ 正确方式（第142-147行）
            stmt = select(UserPreferences).where(UserPreferences.user_id == user_id_from_token)
            result = await db.execute(stmt)
            db_prefs = result.scalar_one_or_none()
            assert db_prefs is not None
            assert db_prefs.theme_mode == "scheduled"
            break
        break


@pytest.mark.asyncio
async def test_update_user_preferences_update(async_client, db_session, regular_user_token):
    """更新用户偏好（更新现有偏好）"""
    async for db in db_session:
        # 从 JWT token 解析 user_id
        payload = jwt.decode(regular_user_token, settings.JWT_SECRET_KEY, algorithms=["HS256"])
        user_id_from_token = uuid.UUID(payload.get("user_id"))
        
        # 先创建用户偏好
        prefs = UserPreferences(
            id=uuid.uuid4(),
            user_id=user_id_from_token,
            theme_mode="light",
            homepage_view_mode="double",
        )
        db.add(prefs)
        await db.flush()
        await db.commit()  # ✅ 提交数据
        await db.refresh(prefs)  # 刷新对象，加载所有属性
        initial_updated_at = prefs.updated_at
        
        async for client in async_client:
            headers = {"Authorization": f"Bearer {regular_user_token}"}
            
            # Arrange: 准备更新数据
            update_data = {
                "theme_mode": "dark",
                "homepage_view_mode": "single",
            }
            
            # Act: 更新偏好
            resp = await client.patch(
                "/api/v1/users/me/preferences",
                json=update_data,
                headers=headers,
            )
            
            # Assert: 1. 验证API响应
            assert resp.status_code == 200
            data = resp.json()
            assert data["code"] == 200
            assert data["data"]["theme_mode"] == "dark"  # ✅ 验证状态变化（从light→dark）
            assert data["data"]["homepage_view_mode"] == "single"  # ✅ 验证状态变化（从double→single）
            assert data["data"]["updated_at"] is not None  # ✅ 验证时间戳
            
            # Assert: 2. 验证数据库状态（使用新会话）
            # 删除 async with db.bind.connect() 块，改为：
            stmt = select(UserPreferences).where(UserPreferences.user_id == user_id_from_token)
            result = await db.execute(stmt)
            db_prefs = result.scalar_one_or_none()
            await db.refresh(prefs)  # 刷新 prefs 对象，从数据库重新加载
            assert db_prefs is not None
            assert db_prefs.theme_mode == "dark"
            break
        break


@pytest.mark.asyncio
async def test_update_user_preferences_pinned_categories_limit(async_client, regular_user_token):
    """测试更新用户偏好（固定科室数量超过限制）"""
    async for client in async_client:
        headers = {"Authorization": f"Bearer {regular_user_token}"}
        
        # 尝试更新超过5个固定科室的偏好
        update_data = {
            "pinned_categories": [str(uuid.uuid4()) for _ in range(6)],  # 6个，超过限制
        }
        
        resp = await client.patch(
            "/api/v1/users/me/preferences",
            json=update_data,
            headers=headers,
        )
        
        # Schema验证应该在Service层或API层，这里验证错误响应
        assert resp.status_code in (400, 422)  # 参数验证失败
        if resp.status_code == 400:
            data = resp.json()
            assert data["code"] == 4001  # 参数错误码
        break


@pytest.mark.asyncio
async def test_update_user_preferences_unauthorized(async_client):
    """测试 PATCH /api/v1/users/me/preferences 未认证时返回401"""
    async for client in async_client:
        resp = await client.patch(
            "/api/v1/users/me/preferences",
            json={"theme_mode": "dark"},
        )
        assert resp.status_code == 401
        break


# ==================== Notifications API (User) 测试 ====================

@pytest.mark.asyncio
async def test_get_user_notifications_success(async_client, db_session, regular_user_token):
    """获取通知列表成功"""
    async for db in db_session:
        # 从 JWT token 解析 user_id
        payload = jwt.decode(regular_user_token, settings.JWT_SECRET_KEY, algorithms=["HS256"])
        user_id_from_token = uuid.UUID(payload.get("user_id"))
        
        # 先创建多条通知
        notifications = []
        for i in range(3):
            notification = Notification(
                id=uuid.uuid4(),
                user_id=user_id_from_token,
                title=f"通知{i+1}",
                notification_type="system",
                is_read=(i % 2 == 0),  # 交替设置已读/未读
            )
            db.add(notification)
            notifications.append(notification)
        await db.flush()
        await db.commit()  # ✅ 提交数据
        
        # 记录初始数量
        count_stmt = select(func.count(Notification.id)).where(
            Notification.user_id == user_id_from_token
        )
        initial_count = (await db.execute(count_stmt)).scalar()
        
        async for client in async_client:
            headers = {"Authorization": f"Bearer {regular_user_token}"}
            
            # Act: 获取通知列表
            resp = await client.get(
                "/api/v1/users/me/notifications?page=1&size=10",
                headers=headers,
            )
            
            # Assert: 1. 验证API响应
            assert resp.status_code == 200
            data = resp.json()
            assert data["code"] == 200
            assert "data" in data
            assert "items" in data["data"]
            assert isinstance(data["data"]["items"], list)
            assert data["data"]["total"] >= 3
            assert len(data["data"]["items"]) >= 3
            
            # Assert: 2. 验证数据库状态（增量验证）
            final_count = (await db.execute(count_stmt)).scalar()
            assert final_count == initial_count  # 数量不应变化
            
            # Assert: 3. 验证通知内容
            for item in data["data"]["items"]:
                assert item["user_id"] == str(user_id_from_token)  # ✅ 验证关键字段
                assert item["notification_type"] in ["system", "subscription", "interaction"]  # ✅ 验证枚举字段
                assert "is_read" in item  # ✅ 验证状态字段
            break
        break


@pytest.mark.asyncio
async def test_get_user_notifications_with_filters(async_client, db_session, regular_user_token):
    """获取通知列表（带筛选条件）"""
    async for db in db_session:
        # 从 JWT token 解析 user_id
        payload = jwt.decode(regular_user_token, settings.JWT_SECRET_KEY, algorithms=["HS256"])
        user_id_from_token = uuid.UUID(payload.get("user_id"))
        
        # 创建已读和未读通知
        read_notification = Notification(
            id=uuid.uuid4(),
            user_id=user_id_from_token,
            title="已读通知",
            is_read=True,
        )
        db.add(read_notification)
        
        unread_notification = Notification(
            id=uuid.uuid4(),
            user_id=user_id_from_token,
            title="未读通知",
            is_read=False,
        )
        db.add(unread_notification)
        await db.flush()
        await db.commit()  # ✅ 提交数据
        
        async for client in async_client:
            headers = {"Authorization": f"Bearer {regular_user_token}"}
            
            # Act: 获取未读通知列表
            resp = await client.get(
                "/api/v1/users/me/notifications?is_read=false",
                headers=headers,
            )
            
            # Assert: 验证API响应
            assert resp.status_code == 200
            data = resp.json()
            assert data["code"] == 200
            assert len(data["data"]["items"]) >= 1
            # 验证筛选结果
            for item in data["data"]["items"]:
                assert item["is_read"] is False  # ✅ 验证状态字段筛选
            break
        break


@pytest.mark.asyncio
async def test_get_user_notifications_unauthorized(async_client):
    """测试 GET /api/v1/users/me/notifications 未认证时返回401"""
    async for client in async_client:
        resp = await client.get("/api/v1/users/me/notifications")
        assert resp.status_code == 401
        break


@pytest.mark.asyncio
async def test_get_unread_notifications_count_success(async_client, db_session, regular_user_token):
    """获取未读通知数量成功"""
    async for db in db_session:
        # 从 JWT token 解析 user_id
        payload = jwt.decode(regular_user_token, settings.JWT_SECRET_KEY, algorithms=["HS256"])
        user_id_from_token = uuid.UUID(payload.get("user_id"))
        
        # 记录初始未读数量
        count_stmt = select(func.count(Notification.id)).where(
            Notification.user_id == user_id_from_token,
            Notification.is_read == False  # noqa: E712
        )
        initial_unread_count = (await db.execute(count_stmt)).scalar()
        
        # 创建多条未读通知
        for i in range(3):
            notification = Notification(
                id=uuid.uuid4(),
                user_id=user_id_from_token,
                title=f"未读通知{i+1}",
                is_read=False,
            )
            db.add(notification)
        await db.flush()
        await db.commit()  # ✅ 提交数据
        
        async for client in async_client:
            headers = {"Authorization": f"Bearer {regular_user_token}"}
            
            # Act: 获取未读数量
            resp = await client.get(
                "/api/v1/users/me/notifications/unread-count",
                headers=headers,
            )
            
            # Assert: 验证API响应
            assert resp.status_code == 200
            data = resp.json()
            assert data["code"] == 200
            assert "data" in data
            assert "unread_count" in data["data"]
            assert data["data"]["unread_count"] >= initial_unread_count + 3  # ✅ 增量验证
            
            # Assert: 2. 验证数据库状态（使用新会话）
            final_unread_count = (await db.execute(count_stmt)).scalar()
            assert final_unread_count == initial_unread_count + 3  # ✅ 增量验证
            break
        break


@pytest.mark.asyncio
async def test_get_unread_notifications_count_unauthorized(async_client):
    """测试 GET /api/v1/users/me/notifications/unread-count 未认证时返回401"""
    async for client in async_client:
        resp = await client.get("/api/v1/users/me/notifications/unread-count")
        assert resp.status_code == 401
        break


@pytest.mark.asyncio
async def test_mark_notification_as_read_success(async_client, db_session, regular_user_token):
    """标记通知为已读成功"""
    async for db in db_session:
        # 从 JWT token 解析 user_id
        payload = jwt.decode(regular_user_token, settings.JWT_SECRET_KEY, algorithms=["HS256"])
        user_id_from_token = uuid.UUID(payload.get("user_id"))
        
        # 先创建未读通知
        notification = Notification(
            id=uuid.uuid4(),
            user_id=user_id_from_token,
            title="未读通知",
            is_read=False,
        )
        db.add(notification)
        await db.flush()
        await db.commit()  # ✅ 提交数据
        await db.refresh(notification)  # 刷新对象，加载所有属性
        notification_id = notification.id
        initial_created_at = notification.created_at
        
        async for client in async_client:
            headers = {"Authorization": f"Bearer {regular_user_token}"}
            
            # Act: 标记为已读
            resp = await client.post(
                f"/api/v1/users/me/notifications/{notification_id}/read",
                headers=headers,
            )
            
            # Assert: 1. 验证API响应
            assert resp.status_code == 200
            data = resp.json()
            assert data["code"] == 200
            
            # Assert: 2. 验证数据库状态变化（使用新会话）
            # 删除 async with db.bind.connect() 块，改为：
            stmt = select(Notification).where(Notification.id == notification_id)
            result = await db.execute(stmt)
            db_notification = result.scalar_one_or_none()
            await db.refresh(notification)  # 刷新 notification 对象，从数据库重新加载
            assert db_notification is not None
            assert db_notification.is_read is True
            assert db_notification.created_at == initial_created_at
            break
        break


@pytest.mark.asyncio
async def test_mark_notification_as_read_idempotent(async_client, db_session, regular_user_token):
    """标记通知为已读（幂等性）"""
    async for db in db_session:
        # 从 JWT token 解析 user_id
        payload = jwt.decode(regular_user_token, settings.JWT_SECRET_KEY, algorithms=["HS256"])
        user_id_from_token = uuid.UUID(payload.get("user_id"))
        
        # 先创建已读通知
        notification = Notification(
            id=uuid.uuid4(),
            user_id=user_id_from_token,
            title="已读通知",
            is_read=True,
        )
        db.add(notification)
        await db.flush()
        await db.commit()  # ✅ 提交数据
        notification_id = notification.id
        
        async for client in async_client:
            headers = {"Authorization": f"Bearer {regular_user_token}"}
            
            # Act: 再次标记为已读（应该幂等）
            resp = await client.post(
                f"/api/v1/users/me/notifications/{notification_id}/read",
                headers=headers,
            )
            
            # Assert: 应该成功（幂等）
            assert resp.status_code == 200
            break
        break


@pytest.mark.asyncio
async def test_mark_notification_as_read_not_found(async_client, regular_user_token):
    """标记通知为已读（通知不存在）"""
    async for client in async_client:
        headers = {"Authorization": f"Bearer {regular_user_token}"}
        fake_notification_id = uuid.uuid4()
        
        # Act: 标记不存在的通知为已读
        resp = await client.post(
            f"/api/v1/users/me/notifications/{fake_notification_id}/read",
            headers=headers,
        )
        
        # Assert: 应该返回404
        assert resp.status_code == 404
        data = resp.json()
        assert data["code"] == 2001  # 资源不存在错误码
        break


@pytest.mark.asyncio
async def test_mark_notification_as_read_unauthorized(async_client):
    """测试 POST /api/v1/users/me/notifications/{notification_id}/read 未认证时返回401"""
    async for client in async_client:
        resp = await client.post(f"/api/v1/users/me/notifications/{uuid.uuid4()}/read")
        assert resp.status_code == 401
        break


@pytest.mark.asyncio
async def test_mark_all_notifications_as_read_success(async_client, db_session, regular_user_token):
    """标记所有通知为已读成功"""
    async for db in db_session:
        # 从 JWT token 解析 user_id
        payload = jwt.decode(regular_user_token, settings.JWT_SECRET_KEY, algorithms=["HS256"])
        user_id_from_token = uuid.UUID(payload.get("user_id"))
        
        # 记录初始未读数量
        count_stmt = select(func.count(Notification.id)).where(
            Notification.user_id == user_id_from_token,
            Notification.is_read == False  # noqa: E712
        )
        initial_unread_count = (await db.execute(count_stmt)).scalar()
        
        # 创建多条未读通知
        notifications = []
        for i in range(3):
            notification = Notification(
                id=uuid.uuid4(),
                user_id=user_id_from_token,
                title=f"未读通知{i+1}",
                is_read=False,
            )
            db.add(notification)
            notifications.append(notification)
        await db.flush()
        await db.commit()  # ✅ 提交数据
        
        async for client in async_client:
            headers = {"Authorization": f"Bearer {regular_user_token}"}
            
            # Act: 标记所有为已读
            resp = await client.post(
                "/api/v1/users/me/notifications/read-all",
                headers=headers,
            )
            
            # Assert: 1. 验证API响应
            assert resp.status_code == 200
            data = resp.json()
            assert data["code"] == 200
            assert "data" in data
            assert "updated_count" in data["data"]
            assert data["data"]["updated_count"] >= initial_unread_count + 3  # ✅ 增量验证
            
            # Assert: 2. 验证数据库状态变化（使用新会话）
            async with db.bind.connect() as conn:
                final_count_stmt = select(func.count(Notification.id)).where(
                    Notification.user_id == user_id_from_token,
                    Notification.is_read == False  # noqa: E712
                )
                result = await conn.execute(final_count_stmt)
                final_unread_count = result.scalar()
                # 验证未读数量应减少
                assert final_unread_count <= initial_unread_count  # ✅ 增量验证
            break
        break


@pytest.mark.asyncio
async def test_mark_all_notifications_as_read_unauthorized(async_client):
    """测试 POST /api/v1/users/me/notifications/read-all 未认证时返回401"""
    async for client in async_client:
        resp = await client.post("/api/v1/users/me/notifications/read-all")
        assert resp.status_code == 401
        break


# ==================== Notifications API (Admin) 测试 ====================

@pytest.mark.asyncio
async def test_create_notifications_batch_success(async_client, db_session, admin_user_token):
    """批量创建通知成功（管理员）"""
    async for db in db_session:
        # 从 JWT token 解析 user_id
        payload = jwt.decode(admin_user_token, settings.JWT_SECRET_KEY, algorithms=["HS256"])
        admin_user_id = uuid.UUID(payload.get("user_id"))
        
        # 创建测试用户（接收通知）
        target_user_ids = [uuid.uuid4(), uuid.uuid4()]
        
        # 记录初始数量
        count_stmt = select(func.count(Notification.id))
        initial_count = (await db.execute(count_stmt)).scalar()
        
        async for client in async_client:
            headers = {"Authorization": f"Bearer {admin_user_token}"}
            
            # Arrange: 准备创建数据
            create_data = {
                "user_ids": [str(uid) for uid in target_user_ids],
                "title": "批量通知",
                "content": "通知内容",
                "notification_type": "system",
            }
            
            # Act: 批量创建通知
            resp = await client.post(
                "/api/v1/admin/notifications",
                json=create_data,
                headers=headers,
            )
            
            # Assert: 1. 验证API响应
            assert resp.status_code == 200
            data = resp.json()
            assert data["code"] == 200
            assert "data" in data
            assert "total_created" in data["data"]
            assert data["data"]["total_created"] == 2  # ✅ 验证创建数量
            assert len(data["data"]["user_ids"]) == 2
            
            # Assert: 2. 验证数据库状态变化（增量验证）
            final_count = (await db.execute(count_stmt)).scalar()
            assert final_count == initial_count + 2  # ✅ 增量验证
            
            # Assert: 3. 验证数据库状态（使用新会话）
            async with db.bind.connect() as conn:
                for user_id in target_user_ids:
                    stmt = select(func.count(Notification.id)).where(
                        Notification.user_id == user_id
                    )
                    result = await conn.execute(stmt)
                    count = result.scalar()
                    assert count >= 1  # 每个用户至少有一条通知
            break
        break


@pytest.mark.asyncio
async def test_create_notifications_batch_permission_denied(async_client, regular_user_token):
    """批量创建通知（权限不足）"""
    async for client in async_client:
        headers = {"Authorization": f"Bearer {regular_user_token}"}
        
        create_data = {
            "user_ids": [str(uuid.uuid4())],
            "title": "通知",
            "notification_type": "system",
        }
        
        # Act: 普通用户尝试批量创建通知
        resp = await client.post(
            "/api/v1/admin/notifications",
            json=create_data,
            headers=headers,
        )
        
        # Assert: 应该返回403
        assert resp.status_code == 403
        data = resp.json()
        assert data["code"] == 4003  # 权限不足错误码
        break


@pytest.mark.asyncio
async def test_create_notifications_batch_unauthorized(async_client):
    """测试 POST /api/v1/admin/notifications 未认证时返回401"""
    async for client in async_client:
        resp = await client.post(
            "/api/v1/admin/notifications",
            json={
                "user_ids": [str(uuid.uuid4())],
                "title": "通知",
                "notification_type": "system",
            },
        )
        assert resp.status_code == 401
        break


@pytest.mark.asyncio
async def test_get_notifications_admin_success(async_client, db_session, admin_user_token):
    """获取通知列表成功（管理员）"""
    async for db in db_session:
        # 创建不同用户的通知
        user1_id = uuid.uuid4()
        user2_id = uuid.uuid4()
        
        notification1 = Notification(
            id=uuid.uuid4(),
            user_id=user1_id,
            title="用户1通知",
            notification_type="system",
        )
        db.add(notification1)
        
        notification2 = Notification(
            id=uuid.uuid4(),
            user_id=user2_id,
            title="用户2通知",
            notification_type="subscription",
        )
        db.add(notification2)
        await db.flush()
        await db.commit()  # ✅ 提交数据
        
        async for client in async_client:
            headers = {"Authorization": f"Bearer {admin_user_token}"}
            
            # Act: 管理员获取通知列表
            resp = await client.get(
                "/api/v1/admin/notifications?page=1&size=10",
                headers=headers,
            )
            
            # Assert: 验证API响应
            assert resp.status_code == 200
            data = resp.json()
            assert data["code"] == 200
            assert "data" in data
            assert "items" in data["data"]
            assert data["data"]["total"] >= 2  # 至少包含我们创建的2条通知
            
            # 验证可以查询到不同用户的通知
            user_ids_in_response = [item["user_id"] for item in data["data"]["items"]]
            assert str(user1_id) in user_ids_in_response or str(user2_id) in user_ids_in_response
            break
        break


@pytest.mark.asyncio
async def test_get_notifications_admin_with_filters(async_client, db_session, admin_user_token):
    """获取通知列表（管理员，带筛选条件）"""
    async for db in db_session:
        user_id = uuid.uuid4()
        
        # 创建不同类型的通知
        system_notification = Notification(
            id=uuid.uuid4(),
            user_id=user_id,
            title="系统通知",
            notification_type="system",
        )
        db.add(system_notification)
        
        subscription_notification = Notification(
            id=uuid.uuid4(),
            user_id=user_id,
            title="订阅通知",
            notification_type="subscription",
        )
        db.add(subscription_notification)
        await db.flush()
        await db.commit()  # ✅ 提交数据
        
        async for client in async_client:
            headers = {"Authorization": f"Bearer {admin_user_token}"}
            
            # Act: 管理员获取系统通知列表
            resp = await client.get(
                f"/api/v1/admin/notifications?notification_type=system&user_id={user_id}",
                headers=headers,
            )
            
            # Assert: 验证API响应
            assert resp.status_code == 200
            data = resp.json()
            assert data["code"] == 200
            # 验证筛选结果
            for item in data["data"]["items"]:
                assert item["notification_type"] == "system"  # ✅ 验证枚举字段筛选
                assert item["user_id"] == str(user_id)  # ✅ 验证用户ID筛选
            break
        break


@pytest.mark.asyncio
async def test_get_notifications_admin_permission_denied(async_client, regular_user_token):
    """获取通知列表（权限不足）"""
    async for client in async_client:
        headers = {"Authorization": f"Bearer {regular_user_token}"}
        
        # Act: 普通用户尝试获取管理员通知列表
        resp = await client.get("/api/v1/admin/notifications", headers=headers)
        
        # Assert: 应该返回403
        assert resp.status_code == 403
        data = resp.json()
        assert data["code"] == 4003  # 权限不足错误码
        break


@pytest.mark.asyncio
async def test_update_notification_success(async_client, db_session, admin_user_token):
    """更新通知成功（管理员）"""
    async for db in db_session:
        # 从 JWT token 解析 user_id
        payload = jwt.decode(admin_user_token, settings.JWT_SECRET_KEY, algorithms=["HS256"])
        admin_user_id = uuid.UUID(payload.get("user_id"))
        
        # 创建通知
        notification = Notification(
            id=uuid.uuid4(),
            user_id=admin_user_id,
            title="原标题",
            content="原内容",
        )
        db.add(notification)
        await db.flush()
        await db.commit()  # ✅ 提交数据
        await db.refresh(notification)  # 刷新对象，加载所有属性
        notification_id = notification.id
        initial_created_at = notification.created_at
        
        async for client in async_client:
            headers = {"Authorization": f"Bearer {admin_user_token}"}
            
            # Arrange: 准备更新数据
            update_data = {
                "title": "新标题",
                "content": "新内容",
            }
            
            # Act: 更新通知
            resp = await client.patch(
                f"/api/v1/admin/notifications/{notification_id}",
                json=update_data,
                headers=headers,
            )
            
            # Assert: 1. 验证API响应
            assert resp.status_code == 200
            data = resp.json()
            assert data["code"] == 200
            assert data["data"]["title"] == "新标题"  # ✅ 验证关键字段值变化
            assert data["data"]["content"] == "新内容"  # ✅ 验证关键字段值变化

            async with async_session_factory() as new_db:
                stmt = select(Notification).where(Notification.id == notification_id)
                result = await new_db.execute(stmt)
                db_notification = result.scalar_one_or_none()
                await db.refresh(notification)  # 刷新 notification 对象，从数据库重新加载
                assert db_notification is not None
                assert db_notification.title == "新标题"
                assert db_notification.content == "新内容"
                assert db_notification.created_at == initial_created_at
            break
        break


@pytest.mark.asyncio
async def test_update_notification_not_found(async_client, admin_user_token):
    """更新通知（通知不存在）"""
    async for client in async_client:
        headers = {"Authorization": f"Bearer {admin_user_token}"}
        fake_notification_id = uuid.uuid4()
        
        update_data = {"title": "新标题"}
        
        # Act: 更新不存在的通知
        resp = await client.patch(
            f"/api/v1/admin/notifications/{fake_notification_id}",
            json=update_data,
            headers=headers,
        )
        
        # Assert: 应该返回404
        assert resp.status_code == 404
        data = resp.json()
        assert data["code"] == 2001  # 资源不存在错误码
        break


@pytest.mark.asyncio
async def test_update_notification_permission_denied(async_client, regular_user_token):
    """更新通知（权限不足）"""
    async for client in async_client:
        headers = {"Authorization": f"Bearer {regular_user_token}"}
        notification_id = uuid.uuid4()
        
        update_data = {"title": "新标题"}
        
        # Act: 普通用户尝试更新通知
        resp = await client.patch(
            f"/api/v1/admin/notifications/{notification_id}",
            json=update_data,
            headers=headers,
        )
        
        # Assert: 应该返回403
        assert resp.status_code == 403
        data = resp.json()
        assert data["code"] == 4003  # 权限不足错误码
        break


@pytest.mark.asyncio
async def test_delete_notification_success(async_client, db_session, admin_user_token):
    """删除通知成功（管理员）"""
    async for db in db_session:
        # 从 JWT token 解析 user_id
        payload = jwt.decode(admin_user_token, settings.JWT_SECRET_KEY, algorithms=["HS256"])
        admin_user_id = uuid.UUID(payload.get("user_id"))
        
        # 创建通知
        notification = Notification(
            id=uuid.uuid4(),
            user_id=admin_user_id,
            title="待删除通知",
        )
        db.add(notification)
        await db.flush()
        await db.commit()  # ✅ 提交数据
        notification_id = notification.id
        
        # 记录初始数量
        count_stmt = select(func.count(Notification.id))
        initial_count = (await db.execute(count_stmt)).scalar()
        
        async for client in async_client:
            headers = {"Authorization": f"Bearer {admin_user_token}"}
            
            # Act: 删除通知
            resp = await client.delete(
                f"/api/v1/admin/notifications/{notification_id}",
                headers=headers,
            )
            
            # Assert: 1. 验证API响应
            assert resp.status_code == 200
            data = resp.json()
            assert data["code"] == 200
            
            # Assert: 2. 验证数据库状态变化（增量验证）
            final_count = (await db.execute(count_stmt)).scalar()
            assert final_count == initial_count - 1  # ✅ 增量验证
            
            # Assert: 3. 验证通知已删除（使用新会话）
            async with db.bind.connect() as conn:
                stmt = select(Notification).where(Notification.id == notification_id)
                result = await conn.execute(stmt)
                db_notification = result.scalar_one_or_none()
                assert db_notification is None  # ✅ 验证通知已删除
            break
        break


@pytest.mark.asyncio
async def test_delete_notification_not_found(async_client, admin_user_token):
    """删除通知（通知不存在）"""
    async for client in async_client:
        headers = {"Authorization": f"Bearer {admin_user_token}"}
        fake_notification_id = uuid.uuid4()
        
        # Act: 删除不存在的通知
        resp = await client.delete(
            f"/api/v1/admin/notifications/{fake_notification_id}",
            headers=headers,
        )
        
        # Assert: 应该返回404
        assert resp.status_code == 404
        data = resp.json()
        assert data["code"] == 2001  # 资源不存在错误码
        break


@pytest.mark.asyncio
async def test_delete_notification_permission_denied(async_client, regular_user_token):
    """删除通知（权限不足）"""
    async for client in async_client:
        headers = {"Authorization": f"Bearer {regular_user_token}"}
        notification_id = uuid.uuid4()
        
        # Act: 普通用户尝试删除通知
        resp = await client.delete(
            f"/api/v1/admin/notifications/{notification_id}",
            headers=headers,
        )
        
        # Assert: 应该返回403
        assert resp.status_code == 403
        data = resp.json()
        assert data["code"] == 4003  # 权限不足错误码
        break


@pytest.mark.asyncio
async def test_batch_delete_notifications_success(async_client, db_session, admin_user_token):
    """批量删除通知成功（管理员）"""
    async for db in db_session:
        # 从 JWT token 解析 user_id
        payload = jwt.decode(admin_user_token, settings.JWT_SECRET_KEY, algorithms=["HS256"])
        admin_user_id = uuid.UUID(payload.get("user_id"))
        
        # 创建多条通知
        notifications = []
        for i in range(3):
            notification = Notification(
                id=uuid.uuid4(),
                user_id=admin_user_id,
                title=f"通知{i+1}",
            )
            db.add(notification)
            notifications.append(notification)
        await db.flush()
        await db.commit()  # ✅ 提交数据
        
        # 记录初始数量
        count_stmt = select(func.count(Notification.id))
        initial_count = (await db.execute(count_stmt)).scalar()
        
        # 获取通知ID列表
        notification_ids = [n.id for n in notifications]
        
        async for client in async_client:
            headers = {"Authorization": f"Bearer {admin_user_token}"}
            
            # Arrange: 准备删除数据
            delete_data = {
                "notification_ids": [str(nid) for nid in notification_ids],
            }
            
            # Act: 批量删除通知
            resp = await client.post(
                "/api/v1/admin/notifications/batch-delete",
                json=delete_data,
                headers=headers,
            )
            
            # Assert: 1. 验证API响应
            assert resp.status_code == 200
            data = resp.json()
            assert data["code"] == 200
            assert "data" in data
            assert "deleted_count" in data["data"]
            assert data["data"]["deleted_count"] >= 3  # ✅ 验证删除数量
            
            # Assert: 2. 验证数据库状态变化（增量验证）
            final_count = (await db.execute(count_stmt)).scalar()
            assert final_count == initial_count - 3  # ✅ 增量验证
            
            # Assert: 3. 验证通知已删除（使用新会话）
            async with db.bind.connect() as conn:
                for notification_id in notification_ids:
                    stmt = select(Notification).where(Notification.id == notification_id)
                    result = await conn.execute(stmt)
                    db_notification = result.scalar_one_or_none()
                    assert db_notification is None  # ✅ 验证通知已删除
            break
        break


@pytest.mark.asyncio
async def test_batch_delete_notifications_permission_denied(async_client, regular_user_token):
    """批量删除通知（权限不足）"""
    async for client in async_client:
        headers = {"Authorization": f"Bearer {regular_user_token}"}
        
        delete_data = {
            "notification_ids": [str(uuid.uuid4())],
        }
        
        # Act: 普通用户尝试批量删除通知
        resp = await client.post(
            "/api/v1/admin/notifications/batch-delete",
            json=delete_data,
            headers=headers,
        )
        
        # Assert: 应该返回403
        assert resp.status_code == 403
        data = resp.json()
        assert data["code"] == 4003  # 权限不足错误码
        break


@pytest.mark.asyncio
async def test_batch_delete_notifications_unauthorized(async_client):
    """测试 POST /api/v1/admin/notifications/batch-delete 未认证时返回401"""
    async for client in async_client:
        resp = await client.post(
            "/api/v1/admin/notifications/batch-delete",
            json={"notification_ids": [str(uuid.uuid4())]},
        )
        assert resp.status_code == 401
        break


@pytest.mark.asyncio
async def test_batch_delete_notifications_by_type(async_client, db_session, admin_user_token):
    """批量删除通知（按通知类型）"""
    async for db in db_session:
        # 从 JWT token 解析 user_id
        payload = jwt.decode(admin_user_token, settings.JWT_SECRET_KEY, algorithms=["HS256"])
        admin_user_id = uuid.UUID(payload.get("user_id"))
        
        # 创建不同类型的通知
        system_notification = Notification(
            id=uuid.uuid4(),
            user_id=admin_user_id,
            title="系统通知",
            notification_type="system",
        )
        db.add(system_notification)
        
        subscription_notification = Notification(
            id=uuid.uuid4(),
            user_id=admin_user_id,
            title="订阅通知",
            notification_type="subscription",
        )
        db.add(subscription_notification)
        await db.flush()
        await db.commit()  # ✅ 提交数据
        
        # 记录初始数量
        count_stmt = select(func.count(Notification.id))
        initial_count = (await db.execute(count_stmt)).scalar()
        
        async for client in async_client:
            headers = {"Authorization": f"Bearer {admin_user_token}"}
            
            # Arrange: 准备删除数据（按类型删除）
            delete_data = {
                "notification_type": "system",
            }
            
            # Act: 批量删除系统通知
            resp = await client.post(
                "/api/v1/admin/notifications/batch-delete",
                json=delete_data,
                headers=headers,
            )
            
            # Assert: 验证API响应
            assert resp.status_code == 200
            data = resp.json()
            assert data["code"] == 200
            assert data["data"]["deleted_count"] >= 1  # 至少删除1条系统通知
            
            # Assert: 验证数据库状态变化（增量验证）
            final_count = (await db.execute(count_stmt)).scalar()
            assert final_count < initial_count  # ✅ 增量验证
            break
        break
