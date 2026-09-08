# 融合方案 P3 — Service + API 层代码生成提示词

**版本**: V1.0  
**创建日期**: 2026-06-23  
**基于设计文档**: `app修改记录/融合方案最终设计_A2+C.md`、`app修改记录/融合方案_提示词编写规范借鉴.md`  
**依赖**: P1 (Model + Schema) 已完成 + P2 (CRUD) 已完成  
**目标文件**: 修改 1 个 + 新建 1 个 + 修改 1 个

---

## 1. 角色定义 (Role Definition)

你是一名精通 Clean Architecture（学院派）分层架构的资深 Python 后端架构师。
你需要严格执行 CRUD / Service / API 三层的职责分离，并确保以下**项目级约束**不被破坏：

- Service 层**不直接调用 `db.commit()`**
- Service 层**不捕获裸 Exception**
- API 层使用 `try/except` 捕获 Service 抛出的自定义异常，转 `JSONResponse`
- 不引入数据库触发器 → 用应用层显式 `UPDATE` 同步
- 所有权限检查使用 `role in ['ADMIN', 'SUPERADMIN']`（必须大写）

**一个关键决策已在融合方案中做出**：应用层同步。修改 `expert_departments.category_id` 时，在同方法内显式执行 `UPDATE experts SET category_id = ...`。

---

## 2. 任务目标 (Task Objective)

### 2.1 修改文件（1 个）

| 文件 | 修改内容 | 说明 |
|:-----|:---------|:-----|
| `app/services/expert_service.py` | 6 个修改点 | 重写 `_resolve_active_category_id`、新增 `_resolve_department_and_category`、新增 `_match_broad_category`、新增 `_build_expert_item`、新增 `merge_departments`、新增 `update_department_category` |

### 2.2 新建文件（1 个）

| 文件 | 内容 | 说明 |
|:-----|:-----|:-----|
| `app/api/v1/endpoints/expert_departments.py` | 5 个 Admin API 端点 | GET 分页列表 / POST 创建 / PATCH 更新 / DELETE 软删除 / GET 未映射专家 |

### 2.3 修改文件（1 个）

| 文件 | 修改内容 | 说明 |
|:-----|:---------|:-----|
| `app/api/v1/endpoints/experts.py` | 2 个修改点 | `format_expert_response` 改为调用 `_build_expert_item` 填充 `category_name`；`get_featured_experts` 响应增加 `category_name` |

### 2.4 禁止事项

- ❌ 不修改 `app/crud/` 下的任何文件
- ❌ 不修改 `app/models/` 下的任何文件
- ❌ 不修改 `app/schemas/` 下的任何文件
- ❌ 不修改已有 Admin API 端点的 URL 签名
- ❌ 不在 ExpertDepartment API 端点中使用 `Depends(get_current_user_optional)`（Admin API 必须要求登录）

---

## 3. 核心上下文 (Core Context)

### 3.1 技术栈与架构约定

```
Python 3.9+ | SQLAlchemy 2.0 (async) | FastAPI | Pydantic v2
权限模式: get_current_user → current_user (dict) → user_id (UUID) + role (str)
Admin API: 使用 get_current_user（必须登录）
JWT 提取: user_id = uuid.UUID(current_user["user_id"]) / role = current_user.get("role")
```

### 3.2 已有代码参考

#### 参考 A：`app/services/expert_service.py` — 已有 ExpertService 类（第 67-720 行）

**关键观察点（8 个）**：

1. **构造函数**: `def __init__(self, db: AsyncSession)` → `self.db = db` + `self.logger`
2. **权限检查**: `self._check_admin_permission(role)` → `if role not in ['ADMIN', 'SUPERADMIN']`（大写）
3. **异常类型**: `PermissionDeniedException`、`NotFoundException`、`InvalidParameterException`
4. **方法签名**: `async def xxx(self, ...) -> ResultType`
5. **日志**: `self.logger.info(...)` / `self.logger.warning(...)` / `self.logger.error(...)`
6. **只读查询模式**: `await self.db.execute(select(...))` → `result.scalars().all()`
7. **预加载**: `selectinload(Expert.category)`
8. **CRUD 调用**: `await crud.create_expert(self.db, ...)` — 所有 DB 操作通过 CRUD

