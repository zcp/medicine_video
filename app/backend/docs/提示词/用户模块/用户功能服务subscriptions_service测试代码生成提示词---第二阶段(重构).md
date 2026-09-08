#### **1. 角色定义 (Role Definition)**

You are a Senior Python Backend Engineer specializing in automated testing. You are an expert in using `pytest` with `pytest-asyncio` and mocking frameworks like `pytest-mock`. Your task is to write a robust **unit test suite** for the provided `SubscriptionsService` class.

#### **2. 任务目标 (Task Objective)**

Your goal is to generate the complete code for **one new test file**: `tests/test_subscriptions_service.py`.

#### **3. 核心上下文信息 (Core Context Information)**

**3.1. Testing Strategy**
* **For `Service` layer (`test_subscriptions_service.py`)**: Test thoroughly using **mocking**. All external dependencies (like `crud_user_membership` and `crud_membership_product` functions) **must be mocked** to test the `SubscriptionsService` logic in complete isolation.

**3.2. 被测试代码 (Code to be Tested)**
* `@app/services/subscription_service.py`
```
"""
订阅服务层 - SubscriptionsService
封装所有订阅相关的业务逻辑，包括用户订阅列表查询、新订阅创建、订阅更新等
"""
import logging
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.crud import crud_user_membership, crud_membership_product
from app.schemas.users import (
    UserMembershipResponse, UserMembershipCreate, UserMembershipUpdate,
    SubscriptionCreateRequest, SubscriptionUpdateRequest
)
from app.models.users import User, UserMembership, MembershipStatus, MembershipProductStatus

logger = logging.getLogger(__name__)


# ============================================================================
# 业务异常定义
# ============================================================================

class SubscriptionsServiceException(Exception):
    """订阅服务基础异常"""
    pass


class ProductNotFoundError(SubscriptionsServiceException):
    """产品不存在或不可购买异常"""
    def __init__(self, product_code: str, message: str = "产品不存在或不可购买"):
        self.product_code = product_code
        super().__init__(f"{message}: {product_code}")


class PaymentFailedError(SubscriptionsServiceException):
    """支付失败异常"""
    def __init__(self, payment_error: str, message: str = "支付处理失败"):
        self.payment_error = payment_error
        super().__init__(f"{message}: {payment_error}")


class ActiveSubscriptionExistsError(SubscriptionsServiceException):
    """用户已有同类有效订阅异常"""
    def __init__(self, message: str = "您已拥有一个正在生效的同类会员"):
        super().__init__(message)


class SubscriptionOwnershipError(SubscriptionsServiceException):
    """订阅记录不存在或无权修改异常"""
    def __init__(self, subscription_uuid: str, message: str = "订阅记录不存在或无权修改"):
        self.subscription_uuid = subscription_uuid
        super().__init__(f"{message}: {subscription_uuid}")


class SubscriptionUpdateForbiddenError(SubscriptionsServiceException):
    """订阅状态不允许修改异常"""
    def __init__(self, status: str, message: str = "已过期的订阅无法修改"):
        self.status = status
        super().__init__(f"{message}: 当前状态为 {status}")


# ============================================================================
# 订阅服务类
# ============================================================================

class SubscriptionsService:
    """订阅服务类"""
    
    def __init__(self, db: AsyncSession):
        """
        初始化订阅服务
        
        Args:
            db: 数据库会话
        """
        self.db = db
    
    async def get_user_subscriptions(self, user_id: int, page: int, size: int) -> Dict[str, Any]:
        """
        获取用户的订阅列表（分页）
        
        Args:
            user_id: 用户ID
            page: 页码
            size: 每页数量
            
        Returns:
            包含分页信息的订阅列表字典
        """
        logger.info(f"开始获取用户订阅列表: user_id={user_id}, page={page}, size={size}")
        
        try:
            # 1. 计算分页参数
            skip = (page - 1) * size
            
            # 2. 数据查询 - 获取用户的订阅列表
            memberships = await crud_user_membership.get_multi_by_user_id(
                self.db, user_id=user_id, skip=skip, limit=size
            )
            
            # 3. 序列化 - 将SQLAlchemy对象转换为Pydantic模型
            membership_responses = []
            for membership in memberships:
                try:
                    membership_response = UserMembershipResponse.model_validate(membership)
                    membership_responses.append(membership_response)
                except Exception as e:
                    membership_id = getattr(membership, 'id', 'unknown')
                    logger.warning(f"序列化用户订阅失败: membership_id={membership_id}, error={e}")
                    # 跳过失败的订阅，继续处理其他订阅
                    continue
            
            # 4. 构建分页响应数据
            paginated_result = {
                "total": len(membership_responses),  # 简化处理，实际应该查询总数
                "page": page,
                "size": size,
                "items": membership_responses
            }
            
            logger.info(f"成功获取用户订阅列表: user_id={user_id}, count={len(membership_responses)}")
            return paginated_result
            
        except Exception as e:
            logger.error(f"获取用户订阅列表失败: user_id={user_id}, error={e}")
            raise
    
    async def create_new_subscription(self, user: User, sub_create_request: SubscriptionCreateRequest) -> UserMembership:
        """
        创建新的用户订阅
        
        Args:
            user: 用户对象
            sub_create_request: 订阅创建请求
            
        Returns:
            新创建的订阅记录
            
        Raises:
            ProductNotFoundError: 产品不存在或不可购买
            PaymentFailedError: 支付失败
            ActiveSubscriptionExistsError: 用户已有同类有效订阅
        """
        user_id_for_logging = user.id
        product_code_for_logging = sub_create_request.product_code

        logger.info(f"开始创建用户订阅: user_id={user.id}, product_code={product_code_for_logging}")
        
        try:
            # 1. 业务检查 - 检查产品是否有效且可购买
            # 添加调试日志
            logger.info("步骤1: 开始查询活跃产品")
            products = await crud_membership_product.get_multi_active(self.db)
            logger.info(f"步骤1: 成功查询到 {len(products)} 个活跃产品")
            product = None
            for p in products:
                if p.code == sub_create_request.product_code and p.status == MembershipProductStatus.ACTIVE:
                    product = p
                    break
            
            if not product:
                logger.warning(f"产品不存在或不可购买: product_code={sub_create_request.product_code}")
                raise ProductNotFoundError(sub_create_request.product_code)
            
            # 2. 支付逻辑 - 调用支付服务
            payment_result = self._simulate_payment(sub_create_request.payment_token, float(product.price))
            if not payment_result["success"]:
                payment_error = payment_result.get('error', '未知支付错误')
                logger.warning(f"支付失败: user_id={user.id}, error={payment_error}")
                raise PaymentFailedError(payment_error)
            
            # 3. 计算时间 - 根据产品配置计算过期时间
            start_date = datetime.now()
            expires_at = self._calculate_expiry_date(product.duration_unit, product.duration_value)
            
            # 4. 构造Schema - 创建用户订阅对象
            membership_create = UserMembershipCreate(
                user_id=user.id,
                product_code=product.code,
                transaction_id=payment_result["transaction_id"],
                level=product.level,
                status=MembershipStatus.ACTIVE,
                is_auto_renew=True,  # 默认开启自动续费
                start_date=start_date,
                expires_at=expires_at
            )
            
            # 5. 创建记录 - 调用CRUD层创建订阅记录
            try:
                new_membership = await crud_user_membership.create(self.db, obj_in=membership_create)
                logger.info(f"成功创建用户订阅: user_id={user.id}, membership_id={new_membership.id}")
                return new_membership
            except IntegrityError:
                # 6. 异常处理 - 捕获数据库完整性约束错误
                logger.warning(f"用户已有同类有效订阅: user_id={user_id_for_logging}, product_code={product_code_for_logging}")
                raise ActiveSubscriptionExistsError()
                
        except (ProductNotFoundError, PaymentFailedError, ActiveSubscriptionExistsError):
            raise
        except Exception as e:
            logger.error(f"创建用户订阅失败: user_id={user.id}, error={e}")
            raise
    
    async def update_user_subscription(self, user: User, subscription_uuid: uuid.UUID, sub_update_request: SubscriptionUpdateRequest) -> UserMembership:
        """
        更新用户订阅
        
        Args:
            user: 用户对象
            subscription_uuid: 订阅UUID
            sub_update_request: 订阅更新请求
            
        Returns:
            更新后的订阅记录
            
        Raises:
            SubscriptionOwnershipError: 订阅记录不存在或无权修改
            SubscriptionUpdateForbiddenError: 订阅状态不允许修改
        """
        logger.info(f"开始更新用户订阅: user_id={user.id}, subscription_uuid={subscription_uuid}")
        
        try:
            # 1. 数据查询与权限校验 - 获取并验证订阅记录
            membership = await crud_user_membership.get_by_uuid_and_user_id(
                self.db, uuid=subscription_uuid, user_id=user.id
            )
            
            # 2. 检查订阅记录是否存在且属于该用户
            if not membership:
                logger.warning(f"订阅记录不存在或无权限: subscription_uuid={subscription_uuid}, user_id={user.id}")
                raise SubscriptionOwnershipError(str(subscription_uuid))
            
            # 3. 业务检查 - 检查订阅状态是否允许修改
            if membership.status == MembershipStatus.EXPIRED:
                logger.warning(f"已过期的订阅不允许修改: subscription_uuid={subscription_uuid}")
                raise SubscriptionUpdateForbiddenError(membership.status.value)
            
            # 4. 数据更新 - 更新订阅记录
            update_data = UserMembershipUpdate(is_auto_renew=sub_update_request.is_auto_renew)
            updated_membership = await crud_user_membership.update(
                self.db, db_obj=membership, obj_in=update_data
            )
            
            logger.info(f"成功更新用户订阅: user_id={user.id}, subscription_uuid={subscription_uuid}")
            return updated_membership
            
        except (SubscriptionOwnershipError, SubscriptionUpdateForbiddenError):
            raise
        except Exception as e:
            logger.error(f"更新用户订阅失败: user_id={user.id}, subscription_uuid={subscription_uuid}, error={e}")
            raise
    
    # ========================================================================
    # 内部辅助方法
    # ========================================================================
    
    def _simulate_payment(self, payment_token: str, amount: float) -> Dict[str, Any]:
        """
        模拟支付服务调用
        
        Args:
            payment_token: 支付令牌
            amount: 支付金额
            
        Returns:
            支付结果字典，包含 success 状态和 transaction_id
        """
        logger.info(f"模拟支付处理: payment_token={payment_token}, amount={amount}")
        
        # 模拟支付逻辑 - 在实际环境中这里会调用真实的支付网关
        if payment_token.startswith("tok_invalid"):
            return {"success": False, "error": "支付令牌无效"}
        
        if amount <= 0:
            return {"success": False, "error": "支付金额无效"}
        
        # 模拟支付成功
        # 使用UUID确保绝对唯一性
        transaction_id = f"txn_{uuid.uuid4().hex[:16]}_{payment_token[-4:]}"
        return {"success": True, "transaction_id": transaction_id}
    
    def _calculate_expiry_date(self, duration_unit: str, duration_value: int) -> datetime:
        """
        根据产品配置计算过期时间
        
        Args:
            duration_unit: 时长单位 (day, week, month, year)
            duration_value: 时长数值
            
        Returns:
            过期时间
        """
        now = datetime.now()
        
        if duration_unit == "day":
            return now + timedelta(days=duration_value)
        elif duration_unit == "week":
            return now + timedelta(weeks=duration_value)
        elif duration_unit == "month":
            return now + timedelta(days=duration_value * 30)  # 简化计算
        elif duration_unit == "year":
            return now + timedelta(days=duration_value * 365)  # 简化计算
        else:
            # 默认按天计算
            return now + timedelta(days=duration_value) 
```

