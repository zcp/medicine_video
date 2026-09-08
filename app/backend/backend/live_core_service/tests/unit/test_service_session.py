"""
LiveCore Service - SessionService Unit Tests

This module contains unit tests for the SessionService class,
testing all business logic in complete isolation using mocks.
All external dependencies (CRUD operations) are mocked.
"""

import pytest
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from typing import List

from app.services.session_service import SessionService
from app.models.live_core import LiveSession, LiveRoom, LiveSessionStatus, SessionStatistics
from app.schemas.live_core import ScheduledSessionCreate, LiveSessionCreate, LiveSessionUpdate
from app.exceptions import (
    SessionNotFoundException,
    SessionActionForbiddenException,
    RoomNotFoundException
)


# ==================== Test Data Fixtures ====================

@pytest.fixture
def mock_test_user():
    """为单元测试提供模拟用户数据"""
    return {
        "public_id": "550e8400-e29b-41d4-a716-446655440000",
        "username": "test_user",
        "email": "test@example.com"
    }


# ==================== Test Helper Functions ====================

def create_mock_room(
    room_id: uuid.UUID = None,
    title: str = "测试房间",
    description: str = "测试描述",
    stream_key: str = "test_key",
    is_private: bool = False,
    record_by_default: bool = True,
    user_id: uuid.UUID = None
) -> LiveRoom:
    """创建模拟的LiveRoom对象"""
    if room_id is None:
        room_id = uuid.uuid4()

    mock_room = LiveRoom()
    mock_room.id = room_id
    mock_room.title = title
    mock_room.description = description
    mock_room.stream_key = stream_key
    mock_room.is_private = is_private
    mock_room.record_by_default = record_by_default
    mock_room.user_id = user_id
    mock_room.created_at = datetime.utcnow()
    mock_room.updated_at = datetime.utcnow()

    return mock_room


def create_mock_session(
    session_id: uuid.UUID = None,
    room_id: uuid.UUID = None,
    status: LiveSessionStatus = LiveSessionStatus.SCHEDULED,
    start_time: datetime = None,
    end_time: datetime = None,
    video_id: str = None,
    user_id: uuid.UUID = None
) -> LiveSession:
    """创建模拟的LiveSession对象"""
    if session_id is None:
        session_id = uuid.uuid4()
    if room_id is None:
        room_id = uuid.uuid4()
    if start_time is None:
        start_time = datetime.now(timezone.utc)

    mock_session = LiveSession()
    mock_session.id = session_id
    mock_session.room_id = room_id
    mock_session.status = status
    mock_session.start_time = start_time
    mock_session.end_time = end_time
    mock_session.video_id = video_id
    mock_session.user_id = user_id
    mock_session.created_at = datetime.utcnow()
    mock_session.updated_at = datetime.utcnow()

    return mock_session


# ==================== TestSessionServiceCreateScheduledSession ====================

