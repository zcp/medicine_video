# 内容管理模块设计文档-标签-分类-场次标签关联 SQLAlchemy 模型与 Pydantic Schema 一致性检查提示词

**版本**: V1.0  
**创建日期**: 2026-01-18  
**适用于**: 内容管理模块设计文档-标签-分类-场次标签关联 SQLAlchemy 模型与 Pydantic Schema 一致性检查  
**基于文档**: docs/03_系统设计/直播核心功能设计文档_v6_内容管理模块设计文档-标签-分类-场次标签关联.md

---

## 1. 角色定义 (Role Definition)

你是一名资深的 FastAPI 后端架构师，专注于 API 设计和数据模型的最佳实践。你的任务是审查内容管理模块设计文档-标签-分类-场次标签关联的 SQLAlchemy 模型（`content_management.py`）和 Pydantic Schema（`schemas/content_management.py`）之间的一致性、安全性和功能适配性。

**核心职责**:
- 验证数据模型的完整性和一致性
- 识别潜在的安全风险和数据泄露问题
- 确保 API 设计符合 RESTful 最佳实践
- 检查数据验证规则的完备性

---

## 2. 任务目标 (Task Objective)

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

## 3. 核心输入 (Core Input)

### 3.1. SQLAlchemy 模型代码

**文件路径**: `live_core_service/app/models/content_management.py`

**【请在此处粘贴完整的 `app/models/content_management.py` 代码】**

### 3.2. Pydantic Schema 代码

**文件路径**: `live_core_service/app/schemas/content_management.py`

**【请在此处粘贴完整的 `app/schemas/content_management.py` 代码】**

---

## 4. 审查清单 (Audit Checklist)

### 4.1. 字段命名一致性

**检查项列表**:
- [ ] 检查每个模型的字段名称是否与对应Schema中的字段名称完全一致
- [ ] 检查是否存在拼写差异或语义偏移（如 `banner_url` vs `bannerURL`）

**重点字段检查对比表**:

| Model 字段 | Schema 字段 | 是否一致 | 备注 |
|-----------|-----------|---------|------|
| `Tag.id` | `TagItem.id` | ? | UUID主键 |
| `Tag.name` | `TagBase.name`, `TagItem.name` | ? | 标签名称 |
| `Tag.slug` | `TagBase.slug`, `TagItem.slug` | ? | URL友好标识符 |
| `Tag.description` | `TagBase.description`, `TagItem.description` | ? | 标签描述 |
| `Tag.is_active` | `TagCreate.is_active`, `TagItem.is_active` | ? | 是否启用 |
| `Tag.created_at` | `TagItem.created_at` | ? | 创建时间 |
| `Tag.updated_at` | `TagItem.updated_at` | ? | 更新时间 |
| `Category.id` | `CategoryItem.id` | ? | UUID主键 |
| `Category.name` | `CategoryBase.name`, `CategoryItem.name` | ? | 分类名称 |
| `Category.slug` | `CategoryBase.slug`, `CategoryItem.slug` | ? | URL友好标识符 |
| `Category.icon` | `CategoryBase.icon`, `CategoryItem.icon` | ? | 分类图标 |
| `Category.description` | `CategoryBase.description`, `CategoryItem.description` | ? | 分类描述 |
| `Category.sort_order` | `CategoryCreate.sort_order`, `CategoryItem.sort_order` | ? | 排序权重 |
| `Category.is_active` | `CategoryCreate.is_active`, `CategoryItem.is_active` | ? | 是否启用 |
| `Category.created_at` | `CategoryItem.created_at` | ? | 创建时间 |
| `Category.updated_at` | `CategoryItem.updated_at` | ? | 更新时间 |
| `SessionTag.session_id` | - | ? | 复合主键，不在Schema中 |
| `SessionTag.tag_id` | - | ? | 复合主键，不在Schema中 |
| `SessionTag.created_at` | - | ? | 创建时间，不在Schema中 |

