
-----

### **最终增强版：为 Authing 集成和新用户 API 进行增量测试代码生成的提示词 (已修正)**

#### **1. 角色定义 (Role Definition)**

你是一名资深的 Python 测试工程师（SDET），精通 `pytest`、`pytest-asyncio`、`httpx` 和 `faker`。你擅长为采用分层架构的 FastAPI 应用编写清晰、健壮的单元测试和集成测试。你的核心任务是在现有测试套件上进行**增量式测试开发**，为新功能添加全新的、遵循最高质量标准的测试用例，同时**绝不修改**任何已有的测试代码或配置。

#### **2. 任务目标 (Task Objective)**

你的任务是为最近集成的 **Authing SSO**、**手机号绑定API** 以及相关的用户服务逻辑编写一套完整的、增量式的单元测试和集成测试。测试范围必须覆盖 `crud`, `services`, 和 `api` 层的全部新增及修改的功能点。

**核心约束:** 所有新编写的测试代码必须严格遵循下方定义的**核心测试规范**，特别是数据隔离、测试函数结构和深度测试要求。

#### **3. 核心上下文与依赖**

**3.1. 测试环境假设**
* **测试框架**: `pytest` 和 `pytest-asyncio`。
* **HTTP 客户端**: 使用 `httpx.AsyncClient`，通过 `async_client` 夹具（fixture）获得实例。
* **数据库**: 通过 `db_session` 夹具获得一个事务回滚的 `AsyncSession` 实例。
* **测试数据**: **必须**使用 `faker` 库生成所有唯一的测试数据。
* **模拟 (Mocking)**: 使用 `pytest-mock` 提供的 `mocker` 夹具来模拟所有外部依赖。
* **异步模拟**: 对于异步方法（如Redis客户端、外部API调用），**必须**使用 `mocker.AsyncMock()` 或配置 `mocker.Mock()` 的异步方法。**严禁**使用普通 `Mock` 对象模拟异步方法的返回值。

**3.2. 依赖的上下文模块**
*在编写测试时，你需要依赖以下模块*
* **被测试模块**:
    * `@app/crud/crud_user.py`
    * `@app/services/auth_service.py`
    * `@app/services/user_service.py`
    * `@app/api/v1/endpoints/auth.py`
    * `@app/api/v1/endpoints/users.py`
* **核心依赖**:
    * `@app/models/users.py`
    * `@app/schemas/users.py`, `@app/schemas/auth.py`
    * `@app/core/redis_client.py`
    * `@app/exceptions.py`
* **外部库依赖**:
    * `authing.v3.authentication.AuthenticationClient`


**3.3. 项目结构**

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
|    ├── __init__.py (70B)
|   └── create_tables.py (4.2KB)
├── exception.py
```

#### **3.4. 源代码一致性要求 (Source Code Consistency Requirements)**

**【关键指导原则】** 
  - 测试代码必须严格按照实际的业务实现代码进行编写，确保异常消息、返回值类型、业务逻辑完全一致。 
  - **3.2 依赖的上下文模块** 该小节给出了依赖实际的业务实现代码
**具体要求：**

1. **异常消息严格匹配**：
   - 测试中的异常消息断言必须与源代码中实际抛出的异常消息**完全一致**
   - 禁止使用推测性的异常消息，必须查看源代码确认实际的异常文本

2. **数据类型精确匹配**：
   - 如果源代码返回 `IPv4Address` 对象，测试断言时需要使用 `str()` 转换或直接比较对象
   - 如果源代码返回特定的枚举类型，测试需要使用相同的类型进行比较

3. **异常类型准确判断**：
   - 必须根据源代码的实际异常处理逻辑来确定期望的异常类型
   - 不要假设某个错误"应该"抛出特定异常，而要查看源代码确认实际行为

**源代码关键信息提取（基于实际代码分析）：**

- **AuthService.sso_login 方法**：
  - 被封禁用户抛出：`InvalidCredentialsException("账户已被封禁")`
  - Token验证失败抛出：`InvalidTokenException("身份验证失败")`
  - auth_client为None时抛出：`AttributeError`（系统级错误）
  - 用户登录后 `last_login_ip` 字段类型：`IPv4Address` 对象

- **测试断言修正指南**：
  ```python
  # 正确的异常消息断言
  assert "账户已被封禁" in str(exc_info.value)  # 不是"账户状态异常"
  assert "身份验证失败" in str(exc_info.value)  # 不是"ID Token验证失败"
  
  # 正确的IP地址断言
  assert str(updated_user.last_login_ip) == "192.168.1.3"  # 需要转换为字符串
  
  # 正确的异常类型
  with pytest.raises(AttributeError):  # 不是 InvalidTokenException
      # auth_client为None的情况
  ```
-----

### **4. 核心测试规范 (必须包含在提示词中)**

#### **4.1. 测试数据隔离 (Test Data Isolation)**

  * **指令**: 为了防止测试之间因违反数据库 `UNIQUE` 约束而产生冲突，所有唯一性字段（如 `username`, `email`, `phone_number`）**必须**是随机生成的，以确保每次测试运行时的数据都是独一无二的。
  * **新增要求**: 对于需要认证用户的测试，必须使用 `authenticated_user` fixture，该 fixture 会自动创建唯一的测试用户数据。
  
  * **实现**: 使用 `faker` 库生成符合 Pydantic 模型验证规则的数据。
  * **具体要求**:
      * **`username`**: 必须符合 `min_length=1` 和 `max_length=50`。范例: `f"{fake.user_name()}_{uuid.uuid4().hex[:6]}"`。
      * **`email`**: 必须是一个有效的邮箱格式。范例: `fake.email()`。
      * **`phone_number`**: 长度不能超过20个字符。
      * **禁止硬编码**: 在测试的“准备 (Arrange)”阶段，**严禁**使用硬编码的字符串（如 `'usera'`) 作为唯一性字段的值。

#### **4.2. 测试函数生成规范**

**必须严格遵循以下模板生成所有测试函数：**

```python
# API+数据库测试模板（多fixture）
@pytest.mark.asyncio
async def test_api_with_db(self, async_client, db_session, <any_other_fixtures>):
    """API和数据库组合测试"""
    async for client in async_client:
        async for db in db_session:
            # 如果使用 authenticated_user fixture，需要额外的 async for
            if 'authenticated_user' in self._get_test_parameters():
                async for user, token in authenticated_user:
                    # 组合测试逻辑全部在此嵌套 async for 块内
                    pass
            else:
                # 组合测试逻辑全部在此嵌套 async for 块内
                pass
            # 组合测试逻辑全部在此嵌套 async for 块内
            pass
