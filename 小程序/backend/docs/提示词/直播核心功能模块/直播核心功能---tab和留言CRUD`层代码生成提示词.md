### 1\. `CRUD 层函数代码生成提示词文档 (Tab 和 Message 功能)`

# 直播间 Tab & 留言功能代码生成提示词 - 第一阶段（CRUD层）

## 1\. 角色定义 (Role Definition)

你是一名精通“学院派”架构的资深 Python 后端工程师，擅长异步 SQLAlchemy 2.0。你的任务是编写纯粹的、高性能的、事务安全的数据访问层（CRUD）代码。

## 2\. 任务目标 (Task Objective)

你的任务是为\*\*直播间 Tab 和 留言功能 (Tab & Message)\*\*生成 `app/crud/live_features.py` 文件，封装所有与 `LiveRoomTab` 和 `LiveRoomMessage` 模型相关的数据库操作。

## 3\. 核心架构约束 (学院派)

  * **职责**：CRUD 层**只负责数据访问**，不包含任何业务逻辑（如权限检查）。
  * **[关键] 事务处理**: (遵循母版 5.1, 5.3.A)
      * 所有“写”操作（`create`, `update`, `remove`, `batch_add`）**必须**包含完整的 `try/except IntegrityError/Exception...` 块。
      * **必须**在 `try` 块中处理 `await db.commit()`。
      * **必须**在 `except` 块中处理 `await db.rollback()`。
  * **[关键] 日志与安全**: (遵循母版 5.1)
      * **必须**在 `except` 块中记录 `logger.error`。
      * **必须**遵循“安全异步异常处理”规范：在 `try` 块之前提取所有用于 `except` 块日志记录的变量。

## 4\. 核心上下文信息 (Models & Schemas)

你必须严格依据以下（已符合学院派规范的）模型和 Schema 进行编码：

#### `app/models/live_features.py` (学院派 ENUM 版)

```python
"""
直播间 Tab 和留言功能的数据库模型 (学院派 ENUM 版)
"""
import uuid, enum
from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, ForeignKey, Enum as SAEnum, Index, TIMESTAMP, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, selectinload # 导入 selectinload
from sqlalchemy.sql import func
from app.database import Base

# --- 枚举类型 ---
class LiveRoomMessageUserRole(str, enum.Enum):
    REGULAR = 'REGULAR'
    MODERATOR = 'MODERATOR'
    ADMIN = 'ADMIN'
    SUPERADMIN = 'SUPERADMIN'

class LiveRoomTabContentType(str, enum.Enum):
    TEXT = 'text'
    IMAGE = 'image'
    MIXED = 'mixed'

# --- 模型 ---
class LiveRoomMessage(Base):
    __tablename__ = "live_room_messages"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    room_id = Column(UUID(as_uuid=True), ForeignKey("live_rooms.id", ondelete="CASCADE"), nullable=False)
    session_id = Column(UUID(as_uuid=True), ForeignKey("live_sessions.id", ondelete="SET NULL"), nullable=True)
    user_id = Column(UUID(as_uuid=True), nullable=False, comment='存储 users.public_id')
    user_role = Column(SAEnum(LiveRoomMessageUserRole, name='live_room_message_user_role', native_enum=False), nullable=False, comment='用户角色快照')
    content = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    is_deleted = Column(Boolean, nullable=False, default=False)
    extra = Column(JSONB, nullable=True)
    room = relationship("LiveRoom")
    session = relationship("LiveSession")
    __table_args__ = (
        Index('idx_live_room_messages_room_created', 'room_id', 'created_at'),
        Index('idx_live_room_messages_session_created', 'session_id', 'created_at'),
    )

class LiveRoomTab(Base):
    __tablename__ = "live_room_tabs"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    room_id = Column(UUID(as_uuid=True), ForeignKey("live_rooms.id", ondelete="CASCADE"), nullable=False)
    tab_key = Column(String(64), nullable=False, comment='系统级 key')
    title = Column(String(128), nullable=False, comment='展示名称')
    content_type = Column(SAEnum(LiveRoomTabContentType, name='live_room_tab_content_type', native_enum=False), nullable=False, comment="'text' | 'image' | 'mixed'")
    text_content = Column(Text, nullable=True)
    image_url = Column(Text, nullable=True)
    sort_order = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    room = relationship("LiveRoom")
    __table_args__ = (Index('idx_live_room_tabs_room_sort', 'room_id', 'sort_order'), )
