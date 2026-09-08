# 融合方案 P1 — Model + Schema 代码生成提示词

**版本**: V1.0  
**创建日期**: 2026-06-23  
**基于设计文档**: `app修改记录/融合方案最终设计_A2+C.md`、`app修改记录/融合方案_提示词编写规范借鉴.md`  
**目标文件**: 新建 2 个 + 修改 5 个

---

## 1. 角色定义 (Role Definition)

你是一名精通 SQLAlchemy 2.0 + PostgreSQL + Pydantic v2 的数据库建模专家。
你理解受控词表（Controlled Vocabulary）的设计模式——将自由文本字段升级为 FK 约束，确保数据一致性在数据库层面得到保证。
你熟悉本项目的学院派（Clean Architecture）分层风格和已有的代码模式，能感知现有代码中的"关键观察点"（导入顺序、命名习惯、索引创建方式、FK 删除策略）并严格遵循之。

**三个必须**：
- 必须提供完整、可运行的模型和 Schema 代码
- 必须保持与现有代码风格完全一致
- 必须同步更新 `__init__.py` 注册新模型和 Schema

---

## 2. 任务目标 (Task Objective)

### 2.1 新建文件（共 2 个）

| 文件 | 内容 | 说明 |
|:-----|:-----|:-----|
| `app/models/expert_departments.py` | `ExpertDepartment` 模型类 | 科室受控词表，`name` UNIQUE NOT NULL, `category_id` FK→categories RESTRICT, `synonyms` JSONB, `is_active`, 时间戳 |
| `app/schemas/expert_departments.py` | 5 个 Schema 类 | `ExpertDepartmentCreate` / `Update` / `Item` / `ListResponse` / `BriefItem` |

### 2.2 修改已有文件（共 5 个）

| 文件 | 修改内容 | 程度 |
|:-----|:---------|:----:|
| `app/models/experts.py` | ① 删 `department` 列（第 44 行） ② 新增 `department_id` FK + 索引 ③ `category_id` 改为 `nullable=False` ④ 新增 `expert_department` relationship | ~10 行改 |
| `app/models/content_management.py` | ① `Category.name` 移除 `unique=True` ② 新增 `parent_id` 自引用 FK (RESTRICT) ③ `__table_args__` 新增 2 个部分唯一索引 | ~15 行改 |
| `app/schemas/experts.py` | ① `ExpertBase` / `ExpertUpdate` 中 `department` → `department_name` ② `ExpertItem` 新增 `department_name`/`department_id`/`category_name` ③ `FeaturedExpertItem` 中 `department` → `department_name` | ~10 行改 |
| `app/models/__init__.py` | 末尾追加 `from .expert_departments import ExpertDepartment` | +1 行 |
| `app/schemas/__init__.py` | 新增 `from .expert_departments import (...)` 块 | +8 行 |

### 2.3 禁止事项

- ❌ 不修改 `app/models/experts.py` 中的 `UserExpertSubscription` 和 `LiveSessionExpert` 模型
- ❌ 不修改 `app/models/content_management.py` 中的 `Tag`、`SessionTag`、`LiveRoomCategory` 模型
- ❌ 不修改 `app/api/` 下的任何文件
- ❌ 不修改 `app/services/` 下的任何文件
- ❌ 不修改 `app/crud/` 下的任何文件
- ❌ 不创建 SQL 迁移文件（DDL 由 P4 阶段的迁移提示词处理）
- ❌ 不引入数据库触发器

---

## 3. 核心上下文 (Core Context)

### 3.1 技术栈

```
Python 3.9+ | SQLAlchemy 2.0 (async) | Pydantic v2 | PostgreSQL 15
Base 类位置: from app.database import Base  (不是 app.models.base)
数据库初始化: import app.models → 通过 __init__.py 自动注册
```

### 3.2 已有代码参考

#### 参考 A：`app/models/experts.py` — Expert 模型（完整内容，见 §A）

**关键观察点（12 个）**：

