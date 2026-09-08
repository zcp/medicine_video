# P1-3 Owner 路由合并 + 硬编码下沉 — 代码生成提示词

**版本**: V1.0
**创建日期**: 2026-07-20
**基于设计文档**: `app修改记录/权限体系优化设计文档_实施版.md` §6.3 + §6.3.1
**依赖**: P1-1（deps.py role 规范化）+ P1-2（守卫函数统一化）已完成
**目标文件**: 修改 4 个文件 + 前端配合
**改动模式**: 删除冗余 + 下沉鉴权

---

## 1. 角色定义 (Role Definition)

你是一名精通 FastAPI 路由设计和 RESTful API 架构的资深后端架构师。你的核心任务是**消除 Owner 路由冗余 + 删除 endpoint 层硬编码的 Admin 角色检查**。

**背景**：项目中存在 3 个模块共 7 个 Owner 端点（`room_tab_router` × 4、`room_brand_owner_router` × 1、`room_category_owner_router` × 2），它们与对应的 Admin 端点功能完全相同（调用同一个 Service 方法），只是 URL 和权限检查方式不同。同时，8 个 Admin 端点在 endpoint 层硬编码了 `if role not in ('ADMIN', 'SUPERADMIN')`，与 Service 层的守卫函数形成"双层检查"——这些硬编码阻挡了 Owner 用户，导致不得不另写一套 Owner 路由。

**改造后**：每个写操作只有 1 个 URL、1 份代码、1 个权限判断点（Service 层守卫函数）。`/admin/` 前缀的语义从"调用者必须是 Admin"变为"这是一个管理类操作"。

**三个必须**：
- 必须删除 7 个 Owner 端点（删除代码 + api.py 路由注册）
- 必须删除 8 处 endpoint 层硬编码的 Admin 角色检查
- 必须不改变任何 Service 层逻辑（Service 层的 `check_room_owner_or_admin` 已经能正确处理 Admin+Owner）

---

## 2. 任务目标 (Task Objective)

### 2.1 改动的文件（4 个）

| 文件 | 改动类型 | 说明 |
|:-----|:--------|:-----|
| `app/api/v1/endpoints/live_features.py` | **删除 + 修改** | 删除 4 个 Owner 端点 + 删除 5 处 Admin 硬编码 |
| `app/api/v1/endpoints/brand.py` | **删除 + 修改** | 删除 1 个 Owner 端点 + 删除 1 处 Admin 硬编码 |
| `app/api/v1/endpoints/content_management.py` | **删除 + 修改** | 删除 2 个 Owner 端点 + 删除 2 处 Admin 硬编码 |
| `app/api/v1/api.py` | **删除 3 行注册** | 删除 3 个 Owner 路由器的注册代码 |

### 2.2 前端配合（不改后端文件，但需提供对照表）

前端需将 7 个 Owner URL 切换到对应的 Admin URL（见 §5 对照表）。

### 2.3 禁止事项

- ❌ 不修改 `app/services/` 下的任何文件
- ❌ 不修改 `app/core/` 下的任何文件
- ❌ 不修改 `app/crud/` 下的任何文件
- ❌ 不修改 `app/models/` 下的任何文件
- ❌ 不改动 admin 路由器的 GET 端点（`list_room_tabs` 是管理后台查全量，与 Owner 路由无关）
- ❌ 不改动 public 路由器（`public_tab_router`、`brand_public_router`、`live_room_categories_router`）
- ❌ 不改动 Service 层函数的签名和逻辑

---

## 3. 核心上下文 (Core Context)

### 3.1 正确模式：Session CRUD（一份代码，Service 鉴权）

```python
# room.py — Session 创建端点的"正确模式"
# 一套路由 + 端点层不检查角色 + Service 层守卫函数

@room_router.post("/{room_id}/sessions")
async def create_scheduled_session(
    room_id: uuid.UUID,
    scheduled_session_in: ScheduledSessionCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    # 没有 endpoint 层的 if role not in ('ADMIN', 'SUPERADMIN')
    user_id = uuid.UUID(current_user["user_id"])
    role = current_user.get("role", "REGULAR")
    try:
        new_session = await service.create_scheduled_session(
            room_id=room_id, session_in=scheduled_session_in,
            user_id=user_id, role=role
        )
        # ... 响应构建
    except PermissionDeniedException as e:
        return JSONResponse(status_code=403, content=...)
```

