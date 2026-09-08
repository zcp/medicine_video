# LiveCore 权限体系全面分析报告（代码验证版）

**分析日期**: 2026-07-17
**分析方法**: 逐行阅读全部 endpoint 文件和 service 文件、permissions.py、deps.py 并与设计文档对照
**已比对的代码文件**:
- `app/core/auth.py`, `app/core/deps.py`, `app/core/permissions.py` — 认证和权限基础设施
- `app/api/v1/endpoints/room.py`, `session.py`, `live_features.py`, `batch_import.py`, `brand.py`, `experts.py`, `content_management.py`, `topic.py`, `homepage_search.py`, `internal.py`, `user_behavior.py`, `user_preference_notification.py` — 全部 endpoint 层
- `app/services/room_service.py`, `session_service.py`, `live_features_service.py`, `batch_import.py`, `brand_service.py`, `expert_service.py`, `content_management_service.py`, `homepage_search_service.py`, `srs_callback_service.py`, `user_behavior_service.py`, `user_preference_notification_service.py`, `session_import.py` — 全部 service 层
- `app/crud/room.py` — CRUD 层权限过滤

---

## 一、权限等级体系（代码实际实现）

### 1.1 身份模型实现

代码在 `app/core/auth.py` 和 `app/core/deps.py` 中实现了完整的双轨鉴权：

```python
# app/core/deps.py

# 模式 A: Strict Auth — 无Token→401, Token无效→401
async def get_current_user(token: Dict = Depends(JWTAuth.get_current_user)) -> Dict:
    return token

# 模式 B: Optional Auth — 无Token→None, Token无效→401
async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[Dict]:
    if not credentials or not credentials.credentials:
        return None  # 匿名用户
    try:
        user = JWTAuth.verify_token(credentials.credentials)
        return user
    except HTTPException:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
```

**JWT Payload 字段（实际定义在 auth.py:38）**:
- `user_id`：用户的 public_id（UUID 字符串），代码中几乎所有地方都通过 `current_user["user_id"]` 提取。注意部分 endpoint（如 live_features.py、homepage_search.py）会 fallback 支持 `sub` 字段：`current_user.get("user_id") or current_user.get("sub")`
- `role`：角色字符串（如 "REGULAR"、"ADMIN"、"SUPERADMIN"），代码中统一做 `.upper()` 处理

### 1.2 实际启用的认证模式分配（逐 endpoint 验证）

| 认证模式 | 依赖函数 | 实际使用的 Endpoint |
|---------|---------|-------------------|
| **Strict Auth** | `Depends(get_current_user)` | Room create/patch/delete/cover, Session create/patch/delete, Tab admin CRUD, Tab owner CRUD, Message create, Batch import, Brand admin CRUD, Expert admin CRUD, Expert follow/unfollow, User behavior 全部, User preference 全部, Topic admin CRUD, Homepage FE admin CRUD |
| **Optional Auth** | `Depends(get_current_user_optional)` | Room list/detail/sub-venues, Session detail/list, Message list, Tab public list, Brand public list/detail, Expert public list/detail/sessions, Room brands public, Search, Topic public list |
| **无认证** | 无 Depends | SRS internal callback, Homepage rooms (公开), Featured content public list, Room favorite check (部分) |

---

## 二、公共权限守卫函数（`app/core/permissions.py` 实际实现）

这是整个权限体系的**核心单点**，被所有 Service 层复用：

```python
# app/core/permissions.py

def check_room_owner_or_admin(room, user_id, role):
    """写操作权限：Admin通过 / Owner通过 / 其他→403"""
    if role in ('ADMIN', 'SUPERADMIN'):
        return
    if room.user_id == user_id:
        return
    raise PermissionDeniedException("需要管理员或房间创建者权限")

def check_room_visibility(room, user_id, role):
    """读操作可见性：Public通过 / Admin通过 / Owner通过 / 无权限→404"""
    if not room.is_private:
        return
    if not user_id:
        raise NotFoundException("Room not found")       # 404伪装
    if role in ('ADMIN', 'SUPERADMIN'):
        return
    if room.user_id == user_id:
        return
    raise NotFoundException("Room not found")           # 404伪装
```

**关键观察**：这些守卫函数中完全没有 `MODERATOR` 角色的特殊处理。MODERATOR 在代码中与 REGULAR 完全等价（走 else 分支或 `room.user_id == user_id` 的 Owner 判断）。这与设计文档的"MODERATOR 暂不启用"说法一致。

