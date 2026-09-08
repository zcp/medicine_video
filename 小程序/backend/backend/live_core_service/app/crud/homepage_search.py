"""
首页与搜索模块的CRUD层

本模块负责：
- Phase1: 焦点图CRUD
- Phase2: 首页API（复杂多表JOIN查询）
- Phase3: 搜索API（跨多表全文搜索）
"""
import uuid
import re
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime

from sqlalchemy import select, func, or_, and_, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.models.homepage_search import FeaturedContent
from app.models.live_core import LiveRoom, LiveSession, SessionStatistics
from app.models.experts import Expert
from app.models.topic import Topic
from app.models.brand import Brand
from app.schemas.homepage_search import FeaturedContentCreate, FeaturedContentUpdate
from app.core.exceptions import DatabaseIntegrityException
import logging

logger = logging.getLogger(__name__)


# ==================== Featured Content CRUD ====================

async def get_featured_content_list(
    db: AsyncSession,
    include_inactive: bool = False,
    include_scheduled: bool = False
) -> List[FeaturedContent]:
    """
    获取焦点图列表
    
    Args:
        db: 数据库会话
        include_inactive: 是否包含未启用的焦点图（管理员接口使用）
        include_scheduled: 是否包含未到上线时间的焦点图（管理员接口使用）
        
    Returns:
        焦点图列表
    """
    query = select(FeaturedContent).order_by(FeaturedContent.sort_order)
    
    conditions = []
    
    # 公开接口：只返回启用的焦点图
    if not include_inactive:
        conditions.append(FeaturedContent.is_active == True)
    
    # 公开接口：只返回在有效期内的焦点图
    if not include_scheduled:
        now = datetime.utcnow()
        conditions.append(
            or_(
                FeaturedContent.start_at.is_(None),
                FeaturedContent.start_at <= now
            )
        )
        conditions.append(
            or_(
                FeaturedContent.end_at.is_(None),
                FeaturedContent.end_at >= now
            )
        )
    
    # 组合所有条件
    if conditions:
        query = query.where(and_(*conditions))
    
    # 限制返回数量
    limit = 100 if include_inactive else 10
    query = query.limit(limit)
    
    result = await db.execute(query)
    items = list(result.scalars().all())
    
    logger.info(f"查询焦点图列表，返回{len(items)}条记录，include_inactive={include_inactive}")
    
    return items


async def get_featured_content_by_id(
    db: AsyncSession,
    content_id: uuid.UUID
) -> Optional[FeaturedContent]:
    """
    根据ID获取焦点图
    
    Args:
        db: 数据库会话
        content_id: 焦点图ID
        
    Returns:
        焦点图对象，不存在时返回None
    """
    stmt = select(FeaturedContent).where(FeaturedContent.id == content_id)
    result = await db.execute(stmt)
    content = result.scalar_one_or_none()
    
    logger.info(f"查询焦点图: {str(content_id)[:8]}, 结果={'存在' if content else '不存在'}")
    
    return content


async def create_featured_content(
    db: AsyncSession,
    content_data: FeaturedContentCreate
) -> FeaturedContent:
    """
    创建焦点图
    
    Args:
        db: 数据库会话
        content_data: 焦点图创建数据
        
    Returns:
        创建的焦点图对象
        
    Raises:
        DatabaseIntegrityException: 数据库完整性错误
    """
    content_id = uuid.uuid4()
    content = FeaturedContent(
        id=content_id,
        **content_data.model_dump()
    )
    
    db.add(content)
    
    try:
        await db.commit()
        await db.refresh(content)
        
        logger.info(f"创建焦点图: {str(content_id)[:8]}, 标题={content.title}")
        
        return content
    
    except IntegrityError as e:
        await db.rollback()
        logger.error(f"创建焦点图失败: {str(e)}")
        raise DatabaseIntegrityException("创建焦点图失败")


