# 首页与搜索模块设计文档-焦点图-首页API-搜索API---Pydantic模型代码生成提示词

**版本**: V1.0  
**创建日期**: 2026-01-18  
**基于设计文档**: 直播核心功能设计文档_v6_首页与搜索模块设计文档-焦点图-首页API-搜索API.md  
**目标文件**: `backend/live_core_service/app/schemas/homepage_search.py`

---

## **高效 AI 代码生成提示词：首页与搜索模块 Pydantic 模型**

### **1. 角色定义 (Role Definition)**

你是一名精通 FastAPI 和 Pydantic 的资深 Python 后端工程师。你的任务是根据已存在的 SQLAlchemy ORM 模型（`homepage_search.py`），为 `LiveCore Service` 的首页与搜索模块生成结构清晰、类型精确且符合最佳实践的 **Pydantic Schema 模型**。

**🔥 关键要求**:
- 生成的 Pydantic 模型必须与 SQLAlchemy 模型**完全对应**
- 严格遵循项目现有的 Schema 设计模式
- 确保类型安全和数据验证的完整性
- 必须使用 **Pydantic v2 语法**（`model_config = ConfigDict(from_attributes=True)`）

**🔥 增量开发模式** (非常重要):
- 这是一个 **增量开发** 任务，现有代码已经可以正常运行和测试
- **只能新增代码**，不能修改现有文件（除了追加导入）
- 现有Schema文件（如 `live_core.py`, `brand.py`）**不能修改**
- 只需要创建新文件 `homepage_search.py`
- 只需要在 `schemas/__init__.py` 中**追加**导入语句
- 生成的Schema必须与**已存在的SQLAlchemy模型**完全对应

---

### **2. 任务目标 (Task Objective)**

你的目标是生成以下 Python 文件的完整代码：

**文件路径**: `backend/live_core_service/app/schemas/homepage_search.py`

该文件将包含首页与搜索模块所需的所有 Pydantic Schema 模型，用于：
- API 请求数据验证（Create, Update）
- API 响应数据序列化（Response）
- 数据传输对象（DTO）的类型安全

**需要生成的Schema套件**:

1. **焦点图管理 Schemas**:
   - `FeaturedContentBase` - 焦点图基础Schema
   - `FeaturedContentCreate` - 创建焦点图请求Schema
   - `FeaturedContentUpdate` - 更新焦点图请求Schema（部分更新）
   - `FeaturedContentItem` - 焦点图响应Schema

2. **首页API Schemas**:
   - `LiveStatusEnum` - 直播状态枚举
   - `HomepageHostInfo` - 首页主讲人信息Schema
   - `HomepageStatusData` - 首页状态数据Schema
   - `HomepageRoomItem` - 首页直播间信息Schema
   - `HomepageRoomsResponse` - 首页直播间列表响应Schema

3. **搜索API Schemas**:
   - `SearchResultType` - 搜索结果类型枚举
   - `SearchResultItem` - 搜索结果项Schema
   - `SearchResponse` - 搜索响应Schema

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
│   │   ├── brand.py               # 现有模型
│   │   └── homepage_search.py     # 首页与搜索模块 SQLAlchemy 模型（已存在）
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── live_core.py           # 现有 Schema
│   │   ├── brand.py               # 现有 Schema
│   │   ├── content_management.py  # 现有 Schema（包含PaginatedData）
│   │   └── homepage_search.py     # <-- 这是你要创建的目标文件
│   └── ...
```

**⚠️ 重要提示 - 增量开发原则**:
- ✅ **可以新建**: `homepage_search.py` 文件
- ✅ **可以追加**: 在 `schemas/__init__.py` 中添加导入语句
- ❌ **不要修改**: 现有Schema文件（如 `live_core.py`, `brand.py`）
- ❌ **不要修改**: 现有模型文件

#### **3.3. SQLAlchemy 模型参考 (Existing SQLAlchemy Models)**

**文件**: `backend/live_core_service/app/models/homepage_search.py`

生成的 Pydantic Schema 必须与以下 SQLAlchemy 模型**完全对应**：

```python
"""
首页与搜索模块的数据库模型

本模块包含首页与搜索模块所需的 SQLAlchemy 模型类：
- FeaturedContent: 首页精选/焦点图表
"""
import uuid
from datetime import datetime

from sqlalchemy import Column, String, Integer, Boolean, Index, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.database import Base


