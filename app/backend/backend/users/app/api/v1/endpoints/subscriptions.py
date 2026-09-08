"""
用户订阅管理API端点 - 用户功能服务 (重构版)
实现用户侧会员订阅流程：获取订阅列表、购买订阅、更新订阅设置

重构后的端点层只负责：
- 处理 FastAPI 的 Request 和 Depends
- 实例化 SubscriptionsService
- 调用 SubscriptionsService 中对应的方法
- 捕获 Service 层抛出的业务异常并转换为标准的 JSONResponse
"""
import logging
import uuid

from fastapi import APIRouter, Depends, Path, Query
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_db
from app.core.responses import success_response, error_response
from app.schemas.users import (
    UserMembershipResponse, SubscriptionCreateRequest, SubscriptionUpdateRequest
)
from app.models.users import User
from app.api.v1.deps import get_current_user
from app.services.subscriptions_service import (
    SubscriptionsService,
    ProductNotFoundError,
    PaymentFailedError,
    ActiveSubscriptionExistsError,
    SubscriptionOwnershipError,
    SubscriptionUpdateForbiddenError
)

logger = logging.getLogger(__name__)

subscriptions_router = APIRouter(tags=["User Subscriptions"])


# ============================================================================
# API 端点实现
# ============================================================================

@subscriptions_router.get("", response_model=dict)
async def get_my_memberships(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=100, description="每页数量"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    获取当前用户的会员订阅列表
    
    获取当前登录用户的所有会员订阅记录（包括历史记录和当前生效的）
    """
    # 【主动变量提取】: 在进入try块之前，将需要用于日志记录的用户信息提取到局部变量中
    user_id_for_logging = current_user.id
    
    logger.info(f"开始获取用户订阅列表: user_id={user_id_for_logging}, page={page}, size={size}")
    
    try:
        # 实例化服务层
        sub_service = SubscriptionsService(db)
        
        # 调用服务层方法获取分页订阅列表
        paginated_result = await sub_service.get_user_subscriptions(
            user_id=current_user.id, page=page, size=size
        )
        
        logger.info(f"成功获取用户订阅列表: user_id={user_id_for_logging}, count={len(paginated_result.get('items', []))}")
        return success_response(data=paginated_result)
        
    except Exception as e:
        # 使用安全的局部变量进行日志记录，避免访问可能已失效的ORM对象
        logger.error(f"获取用户订阅列表失败: user_id={user_id_for_logging}, error={e}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=5001, message="服务器内部错误")
        )


@subscriptions_router.post("", response_model=dict)
async def create_subscription(
    request: SubscriptionCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    用户购买/创建新订阅
    
    用户为自己创建一个新的订阅。这是整个会员体系的核心交易接口。
    """
    # 【主动变量提取】: 在进入try块之前，将需要用于日志记录的用户信息提取到局部变量中
    user_id_for_logging = current_user.id
    product_code_for_logging = request.product_code
    payment_token_for_logging = request.payment_token
    logger.info(f"开始创建用户订阅: user_id={user_id_for_logging}, product_code={product_code_for_logging}")
    
    try:
        # 实例化服务层
        sub_service = SubscriptionsService(db)
        
        # 调用服务层方法创建新订阅
        new_subscription = await sub_service.create_new_subscription(
            user=current_user, sub_create_request=request
        )
        
        # 序列化响应数据
        response_data = UserMembershipResponse.model_validate(new_subscription)
        
        logger.info(f"成功创建用户订阅: user_id={user_id_for_logging}, membership_id={new_subscription.id}")
        return success_response(data=response_data)
        
    except ProductNotFoundError as e:
        logger.warning(f"产品不存在或不可购买: user_id={user_id_for_logging}, product_code={product_code_for_logging}")
        return JSONResponse(
            status_code=404,
            content=error_response(code=2004, message=str(e))
        )
    except ActiveSubscriptionExistsError as e:
        logger.warning(f"用户已有同类有效订阅: user_id={user_id_for_logging}, product_code={product_code_for_logging}")
        return JSONResponse(
            status_code=409,
            content=error_response(code=2005, message=str(e))
        )
    except PaymentFailedError:
        # 使用预定义的错误消息
        logger.warning(f"支付失败: user_id={user_id_for_logging}, payment_token={payment_token_for_logging}")
        return JSONResponse(
            status_code=402,
            content=error_response(code=4002, message="支付处理失败")
        )
    except IntegrityError:
        # ✅ FIX: Use the safe local variable for logging
        logger.warning(f"用户已有同类有效订阅: user_id={user_id_for_logging}, product_code={request.product_code}")
        return JSONResponse(
            status_code=409,
            content=error_response(code=2005, message='您已拥有一个正在生效的同类会员')
        )
    except Exception as e:
        # 使用安全的局部变量进行日志记录，避免访问可能已失效的ORM对象
        logger.error(f"创建用户订阅失败: user_id={user_id_for_logging}, error={e}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=5001, message="服务器内部错误")
        )


@subscriptions_router.patch("/{subscription_uuid}", response_model=dict)
async def update_subscription(
    subscription_uuid: uuid.UUID = Path(..., description="订阅UUID"),
    request: SubscriptionUpdateRequest = ...,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    用户更新自己的订阅
    
    更新用户自己的一条订阅记录，主要用于开关"自动续费"。
    """
    # 【主动变量提取】: 在进入try块之前，将需要用于日志记录的用户信息提取到局部变量中
    user_id_for_logging = current_user.id
    subscription_uuid_for_logging = str(subscription_uuid)
    
    logger.info(f"开始更新用户订阅: user_id={user_id_for_logging}, subscription_uuid={subscription_uuid_for_logging}")
    
    try:
        # 实例化服务层
        sub_service = SubscriptionsService(db)
        
        # 调用服务层方法更新订阅
        updated_subscription = await sub_service.update_user_subscription(
            user=current_user, subscription_uuid=subscription_uuid, sub_update_request=request
        )
        
        # 序列化响应数据
        response_data = UserMembershipResponse.model_validate(updated_subscription)
        
        logger.info(f"成功更新用户订阅: user_id={user_id_for_logging}, subscription_uuid={subscription_uuid_for_logging}")
        return success_response(data=response_data)
        
    except SubscriptionOwnershipError as e:
        logger.warning(f"订阅记录不存在或无权限: user_id={user_id_for_logging}, subscription_uuid={subscription_uuid_for_logging}")
        return JSONResponse(
            status_code=404,
            content=error_response(code=2004, message=str(e))
        )
    except SubscriptionUpdateForbiddenError as e:
        logger.warning(f"订阅状态不允许修改: user_id={user_id_for_logging}, subscription_uuid={subscription_uuid_for_logging}")
        return JSONResponse(
            status_code=400,
            content=error_response(code=2002, message=str(e))
        )
    except Exception as e:
        # 使用安全的局部变量进行日志记录，避免访问可能已失效的ORM对象
        logger.error(f"更新用户订阅失败: user_id={user_id_for_logging}, subscription_uuid={subscription_uuid_for_logging}, error={e}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=5001, message="服务器内部错误")
        ) 