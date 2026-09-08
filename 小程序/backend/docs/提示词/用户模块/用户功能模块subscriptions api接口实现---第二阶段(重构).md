

### **最终版：高效 AI 代码重构提示词 (Subscriptions模块: 引入Service层)**

#### **1. 角色定义 (Role Definition)**

你是一名资深的 Python 后端架构师，精通分层架构设计（特别是 `Endpoint -> Service -> CRUD` 模式），并擅长将包含复杂业务逻辑的 FastAPI 端点，安全、高效地重构到独立的服务层中。

#### **2. 任务目标 (Task Objective)**

你的核心任务是**重构**现有的 `app/api/v1/endpoints/subscriptions.py` 文件。具体包括：

1.  **【新增文件】** 创建一个全新的**服务层**文件 `app/services/subscriptions_service.py`。
2.  **【逻辑迁移】** 将 `subscriptions.py` 中所有的**业务逻辑**（如数据查询、支付模拟、时间计算、权限校验等）**完整地、安全地迁移**到新的 `SubscriptionsService` 类中。
3.  **【重构文件】** **重写** `app/api/v1/endpoints/subscriptions.py` 文件，使其变得非常简洁。重构后的端点函数**严禁**包含任何业务逻辑，必须改为调用 `SubscriptionsService` 中对应的方法。

#### **3. 核心上下文信息 (Core Context Information)**

**3.1. 项目结构 (重构后)**

**3.1. 项目结构 (重构后)**

```
users/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── deps.py          # <-- 已存在 (代码如下)
│   │       ├── admin/              # <-- 新增 admin 目录
│   │       │   ├── __init__.py
│   │       │   ├── users.py        # <-- 已存在 (代码如下)
│   │       │   ├── products.py     # <-- 已存在 (代码如下)
│   │       │   └── subscriptions.py# <-- 已存在 (代码如下)
│   │       └── endpoints/
│   │           └── auth.py       # <-- 已存在 (代码如下)
│   │           └── users.py       # <-- 已存在 (代码如下)
│   │           └── subscriptions.py       #  <-- 需要重构
│   │           └── membership_products.py # <-- 已存在 (代码如下)
│   │           └── subscriptions.py # <-- 已存在 (代码如下)
│   ├── core/
│   │   └── redis_client.py         # <-- 已存在 (代码如下)
│   │   └── response.py         # <-- 已存在 (代码如下)
│   ├── crud/
│   ├── crud/
│   │   └── crud_user.py              # <-- 已存在 (代码如下)
│   │   └── crud_membership_product.py   # <-- 作为依赖
│   │   └── crud_user_membership.py   # <-- 作为依赖
│   ├── models/
│   │   └── users.py    # <-- 已存在 (代码如下)
│   ├── schemas/
│   │   └── users.py    # <-- 已存在 (代码如下)
│   ├── services/                
│   │   ├── __init__.py
│   │   └── subscriptions_service.py   # <-- 目标文件 1 (新文件)
│   └── database.py         # <-- 已存在
```

**3.2. 需要被重构的源代码**
*你必须根据以下 `subscriptions.py` 的完整代码进行重构。*
  * `@app/api/v1/endpoints/subscriptions.py`
