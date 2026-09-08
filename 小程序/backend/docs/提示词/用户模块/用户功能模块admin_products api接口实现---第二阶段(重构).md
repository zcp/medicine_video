


### **最终版：高效 AI 代码重构提示词 (Admin Products模块: 引入Service层)**

#### **1. 角色定义 (Role Definition)**

你是一名资深的 Python 后端架构师，精通分层架构设计（特别是 `Endpoint -> Service -> CRUD` 模式），并擅长将包含复杂业务逻辑的 FastAPI 端点，安全、高效地重构到独立的服务层中。

#### **2. 任务目标 (Task Objective)**

你的核心任务是**重构**现有的 `app/api/v1/admin/products.py` 文件。具体包括：

1.  **【新增文件】** 创建一个全新的**服务层**文件 `app/services/admin_products_service.py`。
2.  **【逻辑迁移】** 将 `admin/products.py` 中所有的**业务逻辑**（如唯一性检查、数据查询、序列化等）**完整地、安全地迁移**到新的 `AdminProductsService` 类中。
3.  **【重构文件】** **重写** `app/api/v1/admin/products.py` 文件，使其变得非常简洁。重构后的端点函数**严禁**包含任何业务逻辑，必须改为调用 `AdminProductsService` 中对应的方法。

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
│   │       │   ├── users.py        # <-- 已存在 (代码如下)
│   │       │   ├── products.py     # <-- 需要重构
│   │       │   └── subscriptions.py# <-- 已存在 (代码如下)
│   │       └── endpoints/
│   │           └── auth.py       # <-- 已存在 (代码如下)
│   │           └── users.py       #  <-- 已存在 (代码如下)
│   │           └── membership_products.py 已存在 (代码如下)
│   │           └── subscriptions.py # <-- 已存在 (代码如下)
│   ├── core/
│   │   └── redis_client.py         # <-- 已存在 (代码如下)
│   │   └── response.py         # <-- 已存在 (代码如下)
│   ├── crud/
│   ├── crud/
│   │   └── crud_user.py              # <-- 已存在 (代码如下)
│   │   └── crud_membership_product.py  # <-- 作为依赖
│   │   └── crud_user_membership.py   # <-- 已存在 (代码如下)
│   ├── models/
│   │   └── users.py    # <-- 已存在 (代码如下)
│   ├── schemas/
│   │   └── users.py    # <-- 已存在 (代码如下)
│   ├── services/                
│   │   ├── __init__.py
│   │   └── membership_products_service.py   # <-- 已存在 (代码如下)
│   │   └── admin_products_service.py   # <-- 目标文件 1 (新文件)
│   └── database.py         # <-- 已存在
```

**3.2. 需要被重构的源代码**
*你必须根据以下 `app/api/v1/admin/products.py` 的完整代码进行重构。*

* `@app/api/v1/admin/products.py`

```
"""
后台管理API - 会员产品管理
提供产品创建、查询、更新、删除等管理功能
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query, Path
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.database import get_async_db
from app.core.responses import success_response, error_response
from app.crud import crud_membership_product
from app.schemas.users import (
    MembershipProductResponse, MembershipProductCreate, MembershipProductUpdate,
    PaginatedMembershipProductsResponse
)
from app.models.users import User, MembershipProductStatus
from app.api.v1.deps import get_current_admin_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/membership-products", tags=["Admin - Products"])


@router.post("", response_model=dict)
async def create_product(
    product_in: MembershipProductCreate,
    admin_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    (管理员) 创建一个新的会员产品
    """
    # 【安全日志准备】: 提取管理员信息到局部变量
    admin_user_id_for_logging = admin_user.id
    product_code_for_logging = product_in.code
    
    logger.info(f"管理员开始创建会员产品: admin_user_id={admin_user_id_for_logging}, product_code={product_code_for_logging}")
    
    try:
        # 唯一性检查
        existing_product = await crud_membership_product.get_by_code(db, code=product_in.code)
        if existing_product:
            logger.warning(f"产品编码已存在: product_code={product_code_for_logging}")
            return JSONResponse(
                status_code=409,
                content=error_response(code=2001, message='产品编码已存在')
            )
        
        # 创建产品
        new_product = await crud_membership_product.create(db, obj_in=product_in)
        
        # 构建响应
        response_data = MembershipProductResponse.model_validate(new_product)
        
        logger.info(f"成功创建会员产品: admin_user_id={admin_user_id_for_logging}, product_code={product_code_for_logging}")
        return success_response(response_data)
        
    except Exception as e:
        logger.error(f"创建会员产品失败: admin_user_id={admin_user_id_for_logging}, product_code={product_code_for_logging}, error={e}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message='数据库查询错误')
        )


