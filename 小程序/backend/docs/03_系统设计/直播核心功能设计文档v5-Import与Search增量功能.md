# LiveCore Service - Import 与 Search 增量功能设计文档 (V6.0 - 学院派架构版)

* **版本**: 5.0（增量）
* **状态**: 设计定稿
* **基线版本**: 基于《直播核心功能设计文档 V5》
* **架构风格**: **学院派 (Academic)** - 严格遵循智能 CRUD + 厚 API Endpoint 模式
* **设计日期**: 2025-12-08
* **关联文档**:
  * 《LiveCore Service - 直播核心功能设计文档 V5》
  * 《用户核心模块设计文档 (V5.0 - 权限整合版)》

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
* **类名 (Class)**: 使用大驼峰命名法 (PascalCase)，例如 `SessionImportService`。
* **函数与方法 (Function/Method)**: 使用下划线命名法 (snake_case)，例如 `import_create_session`。
* **变量 (Variable)**: 使用下划线命名法 (snake_case)，例如 `playback_url`。
* **常量 (Constant)**: 使用全大写下划线命名法 (UPPER_SNAKE_CASE)，例如 `MAX_PLAYBACK_URL_LENGTH`。

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
* `INFO`: 记录重要的业务操作节点，如导入会话、搜索操作等。
* `DEBUG`: 用于开发和调试阶段，记录详细的程序运行信息。

##### **2.1.2 日志格式**
每一条日志记录都应包含以下标准字段：
* 时间戳 (ISO 8601 格式)
* 日志级别 (如: INFO)
* 模块名 (如: `services.session_import`)
* 函数名
* 行号
* 消息内容
* 异常堆栈 (仅在记录异常时包含)

##### **2.1.3 日志内容**
应记录但不限于以下关键信息：
* 导入会话操作的入口和结果（成功/失败数量）。
* 搜索查询的关键词和结果数量。
* 批量导入的文件信息、行数、成功率。
* 所有捕获到的异常信息。
* 关键性能监控数据（如 API 耗时）。

##### **2.1.4 日志管理与存储**
* **集中管理**: 使用 ELK Stack (Elasticsearch, Logstash, Kibana) 进行日志的统一收集、存储和查询。
* **存储策略**:
  * 日志文件按日期进行分割和归档。
  * 对用户密码、密钥等所有敏感信息必须进行脱敏处理。

#### **2.2 异常处理规范**

##### **2.2.1 异常分类**
* **系统异常**: 系统级错误（如数据库连接失败、文件读取错误）。
* **业务异常**: 不符合业务规则的正常操作（如导入状态不合法、URL格式错误）。
* **参数异常**: 用户输入参数不符合格式或校验规则。
* **权限异常**: 用户无权访问特定资源或执行特定操作。

##### **2.2.2 异常处理原则**
* **统一处理**: 实现统一的异常处理中间件 (Exception Handling Middleware) 来捕获所有未处理的异常，避免程序崩溃。
* **明确类型**: 使用自定义的、继承自 `Exception` 的异常类来区分不同的异常情况。
* **详细日志**: 捕获到任何异常时，都必须记录详细的错误日志，包含完整的异常堆栈。
* **格式统一**: 返回给客户端的错误响应必须遵循 `2.1. 通用响应结构` 的格式。
* **避免吞没**: 严禁捕获异常后不做任何处理（`except: pass`）。
* **优雅降级**: 在可能的情况下，对系统异常进行优雅降级处理，保证核心功能的可用性。

##### **2.2.3 异常处理流程（学院派）**
1. **CRUD 层**：捕获数据库异常（如 `IntegrityError`），`rollback` 事务，记录 `logger.error`，然后 `raise` 一个自定义的数据库异常（如 `DatabaseIntegrityException`）。
2. **Service 层**：执行业务检查。如果失败（如权限不足、参数非法），`raise` 一个自定义的业务异常（如 `InvalidParameterException`）。Service 层**不**捕获 CRUD 层的数据库异常（任其上浮）。
3. **API (Endpoint) 层**：**必须**使用 `try...except` 块。
   * `except InvalidParameterException as e:` -> `return JSONResponse(status_code=400, content=error_response(code=4xxx, ...))`
   * `except RoomNotFoundException as e:` -> `return JSONResponse(status_code=404, content=error_response(code=2001, ...))`
   * `except DatabaseIntegrityException as e:` -> `return JSONResponse(status_code=400, content=error_response(code=4001, ...))`
   * `except Exception as e:` -> `return JSONResponse(status_code=500, content=error_response(code=1xxx, ...))`

---

## 1. 概述

### 1.1. 文档目的

本文档旨在为 **LiveCore Service** 增加三项增量功能：
1. **Import Session（导入会话）**：允许在创建会话时直接携带 `playback_url`，简化外部会话导入流程。
2. **Search（搜索功能）**：支持按直播间 ID 或标题进行模糊搜索，提升用户查找效率。
3. **Batch Import（批量导入）**：支持通过 CSV/Excel 文件批量创建直播间和会话，并写入回放地址。

本文档将作为项目开发、测试和后续维护的统一依据。

### 1.2. 项目背景与架构决策

当前 LiveCore Service 已支持完整的直播间和会话管理功能。但在实际使用中，用户反馈以下痛点：

1. **导入外部会话繁琐**：对于已有回放地址的外部会话，需要先创建会话（`playback_url` 为 NULL）→ 修改状态为 `finished` → 再通过 PATCH 更新 `playback_url`，流程复杂且容易出错。
2. **缺少搜索能力**：直播间列表缺少按 ID 或标题的模糊搜索功能，用户查找特定直播间效率低。
3. **批量操作不便**：无法批量导入历史直播数据，需要逐个手动创建，工作量大。

本次增量设计严格遵循以下原则：
* **最小侵入**：不修改现有 API 路径和行为，仅新增 Endpoint 或可选参数。
* **架构一致性**：完全遵循"学院派"三层架构（CRUD 层智能化、Service 层业务化、API 层捕获化）。
* **向后兼容**：所有新增功能不影响已有客户端和测试用例。

---

## 2. 需求背景

### 2.1 Import Session（导入会话）

**业务场景**：
* 用户从外部系统（如旧平台、第三方CDN）迁移历史直播数据时，这些会话已经有明确的回放地址（`playback_url`）。
* 当前系统要求先创建会话（`playback_url` 必须为 NULL）→ 改状态为 `finished` → 再 PATCH 更新 `playback_url`，操作繁琐。

**需求描述**：
* 新增专用的"导入创建"API 端点，允许在创建时直接写入 `playback_url` 和终态状态（`finished` 或 `ready`）。
* 不影响普通会话创建流程（保持 `playback_url` 为 NULL 的约定）。

### 2.2 Search（搜索功能）

**业务场景**：
* 用户在管理后台或前端列表页面需要快速查找特定直播间。
* 当前只能通过分页翻页查找，效率低。

**需求描述**：
* 支持按直播间 ID（精确或模糊匹配）或标题（模糊匹配）进行搜索。
* 搜索结果保持分页格式，与现有列表接口返回结构一致。
* 采用"扩展现有接口"方式（新增可选 Query 参数），不破坏现有调用。

