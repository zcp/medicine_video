"""
会员产品数据访问层 - 用户功能服务
封装所有与 MembershipProduct 模型相关的数据库操作
"""
import logging
from typing import List, Optional
from sqlalchemy import select, asc, desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.models.users import MembershipProduct, MembershipProductStatus

logger = logging.getLogger(__name__)


async def get_multi_active(
    db: AsyncSession, 
    *, 
    sort: str = "sort_order", 
    direction: str = "asc"
) -> List[MembershipProduct]:
    """
    获取所有状态为 ACTIVE 的会员产品列表
    
    Args:
        db: 数据库会话
        sort: 排序字段，默认为 sort_order
        direction: 排序方向，asc 或 desc，默认为 asc
        
    Returns:
        会员产品列表
    """
    logger.info(f"开始查询活跃会员产品: sort={sort}, direction={direction}")
    
    try:
        # 构建基础查询
        query = select(MembershipProduct).where(
            MembershipProduct.status == MembershipProductStatus.ACTIVE
        )
        
        # 添加排序
        if hasattr(MembershipProduct, sort):
            sort_column = getattr(MembershipProduct, sort)
            if direction.lower() == "desc":
                query = query.order_by(desc(sort_column))
            else:
                query = query.order_by(asc(sort_column))
        else:
            # 如果排序字段不存在，使用默认排序
            logger.warning(f"排序字段 {sort} 不存在，使用默认排序 sort_order")
            query = query.order_by(asc(MembershipProduct.sort_order))
        
        # 执行查询
        result = await db.execute(query)
        products = result.scalars().all()
        
        logger.info(f"成功查询到 {len(products)} 个活跃会员产品")
        return list(products)
        
    except Exception as e:
        logger.error(f"查询活跃会员产品失败: error={e}")
        raise 


# ============================================================================
# 批次五新增函数 - 后台管理API
# ============================================================================

async def create(db: AsyncSession, *, obj_in: "MembershipProductCreate") -> MembershipProduct:
    """
    创建新的会员产品
    
    Args:
        db: 数据库会话
        obj_in: 会员产品创建数据
        
    Returns:
        新创建的会员产品对象
        
    Raises:
        IntegrityError: 当产品编码已存在时
    """
    try:
        logger.info(f"开始创建会员产品: code={obj_in.code}, name={obj_in.name}")
        
        # 创建MembershipProduct实例
        db_product = MembershipProduct(
            code=obj_in.code,
            name=obj_in.name,
            description=obj_in.description,
            sort_order=obj_in.sort_order,
            price=obj_in.price,
            level=obj_in.level,
            duration_unit=obj_in.duration_unit,
            duration_value=obj_in.duration_value,
            status=obj_in.status,
            payment_gateway_price_id=obj_in.payment_gateway_price_id
        )
        
        db.add(db_product)
        await db.commit()
        await db.refresh(db_product)
        
        logger.info(f"成功创建会员产品: code={db_product.code}, name={db_product.name}")
        return db_product
        
    except IntegrityError as e:
        await db.rollback()
        logger.warning(f"创建会员产品时违反唯一性约束: code={obj_in.code}, error={e}")
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"创建会员产品时发生错误: code={obj_in.code}, error={e}")
        raise


async def get_by_code(db: AsyncSession, *, code: str) -> Optional[MembershipProduct]:
    """
    根据产品编码获取会员产品
    
    Args:
        db: 数据库会话
        code: 产品编码
        
    Returns:
        会员产品对象或None
    """
    try:
        logger.info(f"开始查询会员产品: code={code}")
        
        stmt = select(MembershipProduct).where(MembershipProduct.code == code)
        result = await db.execute(stmt)
        product = result.scalar_one_or_none()
        
        if product:
            logger.info(f"成功找到会员产品: code={product.code}, name={product.name}")
        else:
            logger.info(f"未找到会员产品: code={code}")
        
        return product
        
    except Exception as e:
        logger.error(f"查询会员产品时发生错误: code={code}, error={e}")
        raise


async def get_multi_all(db: AsyncSession, *, skip: int = 0, limit: int = 100) -> List[MembershipProduct]:
    """
    获取所有会员产品列表（包括非活跃状态），用于后台管理
    
    Args:
        db: 数据库会话
        skip: 跳过的记录数，用于分页
        limit: 返回的最大记录数，用于分页
        
    Returns:
        会员产品列表
    """
    try:
        logger.info(f"开始查询所有会员产品: skip={skip}, limit={limit}")
        
        stmt = (
            select(MembershipProduct)
            .order_by(asc(MembershipProduct.sort_order), desc(MembershipProduct.created_at))
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(stmt)
        products = result.scalars().all()
        
        logger.info(f"成功查询到 {len(products)} 个会员产品")
        return list(products)
        
    except Exception as e:
        logger.error(f"查询所有会员产品时发生错误: error={e}")
        raise


async def count_all(db: AsyncSession) -> int:
    """
    获取所有会员产品总数（包括非活跃状态）
    
    Args:
        db: 数据库会话
        
    Returns:
        会员产品总数
    """
    try:
        logger.info("开始统计所有会员产品总数")
        
        stmt = select(func.count(MembershipProduct.code))
        result = await db.execute(stmt)
        total = result.scalar()
        
        logger.info(f"会员产品总数: {total}")
        return total
        
    except Exception as e:
        logger.error(f"统计会员产品总数时发生错误: error={e}")
        raise


async def update(db: AsyncSession, *, db_obj: MembershipProduct, obj_in: "MembershipProductUpdate") -> MembershipProduct:
    """
    更新会员产品信息
    
    Args:
        db: 数据库会话
        db_obj: 要更新的会员产品对象
        obj_in: 更新数据
        
    Returns:
        更新后的会员产品对象
    """
    try:
        logger.info(f"开始更新会员产品: code={db_obj.code}, name={db_obj.name}")
        
        # 转换为字典形式
        update_data = obj_in.model_dump(exclude_unset=True)
        
        # 遍历更新数据，更新对象属性
        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
                logger.debug(f"更新字段 {field}: {value}")
        
        await db.commit()
        await db.refresh(db_obj)
        
        logger.info(f"成功更新会员产品: code={db_obj.code}, name={db_obj.name}")
        return db_obj
        
    except IntegrityError as e:
        await db.rollback()
        logger.warning(f"更新会员产品时违反唯一性约束: code={db_obj.code}, error={e}")
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"更新会员产品时发生错误: code={db_obj.code}, error={e}")
        raise


async def remove(db: AsyncSession, *, code: str) -> Optional[MembershipProduct]:
    """
    删除会员产品（物理删除）
    
    Args:
        db: 数据库会话
        code: 产品编码
        
    Returns:
        被删除的会员产品对象，便于记录日志；如果不存在则返回None
        
    Raises:
        IntegrityError: 当产品仍被用户订阅引用时
    """
    try:
        logger.info(f"开始删除会员产品: code={code}")
        
        # 首先获取产品对象
        product = await get_by_code(db, code=code)
        if not product:
            logger.warning(f"要删除的会员产品不存在: code={code}")
            return None
        
        # 尝试删除
        await db.delete(product)
        await db.commit()
        
        logger.info(f"成功删除会员产品: code={code}, name={product.name}")
        return product
        
    except IntegrityError as e:
        await db.rollback()
        logger.warning(f"删除会员产品时违反引用完整性约束: code={code}, error={e}")
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"删除会员产品时发生错误: code={code}, error={e}")
        raise 