#### 参考 B：`app/api/v1/endpoints/experts.py` — 已有 Admin API 端点模式

**关键观察点（6 个）**：

1. **用户提取**: `user_id = uuid.UUID(current_user["user_id"])` + 提前提取（try 之前）
2. **Service 实例化**: `service = ExpertService(db)`（在 try 内）
3. **异常处理链**: `PermissionDeniedException → 403` / `InvalidParameterException → 400` / `NotFoundException → 404` / `Exception → 500`
4. **成功响应**: `success_response(data=...)`
5. **错误响应**: `JSONResponse(status_code=..., content=error_response(code=..., message=...))`
6. **日志**: `logger.info(...)` / `logger.warning(...)` / `logger.error(...)`

#### 参考 C：P1/P2 已生成

```
app/models/expert_departments.py:
  ExpertDepartment(id, name, category_id, synonyms, is_active, is_verified, ...)

app/schemas/expert_departments.py:
  ExpertDepartmentCreate, ExpertDepartmentUpdate, ExpertDepartmentItem, ExpertDepartmentBriefItem

app/crud/expert_departments.py:
  get_departments_paginated, get_department_by_id, get_department_by_name,
  create_department, update_department, soft_delete_department, get_unmapped_experts

app/crud/experts.py:
  create_expert_raw(db, data: dict) → Expert
```

---

## 4. 架构约束 (Architecture Constraints)

### 4.1 分层职责铁律

| 层 | 能做什么 | 不能做什么 |
|:--|:------|:---------|
| **CRUD** | `db.add()` / `db.flush()` / `db.refresh()` / `try/except IntegrityError` | `db.commit()` / 业务逻辑 |
| **Service** | 权限检查 / 业务校验 / 组装查询 / 调用 CRUD | `db.commit()` / 捕获裸 Exception / 直接操作 ORM 列 |
| **API** | 提取 JWT / 调用 Service / `try/except` 转 JSONResponse / 日志 | 业务逻辑 / 直接调用 CRUD |

### 4.2 API 层异常处理模板

```python
try:
    service = ExpertService(db)
    result = await service.some_action(...)
    return success_response(data=result)

except PermissionDeniedException as e:
    return JSONResponse(status_code=403, content=error_response(code=3003, message=str(e)))
except NotFoundException as e:
    return JSONResponse(status_code=404, content=error_response(code=e.code if hasattr(e,'code') else 2001, message=str(e)))
except InvalidParameterException as e:
    return JSONResponse(status_code=400, content=error_response(code=e.code if hasattr(e,'code') else 4001, message=str(e)))
except Exception as e:
    logger.error(f"意外错误: {str(e)}")
    return JSONResponse(status_code=500, content=error_response(code=1002, message="数据库操作错误"))
```

### 4.3 Service 层 commit 边界

P3 中有两个地方需要 `db.commit()`：

1. `merge_departments` — 需要 commit（多个写操作在同一个事务中）
2. `update_department_category` — 需要 commit（修改科室 + 同步专家）

**注意**：当前 ExpertService 的方法默认不 commit（由 API 层或调用方 commit）。但这两个方法由于涉及多个关联表的写操作，必须在自己内部 commit 以保持原子性。这是有意的设计例外。

### 4.4 `_resolve_department_and_category` — 只读查询

这个函数是只读的——它不做任何写操作。写操作路径（匹配不到 → UPSERT 创建新科室）在 `create_expert` 和 `batch_import` 的调用流程中实现。

---

## 5. 代码生成要求 (Specific Code Generation Requirements)

### 5.1 Service 层：`app/services/expert_service.py`

#### 改动 A — 在导入区域追加新导入

