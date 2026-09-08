好的，这是一项架构风格迁移任务。

我理解您的需求是：

1.  **内容 (What)**：使用《直播核心增量设计文档 V3.3 - Tab & 留言功能》（文档 1，实用派）中的**所有功能需求、API 接口、业务逻辑和表结构**。
2.  **风格 (How)**：将上述内容强制套用在《设计文档自动生成提示词母版 V3 - 学院派》（文档 2）的**架构规范、分层、错误处理和事务模型**上。

我将执行一次**架构风格迁移**。

  * **保留的 (来自文档 1)**：所有 API 路径、JSON 响应示例、业务规则（如“普通用户不能发 URL”）、表和字段名。
  * **迁移的 (应用文档 2)**：数据库 `VARCHAR` 改为 `ENUM`、事务处理从 Service 层**迁移**到 CRUD 层、异常处理从 Service 层**迁移**到 API 层、API 实现流程**重写**为“学院派”的三层 `try/except` 模式。

-----

# LiveCore Service - 直播间 Tab & 留言功能增量设计文档 (V3.3 - 学院派架构版)

  * **版本**: 3.3（增量）
  * **状态**: 设计定稿（基于 LiveCore V3.2）
  * **架构风格**: **学院派 (Academic)** (遵循 V3 统一规范)
  * **关联文档**:
      * 《LiveCore Service - 统一核心服务设计文档 (V3.2)》
      * 《用户核心模块设计文档 (V5.0 - 权限整合版)》

-----

## 1\. 概述

本文档旨在为 LiveCore Service 增加“直播间 Tab 配置”和“直播间留言”两大功能。

## 2\. 需求背景

### 2.1 直播间 Tab 功能（管理员配置）

管理员在创建直播间后，可以为该直播间配置 0\~N 个 Tab（可选）。Tab 类型支持图文混合，用于展示「直播间简介」「医生简介」等。

### 2.2 直播间留言功能（观众 & 管理员）

所有登录用户可以在直播间页面留言。

  * **普通用户**：只允许文字 + Unicode 表情，**禁止 URL**。
  * **管理员**：允许包含 URL 在内的任意文本内容。

### 2.3 认证与权限约束

  * 所有 API 必须使用 JWT 认证。
  * 用户身份由 Access Token 提供 (`user_id = users.public_id`, `role = user_role`)。
  * Tab 管理：仅 `ADMIN` / `SUPERADMIN` 可用。
  * 留言发送：所有登录用户 (`REGULAR` 及以上)。

### 2.4 留言展示名（用户昵称）需求

为提升直播间互动体验，本次在留言功能中引入“用户展示名 (user_display_name)”能力，具体约定如下：

  * **展示名来源**：
      * 优先使用 JWT 中的 `nickname`；
      * 若无昵称，则回退为 `username`；
      * 若两者都不存在，则回退为 `email`。
  * **快照策略**：
      * 在创建留言时，从 `current_user` 中计算得到展示名字符串；
      * 将其作为快照写入 `live_room_messages.extra.user_display_name` 字段；
      * 后续即使用户在用户服务中修改昵称/用户名/邮箱，历史留言仍保持当时的展示效果。
  * **前端展示约定**：
      * 后端在单条留言创建成功响应和留言列表响应中，均通过字段 `user_display_name` 将该展示名返回给前端；
      * 前端在渲染聊天/留言列表时，**必须优先使用 `user_display_name` 字段** 显示用户名；
      * 仅当该字段为空或不存在时，才回退到“匿名用户 / 脱敏 user_id”等兜底逻辑。

## 3\. 数据流与模块说明（学院派架构）

本次新增功能的实现将严格遵循“学院派”分层架构：

1.  **API (router) 层**:
      * 负责接收 HTTP 请求，解析参数，并 `Depends` 注入 `db` 和 `current_user`。
      * **必须**提前提取日志所需变量（如 `user_id`）。
      * **必须**使用 `try...except` 块调用 Service 层。
      * **必须**捕获 Service 层和 CRUD 层上浮的自定义异常（如 `RoomNotFoundException`, `DatabaseIntegrityException`），并将其转换为标准 `JSONResponse` 错误。
