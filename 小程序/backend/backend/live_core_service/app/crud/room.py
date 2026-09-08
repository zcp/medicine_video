"""
LiveCore Service - Room CRUD Operations

This module contains all CRUD operations for LiveRoom model,
providing data access layer functionality.
"""
import logging
import secrets
import uuid
from typing import Optional, List, Tuple, Dict, Any, Union
from sqlalchemy import select, func, and_, or_, delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.live_core import LiveRoom, LiveSession, LiveSessionStatus, SessionStatistics
from app.models.experts import LiveSessionExpert
from app.models.brand import BrandRoom
from app.models.topic import TopicCategoryRoom
from app.models.live_features import LiveRoomMessage, LiveRoomTab
from app.models.user_behavior import (
    UserFavorite,
    WatchHistory,
    UserSubscription,
    SubscriptionTargetType,
)
from app.models.content_management import SessionTag, LiveRoomCategory
from app.models.liveroom_official_accounts import LiveRoomOfficialAccount
from app.schemas.live_core import LiveRoomCreate, LiveRoomUpdate
from app.core.exceptions import DatabaseIntegrityException, DatabaseOperationException

# 设置日志
logger = logging.getLogger(__name__)

async def get(db: AsyncSession, room_id: uuid.UUID, user_id: Optional[uuid.UUID] = None) -> Optional[LiveRoom]:
    """根据ID获取单个房间"""
    logger.debug(f"查询房间: room_id={room_id}, user_id={user_id}")
    
    try:
        query = select(LiveRoom).where(LiveRoom.id == room_id)
        if user_id:
            query = query.where(LiveRoom.user_id == user_id)
        
        result = await db.execute(query)
        room = result.scalar_one_or_none()
        
        if room:
            logger.debug(f"找到房间: room_id={room_id}, title={room.title}")
        else:
            logger.debug(f"房间不存在: room_id={room_id}")
        
        return room
        
    except Exception as e:
        logger.error(f"查询房间失败: room_id={room_id}, user_id={user_id}, error={str(e)}", exc_info=True)
        raise


async def get_by_stream_key(db: AsyncSession, stream_key: str) -> Optional[LiveRoom]:
    """根据 stream_key 获取单个房间"""
    logger.debug(f"根据stream_key查询房间: stream_key={stream_key}")
    
    try:
        result = await db.execute(
            select(LiveRoom).where(LiveRoom.stream_key == stream_key)
        )
        room = result.scalar_one_or_none()
        
        if room:
            logger.debug(f"找到房间: stream_key={stream_key}, room_id={room.id}")
        else:
            logger.debug(f"房间不存在: stream_key={stream_key}")
        
        return room
        
    except Exception as e:
        logger.error(f"根据stream_key查询房间失败: stream_key={stream_key}, error={str(e)}", exc_info=True)
        raise


async def get_by_source_room_id(
    db: AsyncSession,
    source_room_id: uuid.UUID,
) -> Optional[LiveRoom]:
    """按正式间 ID 查找关联测播间（文档 18 幂等复用）"""
    logger.debug(f"按 source_room_id 查询测播间: source_room_id={source_room_id}")
    try:
        result = await db.execute(
            select(LiveRoom).where(LiveRoom.source_room_id == source_room_id)
        )
        return result.scalar_one_or_none()
    except Exception as e:
        logger.error(
            f"按 source_room_id 查询测播间失败: source_room_id={source_room_id}, error={e}",
            exc_info=True,
        )
        raise DatabaseOperationException(f"数据库查询失败: {e}")


