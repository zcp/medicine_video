
---

# 直播核心服务：live_sessions.playback_url 增量改造测试代码生成提示词

## 一、角色定义 (Role Definition)

你是一名资深的 Python 测试工程师，精通 pytest、unittest.mock、FastAPI 异步测试与 SQLAlchemy 异步会话。
你非常熟悉现有直播核心服务项目的测试风格和结构，能够在 **不破坏现有测试用例、不修改 conftest.py** 的前提下，以**增量方式**为新的业务变更补充测试用例。

你的目标是：
在保持现有测试全部通过的前提下，为 **live_sessions.playback_url 持久化与增量改造** 添加完整、清晰、可维护的测试覆盖。

---

## 二、任务目标 (Task Objective)

本次任务是对 **“直播场次回放地址 playback_url 改造”** 进行测试补充，属于 **增量开发** 测试任务。

### 2.1 功能背景

现有设计中，`GET /api/v1/sessions/{session_id}` 已经返回 `playback_url` 字段，但之前的逻辑是“根据 `status + video_id` 动态拼接 URL”，并未将其持久化到数据库中。

现在进行了 **增量改造**：

1. 在 `live_sessions` 表中新增持久字段：`playback_url VARCHAR(1024) NULL`
2. 在 SQLAlchemy Model 与 Pydantic Schema 中同步新增 `playback_url` 字段
3. 创建直播场次时：`playback_url` 必须为 `NULL`
4. 后台任务（如 `post_stream_processing_task`）在满足条件时自动生成并写入 `playback_url`
5. 支持通过 API 手动更新 `playback_url`（仅限特定状态）
6. `GET /api/v1/sessions/{session_id}` 直接返回数据库字段 `live_sessions.playback_url` 的值，不再现场拼接
7. 后台自动生成逻辑必须 **避免覆盖手动设置的播放地址**

### 2.2 本次测试需覆盖的增量行为

你需要为以下行为编写增量测试代码：

1. **新行为一：playback_url 字段持久化行为**

   * 创建场次时 `playback_url` 为 `NULL`
   * 更新或后台任务执行后，`playback_url` 正确持久化到数据库

2. **新行为二：后台任务自动写入 playback_url 的逻辑**

   * 满足条件：

     * `status == 'ready'`
     * `video_id` 不为空
     * `playback_url` 当前为 `NULL`
   * 自动生成并写入回放地址
   * 当 `playback_url` 已有手动值时，后台任务不得覆盖

3. **新行为三：GET session 返回值来源于数据库字段**

   * 若 DB 中 `playback_url` 不为 `NULL`，则响应中 `data["playback_url"]` 等于该值
   * 若 DB 中为 `NULL`，则响应中的 `playback_url` 为 `null`

4. **新行为四：PATCH session 更新 playback_url 的规则**

   * 仅在 `ready` 或 `finished` 状态下允许更新
   * 在 `live` / `scheduled` 状态下更新应被拒绝
   * 手动更新后的值不会被后续后台任务覆盖

---

## 三、核心上下文信息 (Core Context Information)

### 3.1 测试项目结构（与现有保持一致）

```bash
backend/live_core_service/
├── 📁 tests/
│   ├── 📄 conftest.py                     # 测试配置和公共fixture ⛔ 不可修改
│   ├── 📁 unit/
│   │   ├── 📄 test_crud_room.py
│   │   ├── 📄 test_crud_session.py        # Session CRUD 单元测试（本次可能会增量添加）
│   │   ├── 📄 test_service_room.py
│   │   └── 📄 test_service_session.py     # Session Service 单元测试 ⚠️ 本次重点增量添加
│   ├── 📁 integration/
│   │   ├── 📄 test_api_room.py
│   │   └── 📄 test_api_session.py         # Session API 集成测试 ⚠️ 本次重点增量添加
```

> ⚠️ 注意：
>
> * **严格禁止修改 `conftest.py`**
> * **禁止修改或删除任何已有测试函数**
> * 只允许在指定测试文件 **末尾添加新的测试函数 / 测试类**
> * 保持原有测试全部通过

