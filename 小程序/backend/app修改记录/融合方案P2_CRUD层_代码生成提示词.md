# 融合方案 P2 — CRUD 层代码生成提示词

**版本**: V1.0  
**创建日期**: 2026-06-23  
**基于设计文档**: `app修改记录/融合方案最终设计_A2+C.md`、`app修改记录/融合方案_提示词编写规范借鉴.md`  
**依赖**: P1 已完成（Model + Schema）  
**目标文件**: 新建 1 个 + 修改 1 个

---

## 1. 角色定义 (Role Definition)

你是一名精通 SQLAlchemy 2.0 异步查询 + PostgreSQL 的 Python 后端工程师。你熟悉本项目 CRUD 层的编码规范——安全异步异常处理（提前提取变量）、`try/except IntegrityError` 事务模式、分页查询的 `count + offset/limit` 两次查询模式。你的任务是执行**融合方案 P2**：在 P1 已完成 Model + Schema 的基础上，生成 ExpertDepartment 的 CRUD 操作，并修改 Expert 的已有 CRUD 以适配新的 `department_id` FK 和 keyword 搜索。

**四个必须**：
- 必须遵循已有 `crud/experts.py` 和 `crud/content_management.py` 的代码风格
- 必须使用 `try/except IntegrityError` + `db.flush()` + `db.refresh()` 模式
- 必须对分页查询使用 `func.count() + select().offset().limit()` 两次查询
- 必须提前将 ORM 对象的属性提取到局部变量（安全异步异常处理）

---

## 2. 任务目标 (Task Objective)

### 2.1 新建文件（1 个）

| 文件 | 内容 | 函数清单 |
|:-----|:-----|:-----|
| `app/crud/expert_departments.py` | ExpertDepartment CRUD | `get_departments_paginated`、`get_department_by_id`、`get_department_by_name`、`create_department`、`update_department`、`soft_delete_department`、`get_unmapped_experts` |

### 2.2 修改已有文件（1 个）

| 文件 | 修改内容 | 函数 |
|:-----|:---------|:-----|
| `app/crud/experts.py` | ① keyword 搜索中 `Expert.department.ilike(kw)` → 子查询 `expert_departments.name` ② 新增 `create_expert_raw` ③ `get_experts_public_list` 的 `department` 参数改为通过子查询匹配 ④ 导入从 `models/experts.py` 扩展为含 `ExpertDepartment` | `create_expert_raw`(新)、`get_experts_public_list`(改) |

### 2.3 禁止事项

- ❌ 不修改 `app/api/` 下的任何文件
- ❌ 不修改 `app/services/` 下的任何文件
- ❌ 不修改 `app/crud/experts.py` 中 `create_expert`、`get_expert`、`update_expert`、`delete_expert` 的函数签名（只修改内部 keyword 搜索逻辑）
- ❌ 不修改 `app/crud/content_management.py`
- ❌ 不新增 `db.commit()` 调用（commit 由 Service 层或调用方执行）

---

## 3. 核心上下文 (Core Context)

### 3.1 技术栈

```
Python 3.9+ | SQLAlchemy 2.0 (async) | PostgreSQL 15
CRUD 层模式: try/except IntegrityError + db.flush() + db.refresh()
分页模式:    select(func.count()) → scalar() → total + select().offset().limit() → scalars()
```

### 3.2 已有代码参考

#### 参考 A：`app/crud/experts.py` — 已有 Expert CRUD 模式（当前第 1-250 行）

**关键观察点（8 个）**：

