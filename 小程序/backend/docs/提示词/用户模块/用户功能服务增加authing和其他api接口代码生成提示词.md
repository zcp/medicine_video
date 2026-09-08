
-----

### **最终增强版：为 Authing 集成和新用户 API 进行增量代码生成的提示词 (最终修正版)**

#### **1. 角色定义 (Role Definition)**

你是一名资深的 Python 后端工程师，精通 FastAPI、SQLAlchemy 2.0 (异步模式) 和现代 API 设计原则。你擅长在现有代码库上进行**增量式开发**，能够根据详尽的设计文档、数据模型和代码上下文，精确地添加新功能，同时最大限度地减少对现有稳定代码的改动。

#### **2. 任务目标 (Task Objective)**

你的任务是执行一次**增量代码生成**，为现有的用户功能服务集成 **Authing** 作为 SSO 身份提供商，并根据设计文档添加新的用户管理 API。

**核心约束 (Primary Constraint):** 你的首要原则是**最小化对现有代码的修改**。当前代码库已经过测试。你必须优先选择添加新函数、新方法和新类，而不是重构现有代码。只有在支持新功能绝对必要时，才允许进行微小的修改。

#### **3. 核心上下文信息 (Core Context Information)**

你必须完全依赖以下提供的上下文信息来编写代码，严禁猜测或创造任何不存在的模块、函数、数据结构或 SDK 用法。

**3.1. 项目结构与待修改文件**
你将要修改以下文件，请严格按照其在项目中的路径进行操作：

```
backend/users/app/
├── __init__.py (65B)
├── main.py (578B)
├── database.py (2.6KB)
├── api/
│   ├── __init__.py (35B)
│   └── v1/
│       ├── __init__.py (44B)
│       ├── api.py (585B)
│       ├── deps.py (4.9KB)
│       ├── endpoints/
│       │   ├── __init__.py (41B)
│       │   ├── auth.py (11KB)    # <-- 需要修改的文件，要求最小幅度修改，
│       │   ├── subscriptions.py (8.4KB)
│       │   ├── membership_products.py (3.1KB)
│       │   ├── users.py (12KB) # <-- 需要修改的文件，要求最小幅度修改，
│       │   ├── auth_backup.py (24KB)
│       │   ├── subscriptions_backup.py (11KB)
│       │   ├── membership_products_backup.py (3.3KB)
│       │   └── users_backup.py (15KB)
│       └── admin/
│           ├── __init__.py (91B)
│           ├── products.py (11KB)
│           ├── users.py (5.7KB)
│           └── users_backup.py (6.2KB)
├── services/
│   ├── __init__.py (645B)
│   ├── auth_service.py (23KB)  # <-- 需要修改的文件，要求最小幅度修改，
│   ├── admin_products_service.py (10KB)
│   ├── admin_user_service.py (6.8KB)
│   ├── admin_subscriptions_service.py (11KB)
│   ├── membership_products_service.py (5.5KB)
│   ├── user_service.py (16KB)  # <-- 需要修改的文件，要求最小幅度修改，
│   └── subscriptions_service.py (13KB)
├── core/
│   ├── __init__.py (30B)
│   ├── redis_client.py (1.3KB)
│   └── responses.py (1.0KB)  # (提供 success_response 和 error_response)
├── schemas/
│   ├── __init__.py (1.9KB)
│   ├── users.py (16KB)  # <-- 需要修改的文件，要求最小幅度修改，
│   └── auth.py (1.5KB)  # <-- 需要修改的文件，要求最小幅度修改，
├── crud/
│   ├── __init__.py (96B)
│   ├── crud_user.py (13KB)  # <-- 需要修改的文件，要求最小幅度修改，
│   ├── crud_user_membership.py (7.1KB)
│   └── crud_membership_product.py (8.7KB)
├── models/
│   ├── __init__.py (445B)
│   └── users.py (7.6KB)
└── scripts/
    ├── __init__.py (70B)
    └── create_tables.py (4.2KB)

```

**3.2. 关键数据库模型定义 (`app/models/users.py`)**
你的代码必须基于 `users` 表的以下结构。这是**唯一的真实数据源**。AI在生成SQLAlchemy模型时，必须确保字段名、类型和约束与此SQL定义完全匹配。

