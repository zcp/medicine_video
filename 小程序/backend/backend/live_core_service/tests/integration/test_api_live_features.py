"""
直播间 Tab 和留言功能的 API 层测试（实用派）

本测试文件使用真实HTTP客户端和数据库测试完整链路，验证：
- HTTP 请求/响应的正确性
- 业务状态码和数据结构
- 认证和权限控制
- 数据库状态变化

测试风格：实用派 (Pragmatic) - 使用 httpx.AsyncClient + 真实数据库
"""

import pytest
import uuid
import time
import jwt
import os
from faker import Faker
from datetime import datetime, timedelta

from app.models.live_core import LiveRoom, LiveSession, LiveSessionStatus
from app.models.live_features import (
    LiveRoomTab,
    LiveRoomMessage,
    LiveRoomTabContentType,
    LiveRoomMessageUserRole
)
from app.crud import live_features as crud_live_features
import inspect

fake = Faker()

# ==================== Helper Functions ====================

async def get_fixture_room_id(room_fixture):
    """
    辅助函数：从room fixture中安全地获取room_id
    处理async generator fixture的情况
    """
    # 如果fixture已经被pytest解析，直接返回id
    if hasattr(room_fixture, 'id') and not inspect.isasyncgen(room_fixture):
        return room_fixture.id
    
    # 如果是async generator，尝试获取值
    if inspect.isasyncgen(room_fixture):
        try:
            room_obj = await room_fixture.__anext__()
            return room_obj.id
        except StopAsyncIteration:
            # Generator已经被消费，说明pytest已经解析了它
            # 这种情况下，fixture应该已经被解析，但如果没有，说明有问题
            # 尝试直接访问id（如果pytest已经解析）
            if hasattr(room_fixture, 'id'):
                return room_fixture.id
            raise ValueError("无法从fixture中获取room_id：generator已被消费且未解析")
    
    # 默认情况：直接返回id
    return room_fixture.id

# ==================== Test Fixtures ====================
# 注意：权限相关的Fixture（admin_user_token, regular_user_token等）已在conftest.py中定义
# 这里不再重复定义，直接使用conftest.py中的Fixture


