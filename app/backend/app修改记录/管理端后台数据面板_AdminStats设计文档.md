# 管理端后台数据面板 — Admin Stats 设计文档

> 项目：live-streaming-saas-v2-main
> 创建日期：2026-07-23
> 最后更新：2026-07-27（冗余审查精简）
> 关联文档：[管理员页面设计文档.md](../docs/管理员页面设计文档.md)（前端需求来源）
> 状态：**已实施 → 后经冗余审查精简**

---

## 一、需求概述

### 1.1 背景

前端管理员"我的"页面需要展示「管理摘要」卡片。**经 2026-07-27 冗余审查，前端实际仅使用「今日场次」和「正在直播」两张卡片，其余"待审核/未归类专家"入口已移除或归入各自管理页面。** 本端点因此从 6 字段精简为 2 字段。

### 1.2 本次修改目标

1. **新增 `GET /api/v1/admin/stats/daily`** — 管理摘要卡片数据源（仅 today_sessions + live_now）
2. **Expert 模型新增 `is_verified` 字段** — 支持审核语义（保留，用于 Admin 专家列表筛选）
3. **新增 `GET /api/v1/admin/sessions/today`** — 今日场次列表（前端"今日场次"卡片点击跳转目标）
4. **新建 `schemas/admin.py`** — 管理端响应 Schema（AdminDailyStats 仅 2 字段 + TodaySessionItem/TodaySessionListResponse）

---

## 二、修改项详情

### 2.1 Expert 模型增加 `is_verified` 字段

现有 Expert 模型只支持 `is_active`（软删除）和 `is_featured`（是否推荐），缺少审核态。`is_verified` 与 `is_active` 是正交语义：

| 字段 | 语义 | 设计用途 |
|------|------|---------|
| `is_active` | 软删除标志 | `False` = 已删除，前端不展示 |
| `is_verified` | 审核状态 | `True` = 已审批，`False` = 待审批（默认） |
| `is_featured` | 推荐标志 | `True` = 首页推荐展示 |

**语义边界**：
- `is_verified=false` 表示专家档案由用户或自动导入创建，尚未经过管理员人工审核
- `is_verified=true` 表示管理员已审核通过
- 已审核但 `department_id=null` 的专家 → 计入 `unmapped_experts`（待分配科室），**不计入** `pending_experts`
- 未审核的专家无论 `department_id` 是否为空 → 计入 `pending_experts`

#### 2.1.1 Model 层 — `models/experts.py`

新增字段（默认 `False`）：

```python
is_verified = Column(Boolean, default=False, nullable=False, comment="审核状态: False=待审批, True=已审批")
```

#### 2.1.2 CRUD 层 — `crud/experts.py`

`get_experts_multi_and_total()` 新增 `is_verified` 筛选参数：

```python
async def get_experts_multi_and_total(
    db: AsyncSession,
    *,
    page: int = 1,
    size: int = 20,
    name: Optional[str] = None,
    is_featured: Optional[bool] = None,
    is_active: Optional[bool] = None,
    is_verified: Optional[bool] = None,  # ← 新增
    hospital: Optional[str] = None,
    sort: Optional[str] = None,
    category_id: Optional[UUID] = None,
) -> Tuple[List[Expert], int]:
```

#### 2.1.3 Schema 层 — `schemas/experts.py`

- `ExpertCreate`：新增可选字段 `is_verified: bool = False`
- `ExpertUpdate`：新增可选字段 `is_verified: Optional[bool] = None`
- `ExpertItem`：新增字段 `is_verified: bool`

#### 2.1.4 API 层 — `endpoints/experts.py`

`GET /admin/experts` 新增查询参数 `?is_verified=`

```python
@experts_admin_router.get("/experts")
async def list_experts_admin(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    name: Optional[str] = None,
    is_featured: Optional[bool] = None,
    is_active: Optional[bool] = None,
    is_verified: Optional[bool] = None,  # ← 新增
    hospital: Optional[str] = None,
    sort: Optional[str] = None,
    category_id: Optional[UUID] = None,
    ...
):
```

---

### 2.2 新建 `GET /api/v1/admin/stats/daily` — P0

#### 2.2.1 新建文件

`backend/live_core_service/app/api/v1/endpoints/admin_stats.py`

