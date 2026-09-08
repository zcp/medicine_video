-----

### 2\. 【最终完整版】高效 AI 测试代码生成提示词 (v5.3 - 全面修复版)

这是根据您的要求，将您提供的所有“补丁”有机融入您上传的 `_CRUD_live_features.md` 文件后生成的最终版本。

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

##### 6.1. 被测试文件：`app/crud/live_features.py`

```python
"""
直播间 Tab 和留言功能的数据访问层 (CRUD Layer)

本模块提供 LiveRoomTab 和 LiveRoomMessage 模型的数据库操作函数。
遵循学院派架构规范：纯粹的数据访问层，不包含业务逻辑。
"""

import uuid
import logging
from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError

# 导入模型 (学院派 ENUM 版)
from app.models.live_features import (
    LiveRoomTab, 
    LiveRoomMessage, 
    LiveRoomTabContentType, 
    LiveRoomMessageUserRole
)
# 导入 Schemas (学院派 ENUM 版)
from app.schemas.live_features import (
    LiveRoomTabCreate, 
    LiveRoomTabUpdate, 
    LiveRoomMessageCreateInternal
)

logger = logging.getLogger(__name__)


# ==================== LiveRoomTab CRUD 操作 ====================

async def create_tab(
    db: AsyncSession, 
    obj_in: LiveRoomTabCreate, 
    room_id: uuid.UUID
) -> LiveRoomTab:
    """
    创建新的直播间 Tab
    
    Args:
        db: 数据库会话
        obj_in: Tab 创建数据
        room_id: 直播间 ID（来自路径参数）
    
    Returns:
        LiveRoomTab: 创建的 Tab 对象
    
    Raises:
        IntegrityError: 数据库完整性错误（如外键约束失败）
        Exception: 其他数据库错误
    """
    # [学院派规范 5.1] 安全异步异常处理：提前提取日志变量
    room_id_str = str(room_id)
    tab_key = obj_in.tab_key
    
    try:
        # [学院派规范 5.1, 5.3.A] 应用层生成 UUID
        db_obj = LiveRoomTab(
            id=uuid.uuid4(),
            room_id=room_id,
            **obj_in.model_dump()
        )
        db.add(db_obj)
        
        # [学院派规范 5.1] 在 try 块中提交事务
        await db.commit()
        await db.refresh(db_obj)
        
        logger.info(f"Tab created successfully: id={db_obj.id}, room_id={room_id_str}, tab_key={tab_key}")
        return db_obj
        
    except IntegrityError as e:
        # [学院派规范 5.1] 回滚事务并记录错误
        await db.rollback()
        logger.error(f"IntegrityError creating tab for room_id={room_id_str}, tab_key={tab_key}: {str(e)}")
        raise
        
    except Exception as e:
        # [学院派规范 5.1] 捕获其他异常
        await db.rollback()
        logger.error(f"Error creating tab for room_id={room_id_str}, tab_key={tab_key}: {str(e)}")
        raise


async def get_tab(
    db: AsyncSession, 
    tab_id: uuid.UUID
) -> Optional[LiveRoomTab]:
    """
    根据 ID 获取单个 Tab
    
    用于 Service 层的更新/删除操作准备
    
    Args:
        db: 数据库会话
        tab_id: Tab ID
    
    Returns:
        Optional[LiveRoomTab]: Tab 对象，不存在则返回 None
    """
    stmt = select(LiveRoomTab).where(LiveRoomTab.id == tab_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_tab_with_room(
    db: AsyncSession, 
    tab_id: uuid.UUID
) -> Optional[LiveRoomTab]:
    """
    获取 Tab 并预加载 room 关系
    
    用于 Service 层的权限检查准备
    
    Args:
        db: 数据库会话
        tab_id: Tab ID
    
    Returns:
        Optional[LiveRoomTab]: Tab 对象（含 room 关系），不存在则返回 None
    """
    # [学院派规范 5.3.A] 使用 selectinload 避免 N+1 问题
    stmt = select(LiveRoomTab).options(
        selectinload(LiveRoomTab.room)
    ).where(LiveRoomTab.id == tab_id)
    
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_all_by_room_id(
    db: AsyncSession, 
    room_id: uuid.UUID, 
    skip: int = 0, 
    limit: int = 100
) -> Tuple[List[LiveRoomTab], int]:
    """
    分页获取指定直播间的所有 Tab（后台管理用）
    
    Args:
        db: 数据库会话
        room_id: 直播间 ID
        skip: 跳过的记录数
        limit: 返回的最大记录数
    
    Returns:
        Tuple[List[LiveRoomTab], int]: (Tab 列表, 总数)
    """
    # [学院派规范 5.3.A] 分页模式：先获取总数
    count_stmt = select(func.count(LiveRoomTab.id)).where(
        LiveRoomTab.room_id == room_id
    )
    count_result = await db.execute(count_stmt)
    total = count_result.scalar() or 0
    
    # [学院派规范 5.3.A] 分页模式：再获取数据列表
    stmt = select(LiveRoomTab).where(
        LiveRoomTab.room_id == room_id
    ).order_by(
        LiveRoomTab.sort_order.asc()
    ).offset(skip).limit(limit)
    
    result = await db.execute(stmt)
    items = result.scalars().all()
    
    return list(items), total


async def get_active_by_room_id(
    db: AsyncSession, 
    room_id: uuid.UUID
) -> List[LiveRoomTab]:
    """
    获取指定直播间的所有激活的 Tab（前端展示用）
    
    Args:
        db: 数据库会话
        room_id: 直播间 ID
    
    Returns:
        List[LiveRoomTab]: 激活的 Tab 列表，按 sort_order 升序排列
    """
    stmt = select(LiveRoomTab).where(
        and_(
            LiveRoomTab.room_id == room_id,
            LiveRoomTab.is_active == True
        )
    ).order_by(LiveRoomTab.sort_order.asc())
    
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def update_tab(
    db: AsyncSession, 
    db_obj: LiveRoomTab, 
    obj_in: LiveRoomTabUpdate
) -> LiveRoomTab:
    """
    更新 Tab 信息
    
    Args:
        db: 数据库会话
        db_obj: 数据库中的 Tab 对象
        obj_in: 更新数据
    
    Returns:
        LiveRoomTab: 更新后的 Tab 对象
    
    Raises:
        IntegrityError: 数据库完整性错误
        Exception: 其他数据库错误
    """
    # [学院派规范 5.1] 安全异步异常处理：提前提取日志变量
    tab_id_str = str(db_obj.id)
    
    try:
        # 只更新提供的字段
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        # [学院派规范 5.1] 在 try 块中提交事务
        await db.commit()
        await db.refresh(db_obj)
        
        logger.info(f"Tab updated successfully: id={tab_id_str}, updated_fields={list(update_data.keys())}")
        return db_obj
        
    except IntegrityError as e:
        # [学院派规范 5.1] 回滚事务并记录错误
        await db.rollback()
        logger.error(f"IntegrityError updating tab id={tab_id_str}: {str(e)}")
        raise
        
    except Exception as e:
        # [学院派规范 5.1] 捕获其他异常
        await db.rollback()
        logger.error(f"Error updating tab id={tab_id_str}: {str(e)}")
        raise


async def remove_tab(
    db: AsyncSession, 
    db_obj: LiveRoomTab
) -> LiveRoomTab:
    """
    删除 Tab
    
    Args:
        db: 数据库会话
        db_obj: 数据库中的 Tab 对象
    
    Returns:
        LiveRoomTab: 被删除的 Tab 对象
    
    Raises:
        Exception: 数据库错误
    """
    # [学院派规范 5.1] 安全异步异常处理：提前提取日志变量
    tab_id_str = str(db_obj.id)
    tab_key = db_obj.tab_key
    
    try:
        await db.delete(db_obj)
        
        # [学院派规范 5.1] 在 try 块中提交事务
        await db.commit()
        
        logger.info(f"Tab deleted successfully: id={tab_id_str}, tab_key={tab_key}")
        return db_obj
        
    except Exception as e:
        # [学院派规范 5.1] 回滚事务并记录错误
        await db.rollback()
        logger.error(f"Error deleting tab id={tab_id_str}: {str(e)}")
        raise


# ==================== LiveRoomMessage CRUD 操作 ====================

async def create_message(
    db: AsyncSession, 
    obj_in: LiveRoomMessageCreateInternal
) -> LiveRoomMessage:
    """
    创建新的直播间留言
    
    Args:
        db: 数据库会话
        obj_in: 留言创建数据（包含 Service 层传入的所有字段）
    
    Returns:
        LiveRoomMessage: 创建的留言对象
    
    Raises:
        IntegrityError: 数据库完整性错误（如外键约束失败）
        Exception: 其他数据库错误
    """
    # [学院派规范 5.1] 安全异步异常处理：提前提取日志变量
    room_id_str = str(obj_in.room_id)
    user_id_str = str(obj_in.user_id)
    content_preview = obj_in.content[:50] if len(obj_in.content) > 50 else obj_in.content
    
    try:
        # [学院派规范 5.1, 5.2, 5.3.A] 使用 LiveRoomMessageCreateInternal Schema
        # 应用层生成 UUID
        db_obj = LiveRoomMessage(
            id=uuid.uuid4(),
            **obj_in.model_dump()
        )
        db.add(db_obj)
        
        # [学院派规范 5.1] 在 try 块中提交事务
        await db.commit()
        await db.refresh(db_obj)
        
        logger.info(f"Message created successfully: id={db_obj.id}, room_id={room_id_str}, user_id={user_id_str}")
        return db_obj
        
    except IntegrityError as e:
        # [学院派规范 5.1] 回滚事务并记录错误
        await db.rollback()
        logger.error(f"IntegrityError creating message for room_id={room_id_str}, user_id={user_id_str}: {str(e)}")
        raise
        
    except Exception as e:
        # [学院派规范 5.1] 捕获其他异常
        await db.rollback()
        logger.error(f"Error creating message for room_id={room_id_str}, user_id={user_id_str}: {str(e)}")
        raise


async def get_messages_by_room(
    db: AsyncSession, 
    room_id: uuid.UUID, 
    page: int, 
    size: int, 
    since: Optional[datetime] = None
) -> Tuple[List[LiveRoomMessage], int]:
    """
    分页获取直播间留言
    
    Args:
        db: 数据库会话
        room_id: 直播间 ID
        page: 页码（从 1 开始）
        size: 每页大小
        since: 可选的时间过滤（获取该时间之后的留言）
    
    Returns:
        Tuple[List[LiveRoomMessage], int]: (留言列表, 总数)
    """
    # 构建基础查询条件
    conditions = [
        LiveRoomMessage.room_id == room_id,
        LiveRoomMessage.is_deleted == False
    ]
    
    # 添加时间过滤条件
    if since is not None:
        conditions.append(LiveRoomMessage.created_at > since)
    
    # [学院派规范 5.3.A] 分页模式：先获取总数
    count_stmt = select(func.count(LiveRoomMessage.id)).where(and_(*conditions))
    count_result = await db.execute(count_stmt)
    total = count_result.scalar() or 0
    
    # [学院派规范 5.3.A] 分页模式：再获取数据列表
    # 计算 offset
    skip = (page - 1) * size
    
    stmt = select(LiveRoomMessage).where(
        and_(*conditions)
    ).order_by(
        LiveRoomMessage.created_at.desc()
    ).offset(skip).limit(size)
    
    result = await db.execute(stmt)
    items = result.scalars().all()
    
    return list(items), total
```

