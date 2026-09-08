"""
管理员产品服务层 - AdminProductsService
封装所有管理员会员产品管理相关的业务逻辑，包括产品创建、查询、更新、删除等管理功能
"""
import logging
from typing import Dict, Any, Optional
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import crud_membership_product
from app.schemas.users import (
    MembershipProductResponse, MembershipProductCreate, MembershipProductUpdate
)
from app.models.users import MembershipProduct, MembershipProductStatus

logger = logging.getLogger(__name__)


# ============================================================================
# 业务异常定义
# ============================================================================

class AdminProductsServiceException(Exception):
    """管理员产品服务基础异常"""
    pass


class ProductCodeExistsError(AdminProductsServiceException):
    """产品编码已存在异常"""
    def __init__(self, message: str = "产品编码已存在"):
        super().__init__(message)


class ProductNotFoundError(AdminProductsServiceException):
    """产品不存在异常"""
    def __init__(self, message: str = "会员产品不存在"):
        super().__init__(message)


class ProductInUseError(AdminProductsServiceException):
    """产品仍被引用异常"""
    def __init__(self, message: str = "无法删除仍被用户订阅引用的产品，请先将其归档(ARCHIVED)"):
        super().__init__(message)


# ============================================================================
# 管理员产品服务类
# ============================================================================

