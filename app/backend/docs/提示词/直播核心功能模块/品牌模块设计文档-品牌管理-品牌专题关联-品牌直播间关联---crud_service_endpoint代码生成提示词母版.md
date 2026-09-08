# 品牌模块 - CRUD/Service/API代码生成提示词母版

**模块名称**: brand  
**功能模块名称**: 品牌模块设计文档-品牌管理-品牌专题关联-品牌直播间关联  
**版本**: V1.1  
**生成日期**: 2026-01-18  

---

## 1. 模块概述

本模块用于管理合作品牌信息、品牌与专题的关联关系、品牌与直播间的关联关系。

**核心功能**:
- Brands: 品牌/合作伙伴信息管理（CRUD + 列表查询 + 管理员分页查询）
- Brand_Topics: 品牌与专题的多对多关联管理（批量关联、解除关联、查询关联）
- Brand_Rooms: 品牌与直播间的多对多关联管理（绑定品牌、查询绑定、公开展示）

**业务特点**:
- 品牌信息是公开资源，所有用户（包括匿名用户）都可以访问
- 所有写操作（创建、更新、删除、关联管理）都需要管理员权限
- 品牌与专题/直播间采用多对多关联设计

---

## 2. 项目上下文信息

### 2.1. 项目结构

```
backend/live_core_service/
├── app/
│   ├── models/
│   │   ├── __init__.py
│   │   ├── brand.py  ✅ 已生成（步骤2）
│   │   └── ...
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── brand.py  ✅ 已生成（步骤2）
│   │   └── ...
│   ├── crud/
│   │   ├── __init__.py
│   │   ├── brand.py  ⏳ 待生成（步骤6）
│   │   └── ...
│   ├── services/
│   │   ├── __init__.py
│   │   ├── brand_service.py  ⏳ 待生成（步骤6）
│   │   └── ...
│   └── api/
│       └── v1/
│           ├── api.py  ⏳ 需更新路由注册（步骤6）
│           └── endpoints/
│               ├── __init__.py
│               ├── brand.py  ⏳ 待生成（步骤6）
│               └── ...
```

### 2.2. 设计文档路径

**主设计文档**: `docs/03_系统设计/直播核心功能设计文档_v6_品牌模块设计文档-品牌管理-品牌专题关联.md`

**依赖的权限设计文档**: `docs/03_系统设计/直播核心功能设计文档_v6_增加权限设计版(非独立版).md`

**依赖的安全配置文档**: `docs/03_系统设计/直播核心功能设计文档----配置与安全优化方案.md`

**依赖的专题功能文档**: `docs/03_系统设计/直播核心功能设计文档_v6_增加专题功能完整设计文档-修正版.md`

**依赖的v6主文档**: `docs/03_系统设计/直播核心功能设计文档_v6_深度融合最终版.md`

---

## 3. Model 字段摘要（基于实际代码）

### 3.1. Brand 模型

**文件路径**: `backend/live_core_service/app/models/brand.py`

**表名**: `brands`

**字段摘要**:
| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|--------|------|------|--------|------|
| `id` | UUID | PRIMARY KEY | uuid.uuid4() | 品牌ID（应用层生成） |
| `name` | String(150) | NOT NULL, UNIQUE | - | 品牌名称，全局唯一 |
| `slug` | String(150) | NULLABLE | NULL | URL友好标识符 |
| `logo_url` | String(512) | NULLABLE | NULL | 品牌Logo URL |
| `description` | Text | NULLABLE | NULL | 品牌描述 |
| `website_url` | String(255) | NULLABLE | NULL | 品牌官网链接 |
| `sort_order` | Integer | NOT NULL | 0 | 排序权重，数字越小越靠前 |
| `is_active` | Boolean | NOT NULL | True | 是否启用（软删除字段） |
| `created_at` | TIMESTAMP(TZ) | NOT NULL | func.now() | 创建时间 |
| `updated_at` | TIMESTAMP(TZ) | NOT NULL | func.now() | 更新时间（自动更新） |

**索引**:
- `idx_brands_sort_order` (sort_order)
- `idx_brands_is_active` (is_active)
- `idx_brands_active_sort` (is_active, sort_order WHERE is_active=true) - 部分索引

**关系**:
- `topics`: relationship("BrandTopic", cascade="all, delete-orphan")
- `rooms`: relationship("BrandRoom", cascade="all, delete-orphan")

**验证规则**（在Schema层实现）:
- `name`: 必须不为空，长度1-150字符
- `slug`: 只能包含小写字母、数字和连字符（如适用）
- `website_url`: 必须以http://或https://开头

---

### 3.2. BrandTopic 模型

**文件路径**: `backend/live_core_service/app/models/brand.py`

**表名**: `brand_topics`

**字段摘要**:
| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|--------|------|------|--------|------|
| `brand_id` | UUID | PRIMARY KEY, FK(brands.id, CASCADE) | - | 品牌ID |
| `topic_id` | UUID | PRIMARY KEY, FK(topics.id, CASCADE) | - | 专题ID（topics表由专题功能模块定义） |
| `created_at` | TIMESTAMP(TZ) | NOT NULL | func.now() | 创建时间 |

**主键**: 复合主键 (brand_id, topic_id)

**索引**:
- `idx_brand_topics_brand_id` (brand_id)
- `idx_brand_topics_topic_id` (topic_id)

**关系**:
- `brand`: relationship("Brand", back_populates="topics")
- 注意：Topic模型由专题功能模块定义，避免循环导入

**删除策略**: 硬删除（直接DELETE），ON DELETE CASCADE

---

### 3.3. BrandRoom 模型

**文件路径**: `backend/live_core_service/app/models/brand.py`

**表名**: `brand_rooms`

