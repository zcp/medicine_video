# 用户与专家模块新增 API 设计文档  
## 个人直播间列表与全量专家查询接口

> **生成时间**：2026-05-14    
> **版本**：V1.0（初稿）  
> **状态**：设计定稿  
> **核心需求来源**：个人直播间列表API需求分析_2026-05-13 + 专家全量列表API需求分析_2026-05-13  
> **设计目标**：为"我的直播"页面和专家列表页提供稳定的用户数据隔离与全量查询接口，同时与现有管理员接口保持兼容。

---

## 0. 文档结构说明（阅读指南）

本文档采用有机整合的方式，将两个新增 API 需求（个人直播间列表、专家全量列表）整合为统一的系统设计文档，保持与直播核心功能设计文档 V6 一致的风格与规范。

**重点章节**：
- **第 1 节**：最终路由表（统一版本）
- **第 2 节**：最终数据库 DDL（新增索引建议）
- **第 3 节**：开发规范与安全约束
- **第 4 节**：API 接口规范（完整的端点定义、请求/响应示例、错误码）
- **第 5 节**：测试用例与验收标准
- **第 6 节**：兼容性与部署策略

---

## 1. 最终路由表（统一版）

| Domain | Endpoint | Method | Auth | Roles | Request Schema | Response Schema | Error Codes | Source | Notes |
| ------ | -------- | ------ | ---- | ----- | -------------- | --------------- | ----------- | ------ | ----- |
| rooms | /api/v1/users/me/rooms | GET | JWT必需 | all | paging+filter | Room[] | 401/4001/5001 | 本文 | 用户个人直播间分页列表，仅返回当前登录用户创建的直播间 |
| experts | /api/v1/experts | GET | JWT可选 | all | paging+filter | Expert[] | 4001/429/5001 | 本文 | 全量专家分页查询，支持匿名访问 |

> **说明**：  
> - `users/me/rooms`：鉴权必需（`JWT Required`），确保用户数据隔离。  
> - `experts`：鉴权可选（`JWT Optional`），匿名用户与登录用户有不同的速率限制与可见字段集。

---

## 2. 最终数据库设计与索引建议

### 2.1 数据库现状回顾

#### live_rooms 表（已有）

```sql
CREATE TABLE live_rooms (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    parent_room_id UUID NULL REFERENCES live_rooms(id) ON DELETE SET NULL,
    title VARCHAR(100) NOT NULL,
    description TEXT,
    cover_url VARCHAR(255),
    stream_key VARCHAR(255) NOT NULL UNIQUE,
    is_private BOOLEAN DEFAULT false,
    record_by_default BOOLEAN DEFAULT true,
    category_id UUID NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_live_rooms_user_id ON live_rooms(user_id);
```

#### live_sessions 表（已有）

```sql
CREATE TABLE live_sessions (
    id UUID PRIMARY KEY,
    room_id UUID NOT NULL REFERENCES live_rooms(id) ON DELETE CASCADE,
    status live_session_status NOT NULL,
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ,
    video_id UUID NULL UNIQUE,
    playback_url VARCHAR(1024) NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_live_sessions_on_room_id ON live_sessions(room_id);
```

#### session_statistics 表（已有）

