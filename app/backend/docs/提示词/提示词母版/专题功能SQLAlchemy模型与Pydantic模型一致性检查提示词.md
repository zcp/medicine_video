# 专题功能 SQLAlchemy 模型与 Pydantic Schema 一致性检查提示词

---

## **AI 提示词：用于审查专题功能 Model 与 Schema 逻辑一致性**

### **1. 角色定义 (Role Definition)**

你是一名资深的 FastAPI 后端架构师，专注于 API 设计和数据模型的最佳实践。你的任务是审查专题聚合功能的 SQLAlchemy 模型（`topic.py`）和 Pydantic Schema（`schemas/topic.py`）之间的一致性、安全性和功能适配性。

**核心职责**:
- 验证数据模型的完整性和一致性
- 识别潜在的安全风险和数据泄露问题
- 确保 API 设计符合 RESTful 最佳实践
- 检查数据验证规则的完备性

---

### **2. 任务目标 (Task Objective)**

你的目标**不是**检查两个文件是否逐字相同，而是要：

1. ✅ **验证 Pydantic Schemas 是否是 SQLAlchemy Models 合理且安全的"API 视图"**
   - Schema 是否正确映射了 Model 的字段？
   - 是否有遗漏或多余的字段？

2. ✅ **确保数据在"外部世界"（API）和"内部世界"（数据库）之间能够安全、高效地转换**
   - 类型转换是否正确？
   - 时间戳、UUID 等特殊类型是否正确映射？

3. ✅ **找出任何可能导致数据泄露、验证错误或 API 使用不便的设计缺陷**
   - 是否暴露了敏感字段？
   - 验证规则是否足够严格？
   - API 设计是否符合业务需求？

---

### **3. 核心输入 (Core Input)**

#### **3.1. SQLAlchemy 模型代码**

**文件路径**: `live_core_service/app/models/topic.py`

**【请在此处粘贴完整的 `app/models/topic.py` 代码】**

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

