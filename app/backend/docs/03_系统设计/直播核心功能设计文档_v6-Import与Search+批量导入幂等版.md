# LiveCore Service - Import 与 Search + 批量导入幂等设计文档 (V6 - 学院派 + 去重补丁融合版)

> 版本：6.0  
> 基线来源：  
> - 《直播核心功能设计文档 V5》  
> - 《直播核心功能设计文档 V5-Import 与 Search 增量功能》  
> - 《直播核心功能设计文档 V5_to_V6-去重补丁》  
> 本文目标：在**完全继承 V5 及 Import/Search 增量的全部语义**基础上，为 Import Session 与 Batch Import 增加  
> **room 去重 + session 去重（幂等导入）** 能力，并统一整理为一份可独立交付研发的 V6 设计文档。

---

## 0. 阅读指南与范围说明

- **本文是独立的 V6 增量设计文档**，聚焦 Import / Search / Batch Import 相关能力，包含：
  - V5-Import 文档中的：Import Session、Search、Batch Import 设计（学院派架构版）；  
  - V5_to_V6 去重补丁中的：`external_room_id` / `playback_url_hash` Schema 增量、幂等逻辑、测试与发布策略。
- **不再复述 V5 主文档的通用部分**（通用响应结构、全局架构、房间/场次基础 CRUD 等），但默认全部沿用：
  - 响应结构：`{code, message, data, timestamp}`；  
  - 错误码体系：`1xxx` 系统错误、`2xxx` 业务错误、`3xxx` 权限错误、`4xxx` 参数错误；  
  - “学院派”三层架构：API (Catch) → Service (Throw) → CRUD (Transaction)。
- **冲突消解原则**：
  - 若 V5-Import 与 V5_to_V6 在某处存在表述差异，以**去重补丁（V6）为最终口径**；  
  - 例如：V5-Import 曾声明“本增量不改动 DB Schema”，而 V6 去重补丁新增了字段与索引，则 **V6 以“有 DB 增量”为准**，并在自检清单中说明。

---

## 1. 开发规范（承袭 V5-Import）

本节完整承袭《V5-Import 与 Search 增量功能》中的开发规范与日志/异常规范，仅做简要摘录：

- **语言与规范**：
  - Python 3.8+，代码风格遵循 PEP 8；
  - 使用 Pydantic 定义请求/响应 Schema；
  - module / class / function / variable 命名沿用原文档规则（如 `SessionImportService`、`import_create_session`、`playback_url` 等）。
- **架构风格**：学院派 Academic
  - **CRUD 层**：执行原子 DB 操作；内部负责 `commit/rollback`；捕获 `IntegrityError` 并转为 `DatabaseIntegrityException` 等；提前提取日志变量；不做业务/权限校验。
  - **Service 层**：聚焦业务规则与权限校验；抛出自定义业务异常（`RoomNotFoundException`、`PermissionDeniedException`、`InvalidParameterException` 等）；不处理事务。
  - **API 层**：负责参数解析与异常捕获；在 `try...except` 中调用 Service；将异常映射为统一结构的 JSON 响应。
- **日志与异常处理规范**：完全复用 V5-Import 文档中 `2. 日志与异常处理规范` 各小节（日志级别/格式/内容、分层异常处理流程）。

> 说明：  
> V6 在幂等与去重层面仅**扩展业务逻辑与 DB Schema**，不改变已有的学院派三层实现模式和日志/异常规范。

---

## 2. 数据库 Schema 增量（V5-Import → V6 幂等版）

### 2.1 V5-Import 对 DB 的假设

V5-Import 文档中明确：  

- 依赖 V5 主文档中的核心表：
  - `live_rooms`：不含 `external_room_id`；  
  - `live_sessions`：已包含 `playback_url VARCHAR(1024) NULL`，但**没有**结构化去重字段。  
- 本身**不引入新的字段或索引**，Import / Search / Batch Import 均构建在 V5 Schema 之上。