### 2.3 Batch Import（批量导入）

**业务场景**：
* 用户需要一次性导入大量历史直播数据（如从 Excel 表格或旧系统导出的 CSV 文件）。
* 手动逐个创建工作量大且易错。

**需求描述**：
* 支持上传 CSV/Excel 文件，批量创建直播间和会话。
* 支持 dry-run 模式（仅校验，不写库）和 apply 模式（实际写库）。
* 提供详细的导入报告（成功数、失败数、每行错误原因）。

### 2.4 认证与权限约束

* 所有 API 必须使用 JWT 认证。
* Import Session 和 Batch Import：需要验证用户对目标房间的归属权限（`room.user_id` == 当前用户）。
* Search：所有登录用户均可访问，支持按 `user_id` 过滤自己的房间。

---

## 3. 系统影响分析

### 3.1 数据库影响

**结论**：本次增量功能**不需要任何数据库 Schema 变更**。

**原因**：
* V5 版本已在 `live_sessions` 表中定义 `playback_url VARCHAR(1024) NULL` 字段。
* Import Session 只是在创建时允许写入该字段，不需要新增列。
* Search 功能基于现有 `live_rooms` 表的 `id` 和 `title` 字段，利用数据库索引即可。
* Batch Import 是批量调用现有创建逻辑，不引入新的数据结构。

**可选扩展**（本期不实现）：
* 若未来需要追踪导入来源，可考虑新增：
  * `live_sessions.source_type` (ENUM: 'native', 'import')
  * `live_sessions.external_ref` (VARCHAR: 外部系统 ID)

### 3.2 API 影响

**新增 Endpoint**（不修改现有）：
1. `POST /api/v1/rooms/{room_id}/sessions/import` - 导入创建会话
2. `POST /api/v1/rooms/import/batch` - 批量导入
3. `GET /api/v1/rooms?q=<keyword>` - 搜索（扩展现有接口的可选参数）

**兼容性保证**：
* 现有 `POST /api/v1/rooms/{room_id}/sessions` 保持不变（`playback_url` 必须为 NULL）。
* 现有 `GET /api/v1/rooms` 不传 `q` 参数时行为完全一致。

### 3.3 业务逻辑影响

**新增 Service 方法**：
* `SessionImportService.import_create_session()` - 处理导入创建逻辑
* `RoomService.search_rooms()` - 处理搜索逻辑（或扩展现有 `list_rooms`）
* `BatchImportService.import_from_file()` - 处理批量导入逻辑

**CRUD 层扩展**：
* 复用现有 `crud_session.create()` 和 `crud_room.create()`，由 Service 层控制字段赋值。
* 可选新增 `crud_room.search()` 方法，封装搜索 SQL 逻辑。

---

## 4. 数据模型设计

### 4.1 数据库 Schema（无变更）

本次增量功能完全基于现有数据库结构，以下为相关表的关键字段（引用自 V5 文档）：

```sql
-- 直播间表（已存在）
CREATE TABLE live_rooms (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    title VARCHAR(100) NOT NULL,
    description TEXT,
    cover_url VARCHAR(255),
    stream_key VARCHAR(255) NOT NULL UNIQUE,
    is_private BOOLEAN DEFAULT false,
    record_by_default BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 直播会话表（已存在，包含 playback_url 字段）
CREATE TABLE live_sessions (
    id UUID PRIMARY KEY,
    room_id UUID NOT NULL REFERENCES live_rooms(id) ON DELETE CASCADE,
    status live_session_status NOT NULL,
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ,
    video_id UUID NULL UNIQUE,
    playback_url VARCHAR(1024) NULL,  -- ← 关键字段，本次增量利用此字段
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

**关键约束**：
* `playback_url` 允许为 NULL（普通创建时为 NULL，导入创建时可非 NULL）。
* `status` 为 ENUM 类型，Import Session 限制为 `finished` 或 `ready`。

### 4.2 Pydantic Schema 定义

#### 4.2.1 Import Session 相关 Schema

```python
from pydantic import BaseModel, Field, validator
from uuid import UUID
from datetime import datetime
from typing import Optional

class SessionImportCreate(BaseModel):
    """导入创建会话的请求体"""
    start_time: datetime = Field(..., description="会话开始时间（必填）")
    end_time: Optional[datetime] = Field(None, description="会话结束时间（建议必填）")
    status: str = Field(..., description="会话状态，限制为 'finished' 或 'ready'")
    playback_url: str = Field(..., max_length=1024, description="回放地址（必填）")
    title: Optional[str] = Field(None, max_length=100, description="会话标题（可选）")
    description: Optional[str] = Field(None, description="会话描述（可选）")
    
    @validator('status')
    def validate_status(cls, v):
        if v not in ['finished', 'ready']:
            raise ValueError("导入会话的 status 只能为 'finished' 或 'ready'")
        return v
    
    @validator('playback_url')
    def validate_playback_url(cls, v):
        if not v.startswith(('http://', 'https://')):
            raise ValueError("playback_url 必须以 http:// 或 https:// 开头")
        return v

class SessionImportResponse(BaseModel):
    """导入创建会话的响应体"""
    id: UUID
    room_id: UUID
    status: str
    start_time: datetime
    end_time: Optional[datetime]
    video_id: Optional[UUID]
    playback_url: str
    created_at: datetime
    updated_at: datetime
```

#### 4.2.2 Search 相关 Schema

```python
class RoomSearchParams(BaseModel):
    """搜索参数"""
    q: Optional[str] = Field(None, max_length=100, description="搜索关键词（ID 或标题）")
    page: int = Field(1, ge=1, description="页码")
    size: int = Field(10, ge=1, le=100, description="每页数量")
```

#### 4.2.3 Batch Import 相关 Schema

```python
from typing import List

class BatchImportRow(BaseModel):
    """批量导入的单行结果"""
    row_no: int
    room_id: Optional[UUID]
    session_id: Optional[UUID]
    status: str  # 'success' or 'failed'
    error: Optional[str]

class BatchImportResponse(BaseModel):
    """批量导入的响应体"""
    total_rows: int
    success_count: int
    failed_count: int
    items: List[BatchImportRow]
```

---

## 5. API 设计（学院派实现）

所有 API 均继承 V5 规范：
* **统一响应结构**: `{code, message, data, timestamp}`
* **错误码体系**: `1xxx` 系统错误、`2xxx` 业务错误、`3xxx` 权限错误、`4xxx` 参数错误
* **实现模式**: 严格遵循 API (Catch) -> Service (Throw) -> CRUD (Transaction) 三层架构

### 5.1 Import Session API

#### 5.1.1 导入创建会话

* **Endpoint**: `POST /api/v1/rooms/{room_id}/sessions/import`
* **功能概述**: 为已有回放地址的外部会话创建记录，允许在创建时直接写入 `playback_url` 和终态状态。
* **认证**: 需要 JWT Token 认证
* **权限**: 用户必须是该 `room_id` 的所有者（`room.user_id` == 当前用户）

* **请求参数 (Path)**:
  * `room_id`: UUID - 目标直播间 ID

* **请求体** (`application/json`):
```json
{
  "start_time": "2025-07-07T18:00:00Z",
  "end_time": "2025-07-07T19:00:00Z",
  "status": "finished",
  "playback_url": "https://mp2.dayilive.com/mp_clip/video_123.m3u8",
  "title": "历史会议回放",
  "description": "从旧系统迁移的会话"
}
```

* **成功响应** (`200 OK`):
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": "session_uuid_import_001",
    "room_id": "room_uuid_123",
    "status": "finished",
    "start_time": "2025-07-07T18:00:00Z",
    "end_time": "2025-07-07T19:00:00Z",
    "video_id": null,
    "playback_url": "https://mp2.dayilive.com/mp_clip/video_123.m3u8",
    "created_at": "2025-12-08T10:00:00Z",
    "updated_at": "2025-12-08T10:00:00Z"
  },
  "timestamp": "2025-12-08T10:00:00Z"
}
```