### 3.2 与本次改造相关的新增 / 修改代码

> 以下为你需要关注并覆盖测试的“新行为 / 新代码点”（供你生成测试时参考）：

1. **数据库 & Model & Schema 增量字段**

   * `live_sessions.playback_url` 新增字段（可空）
   * SQLAlchemy Model `LiveSession.playback_url`
   * Pydantic 响应 Schema 中新增 `playback_url: Optional[str] = None`
   * PATCH Schema 中允许可选字段 `playback_url`（若存在）

2. **服务层（Service/Task）**

   * 后台任务（可能在 `app/services/session_service.py` 或任务模块）逻辑：

     * 在 `status == READY` 且 `video_id` 不为空 且 `playback_url is None` 时，根据默认规则生成 URL 并写入
     * 如果 `playback_url` 已有值（手动设置），则不得覆盖

3. **API 层**

   * `GET /api/v1/sessions/{session_id}`

     * `data["playback_url"]` 直接来自数据库字段 `live_sessions.playback_url`
   * `PATCH /api/v1/sessions/{session_id}`

     * 允许请求体中包含 `playback_url` 字段
     * 仅在 `ready / finished` 状态下可被更新
     * 在 `live / scheduled` 状态下更新应返回错误（403 或业务定义的错误码）

---

## 四、测试规范与约束 (Constraints)

### 4.1 核心约束 (Primary Constraints)

1. **不修改 `conftest.py`**
2. **不修改任何已有测试函数的实现或签名**
3. **只添加新测试函数 / 新测试类** 到既有测试文件末尾
4. **保持现有测试全部通过**
5. **新增测试必须与现有测试风格完全一致（命名、注释、结构、fixture 使用模式）**

### 4.2 测试风格与命名规范

参照现有测试规范（与封面上传测试提示词保持一致）：

* 文件名：`test_<module_name>.py`

* 函数名：`test_<function_name>_<scenario>`

* 文档字符串格式（三行式）：

  ```python
  """
  测试<功能描述>
  - <步骤1>
  - <步骤2>
  - <期望结果>
  """
  ```

* 结构模式：AAA 模式（Arrange / Act / Assert），但注释用中文：

  * `# 准备测试数据`
  * `# 执行操作`
  * `# 断言结果`
  * **禁止**使用英文 `# Arrange / # Act / # Assert`

* 异步测试：

  ```python
  @pytest.mark.asyncio
  async def test_xxx(async_client, db_session, auth_headers):
      async for client in async_client:
          ...
          break
  ```

---

## 五、本次增量测试范围总览 (Scope Overview)

你需要在以下文件中 **增量添加** 测试：

1. `tests/unit/test_service_session.py`

   * 新增：后台任务 / service 层关于 `playback_url` 自动生成与不覆盖逻辑的测试

2. `tests/integration/test_api_session.py`

   * 新增：围绕 `GET /api/v1/sessions/{session_id}` 与 `PATCH /api/v1/sessions/{session_id}` 的回放地址相关测试

> 可选：
> 如果项目存在 `tests/unit/test_crud_session.py` 且已经对 CRUD 做了通用测试，**可以只在集成测试层验证 `playback_url` 写入结果**，无需强行增加 CRUD 单元测试。

---

## 六、具体测试代码生成指令 (Detailed Instructions)

### 6.1 单元测试：Session Service / 后台任务 (tests/unit/test_service_session.py)

**文件**：`tests/unit/test_service_session.py`
**任务**：在文件末尾新增测试类/函数，用于测试 **后台任务 / Service 层** 关于 `playback_url` 的逻辑。

> 若文件中已经存在类似 `TestSessionService...` 的类，可参考其风格；若没有，可以新增一个测试类来组织本次测试。

#### 6.1.1 需要覆盖的场景列表

