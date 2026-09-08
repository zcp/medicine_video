"""
LiveCore Service - Session CRUD Operations

This module contains all CRUD operations for LiveSession and SessionStatistics models,
providing data access layer functionality.
"""

import uuid
import logging
from typing import Optional, List, Tuple, Union

from pydantic.v1 import UUID4
from sqlalchemy import select, func, and_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.live_core import LiveSession, SessionStatistics, LiveSessionStatus, LiveRoom
from app.schemas.live_core import LiveSessionCreate, LiveSessionUpdate
from app.exceptions import SessionActionForbiddenException
from app.core.exceptions import DatabaseIntegrityException, DatabaseOperationException

# 设置日志
logger = logging.getLogger(__name__)


async def create_with_stats(db: AsyncSession, obj_in: Union[LiveSessionCreate, dict]) -> LiveSession:
    """
    创建一个新的LiveSession记录，并同时创建一个与之关联的、空的SessionStatistics记录
    (CRUD 层 - 学院派实现)
    
    Args:
        db: 数据库会话
        obj_in: LiveSession创建数据 (可以是Pydantic模型或字典)
        
    Returns:
        创建的LiveSession对象（包含关联的统计信息）
    """
    # 提取数据
    if isinstance(obj_in, dict):
        data = obj_in.copy()
        room_id_log = data.get('room_id')
        status_log = data.get('status')
        start_time_log = data.get('start_time')
        session_id_log = data.get('id', uuid.uuid4())
    else:
        data = obj_in.model_dump()
        room_id_log = getattr(obj_in, 'room_id', None)
        status_log = getattr(obj_in, 'status', None)
        start_time_log = getattr(obj_in, 'start_time', None)
        session_id_log = uuid.uuid4() # Pydantic模型通常不带ID

    logger.info(f"开始创建直播session: room_id={room_id_log}, status={status_log}, start_time={start_time_log}")

    try:
        # 准备模型数据
        # LiveSession 模型字段: id, room_id, status, start_time, end_time, video_id, playback_url, playback_url_hash
        valid_fields = {
            'id',
            'room_id',
            'status',
            'start_time',
            'end_time',
            'video_id',
            'playback_url',
            'playback_url_hash',
        }
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}
        
        # 创建LiveSession对象
        db_obj = LiveSession(**filtered_data)
        
        # 添加到数据库
        db.add(db_obj)
        await db.flush()  # 刷新以获取生成的ID
        
        logger.debug(f"LiveSession对象已创建: session_id={db_obj.id}")
        
        # 创建关联的空统计记录
        stats_obj = SessionStatistics(
            session_id=db_obj.id,
            peak_viewer_count=0,
            total_viewer_count=0,
            total_like_count=0,
            total_share_count=0
        )
        
        # 添加统计记录到数据库
        db.add(stats_obj)
        await db.commit()

        await db.refresh(db_obj)
        logger.info(f"直播会话创建事务已提交: session_id={db_obj.id}")

        logger.info(f"成功创建直播会话: session_id={db_obj.id}, room_id={room_id_log}")
        return db_obj
        
    except IntegrityError as e:
        await db.rollback()
        logger.error(
            f"创建直播会话失败（完整性错误）：room_id={room_id_log}, status={status_log}, error={e}",
            exc_info=True
        )
        raise DatabaseIntegrityException("创建会话时发生唯一键冲突")
        
    except Exception as e:
        await db.rollback()
        logger.error(
            f"创建直播会话失败（未知DB错误）：room_id={room_id_log}, status={status_log}, error={e}",
            exc_info=True
        )
        raise DatabaseOperationException(f"数据库操作失败: {e}")

# Alias for convenience as requested by prompt
create = create_with_stats


async def get(db: AsyncSession, session_id: uuid.UUID, user_id: Optional[uuid.UUID] = None) -> Optional[LiveSession]:
    """
    根据ID获取单个会话
    
    Args:
        db: 数据库会话
        session_id: 会话ID
        user_id: 可选的用户ID，用于权限验证
        
    Returns:
        LiveSession对象或None
    """
    logger.debug(f"查询会话: session_id={session_id}, user_id={user_id}")
    
    try:
        query = select(LiveSession).where(LiveSession.id == session_id)
        #if user_id:
        #    query = query.join(LiveRoom).where(LiveRoom.user_id == user_id)
        
        result = await db.execute(query)
        session = result.scalar_one_or_none()
        
        if session:
            logger.debug(f"找到会话: session_id={session_id}, room_id={session.room_id}")
        else:
            logger.debug(f"会话不存在: session_id={session_id}")
        
        return session
        
    except Exception as e:
        logger.error(f"查询会话失败: session_id={session_id}, user_id={user_id}, error={str(e)}", exc_info=True)
        raise


