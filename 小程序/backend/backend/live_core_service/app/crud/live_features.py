"""
直播间 Tab 和留言功能的数据访问层 (CRUD Layer)

本模块提供 LiveRoomTab 和 LiveRoomMessage 模型的数据库操作函数。
遵循学院派架构规范：纯粹的数据访问层，不包含业务逻辑。
"""

import uuid
import logging
from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime

from sqlalchemy import select, func, and_, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError

# 导入模型 (学院派 ENUM 版)
from app.models.live_features import (
    LiveRoomTab, 
    LiveRoomMessage, 
    LiveRoomTabContentType, 
    LiveRoomMessageUserRole
)
# 导入 Schemas (学院派 ENUM 版)
from app.schemas.live_features import (
    LiveRoomTabCreate, 
    LiveRoomTabUpdate, 
    LiveRoomMessageCreateInternal
)

logger = logging.getLogger(__name__)


# ==================== LiveRoomTab CRUD 操作 ====================

async def create_tab(
    db: AsyncSession, 
    obj_in: LiveRoomTabCreate, 
    room_id: uuid.UUID
) -> LiveRoomTab:
    """
    创建新的直播间 Tab
    
    Args:
        db: 数据库会话
        obj_in: Tab 创建数据
        room_id: 直播间 ID（来自路径参数）
    
    Returns:
        LiveRoomTab: 创建的 Tab 对象
    
    Raises:
        IntegrityError: 数据库完整性错误（如外键约束失败）
        Exception: 其他数据库错误
    """
    # [学院派规范 5.1] 安全异步异常处理：提前提取日志变量
    room_id_str = str(room_id)
    tab_key = obj_in.tab_key
    
    try:
        # [学院派规范 5.1, 5.3.A] 应用层生成 UUID
        db_obj = LiveRoomTab(
            id=uuid.uuid4(),
            room_id=room_id,
            **obj_in.model_dump()
        )
        db.add(db_obj)
        
        # [学院派规范 5.1] 在 try 块中提交事务
        await db.commit()
        await db.refresh(db_obj)
        
        logger.info(f"Tab created successfully: id={db_obj.id}, room_id={room_id_str}, tab_key={tab_key}")
        return db_obj
        
    except IntegrityError as e:
        # [学院派规范 5.1] 回滚事务并记录错误
        await db.rollback()
        logger.error(f"IntegrityError creating tab for room_id={room_id_str}, tab_key={tab_key}: {str(e)}")
        raise
        
    except Exception as e:
        # [学院派规范 5.1] 捕获其他异常
        await db.rollback()
        logger.error(f"Error creating tab for room_id={room_id_str}, tab_key={tab_key}: {str(e)}")
        raise