```python
# 在已有导入区域追加（第 33 行之后）
from app.models.expert_departments import ExpertDepartment
from app.models.content_management import Category
from app.schemas.expert_departments import ExpertDepartmentCreate, ExpertDepartmentItem, ExpertDepartmentBriefItem
from app.crud import expert_departments as crud_dept
from sqlalchemy import text, update as sa_update  # 已有 update 导入，确认存在即可
```

#### 改动 B — 新增 `_match_broad_category` 方法

在 `_resolve_active_category_id` 之后追加：

```python
    # ==================== 科室匹配辅助方法 ====================

    async def _match_broad_category(self, name: str) -> Optional[Category]:
        """
        从科室文本中提取根分类。

        策略：
        1. 子串匹配：根分类名包含在输入文本中（如"心内科-冠脉组"→"心内科"）
        2. 别名表匹配：在 DEPARTMENT_CATEGORY_MAP 中查找

        无正则回退。无模糊匹配。匹配不到返回 None。
        """
        from app.models.content_management import Category

        # 加载所有根分类（会话级缓存）
        if not hasattr(self, '_root_categories'):
            result = await self.db.execute(
                select(Category).where(
                    Category.parent_id == None,
                    Category.is_active == True
                ).order_by(Category.sort_order)
            )
            self._root_categories = result.scalars().all()

        # 1. 子串匹配
        for bc in self._root_categories:
            if bc.name in name:
                return bc

        # 2. 别名表匹配
        mapped_name = DEPARTMENT_CATEGORY_MAP.get(name)
        if mapped_name:
            for bc in self._root_categories:
                if bc.name == mapped_name:
                    return bc

        return None
```

**需要在文件头部（类定义之前）追加常量**：

```python
# 科室 → 根分类别名映射表（融合方案 P3）
DEPARTMENT_CATEGORY_MAP = {
    '乳腺外科': '普通外科',
    '甲状腺外科': '普通外科',
    '肝胆外科': '普通外科',
    '胃肠外科一科': '普通外科',
    '胃肠外科二科': '普通外科',
    '胃肠外科三科': '普通外科',
    '胆胰外科': '普通外科',
    '肝外科': '普通外科',
    '脊柱外科': '骨科',
    '关节外科': '骨科',
    '骨肿瘤科': '骨科',
    '运动医学科': '骨科',
    '显微创伤外手科': '骨科',
    '妇科': '妇产科',
    '产科': '妇产科',
    '鼻专科': '耳鼻喉科',
    '耳专科': '耳鼻喉科',
    '咽喉专科': '耳鼻喉科',
    '肾移植专科': '器官移植科',
    '器官移植科/肾移植专科': '器官移植科',
    '器官移植科/肝移植专科': '器官移植科',
    '泌尿外科/男科': '泌尿外科',
    '生殖医学中心': '生殖医学科',
    '生殖男科专科': '生殖医学科',
    '男科/生殖医学中心': '生殖医学科',
    '胸外科': '心胸外科',
    '口内修复科': '口腔科',
    '口腔颌面外科': '口腔科',
    '小儿外科': '儿科',
    '变态反应专科': '其他',
    '外科门诊': '其他',
    '肝外科/超声医学科/介入超声专科': '其他',
}
```

#### 改动 C — 新增 `_resolve_department_and_category` 方法

