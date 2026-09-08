# Admin 接口权限规范化方案

> 创建日期：2026-06-17
> 关联文档：[API路由规范统一方案.md](./API路由规范统一方案.md)
> 状态：阶段A 已完成 ✅ | 阶段B 后端+前端已实施

---

## 一、问题概述

### 1.1 核心矛盾

当前代码中，**8 个端点的 URL 路径包含 `/admin`，但实际权限校验允许普通用户（房间创建者）调用**。

| 模块 | 端点路径 | 当前权限 | 问题 |
|------|---------|---------|:----:|
| Tab 管理 | `GET/POST /admin/rooms/{id}/tabs` | ADMIN 或创建者 | ⚠️ |
| Tab 管理 | `PATCH/DELETE /admin/tabs/{id}` | ADMIN 或创建者 | ⚠️ |
| 分类管理 | `POST /admin/rooms/{id}/categories` | ADMIN 或创建者 | ⚠️ |
| 分类管理 | `DELETE /admin/rooms/{id}/categories/{cid}` | ADMIN 或创建者 | ⚠️ |
| 品牌绑定 | `POST /admin/rooms/{id}/brands` | ADMIN 或创建者 | ⚠️ |

### 1.2 权限校验代码分散

"ADMIN 或房间创建者"的双重校验逻辑在代码库中**重复出现了约 16 处**，分布在 8 个 Service 文件中，没有统一的公共函数。具体位置详见下文 §2.3。

---

## 二、所有涉及位置清单

### 2.1 有 `/admin` 路径问题的端点（需改造）

#### ① Tab 管理 — `live_features.py` / `live_features_service.py`

| # | 端点 | 文件:行 | 当前 URL |
|:-:|------|---------|---------|
| 1 | `list_room_tabs` | `endpoints/live_features.py:63` | `GET /admin/rooms/{room_id}/tabs` |
| 2 | `upload_tab_image` | `endpoints/live_features.py:138` | `POST /admin/rooms/{room_id}/tabs/image` |
| 3 | `create_tab` | `endpoints/live_features.py:177` | `POST /admin/rooms/{room_id}/tabs` |
| 4 | `update_tab` | `endpoints/live_features.py:260` | `PATCH /admin/tabs/{tab_id}` |
| 5 | `delete_tab` | `endpoints/live_features.py:340` | `DELETE /admin/tabs/{tab_id}` |

权限方法：`_check_tab_management_permission()` 位于 `services/live_features_service.py:78-115`

#### ② 分类管理 — `content_management.py` / `content_management_service.py`

| # | 端点 | 文件:行 | 当前 URL |
|:-:|------|---------|---------|
| 6 | `set_live_room_categories` | `endpoints/content_management.py:722` | `POST /admin/rooms/{room_id}/categories` |
| 7 | `delete_live_room_category` | `endpoints/content_management.py:767` | `DELETE /admin/rooms/{room_id}/categories/{category_id}` |

权限逻辑：内联于 `services/content_management_service.py:885` 和 `:928`

#### ③ 品牌绑定 — `brand.py` / `brand_service.py`

| # | 端点 | 文件:行 | 当前 URL |
|:-:|------|---------|---------|
| 8 | `bind_room_brands` | `endpoints/brand.py:578` | `POST /admin/rooms/{room_id}/brands` |

权限逻辑：内联于 `services/brand_service.py:652-657`

### 2.2 无需改造（URL 不含 `/admin`，权限放宽语义正确）

这些是**读操作或自身资源管理**，URL 路径不含 `/admin`，创建者有权访问自己的资源是合理的：

