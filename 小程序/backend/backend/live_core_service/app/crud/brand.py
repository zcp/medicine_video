"""
品牌模块的CRUD层代码

本模块包含品牌模块所需的14个CRUD函数：
- Brands CRUD: 8个函数
- Brand_Topics CRUD: 3个函数
- Brand_Rooms CRUD: 3个函数
"""
import uuid
import logging
from typing import List, Optional, Tuple
from datetime import datetime

from sqlalchemy import select, func, insert, delete, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError

from app.models.brand import Brand, BrandTopic, BrandRoom
from app.models.topic import Topic, TopicStatus  # 专题模型
from app.models.live_core import LiveRoom  # 直播间模型
from app.schemas.brand import BrandCreate, BrandUpdate
from app.exceptions import (
    NotFoundException,
    DatabaseIntegrityException
)

logger = logging.getLogger(__name__)


# ==================== Brands CRUD函数 (8个) ====================

async def get_brands(
    db: AsyncSession,
    limit: int = 100,
    q: Optional[str] = None
) -> List[Brand]:
    """
    获取品牌列表（公开接口）
    
    Args:
        db: 数据库会话
        limit: 返回数量限制（默认100，最大500）
        q: 模糊搜索关键词
    
    Returns:
        品牌列表
    """
    # 兼容前端把未定义参数序列化成字符串的情况
    if q is not None:
        q = q.strip()
        if q.lower() in {"", "undefined", "null", "none"}:
            q = None

    # 构建查询
    stmt = select(Brand).where(Brand.is_active == True).order_by(Brand.sort_order)
    
    # 模糊搜索
    if q:
        stmt = stmt.where(Brand.name.ilike(f'%{q}%'))
    
    # 应用limit
    stmt = stmt.limit(min(limit, 500))
    
    # 执行查询
    result = await db.execute(stmt)
    brands = list(result.scalars().all())
    
    logger.info(f"查询品牌列表，返回{len(brands)}条记录")
    return brands


async def get_brand_with_topics(
    db: AsyncSession,
    brand_id: uuid.UUID
) -> Tuple[Optional[Brand], List[Topic]]:
    """
    获取品牌及其关联的专题列表
    
    Args:
        db: 数据库会话
        brand_id: 品牌ID
    
    Returns:
        (品牌对象, 关联的专题列表)，如果品牌不存在或is_active=False，返回(None, [])
    """
    # 查询品牌并预加载brand_topics关联（获取BrandTopic列表）
    stmt = select(Brand).options(
        selectinload(Brand.topics)  # 预加载Brand.topics关系（BrandTopic列表）
    ).where(Brand.id == brand_id, Brand.is_active == True)
    result = await db.execute(stmt)
    brand = result.scalar_one_or_none()
    
    if not brand:
        logger.warning(f"品牌不存在或已禁用: id={str(brand_id)[:8]}")
        return None, []
    
    # 获取topic_ids列表
    if not brand.topics:
        logger.info(f"品牌未关联专题: id={str(brand_id)[:8]}")
        return brand, []
    
    topic_ids = [bt.topic_id for bt in brand.topics]
    
    # 批量查询专题（仅返回status='published'的专题，按created_at降序排列）
    # 遵循设计文档Section 1777-1787行的JOIN查询逻辑
    topics_stmt = (
        select(Topic)
        .where(Topic.id.in_(topic_ids), Topic.status == TopicStatus.PUBLISHED)
        .order_by(Topic.created_at.desc())
    )
    topics_result = await db.execute(topics_stmt)
    topics = list(topics_result.scalars().all())
    
    logger.info(f"查询品牌及关联专题: id={str(brand_id)[:8]}, 专题数={len(topics)}")
    return brand, topics