### 2.2 V6 去重补丁的 DB 增量（本文件最终口径）

为实现 Import Session 与 Batch Import 的**幂等导入**，V6 在 V5 Schema 基础上新增两个字段 + 部分唯一索引：

```sql
-- 1) live_rooms 新增 external_room_id（外部直播间标识）
ALTER TABLE live_rooms
ADD COLUMN IF NOT EXISTS external_room_id VARCHAR(64) NULL;

-- 为同一 user 下的 external_room_id 建部分唯一索引（仅对非空值生效）
CREATE UNIQUE INDEX IF NOT EXISTS uq_live_rooms_user_external_room
ON live_rooms (user_id, external_room_id)
WHERE external_room_id IS NOT NULL;

COMMENT ON COLUMN live_rooms.external_room_id IS
'外部直播间ID（如第三方平台导出中的直播间ID），用于批量导入时按 (user_id, external_room_id) 维度复用房间';


-- 2) live_sessions 新增 playback_url_hash（回放地址幂等哈希）
ALTER TABLE live_sessions
ADD COLUMN IF NOT EXISTS playback_url_hash VARCHAR(128) NULL;

-- 为 (room_id, playback_url_hash) 建部分唯一索引（仅对非空hash生效）
CREATE UNIQUE INDEX IF NOT EXISTS uq_live_sessions_room_playback_hash
ON live_sessions (room_id, playback_url_hash)
WHERE playback_url_hash IS NOT NULL;

COMMENT ON COLUMN live_sessions.playback_url_hash IS
'playback_url 规范化后的哈希值，用于按 (room_id, playback_url) 维度实现幂等导入';
```

> 兼容性说明：  
> - 使用 `WHERE ... IS NOT NULL` 的部分唯一索引，对历史数据 0 侵入；  
> - V5-Import 文档中“DB 无变更”的说法在 V6 上被**修正为**：“Import / Batch Import 场景新增上述两个字段与索引”。  
> - 旧逻辑若不写入 `external_room_id` / `playback_url_hash`，行为与 V5 完全一致。

### 2.3 ORM 模型增量（说明性）

在 `app/models/live_core.py` 中，对应字段与索引应补充为（与去重补丁保持一致）：

```python
class LiveRoom(Base):
    __tablename__ = "live_rooms"
    ...
    external_room_id = Column(String(64), nullable=True, comment="外部直播间ID（如第三方平台直播间ID）")
    __table_args__ = (
        Index("idx_live_rooms_user_id", "user_id"),
        Index(
            "uq_live_rooms_user_external_room",
            "user_id",
            "external_room_id",
            unique=True,
            postgresql_where=text("external_room_id IS NOT NULL"),
        ),
    )


class LiveSession(Base):
    __tablename__ = "live_sessions"
    ...
    playback_url = Column(String(1024), nullable=True)
    playback_url_hash = Column(String(128), nullable=True, comment="playback_url 规范化后的哈希值")
    __table_args__ = (
        Index(
            "uq_live_sessions_room_playback_hash",
            "room_id",
            "playback_url_hash",
            unique=True,
            postgresql_where=text("playback_url_hash IS NOT NULL"),
        ),
    )
```

---

## 3. 回放 URL 规范化与哈希规则

V5-Import 文档中，Import Session 与 Batch Import 只要求 `playback_url` 为合法 URL，并写入 `live_sessions.playback_url` 字段；  
V6 在此基础上，为幂等判断增加统一的规范化与哈希规则。

### 3.1 规范化规则

- 采用最小规范化策略：
  - `normalized_url = playback_url.strip()`  
  - 不改变协议（`http/https`）、主机名、路径和查询参数；  
  - 未来若需剔除某些 tracking query 参数，需补充文档，并保证对历史数据兼容。

### 3.2 哈希算法

- 使用 `SHA-256` 对规范化后的 URL 做哈希：