```sql
CREATE TABLE session_statistics (
    id UUID PRIMARY KEY,
    session_id UUID NOT NULL UNIQUE REFERENCES live_sessions(id) ON DELETE CASCADE,
    peak_viewer_count INT DEFAULT 0,
    total_viewer_count BIGINT DEFAULT 0,
    total_like_count BIGINT DEFAULT 0,
    total_share_count BIGINT DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

#### experts 表（新增）

本接口假设 `experts` 表已存在，结构如下：

```sql
CREATE TABLE experts (
    id UUID PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    title VARCHAR(100),
    hospital VARCHAR(255),
    department VARCHAR(100),
    expertise_areas TEXT,
    bio TEXT,
    avatar_url VARCHAR(255),
    is_featured BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    sort_order INT NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

### 2.2 新增索引建议

#### 为 GET /api/v1/users/me/rooms 优化

```sql
-- 用户隔离索引，支持状态过滤与分页排序
CREATE INDEX idx_live_rooms_user_active_created_id 
    ON live_rooms(user_id, is_active, created_at DESC, id ASC);

-- 支持分类筛选
CREATE INDEX idx_live_rooms_user_category_created 
    ON live_rooms(user_id, category_id, created_at DESC);

-- 关键词全文搜索（仅 PostgreSQL）
CREATE INDEX idx_live_rooms_title_desc_gin 
    ON live_rooms USING GIN (to_tsvector('chinese', title || ' ' || COALESCE(description, '')));
```

#### 为 GET /api/v1/experts 优化

```sql
-- 专家列表默认排序支持
CREATE INDEX idx_experts_active_sort_created_id 
    ON experts(is_active, sort_order ASC, created_at DESC, id ASC);

-- 科室与医院组合筛选
CREATE INDEX idx_experts_active_dept_hospital 
    ON experts(is_active, department, hospital);

-- 关键词全文搜索（仅 PostgreSQL）
CREATE INDEX idx_experts_name_bio_gin 
    ON experts USING GIN (to_tsvector('chinese', name || ' ' || COALESCE(title, '') || ' ' || COALESCE(bio, '')));
```

#### 为统计聚合优化

```sql
-- 支持个人直播间统计聚合
CREATE INDEX idx_sessions_room_created 
    ON live_sessions(room_id, created_at DESC);

CREATE INDEX idx_session_stats_room_total_viewers 
    ON session_statistics(session_id, total_viewer_count)
    INCLUDE (peak_viewer_count, total_like_count);
```

### 2.3 聚合字段说明

在 `/api/v1/users/me/rooms` 列表响应中，以下字段通过 SQL 聚合或应用层计算得出：

- `session_count`：按 `room_id` 统计 `live_sessions` 行数。
- `last_session_at`：按 `room_id` 取 `live_sessions.created_at` 的最大值。
- `total_viewers`：按 `room_id` 求和所有关联 `session_statistics.total_viewer_count`。

**推荐实现方式**：
1. 在查询直播间列表时，使用 LEFT JOIN + GROUP BY 一次性获取统计数据（避免 N+1 查询）。
2. 为热点数据（`session_count`、`total_viewers`）引入缓存，异步更新。

---

## 3. 开发规范与安全约束

### 3.1 编码与项目规范

**编码标准**：遵循直播核心功能设计文档的规范：
- Python 3.8 或更高版本
- PEP 8 代码风格，使用 4 个空格缩进
- 类名 PascalCase，函数/变量名 snake_case，常量 UPPER_SNAKE_CASE

**项目结构**：遵循模块化设计原则，确保职责单一、高内聚、低耦合。

### 3.2 日志与异常处理规范

#### 日志规范

- **日志级别**：ERROR、WARNING、INFO、DEBUG
- **标准字段**：时间戳、日志级别、模块名、函数名、行号、消息内容
- **脱敏原则**：所有敏感信息（JWT Token、密码、API密钥）必须脱敏
- **关键日志点**：
  - 用户认证请求与结果
  - 直播间查询与过滤条件
  - 专家列表聚合操作
  - 所有捕获到的异常

#### 异常处理规范

- **统一处理**：使用异常处理中间件捕获所有未处理异常
- **自定义异常类**：区分系统异常、业务异常、参数异常、权限异常
- **错误响应格式**：
  ```json
  {
    "code": 401,
    "message": "未授权访问，请登录",
    "data": null,
    "timestamp": "2026-05-14T10:30:00Z",
    "request_id": "2be2f6d7-4f0d-4fce-8f88-63bb78807e20"
  }
  ```

### 3.3 配置与安全规范

#### 环境变量管理

- **配置源**：所有配置必须通过环境变量管理，禁止硬编码敏感信息
- **配置模板**：提供 `.env.example` 作为模板
- **环境隔离**：开发 `.env`、Docker `.env.docker`、生产 `.env.production`
- **验证**：生产环境启动时必须验证所有必需配置项

#### 敏感信息保护

- **禁止硬编码**：数据库密码、JWT密钥、API密钥必须从环境变量读取
- **默认值**：敏感配置的默认值必须为空字符串
- **配置集中管理**：在 `app/core/config.py` 中统一管理所有配置

#### CORS 配置外部化

```python
# .env.example
CORS_ORIGINS=http://localhost:5175,http://localhost:3000

# 生产环境
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

**警告**：生产环境禁止使用 `*` 通配符，必须指定具体允许域名。

### 3.4 权限与数据隔离

#### /api/v1/users/me/rooms（用户个人直播间）

- **鉴权**：JWT 必需，仅登录用户可访问
- **数据隔离**：返回的直播间 `user_id` 必须与当前登录用户 ID 一致
- **权限验证**：应用层检查 `room.user_id == current_user.id`，不允许跨用户查询
- **敏感字段**：`stream_key`（推流密钥）仅对所有者可见

#### /api/v1/experts（专家全量列表）

- **鉴权**：JWT 可选，支持匿名访问
- **速率限制**：
  - 匿名用户：60 req/min/IP
  - 登录用户：300 req/min/user
- **可见字段**：所有公开字段都对匿名用户可见
- **敏感字段隐藏**：内部审核记录、风控标签禁止暴露

---

## 4. API 接口规范

### 4.1 GET /api/v1/users/me/rooms - 用户个人直播间列表

#### 4.1.1 接口概述

返回当前登录用户创建的所有直播间，支持分页、搜索、排序、过滤。

#### 4.1.2 请求规范

**请求方法**：`GET`

**请求路由**：`/api/v1/users/me/rooms`

**鉴权**：JWT 必需

**请求头**：

```
Authorization: Bearer <JWT_TOKEN>
Accept: application/json
X-Request-Id: <UUID>（可选）
```

**查询参数**：

| 参数 | 类型 | 默认值 | 范围 | 说明 |
|------|------|--------|------|------|
| page | integer | 1 | ≥1 | 页码 |
| size | integer | 20 | 1-100 | 每页条数 |
| keyword | string | - | max=200 | 搜索标题与描述，模糊匹配 |
| category_id | UUID | - | - | 分类筛选 |
| is_private | boolean | - | true/false | 隐私状态筛选 |
| status | string | - | active/inactive | 直播间启用状态 |
| sort | string | created_at:desc,id:asc | - | 排序表达式，支持 created_at/updated_at |
| cursor | string | - | - | 游标分页（推荐用于深翻页） |

**示例请求**：

```bash
# 获取第一页，每页20条
curl -H "Authorization: Bearer eyJhbGc..." \
  "https://api.example.com/api/v1/users/me/rooms?page=1&size=20"

# 搜索与过滤
curl -H "Authorization: Bearer eyJhbGc..." \
  "https://api.example.com/api/v1/users/me/rooms?keyword=科普&is_private=false&sort=created_at:desc"

# 使用游标分页
curl -H "Authorization: Bearer eyJhbGc..." \
  "https://api.example.com/api/v1/users/me/rooms?size=20&cursor=eyJpZCI6InV1aWQtMTAwMSJ9"
```

#### 4.1.3 成功响应规范

**HTTP 状态码**：`200 OK`

**响应头**：

```
Content-Type: application/json
X-Request-Id: <UUID>
X-RateLimit-Limit: 300
X-RateLimit-Remaining: 299
```

**响应体**：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "items": [
      {
        "id": "8a01f0e2-f4f6-4af4-9f9c-77ef8c93e3d1",
        "user_id": "user-123-uuid",
        "title": "周一医学科普直播",
        "description": "今天讨论心脏健康知识",
        "cover_url": "https://cdn.example.com/cover/abc123.jpg",
        "stream_key": "example_stream_key_placeholder",
        "is_private": false,
        "record_by_default": true,
        "category_id": "category-uuid-1",
        "is_active": true,
        "created_at": "2026-05-13T00:00:00Z",
        "updated_at": "2026-05-13T10:30:00Z",
        "session_count": 3,
        "last_session_at": "2026-05-13T09:00:00Z",
        "total_viewers": 1250
      },
      {
        "id": "8a01f0e2-f4f6-4af4-9f9c-77ef8c93e3d2",
        "user_id": "user-123-uuid",
        "title": "体检结果解读",
        "description": "为大家解读常见体检项目",
        "cover_url": "https://cdn.example.com/cover/def456.jpg",
        "stream_key": "example_stream_key_placeholder",
        "is_private": true,
        "record_by_default": false,
        "category_id": "category-uuid-2",
        "is_active": true,
        "created_at": "2026-05-10T12:00:00Z",
        "updated_at": "2026-05-13T08:00:00Z",
        "session_count": 1,
        "last_session_at": "2026-05-10T14:00:00Z",
        "total_viewers": 320
      }
    ],
    "total": 8,
    "page": 1,
    "size": 20,
    "has_more": false,
    "next_cursor": null
  },
  "timestamp": "2026-05-13T10:30:00Z",
  "request_id": "2be2f6d7-4f0d-4fce-8f88-63bb78807e20"
}
```

**响应字段说明**：

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 直播间 ID |
| user_id | UUID | 所有者用户 ID |
| title | string | 直播间名称 |
| description | string | 直播间描述 |
| cover_url | string | 封面 URL |
| stream_key | string | 推流密钥（仅所有者可见） |
| is_private | boolean | 是否私密 |
| record_by_default | boolean | 是否默认录制 |
| category_id | UUID | 分类 ID |
| is_active | boolean | 是否启用 |
| created_at | ISO 8601 | 创建时间 |
| updated_at | ISO 8601 | 更新时间 |
| session_count | integer | 直播场次总数 |
| last_session_at | ISO 8601 | 最后一次直播时间 |
| total_viewers | integer | 所有场次观看人数总和 |

#### 4.1.4 错误响应规范

| HTTP 码 | 业务 code | 场景 | 示例响应 |
|--------|----------|------|---------|
| 401 | 4011 | 未登录 | `{"code":4011,"message":"未授权访问，请登录"}` |
| 400 | 4001 | 参数验证失败 | `{"code":4001,"message":"size 超过最大值 100"}` |
| 429 | 4291 | 请求频率超限 | `{"code":4291,"message":"请求过于频繁，请稍候"}` |
| 500 | 1002 | 数据库异常 | `{"code":1002,"message":"数据库查询异常"}` |
| 500 | 5001 | 通用服务器错误 | `{"code":5001,"message":"服务器内部错误"}` |

**错误响应示例**：

```json
{
  "code": 4001,
  "message": "size 超过最大值 100",
  "data": null,
  "timestamp": "2026-05-13T10:30:00Z",
  "request_id": "2be2f6d7-4f0d-4fce-8f88-63bb78807e20"
}
```

#### 4.1.5 OpenAPI v3 规范片段

```yaml
openapi: 3.0.3
info:
  title: User Rooms API
  version: 1.0.0
paths:
  /api/v1/users/me/rooms:
    get:
      summary: 当前用户的直播间分页列表
      security:
        - bearerAuth: []
      parameters:
        - name: page
          in: query
          schema:
            type: integer
            minimum: 1
            default: 1
        - name: size
          in: query
          schema:
            type: integer
            minimum: 1
            maximum: 100
            default: 20
        - name: keyword
          in: query
          schema:
            type: string
            maxLength: 200
        - name: category_id
          in: query
          schema:
            type: string
            format: uuid
        - name: is_private
          in: query
          schema:
            type: boolean
        - name: status
          in: query
          schema:
            type: string
            enum: [active, inactive]
        - name: sort
          in: query
          schema:
            type: string
            example: created_at:desc,id:asc
        - name: cursor
          in: query
          schema:
            type: string
      responses:
        '200':
          description: 查询成功
          content:
            application/json:
              schema:
                type: object
                properties:
                  code:
                    type: integer
                    example: 200
                  message:
                    type: string
                    example: success
                  data:
                    type: object
                    properties:
                      items:
                        type: array
                      total:
                        type: integer
                      page:
                        type: integer
                      size:
                        type: integer
                      has_more:
                        type: boolean
                      next_cursor:
                        type: string
                        nullable: true
        '401':
          description: 未授权
        '400':
          description: 参数错误
        '429':
          description: 请求超限
        '500':
          description: 服务器错误
      tags:
        - Rooms

components:
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
```

---

### 4.2 GET /api/v1/experts - 专家全量列表

#### 4.2.1 接口概述

返回全量可展示专家列表，支持分页、搜索、排序、过滤。匿名用户与登录用户共享同一接口，但有不同的速率限制。

#### 4.2.2 请求规范

**请求方法**：`GET`

**请求路由**：`/api/v1/experts`

**鉴权**：JWT 可选

**请求头**：

```
Authorization: Bearer <JWT_TOKEN>（可选）
Accept: application/json
X-Request-Id: <UUID>（可选）
```

**查询参数**：

| 参数 | 类型 | 默认值 | 范围 | 说明 |
|------|------|--------|------|------|
| page | integer | 1 | ≥1 | 页码 |
| size | integer | 50 | 1-100 | 每页条数 |
| keyword | string | - | max=200 | 搜索姓名、医院、科室、简介 |
| department | string | - | max=100 | 科室筛选 |
| hospital | string | - | max=200 | 医院筛选 |
| is_active | boolean | true | - | 启用状态筛选 |
| sort | string | sort_order:asc,created_at:desc,id:asc | - | 排序表达式 |
| cursor | string | - | - | 游标分页 |

**示例请求**：

```bash
# 获取第一页，每页50条
curl "https://api.example.com/api/v1/experts?page=1&size=50"

# 搜索与过滤
curl "https://api.example.com/api/v1/experts?keyword=心脏&department=心内科"

# 登录用户请求（可获得个性化字段）
curl -H "Authorization: Bearer eyJhbGc..." \
  "https://api.example.com/api/v1/experts?keyword=心脏&page=1"
```

#### 4.2.3 成功响应规范

**HTTP 状态码**：`200 OK`

**响应头**：

```
Content-Type: application/json
X-Request-Id: <UUID>
X-RateLimit-Limit: 60（匿名）/ 300（登录）
X-RateLimit-Remaining: 59
```

**响应体**：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "items": [
      {
        "id": "expert-uuid-001",
        "name": "李医生",
        "title": "主任医师",
        "hospital": "北京协和医院",
        "department": "心内科",
        "expertise_areas": "心脏病诊断与治疗",
        "bio": "从事心脏病诊疗工作20年，擅长冠心病、心衰的诊疗",
        "avatar_url": "https://cdn.example.com/avatar/expert001.jpg",
        "is_featured": true,
        "is_active": true,
        "sort_order": 1,
        "created_at": "2026-01-15T00:00:00Z",
        "updated_at": "2026-05-13T10:30:00Z"
      },
      {
        "id": "expert-uuid-002",
        "name": "王医生",
        "title": "副主任医师",
        "hospital": "北京医院",
        "department": "呼吸科",
        "expertise_areas": "肺炎、哮喘治疗",
        "bio": "呼吸系统疾病专家",
        "avatar_url": "https://cdn.example.com/avatar/expert002.jpg",
        "is_featured": false,
        "is_active": true,
        "sort_order": 2,
        "created_at": "2026-02-20T00:00:00Z",
        "updated_at": "2026-05-10T15:20:00Z"
      }
    ],
    "total": 400,
    "page": 1,
    "size": 50,
    "has_more": true,
    "next_cursor": "eyJpZCI6ImV4cGVydC11dWlkLTAyNyJ9"
  },
  "timestamp": "2026-05-13T10:30:00Z",
  "request_id": "2be2f6d7-4f0d-4fce-8f88-63bb78807e20"
}
```

**响应字段说明**：

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 专家 ID |
| name | string | 姓名 |
| title | string | 职称（如主任医师） |
| hospital | string | 医院名称 |
| department | string | 科室 |
| expertise_areas | string | 擅长领域 |
| bio | string | 个人简介 |
| avatar_url | string | 头像 URL |
| is_featured | boolean | 是否精选专家 |
| is_active | boolean | 是否启用 |
| sort_order | integer | 排序权重（用于精选排序） |
| created_at | ISO 8601 | 创建时间 |
| updated_at | ISO 8601 | 更新时间 |

#### 4.2.4 错误响应规范

| HTTP 码 | 业务 code | 场景 | 示例响应 |
|--------|----------|------|---------|
| 400 | 4001 | 参数验证失败 | `{"code":4001,"message":"size 超过最大值 100"}` |
| 429 | 4291 | 请求频率超限 | `{"code":4291,"message":"请求过于频繁"}` |
| 500 | 1002 | 数据库异常 | `{"code":1002,"message":"数据库查询异常"}` |
| 500 | 5001 | 通用服务器错误 | `{"code":5001,"message":"服务器内部错误"}` |

**错误响应示例**：

```json
{
  "code": 4001,
  "message": "size 超过最大值 100",
  "data": null,
  "timestamp": "2026-05-13T10:30:00Z",
  "request_id": "2be2f6d7-4f0d-4fce-8f88-63bb78807e20"
}
```

#### 4.2.5 OpenAPI v3 规范片段

```yaml
openapi: 3.0.3
info:
  title: Experts API
  version: 1.0.0
