# 增量设计文档：直播核心功能 V5 → V6 批量导入去重补丁

> 目标：在**不改变 V5 任何现有接口语义**的前提下，为 Import Session 与 Batch Import 能力增加  
> **room 去重 + session 去重（幂等导入）**，解决重复 CSV/Excel 上传与跨文件重复行导致的重复数据问题。

---

## 1. 基线与范围

- **基线文档**：
  - 《直播核心功能设计文档 V5》  
  - 《直播核心功能设计文档 V5 - Import 与 Search 增量功能》  
- **本补丁范围**：  
  - 仅影响：
    - Import Session 路径：`POST /api/v1/rooms/{room_id}/sessions/import`；  
    - Batch Import 路径：`POST /api/v1/rooms/import/batch`；  
    - 与 `playback_url` / `playback_url_hash` / `external_room_id` 相关的 DB / ORM / CRUD / Service；  
  - 不影响：
    - 普通房间创建与管理接口；  
    - 普通会话创建/更新/删除接口；  
    - Search 与其他业务模块。

---

## 2. 变更清单（按模块）

### 2.1 数据库与 ORM

**2.1.1 live_rooms：新增 external_room_id**

- 字段：

  ```sql
  ALTER TABLE live_rooms
  ADD COLUMN IF NOT EXISTS external_room_id VARCHAR(64) NULL;
  ```

- 唯一约束（部分唯一索引）：

  ```sql
  CREATE UNIQUE INDEX IF NOT EXISTS uq_live_rooms_user_external_room
  ON live_rooms (user_id, external_room_id)
  WHERE external_room_id IS NOT NULL;
  ```

- 语义：
  - 存储外部系统的直播间 ID（如微赞导出文件中的“直播间ID”）；  
  - 用于在批量导入时按 `(user_id, external_room_id)` 维度复用房间，避免为同一外部直播间创建多个 `live_rooms`。

**2.1.2 live_sessions：新增 playback_url_hash**

- 字段：

  ```sql
  ALTER TABLE live_sessions
  ADD COLUMN IF NOT EXISTS playback_url_hash VARCHAR(128) NULL;
  ```

- 唯一约束（部分唯一索引）：

  ```sql
  CREATE UNIQUE INDEX IF NOT EXISTS uq_live_sessions_room_playback_hash
  ON live_sessions (room_id, playback_url_hash)
  WHERE playback_url_hash IS NOT NULL;
  ```

- 语义：
  - 存储对 `playback_url` 规范化后计算的哈希值（推荐使用 SHA-256 十六进制字符串）；  
  - 用于 Import / Batch Import 场景下按 `(room_id, playback_url)` 维度实现幂等。

**2.1.3 ORM 模型增量**

- `LiveRoom` 增加：

  ```python
  external_room_id = Column(String(64), nullable=True, comment="外部直播间ID（如第三方平台直播间ID）")
  ```

- `LiveSession` 增加：

  ```python
  playback_url_hash = Column(String(128), nullable=True, comment="playback_url 规范化后的哈希值")
  ```

> 注意：索引可通过 SQLAlchemy 的 `Index` 声明或 Alembic 迁移脚本实现，语义必须与上文 DDL 一致。

---

### 2.2 CRUD 层

**2.2.1 Room CRUD：按 external_room_id 查找房间**

- 文件：`app/crud/room.py`
- 新增方法（示例）：

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

**2.2.2 Session CRUD：按 (room_id, playback_url_hash) 查找会话**

- 文件：`app/crud/session.py`
- 新增方法（示例）：

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

---

### 2.3 Service 层

#### 2.3.1 SessionImportService：导入会话幂等化

- 文件：`app/services/session_import.py`
- 在现有 `import_create_session` 基础上，新增：
  - 回放地址规范化；  
  - 哈希计算；  
  - `(room_id, playback_url_hash)` 维度的 get-or-create。

**伪代码：**

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

        # 2. 幂等查询
        existing = await crud_session.get_by_room_and_playback_hash(
            db=self.db,
            room_id=room_id,
            playback_url_hash=playback_hash,
        )
        if existing:
            return existing, True  # True 表示幂等命中

        # 3. 创建会话
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

> 对 API 层而言，返回值可以是 `(session, idempotent_hit)`，由 Endpoint 决定是否在响应中新增 `idempotent_hit` 字段。

#### 2.3.2 BatchImportService：房间与会话幂等

- 文件：`app/services/batch_import.py`

1）房间幂等（Room）：

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

    # b) 有 external_room_id：按(user_id, external_room_id) 幂等
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

2）会话幂等（Session）：

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

> 注意：dry_run 模式下不应写入数据库，但仍需完整执行字段校验与表头映射逻辑。

#### 2.3.3 CSV 表头到 `external_room_id` 映射

为了让 `_get_or_create_room_for_row` 能够使用外部直播间 ID，实现 `(user_id, external_room_id)` 维度的幂等复用，  
需要在 Batch Import 的表头解析逻辑（例如 `_apply_header_aliases`）中新增对 `external_room_id` 的别名映射规则：

- 逻辑字段 `external_room_id` 的候选表头包括（不区分大小写，去除首尾空格后匹配）：
  - `"external_room_id"`
  - `"直播间id"`
  - `"直播间ID"`

即：如果 CSV/Excel 表头为上述任一值，解析后的行数据中应统一映射为 `row["external_room_id"]`，  
后续 `_get_or_create_room_for_row` 可直接使用该字段进行房间幂等判断。

#### 2.3.4 `playback_url_hash` 维护范围（Service 层强约束）

在实现层面，除了在 Import Session / Batch Import 场景中写入 `playback_url_hash` 外，还必须满足以下统一约束：