| # | 位置 | 行号 | 用途 | URL |
|:-:|------|:----:|------|-----|
| A | `services/room_service.py` | 74-89 | `_check_room_visibility()` | `GET /rooms/{id}` 私有房间可见性 |
| B | `services/room_service.py` | 108-119 | `_check_write_permission()` | `PATCH/DELETE /rooms/{id}` 等 |
| C | `services/session_service.py` | 79-93 | 同上（复制 room_service） | 场次可见性 |
| D | `services/session_service.py` | 112-123 | 同上（复制 room_service） | 场次写权限 |
| E | `services/session_import.py` | 55-65 | 同上（复制 room_service） | 导入场次 |
| F | `services/live_features_service.py` | 384-399 | MessageService 可见性 | 留言读 |
| G | `services/topic_service.py` | 1128-1133 | `get_topics_by_room()` | 私有房间的专题可见性 |
| H | `services/topic_service.py` | 1214-1219 | `batch_get_room_status()` | 内部数据过滤 |
| I | `services/expert_service.py` | 1009-1016 | `set_session_experts()` | `POST /experts/sessions/{id}/experts` |
| J | `endpoints/live_features.py` | 589 | `list_room_tabs_public()` 内联 | `GET /rooms/{id}/tabs` 可见性 |

> 以上 A-J 共 10 处代码**重复实现了同一套逻辑**，虽然没有 `/admin` 问题，但建议统一收敛为公共函数以消除重复。

### 2.3 分散的权限校验一览（全量 18 处）

| 组 | 文件 | 行 | 实现方式 | 是否含 /admin 问题 |
|:--:|------|:-:|---------|:----------------:|
| 1 | `live_features_service.py` | 78-115 | ✅ 集中式方法 `_check_tab_management_permission` | ⚠️ 是 |
| 2-5 | 4 个 Tab 端点调用上述方法 | — | 通过方法调用 | ⚠️ 是 |
| 6 | `content_management_service.py` | 885 | 内联 | ⚠️ 是 |
| 7 | `content_management_service.py` | 928 | 内联 | ⚠️ 是 |
| 8 | `brand_service.py` | 652-657 | 内联 | ⚠️ 是 |
| A | `room_service.py` | 74-89 | ✅ 集中式 `_check_room_visibility` | ✅ 否 |
| B | `room_service.py` | 108-119 | ✅ 集中式 `_check_write_permission` | ✅ 否 |
| C | `session_service.py` | 79-93 | 复制 room_service | ✅ 否 |
| D | `session_service.py` | 112-123 | 复制 room_service | ✅ 否 |
| E | `session_import.py` | 55-65 | 复制 room_service | ✅ 否 |
| F | `live_features_service.py` | 384-399 | 内联（复制 room_service） | ✅ 否 |
| G | `topic_service.py` | 1128-1133 | 内联 | ✅ 否 |
| H | `topic_service.py` | 1214-1219 | 内联 | ✅ 否 |
| I | `expert_service.py` | 1009-1016 | 内联 | ✅ 否 |
| J | `endpoints/live_features.py` | 589 | 内联 | ✅ 否 |

---

## 三、改造方案

### 3.1 整体策略

```
阶段划分           内容               风险          依赖
────────────────────────────────────────────────────────
阶段A（现在做）   新建 permissions.py    🟢 低      无
                   + 替换全部18处调用
                   （收敛冗余代码）     
                                                       
阶段B（待确认）   拆分 /admin 语义冲突   🟡 中-高   需先确认外部调用方
                   + 创建者新端点
```

---

### 3.2 阶段A：统一权限校验 + 收敛冗余代码（零API变更）

**目标**：消除全部 18 处重复代码，收敛到 `app/core/permissions.py` 公共函数。不改变任何 API 路径和权限行为。

**风险**：🟢 低 — 纯内部重构，仅替换实现方式，行为不变。

#### 新建 `app/core/permissions.py`

```python
from uuid import UUID
from typing import Optional
from app.models.live_core import LiveRoom


def check_room_owner_or_admin(
    room: LiveRoom,
    user_id: UUID,
    role: str,
) -> None:
    """校验当前用户是 ADMIN/SUPERADMIN 或房间创建者"""
    if role in ('ADMIN', 'SUPERADMIN'):
        return
    if room.user_id == user_id:
        return
    raise PermissionDeniedException("需要管理员或房间创建者权限")


def check_room_visibility(
    room: LiveRoom,
    user_id: Optional[UUID],
    role: Optional[str],
) -> None:
    """校验房间可见性（公开放行 / 私有仅创建者和管理员）"""
    if not room.is_private:
        return
    if not user_id:
        raise NotFoundException("Room not found")
    if role in ('ADMIN', 'SUPERADMIN'):
        return
    if room.user_id == user_id:
        return
    raise NotFoundException("Room not found")
```

