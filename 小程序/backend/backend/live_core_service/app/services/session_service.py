"""
LiveCore Service - Session Business Logic Service

This module contains the SessionService class that encapsulates all business logic
related to LiveSession operations, providing a clean separation between
HTTP endpoints and data access layers.
"""

import uuid
import logging
import os
from typing import List, Tuple, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.live_core import LiveSession, LiveSessionStatus, LiveRoom
from app.schemas.live_core import ScheduledSessionCreate, LiveSessionCreate, LiveSessionUpdate
from sqlalchemy import delete

from app.crud import session as crud_session, room as crud_room
from app.exceptions import (
    SessionNotFoundException,
    SessionActionForbiddenException,
    RoomNotFoundException,
    NotFoundException,
    PermissionDeniedException
)
from app.models.user_behavior import UserSubscription, SubscriptionTargetType
from app.services.utils_playback import calc_playback_url_hash

# 设置日志
logger = logging.getLogger(__name__)


class SessionService:
    """
    Session业务逻辑服务类
    
    负责处理所有与LiveSession相关的业务逻辑，包括：
    - 创建计划场次
    - 获取场次详情和列表
    - 更新场次信息
    - 删除场次
    
    该服务层保持框架无关性，不包含HTTP相关的逻辑。
    """
    
    def __init__(self, db: AsyncSession):
        """
        初始化SessionService
        
        Args:
            db: 异步数据库会话
        """
        self.db = db

    def _check_room_visibility(
        self,
        room: LiveRoom,
        user_id: Optional[uuid.UUID],
        role: Optional[str]
    ) -> None:
        """
        房间读可见性（文档 18）：is_private=true 为不公开（unlisted）。
        持有 room_id 即可读；发现层过滤由列表/搜索 SQL 负责。
        """
        if room.is_private and role in ['ADMIN', 'SUPERADMIN'] and user_id and room.user_id != user_id:
            logger.info(
                f"Admin查看不公开房间: admin={user_id}, role={role}, "
                f"room_id={room.id}, owner={room.user_id}"
            )
        return

    def _check_write_permission(
        self,
        room: LiveRoom,
        user_id: uuid.UUID,
        role: str
    ) -> None:
        """
        写操作权限校验（修改/删除）
        
        Args:
            room: 直播间对象
            user_id: 当前用户的public_id
            role: 当前用户的角色
            
        Raises:
            PermissionDeniedException: 无权修改（403）
        """
        # 管理员：上帝视角通过
        if role in ['ADMIN', 'SUPERADMIN']:
            return
        
        # 资源创建者：通过
        if room.user_id == user_id:
            return
        
        # 其他用户：拒绝（返回403，因为已登录）
        raise PermissionDeniedException(
            "You don't have permission to modify this room"
        )
    
    async def create_scheduled_session(
        self, 
        room_id: uuid.UUID, 
        session_in: ScheduledSessionCreate,
        user_id: uuid.UUID,
        role: str  # ← 新增：权限参数
    ) -> LiveSession:
        """
        为指定房间创建一个计划中的直播场次
        
        Args:
            room_id: 房间ID
            session_in: 计划场次创建数据
            user_id: 当前用户的public_id（从JWT的user_id字段提取）
            role: 当前用户的角色
            
        Returns:
            创建的LiveSession对象
            
        Raises:
            RoomNotFoundException: 当房间不存在时
            PermissionDeniedException: 无权在此房间创建场次（403）
        """
        logger.info(f"开始创建计划场次: room_id={room_id}, user_id={user_id}, role={role}, start_time={session_in.start_time}")
        
        try:
            # ← 修改：验证房间是否存在（不传递权限参数，因为详情查询需要先检查可见性）
            room = await crud_room.get(db=self.db, room_id=room_id)
            if room is None:
                logger.warning(f"房间不存在: room_id={room_id}")
                raise RoomNotFoundException()
            
            # ← 新增：权限校验（检查Room写权限）
            self._check_write_permission(room, user_id, role)
            
            # 2. 创建LiveSessionCreate对象
            session_create = LiveSessionCreate(
                room_id=room_id,
                status=LiveSessionStatus.SCHEDULED,
                start_time=session_in.start_time,
                end_time=None,
                video_id=None
            )
            
            # 3. 调用CRUD层创建会话和统计信息
            new_session = await crud_session.create_with_stats(db=self.db, obj_in=session_create)
            
            logger.info(f"成功创建计划场次: session_id={new_session.id}, room_id={room_id}")
            return new_session
            
        except (RoomNotFoundException, PermissionDeniedException):
            # 重新抛出业务异常，不记录额外日志
            raise
        except Exception as e:
            logger.error(f"创建计划场次失败: room_id={room_id}, user_id={user_id}, role={role}, start_time={session_in.start_time}, error={str(e)}", exc_info=True)
            raise
    
    async def get_sessions_by_room(
        self, 
        room_id: uuid.UUID, 
        page: int, 
        size: int,
        user_id: Optional[uuid.UUID] = None,
        role: Optional[str] = None  # ← 新增：权限参数
    ) -> Tuple[List[LiveSession], int]:
        """
        获取指定房间的直播场次列表（支持匿名访问，继承Room权限）
        
        Args:
            room_id: 房间ID
            page: 页码
            size: 每页大小
            user_id: 当前用户的public_id（匿名时为None）
            role: 当前用户的角色（匿名时为None）
            
        Returns:
            (会话列表, 总数)的元组
            
        Raises:
            NotFoundException: 当房间不存在或无权访问时（404）
        """
        logger.info(f"开始获取房间场次列表: room_id={room_id}, page={page}, size={size}, user_id={user_id}, role={role}")
        
        try:
            # ← 修改：验证房间是否存在并检查可见性
            room = await crud_room.get(db=self.db, room_id=room_id)
            if room is None:
                logger.warning(f"房间不存在: room_id={room_id}")
                raise RoomNotFoundException()
            
            # ← 新增：权限校验（检查Room可见性，Session继承Room权限）
            self._check_room_visibility(room, user_id, role)
            
            # 2. 计算skip值
            skip = (page - 1) * size
            
            # 3. 调用CRUD层获取场次列表和总数
            sessions, total = await crud_session.get_multi_by_room_and_total(
                db=self.db,
                room_id=room_id,
                skip=skip,
                limit=size,
                user_id=user_id
            )
            
            logger.info(f"成功获取房间场次列表: room_id={room_id}, 返回{len(sessions)}条记录, 总数={total}")
            return sessions, total
            
        except (RoomNotFoundException, NotFoundException):
            # 重新抛出业务异常，不记录额外日志
            raise
        except Exception as e:
            logger.error(f"获取房间场次列表失败: room_id={room_id}, page={page}, size={size}, user_id={user_id}, role={role}, error={str(e)}", exc_info=True)
            raise
    
    async def get_session_details(
        self, 
        session_id: uuid.UUID, 
        user_id: Optional[uuid.UUID] = None,
        role: Optional[str] = None  # ← 新增：权限参数
    ) -> LiveSession:
        """
        获取单场直播的详细信息（包含统计信息，支持匿名访问，继承Room权限）
        
        Args:
            session_id: 会话ID
            user_id: 当前用户的public_id（匿名时为None）
            role: 当前用户的角色（匿名时为None）
            
        Returns:
            包含统计信息的LiveSession对象
            
        Raises:
            SessionNotFoundException: 当会话不存在时
            NotFoundException: 当房间不存在或无权访问时（404）
        """
        logger.info(f"开始获取直播会话详情: session_id={session_id}, user_id={user_id}, role={role}")
        
        try:
            # ← 修改：调用CRUD层获取会话和统计信息（不传递权限参数）
            session = await crud_session.get_with_stats(db=self.db, session_id=session_id)
            
            # 检查会话是否存在
            if session is None:
                logger.warning(f"直播会话不存在: session_id={session_id}")
                raise SessionNotFoundException()
            
            # ← 新增：通过Session关联Room，检查Room可见性（Session继承Room权限）
            room = await crud_room.get(db=self.db, room_id=session.room_id)
            if room is None:
                logger.warning(f"会话关联的房间不存在: session_id={session_id}, room_id={session.room_id}")
                raise RoomNotFoundException()
            
            self._check_room_visibility(room, user_id, role)
            
            logger.info(f"成功获取直播会话详情: session_id={session_id}, room_id={session.room_id}")
            return session
            
        except (SessionNotFoundException, RoomNotFoundException, NotFoundException):
            # 重新抛出业务异常，不记录额外日志
            raise
        except Exception as e:
            logger.error(f"获取直播会话详情失败: session_id={session_id}, user_id={user_id}, role={role}, error={str(e)}", exc_info=True)
            raise
    
    async def update_scheduled_session_info(
        self, 
        session_id: uuid.UUID, 
        session_update: LiveSessionUpdate,
        user_id: uuid.UUID,
        role: str  # ← 新增：权限参数
    ) -> LiveSession:
        """
        更新会话信息（支持计划场次更新和回放地址更新）
        
        Args:
            session_id: 会话ID
            session_update: 更新数据
            user_id: 当前用户的public_id（从JWT的user_id字段提取）
            role: 当前用户的角色
            
        Returns:
            更新后的LiveSession对象
            
        Raises:
            SessionNotFoundException: 当会话不存在时
            PermissionDeniedException: 无权修改此会话（403）
            SessionActionForbiddenException: 当会话状态不允许修改时
        """
        logger.info(f"开始更新会话信息: session_id={session_id}, user_id={user_id}, role={role}")
        
        try:
            # ← 修改：获取会话对象（不传递权限参数）
            session = await crud_session.get(db=self.db, session_id=session_id)
            if session is None:
                logger.warning(f"直播会话不存在: session_id={session_id}")
                raise SessionNotFoundException()
            
            # ← 新增：通过Session关联Room，检查Room写权限
            room = await crud_room.get(db=self.db, room_id=session.room_id)
            if room is None:
                logger.warning(f"会话关联的房间不存在: session_id={session_id}, room_id={session.room_id}")
                raise RoomNotFoundException()
            
            self._check_write_permission(room, user_id, role)
            
            # 2. 业务逻辑检查
            update_data = session_update.model_dump(exclude_unset=True)
            is_updating_playback = "playback_url" in update_data
            is_updating_others = any(k != "playback_url" for k in update_data.keys())

            # 检查常规字段更新（需 SCHEDULED 状态）
            #if is_updating_others:
            #    if session.status != LiveSessionStatus.SCHEDULED:
            #        logger.warning(f"无法修改非计划状态的场次信息: session_id={session_id}, status={session.status}")
            #        raise SessionActionForbiddenException("无法修改正在直播或已结束场次的计划信息")

            # 检查回放地址更新（需 READY 或 FINISHED 状态）
            if is_updating_playback:
                #if session.status not in (LiveSessionStatus.READY, LiveSessionStatus.FINISHED):
                #    logger.warning(
                #        "无法在当前状态更新回放地址: session_id=%s, status=%s",
                #        session_id,
                #        session.status,
                #    )
                #    raise SessionActionForbiddenException("仅允许在 ready 或 finished 状态下更新 playback_url")

                # V6：同步维护 playback_url_hash
                #new_url = update_data.get("playback_url")
                #update_data["playback_url_hash"] = calc_playback_url_hash(new_url)
                # V6：同步维护 playback_url_hash；清空时置为 None 避免唯一约束冲突
                new_url = update_data.get("playback_url")
                if new_url is None or (isinstance(new_url, str) and not new_url.strip()):
                    update_data["playback_url"] = None
                    update_data["playback_url_hash"] = None
                else:
                    update_data["playback_url_hash"] = calc_playback_url_hash(new_url)
            # 3. 调用CRUD层更新（允许 obj_in 为 dict）
            updated_session = await crud_session.update(db=self.db, db_obj=session, obj_in=update_data)

            logger.info(f"成功更新会话信息: session_id={session_id}, room_id={updated_session.room_id}")
            return updated_session
            
        except (SessionNotFoundException, RoomNotFoundException, PermissionDeniedException, SessionActionForbiddenException):
            # 重新抛出业务异常，不记录额外日志
            raise
        except Exception as e:
            logger.error(f"更新会话失败: session_id={session_id}, user_id={user_id}, role={role}, error={str(e)}", exc_info=True)
            raise
    
    async def auto_generate_playback_url(self, session_id: uuid.UUID) -> Optional[LiveSession]:
        """
        自动生成回放地址（用于后台任务）
        条件：Status=READY, VideoID!=None, PlaybackURL=None
        """
        try:
            session = await crud_session.get(db=self.db, session_id=session_id)
            if not session:
                return None
                
            if session.status == LiveSessionStatus.READY and session.video_id and session.playback_url is None:
                # 生成回放地址
                base_url = os.getenv("PLAYBACK_BASE_URL", "http://localhost:8000")
                generated_url = f"{base_url}/media/videos/{session.video_id}/playlist.m3u8"

                # 更新数据库（V6：同步维护 hash）
                session.playback_url = generated_url
                session.playback_url_hash = calc_playback_url_hash(generated_url)
                await self.db.commit()
                await self.db.refresh(session)
                logger.info(f"自动生成回放地址成功: session_id={session_id}, url={generated_url}")
                return session
                
            return session
        except Exception as e:
            logger.error(f"自动生成回放地址失败: session_id={session_id}, error={str(e)}", exc_info=True)
            raise
    
    async def delete_session(
        self, 
        session_id: uuid.UUID, 
        user_id: uuid.UUID,
        role: str  # ← 新增：权限参数
    ) -> LiveSession:
        """
        删除指定的直播场次
        
        Args:
            session_id: 会话ID
            user_id: 当前用户的public_id（从JWT的user_id字段提取）
            role: 当前用户的角色
            
        Returns:
            被删除的LiveSession对象
            
        Raises:
            SessionNotFoundException: 当会话不存在时
            PermissionDeniedException: 无权删除此会话（403）
            SessionActionForbiddenException: 当会话正在直播时
        """
        logger.info(f"开始删除计划场次: session_id={session_id}, user_id={user_id}, role={role}")
        
        try:
            # ← 修改：获取会话对象（不传递权限参数）
            session = await crud_session.get(db=self.db, session_id=session_id)
            if session is None:
                logger.warning(f"直播会话不存在: session_id={session_id}")
                raise SessionNotFoundException()
            
            # ← 新增：通过Session关联Room，检查Room写权限
            room = await crud_room.get(db=self.db, room_id=session.room_id)
            if room is None:
                logger.warning(f"会话关联的房间不存在: session_id={session_id}, room_id={session.room_id}")
                raise RoomNotFoundException()
            
            self._check_write_permission(room, user_id, role)
            
            # 2. 业务逻辑检查：不能删除正在直播的场次
            if session.status == LiveSessionStatus.LIVE:
                logger.warning(f"无法删除正在直播的场次: session_id={session_id}, status={session.status}")
                raise SessionActionForbiddenException("无法删除正在直播的场次")

            # 16-D4：删场次前物理清除该场次内容订阅（与 delete_room_related 同风格）
            sub_result = await self.db.execute(
                delete(UserSubscription).where(
                    UserSubscription.target_type == SubscriptionTargetType.SESSION,
                    UserSubscription.target_id == session_id,
                )
            )
            logger.info(
                "删场次级联：已清 session 订阅 session_id=%s rowcount=%s",
                session_id,
                sub_result.rowcount,
            )
            
            # 3. 调用CRUD层删除
            deleted_session = await crud_session.remove(db=self.db, db_obj=session)
            
            logger.info(f"成功删除计划场次: session_id={session_id}, room_id={deleted_session.room_id}")
            return deleted_session
            
        except (SessionNotFoundException, RoomNotFoundException, PermissionDeniedException, SessionActionForbiddenException):
            # 重新抛出业务异常，不记录额外日志
            raise
        except Exception as e:
            logger.error(f"删除计划场次失败: session_id={session_id}, user_id={user_id}, role={role}, error={str(e)}", exc_info=True)
            raise 