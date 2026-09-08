
-----

### 2\. 【最终完整版】高效 AI 测试代码生成提示词 (v5.3 - 全面修复版)

这是根据您的要求，将您提供的所有“补丁”有机融入您上传的 `_API_live_features.md` 文件后生成的最终版本。

-----

### 【最终完整版】高效 AI 测试代码生成提示词 (混合策略执行版)

#### 1\. 角色定义 (Role Definition - 执行者)

你是一名资深的 Python 测试架构师。你精通使用 `pytest`、`pytest-asyncio`、`httpx` 和 `pytest-mock`，并且是"混合测试策略"的专家。

你的任务是**读取**下面 `Section 6` 中提供的应用程序源代码，并**严格按照** `Section 2-5` 的"核心规则"和 `Section 7` 的"具体任务列表"，为它们生成一个**完整、健壮、可运行的 `pytest` 测试文件**。

-----

#### 2\. 核心测试哲学 (The Hybrid Testing Strategy - MANDATORY)

你**必须**根据被测试代码的层级，严格遵循以下混合测试策略。这是最高优先级指令。

| 测试目标层级 | 强制测试风格 | 核心工具 | 测试目标 (你必须验证什么？) |
| :--- | :--- | :--- | :--- |
| **API / Endpoint 层** | **实用派 (Pragmatic)** | `httpx.AsyncClient` + `db_session` + `async_session_factory` | **验证完整链路**：... JSON 响应... 以及*真实*的数据库状态变化（**注意**：必须使用**新会话**查询以避免缓存陷阱）。 |
| **Service (服务) 层** | **学院派 (Academic)** | `mocker` (Mock 掉 CRUD/I/O) | **验证业务逻辑**：*隔离地*测试权限检查、数据编排、以及自定义异常（`pytest.raises`）的抛出。 |
| **CRUD (数据) 层** | **实用派 (Pragmatic)** | `db_session` (真实数据库) | **验证数据库状态**：*必须*通过 `db.refresh()` 或**再次查询**来"证明"数据已被正确创建、更新或删除。 |

-----

#### 3\. 核心实现规范 (Core Implementation Requirements - MANDATORY)

所有生成的测试代码**必须**无条件遵守以下规范。

##### 3.1. 测试环境配置 (`conftest.py`)

  * 你必须假设 `conftest.py`（或 `app.db.session`）已经按如下方式配置好：
    1.  `setup_database` (scope="session", autouse=True): 自动创建和删除表。
    2.  `db_session` (scope="function"): 提供用于**测试准备 (Arrange)** 和 **CRUD 测试**的会话。
    3.  `async_client` (scope="function"): 提供 `httpx.AsyncClient`。
    4.  **`async_session_factory`**: (来自 `app.db.session` 或 `tests.conftest`) 提供了创建**全新独立会话**的能力，专用于在 API 测试的断言阶段验证数据库状态，以规避身份映射缓存。

##### 3.2. 结构化测试 (Arrange, Act, Assert)

  * 所有测试用例**必须**遵循"准备 (Arrange)"、"执行 (Act)"、"断言 (Assert)"的逻辑结构，并使用注释将其清晰分开。

##### 3.3. 严格的异步测试语法 (MANDATORY `async for` Syntax)

  * 所有使用异步 `pytest` Fixture (如 `db_session`, `async_client`) 的测试函数**必须**使用 `async for` 语法来解包。
  * *⚠️ 禁止的写法**：
      * 不得在 `async for` 外部调用数据库操作。
      * 不得直接使用 fixture 参数而不解包。
      * 不得在函数参数中添加类型提示（`db_session: AsyncSession`）。

<!-- end list -->

```python
# ✅ 正确的 CRUD 测试模板
@pytest.mark.asyncio
async def test_crud_operation(self, db_session):
    """测试描述"""
    async for db in db_session:
        # ...所有数据库逻辑必须在此块内...
        pass
```

```python
# ✅ 正确的 API + DB 组合测试模板
@pytest.mark.asyncio
async def test_api_with_db(self, async_client, db_session):
    """API 和数据库组合测试"""
    async for client in async_client:
        async for db in db_session:
            # ...所有组合测试逻辑必须在此嵌套块内...
            pass
```

##### 3.4. 测试数据隔离 (MANDATORY for Pragmatic Tests)

  * **指令**: 为了防止测试之间因违反数据库 `UNIQUE` 约束而产生冲突，所有唯一性字段（如 `username`, `email`, `product_code`）**必须**是随机生成的。
  * **实现**: **必须**导入 `Faker` 和 `uuid` (以及 `random` 和 `string`，如果需要)。
  * **具体要求 (Faker 范例)**:
      * **`username`**: `f"{fake.user_name()}_{uuid.uuid4().hex[:6]}"`
      * **`email`**: `fake.email()`
      * **`product_code`**: `f"PROD_{''.join(random.choices(string.ascii_uppercase + string.digits, k=10))}"`
  * **禁止硬编码**: **严禁**使用硬编码的字符串（如 `'usera'`）作为唯一性字段的值，除非测试目的就是为了验证重复性。

##### 3.5. [关键] 统一的用户身份解析规范 (MANDATORY - V5.1 修复)

**🚨（新增）API 层用户提取规范（JWT→UUID+Enum）**
**`current_user` 永远是一个 JWT payload `dict`，而不是 ORM `User` 模型**。

API 层必须使用以下模式解析：

```python
current_user: Dict = Depends(get_current_user)

user_id = uuid.UUID(current_user.get("user_id") or current_user.get("sub"))
role_str = current_user.get("role", "REGULAR").upper()
user_role = LiveRoomMessageUserRole.get(role_str, LiveRoomMessageUserRole.REGULAR)
```

**🚨（新增）Service 层用户参数规范**
Service 层方法**不得**接受实体类 `User`，**必须**统一为：

```python
async def some_action(
    self,
    user_id: UUID,
    user_role: LiveRoomMessageUserRole,
    ...
):
```

-----

#### 4\. 按层级生成的断言规范 (Assertion Rules by Layer)

你必须根据"核心测试哲学"（第 2 节）生成对应的断言逻辑。