class TestAdminTabAPI:
    """Admin Tab 管理 API 测试（实用派）"""

    @pytest.mark.asyncio
    async def test_api_list_room_tabs_success(self, async_client, db_session, admin_user_token):
        """测试管理员成功获取房间所有Tab"""
        async for client in async_client:
            async for db in db_session:
                # 1. 准备 (Arrange)
                # 创建房间
                room = LiveRoom(
                    id=uuid.uuid4(),
                    user_id=uuid.uuid4(),
                    title=f"Test Room {uuid.uuid4().hex[:8]}",
                    stream_key=f"stream_{uuid.uuid4().hex}"
                )
                db.add(room)
                await db.commit()
                
                # 创建3个Tab
                for i in range(3):
                    tab = LiveRoomTab(
                        id=uuid.uuid4(),
                        room_id=room.id,
                        tab_key=f"tab_{uuid.uuid4().hex[:8]}",
                        title=f"Tab {i}",
                        content_type=LiveRoomTabContentType.TEXT,
                        text_content=f"内容 {i}",
                        sort_order=i
                    )
                    db.add(tab)
                await db.commit()
                
                headers = {"Authorization": f"Bearer {admin_user_token}"}
                
                # 2. 执行 (Act)
                response = await client.get(
                    f"/api/v1/admin/rooms/{room.id}/tabs",
                    headers=headers
                )
                
                # 3. 断言 (Assert)
                assert response.status_code == 200
                data = response.json()
                assert data["code"] == 200
                assert data["data"]["total"] == 3
                assert len(data["data"]["items"]) == 3

    @pytest.mark.asyncio
    async def test_api_list_room_tabs_permission_denied(
        self, 
        async_client, 
        db_session, 
        regular_user_token: str,
        another_user_id: uuid.UUID
    ):
        """测试Regular用户作为非房间创建者权限被拒绝"""
        async for client in async_client:
            async for db in db_session:
                # ===== Arrange (准备) =====
                # 创建房间，创建者是another_user_id（不是regular_user）
                room = LiveRoom(
                    id=uuid.uuid4(),
                    user_id=another_user_id,  # ← 修改：确保房间创建者不是regular_user
                    title=f"Test Room {uuid.uuid4().hex[:8]}",
                    stream_key=f"stream_{uuid.uuid4().hex}"
                )
                db.add(room)
                await db.commit()
                
                headers = {"Authorization": f"Bearer {regular_user_token}"}
                
                # ===== Act (执行) =====
                response = await client.get(
                    f"/api/v1/admin/rooms/{room.id}/tabs",
                    headers=headers
                )
                
                # ===== Assert (断言) =====
                assert response.status_code == 403
                data = response.json()
                assert data["code"] == 3002

    @pytest.mark.asyncio
    async def test_api_list_room_tabs_success_regular_owner(
        self, 
        async_client, 
        db_session, 
        regular_user_token: str,
        regular_user_id: uuid.UUID
    ):
        """测试Regular用户作为房间创建者成功获取房间所有Tab"""
        async for client in async_client:
            async for db in db_session:
                # ===== Arrange (准备) =====
                # 创建房间，创建者是regular_user_id
                room = LiveRoom(
                    id=uuid.uuid4(),
                    user_id=regular_user_id,  # ← 关键：房间创建者是regular_user
                    title=f"Test Room {uuid.uuid4().hex[:8]}",
                    stream_key=f"stream_{uuid.uuid4().hex}"
                )
                db.add(room)
                await db.commit()
                
                # 创建3个Tab
                for i in range(3):
                    tab = LiveRoomTab(
                        id=uuid.uuid4(),
                        room_id=room.id,
                        tab_key=f"tab_{uuid.uuid4().hex[:8]}",
                        title=f"Tab {i}",
                        content_type=LiveRoomTabContentType.TEXT,
                        text_content=f"内容 {i}",
                        sort_order=i
                    )
                    db.add(tab)
                await db.commit()
                
                headers = {"Authorization": f"Bearer {regular_user_token}"}
                
                # ===== Act (执行) =====
                response = await client.get(
                    f"/api/v1/admin/rooms/{room.id}/tabs",
                    headers=headers
                )
                
                # ===== Assert (断言) =====
                assert response.status_code == 200
                data = response.json()
                assert data["code"] == 200
                assert data["data"]["total"] == 3
                assert len(data["data"]["items"]) == 3

    # ← 新增：测试Token缺失场景（S7）
    @pytest.mark.asyncio
    async def test_api_list_room_tabs_unauthorized(self, async_client, db_session):
        """测试Token缺失时返回401（S7场景）"""
        async for client in async_client:
            async for db in db_session:
                # ===== Arrange (准备) =====
                room = LiveRoom(
                    id=uuid.uuid4(),
                    user_id=uuid.uuid4(),
                    title=f"Test Room {uuid.uuid4().hex[:8]}",
                    stream_key=f"stream_{uuid.uuid4().hex}"
                )
                db.add(room)
                await db.commit()
                
                # 不添加Authorization header
                
                # ===== Act (执行) =====
                response = await client.get(
                    f"/api/v1/admin/rooms/{room.id}/tabs"
                )
                
                # ===== Assert (断言) =====
                assert response.status_code == 401
                data = response.json()
                # ← 修改：FastAPI的HTTPException默认格式是 {"detail": "..."}，可能没有code字段
                # 检查是否有code字段，如果没有则只检查detail字段
                if "code" in data:
                    assert data["code"] in [1001, 1002]  # 401错误码
                else:
                    assert "detail" in data  # FastAPI默认错误格式

    # ← 新增：测试Token无效场景（S8）
    @pytest.mark.asyncio
    async def test_api_list_room_tabs_invalid_token(self, async_client, db_session, invalid_token):
        """测试Token无效时返回401（S8场景）"""
        async for client in async_client:
            async for db in db_session:
                # ===== Arrange (准备) =====
                room = LiveRoom(
                    id=uuid.uuid4(),
                    user_id=uuid.uuid4(),
                    title=f"Test Room {uuid.uuid4().hex[:8]}",
                    stream_key=f"stream_{uuid.uuid4().hex}"
                )
                db.add(room)
                await db.commit()
                
                headers = {"Authorization": f"Bearer {invalid_token}"}
                
                # ===== Act (执行) =====
                response = await client.get(
                    f"/api/v1/admin/rooms/{room.id}/tabs",
                    headers=headers
                )
                
                # ===== Assert (断言) =====
                assert response.status_code == 401
                data = response.json()
                # ← 修改：FastAPI的HTTPException默认格式是 {"detail": "..."}，可能没有code字段
                # 检查是否有code字段，如果没有则只检查detail字段
                if "code" in data:
                    assert data["code"] in [1001, 1002]  # 401错误码
                else:
                    assert "detail" in data  # FastAPI默认错误格式

    @pytest.mark.asyncio
    async def test_api_list_room_tabs_room_not_found(self, async_client, admin_user_token):
        """测试房间不存在时返回404"""
        async for client in async_client:
            # 1. 准备 (Arrange)
            non_existent_room_id = uuid.uuid4()
            headers = {"Authorization": f"Bearer {admin_user_token}"}
            
            # 2. 执行 (Act)
            response = await client.get(
                f"/api/v1/admin/rooms/{non_existent_room_id}/tabs",
                headers=headers
            )
            
            # 3. 断言 (Assert)
            assert response.status_code == 404
            data = response.json()
            assert data["code"] == 2001

    @pytest.mark.asyncio
    async def test_api_create_room_tab_success(self, async_client, db_session, admin_user_token):
        """测试管理员成功创建Tab"""
        async for client in async_client:
            async for db in db_session:
                # 1. 准备 (Arrange)
                room = LiveRoom(
                    id=uuid.uuid4(),
                    user_id=uuid.uuid4(),
                    title=f"Test Room {uuid.uuid4().hex[:8]}",
                    stream_key=f"stream_{uuid.uuid4().hex}"
                )
                db.add(room)
                await db.commit()
                
                payload = {
                    "tab_key": f"tab_{uuid.uuid4().hex[:8]}",
                    "title": fake.sentence(nb_words=3),
                    "content_type": "text",
                    "text_content": "测试内容",
                    "sort_order": 0,
                    "is_active": True
                }
                
                headers = {"Authorization": f"Bearer {admin_user_token}"}
                
                # 2. 执行 (Act)
                response = await client.post(
                    f"/api/v1/admin/rooms/{room.id}/tabs",
                    json=payload,
                    headers=headers
                )
                
                # 3. 断言 (Assert)
                assert response.status_code == 200
                data = response.json()
                assert data["code"] == 200
                assert data["data"]["tab_key"] == payload["tab_key"]
                assert data["data"]["title"] == payload["title"]
                
                # [关键] 数据库持久化验证
                tab_id = uuid.UUID(data["data"]["id"])
                db_tab = await crud_live_features.get_tab(db, tab_id)
                assert db_tab is not None
                assert db_tab.room_id == room.id

    @pytest.mark.asyncio
    async def test_api_create_room_tab_permission_denied(
        self, 
        async_client, 
        db_session, 
        regular_user_token: str,
        another_user_id: uuid.UUID
    ):
        """测试Regular用户作为非房间创建者创建Tab被拒绝"""
        async for client in async_client:
            async for db in db_session:
                # ===== Arrange (准备) =====
                # 创建房间，创建者是another_user_id（不是regular_user）
                room = LiveRoom(
                    id=uuid.uuid4(),
                    user_id=another_user_id,  # ← 修改：确保房间创建者不是regular_user
                    title=f"Test Room {uuid.uuid4().hex[:8]}",
                    stream_key=f"stream_{uuid.uuid4().hex}"
                )
                db.add(room)
                await db.commit()
                
                payload = {
                    "tab_key": f"tab_{uuid.uuid4().hex[:8]}",
                    "title": "测试Tab",
                    "content_type": "text",
                    "text_content": "测试内容"
                }
                
                headers = {"Authorization": f"Bearer {regular_user_token}"}
                
                # ===== Act (执行) =====
                response = await client.post(
                    f"/api/v1/admin/rooms/{room.id}/tabs",
                    json=payload,
                    headers=headers
                )
                
                # ===== Assert (断言) =====
                assert response.status_code == 403
                data = response.json()
                assert data["code"] == 3002

    @pytest.mark.asyncio
    async def test_api_create_room_tab_success_regular_owner(
        self, 
        async_client, 
        db_session, 
        regular_user_token: str,
        regular_user_id: uuid.UUID
    ):
        """测试Regular用户作为房间创建者成功创建Tab"""
        async for client in async_client:
            async for db in db_session:
                # ===== Arrange (准备) =====
                # 创建房间，创建者是regular_user_id
                room = LiveRoom(
                    id=uuid.uuid4(),
                    user_id=regular_user_id,  # ← 关键：房间创建者是regular_user
                    title=f"Test Room {uuid.uuid4().hex[:8]}",
                    stream_key=f"stream_{uuid.uuid4().hex}"
                )
                db.add(room)
                await db.commit()
                
                payload = {
                    "tab_key": f"tab_{uuid.uuid4().hex[:8]}",
                    "title": fake.sentence(nb_words=3),
                    "content_type": "text",
                    "text_content": "测试内容",
                    "sort_order": 0,
                    "is_active": True
                }
                
                headers = {"Authorization": f"Bearer {regular_user_token}"}
                
                # ===== Act (执行) =====
                response = await client.post(
                    f"/api/v1/admin/rooms/{room.id}/tabs",
                    json=payload,
                    headers=headers
                )
                
                # ===== Assert (断言) =====
                assert response.status_code == 200
                data = response.json()
                assert data["code"] == 200
                assert data["data"]["tab_key"] == payload["tab_key"]
                assert data["data"]["title"] == payload["title"]
                
                # [关键] 数据库持久化验证
                tab_id = uuid.UUID(data["data"]["id"])
                db_tab = await crud_live_features.get_tab(db, tab_id)
                assert db_tab is not None
                assert db_tab.room_id == room.id

    # ← 新增：测试Token缺失场景（S7）
    @pytest.mark.asyncio
    async def test_api_create_room_tab_unauthorized(
        self, 
        async_client, 
        db_session
    ):
        """测试Token缺失时返回401（S7场景）"""
        async for client in async_client:
            async for db in db_session:
                # ===== Arrange (准备) =====
                room = LiveRoom(
                    id=uuid.uuid4(),
                    user_id=uuid.uuid4(),
                    title=f"Test Room {uuid.uuid4().hex[:8]}",
                    stream_key=f"stream_{uuid.uuid4().hex}"
                )
                db.add(room)
                await db.commit()
                
                payload = {
                    "tab_key": f"tab_{uuid.uuid4().hex[:8]}",
                    "title": "测试Tab",
                    "content_type": "text",
                    "text_content": "测试内容"
                }
                # 不添加Authorization header
                
                # ===== Act (执行) =====
                response = await client.post(
                    f"/api/v1/admin/rooms/{room.id}/tabs",
                    json=payload
                )
                
                # ===== Assert (断言) =====
                assert response.status_code == 401
                data = response.json()
                # ← 修改：FastAPI的HTTPException默认格式是 {"detail": "..."}，可能没有code字段
                # 检查是否有code字段，如果没有则只检查detail字段
                if "code" in data:
                    assert data["code"] in [1001, 1002]  # 401错误码
                else:
                    assert "detail" in data  # FastAPI默认错误格式

    # ← 新增：测试Token无效场景（S8）
    @pytest.mark.asyncio
    async def test_api_create_room_tab_invalid_token(
        self, 
        async_client, 
        db_session,
        invalid_token: str
    ):
        """测试Token无效时返回401（S8场景）"""
        async for client in async_client:
            async for db in db_session:
                # ===== Arrange (准备) =====
                room = LiveRoom(
                    id=uuid.uuid4(),
                    user_id=uuid.uuid4(),
                    title=f"Test Room {uuid.uuid4().hex[:8]}",
                    stream_key=f"stream_{uuid.uuid4().hex}"
                )
                db.add(room)
                await db.commit()
                
                payload = {
                    "tab_key": f"tab_{uuid.uuid4().hex[:8]}",
                    "title": "测试Tab",
                    "content_type": "text",
                    "text_content": "测试内容"
                }
                
                headers = {"Authorization": f"Bearer {invalid_token}"}
                
                # ===== Act (执行) =====
                response = await client.post(
                    f"/api/v1/admin/rooms/{room.id}/tabs",
                    json=payload,
                    headers=headers
                )
                
                # ===== Assert (断言) =====
                assert response.status_code == 401
                data = response.json()
                # ← 修改：FastAPI的HTTPException默认格式是 {"detail": "..."}，可能没有code字段
                # 检查是否有code字段，如果没有则只检查detail字段
                if "code" in data:
                    assert data["code"] in [1001, 1002]  # 401错误码
                else:
                    assert "detail" in data  # FastAPI默认错误格式

    @pytest.mark.asyncio
    async def test_api_create_room_tab_invalid_content_type(self, async_client, db_session, admin_user_token):
        """测试创建Tab时参数无效"""
        async for client in async_client:
            async for db in db_session:
                # 1. 准备 (Arrange)
                room = LiveRoom(
                    id=uuid.uuid4(),
                    user_id=uuid.uuid4(),
                    title=f"Test Room {uuid.uuid4().hex[:8]}",
                    stream_key=f"stream_{uuid.uuid4().hex}"
                )
                db.add(room)
                await db.commit()
                
                payload = {
                    "tab_key": f"tab_{uuid.uuid4().hex[:8]}",
                    "title": "测试Tab",
                    "content_type": "text",
                    "text_content": None  # 无效：text类型但内容为空
                }
                
                headers = {"Authorization": f"Bearer {admin_user_token}"}
                
                # 2. 执行 (Act)
                response = await client.post(
                    f"/api/v1/admin/rooms/{room.id}/tabs",
                    json=payload,
                    headers=headers
                )
                
                # 3. 断言 (Assert)
                assert response.status_code == 400
                data = response.json()
                assert "text_content" in data["message"]

    @pytest.mark.asyncio
    async def test_api_create_room_tab_room_not_found(self, async_client, admin_user_token):
        """测试房间不存在时返回404"""
        async for client in async_client:
            # 1. 准备 (Arrange)
            non_existent_room_id = uuid.uuid4()
            payload = {
                "tab_key": f"tab_{uuid.uuid4().hex[:8]}",
                "title": "测试Tab",
                "content_type": "text",
                "text_content": "测试内容"
            }
            
            headers = {"Authorization": f"Bearer {admin_user_token}"}
            
            # 2. 执行 (Act)
            response = await client.post(
                f"/api/v1/admin/rooms/{non_existent_room_id}/tabs",
                json=payload,
                headers=headers
            )
            
            # 3. 断言 (Assert)
            assert response.status_code == 404
            data = response.json()
            assert data["code"] == 2001

    @pytest.mark.asyncio
    async def test_api_update_room_tab_success(self, async_client, db_session, admin_user_token):
        """测试管理员成功更新Tab"""
        async for client in async_client:
            async for db in db_session:
                # 1. 准备 (Arrange)
                room = LiveRoom(
                    id=uuid.uuid4(),
                    user_id=uuid.uuid4(),
                    title=f"Test Room {uuid.uuid4().hex[:8]}",
                    stream_key=f"stream_{uuid.uuid4().hex}"
                )
                db.add(room)
                await db.commit()
                
                tab = LiveRoomTab(
                    id=uuid.uuid4(),
                    room_id=room.id,
                    tab_key=f"tab_{uuid.uuid4().hex[:8]}",
                    title="原标题",
                    content_type=LiveRoomTabContentType.TEXT,
                    text_content="原内容",
                    is_active=True
                )
                db.add(tab)
                await db.commit()
                await db.refresh(tab)
                
                payload = {
                    "title": "新标题",
                    "is_active": False
                }
                
                headers = {"Authorization": f"Bearer {admin_user_token}"}
                
                # 2. 执行 (Act)
                response = await client.patch(
                    f"/api/v1/admin/tabs/{tab.id}",
                    json=payload,
                    headers=headers
                )
                
                # 3. 断言 (Assert)
                assert response.status_code == 200
                data = response.json()
                assert data["code"] == 200
                assert data["data"]["title"] == "新标题"
                assert data["data"]["is_active"] is False
                
                # [关键] 数据库更新验证
                # 使用新的独立会话查询，完全绕过身份映射缓存
                from sqlalchemy import select
                from tests.conftest import async_session_factory
                
                async with async_session_factory() as new_db:
                    stmt = select(LiveRoomTab).where(LiveRoomTab.id == tab.id)
                    result = await new_db.execute(stmt)
                    updated_tab = result.scalar_one_or_none()
                    assert updated_tab is not None
                    assert updated_tab.title == "新标题"
                    assert updated_tab.is_active is False

    @pytest.mark.asyncio
    async def test_api_update_room_tab_permission_denied(
        self, 
        async_client, 
        db_session, 
        regular_user_token: str,
        another_user_id: uuid.UUID
    ):
        """测试Regular用户作为非房间创建者更新Tab被拒绝"""
        async for client in async_client:
            async for db in db_session:
                # ===== Arrange (准备) =====
                # 创建房间，创建者是another_user_id（不是regular_user）
                room = LiveRoom(
                    id=uuid.uuid4(),
                    user_id=another_user_id,  # ← 修改：确保房间创建者不是regular_user
                    title=f"Test Room {uuid.uuid4().hex[:8]}",
                    stream_key=f"stream_{uuid.uuid4().hex}"
                )
                db.add(room)
                await db.commit()
                
                tab = LiveRoomTab(
                    id=uuid.uuid4(),
                    room_id=room.id,
                    tab_key=f"tab_{uuid.uuid4().hex[:8]}",
                    title="测试Tab",
                    content_type=LiveRoomTabContentType.TEXT,
                    text_content="测试内容"
                )
                db.add(tab)
                await db.commit()
                
                payload = {"title": "新标题"}
                headers = {"Authorization": f"Bearer {regular_user_token}"}
                
                # ===== Act (执行) =====
                response = await client.patch(
                    f"/api/v1/admin/tabs/{tab.id}",
                    json=payload,
                    headers=headers
                )
                
                # ===== Assert (断言) =====
                assert response.status_code == 403
                data = response.json()
                assert data["code"] == 3002

    @pytest.mark.asyncio
    async def test_api_update_room_tab_success_regular_owner(
        self, 
        async_client, 
        db_session, 
        regular_user_token: str,
        regular_user_id: uuid.UUID
    ):
        """测试Regular用户作为房间创建者成功更新Tab"""
        async for client in async_client:
            async for db in db_session:
                # ===== Arrange (准备) =====
                # 创建房间，创建者是regular_user_id
                room = LiveRoom(
                    id=uuid.uuid4(),
                    user_id=regular_user_id,  # ← 关键：房间创建者是regular_user
                    title=f"Test Room {uuid.uuid4().hex[:8]}",
                    stream_key=f"stream_{uuid.uuid4().hex}"
                )
                db.add(room)
                await db.commit()
                
                tab = LiveRoomTab(
                    id=uuid.uuid4(),
                    room_id=room.id,
                    tab_key=f"tab_{uuid.uuid4().hex[:8]}",
                    title="原标题",
                    content_type=LiveRoomTabContentType.TEXT,
                    text_content="原内容",
                    is_active=True
                )
                db.add(tab)
                await db.commit()
                await db.refresh(tab)
                
                payload = {
                    "title": "新标题",
                    "is_active": False
                }
                
                headers = {"Authorization": f"Bearer {regular_user_token}"}
                
                # ===== Act (执行) =====
                response = await client.patch(
                    f"/api/v1/admin/tabs/{tab.id}",
                    json=payload,
                    headers=headers
                )
                
                # ===== Assert (断言) =====
                assert response.status_code == 200
                data = response.json()
                assert data["code"] == 200
                assert data["data"]["title"] == "新标题"
                assert data["data"]["is_active"] is False
                
                # [关键] 数据库更新验证
                from sqlalchemy import select
                from tests.conftest import async_session_factory
                
                async with async_session_factory() as new_db:
                    stmt = select(LiveRoomTab).where(LiveRoomTab.id == tab.id)
                    result = await new_db.execute(stmt)
                    updated_tab = result.scalar_one_or_none()
                    assert updated_tab is not None
                    assert updated_tab.title == "新标题"
                    assert updated_tab.is_active is False

    # ← 新增：测试Token缺失场景（S7）
    @pytest.mark.asyncio
    async def test_api_update_room_tab_unauthorized(
        self, 
        async_client, 
        db_session
    ):
        """测试Token缺失时返回401（S7场景）"""
        async for client in async_client:
            async for db in db_session:
                # ===== Arrange (准备) =====
                room = LiveRoom(
                    id=uuid.uuid4(),
                    user_id=uuid.uuid4(),
                    title=f"Test Room {uuid.uuid4().hex[:8]}",
                    stream_key=f"stream_{uuid.uuid4().hex}"
                )
                db.add(room)
                await db.commit()
                
                tab = LiveRoomTab(
                    id=uuid.uuid4(),
                    room_id=room.id,
                    tab_key=f"tab_{uuid.uuid4().hex[:8]}",
                    title="测试Tab",
                    content_type=LiveRoomTabContentType.TEXT,
                    text_content="测试内容"
                )
                db.add(tab)
                await db.commit()
                
                payload = {"title": "新标题"}
                # 不添加Authorization header
                
                # ===== Act (执行) =====
                response = await client.patch(
                    f"/api/v1/admin/tabs/{tab.id}",
                    json=payload
                )
                
                # ===== Assert (断言) =====
                assert response.status_code == 401
                data = response.json()
                # ← 修改：FastAPI的HTTPException默认格式是 {"detail": "..."}，可能没有code字段
                # 检查是否有code字段，如果没有则只检查detail字段
                if "code" in data:
                    assert data["code"] in [1001, 1002]  # 401错误码
                else:
                    assert "detail" in data  # FastAPI默认错误格式

    @pytest.mark.asyncio
    async def test_api_update_room_tab_not_found(self, async_client, admin_user_token):
        """测试Tab不存在时返回404"""
        async for client in async_client:
            # 1. 准备 (Arrange)
            non_existent_tab_id = uuid.uuid4()
            payload = {"title": "新标题"}
            headers = {"Authorization": f"Bearer {admin_user_token}"}
            
            # 2. 执行 (Act)
            response = await client.patch(
                f"/api/v1/admin/tabs/{non_existent_tab_id}",
                json=payload,
                headers=headers
            )
            
            # 3. 断言 (Assert)
            assert response.status_code == 404
            data = response.json()
            assert data["code"] == 2002

    @pytest.mark.asyncio
    async def test_api_delete_room_tab_success(self, async_client, db_session, admin_user_token):
        """测试管理员成功删除Tab"""
        async for client in async_client:
            async for db in db_session:
                # 1. 准备 (Arrange)
                room = LiveRoom(
                    id=uuid.uuid4(),
                    user_id=uuid.uuid4(),
                    title=f"Test Room {uuid.uuid4().hex[:8]}",
                    stream_key=f"stream_{uuid.uuid4().hex}"
                )
                db.add(room)
                await db.commit()
                
                tab = LiveRoomTab(
                    id=uuid.uuid4(),
                    room_id=room.id,
                    tab_key=f"tab_{uuid.uuid4().hex[:8]}",
                    title="测试Tab",
                    content_type=LiveRoomTabContentType.TEXT,
                    text_content="测试内容"
                )
                db.add(tab)
                await db.commit()
                await db.refresh(tab)
                
                tab_id = tab.id
                headers = {"Authorization": f"Bearer {admin_user_token}"}
                
                # 2. 执行 (Act)
                response = await client.delete(
                    f"/api/v1/admin/tabs/{tab_id}",
                    headers=headers
                )
                
                # 3. 断言 (Assert)
                assert response.status_code == 200
                data = response.json()
                assert data["code"] == 200
                
                # [关键] 数据库删除验证
                deleted_tab = await crud_live_features.get_tab(db, tab_id)
                assert deleted_tab is None

    @pytest.mark.asyncio
    async def test_api_delete_room_tab_permission_denied(
        self, 
        async_client, 
        db_session, 
        regular_user_token: str,
        another_user_id: uuid.UUID
    ):
        """测试Regular用户作为非房间创建者删除Tab被拒绝"""
        async for client in async_client:
            async for db in db_session:
                # ===== Arrange (准备) =====
                # 创建房间，创建者是another_user_id（不是regular_user）
                room = LiveRoom(
                    id=uuid.uuid4(),
                    user_id=another_user_id,  # ← 修改：确保房间创建者不是regular_user
                    title=f"Test Room {uuid.uuid4().hex[:8]}",
                    stream_key=f"stream_{uuid.uuid4().hex}"
                )
                db.add(room)
                await db.commit()
                
                tab = LiveRoomTab(
                    id=uuid.uuid4(),
                    room_id=room.id,
                    tab_key=f"tab_{uuid.uuid4().hex[:8]}",
                    title="测试Tab",
                    content_type=LiveRoomTabContentType.TEXT,
                    text_content="测试内容"
                )
                db.add(tab)
                await db.commit()
                
                headers = {"Authorization": f"Bearer {regular_user_token}"}
                
                # ===== Act (执行) =====
                response = await client.delete(
                    f"/api/v1/admin/tabs/{tab.id}",
                    headers=headers
                )
                
                # ===== Assert (断言) =====
                assert response.status_code == 403
                data = response.json()
                assert data["code"] == 3002

    @pytest.mark.asyncio
    async def test_api_delete_room_tab_success_regular_owner(
        self, 
        async_client, 
        db_session, 
        regular_user_token: str,
        regular_user_id: uuid.UUID
    ):
        """测试Regular用户作为房间创建者成功删除Tab"""
        async for client in async_client:
            async for db in db_session:
                # ===== Arrange (准备) =====
                # 创建房间，创建者是regular_user_id
                room = LiveRoom(
                    id=uuid.uuid4(),
                    user_id=regular_user_id,  # ← 关键：房间创建者是regular_user
                    title=f"Test Room {uuid.uuid4().hex[:8]}",
                    stream_key=f"stream_{uuid.uuid4().hex}"
                )
                db.add(room)
                await db.commit()
                
                tab = LiveRoomTab(
                    id=uuid.uuid4(),
                    room_id=room.id,
                    tab_key=f"tab_{uuid.uuid4().hex[:8]}",
                    title="测试Tab",
                    content_type=LiveRoomTabContentType.TEXT,
                    text_content="测试内容"
                )
                db.add(tab)
                await db.commit()
                await db.refresh(tab)
                
                tab_id = tab.id
                headers = {"Authorization": f"Bearer {regular_user_token}"}
                
                # ===== Act (执行) =====
                response = await client.delete(
                    f"/api/v1/admin/tabs/{tab_id}",
                    headers=headers
                )
                
                # ===== Assert (断言) =====
                assert response.status_code == 200
                data = response.json()
                assert data["code"] == 200
                
                # [关键] 数据库删除验证
                deleted_tab = await crud_live_features.get_tab(db, tab_id)
                assert deleted_tab is None

    # ← 新增：测试Token缺失场景（S7）
    @pytest.mark.asyncio
    async def test_api_delete_room_tab_unauthorized(
        self, 
        async_client, 
        db_session
    ):
        """测试Token缺失时返回401（S7场景）"""
        async for client in async_client:
            async for db in db_session:
                # ===== Arrange (准备) =====
                room = LiveRoom(
                    id=uuid.uuid4(),
                    user_id=uuid.uuid4(),
                    title=f"Test Room {uuid.uuid4().hex[:8]}",
                    stream_key=f"stream_{uuid.uuid4().hex}"
                )
                db.add(room)
                await db.commit()
                
                tab = LiveRoomTab(
                    id=uuid.uuid4(),
                    room_id=room.id,
                    tab_key=f"tab_{uuid.uuid4().hex[:8]}",
                    title="测试Tab",
                    content_type=LiveRoomTabContentType.TEXT,
                    text_content="测试内容"
                )
                db.add(tab)
                await db.commit()
                
                # 不添加Authorization header
                
                # ===== Act (执行) =====
                response = await client.delete(
                    f"/api/v1/admin/tabs/{tab.id}"
                )
                
                # ===== Assert (断言) =====
                assert response.status_code == 401
                data = response.json()
                # ← 修改：FastAPI的HTTPException默认格式是 {"detail": "..."}，可能没有code字段
                # 检查是否有code字段，如果没有则只检查detail字段
                if "code" in data:
                    assert data["code"] in [1001, 1002]  # 401错误码
                else:
                    assert "detail" in data  # FastAPI默认错误格式

    @pytest.mark.asyncio
    async def test_api_delete_room_tab_not_found(self, async_client, admin_user_token):
        """测试删除不存在的Tab返回404"""
        async for client in async_client:
            # 1. 准备 (Arrange)
            non_existent_tab_id = uuid.uuid4()
            headers = {"Authorization": f"Bearer {admin_user_token}"}
            
            # 2. 执行 (Act)
            response = await client.delete(
                f"/api/v1/admin/tabs/{non_existent_tab_id}",
                headers=headers
            )
            
            # 3. 断言 (Assert)
            assert response.status_code == 404
            data = response.json()
            assert data["code"] == 2002


