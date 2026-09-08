# 用户行为模块设计文档-收藏-观看历史-订阅提醒 设计摘要（测试对齐用）

**设计文档**: `docs/03_系统设计/直播核心功能设计文档_v6_用户行为模块设计文档-收藏-观看历史-订阅提醒.md`  
**模块名**: `user_behavior`  
**范围**: 用户收藏、观看历史、订阅提醒  

---

## 1. 数据表与字段定义（DDL 摘要）

### 1.1 user_favorites（用户收藏表）

- 主键：`id UUID PRIMARY KEY`  
- 字段：
  - `user_id UUID NOT NULL`  
    - 含义：用户公开 ID，对应 `users.public_id`  
    - 说明：跨服务引用，不加数据库外键，应用层通过 JWT 中的 `user_id` 验证  
  - `room_id UUID NOT NULL`  
    - 外键：`live_rooms.id`，`ON DELETE CASCADE`  
  - `is_active BOOLEAN NOT NULL DEFAULT true`  
    - 语义：软删除标记，`true=已收藏`，`false=已取消`  
  - `created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP`  
- 约束：
  - `UNIQUE (user_id, room_id)` 名称：`uq_user_favorites_user_room`  
- 索引：
  - `idx_user_favorites_user_id (user_id)`  
  - `idx_user_favorites_room_id (room_id)`  
  - `idx_user_favorites_user_active (user_id, is_active) WHERE is_active = true`  

### 1.2 watch_history（观看历史表）

- 主键：`id UUID PRIMARY KEY`  
- 字段：
  - `user_id UUID NOT NULL`  
  - `session_id UUID NOT NULL` → `live_sessions.id`，`ON DELETE CASCADE`  
  - `progress INT NULL`（观看进度，秒）  
  - `watched_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP`  
  - `is_latest BOOLEAN NOT NULL DEFAULT true`（该用户该场次的最新记录）  
- 索引：
  - `idx_watch_history_user_session (user_id, session_id)`  
  - `idx_watch_history_is_latest (user_id, is_latest)`  

### 1.3 user_subscriptions（用户订阅提醒表）

- 主键：`id UUID PRIMARY KEY`  
- 字段：
  - `user_id UUID NOT NULL`  
  - `target_type ENUM('room','session') NOT NULL`（枚举名：`subscription_target_type`）  
  - `room_id UUID NULL` → `live_rooms.id`，`ON DELETE CASCADE`（`target_type='room'` 时有效）  
  - `session_id UUID NULL` → `live_sessions.id`，`ON DELETE CASCADE`（`target_type='session'` 时有效）  
  - `is_active BOOLEAN NOT NULL DEFAULT true`（软删除标记）  
  - `created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP`  
- 约束：
  - `UNIQUE (user_id, target_type, room_id, session_id)` 名称：`uq_user_subscriptions_user_target`  
- 索引：
  - `idx_user_subscriptions_user_id (user_id)`  

---

## 2. API 端点设计摘要

所有端点都属于“当前登录用户”的行为，路径前缀为 `/users/me/...`，统一响应结构为：

```json
{
  "code": 200,
  "message": "success",
  "data": { ... } | null,
  "timestamp": "2025-10-23T10:00:00Z"
}
```

### 2.1 收藏相关 API

- `POST /api/v1/users/me/favorites`  
  - 功能：为当前用户收藏指定直播间  
  - 请求体：`{ "room_id": UUID }`  
  - 行为：  
    - 如不存在记录 → 创建 `user_favorites` 记录（is_active=true）  
    - 如存在 `is_active=false` 的历史记录 → 恢复为 `true`  
    - 如存在 `is_active=true` 的记录 → 返回“资源已存在”的业务异常（错误码属全局业务码体系）  

- `GET /api/v1/users/me/favorites`  
  - 功能：获取当前用户收藏列表  
  - 查询参数：可选 `limit`（或简单分页），设计文档主张简单 limit 模式  
  - 行为：仅返回 `is_active=true` 的记录，按 `created_at` 降序  

- `DELETE /api/v1/users/me/favorites/{room_id}`  
  - 功能：取消收藏  
  - 行为：  
    - 将匹配 `(user_id, room_id)` 的记录 `is_active` 置为 `false`  
    - 幂等性：如不存在记录或已为 `false`，操作应返回成功但不报错  

### 2.2 观看历史 API