```python
    async def _resolve_department_and_category(
        self,
        department_name: Optional[str],
        category_id: Optional[uuid.UUID],
    ) -> Tuple[Optional[uuid.UUID], uuid.UUID]:
        """
        解析专家科室和分类（只读匹配 + 自适应创建 is_verified=False）。

        返回 (department_id, category_id)。
        department_id 可能为 None（匹配不到任何科室时）。
        category_id 永不返回 None（回退到"其他"分类）。

        规则：
        1. 传了 category_id → 直接使用（管理员明确指定分类）
        2. 传了 department_name → 匹配 expert_departments 表
           a. 精确匹配 name → (dept_id, category_id)
           b. 同义词匹配 synonyms → (dept_id, category_id)
           c. 子串匹配 + 别名表 → 归入"其他-{大类}"子分类
           d. 完全匹配不到 → UPSERT 创建 is_verified=False 科室
        3. 都没传 → (None, OTHER_CATEGORY_ID)
        """
        from app.models.content_management import Category

        # 1. 管理员明确指定了分类
        if category_id is not None:
            cat = await self.db.get(Category, category_id)
            if cat and cat.is_active:
                return (None, category_id)
            raise InvalidParameterException("分类不存在或已禁用")

        # 2. 传了科室名称
        if department_name and department_name.strip():
            normalized = department_name.strip()

            # 2a. 精确匹配标准名称
            dept = await crud_dept.get_department_by_name(self.db, normalized)
            if dept:
                return (dept.id, dept.category_id)

            # 2b. 同义词匹配（synonyms JSONB 数组）
            result = await self.db.execute(
                text("SELECT id, category_id FROM expert_departments "
                     "WHERE :name = ANY(synonyms) AND is_active = true"),
                {"name": normalized}
            )
            row = result.one_or_none()
            if row:
                return (row[0], row[1])

            # 2c. 子串匹配 + 别名表
            category = await self._match_broad_category(normalized)
            if category:
                # 归入对应大类下的"其他-{大类}"子分类
                fallback_dept = await crud_dept.get_department_by_name(
                    self.db, f"其他-{category.name}"
                )
                if fallback_dept:
                    return (fallback_dept.id, category.id)
                return (None, category.id)

            # 2d. 匹配不到 → UPSERT 创建 is_verified=False 科室
            new_dept = ExpertDepartment(
                id=uuid.uuid4(),
                name=normalized,
                category_id=OTHER_CATEGORY_ID,
                is_verified=False,
            )
            try:
                self.db.add(new_dept)
                await self.db.flush()
                await self.db.refresh(new_dept)
                self.logger.info(f"自动创建科室(is_verified=false): name={normalized}")
            except Exception:
                await self.db.rollback()
                # 并发冲突 → 查已有记录
                dept = await crud_dept.get_department_by_name(self.db, normalized)
                if dept:
                    return (dept.id, dept.category_id)
            else:
                return (new_dept.id, new_dept.category_id)

        # 3. 都没传 → "其他"
        other_cat = await self.db.execute(
            select(Category.id).where(Category.name == "其他", Category.is_active == True)
        )
        return (None, other_cat.scalar_one())
```

**关键点**：
- `OTHER_CATEGORY_ID` 在 `__init__` 中初始化（懒加载）
- UPSERT 失败时查已有记录（并发冲突兜底）
- 自动创建的科室 `is_verified=False`

#### 改动 D — 新增 `_build_expert_item` 方法

```python
    async def _build_expert_item(self, expert: Expert) -> ExpertItem:
        """
        构建专家响应，填充 department_name 和 category_name。

        需要预加载 expert.category 和 expert.expert_department。
        如果未预加载，在此函数内按需查询。
        """
        # 按需加载 category
        category_name = None
        if expert.category_id:
            if hasattr(expert, 'category') and expert.category:
                category_name = expert.category.name
            else:
                result = await self.db.execute(
                    select(Category).where(Category.id == expert.category_id)
                )
                cat = result.scalar_one_or_none()
                category_name = cat.name if cat else None

        # 按需加载 expert_department
        department_name = None
        if expert.department_id:
            if hasattr(expert, 'expert_department') and expert.expert_department:
                department_name = expert.expert_department.name
            else:
                result = await self.db.execute(
                    select(ExpertDepartment).where(ExpertDepartment.id == expert.department_id)
                )
                dept = result.scalar_one_or_none()
                department_name = dept.name if dept else None

        item = ExpertItem.model_validate(expert)
        item.category_name = category_name
        item.department_name = department_name
        return item
```

#### 改动 E — 新增 `merge_departments` 方法