* **失败响应示例 1** (`400 Bad Request` - 参数校验失败):
```json
{
  "code": 4001,
  "message": "参数校验失败",
  "data": {
    "field": "status",
    "error": "导入会话的 status 只能为 'finished' 或 'ready'"
  },
  "timestamp": "2025-12-08T10:01:00Z"
}
```

* **失败响应示例 2** (`404 Not Found` - 房间不存在):
```json
{
  "code": 2001,
  "message": "资源不存在",
  "data": {
    "resource": "Room",
    "id": "room_uuid_not_exist"
  },
  "timestamp": "2025-12-08T10:02:00Z"
}
```

* **失败响应示例 3** (`403 Forbidden` - 权限不足):
```json
{
  "code": 3002,
  "message": "权限不足",
  "data": {
    "error": "您无权在此房间导入会话"
  },
  "timestamp": "2025-12-08T10:03:00Z"
}
```

* **【学院派】实现流程描述**:
  1. `(API 层)`: 接收请求，通过 `Depends` 注入 `db` 和 `current_user`。
  2. `(API 层)`: **(安全规范)** 提前提取日志所需变量（如 `public_id = UUID(current_user.get("public_id"))`, `room_id`）。
  3. `(API 层)`: **启动 `try...except` 块**，用于捕获业务异常。
  4. `(API 层)`: 实例化 `service = SessionImportService(db=db)`。
  5. `(API 层)`: 调用 `await service.import_create_session(room_id=room_id, public_id=public_id, session_in=payload)`。
  6. `(Service 层)`: 验证 `room_id` 是否存在，调用 `crud_room.get(db, room_id)`。若不存在，`raise RoomNotFoundException`。
  7. `(Service 层)`: 验证权限：`room.user_id == public_id`。若不匹配，`raise PermissionDeniedException`。
  8. `(Service 层)`: 验证参数：`status` 必须为 `finished` 或 `ready`，`playback_url` 必须非空且格式正确。若不符，`raise InvalidParameterException`。
  9. `(Service 层)`: 调用 `await crud_session.create(db, obj_in=session_data)`（CRUD 层负责事务）。
  10. `(CRUD 层)`: **(学院派核心)** 在 `try...except IntegrityError...finally` 块中处理：
      * `db.add(db_obj)`
      * `await db.commit()`
      * `await db.refresh(db_obj)`
      * 若失败，`await db.rollback()` 并 `raise DatabaseIntegrityException`
  11. `(API 层)`: (`try` 块内) 返回 `success_response(data=session)`。
  12. `(API 层)`: **编写 `except RoomNotFoundException as e:` 块** (404/2001)。
  13. `(API 层)`: **编写 `except PermissionDeniedException as e:` 块** (403/3002)。
  14. `(API 层)`: **编写 `except InvalidParameterException as e:` 块** (400/4001)。
  15. `(API 层)`: **编写 `except DatabaseIntegrityException as e:` 块** (400/4001 或 500/1xxx)。
  16. `(API 层)`: **编写 `except Exception as e:` 块** (500/1000)。

---

### 5.2 Search API

#### 5.2.1 搜索直播间

* **Endpoint**: `GET /api/v1/rooms`
* **功能概述**: 获取直播间列表，支持按 ID 或标题模糊搜索（通过新增可选参数 `q` 实现）。
* **认证**: 需要 JWT Token 认证
* **权限**: 所有登录用户可访问，支持按 `user_id` 过滤

* **请求参数 (Query)**:
  * `q`: string (可选) - 搜索关键词，支持按 `room_id` 精确匹配或 `title` 模糊匹配
  * `page`: int (可选，默认 1) - 页码
  * `size`: int (可选，默认 10) - 每页数量
  * `sort`: string (可选) - 排序字段，格式为 `field:direction`，例如 `created_at:desc`

* **搜索逻辑**:
  * 若 `q` 为空：返回所有房间（保持现有行为）
  * 若 `q` 看起来像 UUID（36 个字符，包含连字符）：优先按 `id == q` 精确匹配
  * 同时支持 `title ILIKE '%q%'` 模糊匹配（OR 关系）