2.  **Service (业务) 层**:
      * 负责所有业务逻辑（如“检查用户角色是否允许发 URL”、“检查 Tab 管理权限”）。
      * **严禁**抛出 `HTTPException`，**必须**抛出自定义 Python 异常（如 `PermissionDeniedException`）。
      * **严禁**处理数据库事务（`db.commit()` / `db.rollback()`）。
3.  **CRUD (数据) 层**:
      * 负责所有数据库原子操作。
      * **必须**在函数内部处理事务（`try/except/finally`, `db.commit()`, `db.rollback()`）。
      * **必须**捕获 `IntegrityError` 等数据库错误，记录 `logger.error`，并 `raise` 自定义的数据库异常（如 `DatabaseIntegrityException`）。

## 4\. 数据库设计（学院派规范）

### 4.1 用户 ID 与角色约定

  * 本次新增表中 `user_id` 字段存储 `users.public_id` (UUID)，通过 JWT 关联，**禁止**设置数据库外键。

### 4.2 【学院派迁移】新增 ENUM 类型

根据学院派规范，状态字段**必须**使用 PostgreSQL ENUM，禁止使用 TEXT/VARCHAR。

```sql
-- 迁移：为 live_room_messages.user_role 创建 ENUM 类型
CREATE TYPE live_room_message_user_role AS ENUM (
    'REGULAR',
    'MODERATOR',
    'ADMIN',
    'SUPERADMIN'
);

-- 迁移：为 live_room_tabs.content_type 创建 ENUM 类型
CREATE TYPE live_room_tab_content_type AS ENUM (
    'text',
    'image',
    'mixed'
);
```

### 4.3 直播间留言表 `live_room_messages`

```sql
-- 留言表
CREATE TABLE live_room_messages (
    id UUID PRIMARY KEY,
    room_id UUID NOT NULL
        REFERENCES live_rooms(id)
        ON DELETE CASCADE,
    session_id UUID NULL
        REFERENCES live_sessions(id)
        ON DELETE SET NULL,

    -- 存储 users.public_id (来自 JWT sub)
    user_id UUID NOT NULL,

    -- [学院派迁移] 字段类型从 VARCHAR(32) 迁移到 ENUM
    user_role live_room_message_user_role NOT NULL,

    content TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    extra JSONB NULL
);

-- 索引
CREATE INDEX idx_live_room_messages_room_created
    ON live_room_messages(room_id, created_at);
CREATE INDEX idx_live_room_messages_session_created
    ON live_room_messages(session_id, created_at);
COMMENT ON TABLE live_room_messages IS '直播间留言表';
```

**字段语义补充：**

  * `extra JSONB NULL`：
      * 作为可扩展字段，存放与业务强一致性无关的展示类信息；
      * 本次功能中约定其中包含键 `user_display_name`，用于保存用户展示名（昵称/用户名/邮箱）的快照，例如：
        ```json
        {
          "user_display_name": "张三医生"
        }
        ```
      * `extra` 中的内容不参与权限判断和业务决策，仅用于前端展示和审计日志的辅助信息。

### 4.4 直播间 Tab 表 `live_room_tabs`

```sql
-- Tab 配置表
CREATE TABLE live_room_tabs (
    id UUID PRIMARY KEY,
    room_id UUID NOT NULL
        REFERENCES live_rooms(id)
        ON DELETE CASCADE,

    tab_key VARCHAR(64) NOT NULL,
    title VARCHAR(128) NOT NULL,

    -- [学院派迁移] 字段类型从 VARCHAR(16) 迁移到 ENUM
    content_type live_room_tab_content_type NOT NULL,

    text_content TEXT NULL,
    image_url TEXT NULL,
    sort_order INT NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 索引
CREATE INDEX idx_live_room_tabs_room_sort
    ON live_room_tabs(room_id, sort_order);
COMMENT ON TABLE live_room_tabs IS '直播间 Tab 配置表';
```