**Service 层**的 `create_scheduled_session` 内部调用：
```python
check_room_owner_or_admin(room, user_id, role)  # Admin 放行，Owner 放行，其余 403
```

**改造目标**：Tab/品牌/分类 的 Admin 端点采用同样的模式。

### 3.2 当前错误模式：Admin 硬编码 + Owner 路由

以 `brand.py` 的**品牌绑定**为例，当前两套路由对比：

**Admin 路由**（`brand.py:580`）：
```python
@brand_admin_router.post("/rooms/{room_id}/brands")
async def bind_room_brands(...):
    role = current_user.get("role", "REGULAR").upper()
    # ← 第 1 层：endpoint 硬编码（阻挡 Owner）
    if role not in ('ADMIN', 'SUPERADMIN'):
        return JSONResponse(status_code=403, ...)
    try:
        # ← 第 2 层：Service 守卫函数（只有 Admin 能达到这里）
        result = await brand_service.bind_room_brands(...)
```

**Owner 路由**（`brand.py:669`）：
```python
@room_brand_owner_router.post("/rooms/{room_id}/brands")
async def bind_room_brands_as_owner(...):
    # 没有硬编码，直接进 Service
    result = await brand_service.bind_room_brands(...)
    # ↑ Service 内部有 check_room_owner_or_admin
```

**问题**：
1. Admin 端点的 endpoint 层硬编码把 Owner 挡死了，Owner 只能走 Owner 路由
2. 两套代码做同一件事，~310 行重复代码
3. 公众号关联写操作**只有 Admin 路由**，Owner 无法管理（缺口）

### 3.3 Owner 端点清单（7 个，全部需删除）

| 模块 | 路由器 | 端点函数 | 文件行号 | API 路径 |
|:----|:------|:--------|:--------:|:---------|
| Tab | `room_tab_router` | `upload_tab_image_as_owner` | `live_features.py:450` | `POST /rooms/{room_id}/tabs/image` |
| Tab | `room_tab_router` | `create_room_tab_as_owner` | `live_features.py:488` | `POST /rooms/{room_id}/tabs` |
| Tab | `room_tab_router` | `update_room_tab_as_owner` | `live_features.py:559` | `PATCH /rooms/{room_id}/tabs/{tab_id}` |
| Tab | `room_tab_router` | `delete_room_tab_as_owner` | `live_features.py:630` | `DELETE /rooms/{room_id}/tabs/{tab_id}` |
| 品牌 | `room_brand_owner_router` | `bind_room_brands_as_owner` | `brand.py:669` | `POST /rooms/{room_id}/brands` |
| 分类 | `room_category_owner_router` | `set_live_room_categories_as_owner` | `content_management.py:725` | `POST /rooms/{room_id}/categories` |
| 分类 | `room_category_owner_router` | `delete_live_room_category_as_owner` | `content_management.py:770` | `DELETE /rooms/{room_id}/categories/{category_id}` |

### 3.4 Admin 硬编码清单（8 处，全部需删除）

| # | 文件 | 行号 | 当前硬编码 |
|:-:|:----|:----:|:----------|
| 1 | `live_features.py` | L83 | `list_room_tabs`: `if role_str not in ('ADMIN', 'SUPERADMIN'):` |
| 2 | `live_features.py` | L165 | `upload_tab_image`(admin): `if role_str not in ('ADMIN', 'SUPERADMIN'):` |
| 3 | `live_features.py` | L216 | `create_room_tab`: `if role_str not in ('ADMIN', 'SUPERADMIN'):` |
| 4 | `live_features.py` | L308 | `update_room_tab`: `if role_str not in ('ADMIN', 'SUPERADMIN'):` |
| 5 | `live_features.py` | L395 | `delete_room_tab`: `if role_str not in ('ADMIN', 'SUPERADMIN'):` |
| 6 | `brand.py` | L594 | `bind_room_brands`: `if role not in ('ADMIN', 'SUPERADMIN'):` |
| 7 | `content_management.py` | L826 | `set_live_room_categories`: `if role not in ('ADMIN', 'SUPERADMIN'):` |
| 8 | `content_management.py` | L878 | `delete_live_room_category`: `if role not in ('ADMIN', 'SUPERADMIN'):` |