class FeaturedContent(Base):
    """首页精选/焦点图内容配置表"""
    __tablename__ = "featured_content"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False, comment='焦点图标题')
    subtitle = Column(String(512), nullable=True, comment='焦点图副标题')
    image_url = Column(String(512), nullable=False, comment='焦点图图片URL')
    target_type = Column(String(50), nullable=True, comment='目标类型')
    target_id = Column(UUID(as_uuid=True), nullable=True, comment='目标ID')
    target_url = Column(String(512), nullable=True, comment='外部链接')
    sort_order = Column(Integer, default=0, nullable=False, comment='排序权重')
    is_active = Column(Boolean, default=True, nullable=False, comment='是否启用')
    start_at = Column(TIMESTAMP(timezone=True), nullable=True, comment='上线时间')
    end_at = Column(TIMESTAMP(timezone=True), nullable=True, comment='下线时间')
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
```

#### **3.4. 现有Schema文件参考 (Existing Schema Reference)**

**文件**: `backend/live_core_service/app/schemas/brand.py`

**关键观察点**（你必须遵循的风格）:

1. **Pydantic v2语法**: `model_config = ConfigDict(from_attributes=True)`
2. **Schema套件结构**: Base、Create、Update、Item/Response
3. **字段验证**: 使用 `Field` 参数（min_length、max_length、ge、le等）
4. **类型注解**: 所有字段必须有完整的类型注解
5. **文档字符串**: 每个Schema类包含中文文档字符串
6. **导入语句**: `from pydantic import BaseModel, Field, ConfigDict, field_validator`
7. **枚举类定义**: 继承 `str, Enum`

**完整示例代码**（参考现有代码风格）:

```python
"""
品牌模块的 Pydantic Schemas

本模块包含品牌模块所需的所有 Pydantic Schema 模型，用于API数据验证和序列化。
"""
import uuid
import datetime
import re
from typing import Optional, List
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict, field_validator


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


class BrandItem(BrandBase):
    """品牌响应Schema"""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID = Field(..., description="品牌ID")
    sort_order: int = Field(..., description="排序权重")
    is_active: bool = Field(..., description="是否激活")
    created_at: datetime.datetime = Field(..., description="创建时间")
    updated_at: datetime.datetime = Field(..., description="更新时间")
