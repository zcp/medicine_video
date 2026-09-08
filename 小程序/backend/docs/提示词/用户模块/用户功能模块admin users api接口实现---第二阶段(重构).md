### **最终版：高效 AI 代码重构提示词 (Admin Users模块: 引入Service层)**

#### **1. 角色定义 (Role Definition)**

你是一名资深的 Python 后端架构师，精通分层架构设计（特别是 `Endpoint -> Service -> CRUD` 模式），并擅长将包含复杂业务逻辑的 FastAPI 端点，安全、高效地重构到独立的服务层中。

#### **2. 任务目标 (Task Objective)**

你的核心任务是**重构**现有的 `app/api/v1/admin/users.py` 文件。具体包括：

1.  **【新增文件】** 创建一个全新的**服务层**文件 `app/services/admin_user_service.py`。
2.  **【逻辑迁移】** 将 `admin/users.py` 中所有的**业务逻辑**（如用户查找、权限控制、数据构造等）**完整地、安全地迁移**到新的 `AdminUserService` 类中。
3.  **【重构文件】** **重写** `app/api/v1/admin/users.py` 文件，使其变得非常简洁。重构后的端点函数**严禁**包含任何业务逻辑，必须改为调用 `AdminUserService` 中对应的方法。

#### **3. 核心上下文信息 (Core Context Information)**

**3.1. 项目结构 (重构后)**

```
users/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── deps.py          # <-- 已存在 (代码如下)
│   │       ├── admin/              # <-- 
│   │       │   ├── __init__.py
│   │       │   ├── users.py        # <--  需要重构
│   │       │   ├── products.py     # <-- 已存在 (代码如下)
│   │       │   └── subscriptions.py# <-- 已存在 (代码如下)
│   │       └── endpoints/
│   │           └── auth.py       # <-- 已存在 (代码如下)
│   │           └── users.py       #  <-- 已存在 (代码如下)
│   │           └── membership_products.py # <-- 已存在 (代码如下)
│   │           └── subscriptions.py # <-- 已存在 (代码如下)
│   ├── core/
│   │   └── redis_client.py         # <-- 已存在 (代码如下)
│   │   └── response.py         # <-- 已存在 (代码如下)
│   ├── crud/
│   ├── crud/
│   │   └── crud_user.py              # <-- 已存在 (代码如下)
│   │   └── crud_membership_product.py  # <-- 已存在 (代码如下)
│   │   └── crud_user_membership.py   # <-- 已存在 (代码如下)
│   ├── models/
│   │   └── users.py    # <-- 已存在 (代码如下)
│   ├── schemas/
│   │   └── users.py    # <-- 已存在 (代码如下)
│   ├── services/                
│   │   ├── __init__.py
│   │   └── admin_user_service.py   # <-- 目标文件 1 (新文件)
│   └── database.py         # <-- 已存在
```