```python
def normalize_playback_url(url: str) -> str:
    return url.strip()

def calc_playback_url_hash(url: str) -> str:
    """
    统一的 playback_url 哈希计算函数。
    内部会先调用 normalize_playback_url，避免调用方忘记先规范化。
    """
    from hashlib import sha256
    normalized = normalize_playback_url(url)
    return sha256(normalized.encode("utf-8")).hexdigest()
```

- 存储为 64 字节十六进制字符串；`VARCHAR(128)` 可以完整存储 SHA-256 十六进制字符串（实际长度为 64）。

### 3.3 维护时机（全局硬约束）

在原 V5-Import 设计中，以下路径会写入或更新 `playback_url`：

- Import Session：`POST /api/v1/rooms/{room_id}/sessions/import`；  
- Batch Import：`POST /api/v1/rooms/import/batch`；  
- 会话更新：`PATCH /api/v1/sessions/{session_id}`（在 READY/FINISHED 状态手动修改 `playback_url`）；  
- 后台任务自动写回回放地址：`SessionService.auto_generate_playback_url`。

V6 约束：  

- **所有会修改 `playback_url` 的 Service 方法**（包括但不限于上述四类），在更新 `playback_url` 时，必须同步执行：

```python
playback_url_hash = calc_playback_url_hash(new_url)
```

并写入 `live_sessions.playback_url_hash` 字段。

> 换言之：**凡是更新 `playback_url` 的 Service 方法，都必须同步维护 `playback_url_hash`**，  
> 任何只改 URL 而不更新 hash 的实现视为不符合本 V6 设计。

---

## 4. Import Session API（导入会话 + 幂等扩展）

### 4.1 V5-Import 语义（回顾）

- **Endpoint**：`POST /api/v1/rooms/{room_id}/sessions/import`  
- 功能：为已有回放地址的外部会话创建记录，允许创建时直接写入 `playback_url` 和终态状态（`finished` / `ready`）。  
- 认证与权限：
  - 需要 JWT；  
  - 仅房间所有者可导入：`room.user_id == current_user.public_id`。  
- 关键约束：
  - `playback_url` 必填，长度 ≤ 1024，`http://` / `https://`；  
  - `status ∈ {'finished', 'ready'}`。

### 4.2 V6 幂等语义扩展（按 playback_url 去重）

在保持 V5-Import 的接口签名与返回结构不变的前提下，V6 增加**会话级幂等**语义：

- 对同一 `room_id`，若多次导入的 `playback_url`（经规范化后）相同，则**只创建一条物理会话记录**；
- 幂等查重维度：`(room_id, playback_url_hash)`。

#### 4.2.1 Service 层逻辑（SessionImportService）

综合 V5-Import 与 V5_to_V6 去重补丁，`SessionImportService.import_create_session` 的关键逻辑为：

```python
class SessionImportService:
    async def import_create_session(
        self,
        room_id: UUID,
        public_id: UUID,
        session_in: dict,
    ) -> Tuple[LiveSession, bool]:
        # 1. 房间存在性 + 权限检查（保持 V5 行为）
        room = await crud_room.get(self.db, room_id=room_id)
        ...

        status = session_in["status"]
        playback_url = session_in["playback_url"]

        # 统一使用 calc_playback_url_hash：内部负责 normalize + hash
        playback_hash = calc_playback_url_hash(playback_url)
        # 如需存储规范化后的 URL，可单独调用 normalize_playback_url
        normalized = normalize_playback_url(playback_url)

        # 2. 幂等查询：按 (room_id, playback_url_hash)
        existing = await crud_session.get_by_room_and_playback_hash(
            db=self.db,
            room_id=room_id,
            playback_url_hash=playback_hash,
        )
        if existing:
            return existing, True  # True 表示幂等命中

        # 3. 创建会话（包含 playback_url_hash）
        session_data = {
            "id": uuid.uuid4(),
            "room_id": room_id,
            "status": status,
            "start_time": session_in.get("start_time"),
            "end_time": session_in.get("end_time"),
            "playback_url": normalized,
            "playback_url_hash": playback_hash,
        }
        db_session = await crud_session.create(self.db, obj_in=session_data)
        return db_session, False
```

