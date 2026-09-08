# 管理端用户管理模块设计文档（Admin Users）

**项目**: Live-Saas-Wechat  
**模块编号**: 14  
**版本**: 1.1  
**创建日期**: 2026-07-13  
**状态**: 骨架已实现可联调；权限/开播/吊销等语义以 V2 为准  
**基于**: 《10-用户认证与管理-后端设计文档.md》(V1.2)、《用户模块设计文档.md》(V4.0)  
**修订文档**: 《[Live-Saas-Wechat-14-管理端用户管理-账号能力模型与权限修订-设计文档-v2.0](./Live-Saas-Wechat-14-管理端用户管理-账号能力模型与权限修订-设计文档-v2.0.md)》  
**配套前端**: 《[Live-Saas-Wechat-14-管理端用户管理-前端设计文档-v1.0](./Live-Saas-Wechat-14-管理端用户管理-前端设计文档-v1.0.md)》、V2《[Live-Saas-Wechat-14-管理端用户管理-账号能力模型与权限修订-前端设计文档-v2.0](./Live-Saas-Wechat-14-管理端用户管理-账号能力模型与权限修订-前端设计文档-v2.0.md)》

> **修订说明（2026-07-14；2026-07-30 补 V2.1）**  
> 开播能力（`can_stream`，**V2.1 默认 true；false=禁止开播**）、ADMIN/SUPERADMIN 职责收敛、封禁/禁止开播会话吊销、运营检索、专家认领、品牌成员与货架商品等，以  
> 《[14-管理端用户管理-V2-账号能力模型与权限修订设计文档](./14-管理端用户管理-V2-账号能力模型与权限修订设计文档.md)》及前端《V2 前端》**2.1.0** 为准。  
> 本文档（V1.1）中「默认 false / 授予开播资格」等表述 **已废止**。  
> 本文档 V1 仍有效部分：网关前缀、列表/PATCH 骨架、统一响应、会员产品与订阅 Admin API。与 V2 冲突时以 V2 为准。

---

## 📌 核心定位说明

### 1. 本文档的定位

本文档专注于 **管理端用户管理（Admin Users）** 的后端实现设计，是 `user_service` 中管理员后台的核心子模块，包括：

**包含模块**:
- **Admin Users（管理端用户管理）**: 分页查询、筛选、更新用户状态/开播权；改角色仅超管（V2）
- **Admin Membership Products（管理端会员产品）**: 会员产品 CRUD（同 `/admin` 前缀，关联模块）
- **Admin Subscriptions（管理端订阅管理）**: 查看/创建/更新用户订阅（同 `/admin` 前缀，关联模块）

**模块范围**:
- 1 张核心数据表（`users`，只读 + 部分字段更新）
- 2 个用户管理 API 接口（列表 + 更新）
- 7 个关联管理 API 接口（会员产品 5 个、订阅 3 个，见 §9 路由表）
- 完整的 Pydantic Schemas、Service 层、CRUD 层设计
- 网关路径约定（`/api/users/admin/*`）

### 2. 本文档的核心特点

- ✅ **骨架与实现一致**: 列表 + PATCH、网关路径对齐当前 `backend/users` 与 Nginx
- ⚠️ **权限语义以 V2 为准**: V1「ADMIN 可改他人 role」废止；`can_stream`/吊销等见 V2（部分待开发）
- ✅ **服务边界明确**: 归属 `user_service`，**不**走 `/api/core/` 网关前缀

### 3. 业务价值说明

> ⚠️ **部分表述 Deprecated**：角色日常可调全套枚举、筛选项仅用户名邮箱等 — 以 V2 为准（开播权、禁改 role 等）。

**管理端用户管理（Admin Users）**:
- 为运营/管理员提供全量用户检索与状态管控能力
- 支持按用户名、邮箱、角色、状态筛选，快速定位问题账号（V2 还将补手机号/昵称/开播权）
- 支持禁用（BANNED）、恢复（NORMAL）等状态变更；**V2：授予/撤销开播权 `can_stream`**
- 角色调整：**V2 仅 SUPERADMIN 可改 `role`**；管理端日常隐藏 MODERATOR

