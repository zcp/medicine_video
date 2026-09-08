"""
会员产品API端点 - 用户功能服务
实现会员产品公开接口（重构后：业务逻辑已迁移到服务层）
"""
import logging
from typing import Optional
from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_db
from app.core.responses import success_response, error_response
from app.services.membership_products_service import (
    MembershipProductsService,
    InvalidSortParameterError,
    ProductSerializationError
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/membership-products", tags=["Membership Products"])


@router.get("")
async def get_membership_products(
    sort: Optional[str] = Query(
        default="sort_order:asc",
        description="排序字段及顺序，格式: field:direction (如 price:desc)",
        example="sort_order:asc"
    ),
    db: AsyncSession = Depends(get_async_db)
):
    """
    获取可购买的会员产品列表
    
    公开接口，获取所有状态为 ACTIVE 的、可供用户购买的会员产品列表，
    通常用于价格或购买页面。
    
    Args:
        sort: 排序参数，格式为 field:direction
        db: 数据库会话
        
    Returns:
        会员产品列表响应
    """
    # 主动变量提取
    sort_for_logging = sort or "sort_order:asc"
    
    logger.info(f"开始处理获取会员产品列表请求: sort={sort_for_logging}")
    
    try:
        # 实例化服务
        product_service = MembershipProductsService(db)
        
        # 调用服务层方法
        products = await product_service.get_active_products(sort=sort)
        
        logger.info(f"成功处理获取会员产品列表请求: count={len(products)}")
        
        # 构建成功响应
        return success_response(data={
            "items": products
        })
        
    except InvalidSortParameterError as e:
        logger.warning(f"排序参数无效: sort={sort_for_logging}, error={e}")
        return JSONResponse(
            status_code=400,
            content=error_response(
                code=4001,
                message="排序参数格式无效",
                data={"sort_parameter": sort_for_logging}
            )
        )
    except ProductSerializationError as e:
        logger.error(f"产品序列化失败: sort={sort_for_logging}, error={e}")
        return JSONResponse(
            status_code=500,
            content=error_response(
                code=1003,
                message="产品数据处理错误",
                data={"error": "Product serialization failed"}
            )
        )
    except Exception as e:
        logger.error(f"获取会员产品列表失败: sort={sort_for_logging}, error={e}")
        return JSONResponse(
            status_code=500,
            content=error_response(
                code=1002,
                message="数据库查询错误",
                data={"error": "An unexpected database error occurred"}
            )
        ) 