#### 替换范围（按执行顺序）

| 顺序 | 文件 | 替换内容 | 涉及行 |
|:---:|------|---------|:------:|
| 1 | `services/room_service.py` | `_check_room_visibility` + `_check_write_permission` 内部实现 | 74-89, 108-119 |
| 2 | `services/session_service.py` | 复制 room_service 的逻辑 → 调公共函数 | 79-93, 112-123 |
| 3 | `services/session_import.py` | 同上 | 55-65 |
| 4 | `services/live_features_service.py` | MessageService 可见性 + TabService 权限方法 | 78-115, 384-399 |
| 5 | `services/content_management_service.py` | 分类设置/删除的内联校验 | 885, 928 |
| 6 | `services/brand_service.py` | 品牌绑定的内联校验 | 652-657 |
| 7 | `services/expert_service.py` | 场次设专家的内联校验 | 1009-1016 |
| 8 | `services/topic_service.py` | 专题查询的内联校验 | 1128-1133, 1214-1219 |
| 9 | `endpoints/live_features.py` | 公开 Tab 可见性内联校验 | 589 |

> 每个文件替换完成后运行测试，确保无回归后再进行下一个。

#### 阶段A 执行结果

**执行日期**：2026-06-17

**修改文件清单**：

| 文件 | 操作 | 说明 |
|------|:----:|------|
| `app/core/permissions.py` | **新建** | 两个公共函数：`check_room_owner_or_admin`、`check_room_visibility` |
| `services/room_service.py` | 修改 | `_check_room_visibility` + `_check_write_permission` 委托给公共函数 |
| `services/session_service.py` | 修改 | 同上（消除重复） |
| `services/session_import.py` | 修改 | `_check_write_permission` 委托给公共函数（消除重复） |
| `services/live_features_service.py` | 修改 | `_check_tab_management_permission` + MessageService 可见性委托（消除重复） |
| `services/content_management_service.py` | 修改 | `set_live_room_categories` + `delete_live_room_category` 内联校验替换 |
| `services/brand_service.py` | 修改 | `bind_room_brands` 内联校验替换（同时消除了重复的 room 查询） |
| `services/expert_service.py` | 修改 | `set_session_experts` 内联校验替换 |
| `services/topic_service.py` | 修改 | `get_topics_by_room` 可见性校验替换 |
| `endpoints/live_features.py` | 修改 | `list_room_tabs_public` 内联可见性校验替换 |

**测试结果**：

| 测试 | 用例数 | 结果 |
|------|:------:|:----:|
| 已有集成测试（公开 Tab 8 + 图片上传 6） | 14 | ✅ 全部通过 |
| **新增单元测试** `tests/unit/test_core_permissions.py` | **16** | ✅ **全部通过** |
| **合计** | **30** | ✅ **全部通过** |

**新增测试覆盖**：

`tests/unit/test_core_permissions.py` — 直接测试 `app.core.permissions` 的两个公共函数：

`TestCheckRoomOwnerOrAdmin`（7 用例）：
- ADMIN/SUPERADMIN 通行
- 创建者（REGULAR）通行
- 小写 `"regular"` role 兼容
- 非创建者拒、空 role 拒、None role 拒

`TestCheckRoomVisibility`（9 用例）：
- 公开房间：匿名/普通/Admin 均可访问
- 私有房间：匿名拒（404）、Admin/SUPERADMIN 通、创建者通、非创建者拒（404）、空 role 拒

**验证方式**：