##### 6.2. 依赖文件：`app/models/live_features.py`

```python
"""
直播间 Tab 和留言功能的数据库模型
"""
import uuid
from datetime import datetime
import enum

# SQLAlchemy 核心导入
from sqlalchemy import Column, String, Text, Integer, ForeignKey, Enum as SAEnum, Index, TIMESTAMP, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


# ==================== 枚举类型定义 ====================
# 对应 DDL: CREATE TYPE live_room_message_user_role
class LiveRoomMessageUserRole(str, enum.Enum):
    """留言用户角色枚举"""
    REGULAR = 'REGULAR'
    MODERATOR = 'MODERATOR'
    ADMIN = 'ADMIN'
    SUPERADMIN = 'SUPERADMIN'


# 对应 DDL: CREATE TYPE live_room_tab_content_type
class LiveRoomTabContentType(str, enum.Enum):
    """Tab内容类型枚举"""
    TEXT = 'text'
    IMAGE = 'image'
    MIXED = 'mixed'


# ==================== 模型类定义 ====================

class LiveRoomMessage(Base):
    """直播间留言表"""
    __tablename__ = "live_room_messages"
    
    # 主键
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # 外键
    room_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("live_rooms.id", ondelete="CASCADE"), 
        nullable=False
    )
    session_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("live_sessions.id", ondelete="SET NULL"), 
        nullable=True
    )
    
    # 用户信息
    user_id = Column(
        UUID(as_uuid=True), 
        nullable=False, 
        comment='存储 users.public_id'
    )
    user_role = Column(
        SAEnum(LiveRoomMessageUserRole, name='live_room_message_user_role', create_type=False), 
        nullable=False, 
        comment='用户角色快照'
    )
    
    # 留言内容
    content = Column(Text, nullable=False)
    
    # 状态与扩展
    is_deleted = Column(Boolean, nullable=False, default=False)
    extra = Column(JSONB, nullable=True)
    
    # 时间戳
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    
    # 索引定义
    __table_args__ = (
        Index('idx_live_room_messages_room_created', 'room_id', 'created_at'),
        Index('idx_live_room_messages_session_created', 'session_id', 'created_at'),
    )
    
    # 关联关系（单向）
    room = relationship("LiveRoom")
    session = relationship("LiveSession")
    
    def __repr__(self):
        return f"<LiveRoomMessage(id={self.id}, user_id={self.user_id})>"


class LiveRoomTab(Base):
    """直播间 Tab 表"""
    __tablename__ = "live_room_tabs"
    
    # 主键
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # 外键
    room_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("live_rooms.id", ondelete="CASCADE"), 
        nullable=False
    )
    
    # Tab 基本信息
    tab_key = Column(
        String(64), 
        nullable=False, 
        comment='系统级 key，用于逻辑识别'
    )
    title = Column(
        String(128), 
        nullable=False, 
        comment='展示名称'
    )
    
    # 内容类型与内容
    content_type = Column(
        SAEnum(LiveRoomTabContentType, name='live_room_tab_content_type', create_type=False), 
        nullable=False, 
        comment="'text' | 'image' | 'mixed'"
    )
    text_content = Column(Text, nullable=True)
    image_url = Column(Text, nullable=True)
    
    # 排序与状态
    sort_order = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)
    
    # 时间戳
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
    # 索引定义
    __table_args__ = (
        Index('idx_live_room_tabs_room_sort', 'room_id', 'sort_order'),
    )
    
    # 关联关系（单向）
    room = relationship("LiveRoom")
    
    def __repr__(self):
        return f"<LiveRoomTab(id={self.id}, title={self.title}, room_id={self.room_id})>"
```