**检查方法**: 逐字段对比Model和Schema中的字段名称，确保完全一致。

---

### 4.2. 数据类型兼容性

**检查项列表**:
- [ ] UUID类型字段是否在Schema中映射为`uuid.UUID`
- [ ] String(n)类型字段是否在Schema中映射为`str`，并使用`Field(max_length=n)`限制
- [ ] Text类型字段是否在Schema中映射为`str`（不限长度）
- [ ] Integer类型字段是否在Schema中映射为`int`
- [ ] TIMESTAMP(timezone=True)类型字段是否在Schema中映射为`datetime`
- [ ] Boolean类型字段是否在Schema中映射为`bool`

**类型映射表**:

| SQLAlchemy 类型 | Pydantic 类型 | 验证规则 | 是否正确映射 | 示例字段 |
|----------------|--------------|---------|------------|---------|
| `UUID(as_uuid=True)` | `uuid.UUID` | - | ? | `Tag.id`, `Category.id` |
| `String(80)` | `str` | `Field(max_length=80)` | ? | `Tag.name` |
| `String(100)` | `str` | `Field(max_length=100)` | ? | `Tag.slug` |
| `String(120)` | `str` | `Field(max_length=120)` | ? | `Category.slug` |
| `String(255)` | `str` | `Field(max_length=255)` | ? | `Category.icon` |
| `Text` | `str` | 无长度限制 | ? | `Tag.description`, `Category.description` |
| `Integer` | `int` | `Field(ge=0)` | ? | `Category.sort_order` |
| `Boolean` | `bool` | - | ? | `Tag.is_active`, `Category.is_active` |
| `TIMESTAMP(timezone=True)` | `datetime` | - | ? | `Tag.created_at`, `Tag.updated_at` |

---

### 4.3. Create Schema审查

**检查项列表**:
- [ ] Create Schema是否包含创建所需的所有必填字段
- [ ] Create Schema是否**正确排除**了系统生成字段（`id`, `created_at`, `updated_at`）
- [ ] Create Schema是否**正确排除**了外键字段（从路径参数或JWT Token获取）

**关键问题说明**:

1. **Create Schema中是否错误地包含了`id`字段？**
   - ❌ 错误：`id`应由数据库或应用层生成
   - ✅ 正确：Create Schema不包含`id`

2. **Create Schema中是否错误地包含了时间戳字段？**
   - ❌ 错误：`created_at`和`updated_at`应由数据库自动生成
   - ✅ 正确：Create Schema不包含时间戳字段

3. **Create Schema中是否错误地包含了外键字段？**
   - ❌ 错误：外键应从路径参数获取
   - ✅ 正确：Create Schema不包含外键字段

**Create Schema检查表**:

| Schema | 是否包含 `id` | 是否包含 `created_at` | 是否包含 `updated_at` | 是否包含外键 | 是否符合要求 |
|--------|-------------|---------------------|---------------------|------------|------------|
| `TagCreate` | ? | ? | ? | N/A | ? |
| `CategoryCreate` | ? | ? | ? | N/A | ? |
| `SessionTagsSetRequest` | N/A | ? | ? | N/A | ? |

---

### 4.4. Update Schema审查

**检查项列表**:
- [ ] Update Schema中的所有字段是否都定义为`Optional[...]`
- [ ] Update Schema是否遗漏了常用更新字段
- [ ] Update Schema是否**正确排除**了不可更新字段（`id`, `created_at`, `updated_at`）

**PATCH语义验证**:
- [ ] 所有Update Schema是否支持部分更新（所有字段可选）
- [ ] 字段验证规则是否与Create Schema一致（如长度限制、范围限制）

**Update Schema检查表**:

| Schema | 所有字段可选 | 不包含 `id` | 不包含 `created_at` | 不包含 `updated_at` | 是否符合要求 |
|--------|------------|------------|-------------------|-------------------|------------|
| `TagUpdate` | ? | ? | ? | ? | ? |
| `CategoryUpdate` | ? | ? | ? | ? | ? |