**字段摘要**:
| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|--------|------|------|--------|------|
| `brand_id` | UUID | PRIMARY KEY, FK(brands.id, CASCADE) | - | 品牌ID |
| `room_id` | UUID | PRIMARY KEY, FK(live_rooms.id, CASCADE) | - | 直播间ID（live_rooms表由v6主文档定义） |
| `created_at` | TIMESTAMP(TZ) | NOT NULL | func.now() | 创建时间 |

**主键**: 复合主键 (brand_id, room_id)

**索引**:
- `idx_brand_rooms_brand_id` (brand_id)
- `idx_brand_rooms_room_id` (room_id)

**关系**:
- `brand`: relationship("Brand", back_populates="rooms")
- 注意：LiveRoom模型由v6主文档定义，避免循环导入

**删除策略**: 硬删除（直接DELETE），ON DELETE CASCADE

---

## 4. Schema 摘要（基于实际代码）

### 4.1. 品牌管理 Schemas

**文件路径**: `backend/live_core_service/app/schemas/brand.py`

#### 4.1.1. BrandBase
- **用途**: 品牌基础Schema
- **字段**: name (str, 1-150), slug (Optional[str], max 150), logo_url (Optional[str], max 512), description (Optional[str]), website_url (Optional[str], max 255)
- **验证器**: `validate_website_url`: 验证URL格式（必须以http://或https://开头）

#### 4.1.2. BrandCreate
- **用途**: 创建品牌请求
- **继承**: BrandBase
- **新增字段**: sort_order (Optional[int], default 0, ≥0), is_active (Optional[bool], default True)

#### 4.1.3. BrandUpdate
- **用途**: 更新品牌请求（部分更新）
- **字段**: 所有字段均为Optional
- **配置**: `from_attributes=True`

#### 4.1.4. BrandItem
- **用途**: 品牌响应Schema
- **继承**: BrandBase
- **新增字段**: id (UUID), sort_order (int), is_active (bool), created_at (datetime), updated_at (datetime)
- **配置**: `from_attributes=True`

---

### 4.2. 品牌内容响应 Schemas

**文件路径**: `backend/live_core_service/app/schemas/brand.py`

#### 4.2.1. TopicBriefItem
- **用途**: 专题简要信息Schema
- **字段**: id (UUID), title (str), banner_url (Optional[str])
- **配置**: `from_attributes=True`

#### 4.2.2. BrandContentData
- **用途**: 品牌内容数据Schema
- **字段**: brand_info (BrandItem), associated_topics (List[TopicBriefItem], default_factory=list, max 1000)

#### 4.2.3. BrandContentResponse
- **用途**: 品牌内容响应Schema
- **字段**: code (int, 200), message (str, "success"), data (BrandContentData), timestamp (datetime)

---

### 4.3. 品牌-专题关联 Schemas

**文件路径**: `backend/live_core_service/app/schemas/brand.py`

#### 4.3.1. BrandTopicBindIn
- **用途**: 绑定品牌专题请求Schema
- **字段**: topic_ids (List[UUID], default_factory=list, max 100)

#### 4.3.2. TopicBrandItem
- **用途**: 专题品牌展示项Schema
- **字段**: id (UUID), name (str), slug (Optional[str]), logo_url (Optional[str]), sort_order (int, default 0)
- **配置**: `from_attributes=True`

#### 4.3.3. BrandTopicBindOut
- **用途**: 绑定品牌专题响应Schema
- **字段**: brand_id (UUID), topic_ids (List[UUID], max 100), updated_at (datetime)

---

### 4.4. 品牌-直播间关联 Schemas（V1.1新增）

**文件路径**: `backend/live_core_service/app/schemas/brand.py`

#### 4.4.1. BrandRoomBindIn
- **用途**: 直播间绑定品牌请求Schema
- **字段**: brand_ids (List[UUID], default_factory=list, max 100)

#### 4.4.2. RoomBrandItem
- **用途**: 直播间品牌Tab展示项Schema（Room Page专用）
- **字段**: id (UUID), name (str), slug (Optional[str]), logo_url (Optional[str]), website_url (Optional[str]), sort_order (int, default 0)
- **配置**: `from_attributes=True`

#### 4.4.3. BrandRoomBindOut
- **用途**: 直播间绑定品牌响应Schema
- **字段**: room_id (UUID), brand_ids (List[UUID], max 100), updated_at (datetime)

---

## 5. 架构规范引用

### 5.1. Clean Architecture 分层架构

本模块遵循Clean Architecture分层架构。

**核心原则**:
- CRUD层：数据访问层，仅负责数据库操作
- Service层：业务逻辑层，负责业务编排和权限检查
- Endpoint层：HTTP端点层，负责请求解析和响应构造

**依赖方向**: Endpoint → Service → CRUD → Models

### 5.2. 权限设计规范

本模块遵循统一的权限设计规范。

**核心原则**:
- 双轨鉴权模式：Strict Auth（写操作） + Optional Auth（读操作）
- Service层负责权限检查（不在Endpoint层检查）
- 品牌信息是公开资源，所有用户都可以访问
- 所有写操作都需要管理员权限

**权限守卫函数**（在Service层实现）:
- `_check_admin_permission(role: str)`: 管理员权限检查

**适用场景**:
- Brands: 
  - 创建/更新/删除品牌: 需要管理员权限（`_check_admin_permission`）
  - 查询品牌: 公开访问（无需权限检查）或管理员分页查询（需要管理员权限）
- Brand_Topics:
  - 批量关联/解除关联专题: 需要管理员权限
  - 查询品牌关联的专题: 管理员权限或公开访问（根据接口）
- Brand_Rooms:
  - 绑定/查询直播间品牌: 需要管理员权限（配置后台）
  - 获取直播间品牌Tab内容: 公开访问（前端展示）

### 5.3. 全项目通用安全与一致性规范（最高优先级）

本模块**必须**严格遵循以下所有安全与一致性规范。

#### 5.3.1. 安全异步异常处理规范

**🚨 [强制要求] 安全异步异常处理（最高优先级）**：