```python
-- users 表
CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    public_id UUID NOT NULL UNIQUE,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(255) UNIQUE,
    phone_number VARCHAR(20) UNIQUE,
    password_hash VARCHAR(255),
    nickname VARCHAR(50) NOT NULL,
    avatar_url VARCHAR(512),
    bio TEXT,
    role user_role NOT NULL DEFAULT 'REGULAR',
    status entity_status NOT NULL DEFAULT 'NORMAL',
    is_email_verified BOOLEAN NOT NULL DEFAULT false,
    is_phone_verified BOOLEAN NOT NULL DEFAULT false,
    last_login_at TIMESTAMPTZ NULL,
    last_login_ip INET,
    social_provider VARCHAR(20),
    social_id VARCHAR(255),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT users_login_method_check
        CHECK (password_hash IS NOT NULL OR (social_provider IS NOT NULL AND social_id IS NOT NULL))
);
CREATE UNIQUE INDEX idx_users_social_login ON users (social_provider, social_id);
COMMENT ON TABLE users IS '用户核心表';
COMMENT ON COLUMN users.id IS '【内部ID】主键，仅用于数据库内部关联';
COMMENT ON COLUMN users.public_id IS '【公开ID】对外暴露的唯一标识符，用于API等';
COMMENT ON COLUMN users.role IS '用户角色: REGULAR, MODERATOR, ADMIN, SUPERADMIN';
COMMENT ON COLUMN users.status IS '用户状态: NORMAL, BANNED, DELETED, PENDING_REVIEW, REJECTED';
CREATE TRIGGER set_timestamp_users BEFORE UPDATE ON users FOR EACH ROW EXECUTE PROCEDURE trigger_set_timestamp();

```

**3.2.1. [新增] JWT Token 字段说明**
**重要**: 当前系统的JWT Token中存储的是 `public_id`（UUID字符串），而不是内部 `id`（BIGINT）。这影响以下关键逻辑：

1. **Token创建**: `_create_access_token()` 和 `_create_refresh_token()` 方法接收 `public_id` 参数
2. **Token验证**: `deps.py` 中的 `get_current_user()` 必须使用 `crud_user.get_by_uuid()` 查询
3. **用户查询**: 所有基于JWT Token的用户查询都必须使用 `public_id` 字段

**字段映射关系**:
- JWT Token中的 `user_id` → 对应数据库的 `users.public_id` 字段
- 内部关联使用 → 对应数据库的 `users.id` 字段
```

**3.3.  你将要修改以下 `app/` 目录下的七个文件，**修改幅度必须最小化**：

  * `schemas/auth.py`
  * `schemas/users.py`
  * `crud/crud_user.py`
  * `services/auth_service.py`
  * `services/user_service.py`
  * `api/v1/endpoints/auth.py`
  * `api/v1/endpoints/users.py`

**3.4. [新增] 环境变量 (`.env`)**
所有Authing相关的配置都必须通过环境变量读取，请使用以下变量名：

```bash
# ===== Authing 用户池配置 =====
USER_POOL_ID=your_user_pool_id
USER_POOL_SECRET=your_user_pool_secret  # 仅后端管理操作需要

# ===== 应用 Client ID =====
# 用于 verify_id_token 时的 audience 校验
VITE_CLIENT_ID=your_current_app_client_id
```

**环境变量加载方式：**
在服务启动时（如 `run.py` 或 `main.py` 文件顶部），必须添加以下代码来加载环境变量：

```python
from dotenv import load_dotenv
import os

# 加载当前目录的 .env 文件
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

# 或者更明确地指定路径
load_dotenv('.env')
```

> 📝 **重要**：确保在任何使用 `os.getenv()` 的代码执行之前调用 `load_dotenv()`。
```

## ✅ 3.5. [已精简 + 详细说明] Authing SDK API 核心说明（v3 版）

> ⚠️ 你的任务**只需要**使用以下两个客户端及其列出的方法。严禁使用文档中未提及的其他任何方法。

---

### **A. `AuthenticationClient` —— 用于 Token 验证（推荐）**

> 用于验证前端传来的 `ID Token` 是否合法（签名、过期时间、受众等），适用于后端接口身份认证。

#### **初始化**

```python
from authing import AuthenticationClient
import os

from authing import AuthenticationClient

# 初始化 AuthenticationClient
authentication_client = AuthenticationClient(
    # Authing 应用 ID
    app_id='AUTHING_APP_ID',

    # Authing 应用密钥
    app_secret='AUTHING_APP_SECRET',

    # Authing 应用地址，如 https://example.authing.cn
    app_host='AUTHING_APP_HOST',

    # Authing 应用配置的登录回调地址
    redirect_uri='AUTHING_APP_REDIRECT_URI',
)

```

> 🔐 注意：
> - 所以字段/变量量必须通过环境变量安全注入。
> - `secret` **绝不能暴露在前端或日志中**。

---

#### **核心方法：`verify_id_token_pyjwt(...)`（自定义实现）**

##### ✅ 功能
由于 Python SDK 与 Node.js SDK 的差异，需要自定义实现 ID Token 验证方法。该方法使用 PyJWT 的 PyJWKClient 验证 RS256 签名的 OIDC ID Token，包括：
- 签名是否有效（使用 JWKS 公钥）
- 是否过期（`exp` 时间戳）
- 受众（`aud`）是否匹配当前应用
- 发行者（`iss`）是否为当前用户池