async def create_brand(
    db: AsyncSession,
    brand_in: BrandCreate
) -> Brand:
    """
    创建品牌
    
    Args:
        db: 数据库会话
        brand_in: 品牌创建数据
    
    Returns:
        创建的品牌对象
    
    Raises:
        DatabaseIntegrityException: 品牌名称已存在
    """
    try:
        # 创建Brand实例（应用层生成UUID）
        brand = Brand(
            id=uuid.uuid4(),
            name=brand_in.name,
            slug=brand_in.slug,
            logo_url=brand_in.logo_url,
            description=brand_in.description,
            website_url=brand_in.website_url,
            sort_order=brand_in.sort_order if brand_in.sort_order is not None else 0,
            is_active=brand_in.is_active if brand_in.is_active is not None else True
        )
        
        db.add(brand)
        await db.commit()
        await db.refresh(brand)
        
        logger.info(f"创建品牌成功: id={str(brand.id)[:8]}, name={brand.name}")
        return brand

        # backend/live_core_service/app/crud/brand.py

        # 修改 create_brand 函数（第149-154行）
    except IntegrityError as e:
        await db.rollback()
        error_msg = str(e).lower()
        # ✅ 修复：支持中文错误消息和实际约束名
        if ("unique constraint" in error_msg or
                "uq_brands_name" in error_msg or
                "brands_name_key" in error_msg or  # 实际约束名
                "重复键违反唯一约束" in error_msg or  # 中文错误消息
                "duplicate key" in error_msg):  # 英文错误消息
            raise DatabaseIntegrityException("品牌名称已存在")
        raise

    # 修改 update_brand 函数（第271-276行）
    except IntegrityError as e:
        await db.rollback()
        error_msg = str(e).lower()
        # ✅ 修复：支持中文错误消息和实际约束名
        if ("unique constraint" in error_msg or
                "uq_brands_name" in error_msg or
                "brands_name_key" in error_msg or  # 实际约束名
                "重复键违反唯一约束" in error_msg or  # 中文错误消息
                "duplicate key" in error_msg):  # 英文错误消息
            raise DatabaseIntegrityException("品牌名称已存在")
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"创建品牌失败: {type(e).__name__}")
        raise


async def get_brands_paginated(
    db: AsyncSession,
    page: int,
    size: int,
    name: Optional[str] = None,
    is_active: Optional[bool] = None
) -> Tuple[List[Brand], int]:
    """
    获取品牌列表（管理员接口，分页）
    
    Args:
        db: 数据库会话
        page: 页码（从1开始）
        size: 每页数量
        name: 品牌名称模糊搜索
        is_active: 是否激活筛选
    
    Returns:
        (品牌列表, 总数)
    """
    # 构建筛选条件
    filters = []
    if name:
        filters.append(Brand.name.ilike(f'%{name}%'))
    if is_active is not None:
        filters.append(Brand.is_active == is_active)
    
    # 第一次查询：获取总数
    count_stmt = select(func.count()).select_from(Brand)
    if filters:
        count_stmt = count_stmt.where(and_(*filters))
    total = await db.scalar(count_stmt) or 0
    
    # 第二次查询：获取当前页数据
    stmt = select(Brand).order_by(Brand.sort_order)
    if filters:
        stmt = stmt.where(and_(*filters))
    stmt = stmt.offset((page - 1) * size).limit(size)
    
    result = await db.execute(stmt)
    brands = list(result.scalars().all())
    
    logger.info(f"管理员查询品牌列表: page={page}, size={size}, 返回{len(brands)}条，总数{total}")
    return brands, total


async def get_brand_by_id(
    db: AsyncSession,
    brand_id: uuid.UUID
) -> Optional[Brand]:
    """
    根据ID获取品牌
    
    Args:
        db: 数据库会话
        brand_id: 品牌ID
    
    Returns:
        品牌对象，如果不存在返回None
    """
    stmt = select(Brand).where(Brand.id == brand_id)
    result = await db.execute(stmt)
    brand = result.scalar_one_or_none()
    
    if brand:
        logger.info(f"查询品牌: id={str(brand_id)[:8]}, name={brand.name}")
    else:
        logger.warning(f"品牌不存在: id={str(brand_id)[:8]}")
    
    return brand