- **规则**：在任何 `try...except` 块中，如果需要使用来自 JWT dict（如 `current_user`）的属性（如 `current_user["user_id"]`）进行日志记录，这些属性**必须在进入 `try` 块之前**被提取并存储到局部变量中。
- **指令**：**严禁**在捕获了数据库相关异常的 `except` 块中访问可能已失效的字典属性。

**✅ 正确示例**：
```python
# API层端点
async def create_brand(
    brand_data: BrandCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    # 🚨 必须在try块之前提取属性
    current_user_id = UUID(current_user["user_id"])
    role = current_user.get("role", "REGULAR").upper()
    user_id_for_logging = str(current_user_id)[:8]  # ✅ 提前提取
    
    try:
        result = await service.create_brand(db, brand_data, current_user_id, role)
        # ✅ 使用success_response包装Service层返回的业务对象
        return success_response(data=result, message="品牌创建成功")
    except Exception as e:
        logger.error(f"创建品牌异常: user_id={user_id_for_logging}, error={str(e)}")  # ✅ 使用提前提取的变量
        return JSONResponse(...)
```

**❌ 错误示例**：
```python
try:
    result = await service.create_brand(...)
except Exception as e:
    user_id = current_user["user_id"]  # ❌ 在except块中访问dict属性
    logger.error(f"创建品牌异常: user_id={user_id}, error={str(e)}")
```

#### 5.3.2. 内部ID不得对外暴露规范

**🚨 [强制要求] 内部ID不得对外暴露（最高优先级）**：

- 所有对外 API 的 Response Schema 中，**可以**直接暴露数据库主键UUID（如 `id`）。
- **注意**：品牌模块使用UUID作为主键，UUID本身是安全的，可以对外暴露。

**✅ 正确示例**：
```python
# API Schema（对外）
class BrandItem(BaseModel):
    id: UUID  # ✅ UUID主键可以暴露
    name: str
```

#### 5.3.3. API Schema 与内部 CRUD Schema 严格区分规范

**🚨 [强制要求] API Schema 与内部 CRUD Schema 严格区分（最高优先级）**：

1. **API 输入/输出 Schema** (对外边界，安全优先):
   - **不得包含**任何内部控制字段或敏感字段（如 `role`, `is_admin`, `password_hash`, `user_id` 等）。

2. **内部 CRUD Schema** (仅服务内部使用):
   - 示例: `BrandCreateInternal`
   - 用途: 封装 Service / CRUD 层写入数据库所需的**完整字段集合**（可包含 `role`, `user_id` 等）。
   - 约束: **禁止**在 API 路由函数中直接作为请求体暴露给外部。

**✅ 正确示例**：
```python
# API Schema（对外）
class BrandCreate(BaseModel):
    name: str
    slug: Optional[str] = None
    # ❌ 禁止包含role、user_id等内部字段

# 内部 CRUD Schema（内部使用）
class BrandCreateInternal(BaseModel):
    name: str
    slug: Optional[str] = None
    user_id: UUID  # ✅ 内部Schema可以包含
    role: str  # ✅ 内部Schema可以包含
```

#### 5.3.4. Enum 字段声明规范

**🚨 [强制要求] Enum 字段声明规范（最高优先级）**：

- **必须**使用 Python `enum.Enum` 类，并配合 `sqlalchemy.Enum`。
- **必须**使用 `native_enum=False`（除非有特殊原因）。

**注意**：品牌模块当前不使用Enum字段，如果未来需要，请参考此规范。

#### 5.3.5. 环境变量驱动配置规范

**🚨 [强制要求] 环境变量驱动配置规范（最高优先级）**：

- **禁止**在代码中硬编码敏感信息（如数据库密码、JWT密钥、CORS配置等）。
- **必须**通过环境变量读取所有敏感配置。
- **禁止**为敏感信息设置不安全的默认值。

#### 5.3.6. RESTful API 设计原则

**🚨 [强制要求] RESTful API 设计原则（最高优先级）**：

- **资源导向**：API路径应该表示资源（如 `/brands`, `/topics`），而非操作（如 `/get_brands`, `/create_brand`）。
- **层次结构**：使用嵌套路径表示资源关系（如 `/brands/{brand_id}/topics`, `/rooms/{room_id}/brands`）。
- **HTTP 方法**：使用标准HTTP方法（GET、POST、PUT、DELETE、PATCH）表示操作。
- **状态码**：使用标准HTTP状态码（200、201、400、404、500等）。

**✅ 正确示例**：
```python
# ✅ 资源导向
GET /api/v1/brands  # 获取品牌列表
POST /api/v1/admin/brands  # 创建品牌
PATCH /api/v1/admin/brands/{brand_id}  # 更新品牌
DELETE /api/v1/admin/brands/{brand_id}  # 删除品牌

# ✅ 层次结构
GET /api/v1/brands/{brand_id}/content  # 获取品牌内容
POST /api/v1/admin/brands/{brand_id}/topics  # 为品牌关联专题
POST /api/v1/admin/rooms/{room_id}/brands  # 为直播间绑定品牌
```

**❌ 错误示例**：
```python
# ❌ 操作导向
GET /api/v1/get_brands  # ❌ 禁止
POST /api/v1/create_brand  # ❌ 禁止
```

#### 5.3.7. 日志与错误消息脱敏规范

**核心要求**:
- **日志脱敏**：日志中不记录用户敏感信息（如完整UUID，只记录前8位）
- **错误消息脱敏**：错误消息不暴露内部实现细节
- **输入验证**：所有用户输入通过Pydantic验证，防止XSS和SQL注入

**✅ 正确示例**：
```python
# ✅ 日志脱敏
logger.info(f"创建品牌成功: id={str(brand_id)[:8]}")  # ✅ 只记录前8位

# ✅ 错误消息脱敏
except Exception as e:
    logger.error(f"创建品牌失败: {type(e).__name__}")  # ✅ 不暴露完整异常信息
    return JSONResponse(
        status_code=500,
        content=error_response(code=1002, message="内部服务器错误")  # ✅ 通用错误消息
    )
```

