"""
内容管理模块的CRUD层
负责Tags、Categories、Session_Tags的数据访问
"""
from typing import List, Literal, Optional, Tuple
from uuid import UUID
import logging

from sqlalchemy import select, delete, update, func, and_, or_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.models.content_management import Tag, Category, SessionTag, LiveRoomCategory
from app.models.live_core import LiveRoom
from app.schemas.content_management import TagCreate, TagUpdate, CategoryCreate, CategoryUpdate
from app.core.exceptions import DatabaseIntegrityException, DatabaseOperationException

logger = logging.getLogger(__name__)

# 列表字符串搜索字段（设计文档显式声明，可配置）
CATEGORY_LIST_SEARCH_FIELDS = ["name"]
TAGS_LIST_SEARCH_FIELDS = ["name"]


async def get_category_descendant_ids(
    db: AsyncSession,
    category_id: UUID,
) -> List[UUID]:
    """
    递归获取某个分类的所有子孙分类 ID（含自身）。
    """
    result = [category_id]
    stmt = select(Category.id).where(Category.parent_id == category_id, Category.is_active == True)
    rows = await db.execute(stmt)
    child_ids = [row[0] for row in rows.all()]
    for child_id in child_ids:
        result.extend(await get_category_descendant_ids(db, child_id))
    return result


# ============================================================================
# Tags CRUD Functions
# ============================================================================

async def get_tags(
    db: AsyncSession,
    is_active: Optional[bool],
    current_user_id: Optional[UUID],
    role: Optional[str],
    q: Optional[str] = None,
    search_type: Optional[str] = None,
) -> List[Tag]:
    """
    获取标签列表
    
    Args:
        db: 数据库会话
        is_active: 是否启用（可选）
        current_user_id: 当前用户ID（可选，用于权限过滤）
        role: 用户角色（可选，用于权限过滤）
        
    Returns:
        标签列表
        
    SQL级权限过滤:
    - 如果role not in ['ADMIN', 'SUPERADMIN']，则自动添加where is_active=True（🚨 必须使用大写）
    - 如果is_active参数不为None，则添加where is_active=is_active
    """
    query = select(Tag).order_by(Tag.created_at.desc())
    
    # 应用权限过滤（where条件）
    conditions = []
    
    # 如果role不是管理员，强制过滤is_active=True（🚨 必须使用大写）
    if role not in ['ADMIN', 'SUPERADMIN']:
        conditions.append(Tag.is_active == True)
    elif is_active is not None:
        # 管理员可以按is_active过滤
        conditions.append(Tag.is_active == is_active)
    
    # q / search_type：ID 精确 或 字符串字段模糊（设计文档声明的 TAGS_LIST_SEARCH_FIELDS）
    if q and str(q).strip():
        q_clean = str(q).strip()
        if search_type == 'id':
            try:
                conditions.append(Tag.id == UUID(q_clean))
            except (ValueError, TypeError):
                pass  # API 层已校验；非法时此处不追加条件
        else:
            or_clauses = [getattr(Tag, f).ilike(f"%{q_clean}%") for f in TAGS_LIST_SEARCH_FIELDS if hasattr(Tag, f)]
            if or_clauses:
                conditions.append(or_(*or_clauses))
    
    if conditions:
        query = query.where(and_(*conditions))
    
    result = await db.execute(query)
    tags = result.scalars().all()
    
    logger.info(f"查询标签列表，返回{len(tags)}条记录")
    return list(tags)


async def get_tag_by_name(db: AsyncSession, name: str) -> Optional[Tag]:
    """按精确名称查询标签（strip 后的完整名）。"""
    result = await db.execute(select(Tag).where(Tag.name == name))
    return result.scalar_one_or_none()