```
"""
用户订阅管理API端点 - 用户功能服务
实现用户侧会员订阅流程：获取订阅列表、购买订阅、更新订阅设置
"""
import logging
import uuid
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Path, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.database import get_async_db
from app.core.responses import success_response, error_response
from app.crud import crud_user_membership, crud_membership_product
from app.schemas.users import (
    UserMembershipResponse, UserMembershipCreate, UserMembershipUpdate,
    SubscriptionCreateRequest, SubscriptionUpdateRequest, PaginatedSubscriptionsResponse
)
from app.models.users import User, MembershipStatus, MembershipProductStatus
from app.api.v1.deps import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users/me/memberships", tags=["User Subscriptions"])


# ============================================================================
# 工具函数
# ============================================================================

async def simulate_payment(payment_token: str, amount: float) -> dict:
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
    transaction_id = f"txn_{datetime.now().strftime('%Y%m%d%H%M%S')}_{payment_token[-4:]}"
    return {"success": True, "transaction_id": transaction_id}


def calculate_expiry_date(duration_unit: str, duration_value: int) -> datetime:
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


# ============================================================================
# API 端点实现
# ============================================================================

@router.get("", response_model=dict)
async def get_my_memberships(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=100, description="每页数量"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    获取当前用户的会员订阅列表
    
    获取当前登录用户的所有会员订阅记录（包括历史记录和当前生效的）
    """
    logger.info(f"开始获取用户订阅列表: user_id={current_user.id}, page={page}, size={size}")
    
    try:
        # 计算分页参数
        skip = (page - 1) * size
        
        # 获取用户的订阅列表
        memberships = await crud_user_membership.get_multi_by_user_id(
            db, user_id=current_user.id, skip=skip, limit=size
        )
        
        # 将结果序列化为List[schemas.UserMembershipResponse]
        membership_responses = [
            UserMembershipResponse.model_validate(membership) 
            for membership in memberships
        ]
        
        # 构建分页响应数据
        response_data = {
            "total": len(membership_responses),  # 简化处理，实际应该查询总数
            "page": page,
            "size": size,
            "items": membership_responses
        }
        
        logger.info(f"成功获取用户订阅列表: user_id={current_user.id}, count={len(membership_responses)}")
        return success_response(response_data)
        
    except Exception as e:
        logger.error(f"获取用户订阅列表失败: user_id={current_user.id}, error={e}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=5001, message="服务器内部错误")
        )


@router.post("", response_model=dict)
async def create_subscription(
    request: SubscriptionCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    用户购买/创建新订阅
    
    用户为自己创建一个新的订阅。这是整个会员体系的核心交易接口。
    """
    # 【安全日志准备】: 在进入try块之前，将需要用于日志记录的用户信息提取到局部变量中
    user_id_for_logging = current_user.id
    
    logger.info(f"开始创建用户订阅: user_id={user_id_for_logging}, product_code={request.product_code}")
    
    try:
        # 1. 业务检查: 调用CRUD检查product_code是否有效且可购买
        products = await crud_membership_product.get_multi_active(db)
        product = None
        for p in products:
            if p.code == request.product_code and p.status == MembershipProductStatus.ACTIVE:
                product = p
                break
        
        if not product:
            logger.warning(f"产品不存在或不可购买: product_code={request.product_code}")
            return JSONResponse(
                status_code=404,
                content=error_response(code=2004, message="产品不存在或不可购买")
            )
        
        # 2. 支付逻辑: (模拟)调用支付服务
        payment_result = await simulate_payment(request.payment_token, float(product.price))
        if not payment_result["success"]:
            logger.warning(f"支付失败: user_id={user_id_for_logging}, error={payment_result.get('error')}")
            return JSONResponse(
                status_code=402,
                content=error_response(code=4002, message="支付失败", data={"error": payment_result.get("error")})
            )
        
        # 3. 支付成功后，构造schemas.UserMembershipCreate对象（user_id来自current_user.id）
        start_date = datetime.now()
        expires_at = calculate_expiry_date(product.duration_unit, product.duration_value)
        
        membership_create = UserMembershipCreate(
            user_id=current_user.id,
            product_code=product.code,
            transaction_id=payment_result["transaction_id"],
            level=product.level,
            status=MembershipStatus.ACTIVE,
            is_auto_renew=True,  # 默认开启自动续费
            start_date=start_date,
            expires_at=expires_at
        )
        
        # 4. 调用crud_user_membership.create()创建订阅记录
        try:
            new_membership = await crud_user_membership.create(db, obj_in=membership_create)
        except IntegrityError:
            # 5. 异常处理: 捕获IntegrityError并返回409冲突
            # 使用安全的局部变量进行日志记录，避免访问可能已失效的ORM对象
            logger.warning(f"用户已有同类有效订阅: user_id={user_id_for_logging}, product_code={request.product_code}")
            return JSONResponse(
                status_code=409,
                content=error_response(code=2005, message='您已拥有一个正在生效的同类会员')
            )
        
        # 6. 调用success_response返回新创建的订阅信息
        response_data = UserMembershipResponse.model_validate(new_membership)
        logger.info(f"成功创建用户订阅: user_id={user_id_for_logging}, membership_id={new_membership.id}")
        return success_response(response_data)
        
    except Exception as e:
        # 使用安全的局部变量进行日志记录，避免访问可能已失效的ORM对象
        logger.error(f"创建用户订阅失败: user_id={user_id_for_logging}, error={e}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=5001, message="服务器内部错误")
        )


@router.patch("/{subscription_uuid}", response_model=dict)
async def update_subscription(
    subscription_uuid: uuid.UUID = Path(..., description="订阅UUID"),
    request: SubscriptionUpdateRequest = ...,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    用户更新自己的订阅
    
    更新用户自己的一条订阅记录，主要用于开关"自动续费"。
    """
    logger.info(f"开始更新用户订阅: user_id={current_user.id}, subscription_uuid={subscription_uuid}")
    
    try:
        # 1. 调用crud_user_membership.get_by_uuid_and_user_id()，并传入uuid=subscription_uuid和user_id=current_user.id来获取并验证订阅记录
        membership = await crud_user_membership.get_by_uuid_and_user_id(
            db, uuid=subscription_uuid, user_id=current_user.id
        )
        
        # 2. 若记录为None（不存在或不属于该用户），返回JSONResponse(status_code=404, content=error_response(code=2004, message='订阅记录不存在'))
        if not membership:
            logger.warning(f"订阅记录不存在或无权限: subscription_uuid={subscription_uuid}, user_id={current_user.id}")
            return JSONResponse(
                status_code=404,
                content=error_response(code=2004, message='订阅记录不存在')
            )
        
        # 3. 业务检查: 检查订阅状态是否允许修改is_auto_renew（例如，EXPIRED状态的就不允许）
        if membership.status == MembershipStatus.EXPIRED:
            logger.warning(f"已过期的订阅不允许修改: subscription_uuid={subscription_uuid}")
            return JSONResponse(
                status_code=400,
                content=error_response(code=2002, message="已过期的订阅不允许修改续费设置")
            )
        
        # 4. 调用crud_user_membership.update()更新记录
        update_data = UserMembershipUpdate(is_auto_renew=request.is_auto_renew)
        updated_membership = await crud_user_membership.update(
            db, db_obj=membership, obj_in=update_data
        )
        
        # 5. 调用success_response返回更新后的订阅信息
        response_data = UserMembershipResponse.model_validate(updated_membership)
        logger.info(f"成功更新用户订阅: user_id={current_user.id}, subscription_uuid={subscription_uuid}")
        return success_response(response_data)
        
    except Exception as e:
        logger.error(f"更新用户订阅失败: user_id={current_user.id}, subscription_uuid={subscription_uuid}, error={e}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=5001, message="服务器内部错误")
        ) 
```

