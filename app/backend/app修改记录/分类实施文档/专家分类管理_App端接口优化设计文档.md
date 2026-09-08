# 专家分类管理 — App 端接口优化设计文档

> **版本**: V1.1
> **创建日期**: 2026-07-24
> **最后更新**: 2026-07-27（冗余审查后删除 Phase 3）
> **关联文档**:
> - [分类系统现状分析与A2方案设计.md](./分类系统现状分析与A2方案设计.md)（科室词表体系背景）
> - [融合方案最终设计_A2+C.md](./融合方案最终设计_A2+C.md)（department 受控词表融合方案）
> - [融合方案P3_Service与API_代码生成提示词.md](./融合方案P3_Service与API_代码生成提示词.md)（expert_departments 端点实施参考）
> - [管理端后台数据面板_AdminStats设计文档.md](./管理端后台数据面板_AdminStats设计文档.md)（Admin 端点设计规范参考）
> - [API路由规范统一方案.md](./API路由规范统一方案.md)（Router 命名与注册规范）
> - `../docs/03_系统设计/直播核心功能设计文档_v6_专家模块设计文档-专家信息-专家关注-统一版.md`（专家模块设计基础）
> - `../docs/03_系统设计/直播核心功能设计文档_v6_内容管理模块设计文档-标签-分类-场次标签关联-合并版-含搜索与科室图片.md`（分类模块设计基础）
> **状态**: ~~🟡 设计完成，待实施~~ → **已实施后经冗余审查，Phase 3（department-stats）删除，Phase 1/2/4 保留**

> **⚠️ 冗余审查结论（2026-07-27）**：本文档 Phase 3 设计的 `GET /admin/categories/department-stats` 端点经前后端联合审查确认为**零前端调用**。该端点做了 3 表 JOIN + CASE WHEN 聚合（~100 行），但前端可通过已有 `GET /content/categories?include_counts=true` + `GET /admin/expert-departments?category_id=X`（共 25 个固定量级分类）组合实现。已从 `content_management.py` 中删除该端点及 `check_admin_permission` 导入。Phase 1/2/4 保留。

---

## 目录