async def create_tag(
    db: AsyncSession,
    tag_data: TagCreate,
    *,
    source: str = "admin",
    created_by: Optional[UUID] = None,
) -> Tag:
    """
    创建标签
    
    Args:
        db: 数据库会话
        tag_data: 标签创建数据
        source: 来源 admin|user（V2）
        created_by: 创建者 public_id（V2；Admin 可空）
        
    Returns:
        创建的标签对象
        
    Raises:
        DatabaseIntegrityException: 标签名称已存在
    """
    try:
        payload = tag_data.model_dump()
        tag = Tag(**payload, source=source, created_by=created_by)
        
        # 添加到会话
        db.add(tag)
        
        # Flush（不commit）- 触发唯一性检查
        await db.flush()
        
        # 刷新对象 - 获取数据库生成的时间戳
        await db.refresh(tag)
        
        logger.info(
            f"创建标签成功: id={str(tag.id)[:8]}, name={tag.name}, source={source}"
        )
        return tag
        
    except IntegrityError as e:
        await db.rollback()
        logger.error(f"创建标签失败（唯一性冲突）: {str(e)}")
        raise DatabaseIntegrityException(f"标签名称已存在: {tag_data.name}")
    except Exception as e:
        await db.rollback()
        logger.error(f"创建标签失败（数据库错误）: {str(e)}")
        raise DatabaseOperationException("创建标签时发生数据库错误")


async def update_tag(
    db: AsyncSession,
    tag_id: UUID,
    tag_data: TagUpdate
) -> Optional[Tag]:
    """
    更新标签（部分更新）
    
    Args:
        db: 数据库会话
        tag_id: 标签ID
        tag_data: 更新数据
        
    Returns:
        更新后的标签对象，如果不存在则返回None
        
    Raises:
        DatabaseIntegrityException: 标签名称已存在
    """
    try:
        # 查询标签
        query = select(Tag).where(Tag.id == tag_id)
        result = await db.execute(query)
        tag = result.scalar_one_or_none()
        
        # 如果tag为None，返回None（由Service层处理404）
        if tag is None:
            return None
        
        # 部分更新
        update_data = tag_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(tag, field, value)
        
        # Flush
        await db.flush()
        
        # 刷新对象
        await db.refresh(tag)
        
        logger.info(f"更新标签成功: id={str(tag_id)[:8]}")
        return tag
        
    except IntegrityError as e:
        await db.rollback()
        logger.error(f"更新标签失败（唯一性冲突）: {str(e)}")
        raise DatabaseIntegrityException("标签名称已存在")


async def delete_tag(db: AsyncSession, tag_id: UUID) -> bool:
    """
    删除标签（软删除，设置is_active=False）
    
    Args:
        db: 数据库会话
        tag_id: 标签ID
        
    Returns:
        True表示成功，False表示标签不存在
        
    Raises:
        DatabaseOperationException: 数据库操作错误
    """
    try:
        # 查询标签
        query = select(Tag).where(Tag.id == tag_id)
        result = await db.execute(query)
        tag = result.scalar_one_or_none()
        
        # 如果tag为None，返回False
        if tag is None:
            return False
        
        # 软删除
        tag.is_active = False
        
        # Flush
        await db.flush()
        
        logger.info(f"软删除标签成功: id={str(tag_id)[:8]}")
        return True
    except Exception as e:
        await db.rollback()
        logger.error(f"软删除标签失败（数据库错误）: id={str(tag_id)[:8]}, error={str(e)}")
        raise DatabaseOperationException("软删除标签时发生数据库错误")


# ============================================================================
# Categories CRUD Functions
# ============================================================================