-----

## 5\. API 设计（学院派实现）

所有 API 均继承 V3 规范：

  * **路径**: `api/v1/...` 或 `api/v1/admin/...`
  * **响应**: 统一 `JSONResponse { code, message, data, timestamp }`
  * **实现**: 严格遵循 API (Catch) -\> Service (Throw) -\> CRUD (Transaction) 模式。

### 5.1 房间详情扩展：Tabs 列表

#### 5.1.1 获取单个直播房间详情（扩展）

  * **Endpoint**: `GET /api/v1/rooms/{room_id}`
  * **功能概述**: 在原有返回结构基础上，新增 `tabs` 数组字段。
  * **成功响应 (节选)**:
    ```json
    {
      "code": 200,
      "message": "success",
      "data": {
        "id": "room_uuid",
        "title": "新产品发布会直播",
        "tabs": [
          {
            "id": "tab_uuid_1",
            "tab_key": "room",
            "title": "直播间简介",
            "content_type": "text",
            /* ... 其他字段 ... */
          }
        ]
      },
      "timestamp": "2025-07-07T19:15:00Z"
    }
    ```
  * **【学院派】实现流程描述**:
    1.  `(API 层)`: 接收 `room_id`，注入 `db`。
    2.  `(API 层)`: `try...except` 块启动。
    3.  `(API 层)`: 调用 `service.get_room_details(db, room_id)`。
    4.  `(Service 层)`: 调用 `crud.rooms.get(db, room_id)`。若 `None`，`raise RoomNotFoundException`。
    5.  `(Service 层)`: 调用 `crud.tabs.get_active_by_room_id(db, room_id)`。
    6.  `(Service 层)`: 组合 `room` 和 `tabs` 数据并返回。
    7.  `(API 层)`: (`try` 块内) 返回 `success_response(data=...)`。
    8.  `(API 层)`: `except RoomNotFoundException as e:` -\> `logger.warning(...)` 并返回 404/2001 `JSONResponse`。
    9.  `(API 层)`: `except Exception as e:` -\> `logger.error(...)` 并返回 500/1xxx `JSONResponse`。

-----

### 5.2 Tab 管理 API（Admin Only）

#### 5.2.1 查询直播间 Tab 列表（后台管理）

  * **Endpoint**: `GET /api/v1/admin/rooms/{room_id}/tabs`
  * **权限**: `role ∈ {ADMIN, SUPERADMIN}`
  * **成功响应**: (内容同 V3.3 文档)
  * **【学院派】实现流程描述**:
    1.  `(API 层)`: 注入 `db` 和 `current_user`。
    2.  `(API 层)`: `try...except` 块启动。
    3.  `(API 层)`: 实例化 `service = TabService(db)`。
    4.  `(API 层)`: 调用 `await service.list_tabs_for_admin(user=current_user, room_id=room_id)`。
    5.  `(Service 层)`: 检查 `user.role`。若权限不足，`raise PermissionDeniedException`。
    6.  `(Service 层)`: 调用 `crud.tabs.get_all_by_room_id(...)` 并返回。
    7.  `(API 层)`: (`try` 块内) 返回 `success_response(data=...)`。
    8.  `(API 层)`: `except PermissionDeniedException as e:` -\> `logger.warning(...)` 并返回 403/3002 `JSONResponse`。