class TestSessionServiceCreateScheduledSession:
    """测试创建计划场次的业务逻辑"""

    @pytest.mark.asyncio
    async def test_create_scheduled_session_success(self, mocker, mock_test_user):
        """
        测试成功创建计划场次
        - 验证房间存在
        - 正确构造LiveSessionCreate对象
        - 调用CRUD层创建会话和统计信息
        """
        # Arrange - 创建测试数据
        room_id = uuid.uuid4()
        session_id = uuid.uuid4()
        start_time = datetime.now(timezone.utc)

        # 创建模拟的房间对象
        mock_room = create_mock_room(
            room_id=room_id,
            title="测试房间",
            description="测试描述",
            stream_key="test_key",
            is_private=False,
            record_by_default=True,
            user_id=mock_test_user['public_id']
        )

        # 创建模拟的会话对象
        mock_session = create_mock_session(
            session_id=session_id,
            room_id=room_id,
            status=LiveSessionStatus.SCHEDULED,
            start_time=start_time,
            end_time=None,
            video_id=None,
            user_id=mock_test_user['public_id']
        )

        # 创建输入Schema
        session_in = ScheduledSessionCreate(start_time=start_time, playback_url="https://example.com/live.m3u8")

        # Mock CRUD操作
        mock_room_get = mocker.patch('app.crud.room.get', new_callable=AsyncMock)
        mock_room_get.return_value = mock_room

        mock_session_create = mocker.patch('app.crud.session.create_with_stats', new_callable=AsyncMock)
        mock_session_create.return_value = mock_session

        # Act - 执行测试
        service = SessionService(db=MagicMock())  # ← 修改：提供mock db，因为create_scheduled_session需要self.db
        role = "REGULAR"  # ← 新增：权限参数（字符串格式）
        result = await service.create_scheduled_session(
            room_id=room_id,
            session_in=session_in,
            user_id=mock_test_user['public_id'],
            role=role  # ← 新增：传递权限参数
        )

        # Assert - 验证结果
        # ← 注意：create_scheduled_session内部调用crud_room.get时只传递room_id，不传递user_id
        mock_room_get.assert_called_once_with(db=service.db, room_id=room_id)

        # 验证调用了会话创建，并检查传入的参数
        mock_session_create.assert_called_once()
        call_args = mock_session_create.call_args
        session_create_obj = call_args[1]['obj_in']  # 获取obj_in参数

        assert isinstance(session_create_obj, LiveSessionCreate)
        assert session_create_obj.room_id == room_id
        assert session_create_obj.status == LiveSessionStatus.SCHEDULED
        assert session_create_obj.start_time == start_time
        assert session_create_obj.end_time is None
        assert session_create_obj.video_id is None

        # 验证返回结果
        assert result == mock_session

    @pytest.mark.asyncio
    async def test_create_scheduled_session_room_not_found(self, mocker, mock_test_user):
        """
        测试房间不存在时的异常处理
        - 房间查询返回None
        - 抛出RoomNotFoundException
        """
        # Arrange
        room_id = uuid.uuid4()
        start_time = datetime.now(timezone.utc)
        session_in = ScheduledSessionCreate(start_time=start_time, playback_url="https://example.com/live.m3u8")

        # Mock房间不存在
        mock_room_get = mocker.patch('app.crud.room.get', new_callable=AsyncMock)
        mock_room_get.return_value = None

        # Act & Assert
        service = SessionService(db=None)
        role = "REGULAR"  # ← 新增：权限参数（字符串格式）
        with pytest.raises(RoomNotFoundException):
            await service.create_scheduled_session(
                room_id=room_id,
                session_in=session_in,
                user_id=mock_test_user['public_id'],
                role=role  # ← 新增：传递权限参数
            )

        # 验证只调用了房间查询，没有调用会话创建
        # ← 注意：create_scheduled_session调用crud_room.get时只传递db和room_id，不传递user_id
        mock_room_get.assert_called_once_with(db=None, room_id=room_id)


# ==================== TestSessionServiceUpdateScheduledSessionInfo ====================