async def get_with_stats(db: AsyncSession, session_id: uuid.UUID, user_id: Optional[uuid.UUID] = None) -> Optional[LiveSession]:
    """
    根据ID获取单个场次，并预加载关联的统计数据
    
    Args:
        db: 数据库会话
        session_id: 会话ID
        user_id: 可选的用户ID，用于权限验证
        
    Returns:
        包含统计信息的LiveSession对象或None
    """
    logger.debug(f"查询会话详情(含统计): session_id={session_id}, user_id={user_id}")
    
    try:
        query = select(LiveSession).options(selectinload(LiveSession.statistics))
        
        #if user_id:
            # 如果提供user_id，通过房间ID验证用户权限
        #    query = query.join(LiveRoom).where(LiveRoom.user_id == user_id)
        
        query = query.where(LiveSession.id == session_id)
        
        result = await db.execute(query)
        session = result.scalar_one_or_none()
        
        if session:
            logger.debug(f"找到会话详情: session_id={session_id}, room_id={session.room_id}")
        else:
            logger.debug(f"会话详情不存在: session_id={session_id}")
        
        return session
        
    except Exception as e:
        logger.error(f"查询会话详情失败: session_id={session_id}, user_id={user_id}, error={str(e)}", exc_info=True)
        raise


async def get_latest_scheduled_session(db: AsyncSession, room_id: uuid.UUID) -> Optional[LiveSession]:
    """获取指定房间最新的、状态为'scheduled'的会话"""
    logger.debug(f"查询房间最新计划会话: room_id={room_id}")
    
    try:
        result = await db.execute(
            select(LiveSession)
            .where(
                and_(
                    LiveSession.room_id == room_id,
                    LiveSession.status == LiveSessionStatus.SCHEDULED
                )
            )
            .order_by(LiveSession.created_at.desc())
            .limit(1)
        )
        session = result.scalar_one_or_none()
        
        if session:
            logger.debug(f"找到最新计划会话: session_id={session.id}, room_id={room_id}")
        else:
            logger.debug(f"房间无计划会话: room_id={room_id}")
        
        return session
        
    except Exception as e:
        logger.error(f"查询房间最新计划会话失败: room_id={room_id}, error={str(e)}", exc_info=True)
        raise


async def get_live_session_by_room(db: AsyncSession, room_id: uuid.UUID) -> Optional[LiveSession]:
    """获取指定房间内状态为'live'的会话"""
    logger.debug(f"查询房间直播会话: room_id={room_id}")
    
    try:
        result = await db.execute(
            select(LiveSession)
            .where(
                and_(
                    LiveSession.room_id == room_id,
                    LiveSession.status == LiveSessionStatus.LIVE
                )
            )
        )
        session = result.scalar_one_or_none()
        
        if session:
            logger.debug(f"找到直播会话: session_id={session.id}, room_id={room_id}")
        else:
            logger.debug(f"房间无直播会话: room_id={room_id}")
        
        return session
        
    except Exception as e:
        logger.error(f"查询房间直播会话失败: room_id={room_id}, error={str(e)}", exc_info=True)
        raise


async def get_by_room_and_playback_hash(
    db: AsyncSession,
    room_id: uuid.UUID,
    playback_url_hash: str,
) -> Optional[LiveSession]:
    """
    根据 (room_id, playback_url_hash) 获取单个会话（V6 去重幂等增量）
    只做纯查询，不做业务逻辑或权限检查。
    """
    logger.debug(
        f"根据 playback_url_hash 查询会话: room_id={room_id}, playback_url_hash={playback_url_hash}"
    )

    try:
        query = select(LiveSession).where(
            LiveSession.room_id == room_id,
            LiveSession.playback_url_hash == playback_url_hash,
        )
        result = await db.execute(query)
        session = result.scalar_one_or_none()

        if session:
            logger.debug(
                f"找到会话: session_id={session.id}, room_id={room_id}, playback_url_hash={playback_url_hash}"
            )
        else:
            logger.debug(
                f"未找到会话: room_id={room_id}, playback_url_hash={playback_url_hash}"
            )

        return session
    except Exception as e:
        logger.error(
            f"根据 playback_url_hash 查询会话失败: room_id={room_id}, playback_url_hash={playback_url_hash}, error={e}",
            exc_info=True,
        )
        raise DatabaseOperationException(f"数据库查询失败: {e}")
        
    except Exception as e:
        logger.error(f"查询房间直播会话失败: room_id={room_id}, error={str(e)}", exc_info=True)
        raise


