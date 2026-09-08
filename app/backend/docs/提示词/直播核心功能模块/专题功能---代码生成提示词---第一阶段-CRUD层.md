# 专题功能代码生成提示词 - 第一阶段（CRUD层）

## 1. 角色定义 (Role Definition)

你是一名资深的 Python 后端工程师，精通 FastAPI 和异步 SQLAlchemy，并擅长根据详细的设计文档和代码上下文，编写出精确、健壮且符合规范的代码。你特别擅长处理复杂的多表关联查询和事务管理。

## 2. 任务目标 (Task Objective)

你的任务是为**专题聚合功能 (Topics)**生成第一阶段的代码，包括：

1. **数据访问层 (CRUD Layer)**：创建 `app/crud/topic.py` 文件，封装所有与 `Topic`、`TopicCategory`、`TopicCategoryRoom` 模型相关的数据库操作。

在此阶段，CRUD层**只负责数据访问**，不包含任何业务逻辑验证（如权限检查），这些将在Service层实现。

## 3. 核心上下文信息 (Core Context Information)

### 3.1. 项目结构

你将要生成以下文件，请严格按照此路径：

```
backend/live_core_service/
├── app/
│   ├── crud/
│   │   └── topic.py              # <-- 目标文件（本阶段）
│   ├── services/
│   │   └── topic_service.py      # <-- 第二阶段生成
│   ├── api/v1/endpoints/
│   │   └── topic.py              # <-- 第二阶段生成
│   ├── models/
│   │   ├── live_core.py          # <-- 已存在（包含LiveRoom、LiveSession等）
│   │   └── topic.py              # <-- 已存在（包含Topic、TopicCategory、TopicCategoryRoom）
│   ├── schemas/
│   │   └── topic.py              # <-- 已存在
│   ├── exceptions.py             # <-- 已存在（第二阶段会追加专题相关异常）
│   └── database.py               # <-- 已存在
```

### 3.2. 已存在的代码全文

**重要提示**：以下代码是你必须严格依据的基础，所有字段名、类型、关系都必须与之完全一致。

#### `app/models/live_core.py` (专题相关模型节选)

```python
"""
LiveCore Service - SQLAlchemy ORM Models

This module contains all SQLAlchemy ORM models for the LiveCore Service,
corresponding to the database tables defined in the schema.
"""

import uuid
from datetime import datetime
from typing import Optional, List
import enum
from sqlalchemy import Column, String, Text, Boolean, Integer, BigInteger, TIMESTAMP, ForeignKey, Enum as SAEnum, Index  # 关键：将SQLAlchemy的Enum重命名，以避免和Python内置的enum冲突
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

# 从数据库配置导入Base
from app.database import Base


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
    user_id = Column(
        UUID(as_uuid=True), 
        nullable=False, 
        comment="用户ID，关联到用户服务的public_id（应用层验证）"
    )
    
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

    # 索引定义
    __table_args__ = (
        Index("idx_live_rooms_user_id", "user_id"),
    )

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
    status = Column(SAEnum(LiveSessionStatus, values_callable=lambda obj: [e.value for e in obj]), nullable=False)
    
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

#### `app/models/topic.py`
```python
"""
专题聚合功能的数据库模型

本模块包含专题聚合功能所需的三个 SQLAlchemy 模型类：
- Topic: 专题表（顶层实体）
- TopicCategory: 专题内分类表（中层实体）
- TopicCategoryRoom: 专题分类与直播间的关联表（关系层）
"""
import uuid
from datetime import datetime
import enum

# SQLAlchemy 核心导入
from sqlalchemy import Column, String, Text, Integer, ForeignKey, Enum as SAEnum, UniqueConstraint, Index, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


# ==================== 枚举类型定义 ====================

class TopicStatus(str, enum.Enum):
    """专题状态枚举"""
    DRAFT = "draft"          # 草稿
    PUBLISHED = "published"  # 已发布
    ARCHIVED = "archived"    # 已归档