1. **导入模式**: `from sqlalchemy import select, delete, and_, or_, func, update as sa_update`
2. **UUID 生成**: `uuid.uuid4()` 在函数内生成（不在数据库自动生成）
3. **事务处理**: `try: db.add(expert) → db.flush() → db.refresh(expert) | except IntegrityError: db.rollback()`
4. **提前提取变量**: 在 try 块之前提取 `expert_id_for_logging = str(expert_id)[:8]`
5. **分页查询**: `select(func.count()).select_from(query.subquery())` → `total` + `query.offset(offset).limit(size)` → `list()`
6. **keyword 搜索**: `Expert.name.ilike(kw), Expert.hospital.ilike(kw), Expert.department.ilike(kw)`
7. **条件构建**: `conditions = []` → `conditions.append(...)` → `if conditions: query = query.where(and_(*conditions))`
8. **返回值**: `Tuple[List[Expert], int]`（列表 + 总数）

#### 参考 B：`app/crud/content_management.py` — 已有 Category CRUD 模式

**额外关键观察点**：

- `create_category` (第 325-352 行)：`Category(**category_data.model_dump())` → `db.add()` → `db.flush()` → `db.refresh()`
- `get_categories_paginated` (第 252-322 行)：标准的 `conditions` → `count` → `offset/limit` 模式
- `set_live_room_categories` (第 700-760 行)：多写操作的原子处理

#### 参考 C：P1 已生成的 Model + Schema

```
app/models/expert_departments.py:
  ExpertDepartment 模型:
    id (UUID PK), name (String 120 UNIQUE), category_id (FK→categories RESTRICT),
    synonyms (JSONB, default=list), is_active (Boolean), is_verified (Boolean),
    created_at (TIMESTAMP), updated_at (TIMESTAMP)

app/schemas/expert_departments.py:
  ExpertDepartmentCreate (name, category_id, synonyms, is_verified)
  ExpertDepartmentUpdate (全部 Optional)
  ExpertDepartmentItem (含 category_name, expert_count)
```

---

## 4. 架构约束 (Architecture Constraints)

### 4.1 CRUD 层事务铁律

```
CRUD 层的"写"操作:
  ✅ try: db.add() / db.execute(update()) → db.flush() → db.refresh()
  ✅ except IntegrityError: db.rollback() → raise DatabaseIntegrityException
  ❌ 不在 CRUD 层调用 db.commit()（由 Service 层或 API 层 commit）
  ❌ 不捕获裸 Exception（让未预期的异常向上传播）
```

### 4.2 SQLAlchemy 2.0 async 查询模式

```python
# ✅ 正确：使用 select() + execute() + scalars()
stmt = select(ExpertDepartment).where(ExpertDepartment.is_active == True)
result = await db.execute(stmt)
departments = result.scalars().all()

# ✅ 正确：使用子查询
subquery = select(ExpertDepartment.id).where(ExpertDepartment.name.ilike(kw))
conditions.append(Expert.department_id.in_(subquery))

# ❌ 错误：使用 db.query() 语法（SQLAlchemy 1.x 遗留风格）
```

### 4.3 keyword 搜索的 Jaccard 转移规则

原 `get_experts_public_list` 中 keyword 搜索用 `Expert.department.ilike(kw)`——直接对 VARCHAR 列做模糊匹配。由于 P1 已使 `experts.department` 列为 `null`（等待 P4 删除），keyword 中的科室搜索应改为对 `expert_departments.name` 做子查询：

```python
# 修改前
or_(
    Expert.name.ilike(kw),
    Expert.hospital.ilike(kw),
    Expert.department.ilike(kw),        # ← 删除此行
    Expert.expertise_areas.ilike(kw),
    Expert.bio.ilike(kw),
)

# 修改后
or_(
    Expert.name.ilike(kw),
    Expert.hospital.ilike(kw),
    Expert.department_id.in_(              # ← 新增：子查询 expert_departments
        select(ExpertDepartment.id).where(
            ExpertDepartment.name.ilike(kw)
        )
    ),
    Expert.expertise_areas.ilike(kw),
    Expert.bio.ilike(kw),
)
```

### 4.4 get_experts_public_list 的 category_id 筛选

当前（第 218-220 行）：

```python
if category_id is not None:
    conditions.append(Expert.category_id == category_id)
```

