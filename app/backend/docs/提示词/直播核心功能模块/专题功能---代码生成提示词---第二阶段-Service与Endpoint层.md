# 专题功能代码生成提示词 - 第二阶段（Service层 + Endpoint层）

## 1. 角色定义 (Role Definition)

你是一名资深的 Python 后端工程师和系统架构师，精通 FastAPI、异步编程、RESTful API设计和分层架构。你擅长将业务逻辑从数据访问层分离，构建清晰、可测试、可维护的代码结构。

## 2. 任务目标 (Task Objective)

你的任务是为**专题聚合功能 (Topics)**生成第二阶段的代码，包括：

1. **业务逻辑层 (Service Layer)**：创建 `app/services/topic_service.py` 文件，封装所有专题相关的业务逻辑
2. **API端点层 (Endpoint Layer)**：创建 `app/api/v1/endpoints/topic.py` 文件，实现所有RESTful API接口

在此阶段，Service层负责：
- 业务逻辑验证（权限检查、状态检查等）
- 复杂查询的组装
- 事务管理

Endpoint层负责：
- HTTP请求/响应处理
- 调用Service层
- 异常转换为HTTP响应

## 3. 核心上下文信息 (Core Context Information)

### 3.1. 项目结构

```
backend/live_core_service/
├── app/
│   ├── services/
│   │   └── topic_service.py      # <-- 目标文件1（本阶段）
│   ├── api/v1/endpoints/
│   │   └── topic.py              # <-- 目标文件2（本阶段）
│   ├── crud/
│   │   └── topic.py              # <-- 已存在（第一阶段生成）
│   ├── models/
│   │   ├── live_core.py          # <-- 已存在（包含LiveRoom, LiveSession模型）
│   │   └── topic.py              # <-- 已存在（包含Topic, TopicCategory, TopicCategoryRoom模型）
│   ├── schemas/
│   │   └── topic.py              # <-- 已存在
│   ├── core/
│   │   ├── deps.py               # <-- 已存在（包含get_current_user）
│   │   └── responses.py          # <-- 已存在（success_response, error_response）
│   ├── exceptions.py             # <-- 需要添加专题相关异常
│   └── database.py               # <-- 已存在（提供get_db）
```

### 3.2. 依赖代码假设

假设以下代码已存在且可用：
#### `app/models/live_core.py`
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

#### `app/schema/topic.py`
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
    注意：banner_url 不在此基类中，通过专门的上传接口设置。
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
    # banner_url 已移除，通过 POST /api/v1/topics/{topic_id}/banner 接口上传
    status: TopicStatus = Field(
        default=TopicStatus.DRAFT, 
        description="专题状态，默认为草稿"
    )


class TopicCreate(TopicBase):
    """
    创建专题请求 Schema
    
    用于 POST /api/v1/topics 接口的请求体。
    user_id 从 JWT Token 中提取，不在请求体中。
    banner_url 默认为 NULL，需通过 POST /api/v1/topics/{topic_id}/banner 接口上传。
    """
    pass  # 继承 TopicBase 的所有字段（不包含 banner_url）


class TopicUpdate(BaseModel):
    """
    更新专题请求 Schema
    
    用于 PATCH /api/v1/topics/{topic_id} 接口的请求体。
    所有字段都是可选的，允许部分更新（PATCH 语义）。
    注意：banner_url 不能通过此接口更新，需使用专门的上传接口。
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
    # banner_url 已移除，通过 POST /api/v1/topics/{topic_id}/banner 接口更新
    status: Optional[TopicStatus] = Field(
        None,
        description="专题状态"
    )


class TopicInDB(TopicBase):
    """
    数据库中的专题 Schema
    
    包含所有数据库字段，包括系统生成的 id 和时间戳。
    支持从 SQLAlchemy ORM 对象转换。
    注意：banner_url 在此显式声明，因为 TopicBase 中已移除。
    """
    id: uuid.UUID = Field(..., description="专题唯一标识")
    user_id: uuid.UUID = Field(..., description="创建者用户ID")
    banner_url: Optional[str] = Field(
        None, 
        description="横幅图URL，通过上传接口设置，默认为null"
    )
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

#### 横幅上传接口说明

**注意**：横幅上传接口应**复用**直播间封面上传的逻辑。假设已存在 `upload_room_cover` 函数或类似的文件上传服务，横幅上传可以这样实现：

```python
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
from datetime import datetime

@router.post("/{topic_id}/banner")
async def upload_topic_banner(
    topic_id: uuid.UUID,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    上传/更新专题横幅
    
    完全复用直播间封面上传的实现逻辑：
    - 文件校验：PNG, JPG 格式，5MB 以内
    - 权限验证：仅创建者可上传
    - 存储路径：/media/topics/{topic_id}/banner_{timestamp}.{ext}
    """
    # 1. 验证专题存在性和权限
    from app.crud import topic as crud_topic
    topic = await crud_topic.get(db, topic_id)
    if not topic:
        return JSONResponse(
            status_code=404,
            content=error_response(
                code=2001, 
                message="资源不存在",
                data={"resource": "Topic", "id": str(topic_id)}
            )
        )
    
    if topic.user_id != uuid.UUID(current_user["user_id"]):
        return JSONResponse(
            status_code=403,
            content=error_response(
                code=2003,
                message="操作被禁止",
                data={"error": "权限不足", "reason": "只有创建者可以上传横幅"}
            )
        )
    
    # 2. 文件校验
    if file.content_type not in ["image/png", "image/jpeg"]:
        return JSONResponse(
            status_code=400,
            content=error_response(
                code=4002,
                message="参数校验失败",
                data={"file": "仅支持 PNG, JPG 格式"}
            )
        )
    
    # 3. 复用文件上传服务（与直播间封面相同的逻辑）
    # 4. 保存文件到 /media/topics/{topic_id}/banner_{timestamp}.ext
    # 5. 更新数据库 topic.banner_url
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    file_ext = file.filename.split('.')[-1].lower()
    banner_url = f"/media/topics/{topic_id}/banner_{timestamp}.{file_ext}"
    
    # 更新数据库
    topic.banner_url = banner_url
    await db.commit()
    
    # 6. 返回响应
    return success_response(data={
        "topic_id": str(topic_id),
        "banner_url": banner_url
    })
```

---

#### `app/crud/topic.py`
```python
"""
专题聚合功能的 CRUD 层

本模块封装所有与 Topic、TopicCategory、TopicCategoryRoom 模型相关的数据库操作。
提供纯粹的数据访问接口，不包含任何业务逻辑验证。

所有函数遵循以下规范：
- 使用 async/await 异步编程
- UUID 在应用层生成
- 使用 selectinload/joinedload 避免 N+1 查询
- 遵循安全异步异常处理原则（提前提取变量）
- 记录适当的日志
"""

# 标准库导入
import uuid
import logging
from typing import List, Optional, Tuple, Dict, Any

# 第三方库导入
from sqlalchemy import select, update, delete, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.exc import IntegrityError

# 项目内导入
from app.models.topic import Topic, TopicCategory, TopicCategoryRoom, TopicStatus
from app.models.live_core import LiveRoom, LiveSession
from app.schemas.topic import TopicCreate, TopicUpdate, CategoryCreate, CategoryUpdate, RoomAssociation

# 配置日志
logger = logging.getLogger(__name__)


# ==================== 专题 (Topic) 相关操作 ====================

async def create(
    db: AsyncSession, 
    obj_in: TopicCreate, 
    user_id: uuid.UUID
) -> Topic:
    """
    创建新专题
    
    Args:
        db: 数据库会话
        obj_in: 专题创建数据
        user_id: 创建者用户ID
    
    Returns:
        Topic: 创建的专题对象
    
    Raises:
        IntegrityError: 数据库完整性约束错误
    """
    # 应用层生成UUID
    topic_id = uuid.uuid4()
    
    topic = Topic(
        id=topic_id,
        user_id=user_id,
        title=obj_in.title,
        description=obj_in.description,
        banner_url=obj_in.banner_url,
        status=obj_in.status
    )
    
    # 提前提取用于日志的变量
    topic_id_for_logging = topic.id
    user_id_for_logging = user_id
    
    try:
        db.add(topic)
        await db.commit()
        await db.refresh(topic)
        logger.debug(f"创建专题成功: topic_id={topic_id_for_logging}, user_id={user_id_for_logging}")
        return topic
    except IntegrityError as e:
        await db.rollback()
        # ✅ 使用局部变量记录日志
        logger.error(f"创建专题失败-完整性错误: topic_id={topic_id_for_logging}, error={str(e)}")
        raise
    except Exception as e:
        await db.rollback()
        # ✅ 使用局部变量记录日志
        logger.error(f"创建专题失败: topic_id={topic_id_for_logging}, error={str(e)}")
        raise


