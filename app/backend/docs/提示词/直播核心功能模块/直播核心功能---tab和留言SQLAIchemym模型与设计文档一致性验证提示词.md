### 2\. 【完整修改版】直播核心功能---tab和留言SQLAIchemym模型与设计文档一致性验证提示词

（修改说明：我已将 DDL 规范、待审查的 SQLAlchemy 示例代码、以及所有的审查清单（4.2, 4.4, 4.11）全部更新为使用 `ENUM` 类型，使其与您的学院派设计文档 完全一致。）

## **高效 AI 代码审计提示词：验证 `live_features.py` 与 V3.3 (学院派) 设计文档的一致性**

-----

### **1. 角色定义 (Role Definition)**

你是一名资深的 Python 后端技术审计员和 SQLAlchemy 2.0 专家。你的核心任务是进行严格的代码审查，确保下文中提供的 Tab 和留言功能 SQLAlchemy ORM 模型代码 (`live_features.py`) **百分之百**地、**严格地**遵循了给定的**学院派**数据库设计规范 (DDL)。

你必须以**挑剔和精确**的态度找出任何细微的偏差，包括但不限于：

  * 字段名称不一致
  * **数据类型不匹配（特别是 `ENUM`, `TIMESTAMP` 和 `Boolean`/`JSONB`）**
  * 默认值设置错误
  * 索引定义缺失或错误
  * 外键约束（`ondelete` 规则）不正确
  * `user_id` 字段的特殊约束（无外键）

-----

### **2. 任务目标 (Task Objective)**

你的目标是：

1.  **比较**下面提供的【数据库设计规范 (DDL)】和【待审查的 SQLAlchemy 模型代码】
2.  **验证**代码是否完全实现了 DDL 中定义的所有表、字段、类型、约束和索引
3.  **生成**一份详细的审查报告，明确指出所有一致、不一致或缺失的实现，并提供修正建议

-----

### **3. 核心输入 (Core Inputs)**

#### **3.1. 权威的数据库设计规范 (Authoritative Database Schema - DDL)**

这是唯一的设计标准，所有代码实现都必须与此对齐。

**来源**: `《直播核心增量设计文档 - V3.3 (学院派)》`

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

```sql
-- 表 1: live_room_messages (直播间留言表)
CREATE TABLE live_room_messages (
    id UUID PRIMARY KEY,
    room_id UUID NOT NULL
        REFERENCES live_rooms(id)
        ON DELETE CASCADE,

    -- 可选：关联具体场次
    session_id UUID NULL
        REFERENCES live_sessions(id)
        ON DELETE SET NULL,

    -- 存储的是 users.public_id
    user_id UUID NOT NULL,

    -- [学院派迁移] 用户角色快照 (ENUM)
    user_role live_room_message_user_role NOT NULL,

    content TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- 软删除标记
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,

    -- 预留扩展字段
    extra JSONB NULL
);

-- 索引
CREATE INDEX idx_live_room_messages_room_created
    ON live_room_messages(room_id, created_at);

CREATE INDEX idx_live_room_messages_session_created
    ON live_room_messages(session_id, created_at);


-- 表 2: live_room_tabs (直播间 Tab 表)
CREATE TABLE live_room_tabs (
    id UUID PRIMARY KEY,
    room_id UUID NOT NULL
        REFERENCES live_rooms(id)
        ON DELETE CASCADE,

    -- 系统级 key
    tab_key VARCHAR(64) NOT NULL,
    -- 展示名称
    title VARCHAR(128) NOT NULL,
    
    -- [学院派迁移] 内容类型 (ENUM)
    content_type live_room_tab_content_type NOT NULL,
    
    text_content TEXT NULL,
    image_url TEXT NULL,

    -- Tab 排序
    sort_order INT NOT NULL DEFAULT 0,
    -- Tab 是否对前端可见
    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 索引
CREATE INDEX idx_live_room_tabs_room_sort
    ON live_room_tabs(room_id, sort_order);
```

-----

#### **3.2. 待审查的 SQLAlchemy 模型代码**

**文件**: `backend/live_core_service/app/models/live_features.py`

*请在此处提供 `live_features.py` 文件的完整内容*

**[学院派迁移]：以下是 *符合* 学院派 ENUM 规范的 *正确示例* 代码。请用此标准审查。**

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