---

## 三、逐模块代码-文档一致性验证

### 3.1 直播房间模块

**Endpoint 文件**: `app/api/v1/endpoints/room.py`
**Service 文件**: `app/services/room_service.py`

| 接口 | Auth模式(代码) | 代码权限实现 | 与文档一致? |
|------|:---:|------|:---:|
| `POST /api/v1/rooms` | Strict | API层提取 user_id+role, Service层 `create_new_room()` 接受但不额外校验(创建者自动成为Owner) | ✅ |
| `GET /api/v1/rooms` | **Optional** | 代码第111行：`Depends(get_current_user_optional)`, 支持 `owner_only` 参数(第109行/第171行), CRUD层 `get_multi_and_total` SQL过滤 is_private | ✅ |
| `GET /api/v1/rooms/{id}` | **Optional** | 代码第302行：Optional Auth, Service调用 `_check_room_visibility`→委托给 `check_room_visibility()`, Private无权限返回404 | ✅ |
| `PATCH /api/v1/rooms/{id}` | Strict | Service调用 `_check_write_permission`→`check_room_owner_or_admin()`, PermissionDeniedException→403, ActionForbiddenException(正在直播)→403 | ✅ |
| `DELETE /api/v1/rooms/{id}` | Strict | 同上, 额外处理 DatabaseIntegrityException→409 | ✅ |
| `POST /api/v1/rooms/{id}/cover` | Strict | Service调用 `_check_write_permission`, PermissionDeniedException→403 | ✅ |
| `GET /api/v1/rooms/{id}/sub-venues` | **Optional** | 代码第518行：Optional Auth, Service 检查主会场可见性 | ✅ |
| `GET /api/v1/rooms/{id}/stream_key` | **未实现独立端点** | stream_key 内嵌在 `GET /api/v1/rooms/{id}` 响应中(line 339), 未做脱敏 —— **这是一个安全风险** | ❌ |

**⚠️ 重大发现**：stream_key（推流密钥）在 `get_room` 接口的响应中直接返回（第339行 `"stream_key": room.stream_key`），但该接口使用的是 Optional Auth。这意味着匿名用户也能看到公开房间的 stream_key。这与设计文档中的"推流密钥严禁匿名"的要求直接矛盾！

**`get_my_rooms` 接口**: 代码第225-295行定义了 `users_me_rooms_router.get("/rooms")`，使用 Strict Auth + `owner_only=True`，仅返回当前用户创建的房间。这是管理后台 RoomList 视图的实现。

### 3.2 直播场次模块

**Endpoint 文件**: `app/api/v1/endpoints/session.py` + `room.py`（部分）
**Service 文件**: `app/services/session_service.py`

| 接口 | Auth模式(代码) | 代码权限实现 | 与文档一致? |
|------|:---:|------|:---:|
| `POST /api/v1/rooms/{id}/sessions` | Strict (在 room.py 576行) | Service 先查 Room→调用 `_check_write_permission`(→`check_room_owner_or_admin`), 再创建 Session | ✅ |
| `GET /api/v1/rooms/{id}/sessions` | **Optional** (在 room.py 646行) | Service 先查 Room→调用 `_check_room_visibility`(→`check_room_visibility`), 再查 Session 列表。**Session 继承 Room 可见性** | ✅ |
| `GET /api/v1/sessions/{id}` | **Optional** (session.py 43行) | Service 查 Session→JOIN Room→调用 `_check_room_visibility` | ✅ |
| `PATCH /api/v1/sessions/{id}` | Strict (session.py 114行) | Service 查 Session+Room→调用 `_check_write_permission`→`check_room_owner_or_admin` | ✅ |
| `DELETE /api/v1/sessions/{id}` | Strict (session.py 188行) | 同上 | ✅ |

**验证结论**：Session 模块权限实现与文档完全一致。Session 通过 JOIN Room 后调用 `check_room_visibility` 和 `check_room_owner_or_admin` 实现权限继承。

### 3.3 Tab 管理模块 ⚠️ 代码与文档存在重要差异

**Endpoint 文件**: `app/api/v1/endpoints/live_features.py`
**Service 文件**: `app/services/live_features_service.py`

**实际代码中 Tab 有 3 套路由，权限各不相同**：

