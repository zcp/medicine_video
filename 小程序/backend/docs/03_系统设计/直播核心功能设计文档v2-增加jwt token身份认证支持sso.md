-----

# LiveCore Service - 统一核心服务设计文档 (V3.2)

  * **版本**: 3.2 (最终版)
  * **状态**: 设计定稿
  * **设计日期**: 2025-07-07

当然可以。将这些分散的规范整合到一个逻辑清晰的结构中，可以极大地提高文档的可读性和实用性。

下面是为您合并和整理后的开发规范内容，您可以将其作为一个独立的章节放入您的主设计文档中。

---

## **开发规范**

### **1. 编码与项目规范**

#### **1.1 代码规范**
* 遵循 `rules.md` 中定义的团队代码规范。
* **开发语言**: 使用 Python 3.8 或更高版本。
* **代码风格**: 严格遵循 PEP 8 规范。
* **格式化**:
    * 使用 4 个空格作为缩进。
    * 所有代码文件必须使用 UTF-8 编码。

#### **1.2 命名规范**
* 遵循 `开发规范文档` 中定义的统一命名规范。
* **类名 (Class)**: 使用大驼峰命名法 (PascalCase)，例如 `LiveRoom`。
* **函数与方法 (Function/Method)**: 使用下划线命名法 (snake\_case)，例如 `get_room_details`。
* **变量 (Variable)**: 使用下划线命名法 (snake\_case)，例如 `session_id`。
* **常量 (Constant)**: 使用全大写下划线命名法 (UPPER\_SNAKE\_CASE)，例如 `MAX_CONNECTIONS`。

#### **1.3 项目结构规范**
* 遵循 `开发规范文档` 中定义的后端项目结构规范。
* **设计原则**: 采用模块化设计，确保各功能模块职责单一、高内聚、低耦合。
* **目录结构**: 保持清晰、可预测的目录结构，便于团队成员快速定位代码。

#### **1.4 测试规范**
* 遵循 `测试规范文档` 中定义的统一测试规范。
* **单元测试**: 核心业务逻辑的单元测试覆盖率必须大于 80%。
* **接口测试**: 所有公开 API 接口都必须有完整的测试用例覆盖。
* **性能测试**: 核心接口和高并发场景需通过性能测试，确保达到设计指标。

### **2. 日志与异常处理规范**

#### **2.1 日志规范**

##### **2.1.1 日志级别**
* `ERROR`: 关键系统错误、导致业务失败的异常。必须立即关注。
* `WARNING`: 潜在的问题或警告信息，不影响当前流程但需关注。
* `INFO`: 记录重要的业务操作节点，如用户登录、创建直播间等。
* `DEBUG`: 用于开发和调试阶段，记录详细的程序运行信息。

##### **2.1.2 日志格式**
每一条日志记录都应包含以下标准字段：
* 时间戳 (ISO 8601 格式)
* 日志级别 (如: INFO)
* 模块名 (如: `routers.rooms`)
* 函数名
* 行号
* 消息内容
* 异常堆栈 (仅在记录异常时包含)

##### **2.1.3 日志内容**
应记录但不限于以下关键信息：
* 系统启动与关闭事件。
* 用户认证操作（登录/登出），需注意脱敏。
* 核心业务操作的入口和结果（如创建/更新/删除房间）。
* 所有捕获到的异常信息。
* 关键性能监控数据（如 API 耗时）。

##### **2.1.4 日志管理与存储**
* **集中管理**: 使用 ELK Stack (Elasticsearch, Logstash, Kibana) 进行日志的统一收集、存储和查询。
* **存储策略**:
    * 日志文件按日期进行分割和归档。
    * 对用户密码、密钥等所有敏感信息必须进行脱敏处理。

#### **2.2 异常处理规范**

##### **2.2.1 异常分类**
* **系统异常**: 系统级错误（如数据库连接失败、中间件故障）。
* **业务异常**: 不符合业务规则的正常操作（如余额不足、库存不够）。
* **参数异常**: 用户输入参数不符合格式或校验规则。
* **权限异常**: 用户无权访问特定资源或执行特定操作。

##### **2.2.2 异常处理原则**
* **统一处理**: 实现统一的异常处理中间件 (Exception Handling Middleware) 来捕获所有未处理的异常，避免程序崩溃。
* **明确类型**: 使用自定义的、继承自 `Exception` 的异常类来区分不同的异常情况。
* **详细日志**: 捕获到任何异常时，都必须记录详细的错误日志，包含完整的异常堆栈。
* **格式统一**: 返回给客户端的错误响应必须遵循 `2.1. 通用响应结构` 的格式：    
比如：
{
  "code": 2003,
  "message": "操作被禁止",
  "data": {
    "resource_id": "room_uuid_123",
    "current_status": "live",
    "reason": "无法删除正在直播的房间"
  },
  "timestamp": "2025-07-08T14:40:00Z"
}


* **避免吞没**: 严禁捕获异常后不做任何处理（`except: pass`）。
* **优雅降级**: 在可能的情况下，对系统异常进行优雅降级处理，保证核心功能的可用性。

##### **2.2.3 异常处理流程**
1.  在业务代码中**捕获**可预见的异常。
2.  将原始异常**记录**到日志系统。
3.  将原始异常**转换**为对应的自定义业务异常类型。
4.  由统一的异常处理中间件捕获所有异常，并**返回**统一格式的错误响应。
5.  在必要时（如文件句柄、数据库连接），使用 `finally` 块**清理**资源。


## 3\. 概述

### 3.1. 文档目的

本文档旨在详细定义 **核心直播服务 (LiveCore Service)** 的技术架构、数据库设计、API 接口规范、存储约定及开发实施计划。它将作为项目开发、测试和后续维护的统一依据。
这个文档中的数据库设计支持多会场直播，并支持专题扩展。

### 3.2. 项目背景与架构决策

为快速、稳定地实现直播业务的核心功能，本项目初期将采用**统一服务架构**，将房间管理、直播生命周期、统计等功能内聚于单个 FastAPI 应用中。数据库设计采用**双表核心模型**，将持久化的“直播房间”(`live_rooms`)与瞬时的“直播场次”(`live_sessions`)进行分离，以确保系统的长期可扩展性和数据结构的清晰性。

## 4\. 通用 API 规范

### 4.1. 通用响应结构

所有公开 API 接口的响应都将遵循以下统一结构，以确保前端和客户端能够进行标准化处理。

| 字段名      | 类型     | 说明                                     |
| :---------- | :------- | :--------------------------------------- |
| `code`      | `int`    | 业务状态码（200 表示成功，非 200 表示各类错误） |
| `message`   | `string` | 对本次请求结果的简要说明，如 "success" 或 "参数错误"。 |
| `data`      | `object` | 实际返回的核心数据内容。成功时为业务数据对象，失败时可为 `null` 或包含详细错误信息的对象。 |
| `timestamp` | `string` | 服务器生成响应的时间戳，采用 ISO 8601 格式。 |
比如：
{
  "code": 2003,
  "message": "操作被禁止",
  "data": {
    "resource_id": "room_uuid_123",
    "current_status": "live",
    "reason": "无法删除正在直播的房间"
  },
  "timestamp": "2025-07-08T14:40:00Z"
}

### 4.2. 状态码约定

#### 4.2.1. HTTP 状态码

HTTP 状态码用于反映网络层面的请求结果。

| HTTP 状态码 | 说明             |
| :---------- | :--------------- |
| `200`       | 请求成功         |
| `400`       | 客户端请求错误   |
| `401`       | 未授权           |
| `403`       | 禁止访问         |
| `404`       | 资源或路径不存在 |
| `500`       | 服务器内部错误   |

#### 4.2.2. 业务状态码 (`code` 字段)

业务状态码用于精确表示业务逻辑的处理结果。

| 业务状态码 | 含义             |
| :--------- | :--------------- |
| `200`      | 成功             |
| `1xxx`     | 系统级错误       |
| `2xxx`     | 业务逻辑错误     |
| `3xxx`     | 权限或认证错误   |
| `4xxx`     | 参数校验错误     |

### 4.3. 分页格式约定

