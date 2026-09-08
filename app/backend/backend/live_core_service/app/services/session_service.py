"""
LiveCore Service - Session Business Logic Service

This module contains the SessionService class that encapsulates all business logic
related to LiveSession operations, providing a clean separation between
HTTP endpoints and data access layers.
"""

import uuid
import logging
import os
from datetime import datetime, timezone
from typing import List, Tuple, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.live_core import LiveSession, LiveSessionStatus, SourceType, LiveRoom
from app.schemas.live_core import ScheduledSessionCreate, LiveSessionCreate, LiveSessionUpdate
from app.crud import session as crud_session, room as crud_room
from app.exceptions import (
    SessionNotFoundException,
    SessionActionForbiddenException,
    RoomNotFoundException,
    NotFoundException,
    PermissionDeniedException,
    ConflictException,
)
from app.core.permissions import check_room_visibility, check_room_owner_or_admin
from app.services.utils_playback import calc_playback_url_hash

# 设置日志
logger = logging.getLogger(__name__)


# V15：external 场次手动状态流转白名单矩阵（V2.0 修订）
# scheduled → live(开播) / ready(直接发回放)
# live → finished(停播) / ready(转回放)
# finished → live(恢复开播) / ready(发布回放)
# ready 为终态（回放已公开，不支持回转直播/预告）
# 已删除：live→scheduled（回预告后开播时间无法定义）、ready→live（回放地址≠直播地址）
_ALLOWED_EXTERNAL_TRANSITIONS = {
    LiveSessionStatus.SCHEDULED: {LiveSessionStatus.LIVE, LiveSessionStatus.READY},
    LiveSessionStatus.LIVE: {LiveSessionStatus.FINISHED, LiveSessionStatus.READY},
    LiveSessionStatus.FINISHED: {LiveSessionStatus.LIVE, LiveSessionStatus.READY},
    LiveSessionStatus.READY: set(),
}


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
        统一的房间可见性校验逻辑（Session继承Room权限）

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

    def _check_write_permission(
        self,
        room: LiveRoom,
        user_id: uuid.UUID,
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

            # V15：三态创建
            requested_status = session_in.status or LiveSessionStatus.SCHEDULED
            # 创建初始状态仅允许 scheduled/live/ready（finished/processing/error 由流转产生，不能作为初始状态）
            if requested_status not in (
                LiveSessionStatus.SCHEDULED,
                LiveSessionStatus.LIVE,
                LiveSessionStatus.READY,
            ):
                raise SessionActionForbiddenException("创建场次初始状态仅允许 scheduled/live/ready")

            start_time = session_in.start_time
            if requested_status == LiveSessionStatus.LIVE:
                # 创建即开播：start_time 强制取当前时间，end_time 为空
                start_time = datetime.now(timezone.utc)

            # 2. 创建LiveSessionCreate对象（playback_url 对所有场次均为必填）
            session_create = LiveSessionCreate(
                room_id=room_id,
                status=requested_status,
                start_time=start_time,
                end_time=None,
                video_id=None,
                playback_url=session_in.playback_url,
                source_type=session_in.source_type or SourceType.EXTERNAL,
            )
            # 计算 playback_url_hash 用于幂等去重（与导入回放保持一致）
            if session_in.playback_url:
                session_create.playback_url_hash = calc_playback_url_hash(session_in.playback_url)
            
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

            # V15：惰性补转（external scheduled 到期 → live），在返回前执行以保证最新状态
            await self.lazy_promote_if_due(session)

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
            requested_status = update_data.get("status")
            requested_status_value = (
                requested_status.value
                if hasattr(requested_status, "value")
                else requested_status
            )

            # V15（方案A）：external 场次的状态切换统一转发到 switch_external_status
            # （状态切换场景下时间字段由系统维护，start_time/end_time 不随 PATCH 传入）
            if session.source_type == SourceType.EXTERNAL and requested_status is not None:
                return await self.switch_external_status(
                    session_id=session_id,
                    target=LiveSessionStatus(requested_status_value),
                    user_id=user_id,
                    role=role,
                    new_playback_url=update_data.get("playback_url"),
                )

            if "video_id" in update_data:
                raise SessionActionForbiddenException("不允许手动修改视频ID")

            # 用户编辑接口只允许维护业务可编辑态：预告(scheduled)与回放(ready)。
            # live/finished/processing/error 由推流回调或后台任务写入，不能由前端表单直接写入。
            if requested_status is not None:
                if requested_status_value not in (
                    LiveSessionStatus.SCHEDULED.value,
                    LiveSessionStatus.READY.value,
                ):
                    logger.warning(
                        "用户接口禁止写入系统态: session_id=%s, current=%s, requested=%s",
                        session_id,
                        session.status,
                        requested_status_value,
                    )
                    raise SessionActionForbiddenException("不允许手动修改为该场次状态")

                if requested_status_value == LiveSessionStatus.SCHEDULED.value:
                    if session.status != LiveSessionStatus.SCHEDULED:
                        raise SessionActionForbiddenException("仅预告场次允许保持为预告状态")

                if requested_status_value == LiveSessionStatus.READY.value:
                    effective_playback_url = update_data.get("playback_url", session.playback_url)
                    if not effective_playback_url or not str(effective_playback_url).strip():
                        raise SessionActionForbiddenException("设置为回放状态必须提供回放地址")
                    if session.status not in (
                        LiveSessionStatus.SCHEDULED,
                        LiveSessionStatus.READY,
                        LiveSessionStatus.ERROR,
                    ):
                        raise SessionActionForbiddenException("当前状态不允许手动转为回放")

                update_data["status"] = LiveSessionStatus(requested_status_value)

            # 时间等计划信息只允许在预告/回放/错误修复场景下编辑。
            schedule_fields = {"start_time", "end_time"}
            if any(k in schedule_fields for k in update_data.keys()):
                if session.status not in (
                    LiveSessionStatus.SCHEDULED,
                    LiveSessionStatus.READY,
                    LiveSessionStatus.ERROR,
                ):
                    logger.warning(
                        "无法修改系统态场次信息: session_id=%s, status=%s",
                        session_id,
                        session.status,
                    )
                    raise SessionActionForbiddenException("当前场次状态不允许编辑计划信息")

            # 检查回放地址更新：只允许预告转回放、回放维护、错误后手动修复。
            if is_updating_playback:
                if session.status not in (
                    LiveSessionStatus.SCHEDULED,
                    LiveSessionStatus.READY,
                    LiveSessionStatus.ERROR,
                ):
                    logger.warning(
                        "无法在当前状态更新回放地址: session_id=%s, status=%s",
                        session_id,
                        session.status,
                    )
                    raise SessionActionForbiddenException("当前状态不允许手动更新回放地址")

                # V6：同步维护 playback_url_hash；清空时置为 None 避免唯一约束冲突
                new_url = update_data.get("playback_url")
                if new_url is None or (isinstance(new_url, str) and not new_url.strip()):
                    update_data["playback_url"] = None
                    update_data["playback_url_hash"] = None
                else:
                    update_data["playback_url_hash"] = calc_playback_url_hash(new_url)
                    if requested_status is None and session.status in (
                        LiveSessionStatus.SCHEDULED,
                        LiveSessionStatus.ERROR,
                    ):
                        update_data["status"] = LiveSessionStatus.READY
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
    
    async def switch_external_status(
        self,
        session_id: uuid.UUID,
        target: LiveSessionStatus,
        user_id: uuid.UUID,
        role: str,
        new_playback_url: Optional[str] = None,
    ) -> LiveSession:
        """
        external 场次手动状态流转（核心方法）

        Args:
            session_id: 场次ID
            target: 目标状态（scheduled/live/finished/ready）
            user_id: 当前用户 public_id
            role: 当前用户角色
            new_playback_url: 更新播放地址（转 live/ready 时允许；ready→live 必须提供）

        Returns:
            更新后的 LiveSession 对象

        Raises:
            SessionNotFoundException: 场次不存在
            RoomNotFoundException: 房间不存在
            PermissionDeniedException: 无写权限
            SessionActionForbiddenException: 非 external 场次 / 非法流转 / 守卫不满足
            ConflictException: 并发冲突（状态已被并发修改）
        """
        logger.info(f"切换external场次状态: session_id={session_id}, target={target}, user_id={user_id}")

        # 1. 查场次 + 房间，校验写权限
        session = await crud_session.get(db=self.db, session_id=session_id)
        if session is None:
            logger.warning(f"直播会话不存在: session_id={session_id}")
            raise SessionNotFoundException()

        room = await crud_room.get(db=self.db, room_id=session.room_id)
        if room is None:
            logger.warning(f"会话关联的房间不存在: session_id={session_id}, room_id={session.room_id}")
            raise RoomNotFoundException()

        self._check_write_permission(room, user_id, role)

        # 2. 仅 external 场次可手动流转（push 场次由推流回调独占）
        if session.source_type != SourceType.EXTERNAL:
            logger.warning(
                f"推流场次不支持手动切换状态: session_id={session_id}, source_type={session.source_type}"
            )
            raise SessionActionForbiddenException("推流场次不支持手动切换状态")

        # 3. 幂等：目标 == 当前状态直接返回
        if target == session.status:
            logger.info(f"目标状态与当前一致，幂等返回: session_id={session_id}, status={target}")
            return session

        # 4. 状态矩阵校验
        allowed_targets = _ALLOWED_EXTERNAL_TRANSITIONS.get(session.status, set())
        if target not in allowed_targets:
            logger.warning(
                f"非法状态流转: session_id={session_id}, from={session.status}, to={target}"
            )
            raise SessionActionForbiddenException(
                f"不允许从 {session.status.value} 切换到 {target.value}"
            )

        # 5. 守卫规则
        effective_playback_url = (
            new_playback_url if new_playback_url and str(new_playback_url).strip()
            else session.playback_url
        )
        if target in (LiveSessionStatus.LIVE, LiveSessionStatus.READY):
            if not effective_playback_url or not str(effective_playback_url).strip():
                logger.warning(f"切换为直播/回放状态必须提供播放地址: session_id={session_id}")
                raise SessionActionForbiddenException("切换为直播/回放状态必须提供播放地址")

        # 6. 时间字段维护 + 播放地址更新
        now = datetime.now(timezone.utc)
        update_data: dict = {"status": target}
        if target == LiveSessionStatus.LIVE:
            # 转 live：清空 end_time（重新开播语义）
            update_data["end_time"] = None
        elif target in (LiveSessionStatus.FINISHED, LiveSessionStatus.READY):
            # 转 finished/ready：end_time 为空则记录当前时间
            update_data["end_time"] = session.end_time if session.end_time is not None else now

        if new_playback_url and str(new_playback_url).strip():
            update_data["playback_url"] = new_playback_url
            update_data["playback_url_hash"] = calc_playback_url_hash(new_playback_url)

        # 7. 条件更新（并发保护：仅当当前状态未被并发修改时生效）
        affected = await crud_session.update_status_conditional(
            db=self.db,
            session_id=session_id,
            expected_status=session.status,
            update_data=update_data,
        )
        if affected == 0:
            logger.warning(
                f"场次状态已被并发修改，切换失败: session_id={session_id}, expected={session.status}"
            )
            raise ConflictException("场次状态已被并发修改，请刷新后重试")

        await self.db.refresh(session)
        logger.info(f"切换external场次状态成功: session_id={session_id}, status={target}")
        return session

    async def lazy_promote_if_due(self, session: LiveSession) -> None:
        """读取路径调用：external + scheduled + start_time<=now → 条件更新转 live。

        自动开播的 v1 形态（§4.6）：到点后"有人访问即自动开播"；
        无人访问时保持 scheduled（用户可手动开播），两者完全兼容。
        条件更新保证幂等与并发安全（rowcount=0 时跳过）。

        Args:
            session: 已加载的 LiveSession 对象（将被原地更新状态）
        """
        if (
            session.source_type == SourceType.EXTERNAL
            and session.status == LiveSessionStatus.SCHEDULED
            and session.start_time <= datetime.now(timezone.utc)
        ):
            affected = await crud_session.update_status_conditional(
                db=self.db,
                session_id=session.id,
                expected_status=LiveSessionStatus.SCHEDULED,
                update_data={"status": LiveSessionStatus.LIVE, "end_time": None},
            )
            if affected == 1:
                # ORM 状态同步：条件更新已 commit，直接同步对象属性避免返回 stale 状态
                session.status = LiveSessionStatus.LIVE
                logger.info(f"惰性补转：场次到期自动开播 session_id={session.id}")

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
            
            # 3. 数据关联治理（P0-1/P0-2）：先清理关联数据，再删主实体
            # 3.1 软下线指向该场次的焦点图，避免 target 悬挂引用（无外键多态关联）
            from app.crud.homepage_search import disable_featured_content_by_target
            await disable_featured_content_by_target(self.db, "session", session_id)
            # 3.2 硬删指向该场次的用户订阅（D5 定稿：与删房间路径对齐，参照 crud/room.py:601-607 同语义）
            from sqlalchemy import delete as sa_delete
            from app.models.user_behavior import UserSubscription, SubscriptionTargetType
            await self.db.execute(
                sa_delete(UserSubscription).where(
                    UserSubscription.target_type == SubscriptionTargetType.SESSION,
                    UserSubscription.target_id == session_id,
                )
            )
            
            # 4. 调用CRUD层删除
            deleted_session = await crud_session.remove(db=self.db, db_obj=session)
            
            logger.info(f"成功删除计划场次: session_id={session_id}, room_id={deleted_session.room_id}")
            return deleted_session
            
        except (SessionNotFoundException, RoomNotFoundException, PermissionDeniedException, SessionActionForbiddenException):
            # 重新抛出业务异常，不记录额外日志
            raise
        except Exception as e:
            logger.error(f"删除计划场次失败: session_id={session_id}, user_id={user_id}, role={role}, error={str(e)}", exc_info=True)
            raise 
