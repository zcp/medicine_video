
-----

### 【最终完整版】高效 AI 代码生成提示词 (架构风格迁移母版 v4.1 - 用户身份修复版)

**目标**：获取“实用派”设计文档的**内容**（例如：需要一个 `create_message` 函数），但**强制**将其套用在本文档定义的、完整的“学院派”**架构与工程规范**上。

#### **1. 角色定义 (Role Definition)**

你是一名精通“学院派”架构（Clean Architecture）的资深 Python 后端架构师。你擅长将业务需求（来自设计文档）解耦，并严格执行分层架构。

#### **2. 任务目标 (Task Objective)**

你的任务是为\*\*直播间 Tab 和 留言功能 (Tab & Message)\*\*生成第二阶段的代码，包括：

1.  **自定义异常** (在 `app/exceptions.py` 中补充)
2.  **业务逻辑层 (Service Layer)** (创建 `app/services/live_features_service.py`)
3.  **API端点层 (Endpoint Layer)** (创建 `app/api/v1/endpoints/live_features.py`)
4.  **[关键] 增量修改**：修改**现有**的 `app/api/v1/endpoints/room.py`（假设存在），以实现 `GET /rooms/{id}` 的扩展。

#### **3. 核心架构约束 (\!\!\! 学院派关键规则 \!\!\!)**

你**必须**严格执行“学院派”架构分层（遵循母版 5.1, 5.3.B, 5.3.C）：

  * **`Service` 层 (本提示词生成)**:

      * **负责**：业务逻辑（权限检查、URL 过滤、状态校验）。
      * **严禁**：处理事务（`db.commit/rollback`）。
      * **严禁**：抛出 `HTTPException` 或返回 `JSONResponse`。
      * **[关键] 权限模式**：**必须**遵循 `5.0` 规范，接收 `user_id: UUID` 和 `user_role: Enum`，失败则 `raise PermissionDeniedException("权限不足...")`。

  * **`Endpoint` (API) 层 (本提示词生成)**:

      * **负责**：参数绑定、`Depends` 注入、调用 Service。
      * **[关键] 权限模式**：**必须**遵循 `5.0` 规范，依赖 `get_current_user` 获取 `Dict`，**并在 API 层解析**。
      * **[关键] 异常处理**：**必须**使用 `try/except` 块捕获所有自定义异常（`PermissionDeniedException`, `RoomNotFoundException` 等），并将其转换为 `JSONResponse(status_code=..., content=error_response(code=...))`。
      * **[关键] 路由定义**：**必须**在 `endpoints/xxx.py` 中定义 `APIRouter(tags=["..."])` (不含 `prefix`)。`prefix` **必须**在顶层 `api_router.include_router(...)` 中统一指定。
      * **[关键] URL 拼接**：如需返回 `image_url`，**必须**注入 `request: Request` 并拼接 `base_url`。

#### **4. 核心上下文信息 (Dependencies)**

  * `app/crud/live_features.py`：已存在 `crud_tab` 和 `crud_message` 对象。
  * `app/crud/room.py`：已存在 `crud_room.get(db, room_id)` 函数。
  * `app/core/deps.py`：已存在 `get_current_user(token:...) -> Dict`。 **[V4.1 修改]**：返回类型为 `Dict` (JWT Payload)。
  * `app/core/responses.py`：已存在 `success_response(data)` 和 `error_response(code, message, data)`。
  * `app/models/live_features.py`：已存在 `LiveRoomMessageUserRole` Enum。

-----

#### **5. 具体代码生成指令**

##### **5.0 【新增段落：统一的用户身份解析规范（根据实际 Bug 修复）】**

**（新增）API 层用户提取规范（JWT→UUID+Enum）**

  * **`current_user` 永远是一个 JWT payload `Dict`，而不是 ORM `User` 模型**。 API 层必须使用以下模式解析：

<!-- end list -->