async def get(db: AsyncSession, topic_id: uuid.UUID) -> Optional[Topic]:
    """
    根据ID获取单个专题
    
    Args:
        db: 数据库会话
        topic_id: 专题唯一标识
    
    Returns:
        Optional[Topic]: 专题对象，如果不存在则返回None
    """
    logger.debug(f"查询专题: topic_id={topic_id}")
    
    stmt = select(Topic).where(Topic.id == topic_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_with_categories(
    db: AsyncSession, 
    topic_id: uuid.UUID
) -> Optional[Topic]:
    """
    获取专题及其所有分类（预加载）
    
    使用 selectinload 避免 N+1 查询问题。
    
    Args:
        db: 数据库会话
        topic_id: 专题唯一标识
    
    Returns:
        Optional[Topic]: 包含预加载分类的专题对象，如果不存在则返回None
    """
    logger.debug(f"查询专题及分类: topic_id={topic_id}")
    
    stmt = select(Topic).options(
        selectinload(Topic.categories)
    ).where(Topic.id == topic_id)
    
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_multi_and_total(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 10,
    status: Optional[TopicStatus] = None,
    user_id: Optional[uuid.UUID] = None
) -> Tuple[List[Topic], int]:
    """
    分页获取专题列表，支持按状态和用户ID筛选
    
    Args:
        db: 数据库会话
        skip: 跳过的记录数（用于分页）
        limit: 返回的最大记录数
        status: 专题状态筛选条件（可选）
        user_id: 用户ID筛选条件（可选）
    
    Returns:
        Tuple[List[Topic], int]: (专题列表, 总记录数)
    """
    logger.debug(f"查询专题列表: skip={skip}, limit={limit}, status={status}, user_id={user_id}")
    
    # 构建基础查询
    stmt = select(Topic)
    count_stmt = select(func.count()).select_from(Topic)
    
    # 应用筛选条件
    filters = []
    if status is not None:
        filters.append(Topic.status == status)
    if user_id is not None:
        filters.append(Topic.user_id == user_id)
    
    if filters:
        stmt = stmt.where(and_(*filters))
        count_stmt = count_stmt.where(and_(*filters))
    
    # 获取总数
    total_result = await db.execute(count_stmt)
    total = total_result.scalar()
    
    # 应用排序和分页
    stmt = stmt.order_by(Topic.created_at.desc()).offset(skip).limit(limit)
    
    # 执行查询
    result = await db.execute(stmt)
    topics = result.scalars().all()
    
    return list(topics), total


async def update(
    db: AsyncSession, 
    db_obj: Topic, 
    obj_in: TopicUpdate
) -> Topic:
    """
    更新专题信息
    
    Args:
        db: 数据库会话
        db_obj: 要更新的专题对象
        obj_in: 更新数据
    
    Returns:
        Topic: 更新后的专题对象
    
    Raises:
        IntegrityError: 数据库完整性约束错误
    """
    # 提前提取用于日志的变量
    topic_id_for_logging = db_obj.id
    
    # 获取更新数据（排除未设置的字段）
    update_data = obj_in.model_dump(exclude_unset=True)
    
    logger.debug(f"更新专题: topic_id={topic_id_for_logging}, fields={list(update_data.keys())}")
    
    try:
        # 更新字段
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    except IntegrityError as e:
        await db.rollback()
        # ✅ 使用局部变量记录日志
        logger.error(f"更新专题失败-完整性错误: topic_id={topic_id_for_logging}, error={str(e)}")
        raise
    except Exception as e:
        await db.rollback()
        # ✅ 使用局部变量记录日志
        logger.error(f"更新专题失败: topic_id={topic_id_for_logging}, error={str(e)}")
        raise


async def remove(db: AsyncSession, db_obj: Topic) -> Topic:
    """
    删除专题（级联删除分类和关联）
    
    数据库已配置 ON DELETE CASCADE，子对象会自动删除。
    
    Args:
        db: 数据库会话
        db_obj: 要删除的专题对象
    
    Returns:
        Topic: 被删除的专题对象
    
    Raises:
        Exception: 删除操作失败
    """
    # 提前提取用于日志的变量
    topic_id_for_logging = db_obj.id
    categories_count = len(db_obj.categories) if hasattr(db_obj, 'categories') else 0
    
    logger.warning(f"删除专题: topic_id={topic_id_for_logging}, categories_count={categories_count}")
    
    try:
        await db.delete(db_obj)
        await db.commit()
        return db_obj
    except Exception as e:
        await db.rollback()
        # ✅ 使用局部变量记录日志
        logger.error(f"删除专题失败: topic_id={topic_id_for_logging}, error={str(e)}")
        raise


# ==================== 分类 (TopicCategory) 相关操作 ====================

async def create_category(
    db: AsyncSession,
    obj_in: CategoryCreate,
    topic_id: uuid.UUID
) -> TopicCategory:
    """
    创建新分类
    
    Args:
        db: 数据库会话
        obj_in: 分类创建数据
        topic_id: 所属专题ID
    
    Returns:
        TopicCategory: 创建的分类对象
    
    Raises:
        IntegrityError: 数据库完整性约束错误（如分类名称重复）
    """
    # 应用层生成UUID
    category_id = uuid.uuid4()
    
    category = TopicCategory(
        id=category_id,
        topic_id=topic_id,
        name=obj_in.name,
        sort_order=obj_in.sort_order
    )
    
    # 提前提取用于日志的变量
    category_id_for_logging = category.id
    topic_id_for_logging = topic_id
    
    try:
        db.add(category)
        await db.commit()
        await db.refresh(category)
        logger.debug(f"创建分类成功: category_id={category_id_for_logging}, topic_id={topic_id_for_logging}")
        return category
    except IntegrityError as e:
        await db.rollback()
        # ✅ 使用局部变量记录日志
        logger.error(f"创建分类失败-完整性错误: category_id={category_id_for_logging}, error={str(e)}")
        raise
    except Exception as e:
        await db.rollback()
        # ✅ 使用局部变量记录日志
        logger.error(f"创建分类失败: category_id={category_id_for_logging}, error={str(e)}")
        raise


async def get_category(
    db: AsyncSession, 
    category_id: uuid.UUID
) -> Optional[TopicCategory]:
    """
    根据ID获取单个分类
    
    Args:
        db: 数据库会话
        category_id: 分类唯一标识
    
    Returns:
        Optional[TopicCategory]: 分类对象，如果不存在则返回None
    """
    logger.debug(f"查询分类: category_id={category_id}")
    
    stmt = select(TopicCategory).where(TopicCategory.id == category_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_category_with_topic(
    db: AsyncSession,
    category_id: uuid.UUID
) -> Optional[TopicCategory]:
    """
    获取分类及其关联的专题（用于权限验证）
    
    使用 selectinload 预加载专题对象。
    
    Args:
        db: 数据库会话
        category_id: 分类唯一标识
    
    Returns:
        Optional[TopicCategory]: 包含预加载专题的分类对象，如果不存在则返回None
    """
    logger.debug(f"查询分类及专题: category_id={category_id}")
    
    stmt = select(TopicCategory).options(
        selectinload(TopicCategory.topic)
    ).where(TopicCategory.id == category_id)
    
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_categories_by_topic(
    db: AsyncSession,
    topic_id: uuid.UUID,
    skip: int = 0,
    limit: int = 100
) -> Tuple[List[TopicCategory], int]:
    """
    分页获取专题下的所有分类
    
    按 sort_order ASC 排序。
    
    Args:
        db: 数据库会话
        topic_id: 专题唯一标识
        skip: 跳过的记录数
        limit: 返回的最大记录数
    
    Returns:
        Tuple[List[TopicCategory], int]: (分类列表, 总记录数)
    """
    logger.debug(f"查询专题分类列表: topic_id={topic_id}, skip={skip}, limit={limit}")
    
    # 获取总数
    count_stmt = select(func.count()).select_from(TopicCategory).where(
        TopicCategory.topic_id == topic_id
    )
    total_result = await db.execute(count_stmt)
    total = total_result.scalar()
    
    # 获取分类列表
    stmt = select(TopicCategory).where(
        TopicCategory.topic_id == topic_id
    ).order_by(TopicCategory.sort_order.asc()).offset(skip).limit(limit)
    
    result = await db.execute(stmt)
    categories = result.scalars().all()
    
    return list(categories), total


async def update_category(
    db: AsyncSession,
    db_obj: TopicCategory,
    obj_in: CategoryUpdate
) -> TopicCategory:
    """
    更新分类信息
    
    Args:
        db: 数据库会话
        db_obj: 要更新的分类对象
        obj_in: 更新数据
    
    Returns:
        TopicCategory: 更新后的分类对象
    
    Raises:
        IntegrityError: 数据库完整性约束错误
    """
    # 提前提取用于日志的变量
    category_id_for_logging = db_obj.id
    
    # 获取更新数据
    update_data = obj_in.model_dump(exclude_unset=True)
    
    logger.debug(f"更新分类: category_id={category_id_for_logging}, fields={list(update_data.keys())}")
    
    try:
        # 更新字段
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    except IntegrityError as e:
        await db.rollback()
        # ✅ 使用局部变量记录日志
        logger.error(f"更新分类失败-完整性错误: category_id={category_id_for_logging}, error={str(e)}")
        raise
    except Exception as e:
        await db.rollback()
        # ✅ 使用局部变量记录日志
        logger.error(f"更新分类失败: category_id={category_id_for_logging}, error={str(e)}")
        raise


async def remove_category(
    db: AsyncSession, 
    db_obj: TopicCategory
) -> TopicCategory:
    """
    删除分类（级联删除关联）
    
    数据库已配置 ON DELETE CASCADE，关联的直播间记录会自动删除。
    
    Args:
        db: 数据库会话
        db_obj: 要删除的分类对象
    
    Returns:
        TopicCategory: 被删除的分类对象
    
    Raises:
        Exception: 删除操作失败
    """
    # 提前提取用于日志的变量
    category_id_for_logging = db_obj.id
    rooms_count = len(db_obj.rooms) if hasattr(db_obj, 'rooms') else 0
    
    logger.warning(f"删除分类: category_id={category_id_for_logging}, rooms_count={rooms_count}")
    
    try:
        await db.delete(db_obj)
        await db.commit()
        return db_obj
    except Exception as e:
        await db.rollback()
        # ✅ 使用局部变量记录日志
        logger.error(f"删除分类失败: category_id={category_id_for_logging}, error={str(e)}")
        raise


# ==================== 直播间关联 (TopicCategoryRoom) 相关操作 ====================

async def add_room_to_category(
    db: AsyncSession,
    category_id: uuid.UUID,
    room_id: uuid.UUID,
    sort_order: int = 0
) -> TopicCategoryRoom:
    """
    将直播间添加到分类
    
    Args:
        db: 数据库会话
        category_id: 分类唯一标识
        room_id: 直播间唯一标识
        sort_order: 排序顺序，默认0
    
    Returns:
        TopicCategoryRoom: 创建的关联对象
    
    Raises:
        IntegrityError: 唯一约束冲突（直播间已存在于该分类）
    """
    # 应用层生成UUID
    association_id = uuid.uuid4()
    
    association = TopicCategoryRoom(
        id=association_id,
        category_id=category_id,
        room_id=room_id,
        sort_order=sort_order
    )
    
    # 提前提取用于日志的变量
    association_id_for_logging = association.id
    category_id_for_logging = category_id
    room_id_for_logging = room_id
    
    try:
        db.add(association)
        await db.commit()
        await db.refresh(association)
        logger.debug(
            f"添加直播间到分类成功: association_id={association_id_for_logging}, "
            f"category_id={category_id_for_logging}, room_id={room_id_for_logging}"
        )
        return association
    except IntegrityError as e:
        await db.rollback()
        # ✅ 使用局部变量记录日志
        logger.error(
            f"添加直播间失败-完整性错误: category_id={category_id_for_logging}, "
            f"room_id={room_id_for_logging}, error={str(e)}"
        )
        raise
    except Exception as e:
        await db.rollback()
        # ✅ 使用局部变量记录日志
        logger.error(
            f"添加直播间失败: category_id={category_id_for_logging}, "
            f"room_id={room_id_for_logging}, error={str(e)}"
        )
        raise


async def batch_add_rooms(
    db: AsyncSession,
    category_id: uuid.UUID,
    room_associations: List[RoomAssociation]
) -> List[TopicCategoryRoom]:
    """
    批量添加直播间到分类
    
    Args:
        db: 数据库会话
        category_id: 分类唯一标识
        room_associations: 直播间关联列表
    
    Returns:
        List[TopicCategoryRoom]: 创建的关联对象列表
    
    Raises:
        IntegrityError: 唯一约束冲突
    """
    # 提前提取用于日志的变量
    category_id_for_logging = category_id
    room_count = len(room_associations)
    
    logger.debug(f"批量添加直播间: category_id={category_id_for_logging}, count={room_count}")
    
    associations = []
    for assoc in room_associations:
        tcr = TopicCategoryRoom(
            id=uuid.uuid4(),
            category_id=category_id,
            room_id=assoc.room_id,
            sort_order=assoc.sort_order
        )
        associations.append(tcr)
    
    try:
        db.add_all(associations)
        await db.commit()
        
        # 刷新所有对象
        for assoc in associations:
            await db.refresh(assoc)
        
        return associations
    except IntegrityError as e:
        await db.rollback()
        # ✅ 使用局部变量记录日志
        logger.error(
            f"批量添加直播间失败-完整性错误: category_id={category_id_for_logging}, "
            f"count={room_count}, error={str(e)}"
        )
        raise
    except Exception as e:
        await db.rollback()
        # ✅ 使用局部变量记录日志
        logger.error(
            f"批量添加直播间失败: category_id={category_id_for_logging}, "
            f"count={room_count}, error={str(e)}"
        )
        raise


async def get_rooms_by_category(
    db: AsyncSession,
    category_id: uuid.UUID,
    skip: int = 0,
    limit: int = 100
) -> Tuple[List[Dict[str, Any]], int]:
    """
    分页获取分类下的直播间列表
    
    返回直播间信息字典列表，包含room详情和sort_order。
    按 sort_order ASC 排序。
    
    Args:
        db: 数据库会话
        category_id: 分类唯一标识
        skip: 跳过的记录数
        limit: 返回的最大记录数
    
    Returns:
        Tuple[List[Dict], int]: (直播间信息字典列表, 总记录数)
    """
    logger.debug(f"查询分类直播间列表: category_id={category_id}, skip={skip}, limit={limit}")
    
    # 获取总数
    count_stmt = select(func.count()).select_from(TopicCategoryRoom).where(
        TopicCategoryRoom.category_id == category_id
    )
    total_result = await db.execute(count_stmt)
    total = total_result.scalar()
    
    # 获取直播间列表（JOIN live_rooms表）
    stmt = select(
        TopicCategoryRoom.id.label('association_id'),
        TopicCategoryRoom.sort_order,
        LiveRoom.id.label('room_id'),
        LiveRoom.title,
        LiveRoom.cover_url,
        LiveRoom.user_id,
        LiveRoom.created_at
    ).join(
        LiveRoom, TopicCategoryRoom.room_id == LiveRoom.id
    ).where(
        TopicCategoryRoom.category_id == category_id
    ).order_by(
        TopicCategoryRoom.sort_order.asc()
    ).offset(skip).limit(limit)
    
    result = await db.execute(stmt)
    rows = result.all()
    
    # 转换为字典列表
    rooms = [
        {
            "association_id": str(row.association_id),
            "sort_order": row.sort_order,
            "room_id": str(row.room_id),
            "title": row.title,
            "cover_url": row.cover_url,
            "user_id": str(row.user_id),
            "created_at": row.created_at
        }
        for row in rows
    ]
    
    return rooms, total


async def update_room_sort_order(
    db: AsyncSession,
    category_id: uuid.UUID,
    room_sort_updates: List[Dict[str, Any]]
) -> int:
    """
    批量更新分类下直播间的排序
    
    Args:
        db: 数据库会话
        category_id: 分类唯一标识
        room_sort_updates: 更新列表，格式为 [{"room_id": UUID, "sort_order": int}, ...]
    
    Returns:
        int: 更新的记录数
    
    Raises:
        Exception: 更新操作失败
    """
    # 提前提取用于日志的变量
    category_id_for_logging = category_id
    update_count = len(room_sort_updates)
    
    logger.debug(f"批量更新排序: category_id={category_id_for_logging}, count={update_count}")
    
    updated_count = 0
    
    try:
        for item in room_sort_updates:
            stmt = update(TopicCategoryRoom).where(
                and_(
                    TopicCategoryRoom.category_id == category_id,
                    TopicCategoryRoom.room_id == item["room_id"]
                )
            ).values(sort_order=item["sort_order"])
            
            result = await db.execute(stmt)
            updated_count += result.rowcount
        
        await db.commit()
        logger.debug(f"批量更新排序成功: updated_count={updated_count}")
        return updated_count
    except Exception as e:
        await db.rollback()
        # ✅ 使用局部变量记录日志
        logger.error(
            f"批量更新排序失败: category_id={category_id_for_logging}, "
            f"count={update_count}, error={str(e)}"
        )
        raise


async def remove_room_from_category(
    db: AsyncSession,
    category_id: uuid.UUID,
    room_id: uuid.UUID
) -> bool:
    """
    移除单个直播间关联
    
    Args:
        db: 数据库会话
        category_id: 分类唯一标识
        room_id: 直播间唯一标识
    
    Returns:
        bool: 是否成功删除（True表示删除了记录，False表示记录不存在）
    
    Raises:
        Exception: 删除操作失败
    """
    # 提前提取用于日志的变量
    category_id_for_logging = category_id
    room_id_for_logging = room_id
    
    logger.debug(f"移除直播间关联: category_id={category_id_for_logging}, room_id={room_id_for_logging}")
    
    try:
        stmt = delete(TopicCategoryRoom).where(
            and_(
                TopicCategoryRoom.category_id == category_id,
                TopicCategoryRoom.room_id == room_id
            )
        )
        
        result = await db.execute(stmt)
        await db.commit()
        
        success = result.rowcount > 0
        logger.debug(f"移除直播间关联结果: success={success}")
        return success
    except Exception as e:
        await db.rollback()
        # ✅ 使用局部变量记录日志
        logger.error(
            f"移除直播间关联失败: category_id={category_id_for_logging}, "
            f"room_id={room_id_for_logging}, error={str(e)}"
        )
        raise


async def batch_remove_rooms(
    db: AsyncSession,
    category_id: uuid.UUID,
    room_ids: List[uuid.UUID]
) -> int:
    """
    批量移除直播间关联
    
    Args:
        db: 数据库会话
        category_id: 分类唯一标识
        room_ids: 要移除的直播间ID列表
    
    Returns:
        int: 删除的记录数
    
    Raises:
        Exception: 删除操作失败
    """
    # 提前提取用于日志的变量
    category_id_for_logging = category_id
    room_count = len(room_ids)
    
    logger.debug(f"批量移除直播间: category_id={category_id_for_logging}, count={room_count}")
    
    try:
        stmt = delete(TopicCategoryRoom).where(
            and_(
                TopicCategoryRoom.category_id == category_id,
                TopicCategoryRoom.room_id.in_(room_ids)
            )
        )
        
        result = await db.execute(stmt)
        await db.commit()
        
        deleted_count = result.rowcount
        logger.debug(f"批量移除直播间成功: deleted_count={deleted_count}")
        return deleted_count
    except Exception as e:
        await db.rollback()
        # ✅ 使用局部变量记录日志
        logger.error(
            f"批量移除直播间失败: category_id={category_id_for_logging}, "
            f"count={room_count}, error={str(e)}"
        )
        raise


async def check_room_association_exists(
    db: AsyncSession,
    category_id: uuid.UUID,
    room_id: uuid.UUID
) -> bool:
    """
    检查关联是否已存在
    
    用于避免重复添加直播间到同一分类。
    
    Args:
        db: 数据库会话
        category_id: 分类唯一标识
        room_id: 直播间唯一标识
    
    Returns:
        bool: 关联是否存在
    """
    logger.debug(f"检查关联存在性: category_id={category_id}, room_id={room_id}")
    
    stmt = select(func.count()).select_from(TopicCategoryRoom).where(
        and_(
            TopicCategoryRoom.category_id == category_id,
            TopicCategoryRoom.room_id == room_id
        )
    )
    
    result = await db.execute(stmt)
    count = result.scalar()
    
    exists = count > 0
    logger.debug(f"关联存在性检查结果: exists={exists}")
    return exists


# ==================== 辅助查询操作 ====================

async def get_topics_by_room(
    db: AsyncSession,
    room_id: uuid.UUID
) -> List[Dict[str, Any]]:
    """
    获取指定直播间关联的所有已发布专题
    
    返回专题和分类的信息，用于在直播间详情页显示"该直播间所属的专题活动"。
    
    Args:
        db: 数据库会话
        room_id: 直播间唯一标识
    
    Returns:
        List[Dict]: 专题信息字典列表，包含:
            - topic_id: 专题ID
            - topic_title: 专题标题
            - topic_status: 专题状态
            - category_id: 分类ID
            - category_name: 分类名称
    """
    logger.debug(f"查询直播间关联的专题: room_id={room_id}")
    
    # 三表JOIN: topic_category_rooms -> topic_categories -> topics
    # 筛选条件: room_id匹配 AND status='published'
    stmt = select(
        Topic.id.label('topic_id'),
        Topic.title.label('topic_title'),
        Topic.status.label('topic_status'),
        TopicCategory.id.label('category_id'),
        TopicCategory.name.label('category_name')
    ).select_from(TopicCategoryRoom).join(
        TopicCategory, TopicCategoryRoom.category_id == TopicCategory.id
    ).join(
        Topic, TopicCategory.topic_id == Topic.id
    ).where(
        and_(
            TopicCategoryRoom.room_id == room_id,
            Topic.status == TopicStatus.PUBLISHED
        )
    ).order_by(Topic.created_at.desc())
    
    result = await db.execute(stmt)
    rows = result.all()
    
    # 转换为字典列表
    topics = [
        {
            "topic_id": str(row.topic_id),
            "topic_title": row.topic_title,
            "topic_status": row.topic_status.value if isinstance(row.topic_status, TopicStatus) else row.topic_status,
            "category_id": str(row.category_id),
            "category_name": row.category_name
        }
        for row in rows
    ]
    
    logger.debug(f"找到关联专题数量: count={len(topics)}")
    return topics



```


#### `app/core/responses.py`
```python
from datetime import datetime
from typing import Any

def success_response(data: Any, message: str = "success") -> dict:
    """构建标准成功响应"""
    return {
        "code": 200,
        "message": message,
        "data": data,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

def error_response(code: int, message: str, data: Any = None) -> dict:
    """构建标准错误响应"""
    return {
        "code": code,
        "message": message,
        "data": data,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
```

#### `app/core/deps.py`
```python
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

security = HTTPBearer()

async def get_current_user(token: str = Depends(security)) -> dict:
    """验证JWT Token并返回用户信息"""
    # 实际实现会验证Token
    return {
        "user_id": "uuid...",  # 从Token解析出的user_id
        "username": "user1"
    }
```

#### `app/database.py`
```python
async def get_db() -> AsyncSession:
    """获取数据库会话的依赖函数"""
    # 实际实现...
    pass
```

## 4. 通用规范与核心原则

### 4.1. 🛡️ 安全异步异常处理（强制执行）

**在Service层和Endpoint层都必须遵守以下规则：**

1. **主动变量提取**：在进入 `try` 块之前，主动提取所有需要在异常处理中使用的变量
2. **禁止在except块中访问ORM对象**：捕获数据库异常后，只使用局部变量

**Service层示例**：
```python
async def update_topic(self, topic_id: UUID, user_id: UUID, obj_in: TopicUpdate) -> Topic:
    # ✅ 提前提取用于日志的变量
    topic_id_for_logging = topic_id
    user_id_for_logging = user_id
    
    try:
        topic = await crud_topic.get(self.db, topic_id)
        if not topic:
            raise TopicNotFoundException(str(topic_id))
        
        # 权限验证
        if topic.user_id != user_id:
            raise TopicPermissionDeniedException("修改")
        
        # 再次提取（如果需要在commit后使用）
        topic_id_for_logging = topic.id
        
        updated_topic = await crud_topic.update(self.db, topic, obj_in)
        return updated_topic
        
    except (TopicNotFoundException, TopicPermissionDeniedException):
        # 业务异常直接抛出
        raise
    except Exception as e:
        # ✅ 使用局部变量记录日志
        logger.error(
            f"更新专题失败: topic_id={topic_id_for_logging}, "
            f"user_id={user_id_for_logging}, error={str(e)}"
        )
        raise
```

**Endpoint层示例**：
```python
@router.patch("/{topic_id}")
async def update_topic(
    topic_id: uuid.UUID,
    topic_update: TopicUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # ✅ 提前提取用于日志的变量
    user_id_for_logging = current_user["user_id"]
    topic_id_for_logging = topic_id
    
    try:
        service = TopicService(db)
        updated_topic = await service.update_topic(
            topic_id=topic_id,
            user_id=uuid.UUID(user_id_for_logging),
            obj_in=topic_update
        )
        return success_response(data=updated_topic)
    
    except TopicNotFoundException:
        logger.warning(f"专题不存在: topic_id={topic_id_for_logging}")
        return JSONResponse(
            status_code=404,
            content=error_response(code=2001, message="资源不存在", 
                                 data={"resource": "Topic", "id": str(topic_id_for_logging)})
        )
    except TopicPermissionDeniedException as e:
        # ✅ 使用局部变量
        logger.warning(f"权限不足: topic_id={topic_id_for_logging}, user_id={user_id_for_logging}")
        return JSONResponse(
            status_code=403,
            content=error_response(code=2003, message="操作被禁止", data={"error": str(e)})
        )
    except Exception as e:
        # ✅ 使用局部变量记录未知错误
        logger.error(
            f"更新专题异常: topic_id={topic_id_for_logging}, "
            f"user_id={user_id_for_logging}, error={str(e)}"
        )
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="数据库操作错误")
        )
```

### 4.2. 🌐 RESTful 设计规范

**⚠️ 关键：避免路由配置错误（404 Not Found）**

**URL路径规范**：

1. **路由器定义时不指定 prefix**（prefix 统一在 `api.py` 中指定）
   ```python
   # ✅ 正确：在 endpoints/topic.py 中
   router = APIRouter(tags=["Topics"])
   category_router = APIRouter(tags=["Topic Categories"])
   room_router = APIRouter(tags=["Room-Topic Relations"])
   
   # ❌ 错误：不要在定义时指定 prefix
   router = APIRouter(prefix="/topics", tags=["Topics"])
   )
```

**注意：**
- ✅ 路由器定义时**只指定 tags**，不指定 prefix
- ✅ prefix 将在 `api.py` 中注册时统一指定

2. **集合端点**：对于操作集合的端点（GET列表、POST创建），使用空字符串 ""
   ```python
   # ✅ 正确
   @router.get("")   # 最终路径：GET /api/v1/topics
   @router.post("")  # 最终路径：POST /api/v1/topics
   
   # ❌ 错误：使用 "/" 会导致路径末尾有斜杠
   @router.get("/")   # 错误路径：GET /api/v1/topics/
   @router.post("/")  # 错误路径：POST /api/v1/topics/...
   ```

3. **单个资源端点**：使用 `path="/{resource_id}"`
   ```python
   @router.get("/{topic_id}")     # GET /api/v1/topics/{topic_id}
   @router.patch("/{topic_id}")   # PATCH /api/v1/topics/{topic_id}
   @router.delete("/{topic_id}")  # DELETE /api/v1/topics/{topic_id}
   ```

4. **嵌套资源**：使用 `path="/{parent_id}/子资源"`
   ```python
   @router.post("/{topic_id}/categories")  # POST /api/v1/topics/{topic_id}/categories
   @router.get("/{topic_id}/categories")   # GET /api/v1/topics/{topic_id}/categories
   ```
5.在 api.py 中注册路由时指定 prefix
   # 在 app/api/v1/api.py 中
   from app.api.v1.endpoints import topic
   
   # 必须显式指定每个路由器的 prefix
   api_router.include_router(
       topic.router,
       prefix="/topics",      # 在这里统一指定 prefix
       tags=["topics"]
   )
   
   api_router.include_router(
       topic.category_router,
       prefix="/topic-categories",
       tags=["topic-categories"]
   )
   
   api_router.include_router(
       topic.room_router,
       prefix="/rooms",
       tags=["room-topic-relations"]
   )
   
### 4.3. 响应处理规范

#### ✅ 成功响应
所有成功操作**必须**调用 `success_response(data=...)` 并直接返回：
```python
return success_response(data=topic_data)
```

#### ❌ 错误响应
所有业务错误**必须**返回 `JSONResponse`，其 `content` 由 `error_response(...)` 构建：
```python
return JSONResponse(
    status_code=404,
    content=error_response(
        code=2001,
        message="资源不存在",
        data={"resource": "Topic", "id": str(topic_id)}
    )
)
```

### 4.4. 🔐 环境变量驱动配置

所有外部服务连接信息必须通过环境变量读取：
```python
import os

# Service层或配置文件中
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
```

### 4.5. 统一响应结构

所有API响应必须遵循：
```json
{
  "code": 200,
  "message": "success",
  "data": {...},
  "timestamp": "2025-10-15T10:00:00Z"
}
```

分页响应格式：
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "total": 100,
    "page": 1,
    "size": 10,
    "items": [...]
  },
  "timestamp": "2025-10-15T10:00:00Z"
}
```

### 4.6. 状态码约定

| HTTP状态码 | 业务状态码 | 说明 |
|-----------|-----------|------|
| 200 | 200 | 成功 |
| 400 | 4001 | 参数校验失败 |
| 401 | 401 | 未认证 |
| 403 | 2003 | 权限不足 |
| 404 | 2001 | 资源不存在 |
| 500 | 1002 | 数据库操作错误 |

## 5. 具体代码生成指令

### 5.1. 第一部分：`app/exceptions.py` 补充

在现有 `app/exceptions.py` 文件中添加以下专题相关异常：

```python
class TopicNotFoundException(Exception):
    """专题不存在异常"""
    pass

class CategoryNotFoundException(Exception):
    """分类不存在异常"""
    pass

class TopicPermissionDeniedException(Exception):
    """专题权限不足异常"""
    def __init__(self, action: str = "操作"):
        self.message = f"您没有权限进行此{action}"
        super().__init__(self.message)

class RoomAlreadyAssociatedException(Exception):
    """直播间已关联异常"""
    def __init__(self, room_id: str, category_id: str):
        self.message = "该直播间已关联到此分类"
        self.room_id = room_id
        self.category_id = category_id
        super().__init__(self.message)

class RoomNotFoundException(Exception):
    """直播间不存在异常"""
    pass
```

### 5.2. 第二部分：`app/services/topic_service.py`


**职责**：封装所有专题相关的业务逻辑，保持框架无关性。

#### 代码生成模板

请严格按照以下模板生成 `app/services/topic_service.py` 文件：

\`\`\`python
"""
专题聚合功能的 Service 层

本模块封装所有专题相关的业务逻辑，保持框架无关性。

职责：
- 业务逻辑验证（权限检查、状态检查等）
- 复杂查询的组装
- 事务管理

所有方法遵循安全异步异常处理原则。
"""

# 标准库导入
import uuid
import logging
from typing import List, Optional, Tuple, Dict, Any

# 第三方库导入
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

# 项目内导入 - CRUD 模块
from app.crud import topic as crud_topic  # ← 关键！后续所有 CRUD 调用使用 crud_topic

from app.models.topic import Topic, TopicCategory, TopicCategoryRoom, TopicStatus
from app.models.live_core import LiveRoom, LiveSession, SessionStatistics
from app.schemas.topic import (
    TopicCreate, TopicUpdate, TopicResponse,
    CategoryCreate, CategoryUpdate, CategoryResponse,
    RoomAssociation
)
from app.exceptions import (
    TopicNotFoundException,
    CategoryNotFoundException,
    TopicPermissionDeniedException,
    RoomAlreadyAssociatedException,
    RoomNotFoundException
)

# 配置日志
logger = logging.getLogger(__name__)


class TopicService:
    """
    专题聚合功能的业务逻辑服务类
    
    封装所有专题相关的业务逻辑，包括权限验证和复杂查询。
    """
    
    def __init__(self, db: AsyncSession):
        """
        初始化Service，存储数据库会话
        
        Args:
            db: 异步数据库会话对象
        """
        self.db = db
    
    # ==================== 专题管理方法 ====================
    
    async def create_topic(
        self, 
        obj_in: TopicCreate, 
        user_id: uuid.UUID
    ) -> Topic:
        """
        创建新专题
        
        Args:
            obj_in: 专题创建数据
            user_id: 创建者用户ID
        
        Returns:
            Topic: 创建的专题对象
        
        Raises:
            Exception: 数据库操作失败
        """
        # 提前提取用于日志的变量
        user_id_for_logging = user_id
        
        try:
            topic = await crud_topic.create(self.db, obj_in, user_id)  # ← 使用 crud_topic
            logger.info(
                f"创建专题成功: user_id={user_id_for_logging}, "
                f"topic_id={topic.id}, title={topic.title}"
            )
            return topic
        except Exception as e:
            # ✅ 使用局部变量记录日志
            logger.error(
                f"创建专题失败: user_id={user_id_for_logging}, error={str(e)}"
            )
            raise
    
    # ... 继续实现其他方法 ...
\`\`\`

#### 需实现的方法清单

基于上述模板，实现以下所有方法。**注意**：所有 CRUD 调用都使用 `crud_topic.函数名()` 格式。

**需实现的方法清单**：

#### **专题管理方法**

1. **`__init__(self, db: AsyncSession)`**
   - 初始化Service，存储数据库会话

2. **`create_topic(self, obj_in: TopicCreate, user_id: UUID) -> Topic`**
   - 功能：创建新专题
   - 业务逻辑：
     - 调用 `crud_topic.create()`
     - 记录INFO日志
   - 异常：数据库异常

3. **`get_topic_list(self, page: int, size: int, status: Optional[TopicStatus] = None, user_id: Optional[UUID] = None) -> Tuple[List[Topic], int]`**
   - 功能：获取专题列表（支持筛选）
   - 业务逻辑：
     - 计算 `skip = (page - 1) * size`
     - 调用 `crud_topic.get_multi_and_total()`
   - 返回：(专题列表, 总数)

4. **`get_topic_detail(self, topic_id: UUID) -> Dict`**
   - 功能：获取专题详情（包含层级化的分类和直播间）
   - 业务逻辑：
     1. 调用 `crud_topic.get_with_categories()` 获取专题和分类
     2. 如果不存在，抛出 `TopicNotFoundException`
     3. 对每个分类，调用 `crud_topic.get_rooms_by_category()` 获取直播间列表
     4. 对每个直播间，查询 `live_sessions` 和 `session_statistics` 计算heat值：
        ```python
        heat = int(
            total_viewer_count * 0.5 + 
            total_like_count * 0.3 + 
            peak_viewer_count * 0.2
        )
        ```
     5. 组装层级化数据结构
   - 返回：完整的专题详情字典

5. **`update_topic(self, topic_id: UUID, user_id: UUID, obj_in: TopicUpdate) -> Topic`**
   - 功能：更新专题信息
   - 业务逻辑：
     1. 获取专题对象
     2. **权限验证**：检查 `topic.user_id == user_id`
     3. 如果不匹配，抛出 `TopicPermissionDeniedException("修改")`
     4. 调用 `crud_topic.update()`
   - 异常：`TopicNotFoundException`, `TopicPermissionDeniedException`

6. **`delete_topic(self, topic_id: UUID, user_id: UUID) -> Topic`**
   - 功能：删除专题
   - 业务逻辑：
     1. 获取专题对象
     2. **权限验证**：检查 `topic.user_id == user_id`
     3. 调用 `crud_topic.remove()`
     4. 记录WARNING日志
   - 异常：`TopicNotFoundException`, `TopicPermissionDeniedException`

#### **分类管理方法**

7. **`create_category(self, topic_id: UUID, user_id: UUID, obj_in: CategoryCreate) -> TopicCategory`**
   - 功能：创建分类
   - 业务逻辑：
     1. 获取专题对象
     2. **权限验证**：检查 `topic.user_id == user_id`
     3. 调用 `crud_topic.create_category()`

8. **`get_category_list(self, topic_id: UUID, page: int, size: int) -> Tuple[List[TopicCategory], int]`**
   - 功能：获取分类列表
   - 业务逻辑：
     1. 验证专题存在性
     2. 调用 `crud_topic.get_categories_by_topic()`

9. **`update_category(self, category_id: UUID, user_id: UUID, obj_in: CategoryUpdate) -> TopicCategory`**
   - 功能：更新分类
   - 业务逻辑：
     1. 调用 `crud_topic.get_category_with_topic()` 获取分类及其专题
     2. **权限验证**：检查 `category.topic.user_id == user_id`
     3. 调用 `crud_topic.update_category()`

10. **`delete_category(self, category_id: UUID, user_id: UUID) -> TopicCategory`**
    - 功能：删除分类
    - 业务逻辑：同update_category的权限验证流程

#### **直播间关联方法**

11. **`add_rooms_to_category(self, category_id: UUID, user_id: UUID, room_associations: List[RoomAssociation]) -> List[TopicCategoryRoom]`**
    - 功能：批量添加直播间到分类
    - 业务逻辑：
      1. 获取分类及其专题，验证权限
      2. 验证所有 `room_id` 存在（查询 `live_rooms` 表）
      3. 检查是否已存在关联（调用 `crud_topic.check_room_association_exists()`）
      4. 调用 `crud_topic.batch_add_rooms()`
    - 异常：`CategoryNotFoundException`, `TopicPermissionDeniedException`, `RoomNotFoundException`, `RoomAlreadyAssociatedException`

12. **`get_rooms_in_category(self, category_id: UUID, page: int, size: int) -> Tuple[List[Dict], int]`**
    - 功能：获取分类下的直播间列表
    - 业务逻辑：
      1. 验证分类存在
      2. 调用 `crud_topic.get_rooms_by_category()`
      3. 查询每个直播间的最新 `live_status`（从 `live_sessions` 表）

13. **`update_room_sort_order(self, category_id: UUID, user_id: UUID, room_sort_updates: List[Dict]) -> int`**
    - 功能：批量更新排序
    - 业务逻辑：
      1. 获取分类及其专题，验证权限
      2. 调用 `crud_topic.update_room_sort_order()`

14. **`remove_rooms_from_category(self, category_id: UUID, user_id: UUID, room_ids: List[UUID]) -> int`**
    - 功能：批量移除直播间
    - 业务逻辑：
      1. 获取分类及其专题，验证权限
      2. 调用 `crud_topic.batch_remove_rooms()`

#### **辅助查询方法**

15. **`get_topics_by_room(self, room_id: UUID) -> List[Dict]`**
    - 功能：获取直播间关联的专题列表
    - 业务逻辑：
      1. 验证直播间存在
      2. 调用 `crud_topic.get_topics_by_room()`
      3. 仅返回 `status='published'` 的专题

16. **`batch_get_room_status(self, room_ids: List[UUID]) -> List[Dict]`**
    - 功能：批量获取多个直播间的实时状态
    - 业务逻辑：
      1. 参数验证：检查 `room_ids` 列表长度不超过100（防止性能问题）
      2. 批量查询直播间：查询 `live_rooms` 表确认所有直播间存在
      3. 批量查询场次状态：
         - 查询 `live_sessions` 表，对每个 `room_id`，获取最新的场次
         - 优先返回 `status = 'live'` 的场次，其次是 `status = 'scheduled'`
      4. 批量查询观看人数：对于 `status = 'live'` 的场次，查询 `session_statistics` 表获取 `current_viewer_count`
      5. 组装结果：为每个直播间构建状态对象
    - 返回：直播间状态列表 `[{"room_id": UUID, "live_status": str, "current_session_id": Optional[UUID], "viewer_count": int}, ...]`
    - 异常：`RoomNotFoundException`（如果有不存在的room_id）

### 5.3. 第三部分：`app/api/v1/endpoints/topic.py`

**职责**：实现所有专题相关的RESTful API接口。

**需实现的端点清单**（严格按照设计文档）：

#### **路由器定义**

**在 topic.py 中定义三个路由器（不使用 prefix）**：
```python
# 主路由器 - 专题管理（包含端点1-7）
router = APIRouter(tags=["Topics"])

# 子路由器 - 分类管理（包含端点8-13）
category_router = APIRouter(tags=["Topic Categories"])

# 子路由器 - 直播间关联（包含端点14-15）
room_router = APIRouter(tags=["Room-Topic Relations"])
```

**在 api.py 中挂载路由器（指定 prefix）**：
```python
from app.api.v1.endpoints import topic

# 1. 主专题路由器
api_router.include_router(
    topic.router,
    prefix="/topics",
    tags=["topics"]
)

# 2. 分类路由器
api_router.include_router(
    topic.category_router,
    prefix="/topic-categories",
    tags=["topic-categories"]
)

# 3. 直播间-专题关系路由器
api_router.include_router(
    topic.room_router,
    prefix="/rooms",
    tags=["room-topic-relations"]
)
```

#### **专题管理端点**（在主路由器 `router` 上）

1. **`@router.post("")` - 创建专题**
   - 装饰器：`@router.post("")`（对应完整路径 `/api/v1/topics`）
   - 请求体：`TopicCreate`
   - 依赖：`current_user`, `db`（**不需要** `request: Request`）
   - 流程：
     1. 提取 `user_id_for_logging = current_user["user_id"]`
     2. 实例化 `service = TopicService(db)`
     3. 调用 `service.create_topic(obj_in, user_id)`
     4. 使用 `format_topic_response(topic)` 格式化响应（banner_url为null，无需拼接）
     5. 返回 `success_response(data=...)`
   - 异常处理：捕获通用异常返回500
   - **注意**：创建时 banner_url 默认为 NULL，无需拼接 base_url

2. **`@router.get("")` - 获取专题列表**
   - 装饰器：`@router.get("")`（对应完整路径 `/api/v1/topics`）
   - 查询参数：`page`, `size`, `status`, `user_id`
   - 依赖：`request: Request`, `db`（**需要** `request` 用于拼接 banner_url）
   - 流程：
     1. 调用 `service.get_topic_list()`
     2. 获取 `base_url = str(request.base_url).rstrip('/')`
     3. 遍历 `items`，对每个专题的 `banner_url`（如不为空）拼接 base_url
     4. 构建分页响应 `{"total": ..., "page": ..., "size": ..., "items": [...]}`
     5. 返回 `success_response(data=paginated_data)`
   - **注意**：需要拼接每个专题的 banner_url

3. **`@router.get("/{topic_id}")` - 获取专题详情**
   - 装饰器：`@router.get("/{topic_id}")`（对应完整路径 `/api/v1/topics/{topic_id}`）
   - 依赖：`request: Request`, `db`（**需要** `request` 用于拼接 banner_url）
   - 流程：
     1. 调用 `service.get_topic_detail(topic_id)`
     2. 获取 `base_url = str(request.base_url).rstrip('/')`
     3. 对专题的 `banner_url`（如不为空）拼接 base_url
     4. 返回层级化数据
   - 异常：`TopicNotFoundException` -> 404
   - **注意**：需要拼接专题的 banner_url

4. **`@router.patch("/{topic_id}")` - 更新专题**
   - 装饰器：`@router.patch("/{topic_id}")`（对应完整路径 `/api/v1/topics/{topic_id}`）
   - 请求体：`TopicUpdate`
   - 依赖：`request: Request`, `current_user`, `db`（**需要** `request` 用于拼接 banner_url）
   - 流程：
     1. 提取 `user_id` 和 `topic_id` 用于日志
     2. 调用 `service.update_topic(topic_id, user_id, obj_in)`
     3. 获取 `base_url = str(request.base_url).rstrip('/')`
     4. 对更新后专题的 `banner_url`（如不为空）拼接 base_url
     5. 返回 `success_response(data=formatted_topic)`
   - 异常：
     - `TopicNotFoundException` -> 404
     - `TopicPermissionDeniedException` -> 403
   - **注意**：需要拼接返回的专题 banner_url

5. **`@router.delete("/{topic_id}")` - 删除专题**
   - 装饰器：`@router.delete("/{topic_id}")`（对应完整路径 `/api/v1/topics/{topic_id}`）
   - 流程：同update
   - 返回：`{"id": "...", "status": "deleted"}`

6. **`@router.post("/{topic_id}/categories")` - 创建分类**
   - 装饰器：`@router.post("/{topic_id}/categories")`（对应完整路径 `/api/v1/topics/{topic_id}/categories`）
   - 请求体：`CategoryCreate`
   - 流程：调用 `service.create_category(topic_id, user_id, obj_in)`

7. **`@router.get("/{topic_id}/categories")` - 获取分类列表**
   - 装饰器：`@router.get("/{topic_id}/categories")`（对应完整路径 `/api/v1/topics/{topic_id}/categories`）
   - 查询参数：`page`, `size`
   - 流程：调用 `service.get_category_list()`

#### **分类管理端点**（在子路由器 `category_router` 上）

8. **`@category_router.patch("/{category_id}")` - 更新分类**
   - 装饰器：`@category_router.patch("/{category_id}")`（对应完整路径 `/api/v1/topic-categories/{category_id}`）
   - 流程：调用 `service.update_category()`

9. **`@category_router.delete("/{category_id}")` - 删除分类**
   - 装饰器：`@category_router.delete("/{category_id}")`（对应完整路径 `/api/v1/topic-categories/{category_id}`）
   - 流程：调用 `service.delete_category()`

10. **`@category_router.post("/{category_id}/rooms")` - 添加直播间**
    - 装饰器：`@category_router.post("/{category_id}/rooms")`（对应完整路径 `/api/v1/topic-categories/{category_id}/rooms`）
    - 请求体：`AddRoomsRequest`
    - 流程：调用 `service.add_rooms_to_category()`
    - 异常：
      - `RoomNotFoundException` -> 400 (code=4001)
      - `RoomAlreadyAssociatedException` -> 400 (code=4001)

11. **`@category_router.get("/{category_id}/rooms")` - 获取直播间列表**
    - 装饰器：`@category_router.get("/{category_id}/rooms")`（对应完整路径 `/api/v1/topic-categories/{category_id}/rooms`）
    - 流程：调用 `service.get_rooms_in_category()`

12. **`@category_router.patch("/{category_id}/rooms/sort-order")` - 更新排序**
    - 装饰器：`@category_router.patch("/{category_id}/rooms/sort-order")`（对应完整路径 `/api/v1/topic-categories/{category_id}/rooms/sort-order`）
    - 请求体：`UpdateRoomSortRequest`
    - 流程：调用 `service.update_room_sort_order()`

13. **`@category_router.delete("/{category_id}/rooms")` - 移除直播间**
    - 装饰器：`@category_router.delete("/{category_id}/rooms")`（对应完整路径 `/api/v1/topic-categories/{category_id}/rooms`）
    - 请求体：`RemoveRoomsRequest`
    - 流程：调用 `service.remove_rooms_from_category()`

#### **辅助查询端点**（在子路由器 `room_router` 上）

14. **`@room_router.get("/{room_id}/topics")` - 获取直播间关联的专题**
    - 装饰器：`@room_router.get("/{room_id}/topics")`（对应完整路径 `/api/v1/rooms/{room_id}/topics`）
    - 流程：调用 `service.get_topics_by_room(room_id)`

15. **`@room_router.post("/batch-status")` - 批量获取直播间状态**
    - 装饰器：`@room_router.post("/batch-status")`（对应完整路径 `/api/v1/rooms/batch-status`）
    - 请求体：`BatchStatusRequest` (包含 `room_ids: List[UUID]`)
    - 查询参数：无
    - 流程：
      1. 提取 `room_ids` 列表
      2. 实例化 `service = TopicService(db)`
      3. 调用 `service.batch_get_room_status(room_ids)`
      4. 返回 `success_response(data=room_status_list)`
    - 异常处理：
      - 参数校验失败（超过100个room_id）-> 400 (code=4001, message="最多支持一次查询100个直播间")
      - `RoomNotFoundException` -> 400 (code=4001, message="部分直播间不存在")

---

**端点路径总结表**：

| 编号 | 装饰器路径 | 最终完整路径 | 说明 |
|-----|-----------|------------|------|
| 1 | `@router.post("")` | `/api/v1/topics` | 创建专题 |
| 2 | `@router.get("")` | `/api/v1/topics` | 获取专题列表 |
| 3 | `@router.get("/{topic_id}")` | `/api/v1/topics/{topic_id}` | 获取专题详情 |
| 4 | `@router.patch("/{topic_id}")` | `/api/v1/topics/{topic_id}` | 更新专题 |
| 5 | `@router.delete("/{topic_id}")` | `/api/v1/topics/{topic_id}` | 删除专题 |
| 6 | `@router.post("/{topic_id}/categories")` | `/api/v1/topics/{topic_id}/categories` | 创建分类 |
| 7 | `@router.get("/{topic_id}/categories")` | `/api/v1/topics/{topic_id}/categories` | 获取分类列表 |
| 8 | `@category_router.patch("/{category_id}")` | `/api/v1/topic-categories/{category_id}` | 更新分类 |
| 9 | `@category_router.delete("/{category_id}")` | `/api/v1/topic-categories/{category_id}` | 删除分类 |
| 10 | `@category_router.post("/{category_id}/rooms")` | `/api/v1/topic-categories/{category_id}/rooms` | 添加直播间 |
| 11 | `@category_router.get("/{category_id}/rooms")` | `/api/v1/topic-categories/{category_id}/rooms` | 获取直播间列表 |
| 12 | `@category_router.patch("/{category_id}/rooms/sort-order")` | `/api/v1/topic-categories/{category_id}/rooms/sort-order` | 更新排序 |
| 13 | `@category_router.delete("/{category_id}/rooms")` | `/api/v1/topic-categories/{category_id}/rooms` | 移除直播间 |
| 14 | `@room_router.get("/{room_id}/topics")` | `/api/v1/rooms/{room_id}/topics` | 获取直播间的专题 |
| 15 | `@room_router.post("/batch-status")` | `/api/v1/rooms/batch-status` | 批量获取直播间状态 |

**关键理解**：
- 路由器定义时**不包含 prefix**，只有 tags
- 在 `api.py` 中挂载时才指定 prefix
- 装饰器路径是相对于路由器的路径
- 最终完整路径 = `/api/v1` + prefix + 装饰器路径

### 5.4. 响应数据格式化要求

#### **关键：base_url 拼接规范**

**原则**：
- **数据库存储相对路径**（如 `/media/topics/{topic_id}/banner_xxx.png`）
- **API 返回完整 URL**（如 `http://domain.com/media/topics/{topic_id}/banner_xxx.png`）
- **拼接时机**：在 Endpoint 层返回数据前拼接

#### **标准拼接逻辑**

在需要拼接 banner_url 的端点中，使用以下标准逻辑：

```python
# 1. 获取 base_url
base_url = str(request.base_url)
if base_url.endswith('/'):
    base_url = base_url[:-1]

# 2. 拼接 banner_url（如果不为空）
if banner_url:
    # 检查是否已经是完整 URL
    if not (banner_url.startswith("http://") or banner_url.startswith("https://")):
        # 确保相对路径以 / 开头
        relative_url = banner_url if banner_url.startswith('/') else f'/{banner_url}'
        # 拼接完整 URL
        full_banner_url = f"{base_url}{relative_url}"
    else:
        # 已经是完整 URL，直接使用
        full_banner_url = banner_url
```

#### **format_topic_response 辅助函数**

定义一个**不带** base_url 参数的格式化函数，仅负责 ORM 对象到字典的转换：

```python
def format_topic_response(topic: Topic) -> dict:
    """
    格式化专题响应数据（不拼接 base_url）
    
    Args:
        topic: Topic ORM 对象
    
    Returns:
        dict: 格式化后的专题数据字典（banner_url 保持原始值）
    """
    return {
        "id": str(topic.id),
        "user_id": str(topic.user_id),
        "title": topic.title,
        "description": topic.description,
        "banner_url": topic.banner_url,  # 保持原始相对路径或 null
        "status": topic.status.value if hasattr(topic.status, 'value') else str(topic.status),
        "created_at": topic.created_at.isoformat() + "Z",
        "updated_at": topic.updated_at.isoformat() + "Z"
    }
```

#### **在 Endpoint 层使用的完整示例**

**示例1：获取专题列表（需要拼接）**

```python
@router.get("")
async def get_topic_list(
    request: Request,  # ← 注入 Request
    page: int = Query(default=1, ge=1),
    size: int = Query(default=10, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    service = TopicService(db)
    topics, total = await service.get_topic_list(page=page, size=size)
    
    # 获取 base_url
    base_url = str(request.base_url).rstrip('/')
    
    # 格式化并拼接每个专题的 banner_url
    items = []
    for topic in topics:
        topic_data = format_topic_response(topic)
        # 拼接 banner_url
        if topic_data["banner_url"]:
            banner_url = topic_data["banner_url"]
            if not (banner_url.startswith("http://") or banner_url.startswith("https://")):
                relative_url = banner_url if banner_url.startswith('/') else f'/{banner_url}'
                topic_data["banner_url"] = f"{base_url}{relative_url}"
        items.append(topic_data)
    
    # 构建分页响应
    paginated_data = {
        "total": total,
        "page": page,
        "size": size,
        "items": items
    }
    
    return success_response(data=paginated_data)
```

**示例2：更新专题（需要拼接）**

```python
@router.patch("/{topic_id}")
async def update_topic(
    request: Request,  # ← 注入 Request
    topic_id: uuid.UUID,
    topic_update: TopicUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = TopicService(db)
    updated_topic = await service.update_topic(
        topic_id=topic_id,
        user_id=uuid.UUID(current_user["user_id"]),
        obj_in=topic_update
    )
    
    # 获取 base_url
    base_url = str(request.base_url).rstrip('/')
    
    # 格式化响应
    topic_data = format_topic_response(updated_topic)
    
    # 拼接 banner_url（如果不为空）
    if topic_data["banner_url"]:
        banner_url = topic_data["banner_url"]
        if not (banner_url.startswith("http://") or banner_url.startswith("https://")):
            relative_url = banner_url if banner_url.startswith('/') else f'/{banner_url}'
            topic_data["banner_url"] = f"{base_url}{relative_url}"
    
    return success_response(data=topic_data)
```

**示例3：创建专题（不需要拼接）**

```python
@router.post("")
async def create_topic(
    topic_create: TopicCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
    # ← 注意：不需要 request 参数
):
    service = TopicService(db)
    topic = await service.create_topic(
        obj_in=topic_create,
        user_id=uuid.UUID(current_user["user_id"])
    )
    
    # 直接返回，banner_url 为 null，无需拼接
    return success_response(data=format_topic_response(topic))
```

#### **需要拼接 banner_url 的接口清单**

| 接口 | Request 参数 | 需要拼接 | 说明 |
|-----|-------------|---------|------|
| `POST /topics` (创建) | ❌ 不需要 | ❌ 不需要 | banner_url 为 NULL |
| `GET /topics` (列表) | ✅ 需要 | ✅ 需要 | 遍历拼接每个专题 |
| `GET /topics/{id}` (详情) | ✅ 需要 | ✅ 需要 | 拼接专题 banner_url |
| `PATCH /topics/{id}` (更新) | ✅ 需要 | ✅ 需要 | 拼接更新后的 banner_url |
| `POST /topics/{id}/banner` (上传) | ✅ 需要 | ✅ 需要 | 拼接上传后的 banner_url |

### 5.5. 日志记录要求

**Service层日志**：
```python
logger.info(f"创建专题成功: user_id={user_id}, topic_id={topic.id}, title={topic.title}")
logger.warning(f"删除专题: user_id={user_id}, topic_id={topic_id}, categories_count={len(topic.categories)}")
logger.error(f"权限验证失败: user_id={user_id}, topic_id={topic_id}, action=update")
```

**Endpoint层日志**：
```python
logger.info(f"API调用: POST /topics, user_id={user_id}")
logger.warning(f"专题不存在: topic_id={topic_id}")
logger.error(f"未知异常: endpoint=update_topic, error={str(e)}")
```

## 6. 最终交付 (Final Deliverable)

请根据以上所有要求，为我生成以下三个文件的完整、可直接使用的 Python 代码：

1. **`app/exceptions.py`**（补充专题相关异常）
2. **`app/services/topic_service.py`**（完整Service层）
3. **`app/api/v1/endpoints/topic.py`**（完整Endpoint层）

**代码应包含**：
- 完整的模块文档字符串
- 所有必要的导入语句
- 上述列出的所有方法/端点
- 完整的类型注解
- 详细的函数文档字符串
- **严格遵循安全异步异常处理原则**（主动变量提取）
- 适当的日志记录
- 完善的异常处理和HTTP响应转换

**代码格式要求**：
- 每个文件放在独立的代码块中，并明确标注文件路径
- 使用清晰的注释说明关键逻辑
- 确保所有函数签名与上述规格完全一致
- 所有端点必须包含完整的 `try...except` 块

---

## 附录：快速检查清单

生成代码后，请确认以下内容：

### 数据库层面
- [x] 所有数据库操作使用 `async/await`
- [x] 主键UUID在应用层生成
- [x] 使用 `selectinload` 避免N+1查询

### API层面
- [x] 所有端点需要JWT Token认证（`Depends(get_current_user)`）
- [x] 使用统一响应结构（`success_response` / `error_response`）
- [x] 分页接口使用标准格式（`total`, `page`, `size`, `items`）
- [x] HTTP状态码和业务状态码正确对应

### 代码层面
- [x] 类名使用大驼峰（`TopicService`）
- [x] 函数名使用下划线（`create_topic`）
- [x] 权限验证在Service层进行
- [x] **在所有 `try...except` 块中主动提取变量**
- [x] **禁止在 `except` 块中访问ORM对象属性**
- [x] 异常使用自定义异常类
- [x] 日志记录符合规范

### RESTful规范
- [x] URL路径不以斜杠结尾
- [x] 集合端点使用 `path="/"`
- [x] 使用合适的HTTP方法（GET、POST、PATCH、DELETE）

---

**现在，请开始生成代码！**