async def get_tab(
    db: AsyncSession, 
    tab_id: uuid.UUID
) -> Optional[LiveRoomTab]:
    """
    根据 ID 获取单个 Tab
    
    用于 Service 层的更新/删除操作准备
    
    Args:
        db: 数据库会话
        tab_id: Tab ID
    
    Returns:
        Optional[LiveRoomTab]: Tab 对象，不存在则返回 None
    """
    stmt = select(LiveRoomTab).where(LiveRoomTab.id == tab_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_tab_with_room(
    db: AsyncSession, 
    tab_id: uuid.UUID
) -> Optional[LiveRoomTab]:
    """
    获取 Tab 并预加载 room 关系
    
    用于 Service 层的权限检查准备
    
    Args:
        db: 数据库会话
        tab_id: Tab ID
    
    Returns:
        Optional[LiveRoomTab]: Tab 对象（含 room 关系），不存在则返回 None
    """
    # [学院派规范 5.3.A] 使用 selectinload 避免 N+1 问题
    stmt = select(LiveRoomTab).options(
        selectinload(LiveRoomTab.room)
    ).where(LiveRoomTab.id == tab_id)
    
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_all_by_room_id(
    db: AsyncSession, 
    room_id: uuid.UUID, 
    skip: int = 0, 
    limit: int = 100
) -> Tuple[List[LiveRoomTab], int]:
    """
    分页获取指定直播间的所有 Tab（后台管理用）
    
    Args:
        db: 数据库会话
        room_id: 直播间 ID
        skip: 跳过的记录数
        limit: 返回的最大记录数
    
    Returns:
        Tuple[List[LiveRoomTab], int]: (Tab 列表, 总数)
    """
    # [学院派规范 5.3.A] 分页模式：先获取总数
    count_stmt = select(func.count(LiveRoomTab.id)).where(
        LiveRoomTab.room_id == room_id
    )
    count_result = await db.execute(count_stmt)
    total = count_result.scalar() or 0
    
    # [学院派规范 5.3.A] 分页模式：再获取数据列表
    stmt = select(LiveRoomTab).where(
        LiveRoomTab.room_id == room_id
    ).order_by(
        LiveRoomTab.sort_order.asc()
    ).offset(skip).limit(limit)
    
    result = await db.execute(stmt)
    items = result.scalars().all()
    
    return list(items), total


async def get_active_by_room_id(
    db: AsyncSession, 
    room_id: uuid.UUID
) -> List[LiveRoomTab]:
    """
    获取指定直播间的所有激活的 Tab（前端展示用）
    
    Args:
        db: 数据库会话
        room_id: 直播间 ID
    
    Returns:
        List[LiveRoomTab]: 激活的 Tab 列表，按 sort_order 升序排列
    """
    stmt = select(LiveRoomTab).where(
        and_(
            LiveRoomTab.room_id == room_id,
            LiveRoomTab.is_active == True
        )
    ).order_by(LiveRoomTab.sort_order.asc())
    
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def update_tab(
    db: AsyncSession, 
    db_obj: LiveRoomTab, 
    obj_in: LiveRoomTabUpdate
) -> LiveRoomTab:
    """
    更新 Tab 信息
    
    Args:
        db: 数据库会话
        db_obj: 数据库中的 Tab 对象
        obj_in: 更新数据
    
    Returns:
        LiveRoomTab: 更新后的 Tab 对象
    
    Raises:
        IntegrityError: 数据库完整性错误
        Exception: 其他数据库错误
    """
    # [学院派规范 5.1] 安全异步异常处理：提前提取日志变量
    tab_id_str = str(db_obj.id)
    
    try:
        # 只更新提供的字段
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        # [学院派规范 5.1] 在 try 块中提交事务
        await db.commit()
        await db.refresh(db_obj)
        
        logger.info(f"Tab updated successfully: id={tab_id_str}, updated_fields={list(update_data.keys())}")
        return db_obj
        
    except IntegrityError as e:
        # [学院派规范 5.1] 回滚事务并记录错误
        await db.rollback()
        logger.error(f"IntegrityError updating tab id={tab_id_str}: {str(e)}")
        raise
        
    except Exception as e:
        # [学院派规范 5.1] 捕获其他异常
        await db.rollback()
        logger.error(f"Error updating tab id={tab_id_str}: {str(e)}")
        raise


async def remove_tab(
    db: AsyncSession, 
    db_obj: LiveRoomTab
) -> LiveRoomTab:
    """
    删除 Tab
    
    Args:
        db: 数据库会话
        db_obj: 数据库中的 Tab 对象
    
    Returns:
        LiveRoomTab: 被删除的 Tab 对象
    
    Raises:
        Exception: 数据库错误
    """
    # [学院派规范 5.1] 安全异步异常处理：提前提取日志变量
    tab_id_str = str(db_obj.id)
    tab_key = db_obj.tab_key
    
    try:
        await db.delete(db_obj)
        
        # [学院派规范 5.1] 在 try 块中提交事务
        await db.commit()
        
        logger.info(f"Tab deleted successfully: id={tab_id_str}, tab_key={tab_key}")
        return db_obj
        
    except Exception as e:
        # [学院派规范 5.1] 回滚事务并记录错误
        await db.rollback()
        logger.error(f"Error deleting tab id={tab_id_str}: {str(e)}")
        raise


# ==================== LiveRoomMessage CRUD 操作 ====================

async def create_message(
    db: AsyncSession, 
    obj_in: LiveRoomMessageCreateInternal
) -> LiveRoomMessage:
    """
    创建新的直播间留言
    
    Args:
        db: 数据库会话
        obj_in: 留言创建数据（包含 Service 层传入的所有字段）
    
    Returns:
        LiveRoomMessage: 创建的留言对象
    
    Raises:
        IntegrityError: 数据库完整性错误（如外键约束失败）
        Exception: 其他数据库错误
    """
    # [学院派规范 5.1] 安全异步异常处理：提前提取日志变量
    room_id_str = str(obj_in.room_id)
    user_id_str = str(obj_in.user_id)
    content_preview = obj_in.content[:50] if len(obj_in.content) > 50 else obj_in.content
    
    try:
        # [学院派规范 5.1, 5.2, 5.3.A] 使用 LiveRoomMessageCreateInternal Schema
        # 应用层生成 UUID
        db_obj = LiveRoomMessage(
            id=uuid.uuid4(),
            **obj_in.model_dump()
        )
        db.add(db_obj)
        
        # [学院派规范 5.1] 在 try 块中提交事务
        await db.commit()
        await db.refresh(db_obj)
        
        logger.info(f"Message created successfully: id={db_obj.id}, room_id={room_id_str}, user_id={user_id_str}")
        return db_obj
        
    except IntegrityError as e:
        # [学院派规范 5.1] 回滚事务并记录错误
        await db.rollback()
        logger.error(f"IntegrityError creating message for room_id={room_id_str}, user_id={user_id_str}: {str(e)}")
        raise
        
    except Exception as e:
        # [学院派规范 5.1] 捕获其他异常
        await db.rollback()
        logger.error(f"Error creating message for room_id={room_id_str}, user_id={user_id_str}: {str(e)}")
        raise


async def get_messages_by_room(
    db: AsyncSession, 
    room_id: uuid.UUID, 
    page: int, 
    size: int, 
    since: Optional[datetime] = None
) -> Tuple[List[LiveRoomMessage], int]:
    """
    分页获取直播间留言
    
    Args:
        db: 数据库会话
        room_id: 直播间 ID
        page: 页码（从 1 开始）
        size: 每页大小
        since: 可选的时间过滤（获取该时间之后的留言）
    
    Returns:
        Tuple[List[LiveRoomMessage], int]: (留言列表, 总数)
    """
    # 构建基础查询条件
    conditions = [
        LiveRoomMessage.room_id == room_id,
        LiveRoomMessage.is_deleted == False
    ]
    
    # 添加时间过滤条件
    if since is not None:
        conditions.append(LiveRoomMessage.created_at > since)
    
    # [学院派规范 5.3.A] 分页模式：先获取总数
    count_stmt = select(func.count(LiveRoomMessage.id)).where(and_(*conditions))
    count_result = await db.execute(count_stmt)
    total = count_result.scalar() or 0
    
    # [学院派规范 5.3.A] 分页模式：再获取数据列表
    # 计算 offset
    skip = (page - 1) * size
    
    stmt = select(LiveRoomMessage).where(
        and_(*conditions)
    ).order_by(
        LiveRoomMessage.created_at.desc()
    ).offset(skip).limit(size)
    
    result = await db.execute(stmt)
    items = result.scalars().all()
    
    return list(items), total


async def get_message_by_id(
    db: AsyncSession,
    message_id: uuid.UUID,
    room_id: Optional[uuid.UUID] = None,
) -> Optional[LiveRoomMessage]:
    """按 ID 获取留言（可选限定 room_id）"""
    conditions = [LiveRoomMessage.id == message_id, LiveRoomMessage.is_deleted == False]
    if room_id is not None:
        conditions.append(LiveRoomMessage.room_id == room_id)
    stmt = select(LiveRoomMessage).where(and_(*conditions))
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def soft_delete_message(db: AsyncSession, db_obj: LiveRoomMessage) -> LiveRoomMessage:
    """软删除留言"""
    message_id_str = str(db_obj.id)
    try:
        db_obj.is_deleted = True
        await db.commit()
        await db.refresh(db_obj)
        logger.info(f"Message soft-deleted: id={message_id_str}")
        return db_obj
    except Exception as e:
        await db.rollback()
        logger.error(f"Error soft-deleting message id={message_id_str}: {str(e)}")
        raise


async def batch_delete_messages(
    db: AsyncSession, message_ids: List[uuid.UUID]
) -> Tuple[int, int]:
    """物理批量删除留言，返回 (deleted_count, failed_count)"""
    if not message_ids:
        return 0, 0
    try:
        stmt = select(LiveRoomMessage.id).where(LiveRoomMessage.id.in_(message_ids))
        result = await db.execute(stmt)
        existing_ids = {row[0] for row in result.all()}
        if not existing_ids:
            return 0, len(message_ids)
        delete_stmt = delete(LiveRoomMessage).where(LiveRoomMessage.id.in_(existing_ids))
        await db.execute(delete_stmt)
        await db.commit()
        deleted = len(existing_ids)
        failed = len(message_ids) - deleted
        logger.info(f"Batch deleted {deleted} messages, failed={failed}")
        return deleted, failed
    except Exception as e:
        await db.rollback()
        logger.error(f"Error batch deleting messages: {str(e)}")
        raise


async def clear_room_messages(db: AsyncSession, room_id: uuid.UUID) -> int:
    """物理删除指定直播间所有留言"""
    room_id_str = str(room_id)
    try:
        count_stmt = select(func.count(LiveRoomMessage.id)).where(
            LiveRoomMessage.room_id == room_id
        )
        count_result = await db.execute(count_stmt)
        total = count_result.scalar() or 0
        if total == 0:
            return 0
        await db.execute(delete(LiveRoomMessage).where(LiveRoomMessage.room_id == room_id))
        await db.commit()
        logger.info(f"Cleared {total} messages for room {room_id_str}")
        return total
    except Exception as e:
        await db.rollback()
        logger.error(f"Error clearing messages for room {room_id_str}: {str(e)}")
        raise


async def admin_list_messages(
    db: AsyncSession,
    room_id: Optional[uuid.UUID] = None,
    user_id: Optional[uuid.UUID] = None,
    keyword: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    page: int = 1,
    page_size: int = 20,
) -> Tuple[List[Tuple[LiveRoomMessage, Optional[str]]], int, int, int]:
    """
    管理端全局留言列表（JOIN live_rooms 取标题）

    Returns:
        ([(message, room_title), ...], total, distinct_room_count, distinct_user_count)
    """
    from app.models.live_core import LiveRoom

    conditions = [LiveRoomMessage.is_deleted == False]
    if room_id is not None:
        conditions.append(LiveRoomMessage.room_id == room_id)
    if user_id is not None:
        conditions.append(LiveRoomMessage.user_id == user_id)
    if keyword:
        conditions.append(LiveRoomMessage.content.ilike(f"%{keyword}%"))
    if start_time is not None:
        conditions.append(LiveRoomMessage.created_at >= start_time)
    if end_time is not None:
        conditions.append(LiveRoomMessage.created_at <= end_time)

    base_filter = and_(*conditions)

    count_stmt = select(func.count(LiveRoomMessage.id)).where(base_filter)
    total = (await db.execute(count_stmt)).scalar() or 0

    room_count_stmt = select(func.count(func.distinct(LiveRoomMessage.room_id))).where(base_filter)
    distinct_room_count = (await db.execute(room_count_stmt)).scalar() or 0

    user_count_stmt = select(func.count(func.distinct(LiveRoomMessage.user_id))).where(base_filter)
    distinct_user_count = (await db.execute(user_count_stmt)).scalar() or 0

    skip = (page - 1) * page_size
    stmt = (
        select(LiveRoomMessage, LiveRoom.title)
        .join(LiveRoom, LiveRoomMessage.room_id == LiveRoom.id)
        .where(base_filter)
        .order_by(LiveRoomMessage.created_at.desc())
        .offset(skip)
        .limit(page_size)
    )
    result = await db.execute(stmt)
    rows = [(row[0], row[1]) for row in result.all()]
    return rows, total, distinct_room_count, distinct_user_count