```python
# [V4.1 关键模式]
from typing import Dict
from app.models.live_features import LiveRoomMessageUserRole # 导入 Enum

current_user: Dict = Depends(get_current_user)

# 在进入 try 块之前安全提取
user_id = uuid.UUID(current_user.get("user_id") or current_user.get("sub"))
role_str = current_user.get("role", "REGULAR").upper()
user_role = LiveRoomMessageUserRole.get(role_str, LiveRoomMessageUserRole.REGULAR)

# 日志变量
user_id_log = user_id
user_role_log = user_role
```

  * **（新增）Service 层用户参数规范**
    Service 层方法**不得**接受实体类 `User`，**必须**统一为：

<!-- end list -->

```python
# [V4.1 关键模式]
async def some_action(
    self,
    user_id: UUID,
    user_role: LiveRoomMessageUserRole,
    ...
):
```

-----

##### **5.1. 第一部分：`app/exceptions.py` 补充**

在现有 `app/exceptions.py` 文件中添加以下自定义异常：

```python
# --- 学院派异常 (Service 层抛出) ---

class TabNotFoundException(Exception):
    """Tab 不存在"""
    pass

class MessageNotFoundException(Exception):
    """留言不存在"""
    pass

class RoomNotFoundException(Exception):
    """直播间不存在 (由 Service 层检查并抛出)"""
    pass

class PermissionDeniedException(Exception):
    """权限不足 (由 Service 层检查并抛出)"""
    pass

class InvalidParameterException(Exception):
    """
    业务参数无效 (由 Service 层检查并抛出)
    例如：内容包含非法 URL, content_type 与 content 不匹配
    """
    def __init__(self, message: str, code: int = 4001):
        self.message = message
        self.code = code  # 允许携带业务码
        super().__init__(self.message)

# --- CRUD 层异常 (CRUD 层抛出, API 层捕获) ---
# (假设已存在)
class DatabaseIntegrityException(Exception):
    """数据库完整性异常 (如唯一键冲突)"""
    pass

class DatabaseOperationException(Exception):
    """数据库操作异常 (通用)"""
    pass
```

##### **5.2. 第二部分：`app/services/live_features_service.py`**

**职责**：封装所有 Tab 和 Message 相关的**业务逻辑**。

#### 代码生成模板

```python
"""
直播间 Tab 和 留言功能的 Service 层 (学院派)
职责：
- 业务逻辑验证 (权限检查, URL 过滤, 状态校验)
- 组合 CRUD 操作
- 抛出自定义 Python 异常 (e.g., TabNotFoundException)
- [V4.1 修改] 接收 user_id 和 user_role，而不是 User 对象
- 严禁处理事务 (db.commit/rollback)
- 严禁抛出 HTTPException
"""
import uuid, logging, re
from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

# [学院派] 导入 CRUD 模块
from app.crud import live_features as crud_live_features
from app.crud import room as crud_room # 用于检查 Room 是否存在

from app.models.live_features import LiveRoomTab, LiveRoomMessage, LiveRoomMessageUserRole, LiveRoomTabContentType
from app.models.live_core import LiveRoom # 导入 LiveRoom
from app.schemas.live_features import LiveRoomTabCreate, LiveRoomTabUpdate, LiveRoomMessageCreate, LiveRoomMessageCreateInternal
# [V4.1 修改] 不再需要导入 User 模型
# from app.models.user import User 

# [学院派] 导入自定义异常
from app.exceptions import (
    TabNotFoundException,
    RoomNotFoundException,
    PermissionDeniedException,
    InvalidParameterException
)

logger = logging.getLogger(__name__)

# URL 匹配正则表达式 (用于留言)
URL_REGEX = re.compile(
    r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
)

class TabService:
    """Tab 相关业务逻辑"""
    def __init__(self, db: AsyncSession):
        self.db = db
    
    # ... (实现 TabService 方法) ...

class MessageService:
    """留言相关业务逻辑"""
    def __init__(self, db: AsyncSession):
        self.db = db

    # ... (实现 MessageService 方法) ...
```

#### 需实现的方法清单 (TabService)