#### 4.3.1. 分页请求参数

分页查询将通过 URL 的 Query 参数进行控制。

| 参数名 | 类型     | 描述                                     |
| :----- | :------- | :--------------------------------------- |
| `page` | `int`    | 请求的页码，从 1 开始，默认为 1。        |
| `size` | `int`    | 每页返回的数据条数，默认为 10，最大为 100。 |
| `sort` | `string` | 排序字段及顺序，格式为 `field:direction`，例如 `created_at:desc`。 |

#### 4.3.2. 分页响应格式

分页查询成功时，`data` 字段将采用以下结构。

```json
{
  "total": 100,
  "page": 1,
  "size": 10,
  "items": [
    { "...": "..." }
  ]
}
```

-----

*文档的其余部分将遵循以上规范。*

## 5\. 技术栈

| 分类               | 技术选型            | 用途说明                                                                                                                                                                                                                        |
|:-----------------|:----------------|:----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **服务端框架**        | FastAPI         | 构建高性能、异步的 RESTful API。                                                                                                                                                                                                      |
| **ORM**          | SQLAlchemy (异步) | 与 PostgreSQL 数据库进行交互，管理数据模型。                                                                                                                                                                                                |
| **数据模型**         | Pydantic        | 定义 API 的数据结构、请求体验证和响应序列化。                                                                                                                                                                                                   |
| **数据库**          | PostgreSQL      | 持久化存储直播房间、场次、统计等核心数据。                                                                                                                                                                                                       |
| **媒体服务器**        | SRS             | 接收 RTMP 推流，生成 HLS 流，并通过 HTTP 回调通知后端。                                                                                                                                                                                        |
| **Web 服务器**      | Nginx           | 作为反向代理、SSL 终止、负载均衡和静态资源服务。                                                                                                                                                                                                  |
| **前端播放器**        | Video.js        | 在网页端嵌入，用于播放 SRS 生成的 HLS 直播流。                                                                                                                                                                                                |
| **后台任务队列**       | celery          | 执行耗时的后台异步任务，以避免主应用（FastAPI）在处理长时间操作时被阻塞。主要用于直播结束后，在 on_unpublish 回调触发下，处理视频转码、生成封面、数据归档等任务。通过独立的 Worker 进程，实现任务处理的解耦与水平扩展。                                                                                                  |
| **消息中间件 / 缓存**   | Redis           | 主要职责：作为 Celery 的消息中间件（Broker），负责高效、可靠地存储和分发从主应用发布的后台任务消息。                                                                                                                                                                   |
| **协程/并发库**   |gevent          | 作为 Celery 的执行池（Execution Pool），使其 Worker 能够原生、高并发地执行 async def 异步任务。这统一了整个项目的异步技术模型，并提供了卓越的 I/O 并发性能。                                                                                                                       |
| **身份认证**          | JWT             | 实现无状态的用户身份认证，支持SSO登录，确保API访问安全。            

## 6\. 系统架构

### 6.1. 架构图

```mermaid
graph TD
    subgraph "外部用户/设备"
        Client[客户端/浏览器]
        Pusher[推流端 (FFmpeg/OBS)]
    end

    subgraph "公网入口"
        Nginx[Nginx 网关 <br> (HTTPS, 反向代理)]
    end

    subgraph "内部网络"
        SRS[SRS 媒体服务器]
        LiveCoreSvc[LiveCore Service (FastAPI)]
        AuthService[认证服务 <br> (JWT验证)]
        DB[(PostgreSQL 数据库)]
    end

    Client -- "HTTPS (API/HLS)" --> Nginx
    Pusher -- "RTMP/SRT" --> SRS

    Nginx -- "HTTP 代理 (/api/...)" --> LiveCoreSvc
    Nginx -- "HTTP 代理 (/live/...)" --> SRS

    LiveCoreSvc -- "JWT验证" --> AuthService
    SRS -- "内部 HTTP 回调" --> LiveCoreSvc
    LiveCoreSvc -- "内部 HTTP API (统计)" --> SRS
    LiveCoreSvc -- "SQL" --> DB
```

### 6.2. 组件职责

  * **Nginx 网关**: 系统的唯一公网入口，负责反向代理所有 API 和 HLS 请求到对应的后端服务，并处理 HTTPS。
  * **SRS 媒体服务器**: 专业的媒体处理核心，负责接收推流、生成 HLS 流，并通过 HTTP 回调与 LiveCore Service 实时同步直播事件。
  * **LiveCore Service (FastAPI)**: 系统的“大脑”，负责处理所有业务逻辑。
  * **PostgreSQL 数据库**: 系统的持久化存储中心。

## 7\. 数据库设计

### 7.1. 设计原则

  * **双表模型**: `live_rooms` (配置) 与 `live_sessions` (事件) 分离。
  * **UUID 主键**: 所有表主键使用 `UUID`，保证全局唯一性。
  * **时区兼容**: 所有时间戳使用 `TIMESTAMPTZ`，以 UTC 存储。
  * **数据完整性**: 使用 `UNIQUE`, `ENUM` 保证数据准确，`user_id` 通过JWT Token应用层验证保证引用完整性。
### 7.2. Schema DDL (最终版)

```sql
-- LiveCore Service - 完整数据库 Schema (V3.2)


CREATE TYPE live_session_status AS ENUM (
    'scheduled',    -- [新增] 已计划，待开播
    'live', 'finished', 'processing', 'ready', 'error'
);

-- 表 1: live_rooms (持久化容器)
CREATE TABLE live_rooms (
 -- 核心标识 (在应用层通过 uuid.uuid4() 生成)
    id UUID PRIMARY KEY,
    
    -- 用户ID，通过JWT Token应用层验证保证引用完整性
    -- 由于采用微服务架构，user_id无法跨数据库外键关联，通过JWT Token验证用户存在性
    user_id UUID NOT NULL,
   
    -- 【新增】自引用外键，用于实现“主会场-分会场”结构
    parent_room_id UUID NULL REFERENCES live_rooms(id) ON DELETE SET NULL,

    title VARCHAR(100) NOT NULL,
    description TEXT,
    cover_url VARCHAR(255),
    stream_key VARCHAR(255) NOT NULL UNIQUE,
    is_private BOOLEAN DEFAULT false,
    record_by_default BOOLEAN DEFAULT true,

    -- 分类信息
    category_id UUID NULL, -- [待办] 初期允许为空。未来在分类模块实现后，应添加 FOREIGN KEY REFERENCES categories(id)。
 
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP

);
CREATE INDEX idx_live_rooms_user_id ON live_rooms(user_id);
COMMENT ON TABLE live_rooms IS '直播房间表，存储可复用的持久化信息和推流密钥。';

-- 表 2: live_sessions (瞬时事件)
CREATE TABLE live_sessions (

    -- 核心标识 (在应用层通过 uuid.uuid4() 生成)
    id UUID PRIMARY KEY,

    room_id UUID NOT NULL REFERENCES live_rooms(id) ON DELETE CASCADE,

    -- 【核心修改】status 不再有默认值，由应用层在创建时明确指定
    status live_session_status NOT NULL,

    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ,

-- 【为未来扩展预留的字段】
    video_id UUID NULL UNIQUE, -- [待办] 用于关联到未来的 VOD 媒资表 (videos)。当前阶段可不使用，在回放功能开发时启用。

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE live_sessions IS '直播场次表，记录每一次具体的直播事件及其生命周期。';

-- 表 3: session_statistics (场次统计)
CREATE TABLE session_statistics (
   -- 核心标识 (在应用层通过 uuid.uuid4() 生成)
    id UUID PRIMARY KEY,

    session_id UUID NOT NULL UNIQUE REFERENCES live_sessions(id) ON DELETE CASCADE,
    peak_viewer_count INT DEFAULT 0,
    total_viewer_count BIGINT DEFAULT 0,
    total_like_count BIGINT DEFAULT 0,
    total_share_count BIGINT DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE session_statistics IS '单场直播的统计数据表，与 live_sessions 表一一对应。';

-- 索引
CREATE INDEX idx_live_rooms_on_user_id ON live_rooms(user_id);
CREATE INDEX idx_live_sessions_on_room_id ON live_sessions(room_id);
CREATE INDEX idx_live_sessions_on_status ON live_sessions(status);
CREATE INDEX idx_live_sessions_on_video_id ON live_sessions(video_id);
```