async def update_brand(
    db: AsyncSession,
    brand_id: uuid.UUID,
    brand_in: BrandUpdate
) -> Brand:
    """
    更新品牌信息
    
    Args:
        db: 数据库会话
        brand_id: 品牌ID
        brand_in: 品牌更新数据
    
    Returns:
        更新后的品牌对象
    
    Raises:
        NotFoundException: 品牌不存在
        DatabaseIntegrityException: 品牌名称已存在
    """
    try:
        # 查询品牌
        brand = await get_brand_by_id(db, brand_id)
        if not brand:
            raise NotFoundException("品牌不存在")
        
        # 更新字段（部分更新）
        update_data = brand_in.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(brand, key, value)
        
        # 提交事务
        await db.commit()
        await db.refresh(brand)
        
        logger.info(f"更新品牌成功: id={str(brand.id)[:8]}, name={brand.name}")
        return brand

    except IntegrityError as e:
        await db.rollback()
        error_msg = str(e).lower()
        # ✅ 修复：支持中文错误消息和实际约束名
        if ("unique constraint" in error_msg or
                "uq_brands_name" in error_msg or
                "brands_name_key" in error_msg or  # 实际约束名
                "重复键违反唯一约束" in error_msg or  # 中文错误消息
                "duplicate key" in error_msg):  # 英文错误消息
            raise DatabaseIntegrityException("品牌名称已存在")
        raise
    except NotFoundException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"更新品牌失败: {type(e).__name__}")
        raise


async def delete_brand(
    db: AsyncSession,
    brand_id: uuid.UUID,
    hard_delete: bool = False
) -> Brand:
    """
    删除品牌
    
    Args:
        db: 数据库会话
        brand_id: 品牌ID
        hard_delete: 是否硬删除（True=硬删除，False=软删除）
    
    Returns:
        删除的品牌对象（软删除时返回）
    
    Raises:
        NotFoundException: 品牌不存在
    """
    try:
        # 查询品牌
        brand = await get_brand_by_id(db, brand_id)
        if not brand:
            raise NotFoundException("品牌不存在")
        
        # 执行删除
        if hard_delete:
            await db.delete(brand)
            logger.warning(f"硬删除品牌: id={str(brand.id)[:8]}, name={brand.name}")
        else:
            brand.is_active = False
            logger.info(f"软删除品牌: id={str(brand.id)[:8]}, name={brand.name}")
        
        # 提交事务
        await db.commit()
        if not hard_delete:
            await db.refresh(brand)
        
        return brand
        
    except NotFoundException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"删除品牌失败: {type(e).__name__}")
        raise


async def check_brand_references(
    db: AsyncSession,
    brand_id: uuid.UUID
) -> Tuple[int, int]:
    """
    检查品牌被引用的情况
    
    Args:
        db: 数据库会话
        brand_id: 品牌ID
    
    Returns:
        (专题引用数, 直播间引用数)
    """
    # 查询专题引用数
    topic_count_stmt = select(func.count()).select_from(BrandTopic).where(
        BrandTopic.brand_id == brand_id
    )
    topic_count = await db.scalar(topic_count_stmt) or 0
    
    # 查询直播间引用数
    room_count_stmt = select(func.count()).select_from(BrandRoom).where(
        BrandRoom.brand_id == brand_id
    )
    room_count = await db.scalar(room_count_stmt) or 0
    
    logger.info(f"品牌引用检查: id={str(brand_id)[:8]}, 专题:{topic_count}, 直播间:{room_count}")
    return topic_count, room_count


# ==================== Brand_Topics CRUD函数 (3个) ====================

