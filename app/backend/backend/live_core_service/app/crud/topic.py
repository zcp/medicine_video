"""
专题聚合功能的 CRUD 层

本模块封装所有与 Topic、TopicCategory、TopicCategoryRoom 模型相关的数据库操作。
提供纯粹的数据访问接口，不包含任何业务逻辑验证。

所有函数遵循以下规范：
- 使用 async/await 异步编程
- UUID 在应用层生成
- 使用 selectinload/joinedload 避免 N+1 查询
- 遵循安全异步异常处理原则（提前提取变量）
- 记录适当的日志
"""

# 标准库导入
import uuid
import logging
from typing import List, Optional, Tuple, Dict, Any

# 第三方库导入

from sqlalchemy import select, delete, and_, or_, func, update as sa_update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.exc import IntegrityError

# 项目内导入
from app.models.topic import Topic, TopicCategory, TopicCategoryRoom, TopicStatus
from app.models.live_core import LiveRoom, LiveSession
from app.schemas.topic import TopicCreate, TopicUpdate, TopicCategoryCreate, TopicCategoryUpdate, RoomAssociation

# 配置日志
logger = logging.getLogger(__name__)


# ==================== 专题 (Topic) 相关操作 ====================

async def create(
    db: AsyncSession, 
    obj_in: TopicCreate, 
    user_id: uuid.UUID
) -> Topic:
    """
    创建新专题
    
    Args:
        db: 数据库会话
        obj_in: 专题创建数据
        user_id: 创建者用户ID
    
    Returns:
        Topic: 创建的专题对象
    
    Raises:
        IntegrityError: 数据库完整性约束错误
    """
    # 应用层生成UUID
    topic_id = uuid.uuid4()
    
    topic = Topic(
        id=topic_id,
        user_id=user_id,
        title=obj_in.title,
        description=obj_in.description,
        # banner_url 默认为 NULL，通过 POST /api/v1/topics/{topic_id}/banner 接口上传
        status=obj_in.status
    )
    
    # 提前提取用于日志的变量
    topic_id_for_logging = topic.id
    user_id_for_logging = user_id
    
    try:
        db.add(topic)
        await db.commit()
        await db.refresh(topic)
        logger.debug(f"创建专题成功: topic_id={topic_id_for_logging}, user_id={user_id_for_logging}")
        return topic
    except IntegrityError as e:
        await db.rollback()
        # ✅ 使用局部变量记录日志
        logger.error(f"创建专题失败-完整性错误: topic_id={topic_id_for_logging}, error={str(e)}")
        raise
    except Exception as e:
        await db.rollback()
        # ✅ 使用局部变量记录日志
        logger.error(f"创建专题失败: topic_id={topic_id_for_logging}, error={str(e)}")
        raise


