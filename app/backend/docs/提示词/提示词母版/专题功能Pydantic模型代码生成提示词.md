# 专题功能 Pydantic Schema 代码生成提示词

---

## **高效 AI 代码生成提示词：专题功能 Pydantic 模型**

### **1. 角色定义 (Role Definition)**

你是一名精通 FastAPI 和 Pydantic 的资深 Python 后端工程师。你的任务是根据已存在的 SQLAlchemy ORM 模型（`topic.py`），为 `LiveCore Service` 的专题聚合功能生成结构清晰、类型精确且符合最佳实践的 **Pydantic Schema 模型**。

**🔥 关键要求**:
- 生成的 Pydantic 模型必须与 SQLAlchemy 模型**完全对应**
- 严格遵循项目现有的 Schema 设计模式
- 确保类型安全和数据验证的完整性

---

### **2. 任务目标 (Task Objective)**

你的目标是生成以下 Python 文件的完整代码：

**文件路径**: `live_core_service/app/schemas/topic.py`

该文件将包含专题聚合功能所需的所有 Pydantic Schema 模型，用于：
- API 请求数据验证（Create, Update）
- API 响应数据序列化（Response）
- 数据传输对象（DTO）的类型安全

---

### **3. 核心上下文信息 (Core Context Information)**

#### **3.1. 技术栈 (Technology Stack)**

- **框架**: FastAPI
- **ORM**: SQLAlchemy 2.0 (异步模式, 使用 `AsyncSession`)
- **数据库**: PostgreSQL
- **数据模型**: Pydantic v2
- **Python 版本**: 3.9+

#### **3.2. 项目文件结构 (Project File Structure)**

```
live_core_service/
├── app/
│   ├── __init__.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── live_core.py          # 现有模型
│   │   └── topic.py               # 专题功能 SQLAlchemy 模型（已存在）
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── live_core.py           # 现有 Schema
│   │   └── topic.py               # <-- 这是你要生成的目标文件
│   └── ...
```

#### **3.3. SQLAlchemy 模型参考 (Existing SQLAlchemy Models)**

**文件**: `live_core_service/app/models/topic.py`

生成的 Pydantic Schema 必须与以下 SQLAlchemy 模型**完全对应**：

```python
"""
专题聚合功能的数据库模型
"""
import uuid
from datetime import datetime
import enum

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
    """
    __tablename__ = "topics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, comment='创建者用户ID')
    title = Column(String(100), nullable=False, comment='专题标题')
    description = Column(Text, nullable=True, comment='专题描述')
    banner_url = Column(String(255), nullable=True, comment='横幅图URL')
    status = Column(SAEnum(TopicStatus, values_callable=lambda obj: [e.value for e in obj]), 
                   nullable=False, default=TopicStatus.DRAFT)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
    # 关联关系
    categories = relationship("TopicCategory", back_populates="topic", cascade="all, delete-orphan")


class TopicCategory(Base):
    """
    专题内分类表
    """
    __tablename__ = "topic_categories"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    topic_id = Column(UUID(as_uuid=True), ForeignKey("topics.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(50), nullable=False, comment='分类名称')
    sort_order = Column(Integer, default=0, nullable=False, comment='排序顺序')
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
    # 关联关系
    topic = relationship("Topic", back_populates="categories")
    rooms = relationship("TopicCategoryRoom", back_populates="category", cascade="all, delete-orphan")


class TopicCategoryRoom(Base):
    """
    专题分类与直播间的关联表
    """
    __tablename__ = "topic_category_rooms"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    category_id = Column(UUID(as_uuid=True), ForeignKey("topic_categories.id", ondelete="CASCADE"), nullable=False)
    room_id = Column(UUID(as_uuid=True), ForeignKey("live_rooms.id", ondelete="CASCADE"), nullable=False)
    sort_order = Column(Integer, default=0, nullable=False, comment='排序顺序')
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
    # 关联关系
    category = relationship("TopicCategory", back_populates="rooms")
    room = relationship("LiveRoom")
```

---

### **4. 代码生成具体要求 (Specific Code Generation Requirements)**

#### **4.1. 通用规范**

- **代码风格**: 严格遵循 PEP 8 规范
- **Pydantic 版本**: 使用 Pydantic v2 语法（`model_config = ConfigDict(from_attributes=True)`）
- **类型注解**: 所有字段必须有完整的类型注解
- **文档字符串**: 每个 Schema 类添加中文文档字符串说明用途

