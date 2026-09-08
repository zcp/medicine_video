# 专家模块设计文档-专家信息-专家关注 SQLAlchemy 模型与 Pydantic Schema 一致性检查提示词

**版本**: V1.0  
**创建日期**: 2026-01-18  
**适用于**: 专家模块设计文档-专家信息-专家关注 SQLAlchemy 模型与 Pydantic Schema 一致性检查  
**基于文档**: @docs/03_系统设计/直播核心功能设计文档_v6_专家模块设计文档-专家信息-专家关注.md

---

## 1. 角色定义 (Role Definition)

你是一名资深的 FastAPI 后端架构师，专注于 API 设计和数据模型的最佳实践。你的任务是审查专家模块设计文档-专家信息-专家关注的 SQLAlchemy 模型（`experts.py`）和 Pydantic Schema（`schemas/experts.py`）之间的一致性、安全性和功能适配性。

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

**文件路径**: `backend/live_core_service/app/models/experts.py`

**【请在此处粘贴完整的 `app/models/experts.py` 代码】**

(代码将在执行时自动读取)

### 3.2. Pydantic Schema 代码

**文件路径**: `backend/live_core_service/app/schemas/experts.py`

**【请在此处粘贴完整的 `app/schemas/experts.py` 代码】**

(代码将在执行时自动读取)

---

## 4. 审查清单 (Audit Checklist)

### 4.1. 字段命名一致性

**检查项列表**:
- [ ] 检查每个模型的字段名称是否与对应Schema中的字段名称完全一致
- [ ] 检查是否存在拼写差异或语义偏移（如 `banner_url` vs `bannerURL`）

**重点字段检查对比表**:

| Model 字段 | Schema 字段 | 是否一致 |
|-----------|-----------|---------|
| `Expert.user_id` | `ExpertItem.user_id` | ? |
| `Expert.name` | `ExpertBase.name` | ? |
| `Expert.title` | `ExpertBase.title` | ? |
| `Expert.hospital` | `ExpertBase.hospital` | ? |
| `Expert.department` | `ExpertBase.department` | ? |
| `Expert.expertise_areas` | `ExpertBase.expertise_areas` | ? |
| `Expert.bio` | `ExpertBase.bio` | ? |
| `Expert.avatar_url` | `ExpertBase.avatar_url` | ? |
| `Expert.is_featured` | `ExpertItem.is_featured` | ? |
| `Expert.sort_order` | `ExpertItem.sort_order` | ? |
| `Expert.contact_info` | `ExpertCreate.contact_info` | ? |
| `Expert.created_at` | `ExpertItem.created_at` | ? |
| `Expert.updated_at` | `ExpertItem.updated_at` | ? |

**检查方法**: 逐字段对比Model和Schema中的字段名称，确保完全一致。

---

### 4.2. 数据类型兼容性

**检查项列表**:
- [ ] UUID类型字段是否在Schema中映射为`uuid.UUID`
- [ ] String(n)类型字段是否在Schema中映射为`str`，并使用`Field(max_length=n)`限制
- [ ] Text类型字段是否在Schema中映射为`str`（不限长度）
- [ ] Integer类型字段是否在Schema中映射为`int`
- [ ] TIMESTAMP(timezone=True)类型字段是否在Schema中映射为`datetime`
- [ ] Enum类型字段是否在Schema中使用对应的Pydantic `Enum`
- [ ] JSONB类型字段是否在Schema中映射为`dict`

**类型映射表**:

| SQLAlchemy 类型 | Pydantic 类型 | 验证规则 | 是否正确映射 |
|----------------|--------------|---------|------------|
| `UUID(as_uuid=True)` | `uuid.UUID` | - | ? |
| `String(120)` | `str` | `Field(max_length=120)` | ? |
| `String(200)` | `str` | `Field(max_length=200)` | ? |
| `String(512)` | `str` | `Field(max_length=512)` | ? |
| `String(50)` | `str` | `Field(max_length=50)` | ? |
| `Text` | `str` | 无长度限制 | ? |
| `Integer` | `int` | - | ? |
| `Boolean` | `bool` | - | ? |
| `TIMESTAMP(timezone=True)` | `datetime` | - | ? |
| `JSONB` | `dict` | - | ? |
| `SessionExpertRole` (Enum) | `SessionExpertRole` (Pydantic Enum) | 枚举值验证 | ? |