##### 4.1. 实用派测试 (Pragmatic: CRUD & API)

  * **A. API 响应验证 (针对 API 测试)**:

      * **必须**同时验证 HTTP 状态码和完整的 JSON 响应结构（`code`, `message`, `data`）。
      * **必须**验证业务状态码（`response.json()["code"]`）和 `"data"` 内部的关键字段。
      * 对于失败响应，**必须**验证业务错误码（例如 `assert response.json()["code"] == 2001`）。

  * **B. 数据库状态验证 [关键修改]**

      * **(针对 CRUD 层测试)**:

          * 在**同一个** `db_session` 中执行的 `create()`, `update()`, `remove()` 操作，**必须**在操作后立即使用 `await db.refresh(obj)` 或**再次 `get(db, obj.id)`**，来验证数据已正确持久化。

      * **(针对 API / Endpoint 层测试)**:

          * **[关键禁令]**：在 `await client.patch(...)` 或 `client.post(...)`（它们使用*独立会话*）之后，**严禁**使用*原始的* `db_session`（用于 Arrange 阶段）来 `get()` 或查询对象。这样做**必定**会读取到 SQLAlchemy 身份映射（Identity Map）中的**陈旧缓存**，导致测试失败。

      * **[API 层正确验证方案]**: 要验证 API 调用后的数据库*真实*状态，**必须**选择以下两种方法之一：

        1.  **(首选 - 验证响应)**: **只断言** API 返回的 `response.json()["data"]` 中的内容是否正确（例如 `assert response.json()["data"]["title"] == "新标题"`）。
        2.  **(次选 - 验证数据库)**: **必须**导入 `async_session_factory`（见 3.1 节），创建一个**全新的、独立的会话**（`async with async_session_factory() as new_db:`），并使用这个 `new_db` 会话执行显式的 `select()` 语句来查询数据库，以获取**最新**数据。

##### 4.2. 学院派测试 (Academic: Service & I/O)

  * **A. 异常逻辑验证**:

      * **必须**使用 `with pytest.raises(TopicPermissionDeniedException):` 来验证在特定条件下是否正确抛出了**自定义业务异常**。

  * **B. 行为验证 (Mocks)**:

      * **必须**使用 `mock_crud.assert_called_once_with(...)` 来验证依赖是否被正确调用。
      * **[关键] Mock 路径规范 (MANDATORY)**:
          * 假设 Service 层使用别名导入 (`from app.crud import topic as crud_topic`)。
          * 测试代码在 `mocker.patch()` 中**必须**使用**原始模块路径** (`"app.crud.topic.create"`)。
          * **必须**为异步函数使用 `new_callable=AsyncMock`。
      * **示例**:
        ```python
        # Service 层 (app/services/my_service.py)
        # from app.crud import topic as crud_topic
        # await crud_topic.create(...)

        # 测试层 (tests/unit/test_my_service.py)
        @pytest.mark.asyncio
        async def test_service_create(mocker):
            # 1. 准备 (Arrange)
            # [关键] Mock 原始路径 "app.crud.topic.create"
            mock_create = mocker.patch(
                "app.crud.topic.create",
                new_callable=AsyncMock,
                return_value=mock_topic_object
            )
            # ...
            # 3. 断言 (Assert)
            mock_create.assert_called_once_with(...)
        ```

  * **C. [关键] 用户身份 Mock 规范 (V5.3 修复)**

      * **📌【新增段落：Service 层用户 Mock 的统一规范】**
      * **🚨（新增）Service 层测试中，禁止 mock User 实体**
      * Service 层方法必须采用统一签名 (见 3.5)：
        ```python
        user_id: UUID
        user_role: LiveRoomMessageUserRole
        ```
      * 因此测试**必须** mock：
        ```python
        user_id = uuid.uuid4()
        user_role = LiveRoomMessageUserRole.ADMIN
        ```
      * **不允许**：
        ```python
        mock_user = MagicMock()
        mock_user.public_id = ...
        mock_user.role = ...
        ```
      * 此模式将导致类型不匹配错误，并已在真实测试中引发失败。

##### 4.3. [关键] 异步 SQLAlchemy 会话的测试规范 (V5.2 修复)

**🚨（新增）异步 SQLAlchemy Session 的禁止操作**
在所有测试中：

**严禁使用**：

  * `db.expire_all()`
  * `db.expire(obj)`

因为这会触发 lazy loading，并在异步环境中引发：

`sqlalchemy.exc.MissingGreenlet`

**🚨（新增）避免 Identity Map 缓存污染**
若测试创建了对象（会话 A），但 API 在另一会话（B）修改了该对象：

  * 会话 A 再查询该 ID → 会直接命中缓存，无法看到最新值

**⭐ 正确验证最新数据库值的两种模式**

  * **最推荐方式**：完全依赖 API 返回 JSON，测试不访问数据库（见 `4.1.A`）。
  * **若必须访问数据库**：
      * 必须使用新的独立会话（见 `4.1.B`）。
      * `async with async_session_factory() as new_db:`
      * `stmt = select(Model).where(Model.id == id)`
      * `result = await new_db.execute(stmt)`
      * `obj = result.scalar_one_or_none()`
  * **⚠️ 警告**：不能在**同一个**测试会话中二次查询同一主键，否则会命中身份映射缓存。

-----

#### 5\. 工程与风格规范 (Engineering & Style Norms)

  * **RESTful 路径规范 (MANDATORY)**:
      * 在 `APIRouter` 中定义 `prefix` 时，**严禁**在末尾添加斜杠 (例如：`prefix="/rooms"`)。
      * 对于集合端点（`GET /rooms`, `POST /rooms`），**必须**在装饰器中使用 `path="/"`。

-----

#### 6\. [动态生成] 核心上下文与被测试代码 (Context & Code to Test)

##### 6.1. 被测试文件：`app/api/v1/endpoints/live_features.py` **[V5.3 修复]**