**关联模块（同服务 admin 前缀）**:
- 会员产品管理：配置可售会员套餐
- 订阅管理：查看用户订阅历史、手动补录订阅

---

## 📚 依赖文档清单

| 序号 | 文档名称 | 依赖关系 | 影响范围 |
|------|---------|---------|---------|
| 1 | 《10-用户认证与管理-后端设计文档.md》(V1.2) | 📋 **主设计文档** | `users` 表 DDL、JWT 规范、Admin Users API 初版设计 |
| 2 | 《用户模块设计文档.md》(V4.0) | 📋 **模块设计文档** | 用户角色枚举、状态枚举、安全规范 |
| 3 | 《前端API路径变更同步报告.md》 | 📖 **参考文档** | 网关前缀约定、联调环境 |
| 4 | 《测试账号信息.md》 | 📖 **参考文档** | 管理员测试账号 |

**⚠️ 重要说明**:
- 本模块 V1 **不新建数据表**，直接读写 `users` 表  
  > ⚠️ **Deprecated（字段层面）**：V2 将为 `users` **新增** `can_stream`；专家/品牌表变更见 V2，不在本模块建表叙事内。
- JWT 由 `user_service` 统一签发，Payload 字段与其他服务保持一致（V2 增 `can_stream`）
- 管理端接口 **仅** 在 `user_service` 挂载，经 Nginx `/api/users/admin/` 对外暴露
- **禁止** 使用 `/api/core/admin/users`（该前缀归属 `live_core_service`，无用户管理路由）

---

## 📖 文档规范说明

### 统一响应结构

```json
{
  "code": 200,
  "message": "success",
  "data": { ... },
  "timestamp": "2026-07-13T09:00:00Z"
}
```

### 统一分页格式

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "total": 100,
    "page": 1,
    "size": 20,
    "items": [ ... ]
  },
  "timestamp": "2026-07-13T09:00:00Z"
}
```

### 统一认证规范

| 级别 | 说明 | 本模块适用 |
|------|------|-----------|
| **Public** | 无需 Token | ❌ 不适用 |
| **JWT** | 需有效 Token | ❌ 不适用（管理端一律需管理员） |
| **ADMIN** | Token + 角色为 `ADMIN` 或 `SUPERADMIN` | ✅ 全部接口 |

### JWT Token 格式说明

```json
{
  "user_id": "uuid-string",
  "username": "admin",
  "role": "ADMIN",
  "type": "access",
  "can_stream": false,
  "exp": 1717756800
}
```

> **重要说明**: JWT Payload 中用户标识字段为 `user_id`（非 `sub`）。`role` 取值与库枚举一致（如 `ADMIN`，非小写 `admin`）。`can_stream` 为 V2 字段，旧 Token 缺省按 `false`。管理端鉴权通过 `Depends(get_current_admin_user)` 实现，允许角色为 `ADMIN` 或 `SUPERADMIN`。

### 业务状态码

| 状态码 | 说明 | HTTP 状态 | 使用场景 |
|--------|------|-----------|----------|
| `200` | 成功 | 200 | 查询/更新成功 |
| `1002` | 数据库错误 | 500 | 数据库操作异常 |
| `2004` | 资源不存在 | 404 | 目标用户 UUID 不存在 |
| `3001` | 未授权 | 401 | Token 缺失或无效 |
| `3002` | 权限不足 | 403 | 非管理员，或 ADMIN 越权操作 SUPERADMIN |
| `4001` | 参数校验失败 | 422 | Query/Body 不符合 Schema |

---

## 🎯 设计要点与约定

### 1.1 服务与路由归属

| 维度 | 值 |
|------|-----|
| **微服务** | `user_service` |
| **容器端口** | `8002` |
| **服务内 API 前缀** | `/api/v1` |
| **管理端路由前缀** | `/api/v1/admin` |
| **Nginx 网关前缀** | `/api/users/admin/` |

### 1.2 API 路径约定（服务内 vs 网关）

文档中 **Endpoint** 默认为微服务内部路径。经 Nginx 对外暴露时需加网关前缀：

| 对外网关路径（nginx） | 转发至服务内路径 | 所属服务 |
|---|---|---|
| `GET /api/users/admin/users` | `GET /api/v1/admin/users` | user_service |
| `PATCH /api/users/admin/users/{user_uuid}` | `PATCH /api/v1/admin/users/{user_uuid}` | user_service |
| `GET /api/users/admin/membership-products` | `GET /api/v1/admin/membership-products` | user_service |
| `GET /api/users/admin/subscriptions/by-user/{user_uuid}` | `GET /api/v1/admin/subscriptions/by-user/{user_uuid}` | user_service |

> ❌ **错误路径**: `/api/core/admin/users` → 转发至 `live_core_service`，返回 **404**。

### 1.3 架构分层

```
API 层 (app/api/v1/admin/users.py)
  → 仅负责 Depends 注入、调用 Service、异常转 JSONResponse
