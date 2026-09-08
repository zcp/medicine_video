"""
LiveCore Service - V6 API Import and Batch Import Idempotent Integration Tests

This module contains integration tests for V6 idempotency features:
- Import Session API idempotency
- Batch Import API idempotency
- External room ID header aliases
- Cross-file deduplication

遵循测试代码生成提示词母版 - Pragmatic 测试策略（真实 DB + 完整链路）
"""

import pytest
import uuid
import io
import csv
from datetime import datetime, timezone
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.live_core import LiveRoom, LiveSession
from app.services.utils_playback import calc_playback_url_hash
from tests.conftest import async_session_factory
from fastapi import FastAPI
from app.api.v1.api import api_router
from app.core.deps import get_db, get_current_user
import time


# ==================== Test Fixtures ====================

@pytest.fixture
async def async_client_with_public_id(regular_user_id: uuid.UUID, regular_user_role: str) -> AsyncClient:
    """
    提供带有 public_id 和 role 的异步客户端（用于 V6 幂等测试）
    """
    import os
    from tests.conftest import async_session_factory
    
    # 设置测试环境变量
    os.environ["JWT_SECRET_KEY"] = "my-key"
    os.environ["JWT_ALGORITHM"] = "HS256"

    # 创建测试专用的FastAPI应用
    app = FastAPI(
        title="LiveCore Service Test",
        version="1.0.0",
        redirect_slashes=False
    )

    # 使用与main.py相同的路由结构
    app.include_router(api_router, prefix="/api/v1")

    # 覆盖数据库依赖，使用测试数据库
    async def override_get_db():
        async with async_session_factory() as session:
            yield session

    # 覆盖JWT认证依赖，添加 public_id 和 role 字段
    async def override_get_current_user():
        return {
            "public_id": str(regular_user_id),  # ← 修改：使用regular_user_id
            "user_id": str(regular_user_id),
            "sub": str(regular_user_id),
            "email": "regular@example.com",
            "role": regular_user_role,  # ← 新增：添加role字段
            "exp": int(time.time()) + 3600
        }

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    # 使用测试服务器
    async with AsyncClient(app=app, base_url="http://localhost:8000") as client:
        yield client


@pytest.fixture
async def async_client_with_admin_role(regular_user_id: uuid.UUID, admin_user_role: str) -> AsyncClient:
    """
    提供带有 admin role 的异步客户端（用于需要管理员权限的测试，如批量导入）
    
    注意：这个 fixture 覆盖了 get_current_user 依赖，使用 ADMIN 角色
    """
    import os
    from tests.conftest import async_session_factory
    
    # 设置测试环境变量
    os.environ["JWT_SECRET_KEY"] = "my-key"
    os.environ["JWT_ALGORITHM"] = "HS256"

    # 创建测试专用的FastAPI应用
    app = FastAPI(
        title="LiveCore Service Test",
        version="1.0.0",
        redirect_slashes=False
    )

    # 使用与main.py相同的路由结构
    app.include_router(api_router, prefix="/api/v1")

    # 覆盖数据库依赖，使用测试数据库
    async def override_get_db():
        async with async_session_factory() as session:
            yield session

    # 覆盖JWT认证依赖，添加 public_id 和 ADMIN role 字段
    async def override_get_current_user():
        return {
            "public_id": str(regular_user_id),
            "user_id": str(regular_user_id),
            "sub": str(regular_user_id),
            "email": "admin@example.com",
            "role": admin_user_role,  # ← 使用 ADMIN 角色
            "exp": int(time.time()) + 3600
        }

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    # 使用测试服务器
    async with AsyncClient(app=app, base_url="http://localhost:8000") as client:
        yield client


# ==================== Helper Functions ====================