1. **Base 导入方式**: `from app.database import Base`
2. **导入顺序**: 标准库→sqlalchemy→sqlalchemy.dialects→sqlalchemy.orm→sqlalchemy.sql→app
3. **TIMESTAMP 导入**: `from sqlalchemy import ... TIMESTAMP`（不是从 `dialects.postgresql`）
4. **UUID 导入**: `from sqlalchemy.dialects.postgresql import UUID`（不从 `sqlalchemy`）
5. **Enum 用法**: 继承 `str, enum.Enum`，无 `native_enum=False`
6. **UUID 主键**: `UUID(as_uuid=True), primary_key=True, default=uuid.uuid4`
7. **时间戳**: `TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()`
8. **FK ondelete**: `ForeignKey("categories.id", ondelete="SET NULL")` → Expert → Category 用 SET NULL
9. **__table_args__**: 用 `Index('idx_...', 'col1', 'col2')` 显式命名
10. **relationship**: 用 `lazy="select"` 模式
11. **__repr__**: 只返回 id + name，不暴露敏感信息
12. **JSONB 导入**: `from sqlalchemy.dialects.postgresql import UUID, JSONB`

#### 参考 B：`app/models/content_management.py` — Category 模型（完整内容，见 §B）

**额外关键观察点**：

- `Category.name` — 当前为 `unique=True`（在 Column 上），需移除，改为部分索引
- `LiveRoomCategory.is_primary` — `Boolean, nullable=False, default=False`
- `LiveRoomCategory.category_id` — `ForeignKey("categories.id", ondelete="CASCADE")`

#### 参考 C：`app/schemas/experts.py` — ExpertItem Schema（完整内容，见 §C）

**额外关键观察点**：

- Pydantic v2：`model_config = ConfigDict(from_attributes=True)`
- `ExpertBase` 是纯字段定义（无 `id`、无 `created_at`）
- `ExpertItem(ExpertBase)` 继承 `ExpertBase`，追加 `id` + `created_at` + `updated_at`
- `ExpertUpdate` 所有字段均为 `Optional[...] = None`

#### 参考 D：`app/models/__init__.py` — 注册模式

```python
# 专家模块模型（新增）
from .experts import Expert, UserExpertSubscription, LiveSessionExpert
```

新模型按照相同的注释模式追加。

---

## 4. 架构约束 (Architecture Constraints)

### 4.1 FK 删除策略对照表

| FK 关系 | ondelete | 原因 |
|:--------|:--------|:-----|
| `Expert.category_id` → `categories.id` | **SET NULL** | 分类被删除时专家不被级联删除 |
| `Expert.department_id` → `expert_departments.id` | **SET NULL** | 科室被删除时专家不被级联删除 |
| `ExpertDepartment.category_id` → `categories.id` | **RESTRICT** | **禁止删除仍有科室的分类** |
| `Category.parent_id` → `categories.id` | **RESTRICT** | **禁止删除仍有子分类的父分类** |

**RESTRICT 的含义**：在 PostgreSQL 中，`ON DELETE RESTRICT` 阻止删除操作（如果 FK 引用存在）。分类本身使用 `is_active` 软删除，不走物理 DELETE。

### 4.2 JSONB 列的精确写法

```python
# ✅ 正确
synonyms = Column(JSONB, nullable=False, default=list)

# ❌ 错误
synonyms = Column(JSONB, nullable=False, default='[]')  # 存的是字符串，不是 JSON 数组
synonyms = Column(JSONB, default=[])                      # 变异默认值！必须用 default=list
```

### 4.3 部分唯一索引的精确写法

```python
from sqlalchemy.sql import text

__table_args__ = (
    # 根分类名称全局唯一（parent_id IS NULL 时生效）
    Index('uq_root_category_name', 'name', unique=True,
          postgresql_where=text("parent_id IS NULL")),
    # 子分类在同父类下唯一（parent_id IS NOT NULL 时生效）
    Index('uq_sub_category_name', 'parent_id', 'name', unique=True,
          postgresql_where=text("parent_id IS NOT NULL")),
)
```

### 4.4 name 列移除 unique=True

`Category.name` 当前在 Column 定义上有 `unique=True`。P1 必须移除这个属性，改用部分索引（见 §4.3）。**原因**：PostgreSQL 的 `UNIQUE` 约束无法区分 `parent_id IS NULL` 和 `parent_id IS NOT NULL`——全局 UNIQUE 会阻止"冠脉介入组"在"心内科"和"神经外科"下同时存在。

**注意**：旧的 `categories_name_key` 约束的删除（`DROP CONSTRAINT`）由 P4 迁移 SQL 处理。P1 只改 ORM 模型定义，不执行数据库迁移。

