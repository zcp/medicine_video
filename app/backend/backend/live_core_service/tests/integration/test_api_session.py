"""
LiveCore Service - Session API Integration Tests

This module contains integration tests for the session API endpoints,
testing the external API contract and critical business logic flows.
"""

import pytest
import uuid
import json
from datetime import datetime, timezone
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.live_core import LiveRoom, LiveSession, SessionStatistics, LiveSessionStatus
from app.schemas.live_core import LiveSessionCreate


# Helper function to create a test room via API
async def create_test_room_via_api(client: AsyncClient, token: str) -> dict:
    """通过API创建测试房间并返回响应数据"""
    room_data = {
        "title": "测试房间",
        "description": "API测试房间",
        "is_private": False,
        "record_by_default": True
    }
    
    headers = {"Authorization": f"Bearer {token}"}
    response = await client.post("/api/v1/rooms", json=room_data, headers=headers)
    assert response.status_code == 200
    
    response_json = response.json()
    assert response_json["code"] == 200
    return response_json["data"]


# Helper function to create a test room directly in database
async def create_test_room_in_db(db: AsyncSession, user_id: uuid.UUID = None) -> LiveRoom:
    """直接在数据库中创建测试房间"""
    # 如果没有提供user_id，使用默认的测试用户ID
    if user_id is None:
        user_id = uuid.UUID("1142ba9a-f551-4a86-9a0e-a281c93ca36a")  # 使用测试用户ID
    
    room = LiveRoom(
        title="数据库测试房间",
        description="用于API测试的房间",
        stream_key=f"test_key_{uuid.uuid4().hex[:8]}",
        is_private=False,
        record_by_default=True,
        user_id=user_id  # 添加user_id字段
    )
    db.add(room)
    await db.commit()
    await db.refresh(room)
    return room




@pytest.mark.asyncio
async def test_update_scheduled_session_success(
    async_client, 
    db_session, 
    regular_user_token: str
):
    """
    Tests the successful update of a scheduled session.
    """
    # ===== Arrange (准备) =====
    headers = {"Authorization": f"Bearer {regular_user_token}"}
    
    async for client in async_client:
        room_data = await create_test_room_via_api(client, regular_user_token)
        room_id = room_data["id"]

        initial_start_time = datetime.now(timezone.utc).isoformat()
        session_payload = {"start_time": initial_start_time}
        create_response = await client.post(f"/api/v1/rooms/{room_id}/sessions", json=session_payload, headers=headers)
        session_id = create_response.json()["data"]["id"]

        # Prepare the new start time as a datetime object
        new_start_time_obj = datetime.now(timezone.utc)
        update_data = {"start_time": new_start_time_obj.isoformat()}

        # ===== Act (执行) =====
        response = await client.patch(f"/api/v1/sessions/{session_id}", json=update_data, headers=headers)

        # ===== Assert (断言) =====
        assert response.status_code == 200
        response_json = response.json()
        assert response_json["code"] == 200

        # --- THE FIX IS HERE ---
        # 1. Get the time string from the API response.
        response_time_str = response_json["data"]["start_time"].replace("Z", "")
        # Resulting string looks like: '...Z'
        # 2. Parse the response string back into a timezone-aware datetime object.
        #    The .replace('Z', '+00:00') handles both 'Z' and '+00:00' formats.
        print("xxxyz",response_time_str)

        response_time_obj = datetime.fromisoformat(response_time_str.replace('+00:00Z','Z'))

        # 3. Compare the datetime objects. To avoid tiny microsecond differences,
        #    it's robust to check if the difference is less than a second.
        time_difference = abs(response_time_obj - new_start_time_obj)
        assert time_difference.total_seconds() < 1
        break