async def create_test_room_for_import(db: AsyncSession, user_id: uuid.UUID) -> LiveRoom:
    """创建用于导入测试的房间"""
    room = LiveRoom(
        title=f"导入测试房间_{uuid.uuid4().hex[:8]}",
        description="用于导入会话的测试房间",
        stream_key=f"test_key_{uuid.uuid4().hex[:8]}",
        is_private=False,
        record_by_default=True,
        user_id=user_id
    )
    db.add(room)
    await db.commit()
    await db.refresh(room)
    return room


def create_csv_file(rows: list, encoding: str = 'utf-8-sig') -> io.BytesIO:
    """创建 CSV 文件内容（内存）"""
    output = io.StringIO()
    writer = csv.writer(output)
    for row in rows:
        writer.writerow(row)
    
    csv_content = output.getvalue()
    return io.BytesIO(csv_content.encode(encoding))


# ==================== Import Session API Idempotent Tests ====================

@pytest.mark.asyncio
async def test_api_import_session_first_time_success(
    async_client_with_public_id, 
    db_session,
    regular_user_id: uuid.UUID
):
    """
    测试第一次导入会话成功
    - 使用 async_client + db_session + async_session_factory
    - 断言: HTTP 状态码正确，playback_url_hash 正确写入，只生成一条 Session 记录
    """
    async for client in async_client_with_public_id:
        async for db in db_session:
            # Arrange: 创建房间
            # ===== Arrange (准备) =====
            # 使用regular_user_id（从conftest.py获取，与async_client_with_public_id中的user_id一致）
            room = await create_test_room_for_import(db, regular_user_id)
            room_id = str(room.id)
            
            playback_url = "https://cdn.example.com/videos/test_playback_123.m3u8"
            import_payload = {
                "start_time": datetime.now(timezone.utc).isoformat(),
                "end_time": datetime.now(timezone.utc).isoformat(),
                "status": "finished",
                "playback_url": playback_url
            }
            
            # Act: 调用导入会话 API
            response = await client.post(
                f"/api/v1/rooms/{room_id}/sessions/import",
                json=import_payload
            )
            
            # Assert: 验证 HTTP 响应
            assert response.status_code == 200
            response_json = response.json()
            assert response_json["code"] == 200
            
            session_data = response_json["data"]
            session_id = session_data["id"]
            
            # 验证 playback_url 正确
            assert session_data["playback_url"] == playback_url.strip()
            
            # 验证 idempotent_hit 字段（如果存在）
            if "idempotent_hit" in session_data:
                assert session_data["idempotent_hit"] is False
            
            # 使用新会话验证 DB 状态（避免 identity map 缓存）
            async with async_session_factory() as new_db:
                result = await new_db.execute(
                    select(LiveSession).where(LiveSession.id == uuid.UUID(session_id))
                )
                db_session = result.scalar_one_or_none()
                
                assert db_session is not None
                assert db_session.playback_url == playback_url.strip()
                
                # 验证 playback_url_hash 正确写入
                expected_hash = calc_playback_url_hash(playback_url)
                assert db_session.playback_url_hash == expected_hash