* **成功响应** (`200 OK`):
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "total": 3,
    "page": 1,
    "size": 10,
    "items": [
      {
        "id": "a1b2c3d4-e5f6-4a1b-8c3d-e5f6a1b2c3d4",
        "title": "新产品发布会直播",
        "cover_url": "/media/rooms/a1b2c3d4.../cover_....png",
        "created_at": "2025-07-07T19:10:00Z"
      },
      {
        "id": "b2c3d4e5-f6a1-4b2c-8d3e-f6a1b2c3d4e5",
        "title": "产品技术分享",
        "cover_url": "/media/rooms/b2c3d4e5.../cover_....png",
        "created_at": "2025-07-08T10:20:00Z"
      }
    ]
  },
  "timestamp": "2025-12-08T11:00:00Z"
}
```

* **失败响应示例** (`400 Bad Request` - 参数错误):
```json
{
  "code": 4001,
  "message": "参数校验失败",
  "data": {
    "field": "q",
    "error": "搜索关键词长度不能超过 100 个字符"
  },
  "timestamp": "2025-12-08T11:01:00Z"
}
```

* **【学院派】实现流程描述**:
  1. `(API 层)`: 接收请求，注入 `db`、`current_user`、`pagination_params`。
  2. `(API 层)`: 提取日志变量 `public_id = UUID(current_user.get("public_id"))`。
  3. `(API 层)`: **启动 `try...except` 块**。
  4. `(API 层)`: 实例化 `service = RoomService(db=db)`。
  5. `(API 层)`: 调用 `await service.search_rooms(public_id=public_id, q=q, page=page, size=size, sort=sort)`。
  6. `(Service 层)`: 构建查询条件：
     * 若 `q` 为空：不添加 WHERE 条件（保持现有逻辑）
     * 若 `q` 非空：
       * 判断是否为 UUID 格式（长度 36，包含 `-`）
       * 添加 `WHERE (id = q OR title ILIKE '%q%')` 条件
  7. `(Service 层)`: 调用 `crud_room.list_with_search(db, filters=..., page=..., size=..., sort=...)`。
  8. `(CRUD 层)`: 执行 SQL 查询（支持 ILIKE 和 UUID 精确匹配），根据 `sort` 参数动态构建排序（默认 `created_at DESC`），返回结果。
  9. `(API 层)`: (`try` 块内) 返回 `success_response(data={"total": ..., "page": ..., "items": ...})`。
  10. `(API 层)`: `except InvalidParameterException as e:` -> 400/4001。
  11. `(API 层)`: `except Exception as e:` -> 500/1000。

---

### 5.3 Batch Import API

#### 5.3.1 批量导入直播间和会话

* **Endpoint**: `POST /api/v1/rooms/import/batch`
* **功能概述**: 通过上传 CSV/Excel 文件批量创建直播间和会话，并写入回放地址。
* **认证**: 需要 JWT Token 认证
* **权限**: 所有登录用户可调用（创建的房间归属当前用户）

* **请求参数 (Query)**:
  * `mode`: string (可选，默认 `dry_run`) - 导入模式，可选值：`dry_run`（仅校验，不写库）、`apply`（实际写库）
  * `encoding_hint`: string (可选) - 文件编码提示，可选值：`utf-8-sig`、`utf-8`、`gbk`。若不提供，自动探测。

* **请求体** (`multipart/form-data`):
  * `file`: File - CSV 或 Excel 文件

* **CSV 文件格式**（列名不区分大小写，顺序不限）:
  * **逻辑必需列**（经标准化后的字段名，内部统一使用英文）:
    * `room_title`: string - 直播间标题
    * `playback_url`: string - 回放地址
  * **可选列**:
    * `room_id`: UUID - 若提供且存在，则复用该房间；否则创建新房间
    * `session_id`: UUID - 若提供，使用该 ID 创建会话；否则自动生成
    * `room_description`: string - 直播间描述
    * `session_title`: string - 会话标题（若不提供，使用 `room_title`）
    * `start_time`: ISO 8601 格式时间 - 会话开始时间（若不提供，使用当前时间）
    * `end_time`: ISO 8601 格式时间 - 会话结束时间
    * `status`: string - 会话状态，限制为 `finished` 或 `ready`（默认 `finished`）
    * `cover_url`: string - 封面地址
  * **与业务源文件（微赞导出格式）的表头映射关系**：
    * 典型源文件表头示例：`直播间ID, 标题, 直播间url, 创建时间, 开始时间, 结束时间, 播放url, 封面图片, ...`。
    * 解析时应先将表头统一为小写并去除首尾空格，然后做如下最小映射，再落到上述逻辑字段：
      * `标题` → `room_title`
      * `播放url`（以及历史模板中的 `播放url1`）→ `playback_url`
      * `封面图片` → `cover_url`
    * 只要经过映射后存在 `room_title` 与 `playback_url`，即可视为满足必需列要求；若既没有英文表头，也没有等价中文列，应返回 `"CSV 文件缺少必需列：room_title, playback_url"` 的错误提示。

* **成功响应** (`200 OK`):
```json
{
  "code": 200,
  "message": "success",
  "data": {
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
  },
  "timestamp": "2025-12-08T12:00:00Z"
}
```

* **失败响应示例 1** (`400 Bad Request` - 文件格式错误):
```json
{
  "code": 4001,
  "message": "参数校验失败",
  "data": {
    "error": "上传的文件必须是 CSV 或 Excel 格式"
  },
  "timestamp": "2025-12-08T12:01:00Z"
}
```

* **失败响应示例 2** (`400 Bad Request` - 必需列缺失):
```json
{
  "code": 4002,
  "message": "参数校验失败",
  "data": {
    "error": "CSV 文件缺少必需列：room_title, playback_url"
  },
  "timestamp": "2025-12-08T12:02:00Z"
}
```

* **【学院派】实现流程描述**:
  1. `(API 层)`: 接收请求，注入 `db`、`current_user`、`file: UploadFile`、`mode`。
  2. `(API 层)`: 提取日志变量 `public_id = UUID(current_user.get("public_id"))`。
  3. `(API 层)`: **启动 `try...except` 块**。
  4. `(API 层)`: 验证文件类型（`.csv` 或 `.xlsx`）。若不符，`raise InvalidParameterException`（在 API 层直接处理）。
  5. `(API 层)`: 实例化 `service = BatchImportService(db=db)`。
  6. `(API 层)`: 调用 `await service.import_from_file(public_id=public_id, file=file, mode=mode, encoding_hint=encoding_hint)`。
  7. `(Service 层)`: 读取文件内容（支持自动编码探测：utf-8-sig -> utf-8 -> gbk）。
  8. `(Service 层)`: 解析 CSV/Excel，提取原始表头，先统一做 **标准化与别名映射**（如将 `标题` 映射为 `room_title`，将 `播放url`（以及历史模板中的 `播放url1`）映射为 `playback_url`，将 `封面图片` 映射为 `cover_url`），得到逻辑字段集合；再验证是否包含 `room_title` 与 `playback_url` 两个必需列，若缺失则 `raise InvalidParameterException`。
  9. `(Service 层)`: 逐行处理：
     * **行级事务隔离**：每行的创建操作独立（一行失败不影响其他行）
     * 标准化文本（trim、折叠多余空白）
     * 验证 `room_title`、`playback_url` 必填
     * 若提供 `room_id` 且存在：
       * 验证权限（`room.user_id == public_id`）
       * 复用该房间
     * 否则：
       * 创建新房间（调用 `crud_room.create`，自动生成 `stream_key`）
     * 创建会话（调用 `crud_session.create`，写入 `playback_url`）
     * 记录结果：`{"row_no": i, "room_id": ..., "session_id": ..., "status": "success" or "failed", "error": ...}`
  10. `(Service 层)`: 根据 `mode` 决定是否提交事务：
      * `dry_run`：不调用 `db.commit()`，仅返回校验结果
      * `apply`：每行成功后 `db.commit()`（或使用 SAVEPOINT 实现行级回滚）
  11. `(Service 层)`: 返回导入报告 `{"total_rows": ..., "success_count": ..., "failed_count": ..., "items": [...]}`。
  12. `(API 层)`: (`try` 块内) 返回 `success_response(data=import_report)`。
  13. `(API 层)`: `except InvalidParameterException as e:` -> 400/4001。
  14. `(API 层)`: `except Exception as e:` -> 500/1000。

---

## 6. Service 层逻辑（学院派实现）

### 6.1 SessionImportService（导入会话服务）

```python
# app/services/session_import.py
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud import crud_room, crud_session, crud_session_statistics
from app.schemas.session_import import SessionImportCreate
from app.core.exceptions import (
    RoomNotFoundException,
    PermissionDeniedException,
    InvalidParameterException
)
import logging

logger = logging.getLogger(__name__)