##### 6.3. 依赖文件：`app/schemas/live_features.py`

```python
"""
直播间 Tab 和留言功能的 Pydantic Schema (学院派 ENUM 版)
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid
from enum import Enum


# ==================== 枚举类型定义 ====================
# 必须与 models/live_features.py 中的 ENUM 完全一致

class LiveRoomMessageUserRole(str, Enum):
    """留言用户角色枚举"""
    REGULAR = 'REGULAR'
    MODERATOR = 'MODERATOR'
    ADMIN = 'ADMIN'
    SUPERADMIN = 'SUPERADMIN'


class LiveRoomTabContentType(str, Enum):
    """Tab内容类型枚举"""
    TEXT = 'text'
    IMAGE = 'image'
    MIXED = 'mixed'


# ==================== LiveRoomTab Schema 部分 ====================

class LiveRoomTabBase(BaseModel):
    """
    Tab 基础 Schema
    
    包含 Tab 的核心业务字段
    """
    tab_key: str = Field(
        ..., 
        max_length=64, 
        description="系统级 key，用于前端逻辑判断"
    )
    title: str = Field(
        ..., 
        max_length=128, 
        description="展示名称"
    )
    
    # [学院派] 字段类型为 ENUM
    content_type: LiveRoomTabContentType = Field(
        ..., 
        description="内容类型, 'text', 'image' 或 'mixed'"
    )
    
    text_content: Optional[str] = Field(None, description="文本内容 (当 content_type 为 'text' 或 'mixed' 时)")
    image_url: Optional[str] = Field(None, description="图片 URL (当 content_type 为 'image' 或 'mixed' 时)")
    
    sort_order: int = Field(
        default=0, 
        ge=0, 
        description="排序顺序, 数值越小越靠前"
    )
    is_active: bool = Field(
        default=True, 
        description="是否激活, 是否在前端展示"
    )


class LiveRoomTabCreate(LiveRoomTabBase):
    """
    Tab 创建请求 Schema
    
    用于 POST /api/v1/admin/rooms/{room_id}/tabs
    room_id 来自路径参数，不包含在请求体中
    """
    pass


class LiveRoomTabUpdate(BaseModel):
    """
    Tab 更新请求 Schema
    
    用于 PATCH /api/v1/admin/tabs/{tab_id}
    所有字段可选，支持部分更新
    """
    tab_key: Optional[str] = Field(None, max_length=64, description="系统级 key")
    title: Optional[str] = Field(None, max_length=128, description="展示名称")
    content_type: Optional[LiveRoomTabContentType] = Field(None, description="内容类型")
    text_content: Optional[str] = Field(None, description="文本内容")
    image_url: Optional[str] = Field(None, description="图片 URL")
    sort_order: Optional[int] = Field(None, ge=0, description="排序顺序")
    is_active: Optional[bool] = Field(None, description="是否激活")


class LiveRoomMessageCreateInternal(BaseModel):
    """
    [学院派] 留言创建内部 Schema
    
    仅供 Service 层 -> CRUD 层使用
    包含 Service 层传入的所有必需字段（room_id, user_id, user_role 等）
    禁止在 API 路由中直接暴露给外部
    """
    room_id: uuid.UUID = Field(..., description="直播间 ID")
    session_id: Optional[uuid.UUID] = Field(None, description="会话 ID")
    user_id: uuid.UUID = Field(..., description="用户 ID")
    user_role: LiveRoomMessageUserRole = Field(..., description="用户角色")
    content: str = Field(..., min_length=1, max_length=500, description="留言内容")
```