async def get_by_external_id(
    db: AsyncSession,
    user_id: uuid.UUID,
    external_room_id: str,
) -> Optional[LiveRoom]:
    """
    根据 (user_id, external_room_id) 获取单个房间（V6 去重幂等增量）
    只做纯查询，不做权限和业务校验。
    """
    logger.debug(
        f"根据 external_room_id 查询房间: user_id={user_id}, external_room_id={external_room_id}"
    )

    try:
        query = (
            select(LiveRoom)
            .where(
                LiveRoom.user_id == user_id,
                LiveRoom.external_room_id == external_room_id,
            )
        )
        result = await db.execute(query)
        room = result.scalar_one_or_none()

        if room:
            logger.debug(
                f"找到房间: user_id={user_id}, external_room_id={external_room_id}, room_id={room.id}"
            )
        else:
            logger.debug(
                f"未找到房间: user_id={user_id}, external_room_id={external_room_id}"
            )

        return room
    except Exception as e:
        logger.error(
            f"根据 external_room_id 查询房间失败: user_id={user_id}, external_room_id={external_room_id}, error={e}",
            exc_info=True,
        )
        raise DatabaseOperationException(f"数据库查询失败: {e}")


async def get_multi_and_total(
    db: AsyncSession, 
    skip: int = 0, 
    limit: int = 10,
    user_id: Optional[uuid.UUID] = None,  # ← 修改：权限参数（当前用户的public_id，匿名时为None）
    role: Optional[str] = None           # ← 新增：权限参数（当前用户的角色，匿名时为None）
) -> Tuple[List[LiveRoom], int]:
    """分页获取房间列表，同时返回总数（带权限过滤）"""
    logger.debug(f"分页查询房间列表: skip={skip}, limit={limit}, user_id={user_id}, role={role}")
    
    try:
        # 构建基础查询
        query = select(LiveRoom)
        
        # 发现层：非 Admin 一律排除不公开房（含自己的测播间）。
        # 「我的直播」走 get_multi_and_total_by_owner，不经此路径。
        if role in ['ADMIN', 'SUPERADMIN']:
            pass
        else:
            query = query.where(LiveRoom.is_private == False)
        
        # ← 修改：计算总数（需要应用相同的WHERE条件）
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await db.execute(count_query)
        total = count_result.scalar()
        
        # ← 保持不变：获取分页数据
        result = await db.execute(
            query
            .order_by(LiveRoom.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        rooms = result.scalars().all()
        
        logger.debug(f"分页查询房间列表完成: 返回{len(rooms)}条记录, 总数={total}")
        return list(rooms), total
        
    except Exception as e:
        logger.error(f"分页查询房间列表失败: skip={skip}, limit={limit}, user_id={user_id}, role={role}, error={str(e)}", exc_info=True)
        raise


async def list_admin_rooms(
    db: AsyncSession,
    *,
    skip: int = 0,
    limit: int = 20,
    q: Optional[str] = None,
    owner_user_id: Optional[uuid.UUID] = None,
    is_private: Optional[bool] = None,
) -> Tuple[List[LiveRoom], int]:
    """
    管理端全站房间列表（不过滤私密；权限由 API 层 verify_admin_role 保证）。

    支持标题 ILIKE、按房主 public_id、按 is_private 筛选；按 updated_at DESC, id DESC。
    """
    logger.debug(
        "Admin分页查询房间: skip=%s limit=%s q=%s owner=%s is_private=%s",
        skip, limit, q, owner_user_id, is_private,
    )
    try:
        query = select(LiveRoom)
        if q:
            query = query.where(LiveRoom.title.ilike(f"%{q}%"))
        if owner_user_id is not None:
            query = query.where(LiveRoom.user_id == owner_user_id)
        if is_private is not None:
            query = query.where(LiveRoom.is_private == is_private)

        count_query = select(func.count()).select_from(query.subquery())
        total = (await db.execute(count_query)).scalar() or 0

        result = await db.execute(
            query.order_by(LiveRoom.updated_at.desc(), LiveRoom.id.desc())
            .offset(skip)
            .limit(limit)
        )
        rooms = list(result.scalars().all())
        logger.debug("Admin分页查询房间完成: 返回%s条, 总数=%s", len(rooms), total)
        return rooms, total
    except Exception as e:
        logger.error("Admin分页查询房间失败: error=%s", e, exc_info=True)
        raise


async def get_multi_and_total_by_owner(
    db: AsyncSession,
    owner_id: uuid.UUID,
    skip: int = 0,
    limit: int = 10,
) -> Tuple[List[LiveRoom], int]:
    """
    分页获取指定用户创建的房间列表，并返回总数（管理后台 RoomList 视图使用）。
    
    说明：
        - 该方法仅按 `LiveRoom.user_id == owner_id` 进行过滤，不再区分 is_private；
        - 适用于“Regular 只管理自己的房间”这一管理视图场景；
        - 权限边界仍由 Service 层根据 role/user_id 控制（例如仅在 Regular 管理页启用）。
    """
    logger.debug(f"按owner分页查询房间列表: skip={skip}, limit={limit}, owner_id={owner_id}")
    try:
        # 构建仅按 owner 过滤的基础查询
        query = select(LiveRoom).where(LiveRoom.user_id == owner_id)

        # 计算总数（应用相同的 WHERE 条件）
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await db.execute(count_query)
        total = count_result.scalar()

        # 获取分页数据（按创建时间倒序）
        result = await db.execute(
            query.order_by(LiveRoom.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        rooms = result.scalars().all()

        logger.debug(
            f"按owner分页查询房间列表完成: owner_id={owner_id}, 返回{len(rooms)}条记录, 总数={total}"
        )
        return list(rooms), total
    except Exception as e:
        logger.error(
            f"按owner分页查询房间列表失败: skip={skip}, limit={limit}, owner_id={owner_id}, error={str(e)}",
            exc_info=True,
        )
        raise


async def list_with_search(
    db: AsyncSession,
    filters: dict = None,
    page: int = 1,
    size: int = 10,
    sort: Optional[str] = None,
    user_id: Optional[uuid.UUID] = None,  # ← 新增：权限参数（当前用户的public_id，匿名时为None）
    role: Optional[str] = None,           # ← 新增：权限参数（当前用户的角色，匿名时为None）
    owner_only: bool = False,
) -> dict:
    """
    搜索房间列表（CRUD 层 - 学院派实现，带权限过滤）
    
    职责：
    1. 执行数据库查询
    2. 支持 ID 精确匹配和标题模糊匹配
    3. 支持可配置排序
    4. 分页返回
    5. ← 新增：应用权限过滤（Admin/Regular/Anonymous）
    
    不做：
    1. 业务逻辑（由 Service 层负责）
    """
    try:
        # 构建基础查询
        query = select(LiveRoom)
        
        # ← 保持不变：添加搜索条件
        search_conditions = None
        if filters and 'id_or_title' in filters:
            field, value = filters['id_or_title']
            
            if field == 'id':
                # UUID 精确匹配
                search_conditions = (LiveRoom.id == value)
            elif field == 'title':
                # 标题模糊匹配
                search_conditions = (LiveRoom.title.ilike(value))
        
        # 发现层：非 Admin / 非「我的」路径一律排除不公开房
        if owner_only and user_id:
            # 个人资源：仅返回当前用户自己的房间（含测播间）
            if search_conditions is not None:
                query = query.where(
                    and_(
                        search_conditions,
                        LiveRoom.user_id == user_id,
                    )
                )
            else:
                query = query.where(LiveRoom.user_id == user_id)
        elif role in ['ADMIN', 'SUPERADMIN']:
            if search_conditions is not None:
                query = query.where(search_conditions)
        else:
            if search_conditions is not None:
                query = query.where(
                    and_(
                        search_conditions,
                        LiveRoom.is_private == False,
                    )
                )
            else:
                query = query.where(LiveRoom.is_private == False)
        
        # ← 保持不变：计算总数（需要应用相同的WHERE条件）
        count_query = select(func.count()).select_from(query.subquery())
        result = await db.execute(count_query)
        total = result.scalar()
        
        # ← 保持不变：排序处理
        if sort:
            # 解析 sort 参数（格式：field:direction）
            sort_parts = sort.split(':')
            if len(sort_parts) == 2:
                field_name, direction = sort_parts[0], sort_parts[1].upper()
                # 验证字段名（仅允许安全字段）
                if hasattr(LiveRoom, field_name) and direction in ('ASC', 'DESC'):
                    field = getattr(LiveRoom, field_name)
                    if direction == 'DESC':
                        query = query.order_by(field.desc())
                    else:
                        query = query.order_by(field.asc())
                else:
                    # 无效的排序参数，使用默认排序
                    query = query.order_by(LiveRoom.created_at.desc())
            else:
                # 无效格式，使用默认排序
                query = query.order_by(LiveRoom.created_at.desc())
        else:
            # 默认排序
            query = query.order_by(LiveRoom.created_at.desc())
        
        # ← 保持不变：分页
        query = query.offset((page - 1) * size).limit(size)
        
        # ← 保持不变：执行查询
        result = await db.execute(query)
        rooms = result.scalars().all()
        
        return {
            "total": total,
            "page": page,
            "size": size,
            "items": rooms
        }
        
    except Exception as e:
        logger.error(f"搜索房间失败：{e}", exc_info=True)
        raise DatabaseOperationException(f"数据库查询失败: {e}")


async def create(db: AsyncSession, obj_in: Union[LiveRoomCreate, dict], user_id: uuid.UUID) -> LiveRoom:
    """
    创建新房间（CRUD 层 - 学院派实现）
    
    职责：
    1. 创建数据库记录
    2. 处理事务（commit/rollback）
    3. 处理数据库异常
    4. 记录错误日志
    
    不做：
    1. 业务逻辑校验（由 Service 层负责）
    2. 权限检查（由 Service 层负责）
    """
    # 提取数据
    if isinstance(obj_in, dict):
        data = obj_in.copy()
        title_log = data.get('title')
        stream_key = data.get('stream_key')
        # 如果 id 存在，提取用于日志
        room_id_log = data.get('id', uuid.uuid4())
    else:
        data = obj_in.model_dump()
        title_log = getattr(obj_in, 'title', None)
        stream_key = getattr(obj_in, 'stream_key', None)
        room_id_log = uuid.uuid4()
        
    logger.info(f"开始创建房间: title={title_log}, user_id={user_id}")
    
    try:
        # 如果未提供 stream_key，则生成一个
        if not stream_key:
            # 生成唯一的推流密钥
            stream_key = f"sk_live_{secrets.token_hex(16)}"
            
            # 确保stream_key唯一性 (TODO: 这里的重试逻辑在事务中可能需要注意，但 CRUD 层应封装操作)
            # 在学院派模式下，如果 stream_key 是必须唯一的，应该由 DB 约束保证，
            # 如果冲突则抛出 IntegrityError，由 Service 层重试或处理。
            # 但为了保持原有逻辑，保留重试。
            
            retry_count = 0
            while retry_count < 10:  # 防止无限循环
                existing = await db.execute(
                    select(LiveRoom).where(LiveRoom.stream_key == stream_key)
                )
                if existing.scalar_one_or_none() is None:
                    break
                stream_key = f"sk_live_{secrets.token_hex(16)}"
                retry_count += 1
            
            if retry_count >= 10:
                logger.error(f"生成唯一stream_key失败，重试次数过多: title={title_log}")
                raise Exception("无法生成唯一的推流密钥")
        
        data['stream_key'] = stream_key
        data['user_id'] = user_id
        
        # 移除不在模型中的字段（如果是dict可能包含多余字段）
        # LiveRoom 模型字段：id, user_id, title, description, cover_url, stream_key,
        # is_private, record_by_default, category_id, parent_room_id, external_room_id,
        # source_room_id
        valid_fields = {
            'id',
            'user_id',
            'title',
            'description',
            'cover_url',
            'stream_key',
            'is_private',
            'record_by_default',
            'category_id',
            'parent_room_id',
            'external_room_id',
            'source_room_id',
        }
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}
        
        # 创建房间对象
        db_obj = LiveRoom(**filtered_data)
        
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)

        logger.info(f"房间创建成功: room_id={db_obj.id}, title={db_obj.title}, stream_key={stream_key}")
        return db_obj
        
    except IntegrityError as e:
        await db.rollback()
        logger.error(
            f"创建房间失败（完整性错误）：title={title_log}, user_id={user_id}, error={e}",
            exc_info=True
        )
        raise DatabaseIntegrityException("创建房间时发生唯一键冲突")
        
    except Exception as e:
        await db.rollback()
        logger.error(
            f"创建房间失败（未知DB错误）：title={title_log}, user_id={user_id}, error={e}",
            exc_info=True
        )
        raise DatabaseOperationException(f"数据库操作失败: {e}")


async def update(
    db: AsyncSession, 
    db_obj: LiveRoom, 
    obj_in: LiveRoomUpdate
) -> LiveRoom:
    """更新房间信息"""
    logger.info(f"开始更新房间: room_id={db_obj.id}, title={db_obj.title}")
    
    # 提取日志变量
    room_id_log = db_obj.id
    
    try:
        # 获取更新数据，排除None值
        update_data = obj_in.model_dump(exclude_unset=True)
        logger.debug(f"更新字段: {list(update_data.keys())}")
        
        # 更新对象属性
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        await db.commit()
        await db.refresh(db_obj)

        logger.info(f"房间更新成功: room_id={db_obj.id}, title={db_obj.title}")
        return db_obj
        
    except IntegrityError as e:
        await db.rollback()
        logger.error(f"更新房间失败（完整性错误）: room_id={room_id_log}, error={e}", exc_info=True)
        raise DatabaseIntegrityException("更新房间时发生唯一键冲突")

    except Exception as e:
        await db.rollback()
        logger.error(f"更新房间失败: room_id={room_id_log}, error={e}", exc_info=True)
        raise DatabaseOperationException(f"数据库操作失败: {e}")


async def delete_room_related(db: AsyncSession, room_id: uuid.UUID) -> None:
    """
    删除房间前先删除所有关联数据，避免外键约束导致 IntegrityError。
    顺序：场次相关（专家/统计/标签/留言/观看记录/内容订阅）→
    房间相关（品牌/专题/科室关联/公众号关联/留言/Tab/收藏/内容订阅）→ 场次 → 房间由 remove 删除。
    """
    logger.info(f"开始删除房间关联数据: room_id={room_id}")
    try:
        result = await db.execute(select(LiveSession.id).where(LiveSession.room_id == room_id))
        session_ids = [row[0] for row in result.all()]

        if session_ids:
            await db.execute(delete(LiveSessionExpert).where(LiveSessionExpert.session_id.in_(session_ids)))
            await db.execute(delete(SessionStatistics).where(SessionStatistics.session_id.in_(session_ids)))
            await db.execute(delete(SessionTag).where(SessionTag.session_id.in_(session_ids)))
            await db.execute(delete(LiveRoomMessage).where(LiveRoomMessage.session_id.in_(session_ids)))
            await db.execute(delete(WatchHistory).where(WatchHistory.session_id.in_(session_ids)))
            # 16-D4：物理删除场次级内容订阅
            sess_sub_result = await db.execute(
                delete(UserSubscription).where(
                    UserSubscription.target_type == SubscriptionTargetType.SESSION,
                    UserSubscription.target_id.in_(session_ids),
                )
            )
            logger.info(
                "删房级联：已清场次订阅 room_id=%s session_subs=%s",
                room_id,
                sess_sub_result.rowcount,
            )

        await db.execute(delete(BrandRoom).where(BrandRoom.room_id == room_id))
        await db.execute(delete(TopicCategoryRoom).where(TopicCategoryRoom.room_id == room_id))
        await db.execute(delete(LiveRoomCategory).where(LiveRoomCategory.room_id == room_id))
        await db.execute(delete(LiveRoomOfficialAccount).where(LiveRoomOfficialAccount.room_id == room_id))
        await db.execute(delete(LiveRoomMessage).where(LiveRoomMessage.room_id == room_id))
        await db.execute(delete(LiveRoomTab).where(LiveRoomTab.room_id == room_id))
        await db.execute(delete(UserFavorite).where(UserFavorite.room_id == room_id))
        # 16-D4：物理删除房间级内容订阅
        room_sub_result = await db.execute(
            delete(UserSubscription).where(
                UserSubscription.target_type == SubscriptionTargetType.ROOM,
                UserSubscription.target_id == room_id,
            )
        )
        logger.info(
            "删房级联：已清房间订阅 room_id=%s room_subs=%s",
            room_id,
            room_sub_result.rowcount,
        )
        await db.execute(delete(LiveSession).where(LiveSession.room_id == room_id))
        logger.info(f"房间关联数据已删除: room_id={room_id}, sessions_count={len(session_ids)}")
    except Exception as e:
        await db.rollback()
        logger.error(f"删除房间关联数据失败: room_id={room_id}, error={e}", exc_info=True)
        raise DatabaseOperationException(f"删除房间关联数据失败: {e}")


async def remove(db: AsyncSession, db_obj: LiveRoom) -> LiveRoom:
    """删除房间"""
    logger.info(f"开始删除房间: room_id={db_obj.id}, title={db_obj.title}")
    
    # 提取日志变量
    room_id_log = db_obj.id
    title_log = db_obj.title

    try:
        await db.delete(db_obj)
        await db.commit()
        logger.info(f"房间删除成功: room_id={room_id_log}, title={title_log}")
        
        return db_obj
        
    except IntegrityError as e:
        await db.rollback()
        logger.error(f"删除房间失败（完整性错误）: room_id={room_id_log}, error={e}", exc_info=True)
        raise DatabaseIntegrityException("删除房间时发生完整性冲突")

    except Exception as e:
        await db.rollback()
        logger.error(f"删除房间失败: room_id={room_id_log}, error={e}", exc_info=True)
        raise DatabaseOperationException(f"数据库操作失败: {e}")


async def is_live(db: AsyncSession, room_id: uuid.UUID) -> bool:
    """检查指定房间当前是否有状态为'live'的LiveSession记录"""
    logger.debug(f"检查房间直播状态: room_id={room_id}")
    
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
        is_live_status = result.scalar_one_or_none() is not None
        logger.debug(f"房间直播状态检查完成: room_id={room_id}, is_live={is_live_status}")
        return is_live_status
        
    except Exception as e:
        logger.error(f"检查房间直播状态失败: room_id={room_id}, error={str(e)}", exc_info=True)
        raise


async def get_sub_venues_with_live_status(
    db: AsyncSession, 
    parent_room_id: uuid.UUID, 
    skip: int = 0, 
    limit: int = 10,
    user_id: Optional[uuid.UUID] = None,
    role: Optional[str] = None  # ← 新增：角色参数，用于 is_private 过滤
) -> Tuple[List[Dict[str, Any]], int]:
    """
    获取指定主会场下的所有分会场，并包含其实时直播状态
    使用LEFT OUTER JOIN关联LiveSession表
    
    注意：主会场的权限验证已在 Service 层完成（通过 get_room_details），
    本函数仅负责查询分会场并应用 is_private 过滤。
    """
    logger.debug(f"查询分会场列表: parent_room_id={parent_room_id}, skip={skip}, limit={limit}, user_id={user_id}, role={role}")
    
    try:
        # ✅ 构建基础查询条件：parent_room_id
        base_condition = LiveRoom.parent_room_id == parent_room_id
        
        # ✅ 根据用户身份应用 is_private 过滤（符合文档第387行要求）
        # 文档要求：必须在 Repository 层通过 SQL 过滤，禁止在内存过滤（性能陷阱）
        if role in ['ADMIN', 'SUPERADMIN']:
            # Admin: 无过滤，看所有分会场
            visibility_condition = None
        elif user_id:
            # Regular User: Public OR Own
            visibility_condition = or_(
                LiveRoom.is_private == False,
                LiveRoom.user_id == user_id
            )
        else:
            # Anonymous: Only Public
            visibility_condition = LiveRoom.is_private == False
        
        # 组合查询条件
        if visibility_condition is not None:
            where_clause = and_(base_condition, visibility_condition)
        else:
            where_clause = base_condition
        
        # 获取总数
        count_result = await db.execute(
            select(func.count(LiveRoom.id))
            .where(where_clause)
        )
        total = count_result.scalar()
        
        # 获取分会场数据和直播状态
        result = await db.execute(
            select(
                LiveRoom.id,
                LiveRoom.title,
                LiveRoom.description,
                LiveRoom.cover_url,
                LiveRoom.is_private,
                LiveRoom.record_by_default,
                LiveRoom.category_id,
                LiveRoom.user_id,
                LiveRoom.created_at,
                LiveRoom.updated_at,
                LiveSession.status.label('live_status'),
                LiveSession.id.label('current_session_id')
            )
            .select_from(LiveRoom)
            .outerjoin(
                LiveSession,
                and_(
                    LiveSession.room_id == LiveRoom.id,
                    LiveSession.status == LiveSessionStatus.LIVE
                )
            )
            .where(where_clause)
            .order_by(LiveRoom.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        
        # 转换为字典列表
        sub_venues = []
        for row in result:
            sub_venue = {
                'id': row.id,
                'title': row.title,
                'description': row.description,
                'cover_url': row.cover_url,
                'is_private': row.is_private,
                'record_by_default': row.record_by_default,
                'category_id': row.category_id,
                'user_id': row.user_id,
                'created_at': row.created_at,
                'updated_at': row.updated_at,
                'live_status': row.live_status,
                'current_session_id': row.current_session_id
            }
            sub_venues.append(sub_venue)
        
        logger.debug(f"分会场列表查询完成: parent_room_id={parent_room_id}, 返回{len(sub_venues)}条记录, 总数={total}")
        return sub_venues, total
        
    except Exception as e:
        logger.error(f"查询分会场列表失败: parent_room_id={parent_room_id}, skip={skip}, limit={limit}, user_id={user_id}, error={str(e)}", exc_info=True)
        raise


async def update_cover_url(
    db: AsyncSession, 
    room_id: uuid.UUID, 
    cover_url: str
) -> Optional[LiveRoom]:
    """
    更新房间封面URL
    
    Args:
        db: 数据库会话
        room_id: 房间ID
        cover_url: 新的封面URL
        
    Returns:
        更新后的LiveRoom对象或None
    """
    logger.info(f"开始更新房间封面URL: room_id={room_id}")
    
    try:
        # 1. 查询房间对象
        result = await db.execute(
            select(LiveRoom).where(LiveRoom.id == room_id)
        )
        room = result.scalar_one_or_none()
        
        if room is None:
            logger.warning(f"房间不存在，无法更新封面: room_id={room_id}")
            return None
        
        # 2. 更新 cover_url 字段
        room.cover_url = cover_url
        
        # 3. 提交事务
        await db.commit()
        
        # 4. 刷新对象并返回
        await db.refresh(room)
        logger.info(f"房间封面URL更新成功: room_id={room_id}, cover_url={cover_url}")
        
        return room
        
    except IntegrityError as e:
        await db.rollback()
        logger.error(f"更新房间封面URL失败（完整性错误）: room_id={room_id}, error={e}", exc_info=True)
        raise DatabaseIntegrityException("更新房间封面时发生冲突")

    except Exception as e:
        await db.rollback()
        logger.error(f"更新房间封面URL失败: room_id={room_id}, error={str(e)}", exc_info=True)
        raise DatabaseOperationException(f"数据库操作失败: {e}")
