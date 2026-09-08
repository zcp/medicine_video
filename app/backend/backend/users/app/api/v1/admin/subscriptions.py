"""
后台管理API - 订阅管理 (重构版)
重构后的端点层只负责：
- 处理 FastAPI 的 Request 和 Depends
- 实例化 AdminSubscriptionsService
- 调用 AdminSubscriptionsService 中对应的方法
- 捕获 Service 层抛出的业务异常并转换为标准的 JSONResponse
"""
import logging
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query, Path
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_db
from app.core.responses import success_response, error_response
from app.schemas.users import (
    UserMembershipResponse, UserMembershipCreateAdmin, UserMembershipUpdate
)
from app.models.users import User
from app.api.v1.deps import get_current_admin_user
from app.services.admin_subscriptions_service import (
    AdminSubscriptionsService,
    TargetUserNotFoundError,
    ProductNotFoundError,
    SubscriptionNotFoundError,
    ActiveSubscriptionExistsError
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/subscriptions", tags=["Admin - Subscriptions"])


# ============================================================================
# API 端点实现
# ============================================================================

@router.get("/by-user/{user_uuid}", response_model=dict)
async def get_user_subscriptions(
    user_uuid: uuid.UUID = Path(..., description="用户UUID"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=100, description="每页数量"),
    admin_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    (管理员) 获取指定用户的所有订阅历史记录（分页）
    """
    # 🔴 主动变量提取（安全红线）
    admin_user_id_for_logging = admin_user.id
    user_uuid_for_logging = str(user_uuid)
    
    logger.info(f"管理员开始获取用户订阅列表: admin_user_id={admin_user_id_for_logging}, user_uuid={user_uuid_for_logging}, page={page}, size={size}")
    
    try:
        # 实例化服务层
        subscription_service = AdminSubscriptionsService(db)
        
        # 调用服务层方法获取用户订阅列表
        paginated_result = await subscription_service.get_subscriptions_by_user(
            user_uuid=user_uuid, page=page, size=size
        )
        
        logger.info(f"成功获取用户订阅列表: admin_user_id={admin_user_id_for_logging}, user_uuid={user_uuid_for_logging}, total={paginated_result.get('total', 0)}")
        return success_response(data=paginated_result)
        
    except TargetUserNotFoundError as e:
        logger.warning(f"目标用户不存在: admin_user_id={admin_user_id_for_logging}, user_uuid={user_uuid_for_logging}")
        return JSONResponse(
            status_code=404,
            content=error_response(code=2004, message=str(e))
        )
    except Exception as e:
        # 使用安全的局部变量进行日志记录，避免访问可能已失效的ORM对象
        logger.error(f"获取用户订阅列表失败: admin_user_id={admin_user_id_for_logging}, user_uuid={user_uuid_for_logging}, error={e}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message='数据库查询错误')
        )


@router.post("/by-user/{user_uuid}", response_model=dict)
async def create_subscription_for_user(
    user_uuid: uuid.UUID = Path(..., description="用户UUID"),
    subscription_in: UserMembershipCreateAdmin = ...,
    admin_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    (管理员) 手动为用户创建订阅
    """
    # 🔴 主动变量提取（安全红线）
    admin_user_id_for_logging = admin_user.id
    user_uuid_for_logging = str(user_uuid)
    product_code_for_logging = subscription_in.product_code
    
    logger.info(f"管理员开始为用户创建订阅: admin_user_id={admin_user_id_for_logging}, user_uuid={user_uuid_for_logging}, product_code={product_code_for_logging}")
    
    try:
        # 实例化服务层
        subscription_service = AdminSubscriptionsService(db)
        
        # 调用服务层方法创建订阅
        new_subscription = await subscription_service.create_subscription_for_user(
            user_uuid=user_uuid, sub_create_request=subscription_in
        )
        
        # 序列化响应数据
        response_data = UserMembershipResponse.model_validate(new_subscription)
        
        logger.info(f"成功为用户创建订阅: admin_user_id={admin_user_id_for_logging}, user_uuid={user_uuid_for_logging}, product_code={product_code_for_logging}")
        return success_response(data=response_data)
        
    except TargetUserNotFoundError as e:
        logger.warning(f"目标用户不存在: admin_user_id={admin_user_id_for_logging}, user_uuid={user_uuid_for_logging}")
        return JSONResponse(
            status_code=404,
            content=error_response(code=2004, message=str(e))
        )
    except ProductNotFoundError as e:
        logger.warning(f"产品不存在: admin_user_id={admin_user_id_for_logging}, product_code={product_code_for_logging}")
        return JSONResponse(
            status_code=404,
            content=error_response(code=2004, message=str(e))
        )
    except ActiveSubscriptionExistsError as e:
        logger.warning(f"用户已有同类有效订阅: admin_user_id={admin_user_id_for_logging}, user_uuid={user_uuid_for_logging}, product_code={product_code_for_logging}")
        return JSONResponse(
            status_code=409,
            content=error_response(code=2002, message=str(e))
        )
    except Exception as e:
        # 使用安全的局部变量进行日志记录，避免访问可能已失效的ORM对象
        logger.error(f"为用户创建订阅失败: admin_user_id={admin_user_id_for_logging}, user_uuid={user_uuid_for_logging}, product_code={product_code_for_logging}, error={e}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message='数据库查询错误')
        )


@router.patch("/{subscription_uuid}", response_model=dict)
async def update_subscription(
    subscription_uuid: uuid.UUID = Path(..., description="订阅UUID"),
    subscription_update: UserMembershipUpdate = ...,
    admin_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    (管理员) 更新指定订阅记录
    """
    # 🔴 主动变量提取（安全红线）
    admin_user_id_for_logging = admin_user.id
    subscription_uuid_for_logging = str(subscription_uuid)
    
    logger.info(f"管理员开始更新订阅: admin_user_id={admin_user_id_for_logging}, subscription_uuid={subscription_uuid_for_logging}")
    
    try:
        # 实例化服务层
        subscription_service = AdminSubscriptionsService(db)
        
        # 调用服务层方法更新订阅
        updated_subscription = await subscription_service.update_subscription(
            subscription_uuid=subscription_uuid, sub_update_request=subscription_update
        )
        
        # 序列化响应数据
        response_data = UserMembershipResponse.model_validate(updated_subscription)
        
        logger.info(f"成功更新订阅: admin_user_id={admin_user_id_for_logging}, subscription_uuid={subscription_uuid_for_logging}")
        return success_response(data=response_data)
        
    except SubscriptionNotFoundError as e:
        logger.warning(f"订阅记录不存在: admin_user_id={admin_user_id_for_logging}, subscription_uuid={subscription_uuid_for_logging}")
        return JSONResponse(
            status_code=404,
            content=error_response(code=2004, message=str(e))
        )
    except Exception as e:
        # 使用安全的局部变量进行日志记录，避免访问可能已失效的ORM对象
        logger.error(f"更新订阅失败: admin_user_id={admin_user_id_for_logging}, subscription_uuid={subscription_uuid_for_logging}, error={e}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message='数据库查询错误')
        )

