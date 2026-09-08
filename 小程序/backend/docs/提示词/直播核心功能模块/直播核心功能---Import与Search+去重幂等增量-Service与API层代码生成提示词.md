# LiveCore Service - Import 与 Search + 批量导入 V6 去重幂等增量 - Service 与 API 层代码生成提示词

## 1. 角色定义

你是一名精通「学院派架构（Clean Architecture）」的资深 Python 后端架构师，负责 **Service 层（业务逻辑）** 与 **API 层（Endpoint 路由）** 的实现。  
你已经基于《Import 与 Search 增量功能》完成了 V5 的 Import / Search / Batch Import 代码，现在需要在 **不破坏现有行为** 的前提下，为 **V6 去重幂等增量** 做补丁式增强。

## 2. 任务目标（V6 增量范围）

本次任务 **只针对 V6 去重幂等相关逻辑做最小增量**，不重写、不删除既有 Import / Search / Batch Import 实现：

1. **Import Session 幂等化（Service 层）**  
   - 在 `SessionImportService.import_create_session` 中引入：  
     - `playback_url` 规范化与哈希计算；  
     - 通过 `(room_id, playback_url_hash)` 查重（若存在则返回已有记录 + `idempotent_hit=True`）；  
     - 若不存在则创建新会话，写入 `playback_url_hash`，返回 `idempotent_hit=False`。
2. **Batch Import 幂等化（Service 层）**  
   - 在 `BatchImportService` 中：  
     - 扩展 `_get_or_create_room_for_row`，支持 `(user_id, external_room_id)` 维度的 Room 幂等复用；  
     - 改造 `_process_row`，统一调用 `SessionImportService.import_create_session`，并在结果中增加 `skipped` / `skip_reason`。
3. **`playback_url_hash` 全局维护（Service 层）**  
   - 在所有会修改 `playback_url` 的 Service 方法中（包括但不限于）：  
     - `SessionImportService.import_create_session`；  
     - `BatchImportService` 中 `mode="apply"` 写入回放地址的路径；  
     - `SessionService.update_scheduled_session_info` 中允许更新回放地址的分支；  
     - `SessionService.auto_generate_playback_url` 等后台生成回放地址的方法；  
   - 都必须在更新 `playback_url` 时同步调用 `calc_playback_url_hash(new_url)`，写入 `playback_url_hash`。
4. **API 层最小扩展**  
   - Import Session Endpoint：在保持原有请求/响应结构不变的前提下，**可选**增加 `idempotent_hit` 字段；  
   - Batch Import Endpoint：在 `data.items[*]` 中新增 `skipped` / `skip_reason` 字段，以及可选的顶层 `skipped_count`。

> 关键：  
> - **禁止**修改已有路由路径、HTTP 方法、必填字段、错误码语义；  
> - **禁止**删除或重命名现有 Service / API 函数；  
> - 所有改动都必须是 **补丁式增强**，对旧调用方透明。

## 3. 内容来源（设计文档）

本次增量必须严格对齐以下设计文档：

- `docs/03_系统设计/直播核心功能设计文档v6-Import与Search+批量导入幂等版.md`
  - 重点章节：
    - 2「数据库 Schema 增量（V5-Import → V6 幂等版）」  
    - 3「回放 URL 规范化与哈希规则」  
    - 4「Import Session API（导入会话 + 幂等扩展）」  
    - 6「Batch Import API（批量导入 + 幂等扩展）」  
    - 7「CRUD 扩展（去重相关）」  
    - 9「测试策略（在 V5-Import 基础上的增量）」  

如设计文档与本提示词存在差异，以 **V6 设计文档** 为最终口径。

## 4. 继承的架构与编码规范

本提示词在以下方面**完全继承**你现有的「Import 与 Search 增量功能 - Service 与 API 层代码生成提示词」中的规范：

### 4.1 用户身份解析规范（JWT → UUID）

**API 层**：

```python
from typing import Dict
from uuid import UUID

current_user: Dict = Depends(get_current_user)
public_id = UUID(current_user.get("public_id"))
role_str = current_user.get("role", "REGULAR").upper()
```

**Service 层** 只接受 `public_id: UUID` 等基础标识，不接受 ORM `User` 实体：

```python
async def some_action(
    self,
    public_id: UUID,
    room_id: UUID,
    ...
):
    ...
```

### 4.2 分层职责（学院派核心）