class TestSessionServiceUpdateScheduledSessionInfo:
    """测试更新计划场次信息的业务逻辑"""

    @pytest.mark.asyncio
    async def test_update_session_info_success(self, mocker, mock_test_user):
        """
        测试成功更新计划场次信息
        - 会话存在且状态为SCHEDULED
        - 正确调用CRUD层更新操作
        """
        # Arrange
        session_id = uuid.uuid4()
        new_start_time = datetime.now(timezone.utc)

        # 创建模拟的会话对象（状态为SCHEDULED）
        mock_session = create_mock_session(
            session_id=session_id,
            room_id=uuid.uuid4(),
            status=LiveSessionStatus.SCHEDULED,
            start_time=datetime.now(timezone.utc),
            end_time=None,
            video_id=None,
            user_id=mock_test_user['public_id']
        )

        # 创建更新后的会话对象
        updated_session = create_mock_session(
            session_id=session_id,
            room_id=mock_session.room_id,
            status=LiveSessionStatus.SCHEDULED,
            start_time=new_start_time,
            end_time=None,
            video_id=None,
            user_id=mock_test_user['public_id']
        )

        session_update = LiveSessionUpdate(start_time=new_start_time)

        # Mock CRUD操作
        mock_session_get = mocker.patch('app.crud.session.get', new_callable=AsyncMock)
        mock_session_get.return_value = mock_session
        
        # Mock crud_room.get（update_scheduled_session_info内部会调用）
        mock_room_get = mocker.patch('app.crud.room.get', new_callable=AsyncMock)
        mock_room = create_mock_room(room_id=mock_session.room_id, user_id=mock_test_user['public_id'])
        mock_room_get.return_value = mock_room

        mock_session_update = mocker.patch('app.crud.session.update', new_callable=AsyncMock)
        mock_session_update.return_value = updated_session

        # Act
        service = SessionService(db=MagicMock())  # ← 修改：提供mock db
        role = "REGULAR"  # ← 新增：权限参数（字符串格式）
        result = await service.update_scheduled_session_info(
            session_id=session_id,
            session_update=session_update,
            user_id=mock_test_user['public_id'],
            role=role  # ← 新增：传递权限参数
        )

        # Assert
        # ← 注意：update_scheduled_session_info内部调用crud_session.get时只传递session_id，不传递user_id
        mock_session_get.assert_called_once_with(db=service.db, session_id=session_id)
        # ← 注意：update_scheduled_session_info内部调用crud_room.get时只传递room_id，不传递user_id
        mock_room_get.assert_called_once_with(db=service.db, room_id=mock_session.room_id)
        # 注意：实际代码中使用关键字参数调用 crud_session.update(db=self.db, ...)
        # update_data 是 session_update.model_dump() 的结果，是一个 dict
        expected_update_data = session_update.model_dump(exclude_unset=True)
        mock_session_update.assert_called_once_with(
            db=service.db,
            db_obj=mock_session,
            obj_in=expected_update_data
        )
        assert result == updated_session

    @pytest.mark.asyncio
    async def test_update_session_info_not_found(self, mocker, mock_test_user):
        """
        测试更新不存在的会话
        - 会话查询返回None
        - 抛出SessionNotFoundException
        """
        # Arrange
        session_id = uuid.uuid4()
        session_update = LiveSessionUpdate(start_time=datetime.now(timezone.utc))

        # Mock会话不存在
        mock_session_get = mocker.patch('app.crud.session.get', new_callable=AsyncMock)
        mock_session_get.return_value = None

        # Act & Assert
        service = SessionService(db=MagicMock())  # ← 修改：提供mock db
        role = "REGULAR"  # ← 新增：权限参数（字符串格式）
        with pytest.raises(SessionNotFoundException):
            await service.update_scheduled_session_info(
                session_id=session_id,
                session_update=session_update,
                user_id=mock_test_user['public_id'],
                role=role  # ← 新增：传递权限参数
            )

        # ← 注意：update_scheduled_session_info内部调用crud_session.get时只传递session_id，不传递user_id
        mock_session_get.assert_called_once_with(db=service.db, session_id=session_id)

    @pytest.mark.asyncio
    async def test_update_session_info_forbidden_when_live(self, mocker, mock_test_user):
        """
        测试更新正在直播的场次
        - 会话状态为LIVE
        - 抛出SessionActionForbiddenException，错误消息正确
        """
        # Arrange
        session_id = uuid.uuid4()
        room_id = uuid.uuid4()

        # 创建正在直播的会话对象
        mock_session = create_mock_session(
            session_id=session_id,
            room_id=room_id,
            status=LiveSessionStatus.LIVE,  # 状态为LIVE
            start_time=datetime.now(timezone.utc),
            end_time=None,
            video_id=None,
            user_id=mock_test_user['public_id']
        )

        # 创建模拟的房间对象
        mock_room = create_mock_room(
            room_id=room_id,
            user_id=mock_test_user['public_id']
        )

        session_update = LiveSessionUpdate(start_time=datetime.now(timezone.utc))

        # Mock CRUD操作
        mock_session_get = mocker.patch('app.crud.session.get', new_callable=AsyncMock)
        mock_session_get.return_value = mock_session
        
        mock_room_get = mocker.patch('app.crud.room.get', new_callable=AsyncMock)
        mock_room_get.return_value = mock_room

        # Act & Assert
        service = SessionService(db=None)
        role = "REGULAR"  # ← 新增：权限参数（字符串格式）
        with pytest.raises(SessionActionForbiddenException) as exc_info:
            await service.update_scheduled_session_info(
                session_id=session_id,
                session_update=session_update,
                user_id=mock_test_user['public_id'],
                role=role  # ← 新增：传递权限参数
            )

        # 验证异常消息
        assert exc_info.value.message == "当前场次状态不允许编辑计划信息"
        # ← 注意：update_scheduled_session_info内部调用crud_session.get时只传递session_id，不传递user_id
        mock_session_get.assert_called_once_with(db=service.db, session_id=session_id)
        # ← 验证：update_scheduled_session_info会先获取room进行权限检查
        mock_room_get.assert_called_once_with(db=service.db, room_id=room_id)