#### 5.2.2 创建 Tab

  * **Endpoint**: `POST /api/v1/admin/rooms/{room_id}/tabs`
  * **权限**: `role ∈ {ADMIN, SUPERADMIN}`
  * **请求体**: (内容同 V3.3 文档)
  * **失败响应 (示例：参数错误)**:
    ```json
    {
      "code": 4001,
      "message": "参数校验失败",
      "data": { "error": "当 content_type=text 时, text_content 不能为空" },
      "timestamp": "2025-07-08T12:10:00Z"
    }
    ```
  * **【学院派】实现流程描述**:
    1.  `(API 层)`: 注入 `db`, `current_user`。
    2.  `(API 层)`: **(安全规范)** 提取日志变量 `user_id = current_user.public_id`。
    3.  `(API 层)`: `try...except` 块启动。
    4.  `(API 层)`: 实例化 `service = TabService(db)`。
    5.  `(API 层)`: 调用 `await service.create_tab(user=current_user, room_id=room_id, tab_in=payload)`。
    6.  `(Service 层)`: 检查 `user.role` 权限，失败则 `raise PermissionDeniedException`。
    7.  `(Service 层)`: 检查 `room_id` 是否存在 (调用 `crud.rooms.get`)，失败则 `raise RoomNotFoundException`。
    8.  `(Service 层)`: 校验 `content_type` 逻辑，失败则 `raise InvalidParameterException("content_type 校验失败...")`。
    9.  `(Service 层)`: 调用 `await crud.tabs.create(db, obj_in=...)`。
    10. `(CRUD 层)`: **(学院派核心)**
          * `try:`
          * `db.add(db_obj)`
          * `await db.commit()`
          * `await db.refresh(db_obj)`
          * `return db_obj`
          * `except IntegrityError as e:`
          * `await db.rollback()`
          * `logger.error(f"创建 Tab 失败: {e}", exc_info=True)`
          * `raise DatabaseIntegrityException("数据库完整性冲突")`
    11. `(API 层)`: (`try` 块内) 返回 `success_response(data=...)`。
    12. `(API 层)`: `except PermissionDeniedException as e:` -\> 403/3002 `JSONResponse`。
    13. `(API 层)`: `except RoomNotFoundException as e:` -\> 404/2001 `JSONResponse`。
    14. `(API 层)`: `except InvalidParameterException as e:` -\> 400/4001 `JSONResponse`。
    15. `(API 层)`: `except DatabaseIntegrityException as e:` -\> 400/4001 `JSONResponse` (或 500)。

#### 5.2.3 更新 Tab

  * **Endpoint**: `PATCH /api/v1/admin/tabs/{tab_id}`
  * **权限**: `role ∈ {ADMIN, SUPERADMIN}`

#### 5.2.4 删除 Tab

  * **Endpoint**: `DELETE /api/v1/admin/tabs/{tab_id}`
  * **权限**: `role ∈ {ADMIN, SUPERADMIN}`

-----

### 5.3 留言 API（观众 & 管理员）