```python
"""
直播间 Tab 和 留言功能的 API Endpoint 层（学院派）

职责：
- 参数绑定和依赖注入
- 调用 Service 层
- 捕获自定义异常并转换为 HTTP 响应
- URL 拼接处理
- 严禁包含业务逻辑
"""

import uuid
import logging
from typing import List, Optional, Dict, Any # [V5.3 修复] 导入 Dict
from datetime import datetime

from fastapi import APIRouter, Depends, Query, Body, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_db # 假设
from app.core.deps import get_current_user  # [关键] 只导入 get_current_user
from app.core.responses import success_response, error_response
# [V5.3 修复] 导入 Enum 用于解析
from app.models.live_features import LiveRoomMessageUserRole
# [V5.3 修复] 不再需要 User 模型
# from app.models.user import User 

from app.services.live_features_service import TabService, MessageService
from app.schemas.live_features import (
    LiveRoomTabCreate,
    LiveRoomTabUpdate,
    LiveRoomTabResponse,
    LiveRoomMessageCreate,
    LiveRoomMessagePostResponse,
    LiveRoomMessageListResponseItem,
    PaginatedLiveRoomMessageResponse
)

# [关键] 导入所有需要捕获的异常
from app.exceptions import (
    TabNotFoundException,
    RoomNotFoundException,
    PermissionDeniedException,
    InvalidParameterException,
    DatabaseIntegrityException,
    DatabaseOperationException
)

logger = logging.getLogger(__name__)


# ==================== 路由器定义（学院派规范 5.3.C）====================
# 严禁在此处使用 prefix，prefix 由顶层 api_router 统一管理

admin_tab_router = APIRouter(tags=["Admin - Tabs"])
public_message_router = APIRouter(tags=["Public - Messages"])


# ==================== Admin Tab 管理端点 ====================

@admin_tab_router.get("/rooms/{room_id}/tabs")
async def list_room_tabs(
    room_id: uuid.UUID,
    request: Request,  # [关键] 注入 Request 用于 URL 拼接
    db: AsyncSession = Depends(get_async_db),
    current_user: Dict = Depends(get_current_user)  # [V5.3 修复]
):
    """
    获取房间的所有 Tab（管理员用）
    
    权限：仅限 ADMIN 和 SUPERADMIN
    """
    # [V5.3 修复] 身份解析 (规范 3.5)
    try:
        user_id = uuid.UUID(current_user.get("user_id") or current_user.get("sub"))
        role_str = current_user.get("role", "REGULAR").upper()
        user_role = LiveRoomMessageUserRole.get(role_str, LiveRoomMessageUserRole.REGULAR)
        # [学院派规范 5.1] 安全异步异常处理：提前提取日志变量
        admin_user_id_log = str(user_id)
        room_id_log = str(room_id)
    except (AttributeError, TypeError, ValueError) as e:
        logger.warning(f"JWT 解析失败: {e}")
        return JSONResponse(status_code=401, content=error_response(code=3001, message="Token 无效"))
    
    logger.info(f"Admin {admin_user_id_log} listing tabs for room {room_id_log}")
    
    try:
        # 调用 Service 层
        service = TabService(db)
        tabs, total = await service.list_tabs_for_admin(user_id=user_id, user_role=user_role, room_id=room_id)
        
        # [学院派规范 5.3.C] URL 拼接
        base_url = str(request.base_url).rstrip('/')
        tabs_with_urls = []
        for tab in tabs:
            tab_response = LiveRoomTabResponse.model_validate(tab)
            # 拼接 image_url
            if tab_response.image_url and not tab_response.image_url.startswith('http'):
                tab_response.image_url = f"{base_url}{tab_response.image_url}"
            tabs_with_urls.append(tab_response.model_dump())
        
        return success_response(data={"items": tabs_with_urls, "total": total})
    
    except PermissionDeniedException as e:
        # [学院派规范 5.3.C] 权限异常 -> 403
        logger.warning(f"Admin permission denied: user_id={admin_user_id_log}, error={str(e)}")
        return JSONResponse(
            status_code=403,
            content=error_response(code=3002, message=str(e))
        )
    
    except RoomNotFoundException as e:
        # [学院派规范 5.1] 资源不存在 -> 404
        logger.warning(f"Room not found: room_id={room_id_log}, error={str(e)}")
        return JSONResponse(
            status_code=404,
            content=error_response(code=2001, message=str(e))
        )
    
    except Exception as e:
        # [学院派规范 5.1] 未捕获异常 -> 500
        logger.error(f"Error listing tabs: user_id={admin_user_id_log}, room_id={room_id_log}, error={str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content=error_response(code=1000, message=f"内部错误: {str(e)}")
        )


@admin_tab_router.post("/rooms/{room_id}/tabs")
async def create_room_tab(
    room_id: uuid.UUID,
    obj_in: LiveRoomTabCreate = Body(...),
    request: Request = None,  # [关键] 注入 Request
    db: AsyncSession = Depends(get_async_db),
    current_user: Dict = Depends(get_current_user) # [V5.3 修复]
):
    """
    创建房间 Tab（管理员用）
    
    权限：仅限 ADMIN 和 SUPERADMIN
    """
    # [V5.3 修复] 身份解析 (规范 3.5)
    try:
        user_id = uuid.UUID(current_user.get("user_id") or current_user.get("sub"))
        role_str = current_user.get("role", "REGULAR").upper()
        user_role = LiveRoomMessageUserRole.get(role_str, LiveRoomMessageUserRole.REGULAR)
        # [学院派规范 5.1] 安全异步异常处理：提前提取日志变量
        admin_user_id_log = str(user_id)
        room_id_log = str(room_id)
        tab_key_log = obj_in.tab_key
    except (AttributeError, TypeError, ValueError) as e:
        logger.warning(f"JWT 解析失败: {e}")
        return JSONResponse(status_code=401, content=error_response(code=3001, message="Token 无效"))
    
    logger.info(f"Admin {admin_user_id_log} creating tab for room {room_id_log}, tab_key={tab_key_log}")
    
    try:
        # 调用 Service 层
        service = TabService(db)
        new_tab = await service.create_tab(user_id=user_id, user_role=user_role, room_id=room_id, obj_in=obj_in)
        
        # [学院派规范 5.3.C] URL 拼接
        tab_response = LiveRoomTabResponse.model_validate(new_tab)
        if request and tab_response.image_url and not tab_response.image_url.startswith('http'):
            base_url = str(request.base_url).rstrip('/')
            tab_response.image_url = f"{base_url}{tab_response.image_url}"
        
        return success_response(data=tab_response.model_dump())
    
    except PermissionDeniedException as e:
        logger.warning(f"Admin permission denied: user_id={admin_user_id_log}, error={str(e)}")
        return JSONResponse(
            status_code=403,
            content=error_response(code=3002, message=str(e))
        )
    
    except RoomNotFoundException as e:
        logger.warning(f"Room not found: room_id={room_id_log}, error={str(e)}")
        return JSONResponse(
            status_code=404,
            content=error_response(code=2001, message=str(e))
        )
    
    except InvalidParameterException as e:
        # [学院派规范] 业务参数错误 -> 400
        logger.warning(f"Invalid parameter: user_id={admin_user_id_log}, error={str(e)}")
        return JSONResponse(
            status_code=400,
            content=error_response(code=e.code, message=e.message)
        )
    
    except (DatabaseIntegrityException, DatabaseOperationException) as e:
        # [学院派规范] 数据库错误（来自 CRUD 层）-> 400
        logger.error(f"Database error creating tab: user_id={admin_user_id_log}, error={str(e)}")
        return JSONResponse(
            status_code=400,
            content=error_response(code=4001, message=f"数据库操作失败: {str(e)}")
        )
    
    except Exception as e:
        logger.error(f"Error creating tab: user_id={admin_user_id_log}, room_id={room_id_log}, error={str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content=error_response(code=1000, message=f"内部错误: {str(e)}")
        )


@admin_tab_router.patch("/tabs/{tab_id}")
async def update_room_tab(
    tab_id: uuid.UUID,
    obj_in: LiveRoomTabUpdate = Body(...),
    request: Request = None,  # [关键] 注入 Request
    db: AsyncSession = Depends(get_async_db),
    current_user: Dict = Depends(get_current_user) # [V5.3 修复]
):
    """
    更新房间 Tab（管理员用）
    
    权限：仅限 ADMIN 和 SUPERADMIN
    """
    # [V5.3 修复] 身份解析 (规范 3.5)
    try:
        user_id = uuid.UUID(current_user.get("user_id") or current_user.get("sub"))
        role_str = current_user.get("role", "REGULAR").upper()
        user_role = LiveRoomMessageUserRole.get(role_str, LiveRoomMessageUserRole.REGULAR)
        # [学院派规范 5.1] 安全异步异常处理：提前提取日志变量
        admin_user_id_log = str(user_id)
        tab_id_log = str(tab_id)
    except (AttributeError, TypeError, ValueError) as e:
        logger.warning(f"JWT 解析失败: {e}")
        return JSONResponse(status_code=401, content=error_response(code=3001, message="Token 无效"))
    
    logger.info(f"Admin {admin_user_id_log} updating tab {tab_id_log}")
    
    try:
        # 调用 Service 层
        service = TabService(db)
        updated_tab = await service.update_tab(user_id=user_id, user_role=user_role, tab_id=tab_id, obj_in=obj_in)
        
        # [学院派规范 5.3.C] URL 拼接
        tab_response = LiveRoomTabResponse.model_validate(updated_tab)
        if request and tab_response.image_url and not tab_response.image_url.startswith('http'):
            base_url = str(request.base_url).rstrip('/')
            tab_response.image_url = f"{base_url}{tab_response.image_url}"
        
        return success_response(data=tab_response.model_dump())
    
    except PermissionDeniedException as e:
        logger.warning(f"Admin permission denied: user_id={admin_user_id_log}, error={str(e)}")
        return JSONResponse(
            status_code=403,
            content=error_response(code=3002, message=str(e))
        )
    
    except TabNotFoundException as e:
        logger.warning(f"Tab not found: tab_id={tab_id_log}, error={str(e)}")
        return JSONResponse(
            status_code=404,
            content=error_response(code=2002, message=str(e))
        )
    
    except InvalidParameterException as e:
        logger.warning(f"Invalid parameter: user_id={admin_user_id_log}, error={str(e)}")
        return JSONResponse(
            status_code=400,
            content=error_response(code=e.code, message=e.message)
        )
    
    except (DatabaseIntegrityException, DatabaseOperationException) as e:
        logger.error(f"Database error updating tab: user_id={admin_user_id_log}, error={str(e)}")
        return JSONResponse(
            status_code=400,
            content=error_response(code=4001, message=f"数据库操作失败: {str(e)}")
        )
    
    except Exception as e:
        logger.error(f"Error updating tab: user_id={admin_user_id_log}, tab_id={tab_id_log}, error={str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content=error_response(code=1000, message=f"内部错误: {str(e)}")
        )


@admin_tab_router.delete("/tabs/{tab_id}")
async def delete_room_tab(
    tab_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: Dict = Depends(get_current_user) # [V5.3 修复]
):
    """
    删除房间 Tab（管理员用）
    
    权限：仅限 ADMIN 和 SUPERADMIN
    """
    # [V5.3 修复] 身份解析 (规范 3.5)
    try:
        user_id = uuid.UUID(current_user.get("user_id") or current_user.get("sub"))
        role_str = current_user.get("role", "REGULAR").upper()
        user_role = LiveRoomMessageUserRole.get(role_str, LiveRoomMessageUserRole.REGULAR)
        # [学院派规范 5.1] 安全异步异常处理：提前提取日志变量
        admin_user_id_log = str(user_id)
        tab_id_log = str(tab_id)
    except (AttributeError, TypeError, ValueError) as e:
        logger.warning(f"JWT 解析失败: {e}")
        return JSONResponse(status_code=401, content=error_response(code=3001, message="Token 无效"))
    
    logger.info(f"Admin {admin_user_id_log} deleting tab {tab_id_log}")
    
    try:
        # 调用 Service 层
        service = TabService(db)
        deleted_tab = await service.delete_tab(user_id=user_id, user_role=user_role, tab_id=tab_id)
        
        return success_response(data={"message": "Tab 删除成功", "tab_id": str(deleted_tab.id)})
    
    except PermissionDeniedException as e:
        logger.warning(f"Admin permission denied: user_id={admin_user_id_log}, error={str(e)}")
        return JSONResponse(
            status_code=403,
            content=error_response(code=3002, message=str(e))
        )
    
    except TabNotFoundException as e:
        logger.warning(f"Tab not found: tab_id={tab_id_log}, error={str(e)}")
        return JSONResponse(
            status_code=404,
            content=error_response(code=2002, message=str(e))
        )
    
    except Exception as e:
        logger.error(f"Error deleting tab: user_id={admin_user_id_log}, tab_id={tab_id_log}, error={str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content=error_response(code=1000, message=f"内部错误: {str(e)}")
        )


# ==================== Public 留言端点 ====================

@public_message_router.post("/{room_id}/messages")
async def send_message(
    room_id: uuid.UUID,
    obj_in: LiveRoomMessageCreate = Body(...),
    db: AsyncSession = Depends(get_async_db),
    current_user: Dict = Depends(get_current_user) # [V5.3 修复]
):
    """
    发送留言
    
    权限：所有登录用户
    限制：普通用户不能发送包含 URL 的留言
    """
    # [V5.3 修复] 身份解析 (规范 3.5)
    try:
        user_id = uuid.UUID(current_user.get("user_id") or current_user.get("sub"))
        role_str = current_user.get("role", "REGULAR").upper()
        user_role = LiveRoomMessageUserRole.get(role_str, LiveRoomMessageUserRole.REGULAR)
        # [学院派规范 5.1] 安全异步异常处理：提前提取日志变量
        user_id_log = str(user_id)
        user_role_log = str(user_role.value)
        room_id_log = str(room_id)
    except (AttributeError, TypeError, ValueError) as e:
        logger.warning(f"JWT 解析失败: {e}")
        return JSONResponse(status_code=401, content=error_response(code=3001, message="Token 无效"))
    
    logger.info(f"User {user_id_log} (role={user_role_log}) sending message to room {room_id_log}")
    
    try:
        # 调用 Service 层
        service = MessageService(db)
        new_msg = await service.create_message(user_id=user_id, user_role=user_role, room_id=room_id, obj_in=obj_in)
        
        # [关键] 响应规范（学院派 5.2）：使用 LiveRoomMessagePostResponse
        response_data = LiveRoomMessagePostResponse.model_validate(new_msg)
        
        return success_response(data=response_data.model_dump())
    
    except RoomNotFoundException as e:
        logger.warning(f"Room not found: room_id={room_id_log}, error={str(e)}")
        return JSONResponse(
            status_code=404,
            content=error_response(code=2001, message=str(e))
        )
    
    except InvalidParameterException as e:
        # [关键] 捕获 URL 过滤异常（code=4004）
        logger.warning(f"Invalid parameter: user_id={user_id_log}, error={str(e)}")
        return JSONResponse(
            status_code=400,
            content=error_response(code=e.code, message=e.message)
        )
    
    except (DatabaseIntegrityException, DatabaseOperationException) as e:
        logger.error(f"Database error creating message: user_id={user_id_log}, error={str(e)}")
        return JSONResponse(
            status_code=400,
            content=error_response(code=4001, message=f"数据库操作失败: {str(e)}")
        )
    
    except Exception as e:
        logger.error(f"Error sending message: user_id={user_id_log}, room_id={room_id_log}, error={str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content=error_response(code=1000, message=f"内部错误: {str(e)}")
        )


@public_message_router.get("/{room_id}/messages")
async def get_room_messages(
    room_id: uuid.UUID,
    page: int = Query(1, ge=1, description="页码，从 1 开始"),
    size: int = Query(20, ge=1, le=100, description="每页大小，最大 100"),
    since: Optional[datetime] = Query(None, description="获取该时间之后的留言"),
    db: AsyncSession = Depends(get_async_db)
):
    """
    获取房间留言列表（分页）
    
    权限：所有用户（包括未登录）
    """
    room_id_log = str(room_id)
    
    logger.info(f"Getting messages for room {room_id_log}, page={page}, size={size}")
    
    try:
        # 调用 Service 层
        service = MessageService(db)
        messages, total = await service.get_messages(room_id, page, size, since)
        
        # 转换为响应 Schema
        message_items = [
            LiveRoomMessageListResponseItem.model_validate(msg)
            for msg in messages
        ]
        
        # 构建分页响应
        paginated_data = PaginatedLiveRoomMessageResponse(
            total=total,
            page=page,
            size=size,
            items=message_items
        )
        
        return success_response(data=paginated_data.model_dump())
    
    except RoomNotFoundException as e:
        logger.warning(f"Room not found: room_id={room_id_log}, error={str(e)}")
        return JSONResponse(
            status_code=404,
            content=error_response(code=2001, message=str(e))
        )
    
    except Exception as e:
        logger.error(f"Error getting messages: room_id={room_id_log}, error={str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content=error_response(code=1000, message=f"内部错误: {str(e)}")
        )
```