1.  **`_check_room_exists(self, room_id: UUID) -> LiveRoom` (辅助函数)**

      * 调用 `crud_room.get(self.db, room_id)`。
      * 如果 `room` 为 `None`，`raise RoomNotFoundException(f"Room ID: {room_id} 不存在")`。
      * 返回 `room`。

2.  **`_check_admin_permission(self, user_role: LiveRoomMessageUserRole)` (辅助函数) [V4.1 修改]**

      * **[V4.1] 权限模式**：
      * `if user_role not in [LiveRoomMessageUserRole.ADMIN, LiveRoomMessageUserRole.SUPERADMIN]:`
      * `raise PermissionDeniedException("无权操作 Tab")`

3.  **`list_tabs_for_admin(self, user_id: UUID, user_role: LiveRoomMessageUserRole, room_id: UUID) -> Tuple[List[LiveRoomTab], int]` [V4.1 修改]**

      * **业务逻辑**：
        1.  `await self._check_admin_permission(user_role)`
        2.  `await self._check_room_exists(room_id)`
        3.  调用 `crud_live_features.get_all_by_room_id(self.db, room_id, 0, 100)` (暂不分页)。

4.  **`get_active_tabs_for_room(self, room_id: UUID) -> List[LiveRoomTab]`**

      * **业务逻辑**：
        1.  `await self._check_room_exists(room_id)` (确保房间存在，即使是公共访问)
        2.  调用 `crud_live_features.get_active_by_room_id(self.db, room_id)`。

5.  **`create_tab(self, user_id: UUID, user_role: LiveRoomMessageUserRole, room_id: UUID, obj_in: LiveRoomTabCreate) -> LiveRoomTab` [V4.1 修改]**

      * **业务逻辑**：
        1.  `await self._check_admin_permission(user_role)`
        2.  `await self._check_room_exists(room_id)`
        3.  **参数校验**：
              * `if obj_in.content_type == LiveRoomTabContentType.TEXT and not obj_in.text_content:`
              * `raise InvalidParameterException("当 content_type=text 时, text_content 不能为空")`
              * (其他 `content_type` 校验)
        4.  调用 `crud_live_features.create_tab(self.db, obj_in, room_id)`。

6.  **`update_tab(self, user_id: UUID, user_role: LiveRoomMessageUserRole, tab_id: UUID, obj_in: LiveRoomTabUpdate) -> LiveRoomTab` [V4.1 修改]**

      * **业务逻辑**：
        1.  `await self._check_admin_permission(user_role)`
        2.  `db_tab = await crud_live_features.get_tab(self.db, tab_id)`
        3.  `if db_tab is None: raise TabNotFoundException(f"Tab ID: {tab_id} 不存在")`
        4.  (可选参数校验)
        5.  调用 `crud_live_features.update_tab(self.db, db_obj=db_tab, obj_in=obj_in)`。

7.  **`delete_tab(self, user_id: UUID, user_role: LiveRoomMessageUserRole, tab_id: UUID) -> LiveRoomTab` [V4.1 修改]**

      * **业务逻辑**：
        1.  `await self._check_admin_permission(user_role)`
        2.  `db_tab = await crud_live_features.get_tab(self.db, tab_id)`
        3.  `if db_tab is None: raise TabNotFoundException(f"Tab ID: {tab_id} 不存在")`
        4.  调用 `crud_live_features.remove_tab(self.db, db_obj=db_tab)`。

#### 需实现的方法清单 (MessageService)

1.  **`_check_room_exists(self, room_id: UUID) -> LiveRoom` (辅助函数)**

      * (同 TabService, 或设为公共)

