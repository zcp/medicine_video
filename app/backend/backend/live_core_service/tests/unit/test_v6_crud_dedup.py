"""
LiveCore Service - V6 CRUD Deduplication Unit Tests

This module contains unit tests for V6 deduplication-related CRUD operations:
- Room CRUD: get_by_external_id
- Session CRUD: get_by_room_and_playback_hash
- Partial unique index constraints
"""

import pytest
import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.crud import room as crud_room
from app.crud import session as crud_session
from app.schemas.live_core import LiveRoomCreate, LiveSessionCreate
from app.models.live_core import LiveRoom, LiveSession, LiveSessionStatus
from app.services.utils_playback import calc_playback_url_hash
from app.core.exceptions import DatabaseIntegrityException


# ==================== Room CRUD: get_by_external_id ====================

@pytest.mark.asyncio
async def test_get_by_external_id_found(db_session, test_user):
    """
    测试根据 (user_id, external_room_id) 查找房间 - 找到的情况
    """
    async for db in db_session:
        async for user in test_user:
            # Arrange: 创建一个带 external_room_id 的房间
            room_data = LiveRoomCreate(
                title="测试房间",
                description="用于测试的房间",
                is_private=False,
                record_by_default=True
            )
            created_room = await crud_room.create(
                db=db,
                obj_in=room_data,
                user_id=user['public_id']
            )
            
            # 设置 external_room_id
            created_room.external_room_id = "ext_room_123"
            await db.commit()
            await db.refresh(created_room)
            
            # Act: 根据 external_room_id 查找
            found_room = await crud_room.get_by_external_id(
                db=db,
                user_id=user['public_id'],
                external_room_id="ext_room_123"
            )
            
            # Assert
            assert found_room is not None
            assert found_room.id == created_room.id
            assert found_room.user_id == user['public_id']
            assert found_room.external_room_id == "ext_room_123"
            assert found_room.title == created_room.title


@pytest.mark.asyncio
async def test_get_by_external_id_not_found(db_session, test_user):
    """
    测试根据 (user_id, external_room_id) 查找房间 - 未找到的情况
    """
    async for db in db_session:
        async for user in test_user:
            # Act: 查找不存在的 external_room_id
            found_room = await crud_room.get_by_external_id(
                db=db,
                user_id=user['public_id'],
                external_room_id="non_existent_ext_id"
            )
            
            # Assert
            assert found_room is None


@pytest.mark.asyncio
async def test_get_by_external_id_different_user(db_session, test_user):
    """
    测试不同用户的 external_room_id 不会冲突
    """
    async for db in db_session:
        async for user in test_user:
            # Arrange: 创建两个不同用户的房间，使用相同的 external_room_id
            room_data1 = LiveRoomCreate(
                title="用户1的房间",
                description="测试",
                is_private=False,
                record_by_default=True
            )
            room1 = await crud_room.create(
                db=db,
                obj_in=room_data1,
                user_id=user['public_id']
            )
            room1.external_room_id = "shared_ext_id"
            await db.commit()
            await db.refresh(room1)
            
            # 创建另一个用户（使用不同的 public_id）
            other_user_id = uuid.uuid4()
            room_data2 = LiveRoomCreate(
                title="用户2的房间",
                description="测试",
                is_private=False,
                record_by_default=True
            )
            room2 = await crud_room.create(
                db=db,
                obj_in=room_data2,
                user_id=other_user_id
            )
            room2.external_room_id = "shared_ext_id"
            await db.commit()
            await db.refresh(room2)
            
            # Act: 分别查找
            found_room1 = await crud_room.get_by_external_id(
                db=db,
                user_id=user['public_id'],
                external_room_id="shared_ext_id"
            )
            found_room2 = await crud_room.get_by_external_id(
                db=db,
                user_id=other_user_id,
                external_room_id="shared_ext_id"
            )
            
            # Assert
            assert found_room1 is not None
            assert found_room1.id == room1.id
            assert found_room2 is not None
            assert found_room2.id == room2.id
            assert found_room1.id != found_room2.id