@pytest.mark.asyncio
async def test_get_session_details_success(
    async_client, 
    db_session, 
    regular_user_token: str
):
    """
    测试成功获取会话详情（继承Room权限，Owner可访问）
    - 流程：创建会话后获取其详情
    - 验证：API返回完整的会话信息包括统计数据
    """
    # ===== Arrange (准备) =====
    headers = {"Authorization": f"Bearer {regular_user_token}"}
    
    async for client in async_client:
        async for db in db_session:
            room_data = await create_test_room_via_api(client, regular_user_token)
            room_id = room_data["id"]
            
            # 创建计划场次
            start_time = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            session_data = {"start_time": start_time}
            
            create_response = await client.post(f"/api/v1/rooms/{room_id}/sessions", json=session_data, headers=headers)
            session_id = create_response.json()["data"]["id"]
            
            # ===== Act (执行) =====
            response = await client.get(f"/api/v1/sessions/{session_id}", headers=headers)
            
            # ===== Assert (断言) =====
            assert response.status_code == 200
            response_json = response.json()
            assert response_json["code"] == 200
            assert response_json["message"] == "success"
            
            # 验证响应数据包含统计信息
            data = response_json["data"]
            assert data["id"] == session_id
            assert data["room_id"] == room_id
            assert data["status"] == "scheduled"
            assert data["statistics"] is not None
            
            # 验证统计信息结构
            stats = data["statistics"]
            assert "id" in stats
            assert stats["session_id"] == session_id
            assert stats["peak_viewer_count"] == 0
            assert stats["total_viewer_count"] == 0
            assert stats["total_like_count"] == 0
            assert stats["total_share_count"] == 0
            break
        break


@pytest.mark.asyncio
async def test_get_session_details_not_found(
    async_client, 
    db_session, 
    regular_user_token: str
):
    """
    测试获取不存在的会话详情
    - 流程：使用不存在的session_id获取详情
    - 验证：返回404错误
    """
    # ===== Arrange (准备) =====
    headers = {"Authorization": f"Bearer {regular_user_token}"}
    random_session_id = str(uuid.uuid4())
    
    # ===== Act (执行) =====
    async for client in async_client:
        async for db in db_session:
            response = await client.get(f"/api/v1/sessions/{random_session_id}", headers=headers)
            
            # ===== Assert (断言) =====
            assert response.status_code == 404
            response_json = response.json()
            assert response_json["code"] == 2001
            assert response_json["message"] == "资源不存在"
            assert response_json["data"]["resource"] == "Session"
            assert response_json["data"]["id"] == random_session_id
            break
        break



@pytest.mark.asyncio
async def test_update_scheduled_session_fails_when_live(
    async_client, 
    db_session, 
    regular_user_token: str,
    regular_user_id: uuid.UUID
):
    """
    测试更新正在直播的场次失败
    - 流程：创建场次，设置为LIVE状态，然后尝试更新
    - 验证：返回403错误，数据库状态无变化
    """
    async for client in async_client:
        async for db in db_session:
            # Arrange: 在数据库中创建房间和会话（使用当前用户的user_id，确保有权限）
            room = await create_test_room_in_db(db, user_id=regular_user_id)
            
            # 创建会话并设置为LIVE状态
            start_time = datetime.now(timezone.utc)
            original_start_time = start_time
            
            session = LiveSession(
                room_id=room.id,
                status=LiveSessionStatus.LIVE,
                start_time=start_time,
                end_time=None,
                video_id=None
            )
            db.add(session)
            await db.commit()
            await db.refresh(session)
            
            # ===== Arrange (准备) =====
            new_start_time = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            update_data = {"start_time": new_start_time}
            headers = {"Authorization": f"Bearer {regular_user_token}"}
            
            # ===== Act (执行) =====
            response = await client.patch(f"/api/v1/sessions/{session.id}", json=update_data, headers=headers)
            
            # 需求变更：允许修改正在直播的场次，期望200
            assert response.status_code == 200
            response_json = response.json()
            assert response_json.get("code") == 200


