"""
订阅服务层单元测试 - test_subscriptions_service.py
对 app/services/subscriptions_service.py 中的 SubscriptionsService 类进行详细的、隔离的单元测试。
使用 mocker fixture 模拟所有外部依赖。
"""

import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock
from faker import Faker
from decimal import Decimal
from datetime import datetime, timedelta

from sqlalchemy.exc import IntegrityError

from app.services.subscriptions_service import (
    SubscriptionsService,
    ProductNotFoundError,
    PaymentFailedError,
    ActiveSubscriptionExistsError,
    SubscriptionOwnershipError,
    SubscriptionUpdateForbiddenError
)
from app.schemas.users import (
    UserMembershipResponse, UserMembershipCreate, UserMembershipUpdate,
    SubscriptionCreateRequest, SubscriptionUpdateRequest
)
from app.models.users import User, UserMembership, MembershipStatus, MembershipProductStatus

fake = Faker()


class TestSubscriptionsService:
    """SubscriptionsService 测试类"""

    @pytest.fixture
    def mock_db_session(self):
        """Mock 数据库会话"""
        return AsyncMock()

    @pytest.fixture
    def subscriptions_service(self, mock_db_session):
        """创建订阅服务实例"""
        return SubscriptionsService(mock_db_session)

    @pytest.fixture
    def mock_user(self):
        """创建模拟的用户对象"""
        user = MagicMock()
        user.id = fake.random_int(min=1, max=10000)
        user.username = fake.user_name()
        user.email = fake.email()
        return user

    @pytest.fixture
    def mock_subscription_create_request(self):
        """创建订阅创建请求对象"""
        return SubscriptionCreateRequest(
            product_code=f"PROD_{uuid.uuid4().hex[:8].upper()}",
            payment_token=f"tok_visa_{fake.random_number(digits=10)}"
        )

    @pytest.fixture
    def mock_subscription_update_request(self):
        """创建订阅更新请求对象"""
        return SubscriptionUpdateRequest(
            is_auto_renew=fake.boolean()
        )

    @pytest.fixture
    def mock_membership_product(self):
        """创建模拟的会员产品对象"""
        product = MagicMock()
        product.code = f"PROD_{uuid.uuid4().hex[:8].upper()}"
        product.name = fake.catch_phrase()
        product.price = Decimal(str(fake.random_number(digits=2)))
        product.level = fake.random_int(min=1, max=5)
        product.duration_unit = "month"
        product.duration_value = fake.random_int(min=1, max=12)
        product.status = MembershipProductStatus.ACTIVE
        return product

    @pytest.fixture
    def mock_user_membership(self):
        """创建模拟的用户订阅对象"""
        membership = MagicMock()
        membership.id = fake.random_int(min=1, max=10000)
        membership.public_id = fake.uuid4()
        membership.user_id = fake.random_int(min=1, max=10000)
        membership.product_code = f"PROD_{uuid.uuid4().hex[:8].upper()}"
        membership.transaction_id = f"txn_{uuid.uuid4().hex[:16]}"
        membership.level = fake.random_int(min=1, max=5)
        membership.status = MembershipStatus.ACTIVE
        membership.is_auto_renew = True
        membership.start_date = datetime.now()
        membership.expires_at = datetime.now() + timedelta(days=30)
        return membership

    # ========================================================================
    # 测试 get_user_subscriptions 方法
    # ========================================================================

    @pytest.mark.asyncio
    async def test_get_user_subscriptions_success(self, subscriptions_service, mocker):
        """测试成功获取用户订阅列表"""
        # Arrange
        user_id = fake.random_int(min=1, max=10000)
        page = 1
        size = 10
        
        # 创建模拟的订阅列表
        mock_memberships = []
        for _ in range(3):
            membership = MagicMock()
            membership.id = fake.random_int(min=1, max=10000)
            membership.user_id = user_id
            membership.product_code = f"PROD_{uuid.uuid4().hex[:8].upper()}"
            mock_memberships.append(membership)
        
        # Mock CRUD 方法
        mock_get_multi = mocker.patch('app.crud.crud_user_membership.get_multi_by_user_id')
        mock_get_multi.return_value = mock_memberships
        
        # Mock Pydantic 序列化
        mock_response_list = []
        for membership in mock_memberships:
            mock_response = MagicMock()
            mock_response_list.append(mock_response)
        
        mock_model_validate = mocker.patch('app.schemas.users.UserMembershipResponse.model_validate')
        mock_model_validate.side_effect = mock_response_list

        # Act
        result = await subscriptions_service.get_user_subscriptions(user_id, page, size)

        # Assert
        assert isinstance(result, dict)
        assert "items" in result
        assert "total" in result
        assert "page" in result
        assert "size" in result
        assert len(result["items"]) == 3
        assert result["total"] == 3
        assert result["page"] == page
        assert result["size"] == size
        
        # 验证 CRUD 方法被正确调用
        expected_skip = (page - 1) * size
        mock_get_multi.assert_called_once_with(
            subscriptions_service.db, user_id=user_id, skip=expected_skip, limit=size
        )

    # ========================================================================
    # 测试 create_new_subscription 方法
    # ========================================================================

    @pytest.mark.asyncio
    async def test_create_new_subscription_success(self, subscriptions_service, mock_user, mock_subscription_create_request, mock_membership_product, mocker):
        """测试成功创建新订阅"""
        # Arrange
        # 确保请求中的产品代码与模拟产品匹配
        mock_subscription_create_request.product_code = mock_membership_product.code
        
        # Mock CRUD 方法
        mock_get_multi_active = mocker.patch('app.crud.crud_membership_product.get_multi_active')
        mock_get_multi_active.return_value = [mock_membership_product]
        
        # Mock 支付方法
        mock_payment_result = {"success": True, "transaction_id": f"txn_{uuid.uuid4().hex[:16]}"}
        mock_simulate_payment = mocker.patch.object(subscriptions_service, '_simulate_payment')
        mock_simulate_payment.return_value = mock_payment_result
        
        # Mock 时间计算方法
        mock_expiry_date = datetime.now() + timedelta(days=30)
        mock_calculate_expiry = mocker.patch.object(subscriptions_service, '_calculate_expiry_date')
        mock_calculate_expiry.return_value = mock_expiry_date
        
        # Mock CRUD 创建方法
        mock_new_membership = MagicMock()
        mock_new_membership.id = fake.random_int(min=1, max=10000)
        mock_create = mocker.patch('app.crud.crud_user_membership.create')
        mock_create.return_value = mock_new_membership

        # Act
        result = await subscriptions_service.create_new_subscription(mock_user, mock_subscription_create_request)

        # Assert
        assert result == mock_new_membership
        
        # 验证各个方法被正确调用
        mock_get_multi_active.assert_called_once_with(subscriptions_service.db)
        mock_simulate_payment.assert_called_once_with(
            mock_subscription_create_request.payment_token, 
            float(mock_membership_product.price)
        )
        mock_calculate_expiry.assert_called_once_with(
            mock_membership_product.duration_unit,
            mock_membership_product.duration_value
        )
        mock_create.assert_called_once()
        
        # 验证传递给 create 的数据
        call_args = mock_create.call_args
        obj_in = call_args[1]['obj_in']  # 从关键字参数获取
        assert obj_in.user_id == mock_user.id
        assert obj_in.product_code == mock_membership_product.code
        assert obj_in.transaction_id == mock_payment_result["transaction_id"]
        assert obj_in.level == mock_membership_product.level
        assert obj_in.status == MembershipStatus.ACTIVE
        assert obj_in.is_auto_renew == True

    @pytest.mark.asyncio
    async def test_create_new_subscription_fails_if_product_not_found(self, subscriptions_service, mock_user, mock_subscription_create_request, mocker):
        """测试产品不存在时创建订阅失败"""
        # Arrange
        # Mock CRUD 方法返回空列表
        mock_get_multi_active = mocker.patch('app.crud.crud_membership_product.get_multi_active')
        mock_get_multi_active.return_value = []

        # Act & Assert
        with pytest.raises(ProductNotFoundError) as exc_info:
            await subscriptions_service.create_new_subscription(mock_user, mock_subscription_create_request)
        
        # 验证异常信息
        assert mock_subscription_create_request.product_code in str(exc_info.value)
        mock_get_multi_active.assert_called_once_with(subscriptions_service.db)

    @pytest.mark.asyncio
    async def test_create_new_subscription_fails_if_payment_fails(self, subscriptions_service, mock_user, mock_subscription_create_request, mock_membership_product, mocker):
        """测试支付失败时创建订阅失败"""
        # Arrange
        # 确保请求中的产品代码与模拟产品匹配
        mock_subscription_create_request.product_code = mock_membership_product.code
        
        # Mock CRUD 方法
        mock_get_multi_active = mocker.patch('app.crud.crud_membership_product.get_multi_active')
        mock_get_multi_active.return_value = [mock_membership_product]
        
        # Mock 支付失败
        mock_payment_result = {"success": False, "error": "支付令牌无效"}
        mock_simulate_payment = mocker.patch.object(subscriptions_service, '_simulate_payment')
        mock_simulate_payment.return_value = mock_payment_result

        # Act & Assert
        with pytest.raises(PaymentFailedError) as exc_info:
            await subscriptions_service.create_new_subscription(mock_user, mock_subscription_create_request)
        
        # 验证异常信息
        assert "支付令牌无效" in str(exc_info.value)
        mock_simulate_payment.assert_called_once_with(
            mock_subscription_create_request.payment_token,
            float(mock_membership_product.price)
        )

    @pytest.mark.asyncio
    async def test_create_new_subscription_fails_if_already_active(self, subscriptions_service, mock_user, mock_subscription_create_request, mock_membership_product, mocker):
        """测试用户已有有效订阅时创建订阅失败"""
        # Arrange
        # 确保请求中的产品代码与模拟产品匹配
        mock_subscription_create_request.product_code = mock_membership_product.code
        
        # Mock CRUD 方法
        mock_get_multi_active = mocker.patch('app.crud.crud_membership_product.get_multi_active')
        mock_get_multi_active.return_value = [mock_membership_product]
        
        # Mock 支付成功
        mock_payment_result = {"success": True, "transaction_id": f"txn_{uuid.uuid4().hex[:16]}"}
        mock_simulate_payment = mocker.patch.object(subscriptions_service, '_simulate_payment')
        mock_simulate_payment.return_value = mock_payment_result
        
        # Mock 时间计算方法
        mock_expiry_date = datetime.now() + timedelta(days=30)
        mock_calculate_expiry = mocker.patch.object(subscriptions_service, '_calculate_expiry_date')
        mock_calculate_expiry.return_value = mock_expiry_date
        
        # Mock CRUD 创建方法抛出 IntegrityError
        mock_create = mocker.patch('app.crud.crud_user_membership.create')
        mock_create.side_effect = IntegrityError("statement", "params", "orig")

        # Act & Assert
        with pytest.raises(ActiveSubscriptionExistsError):
            await subscriptions_service.create_new_subscription(mock_user, mock_subscription_create_request)
        
        # 验证 create 方法被调用了
        mock_create.assert_called_once()

    # ========================================================================
    # 测试 update_user_subscription 方法
    # ========================================================================

    @pytest.mark.asyncio
    async def test_update_user_subscription_success(self, subscriptions_service, mock_user, mock_subscription_update_request, mock_user_membership, mocker):
        """测试成功更新用户订阅"""
        # Arrange
        subscription_uuid = uuid.uuid4()
        
        # 确保订阅状态为 ACTIVE (允许修改)
        mock_user_membership.status = MembershipStatus.ACTIVE
        
        # Mock CRUD 查询方法
        mock_get_by_uuid = mocker.patch('app.crud.crud_user_membership.get_by_uuid_and_user_id')
        mock_get_by_uuid.return_value = mock_user_membership
        
        # Mock CRUD 更新方法
        mock_updated_membership = MagicMock()
        mock_update = mocker.patch('app.crud.crud_user_membership.update')
        mock_update.return_value = mock_updated_membership

        # Act
        result = await subscriptions_service.update_user_subscription(
            mock_user, subscription_uuid, mock_subscription_update_request
        )

        # Assert
        assert result == mock_updated_membership
        
        # 验证查询方法被正确调用
        mock_get_by_uuid.assert_called_once_with(
            subscriptions_service.db, uuid=subscription_uuid, user_id=mock_user.id
        )
        
        # 验证更新方法被正确调用
        mock_update.assert_called_once()
        call_args = mock_update.call_args
        assert call_args[1]['db_obj'] == mock_user_membership
        
        # 验证更新数据
        obj_in = call_args[1]['obj_in']
        assert obj_in.is_auto_renew == mock_subscription_update_request.is_auto_renew

    @pytest.mark.asyncio
    async def test_update_user_subscription_fails_if_not_owner(self, subscriptions_service, mock_user, mock_subscription_update_request, mocker):
        """测试非订阅所有者时更新订阅失败"""
        # Arrange
        subscription_uuid = uuid.uuid4()
        
        # Mock CRUD 查询方法返回 None (找不到或不属于该用户)
        mock_get_by_uuid = mocker.patch('app.crud.crud_user_membership.get_by_uuid_and_user_id')
        mock_get_by_uuid.return_value = None

        # Act & Assert
        with pytest.raises(SubscriptionOwnershipError) as exc_info:
            await subscriptions_service.update_user_subscription(
                mock_user, subscription_uuid, mock_subscription_update_request
            )
        
        # 验证异常信息包含 subscription_uuid
        assert str(subscription_uuid) in str(exc_info.value)
        mock_get_by_uuid.assert_called_once_with(
            subscriptions_service.db, uuid=subscription_uuid, user_id=mock_user.id
        )

    @pytest.mark.asyncio
    async def test_update_user_subscription_fails_if_expired(self, subscriptions_service, mock_user, mock_subscription_update_request, mock_user_membership, mocker):
        """测试订阅已过期时更新订阅失败"""
        # Arrange
        subscription_uuid = uuid.uuid4()
        
        # 设置订阅状态为 EXPIRED
        mock_user_membership.status = MembershipStatus.EXPIRED
        
        # Mock CRUD 查询方法
        mock_get_by_uuid = mocker.patch('app.crud.crud_user_membership.get_by_uuid_and_user_id')
        mock_get_by_uuid.return_value = mock_user_membership

        # Act & Assert
        with pytest.raises(SubscriptionUpdateForbiddenError) as exc_info:
            await subscriptions_service.update_user_subscription(
                mock_user, subscription_uuid, mock_subscription_update_request
            )
        
        # 验证异常信息包含状态信息
        assert MembershipStatus.EXPIRED.value in str(exc_info.value)
        mock_get_by_uuid.assert_called_once_with(
            subscriptions_service.db, uuid=subscription_uuid, user_id=mock_user.id
        )

    # ========================================================================
    # 测试内部辅助方法
    # ========================================================================

    def test_simulate_payment_success(self, subscriptions_service):
        """测试支付模拟成功"""
        # Arrange
        payment_token = "tok_visa_1234567890"
        amount = 99.99

        # Act
        result = subscriptions_service._simulate_payment(payment_token, amount)

        # Assert
        assert result["success"] == True
        assert "transaction_id" in result
        assert result["transaction_id"].startswith("txn_")
        assert payment_token[-4:] in result["transaction_id"]

    def test_simulate_payment_invalid_token(self, subscriptions_service):
        """测试无效支付令牌"""
        # Arrange
        payment_token = "tok_invalid_1234567890"
        amount = 99.99

        # Act
        result = subscriptions_service._simulate_payment(payment_token, amount)

        # Assert
        assert result["success"] == False
        assert "支付令牌无效" in result["error"]

    def test_simulate_payment_invalid_amount(self, subscriptions_service):
        """测试无效支付金额"""
        # Arrange
        payment_token = "tok_visa_1234567890"
        amount = 0

        # Act
        result = subscriptions_service._simulate_payment(payment_token, amount)

        # Assert
        assert result["success"] == False
        assert "支付金额无效" in result["error"]

    def test_calculate_expiry_date_month(self, subscriptions_service):
        """测试计算月度过期时间"""
        # Arrange
        duration_unit = "month"
        duration_value = 1

        # Act
        result = subscriptions_service._calculate_expiry_date(duration_unit, duration_value)

        # Assert
        assert isinstance(result, datetime)
        # 简化验证：检查时间差大约是30天
        now = datetime.now()
        diff = result - now
        assert 29 <= diff.days <= 31

    def test_calculate_expiry_date_year(self, subscriptions_service):
        """测试计算年度过期时间"""
        # Arrange
        duration_unit = "year"
        duration_value = 1

        # Act
        result = subscriptions_service._calculate_expiry_date(duration_unit, duration_value)

        # Assert
        assert isinstance(result, datetime)
        # 简化验证：检查时间差大约是365天
        now = datetime.now()
        diff = result - now
        assert 364 <= diff.days <= 366

    def test_calculate_expiry_date_default(self, subscriptions_service):
        """测试计算默认过期时间（按天计算）"""
        # Arrange
        duration_unit = "unknown"  # 不支持的单位，应该按天计算
        duration_value = 7

        # Act
        result = subscriptions_service._calculate_expiry_date(duration_unit, duration_value)

        # Assert
        assert isinstance(result, datetime)
        # 验证时间差是7天
        now = datetime.now()
        diff = result - now
        assert 6 <= diff.days <= 8  # 允许少量误差 