
-----

### **批次一：核心认证流程 (Batch 1: Core Authentication Flow)**
  * **目标**: 让一个用户能够成功注册和登录，打通最基础的流程，为后续所有功能提供认证基础。
### 1.1. 获取图形验证码 (CAPTCHA)

  * **Endpoint**: `GET /api/v1/auth/captcha`
  * **功能描述**: 生成一个唯一的、有时效性的图形验证码挑战，用于人机识别，防止机器人攻击。
  * **认证**: 无需认证。
  * **请求参数**: 无。
  * **成功响应** (`200 OK`):
    ```json
    {
      "code": 200,
      "message": "success",
      "data": {
        "captcha_id": "c1b2d3a4-e5f6-4a1b-8c3d-e5f6a1b2c3d4",
        "image_base64": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUg..."
      },
      "timestamp": "2025-07-23T11:00:00Z"
    }
    ```
  * **失败响应示例** (`500 Internal Server Error` - 缓存服务异常):
    ```json
    {
      "code": 1001,
      "message": "系统内部错误",
      "data": {
        "error": "无法连接到缓存服务"
      },
      "timestamp": "2025-07-23T11:00:05Z"
    }
    ```
  * **实现流程描述**:
    1.  **生成唯一ID**: 使用 `uuid.uuid4()` 生成 `captcha_id`。
    2.  **生成随机答案**: 生成一个4-6位的随机字母数字组合。
    3.  **存入缓存**: 将 `captcha_id` 作为键，答案（转为小写）作为值，存入 Redis，并设置3分钟过期时间。
    4.  **生成图片**: 使用图像处理库（如 Pillow）将答案绘制成带有干扰的图片。
    5.  **编码与返回**: 将图片进行 Base64 编码，并与 `captcha_id` 一并返回。

### 1.2. 发送OTP验证码 (邮件/短信)

  * **Endpoint**: `POST /api/v1/auth/verification-codes`
  * **功能描述**: 根据业务场景，向用户的邮箱或手机发送一个有时效性的OTP验证码。此接口受图形验证码保护。
  * **认证**: 无需认证。
  * **请求体** (`application/json`):
    ```json
    {
      "channel": "EMAIL",
      "recipient": "newuser@example.com",
      "scenario": "REGISTER",
      "captcha_id": "c1b2d3a4-e5f6-4a1b-8c3d-e5f6a1b2c3d4",
      "captcha_solution": "aB5DeF"
    }
    ```
  * **成功响应** (`200 OK`):
    ```json
    {
      "code": 200,
      "message": "success",
      "data": {
        "message": "验证码已发送，请注意查收。",
        "recipient_masked": "n******r@example.com",
        "cooldown_seconds": 60
      },
      "timestamp": "2025-07-23T10:30:00Z"
    }
    ```
  * **失败响应示例** (`429 Too Many Requests` - 请求过于频繁):
    ```json
    {
      "code": 4029,
      "message": "请求过于频繁",
      "data": {
        "error": "请在 60 秒后重试"
      },
      "timestamp": "2025-07-23T10:33:00Z"
    }
    ```
  * **实现流程描述**:
    1.  **图形验证码校验**: 首先校验 `captcha_id` 和 `captcha_solution` 的正确性。
    2.  **参数校验**: 验证 `channel`, `recipient`, `scenario` 的格式和取值。
    3.  **频率限制**: 检查 `recipient` 或 IP 的请求频率，防止滥用。
    4.  **业务前置检查**: 根据 `scenario` 检查用户是否存在（如注册时应不存在，重置密码时应存在）。
    5.  **生成与存储**: 生成6位数字OTP，以 `(scenario, recipient)` 为键存入 Redis，设置5分钟过期。
    6.  **异步发送**: 将发送邮件/短信的任务推送到后台任务队列（如 Celery）。
    7.  **立即返回**: 立即向客户端返回成功响应。


  * **Endpoint**: `POST /api/v1/users/register`
  * **功能描述**: 创建一个新的用户账户。**在第一阶段，此接口仅使用图形验证码进行人机识别。**
  * **认证**: 无需认证。
  * **请求体** (`application/json`):
    ```json
    {
      "username": "newuser",
      "email": "newuser@example.com",
      "password": "strongpassword123",
      "nickname": "新手上路",
      "captcha_id": "c1b2d3a4-e5f6-4a1b-8c3d-e5f6a1b2c3d4",
      "captcha_solution": "aB5DeF"
    }
    ```
      * **`verification_code`** 字段在此阶段**已被移除**。
      * 新增 **`captcha_id`** 和 **`captcha_solution`** 字段，用于图形验证码校验。

  * **成功响应** (`200 OK`):

    ```json
    {
      "code": 200,
      "message": "success",
      "data": {
        "uuid": "a1b2c3d4-e5f6-4a1b-8c3d-e5f6a1b2c3d4",
        "username": "newuser",
        "nickname": "新手上路"
      },
      "timestamp": "2025-07-22T20:00:00Z"
    }
    ```

  * **失败响应示例** (`400 Bad Request` - 图形验证码错误):

    ```json
    {
      "code": 4003,
      "message": "参数校验失败",
      "data": {
        "error": "图形验证码错误或已过期"
      },
      "timestamp": "2025-07-23T12:00:00Z"
    }
    ```

  * **实现流程描述**:

    1.  **图形验证码校验**: 首先从 Redis 中获取与 `captcha_id` 对应的正确答案，与用户提交的 `captcha_solution` 进行比对。若不匹配或键不存在，返回 400 错误。成功后立即删除该键。
    2.  **参数校验**: 验证 `username`, `email`, `password`, `nickname` 等字段的格式和长度。
    3.  **唯一性检查**: 检查 `username` 和 `email` 是否已被占用。若占用，返回 409 Conflict 错误。
    4.  **密码处理**: 对 `password` 进行加盐哈希，生成 `password_hash`。
    5.  **创建记录**: 创建 `users` 表的新记录。**注意：在第一阶段，`is_email_verified` 和 `is_phone_verified` 字段应保持其默认值 `false`**，因为邮箱和手机尚未经过OTP验证。
    6.  **提交与返回**: 提交数据库事务，并返回新用户的公开信息。