#### **4.2. 导入语句要求**

必须包含以下导入：

```python
from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional, List
from datetime import datetime
import uuid
from enum import Enum
```

#### **4.3. 枚举类型定义**

##### **4.3.1. TopicStatus 枚举**

- 必须定义 Pydantic 兼容的 `TopicStatus` 枚举
- 枚举值必须与 SQLAlchemy 模型中的枚举值**完全一致**
- 继承 `str, Enum` 以确保 JSON 序列化正确

**示例格式**:
```python
class TopicStatus(str, Enum):
    """专题状态枚举"""
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"
```

---

#### **4.4. Pydantic Schema 模型设计模式**

为每个 SQLAlchemy 模型创建**完整的 Schema 套件**，包括：

##### **4.4.1. Schema 套件结构**

每个数据库模型应包含以下 Pydantic Schema：

1. **`...Base`** - 基础 Schema（包含通用字段）
2. **`...Create`** - 创建请求 Schema
3. **`...Update`** - 更新请求 Schema（所有字段可选）
4. **`...InDB`** - 数据库完整记录 Schema
5. **`...Response`** - API 响应 Schema
6. **（可选）扩展 Schema** - 用于特殊场景（如聚合页面）

##### **4.4.2. 字段映射规则**

| SQLAlchemy 类型 | Pydantic 类型 | 说明 |
|----------------|--------------|------|
| `UUID` | `uuid.UUID` | 使用 Python 标准库的 UUID |
| `String(n)` | `str` | 使用 `Field(max_length=n)` 限制长度 |
| `Text` | `str` | 不限制长度 |
| `Integer` | `int` | 整数类型 |
| `TIMESTAMP(timezone=True)` | `datetime` | 使用 `datetime.datetime` |
| `Boolean` | `bool` | 布尔类型 |
| `Enum` | 对应的 Pydantic `Enum` | 必须定义对应的枚举类 |

##### **4.4.3. 必需字段 vs 可选字段**

- **Create Schema**: 
  - 不包含 `id`, `created_at`, `updated_at`（由系统生成）
  - 不包含外键的 `_id` 字段（通过路径参数传递）
  - 标记必需字段为非可选，可选字段为 `Optional`
  
- **Update Schema**: 
  - 所有业务字段都是 `Optional`
  - 不包含 `id`, `created_at`, `updated_at`
  
- **Response Schema**: 
  - 包含所有字段（包括 `id`, `created_at`, `updated_at`）
  - 设置 `model_config = ConfigDict(from_attributes=True)`

---

#### **4.5. Topic 相关 Schema 详细要求**

##### **4.5.1. TopicBase**

```python
class TopicBase(BaseModel):
    """专题基础 Schema"""
    title: str = Field(..., min_length=1, max_length=100, description="专题标题")
    description: Optional[str] = Field(None, description="专题描述")
    banner_url: Optional[str] = Field(None, max_length=255, description="横幅图URL")
    status: TopicStatus = Field(TopicStatus.DRAFT, description="专题状态")
```

**关键点**:
- `title` 必填，长度 1-100
- `description` 可选，不限长度
- `banner_url` 可选，最大 255 字符
- `status` 默认为 `DRAFT`

##### **4.5.2. TopicCreate**

```python
class TopicCreate(TopicBase):
    """创建专题请求 Schema"""
    pass  # 继承 TopicBase 的所有字段
```

**关键点**:
- 不包含 `id`, `user_id`, `created_at`, `updated_at`
- `user_id` 从 JWT Token 中提取，不在请求体中

##### **4.5.3. TopicUpdate**

```python
class TopicUpdate(BaseModel):
    """更新专题请求 Schema"""
    title: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    banner_url: Optional[str] = Field(None, max_length=255)
    status: Optional[TopicStatus] = None
```

**关键点**:
- 所有字段都是可选的
- 允许部分更新（PATCH 语义）

##### **4.5.4. TopicInDB**

```python
class TopicInDB(TopicBase):
    """数据库中的专题 Schema"""
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
```

**关键点**:
- 包含所有数据库字段
- 必须设置 `from_attributes=True` 以支持 ORM 对象转换

##### **4.5.5. TopicResponse**

```python
class TopicResponse(TopicInDB):
    """专题响应 Schema"""
    pass  # 可以在此添加计算字段或额外信息
```

**关键点**:
- 用于 API 响应
- 继承 `TopicInDB` 的所有字段

---

