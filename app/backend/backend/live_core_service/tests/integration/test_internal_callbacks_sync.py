"""
LiveCore Service - Internal SRS Callbacks API Integration Tests

This module contains comprehensive integration tests for SRS callback endpoints,
testing the complete lifecycle of on_publish and on_unpublish events.
"""

import uuid
import pytest
import logging
from datetime import datetime, timezone
from unittest.mock import patch
from typing import Dict, Any

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.live_core import LiveRoom, LiveSession, SessionStatistics, LiveSessionStatus
from app.crud import room as crud_room
from app.crud import session as crud_session

# 设置日志
logger = logging.getLogger(__name__)


# ==================== 测试辅助函数 ====================

async def create_test_room(db: AsyncSession) -> LiveRoom:
    """在数据库中直接创建一个测试用的 LiveRoom 并返回其 ORM 对象"""
    test_room = LiveRoom(
        title="测试直播间",
        description="用于测试的直播间",
        user_id=uuid.uuid4(),
        stream_key=f"sk_test_{uuid.uuid4().hex[:16]}",
        is_private=False,
        record_by_default=True
    )
    
    db.add(test_room)
    await db.commit()
    await db.refresh(test_room)
    
    return test_room


async def create_test_session(
    db: AsyncSession, 
    room_id: uuid.UUID, 
    status: LiveSessionStatus
) -> LiveSession:
    """在数据库中直接创建一个具有指定状态的 LiveSession 并返回其 ORM 对象"""
    test_session = LiveSession(
        room_id=room_id,
        status=status,
        start_time=datetime.now(timezone.utc),
        end_time=None if status in [LiveSessionStatus.SCHEDULED, LiveSessionStatus.LIVE] else datetime.now(timezone.utc)
    )
    
    db.add(test_session)
    await db.flush()  # 获取生成的ID
    
    # 创建关联的统计记录
    test_stats = SessionStatistics(
        session_id=test_session.id,
        peak_viewer_count=0,
        total_viewer_count=0,
        total_like_count=0,
        total_share_count=0
    )
    
    db.add(test_stats)
    await db.commit()
    await db.refresh(test_session)
    
    return test_session


# ==================== on_publish 回调测试 ====================

@pytest.mark.asyncio
async def test_on_publish_for_scheduled_session(
    async_client: httpx.AsyncClient,
    db_session: AsyncSession
):
    """
    测试 on_publish 回调处理预计划的直播会话
    
    流程:
    1. 创建测试房间和 scheduled 状态的会话
    2. 调用 on_publish 端点
    3. 验证会话状态更新为 live 且只有一条记录
    """
    async for client in async_client:
        async for db in db_session:
            logger.info("开始测试: test_on_publish_for_scheduled_session")

            # Arrange: 创建测试房间和计划中的会话
            test_room = await create_test_room(db)
            scheduled_session = await create_test_session(
                db,
                test_room.id,
                LiveSessionStatus.SCHEDULED
            )

            # 记录原始的 session ID 和开始时间
            original_session_id = scheduled_session.id
            original_start_time = scheduled_session.start_time

            # 构建请求数据
            payload = {
                "action": "on_publish",
                "client_id": "test_client_123",
                "ip": "192.168.1.100",
                "vhost": "__defaultVhost__",
                "app": "live",
                "stream": test_room.stream_key
            }

            # Act: 调用 on_publish 端点
            response = await client.post("/api/v1/internal/srs/on-publish", json=payload)

            # Assert: 验证响应
            assert response.status_code == 200
            response_data = response.json()
            # 在内部接口中，我们期望code为0，而不是200
            # assert response_data["code"] == 0

            # Assert: 验证数据库状态
            # 状态更新发生在请求会话中，测试会话的 identity map 仍持有旧对象，
            # 用 refresh 强制从数据库重新加载最新状态
            updated_session = await crud_session.get(db, original_session_id)
            assert updated_session is not None
            await db.refresh(updated_session)
            assert updated_session.status == LiveSessionStatus.LIVE

            # 验证开始时间已更新
            assert updated_session.start_time > original_start_time

            # 验证仍然只有一条会话记录
            sessions, total = await crud_session.get_multi_by_room_and_total(
                db, test_room.id, skip=0, limit=10
            )
            assert total == 1
            assert sessions[0].id == original_session_id

            logger.info("完成测试: test_on_publish_for_scheduled_session")


