"""
LiveCore Service - SRS Internal Callbacks Integration Tests

This module contains comprehensive integration tests for SRS callback endpoints,
verifying API responses, database state changes, and background task execution.
"""
import httpx
import pytest
import uuid
from datetime import datetime, timezone
from unittest.mock import patch

from app.models.live_core import LiveSessionStatus

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

from app.core.config import settings
from sqlalchemy.orm import sessionmaker

# ============================================================================
# Test Helper Functions (假设这些函数在conftest.py或其他地方定义)
# ============================================================================

async def create_test_room(db):
    """在数据库中创建一个测试用的LiveRoom"""
    from app.crud import room as crud_room
    from app.schemas.live_core import LiveRoomCreate
    
    # 生成一个测试用户ID
    test_user_id = uuid.uuid4()
    
    room_create = LiveRoomCreate(
        title="Test Room",
        description="Test room for SRS callbacks",
        is_private=False,
        record_by_default=True
    )
    return await crud_room.create(db, obj_in=room_create, user_id=test_user_id)


async def create_test_session(db, room_id: uuid.UUID, status: LiveSessionStatus):
    """在数据库中创建一个具有指定状态的LiveSession"""
    from app.crud import session as crud_session
    from app.schemas.live_core import LiveSessionCreate
    
    session_create = LiveSessionCreate(
        room_id=room_id,
        status=status,
        start_time=datetime.now(timezone.utc),
        end_time=None,
        video_id=None
    )
    return await crud_session.create_with_stats(db, obj_in=session_create)


# ============================================================================
# on_publish 回调测试用例
# ============================================================================

@pytest.mark.asyncio
async def test_on_publish_for_scheduled_session(async_client, db_session):
    """
    测试on_publish回调处理已有scheduled状态的会话
    验证API响应和数据库状态更新
    """
    async for client in async_client:
        async for db in db_session:
            # Arrange: 创建测试房间和scheduled会话
            test_room = await create_test_room(db)
            scheduled_session = await create_test_session(
                db, test_room.id, LiveSessionStatus.SCHEDULED
            )
            original_session_id = scheduled_session.id
            original_start_time = scheduled_session.start_time

            # 准备请求数据
            payload = {
                "action": "on_publish",
                "client_id": "test_client_123",
                "ip": "192.168.1.100",
                "vhost": "__defaultVhost__",
                "app": "live",
                "stream": test_room.stream_key
            }

            # Act: 调用on_publish端点
            response = await client.post("/api/v1/internal/srs/on-publish", json=payload)

            # Assert: 验证API响应
            assert response.status_code == 200
            response_data = response.json()
            assert response_data["code"] == 0

            # Assert: 验证数据库状态更新
            from app.crud import session as crud_session
            updated_session = await crud_session.get(db, session_id=original_session_id)
            # 1. 创建一个临时的、一次性的数据库引擎
            temp_engine = create_async_engine(settings.DATABASE_URL)

            # 2. 创建一个临时的会话工厂
            TempSessionLocal = sessionmaker(
                bind=temp_engine,
                class_=AsyncSession,
                expire_on_commit=False
            )

            # 3. 使用这个临时的会话来执行查询
            async with TempSessionLocal() as verification_db:
                updated_session = await crud_session.get(verification_db, session_id=original_session_id)

            # 4. 确保关闭临时引擎
            await temp_engine.dispose()

            # ==================================================

            # 现在，用从独立会话中获取的数据进行断言
            assert updated_session is not None
            assert updated_session.status == LiveSessionStatus.LIVE

            # 验证开始时间已更新
            assert updated_session.start_time > original_start_time

            # 验证仍然只有一条会话记录
            sessions, total = await crud_session.get_multi_by_room_and_total(
                db, test_room.id, skip=0, limit=10
            )
            assert total == 1
            assert sessions[0].id == original_session_id


@pytest.mark.asyncio
async def test_on_publish_for_impromptu_session(async_client, db_session):
    """
    测试on_publish回调创建即兴直播会话
    验证新会话和统计记录的创建
    """
    async for client in async_client:
        async for db in db_session:
            # Arrange: 只创建测试房间，不创建任何LiveSession
            test_room = await create_test_room(db)

            # 准备请求数据
            payload = {
                "action": "on_publish",
                "client_id": "test_client_456",
                "ip": "192.168.1.101",
                "vhost": "__defaultVhost__",
                "app": "live",
                "stream": test_room.stream_key
            }

            # Act: 调用on_publish端点
            response = await client.post("/api/v1/internal/srs/on-publish", json=payload)

            # Assert: 验证API响应
            assert response.status_code == 200
            response_data = response.json()
            assert response_data["code"] == 0

            # Assert: 验证新创建的LiveSession记录
            from sqlalchemy import select
            from app.models.live_core import LiveSession
            session_result = await db.execute(
                select(LiveSession).where(LiveSession.room_id == test_room.id)
            )
            new_session = session_result.scalar_one()
            assert new_session.room_id == test_room.id
            assert new_session.status == LiveSessionStatus.LIVE

            # Assert: 验证关联的SessionStatistics记录也被创建
            from app.models.live_core import SessionStatistics
            stats_result = await db.execute(
                select(SessionStatistics).where(SessionStatistics.session_id == new_session.id)
            )
            stats = stats_result.scalar_one()
            assert stats.session_id == new_session.id
            assert stats.peak_viewer_count == 0
            assert stats.total_viewer_count == 0