##### 📥 参数

| 参数 | 类型 | 是否必填 | 说明 |
|------|------|----------|------|
| `id_token` | `str` | ✅ 是 | 从前端传来的 JWT 格式的 ID Token |
| `issuer` | `str` | ✅ 是 | OIDC 发行者地址，格式为 `https://<domain>.authing.cn/oidc` |
| `audience` | `str` | ✅ 是 | 应用的 `CLIENT_ID`，用于校验 `aud` 字段 |
| `timeout` | `int` | ❌ 否 | JWKS 请求超时时间，默认 5 秒 |

##### 📤 返回值
- 成功时返回一个 `dict`，即 JWT 的 payload，包含：
  ```python
  {
    "sub": "63d...123",           # 用户唯一标识（User ID）
    "email": "user@example.com",  # 邮箱（如有）
    "nickname": "张三",            # 昵称（如有）
    "exp": 1735689600,            # 过期时间戳（秒）
    "iat": 1735686000,            # 签发时间
    "iss": "https://xxx.authing.cn/oidc",
    "aud": "63d...app1"
  }
  ```

##### ⚠️ 异常（常见）
| 异常类型 | 触发条件 |
|---------|----------|
| `ExpiredSignatureError` | Token 已过期（`exp < now`） |
| `InvalidSignatureError` | 签名无效（Token 被篡改或非本用户池签发） |
| `InvalidAudienceError` | `aud` 不匹配（Token 不是发给当前应用的） |
| `InvalidIssuerError` | `iss` 不匹配（Token 不是本用户池签发） |
| `InvalidTokenError` | 通用格式错误（如非 JWT、缺失字段等） |

##### ✅ 实现示例

```python
def verify_id_token_pyjwt(self, id_token: str, issuer: str, audience: str, timeout: int = 5) -> dict:
    """
    使用 PyJWT 的 PyJWKClient 校验 RS256 OIDC id_token
    issuer 例：https://uni-app-multiplatform.authing.cn/oidc
    audience 例：你的 App ID（689e762956a8a5df2b154759）
    """
    issuer = issuer.rstrip("/")
    jwks_url = f"{issuer}/.well-known/jwks.json"

    jwk_client = PyJWKClient(jwks_url, timeout=timeout)
    signing_key = jwk_client.get_signing_key_from_jwt(id_token)

    payload = jwt.decode(
        id_token,
        signing_key.key,
        algorithms=["RS256"],
        audience=audience,
        issuer=issuer,
        options={"require": ["exp", "iat", "iss", "aud"]},  # 可按需调整
        leeway=60,  # 允许 60s 时间漂移
    )
    return payload
```

> 🔔 提示：这是你**必须自定义实现的 Token 验证方法**，因为 Python SDK 与 Node.js SDK 在此方面存在差异。

---

### **B. `ManagementClient` —— 用于后台用户管理**

> 用于在服务端安全地查询、创建、更新用户信息。需使用 `USER_POOL_SECRET`，**不可用于前端**。

#### **初始化**

```python
from authing.v3.management import ManagementClient
import os

mgmt_client = ManagementClient(
    user_pool_id=os.getenv("USER_POOL_ID"),  # 必填：用户池 ID
    secret=os.getenv("USER_POOL_SECRET")     # 必填：用户池密钥，用于 API 调用鉴权
)
```

> 🔐 安全要求：`secret` 必须保密，仅用于后端服务间调用。

---

#### **核心方法**

---

##### 1. `mgmt_client.users.list(email=None, page=1, limit=10)`

###### ✅ 功能
根据条件分页查询用户列表，支持按邮箱精确查询。

###### 📥 参数

| 参数 | 类型 | 是否必填 | 说明 |
|------|------|----------|------|
| `email` | `str` | ❌ 否 | 邮箱地址，精确匹配 |
| `page` | `int` | ❌ 否 | 页码，从 1 开始，默认 1 |
| `limit` | `int` | ❌ 否 | 每页数量，最大 50，默认 10 |

###### 📤 返回值
返回一个 `dict`，结构如下：
```python
{
  "totalCount": 1,           # 总用户数
  "list": [
    {
      "userId": "63d...123",
      "email": "user@example.com",
      "nickname": "张三",
      "phone": None,
      "status": "Activated",
      ...
    }
  ]
}
```
- 若未找到，`list` 为空数组。

---

##### 2. `mgmt_client.users.create(user_info: dict)`

###### ✅ 功能
在用户池中创建一个新用户。

###### 📥 参数（`user_info` 字典）