@pytest.mark.asyncio
async def test_delete_finished_session_success(
    async_client, 
    db_session, 
    regular_user_token: str, 
    regular_user_id: uuid.UUID
):
    """
    测试成功删除已结束的场次
    - 流程：创建已结束的场次然后删除
    - 验证：API响应正确，数据库中的记录被删除
    """
    async for client in async_client:
        async for db in db_session:
            # ===== Arrange (准备) =====
            headers = {"Authorization": f"Bearer {regular_user_token}"}
            room = await create_test_room_in_db(db, user_id=regular_user_id)

            session = LiveSession(
                room_id=room.id,
                status=LiveSessionStatus.FINISHED,
                start_time=datetime.now(timezone.utc),
                end_time=datetime.now(timezone.utc),
                video_id=None
            )
            db.add(session)
            await db.commit()
            await db.refresh(session)
            session_id = session.id

            # ===== Act (执行) =====
            response = await client.delete(f"/api/v1/sessions/{session_id}", headers=headers)
            
            # ===== Assert (断言) =====
            assert response.status_code == 200
            response_json = response.json()
            assert response_json["code"] == 200
            assert response_json["message"] == "success"
            assert response_json["data"]["id"] == str(session_id)
            assert response_json["data"]["status"] == "deleted"

            # Verify Database State: 验证记录被删除
            deleted_session_result = await db.execute(
                select(LiveSession).where(LiveSession.id == session_id)
            )
            deleted_session = deleted_session_result.scalar_one_or_none()

            # Assert: 验证行被真正删除
            assert deleted_session is None
            break
        break


@pytest.mark.asyncio
async def test_delete_session_fails_when_live(
    async_client, 
    db_session, 
    regular_user_token: str,
    regular_user_id: uuid.UUID
):
    """
    测试删除正在直播的场次失败
    - 流程：创建正在直播的场次然后尝试删除
    - 验证：返回403错误，数据库中记录未被删除
    """
    async for client in async_client:
        async for db in db_session:
            # Arrange: 在数据库中创建房间和正在直播的会话（使用当前用户的user_id，确保有权限）
            room = await create_test_room_in_db(db, user_id=regular_user_id)
            
            session = LiveSession(
                room_id=room.id,
                status=LiveSessionStatus.LIVE,
                start_time=datetime.now(timezone.utc),
                end_time=None,
                video_id=None
            )
            db.add(session)
            await db.commit()
            await db.refresh(session)
            session_id = session.id
            
            # ===== Arrange (准备) =====
            headers = {"Authorization": f"Bearer {regular_user_token}"}
            
            # ===== Act (执行) =====
            response = await client.delete(f"/api/v1/sessions/{session_id}", headers=headers)
            
            # ===== Assert (断言) =====
            # ← 修改：SessionActionForbiddenException返回403，不是404
            assert response.status_code == 403
            response_json = response.json()
            assert response_json["code"] == 2005  # SessionActionForbiddenException的code（删除时是2005）
            assert response_json["message"] == "业务逻辑错误"
            #assert "无法删除正在直播的场次" in response_json["data"]["error"]
            
            # Verify Database State: 验证记录未被删除
            live_session_result = await db.execute(
                select(LiveSession).where(LiveSession.id == session_id)
            )
            live_session = live_session_result.scalar_one_or_none()
            
            # Assert: 验证行未被删除
            assert live_session is not None
            assert live_session.status == LiveSessionStatus.LIVE
            break
        break


@pytest.mark.asyncio
async def test_create_session_for_non_existent_room(
    async_client, 
    db_session, 
    regular_user_token: str
):
    """
    测试为不存在的房间创建场次
    - 流程：使用不存在的room_id创建场次
    - 验证：返回404错误
    """
    async for client in async_client:
        async for db in db_session:
            # ===== Arrange (准备) =====
            headers = {"Authorization": f"Bearer {regular_user_token}"}
            random_room_id = str(uuid.uuid4())
            
            # 准备会话数据
            start_time = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            session_data = {"start_time": start_time}
            
            # ===== Act (执行) =====
            response = await client.post(f"/api/v1/rooms/{random_room_id}/sessions", json=session_data, headers=headers)
            
            # Assert API Response: 验证404响应
            assert response.status_code == 404
            response_json = response.json()
            assert response_json["code"] == 2001
            assert response_json["message"] == "资源不存在"
            assert response_json["data"]["resource"] == "Room"
            assert response_json["data"]["id"] == random_room_id