#### **4.6. TopicCategory 相关 Schema 详细要求**

##### **4.6.1. CategoryBase**

```python
class CategoryBase(BaseModel):
    """分类基础 Schema"""
    name: str = Field(..., min_length=1, max_length=50, description="分类名称")
    sort_order: int = Field(0, ge=0, description="排序顺序")
```

**关键点**:
- `name` 必填，长度 1-50
- `sort_order` 默认 0，必须 >= 0

##### **4.6.2. CategoryCreate**

```python
class CategoryCreate(CategoryBase):
    """创建分类请求 Schema"""
    pass
```

**关键点**:
- `topic_id` 不在请求体中，从路径参数 `/topics/{topic_id}/categories` 获取

##### **4.6.3. CategoryUpdate**

```python
class CategoryUpdate(BaseModel):
    """更新分类请求 Schema"""
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    sort_order: Optional[int] = Field(None, ge=0)
```

##### **4.6.4. CategoryInDB**

```python
class CategoryInDB(CategoryBase):
    """数据库中的分类 Schema"""
    id: uuid.UUID
    topic_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
```

##### **4.6.5. CategoryResponse**

```python
class CategoryResponse(CategoryInDB):
    """分类响应 Schema"""
    pass
```

---

#### **4.7. TopicCategoryRoom 相关 Schema 详细要求**

##### **4.7.1. RoomAssociation (用于批量添加)**

```python
class RoomAssociation(BaseModel):
    """单个直播间关联 Schema"""
    room_id: uuid.UUID = Field(..., description="直播间ID")
    sort_order: int = Field(0, ge=0, description="排序顺序")
```

**关键点**:
- 用于 `POST /api/v1/topic-categories/{category_id}/rooms` 的请求体
- 支持批量添加多个直播间

##### **4.7.2. AddRoomsRequest**

```python
class AddRoomsRequest(BaseModel):
    """添加直播间到分类请求 Schema"""
    rooms: List[RoomAssociation] = Field(..., min_length=1, max_length=50, description="要添加的直播间列表")
    
    @field_validator('rooms')
    @classmethod
    def validate_unique_room_ids(cls, v):
        """验证 room_id 唯一性"""
        room_ids = [r.room_id for r in v]
        if len(room_ids) != len(set(room_ids)):
            raise ValueError("room_id 不能重复")
        return v
```

**关键点**:
- 支持批量添加 1-50 个直播间
- 自动验证 `room_id` 唯一性

##### **4.7.3. UpdateRoomSortRequest**

```python
class UpdateRoomSortRequest(BaseModel):
    """更新直播间排序请求 Schema"""
    rooms: List[RoomAssociation] = Field(..., min_length=1, max_length=100)
```

##### **4.7.4. RemoveRoomsRequest**

```python
class RemoveRoomsRequest(BaseModel):
    """移除直播间请求 Schema"""
    room_ids: List[uuid.UUID] = Field(..., min_length=1, max_length=50, description="要移除的直播间ID列表")
```

---

#### **4.8. 聚合响应 Schema 要求（用于专题详情页）**

##### **4.8.1. RoomInCategory**

```python
class RoomInCategory(BaseModel):
    """分类下的直播间 Schema（用于聚合页面）"""
    id: uuid.UUID
    title: str
    cover_url: Optional[str]
    live_status: str  # "scheduled", "live", "finished"
    start_time: Optional[datetime]
    heat: int = Field(0, ge=0, description="热度值")
    
    model_config = ConfigDict(from_attributes=True)
```

**关键点**:
- `live_status` 从最新的 `LiveSession` 获取
- `heat` 根据统计数据计算：`int(total_viewer_count * 0.5 + total_like_count * 0.3 + peak_viewer_count * 0.2)`

##### **4.8.2. CategoryWithRooms**

```python
class CategoryWithRooms(BaseModel):
    """包含直播间列表的分类 Schema"""
    id: uuid.UUID
    name: str
    sort_order: int
    rooms: List[RoomInCategory] = []
    
    model_config = ConfigDict(from_attributes=True)
```

##### **4.8.3. TopicDetailResponse**

```python
class TopicDetailResponse(TopicInDB):
    """专题详情响应 Schema（包含层级化数据）"""
    categories: List[CategoryWithRooms] = []
```

**关键点**:
- 用于 `GET /api/v1/topics/{topic_id}` 的响应
- 返回完整的层级化数据结构：专题 → 分类 → 直播间

---

#### **4.9. 辅助 Schema 要求**

