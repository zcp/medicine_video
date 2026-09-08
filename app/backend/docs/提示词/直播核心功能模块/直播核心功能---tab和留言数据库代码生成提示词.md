
### 1\. 【完整修改版】直播核心功能---tab和留言数据库代码生成提示词

（修改说明：我已将 DDL 规范更新为 `ENUM`，并添加了 Python `enum.Enum` 类的生成要求，使其与您的学院派设计文档 完全一致。）

# 直播间 Tab & 留言功能数据库模型代码生成提示词

## **高效 AI 提示词：生成直播间 Tab & 留言功能的 SQLAlchemy 模型**

### **1. 角色定义 (Role Definition)**

你是一名精通 SQLAlchemy 2.0（异步）和 FastAPI 的资深 Python 后端工程师。你的任务是为 `LiveCore Service` 项目创建直播间 Tab 和留言功能的数据库模型代码，确保与现有代码风格、架构和规范**完全一致**。

**🔥 增量开发模式** (非常重要):

  * 这是一个 **增量开发** 任务，现有代码（`live_core.py`, `topic.py`）已经可以正常运行和测试。
  * **只能新增代码**，不能修改现有文件（除了追加导入）。
  * Base 类已经在 `database.py` 中定义，**不需要也不能修改** `database.py`。

-----

### **2. 任务目标 (Task Objective)**

生成一个名为 `live_features.py` 的 Python 文件，该文件位于项目的 `live_core_service/app/models/` 目录下。这个文件将包含 Tab 和留言功能所需的两个 SQLAlchemy 模型类：

1.  **LiveRoomMessage**: 直播间留言表
2.  **LiveRoomTab**: 直播间 Tab 表

当这些模型被正确导入并注册到 SQLAlchemy 的元数据后，可以通过以下方式创建对应的数据库表：

  * **方式1（推荐）**: 运行 `python app/init_db.py` - 会自动识别 `models/__init__.py` 中导出的所有模型。

-----

### **3. 核心上下文信息 (Core Context Information)**

这是成功生成代码所必需的背景信息：

#### **3.1. 项目文件结构 (Project File Structure)**

你的模型文件必须基于以下项目结构来正确组织代码：

```
live_core_service/
├── app/
│   ├── __init__.py
│   ├── database.py                    # 定义了 Base, AsyncEngine 和 AsyncSession
│   ├── models/
│   │   ├── __init__.py                # 导入所有模型，便于统一管理
│   │   ├── live_core.py               # 现有模型：LiveRoom, LiveSession
│   │   ├── topic.py                   # 现有模型：Topic, TopicCategory
│   │   └── live_features.py           # <-- 这是你要生成的目标文件
│   └── ...
```

**⚠️ 重要提示 - 增量开发原则**:

  * ✅ **可以添加**: 新建 `live_features.py` 文件
  * ✅ **可以追加**: 在 `models/__init__.py` 中添加导入语句
  * ❌ **不要修改**: `database.py` 文件（已有代码依赖它）
  * ❌ **不要修改**: `live_core.py` 或 `topic.py` 文件

#### **3.2. 现有模型文件参考 (Existing Model Reference)**

**文件**: `live_core_service/app/models/live_core.py`

**关键特征**（你必须遵循的风格）:

```python
"""
直播核心功能的数据库模型
"""
import uuid
from datetime import datetime
import enum

# 注意导入顺序和重命名
from sqlalchemy import Column, String, Text, Integer, ForeignKey, Enum as SAEnum, UniqueConstraint, Index, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base  # 注意：Base 在 database.py 中定义，不是 base.py

# ... (枚举类定义) ...

# 模型类定义
class LiveRoom(Base):
    """直播间表"""
    __tablename__ = "live_rooms"
    
    # 核心字段
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True), 
        nullable=False, 
        comment="用户ID，关联到用户服务的public_id（应用层验证）"
    )
    # ... (其他字段) ...
    
    # 时间戳 - 使用 server_default 和 func.now()
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
    # 索引定义（使用 __table_args__ 显式命名）
    __table_args__ = (
        Index("idx_live_rooms_user_id", "user_id"),
    )
    
    # 关联关系
    live_sessions = relationship("LiveSession", back_populates="room", cascade="all, delete-orphan")
```

