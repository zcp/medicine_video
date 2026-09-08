# 用户行为模块 Pydantic 模型代码生成提示词

**版本**: V1.0  
**创建日期**: 2026-01-18  
**基于设计文档**: 直播核心功能设计文档_v6_用户行为模块设计文档-收藏-观看历史-订阅提醒.md  
**目标文件**: `backend/live_core_service/app/schemas/user_behavior.py`

---

## 1. 角色定义

你是一名精通 Pydantic v2 和 FastAPI 的资深后端工程师。你的任务是为 `LiveCore Service` 的**用户行为模块**生成一组 Pydantic Schema，用于：

- API 入参（Create/Update 请求体）；
- API 出参（单项和列表响应）；
- 统一响应结构中的业务数据部分。

这些 Schema 必须与设计文档和即将生成的 `app/models/user_behavior.py` 模型保持字段和约束上的一致。  

---

## 2. 任务目标

在 `backend/live_core_service/app/schemas/user_behavior.py` 中生成以下 Schema：

1. 收藏相关：
   - `FavoriteCreate`：创建收藏请求体（例如收藏房间）。
   - `FavoriteItem`：单条收藏记录（用于列表返回）。
   - `FavoriteListResponse`：收藏列表分页/集合响应。

2. 观看历史相关：
   - `WatchEventRequest`：记录观看事件的请求体（包含 session_id、progress 等）。
   - `WatchHistoryItem`：单条观看历史记录。
   - `WatchHistoryListResponse`：观看历史列表分页/集合响应。

3. 订阅提醒相关：
   - `SubscriptionCreate`：创建订阅请求体（target_type + room_id/session_id）。
   - `SubscriptionItem`：单条订阅记录。
   - `SubscriptionListResponse`：订阅列表响应。

以及必要的枚举和基础类型：
- `SubscriptionTargetType`：与模型层枚举保持一致（`room` / `session`）。

---

## 3. 核心约束 (根据设计文档摘要)

### 3.1 用户收藏（favorites）

根据 `user_favorites` 表设计：

- `user_id`：在 API 层**不作为显式字段**，从 JWT 的 `user_id` 中提取，不出现在请求体中。
- `room_id`：必填，UUID，指向 `live_rooms.id`。
- `is_active`：在 API 入参中通常不暴露，由后端控制；在出参中可以展示当前收藏状态。
- `created_at`：只读字段，出参中展示。

由此推导 Schema：

- `FavoriteCreate`：
  - 字段：`room_id: UUID`
  - 不包含 `user_id`、`is_active`、`created_at`（后端填充）。

- `FavoriteItem`：
  - 字段：`id: UUID`, `room_id: UUID`, `is_active: bool`, `created_at: datetime`

- `FavoriteListResponse`：
  - 参考全局分页/列表响应规范，可以是：
    - 简单列表：`items: List[FavoriteItem]`
    - 或带分页：`total, page, size, items`（根据项目统一的 ListResponse 模式选择，需与其它模块一致）。

### 3.2 观看历史（watch_history）

根据设计文档 `watch_history` 设计要点：

- 仅关联 `session_id`，不直接暴露 `room_id`。  
- 记录字段包括：`progress`（观看进度，秒）、`watched_at`（时间戳）、`is_latest`（是否最新记录）。
- `user_id` 同样由 JWT 提取，不出现在请求体中。

Schema 约束：

- `WatchEventRequest`：
  - 字段：
    - `session_id: UUID`（必填）
    - `progress: int`（可选或必填，`ge=0`）
  - 不包含 `user_id`、`watched_at`、`is_latest`（后端自动维护）。

- `WatchHistoryItem`：
  - 字段示例：`id, session_id, progress, watched_at, is_latest`。

- `WatchHistoryListResponse`：
  - 与收藏列表类似，采用统一的分页/列表结构。

### 3.3 订阅提醒（user_subscriptions）

设计要点：

- `target_type`：订阅目标类型，`room` 或 `session`。
- `room_id` 和 `session_id` 至少一个不为 NULL，取决于 `target_type`。
- `is_active`：软删除标志。

Schema 约束：

- `SubscriptionCreate`：
  - 字段：
    - `target_type: SubscriptionTargetType`（必填）
    - `room_id: Optional[UUID]`（当 target_type 为 room 时必填）
    - `session_id: Optional[UUID]`（当 target_type 为 session 时必填）
  - 在 Pydantic 层做简单校验：根据 `target_type` 检查对应字段非空。

- `SubscriptionItem`：
  - 字段：`id, target_type, room_id, session_id, is_active, created_at` 等。

- `SubscriptionListResponse`：
  - 使用统一的列表/分页结构。

---

## 4. 实现规范

请在 `user_behavior.py` Schema 文件中遵循以下规范：

1. 使用 Pydantic v2 风格：
   - `from pydantic import BaseModel, Field`
   - 使用 `ConfigDict(from_attributes=True)` 支持 ORM 模式。

2. 枚举与模型对齐：
   - Schema 层的 `SubscriptionTargetType` 必须与模型层同名枚举保持值一致。

3. 字段约束：
   - 使用 `Field(..., description="...")` 描述关键字段含义（如 `progress`, `target_type`）。
   - 对需要非负的整型字段（如 `progress`）使用 `ge=0` 约束。

4. 列表/分页响应：
   - 推荐复用项目中已有的通用分页结构（如 `PaginatedData`），如果有的话；
   - 否则，在本模块内定义简单的 `total/page/size/items` 结构，并与其它模块保持一致。

5. 只读/写入字段区分：
   - Create 请求体不包含只读字段（如 `id`, `created_at`, `is_active`）。
   - 出参 Item 模型包含这些只读字段，方便前端展示。

---

## 5. 输出要求

最终输出应是完整的 `schemas/user_behavior.py` 文件内容，包含上述所有 Schema 定义，且：

- 字段名、类型与数据库模型和设计文档一致；
- 不包含任何业务逻辑，只做数据结构定义和轻量级验证；
- 可以被 `schemas/__init__.py` 导入使用。*** End Patch***}‬‬
