"""
LiveCore Service - Session CRUD Unit Tests

This module contains unit tests for the session CRUD operations,
testing each function in isolation to ensure data layer correctness.
"""

import pytest
import uuid
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import room as crud_room
from app.schemas.live_core import LiveRoomCreate, LiveRoomUpdate, LiveSessionCreate
from app.models.live_core import LiveRoom, LiveSession, LiveSessionStatus

from app.crud import session as crud_session



# Helper function to create a test room
async def create_test_room_old(db: AsyncSession) -> LiveRoom:
    """创建测试用的LiveRoom"""
    room = LiveRoom(
        title="测试房间",
        description="用于测试的房间",
        stream_key=f"test_key_{uuid.uuid4().hex[:8]}",
        is_private=False,
        record_by_default=True
    )
    db.add(room)
    await db.commit()
    await db.refresh(room)
    return room

async def create_test_room(db_session, test_user):
    """
    测试创建房间功能
    - 准备: 创建LiveRoomCreate对象
    - 执行: 调用crud.room.create()
    - 断言: 验证返回值和数据库状态
    """
    async for db in db_session:
            # 准备测试数据
            room_data = LiveRoomCreate(
                title="测试直播房间",
                description="这是一个测试房间",
                cover_url="https://example.com/cover.jpg",
                is_private=False,
                record_by_default=True,
                category_id=uuid.uuid4(),
                parent_room_id=None,
            )

            # 执行创建操作
            created_room = await crud_room.create(db=db, obj_in=room_data, user_id = test_user.public_id)

            return created_room


@pytest.mark.asyncio
async def test_create_with_stats(db_session, test_user):
    """
    测试create_with_stats函数
    - 功能：创建LiveSession并同时创建关联的SessionStatistics
    - 验证：Session创建成功，Statistics记录存在且默认值正确
    """
    async for db in db_session:
        async for user in test_user:
            # Arrange: 创建测试房间
            room = await create_test_room(db, test_user)

            # 准备会话创建数据
            start_time = datetime.now(timezone.utc)
            session_data = LiveSessionCreate(
                room_id=room.id,
                status=LiveSessionStatus.SCHEDULED,
                start_time=start_time,
                end_time=None,
                video_id=None
            )

            # Act: 调用create_with_stats
            created_session = await crud_session.create_with_stats(db=db, obj_in=session_data, user_id = test_user['public_id'])

            # Assert: 验证Session创建
            assert created_session is not None
            assert created_session.room_id == room.id
            assert created_session.status == LiveSessionStatus.SCHEDULED
            assert created_session.start_time == start_time
            assert created_session.end_time is None
            assert created_session.video_id is None

            # Assert: 验证Statistics创建
            # 查询SessionStatistics表
            stats_result = await db.execute(
                select(SessionStatistics).where(SessionStatistics.session_id == created_session.id)
            )
            stats_record = stats_result.scalar_one_or_none()

            assert stats_record is not None
            assert stats_record.session_id == created_session.id
            assert stats_record.peak_viewer_count == 0
            assert stats_record.total_viewer_count == 0
            assert stats_record.total_like_count == 0
            assert stats_record.total_share_count == 0


@pytest.mark.asyncio
async def test_get_with_stats(db_session, test_user):
    """
    测试get_with_stats函数
    - 功能：获取Session并预加载Statistics关系
    - 验证：返回的对象包含已加载的statistics关系
    """
    async for db in db_session:
        async for user in test_user:
            # Arrange: 创建测试房间和会话
            room = await create_test_room(db, test_user)

            session_data = LiveSessionCreate(
                room_id=room.id,
                status=LiveSessionStatus.SCHEDULED,
                start_time=datetime.now(timezone.utc),
                end_time=None,
                video_id=None
            )

            created_session = await crud_session.create_with_stats(db=db, obj_in=session_data, user_id = test_user['public_id'])

            # Act: 调用get_with_stats
            retrieved_session = await crud_session.get_with_stats(db=db, session_id=created_session.id, user_id = test_user['public_id'])

            # Assert: 验证返回的对象和statistics关系
            assert retrieved_session is not None
            assert retrieved_session.id == created_session.id
            assert retrieved_session.room_id == room.id
            assert retrieved_session.statistics is not None
            assert retrieved_session.statistics.session_id == created_session.id


@pytest.mark.asyncio
async def test_get_with_stats_not_found(db_session, test_user):
    """
    测试get_with_stats函数处理不存在的session
    - 功能：查询不存在的session_id
    - 验证：返回None
    """
    async for db in db_session:
        async for user in test_user:
            # Arrange: 使用随机UUID
            random_id = uuid.uuid4()

            # Act: 调用get_with_stats
            result = await crud_session.get_with_stats(db=db, session_id=random_id)

            # Assert: 验证返回None
            assert result is None


