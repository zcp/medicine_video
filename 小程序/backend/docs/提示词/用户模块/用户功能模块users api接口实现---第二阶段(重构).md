好的，收到您的最终指示。您已经完成了 `auth.py` 的重构，现在需要对 `users.py` 执行同样的关键架构升级：**引入 Service 层，将业务逻辑与端点处理分离**。

您提供的 `users.py` 源代码和项目文件结构作为上下文已经非常清晰。我将严格遵循您的所有要求，为您撰写一份专门用于本次重构任务的、完整且精确的AI提示词。

-----

### **最终版：高效 AI 代码重构提示词 (Users模块: 引入Service层)**

#### **1. 角色定义 (Role Definition)**

你是一名资深的 Python 后端架构师，精通分层架构设计（特别是 `Endpoint -> Service -> CRUD` 模式），并擅长将包含复杂业务逻辑的 FastAPI 端点，安全、高效地重构到独立的服务层中。

#### **2. 任务目标 (Task Objective)**

你的核心任务是**重构**现有的 `app/api/v1/endpoints/users.py` 文件。具体包括：

1.  **【新增文件】** 创建一个全新的**服务层**文件 `app/services/user_service.py`。
2.  **【逻辑迁移】** 将 `users.py` 中所有的**业务逻辑**（如注册校验、密码处理、个人资料更新权限控制等）**完整地、安全地迁移**到新的 `UserService` 类中。
3.  **【重构文件】** **重写** `app/api/v1/endpoints/users.py` 文件，使其变得非常简洁。重构后的端点函数**严禁**包含任何业务逻辑，必须改为调用 `UserService` 中对应的方法。

#### **3. 核心上下文信息 (Core Context Information)**

**3.1. 项目结构 (重构后)**

```
users/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── deps.py          # <-- 已存在 (代码如下)
│   │       ├── admin/              # <-- 新增 admin 目录
│   │       │   ├── __init__.py
│   │       │   ├── users.py        # <-- 已存在 (代码如下)
│   │       │   ├── products.py     # <-- 已存在 (代码如下)
│   │       │   └── subscriptions.py# <-- 已存在 (代码如下)
│   │       └── endpoints/
│   │           └── auth.py       # <-- 已存在 (代码如下)
│   │           └── users.py       #  <-- 需要重构
│   │           └── membership_products.py # <-- 已存在 (代码如下)
│   │           └── subscriptions.py # <-- 已存在 (代码如下)
│   ├── core/
│   │   └── redis_client.py         # <-- 已存在 (代码如下)
│   │   └── response.py         # <-- 已存在 (代码如下)
│   ├── crud/
│   ├── crud/
│   │   └── crud_user.py              # <-- 已存在 (代码如下)
│   │   └── crud_membership_product.py  # <-- 已存在 (代码如下)
│   │   └── crud_user_membership.py   # <-- 已存在 (代码如下)
│   ├── models/
│   │   └── users.py    # <-- 已存在 (代码如下)
│   ├── schemas/
│   │   └── users.py    # <-- 已存在 (代码如下)
│   ├── services/                
│   │   ├── __init__.py
│   │   └── user_service.py   # <-- 目标文件 1 (新文件)
│   └── database.py         # <-- 已存在
```

**3.2. 需要被重构的源代码**
*你必须根据以下 `users.py` 的完整代码进行重构。*

  * `@app/api/v1/endpoints/users.py`