**3.3. 依赖的上下文 (Dependencies & Context)**
* `@tests/conftest.py` (**作为测试环境和 Fixture 的来源，不可修改**)
* `@app/models/users.py` (需要 `User`, `UserMembership`, `MembershipProduct` 模型)
* `@app/schemas/users.py` (需要 `UserMembershipCreate`, `SubscriptionCreateRequest` 等 Schemas)
* `@app/crud/crud_user_membership.py`
* `@app/crud/crud_membership_product.py`

---
#### **4. 代码生成具体要求 (Specific Code Generation Instructions)**

##### **4.1. `tests/conftest.py` - 测试设置**
* **指令**: 你的任务**不包括**生成或修改 `conftest.py`。你**必须假设**它已存在并提供 `db_session` fixture。

##### **4.2. 测试数据隔离 (Test Data Isolation)**
* **指令**: 所有测试用例在准备数据时，**必须**使用 `faker` 或 `uuid` 生成随机且唯一的测试数据。

##### **4.3. `tests/test_services/test_subscriptions_service.py` - Service层单元测试**

* **文件名**: `tests/test_services/test_subscriptions_service.py`
* **职责**: 对 `app/services/subscriptions_service.py` 中的每个公共方法进行详细的、隔离的单元测试。
* **核心要求**: **必须使用 `mocker` fixture** 来模拟所有外部依赖。

