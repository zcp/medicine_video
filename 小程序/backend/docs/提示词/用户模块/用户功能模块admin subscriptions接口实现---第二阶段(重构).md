

### **最终版：高效 AI 代码重构提示词 (Subscriptions模块: 引入Service层)**

#### **1. 角色定义 (Role Definition)**

你是一名资深的 Python 后端架构师，精通分层架构设计（特别是 `Endpoint -> Service -> CRUD` 模式），并擅长将包含复杂业务逻辑的 FastAPI 端点，安全、高效地重构到独立的服务层中。

#### **2. 任务目标 (Task Objective)**

你的核心任务是**重构**现有的 `app/api/v1/admin/subscriptions.py` 文件。具体包括：

1.  **【新增文件】** 创建一个全新的**服务层**文件 `app/services/admin_subscriptions_service.py`。
2.  **【逻辑迁移】** 将 `admin/subscriptions.py` 中所有的**业务逻辑**（如用户查找、产品校验、权限控制、数据构造等）**完整地、安全地迁移**到新的 `AdminSubscriptionsService` 类中。
3.  **【重构文件】** **重写** `app/api/v1/admin/subscriptions.py` 文件，使其变得非常简洁。重构后的端点函数**严禁**包含任何业务逻辑，必须改为调用 `AdminSubscriptionsService` 中对应的方法。

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
│   │       │   └── subscriptions.py#  <-- 需要重构
│   │       └── endpoints/
│   │           └── auth.py       # <-- 已存在 (代码如下)
│   │           └── users.py       # <-- 已存在 (代码如下)
│   │           └── subscriptions.py      # <-- 已存在 (代码如下)
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
│   │   └── admin_subscriptions_service.py   # <-- 目标文件 1 (新文件)
│   └── database.py         # <-- 已存在
```

**3.2. 需要被重构的源代码**
*你必须根据以下 `subscriptions.py` 的完整代码进行重构。*
  * `@app/api/v1/endpoints/subscriptions.py`
```
"""
后台管理API - 用户订阅管理
提供订阅查询、手动创建、更新等管理功能
"""
import logging
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query, Path
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.database import get_async_db
from app.core.responses import success_response, error_response
from app.crud import crud_user, crud_user_membership, crud_membership_product
from app.schemas.users import (
    UserMembershipResponse, UserMembershipCreateAdmin, UserMembershipUpdate,
    PaginatedUserMembershipsResponse, UserMembershipCreate
)
from app.models.users import User, MembershipStatus
from app.api.v1.deps import get_current_admin_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/subscriptions", tags=["Admin - Subscriptions"])