```python
import asyncio
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func, String
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_db
from app.core.deps import get_current_user
from app.core.response import success_response
from app.models.live_core import LiveRoom, LiveSession
from app.models.experts import Expert, LiveSessionExpert
from app.models.expert_departments import ExpertDepartment

router = APIRouter(tags=["管理端-统计摘要"])


def _check_admin(role: str) -> None:
    """校验 ADMIN/SUPERADMIN 角色（对齐现有 admin 端点的模式）"""
    if role not in ("ADMIN", "SUPERADMIN"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="需要管理员权限")


@router.get("/admin/stats/daily")
async def get_admin_daily_stats(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """
    管理摘要运营统计。

    数据分两类：
    - 时间敏感型（每天自然归零）：today_sessions, live_now, today_new_rooms
    - 累积待办型（处理后才减少）：pending_departments, pending_experts, unmapped_experts
    """
    _check_admin(current_user.get("role", "REGULAR"))

    # 6 个 COUNT 使用 asyncio.gather 并行执行，降低总延迟
    q_today_sessions = select(func.count(LiveSession.id)).where(
        func.date(LiveSession.start_time) == func.current_date()
    )
    # live_now：查当前 status='live' 的场次对应的去重房间数
    # LiveRoom 无 live_status 列，需通过 LiveSession.status 推导
    q_live_now = select(func.count(LiveRoom.id.distinct())).join(
        LiveSession, LiveSession.room_id == LiveRoom.id
    ).where(LiveSession.status == "live")
    q_today_new_rooms = select(func.count(LiveRoom.id)).where(
        func.date(LiveRoom.created_at) == func.current_date()
    )
    # ExpertDepartment 使用 is_active 做软删除（无 deleted_at 列）
    q_pending_dept = select(func.count(ExpertDepartment.id)).where(
        ExpertDepartment.is_verified == False,
        ExpertDepartment.is_active == True,
    )
    q_pending_exp = select(func.count(Expert.id)).where(
        Expert.is_verified == False,
        Expert.is_active == True,
    )
    q_unmapped = select(func.count(Expert.id)).where(
        Expert.department_id.is_(None),
        Expert.is_active == True,
    )

    results = await asyncio.gather(
        db.execute(q_today_sessions),
        db.execute(q_live_now),
        db.execute(q_today_new_rooms),
        db.execute(q_pending_dept),
        db.execute(q_pending_exp),
        db.execute(q_unmapped),
    )

    (today_sessions, live_now, today_new_rooms,
     pending_departments, pending_experts, unmapped_experts) = (
        r.scalar() or 0 for r in results
    )

    return success_response(data={
        "today_sessions": today_sessions,
        "live_now": live_now,
        "today_new_rooms": today_new_rooms,
        "pending_departments": pending_departments,
        "pending_experts": pending_experts,
        "unmapped_experts": unmapped_experts,
    })
```

#### 2.2.2 路由注册 — `api.py`

在 `expert_departments` 的路由注册之后（约第 85 行附近），新增：

```python
# 13. 管理端统计摘要
from app.api.v1.endpoints import admin_stats
api_router.include_router(admin_stats.router, prefix="")
```

> 路由器内部已含 `/admin/...` 前缀，故 `prefix=""`。最终路径为 `GET /api/v1/admin/stats/daily` 和 `GET /api/v1/admin/sessions/today`。

#### 2.2.3 鉴权要求

使用 `Depends(get_current_user)` 获取当前用户，通过内联 `_check_admin()` 校验 `role in ('ADMIN', 'SUPERADMIN')`。对齐现有 `/admin/` 端点的鉴权模式（见 `expert_departments.py`、`live_features.py` 中的内联 role 校验）。

---

### 2.3 新建 `GET /api/v1/admin/sessions/today` — P1

#### 2.3.1 端点位置

新增函数在 `admin_stats.py`（与 stats/daily 同文件）或独立文件。