**3.3. 依赖的上下文**
*在重构过程中，你需要依赖以下模块*

  * `@app/crud/crud_user_membership.py`
  * `@app/crud/crud_membership_product.py`
  * `@app/models/users.py`
  * `@app/schemas/users.py`
  * `@app/core/responses.py`
  * `@app/database.py`
  * `@app/api/v1/deps.py`


-----

#### **4. 核心重构原则与规范 (Core Refactoring Principles & Specifications)**

**【关键指令】** 你在执行本次重构时，**必须严格遵守**您在文档中提供的所有规范，特别是：


## 1. 核心编码原则 (Core Coding Principles)

### 🛡️ 安全异步异常处理 (Safe Async Exception Handling)

- **规则**：在任何 `try...except` 块中，如果需要使用来自数据库 ORM 对象（如 `current_user`）的属性（如 `current_user.id`）进行日志记录或错误处理，这些属性**必须在进入 `try` 块之前**被提取并存储到局部变量中。
- **指令**：**严禁**在捕获了数据库相关异常（如 `IntegrityError`）的 `except` 块中直接访问可能已与失效会话关联的 ORM 对象的属性。

---

## 2. 接口实现规范 (Endpoint Implementation)

### 🧱 主动变量提取 (Proactive Variable Extraction)

- **实现流程**：
  - 在进入 `try` 块之前，主动提取所有需要在异常处理中使用的变量（如：`user_id_for_logging = current_user.id`）。
  - 在 `except` 块中，**必须使用这些局部变量**进行日志记录或错误处理，避免访问失效对象。