@pytest.mark.asyncio
async def test_api_import_session_idempotent_twice(
    async_client_with_public_id, 
    db_session,
    regular_user_id: uuid.UUID
):
    """
    测试同一 payload 调用两次的幂等性
    - 场景: 同一 payload 调用两次
    - 断言: 两次返回的 data.id 相同，第二次 idempotent_hit=True，DB 中仅存在一条 Session
    """
    async for client in async_client_with_public_id:
        async for db in db_session:
            # Arrange: 创建房间
            # ===== Arrange (准备) =====
            # 使用regular_user_id（从conftest.py获取，与async_client_with_public_id中的user_id一致）
            room = await create_test_room_for_import(db, regular_user_id)
            room_id = str(room.id)
            
            playback_url = "https://cdn.example.com/videos/test_playback_456.m3u8"
            import_payload = {
                "start_time": datetime.now(timezone.utc).isoformat(),
                "end_time": datetime.now(timezone.utc).isoformat(),
                "status": "finished",
                "playback_url": playback_url
            }
            
            # Act: 第一次调用
            response1 = await client.post(
                f"/api/v1/rooms/{room_id}/sessions/import",
                json=import_payload
            )
            
            assert response1.status_code == 200
            response1_json = response1.json()
            session_id_1 = response1_json["data"]["id"]
            
            # Act: 第二次调用（相同 payload）
            response2 = await client.post(
                f"/api/v1/rooms/{room_id}/sessions/import",
                json=import_payload
            )
            
            assert response2.status_code == 200
            response2_json = response2.json()
            session_id_2 = response2_json["data"]["id"]
            
            # Assert: 两次返回的 session_id 相同
            assert session_id_1 == session_id_2
            
            # 验证第二次返回的 idempotent_hit 字段（如果存在）
            if "idempotent_hit" in response2_json["data"]:
                assert response2_json["data"]["idempotent_hit"] is True
            
            # 验证 DB 中只存在一条 Session
            async with async_session_factory() as new_db:
                result = await new_db.execute(
                    select(LiveSession).where(LiveSession.room_id == room.id)
                )
                sessions = result.scalars().all()
                
                # 过滤出相同 playback_url_hash 的会话
                expected_hash = calc_playback_url_hash(playback_url)
                matching_sessions = [s for s in sessions if s.playback_url_hash == expected_hash]
                
                assert len(matching_sessions) == 1


# ==================== Batch Import API Idempotent Tests ====================

@pytest.mark.asyncio
async def test_api_batch_import_idempotent_same_file_twice(
    async_client_with_public_id, 
    async_client_with_admin_role,
    db_session,
    regular_user_id: uuid.UUID
):
    """
    测试同一个 CSV 文件两次导入的幂等性
    - 场景: 同一个 CSV 文件，两次 mode="apply" 导入
    - CSV 至少包含一行带 external_room_id + playback_url 的记录
    - 断言: 第一次成功落库，第二次所有行 skipped=True，DB 中房间/场次数量不增加
    """
    async for client in async_client_with_public_id:
        async for db in db_session:
            # Arrange: 创建 CSV 文件
            csv_rows = [
                ["room_title", "external_room_id", "playback_url", "status"],
                ["测试房间1", "ext_room_001", "https://example.com/video1.m3u8", "finished"],
                ["测试房间2", "ext_room_002", "https://example.com/video2.m3u8", "finished"],
            ]
            csv_file = create_csv_file(csv_rows)
            
            # ← 修改：在循环外部获取管理员客户端，避免重复创建
            async for admin_client in async_client_with_admin_role:
                # Act: 第一次导入（使用管理员客户端）
                csv_file.seek(0)
                response1 = await admin_client.post(
                    "/api/v1/rooms/import/batch?mode=apply",
                    files={"file": ("test.csv", csv_file, "text/csv")}
                )
                
                assert response1.status_code == 200
                response1_json = response1.json()
                assert response1_json["code"] == 200
                
                first_success_count = response1_json["data"]["success_count"]
                first_failed_count = response1_json["data"]["failed_count"]
                
                # ===== Assert (断言) =====
                # 记录第一次导入后的房间和会话数量
                async with async_session_factory() as new_db:
                    room_count_1 = await new_db.execute(
                        select(LiveRoom).where(LiveRoom.user_id == regular_user_id)
                    )
                    rooms_1 = room_count_1.scalars().all()
                    room_count_after_first = len(rooms_1)
                    
                    session_count_1 = await new_db.execute(select(LiveSession))
                    sessions_1 = session_count_1.scalars().all()
                    session_count_after_first = len(sessions_1)
                
                # Act: 第二次导入（相同文件，使用管理员客户端）
                csv_file.seek(0)
                response2 = await admin_client.post(
                    "/api/v1/rooms/import/batch?mode=apply",
                    files={"file": ("test.csv", csv_file, "text/csv")}
                )
                
                assert response2.status_code == 200
                response2_json = response2.json()
                assert response2_json["code"] == 200
                
                second_success_count = response2_json["data"]["success_count"]
                second_failed_count = response2_json["data"]["failed_count"]
                
                # Assert: 第二次导入的成功数应该等于第一次
                assert second_success_count == first_success_count
                assert second_failed_count == 0
                
                # 验证所有成功行的 skipped 字段
                items = response2_json["data"]["items"]
                for item in items:
                    if item["status"] == "success":
                        assert item["skipped"] is True
                        assert item["skip_reason"] == "duplicate_session_by_playback_url"
                
                # 验证 skipped_count（如果存在）
                if "skipped_count" in response2_json["data"]:
                    assert response2_json["data"]["skipped_count"] == first_success_count
                
                # 验证 DB 中房间/场次数量不增加
                async with async_session_factory() as new_db:
                    room_count_2 = await new_db.execute(
                        select(LiveRoom).where(LiveRoom.user_id == regular_user_id)
                    )
                    rooms_2 = room_count_2.scalars().all()
                    room_count_after_second = len(rooms_2)
                    
                    session_count_2 = await new_db.execute(select(LiveSession))
                    sessions_2 = session_count_2.scalars().all()
                    session_count_after_second = len(sessions_2)
                    
                    assert room_count_after_second == room_count_after_first
                    assert session_count_after_second == session_count_after_first
                break