---

## 6. 待生成的代码清单

### 6.1. CRUD层代码

**文件路径**: `backend/live_core_service/app/crud/brand.py`

**需要生成的CRUD函数**（基于设计文档的API接口和业务逻辑）:

#### Brands CRUD 函数
1. `async def get_brands(db: AsyncSession, limit: int, q: Optional[str]) -> List[Brand]`
   - 获取品牌列表（公开接口，按sort_order升序，过滤is_active=True）
   - 支持按名称模糊搜索（q参数）

2. `async def get_brand_with_topics(db: AsyncSession, brand_id: UUID) -> Tuple[Brand, List[Topic]]`
   - 获取品牌及其关联的专题列表
   - 返回：(品牌对象, 关联的专题列表)
   - 仅返回已发布的专题（status='published'）

3. `async def create_brand(db: AsyncSession, brand_in: BrandCreate) -> Brand`
   - 创建品牌
   - 在应用层生成UUID
   - 捕获唯一性约束违反（name字段）

4. `async def get_brands_paginated(db: AsyncSession, page: int, size: int, name: Optional[str], is_active: Optional[bool]) -> Tuple[List[Brand], int]`
   - 获取品牌列表（管理员接口，分页）
   - 支持按名称模糊搜索和is_active筛选
   - 返回：(品牌列表, 总数)

5. `async def get_brand_by_id(db: AsyncSession, brand_id: UUID) -> Optional[Brand]`
   - 根据ID获取品牌
   - 返回品牌对象或None

6. `async def update_brand(db: AsyncSession, brand_id: UUID, brand_in: BrandUpdate) -> Brand`
   - 更新品牌信息
   - 部分更新（PATCH）
   - 捕获唯一性约束违反

7. `async def delete_brand(db: AsyncSession, brand_id: UUID, hard_delete: bool) -> Brand`
   - 删除品牌
   - 软删除：设置is_active=False
   - 硬删除：直接DELETE（需检查引用关系）

8. `async def check_brand_references(db: AsyncSession, brand_id: UUID) -> Tuple[int, int]`
   - 检查品牌被引用的情况
   - 返回：(专题引用数, 直播间引用数)

#### Brand_Topics CRUD 函数
9. `async def batch_add_brand_topics(db: AsyncSession, brand_id: UUID, topic_ids: List[UUID]) -> int`
   - 批量添加品牌-专题关联
   - 使用INSERT ... ON CONFLICT DO NOTHING保证幂等性
   - 返回实际新增的关联数

10. `async def delete_brand_topic(db: AsyncSession, brand_id: UUID, topic_id: UUID) -> bool`
    - 删除单个品牌-专题关联（硬删除）
    - 返回：是否成功删除

11. `async def get_brand_topics_paginated(db: AsyncSession, brand_id: UUID, page: int, size: int) -> Tuple[List[dict], int]`
    - 获取品牌关联的专题列表（管理员接口，分页）
    - 联表查询brand_topics + topics
    - 返回：(专题信息列表, 总数)

#### Brand_Rooms CRUD 函数（V1.1新增）
12. `async def bind_room_brands(db: AsyncSession, room_id: UUID, brand_ids: List[UUID]) -> List[UUID]`
    - 为直播间绑定品牌（全量替换策略）
    - 先删除该room_id的所有旧关联，再批量插入新关联
    - 返回绑定的brand_ids列表

13. `async def get_room_brands(db: AsyncSession, room_id: UUID) -> List[Brand]`
    - 获取直播间绑定的品牌列表
    - 联表查询brand_rooms + brands
    - 按brands.sort_order升序排序
    - 仅返回is_active=True的品牌

14. `async def get_room_brands_for_tab(db: AsyncSession, room_id: UUID) -> List[Brand]`
    - 获取直播间品牌Tab内容（公开接口）
    - 与get_room_brands相同，但明确用于前端展示

---

### 6.2. Service层代码

**文件路径**: `backend/live_core_service/app/services/brand_service.py`

**需要生成的Service方法**（基于设计文档的API接口）:

#### 权限守卫函数
1. `def _check_admin_permission(self, user_role: str) -> None`
   - 管理员权限检查
   - 如果role不在['ADMIN', 'SUPERADMIN']，抛出PermissionDeniedException

#### Brands Service 方法
2. `async def get_brands_list(self, db: AsyncSession, limit: int, q: Optional[str], current_user_id: Optional[UUID], role: Optional[str]) -> Any`
   - 获取品牌列表（公开接口）
   - 返回包含品牌列表的响应对象

3. `async def get_brand_content(self, db: AsyncSession, brand_id: UUID, current_user_id: Optional[UUID], role: Optional[str]) -> Any`
   - 获取品牌详情及关联专题
   - 404检查：品牌不存在或is_active=False抛出NotFoundException
   - 返回包含品牌信息和关联专题的响应对象

4. `async def create_brand(self, db: AsyncSession, brand_data: BrandCreate, current_user_id: UUID, role: str) -> Any`
   - 创建品牌
   - 权限检查: `_check_admin_permission(role)`
   - 返回包含品牌信息的响应对象

5. `async def get_brands_paginated(self, db: AsyncSession, page: int, size: int, name: Optional[str], is_active: Optional[bool], current_user_id: UUID, role: str) -> Any`
   - 获取品牌列表（管理员接口，分页）
   - 权限检查: `_check_admin_permission(role)`
   - 返回分页响应对象

6. `async def get_brand_by_id(self, db: AsyncSession, brand_id: UUID, current_user_id: UUID, role: str) -> Any`
   - 获取单个品牌详情（管理员接口）
   - 权限检查: `_check_admin_permission(role)`
   - 404检查：品牌不存在抛出NotFoundException
   - 返回包含品牌信息的响应对象