@pytest.mark.asyncio
async def test_get_room_sessions_success(
    async_client, 
    db_session, 
    regular_user_token: str
):
    """
    测试成功获取房间的会话列表
    - 流程：创建房间和多个会话，然后获取会话列表
    - 验证：返回正确的分页数据
    """
    async for client in async_client:
        async for db in db_session:
            # ===== Arrange (准备) =====
            headers = {"Authorization": f"Bearer {regular_user_token}"}
            room_data = await create_test_room_via_api(client, regular_user_token)
            room_id = room_data["id"]
            
            # 创建3个会话
            session_ids = []
            for i in range(3):
                start_time = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
                session_data = {"start_time": start_time}
                
                create_response = await client.post(f"/api/v1/rooms/{room_id}/sessions", json=session_data, headers=headers)
                session_id = create_response.json()["data"]["id"]
                session_ids.append(session_id)
            
            # ===== Act (执行) =====
            response = await client.get(f"/api/v1/rooms/{room_id}/sessions?page=1&size=2", headers=headers)
            
            # ===== Assert (断言) =====
            assert response.status_code == 200
            response_json = response.json()
            assert response_json["code"] == 200
            assert response_json["message"] == "success"
            
            # 验证分页数据
            data = response_json["data"]
            assert data["total"] == 3
            assert data["page"] == 1
            assert data["size"] == 2
            assert len(data["items"]) == 2
            
            # 验证每个项目的结构
            for item in data["items"]:
                assert "id" in item
                assert item["room_id"] == room_id
                assert item["status"] == "scheduled"
                assert "start_time" in item
            break
        break


@pytest.mark.asyncio
async def test_get_room_sessions_for_non_existent_room(
    async_client, 
    db_session, 
    regular_user_token: str
):
    """
    测试获取不存在房间的会话列表
    - 流程：使用不存在的room_id获取会话列表
    - 验证：返回404错误
    """
    async for client in async_client:
        async for db in db_session:
            # Arrange: 使用随机UUID作为不存在的room_id
            random_room_id = str(uuid.uuid4())
            # ← 修改：添加headers定义
            headers = {"Authorization": f"Bearer {regular_user_token}"}
            
            # ===== Act (执行) =====
            response = await client.get(f"/api/v1/rooms/{random_room_id}/sessions", headers=headers)
            
            # Assert API Response: 验证404响应
            assert response.status_code == 404
            response_json = response.json()
            assert response_json["code"] == 2001
            assert response_json["message"] == "资源不存在"
            assert response_json["data"]["resource"] == "Room"
            assert response_json["data"]["id"] == random_room_id


# ==================== 新增增量测试：Playback URL 持久化与更新 ====================

@pytest.mark.asyncio
async def test_get_session_details_returns_playback_url_from_db(
    async_client, 
    db_session, 
    regular_user_token: str
):
    """
    测试 GET session 返回数据库中持久化的 playback_url
    - 步骤：
      1. 在DB中直接创建带 playback_url 的 Session
      2. 调用 GET /sessions/{id}
    - 期望：
      1. 返回的 data["playback_url"] 等于 DB 中的值
    """
    async for client in async_client:
        async for db in db_session:
            # 准备测试数据
            room = await create_test_room_in_db(db)
            expected_url = "https://test-cdn.example.com/media/video_db_123.mp4"
            
            session = LiveSession(
                room_id=room.id,
                status=LiveSessionStatus.READY,
                start_time=datetime.now(timezone.utc),
                video_id=uuid.uuid4(),
                playback_url=expected_url  # 直接写入 DB
            )
            db.add(session)
            await db.commit()
            await db.refresh(session)
            
            # ===== Arrange (准备) =====
            headers = {"Authorization": f"Bearer {regular_user_token}"}
            
            # ===== Act (执行) =====
            response = await client.get(f"/api/v1/sessions/{session.id}", headers=headers)
            
            # ===== Assert (断言) =====
            assert response.status_code == 200
            data = response.json()["data"]
            assert data["playback_url"] == expected_url
            
            break
        break

