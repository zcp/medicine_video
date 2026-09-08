# 品牌模块设计文档-品牌管理-品牌专题关联-品牌直播间关联---Pydantic模型代码生成提示词

**版本**: V1.0  
**创建日期**: 2026-01-18  
**基于设计文档**: 直播核心功能设计文档_v6_品牌模块设计文档-品牌管理-品牌专题关联.md  
**目标文件**: `backend/live_core_service/app/schemas/brand.py`

---

## **高效 AI 代码生成提示词：品牌模块 Pydantic 模型**

### **1. 角色定义 (Role Definition)**

你是一名精通 FastAPI 和 Pydantic 的资深 Python 后端工程师。你的任务是根据已存在的 SQLAlchemy ORM 模型（`brand.py`），为 `LiveCore Service` 的品牌模块生成结构清晰、类型精确且符合最佳实践的 **Pydantic Schema 模型**。

**🔥 关键要求**:
- 生成的 Pydantic 模型必须与 SQLAlchemy 模型**完全对应**
- 严格遵循项目现有的 Schema 设计模式
- 确保类型安全和数据验证的完整性
- 必须使用 **Pydantic v2 语法**（`model_config = ConfigDict(from_attributes=True)`）

**🔥 增量开发模式** (非常重要):
- 这是一个 **增量开发** 任务，现有代码已经可以正常运行和测试
- **只能新增代码**，不能修改现有文件（除了追加导入）
- 现有Schema文件（如 `live_core.py`）**不能修改**
- 只需要创建新文件 `brand.py`
- 只需要在 `schemas/__init__.py` 中**追加**导入语句
- 生成的Schema必须与**已存在的SQLAlchemy模型**完全对应

---

### **2. 任务目标 (Task Objective)**

你的目标是生成以下 Python 文件的完整代码：

**文件路径**: `backend/live_core_service/app/schemas/brand.py`

该文件将包含品牌模块所需的所有 Pydantic Schema 模型，用于：
- API 请求数据验证（Create, Update）
- API 响应数据序列化（Response）
- 数据传输对象（DTO）的类型安全

**需要生成的Schema套件**:

1. **品牌管理 Schemas**:
   - `BrandBase` - 品牌基础Schema
   - `BrandCreate` - 创建品牌请求Schema
   - `BrandUpdate` - 更新品牌请求Schema（部分更新）
   - `BrandItem` - 品牌响应Schema（包含所有数据库字段）

2. **品牌内容响应 Schemas**:
   - `TopicBriefItem` - 专题简要信息Schema（用于品牌内容响应）
   - `BrandContentData` - 品牌内容数据Schema（品牌信息+关联专题）
   - `BrandContentResponse` - 品牌内容响应Schema（统一响应格式）

3. **品牌-专题关联 Schemas**:
   - `BrandTopicBindIn` - 绑定品牌专题请求Schema
   - `BrandTopicBindOut` - 绑定品牌专题响应Schema
   - `TopicBrandItem` - 专题品牌展示项Schema

4. **品牌-直播间关联 Schemas**（V1.1新增）:
   - `BrandRoomBindIn` - 直播间绑定品牌请求Schema
   - `BrandRoomBindOut` - 直播间绑定品牌响应Schema
   - `RoomBrandItem` - 直播间品牌Tab展示项Schema

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
│   │   └── brand.py               # 品牌模块 SQLAlchemy 模型（已存在）
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── live_core.py           # 现有 Schema
│   │   └── brand.py               # <-- 这是你要创建的目标文件
│   └── ...
```

**⚠️ 重要提示 - 增量开发原则**:
- ✅ **可以新建**: `brand.py` 文件
- ✅ **可以追加**: 在 `schemas/__init__.py` 中添加导入语句
- ❌ **不要修改**: 现有Schema文件（如 `live_core.py`）
- ❌ **不要修改**: 现有模型文件

#### **3.3. SQLAlchemy 模型参考 (Existing SQLAlchemy Models)**

**文件**: `backend/live_core_service/app/models/brand.py`

生成的 Pydantic Schema 必须与以下 SQLAlchemy 模型**完全对应**：

```python
"""
品牌模块的数据库模型

本模块包含品牌模块所需的三个 SQLAlchemy 模型类：
- Brand: 品牌/合作伙伴表
- BrandTopic: 品牌-专题关联表
- BrandRoom: 品牌-直播间关联表
"""
import uuid
from datetime import datetime
import enum