# ==================== 模型类定义 ====================

class Topic(Base):
    """
    专题活动表
    
    用于聚合多个分类和直播间，实现类似聚合页面的功能。
    一个专题可以包含多个分类，每个分类下可以关联多个直播间。
    """
    __tablename__ = "topics"
    
    # 核心标识 (在应用层通过 uuid.uuid4() 生成)
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # 用户ID，对应 users 表的 public_id（通过JWT Token应用层验证保证引用完整性）
    # 注意：不使用 ForeignKey，因为 User 服务可能独立部署
    user_id = Column(
        UUID(as_uuid=True), 
        nullable=False, 
        comment='创建者用户ID，对应 users.public_id'
    )
    
    # 业务字段
    title = Column(String(100), nullable=False, comment='专题标题')
    description = Column(Text, nullable=True, comment='专题描述')
    banner_url = Column(String(255), nullable=True, comment='横幅图URL')
    
    # 专题状态
    status = Column(
        SAEnum(TopicStatus, values_callable=lambda obj: [e.value for e in obj]), 
        nullable=False, 
        default=TopicStatus.DRAFT,
        comment='专题状态: draft(草稿), published(已发布), archived(已归档)'
    )
    
    # 时间戳 - 使用 server_default 和 func.now()
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
    # 索引定义
    __table_args__ = (
        Index('idx_topics_user_id', 'user_id'),
        Index('idx_topics_status', 'status'),
        Index('idx_topics_created_at', 'created_at'),
    )
    
    # 关联关系
    categories = relationship(
        "TopicCategory", 
        back_populates="topic", 
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    
    def __repr__(self):
        return f"<Topic(id={self.id}, title={self.title})>"


class TopicCategory(Base):
    """
    专题内分类表
    
    专题下的分类，如按省份、按科室等。
    一个专题可以包含多个分类，每个分类可以关联多个直播间。
    """
    __tablename__ = "topic_categories"
    
    # 核心标识 (在应用层通过 uuid.uuid4() 生成)
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # 外键 - 关联到专题
    topic_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("topics.id", ondelete="CASCADE"), 
        nullable=False,
        comment='所属专题ID'
    )
    
    # 业务字段
    name = Column(String(50), nullable=False, comment='分类名称')
    sort_order = Column(Integer, default=0, nullable=False, comment='排序顺序，数值越小越靠前')
    
    # 时间戳 - 使用 server_default 和 func.now()
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
    # 索引和约束定义
    __table_args__ = (
        Index('idx_topic_categories_topic_id', 'topic_id'),
        Index('idx_topic_categories_topic_sort', 'topic_id', 'sort_order'),
        UniqueConstraint('topic_id', 'name', name='uq_topic_category_name'),
    )
    
    # 关联关系
    topic = relationship("Topic", back_populates="categories")
    rooms = relationship(
        "TopicCategoryRoom", 
        back_populates="category", 
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    
    def __repr__(self):
        return f"<TopicCategory(id={self.id}, name={self.name}, sort_order={self.sort_order})>"


class TopicCategoryRoom(Base):
    """
    专题分类与直播间的关联表
    
    用于定义专题分类与直播间的多对多关联关系。
    同一个直播间可以被添加到多个不同的专题分类中。
    """
    __tablename__ = "topic_category_rooms"
    
    # 核心标识 (在应用层通过 uuid.uuid4() 生成)
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # 外键 - 关联到分类
    category_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("topic_categories.id", ondelete="CASCADE"), 
        nullable=False,
        comment='所属分类ID'
    )
    
    # 外键 - 关联到直播间
    room_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("live_rooms.id", ondelete="CASCADE"), 
        nullable=False,
        comment='关联的直播间ID'
    )
    
    # 业务字段
    sort_order = Column(Integer, default=0, nullable=False, comment='在分类下的排序顺序，数值越小越靠前')
    
    # 时间戳 - 使用 server_default 和 func.now()
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
    # 索引和约束定义
    __table_args__ = (
        Index('idx_tcr_category_id', 'category_id'),
        Index('idx_tcr_room_id', 'room_id'),
        Index('idx_tcr_category_sort', 'category_id', 'sort_order'),
        UniqueConstraint('category_id', 'room_id', name='uq_category_room'),
    )
    
    # 关联关系
    category = relationship("TopicCategory", back_populates="rooms")
    room = relationship("LiveRoom")
    
    def __repr__(self):
        return f"<TopicCategoryRoom(category_id={self.category_id}, room_id={self.room_id}, sort_order={self.sort_order})>"