---
```
#### **3.2. Pydantic Schema 代码**

**文件路径**: `live_core_service/app/schemas/topic.py`

**【请在此处粘贴完整的 `app/schemas/topic.py` 代码】**
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

---

## ✅ **4. 审查清单（基础逻辑）**

请根据以下维度对比专题功能的 Model 与 Schema 设计是否一致、合理：

### **4.1 字段命名一致性**

**检查项**:
- [ ] `Topic` 模型的字段名称是否与 `Topic*` Schema 中的字段名称完全一致？
- [ ] `TopicCategory` 模型的字段名称是否与 `Category*` Schema 中的字段名称完全一致？
- [ ] `TopicCategoryRoom` 模型的字段名称是否与 `RoomAssociation` 相关 Schema 中的字段名称完全一致？
- [ ] 是否存在拼写差异或语义偏移（如 `banner_url` vs `bannerURL`）？

**重点字段检查**:
| Model 字段 | Schema 字段 | 是否一致 |
|-----------|-----------|---------|
| `Topic.title` | `TopicBase.title` | ? |
| `Topic.description` | `TopicBase.description` | ? |
| `Topic.banner_url` | `TopicBase.banner_url` | ? |
| `Topic.status` | `TopicBase.status` | ? |
| `TopicCategory.name` | `CategoryBase.name` | ? |
| `TopicCategory.sort_order` | `CategoryBase.sort_order` | ? |
| `TopicCategoryRoom.room_id` | `RoomAssociation.room_id` | ? |
| `TopicCategoryRoom.sort_order` | `RoomAssociation.sort_order` | ? |

---

### **4.2 数据类型兼容性**

**检查项**:
- [ ] `UUID` 类型字段是否在 Schema 中映射为 `uuid.UUID`？
- [ ] `String(n)` 类型字段是否在 Schema 中映射为 `str`，并使用 `Field(max_length=n)` 限制？
- [ ] `Text` 类型字段是否在 Schema 中映射为 `str`（不限长度）？
- [ ] `Integer` 类型字段是否在 Schema 中映射为 `int`？
- [ ] `TIMESTAMP(timezone=True)` 类型字段是否在 Schema 中映射为 `datetime`？
- [ ] `Enum` 类型字段是否在 Schema 中使用对应的 Pydantic `Enum`？

**类型映射表**:
| SQLAlchemy 类型 | Pydantic 类型 | 验证规则 | 是否正确映射 |
|----------------|--------------|---------|------------|
| `UUID(as_uuid=True)` | `uuid.UUID` | - | ? |
| `String(100)` | `str` | `Field(max_length=100)` | ? |
| `String(50)` | `str` | `Field(max_length=50)` | ? |
| `String(255)` | `str` | `Field(max_length=255)` | ? |
| `Text` | `str` | 无长度限制 | ? |
| `Integer` | `int` | - | ? |
| `TIMESTAMP(timezone=True)` | `datetime` | - | ? |
| `SAEnum(TopicStatus)` | `TopicStatus` (Pydantic Enum) | 枚举值验证 | ? |

---

### **4.3 Create Schema 审查**

**检查项**:
- [ ] `TopicCreate` 是否包含创建专题所需的所有必填字段（`title`, `status`）？
- [ ] `TopicCreate` 是否**正确排除**了系统生成字段（`id`, `user_id`, `created_at`, `updated_at`）？
- [ ] `CategoryCreate` 是否包含创建分类所需的所有必填字段（`name`, `sort_order`）？
- [ ] `CategoryCreate` 是否**正确排除**了外键字段（`topic_id`，从路径参数获取）？
- [ ] `RoomAssociation` 是否包含关联直播间所需的字段（`room_id`, `sort_order`）？

**关键问题**:
1. **`TopicCreate` 中是否错误地包含了 `id` 字段？**
   - ❌ 错误：`id` 应由数据库或应用层生成
   - ✅ 正确：`TopicCreate` 不包含 `id`

2. **`TopicCreate` 中是否错误地包含了 `user_id` 字段？**
   - ❌ 错误：`user_id` 应从 JWT Token 提取
   - ✅ 正确：`TopicCreate` 不包含 `user_id`，由认证中间件提供

3. **`CategoryCreate` 中是否错误地包含了 `topic_id` 字段？**
   - ❌ 错误：`topic_id` 应从路径参数 `/topics/{topic_id}/categories` 获取
   - ✅ 正确：`CategoryCreate` 不包含 `topic_id`

---

### **4.4 Update Schema 审查**

**检查项**:
- [ ] `TopicUpdate` 中的所有字段是否都定义为 `Optional[...]`？
- [ ] `TopicUpdate` 是否遗漏了常用更新字段（`title`, `description`, `banner_url`, `status`）？
- [ ] `CategoryUpdate` 中的所有字段是否都定义为 `Optional[...]`？
- [ ] `CategoryUpdate` 是否遗漏了常用更新字段（`name`, `sort_order`）？
- [ ] `Update` Schema 是否**正确排除**了不可更新字段（`id`, `user_id`, `created_at`, `updated_at`）？

**PATCH 语义验证**:
- [ ] 所有 `Update` Schema 是否支持部分更新（所有字段可选）？
- [ ] 字段验证规则是否与 `Create` Schema 一致（如长度限制、范围限制）？

---

### **4.5 Response Schema 审查**

#### **4.5.1 安全审计**

**检查项**:
- [ ] `TopicResponse` 是否暴露了 `user_id`？
  - ⚠️ **注意**: `user_id` 是否应该暴露给前端？
  - 如果不应该暴露，应从 `TopicResponse` 中移除
  
- [ ] `CategoryResponse` 是否暴露了内部关联字段（如数据库内部 ID）？

- [ ] 是否有其他敏感字段不应暴露但出现在响应中？
  - 例如：内部状态标记、系统配置、调试信息等

**安全清单**:
| 字段 | 是否暴露 | 是否合理 | 建议 |
|------|---------|---------|------|
| `Topic.user_id` | ✅ 是 | ? | 如果专题是公开的，可以暴露创建者ID；否则应移除 |
| `Topic.created_at` | ✅ 是 | ✅ 合理 | 时间戳信息通常可以暴露 |
| `TopicCategory.topic_id` | ✅ 是 | ✅ 合理 | 外键关系对前端有用 |

#### **4.5.2 结构审计**

**检查项**:
- [ ] `TopicResponse` 是否包含所有必要字段（`id`, `title`, `description`, `banner_url`, `status`, `user_id`, `created_at`, `updated_at`）？
- [ ] `CategoryResponse` 是否包含所有必要字段（`id`, `topic_id`, `name`, `sort_order`, `created_at`, `updated_at`）？
- [ ] `TopicDetailResponse` 是否正确嵌套了 `categories` 字段？
- [ ] `CategoryWithRooms` 是否正确嵌套了 `rooms` 字段？

**嵌套层级检查**:
- [ ] `TopicDetailResponse` → `CategoryWithRooms` → `RoomInCategory` 的嵌套层级是否合理（3层）？
- [ ] 是否存在潜在的循环依赖（如 `Topic` → `Category` → `Topic`）？
  - ❌ **不合理**: 嵌套层级过深（> 3 层）
  - ✅ **合理**: 3 层嵌套，无循环依赖

**`from_attributes` 配置检查**:
- [ ] 所有 `Response` Schema 是否设置了 `model_config = ConfigDict(from_attributes=True)`？
- [ ] `RoomInCategory` 是否设置了 `from_attributes=True`（用于 ORM 对象转换）？
- [ ] `CategoryWithRooms` 是否设置了 `from_attributes=True`？

---

## 🔒 **5. 安全与设计一致性增强项**

请额外检查以下安全与架构细节：

### **5.1 默认值一致性**

**检查项**:
- [ ] `Topic.status` 在 Model 中的默认值（`TopicStatus.DRAFT`）是否与 Schema 中一致？
- [ ] `TopicCategory.sort_order` 在 Model 中的默认值（`0`）是否与 Schema 中一致？
- [ ] `TopicCategoryRoom.sort_order` 在 Model 中的默认值（`0`）是否与 Schema 中一致？

**默认值对比表**:
| Model 字段 | Model 默认值 | Schema 默认值 | 是否一致 |
|-----------|------------|--------------|---------|
| `Topic.status` | `TopicStatus.DRAFT` | `TopicStatus.DRAFT` | ? |
| `TopicCategory.sort_order` | `0` | `0` | ? |
| `TopicCategoryRoom.sort_order` | `0` | `0` | ? |
| `RoomInCategory.heat` | - | `0` | ? |

---

### **5.2 枚举类型一致性**

**检查项**:
- [ ] SQLAlchemy 模型中的 `TopicStatus` 枚举值是否与 Pydantic Schema 中的 `TopicStatus` 枚举值完全一致？
- [ ] 枚举值的顺序和命名是否一致？

**枚举值对比**:
| 枚举值 | Model 定义 | Schema 定义 | 是否一致 |
|-------|-----------|------------|---------|
| `DRAFT` | `"draft"` | `"draft"` | ? |
| `PUBLISHED` | `"published"` | `"published"` | ? |
| `ARCHIVED` | `"archived"` | `"archived"` | ? |

---

### **5.3 字段约束映射**

**检查项**:
- [ ] Model 中 `nullable=False` 的字段是否在 Schema 中标记为必填（`...` 而非 `Optional`）？
- [ ] Model 中 `nullable=True` 的字段是否在 Schema 中标记为可选（`Optional`）？
- [ ] Model 中的字符串长度限制（`String(n)`）是否在 Schema 中通过 `Field(max_length=n)` 体现？
- [ ] Model 中的唯一性约束是否在业务逻辑或验证器中体现？

**约束映射表**:
| Model 字段 | Model 约束 | Schema 验证规则 | 是否正确映射 |
|-----------|-----------|----------------|------------|
| `Topic.title` | `nullable=False, String(100)` | `Field(..., min_length=1, max_length=100)` | ? |
| `Topic.description` | `nullable=True, Text` | `Optional[str]` | ? |
| `Topic.banner_url` | `nullable=True, String(255)` | `Optional[str], Field(max_length=255)` | ? |
| `TopicCategory.name` | `nullable=False, String(50)` | `Field(..., min_length=1, max_length=50)` | ? |
| `TopicCategory.sort_order` | `nullable=False, Integer, default=0` | `Field(default=0, ge=0)` | ? |

---

### **5.4 结构冗余或字段歧义**

**检查项**:
- [ ] 是否存在字段在多个 Schema 中冗余定义（应使用继承）？
- [ ] `TopicBase` 和 `CategoryBase` 是否被正确继承？
- [ ] 是否存在结构重复、命名歧义或字段冲突？
- [ ] `RoomAssociation` 中的 `sort_order` 是否与 `TopicCategoryRoom.sort_order` 对应？

**继承结构检查**:
```
TopicBase (基础字段)
    ├── TopicCreate (继承 TopicBase)
    ├── TopicInDB (继承 TopicBase, 添加系统字段)
    └── TopicResponse (继承 TopicInDB)
        └── TopicDetailResponse (继承 TopicResponse, 添加嵌套字段)