7. `async def update_brand(self, db: AsyncSession, brand_id: UUID, brand_data: BrandUpdate, current_user_id: UUID, role: str) -> Any`
   - 更新品牌
   - 权限检查: `_check_admin_permission(role)`
   - 404检查：品牌不存在抛出NotFoundException
   - 返回包含更新后品牌信息的响应对象

8. `async def delete_brand(self, db: AsyncSession, brand_id: UUID, hard_delete: bool, current_user_id: UUID, role: str) -> Any`
   - 删除品牌
   - 权限检查: `_check_admin_permission(role)`（软删除需ADMIN，硬删除需SUPERADMIN）
   - 404检查：品牌不存在抛出NotFoundException
   - 引用检查：如果被引用且为硬删除，抛出ConflictException
   - 返回删除状态响应对象

#### Brand_Topics Service 方法
9. `async def batch_add_brand_topics(self, db: AsyncSession, brand_id: UUID, topic_ids: List[UUID], current_user_id: UUID, role: str) -> Any`
   - 批量关联专题到品牌
   - 权限检查: `_check_admin_permission(role)`
   - 业务验证: 检查brand_id和所有topic_ids是否存在
   - 返回包含关联结果的响应对象

10. `async def delete_brand_topic(self, db: AsyncSession, brand_id: UUID, topic_id: UUID, current_user_id: UUID, role: str) -> Any`
    - 解除单个品牌-专题关联
    - 权限检查: `_check_admin_permission(role)`
    - 404检查：关联关系不存在抛出NotFoundException
    - 返回删除状态响应对象

11. `async def get_brand_topics_paginated(self, db: AsyncSession, brand_id: UUID, page: int, size: int, current_user_id: UUID, role: str) -> Any`
    - 获取品牌的关联专题列表（管理员接口，分页）
    - 权限检查: `_check_admin_permission(role)`
    - 404检查：品牌不存在抛出NotFoundException
    - 返回分页响应对象

#### Brand_Rooms Service 方法（V1.1新增）
12. `async def bind_room_brands(self, db: AsyncSession, room_id: UUID, brand_ids: List[UUID], current_user_id: UUID, role: str) -> Any`
    - 为直播间绑定品牌
    - 权限检查: `_check_admin_permission(role)`
    - 业务验证: 检查room_id和所有brand_ids是否存在且is_active=True
    - 返回包含绑定结果的响应对象

13. `async def get_room_brands_admin(self, db: AsyncSession, room_id: UUID, current_user_id: UUID, role: str) -> Any`
    - 获取直播间绑定的品牌（管理员接口）
    - 权限检查: `_check_admin_permission(role)`
    - 404检查：直播间不存在抛出NotFoundException
    - 返回包含品牌列表的响应对象

14. `async def get_room_brands_for_tab(self, db: AsyncSession, room_id: UUID, include_topic_brands: bool, topic_id: Optional[UUID], current_user_id: Optional[UUID], role: Optional[str]) -> Any`
    - 获取直播间品牌Tab内容（公开接口）
    - 404检查：直播间不存在抛出NotFoundException
    - 如果include_topic_brands=True，还需验证topic_id并查询topic品牌
    - 返回包含品牌列表或结构化数据的响应对象

---

### 6.3. API层代码

**文件路径**: `backend/live_core_service/app/api/v1/endpoints/brand.py`

**需要生成的端点**（基于设计文档的API接口清单）:

#### Brands 端点
1. `GET /api/v1/brands` - 获取品牌列表（Public + Optional Auth）
2. `GET /api/v1/brands/{brand_id}/content` - 获取品牌详情及关联专题（Public + Optional Auth）
3. `POST /api/v1/admin/brands` - 创建品牌（Strict Auth + Admin）
4. `GET /api/v1/admin/brands` - 获取品牌列表（Admin分页接口）
5. `GET /api/v1/admin/brands/{brand_id}` - 获取单个品牌详情（Admin）
6. `PATCH /api/v1/admin/brands/{brand_id}` - 更新品牌（Admin）
7. `DELETE /api/v1/admin/brands/{brand_id}` - 删除品牌（Admin/SuperAdmin）

#### Brand_Topics 端点
8. `POST /api/v1/admin/brands/{brand_id}/topics` - 批量关联专题到品牌（Admin）
9. `DELETE /api/v1/admin/brands/{brand_id}/topics/{topic_id}` - 解除单个品牌-专题关联（Admin）
10. `GET /api/v1/admin/brands/{brand_id}/topics` - 获取品牌的关联专题列表（Admin分页）

#### Brand_Rooms 端点（V1.1新增）
11. `POST /api/v1/admin/rooms/{room_id}/brands` - 绑定直播间品牌（Admin）
12. `GET /api/v1/admin/rooms/{room_id}/brands` - 获取直播间绑定的品牌（Admin）
13. `GET /api/v1/rooms/{room_id}/brands` - 获取直播间品牌Tab内容（Public + Optional Auth）

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
  - **必须**导入`JSONResponse`、`success_response`和`error_response`：`from fastapi.responses import JSONResponse`，`from app.core.response import success_response, error_response`
  - **禁止**使用`raise HTTPException`，**必须**使用`JSONResponse` + `error_response()`
  - **响应函数使用规范**：
    - **成功响应**: 直接使用 `return success_response(data=...)`，FastAPI自动序列化为JSON（状态码200）
    - **错误响应**: **必须**使用 `return JSONResponse(status_code=xxx, content=error_response(...))`，因为`error_response()`仅返回响应体字典，需要通过`JSONResponse`的`status_code`参数指定HTTP状态码（如403、404、500等）
  - 必须捕获通用`Exception`并返回500错误

---

### 6.4. API-Service对应关系验证

**验证结果**：

API端点数量：13个
Service方法数量（排除权限守卫函数）：13个