---

### 4.5. Response Schema审查

#### 4.5.1. 安全审计

**检查项列表**:
- [ ] Response Schema是否暴露了敏感字段（如`user_id`、`password`等）
- [ ] 是否有其他敏感字段不应暴露但出现在响应中

**安全清单表格**:

| 字段 | 是否暴露 | 是否合理 | 建议 |
|------|---------|---------|------|
| `Tag.id` | ? | ? | UUID主键，可以暴露 |
| `Tag.name` | ? | ? | 标签名称，可以暴露 |
| `Tag.slug` | ? | ? | URL友好标识符，可以暴露 |
| `Tag.description` | ? | ? | 标签描述，可以暴露 |
| `Tag.is_active` | ? | ? | 是否启用，可以暴露 |
| `Category.id` | ? | ? | UUID主键，可以暴露 |
| `Category.name` | ? | ? | 分类名称，可以暴露 |
| `Category.sort_order` | ? | ? | 排序权重，可以暴露 |

#### 4.5.2. 结构审计

**检查项列表**:
- [ ] Response Schema是否包含所有必要字段
- [ ] 嵌套Schema是否正确嵌套

**嵌套层级检查**:
- [ ] 嵌套层级是否合理（建议不超过3层）
- [ ] 是否存在潜在的循环依赖

**嵌套结构验证**:

```
TagItem
├── id, name, slug, description, is_active
├── created_at, updated_at
└── (无嵌套)

CategoryItem
├── id, name, slug, icon, description, sort_order, is_active
├── created_at, updated_at
└── (无嵌套)

TagListResponse
├── code, message, timestamp
└── data: List[TagItem]

CategoryListResponse
├── code, message, timestamp
└── data: List[CategoryItem]

CategoryAdminListResponse
├── code, message, timestamp
└── data: PaginatedData[CategoryItem]
    ├── total, page, size
    └── items: List[CategoryItem]

SessionTagsListResponse
├── code, message, timestamp
└── data: List[TagItem]
```

#### 4.5.3. `from_attributes` 配置检查

**检查项列表**:
- [ ] 所有Response Schema是否设置了`model_config = ConfigDict(from_attributes=True)`
- [ ] 嵌套Schema是否也设置了`from_attributes=True`

**配置清单表格**:

| Schema | 是否设置 `from_attributes=True` | 是否合理 |
|--------|-------------------------------|---------|
| `TagItem` | ? | 必须设置 |
| `CategoryItem` | ? | 必须设置 |
| `TagBriefItem` | ? | 必须设置（用于ORM转换） |
| `PaginatedData` | ? | 不需要（不直接映射ORM） |

---

### 4.6. 默认值一致性

**检查项列表**:
- [ ] Model中的默认值是否与Schema中的默认值一致

**默认值对比表**:

| Model 字段 | Model 默认值 | Schema 默认值 | 是否一致 |
|-----------|------------|--------------|---------|
| `Tag.is_active` | `default=True` | `Field(True)` | ? |
| `Category.sort_order` | `default=0` | `Field(0, ge=0)` | ? |
| `Category.is_active` | `default=True` | `Field(True)` | ? |

---

### 4.7. 枚举类型一致性

**检查项列表**:
- [ ] SQLAlchemy模型中的枚举值是否与Pydantic Schema中的枚举值完全一致
- [ ] 枚举值的顺序和命名是否一致

**枚举值对比表**:

| 枚举值 | Model 定义 | Schema 定义 | 是否一致 |
|-------|-----------|------------|---------|
| N/A | 本模块无枚举类型 | N/A | N/A |

**注意**: 本模块不包含枚举类型，此检查项不适用。

---

### 4.8. 字段约束映射