```

---

## 🧩 **6. 嵌套结构与复合 Schema 审查**

### **6.1 嵌套 Schema 合理性**

**检查项**:
- [ ] `TopicDetailResponse` 嵌套 `CategoryWithRooms` 是否合理？
- [ ] `CategoryWithRooms` 嵌套 `RoomInCategory` 是否合理？
- [ ] 是否使用 `default_factory=list` 明确初始化避免 `null` 值？
- [ ] 嵌套层级是否超过 3 层（可能导致性能问题）？

**嵌套结构验证**:
```
TopicDetailResponse
├── id, user_id, title, description, banner_url, status
├── created_at, updated_at
└── categories: List[CategoryWithRooms]
    ├── id, name, sort_order
    └── rooms: List[RoomInCategory]
        ├── id, title, cover_url
        ├── live_status, start_time
        └── heat
```

**检查要点**:
- [ ] 每个嵌套列表是否使用 `default_factory=list`？
- [ ] 嵌套对象是否都设置了 `from_attributes=True`？
- [ ] 嵌套层级是否清晰且易于理解？

---

### **6.2 复合对象字段控制**

**检查项**:
- [ ] `AddRoomsRequest.rooms` 是否限制了列表长度（`min_length=1, max_length=50`）？
- [ ] `UpdateRoomSortRequest.rooms` 是否限制了列表长度（`min_length=1, max_length=100`）？
- [ ] `RemoveRoomsRequest.room_ids` 是否限制了列表长度（`min_length=1, max_length=50`）？
- [ ] `BatchStatusRequest.room_ids` 是否限制了列表长度（`min_length=1, max_length=100`）？

**性能隐患检查**:
- [ ] 是否存在无限制的列表字段（可能导致大查询）？
- [ ] 是否存在递归列表或嵌套嵌套（可能导致性能问题）？
- [ ] `TopicDetailResponse` 返回所有分类和直播间是否合理（是否需要分页）？

**建议**:
- ✅ 为所有列表字段设置合理的 `max_length`
- ✅ 对于大量数据，使用分页机制
- ✅ 避免在单个接口返回过多嵌套数据

---

## 🧰 **7. Schema 继承与通用结构审查（高级）**

### **7.1 继承结构审查**

**检查项**:
- [ ] `TopicCreate` 是否继承自 `TopicBase`？
- [ ] `TopicInDB` 是否继承自 `TopicBase`？
- [ ] `TopicResponse` 是否继承自 `TopicInDB`？
- [ ] `TopicDetailResponse` 是否继承自 `TopicInDB` 或 `TopicResponse`？
- [ ] 继承关系是否清晰且符合逻辑？

**继承链验证**:
```
Topic 继承链:
TopicBase → TopicCreate
TopicBase → TopicInDB → TopicResponse → TopicDetailResponse