Service 层 (app/services/admin_user_service.py)
  → 业务逻辑、权限校验、分页组装
CRUD 层 (app/crud/crud_user.py)
  → SQL 查询与更新
```

**代码文件清单**:

| 层级 | 文件路径 |
|------|---------|
| 路由注册 | `backend/users/app/api/v1/api.py` |
| API 端点 | `backend/users/app/api/v1/admin/users.py` |
| 权限依赖 | `backend/users/app/api/v1/deps.py` → `get_current_admin_user` |
| Service | `backend/users/app/services/admin_user_service.py` |
| CRUD | `backend/users/app/crud/crud_user.py` |
| Schema | `backend/users/app/schemas/users.py` |
| Model | `backend/users/app/models/users.py` |
| Nginx | `nginx/nginx.conf`、`nginx/nginx.windows.conf` |

### 1.4 权限矩阵（ADMIN vs SUPERADMIN）

> **V2 修订（以本表为准；旧「ADMIN 可改他人 role」废止）**  
> 完整能力模型（`can_stream`、会话吊销等）见 《Live-Saas-Wechat-14-管理端用户管理-账号能力模型与权限修订-设计文档-v2.0》。

| 操作 | ADMIN | SUPERADMIN |
|------|-------|------------|
| 查看用户列表 | ✅ | ✅ |
| 修改目标用户 `status`（日常仅 NORMAL↔BANNED） | ✅（不可改自己；不可改 SUPERADMIN） | ✅（不可改自己） |
| 授予/撤销 `can_stream`（开播权，V2） | ✅（同上约束） | ✅ |
| **修改他人 `role`（任命/解除管理员）** | ❌ 403 | ✅ |
| 修改 SUPERADMIN 用户任意字段 | ❌ 403 | ✅ |
| 将用户角色设为 SUPERADMIN | ❌ 403 | ✅ |
| 将角色设为 MODERATOR | ❌ 不推荐（管理端隐藏，见 V2） | ❌ 不推荐 |

**实现位置**: `AdminUserService.update_user_by_admin()` — V1 已有「碰 SUPERADMIN」检查；V2 需补：禁改自己、ADMIN 禁写 `role`、封禁/撤开播吊销会话。

### 1.5 软删除与状态策略

| 字段 | 策略 | 说明 |
|------|------|------|
| `users.status` | 状态枚举 | 运营主路径：`NORMAL` / `BANNED`；其余枚举保留但非主按钮（见 V2） |
| `users.can_stream` | V2 新增 | 开播资格，与 `role` 正交；默认 `false` |
| 管理端更新 | PATCH 部分字段 | 日常改 `status` / `can_stream`；改 `role` 仅 SUPERADMIN；不直接删行 |

---

## 1. 数据库 Schema 设计（DDL）

> 本模块 **不新建表**，依赖 `users` 表。以下为管理端相关字段摘要（完整 DDL 见《10-用户认证与管理-后端设计文档.md》§1）。  
> ⚠️ **Deprecated**：下方 DDL **尚未含** `can_stream`；V2 字段定义与迁移见 《14-…-V2…》§1.1。

### 1.1 users（用户核心表 — 管理端读写字段）

```sql
-- ==========================================================
-- 表：users（用户核心表）
-- 说明：管理端用户管理模块读取全表，仅 PATCH 更新 role/status 等字段
-- ==========================================================

