"""
用户会员订阅数据访问层 - 用户功能服务
封装所有与UserMembership模型相关的数据库操作
"""
import logging
import uuid
from typing import Optional, Union, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError

from ..models.users import UserMembership
from ..schemas.users import UserMembershipCreate, UserMembershipUpdate

logger = logging.getLogger(__name__)


async def create(db: AsyncSession, *, obj_in: UserMembershipCreate) -> UserMembership:
    """
    创建一个新的UserMembership记录
    
    Args:
        db: 数据库会话
        obj_in: 用户会员订阅创建数据
        
    Returns:
        新创建的用户会员订阅对象
        
    Raises:
        IntegrityError: 当违反唯一性约束时（如用户已有同产品的有效订阅）
    """
    try:
        logger.info(f"开始创建用户会员订阅: user_id={obj_in.user_id}, product_code={obj_in.product_code}")
        
        # 创建UserMembership实例
        db_membership = UserMembership(
            user_id=obj_in.user_id,
            product_code=obj_in.product_code,
            transaction_id=obj_in.transaction_id,
            level=obj_in.level,
            status=obj_in.status,
            is_auto_renew=obj_in.is_auto_renew,
            admin_notes=obj_in.admin_notes,
            start_date=obj_in.start_date,
            expires_at=obj_in.expires_at
        )
        
        db.add(db_membership)
        await db.commit()
        await db.refresh(db_membership)
        
        logger.info(f"成功创建用户会员订阅: id={db_membership.id}, public_id={db_membership.public_id}")
        return db_membership
        
    except IntegrityError as e:
        await db.rollback()
        logger.warning(f"创建用户会员订阅时违反唯一性约束: user_id={obj_in.user_id}, product_code={obj_in.product_code}, error={e}")
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"创建用户会员订阅时发生错误: user_id={obj_in.user_id}, product_code={obj_in.product_code}, error={e}")
        raise


async def get_by_uuid_and_user_id(db: AsyncSession, *, uuid: uuid.UUID, user_id: int) -> Optional[UserMembership]:
    """
    根据uuid获取属于特定user_id的单个订阅记录（用于权限校验）
    
    Args:
        db: 数据库会话
        uuid: 订阅记录的公开UUID
        user_id: 用户ID，用于权限验证
        
    Returns:
        用户会员订阅对象或None
    """
    try:
        logger.info(f"开始查询用户会员订阅: uuid={uuid}, user_id={user_id}")
        
        stmt = select(UserMembership).where(
            (UserMembership.public_id == uuid) & 
            (UserMembership.user_id == user_id)
        )
        result = await db.execute(stmt)
        membership = result.scalar_one_or_none()
        
        if membership:
            logger.info(f"成功找到用户会员订阅: id={membership.id}, public_id={membership.public_id}")
        else:
            logger.info(f"未找到用户会员订阅: uuid={uuid}, user_id={user_id}")
        
        return membership
        
    except Exception as e:
        logger.error(f"查询用户会员订阅时发生错误: uuid={uuid}, user_id={user_id}, error={e}")
        raise


async def get_multi_by_user_id(db: AsyncSession, *, user_id: int, skip: int = 0, limit: int = 100) -> List[UserMembership]:
    """
    获取特定user_id的所有订阅记录（支持分页）
    
    Args:
        db: 数据库会话
        user_id: 用户ID
        skip: 跳过的记录数，用于分页
        limit: 返回的最大记录数，用于分页
        
    Returns:
        用户会员订阅列表
    """
    try:
        logger.info(f"开始查询用户会员订阅列表: user_id={user_id}, skip={skip}, limit={limit}")
        
        stmt = (
            select(UserMembership)
            .where(UserMembership.user_id == user_id)
            .order_by(UserMembership.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(stmt)
        memberships = result.scalars().all()
        
        logger.info(f"成功查询到 {len(memberships)} 个用户会员订阅: user_id={user_id}")
        return list(memberships)
        
    except Exception as e:
        logger.error(f"查询用户会员订阅列表时发生错误: user_id={user_id}, error={e}")
        raise


async def update(db: AsyncSession, *, db_obj: UserMembership, obj_in: Union[UserMembershipUpdate, Dict[str, Any]]) -> UserMembership:
    """
    更新一个UserMembership记录
    
    Args:
        db: 数据库会话
        db_obj: 要更新的用户会员订阅对象
        obj_in: 更新数据（Pydantic模型或字典）
        
    Returns:
        更新后的用户会员订阅对象
    """
    try:
        logger.info(f"开始更新用户会员订阅: id={db_obj.id}, public_id={db_obj.public_id}")
        
        # 转换为字典形式
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)
        
        # 遍历更新数据，更新对象属性
        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
                logger.debug(f"更新字段 {field}: {value}")
        
        await db.commit()
        await db.refresh(db_obj)
        
        logger.info(f"成功更新用户会员订阅: id={db_obj.id}, public_id={db_obj.public_id}")
        return db_obj
        
    except IntegrityError as e:
        await db.rollback()
        logger.warning(f"更新用户会员订阅时违反唯一性约束: id={db_obj.id}, error={e}")
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"更新用户会员订阅时发生错误: id={db_obj.id}, error={e}")
        raise 


# ============================================================================
# 批次五新增函数 - 后台管理API
# ============================================================================

async def get_by_uuid(db: AsyncSession, *, uuid: uuid.UUID) -> Optional[UserMembership]:
    """
    （管理员权限）根据uuid获取任意用户的订阅记录
    
    Args:
        db: 数据库会话
        uuid: 订阅记录的公开UUID
        
    Returns:
        用户会员订阅对象或None
    """
    try:
        logger.info(f"开始查询用户会员订阅(管理员): uuid={uuid}")
        
        stmt = select(UserMembership).where(UserMembership.public_id == uuid)
        result = await db.execute(stmt)
        membership = result.scalar_one_or_none()
        
        if membership:
            logger.info(f"成功找到用户会员订阅: id={membership.id}, public_id={membership.public_id}, user_id={membership.user_id}")
        else:
            logger.info(f"未找到用户会员订阅: uuid={uuid}")
        
        return membership
        
    except Exception as e:
        logger.error(f"查询用户会员订阅时发生错误(管理员): uuid={uuid}, error={e}")
        raise 