from sqlalchemy import Column, String, Text, Integer, Boolean, ForeignKey, Index, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Brand(Base):
    """品牌/合作伙伴信息表"""
    __tablename__ = "brands"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(150), nullable=False, unique=True, comment='品牌名称')
    slug = Column(String(150), nullable=True, comment='URL友好标识符')
    logo_url = Column(String(512), nullable=True, comment='品牌Logo图片URL')
    description = Column(Text, nullable=True, comment='品牌描述')
    website_url = Column(String(255), nullable=True, comment='品牌官网链接')
    sort_order = Column(Integer, default=0, nullable=False, comment='排序权重')
    is_active = Column(Boolean, default=True, nullable=False, comment='软删除标识')
    
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class BrandTopic(Base):
    """品牌与专题的多对多关联表"""
    __tablename__ = "brand_topics"
    
    brand_id = Column(UUID(as_uuid=True), ForeignKey("brands.id", ondelete="CASCADE"), nullable=False, primary_key=True)
    topic_id = Column(UUID(as_uuid=True), ForeignKey("topics.id", ondelete="CASCADE"), nullable=False, primary_key=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())


class BrandRoom(Base):
    """品牌与直播间的多对多关联表"""
    __tablename__ = "brand_rooms"
    
    brand_id = Column(UUID(as_uuid=True), ForeignKey("brands.id", ondelete="CASCADE"), nullable=False, primary_key=True)
    room_id = Column(UUID(as_uuid=True), ForeignKey("live_rooms.id", ondelete="CASCADE"), nullable=False, primary_key=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
```

#### **3.4. 现有Schema文件参考 (Existing Schema Reference)**

**文件**: `backend/live_core_service/app/schemas/live_core.py`

**关键观察点**（你必须遵循的风格）:

1. **Pydantic v2语法**: `model_config = ConfigDict(from_attributes=True)`
2. **Schema套件结构**: Base、Create、Update、InDB/Response
3. **字段验证**: 使用 `Field` 参数（min_length、max_length、ge、le等）
4. **类型注解**: 所有字段必须有完整的类型注解
5. **文档字符串**: 每个Schema类包含中文文档字符串
6. **导入语句**: `from pydantic import BaseModel, Field, ConfigDict, field_validator`

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


class LiveRoomBase(BaseModel):
    """直播房间基础Schema"""
    title: str = Field(..., max_length=100, description="房间标题")
    description: Optional[str] = Field(None, description="房间描述")
    cover_url: Optional[str] = Field(None, max_length=255, description="封面图片URL")
    is_private: bool = Field(False, description="是否为私密房间")


class LiveRoomCreate(LiveRoomBase):
    """创建直播房间请求Schema"""
    parent_room_id: Optional[uuid.UUID] = Field(None, description="父房间ID")


class LiveRoomUpdate(BaseModel):
    """更新直播房间请求Schema"""
    model_config = ConfigDict(from_attributes=True)
    
    title: Optional[str] = Field(None, max_length=100, description="房间标题")
    description: Optional[str] = Field(None, description="房间描述")
    cover_url: Optional[str] = Field(None, max_length=255, description="封面图片URL")
    is_private: Optional[bool] = Field(None, description="是否为私密房间")
    parent_room_id: Optional[uuid.UUID] = Field(None, description="父房间ID")


class LiveRoomResponse(LiveRoomBase):
    """直播房间响应Schema"""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(..., description="房间ID")
    parent_room_id: Optional[uuid.UUID] = Field(None, description="父房间ID")
    user_id: uuid.UUID = Field(..., description="用户ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
```

#### **3.5. 设计文档规范提取 (Design Document Specifications)**

**从设计文档中提取的API Schema规范**（Section 3）:

##### **3.5.1. 品牌管理Schemas要求**（Section 3.1）

1. **BrandBase**:
   - `name`: str, min_length=1, max_length=150, 必需字段
   - `slug`: Optional[str], max_length=150
   - `logo_url`: Optional[str], max_length=512
   - `description`: Optional[str], max_length=500（设计文档中未明确，建议500）
   - `website_url`: Optional[str], max_length=255
   - **自定义验证器**: `website_url` 需要验证URL格式（必须以http://或https://开头）

2. **BrandCreate**:
   - 继承 `BrandBase`
   - `sort_order`: Optional[int], default=0, ge=0（非负整数）
   - `is_active`: Optional[bool], default=True
   - **不包含**: id, created_at, updated_at（由系统生成）

3. **BrandUpdate**:
   - 所有字段都是 `Optional`
   - 支持部分更新
   - **不包含**: id, created_at, updated_at

4. **BrandItem**:
   - 继承 `BrandBase`
   - 包含所有数据库字段：id, sort_order, is_active, created_at, updated_at
   - 使用 `model_config = ConfigDict(from_attributes=True)` 支持ORM对象转换

##### **3.5.2. 品牌内容响应Schemas要求**（Section 3.2）

1. **TopicBriefItem**:
   - `id`: uuid.UUID
   - `title`: str
   - `banner_url`: Optional[str]

2. **BrandContentData**:
   - `brand_info`: BrandItem
   - `associated_topics`: List[TopicBriefItem]（必须添加 `max_length` 限制，建议1000）

3. **BrandContentResponse**:
   - 统一响应格式：code, message, data, timestamp
   - `code`: int = 200
   - `message`: str = "success"
   - `data`: BrandContentData
   - `timestamp`: datetime.datetime

##### **3.5.3. 品牌-直播间关联Schemas要求**（Section 3.3）

1. **BrandRoomBindIn**:
   - `brand_ids`: List[uuid.UUID], default_factory=list（必须添加 `max_length` 限制，建议100）

2. **RoomBrandItem**:
   - 包含品牌基本信息：id, name, slug, logo_url, website_url, sort_order
   - 使用 `model_config = ConfigDict(from_attributes=True)`

3. **BrandRoomBindOut**:
   - `room_id`: uuid.UUID
   - `brand_ids`: List[uuid.UUID]（必须添加 `max_length` 限制，建议100）
   - `updated_at`: datetime.datetime

---

### **4. 代码生成具体要求 (Specific Code Generation Requirements)**

#### **4.1. 导入语句要求**

必须使用以下导入语句：

```python
"""
品牌模块的 Pydantic Schemas

本模块包含品牌模块所需的所有 Pydantic Schema 模型，用于API数据验证和序列化。
"""
import uuid
import datetime
import re
from typing import Optional, List

from pydantic import BaseModel, Field, ConfigDict, field_validator
```

#### **4.2. Schema套件定义要求**

##### **4.2.1. 品牌管理 Schemas**

```python
class BrandBase(BaseModel):
    """品牌基础Schema"""
    name: str = Field(..., min_length=1, max_length=150, description="品牌名称")
    slug: Optional[str] = Field(None, max_length=150, description="URL友好标识符")
    logo_url: Optional[str] = Field(None, max_length=512, description="品牌Logo URL")
    description: Optional[str] = Field(None, description="品牌描述")
    website_url: Optional[str] = Field(None, max_length=255, description="品牌官网")
    
    @field_validator('website_url')
    @classmethod
    def validate_website_url(cls, v: Optional[str]) -> Optional[str]:
        """验证URL格式"""
        if v is not None:
            v = v.strip()
            if not re.match(r'^https?://', v):
                raise ValueError('网站URL必须以http://或https://开头')
        return v


class BrandCreate(BrandBase):
    """创建品牌请求Schema"""
    sort_order: Optional[int] = Field(0, ge=0, description="排序权重")
    is_active: Optional[bool] = Field(True, description="是否激活")


class BrandUpdate(BaseModel):
    """更新品牌请求Schema（部分更新）"""
    model_config = ConfigDict(from_attributes=True)
    
    name: Optional[str] = Field(None, min_length=1, max_length=150, description="品牌名称")
    slug: Optional[str] = Field(None, max_length=150, description="URL友好标识符")
    logo_url: Optional[str] = Field(None, max_length=512, description="品牌Logo URL")
    description: Optional[str] = Field(None, description="品牌描述")
    website_url: Optional[str] = Field(None, max_length=255, description="品牌官网")
    sort_order: Optional[int] = Field(None, ge=0, description="排序权重")
    is_active: Optional[bool] = Field(None, description="是否激活")


class BrandItem(BrandBase):
    """品牌响应Schema"""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID = Field(..., description="品牌ID")
    sort_order: int = Field(..., description="排序权重")
    is_active: bool = Field(..., description="是否激活")
    created_at: datetime.datetime = Field(..., description="创建时间")
    updated_at: datetime.datetime = Field(..., description="更新时间")
```

##### **4.2.2. 品牌内容响应 Schemas**

```python
class TopicBriefItem(BaseModel):
    """专题简要信息Schema"""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID = Field(..., description="专题ID")
    title: str = Field(..., description="专题标题")
    banner_url: Optional[str] = Field(None, description="专题横幅图URL")


class BrandContentData(BaseModel):
    """品牌内容数据Schema"""
    brand_info: BrandItem = Field(..., description="品牌信息")
    associated_topics: List[TopicBriefItem] = Field(
        default_factory=list, 
        max_length=1000, 
        description="关联的专题列表"
    )


class BrandContentResponse(BaseModel):
    """品牌内容响应Schema"""
    code: int = Field(200, description="状态码")
    message: str = Field("success", description="响应消息")
    data: BrandContentData = Field(..., description="响应数据")
    timestamp: datetime.datetime = Field(..., description="响应时间戳")
```

##### **4.2.3. 品牌-专题关联 Schemas**

```python
class BrandTopicBindIn(BaseModel):
    """绑定品牌专题请求Schema"""
    topic_ids: List[uuid.UUID] = Field(
        default_factory=list, 
        max_length=100, 
        description="要绑定的专题ID列表"
    )


class TopicBrandItem(BaseModel):
    """专题品牌展示项Schema"""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID = Field(..., description="品牌ID")
    name: str = Field(..., description="品牌名称")
    slug: Optional[str] = Field(None, description="URL友好标识符")
    logo_url: Optional[str] = Field(None, description="品牌Logo URL")
    sort_order: int = Field(0, description="排序权重")


class BrandTopicBindOut(BaseModel):
    """绑定品牌专题响应Schema"""
    brand_id: uuid.UUID = Field(..., description="品牌ID")
    topic_ids: List[uuid.UUID] = Field(
        ..., 
        max_length=100, 
        description="绑定的专题ID列表"
    )
    updated_at: datetime.datetime = Field(..., description="更新时间")
```

##### **4.2.4. 品牌-直播间关联 Schemas（V1.1新增）**

```python
class BrandRoomBindIn(BaseModel):
    """直播间绑定品牌请求Schema"""
    brand_ids: List[uuid.UUID] = Field(
        default_factory=list, 
        max_length=100, 
        description="要绑定的品牌ID列表"
    )


class RoomBrandItem(BaseModel):
    """直播间品牌Tab展示项Schema（Room Page专用）"""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID = Field(..., description="品牌ID")
    name: str = Field(..., description="品牌名称")
    slug: Optional[str] = Field(None, description="URL友好标识符")
    logo_url: Optional[str] = Field(None, description="品牌Logo URL")
    website_url: Optional[str] = Field(None, description="品牌官网")
    sort_order: int = Field(0, description="排序权重")


class BrandRoomBindOut(BaseModel):
    """直播间绑定品牌响应Schema"""
    room_id: uuid.UUID = Field(..., description="直播间ID")
    brand_ids: List[uuid.UUID] = Field(
        ..., 
        max_length=100, 
        description="绑定的品牌ID列表"
    )
    updated_at: datetime.datetime = Field(..., description="更新时间")
```

#### **4.3. 字段映射规则（SQLAlchemy类型到Pydantic类型）**

- `UUID` → `uuid.UUID`
- `String(n)` → `str`（使用 `Field(max_length=n)` 限制长度）
- `Text` → `str`（不限制长度）
- `Integer` → `int`（使用 `Field(ge=0)` 等限制范围）
- `Boolean` → `bool`
- `TIMESTAMP(timezone=True)` → `datetime.datetime`

#### **4.4. 字段验证要求**

1. **字符串长度验证**: `Field(..., min_length=1, max_length=150)`
2. **数值范围验证**: `Field(0, ge=0)`（非负整数）
3. **列表字段验证**: 
   - 所有列表字段（如 `List[uuid.UUID]`）必须添加 `max_length` 限制
   - 建议使用 `default_factory=list` 以避免潜在的 `None` 值问题
   - 示例：`Field(default_factory=list, max_length=100)`
4. **自定义验证器**: 使用 `@field_validator` 装饰器（如 `website_url` 的URL格式验证）

#### **4.5. 必需字段vs可选字段**

1. **Create Schema**: 
   - 不包含 `id`, `created_at`, `updated_at`（由系统生成）
   - 标记必需字段为非可选，可选字段为 `Optional`
   - 有默认值的字段可以为 `Optional` 或直接提供默认值

2. **Update Schema**: 
   - 所有业务字段都是 `Optional`
   - 不包含 `id`, `created_at`, `updated_at`

3. **Response Schema**: 
   - 包含所有字段（包括 `id`, `created_at`, `updated_at`）
   - 设置 `model_config = ConfigDict(from_attributes=True)`

#### **4.6. 代码组织要求**

**文件结构**:
```
模块文档字符串
导入语句
品牌管理Schemas（BrandBase, BrandCreate, BrandUpdate, BrandItem）
品牌内容响应Schemas（TopicBriefItem, BrandContentData, BrandContentResponse）
品牌-专题关联Schemas（BrandTopicBindIn, TopicBrandItem, BrandTopicBindOut）
品牌-直播间关联Schemas（BrandRoomBindIn, RoomBrandItem, BrandRoomBindOut）
```

**命名规范**: 
- 类名使用大驼峰命名法（PascalCase）：`BrandBase`, `BrandCreate`, `BrandItem`
- 字段名使用下划线命名法（snake_case）：`brand_id`, `logo_url`, `sort_order`

---

### **5. 完整性检查清单 (Completeness Checklist)**

生成代码后，请检查以下所有项：

**导入语句**:
- ✅ BaseModel、Field、ConfigDict、field_validator导入正确
- ✅ uuid、datetime、re、typing导入正确

**品牌管理Schemas**:
- ✅ BrandBase定义完整（所有字段、验证器）
- ✅ BrandCreate定义完整（继承BrandBase，包含sort_order和is_active）
- ✅ BrandUpdate定义完整（所有字段Optional，支持部分更新）
- ✅ BrandItem定义完整（包含所有数据库字段，from_attributes=True）

**品牌内容响应Schemas**:
- ✅ TopicBriefItem定义完整
- ✅ BrandContentData定义完整（包含brand_info和associated_topics，列表字段有max_length）
- ✅ BrandContentResponse定义完整（统一响应格式）

**品牌-专题关联Schemas**:
- ✅ BrandTopicBindIn定义完整（列表字段有max_length和default_factory）
- ✅ TopicBrandItem定义完整（from_attributes=True）
- ✅ BrandTopicBindOut定义完整

**品牌-直播间关联Schemas**:
- ✅ BrandRoomBindIn定义完整（列表字段有max_length和default_factory）
- ✅ RoomBrandItem定义完整（from_attributes=True）
- ✅ BrandRoomBindOut定义完整

**字段验证**:
- ✅ 所有字符串字段有长度限制（max_length）
- ✅ 所有数值字段有范围限制（ge, le等）
- ✅ 所有列表字段有max_length限制和default_factory
- ✅ 自定义验证器正确实现（website_url的URL格式验证）

**代码质量**:
- ✅ 所有Schema类有文档字符串
- ✅ 所有字段有description参数
- ✅ 代码遵循PEP 8规范
- ✅ 类型注解完整

**安全规范**:
- ✅ Schema定义中无硬编码的敏感信息默认值
- ✅ 字段描述中无真实的敏感信息示例
- ✅ 文档字符串中无真实的敏感信息示例

**增量开发规范**:
- ✅ 新文件创建在 `app/schemas/brand.py`
- ✅ 需要在 `schemas/__init__.py` 中追加导入：`from .brand import BrandItem, BrandCreate, BrandUpdate, ...`
- ✅ `__init__.py` 修改为最小幅度（仅追加导入，不修改现有内容）
- ✅ 新导入格式与现有导入格式完全一致
- ✅ 无重复导入
- ✅ 无命名冲突

---

### **6. 最终交付 (Final Deliverable)**

**生成的文件**:
- `backend/live_core_service/app/schemas/brand.py` - 包含所有品牌模块的Pydantic Schema类

**需要手动完成的步骤**:

1. **更新 `schemas/__init__.py`**：
   在文件末尾追加导入语句：

   ```python
   # 现有代码（不要修改任何内容，包括格式、顺序、空行、注释等）
   from .live_core import LiveRoomResponse, LiveSessionResponse
   # ... 其他现有导入 ...
   
   # 新增导入（追加在文件末尾，保持与现有导入格式完全一致）
   from .brand import (
       BrandItem, BrandCreate, BrandUpdate, BrandBase,
       BrandContentData, BrandContentResponse, TopicBriefItem,
       BrandTopicBindIn, BrandTopicBindOut, TopicBrandItem,
       BrandRoomBindIn, BrandRoomBindOut, RoomBrandItem
   )
   ```

   **⚠️ 最小改动要求**:
   - ✅ **只追加**：仅在文件末尾追加新导入，不修改任何现有内容
   - ✅ **格式一致**：新导入的格式必须与现有导入完全一致（缩进、引号、换行等）
   - ✅ **检查重复**：追加前检查是否已存在相同导入，避免重复
   - ✅ **检查冲突**：追加前检查类名是否冲突，如有冲突使用别名
   - ❌ **不重新排序**：不改变现有导入的顺序
   - ❌ **不修改格式**：不修改现有导入的格式

**验证步骤**:
1. 检查生成的代码语法正确（无linter错误）
2. 检查 `__init__.py` 导入语句正确
3. 验证Schema与SQLAlchemy模型字段完全对应
4. 验证字段验证规则正确（长度限制、范围限制等）
5. 验证列表字段都有max_length限制和default_factory

---

**版本历史**:
- V1.0 (2026-01-18): 初始版本
