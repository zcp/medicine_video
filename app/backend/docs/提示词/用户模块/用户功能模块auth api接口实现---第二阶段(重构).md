
-----
### **最终版：高效 AI 代码重构提示词 (Auth模块: 引入Service层)**

#### **1. 角色定义 (Role Definition)**

你是一名资深的 Python 后端架构师，精通分层架构设计（特别是 `Endpoint -> Service -> CRUD` 模式），并擅长将包含复杂业务逻辑的 FastAPI 端点，安全、高效地重构到独立的服务层中。

#### **2. 任务目标 (Task Objective)**

你的核心任务是**重构**现有的 `app/api/v1/endpoints/auth.py` 文件。具体包括：

1.  **【新增文件】** 创建一个全新的**服务层**文件 `app/services/auth_service.py`。
2.  **【逻辑迁移】** 将 `auth.py` 中所有的**业务逻辑**（如验证码处理、密码哈希、JWT操作、Redis交互等）**完整地、安全地迁移**到新的 `AuthService` 类中。
3.  **【重构文件】** **重写** `app/api/v1/endpoints/auth.py` 文件，使其变得非常简洁。重构后的端点函数**严禁**包含任何业务逻辑，必须改为调用 `AuthService` 中对应的方法。

#### **3. 核心上下文信息 (Core Context Information)**

**3.1. 项目结构 (重构后)**

```
users/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/
│   │       │   └── auth.py       # <-- 需要重构
│   ├── crud/
│   │   └── crud_user.py         # <-- 作为依赖
│   ├── services/                 # <-- 【新增】Service层目录
│   │   ├── __init__.py
│   │   └── auth_service.py   # <-- 目标文件 1 (新文件)
...
```

**3.2. 需要被重构的源代码**
*你必须根据以下 `auth.py` 的完整代码进行重构。*

  * `@app/api/v1/endpoints/auth.py` (即您上传的 `auth.py` 文件)

**3.3. 依赖的上下文**
*在重构过程中，你需要依赖以下模块*

  * `@app/crud/crud_user.py`
  * `@app/models/users.py`
  * `@app/schemas/users.py`
  * `@app/core/responses.py`
  * `@app/core/redis_client.py`
  * `@app/database.py`

-----
**3.3. 已存在的代码全文 (Full Text of Existing Code)**

@app/api/v1/endpoint/auth.py

#### **4. 通用规范与 API 定义 (General Specifications & API Definitions)**

**4.1. 权威设计文档**
##### **1. 所有实现细节必须严格遵循【直播核心功能设计文档.md】。

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



#### **6. 具体代码生成指令 (Specific Code Generation Instructions)**

**【关键指令】** 你在执行本次重构时，**必须严格遵守**以下所有规范：

##### **6.1. 服务层 (`AuthService`) 设计规范**

  * **类化设计**: 在 `app/services/auth_service.py` 中创建一个 `AuthService` 类。
  * **依赖注入**: `AuthService` 的 `__init__` 方法应接收 `db: AsyncSession` 和 `redis_client` 作为参数，供其内部方法使用。
  * **职责**:
      * 封装所有**图形验证码**的生成和校验逻辑。
      * 封装所有**OTP验证码**的发送流程（频率限制、业务检查、生成存储）。
      * 封装完整的**用户登录**认证流程（密码验证、状态检查）。
      * 封装所有 **JWT** 操作（创建 `access_token` 和 `refresh_token`、验证 Token、Token 黑名单处理）。
      * 封装完整的**密码重置**流程。

##### **6.2. 端点层 (`auth.py`) 重构规范**

  * **保持简洁**: 重构后的端点函数体应该非常简短。
  * **职责**:
      * 只负责处理 FastAPI 的 `Request` 和 `Depends`。
      * 实例化 `AuthService`。
      * 调用 `AuthService` 中对应的方法来执行业务逻辑。
      * 使用 `success_response` 和 `error_response` 来构建并返回最终的 `JSONResponse`。比如：## 3. 响应处理规范 (Response Handling)

### ✅ 成功响应