class LiveRoomMessage(Base):
    """直播间留言表"""
    __tablename__ = "live_room_messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    room_id = Column(UUID(as_uuid=True), ForeignKey("live_rooms.id", ondelete="CASCADE"), nullable=False)
    session_id = Column(UUID(as_uuid=True), ForeignKey("live_sessions.id", ondelete="SET NULL"), nullable=True)
    
    # 存储 users.public_id，无数据库外键
    user_id = Column(UUID(as_uuid=True), nullable=False, comment='存储 users.public_id')
    # [学院派迁移] 使用 SAEnum 映射
    user_role = Column(SAEnum(LiveRoomMessageUserRole, name='live_room_message_user_role', create_type=False), nullable=False, comment='用户角色快照')
    
    content = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    is_deleted = Column(Boolean, nullable=False, default=False)
    extra = Column(JSONB, nullable=True)
    
    # 索引定义
    __table_args__ = (
        Index('idx_live_room_messages_room_created', 'room_id', 'created_at'),
        Index('idx_live_room_messages_session_created', 'session_id', 'created_at'),
    )
    
    # 关联关系 (单向)
    room = relationship("LiveRoom")
    session = relationship("LiveSession")
    
    def __repr__(self):
        return f"<LiveRoomMessage(id={self.id}, user_id={self.user_id})>"


class LiveRoomTab(Base):
    """直播间 Tab 表"""
    __tablename__ = "live_room_tabs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    room_id = Column(UUID(as_uuid=True), ForeignKey("live_rooms.id", ondelete="CASCADE"), nullable=False)
    
    tab_key = Column(String(64), nullable=False, comment='系统级 key，用于逻辑识别')
    title = Column(String(128), nullable=False, comment='展示名称')
    # [学院派迁移] 使用 SAEnum 映射
    content_type = Column(SAEnum(LiveRoomTabContentType, name='live_room_tab_content_type', create_type=False), nullable=False, comment="'text' | 'image' | 'mixed'")
    text_content = Column(Text, nullable=True)
    image_url = Column(Text, nullable=True)
    
    sort_order = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)
    
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
    # 索引定义
    __table_args__ = (
        Index('idx_live_room_tabs_room_sort', 'room_id', 'sort_order'),
    )
    
    # 关联关系 (单向)
    room = relationship("LiveRoom")
    
    def __repr__(self):
        return f"<LiveRoomTab(id={self.id}, title={self.title}, room_id={self.room_id})>"