```
**重要说明：**
- 当测试函数使用 `authenticated_user` fixture 时，必须添加第三层 `async for user, token in authenticated_user:`
- 这是为了正确处理异步生成器 fixture 的迭代

#### **4.3. 深度测试要求**

所有测试用例必须采用**准备 (Arrange)**、**执行 (Act)** , **断言 (Assert)** 模式，和 **清理 (Cleanup)**, 并包含**状态验证 (State Verification)** 的深度测试。

  * **深度测试流程**:
    1.  **准备 (Arrange)**: 使用 `faker` 和 `db_session` 创建所有必要的先决条件数据。对于API测试，还需要准备认证头和模拟外部服务。
    2.  **执行 (Act)**: 调用 Service 方法或 API 端点。
    3.  **断言 (Assert)**: 验证函数返回值或 API 响应（HTTP状态码、业务`code`、`data`结构和内容）。
    4.  **状态验证 (State Verification)**: 通过 `db_session` 重新查询数据库，断言数据的状态（增、删、改）是否符合预期。例如，验证 `last_login_at` 字段是否已更新。
    5. **清理 (Cleanup)**: **【新增要求】** 确保测试数据的自动清理

**测试数据隔离和清理策略：**
- **推荐方式**：使用 `db_session` fixture的事务回滚机制（已配置）
- **数据库fixture原理**：每个测试在独立事务中运行，测试结束后自动回滚
- **无需手动清理**：由于使用事务回滚，测试创建的数据会自动清理
- **唯一性冲突预防**：仍需使用 `faker` 生成唯一数据，防止同一测试运行中的冲突
- 
#### **4.4. 异步模拟规范 (Async Mocking Standards)**

**必须严格遵循以下异步模拟规则：**

* **异步方法模拟**: 对于所有异步方法（返回协程的方法），必须使用以下方式之一进行模拟：
  
  **方式一 - 使用 AsyncMock**:
  ```python
  # 正确：对于异步客户端
  mock_redis_client = mocker.AsyncMock()
  mock_redis_client.get.return_value = "expected_value"
  mock_redis_client.delete.return_value = True
  ```
  
* **错误示例 - 禁止使用**:
  ```python
  # 错误：普通Mock无法模拟异步方法
  mock_redis_client = mocker.Mock()
  mock_redis_client.get.return_value = "value"  # 这会导致 TypeError
  ```

* **常见异步依赖**:
  - **Redis客户端**: `redis_client.get()`, `redis_client.set()`, `redis_client.delete()`
  - **数据库会话**: 已通过fixture提供，无需额外模拟
  - **HTTP客户端**: `httpx.AsyncClient` 的所有方法
  - **外部API**: 如 `AuthenticationClient.oidc.verify_id_token()`
-----

### **5. 具体代码生成指令 (Specific Code Generation Instructions)**

#### **5.1. 【新增文件】 `tests/crud/test_crud_user_new.py`**

  * **任务**: 测试新增的 `CRUDUser` 方法。
  * **测试用例**:
    1.  `test_get_by_social_id`:
          * **准备**: 使用 `faker` 创建一个包含 `social_provider` 和 `social_id` 的用户并存入数据库。
          * **执行**: 调用 `crud_user.get_by_social_id()`。
          * **断言**: 成功找到该用户，且返回对象的 `social_id` 匹配。同时测试未找到时返回 `None`。
    2.  `test_get_by_login_identifier`:
          * **准备**: 创建一个用户，其 `phone_number` 已验证 (`is_phone_verified = True`)。创建另一个用户，其手机号未验证。
          * **执行**: 分别使用 `username`, `email`, 和**已验证的手机号**调用 `crud_user.get_by_login_identifier()`。
          * **断言**: 三种方式都能成功找到用户。再使用**未验证的手机号**调用，断言返回 `None`。

#### **5.2. 【新增文件】 `tests/services/test_auth_service_sso.py`**

  * **任务**: 详细测试 `AuthService` 中新增的 `sso_login` 逻辑。
  * **测试用例**:
    1.  `test_sso_login_with_existing_social_user`:
          * **准备**: 模拟 `authing_client.oidc.verify_id_token` 返回成功 payload。在数据库中创建一个 `social_id` 与 payload `sub` 匹配的用户。
          * **执行**: 调用 `auth_service.sso_login()`。
          * **断言**: 返回了包含 `access_token` 的字典。
          * **状态验证**: 重新查询该用户，断言其 `last_login_at` 和 `last_login_ip` 已被更新。
    2.  `test_sso_login_linking_existing_email_user`:
          * **准备**: 模拟 `verify_id_token` 返回成功 payload。在数据库中创建一个 `email` 匹配但 `social_id` 为空的账户。
          * **执行**: 调用 `sso_login()`。
          * **断言**: 返回 `access_token`。
          * **状态验证**: 重新查询该用户，断言其 `social_provider` 和 `social_id` 已被成功填充。
    3.  `test_sso_login_creating_new_user`:
          * **准备**: 模拟 `verify_id_token`。确保数据库中无匹配用户。
          * **执行**: 调用 `sso_login()`。
          * **断言**: 返回 `access_token`。
          * **状态验证**: 查询数据库，断言一个新用户已被创建，其 `email`, `nickname`, `social_id` 均与 payload 匹配。
    4.  `test_sso_login_fails_for_banned_user`:
          * **准备**: 类似 `test_sso_login_with_existing_social_user`，但将用户的 `status` 设为 `BANNED`。
          * **执行/断言**: 使用 `pytest.raises` 断言 `InvalidCredentialsException` 被抛出。
    5.  `test_sso_login_fails_with_invalid_authing_token`:
          * **准备**: 模拟 `verify_id_token` 抛出 `InvalidTokenError` 异常。
          * **执行/断言**: 断言 `InvalidTokenException` 被抛出。


**关键测试用例的正确实现示例：**

```python
# 示例1：正确的IP地址断言
@pytest.mark.asyncio
async def test_sso_login_creating_new_user(self, db_session, mocker):
    async for db in db_session:
        # ... 准备和执行代码 ...
        
        # 状态验证：正确的IP地址断言
        new_user = await crud_user.get_by_email(db, email)
        assert str(new_user.last_login_ip) == "192.168.1.3"  # 转换为字符串