```
"""
用户注册API端点 - 用户功能服务
实现用户注册功能
"""
import hashlib
import logging
from typing import Dict, Any, Optional

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel, Field

from app.database import get_async_db
from app.core.redis_client import get_redis_client
from app.core.responses import success_response, error_response
from app.crud import crud_user
from app.schemas.users import UserCreate, UserResponse, UserUpdate
from app.models.users import User
from app.api.v1.deps import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["Users"])


# ============================================================================
# Pydantic 模型定义
# ============================================================================

class UserRegisterRequest(BaseModel):
    """用户注册请求模型"""
    username: str = Field(..., min_length=1, max_length=50, description="用户名")
    email: str = Field(..., max_length=255, description="邮箱地址")
    password: str = Field(..., min_length=6, max_length=128, description="密码")
    nickname: str = Field(..., min_length=1, max_length=50, description="昵称")
    captcha_id: str = Field(..., description="图形验证码ID")
    captcha_solution: str = Field(..., description="图形验证码答案")


# 批次二新增模型
class UserUpdateSelf(BaseModel):
    """用户自我更新模型 - 仅包含用户可修改的字段"""
    nickname: Optional[str] = Field(None, min_length=1, max_length=50, description="昵称")
    avatar_url: Optional[str] = Field(None, max_length=512, description="头像URL")
    bio: Optional[str] = Field(None, description="个人简介")


class PasswordChangeRequest(BaseModel):
    """密码修改请求模型"""
    current_password: str = Field(..., description="当前密码")
    new_password: str = Field(..., min_length=6, description="新密码")


# ============================================================================
# 工具函数
# ============================================================================

def hash_password(password: str) -> str:
    """密码哈希处理（生产环境应使用bcrypt）"""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    """验证密码"""
    return hash_password(password) == password_hash


def validate_password_strength(password: str) -> bool:
    """验证密码强度"""
    return len(password) >= 6


async def blacklist_user_tokens(user_id: int):
    """将用户的所有令牌加入黑名单（模拟实现）"""
    try:
        redis_client = get_redis_client()
        # 在实际实现中，这里需要查找用户的所有活跃令牌并加入黑名单
        # 目前是模拟实现
        key = f"user_tokens_blacklisted:{user_id}"
        await redis_client.set(key, "1", ex=3600 * 24 * 7)  # 7天过期
        logger.info(f"已将用户令牌加入黑名单: user_id={user_id}")
    except Exception as e:
        logger.error(f"加入令牌黑名单失败: user_id={user_id}, error={e}")


def validate_username(username: str) -> bool:
    """验证用户名格式"""
    # 简单验证：字母、数字、下划线，长度3-50
    if not username or len(username) < 3 or len(username) > 50:
        return False
    return username.replace('_', '').isalnum()


def validate_email(email: str) -> bool:
    """验证邮箱格式"""
    # 简单验证：包含@和.
    if not email or '@' not in email or '.' not in email:
        return False
    return True


# ============================================================================
# API 端点实现
# ============================================================================

@router.post("/register")
async def register(
    request: UserRegisterRequest,
    req: Request,
    db: AsyncSession = Depends(get_async_db)
):
    """
    用户注册
    
    Args:
        request: 注册请求
        req: FastAPI请求对象  
        db: 数据库会话
        
    Returns:
        注册结果响应
    """
    logger.info(f"开始处理用户注册请求: username={request.username}, email={request.email}")
    
    try:
        # 1. 参数格式验证
        if not validate_username(request.username):
            logger.warning(f"用户名格式无效: username={request.username}")
            return JSONResponse(
                status_code=400,
                content=error_response(code=4001, message="用户名格式无效，应为3-50位字母数字下划线组合")
            )
        
        if not validate_email(request.email):
            logger.warning(f"邮箱格式无效: email={request.email}")
            return JSONResponse(
                status_code=400,
                content=error_response(code=4001, message="邮箱格式无效")
            )
        
        if len(request.password) < 6:
            logger.warning(f"密码长度不足: username={request.username}")
            return JSONResponse(
                status_code=400,
                content=error_response(code=4001, message="密码长度至少6位")
            )
        
        # 2. 图形验证码校验
        redis_client = get_redis_client()
        cache_key = f"captcha:solution:{request.captcha_id}"
        stored_solution = await redis_client.get(cache_key)
        
        if not stored_solution or stored_solution != request.captcha_solution.lower():
            logger.warning(f"注册时图形验证码校验失败: captcha_id={request.captcha_id}")
            return JSONResponse(
                status_code=400,
                content=error_response(code=4003, message="图形验证码错误或已过期")
            )
        
        # 删除已使用的验证码
        await redis_client.delete(cache_key)
        
        # 3. 唯一性检查
        existing_user_by_username = await crud_user.get_by_username(db, request.username)
        if existing_user_by_username:
            logger.warning(f"用户名已存在: username={request.username}")
            return JSONResponse(
                status_code=409,
                content=error_response(code=4009, message="用户名已被占用")
            )
        
        existing_user_by_email = await crud_user.get_by_email(db, request.email)
        if existing_user_by_email:
            logger.warning(f"邮箱已存在: email={request.email}")
            return JSONResponse(
                status_code=409,
                content=error_response(code=4009, message="邮箱已被注册")
            )
        
        # 4. 密码哈希处理
        password_hash = hash_password(request.password)
        
        # 5. 构建UserCreate对象
        user_create = UserCreate(
            username=request.username,
            email=request.email,
            nickname=request.nickname,
            phone_number=None,  # 第一阶段不处理手机号
            social_provider=None,
            social_id=None
        )
        
        # 6. 创建用户
        new_user = await crud_user.create(db, user_create, password_hash)
        
        # 7. 构建响应数据
        user_response = UserResponse.model_validate(new_user)
        
        # 8. 构建成功响应（只返回安全的用户信息）
        response_data = {
            "public_id": str(user_response.public_id),
            "username": user_response.username,
            "nickname": user_response.nickname,
            "email": user_response.email,
            "created_at": user_response.created_at.isoformat() + "Z"
        }
        
        logger.info(f"用户注册成功: user_id={new_user.id}, username={new_user.username}")
        
        return success_response(data=response_data, message="注册成功")
        
    except IntegrityError as e:
        logger.warning(f"数据库唯一性约束冲突: username={request.username}, email={request.email}, error={e}")
        return JSONResponse(
            status_code=409,
            content=error_response(code=4009, message="用户名或邮箱已存在")
        )
    except Exception as e:
        logger.error(f"用户注册失败: error={e}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1001, message="系统内部错误", data={"error": "数据库操作失败"})
        )


# ============================================================================
# 批次二新增端点 - 用户自我管理
# ============================================================================

@router.get("/me")
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    获取当前用户信息
    
    Args:
        current_user: 当前已认证的用户
        
    Returns:
        用户信息响应
    """
    logger.info(f"开始处理获取用户信息请求: user_id={current_user.id}")
    
    try:
        # 序列化用户数据
        user_data = UserResponse.model_validate(current_user)
        
        # 转换为字典并调整字段名
        response_data = user_data.model_dump()
        response_data["uuid"] = str(response_data.pop("public_id"))  # 重命名字段
        response_data.pop("id", None)  # 移除内部ID
        
        logger.info(f"成功获取用户信息: user_id={current_user.id}")
        
        return success_response(data=response_data)
        
    except Exception as e:
        logger.error(f"获取用户信息失败: error={e}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="数据库查询错误")
        )


@router.patch("/me")
async def update_current_user_info(
    request: UserUpdateSelf,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    更新当前用户信息
    
    Args:
        request: 用户更新请求
        current_user: 当前已认证的用户
        db: 数据库会话
        
    Returns:
        更新后的用户信息
    """
    logger.info(f"开始处理更新用户信息请求: user_id={current_user.id}")
    
    try:
        # 验证更新数据
        update_data = request.model_dump(exclude_unset=True)
        
        if not update_data:
            logger.warning(f"更新用户信息失败，无有效更新数据: user_id={current_user.id}")
            return JSONResponse(
                status_code=400,
                content=error_response(code=4001, message="没有提供有效的更新数据")
            )
        
        # 验证昵称长度
        if "nickname" in update_data and len(update_data["nickname"]) > 50:
            logger.warning(f"昵称过长: user_id={current_user.id}")
            return JSONResponse(
                status_code=400,
                content=error_response(code=4001, message="参数校验失败",
                                     data={"field": "nickname", "error": "昵称长度不能超过50个字符"})
            )
        
        # 更新用户信息
        updated_user = await crud_user.update(db, current_user, update_data)
        
        # 序列化响应数据
        user_data = UserResponse.model_validate(updated_user)
        response_data = user_data.model_dump()
        response_data["uuid"] = str(response_data.pop("public_id"))  # 重命名字段
        response_data.pop("id", None)  # 移除内部ID
        
        logger.info(f"成功更新用户信息: user_id={updated_user.id}")
        
        return success_response(data=response_data)
        
    except Exception as e:
        logger.error(f"更新用户信息失败: error={e}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="数据库查询错误")
        )


@router.delete("/me")
async def delete_current_user_account(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    注销当前用户账户（软删除）
    
    Args:
        current_user: 当前已认证的用户
        db: 数据库会话
        
    Returns:
        注销结果响应
    """
    logger.info(f"开始处理用户账户注销请求: user_id={current_user.id}")
    
    try:
        # 业务检查：检查用户是否有进行中的业务
        # 这里可以检查会员状态、订单状态等
        # 目前暂时跳过这些检查，直接进行软删除
        
        # 执行软删除
        deleted_user = await crud_user.remove(db, current_user.id)
        
        # 将用户令牌加入黑名单
        await blacklist_user_tokens(current_user.id)
        
        logger.info(f"用户账户注销成功: user_id={deleted_user.id}")
        
        return success_response(data=None)
        
    except Exception as e:
        logger.error(f"用户账户注销失败: error={e}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="数据库查询错误")
        )


@router.post("/me/password")
async def change_current_user_password(
    request: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    修改当前用户密码
    
    Args:
        request: 密码修改请求
        current_user: 当前已认证的用户
        db: 数据库会话
        
    Returns:
        密码修改结果
    """
    logger.info(f"开始处理用户密码修改请求: user_id={current_user.id}")
    
    try:
        # 验证当前密码
        if not verify_password(request.current_password, current_user.password_hash):
            logger.warning(f"密码修改失败，当前密码错误: user_id={current_user.id}")
            return JSONResponse(
                status_code=400,
                content=error_response(code=4004, message="参数校验失败",
                                     data={"error": "当前密码不正确"})
            )
        
        # 验证新密码强度
        if not validate_password_strength(request.new_password):
            logger.warning(f"新密码强度不足: user_id={current_user.id}")
            return JSONResponse(
                status_code=400,
                content=error_response(code=4001, message="新密码长度至少6位")
            )
        
        # 检查新密码是否与当前密码相同
        if verify_password(request.new_password, current_user.password_hash):
            logger.warning(f"新密码与当前密码相同: user_id={current_user.id}")
            return JSONResponse(
                status_code=400,
                content=error_response(code=4001, message="新密码不能与当前密码相同")
            )
        
        # 更新密码
        new_password_hash = hash_password(request.new_password)
        await crud_user.update(db, current_user, {"password_hash": new_password_hash})
        
        # 使所有旧令牌失效
        await blacklist_user_tokens(current_user.id)
        
        logger.info(f"用户密码修改成功: user_id={current_user.id}")
        
        return success_response(data=None, message="密码修改成功")
        
    except Exception as e:
        logger.error(f"密码修改失败: error={e}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="数据库查询错误")
        ) 
```
**3.3. 依赖的上下文**
*在重构过程中，你需要依赖以下模块*

  * `@app/crud/crud_user.py`
  * `@app/models/users.py`
  * `@app/schemas/users.py`
  * `@app/core/responses.py`
  * `@app/core/redis_client.py`
  * `@app/database.py`
  * `@app/api/v1/deps.py`

