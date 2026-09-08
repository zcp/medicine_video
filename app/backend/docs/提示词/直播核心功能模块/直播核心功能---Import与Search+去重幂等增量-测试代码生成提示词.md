## LiveCore Service - Import 与 Search + 批量导入 V6 幂等增量  
### 测试代码生成提示词（专用版）

> 使用方式：  
> 1. 在 Cursor 聊天框中，先粘贴（或通过 `@` 引用）本 `.md` 文件的全部内容；  
> 2. 然后在**同一条消息的最上方**，按下面“5. 上下文文件引用列表”中的示例，用 `@` 引用你的设计文档和实现代码文件；  
> 3. 让 AI 严格按照本提示词生成**新的测试代码文件**（不能修改已有测试与 `conftest.py`）。

---

### 1. 角色定义（执行者）

你是一名资深 **Python 测试架构师**，熟悉：

- `pytest` / `pytest-asyncio` / `httpx.AsyncClient` / `pytest-mock` / `AsyncMock`
- “学院派”三层架构：API (Catch) → Service (Throw) → CRUD (Transaction)
- 已经存在一套 **V5 + V5-Import** 的测试与 `conftest.py`，这些测试全部通过，**禁止修改**

你的任务是：在**不修改任何已有测试代码/fixture** 的前提下，为

- 《直播核心功能设计文档 V6 - Import 与 Search + 批量导入幂等版》

中描述的 **V6 去重幂等增量**，编写一套 **新增的、可运行的 pytest 测试文件**，完全覆盖所有 V6 新增/变更点。

---

### 2. 范围与硬约束

- **测试范围**：仅针对 **V6 Import/Search + 批量导入幂等增量**，包括但不限于：
  - `external_room_id` / `playback_url_hash` 字段与部分唯一索引；
  - 新增 CRUD 方法：`get_by_external_id`、`get_by_room_and_playback_hash`；
  - `SessionImportService.import_create_session` 幂等逻辑；
  - `BatchImportService` 中房间幂等（`_get_or_create_room_for_row`）与会话幂等（`_process_row`）；
  - CSV 表头 alias（`external_room_id` 的中英文表头映射）；
  - 新增响应字段：`idempotent_hit` / `skipped` / `skip_reason` / （可选）`skipped_count`；
  - 所有修改 `playback_url` 的 Service 方法同步维护 `playback_url_hash`；
  - 并发请求下的幂等与唯一约束兜底。
- **禁止修改**：
  - 已有所有测试文件（尤其是 V5 与 V5-Import 相关测试）；
  - `conftest.py`（以及其中已有的 fixture 定义）。
- **允许操作**：
  - 只允许新增测试文件，例如：
    - `tests/test_v6_crud_dedup.py`
    - `tests/test_v6_service_import_idempotent.py`
    - `tests/test_v6_service_batch_idempotent.py`
    - `tests/test_v6_api_import_and_batch_idempotent.py`
  - 在新增测试文件中定义新的测试函数与必要的**测试辅助函数**。

---

### 3. 测试环境与 fixture 约定（只读，不可改）

假定项目已有（**且不可修改**）如下 fixture / 配置（命名以你现有工程为准，若有差异，请以实际为准，但**不得改动实现**）：

- `setup_database`：session 级，负责建表和清理；
- `db_session`：function 级，异步 SQLAlchemy 会话，用于 CRUD 级测试与 API 测试的 Arrange 阶段；
- `async_client`：function 级，`httpx.AsyncClient` 实例；
- `async_session_factory`：用于创建**全新独立会话**，在 API 测试的 Assert 阶段验证数据库最新状态。

**要求：**

- 所有新增测试代码必须**直接复用**这些 fixture，不得重新定义、不得改签名、不得改行为；
- 新增测试函数的 fixture 使用风格应**模仿你现有测试文件**（例如是否使用 `async for`、如何获取 Session 等），保持一致。

---

### 4. 测试哲学与断言策略（按层级区分）

#### 4.1 测试风格总表

| 测试目标层级           | 强制测试风格       | 工具/依赖                                | 重点验证目标                                           |
| ---------------------- | ------------------ | ---------------------------------------- | ------------------------------------------------------ |
| **CRUD 层**            | 实用派（Pragmatic） | `db_session`（真实 DB）                  | 字段写入、查询结果、部分唯一索引行为                   |
| **Service 层**         | 学院派（Academic） | `pytest-mock` / `AsyncMock`（Mock CRUD） | 业务逻辑：幂等判断、hash 计算、权限/参数异常          |
| **API / Endpoint 层**  | 实用派（Pragmatic） | `async_client` + `async_session_factory` | 完整链路：HTTP→JSON 响应→真实 DB 状态（幂等表现）     |

#### 4.2 通用结构规范

