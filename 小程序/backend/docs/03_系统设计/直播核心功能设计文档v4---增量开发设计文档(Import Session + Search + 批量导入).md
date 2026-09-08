````md
# LiveCore Service - 增量开发设计文档（Import Session + Search + 批量导入）  
- **基线版本**：以《直播核心功能设计文档v4.md（V4.1 - 响应修复版）》为准  
- **增量目标**：在 **最小改动** 前提下，引入：
  1) **Import 创建 session**（可直接携带 `playback_url`）  
  2) **搜索功能**（按直播间 id 或 title 模糊查找，UI 类似你截图）  
  3) **CSV/Excel 批量导入**（批量创建 room + session，并写入 `playback_url`）  
- **核心约束（必须满足）**：
  - 尽量不改动已有代码；若必须改动，控制在最小范围（新增 router/service/CRUD，避免改已有路径和行为）
  - **不影响已有路由调用**：不改动现有 Endpoint 的 path/method/返回结构；只允许新增 Endpoint 或为列表接口新增**可选** Query 参数
  - 尽量不修改已有测试函数和配置：新增测试文件/新增用例即可；不改旧用例断言（除非 v4 已要求修复的 PATCH 响应字段一致性）

---

## 1. 背景与问题定义（增量动机）

v4 已将 `playback_url` 作为 `live_sessions` 的持久化字段（`VARCHAR(1024) NULL`），并规定：
- **普通创建 session**：`playback_url` 默认应为 `NULL`  
- **后台任务**：在特定状态（如 ready 且 video_id 非空等）可以生成默认回放地址，但不得覆盖手动设置  
- **PATCH session**：在 ready/finished 状态允许修改 playback_url，且响应必须返回更新后的 playback_url（与 GET 一致）

当前你的痛点是：
- “从外部拷贝来的 live session”在创建时就已经有 `playback_url`，但你不得不先创建→改 finished→再 PATCH playback_url，操作繁琐且容易误用。
- 需要一个“导入/导出/检索”友好的增量能力：支持单个导入与批量导入；支持按 id/title 模糊搜索并快速定位。

> 结论：引入 **Import 类型创建** 是最小侵入且最符合原则的方案：不改变普通创建语义，仅新增一条导入路径专门处理“已存在回放”的 session。

---

## 2. 设计原则（与 v4 保持一致 + 强化增量最小修改）

### 2.1 与 v4 一致的规范（不再重复，仅强调一致性）
- **统一响应结构**：`{code, message, data, timestamp}`（v4 的通用响应规范）  
- **分层架构**：Router → Service → CRUD（CRUD 不做权限校验；权限/业务校验在 Service）  
- **日志/异常**：遵循 v4 的日志格式字段与异常分类（系统/业务/参数/权限）  
- **数据库访问**：保持既有 ORM/Session 管理方式，不引入与现有冲突的 DB 访问层

### 2.2 增量与最小修改原则（本增量的硬约束）
1) **旧路由不改**：现有 `POST /api/v1/rooms/{room_id}/sessions` 仍保持“普通创建”语义（playback_url 必须为 NULL）。  
2) **新增而非修改**：导入能力通过 **新增 Endpoint + 新 DTO** 实现；避免在旧 DTO 上加必填字段导致兼容性风险。  
3) **测试不破坏**：旧测试用例不改断言；新增测试覆盖导入/search/batch 导入。  
4) **可扩展与通用**：导入能力未来可支持更多字段（例如外部 source、external_id），但当前先最小落地：只解决 `playback_url`。

---

## 3. 数据库与模型影响（最小化）

### 3.1 是否需要修改数据库？
- 若你已经按 v4 在 `live_sessions` 表中加入了 `playback_url VARCHAR(1024) NULL`：**本增量不需要任何数据库变更**。  
- Import 只是“创建时允许写入 playback_url”，不要求新字段。

> ✅ 结论：本增量在 DB 层面维持 “0 变更” 的最小方案。

### 3.2（可选）为将来扩展预留，但本期不做
如将来需要追踪导入来源，可考虑新增：
- `live_sessions.source_type`（enum: native/import）
- `live_sessions.external_ref`（外部系统的唯一标识）
本增量 **不引入**，避免迁移与旧逻辑耦合。

---

## 4. API 设计（新增，不影响旧路由）

> 以下新增 API 均遵循 v4 的统一响应结构与分页约定。

### 4.1 Import 创建 Session（新增 Endpoint）

