
### 2\. 【完整版】高效 AI 测试代码生成提示词 (v5.3 - 全面修复版)

这是根据您的要求，将您提供的所有“补丁”有机融入您上传的 `_Service_live_features.md` 文件后生成的最终版本。

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
    2.  `db_session` (scope="function"): 提供 `AsyncSession` 并自动 `rollback`。
    3.  `async_client` (scope="function"): 提供 `httpx.AsyncClient`。
    4.  **`async_session_factory`**: (来自 `app.db.session` 或 `tests.conftest`) 提供了创建**全新独立会话**的能力，专用于在 API 测试的断言阶段验证数据库状态，以规避身份映射缓存。

##### 3.2. 结构化测试 (Arrange, Act, Assert)

  * 所有测试用例**必须**遵循"准备 (Arrange)"、"执行 (Act)"、"断言 (Assert)"的逻辑结构，并使用注释将其清晰分开。

##### 3.3. 严格的异步测试语法 (MANDATORY `async for` Syntax)

  * 所有使用异步 `pytest` Fixture (如 `db_session`, `async_client`) 的测试函数**必须**使用 `async for` 语法来解包。
  * **⚠️ 禁止的写法**：
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
          * 假设 Service 层使用别名导入 (`from app.crud import live_features as crud_live_features`)。
          * 测试代码在 `mocker.patch()` 中**必须**使用**原始模块路径** (`"app.crud.live_features.create_tab"`)。
          * **必须**为异步函数使用 `new_callable=AsyncMock`。
      * **示例**:
        ```python
        # Service 层 (app/services/live_features_service.py)
        # from app.crud import live_features as crud_live_features
        # await crud_live_features.create_tab(...)

        # 测试层 (tests/unit/test_service_live_features.py)
        @pytest.mark.asyncio
        async def test_service_create(mocker):
            # 1. 准备 (Arrange)
            # [关键] Mock 原始路径 "app.crud.live_features.create_tab"
            mock_create = mocker.patch(
                "app.crud.live_features.create_tab",
                new_callable=AsyncMock,
                return_value=mock_tab_object
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

##### 6.1. 被测试文件：`app/services/live_features_service.py` **[V5.3 修复]**

```python
"""
直播间 Tab 和 留言功能的 Service 层（学院派）

职责：
- 业务逻辑验证（权限检查, URL 过滤, 状态校验）
- 组合 CRUD 操作
- 抛出自定义 Python 异常（e.g., TabNotFoundException）
- [V5.3 修复] 接收 user_id 和 user_role，而不是 User 对象
- 严禁处理事务（db.commit/rollback）
- 严禁抛出 HTTPException
"""

import uuid
import logging
import re
from typing import List, Optional, Tuple
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

# [学院派] 导入 CRUD 模块
from app.crud import live_features as crud_live_features
from app.crud import room as crud_room  # 用于检查 Room 是否存在

from app.models.live_features import (
    LiveRoomTab, 
    LiveRoomMessage, 
    LiveRoomMessageUserRole, 
    LiveRoomTabContentType
)
from app.models.live_core import LiveRoom  # 导入 LiveRoom
from app.schemas.live_features import (
    LiveRoomTabCreate, 
    LiveRoomTabUpdate, 
    LiveRoomMessageCreate, 
    LiveRoomMessageCreateInternal
)
# [V5.3 修复] 不再需要导入 User 模型
# from app.models.user import User

# [学院派] 导入自定义异常
from app.exceptions import (
    TabNotFoundException,
    RoomNotFoundException,
    PermissionDeniedException,
    InvalidParameterException
)

logger = logging.getLogger(__name__)

# URL 匹配正则表达式（用于留言）
URL_REGEX = re.compile(
    r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
)