async def batch_add_brand_topics(
    db: AsyncSession,
    brand_id: uuid.UUID,
    topic_ids: List[uuid.UUID]
) -> int:
    """
    批量添加品牌-专题关联
    
    Args:
        db: 数据库会话
        brand_id: 品牌ID
        topic_ids: 专题ID列表
    
    Returns:
        新增的关联数量
    """
    try:
        added_count = 0
        for topic_id in topic_ids:
            # 使用insert().on_conflict_do_nothing()保证幂等性
            stmt = insert(BrandTopic).values(
                brand_id=brand_id,
                topic_id=topic_id
            )
            # PostgreSQL特定语法
            from sqlalchemy.dialects.postgresql import insert as pg_insert
            stmt = pg_insert(BrandTopic).values(
                brand_id=brand_id,
                topic_id=topic_id
            ).on_conflict_do_nothing(
                index_elements=['brand_id', 'topic_id']
            )
            
            result = await db.execute(stmt)
            if result.rowcount > 0:
                added_count += 1
        
        await db.commit()
        logger.info(f"批量添加品牌专题关联: brand_id={str(brand_id)[:8]}, 新增{added_count}条")
        return added_count
        
    except Exception as e:
        await db.rollback()
        logger.error(f"批量添加品牌专题关联失败: {type(e).__name__}")
        raise


async def delete_brand_topic(
    db: AsyncSession,
    brand_id: uuid.UUID,
    topic_id: uuid.UUID
) -> bool:
    """
    删除单个品牌-专题关联（硬删除）
    
    Args:
        db: 数据库会话
        brand_id: 品牌ID
        topic_id: 专题ID
    
    Returns:
        是否成功删除（True=成功，False=关联不存在）
    """
    try:
        stmt = delete(BrandTopic).where(
            BrandTopic.brand_id == brand_id,
            BrandTopic.topic_id == topic_id
        )
        result = await db.execute(stmt)
        await db.commit()
        
        success = result.rowcount > 0
        if success:
            logger.info(f"删除品牌专题关联: brand_id={str(brand_id)[:8]}, topic_id={str(topic_id)[:8]}")
        else:
            logger.warning(f"品牌专题关联不存在: brand_id={str(brand_id)[:8]}, topic_id={str(topic_id)[:8]}")
        
        return success
        
    except Exception as e:
        await db.rollback()
        logger.error(f"删除品牌专题关联失败: {type(e).__name__}")
        raise