**对应关系**：
1. `GET /api/v1/brands` ↔ `get_brands_list`
2. `GET /api/v1/brands/{brand_id}/content` ↔ `get_brand_content`
3. `POST /api/v1/admin/brands` ↔ `create_brand`
4. `GET /api/v1/admin/brands` ↔ `get_brands_paginated`
5. `GET /api/v1/admin/brands/{brand_id}` ↔ `get_brand_by_id`
6. `PATCH /api/v1/admin/brands/{brand_id}` ↔ `update_brand`
7. `DELETE /api/v1/admin/brands/{brand_id}` ↔ `delete_brand`
8. `POST /api/v1/admin/brands/{brand_id}/topics` ↔ `batch_add_brand_topics`
9. `DELETE /api/v1/admin/brands/{brand_id}/topics/{topic_id}` ↔ `delete_brand_topic`
10. `GET /api/v1/admin/brands/{brand_id}/topics` ↔ `get_brand_topics_paginated`
11. `POST /api/v1/admin/rooms/{room_id}/brands` ↔ `bind_room_brands`
12. `GET /api/v1/admin/rooms/{room_id}/brands` ↔ `get_room_brands_admin`
13. `GET /api/v1/rooms/{room_id}/brands` ↔ `get_room_brands_for_tab`

**验证结论**：✅ API端点与Service方法完全对应，无遗漏。

---

## 6. 架构实现规范（完整版）

**重要说明**：本节包含所有层级的详细实现规范，是代码生成的强制要求，必须严格遵守。

### 6.1. CRUD层实现规范

#### 6.1.1. N+1问题防治规范

**规则**：所有返回嵌套关系数据的查询必须使用 `selectinload` 或 `joinedload` 预加载关联对象。

**✅ 正确示例**：
```python
from sqlalchemy.orm import selectinload

# 获取品牌及其关联的专题（避免N+1问题）
stmt = select(Brand).options(
    selectinload(Brand.topics).selectinload(BrandTopic.topic)
).where(Brand.id == brand_id)
result = await db.execute(stmt)
brand = result.scalar_one_or_none()
```

**❌ 错误示例**：
```python
# 不使用预加载，会导致N+1问题
brand = await db.get(Brand, brand_id)
for brand_topic in brand.topics:  # ❌ 每次迭代都会触发一次查询
    print(brand_topic.topic.title)
```

#### 6.1.2. 分页模式规范（两次查询）

**规则**：分页查询必须先COUNT总数，再查询当前页数据。

**✅ 正确示例**：
```python
from sqlalchemy import select, func

async def get_brands_paginated(
    db: AsyncSession,
    page: int,
    size: int
) -> Tuple[List[Brand], int]:
    # 第一次查询：获取总数
    count_stmt = select(func.count()).select_from(Brand).where(Brand.is_active == True)
    total_result = await db.execute(count_stmt)
    total = total_result.scalar_one()
    
    # 第二次查询：获取当前页数据
    stmt = select(Brand).where(Brand.is_active == True).order_by(Brand.sort_order)
    stmt = stmt.offset((page - 1) * size).limit(size)
    result = await db.execute(stmt)
    brands = list(result.scalars().all())
    
    return brands, total
```

#### 6.1.3. 事务处理规范

**规则1：单表操作**：使用单次 `db.commit()`，配合异常处理。

**✅ 正确示例**：
```python
async def create_brand(db: AsyncSession, brand_in: BrandCreate) -> Brand:
    try:
        brand = Brand(
            id=uuid.uuid4(),
            name=brand_in.name,
            # ... 其他字段
        )
        db.add(brand)
        await db.commit()
        await db.refresh(brand)
        return brand
    except IntegrityError as e:
        await db.rollback()
        if "uq_brands_name" in str(e):
            raise DatabaseIntegrityException("品牌名称已存在")
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"创建品牌失败: {str(e)}")
        raise
```

**规则2：批量操作**：使用 `async with db.begin()` 显式事务。

**✅ 正确示例**：
```python
async def bind_room_brands(
    db: AsyncSession,
    room_id: UUID,
    brand_ids: List[UUID]
) -> List[UUID]:
    try:
        async with db.begin():  # 显式事务
            # 1. 删除旧关联
            delete_stmt = delete(BrandRoom).where(BrandRoom.room_id == room_id)
            await db.execute(delete_stmt)
            
            # 2. 批量插入新关联
            if brand_ids:
                new_relations = [
                    BrandRoom(brand_id=bid, room_id=room_id)
                    for bid in brand_ids
                ]
                db.add_all(new_relations)
            
            # async with 块退出时自动commit
        return brand_ids
    except Exception as e:
        await db.rollback()
        logger.error(f"绑定直播间品牌失败: {str(e)}")
        raise
```

#### 6.1.4. 异常处理规范

**强制要求**：所有CRUD函数必须包含完整的异常处理。

**必须捕获的异常**：
- `IntegrityError`：唯一约束、外键约束违反
- `Exception`：其他未预期错误

**✅ 完整模板**：
```python
async def crud_operation(db: AsyncSession, ...) -> ...:
    try:
        # 数据库操作
        ...
        await db.commit()
        return result
    except IntegrityError as e:
        await db.rollback()
        # 识别具体的约束违反类型
        if "unique constraint" in str(e).lower():
            raise DatabaseIntegrityException("资源已存在")
        elif "foreign key constraint" in str(e).lower():
            raise DatabaseIntegrityException("关联的资源不存在")
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"操作失败: {type(e).__name__}, {str(e)}")
        raise
    finally:
        # 可选：清理资源（如有必要）
        pass
```

---

### 6.2. Service层实现规范

#### 6.2.1. 业务编排规范

**规则**：Service层负责业务逻辑编排，调用多个CRUD函数完成复杂业务。