CREATE TABLE users (
    id              BIGSERIAL PRIMARY KEY,
    public_id       UUID NOT NULL UNIQUE DEFAULT gen_random_uuid(),
    username        VARCHAR(50) NOT NULL UNIQUE,
    email           VARCHAR(255) UNIQUE,
    phone_number    VARCHAR(20) UNIQUE,
    password_hash   VARCHAR(255),
    nickname        VARCHAR(50) NOT NULL,
    avatar_url      VARCHAR(512),
    bio             TEXT,
    role            user_role NOT NULL DEFAULT 'REGULAR',
    status          entity_status NOT NULL DEFAULT 'NORMAL',
    is_email_verified BOOLEAN NOT NULL DEFAULT FALSE,
    is_phone_verified BOOLEAN NOT NULL DEFAULT FALSE,
    last_login_at   TIMESTAMPTZ,
    last_login_ip   INET,
    social_provider VARCHAR(20),
    social_id       VARCHAR(255),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 管理端高频筛选索引
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_status ON users(status);
CREATE INDEX idx_users_created_at ON users(created_at DESC);
```

### 1.2 枚举类型

```sql
-- 用户角色
CREATE TYPE user_role AS ENUM (
    'REGULAR', 'MODERATOR', 'ADMIN', 'SUPERADMIN'
);

-- 用户状态
CREATE TYPE entity_status AS ENUM (
    'NORMAL', 'BANNED', 'DELETED', 'PENDING_REVIEW', 'REJECTED'
);
```

---

## 2. Pydantic Schemas 定义

> ⚠️ **Deprecated（字段不完整）**：下列 Schema 为 V1 现状；V2 须在 `UserResponse` / `UserUpdate` / `UserFilterParams` 增加 `can_stream`，筛选增加 `phone_number`/`nickname`，且 ADMIN 写 `role` 在 Service 层拒绝。详见 V2 §6。

### 2.1 用户响应 Schema

```python
class UserResponse(UserBase):
    """用户响应 Schema — 管理端列表/详情均使用此结构"""
    id: int                          # 内部 ID（BigInt）
    public_id: uuid.UUID             # 对外 UUID（API 路径参数使用此字段）
    is_email_verified: bool
    is_phone_verified: bool
    last_login_at: Optional[datetime]
    last_login_ip: Optional[str]
    social_provider: Optional[str]
    social_id: Optional[str]
    created_at: datetime
    updated_at: datetime
```

### 2.2 管理端更新 Schema

```python
class UserUpdate(BaseModel):
    """管理端 PATCH 更新 Schema — 所有字段 Optional，部分更新"""
    role: Optional[UserRole] = None       # REGULAR | MODERATOR | ADMIN | SUPERADMIN
    status: Optional[EntityStatus] = None   # NORMAL | BANNED | DELETED | ...
    nickname: Optional[str] = None
    # 其他字段理论上可传，但管理端 UI 通常只改 role/status
```

### 2.3 筛选参数 Schema

```python
class UserFilterParams(BaseModel):
    username: Optional[str] = None           # 模糊匹配（ILIKE %username%）
    email: Optional[str] = None                # 精确匹配
    role: Optional[UserRole] = None
    status: Optional[EntityStatus] = None
    is_email_verified: Optional[bool] = None   # CRUD 层支持，API Query 待扩展
    is_phone_verified: Optional[bool] = None   # CRUD 层支持，API Query 待扩展
```

---

## 3. API 接口设计

### 3.1 Admin Users 模块 API

#### 3.1.1 管理端用户列表（ADMIN）

**Endpoint**: `GET /api/v1/admin/users`

**网关路径**: `GET /api/users/admin/users`

**描述**: 分页查询系统用户列表，支持多条件筛选

**认证**: JWT + 管理员权限（`Depends(get_current_admin_user)`）

**请求参数 (Query)**:

> ⚠️ V1 参数如下；**V2 还将增加** `phone_number`、`nickname`、`can_stream`（见 V2 §5.1.1）。

| 参数 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `page` | int | 否 | 1 | 页码，≥1 |
| `size` | int | 否 | 10 | 每页数量，1~100 |
| `sort` | str | 否 | `created_at:desc` | **预留参数**，当前固定按 `created_at DESC` |
| `username` | str | 否 | — | 用户名模糊搜索 |
| `email` | str | 否 | — | 邮箱精确匹配 |
| `role` | UserRole | 否 | — | 角色筛选 |
| `status` | EntityStatus | 否 | — | 状态筛选 |

**成功响应** (`200 OK`):

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "total": 42,
    "page": 1,
    "size": 10,
    "items": [
      {
        "id": 1,
        "public_id": "550e8400-e29b-41d4-a716-446655440000",
        "username": "john_doe",
        "nickname": "John",
        "email": "john@example.com",
        "phone_number": null,
        "avatar_url": "/uploads/avatars/xxx.jpg",
        "bio": null,
        "role": "REGULAR",
        "status": "NORMAL",
        "is_email_verified": true,
        "is_phone_verified": false,
        "last_login_at": "2026-07-10T08:00:00Z",
        "last_login_ip": "127.0.0.1",
        "created_at": "2026-06-01T00:00:00Z",
        "updated_at": "2026-07-10T08:00:00Z"
      }
    ]
  },
  "timestamp": "2026-07-13T09:00:00Z"
}
```

**失败响应**:

| HTTP | code | 场景 |
|------|------|------|
| 401 | 3001 | Token 缺失或无效 |
| 403 | 3002 | 非 ADMIN/SUPERADMIN |
| 500 | 1002 | 数据库异常 |

**执行流程**:

1. **接收请求**: API 路由接收 GET，解析 Query 参数
2. **JWT 验证**: `Depends(get_current_admin_user)` 校验 Token 与管理员角色
3. **构建筛选**: 组装 `UserFilterParams(username, email, role, status)`
4. **调用 Service**: `AdminUserService.list_users(filters, page, size)`
5. **CRUD 查询**: `count_with_filtering` + `get_multi_with_filtering`（`ORDER BY created_at DESC`）
6. **序列化**: 每条记录转为 `UserResponse`
7. **返回响应**: 统一分页 JSON

---

#### 3.1.2 管理员更新用户（ADMIN）

**Endpoint**: `PATCH /api/v1/admin/users/{user_uuid}`

**网关路径**: `PATCH /api/users/admin/users/{user_uuid}`

**描述**: 管理员更新指定用户的角色、状态等核心信息

**认证**: JWT + 管理员权限

**路径参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| `user_uuid` | UUID | 用户 `public_id`（非内部 `id`） |

**请求体**（V2 日常示例；勿再用 MODERATOR 作主示例）:

```json
{
  "status": "BANNED",
  "can_stream": false
}
```

超管任命管理员示例：

```json
{
  "role": "ADMIN"
}
```

**成功响应** (`200 OK`):

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 2,
    "public_id": "660e8400-e29b-41d4-a716-446655440001",
    "username": "bad_user",
    "nickname": "Bad User",
    "role": "REGULAR",
    "status": "BANNED",
    "can_stream": false,
    "...": "..."
  },
  "timestamp": "2026-07-13T09:00:00Z"
}
```

**失败响应**:

| HTTP | code | 场景 |
|------|------|------|
| 401 | 3001 | Token 缺失或无效 |
| 403 | 3002 | 非管理员；改自己；ADMIN 修改/提升 SUPERADMIN；**ADMIN 修改任意 `role`（V2）** |
| 404 | 2004 | `user_uuid` 对应用户不存在 |
| 422 | 4001 | Body 参数校验失败（如 ADMIN 设非 NORMAL/BANNED 的 status） |
| 500 | 1002 | 数据库异常 |

**执行流程**（V2）:

1. **接收请求**: PATCH + `user_uuid` 路径参数 + Body
2. **JWT 验证**: `get_current_admin_user`
3. **Pydantic 校验**: `UserUpdate` Schema（含可选 `can_stream`）
4. **查询目标用户**: `crud_user.get_by_uuid(public_id=user_uuid)`
5. **存在性检查**: 不存在 → `TargetUserNotFoundError` → 404
6. **禁改自己**: 目标 `public_id` == 操作者 → 403
7. **静态权限检查**: ADMIN 不可修改 SUPERADMIN 用户 → 403
8. **角色写权限（V2）**: Body 含 `role` 且操作者为 ADMIN → 403；仅 SUPERADMIN 可改 role
9. **动态权限检查**: ADMIN 不可将 role 设为 SUPERADMIN（超管路径仍保留）→ 403
10. **更新数据库**: `crud_user.update(db_obj, obj_in=user_update)`
11. **会话吊销（V2）**: 若 `status∈{BANNED,DELETED}` 或 `can_stream→false` 或 role 降级 → 写 `user_sessions_revoked`（详见 V2 §4）
12. **返回响应**: 更新后的 `UserResponse`

---

## 4. 执行流程详细说明

### 4.1 用户列表查询完整流程

```
1. GET /api/users/admin/users?page=1&size=20&role=REGULAR
   → 2. Nginx 转发至 user_service /api/v1/admin/users
   → 3. get_current_admin_user（JWT + 角色校验）
   → 4. 构建 UserFilterParams
   → 5. AdminUserService.list_users()
   → 6. crud_user.count_with_filtering()  → total
   → 7. crud_user.get_multi_with_filtering(skip, limit)  → items
   → 8. UserResponse.model_validate × N
   → 9. 返回 { total, page, size, items }