class SessionImportService:
    """导入会话服务（学院派实现）"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def import_create_session(
        self, 
        room_id: UUID, 
        public_id: UUID, 
        session_in: SessionImportCreate
    ):
        """
        导入创建会话（业务逻辑层）
        
        职责：
        1. 验证房间存在性
        2. 验证用户权限
        3. 验证参数合法性
        4. 调用 CRUD 层创建会话（不处理事务）
        
        抛出异常：
        - RoomNotFoundException: 房间不存在
        - PermissionDeniedException: 用户无权操作
        - InvalidParameterException: 参数不合法
        """
        # 1. 验证房间存在性
        room = await crud_room.get(self.db, id=room_id)
        if not room:
            logger.warning(f"导入会话失败：房间不存在 room_id={room_id}")
            raise RoomNotFoundException(f"房间 {room_id} 不存在")
        
        # 2. 验证权限
        if room.user_id != public_id:
            logger.warning(
                f"导入会话失败：权限不足 public_id={public_id}, "
                f"room_id={room_id}, room.user_id={room.user_id}"
            )
            raise PermissionDeniedException("您无权在此房间导入会话")
        
        # 3. 验证参数（Pydantic 已做基础校验，这里做业务校验）
        if session_in.status not in ['finished', 'ready']:
            raise InvalidParameterException(
                code=4001,
                message="导入会话的 status 只能为 'finished' 或 'ready'"
            )
        
        if not session_in.playback_url:
            raise InvalidParameterException(
                code=4001,
                message="导入会话必须提供 playback_url"
            )
        
        # 4. 调用 CRUD 层创建会话（CRUD 层负责事务）
        # Service 层不调用 db.commit() 或 db.rollback()
        session_data = {
            "id": uuid.uuid4(),
            "room_id": room_id,
            "status": session_in.status,
            "start_time": session_in.start_time,
            "end_time": session_in.end_time,
            "playback_url": session_in.playback_url,
            "title": session_in.title,
            "description": session_in.description,
        }
        
        # CRUD 层负责事务，若失败会抛出 DatabaseIntegrityException
        db_session = await crud_session.create(self.db, obj_in=session_data)
        
        # 同时创建统计记录
        await crud_session_statistics.create(
            self.db, 
            obj_in={"session_id": db_session.id}
        )
        
        logger.info(
            f"导入会话成功：session_id={db_session.id}, "
            f"room_id={room_id}, public_id={public_id}"
        )
        
        return db_session
```

### 6.2 RoomService（搜索功能扩展）

```python
# app/services/room.py（扩展现有服务）
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud import crud_room
from typing import Optional
import logging
import re

logger = logging.getLogger(__name__)

class RoomService:
    """直播间服务（学院派实现）"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def search_rooms(
        self, 
        public_id: UUID,
        q: Optional[str] = None,
        page: int = 1,
        size: int = 10,
        sort: Optional[str] = None
    ):
        """
        搜索直播间（业务逻辑层）
        
        职责：
        1. 构建搜索条件
        2. 调用 CRUD 层查询
        
        参数：
        - public_id: 当前用户公开标识
        - q: 搜索关键词（ID 或标题）
        - page/size: 分页参数
        - sort: 排序字段（可选），格式为 field:direction
        
        返回：
        - {"total": int, "page": int, "size": int, "items": [Room]}
        """
        # 1. 构建搜索条件
        search_filters = {}
        
        if q:
            # 判断是否为 UUID 格式（36 个字符，包含 '-'）
            uuid_pattern = re.compile(
                r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-'
                r'[0-9a-f]{4}-[0-9a-f]{12}$',
                re.IGNORECASE
            )
            
            if uuid_pattern.match(q):
                # UUID 精确匹配
                search_filters['id_or_title'] = ('id', q)
                logger.info(f"搜索直播间（UUID）：q={q}")
            else:
                # 标题模糊匹配
                search_filters['id_or_title'] = ('title', f'%{q}%')
                logger.info(f"搜索直播间（标题）：q={q}")
        
        # 2. 调用 CRUD 层查询
        result = await crud_room.list_with_search(
            self.db, 
            filters=search_filters,
            page=page,
            size=size,
            sort=sort
        )
        
        logger.info(
            f"搜索直播间完成：q={q}, total={result['total']}, "
            f"found={len(result['items'])}"
        )
        
        return result
```

### 6.3 BatchImportService（批量导入服务）

```python
# app/services/batch_import.py
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import UploadFile
from app.crud import crud_room, crud_session
from app.core.exceptions import InvalidParameterException
import logging
import csv
import io
import chardet
from typing import List, Dict

logger = logging.getLogger(__name__)