async def get_categories(
    db: AsyncSession,
    current_user_id: Optional[UUID],
    role: Optional[str],
    tree: bool = False,
) -> List[Category]:
    """
    获取分类列表（公开接口，按sort_order排序，只返回is_active=True）

    Args:
        db: 数据库会话
        current_user_id: 当前用户ID（可选）
        role: 用户角色（可选）
        tree: 【V2新增】是否返回树形结构（True=只返回一级分类并预加载children）

    Returns:
        分类列表

    SQL级权限过滤:
    - 强制过滤：where is_active=True（公开接口）
    - 按sort_order ASC排序
    - tree=True 时只返回 parent_id IS NULL 的一级分类，并预加载 children
    """
    if tree:
        # 树形模式：只查一级分类，预加载 children（按 sort_order 排序）
        # 【修复V3】三层 selectinload 覆盖 最多三级子分类，避免 Pydantic 序列化时 MissingGreenlet
        query = (
            select(Category)
            .where(Category.is_active == True)
            .where(Category.parent_id.is_(None))
            .options(
                selectinload(Category.children)
                .selectinload(Category.children)
                .selectinload(Category.children)
            )
            .order_by(Category.sort_order.asc())
        )
    else:
        # 扁平模式（V1 兼容）
        # 【修复】必须 selectinload children，否则 Pydantic model_validate 访问
        # category.children 时会触发懒加载 → 异步上下文中 MissingGreenlet 报错
        # 【修复V3】三层 selectinload 覆盖 最多三级子分类
        query = (
            select(Category)
            .where(Category.is_active == True)
            .options(
                selectinload(Category.children)
                .selectinload(Category.children)
                .selectinload(Category.children)
            )
            .order_by(Category.sort_order.asc())
        )

    result = await db.execute(query)
    # selectinload 需要 unique() 去重（防止一对多 JOIN 导致的重复行）
    categories = result.scalars().unique().all()

    logger.info(f"查询分类列表（公开，tree={tree}），返回{len(categories)}条记录")
    return list(categories)


async def get_children_categories(
    db: AsyncSession,
    parent_id: UUID,
) -> List[Category]:
    """
    【V2新增】获取指定父分类的子分类列表

    Args:
        db: 数据库会话
        parent_id: 父分类ID

    Returns:
        子分类列表（is_active=True），按 sort_order ASC 排序
    """
    query = (
        select(Category)
        .where(Category.parent_id == parent_id)
        .where(Category.is_active == True)
        .options(
            selectinload(Category.children)
            .selectinload(Category.children)
            .selectinload(Category.children)
        )
        .order_by(Category.sort_order.asc())
    )
    result = await db.execute(query)
    categories = result.scalars().unique().all()
    logger.info(f"查询子分类列表: parent_id={str(parent_id)[:8]}, count={len(categories)}")
    return list(categories)