| 路由 | 路由器 | 权限实现 | 访问者 |
|------|-------|---------|-------|
| `GET /api/v1/admin/rooms/{id}/tabs` | `admin_tab_router` | **Admin Only** (代码76-88行：`if role_str not in ('ADMIN','SUPERADMIN'): return 403`) | 仅 ADMIN/SUPERADMIN |
| `POST /api/v1/admin/rooms/{id}/tabs` | `admin_tab_router` | **Admin Only** (代码216-221行：同上) | 仅 ADMIN/SUPERADMIN |
| `PATCH /api/v1/admin/tabs/{id}` | `admin_tab_router` | **Admin Only** (代码308-313行：同上) | 仅 ADMIN/SUPERADMIN |
| `DELETE /api/v1/admin/tabs/{id}` | `admin_tab_router` | **Admin Only** (代码395-400行：同上) | 仅 ADMIN/SUPERADMIN |
| `POST /api/v1/rooms/{id}/tabs` | `room_tab_router` | **Owner+Admin** (Service 调用 `_check_tab_management_permission`→`check_room_owner_or_admin`) | 创建者+Admin |
| `PATCH /api/v1/rooms/{id}/tabs/{tab_id}` | `room_tab_router` | **Owner+Admin** (同上) | 创建者+Admin |
| `DELETE /api/v1/rooms/{id}/tabs/{tab_id}` | `room_tab_router` | **Owner+Admin** (同上) | 创建者+Admin |
| `GET /api/v1/rooms/{id}/tabs` | `public_tab_router` | **Public+Optional** (代码861-877行：`check_room_visibility` 继承 Room 可见性) | 所有人(含匿名) |
| `POST /api/v1/admin/rooms/{id}/tabs/image` | `admin_tab_router` | **Admin Only** | 仅 ADMIN/SUPERADMIN |
| `POST /api/v1/rooms/{id}/tabs/image` | `room_tab_router` | **Owner+Admin** (代码450-486行) | 创建者+Admin |

**⚠️ 代码-文档差异**：

1. **`admin_tab_router` 仍为 Admin Only**：设计文档 v6.1.1 说 Tab 管理权限从 Admin Only 放宽为 Owner+Admin，但 `admin_tab_router` 的4个端点（list/create/update/delete）在 endpoint 层直接硬编码了 `if role_str not in ('ADMIN', 'SUPERADMIN'): return 403`，**绕过了 Service 层的 `_check_tab_management_permission`**。这与文档描述矛盾。

2. **`room_tab_router` 才是真正的 Owner+Admin**：代码确实新增了 `room_tab_router`（第488-688行），其权限调用 `_check_tab_management_permission(room, user_id, role)`，该函数内部委托给 `check_room_owner_or_admin(room, user_id, role)`——即 Admin 全部管理 + Regular 只能管理自己房间的 Tab。

3. **Tab 内容公开端点**：`public_tab_router` 第849-897行，`GET /api/v1/rooms/{id}/tabs` 使用 Optional Auth + `check_room_visibility`，Tab 内容对所有人可见（继承 Room 可见性）。这与文档描述一致。

**结论**：代码中存在**两套平行的 Tab 管理路由**（admin 路由 + room 路由），这在设计文档中没有明确说明。实际权限上，`admin_tab_router` 是严格 Admin Only，`room_tab_router` 是 Owner+Admin，`public_tab_router` 是公开。

### 3.4 留言模块

**Endpoint 文件**: `app/api/v1/endpoints/live_features.py` (第693-845行)
**Service 文件**: `app/services/live_features_service.py` (第319-440行)

| 接口 | Auth模式(代码) | 代码权限实现 | 与文档一致? |
|------|:---:|------|:---:|
| `POST /api/v1/rooms/{id}/messages` | Strict (698行) | Service `create_message()` 第393-424行：1)先查 Room 2)调 `_check_room_visibility` 3)**URL三级过滤** | ✅ |
| `GET /api/v1/rooms/{id}/messages` | **Optional** (790行) | Service `get_messages()` 调 `_check_room_visibility` 继承 Room 可见性 | ✅ |

**URL 过滤三级逻辑（代码 live_features_service.py 第402-424行）**：
1. `is_admin = role in ['ADMIN', 'SUPERADMIN']` → 放行
2. `room.user_id == user_id` → 房间创建者在自己房间允许 URL
3. 其他 Regular → `InvalidParameterException(code=4004)` 拒绝

这与设计文档 v6.1.1 完全一致。

### 3.5 批量导入模块 ⚠️ 代码与文档存在重大矛盾