##### **4.9.1. BatchStatusRequest**

```python
class BatchStatusRequest(BaseModel):
    """批量查询状态请求 Schema"""
    room_ids: List[uuid.UUID] = Field(..., min_length=1, max_length=100)
```

##### **4.9.2. RoomStatusResponse**

```python
class RoomStatusResponse(BaseModel):
    """直播间状态响应 Schema"""
    room_id: uuid.UUID
    live_status: str
    current_session_id: Optional[uuid.UUID]
    viewer_count: int = 0
```

---

#### **4.10. 代码组织要求**

##### **4.10.1. 文件结构**

```python
"""
专题聚合功能的 Pydantic Schema

本模块包含专题聚合功能所需的所有 Pydantic 模型：
- Topic 相关 Schema
- TopicCategory 相关 Schema
- TopicCategoryRoom 相关 Schema
- 聚合响应 Schema
"""

# 导入部分

# 枚举定义部分
# - TopicStatus

# Topic Schema 部分
# - TopicBase
# - TopicCreate
# - TopicUpdate
# - TopicInDB
# - TopicResponse

# TopicCategory Schema 部分
# - CategoryBase
# - CategoryCreate
# - CategoryUpdate
# - CategoryInDB
# - CategoryResponse

# TopicCategoryRoom Schema 部分
# - RoomAssociation
# - AddRoomsRequest
# - UpdateRoomSortRequest
# - RemoveRoomsRequest

# 聚合响应 Schema 部分
# - RoomInCategory
# - CategoryWithRooms
# - TopicDetailResponse

# 辅助 Schema 部分
# - BatchStatusRequest
# - RoomStatusResponse
```

##### **4.10.2. 命名规范**

- **类名**: 大驼峰命名法（PascalCase）
  - 基础: `TopicBase`, `CategoryBase`
  - 创建: `TopicCreate`, `CategoryCreate`
  - 更新: `TopicUpdate`, `CategoryUpdate`
  - 数据库: `TopicInDB`, `CategoryInDB`
  - 响应: `TopicResponse`, `CategoryResponse`

- **字段名**: 下划线命名法（snake_case）
  - `user_id`, `banner_url`, `sort_order`, `room_id`

---

### **5. 字段验证要求 (Field Validation Requirements)**

#### **5.1. 字符串长度验证**

```python
# 使用 Field 的 min_length 和 max_length
title: str = Field(..., min_length=1, max_length=100)
```

#### **5.2. 数值范围验证**

```python
# 使用 Field 的 ge (>=) 和 le (<=)
sort_order: int = Field(0, ge=0)
```

#### **5.3. 自定义验证器**

```python
@field_validator('rooms')
@classmethod
def validate_unique_room_ids(cls, v):
    """验证 room_id 唯一性"""
    room_ids = [r.room_id for r in v]
    if len(room_ids) != len(set(room_ids)):
        raise ValueError("room_id 不能重复")
    return v
```

---

### **6. 完整性检查清单 (Completeness Checklist)**

生成的代码必须满足以下所有条件：

#### **6.1. 导入语句检查**
- [ ] 导入了 `BaseModel`, `Field`, `ConfigDict`, `field_validator`
- [ ] 导入了 `Optional`, `List`
- [ ] 导入了 `datetime`
- [ ] 导入了 `uuid`
- [ ] 导入了 `Enum`

#### **6.2. 枚举定义检查**
- [ ] 定义了 `TopicStatus` 枚举
- [ ] 枚举继承自 `str, Enum`
- [ ] 枚举值与 SQLAlchemy 模型一致

#### **6.3. Topic Schema 检查**
- [ ] 定义了 `TopicBase`
- [ ] 定义了 `TopicCreate`
- [ ] 定义了 `TopicUpdate`（所有字段可选）
- [ ] 定义了 `TopicInDB`（包含 `id`, `user_id`, 时间戳）
- [ ] 定义了 `TopicResponse`
- [ ] `TopicInDB` 设置了 `from_attributes=True`

#### **6.4. TopicCategory Schema 检查**
- [ ] 定义了 `CategoryBase`
- [ ] 定义了 `CategoryCreate`
- [ ] 定义了 `CategoryUpdate`
- [ ] 定义了 `CategoryInDB`
- [ ] 定义了 `CategoryResponse`