```

### 4.2 用户状态/开播权/角色更新完整流程（V2）

```
1. PATCH /api/users/admin/users/{uuid}  Body: { "status": "BANNED" } 或 { "can_stream": false }
   → 2. Nginx 转发
   → 3. get_current_admin_user
   → 4. get_by_uuid → 用户不存在则 404
   → 5. 禁改自己 → 403
   → 6. ADMIN 不可碰 SUPERADMIN → 403
   → 7. Body 含 role 且为 ADMIN → 403（仅超管可改角色）
   → 8. crud_user.update（仅更新 Body 中非 null 字段）
   → 9. 按 V2 §4 触发会话吊销（封禁/撤开播/降权）
   → 10. 返回 UserResponse
```

---

## 5. 错误处理与事务管理

### 5.1 错误处理策略

**API 层**:
- 捕获 `TargetUserNotFoundError` → HTTP 404, code=2004
- 捕获 `PermissionDeniedError` → HTTP 403, code=3002
- 捕获通用 `Exception` → HTTP 500, code=1002

**Service 层**:
- 抛出业务异常，不直接返回 HTTP 响应
- 日志记录使用「主动变量提取」模式，避免 ORM 对象失效后访问

### 5.2 事务管理

- 单用户 PATCH 为单表操作，CRUD `update` 内部 `commit`
- 列表查询为只读，无事务写入

---

## 6. 性能优化建议

### 6.1 数据库

- 筛选字段 `role`、`status`、`created_at` 已建索引
- 用户名模糊搜索（`ILIKE`）数据量大时考虑 pg_trgm 或 ES

### 6.2 应用层

- 列表接口默认 `size=10`，前端建议不超过 50
- 管理端列表 **不建议** 全量拉取，始终使用分页

---

## 7. 测试建议

### 7.1 集成测试（已有）

测试文件: `backend/users/tests/test_api_admin_users.py`

| # | 用例 | 预期 |
|---|------|------|
| T1 | 普通用户 Token 访问 GET /admin/users | 403 |
| T2 | ADMIN Token + role=MODERATOR 筛选 | 200 + 筛选结果（筛选能力保留；管理端日常勿设该角色） |
| T3 | ADMIN Token + status=BANNED 筛选 | 200 |
| T4 | ADMIN 更新普通用户 **status** / **can_stream** | 200 |
| T4b | ADMIN 更新普通用户 **role** | **403**（V2：仅 SUPERADMIN 可改角色） |
| T5 | ADMIN 更新 SUPERADMIN | 403 |
| T6 | 更新不存在的 UUID | 404 |
| T7 | ADMIN PATCH 自己 | 403（V2） |

### 7.2 网关冒烟测试

| # | 请求 | 预期 |
|---|------|------|
| G1 | `GET /api/users/admin/users`（无 Token） | 401 |
| G2 | `GET /api/v1/admin/users`（直连 8002，无 Token） | 401 |
| G3 | `GET /api/core/admin/users` | **404**（错误前缀） |

---

## 8. 错误码对照表

| 错误码 | 说明 | HTTP | 使用场景 |
|--------|------|------|----------|
| `200` | 成功 | 200 | 查询/更新成功 |
| `1002` | 数据库错误 | 500 | DB 异常 |
| `2004` | 用户不存在 | 404 | UUID 无对应用户 |
| `3001` | 未授权 | 401 | Token 问题 |
| `3002` | 权限不足 | 403 | 非管理员或越权 |
| `4001` | 参数校验失败 | 422 | Query/Body 非法 |

---

## 9. 部署与联调

### 9.1 部署检查清单

- [x] `backend/users/app/api/v1/api.py` 已注册 admin 路由
- [x] `nginx/nginx.conf` 与 `nginx/nginx.windows.conf` 已配置 `/api/users/admin/`
- [ ] `user_service` 容器已重建
- [ ] `nginx` 已 reload/restart
- [ ] 管理员测试账号可用（见《测试账号信息.md》）

### 9.2 重建命令（Windows 本地）

```batch
docker compose -f docker-compose.yml -f docker-compose.windows.yml up -d --build user_service
docker compose restart nginx
```

### 9.3 联调环境

| 项目 | 值 |
|------|-----|
| user_service 直连 | `http://localhost:8002` |
| Nginx 网关 | `http://localhost:8080` |
| 服务内 API 前缀 | `/api/v1` |
| 网关 Admin 前缀 | `/api/users/admin/` |

