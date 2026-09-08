
-----

### 【完整修改版】直播核心功能---Pydantic Schema 代码生成提示词 (学院派 ENUM 版)

# 直播间 Tab & 留言功能 Pydantic Schema 代码生成提示词

-----

## **高效 AI 代码生成提示词：直播间 Tab & 留言功能 Pydantic 模型**

### **1. 角色定义 (Role Definition)**

你是一名精通 FastAPI 和 Pydantic v2 的资深 Python 后端工程师。你的任务是根据已存在的 SQLAlchemy ORM 模型（`live_features.py`），为 `LiveCore Service` 的 Tab 和留言功能生成结构清晰、类型精确且符合最佳实践的 **Pydantic Schema 模型**。

**🔥 关键要求**:

  * 生成的 Pydantic 模型必须与 SQLAlchemy 模型**完全对应**。
  * 严格遵循项目现有的 Schema 设计模式（`Base`, `Create`, `Update`, `InDB`, `Response`）。
  * **必须**参考 `V3.3` 设计文档中的 API 规范来定义 `Create` 和 `Response` 模型。
  * 使用 Pydantic v2 语法。
  * **[学院派]** 必须正确处理 `SAEnum` 到 Pydantic（Python `enum.Enum`）的映射。

-----

### **2. 任务目标 (Task Objective)**

你的目标是生成以下 Python 文件的完整代码：

**文件路径**: `live_core_service/app/schemas/live_features.py`

该文件将包含 Tab 和留言功能所需的所有 Pydantic Schema 模型，用于 API 请求数据验证和响应数据序列化。

-----

### **3. 核心上下文信息 (Core Context Information)**

#### **3.1. 技术栈 (Technology Stack)**

  * **框架**: FastAPI
  * **数据模型**: Pydantic v2 (`ConfigDict`)
  * **Python 版本**: 3.9+

#### **3.2. 项目文件结构 (Project File Structure)**

```
live_core_service/
├── app/
│   ├── ...
│   ├── models/
│   │   ├── live_core.py
│   │   ├── topic.py
│   │   └── live_features.py           # 专题功能 SQLAlchemy 模型（已存在）
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── live_core.py               # 现有 Schema
│   │   ├── topic.py                   # 现有 Schema
│   │   └── live_features.py           # <-- 这是你要生成的目标文件
│   └── ...
```

#### **3.3. SQLAlchemy 模型参考 (Existing SQLAlchemy Models)**

**文件**: `live_core_service/app/models/live_features.py` (这是你刚生成的 **学院派** 版本)

生成的 Pydantic Schema 必须与以下 SQLAlchemy 模型**完全对应**：

```python
"""
直播间 Tab 和留言功能的数据库模型 (学院派 ENUM 版)
"""
import uuid
from datetime import datetime
import enum  # [学院派] 导入 enum

# SQLAlchemy 核心导入
from sqlalchemy import Column, String, Text, Integer, ForeignKey, Enum as SAEnum, Index, TIMESTAMP, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

# ==================== [学院派] 枚举类型定义 ====================
class LiveRoomMessageUserRole(str, enum.Enum):
    REGULAR = 'REGULAR'
    MODERATOR = 'MODERATOR'
    ADMIN = 'ADMIN'
    SUPERADMIN = 'SUPERADMIN'

class LiveRoomTabContentType(str, enum.Enum):
    TEXT = 'text'
    IMAGE = 'image'
    MIXED = 'mixed'

# ==================== 模型类定义 ====================

class LiveRoomMessage(Base):
    """直播间留言表"""
    __tablename__ = "live_room_messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    room_id = Column(UUID(as_uuid=True), ForeignKey("live_rooms.id", ondelete="CASCADE"), nullable=False)
    session_id = Column(UUID(as_uuid=True), ForeignKey("live_sessions.id", ondelete="SET NULL"), nullable=True)
    user_id = Column(UUID(as_uuid=True), nullable=False, comment='存储 users.public_id')
    
    # [学院派] 使用 SAEnum
    user_role = Column(SAEnum(LiveRoomMessageUserRole, name='live_room_message_user_role', create_type=False), nullable=False, comment='用户角色快照')
    
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
    """直播间 Tab 表"""
    __tablename__ = "live_room_tabs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    room_id = Column(UUID(as_uuid=True), ForeignKey("live_rooms.id", ondelete="CASCADE"), nullable=False)
    tab_key = Column(String(64), nullable=False, comment='系统级 key')
    title = Column(String(128), nullable=False, comment='展示名称')
    
    # [学院派] 使用 SAEnum
    content_type = Column(SAEnum(LiveRoomTabContentType, name='live_room_tab_content_type', create_type=False), nullable=False, comment="'text' | 'image' | 'mixed'")
    
    text_content = Column(Text, nullable=True)
    image_url = Column(Text, nullable=True)
    sort_order = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
    room = relationship("LiveRoom")
    
    __table_args__ = (Index('idx_live_room_tabs_room_sort', 'room_id', 'sort_order'), )
```