```

#### **3.5. 设计文档规范提取 (Design Document Specifications)**

**从设计文档中提取的API Schema规范**（Section 3）:

##### **3.5.1. 焦点图管理Schemas要求**（Section 3.1）

1. **FeaturedContentBase**:
   - `title`: str, min_length=1, max_length=255, 必需字段
   - `subtitle`: Optional[str], max_length=512
   - `image_url`: str, max_length=512, 必需字段
   - `target_type`: Optional[str], max_length=50
   - `target_id`: Optional[uuid.UUID]
   - `target_url`: Optional[str], max_length=512
   - **自定义验证器**: `image_url` 和 `target_url` 需要验证URL格式（必须以http://、https://或/开头）

2. **FeaturedContentCreate**:
   - 继承 `FeaturedContentBase`
   - `sort_order`: Optional[int], default=0, ge=0（非负整数）
   - `is_active`: Optional[bool], default=True
   - `start_at`: Optional[datetime.datetime]（上线时间）
   - `end_at`: Optional[datetime.datetime]（下线时间）
   - **不包含**: id, created_at, updated_at（由系统生成）

3. **FeaturedContentUpdate**:
   - 所有字段都是 `Optional`
   - 支持部分更新
   - **不包含**: id, created_at, updated_at

4. **FeaturedContentItem**:
   - 继承 `FeaturedContentBase`
   - 包含所有数据库字段：id, sort_order, is_active, start_at, end_at, created_at, updated_at
   - 使用 `model_config = ConfigDict(from_attributes=True)` 支持ORM对象转换

##### **3.5.2. 首页API Schemas要求**（Section 3.2）

1. **LiveStatusEnum**:
   - 枚举类型，继承 `str, Enum`
   - 值：`LIVE = 'live'`, `SCHEDULED = 'scheduled'`, `REPLAY = 'replay'`

2. **HomepageHostInfo**:
   - `expert_id`: Optional[uuid.UUID]
   - `user_id`: Optional[uuid.UUID]
   - `name`: str（必需）
   - `title`: Optional[str]（职称）
   - `hospital`: Optional[str]（医院）
   - 使用 `model_config = ConfigDict(from_attributes=True)`

3. **HomepageStatusData**:
   - `viewer_count`: Optional[int]（正在直播的观看人数）
   - `start_time`: Optional[datetime.datetime]（计划开始时间）
   - `duration_seconds`: Optional[int]（回放时长）
   - `play_count`: Optional[int]（回放播放次数）
   - 使用 `model_config = ConfigDict(from_attributes=True)`

4. **HomepageRoomItem**:
   - `id`: uuid.UUID
   - `title`: str
   - `cover_url`: Optional[str]
   - `summary`: Optional[str]
   - `live_status`: LiveStatusEnum
   - `host`: Optional[HomepageHostInfo]
   - `status_data`: HomepageStatusData
   - `heat`: Optional[int]
   - 使用 `model_config = ConfigDict(from_attributes=True)`

5. **HomepageRoomsResponse**:
   - 统一响应格式：code, message, data, timestamp
   - `code`: int = 200
   - `message`: str = "success"
   - `data`: PaginatedData[HomepageRoomItem]（需要从content_management导入PaginatedData）
   - `timestamp`: datetime.datetime

##### **3.5.3. 搜索API Schemas要求**（Section 3.3）

1. **SearchResultType**:
   - 枚举类型，继承 `str, Enum`
   - 值：`ROOM = 'room'`, `EXPERT = 'expert'`, `TOPIC = 'topic'`, `BRAND = 'brand'`

2. **SearchResultItem**:
   - `type`: SearchResultType
   - `id`: uuid.UUID
   - `title`: str
   - `summary`: Optional[str]
   - `cover_url`: Optional[str]
   - `match_score`: Optional[float], Field(None, ge=0.0, le=1.0)（匹配分数）
   - `highlight`: Optional[str]（高亮后的文本片段）
   - `metadata`: Optional[Dict[str, Any]]（类型特定的元数据）
   - 使用 `model_config = ConfigDict(from_attributes=True)`

3. **SearchResponse**:
   - 统一响应格式：code, message, data, timestamp
   - `code`: int = 200
   - `message`: str = "success"
   - `data`: PaginatedData[SearchResultItem]（需要从content_management导入PaginatedData）
   - `timestamp`: datetime.datetime

---

### **4. 代码生成具体要求 (Specific Code Generation Requirements)**

#### **4.1. 导入语句要求**

必须使用以下导入语句：

```python
"""
首页与搜索模块的 Pydantic Schemas

本模块包含首页与搜索模块所需的所有 Pydantic Schema 模型，用于API数据验证和序列化。
"""
import uuid
import datetime
import re
from typing import Optional, Dict, Any
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict, field_validator

# 导入通用分页Schema
from app.schemas.content_management import PaginatedData
```

**⚠️ 关键注意事项**（必须在代码中遵循）:
1. ✅ 标准库导入放在最前面（uuid, datetime, re）
2. ✅ 导入 `Enum` 用于枚举类定义
3. ✅ 导入 `Dict`, `Any` 用于 `metadata` 字段类型
4. ✅ **必须导入** `PaginatedData` from `app.schemas.content_management`（用于分页响应）

#### **4.2. Schema套件定义要求**

##### **4.2.1. 焦点图管理 Schemas**

```python
# ==================== 焦点图管理 Schemas ====================

class FeaturedContentBase(BaseModel):
    """焦点图基础Schema"""
    title: str = Field(..., min_length=1, max_length=255, description="焦点图标题")
    subtitle: Optional[str] = Field(None, max_length=512, description="焦点图副标题")
    image_url: str = Field(..., max_length=512, description="焦点图图片URL")
    target_type: Optional[str] = Field(None, max_length=50, description="目标类型")
    target_id: Optional[uuid.UUID] = Field(None, description="目标资源ID")
    target_url: Optional[str] = Field(None, max_length=512, description="外部链接")
    
    @field_validator('image_url', 'target_url')
    @classmethod
    def validate_url(cls, v: Optional[str]) -> Optional[str]:
        """验证URL格式"""
        if v is not None:
            v = v.strip()
            if not re.match(r'^https?://', v) and not v.startswith('/'):
                raise ValueError('URL必须以http://、https://或/开头')
        return v


class FeaturedContentCreate(FeaturedContentBase):
    """创建焦点图请求Schema"""
    sort_order: Optional[int] = Field(0, ge=0, description="排序权重")
    is_active: Optional[bool] = Field(True, description="是否启用")
    start_at: Optional[datetime.datetime] = Field(None, description="上线时间")
    end_at: Optional[datetime.datetime] = Field(None, description="下线时间")