##### 6.2. 依赖文件：`app/core/responses.py`

```python
"""
LiveCore Service - Response Utilities

This module contains utility functions for constructing standardized API responses.
"""

from datetime import datetime
from typing import Any


def success_response(data: Any, message: str = "success") -> dict:
    """
    构建标准的成功响应体
    
    Args:
        data: 响应数据
        message: 响应消息
        
    Returns:
        标准格式的响应字典
    """
    return {
        "code": 200,
        "message": message,
        "data": data,
        "timestamp": datetime.now().isoformat() + "Z"
    }


def error_response(code: int, message: str, data: Any = None) -> dict:
    """
    构建标准的错误响应体
    
    Args:
        code: 业务错误码
        message: 错误消息
        data: 错误详细数据
        
    Returns:
        标准格式的错误响应字典
    """
    return {
        "code": code,
        "message": message,
        "data": data,
        "timestamp": datetime.now().isoformat() + "Z"
    }
```

##### 6.3. 相关 Schema 文件

(已在前面的文档中提供，此处省略)

-----

#### 7\. [动态生成] 具体测试任务列表 (Dynamic-Generated Specific Test Tasks)

**你必须为 `Section 6` 中的代码严格生成以下所有测试用例：**

> **[测试目标层级]**: API / Endpoint 层
> **[强制测试风格]**: 实用派 (Pragmatic) - 使用真实 HTTP 客户端和数据库
> **[核心工具]**: `httpx.AsyncClient` + `db_session` + `async_session_factory`

