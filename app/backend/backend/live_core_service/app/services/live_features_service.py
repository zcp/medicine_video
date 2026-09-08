"""
直播间 Tab 和 留言功能的 Service 层（学院派）

职责：
- 业务逻辑验证（权限检查, URL 过滤, 状态校验）
- 组合 CRUD 操作
- 抛出自定义 Python 异常（e.g., TabNotFoundException）
- 严禁处理事务（db.commit/rollback）
- 严禁抛出 HTTPException
"""

import uuid
import logging
import re
from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

# [学院派] 导入 CRUD 模块
from app.crud import live_features as crud_live_features
from app.crud import room as crud_room  # 用于检查 Room 是否存在

from app.models.live_features import (
    LiveRoomTab, 
    LiveRoomMessage, 
    LiveRoomMessageUserRole, 
    LiveRoomTabContentType
)
from app.models.live_core import LiveRoom  # 导入 LiveRoom
from app.schemas.live_features import (
    LiveRoomTabCreate, 
    LiveRoomTabUpdate, 
    LiveRoomMessageCreate, 
    LiveRoomMessageCreateInternal
)

# [学院派] 导入自定义异常
from app.exceptions import (
    TabNotFoundException,
    RoomNotFoundException,
    PermissionDeniedException,
    InvalidParameterException,
    NotFoundException,
    MessageNotFoundException,
)
from app.core.permissions import check_room_owner_or_admin, check_room_visibility

logger = logging.getLogger(__name__)

# URL 匹配正则表达式（用于留言）
URL_REGEX = re.compile(
    r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
)


