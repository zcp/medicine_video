

# **后端修改与新增需求 API 详细设计文档 (V3.1)**

**目标**: 本文档基于 `后端修改与新增需求设计文档 (V3.0)`，为其中列出的 API 接口修改和新增提供详细的设计规范，包括 Pydantic Schema 定义、成功/失败响应示例以及实现流程描述，确保与现有后端文档规范完全一致，以支持前后端并行开发。

**遵循规范**:

  * **通用响应结构**: `{ code: int, message: str, data: object|null, timestamp: str }`。
  * **分页格式**: 请求 (`page`, `size`, `sort`)，响应 (`total`, `page`, `size`, `items`)。
  * **状态码**: 遵循 HTTP 状态码和业务 `code` 约定。
  * **认证**: 默认需要 JWT Bearer Token (`Depends(get_current_user)`)，公开接口会特别注明。
  * **授权**: Service 层负责权限校验（所有权或角色）。
  * **数据库与字段**: 严格使用已定义的表和字段。
  * **日志与异常**: 遵循规范。

-----

## 模块一：Room 模块 (直播核心功能)

本模块涵盖了直播间（Room）和直播场次（Session）的核心功能，包括列表获取、详情、创建、更新以及标签功能。

### API 接口

#### 1\. `GET /api/v1/rooms` (通用房间列表) - *增强*

  * **描述**：获取通用的房间列表，响应体中新增了 `summary` 字段。

  * **返回类型 (Pydantic Schema)**：
    响应体 `data` 字段为一个标准分页对象，其 `items` 列表中的元素类型为 `RoomListItem`。

    ```python
    class RoomListItem(BaseModel):
        id: uuid.UUID
        title: str
        cover_url: Optional[str] = None
        summary: Optional[str] = None # <-- 新增字段
        created_at: datetime

        class Config:
            from_attributes = True
    ```

  * **返回值 (成功响应示例 - `data` 字段)**：

    ```json
    {
      "total": 50,
      "page": 1,
      "size": 10,
      "items": [
        {
          "id": "a1b2c3d4-e5f6-4a1b-8c3d-e5f6a1b2c3d4",
          "title": "新产品发布会直播",
          "cover_url": "/media/rooms/a1b2.../cover.png",
          "summary": "介绍我们即将发布的 v3.0 版本。", // <-- 新增字段
          "created_at": "2025-07-07T19:10:00Z"
        }
        // ... more items
      ]
    }
    ```

  * **执行流程**：

    1.  验证 JWT Token (如果需要认证访问)。
    2.  解析分页、排序参数。
    3.  构建 SQLAlchemy 查询 `select(LiveRoom)`。
    4.  (如果需要) 添加 `user_id` 筛选。
    5.  执行 `count()` 查询获取 `total`。
    6.  应用 `order_by`, `offset`, `limit`。
    7.  确保查询包含 `live_rooms.summary` 字段。
    8.  执行查询获取 `items`。
    9.  将结果映射到 `RoomListItem` Schema。
    10. 记录 DEBUG 日志。
    11. 返回标准分页响应。

-----

#### 2\. `GET /api/v1/sessions/{session_id}` (获取场次详情) - *增强*

  * **描述**：获取特定场次的详细信息，响应体中新增了主讲专家 (`featured_expert`) 和标签 (`tags`) 字段。

  * **返回类型 (Pydantic Schema)**：
    响应体 `data` 字段为 `SessionDetail` 对象。

    ```python
    class TagInfo(BaseModel):
        id: uuid.UUID
        name: str
        class Config: from_attributes = True

    class ExpertInfo(BaseModel):
        id: uuid.UUID # experts.id
        user_id: Optional[uuid.UUID] = None # users.public_id, if linked
        name: str
        title: Optional[str] = None
        hospital: Optional[str] = None
        avatar_url: Optional[str] = None
        bio: Optional[str] = None
        class Config: from_attributes = True

    class SessionDetail(BaseModel):
        id: uuid.UUID
        room_id: uuid.UUID
        room_title: str # From joined live_rooms
        status: LiveStatusEnum 
        start_time: datetime
        end_time: Optional[datetime] = None
        # ... other existing session fields ...
        playback_url: Optional[str] = None
        featured_expert: Optional[ExpertInfo] = None # <-- 新增对象
        tags: List[TagInfo] = [] # <-- 新增列表
        statistics: Optional[SessionStatisticsResponse] = None

        class Config:
            from_attributes = True
    ```

  * **返回值 (成功响应示例 - `data` 字段)**：

    ```json
    {
      "id": "session_uuid_1",
      "room_id": "a1b2...",
      "room_title": "肝胆胰外科手术直播演示",
      "status": "live", 
      "start_time": "2025-10-22T08:00:00Z",
      "end_time": null,
      "playback_url": null,
      "featured_expert": { // <-- 新增
          "id": "expert_uuid_doc_B",
          "user_id": null,
          "name": "李四 教授",
          "title": "主任医师",
          "hospital": "XX 医院",
          "avatar_url": "/media/experts/.../avatar.jpg",
          "bio": "专注于微创肝胆手术..."
      },
      "tags": [ // <-- 新增
          {"id": "tag_uuid_1", "name": "微创手术"},
          {"id": "tag_uuid_2", "name": "肝胆外科"}
      ],
      "statistics": {
          "current_viewer_count": 1250,
          "peak_viewer_count": 1300
      }
    }
    ```

  * **执行流程**：

    1.  验证 JWT Token (如果需要认证)。
    2.  根据 `session_id` 查询 `live_sessions ls`。
    3.  `JOIN live_rooms lr ON ls.room_id = lr.id` (获取 `room_title`)。
    4.  `LEFT JOIN experts fe ON ls.featured_expert_id = fe.id` (获取主讲专家信息)。
    5.  使用子查询或单独查询 + JOIN 来获取通过 `session_tags` 关联的 `tags`。
    6.  `LEFT JOIN session_statistics ss ON ls.id = ss.session_id` (获取统计)。
    7.  如果未找到 `session`，返回 404。
    8.  构建 `playback_url` (仅当 `status` 为 'ready')。
    9.  将查询结果映射到 `SessionDetail` Schema，包括嵌套的 `featured_expert` 和 `tags`。
    10. 记录 DEBUG/INFO 日志。
    11. 返回标准响应。

-----

#### 3\. `POST /api/v1/rooms/{room_id}/sessions` (创建计划场次) - *增强*

  * **描述**：创建新的直播场次，请求体中新增了 `featured_expert_id` 字段。

  * **请求体类型 (Pydantic Schema)**：

    ```python
    class SessionCreateRequest(BaseModel):
        title: str
        description: Optional[str] = None
        scheduled_start_time: datetime
        featured_expert_id: Optional[uuid.UUID] = None # <-- 新增字段
        # ... other fields ...
    ```

  * **返回值 (成功响应示例)**：

      * (文档未明确提供成功响应示例，但通常会返回新创建的 Session 详细信息，类似于 `GET /api/v1/sessions/{session_id}` 的 `SessionDetail` 结构体)。

  * **执行流程 (补充)**：

    1.  (验证 `room_id`, 解析请求体)...
    2.  **验证 `featured_expert_id`**：如果 `featured_expert_id` 在请求中提供且不为 `None`，查询 `experts` 表确认该 ID 存在。如果不存在，返回 400 Bad Request (业务码 `4xxx`)，说明专家 ID 无效。
    3.  创建 `live_sessions` 实例时，设置 `featured_expert_id` 字段。
    4.  (创建 `session_statistics`, 存入数据库, 返回响应)...