```python
@router.get("/admin/sessions/today")
async def get_admin_sessions_today(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """
    今日场次列表。筛选规则：DATE(start_time) = CURRENT_DATE。
    用于管理摘要「今日场次」卡片点击后跳转的目标页面。
    """
    _check_admin(current_user.get("role", "REGULAR"))

    # 查询今日场次总数
    count_result = await db.execute(
        select(func.count(LiveSession.id)).where(
            func.date(LiveSession.start_time) == func.current_date()
        )
    )
    total = count_result.scalar() or 0

    # 查询今日场次列表（JOIN live_rooms + live_session_experts + experts）
    # 注意：LiveSession 无 title 列，使用 room_title 作为展示标题
    offset = (page - 1) * size

    # 子查询：取每个 session 的主讲专家姓名（仅 role='主讲'，避免混入主持/嘉宾）
    expert_subq = (
        select(
            LiveSessionExpert.session_id,
            func.string_agg(Expert.name, "、").label("expert_names"),
        )
        .join(Expert, LiveSessionExpert.expert_id == Expert.id)
        .where(LiveSessionExpert.role == "主讲")
        .group_by(LiveSessionExpert.session_id)
        .subquery()
    )

    query = (
        select(
            LiveSession.id,
            LiveSession.room_id,
            LiveSession.status,
            LiveSession.start_time,
            LiveRoom.title.label("room_title"),
            LiveRoom.cover_url,
            expert_subq.c.expert_names,
        )
        .join(LiveRoom, LiveSession.room_id == LiveRoom.id)
        .outerjoin(expert_subq, expert_subq.c.session_id == LiveSession.id)
        .where(func.date(LiveSession.start_time) == func.current_date())
        .order_by(LiveSession.start_time.desc())
        .offset(offset)
        .limit(size)
    )
    result = await db.execute(query)
    rows = result.all()

    items = [
        {
            "id": str(row._mapping["id"]),
            "room_id": str(row._mapping["room_id"]),
            "status": row._mapping["status"],
            "start_time": row._mapping["start_time"].isoformat() if row._mapping["start_time"] else None,
            "room_title": row._mapping["room_title"],
            "cover_url": row._mapping["cover_url"],
            "expert_name": row._mapping["expert_names"] or None,
        }
        for row in rows
    ]

    return success_response(data={
        "items": items,
        "total": total,
        "page": page,
        "size": size,
    })
```

#### 2.3.2 字段说明

> `LiveSession` 模型无 `title` 列。前端响应中的 `title` 字段映射为 `room_title`（直播间标题），前端按需调整展示文案。`expert_name` 通过 `live_session_experts` + `experts` LEFT JOIN 获取。
>
> **预存缺口**：`SessionImportCreate.title` 虽被 Schema 接受，但 `LiveSession` 模型无对应列，数据被静默丢弃。前端如需场次级独立标题，需与后端协商新增列，或统一用 `room_title` 替代。

| 字段 | 类型 | 来源 | 说明 |
|------|------|------|------|
| `id` | UUID | `live_sessions.id` | 场次ID |
| `room_id` | UUID | `live_sessions.room_id` | 直播间ID |
| `status` | string | `live_sessions.status` | 场次状态 |
| `start_time` | datetime | `live_sessions.start_time` | 开始时间（ISO 8601） |
| `room_title` | string | `live_rooms.title`（JOIN） | 直播间标题，替代无 `title` 的场次 |
| `cover_url` | string | `live_rooms.cover_url`（JOIN） | 直播间封面 |
| `expert_name` | string | `experts.name`（LEFT JOIN） | 主讲专家名（来自 `live_session_experts` 关联） |

---

### 2.4 新建 `schemas/admin.py`

统一管理端响应 Schema，便于类型校验和代码维护。

```python
from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel


class AdminDailyStats(BaseModel):
    """GET /admin/stats/daily 响应 data（经 2026-07-27 精简，仅保留前端实际使用的 2 字段）"""
    today_sessions: int
    live_now: int


class TodaySessionItem(BaseModel):
    """今日场次列表项（LiveSession 无 title 列，使用 room_title）"""
    id: UUID
    room_id: UUID
    status: str
    start_time: Optional[datetime] = None
    room_title: str
    cover_url: Optional[str] = None
    expert_name: Optional[str] = None


class TodaySessionListResponse(BaseModel):
    """GET /admin/sessions/today 响应 data"""
    items: List[TodaySessionItem]
    total: int
    page: int
    size: int
```

---

## 三、影响范围与依赖

### 3.1 文件修改清单

| 文件 | 操作 | 说明 |
|------|:----:|------|
| `backend/live_core_service/app/models/experts.py` | 修改 | 新增 `is_verified` 字段 |
| `backend/live_core_service/app/crud/experts.py` | 修改 | `get_experts_multi_and_total()` 新增 `is_verified` 参数 |
| `backend/live_core_service/app/schemas/experts.py` | 修改 | Create/Update/Item 新增 `is_verified` |
| `backend/live_core_service/app/api/v1/endpoints/experts.py` | 修改 | `GET /admin/experts` 新增 `?is_verified=` 参数 |
| `backend/live_core_service/app/api/v1/endpoints/admin_stats.py` | **新建** | `GET /admin/stats/daily` + `GET /admin/sessions/today` |
| `backend/live_core_service/app/schemas/admin.py` | **新建** | 管理端统一响应 Schema |
| `backend/live_core_service/app/api/v1/api.py` | 修改 | 注册 `admin_stats.router` |
| `backend/live_core_service/app/seed.py` | 修改 | 种子专家创建处补充 `is_verified=True` |