## 8\. API 接口规范


##### **资源: 直播房间 (`live_rooms`) 与分会场**
| 主要功能 | HTTP 方法 | API 端点 | 简要说明 |
| :--- | :--- | :--- | :--- |
| **创建主会场/分会场** | `POST` | `/api/v1/rooms` | 创建一个新的直播房间。请求体中若包含 `parent_room_id`，则创建的是分会场。 |
| **获取房间列表** | `GET` | `/api/v1/rooms` | 分页获取所有直播房间。可通过 Query 参数筛选主会场 (`level=main`)。 |
| **获取房间详情** | `GET` | `/api/v1/rooms/{room_id}` | 获取指定 ID 的房间（无论主次）的详细、持久化信息。 |
| **更新房间信息** | `PATCH` | `/api/v1/rooms/{room_id}` | 更新指定 ID 的房间（无论主次）的标题、描述等信息。不能在直播中更新。 |
| **删除房间** | `DELETE` | `/api/v1/rooms/{room_id}` | 删除指定 ID 的房间（无论主次）。不能在直播中删除。 |
| **获取分会场列表** | `GET` | `/api/v1/rooms/{room_id}/sub-venues` | 分页获取指定主会场下的所有直属分会场列表，并包含其实时状态。 |

##### **资源: 直播场次 (`live_sessions`)**
| 主要功能 | HTTP 方法 | API 端点 | 简要说明 |
| :--- | :--- | :--- | :--- |
| **创建计划场次** | `POST` | `/api/v1/rooms/{room_id}/sessions` | 为指定房间预先创建一个“计划中”(`scheduled`)的直播场次。 |
| **获取场次列表** | `GET` | `/api/v1/rooms/{room_id}/sessions` | 分页获取指定房间的所有历史和计划直播场次。 |
| **获取场次详情** | `GET` | `/api/v1/sessions/{session_id}` | 获取单场直播的详细信息，包含其实时状态和统计数据。**这是判断是否在直播的核心接口。** |
| **更新计划场次** | `PATCH` | `/api/v1/sessions/{session_id}` | 更新一个还未开始的计划场次的信息，如修改预告时间、标题等。 |
| **删除计划场次** | `DELETE` | `/api/v1/sessions/{session_id}` | 删除一个还未开始或已结束的直播场次。不能删除正在直播的场次。 |

---

#### **2. 内部 API (Internal APIs)**

| 主要功能 | HTTP 方法 | API 端点 | 简要说明 |
| :--- | :--- | :--- | :--- |
| **推流鉴权与激活** | `POST` | `/internal/srs/on_publish` | 由 SRS 服务器在收到推流时回调。用于验证 `stream_key`，并将 `scheduled` 状态的场次激活为 `live`，或为即兴直播创建新的 `live` 场次。 |
| **断流处理** | `POST` | `/internal/srs/on_unpublish` | 由 SRS 服务器在推流断开时回调。用于将 `live` 状态的场次更新为 `finished`，并触发后续处理（如转码）。 |

### 6.1. 公开 API (Public APIs)

**认证要求**: 所有以下API接口都需要JWT Token认证，请求头必须包含 `Authorization: Bearer <JWT_TOKEN>`

#### **资源: 直播房间 (`live_rooms`)**

##### **1. 创建直播房间**
* **Endpoint**: `POST /api/v1/rooms`
* **认证**: 需要JWT Token认证
* **权限**: 用户只能为自己创建直播房间
* **请求体** (`application/json`):
  ```json
  {
    "title": "新产品发布会直播",
    "description": "介绍我们即将发布的 v3.0 版本。",
    "record_by_default": true
  }
  ```