---

### 4.3. Create Schema审查

**检查项列表**:
- [ ] Create Schema是否包含创建所需的所有必填字段
- [ ] Create Schema是否**正确排除**了系统生成字段（`id`, `created_at`, `updated_at`）
- [ ] Create Schema是否**正确排除**了外键字段（从路径参数获取）

**关键问题说明**:

1. **Create Schema中是否错误地包含了`id`字段？**
   - ❌ 错误：`id`应由数据库或应用层生成
   - ✅ 正确：Create Schema不包含`id`

2. **Create Schema中是否错误地包含了外键字段？**
   - ❌ 错误：外键应从路径参数获取
   - ✅ 正确：Create Schema不包含外键字段

---

### 4.4. Update Schema审查

**检查项列表**:
- [ ] Update Schema中的所有字段是否都定义为`Optional[...]`
- [ ] Update Schema是否遗漏了常用更新字段
- [ ] Update Schema是否**正确排除**了不可更新字段（`id`, `user_id`, `created_at`, `updated_at`）

**PATCH语义验证**:
- [ ] 所有Update Schema是否支持部分更新（所有字段可选）
- [ ] 字段验证规则是否与Create Schema一致（如长度限制、范围限制）

---

### 4.5. Response Schema审查

**安全审计**:
- [ ] Response Schema是否暴露了敏感字段（如`contact_info`的敏感内容）
- [ ] 是否有其他敏感字段不应暴露但出现在响应中

**安全清单表格**:

| 字段 | 是否暴露 | 是否合理 | 建议 |
|------|---------|---------|------|
| `Expert.contact_info` | ✅/❌ | ? | 说明是否应该完整暴露 |
| `Expert.user_id` | ✅/❌ | ? | 说明是否应该暴露 |

**结构审计**:
- [ ] Response Schema是否包含所有必要字段
- [ ] 嵌套Schema是否正确嵌套

**`from_attributes` 配置检查**:
- [ ] 所有Response Schema是否设置了`model_config = ConfigDict(from_attributes=True)`
- [ ] 嵌套Schema是否也设置了`from_attributes=True`

---

### 4.6. 默认值一致性

**检查项列表**:
- [ ] Model中的默认值是否与Schema中的默认值一致

**默认值对比表**:

| Model 字段 | Model 默认值 | Schema 默认值 | 是否一致 |
|-----------|------------|--------------|---------|
| `Expert.is_featured` | `False` | `False` | ? |
| `Expert.sort_order` | `0` | `0` | ? |
| `LiveSessionExpert.role` | `SessionExpertRole.MAIN_SPEAKER` | `"主讲"` | ? |
| `LiveSessionExpert.sort_order` | `0` | `0` | ? |

---

### 4.7. 枚举类型一致性

**检查项列表**:
- [ ] SQLAlchemy模型中的枚举值是否与Pydantic Schema中的枚举值完全一致
- [ ] 枚举值的顺序和命名是否一致

**枚举值对比表**:

| 枚举值 | Model 定义 | Schema 定义 | 是否一致 |
|-------|-----------|------------|---------|
| `MAIN_SPEAKER` | `"主讲"` | `"主讲"` | ? |
| `HOST` | `"主持"` | `"主持"` | ? |
| `GUEST` | `"嘉宾"` | `"嘉宾"` | ? |

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
| `Expert.name` | `nullable=False, String(120)` | `Field(..., min_length=1, max_length=120)` | ? |
| `Expert.title` | `String(120)` | `Field(None, max_length=120)` | ? |
| `Expert.hospital` | `String(200)` | `Field(None, max_length=200)` | ? |
| `Expert.department` | `String(120)` | `Field(None, max_length=120)` | ? |
| `Expert.bio` | `Text` | `Field(None, max_length=1000)` | ? |
| `Expert.sort_order` | `Integer, default=0` | `Field(0, ge=0)` | ? |

---

### 4.9. 结构冗余或字段歧义