class TabService:
    """Tab 相关业务逻辑"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def _check_room_exists(self, room_id: uuid.UUID) -> LiveRoom:
        """
        辅助函数：检查房间是否存在
        
        Args:
            room_id: 房间 ID
        
        Returns:
            LiveRoom: 房间对象
        
        Raises:
            RoomNotFoundException: 房间不存在
        """
        room = await crud_room.get(self.db, room_id)
        if room is None:
            raise RoomNotFoundException(f"Room ID: {room_id} 不存在")
        return room
    
    async def _check_admin_permission(self, user_role: LiveRoomMessageUserRole) -> None:
        """
        [V5.3 修复] 辅助函数：检查管理员权限
        
        Args:
            user_role: 用户角色 Enum
        
        Raises:
            PermissionDeniedException: 权限不足
        """
        # [学院派规范 5.3.B / V5.3 修复] 权限检查
        if user_role not in [LiveRoomMessageUserRole.ADMIN, LiveRoomMessageUserRole.SUPERADMIN]:
            raise PermissionDeniedException("无权操作 Tab")
    
    async def list_tabs_for_admin(
        self,
        user_id: uuid.UUID, # [V5.3 修复]
        user_role: LiveRoomMessageUserRole, # [V5.3 修复]
        room_id: uuid.UUID
    ) -> Tuple[List[LiveRoomTab], int]:
        """
        获取指定房间的所有 Tab（管理员用）
        
        Args:
            user_id: 当前用户 ID
            user_role: 当前用户角色
            room_id: 房间 ID
        
        Returns:
            Tuple[List[LiveRoomTab], int]: (Tab 列表, 总数)
        
        Raises:
            PermissionDeniedException: 权限不足
            RoomNotFoundException: 房间不存在
        """
        # 1. 权限检查
        await self._check_admin_permission(user_role)
        
        # 2. 检查房间是否存在
        await self._check_room_exists(room_id)
        
        # 3. 获取所有 Tab（暂不分页，获取前100个）
        tabs, total = await crud_live_features.get_all_by_room_id(self.db, room_id, skip=0, limit=100)
        
        logger.info(f"Admin user {user_id} listed {len(tabs)} tabs for room {room_id}")
        return tabs, total
    
    async def get_active_tabs_for_room(self, room_id: uuid.UUID) -> List[LiveRoomTab]:
        """
        获取指定房间的所有激活的 Tab（前端展示用）
        
        Args:
            room_id: 房间 ID
        
        Returns:
            List[LiveRoomTab]: 激活的 Tab 列表
        
        Raises:
            RoomNotFoundException: 房间不存在
        """
        # 1. 检查房间是否存在（确保房间存在，即使是公共访问）
        await self._check_room_exists(room_id)
        
        # 2. 获取激活的 Tab
        tabs = await crud_live_features.get_active_by_room_id(self.db, room_id)
        
        logger.info(f"Retrieved {len(tabs)} active tabs for room {room_id}")
        return tabs
    
    async def create_tab(
        self, 
        user_id: uuid.UUID, # [V5.3 修复]
        user_role: LiveRoomMessageUserRole, # [V5.3 修复]
        room_id: uuid.UUID, 
        obj_in: LiveRoomTabCreate
    ) -> LiveRoomTab:
        """
        创建新的 Tab
        
        Args:
            user_id: 当前用户 ID
            user_role: 当前用户角色
            room_id: 房间 ID
            obj_in: Tab 创建数据
        
        Returns:
            LiveRoomTab: 创建的 Tab 对象
        
        Raises:
            PermissionDeniedException: 权限不足
            RoomNotFoundException: 房间不存在
            InvalidParameterException: 参数无效
        """
        # 1. 权限检查
        await self._check_admin_permission(user_role)
        
        # 2. 检查房间是否存在
        await self._check_room_exists(room_id)
        
        # 3. 参数校验：content_type 与内容匹配
        if obj_in.content_type == LiveRoomTabContentType.TEXT and not obj_in.text_content:
            raise InvalidParameterException("当 content_type=text 时, text_content 不能为空")
        
        if obj_in.content_type == LiveRoomTabContentType.IMAGE and not obj_in.image_url:
            raise InvalidParameterException("当 content_type=image 时, image_url 不能为空")
        
        if obj_in.content_type == LiveRoomTabContentType.MIXED:
            if not obj_in.text_content and not obj_in.image_url:
                raise InvalidParameterException("当 content_type=mixed 时, text_content 和 image_url 至少需要一个")
        
        # 4. 调用 CRUD 层创建
        new_tab = await crud_live_features.create_tab(self.db, obj_in, room_id)
        
        logger.info(f"Admin user {user_id} created tab {new_tab.id} for room {room_id}")
        return new_tab
    
    async def update_tab(
        self, 
        user_id: uuid.UUID, # [V5.3 修复]
        user_role: LiveRoomMessageUserRole, # [V5.3 修复]
        tab_id: uuid.UUID, 
        obj_in: LiveRoomTabUpdate
    ) -> LiveRoomTab:
        """
        更新 Tab
        
        Args:
            user_id: 当前用户 ID
            user_role: 当前用户角色
            tab_id: Tab ID
            obj_in: 更新数据
        
        Returns:
            LiveRoomTab: 更新后的 Tab 对象
        
        Raises:
            PermissionDeniedException: 权限不足
            TabNotFoundException: Tab 不存在
            InvalidParameterException: 参数无效
        """
        # 1. 权限检查
        await self._check_admin_permission(user_role)
        
        # 2. 获取 Tab
        db_tab = await crud_live_features.get_tab(self.db, tab_id)
        if db_tab is None:
            raise TabNotFoundException(f"Tab ID: {tab_id} 不存在")
        
        # 3. 参数校验（可选，如果提供了 content_type）
        if obj_in.content_type is not None:
            # 获取更新后的值
            new_content_type = obj_in.content_type
            new_text_content = obj_in.text_content if obj_in.text_content is not None else db_tab.text_content
            new_image_url = obj_in.image_url if obj_in.image_url is not None else db_tab.image_url
            
            if new_content_type == LiveRoomTabContentType.TEXT and not new_text_content:
                raise InvalidParameterException("当 content_type=text 时, text_content 不能为空")
            
            if new_content_type == LiveRoomTabContentType.IMAGE and not new_image_url:
                raise InvalidParameterException("当 content_type=image 时, image_url 不能为空")
        
        # 4. 调用 CRUD 层更新
        updated_tab = await crud_live_features.update_tab(self.db, db_tab, obj_in)
        
        logger.info(f"Admin user {user_id} updated tab {tab_id}")
        return updated_tab
    
    async def delete_tab(
        self, 
        user_id: uuid.UUID, # [V5.3 修复]
        user_role: LiveRoomMessageUserRole, # [V5.3 修复]
        tab_id: uuid.UUID
    ) -> LiveRoomTab:
        """
        删除 Tab
        
        Args:
            user_id: 当前用户 ID
            user_role: 当前用户角色
            tab_id: Tab ID
        
        Returns:
            LiveRoomTab: 被删除的 Tab 对象
        
        Raises:
            PermissionDeniedException: 权限不足
            TabNotFoundException: Tab 不存在
        """
        # 1. 权限检查
        await self._check_admin_permission(user_role)
        
        # 2. 获取 Tab
        db_tab = await crud_live_features.get_tab(self.db, tab_id)
        if db_tab is None:
            raise TabNotFoundException(f"Tab ID: {tab_id} 不存在")
        
        # 3. 调用 CRUD 层删除
        deleted_tab = await crud_live_features.remove_tab(self.db, db_tab)
        
        logger.info(f"Admin user {user_id} deleted tab {tab_id}")
        return deleted_tab


class MessageService:
    """留言相关业务逻辑"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def _check_room_exists(self, room_id: uuid.UUID) -> LiveRoom:
        """
        辅助函数：检查房间是否存在
        
        Args:
            room_id: 房间 ID
        
        Returns:
            LiveRoom: 房间对象
        
        Raises:
            RoomNotFoundException: 房间不存在
        """
        room = await crud_room.get(self.db, room_id)
        if room is None:
            raise RoomNotFoundException(f"Room ID: {room_id} 不存在")
        return room
    
    async def create_message(
        self, 
        user_id: uuid.UUID, # [V5.3 修复]
        user_role: LiveRoomMessageUserRole, # [V5.3 修复]
        room_id: uuid.UUID, 
        obj_in: LiveRoomMessageCreate
    ) -> LiveRoomMessage:
        """
        创建新留言
        
        Args:
            user_id: 当前用户 ID
            user_role: 当前用户角色
            room_id: 房间 ID
            obj_in: 留言创建数据
        
        Returns:
            LiveRoomMessage: 创建的留言对象
        
        Raises:
            RoomNotFoundException: 房间不存在
            InvalidParameterException: 参数无效（如普通用户发送包含 URL 的留言）
        """
        # 1. 检查房间是否存在
        await self._check_room_exists(room_id)
        
        # 2. [关键] URL 过滤（学院派规范 5.3.B / V5.3 修复）
        is_admin = user_role in [LiveRoomMessageUserRole.ADMIN, LiveRoomMessageUserRole.SUPERADMIN]
        has_url = bool(URL_REGEX.search(obj_in.content))
        
        if not is_admin and has_url:
            raise InvalidParameterException(
                code=4004, 
                message="普通用户不允许发送包含 URL 的留言"
            )
        
        # 3. [关键] 内部 Schema 转换（学院派规范 5.2 / V5.3 修复）
        internal_obj_in = LiveRoomMessageCreateInternal(
            content=obj_in.content,
            room_id=room_id,
            session_id=None,  # 可以后续扩展从当前 session 获取
            user_id=user_id,
            user_role=user_role
        )
        
        # 4. 调用 CRUD 层创建
        new_message = await crud_live_features.create_message(self.db, internal_obj_in)
        
        logger.info(f"User {user_id} created message {new_message.id} in room {room_id}")
        return new_message
    
    async def get_messages(
        self, 
        room_id: uuid.UUID, 
        page: int, 
        size: int, 
        since: Optional[datetime] = None
    ) -> Tuple[List[LiveRoomMessage], int]:
        """
        获取房间留言列表
        
        Args:
            room_id: 房间 ID
            page: 页码（从 1 开始）
            size: 每页大小
            since: 可选的时间过滤
        
        Returns:
            Tuple[List[LiveRoomMessage], int]: (留言列表, 总数)
        
        Raises:
            RoomNotFoundException: 房间不存在
        """
        # 1. 检查房间是否存在
        await self._check_room_exists(room_id)
        
        # 2. 调用 CRUD 层获取留言
        messages, total = await crud_live_features.get_messages_by_room(
            self.db, 
            room_id, 
            page, 
            size, 
            since
        )
        
        logger.info(f"Retrieved {len(messages)} messages for room {room_id}, page {page}")
        return messages, total
