# 专家分类管理 App 端接口优化 — 代码生成提示词

**版本**: V1.0
**创建日期**: 2026-07-24
**基于设计文档**: `app修改记录/专家分类管理_App端接口优化设计文档.md`
**依赖**: 无（所有依赖的 Model / Schema / CRUD / 端点 / 权限守卫均已就绪）
**目标文件**: 修改 6 个已有文件
**改动模式**: 在已有端点文件中追加新路由 / 在已有函数上扩展响应字段和参数

---

## 1. 角色定义 (Role Definition)

你是一名精通 FastAPI + SQLAlchemy 2.0 async + PostgreSQL 的 Python 后端工程师。你熟悉本项目的"学院派"分层架构（CRUD → Service → Endpoint）、`success_response` / `error_response` 统一响应格式、`Depends(get_current_user)` + `check_admin_permission(role)` 鉴权模式。

你的任务是为「专家分类管理」App 端页面补齐 4 个后端接口缺口，**严格在已有文件内追加代码**，不新建文件，不修改现有 API 签名。

**四个必须**：
- 必须遵循已有 `expert_departments.py` / `content_management.py` / `experts.py` 中各端点的代码风格（内联 CRUD、try/except 转 JSONResponse、lazy import）
- 必须使用 `check_admin_permission(role)` 做权限守卫（对齐已有端点）
- 必须确保 `GET /{department_id}` 路由注册在 `GET /unmapped` **之后**，否则 FastAPI 会把 `"unmapped"` 当作 UUID 解析
- 不修改任何已有端点的 URL 签名和 HTTP 方法

---

## 2. 任务目标 (Task Objective)

### 2.1 修改已有文件（6 个）

| # | 文件 | Phase | 改动内容 |
|:--:|------|:--:|------|
| 1 | `app/api/v1/endpoints/expert_departments.py` | P1, P2 | 新增 `GET /{department_id}` 详情端点（追加在文件末尾）；扩展 `list_unmapped_experts` 响应字段 |
| 2 | `app/crud/expert_departments.py` | P2 | `get_unmapped_experts` 增加 `joinedload(Expert.category)` |
| 3 | `app/api/v1/endpoints/content_management.py` | P3 | 新增 `GET /categories/department-stats` 统计端点（追加在 `categories_stats` 之后）；新增 `check_admin_permission` 导入 |
| 4 | `app/crud/experts.py` | P4 | `get_experts_multi_and_total` 签名新增 `department_id` 参数 + WHERE 条件 |
| 5 | `app/services/expert_service.py` | P4 | `get_experts_list` 签名新增 `department_id` + 透传至 CRUD |
| 6 | `app/api/v1/endpoints/experts.py` | P4 | `get_experts_list` 新增 `department_id` Query param + UUID 校验 + 透传至 Service |

### 2.2 禁止事项

- ❌ 不修改 `app/models/` 下的任何文件
- ❌ 不修改 `app/schemas/` 下的任何文件
- ❌ 不修改 `app/core/` 下的 `deps.py`、`permissions.py`、`config.py`
- ❌ 不修改 `app/api/v1/api.py` 路由注册
- ❌ 不修改已有端点的 HTTP 方法和 URL 路径签名
- ❌ 不新建文件
- ❌ 不在 Admin 端点使用 `Depends(get_current_user_optional)`（必须 `get_current_user`）

---

## 3. 核心上下文 (Core Context)

### 3.1 技术栈与架构约定

```
Python 3.9+ | SQLAlchemy 2.0 (async) | FastAPI | Pydantic v2
asyncpg → PostgreSQL 15
鉴权: get_current_user → current_user (dict) → user_id (UUID) + role (str)
Admin 权限: check_admin_permission(role)  # from app.core.permissions
JWT 提取: user_id = uuid.UUID(current_user["user_id"]); role = current_user.get("role")
响应: success_response(data=...) / JSONResponse(status_code=XXX, content=error_response(...))
```

### 3.2 已有端点代码风格（必须模仿）

本提示词涉及的已有文件中，所有端点均遵循以下模式（来自 `expert_departments.py`）：