### 🧪 异常处理 (Exception Handling)

- 将整个接口流程包裹在 `try...except` 块中。
- 若发生数据库查询等未知异常，应：
  - 记录错误日志；
  - 返回统一错误响应：
    ```python
    JSONResponse(
        status_code=500,
        content=error_response(code=1002, message='数据库查询错误')
    )
    ```

---

## 3. 响应处理规范 (Response Handling)

### ✅ 成功响应

- 所有成功返回**必须**调用 `success_response(data=...)` 函数构建响应内容。
- 示例：
  ```python
  return success_response(data=user_info)
  ```

### ❌ 错误响应

- 所有业务错误必须返回 `fastapi.responses.JSONResponse`，其 `content` 由 `error_response(...)` 构建。
- 示例：
  ```python
  return JSONResponse(
      status_code=400,
      content=error_response(code=1001, message='参数错误')
  )
  ```

> 假设 `success_response()` 和 `error_response()` 已定义在 `app/core/responses.py` 中。

---

## 4. 外部服务连接规范 (External Service Connections)

### 🔐 环境变量驱动配置

- 所有外部服务（如 Redis、数据库、第三方 API）的连接信息**必须**通过环境变量读取。
- 示例：
  ```python
  import os
  redis_host = os.getenv("REDIS_HOST", "localhost")
  redis_port = os.getenv("REDIS_PORT", "6379")
  ```
- 目的：确保代码在本地、Docker、测试、生产等不同环境下**无需修改即可运行**。

##### **4.1. 服务层 (`SubscriptionsService`) 设计规范**

  * **类化设计**: 在 `app/services/subscriptions_service.py` 中创建一个 `SubscriptionsService` 类。
  * **依赖注入**: `SubscriptionsService` 的 `__init__` 方法应接收 `db: AsyncSession` 作为参数。
  * **职责**:
      * 封装完整的**用户注册**流程。
      * 封装用户**更新个人资料**的流程。
      * 封装用户**修改密码**的流程。
      * 封装用户**注销账户**的流程。

##### **4.2. 端点层 (`subscriptionss.py`) 重构规范**

  * **保持简洁**: 重构后的端点函数体应该非常简短。
  * **职责**:
      * 只负责处理 FastAPI 的 `Request` 和 `Depends`。
      * 实例化 `SubscriptionsService`。
      * 调用 `SubscriptionsService` 中对应的方法来执行业务逻辑。
      * 捕获 `Service` 层抛出的业务异常，并使用 `error_response` 将其转换为标准的 `JSONResponse`。
  * **禁止**: **严禁**在重构后的端点函数中直接调用 `crud_*` 模块或执行任何业务逻辑计算。
  * *必须**遵循"主动变量提取"和安全异常处理模式  # ← 容易被忽略

比如：
```python
async def service_method(self, user: User, request: SomeRequest) -> SomeResult:
    # 🔴 第一步：立即提取变量（安全红线）
    user_id_for_logging = user.id
    request_field_for_logging = request.field
    
    logger.info(f"开始处理: user_id={user_id_for_logging}")
    
    try:
        # 业务逻辑
        pass
    except SpecificException as e:
        # 🔴 只使用局部变量（安全红线）
        logger.warning(f"特定错误: user_id={user_id_for_logging}")
        raise
    except Exception as e:
        # 🔴 只使用局部变量（安全红线）
        logger.error(f"通用错误: user_id={user_id_for_logging}, error={e}")
        raise
```

### **❌ 绝对禁止的反模式**
```python
# ❌ 错误：在异常处理中访问ORM对象
except IntegrityError:
    logger.warning(f"错误: user_id={user.id}")  # ← 会导致greenlet错误
```

-----

#### **5. 具体代码生成指令 (Specific Code Generation Instructions)**

## 🚨 **重要提醒**
**在开始重构前，请先阅读并严格遵循:  4. 核心重构原则与规范 (Core Refactoring Principles & Specifications)**