2.  **`create_message(self, user_id: UUID, user_role: LiveRoomMessageUserRole, room_id: UUID, obj_in: LiveRoomMessageCreate, user_display_name: Optional[str] = None) -> LiveRoomMessage` [V4.1 修改 + 昵称方案 B]**

      * **业务逻辑**：
        1.  `await self._check_room_exists(room_id)`
        2.  **[关键] URL 过滤 (V4.1)**：
              * `is_admin = user_role in [LiveRoomMessageUserRole.ADMIN, LiveRoomMessageUserRole.SUPERADMIN]`
              * `has_url = bool(URL_REGEX.search(obj_in.content))`
              * `if not is_admin and has_url:`
              * `raise InvalidParameterException(code=4004, message="普通用户不允许发送包含 URL 的留言")`
        3.  **[关键] 内部 Schema 转换 + 显示名快照 (V4.1 + 昵称方案 B)**：
              * 根据 `user_display_name` 构造扩展字段：
                * `extra: Optional[Dict[str, Any]] = None`
                * `if user_display_name: extra = {"user_display_name": user_display_name}`
              * 使用 `LiveRoomMessageCreateInternal` 承载所有字段：
                * `internal_obj_in = LiveRoomMessageCreateInternal(`
                * `content=obj_in.content, room_id=room_id, session_id=None, user_id=user_id, user_role=user_role, extra=extra`
                * `)`
              * 这样，昵称/用户名/邮箱被快照在 `LiveRoomMessage.extra.user_display_name` 中，由 CRUD 层原样入库。
        4.  调用 `crud_live_features.create_message(self.db, obj_in=internal_obj_in)`。

3.  **`get_messages(self, room_id: UUID, page: int, size: int, since: Optional[datetime]) -> Tuple[List[LiveRoomMessage], int]`**

      * **业务逻辑**：
        1.  `await self._check_room_exists(room_id)`
        2.  调用 `crud_live_features.get_messages_by_room(self.db, room_id, (page - 1) * size, size, since)` (注意分页计算)。

##### **5.3. 第三部分：`app/api/v1/endpoints/live_features.py`**

**职责**：实现所有 Tab 和 Message 相关的 RESTful API 接口，**必须**处理异常转换。

#### 路由器定义 (遵循母版 5.3.C)

```python
import uuid, logging
from typing import List, Optional, Dict, Any # [V4.1 修改] 导入 Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, Query, Body, Request # [关键] 导入 Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.core.deps import get_current_user # [关键] 只导入 get_current_user
from app.core.responses import success_response, error_response
# [V4.1 修改] 导入 Enum 用于解析
from app.models.live_features import LiveRoomMessageUserRole 

from app.services.live_features_service import TabService, MessageService
from app.schemas.live_features import (
    LiveRoomTabCreate, LiveRoomTabUpdate, LiveRoomTabResponse,
    LiveRoomMessageCreate, LiveRoomMessagePostResponse, PaginatedLiveRoomMessageResponse
)
from app.schemas.response import PaginatedResponse # 假设用于分页

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

# --- 路由器定义 (遵循母版 5.3.C) ---
# 严禁在此处使用 prefix
admin_tab_router = APIRouter(tags=["Admin - Tabs"])
public_message_router = APIRouter(tags=["Public - Messages"])
```

#### API 挂载 (在 `app/api/v1/api.py` 中 - 仅供参考，无需生成)

```python
# (参考)
# api_router.include_router(live_features.admin_tab_router, prefix="/admin")
# api_router.include_router(live_features.public_message_router, prefix="/rooms")
```

#### 需实现的端点清单 (admin\_tab\_router)

1.  **`GET /admin/rooms/{room_id}/tabs` - 查询 Tab 列表 (Admin)**

      * `@admin_tab_router.get("/rooms/{room_id}/tabs")` (遵循母版 5.3.C)
      * `Depends`: `request: Request`, `db: AsyncSession = Depends(get_db)`, `current_user: Dict = Depends(get_current_user)` **[V4.1 修改]**
      * **[学院派] 实现流程 (V4.1)**:
        1.  `logger.info(...)`
        2.  **[V4.1] 身份解析 (5.0)**:
              * `try:`
              * `user_id = uuid.UUID(current_user.get("user_id") or current_user.get("sub"))`
              * `role_str = current_user.get("role", "REGULAR").upper()`
              * `user_role = LiveRoomMessageUserRole.get(role_str, LiveRoomMessageUserRole.REGULAR)`
              * `user_id_log = user_id`
              * `except (AttributeError, TypeError, ValueError) as e:`
              * `logger.warning(f"JWT 解析失败: {e}")`
              * `return JSONResponse(status_code=401, content=error_response(code=3001, message="Token 无效"))`
        3.  **`try`**:
              * `service = TabService(db)`
              * `tabs, total = await service.list_tabs_for_admin(user_id=user_id, user_role=user_role, room_id=room_id)`
              * **URL 拼接 (5.3.C)**: `base_url = str(request.base_url).rstrip('/')` (实现拼接逻辑)
              * `return success_response(data={"items": tabs_with_urls, "total": total})`
        4.  **`except PermissionDeniedException as e:`** (5.3.C)
              * `logger.warning(f"Admin permission denied: user_id={user_id_log}, error={e}")`
              * `return JSONResponse(status_code=403, content=error_response(code=3002, message=str(e)))`
        5.  **`except RoomNotFoundException as e:`** (5.1) -\> 404/2001
        6.  **`except Exception as e:`** (5.1) -\> 500/1000 (记录 `exc_info=True`)

