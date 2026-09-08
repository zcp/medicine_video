"""
LiveCore Service - Room Permission Guards Unit Tests

测试范围：_check_room_visibility（文档 18 unlisted）、_check_write_permission
"""

import pytest
import uuid
from unittest.mock import MagicMock

from app.services.room_service import RoomService
from app.exceptions import PermissionDeniedException


class TestRoomPermissionGuards:
    """直播间权限守卫函数专项测试"""

    @pytest.mark.asyncio
    async def test_check_room_visibility_public_anonymous(self):
        """Public 房间，匿名可读"""
        room_service = RoomService(db=MagicMock())
        mock_room = MagicMock()
        mock_room.id = uuid.uuid4()
        mock_room.is_private = False
        mock_room.user_id = uuid.uuid4()

        room_service._check_room_visibility(
            mock_room,
            user_id=None,
            role=None,
        )

    @pytest.mark.asyncio
    async def test_check_room_visibility_private_anonymous_allowed(self):
        """不公开房间：匿名持 room_id 可读（unlisted）"""
        room_service = RoomService(db=MagicMock())
        mock_room = MagicMock()
        mock_room.id = uuid.uuid4()
        mock_room.is_private = True
        mock_room.user_id = uuid.uuid4()

        room_service._check_room_visibility(
            mock_room,
            user_id=None,
            role=None,
        )

    @pytest.mark.asyncio
    async def test_check_room_visibility_private_owner_success(
        self,
        regular_user_id: uuid.UUID,
    ):
        """不公开房间，Owner 可读"""
        room_service = RoomService(db=MagicMock())
        mock_room = MagicMock()
        mock_room.id = uuid.uuid4()
        mock_room.is_private = True
        mock_room.user_id = regular_user_id

        room_service._check_room_visibility(
            mock_room,
            user_id=regular_user_id,
            role="REGULAR",
        )

    @pytest.mark.asyncio
    async def test_check_room_visibility_private_non_owner_allowed(
        self,
        regular_user_id: uuid.UUID,
        another_user_id: uuid.UUID,
    ):
        """不公开房间：非 Owner 持链可读"""
        room_service = RoomService(db=MagicMock())
        mock_room = MagicMock()
        mock_room.id = uuid.uuid4()
        mock_room.is_private = True
        mock_room.user_id = another_user_id

        room_service._check_room_visibility(
            mock_room,
            user_id=regular_user_id,
            role="REGULAR",
        )

    @pytest.mark.asyncio
    async def test_check_room_visibility_private_admin_success(
        self,
        admin_user_id: uuid.UUID,
    ):
        """不公开房间，Admin 可读"""
        room_service = RoomService(db=MagicMock())
        another_user_id = uuid.uuid4()
        mock_room = MagicMock()
        mock_room.id = uuid.uuid4()
        mock_room.is_private = True
        mock_room.user_id = another_user_id

        room_service._check_room_visibility(
            mock_room,
            user_id=admin_user_id,
            role="ADMIN",
        )

    @pytest.mark.asyncio
    async def test_check_write_permission_owner_success(
        self,
        regular_user_id: uuid.UUID,
    ):
        """Owner 可写"""
        room_service = RoomService(db=MagicMock())
        mock_room = MagicMock()
        mock_room.id = uuid.uuid4()
        mock_room.user_id = regular_user_id

        room_service._check_write_permission(
            mock_room,
            user_id=regular_user_id,
            role="REGULAR",
        )

    @pytest.mark.asyncio
    async def test_check_write_permission_non_owner_raises(
        self,
        regular_user_id: uuid.UUID,
        another_user_id: uuid.UUID,
    ):
        """非 Owner 不可写"""
        room_service = RoomService(db=MagicMock())
        mock_room = MagicMock()
        mock_room.id = uuid.uuid4()
        mock_room.user_id = another_user_id

        with pytest.raises(PermissionDeniedException):
            room_service._check_write_permission(
                mock_room,
                user_id=regular_user_id,
                role="REGULAR",
            )

    @pytest.mark.asyncio
    async def test_check_write_permission_admin_success(
        self,
        admin_user_id: uuid.UUID,
    ):
        """Admin 可写他人房"""
        room_service = RoomService(db=MagicMock())
        mock_room = MagicMock()
        mock_room.id = uuid.uuid4()
        mock_room.user_id = uuid.uuid4()

        room_service._check_write_permission(
            mock_room,
            user_id=admin_user_id,
            role="ADMIN",
        )
