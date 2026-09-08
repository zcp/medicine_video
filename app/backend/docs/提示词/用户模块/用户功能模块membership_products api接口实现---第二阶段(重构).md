

### **最终版：高效 AI 代码重构提示词 (MembershipProducts模块: 引入Service层)**

#### **1. 角色定义 (Role Definition)**

你是一名资深的 Python 后端架构师，精通分层架构设计（特别是 `Endpoint -> Service -> CRUD` 模式），并擅长将包含复杂业务逻辑的 FastAPI 端点，安全、高效地重构到独立的服务层中。

#### **2. 任务目标 (Task Objective)**

你的核心任务是**重构**现有的 `app/api/v1/endpoints/membership_products.py` 文件。具体包括：

1.  **【新增文件】** 创建一个全新的**服务层**文件 `app/services/membership_products_service.py`。
2.  **【逻辑迁移】** 将 `membership_products.py` 中所有的**业务逻辑**（如参数解析、数据查询和序列化）**完整地、安全地迁移**到新的 `MembershipProductsService` 类中。
3.  **【重构文件】** **重写** `app/api/v1/endpoints/membership_products.py` 文件，使其变得非常简洁。重构后的端点函数**严禁**包含任何业务逻辑，必须改为调用 `MembershipProductsService` 中对应的方法。

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
│   │       │   ├── products.py     # <-- 已存在 (代码如下)
│   │       │   └── subscriptions.py# <-- 已存在 (代码如下)
│   │       └── endpoints/
│   │           └── auth.py       # <-- 已存在 (代码如下)
│   │           └── users.py       #  <-- 已存在 (代码如下)
│   │           └── membership_products.py # <-- 需要重构
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
│   │   └── membership_products_service.py   # <-- 目标文件 1 (新文件)
│   └── database.py         # <-- 已存在
```

**3.2. 需要被重构的源代码**
*你必须根据以下 `membership_products.py` 的完整代码进行重构。*

  * `@app/api/v1/endpoints/membership_products.py`
```
"""
会员产品API端点 - 用户功能服务
实现会员产品公开接口
"""
import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_db
from app.core.responses import success_response, error_response
from app.crud import crud_membership_product
from app.schemas.users import MembershipProductResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/membership-products", tags=["Membership Products"])


@router.get("")
async def get_membership_products(
    sort: Optional[str] = Query(
        default="sort_order:asc",
        description="排序字段及顺序，格式: field:direction (如 price:desc)",
        example="sort_order:asc"
    ),
    db: AsyncSession = Depends(get_async_db)
):
    """
    获取可购买的会员产品列表
    
    公开接口，获取所有状态为 ACTIVE 的、可供用户购买的会员产品列表，
    通常用于价格或购买页面。
    
    Args:
        sort: 排序参数，格式为 field:direction
        db: 数据库会话
        
    Returns:
        会员产品列表响应
    """
    logger.info(f"开始处理获取会员产品列表请求: sort={sort}")
    
    try:
        # 参数处理 - 解析sort查询参数
        sort_field = "sort_order"
        sort_direction = "asc"
        
        if sort and ":" in sort:
            parts = sort.split(":")
            if len(parts) == 2:
                sort_field = parts[0].strip()
                sort_direction = parts[1].strip().lower()
                if sort_direction not in ["asc", "desc"]:
                    sort_direction = "asc"
        
        logger.info(f"解析排序参数: field={sort_field}, direction={sort_direction}")
        
        # 数据查询 - 调用CRUD层获取活跃的会员产品
        products = await crud_membership_product.get_multi_active(
            db, 
            sort=sort_field, 
            direction=sort_direction
        )
        
        # 构建响应 - 序列化为Pydantic模型
        serialized_products: List[MembershipProductResponse] = []
        for product in products:
            try:
                product_response = MembershipProductResponse.model_validate(product)
                serialized_products.append(product_response)
            except Exception as e:
                logger.warning(f"序列化会员产品失败: product_code={product.code}, error={e}")
                continue
        
        logger.info(f"成功获取会员产品列表: count={len(serialized_products)}")
        
        # 最终返回 - 使用success_response构建响应
        return success_response(data={
            "items": [product.model_dump() for product in serialized_products]
        })
        
    except Exception as e:
        logger.error(f"获取会员产品列表失败: error={e}")
        return JSONResponse(
            status_code=500,
            content=error_response(
                code=1002, 
                message="数据库查询错误",
                data={"error": "An unexpected database error occurred"}
            )
        ) 