**检查项列表**:
- [ ] 是否存在字段在多个Schema中冗余定义（应使用继承）
- [ ] Base Schema是否被正确继承
- [ ] 是否存在结构重复、命名歧义或字段冲突

**继承结构检查**:

```
ExpertBase (基础字段)
    ├── ExpertCreate (继承 ExpertBase)
    ├── ExpertUpdate (继承 BaseModel)
    └── ExpertItem (继承 ExpertBase)

SessionExpertRole (枚举)
    └── SessionExpertItem (基础字段)
```

---

### 4.10. 嵌套结构与复合 Schema 审查

**嵌套Schema合理性**:
- [ ] 嵌套Schema是否合理
- [ ] 嵌套层级是否超过3层（可能导致性能问题）

**嵌套结构验证**:

```
FollowedExpertItem
    ├── expert_id, name, title, hospital, avatar_url
    ├── subscribed_at
    └── live_status: dict (可选)

SessionExpertItem
    ├── id, name, title, hospital, avatar_url
    └── role, sort_order (可选)
```

---

### 4.11. Schema 继承与通用结构审查

**继承结构审查**:
- [ ] Create Schema是否继承自Base Schema
- [ ] Response Schema是否继承自Base Schema
- [ ] 继承关系是否清晰且符合逻辑

**继承链验证**:

```
Expert 继承链:
ExpertBase → ExpertCreate
ExpertBase → ExpertUpdate (BaseModel)
ExpertBase → ExpertItem
ExpertItem → FeaturedExpertItem (简化字段)
```

**ORM映射配置审查**:
- [ ] 所有`*Response` Schema是否设置了`model_config = ConfigDict(from_attributes=True)`
- [ ] 嵌套Schema是否也设置了`from_attributes=True`

**配置清单表格**:

| Schema | 是否设置 `from_attributes=True` | 是否合理 |
|--------|-------------------------------|---------|
| `ExpertItem` | ? | 必须设置 |
| `FeaturedExpertItem` | ? | 必须设置 |
| `FollowedExpertItem` | ? | 必须设置 |
| `SessionExpertItem` | ? | 必须设置 |

**字段注释与文档字符串审查**:
- [ ] 所有Schema类是否包含中文文档字符串
- [ ] 关键字段是否包含`description`参数
- [ ] 字段注释是否与ORM定义同步

---

### 4.12. 特殊功能审查

**业务逻辑字段审查**:
- [ ] 计算字段是否是计算字段
- [ ] 计算逻辑是否在文档中说明
- [ ] 字段来源是否明确

**特殊约束审查**:
- [ ] Model中的唯一性约束是否在业务逻辑中体现
- [ ] 是否有相应的错误处理逻辑（如捕获`IntegrityError`）

---

## 5. 审查重点总结

### 5.1 必须检查的项目（P0 优先级）

1. ✅ 字段名称完全一致
2. ✅ 数据类型正确映射
3. ✅ `Create` Schema 不包含系统生成字段
4. ✅ `Update` Schema 所有字段可选
5. ✅ `Response` Schema 设置了 `from_attributes=True`
6. ✅ 枚举值完全一致
7. ✅ 必填字段约束正确映射

### 5.2 重要检查的项目（P1 优先级）

1. ✅ 默认值一致性
2. ✅ 字段长度限制正确映射
3. ✅ 敏感字段是否应暴露
4. ✅ 继承结构清晰
5. ✅ `from_attributes=True` 配置正确

### 5.3 建议检查的项目（P2 优先级）

1. ✅ 嵌套层级是否合理
2. ✅ 字段注释和文档字符串完整
3. ✅ 特殊字段（如`contact_info`）的敏感信息处理

---

## 6. 最终交付 (Final Deliverable)

生成一份简明的审查报告，指出你发现的任何**逻辑不一致**、**安全风险**或**不符合最佳实践**的地方，并提供具体的修改建议。

### 6.1. 报告结构

```markdown
# 专家模块 Model 与 Schema 一致性审查报告

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

[... 其他审查项 ...]

## 7. 总体建议
- 优先修复项: ...
- 可选优化项: ...
- 架构改进建议: ...
```

---

**文档版本**: V1.0  
**创建日期**: 2026-01-18  
**适用于**: 专家模块设计文档-专家信息-专家关注

