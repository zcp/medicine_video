# 系统架构设计

> 基于实际项目代码分析，更新时间：2026-07-13

---

## 一、整体架构

### 架构分层

项目采用经典的**五层架构**，从路由层到数据库层逐层调用：

```
┌─────────────────────────────────────┐
│     FastAPI Application (main.py)    │
├─────────────────────────────────────┤
│  1. API Endpoints (路由层)           │
│     - 参数验证、路由分发、调用Service │
├─────────────────────────────────────┤
│  2. Services (业务逻辑层)            │
│     - 业务规则编排、跨模块调用       │
├─────────────────────────────────────┤
│  3. CRUD (数据访问层)                │
│     - 数据库查询、事务管理           │
├─────────────────────────────────────┤
│  4. Models (ORM模型层)              │
│     - 表结构定义、关系映射           │
├─────────────────────────────────────┤
│  5. Database (数据库层)              │
│     - PostgreSQL (async + sync)      │
│     - Redis (缓存/消息队列)          │
└─────────────────────────────────────┘
```

### 职责说明

| 层次 | 目录 | 职责 | 不应做的事情 |
|------|------|------|--------------|
| **API** | `app/api/v1/endpoints/` | 路由定义、参数验证、调用 Service | 不应包含业务逻辑 |
| **Service** | `app/services/` | 业务逻辑编排、数据转换 | 不应直接操作 ORM Session |
| **CRUD** | `app/crud/` | 数据库 CRUD 操作、查询构建 | 不应包含业务规则 |
| **Models** | `app/models/` | 表结构定义、索引、关系 | 不应包含业务逻辑 |
| **Schemas** | `app/schemas/` | API 请求/响应数据结构 | - |
| **Core** | `app/core/` | 认证、配置、依赖注入、异常 | - |
| **Tasks** | `app/tasks/` | Celery 异步任务 | - |

---

## 二、项目模块总览

基于实际代码中的 **17 个 API 路由模块**，项目包含以下功能模块：

```
backend/live_core_service/
│
├── app/
│   ├── main.py                    # FastAPI 应用入口
│   ├── database.py                # 异步+同步数据库连接
│   │
│   ├── api/v1/
│   │   ├── api.py                 # 路由聚合（注册全部模块）
│   │   └── endpoints/             # ===== 17 个 API 路由模块 =====
│   │       ├── room.py            # 直播间管理
│   │       ├── session.py         # 直播会话管理
│   │       ├── experts.py         # 专家系统
│   │       ├── topic.py           # 专题管理
│   │       ├── brand.py           # 品牌管理
│   │       ├── content_management.py  # 内容管理 (分类/标签)
│   │       ├── live_features.py   # 直播特性 (Tab/留言)
│   │       ├── homepage_search.py # 首页搜索
│   │       ├── liveroom_official_accounts.py  # 公众号关联
│   │       ├── batch_import.py    # 批量导入
│   │       ├── session_import.py  # 会话导入
│   │       ├── user_behavior.py   # 用户行为
│   │       ├── user_preference_notification.py  # 用户偏好通知
│   │       ├── internal.py        # SRS 回调 (内部)
│   │       ├── health.py          # 健康检查
│   │       ├── search_extra.py    # 搜索扩展 (历史/热门)
│   │       └── room_backup.py     # 房间备份
│   │
│   ├── services/                  # ===== 17 个业务逻辑服务 =====
│   │   ├── room_service.py
│   │   ├── session_service.py
│   │   ├── expert_service.py
│   │   ├── topic_service.py
│   │   ├── brand_service.py
│   │   ├── content_management_service.py
│   │   ├── live_features_service.py
│   │   ├── homepage_search_service.py
│   │   ├── liveroom_official_accounts_service.py
│   │   ├── batch_import.py
│   │   ├── session_import.py
│   │   ├── user_behavior_service.py
│   │   ├── user_preference_notification_service.py
│   │   ├── srs_callback_service.py
│   │   ├── health_service.py
│   │   └── utils_playback.py
│   │
│   ├── crud/                      # ===== 14 个数据访问模块 =====
│   │   ├── room.py
│   │   ├── session.py
│   │   ├── experts.py
│   │   ├── topic.py
│   │   ├── brand.py
│   │   ├── content_management.py
│   │   ├── live_features.py
│   │   ├── homepage_search.py
│   │   ├── liveroom_official_accounts.py
│   │   ├── search.py
│   │   ├── user_behavior.py
│   │   ├── user_preference_notification.py
│   │   └── health.py
│   │
│   ├── models/                    # ===== 11 个 ORM 模型 =====
│   │   ├── live_core.py           # LiveRoom, LiveSession, SessionStatistics
│   │   ├── experts.py             # Expert, UserExpertSubscription, LiveSessionExpert
│   │   ├── content_management.py  # Tag, Category, SessionTag, LiveRoomCategory
│   │   ├── live_features.py       # LiveRoomMessage, LiveRoomTab
│   │   ├── brand.py
│   │   ├── homepage_search.py
│   │   ├── topic.py
│   │   ├── user_behavior.py
│   │   ├── user_preference_notification.py
│   │   ├── liveroom_official_accounts.py
│   │   └── search.py
│   │
│   ├── schemas/                   # Pydantic 数据模型
│   │   ├── batch_import.py
│   │   ├── brand.py
│   │   ├── homepage_search.py
│   │   ├── live_features.py
│   │   ├── liveroom_official_accounts.py
│   │   ├── user_behavior.py
│   │   └── user_preference_notification.py
│   │
│   ├── core/                      # 核心基础设施
│   │   ├── auth.py                # JWT 认证
│   │   ├── config.py              # Settings 配置类
│   │   ├── deps.py                # 依赖注入
│   │   ├── exceptions.py          # 自定义异常
│   │   ├── file_handler.py        # 文件处理
│   │   ├── logging_utils.py       # 日志工具
│   │   └── response.py            # 统一响应格式
│   │
│   └── tasks/                     # Celery 异步任务
│       ├── celery_app.py          # Celery 实例配置
│       └── session_processing.py  # 会话处理任务
│
├── tests/
│   ├── integration/               # 33 个集成测试文件
│   └── unit/                      # 41 个单元测试文件
│
├── migrations/                    # 数据库迁移 SQL
│   ├── add_experts_is_active.sql
│   ├── 20260531_add_keyword_to_search_keyword_stats.sql
│   └── drop_live_rooms_category_id.sql
│
├── requirements.txt               # Python 依赖
├── Dockerfile                     # Docker 构建文件
├── run.py                         # 启动入口
└── pytest.ini                     # 测试配置
```