- **所有会修改 `playback_url` 的 Service 方法**（包括但不限于：
  - `SessionImportService.import_create_session`；
  - `BatchImportService` 中调用 Import Session 的路径；
  - `SessionService.update_scheduled_session_info` 中允许更新回放地址的分支；
  - `SessionService.auto_generate_playback_url` 等后台生成回放地址的方法），
- 都必须在更新 `playback_url` 时，同步调用：

  ```python
  playback_url_hash = calc_playback_url_hash(new_url)
  ```

  将计算结果写入 `live_sessions.playback_url_hash` 字段。

> 换言之：**凡是更新 `playback_url` 的 Service 方法，都必须同步维护 `playback_url_hash`**，  
> 任何只改 URL 而不更新 hash 的实现都视为不符合本补丁的设计约定。

---

### 2.4 API 层

**2.4.1 Import Session Endpoint（可选扩展）**

- 文件：`app/api/v1/endpoints/session_import.py`
- 在成功响应中，**可选**增加 `idempotent_hit` 字段：

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
    "idempotent_hit": idempotent_hit,
}
```

**2.4.2 Batch Import Endpoint**

- 文件：`app/api/v1/endpoints/batch_import.py`
- 路由与 Query 参数保持 V5 不变；  
- 无需改动接口签名，只需兼容新的导入报告结构（`data.items[*]` 中新增 `skipped` / `skip_reason`）。

---

## 3. 关键流程差异（Before / After）

### 3.1 房间创建（Batch Import）

- **V5 Before**：
  1. 若行有 `room_id`：按 `room_id` + 权限校验复用房间；  
  2. 否则：每行创建一个全新的 `LiveRoom`。

- **V6 After**：
  1. 若行有 `room_id`：行为与 V5 一致；  
  2. 否则若有 `external_room_id`：按 `(user_id, external_room_id)` 幂等复用房间；  
  3. 否则：每行创建一个新房间（与 V5 一致）。

### 3.2 会话创建（Import / Batch Import）

- **V5 Before**：
  - Import Session / Batch Import 直接创建新的 `LiveSession` + `SessionStatistics`，不查重；  
  - 同一 `room_id` 下可以存在多条 `playback_url` 完全相同的记录。

- **V6 After**：
  1. 对 `playback_url` 做规范化与哈希计算：`playback_url_hash`；  
  2. 按 `(room_id, playback_url_hash)` 查询是否已有记录：  
     - 若存在 → 返回已有记录，视为幂等命中；  
     - 若不存在 → 创建新记录并写入 hash。

---

## 4. 新增/修改测试用例清单

在 `tests/integration/test_import_batch.py` 与 `tests/integration/test_sessions_import.py` 基础上，建议新增：

1. `test_batch_import_idempotent_same_csv_twice`  
   - 同一 CSV 以 `mode=apply` 导入两次；  
   - 断言：  
     - 第二次导入 `success_count` 与第一次相同；  
     - `items[*].skipped == True`；  
     - 数据库中房间数/场次数不增加。

2. `test_batch_import_idempotent_cross_files`  
   - 构造两个 CSV，包含相同“外部直播间ID + playback_url”的行；  
   - 依次导入后，断言只存在一个对应 `LiveRoom` + 一个对应 `LiveSession`。

3. `test_import_session_idempotent`  
   - 对同一 `room_id` + 相同 `playback_url` 的 Import Session API 连续调用两次；  
   - 断言第二次返回的 `id` 与第一次相同；  
   - 若实现了 `idempotent_hit` 字段，则额外断言为 `true`。

4. `test_batch_import_report_skipped_field`  
   - 验证导入报告 `items[*]` 中存在 `skipped` / `skip_reason` 字段，且语义正确。

---

## 5. 发布步骤与回滚策略

### 5.1 发布步骤

1. **执行数据库迁移（只加字段和索引）**
   - 执行本补丁第 2.1 节中的 DDL 脚本；  
   - 确保所有实例 schema 与应用代码期望一致。

2. **上线应用层代码**
   - 部署包含新字段支持、CRUD 扩展、Service 幂等等改动的版本；  
   - 保证 Import / Batch Import / 回放更新路径均正确维护 `external_room_id` 与 `playback_url_hash`。

3. **灰度验证**
   - 在灰度环境中运行重复导入用例，确认不再产生重复房间/场次；  
   - 监控数据库唯一索引冲突日志，确保异常被正确捕获与转换。

### 5.2 回滚策略

- 若仅需回滚应用逻辑（DB 迁移保留）：
  - 退回到 V5 逻辑版本；  
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

  3. 回滚应用代码到 V5 版本。

---

## 6. Self-check 自检清单

- **V5 内容是否被删除或弱化？**  
  - 否。本补丁仅新增字段/索引与 Import/Batch Import 相关逻辑，所有 V5 API 与现有行为保持不变。

- **是否覆盖两类重复导入场景？**  
  - 同一 CSV 重复上传：通过 `(user_id, external_room_id)` + `(room_id, playback_url_hash)` 去重；  
  - 不同 CSV 含相同行：只要外部直播间 ID 与 playback_url 一致，也会通过相同机制去重。

- **DDL/索引是否与字段类型一致？**  
  - `external_room_id` 使用 `VARCHAR(64)`；  
  - `playback_url_hash` 使用 `VARCHAR(128)`，可以完整存储 SHA-256 十六进制字符串（实际长度为 64）。

- **旧路由/旧语义是否保持不变？**  
  - 是。未对任何已有 API 做删除/重命名/参数语义变更。

- **并发/重复请求是否有 DB 级兜底？**  
  - 是。通过新增的部分唯一索引保证最终只保留一条物理记录；  
  - CRUD 层负责将唯一约束异常转换为可预期的业务异常。


