"""
管理员订阅服务层单元测试 - test_admin_subscriptions_service.py
对 app/services/admin_subscriptions_service.py 中的 AdminSubscriptionsService 类进行详细的、隔离的单元测试。
使用 mocker fixture 模拟所有外部依赖。
"""

import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock
from faker import Faker
from decimal import Decimal
from datetime import datetime, timedelta

from sqlalchemy.exc import IntegrityError

from app.services.admin_subscriptions_service import (
    AdminSubscriptionsService,
    TargetUserNotFoundError,
    ProductNotFoundError,
    ActiveSubscriptionExistsError,
    SubscriptionNotFoundError
)
from app.schemas.users import (
    UserMembershipResponse, UserMembershipCreate, UserMembershipUpdate,
    UserMembershipCreateAdmin
)
from app.models.users import User, UserMembership, MembershipStatus

fake = Faker()


class TestAdminSubscriptionsService:
    """AdminSubscriptionsService 测试类"""

    @pytest.fixture
    def mock_db_session(self):
        """Mock 数据库会话"""
        return AsyncMock()

    @pytest.fixture
    def admin_sub_service(self, mock_db_session):
        """创建管理员订阅服务实例"""
        return AdminSubscriptionsService(mock_db_session)

    @pytest.fixture
    def mock_target_user(self):
        """创建模拟的目标用户对象"""
        user = MagicMock()
        user.id = fake.random_int(min=1, max=10000)
        user.public_id = fake.uuid4()
        user.username = fake.user_name()
        user.email = fake.email()
        return user

    @pytest.fixture
    def mock_product(self):
        """创建模拟的会员产品对象"""
        product = MagicMock()
        product.code = f"PROD_{uuid.uuid4().hex[:8].upper()}"
        product.name = fake.catch_phrase()
        product.price = Decimal(str(fake.random_number(digits=2)))
        product.level = fake.random_int(min=1, max=5)
        product.duration_unit = "month"
        product.duration_value = fake.random_int(min=1, max=12)
        return product

    @pytest.fixture
    def mock_subscription(self):
        """创建模拟的用户订阅对象"""
        subscription = MagicMock()
        subscription.id = fake.random_int(min=1, max=10000)
        subscription.public_id = fake.uuid4()
        subscription.user_id = fake.random_int(min=1, max=10000)
        subscription.product_code = f"PROD_{uuid.uuid4().hex[:8].upper()}"
        subscription.transaction_id = f"txn_{uuid.uuid4().hex[:16]}"
        subscription.level = fake.random_int(min=1, max=5)
        subscription.status = MembershipStatus.ACTIVE
        subscription.is_auto_renew = False
        subscription.start_date = datetime.now()
        subscription.expires_at = datetime.now() + timedelta(days=30)
        subscription.admin_notes = fake.sentence()
        return subscription

    @pytest.fixture
    def sub_create_request(self):
        """创建订阅创建请求对象"""
        return UserMembershipCreateAdmin(
            product_code=f"PROD_{uuid.uuid4().hex[:8].upper()}",
            transaction_id=f"admin_txn_{uuid.uuid4().hex[:12]}",
            admin_notes=fake.sentence(),
            start_date=datetime.now(),
            expires_at=datetime.now() + timedelta(days=30)
        )

    @pytest.fixture
    def update_request(self):
        """创建订阅更新请求对象"""
        return UserMembershipUpdate(
            status=MembershipStatus.ACTIVE,
            is_auto_renew=fake.boolean(),
            admin_notes=fake.sentence(),
            expires_at=datetime.now() + timedelta(days=60)
        )

    # ========================================================================
    # 测试 get_subscriptions_by_user 方法
    # ========================================================================

    @pytest.mark.asyncio
    async def test_get_subscriptions_by_user_success(self, admin_sub_service, mock_target_user, mocker):
        """测试成功获取用户订阅列表"""
        # Arrange
        user_uuid = uuid.uuid4()
        page = 1
        size = 10
        
        # 创建模拟的订阅列表
        mock_memberships = []
        for _ in range(3):
            membership = MagicMock()
            membership.id = fake.random_int(min=1, max=10000)
            membership.user_id = mock_target_user.id
            membership.product_code = f"PROD_{uuid.uuid4().hex[:8].upper()}"
            mock_memberships.append(membership)
        
        # Mock CRUD 方法
        mock_get_by_uuid = mocker.patch('app.crud.crud_user.get_by_uuid')
        mock_get_by_uuid.return_value = mock_target_user
        
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
        result = await admin_sub_service.get_subscriptions_by_user(user_uuid, page, size)

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
        mock_get_by_uuid.assert_called_once_with(admin_sub_service.db, public_id=user_uuid)
        
        expected_skip = (page - 1) * size
        mock_get_multi.assert_called_once_with(
            admin_sub_service.db, user_id=mock_target_user.id, skip=expected_skip, limit=size
        )

    @pytest.mark.asyncio
    async def test_get_subscriptions_by_user_fails_if_user_not_found(self, admin_sub_service, mocker):
        """测试目标用户不存在时获取订阅失败"""
        # Arrange
        user_uuid = uuid.uuid4()
        page = 1
        size = 10
        
        # Mock CRUD 方法返回 None
        mock_get_by_uuid = mocker.patch('app.crud.crud_user.get_by_uuid')
        mock_get_by_uuid.return_value = None

        # Act & Assert
        with pytest.raises(TargetUserNotFoundError) as exc_info:
            await admin_sub_service.get_subscriptions_by_user(user_uuid, page, size)
        
        # 验证异常信息
        assert str(user_uuid) in str(exc_info.value)
        mock_get_by_uuid.assert_called_once_with(admin_sub_service.db, public_id=user_uuid)

    # ========================================================================
    # 测试 create_subscription_for_user 方法
    # ========================================================================

    @pytest.mark.asyncio
    async def test_create_subscription_for_user_success(self, admin_sub_service, mock_target_user, mock_product, sub_create_request, mocker):
        """测试成功为用户创建订阅"""
        # Arrange
        user_uuid = uuid.uuid4()
        
        # 确保请求中的产品代码与模拟产品匹配
        sub_create_request.product_code = mock_product.code
        
        # Mock CRUD 方法
        mock_get_user_by_uuid = mocker.patch('app.crud.crud_user.get_by_uuid')
        mock_get_user_by_uuid.return_value = mock_target_user
        
        mock_get_product_by_code = mocker.patch('app.crud.crud_membership_product.get_by_code')
        mock_get_product_by_code.return_value = mock_product
        
        # Mock CRUD 创建方法
        mock_new_membership = MagicMock()
        mock_new_membership.id = fake.random_int(min=1, max=10000)
        mock_create = mocker.patch('app.crud.crud_user_membership.create')
        mock_create.return_value = mock_new_membership

        # Act
        result = await admin_sub_service.create_subscription_for_user(user_uuid, sub_create_request)

        # Assert
        assert result == mock_new_membership
        
        # 验证各个方法被正确调用
        mock_get_user_by_uuid.assert_called_once_with(admin_sub_service.db, public_id=user_uuid)
        mock_get_product_by_code.assert_called_once_with(admin_sub_service.db, code=sub_create_request.product_code)
        mock_create.assert_called_once()
        
        # 验证传递给 create 的数据
        call_args = mock_create.call_args
        obj_in = call_args[1]['obj_in']  # 从关键字参数获取
        assert obj_in.user_id == mock_target_user.id
        assert obj_in.product_code == mock_product.code
        assert obj_in.transaction_id == sub_create_request.transaction_id
        assert obj_in.level == mock_product.level
        assert obj_in.status == MembershipStatus.ACTIVE
        assert obj_in.is_auto_renew == False  # 手动创建的订阅默认不自动续费
        assert obj_in.admin_notes == sub_create_request.admin_notes
        assert obj_in.start_date == sub_create_request.start_date
        assert obj_in.expires_at == sub_create_request.expires_at

    @pytest.mark.asyncio
    async def test_create_subscription_fails_if_target_user_not_found(self, admin_sub_service, sub_create_request, mocker):
        """测试目标用户不存在时创建订阅失败"""
        # Arrange
        user_uuid = uuid.uuid4()
        
        # Mock CRUD 方法返回 None
        mock_get_user_by_uuid = mocker.patch('app.crud.crud_user.get_by_uuid')
        mock_get_user_by_uuid.return_value = None

        # Act & Assert
        with pytest.raises(TargetUserNotFoundError) as exc_info:
            await admin_sub_service.create_subscription_for_user(user_uuid, sub_create_request)
        
        # 验证异常信息
        assert str(user_uuid) in str(exc_info.value)
        mock_get_user_by_uuid.assert_called_once_with(admin_sub_service.db, public_id=user_uuid)

    @pytest.mark.asyncio
    async def test_create_subscription_fails_if_product_not_found(self, admin_sub_service, mock_target_user, sub_create_request, mocker):
        """测试产品不存在时创建订阅失败"""
        # Arrange
        user_uuid = uuid.uuid4()
        
        # Mock CRUD 方法
        mock_get_user_by_uuid = mocker.patch('app.crud.crud_user.get_by_uuid')
        mock_get_user_by_uuid.return_value = mock_target_user
        
        # Mock 产品查询返回 None
        mock_get_product_by_code = mocker.patch('app.crud.crud_membership_product.get_by_code')
        mock_get_product_by_code.return_value = None

        # Act & Assert
        with pytest.raises(ProductNotFoundError) as exc_info:
            await admin_sub_service.create_subscription_for_user(user_uuid, sub_create_request)
        
        # 验证异常信息
        assert sub_create_request.product_code in str(exc_info.value)
        mock_get_product_by_code.assert_called_once_with(admin_sub_service.db, code=sub_create_request.product_code)

    @pytest.mark.asyncio
    async def test_create_subscription_fails_if_already_active(self, admin_sub_service, mock_target_user, mock_product, sub_create_request, mocker):
        """测试用户已有有效订阅时创建订阅失败"""
        # Arrange
        user_uuid = uuid.uuid4()
        
        # 确保请求中的产品代码与模拟产品匹配
        sub_create_request.product_code = mock_product.code
        
        # Mock CRUD 方法
        mock_get_user_by_uuid = mocker.patch('app.crud.crud_user.get_by_uuid')
        mock_get_user_by_uuid.return_value = mock_target_user
        
        mock_get_product_by_code = mocker.patch('app.crud.crud_membership_product.get_by_code')
        mock_get_product_by_code.return_value = mock_product
        
        # Mock CRUD 创建方法抛出 IntegrityError
        mock_create = mocker.patch('app.crud.crud_user_membership.create')
        mock_create.side_effect = IntegrityError("statement", "params", "orig")

        # Act & Assert
        with pytest.raises(ActiveSubscriptionExistsError):
            await admin_sub_service.create_subscription_for_user(user_uuid, sub_create_request)
        
        # 验证 create 方法被调用了
        mock_create.assert_called_once()

    # ========================================================================
    # 测试 update_subscription 方法
    # ========================================================================

    @pytest.mark.asyncio
    async def test_update_subscription_success(self, admin_sub_service, mock_subscription, update_request, mocker):
        """测试成功更新订阅"""
        # Arrange
        subscription_uuid = uuid.uuid4()
        
        # Mock CRUD 查询方法
        mock_get_by_uuid = mocker.patch('app.crud.crud_user_membership.get_by_uuid')
        mock_get_by_uuid.return_value = mock_subscription
        
        # Mock CRUD 更新方法
        mock_updated_subscription = MagicMock()
        mock_update = mocker.patch('app.crud.crud_user_membership.update')
        mock_update.return_value = mock_updated_subscription

        # Act
        result = await admin_sub_service.update_subscription(subscription_uuid, update_request)

        # Assert
        assert result == mock_updated_subscription
        
        # 验证查询方法被正确调用
        mock_get_by_uuid.assert_called_once_with(admin_sub_service.db, uuid=subscription_uuid)
        
        # 验证更新方法被正确调用
        mock_update.assert_called_once()
        call_args = mock_update.call_args
        assert call_args[1]['db_obj'] == mock_subscription
        assert call_args[1]['obj_in'] == update_request

    @pytest.mark.asyncio
    async def test_update_subscription_fails_if_not_found(self, admin_sub_service, update_request, mocker):
        """测试订阅记录不存在时更新订阅失败"""
        # Arrange
        subscription_uuid = uuid.uuid4()
        
        # Mock CRUD 查询方法返回 None
        mock_get_by_uuid = mocker.patch('app.crud.crud_user_membership.get_by_uuid')
        mock_get_by_uuid.return_value = None

        # Act & Assert
        with pytest.raises(SubscriptionNotFoundError) as exc_info:
            await admin_sub_service.update_subscription(subscription_uuid, update_request)
        
        # 验证异常信息包含 subscription_uuid
        assert str(subscription_uuid) in str(exc_info.value)
        mock_get_by_uuid.assert_called_once_with(admin_sub_service.db, uuid=subscription_uuid)

    # ========================================================================
    # 测试异常类
    # ========================================================================

    def test_target_user_not_found_error(self):
        """测试目标用户不存在异常"""
        user_uuid = str(uuid.uuid4())
        error = TargetUserNotFoundError(user_uuid)
        
        assert error.user_uuid == user_uuid
        assert user_uuid in str(error)
        assert "目标用户不存在" in str(error)

    def test_product_not_found_error(self):
        """测试产品不存在异常"""
        product_code = "PROD_TEST123"
        error = ProductNotFoundError(product_code)
        
        assert error.product_code == product_code
        assert product_code in str(error)
        assert "指定的产品编码不存在" in str(error)

    def test_active_subscription_exists_error(self):
        """测试用户已有有效订阅异常"""
        error = ActiveSubscriptionExistsError()
        
        assert "用户已拥有一个正在生效的同类会员" in str(error)

    def test_subscription_not_found_error(self):
        """测试订阅记录不存在异常"""
        subscription_uuid = str(uuid.uuid4())
        error = SubscriptionNotFoundError(subscription_uuid)
        
        assert error.subscription_uuid == subscription_uuid
        assert subscription_uuid in str(error)
        assert "订阅记录不存在" in str(error)

    # ========================================================================
    # 测试服务初始化
    # ========================================================================

    def test_admin_subscriptions_service_initialization(self, mock_db_session):
        """测试管理员订阅服务初始化"""
        service = AdminSubscriptionsService(mock_db_session)
        
        assert service.db == mock_db_session
        assert hasattr(service, 'get_subscriptions_by_user')
        assert hasattr(service, 'create_subscription_for_user')
        assert hasattr(service, 'update_subscription') 