async def get_categories_paginated(
    db: AsyncSession,
    page: int,
    size: int,
    is_active: Optional[bool],
    current_user_id: Optional[UUID],
    role: Optional[str],
    q: Optional[str] = None,
    search_type: Optional[str] = None,
    parent_id: Optional[UUID] = None,
) -> Tuple[List[Category], int]:
    """
    获取分类列表（管理员接口，分页，支持按is_active过滤）

    Args:
        db: 数据库会话
        page: 页码（从1开始）
        size: 每页数量
        is_active: 是否启用（可选）
        current_user_id: 当前用户ID（可选）
        role: 用户角色（可选）
        q: 关键词或主键ID（可选）
        search_type: id | keyword（可选）
        parent_id: 【V2新增】按父分类ID过滤（可选，传 None 表示不过滤）

    Returns:
        (分类列表, 总数)

    SQL级权限过滤:
    - 如果is_active参数不为None，则添加where is_active=is_active
    - 如果role not in ['admin', 'superadmin']，则强制添加where is_active=True（防御性编程）
    """
    # 构建基础查询
    # 【修复】selectinload children 避免 Pydantic 序列化时懒加载触发 MissingGreenlet
    # 【修复V3】三层 selectinload 覆盖 最多三级子分类，避免子分类序列化时 MissingGreenlet
    query = (
        select(Category)
        .options(
            selectinload(Category.children)
            .selectinload(Category.children)
            .selectinload(Category.children)
        )
        .order_by(Category.sort_order.asc())
    )

    # 应用权限过滤（where条件）
    conditions = []

    # 如果role不是管理员，强制过滤is_active=True（🚨 必须使用大写）
    if role not in ['ADMIN', 'SUPERADMIN']:
        conditions.append(Category.is_active == True)
    elif is_active is not None:
        # 管理员可以按is_active过滤
        conditions.append(Category.is_active == is_active)

    # 【V2新增】按 parent_id 过滤
    if parent_id is not None:
        conditions.append(Category.parent_id == parent_id)
    
    # q / search_type：ID 精确 或 字符串字段模糊（设计文档声明的 CATEGORY_LIST_SEARCH_FIELDS）
    if q and str(q).strip():
        q_clean = str(q).strip()
        if search_type == 'id':
            try:
                conditions.append(Category.id == UUID(q_clean))
            except (ValueError, TypeError):
                pass
        else:
            or_clauses = [getattr(Category, f).ilike(f"%{q_clean}%") for f in CATEGORY_LIST_SEARCH_FIELDS if hasattr(Category, f)]
            if or_clauses:
                conditions.append(or_(*or_clauses))
    
    if conditions:
        query = query.where(and_(*conditions))

    # 执行总数查询（直接基于 Category 模型，避免 selectinload 子查询问题）
    count_stmt = select(func.count()).select_from(Category)
    if conditions:
        count_stmt = count_stmt.where(and_(*conditions))
    count_result = await db.execute(count_stmt)
    total = count_result.scalar() or 0

    # 执行分页查询
    offset = (page - 1) * size
    query = query.offset(offset).limit(size)
    
    result = await db.execute(query)
    categories = result.scalars().unique().all()

    logger.info(f"查询分类列表（Admin），page={page}, size={size}, total={total}")
    return (list(categories), total)


async def create_category(db: AsyncSession, category_data: CategoryCreate) -> Category:
    """
    创建分类
    
    Args:
        db: 数据库会话
        category_data: 分类创建数据
        
    Returns:
        创建的分类对象
        
    Raises:
        DatabaseIntegrityException: 分类名称已存在
    """
    try:
        # 创建Category实例
        category = Category(**category_data.model_dump())
        
        # 添加到会话
        db.add(category)
        
        # Flush（不commit）- 触发唯一性检查
        await db.flush()
        
        # 刷新对象 - 获取数据库生成的时间戳
        await db.refresh(category)
        
        logger.info(f"创建分类成功: id={str(category.id)[:8]}, name={category.name}")
        return category
        
    except IntegrityError as e:
        await db.rollback()
        logger.error(f"创建分类失败（唯一性冲突）: {str(e)}")
        raise DatabaseIntegrityException("分类名称已存在")


async def update_category(
    db: AsyncSession,
    category_id: UUID,
    category_data: CategoryUpdate
) -> Optional[Category]:
    """
    更新分类（部分更新）
    
    Args:
        db: 数据库会话
        category_id: 分类ID
        category_data: 更新数据
        
    Returns:
        更新后的分类对象，如果不存在则返回None
        
    Raises:
        DatabaseIntegrityException: 分类名称已存在
    """
    try:
        # 查询分类
        query = select(Category).where(Category.id == category_id)
        result = await db.execute(query)
        category = result.scalar_one_or_none()
        
        # 如果category为None，返回None（由Service层处理404）
        if category is None:
            return None
        
        # 部分更新
        update_data = category_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(category, field, value)
        
        # Flush
        await db.flush()
        
        # 刷新对象
        await db.refresh(category)
        
        logger.info(f"更新分类成功: id={str(category_id)[:8]}")
        return category
        
    except IntegrityError as e:
        await db.rollback()
        logger.error(f"更新分类失败（唯一性冲突）: {str(e)}")
        raise DatabaseIntegrityException("分类名称已存在")