-----

#### 4\. `PATCH /api/v1/sessions/{session_id}` (更新计划场次) - *增强*

  * **描述**：更新已有的直播场次，请求体中新增了 `featured_expert_id` 字段。

  * **请求体类型 (Pydantic Schema)**：

    ```python
    class SessionUpdateRequest(BaseModel):
        title: Optional[str] = None
        description: Optional[str] = None
        scheduled_start_time: Optional[datetime] = None
        featured_expert_id: Optional[uuid.UUID] = None # <-- 新增字段
        # ... other fields ...
    ```

  * **返回值 (成功响应示例)**：

      * (文档未明确提供成功响应示例，但通常会返回更新后的 Session 详细信息，类似于 `GET /api/v1/sessions/{session_id}` 的 `SessionDetail` 结构体)。

  * **执行流程 (补充)**：

    1.  (查询 `session`, 检查 `status` 是否允许修改)...
    2.  **验证 `featured_expert_id`**：如果 `featured_expert_id` 在请求中提供，查询 `experts` 表确认该 ID 存在。如果不存在，返回 400 Bad Request。
    3.  遍历 `SessionUpdateRequest` 中的非 `None` 字段，更新 `session` 对象，包括 `featured_expert_id`。
    4.  (提交事务, 返回响应)...

-----

#### 5\. `POST /api/v1/rooms/{room_id}/favorite` (新增)

  * **描述**：用户收藏一个直播间。 (依赖 `user_favorites` 表)。

  * **返回类型 (Pydantic Schema)**：
    响应体 `data` 字段为 `FavoriteResponse` 对象。

    ```python
    class FavoriteResponse(BaseModel):
        id: uuid.UUID # ID of the created user_favorites record
        user_id: uuid.UUID
        room_id: uuid.UUID
        created_at: datetime
    ```

  * **返回值 (成功响应示例)**：

    ```json
    {
        "code": 200, "message": "success",
        "data": {
            "id": "fav_uuid_1",
            "user_id": "user_public_id_1",
            "room_id": "room_uuid_target",
            "created_at": "2025-10-22T10:30:00Z"
        },
        "timestamp": "..."
    }
    ```

  * **执行流程**：

    1.  验证 JWT Token, 获取 `user_id` (public\_id)。
    2.  从路径参数获取 `room_id`。
    3.  查询 `live_rooms` 确认 `room_id` 存在，否则 404。
    4.  查询 `user_favorites` 检查 `(user_id, room_id)` 是否已存在，若存在则 409。
    5.  创建 `user_favorites` 记录，填充 `user_id`, `room_id`。
    6.  `await db.commit()`, `await db.refresh()`。
    7.  记录 INFO 日志。
    8.  返回新创建的 `FavoriteResponse`。

-----

#### 6\. `DELETE /api/v1/rooms/{room_id}/favorite` (新增)

  * **描述**：用户取消收藏一个直播间。 (依赖 `user_favorites` 表)。

  * **返回类型 (Pydantic Schema)**：
    响应体 `data` 字段为 `DeleteStatus` 对象。

    ```python
    class DeleteStatus(BaseModel):
        id: uuid.UUID # ID of the deleted resource (room_id in this context)
        status: str = "deleted"
    ```

  * **返回值 (成功响应示例)**：

    ```json
    {
        "code": 200, "message": "success",
        "data": { "id": "room_uuid_target", "status": "deleted" },
        "timestamp": "..."
    }
    ```

  * **执行流程**：

    1.  验证 JWT Token, 获取 `user_id` (public\_id)。
    2.  从路径参数获取 `room_id`。
    3.  查询 `user_favorites` 记录 WHERE `user_id = :user_id` AND `room_id = :room_id`。
    4.  如果未找到记录，返回 404。
    5.  `await db.delete(favorite_record)`。
    6.  `await db.commit()`。
    7.  记录 INFO/WARN 日志。
    8.  返回 `DeleteStatus` 响应。

-----

#### 7\. `POST /api/v1/sessions/{session_id}/subscribe` (新增)

  * **描述**：用户订阅一个场次的开播提醒。 (依赖 `user_subscriptions` 表)。

  * **返回类型 (Pydantic Schema)**：
    响应体 `data` 字段为 `SubscriptionResponse` 对象。

    ```python
    class SubscriptionResponse(BaseModel):
        id: uuid.UUID # ID of the created user_subscriptions record
        user_id: uuid.UUID
        target_id: uuid.UUID
        target_type: str # 'session' or 'room'
        created_at: datetime
    ```

  * **返回值 (成功响应示例)**：

    ```json
    {
        "code": 200, "message": "success",
        "data": {
            "id": "sub_uuid_1",
            "user_id": "user_public_id_1",
            "target_id": "session_uuid_target",
            "target_type": "session",
            "created_at": "2025-10-22T10:40:00Z"
        },
        "timestamp": "..."
    }
    ```

  * **执行流程**：

    1.  验证 JWT Token, 获取 `user_id` (public\_id)。
    2.  从路径参数获取 `session_id`。
    3.  查询 `live_sessions` 确认 `session_id` 存在，否则 404。
    4.  查询 `user_subscriptions` 检查 `(user_id, session_id, 'session')` 是否已存在，若存在则 409。
    5.  创建 `user_subscriptions` 记录，填充 `user_id`, `target_id = session_id`, `target_type = 'session'`。
    6.  `await db.commit()`, `await db.refresh()`。
    7.  记录 INFO 日志。
    8.  返回新创建的 `SubscriptionResponse`。

-----

#### 8\. `POST /api/v1/rooms/{room_id}/subscribe` (新增 - 可选)

  * **描述**：用户订阅一个直播间（所有场次）的开播提醒。 (依赖 `user_subscriptions` 表)。
  * **返回类型 (Pydantic Schema)**：
    `SubscriptionResponse` (与订阅 Session 相同)。
  * **返回值 (成功响应示例)**：
      * (文档未明确提供，但结构同上，`target_id` 为 `room_id`，`target_type` 为 `"room"`)。
  * **执行流程**：
      * 逻辑与订阅 Session 非常相似，仅 `target_id` 为 `room_id`，`target_type` 为 `'room'`，并验证 `live_rooms` 存在性。

-----