| 字段 | 类型 | 是否必填 | 说明 |
|------|------|----------|------|
| `email` | `str` | ✅ 是 | 邮箱（唯一） |
| `password` | `str` | ✅ 是 | 密码（明文，SDK 会自动加密） |
| `nickname` | `str` | ❌ 否 | 昵称 |
| `phone` | `str` | ❌ 否 | 手机号 |
| `photo` | `str` | ❌ 否 | 头像 URL |

> 📝 注意：其他字段请参考 Authing 用户模型文档，但你**只能使用上述字段**，除非明确允许。

###### 📤 返回值
成功返回创建的用户信息 `dict`，包含 `userId`、`email` 等。

---

##### 3. `mgmt_client.users.update(user_id: str, updates: dict)`

###### ✅ 功能
更新指定用户的部分信息。

###### 📥 参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `user_id` | `str` | 用户的 `userId`（即 `sub`） |
| `updates` | `dict` | 要更新的字段键值对，如 `{"nickname": "李四", "email": "new@ex.com"}` |

> 📝 注意：
> - `email` 更新可能触发验证流程。
> - 不支持通过此方法修改密码（需用 `reset_password` 等专用接口，但你**不能使用**）。

###### 📤 返回值
返回更新后的用户信息 `dict`。

---

### ✅ 总结：你只能使用的方法清单

| 客户端 | 允许使用的方法 |
|--------|----------------|
| `AuthService` (自定义) | `verify_id_token_pyjwt(...)` (自定义实现) |
| `ManagementClient` | `mgmt_client.users.list(...)`<br>`mgmt_client.users.create(...)`<br>`mgmt_client.users.update(...)` |

> 🚫 **严禁使用其他任何方法**，如：
> - `auth_client.oidc.verify_id_token`（Python SDK 中不存在）
> - `auth_client.login`（前端用）
> - `auth_client.get_user`（需 access token）
> - `mgmt_client.roles.*`、`mgmt_client.acl.*` 等权限相关
> - 任何未在此列出的方法

---


## ✅ 3.6. 技术栈

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
| **统一身份认证平台**     | Authing         | 作为企业级身份认证中台，实现单点登录（SSO）与第三方身份源集成。当前主要用于支持用户通过企业微信、钉钉、GitHub、Google 等外部身份提供商快速登录系统。Authing 验证成功后返回标准 OIDC ID Token，后端通过 SDK 验证 Token 合法性并获取用户信息，与本地用户系统进行映射或自动注册（Just-in-Time），实现无缝融合的身份体验。 |

**集成模式说明**：Authing 不替代现有用户系统，而是作为“身份入口”，处理 SSO 和第三方认证；认证完成后，通过 `ID Token` 与本地用户进行关联或自动创建，核心用户数据仍由本地系统维护。

**3.7. [新增] JWT Token 字段架构说明**
**关键设计决策**: 当前系统在JWT Token中存储 `public_id`（UUID）而不是内部 `id`（BIGINT），这影响整个认证流程：

1. **Token结构**: JWT payload中的 `user_id` 字段存储的是 `users.public_id` 的字符串表示
2. **用户查询**: 所有基于JWT Token的用户查询都必须使用 `crud_user.get_by_uuid()` 方法
3. **字段映射**: 
   - JWT Token: `user_id` → `users.public_id` (UUID)
   - 内部关联: 使用 `users.id` (BIGINT)
4. **查询方法**: 
   - 通过JWT Token查询用户: `get_by_uuid(public_id=uuid.UUID(user_id))`
   - 通过内部ID查询用户: `get(id=user_id)`


#### **4. 通用规范与 API 定义 (General Specifications & API Definitions)**

**4.1. 权威设计文档**
##### **1. 所有实现细节必须严格遵循【用户模块设计文档authing版.md】。

##### **2. 日志记录: 在每个端点函数的入口处，应使用 logger.info() 记录请求的开始。 在成功完成数据库操作后，也应记录成功的消息。在 raise HTTPException 之前，应使用 logger.warning() 记录下具体的业务错误原因。

##### **3. 代码规范**
* 遵循 `rules.md` 中定义的团队代码规范。
* **开发语言**: 使用 Python 3.8 或更高版本。
* **代码风格**: 严格遵循 PEP 8 规范。
* **格式化**:
    * 使用 4 个空格作为缩进。
    * 所有代码文件必须使用 UTF-8 编码。

##### **4. 命名规范**
* **类名 (Class)**: 使用大驼峰命名法 (PascalCase)，例如 `LiveSession`。
* **函数与方法 (Function/Method)**: 使用下划线命名法 (snake\_case)，例如 `get_room_details`。
* **变量 (Variable)**: 使用下划线命名法 (snake\_case)，例如 `session_id`。
* **常量 (Constant)**: 使用全大写下划线命名法 (UPPER\_SNAKE\_CASE)，例如 `MAX_CONNECTIONS`。