class BatchImportService:
    """批量导入服务（学院派实现）"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def import_from_file(
        self,
        public_id: UUID,
        file: UploadFile,
        mode: str = 'dry_run',
        encoding_hint: Optional[str] = None
    ) -> Dict:
        """
        从 CSV/Excel 文件批量导入直播间和会话
        
        职责：
        1. 读取并解析文件
        2. 验证必需列
        3. 逐行处理（行级事务隔离）
        4. 根据 mode 决定是否提交事务
        
        参数：
        - public_id: 当前用户公开标识
        - file: 上传的文件
        - mode: 'dry_run' 或 'apply'
        - encoding_hint: 编码提示
        
        返回：
        - {"total_rows": int, "success_count": int, "failed_count": int, "items": []}
        """
        # 1. 读取文件内容
        content = await file.read()
        
        # 2. 自动探测编码
        encoding = self._detect_encoding(content, encoding_hint)
        logger.info(f"文件编码：{encoding}")
        
        # 3. 解析 CSV
        text = content.decode(encoding)
        csv_reader = csv.DictReader(io.StringIO(text))
        
        # 4. 验证必需列
        required_columns = {'room_title', 'playback_url'}
        columns = {col.lower().strip() for col in csv_reader.fieldnames}
        
        if not required_columns.issubset(columns):
            missing = required_columns - columns
            raise InvalidParameterException(
                code=4002,
                message=f"CSV 文件缺少必需列：{', '.join(missing)}"
            )
        
        # 5. 逐行处理
        import_results = []
        success_count = 0
        failed_count = 0
        
        for row_no, row in enumerate(csv_reader, start=1):
            try:
                # 标准化列名（转小写）
                row = {k.lower().strip(): v.strip() for k, v in row.items()}
                
                # 处理单行
                result = await self._process_row(
                    public_id=public_id,
                    row_no=row_no,
                    row=row,
                    mode=mode
                )
                
                import_results.append(result)
                
                if result['status'] == 'success':
                    success_count += 1
                else:
                    failed_count += 1
                    
            except Exception as e:
                logger.error(f"处理第 {row_no} 行失败：{e}", exc_info=True)
                import_results.append({
                    "row_no": row_no,
                    "room_id": None,
                    "session_id": None,
                    "status": "failed",
                    "error": str(e)
                })
                failed_count += 1
        
        # 6. 返回导入报告
        return {
            "total_rows": len(import_results),
            "success_count": success_count,
            "failed_count": failed_count,
            "items": import_results
        }
    
    async def _process_row(
        self,
        public_id: UUID,
        row_no: int,
        row: Dict,
        mode: str
    ) -> Dict:
        """处理单行数据（行级事务）"""
        # 1. 验证必需字段
        room_title = row.get('room_title')
        playback_url = row.get('playback_url')
        
        if not room_title or not playback_url:
            return {
                "row_no": row_no,
                "room_id": None,
                "session_id": None,
                "status": "failed",
                "error": "room_title 和 playback_url 不能为空"
            }
        
        # 2. 创建或复用房间
        room_id = row.get('room_id')
        
        if room_id:
            # 复用房间（需验证权限）
            room = await crud_room.get(self.db, id=room_id)
            if not room:
                return {
                    "row_no": row_no,
                    "room_id": None,
                    "session_id": None,
                    "status": "failed",
                    "error": f"房间 {room_id} 不存在"
                }
            if room.user_id != public_id:
                return {
                    "row_no": row_no,
                    "room_id": None,
                    "session_id": None,
                    "status": "failed",
                    "error": "无权操作该房间"
                }
        else:
            # 创建新房间
            if mode == 'apply':
                room_data = {
                    "id": uuid.uuid4(),
                    "user_id": public_id,
                    "title": room_title,
                    "description": row.get('room_description', ''),
                    "stream_key": self._generate_stream_key(),
                    "cover_url": row.get('cover_url'),
                }
                room = await crud_room.create(self.db, obj_in=room_data)
                room_id = room.id
            else:
                room_id = uuid.uuid4()  # dry_run 模式，生成临时 ID
        
        # 3. 创建会话
        session_id = row.get('session_id') or uuid.uuid4()
        
        if mode == 'apply':
            session_data = {
                "id": session_id,
                "room_id": room_id,
                "status": row.get('status', 'finished'),
                "start_time": row.get('start_time', datetime.utcnow()),
                "end_time": row.get('end_time'),
                "playback_url": playback_url,
                "title": row.get('session_title', room_title),
            }
            session = await crud_session.create(self.db, obj_in=session_data)
            session_id = session.id
        
        # 4. 返回结果
        return {
            "row_no": row_no,
            "room_id": str(room_id),
            "session_id": str(session_id),
            "status": "success",
            "error": None
        }
    
    def _detect_encoding(self, content: bytes, hint: Optional[str]) -> str:
        """自动探测文件编码"""
        if hint:
            return hint
        
        # 尝试顺序：utf-8-sig -> utf-8 -> gbk -> chardet
        for encoding in ['utf-8-sig', 'utf-8', 'gbk']:
            try:
                content.decode(encoding)
                return encoding
            except UnicodeDecodeError:
                continue
        
        # 使用 chardet 自动探测
        detected = chardet.detect(content)
        return detected['encoding'] or 'utf-8'
    
    def _generate_stream_key(self) -> str:
        """生成唯一的推流密钥"""
        import secrets
        return f"sk_live_{secrets.token_hex(16)}"
```

---

## 7. CRUD 层定义（学院派实现）

### 7.1 CRUD 层职责（学院派核心）

**必须遵守的规则**：
1. **必须**封装原子性数据库操作。
2. **必须**在写操作（create, update, delete）函数内部处理事务。
3. **必须**包含 `try...except IntegrityError/Exception...finally` 块。
4. **必须**处理 `db.commit()` 和 `db.rollback()`。
5. **必须**处理数据库错误日志 (`logger.error`)。
6. **必须**在 `try` 块之前提取日志所需变量（安全异步异常处理）。
7. **不做**业务逻辑或权限检查。

### 7.2 CRUD 示例：创建会话（支持导入）

```python
# app/crud/crud_session.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from app.models import LiveSession
from app.core.exceptions import DatabaseIntegrityException, DatabaseOperationException
import logging
import uuid

logger = logging.getLogger(__name__)

async def create(db: AsyncSession, obj_in: dict) -> LiveSession:
    """
    创建直播会话（CRUD 层 - 学院派实现）
    
    职责：
    1. 创建数据库记录
    2. 处理事务（commit/rollback）
    3. 处理数据库异常
    4. 记录错误日志
    
    不做：
    1. 业务逻辑校验（由 Service 层负责）
    2. 权限检查（由 Service 层负责）
    """
    # 提前提取日志所需变量（安全规范）
    session_id_log = obj_in.get('id', uuid.uuid4())
    room_id_log = obj_in.get('room_id')
    
    try:
        # 创建 ORM 对象
        db_session = LiveSession(**obj_in)
        db.add(db_session)
        
        # 提交事务
        await db.commit()
        await db.refresh(db_session)
        
        logger.info(
            f"创建会话成功：session_id={db_session.id}, "
            f"room_id={room_id_log}"
        )
        
        return db_session
        
    except IntegrityError as e:
        # 数据库完整性错误（如唯一键冲突）
        await db.rollback()
        logger.error(
            f"创建会话失败（完整性错误）：session_id={session_id_log}, "
            f"room_id={room_id_log}, error={e}",
            exc_info=True
        )
        raise DatabaseIntegrityException("创建会话时发生唯一键冲突")
        
    except Exception as e:
        # 其他数据库错误
        await db.rollback()
        logger.error(
            f"创建会话失败（未知DB错误）：session_id={session_id_log}, "
            f"room_id={room_id_log}, error={e}",
            exc_info=True
        )
        raise DatabaseOperationException(f"数据库操作失败: {e}")
```

### 7.3 CRUD 示例：搜索房间

```python
# app/crud/crud_room.py（扩展现有 CRUD）
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func
from app.models import LiveRoom
from app.core.exceptions import DatabaseOperationException
from typing import Optional
import logging

logger = logging.getLogger(__name__)

async def list_with_search(
    db: AsyncSession,
    filters: dict = None,
    page: int = 1,
    size: int = 10,
    sort: Optional[str] = None
) -> dict:
    """
    搜索房间列表（CRUD 层 - 学院派实现）
    
    职责：
    1. 执行数据库查询
    2. 支持 ID 精确匹配和标题模糊匹配
    3. 支持可配置排序
    4. 分页返回
    
    不做：
    1. 业务逻辑（由 Service 层负责）
    """
    try:
        # 构建基础查询
        query = select(LiveRoom)
        
        # 添加搜索条件
        if filters and 'id_or_title' in filters:
            field, value = filters['id_or_title']
            
            if field == 'id':
                # UUID 精确匹配
                query = query.where(LiveRoom.id == value)
            elif field == 'title':
                # 标题模糊匹配
                query = query.where(LiveRoom.title.ilike(value))
        
        # 计算总数
        count_query = select(func.count()).select_from(query.subquery())
        result = await db.execute(count_query)
        total = result.scalar()
        
        # 分页
        query = query.offset((page - 1) * size).limit(size)
        
        # 排序处理
        if sort:
            # 解析 sort 参数（格式：field:direction）
            sort_parts = sort.split(':')
            if len(sort_parts) == 2:
                field_name, direction = sort_parts[0], sort_parts[1].upper()
                # 验证字段名（仅允许安全字段）
                if hasattr(LiveRoom, field_name) and direction in ('ASC', 'DESC'):
                    field = getattr(LiveRoom, field_name)
                    if direction == 'DESC':
                        query = query.order_by(field.desc())
                    else:
                        query = query.order_by(field.asc())
                else:
                    # 无效的排序参数，使用默认排序
                    query = query.order_by(LiveRoom.created_at.desc())
            else:
                # 无效格式，使用默认排序
                query = query.order_by(LiveRoom.created_at.desc())
        else:
            # 默认排序
            query = query.order_by(LiveRoom.created_at.desc())
        
        # 执行查询
        result = await db.execute(query)
        rooms = result.scalars().all()
        
        return {
            "total": total,
            "page": page,
            "size": size,
            "items": rooms
        }
        
    except Exception as e:
        logger.error(f"搜索房间失败：{e}", exc_info=True)
        raise DatabaseOperationException(f"数据库查询失败: {e}")
```

---

## 8. 认证与权限体系

### 8.1 认证要求

**所有 API 接口都需要 JWT Token 认证：**
* 请求头必须包含：`Authorization: Bearer <JWT_TOKEN>`
* Token 由用户服务颁发，包含用户身份信息（`sub = users.public_id`, `role = user_role`）
* 未认证的请求返回 401 状态码

### 8.2 权限控制

**Import Session 权限规则**：
* 用户只能在自己创建的房间（`room.user_id == current_user.public_id`）导入会话
* 验证逻辑在 **Service 层** 实现，失败时抛出 `PermissionDeniedException`

**Search 权限规则**：
* 所有登录用户可搜索所有房间
* 支持按 `user_id` 过滤（仅查看自己的房间）

**Batch Import 权限规则**：
* 所有登录用户可调用批量导入
* 创建的房间归属当前用户（`user_id = current_user.public_id`）
* 若复用现有房间，必须验证权限（`room.user_id == current_user.public_id`）

### 8.3 认证失败处理

| HTTP状态码 | 错误码 | 说明 | 处理建议 |
|-----------|--------|------|----------|
| 401 | 401001 | 认证凭证缺失 | 检查 Authorization 头 |
| 401 | 401002 | 认证凭证无效 | 重新登录获取 Token |
| 401 | 401003 | 认证凭证已过期 | 刷新 Token 或重新登录 |
| 403 | 3002 | 权限不足 | 检查用户对资源的归属权限 |

---

## 9. 日志与异常处理方案（学院派实现）

### 9.1 日志规范（分层记录）

**CRUD 层日志**（`logger.error`）：
* 记录数据库异常（`IntegrityError`、`DatabaseOperationException`）
* 必须包含 `exc_info=True` 以记录完整堆栈
* 示例：`logger.error(f"创建会话失败：session_id={id}, error={e}", exc_info=True)`

**Service 层日志**（`logger.info` / `logger.warning`）：
* `INFO`：记录关键业务操作（导入成功、搜索完成）
* `WARNING`：记录业务异常（权限不足、参数非法）
* 示例：`logger.info(f"导入会话成功：session_id={id}, public_id={public_id}")`

**API 层日志**（`logger.warning`）：
* 记录捕获到的业务异常（在 `except` 块中）
* 示例：`logger.warning(f"参数错误：public_id={public_id}, error={e.message}")`

### 9.2 异常处理流程（学院派三层模式）

**1. CRUD 层**：
```python
async def create(db: AsyncSession, obj_in: dict):
    # 提前提取日志变量
    obj_id_log = obj_in.get('id')
    
    try:
        db_obj = Model(**obj_in)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    except IntegrityError as e:
        await db.rollback()
        logger.error(f"DB错误: id={obj_id_log}, error={e}", exc_info=True)
        raise DatabaseIntegrityException("唯一键冲突")
    except Exception as e:
        await db.rollback()
        logger.error(f"未知DB错误: id={obj_id_log}, error={e}", exc_info=True)
        raise DatabaseOperationException(f"数据库操作失败: {e}")
```

**2. Service 层**：
```python
async def import_create_session(self, room_id, public_id, session_in):
    # 业务校验
    room = await crud_room.get(self.db, id=room_id)
    if not room:
        raise RoomNotFoundException(f"房间 {room_id} 不存在")
    
    if room.user_id != public_id:
        raise PermissionDeniedException("无权操作")
    
    # 调用 CRUD（不捕获异常，任其上浮）
    return await crud_session.create(self.db, obj_in=session_data)
```

**3. API 层**：
```python
@router.post("/rooms/{room_id}/sessions/import")
async def import_session(
    room_id: UUID,
    payload: SessionImportCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    # 提取日志变量（从 JWT 提取用户公开标识）
    public_id = UUID(current_user.get("public_id"))
    
    try:
        service = SessionImportService(db)
        session = await service.import_create_session(
            room_id=room_id,
            public_id=public_id,
            session_in=payload
        )
        return success_response(data=session)
    
    except RoomNotFoundException as e:
        logger.warning(f"资源未找到: room_id={room_id}, error={e}")
        return JSONResponse(
            status_code=404,
            content=error_response(code=2001, message="房间不存在")
        )
    
    except PermissionDeniedException as e:
        logger.warning(f"权限不足: public_id={public_id}, room_id={room_id}")
        return JSONResponse(
            status_code=403,
            content=error_response(code=3002, message="权限不足")
        )
    
    except InvalidParameterException as e:
        logger.warning(f"参数错误: {e.message}")
        return JSONResponse(
            status_code=400,
            content=error_response(code=e.code, message=e.message)
        )
    
    except DatabaseIntegrityException as e:
        logger.warning(f"数据冲突: {e.message}")
        return JSONResponse(
            status_code=400,
            content=error_response(code=4001, message="数据冲突或参数错误")
        )
    
    except Exception as e:
        logger.error(f"未知错误: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content=error_response(code=1000, message="服务器内部错误")
        )
```

---

## 10. 安全规范

### 10.1 JWT 认证安全
* **密钥管理**: `JWT_SECRET_KEY` 必须与用户服务保持一致
* **算法选择**: 使用 HS256 算法进行 Token 签名
* **过期时间**: Token 过期时间设置为 30 分钟
* **刷新机制**: 支持 Token 刷新，避免频繁重新登录

### 10.2 权限验证安全
* **用户隔离**: 严格验证用户对资源的访问权限（`room.user_id == current_user.public_id`）
* **操作审计**: 记录所有导入和搜索操作日志
* **异常处理**: 认证失败时返回统一的错误响应

### 10.3 文件上传安全
* **文件类型限制**: 仅允许 `.csv` 和 `.xlsx` 格式
* **文件大小限制**: 建议限制在 10MB 以内（通过 Nginx `client_max_body_size` 配置）
* **内容校验**: 验证文件编码和必需列，防止注入攻击
* **XSS 防护**: 前端必须对 CSV 中的文本内容进行 HTML 转义

### 10.4 安全异步异常处理（关键）
**必须**在 **API 层**和 **CRUD 层**的 `try...except` 块中遵循以下原则：
* **必须**在 `try` 之前提取所有用于 `except` 块日志记录的变量（如 `public_id`, `room_id`）
* **严禁**在 `except` 块中访问可能已失效的数据库会话或 ORM 对象属性来获取日志信息

**示例**：
```python
# ✅ 正确做法
public_id_log = UUID(current_user.get("public_id"))
room_id_log = room_id

try:
    # 数据库操作
    pass
except Exception as e:
    logger.error(f"错误：public_id={public_id_log}, room_id={room_id_log}, error={e}")

# ❌ 错误做法
try:
    # 数据库操作
    pass
except Exception as e:
    # 此时 current_user 可能已失效
    logger.error(f"错误：public_id={current_user.get('public_id')}, error={e}")
```

---

## 11. 前后端兼容性说明

### 11.1 API 兼容性保证

**不破坏现有调用**：
* `POST /api/v1/rooms/{room_id}/sessions` - 保持不变，`playback_url` 必须为 NULL
* `GET /api/v1/rooms` - 不传 `q` 参数时行为完全一致
* `PATCH /api/v1/sessions/{session_id}` - 保持不变，支持更新 `playback_url`

**新增端点**：
* `POST /api/v1/rooms/{room_id}/sessions/import` - 新增，不影响旧端点
* `POST /api/v1/rooms/import/batch` - 新增，不影响旧端点
* `GET /api/v1/rooms?q=<keyword>` - 扩展可选参数，旧调用不受影响

### 11.2 数据库兼容性

* 无 Schema 变更
* 无数据迁移
* 无索引变更

### 11.3 前端适配建议

**Import Session**：
* 前端需判断创建类型（普通创建 vs 导入创建）
* 导入创建时调用 `/sessions/import` 端点，并提供 `playback_url`

**Search**：
* 在列表页面添加搜索框，用户输入关键词
* 调用 `GET /api/v1/rooms?q=<keyword>` 进行搜索
* 保持分页逻辑不变

**Batch Import**：
* 添加文件上传组件（支持 `.csv` 和 `.xlsx`）
* 提供 dry-run 模式（先校验，再确认）
* 显示导入报告（成功数、失败数、错误详情）

---

## 12. 扩展性说明

### 12.1 可扩展点

**导入来源追踪**（未来扩展）：
* 新增 `live_sessions.source_type` (ENUM: 'native', 'import', 'api')
* 新增 `live_sessions.external_ref` (VARCHAR: 外部系统 ID)

**更多文件格式支持**（未来扩展）：
* 支持 JSON 格式批量导入
* 支持从 URL 导入（直接提供文件 URL）

**搜索功能增强**（未来扩展）：
* 支持按创建时间、状态等字段筛选
* 支持多字段组合搜索
* 支持全文搜索（基于 Elasticsearch）

### 12.2 性能优化建议

**批量导入优化**：
* 对于大文件（>1000 行），建议使用异步任务队列（Celery）处理
* 使用批量插入（`bulk_insert_mappings`）替代逐行插入
* 添加进度条支持（通过 WebSocket 或轮询）

**搜索优化**：
* 为 `live_rooms.title` 添加全文索引
* 使用缓存（Redis）存储热门搜索结果
* 实现搜索词高亮

---

## 13. 测试策略

### 13.1 单元测试（新增）

**测试文件**：
* `tests/test_session_import.py` - 导入会话功能测试
* `tests/test_room_search.py` - 搜索功能测试
* `tests/test_batch_import.py` - 批量导入功能测试

**测试用例**：
1. **Import Session**:
   * 成功：创建时携带 `playback_url`，直接保存
   * 失败：`status` 不在 `finished`/`ready`
   * 失败：`playback_url` 缺失或格式错误
   * 失败：房间不存在
   * 失败：权限不足（非房间所有者）

2. **Search**:
   * 成功：`q` 为 UUID，精确匹配
   * 成功：`q` 为文本，标题模糊匹配
   * 成功：不传 `q`，返回所有房间（回归测试）
   * 失败：`q` 长度超过限制

3. **Batch Import**:
   * 成功：dry_run 模式，不落库，仅返回校验报告
   * 成功：apply 模式，成功落库并返回 `room_id`/`session_id`
   * 失败：文件格式错误（非 CSV/Excel）
   * 失败：必需列缺失（包括缺少逻辑字段 `room_title`/`playback_url`，或缺少其等价中文表头如 `标题`、`播放url`（以及历史模板中的 `播放url1`））
   * 失败：某行数据错误，其他行正常（行级隔离）
   * 成功：CSV 编码容错（utf-8-sig/utf-8/gbk）

### 13.2 集成测试

**测试场景**：
* 完整流程：创建房间 → 导入会话 → 搜索验证 → 批量导入验证
* 权限验证：用户 A 无法在用户 B 的房间导入会话
* 并发测试：多用户同时批量导入，验证数据一致性

### 13.3 性能测试

**测试指标**：
* Import Session: 单次创建 < 200ms
* Search: 搜索响应 < 100ms（10000 条数据）
* Batch Import: 100 行导入 < 5s（dry_run），< 10s（apply）

---

## 14. 附录

### 附录 A: 错误码汇总

| 错误码 | HTTP 状态码 | 说明 | 场景 |
|--------|-----------|------|------|
| 200 | 200 | 成功 | 所有成功请求 |
| 1000 | 500 | 服务器内部错误 | 未知异常 |
| 2001 | 404 | 资源不存在 | 房间不存在 |
| 3002 | 403 | 权限不足 | 非房间所有者 |
| 4001 | 400 | 参数校验失败 | status 不合法 |
| 4002 | 400 | 参数校验失败 | 必需列缺失 |
| 401001 | 401 | 认证凭证缺失 | 未提供 Token |
| 401002 | 401 | 认证凭证无效 | Token 格式错误 |
| 401003 | 401 | 认证凭证已过期 | Token 过期 |

### 附录 B: CSV 文件模板

```csv
room_title,playback_url,room_description,session_title,start_time,end_time,status,cover_url
产品发布会,https://cdn.example.com/video1.m3u8,新品发布,产品发布会回放,2025-07-07T18:00:00Z,2025-07-07T19:00:00Z,finished,https://cdn.example.com/cover1.jpg
技术分享会,https://cdn.example.com/video2.m3u8,技术交流,技术分享会回放,2025-07-08T14:00:00Z,2025-07-08T15:30:00Z,finished,https://cdn.example.com/cover2.jpg
```
> 说明：本模板展示的是**内部逻辑字段名**（英文表头）的标准批量导入格式。对于直接使用微赞后台导出的中文表头文件（如 `直播间ID, 标题, 直播间url, 播放url, 封面图片, ...`，以及历史导出格式中可能出现的 `播放url1`），应在 Service 层先按“标题 → room_title、播放url（以及历史模板中的 `播放url1`）→ playback_url、封面图片 → cover_url”的规则做表头映射后，再套用此模板的字段语义。

### 附录 C: 开发实施计划

**Phase 1: Import Session（1 周）**
1. 定义 Schema 和异常类
2. 实现 CRUD 层（复用现有 `create`）
3. 实现 Service 层（权限验证、参数校验）
4. 实现 API 层（异常捕获、响应格式）
5. 编写单元测试和集成测试

**Phase 2: Search（1 周）**
1. 扩展 CRUD 层（新增 `list_with_search`）
2. 扩展 Service 层（搜索逻辑、UUID 识别）
3. 扩展 API 层（新增 `q` 参数）
4. 编写测试用例（精确匹配、模糊匹配、回归测试）

**Phase 3: Batch Import（2 周）**
1. 实现文件解析（CSV/Excel、编码探测）
2. 实现 Service 层（逐行处理、行级事务隔离）
3. 实现 API 层（文件上传、导入报告）
4. 编写测试用例（dry_run、apply、容错、并发）
5. 性能优化（批量插入、异步任务）

**Phase 4: 测试与部署（1 周）**
1. 完整集成测试
2. 性能测试
3. 文档更新
4. 部署上线

---

**文档结束**