```

#### `app/schemas/topic.py` (已存在)

```python
"""
专题聚合功能的 Pydantic Schema

本模块包含专题聚合功能所需的所有 Pydantic 模型：
- Topic 相关 Schema
- TopicCategory 相关 Schema
- TopicCategoryRoom 相关 Schema
- 聚合响应 Schema
"""

# 标准库导入
from datetime import datetime
from enum import Enum
from typing import List, Optional
import uuid

# 第三方库导入
from pydantic import BaseModel, Field, ConfigDict, field_validator


# ==================== 枚举定义部分 ====================

class TopicStatus(str, Enum):
    """专题状态枚举"""
    DRAFT = "draft"          # 草稿
    PUBLISHED = "published"  # 已发布
    ARCHIVED = "archived"    # 已归档


# ==================== Topic Schema 部分 ====================

class TopicBase(BaseModel):
    """
    专题基础 Schema
    
    包含专题的核心业务字段，用于创建和更新操作的基类。
    """
    title: str = Field(
        ..., 
        min_length=1, 
        max_length=100, 
        description="专题标题，必填，长度 1-100 字符"
    )
    description: Optional[str] = Field(
        None, 
        description="专题描述，可选，支持 Markdown 格式"
    )
    banner_url: Optional[str] = Field(
        None, 
        max_length=255, 
        description="横幅图 URL，可选，最大 255 字符"
    )
    status: TopicStatus = Field(
        default=TopicStatus.DRAFT, 
        description="专题状态，默认为草稿"
    )


class TopicCreate(TopicBase):
    """
    创建专题请求 Schema
    
    用于 POST /api/v1/topics 接口的请求体。
    user_id 从 JWT Token 中提取，不在请求体中。
    """
    pass  # 继承 TopicBase 的所有字段


class TopicUpdate(BaseModel):
    """
    更新专题请求 Schema
    
    用于 PATCH /api/v1/topics/{topic_id} 接口的请求体。
    所有字段都是可选的，允许部分更新（PATCH 语义）。
    """
    title: Optional[str] = Field(
        None, 
        min_length=1, 
        max_length=100,
        description="专题标题"
    )
    description: Optional[str] = Field(
        None,
        description="专题描述"
    )
    banner_url: Optional[str] = Field(
        None, 
        max_length=255,
        description="横幅图 URL"
    )
    status: Optional[TopicStatus] = Field(
        None,
        description="专题状态"
    )