#### **3.4. API 设计规范参考 (V3.3 文档)**

  * **Tab 创建**: `POST /api/v1/admin/rooms/{room_id}/tabs` - `room_id` 来自路径。
  * **Tab 更新**: `PATCH /api/v1/admin/tabs/{tab_id}` - 字段全可选。
  * **Tab 响应**: `GET /api/v1/admin/rooms/{room_id}/tabs` - 返回 `LiveRoomTab` 完整模型列表。
  * **留言创建**: `POST /api/v1/rooms/{room_id}/messages`
      * `room_id` 来自路径。
      * 请求体: `{ "content": "..." }`
      * `content` 验证: `1 <= len <= 500`。
      * 响应体: `{ id, room_id, user_id, user_role, content, created_at }`
  * **留言列表**: `GET /api/v1/rooms/{room_id}/messages`
      * 响应体 (Paginated): `{ total, page, size, items: [...] }`
      * `items` 字段: `{ id, user_role, content, created_at }`

-----

### **4. 代码生成具体要求 (Specific Code Generation Requirements)**

#### **4.1. 通用规范**

  * **代码风格**: 严格遵循 PEP 8 规范。
  * **Pydantic 版本**: 使用 Pydantic v2 语法 (`model_config = ConfigDict(from_attributes=True)`)。
  * **类型注解**: 所有字段必须有完整的类型注解。
  * **文档字符串**: 每个 Schema 类添加中文文档字符串说明用途。

#### **4.2. 导入语句要求**

```python
from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid
from enum import Enum
```

#### **4.3. [学院派] 枚举类型定义**

  * **[学院派迁移]** 本次增量设计**必须包含**新的 Pydantic Enum 类型，以匹配 SQLAlchemy 模型。
  * 你 **必须** 在 Pydantic Schema 文件的顶部（导入语句之后）定义以下 Python `enum.Enum` 类：

<!-- end list -->

```python
# ==================== 枚举类型定义 ====================
# 必须与 models/live_features.py 中的 ENUM 完全一致

class LiveRoomMessageUserRole(str, Enum):
    REGULAR = 'REGULAR'
    MODERATOR = 'MODERATOR'
    ADMIN = 'ADMIN'
    SUPERADMIN = 'SUPERADMIN'

class LiveRoomTabContentType(str, Enum):
    TEXT = 'text'
    IMAGE = 'image'
    MIXED = 'mixed'
```

-----

#### **4.4. Pydantic Schema 模型设计模式**

  * **`...Base`**: 基础 Schema（包含通用业务字段）
  * **`...Create`**: 创建请求 Schema（**不含** `id`, `created_at`, `updated_at`, 以及从路径参数获取的 `room_id`）
  * **`...Update`**: 更新请求 Schema（所有字段 `Optional`）
  * **`...InDB`**: 数据库完整记录 Schema（包含所有字段，用于 ORM 转换）
  * **`...Response`**: API 响应 Schema（根据 API 规范定制）

#### **4.5. 字段映射规则**

| SQLAlchemy 类型 | Pydantic 类型 | 说明 |
|---|---|---|
| `UUID` | `uuid.UUID` | |
| **`SAEnum(MyEnum)`** | **`MyEnum` (Python Enum)** | **[学院派]** |
| `String(n)` | `str` | 使用 `Field(max_length=n)` |
| `Text` | `str` | |
| `Integer` | `int` | |
| `TIMESTAMP` | `datetime` | |
| `Boolean` | `bool` | |
| `JSONB` | `Optional[Dict[str, Any]]` | |

-----

#### **4.6. LiveRoomTab 相关 Schema 详细要求**

##### **4.6.1. LiveRoomTabBase**

  * **用途**: 包含 Tab 的核心业务字段。
  * **字段**: `tab_key` (max 64), `title` (max 128), **`content_type` (LiveRoomTabContentType)**, `text_content` (Optional), `image_url` (Optional), `sort_order` (default 0, `ge=0`), `is_active` (default True)。

##### **4.6.2. LiveRoomTabCreate**

  * **用途**: `POST /.../tabs` 请求体验证。
  * **继承**: `LiveRoomTabBase`。
  * (不含 `room_id`，因其来自路径)。

