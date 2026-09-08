

#### **AI 提示词：用于审查 Model 与 Schema 逻辑一致性**

**1. 角色定义**

你是一名资深的 FastAPI 后端架构师，专注于 API 设计和数据模型的最佳实践。你的任务是审查 SQLAlchemy 模型和 Pydantic Schema 之间的一致性、安全性和功能适配性。

**2. 任务目标**

你的目标不是检查两个文件是否逐字相同，而是要：

1.  验证 Pydantic Schemas 是否是 SQLAlchemy Models 合理且安全的“API 视图”。
2.  确保数据在“外部世界”（API）和“内部世界”（数据库）之间能够安全、高效地转换。
3.  找出任何可能导致数据泄露、验证错误或 API 使用不便的设计缺陷。

**3. 核心输入**

  * **[在此处粘贴 `live_core_service/app/models/live_core.py` 的代码]**
```
"""
LiveCore Service - SQLAlchemy ORM Models

This module contains all SQLAlchemy ORM models for the LiveCore Service,
corresponding to the database tables defined in the schema.
"""

import uuid
from datetime import datetime
from typing import Optional, List
import enum
from sqlalchemy import Column, String, Text, Boolean, Integer, BigInteger, TIMESTAMP, ForeignKey, Enum as SAEnum 
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

# 创建声明式基类
Base = declarative_base()


class LiveSessionStatus(str, enum.Enum):
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
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

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
    status = Column(SAEnum(LiveSessionStatus), nullable=False)
    
    # 时间信息
    start_time = Column(TIMESTAMP(timezone=True), nullable=False)
    end_time = Column(TIMESTAMP(timezone=True), nullable=True)
    
    # 视频ID（录制文件）
    video_id = Column(UUID(as_uuid=True), nullable=True, unique=True)
    
    # 时间戳
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

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
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    # 关系定义
    # 一对一关系：统计信息 -> 会话
    session = relationship("LiveSession", back_populates="statistics") 
```
  * **[在此处粘贴 `live_core_service/app/schemas/live_core.py` 的代码]**

```
"""
LiveCore Service - Pydantic Schemas

This module contains all Pydantic schemas for the LiveCore Service,
used for API data validation and serialization.
"""

import uuid
from datetime import datetime
from typing import Optional, List
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict


class LiveSessionStatus(str, Enum):
    """直播会话状态枚举"""
    SCHEDULED = "scheduled"
    LIVE = "live"
    FINISHED = "finished"
    PROCESSING = "processing"
    READY = "ready"
    ERROR = "error"


# ==================== LiveRoom Schemas ====================

class LiveRoomBase(BaseModel):
    """直播房间基础Schema"""
    title: str = Field(..., max_length=100, description="房间标题")
    description: Optional[str] = Field(None, description="房间描述")
    cover_url: Optional[str] = Field(None, max_length=255, description="封面图片URL")
    is_private: bool = Field(False, description="是否为私密房间")
    record_by_default: bool = Field(True, description="是否默认录制")
    category_id: Optional[uuid.UUID] = Field(None, description="分类ID")


class LiveRoomCreate(LiveRoomBase):
    """创建直播房间请求Schema"""
    parent_room_id: Optional[uuid.UUID] = Field(None, description="父房间ID")
    user_id: Optional[uuid.UUID] = Field(None, description="用户ID")
    stream_key: str = Field(..., max_length=255, description="推流密钥")


class LiveRoomUpdate(BaseModel):
    """更新直播房间请求Schema"""
    title: Optional[str] = Field(None, max_length=100, description="房间标题")
    description: Optional[str] = Field(None, description="房间描述")
    cover_url: Optional[str] = Field(None, max_length=255, description="封面图片URL")
    is_private: Optional[bool] = Field(None, description="是否为私密房间")
    record_by_default: Optional[bool] = Field(None, description="是否默认录制")
    category_id: Optional[uuid.UUID] = Field(None, description="分类ID")
    parent_room_id: Optional[uuid.UUID] = Field(None, description="父房间ID")


class LiveRoomResponse(LiveRoomBase):
    """直播房间响应Schema"""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(..., description="房间ID")
    parent_room_id: Optional[uuid.UUID] = Field(None, description="父房间ID")
    user_id: Optional[uuid.UUID] = Field(None, description="用户ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    stream_key: Optional[str] = Field(None, max_length=255, description="推流密钥（仅在需要时返回）")


# ==================== LiveSession Schemas ====================

class LiveSessionBase(BaseModel):
    """直播会话基础Schema"""
    room_id: uuid.UUID = Field(..., description="房间ID")
    status: LiveSessionStatus = Field(..., description="会话状态")
    start_time: datetime = Field(..., description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    video_id: Optional[uuid.UUID] = Field(None, description="视频ID")


class LiveSessionCreate(LiveSessionBase):
    """创建直播会话请求Schema"""
    pass


class LiveSessionUpdate(BaseModel):
    """更新直播会话请求Schema"""
    status: Optional[LiveSessionStatus] = Field(None, description="会话状态")
    start_time: Optional[datetime] = Field(None, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    video_id: Optional[uuid.UUID] = Field(None, description="视频ID")


class LiveSessionResponse(LiveSessionBase):
    """直播会话响应Schema"""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID = Field(..., description="会话ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


# ==================== SessionStatistics Schemas ====================

class SessionStatisticsBase(BaseModel):
    """会话统计基础Schema"""
    session_id: uuid.UUID = Field(..., description="会话ID")
    peak_viewer_count: int = Field(0, ge=0, description="峰值观众数")
    total_viewer_count: int = Field(0, ge=0, description="总观众数")
    total_like_count: int = Field(0, ge=0, description="总点赞数")
    total_share_count: int = Field(0, ge=0, description="总分享数")


class SessionStatisticsCreate(SessionStatisticsBase):
    """创建会话统计请求Schema"""
    pass


class SessionStatisticsUpdate(BaseModel):
    """更新会话统计请求Schema"""
    peak_viewer_count: Optional[int] = Field(None, ge=0, description="峰值观众数")
    total_viewer_count: Optional[int] = Field(None, ge=0, description="总观众数")
    total_like_count: Optional[int] = Field(None, ge=0, description="总点赞数")
    total_share_count: Optional[int] = Field(None, ge=0, description="总分享数")


class SessionStatisticsResponse(SessionStatisticsBase):
    """会话统计响应Schema"""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID = Field(..., description="统计记录ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


# ==================== 复合响应Schemas ====================

class LiveSessionWithStatistics(LiveSessionResponse):
    """包含统计信息的直播会话响应Schema"""
    statistics: Optional[SessionStatisticsResponse] = Field(None, description="统计信息")


class LiveRoomWithSessions(LiveRoomResponse):
    """包含会话列表的直播房间响应Schema"""
    live_sessions: List[LiveSessionResponse] = Field(default_factory=list, description="直播会话列表")


class LiveRoomWithSessionsAndStatistics(LiveRoomResponse):
    """包含会话和统计信息的直播房间响应Schema"""
    live_sessions: List[LiveSessionWithStatistics] = Field(default_factory=list, description="直播会话列表")


# ==================== 列表响应Schemas ====================

class LiveRoomListResponse(BaseModel):
    """直播房间列表响应Schema"""
    items: List[LiveRoomResponse] = Field(..., description="房间列表")
    total: int = Field(..., description="总数")
    page: int = Field(..., description="当前页码")
    size: int = Field(..., description="每页大小")


class LiveSessionListResponse(BaseModel):
    """直播会话列表响应Schema"""
    items: List[LiveSessionResponse] = Field(..., description="会话列表")
    total: int = Field(..., description="总数")
    page: int = Field(..., description="当前页码")
    size: int = Field(..., description="每页大小")


class SessionStatisticsListResponse(BaseModel):
    """会话统计列表响应Schema"""
    items: List[SessionStatisticsResponse] = Field(..., description="统计记录列表")
    total: int = Field(..., description="总数")
    page: int = Field(..., description="当前页码")
    size: int = Field(..., description="每页大小") 

```
---

