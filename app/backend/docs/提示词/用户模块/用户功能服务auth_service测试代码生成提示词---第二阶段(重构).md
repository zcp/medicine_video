

1.  Write **detailed tests** for the stable `crud` layer.
2.  Write **high-level tests** for the `endpoints` layer to verify the API contract and critical business logic, without delving into implementation details that will change.

-----


### **最终版：高效 AI 测试代码生成提示词 (针对重构后的 Auth 模块)**

#### **1. 角色定义 (Role Definition)**

You are a Senior Python Backend Engineer specializing in automated testing. You are an expert in using `pytest` with `pytest-asyncio` and mocking frameworks like `pytest-mock`. Your task is to write a robust test suite for a refactored, service-oriented authentication module.

#### **2. 任务目标 (Task Objective)**

Your goal is to generate the complete code for **one new test files**:

1.  **`tests/test_auth_service.py`**: This file will contain detailed **unit tests** for the new `AuthService` class, focusing on its internal business logic in isolation.

#### **3. 核心上下文信息 (Core Context Information)**

**3.1. Testing Strategy**
* **For `Service` layer (`test_auth_service.py`)**: Test thoroughly using **mocking**. All external dependencies (like `crud` functions, `redis`, `jwt` library) **must be mocked** to test the service logic in complete isolation.

**3.2. Project Structure & Code Context**
*You must generate tests based on the logic within the following application code.*
* **被测试代码 (Code to be Tested)**:
    * `@app/services/auth_service.py` (假设已根据之前的指令生成)
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
│   └── database.py         # <-- 已存在
|___└── tests/
        ├── conftest.py               # <-- has been generated (for test setup)
        ├── test_auth_service.py     # <-- To be generated
```

**3.4. 已存在的代码全文 (Full Text of Existing Code)**

*You must generate tests based on the logic within the following application code.*

* **已存在的代码**:

    * `@app/crud/crud_users.py`
    * `@app/crud/crud_membership_product.py`
    * `@app/crud/crud_user_membership.py`
    * `@app/models/users.py` 
    * `@app/schemas/users.py` 
  
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
#TEST_DATABASE_URL = "postgresql+asyncpg://postgres:CHANGE_ME@localhost:5432/live_core_test"

# 使用环境变量或默认值
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "CHANGE_ME")
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
  * **目标**: 让一个用户能够成功注册和登录，打通最基础的流程，为后续所有功能提供认证基础。
```
"""
认证服务层 - AuthService
封装所有认证相关的业务逻辑，包括验证码、登录、JWT管理等
"""
import uuid
import base64
import hashlib
import logging
import random
import string
import os
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
import jwt

from app.core.redis_client import get_redis_client
from app.crud import crud_user
from app.models.users import EntityStatus
from app import schemas

# 条件导入captcha库
try:
    from captcha.image import ImageCaptcha
    CAPTCHA_AVAILABLE = True
except ImportError:
    CAPTCHA_AVAILABLE = False

logger = logging.getLogger(__name__)


class CaptchaErrorException(Exception):
    """图形验证码错误异常"""
    pass


class RateLimitException(Exception):
    """频率限制异常"""
    pass


class UserAlreadyExistsException(Exception):
    """用户已存在异常"""
    pass


class InvalidCredentialsException(Exception):
    """无效凭证异常"""
    pass


class InvalidTokenException(Exception):
    """无效令牌异常"""
    pass


class InvalidResetTokenException(Exception):
    """无效重置令牌异常"""
    pass


class WeakPasswordException(Exception):
    """密码强度不足异常"""
    pass