### 1.3. 用户登录

  * **Endpoint**: `POST /api/v1/auth/login`
  * **功能描述**: 通过用户名/密码进行身份验证，成功后返回 Access Token 和 Refresh Token。此接口受图形验证码保护。
  * **认证**: 无需认证。
  * **请求体** (`application/json`):
    ```json
    {
      "username": "testuser",
      "password": "password123",
      "captcha_id": "d1e2f3a4-e5f6-4a1b-8c3d-e5f6a1b2c3d4",
      "captcha_solution": "xY7zPq"
    }
    ```
  * **成功响应** (`200 OK`):
    ```json
    {
      "code": 200,
      "message": "success",
      "data": {
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "refresh_token": "a1b2c3d4e5f6...",
        "token_type": "bearer"
      },
      "timestamp": "2025-07-22T19:50:00Z"
    }
    ```
  * **失败响应示例** (`401 Unauthorized` - 密码错误):
    ```json
    {
      "code": 3001,
      "message": "用户名或密码错误",
      "data": null,
      "timestamp": "2025-07-22T19:51:00Z"
    }
    ```
  * **实现流程描述**:
    1.  **图形验证码校验**: 首先校验 `captcha_id` 和 `captcha_solution` 的正确性。
    2.  **用户查询**: 根据 `username` 查询 `users` 表（可匹配 `username` 或 `email` 字段）。
    3.  **状态与密码校验**: 检查用户 `status` 是否为 `NORMAL`，并验证 `password_hash`。
    4.  **Token 生成**: 生成 JWT 格式的 `access_token` 和 `refresh_token`。
    5.  **信息更新**: 更新用户的 `last_login_at` 和 `last_login_ip` 字段。
    6.  **提交与返回**: 提交数据库事务，并返回 Token 信息。


批次二：认证生命周期与用户自我管理 (Batch 2: Auth Lifecycle & User Self-Management)
目标: 完善Token管理和用户对自身信息的管理，构建完整的用户个人中心功能。

#### 2.2. 获取当前用户信息

  * **Endpoint**: `GET /api/v1/users/me`
  * **功能描述**: 获取当前已登录用户的详细个人资料。
  * **认证**: 需要提供有效的 `Access Token`。
  * **请求参数**: 无。
  * **成功响应** (`200 OK`):
    ```json
    {
      "code": 200,
      "message": "success",
      "data": {
        "uuid": "a1b2c3d4-e5f6-4a1b-8c3d-e5f6a1b2c3d4",
        "username": "testuser",
        "email": "testuser@example.com",
        "nickname": "测试用户",
        "avatar_url": null,
        "bio": null,
        "role": "REGULAR",
        "status": "NORMAL",
        "is_email_verified": true
      },
      "timestamp": "2025-07-22T20:05:00Z"
    }
    ```
  * **失败响应示例** (`401 Unauthorized` - Token无效):
    ```json
    {
      "code": 3004,
      "message": "认证凭证无效",
      "data": {
        "error": "Token has expired or is invalid"
      },
      "timestamp": "2025-07-22T20:06:00Z"
    }
    ```
  * **实现流程描述**:
    1.  从 `Authorization` Header 中解析 `Access Token` 并验证其有效性。
    2.  从 Token 的载荷 (payload) 中解析出用户的内部ID (`id`)。
    3.  根据 `id` 查询 `users` 表获取完整的用户记录。
    4.  若用户不存在或状态异常（如 `BANNED`），返回 401 或 403 错误。
    5.  将查询结果序列化为 Pydantic 模型（过滤掉 `password_hash` 等敏感字段），并返回。

#### 2.3. 更新当前用户信息

  * **Endpoint**: `PATCH /api/v1/users/me`
  * **功能描述**: 更新当前用户的公开个人资料，如昵称、简介、头像。
  * **认证**: 需要提供有效的 `Access Token`。
  * **请求体** (`application/json`):
    ```json
    {
      "nickname": "资深测试用户",
      "bio": "更新后的个人简介。"
    }
    ```
  * **成功响应** (`200 OK`): (返回更新后的完整用户对象)
    ```json
    {
      "code": 200,
      "message": "success",
      "data": {
        "uuid": "a1b2c3d4-...", "username": "testuser", "email": "testuser@example.com",
        "nickname": "资深测试用户", "avatar_url": null, "bio": "更新后的个人简介。",
        "role": "REGULAR", "status": "NORMAL", "is_email_verified": true
      },
      "timestamp": "2025-07-22T20:08:00Z"
    }
    ```
  * **失败响应示例** (`400 Bad Request` - 昵称过长):
    ```json
    {
      "code": 4001,
      "message": "参数校验失败",
      "data": {
        "field": "nickname",
        "error": "昵称长度不能超过50个字符"
      },
      "timestamp": "2025-07-23T12:05:00Z"
    }
    ```
  * **实现流程描述**:
    1.  解析 `Access Token` 获取用户ID。
    2.  根据ID查询 `users` 表获取用户对象。
    3.  创建一个仅包含允许用户修改字段 (`nickname`, `avatar_url`, `bio`) 的 Pydantic 模型来解析请求体，以防权限提升攻击。
    4.  遍历 Pydantic 模型中已设置的字段，更新用户对象的相应属性。
    5.  提交数据库事务。
    6.  返回更新后的完整用户信息。