```powershell
# 运行新增的单元测试
docker exec live-streaming-saas-v2-main-live_core_service-1 python -c "import sys; sys.path.insert(0, '/app'); import app.database; import app.models.live_core; import app.models.live_features; import types; app_t=types.ModuleType('app.tests'); app_t.__path__=['/app/tests']; sys.modules['app.tests']=app_t; import pytest; exit(pytest.main(['tests/unit/test_core_permissions.py','-v']))"

# 运行已有集成测试（确认无回归）
docker exec live-streaming-saas-v2-main-live_core_service-1 python //app//run_preload.py
```

**未改动说明**：

`topic_service.py:1214-1219` `batch_get_room_status()` 中的过滤循环未替换，原因是该处为数据过滤（循环内判断是否追加到结果列表）而非守卫函数（抛出异常），逻辑正确且不适用公共函数的异常抛出模式。

---

### 3.4 阶段B 执行记录（新增创建者端点 + 前端路径切换）

**执行日期**：2026-06-17

本次实施的是阶段B 的**安全部分**：新增创建者专用端点 + 前端切换到新路径。暂未收紧旧 admin 端点权限（旧路径仍保持"ADMIN 或创建者"）。

#### 后端新增端点（7 个）

| Router | 路径 | 方法 | 用途 |
|--------|------|:----:|------|
| `room_tab_router` (new) | `/rooms/{room_id}/tabs` | POST | 创建者创建 Tab |
| `room_tab_router` (new) | `/rooms/{room_id}/tabs/image` | POST | 创建者上传 Tab 图片 |
| `room_tab_router` (new) | `/rooms/{room_id}/tabs/{tab_id}` | PATCH | 创建者更新 Tab |
| `room_tab_router` (new) | `/rooms/{room_id}/tabs/{tab_id}` | DELETE | 创建者删除 Tab |
| `live_room_categories_router` (已有) | `/rooms/{room_id}/categories` | POST | 创建者设置分类 |
| `live_room_categories_router` (已有) | `/rooms/{room_id}/categories/{category_id}` | DELETE | 创建者删除分类 |

#### 前端修改（3 个 API 文件 + 1 个页面文件）

| 前端文件 | 修改内容 |
|---------|---------|
| `src/api/tab.ts` | `createRoomTab`、`getRoomTabList`、`uploadTabImage` 路径改为 `/rooms/...`；`updateRoomTab`、`deleteRoomTab` 新增 `roomId` 参数 + 路径改为 `/rooms/...` |
| `src/api/roomCategories.ts` | `setRoomCategories`、`removeRoomCategory` 路径改为 `/rooms/...` |
| `src/api/brand.ts` | `bindRoomBrands`、`associateRoomBrands` 路径改为 `/rooms/...` |
| `src/pages/app/live-manage/edit.vue` | `updateRoomTab` 调用处新增 `roomId` 参数 |

#### 测试结果

| 测试 | 用例数 | 结果 |
|------|:------:|:----:|
| 已有集成测试 | 14 | ✅ 全部通过 |
| 后端文件语法检查 | 5 个文件 | ✅ 全部通过 |

### 3.3 阶段B：拆分 `/admin` 语义冲突的端点（待确认后实施）

**风险**：🟡 中-高 — 涉及 API 权限收紧，需先确认外部调用方是否使用创建者 Token 访问 `/admin/` 路径。

**前置条件**：
1. 阶段A 完成并验证通过
2. 确认外部管理后台是否使用创建者 Token 调用 `/admin/rooms/{id}/tabs`、`/admin/rooms/{id}/categories`、`/admin/rooms/{id}/brands`
3. 如是，先切换外部前端到新路径，再收紧

#### 改造原则

- `/admin/` 路径下的接口统一**仅 ADMIN/SUPERADMIN 可调用**
- 房间创建者可操作的功能迁移到 `/rooms/` 路径下
- 原有 `/admin/` 端点保留（权限收紧），前端可按角色切换调用路径

#### ① Tab 管理改造

**现状（5 个端点在 admin_tab_router，注册于 /admin 前缀）：**