# ==================== TestSessionServiceDeleteSession ====================

class TestSessionServiceDeleteSession:
    """测试删除场次的业务逻辑"""

    @pytest.mark.asyncio
    async def test_delete_session_success_when_finished(self, mocker, mock_test_user):
        """
        测试成功删除已结束的场次
        - 会话状态为FINISHED
        - 正确调用CRUD层删除操作
        """
        # Arrange
        session_id = uuid.uuid4()

        # 创建已结束的会话对象
        mock_session = create_mock_session(
            session_id=session_id,
            room_id=uuid.uuid4(),
            status=LiveSessionStatus.FINISHED,  # 状态为FINISHED
            start_time=datetime.now(timezone.utc),
            end_time=datetime.now(timezone.utc),
            video_id=None,
            user_id=mock_test_user['public_id']
        )

        # Mock CRUD操作
        mock_session_get = mocker.patch('app.crud.session.get', new_callable=AsyncMock)
        mock_session_get.return_value = mock_session
        
        # Mock crud_room.get（delete_session内部会调用）
        mock_room_get = mocker.patch('app.crud.room.get', new_callable=AsyncMock)
        mock_room = create_mock_room(room_id=mock_session.room_id, user_id=mock_test_user['public_id'])
        mock_room_get.return_value = mock_room

        mock_session_remove = mocker.patch('app.crud.session.remove', new_callable=AsyncMock)
        mock_session_remove.return_value = mock_session

        # Mock 数据关联治理（P0-1/P0-2）：删除场次时软下线焦点图 + 硬删订阅
        mock_disable_featured = mocker.patch(
            'app.crud.homepage_search.disable_featured_content_by_target',
            new_callable=AsyncMock,
        )

        # Act
        mock_db = MagicMock()  # ← 修改：提供mock db
        service = SessionService(db=mock_db)
        # 订阅硬删直接走 self.db.execute（P0-2），mock db 需可 await
        mocker.patch.object(mock_db, 'execute', new_callable=AsyncMock)
        role = "REGULAR"  # ← 新增：权限参数（字符串方式）
        result = await service.delete_session(
            session_id=session_id, 
            user_id=mock_test_user['public_id'],
            role=role  # ← 新增：显式传入权限参数
        )

        # Assert
        # ← 注意：delete_session内部调用crud_session.get时只传session_id，不传user_id
        mock_session_get.assert_called_once_with(db=service.db, session_id=session_id)
        mock_session_remove.assert_called_once_with(db=service.db, db_obj=mock_session)
        mock_disable_featured.assert_called_once_with(service.db, "session", session_id)
        assert result == mock_session

    @pytest.mark.asyncio
    async def test_delete_session_fails_when_live(self, mocker, mock_test_user):
        """
        测试删除正在直播的场次失败
        - 会话状态为LIVE
        - 抛出SessionActionForbiddenException，错误消息正确
        """
        # Arrange
        session_id = uuid.uuid4()

        # 创建正在直播的会话对象
        mock_session = create_mock_session(
            session_id=session_id,
            room_id=uuid.uuid4(),
            status=LiveSessionStatus.LIVE,  # 状态为LIVE
            start_time=datetime.now(timezone.utc),
            end_time=None,
            video_id=None,
            user_id=mock_test_user['public_id']
        )

        # Mock CRUD操作
        mock_session_get = mocker.patch('app.crud.session.get', new_callable=AsyncMock)
        mock_session_get.return_value = mock_session
        
        # Mock crud_room.get（delete_session内部会调用）
        mock_room_get = mocker.patch('app.crud.room.get', new_callable=AsyncMock)
        mock_room = create_mock_room(room_id=mock_session.room_id, user_id=mock_test_user['public_id'])
        mock_room_get.return_value = mock_room

        # Act & Assert
        service = SessionService(db=MagicMock())  # ← 修改：提供mock db
        role = "REGULAR"  # ← 新增：权限参数（字符串格式）
        with pytest.raises(SessionActionForbiddenException) as exc_info:
            await service.delete_session(
                session_id=session_id, 
                user_id=mock_test_user['public_id'],
                role=role  # ← 新增：传递权限参数
            )

        # 验证异常消息
        assert exc_info.value.message == "无法删除正在直播的场次"
        # ← 注意：delete_session内部调用crud_session.get时只传递session_id，不传递user_id
        mock_session_get.assert_called_once_with(db=service.db, session_id=session_id)

    @pytest.mark.asyncio
    async def test_delete_session_not_found(self, mocker, mock_test_user):
        """
        测试删除不存在的会话
        - 会话查询返回None
        - 抛出SessionNotFoundException
        """
        # Arrange
        session_id = uuid.uuid4()

        # Mock会话不存在
        mock_session_get = mocker.patch('app.crud.session.get', new_callable=AsyncMock)
        mock_session_get.return_value = None

        # Act & Assert
        service = SessionService(db=MagicMock())  # ← 修改：提供mock db
        role = "REGULAR"  # ← 新增：权限参数（字符串格式）
        with pytest.raises(SessionNotFoundException):
            await service.delete_session(
                session_id=session_id, 
                user_id=mock_test_user['public_id'],
                role=role  # ← 新增：传递权限参数
            )

        # ← 注意：delete_session内部调用crud_session.get时只传递session_id，不传递user_id
        mock_session_get.assert_called_once_with(db=service.db, session_id=session_id)


