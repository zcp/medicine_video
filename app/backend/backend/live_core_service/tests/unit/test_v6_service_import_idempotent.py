"""
LiveCore Service - V6 Session Import Service Idempotent Unit Tests

This module contains unit tests for SessionImportService.import_create_session
with idempotency logic (V6 deduplication).
All external dependencies (CRUD operations) are mocked.
"""

import pytest
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch
from typing import Tuple

from app.services.session_import import SessionImportService
from app.models.live_core import LiveSession, LiveRoom, LiveSessionStatus
from app.exceptions import (
    RoomNotFoundException,
    PermissionDeniedException,
    InvalidParameterException,
)
from app.services.utils_playback import normalize_playback_url, calc_playback_url_hash


# ==================== Test Helper Functions ====================

def create_mock_room(
    room_id: uuid.UUID = None,
    user_id: uuid.UUID = None,
    title: str = "测试房间"
) -> LiveRoom:
    """创建模拟的LiveRoom对象"""
    if room_id is None:
        room_id = uuid.uuid4()
    if user_id is None:
        user_id = uuid.uuid4()

    mock_room = LiveRoom()
    mock_room.id = room_id
    mock_room.user_id = user_id
    mock_room.title = title
    mock_room.created_at = datetime.utcnow()
    mock_room.updated_at = datetime.utcnow()

    return mock_room


def create_mock_session(
    session_id: uuid.UUID = None,
    room_id: uuid.UUID = None,
    playback_url: str = "https://example.com/video123",
    playback_url_hash: str = None,
    status: LiveSessionStatus = LiveSessionStatus.FINISHED
) -> LiveSession:
    """创建模拟的LiveSession对象"""
    if session_id is None:
        session_id = uuid.uuid4()
    if room_id is None:
        room_id = uuid.uuid4()
    if playback_url_hash is None:
        playback_url_hash = calc_playback_url_hash(playback_url)

    mock_session = LiveSession()
    mock_session.id = session_id
    mock_session.room_id = room_id
    mock_session.status = status
    mock_session.playback_url = normalize_playback_url(playback_url)
    mock_session.playback_url_hash = playback_url_hash
    mock_session.start_time = datetime.now(timezone.utc)
    mock_session.created_at = datetime.utcnow()
    mock_session.updated_at = datetime.utcnow()

    return mock_session


# ==================== Test SessionImportService.import_create_session ====================