-----

#### 7\. [动态生成] 具体测试任务列表 (Dynamic-Generated Specific Test Tasks)

**你必须为 `Section 6` 中的代码严格生成以下所有测试用例：**

> **[测试目标层级]**: CRUD 层（数据访问层）
> **[强制测试风格]**: 实用派 (Pragmatic) - 使用真实数据库
> **[核心工具]**: `db_session` (AsyncSession)

-----

### A. 针对 `app/crud/live_features.py` - LiveRoomTab CRUD 测试（实用派）

#### **函数 1: `async def create_tab(db, obj_in, room_id)`**

1.  **`test_create_tab_success`** (成功场景):

      * **准备 (Arrange)**:
          * 使用 `db_session` fixture。
          * 首先创建一个 `LiveRoom` 对象（作为外键依赖）。
          * 使用 `Faker` 生成随机的 `tab_key` 和 `title`（如 `f"tab_{uuid.uuid4().hex[:8]}"`）。
          * 准备一个 `LiveRoomTabCreate` 对象（`tab_key`, `title`, `content_type=LiveRoomTabContentType.TEXT`, `text_content="测试内容"`, `sort_order=0`, `is_active=True`）。
      * **执行 (Act)**:
          * 调用 `await crud_live_features.create_tab(db, obj_in, room_id)`。
      * **断言 (Assert)**:
          * **必须**断言返回的 `new_tab` 对象不为 `None`。
          * **必须**断言 `new_tab.id` 是一个有效的 UUID。
          * **必须**断言 `new_tab.room_id == room_id`。
          * **必须**断言 `new_tab.tab_key == obj_in.tab_key`。
          * **必须**断言 `new_tab.title == obj_in.title`。
          * **必须**断言 `new_tab.content_type == obj_in.content_type`。
          * **必须**断言 `new_tab.text_content == obj_in.text_content`。
          * **必须**断言 `new_tab.sort_order == obj_in.sort_order`。
          * **必须**断言 `new_tab.is_active == obj_in.is_active`。
          * **必须**断言 `new_tab.created_at` 不为 `None`。
          * **必须**断言 `new_tab.updated_at` 不为 `None`。
          * **[关键] 数据库持久化验证**: **必须**再次调用 `await crud_live_features.get_tab(db, new_tab.id)`，断言能够重新查询到该对象。