### 3.5 api.py 中需删除的 3 处 Owner 路由器注册

| 行号 | 当前代码 |
|:----:|:---------|
| L87-92 | `api_router.include_router(live_features.room_tab_router, prefix="/rooms", ...)` |
| L166-171 | `api_router.include_router(content_management.room_category_owner_router, prefix="/rooms", ...)` |
| L217-222 | `api_router.include_router(brand.room_brand_owner_router, prefix="/rooms", ...)` |

### 3.6 保存的路由器定义

删除 Owner 端点后，**路由器的定义行本身也要删除**：

| 文件 | 行号 | 定义代码 |
|:----|:----:|:---------|
| `live_features.py` | L59 | `room_tab_router = APIRouter(tags=["Room Owner - Tabs"])` |
| `brand.py` | L35 | `room_brand_owner_router = APIRouter()` |
| `content_management.py` | L38 | `room_category_owner_router = APIRouter(tags=["Content Management - 直播间分类-创建者"])` |

---

## 4. 架构约束 (Architecture Constraints)

### 4.1 核心原则

- **Endpoint 层不做角色检查** — 只做认证（提取 user_id + role），不判断 role 值
- **Service 层单点鉴权** — `check_room_owner_or_admin`、`check_admin_permission` 等守卫函数在 Service 层调用
- **这不是放宽权限** — 权限检查从 endpoint 层的一刀切 Admin Only 改为 Service 层的精确判断 Admin+Owner，非 Owner 的 Regular 用户仍然被 Service 层拒绝（403），安全强度不变

### 4.2 `/admin/` 前缀语义变更

| 改造前 | 改造后 |
|--------|--------|
| `/admin/` = "调用者必须是 ADMIN" | `/admin/` = "这是一个管理类操作"（Service 层判断 Admin 或 Owner） |

**说明**：当 Owner 用户调用 `POST /admin/rooms/{id}/tabs` 时，endpoint 层不拦截，Service 层的 `check_room_owner_or_admin` 会放行（因为他是房间创建者）。这**不是**安全降级——Service 层的守卫函数本身就是项目的标准权限判断方式（与 Session CRUD 一致）。

### 4.3 删除注意事项

- 删除端点时，需要连带删除该端点函数的**完整定义**（从 `@router.xxx(...)` 到函数体的最后一个 `except` 块或 `return`）
- 删除后需检查文件中是否还有对其他已删除函数的引用（如 import 是否需要清理）
- api.py 中的 `include_router` 按行删除，注意保留前后的空行和注释

---

## 5. 代码生成要求 (Code Generation Requirements)

### 5.1 `live_features.py` 的修改

**删除区域 A**：`room_tab_router` 路由器定义（L59）
```python
# 删除这行：
room_tab_router = APIRouter(tags=["Room Owner - Tabs"])
```

**删除区域 B**：4 个 Owner 端点（每个端点的函数定义 + @router 装饰器）

| 删除范围 | 函数名 | 备注 |
|:--------:|:------|:-----|
| L448-486 | `upload_tab_image_as_owner` | 含空行分隔的区域 |
| L488-556 | `create_room_tab_as_owner` | 完整函数，约 68 行 |
| L559-627 | `update_room_tab_as_owner` | 完整函数，约 68 行 |
| L630-688 | `delete_room_tab_as_owner` | 完整函数，约 58 行 |

**删除区域 C**：5 处 Admin 端点硬编码

每处需要删除的内容模式：
```python
    # ← 新增：Admin 专用端点，仅 ADMIN/SUPERADMIN 可调用
    if role_str not in ('ADMIN', 'SUPERADMIN'):
        logger.warning(f"非管理员尝试...: user_id={user_id}, role={role_str}")
        return JSONResponse(
            status_code=403,
            content=error_response(code=3003, message="需要管理员权限")
        )
```