**✅ 正确示例**：
```python
class BrandService:
    async def delete_brand(
        self,
        db: AsyncSession,
        brand_id: UUID,
        hard_delete: bool,
        current_user_id: UUID,
        role: str
    ) -> Any:
        # 1. 权限检查
        if hard_delete and role not in ['SUPERADMIN']:
            raise PermissionDeniedException("硬删除需要SUPERADMIN权限")
        self._check_admin_permission(role)
        
        # 2. 检查品牌是否存在
        brand = await crud.get_brand_by_id(db, brand_id)
        if not brand:
            raise NotFoundException("品牌不存在")
        
        # 3. 如果是硬删除，检查引用关系
        if hard_delete:
            topic_count, room_count = await crud.check_brand_references(db, brand_id)
            if topic_count > 0 or room_count > 0:
                raise ConflictException(
                    f"品牌被引用，无法删除。专题引用:{topic_count}, 直播间引用:{room_count}"
                )
        
        # 4. 执行删除
        deleted_brand = await crud.delete_brand(db, brand_id, hard_delete)
        
        # 5. 构造响应
        return {
            "code": 200,
            "message": "success",
            "data": {
                "id": str(brand_id),
                "status": "hard_deleted" if hard_delete else "soft_deleted",
                "deleted_at": datetime.utcnow()
            },
            "timestamp": datetime.utcnow()
        }
```

#### 6.2.2. 批量验证规范

**规则**：批量操作前必须验证所有输入ID的有效性。

**✅ 正确示例**：
```python
async def batch_add_brand_topics(
    self,
    db: AsyncSession,
    brand_id: UUID,
    topic_ids: List[UUID],
    current_user_id: UUID,
    role: str
) -> Any:
    # 1. 权限检查
    self._check_admin_permission(role)
    
    # 2. 验证品牌存在
    brand = await crud.get_brand_by_id(db, brand_id)
    if not brand or not brand.is_active:
        raise NotFoundException("品牌不存在")
    
    # 3. 批量验证专题ID
    stmt = select(Topic.id).where(Topic.id.in_(topic_ids))
    result = await db.execute(stmt)
    existing_ids = set(result.scalars().all())
    invalid_ids = set(topic_ids) - existing_ids
    
    if invalid_ids:
        raise InvalidParameterException(
            f"部分专题ID不存在: {[str(id) for id in invalid_ids]}"
        )
    
    # 4. 执行批量关联
    added_count = await crud.batch_add_brand_topics(db, brand_id, topic_ids)
    
    # 5. 返回结果
    return {
        "code": 200,
        "message": "success",
        "data": {
            "brand_id": str(brand_id),
            "added_count": added_count,
            "topic_ids": [str(id) for id in topic_ids]
        },
        "timestamp": datetime.utcnow()
    }
```

#### 6.2.3. 权限模式规范

**规则**：所有角色比较必须使用大写字符串。

**✅ 正确示例**：
```python
def _check_admin_permission(self, user_role: str) -> None:
    # ✅ 必须使用大写
    if user_role not in ['ADMIN', 'SUPERADMIN']:
        raise PermissionDeniedException("权限不足，需要管理员权限")
```

**❌ 错误示例**：
```python
def _check_admin_permission(self, user_role: str) -> None:
    # ❌ 禁止使用小写
    if user_role not in ['admin', 'superadmin']:
        raise PermissionDeniedException("权限不足，需要管理员权限")
```

---

### 6.3. API层实现规范

#### 6.3.1. API端点实现强制模板

**规则**：所有API端点必须遵循以下完整模板。

**✅ 强制模板**：
```python
from fastapi import APIRouter, Depends, Query, Path
from fastapi.responses import JSONResponse
from app.exceptions import PermissionDeniedException, NotFoundException, InvalidParameterException
from app.core.response import success_response, error_response
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/admin/brands", ...)
async def create_brand(
    brand_data: BrandCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> Any:
    """创建品牌（Strict Auth + Admin）"""
    # 🚨 步骤1：在try块之前提取所有必要信息
    current_user_id = UUID(current_user["user_id"])
    role = current_user.get("role", "REGULAR").upper()  # ✅ 必须调用.upper()
    user_id_for_logging = str(current_user_id)[:8]  # ✅ 提前提取用于日志
    
    try:
        # 🚨 步骤2：调用Service层
        result = await brand_service.create_brand(db, brand_data, current_user_id, role)
        # ✅ 使用success_response包装Service层返回的业务对象
        return success_response(data=result, message="品牌创建成功")
        
    # 🚨 步骤3：捕获所有可能的异常
    # ✅ 注意：error_response()仅返回响应体字典，必须使用JSONResponse指定HTTP状态码
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
    except ConflictException as e:
        logger.warning(f"操作冲突: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=409,
            content=error_response(code=2003, message=str(e))
        )
    except Exception as e:
        # 🚨 步骤4：捕获所有未预期错误
        logger.error(f"创建品牌异常: user_id={user_id_for_logging}, error={type(e).__name__}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="内部服务器错误")
        )
```

**关键要点**：
1. **提前提取**：role必须在try块之前提取并调用`.upper()`
2. **日志脱敏**：UUID只记录前8位
3. **完整异常处理**：至少包含4种异常类型
4. **统一响应格式**：使用`JSONResponse` + `error_response()`
5. **禁止HTTPException**：不使用`raise HTTPException`

#### 6.3.2. API层导入规范

**强制导入清单**：
```python
from fastapi import APIRouter, Depends, Query, Path, Body
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import Optional, List, Any
import logging

# 核心依赖
from app.database import get_db
from app.core.deps import get_current_user, get_current_user_optional
from app.core.response import success_response, error_response

# 异常类
from app.exceptions import (
    PermissionDeniedException,
    NotFoundException,
    InvalidParameterException,
    ConflictException,
    DatabaseIntegrityException
)

# Schemas
from app.schemas.brand import (
    BrandCreate, BrandUpdate, BrandItem,
    BrandTopicBindIn, BrandRoomBindIn,
    # ... 其他必要的Schema
)

# Service
from app.services.brand_service import BrandService

logger = logging.getLogger(__name__)
router = APIRouter()  # ⚠️ 不指定prefix，prefix在api.py中统一指定
brand_service = BrandService()
```