# 示例2：正确的异常消息断言
@pytest.mark.asyncio  
async def test_sso_login_fails_for_banned_user(self, db_session, mocker):
    async for db in db_session:
        # ... 准备代码 ...
        
        with pytest.raises(InvalidCredentialsException) as exc_info:
            await auth_service.sso_login(db, id_token="dummy_token", client_ip="192.168.1.4")
        
        assert "账户已被封禁" in str(exc_info.value)  # 实际的异常消息

# 示例3：正确的系统级异常处理
@pytest.mark.asyncio
async def test_sso_login_fails_when_authing_client_unavailable(self, db_session):
    async for db in db_session:
        auth_service = AuthService(db)
        auth_service.auth_client = None
        
        with pytest.raises(AttributeError) as exc_info:  # 系统级异常
            await auth_service.sso_login(db, id_token="dummy_token", client_ip="192.168.1.6")
        
        assert "'NoneType' object has no attribute 'oidc'" in str(exc_info.value)
```


#### **5.3. 【新增文件】 `tests/services/test_user_service_new.py`**


  * **任务**: 测试 `UserService` 的手机号绑定逻辑和增强的密码验证。
    * **测试用例**:
      1.  `test_bind_phone_number_success`:
            * **准备**: * **准备**: 创建一个用户。使用 `mocker.AsyncMock()` 方法模拟 `redis_client.get` 返回正确的验证码，模拟 `redis_client.delete` 返回 `True`。
            * **执行**: 调用 `user_service.bind_phone_number()`。
            * **断言**: `redis_client.delete` 被调用一次，确保验证码被销毁。
            * **状态验证**: 重新查询用户，断言其 `phone_number` 被更新且 `is_phone_verified` 为 `True`。
            * * **模拟示例**:
            ```python
            # 方式一：AsyncMock
            mock_redis_client = mocker.AsyncMock()
            mock_redis_client.get.return_value = verification_code
            mock_redis_client.delete.return_value = True
          ```
          
      2.  `test_bind_phone_number_fails_with_wrong_code`:
            * **准备**: 创建用户。模拟 `redis_client.get` 返回 `None` 或错误的验证码。
            * **执行/断言**: 断言调用 `bind_phone_number` 时抛出 `ValidationError`，且错误信息为“手机验证码错误或已过期”。
      3.  `test_bind_phone_number_fails_when_phone_is_taken`:
            * **准备**: 创建两个用户。将目标手机号绑定到第一个用户。
            * **执行/断言**: 当第二个用户尝试绑定同一个手机号时，断言 `ValidationError` 被抛出，错误信息为“该手机号已被其他账号绑定”。
      4.  `test_password_strength_validation`:
            * **准备**: 使用 `@pytest.mark.parametrize` 提供多种密码组合。
            * **执行**: 调用 `_validate_password_strength`。
            * **断言**: 强密码（包含大小写、数字、特殊字符且长度足够）通过验证，而任何缺少其中一项的弱密码都会导致 `ValidationError`。

#### **5.4. `新增文件】 `tests/api/v1/endpoints/test_auth_sso.py`**

  * **任务**: * **【新增内容】** 添加针对`POST /api/v1/auth/sso-login`端点的集成测试。**必须**模拟`AuthService`层。需要验证：
  * **测试用例**:
    1.  `test_sso_login_api_success` (`test_auth.py`):
          * **准备**: 模拟 `AuthService.sso_login` 方法成功返回 token 字典。
          * **执行**: 向 `POST /api/v1/auth/sso-login` 发送请求。
          * **断言**: 状态码 `200`，业务 `code` `200`，且响应 `data` 与模拟的返回值一致。
    2.  `test_sso_login_api_authing_failure` (`test_auth.py`):
          * **准备**: 模拟 `AuthService.sso_login` 抛出 `InvalidTokenException`。
          * **执行**: 发送 `POST` 请求。
          * **断言**: 状态码 `401`，业务 `code` `3005`，`message` 为“认证凭证无效”。