Category 继承链:
CategoryBase → CategoryCreate
CategoryBase → CategoryInDB → CategoryResponse
```

---

### **7.2 ORM 映射配置审查**

**检查项**:
- [ ] 所有 `*InDB` Schema 是否设置了 `model_config = ConfigDict(from_attributes=True)`？
- [ ] 所有 `*Response` Schema 是否继承了正确的 `*InDB` Schema（自动获得 ORM 映射配置）？
- [ ] 嵌套 Schema（`RoomInCategory`, `CategoryWithRooms`）是否也设置了 `from_attributes=True`？

**配置清单**:
| Schema | 是否设置 `from_attributes=True` | 是否合理 |
|--------|-------------------------------|---------|
| `TopicInDB` | ? | 必须设置 |
| `TopicResponse` | ? | 继承自 `TopicInDB`，自动获得 |
| `TopicDetailResponse` | ? | 继承自 `TopicInDB`，自动获得 |
| `CategoryInDB` | ? | 必须设置 |
| `CategoryResponse` | ? | 继承自 `CategoryInDB`，自动获得 |
| `RoomInCategory` | ? | 必须设置（用于 ORM 转换） |
| `CategoryWithRooms` | ? | 必须设置（用于 ORM 转换） |

---

### **7.3 字段注释与文档字符串审查**

**检查项**:
- [ ] 所有 Schema 类是否包含中文文档字符串？
- [ ] 关键字段是否包含 `description` 参数？
- [ ] 字段注释是否与 ORM 定义同步（便于自动文档生成）？
- [ ] 枚举值是否有注释说明？

**文档质量检查**:
- [ ] 每个 Schema 类的文档字符串是否说明了其用途？
- [ ] 每个字段的 `description` 是否清晰描述了字段含义？
- [ ] 复杂字段（如 `heat`）是否说明了计算逻辑？

---

## 🔍 **8. 特殊功能审查**

### **8.1 自定义验证器审查**

**检查项**:
- [ ] `AddRoomsRequest` 是否实现了 `validate_unique_room_ids` 验证器？
- [ ] 验证器是否使用了 `@field_validator` 装饰器？
- [ ] 验证器是否使用了 `@classmethod` 装饰器？
- [ ] 验证器逻辑是否正确（检查 `room_id` 唯一性）？
- [ ] 验证器错误信息是否清晰（`"room_id 不能重复"`）？

**验证器实现检查**:
```python
@field_validator('rooms')
@classmethod
def validate_unique_room_ids(cls, v):
    room_ids = [r.room_id for r in v]
    if len(room_ids) != len(set(room_ids)):
        raise ValueError("room_id 不能重复")
    return v