paths:
  /api/v1/experts:
    get:
      summary: 全量专家分页查询
      security:
        - bearerAuth: []
      parameters:
        - name: page
          in: query
          schema:
            type: integer
            minimum: 1
            default: 1
        - name: size
          in: query
          schema:
            type: integer
            minimum: 1
            maximum: 100
            default: 50
        - name: keyword
          in: query
          schema:
            type: string
            maxLength: 200
        - name: department
          in: query
          schema:
            type: string
            maxLength: 100
        - name: hospital
          in: query
          schema:
            type: string
            maxLength: 200
        - name: is_active
          in: query
          schema:
            type: boolean
            default: true
        - name: sort
          in: query
          schema:
            type: string
            example: sort_order:asc,created_at:desc,id:asc
        - name: cursor
          in: query
          schema:
            type: string
      responses:
        '200':
          description: 查询成功
          content:
            application/json:
              schema:
                type: object
                properties:
                  code:
                    type: integer
                    example: 200
                  message:
                    type: string
                    example: success
                  data:
                    type: object
                    properties:
                      items:
                        type: array
                      total:
                        type: integer
                      page:
                        type: integer
                      size:
                        type: integer
                      has_more:
                        type: boolean
                      next_cursor:
                        type: string
                        nullable: true
        '400':
          description: 参数错误
        '429':
          description: 请求超限
        '500':
          description: 服务器错误
      tags:
        - Experts