**Endpoint 文件**: `app/api/v1/endpoints/batch_import.py`
**Service 文件**: `app/services/batch_import.py`

**代码实际权限逻辑**（batch_import.py 第37-82行）：

```python
def _check_admin_role(self, role: str) -> None:
    if role not in ['REGULAR', 'ADMIN', 'SUPERADMIN']:  # ← 函数名叫 admin_role，但实际允许 REGULAR！
        raise PermissionDeniedException("Admin role required")
```

**核心矛盾**：
- **函数名**是 `_check_admin_role`
- **docstring** 写 "管理员角色校验（用于批量导入等后台管理功能）"，"Raises: PermissionDeniedException: 非Admin用户"
- **实际代码逻辑**却是 `role not in ['REGULAR', 'ADMIN', 'SUPERADMIN']`——即允许 REGULAR
- **设计文档 v6.1 最终版** 写 "所有登录用户均可使用"
- **测试代码** 中却有大量测试因 REGULAR 角色触发 403

**结论**：当前代码实际允许 REGULAR 用户批量导入（因为白名单里包含了 'REGULAR'）。这是从原本的 Admin Only 改出来的，但函数名和注释没同步更新，测试代码也未统一。这是一个遗留的技术债务。

### 3.6 品牌模块

**Endpoint 文件**: `app/api/v1/endpoints/brand.py`
**Service 文件**: `app/services/brand_service.py`

品牌有 3 个路由器：

| 路由 | 权限 | 实际验证位置 |
|------|------|------------|
| `brand_public_router` | Public + Optional Auth | 无写操作权限检查 |
| `brand_admin_router` | Strict Auth + `_check_admin_permission` | brand_service.py 第41-52行 |
| `room_brand_owner_router` | Strict Auth + `check_room_owner_or_admin` | brand_service.py 第658行 |

**`_check_admin_permission` 实际代码**（brand_service.py 第41-52行）：
```python
def _check_admin_permission(self, user_role: str) -> None:
    if user_role not in ['ADMIN', 'SUPERADMIN']:
        raise PermissionDeniedException("权限不足，需要管理员权限")
```

品牌模块的所有 CUD 操作（创建、更新、删除品牌、Logo 上传、专题关联）均调用 `_check_admin_permission`，仅限 ADMIN/SUPERADMIN。

**⚠️ 代码-文档差异**：
- 文档之前认为"品牌关联直播间"操作 Regular 可用（通过 `check_room_owner_or_admin`），但实际上 `brand_admin_router` 中有 `bind_room_brands` endpoint（第580-630行）硬编码了 Admin Only 检查：`if role not in ('ADMIN', 'SUPERADMIN'): return 403`
- 同时也存在 `room_brand_owner_router`（第669-710行），它使用 `check_room_owner_or_admin`，允许房间创建者绑定品牌
- **实际结论**：品牌关联直播间有两条路由，Admin Only 路由和 Owner+Admin 路由各一条

### 3.7 专家模块

**Endpoint 文件**: `app/api/v1/endpoints/experts.py`
**Service 文件**: `app/services/expert_service.py`

专家模块有 4 个路由器：

| 路由 | Auth | 专家CUD权限 | 关注权限 |
|------|------|-----------|---------|
| `experts_featured_router` | **无认证** | ❌ | ❌ |
| `experts_public_router` | Optional | ❌ | ❌ (读操作) |
| `experts_admin_router` | Strict + `_check_admin_permission` | ✅ Admin Only | - |
| `experts_user_router` | Strict + `_check_user_resource_permission` | ❌ | ✅ Owner Only |

**`_check_admin_permission` 实际代码**（expert_service.py 第143-155行）：
```python
def _check_admin_permission(self, role: Optional[str]) -> None:
    if role not in ['ADMIN', 'SUPERADMIN']:
        raise PermissionDeniedException("需要管理员权限")
```

**`_check_expert_visibility` 实际代码**（expert_service.py 第184-209行）：
```python
def _check_expert_visibility(self, expert, current_user_id, role):
    if expert is None:
        raise NotFoundException("专家不存在")
    if not expert.is_active and role not in ['ADMIN', 'SUPERADMIN']:
        raise NotFoundException("专家不存在")  # 404伪装（下架专家对非Admin不可见）
```

**专家关注权限**（expert_service.py 第157-182行）：使用 `_check_user_resource_permission`，检查 `resource_owner_id == current_user_id`，Regular 只能操作自己的关注，Admin 可操作所有用户。