```

-----

### **4. 审查清单与验证规则 (Audit Checklist & Validation Rules)**

请根据以下清单逐项进行严格审查：

#### **4.1. 表与模型映射 (Table-to-Model Mapping)**

  * [ ] `live_room_messages`, `live_room_tabs` 两个表是否都已正确映射为 SQLAlchemy 模型类？
  * [ ] 每个模型类的 `__tablename__` 是否与 DDL 表名完全对应？
  * [ ] 模型类命名是否符合 Python 规范（大驼峰命名法）？
      * `live_room_messages` → `LiveRoomMessage`
      * `live_room_tabs` → `LiveRoomTab`

-----

#### **4.2. 枚举类型定义 (Enum Type Definition)**

  * [ ] **[学院派检查]** DDL V3.3 **定义了** `CREATE TYPE` 枚举。代码中是否包含对应的 Python `enum.Enum` 类（`LiveRoomMessageUserRole`, `LiveRoomTabContentType`）？

-----

#### **4.3. 字段与列的完全对应 (Field-to-Column Correspondence)**

##### **4.3.1. LiveRoomMessage 模型字段检查**

| DDL 列名 | 是否存在 | 字段命名正确 | 备注 |
|---|---|---|---|
| `id` | [ ] | [ ] | 主键 UUID |
| `room_id` | [ ] | [ ] | 外键到 live\_rooms |
| `session_id` | [ ] | [ ] | 外键到 live\_sessions |
| `user_id` | [ ] | [ ] | 用户ID，无外键 |
| `user_role` | [ ] | [ ] | 角色快照 (ENUM) |
| `content` | [ ] | [ ] | 留言内容 |
| `created_at` | [ ] | [ ] | 创建时间 |
| `is_deleted` | [ ] | [ ] | 软删除标记 |
| `extra` | [ ] | [ ] | 扩展字段 |

##### **4.3.2. LiveRoomTab 模型字段检查**

| DDL 列名 | 是否存在 | 字段命名正确 | 备注 |
|---|---|---|---|
| `id` | [ ] | [ ] | 主键 UUID |
| `room_id` | [ ] | [ ] | 外键到 live\_rooms |
| `tab_key` | [ ] | [ ] | Tab Key |
| `title` | [ ] | [ ] | Tab 标题 |
| `content_type` | [ ] | [ ] | 内容类型 (ENUM) |
| `text_content` | [ ] | [ ] | 文本内容 |
| `image_url` | [ ] | [ ] | 图片 URL |
| `sort_order` | [ ] | [ ] | 排序 |
| `is_active` | [ ] | [ ] | 激活状态 |
| `created_at` | [ ] | [ ] | 创建时间 |
| `updated_at` | [ ] | [ ] | 更新时间 |

-----

#### **4.4. 数据类型精确性 (Data Type Accuracy)**

##### **4.4.1. UUID 类型检查**

  * [ ] 是否从 `sqlalchemy.dialects.postgresql` 导入 `UUID`？
  * [ ] 所有 UUID 字段是否使用 `UUID(as_uuid=True)`？
  * [ ] 主键 `id` 是否包含 `default=uuid.uuid4`？
  * [ ] 是否导入了 `import uuid`？

##### **4.4.2. 字符串类型检查**

| 字段 | DDL 类型 | 应映射为 | 是否正确 |
|---|---|---|---|
| `live_room_messages.content` | `TEXT` | `Text` | [ ] |
| `live_room_tabs.tab_key` | `VARCHAR(64)` | `String(64)` | [ ] |
| `live_room_tabs.title` | `VARCHAR(128)` | `String(128)` | [ ] |
| `live_room_tabs.text_content` | `TEXT` | `Text` | [ ] |
| `live_room_tabs.image_url` | `TEXT` | `Text` | [ ] |

##### **4.4.3. [学院派] ENUM 类型检查 (关键)**

  * [ ] 是否导入了 `import enum` 和 `from sqlalchemy import Enum as SAEnum`？
  * [ ] `user_role` 字段是否使用 `SAEnum(LiveRoomMessageUserRole, ...)`？
  * [ ] `content_type` 字段是否使用 `SAEnum(LiveRoomTabContentType, ...)`？
  * [ ] `SAEnum` 是否包含 `name='...'` 和 `create_type=False` 参数？

##### **4.4.4. 数值类型检查**

| 字段 | DDL 类型 | 应映射为 | 是否正确 |
|---|---|---|---|
| `live_room_tabs.sort_order` | `INT` | `Integer` | [ ] |

##### **4.4.5. 布尔与 JSON 类型检查**

  * [ ] `is_deleted` 和 `is_active` 字段是否使用 `Boolean`？
  * [ ] `extra` 字段是否使用 `JSONB`？
  * [ ] 是否从 `sqlalchemy` 导入 `Boolean`？
  * [ ] 是否从 `sqlalchemy.dialects.postgresql` 导入 `JSONB`？

##### **4.4.6. 时间戳类型检查 (关键)**

  * [ ] 是否从 `sqlalchemy` 导入 `TIMESTAMP`？
  * [ ] 是否从 `sqlalchemy.sql` 导入 `func`？
  * [ ] 所有时间戳字段是否使用 `TIMESTAMP(timezone=True)`？
  * [ ] `created_at` 字段是否使用 `server_default=func.now()`？
  * [ ] `live_room_tabs.updated_at` 是否使用 `server_default=func.now(), onupdate=func.now()`？
  * [ ] ⚠️ `live_room_messages.created_at` 是否**没有** `onupdate=func.now()`（DDL 中未定义）？
  * [ ] ⚠️ **严禁使用** `default=datetime.utcnow`。

**正确示例**:

```python
from sqlalchemy import TIMESTAMP, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
is_deleted = Column(Boolean, nullable=False, default=False)
extra = Column(JSONB, nullable=True)
```

-----

#### **4.5. 主键定义 (Primary Keys)**

  * [ ] 所有 `id` 字段是否标记为 `primary_key=True`？
  * [ ] 所有 `id` 字段是否包含 `default=uuid.uuid4`？

-----

#### **4.6. 外键与级联规则 (Foreign Keys & Cascade Rules)**

##### **4.6.1. live\_room\_messages.room\_id**

  * [ ] 是否定义了 `ForeignKey("live_rooms.id", ondelete="CASCADE")`？
  * [ ] `ondelete` 是否正确设置为 `"CASCADE"`（大写）？

##### **4.6.2. live\_room\_messages.session\_id**

  * [ ] 是否定义了 `ForeignKey("live_sessions.id", ondelete="SET NULL")`？
  * [ ] `ondelete` 是否正确设置为 `"SET NULL"`？

##### **4.6.3. live\_room\_tabs.room\_id**

  * [ ] 是否定义了 `ForeignKey("live_rooms.id", ondelete="CASCADE")`？
  * [ ] `ondelete` 是否正确设置为 `"CASCADE"`？

##### **4.6.4. live\_room\_messages.user\_id (特殊情况)**

  * [ ] `user_id` 字段是否**没有**定义 `ForeignKey`？
  * [ ] 是否在 `comment` 中说明"存储 users.public\_id"？

-----

#### **4.7. 约束和默认值 (Constraints and Defaults)**

##### **4.7.1. NOT NULL 约束**

检查以下字段是否正确设置 `nullable=False`：
**LiveRoomMessage**: `id`, `room_id`, `user_id`, `user_role`, `content`, `created_at`, `is_deleted` (共 7 个)
**LiveRoomTab**: `id`, `room_id`, `tab_key`, `title`, `content_type`, `sort_order`, `is_active`, `created_at`, `updated_at` (共 9 个)

##### **4.7.2. NULL 约束**

检查以下字段是否正确设置 `nullable=True`（或默认）：
**LiveRoomMessage**: `session_id`, `extra`
**LiveRoomTab**: `text_content`, `image_url`

##### **4.7.3. 默认值 (Defaults)**

| 字段 | DDL 默认值 | 应设置为 | 是否正确 |
|---|---|---|---|
| `live_room_messages.is_deleted` | `FALSE` | `default=False` | [ ] |
| `live_room_tabs.sort_order` | `0` | `default=0` | [ ] |
| `live_room_tabs.is_active` | `TRUE` | `default=True` | [ ] |
| 所有 `created_at` | `CURRENT_TIMESTAMP` | `server_default=func.now()` | [ ] |
| `live_room_tabs.updated_at` | `NOW()` | `server_default=func.now(), onupdate=func.now()` | [ ] |

-----

#### **4.8. 唯一约束 (Unique Constraints)**

  * [ ] **(V3.3 检查)** `live_room_messages` 和 `live_room_tabs` 在 DDL 中均未定义 `UniqueConstraint`。代码中不应包含。

-----

#### **4.9. 索引定义 (Index Definitions)**

**⚠️ 关键要求**: 所有索引必须使用 `__table_args__` 显式命名，**不能使用** `index=True`。

##### **4.9.1. LiveRoomMessage 模型索引**

  * [ ] 是否定义了 `Index('idx_live_room_messages_room_created', 'room_id', 'created_at')`？
  * [ ] 是否定义了 `Index('idx_live_room_messages_session_created', 'session_id', 'created_at')`？
  * [ ] 组合索引的字段顺序是否正确？

##### **4.9.2. LiveRoomTab 模型索引**

  * [ ] 是否定义了组合索引 `Index('idx_live_room_tabs_room_sort', 'room_id', 'sort_order')`？
  * [ ] 组合索引的字段顺序是否正确？

##### **4.9.3. 索引定义位置**

  * [ ] 所有索引是否都在 `__table_args__` 中定义？
  * [ ] 是否从 `sqlalchemy` 导入了 `Index`？

-----

#### **4.10. 关系完整性 (Relationship Integrity)**

##### **4.10.1. 单向关系检查 (V3.3 增量规则)**

  * [ ] **(V3.3 检查)** 为保持增量开发（不修改 `live_core.py`），`live_features.py` 中的关系应为单向（无 `back_populates`）。
  * [ ] `LiveRoomMessage` 中是否定义了 `room = relationship("LiveRoom")`？
  * [ ] `LiveRoomMessage` 中是否定义了 `session = relationship("LiveSession")`？
  * [ ] `LiveRoomTab` 中是否定义了 `room = relationship("LiveRoom")`？

-----

#### **4.11. 导入语句检查 (Import Statements)**

  * [ ] 是否导入了 `import uuid`?
  * [ ] 是否导入了 `import enum`?
  * [ ] 是否导入了 `from sqlalchemy import ..., Boolean, Enum as SAEnum`?
  * [ ] 是否导入了 `from sqlalchemy.dialects.postgresql import UUID, JSONB`?
  * [ ] 是否导入了 `from app.database import Base`?

-----

#### **4.12. 代码风格与文档 (Code Style & Documentation)**

  * [ ] 每个模型类是否包含文档字符串？
  * [ ] 关键字段是否包含中文 `comment` 参数（`user_id`, `user_role`, `tab_key`, `title`, `content_type`）？
  * [ ] 是否遵循 PEP 8 代码风格？
  * [ ] 是否包含 `__repr__` 方法？

-----

### **5. 最终交付 (Final Deliverable)**

请生成一份 **Markdown 格式**的详细审查报告，包含以下部分：

#### **5.1. 总体结论 (Overall Conclusion)**

一句话总结代码与设计规范的符合程度。

#### **5.2. 符合性评分 (Compliance Score)**

(可选项，参考模板)

#### **5.3. 详细审查结果表 (Detailed Audit Results)**

| 审查项 | 审查结果 | 问题描述 | 修正建议 |
|---|---|---|---|
| 表映射: live\_room\_messages | ✅ 通过 / ❌ 失败 | | |
| **[学院派] ENUM 定义** | ✅ 通过 / ❌ 失败 | | |
| **[学院派] 字段: user\_role (SAEnum)** | ✅ 通过 / ❌ 失败 | | |
| 字段: user\_id (特殊) | ✅ 通过 / ❌ 失败 | | |
| 数据类型: TIMESTAMPTZ | ✅ 通过 / ❌ 失败 | | |
| 外键: session\_id | ✅ 通过 / ❌ 失败 | | |
| 索引: idx\_live\_room\_tabs\_room\_sort | ✅ 通过 / ❌ 失败 | | |
| ... | ... | ... | ... |

#### **5.4. 关键问题清单 (Critical Issues)**

列出所有 ❌ 失败的检查项。

-----

### **6. 审查标准 (Audit Standards)**

#### **6.1. 严格标准 (Strict Standards)**

以下项目必须100%符合DDL规范，任何偏差都算作**失败**：

  * 表名、字段名
  * **数据类型（`ENUM`, `TIMESTAMP`, `Boolean`, `JSONB`）**
  * 外键约束和级联规则（`CASCADE`, `SET NULL`）
  * `NOT NULL` / `NULL` 约束
  * `user_id` 无外键的特殊规则

#### **6.2. 宽松标准 (Flexible Standards)**

  * 索引名称（只要能清晰表达含义即可）
  * `__repr__` 方法（可选）

#### **6.3. 推荐实践 (Best Practices)**

  * 添加 `__repr__` 方法
  * 添加详细的中文 `comment`

-----

### **7. 审查重点**

特别关注以下容易出错的地方：

1.  ⚠️ **[学院派] `ENUM` 映射** - 必须使用 Python `enum` + `SAEnum(...)`。
2.  ⚠️ **时间戳字段** - 必须使用 `TIMESTAMP` + `server_default=func.now()`。
3.  ⚠️ **`messages.created_at`** 必须**没有** `onupdate`。
4.  ⚠️ **索引定义** - 必须使用 `__table_args__` 显式命名。
5.  ⚠️ **`user_id`** - 必须**没有** `ForeignKey`。
6.  ⚠️ **`ondelete` 规则** - `CASCADE` vs `SET NULL` 必须正确。
7.  ⚠️ **`Boolean` 和 `JSONB`** - 必须正确导入和使用。

-----

### **8. 验证完成标准 (Completion Criteria)**

审查报告完成后，必须明确回答以下问题：

1.  ✅ / ❌ 所有表是否正确映射？
2.  ✅ / ❌ 所有字段是否完整对应？
3.  ✅ / ❌ 所有数据类型是否精确匹配？
4.  ✅ / ❌ 所有索引是否正确定义？
5.  ✅ / ❌ 所有外键和级联规则是否正确？
6.  ✅ / ❌ 所有约束和默认值是否正确？
7.  ✅ / ❌ 所有关系是否按（单向）要求定义？

**只有当以上7个问题全部回答"✅"时，才认为模型代码与设计文档完全一致。**

-----