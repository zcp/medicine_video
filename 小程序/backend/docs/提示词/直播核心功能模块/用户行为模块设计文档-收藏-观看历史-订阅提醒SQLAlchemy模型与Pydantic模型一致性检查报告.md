# 用户行为模块设计文档-收藏-观看历史-订阅提醒 SQLAlchemy 模型与 Pydantic Schema 一致性检查报告

## 1. 总体评估

**审查日期**: 2026-01-18  
**模块名称**: 用户行为模块 - 收藏 / 观看历史 / 订阅提醒  
**审查人**: AI一致性检测系统  

---

## 2. 符合性评分

| 检查项             | 通过/失败 | 问题数量 | 说明                                   |
|--------------------|----------|---------|----------------------------------------|
| 字段命名一致性     | 通过     | 0       | Model 与 Schema 字段命名一致           |
| 数据类型兼容性     | 通过     | 0       | UUID/Boolean/Integer/时间类型映射正确  |
| Create Schema 审查 | 通过     | 0       | 请求体不暴露 user_id 等内部字段        |
| Response Schema 审查 | 通过   | 0       | 只返回需要的字段，结构清晰             |
| 默认值与语义       | 通过     | 0       | 软删除/最新标记语义在 Schema 中保持一致 |
| 枚举类型一致性     | 通过     | 0       | SubscriptionTargetType 完全一致         |

**总体评分**: 6/6 ✅  

---

## 3. 详细检查结果

### 3.1 字段命名与映射关系

#### 3.1.1 UserFavorite ↔ 收藏 Schema

- Model:  
  - `UserFavorite.id`  
  - `UserFavorite.user_id`  
  - `UserFavorite.room_id`  
  - `UserFavorite.is_active`  
  - `UserFavorite.created_at`  

- Schema:  
  - `FavoriteCreate(room_id)`  
  - `FavoriteItem(id, room_id, is_active, created_at)`  
  - `FavoriteListResponse(items: List[FavoriteItem])`  

**结论**：  

- `[一致]` `room_id`、`is_active`、`created_at`、`id` 等字段在 Schema 中都有清晰映射；  
- `[预期缺失但合理]` `user_id` 只在 Model 中存在，通过 JWT 提供，不在请求体/响应体中暴露，符合设计文档“user_id 来源于 Token”的要求。  

#### 3.1.2 WatchHistory ↔ 观看历史 Schema

- Model:  
  - `WatchHistory.id`  
  - `WatchHistory.user_id`  
  - `WatchHistory.session_id`  
  - `WatchHistory.progress`  
  - `WatchHistory.watched_at`  
  - `WatchHistory.is_latest`  

- Schema:  
  - `WatchEventRequest(session_id, progress?)`  
  - `WatchHistoryItem(id, session_id, progress?, watched_at, is_latest)`  
  - `WatchHistoryListResponse(items: List[WatchHistoryItem])`  

**结论**：  

- `[一致]` 所有业务相关字段（`session_id`、`progress`、`watched_at`、`is_latest`）都有一一对应的 Schema 字段；  
- `[预期缺失但合理]` `user_id` 只存在于 Model，用于权限和过滤，不对前端暴露。  

#### 3.1.3 UserSubscription ↔ 订阅 Schema

- Model:  
  - `UserSubscription.id`  
  - `UserSubscription.user_id`  
  - `UserSubscription.target_type`  
  - `UserSubscription.room_id`  
  - `UserSubscription.session_id`  
  - `UserSubscription.is_active`  
  - `UserSubscription.created_at`  

- Schema:  
  - `SubscriptionCreate(target_type, room_id?, session_id?)`  
  - `SubscriptionItem(id, target_type, room_id?, session_id?, is_active, created_at)`  
  - `SubscriptionListResponse(items: List[SubscriptionItem])`  

**结论**：  

- `[一致]` `target_type`、`room_id`、`session_id`、`is_active`、`created_at`、`id` 在 Schema 中都有对应字段；  
- `[预期缺失但合理]` `user_id` 作为当前登录用户上下文，不暴露在请求体/响应体中。  

---

### 3.2 数据类型兼容性

- `PG_UUID(as_uuid=True)` ↔ `uuid.UUID`：  
  - 用于所有 ID 字段（`id`、`room_id`、`session_id`、`user_id`），Schema 对这些对外暴露的字段全部使用 `uuid.UUID` 类型。  

- `Boolean` ↔ `bool`：  
  - `is_active`, `is_latest` 在 Schema 中为 `bool`，并带有描述说明语义。  

- `Integer` ↔ `int`：  
  - `progress` 在 Schema 中使用 `Optional[int]` 且使用 `Field(ge=0)` 做下界校验。  

- `TIMESTAMP(timezone=True)` ↔ `datetime`：  
  - `created_at`, `watched_at` 在 Schema 中都使用 `datetime` 类型。  

- `SAEnum(SubscriptionTargetType)` ↔ Enum `SubscriptionTargetType(str, Enum)`：  
  - 枚举成员 `ROOM="room"`, `SESSION="session"` 在 Model 与 Schema 中完全一致。  

**结论**：  

- `[一致]` 所有字段类型和约束在 ORM 与 Schema 间映射正确，无异常类型转换。  

---

### 3.3 Create / Request Schema 审查

#### 3.3.1 FavoriteCreate

- 仅包含：`room_id: uuid.UUID`；  
- 不包含：`id`、`user_id`、`is_active`、`created_at` 等内部或只读字段。  

**结论**：`[一致]` 完全符合设计“当前用户收藏直播间”的接口语义。  

#### 3.3.2 WatchEventRequest

- 字段：  
  - `session_id: uuid.UUID`  
  - `progress: Optional[int] = Field(None, ge=0)`  
- 不包含 `user_id`、`watched_at`、`is_latest`。  

**结论**：`[一致]` 请求体只承载用户上报的信息，其余由服务端补全。  

#### 3.3.3 SubscriptionCreate

- 字段：  
  - `target_type: SubscriptionTargetType`  
  - `room_id: Optional[uuid.UUID]`  
  - `session_id: Optional[uuid.UUID]`  
- “当 target_type=room 时 room_id 必填；当 target_type=session 时 session_id 必填”的约束由 Service 层实现。  

**结论**：`[一致]` 请求体与设计文档的参数约束匹配。  

---

### 3.4 响应 Schema 审查

- `FavoriteItem` / `WatchHistoryItem` / `SubscriptionItem` 均：  
  - 设置 `model_config = ConfigDict(from_attributes=True)`；  
  - 完整反映了需要对前端暴露的字段，无多余内部字段。  

- 列表响应：  
  - `FavoriteListResponse(items: List[FavoriteItem])`  
  - `WatchHistoryListResponse(items: List[WatchHistoryItem])`  
  - `SubscriptionListResponse(items: List[SubscriptionItem])`  

**结论**：`[一致]` 列表 Schema 结构简单清晰，符合项目其他模块的风格。  

---

## 4. 关键问题清单

### 4.1 严重问题 (必须修复)

无。  

### 4.2 中等问题 (建议修复)

无。  

### 4.3 轻微问题 (可选修复)

无。  

---

## 5. 一致性总结

**总体评估**: ✅ **完全一致**  

**说明**：  

1. ORM 与 Schema 在字段名、类型、默认值和业务语义上保持一致；  
2. 所有请求体 Schema 都避免暴露 `user_id` 等内部字段，符合“从 JWT 读取用户身份”的设计；  
3. 响应 Schema 仅返回对前端有意义的字段，未引入实现细节；  
4. 可以将本次检查结果作为后续 CRUD/Service/API 自动化代码与测试生成的坚实基础。  