#### 9\. `POST /api/v1/sessions/{session_id}/watch-event` (新增)

  * **描述**：上报用户观看事件/进度。 (依赖 `watch_history` 表)。

  * **请求体类型 (Pydantic Schema)**：

    ```python
    class WatchEventRequest(BaseModel):
        progress: Optional[int] = Field(None, ge=0, description="Current watch progress in seconds")
    ```

  * **返回值 (成功响应示例)**：

    ```json
    { "code": 200, "message": "success", "data": null, "timestamp": "..." }
    ```

  * **执行流程**：

    1.  验证 JWT Token, 获取 `user_id` (public\_id)。
    2.  从路径参数获取 `session_id`。
    3.  查询 `live_sessions` 确认 `session_id` 存在，否则 404。
    4.  获取请求体中的 `progress` (如果提供)。
    5.  **处理逻辑** (根据业务需求选择)：
          * **选项A (记录每次事件)**：直接创建一条 `watch_history` 记录，包含 `user_id`, `session_id`, `watched_at = NOW()`, `progress`。
          * **选项B (只保留最新)**：查询 `watch_history` 是否已有 `(user_id, session_id)` 记录。若有，则更新 `watched_at` 和 `progress`；若无，则创建新记录。
    6.  `await db.commit()`。
    7.  记录 DEBUG/INFO 日志 (可能频率很高，注意日志级别)。
    8.  返回成功响应。

-----

* **`live_rooms` 表**:
    * **确认**: `category_id UUID NULL` 字段已存在。
    * [cite_start]**新增**: `summary VARCHAR(255)` 字段 。

* **`live_sessions` 表**:
    * **新增**: `featured_expert_id UUID NULL REFERENCES experts(id) ON DELETE SET NULL` 字段。
    * **(可选)**: `summary VARCHAR(255)` 字段。

* **`tags` 表 (新增)**:
    ```sql
    CREATE TABLE tags (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        name VARCHAR(50) NOT NULL UNIQUE,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    COMMENT ON TABLE tags IS '内容标签表';
    ```

* **`session_tags` 表 (新增)**:
    ```sql
    CREATE TABLE session_tags (
        session_id UUID NOT NULL REFERENCES live_sessions(id) ON DELETE CASCADE,
        tag_id UUID NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
        PRIMARY KEY (session_id, tag_id)
    );
    COMMENT ON TABLE session_tags IS '直播场次与标签的多对多关联表';
    ```

* **`watch_history` 表 (新增)**:
    ```sql
    CREATE TABLE watch_history (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        user_id UUID NOT NULL REFERENCES users(public_id) ON DELETE CASCADE,
        session_id UUID NOT NULL REFERENCES live_sessions(id) ON DELETE CASCADE,
        watched_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        progress INT DEFAULT 0 -- Optional: 观看进度 (秒)
        -- Consider adding UNIQUE(user_id, session_id) if only latest watch event is needed
    );
    CREATE INDEX idx_watch_history_user_session ON watch_history(user_id, session_id);
    CREATE INDEX idx_watch_history_watched_at ON watch_history(user_id, watched_at DESC);
    COMMENT ON TABLE watch_history IS '用户观看历史记录表';
    ```
  

# 模块二：User & Expert 模块（用户、专家核心功能）

本模块定义了用户（User）的扩展功能（如通知、收藏、历史）以及新增的专家（Expert）实体及其管理功能。

---

## 📘 API 接口

### 1. `GET /api/v1/users/me/notifications` （新增）

**描述：** 获取当前用户的通知列表（分页）。
**认证：** JWT Token 必需。

#### 请求参数

| 参数   | 类型  | 默认值             | 说明   |
| ---- | --- | --------------- | ---- |
| page | int | 1               | 页码   |
| size | int | 10              | 每页数量 |
| sort | str | created_at:desc | 排序字段 |

#### 返回类型（Pydantic Schema）

```python
class NotificationItem(BaseModel):
    id: uuid.UUID
    title: str
    content: Optional[str] = None
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True
```

#### 成功响应示例

```json
{
  "total": 12,
  "page": 1,
  "size": 10,
  "items": [
    {
      "id": "notification_uuid_1",
      "title": "您的订阅即将开始",
      "content": "您订阅的 '肝胆胰外科手术直播演示' 将在 10 分钟后开始。",
      "is_read": false,
      "created_at": "2025-10-22T07:50:00Z"
    },
    {
      "id": "notification_uuid_2",
      "title": "欢迎使用",
      "content": "欢迎您注册平台。",
      "is_read": true,
      "created_at": "2025-10-21T14:00:00Z"
    }
  ]
}
```

#### 执行流程

1. 验证 JWT，获取 `user_id`。
2. 查询 `notifications WHERE user_id = :user_id`。
3. 应用排序、分页。
4. 执行查询，映射到 Schema，返回分页响应。

---

### 2. `POST /api/v1/users/me/notifications/{notification_id}/read` （新增）

**描述：** 将单条通知标记为已读。
**认证：** JWT Token 必需。
**请求体：** 无。

#### 返回类型（Pydantic Schema）

`data` 字段为 `null`。

#### 成功响应示例

```json
{
  "code": 200,
  "message": "success",
  "data": null,
  "timestamp": "2025-10-22T08:00:00Z"
}
```

#### 执行流程

1. 验证 JWT，获取 `user_id`。
2. 查询 `notifications WHERE id = :notification_id AND user_id = :user_id`。
3. 若未找到，返回 404（业务码 2001/2004）。
4. 更新 `is_read = true`。
5. 提交事务并返回成功响应。

---

### 3. `GET /api/v1/users/me/favorites` （新增）

**描述：** 获取当前用户的收藏直播间列表。
**认证：** JWT Token 必需。

#### 请求参数

| 参数   | 类型  | 默认值             | 说明   |
| ---- | --- | --------------- | ---- |
| page | int | 1               | 页码   |
| size | int | 10              | 每页数量 |
| sort | str | created_at:desc | 排序字段 |

#### 返回类型（Pydantic Schema）

```python
class FavoriteRoomInfo(BaseModel):
    room_id: uuid.UUID
    title: str
    cover_url: Optional[str] = None
    summary: Optional[str] = None
    favorited_at: datetime

    class Config:
        from_attributes = True
```

#### 成功响应示例

```json
{
  "total": 1,
  "page": 1,
  "size": 10,
  "items": [
    {
      "room_id": "room_uuid_target",
      "title": "新产品发布会直播",
      "cover_url": "/media/rooms/a1b2.../cover.png",
      "summary": "介绍我们即将发布的 v3.0 版本。",
      "favorited_at": "2025-10-22T10:30:00Z"
    }
  ]
}
```

#### 执行流程

1. 验证 JWT，获取 `user_id`。
2. 联表查询 `user_favorites` 与 `live_rooms`。
3. 应用排序、分页，返回结果。

---

### 4. `GET /api/v1/users/me/history` （新增）

**描述：** 获取当前用户的观看历史记录。
**认证：** JWT Token 必需。

#### 返回类型（Pydantic Schema）

```python
class HistoryItem(BaseModel):
    session_id: uuid.UUID
    room_id: uuid.UUID
    session_title: str
    room_cover_url: Optional[str] = None
    watched_at: datetime
    progress: Optional[int] = None

    class Config:
        from_attributes = True
```