components:
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
```

---

## 5. 分页与排序策略

### 5.1 分页模式对比

| 模式 | 实现复杂度 | 强一致性 | 深翻性能 | 推荐场景 |
|------|----------|---------|---------|---------|
| Offset-based (page/size) | 低 | 弱（可能漏项/重复） | 差 | 浅翻页（前3页以内） |
| Cursor-based | 中 | 强 | 优 | 深翻页或实时数据流 |

### 5.2 排序稳定性要求

#### /api/v1/users/me/rooms

**默认排序**：
```
created_at DESC, id ASC
```

**支持的排序字段**：
- `created_at` - 创建时间
- `updated_at` - 更新时间
- `session_count` - 场次数量

**稳定性保证**：
- 最终使用 `id` 作为强 tiebreaker，确保分页结果一致
- 并发写入时，offset 可能出现"重复/漏项"，推荐使用 cursor

#### /api/v1/experts

**默认排序**：
```
sort_order ASC, created_at DESC, id ASC
```

**支持的排序字段**：
- `sort_order` - 排序权重
- `created_at` - 创建时间
- `updated_at` - 更新时间

**稳定性保证**：
- 最终使用 `id` 作为强 tiebreaker
- `sort_order` 用于精选/推荐排序

### 5.3 游标实现细节

若请求携带 `cursor` 参数：
1. 服务端解析游标（通常为 Base64 编码的 JSON），提取排序键与ID
2. 忽略 `page` 参数，仅使用 `cursor` 和 `size` 进行查询
3. 返回 `next_cursor` 供下一次翻页使用
4. 游标过期或无效时返回 `4001` 参数错误

**游标格式示例**（Base64 编码）：
```json
{
  "created_at": "2026-05-13T10:30:00Z",
  "id": "8a01f0e2-f4f6-4af4-9f9c-77ef8c93e3d1"
}
```

---

## 6. 测试用例与验收标准

### 6.1 单元测试（Service/CRUD）

#### /api/v1/users/me/rooms

- [ ] 参数边界：`page < 1`、`size = 0`、`size > 100`
- [ ] 关键词长度：超过 200 字符返回 4001
- [ ] 排序解析：非法 sort 值回退默认排序
- [ ] 过滤组合：`keyword + is_private + category_id + status` 组合查询有效
- [ ] 用户隔离：相同直播间，不同用户查询返回结果不同（或 403）
- [ ] 游标分页：解析、编码、下一页指针生成正确

#### /api/v1/experts

- [ ] 参数边界：`page < 1`、`size = 0`、`size > 100`
- [ ] 关键词长度：超过 200 字符返回 4001
- [ ] 排序解析：非法 sort 值回退默认排序
- [ ] 过滤组合：`keyword + department + hospital` 组合查询有效
- [ ] 活跃状态：默认过滤 `is_active = true`
- [ ] 游标分页：编码/解码正确，翻页连贯

### 6.2 接口测试（API）

#### 未认证与权限测试

- [ ] 调用 `/api/v1/users/me/rooms` 不带 Authorization 返回 401（code: 4011）
- [ ] 调用 `/api/v1/experts` 不带 Authorization 返回 200（匿名访问）
- [ ] 用户 A 无法通过参数绕过，查看用户 B 的直播间

#### 数据完整性测试

- [ ] 创建直播间后，列表接口立即可查询到
- [ ] 修改直播间后，列表数据同步更新
- [ ] 删除直播间后，列表中移除该项
- [ ] 专家列表中，`is_featured = true` 的专家排序靠前

#### 参数验证测试

- [ ] 参数越界返回 4001，错误信息明确指出违规字段
- [ ] 无效 UUID 参数返回 4001
- [ ] 重复过滤条件被合理合并（如多个 `category_id`）

#### 边界与压力测试

- [ ] 空结果：返回 `items = []`、`total = 0`、`has_more = false`
- [ ] 单页容纳：size = 1 时，翻页正常
- [ ] 深翻页：使用 cursor 翻到第 100 页无性能衰减
- [ ] 并发查询：10 个并发请求，结果一致

### 6.3 集成与回归测试

#### /api/v1/users/me/rooms 与现有接口兼容性

- [ ] `GET /api/v1/rooms` 不受影响（管理员接口仍正常）
- [ ] `GET /api/v1/rooms/{id}` 不受影响（详情接口仍正常）
- [ ] 创建/修改/删除房间接口仍正常
- [ ] 创建/查询直播场次接口不受影响

#### /api/v1/experts 与现有接口兼容性

- [ ] `GET /api/v1/featured-experts` 不受影响（精选接口仍正常）
- [ ] `GET /api/v1/experts/{id}` 不受影响（详情接口）
- [ ] 管理员 `GET /api/v1/admin/experts` 不受影响
- [ ] 专家创建/修改/删除接口仍正常

#### 数据一致性测试

- [ ] 专家表聚合字段更新后，列表数据同步（或缓存同步）
- [ ] 直播间统计数据（session_count、total_viewers）与数据库一致

### 6.4 验收脚本示例（pytest）

```python
import pytest
import requests
from typing import Optional