### 4.5 Schema 命名规范

| Schema 类 | 继承 | 用途 |
|:---------|:----|:-----|
| `ExpertDepartmentCreate` | `BaseModel` | 管理员创建科室（name + category_id + synonyms） |
| `ExpertDepartmentUpdate` | `BaseModel` | 管理员更新科室（全部字段 Optional） |
| `ExpertDepartmentItem` | `BaseModel` | 列表/详情响应（含 id + category_name + expert_count） |

### 4.6 ExpertBase 和 ExpertUpdate 中 department → department_name

**原因**：方案 C 将 `department` 从自由文本升级为受控词表 FK。前端请求中的字段名同步改为 `department_name`（匹配后由 Service 转为 `department_id`）。

**保留 `category_id` 字段**：管理员仍可通过直接传入 `category_id` 来显式指定分类（不经过科室匹配）。

---

## 5. 代码生成要求 (Specific Code Generation Requirements)

### 5.1 新文件：`app/models/expert_departments.py`

**文件头部**：

```python
"""
专家科室受控词表 — 数据库模型

将 department 从自由文本升级为受控词表 FK。
每个科室名全局唯一，同义词存储在 synonyms JSONB 数组中。
科室 → 分类的映射在 category_id 中，是唯一的真相源。
"""
```

**导入语句**（严格参照 `app/models/experts.py` 的模式）：

```python
import uuid
from sqlalchemy import Column, String, Boolean, ForeignKey, Index, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
```

**模型类定义**：

```python
class ExpertDepartment(Base):
    """
    专家科室受控词表

    取代 experts.department 自由文本字段，确保每个科室名全局唯一。
    同义词列表通过 synonyms JSONB 存储，导入时直接匹配即可，不需要管理者手动创建。
    is_verified 标记是否为已审核的标准科室。
    """
    __tablename__ = "expert_departments"

    # 核心标识
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
                comment='主键UUID，在应用层生成')

    # 标准科室名称 — 全局唯一（唯一约束由 DDL 级别保证，ORM 用 unique=True）
    name = Column(String(120), nullable=False, unique=True,
                  comment='标准科室名称，全局唯一，如"乳腺外科"、"冠脉介入组"')

    # 科室 → 分类映射（唯一真相源）
    category_id = Column(
        UUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="RESTRICT"),
        nullable=False,
        comment='科室所属的主分类ID。RESTRICT 防止误删关联的分类'
    )

    # 同义词列表（JSONB 数组）
    synonyms = Column(JSONB, nullable=False, default=list,
                      comment='同义词列表 JSON 数组，如 ["乳腺科","乳房外科"]')

    # 业务字段
    is_active = Column(Boolean, nullable=False, default=True,
                       comment='是否启用。false 表示该科室不再用于新专家')
    is_verified = Column(Boolean, nullable=False, default=False,
                         comment='是否已审核。false=自适应创建待确认，true=已审核标准词')

    # 时间戳
    created_at = Column(TIMESTAMP(timezone=True), nullable=False,
                        server_default=func.now(), comment='创建时间')
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False,
                        server_default=func.now(), onupdate=func.now(), comment='更新时间')

    # 索引定义
    __table_args__ = (
        Index('idx_expert_departments_category_id', 'category_id'),
        Index('idx_expert_departments_is_active', 'is_active'),
        Index('idx_expert_departments_is_verified', 'is_verified'),
    )

    # 关联关系
    category = relationship("Category", lazy="select")

    def __repr__(self):
        return f"<ExpertDepartment(id={self.id}, name={self.name})>"
```

**关键点**：
- `name` 有 `unique=True`（DDL 级别唯一）
- `category_id` 用 `RESTRICT`（不自动删除分类）
- `synonyms` 用 `default=list`（不是 `default='[]'`）
- `is_verified` 默认 `False`（自适应创建的需要审核）
- `__table_args__` 中显式命名所有索引

### 5.2 修改：`app/models/experts.py`

**改动 1 — 删 `department` 列**：

```python
    # ❌ 删除这行（第 44 行）
    # department = Column(String(120), nullable=True, ...)
```

**改动 2 — 新增 `department_id` FK**：

在 `expertise_areas` 之后、`bio` 之前插入：