async def delete_category(db: AsyncSession, category_id: UUID) -> bool:
    """
    删除分类（软删除，设置is_active=False）
    
    Args:
        db: 数据库会话
        category_id: 分类ID
        
    Returns:
        True表示成功，False表示分类不存在
        
    Raises:
        DatabaseOperationException: 数据库操作错误
    """
    try:
        # 查询分类
        query = select(Category).where(Category.id == category_id)
        result = await db.execute(query)
        category = result.scalar_one_or_none()
        
        # 如果category为None，返回False
        if category is None:
            return False
        
        # 软删除
        category.is_active = False
        
        # Flush
        await db.flush()
        
        logger.info(f"软删除分类成功: id={str(category_id)[:8]}")
        return True
    except Exception as e:
        await db.rollback()
        logger.error(f"软删除分类失败（数据库错误）: id={str(category_id)[:8]}, error={str(e)}")
        raise DatabaseOperationException("软删除分类时发生数据库错误")


async def get_category_by_id(db: AsyncSession, category_id: UUID) -> Optional[Category]:
    """
    根据ID获取分类（用于更新和删除时的验证）
    
    Args:
        db: 数据库会话
        category_id: 分类ID
        
    Returns:
        分类对象，如果不存在则返回None
    """
    query = (
        select(Category)
        .where(Category.id == category_id)
        .options(
            selectinload(Category.children)
            .selectinload(Category.children)
            .selectinload(Category.children)
        )
    )
    result = await db.execute(query)
    category = result.scalar_one_or_none()

    logger.info(f"根据ID查询分类: id={str(category_id)[:8]}")
    return category


# ============================================================================
# Session_Tags CRUD Functions
# ============================================================================

async def set_session_tags(
    db: AsyncSession,
    session_id: UUID,
    tag_ids: List[UUID],
    mode: str
) -> List[Tag]:
    """
    为场次设置标签
    
    Args:
        db: 数据库会话
        session_id: 场次ID
        tag_ids: 标签ID列表
        mode: 操作模式（"replace"或"append"）
        
    Returns:
        设置后的标签列表（包含完整的Tag对象）
        
    模式处理:
    - mode="replace": 先删除所有现有关联，再创建新关联
    - mode="append": 只追加新关联（如已存在则忽略）
    
    Raises:
        DatabaseIntegrityException: 外键约束冲突
        DatabaseOperationException: 数据库操作错误
    """
    try:
        if mode == "replace":
            # 删除现有关联
            delete_query = delete(SessionTag).where(SessionTag.session_id == session_id)
            await db.execute(delete_query)
            await db.flush()
            
            # 创建新关联（空列表 = 清空）
            for tag_id in tag_ids:
                session_tag = SessionTag(session_id=session_id, tag_id=tag_id)
                db.add(session_tag)
            await db.flush()
            
            # 空列表时跳过 IN ()，避免非法 SQL
            if not tag_ids:
                logger.info(f"为场次清空标签（replace）: session_id={str(session_id)[:8]}")
                return []

            query = select(Tag).where(Tag.id.in_(tag_ids))
            result = await db.execute(query)
            tags = result.scalars().all()
            
            logger.info(f"为场次设置标签（replace）: session_id={str(session_id)[:8]}, tag_count={len(tag_ids)}")
            return list(tags)
            
        elif mode == "append":
            # 查询现有关联
            query = select(SessionTag.tag_id).where(SessionTag.session_id == session_id)
            result = await db.execute(query)
            existing_tag_ids = set(result.scalars().all())
            
            # 过滤新标签（排除已存在的）
            new_tag_ids = [tag_id for tag_id in tag_ids if tag_id not in existing_tag_ids]
            
            # 创建新关联
            for tag_id in new_tag_ids:
                session_tag = SessionTag(session_id=session_id, tag_id=tag_id)
                db.add(session_tag)
            await db.flush()
            
            # 查询所有标签列表（包括已存在的）；无标签时跳过 IN ()
            all_tag_ids = list(existing_tag_ids) + new_tag_ids
            if not all_tag_ids:
                logger.info(f"为场次追加标签（append，仍为空）: session_id={str(session_id)[:8]}")
                return []

            query = select(Tag).where(Tag.id.in_(all_tag_ids))
            result = await db.execute(query)
            tags = result.scalars().all()
            
            logger.info(f"为场次追加标签（append）: session_id={str(session_id)[:8]}, new_tag_count={len(new_tag_ids)}")
            return list(tags)
            
        else:
            raise ValueError(f"无效的mode参数: {mode}，必须是'replace'或'append'")
    except IntegrityError as e:
        await db.rollback()
        logger.error(f"为场次设置标签失败（外键约束冲突）: session_id={str(session_id)[:8]}, error={str(e)}")
        raise DatabaseIntegrityException("场次或标签不存在")
    except Exception as e:
        await db.rollback()
        logger.error(f"为场次设置标签失败（数据库错误）: session_id={str(session_id)[:8]}, error={str(e)}")
        raise DatabaseOperationException("为场次设置标签时发生数据库错误")


