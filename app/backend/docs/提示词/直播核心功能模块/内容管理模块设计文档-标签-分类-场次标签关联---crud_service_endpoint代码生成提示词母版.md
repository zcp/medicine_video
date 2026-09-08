# 内容管理模块 - CRUD/Service/API代码生成提示词母版

**模块名称**: content_management  
**功能模块名称**: 内容管理模块设计文档-标签-分类-场次标签关联  
**版本**: V1.0  
**生成日期**: 2026-01-18  

---

## 1. 模块概述

本模块用于管理直播内容的标签(Tags)、分类(Categories)和场次标签关联(Session_Tags)。

**核心功能**:
- Tags: 全局内容标签管理（CRUD + 列表查询）
- Categories: 医学内容分类管理（CRUD + 列表查询 + 管理员分页查询）
- Session_Tags: 场次与标签的多对多关联管理

---

## 2. 项目上下文信息

### 2.1. 项目结构

```
backend/live_core_service/
├── app/
│   ├── models/
│   │   ├── __init__.py
│   │   ├── content_management.py  ✅ 已生成（步骤2）
│   │   └── ...
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── content_management.py  ✅ 已生成（步骤2）
│   │   └── ...
│   ├── crud/
│   │   ├── __init__.py
│   │   ├── content_management.py  ⏳ 待生成（步骤6）
│   │   └── ...
│   ├── services/
│   │   ├── __init__.py
│   │   ├── content_management_service.py  ⏳ 待生成（步骤6）
│   │   └── ...
│   └── api/
│       └── v1/
│           ├── api.py  ⏳ 需更新路由注册（步骤6）
│           └── endpoints/
│               ├── __init__.py
│               ├── content_management.py  ⏳ 待生成（步骤6）
│               └── ...
```

### 2.2. 设计文档路径

**主设计文档**: `docs/03_系统设计/直播核心功能设计文档_v6_内容管理模块设计文档-标签-分类-场次标签关联.md`

**依赖的权限设计文档**: `docs/03_系统设计/直播核心功能设计文档_v6_增加专题功能权限管理增量设计版.md`

**依赖的安全配置文档**: `docs/03_系统设计/直播核心功能设计文档----配置与安全优化方案.md`

---

## 3. Model 字段摘要（基于实际代码）

### 3.1. Tag 模型

**文件路径**: `backend/live_core_service/app/models/content_management.py`

**表名**: `tags`

**字段摘要**:
| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|--------|------|------|--------|------|
| `id` | UUID | PRIMARY KEY | uuid.uuid4() | 标签ID |
| `name` | String(80) | NOT NULL, UNIQUE | - | 标签名称，全局唯一 |
| `slug` | String(100) | NULLABLE | NULL | URL友好标识符 |
| `description` | Text | NULLABLE | NULL | 标签描述 |
| `is_active` | Boolean | NOT NULL | True | 是否启用（软删除字段） |
| `created_at` | TIMESTAMP(TZ) | NOT NULL | func.now() | 创建时间 |
| `updated_at` | TIMESTAMP(TZ) | NOT NULL | func.now() | 更新时间（自动更新） |

**索引**:
- `idx_tags_name` (name)
- `idx_tags_is_active` (is_active)

**关系**:
- `session_tags`: relationship("SessionTag", cascade="all, delete-orphan")

**验证规则**（在Schema层实现）:
- `name`: 必须不包含特殊字符 `<>'";`
- `slug`: 只能包含小写字母、数字和连字符 `^[a-z0-9-]+$`

---

### 3.2. Category 模型

**文件路径**: `backend/live_core_service/app/models/content_management.py`

**表名**: `categories`

**字段摘要**:
| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|--------|------|------|--------|------|
| `id` | UUID | PRIMARY KEY | uuid.uuid4() | 分类ID |
| `name` | String(100) | NOT NULL, UNIQUE | - | 分类名称，全局唯一 |
| `slug` | String(120) | NULLABLE | NULL | URL友好标识符 |
| `icon` | String(255) | NULLABLE | NULL | 图标名称或URL |
| `description` | Text | NULLABLE | NULL | 分类描述 |
| `sort_order` | Integer | NOT NULL | 0 | 排序权重，数字越小越靠前 |
| `is_active` | Boolean | NOT NULL | True | 是否启用（软删除字段） |
| `created_at` | TIMESTAMP(TZ) | NOT NULL | func.now() | 创建时间 |
| `updated_at` | TIMESTAMP(TZ) | NOT NULL | func.now() | 更新时间（自动更新） |

**索引**:
- `idx_categories_sort_order` (sort_order)
- `idx_categories_is_active` (is_active)
- `idx_categories_active_sort` (is_active, sort_order WHERE is_active=true) - 部分索引，需在DDL中定义

**验证规则**（在Schema层实现）:
- `name`: 必须不包含特殊字符 `<>'";`

---