@router.get("/by-user/{user_uuid}", response_model=dict)
async def get_user_memberships(
    user_uuid: uuid.UUID = Path(..., description="用户UUID"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=100, description="每页数量"),
    sort: Optional[str] = Query("created_at:desc", description="排序字段"),
    admin_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    (管理员/客服) 获取指定用户的所有订阅历史记录
    """
    # 【安全日志准备】: 提取管理员信息到局部变量
    admin_user_id_for_logging = admin_user.id
    
    logger.info(f"管理员开始查询用户订阅列表: admin_user_id={admin_user_id_for_logging}, target_user_uuid={user_uuid}")
    
    try:
        # 根据user_uuid找到user_id
        target_user = await crud_user.get_by_uuid(db, public_id=user_uuid)
        if not target_user:
            logger.warning(f"目标用户不存在: user_uuid={user_uuid}")
            return JSONResponse(
                status_code=404,
                content=error_response(code=2004, message='用户不存在')
            )
        
        # 【安全日志准备】: 提取目标用户信息到局部变量
        target_user_id_for_logging = target_user.id
        
        # 计算分页参数
        skip = (page - 1) * size
        
        # 获取该用户的所有订阅记录
        memberships = await crud_user_membership.get_multi_by_user_id(
            db, user_id=target_user.id, skip=skip, limit=size
        )
        
        # 构建响应
        membership_responses = [UserMembershipResponse.model_validate(membership) for membership in memberships]
        
        response_data = {
            "total": len(membership_responses),  # 简化处理
            "page": page,
            "size": size,
            "items": membership_responses
        }
        
        logger.info(f"成功查询用户订阅列表: admin_user_id={admin_user_id_for_logging}, target_user_id={target_user_id_for_logging}, count={len(memberships)}")
        return success_response(response_data)
        
    except Exception as e:
        logger.error(f"查询用户订阅列表失败: admin_user_id={admin_user_id_for_logging}, target_user_uuid={user_uuid}, error={e}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message='数据库查询错误')
        )


@router.post("/by-user/{user_uuid}", response_model=dict)
async def create_user_membership(
    user_uuid: uuid.UUID = Path(..., description="用户UUID"),
    subscription_in: UserMembershipCreateAdmin = ...,
    admin_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    (管理员/客服) 手动为用户赠送或补偿一个会员订阅
    """
    # 【安全日志准备】: 提取管理员信息到局部变量
    admin_user_id_for_logging = admin_user.id
    product_code_for_logging = subscription_in.product_code
    
    logger.info(f"管理员开始为用户创建订阅: admin_user_id={admin_user_id_for_logging}, target_user_uuid={user_uuid}, product_code={product_code_for_logging}")
    
    try:
        # 根据user_uuid找到user_id
        target_user = await crud_user.get_by_uuid(db, public_id=user_uuid)
        if not target_user:
            logger.warning(f"目标用户不存在: user_uuid={user_uuid}")
            return JSONResponse(
                status_code=404,
                content=error_response(code=2004, message='用户不存在')
            )
        
        # 【安全日志准备】: 提取目标用户信息到局部变量
        target_user_id_for_logging = target_user.id
        
        # 根据product_code查询产品信息
        product = await crud_membership_product.get_by_code(db, code=subscription_in.product_code)
        if not product:
            logger.warning(f"产品不存在: product_code={product_code_for_logging}")
            return JSONResponse(
                status_code=400,
                content=error_response(code=4001, message='指定的产品编码不存在')
            )
        
        # 构造UserMembershipCreate对象
        membership_create = UserMembershipCreate(
            user_id=target_user.id,
            product_code=subscription_in.product_code,
            transaction_id=subscription_in.transaction_id,
            level=product.level,
            status=MembershipStatus.ACTIVE,
            is_auto_renew=False,  # 手动创建的订阅默认不自动续费
            admin_notes=subscription_in.admin_notes,
            start_date=subscription_in.start_date,
            expires_at=subscription_in.expires_at
        )
        
        # 创建订阅记录
        try:
            new_membership = await crud_user_membership.create(db, obj_in=membership_create)
        except IntegrityError:
            # 用户已有同产品的有效订阅
            logger.warning(f"用户已有同类有效订阅: admin_user_id={admin_user_id_for_logging}, target_user_id={target_user_id_for_logging}, product_code={product_code_for_logging}")
            return JSONResponse(
                status_code=409,
                content=error_response(code=2005, message='用户已拥有一个正在生效的同类会员')
            )
        
        # 构建响应
        response_data = UserMembershipResponse.model_validate(new_membership)
        
        logger.info(f"成功为用户创建订阅: admin_user_id={admin_user_id_for_logging}, target_user_id={target_user_id_for_logging}, membership_id={new_membership.id}")
        return success_response(response_data)
        
    except Exception as e:
        logger.error(f"为用户创建订阅失败: admin_user_id={admin_user_id_for_logging}, target_user_uuid={user_uuid}, product_code={product_code_for_logging}, error={e}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message='数据库查询错误')
        )


@router.patch("/{subscription_uuid}", response_model=dict)
async def update_subscription(
    subscription_uuid: uuid.UUID = Path(..., description="订阅UUID"),
    subscription_update: UserMembershipUpdate = ...,
    admin_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    (管理员/客服) 手动更新一个订阅的状态或有效期
    """
    # 【安全日志准备】: 提取管理员信息到局部变量
    admin_user_id_for_logging = admin_user.id
    
    logger.info(f"管理员开始更新订阅: admin_user_id={admin_user_id_for_logging}, subscription_uuid={subscription_uuid}")
    
    try:
        # 根据subscription_uuid查询订阅记录
        subscription_to_update = await crud_user_membership.get_by_uuid(db, uuid=subscription_uuid)
        if not subscription_to_update:
            logger.warning(f"订阅记录不存在: subscription_uuid={subscription_uuid}")
            return JSONResponse(
                status_code=404,
                content=error_response(code=2004, message='订阅记录不存在')
            )
        
        # 【安全日志准备】: 提取订阅信息到局部变量
        subscription_id_for_logging = subscription_to_update.id
        subscription_user_id_for_logging = subscription_to_update.user_id
        
        # 更新订阅记录
        updated_subscription = await crud_user_membership.update(
            db, db_obj=subscription_to_update, obj_in=subscription_update
        )
        
        # 构建响应
        response_data = UserMembershipResponse.model_validate(updated_subscription)
        
        logger.info(f"成功更新订阅: admin_user_id={admin_user_id_for_logging}, subscription_id={subscription_id_for_logging}")
        return success_response(response_data)
        
    except Exception as e:
        logger.error(f"更新订阅失败: admin_user_id={admin_user_id_for_logging}, subscription_uuid={subscription_uuid}, error={e}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message='数据库查询错误')
        ) 
```

**3.3. 依赖的上下文**
*在重构过程中，你需要依赖以下模块*


  * `@app/crud/crud_user.py`
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

假设 `success_response()` 和 `error_response()` 已定义在 `app/core/responses.py` 中。

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

##### **5.1. 第一部分: `app/services/admin_subscriptions_service.py` (新文件)**

  * **指令**: 请为以下文件路径生成完整的 Python 代码：
    `app/services/admin_subscriptions_service.py`

  * **内容要求**:

      * 创建一个 `AdminSubscriptionsService` 类。
      * 将【3.2】中 `admin/subscriptions.py` 文件里的所有**业务逻辑**迁移到 `AdminSubscriptionsService` 的方法中。
      * **必须**定义清晰的业务异常类（例如 `TargetUserNotFoundError`, `ProductNotFoundError`, `ActiveSubscriptionExistsError`）。

  * **需在 `AdminSubscriptionsService` 类中实现的方法**:

    1.  **`get_subscriptions_by_user(self, user_uuid: uuid.UUID, page: int, size: int) -> dict`**:

          * **业务逻辑流程**:
            1.  **用户查询**: 调用 `crud_user.get_by_uuid()` 查找目标用户。如果未找到，`raise TargetUserNotFoundError()`。
            2.  **数据查询**: 调用 `crud_user_membership.get_multi_by_user_id()` 和 `count_by_user_id()` 获取该用户的订阅列表和总数。
            3.  **序列化与返回**: 将结果序列化并组装成分页格式的字典返回。

    2.  **`create_subscription_for_user(self, user_uuid: uuid.UUID, sub_create_request: schemas.UserMembershipCreateAdmin) -> models.UserMembership`**:

          * **业务逻辑流程**:
            1.  **用户查询**: 调用 `crud_user.get_by_uuid()` 查找目标用户。如果未找到，`raise TargetUserNotFoundError()`。
            2.  **产品查询**: 调用 `crud_membership_product.get_by_code()` 检查 `product_code` 是否有效。如果不存在，`raise ProductNotFoundError()`。
            3.  **构造Schema**: 将 `target_user.id` 和 `sub_create_request` 的数据组合成一个完整的 `schemas.UserMembershipCreate` 对象。
            4.  **创建记录**: 在 `try...except IntegrityError` 块中调用 `crud_user_membership.create()`。
            5.  **异常处理**: 如果捕获 `IntegrityError`，`raise ActiveSubscriptionExistsError("用户已拥有一个正在生效的同类会员")`。
            6.  返回成功创建的 `models.UserMembership` 对象。

    3.  **`update_subscription(self, subscription_uuid: uuid.UUID, sub_update_request: schemas.UserMembershipUpdate) -> models.UserMembership`**:

          * **业务逻辑流程**:
            1.  **数据查询**: 调用 `crud_user_membership.get_by_uuid()` 获取 `subscription_to_update` 对象。如果不存在，`raise SubscriptionNotFoundError()`。
            2.  **数据更新**: 调用 `crud_user_membership.update()` 更新订阅记录。
            3.  返回更新后的 `models.UserMembership` 对象。

##### **5.2. 第二部分: `app/api/v1/admin/subscriptions.py` (重构后的完整版)**

  * **指令**: 请为以下文件路径生成**重构后的**完整 Python 代码：
    `app/api/v1/admin/subscriptions.py`

  * **内容要求**:

      * 保留 `APIRouter` 和所有端点定义。
      * **重写**每个端点函数的内部实现，使其只包含对 `AdminSubscriptionsService` 的调用和响应处理。
      * **必须**遵循“主动变量提取”和安全异常处理模式。比如：比如：
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

  * **需重构的端点 (在 `app/api/v1/admin/subscriptions.py` 中)**:

    1.  **`GET /by-user/{user_uuid}` (获取指定用户的订阅列表)**

          * **重构实现流程**:
            1.  通过 `Depends(get_current_admin_user)` 获取 `admin_user` 对象。
            2.  **主动提取**: `admin_user_id_for_logging = admin_user.id`。
            3.  在 `try...except` 块中：
                  * a. 实例化 `admin_sub_service = AdminSubscriptionsService(db)`。
                  * b. 调用 `paginated_result = await admin_sub_service.get_subscriptions_by_user(...)`。
                  * c. 调用 `success_response` 返回 `paginated_result`。
            4.  **异常处理**:
                  * a. `except TargetUserNotFoundError as e`: 返回 `JSONResponse(status_code=404, content=error_response(code=2004, message=str(e)))`。
                  * b. `except Exception as e`: 返回 `500` 错误。

    2.  **`POST /by-user/{user_uuid}` (手动为用户创建订阅)**

          * **重构实现流程**:
            1.  获取 `admin_user` 和 `db` 依赖。
            2.  **主动提取**: `admin_user_id_for_logging = admin_user.id`。
            3.  在 `try...except` 块中：
                  * a. 实例化 `admin_sub_service = AdminSubscriptionsService(db)`。
                  * b. 调用 `new_subscription = await admin_sub_service.create_subscription_for_user(...)`。
                  * c. 序列化 `new_subscription` 并调用 `success_response` 返回。
            4.  **异常处理**:
                  * a. `except TargetUserNotFoundError as e`: 返回 `404` 错误。
                  * b. `except ProductNotFoundError as e`: 返回 `400` 错误。
                  * c. `except ActiveSubscriptionExistsError as e`: 返回 `409` 错误。
                  * d. `except Exception as e`: 返回 `500` 错误。

    3.  **`PATCH /{subscription_uuid}` (手动更新指定订阅)**

          * **重构实现流程**:
            1.  获取 `admin_user` 和 `db` 依赖。
            2.  **主动提取**: `admin_user_id_for_logging = admin_user.id`。
            3.  在 `try...except` 块中：
                  * a. 实例化 `admin_sub_service = AdminSubscriptionsService(db)`。
                  * b. 调用 `updated_subscription = await admin_sub_service.update_subscription(...)`。
                  * c. 序列化 `updated_subscription` 并调用 `success_response` 返回。
            4.  **异常处理**:
                  * a. `except SubscriptionNotFoundError as e`: 返回 `404` 错误。
                  * b. `except Exception as e`: 返回 `500` 错误。

#### **6. 最终交付 (Final Deliverable)**

请根据以上所有要求，为我生成以下**两个文件**的完整、可直接使用的 Python 代码。

1.  `app/services/admin_subscriptions_service.py` **(新文件)**
2.  `app/api/v1/admin/subscriptions.py` **(重构后的完整版)**