#### 成功响应示例

```json
{
  "total": 5,
  "page": 1,
  "size": 10,
  "items": [
    {
      "session_id": "session_uuid_watched",
      "room_id": "room_uuid_3",
      "session_title": "基础操作演示 (回放)",
      "room_cover_url": "/media/rooms/.../cover3.jpg",
      "watched_at": "2025-10-22T11:00:00Z",
      "progress": 120
    }
  ]
}
```

#### 执行流程

1. 验证 JWT，获取 `user_id`。
2. 联表查询 `watch_history`、`live_sessions`、`live_rooms`。
3. 使用 `DISTINCT ON` 或 `ROW_NUMBER()` 去重。
4. 返回分页结果。

---

### 5. `GET /api/v1/featured-experts` （新增）

**描述：** 获取首页推荐的专家列表。
**认证：** 公开访问。

#### 请求参数

| 参数    | 类型  | 默认值 | 说明         |
| ----- | --- | --- | ---------- |
| limit | int | 10  | 数量限制（1~50） |

#### 返回类型（Pydantic Schema）

```python
class FeaturedExpertItem(BaseModel):
    expert_id: uuid.UUID
    user_id: Optional[uuid.UUID] = None
    name: str
    title: Optional[str] = None
    hospital: Optional[str] = None
    avatar_url: Optional[str] = None

    class Config:
        from_attributes = True
```

#### 成功响应示例

```json
[
  {
    "expert_id": "expert_uuid_doc_B",
    "user_id": null,
    "name": "李四 教授",
    "title": "主任医师",
    "hospital": "XX 医院",
    "avatar_url": "/media/experts/.../avatar.jpg"
  },
  {
    "expert_id": "expert_uuid_doc_C",
    "user_id": "user_uuid_C",
    "name": "王五 主任",
    "title": "骨科主任",
    "hospital": "YY 医院",
    "avatar_url": "/media/experts/.../avatar_c.jpg"
  }
]
```

---

### 6. `GET /api/v1/professors/{expert_id}/content` （新增）

**描述：** 获取指定专家的详细信息及其关联的直播场次。
**认证：** 公开访问。

#### 返回类型（Pydantic Schema）

```python
class ExpertDetail(ExpertInfo):
    department: Optional[str] = None
    expertise_areas: Optional[str] = None

class ExpertContentResponse(BaseModel):
    expert_info: ExpertDetail
    sessions: dict  # 分页结构
```

#### 成功响应示例

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "expert_info": {
      "id": "expert_uuid_doc_B",
      "name": "李四 教授",
      "title": "主任医师",
      "hospital": "XX 医院",
      "bio": "专注于微创肝胆手术...",
      "department": "肝胆外科",
      "expertise_areas": "微创手术, 肝脏移植"
    },
    "sessions": {
      "total": 5,
      "page": 1,
      "size": 10,
      "items": [
        {
          "id": "session_uuid_1",
          "title": "肝胆胰外科手术直播演示",
          "status": "replay",
          "start_time": "2025-10-22T08:00:00Z"
        }
      ]
    }
  },
  "timestamp": "2025-10-22T08:00:00Z"
}
```

---

### 7. `POST /api/v1/admin/experts` （新增 - Admin）

**描述：** 管理员创建新专家记录。
**认证：** JWT Token + ADMIN/SUPERADMIN。
**请求体：** `ExpertCreate`。

---

### 8. `PATCH /api/v1/admin/experts/{expert_id}` （新增 - Admin）

**描述：** 管理员更新专家信息。
**认证：** JWT Token + ADMIN/SUPERADMIN。
**请求体：** `ExpertUpdate`。

---

### 9. `DELETE /api/v1/admin/experts/{expert_id}` （新增 - Admin）

**描述：** 管理员删除专家记录。
**认证：** JWT Token + ADMIN/SUPERADMIN。

#### 返回类型

```python
class DeleteStatus(BaseModel):
    id: uuid.UUID
    status: str = "deleted"
```

#### 成功响应示例

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": "expert_uuid_to_delete",
    "status": "deleted"
  },
  "timestamp": "2025-10-22T08:00:00Z"
}
```

---

## 🗄 数据库 Schema 定义

### `experts` 表（新增）

```sql
CREATE TABLE experts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID UNIQUE NULL REFERENCES users(public_id) ON DELETE SET NULL,
    name VARCHAR(100) NOT NULL,
    title VARCHAR(100),
    hospital VARCHAR(150),
    department VARCHAR(100),
    expertise_areas TEXT,
    avatar_url VARCHAR(512),
    bio TEXT,
    is_featured BOOLEAN DEFAULT false,
    sort_order INT DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_experts_user_id ON experts(user_id);
CREATE INDEX idx_experts_is_featured ON experts(is_featured, sort_order);

COMMENT ON TABLE experts IS '专家信息表';
```

---

### `notifications` 表（新增）

```sql
CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(public_id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    content TEXT,
    is_read BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_notifications_user_id ON notifications(user_id);
COMMENT ON TABLE notifications IS '用户通知表';
```

---

### `user_favorites` 表（新增）

```sql
CREATE TABLE user_favorites (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(public_id) ON DELETE CASCADE,
    room_id UUID NOT NULL REFERENCES live_rooms(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (user_id, room_id)
);

CREATE INDEX idx_user_favorites_user_id ON user_favorites(user_id);
COMMENT ON TABLE user_favorites IS '用户收藏直播间关联表';
```

---

### `user_subscriptions` 表（新增）

```sql
CREATE TYPE subscription_target_type AS ENUM ('room', 'session');

CREATE TABLE user_subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(public_id) ON DELETE CASCADE,
    target_id UUID NOT NULL,
    target_type subscription_target_type NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (user_id, target_id, target_type)
);

CREATE INDEX idx_user_subscriptions_user_target ON user_subscriptions(user_id, target_id, target_type);
COMMENT ON TABLE user_subscriptions IS '用户订阅开播提醒表';
```


-----

## 3\. Topic 模块 (专题功能)

  * **(保持不变)**: 与 User 和 Room 集成。

-----

## 4\. 新增 全局分类 (Categories) 模块