#### 2.4. 用户注销账户

  * **Endpoint**: `DELETE /api/v1/users/me`
  * **功能描述**: 用户软删除自己的账户。
  * **认证**: 需要提供有效的 `Access Token`。
  * **请求参数**: 无。
  * **成功响应** (`200 OK`):
    ```json
    {
      "code": 200,
      "message": "success",
      "data": null,
      "timestamp": "2025-07-22T21:10:00Z"
    }
    ```
  * **失败响应示例** (`403 Forbidden` - 账户有未完成的业务):
    ```json
    {
      "code": 2002,
      "message": "业务逻辑错误",
      "data": {
        "error": "账户下存在有效会员，请先处理"
      },
      "timestamp": "2025-07-23T12:10:00Z"
    }
    ```
  * **实现流程描述**:
    1.  解析 `Access Token` 获取用户ID。
    2.  （可选）执行安全校验，如要求用户再输入一次密码进行确认。
    3.  （可选）执行业务检查，如确认用户没有正在进行的订阅或交易。若有，返回 403 错误。
    4.  将该用户的 `status` 字段更新为 `'DELETED'` (或 `'DEACTIVATED'`)。
    5.  将该用户的所有 Token 加入黑名单，强制其下线。
    6.  提交数据库事务，返回成功响应。


### 1.4. 刷新令牌

  * **Endpoint**: `POST /api/v1/auth/refresh`
  * **功能描述**: 使用有效的 `refresh_token` 获取一个新的 `access_token`。
  * **认证**: 无需认证。
  * **请求体** (`application/json`):
    ```json
    {
      "refresh_token": "a1b2c3d4e5f6..."
    }
    ```
  * **成功响应** (`200 OK`):
    ```json
    {
      "code": 200,
      "message": "success",
      "data": {
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9_new...",
        "token_type": "bearer"
      },
      "timestamp": "2025-07-22T21:00:00Z"
    }
    ```
  * **失败响应示例** (`401 Unauthorized` - Refresh Token无效或过期):
    ```json
    {
      "code": 3003,
      "message": "凭证无效或已过期",
      "data": {
        "error": "Invalid or expired refresh token"
      },
      "timestamp": "2025-07-22T21:01:00Z"
    }
    ```
  * **实现流程描述**:
    1.  验证 `refresh_token` 的有效性（是否存在、未过期、未在黑名单中）。
    2.  若有效，为该 Token 关联的用户生成一个新的 `access_token`。
    3.  返回新的 `access_token`。

### 1.5. 用户登出

  * **Endpoint**: `POST /api/v1/auth/logout`
  * **功能描述**: 用户主动登出，使其持有的 Token 失效。
  * **认证**: 需要提供有效的 `Access Token`。
  * **请求参数**: 无请求体，Token 通过 `Authorization` Header 传递。
  * **成功响应** (`200 OK`):
    ```json
    {
      "code": 200,
      "message": "success",
      "data": null,
      "timestamp": "2025-07-22T21:05:00Z"
    }
    ```
  * **失败响应示例** (`401 Unauthorized` - Token格式错误或已过期):
    ```json
    {
      "code": 3004,
      "message": "认证凭证格式无效",
      "data": null,
      "timestamp": "2025-07-22T21:06:00Z"
    }
    ```
  * **实现流程描述**:
    1.  解析 `access_token` 获取其唯一标识（`jti`）。
    2.  将该 `access_token` 和关联的 `refresh_token` 标识加入到 Redis 黑名单中，并设置适当的过期时间。
    3.  返回成功响应。
好的，收到您的指示。我将严格按照最详尽的标准，为您完善“资源: 用户 (Users) - 公开接口”这一章节，确保每个接口都包含完整的**请求说明**、**成功响应体**、**失败响应体**和**执行流程**。

#### **(新增) 1.6. 修改密码 (用户已登录)**

  * **Endpoint**: `POST /api/v1/users/me/password`
  * **功能描述**: 当前已登录的用户修改自己的密码。为保证安全，此操作需要用户提供其**当前密码**。
  * **认证**: 需要提供有效的 `Access Token`。
  * **请求体** (`application/json`):
    ```json
    {
      "current_password": "old_password123",
      "new_password": "a_very_strong_new_password"
    }
    ```
      * *前端提示：建议增加一个“确认新密码”的输入框，并在前端校验两次输入的新密码是否一致，后端只需接收一次 `new_password` 即可。*
  * **成功响应** (`200 OK`):
    ```json
    {
      "code": 200,
      "message": "密码修改成功",
      "data": null,
      "timestamp": "2025-07-23T23:00:00Z"
    }
    ```
  * **失败响应示例** (`400 Bad Request` - 当前密码错误):
    ```json
    {
      "code": 4004,
      "message": "参数校验失败",
      "data": {
        "error": "当前密码不正确"
      },
      "timestamp": "2025-07-23T23:01:00Z"
    }
    ```
  * **实现流程描述**:
    1.  从 `Access Token` 中解析出用户ID。
    2.  根据用户ID查询 `users` 表，获取 `password_hash`。
    3.  验证请求体中的 `current_password` 与存储的 `password_hash` 是否匹配。若不匹配，返回 400 错误。
    4.  验证 `new_password` 是否符合密码强度策略（如长度、复杂度等）。
    5.  对 `new_password` 进行加盐哈希，生成新的 `password_hash`。
    6.  更新数据库中该用户的 `password_hash` 字段。
    7.  **安全增强**: 使该用户的所有旧 Token 和 Refresh Token 失效，强制其在其他设备上重新登录。
    8.  提交事务，并返回成功响应。

#### **(新增) 1.7. 忘记密码/重置密码流程 (用户未登录)**

此流程分为两步：请求重置 和 执行重置。