@pytest.mark.asyncio
async def test_on_publish_with_invalid_stream_key(async_client, db_session):
    """
    测试on_publish回调处理无效的stream_key
    验证返回403 Forbidden错误
    """
    async for client in async_client:
        async for db in db_session:
            # Arrange: 准备无效的stream_key
            invalid_stream_key = "streamkey_invalid_key_12345"
            
            # 准备请求数据
            payload = {
                "action": "on_publish",
                "client_id": "test_client_789",
                "ip": "192.168.1.102",
                "vhost": "__defaultVhost__",
                "app": "live",
                "stream": invalid_stream_key
            }
            
            # Act: 调用on_publish端点
            response = await client.post("/api/v1/internal/srs/on-publish", json=payload)
            
            # Assert: 验证API响应为403 Forbidden
            assert response.status_code == 403
            response_data = response.json()
            assert response_data["code"] == 403
            assert "Stream key not found" in response_data["message"]


@pytest.mark.asyncio
async def test_on_publish_for_already_live_session(async_client, db_session):
    """
    测试on_publish回调处理已经是live状态的会话
    验证幂等性：不创建新会话，不修改现有会话的开始时间
    """
    async for client in async_client:
        async for db in db_session:
            # Arrange: 创建测试房间和已经是live状态的会话
            test_room = await create_test_room(db)
            live_session = await create_test_session(
                db, test_room.id, LiveSessionStatus.LIVE
            )
            original_session_id = live_session.id
            original_start_time = live_session.start_time
            
            # 准备请求数据
            payload = {
                "action": "on_publish",
                "client_id": "test_client_duplicate",
                "ip": "192.168.1.103",
                "vhost": "__defaultVhost__",
                "app": "live",
                "stream": test_room.stream_key
            }
            
            # Act: 再次调用on_publish端点
            response = await client.post("/api/v1/internal/srs/on-publish", json=payload)
            
            # Assert: 验证API响应成功
            assert response.status_code == 200
            response_data = response.json()
            assert response_data["code"] == 0
            
            # Assert: 验证仍然只有一条LiveSession记录
            from sqlalchemy import select, func
            from app.models.live_core import LiveSession
            count_result = await db.execute(
                select(func.count(LiveSession.id)).where(LiveSession.room_id == test_room.id)
            )
            assert count_result.scalar() == 1
            
            # Assert: 验证会话ID和开始时间保持不变
            from app.crud import session as crud_session
            current_session = await crud_session.get(db, session_id=original_session_id)
            assert current_session.id == original_session_id
            assert current_session.start_time == original_start_time


# ============================================================================
# on_unpublish 回调测试用例
# ============================================================================

@pytest.mark.asyncio
async def test_post_stream_processing_task_success(db_session: AsyncSession):
    """
    单元测试：验证后台任务成功执行时的状态流转
    """
    async for db in db_session:
        # Arrange: 准备一个 'finished' 状态的会话
        test_room = await create_test_room(db)
        finished_session = await create_test_session(db, test_room.id, LiveSessionStatus.FINISHED)

        # Act: 直接调用任务函数的核心逻辑（因为我们无法直接await一个celery task）
        # 我们需要测试的是那个被包裹的异步函数
        from app.tasks.session_processing import _process_session_async
        await _process_session_async(db, str(finished_session.id))

        # Assert: 验证最终状态
        from app.crud import session as crud_session
        await db.refresh(finished_session)
        final_session = await crud_session.get(db, finished_session.id)
        assert final_session.status == LiveSessionStatus.READY