```python
    # 受控词表科室关联（替代原来的自由文本 department 字段）
    department_id = Column(
        UUID(as_uuid=True),
        ForeignKey("expert_departments.id", ondelete="SET NULL"),
        nullable=True,
        comment='科室 ID，关联 expert_departments 受控词表。NULL 表示未映射标准科室'
    )
```

**改动 3 — `category_id` 改为 NOT NULL**：

```python
    category_id = Column(
        UUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=False,  # ← 从 True 改为 False
        comment='专家主专业分类，关联全局 categories.id。由 department_id 推导，应用层保证一致性'
    )
```

**改动 4 — 新增索引**：

在 `__table_args__` 中追加：

```python
    __table_args__ = (
        Index('idx_experts_is_featured', 'is_featured', 'sort_order'),
        Index('idx_experts_is_active', 'is_active'),
        Index('idx_experts_user_id', 'user_id'),
        Index('idx_experts_category_id', 'category_id'),
        Index('idx_experts_department_id', 'department_id'),  # ← 新增
    )
```

**改动 5 — 新增 relationship**：

```python
    # 受控词表科室关联（新增）
    expert_department = relationship("ExpertDepartment", lazy="select")
```

### 5.3 修改：`app/models/content_management.py`

**改动 1 — `Category.name` 移除 `unique=True`**：

```python
    # 修改前
    name = Column(String(100), nullable=False, unique=True, comment='...')

    # 修改后
    name = Column(String(100), nullable=False, comment='分类名称')
```

**改动 2 — 新增 `parent_id` FK**：

在 `sort_order` 之后、`is_active` 之前插入：

```python
    parent_id = Column(
        UUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="RESTRICT"),
        nullable=True,
        comment='父分类ID。NULL=根分类（一级分类）；非NULL=子分类（具体专业方向）'
    )
```

**改动 3 — 替换 `__table_args__`**：

```python
    # 修改前
    __table_args__ = (
        Index('idx_categories_sort_order', 'sort_order'),
        Index('idx_categories_is_active', 'is_active'),
    )

    # 修改后
    __table_args__ = (
        Index('idx_categories_sort_order', 'sort_order'),
        Index('idx_categories_is_active', 'is_active'),
        Index('idx_categories_parent_id', 'parent_id'),  # ← 新增普通索引
        # 部分唯一索引（替代原来的 unique=True）
        Index('uq_root_category_name', 'name', unique=True,
              postgresql_where=text("parent_id IS NULL")),
        Index('uq_sub_category_name', 'parent_id', 'name', unique=True,
              postgresql_where=text("parent_id IS NOT NULL")),
    )
```

**改动 4 — 新增导入**：

需要在 `app/models/content_management.py` 顶部追加：

```python
from sqlalchemy.sql import text  # 用于部分索引的 postgresql_where
```

当前导入行：
```python
from sqlalchemy import Column, String, Text, Integer, ForeignKey, Boolean, Index, TIMESTAMP
```

改为：
```python
from sqlalchemy import Column, String, Text, Integer, ForeignKey, Boolean, Index, TIMESTAMP
from sqlalchemy.sql import text
```

### 5.4 新文件：`app/schemas/expert_departments.py`

```python
"""
专家科室受控词表 — Pydantic Schemas 定义
"""
import uuid
import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field


class ExpertDepartmentCreate(BaseModel):
    """管理员创建科室"""
    name: str = Field(..., min_length=1, max_length=120, description="标准科室名称")
    category_id: uuid.UUID = Field(..., description="所属主分类ID")
    synonyms: List[str] = Field(default_factory=list, description="同义词列表")
    is_verified: Optional[bool] = Field(False, description="是否已审核")


class ExpertDepartmentUpdate(BaseModel):
    """管理员更新科室（全部字段可选）"""
    name: Optional[str] = Field(None, min_length=1, max_length=120, description="标准科室名称")
    category_id: Optional[uuid.UUID] = Field(None, description="所属主分类ID")
    synonyms: Optional[List[str]] = Field(None, description="同义词列表")
    is_active: Optional[bool] = Field(None, description="是否启用")
    is_verified: Optional[bool] = Field(None, description="是否已审核")


class ExpertDepartmentItem(BaseModel):
    """科室列表/详情响应"""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    category_id: uuid.UUID
    category_name: Optional[str] = Field(None, description="分类名称（JOIN填充）")
    synonyms: List[str] = Field(default_factory=list, description="同义词列表")
    is_active: bool
    is_verified: bool
    expert_count: int = Field(0, description="关联的专家数")
    created_at: datetime.datetime
    updated_at: datetime.datetime


class ExpertDepartmentBriefItem(BaseModel):
    """科室简要信息（用于下拉选择器）"""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    category_id: uuid.UUID
    category_name: Optional[str] = None


class ExpertDepartmentListResponse(BaseModel):
    """科室分页列表响应"""
    code: int = Field(200, description="状态码")
    message: str = Field("success", description="响应消息")
    data: dict = Field(..., description="{ items: [...], total: N, page: N, size: N }")
    timestamp: datetime.datetime
```