@pytest.mark.asyncio
async def test_get_multi_by_room_and_total(db_session, test_user):
    """
    测试get_multi_by_room_and_total函数
    - 功能：分页获取指定房间的会话列表和总数
    - 验证：返回正确的分页数据和总数
    """
    async for db in db_session:
        async for user in test_user:
            # Arrange: 创建测试房间
            room = await create_test_room(db,test_user)

            # 创建3个会话
            sessions_data = []
            for i in range(3):
                session_data = LiveSessionCreate(
                    room_id=room.id,
                    status=LiveSessionStatus.SCHEDULED,
                    start_time=datetime.now(timezone.utc),
                    end_time=None,
                    video_id=None
                )
                session = await crud_session.create_with_stats(db=db, obj_in=session_data, user_id = test_user['public_id'])
                sessions_data.append(session)

            # Act: 调用get_multi_by_room_and_total，限制返回2条
            sessions, total = await crud_session.get_multi_by_room_and_total(
                db=db,
                room_id=room.id,
                skip=0,
                limit=2
            )

            # Assert: 验证分页结果
            assert len(sessions) == 2  # 返回2条记录
            assert total == 3  # 总共3条记录

            # 验证所有返回的会话都属于同一个房间
            for session in sessions:
                assert session.room_id == room.id


@pytest.mark.asyncio
async def test_update_session(db_session,test_user):
    """
    测试update函数
    - 功能：更新会话信息
    - 验证：数据库中的记录被正确更新
    """
    async for db in db_session:
        async for user in test_user:
            # Arrange: 创建测试房间和会话
            room = await create_test_room(db,test_user)

            session_data = LiveSessionCreate(
                room_id=room.id,
                status=LiveSessionStatus.SCHEDULED,
                start_time=datetime.now(timezone.utc),
                end_time=None,
                video_id=None
            )

            created_session = await crud_session.create_with_stats(db=db, obj_in=session_data, user_id = test_user['public_id'])

            # 准备更新数据
            update_data = LiveSessionUpdate(
                status=LiveSessionStatus.FINISHED,
                end_time=datetime.now(timezone.utc)
            )

            # Act: 调用update
            updated_session = await crud_session.update(
                db=db,
                db_obj=created_session,
                obj_in=update_data
            )

            # Assert: 验证更新结果
            assert updated_session.status == LiveSessionStatus.FINISHED
            assert updated_session.end_time is not None

            # 从数据库重新获取，验证更改已持久化
            db_session_check = await crud_session.get(db=db, session_id=created_session.id, user_id = test_user['public_id'])
            assert db_session_check.status == LiveSessionStatus.FINISHED
            assert db_session_check.end_time is not None


@pytest.mark.asyncio
async def test_remove_session(db_session,test_user):
    """
    测试remove函数
    - 功能：删除会话及其关联的统计信息
    - 验证：会话和统计信息都被删除（级联删除）
    """
    async for db in db_session:
        async for user in test_user:
            # Arrange: 创建测试房间和会话
            room = await create_test_room(db,test_user)

            session_data = LiveSessionCreate(
                room_id=room.id,
                status=LiveSessionStatus.SCHEDULED,
                start_time=datetime.now(timezone.utc),
                end_time=None,
                video_id=None
            )

            created_session = await crud_session.create_with_stats(db=db, obj_in=session_data, user_id = test_user['public_id'])
            session_id = created_session.id

            # 获取统计信息ID
            stats_result = await db.execute(
                select(SessionStatistics).where(SessionStatistics.session_id == session_id)
            )
            stats_record = stats_result.scalar_one()
            stats_id = stats_record.id

            # Act: 调用remove
            deleted_session = await crud_session.remove(db=db, db_obj=created_session, user_id = test_user['public_id'])

            # Assert: 验证删除结果
            assert deleted_session.id == session_id

            # 验证会话被删除
            session_check = await crud_session.get(db=db, session_id=session_id, user_id = test_user['public_id'])
            assert session_check is None

            # 验证统计信息也被删除（级联删除）
            stats_check_result = await db.execute(
                select(SessionStatistics).where(SessionStatistics.id == stats_id)
            )
            stats_check = stats_check_result.scalar_one_or_none()
            assert stats_check is None


@pytest.mark.asyncio
async def test_get_session_without_stats(db_session,test_user):
    """
    测试get函数（不预加载statistics）
    - 功能：获取单个会话但不预加载关联数据
    - 验证：返回正确的LiveSession对象
    """
    async for db in db_session:
        async for user in test_user:
            # Arrange: 创建测试房间和会话
            room = await create_test_room(db,test_user)

            session_data = LiveSessionCreate(
                room_id=room.id,
                status=LiveSessionStatus.SCHEDULED,
                start_time=datetime.now(timezone.utc),
                end_time=None,
                video_id=None
            )

            created_session = await crud_session.create_with_stats(db=db, obj_in=session_data, user_id = test_user['public_id'])

            # Act: 调用get（不预加载statistics）
            retrieved_session = await crud_session.get(db=db, session_id=created_session.id, user_id = test_user['public_id'])

            # Assert: 验证返回的对象
            assert retrieved_session is not None
            assert isinstance(retrieved_session, LiveSession)
            assert retrieved_session.id == created_session.id
            assert retrieved_session.room_id == room.id
            assert retrieved_session.status == LiveSessionStatus.SCHEDULED