@pytest.mark.asyncio
async def test_post_stream_processing_task_failure(db_session: AsyncSession, mocker):
    """
    单元测试：验证后台任务失败时的状态流转
    """
    async for db in db_session:
        # Arrange: 准备一个 'finished' 状态的会话
        test_room = await create_test_room(db)
        finished_session = await create_test_session(db, test_room.id, LiveSessionStatus.FINISHED)

        # Arrange: 模拟核心处理逻辑失败
        mocker.patch("asyncio.sleep", side_effect=Exception("模拟转码失败"))

        # Act: 调用任务的核心逻辑
        from app.tasks.session_processing import _process_session_async
        await _process_session_async(db, str(finished_session.id))

        # Assert: 验证最终状态
        await db.refresh(finished_session)
        from app.crud import session as crud_session
        final_session = await crud_session.get(db, finished_session.id)
        assert final_session.status == LiveSessionStatus.ERROR


@pytest.mark.asyncio
async def test_on_unpublish_updates_status_and_dispatches_task(
    async_client: httpx.AsyncClient,
    db_session: AsyncSession,
    mocker  # 引入 mocker fixture
):
    """
    测试 on_unpublish 接口的核心职责：
    1. 正确更新会话状态为 'finished'。
    2. 成功派发后台处理任务。
    """
    async for client in async_client:
        async for db in db_session:

            # Arrange: 创建一个 live 状态的会话
            test_room = await create_test_room(db)
            live_session = await create_test_session(db, test_room.id, LiveSessionStatus.LIVE)
            original_session_id = live_session.id

            # Arrange: 使用 mocker "监听" Celery 任务的 .delay() 方法
            # 我们并不实际执行任务，只验证它是否被正确地调用了
            mock_task_delay = mocker.patch(
                "app.services.srs_callback_service.post_stream_processing_task.delay"
            )

            # 准备请求数据
            payload = {
                "action": "on_unpublish",
                "client_id": "test_client_end",
                "ip": "192.168.1.104",
                "vhost": "__defaultVhost__",
                "app": "live",
                "stream": test_room.stream_key
            }

            # Act: 调用 on_unpublish 端点
            response = await client.post("/api/v1/internal/srs/on-unpublish", json=payload)

            # Assert 1: 验证 API 响应是成功的
            assert response.status_code == 200
            assert response.json()["code"] == 0

            # Assert 2: 验证数据库状态被立即更新为 'finished'
            # 因为不再有异步任务的干扰，我们可以安全地使用测试会话db来验证
            await db.refresh(live_session)
            assert live_session.status == LiveSessionStatus.FINISHED
            assert live_session.end_time is not None

            # Assert 3: 验证后台任务被准确地调用了一次，并且传递了正确的session_id
            mock_task_delay.assert_called_once_with(str(original_session_id))


@pytest.mark.asyncio
async def test_on_unpublish_with_invalid_stream_key(async_client, db_session):
    """
    测试on_unpublish回调处理无效的stream_key
    验证返回成功响应以避免SRS重试
    """
    async for client in async_client:
        async for db in db_session:
            # Arrange: 准备无效的stream_key
            invalid_stream_key = "streamkey_invalid_unpublish_key"
            
            # 准备请求数据
            payload = {
                "action": "on_unpublish",
                "client_id": "test_client_invalid",
                "ip": "192.168.1.106",
                "vhost": "__defaultVhost__",
                "app": "live",
                "stream": invalid_stream_key
            }
            
            # Act: 调用on_unpublish端点
            response = await client.post("/api/v1/internal/srs/on-unpublish", json=payload)
            
            # Assert: 验证API响应为成功，避免SRS重试
            assert response.status_code == 200
            response_data = response.json()
            assert response_data["code"] == 0


@pytest.mark.asyncio
async def test_on_unpublish_when_no_live_session_exists(async_client, db_session):
    """
    测试on_unpublish回调当不存在live状态会话时的处理
    验证正常返回成功响应，数据库无变化
    """
    async for client in async_client:
        async for db in db_session:
            # Arrange: 创建测试房间和非live状态的会话
            test_room = await create_test_room(db)
            scheduled_session = await create_test_session(
                db, test_room.id, LiveSessionStatus.SCHEDULED
            )
            original_status = scheduled_session.status
            
            # 准备请求数据
            payload = {
                "action": "on_unpublish",
                "client_id": "test_client_no_live",
                "ip": "192.168.1.107",
                "vhost": "__defaultVhost__",
                "app": "live",
                "stream": test_room.stream_key
            }
            
            # Act: 调用on_unpublish端点
            response = await client.post("/api/v1/internal/srs/on-unpublish", json=payload)
            
            # Assert: 验证API响应成功
            assert response.status_code == 200
            response_data = response.json()
            assert response_data["code"] == 0
            
            # Assert: 验证数据库状态没有发生变化
            from app.crud import session as crud_session
            unchanged_session = await crud_session.get(db, session_id=scheduled_session.id)
            assert unchanged_session.status == original_status
            assert unchanged_session.end_time is None 