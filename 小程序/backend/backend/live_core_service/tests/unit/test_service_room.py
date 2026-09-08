"""
LiveCore Service - Room Service Unit Tests

This module contains comprehensive unit tests for the RoomService class,
testing all business logic in complete isolation using mocks.
"""

import pytest
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from typing import List, Dict, Any

from app.services.room_service import RoomService
from app.schemas.live_core import LiveRoomCreate, LiveRoomUpdate
from app.models.live_core import LiveRoom
from app.exceptions import (
    RoomNotFoundException,
    ActionForbiddenException,
    ParentRoomNotFoundException,
    PermissionDeniedException
)


# ==================== Test Data Fixtures ====================

def create_mock_room(
    room_id: uuid.UUID = None,
    title: str = "测试房间",
    description: str = "测试描述",
    stream_key: str = "sk_live_test123",
    is_private: bool = False,
    record_by_default: bool = True,
    parent_room_id: uuid.UUID = None,
    user_id: uuid.UUID = None,
    cover_url: str = None
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
    mock_room.parent_room_id = parent_room_id
    mock_room.user_id = user_id
    mock_room.cover_url = cover_url
    mock_room.created_at = datetime.utcnow()
    mock_room.updated_at = datetime.utcnow()
    
    return mock_room


def create_room_create_data(
    title: str = "新建房间",
    description: str = "新建房间描述",
    parent_room_id: uuid.UUID = None,
    user_id: uuid.UUID = None
) -> LiveRoomCreate:
    """创建房间创建请求数据"""
    return LiveRoomCreate(
        title=title,
        description=description,
        parent_room_id=parent_room_id,
        user_id=user_id,
        is_private=False,
        record_by_default=True
    )


def create_room_update_data(
    title: str = "更新后的房间",
    description: str = "更新后的描述"
) -> LiveRoomUpdate:
    """创建房间更新请求数据"""
    return LiveRoomUpdate(
        title=title,
        description=description
    )


# ==================== create_new_room Tests ====================

@pytest.fixture
def mock_test_user():
    """为单元测试提供模拟用户数据"""
    return {
        "public_id": "550e8400-e29b-41d4-a716-446655440000",
        "username": "test_user",
        "email": "test@example.com"
    }

@pytest.mark.asyncio
async def test_create_new_room_success(mocker, mock_test_user):
    """
    T2: REGULAR + can_stream=true 创建房间成功
    """
    # Arrange
    mock_room = create_mock_room(user_id=mock_test_user['public_id'])
    room_create_data = create_room_create_data(user_id=mock_test_user['public_id'])

    mocker.patch("app.services.room_service.check_scene_fields", new_callable=AsyncMock)
    mock_create = mocker.patch("app.crud.room.create", return_value=mock_room)

    # Act
    service = RoomService(db=None)
    result = await service.create_new_room(
        room_create_data,
        user_id=mock_test_user['public_id'],
        role="REGULAR",
        can_stream=True,
    )

    # Assert
    assert result == mock_room
    mock_create.assert_called_once_with(db=None, obj_in=room_create_data, user_id=mock_test_user['public_id'])


@pytest.mark.asyncio
async def test_create_new_room_denied_when_stream_disabled(mocker, mock_test_user):
    """REGULAR + can_stream=false（禁止开播）→ PermissionDeniedException"""
    from app.exceptions import PermissionDeniedException

    room_create_data = create_room_create_data(user_id=mock_test_user['public_id'])
    mock_create = mocker.patch("app.crud.room.create")
    service = RoomService(db=None)

    with pytest.raises(PermissionDeniedException, match="开播功能已被禁用"):
        await service.create_new_room(
            room_create_data,
            user_id=mock_test_user['public_id'],
            role="REGULAR",
            can_stream=False,
        )
    mock_create.assert_not_called()


@pytest.mark.asyncio
async def test_create_new_room_admin_bypass(mocker, mock_test_user):
    """ADMIN + ADMIN_STREAM_BYPASS 可旁路 can_stream"""
    mock_room = create_mock_room(user_id=mock_test_user['public_id'])
    room_create_data = create_room_create_data(user_id=mock_test_user['public_id'])
    mocker.patch("app.services.room_service.check_scene_fields", new_callable=AsyncMock)
    mocker.patch("app.crud.room.create", return_value=mock_room)
    mocker.patch("app.core.config.settings.ADMIN_STREAM_BYPASS", True)

    service = RoomService(db=None)
    result = await service.create_new_room(
        room_create_data,
        user_id=mock_test_user['public_id'],
        role="ADMIN",
        can_stream=False,
    )
    assert result == mock_room


@pytest.mark.asyncio
async def test_create_new_room_with_parent_success(mocker, mock_test_user):
    """
    测试成功创建分会场（带父房间ID）
    """
    # Arrange
    parent_room_id = uuid.uuid4()
    mock_parent_room = create_mock_room(room_id=parent_room_id, title="主会场", user_id=mock_test_user['public_id'])
    mock_room = create_mock_room(parent_room_id=parent_room_id, title="分会场", user_id=mock_test_user['public_id'])
    room_create_data = create_room_create_data(
        title="分会场",
        parent_room_id=parent_room_id,
        user_id=mock_test_user['public_id']
    )

    mocker.patch("app.services.room_service.check_scene_fields", new_callable=AsyncMock)
    mock_get = mocker.patch("app.crud.room.get", return_value=mock_parent_room)
    mock_create = mocker.patch("app.crud.room.create", return_value=mock_room)

    # Act
    service = RoomService(db=None)
    result = await service.create_new_room(
        room_create_data, 
        user_id=mock_test_user['public_id'],
        role="REGULAR",
        can_stream=True,
    )

    # Assert
    assert result == mock_room
    mock_get.assert_called_once_with(db=None, room_id=parent_room_id)
    mock_create.assert_called_once_with(db=None, obj_in=room_create_data, user_id=mock_test_user['public_id'])

@pytest.mark.asyncio
async def test_create_sub_venue_parent_not_found(mocker, mock_test_user):
    """
    测试创建分会场时父房间不存在的情况
    """
    # Arrange
    parent_room_id = uuid.uuid4()
    room_create_data = create_room_create_data(
        title="分会场",
        parent_room_id=parent_room_id,
        user_id=mock_test_user['public_id']
    )

    mock_get = mocker.patch("app.crud.room.get", return_value=None)

    # Act & Assert
    service = RoomService(db=None)
    with pytest.raises(ParentRoomNotFoundException):
        await service.create_new_room(
            room_create_data,
            user_id=mock_test_user['public_id'],
            role="REGULAR",
            can_stream=True,
        )

    mock_get.assert_called_once_with(db=None, room_id=parent_room_id)


# ==================== get_room_list Tests ====================

@pytest.mark.asyncio
async def test_get_room_list_success(mocker, mock_test_user):
    """
    测试成功获取房间列表
    - 模拟CRUD层返回房间列表和总数
    - 验证返回正确的数据和分页计算
    """
    # Arrange
    mock_room_1 = create_mock_room(title="房间1", user_id=mock_test_user['public_id'])
    mock_room_2 = create_mock_room(title="房间2", user_id=mock_test_user['public_id'])
    mock_rooms = [mock_room_1, mock_room_2]
    mock_total = 10

    # Mock CRUD operations
    mock_get_multi = mocker.patch(
        "app.crud.room.get_multi_and_total",
        return_value=(mock_rooms, mock_total)
    )

    # Act
    service = RoomService(db=None)
    role = "REGULAR"  # ← 新增：权限参数（字符串格式）
    result_rooms, result_total = await service.get_room_list(
        page=2, 
        size=5, 
        user_id=mock_test_user['public_id'],
        role=role  # ← 新增：传递权限参数
    )

    # Assert
    assert result_rooms == mock_rooms
    assert result_total == mock_total
    # 验证skip计算: (page - 1) * size = (2 - 1) * 5 = 5
    mock_get_multi.assert_called_once_with(db=None, skip=5, limit=5, user_id=mock_test_user['public_id'], role=role)


@pytest.mark.asyncio
async def test_get_room_list_empty_result(mocker, mock_test_user):
    """
    测试获取空房间列表
    - 模拟没有房间的情况
    - 验证返回空列表和0总数
    """
    # Arrange
    mock_rooms = []
    mock_total = 0

    # Mock CRUD operations
    mock_get_multi = mocker.patch(
        "app.crud.room.get_multi_and_total",
        return_value=(mock_rooms, mock_total)
    )

    # Act
    service = RoomService(db=None)
    role = "REGULAR"  # ← 新增：权限参数（字符串格式）
    result_rooms, result_total = await service.get_room_list(page=1, size=10, user_id=mock_test_user['public_id'], role=role)

    # Assert
    assert result_rooms == []
    assert result_total == 0
    mock_get_multi.assert_called_once_with(db=None, skip=0, limit=10, user_id=mock_test_user['public_id'], role=role)


# ==================== get_room_details Tests ====================

@pytest.mark.asyncio
async def test_get_room_details_success(mocker, mock_test_user):
    """
    测试成功获取房间详情
    - 模拟房间存在的情况
    - 验证返回正确的房间对象
    """
    # Arrange
    room_id = uuid.uuid4()
    mock_room = create_mock_room(room_id=room_id, user_id=mock_test_user['public_id'])

    # Mock CRUD operations
    mock_get = mocker.patch("app.crud.room.get", return_value=mock_room)

    # Act
    service = RoomService(db=None)
    role = "REGULAR"  # ← 新增：权限参数（字符串格式）
    result = await service.get_room_details(
        room_id, 
        user_id=mock_test_user['public_id'],
        role=role  # ← 新增：传递权限参数
    )

    # Assert
    assert result == mock_room
    # ← 注意：get_room_details内部调用crud_room.get时只传递room_id，不传递user_id
    mock_get.assert_called_once_with(db=None, room_id=room_id)


@pytest.mark.asyncio
async def test_get_room_details_not_found(mocker, mock_test_user):
    """
    测试获取不存在的房间详情
    - 模拟房间不存在的情况
    - 验证抛出RoomNotFoundException异常
    """
    # Arrange
    room_id = uuid.uuid4()

    # Mock CRUD operations - 房间不存在
    mock_get = mocker.patch("app.crud.room.get", return_value=None)

    # Act & Assert
    service = RoomService(db=None)
    role = "REGULAR"  # ← 新增：权限参数（字符串格式）
    with pytest.raises(RoomNotFoundException):
        await service.get_room_details(room_id, user_id=mock_test_user['public_id'], role=role)

    # ← 注意：get_room_details内部调用crud_room.get时只传递room_id，不传递user_id
    mock_get.assert_called_once_with(db=None, room_id=room_id)


# ==================== update_room_info Tests ====================

@pytest.mark.asyncio
async def test_update_room_success(mocker, mock_test_user):
    """
    测试成功更新房间信息
    - 模拟房间存在且未在直播
    - 验证更新成功并返回更新后的房间对象
    """
    # Arrange
    room_id = uuid.uuid4()
    mock_room = create_mock_room(room_id=room_id, user_id=mock_test_user['public_id'])
    updated_mock_room = create_mock_room(room_id=room_id, title="更新后的房间", user_id=mock_test_user['public_id'])
    room_update_data = create_room_update_data()

    # Mock CRUD operations（当前后端不再调用 is_live，仅 mock get/update）
    mock_get = mocker.patch("app.crud.room.get", return_value=mock_room)
    mock_update = mocker.patch("app.crud.room.update", return_value=updated_mock_room)

    # Act
    service = RoomService(db=None)
    role = "REGULAR"  # ← 新增：权限参数（字符串格式）
    result = await service.update_room_info(
        room_id, 
        room_update_data, 
        user_id=mock_test_user['public_id'],
        role=role  # ← 新增：传递权限参数
    )

    # Assert
    assert result == updated_mock_room
    mock_get.assert_called_once_with(db=None, room_id=room_id)
    mock_update.assert_called_once_with(db=None, db_obj=mock_room, obj_in=room_update_data)


@pytest.mark.asyncio
async def test_update_room_not_found(mocker, mock_test_user):
    """
    测试更新不存在的房间
    - 模拟房间不存在的情况
    - 验证抛出RoomNotFoundException异常
    """
    # Arrange
    room_id = uuid.uuid4()
    room_update_data = create_room_update_data()

    # Mock CRUD operations - 房间不存在
    mock_get = mocker.patch("app.crud.room.get", return_value=None)

    # Act & Assert
    service = RoomService(db=None)
    role = "REGULAR"  # ← 新增：权限参数（字符串格式）
    with pytest.raises(RoomNotFoundException):
        await service.update_room_info(
            room_id, 
            room_update_data, 
            user_id=mock_test_user['public_id'],
            role=role  # ← 新增：传递权限参数
        )

    # ← 注意：update_room_info内部调用crud_room.get时只传递room_id，不传递user_id
    mock_get.assert_called_once_with(db=None, room_id=room_id)


@pytest.mark.asyncio
async def test_update_room_forbidden_when_live(mocker, mock_test_user):
    """
    测试更新正在直播的房间
    - 模拟房间存在但正在直播
    - 验证抛出ActionForbiddenException异常
    """
    # Arrange
    room_id = uuid.uuid4()
    mock_room = create_mock_room(room_id=room_id, user_id=mock_test_user['public_id'])
    room_update_data = create_room_update_data()

    # Mock CRUD operations
    mock_get = mocker.patch("app.crud.room.get", return_value=mock_room)
    mock_is_live = mocker.patch("app.crud.room.is_live", return_value=True)  # 正在直播

    # Act & Assert
    service = RoomService(db=None)
    role = "REGULAR"  # ← 新增：权限参数（字符串格式）
    with pytest.raises(ActionForbiddenException) as exc_info:
        await service.update_room_info(
            room_id, 
            room_update_data, 
            user_id=mock_test_user['public_id'],
            role=role  # ← 新增：传递权限参数
        )

        assert str(exc_info.value) == "无法修改正在直播的房间"
        # ← 注意：update_room_info内部调用crud_room.get时只传递room_id，不传递user_id
        mock_get.assert_called_once_with(db=None, room_id=room_id)
        mock_is_live.assert_called_once_with(db=None, room_id=room_id)


# ==================== delete_room Tests ====================

@pytest.mark.asyncio
async def test_delete_room_success(mocker, mock_test_user):
    """
    测试成功删除房间
    - 模拟房间存在且未在直播
    - 验证删除成功并返回被删除的房间对象
    """
    # Arrange
    room_id = uuid.uuid4()
    mock_room = create_mock_room(room_id=room_id, user_id=mock_test_user['public_id'])

    # Mock CRUD operations（当前后端不再调用 is_live，需 mock get/delete_room_related/remove）
    mock_get = mocker.patch("app.crud.room.get", return_value=mock_room)
    mock_remove = mocker.patch("app.crud.room.remove", return_value=mock_room)
    mock_delete_related = mocker.patch("app.crud.room.delete_room_related", new_callable=AsyncMock)

    # Act
    service = RoomService(db=None)
    role = "REGULAR"  # ← 新增：权限参数（字符串格式）
    result = await service.delete_room(
        room_id, 
        user_id=mock_test_user['public_id'],
        role=role  # ← 新增：传递权限参数
    )

    # Assert
    assert result == mock_room
    mock_get.assert_called_once_with(db=None, room_id=room_id)
    mock_delete_related.assert_called_once()
    mock_remove.assert_called_once_with(db=None, db_obj=mock_room)


@pytest.mark.asyncio
async def test_delete_room_not_found(mocker, mock_test_user):
    """
    测试删除不存在的房间
    - 模拟房间不存在的情况
    - 验证抛出RoomNotFoundException异常
    """
    # Arrange
    room_id = uuid.uuid4()

    # Mock CRUD operations - 房间不存在
    mock_get = mocker.patch("app.crud.room.get", return_value=None)

    # Act & Assert
    service = RoomService(db=None)
    role = "REGULAR"  # ← 新增：权限参数（字符串格式）
    with pytest.raises(RoomNotFoundException):
        await service.delete_room(
            room_id, 
            user_id=mock_test_user['public_id'],
            role=role  # ← 新增：传递权限参数
        )

    # ← 注意：delete_room内部调用crud_room.get时只传递room_id，不传递user_id
    mock_get.assert_called_once_with(db=None, room_id=room_id)


@pytest.mark.asyncio
async def test_delete_room_forbidden_when_live(mocker, mock_test_user):
    """
    测试删除正在直播的房间
    - 模拟房间存在但正在直播
    - 验证抛出ActionForbiddenException异常
    """
    # Arrange
    room_id = uuid.uuid4()
    mock_room = create_mock_room(room_id=room_id, user_id=mock_test_user['public_id'])

    # Mock CRUD operations
    mock_get = mocker.patch("app.crud.room.get", return_value=mock_room)
    mock_is_live = mocker.patch("app.crud.room.is_live", return_value=True)  # 正在直播

    # Act & Assert
    service = RoomService(db=None)
    role = "REGULAR"  # ← 新增：权限参数（字符串格式）
    with pytest.raises(ActionForbiddenException) as exc_info:
        await service.delete_room(
            room_id, 
            user_id=mock_test_user['public_id'],
            role=role  # ← 新增：传递权限参数
        )

    assert str(exc_info.value) == "无法删除正在直播的房间"
    # ← 注意：delete_room内部调用crud_room.get时只传递room_id，不传递user_id
    mock_get.assert_called_once_with(db=None, room_id=room_id)
    mock_is_live.assert_called_once_with(db=None, room_id=room_id)


# ==================== get_sub_venue_list Tests ====================

@pytest.mark.asyncio
async def test_get_sub_venue_list_success(mocker, mock_test_user):
    """
    测试成功获取分会场列表
    - 模拟主会场存在且有分会场
    - 验证返回正确的分会场列表和总数
    """
    # Arrange
    parent_room_id = uuid.uuid4()
    mock_parent_room = create_mock_room(room_id=parent_room_id, title="主会场", user_id=mock_test_user['public_id'])

    mock_sub_venues = [
        {
            'id': uuid.uuid4(),
            'title': '分会场1',
            'live_status': 'live',
            'current_session_id': uuid.uuid4()
        },
        {
            'id': uuid.uuid4(),
            'title': '分会场2',
            'live_status': None,
            'current_session_id': None
        }
    ]
    mock_total = 2

    # Mock CRUD operations
    mock_get = mocker.patch("app.crud.room.get", return_value=mock_parent_room)
    mock_get_sub_venues = mocker.patch(
        "app.crud.room.get_sub_venues_with_live_status",
        return_value=(mock_sub_venues, mock_total)
    )

    # Act
    service = RoomService(db=None)
    role = "REGULAR"  # ← 新增：权限参数（字符串格式）
    result_venues, result_total = await service.get_sub_venue_list(
        parent_room_id, 
        page=1, 
        size=10, 
        user_id=mock_test_user['public_id'],
        role=role  # ← 新增：传递权限参数
    )

    # Assert
    assert result_venues == mock_sub_venues
    assert result_total == mock_total
    # ← 注意：get_sub_venue_list内部调用get_room_details，get_room_details调用crud_room.get时只传递room_id
    mock_get.assert_called_once_with(db=None, room_id=parent_room_id)
    mock_get_sub_venues.assert_called_once_with(
        db=None, parent_room_id=parent_room_id, skip=0, limit=10, user_id=mock_test_user['public_id'], role=role
    )


@pytest.mark.asyncio
async def test_get_sub_venue_list_parent_not_found(mocker, mock_test_user):
    """
    测试获取分会场列表时主会场不存在
    - 模拟主会场不存在的情况
    - 验证抛出RoomNotFoundException异常
    """
    # Arrange
    parent_room_id = uuid.uuid4()

    # Mock CRUD operations - 主会场不存在
    mock_get = mocker.patch("app.crud.room.get", return_value=None)

    # Act & Assert
    service = RoomService(db=None)
    role = "REGULAR"  # ← 新增：权限参数（字符串格式）
    with pytest.raises(RoomNotFoundException):
        await service.get_sub_venue_list(
            parent_room_id, 
            page=1, 
            size=10, 
            user_id=mock_test_user['public_id'],
            role=role  # ← 新增：传递权限参数
        )

    # ← 注意：get_sub_venue_list内部调用get_room_details，get_room_details调用crud_room.get时只传递room_id
    mock_get.assert_called_once_with(db=None, room_id=parent_room_id)


@pytest.mark.asyncio
async def test_get_sub_venue_list_pagination_calculation(mocker, mock_test_user):
    """
    测试分会场列表的分页计算
    - 验证skip值的正确计算
    - 测试不同的页码和页面大小参数
    """
    # Arrange
    parent_room_id = uuid.uuid4()
    mock_parent_room = create_mock_room(room_id=parent_room_id, title="主会场", user_id=mock_test_user['public_id'])
    mock_sub_venues = []
    mock_total = 0

    # Mock CRUD operations
    mock_get = mocker.patch("app.crud.room.get", return_value=mock_parent_room)
    mock_get_sub_venues = mocker.patch(
        "app.crud.room.get_sub_venues_with_live_status",
        return_value=(mock_sub_venues, mock_total)
    )

    # Act
    service = RoomService(db=None)
    role = "REGULAR"  # ← 新增：权限参数（字符串格式）
    await service.get_sub_venue_list(
        parent_room_id, 
        page=3, 
        size=20, 
        user_id=mock_test_user['public_id'],
        role=role  # ← 新增：传递权限参数
    )

    # Assert
    # 验证skip计算: (page - 1) * size = (3 - 1) * 20 = 40
    mock_get_sub_venues.assert_called_once_with(
        db=None, parent_room_id=parent_room_id, skip=40, limit=20, user_id=mock_test_user['public_id'], role=role
    )


# ==================== TestRoomServiceUploadCover ====================

class TestRoomServiceUploadCover:
    """测试上传房间封面的业务逻辑"""
    
    @pytest.mark.asyncio
    async def test_upload_room_cover_success(self, mocker, mock_test_user):
        """
        测试成功上传封面
        - 模拟房间存在且用户有权限
        - 验证调用FileHandler保存文件
        - 验证调用CRUD层更新数据库
        """
        # 准备测试数据
        room_id = uuid.uuid4()
        user_id = uuid.UUID(mock_test_user['public_id'])
        mock_room = create_mock_room(room_id=room_id, user_id=user_id, cover_url=None)
        updated_room = create_mock_room(
            room_id=room_id, 
            user_id=user_id, 
            cover_url="/media/rooms/{}/cover_123.jpg".format(room_id)
        )
        
        # 创建Mock文件
        mock_file = MagicMock()
        mock_file.filename = "test.jpg"
        
        # Mock CRUD层方法（upload_room_cover直接调用crud_room.get，不是get_room_details）
        mock_get_room = mocker.patch(
            "app.crud.room.get",
            new_callable=AsyncMock,
            return_value=mock_room
        )
        
        # Mock FileHandler方法
        mock_delete_cover = mocker.patch("app.core.file_handler.FileHandler.delete_old_cover")
        mock_save_file = mocker.patch(
            "app.core.file_handler.FileHandler.save_cover_file",
            new_callable=AsyncMock,
            return_value="/media/rooms/{}/cover_123.jpg".format(room_id)
        )
        
        # Mock CRUD层方法
        mock_update_url = mocker.patch(
            "app.crud.room.update_cover_url",
            new_callable=AsyncMock,
            return_value=updated_room
        )
        
        # 执行上传操作
        service = RoomService(db=MagicMock())  # ← 修改：提供mock db，因为upload_room_cover需要self.db
        role = "REGULAR"  # ← 新增：权限参数（字符串格式）
        result = await service.upload_room_cover(
            room_id=room_id,
            file=mock_file,
            user_id=user_id,
            role=role  # ← 新增：传递权限参数
        )
        
        # 断言返回值
        assert result == updated_room
        
        # 验证方法调用
        mock_get_room.assert_called_once_with(db=service.db, room_id=room_id)
        mock_save_file.assert_called_once_with(file=mock_file, room_id=room_id)
        mock_update_url.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_upload_room_cover_room_not_found(self, mocker, mock_test_user):
        """
        测试房间不存在时抛出异常
        - 模拟get_room_details抛出RoomNotFoundException
        - 验证异常被正确抛出
        """
        # 准备测试数据
        room_id = uuid.uuid4()
        user_id = uuid.UUID(mock_test_user['public_id'])
        mock_file = MagicMock()
        
        # Mock CRUD层方法（upload_room_cover直接调用crud_room.get，返回None表示房间不存在）
        mock_get_room = mocker.patch(
            "app.crud.room.get",
            new_callable=AsyncMock,
            return_value=None
        )
        
        # 执行并验证异常
        service = RoomService(db=MagicMock())  # ← 修改：提供mock db
        role = "REGULAR"  # ← 新增：权限参数（字符串格式）
        with pytest.raises(RoomNotFoundException):
            await service.upload_room_cover(
                room_id=room_id,
                file=mock_file,
                user_id=user_id,
                role=role  # ← 新增：传递权限参数
            )
        
        # 验证只调用了crud_room.get
        mock_get_room.assert_called_once_with(db=service.db, room_id=room_id)
    
    @pytest.mark.asyncio
    async def test_upload_room_cover_permission_denied(self, mocker, mock_test_user):
        """
        测试用户无权上传封面
        - 模拟get_room_details抛出ActionForbiddenException
        - 验证异常被正确抛出
        """
        # 准备测试数据
        room_id = uuid.uuid4()
        user_id = uuid.UUID(mock_test_user['public_id'])
        mock_file = MagicMock()
        
        # Mock CRUD层方法（upload_room_cover直接调用crud_room.get）
        # 创建一个不属于当前用户的房间，触发权限检查失败
        other_user_id = uuid.uuid4()
        mock_room = create_mock_room(room_id=room_id, user_id=other_user_id)
        mock_get_room = mocker.patch(
            "app.crud.room.get",
            new_callable=AsyncMock,
            return_value=mock_room
        )
        
        # 执行并验证异常
        service = RoomService(db=MagicMock())  # ← 修改：提供mock db
        role = "REGULAR"  # ← 新增：权限参数（字符串格式）
        with pytest.raises(PermissionDeniedException):
            await service.upload_room_cover(
                room_id=room_id,
                file=mock_file,
                user_id=user_id,
                role=role  # ← 新增：传递权限参数
            )
        
        # 验证调用了crud_room.get
        mock_get_room.assert_called_once_with(db=service.db, room_id=room_id)
    
    @pytest.mark.asyncio
    async def test_upload_room_cover_with_old_cover_deletion(self, mocker, mock_test_user):
        """
        测试上传新封面时删除旧封面
        - 模拟房间已有旧封面URL
        - 验证FileHandler.delete_old_cover被调用
        """
        # 准备测试数据
        room_id = uuid.uuid4()
        user_id = uuid.UUID(mock_test_user['public_id'])
        old_cover_url = "/media/rooms/{}/cover_old.jpg".format(room_id)
        new_cover_url = "/media/rooms/{}/cover_new.jpg".format(room_id)
        
        # 创建有旧封面的房间
        mock_room = create_mock_room(room_id=room_id, user_id=user_id, cover_url=old_cover_url)
        updated_room = create_mock_room(room_id=room_id, user_id=user_id, cover_url=new_cover_url)
        
        mock_file = MagicMock()
        
        # Mock CRUD层方法（upload_room_cover直接调用crud_room.get）
        mock_get_room = mocker.patch(
            "app.crud.room.get",
            new_callable=AsyncMock,
            return_value=mock_room
        )
        
        mock_delete_cover = mocker.patch("app.core.file_handler.FileHandler.delete_old_cover")
        
        mock_save_file = mocker.patch(
            "app.core.file_handler.FileHandler.save_cover_file",
            new_callable=AsyncMock,
            return_value=new_cover_url
        )
        
        mock_update_url = mocker.patch(
            "app.crud.room.update_cover_url",
            new_callable=AsyncMock,
            return_value=updated_room
        )
        
        # 执行上传操作
        service = RoomService(db=MagicMock())  # ← 修改：提供mock db，因为upload_room_cover需要self.db
        role = "REGULAR"  # ← 新增：权限参数（字符串格式）
        result = await service.upload_room_cover(
            room_id=room_id,
            file=mock_file,
            user_id=user_id,
            role=role  # ← 新增：传递权限参数
        )
        
        # 断言返回值
        assert result == updated_room
        
        # 验证方法调用
        mock_get_room.assert_called_once_with(db=service.db, room_id=room_id)
        mock_delete_cover.assert_called_once_with(old_cover_url)
        mock_save_file.assert_called_once_with(file=mock_file, room_id=room_id)
        mock_update_url.assert_called_once()
        
        # 验证其他方法也被正确调用
        mock_save_file.assert_called_once()
        mock_update_url.assert_called_once()