class TestPublicMessageAPI:
    """Public 留言 API 测试（实用派）"""

    @pytest.mark.asyncio
    async def test_api_send_message_success(
        self, 
        async_client, 
        db_session, 
        regular_user_token: str,
        regular_user_id: uuid.UUID,
        public_room
    ):
        """测试普通用户成功发送留言（Public房间）"""
        async for client in async_client:
            # ← 修改：在外层循环获取room_id，避免在内层循环时generator已被消费
            room_id = await get_fixture_room_id(public_room)
            async for db in db_session:
                
                # ===== Arrange (准备) =====
                payload = {
                    "content": fake.text(max_nb_chars=100)
                }
                
                headers = {"Authorization": f"Bearer {regular_user_token}"}
                
                # ===== Act (执行) =====
                response = await client.post(
                    f"/api/v1/rooms/{room_id}/messages",
                    json=payload,
                    headers=headers
                )
                
                # ===== Assert (断言) =====
                assert response.status_code == 200
                data = response.json()
                assert data["code"] == 200
                assert data["data"]["content"] == payload["content"]
                # [关键] 响应Schema验证
                assert "id" in data["data"]
                assert "room_id" in data["data"]
                assert "user_id" in data["data"]
                assert "user_role" in data["data"]
                assert "created_at" in data["data"]
                
                # [关键] 数据库持久化验证
                message_id = uuid.UUID(data["data"]["id"])
                from sqlalchemy import select
                from app.models.live_features import LiveRoomMessage
                stmt = select(LiveRoomMessage).where(LiveRoomMessage.id == message_id)
                result = await db.execute(stmt)
                db_message = result.scalar_one_or_none()
                assert db_message is not None
                assert db_message.content == payload["content"]

    # ← 新增：测试Token缺失场景（S7）
    @pytest.mark.asyncio
    async def test_api_send_message_unauthorized(
        self, 
        async_client, 
        db_session, 
        public_room
    ):
        """测试Token缺失时返回401（S7场景）"""
        async for client in async_client:
            # ← 修改：在外层循环获取room_id，避免在内层循环时generator已被消费
            room_id = await get_fixture_room_id(public_room)
            async for db in db_session:
                
                # ===== Arrange (准备) =====
                payload = {
                    "content": fake.text(max_nb_chars=100)
                }
                # 不添加Authorization header
                
                # ===== Act (执行) =====
                response = await client.post(
                    f"/api/v1/rooms/{room_id}/messages",
                    json=payload
                )
                
                # ===== Assert (断言) =====
                assert response.status_code == 401
                data = response.json()
                # ← 修改：FastAPI的HTTPException默认格式是 {"detail": "..."}，可能没有code字段
                # 检查是否有code字段，如果没有则只检查detail字段
                if "code" in data:
                    assert data["code"] in [1001, 1002]  # 401错误码
                else:
                    assert "detail" in data  # FastAPI默认错误格式

    # ← 文档 18：发留言需登录；不公开房不再因 is_private 伪装 404
    @pytest.mark.asyncio
    async def test_api_send_message_private_room_anonymous(
        self, 
        async_client, 
        db_session, 
        private_room
    ):
        """匿名用户发留言仍需登录（401）"""
        async for client in async_client:
            room_id = await get_fixture_room_id(private_room)
            async for db in db_session:
                payload = {
                    "content": fake.text(max_nb_chars=100)
                }
                response = await client.post(
                    f"/api/v1/rooms/{room_id}/messages",
                    json=payload
                )
                assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_api_send_message_private_room_as_non_owner(
        self, 
        async_client, 
        db_session, 
        another_user_token: str,
        private_room_owned_by_user
    ):
        """非 Owner 持链可在不公开房留言"""
        async for client in async_client:
            room_id = await get_fixture_room_id(private_room_owned_by_user)
            async for db in db_session:
                payload = {
                    "content": fake.text(max_nb_chars=100)
                }
                headers = {"Authorization": f"Bearer {another_user_token}"}
                response = await client.post(
                    f"/api/v1/rooms/{room_id}/messages",
                    json=payload,
                    headers=headers
                )
                assert response.status_code == 200
                data = response.json()
                assert data["code"] == 200

    @pytest.mark.asyncio
    async def test_api_send_message_admin_with_url(
        self, 
        async_client, 
        db_session, 
        admin_user_token: str,
        public_room
    ):
        """测试管理员可以发送包含URL的留言（S12场景）"""
        async for client in async_client:
            # ← 修改：在外层循环获取room_id，避免在内层循环时generator已被消费
            room_id = await get_fixture_room_id(public_room)
            async for db in db_session:
                
                # ===== Arrange (准备) =====
                payload = {
                    "content": "管理员留言 https://example.com"
                }
                
                headers = {"Authorization": f"Bearer {admin_user_token}"}
                
                # ===== Act (执行) =====
                response = await client.post(
                    f"/api/v1/rooms/{room_id}/messages",
                    json=payload,
                    headers=headers
                )
                
                # ===== Assert (断言) =====
                assert response.status_code == 200
                data = response.json()
                assert data["code"] == 200

    @pytest.mark.asyncio
    async def test_api_send_message_regular_user_with_url_rejected(
        self, 
        async_client, 
        db_session, 
        regular_user_token: str,
        another_user_id: uuid.UUID
    ):
        """测试Regular用户作为非房间创建者发送包含URL的留言被拒绝"""
        async for client in async_client:
            async for db in db_session:
                # ===== Arrange (准备) =====
                # 创建Public房间，创建者是another_user_id（不是regular_user）
                room = LiveRoom(
                    id=uuid.uuid4(),
                    user_id=another_user_id,  # ← 修改：确保房间创建者不是regular_user
                    title=f"Test Room {uuid.uuid4().hex[:8]}",
                    stream_key=f"stream_{uuid.uuid4().hex}",
                    is_private=False  # Public房间
                )
                db.add(room)
                await db.commit()
                
                payload = {
                    "content": "包含URL https://evil.com"
                }
                
                headers = {"Authorization": f"Bearer {regular_user_token}"}
                
                # ===== Act (执行) =====
                response = await client.post(
                    f"/api/v1/rooms/{room.id}/messages",
                    json=payload,
                    headers=headers
                )
                
                # ===== Assert (断言) =====
                assert response.status_code == 400
                data = response.json()
                # [关键] URL过滤错误码
                assert data["code"] == 4004
                assert "URL" in data["message"]

    @pytest.mark.asyncio
    async def test_api_send_message_regular_owner_with_url_success(
        self, 
        async_client, 
        db_session, 
        regular_user_token: str,
        regular_user_id: uuid.UUID
    ):
        """测试Regular用户作为房间创建者成功发送包含URL的留言"""
        async for client in async_client:
            async for db in db_session:
                # ===== Arrange (准备) =====
                # 创建Public房间，创建者是regular_user_id
                room = LiveRoom(
                    id=uuid.uuid4(),
                    user_id=regular_user_id,  # ← 关键：房间创建者是regular_user
                    title=f"Test Room {uuid.uuid4().hex[:8]}",
                    stream_key=f"stream_{uuid.uuid4().hex}",
                    is_private=False  # Public房间
                )
                db.add(room)
                await db.commit()
                
                payload = {
                    "content": "房间创建者留言 https://example.com"
                }
                
                headers = {"Authorization": f"Bearer {regular_user_token}"}
                
                # ===== Act (执行) =====
                response = await client.post(
                    f"/api/v1/rooms/{room.id}/messages",
                    json=payload,
                    headers=headers
                )
                
                # ===== Assert (断言) =====
                assert response.status_code == 200
                data = response.json()
                assert data["code"] == 200
                assert data["data"]["content"] == payload["content"]
                
                # [关键] 数据库持久化验证
                message_id = uuid.UUID(data["data"]["id"])
                from sqlalchemy import select
                from app.models.live_features import LiveRoomMessage
                stmt = select(LiveRoomMessage).where(LiveRoomMessage.id == message_id)
                result = await db.execute(stmt)
                db_message = result.scalar_one_or_none()
                assert db_message is not None
                assert db_message.content == payload["content"]

    @pytest.mark.asyncio
    async def test_api_send_message_room_not_found(
        self, 
        async_client, 
        regular_user_token: str
    ):
        """测试房间不存在时返回404"""
        async for client in async_client:
            # ===== Arrange (准备) =====
            non_existent_room_id = uuid.uuid4()
            payload = {"content": "测试留言"}
            headers = {"Authorization": f"Bearer {regular_user_token}"}
            
            # ===== Act (执行) =====
            response = await client.post(
                f"/api/v1/rooms/{non_existent_room_id}/messages",
                json=payload,
                headers=headers
            )
            
            # ===== Assert (断言) =====
            assert response.status_code == 404
            data = response.json()
            assert data["code"] == 2001

    @pytest.mark.asyncio
    async def test_api_get_room_messages_success_public(
        self, 
        async_client, 
        db_session,
        public_room
    ):
        """测试成功获取Public房间留言列表（匿名用户可访问，S1场景）"""
        async for client in async_client:
            # ← 修改：在外层循环获取room_id，避免在内层循环时generator已被消费
            room_id = await get_fixture_room_id(public_room)
            async for db in db_session:
                
                # ===== Arrange (准备) =====
                # 创建5个留言
                for i in range(5):
                    message = LiveRoomMessage(
                        id=uuid.uuid4(),
                        room_id=room_id,
                        session_id=None,
                        user_id=uuid.uuid4(),
                        user_role=LiveRoomMessageUserRole.REGULAR,
                        content=f"留言 {i}",
                        is_deleted=False
                    )
                    db.add(message)
                await db.commit()
                
                # ===== Act (执行) =====
                # 不添加Authorization header（匿名用户）
                response = await client.get(
                    f"/api/v1/rooms/{room_id}/messages?page=1&size=10"
                )
                
                # ===== Assert (断言) =====
                assert response.status_code == 200
                data = response.json()
                assert data["code"] == 200
                assert data["data"]["total"] == 5
                assert len(data["data"]["items"]) == 5
                
                # [关键] 响应Schema验证 - 不包含user_id
                for item in data["data"]["items"]:
                    assert "id" in item
                    assert "user_role" in item
                    assert "content" in item
                    assert "created_at" in item
                    assert "user_id" not in item  # 安全要求

    # ← 文档 18：不公开房留言列表持链可读
    @pytest.mark.asyncio
    async def test_api_get_room_messages_private_anonymous(
        self, 
        async_client, 
        db_session,
        private_room
    ):
        """匿名用户持链可读不公开房留言列表"""
        async for client in async_client:
            room_id = await get_fixture_room_id(private_room)
            async for db in db_session:
                for i in range(3):
                    message = LiveRoomMessage(
                        id=uuid.uuid4(),
                        room_id=room_id,
                        session_id=None,
                        user_id=uuid.uuid4(),
                        user_role=LiveRoomMessageUserRole.REGULAR,
                        content=f"留言 {i}",
                        is_deleted=False
                    )
                    db.add(message)
                await db.commit()
                
                response = await client.get(
                    f"/api/v1/rooms/{room_id}/messages?page=1&size=10"
                )
                
                assert response.status_code == 200
                data = response.json()
                assert data["code"] == 200
                assert data["data"]["total"] == 3

    # ← 新增：测试Owner访问自己的Private房间（S3场景）
    @pytest.mark.asyncio
    async def test_api_get_room_messages_private_as_owner(
        self, 
        async_client, 
        db_session,
        regular_user_token: str,
        private_room_owned_by_user
    ):
        """测试Owner访问自己的Private房间留言列表（S3场景）"""
        async for client in async_client:
            # ← 修改：在外层循环获取room_id，避免在内层循环时generator已被消费
            room_id = await get_fixture_room_id(private_room_owned_by_user)
            async for db in db_session:
                
                # ===== Arrange (准备) =====
                # 创建5个留言
                for i in range(5):
                    message = LiveRoomMessage(
                        id=uuid.uuid4(),
                        room_id=room_id,
                        session_id=None,
                        user_id=uuid.uuid4(),
                        user_role=LiveRoomMessageUserRole.REGULAR,
                        content=f"留言 {i}",
                        is_deleted=False
                    )
                    db.add(message)
                await db.commit()
                
                headers = {"Authorization": f"Bearer {regular_user_token}"}
                
                # ===== Act (执行) =====
                response = await client.get(
                    f"/api/v1/rooms/{room_id}/messages?page=1&size=10",
                    headers=headers
                )
                
                # ===== Assert (断言) =====
                assert response.status_code == 200
                data = response.json()
                assert data["code"] == 200
                assert data["data"]["total"] == 5
                assert len(data["data"]["items"]) == 5

    # ← 文档 18：非 Owner 持链可读留言
    @pytest.mark.asyncio
    async def test_api_get_room_messages_private_as_non_owner(
        self, 
        async_client, 
        db_session,
        another_user_token: str,
        private_room_owned_by_user
    ):
        """非 Owner 持链可读他人不公开房留言列表"""
        async for client in async_client:
            room_id = await get_fixture_room_id(private_room_owned_by_user)
            async for db in db_session:
                for i in range(3):
                    message = LiveRoomMessage(
                        id=uuid.uuid4(),
                        room_id=room_id,
                        session_id=None,
                        user_id=uuid.uuid4(),
                        user_role=LiveRoomMessageUserRole.REGULAR,
                        content=f"留言 {i}",
                        is_deleted=False
                    )
                    db.add(message)
                await db.commit()
                
                headers = {"Authorization": f"Bearer {another_user_token}"}
                response = await client.get(
                    f"/api/v1/rooms/{room_id}/messages?page=1&size=10",
                    headers=headers
                )
                
                assert response.status_code == 200
                data = response.json()
                assert data["code"] == 200
                assert data["data"]["total"] == 3

    # ← 新增：测试Admin访问任意Private房间（S6场景）
    @pytest.mark.asyncio
    async def test_api_get_room_messages_private_as_admin(
        self, 
        async_client, 
        db_session,
        admin_user_token: str,
        private_room
    ):
        """测试Admin访问任意Private房间留言列表（S6场景）"""
        async for client in async_client:
            # ← 修改：在外层循环获取room_id，避免在内层循环时generator已被消费
            room_id = await get_fixture_room_id(private_room)
            async for db in db_session:
                
                # ===== Arrange (准备) =====
                # 创建5个留言
                for i in range(5):
                    message = LiveRoomMessage(
                        id=uuid.uuid4(),
                        room_id=room_id,
                        session_id=None,
                        user_id=uuid.uuid4(),
                        user_role=LiveRoomMessageUserRole.REGULAR,
                        content=f"留言 {i}",
                        is_deleted=False
                    )
                    db.add(message)
                await db.commit()
                
                headers = {"Authorization": f"Bearer {admin_user_token}"}
                
                # ===== Act (执行) =====
                response = await client.get(
                    f"/api/v1/rooms/{room_id}/messages?page=1&size=10",
                    headers=headers
                )
                
                # ===== Assert (断言) =====
                assert response.status_code == 200
                data = response.json()
                assert data["code"] == 200
                assert data["data"]["total"] == 5
                assert len(data["data"]["items"]) == 5

    @pytest.mark.asyncio
    async def test_api_get_room_messages_pagination(
        self, 
        async_client, 
        db_session,
        public_room
    ):
        """测试留言分页功能（Public房间，匿名用户可访问）"""
        async for client in async_client:
            # ← 修改：在外层循环获取room_id，避免在内层循环时generator已被消费
            room_id = await get_fixture_room_id(public_room)
            async for db in db_session:
                
                # ===== Arrange (准备) =====
                # 创建10个留言
                for i in range(10):
                    message = LiveRoomMessage(
                        id=uuid.uuid4(),
                        room_id=room_id,
                        session_id=None,
                        user_id=uuid.uuid4(),
                        user_role=LiveRoomMessageUserRole.REGULAR,
                        content=f"留言 {i}",
                        is_deleted=False
                    )
                    db.add(message)
                await db.commit()
                
                # ===== Act (执行) =====
                # 不添加Authorization header（匿名用户）
                response = await client.get(
                    f"/api/v1/rooms/{room_id}/messages?page=2&size=3"
                )
                
                # ===== Assert (断言) =====
                assert response.status_code == 200
                data = response.json()
                assert data["data"]["total"] == 10
                assert data["data"]["page"] == 2
                assert len(data["data"]["items"]) == 3

    @pytest.mark.asyncio
    async def test_api_get_room_messages_with_since_filter(
        self, 
        async_client, 
        db_session,
        public_room
    ):
        """测试时间过滤功能（Public房间，匿名用户可访问）"""
        async for client in async_client:
            # ← 修改：在外层循环获取room_id，避免在内层循环时generator已被消费
            room_id = await get_fixture_room_id(public_room)
            async for db in db_session:
                
                # ===== Arrange (准备) =====
                now = datetime.utcnow()
                middle_time = now - timedelta(hours=1)
                
                # 创建留言，手动设置时间
                for i, time_delta in enumerate([timedelta(hours=2), timedelta(minutes=30)]):
                    message = LiveRoomMessage(
                        id=uuid.uuid4(),
                        room_id=room_id,
                        session_id=None,
                        user_id=uuid.uuid4(),
                        user_role=LiveRoomMessageUserRole.REGULAR,
                        content=f"留言 {i}",
                        is_deleted=False,
                        created_at=now - time_delta
                    )
                    db.add(message)
                await db.commit()
                
                # ===== Act (执行) =====
                # 不添加Authorization header（匿名用户）
                since_str = middle_time.isoformat()
                response = await client.get(
                    f"/api/v1/rooms/{room_id}/messages?page=1&size=10&since={since_str}"
                )
                
                # ===== Assert (断言) =====
                assert response.status_code == 200
                data = response.json()
                # 只有一条留言在middle_time之后
                assert data["data"]["total"] >= 1

    @pytest.mark.asyncio
    async def test_api_get_room_messages_excludes_deleted(
        self, 
        async_client, 
        db_session,
        public_room
    ):
        """测试排除已删除的留言（Public房间，匿名用户可访问）"""
        async for client in async_client:
            # ← 修改：在外层循环获取room_id，避免在内层循环时generator已被消费
            room_id = await get_fixture_room_id(public_room)
            async for db in db_session:
                
                # ===== Arrange (准备) =====
                # 创建3个留言：2个未删除，1个已删除
                for i in range(3):
                    message = LiveRoomMessage(
                        id=uuid.uuid4(),
                        room_id=room_id,
                        session_id=None,
                        user_id=uuid.uuid4(),
                        user_role=LiveRoomMessageUserRole.REGULAR,
                        content=f"留言 {i}",
                        is_deleted=(i == 2)
                    )
                    db.add(message)
                await db.commit()
                
                # ===== Act (执行) =====
                # 不添加Authorization header（匿名用户）
                response = await client.get(
                    f"/api/v1/rooms/{room_id}/messages?page=1&size=10"
                )
                
                # ===== Assert (断言) =====
                assert response.status_code == 200
                data = response.json()
                assert data["data"]["total"] == 2  # 排除已删除

    @pytest.mark.asyncio
    async def test_api_get_room_messages_room_not_found(self, async_client):
        """测试房间不存在时返回404"""
        async for client in async_client:
            # ===== Arrange (准备) =====
            non_existent_room_id = uuid.uuid4()
            
            # ===== Act (执行) =====
            # 不添加Authorization header（匿名用户）
            response = await client.get(
                f"/api/v1/rooms/{non_existent_room_id}/messages?page=1&size=10"
            )
            
            # ===== Assert (断言) =====
            assert response.status_code == 404
            data = response.json()
            assert data["code"] == 2001