P2 保持此逻辑**不改**（搜索展开 `ANY` 是 P4 迁移后的增强，P2 不涉及）。

---

## 5. 代码生成要求 (Specific Code Generation Requirements)

### 5.1 新文件：`app/crud/expert_departments.py`

**文件头部**：

```python
"""
专家科室受控词表 CRUD 层

封装 ExpertDepartment 模型的所有数据库操作。
提供纯粹的数据访问接口，不包含业务逻辑验证。

所有函数遵循以下规范：
- 使用 async/await 异步编程
- UUID 在应用层生成
- 遵循安全异步异常处理原则（提前提取变量）
- 记录适当的日志
"""

# 标准库导入
import uuid
import logging
from typing import List, Optional, Tuple

# 第三方库导入
from sqlalchemy import select, delete, and_, or_, func, update as sa_update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

# 项目内导入
from app.models.expert_departments import ExpertDepartment
from app.models.experts import Expert
from app.schemas.expert_departments import ExpertDepartmentCreate, ExpertDepartmentUpdate
from app.exceptions import DatabaseIntegrityException, DatabaseOperationException, InvalidParameterException

logger = logging.getLogger(__name__)
```

**函数 1：`get_departments_paginated`** — 分页列表（管理员）

```python
async def get_departments_paginated(
    db: AsyncSession,
    page: int = 1,
    size: int = 50,
    is_active: Optional[bool] = None,
    is_verified: Optional[bool] = None,
    category_id: Optional[uuid.UUID] = None,
    q: Optional[str] = None,
) -> Tuple[List[ExpertDepartment], int]:
    """
    获取科室列表（管理员接口，分页，支持筛选）。

    Args:
        db: 数据库会话
        page: 页码
        size: 每页数量（最大 200）
        is_active: 启用状态筛选（可选）
        is_verified: 审核状态筛选（可选）
        category_id: 分类筛选（可选）
        q: 搜索关键词（name ILIKE %q%，可选）

    Returns:
        (科室列表, 总条数)
    """
    if page < 1:
        page = 1
    if size < 1:
        size = 50
    elif size > 200:
        size = 200

    query = select(ExpertDepartment).order_by(ExpertDepartment.created_at.desc())
    conditions = []

    if is_active is not None:
        conditions.append(ExpertDepartment.is_active == is_active)
    if is_verified is not None:
        conditions.append(ExpertDepartment.is_verified == is_verified)
    if category_id:
        conditions.append(ExpertDepartment.category_id == category_id)
    if q and q.strip():
        conditions.append(ExpertDepartment.name.ilike(f"%{q.strip()}%"))

    if conditions:
        query = query.where(and_(*conditions))

    # count
    count_query = select(func.count()).select_from(query.subquery())
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    # pagination
    offset = (page - 1) * size
    query = query.offset(offset).limit(size)
    result = await db.execute(query)
    departments = result.scalars().all()

    logger.info(f"查询科室列表: page={page}, size={size}, total={total}")
    return (list(departments), total)
```

**函数 2：`get_department_by_id`** — 单条查询

```python
async def get_department_by_id(
    db: AsyncSession,
    department_id: uuid.UUID,
) -> Optional[ExpertDepartment]:
    """根据 ID 获取单个科室"""
    dept_id_log = str(department_id)[:8]
    try:
        stmt = select(ExpertDepartment).where(ExpertDepartment.id == department_id)
        result = await db.execute(stmt)
        dept = result.scalar_one_or_none()
        if dept:
            logger.debug(f"查询科室成功: id={dept_id_log}, name={dept.name}")
        return dept
    except Exception as e:
        logger.error(f"查询科室失败: id={dept_id_log}, error={str(e)}")
        raise
```

**函数 3：`get_department_by_name`** — 按名称查