2.  **`test_create_tab_with_invalid_room_id_raises_integrity_error`** (失败场景 - 外键约束):

      * **准备 (Arrange)**:
          * 准备一个**不存在的** `room_id`（如 `uuid.uuid4()`）。
          * 准备一个有效的 `LiveRoomTabCreate` 对象。
      * **执行 & 断言 (Act & Assert)**:
          * **必须**使用 `with pytest.raises(IntegrityError):` 包裹 `await crud_live_features.create_tab(db, obj_in, invalid_room_id)` 调用。

#### **函数 2: `async def get_tab(db, tab_id)`**

1.  **`test_get_tab_success`** (成功场景):

      * **准备 (Arrange)**:
          * 使用 `db_session`。
          * 创建一个 `LiveRoom` 和一个 `LiveRoomTab` 对象。
      * **执行 (Act)**:
          * 调用 `await crud_live_features.get_tab(db, tab.id)`。
      * **断言 (Assert)**:
          * **必须**断言返回的对象不为 `None`。
          * **必须**断言 `result.id == tab.id`。
          * **必须**断言 `result.tab_key == tab.tab_key`。

2.  **`test_get_tab_not_found`** (失败场景):

      * **准备 (Arrange)**:
          * 准备一个**不存在的** `tab_id`（如 `uuid.uuid4()`）。
      * **执行 (Act)**:
          * 调用 `await crud_live_features.get_tab(db, non_existent_id)`。
      * **断言 (Assert)**:
          * **必须**断言返回结果为 `None`。

#### **函数 3: `async def get_tab_with_room(db, tab_id)`**

1.  **`test_get_tab_with_room_success`** (成功场景 - 验证预加载):

      * **准备 (Arrange)**:
          * 创建一个 `LiveRoom` 和一个 `LiveRoomTab`。
      * **执行 (Act)**:
          * 调用 `await crud_live_features.get_tab_with_room(db, tab.id)`。
      * **断言 (Assert)**:
          * **必须**断言返回的对象不为 `None`。
          * **必须**断言 `result.id == tab.id`。
          * **[关键] 预加载验证**: **必须**断言 `result.room` 不为 `None`（关系已预加载）。
          * **必须**断言 `result.room.id == room.id`。

2.  **`test_get_tab_with_room_not_found`** (失败场景):

      * **准备 (Arrange)**:
          * 准备一个不存在的 `tab_id`。
      * **执行 (Act)**:
          * 调用 `await crud_live_features.get_tab_with_room(db, non_existent_id)`。
      * **断言 (Assert)**:
          * **必须**断言返回结果为 `None`。

#### **函数 4: `async def get_all_by_room_id(db, room_id, skip, limit)`**

1.  **`test_get_all_by_room_id_success`** (成功场景 - 分页):

      * **准备 (Arrange)**:
          * 创建一个 `LiveRoom`。
          * 创建 **3 个** `LiveRoomTab` 对象，分别设置 `sort_order=0, 1, 2`。
      * **执行 (Act)**:
          * 调用 `await crud_live_features.get_all_by_room_id(db, room_id, skip=0, limit=10)`。
      * **断言 (Assert)**:
          * **必须**断言返回值为 `(tabs, total)` 元组。
          * **必须**断言 `total == 3`。
          * **必须**断言 `len(tabs) == 3`。
          * **[关键] 排序验证**: **必须**断言 `tabs[0].sort_order < tabs[1].sort_order < tabs[2].sort_order`。

