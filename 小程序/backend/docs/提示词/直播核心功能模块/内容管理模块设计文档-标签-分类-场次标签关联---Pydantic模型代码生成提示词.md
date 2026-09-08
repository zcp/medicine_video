# 内容管理模块 Pydantic Schema 代码生成提示词

**版本**: V1.0  
**创建日期**: 2026-01-18  
**基于设计文档**: 直播核心功能设计文档_v6_内容管理模块设计文档-标签-分类-场次标签关联.md  
**目标文件**: `backend/live_core_service/app/schemas/content_management.py`

---

## **高效 AI 代码生成提示词：内容管理模块 Pydantic 模型**

### **1. 角色定义 (Role Definition)**

你是一名精通 FastAPI 和 Pydantic 的资深 Python 后端工程师。你的任务是根据已存在的 SQLAlchemy ORM 模型（`content_management.py`），为 `LiveCore Service` 的内容管理模块生成结构清晰、类型精确且符合最佳实践的 **Pydantic Schema 模型**。

**🔥 关键要求**:
- 生成的 Pydantic 模型必须与 SQLAlchemy 模型**完全对应**
- 严格遵循项目现有的 Schema 设计模式
- 确保类型安全和数据验证的完整性
- 必须使用 **Pydantic v2 语法**（`model_config = ConfigDict(from_attributes=True)`）

**🔥 增量开发模式** (非常重要):
- 这是一个 **增量开发** 任务，现有代码已经可以正常运行和测试
- **只能新增代码**，不能修改现有文件（除了追加导入）
- 现有Schema文件（如 `live_core.py`）**不能修改**
- 只需要完善 `content_management.py` 文件（如果已存在但不完整）或创建新文件
- 只需要在 `schemas/__init__.py` 中**追加**导入语句（如果尚未导入）
- 生成的Schema必须与**已存在的SQLAlchemy模型**完全对应

---

### **2. 任务目标 (Task Objective)**

你的目标是生成或完善以下 Python 文件的完整代码：

**文件路径**: `backend/live_core_service/app/schemas/content_management.py`

该文件将包含内容管理模块所需的所有 Pydantic Schema 模型，用于：
- API 请求数据验证（Create, Update）
- API 响应数据序列化（Response）
- 数据传输对象（DTO）的类型安全

**需要生成的Schema套件**:

1. **Tags 相关 Schema**:
   - `TagBase` - 标签基础Schema
   - `TagCreate` - 创建标签请求Schema
   - `TagUpdate` - 更新标签请求Schema（部分更新）
   - `TagItem` / `TagInDB` - 标签响应Schema（包含所有数据库字段）
   - `TagListResponse` - 标签列表响应Schema（可选，用于统一响应格式）

2. **Categories 相关 Schema**:
   - `CategoryBase` - 分类基础Schema
   - `CategoryCreate` - 创建分类请求Schema
   - `CategoryUpdate` - 更新分类请求Schema（部分更新）
   - `CategoryItem` / `CategoryInDB` - 分类响应Schema（包含所有数据库字段）
   - `CategoryListResponse` - 分类列表响应Schema（可选，用于统一响应格式）
   - `CategoryAdminListResponse` - 分类列表响应Schema（Admin接口，分页）