---

## 三、一个具体请求的完整调用链路

以"获取直播间详情"为例，展示五层架构的实际流转：

```
HTTP Request: GET /api/v1/rooms/{room_id}
│
▼
┌─────────────────────────────────────────────────────┐
│  1. API Endpoint: room.py                           │
│     @router.get("/{room_id}")                       │
│     async def get_room(room_id, db, current_user)   │
│                                                     │
│     职责: 参数验证 + 权限检查 + 调用 Service         │
│     输入: room_id (UUID), current_user (JWT Token)  │
│     输出: 标准响应格式 (code/message/data)          │
└──────────────────┬──────────────────────────────────┘
                   │
▼
┌─────────────────────────────────────────────────────┐
│  2. Service: room_service.py                        │
│     async def get_room_detail(db, room_id, user)    │
│                                                     │
│     职责: 业务逻辑 — 权限判断 + 数据聚合             │
│     - 检查房间是否存在                               │
│     - 检查是否为私有房间                             │
│     - 聚合关联数据 (sessions, statistics, tabs)     │
└──────────────────┬──────────────────────────────────┘
                   │
▼
┌─────────────────────────────────────────────────────┐
│  3. CRUD: room.py                                   │
│     async def get_room_by_id(db, room_id)           │
│                                                     │
│     职责: 数据库查询 — 构建 SQL 查询                │
│     - SELECT * FROM live_rooms WHERE id = :room_id  │
└──────────────────┬──────────────────────────────────┘
                   │
▼
┌─────────────────────────────────────────────────────┐
│  4. Model: LiveRoom (live_core.py)                  │
│     __tablename__ = "live_rooms"                    │
│                                                     │
│     职责: 定义表结构与 Python 对象的映射             │
│     - 列定义 (id, title, stream_key, ...)           │
│     - 关系定义 (live_sessions, child_rooms)         │
│     - 索引定义 (uq_live_rooms_user_external_room)   │
└──────────────────┬──────────────────────────────────┘
                   │
▼
┌─────────────────────────────────────────────────────┐
│  5. Database: PostgreSQL (database.py)              │
│     AsyncSessionLocal → asyncpg 驱动                │
│                                                     │
│     职责: 执行 SQL 并返回结果                        │
│     - 异步连接池管理                                 │
│     - 事务管理 (自动 commit/rollback)               │
└─────────────────────────────────────────────────────┘
```

---

## 四、核心基础设施层