#### 5.3.1 发送留言

  * **Endpoint**: `POST /api/v1/rooms/{room_id}/messages`
  * **权限**: `REGULAR` 及以上
  * **请求体**: `{"content": "医生讲得很好 👍"}`
  * **成功响应 (节选)**:
    ```json
    {
      "code": 200,
      "message": "success",
      "data": {
        "id": "message_uuid",
        "room_id": "room_uuid",
        "session_id": null,
        "user_id": "user_public_id",
        "user_role": "REGULAR",
        "content": "医生讲得很好 👍",
        "created_at": "2025-07-08T12:10:00Z",
        "user_display_name": "张三医生"
      },
      "timestamp": "2025-07-08T12:10:00Z"
    }
    ```
  * **失败响应 (普通用户发送 URL)**:
    ```json
    {
      "code": 4004,
      "message": "参数校验失败",
      "data": {
        "field": "content",
        "error": "普通用户不允许发送包含 URL 的留言"
      },
      "timestamp": "2025-07-08T12:10:00Z"
    }
    ```
  * **【学院派】实现流程描述**:
    1.  `(API 层)`: 注入 `db`, `current_user`。
    2.  `(API 层)`: **(安全规范)** 提取日志变量 `user_id = current_user.public_id`, `user_role = current_user.role`，并计算展示名：
        `user_display_name = current_user.nickname or current_user.username or current_user.email`。
    3.  `(API 层)`: `try...except` 块启动。
    4.  `(API 层)`: 实例化 `service = MessageService(db)`。
    5.  `(API 层)`: 调用 `await service.create_message(user_id=user_id, user_role=user_role, room_id=room_id, content=payload.content, user_display_name=user_display_name, ...)`，将展示名一并传入 Service 层。
    6.  `(Service 层)`: 检查 `room_id` 是否存在，失败则 `raise RoomNotFoundException`。
    7.  `(Service 层)`: **(业务逻辑)** 检查 `content` 长度，失败则 `raise InvalidParameterException("内容过长")`。
    8.  `(Service 层)`: **(业务逻辑)** 检查 `user_role` 和 `content` 中的 URL。如果 `role == 'REGULAR'` 且包含 URL，`raise InvalidParameterException("普通用户不允许发送包含 URL 的留言", code=4004)`。
    9.  `(Service 层)`: 在构造内部创建模型 `LiveRoomMessageCreateInternal` 时，将 `user_display_name` 写入 `extra` 字段（形如 `{"user_display_name": "张三医生"}`），并通过 CRUD 层持久化到 `live_room_messages.extra`。
    10. `(Service 层)`: 调用 `await crud.messages.create(...)` (CRUD 层负责事务)。
    11. `(API 层)`: (`try` 块内) 将 ORM 对象映射为响应模型，若 `extra.user_display_name` 存在，则填充响应中的 `user_display_name` 字段，并返回 `success_response(data=...)`。
    12. `(API 层)`: `except RoomNotFoundException as e:` -\> 404/2001 `JSONResponse`。
    13. `(API 层)`: `except InvalidParameterException as e:` -\> 400/`e.code` (4004) `JSONResponse`。
    14. `(API 层)`: `except DatabaseIntegrityException as e:` -\> 400/4001 `JSONResponse`。
    15. `(API 层)`: `except Exception as e:` -\> 500/1xxx `JSONResponse`。

#### 5.3.2 获取留言列表（按直播间）

  * **Endpoint**: `GET /api/v1/rooms/{room_id}/messages`
  * **权限**: `REGULAR` 及以上
  * **Query**: `page`, `size`, `since`
  * **响应扩展**：
      * 留言列表中每条记录在原有字段基础上新增可选字段 `user_display_name`，用于直接展示用户昵称/用户名/邮箱快照；
      * 对于历史数据（创建时未写入 `extra.user_display_name` 的留言），该字段返回 `null`，前端可回退到“匿名用户 / 脱敏 user_id”逻辑。
  * **【学院派】实现流程扩展**：
      1. `(Service 层)`: 保持原有分页查询逻辑不变，返回 ORM 模型列表 `messages`，其中 `extra` 字段可能包含 `user_display_name`。
      2. `(API 层)`: 在将每条 ORM 记录映射为 `LiveRoomMessageListResponseItem` 时：
          * 若 `msg.extra` 为字典且包含 `user_display_name`，则通过 `model_copy(update={"user_display_name": display_name})` 写入响应 DTO；
          * 否则保持 `user_display_name = null`。

-----

## 6\. 认证与权限

  * 所有 API 必须登录。
  * Tab 管理 API (`/api/v1/admin/...`) **必须**在 **Service 层** 检查 `current_user.role` 是否为 `ADMIN` 或 `SUPERADMIN`。
  * 留言 API (`/api/v1/rooms/.../messages`) **必须**在 **Service 层** 检查 `current_user.role` 以决定是否执行 URL 过滤。
  * 所有权限不足的检查，**Service 层** 均 `raise PermissionDeniedException`。

## 7\. 日志与异常（学院派规范）

### 7.1 日志规范

  * `INFO`：关键业务动作（`logger.info("留言发送成功...")`）。
  * `WARNING`：**API 层**捕获到**业务异常**时（`except PermissionDeniedException:` -\> `logger.warning("权限不足...")`）。
  * `ERROR`：**CRUD 层**捕获到**数据库异常**时（`except IntegrityError:` -\> `logger.error(..., exc_info=True)`）。