@pytest.mark.asyncio
async def test_external_room_id_partial_unique_index(db_session, test_user):
    """
    测试 external_room_id 的部分唯一索引约束
    同一用户下不能有重复的 external_room_id（非空值）
    """
    async for db in db_session:
        async for user in test_user:
            # Arrange: 创建一个带 external_room_id 的房间
            room_data1 = LiveRoomCreate(
                title="第一个房间",
                description="测试",
                is_private=False,
                record_by_default=True
            )
            room1 = await crud_room.create(
                db=db,
                obj_in=room_data1,
                user_id=user['public_id']
            )
            room1.external_room_id = "unique_ext_id"
            await db.commit()
            await db.refresh(room1)
            
            # Act & Assert: 尝试创建第二个相同 external_room_id 的房间
            room_data2 = LiveRoomCreate(
                title="第二个房间",
                description="测试",
                is_private=False,
                record_by_default=True
            )
            room2 = await crud_room.create(
                db=db,
                obj_in=room_data2,
                user_id=user['public_id']
            )
            room2.external_room_id = "unique_ext_id"
            
            # 应该触发唯一约束错误
            with pytest.raises((IntegrityError, DatabaseIntegrityException)):
                await db.commit()


# ==================== Session CRUD: get_by_room_and_playback_hash ====================

@pytest.mark.asyncio
async def test_get_by_room_and_playback_hash_found(db_session, test_user):
    """
    测试根据 (room_id, playback_url_hash) 查找会话 - 找到的情况
    """
    async for db in db_session:
        async for user in test_user:
            # Arrange: 创建房间和会话
            room_data = LiveRoomCreate(
                title="测试房间",
                description="用于测试的房间",
                is_private=False,
                record_by_default=True
            )
            room = await crud_room.create(
                db=db,
                obj_in=room_data,
                user_id=user['public_id']
            )
            
            playback_url = "https://example.com/playback/video123"
            playback_hash = calc_playback_url_hash(playback_url)
            
            session_data = LiveSessionCreate(
                room_id=room.id,
                status=LiveSessionStatus.FINISHED,
                start_time=datetime.now(timezone.utc),
                playback_url=playback_url
            )
            created_session = await crud_session.create_with_stats(
                db=db,
                obj_in=session_data,
                user_id=user['public_id']
            )
            
            # 设置 playback_url_hash
            created_session.playback_url_hash = playback_hash
            await db.commit()
            await db.refresh(created_session)
            
            # Act: 根据 playback_url_hash 查找
            found_session = await crud_session.get_by_room_and_playback_hash(
                db=db,
                room_id=room.id,
                playback_url_hash=playback_hash
            )
            
            # Assert
            assert found_session is not None
            assert found_session.id == created_session.id
            assert found_session.room_id == room.id
            assert found_session.playback_url_hash == playback_hash


@pytest.mark.asyncio
async def test_get_by_room_and_playback_hash_not_found(db_session, test_user):
    """
    测试根据 (room_id, playback_url_hash) 查找会话 - 未找到的情况
    """
    async for db in db_session:
        async for user in test_user:
            # Arrange: 创建房间
            room_data = LiveRoomCreate(
                title="测试房间",
                description="用于测试的房间",
                is_private=False,
                record_by_default=True
            )
            room = await crud_room.create(
                db=db,
                obj_in=room_data,
                user_id=user['public_id']
            )
            
            # Act: 查找不存在的 playback_url_hash
            non_existent_hash = "non_existent_hash_value_12345"
            found_session = await crud_session.get_by_room_and_playback_hash(
                db=db,
                room_id=room.id,
                playback_url_hash=non_existent_hash
            )
            
            # Assert
            assert found_session is None


