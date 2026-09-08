
### **最终版：高效 AI 测试代码生成提示词 (针对 `MembershipProductsService` 的单元测试)**

**(您可以直接复制下面这份完整、修正后的提示词用于生成测试代码)**

#### **1. 角色定义 (Role Definition)**

You are a Senior Python Backend Engineer specializing in automated testing. You are an expert in using `pytest` with `pytest-asyncio` and mocking frameworks like `pytest-mock`. Your task is to write a robust **unit test suite** for the provided `MembershipProductsService` class.

#### **2. 任务目标 (Task Objective)**

Your goal is to generate the complete code for **one new test file**: `tests/test_membership_products_service.py`.

#### **3. 核心上下文信息 (Core Context Information)**

**3.1. Testing Strategy**
* **For `Service` layer (`test_membership_products_service.py`)**: Test thoroughly using **mocking**. All external dependencies (like `crud_membership_product` functions) **must be mocked** to test the `MembershipProductsService` logic in complete isolation.

**3.2. 被测试代码 (Code to be Tested)**
* `@app/services/membership_products_service.py`
```
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
```

**3.3. 依赖的上下文 (Dependencies & Context)**
* `@tests/conftest.py` (**作为测试环境和 Fixture 的来源，不可修改**)
* `@app/models/users.py` (需要 `MembershipProduct` 模型和 `MembershipProductStatus` 枚举)
* `@app/schemas/users.py` (需要 `MembershipProductResponse` 等 Schemas)
* `@app/crud/crud_membership_product.py`

---
#### **4. 代码生成具体要求 (Specific Code Generation Instructions)**

##### **4.1. `tests/conftest.py` - 测试设置**
* **指令**: 你的任务**不包括**生成或修改 `conftest.py`。你**必须假设**它已存在并提供 `db_session` fixture。

##### **4.2. 测试数据隔离 (Test Data Isolation)**
* **指令**: 所有测试用例在准备数据时，**必须**使用 `faker` 或 `uuid` 生成随机且唯一的 `product_code` 等字段，以防止测试间冲突。

##### **4.3. `tests/test_services/test_membership_products_service.py` - Service层单元测试**

* **文件名**: `tests/test_services/test_membership_products_service.py`
* **职责**: 对 `app/services/membership_products_service.py` 中的每个公共方法进行详细的、隔离的单元测试。
* **核心要求**: **必须使用 `mocker` fixture** 来模拟所有外部依赖。

* **需实现的测试用例**:

    1.  **`test_get_active_products_success_with_default_sort`**:
        * **准备 (Arrange)**:
            * a. 创建一个 `MembershipProductsService` 的实例 `product_service`，并为其注入一个 `AsyncMock` 作为 `db` 会话。
            * b. 创建一个包含多个模拟 `models.MembershipProduct` 对象的列表 `mock_products`。
            * c. Mock `crud_membership_product.get_multi_active` 方法，使其返回 `mock_products`。
        * **执行 (Act)**: 调用 `product_service.get_active_products(sort=None)`。
        * **断言 (Assert)**:
            * a. 断言 `crud_membership_product.get_multi_active` **被调用了一次**。
            * b. 验证 `get_multi_active` 被调用时的参数：`sort` 应为 `'sort_order'`，`direction` 应为 `'asc'`。
            * c. 断言返回的结果是一个列表，其长度与 `mock_products` 相同。
            * d. 断言返回列表中的每个元素都是 `schemas.MembershipProductResponse` 的实例。

    2.  **`test_get_active_products_success_with_custom_sort`**:
        * **准备 (Arrange)**:
            * a. 同上，创建 `product_service` 和 `mock_products`。
            * b. Mock `crud_membership_product.get_multi_active` 方法。
        * **执行 (Act)**: 调用 `product_service.get_active_products(sort="price:desc")`。
        * **断言 (Assert)**:
            * a. 断言 `crud_membership_product.get_multi_active` **被调用了一次**。
            * b. 验证 `get_multi_active` 被调用时的参数：`sort` 应为 `'price'`，`direction` 应为 `'desc'`。

    3.  **`test_get_active_products_handles_serialization_error`**:
        * **准备 (Arrange)**:
            * a. 创建 `product_service`。
            * b. 创建一个“损坏的”产品对象 `bad_product`，它缺少Pydantic模型序列化时所需的字段。
            * c. Mock `crud_membership_product.get_multi_active` 返回 `[good_product, bad_product]`。
        * **执行 (Act)**: 调用 `product_service.get_active_products(sort=None)`。
        * **断言 (Assert)**:
            * a. 断言返回的列表**长度为1**，只包含成功序列化的 `good_product`。
            * b. （可选）可以检查日志中是否记录了关于 `bad_product` 序列化失败的 `warning` 消息。

    4.  **`test_internal_parse_sort_parameter`**:
        * **说明**: 为内部辅助方法 `_parse_sort_parameter` 编写单元测试，以确保其逻辑正确。
        * **场景 1**: 测试传入 `None` 或无效字符串（如 `'price'`）时，返回 `('sort_order', 'asc')`。
        * **场景 2**: 测试传入 `'price:desc'` 时，返回 `('price', 'desc')`。
        * **场景 3**: 测试传入 `'name:invalid_direction'` 时，返回 `('name', 'asc')`。

#### **5. 最终交付 (Final Deliverable)**

Please generate the complete, runnable Python code for the following **one new file**:
1.  `tests/test_membership_products_service.py`