async def get_multi_by_room_and_total(
    db: AsyncSession, 
    room_id: uuid.UUID, 
    skip: int = 0, 
    limit: int = 10,
    user_id: Optional[uuid.UUID] = None
) -> Tuple[List[LiveSession], int]:
    """
    分页获取指定room_id的所有场次列表，并返回总数
    
    Args:
        db: 数据库会话
        room_id: 房间ID
        skip: 跳过的记录数
        limit: 限制返回的记录数
        user_id: 可选的用户ID，用于权限验证
        
    Returns:
        (会话列表, 总数)的元组
    """
    logger.debug(f"分页查询房间会话列表: room_id={room_id}, skip={skip}, limit={limit}, user_id={user_id}")
    
    try:
        # 如果提供user_id，验证房间权限
        #if user_id:
        #    room_query = select(LiveRoom).where(
        #        and_(LiveRoom.id == room_id, LiveRoom.user_id == user_id)
        #    )
        #    room = await db.execute(room_query)
        #    if not room.scalar_one_or_none():
        #        # 如果房间不属于当前用户，返回空结果
        #        logger.debug(f"房间不属于当前用户: room_id={room_id}, user_id={user_id}")
        #        return [], 0
        
        # 获取总数
        count_result = await db.execute(
            select(func.count(LiveSession.id)).where(LiveSession.room_id == room_id)
        )
        total = count_result.scalar()
        
        # 获取分页数据
        result = await db.execute(
            select(LiveSession)
            .where(LiveSession.room_id == room_id)
            .order_by(LiveSession.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        sessions = result.scalars().all()
        
        logger.debug(f"分页查询房间会话列表完成: room_id={room_id}, 返回{len(sessions)}条记录, 总数={total}")
        return list(sessions), total
        
    except Exception as e:
        logger.error(f"分页查询房间会话列表失败: room_id={room_id}, skip={skip}, limit={limit}, user_id={user_id}, error={str(e)}", exc_info=True)
        raise


async def update(
    db: AsyncSession,
    db_obj: LiveSession,
    obj_in: Union[LiveSessionUpdate, dict],
) -> LiveSession:
    """
    更新场次信息
    
    Args:
        db: 数据库会话
        db_obj: 要更新的LiveSession对象
        obj_in: 更新数据
        
    Returns:
        更新后的LiveSession对象
    """
    logger.info(f"开始更新直播会话: session_id={db_obj.id}, room_id={db_obj.room_id}")
    
    # 提取日志变量
    session_id_log = db_obj.id
    
    try:
        # 获取更新数据，排除未设置的字段
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)
        logger.debug(f"更新字段: {list(update_data.keys())}")
        
        # 更新字段
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        # 提交更改
        await db.commit()
        await db.refresh(db_obj)

        logger.info(f"直播会话更新事务已提交: session_id={db_obj.id}")

        logger.info(f"成功更新直播会话: session_id={db_obj.id}, room_id={db_obj.room_id}")
        return db_obj
        
    except IntegrityError as e:
        await db.rollback()
        logger.error(f"更新直播会话失败（完整性错误）: session_id={session_id_log}, error={e}", exc_info=True)
        raise DatabaseIntegrityException("更新会话时发生冲突")

    except Exception as e:
        await db.rollback()
        logger.error(f"更新直播会话失败: session_id={session_id_log}, error={e}", exc_info=True)
        raise DatabaseOperationException(f"数据库操作失败: {e}")


async def remove(db: AsyncSession, db_obj: LiveSession) -> LiveSession:
    """
    删除场次（由于数据库设置了级联，关联的session_statistics会被自动删除）
    
    Args:
        db: 数据库会话
        db_obj: 要删除的LiveSession对象
        
    Returns:
        被删除的LiveSession对象
    """
    logger.info(f"开始删除直播会话: session_id={db_obj.id}, room_id={db_obj.room_id}")
    
    # 提取日志变量
    session_id_log = db_obj.id
    
    try:
        await db.delete(db_obj)
        await db.commit()
        logger.info(f"直播会话删除成功: session_id={session_id_log}, room_id={db_obj.room_id}")
        return db_obj
        
    except IntegrityError as e:
        await db.rollback()
        logger.error(f"删除直播会话失败（完整性错误）: session_id={session_id_log}, error={e}", exc_info=True)
        raise DatabaseIntegrityException("删除会话时发生完整性冲突")

    except Exception as e:
        await db.rollback()
        logger.error(f"删除直播会话失败: session_id={session_id_log}, error={e}", exc_info=True)
        raise DatabaseOperationException(f"数据库操作失败: {e}")
