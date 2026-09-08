"""
LiveCore Service - Session Import Service

This module contains the business logic for importing pre-recorded sessions.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import Tuple
import logging
import uuid

from app.crud import room as crud_room
from app.crud import session as crud_session
from app.models.live_core import LiveSession, LiveRoom
from app.exceptions import (
    RoomNotFoundException,
    PermissionDeniedException,
    InvalidParameterException,
    NotFoundException
)
from app.core.exceptions import DatabaseOperationException
from app.core.permissions import check_room_owner_or_admin
from app.services.utils_playback import (
    normalize_playback_url,
    calc_playback_url_hash,
)

logger = logging.getLogger(__name__)


class SessionImportService:
    """导入会话服务（学院派实现，V6 幂等扩展版）"""

    def __init__(self, db: AsyncSession):
        self.db = db

    def _check_write_permission(
        self,
        room: LiveRoom,
        user_id: UUID,
        role: str
    ) -> None:
        """
        写操作权限校验（修改/删除）

        委托给公共函数 check_room_owner_or_admin 实现。
        保留此方法避免改动外部调用方。

        Raises:
            PermissionDeniedException: 无权修改（403）
        """
        check_room_owner_or_admin(room, user_id, role)

    async def import_create_session(
        self,
        room_id: UUID,
        public_id: UUID,
        session_in: dict,
        role: str  # ← 新增：权限参数
    ) -> Tuple[LiveSession, bool]:
        """
        导入创建会话（业务逻辑层）

        职责：
        1. 验证房间存在性
        2. 验证用户权限（调用权限守卫函数）
        3. 验证参数合法性
        4. 基于 (room_id, playback_url_hash) 的幂等 get-or-create

        返回：
        - (LiveSession, bool): 第二个布尔值表示是否命中幂等（True = 已存在记录）
        """
        # ← 修改：验证房间存在性（不传递权限参数）
        room = await crud_room.get(self.db, room_id=room_id)
        if not room:
            logger.warning("导入会话失败：房间不存在 room_id=%s", room_id)
            raise RoomNotFoundException(f"房间 {room_id} 不存在")

        # ← 修改：使用权限守卫函数验证权限
        self._check_write_permission(room, public_id, role)

        # 3. 验证参数
        status = session_in.get("status")
        playback_url = session_in.get("playback_url")

        if status != "ready":
            raise InvalidParameterException(
                message="导入回放会话的 status 只能为 'ready'",
                code=4001,
            )

        if not playback_url:
            raise InvalidParameterException(
                message="导入会话必须提供 playback_url",
                code=4001,
            )

        # 4. 规范化 URL 并计算哈希（V6 新增）
        playback_hash = calc_playback_url_hash(playback_url)
        normalized_url = normalize_playback_url(playback_url)

        # 5. 幂等查询：按 (room_id, playback_url_hash)
        try:
            existing = await crud_session.get_by_room_and_playback_hash(
                db=self.db,
                room_id=room_id,
                playback_url_hash=playback_hash,
            )
        except DatabaseOperationException:
            # 透传数据库操作异常，由上层统一处理
            raise

        if existing:
            logger.info(
                "导入会话命中幂等：room_id=%s, playback_url_hash=%s, session_id=%s",
                room_id,
                playback_hash,
                existing.id,
            )
            return existing, True

        # 6. 构建 session_data 字典并创建会话（包含 playback_url_hash）
        session_data = {
            "id": uuid.uuid4(),
            "room_id": room_id,
            "status": status,
            "start_time": session_in.get("start_time"),
            "end_time": session_in.get("end_time"),
            "playback_url": normalized_url,
            "playback_url_hash": playback_hash,
        }

        # crud_session.create (alias to create_with_stats) handles transaction and stats creation.
        db_session = await crud_session.create(self.db, obj_in=session_data)

        logger.info(
            "导入会话成功：session_id=%s, room_id=%s, public_id=%s, playback_url_hash=%s",
            db_session.id,
            room_id,
            public_id,
            playback_hash,
        )

        return db_session, False