-----

### A. 针对 Admin Tab 管理端点的测试（实用派） **[V5.3 修复]**

#### **端点 1: `GET /rooms/{room_id}/tabs` (list\_room\_tabs)**

1.  **`test_api_list_room_tabs_success`** (成功场景):

      * **准备 (Arrange)**:
          * 使用 `async_client` 和 `db_session`。
          * 在数据库中创建一个 `LiveRoom`。
          * 在数据库中创建 **3 个** `LiveRoomTab`（属于该房间）。
          * **[V5.3 修复]** 创建一个 **ADMIN** 用户的 `user_id` 和 `user_role`，并生成有效的 JWT Token (假设 `conftest.py` 提供了 `admin_auth_headers` fixture)。
      * **执行 (Act)**:
          * `GET /api/v1/admin/rooms/{room_id}/tabs`（带认证 header）。
      * **断言 (Assert)**:
          * **必须**断言 `response.status_code == 200`。
          * **必须**断言 `response.json()["code"] == 200`。
          * **必须**断言 `response.json()["data"]["total"] == 3`。
          * **必须**断言 `len(response.json()["data"]["items"]) == 3`。
          * **[关键] URL 拼接验证**: 如果 Tab 的 `image_url` 是相对路径，断言响应中的 `image_url` 已被拼接为完整 URL。

2.  **`test_api_list_room_tabs_permission_denied`** (权限不足场景):

      * **准备 (Arrange)**:
          * 创建一个 `LiveRoom`。
          * **[V5.3 修复]** 创建一个 **REGULAR** 用户的 `user_id` 和 `user_role`，并生成有效的 JWT Token (假设 `conftest.py` 提供了 `user_auth_headers` fixture)。
      * **执行 (Act)**:
          * `GET /api/v1/admin/rooms/{room_id}/tabs`。
      * **断言 (Assert)**:
          * **必须**断言 `response.status_code == 403`。
          * **必须**断言 `response.json()["code"] == 3002`（权限错误码）。

3.  **`test_api_list_room_tabs_room_not_found`** (房间不存在场景):

      * **准备 (Arrange)**:
          * 准备一个**不存在的** `room_id`。
          * **[V5.3 修复]** 获取 `admin_auth_headers`。
      * **执行 (Act)**:
          * `GET /api/v1/admin/rooms/{non_existent_room_id}/tabs`。
      * **断言 (Assert)**:
          * **必须**断言 `response.status_code == 404`。
          * **必须**断言 `response.json()["code"] == 2001`（资源不存在错误码）。

