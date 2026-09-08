"""
LiveCore Service - Room Permission Guards Unit Tests

本模块包含直播间权限守卫函数的专项测试。
测试范围：_check_room_visibility、_check_write_permission

测试场景：
- 匿名用户、Owner、非Owner、Admin
- Public、Private房间
"""

import pytest
import uuid
from unittest.mock import MagicMock

from app.services.room_service import RoomService
from app.exceptions import PermissionDeniedException


class TestRoomPermissionGuards:
    """直播间权限守卫函数专项测试"""
    
    # ==================== _check_room_visibility 测试 ====================
    
    @pytest.mark.asyncio
    async def test_check_room_visibility_public_anonymous(self):
        """测试：Public房间，匿名用户可访问"""
        # ===== Arrange (准备) =====
        room_service = RoomService(db=MagicMock())
        mock_room = MagicMock()
        mock_room.id = uuid.uuid4()
        mock_room.is_private = False  # Public房间
        mock_room.user_id = uuid.uuid4()
        
        # ===== Act & Assert (执行 & 断言) =====
        # 应该不抛出异常
        room_service._check_room_visibility(
            mock_room,
            user_id=None,
            role=None
        )
    
    @pytest.mark.asyncio
    async def test_check_room_visibility_private_anonymous_allowed(self):
        """测试：Private房间，unlisted 语义——匿名用户持链可读（不再 404）"""
        # ===== Arrange (准备) =====
        room_service = RoomService(db=MagicMock())
        mock_room = MagicMock()
        mock_room.id = uuid.uuid4()
        mock_room.is_private = True  # Private房间
        mock_room.user_id = uuid.uuid4()

        # ===== Act & Assert (执行 & 断言) =====
        # 不抛异常（unlisted：持链可读）
        room_service._check_room_visibility(
            mock_room,
            user_id=None,
            role=None
        )
    
    @pytest.mark.asyncio
    async def test_check_room_visibility_private_owner_success(
        self,
        regular_user_id: uuid.UUID
    ):
        """测试：Private房间，Owner可访问"""
        # ===== Arrange (准备) =====
        room_service = RoomService(db=MagicMock())
        mock_room = MagicMock()
        mock_room.id = uuid.uuid4()
        mock_room.is_private = True  # Private房间
        mock_room.user_id = regular_user_id
        
        # ===== Act & Assert (执行 & 断言) =====
        # 应该不抛出异常
        room_service._check_room_visibility(
            mock_room,
            user_id=regular_user_id,
            role="REGULAR"
        )
    
    @pytest.mark.asyncio
    async def test_check_room_visibility_private_non_owner_allowed(
        self,
        regular_user_id: uuid.UUID,
        another_user_id: uuid.UUID
    ):
        """测试：Private房间，unlisted 语义——非 Owner 持链可读（不再 404）"""
        # ===== Arrange (准备) =====
        room_service = RoomService(db=MagicMock())
        mock_room = MagicMock()
        mock_room.id = uuid.uuid4()
        mock_room.is_private = True  # Private房间
        mock_room.user_id = another_user_id  # 属于另一个用户

        # ===== Act & Assert (执行 & 断言) =====
        # 不抛异常（unlisted：持链可读）
        room_service._check_room_visibility(
            mock_room,
            user_id=regular_user_id,  # 不是Owner
            role="REGULAR"
        )
    
    @pytest.mark.asyncio
    async def test_check_room_visibility_private_admin_success(
        self,
        admin_user_id: uuid.UUID
    ):
        """测试：Private房间，Admin可访问"""
        # ===== Arrange (准备) =====
        room_service = RoomService(db=MagicMock())
        another_user_id = uuid.uuid4()  # 非Admin的房间
        mock_room = MagicMock()
        mock_room.id = uuid.uuid4()
        mock_room.is_private = True  # Private房间
        mock_room.user_id = another_user_id
        
        # ===== Act & Assert (执行 & 断言) =====
        # 应该不抛出异常（Admin有上帝视角）
        room_service._check_room_visibility(
            mock_room,
            user_id=admin_user_id,
            role="ADMIN"
        )
    
    # ==================== _check_write_permission 测试 ====================
    
    @pytest.mark.asyncio
    async def test_check_write_permission_owner_success(
        self,
        regular_user_id: uuid.UUID
    ):
        """测试：Owner有写权限"""
        # ===== Arrange (准备) =====
        room_service = RoomService(db=MagicMock())
        mock_room = MagicMock()
        mock_room.id = uuid.uuid4()
        mock_room.user_id = regular_user_id
        
        # ===== Act & Assert (执行 & 断言) =====
        # 应该不抛出异常
        room_service._check_write_permission(
            mock_room,
            user_id=regular_user_id,
            role="REGULAR"
        )
    
    @pytest.mark.asyncio
    async def test_check_write_permission_non_owner_raises_403(
        self,
        regular_user_id: uuid.UUID,
        another_user_id: uuid.UUID
    ):
        """测试：非Owner写操作应抛出403"""
        # ===== Arrange (准备) =====
        room_service = RoomService(db=MagicMock())
        mock_room = MagicMock()
        mock_room.id = uuid.uuid4()
        mock_room.user_id = another_user_id  # 属于另一个用户
        
        # ===== Act & Assert (执行 & 断言) =====
        with pytest.raises(PermissionDeniedException):
            room_service._check_write_permission(
                mock_room,
                user_id=regular_user_id,  # 不是Owner
                role="REGULAR"
            )
    
    @pytest.mark.asyncio
    async def test_check_write_permission_admin_success(
        self,
        admin_user_id: uuid.UUID
    ):
        """测试：Admin有写权限（即使不是Owner）"""
        # ===== Arrange (准备) =====
        room_service = RoomService(db=MagicMock())
        another_user_id = uuid.uuid4()  # 非Admin的房间
        mock_room = MagicMock()
        mock_room.id = uuid.uuid4()
        mock_room.user_id = another_user_id
        
        # ===== Act & Assert (执行 & 断言) =====
        # 应该不抛出异常（Admin有上帝视角）
        room_service._check_write_permission(
            mock_room,
            user_id=admin_user_id,
            role="ADMIN"
        )

