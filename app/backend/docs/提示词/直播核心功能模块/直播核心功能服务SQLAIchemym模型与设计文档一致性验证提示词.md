好的，我完全理解你的需求。你已经有了一个用于**生成代码**的强大提示词，现在你需要一个用于**验证代码**的提示词。

这个新的提示词将扮演“代码审查员”或“技术审计员”的角色，其唯一目标是**严格比对**已生成的 `models/live_core.py` 文件和原始的 DDL 设计规范，找出任何不一致或不符合要求的地方。

这是一种非常高效和严谨的 AI 协作模式：一个 AI 生成，另一个 AI 验证。

-----

### **高效 AI 代码审计提示词 (针对 `live_core.py` 的一致性审查)**

#### **1. 角色定义 (Role Definition)**

你是一名资深的 Python 后端技术审计员和 SQLAlchemy 专家。你的核心任务是进行代码审查，以确保下文中提供的 SQLAlchemy ORM 模型代码**百分之百**地、**严格地**遵循了给定的数据库设计规范 (DDL)。你必须以挑剔和精确的态度找出任何细微的偏差。

#### **2. 任务目标 (Task Objective)**

你的目标是：

1.  **比较**下面提供的【数据库设计规范 (DDL)】和【待审查的 SQLAlchemy 模型代码】。
2.  **验证**代码是否完全实现了 DDL 中定义的所有表、字段、类型、约束和关系。
3.  **生成**一份详细的审查报告，明确指出所有一致、不一致或缺失的实现，并提供修正建议。

#### **3. 核心输入 (Core Inputs)**

**3.1. 权威的数据库设计规范 (Authoritative Database Schema - DDL)**
这是唯一的设计标准，所有代码实现都必须与此对齐。

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

**3.2. 待审查的 SQLAlchemy 模型代码 (`live_core.py`)**
*在这里粘贴你由 AI 生成的 `live_core.py` 的完整代码。*

```python
"""
LiveCore Service - SQLAlchemy ORM Models

This module contains all SQLAlchemy ORM models for the LiveCore Service,
corresponding to the database tables defined in the schema.
"""

import uuid
from datetime import datetime
from typing import Optional, List

from sqlalchemy import Column, String, Text, Boolean, Integer, BigInteger, DateTime, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

# 创建声明式基类
Base = declarative_base()


class LiveSessionStatus(str, Enum):
    """直播会话状态枚举"""
    SCHEDULED = "scheduled"
    LIVE = "live"
    FINISHED = "finished"
    PROCESSING = "processing"
    READY = "ready"
    ERROR = "error"


class LiveRoom(Base):
    """
    直播房间模型 - 对应 live_rooms 表
    持久化容器，存储直播房间的基本信息
    """
    __tablename__ = "live_rooms"

    # 主键 - UUID类型，应用层生成
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # 外键 - 父房间ID，自引用关系
    parent_room_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("live_rooms.id", ondelete="SET NULL"), 
        nullable=True
    )
    
    # 用户ID
    user_id = Column(UUID(as_uuid=True), nullable=True)
    
    # 基本信息
    title = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    cover_url = Column(String(255), nullable=True)
    stream_key = Column(String(255), nullable=False, unique=True)
    
    # 设置选项
    is_private = Column(Boolean, default=False)
    record_by_default = Column(Boolean, default=True)
    
    # 分类ID
    category_id = Column(UUID(as_uuid=True), nullable=True)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.current_timestamp())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.current_timestamp(), onupdate=func.current_timestamp())

    # 关系定义
    # 自引用关系：父房间 -> 子房间
    parent_room = relationship("LiveRoom", remote_side=[id], back_populates="child_rooms")
    child_rooms = relationship("LiveRoom", back_populates="parent_room")
    
    # 一对多关系：房间 -> 直播会话
    live_sessions = relationship("LiveSession", back_populates="room", cascade="all, delete-orphan")


class LiveSession(Base):
    """
    直播会话模型 - 对应 live_sessions 表
    瞬时事件，记录每次直播会话的信息
    """
    __tablename__ = "live_sessions"

    # 主键 - UUID类型，应用层生成
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # 外键 - 房间ID
    room_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("live_rooms.id", ondelete="CASCADE"), 
        nullable=False
    )
    
    # 会话状态
    status = Column(Enum(LiveSessionStatus), nullable=False)
    
    # 时间信息
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=True)
    
    # 视频ID（录制文件）
    video_id = Column(UUID(as_uuid=True), nullable=True, unique=True)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.current_timestamp())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.current_timestamp(), onupdate=func.current_timestamp())

    # 关系定义
    # 多对一关系：会话 -> 房间
    room = relationship("LiveRoom", back_populates="live_sessions")
    
    # 一对一关系：会话 -> 统计信息
    statistics = relationship("SessionStatistics", back_populates="session", uselist=False, cascade="all, delete-orphan")


class SessionStatistics(Base):
    """
    会话统计模型 - 对应 session_statistics 表
    存储直播会话的统计数据
    """
    __tablename__ = "session_statistics"

    # 主键 - UUID类型，应用层生成
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # 外键 - 会话ID，一对一关系
    session_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("live_sessions.id", ondelete="CASCADE"), 
        nullable=False, 
        unique=True
    )
    
    # 统计数据
    peak_viewer_count = Column(Integer, default=0)
    total_viewer_count = Column(BigInteger, default=0)
    total_like_count = Column(BigInteger, default=0)
    total_share_count = Column(BigInteger, default=0)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.current_timestamp())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.current_timestamp(), onupdate=func.current_timestamp())

    # 关系定义
    # 一对一关系：统计信息 -> 会话
    session = relationship("LiveSession", back_populates="statistics") 
```