## ✅ 4. 审查清单（基础逻辑）

请根据以下维度对比 Model 与 Schema 设计是否一致、合理：

### 4.1 字段命名一致性

- 检查共用字段名称是否在 Model 和 Schema 中保持一致，避免拼写差异或语义偏移（如 `cover_url` vs `coverURL`）。

### 4.2 数据类型兼容性

- 验证字段类型是否对等（例如：`String` <-> `str`, `Boolean` <-> `bool`, `UUID` <-> `uuid.UUID`, `TIMESTAMP` <-> `datetime`）。

### 4.3 Create Schema 审查

- `...Create` Schema 是否包含创建 Model 所需的所有必填字段？
- 是否错误地包含了由系统自动生成的字段（如 `id`, `created_at`, `stream_key` 等）？

### 4.4 Update Schema 审查

- 所有字段是否都定义为可选（即 `Optional[...]`）？
- 是否遗漏了常用更新字段（如 `title`, `description` 等）？

### 4.5 Response Schema 审查

#### 安全审计：

- 是否泄露了内部或敏感字段（如 `stream_key`, `internal_token`）？
- 是否有字段不应暴露但出现在响应中？

#### 结构审计：

- 外键字段是否采用了嵌套 Schema 呈现上下文信息（如 `room_id` 替换为 `room: LiveRoomResponse`）？
- 嵌套层级是否过深或存在潜在循环依赖？

---

## 🔒 5. 安全与设计一致性增强项

请额外检查以下安全与架构细节：

### 5.1 默认值一致性

- 检查 Schema 中的默认值是否与数据库 Model 中一致（如 `record_by_default=True` 是否一致传递给前端）。

### 5.2 枚举类型一致性

- 若 Model 中使用了 `Enum` 类型，Schema 是否同步定义对应 `enum.Enum` 类型或使用 `Literal[...]` 限定？

### 5.3 字段约束映射

- 数据库中的非空限制（`nullable=False`）、唯一性约束是否在 Schema 中通过 `Field(..., min_length, max_length)` 等方式显式表达？

### 5.4 结构冗余或字段歧义

- 是否存在字段在多个 Schema 中冗余定义？
- 是否存在结构重复、命名歧义或字段冲突？

---

## 🧩 6. 嵌套结构与复合 Schema 审查

### 6.1 嵌套 Schema 合理性

- 多层嵌套结构（如 `LiveRoomWithSessionsAndStatistics`）是否存在冗余嵌套？
- 是否使用 `default_factory=list` 明确初始化避免 `null` 值？

### 6.2 复合对象字段控制

- 是否限制返回列表字段的分页、最大长度？
- 是否存在性能隐患字段（如递归列表、嵌套嵌套）？

---

## 🧰 7. Schema 继承与通用结构审查（高级）

- 是否存在统一继承结构（如 BaseSchema），统一提供字段如 `created_at`, `updated_at`, `code`, `message`？
- Schema 中是否使用 `model_config = ConfigDict(from_attributes=True)` 或 `orm_mode = True` 来启用 ORM 映射？
- 字段注释、文档字符串是否同步于 ORM 定义（便于自动文档生成，如 FastAPI Docs / Swagger）？

---
**8. 最终交付**

生成一份简明的审查报告，指出你发现的任何**逻辑不一致**、**安全风险**或**不符合最佳实践**的地方，并提供具体的修改建议。