### 4.1 API 接口

  * **`GET /api/v1/categories` (查询公开分类列表)**
      * **描述**: 获取所有全局医学内容分类。此接口为**公开访问**，用于客户端（如 App、Web）展示全部分类列表。
      * **认证**: **公开访问**。 (不需要 `Authorization` Header)
      * **标签**: `Categories`
      * **请求 (Query Parameters)**:
          * *此接口不支持分页或自定义排序。* (它始终返回所有项目，并按 `sort_order` 排序)。

      * **Pydantic Schema (响应体定义)**:

        ```python
        import uuid
        import datetime
        from typing import List, Optional
        from pydantic import BaseModel, Field

        # 规范中定义的列表项 Schema
        class CategoryItem(BaseModel):
            id: uuid.UUID
            name: str
            icon: Optional[str] = None
            sort_order: int

            class Config:
                from_attributes = True

        # 遵循“通用响应结构”规范
        # data 字段遵循 "成功响应 (200 OK - data): List[CategoryItem]" 规范
        class CategoryListResponse(BaseModel):
            code: int = Field(200, description="业务状态码")
            message: str = Field("Success", description="响应消息")
            data: List[CategoryItem] = Field(..., description="分类列表数据")
            timestamp: datetime.datetime = Field(..., description="ISO 8601 格式的时间戳")

        # 通用错误响应结构
        class ErrorResponse(BaseModel):
            code: int = Field(..., description="业务状态码 (非 200)")
            message: str = Field(..., description="错误信息")
            data: Optional[object] = Field(None, description="错误时 data 为 null")
            timestamp: datetime.datetime = Field(..., description="ISO 8601 格式的时间戳")
        ```

      * **成功响应 (200 OK)**:

          * **Response Body**: `CategoryListResponse`
          * **示例**:
            ```json
            {
                "code": 200,
                "message": "Success",
                "data": [
                    {
                        "id": "c9a0c6a8-0b1e-4b9e-8b0e-1c1a1a1a1a1a",
                        "name": "内科",
                        "icon": "icon-internal-medicine",
                        "sort_order": 0
                    },
                    {
                        "id": "d1b1b7b9-1c2f-4c0f-9c1f-2c2b2b2b2b2b",
                        "name": "外科",
                        "icon": "icon-surgery",
                        "sort_order": 1
                    }
                ],
                "timestamp": "2025-10-22T08:30:00.123Z"
            }
            ```

      * **错误响应**:

          * **`500 Internal Server Error`**:
              * **Response Body**: `ErrorResponse`
              * **描述**: 数据库查询失败或其他内部错误。
              * **示例**:
                ```json
                {
                    "code": 5001,
                    "message": "Database query failed.",
                    "data": null,
                    "timestamp": "2025-10-22T08:30:01.456Z"
                }
                ```

      * **实现流程**:

        1.  (认证): 无，此为公开接口。
        2.  (授权): 无，数据为公开数据。
        3.  (执行): `SELECT id, name, icon, sort_order FROM categories`。
        4.  (排序): `ORDER BY sort_order ASC`。 (遵循 `idx_categories_sort_order` 索引)。
        5.  (返回): 将查询结果列表（`List[CategoryItem]`）封装到标准 `CategoryListResponse` 结构中返回。
### 4.2 数据库 Schema

* **`categories` 表 (新增)**:
    ```sql
    CREATE TABLE categories (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        name VARCHAR(100) NOT NULL UNIQUE,
        icon VARCHAR(255), -- Optional icon URL/class
        sort_order INT DEFAULT 0,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX idx_categories_sort_order ON categories(sort_order);
    COMMENT ON TABLE categories IS '全局医学内容分类表';
    ```

### 4.3 后端逻辑 (Admin API 接口)

以下是为后台管理系统（Admin）提供的 `categories` 模块的 CRUD API 接口定义，所有接口默认都需要 Admin 权限认证。

#### 4.3.1 Pydantic Schemas (Admin)

```python
import uuid
import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

# 规范：通用响应结构
class CommonResponse(BaseModel):
    code: int = Field(..., description="业务状态码")
    message: str = Field(..., description="响应消息")
    data: Optional[object] = Field(None, description="响应数据")
    timestamp: datetime.datetime = Field(..., description="ISO 8601 格式的时间戳")

# --- Category Admin Schemas ---

# Admin 接口返回的完整 Category 结构
class CategoryAdminItem(BaseModel):
    id: uuid.UUID
    name: str
    icon: Optional[str] = None
    sort_order: int
    created_at: datetime.datetime
    updated_at: datetime.datetime
    
    class Config:
        from_attributes = True

# POST (Create) 请求体
class CategoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="分类名称 (必须唯一)")
    icon: Optional[str] = Field(None, max_length=255, description="图标 URL 或 class")
    sort_order: int = Field(0, description="排序值")

# PUT (Update) 请求体
class CategoryUpdate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="分类名称 (必须唯一)")
    icon: Optional[str] = Field(None, max_length=255, description="图标 URL 或 class")
    sort_order: int = Field(..., description="排序值")

# 规范：分页格式 (响应)
class PaginatedCategoryAdminList(BaseModel):
    total: int = Field(..., description="总项目数")
    page: int = Field(..., description="当前页码")
    size: int = Field(..., description="每页大小")
    items: List[CategoryAdminItem] = Field(..., description="当前页的项目列表")

# GET (List) 的成功响应 (data 字段)
class CategoryAdminListResponse(BaseModel):
    code: int = 200
    message: str = "Success"
    data: PaginatedCategoryAdminList
    timestamp: datetime.datetime

# GET (One) / POST / PUT 的成功响应 (data 字段)
class CategoryAdminDetailResponse(BaseModel):
    code: int = 200
    message: str = "Success"
    data: CategoryAdminItem
    timestamp: datetime.datetime
```
-----

