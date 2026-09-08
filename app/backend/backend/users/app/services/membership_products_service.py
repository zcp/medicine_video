"""
会员产品服务层 - MembershipProductsService
封装所有会员产品相关的业务逻辑，包括数据查询、参数处理、序列化等
"""
import logging
from typing import Optional, List

from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import crud_membership_product
from app.schemas.users import MembershipProductResponse

logger = logging.getLogger(__name__)


# ============================================================================
# 业务异常定义
# ============================================================================

class MembershipProductsServiceException(Exception):
    """会员产品服务基础异常"""
    pass


class InvalidSortParameterError(MembershipProductsServiceException):
    """无效排序参数异常"""
    def __init__(self, sort_param: str, message: str = "排序参数格式无效"):
        self.sort_param = sort_param
        super().__init__(f"{message}: {sort_param}")


class ProductSerializationError(MembershipProductsServiceException):
    """产品序列化异常"""
    def __init__(self, product_code: str, message: str = "产品序列化失败"):
        self.product_code = product_code
        super().__init__(f"{message}: {product_code}")


# ============================================================================
# 会员产品服务类
# ============================================================================

class MembershipProductsService:
    """会员产品服务类"""
    
    def __init__(self, db: AsyncSession):
        """
        初始化会员产品服务
        
        Args:
            db: 数据库会话
        """
        self.db = db
    
    async def get_active_products(self, sort: Optional[str] = None) -> List[dict]:
        """
        获取可购买的会员产品列表
        
        Args:
            sort: 排序参数，格式为 field:direction
            
        Returns:
            序列化后的会员产品列表
            
        Raises:
            InvalidSortParameterError: 排序参数格式无效
            ProductSerializationError: 产品序列化失败
        """
        logger.info(f"开始处理获取会员产品列表请求: sort={sort}")
        
        try:
            # 1. 参数处理 - 解析sort查询参数
            sort_field, sort_direction = self._parse_sort_parameter(sort)
            
            logger.info(f"解析排序参数: field={sort_field}, direction={sort_direction}")
            
            # 2. 数据查询 - 调用CRUD层获取活跃的会员产品
            products = await crud_membership_product.get_multi_active(
                self.db, 
                sort=sort_field, 
                direction=sort_direction
            )
            
            # 3. 序列化 - 将SQLAlchemy对象转换为Pydantic模型
            serialized_products = self._serialize_products(products)
            
            logger.info(f"成功获取会员产品列表: count={len(serialized_products)}")
            
            # 4. 返回序列化后的数据
            return [product.model_dump() for product in serialized_products]
            
        except (InvalidSortParameterError, ProductSerializationError):
            raise
        except Exception as e:
            logger.error(f"获取会员产品列表失败: error={e}")
            raise
    
    def _parse_sort_parameter(self, sort: Optional[str]) -> tuple[str, str]:
        """
        解析排序参数
        
        Args:
            sort: 排序参数字符串，格式为 field:direction
            
        Returns:
            (sort_field, sort_direction) 元组
            
        Raises:
            InvalidSortParameterError: 排序参数格式无效
        """
        # 设置默认值
        sort_field = "sort_order"
        sort_direction = "asc"
        
        if sort and ":" in sort:
            parts = sort.split(":")
            if len(parts) == 2:
                sort_field = parts[0].strip()
                sort_direction = parts[1].strip().lower()
                
                # 验证排序方向
                if sort_direction not in ["asc", "desc"]:
                    logger.warning(f"无效的排序方向: {sort_direction}, 重置为默认值 asc")
                    sort_direction = "asc"
            else:
                logger.warning(f"排序参数格式错误: {sort}, 使用默认排序")
        
        return sort_field, sort_direction
    
    def _serialize_products(self, products: List) -> List[MembershipProductResponse]:
        """
        序列化产品列表
        
        Args:
            products: SQLAlchemy 产品对象列表
            
        Returns:
            序列化后的 Pydantic 产品对象列表
            
        Raises:
            ProductSerializationError: 序列化失败
        """
        serialized_products: List[MembershipProductResponse] = []
        
        for product in products:
            try:
                product_response = MembershipProductResponse.model_validate(product)
                serialized_products.append(product_response)
            except Exception as e:
                product_code = getattr(product, 'code', 'unknown')
                logger.warning(f"序列化会员产品失败: product_code={product_code}, error={e}")
                # 跳过失败的产品，继续处理其他产品
                continue
        
        return serialized_products 