@pytest.mark.asyncio
async def test_get_by_room_and_playback_hash_different_rooms(db_session, test_user):
    """
    测试不同房间可以有相同的 playback_url_hash
    """
    async for db in db_session:
        async for user in test_user:
            # Arrange: 创建两个房间
            room_data1 = LiveRoomCreate(
                title="房间1",
                description="测试",
                is_private=False,
                record_by_default=True
            )
            room1 = await crud_room.create(
                db=db,
                obj_in=room_data1,
                user_id=user['public_id']
            )
            
            room_data2 = LiveRoomCreate(
                title="房间2",
                description="测试",
                is_private=False,
                record_by_default=True
            )
            room2 = await crud_room.create(
                db=db,
                obj_in=room_data2,
                user_id=user['public_id']
            )
            
            # 两个房间使用相同的 playback_url
            playback_url = "https://example.com/shared_video"
            playback_hash = calc_playback_url_hash(playback_url)
            
            # 创建两个会话
            session_data1 = LiveSessionCreate(
                room_id=room1.id,
                status=LiveSessionStatus.FINISHED,
                start_time=datetime.now(timezone.utc),
                playback_url=playback_url
            )
            session1 = await crud_session.create_with_stats(
                db=db,
                obj_in=session_data1,
                user_id=user['public_id']
            )
            session1.playback_url_hash = playback_hash
            await db.commit()
            await db.refresh(session1)
            
            session_data2 = LiveSessionCreate(
                room_id=room2.id,
                status=LiveSessionStatus.FINISHED,
                start_time=datetime.now(timezone.utc),
                playback_url=playback_url
            )
            session2 = await crud_session.create_with_stats(
                db=db,
                obj_in=session_data2,
                user_id=user['public_id']
            )
            session2.playback_url_hash = playback_hash
            await db.commit()
            await db.refresh(session2)
            
            # Act: 分别查找
            found_session1 = await crud_session.get_by_room_and_playback_hash(
                db=db,
                room_id=room1.id,
                playback_url_hash=playback_hash
            )
            found_session2 = await crud_session.get_by_room_and_playback_hash(
                db=db,
                room_id=room2.id,
                playback_url_hash=playback_hash
            )
            
            # Assert
            assert found_session1 is not None
            assert found_session1.id == session1.id
            assert found_session2 is not None
            assert found_session2.id == session2.id
            assert found_session1.id != found_session2.id


@pytest.mark.asyncio
async def test_playback_url_hash_partial_unique_index(db_session, test_user):
    """
    测试 playback_url_hash 的部分唯一索引约束
    同一房间下不能有重复的 playback_url_hash（非空值）
    """
    async for db in db_session:
        async for user in test_user:
            # Arrange: 创建房间和第一个会话
            room_data = LiveRoomCreate(
                title="测试房间",
                description="测试",
                is_private=False,
                record_by_default=True
            )
            room = await crud_room.create(
                db=db,
                obj_in=room_data,
                user_id=user['public_id']
            )
            
            playback_url = "https://example.com/video123"
            playback_hash = calc_playback_url_hash(playback_url)
            
            session_data1 = LiveSessionCreate(
                room_id=room.id,
                status=LiveSessionStatus.FINISHED,
                start_time=datetime.now(timezone.utc),
                playback_url=playback_url
            )
            session1 = await crud_session.create_with_stats(
                db=db,
                obj_in=session_data1,
                user_id=user['public_id']
            )
            session1.playback_url_hash = playback_hash
            await db.commit()
            await db.refresh(session1)
            
            # Act & Assert: 尝试创建第二个相同 playback_url_hash 的会话
            session_data2 = LiveSessionCreate(
                room_id=room.id,
                status=LiveSessionStatus.FINISHED,
                start_time=datetime.now(timezone.utc),
                playback_url=playback_url
            )
            session2 = await crud_session.create_with_stats(
                db=db,
                obj_in=session_data2,
                user_id=user['public_id']
            )
            session2.playback_url_hash = playback_hash
            
            # 应该触发唯一约束错误
            with pytest.raises((IntegrityError, DatabaseIntegrityException)):
                await db.commit()

