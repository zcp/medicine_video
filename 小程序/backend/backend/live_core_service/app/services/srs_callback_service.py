"""
LiveCore Service - SRS Callback Service

This module contains the service layer for handling SRS callback events,
providing business logic for on_publish and on_unpublish callbacks.
"""

import uuid
import logging
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import room as crud_room
from app.crud import session as crud_session
from app.models.live_core import LiveRoom, LiveSession, LiveSessionStatus
from app.schemas.live_core import LiveSessionCreate, LiveSessionUpdate
from app.tasks.session_processing import post_stream_processing_task

# 设置日志
logger = logging.getLogger(__name__)


class RoomNotFoundException(Exception):
    """房间不存在异常"""
    pass


class SrsCallbackService:
    """SRS回调服务类"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def handle_on_publish(self, stream_key: str) -> LiveSession:
        """
        处理on_publish回调
        
        Args:
            stream_key: 推流密钥
            
        Returns:
            LiveSession对象
            
        Raises:
            RoomNotFoundException: 房间不存在时抛出
        """
        logger.info(f"处理on_publish回调: stream_key={stream_key}")
        
        # 根据stream_key获取房间
        room = await crud_room.get_by_stream_key(self.db, stream_key=stream_key)
        if not room:
            logger.warning(f"房间不存在: stream_key={stream_key}")
            raise RoomNotFoundException(f"Room with stream_key {stream_key} not found")
        
        logger.info(f"找到房间: room_id={room.id}, title={room.title}")
        
        # --- 新增的幂等性检查逻辑 ---
        # 2. 检查是否已有 'live' 状态的会话
        existing_live_session = await crud_session.get_live_session_by_room(self.db, room_id=room.id)
        if existing_live_session:
            logger.warning(f"收到重复的on_publish回调，会话已处于live状态: session_id={existing_live_session.id}")
            # 如果已存在，直接返回当前正在直播的会话，不进行任何操作
            return existing_live_session
        # --- 幂等性检查结束 ---
        
        # 查找计划中的会话
        scheduled_session = await crud_session.get_latest_scheduled_session(
            self.db, room_id=room.id
        )
        
        current_time = datetime.now(timezone.utc)
        
        if scheduled_session:
            # 如果找到计划中的会话，更新其状态为live
            logger.info(f"找到计划中会话: session_id={scheduled_session.id}")
            
            session_update = LiveSessionUpdate(
                status=LiveSessionStatus.LIVE,
                start_time=current_time
            )
            
            updated_session = await crud_session.update(
                self.db, db_obj=scheduled_session, obj_in=session_update
            )
            
            logger.info(f"成功更新会话状态为live: session_id={updated_session.id}")
            return updated_session
            
        else:
            # 如果没有找到计划中的会话，创建新的live会话
            logger.info(f"未找到计划中会话，创建新的live会话: room_id={room.id}")
            
            session_create = LiveSessionCreate(
                room_id=room.id,
                status=LiveSessionStatus.LIVE,
                start_time=current_time,
                end_time=None,
                video_id=None
            )
            
            new_session = await crud_session.create_with_stats(
                self.db, obj_in=session_create
            )
            
            logger.info(f"成功创建新的live会话: session_id={new_session.id}")
            return new_session
    
    async def handle_on_unpublish(self, stream_key: str) -> Optional[LiveSession]:
        """
        处理on_unpublish回调
        
        Args:
            stream_key: 推流密钥
            
        Returns:
            更新后的LiveSession对象，如果没有找到则返回None
            
        Raises:
            RoomNotFoundException: 房间不存在时抛出
        """
        logger.info(f"处理on_unpublish回调: stream_key={stream_key}")
        
        # 根据stream_key获取房间
        room = await crud_room.get_by_stream_key(self.db, stream_key=stream_key)
        if not room:
            logger.warning(f"房间不存在: stream_key={stream_key}")
            raise RoomNotFoundException(f"Room with stream_key {stream_key} not found")
        
        logger.info(f"找到房间: room_id={room.id}, title={room.title}")
        
        # 获取当前正在直播的会话
        live_session = await crud_session.get_live_session_by_room(
            self.db, room_id=room.id
        )
        
        if not live_session:
            logger.warning(f"未找到正在直播的会话: room_id={room.id}")
            return None
        
        logger.info(f"找到正在直播的会话: session_id={live_session.id}")
        
        # 更新会话状态为finished并记录结束时间
        current_time = datetime.now(timezone.utc)
        session_update = LiveSessionUpdate(
            status=LiveSessionStatus.FINISHED,
            end_time=current_time
        )
        
        updated_session = await crud_session.update(
            self.db, db_obj=live_session, obj_in=session_update
        )
        
        logger.info(f"成功更新会话状态为finished: session_id={updated_session.id}")
        
        # 启动后台处理任务
        try:
            post_stream_processing_task.delay(str(updated_session.id))
            logger.info(f"成功启动后台处理任务: session_id={updated_session.id}")
        except Exception as e:
            logger.error(f"启动后台处理任务失败: session_id={updated_session.id}, error={e}")
        
        return updated_session 