# ==================== TestSessionServiceGetSessionsByRoom ====================

class TestSessionServiceGetSessionsByRoom:
    """测试获取房间场次列表的业务逻辑"""

    @pytest.mark.asyncio
    async def test_get_sessions_by_room_success(self, mocker, mock_test_user):
        """
        测试成功获取房间场次列表
        - 验证房间存在
        - 正确计算skip值
        - 返回正确的分页数据
        """
        # Arrange
        room_id = uuid.uuid4()
        page = 2
        size = 5
        expected_skip = (page - 1) * size  # = 5

        # 创建模拟数据
        mock_room = create_mock_room(
            room_id=room_id,
            title="测试房间",
            description="测试描述",
            stream_key="test_key",
            is_private=False,
            record_by_default=True,
            user_id=mock_test_user['public_id']
        )

        mock_sessions = [
            create_mock_session(
                session_id=uuid.uuid4(),  # 修复：使用 session_id 而不是 id
                room_id=room_id,
                status=LiveSessionStatus.SCHEDULED,
                start_time=datetime.now(timezone.utc),
                end_time=None,
                video_id=None,
                user_id=mock_test_user['public_id']
            )
        ]
        mock_total = 1

        # Mock CRUD操作
        mock_room_get = mocker.patch('app.crud.room.get', new_callable=AsyncMock)
        mock_room_get.return_value = mock_room

        mock_get_multi = mocker.patch('app.crud.session.get_multi_by_room_and_total', new_callable=AsyncMock)
        mock_get_multi.return_value = (mock_sessions, mock_total)

        # Act
        service = SessionService(db=MagicMock())  # ← 修改：提供mock db
        role = "REGULAR"  # ← 新增：权限参数（字符串格式）
        sessions, total = await service.get_sessions_by_room(
            room_id=room_id,
            page=page,
            size=size,
            user_id=mock_test_user['public_id'],
            role=role  # ← 新增：传递权限参数
        )

        # Assert
        # ← 注意：get_sessions_by_room内部调用crud_room.get时只传递room_id，不传递user_id
        mock_room_get.assert_called_once_with(db=service.db, room_id=room_id)
        mock_get_multi.assert_called_once_with(
            db=service.db,
            room_id=room_id,
            skip=expected_skip,
            limit=size,
            user_id=mock_test_user['public_id']
        )
        assert sessions == mock_sessions
        assert total == mock_total

    @pytest.mark.asyncio
    async def test_get_sessions_by_room_room_not_found(self, mocker, mock_test_user):
        """
        测试获取不存在房间的场次列表
        - 房间查询返回None
        - 抛出RoomNotFoundException
        """
        # Arrange
        room_id = uuid.uuid4()
        page = 1
        size = 10

        # Mock房间不存在
        mock_room_get = mocker.patch('app.crud.room.get', new_callable=AsyncMock)
        mock_room_get.return_value = None

        # Act & Assert
        service = SessionService(db=None)
        role = "REGULAR"  # ← 新增：权限参数（字符串格式）
        with pytest.raises(RoomNotFoundException):
            await service.get_sessions_by_room(
                room_id=room_id,
                page=page,
                size=size,
                user_id=mock_test_user['public_id'],
                role=role  # ← 新增：传递权限参数
            )

        # ← 注意：get_sessions_by_room内部调用crud_room.get时只传递room_id，不传递user_id
        mock_room_get.assert_called_once_with(db=service.db, room_id=room_id)


