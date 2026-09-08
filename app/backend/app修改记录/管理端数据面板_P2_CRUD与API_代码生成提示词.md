# 管理端数据面板 P2 — CRUD + API 代码生成提示词

**版本**: V1.0
**创建日期**: 2026-07-23
**基于设计文档**: `app修改记录/管理端后台数据面板_AdminStats设计文档.md`
**依赖**: P1 已完成（Model + Schema）
**目标文件**: 修改 2 个 + 新建 1 个

---

## 1. 角色定义 (Role Definition)

你是一名精通 FastAPI + SQLAlchemy 2.0 异步查询 + PostgreSQL 的 Python 后端工程师。你熟悉本项目 API 层的编码规范——内联 role 校验、`success_response` / `error_response` 统一响应格式、`Depends(get_current_user)` 鉴权模式。你的任务是执行**管理端数据面板 P2**：在 P1 已完成 Model + Schema 的基础上，修改 CRUD 支持 `is_verified` 筛选，新建 `admin_stats.py` 端点文件，注册路由。

**四个必须**：
- 必须遵循已有 `crud/experts.py` 和 `endpoints/expert_departments.py` 的代码风格
- CRUD 层只新增参数，不修改既有函数签名
- API 层必须使用内联 `_check_admin()` 模式（对齐 `expert_departments.py`）
- 查询必须使用异步 SQLAlchemy 2.0 `select()` 风格

---

## 2. 任务目标 (Task Objective)

### 2.1 修改已有文件（2 个）

| 文件 | 修改内容 | 程度 |
|:-----|:---------|:----:|
| `app/crud/experts.py` | `get_experts_multi_and_total()` 新增 `is_verified` 参数 | +3 行 |
| `app/api/v1/endpoints/experts.py` | `list_experts_admin()` 新增 `?is_verified=` 查询参数 | +2 行 |

### 2.2 新建文件（1 个）

| 文件 | 内容 |
|:-----|:-----|
| `app/api/v1/endpoints/admin_stats.py` | `GET /admin/stats/daily` + `GET /admin/sessions/today` |

### 2.3 禁止事项

- ❌ 不修改 `app/services/` 下的任何文件
- ❌ 不修改 `app/models/` 下的任何文件（P1 已完成）
- ❌ 不修改 `app/schemas/` 下的任何文件（P1 已完成）
- ❌ 不修改 `app/core/` 下的依赖注入文件（`get_current_admin` 不存在，方案为内联校验）
- ❌ 不修改既有端点的响应格式

---

## 3. 核心上下文 (Core Context)

### 3.1 `app/crud/experts.py` — `get_experts_multi_and_total()`

**当前函数签名**（约第 250 行附近）：

```python
async def get_experts_multi_and_total(
    db: AsyncSession,
    *,
    page: int = 1,
    size: int = 20,
    name: Optional[str] = None,
    is_featured: Optional[bool] = None,
    is_active: Optional[bool] = None,
    hospital: Optional[str] = None,
    sort: Optional[str] = None,
    category_id: Optional[UUID] = None,
) -> Tuple[List[Expert], int]:
```

**修改**：在 `is_active` 参数之后新增 `is_verified: Optional[bool] = None`，并在 `where` 条件构建处添加：

```python
if is_verified is not None:
    stmt = stmt.where(Expert.is_verified == is_verified)
```

**位置参考**：现有 `is_featured` 和 `is_active` 的 where 条件逻辑在 `stmt` 构建之后、`count` / `order_by` 之前。

### 3.2 `app/api/v1/endpoints/experts.py` — `list_experts_admin()`

**当前端点**（约第 70 行附近，在 `experts_admin_router` 中）：

```python
@experts_admin_router.get("/experts")
async def list_experts_admin(
    ...
    is_active: Optional[bool] = None,
    ...
):
```

**修改**：在 `is_active` 参数之后新增 `is_verified: Optional[bool] = Query(None, description="审核状态筛选")`，并传入 CRUD 调用。

### 3.3 新建 `app/api/v1/endpoints/admin_stats.py`

完整代码参考设计文档 §2.2.1 + §2.3.1。关键设计点：

**端点 A — `GET /admin/stats/daily`**：
- 6 个 COUNT 查询使用 `asyncio.gather` 并行化
- `live_now` 通过 JOIN `LiveSession` 查询 `status='live'` 的去重 `room_id`
- `ExpertDepartment` 的软删除判断用 `is_active == True`（不是 `deleted_at IS NULL`）
- 返回字段包含 `today_new_rooms`（可选辅助指标）

**端点 B — `GET /admin/sessions/today`**：
- 分页查询（`page`, `size` 参数）
- LEFT JOIN `live_rooms` 获取 `room_title`, `cover_url`
- 子查询 JOIN `live_session_experts` + `experts` 获取主讲专家名（`role='主讲'`）
- `LiveSession` 无 `title` 列，响应中不包含此字段
- 使用 `row._mapping["key"]` 方式读取查询结果列

**公共鉴权**：
```python
def _check_admin(role: str) -> None:
    if role not in ("ADMIN", "SUPERADMIN"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="需要管理员权限")
```

两个端点都需在函数体开始处调用 `_check_admin(current_user.get("role", "REGULAR"))`。

---

## 4. 路由注册 (`app/api/v1/api.py`)

在 `expert_departments` 的 `include_router` 之后（约第 85 行附近）新增：

```python
# 13. 管理端统计摘要
from app.api.v1.endpoints import admin_stats
api_router.include_router(admin_stats.router, prefix="")
```

`admin_stats.router` 内部路径已包含 `/admin/` 前缀，所以 `prefix=""`。

---

## 5. 输出要求

### 5.1 输出格式

每个文件用代码块包裹并标注文件路径。修改的 `crud/experts.py` 和 `endpoints/experts.py` 输出 diff 或完整函数体；新建文件输出完整内容。

### 5.2 验证清单

- [ ] `get_experts_multi_and_total()` 新增 `is_verified` 参数后原有调用方不报错
- [ ] `list_experts_admin()` 新增 `is_verified` Query 参数后不破坏已有 API 响应
- [ ] `_check_admin()` 函数在 `admin_stats.py` 中正确定义且被两个端点使用
- [ ] `asyncio.gather` 的导入和用法正确（`import asyncio` 在文件顶部）
- [ ] 6 个 COUNT 查询的 `q_*` 变量定义先于 `asyncio.gather` 调用
- [ ] `live_now` 使用 `select(func.count(LiveRoom.id.distinct())).join(LiveSession, ...)`
- [ ] `pending_departments` 使用 `is_active == True`（不是 `deleted_at IS NULL`）
- [ ] 今日场次的 `expert_subq` 使用 `.where(LiveSessionExpert.role == "主讲")`
- [ ] 今日场次响应不包含 `title` 字段
- [ ] `row._mapping` 读取方式正确（非 `row.id` 触发懒加载）
- [ ] 路由注册位置正确（`admin_stats` 的 `include_router` 在已有 admin 路由之后）