-----

#### **4. 核心重构原则与规范 (Core Refactoring Principles & Specifications)**

**【关键指令】** 你在执行本次重构时，**必须严格遵守**您在文档中提供的所有规范，特别是：


## 1. 核心编码原则 (Core Coding Principles)

### 🛡️ 安全异步异常处理 (Safe Async Exception Handling)

- **规则**：在任何 `try...except` 块中，如果需要使用来自数据库 ORM 对象（如 `current_user`）的属性（如 `current_user.id`）进行日志记录或错误处理，这些属性**必须在进入 `try` 块之前**被提取并存储到局部变量中。
- **指令**：**严禁**在捕获了数据库相关异常（如 `IntegrityError`）的 `except` 块中直接访问可能已与失效会话关联的 ORM 对象的属性。

---

## 2. 接口实现规范 (Endpoint Implementation)

### 🧱 主动变量提取 (Proactive Variable Extraction)

- **实现流程**：
  - 在进入 `try` 块之前，主动提取所有需要在异常处理中使用的变量（如：`user_id_for_logging = current_user.id`）。
  - 在 `except` 块中，**必须使用这些局部变量**进行日志记录或错误处理，避免访问失效对象。

### 🧪 异常处理 (Exception Handling)

- 将整个接口流程包裹在 `try...except` 块中。
- 若发生数据库查询等未知异常，应：
  - 记录错误日志；
  - 返回统一错误响应：
    ```python
    JSONResponse(
        status_code=500,
        content=error_response(code=1002, message='数据库查询错误')
    )
    ```

