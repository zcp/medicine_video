
-----

### **高效 AI 代码生成提示词 (针对 LiveCore Service)**

#### **1. 角色定义 (Role Definition)**

你是一名精通 FastAPI 和异步 SQLAlchemy 的资深 Python 后端工程师。你的任务是根据我提供的数据库设计规范，为 `LiveCore Service` 生成结构清晰、类型精确且符合最佳实践的 SQLAlchemy ORM 模型和 Pydantic Schema。

#### **2. 任务目标 (Task Objective)**

你的目标是生成以下两个 Python 文件的完整代码：

1.  `live_core_service/app/models/live_core.py`: 包含所有与数据库表对应的 SQLAlchemy 模型。
2.  `live_core_service/app/schemas/live_core.py`: 包含所有用于 API 数据交互的 Pydantic 模型。

#### **3. 核心上下文信息 (Core Context Information)**

**3.1. 技术栈 (Technology Stack)**

  * **框架**: FastAPI
  * **ORM**: SQLAlchemy (异步模式, 使用 `AsyncSession`)
  * **数据库**: PostgreSQL
  * **数据模型**: Pydantic
  * **Python 版本**: 3.8+

**3.2. 数据库 Schema (Database Schema - DDL)**
这是项目最终的数据库表结构定义，请严格根据它来创建 SQLAlchemy 模型：

```sql
-- LiveCore Service - 完整数据库 Schema (V3.2)

CREATE TYPE live_session_status AS ENUM (
    'scheduled', 'live', 'finished', 'processing', 'ready', 'error'
);

-- 表 1: live_rooms (持久化容器)
CREATE TABLE live_rooms (
    id UUID PRIMARY KEY,
    parent_room_id UUID NULL REFERENCES live_rooms(id) ON DELETE SET NULL,
    user_id UUID NULL,
    title VARCHAR(100) NOT NULL,
    description TEXT,
    cover_url VARCHAR(255),
    stream_key VARCHAR(255) NOT NULL UNIQUE,
    is_private BOOLEAN DEFAULT false,
    record_by_default BOOLEAN DEFAULT true,
    category_id UUID NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 表 2: live_sessions (瞬时事件)
CREATE TABLE live_sessions (
    id UUID PRIMARY KEY,
    room_id UUID NOT NULL REFERENCES live_rooms(id) ON DELETE CASCADE,
    status live_session_status NOT NULL,
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ,
    video_id UUID NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 表 3: session_statistics (场次统计)
CREATE TABLE session_statistics (
    id UUID PRIMARY KEY,
    session_id UUID NOT NULL UNIQUE REFERENCES live_sessions(id) ON DELETE CASCADE,
    peak_viewer_count INT DEFAULT 0,
    total_viewer_count BIGINT DEFAULT 0,
    total_like_count BIGINT DEFAULT 0,
    total_share_count BIGINT DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

#### **4. 期望的项目文件结构 (新增部分)
请将生成的代码放入以下结构中：
```
live_core_service/
├── app/
│   ├── __init__.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── live_core.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── live_core.py
│   └── ...
│
└── ...
```
-----

#### **5. 代码生成具体要求 (Specific Code Generation Requirements)**
**5.1 代码风格必须严格遵循 PEP 8 规范
**5.2. SQLAlchemy 模型 (`live_core_service/app/models/live_core.py`)**

  * 必须使用 SQLAlchemy 的声明式基类 (`declarative_base`)。
  * 所有 `UUID` 类型的主键和外键，必须使用 `from sqlalchemy.dialects.postgresql import UUID`，并在 `Column` 中定义为 `UUID(as_uuid=True)` 以确保类型正确。
  * 所有主键 `id` 字段必须在应用层生成，模型定义应为 `id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)`。请确保导入 `uuid` 库。
  * 必须精确定义所有表之间的 `relationship()`，并使用 `back_populates` 来建立双向关系。
  * 外键的 `ondelete` 行为必须与 DDL 中的定义（如 `ON DELETE CASCADE`）保持一致。
  * 为每个模型类添加注释，说明它对应哪个数据库表。

**5.3. Pydantic 模型 (`live_core_service/app/schemas/live_core.py`)**

  * 为每个 SQLAlchemy 模型创建一组对应的 Pydantic Schema，至少包含：
      * **`...Base`**: 包含通用的、可被继承的字段。
      * **`...Create`**: 用于 API 创建资源时接收的请求体。
      * **`...Update`**: 用于 API 更新资源时接收的请求体，所有字段应为可选（`Optional`）。
      * **`...Response`**: 用于 API 返回给客户端的响应数据。
  * 所有用于从数据库对象转换的 Schema，必须配置 `from_attributes=True` (对于 Pydantic v2) 或 `orm_mode = True` (对于 Pydantic v1)。
  * 所有 `UUID` 字段的类型应为 `uuid.UUID`，所有 `TIMESTAMPTZ` 字段的类型应为 `datetime.datetime`。

#### **6. 最终交付 (Final Deliverable)**

请根据以上所有要求，为我生成以下两个文件的完整 Python 代码。请将每个文件的代码放在独立的、有明确标记的代码块中。

1.  **`live_core_service/app/models/live_core.py`**
2.  **`live_core_serivce/app/schemas/live_core.py`**

-----