async def get_tags_by_session_id(db: AsyncSession, session_id: UUID) -> List[Tag]:
    """
    根据场次ID获取标签列表
    
    Args:
        db: 数据库会话
        session_id: 场次ID
        
    Returns:
        标签列表
        
    SQL级权限过滤:
    - 强制过滤：where Tag.is_active=True（只返回启用的标签）
    """
    query = (
        select(Tag)
        .join(SessionTag, Tag.id == SessionTag.tag_id)
        .where(SessionTag.session_id == session_id)
        .where(Tag.is_active == True)
        .order_by(Tag.name.asc())
    )
    
    result = await db.execute(query)
    tags = result.scalars().all()
    
    logger.info(f"查询场次标签: session_id={str(session_id)[:8]}, tag_count={len(tags)}")
    return list(tags)


async def get_sessions_by_tags(
    db: AsyncSession,
    tag_ids: List[UUID],
    match_all: bool
) -> List[UUID]:
    """
    根据标签查询场次ID列表
    
    Args:
        db: 数据库会话
        tag_ids: 标签ID列表
        match_all: 匹配模式（True=AND逻辑，False=OR逻辑）
        
    Returns:
        场次ID列表
        
    匹配模式:
    - match_all=True: AND逻辑（场次必须包含所有指定标签）
    - match_all=False: OR逻辑（场次包含任一指定标签即可）
    """
    if match_all:
        # AND逻辑（使用GROUP BY和HAVING）
        query = (
            select(SessionTag.session_id)
            .where(SessionTag.tag_id.in_(tag_ids))
            .group_by(SessionTag.session_id)
            .having(func.count(SessionTag.tag_id) == len(tag_ids))
        )
    else:
        # OR逻辑
        query = (
            select(SessionTag.session_id)
            .where(SessionTag.tag_id.in_(tag_ids))
            .distinct()
        )
    
    result = await db.execute(query)
    session_ids = result.scalars().all()
    
    logger.info(f"根据标签查询场次: tag_count={len(tag_ids)}, match_all={match_all}, session_count={len(session_ids)}")
    return list(session_ids)


async def remove_session_tag(
    db: AsyncSession,
    session_id: UUID,
    tag_id: UUID
) -> bool:
    """
    删除场次与标签的关联（硬删除）
    
    Args:
        db: 数据库会话
        session_id: 场次ID
        tag_id: 标签ID
        
    Returns:
        True表示成功，False表示关联不存在
        
    Raises:
        DatabaseOperationException: 数据库操作错误
    """
    try:
        # 构建DELETE语句
        delete_query = delete(SessionTag).where(
            SessionTag.session_id == session_id,
            SessionTag.tag_id == tag_id
        )
        
        # 执行删除
        result = await db.execute(delete_query)
        
        # Flush
        await db.flush()
        
        # 检查是否删除了记录
        deleted_count = result.rowcount
        
        logger.info(f"删除场次标签关联: session_id={str(session_id)[:8]}, tag_id={str(tag_id)[:8]}, deleted={deleted_count > 0}")
        return deleted_count > 0
    except Exception as e:
        await db.rollback()
        logger.error(f"删除场次标签关联失败（数据库错误）: session_id={str(session_id)[:8]}, tag_id={str(tag_id)[:8]}, error={str(e)}")
        raise DatabaseOperationException("删除场次标签关联时发生数据库错误")