### 3.8 内容管理模块（标签/分类/专题）

**Endpoint 文件**: `app/api/v1/endpoints/content_management.py`
**Service 文件**: `app/services/content_management_service.py`

| 操作类型 | Auth | 权限实现 | 与文档一致? |
|---------|------|---------|:---:|
| 标签/分类的查询 | Optional | 公开资源，无权限过滤 | ✅ |
| 标签/分类的CUD | Strict + `_check_admin_permission` | Admin Only (content_management_service.py 42行) | ✅ |
| 专题查询 | Optional + `_check_topic_visibility` | 公开/Draft对Owner和Admin可见 | ✅ |
| 专题CUD | Strict + `_check_write_permission` + `check_room_owner_or_admin` | Owner+Admin | ✅ |

**`_check_admin_permission` 实际代码**（content_management_service.py 第42-54行）：
```python
def _check_admin_permission(self, role: Optional[str]) -> None:
    if role not in ['ADMIN', 'SUPERADMIN']:
        raise PermissionDeniedException("权限不足")
```

### 3.9 用户行为模块

**Endpoint 文件**: `app/api/v1/endpoints/user_behavior.py`
**使用**：全部端点使用 `Depends(get_current_user)` (Strict Auth)，但 Service 层通过 `user_id=UUID(current_user["user_id"])` 直接以当前用户 ID 进行 CRUD，**不传 role 参数**。代码中没有显式的 `_check_write_permission` 调用，因为行为数据天然按 user_id 隔离。

### 3.10 用户偏好与通知模块

**Endpoint 文件**: `app/api/v1/endpoints/user_preference_notification.py`
**使用**：全部端点使用 `Depends(get_current_user)` (Strict Auth)，Service 层提取 `user_id` 和 `role`。代码中直接按 user_id 过滤数据，Admin 可以查看任意用户的偏好（Service 层 `get_preferences_by_user_id` 方法）。

### 3.11 首页与搜索模块

**Endpoint 文件**: `app/api/v1/endpoints/homepage_search.py`

| 接口 | Auth(代码) | 权限 | 与文档一致? |
|------|:---:|------|:---:|
| `GET /api/v1/featured-content` | **无认证** (320行) | 公开 | ✅ |
| `GET /api/v1/homepage/rooms` | **无认证** (350行) | 公开 | ✅ |
| `GET /api/v1/search` | **Optional** (402行) | 登录用户自动记录搜索历史 | ✅ |
| 焦点图 Admin CRUD | Strict + `_check_admin_permission` | Admin Only | ✅ |

### 3.12 内部回调模块

**Endpoint 文件**: `app/api/v1/endpoints/internal.py`

**代码实际实现**：SRS 回调接口（`POST /internal/on-publish` / `POST /internal/on-unpublish`）**完全没有认证**。代码仅通过 Pydantic schema 验证 payload，未实现设计文档中建议的 IP 白名单或 HMAC 签名。

```python
# internal.py 第33-69行
@internal_router.post("/on-publish")
async def on_publish_post(
    payload: SrsOnPublishPayload,  # 仅做 schema 校验
    db: AsyncSession = Depends(get_db)
):
    # 无任何认证逻辑！
```

**结论**：内部回调接口的安全性**完全依赖网络层隔离**（如防火墙、内网部署），应用层无额外认证机制。这与设计文档建议的"IP白名单+HMAC签名"方案存在差距。

---

## 四、CRUD 层权限过滤代码验证

`app/crud/room.py` 中的 `get_multi_and_total` 函数（第123-166行）**确实实现了 SQL 层面的权限过滤**：

```python
# crud/room.py 第123-147行
async def get_multi_and_total(db, skip, limit, user_id=None, role=None, ...):
    query = select(LiveRoom)
    if role in ['ADMIN', 'SUPERADMIN']:
        pass  # 管理员无过滤
    elif user_id:
        query = query.where(or_(
            LiveRoom.is_private == False,
            LiveRoom.user_id == user_id
        ))
    else:
        query = query.where(LiveRoom.is_private == False)
    # ... 然后再应用业务筛选条件（AND 关系）
```

这与设计文档的要求完全一致：Admin 无过滤、Regular 看 Public+Own、Anonymous 仅 Public，且业务筛选条件与权限过滤条件使用 AND 关系。

---

## 五、代码与文档一致性总结

### ✅ 完全一致