class AuthService:
    """认证服务类"""
    
    def __init__(self, db: AsyncSession, redis_client=None):
        """
        初始化认证服务
        
        Args:
            db: 数据库会话
            redis_client: Redis客户端（可选，如果不提供会获取默认客户端）
        """
        self.db = db
        self.redis_client = redis_client or get_redis_client()
        
        # JWT配置
        self.jwt_secret_key = os.getenv("JWT_SECRET_KEY", "your-super-secret-key-here")
        self.jwt_algorithm = "HS256"
    
    # ========================================================================
    # 工具方法
    # ========================================================================
    
    def _generate_captcha_solution(self, length: int = 5) -> str:
        """生成随机验证码答案"""
        chars = string.ascii_letters + string.digits
        return ''.join(random.choice(chars) for _ in range(length))
    
    def _generate_otp(self, length: int = 6) -> str:
        """生成数字OTP验证码"""
        return ''.join(random.choice(string.digits) for _ in range(length))
    
    def _hash_password(self, password: str) -> str:
        """简单的密码哈希（生产环境应使用bcrypt）"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _verify_password(self, password: str, password_hash: str) -> bool:
        """验证密码"""
        return self._hash_password(password) == password_hash
    
    def _mask_recipient(self, recipient: str) -> str:
        """掩码处理收件人信息"""
        if "@" in recipient:  # 邮箱
            local, domain = recipient.split("@", 1)
            if len(local) <= 2:
                masked_local = "*" * len(local)
            else:
                masked_local = local[0] + "*" * (len(local) - 2) + local[-1]
            return f"{masked_local}@{domain}"
        else:  # 手机号
            if len(recipient) <= 4:
                return "*" * len(recipient)
            return recipient[:3] + "*" * (len(recipient) - 6) + recipient[-3:]
    
    def _validate_password_strength(self, password: str) -> bool:
        """验证密码强度"""
        if len(password) < 6:
            return False
        return True
    
    def _create_access_token(self, user_id: int) -> str:
        """创建访问令牌"""
        now = datetime.utcnow()
        payload = {
            "user_id": user_id,
            "type": "access",
            "iat": now,
            "exp": now + timedelta(hours=1),
            "jti": str(uuid.uuid4())  # 添加唯一标识符确保token唯一性
        }
        return jwt.encode(payload, self.jwt_secret_key, algorithm=self.jwt_algorithm)
    
    def _create_refresh_token(self, user_id: int) -> str:
        """创建刷新令牌"""
        now = datetime.utcnow()
        payload = {
            "user_id": user_id,
            "type": "refresh",
            "iat": now,
            "exp": now + timedelta(days=7),
            "jti": str(uuid.uuid4())  # 添加唯一标识符确保token唯一性
        }
        return jwt.encode(payload, self.jwt_secret_key, algorithm=self.jwt_algorithm)
    
    def _verify_token(self, token: str, token_type: str = "access") -> Optional[dict]:
        """验证JWT令牌"""
        try:
            payload = jwt.decode(token, self.jwt_secret_key, algorithms=[self.jwt_algorithm])
            if payload.get("type") != token_type:
                return None
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("JWT令牌已过期")
            return None
        except jwt.InvalidTokenError:
            logger.warning("JWT令牌无效")
            return None
    
    async def _is_token_blacklisted(self, token: str) -> bool:
        """检查令牌是否在黑名单中"""
        try:
            blacklisted = await self.redis_client.get(f"blacklist:token:{token}")
            return blacklisted is not None
        except Exception:
            return False
    
    async def _blacklist_token(self, token: str, expire_time: int = 3600) -> bool:
        """将令牌加入黑名单"""
        try:
            await self.redis_client.set(f"blacklist:token:{token}", "1", ex=expire_time)
            return True
        except Exception:
            return False
    
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
    
    # ========================================================================
    # 主要业务方法
    # ========================================================================
    
    async def generate_captcha(self) -> dict:
        """
        生成图形验证码
        
        Returns:
            包含captcha_id和image_base64的字典
            
        Raises:
            Exception: 当Redis操作失败或图片生成失败时
        """
        logger.info("开始生成图形验证码")
        
        try:
            # 1. 生成唯一ID和随机答案
            captcha_id = str(uuid.uuid4())
            captcha_solution = self._generate_captcha_solution()
            
            logger.info(f"生成验证码: captcha_id={captcha_id}")
            
            # 2. 存储到Redis
            cache_key = f"captcha:solution:{captcha_id}"
            await self.redis_client.set(cache_key, captcha_solution.lower(), ex=180)  # 3分钟过期
            
            # 3. 生成图片
            if CAPTCHA_AVAILABLE:
                image_captcha = ImageCaptcha(width=160, height=60)
                image_data = image_captcha.generate(captcha_solution)
                image_base64 = base64.b64encode(image_data.getvalue()).decode('utf-8')
            else:
                # 如果captcha库不可用，返回模拟数据
                image_base64 = base64.b64encode(b"fake_image_data").decode('utf-8')
                logger.warning("captcha库不可用，返回模拟图片数据")
            
            logger.info(f"成功生成图形验证码: captcha_id={captcha_id}")
            
            return {
                "captcha_id": captcha_id,
                "image_base64": f"data:image/png;base64,{image_base64}"
            }
            
        except Exception as e:
            logger.error(f"生成图形验证码失败: error={e}")
            raise
    
    async def send_otp_code(self, otp_request: schemas.VerificationCodeRequest, client_ip: str = None) -> dict:
        """
        发送OTP验证码
        
        Args:
            otp_request: 验证码发送请求
            client_ip: 客户端IP地址（用于频率限制）
            
        Returns:
            包含发送结果的字典
            
        Raises:
            CaptchaErrorException: 图形验证码错误
            RateLimitException: 请求频率超限
            UserAlreadyExistsException: 注册场景下用户已存在
        """
        logger.info(f"开始处理发送验证码请求: recipient={otp_request.recipient}, scenario={otp_request.scenario}")
        
        try:
            # 1. 图形验证码校验
            if not await self._verify_captcha(otp_request.captcha_id, otp_request.captcha_solution):
                logger.warning(f"图形验证码校验失败: captcha_id={otp_request.captcha_id}")
                raise CaptchaErrorException("图形验证码错误或已过期")
            
            # 2. 频率限制检查
            if client_ip:
                rate_limit_key = f"rate_limit:verification_code:{client_ip}"
                request_count = await self.redis_client.get(rate_limit_key)
                
                if request_count and int(request_count) >= 5:  # 每小时最多5次
                    logger.warning(f"IP请求频率超限: ip={client_ip}")
                    raise RateLimitException("请求过于频繁，请在 60 秒后重试")
            
            # 3. 业务前置检查
            if otp_request.scenario == "REGISTER":
                # 注册场景：检查用户是否已存在
                existing_user = await crud_user.get_by_email(self.db, otp_request.recipient)
                if existing_user:
                    logger.warning(f"注册验证码发送失败，用户已存在: email={otp_request.recipient}")
                    raise UserAlreadyExistsException("该邮箱已被注册")
            elif otp_request.scenario == "RESET_PASSWORD":
                # 重置密码场景：检查用户是否存在（为了安全，不存在也直接返回成功）
                existing_user = await crud_user.get_by_email(self.db, otp_request.recipient)
                if not existing_user:
                    logger.warning(f"重置密码验证码发送失败，用户不存在: email={otp_request.recipient}")
                    # 为了安全，直接返回成功，不抛出异常
                    return {
                        "message": "验证码已发送，请注意查收。",
                        "recipient_masked": self._mask_recipient(otp_request.recipient),
                        "cooldown_seconds": 60
                    }
            
            # 4. 生成和存储OTP
            otp_code = self._generate_otp()
            otp_key = f"otp:{otp_request.scenario}:{otp_request.recipient}"
            await self.redis_client.set(otp_key, otp_code, ex=300)  # 5分钟过期
            
            # 5. 更新频率限制计数
            if client_ip:
                await self.redis_client.incr(rate_limit_key)
                await self.redis_client.expire(rate_limit_key, 3600)  # 1小时过期
            
            # 6. 异步发送（模拟）
            logger.info(f"模拟发送验证码: code={otp_code}, recipient={otp_request.recipient}")
            
            # 掩码处理收件人信息
            recipient_masked = self._mask_recipient(otp_request.recipient)
            
            logger.info(f"成功处理验证码发送请求: recipient={recipient_masked}")
            
            return {
                "message": "验证码已发送，请注意查收。",
                "recipient_masked": recipient_masked,
                "cooldown_seconds": 60
            }
            
        except (CaptchaErrorException, RateLimitException, UserAlreadyExistsException):
            raise
        except Exception as e:
            logger.error(f"发送验证码失败: error={e}")
            raise
    
    async def login_user(self, login_request: schemas.LoginRequest, client_ip: str = None) -> dict:
        """
        用户登录
        
        Args:
            login_request: 登录请求
            client_ip: 客户端IP地址
            
        Returns:
            包含access_token和refresh_token的字典
            
        Raises:
            CaptchaErrorException: 图形验证码错误
            InvalidCredentialsException: 用户名或密码错误
        """
        logger.info(f"开始处理用户登录请求: username={login_request.username}")
        
        try:
            # 1. 图形验证码校验
            if not await self._verify_captcha(login_request.captcha_id, login_request.captcha_solution):
                logger.warning(f"登录时图形验证码校验失败: captcha_id={login_request.captcha_id}")
                raise CaptchaErrorException("图形验证码错误或已过期")
            
            # 2. 用户查询
            user = await crud_user.get_by_username(self.db, login_request.username)
            if not user:
                logger.warning(f"登录失败，用户不存在: username={login_request.username}")
                raise InvalidCredentialsException("用户名或密码错误")
            
            # 提前提取用户属性以防止MissingGreenlet错误
            user_id = user.id
            user_username = user.username
            user_status = user.status
            user_password_hash = user.password_hash
            
            # 3. 状态和密码校验
            if user_status != EntityStatus.NORMAL:
                logger.warning(f"登录失败，用户状态异常: username={login_request.username}, status={user_status}")
                raise InvalidCredentialsException("账户状态异常")
            
            if not self._verify_password(login_request.password, user_password_hash):
                logger.warning(f"登录失败，密码错误: username={login_request.username}")
                raise InvalidCredentialsException("用户名或密码错误")
            
            # 4. 生成Token
            access_token = self._create_access_token(user_id)
            refresh_token = self._create_refresh_token(user_id)
            
            # 5. 更新登录信息
            user.last_login_at = datetime.utcnow()
            if client_ip:
                user.last_login_ip = client_ip
            
            await self.db.commit()
            
            logger.info(f"用户登录成功: user_id={user_id}, username={user_username}")
            
            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer"
            }
            
        except (CaptchaErrorException, InvalidCredentialsException):
            raise
        except Exception as e:
            logger.error(f"用户登录失败: error={e}")
            raise
    
    async def refresh_access_token(self, refresh_token: str) -> dict:
        """
        刷新访问令牌
        
        Args:
            refresh_token: 刷新令牌
            
        Returns:
            包含新access_token的字典
            
        Raises:
            InvalidTokenException: 令牌无效或已过期
        """
        logger.info("开始处理令牌刷新请求")
        
        try:
            # 1. Token验证
            payload = self._verify_token(refresh_token, token_type="refresh")
            if not payload:
                logger.warning("刷新令牌无效或已过期")
                raise InvalidTokenException("凭证无效或已过期")
            
            # 2. 黑名单检查
            if await self._is_token_blacklisted(refresh_token):
                logger.warning("刷新令牌已在黑名单中")
                raise InvalidTokenException("凭证无效或已过期")
            
            # 3. Token生成
            user_id = payload.get("user_id")
            new_access_token = self._create_access_token(user_id)
            
            logger.info(f"成功刷新令牌: user_id={user_id}")
            
            return {
                "access_token": new_access_token,
                "token_type": "bearer"
            }
            
        except InvalidTokenException:
            raise
        except Exception as e:
            logger.error(f"令牌刷新失败: error={e}")
            raise
    
    async def logout_user(self, access_token: str):
        """
        用户登出
        
        Args:
            access_token: 访问令牌
            
        Raises:
            InvalidTokenException: 令牌无效
        """
        logger.info("开始处理用户登出请求")
        
        try:
            # 1. Token验证
            payload = self._verify_token(access_token, token_type="access")
            if not payload:
                logger.warning("访问令牌无效或已过期")
                raise InvalidTokenException("认证凭证格式无效")
            
            # 2. 将access_token加入黑名单
            await self._blacklist_token(access_token, expire_time=3600)
            
            user_id = payload.get("user_id")
            logger.info(f"用户成功登出: user_id={user_id}")
            
        except InvalidTokenException:
            raise
        except Exception as e:
            logger.error(f"用户登出失败: error={e}")
            raise
    
    async def request_password_reset(self, reset_request: schemas.PasswordResetRequest):
        """
        请求密码重置
        
        Args:
            reset_request: 密码重置请求
            
        Raises:
            CaptchaErrorException: 图形验证码错误
        """
        logger.info(f"开始处理密码重置请求: email={reset_request.email}")
        
        try:
            # 1. 图形验证码校验
            if not await self._verify_captcha(reset_request.captcha_id, reset_request.captcha_solution):
                logger.warning(f"图形验证码校验失败: captcha_id={reset_request.captcha_id}")
                raise CaptchaErrorException("图形验证码错误或已过期")
            
            # 2. 用户查询
            user = await crud_user.get_by_email(self.db, reset_request.email)
            
            # 3. 安全处理：如果用户不存在，为了防止邮箱枚举攻击，直接返回
            if not user:
                logger.info(f"密码重置请求的邮箱不存在: email={reset_request.email}")
                return  # 直接返回，不执行任何操作也不抛出异常
            
            # 4. Token生成
            reset_token = secrets.token_urlsafe(32)
            
            # 5. 存入缓存
            reset_key = f"password_reset:{reset_token}"
            await self.redis_client.set(reset_key, str(user.id), ex=900)  # 15分钟过期
            
            # 6. 异步发送邮件（模拟）
            logger.info(f"模拟发送密码重置邮件: email={reset_request.email}, reset_token={reset_token}")
            
            logger.info(f"成功处理密码重置请求: email={reset_request.email}")
            
        except CaptchaErrorException:
            raise
        except Exception as e:
            logger.error(f"密码重置请求失败: error={e}")
            raise
    
    async def perform_password_reset(self, confirm_request: schemas.PasswordResetConfirmRequest):
        """
        执行密码重置
        
        Args:
            confirm_request: 密码重置确认请求
            
        Raises:
            InvalidResetTokenException: 重置令牌无效
            WeakPasswordException: 密码强度不足
        """
        logger.info("开始处理密码重置执行请求")
        
        try:
            # 1. Token验证
            reset_key = f"password_reset:{confirm_request.reset_token}"
            user_id_str = await self.redis_client.get(reset_key)
            
            if not user_id_str:
                logger.warning(f"重置令牌无效或已过期: reset_token={confirm_request.reset_token}")
                raise InvalidResetTokenException("密码重置链接无效或已过期")
            
            # 2. Token销毁：立即删除令牌防止重复使用
            await self.redis_client.delete(reset_key)
            
            # 3. 密码强度验证
            if not self._validate_password_strength(confirm_request.new_password):
                logger.warning("新密码不符合强度要求")
                raise WeakPasswordException("新密码不符合强度要求")
            
            # 4. 数据库更新
            user_id = int(user_id_str)
            user = await crud_user.get(self.db, user_id)
            
            if not user:
                logger.warning(f"重置密码时用户不存在: user_id={user_id}")
                raise InvalidResetTokenException("无效的令牌")
            
            # 5. 密码哈希和更新
            new_password_hash = self._hash_password(confirm_request.new_password)
            update_data = {
                "password_hash": new_password_hash,
                "updated_at": datetime.utcnow()
            }
            
            await crud_user.update(self.db, db_obj=user, obj_in=update_data)
            
            logger.info(f"成功重置用户密码: user_id={user_id}")
            
        except (InvalidResetTokenException, WeakPasswordException):
            raise
        except Exception as e:
            logger.error(f"密码重置失败: error={e}")
            raise 
```
-----


#### **4. 代码生成具体要求 (Specific Code Generation Instructions) - REVISED FOR USERS & AUTH**
##### **4.1. `tests/conftest.py` - 测试设置**
* **指令**:
    1.  你的任务**不包括**生成或修改 `conftest.py`。
    2.  你**必须假设**一个已存在的 `conftest.py` 文件已经提供了 `db_session` (异步数据库会话) 和 `async_client` (异步HTTP客户端) 这两个 fixtures，并且它们可以正常工作。

---

##### **4.2 测试函数生成规范**

**必须严格遵循以下模板生成所有测试函数：**

```python
# CRUD测试模板
@pytest.mark.asyncio
async def test_crud_operation(self, db_session):
    """测试描述"""
    async for db in db_session:
        # 测试逻辑全部在此 async for 块内
        pass

# API测试模板（单fixture）
@pytest.mark.asyncio  
async def test_api_endpoint(self, async_client, mock_redis_captcha_success):
    """API测试描述"""
    async for client in async_client:
        # API测试逻辑全部在此 async for 块内
        pass

# API+数据库测试模板（多fixture）
@pytest.mark.asyncio
async def test_api_with_db(self, async_client, db_session, mock_redis_captcha_success):
    """API和数据库组合测试"""
    async for client in async_client:
        async for db in db_session:
            # 组合测试逻辑全部在此嵌套 async for 块内
            pass
```

**⚠️ 禁止的写法：**
- 不得在 async for 外部调用数据库操作
- 不得直接使用 fixture 参数而不解包
- 不得在函数参数中添加类型提示（会导致混淆）
- 

**Example of a Test Helper Function (Working Example):**
```
@pytest.mark.asyncio
async def test_retry_mp4_task_exceeds_max_retry_count(async_client, db_session):
        """
        Test retrying MP4 task that already exceeded max retry count.
        - Create a FAILED MP4 task with retry_count=3
        - Call retry API
        - Assert 400 response and error message
        """
        async for client in async_client:
            async for db in db_session:
                task = await task_pending_basic_for_invalid_mp4_url_retry(db)

                task.retry_count = 3
                await db.commit()

                response = await client.post(f"/api/v1/download/tasks/{task.id}/retry")
                assert response.status_code == 400
                assert "重试次数已达上限" in response.text or "Retry limit exceeded" in response.text
```
##### **4.3. `tests/test_services/test_auth_service.py` - Service层单元测试 (新文件)**

* **文件名**: `tests/test_services/test_auth_service.py`
* **职责**: 对 `app/services/auth_service.py` 中的每个公共方法进行详细的、隔离的单元测试。
* **核心要求**: **必须使用 `mocker` fixture** 来模拟所有外部依赖（`crud`函数、`redis_client`、`jwt.encode/decode`等）。**不允许**进行真实的数据库或Redis调用。



* **需实现的测试用例**:

    1.  **`test_login_user_success`**:
        * **准备 (Arrange)**:
            * a. 创建一个 `status` 为 `NORMAL` 的模拟 `models.User` 对象 `mock_user`。
            * b. Mock `crud_user.get_by_username` 使其返回 `mock_user`。
            * c. Mock `verify_password` 使其返回 `True`。
            * d. Mock `create_access_token` 和 `create_refresh_token` 分别返回固定的测试Token字符串。
        * **执行 (Act)**: 调用 `auth_service.login_user()`。
        * **断言 (Assert)**:
            * a. 断言返回的字典中包含了正确的 `access_token` 和 `refresh_token`。
            * b. 断言 `db.commit()` 被调用了一次。
            * c. 断言 `db.refresh()` 被以 `mock_user` 为参数调用了一次。

    2.  **`test_login_user_fails_if_user_not_found`**:
        * **准备 (Arrange)**: Mock `crud_user.get_by_username` 使其返回 `None`。
        * **执行与断言 (Act & Assert)**: 使用 `with pytest.raises(InvalidCredentialsException):` 来包裹对 `auth_service.login_user()` 的调用，并断言异常消息为 "用户名或密码错误"。

    3.  **`test_login_user_fails_if_password_is_wrong`**:
        * **准备**: Mock `crud_user.get_by_username` 返回一个模拟用户，但 Mock `verify_password` 使其返回 `False`。
        * **执行与断言**: 使用 `with pytest.raises(InvalidCredentialsException):` 来断言抛出了正确的异常。

    4.  **`test_login_user_fails_if_user_is_banned`**:
        * **准备**: Mock `crud_user.get_by_username` 返回一个 `status` 为 `BANNED` 的用户。Mock `verify_password` 返回 `True`。
        * **执行与断言**: 使用 `with pytest.raises(InactiveUserException):` 来断言抛出了正确的异常。

    5.  **为 `send_otp_code` 编写测试**:
        * **`..._success_for_register`**:
            * **准备**: Mock `crud_user.get_by_email` 返回 `None`。Mock `self.verify_captcha` 返回 `None` (无异常)。Mock Redis `set` 命令。
            * **执行**: 调用 `auth_service.send_otp_code()` 并传入 `scenario='REGISTER'`。
            * **断言**: 断言 Redis 的 `set` 命令被以正确的键（包含`REGISTER`和`recipient`）和正确的过期时间（300秒）调用了一次。
        * **`..._fails_if_email_exists_for_register`**:
            * **准备**: Mock `crud_user.get_by_email` 返回一个模拟用户。Mock `self.verify_captcha` 成功。
            * **执行与断言**: 使用 `with pytest.raises(UserAlreadyExistsException):` 来包裹对 `auth_service.send_otp_code()` 的调用。

    6.  **为 `refresh_access_token` 编写测试**:
        * **`..._success`**:
            * **准备**: Mock `verify_token` 返回一个有效的 payload。Mock `is_token_blacklisted` 返回 `False`。Mock `create_access_token` 返回 `'new_access_token'`。
            * **执行**: 调用 `auth_service.refresh_access_token()`。
            * **断言**: 断言返回的字典中 `access_token` 的值是 `'new_access_token'`。
        * **`..._fails_if_token_is_blacklisted`**:
            * **准备**: Mock `verify_token` 返回有效 payload，但 Mock `is_token_blacklisted` 返回 `True`。
            * **执行与断言**: 使用 `with pytest.raises(InvalidTokenException):` 来包裹调用。


### **为 `request_password_reset` 和 `perform_password_reset` 编写的测试指令**

* **文件名**: `tests/test_services/test_auth_service.py`
* **职责**: 对 `app/services/auth_service.py` 中的密码重置相关方法进行详细的、隔离的单元测试。
* **核心要求**: **必须使用 `mocker` fixture** 来模拟所有外部依赖（`crud`函数、`redis_client`、内部辅助方法等）。

* **需实现的测试用例**:

    1.  **`test_request_password_reset_success`**:
        * **准备 (Arrange)**:
            * a. 创建一个模拟的 `schemas.PasswordResetRequest` 对象 `reset_request`。
            * b. 创建一个模拟的 `models.User` 对象 `mock_user`，并为其设置一个 `id`。
            * c. Mock `auth_service._verify_captcha` 使其返回 `True`，表示验证码校验通过。
            * d. Mock `crud_user.get_by_email` 使其返回 `mock_user`。
            * e. Mock `secrets.token_urlsafe` 使其返回一个固定的测试令牌 `'test_reset_token'`。
            * f. Mock `redis_client.set` 方法，这是一个 `AsyncMock` 实例。
        * **执行 (Act)**: 调用 `auth_service.request_password_reset(reset_request)`。
        * **断言 (Assert)**:
            * a. 断言 `crud_user.get_by_email` 被以正确的 `email` 参数调用了一次。
            * b. 断言 `redis_client.set` **被调用了一次**。
            * c. 验证 `redis_client.set` 被调用时的参数：键应为 `f"password_reset:test_reset_token"`，值应为 `str(mock_user.id)`，过期时间 `ex` 应为 `900` (15分钟)。

    2.  **`test_request_password_reset_does_nothing_if_user_not_found`**:
        * **准备 (Arrange)**:
            * a. Mock `auth_service._verify_captcha` 使其返回 `True`。
            * b. Mock `crud_user.get_by_email` 使其返回 `None`，模拟用户不存在的场景。
            * c. Mock `redis_client.set` 方法。
        * **执行 (Act)**: 调用 `auth_service.request_password_reset()`。
        * **断言 (Assert)**:
            * a. 断言 `crud_user.get_by_email` 被调用了一次。
            * b. 断言 `redis_client.set` **从未被调用** (`assert_not_called()`)，以确保在用户不存在时不会执行任何后续操作。

    3.  **`test_perform_password_reset_success`**:
        * **准备 (Arrange)**:
            * a. 创建一个 `schemas.PasswordResetConfirmRequest` 对象 `confirm_request`，包含 `'test_reset_token'` 和 `'new_strong_password'`。
            * b. 创建一个模拟用户 `mock_user`。
            * c. Mock `redis_client.get` 使其在被以 `'password_reset:test_reset_token'` 为键调用时，返回 `str(mock_user.id)`。
            * d. Mock `redis_client.delete` 方法。
            * e. Mock `auth_service._validate_password_strength` 使其返回 `True`。
            * f. Mock `auth_service._hash_password` 使其返回一个固定的哈希值 `'new_hashed_password'`。
            * g. Mock `crud_user.get` 使其返回 `mock_user`。
            * h. Mock `crud_user.update` 方法。
        * **执行 (Act)**: 调用 `auth_service.perform_password_reset(confirm_request)`。
        * **断言 (Assert)**:
            * a. 断言 `redis_client.delete` 被以正确的键 `'password_reset:test_reset_token'` 调用了一次，确保令牌被销毁。
            * b. 断言 `crud_user.update` 被调用了一次。
            * c. **验证数据库字段变更**: 检查传递给 `crud_user.update` 的 `obj_in` 参数，断言它是一个字典，且 `obj_in['password_hash']` 的值**等于** `'new_hashed_password'`。

    4.  **`test_perform_password_reset_fails_if_token_is_invalid`**:
        * **准备 (Arrange)**: Mock `redis_client.get` 使其返回 `None`，模拟令牌无效或已过期的场景。
        * **执行与断言 (Act & Assert)**: 使用 `with pytest.raises(InvalidResetTokenException):` 来包裹对 `auth_service.perform_password_reset()` 的调用，并可以断言异常消息。

    5.  **`test_perform_password_reset_fails_if_password_is_weak`**:
        * **准备**: Mock `redis_client.get` 返回一个有效的 `user_id`，但 Mock `auth_service._validate_password_strength` 使其返回 `False`。
        * **执行与断言**: 使用 `with pytest.raises(WeakPasswordException):` 来包裹对 `auth_service.perform_password_reset()` 的调用。

    6.  **`test_generate_captcha_success`**:
        * **准备 (Arrange)**:
            * a. 创建 `AuthService` 的一个实例 `auth_service`，并为其注入一个 `AsyncMock` 作为 `redis_client`。
            * b. Mock `uuid.uuid4` 使其返回一个固定的、可预测的 UUID 对象，例如 `mocker.patch('uuid.uuid4', return_value=mock_uuid)`。
            * c. Mock `auth_service._generate_captcha_solution` 方法，使其返回一个固定的答案，例如 `'test'`。
            * d. Mock `ImageCaptcha` 库的行为，使其 `generate` 方法返回一个模拟的图片数据对象。
            * e. Mock `base64.b64encode` 使其返回一个固定的 Base64 编码字符串，例如 `b'dGVzdF9pbWFnZQ=='`。
        * **执行 (Act)**: 调用 `await auth_service.generate_captcha()`。
        * **断言 (Assert)**:
            * a. 断言 `auth_service.redis_client.set` **被调用了一次** (`assert_called_once()`)。
            * b. 验证 `redis_client.set` 被调用时的参数：
                * `key` 应为 `f"captcha:solution:{mock_uuid}"`。
                * `value` 应为 `'test'` (小写)。
                * 过期时间 `ex` 应为 `180`。
            * c. 断言返回的字典中 `captcha_id` 字段的值等于 `str(mock_uuid)`。
            * d. 断言返回的字典中 `image_base64` 字段的值等于 `'data:image/png;base64,dGVzdF9pbWFnZQ=='`。

    7.  **`test_generate_captcha_handles_redis_exception`**:
        * **准备 (Arrange)**:
            * a. 创建 `AuthService` 实例。
            * b. Mock `auth_service.redis_client.set` 方法，使其在被调用时**主动抛出**一个 `RedisError` 异常：`mocker.patch.object(auth_service.redis_client, 'set', side_effect=redis.exceptions.RedisError)`。
        * **执行与断言 (Act & Assert)**:
            * a. 使用 `with pytest.raises(Exception):` 来包裹对 `auth_service.generate_captcha()` 的调用，断言该方法会将底层异常继续向外抛出，而不是吞没它。

    8. test_logout_user_success (已补充):
       * **准备**: Mock auth_service._verify_token 返回一个包含 exp (过期时间) 的有效 payload。Mock auth_service._blacklist_token 方法。
       * **执行**: 调用 auth_service.logout_user()。
       * **断言**: 断言 auth_service._blacklist_token 被以正确的 token 和计算出的剩余秒数作为参数调用了一次。