##### **4.6.3. LiveRoomTabUpdate**

  * **用途**: `PATCH /.../tabs/{tab_id}` 请求体验证。
  * **继承**: `BaseModel`。
  * **字段**: `tab_key` (Optional, max 64), `title` (Optional, max 128), **`content_type` (Optional[LiveRoomTabContentType])**, `text_content` (Optional), `image_url` (Optional), `sort_order` (Optional, `ge=0`), `is_active` (Optional)。

##### **4.6.4. LiveRoomTabInDB**

  * **用途**: 从 ORM 对象转换。
  * **继承**: `LiveRoomTabBase`。
  * **字段**: `id` (UUID), `room_id` (UUID), `created_at` (datetime), `updated_at` (datetime)。
  * **配置**: `model_config = ConfigDict(from_attributes=True)`。

##### **4.6.5. LiveRoomTabResponse**

  * **用途**: `GET /.../tabs` 响应。
  * **继承**: `LiveRoomTabInDB`。
  * (根据 V3.3 API 规范，响应返回完整模型)。

-----

#### **4.7. LiveRoomMessage 相关 Schema 详细要求**

##### **4.7.1. LiveRoomMessageBase**

  * **用途**: 留言的核心业务字段。
  * **字段**: `content: str = Field(..., min_length=1, max_length=500, description="留言内容")`。
  * **关键**: 必须包含 `min_length` 和 `max_length` 验证。

##### **4.7.2. LiveRoomMessageCreate**

  * **用途**: `POST /.../messages` 请求体验证。
  * **继承**: `LiveRoomMessageBase`。
  * (根据 V3.3 API 规范，请求体只有 `content`)。

##### **4.7.3. LiveRoomMessageUpdate**

  * **用途**: (后台管理用，非 V3.3 API 必须)。
  * **继承**: `BaseModel`。
  * **字段**: `content` (Optional, max 500), `is_deleted` (Optional)。

##### **4.7.4. LiveRoomMessageInDB**

  * **用途**: 从 ORM 对象转换。
  * **继承**: `LiveRoomMessageBase`。
  * **字段**: `id` (UUID), `room_id` (UUID), `session_id` (Optional[UUID]), `user_id` (UUID), **`user_role` (LiveRoomMessageUserRole)**, `created_at` (datetime), `is_deleted` (bool), `extra` (Optional[Dict[str, Any]])。
  * **配置**: `model_config = ConfigDict(from_attributes=True)`。

##### **4.7.5. LiveRoomMessagePostResponse**

  * **用途**: `POST /.../messages` 响应。
  * **继承**: `BaseModel`。
  * **字段**: `id` (UUID), `room_id` (UUID), `user_id` (UUID), **`user_role` (LiveRoomMessageUserRole)**, `content` (str), `created_at` (datetime)。
  * **配置**: `model_config = ConfigDict(from_attributes=True)`。
  * (严格遵循 V3.3 API 3.3.1 响应体)。

##### **4.7.6. LiveRoomMessageListResponseItem**

  * **用途**: `GET /.../messages` 列表中的单项。
  * **继承**: `BaseModel`。
  * **字段**: `id` (UUID), **`user_role` (LiveRoomMessageUserRole)**, `content` (str), `created_at` (datetime)。
  * **配置**: `model_config = ConfigDict(from_attributes=True)`。
  * (严格遵循 V3.3 API 3.3.2 `items` 字段)。

##### **4.7.7. PaginatedLiveRoomMessageResponse**

  * **用途**: `GET /.../messages` 完整响应。
  * **继承**: `BaseModel`。
  * **字段**: `total` (int), `page` (int), `size` (int), `items: List[LiveRoomMessageListResponseItem]`。

-----

#### **4.8. 字段验证要求 (Field Validation Requirements)**

  * **字符串长度**:
      * `LiveRoomMessageBase.content`: `Field(..., min_length=1, max_length=500)`
      * `LiveRoomTabBase.tab_key`: `Field(..., max_length=64)`
      * `LiveRoomTabBase.title`: `Field(..., max_length=128)`
  * **数值范围**:
      * `LiveRoomTabBase.sort_order`: `Field(0, ge=0)`
  * **[学院派] ENUM 验证**:
      * `LiveRoomTabBase.content_type` 必须使用 `LiveRoomTabContentType` ENUM。
      * `LiveRoomMessageInDB.user_role` (及相关 Response) 必须使用 `LiveRoomMessageUserRole` ENUM。
  * **自定义验证器**:
      * **不需要**。V3.3 文档中对 `content` 的 URL 限制是**业务逻辑层**（Service 层）根据 `user_role`（不在 `Create` DTO 中）判断的，**不**属于 Pydantic 验证层。

-----

#### **4.9. 代码组织要求**