| 当前 URL | 当前权限 |
|---------|---------|
| `GET /admin/rooms/{id}/tabs` | ADMIN 或创建者 |
| `POST /admin/rooms/{id}/tabs/image` | ADMIN 或创建者 |
| `POST /admin/rooms/{id}/tabs` | ADMIN 或创建者 |
| `PATCH /admin/tabs/{id}` | ADMIN 或创建者 |
| `DELETE /admin/tabs/{id}` | ADMIN 或创建者 |

**改造后：**

| 路径 | 调用者 | 权限 |
|------|-------|------|
| `GET /admin/rooms/{id}/tabs` **(保留)** | 管理后台 | **仅 ADMIN/SUPERADMIN** |
| `POST /admin/rooms/{id}/tabs` **(保留)** | 管理后台 | **仅 ADMIN/SUPERADMIN** |
| `PATCH /admin/tabs/{id}` **(保留)** | 管理后台 | **仅 ADMIN/SUPERADMIN** |
| `DELETE /admin/tabs/{id}` **(保留)** | 管理后台 | **仅 ADMIN/SUPERADMIN** |
| **新增** `POST /rooms/{id}/tabs` | 房间创建者 | ADMIN 或创建者 |
| **新增** `PATCH /rooms/{room_id}/tabs/{tab_id}` | 房间创建者 | ADMIN 或创建者 |
| **新增** `DELETE /rooms/{room_id}/tabs/{tab_id}` | 房间创建者 | ADMIN 或创建者 |

> `POST /admin/rooms/{id}/tabs/image` 属于管理端功能，保持仅 ADMIN 可调。

**新增 Router**：在 `live_features.py` 中添加 `room_tab_router`，注册到 `api.py` 的 `"/rooms"` 前缀下。

#### ② 分类管理改造

**现状（2 个端点在 live_room_categories_admin_router，注册于 /admin/rooms 前缀）：**

| 当前 URL | 当前权限 |
|---------|---------|
| `POST /admin/rooms/{id}/categories` | ADMIN 或创建者 |
| `DELETE /admin/rooms/{id}/categories/{cid}` | ADMIN 或创建者 |

**改造后：**

| 路径 | 权限 |
|------|------|
| `POST /admin/rooms/{id}/categories` **(保留)** | **仅 ADMIN/SUPERADMIN** |
| `DELETE /admin/rooms/{id}/categories/{cid}` **(保留)** | **仅 ADMIN/SUPERADMIN** |
| **新增** `POST /rooms/{id}/categories` | ADMIN 或创建者 |
| **新增** `DELETE /rooms/{id}/categories/{cid}` | ADMIN 或创建者 |

> `GET /rooms/{id}/categories` 已存在（公开查询），无需变动。

#### ③ 品牌绑定改造

**现状（1 个端点在 brand.router，路径含 /admin）：**

| 当前 URL | 当前权限 |
|---------|---------|
| `POST /admin/rooms/{id}/brands` | ADMIN 或创建者 |

**改造后：**

| 路径 | 权限 |
|------|------|
| `POST /admin/rooms/{id}/brands` **(保留)** | **仅 ADMIN/SUPERADMIN** |
| **新增** `POST /rooms/{id}/brands` | ADMIN 或创建者 |

> `GET /rooms/{id}/brands` 已存在（公开查询），无需变动。

---

## 四、与现有规范性文档的关系

### 4.1 与 `API路由规范统一方案.md` 的关系

该文档（`API路由规范统一方案.md`）已定义了路由命名规范，其中对 `content_management`、`brand` 等模块的改造重点在 **URL 路径格式**（去除 admin 后缀、拆分 Router）。

本方案的改造重点在 **权限语义**（让 `/admin/` 路径的接口真正仅 ADMIN 可调）。

两者互不冲突，可以并行执行，也可以在路由格式改造完成后执行本方案。建议流程：

```
API路由规范统一方案（先做路径格式改造）
        ↓
Admin接口权限规范化方案（再做权限语义统一）
```

### 4.2 重叠部分

两个方案都涉及 `content_management.py` 和 `brand.py`。建议按以下顺序协调：

1. 先按 `API路由规范统一方案` 拆分 Router、调整路径格式
2. 再按本方案收敛权限校验、拆分创建者/ADMIN 路径