```

#### `app/schemas/live_features.py` (相关 Schemas)

```python
from pydantic import BaseModel, Field
import uuid
from typing import Optional, Dict, Any
# (假设 Enum 类已在此文件中定义)

class LiveRoomTabCreate(BaseModel):
    tab_key: str = Field(..., max_length=64)
    title: str = Field(..., max_length=128)
    content_type: LiveRoomTabContentType
    text_content: Optional[str] = None
    image_url: Optional[str] = None
    sort_order: int = Field(default=0, ge=0)
    is_active: bool = Field(default=True)

class LiveRoomTabUpdate(BaseModel):
    tab_key: Optional[str] = Field(None, max_length=64)
    title: Optional[str] = Field(None, max_length=128)
    content_type: Optional[LiveRoomTabContentType] = None
    text_content: Optional[str] = None
    image_url: Optional[str] = None
    sort_order: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None

class LiveRoomMessageCreateInternal(BaseModel):
    """[学院派] 内部 CRUD Schema (遵循母版 5.2)"""
    room_id: uuid.UUID
    session_id: Optional[uuid.UUID]
    user_id: uuid.UUID
    user_role: LiveRoomMessageUserRole
    content: str = Field(..., min_length=1, max_length=500)
    extra: Optional[Dict[str, Any]] = Field(
        default=None,
        description="扩展字段，例如包含 user_display_name（用户展示名称/昵称快照）等展示信息"
    )
```

## 5\. 具体代码生成指令 - CRUD Layer (`app/crud/live_features.py`)

### 5.1. 导入语句

```python
import uuid
import logging
from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError

# 导入模型 (学院派 ENUM 版)
from app.models.live_features import LiveRoomTab, LiveRoomMessage, LiveRoomTabContentType, LiveRoomMessageUserRole
# 导入 Schemas (学院派 ENUM 版)
from app.schemas.live_features import LiveRoomTabCreate, LiveRoomTabUpdate, LiveRoomMessageCreateInternal