**关键观察点 (必须遵循)**:

1.  ✅ 使用 `from app.database import Base` (注意：不是 app.models.base)
2.  ✅ TIMESTAMP 从 `sqlalchemy` 导入，UUID 和 JSONB (如果需要) 从 `sqlalchemy.dialects.postgresql` 导入
3.  ✅ Enum 重命名为 SAEnum
4.  ✅ 导入 `func` 用于数据库函数（`func.now()`）
5.  ✅ UUID 字段使用 `UUID(as_uuid=True), primary_key=True, default=uuid.uuid4`
6.  ✅ 时间戳使用 `TIMESTAMP(timezone=True)`，并使用 `server_default=func.now(), onupdate=func.now()`
7.  ✅ 索引使用 `__table_args__` 显式命名（而非 `index=True`）
8.  ✅ 级联删除使用 `cascade="all, delete-orphan"` 或 DDL 中指定的 `ondelete` 属性
9.  ✅ `user_id` 字段必须包含 comment 说明对应 `users.public_id`

#### **3.3. Base 类定义 (database.py)**

**⚠️ 关键信息**: Base 类在 `database.py` 中定义，**不是** `base.py`
**导入方式**: `from app.database import Base`

#### **3.4. 数据库初始化脚本说明 (重要)**

**结论: 必须使用 `init_db.py`**

  * ✅ **增量开发流程**:
    1.  创建 `live_features.py`
    2.  在 `models/__init__.py` 追加导入
    3.  运行 `python app/init_db.py` (自动识别新表)

-----

#### **3.5. 数据库设计规范 (Database Design Specification)**

根据 `《直播核心增量设计文档 - V3.3 (学院派)》` 的要求：

**3.5.1. 用户 ID 与角色约定 (必须遵守)**

  * 所有新增表中的 `user_id` 字段**必须**存储 `users.public_id`（UUID）。
  * **不**使用数据库级 `ForeignKey` 指向 `users` 表，通过应用层（JWT Token）保证引用完整性。
  * `user_id` 字段类型为 `UUID(as_uuid=True)`，并添加 `comment='存储 users.public_id'`。

**【学院派迁移】新增 ENUM 类型**

```sql
-- 迁移：为 live_room_messages.user_role 创建 ENUM 类型
CREATE TYPE live_room_message_user_role AS ENUM (
    'REGULAR',
    'MODERATOR',
    'ADMIN',
    'SUPERADMIN'
);

-- 迁移：为 live_room_tabs.content_type 创建 ENUM 类型
CREATE TYPE live_room_tab_content_type AS ENUM (
    'text',
    'image',
    'mixed'
);
```

**表1: `live_room_messages` (直播间留言表)**

```sql
CREATE TABLE live_room_messages (
    id UUID PRIMARY KEY,
    room_id UUID NOT NULL REFERENCES live_rooms(id) ON DELETE CASCADE,
    session_id UUID NULL REFERENCES live_sessions(id) ON DELETE SET NULL,
    user_id UUID NOT NULL, -- 存储 users.public_id
    user_role live_room_message_user_role NOT NULL, -- [学院派迁移] ENUM 类型
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    extra JSONB NULL
);
-- 索引
CREATE INDEX idx_live_room_messages_room_created ON live_room_messages(room_id, created_at);
CREATE INDEX idx_live_room_messages_session_created ON live_room_messages(session_id, created_at);
```

**表2: `live_room_tabs` (直播间 Tab 表)**

```sql
CREATE TABLE live_room_tabs (
    id UUID PRIMARY KEY,
    room_id UUID NOT NULL REFERENCES live_rooms(id) ON DELETE CASCADE,
    tab_key VARCHAR(64) NOT NULL,
    title VARCHAR(128) NOT NULL,
    content_type live_room_tab_content_type NOT NULL, -- [学院派迁移] ENUM 类型
    text_content TEXT NULL,
    image_url TEXT NULL,
    sort_order INT NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
-- 索引
CREATE INDEX idx_live_room_tabs_room_sort ON live_room_tabs(room_id, sort_order);
```

-----

### **4. 代码生成具体要求 (Specific Code Generation Requirements)**