#### **4. 审查清单与验证规则 (Audit Checklist & Validation Rules)**

请根据以下清单逐项进行严格审查：

1.  **表与模型映射 (Table-to-Model Mapping):**

      * `live_rooms`, `live_sessions`, `session_statistics` 三个表是否都已正确映射为 SQLAlchemy 模型类？
      * 每个模型类的 `__tablename__` 是否与 DDL 表名完全对应？

2.  **字段与列的完全对应 (Field-to-Column Correspondence):**

      * 每个模型中的字段是否与 DDL 中对应表的列一一对应，不多不少？
      * 字段命名是否符合 Python 风格（例如 `stream_key`）？

3.  **数据类型精确性 (Data Type Accuracy):**

      * `UUID`: 是否使用了 `from sqlalchemy.dialects.postgresql import UUID` 并定义为 `Column(UUID(as_uuid=True), ...)`？
      * `VARCHAR(n)`: 是否映射为 `String(n)`？ (例如 `String(100)`, `String(255)`)
      * `TEXT`: 是否映射为 `Text`？
      * `TIMESTAMPTZ`: 是否映射为 `TIMESTAMP(timezone=True)`？
      * `BOOLEAN`: 是否映射为 `Boolean`？
      * `INT`: 是否映射为 `Integer`？
      * `BIGINT`: 是否映射为 `BigInteger`？
      * `live_session_status` (ENUM): 是否创建了一个 Python `enum.Enum` 类，并将其用于 `sqlalchemy.Enum` 中？

4.  **主键 (Primary Keys):**

      * `id` 字段是否被正确定义为 `primary_key=True`？
      * `id` 字段是否包含 `default=uuid.uuid4`？（需要 `import uuid`）

5.  **外键与级联规则 (Foreign Keys & Cascade Rules):**

      * `live_sessions.room_id`: `ForeignKey` 是否正确指向 `live_rooms.id`？`ondelete` 是否设置为 `'CASCADE'`？
      * `session_statistics.session_id`: `ForeignKey` 是否正确指向 `live_sessions.id`？`ondelete` 是否设置为 `'CASCADE'`？
      * `live_rooms.parent_room_id`: `ForeignKey` 是否正确指向 `live_rooms.id`？`ondelete` 是否设置为 `'SET NULL'`？

6.  **关系完整性 (Relationship Integrity):**

      * 所有外键是否都定义了对应的 `relationship()`？
      * 是否使用了 `back_populates` 来确保所有关系都是双向的？
          * `live_rooms` \<-\> `live_sessions`
          * `live_sessions` \<-\> `session_statistics`
          * `live_rooms` \<-\> `live_rooms` (自引用关系)

7.  **约束和默认值 (Constraints and Defaults):**

      * `NOT NULL`: 是否正确转换为 `nullable=False`？
      * `NULL`: 是否正确转换为 `nullable=True`（或保持默认）？
      * `UNIQUE`: 是否为 `stream_key`, `video_id`, 和 `session_id` 设置了 `unique=True`？
      * `DEFAULT ...`: 是否正确设置了 `default` 或 `server_default`？
          * `DEFAULT CURRENT_TIMESTAMP` 应该使用 `server_default=func.now()`。
          * `DEFAULT false`/`true`/`0` 应该使用 `server_default='false'`/`'true'`/`'0'` 或 `default=...`。

#### **5. 最终交付 (Final Deliverable)**

请生成一份 Markdown 格式的审查报告。报告应包含以下部分：

1.  **总体结论 (Overall Conclusion):**

      * 一句话总结代码与设计规范的符合程度（例如：“完全一致”、“基本一致，但存在小问题”、“存在严重偏差”）。

2.  **详细分析报告 (Detailed Analysis Report):**

      * 使用表格形式，逐项列出【第 4 部分】中的所有审查规则。
      * 表格应包含三列：`审查项`、`审查结果 (通过/失败)`、`备注与修改建议`。
      * 如果审查结果为“失败”，必须在备注中清晰地解释问题所在，并**提供修正后的正确代码片段**。

**示例报告格式:**

| 审查项 | 审查结果 | 备注与修改建议 |
| :--- | :--- | :--- |
| **表与模型映射** | 通过 | `live_rooms`, `live_sessions`, `session_statistics` 均已正确映射。 |
| **数据类型: `TIMESTAMPTZ`** | \<span style="color:red;"\>失败\</span\> | `live_rooms.created_at` 被错误地定义为 `DateTime`，缺少时区信息。应使用 `TIMESTAMP(timezone=True)`。\<br\>**修正建议:**\<br\>`python<br>created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())<br>` |
| **...** | ... | ... |  