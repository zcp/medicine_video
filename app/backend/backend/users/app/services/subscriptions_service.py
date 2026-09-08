"""
订阅服务层 - SubscriptionsService
封装所有订阅相关的业务逻辑，包括用户订阅列表查询、新订阅创建、订阅更新等
"""
import logging
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.crud import crud_user_membership, crud_membership_product
from app.schemas.users import (
    UserMembershipResponse, UserMembershipCreate, UserMembershipUpdate,
    SubscriptionCreateRequest, SubscriptionUpdateRequest
)
from app.models.users import User, UserMembership, MembershipStatus, MembershipProductStatus

logger = logging.getLogger(__name__)


# ============================================================================
# 业务异常定义
# ============================================================================

class SubscriptionsServiceException(Exception):
    """订阅服务基础异常"""
    pass


class ProductNotFoundError(SubscriptionsServiceException):
    """产品不存在或不可购买异常"""
    def __init__(self, product_code: str, message: str = "产品不存在或不可购买"):
        self.product_code = product_code
        super().__init__(f"{message}: {product_code}")


class PaymentFailedError(SubscriptionsServiceException):
    """支付失败异常"""
    def __init__(self, payment_error: str, message: str = "支付处理失败"):
        self.payment_error = payment_error
        super().__init__(f"{message}: {payment_error}")


class ActiveSubscriptionExistsError(SubscriptionsServiceException):
    """用户已有同类有效订阅异常"""
    def __init__(self, message: str = "您已拥有一个正在生效的同类会员"):
        super().__init__(message)


class SubscriptionOwnershipError(SubscriptionsServiceException):
    """订阅记录不存在或无权修改异常"""
    def __init__(self, subscription_uuid: str, message: str = "订阅记录不存在或无权修改"):
        self.subscription_uuid = subscription_uuid
        super().__init__(f"{message}: {subscription_uuid}")


class SubscriptionUpdateForbiddenError(SubscriptionsServiceException):
    """订阅状态不允许修改异常"""
    def __init__(self, status: str, message: str = "已过期的订阅无法修改"):
        self.status = status
        super().__init__(f"{message}: 当前状态为 {status}")


# ============================================================================
# 订阅服务类
# ============================================================================