---

## 10. 后续开发建议

> **本节已按 V2 重排。** 下列「V1 旧建议」降级，完整方案见 《Live-Saas-Wechat-14-管理端用户管理-账号能力模型与权限修订-设计文档-v2.0》。

### 10.1 优先级 P0（必须先做，对齐 V2）

- [ ] `users.can_stream` + Admin PATCH 授予/撤销；列表返回与筛选
- [ ] 创建直播间开播门禁（live_core）；JWT 声明 `can_stream`
- [ ] 封禁 / 撤开播 / 降权 → 会话吊销；live_core（建议 users）access 校验吊销 Key
- [ ] Admin 护栏：禁改自己；**仅 SUPERADMIN 可改 `role`**；日常 status 白名单 NORMAL|BANNED
- [ ] 列表筛选：`phone_number`、`nickname`

### 10.2 优先级 P1 / P2（见 V2，非本文扩写）

- [ ] P1：专家认领 `/experts/me`、头像可选同步（live_core）
- [ ] P2：品牌成员 + 货架商品；Admin 管全部已上架商品（live_core）

### 10.3 Deprecated（原 V1 建议，让位 P0）

- ~~API 暴露 `is_email_verified` / `is_phone_verified` 筛选~~ → 降级
- ~~启用 `sort`~~ → 降级
- ~~用户详情单条 GET / 审计表 / 批量导出~~ → 可后续，非本轮