### 5.5 修改：`app/schemas/experts.py`

**改动 1 — `ExpertBase` 中 `department` → `department_name`**：

```python
    # 修改前
    department: Optional[str] = Field(None, max_length=120, description="展示用细分科室...")

    # 修改后
    department_name: Optional[str] = Field(None, max_length=120, description="科室名称（匹配 expert_departments 受控词表）")
```

**改动 2 — `ExpertItem` 新增 3 个字段**：

```python
class ExpertItem(ExpertBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: Optional[uuid.UUID] = None
    category_id: Optional[uuid.UUID] = None
    category_name: Optional[str] = Field(None, description="分类名称")          # ← 新增
    department_id: Optional[uuid.UUID] = Field(None, description="科室ID")      # ← 新增
    department_name: Optional[str] = Field(None, description="标准科室名称")    # ← 新增
    is_featured: bool
    is_active: bool
    sort_order: int
    created_at: datetime.datetime
    updated_at: datetime.datetime
```

**改动 3 — `ExpertUpdate` 中 `department` → `department_name`**：

```python
    # 修改前
    department: Optional[str] = Field(None, max_length=120, description="...")

    # 修改后
    department_name: Optional[str] = Field(None, max_length=120, description="科室名称（匹配 expert_departments 受控词表）")
```

**改动 4 — `FeaturedExpertItem` 中 `department` → `department_name`**：

```python
    # 修改前
    department: Optional[str] = None

    # 修改后
    department_name: Optional[str] = None
```

### 5.6 修改：`app/models/__init__.py`

在文件末尾追加（保持与已有注释风格一致）：

```python
# 专家科室受控词表模型（新增 — 融合方案 P1）
from .expert_departments import ExpertDepartment
```

**严格规则**：
- 必须追加在文件最末尾
- 不修改、不删除、不重新排序任何现有导入
- 注释格式与已有行一致

### 5.7 修改：`app/schemas/__init__.py`

在文件末尾追加：

```python
# 专家科室受控词表 Schema（新增 — 融合方案 P1）
from .expert_departments import (
    ExpertDepartmentCreate,
    ExpertDepartmentUpdate,
    ExpertDepartmentItem,
    ExpertDepartmentBriefItem,
    ExpertDepartmentListResponse,
)
```

---

## 6. 完整性检查清单 (Completeness Checklist)

### 6.1 ExpertDepartment 模型

- ✅ `name` 有 `unique=True`
- ✅ `category_id` 的 `ForeignKey` 用 `ondelete="RESTRICT"`
- ✅ `synonyms` 的 `default=list`
- ✅ `is_verified` 默认 `False`
- ✅ `idx_expert_departments_category_id` 索引已创建
- ✅ `idx_expert_departments_is_active` 索引已创建
- ✅ `idx_expert_departments_is_verified` 索引已创建
- ✅ `category` relationship 用 `lazy="select"`
- ✅ `__repr__` 只返回 `id` 和 `name`

### 6.2 Expert 模型改造

- ✅ `department` 列已删除
- ✅ `department_id` 新增，`ForeignKey("expert_departments.id", ondelete="SET NULL")`
- ✅ `category_id` 的 `nullable` 改为 `False`
- ✅ `idx_experts_department_id` 索引已追加到 `__table_args__`
- ✅ `expert_department` relationship 已新增

### 6.3 Category 模型改造

