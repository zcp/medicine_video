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

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import Base, get_async_db
from app.models.users import User, MembershipProduct, UserMembership

# 使用环境变量或默认值
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "CHANGE_ME")
POSTGRES_SERVER = os.getenv("POSTGRES_SERVER", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "users_service_test")

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

    # 创建测试专用的FastAPI应用
    app = FastAPI(
        title="Users Service Test",
        version="1.0.0",
        redirect_slashes=False  # 禁用自动重定向，避免307问题
    )

    # 添加路由
    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(users_router, prefix="/api/v1")

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
    with patch('app.core.redis_client.get_redis_client') as mock_get_redis:
        mock_redis_client = AsyncMock()

        # 使用side_effect根据不同key返回不同值
        async def mock_get(key):
            if key.startswith("captcha:solution:"):
                return "test123"  # 验证码键返回验证码答案
            elif key.startswith("rate_limit:"):
                return None  # 频率限制键返回None（表示没有限制记录）
            elif key.startswith("blacklist:token:"):
                return None  # 黑名单键返回None
            else:
                return None

        mock_redis_client.get.side_effect = mock_get
        mock_redis_client.set.return_value = True
        mock_redis_client.delete.return_value = True
        mock_redis_client.incr.return_value = 1
        mock_redis_client.expire.return_value = True

        mock_get_redis.return_value = mock_redis_client
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
    import bcrypt
    from app.models.users import User, UserRole, EntityStatus

    password_hash = bcrypt.hashpw("testpassword123".encode(), bcrypt.gensalt()).decode()

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