@router.get("", response_model=dict)
async def get_products_list(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=100, description="每页数量"),
    sort: Optional[str] = Query("created_at:desc", description="排序字段"),
    status: Optional[MembershipProductStatus] = Query(None, description="按产品状态筛选"),
    admin_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    (管理员) 分页获取所有会员产品，包括DRAFT、INACTIVE等非上线状态
    """
    # 【安全日志准备】: 提取管理员信息到局部变量
    admin_user_id_for_logging = admin_user.id
    
    logger.info(f"管理员开始查询会员产品列表: admin_user_id={admin_user_id_for_logging}, page={page}, size={size}")
    
    try:
        # 计算分页参数
        skip = (page - 1) * size
        
        # 数据查询
        total = await crud_membership_product.count_all(db)
        products = await crud_membership_product.get_multi_all(
            db, skip=skip, limit=size
        )
        
        # 如果有状态筛选，需要在应用层过滤（简化实现）
        if status:
            products = [p for p in products if p.status == status]
            total = len(products)
        
        # 构建响应
        product_responses = [MembershipProductResponse.model_validate(product) for product in products]
        
        response_data = {
            "total": total,
            "page": page,
            "size": size,
            "items": product_responses
        }
        
        logger.info(f"成功查询会员产品列表: admin_user_id={admin_user_id_for_logging}, total={total}, count={len(products)}")
        return success_response(response_data)
        
    except Exception as e:
        logger.error(f"查询会员产品列表失败: admin_user_id={admin_user_id_for_logging}, error={e}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message='数据库查询错误')
        )


@router.get("/{product_code}", response_model=dict)
async def get_product_detail(
    product_code: str = Path(..., description="产品编码"),
    admin_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    (管理员) 获取单个会员产品的全部信息，用于编辑页面
    """
    # 【安全日志准备】: 提取管理员信息到局部变量
    admin_user_id_for_logging = admin_user.id
    
    logger.info(f"管理员开始查询会员产品详情: admin_user_id={admin_user_id_for_logging}, product_code={product_code}")
    
    try:
        # 查询产品
        product = await crud_membership_product.get_by_code(db, code=product_code)
        if not product:
            logger.warning(f"会员产品不存在: product_code={product_code}")
            return JSONResponse(
                status_code=404,
                content=error_response(code=2004, message='会员产品不存在')
            )
        
        # 构建响应
        response_data = MembershipProductResponse.model_validate(product)
        
        logger.info(f"成功查询会员产品详情: admin_user_id={admin_user_id_for_logging}, product_code={product_code}")
        return success_response(response_data)
        
    except Exception as e:
        logger.error(f"查询会员产品详情失败: admin_user_id={admin_user_id_for_logging}, product_code={product_code}, error={e}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message='数据库查询错误')
        )