```

##### 6.2. 依赖文件：`app/models/live_features.py`

(已在CRUD测试文档中提供，此处省略)

##### 6.3. 依赖文件：`app/schemas/live_features.py`

(已在CRUD测试文档中提供，此处省略)

##### 6.4. 依赖文件：`app/exceptions.py`

```python
"""
LiveCore Service - Custom Business Exceptions

This module contains all custom exceptions for the LiveCore Service,
used for business logic validation and error handling.
"""

class RoomNotFoundException(Exception):
    """Raised when a room is not found in the database."""
    pass

class TabNotFoundException(Exception):
    """Tab 不存在"""
    pass

class MessageNotFoundException(Exception):
    """留言不存在"""
    pass

class PermissionDeniedException(Exception):
    """权限不足（由 Service 层检查并抛出）"""
    pass

class InvalidParameterException(Exception):
    """
    业务参数无效（由 Service 层检查并抛出）
    例如：内容包含非法 URL, content_type 与 content 不匹配
    """
    def __init__(self, message: str, code: int = 4001):
        self.message = message
        self.code = code  # 允许携带业务码
        super().__init__(self.message)
```

-----

#### 7\. [动态生成] 具体测试任务列表 (Dynamic-Generated Specific Test Tasks)

**你必须为 `Section 6` 中的代码严格生成以下所有测试用例：**

> **[测试目标层级]**: Service 层（业务逻辑层）
> **[强制测试风格]**: 学院派 (Academic) - 使用 Mock 隔离测试
> **[核心工具]**: `mocker` (pytest-mock)

-----

### A. 针对 `TabService` 类的测试（学院派） **[V5.3 修复]**

#### **方法 1: `async def list_tabs_for_admin(user_id, user_role, room_id)`**

1.  **`test_list_tabs_for_admin_success`** (成功场景):

      * **准备 (Arrange)**:
          * **(遵循 4.2.C)** 定义 `test_user_id = uuid.uuid4()` 和 `test_user_role = LiveRoomMessageUserRole.ADMIN`。
          * Mock `crud_room.get` 返回一个模拟的 `LiveRoom` 对象。
          * Mock `crud_live_features.get_all_by_room_id` 返回 `([mock_tab1, mock_tab2], 2)`。
      * **执行 (Act)**:
          * 创建 `TabService(db)` 实例。
          * 调用 `await service.list_tabs_for_admin(test_user_id, test_user_role, room_id)`。
      * **断言 (Assert)**:
          * **必须**断言 `crud_room.get` 被调用一次。
          * **必须**断言 `crud_live_features.get_all_by_room_id` 被调用一次，参数 `skip=0, limit=100`。
          * **必须**断言返回值为 `([mock_tab1, mock_tab2], 2)`。

2.  **`test_list_tabs_for_admin_permission_denied`** (权限不足场景):

      * **准备 (Arrange)**:
          * **(遵循 4.2.C)** 定义 `test_user_id = uuid.uuid4()` 和 `test_user_role = LiveRoomMessageUserRole.REGULAR`（非管理员）。
      * **执行 & 断言 (Act & Assert)**:
          * **必须**使用 `with pytest.raises(PermissionDeniedException):` 包裹调用 `service.list_tabs_for_admin`。
          * **必须**断言 `crud_room.get` **未被调用**（权限检查在前）。

3.  **`test_list_tabs_for_admin_room_not_found`** (房间不存在场景):

      * **准备 (Arrange)**:
          * **(遵循 4.2.C)** 定义 `test_user_id` 和 `test_user_role = LiveRoomMessageUserRole.ADMIN`。
          * Mock `crud_room.get` 返回 `None`。
      * **执行 & 断言 (Act & Assert)**:
          * **必须**使用 `with pytest.raises(RoomNotFoundException):` 包裹调用。

#### **方法 2: `async def get_active_tabs_for_room(room_id)`**

1.  **`test_get_active_tabs_for_room_success`** (成功场景):

      * **准备 (Arrange)**:
          * Mock `crud_room.get` 返回一个模拟的 `LiveRoom` 对象。
          * Mock `crud_live_features.get_active_by_room_id` 返回 `[mock_tab1, mock_tab2]`。
      * **执行 (Act)**:
          * 调用 `await service.get_active_tabs_for_room(room_id)`。
      * **断言 (Assert)**:
          * **必须**断言 `crud_live_features.get_active_by_room_id` 被调用一次。
          * **必须**断言返回值为 `[mock_tab1, mock_tab2]`。

2.  **`test_get_active_tabs_for_room_room_not_found`** (房间不存在场景):

      * **准备 (Arrange)**:
          * Mock `crud_room.get` 返回 `None`。
      * **执行 & 断言 (Act & Assert)**:
          * **必须**使用 `with pytest.raises(RoomNotFoundException):` 包裹调用。

#### **方法 3: `async def create_tab(user_id, user_role, room_id, obj_in)`**

1.  **`test_create_tab_success`** (成功场景):

      * **准备 (Arrange)**:
          * **(遵循 4.2.C)** 定义 `test_user_id` 和 `test_user_role = LiveRoomMessageUserRole.ADMIN`。
          * Mock `crud_room.get` 返回 `LiveRoom`。
          * 准备 `LiveRoomTabCreate` 对象 (`content_type=TEXT, text_content="测试"`)。
          * Mock `crud_live_features.create_tab` 返回一个模拟的 `LiveRoomTab`。
      * **执行 (Act)**:
          * 调用 `await service.create_tab(test_user_id, test_user_role, room_id, obj_in)`。
      * **断言 (Assert)**:
          * **必须**断言 `crud_live_features.create_tab` 被调用一次，参数包含 `db, obj_in, room_id`。
          * **必须**断言返回值为模拟的 Tab 对象。

2.  **`test_create_tab_permission_denied`** (权限不足场景):

      * **准备 (Arrange)**:
          * **(遵循 4.2.C)** 定义 `test_user_id` 和 `test_user_role = LiveRoomMessageUserRole.REGULAR`。
      * **执行 & 断言 (Act & Assert)**:
          * **必须**使用 `with pytest.raises(PermissionDeniedException):` 包裹调用。

3.  **`test_create_tab_room_not_found`** (房间不存在场景):

      * **准备 (Arrange)**:
          * **(遵循 4.2.C)** 定义 `test_user_id` 和 `test_user_role = LiveRoomMessageUserRole.ADMIN`。
          * Mock `crud_room.get` 返回 `None`。
      * **执行 & 断言 (Act & Assert)**:
          * **必须**使用 `with pytest.raises(RoomNotFoundException):` 包裹调用。

4.  **`test_create_tab_invalid_content_type_text`** (参数无效 - TEXT 缺少 text\_content):

      * **准备 (Arrange)**:
          * **(遵循 4.2.C)** 定义 `test_user_id` 和 `test_user_role = LiveRoomMessageUserRole.ADMIN`。
          * Mock `crud_room.get` 返回 `LiveRoom`。
          * 准备 `LiveRoomTabCreate` (`content_type=TEXT, text_content=None`)。
      * **执行 & 断言 (Act & Assert)**:
          * **必须**使用 `with pytest.raises(InvalidParameterException):` 包裹调用。
          * **必须**验证异常消息包含 "text\_content 不能为空"。

5.  **`test_create_tab_invalid_content_type_image`** (参数无效 - IMAGE 缺少 image\_url):

      * **准备 (Arrange)**:
          * (同上) 准备 `LiveRoomTabCreate` (`content_type=IMAGE, image_url=None`)。
      * **执行 & 断言 (Act & Assert)**:
          * **必须**使用 `with pytest.raises(InvalidParameterException):` 包裹调用。
          * **必须**验证异常消息包含 "image\_url 不能为空"。

6.  **`test_create_tab_invalid_content_type_mixed`** (参数无效 - MIXED 两个都为空):

      * **准备 (Arrange)**:
          * (同上) 准备 `LiveRoomTabCreate` (`content_type=MIXED, text_content=None, image_url=None`)。
      * **执行 & 断言 (Act & Assert)**:
          * **必须**使用 `with pytest.raises(InvalidParameterException):` 包裹调用。
          * **必须**验证异常消息包含 "至少需要一个"。

#### **方法 4: `async def update_tab(user_id, user_role, tab_id, obj_in)`**

1.  **`test_update_tab_success`** (成功场景):

      * **准备 (Arrange)**:
          * **(遵循 4.2.C)** 定义 `test_user_id` 和 `test_user_role = LiveRoomMessageUserRole.ADMIN`。
          * 创建一个模拟的 `db_tab` (`content_type=TEXT, text_content="原内容"`)。
          * Mock `crud_live_features.get_tab` 返回 `db_tab`。
          * Mock `crud_live_features.update_tab` 返回更新后的 Tab。
          * 准备 `LiveRoomTabUpdate` (`title="新标题"`)。
      * **执行 (Act)**:
          * 调用 `await service.update_tab(test_user_id, test_user_role, tab_id, obj_in)`。
      * **断言 (Assert)**:
          * **必须**断言 `crud_live_features.get_tab` 被调用一次。
          * **必须**断言 `crud_live_features.update_tab` 被调用一次，参数包含 `db, db_tab, obj_in`。

2.  **`test_update_tab_permission_denied`** (权限不足场景):

      * **准备 (Arrange)**:
          * **(遵循 4.2.C)** 定义 `test_user_id` 和 `test_user_role = LiveRoomMessageUserRole.REGULAR`。
      * **执行 & 断言 (Act & Assert)**:
          * **必须**使用 `with pytest.raises(PermissionDeniedException):` 包裹调用。

3.  **`test_update_tab_not_found`** (Tab不存在场景):

      * **准备 (Arrange)**:
          * **(遵循 4.2.C)** 定义 `test_user_id` 和 `test_user_role = LiveRoomMessageUserRole.ADMIN`。
          * Mock `crud_live_features.get_tab` 返回 `None`。
      * **执行 & 断言 (Act & Assert)**:
          * **必须**使用 `with pytest.raises(TabNotFoundException):` 包裹调用。

4.  **`test_update_tab_invalid_content_type_validation`** (参数校验场景):

      * **准备 (Arrange)**:
          * **(遵循 4.2.C)** 定义 `test_user_id` 和 `test_user_role = LiveRoomMessageUserRole.ADMIN`。
          * 创建一个模拟的 `db_tab` (`text_content=None, image_url=None`)。
          * Mock `crud_live_features.get_tab` 返回 `db_tab`。
          * 准备 `LiveRoomTabUpdate` (`content_type=TEXT`)（但 db\_tab 的 text\_content 为空）。
      * **执行 & 断言 (Act & Assert)**:
          * **必须**使用 `with pytest.raises(InvalidParameterException):` 包裹调用。

#### **方法 5: `async def delete_tab(user_id, user_role, tab_id)`**

1.  **`test_delete_tab_success`** (成功场景):

      * **准备 (Arrange)**:
          * **(遵循 4.2.C)** 定义 `test_user_id` 和 `test_user_role = LiveRoomMessageUserRole.ADMIN`。
          * Mock `crud_live_features.get_tab` 返回模拟的 `db_tab`。
          * Mock `crud_live_features.remove_tab` 返回被删除的 Tab。
      * **执行 (Act)**:
          * 调用 `await service.delete_tab(test_user_id, test_user_role, tab_id)`。
      * **断言 (Assert)**:
          * **必须**断言 `crud_live_features.remove_tab` 被调用一次，参数包含 `db, db_tab`。

2.  **`test_delete_tab_permission_denied`** (权限不足场景):

      * **准备 (Arrange)**:
          * **(遵循 4.2.C)** 定义 `test_user_id` 和 `test_user_role = LiveRoomMessageUserRole.REGULAR`。
      * **执行 & 断言 (Act & Assert)**:
          * **必须**使用 `with pytest.raises(PermissionDeniedException):` 包裹调用。

3.  **`test_delete_tab_not_found`** (Tab不存在场景):

      * **准备 (Arrange)**:
          * **(遵循 4.2.C)** 定义 `test_user_id` 和 `test_user_role = LiveRoomMessageUserRole.ADMIN`。
          * Mock `crud_live_features.get_tab` 返回 `None`。
      * **执行 & 断言 (Act & Assert)**:
          * **必须**使用 `with pytest.raises(TabNotFoundException):` 包裹调用。

-----

### B. 针对 `MessageService` 类的测试（学院派） **[V5.3 修复]**

#### **方法 6: `async def create_message(user_id, user_role, room_id, obj_in)`**

1.  **`test_create_message_success_admin`** (成功场景 - 管理员可发送URL):

      * **准备 (Arrange)**:
          * **(遵循 4.2.C)** 定义 `test_user_id = uuid.uuid4()` 和 `test_user_role = LiveRoomMessageUserRole.ADMIN`。
          * Mock `crud_room.get` 返回 `LiveRoom`。
          * 准备 `LiveRoomMessageCreate` (`content="测试留言 https://example.com"`)。
          * Mock `crud_live_features.create_message` 返回模拟的 `LiveRoomMessage`。
      * **执行 (Act)**:
          * 调用 `await service.create_message(test_user_id, test_user_role, room_id, obj_in)`。
      * **断言 (Assert)**:
          * **必须**断言 `crud_live_features.create_message` 被调用一次。
          * **[关键]** 断言传递给 CRUD 的参数是 `LiveRoomMessageCreateInternal`，包含 `room_id`, `user_id=test_user_id`, `user_role=test_user_role`。

2.  **`test_create_message_success_regular_user_without_url`** (成功场景 - 普通用户无URL):

      * **准备 (Arrange)**:
          * **(遵循 4.2.C)** 定义 `test_user_id` 和 `test_user_role = LiveRoomMessageUserRole.REGULAR`。
          * Mock `crud_room.get` 返回 `LiveRoom`。
          * 准备 `LiveRoomMessageCreate` (`content="普通留言"`)。
          * Mock `crud_live_features.create_message` 返回模拟的消息。
      * **执行 (Act)**:
          * 调用 `await service.create_message(test_user_id, test_user_role, room_id, obj_in)`。
      * **断言 (Assert)**:
          * **必须**断言调用成功，返回模拟的消息。

3.  **`test_create_message_regular_user_with_url_raises_exception`** (失败场景 - 普通用户发送URL):

      * **准备 (Arrange)**:
          * **(遵循 4.2.C)** 定义 `test_user_id` 和 `test_user_role = LiveRoomMessageUserRole.REGULAR`。
          * Mock `crud_room.get` 返回 `LiveRoom`。
          * 准备 `LiveRoomMessageCreate` (`content="包含URL https://evil.com"`)。
      * **执行 & 断言 (Act & Assert)**:
          * **必须**使用 `with pytest.raises(InvalidParameterException) as exc_info:` 包裹调用。
          * **[关键]** 断言 `exc_info.value.code == 4004`。
          * **[关键]** 断言异常消息包含 "URL"。

4.  **`test_create_message_room_not_found`** (失败场景 - 房间不存在):

      * **准备 (Arrange)**:
          * **(遵循 4.2.C)** 定义 `test_user_id` 和 `test_user_role`。
          * Mock `crud_room.get` 返回 `None`。
      * **执行 & 断言 (Act & Assert)**:
          * **必须**使用 `with pytest.raises(RoomNotFoundException):` 包裹调用。

#### **方法 7: `async def get_messages(room_id, page, size, since)`**

1.  **`test_get_messages_success`** (成功场景):

      * **准备 (Arrange)**:
          * Mock `crud_room.get` 返回 `LiveRoom`。
          * Mock `crud_live_features.get_messages_by_room` 返回 `([mock_msg1, mock_msg2], 2)`。
      * **执行 (Act)**:
          * 调用 `await service.get_messages(room_id, page=1, size=20, since=None)`。
      * **断言 (Assert)**:
          * **必须**断言 `crud_live_features.get_messages_by_room` 被调用一次，参数 `room_id, page=1, size=20, since=None`。
          * **必须**断言返回值为 `([mock_msg1, mock_msg2], 2)`。

2.  **`test_get_messages_room_not_found`** (失败场景 - 房间不存在):

      * **准备 (Arrange)**:
          * Mock `crud_room.get` 返回 `None`。
      * **执行 & 断言 (Act & Assert)**:
          * **必须**使用 `with pytest.raises(RoomNotFoundException):` 包裹调用。

-----

### C. 测试类组织（推荐结构）

```python
class TestTabService:
    """TabService 业务逻辑测试（学院派）"""
    
    # test_list_tabs_for_admin_success
    # test_list_tabs_for_admin_permission_denied
    # test_list_tabs_for_admin_room_not_found
    # test_get_active_tabs_for_room_success
    # test_get_active_tabs_for_room_room_not_found
    # test_create_tab_success
    # test_create_tab_permission_denied
    # test_create_tab_room_not_found
    # test_create_tab_invalid_content_type_text
    # test_create_tab_invalid_content_type_image
    # test_create_tab_invalid_content_type_mixed
    # test_update_tab_success
    # test_update_tab_permission_denied
    # test_update_tab_not_found
    # test_update_tab_invalid_content_type_validation
    # test_delete_tab_success
    # test_delete_tab_permission_denied
    # test_delete_tab_not_found