- 每个测试函数必须清晰分成三部分：
  - `# Arrange`：准备数据、构造请求、设置 Mock；
  - `# Act`：执行被测函数 / API；
  - `# Assert`：断言响应与数据库状态。
- 命名建议以行为为中心（例如 `test_import_session_idempotent_hit`、`test_batch_import_external_room_id_aliases`）。

#### 4.3 API 层特别要求

- 必须断言：
  - HTTP 状态码；
  - 业务 code（例如 `response.json()["code"]`）；
  - 关键业务字段（尤其是 V6 新增字段：`idempotent_hit`、`skipped`、`skip_reason`、`skipped_count`）。
- 校验数据库状态时：
  - **禁止**在调用 API 的同一 `db_session` 中再次 `get()` 或查询同一主键（会命中 Identity Map 缓存，读取到旧值）；
  - 必须通过 `async_session_factory` 创建新的会话验证，例如：

```python
async with async_session_factory() as new_db:
    # 使用 new_db 查询最新的 Session / Room，验证幂等行为
```

---

### 5. 上下文文件引用列表（请在使用时用 `@` 引用）

> 在真正执行本提示词前，请在 Cursor 消息顶部增加如下（或等价）`@` 引用，让 AI 能读取设计文档与实现代码。  
> 路径请按你实际项目名称调整，下面是基于你当前仓库的推荐示例：

- 设计文档（V6 语义来源）：
  - `@live-streaming-saas/docs/03_系统设计/直播核心功能设计文档v6-Import与Search+批量导入幂等版.md`
- 模型与 CRUD 层实现：
  - `@backend/live_core_service/app/models/live_core.py`
  - `@backend/live_core_service/app/crud/room.py`
  - `@backend/live_core_service/app/crud/session.py`
- Service 层实现：
  - `@backend/live_core_service/app/services/session_import.py`
  - `@backend/live_core_service/app/services/batch_import.py`
  - `@backend/live_core_service/app/services/session.py`  （包含 `update_scheduled_session_info`、`auto_generate_playback_url` 等）
- API 层实现：
  - `@backend/live_core_service/app/api/v1/endpoints/session_import.py`
  - `@backend/live_core_service/app/api/v1/endpoints/batch_import.py`
- 已有测试与 fixture（只读参考）：
  - `@backend/live_core_service/tests/conftest.py`
  - （如有）`@backend/live_core_service/tests/test_import_*.py`、`@backend/live_core_service/tests/test_batch_import_*.py`

> 要求：生成测试代码时，必须结合上述文件的**真实实现**和 V6 设计文档的语义，确保测试行为与实际代码完全对齐。

> 调用时可以直接按如下模板发起一条消息（上半部分是上下文引用，下半部分是本提示词全文）：
>
> ```md
> @live-streaming-saas/docs/03_系统设计/直播核心功能设计文档v6-Import与Search+批量导入幂等版.md
> @backend/live_core_service/app/models/live_core.py
> @backend/live_core_service/app/crud/room.py
> @backend/live_core_service/app/crud/session.py
> @backend/live_core_service/app/services/session_import.py
> @backend/live_core_service/app/services/batch_import.py
> @backend/live_core_service/app/services/session.py
> @backend/live_core_service/app/api/v1/endpoints/session_import.py
> @backend/live_core_service/app/api/v1/endpoints/batch_import.py
> @backend/live_core_service/tests/conftest.py
>
> （下面粘贴《直播核心功能---Import与Search+去重幂等增量-测试代码生成提示词.md》的全文）
> ```

---

### 6. 具体测试任务清单（必须覆盖所有 V6 新增内容）

> 下列任务是你**必须实现的测试用例集合**。你可以按逻辑分组拆分到多个测试文件中，但不允许漏掉任何一类行为。

#### 6.1 CRUD 层：去重相关方法与唯一索引

**文件**：`app/crud/room.py`

1. `test_get_by_external_id_found`
   - 场景：数据库中存在 `(user_id, external_room_id)` 对应的房间。
   - 断言：
     - `get_by_external_id` 返回非空；
     - 返回的 `id` / `user_id` / `external_room_id` 与插入数据一致。

2. `test_get_by_external_id_not_found`
   - 场景：无匹配记录；
   - 断言：返回 `None`。

3. `test_external_room_id_partial_unique_index`
   - 场景：插入一条 `(user_id, external_room_id)` 后，再插入同样键值；
   - 断言：触发唯一约束错误，并在 CRUD 或 Service 层被转换为预期的自定义异常（具体根据实现而定）。

**文件**：`app/crud/session.py`

4. `test_get_by_room_and_playback_hash_found`
   - 场景：存在 `(room_id, playback_url_hash)` 对应的会话；
   - 断言：返回该 Session。

5. `test_get_by_room_and_playback_hash_not_found`
   - 场景：无匹配记录；
   - 断言：返回 `None`。