```python
    async def merge_departments(
        self,
        source_id: uuid.UUID,
        target_id: uuid.UUID,
    ) -> dict:
        """
        将源科室合并到目标科室（管理员操作）。

        1. 源科室名吸入目标同义词（上限 20 条）
        2. 自动升级 verified 状态
        3. 转移专家关联（department_id）
        4. 应用层同步 category_id
        5. 物理删除源科室
        """
        SYNONYM_LIMIT = 20

        source = await crud_dept.get_department_by_id(self.db, source_id)
        target = await crud_dept.get_department_by_id(self.db, target_id)
        if not source:
            raise NotFoundException("源科室不存在")
        if not target:
            raise NotFoundException("目标科室不存在")

        # 1. 自学习同义词
        new_synonyms = set(target.synonyms or [])
        new_synonyms.add(source.name)
        if source.synonyms:
            new_synonyms.update(source.synonyms)
        target.synonyms = list(new_synonyms)[:SYNONYM_LIMIT]

        # 2. 自动升级 verified 状态
        if source.is_verified and not target.is_verified:
            target.is_verified = True

        # 3. 转移专家关联
        await self.db.execute(
            sa_update(Expert)
            .where(Expert.department_id == source_id)
            .values(department_id=target_id)
        )

        # 4. 同步 category_id（应用层）
        await self.db.execute(
            sa_update(Expert)
            .where(Expert.department_id == target_id)
            .values(category_id=target.category_id)
        )

        # 5. 物理删除源科室
        await self.db.execute(
            sa_update(ExpertDepartment.__table__)
            .where(ExpertDepartment.id == source_id)
            .values(is_active=False)
        )
        await self.db.execute(
            sa_update(ExpertDepartment.__table__)
            .where(ExpertDepartment.id == source_id)
        )
        # 复用 delete 语句
        from sqlalchemy import delete
        await self.db.execute(delete(ExpertDepartment).where(ExpertDepartment.id == source_id))

        await self.db.commit()
        self.logger.info(f"合并科室成功: source={source.name} → target={target.name}")

        return {
            "source_name": source.name,
            "target_name": target.name,
            "synonyms_count": len(target.synonyms),
        }
```

#### 改动 F — 新增 `update_department_category` 方法

```python
    async def update_department_category(
        self,
        dept_id: uuid.UUID,
        new_category_id: uuid.UUID,
    ) -> ExpertDepartmentItem:
        """
        修改科室的分类 + 应用层显式同步所有关联专家的 category_id。

        替代数据库触发器。在一个方法内保证一致性。
        """
        dept = await crud_dept.get_department_by_id(self.db, dept_id)
        if not dept:
            raise NotFoundException("科室不存在")

        # 校验分类
        cat = await self.db.get(Category, new_category_id)
        if not cat or not cat.is_active:
            raise InvalidParameterException("目标分类不存在或已禁用")

        dept.category_id = new_category_id

        # 应用层同步所有关联专家
        await self.db.execute(
            sa_update(Expert)
            .where(Expert.department_id == dept_id)
            .values(category_id=new_category_id)
        )

        await self.db.commit()
        await self.db.refresh(dept)
        self.logger.info(f"科室分类已更新+同步: dept={dept.name}, new_cat={cat.name}")

        return ExpertDepartmentItem(
            id=dept.id,
            name=dept.name,
            category_id=dept.category_id,
            category_name=cat.name,
            synonyms=dept.synonyms or [],
            is_active=dept.is_active,
            is_verified=dept.is_verified,
            expert_count=0,
            created_at=dept.created_at,
            updated_at=dept.updated_at,
        )
```

#### 改动 G — 修改 `create_expert` 方法

将当前 `create_expert`（第 350-400 行）中的 category_id 校验替换为调用 `_resolve_department_and_category`：

```python
    # 原第 380 行附近的 category_id 校验改为：
    # 解析科室和分类
    dept_id, cat_id = await self._resolve_department_and_category(
        department_name=getattr(expert_data, 'department_name', None),
        category_id=expert_data.category_id,
    )

    # 构造创建数据
    create_dict = expert_data.model_dump(exclude={'department_name', 'category_id'})
    create_dict['department_id'] = dept_id
    create_dict['category_id'] = cat_id

    expert = await crud.create_expert_raw(self.db, create_dict)
    await self.db.commit()
    await self.db.refresh(expert)

    # 用 _build_expert_item 填充 category_name 和 department_name
    result = await self._build_expert_item(expert)
    return result
```