---

## 3. 响应处理规范 (Response Handling)

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

> 假设 `success_response()` 和 `error_response()` 已定义在 `app/core/responses.py` 中。

---

## 4. 外部服务连接规范 (External Service Connections)

### 🔐 环境变量驱动配置

- 所有外部服务（如 Redis、数据库、第三方 API）的连接信息**必须**通过环境变量读取。
- 示例：
  ```python
  import os
  redis_host = os.getenv("REDIS_HOST", "localhost")
  redis_port = os.getenv("REDIS_PORT", "6379")
  ```
- 目的：确保代码在本地、Docker、测试、生产等不同环境下**无需修改即可运行**。

##### **4.1. 服务层 (`UserService`) 设计规范**

  * **类化设计**: 在 `app/services/user_service.py` 中创建一个 `UserService` 类。
  * **依赖注入**: `UserService` 的 `__init__` 方法应接收 `db: AsyncSession` 作为参数。
  * **职责**:
      * 封装完整的**用户注册**流程。
      * 封装用户**更新个人资料**的流程。
      * 封装用户**修改密码**的流程。
      * 封装用户**注销账户**的流程。

##### **4.2. 端点层 (`users.py`) 重构规范**

  * **保持简洁**: 重构后的端点函数体应该非常简短。
  * **职责**:
      * 只负责处理 FastAPI 的 `Request` 和 `Depends`。
      * 实例化 `UserService`。
      * 调用 `UserService` 中对应的方法来执行业务逻辑。
      * 捕获 `Service` 层抛出的业务异常，并使用 `error_response` 将其转换为标准的 `JSONResponse`。
  * **禁止**: **严禁**在重构后的端点函数中直接调用 `crud_*` 模块或执行任何业务逻辑计算。