class TabService:
    """Tab 相关业务逻辑"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def _check_room_exists(self, room_id: uuid.UUID) -> LiveRoom:
        """
        辅助函数：检查房间是否存在
        
        Args:
            room_id: 房间 ID
        
        Returns:
            LiveRoom: 房间对象
        
        Raises:
            RoomNotFoundException: 房间不存在
        """
        room = await crud_room.get(self.db, room_id)
        if room is None:
            raise RoomNotFoundException(f"Room ID: {room_id} 不存在")
        return room
    
    def _check_tab_management_permission(
        self,
        room: LiveRoom,
        user_id: uuid.UUID,
        role: str
    ) -> None:
        """
        检查Tab管理权限（创建者或Admin）

        委托给公共函数 check_room_owner_or_admin 实现。
        保留此方法避免改动外部调用方。

        Raises:
            PermissionDeniedException: 无权管理Tab（403）
        """
        # Admin 管理他人房间 Tab 的审计日志
        if role in ('ADMIN', 'SUPERADMIN') and room.user_id != user_id:
            logger.info(
                f"Admin管理他人房间Tab: admin={user_id}, role={role}, "
                f"room_id={room.id}, room_owner={room.user_id}"
            )
        check_room_owner_or_admin(room, user_id, role)

    async def list_tabs_for_admin(
        self, 
        user_id: uuid.UUID,
        user_role: LiveRoomMessageUserRole,
        room_id: uuid.UUID,
        role: str  # ← 新增：权限参数（字符串格式）
    ) -> Tuple[List[LiveRoomTab], int]:
        """
        获取指定房间的所有 Tab（管理员用）
        
        Args:
            user_id: 用户ID
            user_role: 用户角色（Enum格式，保留用于兼容）
            room_id: 房间 ID
            role: 当前用户的角色（字符串格式，从JWT的role字段提取）
        
        Returns:
            Tuple[List[LiveRoomTab], int]: (Tab 列表, 总数)
        
        Raises:
            PermissionDeniedException: 权限不足
            RoomNotFoundException: 房间不存在
        """
        # 2. 检查房间是否存在（先查询room对象）
        room = await self._check_room_exists(room_id)
        
        # ← 修改：使用Tab管理权限检查（创建者或Admin）
        self._check_tab_management_permission(room, user_id, role)
        
        # 3. 获取所有 Tab（暂不分页，获取前100个）
        tabs, total = await crud_live_features.get_all_by_room_id(self.db, room_id, skip=0, limit=100)
        
        logger.info(f"Admin user {user_id} listed {len(tabs)} tabs for room {room_id}")
        return tabs, total
    
    async def get_active_tabs_for_room(self, room_id: uuid.UUID) -> List[LiveRoomTab]:
        """
        获取指定房间的所有激活的 Tab（前端展示用）

        注意：当前生产端点 list_room_tabs_public 直接调用 CRUD 层
        get_active_by_room_id()，因为它需要 room 对象做 is_private 可见性校验。
        此方法保留供未来不需要 room 对象的调用场景使用。
        
        Args:
            room_id: 房间 ID
        
        Returns:
            List[LiveRoomTab]: 激活的 Tab 列表
        
        Raises:
            RoomNotFoundException: 房间不存在
        """
        # 1. 检查房间是否存在（确保房间存在，即使是公共访问）
        await self._check_room_exists(room_id)
        
        # 2. 获取激活的 Tab
        tabs = await crud_live_features.get_active_by_room_id(self.db, room_id)
        
        logger.info(f"Retrieved {len(tabs)} active tabs for room {room_id}")
        return tabs
    
    async def create_tab(
        self, 
        user_id: uuid.UUID,
        user_role: LiveRoomMessageUserRole,
        room_id: uuid.UUID, 
        obj_in: LiveRoomTabCreate,
        role: str  # ← 新增：权限参数（字符串格式）
    ) -> LiveRoomTab:
        """
        创建新的 Tab
        
        Args:
            user_id: 用户ID
            user_role: 用户角色（Enum格式，保留用于兼容）
            room_id: 房间 ID
            obj_in: Tab 创建数据
            role: 当前用户的角色（字符串格式，从JWT的role字段提取）
        
        Returns:
            LiveRoomTab: 创建的 Tab 对象
        
        Raises:
            PermissionDeniedException: 权限不足
            RoomNotFoundException: 房间不存在
            InvalidParameterException: 参数无效
        """
        # 2. 检查房间是否存在（先查询room对象）
        room = await self._check_room_exists(room_id)
        
        # ← 修改：使用Tab管理权限检查（创建者或Admin）
        self._check_tab_management_permission(room, user_id, role)
        
        # 3. 参数校验：content_type 与内容匹配
        if obj_in.content_type == LiveRoomTabContentType.TEXT and not obj_in.text_content:
            raise InvalidParameterException("当 content_type=text 时, text_content 不能为空")
        
        if obj_in.content_type == LiveRoomTabContentType.IMAGE and not obj_in.image_url:
            raise InvalidParameterException("当 content_type=image 时, image_url 不能为空")
        
        if obj_in.content_type == LiveRoomTabContentType.MIXED:
            if not obj_in.text_content and not obj_in.image_url:
                raise InvalidParameterException("当 content_type=mixed 时, text_content 和 image_url 至少需要一个")
        
        # 4. 调用 CRUD 层创建
        new_tab = await crud_live_features.create_tab(self.db, obj_in, room_id)
        
        logger.info(f"Admin user {user_id} created tab {new_tab.id} for room {room_id}")
        return new_tab
    
    async def update_tab(
        self, 
        user_id: uuid.UUID,
        user_role: LiveRoomMessageUserRole,
        tab_id: uuid.UUID, 
        obj_in: LiveRoomTabUpdate,
        role: str  # ← 新增：权限参数（字符串格式）
    ) -> LiveRoomTab:
        """
        更新 Tab
        
        Args:
            user_id: 用户ID
            user_role: 用户角色（Enum格式，保留用于兼容）
            tab_id: Tab ID
            obj_in: 更新数据
            role: 当前用户的角色（字符串格式，从JWT的role字段提取）
        
        Returns:
            LiveRoomTab: 更新后的 Tab 对象
        
        Raises:
            PermissionDeniedException: 权限不足
            TabNotFoundException: Tab 不存在
            InvalidParameterException: 参数无效
        """
        # 2. 获取 Tab
        db_tab = await crud_live_features.get_tab(self.db, tab_id)
        if db_tab is None:
            raise TabNotFoundException(f"Tab ID: {tab_id} 不存在")
        
        # ← 修改：查询room对象并检查Tab管理权限（创建者或Admin）
        room = await self._check_room_exists(db_tab.room_id)
        self._check_tab_management_permission(room, user_id, role)
        
        # 3. 参数校验（可选，如果提供了 content_type）
        if obj_in.content_type is not None:
            # 获取更新后的值
            new_content_type = obj_in.content_type
            new_text_content = obj_in.text_content if obj_in.text_content is not None else db_tab.text_content
            new_image_url = obj_in.image_url if obj_in.image_url is not None else db_tab.image_url
            
            if new_content_type == LiveRoomTabContentType.TEXT and not new_text_content:
                raise InvalidParameterException("当 content_type=text 时, text_content 不能为空")
            
            if new_content_type == LiveRoomTabContentType.IMAGE and not new_image_url:
                raise InvalidParameterException("当 content_type=image 时, image_url 不能为空")
        
        # 4. 调用 CRUD 层更新
        updated_tab = await crud_live_features.update_tab(self.db, db_tab, obj_in)
        
        logger.info(f"Admin user {user_id} updated tab {tab_id}")
        return updated_tab
    
    async def delete_tab(
        self, 
        user_id: uuid.UUID, 
        user_role: LiveRoomMessageUserRole, 
        tab_id: uuid.UUID,
        role: str  # ← 新增：权限参数（字符串格式）
    ) -> LiveRoomTab:
        """
        删除 Tab
        
        Args:
            user_id: 用户ID
            user_role: 用户角色（Enum格式，保留用于兼容）
            tab_id: Tab ID
            role: 当前用户的角色（字符串格式，从JWT的role字段提取）
        
        Returns:
            LiveRoomTab: 被删除的 Tab 对象
        
        Raises:
            PermissionDeniedException: 权限不足
            TabNotFoundException: Tab 不存在
        """
        # 2. 获取 Tab
        db_tab = await crud_live_features.get_tab(self.db, tab_id)
        if db_tab is None:
            raise TabNotFoundException(f"Tab ID: {tab_id} 不存在")
        
        # ← 修改：查询room对象并检查Tab管理权限（创建者或Admin）
        room = await self._check_room_exists(db_tab.room_id)
        self._check_tab_management_permission(room, user_id, role)
        
        # 3. 调用 CRUD 层删除
        deleted_tab = await crud_live_features.remove_tab(self.db, db_tab)
        
        logger.info(f"Admin user {user_id} deleted tab {tab_id}")
        return deleted_tab


class MessageService:
    """留言相关业务逻辑"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def _check_room_exists(self, room_id: uuid.UUID) -> LiveRoom:
        """
        辅助函数：检查房间是否存在
        
        Args:
            room_id: 房间 ID
        
        Returns:
            LiveRoom: 房间对象
        
        Raises:
            RoomNotFoundException: 房间不存在
        """
        room = await crud_room.get(self.db, room_id)
        if room is None:
            raise RoomNotFoundException(f"Room ID: {room_id} 不存在")
        return room
    
    def _check_room_visibility(
        self,
        room: LiveRoom,
        user_id: Optional[uuid.UUID],
        role: Optional[str]
    ) -> None:
        """
        统一的房间可见性校验逻辑（复用Room模块的权限守卫逻辑）

        委托给公共函数 check_room_visibility 实现。
        保留此方法避免改动外部调用方。

        Raises:
            NotFoundException: 房间不存在或无权访问（404）
        """
        # Admin 查看 Private 资源的审计日志
        if room.is_private and role in ('ADMIN', 'SUPERADMIN') and room.user_id != user_id:
            logger.info(
                f"Admin查看Private资源: admin={user_id}, role={role}, "
                f"room_id={room.id}, owner={room.user_id}"
            )
        check_room_visibility(room, user_id, role)
    
    async def create_message(
        self, 
        user_id: uuid.UUID,
        user_role: LiveRoomMessageUserRole,
        room_id: uuid.UUID, 
        obj_in: LiveRoomMessageCreate,
        role: str,  # ← 新增：权限参数（字符串格式）
        user_display_name: Optional[str] = None,
        user_avatar_url: Optional[str] = None
    ) -> LiveRoomMessage:
        """
        创建新留言（需要登录，继承Room权限）
        
        Args:
            user_id: 用户ID
            user_role: 用户角色（Enum格式，保留用于兼容）
            room_id: 房间 ID
            obj_in: 留言创建数据
            role: 当前用户的角色（字符串格式，从JWT的role字段提取）
            user_display_name: 用户展示昵称（写时快照，可选）
            user_avatar_url: 用户头像 URL（写时快照，可选）
        
        Returns:
            LiveRoomMessage: 创建的留言对象
        
        Raises:
            RoomNotFoundException: 房间不存在
            NotFoundException: 房间不存在或无权访问（404）
            InvalidParameterException: 参数无效（如普通用户发送包含 URL 的留言）
        """
        # ← 修改：检查房间是否存在
        room = await crud_room.get(self.db, room_id)
        if room is None:
            raise RoomNotFoundException(f"Room ID: {room_id} 不存在")
        
        # ← 新增：权限校验（检查Room可见性，Message继承Room权限）
        self._check_room_visibility(room, user_id, role)
        
        # ← 修改：URL 过滤（房间创建者在自己房间允许URL）
        is_admin = role in ['ADMIN', 'SUPERADMIN']
        has_url = bool(URL_REGEX.search(obj_in.content))
        
        if has_url:
            # Admin：允许任意内容
            if is_admin:
                pass
            # 房间创建者：允许在自己房间发送URL
            elif room.user_id == user_id:
                logger.info(
                    f"房间创建者发送URL留言: user_id={user_id}, room_id={room.id}, "
                    f"room_owner={room.user_id}"
                )
            # 其他用户：禁止URL
            else:
                logger.warning(
                    f"非管理员/创建者尝试发送URL留言: user_id={user_id}, role={role}, "
                    f"room_id={room.id}, room_owner={room.user_id}"
                )
                raise InvalidParameterException(
                    code=4004, 
                    message="非管理员用户不允许发送包含 URL 的留言"
                )

        # V4.2: 发送频率限制
        from app.core.redis_cache import check_message_rate_limit
        if not await check_message_rate_limit(user_id, room_id):
            raise InvalidParameterException("发送留言过于频繁，请稍后再试", code=4004)

        # PR 2: 内容安全校验
        try:
            from app.content_safety.service import check_scene_fields, assert_content_safe_or_raise
            from app.core.config import settings
            if getattr(settings, "CONTENT_SAFETY_ENABLED", True):
                safety_result = await check_scene_fields(
                    db=self.db,
                    scene="message",
                    field_values={"content": obj_in.content},
                    user_id=user_id,
                    resource_type="message",
                )
                assert_content_safe_or_raise(safety_result)
        except Exception as e:
            from app.content_safety.exceptions import ContentSafetyBlockedException
            if isinstance(e, ContentSafetyBlockedException):
                raise
            logger.warning("内容安全校验异常，降级放行: %s", e)

        # 3. [关键] 内部 Schema 转换（学院派规范 5.2）
        # 写时快照：昵称 + 头像（读时优先个人中心当前值，extra 兜底）
        extra: Optional[Dict[str, Any]] = None
        if user_display_name or user_avatar_url:
            extra = {}
            if user_display_name:
                extra["user_display_name"] = user_display_name
            if user_avatar_url:
                extra["avatar_url"] = user_avatar_url

        internal_obj_in = LiveRoomMessageCreateInternal(
            content=obj_in.content,
            room_id=room_id,
            session_id=None,  # 可以后续扩展从当前 session 获取
            user_id=user_id,
            user_role=user_role,
            extra=extra
        )
        
        # 4. 调用 CRUD 层创建
        new_message = await crud_live_features.create_message(self.db, internal_obj_in)
        
        logger.info(f"User {user_id} created message {new_message.id} in room {room_id}")
        return new_message
    
    async def get_messages(
        self, 
        room_id: uuid.UUID, 
        page: int, 
        size: int, 
        since: Optional[datetime] = None,
        user_id: Optional[uuid.UUID] = None,  # ← 新增：权限参数
        role: Optional[str] = None  # ← 新增：权限参数
    ) -> Tuple[List[LiveRoomMessage], int]:
        """
        获取房间留言列表（支持匿名访问，继承Room权限）
        
        Args:
            room_id: 房间 ID
            page: 页码（从 1 开始）
            size: 每页大小
            since: 可选的时间过滤
            user_id: 当前用户的public_id（匿名时为None）
            role: 当前用户的角色（匿名时为None）
        
        Returns:
            Tuple[List[LiveRoomMessage], int]: (留言列表, 总数)
        
        Raises:
            NotFoundException: 房间不存在或无权访问（404）
        """
        # ← 修改：检查房间是否存在
        room = await crud_room.get(self.db, room_id)
        if room is None:
            raise RoomNotFoundException(f"Room ID: {room_id} 不存在")
        
        # ← 新增：权限校验（检查Room可见性，Message继承Room权限）
        self._check_room_visibility(room, user_id, role)
        
        # 2. 调用 CRUD 层获取留言
        messages, total = await crud_live_features.get_messages_by_room(
            self.db, 
            room_id, 
            page, 
            size, 
            since
        )
        
        logger.info(f"Retrieved {len(messages)} messages for room {room_id}, page {page}")
        return messages, total


    async def admin_list_messages(self, query, role) -> "AdminMessagePageResult":
        """PR 3: 管理端全局留言列表"""
        from app.schemas.live_features import AdminMessageItem, AdminMessagePageResult
        if not role or role.upper() not in ("ADMIN", "SUPERADMIN"):
            raise PermissionDeniedException("权限不足：仅管理员可执行此操作")
        rows, total, room_count, user_count = await crud_live_features.admin_list_messages(
            self.db,
            room_id=query.room_id,
            user_id=query.user_id,
            keyword=query.keyword,
            start_time=query.start_time,
            end_time=query.end_time,
            page=query.page,
            page_size=query.page_size,
        )
        from app.services.user_profile_client import fetch_user_profiles
        from app.core.deactivated_users import filter_deactivated_user_ids
        # N+1 修复：一次批量取所有用户资料（原为循环逐条查询）
        profiles = await fetch_user_profiles([msg.user_id for msg, _ in rows])
        deactivated_ids = await filter_deactivated_user_ids(msg.user_id for msg, _ in rows)
        items = []
        for msg, room_title in rows:
            profile = profiles.get(str(msg.user_id))
            is_deactivated = msg.user_id in deactivated_ids
            # 昵称双源兜底：用户资料 nickname → 留言 extra.user_display_name → 账号名
            extra = msg.extra or {}
            display_name = None
            if profile:
                display_name = profile.get("nickname") or profile.get("username")
            if not display_name:
                display_name = extra.get("user_display_name") if isinstance(extra, dict) else None
            avatar_url = profile.get("avatar_url") if profile else None
            if is_deactivated:
                from app.core.deactivated_users import DEACTIVATED_DISPLAY_NAME
                display_name = DEACTIVATED_DISPLAY_NAME
                avatar_url = None
            items.append(AdminMessageItem(
                id=msg.id, room_id=msg.room_id, user_id=msg.user_id,
                user_role=msg.user_role, content=msg.content,
                created_at=msg.created_at, extra=msg.extra,
                user_display_name=display_name,
                avatar_url=avatar_url,
                room_title=room_title,
            ))
        return AdminMessagePageResult(
            items=items, total=total, page=query.page, page_size=query.page_size,
            filter_summary={"room_count": room_count, "user_count": user_count},
        )


    async def admin_batch_delete(self, message_ids, role) -> tuple:
        """PR 3: 管理员批量删除留言（删除后失效涉及房间的留言缓存）"""
        if not role or role.upper() not in ("ADMIN", "SUPERADMIN"):
            raise PermissionDeniedException("权限不足")
        # 先取涉及房间（删除后需失效缓存，避免 C 端缓存残留已删留言）
        room_ids = await crud_live_features.get_message_room_ids(self.db, message_ids)
        deleted, failed = await crud_live_features.batch_delete_messages(self.db, message_ids)
        if room_ids:
            from app.core.redis_cache import invalidate_message_cache
            for room_id in room_ids:
                await invalidate_message_cache(room_id)
        return deleted, failed


    async def admin_clear_room_messages(self, room_id, role) -> int:
        """PR 3: 管理员清空房间留言"""
        if not role or role.upper() not in ("ADMIN", "SUPERADMIN"):
            raise PermissionDeniedException("权限不足")
        from app.crud import room as crud_room
        room = await crud_room.get(self.db, room_id)
        if room is None:
            from app.exceptions import RoomNotFoundException
            raise RoomNotFoundException(f"Room ID: {room_id} 不存在")
        deleted = await crud_live_features.clear_room_messages(self.db, room_id)
        return deleted

    def _check_message_delete_permission(
        self, message_user_id: uuid.UUID, current_user_id: uuid.UUID, role: Optional[str]
    ) -> None:
        """管理员可删任意留言，普通用户只可删自己的留言"""
        if role and role.upper() in ("ADMIN", "SUPERADMIN"):
            return
        if message_user_id != current_user_id:
            raise PermissionDeniedException("权限不足：只能删除自己的留言")

    async def delete_message(
        self,
        room_id: uuid.UUID,
        message_id: uuid.UUID,
        current_user_id: uuid.UUID,
        role: Optional[str],
    ) -> None:
        """删除留言（本人或管理员）"""
        room = await crud_room.get(self.db, room_id)
        if room is None:
            raise RoomNotFoundException(f"Room ID: {room_id} 不存在")

        message = await crud_live_features.get_message_by_id(self.db, message_id, room_id)
        if message is None:
            raise MessageNotFoundException(f"Message ID: {message_id} 不存在")

        self._check_message_delete_permission(message.user_id, current_user_id, role)
        await crud_live_features.soft_delete_message(self.db, message)
        from app.core.redis_cache import invalidate_message_cache
        await invalidate_message_cache(room_id)
        logger.info(f"User {current_user_id} deleted message {message_id} in room {room_id}")