- 所有成功返回**必须**调用 `success_response(data=...)` 函数构建响应内容。
- 示例：
  ```python
  return success_response(data=user_info)
  ```

### ❌ 错误响应

- 所有业务错误必须返回 `fastapi.responses.JSONResponse`，其 `content` 由 `error_response(...)` 构建。
- 示例：
  ```python
  return JSONResponse(
      status_code=400,
      content=error_response(code=1001, message='参数错误')
  )
  ```
  * **禁止**: **严禁**在重构后的端点函数中直接调用 `crud_*` 模块、`redis_client` 或执行任何业务逻辑计算。

##### **6.3. 安全与编码规范**

  * **【应用核心原则】** 在所有 `Service` 层的方法中，**必须**遵循“**安全异步异常处理**”原则。在 `try...except` 块外提前提取 ORM 对象的属性，以防止 `MissingGreenlet` 错误。
  * **【应用核心原则】** 所有外部服务的连接信息（如JWT密钥）**必须**通过环境变量读取。比如：- 示例：
  ```python
  import os
  redis_host = os.getenv("REDIS_HOST", "localhost")
  redis_port = os.getenv("REDIS_PORT", "6379")
  ```
- 目的：确保代码在本地、Docker、测试、生产等不同环境下**无需修改即可运行**。

-----

#### **7. 具体代码生成指令 (Specific Code Generation Instructions)**


### **重构指令：为 `app/services/auth_service.py` 生成方法**

**说明**：以下所有指令都用于在新的 `AuthService` 类中创建对应的方法。

#### **1. `generate_captcha(self) -> dict`**

* **业务逻辑流程**:
    1.  调用 `uuid.uuid4()` 生成 `captcha_id`。
    2.  调用内部工具函数生成一个4-6位的随机字符串作为 `captcha_solution`。
    3.  将 `captcha_id` 作为键，`captcha_solution`（转为小写）作为值，存入 Redis，并设置3分钟过期时间。
    4.  使用 `captcha` 库，根据 `captcha_solution` 生成图片数据。
    5.  将图片数据进行 Base64 编码。
    6.  返回一个包含 `captcha_id` 和 `image_base64` 的字典。

#### **2. `send_otp_code(self, otp_request: schemas.VerificationCodeRequest) -> dict`**

* **业务逻辑流程**:
    1.  **图形验证码校验**: 调用 `self.verify_captcha()` (一个内部方法) 校验 `otp_request.captcha_id` 和 `otp_request.captcha_solution` 的正确性。如果失败，`raise CaptchaErrorException()`。
    2.  **频率限制**: 检查 `otp_request.recipient` 或请求IP的请求频率。如果超限，`raise RateLimitException()`。
    3.  **业务前置检查**:
        * 如果 `otp_request.scenario` 是 `'REGISTER'`，则调用 `crud_user.get_by_email()` 检查邮箱是否**已存在**。如果已存在，`raise UserAlreadyExistsException()`。
        * 如果 `otp_request.scenario` 是 `'PASSWORD_RESET'`，则调用 `crud_user.get_by_email()` 检查邮箱是否**不存在**。如果不存在，为了安全应直接返回成功，不抛出异常。
    4.  **生成与存储**: 生成6位数字OTP，以 `(scenario, recipient)` 为键存入 Redis，设置5分钟过期。
    5.  **异步发送**: （模拟）将发送邮件/短信的任务推送到后台任务队列。
    6.  返回一个包含 `recipient_masked` 和 `cooldown_seconds` 的成功信息字典。

#### **3. `login_user(self, login_request: schemas.LoginRequest) -> dict`**

* **业务逻辑流程**:
    1.  **图形验证码校验**: 调用 `self.verify_captcha()` 校验 `login_request.captcha_id` 和 `login_request.captcha_solution`。如果失败，`raise CaptchaErrorException()`。
    2.  **用户查询**: 调用 `crud_user.get_by_username()` 查询用户。
    3.  **状态与密码校验**:
        * 如果用户不存在，或者 `user.status` 不为 `NORMAL`，或者 `verify_password()` 校验密码失败，`raise InvalidCredentialsException("用户名或密码错误")`。
    4.  **Token 生成**: 调用内部的JWT工具函数，为该 `user.id` 生成 `access_token` 和 `refresh_token`。
    5.  **信息更新**: 更新用户的 `last_login_at` 和 `last_login_ip` 字段。
    6.  调用 `db.commit()` 和 `db.refresh(user)` 提交更改。
    7.  返回包含 `access_token`, `refresh_token`, `token_type` 的字典。