### 4.1 认证系统 (auth.py + deps.py)

```
         ┌─────────┐
         │ Client  │
         └────┬────┘
              │ 请求 + Bearer Token
              ▼
┌─────────────────────────────┐
│  HTTPBearer (security)      │  提取 Authorization Header
└──────────────┬──────────────┘
               │ Token String
               ▼
┌─────────────────────────────┐
│  JWTAuth.verify_token()     │  解码 JWT，验证签名和有效期
└──────────────┬──────────────┘
               │ payload = {user_id, role, exp, ...}
               ▼
┌─────────────────────────────┐
│  Deps (依赖注入)             │
│  - get_current_user()       │  强制鉴权：无 Token → 401
│  - get_current_user_optional()│  可选鉴权：无 Token → None
└─────────────────────────────┘
```

**认证模式**：
- **强制鉴权** (`get_current_user`)：用于大多数需要登录的接口
- **可选鉴权** (`get_current_user_optional`)：用于公开接口，但已登录用户可看到更多内容

### 4.2 配置系统 (config.py)

```
┌────────────┐    ┌──────────────┐    ┌────────────────┐
│ .env 文件   │ →  │ Settings 类   │ →  │ 生产/开发验证  │
│ 环境变量    │    │ 属性计算      │    │ _validate_*()  │
└────────────┘    └──────────────┘    └────────────────┘
```

**关键配置属性**：
- `DATABASE_URL` - 异步数据库连接 (asyncpg)
- `SYNC_DATABASE_URL` - 同步数据库连接
- `BACKEND_CORS_ORIGINS` - CORS 白名单（从逗号分隔字符串解析）
- `JWT_SECRET_KEY` - JWT 签名密钥

**安全验证机制**：
- 生产环境强制验证密码和密钥不能使用默认值
- 开发环境使用警告而非错误

### 4.3 数据库连接 (database.py)

```
┌──────────────────────────────────┐
│         DATABASE_URL              │
│  postgresql+asyncpg://...        │
└───────────────┬──────────────────┘
                │
    ┌───────────┴───────────┐
    ▼                       ▼
┌────────────┐     ┌────────────────┐
│ engine      │     │ async_engine   │
│ (同步)     │     │ (异步)         │
│ create_engine│    │ create_async_  │
│             │     │ engine         │
└──────┬──────┘     └───────┬────────┘
       │                    │
       ▼                    ▼
┌────────────┐     ┌────────────────┐
│ SessionLocal│     │AsyncSession    │
│ (sync sess)│     │ Local          │
└────────────┘     └───────┬────────┘
                           │
                           ▼
                    ┌────────────────┐
                    │ get_async_db() │
                    │ (FastAPI Dep)  │
                    ├────────────────┤
                    │ commit on      │
                    │ success        │
                    │ rollback on    │
                    │ error          │
                    └────────────────┘
```

**设计特点**：
- 双引擎设计（同步用于初始化，异步用于运行）
- 自动事务管理（成功提交，异常回滚）
- 安全日志（不打印密码）

### 4.4 响应格式 (response.py)

所有 API 返回统一格式：

```json
{
    "code": 200,
    "message": "success",
    "data": { ... },
    "timestamp": "2026-07-13T10:00:00.000Z"
}
```

### 4.5 异常体系 (exceptions.py)

```
Exception
    ├── DatabaseIntegrityException   # 唯一键冲突等
    └── DatabaseOperationException   # 通用数据库错误
```

### 4.6 文件处理 (file_handler.py)

负责文件上传、验证、存储的通用处理逻辑。

---

## 五、数据模型关系图

```
                        ┌─────────────────┐
                        │    categories    │
                        │  (全局分类体系)   │
                        └───┬───────┬─────┘
                            │       │
              ┌─────────────┘       └─────────────┐
              ▼                                    ▼
┌─────────────────────────┐          ┌────────────────────────┐
│   live_room_categories   │          │       experts          │
│   (直播间←→分类 多对多)   │          │   (category_id 外键)   │
└───────────┬─────────────┘          └───────────┬────────────┘
            │                                    │
            ▼                                    ▼
┌─────────────────────────┐          ┌────────────────────────┐
│      live_rooms          │          │ user_expert_subscriptions│
│  (直播房间，核心实体)     │          │  (用户关注专家)         │
└────┬───────┬───────┬────┘          └────────────────────────┘
     │       │       │
     │       │       └──────────────────────────┐
     │       │                                  │
     ▼       ▼                                  ▼
┌─────────┐ ┌──────────────┐    ┌──────────────────────────┐
│live_room│ │live_sessions │    │live_session_experts      │
│_tabs    │ │(直播会话)    │    │(场次←→专家 多对多)       │
└─────────┘ └───┬──────────┘    └──────────────────────────┘
                │
    ┌───────────┼───────────┐
    ▼           ▼           ▼
┌────────┐ ┌──────────┐ ┌──────────────┐
│session │ │live_room │ │session_      │
│_stats  │ │_messages │ │tags          │
│(统计)  │ │(留言)    │ │(会议标签)    │
└────────┘ └──────────┘ └──────┬───────┘
                               │
                               ▼
                         ┌──────────┐
                         │   tags   │
                         │ (标签)   │
                         └──────────┘
```