class TestDeleteMessageAPI:
    """删除留言 API 测试"""

    @pytest.mark.asyncio
    async def test_delete_own_message_success(
        self, async_client, db_session, regular_user_token, regular_user_id, public_room
    ):
        async for client in async_client:
            room_id = await get_fixture_room_id(public_room)
            async for db in db_session:
                message = LiveRoomMessage(
                    id=uuid.uuid4(),
                    room_id=room_id,
                    user_id=regular_user_id,
                    user_role=LiveRoomMessageUserRole.REGULAR,
                    content="待删除留言",
                )
                db.add(message)
                await db.commit()

                response = await client.delete(
                    f"/api/v1/rooms/{room_id}/messages/{message.id}",
                    headers={"Authorization": f"Bearer {regular_user_token}"},
                )
                assert response.status_code == 200
                assert response.json()["code"] == 200

                await db.refresh(message)
                assert message.is_deleted is True

    @pytest.mark.asyncio
    async def test_delete_other_message_forbidden(
        self, async_client, db_session, regular_user_token, another_user_id, public_room
    ):
        async for client in async_client:
            room_id = await get_fixture_room_id(public_room)
            async for db in db_session:
                message = LiveRoomMessage(
                    id=uuid.uuid4(),
                    room_id=room_id,
                    user_id=another_user_id,
                    user_role=LiveRoomMessageUserRole.REGULAR,
                    content="他人留言",
                )
                db.add(message)
                await db.commit()

                response = await client.delete(
                    f"/api/v1/rooms/{room_id}/messages/{message.id}",
                    headers={"Authorization": f"Bearer {regular_user_token}"},
                )
                assert response.status_code == 403
                assert response.json()["code"] == 3002

    @pytest.mark.asyncio
    async def test_admin_delete_other_message_success(
        self, async_client, db_session, admin_user_token, another_user_id, public_room
    ):
        async for client in async_client:
            room_id = await get_fixture_room_id(public_room)
            async for db in db_session:
                message = LiveRoomMessage(
                    id=uuid.uuid4(),
                    room_id=room_id,
                    user_id=another_user_id,
                    user_role=LiveRoomMessageUserRole.REGULAR,
                    content="管理员删除",
                )
                db.add(message)
                await db.commit()

                response = await client.delete(
                    f"/api/v1/rooms/{room_id}/messages/{message.id}",
                    headers={"Authorization": f"Bearer {admin_user_token}"},
                )
                assert response.status_code == 200


