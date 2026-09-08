"""
直播间 Tab 和留言功能的 Service 层测试（学院派）

本测试文件使用 Mock 隔离测试业务逻辑，验证：
- 权限检查逻辑
- 参数校验逻辑
- 自定义异常抛出
- CRUD 层调用是否正确

测试风格：学院派 (Academic) - 使用 pytest-mock 隔离所有依赖
"""

import sys
import uuid
import pytest
from unittest.mock import MagicMock, AsyncMock, Mock

# Mock app.models.user 模块，避免导入错误
# live_core_service 是独立模块，通过JWT获取user_id，不依赖User模型
sys.modules['app.models.user'] = Mock()

from app.services.live_features_service import TabService, MessageService
from app.models.live_features import LiveRoomMessageUserRole, LiveRoomTabContentType
from app.schemas.live_features import (
    LiveRoomTabCreate,
    LiveRoomTabUpdate,
    LiveRoomMessageCreate
)
from app.exceptions import (
    TabNotFoundException,
    RoomNotFoundException,
    PermissionDeniedException,
    InvalidParameterException
)


class TestTabService:
    """TabService 业务逻辑测试（学院派）"""

    # ==================== list_tabs_for_admin 测试 ====================

    @pytest.mark.asyncio
    async def test_list_tabs_for_admin_success(self, mocker):
        """测试管理员成功获取房间所有Tab"""
        # 1. 准备 (Arrange)
        mock_db = MagicMock()
        user_id = uuid.uuid4()
        user_role = LiveRoomMessageUserRole.ADMIN
        role = "ADMIN"  # ← 新增：权限参数（字符串格式）
        
        room_id = uuid.uuid4()
        mock_room = MagicMock()
        mock_tab1 = MagicMock()
        mock_tab2 = MagicMock()
        
        # Mock CRUD 函数
        mock_get_room = mocker.patch(
            "app.crud.room.get",
            new_callable=AsyncMock,
            return_value=mock_room
        )
        mock_get_all_tabs = mocker.patch(
            "app.crud.live_features.get_all_by_room_id",
            new_callable=AsyncMock,
            return_value=([mock_tab1, mock_tab2], 2)
        )
        
        # 2. 执行 (Act)
        service = TabService(mock_db)
        tabs, total = await service.list_tabs_for_admin(
            user_id=user_id, 
            user_role=user_role, 
            room_id=room_id,
            role=role  # ← 新增：传递权限参数
        )
        
        # 3. 断言 (Assert)
        assert tabs == [mock_tab1, mock_tab2]
        assert total == 2
        mock_get_room.assert_called_once_with(mock_db, room_id)
        mock_get_all_tabs.assert_called_once_with(mock_db, room_id, skip=0, limit=100)

    @pytest.mark.asyncio
    async def test_list_tabs_for_admin_permission_denied(self, mocker):
        """测试Regular用户作为非房间创建者权限被拒绝"""
        # 1. 准备 (Arrange)
        mock_db = MagicMock()
        user_id = uuid.uuid4()
        user_role = LiveRoomMessageUserRole.REGULAR
        role = "REGULAR"  # ← 新增：权限参数（字符串格式）
        
        room_id = uuid.uuid4()
        mock_room = MagicMock()
        # ← 修改：设置房间创建者为其他用户（非当前用户）
        other_user_id = uuid.uuid4()
        mock_room.user_id = other_user_id
        mock_room.id = room_id
        
        # Mock crud_room.get（权限检查需要room对象）
        mock_get_room = mocker.patch(
            "app.crud.room.get",
            new_callable=AsyncMock,
            return_value=mock_room
        )
        
        # 2. 执行 & 断言 (Act & Assert)
        service = TabService(mock_db)
        with pytest.raises(PermissionDeniedException):
            await service.list_tabs_for_admin(
                user_id=user_id, 
                user_role=user_role, 
                room_id=room_id,
                role=role  # ← 新增：传递权限参数
            )
        
        # 验证 crud_room.get 被调用（权限检查需要room对象）
        mock_get_room.assert_called_once_with(mock_db, room_id)

    @pytest.mark.asyncio
    async def test_list_tabs_for_admin_room_not_found(self, mocker):
        """测试房间不存在时抛出异常"""
        # 1. 准备 (Arrange)
        mock_db = MagicMock()
        user_id = uuid.uuid4()
        user_role = LiveRoomMessageUserRole.ADMIN
        role = "ADMIN"  # ← 新增：权限参数（字符串格式）
        
        room_id = uuid.uuid4()
        
        # Mock crud_room.get 返回 None
        mock_get_room = mocker.patch(
            "app.crud.room.get",
            new_callable=AsyncMock,
            return_value=None
        )
        
        # 2. 执行 & 断言 (Act & Assert)
        service = TabService(mock_db)
        with pytest.raises(RoomNotFoundException):
            await service.list_tabs_for_admin(
                user_id=user_id, 
                user_role=user_role, 
                room_id=room_id,
                role=role  # ← 新增：传递权限参数
            )
        
        mock_get_room.assert_called_once_with(mock_db, room_id)

    # ==================== get_active_tabs_for_room 测试 ====================

    @pytest.mark.asyncio
    async def test_get_active_tabs_for_room_success(self, mocker):
        """测试成功获取房间激活的Tab"""
        # 1. 准备 (Arrange)
        mock_db = MagicMock()
        room_id = uuid.uuid4()
        mock_room = MagicMock()
        mock_tab1 = MagicMock()
        mock_tab2 = MagicMock()
        
        # Mock CRUD 函数
        mock_get_room = mocker.patch(
            "app.crud.room.get",
            new_callable=AsyncMock,
            return_value=mock_room
        )
        mock_get_active_tabs = mocker.patch(
            "app.crud.live_features.get_active_by_room_id",
            new_callable=AsyncMock,
            return_value=[mock_tab1, mock_tab2]
        )
        
        # 2. 执行 (Act)
        service = TabService(mock_db)
        tabs = await service.get_active_tabs_for_room(room_id=room_id)
        
        # 3. 断言 (Assert)
        assert tabs == [mock_tab1, mock_tab2]
        mock_get_room.assert_called_once_with(mock_db, room_id)
        mock_get_active_tabs.assert_called_once_with(mock_db, room_id)

    @pytest.mark.asyncio
    async def test_get_active_tabs_for_room_room_not_found(self, mocker):
        """测试房间不存在时抛出异常"""
        # 1. 准备 (Arrange)
        mock_db = MagicMock()
        room_id = uuid.uuid4()
        
        # Mock crud_room.get 返回 None
        mock_get_room = mocker.patch(
            "app.crud.room.get",
            new_callable=AsyncMock,
            return_value=None
        )
        
        # 2. 执行 & 断言 (Act & Assert)
        service = TabService(mock_db)
        with pytest.raises(RoomNotFoundException):
            await service.get_active_tabs_for_room(room_id=room_id)
        
        mock_get_room.assert_called_once_with(mock_db, room_id)

    # ==================== create_tab 测试 ====================

    @pytest.mark.asyncio
    async def test_create_tab_success(self, mocker):
        """测试成功创建Tab"""
        # 1. 准备 (Arrange)
        mock_db = MagicMock()
        user_id = uuid.uuid4()
        user_role = LiveRoomMessageUserRole.ADMIN
        
        room_id = uuid.uuid4()
        mock_room = MagicMock()
        
        obj_in = LiveRoomTabCreate(
            tab_key="test_tab",
            title="测试Tab",
            content_type=LiveRoomTabContentType.TEXT,
            text_content="测试内容",
            sort_order=0,
            is_active=True
        )
        
        mock_new_tab = MagicMock()
        mock_new_tab.id = uuid.uuid4()
        
        # Mock CRUD 函数
        mock_get_room = mocker.patch(
            "app.crud.room.get",
            new_callable=AsyncMock,
            return_value=mock_room
        )
        mock_create_tab = mocker.patch(
            "app.crud.live_features.create_tab",
            new_callable=AsyncMock,
            return_value=mock_new_tab
        )
        
        # 2. 执行 (Act)
        service = TabService(mock_db)
        # ← 新增：设置Mock room的is_private属性（公开房间）
        mock_room.is_private = False
        role = "ADMIN"  # ← 新增：权限参数（字符串格式）
        result = await service.create_tab(user_id=user_id, user_role=user_role, room_id=room_id, obj_in=obj_in, role=role)
        
        # 3. 断言 (Assert)
        assert result == mock_new_tab
        mock_get_room.assert_called_once_with(mock_db, room_id)
        mock_create_tab.assert_called_once_with(mock_db, obj_in, room_id)

    @pytest.mark.asyncio
    async def test_create_tab_permission_denied(self, mocker):
        """测试Regular用户作为非房间创建者创建Tab被拒绝"""
        # 1. 准备 (Arrange)
        mock_db = MagicMock()
        user_id = uuid.uuid4()
        user_role = LiveRoomMessageUserRole.REGULAR
        
        room_id = uuid.uuid4()
        mock_room = MagicMock()
        # ← 修改：设置房间创建者为其他用户（非当前用户）
        other_user_id = uuid.uuid4()
        mock_room.user_id = other_user_id
        mock_room.id = room_id
        
        obj_in = LiveRoomTabCreate(
            tab_key="test_tab",
            title="测试Tab",
            content_type=LiveRoomTabContentType.TEXT,
            text_content="测试内容",
            sort_order=0,
            is_active=True
        )
        
        # Mock crud_room.get
        mock_get_room = mocker.patch(
            "app.crud.room.get",
            new_callable=AsyncMock,
            return_value=mock_room
        )
        
        # 2. 执行 & 断言 (Act & Assert)
        service = TabService(mock_db)
        role = "REGULAR"  # ← 新增：权限参数（字符串格式）
        with pytest.raises(PermissionDeniedException):
            await service.create_tab(
                user_id=user_id, 
                user_role=user_role, 
                room_id=room_id, 
                obj_in=obj_in,
                role=role  # ← 新增：传递权限参数
            )
        
        mock_get_room.assert_called_once_with(mock_db, room_id)

    @pytest.mark.asyncio
    async def test_create_tab_room_not_found(self, mocker):
        """测试房间不存在时抛出异常"""
        # 1. 准备 (Arrange)
        mock_db = MagicMock()
        user_id = uuid.uuid4()
        user_role = LiveRoomMessageUserRole.ADMIN
        
        room_id = uuid.uuid4()
        obj_in = LiveRoomTabCreate(
            tab_key="test_tab",
            title="测试Tab",
            content_type=LiveRoomTabContentType.TEXT,
            text_content="测试内容",
            sort_order=0,
            is_active=True
        )
        
        # Mock crud_room.get 返回 None
        mock_get_room = mocker.patch(
            "app.crud.room.get",
            new_callable=AsyncMock,
            return_value=None
        )
        
        # 2. 执行 & 断言 (Act & Assert)
        service = TabService(mock_db)
        role = "ADMIN"  # ← 新增：权限参数（字符串格式）
        with pytest.raises(RoomNotFoundException):
            await service.create_tab(
                user_id=user_id, 
                user_role=user_role, 
                room_id=room_id, 
                obj_in=obj_in,
                role=role  # ← 新增：传递权限参数
            )
        
        mock_get_room.assert_called_once_with(mock_db, room_id)

    @pytest.mark.asyncio
    async def test_create_tab_invalid_content_type_text(self, mocker):
        """测试content_type=TEXT但text_content为空时抛出异常"""
        # 1. 准备 (Arrange)
        mock_db = MagicMock()
        user_id = uuid.uuid4()
        user_role = LiveRoomMessageUserRole.ADMIN
        
        room_id = uuid.uuid4()
        mock_room = MagicMock()
        
        obj_in = LiveRoomTabCreate(
            tab_key="test_tab",
            title="测试Tab",
            content_type=LiveRoomTabContentType.TEXT,
            text_content=None,
            sort_order=0,
            is_active=True
        )
        
        # Mock crud_room.get
        mock_get_room = mocker.patch(
            "app.crud.room.get",
            new_callable=AsyncMock,
            return_value=mock_room
        )
        
        # 2. 执行 & 断言 (Act & Assert)
        service = TabService(mock_db)
        role = "ADMIN"  # ← 新增：权限参数（字符串格式）
        with pytest.raises(InvalidParameterException) as exc_info:
            await service.create_tab(
                user_id=user_id, 
                user_role=user_role, 
                room_id=room_id, 
                obj_in=obj_in,
                role=role  # ← 新增：传递权限参数
            )
        
        assert "text_content 不能为空" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_tab_invalid_content_type_image(self, mocker):
        """测试content_type=IMAGE但image_url为空时抛出异常"""
        # 1. 准备 (Arrange)
        mock_db = MagicMock()
        user_id = uuid.uuid4()
        user_role = LiveRoomMessageUserRole.ADMIN
        
        room_id = uuid.uuid4()
        mock_room = MagicMock()
        
        obj_in = LiveRoomTabCreate(
            tab_key="test_tab",
            title="测试Tab",
            content_type=LiveRoomTabContentType.IMAGE,
            image_url=None,
            sort_order=0,
            is_active=True
        )
        
        # Mock crud_room.get
        mock_get_room = mocker.patch(
            "app.crud.room.get",
            new_callable=AsyncMock,
            return_value=mock_room
        )
        
        # 2. 执行 & 断言 (Act & Assert)
        service = TabService(mock_db)
        role = "ADMIN"  # ← 新增：权限参数（字符串格式）
        with pytest.raises(InvalidParameterException) as exc_info:
            await service.create_tab(
                user_id=user_id, 
                user_role=user_role, 
                room_id=room_id, 
                obj_in=obj_in,
                role=role  # ← 新增：传递权限参数
            )
        
        assert "image_url 不能为空" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_tab_invalid_content_type_mixed(self, mocker):
        """测试content_type=MIXED但两个内容都为空时抛出异常"""
        # 1. 准备 (Arrange)
        mock_db = MagicMock()
        user_id = uuid.uuid4()
        user_role = LiveRoomMessageUserRole.ADMIN
        
        room_id = uuid.uuid4()
        mock_room = MagicMock()
        
        obj_in = LiveRoomTabCreate(
            tab_key="test_tab",
            title="测试Tab",
            content_type=LiveRoomTabContentType.MIXED,
            text_content=None,
            image_url=None,
            sort_order=0,
            is_active=True
        )
        
        # Mock crud_room.get
        mock_get_room = mocker.patch(
            "app.crud.room.get",
            new_callable=AsyncMock,
            return_value=mock_room
        )
        
        # 2. 执行 & 断言 (Act & Assert)
        service = TabService(mock_db)
        role = "ADMIN"  # ← 新增：权限参数（字符串格式）
        with pytest.raises(InvalidParameterException) as exc_info:
            await service.create_tab(
                user_id=user_id, 
                user_role=user_role, 
                room_id=room_id, 
                obj_in=obj_in,
                role=role  # ← 新增：传递权限参数
            )
        
        assert "至少需要一个" in str(exc_info.value)

    # ==================== update_tab 测试 ====================

    @pytest.mark.asyncio
    async def test_update_tab_success(self, mocker):
        """测试成功更新Tab"""
        # 1. 准备 (Arrange)
        mock_db = MagicMock()
        user_id = uuid.uuid4()
        user_role = LiveRoomMessageUserRole.ADMIN
        
        tab_id = uuid.uuid4()
        room_id = uuid.uuid4()
        mock_db_tab = MagicMock()
        mock_db_tab.content_type = LiveRoomTabContentType.TEXT
        mock_db_tab.text_content = "原内容"
        mock_db_tab.room_id = room_id  # ← 新增：设置room_id
        
        # ← 新增：设置room对象（Admin可以管理所有房间）
        mock_room = MagicMock()
        mock_room.user_id = user_id
        mock_room.id = room_id
        
        obj_in = LiveRoomTabUpdate(title="新标题")
        
        mock_updated_tab = MagicMock()
        
        # Mock CRUD 函数
        mock_get_tab = mocker.patch(
            "app.crud.live_features.get_tab",
            new_callable=AsyncMock,
            return_value=mock_db_tab
        )
        mock_get_room = mocker.patch(
            "app.crud.room.get",
            new_callable=AsyncMock,
            return_value=mock_room
        )
        mock_update_tab = mocker.patch(
            "app.crud.live_features.update_tab",
            new_callable=AsyncMock,
            return_value=mock_updated_tab
        )
        
        # 2. 执行 (Act)
        service = TabService(mock_db)
        role = "ADMIN"  # ← 新增：权限参数（字符串格式）
        result = await service.update_tab(
            user_id=user_id, 
            user_role=user_role, 
            tab_id=tab_id, 
            obj_in=obj_in,
            role=role  # ← 新增：传递权限参数
        )
        
        # 3. 断言 (Assert)
        assert result == mock_updated_tab
        mock_get_tab.assert_called_once_with(mock_db, tab_id)
        mock_get_room.assert_called_once_with(mock_db, room_id)
        mock_update_tab.assert_called_once_with(mock_db, mock_db_tab, obj_in)

    @pytest.mark.asyncio
    async def test_update_tab_permission_denied(self, mocker):
        """测试Regular用户作为非房间创建者更新Tab被拒绝"""
        # 1. 准备 (Arrange)
        mock_db = MagicMock()
        user_id = uuid.uuid4()
        user_role = LiveRoomMessageUserRole.REGULAR
        
        tab_id = uuid.uuid4()
        room_id = uuid.uuid4()
        mock_db_tab = MagicMock()
        mock_db_tab.room_id = room_id
        
        # ← 修改：设置房间创建者为其他用户（非当前用户）
        mock_room = MagicMock()
        other_user_id = uuid.uuid4()
        mock_room.user_id = other_user_id
        mock_room.id = room_id
        
        obj_in = LiveRoomTabUpdate(title="新标题")
        
        # Mock CRUD 函数
        mock_get_tab = mocker.patch(
            "app.crud.live_features.get_tab",
            new_callable=AsyncMock,
            return_value=mock_db_tab
        )
        mock_get_room = mocker.patch(
            "app.crud.room.get",
            new_callable=AsyncMock,
            return_value=mock_room
        )
        
        # 2. 执行 & 断言 (Act & Assert)
        service = TabService(mock_db)
        role = "REGULAR"  # ← 新增：权限参数（字符串格式）
        with pytest.raises(PermissionDeniedException):
            await service.update_tab(
                user_id=user_id, 
                user_role=user_role, 
                tab_id=tab_id, 
                obj_in=obj_in,
                role=role  # ← 新增：传递权限参数
            )
        
        mock_get_tab.assert_called_once_with(mock_db, tab_id)
        mock_get_room.assert_called_once_with(mock_db, room_id)

    @pytest.mark.asyncio
    async def test_update_tab_not_found(self, mocker):
        """测试Tab不存在时抛出异常"""
        # 1. 准备 (Arrange)
        mock_db = MagicMock()
        user_id = uuid.uuid4()
        user_role = LiveRoomMessageUserRole.ADMIN
        
        tab_id = uuid.uuid4()
        obj_in = LiveRoomTabUpdate(title="新标题")
        
        # Mock crud_live_features.get_tab 返回 None
        mock_get_tab = mocker.patch(
            "app.crud.live_features.get_tab",
            new_callable=AsyncMock,
            return_value=None
        )
        
        # 2. 执行 & 断言 (Act & Assert)
        service = TabService(mock_db)
        role = "ADMIN"  # ← 新增：权限参数（字符串格式）
        with pytest.raises(TabNotFoundException):
            await service.update_tab(
                user_id=user_id, 
                user_role=user_role, 
                tab_id=tab_id, 
                obj_in=obj_in,
                role=role  # ← 新增：传递权限参数
            )
        
        mock_get_tab.assert_called_once_with(mock_db, tab_id)

    @pytest.mark.asyncio
    async def test_update_tab_invalid_content_type_validation(self, mocker):
        """测试更新content_type时的参数校验"""
        # 1. 准备 (Arrange)
        mock_db = MagicMock()
        user_id = uuid.uuid4()
        user_role = LiveRoomMessageUserRole.ADMIN
        
        tab_id = uuid.uuid4()
        room_id = uuid.uuid4()
        mock_db_tab = MagicMock()
        mock_db_tab.text_content = None
        mock_db_tab.image_url = None
        mock_db_tab.room_id = room_id  # ← 新增：设置room_id
        
        # ← 新增：设置room对象（Admin可以管理所有房间）
        mock_room = MagicMock()
        mock_room.user_id = user_id
        mock_room.id = room_id
        
        obj_in = LiveRoomTabUpdate(content_type=LiveRoomTabContentType.TEXT)
        
        # Mock CRUD 函数
        mock_get_tab = mocker.patch(
            "app.crud.live_features.get_tab",
            new_callable=AsyncMock,
            return_value=mock_db_tab
        )
        mock_get_room = mocker.patch(
            "app.crud.room.get",
            new_callable=AsyncMock,
            return_value=mock_room
        )
        
        # 2. 执行 & 断言 (Act & Assert)
        service = TabService(mock_db)
        role = "ADMIN"  # ← 新增：权限参数（字符串格式）
        with pytest.raises(InvalidParameterException):
            await service.update_tab(user_id=user_id, user_role=user_role, tab_id=tab_id, obj_in=obj_in, role=role)
        
        mock_get_tab.assert_called_once_with(mock_db, tab_id)
        mock_get_room.assert_called_once_with(mock_db, room_id)

    # ==================== delete_tab 测试 ====================

    @pytest.mark.asyncio
    async def test_delete_tab_success(self, mocker):
        """测试成功删除Tab"""
        # 1. 准备 (Arrange)
        mock_db = MagicMock()
        user_id = uuid.uuid4()
        user_role = LiveRoomMessageUserRole.ADMIN
        
        tab_id = uuid.uuid4()
        room_id = uuid.uuid4()
        mock_db_tab = MagicMock()
        mock_db_tab.room_id = room_id  # ← 新增：设置room_id
        
        # ← 新增：设置room对象（Admin可以管理所有房间）
        mock_room = MagicMock()
        mock_room.user_id = user_id
        mock_room.id = room_id
        
        mock_deleted_tab = MagicMock()
        
        # Mock CRUD 函数
        mock_get_tab = mocker.patch(
            "app.crud.live_features.get_tab",
            new_callable=AsyncMock,
            return_value=mock_db_tab
        )
        mock_get_room = mocker.patch(
            "app.crud.room.get",
            new_callable=AsyncMock,
            return_value=mock_room
        )
        mock_remove_tab = mocker.patch(
            "app.crud.live_features.remove_tab",
            new_callable=AsyncMock,
            return_value=mock_deleted_tab
        )
        
        # 2. 执行 (Act)
        service = TabService(mock_db)
        role = "ADMIN"  # ← 新增：权限参数（字符串格式）
        result = await service.delete_tab(
            user_id=user_id, 
            user_role=user_role, 
            tab_id=tab_id,
            role=role  # ← 新增：传递权限参数
        )
        
        # 3. 断言 (Assert)
        assert result == mock_deleted_tab
        mock_get_tab.assert_called_once_with(mock_db, tab_id)
        mock_get_room.assert_called_once_with(mock_db, room_id)
        mock_remove_tab.assert_called_once_with(mock_db, mock_db_tab)

    @pytest.mark.asyncio
    async def test_delete_tab_permission_denied(self, mocker):
        """测试Regular用户作为非房间创建者删除Tab被拒绝"""
        # 1. 准备 (Arrange)
        mock_db = MagicMock()
        user_id = uuid.uuid4()
        user_role = LiveRoomMessageUserRole.REGULAR
        
        tab_id = uuid.uuid4()
        room_id = uuid.uuid4()
        mock_db_tab = MagicMock()
        mock_db_tab.room_id = room_id
        
        # ← 修改：设置房间创建者为其他用户（非当前用户）
        mock_room = MagicMock()
        other_user_id = uuid.uuid4()
        mock_room.user_id = other_user_id
        mock_room.id = room_id
        
        # Mock CRUD 函数
        mock_get_tab = mocker.patch(
            "app.crud.live_features.get_tab",
            new_callable=AsyncMock,
            return_value=mock_db_tab
        )
        mock_get_room = mocker.patch(
            "app.crud.room.get",
            new_callable=AsyncMock,
            return_value=mock_room
        )
        
        # 2. 执行 & 断言 (Act & Assert)
        service = TabService(mock_db)
        role = "REGULAR"  # ← 新增：权限参数（字符串格式）
        with pytest.raises(PermissionDeniedException):
            await service.delete_tab(user_id=user_id, user_role=user_role, tab_id=tab_id, role=role)
        
        mock_get_tab.assert_called_once_with(mock_db, tab_id)
        mock_get_room.assert_called_once_with(mock_db, room_id)

    @pytest.mark.asyncio
    async def test_delete_tab_not_found(self, mocker):
        """测试Tab不存在时抛出异常"""
        # 1. 准备 (Arrange)
        mock_db = MagicMock()
        user_id = uuid.uuid4()
        user_role = LiveRoomMessageUserRole.ADMIN
        
        tab_id = uuid.uuid4()
        
        # Mock crud_live_features.get_tab 返回 None
        mock_get_tab = mocker.patch(
            "app.crud.live_features.get_tab",
            new_callable=AsyncMock,
            return_value=None
        )
        
        # 2. 执行 & 断言 (Act & Assert)
        service = TabService(mock_db)
        role = "ADMIN"  # ← 新增：权限参数（字符串格式）
        with pytest.raises(TabNotFoundException):
            await service.delete_tab(
                user_id=user_id, 
                user_role=user_role, 
                tab_id=tab_id,
                role=role  # ← 新增：传递权限参数
            )
        
        mock_get_tab.assert_called_once_with(mock_db, tab_id)

    # ==================== Regular用户作为房间创建者管理Tab的测试 ====================

    @pytest.mark.asyncio
    async def test_list_tabs_for_admin_success_regular_owner(self, mocker):
        """测试Regular用户作为房间创建者成功获取房间所有Tab"""
        # 1. 准备 (Arrange)
        mock_db = MagicMock()
        user_id = uuid.uuid4()
        user_role = LiveRoomMessageUserRole.REGULAR
        role = "REGULAR"
        
        room_id = uuid.uuid4()
        mock_room = MagicMock()
        # ← 新增：设置房间创建者为当前用户
        mock_room.user_id = user_id
        mock_room.id = room_id
        
        mock_tab1 = MagicMock()
        mock_tab2 = MagicMock()
        
        # Mock CRUD 函数
        mock_get_room = mocker.patch(
            "app.crud.room.get",
            new_callable=AsyncMock,
            return_value=mock_room
        )
        mock_get_all_tabs = mocker.patch(
            "app.crud.live_features.get_all_by_room_id",
            new_callable=AsyncMock,
            return_value=([mock_tab1, mock_tab2], 2)
        )
        
        # 2. 执行 (Act)
        service = TabService(mock_db)
        tabs, total = await service.list_tabs_for_admin(
            user_id=user_id, 
            user_role=user_role, 
            room_id=room_id,
            role=role
        )
        
        # 3. 断言 (Assert)
        assert tabs == [mock_tab1, mock_tab2]
        assert total == 2
        mock_get_room.assert_called_once_with(mock_db, room_id)
        mock_get_all_tabs.assert_called_once_with(mock_db, room_id, skip=0, limit=100)

    @pytest.mark.asyncio
    async def test_create_tab_success_regular_owner(self, mocker):
        """测试Regular用户作为房间创建者成功创建Tab"""
        # 1. 准备 (Arrange)
        mock_db = MagicMock()
        user_id = uuid.uuid4()
        user_role = LiveRoomMessageUserRole.REGULAR
        
        room_id = uuid.uuid4()
        mock_room = MagicMock()
        # ← 新增：设置房间创建者为当前用户
        mock_room.user_id = user_id
        mock_room.id = room_id
        
        obj_in = LiveRoomTabCreate(
            tab_key="test_tab",
            title="测试Tab",
            content_type=LiveRoomTabContentType.TEXT,
            text_content="测试内容",
            sort_order=0,
            is_active=True
        )
        
        mock_new_tab = MagicMock()
        mock_new_tab.id = uuid.uuid4()
        
        # Mock CRUD 函数
        mock_get_room = mocker.patch(
            "app.crud.room.get",
            new_callable=AsyncMock,
            return_value=mock_room
        )
        mock_create_tab = mocker.patch(
            "app.crud.live_features.create_tab",
            new_callable=AsyncMock,
            return_value=mock_new_tab
        )
        
        # 2. 执行 (Act)
        service = TabService(mock_db)
        role = "REGULAR"
        result = await service.create_tab(user_id=user_id, user_role=user_role, room_id=room_id, obj_in=obj_in, role=role)
        
        # 3. 断言 (Assert)
        assert result == mock_new_tab
        mock_get_room.assert_called_once_with(mock_db, room_id)
        mock_create_tab.assert_called_once_with(mock_db, obj_in, room_id)

    @pytest.mark.asyncio
    async def test_update_tab_success_regular_owner(self, mocker):
        """测试Regular用户作为房间创建者成功更新Tab"""
        # 1. 准备 (Arrange)
        mock_db = MagicMock()
        user_id = uuid.uuid4()
        user_role = LiveRoomMessageUserRole.REGULAR
        
        tab_id = uuid.uuid4()
        room_id = uuid.uuid4()
        mock_db_tab = MagicMock()
        mock_db_tab.content_type = LiveRoomTabContentType.TEXT
        mock_db_tab.text_content = "原内容"
        mock_db_tab.room_id = room_id
        
        # ← 新增：设置房间创建者为当前用户
        mock_room = MagicMock()
        mock_room.user_id = user_id
        mock_room.id = room_id
        
        obj_in = LiveRoomTabUpdate(title="新标题")
        
        mock_updated_tab = MagicMock()
        
        # Mock CRUD 函数
        mock_get_tab = mocker.patch(
            "app.crud.live_features.get_tab",
            new_callable=AsyncMock,
            return_value=mock_db_tab
        )
        mock_get_room = mocker.patch(
            "app.crud.room.get",
            new_callable=AsyncMock,
            return_value=mock_room
        )
        mock_update_tab = mocker.patch(
            "app.crud.live_features.update_tab",
            new_callable=AsyncMock,
            return_value=mock_updated_tab
        )
        
        # 2. 执行 (Act)
        service = TabService(mock_db)
        role = "REGULAR"
        result = await service.update_tab(
            user_id=user_id, 
            user_role=user_role, 
            tab_id=tab_id, 
            obj_in=obj_in,
            role=role
        )
        
        # 3. 断言 (Assert)
        assert result == mock_updated_tab
        mock_get_tab.assert_called_once_with(mock_db, tab_id)
        mock_get_room.assert_called_once_with(mock_db, room_id)
        mock_update_tab.assert_called_once_with(mock_db, mock_db_tab, obj_in)

    @pytest.mark.asyncio
    async def test_delete_tab_success_regular_owner(self, mocker):
        """测试Regular用户作为房间创建者成功删除Tab"""
        # 1. 准备 (Arrange)
        mock_db = MagicMock()
        user_id = uuid.uuid4()
        user_role = LiveRoomMessageUserRole.REGULAR
        
        tab_id = uuid.uuid4()
        room_id = uuid.uuid4()
        mock_db_tab = MagicMock()
        mock_db_tab.room_id = room_id
        
        # ← 新增：设置房间创建者为当前用户
        mock_room = MagicMock()
        mock_room.user_id = user_id
        mock_room.id = room_id
        
        mock_deleted_tab = MagicMock()
        
        # Mock CRUD 函数
        mock_get_tab = mocker.patch(
            "app.crud.live_features.get_tab",
            new_callable=AsyncMock,
            return_value=mock_db_tab
        )
        mock_get_room = mocker.patch(
            "app.crud.room.get",
            new_callable=AsyncMock,
            return_value=mock_room
        )
        mock_remove_tab = mocker.patch(
            "app.crud.live_features.remove_tab",
            new_callable=AsyncMock,
            return_value=mock_deleted_tab
        )
        
        # 2. 执行 (Act)
        service = TabService(mock_db)
        role = "REGULAR"
        result = await service.delete_tab(
            user_id=user_id, 
            user_role=user_role, 
            tab_id=tab_id,
            role=role
        )
        
        # 3. 断言 (Assert)
        assert result == mock_deleted_tab
        mock_get_tab.assert_called_once_with(mock_db, tab_id)
        mock_get_room.assert_called_once_with(mock_db, room_id)
        mock_remove_tab.assert_called_once_with(mock_db, mock_db_tab)

    def test_tab_image_upload_permission_regular_owner(self):
        """Tab 图片上传复用 _check_tab_management_permission：房主允许"""
        user_id = uuid.uuid4()
        mock_room = MagicMock()
        mock_room.user_id = user_id
        service = TabService(MagicMock())
        service._check_tab_management_permission(mock_room, user_id, "REGULAR")

    def test_tab_image_upload_permission_non_owner_denied(self):
        """Tab 图片上传：非房主 REGULAR 拒绝"""
        mock_room = MagicMock()
        mock_room.user_id = uuid.uuid4()
        service = TabService(MagicMock())
        with pytest.raises(PermissionDeniedException):
            service._check_tab_management_permission(mock_room, uuid.uuid4(), "REGULAR")