logger = logging.getLogger(__name__)
```

### 5.2. 需实现的函数清单

#### **直播间 Tab (LiveRoomTab) 相关操作**

1.  **`create_tab(db: AsyncSession, obj_in: LiveRoomTabCreate, room_id: UUID) -> LiveRoomTab`**

      * 功能：创建新 Tab。
      * **[学院派] 规范 (5.1, 5.3.A)**：
          * 应用层生成 `id=uuid.uuid4()`。
          * **必须**遵循“安全异步异常处理”规范（提前提取日志变量）。
          * **必须**包含 `try/except IntegrityError/Exception` 块。
          * **必须**在 `try` 中 `await db.commit()`。
          * **必须**在 `except` 中 `await db.rollback()`、`logger.error` 并 `raise`。

2.  **`get_tab(db: AsyncSession, tab_id: UUID) -> Optional[LiveRoomTab]`**

      * 功能：根据 ID 获取单个 Tab（为 Service 层更新/删除准备）。
      * 实现：`select(LiveRoomTab).where(LiveRoomTab.id == tab_id)`。

3.  **`get_tab_with_room(db: AsyncSession, tab_id: UUID) -> Optional[LiveRoomTab]`**

      * 功能：获取 Tab 并预加载 `room` 关系（为 Service 层权限检查准备）。
      * **[学院派] 规范 (5.3.A)**：**必须**使用 `selectinload(LiveRoomTab.room)` 避免 N+1。
      * 实现：`select(LiveRoomTab).options(selectinload(LiveRoomTab.room)).where(LiveRoomTab.id == tab_id)`。

4.  **`get_all_by_room_id(db: AsyncSession, room_id: UUID, skip: int = 0, limit: int = 100) -> Tuple[List[LiveRoomTab], int]`**

      * 功能：分页获取指定 `room_id` 的所有 Tab（后台管理用）。
      * **[学院派] 规范 (5.3.A)**：**必须**使用“分页模式”：
        1.  `select(func.count(LiveRoomTab.id)).where(LiveRoomTab.room_id == room_id)` 获取 `total`。
        2.  `select(LiveRoomTab).where(LiveRoomTab.room_id == room_id).order_by(LiveRoomTab.sort_order.asc()).offset(skip).limit(limit)` 获取 `items`。

5.  **`get_active_by_room_id(db: AsyncSession, room_id: UUID) -> List[LiveRoomTab]`**

      * 功能：获取指定 `room_id` 的所有**激活**的 Tab（前端展示用）。
      * 实现：`where(LiveRoomTab.room_id == room_id, LiveRoomTab.is_active == True)`，按 `sort_order ASC` 排序。
      * **[学院派] 规范 (5.3.A)**：此查询用于 `GET /rooms/{id}` 扩展，**必须**使用 `selectinload(LiveRoomTab.room)` 预加载关系，以备 Service 层使用（即使此函数不直接用）。（*注：修正，此函数用于前端展示，不需要 room 关系，`get_room_details` 才会调用它，因此无需 `selectinload`*）。
      * *修正实现*：`select(LiveRoomTab).where(LiveRoomTab.room_id == room_id, LiveRoomTab.is_active == True).order_by(LiveRoomTab.sort_order.asc())`。

6.  **`update_tab(db: AsyncSession, db_obj: LiveRoomTab, obj_in: LiveRoomTabUpdate) -> LiveRoomTab`**

      * 功能：更新 Tab 信息。
      * 实现：`update_data = obj_in.model_dump(exclude_unset=True)`。
      * **[学院派] 规范 (5.1, 5.3.A)**：**必须**遵循“安全异步异常处理”和“事务处理”规范（`try/commit/rollback`）。

7.  **`remove_tab(db: AsyncSession, db_obj: LiveRoomTab) -> LiveRoomTab`**

      * 功能：删除 Tab。
      * 实现：`await db.delete(db_obj)`。
      * **[学院派] 规范 (5.1, 5.3.A)**：**必须**遵循“安全异步异常处理”和“事务处理”规范（`try/commit/rollback`）。

#### **直播间留言 (LiveRoomMessage) 相关操作**

8.  **`create_message(db: AsyncSession, obj_in: LiveRoomMessageCreateInternal) -> LiveRoomMessage`**

      * 功能：创建新留言。
      * **[学院派] 规范 (5.2)**：**必须**使用 `LiveRoomMessageCreateInternal` Schema，它包含了 Service 层传入的 `user_id`, `room_id` 等所有字段；其中 `extra` 字段用于存放展示类扩展信息（例如 `{"user_display_name": "张三医生"}`）。
      * **[学院派] 规范 (5.1, 5.3.A)**：**必须**遵循“安全异步异常处理”和“事务处理”规范（`try/commit/rollback`）；CRUD 层**不解释** `extra` 的业务含义，仅负责将其原样持久化到 `LiveRoomMessage.extra(JSONB)` 字段。

9.  **`get_messages_by_room(db: AsyncSession, room_id: UUID, page: int, size: int, since: Optional[datetime]) -> Tuple[List[LiveRoomMessage], int]`**

      * 功能：分页获取直播间留言。
      * **[学院派] 规范 (5.3.A)**：**必须**使用“分页模式”（`count()` + `select()`）。
      * 实现：
        1.  构建基础查询 `where(LiveRoomMessage.room_id == room_id, LiveRoomMessage.is_deleted == False)`。
        2.  如果 `since` 提供了，添加 `where(LiveRoomMessage.created_at > since)` 筛选。
        3.  执行 `count()` 查询。
        4.  执行 `select()` 查询，按 `created_at DESC` 排序，并应用 `offset/limit`。

-----
## 6. 最终交付 (Final Deliverable)

请根据以上所有要求（特别是 4. 核心架构约束 和 5. 具体代码生成指令），为我生成 `app/crud/live_features.py` 文件的完整、可直接使用的 Python 代码。

**代码应包含**：
1.  完整的模块文档字符串。
2.  所有必要的导入语句（`uuid`, `logging`, `select`, `AsyncSession`, `selectinload`, `IntegrityError`, Models, Schemas 等）。
3.  `LiveRoomTab` 相关的 7 个 CRUD 函数。
4.  `LiveRoomMessage` 相关的 2 个 CRUD 函数。
5.  所有函数必须有完整的类型注解和 `async def`。
6.  所有“写”操作（`create_tab`, `update_tab`, `remove_tab`, `create_message`）**必须**包含符合学院派规范的 `try/except/rollback` 事务处理和安全日志记录。
7.  所有需要预加载的查询（`get_tab_with_room`）**必须**使用 `selectinload`。
8.  所有分页查询（`get_all_by_room_id`, `get_messages_by_room`）**必须**使用 `count() + select().offset().limit()` 模式。
-----

