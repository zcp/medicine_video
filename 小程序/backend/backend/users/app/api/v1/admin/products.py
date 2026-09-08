"""
后台管理API - 会员产品管理 (重构版)
重构后的端点层只负责：
- 处理 FastAPI 的 Request 和 Depends
- 实例化 AdminProductsService
- 调用 AdminProductsService 中对应的方法
- 捕获 Service 层抛出的业务异常并转换为标准的 JSONResponse
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query, Path
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_db
from app.core.responses import success_response, error_response
from app.schemas.users import (
    MembershipProductResponse, MembershipProductCreate, MembershipProductUpdate
)
from app.models.users import User, MembershipProductStatus
from app.api.v1.deps import get_current_admin_user
from app.services.admin_products_service import (
    AdminProductsService,
    ProductCodeExistsError,
    ProductNotFoundError,
    ProductInUseError
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/membership-products", tags=["Admin - Products"])


# ============================================================================
# API 端点实现
# ============================================================================

@router.post("", response_model=dict)
async def create_product(
    product_in: MembershipProductCreate,
    admin_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    (管理员) 创建一个新的会员产品
    """
    # 🔴 主动变量提取（安全红线）
    admin_user_id_for_logging = admin_user.id
    product_code_for_logging = product_in.code
    
    logger.info(f"管理员开始创建会员产品: admin_user_id={admin_user_id_for_logging}, product_code={product_code_for_logging}")
    
    try:
        # 实例化服务层
        product_service = AdminProductsService(db)
        
        # 调用服务层方法创建产品
        new_product = await product_service.create_product(product_in=product_in)
        
        # 序列化响应数据
        response_data = MembershipProductResponse.model_validate(new_product)
        
        logger.info(f"成功创建会员产品: admin_user_id={admin_user_id_for_logging}, product_code={product_code_for_logging}")
        return success_response(data=response_data)
        
    except ProductCodeExistsError as e:
        logger.warning(f"产品编码已存在: admin_user_id={admin_user_id_for_logging}, product_code={product_code_for_logging}")
        return JSONResponse(
            status_code=409,
            content=error_response(code=2001, message=str(e))
        )
    except Exception as e:
        # 使用安全的局部变量进行日志记录，避免访问可能已失效的ORM对象
        logger.error(f"创建会员产品失败: admin_user_id={admin_user_id_for_logging}, product_code={product_code_for_logging}, error={e}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message='数据库查询错误')
        )


@router.get("", response_model=dict)
async def get_products_list(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=100, description="每页数量"),
    sort: Optional[str] = Query("created_at:desc", description="排序字段"),
    status: Optional[MembershipProductStatus] = Query(None, description="按产品状态筛选"),
    admin_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    (管理员) 分页获取所有会员产品，包括DRAFT、INACTIVE等非上线状态
    """
    # 🔴 主动变量提取（安全红线）
    admin_user_id_for_logging = admin_user.id
    
    logger.info(f"管理员开始查询会员产品列表: admin_user_id={admin_user_id_for_logging}, page={page}, size={size}")
    
    try:
        # 实例化服务层
        product_service = AdminProductsService(db)
        
        # 调用服务层方法获取分页产品列表
        paginated_result = await product_service.list_products(
            page=page, size=size, status=status
        )
        
        logger.info(f"成功查询会员产品列表: admin_user_id={admin_user_id_for_logging}, total={paginated_result.get('total', 0)}, count={len(paginated_result.get('items', []))}")
        return success_response(data=paginated_result)
        
    except Exception as e:
        # 使用安全的局部变量进行日志记录，避免访问可能已失效的ORM对象
        logger.error(f"查询会员产品列表失败: admin_user_id={admin_user_id_for_logging}, error={e}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message='数据库查询错误')
        )


@router.get("/{product_code}", response_model=dict)
async def get_product_detail(
    product_code: str = Path(..., description="产品编码"),
    admin_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    (管理员) 获取单个会员产品的全部信息，用于编辑页面
    """
    # 🔴 主动变量提取（安全红线）
    admin_user_id_for_logging = admin_user.id
    
    logger.info(f"管理员开始查询会员产品详情: admin_user_id={admin_user_id_for_logging}, product_code={product_code}")
    
    try:
        # 实例化服务层
        product_service = AdminProductsService(db)
        
        # 调用服务层方法获取产品详情
        product = await product_service.get_product(product_code=product_code)
        
        # 序列化响应数据
        response_data = MembershipProductResponse.model_validate(product)
        
        logger.info(f"成功查询会员产品详情: admin_user_id={admin_user_id_for_logging}, product_code={product_code}")
        return success_response(data=response_data)
        
    except ProductNotFoundError as e:
        logger.warning(f"会员产品不存在: admin_user_id={admin_user_id_for_logging}, product_code={product_code}")
        return JSONResponse(
            status_code=404,
            content=error_response(code=2004, message=str(e))
        )
    except Exception as e:
        # 使用安全的局部变量进行日志记录，避免访问可能已失效的ORM对象
        logger.error(f"查询会员产品详情失败: admin_user_id={admin_user_id_for_logging}, product_code={product_code}, error={e}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message='数据库查询错误')
        )