#### 4.1.1 新增：导入创建 session
- **Endpoint**：`POST /api/v1/rooms/{room_id}/sessions/import`
- **功能描述**：为“已存在回放的 session（从外部拷贝）”创建场次，并允许 **在创建时直接写入 playback_url**。
- **设计动机**：不污染普通创建语义；避免你现在“先改 finished 再 PATCH”的繁琐流程。
- **请求体（示例）**：
```json
{
  "start_time": "2025-07-07T18:00:00Z",
  "end_time": "2025-07-07T19:00:00Z",
  "status": "finished",
  "playback_url": "https://mp2.dayilive.com/mp_clip/xxxx.m3u8"
}
````

* **参数校验**：

  * `playback_url` 必填（Import 的意义就是携带回放）
  * `status` 限制为：`finished` 或 `ready`（建议最小集合；避免导入 live 状态）
  * `start_time` 必填；`end_time` 建议必填（导入历史回放时通常明确）
  * `playback_url` 仅校验格式（URL 长度 <= 1024），不做可播放性探测（避免引入外部依赖）

* **成功响应（200 OK）**：返回 session 详情，包含 playback_url（与 `GET /api/v1/sessions/{id}` 一致字段集合）

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": "session_uuid",
    "room_id": "room_uuid",
    "status": "finished",
    "start_time": "...",
    "end_time": "...",
    "video_id": null,
    "playback_url": "https://..."
  },
  "timestamp": "..."
}
```

* **失败响应（示例）**：

  * 参数校验失败：`4xxx`
  * room 不存在：`404`（HTTP） + `code=2004/4004`（按你现有规范映射）
  * 无权限：`401/403`（HTTP）+ `3xxx`

> **兼容性保证**：旧的 `POST /api/v1/rooms/{room_id}/sessions` 不变；前端只需在“普通创建/导入创建”上做分支选择。

---

### 4.2 Search（模糊查询：按 room id / title）

你希望类似截图：支持按 **直播间 id 或 title** 搜索，并分页展示列表。

#### 4.2.1 最小侵入方案（推荐）：扩展现有 list rooms 的 Query 参数（可选）

* **Endpoint**：仍使用 `GET /api/v1/rooms`
* **新增可选 Query 参数**：

  * `q`：字符串，模糊匹配（id 精确匹配 + title ILIKE）
  * 或拆分为：

    * `room_id`（精确）
    * `title_like`（模糊）
* **兼容性**：旧调用不传参数，行为完全一致。
* **分页返回**：保持 v4 的 `{total,page,size,items}` 格式。

**实现要点（Service/CRUD）**：

* 若 `q` 看起来像 UUID：优先按 `id == q` 或 `id::text ILIKE`（按你 DB 类型）
* 同时支持 `title ILIKE %q%`
* 返回 items 时字段保持现有 rooms list 输出字段集合

#### 4.2.2（可选）新增专用 search 路由（如果你强烈希望路由更清晰）

* `GET /api/v1/rooms/search?q=...`
* 仍然不改旧路由，但会新增一个新入口
* 缺点：前端与文档多一条路由；优点：语义更清晰

> 如果你的“路由稳定性”要求极高，优先用 4.2.1（仅可选参数）即可。

---

### 4.3 批量导入（CSV/Excel：创建 room + session 并写入 playback_url）

#### 4.3.1 新增：批量导入接口

* **Endpoint**：`POST /api/v1/rooms/import/batch`
* **Content-Type**：`multipart/form-data`
* **上传文件**：`file`（.csv 或 .xlsx）
* **模式**：支持 dry-run（只校验不写入）与 apply（落库）

**请求 Query 参数（可选）**：

* `mode=dry_run|apply`（默认 dry_run，符合“安全与可回溯”）
* `encoding_hint=utf-8-sig|utf-8|gbk`（可选；默认自动探测：utf-8-sig → utf-8 → gbk，与你现有 CSV 容错逻辑一致）

#### 4.3.2 文件字段契约（最小集合）

你的文件包含：直播间 id、title、playback_url 等关键信息。为保证通用性，定义最小必需列：

* **必需列**：

  * `room_title`（直播间标题）
  * `session_title`（可选，如没有则复用 room_title 或置空；看你现有 session 是否有 title 字段）
  * `playback_url`（回放地址）
* **可选列**：

  * `room_id`（若外部指定。若不提供则系统生成 UUID）
  * `session_id`（同上）
  * `start_time`, `end_time`, `status`（若不提供，按导入默认策略）

> 注意：你 v4 的 DDL 里 `live_rooms.title` 必填、`stream_key` 必填且唯一。批量导入创建 room 时，需要一个**可预测且不冲突**的 stream_key 生成策略（例如 UUID 派生或随机），但这属于现有创建 room 的内部策略，不应破坏现有逻辑。

#### 4.3.3 导入业务流程（Service 层）

对每一行：

1. 标准化文本（trim、把多余空白折叠为单空格；不改变中英文内容）
2. 创建或复用 room：

   * 若提供 `room_id` 且存在：复用（权限校验必须做）
   * 否则创建新 room（使用你现有创建逻辑生成 stream_key）
3. 创建 session（Import 语义）：

   * 直接走 **Service 的 import_create_session** 内部方法（不要复制逻辑）
   * playback_url 写入 live_sessions.playback_url
   * status 默认 `finished`（导入历史回放最常见），也允许文件内覆盖为 ready/finished
4. 记录每行结果：success / fail + reason（用于导入报告）