class FeaturedContentUpdate(BaseModel):
    """更新焦点图请求Schema"""
    model_config = ConfigDict(from_attributes=True)
    
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    subtitle: Optional[str] = None
    image_url: Optional[str] = None
    target_type: Optional[str] = None
    target_id: Optional[uuid.UUID] = None
    target_url: Optional[str] = None
    sort_order: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None
    start_at: Optional[datetime.datetime] = None
    end_at: Optional[datetime.datetime] = None


class FeaturedContentItem(FeaturedContentBase):
    """焦点图响应Schema"""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    sort_order: int
    is_active: bool
    start_at: Optional[datetime.datetime] = None
    end_at: Optional[datetime.datetime] = None
    created_at: datetime.datetime
    updated_at: datetime.datetime
```

##### **4.2.2. 首页API Schemas**

```python
# ==================== 首页API Schemas ====================

class LiveStatusEnum(str, Enum):
    """直播状态枚举"""
    LIVE = 'live'
    SCHEDULED = 'scheduled'
    REPLAY = 'replay'


class HomepageHostInfo(BaseModel):
    """首页主讲人信息Schema"""
    model_config = ConfigDict(from_attributes=True)
    
    expert_id: Optional[uuid.UUID] = None
    user_id: Optional[uuid.UUID] = None
    name: str
    title: Optional[str] = None
    hospital: Optional[str] = None


class HomepageStatusData(BaseModel):
    """首页状态数据Schema"""
    model_config = ConfigDict(from_attributes=True)
    
    viewer_count: Optional[int] = None  # 正在直播的观看人数
    start_time: Optional[datetime.datetime] = None  # 计划开始时间
    duration_seconds: Optional[int] = None  # 回放时长（秒）
    play_count: Optional[int] = None  # 回放播放次数


class HomepageRoomItem(BaseModel):
    """首页直播间信息Schema"""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    title: str
    cover_url: Optional[str] = None
    summary: Optional[str] = None
    live_status: LiveStatusEnum
    host: Optional[HomepageHostInfo] = None
    status_data: HomepageStatusData
    heat: Optional[int] = None


class HomepageRoomsResponse(BaseModel):
    """首页直播间列表响应Schema"""
    code: int = 200
    message: str = "success"
    data: PaginatedData[HomepageRoomItem]
    timestamp: datetime.datetime
```

##### **4.2.3. 搜索API Schemas**

```python
# ==================== 搜索API Schemas ====================

class SearchResultType(str, Enum):
    """搜索结果类型枚举"""
    ROOM = 'room'
    EXPERT = 'expert'
    TOPIC = 'topic'
    BRAND = 'brand'


class SearchResultItem(BaseModel):
    """搜索结果项Schema"""
    model_config = ConfigDict(from_attributes=True)
    
    type: SearchResultType
    id: uuid.UUID
    title: str
    summary: Optional[str] = None
    cover_url: Optional[str] = None
    match_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="匹配分数（0-1）")
    highlight: Optional[str] = Field(None, description="高亮后的文本片段")
    metadata: Optional[Dict[str, Any]] = Field(None, description="类型特定的元数据")


class SearchResponse(BaseModel):
    """搜索响应Schema"""
    code: int = 200
    message: str = "success"
    data: PaginatedData[SearchResultItem]
    timestamp: datetime.datetime
```

#### **4.3. 字段映射规则（SQLAlchemy类型到Pydantic类型）**

- `UUID` → `uuid.UUID`
- `String(n)` → `str`（使用 `Field(max_length=n)` 限制长度）
- `Integer` → `int`（使用 `Field(ge=0)` 等限制范围）
- `Boolean` → `bool`
- `TIMESTAMP(timezone=True)` → `datetime.datetime`

#### **4.4. 字段验证要求**

1. **字符串长度验证**: `Field(..., min_length=1, max_length=255)`
2. **数值范围验证**: `Field(0, ge=0)`（非负整数）
3. **浮点数范围验证**: `Field(None, ge=0.0, le=1.0)`（匹配分数0-1）
4. **自定义验证器**: 使用 `@field_validator` 装饰器（如URL格式验证）
5. **枚举类型**: 继承 `str, Enum`

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
焦点图管理Schemas（FeaturedContentBase, FeaturedContentCreate, FeaturedContentUpdate, FeaturedContentItem）
首页API Schemas（LiveStatusEnum, HomepageHostInfo, HomepageStatusData, HomepageRoomItem, HomepageRoomsResponse）
搜索API Schemas（SearchResultType, SearchResultItem, SearchResponse）
```