##### **5.1. 第一部分: `app/services/subscriptions_service.py` (新文件)**

  * **指令**: 请为以下文件路径生成完整的 Python 代码：
    `app/services/subscriptions_service.py`

  * **内容要求**:

      * 创建一个 `SubscriptionsService` 类。
      * 将【3.2】中 `subscriptions.py` 文件里的所有**工具函数**（如 `simulate_payment`, `calculate_expiry_date`）和**业务逻辑**迁移到 `SubscriptionsService` 的方法中。
      * **必须**定义清晰的业务异常类（例如 `ProductNotFoundError`, `PaymentFailedError`, `ActiveSubscriptionExistsError`, `SubscriptionOwnershipError`）。

  * **需在 `SubscriptionsService` 类中实现的方法**:

    1.  **`get_user_subscriptions(self, user_id: int, page: int, size: int) -> dict`**:

          * **业务逻辑流程**:
            1.  计算分页参数 `skip = (page - 1) * size`。
            2.  **数据查询**: 调用 `crud_user_membership.get_multi_by_user_id()` 并传入 `user_id`, `skip`, `limit=size`。
            3.  调用 `crud_user_membership.count_by_user_id()` (假设此新CRUD函数用于获取总数) 获取 `total`。
            4.  **序列化**: 将查询到的 SQLAlchemy 对象列表，逐一安全地序列化为 `List[schemas.UserMembershipResponse]`。
            5.  返回一个包含 `total`, `page`, `size`, `items` 的分页结果字典。

    2.  **`create_new_subscription(self, user: models.User, sub_create_request: schemas.SubscriptionCreateRequest) -> models.UserMembership`**:

          * **业务逻辑流程**:
            1.  **业务检查 (产品)**: 调用 `crud_membership_product.get_by_code()` 检查 `sub_create_request.product_code` 是否有效。如果产品不存在或其 `status` 不为 `ACTIVE`，`raise ProductNotFoundError()`。
            2.  **支付逻辑**: (模拟) 调用一个内部的 `_simulate_payment()` 辅助方法。如果支付失败，`raise PaymentFailedError()`。
            3.  **计算时间**: 根据 `product` 的 `duration_unit` 和 `duration_value` 调用内部的 `_calculate_expiry_date` 辅助方法计算出 `start_date` 和 `expires_at`。
            4.  **构造Schema**: 构造一个完整的 `schemas.UserMembershipCreate` 对象，包含 `user_id=user.id`, `product_code`, `transaction_id`, `level`, `status='ACTIVE'`, `is_auto_renew=True` 以及计算出的时间。
            5.  **创建记录**: 在 `try...except IntegrityError` 块中调用 `crud_user_membership.create()`。
            6.  **异常处理**: 如果捕获 `IntegrityError`，`raise ActiveSubscriptionExistsError("您已拥有一个正在生效的同类会员")`。
            7.  返回成功创建的 `models.UserMembership` 对象。

    3.  **`update_user_subscription(self, user: models.User, subscription_uuid: uuid.UUID, sub_update_request: schemas.SubscriptionUpdateRequest) -> models.UserMembership`**:

          * **业务逻辑流程**:
            1.  **数据查询与权限校验**: 调用 `crud_user_membership.get_by_uuid_and_user_id()`，并传入 `uuid=subscription_uuid` 和 `user_id=user.id` 来获取并验证订阅记录。
            2.  如果记录为 `None` (不存在或不属于该用户)，`raise SubscriptionOwnershipError("订阅记录不存在或无权修改")`。
            3.  **业务检查**: 检查订阅记录的 `status` 是否允许被修改（例如，`EXPIRED` 状态的就不允许）。如果不允许，`raise SubscriptionUpdateForbiddenError("已过期的订阅无法修改")`。
            4.  **数据更新**: 调用 `crud_user_membership.update()` 更新记录的 `is_auto_renew` 字段。
            5.  返回更新后的 `models.UserMembership` 对象。

##### **5.2. 第二部分: `app/api/v1/endpoints/subscriptions.py` (重构后的完整版)**

  * **指令**: 请为以下文件路径生成**重构后的**完整 Python 代码：
    `app/api/v1/endpoints/subscriptions.py`

  * **内容要求**:

      * 保留 `APIRouter` 和所有端点定义。
      * **重写**每个端点函数的内部实现，使其只包含对 `SubscriptionsService` 的调用和响应处理。
      * *必须**遵循"主动变量提取"和安全异常处理模式  # ← 容易被忽略