- **Service 层**：
  - ✅ 负责业务逻辑与权限校验；  
  - ✅ 抛出自定义 Python 异常（`RoomNotFoundException`、`PermissionDeniedException`、`InvalidParameterException` 等）；  
  - ❌ 不抛出 `HTTPException`；  
  - ❌ 不处理事务（不调用 `db.commit()` / `db.rollback()`）。

- **API 层**：
  - ✅ 使用 `try...except` 捕获所有 Service / CRUD 抛出的自定义异常；  
  - ✅ 使用 `JSONResponse` + `error_response()` 构建错误响应；  
  - ✅ 使用 `success_response()` 构建成功响应；  
  - ❌ 不做复杂业务逻辑与权限判断（只做最薄的参数层封装）。

### 4.3 异常与错误码映射

沿用上一版规范，将异常映射到 HTTP 状态码 + 业务错误码，例如：

- `RoomNotFoundException` → `404` + `code=2001`；  
- `PermissionDeniedException` → `403` + `code=3002`；  
- `InvalidParameterException` → `400` + `code=4xxx`（如 4001/4002 等）；  
- `DatabaseIntegrityException` → `400` + `code=4001`；  
- 未捕获异常 → `500` + `code=1000`。

## 5. V6 特有的工具函数与全局约束

### 5.1 URL 规范化与哈希计算

根据 V6 设计文档 3 章，统一的工具函数为：

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

### 5.2 全局硬约束：凡更新 playback_url 必须同步维护 hash

在以下所有 Service 方法中，只要更新 `playback_url`，**必须**同步调用 `calc_playback_url_hash(new_url)` 并更新 `playback_url_hash`：

- `SessionImportService.import_create_session`；  
- `BatchImportService` 中 `mode="apply"` 写入回放地址的路径（通过 Import Service 间接完成）；  
- `SessionService.update_scheduled_session_info` 中允许修改回放地址的分支；  
- `SessionService.auto_generate_playback_url` 等后台自动写回回放地址的方法。

> 换言之：**任何只改 `playback_url` 而不更新 `playback_url_hash` 的实现都违反本 V6 设计。**

## 6. Import Session V6 增量实现要求（Service + API）

### 6.1 Service 层：`SessionImportService.import_create_session`

**文件**：`app/services/session_import.py`  
**目标**：在保持 V5 行为（房间存在性 / 权限 / 参数校验）不变的基础上，引入幂等和 hash 逻辑。

#### 6.1.1 关键步骤

1. **房间存在性与权限检查**（沿用 V5-Import）：  
   - `room = await crud_room.get(self.db, room_id=room_id)`；  
   - 不存在 → `raise RoomNotFoundException`；  
   - `room.user_id != public_id` → `raise PermissionDeniedException`。
2. **参数校验**（可沿用 V5-Import 原有逻辑）：  
   - `status in {'finished', 'ready'}`；  
   - `playback_url` 非空且格式合法。
3. **计算 hash 并查重**（V6 新增逻辑，对齐设计文档 4.2.1）：  

```python
status = session_in["status"]
playback_url = session_in["playback_url"]

playback_hash = calc_playback_url_hash(playback_url)
normalized = normalize_playback_url(playback_url)

existing = await crud_session.get_by_room_and_playback_hash(
    db=self.db,
    room_id=room_id,
    playback_url_hash=playback_hash,
)
if existing:
    # 命中幂等
    return existing, True
```

4. **创建新会话（包含 hash 字段）**：

```python
session_data = {
    "id": uuid.uuid4(),
    "room_id": room_id,
    "status": status,
    "start_time": session_in.get("start_time"),
    "end_time": session_in.get("end_time"),
    "playback_url": normalized,
    "playback_url_hash": playback_hash,
    # 其他字段如 title/description 可按原 V5-Import 逻辑补充
}
db_session = await crud_session.create(self.db, obj_in=session_data)
return db_session, False
```

#### 6.1.2 返回值约定

与 V6 设计文档一致，`import_create_session` 应返回 `(LiveSession, bool)`：

- `bool` 表示是否命中幂等（`idempotent_hit`）。

### 6.2 API 层：Import Session Endpoint

**文件**：`app/api/v1/endpoints/session_import.py`  
**路由**：保持原有 `POST /api/v1/rooms/{room_id}/sessions/import` 不变。