| 模块 | 一致项 |
|------|-------|
| Room CRUD | Optional/Strict 双轨、check_room_visibility、check_room_owner_or_admin、SQL 权限过滤 |
| Session | 继承 Room 可见性、通过 JOIN Room 实现 |
| 留言 | URL 三级过滤完全一致 |
| 专家 | 查询公开、CUD Admin Only、关注 Owner Only、is_active 404 伪装 |
| 品牌 | 查询公开、CUD Admin Only |
| 内容管理 | 标签/分类查询公开、CUD Admin Only、专题 Owner+Admin |
| 用户行为/偏好 | 按 user_id SQL 过滤 |
| 首页/搜索 | 公开接口、焦点图 Admin Only |
| MODERATOR | 代码中无特殊处理，等同 REGULAR |
| 权限守卫函数 | permissions.py 集中管理，与文档描述一致 |

### ❌ 代码与文档存在矛盾

| 矛盾项 | 文档描述 | 代码实际 | 严重程度 |
|--------|---------|---------|---------|
| **StreamKey 泄露** | "推流密钥严禁匿名" | `GET /api/v1/rooms/{id}` 使用 Optional Auth，第339行直接返回 stream_key | 🔴 严重 |
| **Tab Admin 路由** | v6.1.1 说 Tab 管理已从 Admin Only 放宽为 Owner+Admin | admin_tab_router 的4个端点仍然硬编码 Admin Only | ⚠️ 中等 |
| **批量导入权限** | 文档 v6.1 说"所有登录用户" | 函数名叫 `_check_admin_role` 注释说 Admin Only，但代码允许 REGULAR | ⚠️ 中等 |
| **SRS 回调安全** | 文档建议 IP白名单+HMAC | 无任何认证，仅 Pydantic 校验 | ⚠️ 中等 |
| **Brand 绑定路由** | 文档认为"关联直播间" Regular 可用 | 实际有两条路由：Admin Only 和 Owner+Admin | ⚠️ 轻微 |

### ⚡ 代码实现了但文档未充分说明

| 功能 | 说明 |
|------|------|
| `users_me_rooms_router` (代码225-295行) | `GET /users/me/rooms` — 当前用户的房间列表，支持搜索，owner_only 模式。与 `GET /api/v1/rooms?owner_only=true` 等价 |
| Tab 三套并行路由 | admin_tab_router (Admin Only) / room_tab_router (Owner+Admin) / public_tab_router (Public) — 设计文档只提了一种路由 |
| Brand 两套绑定路由 | `brand_admin_router` / `room_brand_owner_router` — 两套路由实现不同权限等级的绑定操作 |
| `user_id` fallback `sub` | 多个端点（live_features.py, homepage_search.py）中使用了 `current_user.get("user_id") or current_user.get("sub")` 的 fallback 写法，而文档严格禁止使用 `sub` |

---

## 六、最终结论

经过逐行代码验证后，**权限体系的三个核心等级结论依然成立**：

- **L0 匿名**：仅可读 Public 资源（is_private=false），不能写
- **L1 Regular(MODERATOR)**：可创建和完全管理自己的资源（房间/场次/专题/Tab/留言），操作他人资源受限（查不到 Private、不能写、不能发含 URL 留言），不能管理平台级资源（品牌/专家/标签/分类/焦点图）
- **L2/L3 Admin/SuperAdmin**：全局读写一切，无视 is_private，管理所有平台资源

**但之前报告基于文档得出的以下结论需要修正**：

1. **之前说 "Tab 已从 Admin Only 放宽为 Owner+Admin"** — 实际上代码中 admin 路由仍为 Admin Only，只是新增了 room 路由实现 Owner+Admin。这是两套路由并行，而非替换。

2. **之前说 "批量导入所有登录用户均可使用"** — 代码中函数名和注释仍写 Admin Only，虽然实际逻辑允许 Regular，但这个矛盾状态表明这并非一个已经拍板的设计决策。

3. **之前未提及 StreamKey 泄露风险** — 这是阅读代码后发现的最严重的安全问题：`GET /api/v1/rooms/{id}` 在 Optional Auth 下直接返回 stream_key，匿名用户可获取公开房间的推流密钥。

4. **之前未提及 SRS 内部回调无应用层认证** — 代码中确实没有任何 IP 白名单或 HMAC 签名的实现。

[View the updated report](computer://D:\live-streaming-saas-v2-main\docs\LiveCore权限体系全面分析报告.md)