- `POST /api/v1/users/me/watch-history`  
  - 功能：记录观看事件 / 更新观看进度  
  - 请求体：  
    - `session_id: UUID`  
    - `progress?: int >= 0`（可空，表示只打开不记录进度）  
  - 行为：  
    - 将该用户对该场次已有的 `is_latest=true` 记录改为 `false`；  
    - 插入新的 `watch_history` 记录，`is_latest=true`。  

- `GET /api/v1/users/me/watch-history`  
  - 功能：获取当前用户的观看历史  
  - 查询参数：`limit` 等（简单限制条数）  
  - 行为：  
    - 仅返回 `is_latest=true` 的记录；  
    - 按 `watched_at` 降序。  

### 2.3 订阅提醒 API

- `POST /api/v1/users/me/subscriptions`  
  - 功能：创建订阅记录  
  - 请求体：  
    - `target_type: "room" | "session"`  
    - `room_id?: UUID`（`target_type="room"` 时必填）  
    - `session_id?: UUID`（`target_type="session"` 时必填）  
  - 行为：  
    - 校验 `target_type` 与 `room_id` / `session_id` 组合的有效性；  
    - 查询是否已存在 `(user_id, target_type, room_id, session_id, is_active=true)`；  
    - 如有 → 抛出“订阅已存在”的业务异常；  
    - 如有 `is_active=false` 的历史记录 → 恢复为 `true`；  
    - 否则创建新记录。  

- `GET /api/v1/users/me/subscriptions`  
  - 功能：获取当前用户的订阅列表  
  - 查询参数：`target_type?`  
  - 行为：  
    - 返回 `is_active=true` 的记录，可按 `target_type` 过滤。  

- `DELETE /api/v1/users/me/subscriptions`  
  - 功能：取消订阅  
  - 查询参数：  
    - `target_type` + `room_id` / `session_id` 的组合  
  - 行为：  
    - 查找匹配记录，并将 `is_active` 设为 `false`；  
    - 未找到匹配记录时视为幂等成功。  

---

## 3. 权限与认证设计摘要

- 所有用户行为接口为 **Strict Auth**：  
  - 必须携带 JWT：`Authorization: Bearer <token>`  
  - API 层统一使用 `Depends(get_current_user)` 注入用户信息。  

- JWT Payload 关键字段：  
  - `user_id`: 用户公开 ID（`users.public_id`），本模块所有 `user_id` 字段引用此值；  
  - `role`: 角色（`REGULAR` / `MODERATOR` / `ADMIN` / `SUPERADMIN`）。  

- 权限分层：
  - **API 层**：只做认证（Authentication），解析 `user_id`、`role`，不做复杂授权；  
  - **Service 层**：负责 Authorization（是否允许当前用户对某资源进行收藏/订阅/查看），可实现 `_check_write_permission` 等守卫函数；  
  - **CRUD 层**：在 SQL 层面按 `user_id` 过滤数据，不做角色判断。  

- 专门说明：
  - 收藏、观看历史、订阅提醒均为“用户专属资源”，用户只能访问和修改自己的记录；  
  - 尝试访问他人资源时，应通过权限逻辑返回业务错误或 404 隐藏存在性（参考权限设计文档的通用约定）。  

---

## 4. 关键业务规则（测试应覆盖）

1. **收藏相关**  
   - 相同 `(user_id, room_id)` 的有效收藏仅允许存在一条；  
   - 取消收藏为软删除（`is_active=false`）；  
   - 重复收藏必须有明确业务行为（恢复 or 抛异常，当前设计为“已存在时视为错误”）；  
   - 所有查询/取消操作只作用于当前登录用户。  

2. **观看历史**  
   - 同一 `(user_id, session_id)` 的 `is_latest=true` 记录在任意时刻只能有一条；  
   - 记录观看事件时，必须正确更新旧记录的 `is_latest=false`；  
   - 查询历史时只看最新记录列表。  

3. **订阅提醒**  
   - `(user_id, target_type, room_id, session_id)` 组合必须唯一；  
   - 对不同 target（room/session）使用不同字段（只允许一侧非空）；  
   - 重复订阅应被拒绝或转为恢复历史订阅；  
   - 取消订阅必须是幂等操作。  

---

> 本摘要文件用于：  
> - 测试提示词生成（测试代码生成提示词会引用本摘要作为“真相源”）；  
> - 一致性检测（判断测试代码与实现是否偏离设计文档）。  