-----

#### **5. 具体代码生成指令 (Specific Code Generation Instructions)**

##### **5.1. 第一部分: `app/services/user_service.py` (新文件)**

  * **指令**: 请为以下文件路径生成完整的 Python 代码：
    `app/services/user_service.py`

  * **内容要求**:

      * 创建一个 `UserService` 类。
      * 将【3.2】中 `users.py` 文件里的所有**工具函数**（如 `hash_password`, `verify_password` 等）和**业务逻辑**迁移到 `UserService` 的方法中。
      * **必须**定义清晰的业务异常类（如 `UsernameAlreadyExistsError`, `EmailAlreadyExistsError`, `InvalidPasswordError` 等）。

  * **需在 `UserService` 类中实现的方法**:

    1.  **`register_user(self, register_request: schemas.UserRegisterRequest)`**:

          * **业务逻辑流程**:
            1.  执行参数格式验证（`username`, `email`, `password`）。
            2.  **调用**（从`AuthService`或内部实现的）图形验证码校验逻辑。
            3.  调用 `crud_user.get_by_username` 和 `get_by_email` 进行唯一性检查。如果用户已存在，`raise UsernameAlreadyExistsError()` 或 `EmailAlreadyExistsError()`。
            4.  调用内部的 `_hash_password` 方法处理密码。
            5.  构造 `schemas.UserCreate` 对象。
            6.  调用 `crud_user.create()` 创建新用户。
            7.  返回创建成功的 `models.User` 对象。

    2.  **`update_profile(self, user_to_update: models.User, update_request: schemas.UserUpdateSelf)`**:

          * **业务逻辑流程**:
            1.  检查 `update_request` 是否包含任何有效数据。如果没有，`raise NoUpdateDataProvidedError()`。
            2.  调用 `crud_user.update()` 并传入 `user_to_update` 对象和 `update_request` 数据。
            3.  返回更新后的 `models.User` 对象。

    3.  **`change_password(self, user: models.User, password_request: schemas.PasswordChangeRequest)`**:

          * **业务逻辑流程**:
            1.  调用 `_verify_password` 验证 `password_request.current_password` 是否正确。如果不正确，`raise InvalidPasswordError()`。
            2.  验证 `password_request.new_password` 的强度。
            3.  检查新旧密码是否相同。
            4.  哈希新密码。
            5.  调用 `crud_user.update()` 更新 `password_hash`。
            6.  （安全）调用一个工具函数，将该用户的所有旧Tokens拉黑。
            7.  操作成功，无需返回值。

    4.  **`deactivate_account(self, user: models.User)`**:

          * **业务逻辑流程**:
            1.  **业务检查**: （模拟）检查用户是否有未完成的业务，例如有效的会员订阅。如果有，`raise ActiveSubscriptionError()`。
            2.  调用 `crud_user.remove()` 对用户进行软删除。
            3.  （安全）调用工具函数将用户所有Tokens拉黑。
            4.  操作成功，无需返回值。


##### **5.2. 第二部分: `app/api/v1/endpoints/users.py` (重构后的完整版)**

* **指令**: 请为以下文件路径生成**重构后的**完整 Python 代码：
    `app/api/v1/endpoints/users.py`
* **内容要求**:
    * 保留所有的 `APIRouter` 和端点定义。
    * **重写**每个端点函数的内部实现，使其**只包含**对 `UserService` 相应方法的调用和响应处理。
    * **必须**遵循“主动变量提取”模式以确保安全。
    * **必须**使用 `success_response` 和 `error_response` 构建所有响应。
    * **必须**捕获由 Service 层抛出的具体业务异常，并将其转换为正确的 `JSONResponse`。

