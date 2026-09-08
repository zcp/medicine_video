"""
AdminProductsService 单元测试
对 app.services.admin_products_service.AdminProductsService 的所有公共方法进行详细的、隔离的单元测试
"""
import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.exc import IntegrityError

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.admin_products_service import (
    AdminProductsService,
    ProductCodeExistsError,
    ProductNotFoundError,
    ProductInUseError
)
from app.schemas.users import MembershipProductCreate, MembershipProductUpdate
from app.models.users import MembershipProduct, MembershipProductStatus


# ============================================================================
# 测试用例
# ============================================================================

class TestAdminProductsService:
    """AdminProductsService 测试类"""

    @pytest.fixture
    def mock_db_session(self):
        """模拟数据库会话"""
        return AsyncMock(spec=AsyncSession)

    @pytest.fixture
    def product_service(self, mock_db_session):
        """AdminProductsService 实例 fixture"""
        return AdminProductsService(db=mock_db_session)

    @pytest.fixture
    def mock_product_create(self):
        """创建模拟产品创建请求"""
        product_code = f"TEST_{uuid.uuid4().hex[:8].upper()}"
        return MembershipProductCreate(
            code=product_code,
            name=f"测试产品_{uuid.uuid4().hex[:6]}",
            description="测试产品描述",
            price=Decimal("99.99"),
            level=1,
            duration_unit="month",
            duration_value=1,
            status=MembershipProductStatus.ACTIVE,
            sort_order=1
        )

    @pytest.fixture
    def mock_product_update(self):
        """创建模拟产品更新请求"""
        return MembershipProductUpdate(
            name=f"更新产品_{uuid.uuid4().hex[:6]}",
            description="更新后的产品描述",
            price=Decimal("199.99"),
            status=MembershipProductStatus.INACTIVE
        )

    @pytest.fixture
    def mock_product(self):
        """创建模拟产品对象"""
        mock_product = MagicMock(spec=MembershipProduct)
        mock_product.code = f"PROD_{uuid.uuid4().hex[:8].upper()}"
        mock_product.name = f"产品_{uuid.uuid4().hex[:6]}"
        mock_product.description = "产品描述"
        mock_product.price = Decimal("99.99")
        mock_product.level = 1
        mock_product.duration_unit = "month"
        mock_product.duration_value = 1
        mock_product.status = MembershipProductStatus.ACTIVE
        mock_product.sort_order = 1
        return mock_product

    # ========================================================================
    # create_product 方法测试
    # ========================================================================

    async def test_create_product_success(self, product_service, mock_product_create, mocker):
        """
        测试成功创建产品
        
        准备: 模拟 crud_membership_product 的方法返回预期数据
        执行: 调用 create_product 方法
        断言: 验证 CRUD 方法被正确调用
        """
        # Arrange - 准备测试数据
        mock_new_product = MagicMock(spec=MembershipProduct)
        mock_new_product.code = mock_product_create.code
        mock_new_product.name = mock_product_create.name

        # Mock crud_membership_product 方法
        mock_get_by_code = mocker.patch(
            'app.services.admin_products_service.crud_membership_product.get_by_code'
        )
        mock_get_by_code.return_value = None  # 表示编码不存在

        mock_create = mocker.patch(
            'app.services.admin_products_service.crud_membership_product.create'
        )
        mock_create.return_value = mock_new_product

        # Act - 执行被测试方法
        result = await product_service.create_product(product_in=mock_product_create)

        # Assert - 验证结果
        # 验证 crud_membership_product.get_by_code 被正确调用
        mock_get_by_code.assert_called_once_with(
            product_service.db, code=mock_product_create.code
        )

        # 验证 crud_membership_product.create 被调用了一次
        mock_create.assert_called_once()
        
        # 验证传递给 create 的参数
        call_args = mock_create.call_args
        assert call_args[0][0] == product_service.db
        assert call_args[1]['obj_in'] == mock_product_create

        # 验证返回的是新创建的产品对象
        assert result == mock_new_product

    async def test_create_product_fails_if_code_exists(self, product_service, mock_product_create, mocker):
        """
        测试产品编码已存在时抛出 ProductCodeExistsError
        
        准备: Mock crud_membership_product.get_by_code 返回存在的产品
        执行与断言: 使用 pytest.raises 验证抛出正确的异常
        """
        # Arrange - 模拟编码已存在
        existing_product = MagicMock(spec=MembershipProduct)
        existing_product.code = mock_product_create.code

        mock_get_by_code = mocker.patch(
            'app.services.admin_products_service.crud_membership_product.get_by_code'
        )
        mock_get_by_code.return_value = existing_product

        # Act & Assert
        with pytest.raises(ProductCodeExistsError) as exc_info:
            await product_service.create_product(product_in=mock_product_create)

        # 验证异常信息
        assert "产品编码已存在" in str(exc_info.value)
        
        # 验证 crud_membership_product.get_by_code 被调用
        mock_get_by_code.assert_called_once_with(
            product_service.db, code=mock_product_create.code
        )

    # ========================================================================
    # list_products 方法测试
    # ========================================================================

    async def test_list_products_success(self, product_service, mocker):
        """
        测试成功列出产品列表
        
        准备: 模拟 crud_membership_product 的方法返回预期数据
        执行: 调用 list_products 方法
        断言: 验证调用参数和返回结果
        """
        # Arrange - 准备测试数据
        page = 1
        size = 10
        skip = (page - 1) * size
        total_count = 5

        # 创建模拟产品列表
        mock_products = []
        for i in range(3):
            mock_product = MagicMock(spec=MembershipProduct)
            mock_product.code = f"PROD_{uuid.uuid4().hex[:8].upper()}"
            mock_product.name = f"产品_{i+1}"
            mock_product.status = MembershipProductStatus.ACTIVE
            mock_products.append(mock_product)

        # Mock crud_membership_product 方法
        mock_count_all = mocker.patch(
            'app.services.admin_products_service.crud_membership_product.count_all'
        )
        mock_count_all.return_value = total_count

        mock_get_multi_all = mocker.patch(
            'app.services.admin_products_service.crud_membership_product.get_multi_all'
        )
        mock_get_multi_all.return_value = mock_products

        # Mock MembershipProductResponse.model_validate
        mock_product_response_validate = mocker.patch(
            'app.services.admin_products_service.MembershipProductResponse.model_validate'
        )
        mock_product_response_validate.side_effect = lambda product: {
            "code": product.code,
            "name": product.name,
            "status": product.status
        }

        # Act - 执行被测试方法
        result = await product_service.list_products(page=page, size=size)

        # Assert - 验证结果
        # 验证 crud_membership_product 方法被正确调用
        mock_count_all.assert_called_once_with(product_service.db)
        mock_get_multi_all.assert_called_once_with(
            product_service.db, skip=skip, limit=size
        )

        # 验证返回结果结构
        assert isinstance(result, dict)
        assert result["total"] == total_count
        assert result["page"] == page
        assert result["size"] == size
        assert len(result["items"]) == len(mock_products)

        # 验证 MembershipProductResponse.model_validate 被调用了正确的次数
        assert mock_product_response_validate.call_count == len(mock_products)

    async def test_list_products_with_status_filter(self, product_service, mocker):
        """
        测试带状态筛选的产品列表查询
        """
        # Arrange
        page = 1
        size = 10
        filter_status = MembershipProductStatus.ACTIVE
        
        # 创建包含不同状态的产品列表
        mock_products = []
        for i, status in enumerate([MembershipProductStatus.ACTIVE, MembershipProductStatus.DRAFT, MembershipProductStatus.ACTIVE]):
            mock_product = MagicMock(spec=MembershipProduct)
            mock_product.code = f"PROD_{uuid.uuid4().hex[:8].upper()}"
            mock_product.name = f"产品_{i+1}"
            mock_product.status = status
            mock_products.append(mock_product)

        # Mock crud_membership_product 方法
        mocker.patch(
            'app.services.admin_products_service.crud_membership_product.count_all',
            return_value=len(mock_products)
        )
        mocker.patch(
            'app.services.admin_products_service.crud_membership_product.get_multi_all',
            return_value=mock_products
        )

        # Mock MembershipProductResponse.model_validate
        mock_product_response_validate = mocker.patch(
            'app.services.admin_products_service.MembershipProductResponse.model_validate'
        )
        mock_product_response_validate.side_effect = lambda product: {
            "code": product.code,
            "name": product.name,
            "status": product.status
        }

        # Act
        result = await product_service.list_products(page=page, size=size, status=filter_status)

        # Assert - 应该只返回匹配状态的产品
        expected_active_count = sum(1 for p in mock_products if p.status == filter_status)
        assert result["total"] == expected_active_count
        assert len(result["items"]) == expected_active_count

    async def test_list_products_with_serialization_error(self, product_service, mocker):
        """
        测试列出产品时部分产品序列化失败的情况
        """
        # Arrange
        page = 1
        size = 10
        
        # 创建包含有问题产品的模拟列表
        mock_products = []
        for i in range(2):
            mock_product = MagicMock(spec=MembershipProduct)
            mock_product.code = f"PROD_{uuid.uuid4().hex[:8].upper()}"
            mock_product.name = f"产品_{i+1}"
            mock_product.status = MembershipProductStatus.ACTIVE
            mock_products.append(mock_product)

        # Mock crud_membership_product 方法
        mocker.patch(
            'app.services.admin_products_service.crud_membership_product.count_all',
            return_value=2
        )
        mocker.patch(
            'app.services.admin_products_service.crud_membership_product.get_multi_all',
            return_value=mock_products
        )

        # Mock MembershipProductResponse.model_validate - 第一个成功，第二个失败
        mock_product_response_validate = mocker.patch(
            'app.services.admin_products_service.MembershipProductResponse.model_validate'
        )
        mock_product_response_validate.side_effect = [
            {"code": "PROD1", "name": "产品1"},  # 第一个成功
            Exception("Serialization error")  # 第二个失败
        ]

        # Act
        result = await product_service.list_products(page=page, size=size)

        # Assert - 应该只返回成功序列化的产品
        assert result["total"] == 2  # 总数不变
        assert len(result["items"]) == 1  # 只有1个成功序列化的产品

    # ========================================================================
    # get_product 方法测试
    # ========================================================================

    async def test_get_product_success(self, product_service, mock_product, mocker):
        """
        测试成功获取产品详情
        
        准备: Mock crud_membership_product.get_by_code 返回产品对象
        执行: 调用 get_product 方法
        断言: 验证返回的对象与mock对象一致
        """
        # Arrange
        product_code = mock_product.code

        # Mock crud_membership_product.get_by_code
        mock_get_by_code = mocker.patch(
            'app.services.admin_products_service.crud_membership_product.get_by_code'
        )
        mock_get_by_code.return_value = mock_product

        # Act
        result = await product_service.get_product(product_code=product_code)

        # Assert
        # 验证 crud_membership_product.get_by_code 被正确调用
        mock_get_by_code.assert_called_once_with(
            product_service.db, code=product_code
        )

        # 验证返回的对象与模拟对象一致
        assert result == mock_product

    async def test_get_product_fails_if_not_found(self, product_service, mocker):
        """
        测试产品不存在时抛出 ProductNotFoundError
        
        准备: Mock crud_membership_product.get_by_code 返回 None
        执行与断言: 使用 pytest.raises 验证抛出正确的异常
        """
        # Arrange
        product_code = f"NONEXISTENT_{uuid.uuid4().hex[:8].upper()}"

        # Mock crud_membership_product.get_by_code 返回 None (产品不存在)
        mock_get_by_code = mocker.patch(
            'app.services.admin_products_service.crud_membership_product.get_by_code'
        )
        mock_get_by_code.return_value = None

        # Act & Assert
        with pytest.raises(ProductNotFoundError) as exc_info:
            await product_service.get_product(product_code=product_code)

        # 验证异常信息
        assert "会员产品不存在" in str(exc_info.value)
        
        # 验证 crud_membership_product.get_by_code 被调用
        mock_get_by_code.assert_called_once_with(
            product_service.db, code=product_code
        )

    # ========================================================================
    # update_product 方法测试
    # ========================================================================

    async def test_update_product_success(
        self, product_service, mock_product, mock_product_update, mocker
    ):
        """
        测试成功更新产品信息
        
        准备: 创建模拟产品对象和更新数据，模拟 crud_membership_product 方法
        执行: 调用 update_product 方法
        断言: 验证 crud_membership_product.update 被正确调用
        """
        # Arrange - 准备测试数据
        product_code = mock_product.code

        # 创建更新后的产品对象
        updated_product = MagicMock(spec=MembershipProduct)
        updated_product.code = mock_product.code
        updated_product.name = mock_product_update.name
        updated_product.description = mock_product_update.description
        updated_product.price = mock_product_update.price
        updated_product.status = mock_product_update.status

        # Mock crud_membership_product 方法
        mock_get_by_code = mocker.patch(
            'app.services.admin_products_service.crud_membership_product.get_by_code'
        )
        mock_get_by_code.return_value = mock_product

        mock_update = mocker.patch(
            'app.services.admin_products_service.crud_membership_product.update'
        )
        mock_update.return_value = updated_product

        # Act - 执行被测试方法
        result = await product_service.update_product(
            product_code=product_code, product_update=mock_product_update
        )

        # Assert - 验证结果
        # 验证 crud_membership_product.get_by_code 被正确调用
        mock_get_by_code.assert_called_once_with(
            product_service.db, code=product_code
        )

        # 验证 crud_membership_product.update 被调用了一次
        mock_update.assert_called_once()
        
        # 验证传递给 update 的参数
        call_args = mock_update.call_args
        assert call_args[0][0] == product_service.db
        assert call_args[1]['db_obj'] == mock_product
        assert call_args[1]['obj_in'] == mock_product_update

        # 验证返回的是更新后的产品对象
        assert result == updated_product

    async def test_update_product_fails_if_not_found(
        self, product_service, mock_product_update, mocker
    ):
        """
        测试更新不存在的产品时抛出 ProductNotFoundError
        """
        # Arrange
        product_code = f"NONEXISTENT_{uuid.uuid4().hex[:8].upper()}"

        # Mock crud_membership_product.get_by_code 返回 None (产品不存在)
        mock_get_by_code = mocker.patch(
            'app.services.admin_products_service.crud_membership_product.get_by_code'
        )
        mock_get_by_code.return_value = None

        # Act & Assert
        with pytest.raises(ProductNotFoundError) as exc_info:
            await product_service.update_product(
                product_code=product_code, product_update=mock_product_update
            )

        # 验证异常信息
        assert "会员产品不存在" in str(exc_info.value)
        
        # 验证 crud_membership_product.get_by_code 被调用
        mock_get_by_code.assert_called_once_with(
            product_service.db, code=product_code
        )

    # ========================================================================
    # delete_product 方法测试
    # ========================================================================

    async def test_delete_product_success(self, product_service, mock_product, mocker):
        """
        测试成功删除产品
        
        准备: Mock crud_membership_product.remove 返回已删除的产品对象
        执行: 调用 delete_product 方法
        断言: 验证 crud_membership_product.remove 被正确调用
        """
        # Arrange
        product_code = mock_product.code

        # Mock crud_membership_product.remove
        mock_remove = mocker.patch(
            'app.services.admin_products_service.crud_membership_product.remove'
        )
        mock_remove.return_value = mock_product

        # Act
        result = await product_service.delete_product(product_code=product_code)

        # Assert
        # 验证 crud_membership_product.remove 被以正确的参数调用了一次
        mock_remove.assert_called_once_with(
            product_service.db, code=product_code
        )

        # 验证返回的是被删除的产品对象
        assert result == mock_product

    async def test_delete_product_fails_if_not_found(self, product_service, mocker):
        """
        测试删除不存在的产品时抛出 ProductNotFoundError
        """
        # Arrange
        product_code = f"NONEXISTENT_{uuid.uuid4().hex[:8].upper()}"

        # Mock crud_membership_product.remove 返回 None (产品不存在)
        mock_remove = mocker.patch(
            'app.services.admin_products_service.crud_membership_product.remove'
        )
        mock_remove.return_value = None

        # Act & Assert
        with pytest.raises(ProductNotFoundError) as exc_info:
            await product_service.delete_product(product_code=product_code)

        # 验证异常信息
        assert "会员产品不存在" in str(exc_info.value)
        
        # 验证 crud_membership_product.remove 被调用
        mock_remove.assert_called_once_with(
            product_service.db, code=product_code
        )

    async def test_delete_product_fails_if_referenced(self, product_service, mocker):
        """
        测试删除被引用的产品时抛出 ProductInUseError
        
        准备: Mock crud_membership_product.remove 主动抛出 IntegrityError
        执行与断言: 使用 pytest.raises 验证抛出正确的异常
        """
        # Arrange
        product_code = f"REFERENCED_{uuid.uuid4().hex[:8].upper()}"

        # Mock crud_membership_product.remove 主动抛出 IntegrityError
        mock_remove = mocker.patch(
            'app.services.admin_products_service.crud_membership_product.remove'
        )
        mock_remove.side_effect = IntegrityError("foreign key constraint", None, None)

        # Act & Assert
        with pytest.raises(ProductInUseError) as exc_info:
            await product_service.delete_product(product_code=product_code)

        # 验证异常信息
        assert "无法删除仍被用户订阅引用的产品" in str(exc_info.value)
        
        # 验证 crud_membership_product.remove 被调用
        mock_remove.assert_called_once_with(
            product_service.db, code=product_code
        ) 