**命名规范**: 
- 类名使用大驼峰命名法（PascalCase）：`FeaturedContentBase`, `HomepageRoomItem`, `SearchResponse`
- 字段名使用下划线命名法（snake_case）：`target_id`, `image_url`, `match_score`
- 枚举值使用大写（LIVE, SCHEDULED, REPLAY）

---

### **5. 完整性检查清单 (Completeness Checklist)**

生成代码后，请检查以下所有项：

**导入语句**:
- ✅ BaseModel、Field、ConfigDict、field_validator导入正确
- ✅ uuid、datetime、re、Enum、typing导入正确
- ✅ PaginatedData从content_management正确导入

**焦点图管理Schemas**:
- ✅ FeaturedContentBase定义完整（所有字段、验证器）
- ✅ FeaturedContentCreate定义完整（继承Base，包含sort_order、is_active、start_at、end_at）
- ✅ FeaturedContentUpdate定义完整（所有字段Optional，支持部分更新）
- ✅ FeaturedContentItem定义完整（包含所有数据库字段，from_attributes=True）

**首页API Schemas**:
- ✅ LiveStatusEnum定义完整（继承str, Enum，三个值）
- ✅ HomepageHostInfo定义完整（from_attributes=True）
- ✅ HomepageStatusData定义完整（from_attributes=True）
- ✅ HomepageRoomItem定义完整（from_attributes=True）
- ✅ HomepageRoomsResponse定义完整（使用PaginatedData）

**搜索API Schemas**:
- ✅ SearchResultType定义完整（继承str, Enum，四个值）
- ✅ SearchResultItem定义完整（from_attributes=True，包含metadata字段）
- ✅ SearchResponse定义完整（使用PaginatedData）

**字段验证**:
- ✅ 所有字符串字段有长度限制（max_length）
- ✅ 所有数值字段有范围限制（ge, le等）
- ✅ match_score字段有0-1范围限制
- ✅ 自定义验证器正确实现（URL格式验证）

**代码质量**:
- ✅ 所有Schema类有文档字符串
- ✅ 所有字段有description参数
- ✅ 代码遵循PEP 8规范
- ✅ 类型注解完整
- ✅ 枚举类正确继承str, Enum

**安全规范**:
- ✅ Schema定义中无硬编码的敏感信息默认值
- ✅ 字段描述中无真实的敏感信息示例
- ✅ 文档字符串中无真实的敏感信息示例

**增量开发规范**:
- ✅ 新文件创建在 `app/schemas/homepage_search.py`
- ✅ 需要在 `schemas/__init__.py` 中追加导入：`from .homepage_search import ...`
- ✅ `__init__.py` 修改为最小幅度（仅追加导入，不修改现有内容）
- ✅ 新导入格式与现有导入格式完全一致
- ✅ 无重复导入
- ✅ 无命名冲突

---

### **6. 最终交付 (Final Deliverable)**

**生成的文件**:
- `backend/live_core_service/app/schemas/homepage_search.py` - 包含所有首页与搜索模块的Pydantic Schema类

**需要手动完成的步骤**:

1. **更新 `schemas/__init__.py`**：
   在文件末尾追加导入语句：

   ```python
   # 现有代码（不要修改任何内容，包括格式、顺序、空行、注释等）
   from .live_core import LiveRoomResponse, LiveSessionResponse
   from .brand import BrandItem, BrandCreate, BrandUpdate
   # ... 其他现有导入 ...
   
   # 新增导入（追加在文件末尾，保持与现有导入格式完全一致）
   from .homepage_search import (
       FeaturedContentBase,
       FeaturedContentCreate,
       FeaturedContentUpdate,
       FeaturedContentItem,
       LiveStatusEnum,
       HomepageHostInfo,
       HomepageStatusData,
       HomepageRoomItem,
       HomepageRoomsResponse,
       SearchResultType,
       SearchResultItem,
       SearchResponse
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
5. 验证枚举类定义正确
6. 验证PaginatedData导入正确

---

**版本历史**:
- V1.0 (2026-01-18): 初始版本
