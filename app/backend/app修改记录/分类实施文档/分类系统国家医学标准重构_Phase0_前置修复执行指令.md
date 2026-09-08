# 分类系统国家医学标准重构 — Phase 0 前置修复 执行指令

**版本**: V1.0
**创建日期**: 2026-07-28
**基于设计文档**: [分类系统国家医学标准重构方案设计 V1.2.md](./分类系统国家医学标准重构方案设计.md) §0
**目标文件**: 修改 2 个
**工时**: ~1.5h
**类型**: 机械性字段补齐（不需要完整提示词架构，checklist 风格即可）

---

## 背景

融合方案 P1 设计文档规定的 `categories.parent_id` 相关改动在 ORM 模型层和 Schema 层**从未实际实施**。数据库 V5 迁移已创建 `parent_id` 列，但 Python 代码层完全不感知该列。

Phase 0 的目标是在 Phase A（V10 SQL）和 Phase B（代码重构）之前，补齐这两个层面的缺失。

---

## 改动清单

### 文件 1：`app/models/content_management.py` — Category 类

**当前状态**（第 49-87 行）：

```python
class Category(Base):
    """
    全局医学科室/专业方向分类表
    ...
    """
    __tablename__ = "categories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    name = Column(String(100), nullable=False, unique=True, comment='全局医学科室/专业方向分类名称，全局唯一')
    slug = Column(String(120), nullable=True, comment='URL友好的标识符')
    icon = Column(String(255), nullable=True, comment='分类图标名称或URL')
    description = Column(Text, nullable=True, comment='分类描述')
    sort_order = Column(Integer, nullable=False, default=0, comment='排序权重')
    is_active = Column(Boolean, nullable=False, default=True, comment='是否启用')

    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index('idx_categories_sort_order', 'sort_order'),
        Index('idx_categories_is_active', 'is_active'),
    )

    expert_count = 0
    room_count = 0

    def __repr__(self):
        return f"<Category(id={self.id}, name={self.name}, sort_order={self.sort_order})>"
```

**需要执行的 4 个修改点**：

#### 修改点 1-1：导入新增 `text`

在文件头部导入区域（第 5-9 行），在 `from sqlalchemy.sql import func` 之后追加一行：

```python
from sqlalchemy.sql import text
```

当前导入：
```python
from sqlalchemy import Column, String, Text, Integer, ForeignKey, Boolean, Index, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
```

修改后：
```python
from sqlalchemy import Column, String, Text, Integer, ForeignKey, Boolean, Index, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func, text
```

#### 修改点 1-2：`name` 字段移除 `unique=True`

将第 62 行：
```python
name = Column(String(100), nullable=False, unique=True, comment='全局医学科室/专业方向分类名称，全局唯一')
```

改为：
```python
name = Column(String(100), nullable=False, comment='全局医学科室/专业方向分类名称。唯一性由 V5 部分唯一索引保障：uq_root_category_name (parent_id IS NULL) + uq_sub_category_name (parent_id IS NOT NULL, name)')
```

> ⚠️ **部署前注意**：ORM 模型中已移除 `unique=True`，但数据库中旧的 `categories_name_key` 全局唯一约束**在 V5 迁移执行前仍然存在**。V5 迁移 SQL 已执行 `DROP CONSTRAINT IF EXISTS categories_name_key`。如果 Phase 0 代码在 V5 之前部署到已有数据的实例，ORM 层面的 `unique=True` 移除不会影响数据库已有约束——SQLAlchemy 不会自动删除数据库约束。

#### 修改点 1-3：新增 `parent_id` Column + relationship

在 `is_active` 字段之后、`created_at` 字段之前（约第 67 行位置），插入以下代码：

```python
    # 层级关系（V5 迁移在数据库层创建，P1 设计在 ORM 层映射）
    parent_id = Column(
        UUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="RESTRICT"),
        nullable=True,
        comment='父分类ID。NULL=根分类（一级科目）；非NULL=子分类（二级科目）'
    )
```

并在 `updated_at` 之后（约第 71 行位置），插入 relationship 定义：

```python
    # 自引用关系
    parent = relationship("Category", remote_side="Category.id", backref="children")
```

> ⚠️ **`remote_side` 必须指定**：自引用 relationship 中，`remote_side` 必须显式传入 `"Category.id"`（字符串引用，避免类未定义时的 NameError），否则 SQLAlchemy 无法正确解析外键方向。

#### 修改点 1-4：`__table_args__` 新增部分唯一索引

将当前的 `__table_args__`：
```python
    __table_args__ = (
        Index('idx_categories_sort_order', 'sort_order'),
        Index('idx_categories_is_active', 'is_active'),
    )
```