6. `test_playback_url_hash_partial_unique_index`
   - 场景：插入一条 `(room_id, playback_url_hash)` 后，再插入相同键值；
   - 断言：唯一约束异常被正确处理（与设计文档中的异常口径一致）。

> 若唯一约束异常只在 Service / API 级别被断言，可以在对应层补测，但至少需有一处验证“只保留一条物理记录”的行为。

---

#### 6.2 Service：Import Session 幂等（`SessionImportService.import_create_session`）

**文件**：`app/services/session_import.py`  
**风格**：Mock CRUD，验证业务分支与幂等逻辑。

1. `test_import_create_session_first_time_success`
   - Mock：
     - `crud_room.get` 返回房间（`room.user_id == public_id`）；
     - `crud_session.get_by_room_and_playback_hash` 返回 `None`；
     - `crud_session.create` 返回新 Session。
   - 断言：
     - 传入 `session_in["playback_url"]` 被 `normalize_playback_url` 规范化后写入 `playback_url`；
     - `playback_url_hash` 使用 `calc_playback_url_hash` 计算得到；
     - 返回 `(session, idempotent_hit=False)`。

2. `test_import_create_session_idempotent_hit`
   - Mock：
     - `crud_session.get_by_room_and_playback_hash` 返回已有 Session；
   - 断言：
     - 不调用 `crud_session.create`；
     - 返回已有 Session；
     - `idempotent_hit=True`。

3. `test_import_create_session_room_not_found_raises`
   - Mock：`crud_room.get` 返回 `None`；
   - 断言：抛出 `RoomNotFoundException`（或实现中对应异常）。

4. `test_import_create_session_permission_denied_raises`
   - Mock：`crud_room.get` 返回房间但 `room.user_id != public_id`；
   - 断言：抛出 `PermissionDeniedException`。

5. （若实现了状态/参数校验）`test_import_create_session_invalid_status_or_url_raises`
   - 场景：非法 `status` 或 `playback_url`；
   - 断言：抛出 `InvalidParameterException`，错误信息与设计文档一致。

---

#### 6.3 Service：Batch Import 幂等（`BatchImportService`）

**文件**：`app/services/batch_import.py`

##### 6.3.1 房间幂等 `_get_or_create_room_for_row`

1. `test_get_or_create_room_with_room_id_reuse`
   - 场景：`row` 含 `room_id`，房间存在且属于当前用户；
   - 断言：
     - 调用 `crud_room.get`；
     - 不调用 `crud_room.get_by_external_id` 和 `crud_room.create`；
     - 返回已有房间。

2. `test_get_or_create_room_with_external_room_id_reuse`
   - 场景：无 `room_id`，有 `external_room_id` 且命中；
   - 断言：
     - 调用 `crud_room.get_by_external_id`；
     - 不调用 `crud_room.create`；
     - 返回已有房间。

3. `test_get_or_create_room_create_with_external_room_id`
   - 场景：无 `room_id`，`external_room_id` 未命中；
   - Mock：`crud_room.get_by_external_id` 返回 `None`，`crud_room.create` 返回新房间；
   - 断言：
     - 会调用 `crud_room.create`；
     - 最终房间的 `external_room_id` 被设置为传入值（可在 Service 层对象上断言，或在 DB 层验证）。

4. `test_get_or_create_room_with_room_id_not_found_or_no_permission_raises`
   - 场景：`room_id` 提供但房间不存在或无权限；
   - 断言：抛出设计文档中指定的参数异常（例如 `InvalidParameterException("房间不存在或无权限")`）。

##### 6.3.2 会话幂等 `_process_row`

1. `test_process_row_apply_first_time_success`
   - 场景：`mode="apply"`，第一次导入；
   - Mock：
     - `_get_or_create_room_for_row` → 房间；
     - `SessionImportService.import_create_session` → `(session, idempotent_hit=False)`。
   - 断言：
     - 返回结构中：`status == "success"`；`skipped == False`；`skip_reason is None`；
     - `room_id` / `session_id` 为有效 UUID 字符串。

2. `test_process_row_apply_idempotent_hit`
   - 场景：`mode="apply"`，命中幂等；
   - Mock：`SessionImportService.import_create_session` → `(session, idempotent_hit=True)`；
   - 断言：
     - `skipped == True`；
     - `skip_reason == "duplicate_session_by_playback_url"`。

3. `test_process_row_dry_run_no_db_writes`
   - 场景：`mode="dry_run"`；
   - 断言：
     - 不调用 `SessionImportService.import_create_session` 与 `crud_session.create`；
     - 仅返回字段校验与解析结果。

---

#### 6.4 Service：`playback_url_hash` 全局维护

**文件**：`app/services/session.py` 等