比如：
```python
async def service_method(self, user: User, request: SomeRequest) -> SomeResult:
    # 🔴 第一步：立即提取变量（安全红线）
    user_id_for_logging = user.id
    request_field_for_logging = request.field
    
    logger.info(f"开始处理: user_id={user_id_for_logging}")
    
    try:
        # 业务逻辑
        pass
    except SpecificException as e:
        # 🔴 只使用局部变量（安全红线）
        logger.warning(f"特定错误: user_id={user_id_for_logging}")
        raise
    except Exception as e:
        # 🔴 只使用局部变量（安全红线）
        logger.error(f"通用错误: user_id={user_id_for_logging}, error={e}")
        raise
```

  * **需重构的端点 (在 `app/api/v1/endpoints/subscriptions.py` 中)**:

    1.  **`GET /` (获取当前用户的会员订阅列表)**

          * **重构实现流程**:
            1.  通过 `Depends(get_current_user)` 获取 `current_user` 对象。
            2.  **主动提取**: `user_id_for_logging = current_user.id`。
            3.  在 `try...except` 块中：
                  * a. 实例化 `sub_service = SubscriptionsService(db)`。
                  * b. 调用 `paginated_result = await sub_service.get_user_subscriptions(user_id=current_user.id, page=page, size=size)`。
                  * c. 调用 `success_response` 返回 `paginated_result`。
            4.  **异常处理**: 捕获通用异常并返回 `500` 错误。

    2.  **`POST /` (用户购买/创建新订阅)**

          * **重构实现流程**:
            1.  通过 `Depends(get_current_user)` 获取 `current_user` 对象。
            2.  **主动提取**: `user_id_for_logging = current_user.id`。
            3.  在 `try...except` 块中：
                  * a. 实例化 `sub_service = SubscriptionsService(db)`。
                  * b. 调用 `new_subscription = await sub_service.create_new_subscription(user=current_user, sub_create_request=request)`。
                  * c. 序列化 `new_subscription` 并调用 `success_response` 返回。
            4.  **异常处理**:
                  * a. `except ProductNotFoundError as e`: 返回 `JSONResponse(status_code=404, content=error_response(code=2004, message=str(e)))`。
                  * b. `except ActiveSubscriptionExistsError as e`: 返回 `JSONResponse(status_code=409, content=error_response(code=2005, message=str(e)))`。
                  * c. `except PaymentFailedError as e`: 返回 `JSONResponse(status_code=402, content=error_response(code=2003, message=str(e)))`。
                  * d. `except Exception as e`: 返回 `500` 错误。

    3.  **`PATCH /{subscription_uuid}` (用户更新自己的订阅)**

          * **重构实现流程**:
            1.  通过 `Depends(get_current_user)` 获取 `current_user` 对象。
            2.  **主动提取**: `user_id_for_logging = current_user.id`。
            3.  在 `try...except` 块中：
                  * a. 实例化 `sub_service = SubscriptionsService(db)`。
                  * b. 调用 `updated_subscription = await sub_service.update_user_subscription(user=current_user, subscription_uuid=subscription_uuid, sub_update_request=request)`。
                  * c. 序列化 `updated_subscription` 并调用 `success_response` 返回。
            4.  **异常处理**:
                  * a. `except SubscriptionOwnershipError as e`: 返回 `JSONResponse(status_code=404, content=error_response(code=2004, message=str(e)))`。
                  * b. `except SubscriptionUpdateForbiddenError as e`: 返回 `JSONResponse(status_code=400, content=error_response(code=2002, message=str(e)))`。
                  * c. `except Exception as e`: 返回 `500` 错误。

#### **6. 最终交付 (Final Deliverable)**

请根据以上所有要求，为我生成以下**两个文件**的完整、可直接使用的 Python 代码。

1.  `app/services/subscriptions_service.py` **(新文件)**
2.  `app/api/v1/endpoints/subscriptions.py` **(重构后的完整版)**