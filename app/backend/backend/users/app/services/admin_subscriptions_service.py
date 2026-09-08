"""
管理员订阅服务层 - AdminSubscriptionsService
封装所有管理员订阅相关的业务逻辑，包括用户订阅查询、手动创建、更新等管理功能
"""
import logging
import uuid
from typing import Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.crud import crud_user, crud_user_membership, crud_membership_product
from app.schemas.users import (
    UserMembershipResponse, UserMembershipCreate, UserMembershipUpdate,
    UserMembershipCreateAdmin
)
from app.models.users import User, UserMembership, MembershipStatus

logger = logging.getLogger(__name__)


# ============================================================================
# 业务异常定义
# ============================================================================

class AdminSubscriptionsServiceException(Exception):
    """管理员订阅服务基础异常"""
    pass


class TargetUserNotFoundError(AdminSubscriptionsServiceException):
    """目标用户不存在异常"""
    def __init__(self, user_uuid: str, message: str = "目标用户不存在"):
        self.user_uuid = user_uuid
        super().__init__(f"{message}: {user_uuid}")


class ProductNotFoundError(AdminSubscriptionsServiceException):
    """产品不存在异常"""
    def __init__(self, product_code: str, message: str = "指定的产品编码不存在"):
        self.product_code = product_code
        super().__init__(f"{message}: {product_code}")


class ActiveSubscriptionExistsError(AdminSubscriptionsServiceException):
    """用户已有同类有效订阅异常"""
    def __init__(self, message: str = "用户已拥有一个正在生效的同类会员"):
        super().__init__(message)


class SubscriptionNotFoundError(AdminSubscriptionsServiceException):
    """订阅记录不存在异常"""
    def __init__(self, subscription_uuid: str, message: str = "订阅记录不存在"):
        self.subscription_uuid = subscription_uuid
        super().__init__(f"{message}: {subscription_uuid}")


# ============================================================================
# 管理员订阅服务类
# ============================================================================