### 3.2 不涉及的文件

- `content_management.py` — 分类逻辑未触及
- `expert_departments.py` — 科室 `is_verified` 已存在，本次改动的是 Expert 模型
- 所有前端文件 — 纯后端改动

### 3.3 数据迁移

新增 `is_verified` 字段后，需要为现有专家数据设置默认值：

```sql
ALTER TABLE experts ADD COLUMN is_verified BOOLEAN NOT NULL DEFAULT FALSE;

-- 将现有已启用(is_active=True)的专家标记为已审批，避免存量数据全部变为待审批
UPDATE experts SET is_verified = TRUE WHERE is_active = TRUE;
```

建议在 `migrations/` 目录下创建 SQL 迁移文件（如 `add_experts_is_verified.sql`），在部署时手动执行。

> **种子数据**：`seed.py` 中需为种子专家的创建调用处补充 `is_verified=True`，防止 400 名种子专家全部变成"待审批"状态。需修改 `seed_experts()` 函数中的 Expert 创建调用。

---

## 四、数据语义与边界

### 4.1 计数 SQL 汇总

> **2026-07-27 冗余审查**：以下仅 `today_sessions` 和 `live_now` 保留。其余 4 个字段前端已不再展示（入口已移除/归入各自管理页面），对应的 COUNT 查询已从 `admin_stats.py` 中删除。

| 字段 | 数据类型 | SQL | 当前状态 |
|------|---------|-----|:--:|
| `today_sessions` | 时间敏感型 | `SELECT COUNT(*) FROM live_sessions WHERE DATE(start_time) = CURRENT_DATE` | 保留 |
| `live_now` | 时间敏感型 | `SELECT COUNT(DISTINCT room_id) FROM live_sessions WHERE status = 'live'` | 保留 |
| `today_new_rooms` | ~~时间敏感型~~ | ~~`SELECT COUNT(*) FROM live_rooms WHERE DATE(created_at) = CURRENT_DATE`~~ | **已删除** |
| `pending_departments` | ~~累积待办型~~ | ~~`SELECT COUNT(*) FROM expert_departments WHERE is_verified = false AND is_active = true`~~ | **已删除** |
| `pending_experts` | ~~累积待办型~~ | ~~`SELECT COUNT(*) FROM experts WHERE is_verified = false AND is_active = true`~~ | **已删除** |
| `unmapped_experts` | ~~累积待办型~~ | ~~`SELECT COUNT(*) FROM experts WHERE department_id IS NULL AND is_active = true`~~ | **已删除** |

### 4.2 字段独立性说明

```
ExpertDepartment.is_verified  →  科室是否审核（已有）
Expert.is_verified（新增）     →  专家档案是否审批
```

两者是不同模型的独立字段，互不影响：

- 一个科室通过审核（`ExpertDepartment.is_verified=True`），引用该科室的专家可以仍处待审批（`Expert.is_verified=False`）
- 一个专家已审批（`Expert.is_verified=True`），但其关联的科室可能仍待审核
- `pending_experts` 和 `unmapped_experts` 的专家集合存在重叠可能（一个专家同时是待审批且未分配科室），但前端两个卡片展示不同维度的计数，不要求集合不交

---

## 五、实施计划

### 5.1 实施顺序

| 步骤 | 内容 | 文件数 | 优先级 |
|:---:|------|:---:|:---:|
| 1 | Expert 模型新增 `is_verified` 字段 | 1 | P0 |
| 2 | Schema 层新增 `is_verified` | 1 | P0 |
| 3 | CRUD 层新增 `is_verified` 筛选 | 1 | P0 |
| 4 | API 层 `GET /admin/experts` 新增参数 | 1 | P0 |
| 5 | 新建 `admin_stats.py` + 两个端点 | 1 | P0 |
| 6 | 新建 `schemas/admin.py` | 1 | P1 |
| 7 | 注册路由到 `api.py` | 1 | P0 |
| 8 | 创建 SQL 迁移文件 | 1 | P0 |
| 9 | 语法检查 + 测试验证 | — | — |