#### 4.3.4 响应（200 OK）

* `data` 中返回：

  * `total_rows`
  * `success_count`
  * `failed_count`
  * `items`（每行导入结果：row_no、room_id、session_id、status、error）
* 若 mode=dry_run：不写 DB，只返回校验结果
* 若 mode=apply：写 DB，并返回落库结果

---

## 5. 编码与实现计划（严格增量，尽量不动已有代码）

### 5.1 推荐的最小代码改动方式

#### 5.1.1 新增 Router（不改旧 Router）

* 新增：`routers/sessions_import.py`

  * 注册：`POST /api/v1/rooms/{room_id}/sessions/import`
* 新增：`routers/import_batch.py`

  * 注册：`POST /api/v1/import/sessions`
* Search：

  * 方案 A（推荐）：只在 `GET /api/v1/rooms` 增加可选参数解析（不改返回结构、不改路径）
  * 方案 B：新增 `GET /api/v1/rooms/search` 路由（不动旧的 /rooms）

#### 5.1.2 新增 Service 方法（复用已有 CRUD）

* `SessionService.import_create_session(room_id, payload, user_id)`

  * 内部复用 session 创建逻辑，但允许 playback_url 非空
  * 额外校验 status 合法
* `RoomService.search_rooms(q/title_like/room_id, pagination, user_id optional)`

  * 仅扩展查询，不改变既有查询默认行为

#### 5.1.3 CRUD 层扩展（只加不改）

* 新增一个 `crud_room.search(...)`（或在现有 list 里加可选条件，不改变默认）
* 新增 `crud_session.create_import(...)`（或复用 create 但由 Service 控制字段）

---

## 6. 测试策略（尽量不改旧测试）

### 6.1 测试改动原则

* 不修改旧测试文件/旧 fixture（除非它们本来就不符合 v4 的 PATCH 响应一致性要求）
* 仅新增：

  * `test_sessions_import.py`
  * `test_rooms_search.py`
  * `test_import_batch.py`

### 6.2 必测用例（新增）

1. Import 创建 session：

   * 成功：创建时携带 playback_url，可直接保存，不需要先 finished 再 PATCH
   * 失败：status 不在 finished/ready
   * 失败：playback_url 缺失/过长
2. Search：

   * q 命中 title 模糊匹配
   * q 为 UUID 时命中 id
   * 不传 q 时行为与旧用例一致（回归）
3. 批量导入：

   * dry_run：不落库，仅返回校验报告
   * apply：成功落库并返回 room_id/session_id
   * CSV 编码容错：utf-8-sig/utf-8/gbk 的读取路径覆盖（至少模拟其中两种）
   * 行级失败隔离：某行失败不影响其他行

---

## 7. 你提到的“操作繁琐”的直接解决方案（最小改动达成）

你现在必须“先把 status 改 finished 保存，再更新 playback_url 才能更新”的原因，本质是：

* 你把“允许修改 playback_url”的规则写在了 `PATCH` 的业务约束里（只允许 ready/finished），而创建时走的是“普通创建”语义（playback_url 必须 NULL）。

引入 **Import 创建 session** 后：

* 外部拷贝来的 session 直接走 `POST /rooms/{room_id}/sessions/import`，请求体里包含 status=finished 与 playback_url
* 你不需要执行额外的 PATCH，流程减少为一步
* 普通创建仍保持 playback_url=NULL 的规则不变（与 v4 一致）

---

## 8. 与 v4 一致性自检清单（确保无冲突）

* [x] `live_sessions.playback_url` 为持久化字段（v4 已定义），本增量不改 DB
* [x] 普通创建 session playback_url 默认 NULL（不改变旧行为）
* [x] 新增 import 创建入口，允许创建时写入 playback_url（新增，不冲突）
* [x] GET session 响应包含 playback_url（v4 已要求）
* [x] PATCH session 允许更新 playback_url（ready/finished），响应包含该字段（v4 已要求；本增量不改）
* [x] Search 采用新增可选 Query 或新增 search 路由，不破坏已有调用
* [x] 批量导入采用新增 endpoint，不影响已有 endpoints
* [x] 测试仅新增，不修改旧测试配置/旧路由测试

---

## 9. 交付清单（增量开发的最小落地）

1. 新增路由：

   * `POST /api/v1/rooms/{room_id}/sessions/import`
   * `POST /api/v1/rooms/import/batch`
   * （二选一）Search：`GET /api/v1/rooms` 增加 `q/title_like/room_id` 可选参数，或新增 `GET /api/v1/rooms/search`
2. 新增 Service：

   * `SessionService.import_create_session`
   * `ImportService.batch_import_sessions`
   * `RoomService.search_rooms`（或 rooms list 扩展）
3. 新增 CRUD 查询方法（不改默认）
4. 新增测试文件与用例（不改旧测试）
5. 更新文档章节（本文件），并在 v4 “API 接口规范”里以增量方式补充上述 3 个小节

---