改为：
```python
    __table_args__ = (
        Index('idx_categories_sort_order', 'sort_order'),
        Index('idx_categories_is_active', 'is_active'),
        Index('idx_categories_parent_id', 'parent_id'),
        # 部分唯一索引：同层分类名唯一（V5 迁移在 DB 层创建，此处 ORM 映射）
        # uq_root_category_name: 根分类名全局唯一
        Index('uq_root_category_name', 'name', unique=True,
              postgresql_where=text("parent_id IS NULL")),
        # uq_sub_category_name: 同一父分类下子分类名唯一
        Index('uq_sub_category_name', 'parent_id', 'name', unique=True,
              postgresql_where=text("parent_id IS NOT NULL")),
    )
```

**验证**：Python REPL 中执行 `from app.models.content_management import Category; c = Category(); c.parent_id = uuid.uuid4()` 无 `AttributeError`。

---

### 文件 2：`app/schemas/content_management.py` — 3 个 Schema 类

#### 修改点 2-1：`CategoryCreate` 新增 `parent_id`

当前（约第 96-99 行）：
```python
class CategoryCreate(CategoryBase):
    """创建分类请求Schema"""
    sort_order: Optional[int] = Field(0, ge=0, description="排序权重")
    is_active: Optional[bool] = Field(True, description="是否启用")
```

改为（在 `sort_order` 之前插入 `parent_id`）：
```python
class CategoryCreate(CategoryBase):
    """创建分类请求Schema"""
    parent_id: Optional[UUID] = Field(None, description="父分类ID。NULL=一级分类，非NULL=二级分类")
    sort_order: Optional[int] = Field(0, ge=0, description="排序权重")
    is_active: Optional[bool] = Field(True, description="是否启用")
```

#### 修改点 2-2：`CategoryUpdate` 新增 `parent_id`

当前（约第 102-111 行）：
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

改为（在 `icon` 之后插入 `parent_id`）：
```python
class CategoryUpdate(BaseModel):
    """更新分类请求Schema（部分更新）"""
    model_config = ConfigDict(from_attributes=True)

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    slug: Optional[str] = None
    icon: Optional[str] = None
    parent_id: Optional[UUID] = Field(None, description="父分类ID。NULL=提升为一级分类")
    description: Optional[str] = None
    sort_order: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None
```

#### 修改点 2-3：`CategoryItem` 新增 `parent_id`

当前（约第 114-124 行）：
```python
class CategoryItem(CategoryBase):
    """分类响应Schema"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    sort_order: int
    is_active: bool
    expert_count: int = Field(0, alias="expert_count", description="关联的专家数（管理端填充）")
    room_count: int = Field(0, alias="room_count", description="关联的直播间数（管理端填充）")
    created_at: datetime
    updated_at: datetime
```

改为（在 `sort_order` 之后插入 `parent_id`）：
```python
class CategoryItem(CategoryBase):
    """分类响应Schema"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    parent_id: Optional[UUID] = Field(None, description="父分类ID。NULL=一级分类")
    sort_order: int
    is_active: bool
    expert_count: int = Field(0, alias="expert_count", description="关联的专家数（管理端填充）")
    room_count: int = Field(0, alias="room_count", description="关联的直播间数（管理端填充）")
    created_at: datetime
    updated_at: datetime
```

**验证**：`RoomCategoryItem(CategoryItem)` 自动继承 `parent_id`，无需额外修改。

---

## 执行验证 Checklist

```
□ 文件 1 (content_management.py):
  □ text 导入已追加到 sqlalchemy.sql import
  □ name.unique=True 已移除，注释已更新
  □ parent_id Column 已添加（位置: is_active 之后, created_at 之前）
  □ parent relationship 已添加（remote_side="Category.id"）
  □ __table_args__ 含 idx_categories_parent_id + uq_root_category_name + uq_sub_category_name
  □ Category 类的 Docstring 保持不变
  □ Tag / SessionTag / LiveRoomCategory 类未做任何修改

□ 文件 2 (schemas/content_management.py):
  □ CategoryCreate 含 parent_id: Optional[UUID] = None
  □ CategoryUpdate 含 parent_id: Optional[UUID] = None
  □ CategoryItem 含 parent_id: Optional[UUID] = None
  □ RoomCategoryItem 自动继承 parent_id（无需修改）

□ 验证:
  □ Python REPL: Category().parent_id = uuid.uuid4() 无 AttributeError
  □ Python REPL: CategoryItem.schema() 输出含 parent_id 字段
  □ CategoryCreate.schema() 输出含 parent_id 字段
```

---

> **最后更新**: 2026-07-28 | **状态**: 🟢 待执行