#### **端点 2: `POST /rooms/{room_id}/tabs` (create\_room\_tab)**

1.  **`test_api_create_room_tab_success`** (成功场景):

      * **准备 (Arrange)**:
          * 在数据库中创建一个 `LiveRoom`。
          * **[V5.3 修复]** 获取 `admin_auth_headers`。
          * 使用 `Faker` 生成随机 `tab_key` 和 `title`。
          * 准备 JSON payload（`tab_key`, `title`, `content_type="text"`, `text_content="测试"`, `sort_order=0`, `is_active=true`）。
      * **执行 (Act)**:
          * `POST /api/v1/admin/rooms/{room_id}/tabs`（带认证 header）。
      * **断言 (Assert)**:
          * **必须**断言 `response.status_code == 200`。
          * **必须**断言 `response.json()["code"] == 200`。
          * **必须**断言 `response.json()["data"]["tab_key"] == payload["tab_key"]`。
          * **[关键 (遵循 4.1.B/4.3)]** 导入 `async_session_factory`，**创建新会话** `new_db`，并用 `new_db` 查询数据库，断言 Tab 已被正确创建。

2.  **`test_api_create_room_tab_permission_denied`** (权限不足场景):

      * **准备 (Arrange)**:
          * 创建一个 `LiveRoom`。
          * **[V5.3 修复]** 获取 `user_auth_headers` (普通用户)。
          * 准备有效的 payload。
      * **执行 (Act)**:
          * `POST /api/v1/admin/rooms/{room_id}/tabs`。
      * **断言 (Assert)**:
          * **必须**断言 `response.status_code == 403`。
          * **必须**断言 `response.json()["code"] == 3002`。

3.  **`test_api_create_room_tab_invalid_content_type`** (参数无效场景):

      * **准备 (Arrange)**:
          * 创建一个 `LiveRoom` 和 **[V5.3 修复]** `admin_auth_headers`。
          * 准备 payload（`content_type="text"`, `text_content=None`）。
      * **执行 (Act)**:
          * `POST /api/v1/admin/rooms/{room_id}/tabs`。
      * **断言 (Assert)**:
          * **必须**断言 `response.status_code == 400`。
          * **必须**验证业务错误码（`response.json()["code"]`）。
          * **必须**验证错误消息包含 "text\_content"。

4.  **`test_api_create_room_tab_room_not_found`** (房间不存在场景):

      * **准备 (Arrange)**:
          * 准备一个不存在的 `room_id`。
          * **[V5.3 修复]** 获取 `admin_auth_headers`。
          * 准备有效的 payload。
      * **执行 (Act)**:
          * `POST /api/v1/admin/rooms/{non_existent_room_id}/tabs`。
      * **断言 (Assert)**:
          * **必须**断言 `response.status_code == 404`。
          * **必须**断言 `response.json()["code"] == 2001`。

#### **端点 3: `PATCH /tabs/{tab_id}` (update\_room\_tab)**

1.  **`test_api_update_room_tab_success`** (成功场景):

      * **准备 (Arrange)**:
          * 在数据库中创建一个 `LiveRoom` 和一个 `LiveRoomTab`。
          * **[V5.3 修复]** 获取 `admin_auth_headers`。
          * 准备 update payload（`title="新标题"`, `is_active=false`）。
      * **执行 (Act)**:
          * `PATCH /api/v1/admin/tabs/{tab_id}`。
      * **断言 (Assert)**:
          * **必须**断言 `response.status_code == 200`。
          * **必须**断言 `response.json()["code"] == 200`。
          * **必须**断言 `response.json()["data"]["title"] == "新标题"`。
          * **必须**断言 `response.json()["data"]["is_active"] == false`。
          * **[关键 (遵循 4.1.B/4.3)]** 导入 `async_session_factory`，**创建新会话** `new_db`，并用 `new_db` 查询数据库，断言 `title` 和 `is_active` 已更新。

2.  **`test_api_update_room_tab_permission_denied`** (权限不足场景):

      * **准备 (Arrange)**:
          * 创建一个 Tab 和 **[V5.3 修复]** `user_auth_headers` (普通用户)。
      * **执行 (Act)**:
          * `PATCH /api/v1/admin/tabs/{tab_id}`。
      * **断言 (Assert)**:
          * **必须**断言 `response.status_code == 403`。

3.  **`test_api_update_room_tab_not_found`** (Tab不存在场景):

      * **准备 (Arrange)**:
          * 准备一个不存在的 `tab_id`。
          * **[V5.3 修复]** 获取 `admin_auth_headers`。
      * **执行 (Act)**:
          * `PATCH /api/v1/admin/tabs/{non_existent_tab_id}`。
      * **断言 (Assert)**:
          * **必须**断言 `response.status_code == 404`。
          * **必须**断言 `response.json()["code"] == 2002`（Tab 不存在错误码）。

#### **端点 4: `DELETE /tabs/{tab_id}` (delete\_room\_tab)**

1.  **`test_api_delete_room_tab_success`** (成功场景):

      * **准备 (Arrange)**:
          * 在数据库中创建一个 `LiveRoom` 和一个 `LiveRoomTab`。
          * **[V5.3 修复]** 获取 `admin_auth_headers`。
          * 记录 `tab_id`。
      * **执行 (Act)**:
          * `DELETE /api/v1/admin/tabs/{tab_id}`。
      * **断言 (Assert)**:
          * **必须**断言 `response.status_code == 200`。
          * **必须**断言 `response.json()["code"] == 200`。
          * **[关键 (遵循 4.1.B/4.3)]** 导入 `async_session_factory`，**创建新会话** `new_db`，并用 `new_db` 查询数据库，**断言返回 `None`**（已删除）。

2.  **`test_api_delete_room_tab_permission_denied`** (权限不足场景):

      * **准备 (Arrange)**:
          * 创建一个 Tab 和 **[V5.3 修复]** `user_auth_headers` (普通用户)。
      * **执行 (Act)**:
          * `DELETE /api/v1/admin/tabs/{tab_id}`。
      * **断言 (Assert)**:
          * **必须**断言 `response.status_code == 403`。

3.  **`test_api_delete_room_tab_not_found`** (Tab不存在场景):

      * **准备 (Arrange)**:
          * 准备一个不存在的 `tab_id`。
          * **[V5.3 修复]** 获取 `admin_auth_headers`。
      * **执行 (Act)**:
          * `DELETE /api/v1/admin/tabs/{non_existent_tab_id}`。
      * **断言 (Assert)**:
          * **必须**断言 `response.status_code == 404`。
          * **必须**断言 `response.json()["code"] == 2002`。