### 3.3. SessionTag 模型

**文件路径**: `backend/live_core_service/app/models/content_management.py`

**表名**: `session_tags`

**字段摘要**:
| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|--------|------|------|--------|------|
| `session_id` | UUID | PRIMARY KEY, FK(live_sessions.id, CASCADE) | - | 场次ID |
| `tag_id` | UUID | PRIMARY KEY, FK(tags.id, CASCADE) | - | 标签ID |
| `created_at` | TIMESTAMP(TZ) | NOT NULL | func.now() | 创建时间 |

**主键**: 复合主键 (session_id, tag_id)

**索引**:
- `idx_session_tags_session_id` (session_id)
- `idx_session_tags_tag_id` (tag_id)

**关系**:
- `tag`: relationship("Tag", back_populates="session_tags")
- `session`: relationship("LiveSession", foreign_keys=[session_id])

**删除策略**: 硬删除（直接DELETE）

---

## 4. Schema 摘要（基于实际代码）

### 4.1. Tags Schemas

**文件路径**: `backend/live_core_service/app/schemas/content_management.py`

#### 4.1.1. TagBase
- **用途**: 标签基础Schema
- **字段**: name (str, 1-80), slug (Optional[str], max 100), description (Optional[str], max 500)
- **验证器**: 
  - `validate_name`: 不包含特殊字符 `<>'";`
  - `validate_slug`: 只能包含小写字母、数字和连字符

#### 4.1.2. TagCreate
- **用途**: 创建标签请求
- **继承**: TagBase
- **新增字段**: is_active (Optional[bool], default True)

#### 4.1.3. TagUpdate
- **用途**: 更新标签请求（部分更新）
- **字段**: 所有字段均为Optional
- **配置**: `from_attributes=True`

#### 4.1.4. TagItem
- **用途**: 标签响应Schema
- **继承**: TagBase
- **新增字段**: id (UUID), is_active (bool), created_at (datetime), updated_at (datetime)
- **配置**: `from_attributes=True`

#### 4.1.5. TagListResponse
- **用途**: 标签列表响应
- **字段**: code (int, 200), message (str, "success"), data (List[TagItem]), timestamp (datetime)

---

### 4.2. Categories Schemas

**文件路径**: `backend/live_core_service/app/schemas/content_management.py`

#### 4.2.1. CategoryBase
- **用途**: 分类基础Schema
- **字段**: name (str, 1-100), slug (Optional[str], max 120), icon (Optional[str], max 255), description (Optional[str], max 500)
- **验证器**: `validate_name`: 不包含特殊字符 `<>'";`

#### 4.2.2. CategoryCreate
- **用途**: 创建分类请求
- **继承**: CategoryBase
- **新增字段**: sort_order (Optional[int], default 0, ≥0), is_active (Optional[bool], default True)

#### 4.2.3. CategoryUpdate
- **用途**: 更新分类请求（部分更新）
- **字段**: 所有字段均为Optional
- **配置**: `from_attributes=True`

#### 4.2.4. CategoryItem
- **用途**: 分类响应Schema
- **继承**: CategoryBase
- **新增字段**: id (UUID), sort_order (int), is_active (bool), created_at (datetime), updated_at (datetime)
- **配置**: `from_attributes=True`

#### 4.2.5. CategoryListResponse
- **用途**: 分类列表响应（公开接口，不分页）
- **字段**: code (int, 200), message (str, "success"), data (List[CategoryItem]), timestamp (datetime)

#### 4.2.6. PaginatedData[T]
- **用途**: 通用分页数据Schema（Generic类型）
- **字段**: total (int), page (int), size (int), items (List[T])

#### 4.2.7. CategoryAdminListResponse
- **用途**: 分类列表响应（Admin接口，分页）
- **字段**: code (int, 200), message (str, "success"), data (PaginatedData[CategoryItem]), timestamp (datetime)

---

### 4.3. Session_Tags Schemas

**文件路径**: `backend/live_core_service/app/schemas/content_management.py`

#### 4.3.1. SessionTagsSetRequest
- **用途**: 为场次设置标签请求
- **字段**: 
  - tag_ids (List[UUID], 1-50个)
  - mode (Literal["replace", "append"])
- **验证器**: `validate_tag_ids_unique`: 确保标签ID列表无重复

#### 4.3.2. TagBriefItem
- **用途**: 标签简要信息（用于关联响应）
- **字段**: id (UUID), name (str)
- **配置**: `from_attributes=True`

#### 4.3.3. SessionTagsSetResponse
- **用途**: 场次标签设置响应
- **字段**: code (int, 200), message (str, "success"), data (dict), timestamp (datetime)
- **data结构**: `{"session_id": "...", "mode": "replace", "tags": [...]}`

#### 4.3.4. SessionTagsListResponse
- **用途**: 场次标签列表响应
- **字段**: code (int, 200), message (str, "success"), data (List[TagItem]), timestamp (datetime)