@router.patch("/{product_code}", response_model=dict)
async def update_product(
    product_code: str = Path(..., description="产品编码"),
    product_update: MembershipProductUpdate = ...,
    admin_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    (管理员) 更新一个已存在的会员产品
    """
    # 【安全日志准备】: 提取管理员信息到局部变量
    admin_user_id_for_logging = admin_user.id
    
    logger.info(f"管理员开始更新会员产品: admin_user_id={admin_user_id_for_logging}, product_code={product_code}")
    
    try:
        # 查询产品
        product_to_update = await crud_membership_product.get_by_code(db, code=product_code)
        if not product_to_update:
            logger.warning(f"会员产品不存在: product_code={product_code}")
            return JSONResponse(
                status_code=404,
                content=error_response(code=2004, message='会员产品不存在')
            )
        
        # 更新产品
        updated_product = await crud_membership_product.update(
            db, db_obj=product_to_update, obj_in=product_update
        )
        
        # 构建响应
        response_data = MembershipProductResponse.model_validate(updated_product)
        
        logger.info(f"成功更新会员产品: admin_user_id={admin_user_id_for_logging}, product_code={product_code}")
        return success_response(response_data)
        
    except Exception as e:
        logger.error(f"更新会员产品失败: admin_user_id={admin_user_id_for_logging}, product_code={product_code}, error={e}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message='数据库查询错误')
        )


@router.delete("/{product_code}", response_model=dict)
async def delete_product(
    product_code: str = Path(..., description="产品编码"),
    admin_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    (管理员) 删除一个会员产品
    注意：只有在没有任何用户订阅记录引用的情况下才能成功
    """
    # 【安全日志准备】: 提取管理员信息到局部变量
    admin_user_id_for_logging = admin_user.id
    
    logger.info(f"管理员开始删除会员产品: admin_user_id={admin_user_id_for_logging}, product_code={product_code}")
    
    try:
        # 尝试删除产品
        deleted_product = await crud_membership_product.remove(db, code=product_code)
        if not deleted_product:
            logger.warning(f"会员产品不存在: product_code={product_code}")
            return JSONResponse(
                status_code=404,
                content=error_response(code=2004, message='会员产品不存在')
            )
        
        logger.info(f"成功删除会员产品: admin_user_id={admin_user_id_for_logging}, product_code={product_code}")
        return success_response(data=None)
        
    except IntegrityError:
        # 产品仍被引用
        logger.warning(f"删除会员产品失败，仍被引用: admin_user_id={admin_user_id_for_logging}, product_code={product_code}")
        return JSONResponse(
            status_code=400,
            content=error_response(code=2006, message='无法删除仍被用户订阅引用的产品，请先将其归档(ARCHIVED)')
        )
    except Exception as e:
        logger.error(f"删除会员产品失败: admin_user_id={admin_user_id_for_logging}, product_code={product_code}, error={e}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message='数据库查询错误')
        ) 
```

**3.3. 依赖的上下文**
*在重构过程中，你需要依赖以下模块*

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
  - 在 `except` 块中，**必须使用这些局部变量**进行日志记录或错误处理，避免访问失效对象。比如，
  - 
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

##### **4.1. 服务层 (`AdminProductsService`) 设计规范**

  * **类化设计**: 在 `app/services/admin_products_service.py` 中创建一个 `AdminProductsService` 类。
  * **依赖注入**: `AdminProductsService` 的 `__init__` 方法应接收 `db: AsyncSession` 作为参数。
  * **职责**:
      * 封装管理员**创建、查询、更新和删除会员产品**的完整流程。

##### **4.2. 端点层 (`app/api/v1/admin/products.py`) 重构规范**

  * **保持简洁**: 重构后的端点函数体应该非常简短。
  * **职责**:
      * 只负责处理 FastAPI 的 `Depends` 和 `Query` 参数。
      * 实例化 `MembershipProductsService`。
      * 调用 `MembershipProductsService` 中对应的方法来执行业务逻辑。
      * 捕获 `Service` 层可能抛出的业务异常，并使用 `error_response` 将其转换为标准的 `JSONResponse`。
  * **禁止**: **严禁**在重构后的端点函数中直接调用 `crud_*` 模块或执行任何业务逻辑计算。

-----

#### **5. 具体代码生成指令 (Specific Code Generation Instructions)**

##### **5.1. 第一部分: `app/services/admin_products_service.py` (新文件)**

* **指令**: 请为以下文件路径生成完整的 Python 代码：
    `app/services/admin_products_service.py`

* **内容要求**:
    * 创建一个 `AdminProductsService` 类。
    * 将【3.2】中 `admin/products.py` 文件里的所有**业务逻辑**迁移到 `AdminProductsService` 的方法中。
    * **必须**定义清晰的业务异常类（例如 `ProductCodeExistsError`, `ProductNotFoundError`, `ProductInUseError`）。

* **需在 `AdminProductsService` 类中实现的方法**:

    1.  **`create_product(self, product_in: schemas.MembershipProductCreate) -> models.MembershipProduct`**:
        * **业务逻辑流程**:
            1.  **唯一性检查**: 调用 `crud_membership_product.get_by_code()` 检查 `product_in.code` 是否已存在。如果已存在，`raise ProductCodeExistsError("产品编码已存在")`。
            2.  **创建产品**: 调用 `crud_membership_product.create(db=self.db, obj_in=product_in)` 创建新产品。
            3.  返回新创建的 `models.MembershipProduct` 对象。

    2.  **`list_products(self, page: int, size: int, status: Optional[schemas.MembershipProductStatus]) -> dict`**:
        * **业务逻辑流程**:
            1.  计算分页参数 `skip = (page - 1) * size`。
            2.  **数据查询**: 调用 `crud_membership_product.count_all(self.db)` 和 `crud_membership_product.get_multi_all(self.db, skip=skip, limit=size)` 获取数据。
            3.  **应用筛选**: 如果 `status` 参数存在，在Python代码中对查询出的 `products` 列表进行过滤。
            4.  **序列化**: 将结果安全地序列化为 `List[schemas.MembershipProductResponse]`。
            5.  返回一个包含 `total`, `page`, `size`, `items` 的分页结果字典。

    3.  **`get_product(self, product_code: str) -> models.MembershipProduct`**:
        * **业务逻辑流程**:
            1.  **数据查询**: 调用 `crud_membership_product.get_by_code(self.db, code=product_code)` 获取产品。
            2.  如果产品不存在，`raise ProductNotFoundError("会员产品不存在")`。
            3.  返回查询到的 `models.MembershipProduct` 对象。

    4.  **`update_product(self, product_code: str, product_update: schemas.MembershipProductUpdate) -> models.MembershipProduct`**:
        * **业务逻辑流程**:
            1.  **数据查询**: 调用 `crud_membership_product.get_by_code(self.db, code=product_code)` 获取 `product_to_update` 对象。如果不存在，`raise ProductNotFoundError("会员产品不存在")`。
            2.  **数据更新**: 调用 `crud_membership_product.update(self.db, db_obj=product_to_update, obj_in=product_update)` 更新产品。
            3.  返回更新后的 `models.MembershipProduct` 对象。

    5.  **`delete_product(self, product_code: str) -> models.MembershipProduct`**:
        * **业务逻辑流程**:
            1.  在 `try...except IntegrityError` 块中，调用 `crud_membership_product.remove(self.db, code=product_code)`。
            2.  **异常处理**: 如果捕获 `IntegrityError` (表示产品仍被引用)，`raise ProductInUseError("无法删除仍被用户订阅引用的产品，请先将其归档(ARCHIVED)")`。
            3.  如果 `remove` 方法返回 `None` (表示产品一开始就不存在)，`raise ProductNotFoundError("会员产品不存在")`。
            4.  返回被成功删除的 `models.MembershipProduct` 对象。

##### **5.2. 第二部分: `app/api/v1/admin/products.py` (重构后的完整版)**

* **指令**: 请为以下文件路径生成**重构后的**完整 Python 代码：
    `app/api/v1/admin/products.py`

* **内容要求**:
    * 保留 `APIRouter` 和所有端点定义。
    * **重写**每个端点函数的内部实现，使其只包含对 `AdminProductsService` 的调用和响应处理。
    * **必须**遵循“主动变量提取”和安全异常处理模式。

      * **必须**遵循“主动变量提取”和安全异常处理模式。
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

* **需重构的端点 (在 `app/api/v1/admin/products.py` 中)**:

    1.  **`POST /` (创建新的会员产品)**
        * **重构实现流程**:
            1.  通过 `Depends(get_current_admin_user)` 获取 `admin_user` 对象。
            2.  **主动提取**: `admin_user_id_for_logging = admin_user.id`。
            3.  在 `try...except` 块中：
                * a. 实例化 `product_service = AdminProductsService(db)`。
                * b. 调用 `new_product = await product_service.create_product(product_in=product_in)`。
                * c. 序列化 `new_product` 并调用 `success_response` 返回。
            4.  **异常处理**:
                * a. `except ProductCodeExistsError as e`: 返回 `JSONResponse(status_code=409, content=error_response(code=2001, message=str(e)))`。
                * b. `except Exception as e`: 返回 `500` 错误。

    2.  **`GET /` (分页获取所有会员产品)**
        * **重构实现流程**:
            1.  获取 `admin_user` 和 `db` 依赖。
            2.  在 `try...except` 块中：
                * a. 实例化 `product_service = AdminProductsService(db)`。
                * b. 调用 `paginated_result = await product_service.list_products(page=page, size=size, status=status)`。
                * c. 调用 `success_response` 返回 `paginated_result`。
            3.  **异常处理**: 捕获通用异常并返回 `500` 错误。

    3.  **`GET /{product_code}` (获取单个会员产品详情)**
        * **重构实现流程**:
            1.  获取 `admin_user` 和 `db` 依赖。
            2.  在 `try...except` 块中：
                * a. 实例化 `product_service = AdminProductsService(db)`。
                * b. 调用 `product = await product_service.get_product(product_code=product_code)`。
                * c. 序列化 `product` 并调用 `success_response` 返回。
            4.  **异常处理**:
                * a. `except ProductNotFoundError as e`: 返回 `JSONResponse(status_code=404, content=error_response(code=2004, message=str(e)))`。
                * b. `except Exception as e`: 返回 `500` 错误。

    4.  **`PATCH /{product_code}` (更新会员产品信息)**
        * **重构实现流程**:
            1.  获取 `admin_user` 和 `db` 依赖。
            2.  在 `try...except` 块中：
                * a. 实例化 `product_service = AdminProductsService(db)`。
                * b. 调用 `updated_product = await product_service.update_product(product_code=product_code, product_update=product_update)`。
                * c. 序列化 `updated_product` 并调用 `success_response` 返回。
            4.  **异常处理**:
                * a. `except ProductNotFoundError as e`: 返回 `404` 错误。
                * b. `except Exception as e`: 返回 `500` 错误。

    5.  **`DELETE /{product_code}` (删除会员产品)**
        * **重构实现流程**:
            1.  获取 `admin_user` 和 `db` 依赖。
            2.  在 `try...except` 块中：
                * a. 实例化 `product_service = AdminProductsService(db)`。
                * b. 调用 `await product_service.delete_product(product_code=product_code)`。
                * c. 调用 `success_response` 返回 `data=None`。
            4.  **异常处理**:
                * a. `except ProductNotFoundError as e`: 返回 `404` 错误。
                * b. `except ProductInUseError as e`: 返回 `JSONResponse(status_code=400, content=error_response(code=2006, message=str(e)))`。
                * c. `except Exception as e`: 返回 `500` 错误。

#### **6. 最终交付 (Final Deliverable)**

请根据以上所有要求，为我生成以下**两个文件**的完整、可直接使用的 Python 代码。

1.  `app/services/admin_products_service.py` **(新文件)**
2.  `app/api/v1/admin/products.py` **(重构后的完整版)**