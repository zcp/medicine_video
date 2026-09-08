# 专家模块增量开发 - CRUD 层代码生成提示词

**模块名称**: experts  
**功能模块名称**: 专家模块增量（is_active、批量导入、关注列表过滤）  
**目标文件**: `backend/live_core_service/app/crud/experts.py`  
**配套文档**: 与现有《专家模块设计文档-专家信息-专家关注---CRUD层代码生成提示词.md》配套使用；执行时先阅读现有 CRUD 提示词（角色、职责、项目结构、Model 摘要、通用原则），再按本增量提示词仅修改或新增下列内容。

---

## 1. 角色定义

在既有专家 CRUD 提示词基础上，按本增量提示词修改/新增下列函数。角色与职责与现有 CRUD 提示词一致（数据访问层，仅负责数据库操作）。

---

## 2. Model 字段变更摘要

### 2.1 Expert 模型增量（4.1 Expert 模型表格增量行）

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|--------|------|------|--------|------|
| `is_active` | Boolean | NOT NULL | True | 是否启用（false 表示软删除/下架） |

**索引**：可新增 `idx_experts_is_active` (is_active)，用于 Admin 列表按 is_active 筛选。

---

## 3. 需要修改的 CRUD 函数清单

### 3.1 函数: `create_expert`

**函数签名**：（与现有一致，ExpertCreate 已含 is_active）

```python
async def create_expert(
    db: AsyncSession,
    expert_data: ExpertCreate
) -> Expert
```

**功能**: 创建专家（变更：写入 Schema 中的 is_active，默认 True）

**执行流程（仅写变更步骤）**:
- 创建 Expert 实例时，`expert_data.model_dump()` 已包含 is_active；若 ExpertCreate 中 is_active 默认 True，则无需在 CRUD 层额外赋值。
- 若 model_dump() 未包含 is_active，则需在构造 Expert 时显式传入 `is_active=getattr(expert_data, 'is_active', True)`。

**异常/日志**: 无变更。

---

### 3.2 函数: `get_featured_experts`

**函数签名**：（与现有一致）

```python
async def get_featured_experts(
    db: AsyncSession,
    limit: int = 10
) -> List[Expert]
```

**功能**: 获取首页推荐专家列表（变更：查询条件增加 Expert.is_active == True）

**执行流程（仅写变更步骤）**:
1. WHERE 条件由 `Expert.is_featured == True` 改为 `Expert.is_featured == True, Expert.is_active == True`（即增加 `Expert.is_active == True`）。

**异常/日志**: 无变更。

---

### 3.3 函数: `get_experts_multi_and_total`

**函数签名**：（增加参数 is_active）

```python
async def get_experts_multi_and_total(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 10,
    name: Optional[str] = None,
    is_featured: Optional[bool] = None,
    is_active: Optional[bool] = None,
    hospital: Optional[str] = None,
    sort: Optional[str] = None
) -> Tuple[List[Expert], int]
```

**功能**: 分页获取专家列表（变更：增加可选参数 is_active，并在 conditions 中按需添加 Expert.is_active == is_active）

**执行流程（仅写变更步骤）**:
2. 应用筛选条件：若 `is_active is not None`，添加 `conditions.append(Expert.is_active == is_active)`。

**异常/日志**: 无变更。

---

### 3.4 函数: `update_expert`

**函数签名**：（与现有一致，ExpertUpdate 已含 is_active）

```python
async def update_expert(
    db: AsyncSession,
    expert_id: uuid.UUID,
    expert_data: ExpertUpdate
) -> Optional[Expert]
```

**功能**: 更新专家（变更：允许更新 is_active，ExpertUpdate 已含该字段）

**执行流程（仅写变更步骤）**:
- 部分更新时 `expert_data.model_dump(exclude_unset=True)` 已包含 is_active，无需额外处理。

**异常/日志**: 无变更。

---

### 3.5 函数: `delete_expert`

**函数签名**：（与现有一致）

```python
async def delete_expert(
    db: AsyncSession,
    expert_id: uuid.UUID
) -> bool
```

**功能**: 删除专家（变更：软删除改为设置 expert.is_active = False，不再修改 is_featured）

**执行流程（仅写变更步骤）**:
6. 软删除：由 `expert.is_featured = False` 改为 `expert.is_active = False`。
7. 记录日志：docstring 与日志文案改为「软删除为 is_active=false」。

**异常/日志**: 无变更。

---

## 4. 需要约定的 CRUD 函数（无代码变更但需在提示词中写明）

- **get_expert**：不按 is_active 过滤；根据 expert_id 查询，返回任意 is_active 状态的专家（由 Service 层 _check_expert_visibility 判断可见性）。
- **get_expert_by_user_id**：不按 is_active 过滤；已下架专家仍占用 user_id，由业务层保证唯一性。
- **get_user_subscriptions**：若采用「CRUD 层过滤关注列表中的已下架专家」，则在此写出签名变更（如增加 `include_inactive: bool = False`）及 WHERE/JOIN 条件（如 JOIN experts 且 Expert.is_active == True）；否则注明「由 Service 层过滤」。
- **批量导入**：不新增 CRUD 函数；去重时调用现有 `get_experts_multi_and_total(db, skip=0, limit=1, name=..., hospital=...)` 判断是否存在；若需按 (name, hospital, department) 去重，可传对应参数。

---

## 5. 质量标准

与现有 CRUD 提示词在「异步、类型提示、事务与 IntegrityError、日志脱敏、安全异步异常处理」等方面要求一致。不改变未被列出的 CRUD 函数的签名与行为。与既有 CRUD 提示词在命名、结构、格式上保持完全一致，无冲突。

---

**文档结束。**