##### **步骤一: 请求密码重置**

  * **Endpoint**: `POST /api/v1/auth/password-reset-request`
  * **功能描述**: 用户提供注册邮箱，系统向该邮箱发送一个包含有时效性重置令牌的链接。此接口受图形验证码保护。
  * **认证**: 无需认证。
  * **请求体** (`application/json`):
    ```json
    {
      "email": "user@example.com",
      "captcha_id": "e1f2a3b4-...",
      "captcha_solution": "kL9mN2"
    }
    ```
  * **成功响应** (`200 OK`):
    ```json
    {
      "code": 200,
      "message": "success",
      "data": {
        "message": "如果该邮箱已注册，一封密码重置邮件已发送至您的邮箱。"
      },
      "timestamp": "2025-07-23T23:10:00Z"
    }
    ```
      * *注意：为防止泄露用户信息，无论邮箱是否存在，都应返回模糊的成功提示。*
  * **失败响应示例**: (`400 Bad Request` - 图形验证码错误)
  * **实现流程描述**:
    1.  校验图形验证码。
    2.  校验 `email` 格式。
    3.  查询 `users` 表确认该 `email` 是否存在。**如果不存在，直接返回成功响应，不执行后续操作**。
    4.  如果存在，生成一个唯一的、有时效性（如15分钟）的 `reset_token`。
    5.  将 `(reset_token, user_id)` 存入 Redis 并设置过期时间。
    6.  异步发送一封包含密码重置链接（如 `https://yoursite.com/reset-password?token=...`）的邮件给用户。
    7.  返回成功响应。

##### **步骤二: 执行密码重置**

  * **Endpoint**: `POST /api/v1/auth/password-reset`
  * **功能描述**: 用户通过重置令牌设置新密码。
  * **认证**: 无需认证。
  * **请求体** (`application/json`):
    ```json
    {
      "reset_token": "unique_reset_token_from_email",
      "new_password": "a_very_strong_new_password"
    }
    ```
  * **成功响应** (`200 OK`):
    ```json
    {
      "code": 200,
      "message": "密码重置成功",
      "data": null,
      "timestamp": "2025-07-23T23:20:00Z"
    }
    ```
  * **失败响应示例** (`400 Bad Request` - 令牌无效或过期):
    ```json
    {
      "code": 4005,
      "message": "无效的令牌",
      "data": {
        "error": "密码重置链接无效或已过期"
      },
      "timestamp": "2025-07-23T23:21:00Z"
    }
    ```
  * **实现流程描述**:
    1.  从请求体获取 `reset_token` 和 `new_password`。
    2.  在 Redis 中查询 `reset_token` 是否存在。若不存在，返回 400 错误。
    3.  从 Redis 中获取关联的 `user_id`，并立即删除该键。
    4.  验证 `new_password` 的强度。
    5.  对 `new_password` 进行加盐哈希。
    6.  更新对应 `user_id` 的 `password_hash` 字段。
    7.  提交事务，返回成功响应。
    


批次三：会员产品公开接口 (Batch 3: Public Membership Product Interface)
目标: 让所有用户（包括未登录的）能够看到可购买的会员产品，为会员购买流程提供“商品”数据。

#### 3.1. 获取可购买的会员产品列表

  * **Endpoint**: `GET /api/v1/membership-products`
  * **功能描述**: 公开接口，获取所有状态为 `ACTIVE` 的、可供用户购买的会员产品列表，通常用于价格或购买页面。
  * **认证**: 无需认证。
  * **请求参数 (Query)**:
      * `sort` (string, 可选): 排序字段及顺序，默认 `sort_order:asc`。例如 `price:desc`。
  * **成功响应** (`200 OK`):
    ```json
    {
      "code": 200,
      "message": "success",
      "data": {
        "items": [
          {
            "code": "VIDEO_YEARLY",
            "name": "年度影视会员",
            "description": "畅享所有视频内容，为期一年。",
            "price": "199.99",
            "level": 1,
            "duration_unit": "year",
            "duration_value": 1
          },
          {
            "code": "LIVE_FAN_MONTHLY",
            "name": "粉丝月度包",
            "description": "直播间专属粉丝徽章和彩色弹幕。",
            "price": "29.99",
            "level": 3,
            "duration_unit": "month",
            "duration_value": 1
          }
        ]
      },
      "timestamp": "2025-07-22T20:10:00Z"
    }
    ```
  * **失败响应示例** (`500 Internal Server Error` - 数据库异常):
    ```json
    {
      "code": 1002,
      "message": "数据库查询错误",
      "data": {
        "error": "An unexpected database error occurred"
      },
      "timestamp": "2025-07-22T20:11:00Z"
    }
    ```
  * **实现流程描述**:
    1.  构建 `select(membership_products)` 查询。
    2.  添加 `WHERE status = 'ACTIVE'` 的筛选条件。
    3.  根据 `sort` Query 参数（若提供）或默认的 `sort_order` 字段对结果进行排序。
    4.  执行查询，将结果序列化为对象列表并返回。

批次四：用户侧会员订阅流程 (Batch 4: User-Side Subscription Flow)
目标: 实现用户购买和管理自己订阅的完整闭环。

依赖: 批次一、二（用户认证）、批次三（产品数据）。