##### **5. 通用响应结构**
所有 API 响应都必须遵循以下结构：

```json
{
  "code": int,
  "message": str,
  "data": object | None,
  "timestamp": str  // ISO 8601 格式
}
```
##### **6. 环境变量管理规范**

* **加载时机**: 在应用启动的最早阶段（如 `run.py` 或 `main.py` 文件顶部）使用 `python-dotenv` 加载环境变量文件。
* **文件位置**: 环境变量文件应放置在各功能模块的根目录下（如 `backend/users/.env`）。
* **验证机制**: 在使用环境变量的关键业务逻辑中，必须验证环境变量是否存在，缺失时抛出明确的异常。
* **动态构建**: 对于需要动态构建的配置（如 `issuer` URL），应基于基础环境变量进行构建，并提供合理的默认值。
* **日志记录**: 在读取环境变量后，应记录配置信息（注意脱敏处理敏感信息）。


#### **5. 日志与异常处理规范**

##### **5.1 日志规范**

##### **5.1.1 日志级别**
* `ERROR`: 关键系统错误、导致业务失败的异常。必须立即关注。
* `WARNING`: 潜在的问题或警告信息，不影响当前流程但需关注。
* `INFO`: 记录重要的业务操作节点，如用户登录、创建直播间等。
* `DEBUG`: 用于开发和调试阶段，记录详细的程序运行信息。

##### **5.1.2 日志格式**
每一条日志记录都应包含以下标准字段：
* 时间戳 (ISO 8601 格式)
* 日志级别 (如: INFO)
* 模块名 (如: `routers.rooms`)
* 函数名
* 行号
* 消息内容
* 异常堆栈 (仅在记录异常时包含)

##### **5.1.3 日志内容**
应记录但不限于以下关键信息：
* 系统启动与关闭事件。
* 用户认证操作（登录/登出），需注意脱敏。
* 核心业务操作的入口和结果（如创建/更新/删除房间）。
* 所有捕获到的异常信息。
* 关键性能监控数据（如 API 耗时）。

##### *5.1.4 日志管理与存储**
* **集中管理**: 使用 ELK Stack (Elasticsearch, Logstash, Kibana) 进行日志的统一收集、存储和查询。
* **存储策略**:
    * 日志文件按日期进行分割和归档。
    * 对用户密码、密钥等所有敏感信息必须进行脱敏处理。

#### **5.2 异常处理规范**

##### **5.2.1 异常分类**
* **系统异常**: 系统级错误（如数据库连接失败、中间件故障）。
* **业务异常**: 不符合业务规则的正常操作（如余额不足、库存不够）。
* **参数异常**: 用户输入参数不符合格式或校验规则。
* **权限异常**: 用户无权访问特定资源或执行特定操作。

##### **5.2.2 异常处理原则**
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

##### **5.2.3 异常处理流程**
1.  在业务代码中**捕获**可预见的异常。
2.  将原始异常**记录**到日志系统。
3.  将原始异常**转换**为对应的自定义业务异常类型。
4.  由统一的异常处理中间件捕获所有异常，并**返回**统一格式的错误响应。
5.  在必要时（如文件句柄、数据库连接），使用 `finally` 块**清理**资源。



**3.5. 响应与异常处理规范**

  * **成功响应**: 所有成功的端点返回**必须**调用 `success_response(data=...)` 函数来构建。
  * **错误响应**: 所有业务错误必须返回 `fastapi.responses.JSONResponse`，其 `content` 由 `error_response(...)` 函数构建。
  * **安全异步异常处理**: 在 `try...except` 块中，**严禁**在捕获数据库异常后访问失效的ORM对象属性。必须在 `try` 块之前将所需属性（如`current_user.id`）提取到局部变量中。

**3.6. [新增] 自定义异常类规范**

  * **任务**: 为了实现清晰的业务逻辑和错误处理分离，你需要定义一套自定义异常。
  * **执行流程**:
    1.  创建一个新文件 `app/exceptions.py`。
    2.  在该文件中，定义 `InvalidTokenException`, `InvalidCredentialsException`, `ValidationError` 等业务异常类。它们都应继承自一个共同的基类（如`BaseAppException(Exception)`)。

-----

#### **6. 具体代码修改指令 (File-by-File Modification Instructions)**