#### **4. `refresh_access_token(self, refresh_token: str) -> dict`**

* **业务逻辑流程**:
    1.  **Token 验证**: 调用 `verify_token(refresh_token, token_type="refresh")` 验证 `refresh_token`。如果返回 `None` (无效或过期)，`raise InvalidTokenException()`。
    2.  **黑名单检查**: 调用 `is_token_blacklisted()` 检查该 `refresh_token` 是否已在 Redis 黑名单中。如果是，`raise InvalidTokenException()`。
    3.  从验证通过的 `payload` 中获取 `user_id`。
    4.  **Token 生成**: 为该 `user_id` 调用 `create_access_token()` 生成一个新的 `access_token`。
    5.  返回包含新的 `access_token` 和 `token_type` 的字典。

#### **5. `logout_user(self, access_token: str)`**

* **业务逻辑流程**:
    1.  **Token 验证**: 调用 `verify_token(access_token, token_type="access")` 验证 `access_token`。如果返回 `None`，`raise InvalidTokenException()`。
    2.  从 `payload` 中计算出 Token 的剩余有效时间。
    3.  **加入黑名单**: 调用 `blacklist_token()` 将该 `access_token` 加入 Redis 黑名单，并设置正确的过期时间。
    4.  （可选）将关联的 `refresh_token` 也一并拉黑。
    5.  操作完成，无需返回值。

#### **6. `request_password_reset(self, reset_request: schemas.PasswordResetRequest)`**

* **业务逻辑流程**:
    1.  **图形验证码校验**: 调用 `self.verify_captcha()`。如果失败，`raise CaptchaErrorException()`。
    2.  **用户查询**: 调用 `crud_user.get_by_email(email=reset_request.email)`。
    3.  **安全处理**: 如果用户**不存在**，为了防止邮箱枚举攻击，**直接返回**，不执行任何操作也不抛出异常。
    4.  **Token 生成**: 如果用户存在，生成一个唯一的、加密安全的 `reset_token` (例如 `secrets.token_urlsafe(32)`)。
    5.  **存入缓存**: 将 `reset_token` 作为键，`user.id` 作为值，存入 Redis，并设置15分钟过期。
    6.  **异步发送**: 异步发送一封包含密码重置链接的邮件给用户。
    7.  操作完成，无需返回值。

#### **7. `perform_password_reset(self, confirm_request: schemas.PasswordResetConfirmRequest)`**

* **业务逻辑流程**:
    1.  **Token 验证**: 从 Redis 中使用 `confirm_request.reset_token` 查询对应的 `user_id`。如果查询不到（无效或过期），`raise InvalidResetTokenException()`。
    2.  **Token 销毁**: 查询成功后，**立即**从 Redis 中删除该 `reset_token` 键，确保一次性使用。
    3.  **密码强度验证**: 调用 `validate_password_strength(confirm_request.new_password)`。如果不符合，`raise WeakPasswordException()`。
    4.  **密码哈希**: 对 `new_password` 进行加盐哈希。
    5.  **数据库更新**:
        * a. 调用 `crud_user.get(id=user_id)` 获取用户对象。
        * b. 调用 `crud_user.update()` 更新用户的 `password_hash` 字段。
    6.  操作完成，无需返回值。
  


#### **8. 最终交付 (Final Deliverable)**

请根据以上所有要求，为我生成以下**两个文件**的完整、可直接使用的 Python 代码。请将每个文件的代码放在独立的、有明确标记的代码块中。

1.  `app/services/auth_service.py` **(新文件)**
2.  `app/api/v1/endpoints/auth.py` **(重构后的完整版)**