#### 4.3.2 API 接口定义

  * **`POST /api/v1/admin/categories` (新增)**

      * **描述**: (Admin) 创建一个新的全局分类。
      * **认证**: **需要 (Admin 权限)**。
      * **标签**: `Admin: Categories`
      * **请求体 (Request Body)**: `CategoryCreate`
      * **成功响应 (201 Created)**:
          * **Response Body**: `CategoryAdminDetailResponse` (返回新创建的资源)
      * **错误响应**:
          * **`400 Bad Request`**: 请求体验证失败 (如 `name` 缺失)。
          * **`401 Unauthorized`**: 未认证。
          * **`403 Forbidden`**: 非 Admin 角色。
          * **`409 Conflict`**: `name` 字段违反唯一性约束 (已存在同名分类)。
      * **实现流程**:
        1.  (认证): `Depends(get_current_user)`，校验 Admin 角色。
        2.  (校验): Service 层校验 `name` 是否已存在 (Unique)。
        3.  (执行): 向 `categories` 表插入一条新记录。
        4.  (返回): 查询新生成的记录并返回 `CategoryAdminItem` 结构。

  * **`GET /api/v1/admin/categories` (查询列表 - 分页)**

      * **描述**: (Admin) 获取全局分类的**分页**列表，支持筛选和排序。
      * **认证**: **需要 (Admin 权限)**。
      * **标签**: `Admin: Categories`
      * **规范 (请求 - 分页)**:
          * `page: int = 1`
          * `size: int = 20`
          * `sort: Optional[str] = "sort_order:asc"` (e.g., "name:desc", "created\_at:asc")
      * **规范 (请求 - 筛选)**:
          * `name: Optional[str] = None` (用于模糊搜索 `name` 字段)
      * **成功响应 (200 OK)**:
          * **Response Body**: `CategoryAdminListResponse` (遵循分页格式规范)
      * **错误响应**:
          * **`400 Bad Request`**: `sort` 参数格式错误或 `page`/`size` 无效。
          * **`401 Unauthorized`**: 未认证。
          * **`403 Forbidden`**: 非 Admin 角色。
      * **实现流程**:
        1.  (认证): `Depends(get_current_user)`，校验 Admin 角色。
        2.  (解析): 解析 `page`, `size`, `sort` 和 `name` 筛选参数。
        3.  (查询 - Count): 执行 `COUNT(*)` 查询 (应用 `name` 筛选) 获取 `total`。
        4.  (查询 - List): 执行 `SELECT *` 查询 (应用 `name` 筛选、`sort` 排序、`LIMIT/OFFSET` 分页)。
        5.  (返回): 组装 `PaginatedCategoryAdminList` 结构并返回。

  * **`GET /api/v1/admin/categories/{category_id}` (查询详情)**

      * **描述**: (Admin) 获取特定 ID 的分类详情。
      * **认证**: **需要 (Admin 权限)**。
      * **标签**: `Admin: Categories`
      * **请求 (Path Parameters)**:
          * `category_id: uuid.UUID`
      * **成功响应 (200 OK)**:
          * **Response Body**: `CategoryAdminDetailResponse` (data 为 `CategoryAdminItem`)
      * **错误响应**:
          * **`401 Unauthorized`**: 未认证。
          * **`403 Forbidden`**: 非 Admin 角色。
          * **`404 Not Found`**: 提供的 `category_id` 在数据库中不存在。
      * **实现流程**:
        1.  (认证): `Depends(get_current_user)`，校验 Admin 角色。
        2.  (查询): `SELECT * FROM categories WHERE id = {category_id}`。
        3.  (校验): 如果未找到记录，返回 404。
        4.  (返回): 返回 `CategoryAdminItem` 结构。

  * **`PUT /api/v1/admin/categories/{category_id}` (更新)**

      * **描述**: (Admin) 更新指定 ID 的分类信息 (全量更新)。
      * **认证**: **需要 (Admin 权限)**。
      * **标签**: `Admin: Categories`
      * **请求 (Path Parameters)**:
          * `category_id: uuid.UUID`
      * **请求体 (Request Body)**: `CategoryUpdate`
      * **成功响应 (200 OK)**:
          * **Response Body**: `CategoryAdminDetailResponse` (返回更新后的资源)
      * **错误响应**:
          * **`400 Bad Request`**: 请求体验证失败。
          * **`401 Unauthorized`**: 未认证。
          * **`403 Forbidden`**: 非 Admin 角色。
          * **`404 Not Found`**: 提供的 `category_id` 在数据库中不存在。
          * **`409 Conflict`**: `name` 字段与*其他*记录冲突。
      * **实现流程**:
        1.  (认证): `Depends(get_current_user)`，校验 Admin 角色。
        2.  (校验): Service 层校验 `category_id` 是否存在 (若不存在则 404)。
        3.  (校验): Service 层校验 `name` 是否与*除自身以外*的其他记录冲突 (若冲突则 409)。
        4.  (执行): `UPDATE categories SET name=..., icon=..., sort_order=..., updated_at=NOW() WHERE id = {category_id}`。
        5.  (返回): 查询更新后的记录并返回 `CategoryAdminItem` 结构。

  * **`DELETE /api/v1/admin/categories/{category_id}` (删除)**

      * **描述**: (Admin) 删除指定 ID 的分类。
      * **认证**: **需要 (Admin 权限)**。
      * **标签**: `Admin: Categories`
      * **请求 (Path Parameters)**:
          * `category_id: uuid.UUID`
      * **成功响应 (200 OK)**:
          * **Response Body**: `CommonResponse` (data 字段为 `null`)
          * **示例**:
            ```json
            {
                "code": 200,
                "message": "Category deleted successfully",
                "data": null,
                "timestamp": "2025-10-22T08:45:00.123Z"
            }
            ```
      * **错误响应**:
          * **`401 Unauthorized`**: 未认证。
          * **`403 Forbidden`**: 非 Admin 角色。
          * **`404 Not Found`**: 提供的 `category_id` 在数据库中不存在。
          * **`409 Conflict`**: (业务逻辑) 如果分类仍被其他数据（如文章）引用，不允许删除。
      * **实现流程**:
        1.  (认证): `Depends(get_current_user)`，校验 Admin 角色。
        2.  (校验): Service 层校验 `category_id` 是否存在 (若不存在则 404)。
        3.  (授权/业务校验): Service 层校验该 `category_id` 是否仍被（例如 `articles` 表）引用。如果被引用，返回 409 Conflict。
        4.  (执行): `DELETE FROM categories WHERE id = {category_id}`。
        5.  (返回): 返回 `code: 200` 且 `data: null` 的通用响应。
-----

## 5\. 新增 品牌/合作伙伴 (Brands/Partners) 模块

### 5.1 API 接口

  * **`GET /api/v1/brands` (新增)**:

      * **认证**: 公开访问。
      * **Pydantic Schema (ListItem)**:
        ```python
        class BrandItem(BaseModel):
            id: uuid.UUID
            name: str
            logo_url: Optional[str] = None
            class Config: from_attributes = True
        ```
      * **成功响应 (200 OK - `data`)**: `List[BrandItem]` (Sorted by `sort_order`).
      * **实现流程**: Query `brands` table, `ORDER BY sort_order`, return list.

  * **`GET /api/v1/brands/{brand_id}/content` (新增)**:

      * **认证**: 公开访问。
      * **Pydantic Schema (Response - `data`)**:
        ```python
        class BrandDetail(BrandItem): # Extends basic info
            description: Optional[str] = None
            website_url: Optional[str] = None

        class AssociatedTopicInfo(BaseModel):
             id: uuid.UUID
             title: str
             banner_url: Optional[str] = None
             # Add other relevant Topic fields
             class Config: from_attributes = True

        class BrandContentResponse(BaseModel):
             brand_info: BrandDetail
             associated_topics: List[AssociatedTopicInfo] = []
        ```
      * **成功响应 (200 OK)**: `{ "code": 200, ..., "data": BrandContentResponse }`
      * **失败响应 (404 Not Found)**: Brand 不存在。 Code `2001`.
      * **实现流程**: Query `brands` by `brand_id` (404 if not found). Query `brand_topics bt JOIN topics t ON bt.topic_id = t.id` WHERE `bt.brand_id = :brand_id`. Combine results into `BrandContentResponse`.

### 5.2 数据库 Schema

* **`brands` 表 (新增)**:
    ```sql
    CREATE TABLE brands (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        name VARCHAR(100) NOT NULL UNIQUE,
        logo_url VARCHAR(512),
        description TEXT,
        website_url VARCHAR(255),
        sort_order INT DEFAULT 0,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX idx_brands_sort_order ON brands(sort_order);
    COMMENT ON TABLE brands IS '品牌/合作伙伴信息表';
    ```