class TestSessionImportServiceIdempotent:
    """测试 SessionImportService.import_create_session 的幂等逻辑"""

    @pytest.mark.asyncio
    async def test_import_create_session_first_time_success(self):
        """
        测试第一次导入会话成功
        - Mock: crud_room.get 返回房间，crud_session.get_by_room_and_playback_hash 返回 None
        - 断言: 调用 create，返回 (session, idempotent_hit=False)
        """
        # Arrange
        mock_db = AsyncMock()
        room_id = uuid.uuid4()
        public_id = uuid.uuid4()
        playback_url = "https://example.com/video123"
        
        mock_room = create_mock_room(room_id=room_id, user_id=public_id)
        mock_session = create_mock_session(room_id=room_id, playback_url=playback_url)
        
        session_in = {
            "status": "ready",
            "playback_url": playback_url,
            "start_time": datetime.now(timezone.utc)
        }
        
        expected_hash = calc_playback_url_hash(playback_url)
        expected_normalized = normalize_playback_url(playback_url)
        
        with patch('app.services.session_import.crud_room') as mock_crud_room, \
             patch('app.services.session_import.crud_session') as mock_crud_session:
            
            mock_crud_room.get = AsyncMock(return_value=mock_room)
            mock_crud_session.get_by_room_and_playback_hash = AsyncMock(return_value=None)
            mock_crud_session.create = AsyncMock(return_value=mock_session)
            
            service = SessionImportService(mock_db)
            
            # Act
            role = "REGULAR"  # ← 新增：权限参数
            result_session, idempotent_hit = await service.import_create_session(
                room_id=room_id,
                public_id=public_id,
                session_in=session_in,
                role=role  # ← 新增：权限参数
            )
            
            # Assert
            assert idempotent_hit is False
            assert result_session == mock_session
            
            # 验证调用了 get_by_room_and_playback_hash
            mock_crud_session.get_by_room_and_playback_hash.assert_called_once()
            call_args = mock_crud_session.get_by_room_and_playback_hash.call_args
            assert call_args[1]['room_id'] == room_id
            assert call_args[1]['playback_url_hash'] == expected_hash
            
            # 验证调用了 create
            mock_crud_session.create.assert_called_once()
            create_call_args = mock_crud_session.create.call_args
            created_data = create_call_args[1]['obj_in']
            assert created_data['room_id'] == room_id
            assert created_data['status'] == "ready"
            assert created_data['playback_url'] == expected_normalized
            assert created_data['playback_url_hash'] == expected_hash

    @pytest.mark.asyncio
    async def test_import_create_session_idempotent_hit(self):
        """
        测试幂等命中：已存在相同 playback_url_hash 的会话
        - Mock: crud_session.get_by_room_and_playback_hash 返回已有 Session
        - 断言: 不调用 create，返回已有 Session，idempotent_hit=True
        """
        # Arrange
        mock_db = AsyncMock()
        room_id = uuid.uuid4()
        public_id = uuid.uuid4()
        playback_url = "https://example.com/video123"
        
        mock_room = create_mock_room(room_id=room_id, user_id=public_id)
        existing_session = create_mock_session(room_id=room_id, playback_url=playback_url)
        
        session_in = {
            "status": "ready",
            "playback_url": playback_url
        }
        
        with patch('app.services.session_import.crud_room') as mock_crud_room, \
             patch('app.services.session_import.crud_session') as mock_crud_session:
            
            mock_crud_room.get = AsyncMock(return_value=mock_room)
            mock_crud_session.get_by_room_and_playback_hash = AsyncMock(return_value=existing_session)
            
            service = SessionImportService(mock_db)
            
            # Act
            role = "REGULAR"  # ← 新增：权限参数
            result_session, idempotent_hit = await service.import_create_session(
                room_id=room_id,
                public_id=public_id,
                session_in=session_in,
                role=role  # ← 新增：权限参数
            )
            
            # Assert
            assert idempotent_hit is True
            assert result_session == existing_session
            
            # 验证调用了 get_by_room_and_playback_hash
            mock_crud_session.get_by_room_and_playback_hash.assert_called_once()
            
            # 验证没有调用 create
            mock_crud_session.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_import_create_session_room_not_found_raises(self):
        """
        测试房间不存在时抛出异常
        - Mock: crud_room.get 返回 None
        - 断言: 抛出 RoomNotFoundException
        """
        # Arrange
        mock_db = AsyncMock()
        room_id = uuid.uuid4()
        public_id = uuid.uuid4()
        
        session_in = {
            "status": "ready",
            "playback_url": "https://example.com/video123"
        }
        
        with patch('app.services.session_import.crud_room') as mock_crud_room:
            mock_crud_room.get = AsyncMock(return_value=None)
            
            service = SessionImportService(mock_db)
            
            # Act & Assert
            role = "REGULAR"  # ← 新增：权限参数（字符串格式）
            with pytest.raises(RoomNotFoundException) as exc_info:
                await service.import_create_session(
                    room_id=room_id,
                    public_id=public_id,
                    session_in=session_in,
                    role=role  # ← 新增：传递权限参数
                )
            
            assert str(room_id) in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_import_create_session_permission_denied_raises(self):
        """
        测试权限不足时抛出异常
        - Mock: crud_room.get 返回房间但 room.user_id != public_id
        - 断言: 抛出 PermissionDeniedException
        """
        # Arrange
        mock_db = AsyncMock()
        room_id = uuid.uuid4()
        public_id = uuid.uuid4()
        other_user_id = uuid.uuid4()
        
        mock_room = create_mock_room(room_id=room_id, user_id=other_user_id)
        
        session_in = {
            "status": "ready",
            "playback_url": "https://example.com/video123"
        }
        
        with patch('app.services.session_import.crud_room') as mock_crud_room:
            mock_crud_room.get = AsyncMock(return_value=mock_room)
            
            service = SessionImportService(mock_db)
            
            # Act & Assert
            role = "REGULAR"  # ← 新增：权限参数
            with pytest.raises(PermissionDeniedException):
                await service.import_create_session(
                    room_id=room_id,
                    public_id=public_id,
                    session_in=session_in,
                    role=role  # ← 新增：权限参数
                )

    @pytest.mark.asyncio
    async def test_import_create_session_invalid_status_raises(self):
        """
        测试非法 status 时抛出异常
        - 场景: status 不是 'finished' 或 'ready'
        - 断言: 抛出 InvalidParameterException
        """
        # Arrange
        mock_db = AsyncMock()
        room_id = uuid.uuid4()
        public_id = uuid.uuid4()
        
        mock_room = create_mock_room(room_id=room_id, user_id=public_id)
        
        session_in = {
            "status": "scheduled",  # 非法状态
            "playback_url": "https://example.com/video123"
        }
        
        with patch('app.services.session_import.crud_room') as mock_crud_room:
            mock_crud_room.get = AsyncMock(return_value=mock_room)
            
            service = SessionImportService(mock_db)
            
            # Act & Assert
            role = "REGULAR"  # ← 新增：权限参数（字符串格式）
            with pytest.raises(InvalidParameterException) as exc_info:
                await service.import_create_session(
                    room_id=room_id,
                    public_id=public_id,
                    session_in=session_in,
                    role=role  # ← 新增：传递权限参数
                )
            
            assert "finished" in str(exc_info.value.message).lower() or "ready" in str(exc_info.value.message).lower()

    @pytest.mark.asyncio
    async def test_import_create_session_missing_playback_url_raises(self):
        """
        测试缺少 playback_url 时抛出异常
        - 场景: session_in 中没有 playback_url
        - 断言: 抛出 InvalidParameterException
        """
        # Arrange
        mock_db = AsyncMock()
        room_id = uuid.uuid4()
        public_id = uuid.uuid4()
        
        mock_room = create_mock_room(room_id=room_id, user_id=public_id)
        
        session_in = {
            "status": "ready"
            # 缺少 playback_url
        }
        
        with patch('app.services.session_import.crud_room') as mock_crud_room:
            mock_crud_room.get = AsyncMock(return_value=mock_room)
            
            service = SessionImportService(mock_db)
            
            # Act & Assert
            role = "REGULAR"  # ← 新增：权限参数（字符串格式）
            with pytest.raises(InvalidParameterException) as exc_info:
                await service.import_create_session(
                    room_id=room_id,
                    public_id=public_id,
                    session_in=session_in,
                    role=role  # ← 新增：传递权限参数
                )
            
            assert "playback_url" in str(exc_info.value.message).lower()

    @pytest.mark.asyncio
    async def test_import_create_session_url_normalization(self):
        """
        测试 playback_url 规范化处理
        - 场景: 传入带空格的 URL
        - 断言: 存储的是规范化后的 URL（去除首尾空格）
        """
        # Arrange
        mock_db = AsyncMock()
        room_id = uuid.uuid4()
        public_id = uuid.uuid4()
        playback_url_with_spaces = "  https://example.com/video123  "
        
        mock_room = create_mock_room(room_id=room_id, user_id=public_id)
        mock_session = create_mock_session(room_id=room_id, playback_url=playback_url_with_spaces)
        
        session_in = {
            "status": "ready",
            "playback_url": playback_url_with_spaces
        }
        
        expected_normalized = normalize_playback_url(playback_url_with_spaces)
        expected_hash = calc_playback_url_hash(playback_url_with_spaces)
        
        with patch('app.services.session_import.crud_room') as mock_crud_room, \
             patch('app.services.session_import.crud_session') as mock_crud_session:
            
            mock_crud_room.get = AsyncMock(return_value=mock_room)
            mock_crud_session.get_by_room_and_playback_hash = AsyncMock(return_value=None)
            mock_crud_session.create = AsyncMock(return_value=mock_session)
            
            service = SessionImportService(mock_db)
            
            # Act
            role = "REGULAR"  # ← 新增：权限参数
            await service.import_create_session(
                room_id=room_id,
                public_id=public_id,
                session_in=session_in,
                role=role  # ← 新增：权限参数
            )
            
            # Assert: 验证 create 调用时使用的是规范化后的 URL
            create_call_args = mock_crud_session.create.call_args
            created_data = create_call_args[1]['obj_in']
            assert created_data['playback_url'] == expected_normalized
            assert created_data['playback_url_hash'] == expected_hash