```

**问题清单**:
- [ ] 是否正确提取了 `room_id` 列表？
- [ ] 是否使用 `set()` 去重检查？
- [ ] 是否抛出了合适的异常（`ValueError`）？
- [ ] 是否返回了验证后的值？

---

### **8.2 业务逻辑字段审查**

**检查项**:
- [ ] `RoomInCategory.heat` 字段是否是计算字段？
- [ ] `heat` 的计算逻辑是否在文档中说明？
- [ ] `live_status` 字段是否从相关的 `LiveSession` 获取？
- [ ] `start_time` 字段是否从最新的 `LiveSession` 获取？

**计算字段验证**:
| 字段 | 来源 | 计算逻辑 | 是否说明 |
|------|------|---------|---------|
| `RoomInCategory.heat` | `SessionStatistics` | `total_viewer_count * 0.5 + total_like_count * 0.3 + peak_viewer_count * 0.2` | ? |
| `RoomInCategory.live_status` | `LiveSession.status` | 最新场次状态 | ? |
| `RoomInCategory.start_time` | `LiveSession.start_time` | 最新场次开始时间 | ? |

---

### **8.3 特殊约束审查**

**检查项**:
- [ ] Model 中的 `UniqueConstraint('category_id', 'room_id')` 约束是否在业务逻辑中体现？
- [ ] Model 中的 `UniqueConstraint('topic_id', 'name')` 约束是否在业务逻辑中体现？
- [ ] 是否有相应的错误处理逻辑（如捕获 `IntegrityError`）？

---

## 📊 **9. 最终交付 (Final Deliverable)**

生成一份简明的审查报告，指出你发现的任何**逻辑不一致**、**安全风险**或**不符合最佳实践**的地方，并提供具体的修改建议。

### **9.1 报告结构**

```markdown
# 专题功能 Model 与 Schema 一致性审查报告