具体位置：

| 端点函数 | 硬编码行号 | 删除的行数 |
|:--------|:---------:|:----------:|
| `list_room_tabs` | L82-88 | 7 行 |
| `upload_tab_image`(admin) | L164-170 | 7 行（需要确认实际行号） |
| `create_room_tab` | L215-221 | 7 行 |
| `update_room_tab` | L307-313 | 7 行 |
| `delete_room_tab` | L394-400 | 7 行 |

**注意**：删除硬编码块后，`role_str` 可能不再被使用（如果后续逻辑不再引用它）。如果 `role_str` 只用于硬编码检查，可一并删除定义它的行。但如果后续代码仍使用 `role_str`（如枚举转换 `LiveRoomMessageUserRole[role_str]`），则保留 `role_str` 的定义。

### 5.2 `brand.py` 的修改

**删除区域 A**：路由器定义（L35）
```python
# 删除这行：
room_brand_owner_router = APIRouter()
```

**删除区域 B**：Owner 端点（L669-710）
```python
@room_brand_owner_router.post("/rooms/{room_id}/brands")
async def bind_room_brands_as_owner(...):
    """绑定直播间品牌（房间创建者用）"""
    # ... 完整函数体，约 42 行
```

**删除区域 C**：Admin 端点 `bind_room_brands` 的硬编码（L593-599）
```python
    # ← 新增：Admin 专用端点，仅 ADMIN/SUPERADMIN 可调用
    if role not in ('ADMIN', 'SUPERADMIN'):
        logger.warning(f"非管理员尝试绑定直播间品牌: user_id={user_id_for_logging}, role={role}")
        return JSONResponse(
            status_code=403,
            content=error_response(code=3003, message="需要管理员权限")
        )
```

### 5.3 `content_management.py` 的修改

**删除区域 A**：路由器定义（L38）
```python
# 删除这行：
room_category_owner_router = APIRouter(tags=["Content Management - 直播间分类-创建者"])
```

**删除区域 B**：2 个 Owner 端点（L725-767 + L770-804）

| 删除范围 | 函数名 | 行数 |
|:--------:|:------|:----:|
| L725-767 | `set_live_room_categories_as_owner` | ~43 行 |
| L770-804 | `delete_live_room_category_as_owner` | ~35 行 |

**删除区域 C**：Admin 端点的 2 处硬编码

| 端点函数 | 硬编码行号 | 行数 |
|:--------|:---------:|:----:|
| `set_live_room_categories` | L825-831 | 7 行 |
| `delete_live_room_category` | L877-883 | 7 行 |

### 5.4 `app/api/v1/api.py` 的修改

删除 3 处 `include_router`：

```python
# 删除以下 3 个块：

# 5.1 直播间-Tab管理：房间创建者 POST/PATCH/DELETE /api/v1/rooms/{room_id}/tabs
api_router.include_router(
    live_features.room_tab_router,
    prefix="/rooms",
    tags=["房间-Tab管理-创建者"]
)

# 11.3 直播间-分类：房间创建者 POST/DELETE /api/v1/rooms/{room_id}/categories
api_router.include_router(
    content_management.room_category_owner_router,
    prefix="/rooms",
    tags=["内容管理-直播间分类-创建者"]
)

# 14.1 品牌-房间创建者：POST /api/v1/rooms/{room_id}/brands
api_router.include_router(
    brand.room_brand_owner_router,
    prefix="/rooms",
    tags=["品牌管理-房间创建者"]
)
```

**注意**：删除后检查 `api.py` 的 import 部分是否有 `live_features`、`content_management`、`brand` 的引用——这些 import 仍然被其他路由器使用（`live_features.admin_tab_router`、`content_management.content_admin_router`、`brand.brand_admin_router` 等），所以不要删除 import。

### 5.5 前端 URL 对照表

以下为前端需要切换的 7 个 URL：