class TestMessageService:
    """MessageService 业务逻辑测试（学院派）"""
    
    # test_create_message_success_admin
    # test_create_message_success_regular_user_without_url
    # test_create_message_regular_user_with_url_raises_exception
    # test_create_message_room_not_found
    # test_get_messages_success
    # test_get_messages_room_not_found
```

-----

#### 8\. 交付物 (Deliverable - 执行者)

请根据**以上所有规范 (1-7)**，为 `Section 6` 中提供的代码生成**完整的 `pytest` 测试文件**。

  * **交付物**:
      * `tests/unit/test_service_live_features.py`
  * **指令**:
    1.  **遵循任务列表**: 严格按照 `Section 7` 中的列表生成所有指定的测试用例（**共 24 个测试用例**）。
    2.  **遵循所有规范**: 确保生成的代码 100% 遵循 `Section 2-5` (哲学, 语法, 断言, 风格)。
    3.  **学院派测试**: 本测试文件属于 Service 层测试，**必须**使用 `mocker` 隔离测试，Mock 所有 CRUD 调用。
    4.  **Mock 路径规范**: 使用原始模块路径 (`app.crud.live_features.xxx`, `app.crud.room.get`)。
    5.  **异常验证**: 所有失败场景**必须**使用 `pytest.raises()` 验证自定义异常。
    6.  **不使用数据库**: Service 层测试**禁止**使用 `db_session` fixture，所有数据库操作必须被 Mock。

-----

### 9\. 关键提示

#### 9.1. [V5.3 修复] Mock 用户身份示例

根据 `Section 3.5` 和 `Section 4.2.C` 规范，**禁止** Mock `User` 对象。**必须**按如下方式准备 `user_id` 和 `user_role`：

```python
import uuid
from app.models.live_features import LiveRoomMessageUserRole