3. **Session_Tags 相关 Schema**:
   - `SessionTagsSetRequest` - 为场次设置标签请求Schema
   - `TagBriefItem` - 标签简要信息Schema（用于关联响应）
   - `SessionTagsSetResponse` - 场次标签设置响应Schema
   - `SessionTagsListResponse` - 场次标签列表响应Schema

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
backend/live_core_service/
├── app/
│   ├── __init__.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── live_core.py          # 现有模型
│   │   ├── topic.py               # 现有模型
│   │   └── content_management.py # 内容管理模块 SQLAlchemy 模型（已存在）
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── live_core.py           # 现有 Schema
│   │   └── content_management.py  # <-- 这是你要生成/完善的目标文件
│   └── ...
```

#### **3.3. SQLAlchemy 模型参考 (Existing SQLAlchemy Models)**

**文件**: `backend/live_core_service/app/models/content_management.py`

生成的 Pydantic Schema 必须与以下 SQLAlchemy 模型**完全对应**：

```python
"""
内容管理模块的数据库模型
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, ForeignKey, Boolean, Index
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMPTZ
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Tag(Base):
    """内容标签表"""
    __tablename__ = "tags"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(80), nullable=False, unique=True)
    slug = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(TIMESTAMPTZ, nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMPTZ, nullable=False, server_default=func.now(), onupdate=func.now())
    
    session_tags = relationship("SessionTag", back_populates="tag", cascade="all, delete-orphan")


class Category(Base):
    """全局医学内容分类表"""
    __tablename__ = "categories"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False, unique=True)
    slug = Column(String(120), nullable=True)
    icon = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    sort_order = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(TIMESTAMPTZ, nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMPTZ, nullable=False, server_default=func.now(), onupdate=func.now())


class SessionTag(Base):
    """直播场次与标签的多对多关联表"""
    __tablename__ = "session_tags"
    
    session_id = Column(UUID(as_uuid=True), ForeignKey("live_sessions.id", ondelete="CASCADE"), primary_key=True)
    tag_id = Column(UUID(as_uuid=True), ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True)
    created_at = Column(TIMESTAMPTZ, nullable=False, server_default=func.now())
    
    tag = relationship("Tag", back_populates="session_tags")
    session = relationship("LiveSession", foreign_keys=[session_id])
```

#### **3.4. 现有Schema文件参考 (Existing Schema Reference)**

**文件**: `backend/live_core_service/app/schemas/live_core.py`

**关键观察点**（你必须遵循的风格）:

1. **Pydantic v2语法**: `model_config = ConfigDict(from_attributes=True)`
2. **Schema套件结构**: Base、Create、Update、InDB/Response
3. **字段验证**: 使用 `Field` 参数（min_length、max_length、ge、le等）
4. **类型注解**: 所有字段必须有完整的类型注解
5. **文档字符串**: 每个Schema类包含中文文档字符串
6. **导入语句**: `from pydantic import BaseModel, Field, ConfigDict`

**完整示例代码**（参考现有代码风格）:

```python
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
    user_id: uuid.UUID = Field(..., description="用户ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    stream_key: Optional[str] = Field(None, max_length=255, description="推流密钥（仅在需要时返回）")
```

#### **3.5. 设计文档规范提取 (Design Document Specifications)**

从设计文档中提取的关键规范：

**API设计规范**（根据设计文档Section 3）:

1. **Tags Schemas 要求**:
   - `TagBase`: 包含 `name`, `slug`, `description` 字段
   - `TagCreate`: 继承 `TagBase`，包含 `is_active` 字段（可选，默认True）
   - `TagUpdate`: 所有字段可选，支持部分更新
   - `TagItem`: 包含所有数据库字段（id, name, slug, description, is_active, created_at, updated_at）
   - 字段验证：`name` 需要自定义验证器（去除特殊字符），`slug` 需要格式验证

2. **Categories Schemas 要求**:
   - `CategoryBase`: 包含 `name`, `slug`, `icon`, `description` 字段
   - `CategoryCreate`: 继承 `CategoryBase`，包含 `sort_order`（默认0）和 `is_active`（默认True）
   - `CategoryUpdate`: 所有字段可选，支持部分更新
   - `CategoryItem`: 包含所有数据库字段（id, name, slug, icon, description, sort_order, is_active, created_at, updated_at）
   - 字段验证：`name` 需要自定义验证器（去除特殊字符）

3. **Session_Tags Schemas 要求**:
   - `SessionTagsSetRequest`: 包含 `tag_ids`（List[UUID]）和 `mode`（Literal["replace", "append"]）
   - `TagBriefItem`: 标签简要信息（id, name）
   - `SessionTagsSetResponse`: 场次标签设置响应
   - `SessionTagsListResponse`: 场次标签列表响应

**字段验证规范**（根据设计文档Section 3）:

1. **字符串长度验证**:
   - `name`: min_length=1, max_length=80 (Tag) / max_length=100 (Category)
   - `slug`: max_length=100 (Tag) / max_length=120 (Category)
   - `description`: 无长度限制（Text类型）

2. **自定义验证器**:
   - `name` 字段：去除首尾空格，检查特殊字符（`<>'";`）
   - `slug` 字段：转换为小写，检查格式（只能包含小写字母、数字和连字符）

3. **列表字段验证**:
   - `tag_ids`: min_length=1, max_length=50
   - 需要验证 `tag_ids` 的唯一性（使用 `@field_validator`）

**安全与配置规范**:

1. **敏感信息处理规范**:
   - 禁止在Schema定义中硬编码密码、密钥等敏感信息的默认值
   - 如果必须设置默认值，应使用空字符串或安全的占位符

2. **字段描述安全**:
   - 禁止在 `Field(description=...)` 中包含真实的敏感信息示例
   - 如需示例，使用占位符（如 `your_password_here`、`your_secret_key_here`）

3. **文档字符串安全**:
   - 禁止在Schema类的文档字符串中包含真实的敏感信息示例
   - 如需示例，使用占位符或通用描述

---

### **4. 代码生成具体要求 (Specific Code Generation Requirements)**

#### **4.1. 导入语句要求**

**完整导入语句示例**（必须遵循）:

```python
"""
内容管理模块的 Pydantic Schemas
定义所有API输入和输出的数据模型
"""
from typing import List, Optional, Literal
from uuid import UUID
from datetime import datetime
import re

from pydantic import BaseModel, Field, ConfigDict, field_validator
```

**关键注意事项**:
1. ✅ 导入 `BaseModel`, `Field`, `ConfigDict`, `field_validator` 从 `pydantic`
2. ✅ 导入 `List`, `Optional`, `Literal` 从 `typing`
3. ✅ 导入 `UUID` 从 `uuid`
4. ✅ 导入 `datetime` 从 `datetime`
5. ✅ 导入 `re` 用于正则表达式验证（自定义验证器需要）

#### **4.2. Pydantic版本要求**

**必须使用 Pydantic v2 语法**:

```python
# ✅ 正确（Pydantic v2）
model_config = ConfigDict(from_attributes=True)

# ❌ 错误（Pydantic v1，已废弃）
class Config:
    from_attributes = True
```

#### **4.3. Schema套件结构要求**

每个数据库模型必须包含以下Schema套件：

1. **`...Base`** - 基础Schema（包含通用字段）
2. **`...Create`** - 创建请求Schema（不包含id、created_at、updated_at、外键_id字段）
3. **`...Update`** - 更新请求Schema（所有字段可选，支持部分更新）
4. **`...InDB` / `...Item`** - 数据库完整记录Schema（包含所有数据库字段，必须设置 `from_attributes=True`）
5. **`...Response`** - API响应Schema（用于API响应，可选）

#### **4.4. 字段映射规则**

**SQLAlchemy类型到Pydantic类型的映射**:

| SQLAlchemy 类型 | Pydantic 类型 | 验证规则 | 示例 |
|----------------|--------------|---------|------|
| `UUID(as_uuid=True)` | `uuid.UUID` | - | `id: uuid.UUID = Field(...)` |
| `String(80)` | `str` | `Field(max_length=80)` | `name: str = Field(..., max_length=80)` |
| `String(100)` | `str` | `Field(max_length=100)` | `slug: str = Field(None, max_length=100)` |
| `Text` | `str` | 无长度限制 | `description: Optional[str] = Field(None)` |
| `Integer` | `int` | `Field(ge=0)` | `sort_order: int = Field(0, ge=0)` |
| `Boolean` | `bool` | - | `is_active: bool = Field(True)` |
| `TIMESTAMPTZ` | `datetime` | - | `created_at: datetime = Field(...)` |

#### **4.5. 字段验证要求**

**字符串长度验证**:
```python
name: str = Field(..., min_length=1, max_length=80, description="标签名称")
```

**数值范围验证**:
```python
sort_order: int = Field(0, ge=0, description="排序权重")
```

**列表字段验证**（必须包含）:
- 所有列表字段（如 `List[Item]`）必须添加 `max_length` 限制（如 `max_length=1000`），避免大查询
- 对于可能返回大量数据的接口，建议使用分页机制
- 建议使用 `default_factory=list` 以避免潜在的 `None` 值问题
- 示例：
```python
# 列表响应字段
data: List[TagItem] = Field(default_factory=list, max_length=1000, description="标签列表")

# 列表请求字段（如已有限制，保持原样）
tag_ids: List[UUID] = Field(..., min_length=1, max_length=50, description="标签UUID列表")
```

**自定义验证器**（根据设计文档要求）:

**TagBase.name 验证器**:
```python
@field_validator('name')
@classmethod
def validate_name(cls, v: str) -> str:
    """验证标签名称"""
    v = v.strip()
    if re.search(r'[<>\'";]', v):
        raise ValueError('标签名称不能包含特殊字符')
    return v
```

**TagBase.slug 验证器**:
```python
@field_validator('slug')
@classmethod
def validate_slug(cls, v: Optional[str]) -> Optional[str]:
    """验证slug格式"""
    if v is not None:
        v = v.strip().lower()
        if not re.match(r'^[a-z0-9-]+$', v):
            raise ValueError('slug只能包含小写字母、数字和连字符')
    return v
```

**SessionTagsSetRequest.tag_ids 验证器**:
```python
@field_validator('tag_ids')
@classmethod
def validate_tag_ids_unique(cls, v: List[uuid.UUID]) -> List[uuid.UUID]:
    """验证标签ID列表唯一性"""
    if len(v) != len(set(v)):
        raise ValueError('标签ID列表中存在重复项')
    return v
```

#### **4.6. 必需字段vs可选字段**

**Create Schema**:
- 不包含 `id`, `created_at`, `updated_at`（由系统生成）
- 不包含外键的 `_id` 字段（通过路径参数传递）
- 标记必需字段为非可选，可选字段为 `Optional`

**Update Schema**:
- 所有业务字段都是 `Optional`
- 不包含 `id`, `created_at`, `updated_at`

**Response Schema**:
- 包含所有字段（包括 `id`, `created_at`, `updated_at`）
- 设置 `model_config = ConfigDict(from_attributes=True)`

#### **4.7. 与SQLAlchemy模型的对应关系**

**字段名称必须完全一致**:
- Model: `name` → Schema: `name`
- Model: `is_active` → Schema: `is_active`
- Model: `sort_order` → Schema: `sort_order`

**字段类型必须正确映射**:
- Model: `String(80)` → Schema: `str` with `Field(max_length=80)`
- Model: `Boolean` → Schema: `bool`
- Model: `TIMESTAMPTZ` → Schema: `datetime`

**默认值必须一致**:
- Model: `is_active = Column(Boolean, default=True)` → Schema: `is_active: bool = Field(True)`
- Model: `sort_order = Column(Integer, default=0)` → Schema: `sort_order: int = Field(0)`

**唯一性约束处理**（重要说明）:
- SQLAlchemy模型中的唯一性约束（`Tag.name`、`Category.name` 的 `unique=True`）需要在业务逻辑层（Service层或CRUD层）处理
- Schema层面无法验证唯一性约束（这是合理的，因为唯一性需要在数据库层面验证）
- 业务逻辑层应捕获 `IntegrityError` 并转换为业务错误码（如 `2002` 资源已存在）
- 不建议在Schema中使用自定义验证器检查唯一性（因为无法访问数据库）

#### **4.8. 安全编码规范**

1. **禁止硬编码敏感信息**: 
   - ❌ 禁止在Schema定义中硬编码密码、密钥等敏感信息的默认值
   - ✅ 如果必须设置默认值，应使用空字符串或安全的占位符

2. **字段描述安全**: 
   - ❌ 禁止在 `Field(description=...)` 中包含真实的敏感信息示例
   - ✅ 如需示例，使用占位符（如 `your_password_here`、`your_secret_key_here`）

3. **文档字符串安全**: 
   - ❌ 禁止在Schema类的文档字符串中包含真实的敏感信息示例
   - ✅ 如需示例，使用占位符或通用描述

#### **4.9. 代码组织要求**

**文件结构**:
1. 模块文档字符串
2. 导入语句
3. Tags Schemas（按顺序：Base → Create → Update → InDB/Item → Response）
4. Categories Schemas（按顺序：Base → Create → Update → InDB/Item → Response）
5. Session_Tags Schemas（按顺序：Request → BriefItem → Response）

**命名规范**:
- 类名使用大驼峰命名法（PascalCase）：`TagBase`, `TagCreate`, `TagUpdate`, `TagItem`
- 字段名使用下划线命名法（snake_case）：`tag_id`, `is_active`, `sort_order`
- Schema命名模式：`{ModelName}Base`, `{ModelName}Create`, `{ModelName}Update`, `{ModelName}Item` / `{ModelName}InDB`

---

### **5. 详细Schema定义要求**

#### **5.1. Tags Schemas**

根据设计文档Section 3.1，需要定义以下Schema：

**TagBase**:
```python
class TagBase(BaseModel):
    """标签基础Schema"""
    name: str = Field(..., min_length=1, max_length=80, description="标签名称")
    slug: Optional[str] = Field(None, max_length=100, description="URL友好标识符")
    description: Optional[str] = Field(None, max_length=500)
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """验证标签名称"""
        v = v.strip()
        if re.search(r'[<>\'";]', v):
            raise ValueError('标签名称不能包含特殊字符')
        return v
    
    @field_validator('slug')
    @classmethod
    def validate_slug(cls, v: Optional[str]) -> Optional[str]:
        """验证slug格式"""
        if v is not None:
            v = v.strip().lower()
            if not re.match(r'^[a-z0-9-]+$', v):
                raise ValueError('slug只能包含小写字母、数字和连字符')
        return v
```

**TagCreate**:
```python
class TagCreate(TagBase):
    """创建标签请求Schema"""
    is_active: Optional[bool] = Field(True, description="是否启用")
```

**TagUpdate**:
```python
class TagUpdate(BaseModel):
    """更新标签请求Schema（部分更新）"""
    model_config = ConfigDict(from_attributes=True)
    
    name: Optional[str] = Field(None, min_length=1, max_length=80)
    slug: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None
```

**TagItem**:
```python
class TagItem(TagBase):
    """标签响应Schema"""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
```

**TagListResponse**（可选，根据设计文档）:
```python
class TagListResponse(BaseModel):
    """标签列表响应Schema"""
    code: int = 200
    message: str = "success"
    data: List[TagItem] = Field(default_factory=list, max_length=1000, description="标签列表")
    timestamp: datetime
```

#### **5.2. Categories Schemas**

根据设计文档Section 3.2，需要定义以下Schema：

**CategoryBase**:
```python
class CategoryBase(BaseModel):
    """分类基础Schema"""
    name: str = Field(..., min_length=1, max_length=100, description="分类名称")
    slug: Optional[str] = Field(None, max_length=120)
    icon: Optional[str] = Field(None, max_length=255, description="图标名称或URL")
    description: Optional[str] = Field(None, max_length=500)
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if re.search(r'[<>\'";]', v):
            raise ValueError('分类名称不能包含特殊字符')
        return v
```

**CategoryCreate**:
```python
class CategoryCreate(CategoryBase):
    """创建分类请求Schema"""
    sort_order: Optional[int] = Field(0, ge=0, description="排序权重")
    is_active: Optional[bool] = Field(True, description="是否启用")
```

**CategoryUpdate**:
```python
class CategoryUpdate(BaseModel):
    """更新分类请求Schema（部分更新）"""
    model_config = ConfigDict(from_attributes=True)
    
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    slug: Optional[str] = None
    icon: Optional[str] = None
    description: Optional[str] = None
    sort_order: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None
```

**CategoryItem**:
```python
class CategoryItem(CategoryBase):
    """分类响应Schema"""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    sort_order: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
```

**CategoryListResponse**（根据设计文档）:
```python
class CategoryListResponse(BaseModel):
    """分类列表响应Schema（公开接口，不分页）"""
    code: int = 200
    message: str = "success"
    data: List[CategoryItem] = Field(default_factory=list, max_length=1000, description="分类列表")
    timestamp: datetime
```

**PaginatedData**（通用分页Schema，根据设计文档）:
```python
from typing import TypeVar, Generic

T = TypeVar('T')

class PaginatedData(BaseModel, Generic[T]):
    """分页数据通用Schema"""
    total: int
    page: int
    size: int
    items: List[T]
```

**CategoryAdminListResponse**（根据设计文档）:
```python
class CategoryAdminListResponse(BaseModel):
    """分类列表响应Schema（Admin接口，分页）"""
    code: int = 200
    message: str = "success"
    data: PaginatedData[CategoryItem]
    timestamp: datetime
```

#### **5.3. Session_Tags Schemas**

根据设计文档Section 3.3，需要定义以下Schema：

**SessionTagsSetRequest**:
```python
class SessionTagsSetRequest(BaseModel):
    """为场次设置标签请求Schema"""
    tag_ids: List[uuid.UUID] = Field(..., min_length=1, max_length=50, description="标签UUID列表")
    mode: Literal["replace", "append"] = Field(..., description="操作模式：replace=替换，append=追加")
    
    @field_validator('tag_ids')
    @classmethod
    def validate_tag_ids_unique(cls, v: List[uuid.UUID]) -> List[uuid.UUID]:
        """验证标签ID列表唯一性"""
        if len(v) != len(set(v)):
            raise ValueError('标签ID列表中存在重复项')
        return v
```

**TagBriefItem**:
```python
class TagBriefItem(BaseModel):
    """标签简要信息Schema（用于关联响应）"""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    name: str
```

**SessionTagsSetResponse**:
```python
class SessionTagsSetResponse(BaseModel):
    """场次标签设置响应Schema"""
    code: int = 200
    message: str = "success"
    data: dict  # {"session_id": "...", "mode": "replace", "tags": [...]}
    timestamp: datetime
```

**SessionTagsListResponse**:
```python
class SessionTagsListResponse(BaseModel):
    """场次标签列表响应Schema"""
    code: int = 200
    message: str = "success"
    data: List[TagItem] = Field(default_factory=list, max_length=100, description="场次标签列表")  # 使用 TagItem 而非 TagBriefItem
    timestamp: datetime
```

---

### **6. 完整性检查清单 (Completeness Checklist)**

生成代码后，请检查以下项目：

- [ ] **导入语句**: BaseModel、Field、ConfigDict、field_validator、类型注解
- [ ] **Tags Schemas**: Base、Create、Update、Item、ListResponse（如需要）
- [ ] **Categories Schemas**: Base、Create、Update、Item、ListResponse、AdminListResponse、PaginatedData
- [ ] **Session_Tags Schemas**: SetRequest、BriefItem、SetResponse、ListResponse
- [ ] **字段验证**: 字符串长度、数值范围、自定义验证器（name、slug、tag_ids）
- [ ] **代码质量**: 文档字符串、字段描述、PEP 8规范、类型注解完整性
- [ ] **Pydantic v2语法**: 所有Response Schema设置了 `model_config = ConfigDict(from_attributes=True)`
- [ ] **字段映射**: 所有字段与SQLAlchemy模型完全对应
- [ ] **默认值一致性**: Schema默认值与Model默认值一致
- [ ] **安全规范**: 
  - [ ] Schema定义中无硬编码的敏感信息默认值
  - [ ] 字段描述中无真实的敏感信息示例
  - [ ] 文档字符串中无真实的敏感信息示例
- [ ] **增量开发规范**:
  - [ ] `__init__.py` 修改为最小幅度（仅追加导入，不修改现有内容）
  - [ ] 新导入格式与现有导入格式完全一致
  - [ ] 无重复导入
  - [ ] 无命名冲突（如有冲突已使用别名）
  - [ ] 未改变现有导入的顺序
  - [ ] 未修改现有导入的格式

---

### **7. 最终交付 (Final Deliverable)**

#### **7.1. 生成的代码文件**

生成的代码应该可以直接复制到 `backend/live_core_service/app/schemas/content_management.py` 文件中。

#### **7.2. __init__.py 文件修改**

**必须最小幅度修改** `backend/live_core_service/app/schemas/__init__.py`，在文件末尾追加导入：

**当前 `__init__.py` 内容**（不要修改任何现有内容）:
```python
# LiveCore Service Schemas Package

# 直播间 Tab 和留言功能 Schema（新增）
from .live_features import (
    LiveRoomMessageUserRole,
    LiveRoomTabContentType,
    LiveRoomTabBase,
    LiveRoomTabCreate,
    LiveRoomTabUpdate,
    LiveRoomTabInDB,
    LiveRoomTabResponse,
    LiveRoomMessageBase,
    LiveRoomMessageCreate,
    LiveRoomMessageCreateInternal,
    LiveRoomMessageUpdate,
    LiveRoomMessageInDB,
    LiveRoomMessagePostResponse,
    LiveRoomMessageListResponseItem,
    PaginatedLiveRoomMessageResponse
)
```

**追加新导入**（在文件末尾追加，保持与现有导入格式完全一致）:
```python
# 内容管理模块 Schema（新增）
from .content_management import (
    TagBase,
    TagCreate,
    TagUpdate,
    TagItem,
    TagListResponse,
    CategoryBase,
    CategoryCreate,
    CategoryUpdate,
    CategoryItem,
    CategoryListResponse,
    PaginatedData,
    CategoryAdminListResponse,
    SessionTagsSetRequest,
    TagBriefItem,
    SessionTagsSetResponse,
    SessionTagsListResponse
)
```

**⚠️ 最小改动要求**:
- ✅ **只追加**：仅在文件末尾追加新导入，不修改任何现有内容
- ✅ **格式一致**：新导入的格式（缩进、引号、换行）必须与现有导入完全一致
- ✅ **检查重复**：追加前必须检查 `__init__.py` 中是否已存在相同导入，避免重复
- ✅ **检查冲突**：追加前必须检查新导入的类名是否与现有类名冲突，如有冲突必须使用别名
- ✅ **保持顺序**：如果现有导入有特定顺序（如按字母顺序），新导入必须遵循相同规则
- ❌ **不重新排序**：严禁改变现有导入的顺序
- ❌ **不修改格式**：严禁修改现有导入的格式（单行/多行、注释等）
- ❌ **不修改空行**：严禁修改现有导入之间的空行
- ❌ **不添加注释**：除非现有代码有注释，否则不添加注释

#### **7.3. 增量开发注意事项**

**⚠️ 增量开发注意事项**（必须在提示词中明确列出）:
- ✅ 只需要创建/完善 **新文件** `content_management.py`
- ✅ 只需要在 `__init__.py` 文件末尾 **追加** 导入语句（最小改动）
- ❌ **不要修改** 现有的Schema文件（如 `live_core.py`）
- ❌ **不要修改** `__init__.py` 中的现有导入（包括顺序、格式、注释等）
- ❌ **不要重新排序** 现有导入语句
- ❌ **不要添加** 重复的导入语句
- ❌ **不要引入** 命名冲突（如有冲突必须使用别名）
- ✅ 生成的Schema必须与**已存在的SQLAlchemy模型**完全对应

---

**文档版本**: V1.0  
**创建日期**: 2026-01-18  
**适用于**: 内容管理模块 Pydantic Schema 代码生成  
**基于设计文档**: 直播核心功能设计文档_v6_内容管理模块设计文档-标签-分类-场次标签关联.md

