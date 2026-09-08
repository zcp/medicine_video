

1.  Write **detailed tests** for the stable `crud` layer.
2.  Write **high-level tests** for the `endpoints` layer to verify the API contract and critical business logic, without delving into implementation details that will change.

-----


### **最终版：高效 AI 测试代码生成提示词 (针对重构后的 Auth 模块)**

#### **1. 角色定义 (Role Definition)**

You are a Senior Python Backend Engineer specializing in automated testing. You are an expert in using `pytest` with `pytest-asyncio` and mocking frameworks like `pytest-mock`. Your task is to write a robust **unit test suite** for the provided `UserService` class.

#### **2. 任务目标 (Task Objective)**

Your goal is to generate the complete code for **one new test file**: `tests/test_services/test_user_service.py`.

#### **3. 核心上下文信息 (Core Context Information)**

**3.1. Testing Strategy**
* **For `Service` layer (`test_user_service.py`)**: Test thoroughly using **mocking**. All external dependencies (like `crud_user` functions and the `redis_client`) **must be mocked** to test the `UserService` logic in complete isolation.

**3.2. Project Structure & Code Context**
*You must generate tests based on the logic within the following application code.*
* **被测试代码 (Code to be Tested)**:
    * `@app/services/user_service.py` 
* **依赖的上下文 (Dependencies & Context)**:
    * `@tests/conftest.py` (**作为测试环境和 Fixture 的来源，不可修改**)
    * `@app/models/users.py`
    * `@app/schemas/users.py`
    * `@app/crud/crud_users.py`
    * `@app/core/responses.py`


**3.3. Project Structure**

```
users/
├── app/
│   ├── api/
│   │   └── v1/
│   │       └── endpoints/
│   │           └── auth.py       # <-- 已存在 (代码如下)
│   │           └── users.py       # <-- 已存在 (代码如下)
│   ├── crud/
│   │   └── crud_users.py         # <-- 已存在 (代码如下)
│   │   └── crud_user_membership.py         # <-- 已存在 (代码如下)
│   │   └── crud_membership_product.py         # <-- 已存在 (代码如下)
│   ├── models/
│   │   └── users.py    # <-- 已存在 (代码如下)
│   ├── schemas/
│   │   └── users.py    # <-- 已存在 (代码如下)
│   ├── services/
│   │   └── user_service.py    # <-- 已存在 (代码如下)
│   └── database.py         # <-- 已存在
|___└── tests/
        ├── conftest.py               # <-- has been generated (for test setup)
        ├── test_users_service.py     # <-- To be generated
```


