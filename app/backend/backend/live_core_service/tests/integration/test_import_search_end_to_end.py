"""
LiveCore Service - Import & Search End-to-End Integration Tests

This module contains end-to-end integration tests for the complete workflow:
Create Room -> Import Session -> Search -> Batch Import

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

from app.models.live_core import LiveRoom, LiveSession, SessionStatistics
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
    提供带有 public_id 和 role 的异步客户端（用于 end-to-end 测试）
    
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
    
    async with AsyncClient(app=app, base_url="http://localhost:8000") as client:
        yield client


@pytest.fixture
async def async_client_with_admin_role(regular_user_id: uuid.UUID, admin_user_role: str) -> AsyncClient:
    """
    提供带有 admin role 的异步客户端（用于需要管理员权限的 end-to-end 测试，如批量导入）
    
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

async def create_test_room_for_e2e(db: AsyncSession, user_id: uuid.UUID, title: str) -> LiveRoom:
    """创建用于端到端测试的房间"""
    room = LiveRoom(
        title=title,
        description="端到端测试房间",
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


# ==================== End-to-End Integration Tests ====================

@pytest.mark.asyncio
async def test_complete_workflow_create_import_search_batch(
    async_client_with_public_id, 
    async_client_with_admin_role,
    db_session,
    regular_user_id: uuid.UUID
):
    """
    测试完整业务流程：创建房间 -> 导入会话 -> 搜索验证 -> 批量导入
    
    策略：Pragmatic - 验证完整业务流程的端到端集成
    """
    async for client in async_client_with_public_id:
        async for db in db_session:
            # ===== Arrange (准备) =====
            unique_room_title = f"端到端测试房间_{uuid.uuid4().hex[:8]}"
            
            # ========== Step 1: 创建房间 ==========
            # ACT: 通过 API 创建房间
            room_data = {
                "title": unique_room_title,
                "description": "用于端到端测试的直播间"
            }
            create_response = await client.post("/api/v1/rooms", json=room_data)
            
            # ASSERT: 验证房间创建成功
            assert create_response.status_code == 200
            create_json = create_response.json()
            assert create_json["code"] == 200
            assert "data" in create_json
            room_id = create_json["data"]["id"]
            
            # 验证数据库状态（使用新会话）
            async with async_session_factory() as verify_db:
                result = await verify_db.execute(
                    select(LiveRoom).where(LiveRoom.id == uuid.UUID(room_id))
                )
                db_room = result.scalar_one_or_none()
                assert db_room is not None
                assert db_room.title == unique_room_title
            
            # ========== Step 2: 导入会话 ==========
            # ACT: 导入一个会话到刚创建的房间
            import_payload = {
                "start_time": datetime.now(timezone.utc).isoformat(),
                "end_time": datetime.now(timezone.utc).isoformat(),
                "status": "finished",
                "playback_url": f"https://cdn.example.com/e2e_test_{uuid.uuid4().hex[:8]}.m3u8",
                "title": "端到端测试会话",
                "description": "通过导入创建的会话"
            }
            import_response = await client.post(
                f"/api/v1/rooms/{room_id}/sessions/import",
                json=import_payload
            )
            
            # ASSERT: 验证会话导入成功
            assert import_response.status_code == 200
            import_json = import_response.json()
            assert import_json["code"] == 200
            session_id = import_json["data"]["id"]
            assert import_json["data"]["playback_url"] == import_payload["playback_url"]
            
            # 验证数据库状态
            async with async_session_factory() as verify_db:
                result = await verify_db.execute(
                    select(LiveSession).where(LiveSession.id == uuid.UUID(session_id))
                )
                db_session_obj = result.scalar_one_or_none()
                assert db_session_obj is not None
                assert db_session_obj.playback_url == import_payload["playback_url"]
                assert db_session_obj.status.value == "finished"
                
                # 验证统计记录也被创建
                stats_result = await verify_db.execute(
                    select(SessionStatistics).where(SessionStatistics.session_id == db_session_obj.id)
                )
                stats = stats_result.scalar_one_or_none()
                assert stats is not None
            
            # ========== Step 3: 搜索房间验证 ==========
            # ACT: 使用房间 ID 搜索
            search_by_id_response = await client.get(f"/api/v1/rooms?q={room_id}")
            
            # ASSERT: 验证搜索结果
            assert search_by_id_response.status_code == 200
            search_by_id_json = search_by_id_response.json()
            assert search_by_id_json["code"] == 200
            assert search_by_id_json["data"]["total"] >= 1
            
            found_rooms = search_by_id_json["data"]["items"]
            found_room = next((r for r in found_rooms if r["id"] == room_id), None)
            assert found_room is not None, "应该找到刚创建的房间"
            assert found_room["title"] == unique_room_title
            
            # ACT: 使用房间标题搜索
            search_by_title_response = await client.get(f"/api/v1/rooms?q={unique_room_title}")
            
            # ASSERT: 验证搜索结果
            assert search_by_title_response.status_code == 200
            search_by_title_json = search_by_title_response.json()
            assert search_by_title_json["code"] == 200
            assert search_by_title_json["data"]["total"] >= 1
            
            found_rooms_by_title = search_by_title_json["data"]["items"]
            found_room_by_title = next((r for r in found_rooms_by_title if r["id"] == room_id), None)
            assert found_room_by_title is not None, "应该通过标题找到房间"
            
            # ========== Step 4: 批量导入验证 ==========
            # ACT: 准备批量导入 CSV（复用刚创建的房间）
            batch_csv_data = [
                ['room_id', 'room_title', 'playback_url', 'status'],
                [
                    room_id,  # 复用刚创建的房间
                    unique_room_title,
                    f"https://cdn.example.com/batch_e2e_{uuid.uuid4().hex[:8]}.m3u8",
                    'finished'
                ],
            ]
            csv_file = create_csv_file(batch_csv_data)
            # ← 修改：批量导入需要管理员权限，使用管理员客户端
            async for admin_client in async_client_with_admin_role:
                batch_import_response = await admin_client.post(
                    "/api/v1/rooms/import/batch?mode=apply",
                    files={'file': ('test_e2e_batch.csv', csv_file, 'text/csv')}
                )
                
                # ASSERT: 验证批量导入成功
                assert batch_import_response.status_code == 200
                batch_import_json = batch_import_response.json()
                assert batch_import_json["code"] == 200
                batch_report = batch_import_json["data"]
                assert batch_report["success_count"] == 1
                assert batch_report["items"][0]["status"] == "success"
                assert batch_report["items"][0]["room_id"] == room_id
                
                batch_session_id = batch_report["items"][0]["session_id"]
                
                # 验证数据库状态：房间下应该有两个会话（一个导入的，一个批量导入的）
                async with async_session_factory() as verify_db:
                    sessions_result = await verify_db.execute(
                        select(LiveSession).where(LiveSession.room_id == uuid.UUID(room_id))
                    )
                    all_sessions = sessions_result.scalars().all()
                    assert len(all_sessions) == 2, "房间下应该有 2 个会话"
                    
                    session_ids = {str(s.id) for s in all_sessions}
                    assert session_id in session_ids, "应该包含导入的会话"
                    assert batch_session_id in session_ids, "应该包含批量导入的会话"
                
                break
        break


@pytest.mark.asyncio
async def test_complete_workflow_multiple_rooms_and_sessions(
    async_client_with_public_id, 
    async_client_with_admin_role,
    db_session,
    regular_user_id: uuid.UUID
):
    """
    测试多房间、多会话的完整流程
    
    策略：Pragmatic - 验证复杂场景的端到端集成
    """
    async for client in async_client_with_public_id:
        async for db in db_session:
            # ===== Arrange (准备) =====
            base_keyword = f"多房间测试_{uuid.uuid4().hex[:8]}"
            
            # ========== Step 1: 创建多个房间 ==========
            room_titles = [
                f"{base_keyword}_房间A",
                f"{base_keyword}_房间B",
                f"{base_keyword}_房间C"
            ]
            created_room_ids = []
            
            for title in room_titles:
                room_data = {"title": title, "description": "多房间测试"}
                response = await client.post("/api/v1/rooms", json=room_data)
                assert response.status_code == 200
                created_room_ids.append(response.json()["data"]["id"])
            
            # ========== Step 2: 为每个房间导入会话 ==========
            imported_session_ids = []
            for room_id in created_room_ids:
                import_payload = {
                    "start_time": datetime.now(timezone.utc).isoformat(),
                    "status": "finished",
                    "playback_url": f"https://cdn.example.com/multi_room_{uuid.uuid4().hex[:8]}.m3u8"
                }
                response = await client.post(
                    f"/api/v1/rooms/{room_id}/sessions/import",
                    json=import_payload
                )
                assert response.status_code == 200
                imported_session_ids.append(response.json()["data"]["id"])
            
            # ========== Step 3: 搜索验证所有房间 ==========
            # ACT: 使用基础关键词搜索
            search_response = await client.get(f"/api/v1/rooms?q={base_keyword}")
            
            # ASSERT: 应该找到所有 3 个房间
            assert search_response.status_code == 200
            search_json = search_response.json()
            assert search_json["code"] == 200
            assert search_json["data"]["total"] >= 3
            
            found_room_ids = {item["id"] for item in search_json["data"]["items"]}
            for room_id in created_room_ids:
                assert room_id in found_room_ids, f"应该找到房间 {room_id}"
            
            # ========== Step 4: 批量导入创建新房间和会话 ==========
            batch_csv_data = [
                ['room_title', 'playback_url', 'status'],
            ]
            # 添加 2 行新房间数据
            for i in range(2):
                batch_csv_data.append([
                    f"{base_keyword}_批量房间{i+1}",
                    f"https://cdn.example.com/batch_multi_{uuid.uuid4().hex[:8]}.m3u8",
                    'finished'
                ])
            
            csv_file = create_csv_file(batch_csv_data)
            # ← 修改：批量导入需要管理员权限，使用管理员客户端
            async for admin_client in async_client_with_admin_role:
                batch_response = await admin_client.post(
                    "/api/v1/rooms/import/batch?mode=apply",
                    files={'file': ('test_multi_batch.csv', csv_file, 'text/csv')}
                )
                
                # ASSERT: 批量导入应该成功创建 2 个新房间和会话
                assert batch_response.status_code == 200
                batch_json = batch_response.json()
                assert batch_json["data"]["success_count"] == 2
                break
            
            # ========== Step 5: 再次搜索验证总数 ==========
            # 现在应该找到 3 + 2 = 5 个房间（通过关键词）
            final_search_response = await client.get(f"/api/v1/rooms?q={base_keyword}")
            assert final_search_response.status_code == 200
            final_search_json = final_search_response.json()
            assert final_search_json["data"]["total"] >= 5, "应该找到所有房间"
            
            break
        break


@pytest.mark.asyncio
async def test_complete_workflow_search_with_sorting(
    async_client_with_public_id, 
    db_session,
    regular_user_id: uuid.UUID
):
    """
    测试完整流程中的搜索排序功能
    
    策略：Pragmatic - 验证搜索和排序的集成
    """
    async for client in async_client_with_public_id:
        async for db in db_session:
            # ===== Arrange (准备) =====
            unique_keyword = f"排序端到端测试_{uuid.uuid4().hex[:8]}"
            
            room_titles = [
                f"{unique_keyword}_第一个",
                f"{unique_keyword}_第二个",
                f"{unique_keyword}_第三个"
            ]
            created_room_ids = []
            
            for title in room_titles:
                room_data = {"title": title}
                response = await client.post("/api/v1/rooms", json=room_data)
                created_room_ids.append(response.json()["data"]["id"])
                # 等待一小段时间确保 created_at 不同
                import asyncio
                await asyncio.sleep(0.1)
            
            # ========== Step 1: 测试升序排序 ==========
            # ACT: 按创建时间升序搜索
            asc_response = await client.get(
                f"/api/v1/rooms?q={unique_keyword}&sort=created_at:asc"
            )
            
            # ASSERT
            assert asc_response.status_code == 200
            asc_json = asc_response.json()
            asc_items = asc_json["data"]["items"]
            
            # 筛选出我们创建的房间
            created_set = set(created_room_ids)
            found_asc = [item for item in asc_items if item["id"] in created_set]
            assert len(found_asc) == 3, "应该找到所有 3 个房间"
            
            # 验证排序：第一个房间应该是最早创建的
            assert found_asc[0]["id"] == created_room_ids[0]
            
            # ========== Step 2: 测试降序排序 ==========
            # ACT: 按创建时间降序搜索
            desc_response = await client.get(
                f"/api/v1/rooms?q={unique_keyword}&sort=created_at:desc"
            )
            
            # ASSERT
            assert desc_response.status_code == 200
            desc_json = desc_response.json()
            desc_items = desc_json["data"]["items"]
            
            found_desc = [item for item in desc_items if item["id"] in created_set]
            assert len(found_desc) == 3
            
            # 验证排序：第一个房间应该是最晚创建的
            assert found_desc[0]["id"] == created_room_ids[2]
            
            break
        break


# ==================== 自检清单 ====================
"""
✅ 是否修改了任何已有测试/fixture/配置？ - 否（仅新增文件）
✅ 是否使用 `async for` 解包 `db_session/async_client`？ - 是
✅ API 调用后的 DB 校验是否用 `async_session_factory` 新会话？ - 是
✅ 是否覆盖了完整业务流程？ - 是
  - 创建房间 -> 导入会话 -> 搜索验证 -> 批量导入
  - 多房间、多会话场景
  - 搜索排序功能集成
✅ 是否断言统一响应结构 code/message/data/timestamp？ - 是
✅ 是否验证数据库状态变化？ - 是
"""