```python
"""
直播间 Tab 和留言功能的 Pydantic Schema (学院派 ENUM 版)
"""

# 导入部分
from pydantic import ...
import enum
...

# ==================== 枚举类型定义 ====================
class LiveRoomMessageUserRole(str, enum.Enum):
    ...

class LiveRoomTabContentType(str, enum.Enum):
    ...

# ==================== LiveRoomTab Schema 部分 ====================
# - LiveRoomTabBase
# - LiveRoomTabCreate
# - LiveRoomTabUpdate
# - LiveRoomTabInDB
# - LiveRoomTabResponse

# ==================== LiveRoomMessage Schema 部分 ====================
# - LiveRoomMessageBase
# - LiveRoomMessageCreate
# - LiveRoomMessageUpdate
# - LiveRoomMessageInDB
# - LiveRoomMessagePostResponse
# - LiveRoomMessageListResponseItem
# - PaginatedLiveRoomMessageResponse
```

-----

### **5. 完整性检查清单 (Completeness Checklist)**

生成的代码必须满足以下所有条件：

#### **6.1. 导入语句检查**

  * [ ] 导入了 `BaseModel`, `Field`, `ConfigDict`
  * [ ] 导入了 `Optional`, `List`, `Dict`, `Any`
  * [ ] 导入了 `datetime`, `uuid`
  * [ ] **[学院派]** 导入了 `from enum import Enum`

#### **6.2. [学院派] Enum 类检查**

  * [ ] 定义了 `LiveRoomMessageUserRole` (Python `enum.Enum`)
  * [ ] 定义了 `LiveRoomTabContentType` (Python `enum.Enum`)

#### **6.3. LiveRoomTab Schema 检查**

  * [ ] 定义了 `LiveRoomTabBase` (含 `LiveRoomTabContentType`)
  * [ ] 定义了 `LiveRoomTabCreate` (继承 Base)
  * [ ] 定义了 `LiveRoomTabUpdate` (全 Optional, 含 `LiveRoomTabContentType`)
  * [ ] 定义了 `LiveRoomTabInDB` (含 `id`, `room_id`, `created_at`, `updated_at`, `from_attributes=True`)
  * [ ] 定义了 `LiveRoomTabResponse` (继承 InDB)

#### **6.4. LiveRoomMessage Schema 检查**

  * [ ] 定义了 `LiveRoomMessageBase` (含 `content` 长度验证)
  * [ ] 定义了 `LiveRoomMessageCreate` (继承 Base)
  * [ ] 定义了 `LiveRoomMessageUpdate` (Optional `content`, `is_deleted`)
  * [ ] 定义了 `LiveRoomMessageInDB` (含 `LiveRoomMessageUserRole`, `from_attributes=True`)
  * [ ] 定义了 `LiveRoomMessagePostResponse` (含 `LiveRoomMessageUserRole`, 字段与 API 3.3.1 一致)
  * [ ] 定义了 `LiveRoomMessageListResponseItem` (含 `LiveRoomMessageUserRole`, 字段与 API 3.3.2 items 一致)
  * [ ] 定义了 `PaginatedLiveRoomMessageResponse` (含 `total`, `page`, `size`, `items`)

#### **6.5. 字段验证检查**

  * [ ] `content` 有 `min_length=1, max_length=500`
  * [ ] `tab_key`, `title` 有 `max_length`
  * [ ] `sort_order` 有 `ge=0`
  * [ ] **[学院派]** `content_type` 和 `user_role` 使用了 ENUM 类，不再是 `max_length` 检查。

#### **6.6. 代码质量检查**

  * [ ] 所有 Schema 类包含中文文档字符串
  * [ ] 所有字段包含 `description` 参数
  * [ ] 遵循 PEP 8 代码风格

-----

### **7. 最终交付 (Final Deliverable)**

请根据以上所有要求，为 `live_core_service/app/schemas/live_features.py` 文件生成**完整**、**健壮**、**符合现有项目风格**且**可直接使用**的 Python 代码。

#### **7.1. 交付要求**

1.  **完整性**: 包含所有必需的 Schema 类 (Enum 2个, Tab 5个, Message 7个)
2.  **一致性**: 与 SQLAlchemy 模型 100% 对应（`SAEnum` -\> `enum.Enum`）
3.  **API 规范性**: `Create` 和 `Response` 模型严格遵循 V3.3 API 文档
4.  **文档化**: 每个类和关键字段都有清晰的中文说明

#### **7.2. 参考示例 (Reference Example)**

以下是 `LiveRoomTabBase` 的完整示例，展示了 `ENUM` 和其他所有要求的实现：

```python
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
```