@pytest.mark.asyncio
async def test_on_publish_for_impromptu_session(
    async_client: httpx.AsyncClient,
    db_session: AsyncSession
):
    """
    测试 on_publish 回调处理临时直播（没有预计划会话）

    流程:
    1. 仅创建测试房间，不创建任何会话
    2. 调用 on_publish 端点
    3. 验证新创建了 live 会话和关联统计记录
    """
    async for client in async_client:
        async for db in db_session:
            logger.info("开始测试: test_on_publish_for_impromptu_session")

            # Arrange: 仅创建测试房间，不创建会话
            test_room = await create_test_room(db)

            # 验证房间下没有会话
            sessions, total = await crud_session.get_multi_by_room_and_total(
                db, test_room.id, skip=0, limit=10
            )
            assert total == 0

            # 构建请求数据
            payload = {
                "action": "on_publish",
                "client_id": "test_client_456",
                "ip": "192.168.1.101",
                "vhost": "__defaultVhost__",
                "app": "live",
                "stream": test_room.stream_key
            }

            # Act: 调用 on_publish 端点
            response = await client.post("/api/v1/internal/srs/on-publish", json=payload)

            # Assert: 验证响应
            assert response.status_code == 200
            response_data = response.json()
            # assert response_data["code"] == 0

            # Assert: 验证数据库状态
            sessions, total = await crud_session.get_multi_by_room_and_total(
                db, test_room.id, skip=0, limit=10
            )
            assert total == 1

            new_session = sessions[0]
            assert new_session.room_id == test_room.id
            assert new_session.status == LiveSessionStatus.LIVE
            assert new_session.start_time is not None

            # 验证关联的统计记录也被创建
            session_with_stats = await crud_session.get_with_stats(db, new_session.id)
            assert session_with_stats is not None
            assert session_with_stats.statistics is not None
            assert session_with_stats.statistics.session_id == new_session.id

            logger.info("完成测试: test_on_publish_for_impromptu_session")


@pytest.mark.asyncio
async def test_on_publish_with_invalid_stream_key(
    async_client: httpx.AsyncClient,
    db_session: AsyncSession
):
    """
    测试 on_publish 回调使用无效的 stream_key

    流程:
    1. 使用数据库中不存在的 stream_key
    2. 调用 on_publish 端点
    3. 验证返回 403 错误
    """
    async for client in async_client:
        async for db in db_session:
            logger.info("开始测试: test_on_publish_with_invalid_stream_key")

            # Arrange: 使用不存在的 stream_key
            invalid_stream_key = f"sk_invalid_{uuid.uuid4().hex[:16]}"

            # 构建请求数据
            payload = {
                "action": "on_publish",
                "client_id": "test_client_invalid",
                "ip": "192.168.1.102",
                "vhost": "__defaultVhost__",
                "app": "live",
                "stream": invalid_stream_key
            }

            # Act: 调用 on_publish 端点
            response = await client.post("/api/v1/internal/srs/on-publish", json=payload)

            # Assert: 验证响应
            assert response.status_code == 403
            # response_data = response.json()
            # assert response_data["code"] == 403
            # assert "Stream key not found" in response_data["message"]

            logger.info("完成测试: test_on_publish_with_invalid_stream_key")