**3.5. 参考代码示例 (Reference Code Samples）**

*The following code is from another module in this project and has been successfully tested. You must use it as a primary reference for coding style, fixture usage, and testing patterns. The newly generated code should be consistent with these examples.*

```
"""
LiveCore Service - Test Configuration

This module contains pytest fixtures and configuration for testing.
"""

import os
import sys
import pytest
import asyncio
from typing import AsyncGenerator, Generator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from httpx import AsyncClient
from uuid import uuid4

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import Base, get_db
from app.models.live_core import LiveRoom, LiveSession, SessionStatistics

# --- 1. 从正确的位置导入 Celery App 实例，并给它一个清晰的别名 ---
from app.tasks.celery_app import app as celery_app_instance



# 测试数据库URL
#TEST_DATABASE_URL = "postgresql+asyncpg://postgres:324zq999@localhost:5432/live_core_test"

# 使用环境变量或默认值
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "324zq999")
POSTGRES_SERVER = os.getenv("POSTGRES_SERVER", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "live_core_test")

# 异步连接字符串（用于应用）
TEST_DATABASE_URL = f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_SERVER}:{POSTGRES_PORT}/{POSTGRES_DB}"


# 创建测试数据库引擎
engine = create_async_engine(TEST_DATABASE_URL, echo=True)

# 创建异步会话工厂
async_session_factory = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


# --- Pytest Fixtures ---
@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
async def setup_database():
    """设置测试数据库"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """提供数据库会话"""
    async with async_session_factory() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """提供异步HTTP客户端"""
    # 总是创建测试专用的FastAPI应用，不依赖外部服务
    from fastapi import FastAPI
    from app.api.v1.api import api_router
    
    # 创建测试专用的FastAPI应用
    app = FastAPI(
        title="LiveCore Service Test", 
        version="1.0.0",
        redirect_slashes=False  # 禁用自动重定向，避免307问题
    )
    
    # 使用与main.py相同的路由结构
    app.include_router(api_router, prefix="/api/v1")
    
    # 覆盖数据库依赖，使用测试数据库
    async def override_get_db():
        async with async_session_factory() as session:
            yield session
    
    app.dependency_overrides[get_db] = override_get_db
    
    # 使用测试服务器 - 独立应用，不依赖外部服务
    async with AsyncClient(app=app, base_url="http://localhost:8000") as client:
        yield client


@pytest.fixture
def sync_client() -> TestClient:
    """提供同步HTTP客户端"""
    try:
        from app.main import app
    except ImportError:
        # 如果main.py不存在，创建一个简单的FastAPI应用用于测试
        from fastapi import FastAPI
        from app.api.v1.endpoints.room import router as room_router
        
        app = FastAPI()
        app.include_router(room_router, prefix="/api/v1")
        
        # 覆盖数据库依赖
        async def override_get_db():
            async with async_session_factory() as session:
                yield session
        
        app.dependency_overrides[get_db] = override_get_db
    
    return TestClient(app)



# ... 其他 fixture ...

# ==================== Celery 测试配置 ====================

@pytest.fixture(scope="session")
def celery_config():
    """定义测试专用的同步配置"""
    return {
        "task_always_eager": True,
        "task_eager_propagates": True,
    }

@pytest.fixture(scope="session", autouse=True)
def configure_celery_for_test(celery_config):
    """
    一个会自动运行的 session 级 fixture。
    它会在所有测试开始前，将上面定义的同步配置应用到项目中共享的 Celery 实例上。
    """
    # --- 2. 确保这里使用的变量名与上面导入时的别名完全一致 ---
    celery_app_instance.conf.update(celery_config)
```

#### **被测试函数的源代码**
* `@app/services/user_service.py` 

```
"""
用户服务层 - UserService
封装所有用户相关的业务逻辑，包括注册、更新、密码管理、账户注销等
"""
import hashlib
import logging
from typing import Dict, Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.core.redis_client import get_redis_client
from app.crud import crud_user
from app.schemas.users import UserCreate, UserUpdateSelf
from app.models.users import User

logger = logging.getLogger(__name__)


# ============================================================================
# 业务异常定义
# ============================================================================

class UserServiceException(Exception):
    """用户服务基础异常"""
    pass


class UsernameAlreadyExistsError(UserServiceException):
    """用户名已存在异常"""
    def __init__(self, username: str):
        self.username = username
        super().__init__(f"用户名已被占用: {username}")


class EmailAlreadyExistsError(UserServiceException):
    """邮箱已存在异常"""
    def __init__(self, email: str):
        self.email = email
        super().__init__(f"邮箱已被注册: {email}")


class InvalidPasswordError(UserServiceException):
    """无效密码异常"""
    def __init__(self, message: str = "当前密码不正确"):
        super().__init__(message)


class WeakPasswordError(UserServiceException):
    """密码强度不足异常"""
    def __init__(self, message: str = "新密码长度至少6位"):
        super().__init__(message)


class NoUpdateDataProvidedError(UserServiceException):
    """没有提供更新数据异常"""
    def __init__(self, message: str = "没有提供有效的更新数据"):
        super().__init__(message)


class ActiveSubscriptionError(UserServiceException):
    """活跃订阅异常"""
    def __init__(self, message: str = "账户存在活跃订阅，无法注销"):
        super().__init__(message)


class CaptchaErrorException(UserServiceException):
    """图形验证码错误异常"""
    def __init__(self, message: str = "图形验证码错误或已过期"):
        super().__init__(message)


class ValidationError(UserServiceException):
    """参数验证异常"""
    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(f"{field}: {message}")


# ============================================================================
# 用户服务类
# ============================================================================

class UserService:
    """用户服务类"""
    
    def __init__(self, db: AsyncSession, redis_client=None):
        """
        初始化用户服务
        
        Args:
            db: 数据库会话
            redis_client: Redis客户端（可选，如果不提供会获取默认客户端）
        """
        self.db = db
        self.redis_client = redis_client or get_redis_client()
    
    # ========================================================================
    # 工具方法
    # ========================================================================
    
    def _hash_password(self, password: str) -> str:
        """密码哈希处理（生产环境应使用bcrypt）"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _verify_password(self, password: str, password_hash: str) -> bool:
        """验证密码"""
        return self._hash_password(password) == password_hash
    
    def _validate_password_strength(self, password: str) -> bool:
        """验证密码强度"""
        return len(password) >= 6
    
    def _validate_username(self, username: str) -> bool:
        """验证用户名格式"""
        # 简单验证：字母、数字、下划线，长度3-50
        if not username or len(username) < 3 or len(username) > 50:
            return False
        return username.replace('_', '').isalnum()
    
    def _validate_email(self, email: str) -> bool:
        """验证邮箱格式"""
        # 简单验证：包含@和.
        if not email or '@' not in email or '.' not in email:
            return False
        return True
    
    async def _verify_captcha(self, captcha_id: str, captcha_solution: str) -> bool:
        """验证图形验证码"""
        try:
            cache_key = f"captcha:solution:{captcha_id}"
            stored_solution = await self.redis_client.get(cache_key)
            
            if not stored_solution or stored_solution != captcha_solution.lower():
                return False
            
            # 删除已使用的验证码
            await self.redis_client.delete(cache_key)
            return True
        except Exception as e:
            logger.error(f"验证图形验证码失败: {e}")
            return False
    
    async def _blacklist_user_tokens(self, user_id: int):
        """将用户的所有令牌加入黑名单（模拟实现）"""
        try:
            # 在实际实现中，这里需要查找用户的所有活跃令牌并加入黑名单
            # 目前是模拟实现
            key = f"user_tokens_blacklisted:{user_id}"
            await self.redis_client.set(key, "1", ex=3600 * 24 * 7)  # 7天过期
            logger.info(f"已将用户令牌加入黑名单: user_id={user_id}")
        except Exception as e:
            logger.error(f"加入令牌黑名单失败: user_id={user_id}, error={e}")
    
    # ========================================================================
    # 主要业务方法
    # ========================================================================
    
    async def register_user(self, register_request) -> User:
        """
        用户注册
        
        Args:
            register_request: 注册请求对象
            
        Returns:
            创建成功的用户对象
            
        Raises:
            ValidationError: 参数验证失败
            CaptchaErrorException: 验证码错误
            UsernameAlreadyExistsError: 用户名已存在
            EmailAlreadyExistsError: 邮箱已存在
        """
        logger.info(f"开始处理用户注册请求: username={register_request.username}, email={register_request.email}")
        
        try:
            # 1. 参数格式验证
            if not self._validate_username(register_request.username):
                logger.warning(f"用户名格式无效: username={register_request.username}")
                raise ValidationError("username", "用户名格式无效，应为3-50位字母数字下划线组合")
            
            if not self._validate_email(register_request.email):
                logger.warning(f"邮箱格式无效: email={register_request.email}")
                raise ValidationError("email", "邮箱格式无效")
            
            if len(register_request.password) < 6:
                logger.warning(f"密码长度不足: username={register_request.username}")
                raise ValidationError("password", "密码长度至少6位")
            
            # 2. 图形验证码校验
            if not await self._verify_captcha(register_request.captcha_id, register_request.captcha_solution):
                logger.warning(f"注册时图形验证码校验失败: captcha_id={register_request.captcha_id}")
                raise CaptchaErrorException()
            
            # 3. 唯一性检查
            existing_user_by_username = await crud_user.get_by_username(self.db, register_request.username)
            if existing_user_by_username:
                logger.warning(f"用户名已存在: username={register_request.username}")
                raise UsernameAlreadyExistsError(register_request.username)
            
            existing_user_by_email = await crud_user.get_by_email(self.db, register_request.email)
            if existing_user_by_email:
                logger.warning(f"邮箱已存在: email={register_request.email}")
                raise EmailAlreadyExistsError(register_request.email)
            
            # 4. 密码哈希处理
            password_hash = self._hash_password(register_request.password)
            
            # 5. 构建UserCreate对象
            user_create = UserCreate(
                username=register_request.username,
                email=register_request.email,
                nickname=register_request.nickname,
                phone_number=None,  # 第一阶段不处理手机号
                social_provider=None,
                social_id=None
            )
            
            # 6. 创建用户
            new_user = await crud_user.create(self.db, user_create, password_hash)
            
            logger.info(f"用户注册成功: user_id={new_user.id}, username={new_user.username}")
            
            return new_user
            
        except (ValidationError, CaptchaErrorException, UsernameAlreadyExistsError, EmailAlreadyExistsError):
            raise
        except IntegrityError as e:
            logger.warning(f"数据库唯一性约束冲突: username={register_request.username}, email={register_request.email}, error={e}")
            raise UsernameAlreadyExistsError(register_request.username)
        except Exception as e:
            logger.error(f"用户注册失败: error={e}")
            raise
    
    async def update_profile(self, user_to_update: User, update_request: UserUpdateSelf) -> User:
        """
        更新用户个人资料
        
        Args:
            user_to_update: 要更新的用户对象
            update_request: 更新请求
            
        Returns:
            更新后的用户对象
            
        Raises:
            NoUpdateDataProvidedError: 没有提供更新数据
            ValidationError: 参数验证失败
        """
        user_id = user_to_update.id
        logger.info(f"开始处理更新用户信息请求: user_id={user_id}")
        
        try:
            # 验证更新数据
            update_data = update_request.model_dump(exclude_unset=True)
            
            if not update_data:
                logger.warning(f"更新用户信息失败，无有效更新数据: user_id={user_id}")
                raise NoUpdateDataProvidedError()
            
            # 验证昵称长度
            if "nickname" in update_data and len(update_data["nickname"]) > 50:
                logger.warning(f"昵称过长: user_id={user_id}")
                raise ValidationError("nickname", "昵称长度不能超过50个字符")
            
            # 更新用户信息
            updated_user = await crud_user.update(self.db, user_to_update, update_data)
            
            logger.info(f"成功更新用户信息: user_id={updated_user.id}")
            
            return updated_user
            
        except (NoUpdateDataProvidedError, ValidationError):
            raise
        except Exception as e:
            logger.error(f"更新用户信息失败: user_id={user_id}, error={e}")
            raise
    
    async def change_password(self, user: User, password_request) -> None:
        """
        修改用户密码
        
        Args:
            user: 用户对象
            password_request: 密码修改请求
            
        Raises:
            InvalidPasswordError: 当前密码错误
            WeakPasswordError: 新密码强度不足
            ValidationError: 新旧密码相同
        """
        user_id = user.id
        logger.info(f"开始处理用户密码修改请求: user_id={user_id}")
        
        try:
            # 验证当前密码
            if not self._verify_password(password_request.current_password, user.password_hash):
                logger.warning(f"密码修改失败，当前密码错误: user_id={user_id}")
                raise InvalidPasswordError()
            
            # 验证新密码强度
            if not self._validate_password_strength(password_request.new_password):
                logger.warning(f"新密码强度不足: user_id={user_id}")
                raise WeakPasswordError()
            
            # 检查新密码是否与当前密码相同
            if self._verify_password(password_request.new_password, user.password_hash):
                logger.warning(f"新密码与当前密码相同: user_id={user_id}")
                raise ValidationError("new_password", "新密码不能与当前密码相同")
            
            # 更新密码
            new_password_hash = self._hash_password(password_request.new_password)
            await crud_user.update(self.db, user, {"password_hash": new_password_hash})
            
            # 使所有旧令牌失效
            await self._blacklist_user_tokens(user_id)
            
            logger.info(f"用户密码修改成功: user_id={user_id}")
            
        except (InvalidPasswordError, WeakPasswordError, ValidationError):
            raise
        except Exception as e:
            logger.error(f"密码修改失败: user_id={user_id}, error={e}")
            raise
    
    async def deactivate_account(self, user: User) -> None:
        """
        注销用户账户（软删除）
        
        Args:
            user: 用户对象
            
        Raises:
            ActiveSubscriptionError: 存在活跃订阅
        """
        user_id = user.id
        logger.info(f"开始处理用户账户注销请求: user_id={user_id}")
        
        try:
            # 业务检查：检查用户是否有进行中的业务
            # 这里可以检查会员状态、订单状态等
            # 目前是模拟检查，在真实场景中需要调用相关的crud方法检查订阅状态
            
            # 模拟检查活跃订阅（在实际实现中需要查询membership表）
            # has_active_subscription = await self._check_active_subscriptions(user_id)
            # if has_active_subscription:
            #     logger.warning(f"用户存在活跃订阅，无法注销: user_id={user_id}")
            #     raise ActiveSubscriptionError()
            
            # 执行软删除
            deleted_user = await crud_user.remove(self.db, user_id)
            
            # 将用户令牌加入黑名单
            await self._blacklist_user_tokens(user_id)
            
            logger.info(f"用户账户注销成功: user_id={deleted_user.id}")
            
        except ActiveSubscriptionError:
            raise
        except Exception as e:
            logger.error(f"用户账户注销失败: user_id={user_id}, error={e}")
            raise
    
    async def _check_active_subscriptions(self, user_id: int) -> bool:
        """
        检查用户是否有活跃订阅（预留方法）
        
        Args:
            user_id: 用户ID
            
        Returns:
            是否有活跃订阅
        """
        # 预留方法，在实际实现中需要查询用户的会员订阅状态
        # 例如：查询 user_membership 表中是否有状态为 ACTIVE 的记录
        return False 
```
-----


#### **4. 代码生成具体要求 (Specific Code Generation Instructions) - REVISED FOR USERS & AUTH**
##### **4.1. `tests/conftest.py` - 测试设置**
* **指令**:
    1.  你的任务**不包括**生成或修改 `conftest.py`。
    2.  你**必须假设**一个已存在的 `conftest.py` 文件已经提供了 `db_session` (异步数据库会话) 和 `async_client` (异步HTTP客户端) 这两个 fixtures，并且它们可以正常工作。

---
---
#### **4. 代码生成具体要求 (Specific Code Generation Instructions)**

##### **4.1. `tests/conftest.py` - 测试设置**
* **指令**: 你的任务**不包括**生成或修改 `conftest.py`。你**必须假设**它已存在并提供 `db_session` fixture。

##### **4.2. 测试数据隔离 (Test Data Isolation)**
* **指令**: 所有测试用例在准备数据时，**必须**使用 `faker` 或 `uuid` 生成随机且唯一的 `username`, `email` 等字段，以防止测试间冲突。

##### **4.3. `tests/test_services/test_user_service.py` - Service层单元测试**

* **文件名**: `tests/test_services/test_user_service.py`
* **职责**: 对 `app/services/user_service.py` 中的每个公共方法进行详细的、隔离的单元测试。
* **核心要求**: **必须使用 `mocker` fixture** 来模拟所有外部依赖。

* **需实现的测试用例**:

    1.  **`test_register_user_success`**:
        * **准备 (Arrange)**:
            * a. 创建一个 `schemas.UserRegisterRequest` 对象 `register_request`。
            * b. Mock `user_service._verify_captcha` 使其返回 `True`。
            * c. Mock `crud_user.get_by_username` 和 `get_by_email` 都返回 `None`。
            * d. Mock `user_service._hash_password` 返回一个固定的哈希值 `'hashed_password'`。
            * e. Mock `crud_user.create` 方法，这是一个 `AsyncMock` 实例。
        * **执行 (Act)**: 调用 `user_service.register_user(register_request)`。
        * **断言 (Assert)**:
            * a. 断言 `crud_user.create` **被调用了一次**。
            * b. **验证数据库字段**: 检查传递给 `crud_user.create` 的 `user_in` 参数，断言其 `username`, `email`, `nickname` 与请求一致；检查 `password_hash` 参数，断言其值等于 `'hashed_password'`。

    2.  **`test_register_user_fails_if_username_exists`**:
        * **准备 (Arrange)**:
            * a. Mock `user_service._verify_captcha` 返回 `True`。
            * b. Mock `crud_user.get_by_username` 返回一个模拟的 `User` 对象，模拟用户名已存在。
        * **执行与断言 (Act & Assert)**: 使用 `with pytest.raises(UsernameAlreadyExistsError):` 来包裹对 `user_service.register_user()` 的调用。

    3.  **`test_update_profile_success`**:
        * **准备**:
            * a. 创建一个模拟的 `models.User` 对象 `user_to_update`。
            * b. 创建一个 `schemas.UserUpdateSelf` 对象 `update_request`，包含新的 `nickname`。
            * c. Mock `crud_user.update` 方法。
        * **执行**: 调用 `user_service.update_profile(user_to_update, update_request)`。
        * **断言**:
            * a. 断言 `crud_user.update` 被调用了一次。
            * b. 检查传递给 `crud_user.update` 的 `obj_in` 参数，断言它是一个字典，且 `obj_in['nickname']` 的值与 `update_request` 中的新昵称一致。

    4.  **`test_change_password_success`**:
        * **准备**:
            * a. 创建一个模拟 `User` 对象 `mock_user`，其 `password_hash` 为 `'old_hashed_password'`。
            * b. 创建一个 `schemas.PasswordChangeRequest` 对象 `password_request`。
            * c. Mock `user_service._verify_password` 在被以 `'old_password'` 和 `'old_hashed_password'` 调用时返回 `True`。
            * d. Mock `user_service._validate_password_strength` 返回 `True`。
            * e. Mock `user_service._hash_password` 在被以新密码调用时返回 `'new_hashed_password'`。
            * f. Mock `crud_user.update` 方法。
            * g. Mock `user_service._blacklist_user_tokens` 方法。
        * **执行**: 调用 `user_service.change_password(mock_user, password_request)`。
        * **断言**:
            * a. 断言 `crud_user.update` 被调用，且传入的 `obj_in` 字典中 `password_hash` 的值为 `'new_hashed_password'`。
            * b. 断言 `user_service._blacklist_user_tokens` 被以 `mock_user.id` 为参数调用了一次。

    5.  **`test_change_password_fails_if_current_password_is_wrong`**:
        * **准备**: Mock `user_service._verify_password` 使其返回 `False`。
        * **执行与断言**: 使用 `with pytest.raises(InvalidPasswordError):` 来包裹对 `user_service.change_password()` 的调用。

    6.  **`test_deactivate_account_success`**:
        * **准备**: 创建一个模拟 `User` 对象 `mock_user`。Mock `crud_user.remove` 方法。Mock `user_service._blacklist_user_tokens` 方法。
        * **执行**: 调用 `user_service.deactivate_account(mock_user)`。
        * **断言**:
            * a. 断言 `crud_user.remove` 被以 `mock_user.id` 为参数调用了一次。
            * b. 断言 `user_service._blacklist_user_tokens` 被以 `mock_user.id` 为参数调用了一次。

#### **5. 最终交付 (Final Deliverable)**

Please generate the complete, runnable Python code for the following **one new file**:
1.  `tests/test_user_service.py`