1. [需求概述](#一需求概述)
2. [现状分析](#二现状分析)
3. [方案设计](#三方案设计)
4. [新增/修改端点详细设计](#四新增修改端点详细设计)
    - [4.1 GET /admin/expert-departments/{id} — 科室详情](#41-get-adminexpert-departmentsdepartment_id--科室详情)
    - [4.2 GET /admin/expert-departments/unmapped — 增强返回字段](#42-get-adminexpert-departmentsunmapped--增强返回字段)
    - [4.3 GET /admin/categories/department-stats — 分类维度统计](#43-get-admincategoriesdepartment-stats--分类维度统计)
    - [4.4 GET /admin/experts — 新增 department_id 筛选](#44-get-adminexperts--新增-department_id-筛选)
5. [响应 Schema 设计](#五响应-schema-设计)
6. [权限与安全性](#六权限与安全性)
7. [实施计划](#七实施计划)
8. [前后端接口对照](#八前后端接口对照)

---

## 一、需求概述

### 1.1 背景

前端 App 端需要新增「专家分类管理」页面（`/pages/app/admin/departments/index`），用于管理员对科室词表（`expert_departments`）进行审核、编辑、合并、删除等运营操作，同时监控未分配科室的"孤儿"专家。

当前已有以下后端端点覆盖了大部分科室管理需求：

| 已有端点 | 支持的功能 |
|---------|-----------|
| `GET /admin/expert-departments` | 分页列表，支持 is_verified / category_id / q 筛选，含 expert_count |
| `POST /admin/expert-departments` | 创建科室 |
| `PATCH /admin/expert-departments/{id}` | 部分更新科室 |
| `DELETE /admin/expert-departments/{id}` | 软删除科室 |
| `POST /admin/expert-departments/merge` | 合并科室 + 专家迁移 + 同义词自学习 |
| `PATCH /admin/expert-departments/{id}/category` | 修改科室分类 + 批量同步专家 category_id |
| `POST /admin/expert-departments/batch-verify` | 批量审核（通过/驳回），最多 200 条 |
| `GET /admin/expert-departments/unmapped` | 查询未分配科室的专家（仅返回 id + name） |
| `PATCH /admin/experts/{id}` | 更新专家（含 department_id，可复用为"分配科室"） |

### 1.2 本次修改目标

| # | 目标 | 类型 | 当前状态 |
|---|------|:--:|:--:|
| 1 | 新增 `GET /admin/expert-departments/{id}` 科室详情端点 | **新端点** | ✅ 保留 |
| 2 | 增强 `GET /admin/expert-departments/unmapped` 返回完整专家字段 | 现有端点扩展 | ✅ 保留 |
| 3 | ~~新增 `GET /admin/categories/department-stats` 按分类返回科室数+专家数~~ | ~~**新端点**~~ | **❌ 已删除**（零前端调用，可用已有接口组合替代） |
| 4 | `GET /admin/experts` 新增 `department_id` 筛选参数 | 现有端点扩展 | ✅ 保留 |

### 1.3 非目标

以下功能不在本次范围内：

- 专家 CRUD（`POST/PATCH/DELETE /admin/experts`）—— 属于"专家管理"页面
- 批量导入专家（`POST /admin/experts/batch-import`）—— 属于"专家管理"页面
- 创建/编辑/删除根分类（`categories` 表）—— 系统级配置，适合桌面后台
- 直播间-分类关联管理 —— 属于"直播间管理"页面
- 专题分类管理 —— 属于"内容/专题管理"页面

### 1.4 数据关系

```
categories (25 个根分类)  ← 平台级分类架构，相对稳定
    ↑ FK RESTRICT
expert_departments (158+ 个标准科室)  ← 可运营的词表，需审核/合并/纠错
    ↑ FK SET NULL
experts (专家)  ← 被分类的对象，按科室维度管理
```

---

## 二、现状分析

### 2.1 已有端点覆盖情况

经过对 `app/api/v1/endpoints/expert_departments.py`、`app/api/v1/endpoints/experts.py`、`app/crud/expert_departments.py`、`app/crud/experts.py` 的逐接口排查，18 项前端需求中 **12 项已就绪，4 项有缺口，2 项无需后端改动**。

### 2.2 四个缺口

| # | 缺口 | 影响的前端功能 | 根因 |
|---|------|--------------|------|
| 1 | 无单条科室详情端点 | 科室详情子页无法展示 | `expert_departments.py` 只有 LIST/POST/PATCH/DELETE/MERGE，缺 GET one |
| 2 | unmapped 端点仅返回 `id + name` | 未分配专家列表信息不全（缺 title、hospital、category_id） | endpoint 响应构造时只提取了 id 和 name，而 CRUD 层实际加载了完整 Expert 对象 |
| 3 | 无按分类的科室数统计 | Tab 1「分类总览」无法展示"科室 N 个" | `GET /content/categories?include_counts=true` 只有 expert_count + room_count，`GET /admin/categories/stats` 只有全局汇总 |
| 4 | Admin 专家列表无 `department_id` 筛参 | 科室详情页"查看更多专家 →" 无法按科室筛选跳转 | `get_experts_multi_and_total` 仅支持 `category_id`，不支持 `department_id` |

### 2.3 关键代码位置

| 缺口 | 涉及文件 | 关键行号 |
|------|---------|:--:|
| 1 — 缺详情端点 | `app/api/v1/endpoints/expert_departments.py` | 全文 258 行，无 GET /{id} |
| 2 — unmapped 字段不全 | `app/api/v1/endpoints/expert_departments.py` | L169: `{"id": str(e.id), "name": e.name}` |
| 3 — 无 per-category stats | `app/crud/content_management.py` | L387-428: `get_categories_stats` 仅全局汇总 |
| 4 — 无 dept_id 筛选 | `app/crud/experts.py` | L305-354: `get_experts_multi_and_total` 无 department_id 参数 |
| 4 — 无 dept_id 筛选 | `app/api/v1/endpoints/experts.py` | L454-499: admin experts list 无 department_id query param |

---

## 三、方案设计

### 3.1 架构原则

```
前端 App (uni-app)                    后端 (FastAPI)
─────────────────                     ──────────────
Tab 1 分类总览                        GET /content/categories?include_counts=true  ← 已有
  点击 → 下钻科室列表                    GET /admin/expert-departments?category_id=X  ← 已有

Tab 2 科室审核                         GET /admin/expert-departments?is_verified=X  ← 已有
  单条/批量审核                         PATCH /{id} + POST /batch-verify  ← 已有
  编辑/合并/删除                        PATCH/POST/DELETE  ← 已有

Tab 3 未分配专家                       GET /admin/expert-departments/unmapped  ← 增强
  分配科室                             PATCH /admin/experts/{id}  ← 已有（复用）

科室详情子页                           GET /admin/expert-departments/{id}  ← 新增
  查看关联专家 →                        GET /admin/experts?department_id=X  ← 新增参数
```

> **2026-07-27 更新**：移除了原先设计的 `GET /admin/categories/department-stats`，该端点经冗余审查确认为零前端调用。Tab 1 的每分类科室数/专家数可通过已有 `GET /content/categories?include_counts=true` + `GET /admin/expert-departments?category_id=X` 组合取得。~~删除线~~

**决策理由**：
- 新增端点均为纯增量，不修改现有 API 签名，不破坏已有前端调用
- Tab 1 拆分为两接口（`GET /content/categories` + `GET /admin/categories/department-stats`），避免在公开接口中夹带管理端特有数据
- 科室详情端点不内嵌专家列表（避免响应膨胀），专家列表通过独立的 `GET /admin/experts?department_id=X` 分页获取

### 3.2 技术栈与架构约定

```
Python 3.9+ | SQLAlchemy 2.0 (async) | FastAPI | Pydantic v2
权限模式: get_current_user → current_user (dict) → user_id (UUID) + role (str)
Admin API: 使用 get_current_user（必须登录），check_admin_permission(role) 守卫
JWT 提取: user_id = uuid.UUID(current_user["user_id"]) / role = current_user.get("role")
分层职责: API 层（鉴权+参数校验） → Service 层（业务逻辑） → CRUD 层（数据库操作）
```

### 3.3 与现有体系的关系

所有新端点均使用 `app/core/permissions.py` 中的统一守卫函数 `check_admin_permission(role)`，与已完成的权限体系优化保持一致。不引入新的权限检查模式。

---

## 四、新增/修改端点详细设计

### 4.1 `GET /admin/expert-departments/{department_id}` — 科室详情

**改动类型**: **新端点**
**权限**: 仅 ADMIN/SUPERADMIN

#### 端点定义

```
GET /api/v1/admin/expert-departments/{department_id}
```

**路径参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|:--:|------|
| `department_id` | UUID | 是 | 科室 ID |

**响应体**:

```jsonc
{
  "code": 200,
  "message": "success",
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "乳腺外科",
    "category_id": "550e8400-e29b-41d4-a716-446655440001",
    "category_name": "普通外科",
    "synonyms": ["乳腺科", "乳房外科", "甲乳科"],
    "is_active": true,
    "is_verified": true,
    "source": "auto_match",
    "created_by": null,
    "expert_count": 8,
    "created_at": "2026-07-15T14:30:00Z",
    "updated_at": "2026-07-22T09:15:00Z"
  },
  "timestamp": "2026-07-24T10:00:00Z"
}
```

**错误码**:

| HTTP 状态码 | code | message | 触发条件 |
|:---:|:---:|------|------|
| 403 | 3003 | 权限不足：需要管理员权限 | role 非 ADMIN/SUPERADMIN |
| 404 | 2001 | 科室不存在 | department_id 在数据库中不存在 |
| 500 | 1002 | 数据库操作错误 | DB 异常 |

#### 实现要点

1. **CRUD 层复用**：`get_department_by_id(db, department_id)` 已存在于 `crud/expert_departments.py:116-131`
2. **expert_count 填充**：查询 `SELECT COUNT(*) FROM experts WHERE department_id = :id` 后附加到响应
3. **category_name 填充**：利用 ExpertDepartment 模型已有的 `category` relationship（lazy="select"），SQLAlchemy 会自动 JOIN 加载
4. **不使用 Service 层**：该端点逻辑简单（查询 + 填充计数），直接在 endpoint 层调用 CRUD，保持轻量
5. **⚠️ 路由注册顺序**：此端点必须放在 `GET /unmapped`（L153）**之后**注册，否则 FastAPI 会把 `/unmapped` 误解析为 `{department_id}` 并尝试 "unmapped" 做 UUID 转换而报错

#### 代码实现

```python
# app/api/v1/endpoints/expert_departments.py — 新增端点

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

        dept = await crud_dept.get_department_by_id(db, department_id)
        if dept is None:
            return JSONResponse(
                status_code=404,
                content=error_response(code=2001, message="科室不存在"),
            )

        # 填充 expert_count 和 category_name
        from app.models.experts import Expert
        from sqlalchemy import select, func
        count_q = select(func.count(Expert.id)).where(
            Expert.department_id == department_id
        )
        count_res = await db.execute(count_q)
        dept.expert_count = count_res.scalar() or 0

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

#### 改动文件

| 文件 | 内容 | 预估行数 |
|------|------|:--:|
| `app/api/v1/endpoints/expert_departments.py` | 新增 GET /{id} 端点 | +35 |

---

### 4.2 `GET /admin/expert-departments/unmapped` — 增强返回字段

**改动类型**: **现有端点扩展**
**权限**: 仅 ADMIN/SUPERADMIN（不变）

#### 端点定义（不变）

```
GET /api/v1/admin/expert-departments/unmapped?page=1&size=50
```

#### 变更内容

**现有响应（仅 2 字段）**：

```jsonc
"items": [{"id": "uuid", "name": "张医生"}]
```

**增强后响应**：

```jsonc
{
  "code": 200,
  "message": "success",
  "data": {
    "items": [
      {
        "id": "550e8400-...",
        "name": "张医生",
        "title": "主任医师",
        "hospital": "中山大学附属第一医院",
        "avatar_url": "https://cdn.example.com/avatars/xxx.jpg",
        "category_id": "550e8400-...",
        "category_name": "普通外科",
        "expertise_areas": ["乳腺肿瘤", "甲状腺疾病"],
        "is_active": true,
        "is_verified": true
      }
    ],
    "total": 12,
    "page": 1,
    "size": 50
  },
  "timestamp": "2026-07-24T10:00:00Z"
}
```

#### 实现要点

1. **CRUD 层无需改动**：`get_unmapped_experts(db, page, size)`（`crud/expert_departments.py:267-300`）已返回完整 `Expert` 对象（含 `title`、`hospital`、`category_id`、`avatar_url` 等）
2. **仅改 endpoint 层的数据提取**：将 `[{"id": str(e.id), "name": e.name}]` 扩展为包含更多字段
3. **category_name 填充**：预加载 `Expert.category` relationship 后提取 `.name`
4. **无性能影响**：不增加额外 DB 查询，仅多提取几个已有字段
5. **`is_verified` 字段**：Expert 模型已确认有此字段（`models/experts.py:71`，AdminStats 设计已实施），无需安全回退

#### 代码修改

```python
# app/api/v1/endpoints/expert_departments.py L168-173 — 替换 items 构造

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

#### 补充：CRUD 层预加载 category

当前 `get_unmapped_experts` 中的 `select(Expert)` 未预加载 `category` relationship，需补充：

```python
# app/crud/expert_departments.py L285 — 增加预加载
query = (
    select(Expert)
    .options(joinedload(Expert.category))    # ← 新增
    .where(Expert.department_id == None)
)
```

#### 改动文件

| 文件 | 内容 | 预估行数 |
|------|------|:--:|
| `app/api/v1/endpoints/expert_departments.py` | L168-173 扩展 items 字段 | ~10（替换） |
| `app/crud/expert_departments.py` | L285 增加 joinedload(Expert.category) | +1 |

---

### 4.3 `GET /admin/categories/department-stats` — ~~分类维度统计~~（已删除）

> **❌ 2026-07-27 冗余审查删除**：该端点经前后端联合审查，确认零前端调用。前端可通过 `GET /content/categories?include_counts=true` + `GET /admin/expert-departments?category_id=X`（25 个固定量级分类）组合获得相同数据。以下为原始设计，仅供归档参考。

**改动类型**: **新端点**
**权限**: 仅 ADMIN/SUPERADMIN

#### 端点定义

```
GET /api/v1/admin/categories/department-stats
```

**响应体**:

```jsonc
{
  "code": 200,
  "message": "success",
  "data": {
    "stats": [
      {
        "category_id": "550e8400-...",
        "category_name": "普通外科",
        "department_count": 15,
        "expert_count": 42,
        "verified_department_count": 12,
        "unverified_department_count": 3
      },
      {
        "category_id": "550e8400-...",
        "category_name": "骨科",
        "department_count": 12,
        "expert_count": 35,
        "verified_department_count": 10,
        "unverified_department_count": 2
      }
    ],
    "summary": {
      "total_categories": 25,
      "total_departments": 158,
      "total_unmapped_experts": 12
    }
  },
  "timestamp": "2026-07-24T10:00:00Z"
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `category_id` | UUID | 分类 ID |
| `category_name` | str | 分类名称 |
| `department_count` | int | 该分类下 `is_active=True` 的科室数 |
| `expert_count` | int | 该分类下所有科室关联的专家数（通过 `expert_departments.category_id` 统计，不含 unmapped） |
| `verified_department_count` | int | 该分类下已审核的科室数 |
| `unverified_department_count` | int | 该分类下待审核的科室数 |
| `summary.total_unmapped_experts` | int | 全局未分配科室的专家总数（含 is_active=False 的软删除专家，与 unmapped 列表保持一致） |

> **expert_count 语义说明**：统计路径为 `categories.id → expert_departments.category_id → experts.department_id`，即通过科室中间表统计。不包含 `department_id=NULL` 的 unmapped 专家（他们虽有 category_id，但不属于任何科室）。这与 Tab 1 "分类总览"的定位一致——按科室层级展示分类体系，而不是按专家直连分类。
>
> **summary.total_departments 语义说明**：仅统计 `is_active=True` 的科室数（主查询 WHERE 条件有 `ExpertDepartment.is_active == True`），软删除的科室不计入。

#### 实现要点

1. **SQL 聚合查询**：使用 `GROUP BY ExpertDepartment.category_id` 获得 per-category 的科室数 + 专家数
2. **一次查询完成**：避免 N+1（25 个分类只需 1 次聚合查询 + 1 次 unmapped 计数查询 + 1 次 all_cats 名称查询）
3. **不新建 Service 层**：逻辑简单（纯统计），直接在 endpoint 层完成
4. **权限检查**：本端点不走 `ContentManagementService._check_admin_permission`（私有方法），需在文件顶部显式 `from app.core.permissions import check_admin_permission`

#### 代码实现

```python
# app/api/v1/endpoints/content_management.py — 新增端点

@content_admin_router.get("/categories/department-stats")
async def get_department_stats_by_category(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """管理员获取按分类维度的科室与专家统计"""
    role = current_user.get("role")

    try:
        check_admin_permission(role)

        # 按分类聚合：科室数 + 专家数（通过 ExpertDepartment 关联）
        from sqlalchemy import select, func, case
        from app.models.expert_departments import ExpertDepartment
        from app.models.experts import Expert
        from app.models.content_management import Category

        # 子查询：每个科室的专家数
        expert_subq = (
            select(
                Expert.department_id,
                func.count(Expert.id).label("expert_cnt"),
            )
            .where(Expert.department_id.isnot(None))
            .group_by(Expert.department_id)
        ).subquery()

        # 主查询：按 category_id 分组
        stats_q = (
            select(
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

        # 补充所有 25 个根分类（含科室数为 0 的分类）
        all_cats_q = select(Category.id, Category.name).where(
            Category.is_active == True,
        ).order_by(Category.sort_order.asc())
        all_cats_res = await db.execute(all_cats_q)
        all_cats = all_cats_res.fetchall()

        stats_by_cat = {}
        for row in stats_rows:
            stats_by_cat[row[0]] = {
                "department_count": row[1],
                "expert_count": row[2],
                "verified_department_count": row[3],
                "unverified_department_count": row[4],
            }

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
        unmapped_q = select(func.count(Expert.id)).where(
            Expert.department_id == None,
        )
        unmapped_res = await db.execute(unmapped_q)
        unmapped_total = unmapped_res.scalar() or 0

        return success_response(data={
            "stats": per_category,
            "summary": {
                "total_categories": len(all_cats),
                "total_departments": sum(s.get("department_count", 0) for s in per_category),
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

#### 改动文件

| 文件 | 内容 | 预估行数 |
|------|------|:--:|
| `app/api/v1/endpoints/content_management.py` | 新增 `/categories/department-stats` 端点 | +80 |

---

### 4.4 `GET /admin/experts` — 新增 `department_id` 筛选

**改动类型**: **现有端点扩展**
**权限**: 仅 ADMIN/SUPERADMIN（不变）

#### 端点定义（不变）

```
GET /api/v1/admin/experts?page=1&size=10&department_id=xxx
```

**新增查询参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|:--:|------|
| `department_id` | str (UUID) | 否 | 按科室 ID 精确筛选。与现有 `category_id` 正交——可同时传两个参数取交集 |

#### 改动范围

需在三层逐级透传 `department_id` 参数：

| 层级 | 文件 | 改动点 |
|:--:|------|------|
| API | `app/api/v1/endpoints/experts.py` L454-500 | `get_experts_list` 新增 `department_id: Optional[str] = Query(default=None)` 参数，校验 UUID 格式后传入 Service |
| Service | `app/services/expert_service.py` L651-700 | `get_experts_list` 方法签名新增 `department_id: Optional[uuid.UUID] = None`，透传至 CRUD |
| CRUD | `app/crud/experts.py` L305-354 | `get_experts_multi_and_total` 新增 `department_id` 参数，追加 `Expert.department_id == department_id` 条件 |

#### 代码修改

**CRUD 层** — `app/crud/experts.py`:

```python
# L305-315: 函数签名新增 department_id
async def get_experts_multi_and_total(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 10,
    name: Optional[str] = None,
    is_featured: Optional[bool] = None,
    is_active: Optional[bool] = None,
    is_verified: Optional[bool] = None,
    hospital: Optional[str] = None,
    sort: Optional[str] = None,
    category_id: Optional[uuid.UUID] = None,
    department_id: Optional[uuid.UUID] = None,  # ← 新增
) -> Tuple[List[Expert], int]:

# L340-354: 条件区新增
    if category_id is not None:
        conditions.append(Expert.category_id == category_id)
    if department_id is not None:                                 # ← 新增
        conditions.append(Expert.department_id == department_id)  # ← 新增
```

**Service 层** — `app/services/expert_service.py`:

```python
# L651-664: get_experts_list 签名新增 department_id
async def get_experts_list(
    self,
    page: int = 1,
    size: int = 10,
    name: Optional[str] = None,
    is_featured: Optional[bool] = None,
    is_active: Optional[bool] = None,
    is_verified: Optional[bool] = None,
    hospital: Optional[str] = None,
    sort: Optional[str] = None,
    category_id: Optional[uuid.UUID] = None,
    department_id: Optional[uuid.UUID] = None,  # ← 新增
    current_user_id: Optional[uuid.UUID] = None,
    role: Optional[str] = None,
) -> Dict[str, Any]:

# L693: CRUD 调用透传
    experts, total = await crud.get_experts_multi_and_total(
        self.db, skip, size, name, is_featured, is_active, is_verified, hospital, sort,
        category_id, department_id  # ← 新增
    )
```

**API 层** — `app/api/v1/endpoints/experts.py`:

```python
# L454-466: get_experts_list 新增 department_id 参数
@experts_admin_router.get("/experts")
async def get_experts_list(
    request: Request,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=10, ge=1, le=100),
    name: Optional[str] = Query(default=None),
    is_featured: Optional[bool] = Query(default=None),
    is_active: Optional[bool] = Query(default=None),
    is_verified: Optional[bool] = Query(default=None),
    hospital: Optional[str] = Query(default=None),
    sort: Optional[str] = Query(default=None),
    category_id: Optional[str] = Query(default=None),
    department_id: Optional[str] = Query(default=None),  # ← 新增
    ...
):

# L476-485: UUID 校验（在 category_id 校验之后追加）
    department_uuid: Optional[uuid.UUID] = None
    if department_id:
        try:
            department_uuid = uuid.UUID(department_id)
        except (ValueError, TypeError):
            return JSONResponse(
                status_code=400,
                content=error_response(code=4001, message="无效的科室ID格式"),
            )

# L491-499: Service 调用透传（在 category_id 参数之后追加）
    result = await service.get_experts_list(
        ...
        category_id=category_uuid,
        department_id=department_uuid,  # ← 新增
        ...
    )
```

#### 改动文件

| 文件 | 内容 | 预估行数 |
|------|------|:--:|
| `app/crud/experts.py` | `get_experts_multi_and_total` 签名 + 条件 | +3 |
| `app/services/expert_service.py` | `get_experts_list` 签名 + 透传 | +3 |
| `app/api/v1/endpoints/experts.py` | `get_experts_list` query param + UUID 校验 + 透传 | +15 |

---

## 五、响应 Schema 设计

### 5.1 现有 Schema 复用

本方案所有端点的响应均复用已有 Schema：

| Schema | 来源文件 | 使用端点 |
|--------|---------|---------|
| `ExpertDepartmentItem` | `app/schemas/expert_departments.py:28-43` | `GET /admin/expert-departments/{id}` |
| `ExpertDepartmentListResponse` | `app/schemas/expert_departments.py:62-66` | 科室列表（不变） |

### 5.2 新增 Schema（如有需要）

`GET /admin/categories/department-stats` 的响应结构较为简单，建议**不新建独立 Schema 文件**，直接在 endpoint 中构造 dict 返回（与 `batch-verify`、`merge` 端点风格一致）。

如需 schema 化，可定义在 `app/schemas/content_management.py`：

```python
# app/schemas/content_management.py — 新增

class CategoryDeptStatItem(BaseModel):
    category_id: uuid.UUID
    category_name: str
    department_count: int = 0
    expert_count: int = 0
    verified_department_count: int = 0
    unverified_department_count: int = 0


class CategoryDeptStatsResponse(BaseModel):
    stats: list[CategoryDeptStatItem]
    summary: dict  # {"total_categories": 25, "total_departments": 158, "total_unmapped_experts": 12}
```

> **决定**：采用 endpoint 层 dict 返回（与现有 `expert_departments.py` 风格一致），不新增 Schema 文件。如后续需要类型安全可再追加。

---

## 六、权限与安全性

### 6.1 端点权限矩阵

| 端点 | 权限 | 检查位置 | 方式 |
|------|------|------|------|
| `GET /admin/expert-departments/{id}` | 仅 ADMIN/SUPERADMIN | Endpoint 层 | `check_admin_permission(role)` |
| `GET /admin/expert-departments/unmapped` | 仅 ADMIN/SUPERADMIN | Endpoint 层 | `check_admin_permission(role)`（已有，不变） |
| `GET /admin/categories/department-stats` | 仅 ADMIN/SUPERADMIN | Endpoint 层 | `check_admin_permission(role)` |
| `GET /admin/experts?department_id=` | 仅 ADMIN/SUPERADMIN | Service 层 | `check_admin_permission(role)`（已有，不变） |

### 6.2 信息泄露防护

- 所有新端点均部署在 `/admin/` 前缀下，非管理员用户通过 `get_current_user` + `check_admin_permission` 被 403 拦截
- 科室详情端点不返回 `created_by` 用户的敏感信息（仅 UUID）
- 统计端点不暴露单个专家的个人数据

### 6.3 与现有权限体系的一致性

所有新端点均使用 `app/core/permissions.py` 中的 `check_admin_permission(role)`，与已完成的权限体系优化（P1-2 守卫函数统一化）保持一致。不引入新的权限检查模式。

---

## 七、实施计划

### 7.1 阶段划分

| 阶段 | 内容 | 预估工时 | 依赖 |
|:--:|------|:--:|------|
| **Phase 1** | `GET /admin/expert-departments/{id}` 科室详情端点 | 0.5h | 无 |
| **Phase 2** | `GET /admin/expert-departments/unmapped` 增强返回字段 | 0.5h | 无 |
| **Phase 3** | `GET /admin/categories/department-stats` 统计端点 | 1.5h | 无 |
| **Phase 4** | `GET /admin/experts` 新增 `department_id` 筛选 | 1h | 无 |
| **总计** | | **3.5h** | |

### 7.2 文件改动总览

> **2026-07-27 更新**：~~删除线~~ 标记的是已删除项。

| 文件 | Phase | 类型 | 预估行数 | 当前状态 |
|------|:--:|:--:|:--:|:--:|
| `app/api/v1/endpoints/expert_departments.py` | 1, 2 | 新增端点 + 修改响应 | +45 | **保留** |
| `app/crud/expert_departments.py` | 2 | 增加 joinedload | +1 | **保留** |
| ~~`app/api/v1/endpoints/content_management.py`~~ | ~~3~~ | ~~新增 stats 端点~~ | ~~+80~~ | **已删除** |
| `app/crud/experts.py` | 4 | 新增 department_id 参数 | +3 | **保留** |
| `app/services/expert_service.py` | 4 | 透传 department_id | +3 | **保留** |
| `app/api/v1/endpoints/experts.py` | 4 | 新增 query param + 校验 + 透传 | +15 | **保留** |
| **实际保留合计** | | | **~67 行** | |
| ~~删除合计~~ | | | ~~~81 行（1 行 import）~~ | |

### 7.3 不新增文件

本方案所有改动均在**已有文件**中进行（2 个新端点追加在已有 endpoint 文件中），无需新建文件，无需修改 `app/api/v1/api.py` 路由注册。

### 7.4 测试建议

| 测试类型 | 覆盖范围 |
|------|------|
| 单元测试 | 可暂不新增（逻辑内聚在 endpoint 层，DB 依赖重） |
| 集成测试 | `GET /admin/expert-departments/{id}` — 正常 / 不存在 / 非管理员 |
| 集成测试 | `GET /admin/expert-departments/unmapped` — 字段完整性校验 |
| 集成测试 | `GET /admin/categories/department-stats` — 统计数字与手动查询一致 |
| 集成测试 | `GET /admin/experts?department_id=X&category_id=Y` — 交集筛选正确 |
| 权限测试 | REGULAR 用户调用所有新/改端点 → 403 |

### 7.5 实施顺序建议

```
Phase 1 (科室详情) ── 可并行 ── Phase 3 (分类统计)
       │                              │
       └──── 合流 ──── Phase 2 (unmapped增强) ──── Phase 4 (department_id筛选)
```

Phase 1 和 Phase 3 无依赖，可并行实施。Phase 2 和 Phase 4 改动量小，可穿插完成。

**⚠️ 实施注意事项**：

1. **路由注册顺序（Phase 1）**：`GET /admin/expert-departments/{department_id}` 必须放在 `GET /unmapped` 之后注册，否则 `/unmapped` 会被 `/{department_id}` 先匹配导致 "unmapped" 尝试 UUID 解析报错。建议追加到文件末尾（L258 之后）。
2. **权限导入（Phase 3）**：`content_management.py` 顶部需新增 `from app.core.permissions import check_admin_permission`，该文件现有代码使用 `service._check_admin_permission(role)` 私有方法（不适用于不依赖 Service 的新端点）。

---

## 八、前后端接口对照

### 8.1 前端功能 → API 完整映射

| # | 前端功能 | 后端端点 | 状态 |
|---|---------|---------|:--:|
| 1 | Tab 1 分类总览（25卡片） | `GET /content/categories?include_counts=true` | 已有（~~原设计附加 `GET /admin/categories/department-stats`，已删除~~） |
| 2 | 按分类下钻科室列表 | `GET /admin/expert-departments?category_id=X` | 已有 |
| 3 | Tab 2 待审核科室列表 | `GET /admin/expert-departments?is_verified=false` | 已有 |
| 4 | 子筛选（待审核/已审核/全部） | `GET /admin/expert-departments?is_verified=X` | 已有 |
| 5 | 按分类筛选科室 | `GET /admin/expert-departments?category_id=X` | 已有 |
| 6 | 搜索科室 | `GET /admin/expert-departments?q=xxx` | 已有 |
| 7 | 单条审核通过 | `PATCH /admin/expert-departments/{id}` `{is_verified:true}` | 已有 |
| 8 | 批量审核 | `POST /admin/expert-departments/batch-verify` | 已有 |
| 9 | 编辑科室 | `PATCH /admin/expert-departments/{id}` | 已有 |
| 10 | 合并科室 | `POST /admin/expert-departments/merge` | 已有 |
| 11 | 删除科室 | `DELETE /admin/expert-departments/{id}` | 已有 |
| 12 | 新增科室 | `POST /admin/expert-departments` | 已有 |
| 13 | Tab 3 未分配专家列表 | `GET /admin/expert-departments/unmapped` | **增强** |
| 14 | 为专家分配科室 | `PATCH /admin/experts/{id}` `{department_id:xxx}` | 已有（复用） |
| 15 | 科室详情子页 | `GET /admin/expert-departments/{id}` | **新增** |
| 16 | 科室下关联专家列表 | `GET /admin/experts?department_id=X` | **新增参数** |
| 17 | 下拉刷新 | 重新请求当前列表 | 无后端改动 |
| 18 | 触底加载更多 | 分页 page/size | 已有 |

### 8.2 前端三 Tab 数据获取策略

| Tab | 首屏加载接口 | 分页/筛选接口 | 说明 |
|-----|------------|-------------|------|
| Tab 1 分类总览 | `GET /content/categories?include_counts=true` + `GET /admin/categories/department-stats` | 无分页（最多 25 条） | 两接口并行请求，前端合并数据 |
| Tab 2 科室审核 | `GET /admin/expert-departments?is_verified=false` | 同接口，改 is_verified / category_id / q 参数 | 默认显示待审核，子筛选切换参数即可 |
| Tab 3 未分配专家 | `GET /admin/expert-departments/unmapped` | page/size 分页 | 一页加载完 |
| 科室详情子页 | `GET /admin/expert-departments/{id}` | `GET /admin/experts?department_id=X`（关联专家） | 详情 + 专家列表两接口 |

### 8.3 科室状态-审核标识映射

| 后端字段 | 值 | 前端展示 | 说明 |
|---------|:--:|------|------|
| `is_verified` | `true` | ✅ 已审核 | 绿色标签 |
| `is_verified` | `false` | ⏳ 待审核 | 橙色标签 |
| `is_active` | `true` | 启用 | 正常展示 |
| `is_active` | `false` | 已禁用 | 灰色/半透明展示 |
| `source` | `auto_match` | 来源：自动匹配 | 详情页展示 |
| `source` | `admin_api` | 来源：管理员创建 | 详情页展示 |
| `source` | `csv_import` | 来源：CSV导入 | 详情页展示 |

---

## 附录 A：与已实施体系的兼容性声明

本方案所有新端点均遵循 `app/core/permissions.py` 的统一守卫函数体系，与以下已完成改造不冲突：

| 已实施项 | 状态 | 本方案影响 |
|---------|:--:|------|
| P1-2 守卫函数统一化 | ✅ 已实施 | 新端点使用 `check_admin_permission` |
| 融合方案 A2+C（expert_departments 受控词表） | ✅ 已实施 | 本方案在已有 CRUD 和端点基础上增量扩展 |
| AdminStats 设计 | ✅ 已实施 | 不冲突 —— 各自独立的端点组 |
| API 路由规范统一 | ✅ 已实施 | 新端点部署在已有 router 中（`expert_dept_admin_router`、`content_admin_router`），不新增 router |

## 附录 B：与前端 Tab 角标数据的关系

前端"我的"页卡片中已有的角标数据来自 `GET /admin/stats/daily`：

| 角标字段 | 数据来源（已有） | 与本次改动关系 |
|---------|----------------|-------------|
| `pending_departments` | `SELECT COUNT(*) FROM expert_departments WHERE is_verified=false` | 不变 —— 本方案不修改 stats/daily |
| `unmapped_experts` | `SELECT COUNT(*) FROM experts WHERE department_id IS NULL AND is_verified=true` | 不变 —— 本方案不修改 stats/daily |

> 本次新增的 `GET /admin/categories/department-stats` 中的 `summary.total_unmapped_experts` 与 stats/daily 的 `unmapped_experts` 语义不同（前者含所有 unmapped，后者仅含已审核的 unmapped），前端调用时注意区分。


---

## 涔濄€佸啑浣欏鏌ヨ褰曪紙2026-07-27锛?
### 9.1 瀹℃煡缁撹

鍥涗釜璁捐鐩爣涓紝Phase 3锛坄GET /admin/categories/department-stats`锛夌‘璁や负鍐椾綑锛屽凡鍒犻櫎銆傜悊鐢憋細

1. **闆跺墠绔皟鐢?*锛氬墠绔唬鐮佸叏閲忔悳绱㈢‘璁ゆ棤浠讳綍缁勪欢璋冪敤姝ょ鐐?2. **鍙敤宸叉湁鎺ュ彛鏇夸唬**锛氬墠绔?`GET /content/categories?include_counts=true` 宸茶繑鍥炴瘡鍒嗙被鐨?expert_count锛岀粍鍚?`GET /admin/expert-departments?category_id=X` 鍗冲彲鑾峰彇姣忓垎绫荤瀹ゆ暟锛堝浐瀹?25 涓垎绫伙紝闈?N+1 闂锛?3. **閬垮厤杩囧害璁捐**锛氳绔偣鍋氫簡 3 琛?JOIN + CASE WHEN + subquery 鑱氬悎锛垀100 琛岋級锛岀淮鎶ゆ垚鏈ぇ浜庢浛浠ｆ柟妗?
### 9.2 鍒犻櫎娓呭崟

| 鏂囦欢 | 鎿嶄綔 |
|------|------|
| `endpoints/content_management.py` L529-626 | 鍒犻櫎 `get_department_stats_by_category` 绔偣锛?8 琛岋級 |
| `endpoints/content_management.py` L17 | 鍒犻櫎 `check_admin_permission` 瀵煎叆锛? 琛岋紝浠呰绔偣浣跨敤锛?|

### 9.3 淇濈暀纭

| Phase | 鍐呭 | 淇濈暀鐞嗙敱 |
|:--:|------|------|
| 1 | `GET /admin/expert-departments/{id}` 绉戝璇︽儏绔偣 | 鎺ュ彛缂哄彛锛圠IST 鏈?GET one 娌℃湁锛夛紝35 琛岋紝鏈潵绉戝璇︽儏瀛愰〉鐩存帴鍙敤 |
| 2 | unmapped 绔偣澧炲己杩斿洖瀛楁 + `joinedload` 棰勫姞杞?| 妗岄潰绔?UnmappedExperts.vue 姝ｅ湪浣跨敤 |
| 4 | `GET /admin/experts?department_id=` 涓夊眰閫忎紶 | 绉戝->鍏宠仈涓撳瀵艰埅鍒氶渶锛?0 琛?|