#### 4.2.2 API 层可选扩展字段

在 V5-Import 文档基础上，V6 建议在成功响应中**可选**增加 `idempotent_hit` 字段，用于标识幂等命中：

```python
session, idempotent_hit = await service.import_create_session(...)

response_data = {
    "id": str(session.id),
    "room_id": str(session.room_id),
    "status": ...,
    "start_time": ...,
    "end_time": ...,
    "playback_url": session.playback_url,
    "created_at": ...,
    "updated_at": ...,
    "idempotent_hit": idempotent_hit,  # V6 新增，可选字段
}
```

- 兼容性：
  - 旧前端忽略 `idempotent_hit` 即可；  
  - 新前端可根据此字段给出“本会话已存在，无需重复导入”的 UI 提示。

---

## 5. Search API（与去重逻辑无直接冲突）

本节基本沿用 V5-Import 文档中的设计：

- **Endpoint**：`GET /api/v1/rooms`  
- 功能：获取房间列表，支持通过可选 Query 参数 `q` 按 `room_id`（UUID 精确匹配）或 `title`（模糊匹配）搜索。  
- 认证：**Optional Auth**（可选鉴权，支持匿名访问）；  
- 权限：复用列表接口的 `is_private` 过滤逻辑（Admin 可搜索所有、Regular 可搜索 public + 自己创建的、匿名只能搜索 public）。

V6 去重能力**不改变 Search 的语义与实现**，仅要求：

- 在需要按外部 ID 搜索时，前端应显式区分：
  - 基于内部 `id` 的搜索（仍走当前 Search）；  
  - 基于外部 `external_room_id` 的搜索（如需，可在未来版本扩展 Search 参数或新增 API，本次 V6 不做）。

---

## 6. Batch Import API（批量导入 + 幂等扩展）

### 6.1 V5-Import 中 Batch Import 的基础设计（回顾）

V5-Import 文档定义了：

- **Endpoint**：`POST /api/v1/rooms/import/batch`  
- **Content-Type**：`multipart/form-data`，上传 `file`（CSV/Excel）；  
- Query 参数：
  - `mode=dry_run|apply`（默认 `dry_run`）：只校验 / 实际写库；  
  - `encoding_hint=utf-8-sig|utf-8|gbk`：可选编码提示。  
- 文件字段契约：
  - 逻辑必需列：`room_title`、`playback_url`；  
  - 可选列：`room_id`、`session_id`、`room_description`、`session_title`、`start_time`、`end_time`、`status`、`cover_url` 等；  
  - 对常见中文表头（如 `标题`、`播放url` / `播放url1`、`封面图片`）做表头映射。
- 导入报告结构：

```json
{
  "total_rows": 10,
  "success_count": 8,
  "failed_count": 2,
  "items": [
    {
      "row_no": 1,
      "room_id": "room_uuid_1",
      "session_id": "session_uuid_1",
      "status": "success",
      "error": null
    },
    {
      "row_no": 2,
      "room_id": null,
      "session_id": null,
      "status": "failed",
      "error": "playback_url 格式错误"
    }
  ]
}
```

### 6.2 V6 新增：external_room_id 表头映射

为实现 `(user_id, external_room_id)` 维度的房间级幂等复用，V6 在 Batch Import 的表头解析逻辑（如 `_apply_header_aliases`）中新增：

- 逻辑字段 `external_room_id` 的候选表头包括（不区分大小写，去除首尾空格后匹配）：
  - `"external_room_id"`
  - `"直播间id"`
  - `"直播间ID"`