---

## 5. 架构规范引用

### 5.1. Clean Architecture 分层架构

本模块遵循Clean Architecture分层架构，详见母版文档第3节。

**核心原则**:
- CRUD层：数据访问层，仅负责数据库操作
- Service层：业务逻辑层，负责业务编排和权限检查
- Endpoint层：HTTP端点层，负责请求解析和响应构造

**依赖方向**: Endpoint → Service → CRUD → Models

### 5.2. 权限设计规范

本模块遵循统一的权限设计规范，详见母版文档第5节和权限设计文档。

**核心原则**:
- 双轨鉴权模式：Strict Auth（写操作） + Optional Auth（读操作）
- Service层负责权限检查（不在Endpoint层检查）
- CRUD层负责SQL级权限过滤（where条件）
- 404伪装机制：未授权资源返回404而非403

**权限守卫函数**（在Service层实现）:
- `_check_admin_permission(role: str)`: 管理员权限检查
- `_check_write_permission(role: str)`: 写权限检查
- `_check_tag_visibility(tag: Tag, current_user_id: Optional[UUID], role: Optional[str])`: 标签可见性检查

**适用场景**:
- Tags: 
  - 创建/更新/删除标签: 需要管理员权限（`_check_admin_permission`）
  - 查询标签: 需要过滤`is_active=True`（公开接口）或无过滤（管理员接口）
- Categories: 
  - 创建/更新/删除分类: 需要管理员权限
  - 查询分类: 公开接口按`sort_order`排序并过滤`is_active=True`，管理员接口支持分页和无过滤
- Session_Tags:
  - 设置场次标签: 需要写权限（`_check_write_permission`）
  - 查询场次标签: 公开接口，无需权限

### 5.3. 全项目通用安全与一致性规范（最高优先级）

本模块**必须**严格遵循母版文档"5.2 全项目通用安全与一致性规范"的所有要求，详见母版文档第891-1213行。

#### 5.3.1. 安全异步异常处理规范

**🚨 [强制要求] 安全异步异常处理（最高优先级）**：

- **规则**：在任何 `try...except` 块中，如果需要使用来自 ORM 对象（如 `current_user`）的属性（如 `current_user.id`）进行日志记录，这些属性**必须在进入 `try` 块之前**被提取并存储到局部变量中。
- **指令**：**严禁**在捕获了数据库相关异常的 `except` 块中访问可能已失效会话的 ORM 对象的属性。

**✅ 正确示例**：
```python
# API层端点
async def create_tag(
    tag_data: TagCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    # 🚨 必须在try块之前提取属性
    current_user_id = UUID(current_user["user_id"])
    role = current_user.get("role", "REGULAR").upper()
    user_id_for_logging = str(current_user_id)[:8]  # ✅ 提前提取
    
    try:
        result = await service.create_tag(db, tag_data, current_user_id, role)
        return result
    except Exception as e:
        logger.error(f"创建标签异常: user_id={user_id_for_logging}, error={str(e)}")  # ✅ 使用提前提取的变量
        return JSONResponse(...)
```

**❌ 错误示例**：
```python
try:
    result = await service.create_tag(...)
except Exception as e:
    user_id = current_user["user_id"]  # ❌ 在except块中访问ORM对象属性
    logger.error(f"创建标签异常: user_id={user_id}, error={str(e)}")
```

#### 5.3.2. 内部ID不得对外暴露规范

**🚨 [强制要求] 内部ID不得对外暴露（最高优先级）**：

- 所有对外 API 的 Response Schema 中，**禁止**直接暴露数据库内部主键（如 `id`, `user_id`）。
- 对外唯一标识统一使用 `public_id` 或业务编号。

**✅ 正确示例**：
```python
# API Schema（对外）
class TagItem(BaseModel):
    public_id: str  # ✅ 使用public_id
    name: str
    # ❌ 禁止暴露内部id字段
```

**❌ 错误示例**：
```python
# API Schema（对外）
class TagItem(BaseModel):
    id: UUID  # ❌ 禁止暴露内部主键
    name: str
```

#### 5.3.3. API Schema 与内部 CRUD Schema 严格区分规范

**🚨 [强制要求] API Schema 与内部 CRUD Schema 严格区分（最高优先级）**：

1. **API 输入/输出 Schema** (对外边界，安全优先):
   - **不得包含**任何内部控制字段或敏感字段（如 `role`, `is_admin`, `password_hash`, `user_id` 等）。

2. **内部 CRUD Schema** (仅服务内部使用):
   - 示例: `TagCreateInternal`
   - 用途: 封装 Service / CRUD 层写入数据库所需的**完整字段集合**（可包含 `role`, `user_id` 等）。
   - 约束: **禁止**在 API 路由函数中直接作为请求体暴露给外部。