| # | 旧 URL（要删除的 Owner 端点） | 新 URL（改造后的 Admin 端点） | HTTP 方法 |
|:-:|:----------------------------|:-----------------------------|:---------:|
| 1 | `/api/v1/rooms/{room_id}/tabs/image` | `/api/v1/admin/rooms/{room_id}/tabs/image` | POST |
| 2 | `/api/v1/rooms/{room_id}/tabs` | `/api/v1/admin/rooms/{room_id}/tabs` | POST |
| 3 | `/api/v1/rooms/{room_id}/tabs/{tab_id}` | `/api/v1/admin/tabs/{tab_id}` | PATCH |
| 4 | `/api/v1/rooms/{room_id}/tabs/{tab_id}` | `/api/v1/admin/tabs/{tab_id}` | DELETE |
| 5 | `/api/v1/rooms/{room_id}/brands` | `/api/v1/admin/rooms/{room_id}/brands` | POST |
| 6 | `/api/v1/rooms/{room_id}/categories` | `/api/v1/admin/rooms/{room_id}/categories` | POST |
| 7 | `/api/v1/rooms/{room_id}/categories/{category_id}` | `/api/v1/admin/rooms/{room_id}/categories/{category_id}` | DELETE |

**注意**：Tab 的 PATCH/DELETE 在新 URL 中**没有 room_id 参数**（路径为 `/admin/tabs/{tab_id}`），前端传参时需要注意。

---

## 6. 完整性检查清单 (Completeness Checklist)

### 6.1 编译验证

- [ ] `live_features.py` 不再引用 `room_tab_router` 路由器和 `upload_tab_image_as_owner`、`create_room_tab_as_owner`、`update_room_tab_as_owner`、`delete_room_tab_as_owner`
- [ ] `brand.py` 不再引用 `room_brand_owner_router` 和 `bind_room_brands_as_owner`
- [ ] `content_management.py` 不再引用 `room_category_owner_router` 和 `set_live_room_categories_as_owner`、`delete_live_room_category_as_owner`
- [ ] `api.py` 不再引用 `room_tab_router`、`room_brand_owner_router`、`room_category_owner_router`
- [ ] 无 `import room_tab_router`、`import room_brand_owner_router`、`import room_category_owner_router` 残留（在 api.py 中）
- [ ] 无 `from app.core.permissions import check_admin_permission` 等在文件顶部出现的新导入（用于替换硬编码）

### 6.2 全库 grep 验证

```bash
# 确认 Owner 路由器已从全库消失
grep -rn "room_tab_router" app/
grep -rn "room_brand_owner_router" app/
grep -rn "room_category_owner_router" app/
# 预期输出：空

# 确认 Admin 硬编码已从 endpoint 层消失
grep -rn "if role.*not in.*ADMIN.*SUPERADMIN" app/api/v1/endpoints/
# 预期输出：空
```

### 6.3 权限回归测试

- [ ] **匿名用户**查公开房间 Tab → 200（走的 `public_tab_router`，不受影响）
- [ ] **Owner 用户**通过 Admin URL `POST /admin/rooms/{id}/tabs` 管理自己的 Tab → 200（Service 层 `check_room_owner_or_admin` 放行）
- [ ] **Owner 用户**通过 Admin URL `POST /admin/rooms/{id}/brands` 绑定自己房间的品牌 → 200
- [ ] **Owner 用户**通过 Admin URL `POST /admin/rooms/{id}/categories` 设置自己房间的分类 → 200
- [ ] **非 Owner 的 Regular 用户**通过 Admin URL 操作他人房间 → 403（Service 层拒绝）
- [ ] **Admin 用户**通过 Admin URL 操作任意房间 → 200

### 6.4 代码量评估

- 删除 ~310 行重复代码（Tab ~200 + 品牌 ~42 + 分类 ~70）
- 删除 ~56 行 endpoint 层硬编码（7 处 × ~8 行）
- 删除 ~13 行 api.py 路由器注册
- **总计删除 ~379 行冗余代码**

### 6.5 其他注意事项

- [ ] 公众号关联写操作（`admin_rooms_official_accounts_router`）的 Service 层已确认有 `check_room_owner_or_admin`，Owner 用户现在可以通过 Admin URL `POST /admin/rooms/{id}/official-accounts` 管理公众号关联（之前 Owner 无法操作此功能）