class SubscriptionsService:
    """订阅服务类"""
    
    def __init__(self, db: AsyncSession):
        """
        初始化订阅服务
        
        Args:
            db: 数据库会话
        """
        self.db = db
    
    async def get_user_subscriptions(self, user_id: int, page: int, size: int) -> Dict[str, Any]:
        """
        获取用户的订阅列表（分页）
        
        Args:
            user_id: 用户ID
            page: 页码
            size: 每页数量
            
        Returns:
            包含分页信息的订阅列表字典
        """
        logger.info(f"开始获取用户订阅列表: user_id={user_id}, page={page}, size={size}")
        
        try:
            # 1. 计算分页参数
            skip = (page - 1) * size
            
            # 2. 数据查询 - 获取用户的订阅列表
            memberships = await crud_user_membership.get_multi_by_user_id(
                self.db, user_id=user_id, skip=skip, limit=size
            )
            
            # 3. 序列化 - 将SQLAlchemy对象转换为Pydantic模型
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
            
            # 4. 构建分页响应数据
            paginated_result = {
                "total": len(membership_responses),  # 简化处理，实际应该查询总数
                "page": page,
                "size": size,
                "items": membership_responses
            }
            
            logger.info(f"成功获取用户订阅列表: user_id={user_id}, count={len(membership_responses)}")
            return paginated_result
            
        except Exception as e:
            logger.error(f"获取用户订阅列表失败: user_id={user_id}, error={e}")
            raise
    
    async def create_new_subscription(self, user: User, sub_create_request: SubscriptionCreateRequest) -> UserMembership:
        """
        创建新的用户订阅
        
        Args:
            user: 用户对象
            sub_create_request: 订阅创建请求
            
        Returns:
            新创建的订阅记录
            
        Raises:
            ProductNotFoundError: 产品不存在或不可购买
            PaymentFailedError: 支付失败
            ActiveSubscriptionExistsError: 用户已有同类有效订阅
        """
        user_id_for_logging = user.id
        product_code_for_logging = sub_create_request.product_code

        logger.info(f"开始创建用户订阅: user_id={user.id}, product_code={product_code_for_logging}")
        
        try:
            # 1. 业务检查 - 检查产品是否有效且可购买
            # 添加调试日志
            logger.info("步骤1: 开始查询活跃产品")
            products = await crud_membership_product.get_multi_active(self.db)
            logger.info(f"步骤1: 成功查询到 {len(products)} 个活跃产品")
            product = None
            for p in products:
                if p.code == sub_create_request.product_code and p.status == MembershipProductStatus.ACTIVE:
                    product = p
                    break
            
            if not product:
                logger.warning(f"产品不存在或不可购买: product_code={sub_create_request.product_code}")
                raise ProductNotFoundError(sub_create_request.product_code)
            
            # 2. 支付逻辑 - 调用支付服务
            payment_result = self._simulate_payment(sub_create_request.payment_token, float(product.price))
            if not payment_result["success"]:
                payment_error = payment_result.get('error', '未知支付错误')
                logger.warning(f"支付失败: user_id={user.id}, error={payment_error}")
                raise PaymentFailedError(payment_error)
            
            # 3. 计算时间 - 根据产品配置计算过期时间
            start_date = datetime.now()
            expires_at = self._calculate_expiry_date(product.duration_unit, product.duration_value)
            
            # 4. 构造Schema - 创建用户订阅对象
            membership_create = UserMembershipCreate(
                user_id=user.id,
                product_code=product.code,
                transaction_id=payment_result["transaction_id"],
                level=product.level,
                status=MembershipStatus.ACTIVE,
                is_auto_renew=True,  # 默认开启自动续费
                start_date=start_date,
                expires_at=expires_at
            )
            
            # 5. 创建记录 - 调用CRUD层创建订阅记录
            try:
                new_membership = await crud_user_membership.create(self.db, obj_in=membership_create)
                logger.info(f"成功创建用户订阅: user_id={user.id}, membership_id={new_membership.id}")
                return new_membership
            except IntegrityError:
                # 6. 异常处理 - 捕获数据库完整性约束错误
                logger.warning(f"用户已有同类有效订阅: user_id={user_id_for_logging}, product_code={product_code_for_logging}")
                raise ActiveSubscriptionExistsError()
                
        except (ProductNotFoundError, PaymentFailedError, ActiveSubscriptionExistsError):
            raise
        except Exception as e:
            logger.error(f"创建用户订阅失败: user_id={user.id}, error={e}")
            raise
    
    async def update_user_subscription(self, user: User, subscription_uuid: uuid.UUID, sub_update_request: SubscriptionUpdateRequest) -> UserMembership:
        """
        更新用户订阅
        
        Args:
            user: 用户对象
            subscription_uuid: 订阅UUID
            sub_update_request: 订阅更新请求
            
        Returns:
            更新后的订阅记录
            
        Raises:
            SubscriptionOwnershipError: 订阅记录不存在或无权修改
            SubscriptionUpdateForbiddenError: 订阅状态不允许修改
        """
        logger.info(f"开始更新用户订阅: user_id={user.id}, subscription_uuid={subscription_uuid}")
        
        try:
            # 1. 数据查询与权限校验 - 获取并验证订阅记录
            membership = await crud_user_membership.get_by_uuid_and_user_id(
                self.db, uuid=subscription_uuid, user_id=user.id
            )
            
            # 2. 检查订阅记录是否存在且属于该用户
            if not membership:
                logger.warning(f"订阅记录不存在或无权限: subscription_uuid={subscription_uuid}, user_id={user.id}")
                raise SubscriptionOwnershipError(str(subscription_uuid))
            
            # 3. 业务检查 - 检查订阅状态是否允许修改
            if membership.status == MembershipStatus.EXPIRED:
                logger.warning(f"已过期的订阅不允许修改: subscription_uuid={subscription_uuid}")
                raise SubscriptionUpdateForbiddenError(membership.status.value)
            
            # 4. 数据更新 - 更新订阅记录
            update_data = UserMembershipUpdate(is_auto_renew=sub_update_request.is_auto_renew)
            updated_membership = await crud_user_membership.update(
                self.db, db_obj=membership, obj_in=update_data
            )
            
            logger.info(f"成功更新用户订阅: user_id={user.id}, subscription_uuid={subscription_uuid}")
            return updated_membership
            
        except (SubscriptionOwnershipError, SubscriptionUpdateForbiddenError):
            raise
        except Exception as e:
            logger.error(f"更新用户订阅失败: user_id={user.id}, subscription_uuid={subscription_uuid}, error={e}")
            raise
    
    # ========================================================================
    # 内部辅助方法
    # ========================================================================
    
    def _simulate_payment(self, payment_token: str, amount: float) -> Dict[str, Any]:
        """
        模拟支付服务调用
        
        Args:
            payment_token: 支付令牌
            amount: 支付金额
            
        Returns:
            支付结果字典，包含 success 状态和 transaction_id
        """
        logger.info(f"模拟支付处理: payment_token={payment_token}, amount={amount}")
        
        # 模拟支付逻辑 - 在实际环境中这里会调用真实的支付网关
        if payment_token.startswith("tok_invalid"):
            return {"success": False, "error": "支付令牌无效"}
        
        if amount <= 0:
            return {"success": False, "error": "支付金额无效"}
        
        # 模拟支付成功
        # 使用UUID确保绝对唯一性
        transaction_id = f"txn_{uuid.uuid4().hex[:16]}_{payment_token[-4:]}"
        return {"success": True, "transaction_id": transaction_id}
    
    def _calculate_expiry_date(self, duration_unit: str, duration_value: int) -> datetime:
        """
        根据产品配置计算过期时间
        
        Args:
            duration_unit: 时长单位 (day, week, month, year)
            duration_value: 时长数值
            
        Returns:
            过期时间
        """
        now = datetime.now()
        
        if duration_unit == "day":
            return now + timedelta(days=duration_value)
        elif duration_unit == "week":
            return now + timedelta(weeks=duration_value)
        elif duration_unit == "month":
            return now + timedelta(days=duration_value * 30)  # 简化计算
        elif duration_unit == "year":
            return now + timedelta(days=duration_value * 365)  # 简化计算
        else:
            # 默认按天计算
            return now + timedelta(days=duration_value) 