**✅ 正确示例**：
```python
# API Schema（对外）
class TagCreate(BaseModel):
    name: str
    slug: Optional[str] = None
    description: Optional[str] = None
    # ❌ 禁止包含role、user_id等内部字段

# 内部 CRUD Schema（内部使用）
class TagCreateInternal(BaseModel):
    name: str
    slug: Optional[str] = None
    description: Optional[str] = None
    user_id: UUID  # ✅ 内部Schema可以包含
    role: str  # ✅ 内部Schema可以包含
```

#### 5.3.4. Enum 字段声明规范

**🚨 [强制要求] Enum 字段声明规范（最高优先级）**：

- **必须**使用 Python `enum.Enum` 类，并配合 `sqlalchemy.Enum`。
- **必须**使用 `native_enum=False`（除非有特殊原因），并显式声明：

**✅ 正确示例**：
```python
from sqlalchemy import Column, Enum as SQLEnum
from enum import Enum

class TagStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"

class Tag(Base):
    status = Column(
        SQLEnum(TagStatus, native_enum=False),  # ✅ 必须使用native_enum=False
        nullable=False,
        default=TagStatus.ACTIVE
    )
```

#### 5.3.5. 环境变量驱动配置规范

**🚨 [强制要求] 环境变量驱动配置规范（最高优先级）**：

- **禁止**在代码中硬编码敏感信息（如数据库密码、JWT密钥、CORS配置等）。
- **必须**通过环境变量读取所有敏感配置。
- **禁止**为敏感信息设置不安全的默认值。

**✅ 正确示例**：
```python
# config.py
POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "")  # ✅ 空字符串作为默认值
JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "")  # ✅ 空字符串作为默认值
CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "*")  # ✅ 从环境变量读取
```

**❌ 错误示例**：
```python
# ❌ 错误：硬编码敏感信息
POSTGRES_PASSWORD = "CHANGE_ME"  # ❌ 禁止
JWT_SECRET_KEY = "my-key"  # ❌ 禁止

# ❌ 错误：不安全的默认值
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "default_password")  # ❌ 禁止
```

#### 5.3.6. RESTful API 设计原则

**🚨 [强制要求] RESTful API 设计原则（最高优先级）**：

- **资源导向**：API路径应该表示资源（如 `/tags`, `/categories`），而非操作（如 `/get_tags`, `/create_tag`）。
- **层次结构**：使用嵌套路径表示资源关系（如 `/sessions/{session_id}/tags`）。
- **HTTP 方法**：使用标准HTTP方法（GET、POST、PUT、DELETE）表示操作。
- **状态码**：使用标准HTTP状态码（200、201、400、404、500等）。

**✅ 正确示例**：
```python
# ✅ 资源导向
GET /api/v1/tags  # 获取标签列表
POST /api/v1/tags  # 创建标签
PUT /api/v1/tags/{tag_id}  # 更新标签
DELETE /api/v1/tags/{tag_id}  # 删除标签

# ✅ 层次结构
GET /api/v1/sessions/{session_id}/tags  # 获取场次标签
POST /api/v1/sessions/{session_id}/tags  # 为场次设置标签
```

**❌ 错误示例**：
```python
# ❌ 操作导向
GET /api/v1/get_tags  # ❌ 禁止
POST /api/v1/create_tag  # ❌ 禁止

# ❌ 非标准HTTP方法
GET /api/v1/tags/delete/{tag_id}  # ❌ 禁止，应使用DELETE方法
```

#### 5.3.7. 日志与错误消息脱敏规范

**核心要求**:
- **日志脱敏**：日志中不记录用户敏感信息（如完整UUID，只记录前8位）
- **错误消息脱敏**：错误消息不暴露内部实现细节
- **输入验证**：所有用户输入通过Pydantic验证，防止XSS和SQL注入

**✅ 正确示例**：
```python
# ✅ 日志脱敏
logger.info(f"创建标签成功: id={str(tag_id)[:8]}")  # ✅ 只记录前8位

# ✅ 错误消息脱敏
except Exception as e:
    logger.error(f"创建标签失败: {type(e).__name__}")  # ✅ 不暴露完整异常信息
    return JSONResponse(
        status_code=500,
        content=error_response(code=1002, message="内部服务器错误")  # ✅ 通用错误消息
    )
```

**❌ 错误示例**：
```python
# ❌ 日志暴露敏感信息
logger.info(f"创建标签成功: id={tag_id}")  # ❌ 暴露完整UUID

# ❌ 错误消息暴露内部实现
except Exception as e:
    return JSONResponse(
        status_code=500,
        content=error_response(code=1002, message=str(e))  # ❌ 暴露完整异常信息
    )
```

---

## 6. 待生成的代码清单

本模块需要生成3个代码文件：

### 6.1. CRUD层代码

**文件路径**: `backend/live_core_service/app/crud/content_management.py`

**需要生成的函数**（基于设计文档的API接口清单）:

#### Tags CRUD 函数
1. `async def get_tags(db: AsyncSession, is_active: Optional[bool], current_user_id: Optional[UUID], role: Optional[str]) -> List[Tag]`
   - 获取标签列表，支持按`is_active`过滤
   - 管理员可查询所有标签，普通用户只能查询`is_active=True`的标签

2. `async def create_tag(db: AsyncSession, tag_data: TagCreate) -> Tag`
   - 创建标签
   - 需检查`name`唯一性（IntegrityError处理）

3. `async def update_tag(db: AsyncSession, tag_id: UUID, tag_data: TagUpdate) -> Optional[Tag]`
   - 更新标签（部分更新）
   - 需检查`name`唯一性（如果更新了name字段）

4. `async def delete_tag(db: AsyncSession, tag_id: UUID) -> bool`
   - 删除标签（软删除：is_active=False）
   - 返回True/False表示是否成功

#### Categories CRUD 函数
5. `async def get_categories(db: AsyncSession, current_user_id: Optional[UUID], role: Optional[str]) -> List[Category]`
   - 获取分类列表（公开接口，按sort_order排序，只返回is_active=True）

6. `async def get_categories_paginated(db: AsyncSession, page: int, size: int, is_active: Optional[bool], current_user_id: Optional[UUID], role: Optional[str]) -> Tuple[List[Category], int]`
   - 获取分类列表（管理员接口，分页，支持按is_active过滤）
   - 返回: (items, total)

7. `async def create_category(db: AsyncSession, category_data: CategoryCreate) -> Category`
   - 创建分类
   - 需检查`name`唯一性

8. `async def update_category(db: AsyncSession, category_id: UUID, category_data: CategoryUpdate) -> Optional[Category]`
   - 更新分类（部分更新）
   - 需检查`name`唯一性（如果更新了name字段）

9. `async def delete_category(db: AsyncSession, category_id: UUID) -> bool`
   - 删除分类（软删除：is_active=False）

10. `async def get_category_by_id(db: AsyncSession, category_id: UUID) -> Optional[Category]`
    - 根据ID获取分类（用于更新和删除时的验证）

#### Session_Tags CRUD 函数
11. `async def set_session_tags(db: AsyncSession, session_id: UUID, tag_ids: List[UUID], mode: str) -> List[Tag]`
    - 为场次设置标签
    - mode="replace": 先删除所有现有关联，再创建新关联
    - mode="append": 只追加新关联（如已存在则忽略）
    - 返回设置后的标签列表（包含完整的Tag对象）

12. `async def get_tags_by_session_id(db: AsyncSession, session_id: UUID) -> List[Tag]`
    - 根据场次ID获取标签列表
    - 只返回`is_active=True`的标签

13. `async def get_sessions_by_tags(db: AsyncSession, tag_ids: List[UUID], match_all: bool) -> List[UUID]`
    - 根据标签查询场次ID列表
    - match_all=True: AND逻辑（场次必须包含所有指定标签）
    - match_all=False: OR逻辑（场次包含任一指定标签即可）

14. `async def remove_session_tag(db: AsyncSession, session_id: UUID, tag_id: UUID) -> bool`
    - 删除场次与标签的关联（硬删除）

---

### 6.2. Service层代码

**文件路径**: `backend/live_core_service/app/services/content_management_service.py`

**需要生成的类**: `ContentManagementService`

**需要生成的方法**:

#### 权限守卫函数
1. `def _check_admin_permission(self, role: Optional[str]) -> None`
   - 检查管理员权限（ADMIN或SUPERADMIN，🚨 必须使用大写）
   - 如果无权限，抛出`PermissionDeniedException`

2. `def _check_write_permission(self, role: Optional[str]) -> None`
   - 检查写权限（REGULAR、ADMIN或SUPERADMIN，🚨 必须使用大写，使用REGULAR而非user）
   - 如果无权限，抛出`PermissionDeniedException`

3. `def _check_tag_visibility(self, tag: Tag, current_user_id: Optional[UUID], role: Optional[str]) -> None`
   - 检查标签可见性
   - 如果tag.is_active=False且不是管理员，抛出`NotFoundException`（404伪装）

#### Tags Service 方法
4. `async def get_tags_list(self, db: AsyncSession, current_user_id: Optional[UUID], role: Optional[str]) -> TagListResponse`
   - 获取标签列表
   - 权限检查: 管理员可查询所有标签，普通用户只能查询`is_active=True`的标签

5. `async def create_tag(self, db: AsyncSession, tag_data: TagCreate, current_user_id: UUID, role: str) -> TagItem`
   - 创建标签
   - 权限检查: `_check_admin_permission(role)`

6. `async def update_tag(self, db: AsyncSession, tag_id: UUID, tag_data: TagUpdate, current_user_id: UUID, role: str) -> TagItem`
   - 更新标签
   - 权限检查: `_check_admin_permission(role)`
   - 404检查: tag不存在抛出`NotFoundException`