**3.2. 需要被重构的源代码**
*你必须根据以下 `users.py` 的完整代码进行重构。*
* `@app/api/v1/admin/users.py`
```
"""
后台管理API - 用户管理
提供用户查询、更新等管理功能
"""
import logging
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query, Path
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_db
from app.core.responses import success_response, error_response
from app.crud import crud_user
from app.schemas.users import (
    UserResponse, UserUpdate, UserFilterParams,
    PaginatedUsersResponse
)
from app.models.users import User, UserRole
from app.api.v1.deps import get_current_admin_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["Admin - Users"])


@router.get("", response_model=dict)
async def get_users_list(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=100, description="每页数量"),
    sort: Optional[str] = Query("created_at:desc", description="排序字段"),
    username: Optional[str] = Query(None, description="按用户名模糊搜索"),
    email: Optional[str] = Query(None, description="按邮箱精确搜索"),
    role: Optional[UserRole] = Query(None, description="按角色筛选"),
    status: Optional[str] = Query(None, description="按状态筛选"),
    admin_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    (管理员) 分页、排序、筛选获取系统中的所有用户列表
    """
    # 【安全日志准备】: 提取管理员信息到局部变量
    admin_user_id_for_logging = admin_user.id
    admin_username_for_logging = admin_user.username
    
    logger.info(f"管理员开始查询用户列表: admin_user_id={admin_user_id_for_logging}, page={page}, size={size}")
    
    try:
        # 构建筛选条件
        from app.models.users import EntityStatus
        filters = UserFilterParams(
            username=username,
            email=email,
            role=role,
            status=EntityStatus(status) if status else None
        )
        
        # 计算分页参数
        skip = (page - 1) * size
        
        # 数据查询
        total = await crud_user.count_with_filtering(db, filters=filters)
        users = await crud_user.get_multi_with_filtering(
            db, skip=skip, limit=size, filters=filters
        )
        
        # 构建响应
        user_responses = [UserResponse.model_validate(user) for user in users]
        
        response_data = {
            "total": total,
            "page": page,
            "size": size,
            "items": user_responses
        }
        
        logger.info(f"成功查询用户列表: admin_user_id={admin_user_id_for_logging}, total={total}, count={len(users)}")
        return success_response(response_data)
        
    except Exception as e:
        logger.error(f"查询用户列表失败: admin_user_id={admin_user_id_for_logging}, error={e}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message='数据库查询错误')
        )


@router.patch("/{user_uuid}", response_model=dict)
async def update_user(
    user_uuid: uuid.UUID = Path(..., description="用户UUID"),
    user_update: UserUpdate = ...,
    admin_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    (管理员) 更新指定用户的核心信息，如角色、状态
    """
    # 【安全日志准备】: 提取管理员信息到局部变量
    admin_user_id_for_logging = admin_user.id
    admin_role_for_logging = admin_user.role
    
    logger.info(f"管理员开始更新用户: admin_user_id={admin_user_id_for_logging}, target_user_uuid={user_uuid}")
    
    try:
        # 用户查询
        user_to_update = await crud_user.get_by_uuid(db, public_id=user_uuid)
        if not user_to_update:
            logger.warning(f"目标用户不存在: user_uuid={user_uuid}")
            return JSONResponse(
                status_code=404,
                content=error_response(code=2004, message='用户不存在')
            )
        
        # 【安全日志准备】: 提取目标用户信息到局部变量
        target_user_id_for_logging = user_to_update.id
        target_user_role_for_logging = user_to_update.role
        
        # 权限检查：ADMIN不能修改SUPERADMIN
        if (admin_user.role == UserRole.ADMIN and 
            user_to_update.role == UserRole.SUPERADMIN):
            logger.warning(f"管理员权限不足: admin_user_id={admin_user_id_for_logging}, target_user_role={target_user_role_for_logging}")
            return JSONResponse(
                status_code=403,
                content=error_response(code=3002, message='权限不足')
            )
        
        # 如果要修改角色，再次检查权限
        update_data = user_update.model_dump(exclude_unset=True)
        if "role" in update_data:
            new_role = update_data["role"]
            if (admin_user.role == UserRole.ADMIN and 
                new_role == UserRole.SUPERADMIN):
                logger.warning(f"管理员无权设置超级管理员角色: admin_user_id={admin_user_id_for_logging}")
                return JSONResponse(
                    status_code=403,
                    content=error_response(code=3002, message='权限不足')
                )
        
        # 数据更新
        updated_user = await crud_user.update(
            db, db_obj=user_to_update, obj_in=user_update
        )
        
        # 构建响应
        response_data = UserResponse.model_validate(updated_user)
        
        logger.info(f"成功更新用户: admin_user_id={admin_user_id_for_logging}, target_user_id={target_user_id_for_logging}")
        return success_response(response_data)
        
    except Exception as e:
        logger.error(f"更新用户失败: admin_user_id={admin_user_id_for_logging}, target_user_uuid={user_uuid}, error={e}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message='数据库查询错误')
        ) 
```


**3.3. 依赖的上下文**
*在重构过程中，你需要依赖以下模块*

  * `@app/crud/crud_user.py`
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

##### **4.1. 服务层 (`AdminUserService`) 设计规范**
* **类化设计**: 在 app/services/admin_user_service.py 中创建一个 AdminUserService 类。
* **依赖注入**: AdminUserService 的 __init__ 方法应接收 db: AsyncSession 作为参数。
* **职责**:
  * 封装管理员分页、筛选查询用户列表的流程。
  * 封装管理员更新指定用户信息（包括权限检查）的流程。

##### **4.2. 端点层 (`app/api/v1/admin/users.py`) 重构规范**

  * **保持简洁**: 重构后的端点函数体应该非常简短。
  * **职责**:
      * 只负责处理 FastAPI 的 `Request` 和 `Depends`。
      * 实例化 `UserService`。
      * 调用 `UserService` 中对应的方法来执行业务逻辑。
      * 捕获 `Service` 层抛出的业务异常，并使用 `error_response` 将其转换为标准的 `JSONResponse`。
  * **禁止**: **严禁**在重构后的端点函数中直接调用 `crud_*` 模块或执行任何业务逻辑计算。

-----

#### **5. 具体代码生成指令 (Specific Code Generation Instructions)**