async def get(db: AsyncSession, topic_id: uuid.UUID) -> Optional[Topic]:
    """
    根据ID获取单个专题
    
    Args:
        db: 数据库会话
        topic_id: 专题唯一标识
    
    Returns:
        Optional[Topic]: 专题对象，如果不存在则返回None
    """
    logger.debug(f"查询专题: topic_id={topic_id}")
    
    stmt = select(Topic).where(Topic.id == topic_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_with_categories(
    db: AsyncSession, 
    topic_id: uuid.UUID
) -> Optional[Topic]:
    """
    获取专题及其所有分类（预加载）
    
    使用 selectinload 避免 N+1 查询问题。
    
    Args:
        db: 数据库会话
        topic_id: 专题唯一标识
    
    Returns:
        Optional[Topic]: 包含预加载分类的专题对象，如果不存在则返回None
    """
    logger.debug(f"查询专题及分类: topic_id={topic_id}")
    
    stmt = select(Topic).options(
        selectinload(Topic.categories)
    ).where(Topic.id == topic_id)
    
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_multi_and_total(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 10,
    status: Optional[TopicStatus] = None,
    title: Optional[str] = None,  # ← 新增：专题标题筛选
    topic_id: Optional[uuid.UUID] = None,  # ← 新增：专题ID筛选
    user_id: Optional[uuid.UUID] = None,
    # ← 新增：权限参数
    current_user_id: Optional[uuid.UUID] = None,  # 当前用户的public_id（匿名时为None）
    current_user_role: Optional[str] = None       # 当前用户的角色（匿名时为None）
) -> Tuple[List[Topic], int]:
    """
    分页获取专题列表，支持按状态、标题、ID、用户ID筛选（带权限过滤）
    
    Args:
        db: 数据库会话
        skip: 跳过的记录数（用于分页）
        limit: 返回的最大记录数
        status: 专题状态筛选条件（可选）
        title: 专题标题筛选，支持模糊匹配（可选）
        topic_id: 专题ID筛选，精确匹配（可选）
        user_id: 用户ID筛选条件（可选，用于业务筛选）
        current_user_id: 当前用户的public_id（匿名时为None，用于权限过滤）
        current_user_role: 当前用户的角色（匿名时为None，用于权限过滤）
    
    Returns:
        Tuple[List[Topic], int]: (专题列表, 总记录数)
    """
    logger.debug(
        f"查询专题列表: skip={skip}, limit={limit}, status={status}, "
        f"title={title}, topic_id={topic_id}, user_id={user_id}, "
        f"current_user_id={current_user_id}, current_user_role={current_user_role}"
    )
    
    # 构建基础查询
    stmt = select(Topic)
    count_stmt = select(func.count()).select_from(Topic)
    
    # 1. 先应用业务筛选条件（包括新增的title和topic_id）
    business_filters = []
    if title:  # ← 新增：专题标题模糊匹配（不区分大小写）
        business_filters.append(Topic.title.ilike(f'%{title}%'))
    if topic_id:  # ← 新增：专题ID精确匹配
        business_filters.append(Topic.id == topic_id)
    if status is not None:
        business_filters.append(Topic.status == status)
    if user_id is not None:
        business_filters.append(Topic.user_id == user_id)
    
    # 2. 再应用权限过滤条件（独立于业务筛选条件，修正后的逻辑）
    permission_filters = []
    if current_user_role in ['ADMIN', 'SUPERADMIN']:
        # 管理员：无权限过滤，看所有
        pass
    elif current_user_id:
        # 普通用户：Published OR (Draft/Archived AND Own)
        # ✅ 修正：权限过滤独立于业务筛选条件，始终应用完整的权限规则
        permission_filters.append(
            or_(
                Topic.status == TopicStatus.PUBLISHED,
                and_(
                    Topic.status.in_([TopicStatus.DRAFT, TopicStatus.ARCHIVED]),
                    Topic.user_id == current_user_id
                )
            )
        )
    else:
        # 匿名用户：Only Published
        permission_filters.append(Topic.status == TopicStatus.PUBLISHED)
    
    # 3. 合并所有筛选条件（AND关系）
    all_filters = permission_filters + business_filters
    
    if all_filters:
        stmt = stmt.where(and_(*all_filters))
        count_stmt = count_stmt.where(and_(*all_filters))
    
    # 获取总数（必须应用相同的WHERE条件）
    total_result = await db.execute(count_stmt)
    total = total_result.scalar()
    
    # 应用排序和分页
    stmt = stmt.order_by(Topic.created_at.desc()).offset(skip).limit(limit)
    
    # 执行查询
    result = await db.execute(stmt)
    topics = result.scalars().all()
    
    return list(topics), total


async def update(
    db: AsyncSession, 
    db_obj: Topic, 
    obj_in: TopicUpdate
) -> Topic:
    """
    更新专题信息
    
    Args:
        db: 数据库会话
        db_obj: 要更新的专题对象
        obj_in: 更新数据
    
    Returns:
        Topic: 更新后的专题对象
    
    Raises:
        IntegrityError: 数据库完整性约束错误
    """
    # 提前提取用于日志的变量
    topic_id_for_logging = db_obj.id
    
    # 获取更新数据（排除未设置的字段）
    update_data = obj_in.model_dump(exclude_unset=True)
    
    logger.debug(f"更新专题: topic_id={topic_id_for_logging}, fields={list(update_data.keys())}")
    
    try:
        # 更新字段
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    except IntegrityError as e:
        await db.rollback()
        # ✅ 使用局部变量记录日志
        logger.error(f"更新专题失败-完整性错误: topic_id={topic_id_for_logging}, error={str(e)}")
        raise
    except Exception as e:
        await db.rollback()
        # ✅ 使用局部变量记录日志
        logger.error(f"更新专题失败: topic_id={topic_id_for_logging}, error={str(e)}")
        raise


async def remove(db: AsyncSession, db_obj: Topic) -> Topic:
    """
    删除专题（级联删除分类和关联）
    
    数据库已配置 ON DELETE CASCADE，子对象会自动删除。
    
    Args:
        db: 数据库会话
        db_obj: 要删除的专题对象
    
    Returns:
        Topic: 被删除的专题对象
    
    Raises:
        Exception: 删除操作失败
    """
    # 提前提取用于日志的变量
    topic_id_for_logging = db_obj.id
    categories_count = len(db_obj.categories) if hasattr(db_obj, 'categories') else 0
    
    logger.warning(f"删除专题: topic_id={topic_id_for_logging}, categories_count={categories_count}")
    
    try:
        await db.delete(db_obj)
        await db.commit()
        return db_obj
    except Exception as e:
        await db.rollback()
        # ✅ 使用局部变量记录日志
        logger.error(f"删除专题失败: topic_id={topic_id_for_logging}, error={str(e)}")
        raise


# ==================== 分类 (TopicCategory) 相关操作 ====================

async def create_category(
    db: AsyncSession,
    obj_in: TopicCategoryCreate,
    topic_id: uuid.UUID
) -> TopicCategory:
    """
    创建新分类
    
    Args:
        db: 数据库会话
        obj_in: 分类创建数据
        topic_id: 所属专题ID
    
    Returns:
        TopicCategory: 创建的分类对象
    
    Raises:
        IntegrityError: 数据库完整性约束错误（如分类名称重复）
    """
    # 应用层生成UUID
    category_id = uuid.uuid4()
    
    category = TopicCategory(
        id=category_id,
        topic_id=topic_id,
        name=obj_in.name,
        sort_order=obj_in.sort_order
    )
    
    # 提前提取用于日志的变量
    category_id_for_logging = category.id
    topic_id_for_logging = topic_id
    
    try:
        db.add(category)
        await db.commit()
        await db.refresh(category)
        logger.debug(f"创建分类成功: category_id={category_id_for_logging}, topic_id={topic_id_for_logging}")
        return category
    except IntegrityError as e:
        await db.rollback()
        # ✅ 使用局部变量记录日志
        logger.error(f"创建分类失败-完整性错误: category_id={category_id_for_logging}, error={str(e)}")
        raise
    except Exception as e:
        await db.rollback()
        # ✅ 使用局部变量记录日志
        logger.error(f"创建分类失败: category_id={category_id_for_logging}, error={str(e)}")
        raise


async def get_category(
    db: AsyncSession, 
    category_id: uuid.UUID
) -> Optional[TopicCategory]:
    """
    根据ID获取单个分类
    
    Args:
        db: 数据库会话
        category_id: 分类唯一标识
    
    Returns:
        Optional[TopicCategory]: 分类对象，如果不存在则返回None
    """
    logger.debug(f"查询分类: category_id={category_id}")
    
    stmt = select(TopicCategory).where(TopicCategory.id == category_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_category_with_topic(
    db: AsyncSession,
    category_id: uuid.UUID
) -> Optional[TopicCategory]:
    """
    获取分类及其关联的专题（用于权限验证）
    
    使用 selectinload 预加载专题对象。
    
    Args:
        db: 数据库会话
        category_id: 分类唯一标识
    
    Returns:
        Optional[TopicCategory]: 包含预加载专题的分类对象，如果不存在则返回None
    """
    logger.debug(f"查询分类及专题: category_id={category_id}")
    
    stmt = select(TopicCategory).options(
        selectinload(TopicCategory.topic)
    ).where(TopicCategory.id == category_id)
    
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_categories_by_topic(
    db: AsyncSession,
    topic_id: uuid.UUID,
    skip: int = 0,
    limit: int = 100
) -> Tuple[List[TopicCategory], int]:
    """
    分页获取专题下的所有分类
    
    按 sort_order ASC 排序。
    
    Args:
        db: 数据库会话
        topic_id: 专题唯一标识
        skip: 跳过的记录数
        limit: 返回的最大记录数
    
    Returns:
        Tuple[List[TopicCategory], int]: (分类列表, 总记录数)
    """
    logger.debug(f"查询专题分类列表: topic_id={topic_id}, skip={skip}, limit={limit}")
    
    # 获取总数
    count_stmt = select(func.count()).select_from(TopicCategory).where(
        TopicCategory.topic_id == topic_id
    )
    total_result = await db.execute(count_stmt)
    total = total_result.scalar()
    
    # 获取分类列表
    stmt = select(TopicCategory).where(
        TopicCategory.topic_id == topic_id
    ).order_by(TopicCategory.sort_order.asc()).offset(skip).limit(limit)
    
    result = await db.execute(stmt)
    categories = result.scalars().all()
    
    return list(categories), total


async def update_category(
    db: AsyncSession,
    db_obj: TopicCategory,
    obj_in: TopicCategoryUpdate
) -> TopicCategory:
    """
    更新分类信息
    
    Args:
        db: 数据库会话
        db_obj: 要更新的分类对象
        obj_in: 更新数据
    
    Returns:
        TopicCategory: 更新后的分类对象
    
    Raises:
        IntegrityError: 数据库完整性约束错误
    """
    # 提前提取用于日志的变量
    category_id_for_logging = db_obj.id
    
    # 获取更新数据
    update_data = obj_in.model_dump(exclude_unset=True)
    
    logger.debug(f"更新分类: category_id={category_id_for_logging}, fields={list(update_data.keys())}")
    
    try:
        # 更新字段
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    except IntegrityError as e:
        await db.rollback()
        # ✅ 使用局部变量记录日志
        logger.error(f"更新分类失败-完整性错误: category_id={category_id_for_logging}, error={str(e)}")
        raise
    except Exception as e:
        await db.rollback()
        # ✅ 使用局部变量记录日志
        logger.error(f"更新分类失败: category_id={category_id_for_logging}, error={str(e)}")
        raise


async def remove_category(
    db: AsyncSession, 
    db_obj: TopicCategory
) -> TopicCategory:
    """
    删除分类（级联删除关联）
    
    数据库已配置 ON DELETE CASCADE，关联的直播间记录会自动删除。
    
    Args:
        db: 数据库会话
        db_obj: 要删除的分类对象
    
    Returns:
        TopicCategory: 被删除的分类对象
    
    Raises:
        Exception: 删除操作失败
    """
    # 提前提取用于日志的变量
    category_id_for_logging = db_obj.id
    rooms_count = len(db_obj.rooms) if hasattr(db_obj, 'rooms') else 0
    
    logger.warning(f"删除分类: category_id={category_id_for_logging}, rooms_count={rooms_count}")
    
    try:
        await db.delete(db_obj)
        await db.commit()
        return db_obj
    except Exception as e:
        await db.rollback()
        # ✅ 使用局部变量记录日志
        logger.error(f"删除分类失败: category_id={category_id_for_logging}, error={str(e)}")
        raise


# ==================== 直播间关联 (TopicCategoryRoom) 相关操作 ====================

async def add_room_to_category(
    db: AsyncSession,
    category_id: uuid.UUID,
    room_id: uuid.UUID,
    sort_order: int = 0
) -> TopicCategoryRoom:
    """
    将直播间添加到分类
    
    Args:
        db: 数据库会话
        category_id: 分类唯一标识
        room_id: 直播间唯一标识
        sort_order: 排序顺序，默认0
    
    Returns:
        TopicCategoryRoom: 创建的关联对象
    
    Raises:
        IntegrityError: 唯一约束冲突（直播间已存在于该分类）
    """
    # 应用层生成UUID
    association_id = uuid.uuid4()
    
    association = TopicCategoryRoom(
        id=association_id,
        category_id=category_id,
        room_id=room_id,
        sort_order=sort_order
    )
    
    # 提前提取用于日志的变量
    association_id_for_logging = association.id
    category_id_for_logging = category_id
    room_id_for_logging = room_id
    
    try:
        db.add(association)
        await db.commit()
        await db.refresh(association)
        logger.debug(
            f"添加直播间到分类成功: association_id={association_id_for_logging}, "
            f"category_id={category_id_for_logging}, room_id={room_id_for_logging}"
        )
        return association
    except IntegrityError as e:
        await db.rollback()
        # ✅ 使用局部变量记录日志
        logger.error(
            f"添加直播间失败-完整性错误: category_id={category_id_for_logging}, "
            f"room_id={room_id_for_logging}, error={str(e)}"
        )
        raise
    except Exception as e:
        await db.rollback()
        # ✅ 使用局部变量记录日志
        logger.error(
            f"添加直播间失败: category_id={category_id_for_logging}, "
            f"room_id={room_id_for_logging}, error={str(e)}"
        )
        raise


async def batch_add_rooms(
    db: AsyncSession,
    category_id: uuid.UUID,
    room_associations: List[RoomAssociation]
) -> List[TopicCategoryRoom]:
    """
    批量添加直播间到分类
    
    Args:
        db: 数据库会话
        category_id: 分类唯一标识
        room_associations: 直播间关联列表
    
    Returns:
        List[TopicCategoryRoom]: 创建的关联对象列表
    
    Raises:
        IntegrityError: 唯一约束冲突
    """
    # 提前提取用于日志的变量
    category_id_for_logging = category_id
    room_count = len(room_associations)
    
    logger.debug(f"批量添加直播间: category_id={category_id_for_logging}, count={room_count}")
    
    associations = []
    for assoc in room_associations:
        tcr = TopicCategoryRoom(
            id=uuid.uuid4(),
            category_id=category_id,
            room_id=assoc.room_id,
            sort_order=assoc.sort_order
        )
        associations.append(tcr)
    
    try:
        db.add_all(associations)
        await db.commit()
        
        # 刷新所有对象
        for assoc in associations:
            await db.refresh(assoc)
        
        return associations
    except IntegrityError as e:
        await db.rollback()
        # ✅ 使用局部变量记录日志
        logger.error(
            f"批量添加直播间失败-完整性错误: category_id={category_id_for_logging}, "
            f"count={room_count}, error={str(e)}"
        )
        raise
    except Exception as e:
        await db.rollback()
        # ✅ 使用局部变量记录日志
        logger.error(
            f"批量添加直播间失败: category_id={category_id_for_logging}, "
            f"count={room_count}, error={str(e)}"
        )
        raise


async def get_rooms_by_category(
    db: AsyncSession,
    category_id: uuid.UUID,
    skip: int = 0,
    limit: int = 100,
    # ← 新增：权限参数（用于直播间权限过滤）
    user_id: Optional[uuid.UUID] = None,  # 当前用户的public_id（匿名时为None）
    role: Optional[str] = None            # 当前用户的角色（匿名时为None）
) -> Tuple[List[Dict[str, Any]], int]:
    """
    分页获取分类下的直播间列表（带权限过滤）
    
    返回直播间信息字典列表，包含room详情和sort_order。
    按 sort_order ASC 排序。
    
    ⚠️ 注意：专题权限由Service层先检查，此方法只负责直播间权限过滤。
    
    Args:
        db: 数据库会话
        category_id: 分类唯一标识
        skip: 跳过的记录数
        limit: 返回的最大记录数
        user_id: 当前用户的public_id（匿名时为None，用于直播间权限过滤）
        role: 当前用户的角色（匿名时为None，用于直播间权限过滤）
    
    Returns:
        Tuple[List[Dict], int]: (直播间信息字典列表, 总记录数)
    """
    logger.debug(f"查询分类直播间列表: category_id={category_id}, skip={skip}, limit={limit}, user_id={user_id}, role={role}")
    
    # 构建基础查询（JOIN live_rooms表）
    base_stmt = select(
        TopicCategoryRoom.id.label('association_id'),
        TopicCategoryRoom.sort_order,
        LiveRoom.id.label('room_id'),
        LiveRoom.title,
        LiveRoom.cover_url,
        LiveRoom.user_id,
        LiveRoom.is_private,
        LiveRoom.created_at
    ).join(
        LiveRoom, TopicCategoryRoom.room_id == LiveRoom.id
    ).where(
        TopicCategoryRoom.category_id == category_id
    )
    
    # ⚠️ 核心修改：根据用户身份应用直播间权限过滤（双重权限过滤：专题权限由Service层检查，此处只过滤直播间）
    # 直播间权限过滤策略：Admin看全部 / Regular看Public+Own / Anonymous看Public
    if role in ['ADMIN', 'SUPERADMIN']:
        # 管理员：无过滤，看所有直播间
        permission_filter = None
    elif user_id:
        # 普通用户：Public OR (Private AND Own)
        permission_filter = or_(
            LiveRoom.is_private == False,
            and_(
                LiveRoom.is_private == True,
                LiveRoom.user_id == user_id
            )
        )
    else:
        # 匿名用户：Only Public
        permission_filter = LiveRoom.is_private == False
    
    # 应用权限过滤
    if permission_filter is not None:
        base_stmt = base_stmt.where(permission_filter)
    
    # 获取总数（必须应用相同的WHERE条件）
    count_stmt = select(func.count()).select_from(
        base_stmt.subquery()
    )
    total_result = await db.execute(count_stmt)
    total = total_result.scalar()
    
    # 获取直播间列表（应用排序和分页）
    stmt = base_stmt.order_by(
        TopicCategoryRoom.sort_order.asc()
    ).offset(skip).limit(limit)
    
    result = await db.execute(stmt)
    rows = result.all()
    
    # 转换为字典列表
    rooms = [
        {
            "association_id": str(row.association_id),
            "sort_order": row.sort_order,
            "room_id": str(row.room_id),
            "title": row.title,
            "cover_url": row.cover_url,
            "user_id": str(row.user_id),
            "created_at": row.created_at
        }
        for row in rows
    ]
    
    return rooms, total


async def update_room_sort_order(
    db: AsyncSession,
    category_id: uuid.UUID,
    room_sort_updates: List[Dict[str, Any]]
) -> int:
    """
    批量更新分类下直播间的排序
    
    Args:
        db: 数据库会话
        category_id: 分类唯一标识
        room_sort_updates: 更新列表，格式为 [{"room_id": UUID, "sort_order": int}, ...]
    
    Returns:
        int: 更新的记录数
    
    Raises:
        Exception: 更新操作失败
    """
    # 提前提取用于日志的变量
    category_id_for_logging = category_id
    update_count = len(room_sort_updates)
    
    logger.debug(f"批量更新排序: category_id={category_id_for_logging}, count={update_count}")
    
    updated_count = 0
    
    try:
        for item in room_sort_updates:
            stmt = sa_update(TopicCategoryRoom).where(
                and_(
                    TopicCategoryRoom.category_id == category_id,
                    TopicCategoryRoom.room_id == item["room_id"]
                )
            ).values(sort_order=item["sort_order"])
            
            result = await db.execute(stmt)
            updated_count += result.rowcount
        
        await db.commit()
        logger.debug(f"批量更新排序成功: updated_count={updated_count}")
        return updated_count
    except Exception as e:
        await db.rollback()
        # ✅ 使用局部变量记录日志
        logger.error(
            f"批量更新排序失败: category_id={category_id_for_logging}, "
            f"count={update_count}, error={str(e)}"
        )
        raise


async def remove_room_from_category(
    db: AsyncSession,
    category_id: uuid.UUID,
    room_id: uuid.UUID
) -> bool:
    """
    移除单个直播间关联
    
    Args:
        db: 数据库会话
        category_id: 分类唯一标识
        room_id: 直播间唯一标识
    
    Returns:
        bool: 是否成功删除（True表示删除了记录，False表示记录不存在）
    
    Raises:
        Exception: 删除操作失败
    """
    # 提前提取用于日志的变量
    category_id_for_logging = category_id
    room_id_for_logging = room_id
    
    logger.debug(f"移除直播间关联: category_id={category_id_for_logging}, room_id={room_id_for_logging}")
    
    try:
        stmt = delete(TopicCategoryRoom).where(
            and_(
                TopicCategoryRoom.category_id == category_id,
                TopicCategoryRoom.room_id == room_id
            )
        )
        
        result = await db.execute(stmt)
        await db.commit()
        
        success = result.rowcount > 0
        logger.debug(f"移除直播间关联结果: success={success}")
        return success
    except Exception as e:
        await db.rollback()
        # ✅ 使用局部变量记录日志
        logger.error(
            f"移除直播间关联失败: category_id={category_id_for_logging}, "
            f"room_id={room_id_for_logging}, error={str(e)}"
        )
        raise


async def batch_remove_rooms(
    db: AsyncSession,
    category_id: uuid.UUID,
    room_ids: List[uuid.UUID]
) -> int:
    """
    批量移除直播间关联
    
    Args:
        db: 数据库会话
        category_id: 分类唯一标识
        room_ids: 要移除的直播间ID列表
    
    Returns:
        int: 删除的记录数
    
    Raises:
        Exception: 删除操作失败
    """
    # 提前提取用于日志的变量
    category_id_for_logging = category_id
    room_count = len(room_ids)
    
    logger.debug(f"批量移除直播间: category_id={category_id_for_logging}, count={room_count}")
    
    try:
        stmt = delete(TopicCategoryRoom).where(
            and_(
                TopicCategoryRoom.category_id == category_id,
                TopicCategoryRoom.room_id.in_(room_ids)
            )
        )
        
        result = await db.execute(stmt)
        await db.commit()
        
        deleted_count = result.rowcount
        logger.debug(f"批量移除直播间成功: deleted_count={deleted_count}")
        return deleted_count
    except Exception as e:
        await db.rollback()
        # ✅ 使用局部变量记录日志
        logger.error(
            f"批量移除直播间失败: category_id={category_id_for_logging}, "
            f"count={room_count}, error={str(e)}"
        )
        raise


async def check_room_association_exists(
    db: AsyncSession,
    category_id: uuid.UUID,
    room_id: uuid.UUID
) -> bool:
    """
    检查关联是否已存在
    
    用于避免重复添加直播间到同一分类。
    
    Args:
        db: 数据库会话
        category_id: 分类唯一标识
        room_id: 直播间唯一标识
    
    Returns:
        bool: 关联是否存在
    """
    logger.debug(f"检查关联存在性: category_id={category_id}, room_id={room_id}")
    
    stmt = select(func.count()).select_from(TopicCategoryRoom).where(
        and_(
            TopicCategoryRoom.category_id == category_id,
            TopicCategoryRoom.room_id == room_id
        )
    )
    
    result = await db.execute(stmt)
    count = result.scalar()
    
    exists = count > 0
    logger.debug(f"关联存在性检查结果: exists={exists}")
    return exists


# ==================== 辅助查询操作 ====================

async def get_topics_by_room(
    db: AsyncSession,
    room_id: uuid.UUID,
    # ← 新增：权限参数
    user_id: Optional[uuid.UUID] = None,  # 当前用户的public_id（匿名时为None）
    role: Optional[str] = None            # 当前用户的角色（匿名时为None）
) -> List[Dict[str, Any]]:
    """
    获取指定直播间关联的专题（带权限过滤）
    
    返回专题和分类的信息，用于在直播间详情页显示"该直播间所属的专题活动"。
    
    Args:
        db: 数据库会话
        room_id: 直播间唯一标识
        user_id: 当前用户的public_id（匿名时为None，用于权限过滤）
        role: 当前用户的角色（匿名时为None，用于权限过滤）
    
    Returns:
        List[Dict]: 专题信息字典列表，包含:
            - topic_id: 专题ID
            - topic_title: 专题标题
            - topic_status: 专题状态
            - category_id: 分类ID
            - category_name: 分类名称
    """
    logger.debug(f"查询直播间关联的专题: room_id={room_id}, user_id={user_id}, role={role}")
    
    # 构建基础查询（三表JOIN: topic_category_rooms -> topic_categories -> topics）
    stmt = select(
        Topic.id.label('topic_id'),
        Topic.title.label('topic_title'),
        Topic.status.label('topic_status'),
        TopicCategory.id.label('category_id'),
        TopicCategory.name.label('category_name')
    ).select_from(TopicCategoryRoom).join(
        TopicCategory, TopicCategoryRoom.category_id == TopicCategory.id
    ).join(
        Topic, TopicCategory.topic_id == Topic.id
    ).where(
        TopicCategoryRoom.room_id == room_id
    )
    
    # ⚠️ 核心修改：根据用户身份应用不同的WHERE条件（权限过滤）
    # 将硬编码的 status='published' 改为动态权限过滤
    if role in ['ADMIN', 'SUPERADMIN']:
        # 管理员：无过滤，看所有状态的专题
        pass
    elif user_id:
        # 普通用户：Published OR (Draft/Archived AND Own)
        stmt = stmt.where(
            or_(
                Topic.status == TopicStatus.PUBLISHED,
                and_(
                    Topic.status.in_([TopicStatus.DRAFT, TopicStatus.ARCHIVED]),
                    Topic.user_id == user_id
                )
            )
        )
    else:
        # 匿名用户：Only Published
        stmt = stmt.where(Topic.status == TopicStatus.PUBLISHED)
    
    # 排序和返回
    stmt = stmt.order_by(Topic.created_at.desc())
    
    result = await db.execute(stmt)
    rows = result.all()
    
    # 转换为字典列表
    topics = [
        {
            "topic_id": str(row.topic_id),
            "topic_title": row.topic_title,
            "topic_status": row.topic_status.value if isinstance(row.topic_status, TopicStatus) else row.topic_status,
            "category_id": str(row.category_id),
            "category_name": row.category_name
        }
        for row in rows
    ]
    
    logger.debug(f"找到关联专题数量: count={len(topics)}")
    return topics


# ==================== 专题横幅管理操作 ====================

async def update_banner_url(
    db: AsyncSession, 
    topic_id: uuid.UUID, 
    banner_url: str
) -> Optional[Topic]:
    """
    更新专题横幅URL
    
    Args:
        db: 数据库会话
        topic_id: 专题ID
        banner_url: 新的横幅URL
        
    Returns:
        更新后的Topic对象或None
        
    Raises:
        Exception: 数据库操作失败
    """
    # 提前提取用于日志的变量
    topic_id_for_logging = topic_id
    
    logger.debug(f"更新专题横幅URL: topic_id={topic_id_for_logging}")
    
    try:
        # 查询专题对象
        stmt = select(Topic).where(Topic.id == topic_id)
        result = await db.execute(stmt)
        topic = result.scalar_one_or_none()
        
        if not topic:
            logger.warning(f"专题不存在: topic_id={topic_id_for_logging}")
            return None
        
        # 更新 banner_url 字段
        topic.banner_url = banner_url
        
        # 提交事务
        await db.commit()
        await db.refresh(topic)
        
        logger.debug(f"横幅URL更新成功: topic_id={topic_id_for_logging}, banner_url={banner_url}")
        return topic
        
    except Exception as e:
        await db.rollback()
        logger.error(
            f"更新横幅URL失败: topic_id={topic_id_for_logging}, error={str(e)}"
        )
        raise