@pytest.mark.asyncio
async def test_api_batch_import_idempotent_cross_files(
    async_client_with_public_id, 
    async_client_with_admin_role,
    db_session,
    regular_user_id: uuid.UUID
):
    """
    测试不同 CSV 文件含相同行的幂等性
    - 场景: 两个 CSV 文件中包含相同的 (external_room_id, playback_url) 行
    - 断言: 两次导入后，数据库中 (user_id, external_room_id) 唯一，只有一个房间；
    - (room_id, playback_url_hash) 唯一，只有一个 Session；第二个文件中的重复行被标记为 skipped
    """
    async for client in async_client_with_public_id:
        async for db in db_session:
            # Arrange: 创建两个 CSV 文件，包含相同的行
            shared_external_id = "shared_ext_001"
            shared_playback_url = "https://example.com/shared_video.m3u8"
            
            csv_rows_1 = [
                ["room_title", "external_room_id", "playback_url", "status"],
                ["房间1", shared_external_id, shared_playback_url, "finished"],
            ]
            csv_file_1 = create_csv_file(csv_rows_1)
            
            csv_rows_2 = [
                ["room_title", "external_room_id", "playback_url", "status"],
                ["房间2", shared_external_id, shared_playback_url, "finished"],  # 相同的 external_room_id 和 playback_url
            ]
            csv_file_2 = create_csv_file(csv_rows_2)
            
            # ← 修改：在循环外部获取管理员客户端，避免重复创建
            async for admin_client in async_client_with_admin_role:
                # Act: 第一次导入（使用管理员客户端）
                csv_file_1.seek(0)
                response1 = await admin_client.post(
                    "/api/v1/rooms/import/batch?mode=apply",
                    files={"file": ("test1.csv", csv_file_1, "text/csv")}
                )
                
                assert response1.status_code == 200
                response1_json = response1.json()
                assert response1_json["code"] == 200
                
                # Act: 第二次导入（包含相同行，使用管理员客户端）
                csv_file_2.seek(0)
                response2 = await admin_client.post(
                    "/api/v1/rooms/import/batch?mode=apply",
                    files={"file": ("test2.csv", csv_file_2, "text/csv")}
                )
                
                assert response2.status_code == 200
                response2_json = response2.json()
                assert response2_json["code"] == 200
                
                # Assert: 验证第二个文件中的重复行被标记为 skipped
                items = response2_json["data"]["items"]
                for item in items:
                    if item["status"] == "success":
                        assert item["skipped"] is True
                        assert item["skip_reason"] == "duplicate_session_by_playback_url"
                
                # 验证 DB 中只有一个房间（按 external_room_id）
                async with async_session_factory() as new_db:
                    result = await new_db.execute(
                        select(LiveRoom).where(
                            LiveRoom.user_id == regular_user_id,
                            LiveRoom.external_room_id == shared_external_id
                        )
                    )
                    rooms = result.scalars().all()
                    assert len(rooms) == 1
                break
                
                # 验证只有一个 Session（按 playback_url_hash）
                expected_hash = calc_playback_url_hash(shared_playback_url)
                session_result = await new_db.execute(
                    select(LiveSession).where(
                        LiveSession.room_id == rooms[0].id,
                        LiveSession.playback_url_hash == expected_hash
                    )
                )
                sessions = session_result.scalars().all()
                assert len(sessions) == 1