# ============================================================================
# Room_Categories CRUD Functions
# ============================================================================

async def get_categories_by_room_id(db: AsyncSession, room_id: UUID) -> List[Category]:
    """
    根据直播间 ID 获取该直播间关联的已启用分类列表。

    Args:
        db: 数据库会话
        room_id: 直播间 ID

    Returns:
        已启用的分类列表，按 sort_order、name 排序；无关联或均已禁用时返回空列表。
    """
    query = (
        select(Category)
        .join(LiveRoomCategory, Category.id == LiveRoomCategory.category_id)
        .where(LiveRoomCategory.room_id == room_id)
        .where(Category.is_active == True)
        .options(
            selectinload(Category.children)
            .selectinload(Category.children)
            .selectinload(Category.children)
        )
        .order_by(Category.sort_order.asc(), Category.name.asc())
    )
    result = await db.execute(query)
    categories = result.scalars().unique().all()
    logger.info(f"查询直播间分类: room_id={str(room_id)[:8]}, category_count={len(categories)}")
    return list(categories)


async def set_live_room_categories(
    db: AsyncSession,
    room_id: UUID,
    category_ids: List[UUID],
    mode: Literal["replace", "append"],
    primary_category_id: Optional[UUID] = None,
) -> List[Category]:
    """
    为直播间批量设置分类。

    - 写 is_primary（未指定 primary 时默认首个为主）
    - 双写主分类到 live_rooms.category_id（过渡期）
    """
    try:
        effective_primary = primary_category_id
        if mode == "replace":
            delete_query = delete(LiveRoomCategory).where(LiveRoomCategory.room_id == room_id)
            await db.execute(delete_query)
            await db.flush()
            if not effective_primary and category_ids:
                effective_primary = category_ids[0]
            for cid in category_ids:
                is_primary = (cid == effective_primary)
                rc = LiveRoomCategory(room_id=room_id, category_id=cid, is_primary=is_primary)
                db.add(rc)
            await db.flush()
            logger.info(
                f"为直播间设置分类（replace）: room_id={str(room_id)[:8]}, "
                f"category_count={len(category_ids)}, primary={str(effective_primary)[:8] if effective_primary else None}"
            )
        elif mode == "append":
            existing_query = select(LiveRoomCategory.category_id).where(LiveRoomCategory.room_id == room_id)
            result = await db.execute(existing_query)
            existing_ids = {row[0] for row in result.all()}

            if effective_primary:
                await db.execute(
                    update(LiveRoomCategory)
                    .where(LiveRoomCategory.room_id == room_id)
                    .values(is_primary=False)
                )
                if effective_primary in existing_ids:
                    await db.execute(
                        update(LiveRoomCategory)
                        .where(LiveRoomCategory.room_id == room_id)
                        .where(LiveRoomCategory.category_id == effective_primary)
                        .values(is_primary=True)
                    )

            for cid in category_ids:
                if cid not in existing_ids:
                    is_primary = (cid == effective_primary)
                    rc = LiveRoomCategory(room_id=room_id, category_id=cid, is_primary=is_primary)
                    db.add(rc)
                    existing_ids.add(cid)
            await db.flush()

            if not effective_primary:
                # append 且未指定主分类：若尚无主分类，将现有第一条设为主
                primary_q = select(LiveRoomCategory.category_id).where(
                    LiveRoomCategory.room_id == room_id,
                    LiveRoomCategory.is_primary == True,
                )
                primary_res = await db.execute(primary_q)
                existing_primary = primary_res.scalar_one_or_none()
                if existing_primary:
                    effective_primary = existing_primary
                elif category_ids:
                    effective_primary = category_ids[0]
                    await db.execute(
                        update(LiveRoomCategory)
                        .where(LiveRoomCategory.room_id == room_id)
                        .where(LiveRoomCategory.category_id == effective_primary)
                        .values(is_primary=True)
                    )
                    await db.flush()

            logger.info(
                f"为直播间追加分类（append）: room_id={str(room_id)[:8]}, "
                f"category_count={len(category_ids)}, primary={str(effective_primary)[:8] if effective_primary else None}"
            )
        else:
            raise ValueError(f"无效的 mode 参数: {mode}，必须是 'replace' 或 'append'")

        # 双写主分类到 live_rooms.category_id
        if mode == "replace" and not category_ids:
            await db.execute(
                update(LiveRoom).where(LiveRoom.id == room_id).values(category_id=None)
            )
        elif effective_primary:
            await db.execute(
                update(LiveRoom).where(LiveRoom.id == room_id).values(category_id=effective_primary)
            )
        await db.flush()

        return await get_categories_by_room_id(db, room_id)
    except IntegrityError as e:
        await db.rollback()
        logger.error(f"为直播间设置分类失败（外键约束）: room_id={str(room_id)[:8]}, error={str(e)}")
        raise DatabaseIntegrityException("直播间或分类不存在")
    except Exception as e:
        await db.rollback()
        logger.error(f"为直播间设置分类失败: room_id={str(room_id)[:8]}, error={str(e)}")
        raise DatabaseOperationException("为直播间设置分类时发生数据库错误")