#### 6.3.3. 路由定义规范

**规则**：
1. **禁止**在`APIRouter()`中指定`prefix`
2. **prefix必须**在`api/v1/api.py`中统一指定
3. 使用资源导向的路径设计

**✅ 正确示例（endpoints/brand.py）**：
```python
router = APIRouter()  # ✅ 不指定prefix

@router.get("/brands")  # ✅ 相对路径
async def get_brands(...):
    pass

@router.post("/admin/brands")  # ✅ 相对路径
async def create_brand(...):
    pass
```

**✅ 正确示例（api/v1/api.py）**：
```python
from fastapi import APIRouter
from app.api.v1.endpoints import brand

api_router = APIRouter()
api_router.include_router(brand.router, prefix="/api/v1", tags=["brands"])  # ✅ 统一指定prefix
```

**❌ 错误示例**：
```python
router = APIRouter(prefix="/api/v1")  # ❌ 禁止在端点文件中指定prefix
```

---

### 6.4. 角色转换强制要求（最高优先级）

**🚨 强制规则**：所有API端点必须在try块之前调用`.upper()`转换role。

**原因**：JWT Token中的role可能是小写或混合大小写，必须统一转换为大写后再传递给Service层。

**✅ 强制模式**：
```python
@router.post("/...")
async def some_endpoint(
    ...,
    current_user: dict = Depends(get_current_user)
) -> Any:
    # 🚨 必须：在try块之前提取并转换
    current_user_id = UUID(current_user["user_id"])
    role = current_user.get("role", "REGULAR").upper()  # ✅ 必须调用.upper()
    
    try:
        result = await service.some_method(..., role)  # ✅ 传递大写的role
        # ✅ 使用success_response包装Service层返回的业务对象
        return success_response(data=result)
    except ...:
        ...
```

**❌ 禁止的错误模式**：
```python
# ❌ 错误1：缺少.upper()调用
role = current_user.get("role", "REGULAR")  # ❌

# ❌ 错误2：在try块内提取
try:
    role = current_user.get("role", "REGULAR").upper()  # ❌ 应在try块之前
    ...
```

---

## 7. 关键约束和注意事项

### 7.1. 唯一性约束处理
- `Brand.name` 具有唯一性约束
- 创建和更新时需捕获`IntegrityError`，转换为`DatabaseIntegrityException`或`ConflictException`

### 7.2. 软删除 vs 硬删除
- `Brand`: 软删除（is_active=False）或硬删除（需SUPERADMIN权限）
- `BrandTopic`: 硬删除（直接DELETE）
- `BrandRoom`: 硬删除（直接DELETE）

### 7.3. 权限模型
- **管理员权限**: `role in ['ADMIN', 'SUPERADMIN']`（🚨 必须使用大写）
- **SUPERADMIN特权**: 硬删除品牌需要SUPERADMIN权限
- **读权限**: 品牌信息完全公开，无需权限（Optional Auth）

**🚨 角色值大小写强制要求（最高优先级）**：
- **API层**：必须调用`.upper()`转换role为大写：`role = current_user.get("role", "REGULAR").upper()`
- **Service层**：必须使用大写`['ADMIN', 'SUPERADMIN']`进行角色比较
- **禁止**使用小写（如`'admin'`, `'superadmin'`）和混合大小写（如`'Admin'`, `'SuperAdmin'`）

### 7.4. 响应构造规范
- Service层返回的响应必须符合Schema定义的嵌套结构
- 标准字段: `code`, `message`, `data`, `timestamp`
- `data`字段的结构必须与Schema定义完全一致

### 7.5. 日志记录规范
- 所有CRUD操作记录日志（INFO级别）
- UUID只记录前8位（脱敏）
- 错误日志记录完整堆栈（ERROR级别）

### 7.6. 导入路径
- Models: `from app.models.brand import Brand, BrandTopic, BrandRoom`
- Schemas: `from app.schemas.brand import BrandCreate, BrandUpdate, ...`
- CRUD: `from app.crud.brand import get_brands, create_brand, ...`
- Service: `from app.services.brand_service import BrandService`
- Exceptions: `from app.core.exceptions import NotFoundException, PermissionDeniedException, DatabaseIntegrityException, InvalidParameterException, ConflictException`
- Deps: `from app.database import get_db`，`from app.core.deps import get_current_user, get_current_user_optional`
- API层必须导入: `from fastapi.responses import JSONResponse`，`from app.core.response import success_response, error_response`，`from app.exceptions import PermissionDeniedException, NotFoundException, InvalidParameterException, ConflictException`，`import logging`
- **🚨 API层响应规范（强制要求）**：所有成功响应必须使用`success_response(data=...)`包装Service层返回的业务对象，禁止直接返回Service层的响应字典

### 7.7. 品牌删除引用检查
- 硬删除品牌前必须检查引用关系（brand_topics和brand_rooms）
- 如果存在引用，返回2003错误，包含引用类型和数量
- 软删除不需要检查引用关系

### 7.8. 全量替换策略（Brand_Rooms）
- `bind_room_brands`使用全量替换策略：先删除旧关联，再插入新关联
- 允许brand_ids为空数组，表示清空绑定
- 保证幂等性和可预测性

---

## 8. 后续步骤

完成本文档的验证后，将进入步骤4.2：

**步骤4.2**: 从模块特定母版生成两个具体的代码生成提示词文档：
1. CRUD层代码生成提示词
2. Service层和API层代码生成提示词

这些文档将用于步骤6的实际代码生成。

---

**文档生成完成时间**: 2026-01-18T12:00:00Z
