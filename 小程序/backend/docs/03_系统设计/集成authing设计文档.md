好的，遵照您的要求，我已经为您修改了这份设计文档。

修改的核心思想是：**移除与您现有用户系统重叠的功能（如密码登录、用户注册管理），并强化其作为“身份认证和绑定”中间件的角色。**

改动点主要包括：

1.  **精简 SDK 能力速查表**：删除了前端密码登录和后端用户创建、更新、删除等您不需要的 API。
2.  **移除 Webhook 部分**：由于您不在 Authing 创建用户，Webhook 的用户事件同步不再必要。
3.  **更新代码示例**：删除了前端的 `emailLogin` 示例，并调整了后端的注释，使其更贴合“验证与绑定”的场景。
4.  **调整配置流程**：简化了用户池的配置说明，聚焦于社会化登录。

以下是修改后的文档全文：

-----

````markdown
# Authing 统一身份认证集成手册（精简版）
> **版本**：v1.4  
> **更新日期**：2025-08-15  
> **适用架构**：前端 uni-app + Vue3（H5/小程序/App），后端 FastAPI + Python  
> **目标**：为现有用户系统集成 SSO 单点登录与第三方身份源，实现安全的用户绑定。
> **协议体系**：基于 **OpenID Connect 1.0**（OIDC），兼容 OAuth2 授权流程，支持 SSO 与微信、Apple 等第三方身份登录。
---

## 🎯 核心原则

| 角色 | 职责 |
|------|------|
| **前端** | 调用第三方登录（如微信、Apple），获取身份令牌（`id_token`）<br>不处理业务逻辑，不存储敏感信息 |
| **后端** | 验证令牌合法性（`verify_id_token`）<br>完成与**本地用户**的绑定或创建<br>颁发自身业务 token（如 JWT）<br>**绝不信任前端传来的用户身份** |
| **协议标准** | 统一采用 **OIDC 1.0** 协议，所有身份令牌为 JWT 格式 |

> 🔐 **安全铁律**：所有身份验证必须在后端完成，前端只做“通行证”传递。

---

## 2\. 技术栈

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

| 分类 | 技术选型 | 用途说明 |
| :--- | :--- | :--- |
| **核心框架** | `uni-app` | 使用Vue语法，一套代码编译到多端平台，实现跨端开发。 |
| **页面语法** | `Vue3` | **推荐使用Vue3 Composition API（`<script setup>`）**。 |
| **状态管理** | Pinia | 推荐Pinia（Vue3官方推荐状态管理），全局store统一管理用户、认证等状态。 |
| **UI组件** | uni-ui/uni-app官方组件/原生HTML | 推荐优先使用`uni-ui`和`uni-app`官方组件，补充原生HTML元素。 |
| **HTTP请求** | `uni.request` | 框架内置请求库，直接使用，并封装拦截器逻辑。 |
| **样式处理** | 内联/全局 SCSS/CSS | 支持全局和内联，推荐`<style lang="scss" scoped">`。 |
| **开发工具** | `HBuilderX` | DCloud官方IDE，是`uni-app`项目的最佳开发环境。 |
| **类型支持** | TypeScript | 推荐 `<script setup lang="ts">`，提升类型安全。 |

## 📚 一、Authing SDK 能力速查表

### 1. AuthenticationClient（前端专用）
用于用户登录、登出、获取令牌。

| 方法 | 说明 | 调用方 | 是否必须 |
|------|------|--------|----------|
| `new AuthenticationClient(...)` | 初始化 SDK | 前端 | ✅ |
| `start()` | 检查 SSO 登录态（自动跳转） | 前端 | ✅（SSO 必需） |
| `logout()` | 退出并清除 SSO Cookie | 前端 | ✅ |
| `social.authorize(provider, opts)` | 第三方登录（微信、Apple 等） | 前端 | ✅ |
| `getCurrentUser()` | 获取当前用户信息（需 access_token） | 前端 | ⚠️ 可选 |

> ⚠️ 注意：`getCurrentUser()` 返回的是 Authing 用户信息，**不能替代后端验证**。

### 2. ManagementClient（后端专用）
用于在绑定用户前进行辅助查询。

| 方法 | 说明 | 调用方 | 是否必须 |
|------|------|--------|----------|
| `users.list()` | 按条件查询用户（如邮箱），辅助判断用户是否已在 Authing 存在 | 后端 | ✅（绑定判断） |