## 1. 总体评估
- 一致性评分: ?/100
- 发现问题数量: ?
  - 严重问题: ?
  - 中等问题: ?
  - 轻微问题: ?

## 2. 字段命名一致性
- [✅/❌] 检查结果
- 问题清单: ...
- 修改建议: ...

## 3. 数据类型兼容性
- [✅/❌] 检查结果
- 问题清单: ...
- 修改建议: ...

## 4. Create Schema 审查
- [✅/❌] 检查结果
- 问题清单: ...
- 修改建议: ...

## 5. Update Schema 审查
- [✅/❌] 检查结果
- 问题清单: ...
- 修改建议: ...

## 6. Response Schema 审查
### 6.1 安全审计
- [✅/❌] 检查结果
- 问题清单: ...
- 修改建议: ...

### 6.2 结构审计
- [✅/❌] 检查结果
- 问题清单: ...
- 修改建议: ...

## 7. 默认值一致性
- [✅/❌] 检查结果
- 问题清单: ...
- 修改建议: ...

## 8. 枚举类型一致性
- [✅/❌] 检查结果
- 问题清单: ...
- 修改建议: ...

## 9. 字段约束映射
- [✅/❌] 检查结果
- 问题清单: ...
- 修改建议: ...

## 10. 嵌套结构审查
- [✅/❌] 检查结果
- 问题清单: ...
- 修改建议: ...

## 11. 自定义验证器审查
- [✅/❌] 检查结果
- 问题清单: ...
- 修改建议: ...

## 12. 总体建议
- 优先修复项: ...
- 可选优化项: ...
- 架构改进建议: ...
```

---

## 🎯 **10. 审查重点总结**

### **10.1 必须检查的项目（P0 优先级）**

1. ✅ 字段名称完全一致
2. ✅ 数据类型正确映射
3. ✅ `Create` Schema 不包含系统生成字段
4. ✅ `Update` Schema 所有字段可选
5. ✅ `Response` Schema 设置了 `from_attributes=True`
6. ✅ 枚举值完全一致
7. ✅ 必填字段约束正确映射

### **10.2 重要检查的项目（P1 优先级）**

1. ✅ 默认值一致性
2. ✅ 字段长度限制正确映射
3. ✅ 嵌套 Schema 使用 `default_factory=list`
4. ✅ 列表字段限制了最大长度
5. ✅ 自定义验证器逻辑正确

### **10.3 建议检查的项目（P2 优先级）**

1. ✅ 敏感字段是否应暴露
2. ✅ 嵌套层级是否合理
3. ✅ 字段注释和文档字符串完整
4. ✅ 继承结构清晰
5. ✅ 性能隐患（如无限制列表）

---

**文档版本**: V1.0  
**创建日期**: 2025-10-16  
**适用于**: 专题聚合功能 SQLAlchemy 模型与 Pydantic Schema 一致性检查  
**基于文档**: `live_core_service/app/models/topic.py` + `live_core_service/app/schemas/topic.py`  
**参考模板**: `直播核心功能服务SQLAIchemym模型和Pyantic模型的一致性检查提示词.md`