class TestMessageService:
    """MessageService 业务逻辑测试（学院派）"""

    # ==================== create_message 测试 ====================

    @pytest.mark.asyncio
    async def test_create_message_success_admin(self, mocker):
        """测试管理员成功发送包含URL的留言"""
        # 1. 准备 (Arrange)
        mock_db = MagicMock()
        user_id = uuid.uuid4()
        user_role = LiveRoomMessageUserRole.ADMIN
        
        room_id = uuid.uuid4()
        mock_room = MagicMock()
        
        obj_in = LiveRoomMessageCreate(content="测试留言 https://example.com")
        
        mock_new_message = MagicMock()
        mock_new_message.id = uuid.uuid4()
        
        # Mock CRUD 函数
        mock_get_room = mocker.patch(
            "app.crud.room.get",
            new_callable=AsyncMock,
            return_value=mock_room
        )
        mock_create_message = mocker.patch(
            "app.crud.live_features.create_message",
            new_callable=AsyncMock,
            return_value=mock_new_message
        )
        
        # 2. 执行 (Act)
        service = MessageService(mock_db)
        # ← 新增：设置Mock room的is_private属性（公开房间）
        mock_room.is_private = False
        role = "ADMIN"  # ← 新增：权限参数（字符串格式）
        result = await service.create_message(user_id=user_id, user_role=user_role, room_id=room_id, obj_in=obj_in, role=role)
        
        # 3. 断言 (Assert)
        assert result == mock_new_message
        mock_get_room.assert_called_once_with(mock_db, room_id)
        mock_create_message.assert_called_once()
        
        # [关键] 验证传递给 CRUD 的参数是 LiveRoomMessageCreateInternal
        call_args = mock_create_message.call_args
        internal_obj = call_args[0][1]  # 第二个参数
        assert internal_obj.room_id == room_id
        assert internal_obj.user_id == user_id
        assert internal_obj.user_role == user_role
        assert internal_obj.content == obj_in.content

    @pytest.mark.asyncio
    async def test_create_message_success_regular_user_without_url(self, mocker):
        """测试普通用户成功发送不包含URL的留言"""
        # 1. 准备 (Arrange)
        mock_db = MagicMock()
        user_id = uuid.uuid4()
        user_role = LiveRoomMessageUserRole.REGULAR
        
        room_id = uuid.uuid4()
        mock_room = MagicMock()
        
        obj_in = LiveRoomMessageCreate(content="普通留言")
        
        mock_new_message = MagicMock()
        
        # Mock CRUD 函数
        mock_get_room = mocker.patch(
            "app.crud.room.get",
            new_callable=AsyncMock,
            return_value=mock_room
        )
        mock_create_message = mocker.patch(
            "app.crud.live_features.create_message",
            new_callable=AsyncMock,
            return_value=mock_new_message
        )
        
        # 2. 执行 (Act)
        service = MessageService(mock_db)
        # ← 新增：设置Mock room的is_private属性（公开房间）
        mock_room.is_private = False
        role = "REGULAR"  # ← 新增：权限参数（字符串格式）
        result = await service.create_message(user_id=user_id, user_role=user_role, room_id=room_id, obj_in=obj_in, role=role)
        
        # 3. 断言 (Assert)
        assert result == mock_new_message
        mock_get_room.assert_called_once_with(mock_db, room_id)
        mock_create_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_message_regular_user_with_url_raises_exception(self, mocker):
        """测试Regular用户作为非房间创建者发送包含URL的留言被拒绝"""
        # 1. 准备 (Arrange)
        mock_db = MagicMock()
        user_id = uuid.uuid4()
        user_role = LiveRoomMessageUserRole.REGULAR
        
        room_id = uuid.uuid4()
        mock_room = MagicMock()
        # ← 修改：设置房间创建者为其他用户（非当前用户）
        other_user_id = uuid.uuid4()
        mock_room.user_id = other_user_id
        mock_room.id = room_id
        mock_room.is_private = False
        
        obj_in = LiveRoomMessageCreate(content="包含URL https://evil.com")
        
        # Mock crud_room.get
        mock_get_room = mocker.patch(
            "app.crud.room.get",
            new_callable=AsyncMock,
            return_value=mock_room
        )
        
        # 2. 执行 & 断言 (Act & Assert)
        service = MessageService(mock_db)
        role = "REGULAR"  # ← 新增：权限参数（字符串格式）
        with pytest.raises(InvalidParameterException) as exc_info:
            await service.create_message(
                user_id=user_id, 
                user_role=user_role, 
                room_id=room_id, 
                obj_in=obj_in,
                role=role  # ← 新增：传递权限参数
            )
        
        # [关键] 验证异常的 code 属性为 4004
        assert exc_info.value.code == 4004
        assert "URL" in exc_info.value.message
        
        mock_get_room.assert_called_once_with(mock_db, room_id)

    @pytest.mark.asyncio
    async def test_create_message_room_not_found(self, mocker):
        """测试房间不存在时抛出异常"""
        # 1. 准备 (Arrange)
        mock_db = MagicMock()
        user_id = uuid.uuid4()
        user_role = LiveRoomMessageUserRole.REGULAR
        
        room_id = uuid.uuid4()
        obj_in = LiveRoomMessageCreate(content="测试留言")
        
        # Mock crud_room.get 返回 None
        mock_get_room = mocker.patch(
            "app.crud.room.get",
            new_callable=AsyncMock,
            return_value=None
        )
        
        # 2. 执行 & 断言 (Act & Assert)
        service = MessageService(mock_db)
        role = "REGULAR"  # ← 新增：权限参数（字符串格式）
        with pytest.raises(RoomNotFoundException):
            await service.create_message(user_id=user_id, user_role=user_role, room_id=room_id, obj_in=obj_in, role=role)
        
        mock_get_room.assert_called_once_with(mock_db, room_id)

    @pytest.mark.asyncio
    async def test_create_message_success_regular_owner_with_url(self, mocker):
        """测试Regular用户作为房间创建者成功发送包含URL的留言"""
        # 1. 准备 (Arrange)
        mock_db = MagicMock()
        user_id = uuid.uuid4()
        user_role = LiveRoomMessageUserRole.REGULAR
        
        room_id = uuid.uuid4()
        mock_room = MagicMock()
        # ← 新增：设置房间创建者为当前用户
        mock_room.user_id = user_id
        mock_room.id = room_id
        mock_room.is_private = False
        
        obj_in = LiveRoomMessageCreate(content="包含URL https://example.com")
        
        mock_new_message = MagicMock()
        mock_new_message.id = uuid.uuid4()
        
        # Mock CRUD 函数
        mock_get_room = mocker.patch(
            "app.crud.room.get",
            new_callable=AsyncMock,
            return_value=mock_room
        )
        mock_create_message = mocker.patch(
            "app.crud.live_features.create_message",
            new_callable=AsyncMock,
            return_value=mock_new_message
        )
        
        # 2. 执行 (Act)
        service = MessageService(mock_db)
        role = "REGULAR"
        result = await service.create_message(user_id=user_id, user_role=user_role, room_id=room_id, obj_in=obj_in, role=role)
        
        # 3. 断言 (Assert)
        assert result == mock_new_message
        mock_get_room.assert_called_once_with(mock_db, room_id)
        mock_create_message.assert_called_once()
        
        # [关键] 验证传递给 CRUD 的参数是 LiveRoomMessageCreateInternal
        call_args = mock_create_message.call_args
        internal_obj = call_args[0][1]  # 第二个参数
        assert internal_obj.room_id == room_id
        assert internal_obj.user_id == user_id
        assert internal_obj.user_role == user_role
        assert internal_obj.content == obj_in.content

    # ==================== get_messages 测试 ====================

    @pytest.mark.asyncio
    async def test_get_messages_success(self, mocker):
        """测试成功获取房间留言列表"""
        # 1. 准备 (Arrange)
        mock_db = MagicMock()
        room_id = uuid.uuid4()
        mock_room = MagicMock()
        mock_msg1 = MagicMock()
        mock_msg2 = MagicMock()
        
        # Mock CRUD 函数
        mock_get_room = mocker.patch(
            "app.crud.room.get",
            new_callable=AsyncMock,
            return_value=mock_room
        )
        mock_get_messages = mocker.patch(
            "app.crud.live_features.get_messages_by_room",
            new_callable=AsyncMock,
            return_value=([mock_msg1, mock_msg2], 2)
        )
        
        # 2. 执行 (Act)
        service = MessageService(mock_db)
        # ← 新增：设置Mock room的is_private属性（公开房间，匿名用户可访问）
        mock_room.is_private = False
        # ← 新增：传递权限参数（匿名用户场景）
        messages, total = await service.get_messages(
            room_id=room_id, 
            page=1, 
            size=20, 
            since=None,
            user_id=None,  # ← 新增：匿名用户
            role=None      # ← 新增：匿名用户
        )
        
        # 3. 断言 (Assert)
        assert messages == [mock_msg1, mock_msg2]
        assert total == 2
        mock_get_room.assert_called_once_with(mock_db, room_id)
        mock_get_messages.assert_called_once_with(mock_db, room_id, 1, 20, None)

    @pytest.mark.asyncio
    async def test_get_messages_room_not_found(self, mocker):
        """测试房间不存在时抛出异常"""
        # 1. 准备 (Arrange)
        mock_db = MagicMock()
        room_id = uuid.uuid4()
        
        # Mock crud_room.get 返回 None
        mock_get_room = mocker.patch(
            "app.crud.room.get",
            new_callable=AsyncMock,
            return_value=None
        )
        
        # 2. 执行 & 断言 (Act & Assert)
        service = MessageService(mock_db)
        # ← 新增：传递权限参数（匿名用户场景）
        with pytest.raises(RoomNotFoundException):
            await service.get_messages(
                room_id=room_id, 
                page=1, 
                size=20, 
                since=None,
                user_id=None,  # ← 新增：匿名用户
                role=None      # ← 新增：匿名用户
            )
        
        mock_get_room.assert_called_once_with(mock_db, room_id)