2.  **`test_get_all_by_room_id_pagination`** (分页场景):

      * **准备 (Arrange)**:
          * 创建一个 `LiveRoom`。
          * 创建 **5 个** `LiveRoomTab` 对象。
      * **执行 (Act)**:
          * 调用 `await crud_live_features.get_all_by_room_id(db, room_id, skip=2, limit=2)`。
      * **断言 (Assert)**:
          * **必须**断言 `total == 5`。
          * **必须**断言 `len(tabs) == 2`（返回第 3-4 个）。

3.  **`test_get_all_by_room_id_empty`** (空结果场景):

      * **准备 (Arrange)**:
          * 创建一个 `LiveRoom`（但不创建任何 Tab）。
      * **执行 (Act)**:
          * 调用 `await crud_live_features.get_all_by_room_id(db, room_id, skip=0, limit=10)`。
      * **断言 (Assert)**:
          * **必须**断言 `total == 0`。
          * **必须**断言 `len(tabs) == 0`。

#### **函数 5: `async def get_active_by_room_id(db, room_id)`**

1.  **`test_get_active_by_room_id_success`** (成功场景 - 只返回激活的):

      * **准备 (Arrange)**:
          * 创建一个 `LiveRoom`。
          * 创建 **3 个** Tab：2 个 `is_active=True`，1 个 `is_active=False`。
      * **执行 (Act)**:
          * 调用 `await crud_live_features.get_active_by_room_id(db, room_id)`。
      * **断言 (Assert)**:
          * **必须**断言 `len(tabs) == 2`（只返回激活的）。
          * **必须**断言所有返回的 Tab 的 `is_active == True`。
          * **[关键] 排序验证**: **必须**断言返回列表按 `sort_order` 升序排列。

2.  **`test_get_active_by_room_id_empty`** (空结果场景):

      * **准备 (Arrange)**:
          * 创建一个 `LiveRoom`（但不创建任何 Tab）。
      * **执行 (Act)**:
          * 调用 `await crud_live_features.get_active_by_room_id(db, room_id)`。
      * **断言 (Assert)**:
          * **必须**断言 `len(tabs) == 0`。

#### **函数 6: `async def update_tab(db, db_obj, obj_in)`**

1.  **`test_update_tab_success`** (成功场景):

      * **准备 (Arrange)**:
          * 创建一个 `LiveRoom` 和一个 `LiveRoomTab`。
          * 准备一个 `LiveRoomTabUpdate` 对象，更新 `title` 和 `is_active`。
      * **执行 (Act)**:
          * 调用 `await crud_live_features.update_tab(db, db_tab, obj_in)`。
      * **断言 (Assert)**:
          * **必须**断言返回的对象不为 `None`。
          * **必须**断言 `updated_tab.title == obj_in.title`（新值）。
          * **必须**断言 `updated_tab.is_active == obj_in.is_active`（新值）。
          * **[关键] 数据库持久化验证**: **必须**再次调用 `await crud_live_features.get_tab(db, updated_tab.id)`，断言数据库中的值已更新。

2.  **`test_update_tab_partial_update`** (部分更新场景):

      * **准备 (Arrange)**:
          * 创建一个 Tab，初始 `title="原标题"`, `sort_order=0`。
          * 准备一个 `LiveRoomTabUpdate` 对象，**只**更新 `sort_order=5`。
      * **执行 (Act)**:
          * 调用 `await crud_live_features.update_tab(db, db_tab, obj_in)`。
      * **断言 (Assert)**:
          * **必须**断言 `updated_tab.sort_order == 5`（已更新）。
          * **必须**断言 `updated_tab.title == "原标题"`（未更新，保持原值）。

#### **函数 7: `async def remove_tab(db, db_obj)`**

1.  **`test_remove_tab_success`** (成功场景):
      * **准备 (Arrange)**:
          * 创建一个 `LiveRoom` 和一个 `LiveRoomTab`。
          * 记录 `tab_id = tab.id`。
      * **执行 (Act)**:
          * 调用 `await crud_live_features.remove_tab(db, db_tab)`。
      * **断言 (Assert)**:
          * **必须**断言返回的对象不为 `None`（返回被删除的对象）。
          * **[关键] 数据库删除验证**: **必须**再次调用 `await crud_live_features.get_tab(db, tab_id)`，**断言返回结果为 `None`**（已从数据库删除）。

-----

### B. 针对 `app/crud/live_features.py` - LiveRoomMessage CRUD 测试（实用派）

#### **函数 8: `async def create_message(db, obj_in)`**

