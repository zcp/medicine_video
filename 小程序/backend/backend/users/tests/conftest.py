"""
Users Service - Test Configuration

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
from unittest.mock import AsyncMock, patch
from dotenv import load_dotenv

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 在导入app模块之前，加载环境变量文件
# 优先加载 .env，如果不存在则加载 .env.example
# 注意：不覆盖已存在的环境变量，只加载缺失的
env_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
env_example_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env.example')

if os.path.exists(env_file):
    load_dotenv(dotenv_path=env_file, override=False)  # 不覆盖已存在的环境变量
elif os.path.exists(env_example_file):
    load_dotenv(dotenv_path=env_example_file, override=False)  # 不覆盖已存在的环境变量

# 如果环境变量仍未设置，使用测试默认值（仅作为后备）
if not os.getenv("JWT_SECRET_KEY"):
    os.environ["JWT_SECRET_KEY"] = "test-jwt-secret-key-for-testing-only"
if not os.getenv("POSTGRES_PASSWORD"):
    os.environ["POSTGRES_PASSWORD"] = ""

from app.database import Base, get_async_db
from app.models.users import User, MembershipProduct, UserMembership

# 使用环境变量或默认值（保持与之前测试通过的配置一致）
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "324zq999")
POSTGRES_SERVER = os.getenv("POSTGRES_SERVER", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "users_service_test")  # 恢复为之前的默认值

# 异步连接字符串（用于测试）
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
    # 创建测试专用的FastAPI应用
    from fastapi import FastAPI
    from app.api.v1.endpoints.auth import router as auth_router
    from app.api.v1.endpoints.users import router as users_router
    from app.api.v1.endpoints.membership_products import router as membership_products_router
    
    # 导入admin路由
    from app.api.v1.admin.users import router as admin_users_router
    from app.api.v1.admin.products import router as admin_products_router
    from app.api.v1.admin.subscriptions import router as admin_subscriptions_router
    
    # 创建测试专用的FastAPI应用
    app = FastAPI(
        title="Users Service Test", 
        version="1.0.0",
        redirect_slashes=False  # 禁用自动重定向，避免307问题
    )
    
    # 添加普通用户路由
    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(users_router, prefix="/api/v1")
    app.include_router(membership_products_router, prefix="/api/v1")
    
    # 添加admin管理路由
    app.include_router(admin_users_router, prefix="/api/v1/admin")
    app.include_router(admin_products_router, prefix="/api/v1/admin")
    app.include_router(admin_subscriptions_router, prefix="/api/v1/admin")
    
    # 添加第四批次订阅路由
    try:
        from app.api.v1.endpoints.subscriptions import router as subscriptions_router
        app.include_router(subscriptions_router, prefix="/api/v1")
    except ImportError:
        pass  # 如果路由不存在则跳过
    
    # 覆盖数据库依赖，使用测试数据库
    async def override_get_async_db():
        async with async_session_factory() as session:
            yield session
    
    app.dependency_overrides[get_async_db] = override_get_async_db
    
    # 使用测试服务器 - 独立应用，不依赖外部服务
    async with AsyncClient(app=app, base_url="http://localhost:8000") as client:
        yield client


@pytest.fixture
def mock_redis():
    """模拟Redis客户端"""
    with patch('app.core.redis_client.get_redis_client') as mock_get_redis:
        # 创建一个模拟的Redis客户端
        mock_redis_client = AsyncMock()
        
        # 设置默认行为
        mock_redis_client.get.return_value = None
        mock_redis_client.set.return_value = True
        mock_redis_client.delete.return_value = True
        mock_redis_client.incr.return_value = 1
        mock_redis_client.expire.return_value = True
        
        mock_get_redis.return_value = mock_redis_client
        yield mock_redis_client


@pytest.fixture
def mock_redis_captcha_success():
    """模拟Redis客户端，使验证码校验总是成功"""
    # 🔥 使用autouse=True强制激活，多路径patch确保命中
    with patch('app.core.redis_client.get_redis_client') as mock1, \
         patch('app.services.auth_service.get_redis_client') as mock2:
        mock_redis_client = AsyncMock()
        
        # 🔥 强制所有验证码键都返回正确答案
        async def mock_get(key):
            print(f"[MOCK DEBUG] Redis.get called with key: {key}")  # 调试输出
            if "captcha:solution:" in str(key):
                print(f"[MOCK DEBUG] Returning test123 for captcha key")
                return "test123"
            elif "rate_limit:" in str(key):
                return None
            else:
                return None
        
        mock_redis_client.get.side_effect = mock_get
        mock_redis_client.set.return_value = True
        mock_redis_client.delete.return_value = True
        mock_redis_client.incr.return_value = 1
        mock_redis_client.expire.return_value = True
        
        # 🔥 同时设置两个路径的mock
        mock1.return_value = mock_redis_client
        mock2.return_value = mock_redis_client
        
        yield mock_redis_client


@pytest.fixture
def mock_redis_with_blacklist():
    """模拟Redis客户端，支持验证码校验和token黑名单功能"""
    with patch('app.core.redis_client.get_redis_client') as mock1, \
         patch('app.services.auth_service.get_redis_client') as mock2, \
         patch('app.api.v1.deps.get_redis_client') as mock3:
        
        mock_redis_client = AsyncMock()
        
        # 模拟一个内存存储来跟踪token黑名单
        blacklist_storage = {}
        
        # 根据不同key返回不同值
        async def mock_get(key):
            if "captcha:solution:" in str(key):
                return "test123"  # 验证码键返回验证码答案
            elif "rate_limit:" in str(key):
                return None  # 频率限制键返回None
            elif "blacklist:token:" in str(key):
                return blacklist_storage.get(key)  # ✅ 从内存存储获取黑名单状态
            else:
                return None
        
        async def mock_set(key, value, ex=None):
            if "blacklist:token:" in str(key):
                blacklist_storage[key] = value  # ✅ 保存到内存存储
            return True
        
        async def mock_delete(key):
            if "blacklist:token:" in str(key):
                blacklist_storage.pop(key, None)  # ✅ 从内存存储删除
            return True
        
        mock_redis_client.get.side_effect = mock_get
        mock_redis_client.set.side_effect = mock_set
        mock_redis_client.delete.side_effect = mock_delete
        mock_redis_client.incr.return_value = 1
        mock_redis_client.expire.return_value = True
        
        # 🔥 同时设置三个路径的mock（包括deps.py）
        mock1.return_value = mock_redis_client
        mock2.return_value = mock_redis_client
        mock3.return_value = mock_redis_client
        
        yield mock_redis_client


@pytest.fixture
def mock_redis_password_reset():
    """模拟Redis客户端，支持验证码校验和密码重置token追踪"""
    with patch('app.core.redis_client.get_redis_client') as mock1, \
         patch('app.services.auth_service.get_redis_client') as mock2, \
         patch(
             'app.services.email_provider.SmtpEmailProvider.send_password_reset',
             new_callable=AsyncMock,
             return_value=True,
         ), \
         patch(
             'app.services.email_provider.MockEmailProvider.send_password_reset',
             new_callable=AsyncMock,
             return_value=True,
         ):
        
        mock_redis_client = AsyncMock()
        
        # 存储reset token的内存字典
        reset_token_storage = {}
        
        async def mock_get(key):
            if "captcha:solution:" in str(key):
                return "test123"  # 验证码键返回验证码答案
            elif "rate_limit:" in str(key):
                return None  # 频率限制键返回None
            elif "password_reset:" in str(key):
                return reset_token_storage.get(key)  # 返回存储的用户ID
            else:
                return None
        
        async def mock_set(key, value, ex=None):
            if "password_reset:" in str(key):
                reset_token_storage[key] = value  # 存储token对应的用户ID
            return True
        
        async def mock_delete(key):
            if "password_reset:" in str(key):
                reset_token_storage.pop(key, None)  # 删除token
            return True
        
        mock_redis_client.get.side_effect = mock_get
        mock_redis_client.set.side_effect = mock_set
        mock_redis_client.delete.side_effect = mock_delete
        mock_redis_client.incr.return_value = 1
        mock_redis_client.expire.return_value = True
        
        # 同时设置两个路径的mock
        mock1.return_value = mock_redis_client
        mock2.return_value = mock_redis_client
        
        # 提供一个方法来获取生成的token
        mock_redis_client._reset_tokens = reset_token_storage
        
        yield mock_redis_client


@pytest.fixture
async def real_redis_client():
    """提供真实Redis连接用于集成测试"""
    from app.core.redis_client import get_redis_client, test_redis_connection
    import logging
    
    logger = logging.getLogger(__name__)
    
    # 测试Redis连接是否可用
    is_connected = await test_redis_connection()
    if not is_connected:
        pytest.skip("Redis服务不可用，跳过集成测试")
    
    redis_client = get_redis_client()
    
    yield redis_client
    
    # 清理测试数据
    try:
        # 删除所有测试相关的键
        test_patterns = [
            "captcha:solution:test-*",
            "captcha:solution:cleanup-*", 
            "otp:*test*",
            "otp:*example.com*",
            "rate_limit:*127.0.0.1*"
        ]
        
        for pattern in test_patterns:
            test_keys = await redis_client.keys(pattern)
            if test_keys:
                await redis_client.delete(*test_keys)
                
        await redis_client.aclose()
        logger.info("Redis测试数据清理完成")
    except Exception as e:
        logger.warning(f"Redis清理失败: {e}")


# ============================================================================
# 测试工具函数
# ============================================================================

async def create_test_user(db: AsyncSession, username: str = "testuser", email: str = "test@example.com") -> User:
    """创建测试用户的辅助函数"""
    import hashlib
    from app.models.users import User, UserRole, EntityStatus
    
    password_hash = hashlib.sha256("testpassword123".encode()).hexdigest()
    
    user = User(
        username=username,
        email=email,
        nickname=f"{username}_nick",
        password_hash=password_hash,
        role=UserRole.REGULAR,
        status=EntityStatus.NORMAL,
        is_email_verified=False,
        is_phone_verified=False
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


def create_captcha_mock_data() -> dict:
    """创建模拟验证码数据"""
    return {
        "captcha_id": "test-captcha-id-12345",
        "captcha_solution": "test123"  # ✅ 匹配mock_redis返回值
    }


@pytest.fixture
async def authenticated_user(db_session):
    """提供已认证的用户和mock token"""
    async for db in db_session:
        # 创建测试用户
        user = await create_test_user(db, username="auth_test_user", email="auth_test@example.com")

        # 生成一个mock token
        mock_token = "test_jwt_token_for_api_testing"

        yield user, mock_token  # 改为 yield
        break  # 确保只执行一次