---

## 📝 文档修订历史

| 版本 | 日期 | 修订内容 | 作者 |
|------|------|----------|------|
| V1.0 | 2026-07-13 | 初始版本：对齐已实现代码、网关路径、权限矩阵 | — |
| V1.1 | 2026-07-14 | 最小同步 V2：改权限矩阵/PATCH 流程/§10/路由 Notes/测试 T4；其余冲突处标 Deprecated，详情以 V2 为准 | — |

---

## 最终路由表

### ✅ 已实现（后端代码已存在）

#### Admin Users（本模块核心）

| Domain | 服务内 Endpoint | 网关路径 | Method | Auth | Roles | Request | Response | Error Codes | Notes |
|--------|----------------|----------|--------|------|-------|---------|----------|-------------|-------|
| admin-users | `/api/v1/admin/users` | `/api/users/admin/users` | GET | JWT | ADMIN, SUPERADMIN | Query: page, size, username, email, role, status；（V2）phone_number, nickname, can_stream | Paginated UserResponse（含 can_stream） | 200, 3001, 3002, 1002 | 用户列表 |
| admin-users | `/api/v1/admin/users/{user_uuid}` | `/api/users/admin/users/{user_uuid}` | PATCH | JWT | ADMIN, SUPERADMIN | Body: status / can_stream；（role **仅 SUPERADMIN**） | UserResponse | 200, 2004, 3001, 3002, 4001, 1002 | 更新状态/开播权；改角色仅超管；封禁等须吊销会话（V2） |