### 5.2 新建：`app/api/v1/endpoints/expert_departments.py`

**文件头部**：

```python
"""
专家科室受控词表 — Admin API 端点

提供科室的 CRUD 管理和未映射专家查询。
所有端点需要管理员权限。
"""
import uuid
import logging
from typing import Optional
from fastapi import APIRouter, Depends, Query, Path
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.core.auth import get_current_user
from app.core.response import success_response, error_response
from app.services.expert_service import ExpertService
from app.schemas.expert_departments import ExpertDepartmentCreate, ExpertDepartmentUpdate
from app.exceptions import PermissionDeniedException, NotFoundException, InvalidParameterException

logger = logging.getLogger(__name__)

expert_dept_admin_router = APIRouter(tags=["科室管理-管理员"])
```

**端点 1：GET 分页列表**

```python
@expert_dept_admin_router.get("/admin/expert-departments")
async def list_departments(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=50, ge=1, le=200),
    is_active: Optional[bool] = Query(default=None),
    is_verified: Optional[bool] = Query(default=None),
    category_id: Optional[str] = Query(default=None),
    q: Optional[str] = Query(default=None, max_length=100),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """管理员查询科室列表（分页）"""
    user_id = uuid.UUID(current_user["user_id"])
    role = current_user.get("role")
    user_id_log = str(user_id)[:8]

    cat_uuid = None
    if category_id:
        try:
            cat_uuid = uuid.UUID(category_id)
        except (ValueError, TypeError):
            return JSONResponse(status_code=400, content=error_response(code=4001, message="无效的分类ID格式"))

    try:
        from app.crud import expert_departments as crud_dept
        items, total = await crud_dept.get_departments_paginated(
            db, page=page, size=size, is_active=is_active,
            is_verified=is_verified, category_id=cat_uuid, q=q,
        )
        return success_response(data={"items": items, "total": total, "page": page, "size": size})
    except Exception as e:
        logger.error(f"查询科室列表失败: user_id={user_id_log}, error={str(e)}")
        return JSONResponse(status_code=500, content=error_response(code=1002, message="数据库操作错误"))
```

**端点 2：POST 创建**

```python
@expert_dept_admin_router.post("/admin/expert-departments")
async def create_department(
    department_data: ExpertDepartmentCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """管理员创建科室"""
    user_id = uuid.UUID(current_user["user_id"])
    role = current_user.get("role")
    user_id_log = str(user_id)[:8]

    try:
        service = ExpertService(db)
        service._check_admin_permission(role)
        from app.crud import expert_departments as crud_dept
        dept = await crud_dept.create_department(db, department_data)
        await db.commit()
        await db.refresh(dept)
        return success_response(data={"id": str(dept.id), "name": dept.name, "category_id": str(dept.category_id)})
    except PermissionDeniedException as e:
        return JSONResponse(status_code=403, content=error_response(code=3003, message=str(e)))
    except InvalidParameterException as e:
        return JSONResponse(status_code=400, content=error_response(code=e.code if hasattr(e,'code') else 4001, message=str(e)))
    except Exception as e:
        logger.error(f"创建科室失败: user_id={user_id_log}, error={str(e)}")
        return JSONResponse(status_code=500, content=error_response(code=1002, message="数据库操作错误"))
```

**端点 3：PATCH 更新**

```python
@expert_dept_admin_router.patch("/admin/expert-departments/{department_id}")
async def update_department(
    department_id: uuid.UUID = Path(...),
    department_data: ExpertDepartmentUpdate = ...,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # 标准 try/except 模式，调用 crud_dept.update_department()
    ...
```

**端点 4：DELETE 软删除**

```python
@expert_dept_admin_router.delete("/admin/expert-departments/{department_id}")
async def delete_department(...):
    # 调用 crud_dept.soft_delete_department()
    ...
```

**端点 5：GET 未映射专家**