---

## 五、改动量预估

| 阶段 | 内容 | 涉及文件 | 预估改动量 | 风险 |
|:----:|------|:--------:|:---------:|:----:|
| 阶段A | 新建 `permissions.py` + 替换全部 18 处调用 | 新建 1 + 修改 9 | 中 | 🟢 低 |
| 阶段B-① | Tab 管理端点拆分 | 2（端点 + api.py） | 中 | 🟡 中-高 |
| 阶段B-② | 分类管理端点拆分 | 2（端点 + api.py） | 中 | 🟡 中-高 |
| 阶段B-③ | 品牌绑定端点拆分 | 2（端点 + api.py） | 中 | 🟡 中-高 |
| — | 补充/更新测试 | 测试文件 | 中 | — |
| — | **前端适配** | 前端项目（独立 repo） | **需沟通** | 🔴 |

---

## 六、风险分析与执行顺序

### 6.1 三类改造的风险评估

#### 类别 A：纯内部重构（阶段A）— 🟢 低风险

| 维度 | 评估 |
|------|------|
| API 变更 | **无** — 不改变任何 URL 路径和权限行为 |
| 前端影响 | **无** — 纯后端内部实现替换 |
| 出错后果 | 参数传错或异常类型不匹配 → 仅影响后端，测试可发现 |
| 验证方式 | 运行现有测试，行为不变则全过 |
| 回退代价 | 逐文件或整体回退，无数据迁移 |

#### 类别 B：端点权限收紧（阶段B 中收紧部分）— 🟡 中-高风险

| 维度 | 评估 |
|------|------|
| API 变更 | **有** — 原有 `/admin/...` 端点从"ADMIN 或创建者"变为"仅 ADMIN" |
| 前端影响 | **不确定** — 如果外部管理后台用**创建者 Token** 调用这些路径，收紧后会返回 403 |
| 出错后果 | 创建者无法在管理后台管理自己的 Tab/分类/品牌 |
| 前置条件 | **需先确认**外部管理后台是否使用创建者角色调用 `/admin/` 路径 |

#### 类别 C：新增创建者端点（阶段B 中新增部分）— 🟢 低风险

| 维度 | 评估 |
|------|------|
| API 变更 | 仅新增路径，不影响已有路径 |
| 出错后果 | 新路径不通最多是新功能不可用，不影响旧流程 |

### 6.2 推荐执行流程

```
阶段A ──── 纯重构，现在就做
  │
  │  完成后运行全量测试，验证无回归
  │
  ▼
确认外部调用方 ──── 查找谁调用了 /admin/rooms/{id}/tabs 等端点
  │                 确认是否使用创建者 Token
  │
  ▼
阶段B ──── 先切换前端 → 再收紧权限 → 补充测试
```

### 6.3 关键决策点

阶段B 开始前必须确认：

1. **管理后台前端在哪个 repo？**（当前 `frontend/` 目录无 admin 调用）
2. **前端调用 `/admin/rooms/{id}/tabs`、`/admin/rooms/{id}/categories`、`/admin/rooms/{id}/brands` 时，是否可能传入非 ADMIN 角色的 Token？**
3. **如果是，这些调用对应什么业务场景？**（如"医生在自己直播间后台管理 Tab"）

---

## 七、注意事项

### 7.1 向后兼容

阶段B 中新增端点与原有端点**并存**，原有端点只是收紧了权限。已授权的 ADMIN 用户不受影响，创建者需要切换到新路径。

### 7.2 测试影响

`Tab功能测试实现与结果文档.md` 中记录了创建者权限测试用例（如 `test_upload_image_owner_success`），阶段B 改造后这些用例应改为调用新的非 admin 路径，同时补充新端点的测试。

### 7.3 与 `API路由规范统一方案.md` 的关系

该文档定义了路由命名规范（URL 路径格式改造），本方案定义权限语义规范。两者互不冲突，建议先做完本方案的阶段A，再根据实际进度协调两个方案的阶段B。