7. `async def delete_tag(self, db: AsyncSession, tag_id: UUID, current_user_id: UUID, role: str) -> dict`
   - 删除标签（软删除）
   - 权限检查: `_check_admin_permission(role)`
   - 404检查: tag不存在抛出`NotFoundException`

#### Categories Service 方法
8. `async def get_categories_list(self, db: AsyncSession, current_user_id: Optional[UUID], role: Optional[str]) -> CategoryListResponse`
   - 获取分类列表（公开接口，不分页）
   - 自动过滤`is_active=True`，按`sort_order`排序

9. `async def get_categories_paginated(self, db: AsyncSession, page: int, size: int, is_active: Optional[bool], current_user_id: UUID, role: str) -> CategoryAdminListResponse`
   - 获取分类列表（管理员接口，分页）
   - 权限检查: `_check_admin_permission(role)`

10. `async def create_category(self, db: AsyncSession, category_data: CategoryCreate, current_user_id: UUID, role: str) -> CategoryItem`
    - 创建分类
    - 权限检查: `_check_admin_permission(role)`

11. `async def update_category(self, db: AsyncSession, category_id: UUID, category_data: CategoryUpdate, current_user_id: UUID, role: str) -> CategoryItem`
    - 更新分类
    - 权限检查: `_check_admin_permission(role)`
    - 404检查: category不存在抛出`NotFoundException`

12. `async def delete_category(self, db: AsyncSession, category_id: UUID, current_user_id: UUID, role: str) -> dict`
    - 删除分类（软删除）
    - 权限检查: `_check_admin_permission(role)`
    - 404检查: category不存在抛出`NotFoundException`

#### Session_Tags Service 方法
13. `async def set_session_tags(self, db: AsyncSession, session_id: UUID, request_data: SessionTagsSetRequest, current_user_id: UUID, role: str) -> SessionTagsSetResponse`
    - 为场次设置标签
    - 权限检查: `_check_write_permission(role)`
    - 业务验证: 检查tag_ids是否存在，检查session_id是否存在

14. `async def get_session_tags(self, db: AsyncSession, session_id: UUID, current_user_id: Optional[UUID], role: Optional[str]) -> SessionTagsListResponse`
    - 获取场次标签列表
    - 无需权限检查（公开接口）

15. `async def get_sessions_by_tags(self, db: AsyncSession, tag_ids: List[UUID], match_all: bool, current_user_id: Optional[UUID], role: Optional[str]) -> List[UUID]`
    - 根据标签查询场次ID列表
    - 无需权限检查（公开接口）

16. `async def remove_session_tag(self, db: AsyncSession, session_id: UUID, tag_id: UUID, current_user_id: UUID, role: str) -> dict`
    - 删除场次与标签的关联
    - 权限检查: `_check_write_permission(role)`

---

### 6.3. API层代码

**文件路径**: `backend/live_core_service/app/api/v1/endpoints/content_management.py`

**需要生成的端点**（基于设计文档的API接口清单）:

#### Tags 端点
1. `GET /api/v1/tags` - 获取标签列表（Public + Optional Auth）
2. `POST /api/v1/tags` - 创建标签（Strict Auth + Admin）
3. `PUT /api/v1/tags/{tag_id}` - 更新标签（Strict Auth + Admin）
4. `DELETE /api/v1/tags/{tag_id}` - 删除标签（Strict Auth + Admin）

#### Categories 端点
5. `GET /api/v1/categories` - 获取分类列表（Public + Optional Auth，不分页）
6. `GET /api/v1/categories/admin` - 获取分类列表（Admin接口，分页）
7. `POST /api/v1/categories` - 创建分类（Strict Auth + Admin）
8. `PUT /api/v1/categories/{category_id}` - 更新分类（Strict Auth + Admin）
9. `DELETE /api/v1/categories/{category_id}` - 删除分类（Strict Auth + Admin）
10. `GET /api/v1/categories/{category_id}` - 根据ID获取分类（Public + Optional Auth）

#### Session_Tags 端点
11. `POST /api/v1/sessions/{session_id}/tags` - 为场次设置标签（Strict Auth + Write）
12. `GET /api/v1/sessions/{session_id}/tags` - 获取场次标签列表（Public + Optional Auth）
13. `GET /api/v1/tags/search/sessions?tag_ids=...&match_all=...` - 根据标签查询场次（Public + Optional Auth）
14. `DELETE /api/v1/sessions/{session_id}/tags/{tag_id}` - 删除场次标签关联（Strict Auth + Write）