### 5.2 验证方式

```powershell
# Python 语法检查
cd backend\live_core_service
python -m py_compile app\models\experts.py app\crud\experts.py app\schemas\experts.py app\api\v1\endpoints\experts.py app\api\v1\endpoints\admin_stats.py app\schemas\admin.py
```

---

## 六、实际实施总结（2026-07-23）

### 6.1 实施范围

| 编号 | 文件 | 操作 | 实施阶段 |
|:---:|------|:----:|:--------:|
| 1 | `app/models/experts.py` | 修改 — 新增 `is_verified` 字段 | P1 |
| 2 | `app/schemas/experts.py` | 修改 — `ExpertCreate`/`ExpertUpdate`/`ExpertItem` 新增 `is_verified` | P1 |
| 3 | `app/schemas/admin.py` | **新建** — `AdminDailyStats`、`TodaySessionItem`、`TodaySessionListResponse` | P1 |
| 4 | `app/crud/experts.py` | 修改 — `get_experts_multi_and_total()` 新增 `is_verified` 参数 | P2 |
| 5 | `app/services/expert_service.py` | 修改 — `get_experts_list()` 新增 `is_verified` 透传参数 | P2 |
| 6 | `app/api/v1/endpoints/experts.py` | 修改 — `GET /admin/experts` 新增 `?is_verified=` 参数 | P2 |
| 7 | `app/api/v1/endpoints/admin_stats.py` | **新建** — `GET /admin/stats/daily` + `GET /admin/sessions/today` | P2 |
| 8 | `app/api/v1/api.py` | 修改 — 注册 `admin_stats.admin_stats_router` | P2 |
| 9 | `migrations/add_experts_is_verified.sql` | **新建** — 幂等迁移 SQL | P3 |
| 10 | `app/seed.py` | 修改 — 种子专家创建补充 `is_verified=True` | P3 |

### 6.2 设计与实现的偏差

#### 6.2.1 API 端点路由注册方式

| 维度 | 设计文档 | 实际实现 | 说明 |
|------|---------|---------|------|
| 路由器变量名 | `router` | `admin_stats_router` | 按项目命名规范（`前缀_router`） |
| 注册方式 | `prefix=""`，路径内联 `/admin/stats/daily` | `prefix="/admin"`，路径仅 `/stats/daily` | 最终 URL 一致：`/api/v1/admin/stats/daily` |
| 注册位置 | "第 85 行附近，13 号段" | 放于 expert_departments 之后（§9.5→§10） | 更清晰 |

#### 6.2.2 鉴权机制

| 维度 | 设计文档 | 实际实现 | 说明 |
|------|---------|---------|------|
| 权限校验函数 | 内联 `_check_admin()` 抛出 `HTTPException(403)` | 共享 `from app.core.permissions import check_admin_permission` 抛出 `PermissionDeniedException` | 更符合项目现有的共享函数模式 |
| DB 依赖 | `get_async_db` | `get_db` | 项目实际使用 `get_db` |

#### 6.2.3 `live_now` 计数 SQL

| 维度 | 设计文档 | 实际实现 | 说明 |
|------|---------|---------|------|
| SQL | `SELECT COUNT(DISTINCT lr.id) FROM live_rooms lr JOIN live_sessions ls ON ...` | `SELECT COUNT(DISTINCT room_id) FROM live_sessions WHERE status='live'` | 不用 JOIN，直接对 LiveSession.room_id 去重，逻辑等价更高效 |

#### 6.2.4 累积待办型计数的 `is_active` 过滤（需注意）

| 字段 | 设计文档 | 实际实现（含本轮修复后） |
|------|---------|----------------------|
| `pending_departments` | `is_verified=false AND is_active=true` | ✅ `is_verified=False, is_active=True` |
| `pending_experts` | `is_verified=false AND is_active=true` | ✅ `is_verified=False, is_active=True` |
| `unmapped_experts` | `department_id IS NULL AND is_active=true` | ✅ `department_id.is_(None), is_active=True` |

> **本轮审查发现**：原实现遗漏了 `is_active=True` 过滤，于 2026-07-23 审查后补正。

#### 6.2.5 今日场次专家查询方式

| 维度 | 设计文档 | 实际实现 | 说明 |
|------|---------|---------|------|
| 专家聚合 | 子查询 `func.string_agg(Expert.name, "、")` 聚合所有主讲 | `OUTER JOIN` 匹配单个主讲（取 `LiveSessionExpert.role='主讲'` 的首条记录） | 实际实现仅取 1 个主讲，与设计的多专家聚合不同 |