class AdminProductsService:
    """管理员产品服务类"""
    
    def __init__(self, db: AsyncSession):
        """
        初始化管理员产品服务
        
        Args:
            db: 数据库会话
        """
        self.db = db
    
    async def create_product(self, product_in: MembershipProductCreate) -> MembershipProduct:
        """
        创建一个新的会员产品
        
        Args:
            product_in: 产品创建数据
            
        Returns:
            新创建的产品对象
            
        Raises:
            ProductCodeExistsError: 产品编码已存在
        """
        # 🔴 主动变量提取（安全红线）
        product_code_for_logging = product_in.code
        
        logger.info(f"开始创建会员产品: product_code={product_code_for_logging}")
        
        try:
            # 1. 唯一性检查 - 检查产品编码是否已存在
            existing_product = await crud_membership_product.get_by_code(self.db, code=product_in.code)
            if existing_product:
                logger.warning(f"产品编码已存在: product_code={product_code_for_logging}")
                raise ProductCodeExistsError("产品编码已存在")
            
            # 2. 创建产品 - 调用 CRUD 方法创建新产品
            new_product = await crud_membership_product.create(self.db, obj_in=product_in)
            
            logger.info(f"成功创建会员产品: product_code={product_code_for_logging}")
            return new_product
            
        except ProductCodeExistsError:
            raise
        except Exception as e:
            logger.error(f"创建会员产品失败: product_code={product_code_for_logging}, error={e}")
            raise
    
    async def list_products(self, page: int, size: int, status: Optional[MembershipProductStatus] = None) -> Dict[str, Any]:
        """
        分页获取所有会员产品，包括DRAFT、INACTIVE等非上线状态
        
        Args:
            page: 页码
            size: 每页数量
            status: 可选的产品状态筛选
            
        Returns:
            包含分页信息的产品列表字典
        """
        logger.info(f"开始查询会员产品列表: page={page}, size={size}, status={status}")
        
        try:
            # 1. 计算分页参数
            skip = (page - 1) * size
            
            # 2. 数据查询 - 获取总数和当页数据
            total = await crud_membership_product.count_all(self.db)
            products = await crud_membership_product.get_multi_all(
                self.db, skip=skip, limit=size
            )
            
            # 3. 应用筛选 - 如果有状态筛选，在Python代码中过滤
            if status:
                products = [p for p in products if p.status == status]
                total = len(products)
            
            # 4. 序列化 - 将SQLAlchemy对象列表转换为Pydantic模型
            product_responses = []
            for product in products:
                try:
                    product_response = MembershipProductResponse.model_validate(product)
                    product_responses.append(product_response)
                except Exception as e:
                    product_code = getattr(product, 'code', 'unknown')
                    logger.warning(f"序列化产品失败: product_code={product_code}, error={e}")
                    # 跳过失败的产品，继续处理其他产品
                    continue
            
            # 5. 构建分页响应数据
            paginated_result = {
                "total": total,
                "page": page,
                "size": size,
                "items": product_responses
            }
            
            logger.info(f"成功查询会员产品列表: total={total}, count={len(product_responses)}")
            return paginated_result
            
        except Exception as e:
            logger.error(f"查询会员产品列表失败: page={page}, size={size}, error={e}")
            raise
    
    async def get_product(self, product_code: str) -> MembershipProduct:
        """
        获取单个会员产品的全部信息，用于编辑页面
        
        Args:
            product_code: 产品编码
            
        Returns:
            产品对象
            
        Raises:
            ProductNotFoundError: 产品不存在
        """
        logger.info(f"开始查询会员产品详情: product_code={product_code}")
        
        try:
            # 1. 数据查询 - 根据产品编码获取产品
            product = await crud_membership_product.get_by_code(self.db, code=product_code)
            if not product:
                logger.warning(f"会员产品不存在: product_code={product_code}")
                raise ProductNotFoundError("会员产品不存在")
            
            logger.info(f"成功查询会员产品详情: product_code={product_code}")
            return product
            
        except ProductNotFoundError:
            raise
        except Exception as e:
            logger.error(f"查询会员产品详情失败: product_code={product_code}, error={e}")
            raise
    
    async def update_product(self, product_code: str, product_update: MembershipProductUpdate) -> MembershipProduct:
        """
        更新一个已存在的会员产品
        
        Args:
            product_code: 产品编码
            product_update: 产品更新数据
            
        Returns:
            更新后的产品对象
            
        Raises:
            ProductNotFoundError: 产品不存在
        """
        logger.info(f"开始更新会员产品: product_code={product_code}")
        
        try:
            # 1. 数据查询 - 根据产品编码获取要更新的产品
            product_to_update = await crud_membership_product.get_by_code(self.db, code=product_code)
            if not product_to_update:
                logger.warning(f"会员产品不存在: product_code={product_code}")
                raise ProductNotFoundError("会员产品不存在")
            
            # 2. 数据更新 - 调用 CRUD 方法更新产品
            updated_product = await crud_membership_product.update(
                self.db, db_obj=product_to_update, obj_in=product_update
            )
            
            logger.info(f"成功更新会员产品: product_code={product_code}")
            return updated_product
            
        except ProductNotFoundError:
            raise
        except Exception as e:
            logger.error(f"更新会员产品失败: product_code={product_code}, error={e}")
            raise
    
    async def delete_product(self, product_code: str) -> MembershipProduct:
        """
        删除一个会员产品
        注意：只有在没有任何用户订阅记录引用的情况下才能成功
        
        Args:
            product_code: 产品编码
            
        Returns:
            被删除的产品对象
            
        Raises:
            ProductNotFoundError: 产品不存在
            ProductInUseError: 产品仍被引用无法删除
        """
        logger.info(f"开始删除会员产品: product_code={product_code}")
        
        try:
            # 1. 尝试删除产品 - 在 try...except IntegrityError 块中处理
            deleted_product = await crud_membership_product.remove(self.db, code=product_code)
            if not deleted_product:
                logger.warning(f"会员产品不存在: product_code={product_code}")
                raise ProductNotFoundError("会员产品不存在")
            
            logger.info(f"成功删除会员产品: product_code={product_code}")
            return deleted_product
            
        except IntegrityError:
            # 2. 异常处理 - 产品仍被引用
            logger.warning(f"删除会员产品失败，仍被引用: product_code={product_code}")
            raise ProductInUseError("无法删除仍被用户订阅引用的产品，请先将其归档(ARCHIVED)")
        except ProductNotFoundError:
            raise
        except Exception as e:
            logger.error(f"删除会员产品失败: product_code={product_code}, error={e}")
            raise 