> 规则：  
> - 若 CSV/Excel 表头为上述任一值，解析后的行数据中应统一映射为 `row["external_room_id"]`；  
> - 后续房间幂等逻辑（`_get_or_create_room_for_row`）可以直接使用该字段进行 `(user_id, external_room_id)` 维度复用。

### 6.3 Room 幂等：按 (user_id, external_room_id) get-or-create

在 V5-Import 的“房间创建或复用”逻辑基础上，V6 将 Batch Import 的房间处理升级为：

```python
async def _get_or_create_room_for_row(self, public_id: UUID, row: Dict) -> LiveRoom:
    room_id_str = row.get("room_id")
    external_room_id = row.get("external_room_id")

    # a) 有 room_id：按 V5 行为复用
    if room_id_str:
        room_id = UUID(room_id_str)
        room = await crud_room.get(self.db, room_id=room_id, user_id=public_id)
        if not room:
            raise InvalidParameterException("房间不存在或无权限")
        return room

    # b) 有 external_room_id：按 (user_id, external_room_id) 幂等
    if external_room_id:
        room = await crud_room.get_by_external_id(
            db=self.db,
            user_id=public_id,
            external_room_id=external_room_id,
        )
        if room:
            return room

    # c) 否则创建新房间
    room_data = {...}
    room = await crud_room.create(self.db, obj_in=room_data, user_id=public_id)
    if external_room_id:
        room.external_room_id = external_room_id
        await self.db.commit()
        await self.db.refresh(room)
    return room
```

### 6.4 Session 幂等：通过 SessionImportService 统一调度

V5-Import 中，Batch Import 直接构造 `session_data` 调用 `crud_session.create`；  
V6 将其改造为**统一走 Import Session 的 Service 层逻辑 + 哈希幂等**：

```python
async def _process_row(...):
    ...
    room = await self._get_or_create_room_for_row(public_id, row)

    if mode == "apply":
        session_in = {
            "status": row.get("status", "finished"),
            "start_time": parsed_start_time,
            "end_time": parsed_end_time,
            "playback_url": row["playback_url"],
            # 可选：title / description 等
        }
        session, idempotent_hit = await SessionImportService(self.db).import_create_session(
            room_id=room.id,
            public_id=public_id,
            session_in=session_in,
        )
        return {
            "row_no": row_no,
            "room_id": str(room.id),
            "session_id": str(session.id),
            "status": "success",
            "error": None,
            "skipped": idempotent_hit,
            "skip_reason": "duplicate_session_by_playback_url" if idempotent_hit else None,
        }
    else:
        # dry_run：仅做字段校验，不写库
        ...
```

### 6.5 导入报告幂等结果表达（扩展）

在 V5-Import 的导入报告结构基础上，V6 追加行级字段：

```json
{
  "row_no": 1,
  "room_id": "room_uuid",
  "session_id": "session_uuid",
  "status": "success",
  "error": null,
  "skipped": true,
  "skip_reason": "duplicate_session_by_playback_url"
}
```

- `skipped: bool`：
  - `true`：表示命中既有 `(room, session)`，未产生新的 DB 写入；  
  - `false` 或缺省：表示创建了新会话。  
- `skip_reason: string | null`：
  - 例如 `"duplicate_session_by_playback_url"` / `"duplicate_room_and_session"`，用于排查幂等命中原因。

顶层可选字段：

- `skipped_count: int`：统计 `items[*].skipped == true` 的行数。

> 兼容性：  
> - `status` / `success_count` / `failed_count` 的含义保持不变；  
> - 旧前端若不关心幂等，可以忽略 `skipped` / `skip_reason` / `skipped_count`。

---

## 7. CRUD 扩展（去重相关）

在 V5-Import 的 CRUD 设计基础上，V6 新增以下方法以支撑幂等逻辑：

### 7.1 Room CRUD：按 external_room_id 查找房间

