# 用户行为模块设计文档-收藏-观看历史-订阅提醒 SQLAlchemy 模型与 Pydantic Schema 一致性检查提示词

**版本**: V1.0  
**创建日期**: 2026-01-18  
**适用于**: 用户行为模块 SQLAlchemy 模型与 Pydantic Schema 一致性检查  
**基于文档**: `docs/03_系统设计/直播核心功能设计文档_v6_用户行为模块设计文档-收藏-观看历史-订阅提醒.md`

---

## 1. 角色定义 (Role Definition)

你是一名资深的 FastAPI / SQLAlchemy 架构师，负责审查**用户行为模块**中：

- SQLAlchemy 模型：`backend/live_core_service/app/models/user_behavior.py`
- Pydantic Schema：`backend/live_core_service/app/schemas/user_behavior.py`

之间的一致性、安全性和 API 适配性。

你的核心目标是确认：

- Pydantic Schemas 是否是 Model 的合理"投影"（不多暴露、不少暴露、类型正确）。  
- 不会因为字段缺失或类型错误导致 API 行为与设计文档不符。  

---

## 2. 核心输入 (Core Input)

### 2.1 SQLAlchemy 模型代码

**文件路径**: `backend/live_core_service/app/models/user_behavior.py`

> 【在实际执行检查时，请先完整粘贴 `app/models/user_behavior.py` 的代码到这里作为上下文。】

### 2.2 Pydantic Schema 代码

**文件路径**: `backend/live_core_service/app/schemas/user_behavior.py`

> 【在实际执行检查时，请先完整粘贴 `app/schemas/user_behavior.py` 的代码到这里作为上下文。】

---

## 3. 审查清单 (Audit Checklist)

### 3.1 字段命名与映射关系

**检查要点**：

- [ ] `UserFavorite` ↔ `FavoriteCreate` / `FavoriteItem` / `FavoriteListResponse`  
- [ ] `WatchHistory` ↔ `WatchEventRequest` / `WatchHistoryItem` / `WatchHistoryListResponse`  
- [ ] `UserSubscription` ↔ `SubscriptionCreate` / `SubscriptionItem` / `SubscriptionListResponse`  

请构造类似下表的对照关系（示意）：

| Model 字段                      | 对应 Schema 字段                    | 是否一致 | 备注                      |
|---------------------------------|--------------------------------------|---------|---------------------------|
| `UserFavorite.id`              | `FavoriteItem.id`                   | ?       | UUID 主键                 |
| `UserFavorite.room_id`         | `FavoriteCreate.room_id`, `FavoriteItem.room_id` | ? | 直播间 ID                 |
| `UserFavorite.is_active`       | `FavoriteItem.is_active`            | ?       | 软删除标记                |
| `UserFavorite.created_at`      | `FavoriteItem.created_at`           | ?       | 创建时间                  |
| `WatchHistory.session_id`      | `WatchEventRequest.session_id`, `WatchHistoryItem.session_id` | ? | 场次 ID            |
| `WatchHistory.progress`        | `WatchEventRequest.progress`, `WatchHistoryItem.progress`     | ? | 观看进度（秒）      |
| `WatchHistory.watched_at`      | `WatchHistoryItem.watched_at`       | ?       | 观看时间                  |
| `WatchHistory.is_latest`       | `WatchHistoryItem.is_latest`        | ?       | 是否最新记录              |
| `UserSubscription.target_type` | `SubscriptionCreate.target_type`, `SubscriptionItem.target_type` | ? | 订阅目标类型   |
| `UserSubscription.target_id`   | `SubscriptionCreate.target_id`, `SubscriptionItem.target_id`     | ? | 订阅目标 ID（根据 target_type 指向 room 或 session） |
| `UserSubscription.is_active`   | `SubscriptionItem.is_active`        | ?       | 是否仍然订阅              |
| `UserSubscription.created_at`  | `SubscriptionItem.created_at`       | ?       | 订阅创建时间              |

**特别说明**：

- `user_id` 字段属于"用户身份上下文"，通过 JWT 注入，不应该出现在 Create 请求体中；只在 Model 中存在，Schema 中只用于响应时只读（如果需要暴露）。  
- 如果某些内部字段（例如统计字段）不需要对外暴露，可以只出现在 Model，不出现在 Schema，但必须在审查报告中说明理由。  

### 3.2 数据类型兼容性

**检查项**：

- [ ] `UUID(as_uuid=True)` ↔ `uuid.UUID`  
- [ ] `Boolean` ↔ `bool`  
- [ ] `Integer` ↔ `int`（必要时加 `ge=0` 限制，如 `progress`）  
- [ ] `TIMESTAMP(timezone=True)` ↔ `datetime`  
- [ ] `SAEnum(SubscriptionTargetType)` ↔ `SubscriptionTargetType(str, Enum)`  

请构造一个简单的类型映射表，验证每个字段的类型是否对应。

### 3.3 Create / Request Schema 正确性

重点审查以下 Schemas：  

- `FavoriteCreate`：  
  - 只包含 `room_id`；不应包含 `user_id`、`is_active`、`created_at`。  
  - 确认字段名与业务设计一致。  

- `WatchEventRequest`：  
  - 必须包含 `session_id`，可以包含 `progress`（非负整数）。  
  - 不应包含 `user_id`、`watched_at`、`is_latest`。  

- `SubscriptionCreate`：  
  - 必须包含 `target_id` 和 `target_type`；  
  - `target_id` 根据 `target_type` 指向 `live_rooms.id` 或 `live_sessions.id`（应用层验证）。  

检查点：

- [ ] Create 请求体中是否误包含只读字段（`id`, `created_at`, `is_active` 等）。  
- [ ] 是否有缺少业务必须字段的情况。  

### 3.4 响应结构合理性

对 `FavoriteListResponse`、`WatchHistoryListResponse`、`SubscriptionListResponse` 审查：  

- [ ] 是否采用了项目统一的列表/分页模式（如 `items` 或 `total/page/size/items`）。  
- [ ] `items` 中的元素是否为对应的 Item Schema。  
- [ ] 是否需要在 Schema 上添加额外的验证或说明（如最大长度、默认值）。  

---

## 4. 输出要求 (Review Output)

请基于上述清单输出一份审查结果，结构建议如下：

1. **总览**：简单说明整体一致性情况（基本一致 / 存在若干问题）。  
2. **字段映射表**：逐字段填写"是否一致"和备注。  
3. **问题列表**：列出发现的问题，例如：  
   - 某字段在 Model 中存在，但在 Schema 中缺失；  
   - 某字段类型不匹配（如 `Integer` ↔ `str`）；  
   - Create 请求体暴露了不该暴露的字段。  
4. **修复建议**：对每个问题给出明确建议（修改 Model 还是 Schema，如何改）。  

如果没有发现问题，请明确写出“一致性检查通过，未发现问题”。*** End Patch***} */