---

## 六、数据设计特点

### 6.1 UUID 主键

所有表使用 UUID 作为主键，在应用层生成 (`uuid.uuid4()`)，而非数据库自增：

```python
id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
```

**优势**：分布式友好、安全（不可预测）、支持离线生成。

### 6.2 双时间戳模式

所有业务表包含 `created_at` 和 `updated_at` 字段：

```python
created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
```

**特点**：存储 UTC 时间，`onupdate` 自动更新。

### 6.3 软删除

使用 `is_active` 字段实现软删除：

```python
is_active = Column(Boolean, nullable=False, default=True)
```

**适用范围**：experts, categories, tags, live_room_tabs。

### 6.4 幂等性设计

批量导入通过两个字段保证幂等：

- `external_room_id` - 外部房间 ID
- `playback_url_hash` - 回放 URL 规范化哈希

使用 PostgreSQL 部分唯一索引（仅对非 NULL 值生效）：

```sql
CREATE UNIQUE INDEX ... WHERE external_room_id IS NOT NULL;
```

---

## 七、服务部署架构

```
                         ┌──────────┐
                         │  Client  │
                         └────┬─────┘
                              │ HTTP/HTTPS
                              ▼
                    ┌──────────────────┐
                    │  Nginx (80/443)   │
                    │  反向代理 / SSL   │
                    └──┬─────┬────┬────┘
                       │     │    │
          ┌────────────┘     │    └──────────────┐
          ▼                  ▼                   ▼
┌─────────────────┐  ┌──────────────┐  ┌─────────────────┐
│ live_core_      │  │ media_download│ │  user_service   │
│ service (:8000) │  │ _service      │ │  (:8002)        │
│                 │  │ (:8001)       │ │                 │
│ FastAPI +       │  │              │  │ 用户管理服务     │
│ Celery Worker   │  │ 媒体下载服务  │  │                 │
└───┬───┬─────────┘  └──────────────┘  └─────────────────┘
    │   │
    │   └──────────────────┐
    ▼                      ▼
┌────────┐          ┌──────────┐
│PostgreSQL│        │  Redis   │
│ (:5432) │         │ (:6379)  │
│         │         │          │
│ 主数据库 │         │ 缓存/队列 │
└────────┘          └──────────┘

┌──────────────────┐     ┌──────────────┐
│  SRS (:1935/8080)│────▶│  推流客户端   │
│  流媒体服务器     │◀────│  (OBS等)     │
│  RTMP/HLS/WebRTC │     └──────────────┘
└──────────────────┘
```

### Docker Compose 服务清单

| 服务 | 端口 | 镜像 | 说明 |
|------|------|------|------|
| live_core_service | 8000 | 本地构建 | 直播核心服务 |
| media_download_service | 8001 | 本地构建 | 媒体下载服务 |
| user_service | 8002 | 本地构建 | 用户管理服务 |
| celery_worker | - | 本地构建 | Celery 异步任务 |
| postgres | 5432 | postgres:15-alpine | 主数据库 |
| redis | 6379 | redis:7-alpine | 缓存和消息队列 |
| srs | 1935, 8080 | ossrs/srs:6 | 流媒体服务器 |
| nginx | 80, 443 | nginx:alpine | 反向代理 |

### 网络架构

所有服务通过 `live-network` 桥接网络互通，Nginx 作为唯一对外入口。

---

## 八、服务间通信

```
┌─────────────────────────────────────────────────────┐
│                    通信方式                           │
├─────────────────┬───────────────────────────────────┤
│ REST API        │ 服务间同步调用 (HTTP)              │
│ WebSocket       │ 实时通信 (待开发)                  │
│ Redis Pub/Sub   │ 事件通知 (Celery 依赖)             │
│ Celery          │ 异步任务分发                       │
│ SRS Callback    │ 流媒体服务器状态回调 (HTTP)        │
└─────────────────┴───────────────────────────────────┘
```