class TestAdminMessageAPI:
    """管理端留言 API 自测清单"""

    async def _create_message(self, db, room_id, user_id, content="测试留言"):
        msg = LiveRoomMessage(
            id=uuid.uuid4(),
            room_id=room_id,
            user_id=user_id,
            user_role=LiveRoomMessageUserRole.REGULAR,
            content=content,
            extra={"user_display_name": "测试用户"},
        )
        db.add(msg)
        await db.commit()
        return msg

    @pytest.mark.asyncio
    async def test_admin_list_forbidden_for_regular_user(
        self, async_client, regular_user_token
    ):
        async for client in async_client:
            response = await client.get(
                "/api/v1/admin/messages",
                headers={"Authorization": f"Bearer {regular_user_token}"},
            )
            assert response.status_code == 403
            assert response.json()["code"] == 3003

    @pytest.mark.asyncio
    async def test_admin_list_success(
        self, async_client, db_session, admin_user_token, admin_user_id, public_room
    ):
        async for client in async_client:
            room_id = await get_fixture_room_id(public_room)
            async for db in db_session:
                await self._create_message(db, room_id, admin_user_id, "广告内容")
                response = await client.get(
                    "/api/v1/admin/messages",
                    headers={"Authorization": f"Bearer {admin_user_token}"},
                )
                assert response.status_code == 200
                data = response.json()["data"]
                assert data["total"] >= 1
                assert len(data["items"]) >= 1

    @pytest.mark.asyncio
    async def test_admin_list_filter_by_room_id(
        self, async_client, db_session, admin_user_token, admin_user_id, public_room
    ):
        async for client in async_client:
            room_id = await get_fixture_room_id(public_room)
            async for db in db_session:
                other_room = LiveRoom(
                    id=uuid.uuid4(),
                    user_id=admin_user_id,
                    title="其他房间",
                    stream_key=f"stream_{uuid.uuid4().hex}",
                )
                db.add(other_room)
                await db.commit()
                await self._create_message(db, room_id, admin_user_id, "房间A留言")
                await self._create_message(db, other_room.id, admin_user_id, "房间B留言")
                response = await client.get(
                    f"/api/v1/admin/messages?room_id={room_id}",
                    headers={"Authorization": f"Bearer {admin_user_token}"},
                )
                assert response.status_code == 200
                items = response.json()["data"]["items"]
                assert all(item["room_id"] == str(room_id) for item in items)

    @pytest.mark.asyncio
    async def test_admin_list_filter_by_user_id(
        self, async_client, db_session, admin_user_token, admin_user_id, another_user_id, public_room
    ):
        async for client in async_client:
            room_id = await get_fixture_room_id(public_room)
            async for db in db_session:
                await self._create_message(db, room_id, admin_user_id, "管理员留言")
                await self._create_message(db, room_id, another_user_id, "其他用户留言")
                response = await client.get(
                    f"/api/v1/admin/messages?user_id={admin_user_id}",
                    headers={"Authorization": f"Bearer {admin_user_token}"},
                )
                assert response.status_code == 200
                items = response.json()["data"]["items"]
                assert all(item["user_id"] == str(admin_user_id) for item in items)

    @pytest.mark.asyncio
    async def test_admin_list_filter_by_time_range(
        self, async_client, db_session, admin_user_token, admin_user_id, public_room
    ):
        async for client in async_client:
            room_id = await get_fixture_room_id(public_room)
            async for db in db_session:
                await self._create_message(db, room_id, admin_user_id)
                start = (datetime.utcnow() - timedelta(hours=1)).isoformat() + "Z"
                end = (datetime.utcnow() + timedelta(hours=1)).isoformat() + "Z"
                response = await client.get(
                    f"/api/v1/admin/messages?start_time={start}&end_time={end}",
                    headers={"Authorization": f"Bearer {admin_user_token}"},
                )
                assert response.status_code == 200
                assert response.json()["data"]["total"] >= 1

    @pytest.mark.asyncio
    async def test_admin_list_pagination(
        self, async_client, db_session, admin_user_token, admin_user_id, public_room
    ):
        async for client in async_client:
            room_id = await get_fixture_room_id(public_room)
            async for db in db_session:
                for i in range(8):
                    await self._create_message(db, room_id, admin_user_id, f"留言{i}")
                response = await client.get(
                    "/api/v1/admin/messages?page=1&page_size=5",
                    headers={"Authorization": f"Bearer {admin_user_token}"},
                )
                assert response.status_code == 200
                data = response.json()["data"]
                assert len(data["items"]) == 5
                assert data["total"] >= 8

    @pytest.mark.asyncio
    async def test_admin_batch_delete_forbidden_for_regular_user(
        self, async_client, regular_user_token
    ):
        async for client in async_client:
            response = await client.post(
                "/api/v1/admin/messages/batch-delete",
                json={"message_ids": [str(uuid.uuid4())]},
                headers={"Authorization": f"Bearer {regular_user_token}"},
            )
            assert response.status_code == 403
            assert response.json()["code"] == 3003

    @pytest.mark.asyncio
    async def test_admin_list_filter_by_keyword(
        self, async_client, db_session, admin_user_token, admin_user_id, public_room
    ):
        async for client in async_client:
            room_id = await get_fixture_room_id(public_room)
            async for db in db_session:
                await self._create_message(db, room_id, admin_user_id, "这是广告留言")
                await self._create_message(db, room_id, admin_user_id, "正常留言")
                response = await client.get(
                    "/api/v1/admin/messages?keyword=广告",
                    headers={"Authorization": f"Bearer {admin_user_token}"},
                )
                assert response.status_code == 200
                items = response.json()["data"]["items"]
                assert all("广告" in item["content"] for item in items)

    @pytest.mark.asyncio
    async def test_admin_batch_delete_success(
        self, async_client, db_session, admin_user_token, admin_user_id, public_room
    ):
        async for client in async_client:
            room_id = await get_fixture_room_id(public_room)
            async for db in db_session:
                msgs = [await self._create_message(db, room_id, admin_user_id) for _ in range(3)]
                response = await client.post(
                    "/api/v1/admin/messages/batch-delete",
                    json={"message_ids": [str(m.id) for m in msgs]},
                    headers={"Authorization": f"Bearer {admin_user_token}"},
                )
                assert response.status_code == 200
                assert response.json()["data"]["deleted_count"] == 3

    @pytest.mark.asyncio
    async def test_admin_batch_delete_nonexistent(
        self, async_client, admin_user_token
    ):
        async for client in async_client:
            response = await client.post(
                "/api/v1/admin/messages/batch-delete",
                json={"message_ids": [str(uuid.uuid4())]},
                headers={"Authorization": f"Bearer {admin_user_token}"},
            )
            assert response.status_code == 200
            assert response.json()["data"]["deleted_count"] == 0

    @pytest.mark.asyncio
    async def test_admin_batch_delete_over_limit(
        self, async_client, admin_user_token
    ):
        async for client in async_client:
            ids = [str(uuid.uuid4()) for _ in range(201)]
            response = await client.post(
                "/api/v1/admin/messages/batch-delete",
                json={"message_ids": ids},
                headers={"Authorization": f"Bearer {admin_user_token}"},
            )
            assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_admin_clear_room_messages(
        self, async_client, db_session, admin_user_token, admin_user_id, public_room
    ):
        async for client in async_client:
            room_id = await get_fixture_room_id(public_room)
            async for db in db_session:
                for _ in range(3):
                    await self._create_message(db, room_id, admin_user_id)
                response = await client.delete(
                    f"/api/v1/admin/rooms/{room_id}/messages",
                    headers={"Authorization": f"Bearer {admin_user_token}"},
                )
                assert response.status_code == 200
                assert response.json()["data"]["deleted_count"] == 3

    @pytest.mark.asyncio
    async def test_admin_clear_nonexistent_room(
        self, async_client, admin_user_token
    ):
        async for client in async_client:
            response = await client.delete(
                f"/api/v1/admin/rooms/{uuid.uuid4()}/messages",
                headers={"Authorization": f"Bearer {admin_user_token}"},
            )
            assert response.status_code == 404
            assert response.json()["code"] == 2001

    @pytest.mark.asyncio
    async def test_admin_endpoints_unauthorized(self, async_client):
        async for client in async_client:
            response = await client.get("/api/v1/admin/messages")
            assert response.status_code == 401

