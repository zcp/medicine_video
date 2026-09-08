"""
用户订阅管理API端点 - 用户功能服务
实现用户侧会员订阅流程：获取订阅列表、购买订阅、更新订阅设置
"""
import logging
import uuid
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Path, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.database import get_async_db
from app.core.responses import success_response, error_response
from app.crud import crud_user_membership, crud_membership_product
from app.schemas.users import (
    UserMembershipResponse, UserMembershipCreate, UserMembershipUpdate,
    SubscriptionCreateRequest, SubscriptionUpdateRequest, PaginatedSubscriptionsResponse
)
from app.models.users import User, MembershipStatus, MembershipProductStatus
from app.api.v1.deps import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users/me/memberships", tags=["User Subscriptions"])


# ============================================================================
# 工具函数
# ============================================================================

async def simulate_payment(payment_token: str, amount: float) -> dict:
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
    transaction_id = f"txn_{datetime.now().strftime('%Y%m%d%H%M%S')}_{payment_token[-4:]}"
    return {"success": True, "transaction_id": transaction_id}


def calculate_expiry_date(duration_unit: str, duration_value: int) -> datetime:
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


# ============================================================================
# API 端点实现
# ============================================================================

@router.get("", response_model=dict)
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
    logger.info(f"开始获取用户订阅列表: user_id={current_user.id}, page={page}, size={size}")
    
    try:
        # 计算分页参数
        skip = (page - 1) * size
        
        # 获取用户的订阅列表
        memberships = await crud_user_membership.get_multi_by_user_id(
            db, user_id=current_user.id, skip=skip, limit=size
        )
        
        # 将结果序列化为List[schemas.UserMembershipResponse]
        membership_responses = [
            UserMembershipResponse.model_validate(membership) 
            for membership in memberships
        ]
        
        # 构建分页响应数据
        response_data = {
            "total": len(membership_responses),  # 简化处理，实际应该查询总数
            "page": page,
            "size": size,
            "items": membership_responses
        }
        
        logger.info(f"成功获取用户订阅列表: user_id={current_user.id}, count={len(membership_responses)}")
        return success_response(response_data)
        
    except Exception as e:
        logger.error(f"获取用户订阅列表失败: user_id={current_user.id}, error={e}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=5001, message="服务器内部错误")
        )


@router.post("", response_model=dict)
async def create_subscription(
    request: SubscriptionCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    用户购买/创建新订阅
    
    用户为自己创建一个新的订阅。这是整个会员体系的核心交易接口。
    """
    # 【安全日志准备】: 在进入try块之前，将需要用于日志记录的用户信息提取到局部变量中
    user_id_for_logging = current_user.id
    
    logger.info(f"开始创建用户订阅: user_id={user_id_for_logging}, product_code={request.product_code}")
    
    try:
        # 1. 业务检查: 调用CRUD检查product_code是否有效且可购买
        products = await crud_membership_product.get_multi_active(db)
        product = None
        for p in products:
            if p.code == request.product_code and p.status == MembershipProductStatus.ACTIVE:
                product = p
                break
        
        if not product:
            logger.warning(f"产品不存在或不可购买: product_code={request.product_code}")
            return JSONResponse(
                status_code=404,
                content=error_response(code=2004, message="产品不存在或不可购买")
            )
        
        # 2. 支付逻辑: (模拟)调用支付服务
        payment_result = await simulate_payment(request.payment_token, float(product.price))
        if not payment_result["success"]:
            logger.warning(f"支付失败: user_id={user_id_for_logging}, error={payment_result.get('error')}")
            return JSONResponse(
                status_code=402,
                content=error_response(code=4002, message="支付失败", data={"error": payment_result.get("error")})
            )
        
        # 3. 支付成功后，构造schemas.UserMembershipCreate对象（user_id来自current_user.id）
        start_date = datetime.now()
        expires_at = calculate_expiry_date(product.duration_unit, product.duration_value)
        
        membership_create = UserMembershipCreate(
            user_id=current_user.id,
            product_code=product.code,
            transaction_id=payment_result["transaction_id"],
            level=product.level,
            status=MembershipStatus.ACTIVE,
            is_auto_renew=True,  # 默认开启自动续费
            start_date=start_date,
            expires_at=expires_at
        )
        
        # 4. 调用crud_user_membership.create()创建订阅记录
        try:
            new_membership = await crud_user_membership.create(db, obj_in=membership_create)
        except IntegrityError:
            # 5. 异常处理: 捕获IntegrityError并返回409冲突
            # 使用安全的局部变量进行日志记录，避免访问可能已失效的ORM对象
            logger.warning(f"用户已有同类有效订阅: user_id={user_id_for_logging}, product_code={request.product_code}")
            return JSONResponse(
                status_code=409,
                content=error_response(code=2005, message='您已拥有一个正在生效的同类会员')
            )
        
        # 6. 调用success_response返回新创建的订阅信息
        response_data = UserMembershipResponse.model_validate(new_membership)
        logger.info(f"成功创建用户订阅: user_id={user_id_for_logging}, membership_id={new_membership.id}")
        return success_response(response_data)
        
    except Exception as e:
        # 使用安全的局部变量进行日志记录，避免访问可能已失效的ORM对象
        logger.error(f"创建用户订阅失败: user_id={user_id_for_logging}, error={e}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=5001, message="服务器内部错误")
        )


@router.patch("/{subscription_uuid}", response_model=dict)
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
    logger.info(f"开始更新用户订阅: user_id={current_user.id}, subscription_uuid={subscription_uuid}")
    
    try:
        # 1. 调用crud_user_membership.get_by_uuid_and_user_id()，并传入uuid=subscription_uuid和user_id=current_user.id来获取并验证订阅记录
        membership = await crud_user_membership.get_by_uuid_and_user_id(
            db, uuid=subscription_uuid, user_id=current_user.id
        )
        
        # 2. 若记录为None（不存在或不属于该用户），返回JSONResponse(status_code=404, content=error_response(code=2004, message='订阅记录不存在'))
        if not membership:
            logger.warning(f"订阅记录不存在或无权限: subscription_uuid={subscription_uuid}, user_id={current_user.id}")
            return JSONResponse(
                status_code=404,
                content=error_response(code=2004, message='订阅记录不存在')
            )
        
        # 3. 业务检查: 检查订阅状态是否允许修改is_auto_renew（例如，EXPIRED状态的就不允许）
        if membership.status == MembershipStatus.EXPIRED:
            logger.warning(f"已过期的订阅不允许修改: subscription_uuid={subscription_uuid}")
            return JSONResponse(
                status_code=400,
                content=error_response(code=2002, message="已过期的订阅不允许修改续费设置")
            )
        
        # 4. 调用crud_user_membership.update()更新记录
        update_data = UserMembershipUpdate(is_auto_renew=request.is_auto_renew)
        updated_membership = await crud_user_membership.update(
            db, db_obj=membership, obj_in=update_data
        )
        
        # 5. 调用success_response返回更新后的订阅信息
        response_data = UserMembershipResponse.model_validate(updated_membership)
        logger.info(f"成功更新用户订阅: user_id={current_user.id}, subscription_uuid={subscription_uuid}")
        return success_response(response_data)
        
    except Exception as e:
        logger.error(f"更新用户订阅失败: user_id={current_user.id}, subscription_uuid={subscription_uuid}, error={e}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=5001, message="服务器内部错误")
        ) 