#### **4.1. 文件名与位置**

  * `live_core_service/app/models/live_features.py`

#### **4.2. 导入语句 (Imports)**

必须包含以下导入（顺序和分组与现有代码一致）:

```python
"""
直播间 Tab 和留言功能的数据库模型
"""
import uuid
from datetime import datetime
import enum

# SQLAlchemy 核心导入
from sqlalchemy import Column, String, Text, Integer, ForeignKey, Enum as SAEnum, UniqueConstraint, Index, TIMESTAMP, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB  # 确保导入 JSONB 和 Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base  # 注意：Base 在 database.py 中
```

#### **4.3. 枚举类型定义**

**[学院派迁移]**：本次增量设计**包含**新的数据库 Enum 类型。**必须**定义 Python `enum.Enum` 类，并使用 `SAEnum` 将其映射到 SQLAlchemy。

```python
# (接在 Imports 之后)

# ==================== 枚举类型定义 ====================
# 对应 DDL: CREATE TYPE live_room_message_user_role
class LiveRoomMessageUserRole(str, enum.Enum):
    REGULAR = 'REGULAR'
    MODERATOR = 'MODERATOR'
    ADMIN = 'ADMIN'
    SUPERADMIN = 'SUPERADMIN'


# 对应 DDL: CREATE TYPE live_room_tab_content_type
class LiveRoomTabContentType(str, enum.Enum):
    TEXT = 'text'
    IMAGE = 'image'
    MIXED = 'mixed'

# ==================== 模型类定义 ====================
```

#### **4.4. 模型类定义**

**4.4.1. LiveRoomMessage 模型类**

  * **表名**: `__tablename__ = "live_room_messages"`
  * **字段定义**:
      * 严格遵循 Section 3.5 的 DDL。
      * `id`: `Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)`
      * `room_id`: `Column(UUID(as_uuid=True), ForeignKey("live_rooms.id", ondelete="CASCADE"), nullable=False)`
      * `session_id`: `Column(UUID(as_uuid=True), ForeignKey("live_sessions.id", ondelete="SET NULL"), nullable=True)`
      * `user_id`: `Column(UUID(as_uuid=True), nullable=False, comment='存储 users.public_id')` (必须有 comment)
      * **[学院派迁移]** `user_role`: `Column(SAEnum(LiveRoomMessageUserRole, name='live_room_message_user_role', create_type=False), nullable=False, comment='用户角色快照')`
      * `content`: `Column(Text, nullable=False)`
      * `is_deleted`: `Column(Boolean, nullable=False, default=False)`
      * `extra`: `Column(JSONB, nullable=True)`
      * `created_at`: `Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())`
      * (注意: 此表没有 `updated_at`)
  * **索引**:
      * 使用 `__table_args__` 显式命名索引
      * `Index('idx_live_room_messages_room_created', 'room_id', 'created_at')`
      * `Index('idx_live_room_messages_session_created', 'session_id', 'created_at')`
  * **关联关系 (单向)**:
      * `room = relationship("LiveRoom")`
      * `session = relationship("LiveSession")`
      * (注意: 为保持增量开发原则，不修改 `live_core.py`，因此这里使用单向关联，不使用 `back_populates`)
  * **repr 方法**: 返回 `<LiveRoomMessage(id={self.id}, user_id={self.user_id})>`

**4.4.2. LiveRoomTab 模型类**

  * **表名**: `__tablename__ = "live_room_tabs"`
  * **字段定义**: 严格遵循 Section 3.5 的 DDL。
      * `id`: `Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)`
      * `room_id`: `Column(UUID(as_uuid=True), ForeignKey("live_rooms.id", ondelete="CASCADE"), nullable=False)`
      * `tab_key`: `Column(String(64), nullable=False, comment='系统级 key，用于逻辑识别')`
      * `title`: `Column(String(128), nullable=False, comment='展示名称')`
      * **[学院派迁移]** `content_type`: `Column(SAEnum(LiveRoomTabContentType, name='live_room_tab_content_type', create_type=False), nullable=False, comment="'text' | 'image' | 'mixed'")`
      * `text_content`: `Column(Text, nullable=True)`
      * `image_url`: `Column(Text, nullable=True)`
      * `sort_order`: `Column(Integer, nullable=False, default=0)`
      * `is_active`: `Column(Boolean, nullable=False, default=True)`
      * `created_at`: `Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())`
      * `updated_at`: `Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())`
  * **索引**:
      * `__table_args__ = (Index('idx_live_room_tabs_room_sort', 'room_id', 'sort_order'), )`
  * **关联关系 (单向)**:
      * `room = relationship("LiveRoom")`
  * **repr 方法**: 返回 `<LiveRoomTab(id={self.id}, title={self.title}, room_id={self.room_id})>`