@router.patch("/{product_code}", response_model=dict)
async def update_product(
    product_code: str = Path(..., description="产品编码"),
    product_update: MembershipProductUpdate = ...,
    admin_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    (管理员) 更新一个已存在的会员产品
    """
    # 🔴 主动变量提取（安全红线）
    admin_user_id_for_logging = admin_user.id
    
    logger.info(f"管理员开始更新会员产品: admin_user_id={admin_user_id_for_logging}, product_code={product_code}")
    
    try:
        # 实例化服务层
        product_service = AdminProductsService(db)
        
        # 调用服务层方法更新产品
        updated_product = await product_service.update_product(
            product_code=product_code, product_update=product_update
        )
        
        # 序列化响应数据
        response_data = MembershipProductResponse.model_validate(updated_product)
        
        logger.info(f"成功更新会员产品: admin_user_id={admin_user_id_for_logging}, product_code={product_code}")
        return success_response(data=response_data)
        
    except ProductNotFoundError as e:
        logger.warning(f"会员产品不存在: admin_user_id={admin_user_id_for_logging}, product_code={product_code}")
        return JSONResponse(
            status_code=404,
            content=error_response(code=2004, message=str(e))
        )
    except Exception as e:
        # 使用安全的局部变量进行日志记录，避免访问可能已失效的ORM对象
        logger.error(f"更新会员产品失败: admin_user_id={admin_user_id_for_logging}, product_code={product_code}, error={e}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message='数据库查询错误')
        )


@router.delete("/{product_code}", response_model=dict)
async def delete_product(
    product_code: str = Path(..., description="产品编码"),
    admin_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    (管理员) 删除一个会员产品
    注意：只有在没有任何用户订阅记录引用的情况下才能成功
    """
    # 🔴 主动变量提取（安全红线）
    admin_user_id_for_logging = admin_user.id
    
    logger.info(f"管理员开始删除会员产品: admin_user_id={admin_user_id_for_logging}, product_code={product_code}")
    
    try:
        # 实例化服务层
        product_service = AdminProductsService(db)
        
        # 调用服务层方法删除产品
        await product_service.delete_product(product_code=product_code)
        
        logger.info(f"成功删除会员产品: admin_user_id={admin_user_id_for_logging}, product_code={product_code}")
        return success_response(data=None)
        
    except ProductNotFoundError as e:
        logger.warning(f"会员产品不存在: admin_user_id={admin_user_id_for_logging}, product_code={product_code}")
        return JSONResponse(
            status_code=404,
            content=error_response(code=2004, message=str(e))
        )
    except ProductInUseError as e:
        logger.warning(f"删除会员产品失败，仍被引用: admin_user_id={admin_user_id_for_logging}, product_code={product_code}")
        return JSONResponse(
            status_code=400,
            content=error_response(code=2006, message=str(e))
        )
    except Exception as e:
        # 使用安全的局部变量进行日志记录，避免访问可能已失效的ORM对象
        logger.error(f"删除会员产品失败: admin_user_id={admin_user_id_for_logging}, product_code={product_code}, error={e}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message='数据库查询错误')
        ) 