**端点规范**:
- 所有端点使用`APIRouter`（**严禁**指定`prefix`，`prefix`必须在顶层`api/v1/api.py`中统一指定）
- Strict Auth端点使用`Depends(get_current_user)`
- Optional Auth端点使用`Depends(get_current_user_optional)`
- 所有响应返回标准化格式（code, message, data, timestamp）
- 所有端点添加详细的docstring和`summary`、`description`参数
- **🚨 API层异常处理（强制要求，最高优先级）**：
  - 所有端点必须在try块之前提取并转换role：`role = current_user.get("role", "REGULAR").upper()`
  - 所有端点必须在try块之前提取`user_id_for_logging = str(current_user_id)[:8]`
  - 所有端点必须添加完整的异常处理（try-except），捕获Service层抛出的异常并转换为`JSONResponse`
  - **必须**导入`JSONResponse`和`error_response`：`from fastapi.responses import JSONResponse`，`from app.core.response import error_response`
  - **禁止**使用`raise HTTPException`，**必须**使用`JSONResponse` + `error_response()`
  - 必须捕获通用`Exception`并返回500错误

---

## 7. 关键约束和注意事项

### 7.1. 唯一性约束处理
- `Tag.name` 和 `Category.name` 具有唯一性约束
- 创建和更新时需捕获`IntegrityError`，转换为`DatabaseIntegrityException`

### 7.2. 软删除 vs 硬删除
- `Tag` 和 `Category`: 软删除（is_active=False）
- `SessionTag`: 硬删除（直接DELETE）

### 7.3. 权限模型
- **管理员权限**: `role in ['ADMIN', 'SUPERADMIN']`（🚨 必须使用大写）
- **写权限**: `role in ['REGULAR', 'ADMIN', 'SUPERADMIN']`（🚨 必须使用大写，使用REGULAR而非user）
- **读权限**: 无需权限（公开接口）或Optional Auth（返回不同数据）

**🚨 角色值大小写强制要求（最高优先级）**：
- **API层**：必须调用`.upper()`转换role为大写：`role = current_user.get("role", "REGULAR").upper()`
- **Service层**：必须使用大写`['ADMIN', 'SUPERADMIN']`或`['REGULAR', 'ADMIN', 'SUPERADMIN']`进行角色比较
- **CRUD层**：必须使用大写`['ADMIN', 'SUPERADMIN']`进行SQL级权限过滤
- **禁止**使用小写（如`'admin'`, `'superadmin'`）和混合大小写（如`'Admin'`, `'SuperAdmin'`）
- **禁止**使用`'user'`，应使用`'REGULAR'`

### 7.4. 响应构造规范
- Service层返回的响应必须符合Schema定义的嵌套结构
- 标准字段: `code`, `message`, `data`, `timestamp`
- `data`字段的结构必须与Schema定义完全一致

### 7.5. 日志记录规范
- 所有CRUD操作记录日志（INFO级别）
- UUID只记录前8位（脱敏）
- 错误日志记录完整堆栈（ERROR级别）

### 7.6. 导入路径
- Models: `from app.models.content_management import Tag, Category, SessionTag`
- Schemas: `from app.schemas.content_management import TagCreate, TagUpdate, ...`
- CRUD: `from app.crud.content_management import get_tags, create_tag, ...`
- Service: `from app.services.content_management_service import ContentManagementService`
- Exceptions: `from app.core.exceptions import NotFoundException, PermissionDeniedException, DatabaseIntegrityException, InvalidParameterException`
- Deps: `from app.database import get_db`，`from app.core.deps import get_current_user, get_current_user_optional`
- API层必须导入: `from fastapi.responses import JSONResponse`，`from app.core.response import success_response, error_response`，`from app.exceptions import PermissionDeniedException, NotFoundException, InvalidParameterException`，`import logging`

### 7.7. API层异常处理规范（🚨 强制要求，最高优先级）

**所有API端点必须遵循以下完整模板**：

```python
from fastapi import APIRouter, Depends, Query, Path
from fastapi.responses import JSONResponse
from app.exceptions import PermissionDeniedException, NotFoundException, InvalidParameterException
from app.core.response import success_response, error_response
import logging

logger = logging.getLogger(__name__)

@router.post("/tags", ...)
async def create_tag(
    tag_data: TagCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> Any:
    """创建标签（Strict Auth + Admin）"""
    # 🚨 必须：在try块之前提取并转换role
    current_user_id = UUID(current_user["user_id"])
    role = current_user.get("role", "REGULAR").upper()  # ✅ 必须调用.upper()
    user_id_for_logging = str(current_user_id)[:8]
    
    try:
        # 调用Service层
        result = await service.create_tag(db, tag_data, current_user_id, role)
        return result  # Service层返回的响应对象
    except PermissionDeniedException as e:
        logger.warning(f"权限不足: user_id={user_id_for_logging}, role={role}")
        return JSONResponse(
            status_code=403,
            content=error_response(code=3003, message="权限不足")
        )
    except NotFoundException as e:
        logger.warning(f"资源不存在: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=404,
            content=error_response(code=2001, message="资源不存在")
        )
    except InvalidParameterException as e:
        logger.warning(f"参数验证失败: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=400,
            content=error_response(code=4001, message=str(e))
        )
    except Exception as e:
        logger.error(f"创建标签异常: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="内部服务器错误")
        )
```

