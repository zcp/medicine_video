"""
用户数据访问层 - User模型的CRUD操作
封装所有与User模型相关的数据库操作
"""
import logging
import uuid
from typing import Optional, Union, Dict, Any, List, TYPE_CHECKING

if TYPE_CHECKING:
    from ..schemas.users import UserFilterParams
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func, or_

from ..models.users import User, EntityStatus
from ..schemas.users import UserCreate, UserUpdate
from ..core.phone import validate_cn_phone

logger = logging.getLogger(__name__)


def _phone_fallback_candidates(phone: str) -> List[str]:
    """生成手机号兜底查询候选集（兼容历史 +86/86 前缀脏格式数据）

    参数归一化后的纯 11 位值，加上常见历史脏格式（86/＋86 前缀），
    排除与入参相同的值；非法手机号入参返回空列表（不触发兜底查询）。

    Args:
        phone: 原始查询手机号

    Returns:
        候选手机号列表（空表示无需兜底查询）
    """
    try:
        normalized = validate_cn_phone(phone)
    except ValueError:
        return []
    candidates = {normalized, f"86{normalized}", f"+86{normalized}"}
    candidates.discard(phone)
    return sorted(candidates)


async def get_by_username(db: AsyncSession, username: str) -> Optional[User]:
    """
    根据用户名获取用户记录
    
    Args:
        db: 数据库会话
        username: 用户名
        
    Returns:
        用户对象或None
    """
    try:
        logger.info(f"开始查询用户: username={username}")
        
        # 查询用户名字段或者邮箱字段匹配的用户（支持邮箱作为用户名登录）
        stmt = select(User).where(
            (User.username == username) | (User.email == username)
        )
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if user:
            logger.info(f"成功找到用户: id={user.id}, username={user.username}")
        else:
            logger.info(f"未找到用户: username={username}")
        
        return user
        
    except Exception as e:
        logger.error(f"查询用户时发生错误: username={username}, error={e}")
        raise


async def get_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """
    根据邮箱获取用户记录
    
    Args:
        db: 数据库会话
        email: 邮箱地址
        
    Returns:
        用户对象或None
    """
    try:
        logger.info(f"开始查询用户: email={email}")
        
        stmt = select(User).where(User.email == email)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if user:
            logger.info(f"成功找到用户: id={user.id}, email={user.email}")
        else:
            logger.info(f"未找到用户: email={email}")
        
        return user
        
    except Exception as e:
        logger.error(f"查询用户时发生错误: email={email}, error={e}")
        raise


async def get_by_phone_number(db: AsyncSession, *, phone_number: str) -> Optional[User]:
    """根据手机号获取用户（精确匹配失败时按常见脏格式候选集兜底查询，兼容历史 +86/86 前缀数据）"""
    try:
        logger.info(f"开始查询用户: phone_number={phone_number}")
        stmt = select(User).where(User.phone_number == phone_number)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            candidates = _phone_fallback_candidates(phone_number)
            if candidates:
                logger.info(f"精确匹配未命中，脏格式候选集兜底查询: {candidates}")
                stmt2 = select(User).where(User.phone_number.in_(candidates))
                result = await db.execute(stmt2)
                user = result.scalar_one_or_none()

        if user:
            logger.info(f"找到用户: phone_number={phone_number}, user_id={user.id}")
        else:
            logger.info(f"未找到用户: phone_number={phone_number}")

        return user
    except Exception as e:
        logger.error(f"查询用户时发生错误: phone_number={phone_number}, error={e}")
        raise


async def create(db: AsyncSession, user_in: UserCreate, password_hash: str) -> User:
    """
    创建新用户记录
    
    Args:
        db: 数据库会话
        user_in: 用户创建数据
        password_hash: 已计算的密码哈希值
        
    Returns:
        新创建的用户对象
    """
    try:
        logger.info(f"开始创建用户: username={user_in.username}, email={user_in.email}")
        
        # 从用户输入数据创建User实例
        db_user = User(
            username=user_in.username,
            email=user_in.email,
            phone_number=user_in.phone_number,
            password_hash=password_hash,  # 使用传入的密码哈希
            nickname=user_in.nickname,
            avatar_url=user_in.avatar_url,
            bio=user_in.bio,
            role=user_in.role,  # 使用默认值从schema
            status=user_in.status,  # 使用默认值从schema
            social_provider=user_in.social_provider,
            social_id=user_in.social_id,
            is_email_verified=False,  # 第一阶段默认为False
            is_phone_verified=False   # 第一阶段默认为False
        )
        
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        
        logger.info(f"成功创建用户: id={db_user.id}, public_id={db_user.public_id}")
        return db_user
        
    except IntegrityError as e:
        await db.rollback()
        logger.warning(f"创建用户时违反唯一性约束: username={user_in.username}, email={user_in.email}, error={e}")
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"创建用户时发生错误: username={user_in.username}, error={e}")
        raise