async def update_featured_content(
    db: AsyncSession,
    content_id: uuid.UUID,
    content_data: FeaturedContentUpdate
) -> Optional[FeaturedContent]:
    """
    更新焦点图
    
    Args:
        db: 数据库会话
        content_id: 焦点图ID
        content_data: 焦点图更新数据
        
    Returns:
        更新后的焦点图对象，不存在时返回None
        
    Raises:
        DatabaseIntegrityException: 数据库完整性错误
    """
    content = await get_featured_content_by_id(db, content_id)
    
    if not content:
        return None
    
    # 提取要更新的字段
    update_data = content_data.model_dump(exclude_unset=True)
    
    # 逐个设置属性
    for key, value in update_data.items():
        setattr(content, key, value)
    
    try:
        await db.commit()
        await db.refresh(content)
        
        logger.info(f"更新焦点图: {str(content_id)[:8]}, 更新字段={list(update_data.keys())}")
        
        return content
    
    except IntegrityError as e:
        await db.rollback()
        logger.error(f"更新焦点图失败: {str(e)}")
        raise DatabaseIntegrityException("更新焦点图失败")


async def delete_featured_content(
    db: AsyncSession,
    content_id: uuid.UUID,
    soft_delete: bool = True
) -> bool:
    """
    删除焦点图
    
    Args:
        db: 数据库会话
        content_id: 焦点图ID
        soft_delete: 是否软删除（默认True）
        
    Returns:
        删除成功返回True，焦点图不存在返回False
    """
    content = await get_featured_content_by_id(db, content_id)
    
    if not content:
        return False
    
    if soft_delete:
        # 软删除：设置is_active=False
        content.is_active = False
        await db.commit()
        logger.warning(f"软删除焦点图: {str(content_id)[:8]}")
    else:
        # 硬删除
        await db.delete(content)
        await db.commit()
        logger.warning(f"硬删除焦点图: {str(content_id)[:8]}")
    
    return True


async def get_featured_content_count(
    db: AsyncSession,
    include_inactive: bool = False
) -> int:
    """
    获取焦点图总数
    
    Args:
        db: 数据库会话
        include_inactive: 是否包含未启用的焦点图
        
    Returns:
        焦点图总数
    """
    query = select(func.count()).select_from(FeaturedContent)
    
    if not include_inactive:
        query = query.where(FeaturedContent.is_active == True)
    
    result = await db.execute(query)
    count = result.scalar_one()
    
    logger.info(f"查询焦点图总数: {count}, include_inactive={include_inactive}")
    
    return count


async def get_featured_content_list_paginated(
    db: AsyncSession,
    page: int = 1,
    size: int = 10,
    q: Optional[str] = None,
    search_type: Optional[str] = None
) -> Tuple[List[FeaturedContent], int]:
    """
    获取焦点图列表（管理员用，分页）。
    不施加 is_active、start_at、end_at 过滤，返回全部记录的分页结果及总数。
    支持按 q、search_type 过滤（与前端《列表筛选与搜索规范》对齐）：id 精确或 title/subtitle 模糊。

    Args:
        db: 数据库会话
        page: 页码（从 1 开始）
        size: 每页数量（1-100）
        q: 关键词；空或不传时不施加关键词/ID 过滤
        search_type: 搜索类型，id=按ID精确，name 或不传=按标题/副标题模糊

    Returns:
        (当前页焦点图列表, 总条数)
    """
    if page < 1:
        page = 1
    if size < 1:
        size = 10
    elif size > 100:
        size = 100

    offset = (page - 1) * size

    # 构建 where_conditions（与前端列表筛选与搜索规范对齐）
    where_conditions = []
    if q:
        if search_type == "id":
            try:
                featured_id = uuid.UUID(q)
                where_conditions.append(FeaturedContent.id == featured_id)
            except ValueError:
                where_conditions.append(text("1=0"))
        else:
            search_pattern = f"%{q}%"
            where_conditions.append(
                or_(
                    FeaturedContent.title.ilike(search_pattern),
                    FeaturedContent.subtitle.ilike(search_pattern)
                )
            )

    # 总数
    count_query = select(func.count()).select_from(FeaturedContent)
    if where_conditions:
        count_query = count_query.where(and_(*where_conditions))
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    # 当前页列表，按 sort_order 升序、created_at 降序
    query = (
        select(FeaturedContent)
        .order_by(
            FeaturedContent.sort_order.asc(),
            FeaturedContent.created_at.desc()
        )
        .offset(offset)
        .limit(size)
    )
    if where_conditions:
        query = query.where(and_(*where_conditions))
    result = await db.execute(query)
    items = list(result.scalars().all())

    logger.info(
        f"查询焦点图列表（分页），page={page}, size={size}, total={total}, q={q}, search_type={search_type}"
    )

    return items, total


# ==================== Homepage API CRUD (Phase2) ====================