# ==================== TestSessionServiceGetSessionDetails ====================

class TestSessionServiceGetSessionDetails:
    """测试获取会话详情的业务逻辑"""

    @pytest.mark.asyncio
    async def test_get_session_details_success(self, mocker, mock_test_user):
        """
        测试成功获取会话详情（包含统计信息）
        - 会话存在
        - 返回包含统计信息的会话对象
        """
        # Arrange
        session_id = uuid.uuid4()

        # 创建包含统计信息的会话对象
        mock_statistics = SessionStatistics(
            id=uuid.uuid4(),
            session_id=session_id,
            peak_viewer_count=100,
            total_viewer_count=500,
            total_like_count=50,
            total_share_count=10
        )

        mock_session = create_mock_session(
            session_id=session_id,
            room_id=uuid.uuid4(),
            status=LiveSessionStatus.FINISHED,
            start_time=datetime.now(timezone.utc),
            end_time=datetime.now(timezone.utc),
            video_id=None,
            #user_id=mock_test_user['public_id']  # 添加 user_id
        )
        mock_session.statistics = mock_statistics

        # Mock CRUD操作 - get_session_details内部调用get_with_stats和crud_room.get
        mock_get_with_stats = mocker.patch('app.crud.session.get_with_stats', new_callable=AsyncMock)
        mock_get_with_stats.return_value = mock_session
        
        # Mock crud_room.get（get_session_details内部会调用）
        mock_room_get = mocker.patch('app.crud.room.get', new_callable=AsyncMock)
        mock_room = create_mock_room(room_id=mock_session.room_id, user_id=mock_test_user['public_id'])
        mock_room_get.return_value = mock_room

        # Act
        service = SessionService(db=MagicMock())  # ← 修改：提供mock db
        role = "REGULAR"  # ← 新增：权限参数（字符串格式）
        result = await service.get_session_details(
            session_id=session_id, 
            user_id=mock_test_user['public_id'],
            role=role  # ← 新增：传递权限参数
        )

        # Assert
        # ← 注意：get_session_details内部调用crud_session.get_with_stats时只传递session_id
        mock_get_with_stats.assert_called_once_with(db=service.db, session_id=session_id)
        # ← 注意：get_session_details内部调用crud_room.get时只传递room_id，不传递user_id
        mock_room_get.assert_called_once_with(db=service.db, room_id=mock_session.room_id)
        assert result == mock_session
        assert result.statistics == mock_statistics


    @pytest.mark.asyncio
    async def test_get_session_details_not_found(self, mocker, mock_test_user):
        """
        测试获取不存在的会话详情
        - 会话查询返回None
        - 抛出SessionNotFoundException
        """
        # Arrange
        session_id = uuid.uuid4()

        # Mock会话不存在 - get_session_details内部调用get_with_stats
        mock_get_with_stats = mocker.patch('app.crud.session.get_with_stats', new_callable=AsyncMock)
        mock_get_with_stats.return_value = None

        # Act & Assert
        service = SessionService(db=MagicMock())  # ← 修改：提供mock db
        role = "REGULAR"  # ← 新增：权限参数（字符串格式）
        with pytest.raises(SessionNotFoundException):
            await service.get_session_details(
                session_id=session_id, 
                user_id=mock_test_user['public_id'],
                role=role  # ← 新增：传递权限参数
            )

        # ← 注意：get_session_details内部调用crud_session.get_with_stats时只传递session_id
        mock_get_with_stats.assert_called_once_with(db=service.db, session_id=session_id)