2.  **`POST /admin/rooms/{room_id}/tabs` - 创建 Tab (Admin)**

      * `@admin_tab_router.post("/rooms/{room_id}/tabs")`
      * `Depends`: `request: Request`, `db: AsyncSession = Depends(get_db)`, `current_user: Dict = Depends(get_current_user)` **[V4.1 修改]**
      * `Body`: `obj_in: LiveRoomTabCreate`
      * **[学院派] 实现流程**:
        1.  **[V4.1] 身份解析 (5.0)**: (同上, 解析 `user_id`, `user_role`, `user_id_log`)
        2.  `room_id_log = room_id`
        3.  **`try`**:
              * `service = TabService(db)`
              * `new_tab = await service.create_tab(user_id=user_id, user_role=user_role, room_id=room_id, obj_in=obj_in)`
              * **URL 拼接**: (同上, 拼接 `new_tab.image_url`)
              * `return success_response(data=new_tab_with_url)`
        4.  **`except PermissionDeniedException as e:`** -\> 403/3002
        5.  **`except RoomNotFoundException as e:`** -\> 404/2001
        6.  **`except InvalidParameterException as e:`** -\> 400/`e.code`
        7.  **`except (DatabaseIntegrityException, DatabaseOperationException) as e:`** (来自 CRUD) -\> 400/4001
        8.  **`except Exception as e:`** -\> 500/1000

3.  **`PATCH /admin/tabs/{tab_id}` - 更新 Tab (Admin)**

      * `@admin_tab_router.patch("/tabs/{tab_id}")`
      * `Depends`: `request: Request`, `db`, `current_user: Dict` **[V4.1 修改]**
      * `Body`: `obj_in: LiveRoomTabUpdate`
      * **[学院派] 实现流程**: (同上, **[V4.1]** 解析 `user_id`, `user_role`, 调用 `service.update_tab`, 捕获 `TabNotFoundException`, 拼接 URL)

4.  **`DELETE /admin/tabs/{tab_id}` - 删除 Tab (Admin)**

      * `@admin_tab_router.delete("/tabs/{tab_id}")`
      * `Depends`: `db`, `current_user: Dict` **[V4.1 修改]**
      * **[学院派] 实现流程**: (同上, **[V4.1]** 解析 `user_id`, `user_role`, 调用 `service.delete_tab`, 捕获 `TabNotFoundException`)

#### 需实现的端点清单 (public\_message\_router)