```python
@expert_dept_admin_router.get("/expert-departments/unmapped")
async def list_unmapped_experts(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=50, ge=1, le=200),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """列出所有 department_id IS NULL 的专家（未映射科室）"""
    user_id = uuid.UUID(current_user["user_id"])
    role = current_user.get("role")

    try:
        check_admin_permission(role)
        from app.crud import expert_departments as crud_dept    # ← lazy import
        experts, total = await crud_dept.get_unmapped_experts(db, page=page, size=size)
        return success_response(data={...})
    except PermissionDeniedException as e:
        return JSONResponse(status_code=403, content=error_response(code=3003, message=str(e)))
    except Exception as e:
        logger.error(f"查询未映射专家失败: error={str(e)}")
        return JSONResponse(status_code=500, content=error_response(code=1002, message="数据库操作错误"))
```

**关键观察点（8 条必遵循）**：

1. **权限检查**: 在 `try` 块第一行调用 `check_admin_permission(role)`，不在 Service 层重复检查
2. **Lazy import**: CRUD 模块在函数内 `from app.crud import xxx as crud_xxx`，不在文件顶部
3. **异常捕获**: 捕获 `PermissionDeniedException` → 403；裸 `Exception` → 500 + `error_response(code=1002)`
4. **变量提取**: `user_id = uuid.UUID(current_user["user_id"])` 在 try 前执行，避免 except 块访问失效对象
5. **响应构造**: 成功用 `success_response(data=...)`；错误用 `JSONResponse(status_code=XXX, content=error_response(...))`
6. **日志**: `logger.error(f"操作失败: error={str(e)}")`，不需要 `logger.info`
7. **参数校验**: UUID 格式校验在 try 前独立完成（参考 `category_id` 校验模式）
8. **不掉 Service 层**: 逻辑简单的端点直接在 endpoint 层调用 CRUD（参考 `list_departments`、`list_unmapped_experts` 等）

### 3.3 三层参数透传模式（Phase 4 参照）

参考已有 `category_id` 的透传链路，新增 `department_id` 必须完全对齐同一模式：

```
Endpoint (experts.py)           Service (expert_service.py)        CRUD (experts.py)
───────────────────             ──────────────────────────         ──────────────────
department_id: Optional[str]    department_id: Optional[uuid.UUID] department_id: Optional[uuid.UUID]
  ↓ UUID 校验                     ↓ 透传                            ↓ WHERE 条件
department_uuid: uuid.UUID       crud.get_...(..., department_id)  Expert.department_id == department_id
  ↓ 传入 Service
service.get_...(department_id=department_uuid)
```

---

## 4. 架构约束 (Architecture Constraints)

### 4.1 分层职责（不可违背）

| 层 | 负责 | 禁止 |
|----|------|------|
| Endpoint | 鉴权（JWT 提取 + `check_admin_permission`）、参数校验（UUID 格式）、调用 CRUD/Service、异常 → JSONResponse 转换 | 不包含复杂业务逻辑 |
| Service | 复杂业务逻辑、多表操作协调、自定义异常抛出 | 不直接调用 `db.commit()`（由 Endpoint 层调用） |
| CRUD | 纯数据库操作、`IntegrityError` → `DatabaseIntegrityException` | 不包含权限/业务逻辑 |

### 4.2 路由注册顺序（⚠️ 关键）

`GET /expert-departments/{department_id}` **必须注册在 `GET /expert-departments/unmapped` 之后**。

```
正确顺序（在文件中的位置）：
  L153: @expert_dept_admin_router.get("/expert-departments/unmapped")   ← 先注册
  L181: @expert_dept_admin_router.post("/expert-departments/merge")
  L208: @expert_dept_admin_router.patch("/expert-departments/{department_id}/category")
  L235: @expert_dept_admin_router.post("/expert-departments/batch-verify")
  L275: @expert_dept_admin_router.get("/expert-departments/{department_id}")  ← 追加在最后

错误顺序会导致 "/unmapped" 被 "{department_id}" 匹配，尝试 "unmapped" 做 UUID 解析报错。
```

### 4.3 异常码体系（与已有端点一致）

| HTTP 状态码 | code | message | 场景 |
|:---:|:---:|------|------|
| 200 | 200 | success | 正常响应 |
| 400 | 4001 | 无效的 `{param}` 格式 | UUID 校验失败 |
| 403 | 3003 | 权限不足：需要管理员权限 | role 非 ADMIN/SUPERADMIN |
| 404 | 2001 | 科室不存在 / 资源不存在 | ID 在数据库中不存在 |
| 500 | 1002 | 数据库操作错误 | DB 异常 |