```python
async def get_department_by_name(
    db: AsyncSession,
    name: str,
) -> Optional[ExpertDepartment]:
    """根据名称获取科室（区分大小写取决于数据库 collation）"""
    try:
        stmt = select(ExpertDepartment).where(
            ExpertDepartment.name == name.strip(),
            ExpertDepartment.is_active == True,
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    except Exception as e:
        logger.error(f"按名称查询科室失败: name={name}, error={str(e)}")
        raise
```

**函数 4：`create_department`** — 创建科室

```python
async def create_department(
    db: AsyncSession,
    department_data: ExpertDepartmentCreate,
) -> ExpertDepartment:
    """
    创建科室（管理员）。

    Raises:
        DatabaseIntegrityException: 科室名重复
    """
    dept_id = uuid.uuid4()
    dept_id_log = str(dept_id)[:8]

    dump_data = department_data.model_dump()
    if "is_active" not in dump_data:
        dump_data["is_active"] = True
    if "is_verified" not in dump_data:
        dump_data["is_verified"] = False

    department = ExpertDepartment(id=dept_id, **dump_data)

    try:
        db.add(department)
        await db.flush()
        await db.refresh(department)
        logger.info(f"创建科室成功: id={dept_id_log}, name={department.name}")
        return department
    except IntegrityError as e:
        await db.rollback()
        logger.error(f"创建科室失败（名称重复）: name={department_data.name}")
        raise DatabaseIntegrityException(f"科室名称已存在: {department_data.name}")
    except Exception as e:
        await db.rollback()
        logger.error(f"创建科室失败: id={dept_id_log}, error={str(e)}")
        raise
```

**函数 5：`update_department`** — 更新科室

```python
async def update_department(
    db: AsyncSession,
    department_id: uuid.UUID,
    department_data: ExpertDepartmentUpdate,
) -> ExpertDepartment:
    """
    更新科室（管理员，部分更新）。

    Args:
        db: 数据库会话
        department_id: 科室 ID
        department_data: 更新数据（全部字段 Optional）

    Returns:
        更新后的科室对象
    """
    dept_id_log = str(department_id)[:8]

    # 查询已有科室
    stmt = select(ExpertDepartment).where(ExpertDepartment.id == department_id)
    result = await db.execute(stmt)
    dept = result.scalar_one_or_none()
    if not dept:
        raise InvalidParameterException("科室不存在")

    # 部分更新（只更新非 None 字段）
    update_dict = department_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(dept, key, value)

    try:
        await db.flush()
        await db.refresh(dept)
        logger.info(f"更新科室成功: id={dept_id_log}")
        return dept
    except IntegrityError as e:
        await db.rollback()
        logger.error(f"更新科室失败（名称冲突）: id={dept_id_log}")
        raise DatabaseIntegrityException("科室名称已存在")
    except Exception as e:
        await db.rollback()
        logger.error(f"更新科室失败: id={dept_id_log}, error={str(e)}")
        raise
```

**函数 6：`soft_delete_department`** — 软删除

```python
async def soft_delete_department(
    db: AsyncSession,
    department_id: uuid.UUID,
) -> ExpertDepartment:
    """软删除科室（is_active = False）"""
    dept_id_log = str(department_id)[:8]

    stmt = select(ExpertDepartment).where(ExpertDepartment.id == department_id)
    result = await db.execute(stmt)
    dept = result.scalar_one_or_none()
    if not dept:
        raise InvalidParameterException("科室不存在")

    dept.is_active = False

    try:
        await db.flush()
        await db.refresh(dept)
        logger.info(f"软删除科室成功: id={dept_id_log}, name={dept.name}")
        return dept
    except Exception as e:
        await db.rollback()
        logger.error(f"软删除科室失败: id={dept_id_log}, error={str(e)}")
        raise
```

**函数 7：`get_unmapped_experts`** — 未映射专家列表