# 准备 Admin 身份
admin_user_id = uuid.uuid4()
admin_user_role = LiveRoomMessageUserRole.ADMIN

# 准备 Regular 用户身份
regular_user_id = uuid.uuid4()
regular_user_role = LiveRoomMessageUserRole.REGULAR
```

#### 9.2. Mock AsyncSession 示例

```python
from unittest.mock import MagicMock

# Service 层测试不需要真实 DB，只需要 Mock
mock_db = MagicMock(spec=AsyncSession)
```

#### 9.3. Mock CRUD 函数示例

```python
from unittest.mock import AsyncMock

# Mock 异步 CRUD 函数
mock_get_room = mocker.patch(
    "app.crud.room.get",
    new_callable=AsyncMock,
    return_value=mock_room_object
)

mock_create_tab = mocker.patch(
    "app.crud.live_features.create_tab",
    new_callable=AsyncMock,
    return_value=mock_tab_object
)
```

#### 9.4. URL 过滤测试关键点

```python
# 测试 URL 检测逻辑
content_with_url = "测试 https://example.com 内容"
content_without_url = "普通测试内容"

# 确保测试覆盖 URL_REGEX 正则表达式
```

-----

### 10\. 最终检查清单

生成的测试代码必须满足：

  - [ ] 包含完整的模块文档字符串
  - [ ] 导入所有必需模块（`pytest`, `uuid`, `MagicMock`, `AsyncMock`, Service classes, Exceptions, Enums）
  - [ ] **禁止**使用 `db_session` fixture（Service 层不需要真实数据库）
  - [ ] 所有测试使用 AAA 结构（Arrange, Act, Assert）并注释分隔
  - [ ] 所有 Mock 使用原始模块路径（`app.crud.xxx`）
  - [ ] 所有异步函数 Mock 使用 `new_callable=AsyncMock`
  - [ ] 所有失败场景使用 `pytest.raises()` 验证异常
  - [ ] 包含 `Section 7` 中列出的所有 24 个测试用例
  - [ ] 所有测试函数包含清晰的 docstring
  - [ ] 测试类名为 `TestTabService` 和 `TestMessageService`
  - [ ] URL 过滤测试验证 `InvalidParameterException` 的 `code` 属性为 `4004`
  - [ ] **[V5.3 检查]** **没有** Mock `User` 对象，**只** Mock `user_id` 和 `user_role`。

-----

**[测试代码生成提示词文档结束]**