async def get_homepage_rooms_with_details(
    db: AsyncSession,
    page: int = 1,
    size: int = 10,
    category_id: Optional[uuid.UUID] = None,
    sort: str = "heat:desc"
) -> Tuple[List[Dict[str, Any]], int]:
    """
    获取首页直播间列表（含详细信息）
    
    使用复杂的多表JOIN查询获取直播间、场次、专家、统计信息。
    
    Args:
        db: 数据库会话
        page: 页码（从1开始）
        size: 每页数量（1-100）
        category_id: 分类ID筛选（可选）
        sort: 排序规则（heat:desc, start_time:asc, created_at:desc）
        
    Returns:
        (rooms_list, total_count): 直播间列表和总数
    """
    # 参数校验
    if page < 1:
        page = 1
    if size < 1:
        size = 10
    elif size > 100:
        size = 100
    
    offset = (page - 1) * size
    
    logger.info(f"获取首页直播间列表: page={page}, size={size}, category_id={category_id}, sort={sort}")
    
    # 发现层硬规则：排除不公开房间；分类筛选权威 = live_room_categories + 子孙展开
    category_where = "WHERE lr.is_private = false"
    if category_id is not None:
        from app.crud.content_management import get_category_descendant_ids
        descendant_ids = await get_category_descendant_ids(db, category_id)
        descendants_str = ",".join([f"'{did}'" for did in descendant_ids])
        category_where += f"""
            AND EXISTS (
                SELECT 1 FROM live_room_categories lrc
                WHERE lrc.room_id = lr.id AND lrc.category_id IN ({descendants_str})
            )
        """
    
    # 构建SQL查询（使用原生SQL以支持LATERAL JOIN）
    sql_str = """
        SELECT 
            -- 直播间基础信息
            lr.id AS room_id,
            lr.title AS room_title,
            lr.cover_url AS room_cover_url,
            lr.description AS room_summary,
            lr.user_id AS room_owner_user_id,
            lr.created_at AS room_created_at,
            (
                SELECT c.name
                FROM live_room_categories lrc2
                JOIN categories c ON c.id = lrc2.category_id
                WHERE lrc2.room_id = lr.id AND lrc2.is_primary = true
                LIMIT 1
            ) AS primary_category_name,
            
            -- 场次信息
            ls.id AS session_id,
            ls.status AS session_status,
            ls.start_time AS session_start_time,
            
            -- 场次专家信息（通过LATERAL JOIN获取优先级最高的专家）
            lse.expert_id AS session_expert_id,
            lse.role AS session_expert_role,
            
            -- 专家详细信息（仅启用专家；禁用专家不挂 host，对齐《16》P44）
            e.id AS expert_id,
            e.name AS expert_name,
            e.title AS expert_title,
            e.hospital AS expert_hospital,
            e.avatar_url AS expert_avatar_url,
            
            -- 统计信息
            ss.peak_viewer_count,
            ss.total_viewer_count,
            -- 注意：SessionStatistics表中没有total_message_count, total_play_count, duration_seconds字段
            -- 这些字段在Service层会被设置为None
            NULL AS total_message_count,
            NULL AS total_play_count,
            -- duration_seconds可以从end_time - start_time计算，但这里先设为NULL，由Service层处理
            CASE 
                WHEN ls.end_time IS NOT NULL AND ls.start_time IS NOT NULL 
                THEN EXTRACT(EPOCH FROM (ls.end_time - ls.start_time))::INTEGER
                ELSE NULL
            END AS duration_seconds
            
        FROM live_rooms lr
        LEFT JOIN LATERAL (
            SELECT id, status, start_time, end_time, room_id
            FROM live_sessions
            WHERE room_id = lr.id
            ORDER BY created_at DESC
            LIMIT 1
        ) ls ON TRUE
        -- 获取场次关联的优先级最高的启用专家（主讲 > 主持 > 嘉宾；跳过 is_active=false）
        LEFT JOIN LATERAL (
            SELECT lse.expert_id, lse.role
            FROM live_session_experts lse
            INNER JOIN experts e_active ON e_active.id = lse.expert_id AND e_active.is_active = true
            WHERE lse.session_id = ls.id
            ORDER BY 
                CASE lse.role
                    WHEN '主讲' THEN 1
                    WHEN '主持' THEN 2
                    WHEN '嘉宾' THEN 3
                    ELSE 4
                END,
                lse.sort_order ASC
            LIMIT 1
        ) lse ON TRUE
        LEFT JOIN experts e ON lse.expert_id = e.id
        LEFT JOIN session_statistics ss ON ls.id = ss.session_id
    """
    if category_where:
        sql_str += category_where
    sql_str += """
        ORDER BY 
            CASE 
                WHEN :sort = 'start_time:asc' THEN ls.start_time
                ELSE NULL
            END ASC,
            CASE 
                WHEN :sort = 'created_at:desc' THEN lr.created_at
                ELSE NULL
            END DESC
        LIMIT :size OFFSET :offset
    """
    sql = text(sql_str)
    
    # COUNT查询
    count_sql_str = """
        SELECT COUNT(DISTINCT lr.id)
        FROM live_rooms lr
    """
    if category_where:
        count_sql_str += category_where
    count_sql = text(count_sql_str)
    
    # 执行COUNT查询
    count_params = {}
    count_result = await db.execute(
        count_sql,
        count_params
    )
    total_count = count_result.scalar_one()
    
    # 执行主查询
    query_params = {
        "sort": sort,
        "size": size,
        "offset": offset
    }
    result = await db.execute(
        sql,
        query_params
    )
    
    # 将结果映射为字典列表
    rooms_list = []
    for row in result:
        room_dict = {
            "room_id": row.room_id,
            "room_title": row.room_title,
            "room_cover_url": row.room_cover_url,
            "room_summary": row.room_summary,
            "room_owner_user_id": row.room_owner_user_id,
            "room_created_at": row.room_created_at,
            "primary_category_name": row.primary_category_name,
            
            "session_id": row.session_id,
            "session_status": row.session_status,
            "session_start_time": row.session_start_time,
            
            "session_expert_id": row.session_expert_id,
            "session_expert_role": row.session_expert_role,
            
            "expert_id": row.expert_id,
            "expert_name": row.expert_name,
            "expert_title": row.expert_title,
            "expert_hospital": row.expert_hospital,
            "expert_avatar_url": row.expert_avatar_url,
            
            "peak_viewer_count": row.peak_viewer_count,
            "total_viewer_count": row.total_viewer_count,
            "total_message_count": row.total_message_count,
            "total_play_count": row.total_play_count,
            "duration_seconds": row.duration_seconds
        }
        rooms_list.append(room_dict)
    
    logger.info(f"获取首页直播间列表成功: 返回{len(rooms_list)}条, 总数{total_count}")
    
    return rooms_list, total_count