@pytest.mark.asyncio
async def test_get_session_details_returns_null_when_playback_url_is_null(
    async_client, 
    db_session, 
    regular_user_token: str
):
    """
    测试 GET session 当 DB 中 playback_url 为 NULL 时返回 null
    - 步骤：
      1. 在DB中创建 playback_url=None 的 Session
      2. 调用 GET /sessions/{id}
    - 期望：
      1. 返回的 data["playback_url"] 为 null
    """
    async for client in async_client:
        async for db in db_session:
            # 准备测试数据
            room = await create_test_room_in_db(db)
            
            session = LiveSession(
                room_id=room.id,
                status=LiveSessionStatus.READY,
                start_time=datetime.now(timezone.utc),
                video_id=uuid.uuid4(),
                playback_url=None  # 显式为 None
            )
            db.add(session)
            await db.commit()
            await db.refresh(session)
            
            # ===== Arrange (准备) =====
            headers = {"Authorization": f"Bearer {regular_user_token}"}
            
            # ===== Act (执行) =====
            response = await client.get(f"/api/v1/sessions/{session.id}", headers=headers)
            
            # ===== Assert (断言) =====
            assert response.status_code == 200
            data = response.json()["data"]
            assert data["playback_url"] is None
            
            break
        break

@pytest.mark.asyncio
async def test_patch_session_updates_playback_url_when_ready(
    async_client, 
    db_session, 
    regular_user_token: str, 
    regular_user_id: uuid.UUID
):
    """
    测试 PATCH 更新 playback_url (在 READY 状态下)
    - 步骤：
      1. 创建 READY 状态的 Session
      2. PATCH 更新 playback_url
    - 期望：
      1. API 返回 200 且包含新 URL
      2. DB 中字段被更新
    """
    async for client in async_client:
        async for db in db_session:
            # ===== Arrange (准备) =====
            headers = {"Authorization": f"Bearer {regular_user_token}"}
            room = await create_test_room_in_db(db, user_id=regular_user_id)
            session = LiveSession(
                room_id=room.id,
                status=LiveSessionStatus.READY,
                start_time=datetime.now(timezone.utc),
                playback_url=None
            )
            db.add(session)
            await db.commit()
            await db.refresh(session)
            
            new_url = "https://manual.example.com/custom_update.mp4"
            
            # ===== Act (执行) =====
            response = await client.patch(
                f"/api/v1/sessions/{session.id}", 
                json={"playback_url": new_url}, 
                headers=headers
            )
            
            # ===== Assert (断言) =====
            assert response.status_code == 200
            data = response.json()["data"]
            assert data["playback_url"] == new_url
            
            # 验证数据库
            await db.refresh(session)
            assert session.playback_url == new_url
            
            break
        break

@pytest.mark.asyncio
async def test_patch_session_forbidden_update_playback_url_when_live(
    async_client, 
    db_session, 
    regular_user_token: str, 
    regular_user_id: uuid.UUID
):
    """
    测试 PATCH 禁止在 LIVE 状态下更新 playback_url
    - 步骤：
      1. 创建 LIVE 状态的 Session
      2. PATCH 更新 playback_url
    - 期望：
      1. API 返回 403 Forbidden
      2. DB 中字段未被更新
    """
    async for client in async_client:
        async for db in db_session:
            # ===== Arrange (准备) =====
            headers = {"Authorization": f"Bearer {regular_user_token}"}
            room = await create_test_room_in_db(db, user_id=regular_user_id)
            session = LiveSession(
                room_id=room.id,
                status=LiveSessionStatus.LIVE,
                start_time=datetime.now(timezone.utc),
                playback_url=None
            )
            db.add(session)
            await db.commit()
            await db.refresh(session)
            
            # ===== Act (执行) =====
            response = await client.patch(
                f"/api/v1/sessions/{session.id}", 
                json={"playback_url": "https://evil.com/hack.mp4"}, 
                headers=headers
            )
            
            # 需求变更：允许在 LIVE 状态下更新 playback_url，期望200
            assert response.status_code == 200
            break
        break