#### **6.5. 关联管理 Schema 检查**
- [ ] 定义了 `RoomAssociation`
- [ ] 定义了 `AddRoomsRequest`（包含 `room_id` 唯一性验证）
- [ ] 定义了 `UpdateRoomSortRequest`
- [ ] 定义了 `RemoveRoomsRequest`

#### **6.6. 聚合响应 Schema 检查**
- [ ] 定义了 `RoomInCategory`
- [ ] 定义了 `CategoryWithRooms`
- [ ] 定义了 `TopicDetailResponse`

#### **6.7. 字段验证检查**
- [ ] 所有字符串字段有长度限制
- [ ] 所有数值字段有范围限制
- [ ] `AddRoomsRequest` 包含 `room_id` 唯一性验证

#### **6.8. 代码质量检查**
- [ ] 所有 Schema 类包含中文文档字符串
- [ ] 所有字段包含 `description` 参数
- [ ] 遵循 PEP 8 代码风格
- [ ] 类名使用大驼峰命名法
- [ ] 字段名使用下划线命名法

---

### **7. 最终交付 (Final Deliverable)**

请根据以上所有要求，为 `live_core_service/app/schemas/topic.py` 文件生成**完整**、**健壮**、**符合现有项目风格**且**可直接使用**的 Python 代码。

#### **7.1. 交付要求**

1. **完整性**: 包含所有必需的 Schema 类（至少 20+ 个）
2. **一致性**: 与 SQLAlchemy 模型 100% 对应
3. **可用性**: 代码可以直接复制使用，无需修改
4. **文档化**: 每个类和关键字段都有清晰的中文说明

#### **7.2. 代码结构**

```python
# 1. 文件文档字符串
# 2. 导入语句（标准库 → 第三方库）
# 3. 枚举定义
# 4. Topic Schema（5个类）
# 5. TopicCategory Schema（5个类）
# 6. 关联管理 Schema（4个类）
# 7. 聚合响应 Schema（3个类）
# 8. 辅助 Schema（2个类）
```

#### **7.3. 使用场景**

生成的 Schema 将用于以下场景：

1. **API 端点定义**:
   ```python
   @router.post("/topics", response_model=TopicResponse)
   async def create_topic(topic_in: TopicCreate, ...):
       ...
   ```

2. **数据验证**:
   ```python
   topic_data = TopicCreate(title="测试专题", status="published")
   ```

3. **ORM 对象转换**:
   ```python
   topic_response = TopicResponse.model_validate(topic_db_obj)
   ```

4. **API 响应**:
   ```python
   return {"code": 200, "data": topic_response.model_dump()}
   ```

---

### **8. 参考示例 (Reference Example)**

以下是 `TopicBase` 的完整示例，展示所有要求的实现：

```python
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
```

**关键要点**:
- ✅ 完整的类型注解
- ✅ 详细的 `Field` 参数（验证规则 + 描述）
- ✅ 中文文档字符串
- ✅ 符合 PEP 8 代码风格

---

### **9. 为什么这个提示词会有效？**

#### **9.1. 提供了精确的上下文**
- ✅ 明确了 SQLAlchemy 模型的完整定义
- ✅ 提供了详细的字段映射规则
- ✅ 说明了每个 Schema 的使用场景

#### **9.2. 指出了关键要点**
- ✅ 强调了 Pydantic v2 语法（`ConfigDict`）
- ✅ 明确了 `from_attributes=True` 的使用场景
- ✅ 指出了字段验证的正确方式

#### **9.3. 要求明确且专业**
- ✅ 要求完整的 Schema 套件（Base, Create, Update, InDB, Response）
- ✅ 要求自定义验证器（如 `room_id` 唯一性）
- ✅ 要求聚合响应 Schema（层级化数据结构）

#### **9.4. 目标清晰无歧义**
- ✅ 任务目标直接说明了要生成哪个文件
- ✅ 详细描述了每个 Schema 的字段和验证规则
- ✅ 提供了完整性检查清单确保代码质量

#### **9.5. 与现有代码保持一致**
- ✅ 参考了 SQLAlchemy 模型的结构
- ✅ 遵循项目的命名规范和代码风格
- ✅ 确保新代码可以无缝集成到现有项目中

---

**文档版本**: V1.0  
**创建日期**: 2025-10-16  
**适用于**: 专题聚合功能 Pydantic Schema (`topic.py`)  
**基于规范**: `专题功能完整设计文档-修正版.md` + `models/topic.py`  
**参考模板**: `直播核心功能服务SQLAlchemym模型和Pydantic模型的代码生成提示词.md`