- ✅ `name` 的 `unique=True` 已移除
- ✅ `parent_id` 新增，`ForeignKey("categories.id", ondelete="RESTRICT")`
- ✅ `idx_categories_parent_id` 普通索引已创建
- ✅ `uq_root_category_name` 部分唯一索引已创建
- ✅ `uq_sub_category_name` 部分唯一索引已创建
- ✅ `from sqlalchemy.sql import text` 已导入

### 6.4 Schema 改造

- ✅ `ExpertDepartmentCreate` 含 `name`、`category_id`、`synonyms`、`is_verified`
- ✅ `ExpertDepartmentUpdate` 全部字段 Optional
- ✅ `ExpertDepartmentItem` 含 `category_name`（Optional）和 `expert_count`
- ✅ `ExpertBase` / `ExpertUpdate` 中 `department` 改为 `department_name`
- ✅ `ExpertItem` 新增 `department_name`、`department_id`、`category_name`
- ✅ `FeaturedExpertItem` 中 `department` 改为 `department_name`

### 6.5 注册

- ✅ `app/models/__init__.py` 追加 `ExpertDepartment` 导入
- ✅ `app/schemas/__init__.py` 追加 5 个 Schema 类导入
- ✅ 注释格式与已有导入块一致

### 6.6 全局约束

- ✅ `app/models/experts.py` 的 `UserExpertSubscription` 和 `LiveSessionExpert` 未被修改
- ✅ `app/models/content_management.py` 的 `Tag`、`SessionTag`、`LiveRoomCategory` 未被修改
- ✅ 所有时间戳用 `server_default=func.now()` + `onupdate=func.now()`
- ✅ 所有索引在 `__table_args__` 中显式命名
- ✅ UUID 主键用 `UUID(as_uuid=True), primary_key=True, default=uuid.uuid4`
- ✅ Pydantic v2 用 `model_config = ConfigDict(from_attributes=True)`

### 6.7 部署前注意（在本提示词产出的代码中注明）

- ⚠️ `categories_name_key` 旧约束仍存在于数据库中（P1 不删它）。P4 的迁移 SQL 会执行 `DROP CONSTRAINT IF EXISTS categories_name_key`
- ⚠️ `department` 列仍存在于数据库中（P1 不改）。P4 的迁移 SQL 会执行 `DROP COLUMN department`
- ⚠️ `category_id` 在数据库中的 `nullable` 未改（P1 只改了 ORM 模型）。P4 的迁移 SQL 会执行 `ALTER COLUMN category_id SET NOT NULL`
- ⚠️ `expert_departments` 表在数据库中尚不存在（P1 只写了 ORM 模型）。P4 的迁移 SQL 会执行 `CREATE TABLE expert_departments`

---

## 附录 A：`app/models/experts.py` — 完整内容

```
（嵌入该文件的完整 180 行代码，此处省略以节省篇幅。在实际执行 P1 时，请读取文件并嵌入。）
```

## 附录 B：`app/models/content_management.py` — 完整内容

```
（嵌入该文件的完整 158 行代码，此处省略以节省篇幅。在实际执行 P1 时，请读取文件并嵌入。）
```

## 附录 C：`app/schemas/experts.py` — 完整内容

```
（嵌入该文件的完整 171 行代码，此处省略以节省篇幅。在实际执行 P1 时，请读取文件并嵌入。）
```

## 附录 D：`app/models/__init__.py` — 导入模板

```
（嵌入该文件的完整 34 行代码，此处省略以节省篇幅。在实际执行 P1 时，请读取文件并嵌入。）
```

## 附录 E：`app/schemas/__init__.py` — 导入模板

```
（嵌入该文件的完整 131 行代码，此处省略以节省篇幅。在实际执行 P1 时，请读取文件并嵌入。）
```

---

## 7. 最终交付 (Final Deliverable)

根据以上要求，生成以下 **7 个文件的修改**：

1. **新建** `app/models/expert_departments.py` — ExpertDepartment 模型
2. **修改** `app/models/experts.py` — 删 department、加 department_id FK、category_id NOT NULL
3. **修改** `app/models/content_management.py` — 加 parent_id、部分唯一索引
4. **新建** `app/schemas/expert_departments.py` — 5 个 Schema 类
5. **修改** `app/schemas/experts.py` — department → department_name，新增 3 个响应字段
6. **修改** `app/models/__init__.py` — 注册 ExpertDepartment
7. **修改** `app/schemas/__init__.py` — 注册新 Schema