```python
async def get_unmapped_experts(
    db: AsyncSession,
    page: int = 1,
    size: int = 50,
) -> Tuple[List[Expert], int]:
    """
    查询 department_id IS NULL 的专家（未映射科室）。

    用于管理员"未映射专家看板"。
    按 created_at DESC 排序。
    """
    if page < 1:
        page = 1
    if size < 1:
        size = 50
    elif size > 200:
        size = 200

    query = select(Expert).where(Expert.department_id == None)
    query = query.order_by(Expert.created_at.desc())

    # count
    count_query = select(func.count()).select_from(query.subquery())
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    # pagination
    offset = (page - 1) * size
    query = query.offset(offset).limit(size)
    result = await db.execute(query)
    experts = result.scalars().all()

    logger.info(f"查询未映射专家: page={page}, size={size}, total={total}")
    return (list(experts), total)
```

### 5.2 修改：`app/crud/experts.py`

**改动 1 — 新增导入**

```python
# 在已有导入区域追加
from app.models.expert_departments import ExpertDepartment
```

位置：当前第 27 行的 `from app.models.experts import ...` 之后。

**改动 2 — 修改 `get_experts_public_list` 的 keyword 搜索**

当前第 201-211 行：

```python
if keyword and keyword.strip():
    kw = f"%{keyword.strip()}%"
    conditions.append(
        or_(
            Expert.name.ilike(kw),
            Expert.hospital.ilike(kw),
            Expert.department.ilike(kw),           # ← 删除这行
            Expert.expertise_areas.ilike(kw),
            Expert.bio.ilike(kw),
        )
    )
```

修改为：

```python
if keyword and keyword.strip():
    kw = f"%{keyword.strip()}%"
    conditions.append(
        or_(
            Expert.name.ilike(kw),
            Expert.hospital.ilike(kw),
            # ← P2: department 自由文本已改为受控词表 FK
            # keyword 在 expert_departments.name 上搜索
            Expert.department_id.in_(
                select(ExpertDepartment.id).where(
                    ExpertDepartment.name.ilike(kw)
                )
            ),
            Expert.expertise_areas.ilike(kw),
            Expert.bio.ilike(kw),
        )
    )
```

**改动 3 — 修改 `get_experts_public_list` 的 department 筛选**

当前第 213-215 行：

```python
if department and department.strip():
    conditions.append(Expert.department.ilike(f"%{department.strip()}%"))
```

修改为：

```python
if department and department.strip():
    conditions.append(
        Expert.department_id.in_(
            select(ExpertDepartment.id).where(
                ExpertDepartment.name.ilike(f"%{department.strip()}%")
            )
        )
    )
```

**改动 4 — 新增 `create_expert_raw` 函数**

在 `create_expert` 函数之后追加：

```python
async def create_expert_raw(
    db: AsyncSession,
    data: dict,
) -> Expert:
    """
    使用字典直接创建专家（融合方案专用）。

    Service 层已通过 _resolve_department_and_category 完成
    department_id 和 category_id 的解析，以 dict 形式传入。
    此函数不做任何业务校验，只负责写入数据库。

    Args:
        db: 数据库会话
        data: 专家创建数据字典（必须包含 name 等必需字段）

    Returns:
        创建的 Expert 对象
    """
    expert_id = uuid.uuid4()
    expert_id_log = str(expert_id)[:8]
    expert_name = data.get("name", "")

    if "is_active" not in data:
        data["is_active"] = True

    expert = Expert(id=expert_id, **data)

    try:
        db.add(expert)
        await db.flush()
        await db.refresh(expert)
        logger.info(f"创建专家成功（raw）: id={expert_id_log}, name={expert_name}")
        return expert
    except IntegrityError as e:
        await db.rollback()
        logger.error(f"创建专家失败（raw, 唯一性冲突）: id={expert_id_log}")
        raise DatabaseIntegrityException("该用户已绑定到其他专家档案")
    except Exception as e:
        await db.rollback()
        logger.error(f"创建专家失败（raw）: id={expert_id_log}, error={str(e)}")
        raise
```

