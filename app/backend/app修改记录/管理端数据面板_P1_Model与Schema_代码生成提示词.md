# 管理端数据面板 P1 — Model + Schema 代码生成提示词

**版本**: V1.0
**创建日期**: 2026-07-23
**基于设计文档**: `app修改记录/管理端后台数据面板_AdminStats设计文档.md`
**目标文件**: 修改 2 个 + 新建 1 个

---

## 1. 角色定义 (Role Definition)

你是一名精通 SQLAlchemy 2.0 + PostgreSQL + Pydantic v2 的数据库建模专家。你的任务是执行**管理端数据面板 P1**：为 Expert 模型新增 `is_verified` 审核字段，并新建管理端统一 Schema 文件。

**四个必须**：
- 必须提供完整、可运行的模型和 Schema 代码
- 必须保持与现有代码风格完全一致（字段定义、comment、import 顺序）
- Expert 模型只新增字段，不改动已有字段和关系
- 新增的 Schema 类必须使用 `from_attributes=True`

---

## 2. 任务目标 (Task Objective)

### 2.1 修改文件（2 个）

| 文件 | 修改内容 | 程度 |
|:-----|:---------|:----:|
| `app/models/experts.py` | `Expert` 类新增 `is_verified` 列 | +3 行（含 comment） |
| `app/schemas/experts.py` | `ExpertCreate` / `ExpertUpdate` / `ExpertItem` 新增 `is_verified` | +3 行 |

### 2.2 新建文件（1 个）

| 文件 | 内容 |
|:-----|:-----|
| `app/schemas/admin.py` | `AdminDailyStats` / `TodaySessionItem` / `TodaySessionListResponse` |

### 2.3 禁止事项

- ❌ 不修改 `app/api/` 下的任何文件
- ❌ 不修改 `app/crud/` 下的任何文件
- ❌ 不修改 `app/services/` 下的任何文件
- ❌ 不修改 `app/models/__init__.py`（`Expert` 已在其中，无需新增导入）
- ❌ 不创建 SQL 迁移文件（由 P3 阶段处理）
- ❌ 不修改 `app/models/experts.py` 中的 `UserExpertSubscription` 和 `LiveSessionExpert`

---

## 3. 核心上下文 (Core Context)

### 3.1 `app/models/experts.py` — Expert 模型

**当前 Expert 类（约第 24-100 行）**，已有字段：
- `id`, `user_id`, `name`, `title`, `hospital`, `expertise_areas`, `department_id`, `bio`, `avatar_url`, `category_id`, `is_featured`, `is_active`, `sort_order`, `contact_info`, `created_at`, `updated_at`
- 关系：`department`, `live_session_experts`

**新增字段位置**：在 `is_active`（约第 72 行）之后、`sort_order` 之前插入：

```python
is_verified = Column(
    Boolean, nullable=False, default=False,
    comment='审核状态: False=待审批, True=已审批'
)
```

`is_verified` 与 `is_active` 是正交语义。`is_active=False` 表示软删除，`is_verified=False` 表示待审批。一个已删除的专家不应计入待审批计数（CRUD 层需组合 `is_active=True` + `is_verified=False`）。

### 3.2 `app/schemas/experts.py` — Expert Schema

**当前 Schema 结构**：

| Schema | 位置（估算行） | 修改方式 |
|--------|:-------------:|---------|
| `ExpertBase` | ~L15 | 不动（继承于它的 Create/Update 各自声明） |
| `ExpertCreate` | ~L50 | `is_verified: bool = Field(False, description="...")` 追加在最后 |
| `ExpertUpdate` | ~L70 | `is_verified: Optional[bool] = Field(None, description="...")` 追加 |
| `ExpertItem` | ~L100 | `is_verified: bool` 追加，`from_attributes=True` 已存在 |

所有新增字段为**可选**或携带默认值，不破坏现有 API 调用方。

### 3.3 新建 `app/schemas/admin.py`

完整 Schema 定义请参考设计文档 §2.4：

| Schema | 字段 |
|--------|------|
| `AdminDailyStats` | `today_sessions: int`, `live_now: int`, `today_new_rooms: int`, `pending_departments: int`, `pending_experts: int`, `unmapped_experts: int` |
| `TodaySessionItem` | `id: UUID`, `room_id: UUID`, `status: str`, `start_time: Optional[datetime]`, `room_title: str`, `cover_url: Optional[str]`, `expert_name: Optional[str]` |
| `TodaySessionListResponse` | `items: List[TodaySessionItem]`, `total: int`, `page: int`, `size: int` |

`TodaySessionItem` 使用 `from_attributes=True`，无需声明 `model_config`（它是手动构造的 dict，非 ORM 映射）。

---

## 4. 输出要求

### 4.1 输出格式

按文件分组输出，每个文件用代码块包裹并标注文件路径：

````
### 文件: `app/models/experts.py`

```python
# 完整文件内容（或只标注改动的 diff，如果改动范围极小）
...
```
````

### 4.2 必须包含

- 完整的 import 语句（新增文件）
- 每个字段的 `comment` 参数（已有风格）
- `model_config = ConfigDict(from_attributes=True)`（已有 Schema 风格）
- `datetime` 和 `UUID` 的类型导入（需检查已有 import）

### 4.3 验证清单

- [ ] Expert 模型新增列后 SQLAlchemy 语法正确
- [ ] `ExpertCreate.is_verified` 有默认值 `False`
- [ ] `ExpertUpdate.is_verified` 为 `Optional[bool]`
- [ ] `ExpertItem.is_verified` 为 `bool`
- [ ] `app/schemas/admin.py` 中所有类型注解正确
- [ ] `AdminDailyStats` 包含 6 个 `int` 字段
- [ ] `TodaySessionItem` 不包含 `title` 字段（LiveSession 无此列）
