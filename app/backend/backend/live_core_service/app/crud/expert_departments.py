"""
专家科室受控词表 CRUD 层

封装 ExpertDepartment 模型的所有数据库操作。
提供纯粹的数据访问接口，不包含业务逻辑验证。

所有函数遵循以下规范：
- 使用 async/await 异步编程
- UUID 在应用层生成
- 遵循安全异步异常处理原则（提前提取变量）
- 记录适当的日志
"""

# 标准库导入
import uuid
import logging
from typing import List, Optional, Tuple

# 第三方库导入
from sqlalchemy import select, delete, and_, or_, func, update as sa_update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import IntegrityError

# 项目内导入
from app.models.expert_departments import ExpertDepartment
from app.models.experts import Expert
from app.models.content_management import Category
from app.schemas.expert_departments import ExpertDepartmentCreate, ExpertDepartmentUpdate
from app.exceptions import DatabaseIntegrityException, DatabaseOperationException

logger = logging.getLogger(__name__)


# ==================== ExpertDepartment CRUD 函数 ====================

async def get_departments_paginated(
    db: AsyncSession,
    page: int = 1,
    size: int = 50,
    is_active: Optional[bool] = None,
    is_verified: Optional[bool] = None,
    category_id: Optional[uuid.UUID] = None,
    q: Optional[str] = None,
) -> Tuple[List[ExpertDepartment], int]:
    """
    获取科室列表（管理员接口，分页，支持筛选）。

    Args:
        db: 数据库会话
        page: 页码
        size: 每页数量（最大 200）
        is_active: 启用状态筛选（可选）
        is_verified: 审核状态筛选（可选）
        category_id: 分类筛选（可选）
        q: 搜索关键词（name ILIKE %q%，可选）

    Returns:
        (科室列表, 总条数)
    """
    if page < 1:
        page = 1
    if size < 1:
        size = 50
    elif size > 200:
        size = 200

    query = select(ExpertDepartment).options(joinedload(ExpertDepartment.category)).order_by(ExpertDepartment.created_at.desc())
    conditions = []

    if is_active is not None:
        conditions.append(ExpertDepartment.is_active == is_active)
    if is_verified is not None:
        conditions.append(ExpertDepartment.is_verified == is_verified)
    if category_id:
        conditions.append(ExpertDepartment.category_id == category_id)
    if q and q.strip():
        conditions.append(ExpertDepartment.name.ilike(f"%{q.strip()}%"))

    if conditions:
        query = query.where(and_(*conditions))

    # count（独立查询，不含 joinedload，避免 LEFT JOIN 参与 count）
    count_query = select(func.count(ExpertDepartment.id))
    if conditions:
        count_query = count_query.where(and_(*conditions))
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    # pagination
    offset = (page - 1) * size
    query = query.offset(offset).limit(size)
    result = await db.execute(query)
    departments = list(result.scalars().all())

    # 批量获取 expert_count + category_name（单次查询避免 N+1）
    if departments:
        dept_ids = [d.id for d in departments]
        count_subq = (
            select(Expert.department_id, func.count(Expert.id).label("cnt"))
            .where(Expert.department_id.in_(dept_ids))
            .group_by(Expert.department_id)
        )
        count_res = await db.execute(count_subq)
        count_map = {row[0]: row[1] for row in count_res.fetchall()}
        logger.debug("expert_count 批量查询: dept_ids=%d, matched=%d", len(dept_ids), len(count_map))
        for d in departments:
            d.expert_count = count_map.get(d.id, 0)

        # 批量填充 category_name（从 joinedload 预加载的 relationship 读取，零额外查询）
        for d in departments:
            d.category_name = d.category.name if d.category is not None else None

    logger.info(f"查询科室列表: page={page}, size={size}, total={total}")
    return (departments, total)