---

## 5. 代码生成要求 (Code Generation Requirements)

### Phase 1 — `GET /admin/expert-departments/{department_id}` 科室详情

**文件**: `app/api/v1/endpoints/expert_departments.py`
**位置**: 追加在文件末尾（`batch_verify_departments` 函数之后）
**路由**: `@expert_dept_admin_router.get("/expert-departments/{department_id}")`

**函数签名和完整实现**（从设计文档 §4.1 逐行照搬）：

```python
@expert_dept_admin_router.get("/expert-departments/{department_id}")
async def get_department_detail(
    department_id: uuid.UUID = Path(...),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """管理员查看单个科室详情（含 expert_count）"""
    user_id = uuid.UUID(current_user["user_id"])
    role = current_user.get("role")

    try:
        check_admin_permission(role)
        from app.crud import expert_departments as crud_dept
        from app.models.experts import Expert
        from sqlalchemy import select as sa_select, func as sa_func

        dept = await crud_dept.get_department_by_id(db, department_id)
        if dept is None:
            return JSONResponse(
                status_code=404,
                content=error_response(code=2001, message="科室不存在"),
            )

        # 填充 expert_count（该科室下所有专家数，含 is_active=False）
        count_q = sa_select(sa_func.count(Expert.id)).where(
            Expert.department_id == department_id
        )
        count_res = await db.execute(count_q)
        dept.expert_count = count_res.scalar() or 0

        # 填充 category_name（利用 ExpertDepartment.category relationship）
        if dept.category is not None:
            dept.category_name = dept.category.name

        result = ExpertDepartmentItem.model_validate(dept)
        return success_response(data=result)
    except PermissionDeniedException as e:
        return JSONResponse(
            status_code=403,
            content=error_response(code=3003, message=str(e)),
        )
    except Exception as e:
        logger.error(f"查询科室详情失败: dept_id={str(department_id)[:8]}, error={str(e)}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="数据库操作错误"),
        )
```

**要点**：
- 复用已有 CRUD `get_department_by_id`（`crud/expert_departments.py:116`）
- `Expert` 和 `sa_select`/`sa_func` 采用 lazy import（对齐已有端点风格）
- `success_response(data=result)` — 直接传 Pydantic model，**不用** `.model_dump()`
- `ExpertDepartmentItem` 已在文件顶部导入（来自 `app.schemas.expert_departments`）

---

### Phase 2 — unmapped 端点增强响应字段

#### 2a. 端点响应扩展

**文件**: `app/api/v1/endpoints/expert_departments.py`
**位置**: `list_unmapped_experts` 函数的 `success_response` 返回体（约 L168-173）

**替换前**：
```python
"items": [{"id": str(e.id), "name": e.name} for e in experts],
```

**替换为**：
```python
"items": [
    {
        "id": str(e.id),
        "name": e.name,
        "title": e.title,
        "hospital": e.hospital,
        "avatar_url": e.avatar_url,
        "category_id": str(e.category_id) if e.category_id else None,
        "category_name": e.category.name if e.category else None,
        "expertise_areas": e.expertise_areas or [],
        "is_active": e.is_active,
        "is_verified": e.is_verified,
    }
    for e in experts
],
```

**要点**：
- `e.is_verified` — Expert 模型已有此字段（`models/experts.py:71`），无需 `hasattr` 安全回退
- `e.category` — 依赖 Phase 2b 的 `joinedload` 预加载

#### 2b. CRUD 层预加载 category

**文件**: `app/crud/expert_departments.py`
**位置**: `get_unmapped_experts` 函数中（约 L285）

**替换前**：
```python
query = select(Expert).where(Expert.department_id == None)
```

**替换为**：
```python
query = (
    select(Expert)
    .options(joinedload(Expert.category))
    .where(Expert.department_id == None)
)
```

**要点**：
- `joinedload` 已在同文件顶部导入（来自 `sqlalchemy.orm`）
- 目的是让 `list_unmapped_experts` 端点中的 `e.category.name` 不触发 N+1 查询

---

### Phase 3 — `GET /admin/categories/department-stats` 统计端点

**文件**: `app/api/v1/endpoints/content_management.py`

#### 3a. 新增导入

**位置**: 文件顶部导入区（约 L17，`app.core.response` 之后）

**新增一行**：
```python
from app.core.permissions import check_admin_permission
```

