"""
专家模块 CRUD 层

本模块封装所有与 Expert、UserExpertSubscription、LiveSessionExpert 模型相关的数据库操作。
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
from app.models.experts import Expert, UserExpertSubscription, LiveSessionExpert
from app.models.expert_departments import ExpertDepartment
from app.schemas.experts import ExpertCreate, ExpertUpdate
from app.exceptions import DatabaseIntegrityException, InvalidParameterException

# 配置日志
logger = logging.getLogger(__name__)


# ==================== Expert CRUD 函数 ====================

async def create_expert(
    db: AsyncSession,
    expert_data: ExpertCreate
) -> Expert:
    """
    创建专家
    
    Args:
        db: 数据库会话
        expert_data: 专家创建数据
    
    Returns:
        Expert: 创建的专家对象
    
    Raises:
        DatabaseIntegrityException: 如果user_id已绑定到其他专家档案
    """
    # 在应用层生成UUID
    expert_id = uuid.uuid4()
    
    # 创建Expert实例（model_dump 已含 is_active；若未包含则显式传入默认 True）
    dump_data = expert_data.model_dump()
    if "is_active" not in dump_data:
        dump_data["is_active"] = getattr(expert_data, "is_active", True)
    expert = Expert(
        id=expert_id,
        **dump_data
    )
    
    # 提前提取用于日志的变量
    expert_id_for_logging = str(expert_id)[:8]
    expert_name = expert_data.name
    
    try:
        db.add(expert)
        await db.flush()  # 触发唯一性检查
        await db.refresh(expert)  # 获取数据库生成的时间戳
        logger.info(f"创建专家成功: id={expert_id_for_logging}, name={expert_name}")
        return expert
    except IntegrityError as e:
        await db.rollback()
        logger.error(f"创建专家失败（唯一性冲突）: id={expert_id_for_logging}, error={str(e)}")
        raise DatabaseIntegrityException("该用户已绑定到其他专家档案")
    except Exception as e:
        await db.rollback()
        logger.error(f"创建专家失败: id={expert_id_for_logging}, error={str(e)}")
        raise


async def get_expert(
    db: AsyncSession,
    expert_id: uuid.UUID
) -> Optional[Expert]:
    """
    根据ID获取单个专家
    
    Args:
        db: 数据库会话
        expert_id: 专家唯一标识
    
    Returns:
        Optional[Expert]: 专家对象，如果不存在则返回None
    """
    expert_id_for_logging = str(expert_id)[:8]
    logger.debug(f"查询专家: expert_id={expert_id_for_logging}")
    
    stmt = select(Expert).options(
        joinedload(Expert.category),
        joinedload(Expert.department_ref),
    ).where(Expert.id == expert_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_expert_by_user_id(
    db: AsyncSession,
    user_id: uuid.UUID
) -> Optional[Expert]:
    """
    根据user_id获取专家（用于检查user_id是否已被绑定）
    
    Args:
        db: 数据库会话
        user_id: 用户公开ID
    
    Returns:
        Optional[Expert]: 专家对象，如果不存在则返回None
    """
    user_id_for_logging = str(user_id)[:8]
    logger.debug(f"查询专家（按user_id）: user_id={user_id_for_logging}")
    
    stmt = select(Expert).where(Expert.user_id == user_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_featured_experts(
    db: AsyncSession,
    limit: int = 10
) -> List[Expert]:
    """
    获取首页推荐专家列表（按sort_order排序）
    
    Args:
        db: 数据库会话
        limit: 返回记录数限制（默认10，最大50）
    
    Returns:
        List[Expert]: 推荐专家列表
    """
    stmt = select(Expert).options(
        joinedload(Expert.department_ref),
        joinedload(Expert.category),
    ).where(
        Expert.is_featured == True,
        Expert.is_active == True
    ).order_by(
        Expert.sort_order.asc(),
        Expert.created_at.desc()
    ).limit(limit)
    
    result = await db.execute(stmt)
    experts = result.scalars().all()
    logger.info(f"查询推荐专家列表，返回{len(experts)}条记录")
    return experts


async def get_experts_public_list(
    db: AsyncSession,
    page: int = 1,
    size: int = 20,
    category_id: Optional[uuid.UUID] = None,
    keyword: Optional[str] = None,
    department: Optional[str] = None,
    hospital: Optional[str] = None,
    is_active: Optional[bool] = None,
    sort: Optional[str] = None,
) -> Tuple[List[Expert], int]:
    """
    获取公开专家列表（分页，默认仅返回已启用的专家）
    支持按分类ID、关键词、科室、医院筛选，支持自定义排序。

    Args:
        db: 数据库会话
        page: 页码（从1开始）
        size: 每页数量（1-100）
        category_id: 分类ID筛选（可选）
        keyword: 关键词模糊搜索（姓名/医院/科室/擅长领域/简介，可选）
        department: 科室筛选（可选）
        hospital: 医院筛选（可选）
        is_active: 启用状态筛选（可选，默认仅启用专家）
        sort: 排序规则（可选，格式 field:direction）

    Returns:
        (专家列表, 总条数)
    """
    if page < 1:
        page = 1
    if size < 1:
        size = 20
    elif size > 100:
        size = 100

    # 默认仅返回已启用专家，除非显式传入 is_active=False
    if is_active is None or is_active is True:
        conditions = [Expert.is_active == True]
    else:
        conditions = []

    # 关键词模糊搜索（姓名/医院/科室/擅长领域/简介）
    if keyword and keyword.strip():
        kw = f"%{keyword.strip()}%"
        conditions.append(
            or_(
                Expert.name.ilike(kw),
                Expert.hospital.ilike(kw),
                # V7 后 department 列已删除，改为搜索 expert_departments.name
                Expert.department_id.in_(
                    select(ExpertDepartment.id).where(ExpertDepartment.name.ilike(kw))
                ),
                Expert.expertise_areas.ilike(kw),
                Expert.bio.ilike(kw),
            )
        )

    # 科室筛选
    if department and department.strip():
        dept_kw = f"%{department.strip()}%"
        dept_ids_subq = select(ExpertDepartment.id).where(
            ExpertDepartment.name.ilike(dept_kw)
        )
        conditions.append(Expert.department_id.in_(dept_ids_subq))

    # 医院筛选
    if hospital and hospital.strip():
        conditions.append(Expert.hospital.ilike(f"%{hospital.strip()}%"))

    # 分类ID筛选（含子分类——父分类聚合子分类数据）
    if category_id is not None:
        from app.models.content_management import Category
        from app.crud.content_management import get_category_descendant_ids
        cat_stmt = select(Category.name).where(
            Category.id == category_id,
            Category.is_active == True
        )
        cat_result = await db.execute(cat_stmt)
        category_name = cat_result.scalar_one_or_none()

        if category_name:
            descendant_ids = await get_category_descendant_ids(db, category_id)
            conditions.append(Expert.category_id.in_(descendant_ids))
            logger.info(f"公开专家列表按分类过滤: category_id={str(category_id)[:8]}, name={category_name}, descendant_count={len(descendant_ids)}")
        else:
            # 阶段5：分类不存在/停用 → 400（不再静默返回空列表；与首页房间筛选语义对齐）
            logger.warning(f"公开专家列表分类不存在或已禁用: category_id={str(category_id)[:8]}")
            raise InvalidParameterException("分类不存在或已停用", code=4001)

    # 总数
    count_query = select(func.count()).select_from(Expert).where(and_(*conditions))
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    # 排序解析
    order_clauses = []
    if sort and sort.strip():
        sort_field_map = {
            "name": Expert.name,
            "title": Expert.title,
            "hospital": Expert.hospital,
            # "department": 已删除 — V7 迁移已从 DB 删除 experts.department 列
            "sort_order": Expert.sort_order,
            "created_at": Expert.created_at,
            "updated_at": Expert.updated_at,
        }
        for part in sort.strip().split(","):
            part = part.strip()
            if ":" in part:
                field_name, direction = part.rsplit(":", 1)
                field_name = field_name.strip()
                direction = direction.strip().lower()
            else:
                field_name = part
                direction = "asc"
            column = sort_field_map.get(field_name)
            if column is not None:
                order_clauses.append(column.desc() if direction == "desc" else column.asc())

    if not order_clauses:
        order_clauses = [Expert.sort_order.asc(), Expert.name.asc()]

    # 分页列表
    offset = (page - 1) * size
    query = (
        select(Expert)
        .options(
            joinedload(Expert.category),
            joinedload(Expert.department_ref),
        )
        .where(and_(*conditions))
        .order_by(*order_clauses)
        .offset(offset)
        .limit(size)
    )
    result = await db.execute(query)
    experts = list(result.scalars().all())

    logger.info(f"查询公开专家列表: page={page}, size={size}, keyword={keyword}, total={total}, returned={len(experts)}")
    return experts, total


async def get_experts_multi_and_total(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 10,
    name: Optional[str] = None,
    is_featured: Optional[bool] = None,
    is_active: Optional[bool] = None,
    is_verified: Optional[bool] = None,
    hospital: Optional[str] = None,
    sort: Optional[str] = None,
    category_id: Optional[uuid.UUID] = None,
    department_id: Optional[uuid.UUID] = None
) -> Tuple[List[Expert], int]:
    """
    分页获取专家列表，支持筛选和排序
    
    Args:
        db: 数据库会话
        skip: 跳过的记录数
        limit: 返回记录数限制
        name: 专家姓名筛选（模糊匹配）
        is_featured: 是否推荐筛选
        is_active: 是否启用筛选（用于 Admin 列表按启用状态过滤）
        is_verified: 审核状态筛选
        hospital: 医院筛选（模糊匹配）
        sort: 排序参数（格式：field:order,field:order，默认：sort_order:asc,created_at:desc）
    
    Returns:
        Tuple[List[Expert], int]: (专家列表, 总数)
    """
    # 构建基础查询
    stmt = select(Expert).options(
        joinedload(Expert.category),
        joinedload(Expert.department_ref),
    )

    # 应用筛选条件
    conditions = []
    if name is not None:
        conditions.append(Expert.name.ilike(f'%{name}%'))
    if is_featured is not None:
        conditions.append(Expert.is_featured == is_featured)
    if is_active is not None:
        conditions.append(Expert.is_active == is_active)
    if is_verified is not None:
        conditions.append(Expert.is_verified == is_verified)
    if hospital is not None:
        conditions.append(Expert.hospital.ilike(f'%{hospital}%'))
    if category_id is not None:
        from app.crud.content_management import get_category_descendant_ids
        descendant_ids = await get_category_descendant_ids(db, category_id)
        conditions.append(Expert.category_id.in_(descendant_ids))
    if department_id is not None:
        conditions.append(Expert.department_id == department_id)
    
    if conditions:
        stmt = stmt.where(and_(*conditions))
    
    # 执行COUNT查询获取总数
    count_stmt = select(func.count()).select_from(stmt.subquery())
    count_result = await db.execute(count_stmt)
    total = count_result.scalar_one()
    
    # 解析sort参数并应用排序
    if sort is None:
        # 默认排序：sort_order:asc,created_at:desc
        stmt = stmt.order_by(Expert.sort_order.asc(), Expert.created_at.desc())
    else:
        # 解析sort参数（格式：field:order,field:order）
        order_by_list = []
        for sort_item in sort.split(','):
            parts = sort_item.strip().split(':')
            if len(parts) == 2:
                field_name, order = parts[0].strip(), parts[1].strip().lower()
                if hasattr(Expert, field_name):
                    field = getattr(Expert, field_name)
                    if order == 'asc':
                        order_by_list.append(field.asc())
                    elif order == 'desc':
                        order_by_list.append(field.desc())
        
        if order_by_list:
            stmt = stmt.order_by(*order_by_list)
        else:
            # 如果解析失败，使用默认排序
            stmt = stmt.order_by(Expert.sort_order.asc(), Expert.created_at.desc())
    
    # 应用分页
    stmt = stmt.offset(skip).limit(limit)
    
    # 执行查询获取数据列表
    result = await db.execute(stmt)
    experts = result.scalars().all()
    
    logger.info(f"查询专家列表，返回{len(experts)}条记录，总数={total}")
    return (experts, total)


async def update_expert(
    db: AsyncSession,
    expert_id: uuid.UUID,
    expert_data: ExpertUpdate
) -> Optional[Expert]:
    """
    更新专家（部分更新）
    
    Args:
        db: 数据库会话
        expert_id: 专家唯一标识
        expert_data: 专家更新数据（部分更新）
    
    Returns:
        Optional[Expert]: 更新后的专家对象，如果不存在则返回None
    
    Raises:
        DatabaseIntegrityException: 如果更新user_id导致唯一性冲突
    """
    # 查询专家
    stmt = select(Expert).where(Expert.id == expert_id)
    result = await db.execute(stmt)
    expert = result.scalar_one_or_none()
    
    if expert is None:
        return None
    
    # 提前提取用于日志的变量
    expert_id_for_logging = str(expert_id)[:8]
    
    try:
        # 部分更新
        update_data = expert_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(expert, field, value)
        
        await db.flush()
        await db.refresh(expert)
        logger.info(f"更新专家成功: id={expert_id_for_logging}")
        return expert
    except IntegrityError as e:
        await db.rollback()
        logger.error(f"更新专家失败（唯一性冲突）: id={expert_id_for_logging}, error={str(e)}")
        raise DatabaseIntegrityException("该用户已绑定到其他专家档案")
    except Exception as e:
        await db.rollback()
        logger.error(f"更新专家失败: id={expert_id_for_logging}, error={str(e)}")
        raise


async def delete_expert(
    db: AsyncSession,
    expert_id: uuid.UUID
) -> bool:
    """
    删除专家（软删除：设置 is_active=False）
    
    Args:
        db: 数据库会话
        expert_id: 专家唯一标识
    
    Returns:
        bool: 如果删除成功返回True，如果专家不存在返回False
    """
    # 查询专家
    stmt = select(Expert).where(Expert.id == expert_id)
    result = await db.execute(stmt)
    expert = result.scalar_one_or_none()
    
    if expert is None:
        return False
    
    # 提前提取用于日志的变量
    expert_id_for_logging = str(expert_id)[:8]
    
    try:
        # 软删除：设置 is_active=False
        expert.is_active = False
        await db.flush()
        await db.refresh(expert)
        logger.warning(f"删除专家（软删除为 is_active=false）: id={expert_id_for_logging}")
        return True
    except Exception as e:
        await db.rollback()
        logger.error(f"删除专家失败: id={expert_id_for_logging}, error={str(e)}")
        raise


# ==================== UserExpertSubscription CRUD 函数 ====================

async def create_subscription(
    db: AsyncSession,
    user_id: uuid.UUID,
    expert_id: uuid.UUID
) -> UserExpertSubscription:
    """
    创建用户关注专家记录
    
    Args:
        db: 数据库会话
        user_id: 用户公开ID
        expert_id: 专家ID
    
    Returns:
        UserExpertSubscription: 创建的关注记录对象
    
    Raises:
        DatabaseIntegrityException: 如果用户已关注该专家
    """
    # 在应用层生成UUID
    subscription_id = uuid.uuid4()
    
    # 创建UserExpertSubscription实例
    subscription = UserExpertSubscription(
        id=subscription_id,
        user_id=user_id,
        expert_id=expert_id
    )
    
    # 提前提取用于日志的变量
    user_id_for_logging = str(user_id)[:8]
    expert_id_for_logging = str(expert_id)[:8]
    
    try:
        db.add(subscription)
        await db.flush()  # 触发唯一性检查
        await db.refresh(subscription)
        logger.info(f"创建关注记录成功: user_id={user_id_for_logging}, expert_id={expert_id_for_logging}")
        return subscription
    except IntegrityError as e:
        await db.rollback()
        logger.error(f"创建关注记录失败（唯一性冲突）: user_id={user_id_for_logging}, expert_id={expert_id_for_logging}, error={str(e)}")
        raise DatabaseIntegrityException("您已关注该专家")
    except Exception as e:
        await db.rollback()
        logger.error(f"创建关注记录失败: user_id={user_id_for_logging}, expert_id={expert_id_for_logging}, error={str(e)}")
        raise


async def get_subscription(
    db: AsyncSession,
    user_id: uuid.UUID,
    expert_id: uuid.UUID
) -> Optional[UserExpertSubscription]:
    """
    查询用户是否已关注专家
    
    Args:
        db: 数据库会话
        user_id: 用户公开ID
        expert_id: 专家ID
    
    Returns:
        Optional[UserExpertSubscription]: 关注记录对象，如果不存在则返回None
    """
    user_id_for_logging = str(user_id)[:8]
    expert_id_for_logging = str(expert_id)[:8]
    logger.debug(f"查询关注记录: user_id={user_id_for_logging}, expert_id={expert_id_for_logging}")
    
    stmt = select(UserExpertSubscription).where(
        and_(
            UserExpertSubscription.user_id == user_id,
            UserExpertSubscription.expert_id == expert_id
        )
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_user_subscriptions(
    db: AsyncSession,
    user_id: uuid.UUID
) -> List[UserExpertSubscription]:
    """
    获取用户关注的所有专家列表（预加载专家信息）
    
    Args:
        db: 数据库会话
        user_id: 用户公开ID
    
    Returns:
        List[UserExpertSubscription]: 关注记录列表（包含预加载的专家信息）
    """
    user_id_for_logging = str(user_id)[:8]
    
    stmt = select(UserExpertSubscription).where(
        UserExpertSubscription.user_id == user_id
    ).order_by(
        UserExpertSubscription.created_at.desc()
    ).options(
        selectinload(UserExpertSubscription.expert)
    )
    
    result = await db.execute(stmt)
    subscriptions = result.scalars().all()
    logger.info(f"查询用户关注列表: user_id={user_id_for_logging}, 返回{len(subscriptions)}条记录")
    return subscriptions


async def delete_subscription(
    db: AsyncSession,
    user_id: uuid.UUID,
    expert_id: uuid.UUID
) -> bool:
    """
    删除用户关注记录（硬删除）
    
    Args:
        db: 数据库会话
        user_id: 用户公开ID
        expert_id: 专家ID
    
    Returns:
        bool: 如果删除成功返回True，如果记录不存在返回False
    """
    # 查询关注记录
    stmt = select(UserExpertSubscription).where(
        and_(
            UserExpertSubscription.user_id == user_id,
            UserExpertSubscription.expert_id == expert_id
        )
    )
    result = await db.execute(stmt)
    subscription = result.scalar_one_or_none()
    
    if subscription is None:
        return False
    
    # 提前提取用于日志的变量
    user_id_for_logging = str(user_id)[:8]
    expert_id_for_logging = str(expert_id)[:8]
    
    try:
        await db.delete(subscription)
        await db.flush()
        logger.info(f"删除关注记录成功: user_id={user_id_for_logging}, expert_id={expert_id_for_logging}")
        return True
    except Exception as e:
        await db.rollback()
        logger.error(f"删除关注记录失败: user_id={user_id_for_logging}, expert_id={expert_id_for_logging}, error={str(e)}")
        raise


async def get_subscriptions_by_expert_ids(
    db: AsyncSession,
    user_id: uuid.UUID,
    expert_ids: List[uuid.UUID]
) -> List[UserExpertSubscription]:
    """
    批量查询用户是否关注了指定的专家列表
    
    Args:
        db: 数据库会话
        user_id: 用户公开ID
        expert_ids: 专家ID列表
    
    Returns:
        List[UserExpertSubscription]: 关注记录列表
    """
    user_id_for_logging = str(user_id)[:8]
    logger.debug(f"批量查询关注记录: user_id={user_id_for_logging}, expert_ids数量={len(expert_ids)}")
    
    if not expert_ids:
        return []
    
    stmt = select(UserExpertSubscription).where(
        and_(
            UserExpertSubscription.user_id == user_id,
            UserExpertSubscription.expert_id.in_(expert_ids)
        )
    )
    result = await db.execute(stmt)
    return result.scalars().all()


# ==================== LiveSessionExpert CRUD 函数 ====================

async def get_session_experts(
    db: AsyncSession,
    session_id: uuid.UUID,
    role: Optional[str] = None,
    viewer_role: Optional[str] = None,
) -> List[LiveSessionExpert]:
    """
    获取场次的专家列表（支持按角色筛选）

    数据关联治理（P1-1，D4 定稿）：viewer_role 非管理员（ADMIN/SUPERADMIN）时
    过滤已停用专家（Expert.is_active == False 不返回），SQL 级过滤任何调用方无法绕过；
    管理员保持全量，便于后台排查已停用专家关联的场次。

    Args:
        db: 数据库会话
        session_id: 直播场次ID
        role: 专家角色筛选（可选，主讲/主持/嘉宾）
        viewer_role: 查看者角色（可选，用于过滤已停用专家；None=匿名）

    Returns:
        List[LiveSessionExpert]: 场次专家关联记录列表（包含预加载的专家信息）
    """
    session_id_for_logging = str(session_id)[:8]
    
    stmt = select(LiveSessionExpert).where(
        LiveSessionExpert.session_id == session_id
    )
    
    if role is not None:
        stmt = stmt.where(LiveSessionExpert.role == role)
    
    # 数据关联治理（P1-1，D4 定稿）：非管理员过滤已停用专家
    if viewer_role not in ('ADMIN', 'SUPERADMIN'):
        stmt = stmt.join(Expert, Expert.id == LiveSessionExpert.expert_id).where(
            Expert.is_active == True
        )
    
    stmt = stmt.order_by(
        LiveSessionExpert.sort_order.asc(),
        LiveSessionExpert.created_at.asc(),
        LiveSessionExpert.id.asc()
    ).options(
        selectinload(LiveSessionExpert.expert)
    )
    
    result = await db.execute(stmt)
    session_experts = result.scalars().all()
    logger.info(f"查询场次专家列表: session_id={session_id_for_logging}, 返回{len(session_experts)}条记录")
    return session_experts


async def get_expert_sessions(
    db: AsyncSession,
    expert_id: uuid.UUID,
    role: Optional[str] = None,
    skip: int = 0,
    limit: int = 10
) -> Tuple[List[LiveSessionExpert], int]:
    """
    获取专家参与的所有场次（分页，支持按角色筛选）
    
    Args:
        db: 数据库会话
        expert_id: 专家ID
        role: 专家角色筛选（可选）
        skip: 跳过的记录数
        limit: 返回记录数限制
    
    Returns:
        Tuple[List[LiveSessionExpert], int]: (场次专家关联记录列表, 总数)
    """
    expert_id_for_logging = str(expert_id)[:8]
    
    # 构建基础查询
    stmt = select(LiveSessionExpert).where(
        LiveSessionExpert.expert_id == expert_id
    )
    
    if role is not None:
        stmt = stmt.where(LiveSessionExpert.role == role)
    
    # 预加载场次信息
    #stmt = stmt.options(selectinload(LiveSessionExpert.session))
    # 预加载场次信息及关联的房间信息（避免懒加载错误）
    stmt = stmt.options(
        selectinload(LiveSessionExpert.session).selectinload("room")
    )
    # 执行COUNT查询获取总数
    count_stmt = select(func.count()).select_from(stmt.subquery())
    count_result = await db.execute(count_stmt)
    total = count_result.scalar_one()
    
    # 应用排序和分页
    stmt = stmt.order_by(
        LiveSessionExpert.sort_order.desc(),
        LiveSessionExpert.created_at.desc()
    ).offset(skip).limit(limit)
    
    # 执行查询获取数据列表
    result = await db.execute(stmt)
    session_experts = result.scalars().all()
    
    logger.info(f"查询专家场次列表: expert_id={expert_id_for_logging}, 返回{len(session_experts)}条记录，总数={total}")
    return (session_experts, total)


async def set_session_experts(
    db: AsyncSession,
    session_id: uuid.UUID,
    expert_data_list: List[Dict[str, Any]]
) -> List[LiveSessionExpert]:
    """
    为场次设置专家列表（先删除旧记录，再创建新记录）
    
    Args:
        db: 数据库会话
        session_id: 直播场次ID
        expert_data_list: 专家数据列表，格式: [{"expert_id": UUID, "role": str, "sort_order": int}, ...]
    
    Returns:
        List[LiveSessionExpert]: 创建的场次专家关联记录列表
    
    Raises:
        DatabaseIntegrityException: 如果场次专家关联已存在
    """
    # 提前提取用于日志的变量
    session_id_for_logging = str(session_id)[:8]
    
    try:
        # 删除旧记录
        delete_stmt = delete(LiveSessionExpert).where(
            LiveSessionExpert.session_id == session_id
        )
        await db.execute(delete_stmt)
        
        # 创建新记录
        new_session_experts = []
        for expert_data in expert_data_list:
            session_expert_id = uuid.uuid4()
            session_expert = LiveSessionExpert(
                id=session_expert_id,
                session_id=session_id,
                expert_id=expert_data["expert_id"],
                role=expert_data["role"],
                sort_order=expert_data.get("sort_order", 0)
            )
            db.add(session_expert)
            new_session_experts.append(session_expert)
        
        await db.flush()  # 触发唯一性检查
        
        # 刷新所有对象
        for session_expert in new_session_experts:
            await db.refresh(session_expert)
        
        logger.info(f"设置场次专家列表成功: session_id={session_id_for_logging}, 专家数量={len(new_session_experts)}")
        return new_session_experts
    except IntegrityError as e:
        await db.rollback()
        logger.error(f"设置场次专家列表失败（唯一性冲突）: session_id={session_id_for_logging}, error={str(e)}")
        raise DatabaseIntegrityException("场次专家关联已存在")
    except Exception as e:
        await db.rollback()
        logger.error(f"设置场次专家列表失败: session_id={session_id_for_logging}, error={str(e)}")
        raise


async def count_followers_by_expert(
    db: AsyncSession,
    expert_id: uuid.UUID
) -> int:
    """
    统计关注指定专家的用户数

    Args:
        db: 数据库会话
        expert_id: 专家ID

    Returns:
        int: 关注该专家的用户数量
    """
    stmt = select(func.count()).select_from(UserExpertSubscription).where(
        UserExpertSubscription.expert_id == expert_id
    )
    result = await db.execute(stmt)
    return result.scalar_one()