#### Admin 关联模块（同前缀，user_service）

| Domain | 服务内 Endpoint | 网关路径 | Method | Auth | Notes |
|--------|----------------|----------|--------|------|-------|
| admin-products | `/api/v1/admin/membership-products` | `/api/users/admin/membership-products` | GET/POST | JWT+ADMIN | 会员产品列表/创建 |
| admin-products | `/api/v1/admin/membership-products/{code}` | `/api/users/admin/membership-products/{code}` | GET/PATCH/DELETE | JWT+ADMIN | 产品详情/更新/删除 |
| admin-subs | `/api/v1/admin/subscriptions/by-user/{uuid}` | `/api/users/admin/subscriptions/by-user/{uuid}` | GET | JWT+ADMIN | 用户订阅列表 |
| admin-subs | `/api/v1/admin/subscriptions/by-user/{uuid}` | `/api/users/admin/subscriptions/by-user/{uuid}` | POST | JWT+ADMIN | 手动创建订阅 |
| admin-subs | `/api/v1/admin/subscriptions/{uuid}` | `/api/users/admin/subscriptions/{uuid}` | PATCH | JWT+ADMIN | 更新订阅 |

### 📋 待实现（以 V2 P0 为准；下列旧项 Deprecated）

| Domain | Endpoint / 能力 | Method | Notes | 优先级 |
|--------|-----------------|--------|-------|--------|
| admin-users | `can_stream` 字段 + PATCH/列表 | — | 开播权 | P0（V2） |
| admin-users | Query: phone_number, nickname | GET | 运营检索 | P0（V2） |
| admin-users | 会话吊销联动 | PATCH | 封禁/撤开播 | P0（V2） |
| admin-users | ~~单用户详情 GET~~ | GET | Deprecated，见 V2 | — |
| admin-users | ~~is_email_verified / is_phone_verified 筛选~~ | GET | Deprecated，让位 P0 | — |

### ❌ 错误路径（请勿使用）

| 路径 | 原因 |
|------|------|
| `/api/core/admin/users` | 归属 live_core_service，无用户管理路由 → 404 |

---

## 11. 自测清单

### A. 路由挂载

| # | 测试用例 | 预期结果 |
|---|---------|---------|
| A1 | `GET :8002/openapi.json` 含 `/api/v1/admin/users` | ✅ 路径存在 |
| A2 | `GET :8002/api/v1/admin/users`（无 Token） | 401 |
| A3 | `GET :8080/api/users/admin/users`（无 Token） | 401 |
| A4 | `GET :8080/api/core/admin/users` | 404 |

### B. 权限（需管理员 Token）

| # | 测试用例 | 预期结果 |
|---|---------|---------|
| B1 | ADMIN Token GET 用户列表 | 200 + 分页 data |
| B2 | REGULAR Token GET 用户列表 | 403 |
| B3 | ADMIN PATCH 普通用户 status=BANNED | 200（并应吊销会话，见 V2） |
| B3b | ADMIN PATCH 普通用户 role=ADMIN | 403（V2） |
| B3c | ADMIN PATCH 自己 | 403（V2） |
| B4 | ADMIN PATCH SUPERADMIN 用户 | 403 |
| B5 | PATCH 不存在的 user_uuid | 404, code=2004 |

### C. 筛选

| # | 测试用例 | 预期结果 |
|---|---------|---------|
| C1 | `?role=MODERATOR` | 仅返回 MODERATOR 用户 |
| C2 | `?status=BANNED` | 仅返回 BANNED 用户 |
| C3 | `?username=admin` | 用户名包含 admin 的用户 |

---

**文档结束** ✅