> 说明：`content_management.py` 已有代码使用 `service._check_admin_permission(role)`（私有方法调用），本端点不依赖 `ContentManagementService`，需显式导入 `check_admin_permission`。

#### 3b. 新增端点

**位置**: `categories_stats` 函数（约 L526 `return JSONResponse(...)`）之后，`get_category_by_id` 函数之前。
**路由**: `@content_admin_router.get("/categories/department-stats")`

**完整函数实现**：

```python
@content_admin_router.get("/categories/department-stats")
async def get_department_stats_by_category(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """管理员获取按分类维度的科室与专家统计"""
    role = current_user.get("role")

    try:
        check_admin_permission(role)

        from sqlalchemy import select as sa_select, func, case
        from app.models.expert_departments import ExpertDepartment
        from app.models.experts import Expert
        from app.models.content_management import Category

        # 子查询：每个科室关联的专家数（只统计有科室归属的专家）
        expert_subq = (
            sa_select(
                Expert.department_id,
                func.count(Expert.id).label("expert_cnt"),
            )
            .where(Expert.department_id.isnot(None))
            .group_by(Expert.department_id)
        ).subquery()

        # 主查询：按 category_id GROUP BY
        stats_q = (
            sa_select(
                ExpertDepartment.category_id,
                func.count(ExpertDepartment.id).label("dept_count"),
                func.coalesce(func.sum(expert_subq.c.expert_cnt), 0).label("expert_count"),
                func.count(
                    case((ExpertDepartment.is_verified == True, 1))
                ).label("verified_count"),
                func.count(
                    case((ExpertDepartment.is_verified == False, 1))
                ).label("unverified_count"),
            )
            .outerjoin(expert_subq, ExpertDepartment.id == expert_subq.c.department_id)
            .where(ExpertDepartment.is_active == True)
            .group_by(ExpertDepartment.category_id)
        )
        stats_res = await db.execute(stats_q)
        stats_rows = stats_res.fetchall()

        # 查询所有活跃分类（25 个根分类，按 sort_order 排列）
        all_cats_q = (
            sa_select(Category.id, Category.name)
            .where(Category.is_active == True)
            .order_by(Category.sort_order.asc())
        )
        all_cats_res = await db.execute(all_cats_q)
        all_cats = all_cats_res.fetchall()

        # 构建 stats_by_cat 映射
        stats_by_cat = {}
        for row in stats_rows:
            stats_by_cat[row[0]] = {
                "department_count": row[1],
                "expert_count": row[2],
                "verified_department_count": row[3],
                "unverified_department_count": row[4],
            }

        # 全量输出（含 department_count=0 的分类）
        per_category = []
        for cat_id, cat_name in all_cats:
            s = stats_by_cat.get(cat_id, {})
            per_category.append({
                "category_id": str(cat_id),
                "category_name": cat_name,
                "department_count": s.get("department_count", 0),
                "expert_count": s.get("expert_count", 0),
                "verified_department_count": s.get("verified_department_count", 0),
                "unverified_department_count": s.get("unverified_department_count", 0),
            })

        # 全局 unmapped 专家计数
        unmapped_q = sa_select(func.count(Expert.id)).where(
            Expert.department_id == None,
        )
        unmapped_res = await db.execute(unmapped_q)
        unmapped_total = unmapped_res.scalar() or 0

        return success_response(data={
            "stats": per_category,
            "summary": {
                "total_categories": len(all_cats),
                "total_departments": sum(
                    s.get("department_count", 0) for s in per_category
                ),
                "total_unmapped_experts": unmapped_total,
            },
        })
    except PermissionDeniedException as e:
        return JSONResponse(
            status_code=403,
            content=error_response(code=3003, message=str(e)),
        )
    except Exception as e:
        logger.error(f"查询科室分类统计失败: error={str(e)}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="数据库操作错误"),
        )
```

**要点**：
- 使用 `sa_select` 别名避免与文件内已有的 `select` 导入冲突
- `func.count(case(...))` 是标准 SQL `COUNT(CASE WHEN ... THEN 1 END)` 模式，只统计非 NULL 值
- `outerjoin` + `coalesce(..., 0)` 确保没有专家的科室也能正确统计
- `all_cats` 查询按 `sort_order` 排列，保证 "其他" 排在最后
- `total_departments` 仅统计 `is_active=True` 的科室（与主查询 WHERE 条件一致）