async def get_primary_category_name(
    db: AsyncSession,
    room_id: UUID,
) -> Optional[str]:
    """查询直播间 is_primary 分类名。"""
    stmt = (
        select(Category.name)
        .join(LiveRoomCategory, Category.id == LiveRoomCategory.category_id)
        .where(
            LiveRoomCategory.room_id == room_id,
            LiveRoomCategory.is_primary == True,
            Category.is_active == True,
        )
        .limit(1)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_primary_category_names_map(
    db: AsyncSession,
    room_ids: List[UUID],
) -> dict:
    """批量查询房间主分类名。"""
    if not room_ids:
        return {}
    stmt = (
        select(LiveRoomCategory.room_id, Category.name)
        .join(Category, Category.id == LiveRoomCategory.category_id)
        .where(
            LiveRoomCategory.room_id.in_(room_ids),
            LiveRoomCategory.is_primary == True,
            Category.is_active == True,
        )
    )
    result = await db.execute(stmt)
    return {row[0]: row[1] for row in result.all()}


async def delete_live_room_category(
    db: AsyncSession,
    room_id: UUID,
    category_id: UUID,
) -> bool:
    """
    删除直播间与分类的关联（硬删除）。

    Args:
        db: 数据库会话
        room_id: 直播间 ID
        category_id: 分类 ID

    Returns:
        True 表示删除成功，False 表示关联不存在
    """
    try:
        delete_query = delete(LiveRoomCategory).where(
            LiveRoomCategory.room_id == room_id,
            LiveRoomCategory.category_id == category_id,
        )
        result = await db.execute(delete_query)
        await db.flush()
        deleted = result.rowcount > 0
        logger.info(f"删除直播间分类关联: room_id={str(room_id)[:8]}, category_id={str(category_id)[:8]}, deleted={deleted}")
        return deleted
    except Exception as e:
        await db.rollback()
        logger.error(f"删除直播间分类关联失败: room_id={str(room_id)[:8]}, category_id={str(category_id)[:8]}, error={str(e)}")
        raise DatabaseOperationException("删除直播间分类关联时发生数据库错误")