#### 3.2. 获取当前用户的会员订阅列表

  * **Endpoint**: `GET /api/v1/users/me/memberships`
  * **功能描述**: 获取当前登录用户的所有会员订阅记录（包括历史记录和当前生效的）。
  * **认证**: 需要提供有效的 `Access Token`。
  * **请求参数**: 支持通用分页参数 (`page`, `size`, `sort`)。
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
            "uuid": "d1e2f3a4-e5f6-4a1b-8c3d-e5f6a1b2c3d4",
            "product_code": "VIDEO_YEARLY",
            "level": 1,
            "status": "ACTIVE",
            "is_auto_renew": true,
            "start_date": "2025-01-15T10:00:00Z",
            "expires_at": "2026-01-15T10:00:00Z",
            "created_at": "2025-01-15T09:59:00Z"
          },
          {
            "uuid": "c1b2d3a4-e5f6-4a1b-8c3d-e5f6a1b2c3d4",
            "product_code": "LIVE_FAN_MONTHLY",
            "level": 3,
            "status": "EXPIRED",
            "is_auto_renew": false,
            "start_date": "2024-12-10T14:00:00Z",
            "expires_at": "2025-01-10T14:00:00Z",
            "created_at": "2024-12-10T13:59:00Z"
          }
        ]
      },
      "timestamp": "2025-07-22T20:15:00Z"
    }
    ```
  * **失败响应示例** (`401 Unauthorized` - Token无效):
    ```json
    {
      "code": 3004,
      "message": "认证凭证无效",
      "data": {
        "error": "Token has expired or is invalid"
      },
      "timestamp": "2025-07-22T20:16:00Z"
    }
    ```
  * **实现流程描述**:
    1.  从 `Access Token` 中解析出用户 `user_id`。
    2.  构建 `select(user_memberships)` 查询，并添加 `WHERE user_id = :user_id` 条件。
    3.  应用分页和排序（默认按 `created_at` 降序）。
    4.  执行查询，将结果序列化后返回。

#### 3.3. 用户购买/创建新订阅

  * **Endpoint**: `POST /api/v1/users/me/memberships`
  * **功能描述**: 用户为自己创建一个新的订阅。这是整个会员体系的核心交易接口。
  * **认证**: 需要提供有效的 `Access Token`。
  * **请求体** (`application/json`):
    ```json
    {
      "product_code": "VIDEO_YEARLY",
      "payment_token": "tok_visa_1234..."
    }
    ```
  * **成功响应** (`200 OK`):
    ```json
    {
      "code": 200,
      "message": "success",
      "data": {
        "uuid": "e1f2a3b4-e5f6-4a1b-8c3d-e5f6a1b2c3d4",
        "product_code": "VIDEO_YEARLY",
        "level": 1,
        "status": "ACTIVE",
        "is_auto_renew": true,
        "start_date": "2025-07-23T14:30:00Z",
        "expires_at": "2026-07-23T14:30:00Z",
        "created_at": "2025-07-23T14:30:00Z"
      },
      "timestamp": "2025-07-23T14:30:00Z"
    }
    ```
  * **失败响应示例** (`409 Conflict` - 用户已有同类有效订阅):
    ```json
    {
      "code": 2005,
      "message": "业务逻辑错误",
      "data": {
        "error": "您已拥有一个正在生效的同类会员"
      },
      "timestamp": "2025-07-23T14:31:00Z"
    }
    ```
  * **实现流程描述**:
    1.  解析 `Access Token` 获取 `user_id`。
    2.  根据 `product_code` 从 `membership_products` 表查询产品信息（价格、时长、`level`等），并检查其 `status` 是否为 `ACTIVE`。若产品不存在或未上架，返回 404 Not Found。
    3.  **检查冲突**: 查询 `user_memberships` 表，检查该用户是否已存在 `product_code` 相同且 `status` 为 `'ACTIVE'` 或 `'PAST_DUE'` 的记录。若是，则返回 409 Conflict（利用数据库的部分唯一索引 `idx_user_memberships_one_active_per_product`）。
    4.  调用支付网关服务，使用 `payment_token` 和查询到的价格完成扣款。若失败，返回 402 Payment Required。
    5.  支付成功后，获取 `transaction_id`，并根据产品时长计算 `start_date` (NOW) 和 `expires_at`。
    6.  在 `user_memberships` 表中创建一条新记录，`status` 为 `'ACTIVE'`，`is_auto_renew` 默认为 `true`。
    7.  提交事务，并返回新创建的订阅详情。

#### 3.4. 用户更新自己的订阅

  * **Endpoint**: `PATCH /api/v1/users/me/memberships/{subscription_uuid}`
  * **功能描述**: 更新用户自己的一条订阅记录，主要用于开关“自动续费”。
  * **认证**: 需要提供有效的 `Access Token`。
  * **请求体** (`application/json`):
    ```json
    {
      "is_auto_renew": false
    }
    ```
  * **成功响应** (`200 OK`):
    ```json
    {
      "code": 200,
      "message": "success",
      "data": {
        "uuid": "d1e2f3a4-e5f6-4a1b-8c3d-e5f6a1b2c3d4",
        "product_code": "VIDEO_YEARLY",
        "status": "ACTIVE",
        "is_auto_renew": false,
        "expires_at": "2026-01-15T10:00:00Z"
      },
      "timestamp": "2025-07-23T15:00:00Z"
    }
    ```
  * **失败响应示例** (`403 Forbidden` - 试图修改不属于自己的订阅):
    ```json
    {
      "code": 3002,
      "message": "权限不足",
      "data": {
        "error": "您无权修改此订阅"
      },
      "timestamp": "2025-07-23T15:01:00Z"
    }
    ```
  * **实现流程描述**:
    1.  解析 `Access Token` 获取 `user_id`。
    2.  根据路径参数 `subscription_uuid` 查询 `user_memberships` 表获取订阅记录。若未找到，返回 404 Not Found。
    3.  **权限校验**: 验证该订阅记录的 `user_id` 是否与当前登录用户匹配。若不匹配，返回 403 Forbidden。
    4.  **业务逻辑检查**: 检查该订阅的 `status` 是否允许被修改（例如，已 `EXPIRED` 的订阅可能不允许再修改续费状态）。
    5.  更新记录的 `is_auto_renew` 字段值。
    6.  提交数据库事务，返回更新后的订阅记录。

    
批次五：后台管理API (Batch 5: Admin APIs)
目标: 生成所有后台管理接口，为运营和客服提供支持。

依赖: 所有基础数据模型已建立。

  * **Endpoint**: `GET /api/v1/admin/users`
  * **功能描述**: (管理员) 分页、排序、筛选获取系统中的所有用户列表。
  * **认证**: 需要 `ADMIN` 或更高权限。
  * **请求参数 (Query)**:
      * `page` (int, 可选, 默认1): 页码。
      * `size` (int, 可选, 默认10): 每页数量。
      * `sort` (string, 可选): 排序字段，如 `created_at:desc`。
      * `username` (string, 可选): 按用户名模糊搜索。
      * `email` (string, 可选): 按邮箱精确搜索。
      * `role` (string, 可选): 按角色筛选 (`REGULAR`, `MODERATOR` 等)。
      * `status` (string, 可选): 按状态筛选 (`NORMAL`, `BANNED` 等)。
  * **成功响应** (`200 OK`):
    ```json
    {
      "code": 200, "message": "success",
      "data": {
        "total": 120, "page": 1, "size": 10,
        "items": [
          {
            "uuid": "a1b2c3d4-e5f6-4a1b-8c3d-e5f6a1b2c3d4",
            "username": "testuser1",
            "nickname": "用户一", 
            "email": "user1@example.com",
            "role": "REGULAR",
            "status": "NORMAL",
            "created_at": "2025-07-20T10:00:00Z"
          }
        ]
      },
      "timestamp": "2025-07-22T21:00:00Z"
    }
    ```
  * **失败响应示例** (`403 Forbidden` - 权限不足):
    ```json
    {
      "code": 3002,
      "message": "权限不足",
      "data": {
        "error": "您没有权限执行此操作"
      },
      "timestamp": "2025-07-23T16:01:00Z"
    }
    ```
  * **实现流程描述**:
    1.  校验操作员的 `ADMIN` 或更高权限。
    2.  构建基础的 `select(users)` 查询。
    3.  根据传入的 Query 参数动态添加 `WHERE` 筛选条件（例如 `ilike` 用于模糊搜索）。
    4.  执行 `count` 查询获取筛选后的总数。
    5.  应用排序和分页（`order_by`, `offset`, `limit`）到查询上。
    6.  执行最终查询获取当页的 `items`。
    7.  构建并返回符合分页规范的成功响应。

    
  * **Endpoint**: `PATCH /api/v1/admin/users/{user_uuid}`
  * **功能描述**: (管理员) 更新指定用户的核心信息，如角色、状态。
  * **认证**: 需要 `ADMIN` 或更高权限。
  * **请求体** (`application/json`):
    ```json
    {
      "role": "MODERATOR",
      "status": "BANNED",
      "nickname": "违规用户-已被处理"
    }
    ```
  * **成功响应** (`200 OK`): (返回更新后的完整用户对象)
    ```json
    {
      "code": 200, "message": "success",
      "data": {
        "uuid": "a1b2c3d4-...", "username": "testuser", "email": "testuser@example.com",
        "nickname": "违规用户-已被处理", "role": "MODERATOR", "status": "BANNED", ...
      },
      "timestamp": "2025-07-23T16:10:00Z"
    }
    ```
  * **失败响应示例** (`404 Not Found` - 用户不存在):
    ```json
    {
      "code": 2004, "message": "资源不存在",
      "data": {
        "resource": "User",
        "id": "{user_uuid}"
      },
      "timestamp": "2025-07-23T16:11:00Z"
    }
    ```
  * **实现流程描述**:
    1.  校验操作员权限。
    2.  根据 `user_uuid` 查询目标用户对象。若未找到，返回 404。
    3.  执行权限检查（例如 `ADMIN` 不能修改 `SUPERADMIN`）。若不通过，返回 403 Forbidden。
    4.  创建一个包含管理员可修改字段的 Pydantic 模型来验证和解析请求体。
    5.  更新用户对象的属性并提交数据库事务。
    6.  返回更新后的完整用户数据。


5.2. 资源: 会员产品管理 (Admin)

  * **Endpoint**: `POST /api/v1/admin/membership-products`
  * **功能描述**: (管理员) 创建一个新的会员产品。
  * **认证**: 需要 `ADMIN` 或更高权限。
  * **请求体** (`application/json`):
    ```json
    {
        "code": "LIVE_SUPER_FAN_MONTHLY",
        "name": "超级粉丝月度包",
        "description": "直播间专属粉丝徽章和彩色弹幕。",
        "price": "29.99",
        "level": 3,
        "duration_unit": "month",
        "duration_value": 1,
        "status": "DRAFT",
        "sort_order": 10
    }
    ```
  * **成功响应** (`200 OK`): (返回新创建的完整产品对象)
    ```json
    {
      "code": 200, "message": "success",
      "data": {
        "code": "LIVE_SUPER_FAN_MONTHLY",
        "name": "超级粉丝月度包",
        "price": "29.99",
        "status": "DRAFT",
        ...
      },
      "timestamp": "2025-07-23T16:20:00Z"
    }
    ```
  * **失败响应示例** (`400 Bad Request` - code已存在):
    ```json
    {
        "code": 4001, "message": "参数校验失败",
        "data": {"field": "code", "error": "产品编码已存在"},
        "timestamp": "2025-07-23T16:21:00Z"
    }
    ```
  * **实现流程描述**:
    1.  校验操作员权限。
    2.  验证请求体数据，特别是 `code` 字段是否已在数据库中存在。
    3.  创建 `membership_products` 的新记录并存入数据库。
    4.  返回新创建的产品对象。


  * **Endpoint**: `GET /api/v1/admin/membership-products`
  * **功能描述**: (管理员) 分页获取所有会员产品，包括`DRAFT`, `INACTIVE`等非上线状态，用于后台管理列表。
  * **认证**: 需要 `ADMIN` 或更高权限。
  * **请求参数 (Query)**:
      * `page` (int, 可选, 默认1): 页码。
      * `size` (int, 可选, 默认10): 每页数量。
      * `sort` (string, 可选): 排序字段，如 `created_at:desc`。
      * `status` (string, 可选): 按产品状态筛选 (`DRAFT`, `ACTIVE` 等)。
  * **成功响应** (`200 OK`):
    ```json
    {
      "code": 200,
      "message": "success",
      "data": {
        "total": 5,
        "page": 1,
        "size": 10,
        "items": [
          {
            "code": "VIDEO_YEARLY",
            "name": "年度影视会员",
            "price": "199.99",
            "level": 1,
            "status": "ACTIVE",
            "created_at": "2025-07-20T10:00:00Z"
          },
          {
            "code": "LIVE_FAN_MONTHLY",
            "name": "粉丝月度包",
            "price": "29.99",
            "level": 3,
            "status": "DRAFT",
            "created_at": "2025-07-21T11:00:00Z"
          }
        ]
      },
      "timestamp": "2025-07-22T21:00:00Z"
    }
    ```
  * **失败响应示例** (`403 Forbidden` - 权限不足):
    ```json
    {
      "code": 3002,
      "message": "权限不足",
      "data": {
        "error": "您没有权限访问此资源"
      },
      "timestamp": "2025-07-23T16:01:00Z"
    }
    ```
  * **实现流程描述**:
    1.  校验操作员的 `ADMIN` 或更高权限。
    2.  构建基础的 `select(membership_products)` 查询。
    3.  根据传入的 `status` 等 Query 参数动态添加 `WHERE` 筛选条件。
    4.  执行 `count` 查询获取筛选后的总数。
    5.  应用排序和分页（`order_by`, `offset`, `limit`）到查询上。
    6.  执行最终查询获取当页的 `items`。
    7.  构建并返回符合分页规范的成功响应。
    



  * **Endpoint**: `GET /api/v1/admin/membership-products/{product_code}`
  * **功能描述**: (管理员) 获取单个会员产品的全部信息，用于编辑页面。
  * **认证**: 需要 `ADMIN` 或更高权限。
  * **请求参数 (Path)**:
      * `product_code` (string, required): 产品的唯一编码。
  * **成功响应** (`200 OK`):
    ```json
    {
      "code": 200,
      "message": "success",
      "data": {
        "code": "VIDEO_YEARLY",
        "name": "年度影视会员",
        "description": "畅享所有视频内容，为期一年。",
        "sort_order": 1,
        "price": "199.99",
        "level": 1,
        "duration_unit": "year",
        "duration_value": 1,
        "status": "ACTIVE",
        "payment_gateway_price_id": "price_1Lq3gR...",
        "created_at": "2025-07-20T10:00:00Z",
        "updated_at": "2025-07-21T14:00:00Z"
      },
      "timestamp": "2025-07-23T18:00:00Z"
    }
    ```
  * **失败响应示例** (`404 Not Found` - 产品不存在):
    ```json
    {
      "code": 2004,
      "message": "资源不存在",
      "data": {
        "resource": "MembershipProduct",
        "id": "INVALID_CODE"
      },
      "timestamp": "2025-07-23T18:01:00Z"
    }
    ```
  * **实现流程描述**:
    1.  校验操作员权限。
    2.  根据路径参数 `product_code` 查询 `membership_products` 表。
    3.  若查询结果为空，返回 404 Not Found。
    4.  如果找到，序列化完整的产品对象并返回。




  * **Endpoint**: `PATCH /api/v1/admin/membership-products/{product_code}`
  * **功能描述**: (管理员) 更新一个已存在的会员产品，常用于修改价格、描述或上下架（修改`status`）。
  * **认证**: 需要 `ADMIN` 或更高权限。
  * **请求体** (`application/json`): (所有字段均为可选)
    ```json
    {
      "price": "25.99",
      "status": "ACTIVE",
      "description": "限时优惠活动！"
    }
    ```
  * **成功响应** (`200 OK`): (返回更新后的完整产品对象)
    ```json
    {
      "code": 200,
      "message": "success",
      "data": {
        "code": "LIVE_FAN_MONTHLY",
        "name": "粉丝月度包",
        "price": "25.99",
        "status": "ACTIVE",
        "description": "限时优惠活动！",
        ...
      },
      "timestamp": "2025-07-23T18:30:00Z"
    }
    ```
  * **失败响应示例** (`404 Not Found` - 产品不存在): (参考 4.2.2)
  * **实现流程描述**:
    1.  校验操作员权限。
    2.  根据 `product_code` 查询目标产品对象。若未找到，返回 404。
    3.  创建一个包含所有可修改字段的 Pydantic 模型来验证和解析请求体。
    4.  遍历请求体中的字段，更新产品对象的相应属性。
    5.  提交数据库事务。
    6.  返回更新后的完整产品数据。




  * **Endpoint**: `DELETE /api/v1/admin/membership-products/{product_code}`
  * **功能描述**: (管理员) 删除一个会员产品。**注意：只有在没有任何用户订阅记录引用的情况下才能成功。**
  * **认证**: 需要 `ADMIN` 或更高权限。
  * **请求参数 (Path)**:
      * `product_code` (string, required): 待删除产品的唯一编码。
  * **成功响应** (`200 OK`):
    ```json
    {
      "code": 200,
      "message": "success",
      "data": null,
      "timestamp": "2025-07-23T18:45:00Z"
    }
    ```
  * **失败响应示例** (`400 Bad Request` - 产品仍被引用):
    ```json
    {
      "code": 2006,
      "message": "业务逻辑错误",
      "data": {
        "error": "无法删除仍被用户订阅引用的产品，请先将其归档(ARCHIVED)"
      },
      "timestamp": "2025-07-22T22:40:00Z"
    }
    ```
  * **实现流程描述**:
    1.  校验操作员权限。
    2.  根据 `product_code` 查询目标产品对象。若未找到，返回 404。
    3.  尝试从数据库中删除该记录。
    4.  由于 `user_memberships` 表的外键设置了 `ON DELETE RESTRICT`，如果该产品已被任何用户订阅，数据库将直接抛出引用完整性错误。
    5.  捕获该数据库错误，并将其转换为业务错误码 `2006` 返回给客户端。
    6.  若删除成功（即无任何引用），返回成功的响应。
    7.  **最佳实践**: 业务上应引导管理员先将产品 `status` 置为 `ARCHIVED`，而非直接物理删除。




  * **Endpoint**: `GET /api/v1/admin/users/{user_uuid}/memberships`
  * **功能描述**: (管理员/客服) 获取指定用户的所有订阅历史记录，用于后台查询和展示。
  * **认证**: 需要 `ADMIN` 或更高权限。
  * **请求参数 (Path)**:
      * `user_uuid` (UUID, required): 目标用户的公开ID。
  * **请求参数 (Query)**:
      * `page` (int, 可选, 默认1): 页码。
      * `size` (int, 可选, 默认10): 每页数量。
      * `sort` (string, 可选): 排序字段，如 `created_at:desc`。
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
            "uuid": "d1e2f3a4-e5f6-4a1b-8c3d-e5f6a1b2c3d4",
            "product_code": "VIDEO_YEARLY",
            "level": 1,
            "status": "ACTIVE",
            "is_auto_renew": true,
            "start_date": "2025-01-15T10:00:00Z",
            "expires_at": "2026-01-15T10:00:00Z",
            "created_at": "2025-01-15T09:59:00Z"
          },
          {
            "uuid": "c1b2d3a4-e5f6-4a1b-8c3d-e5f6a1b2c3d4",
            "product_code": "LIVE_FAN_MONTHLY",
            "level": 3,
            "status": "EXPIRED",
            "is_auto_renew": false,
            "start_date": "2024-12-10T14:00:00Z",
            "expires_at": "2025-01-10T14:00:00Z",
            "created_at": "2024-12-10T13:59:00Z"
          }
        ]
      },
      "timestamp": "2025-07-23T19:00:00Z"
    }
    ```
  * **失败响应示例** (`404 Not Found` - 用户不存在):
    ```json
    {
      "code": 2004,
      "message": "资源不存在",
      "data": {
        "resource": "User",
        "id": "{user_uuid}"
      },
      "timestamp": "2025-07-23T19:01:00Z"
    }
    ```
  * **实现流程描述**:
    1.  校验操作员的 `ADMIN` 或更高权限。
    2.  根据路径参数 `user_uuid` 查询 `users` 表获取用户的内部 `id`。若用户不存在，返回 404 Not Found。
    3.  使用获取到的 `user_id`，查询 `user_memberships` 表获取该用户的所有记录。
    4.  应用分页和排序逻辑。
    5.  构建并返回符合分页规范的成功响应。



  * **Endpoint**: `POST /api/v1/admin/users/{user_uuid}/memberships`
  * **功能描述**: (管理员/客服) 手动为用户赠送或补偿一个会员订阅，例如作为活动奖励或客服解决方案。
  * **认证**: 需要 `ADMIN` 或更高权限。
  * **请求体** (`application/json`):
    ```json
    {
        "product_code": "VIDEO_YEARLY",
        "transaction_id": "manual_gift_by_admin_xyz_001",
        "start_date": "2025-07-23T00:00:00Z",
        "expires_at": "2026-07-23T00:00:00Z",
        "notes": "用户参与“夏日活动”奖励"
    }
    ```
      * `notes` (string, 可选): 操作备注，建议存入数据库（需新增 `admin_notes` 字段）用于审计。
  * **成功响应** (`200 OK`): (返回新创建的 `user_memberships` 对象)
    ```json
    {
      "code": 200,
      "message": "success",
      "data": {
        "uuid": "f1g2h3i4-j5k6-7l8m-9n0o-p1q2r3s4t5u6",
        "user_id": 123,
        "product_code": "VIDEO_YEARLY",
        "level": 1,
        "status": "ACTIVE",
        "is_auto_renew": false, -- 手动创建的订阅默认不自动续费
        "start_date": "2025-07-23T00:00:00Z",
        "expires_at": "2026-07-23T00:00:00Z"
      },
      "timestamp": "2025-07-23T19:10:00Z"
    }
    ```
  * **失败响应示例** (`400 Bad Request` - 产品不存在):
    ```json
    {
        "code": 4001,
        "message": "参数校验失败",
        "data": {
            "field": "product_code",
            "error": "指定的产品编码不存在"
        },
        "timestamp": "2025-07-23T19:11:00Z"
    }
    ```
  * **实现流程描述**:
    1.  校验操作员权限。
    2.  根据 `user_uuid` 找到 `user_id`。若用户不存在，返回 404。
    3.  根据请求体中的 `product_code` 查询 `membership_products` 表，获取 `level` 等信息。若产品不存在，返回 400 Bad Request。
    4.  检查该用户是否已存在与 `product_code` 相同且状态为 `ACTIVE` 或 `PAST_DUE` 的订阅。若存在，返回 409 Conflict。
    5.  在 `user_memberships` 表中插入一条新记录，`status` 设为 `ACTIVE`，`is_auto_renew` 设为 `false`。
    6.  提交事务，并返回新创建的订阅记录。


  * **Endpoint**: `PATCH /api/v1/admin/subscriptions/{subscription_uuid}`
  * **功能描述**: (管理员/客服) 手动更新一个订阅的状态或有效期，例如执行退款、延长会员时间等。
  * **认证**: 需要 `ADMIN` 或更高权限。
  * **请求体** (`application/json`): (所有字段均为可选)
    ```json
    {
      "status": "REFUNDED",
      "expires_at": "2025-08-01T00:00:00Z",
      "is_auto_renew": false,
      "notes": "用户申请退款，客服 Alice 手动处理"
    }
    ```
  * **成功响应** (`200 OK`): (返回更新后的 `user_memberships` 对象)
    ```json
    {
      "code": 200,
      "message": "success",
      "data": {
        "uuid": "{subscription_uuid}",
        "status": "REFUNDED",
        "is_auto_renew": false,
        "expires_at": "2025-08-01T00:00:00Z",
        ...
      },
      "timestamp": "2025-07-23T19:20:00Z"
    }
    ```
  * **失败响应示例** (`404 Not Found` - 订阅不存在):
    ```json
    {
      "code": 2004,
      "message": "资源不存在",
      "data": {
        "resource": "Subscription",
        "id": "{subscription_uuid}"
      },
      "timestamp": "2025-07-23T19:21:00Z"
    }
    ```
  * **实现流程描述**:
    1.  校验操作员权限。
    2.  根据路径参数 `subscription_uuid` 查询 `user_memberships` 表获取订阅记录。若未找到，返回 404 Not Found。
    3.  创建一个包含所有管理员可修改字段的 Pydantic 模型，验证并解析请求体。
    4.  遍历请求体中的字段，更新订阅记录对象的相应属性。
    5.  提交数据库事务。
    6.  返回更新后的订阅记录对象。