##### **5.1. 第一部分: `app/services/admin_user_service.py` (新文件)**

  * **指令**: 请为以下文件路径生成完整的 Python 代码：
    `app/services/admin_user_service.py`

  * **内容要求**:

      * 创建一个 `AdminUserService` 类。
      * 将【3.2】中 `admin/users.py` 文件里的所有**业务逻辑**迁移到 `AdminUserService` 的方法中。
      * **必须**定义清晰的业务异常类（例如 `TargetUserNotFoundError`, `PermissionDeniedError`）。

  * **需在 `AdminUserService` 类中实现的方法**:

    1.  **`list_users(self, filters: schemas.UserFilterParams, page: int, size: int) -> dict`**:

          * **业务逻辑流程**:
            1.  计算分页参数 `skip = (page - 1) * size`。
            2.  **数据查询**:
                  * a. 调用 `crud_user.count_with_filtering(self.db, filters=filters)` 获取筛选后的用户总数。
                  * b. 调用 `crud_user.get_multi_with_filtering(self.db, skip=skip, limit=size, filters=filters)` 获取当页的用户列表。
            3.  **序列化**: 将查询到的 SQLAlchemy 对象列表，逐一安全地序列化为 `List[schemas.UserResponse]`。
            4.  返回一个包含 `total`, `page`, `size`, `items` 的分页结果字典。

    2.  **`update_user_by_admin(self, admin_user: models.User, user_uuid: uuid.UUID, user_update: schemas.UserUpdate) -> models.User`**:

          * **业务逻辑流程**:
            1.  **用户查询**: 调用 `crud_user.get_by_uuid(self.db, public_id=user_uuid)` 获取目标用户 `user_to_update`。如果未找到，`raise TargetUserNotFoundError()`。
            2.  **权限检查 (静态)**: 检查 `admin_user` 的角色是否有权限修改 `user_to_update` 的角色。如果 `admin_user.role` 是 `ADMIN` 且 `user_to_update.role` 是 `SUPERADMIN`，`raise PermissionDeniedError("管理员无权修改超级管理员")`。
            3.  **权限检查 (动态)**: 检查 `user_update` 数据中是否包含对 `role` 字段的修改。如果包含，且 `admin_user` 试图将一个普通用户提升为 `SUPERADMIN`，同样 `raise PermissionDeniedError("管理员无权设置超级管理员角色")`。
            4.  **数据更新**: 调用 `crud_user.update(self.db, db_obj=user_to_update, obj_in=user_update)` 更新用户信息。
            5.  返回更新后的 `models.User` 对象。

##### **5.2. 第二部分: `app/api/v1/admin/users.py` (重构后的完整版)**

  * **指令**: 请为以下文件路径生成**重构后的**完整 Python 代码：
    `app/api/v1/admin/users.py`

  * **内容要求**:

      * 保留 `APIRouter` 和所有端点定义。
      * **重写**每个端点函数的内部实现，使其只包含对 `AdminUserService` 的调用和响应处理。
      * **必须**遵循“主动变量提取”和安全异常处理模式。 比如：
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


  * **需重构的端点 (在 `app/api/v1/admin/users.py` 中)**:

    1.  **`GET /` (分页获取用户列表)**

          * **重构实现流程**:
            1.  通过 `Depends(get_current_admin_user)` 获取 `admin_user` 对象。
            2.  **主动提取**: `admin_user_id_for_logging = admin_user.id`。
            3.  在 `try...except` 块中：
                  * a. 实例化 `admin_user_service = AdminUserService(db)`。
                  * b. 将所有`Query`参数聚合到一个 `schemas.UserFilterParams` 实例中。
                  * c. 调用 `paginated_result = await admin_user_service.list_users(...)`。
                  * d. 调用 `success_response` 返回 `paginated_result`。
            4.  **异常处理**: 捕获通用异常并返回 `500` 错误。

    2.  **`PATCH /{user_uuid}` (更新指定用户信息)**

          * **重构实现流程**:
            1.  通过 `Depends(get_current_admin_user)` 获取 `admin_user` 对象。
            2.  **主动提取**: `admin_user_id_for_logging = admin_user.id`。
            3.  在 `try...except` 块中：
                  * a. 实例化 `admin_user_service = AdminUserService(db)`。
                  * b. 调用 `updated_user = await admin_user_service.update_user_by_admin(...)`。
                  * c. 序列化 `updated_user` 并调用 `success_response` 返回。
            4.  **异常处理**:
                  * a. `except TargetUserNotFoundError as e`: 返回 `JSONResponse(status_code=404, content=error_response(code=2004, message=str(e)))`。
                  * b. `except PermissionDeniedError as e`: 返回 `JSONResponse(status_code=403, content=error_response(code=3002, message=str(e)))`。
                  * c. `except Exception as e`: 返回 `500` 错误。

#### **6. 最终交付 (Final Deliverable)**

请根据以上所有要求，为我生成以下**两个文件**的完整、可直接使用的 Python 代码。

1.  `app/services/admin_user_service.py` **(新文件)**
2.  `app/api/v1/admin/users.py` **(重构后的完整版)**