```python
@expert_dept_admin_router.get("/admin/expert-departments/unmapped")
async def list_unmapped_experts(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=50, ge=1, le=200),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """列出所有 department_id IS NULL 的专家"""
    ...
    # 调用 crud_dept.get_unmapped_experts()
    ...
```

### 5.3 修改：`app/api/v1/endpoints/experts.py`

**改动 A — `format_expert_response` 增加 `category_name`**

```python
def format_expert_response(expert, request: Request = None) -> dict:
    data = {
        ...
        "category_id": str(expert.category_id) if expert.category_id else None,
        "category_name": getattr(expert, 'category_name', None),  # ← 新增
        "department_name": getattr(expert, 'department_name', None),  # ← 新增
        ...
    }
```

**改动 B — `get_featured_experts` 端点适配**

```python
@experts_featured_router.get("/featured-experts")
async def get_featured_experts(...):
    ...
    experts = await service.get_featured_experts(limit=limit)
    experts_data = [
        {
            ...
            "category_id": str(expert.category_id) if expert.category_id else None,
            "category_name": getattr(expert, 'category_name', None),  # ← 新增
            ...
        }
        for expert in experts
    ]
```

---

## 6. 完整性检查清单 (Completeness Checklist)

### 6.1 Service 层

- ✅ `_match_broad_category` 有子串匹配 + 别名表，无正则
- ✅ `_resolve_department_and_category` 有 4 级匹配优先级
- ✅ `_resolve_department_and_category` 永远不返回 `category_id=None`
- ✅ 自动创建科室 `is_verified=False`
- ✅ `_build_expert_item` 填充 `category_name` 和 `department_name`
- ✅ `merge_departments` 含同义词自学习 + 应用层同步
- ✅ `merge_departments` + `update_department_category` 调用 `db.commit()`
- ✅ `DEPARTMENT_CATEGORY_MAP` 包含 30+ 条别名
- ✅ 不修改已有方法的签名（只修改方法体）

### 6.2 API 层 — 新建端点

- ✅ 5 个端点均有完整的 `try/except` 异常处理
- ✅ 所有端点使用 `get_current_user`（必须登录）
- ✅ 异常处理链：PermissionDeniedException → 403 / NotFound → 404 / InvalidParam → 400 / Exception → 500
- ✅ 分页参数有默认值 + 边界校验
- ✅ 日志级别正确（info 成功 / warning 权限 / error 异常）

### 6.3 API 层 — 已修改端点

- ✅ `format_expert_response` 新增 `category_name` 和 `department_name`（不破坏已有结构）
- ✅ `get_featured_experts` 响应新增 `category_name`
- ✅ 不修改已有路由 URL 签名

### 6.4 全局约束

- ✅ 不修改 `app/crud/` 下任何文件
- ✅ 不修改 `app/models/` 下任何文件
- ✅ 不引入数据库触发器
- ✅ 权限检查使用 `role in ['ADMIN', 'SUPERADMIN']`（大写）
- ✅ `DEPARTMENT_CATEGORY_MAP` 定义在文件头部（类定义之前）

---

## 7. 最终交付 (Final Deliverable)

根据以上要求，生成以下 **3 个文件的修改**：

1. **修改** `app/services/expert_service.py` — 6 个改动（B~G）
2. **新建** `app/api/v1/endpoints/expert_departments.py` — 5 个 Admin API 端点
3. **修改** `app/api/v1/endpoints/experts.py` — `format_expert_response` + `get_featured_experts`

**P3 完成后可验证的点**：

```python
# 验证 1：匹配科室
dept_id, cat_id = await service._resolve_department_and_category("乳腺外科", None)
# → ("乳腺外科" 的 UUID, "普通外科" 的 UUID)

# 验证 2：适配新科室
dept_id, cat_id = await service._resolve_department_and_category("结构性心脏病组", None)
# → (自动创建的 UUID, "其他" 的 UUID)  ← 因为"结构性"不在别名表、不包含任何根分类子串

# 验证 3：build_expert_item 填充
item = await service._build_expert_item(expert)
# item.department_name = "乳腺外科"
# item.category_name = "普通外科"
```
