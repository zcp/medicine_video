"""
LiveCore Service - 公共权限校验函数

集中管理所有权限校验逻辑，消除各处分散的重复实现。
所有 Service 层应通过此模块进行权限判断，而非内联手写。

角色定义：
    ADMIN / SUPERADMIN   — 系统管理员，拥有全部操作权限
    MODERATOR（预留）    — 未来版本中与 ADMIN 同权，实施时只需在 role in (...) 元组中添加 'MODERATOR'
    REGULAR              — 普通用户，仅能操作自己的资源
    匿名用户 (None)      — 仅能访问公开资源

使用示例：
    from app.core.permissions import check_room_owner_or_admin
    
    def some_method(self, room, user_id, role):
        check_room_owner_or_admin(room, user_id, role)
        # ... 业务逻辑
"""

from typing import Optional
from uuid import UUID

import logging

from app.models.live_core import LiveRoom
from app.exceptions import PermissionDeniedException, NotFoundException

logger = logging.getLogger(__name__)


def check_room_owner_or_admin(
    room: LiveRoom,
    user_id: UUID,
    role: str,
) -> None:
    """
    校验当前用户是 ADMIN/SUPERADMIN 或房间创建者。

    Args:
        room: 直播间对象
        user_id: 当前用户的 public_id
        role: 当前用户的角色（字符串格式，如 "ADMIN"、"REGULAR"）

    Raises:
        PermissionDeniedException: 无权操作（403）

    Note:
        MODERATOR 角色预留：如需加入，将 role 判断改为 role in ('ADMIN', 'SUPERADMIN', 'MODERATOR')
    """
    if role in ('ADMIN', 'SUPERADMIN'):
        return
    if room.user_id == user_id:
        return
    raise PermissionDeniedException("需要管理员或房间创建者权限")


def check_room_visibility(
    room: LiveRoom,
    user_id: Optional[UUID],
    role: Optional[str],
) -> None:
    """
    校验房间可见性（REST 读路径统一入口）。

    公开房间（is_private=False）：所有用户可访问（含匿名）。
    私有房间（is_private=True）：unlisted 语义——任何人持 room_id 均可访问（含匿名），
    仅不进发现层（列表/首页/搜索由 SQL 过滤）。

    Args:
        room: 直播间对象
        user_id: 当前用户的 public_id（匿名时为 None）
        role: 当前用户的角色（匿名时为 None）

    Raises:
        无（读路径放行；房间不存在由上层抛 404）

    Note:
        - 本函数为 REST 读路径的 unlisted 可见性校验（2026-08-11 语义变更，V1.1 决策 D1）
        - WS 留言订阅走方案 B 保守语义（私密房仅创建者/管理员，见 live_features.py）
        - 写操作权限见 check_room_owner_or_admin（语义不变）
    """
    if not room.is_private:
        return
    if role in ('ADMIN', 'SUPERADMIN') and user_id and room.user_id != user_id:
        logger.info(
            "Admin查看不公开房间: admin=%s, role=%s, room_id=%s, owner=%s",
            user_id, role, room.id, room.user_id,
        )
    return


def check_admin_permission(role: Optional[str]) -> None:
    """
    校验当前用户是 ADMIN 或 SUPERADMIN。

    Args:
        role: 当前用户的角色（允许 None，会被拒绝）

    Raises:
        PermissionDeniedException: 非管理员（403）
    """
    if role not in ('ADMIN', 'SUPERADMIN'):
        raise PermissionDeniedException("需要管理员权限")


def check_authenticated_user(role: Optional[str]) -> None:
    """
    校验当前用户是已登录用户（允许 REGULAR/ADMIN/SUPERADMIN）。
    仅拒绝匿名用户和未知角色。

    Args:
        role: 当前用户的角色（允许 None，会被拒绝）

    Raises:
        PermissionDeniedException: 未登录或角色无效（403）
    """
    if role not in ('REGULAR', 'ADMIN', 'SUPERADMIN'):
        raise PermissionDeniedException("需要登录后才能执行此操作")