**5.5. 【新增文件】 `tests/api/v1/endpoints/test_users_phone.py`**
    1.  `test_bind_phone_api_success` (`test_users.py`):
          * **准备**: 获取一个已认证用户的 `token`。模拟 `UserService.bind_phone_number` 成功执行（返回 `None`）。
          * **执行**: 携带认证头向 `POST /api/v1/users/me/phone` 发送请求。
          * **断言**: 状态码 `200`，业务 `code` `200`，`message` 为“手机号绑定成功”。
    2.  `test_bind_phone_api_invalid_request_data`:
          * **准备**: 使用 `authenticated_user` fixture 获取认证用户和token。
          * **执行**: 分别测试缺少 `phone_number`、缺少 `verification_code`、空请求体的情况。
          * **断言**: 所有情况都返回状态码 `422`（FastAPI validation error）。
    3.  `test_bind_phone_api_validation_error` (`test_users.py`):
          * **准备**: 获取认证 `token`。模拟 `UserService.bind_phone_number` 抛出 `ValidationError`。
          * **执行**: 发送 `POST` 请求。
          * **断言**: 状态码 `400`，业务 `code` `4006`。

-----

#### **6. Fixture 使用规范**

**6.1. authenticated_user fixture**
- **用途**: 为需要认证的API测试提供用户和token
- **结构**: 返回 `(user, token)` 元组
- **使用方式**: 必须使用 `async for user, token in authenticated_user:` 进行迭代
- **示例**:
```python
async for user, token in authenticated_user:
    headers = {"Authorization": f"Bearer {token}"}
    # 使用 user 和 headers 进行测试
```

**6.2. 嵌套 async for 结构**
- **第一层**: `async for client in async_client:`
- **第二层**: `async for db in db_session:`
- **第三层** (可选): `async for user, token in authenticated_user:`
- 
#### **7. 最终交付 (Final Deliverable)**

请根据以上所有要求和规范，为我生成以下**五个全新的测试文件**的完整、可直接使用的 Python 代码：
1.  `tests/test_crud_user_new.py`
2.  `tests/test_auth_service_sso.py`
3.  `tests/test_user_service_new.py`
4.  `tests/test_auth_sso.py`
5.  `tests/test_users_phone.py` 