1.  **`test_create_message_success`** (成功场景):

      * **准备 (Arrange)**:
          * 创建一个 `LiveRoom` 和一个 `LiveSession`（作为外键依赖）。
          * 使用 `Faker` 生成随机的 `content`（如 `fake.text(max_nb_chars=100)`）。
          * 准备一个 `LiveRoomMessageCreateInternal` 对象（包含 `room_id`, `session_id`, `user_id`, `user_role=LiveRoomMessageUserRole.REGULAR`, `content`）。
      * **执行 (Act)**:
          * 调用 `await crud_live_features.create_message(db, obj_in)`。
      * **断言 (Assert)**:
          * **必须**断言返回的 `new_message` 对象不为 `None`。
          * **必须**断言 `new_message.id` 是一个有效的 UUID。
          * **必须**断言 `new_message.room_id == obj_in.room_id`。
          * **必须**断言 `new_message.user_id == obj_in.user_id`。
          * **必须**断言 `new_message.user_role == obj_in.user_role`。
          * **必须**断言 `new_message.content == obj_in.content`。
          * **必须**断言 `new_message.is_deleted == False`（默认值）。
          * **必须**断言 `new_message.created_at` 不为 `None`。
          * **[关键] 数据库持久化验证**: **必须**使用 `await db.refresh(new_message)` 或再次查询，验证数据已持久化。

2.  **`test_create_message_without_session_id`** (session\_id 可选场景):

      * **准备 (Arrange)**:
          * 创建一个 `LiveRoom`（不创建 Session）。
          * 准备一个 `LiveRoomMessageCreateInternal` 对象，`session_id=None`。
      * **执行 (Act)**:
          * 调用 `await crud_live_features.create_message(db, obj_in)`。
      * **断言 (Assert)**:
          * **必须**断言创建成功。
          * **必须**断言 `new_message.session_id == None`。

3.  **`test_create_message_with_invalid_room_id_raises_integrity_error`** (失败场景 - 外键约束):

      * **准备 (Arrange)**:
          * 准备一个**不存在的** `room_id`。
          * 准备一个有效的 `LiveRoomMessageCreateInternal` 对象。
      * **执行 & 断言 (Act & Assert)**:
          * **必须**使用 `with pytest.raises(IntegrityError):` 包裹调用。

#### **函数 9: `async def get_messages_by_room(db, room_id, page, size, since)`**

1.  **`test_get_messages_by_room_success`** (成功场景 - 分页):

      * **准备 (Arrange)**:
          * 创建一个 `LiveRoom` 和一个 `user_id`。
          * 创建 **5 个** `LiveRoomMessage` 对象（使用不同的 `content` 和 `created_at`）。
      * **执行 (Act)**:
          * 调用 `await crud_live_features.get_messages_by_room(db, room_id, page=1, size=10, since=None)`。
      * **断言 (Assert)**:
          * **必须**断言返回值为 `(messages, total)` 元组。
          * **必须**断言 `total == 5`。
          * **必须**断言 `len(messages) == 5`。
          * **[关键] 排序验证**: **必须**断言返回列表按 `created_at` 降序排列（最新的在前）。
          * **[关键] 软删除过滤**: **必须**断言所有返回的消息 `is_deleted == False`。

2.  **`test_get_messages_by_room_pagination`** (分页场景):

      * **准备 (Arrange)**:
          * 创建 **10 个** `LiveRoomMessage`。
      * **执行 (Act)**:
          * 调用 `await crud_live_features.get_messages_by_room(db, room_id, page=2, size=3, since=None)`。
      * **断言 (Assert)**:
          * **必须**断言 `total == 10`。
          * **必须**断言 `len(messages) == 3`（第 4-6 条）。

3.  **`test_get_messages_by_room_with_since_filter`** (时间过滤场景):

      * **准备 (Arrange)**:
          * 创建 **3 个** 留言，手动设置 `created_at`（例如使用 `datetime.utcnow()` 加减时间间隔）。
          * 记录中间时间点 `middle_time`。
      * **执行 (Act)**:
          * 调用 `await crud_live_features.get_messages_by_room(db, room_id, page=1, size=10, since=middle_time)`。
      * **断言 (Assert)**:
          * **必须**断言返回的 `total` 和 `len(messages)` 只包含 `created_at > middle_time` 的留言。

4.  **`test_get_messages_by_room_excludes_deleted`** (软删除过滤场景):

      * **准备 (Arrange)**:
          * 创建 **3 个** 留言：2 个 `is_deleted=False`，1 个 `is_deleted=True`。
      * **执行 (Act)**:
          * 调用 `await crud_live_features.get_messages_by_room(db, room_id, page=1, size=10, since=None)`。
      * **断言 (Assert)**:
          * **必须**断言 `total == 2`（排除已删除的）。
          * **必须**断言 `len(messages) == 2`。
          * **必须**断言所有返回的消息 `is_deleted == False`。

5.  **`test_get_messages_by_room_empty`** (空结果场景):

      * **准备 (Arrange)**:
          * 创建一个 `LiveRoom`（但不创建任何留言）。
      * **执行 (Act)**:
          * 调用 `await crud_live_features.get_messages_by_room(db, room_id, page=1, size=10, since=None)`。
      * **断言 (Assert)**:
          * **必须**断言 `total == 0`。
          * **必须**断言 `len(messages) == 0`。