在调用 Service 之后，增加对 `idempotent_hit` 的处理，例如：

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
    "idempotent_hit": idempotent_hit,  # V6 可选字段
}
return success_response(data=response_data)
```

- 该字段为**可选**：旧前端忽略即可，不影响兼容性。

异常处理逻辑沿用上一版 Service/API 提示词，不再赘述。

## 7. Batch Import V6 增量实现要求（Service + API）

### 7.1 Service 层：`BatchImportService` 房间幂等

**文件**：`app/services/batch_import.py`  
**方法**：`_get_or_create_room_for_row(self, public_id: UUID, row: Dict) -> LiveRoom`

按 V6 文档 6.3 实现：

1. **有 `room_id` 时复用房间**（保持 V5-Import 行为）；
2. **否则若有 `external_room_id` 时，按 `(user_id, external_room_id)` 幂等复用**：

```python
external_room_id = row.get("external_room_id")
if external_room_id:
    room = await crud_room.get_by_external_id(
        db=self.db,
        user_id=public_id,
        external_room_id=external_room_id,
    )
    if room:
        return room
```

3. **否则创建新房间**，并在有 external_room_id 时写入该字段：

```python
room = await crud_room.create(self.db, obj_in=room_data, user_id=public_id)
if external_room_id:
    room.external_room_id = external_room_id
    await self.db.commit()
    await self.db.refresh(room)
return room
```

### 7.2 Service 层：`BatchImportService` 会话幂等

**方法**：`_process_row(...)`

- 在 `mode == "apply"` 的路径下，不再直接调用 `crud_session.create`，而是调用 `SessionImportService.import_create_session`：

```python
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

- `dry_run` 模式保持 **只校验不落库** 的语义。

### 7.3 Batch Import 的 CSV 表头映射扩展

在解析 CSV/Excel 表头时，除了原有的：

- `标题` → `room_title`  
- `播放url` / `播放url1` → `playback_url`  
- `封面图片` → `cover_url`

还要新增：

- `external_room_id` 的候选表头：
  - `"external_room_id"`  
  - `"直播间id"`  
  - `"直播间ID"`

并统一映射为 `row["external_room_id"]`，供 `_get_or_create_room_for_row` 使用。

### 7.4 API 层：Batch Import Endpoint

**文件**：`app/api/v1/endpoints/batch_import.py`  
**路由**：保持 `POST /api/v1/rooms/import/batch` 不变。

- 成功响应中，`data.items[*]` 在原有字段（`row_no` / `room_id` / `session_id` / `status` / `error`）基础上，新增：

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

- 顶层可选新增 `skipped_count`，统计 `skipped == true` 的行数。

旧前端若不关心幂等，可忽略这些新增字段。

## 8. 其他需要打补丁的 Service 方法（hash 维护）

根据 V6 设计文档 3.3，本提示词要求你在实现时 **检查并补齐** 以下方法中的 hash 维护逻辑：

- `SessionService.update_scheduled_session_info`：  
  - 当请求中包含 `playback_url` 且校验通过时，必须计算 `playback_url_hash` 并更新；  
  - 若新 hash 与同一房间内已有记录冲突，应通过 CRUD 层抛出的唯一约束异常转为业务错误，而非静默覆盖。
- `SessionService.auto_generate_playback_url`：  
  - 在生成默认回放地址并写入 `playback_url` 时，同步写入 `playback_url_hash`。

> 提示：  
> - 这些方法的具体签名与已有逻辑需从当前代码中读取；  
> - 本次增量只在「写入 `playback_url`」的那一小段中插入 hash 计算与写入逻辑。

## 9. 代码质量检查清单（V6 增量）

在生成或修改 Service/API 代码后，请自检：

- [ ] 未删除或重命名任何现有 Service / API 类与函数；  
- [ ] Import Session / Batch Import 的路由与请求/响应结构保持与 V5-Import 一致；  
- [ ] 新增的 `idempotent_hit` / `skipped` / `skip_reason` / `skipped_count` 均为**可选字段**；  
- [ ] 所有更新 `playback_url` 的路径都调用了 `calc_playback_url_hash(new_url)` 并写入 `playback_url_hash`；  
- [ ] `SessionImportService.import_create_session` 在逻辑上严格符合 V6 设计文档：  
  - 先查 `(room_id, playback_url_hash)`，再决定返回已有记录或创建新记录；  
- [ ] `BatchImportService` 的 `dry_run` 模式无任何写操作；  
- [ ] 所有新增/修改的 Service 方法仍不处理事务；  
- [ ] 所有新增/修改的 API 端点仍通过 `try...except` + 自定义异常映射构建响应；  
- [ ] 所有日志与异常处理风格与现有代码保持一致。

---

**请根据本提示词，在现有 V5 Import/Search/Batch Import 实现的基础上，以补丁方式完成 V6 去重幂等相关的 Service 与 API 层改造。**