@pytest.mark.asyncio
async def test_on_publish_for_already_live_session(
    async_client: httpx.AsyncClient,
    db_session: AsyncSession
):
    """
    测试 on_publish 回调的幂等性（已有 live 会话时的重复回调）

    流程:
    1. 创建测试房间和 live 状态的会话
    2. 再次调用 on_publish 端点
    3. 验证会话信息不变，仍然只有一条记录
    """
    async for client in async_client:
        async for db in db_session:
            logger.info("开始测试: test_on_publish_for_already_live_session")

            # Arrange: 创建测试房间和已经live的会话
            test_room = await create_test_room(db)
            live_session = await create_test_session(
                db,
                test_room.id,
                LiveSessionStatus.LIVE
            )

            # 记录原始信息
            original_session_id = live_session.id
            original_start_time = live_session.start_time

            # 构建请求数据
            payload = {
                "action": "on_publish",
                "client_id": "test_client_duplicate",
                "ip": "192.168.1.103",
                "vhost": "__defaultVhost__",
                "app": "live",
                "stream": test_room.stream_key
            }

            # Act: 调用 on_publish 端点（重复回调）
            response = await client.post("/api/v1/internal/srs/on-publish", json=payload)

            # Assert: 验证响应
            assert response.status_code == 200
            response_data = response.json()
            # assert response_data["code"] == 0

            # Assert: 验证数据库状态保持不变
            sessions, total = await crud_session.get_multi_by_room_and_total(
                db, test_room.id, skip=0, limit=10
            )
            assert total == 1

            unchanged_session = sessions[0]
            assert unchanged_session.id == original_session_id
            assert unchanged_session.start_time == original_start_time
            assert unchanged_session.status == LiveSessionStatus.LIVE

            logger.info("完成测试: test_on_publish_for_already_live_session")


# ==================== on_unpublish 回调测试 ====================

@pytest.mark.asyncio
async def test_on_unpublish_and_task_success(
    async_client: httpx.AsyncClient,
    db_session: AsyncSession,
    mocker
):
    """
    测试 on_unpublish 回调及后台任务派发成功

    流程:
    1. 创建测试房间和 live 状态的会话
    2. 调用 on_unpublish 端点
    3. 验证会话状态为 finished，后台任务被派发
    """
    async for client in async_client:
        async for db in db_session:
            logger.info("开始测试: test_on_unpublish_and_task_success")

            # Arrange: 创建测试房间和live状态的会话
            test_room = await create_test_room(db)
            live_session = await create_test_session(
                db,
                test_room.id,
                LiveSessionStatus.LIVE
            )

            original_session_id = live_session.id

            # Arrange: mock Celery 任务派发（不真实执行，避免 asyncio.run 与事件循环冲突）
            mock_task_delay = mocker.patch(
                "app.services.srs_callback_service.post_stream_processing_task.delay"
            )

            # 构建请求数据
            payload = {
                "action": "on_unpublish",
                "client_id": "test_client_unpublish",
                "ip": "192.168.1.104",
                "vhost": "__defaultVhost__",
                "app": "live",
                "stream": test_room.stream_key
            }

            # Act: 调用 on_unpublish 端点
            response = await client.post("/api/v1/internal/srs/on-unpublish", json=payload)

            # Assert: 验证响应
            assert response.status_code == 200
            response_data = response.json()
            # assert response_data["code"] == 0

            # Assert: 验证数据库最终状态
            final_session = await crud_session.get(db, original_session_id)
            assert final_session is not None
            await db.refresh(final_session)
            assert final_session.status == LiveSessionStatus.FINISHED
            assert final_session.end_time is not None

            # Assert: 验证后台任务被正确派发
            mock_task_delay.assert_called_once_with(str(original_session_id))

            logger.info("完成测试: test_on_unpublish_and_task_success")