-----

### C. 测试类组织（推荐结构）

为保持测试文件清晰，建议按以下结构组织：

```python
class TestLiveRoomTabCRUD:
    """LiveRoomTab CRUD 操作测试"""
    
    # test_create_tab_success
    # test_create_tab_with_invalid_room_id_raises_integrity_error
    # test_get_tab_success
    # test_get_tab_not_found
    # test_get_tab_with_room_success
    # test_get_tab_with_room_not_found
    # test_get_all_by_room_id_success
    # test_get_all_by_room_id_pagination
    # test_get_all_by_room_id_empty
    # test_get_active_by_room_id_success
    # test_get_active_by_room_id_empty
    # test_update_tab_success
    # test_update_tab_partial_update
    # test_remove_tab_success


class TestLiveRoomMessageCRUD:
    """LiveRoomMessage CRUD 操作测试"""
    
    # test_create_message_success
    # test_create_message_without_session_id
    # test_create_message_with_invalid_room_id_raises_integrity_error
    # test_get_messages_by_room_success
    # test_get_messages_by_room_pagination
    # test_get_messages_by_room_with_since_filter
    # test_get_messages_by_room_excludes_deleted
    # test_get_messages_by_room_empty
```

-----

#### 8\. 交付物 (Deliverable - 执行者)

请根据**以上所有规范 (1-7)**，为 `Section 6` 中提供的代码生成**完整的 `pytest` 测试文件**。

  * **交付物**:
      * `tests/unit/test_crud_live_features.py`
  * **指令**:
    1.  **遵循任务列表**: 严格按照 `Section 7` 中的列表生成所有指定的测试用例（**共 22 个测试用例**）。
    2.  **遵循所有规范**: 确保生成的代码 100% 遵循 `Section 2-5` (哲学, 语法, 断言, 风格)。
    3.  **实用派测试**: 本测试文件属于 CRUD 层测试，**必须**使用真实数据库（`db_session`）。
    4.  **数据隔离**: 所有创建的测试数据**必须**使用 `Faker` 或 `uuid` 生成随机值。
    5.  **数据库持久化验证**: 所有 Create/Update/Delete 操作**必须**通过再次查询来验证数据库状态。
    6.  **必须使用 `async for`**: 所有测试函数必须使用 `async for db in db_session:` 语法。
    7.  **依赖创建**: 测试中需要先创建必需的依赖对象（如 `LiveRoom`, `LiveSession`），可参考项目中现有的测试文件（如 `tests/unit/test_crud_room.py`）。

-----

### 9\. 关键提示

#### 9.1. 外键依赖处理

由于 `LiveRoomTab` 和 `LiveRoomMessage` 依赖 `LiveRoom` (以及 `LiveSession`)，测试中需要：

```python
# 示例：创建依赖对象
from app.models.live_core import LiveRoom, LiveSession, LiveSessionStatus

async for db in db_session:
    # 创建 LiveRoom 依赖
    room = LiveRoom(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        title=f"Test Room {uuid.uuid4().hex[:8]}",
        stream_key=f"stream_{uuid.uuid4().hex}"
    )
    db.add(room)
    await db.commit()
    await db.refresh(room)
    
    # 创建 LiveSession 依赖（如果需要）
    session = LiveSession(
        id=uuid.uuid4(),
        room_id=room.id,
        status=LiveSessionStatus.LIVE,
        start_time=datetime.utcnow()
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
```

#### 9.2. Faker 使用示例

```python
from faker import Faker
import uuid

fake = Faker()

# 生成随机 tab_key（唯一）
tab_key = f"tab_{uuid.uuid4().hex[:8]}"

# 生成随机 title
title = fake.sentence(nb_words=3)

# 生成随机 content
content = fake.text(max_nb_chars=100)
```

#### 9.3. ENUM 使用

```python
from app.models.live_features import LiveRoomTabContentType, LiveRoomMessageUserRole

# 在测试数据中使用 ENUM
content_type = LiveRoomTabContentType.TEXT
user_role = LiveRoomMessageUserRole.REGULAR
```

-----

### 10\. 最终检查清单

生成的测试代码必须满足：

  - [ ] 包含完整的模块文档字符串
  - [ ] 导入所有必需模块（`pytest`, `uuid`, `Faker`, CRUD functions, Models, Schemas）
  - [ ] 使用 `async for db in db_session:` 语法
  - [ ] 所有测试使用 AAA 结构（Arrange, Act, Assert）并注释分隔
  - [ ] 所有唯一性字段使用随机生成
  - [ ] 所有 Create/Update/Delete 操作通过再次查询验证持久化
  - [ ] 包含 `Section 7` 中列出的所有 22 个测试用例
  - [ ] 所有测试函数包含清晰的 docstring
  - [ ] 测试类名为 `TestLiveRoomTabCRUD` 和 `TestLiveRoomMessageCRUD`

-----

**[测试代码生成提示词文档结束]**