1.  **`POST /rooms/{room_id}/messages` - 发送留言 (Public)**

      * `@public_message_router.post("/{room_id}/messages")`
      * `Depends`: `db: AsyncSession = Depends(get_db)`, `current_user: Dict = Depends(get_current_user)` **[V4.1 修改]**
      * `Body`: `obj_in: LiveRoomMessageCreate`
      * **[学院派] 实现流程 + 昵称方案 B**:
        1.  **[V4.1] 身份解析 (5.0)**: (同上, 解析 `user_id`, `user_role`, `user_id_log`, `user_role_log`)
        2.  **展示名计算（昵称 / 用户名 / 邮箱）**：
              * 在进入 `try` 之前，从 `current_user` 中安全提取展示名：
              * `user_display_name = current_user.get("nickname") or current_user.get("username") or current_user.get("email")`
        3.  **`try`**:
              * `service = MessageService(db)`
              * `new_msg = await service.create_message(user_id=user_id, user_role=user_role, room_id=room_id, obj_in=obj_in, user_display_name=user_display_name)`
              * **[关键] 响应规范 (5.2)**：
                * `new_msg` 对象包含 `user_id` 和 `extra`（其中可能含有 `user_display_name`）；
                * API 响应 Schema (`LiveRoomMessagePostResponse`) 必须**不**直接暴露 `user_id`，而是通过显式字段 `user_display_name` 暴露展示名：
                  * `response_data = LiveRoomMessagePostResponse.model_validate(new_msg)`
                  * `extra = getattr(new_msg, "extra", None)`
                  * `if isinstance(extra, dict) and extra.get("user_display_name"):` 使用 `model_copy(update={"user_display_name": extra["user_display_name"]})` 回填展示名。
              * `return success_response(data=response_data)`
        4.  **`except RoomNotFoundException as e:`** -\> 404/2001
        5.  **`except InvalidParameterException as e:`** (捕获 URL 过滤 4004) -\> 400/`e.code`
        6.  **`except (DatabaseIntegrityException, DatabaseOperationException) as e:`** -\> 400/4001
        7.  **`except Exception as e:`** -\> 500/1000

2.  **`GET /rooms/{room_id}/messages` - 获取留言列表 (Public)**

      * `@public_message_router.get("/{room_id}/messages")`
      * `Depends`: `db: AsyncSession = Depends(get_db)`
      * `Query`: `page: int = 1`, `size: int = 20`, `since: Optional[datetime] = None`
      * **[学院派] 实现流程 + 昵称方案 B**:
        1.  `try`:
              * `service = MessageService(db)`
              * `messages, total = await service.get_messages(room_id, page, size, since)`
              * 将 ORM 列表逐条映射为 `LiveRoomMessageListResponseItem`，并从 `msg.extra.user_display_name`（若存在）回填响应字段：
                * 遍历 `messages`：
                  * `item = LiveRoomMessageListResponseItem.model_validate(msg)`
                  * `extra = getattr(msg, "extra", None)`
                  * `if isinstance(extra, dict) and extra.get("user_display_name"):` 使用 `model_copy(update={"user_display_name": extra["user_display_name"]})` 写入展示名；
                  * 将 `item` 收集进 `items` 列表。
              * `paginated_data = PaginatedResponse[LiveRoomMessageListResponseItem](items=items, total=total, page=page, size=size)` (假设 `PaginatedResponse` 存在)
              * `return success_response(data=paginated_data)`
        2.  `except RoomNotFoundException as e:` -\> 404/2001
        3.  `except Exception as e:` -\> 500/1000

##### **5.4. 第四部分：修改 `app/api/v1/endpoints/room.py` (增量修改)**

**职责**：实现对 `GET /rooms/{id}` 接口的**增量修改** (遵循母版 4.0)。

  * **目标文件**: `app/api/v1/endpoints/room.py` (假设此文件已存在并包含 `room_router`)

<!-- end list -->