**关键点**：
- 函数接收 `dict` 而非 `ExpertCreate`（因为 Service 层已经完成了 `department_id` 和 `category_id` 的解析和转换）
- 不调用 `model_dump()`（输入已经是 dict）
- `data` 中不应包含 `department_name`（Pydantic 字段）——只有 DB 列对应的 key

---

## 6. 完整性检查清单 (Completeness Checklist)

### 6.1 新文件 `expert_departments.py`

- ✅ 包含 7 个函数（get_paginated / get_by_id / get_by_name / create / update / soft_delete / get_unmapped_experts）
- ✅ 每个 create/update/delete 函数使用 `try/except IntegrityError` 模式
- ✅ 每个函数提前提取变量用于日志（`dept_id_log` 等）
- ✅ 分页查询使用 `func.count() + select().offset().limit()` 两次查询
- ✅ UUID 在应用层生成（`uuid.uuid4()`）
- ✅ `create_department` 使用 `db.add()` + `db.flush()` + `db.refresh()`
- ✅ `update_department` 使用 `setattr()` + `db.flush()` + `db.refresh()`
- ✅ `soft_delete_department` 设 `is_active=False` 而非物理删除
- ✅ `get_unmapped_experts` 查询 `Expert.department_id == None`
- ✅ 不调用 `db.commit()`（由上层 commit）
- ✅ 异常类型为 `DatabaseIntegrityException` 和 `InvalidParameterException`

### 6.2 修改文件 `experts.py`

- ✅ `get_experts_public_list` 的 keyword 搜索中 `Expert.department.ilike(kw)` 已移除
- ✅ keyword 替换为子查询 `Expert.department_id.in_(select(ExpertDepartment.id)...)`
- ✅ department 参数的筛选改为子查询
- ✅ `create_expert_raw` 接收 `dict` 参数（不是 Pydantic Schema）
- ✅ `create_expert_raw` 使用与 `create_expert` 相同的 `try/except IntegrityError` 模式
- ✅ 现有 `create_expert`、`get_expert`、`update_expert` 等函数签名**未修改**
- ✅ 导入 `ExpertDepartment` 已追加到 import 区域

### 6.3 代码风格一致性

- ✅ 日志使用 `logger = logging.getLogger(__name__)` 模式
- ✅ 每个函数有 Google-style docstring（Args / Returns / Raises）
- ✅ 变量名遵循 snake_case 规范
- ✅ 函数签名按"必需参数在前，可选参数在后"排序
- ✅ 提前提取变量（`dept_id_log`）在 try 块之前

### 6.4 不引入的问题

- ✅ `app/crud/experts.py` 中 `create_expert` 不被修改
- ✅ `app/crud/experts.py` 中 `get_expert` 不被修改
- ✅ `app/crud/experts.py` 中 `update_expert` 不被修改
- ✅ `app/crud/content_management.py` 不被修改
- ✅ `app/services/` 下所有文件不被修改
- ✅ `app/api/` 下所有文件不被修改

---

## 7. 最终交付 (Final Deliverable)

根据以上要求，生成以下 **2 个文件的修改**：

1. **新建** `app/crud/expert_departments.py` — 7 个 CRUD 函数
2. **修改** `app/crud/experts.py` — keyword 搜索改子查询 + 新增 `create_expert_raw`

**P2 完成后可验证的点**：

```python
# 验证 1：keyword 搜索使用新的子查询
kw = "%乳腺%"
subq = select(ExpertDepartment.id).where(ExpertDepartment.name.ilike(kw))
# SELECT experts.* FROM experts WHERE experts.department_id IN (subq)

# 验证 2：create_expert_raw 接收 dict
data = {"name": "张医生", "department_id": dept_uuid, "category_id": cat_uuid}
expert = await crud.create_expert_raw(db, data)

# 验证 3：get_unmapped_experts 查 NULL
experts, total = await crud.get_unmapped_experts(db, page=1, size=20)
# SELECT * FROM experts WHERE department_id IS NULL ORDER BY created_at DESC
```