**检查项列表**:
- [ ] Model中`nullable=False`的字段是否在Schema中标记为必填（`...`而非`Optional`）
- [ ] Model中`nullable=True`的字段是否在Schema中标记为可选（`Optional`）
- [ ] Model中的字符串长度限制（`String(n)`）是否在Schema中通过`Field(max_length=n)`体现
- [ ] Model中的唯一性约束是否在业务逻辑或验证器中体现

**约束映射表**:

| Model 字段 | Model 约束 | Schema 验证规则 | 是否正确映射 |
|-----------|-----------|----------------|------------|
| `Tag.name` | `nullable=False, String(80), unique=True` | `Field(..., min_length=1, max_length=80)` | ? |
| `Tag.slug` | `nullable=True, String(100)` | `Field(None, max_length=100)` | ? |
| `Tag.description` | `nullable=True, Text` | `Field(None)` | ? |
| `Tag.is_active` | `nullable=False, Boolean, default=True` | `Field(True)` | ? |
| `Category.name` | `nullable=False, String(100), unique=True` | `Field(..., min_length=1, max_length=100)` | ? |
| `Category.sort_order` | `nullable=False, Integer, default=0` | `Field(0, ge=0)` | ? |

---

### 4.9. 结构冗余或字段歧义

**检查项列表**:
- [ ] 是否存在字段在多个Schema中冗余定义（应使用继承）
- [ ] Base Schema是否被正确继承
- [ ] 是否存在结构重复、命名歧义或字段冲突

**继承结构检查**:

```
TagBase (基础字段: name, slug, description)
    ├── TagCreate (继承 TagBase, 添加 is_active)
    ├── TagItem (继承 TagBase, 添加 id, is_active, created_at, updated_at)
    └── TagUpdate (不继承，所有字段可选)

CategoryBase (基础字段: name, slug, icon, description)
    ├── CategoryCreate (继承 CategoryBase, 添加 sort_order, is_active)
    ├── CategoryItem (继承 CategoryBase, 添加 id, sort_order, is_active, created_at, updated_at)
    └── CategoryUpdate (不继承，所有字段可选)

SessionTagsSetRequest (独立Schema: tag_ids, mode)
TagBriefItem (独立Schema: id, name)
SessionTagsSetResponse (独立Schema: code, message, data, timestamp)
SessionTagsListResponse (独立Schema: code, message, data, timestamp)
```

---

### 4.10. 嵌套结构与复合 Schema 审查

#### 4.10.1. 嵌套Schema合理性

**检查项列表**:
- [ ] 嵌套Schema是否合理
- [ ] 是否使用`default_factory=list`明确初始化避免`null`值
- [ ] 嵌套层级是否超过3层（可能导致性能问题）

**嵌套结构验证**:

```
TagListResponse
├── code, message, timestamp
└── data: List[TagItem] (无嵌套，合理)

CategoryListResponse
├── code, message, timestamp
└── data: List[CategoryItem] (无嵌套，合理)

CategoryAdminListResponse
├── code, message, timestamp
└── data: PaginatedData[CategoryItem]
    ├── total, page, size
    └── items: List[CategoryItem] (嵌套层级2层，合理)

SessionTagsListResponse
├── code, message, timestamp
└── data: List[TagItem] (无嵌套，合理)
```

**检查要点**:
- 每个嵌套列表是否使用`default_factory=list`（如适用）
- 嵌套对象是否都设置了`from_attributes=True`
- 嵌套层级是否清晰且易于理解

#### 4.10.2. 复合对象字段控制

**检查项列表**:
- [ ] 列表字段是否限制了长度（`min_length`和`max_length`）
- [ ] 是否存在无限制的列表字段（可能导致大查询）
- [ ] 是否存在递归列表或嵌套嵌套（可能导致性能问题）

**性能隐患检查**:

| Schema | 列表字段 | 是否限制长度 | 最大长度 | 是否合理 |
|--------|---------|------------|---------|---------|
| `TagListResponse` | `data: List[TagItem]` | ❌ | 无限制 | ⚠️ 建议限制 |
| `CategoryListResponse` | `data: List[CategoryItem]` | ❌ | 无限制 | ⚠️ 建议限制 |
| `SessionTagsSetRequest` | `tag_ids: List[UUID]` | ✅ | `max_length=50` | ✅ 合理 |
| `SessionTagsListResponse` | `data: List[TagItem]` | ❌ | 无限制 | ⚠️ 建议限制 |

**建议**: 为所有列表字段设置合理的`max_length`，对于大量数据，使用分页机制。

---

### 4.11. Schema 继承与通用结构审查

#### 4.11.1. 继承结构审查

**检查项列表**:
- [ ] Create Schema是否继承自Base Schema
- [ ] InDB Schema是否继承自Base Schema
- [ ] Response Schema是否继承自InDB Schema
- [ ] 继承关系是否清晰且符合逻辑

**继承链验证**:

```
Tag 继承链:
TagBase → TagCreate
TagBase → TagItem
TagUpdate (独立，不继承)

Category 继承链:
CategoryBase → CategoryCreate
CategoryBase → CategoryItem
CategoryUpdate (独立，不继承)
```

#### 4.11.2. ORM映射配置审查

**检查项列表**:
- [ ] 所有`*Item` Schema是否设置了`model_config = ConfigDict(from_attributes=True)`
- [ ] 所有`*Response` Schema是否继承了正确的`*Item` Schema（自动获得ORM映射配置）
- [ ] 嵌套Schema是否也设置了`from_attributes=True`

**配置清单表格**:

| Schema | 是否设置 `from_attributes=True` | 是否合理 |
|--------|-------------------------------|---------|
| `TagItem` | ? | 必须设置 |
| `CategoryItem` | ? | 必须设置 |
| `TagBriefItem` | ? | 必须设置（用于ORM转换） |
| `TagListResponse` | ? | 不需要（不直接映射ORM） |
| `CategoryListResponse` | ? | 不需要（不直接映射ORM） |
| `CategoryAdminListResponse` | ? | 不需要（不直接映射ORM） |
| `SessionTagsListResponse` | ? | 不需要（不直接映射ORM） |

#### 4.11.3. 字段注释与文档字符串审查

**检查项列表**:
- [ ] 所有Schema类是否包含中文文档字符串
- [ ] 关键字段是否包含`description`参数
- [ ] 字段注释是否与ORM定义同步（便于自动文档生成）

**文档质量检查**:
- 每个Schema类的文档字符串是否说明了其用途
- 每个字段的`description`是否清晰描述了字段含义
- 复杂字段（如计算字段）是否说明了计算逻辑

---

### 4.12. 特殊功能审查

#### 4.12.1. 自定义验证器审查

**检查项列表**:
- [ ] 是否实现了自定义验证器
- [ ] 验证器是否使用了`@field_validator`装饰器
- [ ] 验证器是否使用了`@classmethod`装饰器
- [ ] 验证器逻辑是否正确
- [ ] 验证器错误信息是否清晰

**验证器实现检查**:

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

**CategoryBase.name 验证器**:
```python
@field_validator('name')
@classmethod
def validate_name(cls, v: str) -> str:
    v = v.strip()
    if re.search(r'[<>\'";]', v):
        raise ValueError('分类名称不能包含特殊字符')
    return v
```

**SessionTagsSetRequest.tag_ids 验证器**:
```python
@field_validator('tag_ids')
@classmethod
def validate_tag_ids_unique(cls, v: List[UUID]) -> List[UUID]:
    """验证标签ID列表唯一性"""
    if len(v) != len(set(v)):
        raise ValueError('标签ID列表中存在重复项')
    return v
```

**问题清单**:
- [ ] 是否正确提取了需要验证的值
- [ ] 是否使用`set()`去重检查（如适用）
- [ ] 是否抛出了合适的异常（`ValueError`）
- [ ] 是否返回了验证后的值