1. **test_post_stream_processing_sets_playback_url_when_ready_and_empty**

   * 前置：

     * 构造一个 `LiveSession` 对象：

       * `status = READY`
       * `video_id` 为有效 UUID
       * `playback_url = None`
   * Mock：

     * 如有独立 URL 生成工具，可 Mock 其返回 `'https://test-cdn.example.com/media/.../video_xxx.mp4'`
   * 执行：

     * 调用后台任务或对应 service 方法（例如 `SessionService.process_after_stream_end(session_id=...)`）
   * 断言：

     * 数据库/Session 对象的 `playback_url` 不为 None
     * 与预期格式匹配 / 或等于 Mock 返回值

2. **test_post_stream_processing_not_override_manual_playback_url**

   * 前置：

     * `status = READY`
     * `video_id` 为有效 UUID
     * `playback_url` 已有手动填写值 `"https://manual.example.com/custom.mp4"`
   * 执行后台任务
   * 断言：

     * 任务结束后 `playback_url` 仍然是 `"https://manual.example.com/custom.mp4"`
     * 不会被自动生成的 URL 覆盖

3. **test_post_stream_processing_skip_when_not_ready_or_no_video_id**

   * 前置三种子场景（可以写成一个测试中多次调用，也可以拆成多个测试）：

     1. `status = FINISHED`，`video_id` 有值，`playback_url=None`
     2. `status = READY`，`video_id=None`，`playback_url=None`
     3. `status = LIVE`，`video_id` 有值，`playback_url=None`
   * 执行任务
   * 断言：

     * 上述所有场景中，`playback_url` 仍然为 `None`，不会被自动填充

#### 6.1.2 实现要求

1. 使用现有 fixture / mock 风格（参考 `test_service_session.py` 其他测试）
2. 使用 `mocker` 来 Mock 依赖函数（如外部存储 URL 生成函数）
3. 使用文档字符串详细说明测试步骤与期望

---

### 6.2 集成测试：Session API (tests/integration/test_api_session.py)

**文件**：`tests/integration/test_api_session.py`
**任务**：在文件末尾新增一组测试，验证 **playback_url 持久化 + API 行为**。

#### 6.2.1 场景一：GET 返回数据库字段的值

**test_get_session_details_returns_playback_url_from_db**

* 测试目的：

  * 当数据库中 `playback_url` 有值时，`GET /api/v1/sessions/{session_id}` 返回的 `data["playback_url"]` 等于数据库中的值

* 测试流程：

  1. 通过数据库 fixture `db_session` 创建一条 `LiveSession`：

     * `status` 可为 `READY`
     * `video_id` 可填或不填
     * `playback_url` 直接写成 `"https://test-cdn.example.com/media/video_xxx.mp4"`
  2. 提交并刷新对象
  3. 使用 `async_client`、`auth_headers` 调用 `GET /api/v1/sessions/{session_id}`
  4. 断言：

     * `response.status_code == 200`
     * `response_json["code"] == 200`
     * `data["id"] == str(session.id)`
     * `data["playback_url"] == "https://test-cdn.example.com/media/video_xxx.mp4"`

#### 6.2.2 场景二：playback_url 为空时返回 null

**test_get_session_details_returns_null_when_playback_url_is_null**

* 前置：

  * 在数据库创建一条 `LiveSession`，`playback_url=None`
* 调用 `GET /api/v1/sessions/{session_id}`
* 断言：

  * 响应中 `data["playback_url"] is None`

#### 6.2.3 场景三：PATCH 在允许状态下更新 playback_url

**test_patch_session_updates_playback_url_when_ready**

* 前置：

  1. 在数据库中创建 `LiveSession`：

     * `status = READY` 或 `status = FINISHED`
     * `playback_url=None`
  2. 构造请求体：`{"playback_url": "https://manual.example.com/custom.mp4"}`

* 测试流程：

  1. 调用 `PATCH /api/v1/sessions/{session_id}`，携带 `auth_headers`
  2. 断言响应：

     * 状态码 `200`
     * `data["playback_url"] == "https://manual.example.com/custom.mp4"`
  3. 再次访问数据库：

     * 查询该 session
     * 断言 DB 中 `playback_url` 等于该值