* **(隐含) `brand_topics` 关联表 (新增)**:
    ```sql
    CREATE TABLE brand_topics (
        brand_id UUID NOT NULL REFERENCES brands(id) ON DELETE CASCADE,
        topic_id UUID NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
        PRIMARY KEY (brand_id, topic_id)
    );
    COMMENT ON TABLE brand_topics IS '品牌与专题的关联表';
    ```


### 5.3 后端逻辑

  * **(隐含 Admin API)**: `/admin/brands` CRUD and `/admin/brands/{id}/topics` association management needed.

-----

## 6\. 新增 其他 功能模块

### 6.1 全局搜索 (Search)

  * **`GET /api/v1/search` (新增)**:
      * **认证**: 公开访问 (或 JWT).
      * **请求参数 (Query)**: `q: str`, `page`, `size`, `type_filter: Optional[str] = Query(None, description="e.g., room, expert, topic")`.
      * **Pydantic Schema (ListItem)**:
        ```python
        class SearchResultItem(BaseModel):
            type: str # 'room', 'expert', 'topic', etc.
            id: uuid.UUID
            title: str
            summary: Optional[str] = None # Snippet or description
            match_score: Optional[float] = None # If using search engine
            # Add other common fields like cover_url if possible
        ```
      * **成功响应 (200 OK - `data`)**: Standard pagination response with `items: List[SearchResultItem]`.
      * **实现流程**: Delegate to Elasticsearch/Search Service or construct complex SQL query (using `ILIKE`, `UNION ALL`, potentially FTS indexes) across relevant tables (`live_rooms`, `experts`, `topics`, maybe `users`). Apply filtering, scoring (if applicable), pagination. Map results to `SearchResultItem`.

### 6.2 焦点图内容管理 (Featured Content)

  * **`GET /api/v1/featured-content` (新增)**:

      * **认证**: 公开访问。
      * **Pydantic Schema (ListItem)**:
        ```python
        class FeaturedItem(BaseModel):
            id: uuid.UUID
            title: str
            image_url: str
            target_url: Optional[str] = None
            class Config: from_attributes = True
        ```
      * **成功响应 (200 OK - `data`)**: `List[FeaturedItem]` (Sorted by `sort_order`).
      * **实现流程**: Query `featured_content` table WHERE `is_active = true` ORDER BY `sort_order`. Return list.

  * **数据库 Schema**:

      * **(已在 V3.0 中定义 - `featured_content` 示例)**

  * **后端逻辑**:

      * **(隐含 Admin API)**: `/admin/featured-content` CRUD needed.

-----

## 7\. 最终确认

*(保持 V3.0 的确认内容)*


* **`live_rooms` 表**:
    * **确认**: `category_id UUID NULL` 字段已存在。
    * [cite_start]**新增**: `summary VARCHAR(255)` 字段 。

* **`live_sessions` 表**:
    * **新增**: `featured_expert_id UUID NULL REFERENCES experts(id) ON DELETE SET NULL` 字段。
    * **(可选)**: `summary VARCHAR(255)` 字段。

* **`tags` 表 (新增)**:
    ```sql
    CREATE TABLE tags (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        name VARCHAR(50) NOT NULL UNIQUE,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    COMMENT ON TABLE tags IS '内容标签表';
    ```

* **`session_tags` 表 (新增)**:
    ```sql
    CREATE TABLE session_tags (
        session_id UUID NOT NULL REFERENCES live_sessions(id) ON DELETE CASCADE,
        tag_id UUID NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
        PRIMARY KEY (session_id, tag_id)
    );
    COMMENT ON TABLE session_tags IS '直播场次与标签的多对多关联表';
    ```
  
### 2.2 数据库 Schema 修改/新增

* **`users` 表**:
    * **确认**: **不**增加 `is_featured_expert`, `title`, `hospital` 字段。

* **`experts` 表 (新增)**:
    ```sql
    CREATE TABLE experts (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        user_id UUID UNIQUE NULL REFERENCES users(public_id) ON DELETE SET NULL,
        name VARCHAR(100) NOT NULL, -- 专家姓名
        title VARCHAR(100),         -- 专家头衔
        hospital VARCHAR(150),      -- 所属医院/机构
        department VARCHAR(100),    -- 所属科室
        expertise_areas TEXT,       -- 擅长领域
        avatar_url VARCHAR(512),    -- 专家头像
        bio TEXT,                   -- 专家简介
        is_featured BOOLEAN DEFAULT false, -- 是否在首页推荐
        sort_order INT DEFAULT 0,     -- 推荐排序
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX idx_experts_user_id ON experts(user_id);
    CREATE INDEX idx_experts_is_featured ON experts(is_featured, sort_order);
    COMMENT ON TABLE experts IS '专家信息表';
    ```

* **`notifications` 表 (新增)**:
    ```sql
    CREATE TABLE notifications (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        user_id UUID NOT NULL REFERENCES users(public_id) ON DELETE CASCADE,
        title VARCHAR(255) NOT NULL,
        content TEXT,
        is_read BOOLEAN DEFAULT false,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX idx_notifications_user_id ON notifications(user_id);
    COMMENT ON TABLE notifications IS '用户通知表';
    ```

* **`user_favorites` 表 (新增)**:
    ```sql
    CREATE TABLE user_favorites (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        user_id UUID NOT NULL REFERENCES users(public_id) ON DELETE CASCADE,
        room_id UUID NOT NULL REFERENCES live_rooms(id) ON DELETE CASCADE,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        UNIQUE (user_id, room_id)
    );
    CREATE INDEX idx_user_favorites_user_id ON user_favorites(user_id);
    COMMENT ON TABLE user_favorites IS '用户收藏直播间关联表';
    ```

* **`watch_history` 表 (新增)**:
    ```sql
    CREATE TABLE watch_history (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        user_id UUID NOT NULL REFERENCES users(public_id) ON DELETE CASCADE,
        session_id UUID NOT NULL REFERENCES live_sessions(id) ON DELETE CASCADE,
        watched_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        progress INT DEFAULT 0 -- Optional: 观看进度 (秒)
        -- Consider adding UNIQUE(user_id, session_id) if only latest watch event is needed
    );
    CREATE INDEX idx_watch_history_user_session ON watch_history(user_id, session_id);
    CREATE INDEX idx_watch_history_watched_at ON watch_history(user_id, watched_at DESC);
    COMMENT ON TABLE watch_history IS '用户观看历史记录表';
    ```

* **`user_subscriptions` 表 (新增)**:
    ```sql
    CREATE TYPE subscription_target_type AS ENUM ('room', 'session');
    CREATE TABLE user_subscriptions (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        user_id UUID NOT NULL REFERENCES users(public_id) ON DELETE CASCADE,
        target_id UUID NOT NULL,
        target_type subscription_target_type NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        UNIQUE (user_id, target_id, target_type)
    );
    CREATE INDEX idx_user_subscriptions_user_target ON user_subscriptions(user_id, target_id, target_type);
    COMMENT ON TABLE user_subscriptions IS '用户订阅开播提醒表';
    ```