### 7.2 异常处理流程

1.  **CRUD 层**:
    ```python
    # crud/messages.py
    async def create(db: AsyncSession, ...):
        # (安全规范) 提前提取日志变量
        user_id_log = obj_in.user_id 
        try:
            db_obj = Model(...)
            db.add(db_obj)
            await db.commit()
            return db_obj
        except IntegrityError as e:
            await db.rollback()
            logger.error(f"创建留言DB失败: user_id={user_id_log}, error={e}", exc_info=True)
            raise DatabaseIntegrityException("留言创建失败")
        except Exception as e:
            await db.rollback()
            logger.error(f"创建留言未知DB失败: user_id={user_id_log}, error={e}", exc_info=True)
            raise DatabaseOperationException("数据库操作失败")
    ```
2.  **Service 层**:
    ```python
    # services/messages.py
    async def create_message(self, user_id, user_role, content, user_display_name: Optional[str] = None, ...):
        if user_role == 'REGULAR' and 'http' in content:
            # 严禁 HTTPExcepion，必须 raise 自定义异常
            raise InvalidParameterException(code=4004, message="普通用户不允许发送包含 URL 的留言")
        
        # 将 user_display_name 写入内部 DTO 的 extra 字段（例如 {"user_display_name": user_display_name}），由 CRUD 层持久化到 live_room_messages.extra
        # Service 层不捕获 CRUD 的异常，任其上浮
        db_message = await self.crud.create(db=self.db, ...)
        return db_message
    ```
3.  **API (router) 层**:
    ```python
    # routers/messages.py
    @router.post(...)
    async def create_message(..., current_user: ...):
        # (安全规范) 提前提取日志变量
        user_id_log = current_user.public_id
        try:
            service = MessageService(db)
            msg = await service.create_message(...)
            return success_response(data=msg)
        
        # 捕获 Service 层的业务异常
        except InvalidParameterException as e:
            logger.warning(f"参数错误: user_id={user_id_log}, error={e.message}")
            return JSONResponse(status_code=400, content=error_response(code=e.code, message=e.message))
        
        # 捕获 Service 层的权限异常
        except PermissionDeniedException as e:
            logger.warning(f"权限不足: user_id={user_id_log}")
            return JSONResponse(status_code=403, content=error_response(code=3002, message="权限不足"))
            
        # 捕获 CRUD 层的数据库异常
        except DatabaseIntegrityException as e:
            logger.warning(f"数据冲突: user_id={user_id_log}, error={e.message}")
            return JSONResponse(status_code=400, content=error_response(code=4001, message="数据冲突或参数错误"))
            
        # 捕获所有其他异常
        except Exception as e:
            logger.error(f"未知错误: user_id={user_id_log}, error={e}", exc_info=True)
            return JSONResponse(status_code=500, content=error_response(code=1000, message="服务器内部错误"))
    ```

## 8\. 安全规范

  * **JWT & 角色安全**：已在 Service 层强制校验。
  * **XSS / 内容安全**：`content` 字段前端必须转义。`content` URL 限制已在 Service 层实现。
  * **安全异步异常处理**：已在 API 层和 CRUD 层的 `try...except` 流程中强制执行（如日志变量 `user_id_log` 在 `try` 块之前提取）。
  * **展示名安全**：留言展示名 `user_display_name` 仅从已验证的 JWT 中的 `nickname`/`username`/`email` 组合得到，用于展示与审计；不参与权限控制与核心业务决策，也不作为用户存在性的唯一依据。

## 9\. 兼容性说明

  * **数据库**：完全新增表，未修改任何现有表结构。
  * **API**：完全新增 API，仅对 `GET /api/v1/rooms/{room_id}` 增量添加 `tabs` 字段，旧前端可忽略，完全后向兼容。