# ==================== Search API CRUD (Phase3) ====================

async def search_global_resources(
    db: AsyncSession,
    keyword: str,
    page: int = 1,
    size: int = 10,
    resource_types: Optional[List[str]] = None,
    category_id: Optional[uuid.UUID] = None
) -> Tuple[List[Dict[str, Any]], int]:
    """
    全局搜索（跨多个表）
    
    使用UNION ALL合并多个表的搜索结果。
    
    Args:
        db: 数据库会话
        keyword: 搜索关键词（至少2个字符）
        page: 页码（从1开始）
        size: 每页数量（1-50）
        resource_types: 资源类型筛选（['room', 'expert', 'topic', 'brand']）
        category_id: 分类ID筛选（仅对room有效）
        
    Returns:
        (results_list, total_count): 搜索结果列表和总数
    """
    # 参数校验
    if len(keyword.strip()) < 2:
        raise ValueError("搜索关键词至少需要2个字符")
    
    if page < 1:
        page = 1
    if size < 1:
        size = 10
    elif size > 50:
        size = 50
    
    # 默认搜索所有类型
    if not resource_types:
        resource_types = ['room', 'expert', 'topic', 'brand']
    
    offset = (page - 1) * size
    keyword_pattern = f"%{keyword.strip()}%"
    
    logger.info(f"全局搜索: keyword={keyword}, types={resource_types}, page={page}, size={size}")

    desc_ids_str = ""
    if category_id is not None:
        from app.crud.content_management import get_category_descendant_ids
        desc_ids = await get_category_descendant_ids(db, category_id)
        desc_ids_str = ",".join([f"'{did}'" for did in desc_ids])
    
    # 构建子查询列表
    union_queries = []
    
    # room搜索（保留 is_private = false）
    if 'room' in resource_types:
        category_filter = ""
        if category_id is not None:
            category_filter = f"""AND EXISTS (
                SELECT 1 FROM live_room_categories lrc
                WHERE lrc.room_id = live_rooms.id AND lrc.category_id IN ({desc_ids_str})
            )"""
        union_queries.append(f"""
            SELECT 
                'room' AS type,
                id,
                title,
                description AS summary,
                cover_url,
                (CASE 
                    WHEN title ILIKE :keyword THEN 1.0
                    WHEN description  ILIKE :keyword THEN 0.7
                    ELSE 0.5
                END) AS match_score,
                NULL AS metadata_json
            FROM live_rooms
            WHERE is_private = false
                AND (title ILIKE :keyword OR description  ILIKE :keyword)
                {category_filter}
        """)
    
    # expert搜索（含科室词表名；分类筛 experts.category_id）
    if 'expert' in resource_types:
        expert_category_filter = ""
        if category_id is not None:
            expert_category_filter = f"AND experts.category_id IN ({desc_ids_str})"
        union_queries.append(f"""
            SELECT 
                'expert' AS type,
                experts.id,
                experts.name AS title,
                experts.bio AS summary,
                experts.avatar_url AS cover_url,
                (CASE 
                    WHEN experts.name ILIKE :keyword THEN 1.0
                    WHEN experts.bio ILIKE :keyword THEN 0.8
                    WHEN experts.expertise_areas ILIKE :keyword THEN 0.6
                    WHEN ed.name ILIKE :keyword THEN 0.7
                    ELSE 0.5
                END) AS match_score,
                jsonb_build_object('hospital', experts.hospital, 'title', experts.title) AS metadata_json
            FROM experts
            LEFT JOIN expert_departments ed ON ed.id = experts.department_id
            WHERE (
                experts.name ILIKE :keyword
                OR experts.bio ILIKE :keyword
                OR experts.expertise_areas ILIKE :keyword
                OR ed.name ILIKE :keyword
                OR experts.department ILIKE :keyword
            )
                AND experts.is_active = true
                {expert_category_filter}
        """)
    
    # topic搜索
    if 'topic' in resource_types:
        union_queries.append("""
            SELECT 
                'topic' AS type,
                id,
                title,
                description AS summary,
                banner_url AS cover_url,
                (CASE 
                    WHEN title ILIKE :keyword THEN 1.0
                    WHEN description ILIKE :keyword THEN 0.7
                    ELSE 0.5
                END) AS match_score,
                NULL AS metadata_json
            FROM topics
            WHERE (title ILIKE :keyword OR description ILIKE :keyword)
                AND status = 'published'
        """)
    
    # brand搜索
    if 'brand' in resource_types:
        union_queries.append("""
            SELECT 
                'brand' AS type,
                id,
                name AS title,
                description AS summary,
                logo_url AS cover_url,
                (CASE 
                    WHEN name ILIKE :keyword THEN 1.0
                    WHEN description ILIKE :keyword THEN 0.7
                    ELSE 0.5
                END) AS match_score,
                NULL AS metadata_json
            FROM brands
            WHERE (name ILIKE :keyword OR description ILIKE :keyword)
                AND is_active = true
        """)
    
    if not union_queries:
        logger.warning("未指定有效的搜索类型")
        return [], 0
    
    # 合并查询
    full_query = f"""
        WITH search_results AS (
            {' UNION ALL '.join(union_queries)}
        )
        SELECT *
        FROM search_results
        ORDER BY match_score DESC
        LIMIT :size OFFSET :offset
    """
    
    # COUNT查询
    count_query = f"""
        WITH search_results AS (
            {' UNION ALL '.join(union_queries)}
        )
        SELECT COUNT(*)
        FROM search_results
    """
    
    # 执行COUNT查询
    count_params = {"keyword": keyword_pattern}
    count_result = await db.execute(
        text(count_query),
        count_params
    )
    total_count = count_result.scalar_one()
    
    # 执行主查询
    query_params = {
        "keyword": keyword_pattern,
        "size": size,
        "offset": offset
    }
    result = await db.execute(
        text(full_query),
        query_params
    )
    
    # 将结果映射为字典列表
    results_list = []
    for row in result:
        result_dict = {
            "type": row.type,
            "id": row.id,
            "title": row.title,
            "summary": row.summary,
            "cover_url": row.cover_url,
            "match_score": float(row.match_score),
            "metadata_json": row.metadata_json
        }
        results_list.append(result_dict)
    
    logger.info(f"全局搜索成功: 返回{len(results_list)}条, 总数{total_count}")
    
    return results_list, total_count
