"""
LiveCore Service - Session Permission Inheritance Unit Tests

本模块包含场次权限继承的专项测试。
测试范围：场次继承直播间权限（通过SessionService.get_sessions_by_room）

测试场景：
- Public房间的Session列表：匿名用户可访问
- Private房间的Session列表：匿名用户不可访问（继承房间不可见性）
- Owner可访问Private房间的Session
"""

import pytest
import uuid

from app.services.session_service import SessionService


class TestSessionPermissionInheritance:
    """场次权限继承专项测试"""
    
    @pytest.mark.asyncio
    async def test_session_inherits_public_room_visibility_for_anonymous(
        self,
        db_session,
        regular_user_id: uuid.UUID
    ):
        """测试：场次继承Public房间的可见性（匿名用户）"""
        async for db in db_session:
            # ===== Arrange (准备) =====
            # 创建Public房间
            from app.crud import room as crud_room
            from app.schemas.live_core import LiveRoomCreate
            
            room_data = LiveRoomCreate(
                title=f"Public Room {uuid.uuid4().hex[:6]}",
                description="Test Description",
                is_private=False,
                record_by_default=True
            )
            room = await crud_room.create(db, obj_in=room_data, user_id=regular_user_id)
            await db.commit()
            await db.refresh(room)
            
            session_service = SessionService(db=db)
            
            # ===== Act (执行) =====
            # 匿名用户访问该房间的Session列表
            sessions, total = await session_service.get_sessions_by_room(
                room_id=room.id,
                page=1,
                size=10,
                user_id=None,  # 匿名用户
                role=None
            )
            
            # ===== Assert (断言) =====
            # 应该成功返回（继承房间的可见性）
            assert isinstance(sessions, list)
            assert total >= 0
    
    @pytest.mark.asyncio
    async def test_session_inherits_private_room_visibility_for_anonymous(
        self,
        db_session,
        regular_user_id: uuid.UUID
    ):
        """测试：场次继承Private房间的可见性（匿名用户持链可读，unlisted 语义 2026-08-11）"""
        async for db in db_session:
            # ===== Arrange (准备) =====
            # 创建Private房间
            from app.crud import room as crud_room
            from app.schemas.live_core import LiveRoomCreate

            room_data = LiveRoomCreate(
                title=f"Private Room {uuid.uuid4().hex[:6]}",
                description="Test Description",
                is_private=True,
                record_by_default=True
            )
            room = await crud_room.create(db, obj_in=room_data, user_id=regular_user_id)
            await db.commit()
            await db.refresh(room)

            session_service = SessionService(db=db)

            # ===== Act & Assert (执行 & 断言) =====
            # 匿名用户访问该房间的Session列表应成功返回（unlisted：持链可读）
            sessions, total = await session_service.get_sessions_by_room(
                room_id=room.id,
                page=1,
                size=10,
                user_id=None,  # 匿名用户
                role=None
            )
            assert isinstance(sessions, list)
            assert total >= 0
    
    @pytest.mark.asyncio
    async def test_session_inherits_private_room_visibility_for_owner(
        self,
        db_session,
        regular_user_id: uuid.UUID,
        regular_user_role: str
    ):
        """测试：Owner可访问Private房间的Session"""
        async for db in db_session:
            # ===== Arrange (准备) =====
            # 创建Private房间（属于regular_user_id）
            from app.crud import room as crud_room
            from app.schemas.live_core import LiveRoomCreate
            
            room_data = LiveRoomCreate(
                title=f"Private Room {uuid.uuid4().hex[:6]}",
                description="Test Description",
                is_private=True,
                record_by_default=True
            )
            room = await crud_room.create(db, obj_in=room_data, user_id=regular_user_id)
            await db.commit()
            await db.refresh(room)
            
            session_service = SessionService(db=db)
            
            # ===== Act (执行) =====
            # Owner访问该房间的Session列表
            sessions, total = await session_service.get_sessions_by_room(
                room_id=room.id,
                page=1,
                size=10,
                user_id=regular_user_id,  # Owner
                role=regular_user_role
            )
            
            # ===== Assert (断言) =====
            # 应该成功返回（Owner可以访问）
            assert isinstance(sessions, list)
            assert total >= 0

