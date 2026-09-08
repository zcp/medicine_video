# 用户行为模块 - CRUD/Service/API代码生成提示词母版

**模块名称**: user_behavior  
**功能模块名称**: 用户行为模块设计文档-收藏-观看历史-订阅提醒  
**版本**: V1.0  
**生成日期**: 2026-01-18  

---

## 1. 模块概述

用户行为模块用于管理与用户行为相关的数据，包括：

- 用户收藏 (UserFavorite / `user_favorites`)  
- 观看历史 (WatchHistory / `watch_history`)  
- 订阅提醒 (UserSubscription / `user_subscriptions`)  

核心场景：

- 用户收藏/取消收藏直播间；  
- 记录用户观看直播场次的进度（支持区分最新记录）；  
- 用户对房间/场次的订阅与取消订阅，用于开播提醒等。  

---

## 2. 项目上下文信息

### 2.1 项目结构

```text
backend/live_core_service/
├── app/
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user_behavior.py        ✅ 已生成（步骤2）
│   │   └── ...
│   ├­­── schemas/
│   │   ├── __init__.py
│   │   ├── user_behavior.py        ✅ 已生成（步骤2）
│   │   └── ...
│   ├── crud/
│   │   ├── __init__.py
│   │   ├── user_behavior.py        ⏳ 待生成（步骤6.1）
│   │   └── ...
│   ├── services/
│   │   ├── __init__.py
│   │   ├── user_behavior_service.py ⏳ 待生成（步骤6.2）
│   │   └── ...
│   ├── api/
│   │   └── v1/
│   │       ├── api.py              ⏳ 需更新路由注册（步骤6.4）
│   │       └── endpoints/
│   │           ├── __init__.py
│   │           ├── user_behavior.py ⏳ 待生成（步骤6.3）
│   │           └── ...
```

### 2.2 设计文档路径

- 主设计文档: `docs/03_系统设计/直播核心功能设计文档_v6_用户行为模块设计文档-收藏-观看历史-订阅提醒.md`  
- 权限设计与安全规范：  
  - `docs/03_系统设计/直播核心功能设计文档_v6_增加权限设计版.md`  
  - `docs/03_系统设计/直播核心功能设计文档----配置与安全优化方案.md`

---

## 3. Model 与 Schema 摘要（基于实际代码）

> **说明**：本节只保留关键字段摘要，完整定义请从 `app/models/user_behavior.py` 与 `app/schemas/user_behavior.py` 动态读取。

### 3.1 UserFavorite 模型 / 收藏相关 Schema

**表名**: `user_favorites`

| 字段名      | 类型           | 约束                      | 默认值       | 说明                                      |
|-------------|----------------|---------------------------|--------------|-------------------------------------------|
| `id`        | UUID (PK)      | PRIMARY KEY               | uuid.uuid4() | 收藏记录ID                                |
| `user_id`   | UUID           | NOT NULL                  | -            | 用户公开ID（users.public_id）             |
| `room_id`   | UUID (FK)      | NOT NULL, FK→live_rooms   | -            | 直播间ID                                  |
| `is_active` | Boolean        | NOT NULL                  | True         | 是否有效：true=已收藏，false=已取消       |
| `created_at`| TIMESTAMP(TZ)  | NOT NULL                  | now()        | 创建时间                                  |

约束/索引：

- `UNIQUE (user_id, room_id)` (`uq_user_favorites_user_room`)  
- 索引：`idx_user_favorites_user_id`, `idx_user_favorites_room_id`, `idx_user_favorites_user_active`  

Schema 对应：

- `FavoriteCreate(room_id)`  
- `FavoriteItem(id, room_id, is_active, created_at)`  
- `FavoriteListResponse(items: List[FavoriteItem])`

### 3.2 WatchHistory 模型 / 观看历史 Schema

**表名**: `watch_history`

| 字段名       | 类型           | 约束                     | 默认值       | 说明                                  |
|--------------|----------------|--------------------------|--------------|---------------------------------------|
| `id`         | UUID (PK)      | PRIMARY KEY              | uuid.uuid4() | 观看记录ID                            |
| `user_id`    | UUID           | NOT NULL                 | -            | 用户公开ID                            |
| `session_id` | UUID (FK)      | NOT NULL, FK→live_sessions | -         | 直播场次ID                            |
| `progress`   | Integer        | NULLABLE                 | NULL         | 观看进度（秒）                        |
| `watched_at` | TIMESTAMP(TZ)  | NOT NULL                 | now()        | 观看时间                              |
| `is_latest`  | Boolean        | NOT NULL                 | True         | 是否为该用户该场次的最新记录          |

索引：

- `idx_watch_history_user_session (user_id, session_id)`  
- `idx_watch_history_is_latest (user_id, is_latest)`  

Schema 对应：

- `WatchEventRequest(session_id, progress?)`  
- `WatchHistoryItem(id, session_id, progress?, watched_at, is_latest)`  
- `WatchHistoryListResponse(items: List[WatchHistoryItem])`

### 3.3 UserSubscription 模型 / 订阅 Schema

**表名**: `user_subscriptions`