async def get_department_by_id(
    db: AsyncSession,
    department_id: uuid.UUID,
) -> Optional[ExpertDepartment]:
    """根据 ID 获取单个科室"""
    dept_id_log = str(department_id)[:8]
    try:
        stmt = select(ExpertDepartment).where(ExpertDepartment.id == department_id)
        result = await db.execute(stmt)
        dept = result.scalar_one_or_none()
        if dept:
            logger.debug(f"查询科室成功: id={dept_id_log}, name={dept.name}")
        return dept
    except Exception as e:
        logger.error(f"查询科室失败: id={dept_id_log}, error={str(e)}")
        raise


async def get_department_by_name(
    db: AsyncSession,
    name: str,
) -> Optional[ExpertDepartment]:
    """根据名称获取科室（区分大小写取决于数据库 collation）"""
    try:
        stmt = select(ExpertDepartment).where(
            ExpertDepartment.name == name.strip(),
            ExpertDepartment.is_active == True,
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    except Exception as e:
        logger.error(f"按名称查询科室失败: name={name}, error={str(e)}")
        raise


async def create_department(
    db: AsyncSession,
    department_data: ExpertDepartmentCreate,
    created_by: Optional[uuid.UUID] = None,
) -> ExpertDepartment:
    """
    创建科室（管理员）。

    Raises:
        DatabaseIntegrityException: 科室名重复
    """
    dept_id = uuid.uuid4()
    dept_id_log = str(dept_id)[:8]

    dump_data = department_data.model_dump()
    if "is_active" not in dump_data:
        dump_data["is_active"] = True
    if "is_verified" not in dump_data:
        dump_data["is_verified"] = False

    department = ExpertDepartment(id=dept_id, **dump_data)
    if created_by is not None:
        department.created_by = created_by

    try:
        db.add(department)
        await db.flush()
        await db.refresh(department)
        logger.info(f"创建科室成功: id={dept_id_log}, name={department.name}")
        return department
    except IntegrityError as e:
        await db.rollback()
        logger.error(f"创建科室失败（名称重复）: name={department_data.name}")
        raise DatabaseIntegrityException(f"科室名称已存在: {department_data.name}")
    except Exception as e:
        await db.rollback()
        logger.error(f"创建科室失败: id={dept_id_log}, error={str(e)}")
        raise


async def update_department(
    db: AsyncSession,
    department_id: uuid.UUID,
    department_data: ExpertDepartmentUpdate,
) -> Optional[ExpertDepartment]:
    """
    更新科室（管理员，部分更新）。

    Args:
        db: 数据库会话
        department_id: 科室 ID
        department_data: 更新数据（全部字段 Optional）

    Returns:
        更新后的科室对象，如果不存在则返回 None（由 Service 层处理 404）
    """
    dept_id_log = str(department_id)[:8]

    # 查询已有科室
    stmt = select(ExpertDepartment).where(ExpertDepartment.id == department_id)
    result = await db.execute(stmt)
    dept = result.scalar_one_or_none()
    if not dept:
        return None  # 返回 None，由 Service 层处理 404

    # 部分更新（只更新非 None 字段）
    update_dict = department_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(dept, key, value)

    try:
        await db.flush()
        await db.refresh(dept)
        logger.info(f"更新科室成功: id={dept_id_log}")
        return dept
    except IntegrityError as e:
        await db.rollback()
        logger.error(f"更新科室失败（名称冲突）: id={dept_id_log}")
        raise DatabaseIntegrityException("科室名称已存在")
    except Exception as e:
        await db.rollback()
        logger.error(f"更新科室失败: id={dept_id_log}, error={str(e)}")
        raise


async def soft_delete_department(
    db: AsyncSession,
    department_id: uuid.UUID,
) -> bool:
    """
    软删除科室（is_active = False）。

    Returns:
        True 表示成功，False 表示科室不存在（由 Service 层处理 404）
    """
    dept_id_log = str(department_id)[:8]

    stmt = select(ExpertDepartment).where(ExpertDepartment.id == department_id)
    result = await db.execute(stmt)
    dept = result.scalar_one_or_none()
    if not dept:
        return False  # 返回 False，由 Service 层处理 404

    dept.is_active = False

    try:
        await db.flush()
        await db.refresh(dept)
        logger.info(f"软删除科室成功: id={dept_id_log}, name={dept.name}")
        return True
    except Exception as e:
        await db.rollback()
        logger.error(f"软删除科室失败: id={dept_id_log}, error={str(e)}")
        raise


async def get_unmapped_experts(
    db: AsyncSession,
    page: int = 1,
    size: int = 50,
) -> Tuple[List[Expert], int]:
    """
    查询 department_id IS NULL 的专家（未映射科室）。

    用于管理员"未映射专家看板"。
    按 created_at DESC 排序。
    """
    if page < 1:
        page = 1
    if size < 1:
        size = 50
    elif size > 200:
        size = 200

    query = (
        select(Expert)
        .options(joinedload(Expert.category))
        .where(Expert.department_id == None)
    )
    query = query.order_by(Expert.created_at.desc())

    # count（独立查询，不含 joinedload，避免 LEFT JOIN 参与 count）
    count_query = select(func.count(Expert.id)).where(Expert.department_id == None)
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    # pagination
    offset = (page - 1) * size
    query = query.offset(offset).limit(size)
    result = await db.execute(query)
    experts = result.scalars().all()

    logger.info(f"查询未映射专家: page={page}, size={size}, total={total}")
    return (list(experts), total)


async def transfer_experts_to_department(
    db: AsyncSession,
    source_id: uuid.UUID,
    target_id: uuid.UUID,
) -> int:
    """批量将源科室的专家转移到目标科室。

    Returns:
        受影响的行数
    """
    dept_id_log = str(source_id)[:8]
    stmt = (
        sa_update(Expert)
        .where(Expert.department_id == source_id)
        .values(department_id=target_id)
    )
    result = await db.execute(stmt)
    affected = result.rowcount
    logger.info(f"转移专家科室: source_id={dept_id_log}, target_id={str(target_id)[:8]}, count={affected}")
    return affected


async def hard_delete_department(
    db: AsyncSession,
    department_id: uuid.UUID,
) -> bool:
    """物理删除科室（仅用于 merge 操作后清理源科室）。"""
    dept_id_log = str(department_id)[:8]
    stmt = delete(ExpertDepartment).where(ExpertDepartment.id == department_id)
    result = await db.execute(stmt)
    if result.rowcount == 0:
        logger.warning(f"物理删除科室失败（不存在）: id={dept_id_log}")
        return False
    logger.info(f"物理删除科室成功: id={dept_id_log}")
    return True


async def update_experts_category_by_department(
    db: AsyncSession,
    department_id: uuid.UUID,
    new_category_id: uuid.UUID,
) -> int:
    """批量更新指定科室下所有专家的 category_id。"""
    dept_id_log = str(department_id)[:8]
    stmt = (
        sa_update(Expert)
        .where(Expert.department_id == department_id)
        .values(category_id=new_category_id)
    )
    result = await db.execute(stmt)
    affected = result.rowcount
    logger.info(f"同步科室专家分类: dept_id={dept_id_log}, category_id={str(new_category_id)[:8]}, count={affected}")
    return affected


async def batch_verify_departments(
    db: AsyncSession,
    department_ids: List[uuid.UUID],
    verified: bool = True,
) -> int:
    """
    批量设置科室审核状态。
    用于管理端批量审核（通过/驳回）自动创建的科室。
    """
    stmt = (
        sa_update(ExpertDepartment)
        .where(ExpertDepartment.id.in_(department_ids))
        .values(is_verified=verified)
    )
    result = await db.execute(stmt)
    affected = result.rowcount
    logger.info(f"批量设置科室审核状态: verified={verified}, ids_count={len(department_ids)}, affected={affected}")
    return affected