# ==================== TestSessionServicePlaybackUrl ====================

class TestSessionServicePlaybackUrl:
    """测试回放地址自动生成与管理逻辑"""

    @pytest.mark.asyncio
    async def test_post_stream_processing_sets_playback_url_when_ready_and_empty(self, mocker, mock_test_user):
        """
        测试后台任务在满足条件时自动设置回放地址
        - 状态=READY, video_id存在, playback_url为空
        - 期望：自动生成并写入回放地址
        """
        # Arrange
        session_id = uuid.uuid4()
        video_id = uuid.uuid4()
        
        mock_session = create_mock_session(
            session_id=session_id,
            room_id=uuid.uuid4(),
            status=LiveSessionStatus.READY,
            video_id=video_id,
            user_id=mock_test_user['public_id']
        )
        mock_session.playback_url = None

        # Mock CRUD
        mock_get = mocker.patch('app.crud.session.get', new_callable=AsyncMock)
        mock_get.return_value = mock_session
        
        # Mock DB commit/refresh
        mock_db = AsyncMock()
        
        # Act
        service = SessionService(db=mock_db)
        # Mock os.getenv to return a predictable base url
        mocker.patch('os.getenv', return_value="http://test-cdn.com")
        
        await service.auto_generate_playback_url(session_id=session_id)
        
        # Assert
        assert mock_session.playback_url == f"http://test-cdn.com/media/videos/{video_id}/playlist.m3u8"
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once_with(mock_session)

    @pytest.mark.asyncio
    async def test_post_stream_processing_not_override_manual_playback_url(self, mocker, mock_test_user):
        """
        测试后台任务不覆盖已有的手动回放地址
        - 状态=READY, video_id存在, playback_url已有值
        - 期望：playback_url保持原值
        """
        # Arrange
        session_id = uuid.uuid4()
        manual_url = "https://manual.com/video.mp4"
        
        mock_session = create_mock_session(
            session_id=session_id,
            room_id=uuid.uuid4(),
            status=LiveSessionStatus.READY,
            video_id=uuid.uuid4(),
            user_id=mock_test_user['public_id']
        )
        mock_session.playback_url = manual_url

        # Mock CRUD
        mock_get = mocker.patch('app.crud.session.get', new_callable=AsyncMock)
        mock_get.return_value = mock_session
        
        mock_db = AsyncMock()
        
        # Act
        service = SessionService(db=mock_db)
        await service.auto_generate_playback_url(session_id=session_id)
        
        # Assert
        assert mock_session.playback_url == manual_url
        mock_db.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_post_stream_processing_skip_when_not_ready_or_no_video_id(self, mocker, mock_test_user):
        """
        测试不满足条件时跳过自动生成
        - 场景1：状态不是READY
        - 场景2：没有video_id
        """
        # Case 1: Not READY
        session1 = create_mock_session(status=LiveSessionStatus.FINISHED, video_id=uuid.uuid4())
        session1.playback_url = None
        
        # Case 2: No Video ID
        session2 = create_mock_session(status=LiveSessionStatus.READY, video_id=None)
        session2.playback_url = None

        mock_db = AsyncMock()
        service = SessionService(db=mock_db)

        # Mock CRUD to return session1 then session2
        mock_get = mocker.patch('app.crud.session.get', new_callable=AsyncMock)
        mock_get.side_effect = [session1, session2]

        # Act 1
        await service.auto_generate_playback_url(session_id=session1.id)
        assert session1.playback_url is None
        mock_db.commit.assert_not_called()

        # Act 2
        await service.auto_generate_playback_url(session_id=session2.id)
        assert session2.playback_url is None
        mock_db.commit.assert_not_called()