### 3. OIDC 关键方法（后端）
| 方法 | 说明 | 调用方 | 是否必须 |
|------|------|--------|----------|
| `verify_id_token_pyjwt(token, issuer, audience)` | 自定义实现：使用 PyJWT 验证 `id_token` 签名、过期、audience、issuer | 后端 | ✅ |
| `oidc.refresh_token(refresh_token)` | 刷新 `access_token`（如需调用 Authing API） | 后端 | ⚠️ 可选 |

---

## 🔐 二、安全清单（必须遵守）

| 事项 | 要求 |
|------|------|
| **Client Secret** | 仅后端使用，严禁出现在前端代码、Git 提交、日志、浏览器控制台 |
| **回调地址** | 必须精确匹配（协议、域名、端口、大小写）<br>H5、小程序、App 需配置不同回调地址 |
| **环境隔离** | 开发、测试、生产环境使用**独立用户池或独立应用**，避免数据污染 |
| **Token 验证** | 前端传来的 `id_token` 必须在后端通过自定义的 `verify_id_token_pyjwt` 方法验证<br>校验：签名、过期时间、`audience`（Client ID）、`issuer` |
| **依赖更新** | 定期升级 `@authing/web`、`authing-sdk` 等包，关注安全公告 |
| **审计监控** | 记录登录/登出/失败事件，设置异常登录告警（如 5 分钟内失败 5 次） |

---

## 🛠️ 三、实现流程（四步走）