async def get_brand_topics_paginated(
    db: AsyncSession,
    brand_id: uuid.UUID,
    page: int,
    size: int
) -> Tuple[List[dict], int]:
    """
    获取品牌关联的专题列表（管理员接口，分页）
    
    Args:
        db: 数据库会话
        brand_id: 品牌ID
        page: 页码（从1开始）
        size: 每页数量
    
    Returns:
        (专题信息列表, 总数)
    """
    # 第一次查询：获取总数
    count_stmt = select(func.count()).select_from(BrandTopic).where(
        BrandTopic.brand_id == brand_id
    )
    total = await db.scalar(count_stmt) or 0
    
    # 第二次查询：获取当前页数据（联表查询）
    stmt = (
        select(
            Topic.id.label('topic_id'),
            Topic.title.label('topic_title'),
            Topic.status.label('topic_status'),
            BrandTopic.created_at.label('associated_at')
        )
        .select_from(BrandTopic)
        .join(Topic, BrandTopic.topic_id == Topic.id)
        .where(BrandTopic.brand_id == brand_id)
        .order_by(BrandTopic.created_at.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    
    result = await db.execute(stmt)
    topics = [dict(row._mapping) for row in result]
    
    logger.info(f"查询品牌关联专题: brand_id={str(brand_id)[:8]}, 返回{len(topics)}条，总数{total}")
    return topics, total


async def get_brand_rooms_paginated(
    db: AsyncSession,
    brand_id: uuid.UUID,
    page: int,
    size: int
) -> Tuple[List[dict], int]:
    """
    获取品牌关联的直播间列表（管理员接口，分页）
    
    Args:
        db: 数据库会话
        brand_id: 品牌ID
        page: 页码（从1开始）
        size: 每页数量
    
    Returns:
        (直播间信息列表, 总数)
    """
    # 第一次查询：获取总数
    count_stmt = select(func.count()).select_from(BrandRoom).where(
        BrandRoom.brand_id == brand_id
    )
    total = await db.scalar(count_stmt) or 0
    
    # 第二次查询：获取当前页数据（联表查询）
    stmt = (
        select(
            LiveRoom.id.label('room_id'),
            LiveRoom.title.label('room_title'),
            LiveRoom.description.label('description'),
            LiveRoom.is_private.label('is_private'),
            LiveRoom.cover_url.label('cover_url'),
            BrandRoom.created_at.label('associated_at')
        )
        .select_from(BrandRoom)
        .join(LiveRoom, BrandRoom.room_id == LiveRoom.id)
        .where(BrandRoom.brand_id == brand_id)
        .order_by(BrandRoom.created_at.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    
    result = await db.execute(stmt)
    rooms = [dict(row._mapping) for row in result]
    
    logger.info(f"查询品牌关联直播间: brand_id={str(brand_id)[:8]}, 返回{len(rooms)}条，总数{total}")
    return rooms, total


# ==================== Brand_Rooms CRUD函数 (3个) ====================

async def bind_room_brands(
    db: AsyncSession,
    room_id: uuid.UUID,
    brand_ids: List[uuid.UUID]
) -> List[uuid.UUID]:
    """
    为直播间绑定品牌（全量替换策略）
    
    Args:
        db: 数据库会话
        room_id: 直播间ID
        brand_ids: 品牌ID列表（允许为空，表示清空绑定）
    
    Returns:
        绑定的品牌ID列表
    """
    try:
        # 1. 删除该直播间的所有旧关联
        delete_stmt = delete(BrandRoom).where(BrandRoom.room_id == room_id)
        await db.execute(delete_stmt)
            
        # 2. 批量插入新关联
        if brand_ids:
                new_relations = [
                    BrandRoom(brand_id=bid, room_id=room_id)
                    for bid in brand_ids
                ]
                db.add_all(new_relations)
        await db.commit()
        # async with 块退出时自动commit
        
        logger.info(f"绑定直播间品牌: room_id={str(room_id)[:8]}, 品牌数:{len(brand_ids)}")
        return brand_ids
        
    except Exception as e:
        await db.rollback()
        logger.error(f"绑定直播间品牌失败: {type(e).__name__}")
        raise


async def get_room_brands(
    db: AsyncSession,
    room_id: uuid.UUID
) -> List[Brand]:
    """
    获取直播间绑定的品牌列表
    
    Args:
        db: 数据库会话
        room_id: 直播间ID
    
    Returns:
        品牌列表
    """
    stmt = (
        select(Brand)
        .select_from(BrandRoom)
        .join(Brand, BrandRoom.brand_id == Brand.id)
        .where(
            BrandRoom.room_id == room_id,
            Brand.is_active == True
        )
        .order_by(Brand.sort_order)
    )
    
    result = await db.execute(stmt)
    brands = list(result.scalars().all())
    
    logger.info(f"查询直播间品牌: room_id={str(room_id)[:8]}, 返回{len(brands)}条")
    return brands


async def get_room_brands_for_tab(
    db: AsyncSession,
    room_id: uuid.UUID
) -> List[Brand]:
    """
    获取直播间品牌Tab内容（公开接口）
    
    Args:
        db: 数据库会话
        room_id: 直播间ID
    
    Returns:
        品牌列表（仅 is_active=True，16-D5）
    """
    # 与get_room_brands实现相同，但命名明确用于前端展示
    return await get_room_brands(db, room_id)


async def get_brands_by_topic(
    db: AsyncSession,
    topic_id: uuid.UUID,
) -> List[Brand]:
    """
    获取专题关联的启用品牌列表（C 端，16-D5：过滤 is_active=false）
    """
    stmt = (
        select(Brand)
        .select_from(BrandTopic)
        .join(Brand, BrandTopic.brand_id == Brand.id)
        .where(
            BrandTopic.topic_id == topic_id,
            Brand.is_active == True,
        )
        .order_by(Brand.sort_order)
    )
    result = await db.execute(stmt)
    brands = list(result.scalars().all())
    logger.info(
        "查询专题启用品牌: topic_id=%s, 返回%s条",
        str(topic_id)[:8],
        len(brands),
    )
    return brands