-----

### B. 针对 Public 留言端点的测试（实用派） **[V5.3 修复]**

#### **端点 5: `POST /{room_id}/messages` (send\_message)**

1.  **`test_api_send_message_success`** (成功场景):

      * **准备 (Arrange)**:
          * 在数据库中创建一个 `LiveRoom`。
          * **[V5.3 修复]** 获取 `user_auth_headers` (普通用户)。
          * 使用 `Faker` 生成随机 `content`（不含 URL）。
          * 准备 JSON payload（`content="普通留言内容"`）。
      * **执行 (Act)**:
          * `POST /api/v1/rooms/{room_id}/messages`。
      * **断言 (Assert)**:
          * **必须**断言 `response.status_code == 200`。
          * **必须**断言 `response.json()["code"] == 200`。
          * **必须**断言 `response.json()["data"]["content"] == payload["content"]`。
          * **[关键] 响应 Schema 验证**: 断言响应包含 `id`, `room_id`, `user_role`, `content`, `created_at`（符合 `LiveRoomMessagePostResponse`，**不包含 `user_id`**）。
          * **[关键 (遵循 4.1.B/4.3)]** 导入 `async_session_factory`，**创建新会话** `new_db`，并用 `new_db` 查询数据库，断言留言已被正确创建。

2.  **`test_api_send_message_admin_with_url`** (管理员可发送URL):

      * **准备 (Arrange)**:
          * 创建一个 `LiveRoom` 和 **[V5.3 修复]** `admin_auth_headers`。
          * 准备 payload（`content="管理员留言 https://example.com"`）。
      * **执行 (Act)**:
          * `POST /api/v1/rooms/{room_id}/messages`。
      * **断言 (Assert)**:
          * **必须**断言 `response.status_code == 200`。
          * **必须**断言留言创建成功。

3.  **`test_api_send_message_regular_user_with_url_rejected`** (普通用户发送URL被拒绝):

      * **准备 (Arrange)**:
          * 创建一个 `LiveRoom` 和 **[V5.3 修复]** `user_auth_headers`。
          * 准备 payload（`content="包含URL https://evil.com"`）。
      * **执行 (Act)**:
          * `POST /api/v1/rooms/{room_id}/messages`。
      * **断言 (Assert)**:
          * **必须**断言 `response.status_code == 400`。
          * **[关键]** 断言 `response.json()["code"] == 4004`（URL 过滤错误码）。
          * **必须**验证错误消息包含 "URL"。

4.  **`test_api_send_message_room_not_found`** (房间不存在场景):

      * **准备 (Arrange)**:
          * 准备一个不存在的 `room_id`。
          * **[V5.3 修复]** 获取 `user_auth_headers`。
      * **执行 (Act)**:
          * `POST /api/v1/rooms/{non_existent_room_id}/messages`。
      * **断言 (Assert)**:
          * **必须**断言 `response.status_code == 404`。
          * **必须**断言 `response.json()["code"] == 2001`。

#### **端点 6: `GET /{room_id}/messages` (get\_room\_messages)**

1.  **`test_api_get_room_messages_success`** (成功场景):

      * **准备 (Arrange)**:
          * 在数据库中创建一个 `LiveRoom`。
          * 在数据库中创建 **5 个** `LiveRoomMessage`（属于该房间，`is_deleted=false`）。
          * **不需要认证**（公共端点）。
      * **执行 (Act)**:
          * `GET /api/v1/rooms/{room_id}/messages?page=1&size=10`。
      * **断言 (Assert)**:
          * **必须**断言 `response.status_code == 200`。
          * **必须**断言 `response.json()["code"] == 200`。
          * **必须**断言 `response.json()["data"]["total"] == 5`。
          * **必须**断言 `len(response.json()["data"]["items"]) == 5`。
          * **[关键] 响应 Schema 验证**: 断言每个 item 包含 `id`, `user_role`, `content`, `created_at`（符合 `LiveRoomMessageListResponseItem`，**不包含 `user_id`**）。
          * **[关键] 排序验证**: 断言返回的留言按 `created_at` 降序排列（最新在前）。

2.  **`test_api_get_room_messages_pagination`** (分页场景):

      * **准备 (Arrange)**:
          * 创建一个 `LiveRoom`。
          * 创建 **10 个** 留言。
      * **执行 (Act)**:
          * `GET /api/v1/rooms/{room_id}/messages?page=2&size=3`。
      * **断言 (Assert)**:
          * **必须**断言 `response.json()["data"]["total"] == 10`。
          * **必须**断言 `response.json()["data"]["page"] == 2`。
          * **必须**断言 `len(response.json()["data"]["items"]) == 3`（第 4-6 条）。

3.  **`test_api_get_room_messages_with_since_filter`** (时间过滤场景):

      * **准备 (Arrange)**:
          * 创建一个 `LiveRoom`。
          * 创建留言，手动设置不同的 `created_at`。
          * 记录中间时间点 `since_time`。
      * **执行 (Act)**:
          * `GET /api/v1/rooms/{room_id}/messages?page=1&size=10&since={since_time}`。
      * **断言 (Assert)**:
          * **必须**断言返回的留言都是在 `since_time` 之后创建的。

4.  **`test_api_get_room_messages_excludes_deleted`** (排除已删除留言):

      * **准备 (Arrange)**:
          * 创建一个 `LiveRoom`。
          * 创建 **3 个** 留言：2 个 `is_deleted=false`，1 个 `is_deleted=true`。
      * **执行 (Act)**:
          * `GET /api/v1/rooms/{room_id}/messages?page=1&size=10`。
      * **断言 (Assert)**:
          * **必须**断言 `response.json()["data"]["total"] == 2`（排除已删除）。
          * **必须**断言返回的留言都是 `is_deleted=false`。

5.  **`test_api_get_room_messages_room_not_found`** (房间不存在场景):

      * **准备 (Arrange)**:
          * 准备一个不存在的 `room_id`。
      * **执行 (Act)**:
          * `GET /api/v1/rooms/{non_existent_room_id}/messages?page=1&size=10`。
      * **断言 (Assert)**:
          * **必须**断言 `response.status_code == 404`。
          * **必须**断言 `response.json()["code"] == 2001`。

-----

### C. 测试类组织（推荐结构）

