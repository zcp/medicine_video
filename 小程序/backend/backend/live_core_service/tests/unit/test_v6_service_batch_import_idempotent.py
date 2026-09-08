"""
LiveCore Service - V6 Batch Import Service Idempotent Unit Tests

This module contains unit tests for BatchImportService with idempotency logic (V6 deduplication).
All external dependencies (CRUD operations) are mocked.
"""

import pytest
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch, MagicMock
from typing import Dict

from app.services.batch_import import BatchImportService
from app.models.live_core import LiveRoom, LiveSession, LiveSessionStatus
from app.exceptions import InvalidParameterException
from app.services.session_import import SessionImportService


# ==================== Test Helper Functions ====================

def create_mock_room(
    room_id: uuid.UUID = None,
    user_id: uuid.UUID = None,
    external_room_id: str = None,
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
    mock_room.external_room_id = external_room_id
    mock_room.created_at = datetime.utcnow()
    mock_room.updated_at = datetime.utcnow()

    return mock_room


def create_mock_session(
    session_id: uuid.UUID = None,
    room_id: uuid.UUID = None,
    playback_url: str = "https://example.com/video123"
) -> LiveSession:
    """创建模拟的LiveSession对象"""
    if session_id is None:
        session_id = uuid.uuid4()
    if room_id is None:
        room_id = uuid.uuid4()

    mock_session = LiveSession()
    mock_session.id = session_id
    mock_session.room_id = room_id
    mock_session.status = LiveSessionStatus.FINISHED
    mock_session.playback_url = playback_url
    mock_session.created_at = datetime.utcnow()
    mock_session.updated_at = datetime.utcnow()

    return mock_session


# ==================== Test BatchImportService._get_or_create_room_for_row ====================

class TestBatchImportServiceRoomIdempotent:
    """测试 BatchImportService._get_or_create_room_for_row 的房间幂等逻辑"""

    @pytest.mark.asyncio
    async def test_get_or_create_room_with_room_id_reuse(self):
        """
        测试有 room_id 时复用已有房间
        - 场景: row 含 room_id，房间存在且属于当前用户
        - 断言: 调用 crud_room.get，不调用 get_by_external_id 和 create，返回已有房间
        """
        # Arrange
        mock_db = AsyncMock()
        public_id = uuid.uuid4()
        room_id = uuid.uuid4()
        
        existing_room = create_mock_room(room_id=room_id, user_id=public_id)
        
        row = {
            "room_id": str(room_id),
            "room_title": "测试房间",
            "playback_url": "https://example.com/video123"
        }
        
        with patch('app.services.batch_import.crud_room') as mock_crud_room:
            mock_crud_room.get = AsyncMock(return_value=existing_room)
            
            service = BatchImportService(mock_db)
            
            # Act
            result_room = await service._get_or_create_room_for_row(public_id, row)
            
            # Assert
            assert result_room == existing_room
            # 注意：crud_room.get 的 db 参数是位置参数，不是关键字参数
            mock_crud_room.get.assert_called_once_with(
                mock_db,
                room_id=room_id,
                user_id=public_id
            )
            mock_crud_room.get_by_external_id.assert_not_called()
            mock_crud_room.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_or_create_room_with_external_room_id_reuse(self):
        """
        测试有 external_room_id 时复用已有房间
        - 场景: 无 room_id，有 external_room_id 且命中
        - 断言: 调用 get_by_external_id，不调用 create，返回已有房间
        """
        # Arrange
        mock_db = AsyncMock()
        public_id = uuid.uuid4()
        external_room_id = "ext_room_123"
        
        existing_room = create_mock_room(
            user_id=public_id,
            external_room_id=external_room_id
        )
        
        row = {
            "external_room_id": external_room_id,
            "room_title": "测试房间",
            "playback_url": "https://example.com/video123"
        }
        
        with patch('app.services.batch_import.crud_room') as mock_crud_room:
            mock_crud_room.get_by_external_id = AsyncMock(return_value=existing_room)
            
            service = BatchImportService(mock_db)
            
            # Act
            result_room = await service._get_or_create_room_for_row(public_id, row)
            
            # Assert
            assert result_room == existing_room
            mock_crud_room.get_by_external_id.assert_called_once_with(
                db=mock_db,
                user_id=public_id,
                external_room_id=external_room_id
            )
            mock_crud_room.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_or_create_room_create_with_external_room_id(self):
        """
        测试有 external_room_id 但未命中时创建新房间
        - 场景: 无 room_id，external_room_id 未命中
        - 断言: 调用 create，最终房间的 external_room_id 被设置
        """
        # Arrange
        mock_db = AsyncMock()
        public_id = uuid.uuid4()
        external_room_id = "new_ext_room_123"
        
        new_room = create_mock_room(user_id=public_id)
        
        row = {
            "external_room_id": external_room_id,
            "room_title": "新房间",
            "playback_url": "https://example.com/video123"
        }
        
        with patch('app.services.batch_import.crud_room') as mock_crud_room:
            mock_crud_room.get_by_external_id = AsyncMock(return_value=None)
            mock_crud_room.create = AsyncMock(return_value=new_room)
            
            # Mock commit 和 refresh
            mock_db.commit = AsyncMock()
            mock_db.refresh = AsyncMock()
            
            service = BatchImportService(mock_db)
            
            # Act
            result_room = await service._get_or_create_room_for_row(public_id, row)
            
            # Assert
            assert result_room == new_room
            mock_crud_room.get_by_external_id.assert_called_once()
            mock_crud_room.create.assert_called_once()
            
            # 验证 external_room_id 被设置
            assert new_room.external_room_id == external_room_id
            mock_db.commit.assert_called_once()
            mock_db.refresh.assert_called_once_with(new_room)

    @pytest.mark.asyncio
    async def test_get_or_create_room_with_room_id_not_found_raises(self):
        """
        测试 room_id 提供但房间不存在时抛出异常
        - 场景: room_id 提供但房间不存在或无权限
        - 断言: 抛出 InvalidParameterException
        """
        # Arrange
        mock_db = AsyncMock()
        public_id = uuid.uuid4()
        room_id = uuid.uuid4()
        
        row = {
            "room_id": str(room_id),
            "room_title": "测试房间",
            "playback_url": "https://example.com/video123"
        }
        
        with patch('app.services.batch_import.crud_room') as mock_crud_room:
            mock_crud_room.get = AsyncMock(return_value=None)
            
            service = BatchImportService(mock_db)
            
            # Act & Assert
            with pytest.raises(InvalidParameterException) as exc_info:
                await service._get_or_create_room_for_row(public_id, row)
            
            assert "不存在" in str(exc_info.value) or "无权限" in str(exc_info.value)


# ==================== Test BatchImportService._process_row ====================

class TestBatchImportServiceSessionIdempotent:
    """测试 BatchImportService._process_row 的会话幂等逻辑"""

    @pytest.mark.asyncio
    async def test_process_row_apply_first_time_success(self):
        """
        测试第一次导入成功
        - 场景: mode="apply"，第一次导入
        - 断言: status == "success"，skipped == False，skip_reason is None
        """
        # Arrange
        mock_db = AsyncMock()
        public_id = uuid.uuid4()
        room_id = uuid.uuid4()
        session_id = uuid.uuid4()
        
        mock_room = create_mock_room(room_id=room_id, user_id=public_id)
        mock_session = create_mock_session(session_id=session_id, room_id=room_id)
        
        row = {
            "room_title": "测试房间",
            "playback_url": "https://example.com/video123",
            "status": "finished"
        }
        
        with patch.object(BatchImportService, '_get_or_create_room_for_row', new_callable=AsyncMock) as mock_get_room, \
             patch('app.services.batch_import.SessionImportService') as mock_session_service_class:
            
            mock_get_room.return_value = mock_room
            
            mock_session_service = MagicMock()
            mock_session_service.import_create_session = AsyncMock(return_value=(mock_session, False))
            mock_session_service_class.return_value = mock_session_service
            
            service = BatchImportService(mock_db)
            
            # Act
            result = await service._process_row(public_id, 1, row, "apply")
            
            # Assert
            assert result["status"] == "success"
            assert result["skipped"] is False
            assert result["skip_reason"] is None
            assert result["room_id"] == str(room_id)
            assert result["session_id"] == str(session_id)
            assert result["error"] is None

    @pytest.mark.asyncio
    async def test_process_row_apply_idempotent_hit(self):
        """
        测试幂等命中
        - 场景: mode="apply"，命中幂等
        - 断言: skipped == True，skip_reason == "duplicate_session_by_playback_url"
        """
        # Arrange
        mock_db = AsyncMock()
        public_id = uuid.uuid4()
        room_id = uuid.uuid4()
        session_id = uuid.uuid4()
        
        mock_room = create_mock_room(room_id=room_id, user_id=public_id)
        existing_session = create_mock_session(session_id=session_id, room_id=room_id)
        
        row = {
            "room_title": "测试房间",
            "playback_url": "https://example.com/video123",
            "status": "finished"
        }
        
        with patch.object(BatchImportService, '_get_or_create_room_for_row', new_callable=AsyncMock) as mock_get_room, \
             patch('app.services.batch_import.SessionImportService') as mock_session_service_class:
            
            mock_get_room.return_value = mock_room
            
            mock_session_service = MagicMock()
            mock_session_service.import_create_session = AsyncMock(return_value=(existing_session, True))
            mock_session_service_class.return_value = mock_session_service
            
            service = BatchImportService(mock_db)
            
            # Act
            result = await service._process_row(public_id, 1, row, "apply")
            
            # Assert
            assert result["status"] == "success"
            assert result["skipped"] is True
            assert result["skip_reason"] == "duplicate_session_by_playback_url"
            assert result["room_id"] == str(room_id)
            assert result["session_id"] == str(session_id)

    @pytest.mark.asyncio
    async def test_process_row_dry_run_no_db_writes(self):
        """
        测试 dry_run 模式不写库
        - 场景: mode="dry_run"
        - 断言: 不调用 SessionImportService.import_create_session
        """
        # Arrange
        mock_db = AsyncMock()
        public_id = uuid.uuid4()
        
        row = {
            "room_title": "测试房间",
            "playback_url": "https://example.com/video123",
            "status": "finished"
        }
        
        with patch('app.services.batch_import.SessionImportService') as mock_session_service_class:
            service = BatchImportService(mock_db)
            
            # Act
            result = await service._process_row(public_id, 1, row, "dry_run")
            
            # Assert
            assert result["status"] == "success"
            assert result["skipped"] is False
            assert result["skip_reason"] is None
            # 验证没有调用 SessionImportService
            mock_session_service_class.assert_not_called()

    @pytest.mark.asyncio
    async def test_process_row_missing_required_fields(self):
        """
        测试缺少必需字段时返回失败
        - 场景: row 缺少 room_title 或 playback_url
        - 断言: status == "failed"，error 包含相应信息
        """
        # Arrange
        mock_db = AsyncMock()
        public_id = uuid.uuid4()
        
        # 缺少 playback_url
        row = {
            "room_title": "测试房间"
        }
        
        service = BatchImportService(mock_db)
        
        # Act
        result = await service._process_row(public_id, 1, row, "apply")
        
        # Assert
        assert result["status"] == "failed"
        assert result["error"] is not None
        assert "playback_url" in result["error"].lower() or "不能为空" in result["error"]


# ==================== Test BatchImportService Header Aliases ====================

class TestBatchImportServiceHeaderAliases:
    """测试 BatchImportService 的表头别名映射"""

    @pytest.mark.asyncio
    async def test_apply_header_aliases_external_room_id(self):
        """
        测试 external_room_id 的表头别名映射
        - 场景: CSV 表头为 "external_room_id"、"直播间id"、"直播间ID"
        - 断言: 均能映射到 row["external_room_id"]
        """
        # Arrange
        mock_db = AsyncMock()
        service = BatchImportService(mock_db)
        
        # 注意：_apply_header_aliases 期望 row 的 key 是小写的（因为 CSV 解析时会做 lower().strip()）
        test_cases = [
            {"external_room_id": "ext_123"},
            {"直播间id": "ext_456"},  # 已经是小写
            {"直播间id": "ext_789"},  # "直播间ID" 需要改为小写 "直播间id"
        ]
        
        for test_row in test_cases:
            # Act
            result = service._apply_header_aliases([test_row])
            
            # Assert
            assert len(result) == 1
            assert "external_room_id" in result[0]
            assert result[0]["external_room_id"] in ["ext_123", "ext_456", "ext_789"]

