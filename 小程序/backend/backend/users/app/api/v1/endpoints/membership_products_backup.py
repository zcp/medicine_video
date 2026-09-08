"""
会员产品API端点 - 用户功能服务
实现会员产品公开接口
"""
import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_db
from app.core.responses import success_response, error_response
from app.crud import crud_membership_product
from app.schemas.users import MembershipProductResponse

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
    logger.info(f"开始处理获取会员产品列表请求: sort={sort}")
    
    try:
        # 参数处理 - 解析sort查询参数
        sort_field = "sort_order"
        sort_direction = "asc"
        
        if sort and ":" in sort:
            parts = sort.split(":")
            if len(parts) == 2:
                sort_field = parts[0].strip()
                sort_direction = parts[1].strip().lower()
                if sort_direction not in ["asc", "desc"]:
                    sort_direction = "asc"
        
        logger.info(f"解析排序参数: field={sort_field}, direction={sort_direction}")
        
        # 数据查询 - 调用CRUD层获取活跃的会员产品
        products = await crud_membership_product.get_multi_active(
            db, 
            sort=sort_field, 
            direction=sort_direction
        )
        
        # 构建响应 - 序列化为Pydantic模型
        serialized_products: List[MembershipProductResponse] = []
        for product in products:
            try:
                product_response = MembershipProductResponse.model_validate(product)
                serialized_products.append(product_response)
            except Exception as e:
                logger.warning(f"序列化会员产品失败: product_code={product.code}, error={e}")
                continue
        
        logger.info(f"成功获取会员产品列表: count={len(serialized_products)}")
        
        # 最终返回 - 使用success_response构建响应
        return success_response(data={
            "items": [product.model_dump() for product in serialized_products]
        })
        
    except Exception as e:
        logger.error(f"获取会员产品列表失败: error={e}")
        return JSONResponse(
            status_code=500,
            content=error_response(
                code=1002, 
                message="数据库查询错误",
                data={"error": "An unexpected database error occurred"}
            )
        ) 