```python
class TestAdminTabAPI:
    """Admin Tab 管理 API 测试（实用派）"""
    
    # test_api_list_room_tabs_success
    # test_api_list_room_tabs_permission_denied
    # test_api_list_room_tabs_room_not_found
    # test_api_create_room_tab_success
    # test_api_create_room_tab_permission_denied
    # test_api_create_room_tab_invalid_content_type
    # test_api_create_room_tab_room_not_found
    # test_api_update_room_tab_success
    # test_api_update_room_tab_permission_denied
    # test_api_update_room_tab_not_found
    # test_api_delete_room_tab_success
    # test_api_delete_room_tab_permission_denied
    # test_api_delete_room_tab_not_found


class TestPublicMessageAPI:
    """Public 留言 API 测试（实用派）"""
    
    # test_api_send_message_success
    # test_api_send_message_admin_with_url
    # test_api_send_message_regular_user_with_url_rejected
    # test_api_send_message_room_not_found
    # test_api_get_room_messages_success
    # test_api_get_room_messages_pagination
    # test_api_get_room_messages_with_since_filter
    # test_api_get_room_messages_excludes_deleted
    # test_api_get_room_messages_room_not_found
```

-----

#### 8\. 交付物 (Deliverable - 执行者)

请根据**以上所有规范 (1-7)**，为 `Section 6` 中提供的代码生成**完整的 `pytest` 测试文件**。

  * **交付物**:
      * `tests/integration/test_api_live_features.py`
  * **指令**:
    1.  **遵循任务列表**: 严格按照 `Section 7` 中的列表生成所有指定的测试用例（**共 22 个测试用例**）。
    2.  **遵循所有规范**: 确保生成的代码 100% 遵循 `Section 2-5` (哲学, 语法, 断言, 风格)。
    3.  **实用派测试**: 本测试文件属于 API 层测试，**必须**使用真实的 HTTP 客户端（`async_client`）和数据库（`db_session`）。
    4.  **数据隔离**: 所有创建的测试数据**必须**使用 `Faker` 或 `uuid` 生成随机值。
    5.  **完整链路验证**: 所有成功场景**必须**同时验证 HTTP 响应和数据库状态（**遵循 `4.1.B` 和 `4.3` 的新会话规范**）。
    6.  **必须使用 `async for`**: 所有测试函数必须使用 `async for client in async_client:` 和 `async for db in db_session:` 嵌套语法。
    7.  **认证处理**: 需要认证的端点必须在 HTTP 请求中设置正确的认证 header（**假设 `conftest.py` 提供了 `admin_auth_headers` 和 `user_auth_headers` 两个 fixture**）。

-----

### 9\. 关键提示

#### 9.1. 认证 Header 设置示例 **[V5.3 修复]**

```python
# 假设 conftest.py 提供了 fixture
# async def admin_auth_headers() -> dict
# async def user_auth_headers() -> dict

# 1. 获取 Admin 认证
headers = await admin_auth_headers()
response = await client.get(
    f"/api/v1/admin/rooms/{room_id}/tabs",
    headers=headers
)

# 2. 获取 Regular User 认证
headers = await user_auth_headers()
response = await client.post(
    f"/api/v1/rooms/{room_id}/messages",
    headers=headers,
    json=payload
)
```

#### 9.2. 创建测试用户示例 **[V5.3 修复]**

(API 测试**不应**直接创建 `User` 模型。它**必须**依赖 `conftest.py` 提供的 `admin_auth_headers` 和 `user_auth_headers` fixtures。测试代码**不**需要知道 token 是如何生成的。)

#### 9.3. 数据库验证示例 **[V5.3 修复]**

```python
# 验证 Tab 更新成功
from sqlalchemy import select
from app.models.live_features import LiveRoomTab
# [关键] 假设从 conftest 导入
from tests.conftest import async_session_factory 

# 1. 断言 API 响应
assert response.status_code == 200
assert response.json()["data"]["title"] == "新标题"

# 2. [关键] 使用新会话验证数据库
async with async_session_factory() as new_db:
    stmt = select(LiveRoomTab).where(LiveRoomTab.id == tab_id)
    result = await new_db.execute(stmt)
    updated_tab_in_db = result.scalar_one_or_none()
    
    assert updated_tab_in_db is not None
    assert updated_tab_in_db.title == "新标题"
```

#### 9.4. URL 拼接验证示例

```python
# 假设 Tab 的 image_url 是相对路径
# (在 Arrange 阶段创建 tab 时设置)
tab_in_db.image_url = "/uploads/image.jpg"
await db.commit()

# ... 执行 Act ...
response_data = response.json()["data"]["items"][0]

# 验证响应中的 image_url 已被拼接为完整 URL
assert response_data["image_url"].startswith("http://") # 或 https://
assert "/uploads/image.jpg" in response_data["image_url"]
```

#### 9.5. 响应 Schema 安全性验证

```python
# 留言列表响应不应包含 user_id（安全要求）
message_item = response.json()["data"]["items"][0]
assert "user_id" not in message_item
assert "id" in message_item
assert "user_role" in message_item
assert "content" in message_item
assert "created_at" in message_item
```

-----

### 10\. 最终检查清单

生成的测试代码必须满足：

  - [ ] 包含完整的模块文档字符串
  - [ ] 导入所有必需模块（`pytest`, `uuid`, `Faker`, `httpx`, Models, Schemas, `select`, `async_session_factory`）
  - [ ] 使用 `async for client in async_client:` 和 `async for db in db_session:` 嵌套语法
  - [ ] 所有测试使用 AAA 结构（Arrange, Act, Assert）并注释分隔
  - [ ] 所有唯一性字段使用随机生成
  - [ ] 所有成功场景同时验证 HTTP 响应和数据库状态（**遵循 `4.1.B` 和 `4.3` 的新会话规范**）
  - [ ] 所有失败场景验证 HTTP 状态码和业务错误码
  - [ ] 包含 `Section 7` 中列出的所有 22 个测试用例
  - [ ] 所有测试函数包含清晰的 docstring
  - [ ] 测试类名为 `TestAdminTabAPI` 和 `TestPublicMessageAPI`
  - [ ] 认证端点**必须**使用 `admin_auth_headers` 或 `user_auth_headers` fixture
  - [ ] URL 过滤测试验证业务错误码为 `4004`
  - [ ] 留言列表响应验证不包含 `user_id` 字段（安全要求）
  - [ ] 分页测试验证 `page`, `size`, `total` 字段
  - [ ] 时间过滤测试验证 `since` 参数生效
  - [ ] **[V5.3 检查]** **没有** `db.expire_all()` 或 `db.expire()`。
  - [ ] **[V5.3 检查]** 数据库验证**必须**使用 `async_session_factory`。
  - [ ] **[V5.3 检查]** 测试**没有** mock `User` 对象或 `get_current_user`（API 测试是实用派）。

-----

**[测试代码生成提示词文档结束]**