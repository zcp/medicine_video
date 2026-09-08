"""
LiveCore Service - 公共权限函数单元测试

本模块直接测试 app.core.permissions 中的两个公共函数：
- check_room_owner_or_admin: 校验当前用户是 ADMIN/SUPERADMIN 或房间创建者
- check_room_visibility: 校验房间可见性（公开/私有）

不需要数据库、不需要异步、不需要 httpx。
使用 unittest.mock.MagicMock 模拟 LiveRoom 对象即可。
"""

import pytest
import uuid
from unittest.mock import MagicMock

from app.core.permissions import check_room_owner_or_admin, check_room_visibility
from app.exceptions import PermissionDeniedException


# ==================== 辅助函数 ====================

def _make_room(
    *,
    is_private: bool = False,
    user_id: uuid.UUID = None,
) -> MagicMock:
    """
    创建一个模拟的 LiveRoom 对象。
    
    Args:
        is_private: 是否为私有房间
        user_id: 房间创建者的 user_id
    """
    room = MagicMock()
    room.is_private = is_private
    room.user_id = user_id or uuid.uuid4()
    return room


# ==================== check_room_owner_or_admin 测试 ====================

class TestCheckRoomOwnerOrAdmin:
    """check_room_owner_or_admin 函数测试"""

    @pytest.mark.asyncio
    async def test_admin_passes(self):
        """ADMIN 角色：可以管理任何房间"""
        room = _make_room(user_id=uuid.uuid4())
        # 即使不是自己的房间，ADMIN 也应该通过
        check_room_owner_or_admin(
            room,
            user_id=uuid.uuid4(),
            role="ADMIN",
        )

    @pytest.mark.asyncio
    async def test_superadmin_passes(self):
        """SUPERADMIN 角色：可以管理任何房间"""
        room = _make_room(user_id=uuid.uuid4())
        check_room_owner_or_admin(
            room,
            user_id=uuid.uuid4(),
            role="SUPERADMIN",
        )

    @pytest.mark.asyncio
    async def test_owner_passes(self, regular_user_id: uuid.UUID):
        """房间创建者（REGULAR）：可以管理自己的房间"""
        room = _make_room(user_id=regular_user_id)
        check_room_owner_or_admin(
            room,
            user_id=regular_user_id,
            role="REGULAR",
        )

    @pytest.mark.asyncio
    async def test_owner_with_lowercase_role_passes(self, regular_user_id: uuid.UUID):
        """房间创建者 role 为小写 'regular'：也应通过（兼容现有数据）"""
        room = _make_room(user_id=regular_user_id)
        check_room_owner_or_admin(
            room,
            user_id=regular_user_id,
            role="regular",
        )

    @pytest.mark.asyncio
    async def test_non_owner_regular_raises_permission_denied(self):
        """非创建者 REGULAR：操作别人的房间应抛出 PermissionDeniedException"""
        room = _make_room(user_id=uuid.uuid4())
        with pytest.raises(PermissionDeniedException):
            check_room_owner_or_admin(
                room,
                user_id=uuid.uuid4(),  # 不同的 user_id
                role="REGULAR",
            )

    @pytest.mark.asyncio
    async def test_non_owner_without_role_raises(self):
        """role 为空字符串：应抛出 PermissionDeniedException"""
        room = _make_room(user_id=uuid.uuid4())
        with pytest.raises(PermissionDeniedException):
            check_room_owner_or_admin(
                room,
                user_id=uuid.uuid4(),
                role="",
            )

    @pytest.mark.asyncio
    async def test_non_owner_none_role_raises(self):
        """role 为 None：应抛出 PermissionDeniedException"""
        room = _make_room(user_id=uuid.uuid4())
        with pytest.raises(PermissionDeniedException):
            check_room_owner_or_admin(
                room,
                user_id=uuid.uuid4(),
                role=None,
            )


# ==================== check_room_visibility 测试 ====================

class TestCheckRoomVisibility:
    """check_room_visibility 函数测试"""

    # --- 公开房间 ---

    @pytest.mark.asyncio
    async def test_public_room_allows_anonymous(self):
        """公开房间：匿名用户可以访问"""
        room = _make_room(is_private=False)
        check_room_visibility(room, user_id=None, role=None)

    @pytest.mark.asyncio
    async def test_public_room_allows_regular(self, regular_user_id: uuid.UUID):
        """公开房间：普通用户可以访问"""
        room = _make_room(is_private=False)
        check_room_visibility(room, user_id=regular_user_id, role="REGULAR")

    @pytest.mark.asyncio
    async def test_public_room_allows_admin(self):
        """公开房间：Admin 可以访问"""
        room = _make_room(is_private=False)
        check_room_visibility(room, user_id=uuid.uuid4(), role="ADMIN")

    # --- 私有房间（unlisted 语义，2026-08-11 V1.1 决策 D1：持链可读、发现层过滤） ---

    @pytest.mark.asyncio
    async def test_private_room_anonymous_allowed(self):
        """私有房间：unlisted——匿名用户持链可读（不再 404）"""
        room = _make_room(is_private=True)
        check_room_visibility(room, user_id=None, role=None)

    @pytest.mark.asyncio
    async def test_private_room_admin_passes(self):
        """私有房间：Admin 可以访问"""
        room = _make_room(is_private=True)
        check_room_visibility(room, user_id=uuid.uuid4(), role="ADMIN")

    @pytest.mark.asyncio
    async def test_private_room_superadmin_passes(self):
        """私有房间：SUPERADMIN 可以访问"""
        room = _make_room(is_private=True)
        check_room_visibility(room, user_id=uuid.uuid4(), role="SUPERADMIN")

    @pytest.mark.asyncio
    async def test_private_room_owner_passes(self, regular_user_id: uuid.UUID):
        """私有房间：房间创建者可以访问"""
        room = _make_room(is_private=True, user_id=regular_user_id)
        check_room_visibility(room, user_id=regular_user_id, role="REGULAR")

    @pytest.mark.asyncio
    async def test_private_room_non_owner_allowed(self, regular_user_id: uuid.UUID):
        """私有房间：unlisted——非创建者 REGULAR 持链可读（不再 404）"""
        room = _make_room(is_private=True, user_id=uuid.uuid4())  # 创建者是另一个人
        check_room_visibility(room, user_id=regular_user_id, role="REGULAR")

    @pytest.mark.asyncio
    async def test_private_room_non_owner_without_role_allowed(self):
        """私有房间：unlisted——非创建者且 role 为空字符串同样放行"""
        room = _make_room(is_private=True)
        check_room_visibility(room, user_id=uuid.uuid4(), role="")