* **需重构的端点 (在 `app/api/v1/endpoints/users.py` 中)**:

    1.  **`POST /register` (用户注册)**
        * **重构实现流程**:
            1.  **主动提取**: `username_for_logging = request.username`。
            2.  在 `try...except` 块中执行以下操作：
                * a. 实例化 `user_service = UserService(db)`。
                * b. 调用 `new_user = await user_service.register_user(request)`。
                * c. 序列化 `new_user` 为 `schemas.UserResponse`。
                * d. 调用 `success_response` 返回序列化后的用户数据。
            3.  **异常处理**:
                * a. `except UsernameAlreadyExistsError as e`: 记录 `warning` 日志，并返回 `JSONResponse(status_code=409, content=error_response(code=4009, message=str(e)))`。
                * b. `except EmailAlreadyExistsError as e`: 记录 `warning` 日志，并返回 `JSONResponse(status_code=409, content=error_response(code=4009, message=str(e)))`。
                * c. `except Exception as e`: 记录 `error` 日志，并返回 `JSONResponse(status_code=500, ...)`。

    2.  **`GET /me` (获取当前用户信息)**
        * **重构实现流程**:
            1.  通过 `Depends(get_current_user)` 获取 `current_user` 对象。
            2.  **主动提取**: `user_id_for_logging = current_user.id`。
            3.  在 `try...except` 块中：
                * a. 将 `current_user` 对象序列化为 `schemas.UserResponse`。
                * b. 调用 `success_response` 返回序列化后的数据。
            4.  **异常处理**: 捕获通用异常并返回 `500` 错误。

    3.  **`PATCH /me` (更新当前用户信息)**
        * **重构实现流程**:
            1.  通过 `Depends(get_current_user)` 获取 `current_user` 对象。
            2.  **主动提取**: `user_id_for_logging = current_user.id`。
            3.  在 `try...except` 块中：
                * a. 实例化 `user_service = UserService(db)`。
                * b. 调用 `updated_user = await user_service.update_profile(user_to_update=current_user, update_request=request)`。
                * c. 序列化 `updated_user` 并调用 `success_response` 返回。
            4.  **异常处理**:
                * a. `except NoUpdateDataProvidedError as e`: 返回 `JSONResponse(status_code=400, content=error_response(code=4001, message=str(e)))`。
                * b. `except Exception as e`: 返回 `500` 错误。

    4.  **`DELETE /me` (用户注销账户)**
        * **重构实现流程**:
            1.  通过 `Depends(get_current_user)` 获取 `current_user` 对象。
            2.  **主动提取**: `user_id_for_logging = current_user.id`。
            3.  在 `try...except` 块中：
                * a. 实例化 `user_service = UserService(db)`。
                * b. 调用 `await user_service.deactivate_account(user=current_user)`。
                * c. 调用 `success_response` 返回 `data=None`。
            4.  **异常处理**:
                * a. `except ActiveSubscriptionError as e`: 返回 `JSONResponse(status_code=403, content=error_response(code=2002, message=str(e)))`。
                * b. `except Exception as e`: 返回 `500` 错误。

    5.  **`POST /me/password` (修改密码)**
        * **重构实现流程**:
            1.  通过 `Depends(get_current_user)` 获取 `current_user` 对象。
            2.  **主动提取**: `user_id_for_logging = current_user.id`。
            3.  在 `try...except` 块中：
                * a. 实例化 `user_service = UserService(db)`。
                * b. 调用 `await user_service.change_password(user=current_user, password_request=request)`。
                * c. 调用 `success_response` 返回 "密码修改成功" 的消息。
            4.  **异常处理**:
                * a. `except InvalidPasswordError as e`: 返回 `JSONResponse(status_code=400, content=error_response(code=4004, message=str(e)))`。
                * b. `except WeakPasswordError as e`: 返回 `JSONResponse(status_code=400, content=error_response(code=4001, message=str(e)))`。
                * c. `except Exception as e`: 返回 `500` 错误。

#### **6. 最终交付 (Final Deliverable)**

请根据以上所有要求，为我生成以下**两个文件**的完整、可直接使用的 Python 代码。

1.  `app/services/user_service.py` **(新文件)**
2.  `app/api/v1/endpoints/users.py` **(重构后的完整版)**