# ============================================================================
# 批次二新增函数
# ============================================================================

async def get(db: AsyncSession, id: int) -> Optional[User]:
    """
    根据内部主键ID获取用户记录
    
    Args:
        db: 数据库会话
        id: 用户内部ID
        
    Returns:
        用户对象或None
    """
    try:
        logger.info(f"开始查询用户: id={id}")
        
        stmt = select(User).where(User.id == id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if user:
            logger.info(f"成功找到用户: id={user.id}, username={user.username}")
        else:
            logger.info(f"未找到用户: id={id}")
        
        return user
        
    except Exception as e:
        logger.error(f"查询用户时发生错误: id={id}, error={e}")
        raise


async def get_by_uuid(db: AsyncSession, public_id: uuid.UUID) -> Optional[User]:
    """
    根据公开UUID获取用户记录
    
    Args:
        db: 数据库会话
        public_id: 用户公开UUID
        
    Returns:
        用户对象或None
    """
    try:
        logger.info(f"开始查询用户: public_id={public_id}")
        
        stmt = select(User).where(User.public_id == public_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if user:
            logger.info(f"成功找到用户: id={user.id}, public_id={user.public_id}")
        else:
            logger.info(f"未找到用户: public_id={public_id}")
        
        return user
        
    except Exception as e:
        logger.error(f"查询用户时发生错误: public_id={public_id}, error={e}")
        raise


async def get_by_uuids(db: AsyncSession, public_ids: List[uuid.UUID]) -> List[User]:
    """根据公开UUID列表批量获取用户记录。"""
    if not public_ids:
        return []

    try:
        unique_ids = list(dict.fromkeys(public_ids))
        logger.info(f"开始批量查询用户: count={len(unique_ids)}")

        stmt = select(User).where(User.public_id.in_(unique_ids))
        result = await db.execute(stmt)
        users = list(result.scalars().all())

        logger.info(f"批量查询用户完成: requested={len(unique_ids)}, found={len(users)}")
        return users

    except Exception as e:
        logger.error(f"批量查询用户时发生错误: count={len(public_ids)}, error={e}")
        raise


async def update(db: AsyncSession, db_obj: User, obj_in: Union[UserUpdate, Dict[str, Any]]) -> User:
    """
    更新用户记录
    
    Args:
        db: 数据库会话
        db_obj: 要更新的用户对象
        obj_in: 更新数据（Pydantic模型或字典）
        
    Returns:
        更新后的用户对象
    """
    try:
        logger.info(f"开始更新用户: id={db_obj.id}, username={db_obj.username}")
        
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
        
        logger.info(f"成功更新用户: id={db_obj.id}, username={db_obj.username}")
        return db_obj
        
    except IntegrityError as e:
        await db.rollback()
        logger.warning(f"更新用户时违反唯一性约束: id={db_obj.id}, error={e}")
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"更新用户时发生错误: id={db_obj.id}, error={e}")
        raise


async def remove(db: AsyncSession, id: int) -> User:
    """
    软删除用户记录（将status设置为DELETED）
    
    Args:
        db: 数据库会话
        id: 用户内部ID
        
    Returns:
        删除后的用户对象
    """
    try:
        logger.info(f"开始软删除用户: id={id}")
        
        # 首先获取用户对象
        user = await get(db, id)
        if not user:
            logger.warning(f"要删除的用户不存在: id={id}")
            raise ValueError(f"用户不存在: id={id}")
        
        # 检查用户当前状态
        if user.status == EntityStatus.DELETED:
            logger.warning(f"用户已被删除: id={id}")
            return user
        
        # 执行软删除
        user.status = EntityStatus.DELETED
        await db.commit()
        await db.refresh(user)
        
        logger.info(f"成功软删除用户: id={user.id}, username={user.username}")
        return user
        
    except Exception as e:
        await db.rollback()
        logger.error(f"软删除用户时发生错误: id={id}, error={e}")
        raise 


# ============================================================================
# 批次五新增函数 - 后台管理API
# ============================================================================

async def get_multi(db: AsyncSession, *, skip: int = 0, limit: int = 100) -> List[User]:
    """
    获取用户列表（支持分页）
    
    Args:
        db: 数据库会话
        skip: 跳过的记录数，用于分页
        limit: 返回的最大记录数，用于分页
        
    Returns:
        用户列表
    """
    try:
        logger.info(f"开始查询用户列表: skip={skip}, limit={limit}")
        
        stmt = (
            select(User)
            .order_by(User.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(stmt)
        users = result.scalars().all()
        
        logger.info(f"成功查询到 {len(users)} 个用户")
        return list(users)
        
    except Exception as e:
        logger.error(f"查询用户列表时发生错误: error={e}")
        raise


async def count(db: AsyncSession) -> int:
    """
    获取用户总数
    
    Args:
        db: 数据库会话
        
    Returns:
        用户总数
    """
    try:
        logger.info("开始统计用户总数")
        
        stmt = select(func.count(User.id))
        result = await db.execute(stmt)
        total = result.scalar()
        
        logger.info(f"用户总数: {total}")
        return total
        
    except Exception as e:
        logger.error(f"统计用户总数时发生错误: error={e}")
        raise


async def get_multi_with_filtering(
    db: AsyncSession, 
    *, 
    skip: int = 0, 
    limit: int = 100, 
    filters: "UserFilterParams"
) -> List[User]:
    """
    获取带筛选条件的用户列表
    
    Args:
        db: 数据库会话
        skip: 跳过的记录数，用于分页
        limit: 返回的最大记录数，用于分页
        filters: 筛选条件
        
    Returns:
        筛选后的用户列表
    """
    try:
        logger.info(f"开始查询筛选用户列表: skip={skip}, limit={limit}")
        
        # 构建基础查询
        query = select(User)
        
        # 动态添加筛选条件
        if filters.keyword:
            kw = f"%{filters.keyword}%"
            query = query.where(
                or_(
                    User.username.ilike(kw),
                    User.email.ilike(kw),
                    User.nickname.ilike(kw),
                    User.phone_number.ilike(kw),
                )
            )
            logger.debug(f"添加统一关键词筛选: {filters.keyword}")

        if filters.username:
            query = query.where(User.username.ilike(f"%{filters.username}%"))
            logger.debug(f"添加用户名筛选: {filters.username}")
            
        if filters.email:
            query = query.where(User.email == filters.email)
            logger.debug(f"添加邮箱筛选: {filters.email}")

        if filters.phone_number:
            query = query.where(User.phone_number == filters.phone_number)
            logger.debug(f"添加手机号筛选: {filters.phone_number}")

        if filters.nickname:
            query = query.where(User.nickname.ilike(f"%{filters.nickname}%"))
            logger.debug(f"添加昵称筛选: {filters.nickname}")
            
        if filters.role:
            query = query.where(User.role == filters.role)
            logger.debug(f"添加角色筛选: {filters.role}")
            
        if filters.status:
            query = query.where(User.status == filters.status)
            logger.debug(f"添加状态筛选: {filters.status}")

        if filters.can_stream is not None:
            query = query.where(User.can_stream == filters.can_stream)
            logger.debug(f"添加开播资格筛选: {filters.can_stream}")
            
        if filters.is_email_verified is not None:
            query = query.where(User.is_email_verified == filters.is_email_verified)
            logger.debug(f"添加邮箱验证状态筛选: {filters.is_email_verified}")
            
        if filters.is_phone_verified is not None:
            query = query.where(User.is_phone_verified == filters.is_phone_verified)
            logger.debug(f"添加手机验证状态筛选: {filters.is_phone_verified}")
        
        # 添加排序和分页
        query = query.order_by(User.created_at.desc()).offset(skip).limit(limit)
        
        # 执行查询
        result = await db.execute(query)
        users = result.scalars().all()
        
        logger.info(f"成功查询到 {len(users)} 个筛选用户")
        return list(users)
        
    except Exception as e:
        logger.error(f"查询筛选用户列表时发生错误: error={e}")
        raise


async def count_with_filtering(db: AsyncSession, *, filters: "UserFilterParams") -> int:
    """
    获取筛选后的用户总数
    
    Args:
        db: 数据库会话
        filters: 筛选条件
        
    Returns:
        筛选后的用户总数
    """
    try:
        logger.info("开始统计筛选用户总数")
        
        # 构建基础查询
        query = select(func.count(User.id))
        
        # 动态添加筛选条件（与get_multi_with_filtering保持一致）
        if filters.keyword:
            kw = f"%{filters.keyword}%"
            query = query.where(
                or_(
                    User.username.ilike(kw),
                    User.email.ilike(kw),
                    User.nickname.ilike(kw),
                    User.phone_number.ilike(kw),
                )
            )

        if filters.username:
            query = query.where(User.username.ilike(f"%{filters.username}%"))
            
        if filters.email:
            query = query.where(User.email == filters.email)

        if filters.phone_number:
            query = query.where(User.phone_number == filters.phone_number)

        if filters.nickname:
            query = query.where(User.nickname.ilike(f"%{filters.nickname}%"))
            
        if filters.role:
            query = query.where(User.role == filters.role)
            
        if filters.status:
            query = query.where(User.status == filters.status)

        if filters.can_stream is not None:
            query = query.where(User.can_stream == filters.can_stream)
            
        if filters.is_email_verified is not None:
            query = query.where(User.is_email_verified == filters.is_email_verified)
            
        if filters.is_phone_verified is not None:
            query = query.where(User.is_phone_verified == filters.is_phone_verified)
        
        # 执行查询
        result = await db.execute(query)
        total = result.scalar()
        
        logger.info(f"筛选用户总数: {total}")
        return total
        
    except Exception as e:
        logger.error(f"统计筛选用户总数时发生错误: error={e}")
        raise


async def get_by_social_id(db: AsyncSession, *, provider: str, social_id: str) -> Optional[User]:
    """
    根据社交登录信息获取用户记录
    
    Args:
        db: 数据库会话
        provider: 社交登录提供商
        social_id: 社交登录ID
        
    Returns:
        用户对象或None
    """
    try:
        logger.info(f"开始查询用户: provider={provider}, social_id={social_id}")
        
        stmt = select(User).where(
            (User.social_provider == provider) & (User.social_id == social_id)
        )
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if user:
            logger.info(f"成功找到用户: id={user.id}, provider={provider}")
        else:
            logger.info(f"未找到用户: provider={provider}, social_id={social_id}")
        
        return user
        
    except Exception as e:
        logger.error(f"查询用户时发生错误: provider={provider}, social_id={social_id}, error={e}")
        raise


async def get_by_login_identifier(db: AsyncSession, *, identifier: str) -> Optional[User]:
    """
    根据登录标识符获取用户记录（支持用户名、邮箱、已验证手机号）
    
    Args:
        db: 数据库会话
        identifier: 登录标识符（用户名、邮箱或已验证手机号）
        
    Returns:
        用户对象或None
    """
    try:
        logger.info(f"开始查询用户: identifier={identifier}")
        
        stmt = select(User).where(
            or_(
                User.username == identifier,
                User.email == identifier,
                (User.phone_number == identifier) & (User.is_phone_verified == True)
            )
        )
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            candidates = _phone_fallback_candidates(identifier)
            if candidates:
                logger.info(f"精确匹配未命中，脏格式候选集兜底查询: {candidates}")
                stmt2 = select(User).where(
                    (User.phone_number.in_(candidates)) & (User.is_phone_verified == True)
                )
                result = await db.execute(stmt2)
                user = result.scalar_one_or_none()

        if user:
            logger.info(f"成功找到用户: id={user.id}, username={user.username}")
        else:
            logger.info(f"未找到用户: identifier={identifier}")
        
        return user
        
    except Exception as e:
        logger.error(f"查询用户时发生错误: identifier={identifier}, error={e}")
        raise 