* **需实现的测试用例**:

    1.  **`test_get_user_subscriptions_success`**:
        * **准备 (Arrange)**:
            * a. 创建 `SubscriptionsService` 实例 `sub_service`。
            * b. 创建一个模拟的 `UserMembership` 对象列表 `mock_memberships`。
            * c. Mock `crud_user_membership.get_multi_by_user_id` 使其返回 `mock_memberships`。
            * d. Mock `crud_user_membership.count_by_user_id` (假设存在) 使其返回 `len(mock_memberships)`。
        * **执行 (Act)**: 调用 `sub_service.get_user_subscriptions()`。
        * **断言 (Assert)**:
            * a. 断言返回的字典中 `items` 列表的长度与模拟数据一致。
            * b. 断言 `total` 字段的值与模拟的总数一致。
            * c. 断言 `crud_user_membership.get_multi_by_user_id` 被以正确的 `user_id`, `skip`, `limit` 参数调用。

    2.  **`test_create_new_subscription_success`**:
        * **准备 (Arrange)**:
            * a. 创建 `sub_service` 实例。
            * b. 创建模拟的 `user` 对象和 `SubscriptionCreateRequest` 对象 `sub_request`。
            * c. 创建一个`status`为`ACTIVE`的模拟 `MembershipProduct` 对象 `mock_product`。
            * d. Mock `crud_membership_product.get_multi_active` 使其返回 `[mock_product]`。
            * e. Mock `sub_service._simulate_payment` 使其返回 `{"success": True, "transaction_id": "fake_txn_id"}`。
            * f. Mock `crud_user_membership.create` 方法。
        * **执行 (Act)**: 调用 `sub_service.create_new_subscription(user=mock_user, sub_create_request=sub_request)`。
        * **断言 (Assert)**:
            * a. 断言 `crud_user_membership.create` **被调用了一次**。
            * b. **验证数据库字段**: 检查传递给 `create` 的 `obj_in` 参数，断言其 `user_id`, `product_code`, `transaction_id`, `status` 等字段的值都与业务逻辑处理后的预期一致。

    3.  **`test_create_new_subscription_fails_if_product_not_found`**:
        * **准备**: Mock `crud_membership_product.get_multi_active` 返回一个**空列表** `[]`。
        * **执行与断言**: 使用 `with pytest.raises(ProductNotFoundError):` 来包裹对 `sub_service.create_new_subscription()` 的调用。

    4.  **`test_create_new_subscription_fails_if_payment_fails`**:
        * **准备**: Mock `crud_membership_product.get_multi_active` 返回有效产品，但 Mock `sub_service._simulate_payment` 使其返回 `{"success": False, ...}`。
        * **执行与断言**: 使用 `with pytest.raises(PaymentFailedError):` 来包裹调用。

    5.  **`test_create_new_subscription_fails_if_already_active`**:
        * **准备**: Mock `crud_membership_product.get_multi_active` 和 `_simulate_payment` 都成功，但 Mock `crud_user_membership.create` 使其**主动抛出** `IntegrityError`。
        * **执行与断言**: 使用 `with pytest.raises(ActiveSubscriptionExistsError):` 来包裹调用。

    6.  **`test_update_user_subscription_success`**:
        * **准备**:
            * a. 创建模拟的 `user` 对象和 `SubscriptionUpdateRequest` 对象 `update_request`。
            * b. 创建一个 `status` 为 `ACTIVE` 的模拟 `UserMembership` 对象 `mock_subscription`。
            * c. Mock `crud_user_membership.get_by_uuid_and_user_id` 使其返回 `mock_subscription`。
            * d. Mock `crud_user_membership.update` 方法。
        * **执行**: 调用 `sub_service.update_user_subscription(...)`。
        * **断言**:
            * a. 断言 `crud_user_membership.update` 被调用了一次。
            * b. 检查传递给 `update` 的 `obj_in` 参数，断言 `is_auto_renew` 的值与 `update_request` 中的值一致。

    7.  **`test_update_user_subscription_fails_if_not_owner`**:
        * **准备**: Mock `crud_user_membership.get_by_uuid_and_user_id` 使其返回 `None` (模拟找不到或不属于该用户的场景)。
        * **执行与断言**: 使用 `with pytest.raises(SubscriptionOwnershipError):` 来包裹调用。

    8.  **`test_update_user_subscription_fails_if_expired`**:
        * **准备**: 创建一个 `status` 为 `EXPIRED` 的模拟 `UserMembership` 对象，并让 `crud_user_membership.get_by_uuid_and_user_id` 返回它。
        * **执行与断言**: 使用 `with pytest.raises(SubscriptionUpdateForbiddenError):` 来包裹调用。

#### **5. 最终交付 (Final Deliverable)**

Please generate the complete, runnable Python code for the following **one new file**:
1.  `tests/test_subscriptions_service.py`