BASE_URL = "https://api.example.com"

class TestUserRooms:
    @pytest.fixture
    def auth_header(self):
        """获取测试用户认证头"""
        return {"Authorization": "Bearer <TEST_USER_TOKEN>"}
    
    def test_list_user_rooms_success(self, auth_header):
        """测试获取用户直播间列表成功"""
        resp = requests.get(
            f"{BASE_URL}/api/v1/users/me/rooms?page=1&size=20",
            headers=auth_header
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 200
        assert "items" in data["data"]
        assert "total" in data["data"]
    
    def test_unauthorized_access(self):
        """测试未认证访问被拒"""
        resp = requests.get(f"{BASE_URL}/api/v1/users/me/rooms?page=1&size=20")
        assert resp.status_code == 401
        assert resp.json()["code"] == 4011
    
    def test_size_validation(self, auth_header):
        """测试参数验证"""
        resp = requests.get(
            f"{BASE_URL}/api/v1/users/me/rooms?page=1&size=101",
            headers=auth_header
        )
        assert resp.status_code == 400
        assert resp.json()["code"] == 4001
    
    def test_user_isolation(self, auth_header, other_user_room_id):
        """测试用户隔离"""
        # 当前用户不应能查看其他用户的直播间
        resp = requests.get(
            f"{BASE_URL}/api/v1/users/me/rooms?page=1",
            headers=auth_header
        )
        data = resp.json()
        room_ids = [item["id"] for item in data["data"]["items"]]
        assert other_user_room_id not in room_ids

class TestExpertsList:
    def test_list_experts_anonymous(self):
        """测试匿名用户访问专家列表"""
        resp = requests.get(f"{BASE_URL}/api/v1/experts?page=1&size=50")
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 200
        assert len(data["data"]["items"]) > 0
    
    def test_size_validation(self):
        """测试参数验证"""
        resp = requests.get(f"{BASE_URL}/api/v1/experts?page=1&size=101")
        assert resp.status_code == 400
        assert resp.json()["code"] == 4001
    
    def test_filter_by_department(self):
        """测试科室筛选"""
        resp = requests.get(
            f"{BASE_URL}/api/v1/experts?department=心内科&page=1"
        )
        assert resp.status_code == 200
        data = resp.json()
        # 验证返回的专家科室与筛选条件一致
        for item in data["data"]["items"]:
            assert item["department"] == "心内科"
    
    def test_keyword_search(self):
        """测试关键词搜索"""
        resp = requests.get(f"{BASE_URL}/api/v1/experts?keyword=心脏&page=1")
        assert resp.status_code == 200
        data = resp.json()
        assert data["data"]["total"] > 0
```

### 6.5 验收清单

#### 功能验收

- [ ] 登录用户可通过 `/api/v1/users/me/rooms` 查询自己创建的所有直播间
- [ ] 支持分页、关键词搜索、分类/状态/私密筛选
- [ ] 返回数据包含直播间基本信息、推流密钥、场次统计、观看统计
- [ ] 匿名用户可通过 `/api/v1/experts` 查询全量专家
- [ ] 支持分页、搜索、科室/医院筛选
- [ ] 精选专家接口行为保持不变

#### 接口验收

- [ ] `/api/v1/users/me/rooms` 返回 200 且结构稳定
- [ ] `/api/v1/experts` 返回 200 且结构稳定
- [ ] 未登录请求 `/api/v1/users/me/rooms` 返回 401（code: 4011）
- [ ] 参数越界返回 4001，不可突破上限
- [ ] 排序支持主要字段且稳定可靠
- [ ] 所有错误响应包含 `request_id`

#### 用户隔离与字段暴露验收

- [ ] 用户 A 无法获取用户 B 创建的直播间数据
- [ ] `/api/v1/users/me/rooms` 仅返回当前用户的直播间
- [ ] 列表字段与契约一致，不包含内部审核/风控字段
- [ ] 专家列表不暴露内部备注、敏感联系方式

#### 工程质量验收

- [ ] Schema、CRUD、Service、Endpoint 职责清晰
- [ ] 单元、接口、集成测试齐备并进入 CI
- [ ] 监控、日志、限流配置上线前完成
- [ ] 文档完整、代码注释清晰

#### 性能验收

- [ ] 直播间列表单次查询 < 200ms（p99）
- [ ] 专家列表单次查询 < 200ms（p99）
- [ ] 支持 100+ 直播间列表查询无明显性能衰减
- [ ] 缓存策略有效降低数据库负载

---

## 7. 速率限制与监控

### 7.1 速率限制规则

#### /api/v1/users/me/rooms

- **登录用户**：300 req/min/user
- **超限返回**：HTTP 429，业务 code 4291
- **响应头**：
  ```
  X-RateLimit-Limit: 300
  X-RateLimit-Remaining: 299
  Retry-After: 60
  ```

#### /api/v1/experts

- **匿名用户**：60 req/min/IP
- **登录用户**：300 req/min/user
- **超限返回**：HTTP 429，业务 code 4291
- **响应头**同上

### 7.2 监控与告警

#### 关键指标

- **QPS**（整体、登录用户、匿名用户）
- **平均耗时、p95、p99 延迟**
- **4xx/5xx 错误率**
- **限流命中率**
- **列表页加载成功率**（前端埋点）

#### 日志样例

```json
{
  "ts": "2026-05-13T10:30:00Z",
  "trace_id": "8a01f0e2-f4f6-4af4-9f9c-77ef8c93e3d1",
  "request_id": "2be2f6d7-4f0d-4fce-8f88-63bb78807e20",
  "path": "/api/v1/users/me/rooms",
  "method": "GET",
  "status": 200,
  "duration_ms": 45,
  "user_id": "user-123-uuid",
  "query_params": {
    "page": 1,
    "size": 20,
    "keyword": ""
  },
  "response_item_count": 8
}
```

#### 告警规则

| 告警条件 | 阈值 | 严重级别 | 响应 |
|---------|------|---------|------|
| 接口错误率 | > 5% | P1 | 立即告警 |
| p99 延迟 | > 500ms | P2 | 告警观察 |
| 限流触发 | > 10% | P2 | 告警观察 |
| 数据库异常 | 任何 | P1 | 立即告警 |

---

## 8. 兼容性与部署策略

### 8.1 兼容性保证

#### 与现有接口的关系

**直播间相关**：
- 新增 `/api/v1/users/me/rooms`（个人直播间列表）
- 保留 `GET /api/v1/rooms`（管理员全量列表，权限不变）
- 保留 `GET /api/v1/rooms/{id}`（详情接口，权限不变）

**专家相关**：
- 新增 `/api/v1/experts`（全量专家列表，匿名可访问）
- 保留 `GET /api/v1/featured-experts`（精选接口，不变）
- 保留管理员 `GET /api/v1/admin/experts`（管理界面，不变）

#### 数据字段兼容性

- 直播间表：新增聚合字段（`session_count`、`last_session_at`、`total_viewers`）不影响现有字段
- 专家表：假设已存在，本文档不修改现有字段定义

### 8.2 灰度部署建议

#### 阶段一：小流量验证（1-3 天）

1. 在测试环境部署新接口
2. 执行完整的测试套件（单元、接口、集成）
3. 监控数据库性能与缓存命中率
4. 验证日志输出与告警规则

#### 阶段二：金丝雀发布（3-7 天）

1. 将 5-10% 的生产流量引导到新接口
2. 监控错误率、延迟、用户反馈
3. 同时保持旧接口可用作为回退方案
4. 观察是否有异常访问模式（爬虫、刷新）

#### 阶段三：全量发布（1-2 天）

1. 逐步提升流量比例至 50% → 100%
2. 前端完全切换到新接口
3. 观察 24 小时无异常后，下线对旧接口的依赖
4. 保留旧接口代码作为紧急回退方案

### 8.3 回滚策略

#### 前置条件

- 保持旧接口代码与数据完整
- 前端保留对旧接口的支持（可通过 feature flag 控制）
- 数据库索引与字段兼容

#### 回滚流程

1. **立即停用新接口**：通过特性开关返回 404 或维护模式响应
2. **前端降级**：调用旧接口 `GET /api/v1/rooms`（需提前备好逻辑）
3. **根因分析**：检查日志、监控、用户反馈
4. **重新部署**：修复问题后重新灰度发布

#### 回滚检查清单

- [ ] 是否有未完成的交易或状态不一致
- [ ] 缓存与数据库数据是否一致
- [ ] 前端是否成功切回旧接口
- [ ] 用户是否报告功能异常

---

## 9. 前端集成指南

### 9.1 "我的直播"页面集成

**旧流程**（使用 `/api/v1/rooms`）：
```javascript
// 不推荐：获取全量直播间，然后在前端过滤
const resp = await api.get('/api/v1/rooms');
const myRooms = resp.data.items.filter(r => r.user_id === currentUser.id);
```

**新流程**（使用 `/api/v1/users/me/rooms`）：
```javascript
// 推荐：后端过滤，直接获取个人直播间
const resp = await api.get('/api/v1/users/me/rooms', {
  params: {
    page: 1,
    size: 20,
    sort: 'created_at:desc'
  }
});
const myRooms = resp.data.data.items;
```

**优势**：
- 数据隐私：不暴露其他用户的直播间
- 性能：后端过滤减少网络传输
- 权限：明确的权限检查

### 9.2 专家列表页集成

**旧流程**（使用精选接口）：
```javascript
const resp = await api.get('/api/v1/featured-experts');
const experts = resp.data.items; // 仅精选专家
```

**新流程**（使用全量接口）：
```javascript
// 首页精选位：继续使用精选接口
const featuredResp = await api.get('/api/v1/featured-experts');

// 专家列表页：使用全量接口
const allResp = await api.get('/api/v1/experts', {
  params: {
    page: 1,
    size: 50,
    sort: 'sort_order:asc'
  }
});
const allExperts = allResp.data.data.items;
```

### 9.3 错误处理

```javascript
// 统一错误处理
const handleApiError = (error) => {
  const code = error.response?.data?.code;
  const message = error.response?.data?.message;
  
  switch (code) {
    case 4011:
      // 未登录：重定向到登录页
      redirectToLogin();
      break;
    case 4001:
      // 参数错误：显示用户友好的错误提示
      showToast(`参数错误: ${message}`);
      break;
    case 4291:
      // 请求超限：显示重试提示
      showToast('请求过于频繁，请稍候再试');
      break;
    default:
      // 其他错误
      showToast('加载失败，请重试');
  }
};
```

---

## 10. 附录：快速参考

### 10.1 错误码速查表

| code | HTTP | 说明 | 解决方案 |
|------|------|------|--------|
| 200 | 200 | 成功 | - |
| 4001 | 400 | 参数错误 | 检查请求参数范围与格式 |
| 4011 | 401 | 未登录 | 调用登录接口获取 JWT Token |
| 4031 | 403 | 无权访问 | 检查用户权限 |
| 4291 | 429 | 请求超限 | 等待 `Retry-After` 秒后重试 |
| 1002 | 500 | 数据库异常 | 联系技术支持 |
| 5001 | 500 | 服务器错误 | 联系技术支持 |

### 10.2 常见场景问答

**Q: 如何在"我的直播"页面实现搜索？**  
A: 使用 `keyword` 参数，后端自动匹配标题与描述：
```
GET /api/v1/users/me/rooms?keyword=科普&page=1
```

**Q: 如何只查看私密直播间？**  
A: 使用 `is_private` 参数过滤：
```
GET /api/v1/users/me/rooms?is_private=true&page=1
```

**Q: 专家列表支持多条件组合吗？**  
A: 支持，同时传入多个过滤参数：
```
GET /api/v1/experts?keyword=心脏&department=心内科&hospital=协和医院&page=1
```

**Q: 如何处理深分页的性能问题？**  
A: 使用游标分页而非 offset 分页：
```
GET /api/v1/experts?size=50&cursor=eyJpZCI6InV1aWQtMTAwMSJ9
```

**Q: 直播间的 `stream_key` 何时可见？**  
A: 仅当调用用户是该直播间的所有者时返回（通过应用层权限检查）。

---

## 11. 文档版本历史

| 版本 | 日期 | 变更内容 |
|------|------|--------|
| V1.0 | 2026-05-14 | 初稿：整合个人直播间列表 API 与专家全量列表 API，参照直播核心功能设计文档风格 |

---

**文档发布日期**：2026-05-14  
**最后更新**：2026-05-14  
**维护责任人**：开发团队