---

## 九、异步任务架构

```
┌──────────────┐     ┌──────────────────┐     ┌──────────────┐
│  FastAPI     │────▶│  Celery Broker   │────▶│  Celery      │
│  (API请求)   │     │  (Redis)         │     │  Worker      │
│              │     │                  │     │  (10 并发)   │
│  .delay()    │     │  任务入队        │     │              │
└──────────────┘     └──────────────────┘     └──────┬───────┘
                                                     │
                                                     ▼
                                              ┌──────────────┐
                                              │ session_     │
                                              │ processing   │
                                              │ 会话处理任务  │
                                              └──────────────┘
```

**任务列表**：
- `session_processing.py` - 直播会话后处理（录制、统计、转码等）

---

## 十、API 路由结构

```
/api/v1
├── /rooms                        rooms CRUD + batch_import + session_import
│   ├── GET    /                  房间列表
│   ├── POST   /                  创建房间
│   ├── GET    /{room_id}         房间详情
│   ├── PUT    /{room_id}         更新房间
│   ├── DELETE /{room_id}         删除房间
│   ├── POST   /import/batch      批量导入房间
│   └── POST   /{room_id}/sessions/import  导入会话
│
├── /sessions                     sessions CRUD
├── /experts                      专家系统
│   ├── GET    /experts           专家列表 (公开)
│   ├── GET    /experts/{id}      专家详情
│   └── GET    /featured-experts  推荐专家
│
├── /topics                       专题管理
├── /featured-content             焦点图
├── /homepage                     首页内容
├── /search                       搜索功能
├── /brands                       品牌管理
├── /content                      内容管理 (分类/标签)
├── /topic-categories             专题分类
├── /official-accounts            公众号关联
│
├── /users/me                     用户相关
│   ├── GET    /rooms             我的房间
│   ├── POST   /preferences       偏好设置
│   ├── GET    /notifications     通知列表
│   ├── POST   /followed-experts  关注专家
│   └── GET    /search-history    搜索历史
│
├── /admin                        管理员
│   ├── /experts                  专家管理
│   ├── /tabs                     Tab管理
│   ├── /categories               分类管理
│   ├── /tags                     标签管理
│   ├── /brands                   品牌管理
│   ├── /notifications            通知管理
│   └── /featured-content         焦点图管理
│
├── /internal/srs                 内部 SRS 回调
├── /health                       健康检查
└── /                             根路径状态检查
```

---

## 十一、安全设计

### 11.1 多层安全防护

```
┌─────────────────────────────────────┐
│ 1. CORS 中间件                      │
│    allow_origins, allow_credentials │
├─────────────────────────────────────┤
│ 2. JWT 认证                         │
│    HTTPBearer → verify_token        │
├─────────────────────────────────────┤
│ 3. 权限验证 (业务层)                 │
│    房间所有者 / 管理员角色检查        │
├─────────────────────────────────────┤
│ 4. 环境验证 (配置层)                 │
│    production vs development 检查    │
└─────────────────────────────────────┘
```

### 11.2 数据安全

- 密码哈希存储（bcrypt）
- UUID 主键防遍历
- SQL 注入防护（SQLAlchemy ORM）
- 软删除防误操作
- 文件上传类型和大小限制

---

## 十二、技术选型汇总

| 组件 | 技术 | 版本 | 选型原因 |
|------|------|------|----------|
| Web 框架 | FastAPI | 0.100.0 | 异步高性能、自动文档、类型安全 |
| ORM | SQLAlchemy | 1.4.23 | 成熟稳定、关系映射完整 |
| 数据验证 | Pydantic | 2.3.0 | 类型安全、自动验证 |
| 主数据库 | PostgreSQL | 15 | 关系型、JSON 支持、ACID |
| 异步驱动 | asyncpg | 0.30.0 | 高性能 PostgreSQL 异步驱动 |
| 同步驱动 | psycopg2-binary | 2.9.1 | 稳定同步连接 |
| 缓存/队列 | Redis | 7 | 高性能内存数据库 |
| 异步任务 | Celery | 5.3 | 分布式任务队列 |
| ASGI | Uvicorn | 0.15.0 | 高性能 ASGI 服务器 |
| 流媒体 | SRS | 6 | RTMP/HLS/WebRTC 支持 |
| 部署 | Docker Compose | - | 容器编排、环境一致性 |
| 反向代理 | Nginx | alpine | 负载均衡、SSL 终结 |

---

**最后更新**：2026-07-13