**❌ 错误示例（禁止使用）**：
```python
# ❌ 错误1：缺少.upper()调用
role = current_user.get("role")  # ❌

# ❌ 错误2：缺少异常处理
return await service.create_tag(...)  # ❌ 直接返回，没有try-except

# ❌ 错误3：在try块内提取role
try:
    role = current_user.get("role")  # ❌ 应该在try之前提取

# ❌ 错误4：使用HTTPException
raise HTTPException(status_code=403, detail=str(e))  # ❌ 禁止使用
```

**✅ 正确示例（必须使用）**：
```python
# ✅ 正确：完整的端点实现
async def create_tag(...):
    # 🚨 必须在try之前提取user_id和role
    current_user_id = UUID(current_user["user_id"])
    role = current_user.get("role", "REGULAR").upper()  # ✅
    user_id_for_logging = str(current_user_id)[:8]
    
    try:
        result = await service.create_tag(db, tag_data, current_user_id, role)
        return result
    except PermissionDeniedException as e:
        logger.warning(f"权限不足: user_id={user_id_for_logging}, role={role}")
        return JSONResponse(
            status_code=403,
            content=error_response(code=3003, message="权限不足")
        )
    except NotFoundException as e:
        logger.warning(f"资源不存在: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=404,
            content=error_response(code=2001, message="资源不存在")
        )
    except InvalidParameterException as e:
        logger.warning(f"参数验证失败: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=400,
            content=error_response(code=4001, message=str(e))
        )
    except Exception as e:
        logger.error(f"创建标签异常: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="内部服务器错误")
        )
```

**🚨 强制检查清单（每个端点必须验证）**：
- [ ] 是否在try块之前提取了`user_id`和`role`？
- [ ] 是否调用了`.upper()`转换role为大写？
- [ ] 是否提取了`user_id_for_logging`？
- [ ] 是否添加了完整的异常处理（try-except）？
- [ ] 是否捕获了`PermissionDeniedException`并使用`JSONResponse`+`error_response()`返回403？
- [ ] 是否捕获了`NotFoundException`并使用`JSONResponse`+`error_response()`返回404？
- [ ] 是否捕获了`InvalidParameterException`并使用`JSONResponse`+`error_response()`返回400？
- [ ] 是否捕获了通用`Exception`并使用`JSONResponse`+`error_response()`返回500？
- [ ] 是否导入了`JSONResponse`和`error_response`？
- [ ] 是否禁止使用`raise HTTPException`？

---

## 8. 执行指引

### 8.1. 如何使用本母版文档

本母版文档用于生成2个具体的提示词文档：

1. **CRUD层代码生成提示词文档**（步骤4.2.1）
   - 包含第6.1节的所有CRUD函数
   - 包含第3节的Model字段摘要
   - 包含第7节的关键约束

2. **Service层和API层代码生成提示词文档**（步骤4.2.2）
   - 包含第6.2节的所有Service方法
   - 包含第6.3节的所有API端点
   - 包含第4节的Schema摘要
   - 包含第5节的架构规范引用
   - 包含第7节的关键约束

### 8.2. 信息完整性保证

本母版文档已从实际代码中提取了完整的字段摘要：
- ✅ 所有Model字段已列出（字段名、类型、约束）
- ✅ 所有Schema类已列出（类名、主要字段、响应结构）
- ✅ 所有必要的方法签名已明确（参数类型、返回类型）
- ✅ 严禁猜测：所有信息均来自实际代码或设计文档
- ✅ **API-Service对应关系验证**（必须严格执行）：
  * 第6.2节"Service层代码"方法清单和第6.3节"API层代码"端点清单已生成后，**必须执行对应关系验证**
  * 对于每个API端点，验证第6.2节中是否有对应的Service方法（排除权限守卫函数如`_check_*`）
  * 如果发现API端点缺少对应的Service方法，**必须在第6.2节中补充**
  * 如果发现Service方法缺少对应的API端点，检查是否为权限守卫函数或内部方法，否则需要说明原因
  * 验证完成后，确保API端点数量和Service方法数量（排除权限守卫函数）保持一致

### 8.3. 后续步骤

1. **步骤4.2.1**: 使用本母版生成CRUD层代码生成提示词
2. **步骤4.2.2**: 使用本母版生成Service/API层代码生成提示词
3. **步骤5**: 一致性检测（提示词文档 vs 设计文档）
4. **步骤6**: 生成实际代码（CRUD/Service/API）

---

**版本历史**:
- V1.0 (2026-01-18): 初始版本，包含完整的Model和Schema字段摘要，符合V2.4流程规范