#### 4.12.2. 业务逻辑字段审查

**检查项列表**:
- [ ] 计算字段是否是计算字段
- [ ] 计算逻辑是否在文档中说明
- [ ] 字段来源是否明确

**计算字段验证表**:

| 字段 | 来源 | 计算逻辑 | 是否说明 |
|------|------|---------|---------|
| N/A | 本模块无计算字段 | N/A | N/A |

#### 4.12.3. 特殊约束审查

**检查项列表**:
- [ ] Model中的唯一性约束是否在业务逻辑中体现
- [ ] 是否有相应的错误处理逻辑（如捕获`IntegrityError`）

**唯一性约束检查**:

| Model 字段 | 唯一性约束 | 是否在业务逻辑中体现 | 是否合理 |
|-----------|----------|-------------------|---------|
| `Tag.name` | `unique=True` | ? | 应在业务逻辑中检查 |
| `Category.name` | `unique=True` | ? | 应在业务逻辑中检查 |

---

## 5. 审查重点总结

### 5.1 必须检查的项目（P0 优先级）

1. ✅ 字段名称完全一致
2. ✅ 数据类型正确映射
3. ✅ `Create` Schema 不包含系统生成字段
4. ✅ `Update` Schema 所有字段可选
5. ✅ `Response` Schema 设置了 `from_attributes=True`
6. ✅ 必填字段约束正确映射

### 5.2 重要检查的项目（P1 优先级）

1. ✅ 默认值一致性
2. ✅ 字段长度限制正确映射
3. ✅ 嵌套 Schema 使用 `default_factory=list`（如适用）
4. ✅ 列表字段限制了最大长度
5. ✅ 自定义验证器逻辑正确

### 5.3 建议检查的项目（P2 优先级）

1. ✅ 敏感字段是否应暴露
2. ✅ 嵌套层级是否合理
3. ✅ 字段注释和文档字符串完整
4. ✅ 继承结构清晰
5. ✅ 性能隐患（如无限制列表）

---

## 6. 最终交付 (Final Deliverable)

生成一份简明的审查报告，指出你发现的任何**逻辑不一致**、**安全风险**或**不符合最佳实践**的地方，并提供具体的修改建议。

### 6.1 报告结构

```markdown
# 内容管理模块设计文档-标签-分类-场次标签关联 Model 与 Schema 一致性审查报告

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

## 4. Create Schema审查
- [✅/❌] 检查结果
- 问题清单: ...
- 修改建议: ...

## 5. Update Schema审查
- [✅/❌] 检查结果
- 问题清单: ...
- 修改建议: ...

## 6. Response Schema审查
- [✅/❌] 检查结果
- 问题清单: ...
- 修改建议: ...

## 7. 默认值一致性
- [✅/❌] 检查结果
- 问题清单: ...
- 修改建议: ...

## 8. 字段约束映射
- [✅/❌] 检查结果
- 问题清单: ...
- 修改建议: ...

## 9. 结构冗余或字段歧义
- [✅/❌] 检查结果
- 问题清单: ...
- 修改建议: ...

## 10. 嵌套结构与复合 Schema 审查
- [✅/❌] 检查结果
- 问题清单: ...
- 修改建议: ...

## 11. Schema 继承与通用结构审查
- [✅/❌] 检查结果
- 问题清单: ...
- 修改建议: ...

## 12. 特殊功能审查
- [✅/❌] 检查结果
- 问题清单: ...
- 修改建议: ...

## 13. 总体建议
- 优先修复项: ...
- 可选优化项: ...
- 架构改进建议: ...
```

---

**文档版本**: V1.0  
**创建日期**: 2026-01-18  
**适用于**: 内容管理模块设计文档-标签-分类-场次标签关联 SQLAlchemy 模型与 Pydantic Schema 一致性检查