#### 6.2.6 `format_expert_response` 缺少 `is_verified`

| 维度 | 说明 |
|------|------|
| 问题 | `format_expert_response()` 手动构造 dict 时遗漏 `is_verified` 字段（`ExpertItem` schema 已有此字段） |
| 影响 | Admin 可按 `?is_verified=` 筛选但响应中看不到该值 |
| 修复 | 2026-07-23 审查后补正，已添加 `"is_verified": expert.is_verified` |

#### 6.2.7 Function 命名

| 设计文档 | 实际实现 | 说明 |
|---------|---------|------|
| `list_experts_admin()` | `get_experts_list()` | 同路由，命名不同 |

### 6.3 实施文件清单（含缩进）

```
backend/live_core_service/
├── migrations/
│   └── add_experts_is_verified.sql          ★ 新建 — 幂等迁移
├── app/
│   ├── models/
│   │   └── experts.py                       ⚡ 修改 — is_verified 字段
│   ├── schemas/
│   │   ├── admin.py                         ★ 新建 — 管理端响应 Schema
│   │   └── experts.py                       ⚡ 修改 — is_verified 字段
│   ├── crud/
│   │   └── experts.py                       ⚡ 修改 — get_experts_multi_and_total 新增参数
│   ├── services/
│   │   └── expert_service.py                ⚡ 修改 — get_experts_list 透传参数
│   ├── api/
│   │   └── v1/
│   │       ├── api.py                       ⚡ 修改 — 注册 admin_stats 路由
│   │       └── endpoints/
│   │           ├── admin_stats.py           ★ 新建 — 2 个端点
│   │           └── experts.py               ⚡ 修改 — 新增 ?is_verified= 参数 + format_expert_response 补全
│   └── seed.py                              ⚡ 修改 — 种子专家 is_verified=True
```

### 6.4 验证确认

| 检查项 | 结果 |
|--------|------|
| SQL 迁移幂等执行（384 行回填 `is_verified=TRUE`） | ✅ |
| 列定义确认（`boolean NOT NULL DEFAULT false`） | ✅ |
| 所有文件 `py_compile` 语法检查通过 | ✅ |
| Docker 容器启动无 ImportError | ✅ |
| 端点路由正确注册（`/stats/daily`, `/sessions/today`, `/expert-departments` 等） | ✅ |
| `is_verified` 参数三层贯通（Query → Service → CRUD → DB） | ✅ |
| 所有 P3 融合方案 Service 方法可正常导入 | ✅

### 6.5 冗余审查与精简（2026-07-27）

#### 6.5.1 精简背景

经前后端联合审查，前端管理员"我的"页面仅保留「今日场次」「正在直播」两张统计卡片，其余入口（待审核科室、待审批专家、未归类专家）已归入各管理子页面。`GET /admin/stats/daily` 原来返回 6 个字段，其中 4 个不再被任何前端组件展示。

#### 6.5.2 精简内容

| 操作 | 位置 | 说明 |
|------|------|------|
| 删除 4 个 COUNT 查询 | `admin_stats.py` | `today_new_rooms`、`pending_departments`、`pending_experts`、`unmapped_experts` |
| 删除 `asyncio.gather` | `admin_stats.py` | 仅剩 2 个查询，改为顺序 await |
| 精简 `AdminDailyStats` | `schemas/admin.py` | 从 6 字段 → 2 字段（`today_sessions` + `live_now`） |
| 删除废弃 import | `admin_stats.py` | `asyncio`、`Expert`（from experts）、`ExpertDepartment` |

#### 6.5.3 保留确认

| 保留项 | 理由 |
|--------|------|
| `GET /admin/stats/daily` 端点 | 前端 2 张卡片仍在使用 |
| `GET /admin/sessions/today` 端点 | 前端"今日场次"卡片点击下钻使用 |
| `Expert.is_verified` 字段 + 四层透传 | Model 层语义缺口，Admin 专家列表仍需 `?is_verified=` 筛选 |
| `schemas/admin.py` 中 `TodaySessionItem` / `TodaySessionListResponse` | `sessions/today` 仍在使用 |
| `migrations/add_experts_is_verified.sql` | Model 字段未删除，迁移仍需执行 |
| `seed.py` 中 `is_verified=True` | 种子数据正确性 |