class AdminSubscriptionsService:
    """管理员订阅服务类"""
    
    def __init__(self, db: AsyncSession):
        """
        初始化管理员订阅服务
        
        Args:
            db: 数据库会话
        """
        self.db = db
    
    async def get_subscriptions_by_user(self, user_uuid: uuid.UUID, page: int, size: int) -> Dict[str, Any]:
        """
        获取指定用户的所有订阅历史记录（分页）
        
        Args:
            user_uuid: 用户UUID
            page: 页码
            size: 每页数量
            
        Returns:
            包含分页信息的订阅列表字典
            
        Raises:
            TargetUserNotFoundError: 目标用户不存在
        """
        # 🔴 主动变量提取（安全红线）
        user_uuid_for_logging = str(user_uuid)
        
        logger.info(f"开始获取用户订阅列表: user_uuid={user_uuid_for_logging}, page={page}, size={size}")
        
        try:
            # 1. 用户查询 - 根据user_uuid找到user_id
            target_user = await crud_user.get_by_uuid(self.db, public_id=user_uuid)
            if not target_user:
                logger.warning(f"目标用户不存在: user_uuid={user_uuid_for_logging}")
                raise TargetUserNotFoundError(user_uuid_for_logging)
            
            # 🔴 提取目标用户安全变量
            target_user_id_for_logging = target_user.id
            
            # 2. 计算分页参数
            skip = (page - 1) * size
            
            # 3. 数据查询 - 获取该用户的所有订阅记录
            memberships = await crud_user_membership.get_multi_by_user_id(
                self.db, user_id=target_user.id, skip=skip, limit=size
            )
            
            # 4. 序列化 - 将SQLAlchemy对象转换为Pydantic模型
            membership_responses = []
            for membership in memberships:
                try:
                    membership_response = UserMembershipResponse.model_validate(membership)
                    membership_responses.append(membership_response)
                except Exception as e:
                    membership_id = getattr(membership, 'id', 'unknown')
                    logger.warning(f"序列化用户订阅失败: membership_id={membership_id}, error={e}")
                    # 跳过失败的订阅，继续处理其他订阅
                    continue
            
            # 5. 构建分页响应数据
            paginated_result = {
                "total": len(membership_responses),  # 简化处理，实际应该查询总数
                "page": page,
                "size": size,
                "items": membership_responses
            }
            
            logger.info(f"成功获取用户订阅列表: user_uuid={user_uuid_for_logging}, target_user_id={target_user_id_for_logging}, count={len(membership_responses)}")
            return paginated_result
            
        except TargetUserNotFoundError:
            raise
        except Exception as e:
            logger.error(f"获取用户订阅列表失败: user_uuid={user_uuid_for_logging}, error={e}")
            raise
    
    async def create_subscription_for_user(self, user_uuid: uuid.UUID, sub_create_request: UserMembershipCreateAdmin) -> UserMembership:
        """
        手动为用户创建订阅
        
        Args:
            user_uuid: 用户UUID
            sub_create_request: 订阅创建请求
            
        Returns:
            新创建的订阅记录
            
        Raises:
            TargetUserNotFoundError: 目标用户不存在
            ProductNotFoundError: 产品不存在
            ActiveSubscriptionExistsError: 用户已有同类有效订阅
        """
        # 🔴 主动变量提取（安全红线）
        user_uuid_for_logging = str(user_uuid)
        product_code_for_logging = sub_create_request.product_code
        
        logger.info(f"开始为用户创建订阅: user_uuid={user_uuid_for_logging}, product_code={product_code_for_logging}")
        
        try:
            # 1. 用户查询 - 根据user_uuid找到user_id
            target_user = await crud_user.get_by_uuid(self.db, public_id=user_uuid)
            if not target_user:
                logger.warning(f"目标用户不存在: user_uuid={user_uuid_for_logging}")
                raise TargetUserNotFoundError(user_uuid_for_logging)
            
            # 🔴 提取目标用户安全变量
            target_user_id_for_logging = target_user.id
            
            # 2. 产品查询 - 根据product_code查询产品信息
            product = await crud_membership_product.get_by_code(self.db, code=sub_create_request.product_code)
            if not product:
                logger.warning(f"产品不存在: product_code={product_code_for_logging}")
                raise ProductNotFoundError(product_code_for_logging)
            
            # 3. 构造Schema - 创建用户订阅对象
            membership_create = UserMembershipCreate(
                user_id=target_user.id,
                product_code=sub_create_request.product_code,
                transaction_id=sub_create_request.transaction_id,
                level=product.level,
                status=MembershipStatus.ACTIVE,
                is_auto_renew=False,  # 手动创建的订阅默认不自动续费
                admin_notes=sub_create_request.admin_notes,
                start_date=sub_create_request.start_date,
                expires_at=sub_create_request.expires_at
            )
            
            # 4. 创建记录 - 调用CRUD层创建订阅记录
            try:
                new_membership = await crud_user_membership.create(self.db, obj_in=membership_create)
                logger.info(f"成功为用户创建订阅: user_uuid={user_uuid_for_logging}, target_user_id={target_user_id_for_logging}, membership_id={new_membership.id}")
                return new_membership
            except IntegrityError:
                # 5. 异常处理 - 捕获数据库完整性约束错误
                logger.warning(f"用户已有同类有效订阅: user_uuid={user_uuid_for_logging}, target_user_id={target_user_id_for_logging}, product_code={product_code_for_logging}")
                raise ActiveSubscriptionExistsError()
                
        except (TargetUserNotFoundError, ProductNotFoundError, ActiveSubscriptionExistsError):
            raise
        except Exception as e:
            logger.error(f"为用户创建订阅失败: user_uuid={user_uuid_for_logging}, product_code={product_code_for_logging}, error={e}")
            raise
    
    async def update_subscription(self, subscription_uuid: uuid.UUID, sub_update_request: UserMembershipUpdate) -> UserMembership:
        """
        手动更新指定订阅
        
        Args:
            subscription_uuid: 订阅UUID
            sub_update_request: 订阅更新请求
            
        Returns:
            更新后的订阅记录
            
        Raises:
            SubscriptionNotFoundError: 订阅记录不存在
        """
        # 🔴 主动变量提取（安全红线）
        subscription_uuid_for_logging = str(subscription_uuid)
        
        logger.info(f"开始更新订阅: subscription_uuid={subscription_uuid_for_logging}")
        
        try:
            # 1. 数据查询 - 根据subscription_uuid查询订阅记录
            subscription_to_update = await crud_user_membership.get_by_uuid(self.db, uuid=subscription_uuid)
            if not subscription_to_update:
                logger.warning(f"订阅记录不存在: subscription_uuid={subscription_uuid_for_logging}")
                raise SubscriptionNotFoundError(subscription_uuid_for_logging)
            
            # 🔴 提取订阅安全变量
            subscription_id_for_logging = subscription_to_update.id
            subscription_user_id_for_logging = subscription_to_update.user_id
            
            # 2. 数据更新 - 更新订阅记录
            updated_subscription = await crud_user_membership.update(
                self.db, db_obj=subscription_to_update, obj_in=sub_update_request
            )
            
            logger.info(f"成功更新订阅: subscription_uuid={subscription_uuid_for_logging}, subscription_id={subscription_id_for_logging}")
            return updated_subscription
            
        except SubscriptionNotFoundError:
            raise
        except Exception as e:
            logger.error(f"更新订阅失败: subscription_uuid={subscription_uuid_for_logging}, error={e}")
            raise 