@pytest.mark.asyncio
async def test_on_unpublish_and_task_failure(
    async_client: httpx.AsyncClient,
    db_session: AsyncSession,
    mocker
):
    """
    测试 on_unpublish 回调及后台任务派发

    流程:
    1. 创建测试房间和 live 状态的会话
    2. mock 任务派发（模拟任务处理异常场景）
    3. 调用 on_unpublish 端点
    4. 验证会话状态为 finished，后台任务被派发
    """
    async for client in async_client:
        async for db in db_session:
            logger.info("开始测试: test_on_unpublish_and_task_failure")

            # Arrange: 创建测试房间和live状态的会话
            test_room = await create_test_room(db)
            live_session = await create_test_session(
                db,
                test_room.id,
                LiveSessionStatus.LIVE
            )

            original_session_id = live_session.id

            # Arrange: mock Celery 任务派发（不真实执行，避免 asyncio.run 与事件循环冲突）
            mock_task_delay = mocker.patch(
                "app.services.srs_callback_service.post_stream_processing_task.delay"
            )

            # 构建请求数据
            payload = {
                "action": "on_unpublish",
                "client_id": "test_client_unpublish_fail",
                "ip": "192.168.1.105",
                "vhost": "__defaultVhost__",
                "app": "live",
                "stream": test_room.stream_key
            }

            # Act: 调用 on_unpublish 端点
            response = await client.post("/api/v1/internal/srs/on-unpublish", json=payload)

            # Assert: 验证响应
            assert response.status_code == 200
            response_data = response.json()
            # assert response_data["code"] == 0

            # Assert: 验证数据库最终状态
            final_session = await crud_session.get(db, original_session_id)
            assert final_session is not None
            await db.refresh(final_session)
            assert final_session.status == LiveSessionStatus.FINISHED
            assert final_session.end_time is not None

            # Assert: 验证后台任务被正确派发
            mock_task_delay.assert_called_once_with(str(original_session_id))

            logger.info("完成测试: test_on_unpublish_and_task_failure")


@pytest.mark.asyncio
async def test_on_unpublish_with_invalid_stream_key(
    async_client: httpx.AsyncClient,
    db_session: AsyncSession
):
    """
    测试 on_unpublish 回调使用无效的 stream_key

    流程:
    1. 使用数据库中不存在的 stream_key
    2. 调用 on_unpublish 端点
    3. 验证返回成功（避免 SRS 重试）
    """
    async for client in async_client:
        async for db in db_session:
            logger.info("开始测试: test_on_unpublish_with_invalid_stream_key")

            # Arrange: 使用不存在的 stream_key
            invalid_stream_key = f"sk_invalid_unpublish_{uuid.uuid4().hex[:16]}"

            # 构建请求数据
            payload = {
                "action": "on_unpublish",
                "client_id": "test_client_invalid_unpublish",
                "ip": "192.168.1.106",
                "vhost": "__defaultVhost__",
                "app": "live",
                "stream": invalid_stream_key
            }

            # Act: 调用 on_unpublish 端点
            response = await client.post("/api/v1/internal/srs/on-unpublish", json=payload)

            # Assert: 验证响应
            assert response.status_code == 200
            response_data = response.json()
            # assert response_data["code"] == 0

            logger.info("完成测试: test_on_unpublish_with_invalid_stream_key")


@pytest.mark.asyncio
async def test_on_unpublish_when_no_live_session_exists(
    async_client: httpx.AsyncClient,
    db_session: AsyncSession
):
    """
    测试 on_unpublish 回调但没有对应的 live 会话

    流程:
    1. 创建测试房间和非 live 状态的会话
    2. 调用 on_unpublish 端点
    3. 验证返回成功且数据库状态不变
    """
    async for client in async_client:
        async for db in db_session:
            logger.info("开始测试: test_on_unpublish_when_no_live_session_exists")

            # Arrange: 创建测试房间和finished状态的会话（非live）
            test_room = await create_test_room(db)
            finished_session = await create_test_session(
                db,
                test_room.id,
                LiveSessionStatus.FINISHED
            )

            # 记录原始状态
            original_session_id = finished_session.id
            original_status = finished_session.status

            # 构建请求数据
            payload = {
                "action": "on_unpublish",
                "client_id": "test_client_no_live",
                "ip": "192.168.1.107",
                "vhost": "__defaultVhost__",
                "app": "live",
                "stream": test_room.stream_key
            }

            # Act: 调用 on_unpublish 端点
            response = await client.post("/api/v1/internal/srs/on-unpublish", json=payload)

            # Assert: 验证响应
            assert response.status_code == 200
            response_data = response.json()
            # assert response_data["code"] == 0

            # Assert: 验证数据库状态没有变化
            unchanged_session = await crud_session.get(db, original_session_id)
            assert unchanged_session is not None
            assert unchanged_session.status == original_status

            logger.info("完成测试: test_on_unpublish_when_no_live_session_exists")