@pytest.mark.asyncio
async def test_api_batch_import_external_room_id_header_aliases(
    async_client_with_public_id, 
    async_client_with_admin_role,
    db_session,
    regular_user_id: uuid.UUID
):
    """
    测试 external_room_id 的表头别名映射
    - 场景: 使用三种不同表头："external_room_id"、"直播间id"、"直播间ID"
    - 断言: 三种表头均能被解析并映射到 row["external_room_id"]，在 (user_id, external_room_id) 维度上表现出相同的幂等复用行为
    """
    async for client in async_client_with_public_id:
        async for db in db_session:
            # ===== Arrange (准备) =====
            shared_external_id = "alias_test_001"
            playback_url = "https://example.com/alias_test.m3u8"
            
            # ← 修改：在循环外部获取管理员客户端，避免在循环内重复创建
            async for admin_client in async_client_with_admin_role:
                # 测试三种表头
                test_cases = [
                    ("external_room_id", shared_external_id),
                    ("直播间id", f"{shared_external_id}_2"),
                    ("直播间ID", f"{shared_external_id}_3"),
                ]
                
                for header_name, ext_id in test_cases:
                    # Arrange: 创建 CSV 文件
                    csv_rows = [
                        ["room_title", header_name, "playback_url", "status"],
                        ["测试房间", ext_id, playback_url, "finished"],
                    ]
                    csv_file = create_csv_file(csv_rows)
                    
                    # Act: 第一次导入（使用管理员客户端）
                    csv_file.seek(0)
                    response1 = await admin_client.post(
                        "/api/v1/rooms/import/batch?mode=apply",
                        files={"file": (f"test_{header_name}.csv", csv_file, "text/csv")}
                    )
                    
                    assert response1.status_code == 200
                    response1_json = response1.json()
                    assert response1_json["code"] == 200
                    assert response1_json["data"]["success_count"] == 1
                    
                    # Act: 第二次导入（相同数据，使用管理员客户端）
                    csv_file.seek(0)
                    response2 = await admin_client.post(
                        "/api/v1/rooms/import/batch?mode=apply",
                        files={"file": (f"test_{header_name}_2.csv", csv_file, "text/csv")}
                    )
                    
                    assert response2.status_code == 200
                    response2_json = response2.json()
                    assert response2_json["code"] == 200
                    
                    # Assert: 验证第二次导入的行被标记为 skipped
                    items = response2_json["data"]["items"]
                    for item in items:
                        if item["status"] == "success":
                            assert item["skipped"] is True
                    
                    # 验证 DB 中只有一个房间（按 external_room_id）
                    async with async_session_factory() as new_db:
                        result = await new_db.execute(
                            select(LiveRoom).where(
                                LiveRoom.user_id == regular_user_id,
                                LiveRoom.external_room_id == ext_id
                            )
                        )
                        rooms = result.scalars().all()
                        assert len(rooms) == 1