#### 6.2.4 场景四：PATCH 在禁止状态下更新 playback_url

**test_patch_session_forbidden_update_playback_url_when_live**

* 前置：

  * 创建 `status = LIVE` 的 `LiveSession`，`playback_url=None`
* 调用 `PATCH /api/v1/sessions/{session_id}`，传入 `playback_url` 新值
* 断言：

  * HTTP 状态码为 400 或 403（根据业务定义）
  * 顶层结构包含 `code`、`message`、`data`、`timestamp`
  * `code` 对应业务错误码（例如权限或状态错误）
  * 确认数据库中 `playback_url` 依然为 `None`

#### 6.2.5 场景五（可选）：后台任务与 GET 集成流程

**test_post_stream_processing_and_get_session_integration**

* 前置：

  * 创建一条 `status = READY, video_id=UUID, playback_url=None` 的 session
* 执行：

  * 直接调用后台任务的接口 / 或对应 service 方法（如果可在集成测试中触发）
* 调用 GET：

  * 再次 GET 该 session
* 断言：

  * DB 中 `playback_url` 不为 None
  * GET 返回的 `data["playback_url"]` 与 DB 中一致

> ✅ 若当前项目中后台任务无法在测试中方便触发，可以只测试 Service 层（6.1 中的用例），集成测试可不包含本条。

---

## 七、错误与边界场景 (Edge Cases)

在上述测试中，需要特别关注：

1. **状态与 video_id 的组合**

   * READY + video_id + playback_url=None → 会被自动填充（Service 单元测试）
   * READY + video_id + playback_url=手动值 → 不会被覆盖
   * 非 READY 状态 → 无论 video_id 是否存在，都不会自动生成 playback_url

2. **PATCH 的权限与状态控制**

   * 注意只验证与 `playback_url` 相关的逻辑，不扩展到与本次无关的权限边界

---

## 八、测试代码风格与结构 (Style & Structure)

完全参照现有「封面上传和回放地址功能的测试代码生成提示词」中的风格要求：

1. 使用中文文档字符串与注释
2. 遵循 AAA 模式（用中文注释分隔阶段）
3. 使用 pytest + `@pytest.mark.asyncio`
4. 异步 fixture 使用模式如下：

```python
@pytest.mark.asyncio
async def test_xxx(async_client, db_session, auth_headers):
    """
    测试<功能描述>
    - <步骤1>
    - <步骤2>
    - <期望结果>
    """
    async for client in async_client:
        async for db in db_session:
            # 准备测试数据
            
            # 执行操作
            
            # 断言结果
            break
        break
```

---

## 九、最终交付清单 (Deliverables)

请根据本提示词，生成以下 **增量测试代码**：

1. **tests/unit/test_service_session.py**

   * 在文件末尾新增：

     * `test_post_stream_processing_sets_playback_url_when_ready_and_empty`
     * `test_post_stream_processing_not_override_manual_playback_url`
     * `test_post_stream_processing_skip_when_not_ready_or_no_video_id`
   * 如使用测试类，请用清晰分隔注释标明，例如：

     ```python
     # ==================== TestSessionServicePlaybackUrl ====================
     ```

2. **tests/integration/test_api_session.py**

   * 在文件末尾新增：

     * `test_get_session_details_returns_playback_url_from_db`
     * `test_get_session_details_returns_null_when_playback_url_is_null`
     * `test_patch_session_updates_playback_url_when_ready`
     * `test_patch_session_forbidden_update_playback_url_when_live`
     * （可选）`test_post_stream_processing_and_get_session_integration`

> 所有新增测试必须：
>
> * 使用现有 fixture：`async_client`, `db_session`, `auth_headers`, 以及你项目中已定义的辅助创建函数（如 create_test_room_in_db）
> * 不修改任何已有测试函数与 conftest
> * 通过所有断言并与现有测试一起运行不报错

---
