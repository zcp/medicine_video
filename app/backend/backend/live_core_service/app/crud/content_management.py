"""
内容管理模块的CRUD层
负责Tags、Categories、Session_Tags的数据访问
"""
from dataclasses import dataclass
from typing import List, Literal, Optional, Tuple
from uuid import UUID
import logging

from sqlalchemy import select, delete, update, func, and_, or_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.models.content_management import Tag, Category, SessionTag, LiveRoomCategory
from app.models.experts import Expert
from app.models.expert_departments import ExpertDepartment
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

    用于父分类筛选时聚合所有子分类数据。
    使用 Python 递归而非 WITH RECURSIVE CTE，对最深 2-3 层的分类树足够高效。

    Args:
        db: 数据库会话
        category_id: 父分类 ID

    Returns:
        [category_id, child_id_1, child_id_2, ...] — 自身 + 所有子孙 ID
    """
    result = [category_id]
    stmt = select(Category.id).where(Category.parent_id == category_id, Category.is_active == True)
    rows = await db.execute(stmt)
    child_ids = [row[0] for row in rows.all()]
    for child_id in child_ids:
        result.extend(await get_category_descendant_ids(db, child_id))
    return result


@dataclass(frozen=True)
class CategoryReferenceCount:
    """分类引用统计（阶段0 统一计数口径）

    - expert_all / expert_active：物理引用 vs 前台可见（管理列表计数用 active 口径）
    - department_count：科室引用（删除检查此前漏计）
    - room_count：直播间关联
    - active_child_count：启用子分类（级联停用范围预览）
    """
    expert_all: int = 0
    expert_active: int = 0
    department_count: int = 0
    room_count: int = 0
    active_child_count: int = 0

    @property
    def total(self) -> int:
        """删除阻断判定：任一引用（含子分类）非零即阻止非 force 删除"""
        return (
            self.expert_all
            + self.department_count
            + self.room_count
            + self.active_child_count
        )


async def count_category_references(
    db: AsyncSession,
    category_id: UUID,
) -> CategoryReferenceCount:
    """
    统一统计分类引用（删除检查 / 管理列表计数 / 迁移预览共用同一口径）。

    Args:
        db: 数据库会话
        category_id: 分类ID

    Returns:
        CategoryReferenceCount: 五类引用计数
    """
    # 专家：全部 + 启用 两口径一次查询
    expert_stmt = select(
        func.count(Expert.id),
        func.count(Expert.id).filter(Expert.is_active == True),
    ).where(Expert.category_id == category_id)
    expert_all, expert_active = (await db.execute(expert_stmt)).one()

    # 科室
    dept_stmt = (
        select(func.count())
        .select_from(ExpertDepartment)
        .where(ExpertDepartment.category_id == category_id)
    )
    department_count = (await db.execute(dept_stmt)).scalar_one()

    # 直播间关联
    room_stmt = (
        select(func.count())
        .select_from(LiveRoomCategory)
        .where(LiveRoomCategory.category_id == category_id)
    )
    room_count = (await db.execute(room_stmt)).scalar_one()

    # 启用子分类
    child_stmt = (
        select(func.count())
        .select_from(Category)
        .where(Category.parent_id == category_id, Category.is_active == True)
    )
    active_child_count = (await db.execute(child_stmt)).scalar_one()

    return CategoryReferenceCount(
        expert_all=expert_all or 0,
        expert_active=expert_active or 0,
        department_count=department_count or 0,
        room_count=room_count or 0,
        active_child_count=active_child_count or 0,
    )


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


async def get_tags_paginated(
    db: AsyncSession,
    page: int,
    size: int,
    is_active: Optional[bool],
    current_user_id: Optional[UUID],
    role: Optional[str],
    q: Optional[str] = None,
    search_type: Optional[str] = None,
) -> Tuple[List[Tag], int]:
    """
    获取标签列表（管理员接口，分页，支持按is_active过滤）

    Args:
        db: 数据库会话
        page: 页码（从1开始）
        size: 每页数量
        is_active: 是否启用（可选）
        current_user_id: 当前用户ID（可选）
        role: 用户角色（可选）
        q: 关键词或主键 ID（可选）
        search_type: id | keyword（可选）

    Returns:
        (标签列表, 总数)

    SQL级权限过滤:
    - 如果is_active参数不为None，则添加where is_active=is_active
    - 如果role not in ['ADMIN', 'SUPERADMIN']，则强制添加where is_active=True（防御性编程）
    """
    # 构建基础查询
    query = select(Tag).order_by(Tag.created_at.desc())

    # 应用权限过滤（where条件）
    conditions = []

    # 如果role不是管理员，强制过滤is_active=True（🚨 必须使用大写）
    if role not in ['ADMIN', 'SUPERADMIN']:
        conditions.append(Tag.is_active == True)
    elif is_active is not None:
        # 管理员可以按is_active过滤
        conditions.append(Tag.is_active == is_active)

    # q / search_type：ID 精确 或 字符串字段模糊（TAGS_LIST_SEARCH_FIELDS）
    if q and str(q).strip():
        q_clean = str(q).strip()
        if search_type == 'id':
            try:
                conditions.append(Tag.id == UUID(q_clean))
            except (ValueError, TypeError):
                pass
        else:
            or_clauses = [getattr(Tag, f).ilike(f"%{q_clean}%") for f in TAGS_LIST_SEARCH_FIELDS if hasattr(Tag, f)]
            if or_clauses:
                conditions.append(or_(*or_clauses))

    if conditions:
        query = query.where(and_(*conditions))

    # 执行总数查询（与分页列表使用同一套 WHERE 条件）
    count_query = select(func.count()).select_from(query.subquery())
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    # 执行分页查询
    offset = (page - 1) * size
    query = query.offset(offset).limit(size)

    result = await db.execute(query)
    tags = result.scalars().all()

    logger.info(f"查询标签列表（Admin分页），page={page}, size={size}, total={total}")
    return list(tags), total


async def get_tag_by_name(db: AsyncSession, name: str) -> Optional[Tag]:
    """按精确名称查询标签（strip 后的完整名；软删同名可查到，供 resolve "不复活"判断）。"""
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
        source: 来源 admin|user（V2；默认 admin 保持向后兼容）
        created_by: 创建者 public_id（V2；Admin 手工创建可传 None）
        
    Returns:
        创建的标签对象
        
    Raises:
        DatabaseIntegrityException: 标签名称已存在
    """
    try:
        # 创建Tag实例（V2：落溯源字段）
        tag = Tag(**tag_data.model_dump(), source=source, created_by=created_by)
        
        # 添加到会话
        db.add(tag)
        
        # Flush（不commit）- 触发唯一性检查
        await db.flush()
        
        # 刷新对象 - 获取数据库生成的时间戳
        await db.refresh(tag)
        
        logger.info(f"创建标签成功: id={str(tag.id)[:8]}, name={tag.name}")
        return tag
        
    except IntegrityError as e:
        await db.rollback()
        logger.error(f"创建标签失败（唯一性冲突）: {str(e)}")
        raise DatabaseIntegrityException("标签名称已存在")
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
    include_counts: bool = False
) -> List[Category]:
    """
    获取分类列表（按sort_order排序，只返回is_active=True）
    
    Args:
        db: 数据库会话
        current_user_id: 当前用户ID（可选）
        role: 用户角色（可选）
        include_counts: 是否附加 expert_count 和 room_count（管理端使用）
        
    Returns:
        分类列表
    """
    query = (
        select(Category)
        .where(Category.is_active == True)
        .order_by(Category.sort_order.asc())
    )
    
    result = await db.execute(query)
    categories = result.scalars().all()

    # 阶段1 防御过滤：父分类不可见（不存在或 inactive）的子分类不返回，
    # 防止停用父分类后出现孤儿节点（删除路径已级联停用，此为双保险）
    active_ids = {c.id for c in categories}
    categories = [
        c for c in categories
        if c.parent_id is None or c.parent_id in active_ids
    ]
    
    if include_counts:
        cat_ids = [c.id for c in categories]
        if cat_ids:
            # 统计每个分类下的专家数（直接查 Expert.category_id，无关 department_id 是否为空）
            expert_count_q = (
                select(
                    Expert.category_id,
                    func.count(Expert.id.distinct())
                )
                .where(Expert.category_id.in_(cat_ids))
                .where(Expert.is_active == True)
                .group_by(Expert.category_id)
            )
            expert_result = await db.execute(expert_count_q)
            expert_counts = dict(expert_result.all())
            
            # 统计每个分类下的直播间数
            room_count_q = (
                select(
                    LiveRoomCategory.category_id,
                    func.count(LiveRoomCategory.room_id.distinct())
                )
                .where(LiveRoomCategory.category_id.in_(cat_ids))
                .group_by(LiveRoomCategory.category_id)
            )
            room_result = await db.execute(room_count_q)
            room_counts = dict(room_result.all())
            
            for c in categories:
                c.expert_count = expert_counts.get(c.id, 0)
                c.room_count = room_counts.get(c.id, 0)

            # 父分类聚合: 将子分类计数累加到父分类
            children_map: dict = {}
            for c in categories:
                if c.parent_id:
                    children_map.setdefault(c.parent_id, []).append(c.id)
            for c in categories:
                for child_id in children_map.get(c.id, []):
                    c.expert_count += expert_counts.get(child_id, 0)
                    c.room_count += room_counts.get(child_id, 0)
    
    logger.info(f"查询分类列表，返回{len(categories)}条记录")
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
    include_counts: bool = False,
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
        
    Returns:
        (分类列表, 总数)
        
    SQL级权限过滤:
    - 如果is_active参数不为None，则添加where is_active=is_active
    - 如果role not in ['admin', 'superadmin']，则强制添加where is_active=True（防御性编程）
    """
    # 构建基础查询
    query = select(Category).order_by(Category.sort_order.asc())
    
    # 应用权限过滤（where条件）
    conditions = []
    
    # 如果role不是管理员，强制过滤is_active=True（🚨 必须使用大写）
    if role not in ['ADMIN', 'SUPERADMIN']:
        conditions.append(Category.is_active == True)
    elif is_active is not None:
        # 管理员可以按is_active过滤
        conditions.append(Category.is_active == is_active)
    
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
    
    # 执行总数查询（与分页列表使用同一套 WHERE 条件）
    count_query = select(func.count()).select_from(query.subquery())
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0
    
    # 执行分页查询
    offset = (page - 1) * size
    query = query.offset(offset).limit(size)
    
    result = await db.execute(query)
    categories = result.scalars().all()
    
    if include_counts and categories:
        cat_ids = [c.id for c in categories]
        expert_count_q = (
            select(
                Expert.category_id,
                func.count(Expert.id.distinct())
            )
            .where(Expert.category_id.in_(cat_ids))
            .where(Expert.is_active == True)
            .group_by(Expert.category_id)
        )
        expert_result = await db.execute(expert_count_q)
        expert_counts = dict(expert_result.all())
        
        room_count_q = (
            select(
                LiveRoomCategory.category_id,
                func.count(LiveRoomCategory.room_id.distinct())
            )
            .where(LiveRoomCategory.category_id.in_(cat_ids))
            .group_by(LiveRoomCategory.category_id)
        )
        room_result = await db.execute(room_count_q)
        room_counts = dict(room_result.all())
        
        for c in categories:
            c.expert_count = expert_counts.get(c.id, 0)
            c.room_count = room_counts.get(c.id, 0)
    
    logger.info(f"查询分类列表（Admin），page={page}, size={size}, total={total}")
    return (list(categories), total)


async def get_categories_stats(
    db: AsyncSession,
) -> dict:
    """
    获取分类系统的聚合统计数据（管理端仪表盘用）
    
    Returns:
        {
            "total_categories": 分类总数,
            "active_categories": 启用分类数,
            "total_departments": 科室总数,
            "verified_departments": 已审核科室数,
            "unverified_departments": 未审核科室数,
            "auto_matched": 自动匹配来源数,
        }
    """
    # 分类统计
    total_cat = await db.scalar(select(func.count(Category.id)))
    active_cat = await db.scalar(
        select(func.count(Category.id)).where(Category.is_active == True)
    )

    # 科室统计
    total_dept = await db.scalar(select(func.count(ExpertDepartment.id)))
    verified_dept = await db.scalar(
        select(func.count(ExpertDepartment.id)).where(ExpertDepartment.is_verified == True)
    )
    unverified_dept = await db.scalar(
        select(func.count(ExpertDepartment.id)).where(ExpertDepartment.is_verified == False)
    )
    auto_matched = await db.scalar(
        select(func.count(ExpertDepartment.id)).where(ExpertDepartment.source == "auto_match")
    )

    return {
        "total_categories": total_cat or 0,
        "active_categories": active_cat or 0,
        "total_departments": total_dept or 0,
        "verified_departments": verified_dept or 0,
        "unverified_departments": unverified_dept or 0,
        "auto_matched_departments": auto_matched or 0,
    }


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


async def get_category_by_slug(db: AsyncSession, slug: str) -> Optional[Category]:
    """按 slug 查询启用分类（禁删规则/兜底迁移目标用）"""
    stmt = select(Category).where(Category.slug == slug, Category.is_active == True)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_category_id_by_name(
    db: AsyncSession,
    name: str,
    prefer_sub: bool = True,
) -> Optional[UUID]:
    """
    按名称查启用分类 ID（阶段6A：收敛全仓按名查询点，消除同名歧义）。

    部分唯一索引（uq_root/uq_sub）允许同名不同级并存，直接 scalar_one_or_none()
    会抛 MultipleResultsFound——本函数统一处理：
    - 唯一命中 → 直接返回
    - 同名多行 → prefer_sub=True 时二级（parent_id 非空）优先，否则一级优先

    Args:
        db: 数据库会话
        name: 分类名称
        prefer_sub: 同名歧义时是否优先二级分类（默认 True，匹配算法二级优先）

    Returns:
        Optional[UUID]: 分类 ID；无匹配返回 None
    """
    stmt = select(Category).where(
        Category.name == name,
        Category.is_active == True,  # noqa: E712
    )
    cats = (await db.execute(stmt)).scalars().all()
    if not cats:
        return None
    if len(cats) == 1:
        return cats[0].id
    # 同名歧义：按层级偏好选择
    preferred = [c for c in cats if (c.parent_id is not None) == prefer_sub]
    chosen = preferred or list(cats)
    return chosen[0].id


MIGRATE_SCOPE_VALUES = ("experts", "departments", "rooms", "all")


async def migrate_category_references(
    db: AsyncSession,
    category_ids: List[UUID],
    target_id: Optional[UUID],
    scope: str = "all",
) -> dict:
    """
    迁移/解除分类引用（专家 + 科室 + 房间关联），单事务内由 Service 编排。

    语义（阶段1 删除闭环 / 阶段3 迁移端点复用同一实现）：
    - target_id 非空：科室先于专家迁移（V1.1 约定，同事务无差别）；房间关联迁移
      （已关联 target 的房间去重）
    - target_id 为空：仅房间解除场景允许（专家/科室必须已由调用方处理）
    - scope 控制迁移范围：experts / departments / rooms / all（默认 all）

    Args:
        db: 数据库会话
        category_ids: 分类 ID 列表（删除=子树含自身；迁移端点=单分类）
        target_id: 迁移目标分类 ID；None 表示解除房间关联（弱引用）
        scope: 迁移范围（experts/departments/rooms/all）

    Returns:
        {"expert_count", "department_count", "room_count"} 迁移统计
    """
    stats = {"expert_count": 0, "department_count": 0, "room_count": 0}

    if scope not in MIGRATE_SCOPE_VALUES:
        raise ValueError(f"非法 scope: {scope}（可选 {MIGRATE_SCOPE_VALUES}）")

    migrate_experts = scope in ("experts", "all")
    migrate_departments = scope in ("departments", "all")
    migrate_rooms = scope in ("rooms", "all")

    if target_id is not None:
        if migrate_departments:
            res = await db.execute(
                update(ExpertDepartment)
                .where(ExpertDepartment.category_id.in_(category_ids))
                .values(category_id=target_id)
                .execution_options(synchronize_session=False)
            )
            stats["department_count"] = res.rowcount or 0

        if migrate_experts:
            res = await db.execute(
                update(Expert)
                .where(Expert.category_id.in_(category_ids))
                .values(category_id=target_id)
                .execution_options(synchronize_session=False)
            )
            stats["expert_count"] = res.rowcount or 0

        if migrate_rooms:
            # 房间关联：迁移 + 去重
            src_room_stmt = (
                select(LiveRoomCategory.room_id)
                .where(LiveRoomCategory.category_id.in_(category_ids))
            )
            src_rooms = (await db.execute(src_room_stmt)).scalars().all()
            src_room_ids = list(src_rooms)
            stats["room_count"] = len(src_room_ids)
            if src_room_ids:
                dup_rooms = set(
                    (
                        await db.execute(
                            select(LiveRoomCategory.room_id).where(
                                LiveRoomCategory.category_id == target_id,
                                LiveRoomCategory.room_id.in_(src_room_ids),
                            )
                        )
                    ).scalars().all()
                )
                await db.execute(
                    delete(LiveRoomCategory)
                    .where(LiveRoomCategory.category_id.in_(category_ids))
                    .execution_options(synchronize_session=False)
                )
                for room_id in src_room_ids:
                    if room_id not in dup_rooms:
                        db.add(LiveRoomCategory(room_id=room_id, category_id=target_id))
    else:
        # 无 target：解除房间弱引用（专家/科室不允许无 target 迁移，调用方需保证）
        if migrate_rooms:
            res = await db.execute(
                delete(LiveRoomCategory)
                .where(LiveRoomCategory.category_id.in_(category_ids))
                .execution_options(synchronize_session=False)
            )
            stats["room_count"] = res.rowcount or 0

    return stats


async def cascade_disable_category_tree(
    db: AsyncSession,
    category_ids: List[UUID],
) -> int:
    """
    级联软删分类子树（全部 is_active=False）。

    Args:
        db: 数据库会话
        category_ids: 子树分类 ID 列表（含自身）

    Returns:
        实际停用数量（仅统计原本启用的）
    """
    res = await db.execute(
        update(Category)
        .where(Category.id.in_(category_ids), Category.is_active == True)
        .values(is_active=False)
        .execution_options(synchronize_session=False)
    )
    disabled = res.rowcount or 0
    logger.info("级联停用分类子树: ids=%d, disabled=%d", len(category_ids), disabled)
    return disabled


async def get_category_by_id(db: AsyncSession, category_id: UUID) -> Optional[Category]:
    """
    根据ID获取分类（用于更新和删除时的验证）
    
    Args:
        db: 数据库会话
        category_id: 分类ID
        
    Returns:
        分类对象，如果不存在则返回None
    """
    query = select(Category).where(Category.id == category_id)
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
            
            # 创建新关联
            for tag_id in tag_ids:
                session_tag = SessionTag(session_id=session_id, tag_id=tag_id)
                db.add(session_tag)
            await db.flush()

            # V2：空列表 = 清空，跳过 IN () 避免非法 SQL
            if not tag_ids:
                logger.info(f"为场次清空标签（replace）: session_id={str(session_id)[:8]}")
                return []

            # 查询标签列表（用于返回）
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
            
            # 查询所有标签列表（包括已存在的）
            all_tag_ids = list(existing_tag_ids) + new_tag_ids
            # V2：无可关联时早退，跳过 IN () 避免非法 SQL
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

async def get_categories_by_room_id(db: AsyncSession, room_id: UUID) -> List[LiveRoomCategory]:
    """
    根据直播间 ID 获取该直播间的 LiveRoomCategory 关联列表（含 is_primary 标记与已启用 Category）。

    只返回 category.is_active=True 的关联（已禁用分类不出现在结果中）。

    Args:
        db: 数据库会话
        room_id: 直播间 ID

    Returns:
        LiveRoomCategory 关联列表（.category 已预加载），按 Category.sort_order、name 排序；无关联或均已禁用时返回空列表。
    """
    query = (
        select(LiveRoomCategory)
        .join(Category, Category.id == LiveRoomCategory.category_id)
        .where(LiveRoomCategory.room_id == room_id)
        .where(Category.is_active == True)
        .options(selectinload(LiveRoomCategory.category))
        .order_by(Category.sort_order.asc(), Category.name.asc())
    )
    result = await db.execute(query)
    lrcs = result.scalars().all()
    logger.info(f"查询直播间分类关联: room_id={str(room_id)[:8]}, category_count={len(lrcs)}")
    return list(lrcs)


async def set_live_room_categories(
    db: AsyncSession,
    room_id: UUID,
    category_ids: List[UUID],
    mode: Literal["replace", "append"],
    primary_category_id: Optional[UUID] = None,
) -> List[LiveRoomCategory]:
    """
    为直播间批量设置分类。

    自动管理 is_primary：根据传入的 primary_category_id 设置主分类。

    Args:
        db: 数据库会话
        room_id: 直播间 ID
        category_ids: 分类 ID 列表
        mode: replace=先删后插，append=仅插入（已存在则忽略）
        primary_category_id: 主分类 ID

    Returns:
        设置后的 LiveRoomCategory 关联列表（含 is_primary 标记）

    Raises:
        DatabaseIntegrityException: 外键不存在等约束冲突
        DatabaseOperationException: 其他数据库错误
    """
    try:
        if mode == "replace":
            delete_query = delete(LiveRoomCategory).where(LiveRoomCategory.room_id == room_id)
            await db.execute(delete_query)
            await db.flush()
            for cid in category_ids:
                is_primary = (cid == primary_category_id)
                rc = LiveRoomCategory(room_id=room_id, category_id=cid, is_primary=is_primary)
                db.add(rc)
            # 确保至少有一个主分类：如果未指定 primary_category_id 且 category_ids 非空，自动将第一个设为主分类
            if not primary_category_id and category_ids:
                await db.flush()
                update_first = (
                    update(LiveRoomCategory)
                    .where(LiveRoomCategory.room_id == room_id)
                    .where(LiveRoomCategory.category_id == category_ids[0])
                    .values(is_primary=True)
                )
                await db.execute(update_first)
            await db.flush()
            logger.info(f"为直播间设置分类（replace）: room_id={str(room_id)[:8]}, category_count={len(category_ids)}")
        elif mode == "append":
            existing_query = select(LiveRoomCategory.category_id).where(LiveRoomCategory.room_id == room_id)
            result = await db.execute(existing_query)
            existing_ids = {row[0] for row in result.all()}
            
            # 如果指定了新的主分类，先将现有的主分类取消
            if primary_category_id:
                update_query = (
                    update(LiveRoomCategory)
                    .where(LiveRoomCategory.room_id == room_id)
                    .values(is_primary=False)
                )
                await db.execute(update_query)
                
                # 如果新的主分类已经在现有列表中，更新它
                if primary_category_id in existing_ids:
                    update_primary_query = (
                        update(LiveRoomCategory)
                        .where(LiveRoomCategory.room_id == room_id)
                        .where(LiveRoomCategory.category_id == primary_category_id)
                        .values(is_primary=True)
                    )
                    await db.execute(update_primary_query)

            for cid in category_ids:
                if cid not in existing_ids:
                    is_primary = (cid == primary_category_id)
                    rc = LiveRoomCategory(room_id=room_id, category_id=cid, is_primary=is_primary)
                    db.add(rc)
                    existing_ids.add(cid)
            await db.flush()
            logger.info(f"为直播间追加分类（append）: room_id={str(room_id)[:8]}, category_count={len(category_ids)}")
        else:
            raise ValueError(f"无效的 mode 参数: {mode}，必须是 'replace' 或 'append'")
        return await get_categories_by_room_id(db, room_id)
    except IntegrityError as e:
        await db.rollback()
        logger.error(f"为直播间设置分类失败（外键约束）: room_id={str(room_id)[:8]}, error={str(e)}")
        raise DatabaseIntegrityException("直播间或分类不存在")
    except Exception as e:
        await db.rollback()
        logger.error(f"为直播间设置分类失败: room_id={str(room_id)[:8]}, error={str(e)}")
        raise DatabaseOperationException("为直播间设置分类时发生数据库错误")


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