---

### Phase 4 — `GET /admin/experts` 新增 `department_id` 筛选

按 **Endpoint → Service → CRUD** 顺序逐层修改。

#### 4a. CRUD 层

**文件**: `app/crud/experts.py`
**位置**: `get_experts_multi_and_total` 函数

**签名修改**（~L315，在 `category_id` 参数之后）：
```python
    category_id: Optional[uuid.UUID] = None,
    department_id: Optional[uuid.UUID] = None   # ← 新增
) -> Tuple[List[Expert], int]:
```

**条件区修改**（~L352-353，在 `category_id` 条件之后）：
```python
    if category_id is not None:
        conditions.append(Expert.category_id == category_id)
    if department_id is not None:                                 # ← 新增
        conditions.append(Expert.department_id == department_id)  # ← 新增
```

#### 4b. Service 层

**文件**: `app/services/expert_service.py`
**位置**: `get_experts_list` 方法

**签名修改**（~L661，在 `category_id` 参数之后）：
```python
        category_id: Optional[uuid.UUID] = None,
        department_id: Optional[uuid.UUID] = None,   # ← 新增
        current_user_id: Optional[uuid.UUID] = None,
```

**透传修改**（~L693-694，将 `department_id` 追加到 CRUD 调用）：
```python
        experts, total = await crud.get_experts_multi_and_total(
            self.db, skip, size, name, is_featured, is_active, is_verified, hospital, sort,
            category_id, department_id   # ← 新增（注意去掉原有的末尾闭括号换行）
        )
```

#### 4c. API 层

**文件**: `app/api/v1/endpoints/experts.py`
**位置**: `get_experts_list` 函数（admin router）

**Query 参数新增**（~L465，在 `category_id` 之后，`current_user` 之前）：
```python
    category_id: Optional[str] = Query(default=None, description="按专家主专业分类ID筛选（experts.category_id）"),
    department_id: Optional[str] = Query(default=None, description="按标准科室ID筛选（experts.department_id）"),
    current_user: dict = Depends(get_current_user),
```

**UUID 校验**（~L488，在 `category_id` 校验块之后，`user_id_for_logging` 之前）：
```python
    # 校验 department_id 为合法 UUID
    department_uuid: Optional[uuid.UUID] = None
    if department_id:
        try:
            department_uuid = uuid.UUID(department_id)
        except (ValueError, TypeError):
            return JSONResponse(
                status_code=400,
                content=error_response(code=4001, message="无效的科室ID格式")
            )
```

**透传至 Service**（~L513，在 `category_id=category_uuid` 之后）：
```python
            category_id=category_uuid,
            department_id=department_uuid,
            current_user_id=user_id,
```

---

## 6. 完整性检查清单 (Completeness Checklist)

实施完成后，必须逐项确认以下检查点：

### Phase 1 — 科室详情端点
- [ ] `GET /admin/expert-departments/{department_id}` 函数在 `batch_verify_departments` **之后**注册
- [ ] 函数签名使用 `uuid.UUID = Path(...)`，不是 `str`
- [ ] 不存在时返回 404 + `code=2001`
- [ ] `expert_count` 通过子查询填充，不在 Schema 中定义默认值绕过
- [ ] 响应使用 `ExpertDepartmentItem.model_validate(dept)`，不调用 `.model_dump()`
- [ ] 异常分 403 / 500 两个分支

### Phase 2 — unmapped 增强
- [ ] 响应 items 含 9 个字段（id, name, title, hospital, avatar_url, category_id, category_name, expertise_areas, is_active, is_verified）
- [ ] `category_name` 使用 `e.category.name if e.category else None`
- [ ] CRUD 层 `get_unmapped_experts` 加了 `joinedload(Expert.category)`
- [ ] `expertise_areas` 使用 `e.expertise_areas or []` 防止 None

### Phase 3 — 统计端点
- [ ] `check_admin_permission` 已在 `content_management.py` 顶部导入
- [ ] 端点位置在 `categories_stats` 之后、`get_category_by_id` 之前
- [ ] 使用 `sa_select` 别名避免与文件内已有 `select` 对象冲突
- [ ] 分类无科室时 `department_count=0, expert_count=0`（不是 missing key）
- [ ] `stats` 数组长度为 25（或当前活跃分类总数）
- [ ] `total_departments` 仅计 `is_active=True` 的科室