* **实现流程描述**:
  1. 验证JWT Token，提取用户ID
  2. 定义 FastAPI 路由函数，接收 Pydantic 模型 `RoomCreate` 和数据库会话 `db`
  3. 调用 `secrets.token_hex()` 生成唯一的 `stream_key`
  4. 创建 models.LiveRoom 实例，**设置 `user_id` 为当前认证用户ID (来自已验证的JWT Token）**
  5. 通过 `db.add()`, `db.commit()`, `db.refresh()` 将新房间持久化到数据库
  6. 构建并返回符合通用结构的成功响应
  

#### **资源: 直播房间 (`live_rooms`)**
好的，您提的要求非常合理，一个完整的设计文档确实应该包含所有接口的详细规范。我将为您补全 `live_rooms` 资源剩余的 `GET`, `PATCH`, 和 `DELETE` 接口，并确保它们的定义、响应结构和实现流程描述都与其他接口保持严格一致。

-----

##### **1. 创建直播房间**

  * **Endpoint**: `POST /api/v1/rooms`
  * **功能描述**: 创建一个新的、可复用的直播房间，并生成唯一的推流密钥。
  * **请求体** (`application/json`):
    ```json
    {
      "title": "新产品发布会直播",
      "description": "介绍我们即将发布的 v3.0 版本。",
      "record_by_default": true
    }
    ```
  * **成功响应** (`200 OK`):
    ```json
    {
      "code": 200,
      "message": "success",
      "data": {
        "id": "a1b2c3d4-e5f6-4a1b-8c3d-e5f6a1b2c3d4",
        "title": "新产品发布会直播",
        "description": "介绍我们即将发布的 v3.0 版本。",
        "stream_key": "example_stream_key_placeholder",
        "record_by_default": true,
        "created_at": "2025-07-07T19:10:00Z"
      },
      "timestamp": "2025-07-07T19:10:00Z"
    }
    ```
  * **实现流程描述**:
    1.  定义 FastAPI 路由函数，接收 Pydantic 模型 `RoomCreate` 和数据库会话 `db`。
    2.  调用 `secrets.token_hex()` 生成唯一的 `stream_key`。
    3.  创建 models.LiveRoom 实例: 仅创建房间对象，填充 title, description 等从请求中获取的信息。
    4.  通过 `db.add()`, `db.commit()`, `db.refresh()` 将新房间持久化到数据库。
    5.  构建并返回符合通用结构的成功响应。

-----

##### **2. 获取直播房间列表**

  * **Endpoint**: `GET /api/v1/rooms`
  * **功能描述**: 分页获取所有已创建的直播房间列表。
  * **请求参数 (Query)**: `page`, `size`, `sort`
  * **成功响应** (`200 OK`):
    ```json
    {
      "code": 200,
      "message": "success",
      "data": {
        "total": 50,
        "page": 1,
        "size": 10,
        "items": [
          {
            "id": "a1b2c3d4-e5f6-4a1b-8c3d-e5f6a1b2c3d4",
            "title": "新产品发布会直播",
            "cover_url": "https://example.com/cover.jpg",
            "created_at": "2025-07-07T19:10:00Z"
          }
        ]
      },
      "timestamp": "2025-07-07T19:12:00Z"
    }
    ```
  * **实现流程描述**:
    1.  定义 FastAPI 路由函数，注入分页参数对象 `PaginationParams` 和数据库会话 `db`。
    2.  构建基础的 `select(models.LiveRoom)` 查询。
    3.  根据 `PaginationParams` 中的可选参数（如筛选条件）修改查询。
    4.  执行 `count()` 查询获取总数。
    5.  应用排序和分页（`order_by`, `offset`, `limit`）到查询上。
    6.  执行最终查询获取当页的 `items`。
    7.  构建并返回符合分页规范的成功响应。

-----

##### **3. 获取单个直播房间详情**

  * **Endpoint**: `GET /api/v1/rooms/{room_id}`
  * **功能描述**: 获取指定 `room_id` 的直播房间的永久性信息（不包含实时的直播状态）。
  * **成功响应** (`200 OK`):
    ```json
    {
      "code": 200,
      "message": "success",
      "data": {
        "id": "a1b2c3d4-e5f6-4a1b-8c3d-e5f6a1b2c3d4",
        "title": "新产品发布会直播",
        "description": "介绍我们即将发布的 v3.0 版本。",
        "stream_key": "example_stream_key_placeholder",
        "is_private": false,
        "record_by_default": true,
        "created_at": "2025-07-07T19:10:00Z"
      },
      "timestamp": "2025-07-07T19:15:00Z"
    }
    ```
  * **失败响应示例** (`404 Not Found`):
    ```json
    {
        "code": 2001,
        "message": "资源不存在",
        "data": {"resource": "Room", "id": "non_existent_uuid"},
        "timestamp": "2025-07-07T19:16:00Z"
    }
    ```
  * **实现流程描述**:
    1.  定义 FastAPI 路由函数，接收路径参数 `room_id: UUID` 和数据库会话 `db`。
    2.  根据 `room_id` 查询 `live_rooms` 表。
    3.  如果查询结果为空，返回 HTTP `404` 及业务错误码 `2001`。
    4.  如果找到，构建并返回包含房间详细信息的成功响应。

-----

##### **4. 更新直播房间信息**

  * **Endpoint**: `PATCH /api/v1/rooms/{room_id}`
  * **功能描述**: 更新指定 `room_id` 的直播房间信息，如标题、描述等。此操作不应在房间有正在进行的直播时执行。
  * **请求体** (`application/json`):
    ```json
    {
      "title": "新产品发布会直播（已更新）",
      "description": "更新：我们将额外演示 AI 功能。"
    }
    ```
  * **成功响应** (`200 OK`):
    ```json
    {
      "code": 200,
      "message": "success",
      "data": {
        "id": "a1b2c3d4-e5f6-4a1b-8c3d-e5f6a1b2c3d4",
        "title": "新产品发布会直播（已更新）",
        "description": "更新：我们将额外演示 AI 功能。",
        "updated_at": "2025-07-07T19:20:00Z"
      },
      "timestamp": "2025-07-07T19:20:00Z"
    }
    ```
  * **失败响应示例** (`403 Forbidden`):
    ```json
    {
        "code": 2002,
        "message": "业务逻辑错误",
        "data": {"error": "无法修改正在直播的房间"},
        "timestamp": "2025-07-07T19:21:00Z"
    }
    ```
  * **实现流程描述**:
    1.  定义 FastAPI 路由函数，接收 `room_id: UUID`、Pydantic 模型 `RoomUpdate` 和数据库会话 `db`。
    2.  查询 `live_rooms` 表获取 `room` 对象。如果未找到，返回 404。
    3.  **业务逻辑检查**: 查询 `live_sessions` 表，检查是否存在 `room_id` 为此 `room_id` 且 `status` 为 `live` 的场次。如果存在，返回 HTTP `403` 及业务错误码 `2002`。
    4.  遍历 `RoomUpdate` 模型中客户端提交的字段，更新 `room` 对象的相应属性。
    5.  提交事务并刷新对象。
    6.  构建并返回更新后的房间信息。

-----

##### **5. 删除直播房间**

  * **Endpoint**: `DELETE /api/v1/rooms/{room_id}`
  * **功能描述**: 删除一个直播房间。该房间所有关联的直播场次和统计数据将因数据库的 `ON DELETE CASCADE` 设置而被级联删除。
  * **成功响应** (`200 OK`):
    ```json
    {
      "code": 200,
      "message": "success",
      "data": {
        "id": "a1b2c3d4-e5f6-4a1b-8c3d-e5f6a1b2c3d4",
        "status": "deleted"
      },
      "timestamp": "2025-07-07T19:25:00Z"
    }
    ```
  * **失败响应示例** (`403 Forbidden`):
    ```json
    {
        "code": 2003,
        "message": "业务逻辑错误",
        "data": {"error": "无法删除正在直播的房间"},
        "timestamp": "2025-07-07T19:26:00Z"
    }
    ```
  * **实现流程描述**:
    1.  定义 FastAPI 路由函数，接收 `room_id: UUID` 和数据库会话 `db`。
    2.  查询 `live_rooms` 表获取 `room` 对象。如果未找到，返回 404。
    3.  **业务逻辑检查**: 与“更新”操作类似，检查该房间当前是否有正在进行的直播。如果有，返回 HTTP `403` 及业务错误码 `2003`。
    4.  **数据库操作**: 调用 `db.delete(room)` 将房间对象标记为待删除。
    5.  提交事务 `db.commit()`。数据库的级联删除设置会自动删除所有关联的 `live_sessions` 和 `session_statistics` 记录。
    6.  构建并返回操作成功的简单响应。
-----

#### **资源: 直播场次 (`live_sessions`)**

##### **1. 获取指定房间的直播场次列表**

  * **Endpoint**: `GET /api/v1/rooms/{room_id}/sessions`
  * **功能描述**: 分页获取指定 `room_id` 的所有历史和当前直播场次。
  * **成功响应** (`200 OK`):
    ```json
    {
        "code": 200, "message": "success",
        "data": {
            "total": 25, "page": 1, "size": 10,
            "items": [
                {"id": "session_uuid_1", "status": "ready", "start_time": "...", "end_time": "..."},
                {"id": "session_uuid_2", "status": "finished", "start_time": "...", "end_time": "..."}
            ]
        },
        "timestamp": "2025-07-07T19:40:00Z"
    }
    ```

-----

##### **2. 获取单场直播的详细信息**

  * **Endpoint**: `GET /api/v1/sessions/{session_id}`
  * **功能描述**: 获取指定 `session_id` 的直播场次的详细信息，包含其实时或历史统计数据。这是判断一场直播是否在进行、获取其实时数据的核心接口。
  * **成功响应** (`200 OK`):
    ```json
    {
      "code": 200, "message": "success",
      "data": {
        "id": "session_uuid_1",
        "room_id": "a1b2c3d4-e5f6-4a1b-8c3d-e5f6a1b2c3d4",
        "room_title": "我的第一场技术分享直播",
        "status": "live",
        "start_time": "2025-07-07T18:00:00Z",
        "video_id": null,
        "statistics": {
          "current_viewer_count": 150,
          "peak_viewer_count": 200,
          "total_like_count": 2500,
          "updated_at": "2025-07-07T18:30:15Z"
        }
      },
      "timestamp": "2025-07-07T18:30:20Z"
    }
    ```
  * **失败响应示例** (`404 Not Found`):
    ```json
    {
      "code": 2001,
      "message": "资源不存在",
      "data": {"resource": "Session", "id": "session_uuid_not_exist"},
      "timestamp": "2025-07-07T18:31:00Z"
    }
    ```

-----

### **针对分会场API接口**

**核心设计理念**:

  * **创建 (Create)**: 在主会场的上下文中进行，即在创建房间时指定 `parent_room_id`。
  * **读取列表 (Read List)**: 通过主会场的子资源路径进行查询。
  * **读取详情 (Retrieve), 更新 (Update), 删除 (Delete)**: 直接对分会场这个资源本身进行操作，因此使用通用的 `/rooms/{id}` 路径，其中 `id` 为分会场自身的 ID。

-----

#### **1. 创建分会场 (Create)**

  * **Endpoint**: `POST /api/v1/rooms`
  * **功能描述**: 创建一个新的分会场，必须在请求体中提供其所属主会场的 `parent_room_id`。
  * **请求体** (`application/json`):
    ```json
    {
      "title": "分会场A：AI与未来",
      "description": "探讨 AIGC 的最新进展。",
      "parent_room_id": "a1b2c3d4-e5f6-4a1b-8c3d-e5f6a1b2c3d4",
      "record_by_default": true
    }
    ```
  * **成功响应** (`200 OK`):
    ```json
    {
      "code": 200,
      "message": "success",
      "data": {
        "id": "sub_venue_uuid_A",
        "parent_room_id": "a1b2c3d4-e5f6-4a1b-8c3d-e5f6a1b2c3d4",
        "title": "分会场A：AI与未来",
        "stream_key": "example_stream_key_placeholder",
        "created_at": "2025-07-08T12:30:00Z"
      },
      "timestamp": "2025-07-08T12:30:00Z"
    }
    ```
  * **失败响应示例** (`400 Bad Request` - 未提供父级ID或父级ID不存在):
    ```json
    {
        "code": 4001,
        "message": "参数校验失败",
        "data": {
          "field": "parent_room_id",
          "error": "指定的主会场不存在"
        },
        "timestamp": "2025-07-08T12:31:00Z"
    }
    ```
  * **实现流程描述**:
    1.  定义 FastAPI 路由函数，接收 Pydantic 模型 `RoomCreate`，其中 `parent_room_id` 为可选字段。
    2.  **业务逻辑检查**: 如果请求中提供了 `parent_room_id`，必须先查询数据库确认该 ID 对应的主会场是否存在。如果不存在，返回 400 错误。
    3.  调用 `secrets.token_hex()` 生成唯一的 `stream_key`。
    4.  创建 `models.LiveRoom` 实例，填充所有信息，包括 `parent_room_id`。
    5.  通过 `db.add()`, `db.commit()`, `db.refresh()` 将新房间持久化。
    6.  构建并返回成功的响应。

-----

#### **2. 获取分会场列表 (Read - List)**

  * **Endpoint**: `GET /api/v1/rooms/{room_id}/sub-venues`
  * **功能描述**: 分页获取指定 `room_id` 的所有直属分会场列表，并包含每个分会场当前的直播状态。
  * **请求参数 (Query)**: `page`, `size`, `sort`
  * **成功响应** (`200 OK`):
    ```json
    {
      "code": 200,
      "message": "success",
      "data": {
        "total": 2,
        "page": 1,
        "size": 10,
        "items": [
          {
            "id": "sub_venue_uuid_A",
            "title": "分会场A：AI与未来",
            "cover_url": "https://example.com/cover_a.jpg",
            "live_status": "live",
            "current_session_id": "session_uuid_of_A"
          },
          {
            "id": "sub_venue_uuid_B",
            "title": "分会场B：云计算架构",
            "cover_url": "https://example.com/cover_b.jpg",
            "live_status": "finished",
            "current_session_id": null
          }
        ]
      },
      "timestamp": "2025-07-08T11:00:00Z"
    }
    ```
  * **失败响应示例** (`404 Not Found` - 主会场不存在):
    ```json
    {
      "code": 2001,
      "message": "资源不存在",
      "data": { "resource": "Main Room", "id": "non_existent_main_room_uuid" },
      "timestamp": "2025-07-08T11:01:00Z"
    }
    ```
  * **实现流程描述**:
    1.  定义 FastAPI 路由函数，接收路径参数 `room_id: UUID` 和分页参数。
    2.  验证 `room_id` 对应的主会场是否存在，不存在则返回 404。
    3.  构建基础查询，筛选 `parent_room_id` 等于 `room_id` 的所有 `live_rooms`。
    4.  使用 `LEFT JOIN` 关联 `live_sessions` 表（条件为 `live_sessions.room_id = live_rooms.id` 且 `live_sessions.status = 'live'`）以获取实时直播状态。
    5.  应用分页和排序逻辑，执行查询。
    6.  遍历结果，组装 `items` 数组，并构建最终的成功响应。

-----

#### **3. 获取单个分会场详情 (Read - Retrieve)**

  * **Endpoint**: `GET /api/v1/rooms/{sub_venue_id}`
  * **功能描述**: 获取指定 ID 的分会场的详细信息。此接口与获取主会场详情完全相同。
  * **成功响应** (`200 OK`):
    ```json
    {
      "code": 200,
      "message": "success",
      "data": {
        "id": "sub_venue_uuid_A",
        "parent_room_id": "a1b2c3d4-e5f6-4a1b-8c3d-e5f6a1b2c3d4",
        "title": "分会场A：AI与未来",
        "description": "探讨 AIGC 的最新进展。",
        "stream_key": "example_stream_key_placeholder",
        "created_at": "2025-07-08T12:30:00Z"
      },
      "timestamp": "2025-07-08T12:35:00Z"
    }
    ```
  * **实现流程描述**:
    1.  此接口的实现逻辑与获取主会场的 `GET /api/v1/rooms/{room_id}` **完全相同**。
    2.  后端只需根据传入的 `sub_venue_id` 查询 `live_rooms` 表并返回结果即可，无需关心它是否是分会场。

-----

#### **4. 更新分会场信息 (Update)**

  * **Endpoint**: `PATCH /api/v1/rooms/{sub_venue_id}`
  * **功能描述**: 更新指定 ID 的分会场的标题、描述等信息。
  * **请求体** (`application/json`): `{ "title": "分会场A：AI与未来（专家研讨）" }`
  * **成功响应** (`200 OK`): (响应结构与获取详情类似，返回更新后的完整对象)
  * **实现流程描述**:
    1.  此接口的实现逻辑与更新主会场的 `PATCH /api/v1/rooms/{room_id}` **完全相同**。
    2.  后端根据 `sub_venue_id` 找到记录，检查其下是否有正在进行的 `live_session`，如果没有，则更新字段并保存。

-----

#### **5. 删除分会场 (Delete)**

  * **Endpoint**: `DELETE /api/v1/rooms/{sub_venue_id}`
  * **功能描述**: 删除指定 ID 的分会场。删除后，该分会场所有历史场次和统计数据也将被级联删除。
  * **成功响应** (`200 OK`):
    ```json
    {
      "code": 200,
      "message": "success",
      "data": { "id": "sub_venue_uuid_A", "status": "deleted" },
      "timestamp": "2025-07-08T12:40:00Z"
    }
    ```
  * **实现流程描述**:
    1.  此接口的实现逻辑与删除主会场的 `DELETE /api/v1/rooms/{room_id}` **完全相同**。
    2.  后端根据 `sub_venue_id` 找到记录，检查其下是否有正在进行的 `live_session`，如果没有，则执行删除操作。

-----

### 6.3  **新增 API - 创建预告/计划场次**

  * **Endpoint**: `POST /api/v1/rooms/{room_id}/sessions`
  * **功能描述**: 为指定的直播房间，预先创建一个“计划中”的直播场次。
  * **请求体** (`application/json`):
    ```json
    {
      "title": "八月份产品更新前瞻 (预告)",
      "description": "我们将提前揭秘下个版本的新功能。",
      "scheduled_start_time": "2025-08-01T20:00:00+08:00"
    }
    ```
  * **成功响应** (`200 OK`):
    ```json
    {
      "code": 200,
      "message": "success",
      "data": {
        "id": "new_scheduled_session_uuid",
        "room_id": "{room_id}",
        "status": "scheduled",
        "start_time": "2025-08-01T20:00:00+08:00" 
      },
      "timestamp": "..."
    }
    ```
  * **实现流程描述**:
    1.  定义 FastAPI 路由函数，接收 `room_id` 和包含计划信息的 Pydantic 模型。
    2.  验证 `room_id` 是否有效。
    3.  **创建 `live_sessions` 实例**:
          * `id` 由应用层生成。
          * `room_id` 从路径参数获取。
          * **`status` 显式设置为 `'scheduled'`**。
          * **`start_time` 显式设置为请求体中的 `scheduled_start_time`**。
    4.  **创建 `session_statistics` 实例**并关联到新的 `session`。
    5.  将 `session` 和 `statistics` 对象存入数据库。
    6.  构建并返回成功的响应。

##### **3. 更新直播场次信息**

  * **Endpoint**: `PATCH /api/v1/sessions/{session_id}`
  * **功能描述**: 更新指定 `session_id` 的直播场次信息。可更新的字段和时机受限于场次当前的状态。
  * **请求体** (`application/json`):
    ```json
    {
      "title": "八月份产品更新前瞻（时间调整）",
      "description": "我们将提前揭秘下个版本的新功能，并增加 Q&A 环节。",
      "scheduled_start_time": "2025-08-01T21:00:00+08:00"
    }
    ```
  * **成功响应** (`200 OK`):
    ```json
    {
      "code": 200,
      "message": "success",
      "data": {
        "id": "new_scheduled_session_uuid",
        "status": "scheduled",
        "title": "八月份产品更新前瞻（时间调整）",
        "start_time": "2025-08-01T21:00:00+08:00",
        "updated_at": "2025-07-08T14:00:00Z"
      },
      "timestamp": "2025-07-08T14:00:00Z"
    }
    ```
  * **失败响应示例** (`403 Forbidden` - 尝试修改已开始的直播时间):
    ```json
    {
      "code": 2004,
      "message": "业务逻辑错误",
      "data": {
        "error": "无法修改正在直播或已结束场次的计划开始时间"
      },
      "timestamp": "2025-07-08T14:05:00Z"
    }
    ```
  * **实现流程描述**:
    1.  定义 FastAPI 路由函数，接收 `session_id: UUID`、Pydantic 模型 `SessionUpdate` 和数据库会话 `db`。
    2.  根据 `session_id` 查询 `live_sessions` 对象。如果未找到，返回 404。
    3.  **业务逻辑检查**:
          * 如果请求中包含 `scheduled_start_time`，则必须检查该场次的 `status` 是否为 `'scheduled'`。如果不是，则拒绝修改并返回 403 错误。
          * 其他字段（如 `title`, `description`）可以在更多状态下被修改，具体规则由您的业务决定。
    4.  遍历 `SessionUpdate` 模型中客户端提交的字段，更新 `session` 对象的相应属性。
    5.  提交事务并刷新对象。
    6.  构建并返回更新后的场次信息。

##### **3. 删除直播场次**

  * **Endpoint**: `DELETE /api/v1/sessions/{session_id}`
  * **功能描述**: 删除一个指定的直播场次。**业务逻辑应禁止删除正在直播 (`live`) 的场次**。
  * **成功响应** (`200 OK`):
    ```json
    {
      "code": 200,
      "message": "success",
      "data": {
        "id": "a1b2c3d4-e5f6-4a1b-8c3d-e5f6a1b2c3d4",
        "status": "deleted"
      },
      "timestamp": "2025-07-08T15:00:00Z"
    }
    ```
  * **失败响应示例** (`403 Forbidden` - 尝试删除正在直播的场次):
    ```json
    {
        "code": 2005,
        "message": "业务逻辑错误",
        "data": { "error": "无法删除正在直播的场次" },
        "timestamp": "2025-07-08T15:01:00Z"
    }
    ```
  * **实现流程描述**:
    1.  定义 FastAPI 路由函数，接收路径参数 `session_id: UUID` 和数据库会话 `db`。
    2.  根据 `session_id` 查询 `live_sessions` 对象。如果未找到，返回 404。
    3.  **业务逻辑检查**: 检查 `session` 对象的 `status` 是否为 `'live'`。如果是，则返回 HTTP `403` 及业务错误码 `2005`。
    4.  **数据库操作**: 调用 `db.delete(session)` 将该场次对象标记为待删除。由于 `session_statistics` 与之级联，其对应的统计记录也会被一并删除。
    5.  提交事务 `db.commit()`。
    6.  构建并返回操作成功的简单响应。

-----

### **6.4 内部 API 规范 (SRS 回调)**

本章节详细定义由媒体服务器（SRS）回调的内部 API 接口，这些接口是连接媒体层和业务逻辑层的桥梁，负责驱动直播生命周期的自动管理。

#### **1. `POST /internal/srs/on_publish` (推流发布与会话激活)**

* **职责**:
    验证推流凭证 (`stream_key`) 的有效性，并激活或创建一个直播会话 (`LiveSession`)，以正式记录一场直播的开始。

* **核心逻辑**:
    1.  SRS 在接收到客户端推流时，携带 `stream_key` 等信息回调此接口。
    2.  后端服务根据 `stream_key` 验证其所属的直播间 (`LiveRoom`) 是否存在。若无效，则返回 `403` 拒绝推流。
    3.  验证通过后，系统会检查该直播间是否存在一个“计划中”(`scheduled`) 的会话。
        * **场景A (计划内直播)**: 如果存在，系统会将该会话的状态更新为 `live`，并将其 `start_time` 更新为当前的服务器时间，以精确记录实际开播时刻。
        * **场景B (即兴直播)**: 如果不存在，系统会立即创建一个新的会话，状态直接设为 `live`，`start_time` 设为当前服务器时间。
    4.  处理成功后，向 SRS 返回 `200 OK`，允许推流继续。



#### **2. `POST /internal/srs/on_unpublish` (推流结束与后台任务派发)**

* **职责**:
    接收推流结束事件，将直播会话标记为已完成，并**触发**后续的、耗时的媒体处理任务。

* **核心逻辑与实现方案**:

    1.  **即时响应 (通用逻辑)**:
        * SRS 在检测到推流断开时回调此接口。
        * 后端服务立即查找当前 `live` 状态的直播会话，将其状态更新为 `finished`，并记录 `end_time`。

    2.  **后台任务派发 (核心)**:
        * 在完成状态更新后，接口会立即通过 `.delay()` 调用一个预定义的 Celery 任务 (`post_stream_processing_task`)，并将 `session_id` 等必要信息作为参数传递。
        * 任务消息将被发送至 **Redis** 消息队列，API 接口的调用会**立即返回**，从而保证对 SRS 的快速响应。

    3.  **任务执行架构：原生异步 (Task Execution Architecture: Native Async)**:
        * **核心技术**: 本项目采用 Celery 结合 **Redis** 作为消息中间件，并配置 **`gevent`** 作为其执行池（Execution Pool），以实现原生的高性能异步任务处理。
        * **工作原理**: Celery Worker 本身是异步的，它利用 `gevent` 的协程（Coroutines）能力，可以在单个进程内高并发地处理大量 I/O 密集型任务。当一个任务执行到 `await`（如等待数据库响应）时，Worker 不会阻塞，而是会立刻切换去执行另一个就绪的任务，从而极大地提升了系统的吞吐能力。
        * **任务定义**: 所有的 Celery 任务函数（如 `post_stream_processing_task`）都将被定义为**异步函数 (`async def`)**。这使得在任务内部可以直接、自然地使用 `await` 关键字来调用项目中的其他异步函数（例如异步的 CRUD 操作）。

    4.  **最终响应**:
        * 接口在任务被成功派发到 Redis 队列后，会立即向 SRS 返回 `200 OK`。

#### **3. `post_stream_processing_task` 任务核心逻辑 (由 Celery 执行)**

* **职责**:
    本节定义由 Celery 的原生异步 Worker 执行的后台任务 (`post_stream_processing_task`) 的核心业务逻辑。

* **核心逻辑**:
    1.  **进入 `processing` 状态**: 任务开始执行时，应**立即**将数据库中对应 `session_id` 的记录状态从 `finished` **更新**为 `processing`。
    2.  **执行核心任务**: 执行实际的耗时操作，如视频转码、分析、生成封面等。
    3.  **进入最终状态 (`ready` 或 `error`)**:
        * **场景A (处理成功)**: 如果所有任务顺利完成，在最后一步将该会话的状态从 `processing` **更新**为 `ready`。
        * **场景B (处理失败)**: 如果在处理过程中发生无法恢复的错误，应捕获异常，并将该会话的状态从 `processing` **更新**为 `error`。
---


## 7\. 存储与 ID 规范

### 7.1. 存储路径规范(v2, video_id使用uuid，而不是liveroom_4位uuid)

所有由直播场次生成的媒资将遵循以下结构，根目录由 `video_id` 唯一标识。

```
/media/video_4e3a2b1c-76a4-44a2-9b6f-1a2b3c4d5e6f/
├── images/
│   ├── cover_4e3a2b1c-76a4-44a2-9b6f-1a2b3c4d5e6f_upload_20250528T153200.jpg
│   └── thumbnail_4e3a2b1c-76a4-44a2-9b6f-1a2b3c4d5e6f_upload_20250528T153210.webp
├── raw/
│   └── video_4e3a2b1c-76a4-44a2-9b6f-1a2b3c4d5e6f_upload_20250528T153000.mp4
├── hls_1080p_4Mbps/
│   ├── index_4e3a2b1c-76a4-44a2-9b6f-1a2b3c4d5e6f_transcoded_20250528T154500.m3u8
│   └── ts/
│       ├── segment_000_4e3a2b1c-76a4-44a2-9b6f-1a2b3c4d5e6f_transcoded_20250528T154501.ts
├── mp4/
│   ├── video_4e3a2b1c-76a4-44a2-9b6f-1a2b3c4d5e6f_transcoded_1080p_20250528T155000.mp4
└── metadata.json
```


## 8\. 开发实施计划

1.  **阶段一 (基础架构)**: 完成环境搭建，并实现 `live_rooms`, `live_sessions`, `session_statistics` 的数据库模型与 Pydantic Schemas。
2.  **阶段二 (认证体系)**: 实现JWT认证模块，包括Token验证、权限控制、用户隔离等核心功能。
2.  **阶段三 (房间管理)**: 实现 `/api/v1/rooms` 的完整 CRUD 接口。
3.  **阶段四 (直播集成)**: 配置 SRS，实现 `/internal/srs` 的两个回调接口，完成直播生命周期的闭环。
4.  **阶段五 (统计与查询)**: 实现后台定时任务，并实现 `/api/v1/sessions` 的查询接口。
5.  **阶段六 (前端对接与部署)**: 开发简易前端播放页面，配置 Nginx，完成部署。

您提出的这一点非常关键，也是一个优秀的设计者会考虑到的问题。一个系统设计文档，不仅要描述“是什么”（架构），还要能指导“怎么用”（集成与测试）。

您的判断是正确的：文档中确实应该包含关于如何使用 FFmpeg 进行推流的部分。

但是，关于**放在哪里**以及**如何描述**，我建议采用一种能明确区分“后端设计”与“客户端实践”的专业方法。

### 推荐方案：在文档中新增“附录”章节

不建议将 FFmpeg 的具体命令直接写入核心的“系统架构”或“API规范”章节，因为这些章节的重点是定义**服务端的契约和行为**。FFmpeg 是一个**客户端工具**，它的用法属于实践和示例的范畴。

最好的做法是，在您的设计文档末尾创建一个新的顶级章节，例如 **“附录 (Appendix)”**，专门用来存放这类实践指南。

这样做的好处是：

  * **职责分离**: 保持核心设计章节的纯粹性，专注于架构本身。
  * **易于查找**: 为需要进行推流测试的开发者（无论是前端、后端还是测试人员）提供一个清晰的查找入口。
  * **便于扩展**: 未来如果引入 OBS 或其他推流工具，可以方便地在该附录下新增小节，而无需改动核心设计。

-----

## 9\. 身份认证与授权体系

### 9.1 认证架构概述

LiveCore Service采用JWT Token认证机制，与用户服务集成实现统一的身份验证：

- **认证方式**: JWT Token (JSON Web Token)
- **认证流程**: 用户通过用户服务进行SSO登录，获得JWT Token后访问LiveCore Service
- **权限控制**: 1）所有登录用户都可以访问所有直播房间和场次，支持基于user_id的可选过滤
               2）登录用户只能修改删除直接创建的直播间和直播session
- **Token验证**: 使用与用户服务相同的JWT密钥进行Token验证
- **安全机制**: 支持Token过期检查、签名验证、用户权限验证
- **应用层验证**: 通过JWT Token验证用户存在性，保证user_id引用完整性
- **数据一致性**: JWT Token有效即证明用户存在，无需额外验证

### 9.2 认证授权架构

```
┌─────────────┐    ┌─────────────────┐    ┌──────────────┐
│   Frontend  │────│   Users Service │────│   Authing    │
│             │    │  (SSO + JWT)    │    │     SSO      │
└─────────────┘    └─────────────────┘    └──────────────┘
       │                     │
       │              颁发JWT Token
       │                     │
       └─────────────────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
┌───────▼───┐ ┌───────▼───┐ ┌───────▼───┐
│ LiveCore  │ │   Media   │ │   Other   │
│ Service   │ │ Download  │ │  Service  │
│           │ │ Service   │ │           │
└───────────┘ └───────────┘ └───────────┘
        │            │            │
        └────────────┼────────────┘
                     │
              JWT Token验证
                     │
              ┌──────▼──────┐
              │  用户权限验证  │
              │  数据隔离    │
              └─────────────┘

**认证组件说明：**
1. **JWT验证模块** (`app/core/auth.py`): 负责Token验证和用户信息提取
2. **认证中间件** (`app/core/deps.py`): 提供认证依赖注入
3. **权限验证**: 在Service层业务逻辑中验证用户对资源的访问权限
4. **数据隔离**: 确保登录用户可以访问所有的直播房间和场次， 但只能修改删除自己的直播间和场次
5. **架构分层**: Service层负责权限验证，CRUD层专注于数据访问，避免重复验证
```

### 9.3 认证授权规范

#### 9.3.1 认证要求
**所有API接口都需要JWT Token认证：**
- 请求头必须包含：`Authorization: Bearer <JWT_TOKEN>`
- Token由用户服务颁发，包含用户身份信息
- 未认证的请求返回401状态码

#### 9.3.2 权限控制
**用户数据隔离原则：**
- 所有登录用户都可以查看所有直播房间和场次
- 支持基于user_id的可选查询过滤
- 用户只能修改/删除自己的房间和场次
- 所有涉及用户数据的操作都必须验证用户权限
- 通过JWT Token中的user_id进行权限验证

#### 9.3.3 认证失败处理
| HTTP状态码 | 错误码 | 说明 | 处理建议 |
|-----------|--------|------|----------|
| 401 | 401001 | 认证凭证缺失 | 检查Authorization头 |
| 401 | 401002 | 认证凭证无效 | 重新登录获取Token |
| 401 | 401003 | 认证凭证已过期 | 刷新Token或重新登录 |
| 403 | 403001 | 权限不足 | 检查用户权限 |

#### 9.3.4 认证响应格式
**认证失败响应示例：**
```json
{
  "code": 401,
  "message": "认证失败",
  "data": {
    "error": "认证凭证已过期",
    "error_code": "401003"
  },
  "timestamp": "2025-07-07T19:30:00Z"
}
```

### 9.4 用户认证流程

#### 9.4.1 JWT Token验证流程
```python
def verify_user_authentication(token: str) -> Dict:
    """
    验证用户JWT Token
    :param token: JWT Token字符串
    :return: 用户信息字典
    """
    try:
        # 1. 验证Token签名和格式
        payload = jwt.decode(
            token, 
            JWT_SECRET_KEY, 
            algorithms=[JWT_ALGORITHM]
        )
        
        # 2. 检查Token过期时间
        if payload.get('exp') and time.time() > payload['exp']:
            raise HTTPException(status_code=401, detail="认证凭证已过期")
        
        # 3. 提取用户信息
        user_info = {
            "user_id": payload.get("user_id"),
            "username": payload.get("username"),
            "role": payload.get("role", "user"),
            "permissions": payload.get("permissions", [])
        }
        
        # 4. 验证必要字段
        if not user_info["user_id"]:
            raise HTTPException(status_code=401, detail="Token中缺少用户ID")
        
        return user_info
        
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="认证凭证无效")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"认证验证失败: {str(e)}")
```

#### 9.4.2 用户权限验证流程
```python
def verify_user_permission(user_id: str, resource_id: str, resource_type: str = "room") -> bool:
    """
    验证用户对资源的访问权限
    :param user_id: 用户ID
    :param resource_id: 资源ID
    :param resource_type: 资源类型（room/session）
    :return: 是否有权限访问
    """
    try:
        if resource_type == "room":
            # 验证直播房间权限
            room = get_live_room(resource_id)
            return room and room.user_id == user_id
        elif resource_type == "session":
            # 验证直播场次权限（通过room_id关联）
            session = get_live_session(resource_id)
            if session and session.room_id:
                room = get_live_room(session.room_id)
                return room and room.user_id == user_id
            return False
        else:
            return False
    except Exception:
        return False
```

### 9.5 JWT认证安全

#### 9.5.1 Token安全要求
- **密钥管理**: JWT_SECRET_KEY必须与用户服务保持一致
- **算法选择**: 使用HS256算法进行Token签名
- **过期时间**: Token过期时间设置为30分钟
- **刷新机制**: 支持Token刷新，避免频繁重新登录

#### 9.5.2 权限验证安全
- **用户隔离**: 严格验证用户对资源的访问权限
- **数据过滤**: 支持可选的用户ID过滤，默认返回所有数据
- **操作审计**: 记录所有认证和授权操作日志
- **异常处理**: 认证失败时返回统一的错误响应

#### 9.5.3 安全配置
```python
# JWT安全配置
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 30

# 权限验证配置
MAX_FAILED_AUTH_ATTEMPTS = 5
AUTH_LOCKOUT_DURATION = 300  # 5分钟

# 应用层验证配置
USER_ID_VALIDATION_MODE = "jwt_token"  # 通过JWT Token验证用户存在性
CROSS_SERVICE_VALIDATION = False  # 不进行跨服务用户验证
```

### 9.6 认证授权规范

#### 9.6.1 认证日志规范
- **认证成功日志**: 记录用户ID、IP地址、访问时间
- **认证失败日志**: 记录失败原因、IP地址、尝试次数
- **权限验证日志**: 记录资源访问、权限验证结果
- **异常认证日志**: 记录异常Token、格式错误等

#### 9.6.2 权限验证规范
- **房间级权限**: 验证用户对直播房间的访问权限
- **场次级权限**: 验证用户对直播场次的访问权限
- **操作级权限**: 验证用户对特定操作（创建、修改、删除）的权限
- **数据级权限**: 支持登录用户查看所有数据，可选择过滤自己的数据

#### 9.6.3 安全审计规范
- **访问审计**: 记录所有API访问的认证状态
- **操作审计**: 记录所有数据操作的权限验证结果
- **异常审计**: 记录所有认证和授权异常情况
- **合规报告**: 定期生成安全合规性报告


### 9.7 权限验证架构设计

#### 9.7.1 分层权限验证原则

**架构设计原则：**
- **Service层职责**: 负责业务逻辑和权限验证，确保用户只能访问和操作自己的资源
- **CRUD层职责**: 专注于数据访问操作，不包含权限验证逻辑
- **避免重复验证**: 权限验证只在Service层进行，避免在CRUD层重复验证

**权限验证流程：**
1. **API层**: 验证JWT Token，提取用户ID
2. **Service层**: 进行权限验证，确保用户对资源的访问权限
3. **CRUD层**: 执行纯粹的数据访问操作，不涉及权限验证

**实现示例：**
```python
# Service层权限验证示例
async def update_room_info(self, room_id: uuid.UUID, room_update: LiveRoomUpdate, user_id: uuid.UUID) -> LiveRoom:
    # 1. 验证房间是否存在且属于当前用户
    room = await crud_room.get(db=self.db, room_id=room_id, user_id=user_id)
    if not room:
        raise RoomNotFoundException()
    
    # 2. 业务逻辑检查（如直播状态检查）
    is_live = await crud_room.is_live(db=self.db, room_id=room_id)
    if is_live:
        raise ActionForbiddenException("无法修改正在直播的房间")
    
    # 3. 调用CRUD层执行更新（不包含权限验证）
    updated_room = await crud_room.update(db=self.db, db_obj=room, obj_in=room_update)
    return updated_room
```

#### 9.7.2 user_id引用完整性保证

**设计原理：**
- JWT Token由用户服务颁发，包含真实用户的public_id
- Token有效即证明用户存在，无需跨服务验证
- 通过Token提取的user_id直接用于数据库操作

**实现流程：**
1. 用户登录 → 用户服务验证 → 颁发JWT Token
2. LiveCore Service验证Token → 提取user_id
3. 使用user_id创建/查询数据 → 保证引用完整性

**优势：**
- 无需跨服务查询验证用户存在性
- 性能优异，减少网络调用
- 符合微服务架构最佳实践

### 附录章节内容建议

以下是您可以直接采用或修改后放入您文档的附录章节内容。

-----

### **附录 A: 使用 FFmpeg 进行推流测试**

本附录旨在为开发者和测试人员提供使用 FFmpeg 工具向本系统进行 RTMP 推流的详细指南和常见示例。

#### **1. 推流地址格式**

所有推流请求都应遵循以下 RTMP URL 格式。推流地址由多个部分组成，其中最关键的是从后端 API 获取的 `stream_key`。

**标准格式**:
`rtmp://<srs_ip>:<port>/<app>/<stream_key>`

  * **`<srs_ip>`**: 您的 SRS 媒体服务器的公网 IP 地址或域名。
  * **`<port>`**: SRS 监听的 RTMP 端口，默认为 `1935`。
  * **`<app>`**: 您在 SRS 中配置的应用名称，通常为 `live`。
  * **`<stream_key>`**: **推流密钥**。这是推流的唯一凭证，必须通过调用后端的 `POST /api/v1/rooms` 接口创建直播间来获取。每个直播间拥有唯一的 `stream_key`。

#### **2. 核心推流命令**

FFmpeg 是一个功能强大的命令行工具。以下是一个基础的推流命令模板：

```bash
ffmpeg [输入参数] -i [输入源] [编码参数] -f flv [推流地址]
```
  * **`[输入参数]`**: 控制输入源的参数，例如 `-re` 表示以原生帧率读取文件，模拟真实直播。
  * **`-i [输入源]`**: 指定您的输入内容，可以是一个本地视频文件、一个摄像头设备、或桌面画面。
  * **`[编码参数]`**: 设置视频和音频的编码方式。例如，使用 `-c:v copy -c:a copy` 表示直接复制原始编码，不进行转码，可以极大地降低 CPU 消耗。
  * **`-f flv`**: 强制指定输出格式为 FLV，这是 RTMP 协议的标准容器格式。
  * **`[推流地址]`**: 上一步中定义的标准格式 RTMP URL。

#### **3. 常见推流场景示例**

##### **场景 A: 推送本地视频文件 (最常用测试方式)**

此方式用于将一个本地的 MP4 文件作为模拟直播源进行推流。

```bash
# 请将 <YOUR_SRS_IP> 和 <YOUR_STREAM_KEY> 替换为您的实际信息
ffmpeg -re -i /path/to/your/video.mp4 -c:v copy -c:a copy -f flv "rtmp://<YOUR_SRS_IP>:1935/live/<YOUR_STREAM_KEY>"
```

##### **场景 B: 推送无人值守的循环视频流 (24/7 直播)**

使用 `-stream_loop -1` 参数可以使视频文件无限循环播放。

```bash
# 无限循环播放 my_video.mp4
ffmpeg -re -stream_loop -1 -i /path/to/my_video.mp4 -c:v copy -c:a copy -f flv "rtmp://<YOUR_SRS_IP>:1935/live/<YOUR_STREAM_KEY>"
```

##### **场景 C: 推送实时摄像头画面 (真实直播)**

此方式用于捕获本机的摄像头和麦克风进行真实直播。**注意**: 输入设备名称因操作系统而异 (`avfoundation` for macOS, `dshow` for Windows, `video4linux2` for Linux)。

**macOS 示例:**

```bash
# -f avfoundation 指定输入格式
# -i "0:0" 表示使用第一个视频设备和第一个音频设备
ffmpeg -f avfoundation -i "0:0" -c:v libx264 -preset ultrafast -c:a aac -f flv "rtmp://<YOUR_SRS_IP>:1935/live/<YOUR_STREAM_KEY>"
```

**Windows 示例 (设备名称可能需要调整):**

```bash
# 需要先通过命令 `ffmpeg -list_devices true -f dshow -i dummy` 查找设备名称
ffmpeg -f dshow -i video="Integrated Camera":audio="Microphone Array" -c:v libx264 -preset ultrafast -c:a aac -f flv "rtmp://<YOUR_SRS_IP>:1935/live/<YOUR_STREAM_KEY>"
```

### **附录 B: OBS和FFmpeg的使用场景**

| 工具 | 主要用户 | 核心用途 | 优点 |
| :--- | :--- | :--- | :--- |
| **OBS Studio** | 主播、管理员（最终用户） | 日常使用、内容创作 | 图形界面、用户友好、功能丰富 |
| **FFmpeg** | **开发者、测试工程师** | **手动测试、自动化、调试** | **轻量、精准、可脚本化、自动化** |