```python
# --- 在 room.py 文件的 imports 中添加 ---
from fastapi import Request # 导入 Request
from app.services.live_features_service import TabService # 导入新 Service
from app.schemas.live_features import LiveRoomTabResponse # 导入新 Schema
from app.schemas.room import LiveRoomDetailResponse # 假设的响应 Schema
# [V4.1 修改] 导入 RoomNotFoundException
from app.exceptions import RoomNotFoundException 
from app.crud import room as crud_room # 导入 crud_room

# --- 找到并修改现有的 get_room 端点 ---

@room_router.get("/{room_id}", response_model=...)
async def get_room_details(
    room_id: uuid.UUID,
    request: Request, # [关键] 注入 Request
    db: AsyncSession = Depends(get_db)
):
    """
    获取单个直播房间详情 (扩展：包含 Tabs)
    """
    # [学院派] 启用 try/except
    try:
        # 1. (原逻辑) 调用 RoomService (假设)
        # room_service = RoomService(db)
        # room_details_obj = await room_service.get_room_by_id(room_id)
        # (假设 room_details_obj 是 ORM 对象或字典)
        
        # 2. [新增逻辑] 调用 TabService
        tab_service = TabService(db)
        # [V4.1 修改] Service 层现在可能会抛出 RoomNotFoundException
        active_tabs = await tab_service.get_active_tabs_for_room(room_id=room_id)
        
        # 3. [新增逻辑] 拼接 URL (母版 5.3.C)
        base_url = str(request.base_url).rstrip('/')
        tabs_with_urls = []
        for tab in active_tabs:
            tab_response = LiveRoomTabResponse.model_validate(tab) # 转换为 Pydantic
            if tab_response.image_url and not tab_response.image_url.startswith('http'):
                tab_response.image_url = f"{base_url}{tab_response.image_url}"
            tabs_with_urls.append(tab_response)
        
        # 4. (原逻辑) 组装响应
        # room_response_data = LiveRoomDetailResponse.model_validate(room_details_obj).model_dump()
        # room_response_data["tabs"] = tabs_with_urls # 附加 tabs
        
        # (简化版示例，假设已在 tab_service.get_active_tabs_for_room 中检查了 room 是否存在)
        room_details_obj = await crud_room.get(db, room_id) # 假设的调用
        if not room_details_obj:
             # 这一步理论上已被 tab_service 覆盖，但作为双重检查
            raise RoomNotFoundException(f"Room ID: {room_id} 不存在")
        
        room_response_data = {"id": room_details_obj.id, "title": room_details_obj.title, "tabs": tabs_with_urls}
        
        return success_response(data=room_response_data)
        
    except RoomNotFoundException as e:
        logger.warning(f"Room not found: {e}")
        return JSONResponse(status_code=404, content=error_response(code=2001, message=str(e)))
    except Exception as e:
        logger.error(f"Error getting room details: {e}", exc_info=True)
        return JSONResponse(status_code=500, content=error_response(code=1000, message=f"内部错误: {e}"))
```

#### **6. 最终交付 (Final Deliverable)**

请根据以上所有要求（特别是 3. 核心架构约束、5.0 身份规范 和 5. 具体代码生成指令），为我生成**四个**交付物：

1.  **`app/exceptions.py`**（仅包含需要补充的 7 个自定义异常类）。
2.  **`app/services/live_features_service.py`**（完整的 Service 层代码，包含 `TabService` 和 `MessageService` 及其所有方法，**必须**使用 `user_id` 和 `user_role`）。
3.  **`app/api/v1/endpoints/live_features.py`**（完整的、用于 Tab 和 Message 的**新** Endpoint 文件，**必须**依赖 `current_user: Dict` 并在 `try` 块**之前**解析 `user_id` 和 `user_role`）。
4.  **`app/api/v1/endpoints/room.py` 的修改片段**（仅展示**如何修改**现有的 `get_room_details` 端点以添加 `tabs` 字段）。

**代码应包含**：

1.  完整的模块文档字符串。
2.  所有必要的导入语句。
3.  所有在 "需实现的方法清单" 中列出的 Service 方法和 API 端点。
4.  Service 层**必须**只 `raise` 自定义异常（`PermissionDeniedException`, `RoomNotFoundException` 等）。
5.  API 层**必须**使用 `try/except` 块捕获所有自定义异常，并返回 `JSONResponse`（使用 `success_response` 和 `error_response`）。
6.  API 层的 Admin 接口**必须**依赖 `get_current_user`（而非 `get_current_admin_user`），并在 `except PermissionDeniedException` 块中返回 403/3002。
7.  所有需要返回 URL 的 API（如 `GET /tabs`）**必须**注入 `request: Request` 并拼接 `base_url`。
8.  **必须**严格遵循“安全异步异常处理”规范（提前提取日志变量）。