```python
async def get_by_external_id(
    db: AsyncSession,
    user_id: uuid.UUID,
    external_room_id: str,
) -> Optional[LiveRoom]:
    query = (
        select(LiveRoom)
        .where(
            LiveRoom.user_id == user_id,
            LiveRoom.external_room_id == external_room_id,
        )
    )
    result = await db.execute(query)
    return result.scalar_one_or_none()
```

### 7.2 Session CRUD：按 (room_id, playback_url_hash) 查找会话

```python
async def get_by_room_and_playback_hash(
    db: AsyncSession,
    room_id: uuid.UUID,
    playback_url_hash: str,
) -> Optional[LiveSession]:
    query = select(LiveSession).where(
        LiveSession.room_id == room_id,
        LiveSession.playback_url_hash == playback_url_hash,
    )
    result = await db.execute(query)
    return result.scalar_one_or_none()
```

其余 CRUD 设计（如 `crud_session.create`、`crud_room.list_with_search` 等）沿用 V5-Import 文档的学院派实现方式。

---

## 8. 关键流程差异（Before / After）

综合 V5-Import 与 V6 去重补丁，关键流程差异如下：

### 8.1 房间创建（Batch Import）

- **V5-Import Before**：
  1. 若行有 `room_id`：按 `room_id` + 权限校验复用房间；  
  2. 否则：每行创建一个全新的 `LiveRoom`。

- **V6 After**：
  1. 若行有 `room_id`：行为与 V5-Import 一致；  
  2. 否则若有 `external_room_id`：按 `(user_id, external_room_id)` 幂等复用房间；  
  3. 否则：每行创建一个新房间。

### 8.2 会话创建（Import / Batch Import）

- **V5-Import Before**：
  - Import Session / Batch Import 直接创建新的 `LiveSession` + `SessionStatistics`，不查重；  
  - 同一 `room_id` 下可以存在多条 `playback_url` 完全相同的记录。

- **V6 After**：
  1. 对 `playback_url` 做规范化与哈希计算得到 `playback_url_hash`；  
  2. 按 `(room_id, playback_url_hash)` 查询是否已有记录：  
     - 若存在 → 返回已有记录，视为幂等命中；  
     - 若不存在 → 创建新记录并写入 hash。

---

## 9. 测试策略（在 V5-Import 基础上的增量）

V5-Import 已经为 Import / Search / Batch Import 设计了一整套测试用例（单测 + 集成 + 性能）；  
V6 需在此基础上增加如下关键用例（与 V5_to_V6 去重补丁一致）：

1. **同一 CSV 重复上传幂等性**
   - 第一次 `mode=apply` 导入 N 行：  
     - 断言成功创建 N 个 room + N 个 session；  
   - 第二次导入同一文件：  
     - `success_count == N`、`failed_count == 0`；  
     - `items[*].skipped == true`；  
     - 数据库中 room / session 数量**不增加**。

2. **不同 CSV 含相同行幂等性**
   - 构造两个文件，包含相同的“外部直播间 ID + playback_url” 行；  
   - 依次导入后，断言：  
     - `(user_id, external_room_id)` 唯一，只有一个 room；  
     - `(room_id, playback_url_hash)` 唯一，只有一个对应 session。

3. **Import Session 单接口幂等性**
   - 对同一 `room_id` 和相同 payload 连续调用 Import Session 接口两次；  
   - 断言：第二次调用返回的 `id` 与第一次相同；  
   - 若实现了 `idempotent_hit` 字段，则断言 `data.idempotent_hit == true`。

4. **并发导入与唯一约束兜底**
   - 使用并发请求模拟多次同时导入相同 `room_id + playback_url`；  
   - 断言最终数据库中只存在一条对应的会话记录；  
   - 若出现 DB 唯一约束错误，CRUD 层需将其转换为业务层“数据冲突”异常并记录日志。