```sql
    -- featured_content 表 (新增 - 示例)
    CREATE TABLE featured_content (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        title VARCHAR(255) NOT NULL,
        image_url VARCHAR(512) NOT NULL,
        target_url VARCHAR(512), -- Link destination
        sort_order INT DEFAULT 0,
        is_active BOOLEAN DEFAULT true,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX idx_featured_content_active_sort ON featured_content(is_active, sort_order);
    COMMENT ON TABLE featured_content IS '首页焦点图内容配置表';
```


#### **`GET /api/v1/homepage/rooms` (新增 - 首页专用)**

  * **认证**: 公开访问 (或根据业务决定是否需要登录)。
  * **请求参数 (Query)**:
      * `page: int = Query(1, ge=1)`
      * `size: int = Query(10, ge=1, le=100)`
      * `sort: Optional[str] = Query('heat:desc', description="Sort field and direction, e.g., 'heat:desc', 'start_time:asc'")`
      * `category_id: Optional[uuid.UUID] = Query(None, description="Filter by global category ID")`
  * **Pydantic Schema (Response - `data` 字段内的 `items` 元素)**:
    ```python
    from enum import Enum

    class LiveStatusEnum(str, Enum):
        LIVE = 'live'
        SCHEDULED = 'scheduled'
        REPLAY = 'replay'

    class HomepageHostInfo(BaseModel):
        expert_id: Optional[uuid.UUID] = None
        user_id: Optional[uuid.UUID] = None # User's public_id
        name: str # Display name (Expert name > User nickname)
        title: Optional[str] = None # From experts table
        hospital: Optional[str] = None # From experts table

        class Config:
            from_attributes = True

    class HomepageStatusData(BaseModel):
        # Fields relevant based on live_status
        viewer_count: Optional[int] = None # For 'live'
        start_time: Optional[datetime] = None # For 'scheduled'
        duration_seconds: Optional[int] = None # For 'replay'
        play_count: Optional[int] = None # Optional for 'replay'

        class Config:
            from_attributes = True

    class HomepageRoomItem(BaseModel):
        id: uuid.UUID # Room ID
        title: str
        cover_url: Optional[str] = None
        summary: Optional[str] = None
        live_status: LiveStatusEnum
        host: Optional[HomepageHostInfo] = None
        status_data: HomepageStatusData
        heat: Optional[int] = None

        class Config:
            from_attributes = True
    ```
  * **成功响应 (200 OK)**:
    ```json
    {
        "code": 200,
        "message": "success",
        "data": {
            "total": 15,
            "page": 1,
            "size": 10,
            "items": [
                {
                    "id": "room_uuid_1",
                    "title": "肝胆胰外科手术直播演示",
                    "cover_url": "/media/rooms/.../cover1.jpg",
                    "summary": "演示最新的微创技术...",
                    "live_status": "live",
                    "host": {
                        "expert_id": "expert_uuid_doc_B",
                        "user_id": null, // Doctor B is not a platform user
                        "name": "李四 教授", // From experts.name
                        "title": "主任医师", // From experts.title
                        "hospital": "XX 医院" // From experts.hospital
                    },
                    "status_data": {
                        "viewer_count": 1250,
                        "start_time": null,
                        "duration_seconds": null,
                        "play_count": null
                    },
                    "heat": 8500
                },
                {
                    "id": "room_uuid_2",
                    "title": "骨科病例讨论会 (预告)",
                    "cover_url": "/media/rooms/.../cover2.jpg",
                    "summary": "讨论罕见病例...",
                    "live_status": "scheduled",
                    "host": {
                        "expert_id": "expert_uuid_doc_C",
                        "user_id": "user_uuid_C", // Doctor C is also the streamer
                        "name": "王五 主任", // From experts.name
                        "title": "骨科主任", // From experts.title
                        "hospital": "YY 医院" // From experts.hospital
                    },
                    "status_data": {
                        "viewer_count": null,
                        "start_time": "2025-10-25T19:30:00Z",
                        "duration_seconds": null,
                        "play_count": null
                    },
                    "heat": null
                },
                {
                   "id": "room_uuid_3",
                   "title": "基础操作演示 (回放)",
                   "cover_url": "/media/rooms/.../cover3.jpg",
                   "summary": "适合新手学习...",
                   "live_status": "replay",
                   "host": { // Streamer is not an expert
                        "expert_id": null,
                        "user_id": "user_uuid_A",
                        "name": "张三", // From users.nickname
                        "title": null,
                        "hospital": null
                   },
                   "status_data": {
                       "viewer_count": null,
                       "start_time": null,
                       "duration_seconds": 3650,
                       "play_count": 500
                   },
                   "heat": 1500 // Can be calculated based on historical data
                }
                // ... more items
            ]
        },
        "timestamp": "2025-10-22T10:00:00Z"
    }
    ```
  * **实现流程**:
    1.  (如果需要认证) 验证 JWT Token。
    2.  解析 `page`, `size`, `sort`, `category_id` 参数。
    3.  执行复杂的 SQLAlchemy 查询 (或原生 SQL) - **核心**:
          * `FROM live_rooms lr`
          * Apply `WHERE lr.category_id = :cat_id` if `category_id` is provided.
          * Use subquery/window function with `LEFT JOIN live_sessions ls` to find the `relevant_session` (logic: live \> scheduled \> latest replay). Select `ls.id AS relevant_session_id`, `ls.status AS session_status`, `ls.start_time`, `ls.end_time`, `ls.featured_expert_id`.
          * `LEFT JOIN experts fe ON ls.featured_expert_id = fe.id` (主讲专家). Select `fe.id AS fe_id`, `fe.name AS fe_name`, `fe.title AS fe_title`, `fe.hospital AS fe_hospital`, `fe.user_id AS fe_user_id`.
          * `JOIN users su ON lr.user_id = su.public_id` (房间所有者/主播). Select `su.public_id AS su_user_id`, `su.nickname AS su_nickname`.
          * `LEFT JOIN experts se ON su.public_id = se.user_id` (所有者的专家信息). Select `se.id AS se_id`, `se.name AS se_name`, `se.title AS se_title`, `se.hospital AS se_hospital`.
          * `LEFT JOIN session_statistics ss ON relevant_session_id = ss.session_id`. Select relevant stats.
    4.  **构建 Host 对象**: 在 Service 层或数据映射层，根据上述查询结果，应用 Host 选择逻辑 (优先 fe \> se \> su) 填充 `HomepageHostInfo`。
    5.  **确定 `live_status`**: 根据 `session_status` 映射。
    6.  **计算 `heat`**: 使用 `ss` 数据和公式。
    7.  **构造 `status_data`**: 根据 `live_status` 填充相应字段 (viewer\_count, start\_time, duration). Duration might need calculation (`end_time - start_time`).
    8.  执行 `count()` 查询获取 `total` (基于筛选条件)。
    9.  应用 `sort`, `limit`, `offset` 到主查询。
    10. 执行主查询获取 `items` 数据。
    11. 映射到 `HomepageRoomItem` Schema。
    12. 记录 DEBUG 日志。
    13. 返回标准分页响应。