1. `test_update_scheduled_session_info_updates_hash`
   - 场景：通过 `update_scheduled_session_info` 更新包含 `playback_url` 的请求；
   - 断言：
     - 新的 `playback_url` 经 `calc_playback_url_hash` 计算后写入 `playback_url_hash`；
     - 若实现了唯一约束冲突时的异常转换，应有对应测试验证。

2. `test_auto_generate_playback_url_updates_hash`
   - 场景：`auto_generate_playback_url` 为某 Session 生成默认回放地址；
   - 断言：
     - 生成的回放 URL 同步写入 `playback_url_hash`；
     - 行为与设计文档中关于“只在 `ready` 且 `playback_url` 为空时生成”的约束一致。

---

#### 6.5 API：Import Session 与 Batch Import 幂等行为

**文件**：

- `app/api/v1/endpoints/session_import.py`
- `app/api/v1/endpoints/batch_import.py`

##### 6.5.1 Import Session API

1. `test_api_import_session_first_time_success`
   - 使用 `async_client` + `db_session` + `async_session_factory`；
   - 步骤：
     - Arrange：创建房间，构造合法 Import 请求（`status in {'finished', 'ready'}`，带 `playback_url`）；  
     - Act：`POST /api/v1/rooms/{room_id}/sessions/import`；  
     - Assert：
       - HTTP 状态码与业务 code 正确；  
       - `data.playback_url` 为期望值（或规范化后值）；  
       - 若返回 `idempotent_hit`，应为 `False` 或缺省；  
       - 使用 `async_session_factory` 查询 DB，确认 `playback_url_hash` 正确写入，且只生成一条 Session 记录。

2. `test_api_import_session_idempotent_twice`
   - 场景：同一 payload 调用两次；
   - 断言：
     - 两次返回的 `data.id` 相同；  
     - 第二次如有 `data.idempotent_hit` 字段，则为 `True`；  
     - DB 中仅存在一条对应 Session。

##### 6.5.2 Batch Import API

1. `test_api_batch_import_idempotent_same_file_twice`
   - 场景：同一个 CSV 文件，两次 `mode="apply"` 导入；
   - CSV 至少包含一行带 `external_room_id` + `playback_url` 的记录。
   - 断言：
     - 第一次成功落库，`success_count == N`；  
     - 第二次导入：
       - `success_count == N`，`failed_count == 0`；  
       - 所有成功行 `items[*].skipped == True`，`skip_reason == "duplicate_session_by_playback_url"`；  
       - 若返回 `skipped_count`，其值等于被跳过的行数；  
       - DB 中房间/场次数量不增加（用新会话查询）。

2. `test_api_batch_import_idempotent_cross_files`
   - 场景：两个 CSV 文件中包含相同 `(external_room_id, playback_url)` 行；
   - 断言：
     - 两次导入后，数据库中：
       - `(user_id, external_room_id)` 唯一 → 只有一个房间；  
       - `(room_id, playback_url_hash)` 唯一 → 只有一个 Session；  
       - 第二个文件中的重复行在导入报告中被标记为 `skipped`。

3. `test_api_batch_import_external_room_id_header_aliases`
   - 场景：使用三种不同表头：
     - `"external_room_id"`；
     - `"直播间id"`；
     - `"直播间ID"`。
   - 断言：
     - 三种表头均能被解析并映射到 `row["external_room_id"]`；  
     - 在 `(user_id, external_room_id)` 维度上表现出相同的幂等复用行为。

---

#### 6.6 并发与唯一约束兜底（可在 API 或 Service 层）

1. `test_import_session_concurrent_only_one_session_persisted`
   - 场景：并发多个请求导入相同 `room_id + playback_url`；
   - 断言：
     - 最终 DB 中只存在一条匹配 `(room_id, playback_url_hash)` 的 Session；  
     - 若部分请求触发唯一约束异常，应被正确转换为设计文档预期的业务错误响应。

2. （可选）`test_batch_import_concurrent_only_one_session_per_row`
   - 类似策略，可根据实现复杂度决定是否补充。

---

### 7. 交付物要求

在完成上述任务后，你需要输出一组**新增的**测试文件，例如：

- `tests/test_v6_crud_dedup.py`
- `tests/test_v6_service_import_idempotent.py`
- `tests/test_v6_service_batch_import_idempotent.py`
- `tests/test_v6_api_import_and_batch_idempotent.py`

**必须满足：**

1. **测试用例完整覆盖本提示词第 6 节列出的所有行为与场景**（允许拆分/合并，但不允许漏测）。  
2. **不修改、不删除任何已有测试文件与 `conftest.py`**，所有新增测试与既有测试能够一起 `pytest` 全量通过。  
3. 测试代码在风格上与现有项目测试保持一致，并完全符合本提示词中关于分层测试哲学、fixture 使用和断言策略的要求。