#### **4.5. 索引创建**

  * **⚠️ 重要**: 所有索引必须使用 `__table_args__` 显式命名，**不要使用** `index=True`。
  * **索引命名规范**: `idx_{表名}_{字段名}` (与 DDL 一致)。

#### **4.6. 注释与文档**

1.  **模块文档字符串**: "直播间 Tab 和留言功能的数据库模型"
2.  **类文档字符串**: 每个模型类添加中文描述
3.  **字段注释**: 关键字段（如 `user_id`, `tab_key`）必须添加行内 `comment`
4.  **中文说明**: 所有文档字符串和注释使用中文

-----

### **5. 完整性检查清单 (Completeness Checklist)**

生成的代码必须满足以下所有条件：

**文件结构**:

  * [ ] 包含模块文档字符串
  * [ ] 导入语句完整且顺序正确（包含 `JSONB`, `Boolean`, `enum`）
  * [ ] 从 `app.database` 导入 `Base`

**[学院派] Enum 类**:

  * [ ] 包含 `LiveRoomMessageUserRole` (Python `enum.Enum`)
  * [ ] 包含 `LiveRoomTabContentType` (Python `enum.Enum`)

**LiveRoomMessage 模型**:

  * [ ] 表名为 "live\_room\_messages"
  * [ ] 包含所有 9 个字段
  * [ ] **[学院派]** `user_role` 字段使用 `SAEnum(LiveRoomMessageUserRole, ...)`
  * [ ] `user_id` 字段有 `comment`
  * [ ] `room_id` 和 `session_id` 的 `ForeignKey` 定义正确（`ondelete` 属性）
  * [ ] `created_at` 使用 `server_default=func.now()` 且**没有** `onupdate`
  * [ ] `__table_args__` 包含 2 个索引
  * [ ] 包含 2 个单向 `relationship`
  * [ ] 包含 `__repr__` 方法

**LiveRoomTab 模型**:

  * [ ] 表名为 "live\_room\_tabs"
  * [ ] 包含所有 11 个字段
  * [ ] **[学院派]** `content_type` 字段使用 `SAEnum(LiveRoomTabContentType, ...)`
  * [ ] `room_id` 的 `ForeignKey` 定义正确 (`ondelete="CASCADE"`)
  * [ ] `sort_order` 和 `is_active` 有正确的 `default`
  * [ ] `created_at` 和 `updated_at` 配置正确
  * [ ] `__table_args__` 包含 1 个索引
  * [ ] 包含 1 个单向 `relationship`
  * [ ] 包含 `__repr__` 方法

**代码质量**:

  * [ ] 关键字段有中文 `comment`
  * [ ] 遵循 PEP 8 代码风格

-----

### **6. 最终交付 (Final Deliverable)**

请根据以上所有要求，为 `live_core_service/app/models/live_features.py` 文件生成**完整**、**健壮**、**符合现有项目风格**且**可直接使用**的 Python 代码。

**重要提示**:

1.  生成的代码应该可以直接复制到 `app/models/live_features.py` 文件中
2.  **必须同时修改** `app/models/__init__.py`，在现有导入后**追加**：

<!-- end list -->

```python
# ... (现有的 live_core 和 topic 导入) ...

# 新增导入（追加在末尾）
from .live_features import LiveRoomMessage, LiveRoomTab
```

3.  创建数据库表的方式：
      * **方式1（推荐）**: 运行 `python app/init_db.py`
          * ✅ **优点**: 会自动通过 `import app.models` 识别所有导出的模型
          * ✅ **优点**: 只需修改 `models/__init__.py`，完全符合增量开发原则

-----