```

**3.3. 依赖的上下文**
*在重构过程中，你需要依赖以下模块*

  * `@app/crud/crud_user.py`
  * `@app/models/users.py`
  * `@app/schemas/users.py`
  * `@app/core/responses.py`
  * `@app/core/redis_client.py`
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

##### **4.1. 服务层 (`MembershipProductsService`) 设计规范**

  * **类化设计**: 在 `app/services/membership_products_service.py` 中创建一个 `MembershipProductsService` 类。
  * **依赖注入**: `MembershipProductsService` 的 `__init__` 方法应接收 `db: AsyncSession` 作为参数。
  * **职责**:
      * 封装获取**可购买会员产品列表**的完整流程。

##### **4.2. 端点层 (`membership_products.py`) 重构规范**

  * **保持简洁**: 重构后的端点函数体应该非常简短。
  * **职责**:
      * 只负责处理 FastAPI 的 `Depends` 和 `Query` 参数。
      * 实例化 `MembershipProductsService`。
      * 调用 `MembershipProductsService` 中对应的方法来执行业务逻辑。
      * 捕获 `Service` 层可能抛出的业务异常，并使用 `error_response` 将其转换为标准的 `JSONResponse`。
  * **禁止**: **严禁**在重构后的端点函数中直接调用 `crud_*` 模块或执行任何业务逻辑计算。


-----

#### **5. 具体代码生成指令 (Specific Code Generation Instructions)**

##### **5.1. 第一部分: `app/services/membership_products_service.py` (新文件)**

  * **指令**: 请为以下文件路径生成完整的 Python 代码：
    `app/services/membership_products_service.py`

  * **内容要求**:

      * 创建一个 `MembershipProductsService` 类。
      * 将【3.2】中 `membership_products.py` 文件里的所有**业务逻辑**迁移到 `MembershipProductsService` 的方法中。
      * **必须**定义清晰的业务异常类（例如 `InvalidSortParameterError`）。

  * **需在 `MembershipProductsService` 类中实现的方法**:

    1.  **`get_active_products(self, sort: Optional[str]) -> List[schemas.MembershipProductResponse]`**:
          * **业务逻辑流程**:
            1.  **参数处理**:
                  * a. 解析 `sort` 查询参数，分离出 `sort_field` 和 `sort_direction`。
                  * b. 设置默认值为 `sort_order` 和 `asc`。
                  * c. 验证 `sort_direction` 是否为 `asc` 或 `desc` 之一，如果不是，则重置为 `asc`。
            2.  **数据查询**: 调用 `crud_membership_product.get_multi_active()` 并传入解析后的 `sort_field` 和 `sort_direction`，从数据库获取产品列表。
            3.  **序列化**: 将查询到的 SQLAlchemy 对象列表，逐一安全地序列化为 `List[schemas.MembershipProductResponse]`。
            4.  返回序列化后的 Pydantic 对象列表。

##### **5.2. 第二部分: `app/api/v1/endpoints/membership_products.py` (重构后的完整版)**

  * **指令**: 请为以下文件路径生成**重构后的**完整 Python 代码：
    `app/api/v1/endpoints/membership_products.py`

  * **内容要求**:

      * 保留 `APIRouter` 和 `GET /` 端点定义。
      * **重写** `get_membership_products` 函数的内部实现，使其只包含对 `MembershipProductsService` 的调用和响应处理。
      * **必须**遵循“主动变量提取”和安全异常处理模式。

  * **需重构的端点 (在 `app/api/v1/endpoints/membership_products.py` 中)**:

    1.  **`GET /` (获取可购买的会员产品列表)**
          * **重构实现流程**:
            1.  在 `try...except` 块中执行以下操作：
                  * a. 实例化 `product_service = MembershipProductsService(db)`。
                  * b. 调用 `products = await product_service.get_active_products(sort=sort)`。
                  * c. 调用 `success_response` 并传入 `{ "items": products }` 作为 `data`，返回最终的成功响应。
            2.  **异常处理**:
                  * a. `except Exception as e`: 记录 `error` 日志，并返回 `JSONResponse(status_code=500, content=error_response(code=1002, message='数据库查询错误'))`。

#### **6. 最终交付 (Final Deliverable)**

请根据以上所有要求，为我生成以下**两个文件**的完整、可直接使用的 Python 代码。

1.  `app/services/membership_products_service.py` **(新文件)**
2.  `app/api/v1/endpoints/membership_products.py` **(重构后的完整版)**