其余 Import / Search / Batch Import 测试用例，沿用 V5-Import 文档中 `13. 测试策略` 各小节。

---

## 10. 发布步骤与回滚策略

### 10.1 发布步骤

1. **执行数据库迁移（只加字段和索引）**
   - 执行本设计 `2.2` 节中的 DDL 脚本；  
   - 确保所有实例 schema 与应用代码期望一致。

2. **上线应用层代码**
   - 部署包含新字段支持、CRUD 扩展、Service 幂等等改动的版本；  
   - 保证 Import / Batch Import / 回放更新路径均正确维护 `external_room_id` 与 `playback_url_hash`。

3. **灰度验证**
   - 在灰度环境中运行重复导入与幂等相关用例，确认不再产生重复房间/场次；  
   - 监控数据库唯一索引冲突日志，确保异常被正确捕获与转换。

### 10.2 回滚策略

- 若仅需回滚应用逻辑（DB 迁移保留）：
  - 退回到 V5 或 V5-Import 逻辑版本；  
  - 确保回滚后的代码不再依赖 `external_room_id` 与 `playback_url_hash` 字段即可。

- 若必须连同 DB 一并回滚：
  1. 确保停机或无新写入流量；  
  2. 删除两个新增索引与字段：

     ```sql
     DROP INDEX IF EXISTS uq_live_rooms_user_external_room;
     ALTER TABLE live_rooms DROP COLUMN IF EXISTS external_room_id;

     DROP INDEX IF EXISTS uq_live_sessions_room_playback_hash;
     ALTER TABLE live_sessions DROP COLUMN IF EXISTS playback_url_hash;
     ```

  3. 回滚应用代码到 V5 / V5-Import 版本。

---

## 11. Self-check 自检清单（V6 Import + Search + 幂等）

- **V5-Import 内容是否被删除或弱化？**  
  - 否。本文仅在 Import / Batch Import 流程上增加去重/幂等逻辑与 DB 增量；  
  - 原有 Import / Search / Batch Import 的接口语义、返回结构与错误码体系保持不变。

- **是否覆盖两类重复导入场景？**  
  - 同一 CSV 重复上传：通过 `(user_id, external_room_id)` + `(room_id, playback_url_hash)` 去重；  
  - 不同 CSV 含相同行：只要外部直播间 ID 与 `playback_url` 一致，也会通过相同机制去重。

- **DDL/索引是否与字段类型一致？**  
  - `external_room_id` 使用 `VARCHAR(64)`；  
  - `playback_url_hash` 使用 `VARCHAR(128)`，可以完整存储 SHA-256 十六进制字符串（实际长度为 64）。

- **旧路由/旧语义是否保持不变？**  
  - 是。未对任何已有 API 做删除/重命名/参数语义变更；  
  - 新增的幂等语义通过内部逻辑 + 可选返回字段（如 `idempotent_hit`、`skipped`）表达。

- **并发/重复请求是否有 DB 级兜底？**  
  - 是。通过新增的部分唯一索引保证最终只保留一条物理记录；  
  - CRUD 层负责将唯一约束异常转换为可预期的业务异常。

- **所有修改 `playback_url` 的路径是否同步维护 hash？**  
  - 设计层面已经明确列出并加以约束（Import Session / Batch Import / PATCH / auto_generate）；  
  - 实现层须在代码审查中逐一检查对应 Service 方法是否调用 `calc_playback_url_hash(new_url)` 并更新字段。

---

> 注：  
> - V5-Import 与 V5_to_V6 去重补丁中的所有关键内容（Schema 增量、API 行为、Service & CRUD 伪代码、测试与发布策略）均已在本 V6 文档中有机融合；  
> - 两份原文档仍保留在仓库中，可作为补充阅读与历史参考。  
> - 若后续需要将本 V6 文档进一步并入 V5 主文档，可直接作为“Import & Search & 去重幂等增量章节”整体迁移。