class TopicInDB(TopicBase):
    """
    数据库中的专题 Schema
    
    包含所有数据库字段，包括系统生成的 id 和时间戳。
    支持从 SQLAlchemy ORM 对象转换。
    """
    id: uuid.UUID = Field(..., description="专题唯一标识")
    user_id: uuid.UUID = Field(..., description="创建者用户ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    model_config = ConfigDict(from_attributes=True)


class TopicResponse(TopicInDB):
    """
    专题响应 Schema
    
    用于 API 响应，返回专题的完整信息。
    继承 TopicInDB 的所有字段。
    """
    pass


# ==================== TopicCategory Schema 部分 ====================

class CategoryBase(BaseModel):
    """
    分类基础 Schema
    
    包含分类的核心业务字段。
    """
    name: str = Field(
        ..., 
        min_length=1, 
        max_length=50, 
        description="分类名称，必填，长度 1-50 字符"
    )
    sort_order: int = Field(
        default=0, 
        ge=0, 
        description="排序顺序，默认 0，数值越小越靠前"
    )


class CategoryCreate(CategoryBase):
    """
    创建分类请求 Schema
    
    用于 POST /api/v1/topics/{topic_id}/categories 接口的请求体。
    topic_id 从路径参数获取，不在请求体中。
    """
    pass


class CategoryUpdate(BaseModel):
    """
    更新分类请求 Schema
    
    用于 PATCH /api/v1/topic-categories/{category_id} 接口的请求体。
    所有字段都是可选的，允许部分更新。
    """
    name: Optional[str] = Field(
        None, 
        min_length=1, 
        max_length=50,
        description="分类名称"
    )
    sort_order: Optional[int] = Field(
        None, 
        ge=0,
        description="排序顺序"
    )


class CategoryInDB(CategoryBase):
    """
    数据库中的分类 Schema
    
    包含所有数据库字段，包括外键和时间戳。
    支持从 SQLAlchemy ORM 对象转换。
    """
    id: uuid.UUID = Field(..., description="分类唯一标识")
    topic_id: uuid.UUID = Field(..., description="所属专题ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    model_config = ConfigDict(from_attributes=True)


class CategoryResponse(CategoryInDB):
    """
    分类响应 Schema
    
    用于 API 响应，返回分类的完整信息。
    """
    pass


# ==================== TopicCategoryRoom 关联管理 Schema 部分 ====================

class RoomAssociation(BaseModel):
    """
    单个直播间关联 Schema
    
    用于批量添加直播间到分类时的单个直播间数据结构。
    """
    room_id: uuid.UUID = Field(..., description="直播间唯一标识")
    sort_order: int = Field(
        default=0, 
        ge=0, 
        description="在分类下的排序顺序，默认 0"
    )


class AddRoomsRequest(BaseModel):
    """
    添加直播间到分类请求 Schema
    
    用于 POST /api/v1/topic-categories/{category_id}/rooms 接口的请求体。
    支持批量添加 1-50 个直播间，自动验证 room_id 唯一性。
    """
    rooms: List[RoomAssociation] = Field(
        ..., 
        min_length=1, 
        max_length=50, 
        description="要添加的直播间列表，最少 1 个，最多 50 个"
    )
    
    @field_validator('rooms')
    @classmethod
    def validate_unique_room_ids(cls, v):
        """
        验证 room_id 唯一性
        
        确保同一个请求中的 room_id 不重复。
        """
        room_ids = [r.room_id for r in v]
        if len(room_ids) != len(set(room_ids)):
            raise ValueError("room_id 不能重复")
        return v


class UpdateRoomSortRequest(BaseModel):
    """
    更新直播间排序请求 Schema
    
    用于 PATCH /api/v1/topic-categories/{category_id}/rooms/sort 接口的请求体。
    支持批量更新 1-100 个直播间的排序顺序。
    """
    rooms: List[RoomAssociation] = Field(
        ..., 
        min_length=1, 
        max_length=100,
        description="要更新排序的直播间列表"
    )


class RemoveRoomsRequest(BaseModel):
    """
    移除直播间请求 Schema
    
    用于 DELETE /api/v1/topic-categories/{category_id}/rooms 接口的请求体。
    支持批量移除 1-50 个直播间。
    """
    room_ids: List[uuid.UUID] = Field(
        ..., 
        min_length=1, 
        max_length=50, 
        description="要移除的直播间ID列表，最少 1 个，最多 50 个"
    )


# ==================== 聚合响应 Schema 部分 ====================

class RoomInCategory(BaseModel):
    """
    分类下的直播间 Schema（用于聚合页面）
    
    用于专题详情页的直播间展示，包含直播状态和热度信息。
    """
    id: uuid.UUID = Field(..., description="直播间唯一标识")
    title: str = Field(..., description="直播间标题")
    cover_url: Optional[str] = Field(None, description="直播间封面图 URL")
    live_status: str = Field(
        ..., 
        description='直播状态: "scheduled"(预约), "live"(直播中), "finished"(已结束)'
    )
    start_time: Optional[datetime] = Field(None, description="最新场次开始时间")
    heat: int = Field(
        default=0, 
        ge=0, 
        description="热度值，根据观看、点赞等数据计算"
    )
    
    model_config = ConfigDict(from_attributes=True)


class CategoryWithRooms(BaseModel):
    """
    包含直播间列表的分类 Schema
    
    用于专题详情页的分类展示，包含该分类下的所有直播间。
    """
    id: uuid.UUID = Field(..., description="分类唯一标识")
    name: str = Field(..., description="分类名称")
    sort_order: int = Field(..., description="分类排序顺序")
    rooms: List[RoomInCategory] = Field(
        default_factory=list,
        description="该分类下的直播间列表"
    )
    
    model_config = ConfigDict(from_attributes=True)


class TopicDetailResponse(TopicInDB):
    """
    专题详情响应 Schema（包含层级化数据）
    
    用于 GET /api/v1/topics/{topic_id} 接口的响应。
    返回完整的层级化数据结构：专题 → 分类 → 直播间。
    """
    categories: List[CategoryWithRooms] = Field(
        default_factory=list,
        description="专题下的所有分类及其直播间"
    )


# ==================== 辅助 Schema 部分 ====================

class BatchStatusRequest(BaseModel):
    """
    批量查询状态请求 Schema
    
    用于批量查询多个直播间的状态信息。
    """
    room_ids: List[uuid.UUID] = Field(
        ..., 
        min_length=1, 
        max_length=100,
        description="要查询的直播间ID列表，最少 1 个，最多 100 个"
    )


class RoomStatusResponse(BaseModel):
    """
    直播间状态响应 Schema
    
    用于返回单个直播间的实时状态信息。
    """
    room_id: uuid.UUID = Field(..., description="直播间唯一标识")
    live_status: str = Field(
        ..., 
        description='直播状态: "scheduled", "live", "finished"'
    )
    current_session_id: Optional[uuid.UUID] = Field(
        None, 
        description="当前场次ID，如果没有进行中的场次则为 null"
    )
    viewer_count: int = Field(
        default=0, 
        ge=0, 
        description="当前观看人数，仅在直播中时有效"
    )


```

## 4. 通用规范与核心原则 (General Specifications & Core Principles)

### 4.1. 权威设计文档

**所有实现细节必须严格遵循**：
- 📖 **主文档**：`docs/03_系统设计/专题功能完整设计文档-修正版.md`
- 📖 **核心规范**：`docs/03_系统设计/直播核心功能设计文档v3.md`

### 4.2. 代码规范

- **开发语言**：Python 3.8+
- **代码风格**：严格遵循 PEP 8
- **格式化**：4个空格缩进，UTF-8编码
- **命名规范**：
  - 类名：大驼峰 (PascalCase)，例如 `TopicService`
  - 函数/方法：下划线 (snake_case)，例如 `create_topic`
  - 变量：下划线 (snake_case)，例如 `topic_id`
  - 常量：全大写下划线 (UPPER_SNAKE_CASE)，例如 `MAX_TITLE_LENGTH`

### 4.3. 🛡️ 核心编码原则 - 安全异步异常处理

**关键规则**：在任何 `try...except` 块中，如果需要使用来自数据库 ORM 对象的属性进行日志记录或错误处理，这些属性**必须在进入 `try` 块之前**被提取并存储到局部变量中。

**严禁行为**：在捕获了数据库相关异常（如 `IntegrityError`、`DBAPIError`）的 `except` 块中直接访问可能已与失效会话关联的 ORM 对象的属性。

**示例（正确做法）**：
```python
# ✅ 正确：提前提取变量
topic_id_for_logging = topic.id
user_id_for_logging = topic.user_id

try:
    await db.commit()
except IntegrityError as e:
    await db.rollback()
    # ✅ 使用局部变量
    logger.error(f"数据库完整性错误: topic_id={topic_id_for_logging}, error={str(e)}")
    raise
```

**示例（错误做法）**：
```python
# ❌ 错误：在except块中直接访问ORM对象
try:
    await db.commit()
except IntegrityError as e:
    await db.rollback()
    # ❌ 危险！topic对象可能已失效
    logger.error(f"错误: topic_id={topic.id}")  # 可能抛出DetachedInstanceError
```

### 4.4. 异步编程规范

```python
# 所有数据库操作必须使用 async/await
async def create_topic(db: AsyncSession, obj_in: TopicCreate, user_id: uuid.UUID):
    topic = Topic(
        id=uuid.uuid4(),  # 应用层生成UUID
        user_id=user_id,
        **obj_in.dict()
    )
    db.add(topic)
    await db.commit()      # 异步提交
    await db.refresh(topic)  # 异步刷新
    return topic
```

### 4.5. 事务处理规范

```python
# 使用try-except-finally确保事务一致性
async def complex_operation(db: AsyncSession):
    # 提前提取需要的变量
    resource_id_for_logging = None
    
    try:
        # 业务操作
        topic = await create_topic(...)
        resource_id_for_logging = topic.id  # ✅ 提取用于日志
        category = await create_category(...)
        await db.commit()
    except Exception as e:
        await db.rollback()
        # ✅ 使用局部变量记录日志
        logger.error(f"操作失败: resource_id={resource_id_for_logging}, error={str(e)}")
        raise
    finally:
        # 清理资源（如果需要）
        pass
```

## 5. 具体代码生成指令 - CRUD Layer

### 5.1. `app/crud/topic.py` 职责与要求

**职责**：封装所有与 `Topic`、`TopicCategory`、`TopicCategoryRoom` 模型相关的数据库操作，提供纯粹的数据访问接口。

**要求**：
- 所有函数均为 `async def`，并接收 `db: AsyncSession`
- **不包含**任何业务逻辑验证（如权限检查、状态检查）
- 使用 `selectinload`、`joinedload` 等方法避免 N+1 查询
- 遵循安全异步异常处理原则

### 5.2. 需实现的函数清单

#### **专题 (Topic) 相关操作**

1. **`create(db: AsyncSession, obj_in: TopicCreate, user_id: UUID) -> Topic`**
   - 功能：创建新专题
   - 实现要点：
     - 应用层生成UUID：`id=uuid.uuid4()`
     - 关联 `user_id`
     - 提交后刷新对象

2. **`get(db: AsyncSession, topic_id: UUID) -> Optional[Topic]`**
   - 功能：根据ID获取单个专题
   - 返回：Topic对象或None

3. **`get_with_categories(db: AsyncSession, topic_id: UUID) -> Optional[Topic]`**
   - 功能：获取专题及其所有分类（预加载）
   - 实现要点：
     ```python
     select(Topic).options(
         selectinload(Topic.categories)
     ).where(Topic.id == topic_id)
     ```

4. **`get_multi_and_total(db: AsyncSession, skip: int, limit: int, status: Optional[TopicStatus] = None, user_id: Optional[UUID] = None) -> Tuple[List[Topic], int]`**
   - 功能：分页获取专题列表，支持筛选
   - 返回：(专题列表, 总数)
   - 实现要点：
     - 先执行 `count()` 查询获取总数
     - 应用筛选条件（status、user_id）
     - 按 `created_at DESC` 排序

5. **`update(db: AsyncSession, db_obj: Topic, obj_in: TopicUpdate) -> Topic`**
   - 功能：更新专题信息
   - 实现要点：
     ```python
     update_data = obj_in.model_dump(exclude_unset=True)
     for field, value in update_data.items():
         setattr(db_obj, field, value)
     await db.commit()
     await db.refresh(db_obj)
     ```

6. **`remove(db: AsyncSession, db_obj: Topic) -> Topic`**
   - 功能：删除专题（级联删除分类和关联）
   - 实现要点：
     ```python
     # 提前提取用于日志的变量
     topic_id_for_logging = db_obj.id
     
     try:
         await db.delete(db_obj)
         await db.commit()
     except Exception as e:
         await db.rollback()
         logger.error(f"删除失败: topic_id={topic_id_for_logging}, error={str(e)}")
         raise
     ```

#### **分类 (TopicCategory) 相关操作**

7. **`create_category(db: AsyncSession, obj_in: CategoryCreate, topic_id: UUID) -> TopicCategory`**
   - 功能：创建新分类
   - 实现要点：关联 `topic_id`

8. **`get_category(db: AsyncSession, category_id: UUID) -> Optional[TopicCategory]`**
   - 功能：根据ID获取单个分类

9. **`get_category_with_topic(db: AsyncSession, category_id: UUID) -> Optional[TopicCategory]`**
   - 功能：获取分类及其关联的专题（用于权限验证）
   - 实现要点：
     ```python
     select(TopicCategory).options(
         selectinload(TopicCategory.topic)
     ).where(TopicCategory.id == category_id)
     ```

10. **`get_categories_by_topic(db: AsyncSession, topic_id: UUID, skip: int, limit: int) -> Tuple[List[TopicCategory], int]`**
    - 功能：分页获取专题下的所有分类
    - 排序：按 `sort_order ASC`

11. **`update_category(db: AsyncSession, db_obj: TopicCategory, obj_in: CategoryUpdate) -> TopicCategory`**
    - 功能：更新分类信息

12. **`remove_category(db: AsyncSession, db_obj: TopicCategory) -> TopicCategory`**
    - 功能：删除分类（级联删除关联）

#### **直播间关联 (TopicCategoryRoom) 相关操作**

13. **`add_room_to_category(db: AsyncSession, category_id: UUID, room_id: UUID, sort_order: int) -> TopicCategoryRoom`**
    - 功能：将直播间添加到分类
    - 实现要点：
      - 应用层生成UUID
      - 使用 `try...except IntegrityError` 捕获唯一约束冲突

14. **`batch_add_rooms(db: AsyncSession, category_id: UUID, room_associations: List[RoomAssociation]) -> List[TopicCategoryRoom]`**
    - 功能：批量添加直播间
    - 实现要点：
      ```python
      associations = []
      for assoc in room_associations:
          tcr = TopicCategoryRoom(
              id=uuid.uuid4(),
              category_id=category_id,
              room_id=assoc.room_id,
              sort_order=assoc.sort_order
          )
          associations.append(tcr)
      
      db.add_all(associations)
      await db.commit()
      ```

15. **`get_rooms_by_category(db: AsyncSession, category_id: UUID, skip: int, limit: int) -> Tuple[List[Dict], int]`**
    - 功能：分页获取分类下的直播间列表
    - 返回：直播间信息字典列表（包含room详情和sort_order）
    - 实现要点：
      ```python
      # JOIN live_rooms表
      select(
          TopicCategoryRoom.id,
          TopicCategoryRoom.sort_order,
          LiveRoom.id.label('room_id'),
          LiveRoom.title,
          LiveRoom.cover_url,
          # ...其他字段
      ).join(LiveRoom).where(
          TopicCategoryRoom.category_id == category_id
      ).order_by(TopicCategoryRoom.sort_order.asc())
      ```

16. **`update_room_sort_order(db: AsyncSession, category_id: UUID, room_sort_updates: List[Dict[str, Any]]) -> int`**
    - 功能：批量更新分类下直播间的排序
    - 参数：`room_sort_updates = [{"room_id": UUID, "sort_order": int}, ...]`
    - 返回：更新的记录数
    - 实现要点：
      ```python
      updated_count = 0
      for update in room_sort_updates:
          result = await db.execute(
              update(TopicCategoryRoom)
              .where(
                  and_(
                      TopicCategoryRoom.category_id == category_id,
                      TopicCategoryRoom.room_id == update["room_id"]
                  )
              )
              .values(sort_order=update["sort_order"])
          )
          updated_count += result.rowcount
      await db.commit()
      return updated_count
      ```

17. **`remove_room_from_category(db: AsyncSession, category_id: UUID, room_id: UUID) -> bool`**
    - 功能：移除单个直播间关联
    - 返回：是否成功删除（True/False）

18. **`batch_remove_rooms(db: AsyncSession, category_id: UUID, room_ids: List[UUID]) -> int`**
    - 功能：批量移除直播间关联
    - 返回：删除的记录数

19. **`check_room_association_exists(db: AsyncSession, category_id: UUID, room_id: UUID) -> bool`**
    - 功能：检查关联是否已存在
    - 用途：避免重复添加

#### **辅助查询操作**

20. **`get_topics_by_room(db: AsyncSession, room_id: UUID) -> List[Dict]`**
    - 功能：获取指定直播间关联的所有已发布专题
    - 返回：
      ```python
      [
          {
              "topic_id": UUID,
              "topic_title": str,
              "topic_status": str,
              "category_id": UUID,
              "category_name": str
          }
      ]
      ```
    - 实现要点：
      ```python
      # 三表JOIN: topic_category_rooms -> topic_categories -> topics
      # 筛选条件: room_id匹配 AND status='published'
      ```

### 5.3. 日志记录规范

在CRUD层，日志记录应当简洁，主要记录：
- **DEBUG级别**：查询操作、参数信息
- **WARNING级别**：删除操作
- **ERROR级别**：数据库异常

**示例**：
```python
logger.debug(f"查询专题: topic_id={topic_id}")
logger.warning(f"删除专题: topic_id={topic_id}, categories_count={len(topic.categories)}")
logger.error(f"数据库错误: operation=create_topic, error={str(e)}")
```

### 5.4. 特别注意事项

#### ⚠️ UUID生成位置
所有主键UUID必须在应用层生成：
```python
topic = Topic(
    id=uuid.uuid4(),  # ✅ 应用层生成
    user_id=user_id,
    title=obj_in.title
)
```

#### ⚠️ 时间戳处理
`created_at` 和 `updated_at` 由数据库自动管理（`server_default=func.now()`），CRUD层无需手动设置。

#### ⚠️ 级联删除
数据库已配置 `ON DELETE CASCADE`，CRUD层删除父对象时，子对象会自动删除，无需手动处理。

#### ⚠️ 预加载关系
对于需要访问关系属性的查询，必须使用 `selectinload` 或 `joinedload`：
```python
# ✅ 正确
select(Topic).options(selectinload(Topic.categories))

# ❌ 错误（会导致N+1查询或LazyLoadingError）
topic = await get_topic(db, topic_id)
categories = topic.categories  # 可能失败
```

## 6. 最终交付 (Final Deliverable)

请根据以上所有要求，为我生成 `app/crud/topic.py` 文件的完整、可直接使用的 Python 代码。

**代码应包含**：
1. 完整的模块文档字符串
2. 所有必要的导入语句
3. 上述列出的所有20个函数
4. 完整的类型注解
5. 适当的日志记录
6. 完善的异常处理（遵循安全异步异常处理原则）
7. 详细的函数文档字符串（参数、返回值、异常说明）

**代码格式要求**：
- 将代码放在独立的代码块中
- 使用清晰的注释说明关键逻辑
- 确保所有函数签名与上述规格完全一致