### Phase 4 — department_id 筛选
- [ ] CRUD 层 `get_experts_multi_and_total` 签名新增 `department_id: Optional[uuid.UUID] = None`
- [ ] CRUD 层条件区新增 `if department_id is not None: conditions.append(Expert.department_id == department_id)`
- [ ] Service 层 `get_experts_list` 签名新增 `department_id` 并透传到 CRUD 调用
- [ ] API 层 `get_experts_list` 新增 `department_id: Optional[str] = Query(...)`
- [ ] API 层新增 UUID 格式校验（与 `category_id` 校验模式一致）
- [ ] API 层透传 `department_uuid` 到 Service 调用
- [ ] `category_id` 和 `department_id` 可同时传参（AND 交集）

### 全局检查
- [ ] 所有新端点均使用 `check_admin_permission(role)`（非 `service._check_admin_permission`）
- [ ] 所有端点均在 `try` 前提取了 `user_id` 和 `role` 到局部变量
- [ ] 所有异常处理分 PermissionDeniedException / Exception 两个分支
- [ ] 所有成功响应使用 `success_response(data=...)`
- [ ] 所有错误响应使用 `JSONResponse(status_code=XXX, content=error_response(...))`
- [ ] 所有 lazy import 使用 `from app.crud import xxx as crud_xxx` 模式
- [ ] 不修改 `app/api/v1/api.py`

### 路由冲突检测
- [ ] 启动服务后 `curl -H "Authorization: Bearer <admin_token>" http://localhost:8000/api/v1/admin/expert-departments/unmapped` 返回 unmapped 列表（不是 500）
- [ ] 启动服务后 `curl -H "Authorization: Bearer <admin_token>" http://localhost:8000/api/v1/admin/expert-departments/<valid_uuid>` 返回 200
- [ ] 启动服务后 `curl -H "Authorization: Bearer <admin_token>" http://localhost:8000/api/v1/admin/expert-departments/<invalid_uuid>` 返回 404

---

## 7. 实施记录

| Phase | 文件 | 改动行数 | 验证状态 |
|:--:|------|:--:|:--:|
| P1 | `endpoints/expert_departments.py` | +45 | 待验证 |
| P2 | `endpoints/expert_departments.py` | ~10（替换） | 待验证 |
| P2 | `crud/expert_departments.py` | +1 | 待验证 |
| P3 | `endpoints/content_management.py` | +80 +1（导入） | 待验证 |
| P4 | `crud/experts.py` | +3 | 待验证 |
| P4 | `services/expert_service.py` | +3 | 待验证 |
| P4 | `endpoints/experts.py` | +15 | 待验证 |
| **合计** | **6 文件** | **~158** | |

---

## 附录 A：与已有端点文件的集成位置速查

```
expert_departments.py 文件结构（修改后）:
  L28:  GET  /expert-departments              (已有, 列表)
  L67:  POST /expert-departments              (已有, 创建)
  L99:  PATCH /expert-departments/{id}        (已有, 更新)
  L128: DELETE /expert-departments/{id}       (已有, 软删除)
  L153: GET  /expert-departments/unmapped     (已有, Phase 2 修改响应字段)
  L181: POST /expert-departments/merge        (已有)
  L208: PATCH /expert-departments/{id}/category (已有)
  L235: POST /expert-departments/batch-verify (已有)
  L275: GET  /expert-departments/{id}         (← P1 新增, 必须在最后)

content_management.py 文件结构（修改后）:
  L17:  from app.core.permissions import check_admin_permission  (← P3 新增导入)
  L500: GET  /categories/stats                (已有)
  L529: GET  /categories/department-stats     (← P3 新增)
  L535: GET  /categories/{category_id}        (已有)
```

## 附录 B：设计文档引用索引

完整的设计说明、前后端接口对照表、权限矩阵、测试计划见：

`app修改记录/专家分类管理_App端接口优化设计文档.md`

| 设计文档章节 | 对应本提示词 |
|------------|------------|
| §4.1 科室详情端点 | Phase 1 |
| §4.2 unmapped 增强 | Phase 2 |
| §4.3 分类维度统计 | Phase 3 |
| §4.4 department_id 筛选 | Phase 4 |
| §6 权限与安全性 | §4.1、§4.3 |
| §7 实施计划 | §7 实施记录 |
| §8 前后端接口对照 | 附录 A |