**6.1. 第一部分: `schemas/` 目录 (数据校验层)**

  * **文件**: `app/schemas/auth.py`

      * **任务**: 为新的 SSO 登录接口创建请求体模型。
      * **执行流程**:
        1.  在文件末尾，添加一个名为 `SSOLoginRequest` 的新 Pydantic 模型。
        2.  该模型应继承自 `BaseModel`。
        3.  模型内包含一个必需的 `str` 类型的字段 `id_token`。

  * **文件**: `app/schemas/users.py`

      * **任务**: 为手机号绑定接口创建请求体模型。
      * **执行流程**:
        1.  在文件末尾，添加一个名为 `PhoneBindRequest` 的新 Pydantic 模型。
        2.  该模型应继承自 `BaseModel`。
        3.  模型内包含两个必需的 `str` 类型字段：`phone_number` 和 `verification_code`。

**6.2. 第二部分: `crud/` 目录 (数据库操作层)**

  * **文件**: `app/crud/crud_user.py`
      * **任务**: 添加新的数据库查询方法以支持 SSO 和多方式登录。
      * **重要说明**: 由于JWT Token中存储的是 `public_id`（UUID），而 `deps.py` 中的用户查询需要使用这个字段，因此 `get_by_uuid` 方法是**必须实现的关键方法**。
      * **执行流程**:
        1.  **添加 `get_by_social_id` 方法**:
              * 在 `CRUDUser` 类中，添加一个新的异步方法 `get_by_social_id`。
              * **方法签名**: `async def get_by_social_id(self, db: AsyncSession, *, provider: str, social_id: str) -> Optional[models.User]:`
              * **实现**: 构建一个 SQLAlchemy `select` 语句，`where` 条件为 `social_provider` 和 `social_id` 字段同时匹配传入的参数，并返回 `scalar_one_or_none()` 的结果。
        2.  **添加 `get_by_login_identifier` 方法**:
              * 在 `CRUDUser` 类中，添加一个新的异步方法 `get_by_login_identifier`。
              * **方法签名**: `async def get_by_login_identifier(self, db: AsyncSession, *, identifier: str) -> Optional[models.User]:`
              * **实现**: 构建一个 `select` 语句，`where` 条件使用 `or_` 来匹配 `username`, `email`, 或已验证的 `phone_number` (`is_phone_verified == True`)，并返回 `scalar_one_or_none()` 的结果。

        3. **添加 `get_by_phone_number` 方法**:
                    * 在 `CRUDUser` 类中，添加一个新的异步方法 `get_by_phone_number`。
                    * **方法签名**: `async def get_by_phone_number(self, db: AsyncSession, *, phone_number: str) -> Optional[models.User]:`
                    * **实现**: 构建一个 SQLAlchemy `select` 语句，`where` 条件为 `phone_number` 字段匹配传入的参数，并返回 `scalar_one_or_none()` 的结果。
                    * **日志记录**: 在方法中添加适当的日志记录，包括查询开始、结果（找到/未找到）和可能的异常。
        4. **确保 `get_by_uuid` 方法存在**:
           * **重要**: 如果 `get_by_uuid` 方法不存在，必须添加它，因为 `deps.py` 中的用户查询依赖此方法。
           * **方法签名**: `async def get_by_uuid(self, db: AsyncSession, public_id: uuid.UUID) -> Optional[models.User]:`
           * **实现**: 构建一个 `select` 语句，`where` 条件为 `public_id` 字段匹配传入的参数，并返回 `scalar_one_or_none()` 的结果。
  