# ==================== TestSessionServicePlaybackUrlHashMaintenance (V6) ====================

class TestSessionServicePlaybackUrlHashMaintenance:
    """测试 playback_url_hash 的全局维护（V6 新增）"""

    @pytest.mark.asyncio
    async def test_update_scheduled_session_info_updates_hash(self, mocker, mock_test_user):
        """
        测试通过 update_scheduled_session_info 更新 playback_url 时同步更新 hash
        - 场景: 更新包含 playback_url 的请求
        - 断言: 新的 playback_url 经 calc_playback_url_hash 计算后写入 playback_url_hash
        """
        # Arrange
        session_id = uuid.uuid4()
        new_playback_url = "https://example.com/new_video.mp4"
        
        mock_session = create_mock_session(
            session_id=session_id,
            room_id=uuid.uuid4(),
            status=LiveSessionStatus.READY,
            user_id=mock_test_user['public_id']
        )
        mock_session.playback_url = None
        mock_session.playback_url_hash = None
        
        # Mock CRUD
        mock_get = mocker.patch('app.crud.session.get', new_callable=AsyncMock)
        mock_get.return_value = mock_session
        
        # Mock crud_room.get（update_scheduled_session_info内部会调用）
        mock_room_get = mocker.patch('app.crud.room.get', new_callable=AsyncMock)
        mock_room = create_mock_room(room_id=mock_session.room_id, user_id=mock_test_user['public_id'])
        mock_room_get.return_value = mock_room
        
        mock_update = mocker.patch('app.crud.session.update', new_callable=AsyncMock)
        mock_update.return_value = mock_session
        
        mock_db = AsyncMock()
        
        # Mock calc_playback_url_hash
        from app.services.utils_playback import calc_playback_url_hash
        expected_hash = calc_playback_url_hash(new_playback_url)
        
        # Act
        service = SessionService(db=mock_db)
        session_update = LiveSessionUpdate(playback_url=new_playback_url)
        
        role = "REGULAR"  # ← 新增：权限参数（字符串格式）
        await service.update_scheduled_session_info(
            session_id=session_id,
            session_update=session_update,
            user_id=mock_test_user['public_id'],
            role=role  # ← 新增：传递权限参数
        )
        
        # Assert: 验证 update 调用时包含了 playback_url_hash
        mock_update.assert_called_once()
        update_call_args = mock_update.call_args
        update_data = update_call_args[1]['obj_in']
        
        assert isinstance(update_data, dict)
        assert update_data.get('playback_url') == new_playback_url
        assert update_data.get('playback_url_hash') == expected_hash

    @pytest.mark.asyncio
    async def test_auto_generate_playback_url_updates_hash(self, mocker, mock_test_user):
        """
        测试 auto_generate_playback_url 生成回放地址时同步更新 hash
        - 场景: auto_generate_playback_url 为某 Session 生成默认回放地址
        - 断言: 生成的回放 URL 同步写入 playback_url_hash
        """
        # Arrange
        session_id = uuid.uuid4()
        video_id = uuid.uuid4()
        
        mock_session = create_mock_session(
            session_id=session_id,
            room_id=uuid.uuid4(),
            status=LiveSessionStatus.READY,
            video_id=video_id,
            user_id=mock_test_user['public_id']
        )
        mock_session.playback_url = None
        mock_session.playback_url_hash = None
        
        # Mock CRUD
        mock_get = mocker.patch('app.crud.session.get', new_callable=AsyncMock)
        mock_get.return_value = mock_session
        
        mock_db = AsyncMock()
        
        # Act
        service = SessionService(db=mock_db)
        mocker.patch('os.getenv', return_value="http://test-cdn.com")
        
        await service.auto_generate_playback_url(session_id=session_id)
        
        # Assert: 验证 playback_url 和 playback_url_hash 都被设置
        expected_url = f"http://test-cdn.com/media/videos/{video_id}/playlist.m3u8"
        assert mock_session.playback_url == expected_url
        
        from app.services.utils_playback import calc_playback_url_hash
        expected_hash = calc_playback_url_hash(expected_url)
        assert mock_session.playback_url_hash == expected_hash
        
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once_with(mock_session)