### Step 1：创建用户池
1. 登录 [Authing 控制台](https://console.authing.cn)
2. 创建用户池 → 记录 `User Pool ID`
3. 配置：
   - **登录方式**（重点配置**社会化登录**，如微信小程序、Apple ID 等）
   - 短信/邮箱模板（用于验证码等场景）

### Step 2：为每个应用创建独立“应用”
路径：用户池 → 应用 → 创建应用

| 业务系统 | 类型 | 回调地址示例 |
|--------|------|--------------|
| 管理后台 | 单页应用（SPA） | `https://admin.yourdomain.com/callback` |
| 直播前台 | 单页应用（SPA） | `https://live.yourdomain.com/callback` |
| H5 页面 | 单页应用（SPA） | `https://h5.yourdomain.com/callback` |
| iOS App | 原生应用（Native） | `yourapp://authing/callback` |
| Android App | 原生应用（Native） | `yourapp://authing/callback` |

> ✅ 每个应用生成独立的 `Client ID` 和 `Client Secret`  
> ✅ **注意**：原生 App 使用 `Custom Scheme` 回调，需在 Authing 配置

---

## 🧩 四、代码示例

### 前端（uni-app + Vue3）—— 多端适配

```ts
// utils/authing.ts
import { AuthenticationClient } from '@authing/web'

// 根据环境动态配置
const config = {
  userPoolId: import.meta.env.VITE_USER_POOL_ID,
  appId: import.meta.env.VITE_CLIENT_ID,
  host: import.meta.env.VITE_AUTHING_HOST
}

export const authClient = new AuthenticationClient(config)

// 检查 SSO 登录态
export const checkSSO = async () => {
  try {
    return await authClient.start()
  } catch (error) {
    console.error('SSO 检查失败:', error)
    return null
  }
}

// 微信小程序登录
export const wxMiniLogin = async () => {
  try {
    const { code } = await uni.login()
    const user = await authClient.social.authorize('wechatmini', { code })
    return user.id_token // 仅返回 id_token 给后端
  } catch (error) {
    throw new Error(`微信登录失败: ${error.message}`)
  }
}

// Apple 登录（H5）
export const appleLogin = async () => {
  try {
    const user = await authClient.social.authorize('apple', { scope: 'email name' })
    return user.id_token // 仅返回 id_token 给后端
  } catch (error) {
    throw new Error(`Apple 登录失败: ${error.message}`)
  }
}
````

### 后端（FastAPI + Python）—— 安全验证与绑定

```python
# services/authing_service.py
from authing.v3.management import ManagementClient
from fastapi import HTTPException
from jwt import PyJWKClient
import jwt
import os

class AuthingService:
    def __init__(self):
        # 注意：不再使用 AuthenticationClient，因为其 oidc.verify_id_token 方法在 Python SDK 中不可用
        # ManagementClient 主要用于在绑定前，通过 email 等信息反查用户，辅助决策
        self.mgmt_client = ManagementClient(
            user_pool_id=os.getenv("USER_POOL_ID"),
            secret=os.getenv("USER_POOL_SECRET")
        )

    def verify_id_token_pyjwt(self, id_token: str, issuer: str, audience: str, timeout: int = 5) -> dict:
        """
        使用 PyJWT 的 PyJWKClient 校验 RS256 OIDC id_token
        :param id_token: 前端传来的 JWT 格式的 ID Token
        :param issuer: OIDC 发行者地址，格式为 https://<domain>.authing.cn/oidc
        :param audience: 当前应用的 Client ID
        :param timeout: JWKS 请求超时时间，默认 5 秒
        :return: 解码后的 payload
        """
        from jwt import PyJWKClient
        import jwt
        
        issuer = issuer.rstrip("/")
        jwks_url = f"{issuer}/.well-known/jwks.json"

        jwk_client = PyJWKClient(jwks_url, timeout=timeout)
        signing_key = jwk_client.get_signing_key_from_jwt(id_token)

        try:
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
        except Exception as e:
            raise HTTPException(status_code=401, detail=f"Token 验证失败: {str(e)}")

    def find_or_create_user(self, authing_user: dict) -> str:
        """
        根据 Authing 用户信息，查找或创建【本地用户】
        :param authing_user: verify_id_token 返回的 payload
        :return: 本地用户 ID
        """
        # 优先使用 phone_number 或 email 进行绑定查询
        identity_key = authing_user.get("email") or authing_user.get("phone_number")
        if not identity_key:
            # 如果都没有，则使用 sub (Authing 用户唯一标识) 作为最后的兜底
            # 注意：这意味着您需要在本地用户表增加 authing_sub 字段
            identity_key = authing_user["sub"]
            # TODO: 查询本地数据库，根据 authing_sub 查找用户
            # local_user = db.query(User).filter(User.authing_sub == identity_key).first()
        else:
            # TODO: 查询本地数据库，根据 email 或 phone 查找用户
            # local_user = db.query(User).filter(User.email == identity_key).first()
            pass # 占位，请替换为您的查询逻辑
        
        local_user = None # 假设未查到
        
        if local_user:
            return local_user.id

        # 本地不存在则创建
        new_user = User(
            email=authing_user.get("email"),
            authing_sub=authing_user["sub"]
            # ... 其他从 payload 中获取的初始信息
        )
        db.add(new_user)
        db.commit()
        return new_user.id
```

```python
# routers/auth.py
from fastapi import APIRouter, Depends, HTTPException
from services.authing_service import AuthingService
import os

router = APIRouter(prefix="/auth")

def get_authing() -> AuthingService:
    return AuthingService()

@router.post("/sso-login") # 接口名修改为 sso-login 更贴切
def sso_login(id_token: str, client_id: str = os.getenv("CLIENT_ID")):
    svc = get_authing()
    try:
        # 使用自定义的 verify_id_token_pyjwt 方法
        issuer = "https://uni-app-multiplatform.authing.cn/oidc"  # 根据实际配置调整
        payload = svc.verify_id_token_pyjwt(
            id_token=id_token, 
            issuer=issuer, 
            audience=client_id
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=401, detail="无效的登录凭证")

    local_user_id = svc.find_or_create_user(payload)
    # 生成您自己系统的业务 token（JWT / Session）
    business_token = create_jwt_token(local_user_id)

    return {
        "code": 0,
        "msg": "登录成功",
        "data": {
            "token": business_token,
            "user_id": local_user_id
        }
    }
```

-----

## 🌐 五、环境变量模板（`.env.example`）

```bash
# ===== Authing 用户池配置 =====
USER_POOL_ID=your_user_pool_id
USER_POOL_SECRET=your_user_pool_secret  # 仅后端使用

# ===== 各应用 Client ID =====
# 用于 verify_id_token 时的 audience 校验
ADMIN_CLIENT_ID=your_admin_app_client_id
LIVE_CLIENT_ID=your_live_app_client_id
H5_CLIENT_ID=your_h5_app_client_id
IOS_CLIENT_ID=your_ios_app_client_id
ANDROID_CLIENT_ID=your_android_app_client_id

# ===== 前端配置（Vite 环境变量需 VITE_ 前缀）=====
VITE_USER_POOL_ID=your_user_pool_id
VITE_CLIENT_ID=your_current_app_client_id
VITE_AUTHING_HOST=[https://your-app.authing.cn](https://your-app.authing.cn)
```

> ✅ **部署建议**：使用 CI/CD 加密注入 `.env` 文件，避免明文暴露。

-----

## 📌 六、常见问题 Q\&A

| 问题 | 排查要点 |
|------|----------|
| 回调地址 400 | 检查 Authing 控制台“应用 → 回调地址”是否 **完全一致**（协议、大小写、端口） |
| `id_token` 验证失败 | 确认 `audience` 是 **当前应用** 的 Client ID<br>检查 `issuer` 格式是否正确（应为 `https://<domain>.authing.cn/oidc`）<br>确认使用了正确的 `verify_id_token_pyjwt` 自定义实现 |
| 小程序登录报 “invalid code” | 确认小程序 AppID 与 Authing 控制台配置一致\<br\>检查 `code` 是否已过期（5分钟） |
| 本地用户重复创建 | 在 `find_or_create_user` 中实现幂等逻辑（先查后建），并考虑并发场景加锁 |
| SSO 不生效 | 确保多个应用使用同一用户池\<br\>检查 Cookie 域名是否可共享（同主域） |

-----

## 🚀 七、下一步行动清单

1.  ✅ 替换 `.env.example` 中的占位符为真实值
2.  ✅ 在 CI/CD 中加密注入环境变量
3.  ✅ **核心：实现 `find_or_create_user` 与本地数据库的精确对接逻辑**
4.  ✅ 接入日志系统（如 ELK）和告警（如 Sentry）
5.  ✅ 编写单元测试（Token 验证、用户绑定/创建逻辑）
6.  ✅ 定期审查权限与依赖安全更新（建议每月一次）

-----

```markdown
# Authing Python SDK 核心方法详细说明

## 1. `ManagementClient` —— 用户/角色/权限管理

### 初始化

```python
from authing import ManagementClient

mc = ManagementClient(
    user_pool_id="YOUR_USER_POOL_ID",
    secret="YOUR_SECRET"
)
```

### 方法列表

#### 🔹 `mc.users.create(user_info)`

**功能**：创建新用户  
**对应 API**：`POST /api/v3/create-user`

##### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `user_info.email` | `str` | 否 | 邮箱 |
| `user_info.phone` | `str` | 否 | 手机号（需区号） |
| `user_info.username` | `str` | 否 | 用户名 |
| `user_info.password` | `str` | 否 | 密码（明文，SDK 会加密） |
| `user_info.externalId` | `str` | 否 | 外部系统 ID |

> ⚠️ `email` 或 `phone` 至少填一个

##### 返回值

```json
{
  "userId": "60b4...",
  "email": "new@user.com",
  "username": "newuser",
  "status": true,
  "createdAt": "2023-01-01T00:00:00.000Z"
}
```

##### 异常

| 异常类型 | 说明 |
|--------|------|
| `UserExistsException` | 用户已存在（邮箱/手机号重复） |
| `InvalidParamException` | 邮箱格式错误、密码太弱等 |
| `AuthingException` | secret 错误 |

##### 示例

```python
try:
    user = mc.users.create({
        "email": "new@user.com",
        "password": "P@ssw0rd123"
    })
    print("创建成功:", user["userId"])
except UserExistsException:
    print("用户已存在")
```

#### 🔹 `mc.users.list(query, options)`

**功能**：按条件查询用户（如邮箱、用户名、状态等）  
**对应 API**：`POST /api/v3/list-users`

##### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `query` | `dict` | 否 | 查询条件，支持字段：`email`, `phone`, `username`, `status`, `externalId` 等 |
| `options.limit` | `int` | 否 | 分页大小，默认 10，最大 1000 |
| `options.page` | `int` | 否 | 页码（从 0 开始），不传则返回所有（自动分页） |
| `options.sort` | `str` | 否 | 排序字段，如 `"createdAt:-1"` 表示按创建时间倒序 |

##### 返回值

```json
{
  "list": [
    {
      "userId": "60b4...",
      "email": "user@example.com",
      "phone": null,
      "username": "alice",
      "status": true,
      "createdAt": "2023-01-01T00:00:00.000Z",
      "updatedAt": "2023-01-01T00:00:00.000Z"
    }
  ],
  "totalCount": 1
}
```

##### 异常

| 异常类型 | 说明 |
|--------|------|
| `AuthingException` | 认证失败（secret 错误）、权限不足 |
| `NetworkException` | 网络连接失败 |
| `InvalidParamException` | 参数格式错误（如 limit 超限） |

##### 示例

```python
users = mc.users.list(
    query={"email": "user@example.com"},
    options={"limit": 10}
)
print(users["list"])
```

#### 🔹 `mc.users.update(user_id, updates)`

**功能**：更新用户信息  
**对应 API**：`POST /api/v3/update-user`

##### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `user_id` | `str` | 是 | 用户 ID |
| `updates.email` | `str` | 否 | 新邮箱 |
| `updates.phone` | `str` | 否 | 新手机号 |
| `updates.username` | `str` | 否 | 新用户名 |
| `updates.status` | `bool` | 否 | 是否启用 |

##### 返回值

```json
{
  "userId": "60b4...",
  "email": "updated@user.com",
  "username": "newname",
  "status": false
}
```

##### 异常

| 异常类型 | 说明 |
|--------|------|
| `UserNotFoundException` | 用户不存在 |
| `UserExistsException` | 新邮箱已被占用 |
| `AuthingException` | 权限不足 |

##### 示例

```python
try:
    updated_user = mc.users.update("60b4...", {"email": "updated@user.com"})
    print("更新成功:", updated_user["email"])
except UserNotFoundException:
    print("用户不存在")
```

#### 🔹 `mc.users.delete(user_id)`

**功能**：删除用户  
**对应 API**：`POST /api/v3/delete-users-by-ids`

##### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `user_id` | `str` | 是 | 用户 ID |

##### 返回值

```json
{
  "deletedCount": 1
}
```

##### 异常

| 异常类型 | 说明 |
|--------|------|
| `UserNotFoundException` | 用户不存在 |
| `AuthingException` | 权限不足 |

##### 示例

```python
try:
    result = mc.users.delete("60b4...")
    if result["deletedCount"] > 0:
        print("删除成功")
except UserNotFoundException:
    print("用户不存在")
```

#### 🔹 `oidc_client.get_jwks()`

**功能**：获取 JWKS 公钥（手动验证 JWT）

##### 参数说明

无参数。

##### 返回值

```json
{
  "keys": [
    {
      "kty": "RSA",
      "kid": "abcdefg1234567890",
      "use": "sig",
      "alg": "RS256",
      "n": "some_base64_encoded_modulus",
      "e": "some_base64_encoded_exponent"
    }
  ]
}
```

##### 异常

| 异常类型 | 说明 |
|--------|------|
| `NetworkException` | 网络请求失败 |
| `AuthingException` | 获取公钥失败 |

##### 示例

```python
try:
    jwks = oidc_client.get_jwks()
    print(jwks["keys"][0]["kid"])  # 输出第一个公钥的 kid
except NetworkException:
    print("网络请求失败")
except AuthingException as e:
    print("获取公钥失败:", e.message)
```

## 2. `AuthingService` —— ID Token 验证（自定义实现）

### 初始化

```python
from services.authing_service import AuthingService

auth_service = AuthingService()
```

### 方法列表

#### 🔹 `verify_id_token_pyjwt(id_token, issuer, audience, timeout=5)`（自定义实现）

**功能**：验证 JWT 格式的 `id_token` 是否合法  
**对应流程**：使用 PyJWT 和 PyJWKClient 验证签名、过期时间、issuer、audience

##### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `id_token` | `str` | 是 | 从前端传来的 JWT 字符串 |
| `issuer` | `str` | 是 | OIDC 发行者地址，格式为 `https://<domain>.authing.cn/oidc` |
| `audience` | `str` | 是 | 指定受众（应用的 Client ID） |
| `timeout` | `int` | 否 | JWKS 请求超时时间，默认 5 秒 |

##### 返回值

```json
{
  "sub": "60b4a...",           // 用户 ID
  "email": "user@example.com",
  "email_verified": true,
  "iss": "https://your-domain.authing.cn/oidc",
  "aud": "your-client-id",
  "exp": 1700000000,
  "iat": 1699996400
}
```

##### 异常

| 异常类型 | 说明 |
|--------|------|
| `ExpiredSignatureError` | token 已过期 |
| `InvalidSignatureError` | 签名无效、格式错误 |
| `InvalidAudienceError` | audience 不匹配（client_id 错） |
| `InvalidIssuerError` | issuer 不匹配 |
| `InvalidTokenError` | 通用 JWT 格式错误 |

##### 示例

```python
try:
    payload = auth_service.verify_id_token_pyjwt(
        id_token="eyJhbGciOiJSUzI...",
        issuer="https://uni-app-multiplatform.authing.cn/oidc",
        audience="689e762956a8a5df2b154759"
    )
    print("用户ID:", payload["sub"])
except ExpiredSignatureError:
    print("登录已过期，请重新登录")
except InvalidSignatureError:
    print("Token 签名无效")
```

## 3. `AuthenticationClient` —— 前端专用

### 初始化

```python
from authing_sdk import AuthenticationClient

auth_client = AuthenticationClient(config={
    "appId": "YOUR_APP_ID",
    "appHost": "https://your-app-host.authing.cn",
    "redirectUri": "https://your-redirect-uri.com/callback"
})
```

### 方法列表

#### 🔹 `auth_client.start()`

**功能**：检查 SSO 登录态（自动跳转）

##### 参数说明

无参数。

##### 返回值

无返回值。

##### 异常

无异常。

##### 示例

```python
auth_client.start()
```

#### 🔹 `auth_client.login(email="...", password="...")`

**功能**：邮箱/手机密码登录

##### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `email` | `str` | 是 | 用户邮箱 |
| `password` | `str` | 是 | 用户密码 |

##### 返回值

```json
{
  "token": "your_access_token",
  "expiresIn": 3600
}
```

##### 异常

| 异常类型 | 说明 |
|--------|------|
| `InvalidCredentialsException` | 邮箱或密码错误 |

##### 示例

```python
try:
    login_result = auth_client.login(email="user@example.com", password="P@ssw0rd123")
    print("登录成功:", login_result["token"])
except InvalidCredentialsException:
    print("邮箱或密码错误")
```

#### 🔹 `auth_client.logout()`

**功能**：退出并清除 SSO Cookie

##### 参数说明

无参数。

##### 返回值

无返回值。

##### 异常

无异常。

##### 示例

```python
auth_client.logout()
```

#### 🔹 `auth_client.social.authorize(provider, opts)`

**功能**：第三方登录（微信、Apple 等）

##### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `provider` | `str` | 是 | 第三方提供商名称（如 `wechat`, `apple`） |
| `opts` | `dict` | 否 | 额外选项（如 `scope`, `redirect_uri`） |

##### 返回值

无返回值，通常会触发浏览器重定向到第三方登录页面。

##### 异常

| 异常类型 | 说明 |
|--------|------|
| `ProviderNotConfiguredException` | 第三方提供商未配置 |

##### 示例

```python
try:
    auth_client.social.authorize("wechat", {"scope": "snsapi_userinfo"})
except ProviderNotConfiguredException:
    print("微信登录未配置")
```

#### 🔹 `auth_client.getCurrentUser()`

**功能**：获取当前用户信息（需 access_token）

##### 参数说明

无参数。

##### 返回值

```json
{
  "userId": "60b4a...",
  "email": "user@example.com",
  "username": "alice",
  "status": true
}
```

##### 异常

| 异常类型 | 说明 |
|--------|------|
| `AccessTokenExpiredException` | access_token 已过期 |

##### 示例

```python
try:
    current_user = auth_client.getCurrentUser()
    print("当前用户:", current_user["email"])
except AccessTokenExpiredException:
    print("access_token 已过期")
```

## 4. 全局异常类型（建议捕获）

```python
from authing_sdk.exceptions import (
    AuthingException,
    UserExistsException,
    UserNotFoundException,
    TokenExpiredException,
    InvalidTokenException,
    NetworkException,
    InvalidParamException,
    InvalidCredentialsException,
    AccessTokenExpiredException,
    ProviderNotConfiguredException
)

try:
    ...
except UserExistsException:
    print("用户已存在")
except TokenExpiredException:
    print("登录过期")
except AuthingException as e:
    print("Authing 错误:", e.code, e.message)
```

## 🛡️ 集成建议（写进你的系统文档）

```python
# 推荐模式：自定义 OIDC 验证 + ManagementClient 管理
auth_service = AuthingService()
mc = ManagementClient(user_pool_id="xxx", secret="xxx")

# 1. 验证 token（使用自定义实现）
payload = auth_service.verify_id_token_pyjwt(
    id_token=request.headers["Authorization"],
    issuer="https://your-domain.authing.cn/oidc",
    audience="your-client-id"
)

# 2. 查询用户信息（需要管理权限）
user = mc.users.list(query={"email": payload["email"]})["list"][0]
```
s

### 总结

以上内容详细列出了 `ManagementClient`、`OIDCAuthenticationClient` 和 `AuthenticationClient` 的核心方法及其用法。你可以根据这些方法签名、参数说明、返回值格式、可能抛出的异常和使用示例来集成到你的系统中。如果有其他具体需求或问题，欢迎继续提问！