**6.3. 第三部分: `services/` 目录 (业务逻辑层)**

  * **文件**: `services/auth_service.py`

      * **任务**: 添加 Authing SSO 逻辑并增强现有登录功能。
      * **重要前置说明**: 当前系统的JWT Token中存储的是 `public_id`（UUID），而不是内部 `id`。所有Token相关的方法都必须正确处理这个字段类型。
      * 
        * **执行流程**:
           1.  * 在文件顶部，**必须**导入 `jwt` 和 `PyJWKClient`：
               ```python
               import jwt
               from jwt import PyJWKClient
               from jwt import InvalidTokenError, ExpiredSignatureError
               ```
               * 导入必要的自定义异常类（如 `InvalidTokenException`）。
          2.  **在 `AuthService` 类中添加 `verify_id_token_pyjwt` 辅助方法**:
                * **方法签名**: `def verify_id_token_pyjwt(self, id_token: str, issuer: str, audience: str, timeout: int = 5) -> dict:`
                * **实现**: 完全按照 `auth_service.py` 文件中的正确实现。
             3.  **在 `AuthService` 类中添加新的 `sso_login` 方法**:
                   * **方法签名**: `async def sso_login(self, db: AsyncSession, *, id_token: str, client_ip: str) -> dict:`
                   * **实现步骤**:
                     1.  **环境变量读取与验证**：
                          ```python
                          # 从环境变量读取配置
                          audience = os.getenv("VITE_CLIENT_ID")
                          user_pool_id = os.getenv("USER_POOL_ID")
                     
                          # 动态构建 issuer URL
                          if user_pool_id:
                              issuer = f"https://{user_pool_id}.authing.cn/oidc"
                          else:
                              # 使用默认值作为兜底
                              issuer = "https://uni-app-multiplatform.authing.cn/oidc"
                     
                          # 验证必要的环境变量
                          if not audience:
                              logger.error("VITE_CLIENT_ID 环境变量未配置")
                              raise InvalidTokenException("认证配置错误")
                     
                          logger.info(f"OIDC 配置: ISSUER={issuer}, AUDIENCE={audience}")
                          ```
            
                     2. 在 `try...except` 块中调用 `self.verify_id_token_pyjwt(id_token, issuer, audience)`。如果失败，捕获异常，记录日志，并 `raise InvalidTokenException`。
                     3. 成功后，从返回的 payload 中提取 `sub`, `email`, `nickname`。
                     4. **查找或创建用户**:
                           * 首先，调用 `crud_user.get_by_social_id` 进行精确查找。
                           * 如果未找到且 `email` 存在，则调用 `crud_user.get_by_email` 尝试链接现有账户（更新其 `social_provider` 和 `social_id`）。
                           * 如果仍未找到，则调用 `crud_user.create` 创建一个新用户（`password_hash` 为 `None`）。
                     5. 检查找到或创建的用户的 `status` 是否为 `EntityStatus.BANNED`，如果是则 `raise InvalidCredentialsException`。
                     6. **重要**: 调用已有的 `_create_access_token` 和 `_create_refresh_token` 方法生成应用的 JWT，**传入参数必须是 `str(user.public_id)`**：
                        ```python
                          access_token = self._create_access_token(str(user.public_id))
                          refresh_token = self._create_refresh_token(str(user.public_id))
                        ```
                     7. 更新用户的 `last_login_at` 和 `last_login_ip` 字段。
                     8. 提交数据库事务并返回包含 tokens 的字典。
                   3.  **修改现有的 `login_user` 方法**:
                         * 找到 `user = await crud_user.get_by_username(...)` 这一行。
                         * 将其**替换**为对 `crud_user.get_by_login_identifier(...)` 的调用。
                           * **重要**: 在生成Token时，必须使用 `str(user.public_id)` 而不是 `user.id`：
                   ```python
                   access_token = self._create_access_token(str(user.public_id))
                   refresh_token = self._create_refresh_token(str(user.public_id))
                   ```

* **文件**: `services/user_service.py`
* **任务**: 添加手机号绑定逻辑并增强密码验证。
* **执行流程**:
    1.  **在 `UserService` 中添加 `bind_phone_number` 方法**:
        * **方法签名**: `async def bind_phone_number(self, db: AsyncSession, *, current_user: models.User, phone_number: str, verification_code: str) -> None:`
        * **实现步骤**:
            * **a. 【已按您的要求修改】验证验证码 (Verification Code Validation):**
                1.  **获取Redis客户端**: 从 `app.core.redis_client` 导入并调用 `get_redis_client()` 函数，获取一个Redis客户端实例。
                2.  **构造Redis键**: 仿照您发送OTP验证码的流程，使用业务场景和接收者来构造唯一的Redis键。例如: `redis_key = f"otp:BIND_PHONE:{phone_number}"`。
                3.  **获取并销毁验证码**:
                    * 调用 `redis_client.get(redis_key)` 从Redis中获取存储的正确验证码。
                    * **关键**: 获取之后，**立即调用 `redis_client.delete(redis_key)` 将其删除**，以确保验证码只能被使用一次。
                4.  **校验逻辑**: 检查从Redis获取的验证码是否存在，并且是否与用户提交的 `verification_code` 相等（建议进行不区分大小写的比较）。
                5.  **处理失败**: 如果验证码不存在或不匹配，则 `raise ValidationError("手机验证码错误或已过期")`。
            * **b. 检查手机号是否已被占用**:
                   * 调用 `crud_user.get_by_phone_number(db, phone_number=phone_number)` 查询数据库。
                   * 如果返回的用户存在且 `user.id != current_user.id`，说明手机号已被其他用户绑定。
                   * 此时应该 `raise ValidationError("该手机号已被其他账号绑定")`。
            * **c. 更新用户信息**: 设置 `current_user.phone_number = phone_number` 和 `current_user.is_phone_verified = True`。
            * **d. 提交事务**: 将 `current_user` 对象添加到会话中并提交数据库事务。
    2.  **增强 `_validate_password_strength` 方法**:
        * 找到此辅助方法。
        * 将其内部逻辑从简单的长度检查，替换为**同时要求**最小长度（8位）、大写字母、小写字母、数字和特殊字符的检查。
    3.  **修改 `register_user` 方法**:
        * 找到对密码长度的硬编码检查（如 `if len(...) < 6:`）。
        * 将其**替换**为对增强后的 `_validate_password_strength` 辅助方法的调用。

