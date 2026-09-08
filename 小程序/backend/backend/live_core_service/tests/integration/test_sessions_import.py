"""
LiveCore Service - Session Import API Integration Tests

This module contains integration tests for the session import API endpoints,
testing the complete import session workflow with database validation.

遵循测试代码生成提示词母版 - Pragmatic 测试策略（真实 DB + 完整链路）
"""

import pytest
import uuid
from datetime import datetime, timezone
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.live_core import LiveRoom, LiveSession, SessionStatistics
from tests.utils import create_test_room
from tests.conftest import async_session_factory
from fastapi import FastAPI
from app.api.v1.api import api_router
from app.core.deps import get_db, get_current_user
from httpx import AsyncClient
import time


# ==================== Test Fixtures ====================

@pytest.fixture
async def async_client_with_public_id(regular_user_id: uuid.UUID, regular_user_role: str) -> AsyncClient:
    """
    提供带有 public_id 和 role 的异步客户端（用于 session_import 测试）
    
    注意：这个 fixture 覆盖了 get_current_user 依赖，添加了 public_id 和 role 字段
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


# ==================== API Integration Tests (Pragmatic) ====================

@pytest.mark.asyncio
async def test_import_session_success_with_playback_url(
    async_client_with_public_id, 
    db_session,
    regular_user_id: uuid.UUID
):
    """
    测试成功导入会话（携带 playback_url）
    
    策略：Pragmatic - 使用真实 DB + AsyncClient 验证完整链路
    """
    async for client in async_client_with_public_id:
        async for db in db_session:
            # ===== Arrange (准备) =====
            # 使用regular_user_id创建测试房间（与JWT token中的user_id一致）
            room = await create_test_room_for_import(db, regular_user_id)
            room_id = str(room.id)
            
            # 准备导入会话的数据
            start_time = datetime.now(timezone.utc).isoformat()
            end_time = datetime.now(timezone.utc).isoformat()
            import_payload = {
                "start_time": start_time,
                "end_time": end_time,
                "status": "finished",
                "playback_url": "https://cdn.example.com/videos/test_playback_123.m3u8",
                "title": "导入的历史会话",
                "description": "从旧系统迁移"
            }
            
            # ===== Act (执行) =====
            # 注意：async_client_with_public_id已经覆盖了get_current_user，所以不需要额外的headers
            response = await client.post(
                f"/api/v1/rooms/{room_id}/sessions/import",
                json=import_payload
            )
            
            # ASSERT: 验证 HTTP 响应
            assert response.status_code == 200, f"期望 200，实际 {response.status_code}: {response.text}"
            
            response_json = response.json()
            # 验证统一响应结构
            assert "code" in response_json
            assert "message" in response_json
            assert "data" in response_json
            assert "timestamp" in response_json
            
            assert response_json["code"] == 200
            assert response_json["message"] == "success"
            
            # 验证返回的会话数据
            session_data = response_json["data"]
            assert "id" in session_data
            assert session_data["room_id"] == room_id
            assert session_data["status"] == "finished"
            assert session_data["playback_url"] == import_payload["playback_url"]
            
            session_id = session_data["id"]
            
            # ASSERT: 使用新会话验证 DB 状态（避免 identity map 缓存）
            async with async_session_factory() as new_db:
                # 查询会话记录
                result = await new_db.execute(
                    select(LiveSession).where(LiveSession.id == uuid.UUID(session_id))
                )
                db_session_obj = result.scalar_one_or_none()
                
                assert db_session_obj is not None, "会话应该被创建在数据库中"
                assert db_session_obj.room_id == room.id
                assert db_session_obj.playback_url == import_payload["playback_url"]
                assert db_session_obj.status.value == "finished"
                
                # 验证关联的统计记录也被创建
                stats_result = await new_db.execute(
                    select(SessionStatistics).where(SessionStatistics.session_id == db_session_obj.id)
                )
                stats = stats_result.scalar_one_or_none()
                assert stats is not None, "统计记录应该被自动创建"
            
            break
        break


@pytest.mark.asyncio
async def test_import_session_with_status_ready(
    async_client_with_public_id, 
    db_session,
    regular_user_id: uuid.UUID
):
    """
    测试导入 status='ready' 的会话
    
    策略：Pragmatic
    """
    async for client in async_client_with_public_id:
        async for db in db_session:
            # ARRANGE
            # ===== Arrange (准备) =====
            # 使用regular_user_id（从conftest.py获取）
            room = await create_test_room_for_import(db, regular_user_id)
            
            import_payload = {
                "start_time": datetime.now(timezone.utc).isoformat(),
                "status": "ready",
                "playback_url": "https://cdn.example.com/videos/ready_session.m3u8"
            }
            
            # ACT
            response = await client.post(
                f"/api/v1/rooms/{str(room.id)}/sessions/import",
                json=import_payload
            )
            
            # ASSERT
            assert response.status_code == 200
            response_json = response.json()
            assert response_json["code"] == 200
            assert response_json["data"]["status"] == "ready"
            
            # DB 验证
            async with async_session_factory() as new_db:
                result = await new_db.execute(
                    select(LiveSession).where(
                        LiveSession.room_id == room.id,
                        LiveSession.playback_url == import_payload["playback_url"]
                    )
                )
                session = result.scalar_one_or_none()
                assert session is not None
                assert session.status.value == "ready"
            
            break
        break


@pytest.mark.asyncio
async def test_import_session_invalid_status_fails(
    async_client_with_public_id, 
    db_session,
    regular_user_id: uuid.UUID
):
    """
    测试导入非法 status（不是 finished/ready）应失败
    
    策略：Pragmatic - 验证参数校验
    """
    async for client in async_client_with_public_id:
        async for db in db_session:
            # ARRANGE
            # ===== Arrange (准备) =====
            # 使用regular_user_id（从conftest.py获取）
            room = await create_test_room_for_import(db, regular_user_id)
            
            # 使用当前实现不接受的 status（实现仅允许 'finished'/'ready'/'live'）
            import_payload = {
                "start_time": datetime.now(timezone.utc).isoformat(),
                "status": "invalid_status",
                "playback_url": "https://cdn.example.com/videos/invalid.m3u8"
            }
            
            # ACT
            response = await client.post(
                f"/api/v1/rooms/{str(room.id)}/sessions/import",
                json=import_payload
            )
            
            # ASSERT: 非法 status 应返回 400 或 422（Pydantic 校验通常返回 422）
            assert response.status_code in [400, 422]
            if response.status_code == 400:
                response_json = response.json()
                assert response_json["code"] == 4001  # 参数校验失败
            
            # DB 验证：不应创建会话
            async with async_session_factory() as new_db:
                result = await new_db.execute(
                    select(LiveSession).where(LiveSession.room_id == room.id)
                )
                sessions = result.scalars().all()
                assert len(sessions) == 0, "非法参数不应创建会话"
            
            break
        break


@pytest.mark.asyncio
async def test_import_session_missing_playback_url_fails(
    async_client_with_public_id, 
    db_session,
    regular_user_id: uuid.UUID
):
    """
    测试缺少 playback_url 应失败
    
    策略：Pragmatic
    """
    async for client in async_client_with_public_id:
        async for db in db_session:
            # ARRANGE
            # ===== Arrange (准备) =====
            # 使用regular_user_id（从conftest.py获取）
            room = await create_test_room_for_import(db, regular_user_id)
            
            # 不提供 playback_url
            import_payload = {
                "start_time": datetime.now(timezone.utc).isoformat(),
                "status": "finished"
                # 缺少 playback_url
            }
            
            # ACT
            response = await client.post(
                f"/api/v1/rooms/{str(room.id)}/sessions/import",
                json=import_payload
            )
            
            # ASSERT: 应返回 400 或 422 错误（Pydantic 校验）
            assert response.status_code in [400, 422]
            
            break
        break


@pytest.mark.asyncio
async def test_import_session_room_not_found_fails(async_client_with_public_id):
    """
    测试导入到不存在的房间应失败
    
    策略：Pragmatic
    """
    async for client in async_client_with_public_id:
        # ARRANGE: 使用不存在的房间 ID
        nonexistent_room_id = str(uuid.uuid4())
        
        import_payload = {
            "start_time": datetime.now(timezone.utc).isoformat(),
            "status": "finished",
            "playback_url": "https://cdn.example.com/videos/test.m3u8"
        }
        
        # ACT
        response = await client.post(
            f"/api/v1/rooms/{nonexistent_room_id}/sessions/import",
            json=import_payload
        )
        
        # ASSERT: 应返回 404
        assert response.status_code == 404
        response_json = response.json()
        assert response_json["code"] == 2001  # 资源不存在
        
        break


@pytest.mark.asyncio
async def test_import_session_permission_denied_fails(
    async_client_with_public_id, 
    db_session,
    another_user_id: uuid.UUID
):
    """
    测试导入到其他用户的房间应失败（权限不足）
    
    策略：Pragmatic
    """
    async for client in async_client_with_public_id:
        async for db in db_session:
            # ===== Arrange (准备) =====
            # 创建属于另一个用户的房间（使用another_user_id，不同于认证用户的ID）
            room = await create_test_room_for_import(db, another_user_id)
            
            import_payload = {
                "start_time": datetime.now(timezone.utc).isoformat(),
                "status": "finished",
                "playback_url": "https://cdn.example.com/videos/test.m3u8"
            }
            
            # ACT
            response = await client.post(
                f"/api/v1/rooms/{str(room.id)}/sessions/import",
                json=import_payload
            )
            
            # ASSERT: 应返回 403
            assert response.status_code == 403
            response_json = response.json()
            assert response_json["code"] == 3002  # 权限不足
            
            # DB 验证：不应创建会话
            async with async_session_factory() as new_db:
                result = await new_db.execute(
                    select(LiveSession).where(LiveSession.room_id == room.id)
                )
                sessions = result.scalars().all()
                assert len(sessions) == 0
            
            break
        break


@pytest.mark.asyncio
async def test_import_session_invalid_playback_url_format_fails(
    async_client_with_public_id, 
    db_session,
    regular_user_id: uuid.UUID
):
    """
    测试非法 playback_url 格式应失败
    
    策略：Pragmatic
    """
    async for client in async_client_with_public_id:
        async for db in db_session:
            # ARRANGE
            # ===== Arrange (准备) =====
            # 使用regular_user_id（从conftest.py获取）
            room = await create_test_room_for_import(db, regular_user_id)
            
            # 不以 http:// 或 https:// 开头的 URL
            import_payload = {
                "start_time": datetime.now(timezone.utc).isoformat(),
                "status": "finished",
                "playback_url": "ftp://invalid.url/video.m3u8"  # 非法协议
            }
            
            # ACT
            response = await client.post(
                f"/api/v1/rooms/{str(room.id)}/sessions/import",
                json=import_payload
            )
            
            # ASSERT: 应返回 400 或 422（Pydantic validator）
            assert response.status_code in [400, 422]
            
            break
        break


@pytest.mark.asyncio
async def test_import_session_playback_url_too_long_fails(
    async_client_with_public_id, 
    db_session,
    regular_user_id: uuid.UUID
):
    """
    测试 playback_url 长度超过 1024 字符应失败
    
    策略：Pragmatic - 验证参数长度限制
    """
    async for client in async_client_with_public_id:
        async for db in db_session:
            # ARRANGE
            # ===== Arrange (准备) =====
            # 使用regular_user_id（从conftest.py获取）
            room = await create_test_room_for_import(db, regular_user_id)
            
            # 创建超过 1024 字符的 playback_url
            # 基础 URL 长度约 30 字符，需要额外 995+ 字符
            long_path = "x" * 1000
            long_playback_url = f"https://cdn.example.com/videos/{long_path}.m3u8"
            assert len(long_playback_url) > 1024, f"URL 长度应为 {len(long_playback_url)}，应超过 1024"
            
            import_payload = {
                "start_time": datetime.now(timezone.utc).isoformat(),
                "status": "finished",
                "playback_url": long_playback_url
            }
            
            # ACT
            response = await client.post(
                f"/api/v1/rooms/{str(room.id)}/sessions/import",
                json=import_payload
            )
            
            # ASSERT: 应返回 422（Pydantic 校验失败）或 400（业务校验）
            assert response.status_code in [400, 422], f"超长 playback_url 应返回错误，实际: {response.status_code}"
            
            if response.status_code == 400:
                response_json = response.json()
                assert response_json["code"] == 4001  # 参数校验失败
            
            # DB 验证：不应创建会话
            async with async_session_factory() as new_db:
                from sqlalchemy import select
                result = await new_db.execute(
                    select(LiveSession).where(LiveSession.room_id == room.id)
                )
                sessions = result.scalars().all()
                assert len(sessions) == 0, "超长 URL 不应创建会话"
            
            break
        break


@pytest.mark.asyncio
async def test_import_session_playback_url_exactly_1024_chars_success(
    async_client_with_public_id, 
    db_session,
    regular_user_id: uuid.UUID
):
    """
    测试 playback_url 恰好 1024 字符应成功
    
    策略：Pragmatic - 验证边界条件
    """
    async for client in async_client_with_public_id:
        async for db in db_session:
            # ARRANGE
            # ===== Arrange (准备) =====
            # 使用regular_user_id（从conftest.py获取）
            room = await create_test_room_for_import(db, regular_user_id)
            
            # 创建恰好 1024 字符的 playback_url
            # "https://cdn.example.com/videos/" = 32 字符，剩余 992 字符用于路径
            base_url = "https://cdn.example.com/videos/"
            path_part = "x" * (1024 - len(base_url) - len(".m3u8"))
            exact_length_url = f"{base_url}{path_part}.m3u8"
            assert len(exact_length_url) == 1024, f"URL 长度应为 1024，实际: {len(exact_length_url)}"
            
            import_payload = {
                "start_time": datetime.now(timezone.utc).isoformat(),
                "status": "finished",
                "playback_url": exact_length_url
            }
            
            # ACT
            response = await client.post(
                f"/api/v1/rooms/{str(room.id)}/sessions/import",
                json=import_payload
            )
            
            # ASSERT: 应该成功（1024 字符是允许的最大长度）
            assert response.status_code == 200, f"恰好 1024 字符的 URL 应成功，实际: {response.status_code}"
            
            response_json = response.json()
            assert response_json["code"] == 200
            assert response_json["data"]["playback_url"] == exact_length_url
            
            # DB 验证
            async with async_session_factory() as new_db:
                from sqlalchemy import select
                result = await new_db.execute(
                    select(LiveSession).where(LiveSession.id == uuid.UUID(response_json["data"]["id"]))
                )
                session = result.scalar_one_or_none()
                assert session is not None
                assert session.playback_url == exact_length_url
                assert len(session.playback_url) == 1024
            
            break
        break


# ==================== 自检清单 ====================
"""
✅ 是否修改了任何已有测试/fixture/配置？ - 否（仅新增文件）
✅ 是否使用 `async for` 解包 `db_session/async_client`？ - 是
✅ API 调用后的 DB 校验是否用 `async_session_factory` 新会话？ - 是
✅ 是否覆盖了 Import Session 的成功与失败路径？ - 是
  - 成功：finished/ready 状态、边界条件（1024 字符 URL）
  - 失败：非法 status、缺少 playback_url、房间不存在、权限不足、URL 格式错误、URL 超长
✅ 是否断言统一响应结构 code/message/data/timestamp？ - 是
"""

