"""
会员产品服务层单元测试 - test_membership_products_service.py
对 app/services/membership_products_service.py 中的 MembershipProductsService 类进行详细的、隔离的单元测试。
使用 mocker fixture 模拟所有外部依赖。
"""

import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock
from faker import Faker
from decimal import Decimal

from app.services.membership_products_service import (
    MembershipProductsService,
    InvalidSortParameterError,
    ProductSerializationError
)
from app.schemas.users import MembershipProductResponse

fake = Faker()


class TestMembershipProductsService:
    """MembershipProductsService 测试类"""

    @pytest.fixture
    def mock_db_session(self):
        """Mock 数据库会话"""
        return AsyncMock()

    @pytest.fixture
    def product_service(self, mock_db_session):
        """创建 MembershipProductsService 实例"""
        return MembershipProductsService(db=mock_db_session)

    @pytest.fixture
    def mock_product(self):
        """创建模拟的会员产品对象"""
        product = MagicMock()
        product.code = f"PRODUCT_{uuid.uuid4().hex[:8].upper()}"
        product.name = fake.catch_phrase()
        product.description = fake.text(max_nb_chars=200)
        product.price = Decimal(str(fake.random_int(min=10, max=500)))
        product.level = fake.random_int(min=1, max=5)
        product.duration_unit = fake.random_element(elements=("month", "year"))
        product.duration_value = fake.random_int(min=1, max=12)
        product.sort_order = fake.random_int(min=1, max=100)
        product.status = "ACTIVE"
        product.payment_gateway_price_id = f"price_{uuid.uuid4().hex[:16]}"
        product.created_at = fake.date_time()
        product.updated_at = fake.date_time()
        return product

    @pytest.fixture
    def mock_products_list(self, mock_product):
        """创建模拟的产品列表"""
        products = []
        for _ in range(3):
            product = MagicMock()
            product.code = f"PRODUCT_{uuid.uuid4().hex[:8].upper()}"
            product.name = fake.catch_phrase()
            product.description = fake.text(max_nb_chars=200)
            product.price = Decimal(str(fake.random_int(min=10, max=500)))
            product.level = fake.random_int(min=1, max=5)
            product.duration_unit = fake.random_element(elements=("month", "year"))
            product.duration_value = fake.random_int(min=1, max=12)
            product.sort_order = fake.random_int(min=1, max=100)
            product.status = "ACTIVE"
            product.payment_gateway_price_id = f"price_{uuid.uuid4().hex[:16]}"
            product.created_at = fake.date_time()
            product.updated_at = fake.date_time()
            products.append(product)
        return products

    # ========================================================================
    # get_active_products 方法测试
    # ========================================================================

    @pytest.mark.asyncio
    async def test_get_active_products_success_with_default_sort(self, product_service, mock_products_list, mocker):
        """测试使用默认排序获取活跃产品成功"""
        # Arrange
        mock_crud_get_multi_active = mocker.patch('app.crud.crud_membership_product.get_multi_active', return_value=mock_products_list)

        # Act
        result = await product_service.get_active_products(sort=None)

        # Assert
        # 验证 CRUD 方法被调用一次
        mock_crud_get_multi_active.assert_called_once()
        
        # 验证调用参数
        call_args = mock_crud_get_multi_active.call_args
        assert call_args[0][0] == product_service.db  # 第一个参数是 db
        assert call_args[1]['sort'] == 'sort_order'   # sort 参数
        assert call_args[1]['direction'] == 'asc'     # direction 参数
        
        # 验证返回结果
        assert isinstance(result, list)
        assert len(result) == len(mock_products_list)
        
        # 验证每个元素都是字典类型（来自 model_dump()）
        for item in result:
            assert isinstance(item, dict)

    @pytest.mark.asyncio
    async def test_get_active_products_success_with_custom_sort(self, product_service, mock_products_list, mocker):
        """测试使用自定义排序获取活跃产品成功"""
        # Arrange
        mock_crud_get_multi_active = mocker.patch('app.crud.crud_membership_product.get_multi_active', return_value=mock_products_list)

        # Act
        result = await product_service.get_active_products(sort="price:desc")

        # Assert
        # 验证 CRUD 方法被调用一次
        mock_crud_get_multi_active.assert_called_once()
        
        # 验证调用参数
        call_args = mock_crud_get_multi_active.call_args
        assert call_args[0][0] == product_service.db  # 第一个参数是 db
        assert call_args[1]['sort'] == 'price'        # sort 参数
        assert call_args[1]['direction'] == 'desc'    # direction 参数
        
        # 验证返回结果
        assert isinstance(result, list)
        assert len(result) == len(mock_products_list)

    @pytest.mark.asyncio
    async def test_get_active_products_handles_serialization_error(self, product_service, mocker):
        """测试处理序列化错误"""
        # Arrange
        # 创建一个正常的产品
        good_product = MagicMock()
        good_product.code = f"GOOD_PRODUCT_{uuid.uuid4().hex[:8].upper()}"
        good_product.name = fake.catch_phrase()
        good_product.description = fake.text(max_nb_chars=200)
        good_product.price = Decimal(str(fake.random_int(min=10, max=500)))
        good_product.level = fake.random_int(min=1, max=5)
        good_product.duration_unit = "month"
        good_product.duration_value = 1
        good_product.sort_order = 1
        good_product.status = "ACTIVE"
        good_product.payment_gateway_price_id = f"price_{uuid.uuid4().hex[:16]}"
        good_product.created_at = fake.date_time()
        good_product.updated_at = fake.date_time()
        
        # 创建一个"损坏的"产品（缺少必要字段）
        bad_product = MagicMock()
        bad_product.code = f"BAD_PRODUCT_{uuid.uuid4().hex[:8].upper()}"
        # 故意不设置其他必要字段，导致序列化失败
        
        mock_products = [good_product, bad_product]
        mock_crud_get_multi_active = mocker.patch('app.crud.crud_membership_product.get_multi_active', return_value=mock_products)
        
        # Mock MembershipProductResponse.model_validate 
        # 让 good_product 成功序列化，bad_product 失败
        def side_effect_model_validate(product):
            if product == good_product:
                # 返回一个模拟的成功响应
                mock_response = MagicMock()
                mock_response.model_dump.return_value = {
                    "code": good_product.code,
                    "name": good_product.name,
                    "price": str(good_product.price)
                }
                return mock_response
            else:
                # 对于 bad_product，抛出异常
                raise ValueError("Missing required field")
        
        mock_model_validate = mocker.patch('app.schemas.users.MembershipProductResponse.model_validate', side_effect=side_effect_model_validate)
        mock_logger = mocker.patch('app.services.membership_products_service.logger')

        # Act
        result = await product_service.get_active_products(sort=None)

        # Assert
        # 验证只返回了成功序列化的产品
        assert isinstance(result, list)
        assert len(result) == 1  # 只有 good_product 被成功处理
        
        # 验证日志记录了序列化失败
        mock_logger.warning.assert_called()
        warning_call = mock_logger.warning.call_args[0][0]
        assert "序列化会员产品失败" in warning_call
        assert bad_product.code in warning_call

    @pytest.mark.asyncio
    async def test_get_active_products_handles_crud_exception(self, product_service, mocker):
        """测试处理 CRUD 层异常"""
        # Arrange
        mock_crud_get_multi_active = mocker.patch('app.crud.crud_membership_product.get_multi_active', side_effect=Exception("Database error"))
        mock_logger = mocker.patch('app.services.membership_products_service.logger')

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            await product_service.get_active_products(sort=None)
        
        assert "Database error" in str(exc_info.value)
        mock_logger.error.assert_called()

    # ========================================================================
    # _parse_sort_parameter 内部方法测试
    # ========================================================================

    def test_internal_parse_sort_parameter_with_none(self, product_service):
        """测试解析排序参数 - None 输入"""
        # Act
        sort_field, sort_direction = product_service._parse_sort_parameter(None)
        
        # Assert
        assert sort_field == "sort_order"
        assert sort_direction == "asc"

    def test_internal_parse_sort_parameter_with_invalid_string(self, product_service):
        """测试解析排序参数 - 无效字符串输入"""
        # Act
        sort_field, sort_direction = product_service._parse_sort_parameter("price")
        
        # Assert
        assert sort_field == "sort_order"
        assert sort_direction == "asc"

    def test_internal_parse_sort_parameter_with_valid_input(self, product_service):
        """测试解析排序参数 - 有效输入"""
        # Act
        sort_field, sort_direction = product_service._parse_sort_parameter("price:desc")
        
        # Assert
        assert sort_field == "price"
        assert sort_direction == "desc"

    def test_internal_parse_sort_parameter_with_invalid_direction(self, product_service, mocker):
        """测试解析排序参数 - 无效排序方向"""
        # Arrange
        mock_logger = mocker.patch('app.services.membership_products_service.logger')
        
        # Act
        sort_field, sort_direction = product_service._parse_sort_parameter("name:invalid_direction")
        
        # Assert
        assert sort_field == "name"
        assert sort_direction == "asc"  # 应该重置为默认值
        mock_logger.warning.assert_called()

    def test_internal_parse_sort_parameter_with_multiple_colons(self, product_service, mocker):
        """测试解析排序参数 - 多个冒号"""
        # Arrange
        mock_logger = mocker.patch('app.services.membership_products_service.logger')
        
        # Act
        sort_field, sort_direction = product_service._parse_sort_parameter("field:asc:extra")
        
        # Assert
        assert sort_field == "sort_order"
        assert sort_direction == "asc"
        mock_logger.warning.assert_called()

    def test_internal_parse_sort_parameter_with_empty_string(self, product_service):
        """测试解析排序参数 - 空字符串"""
        # Act
        sort_field, sort_direction = product_service._parse_sort_parameter("")
        
        # Assert
        assert sort_field == "sort_order"
        assert sort_direction == "asc"

    def test_internal_parse_sort_parameter_with_whitespace(self, product_service):
        """测试解析排序参数 - 包含空格的输入"""
        # Act
        sort_field, sort_direction = product_service._parse_sort_parameter("  price  :  DESC  ")
        
        # Assert
        assert sort_field == "price"
        assert sort_direction == "desc"  # 应该被转换为小写

    # ========================================================================
    # _serialize_products 内部方法测试
    # ========================================================================

    def test_internal_serialize_products_success(self, product_service, mock_products_list, mocker):
        """测试序列化产品列表成功"""
        # Arrange
        mock_model_validate = mocker.patch('app.schemas.users.MembershipProductResponse.model_validate')
        mock_responses = []
        for i, product in enumerate(mock_products_list):
            mock_response = MagicMock()
            mock_response.model_dump.return_value = {"code": product.code, "name": product.name}
            mock_responses.append(mock_response)
        
        mock_model_validate.side_effect = mock_responses

        # Act
        result = product_service._serialize_products(mock_products_list)

        # Assert
        assert len(result) == len(mock_products_list)
        assert mock_model_validate.call_count == len(mock_products_list)
        
        for i, product in enumerate(mock_products_list):
            mock_model_validate.assert_any_call(product)

    def test_internal_serialize_products_with_partial_failure(self, product_service, mocker):
        """测试序列化产品列表部分失败"""
        # Arrange
        good_product = MagicMock()
        good_product.code = "GOOD_PRODUCT"
        
        bad_product = MagicMock()
        bad_product.code = "BAD_PRODUCT"
        
        products = [good_product, bad_product]
        
        def side_effect_model_validate(product):
            if product == good_product:
                mock_response = MagicMock()
                return mock_response
            else:
                raise ValueError("Serialization failed")
        
        mock_model_validate = mocker.patch('app.schemas.users.MembershipProductResponse.model_validate', side_effect=side_effect_model_validate)
        mock_logger = mocker.patch('app.services.membership_products_service.logger')

        # Act
        result = product_service._serialize_products(products)

        # Assert
        assert len(result) == 1  # 只有 good_product 成功
        mock_logger.warning.assert_called()
        warning_call = mock_logger.warning.call_args[0][0]
        assert "序列化会员产品失败" in warning_call
        assert "BAD_PRODUCT" in warning_call

    def test_internal_serialize_products_empty_list(self, product_service):
        """测试序列化空产品列表"""
        # Act
        result = product_service._serialize_products([])
        
        # Assert
        assert result == []

    def test_internal_serialize_products_product_without_code(self, product_service, mocker):
        """测试序列化没有 code 属性的产品"""
        # Arrange
        product_without_code = MagicMock()
        del product_without_code.code  # 删除 code 属性
        
        mock_model_validate = mocker.patch('app.schemas.users.MembershipProductResponse.model_validate', side_effect=ValueError("Missing code"))
        mock_logger = mocker.patch('app.services.membership_products_service.logger')

        # Act
        result = product_service._serialize_products([product_without_code])

        # Assert
        assert len(result) == 0
        mock_logger.warning.assert_called()
        warning_call = mock_logger.warning.call_args[0][0]
        assert "序列化会员产品失败" in warning_call
        assert "unknown" in warning_call  # 应该使用 'unknown' 作为默认的 product_code 