| 字段名        | 类型                         | 约束                        | 默认值       | 说明                          |
|---------------|------------------------------|-----------------------------|--------------|-------------------------------|
| `id`          | UUID (PK)                    | PRIMARY KEY                 | uuid.uuid4() | 订阅记录ID                    |
| `user_id`     | UUID                         | NOT NULL                    | -            | 用户公开ID                    |
| `target_type` | Enum(SubscriptionTargetType) | NOT NULL                    | -            | 订阅目标类型：room / session |
| `room_id`     | UUID (FK)                    | NULLABLE, FK→live_rooms     | NULL         | 订阅房间ID                    |
| `session_id`  | UUID (FK)                    | NULLABLE, FK→live_sessions  | NULL         | 订阅场次ID                    |
| `is_active`   | Boolean                      | NOT NULL                    | True         | 是否仍然订阅                  |
| `created_at`  | TIMESTAMP(TZ)                | NOT NULL                    | now()        | 创建时间                      |

约束/索引：

- `UNIQUE (user_id, target_type, room_id, session_id)` (`uq_user_subscriptions_user_target`)  
- 納入 `idx_user_subscriptions_user_id` 索引  

Schema 对应：

- `SubscriptionCreate(target_type, room_id?, session_id?)`  
- `SubscriptionItem(id, target_type, room_id?, session_id?, is_active, created_at)`  
- `SubscriptionListResponse(items: List[SubscriptionItem])`

---

## 4. CRUD/Service/API 设计原则

### 4.1 CRUD 层设计 (user_behavior)

**职责**：

- 针对 `UserFavorite` / `WatchHistory` / `UserSubscription` 提供标准的 CRUD 函数：  
  - `create_favorite`, `get_favorite`, `get_user_favorites`, `delete_favorite`, `list_favorites`  
  - `create_or_update_watch_history`, `get_watch_history`, `list_watch_history`  
  - `create_subscription`, `get_subscription`, `list_subscriptions`, `delete_subscription`  

**关键点**：

- 所有函数为 `async def`，接受 `AsyncSession` 作为第一个参数。  
- 不在 CRUD 内部执行 `commit()`，只使用 `add()` / `flush()` / 查询，由 Service 层控制事务。  
- 捕获 `IntegrityError`，抛出 `DatabaseIntegrityException`，并记录日志（UUID 仅记录前8位）。  

### 4.2 Service 层设计 (user_behavior_service)

**职责**：

- 业务编排和权限控制：  
  - 收藏：`add_favorite`, `remove_favorite`, `get_favorites`  
  - 观看历史：`record_watch_event`, `get_watch_history`  
  - 订阅：`subscribe`, `unsubscribe`, `get_subscriptions`  

**权限与规则**：

- 所有操作均需 Strict Auth (`current_user: dict = Depends(get_current_user)`)；  
- 使用权限守卫函数（可重用通用的 `_check_authenticated_user` 或 `_check_user_owner`）：  
  - 收藏/观看/订阅均为"当前用户"自身数据，不允许操作他人数据；  
- 写操作由 Service 层负责 `commit()` / `rollback()`。  

### 4.3 API 层设计 (endpoints/user_behavior.py)

**路由前缀与分组**：

- 收藏相关：`/users/me/favorites`  
- 观看历史：`/users/me/watch-history`  
- 订阅提醒：`/users/me/subscriptions`  

**路由定义（示例）**：

- 收藏：
  - `POST /users/me/favorites` — 创建收藏  
  - `GET /users/me/favorites` — 获取当前用户的收藏列表  
  - `DELETE /users/me/favorites/{room_id}` — 取消收藏  

- 观看历史：
  - `POST /users/me/watch-history` — 上报观看事件（含进度）  
  - `GET /users/me/watch-history` — 获取当前用户观看历史列表（可选过滤）  

- 订阅提醒：
  - `POST /users/me/subscriptions` — 新增订阅  
  - `GET /users/me/subscriptions` — 获取订阅列表  
  - `DELETE /users/me/subscriptions/{subscription_id}` 或基于目标条件取消订阅  

**路由前缀与命名规范**（与母版保持一致）：

- API 层路由统一挂载到 `app/api/v1/api.py` 的 `api_router` 上：  

```python
from app.api.v1.endpoints import user_behavior

api_router.include_router(
    user_behavior.router,
    prefix="/api/v1",
    tags=["用户行为"],
)
```

> **注意**：在 `user_behavior.router` 内部再细分前缀（如 `/users/me/favorites`、`/users/me/watch-history` 等），避免在 `api_router` 注册时重复前缀。

---

## 5. 交付物 (Deliverables)

基于本母版，后续需要生成以下文件：

1. **CRUD 层提示词文档**  
   - 路径：`docs/提示词/直播核心功能模块/用户行为模块设计文档-收藏-观看历史-订阅提醒---CRUD层代码生成提示词.md`  
   - 用于生成 `backend/live_core_service/app/crud/user_behavior.py`。  

2. **Service/API 层提示词文档**  
   - 路径：`docs/提示词/直播核心功能模块/用户行为模块设计文档-收藏-观看历史-订阅提醒---Service层和API层代码生成提示词.md`  
   - 用于生成：  
     - `backend/live_core_service/app/services/user_behavior_service.py`  
     - `backend/live_core_service/app/api/v1/endpoints/user_behavior.py`。  

这两个提示词文档在生成时必须：

- 复用本母版第3节的 Model / Schema 摘要（不要重复写死字段，保持与实际代码动态对齐）；  
- 严格遵守通用 CRUD/Service/API 设计规范（事务、权限、日志、路由前缀、响应结构等）；  
- 不硬编码设计文档内容，而是引用并总结关键点。*** End Patch***}"/>