**6.4. 第四部分: `api/v1/endpoints/` 目录 (端点层)**

**前置要求**: 
1. 确保在应用启动时已正确加载环境变量文件，否则 `AuthService` 中的环境变量读取将失败。
2. **重要**: 由于JWT Token中存储的是 `public_id`（UUID），而 `deps.py` 中的用户查询需要使用 `public_id` 字段，必须使用 `crud_user.get_by_uuid()` 方法。

**文件**: `api/v1/deps.py`
**任务**: 修改 `get_current_user` 依赖函数，使其能够正确处理UUID类型的 `public_id`
**执行流程**:
1. 在文件顶部添加 `import uuid`
2. **修改用户查询逻辑**: 将 `user = await crud_user.get(db, user_id)` 替换为：
   ```python
   user = await crud_user.get_by_uuid(db, public_id=uuid.UUID(user_id))
   ```
3. **添加UUID验证**: 在查询前添加UUID格式验证：
   ```python
   try:
       user_uuid = uuid.UUID(user_id)
   except ValueError:
       logger.warning(f"令牌中的user_id格式无效: {user_id}")
       raise HTTPException(
           status_code=401,
           detail="认证凭证格式错误",
           headers={"WWW-Authenticate": "Bearer"}
       )
   ```

  * **文件**: `api/v1/endpoints/auth.py`
      * **前置要求**: 
        1. 确保在应用启动时已正确加载环境变量文件，否则 `AuthService` 中的环境变量读取将失败。
        2. **重要**: 由于JWT Token中存储的是 `public_id`（UUID），而 `deps.py` 中的用户查询需要使用 `public_id` 字段，必须使用 `crud_user.get_by_uuid()` 方法。

      * **任务**: 暴露新的 Authing SSO 端点，并确保响应处理符合规范。
      * **执行流程**:
        1.  导入 `SSOLoginRequest`, `JSONResponse`, `success_response`, `error_response`。
        2.  **添加新端点 `POST /sso-login`**:
              * 使用 `@router.post("/sso-login", response_model=schemas.TokenResponse)` 装饰器。
              * 函数内实例化 `AuthService`。
              * 使用 `try...except` 块包裹对 `auth_service.sso_login` 的调用。
              * `except InvalidTokenException`: 返回状态码为 `401` 的 `JSONResponse`，`content` 由 `error_response(code=3005, message='认证凭证无效')` 构建。
              * `except InvalidCredentialsException`: 返回状态码为 `401` 的 `JSONResponse`，`content` 由 `error_response(code=3004, message=str(e))` 构建。
              * `except Exception`: 返回状态码为 `500` 的 `JSONResponse`，`content` 由 `error_response(code=1002, message='服务器内部错误')` 构建。
              * **成功时**: **必须**调用 `success_response(data=...)` 来构建, 将`auth_service` 返回的 token 字典赋值给data 。

  * **文件**: `api/v1/endpoints/users.py`

      * **任务**: 暴露手机号绑定端点，并确保响应处理符合规范。
      * **执行流程**:
        1.  导入 `PhoneBindRequest`, `JSONResponse`, `success_response`, `error_response`。
        2.  **添加新端点 `POST /me/phone`**:
              * 使用 `@router.post("/me/phone")` 装饰器。
              * 函数依赖注入 `current_user`。
              * **【安全日志准备】**: 在 `try` 块之前，提取 `user_id_for_logging = current_user.id`。
              * 在 `try...except` 块中调用 `user_service.bind_phone_number`。
              * **成功时**: 返回 `success_response(data=None, message="手机号绑定成功")`。
              * `except ValidationError`: 返回状态码为 `400` 的 `JSONResponse`，`content` 由 `error_response(code=4006, message=str(e))` 构建。
              * `except Exception`: 返回状态码为 `500` 的 `JSONResponse`，`content` 由 `error_response(code=1002, message='服务器内部错误')` 构建。

-----

#### **7. 最终交付 (Final Deliverable)**

请请根据以上所有要求和此核心约束， 特别是**在生成这些文件时，必须严格遵守以下原则：只应用前面指令中明确描述的增量添加和最小修改。对于指令中未提及的任何已有代码，必须保持其原始样貌，不得进行任何形式的重构、格式化调整或逻辑变更**，，为我生成 **`schemas/auth.py`, `schemas/users.py`, `crud/crud_user.py`, `services/auth_service.py`, `services/user_service.py`, `api/v1/endpoints/auth.py`, `api/v1/endpoints/users.py`** 这七个文件被修改后的**完整代码**。
