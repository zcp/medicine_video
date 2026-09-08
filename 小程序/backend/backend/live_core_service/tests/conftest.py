"""
LiveCore Service - Test Configuration

This module contains pytest fixtures and configuration for testing.
"""

import os
import sys
import uuid
from pathlib import Path

import pytest
import asyncio
from typing import AsyncGenerator, Generator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient
from uuid import uuid4
from dotenv import load_dotenv

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 在导入 app.database 之前先加载 .env.example 文件
# 测试环境应该使用模板文件，确保JWT密钥一致
# 这样 app.database 模块级别的数据库连接测试才能正确读取配置
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_example_path = os.path.join(base_dir, '.env.example')
load_dotenv(dotenv_path=env_example_path)

from app.database import Base, get_db
from app.models.live_core import LiveRoom, LiveSession, SessionStatistics
import app.models.content_management  # noqa: F401 - register tables
import app.models.liveroom_official_accounts  # noqa: F401 - register tables
import app.content_safety.models  # noqa: F401 - register content_safety_* tables
import app.models.brand  # noqa: F401
import app.models.topic  # noqa: F401
import app.models.experts  # noqa: F401
import app.models.live_features  # noqa: F401
import app.models.homepage_search  # noqa: F401
import app.models.user_behavior  # noqa: F401
import app.models.user_preference_notification  # noqa: F401



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
    """设置测试数据库（仅连接 POSTGRES_DB；请勿对现网库跑 pytest）"""
    # 确保所有使用 Base 的模型在 create_all 前已注册
    import app.models.content_management  # noqa: F401
    import app.models.liveroom_official_accounts  # noqa: F401
    import app.content_safety.models  # noqa: F401
    import app.models.brand  # noqa: F401
    import app.models.topic  # noqa: F401
    import app.models.experts  # noqa: F401
    import app.models.live_features  # noqa: F401
    import app.models.homepage_search  # noqa: F401
    import app.models.user_behavior  # noqa: F401
    import app.models.user_preference_notification  # noqa: F401

    # 安全闸：禁止对 compose 现网库做 drop_all
    if POSTGRES_DB in {"live_core_test", "live_core"} and os.getenv("ALLOW_DROP_LIVE_CORE_TEST") != "1":
        raise RuntimeError(
            f"拒绝在数据库 {POSTGRES_DB} 上执行测试 drop_all。"
            "请使用独立库，例如: POSTGRES_DB=live_core_pytest"
        )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                public_id UUID PRIMARY KEY,
                username VARCHAR(255),
                email VARCHAR(255),
                nickname VARCHAR(255),
                password_hash VARCHAR(255),
                role VARCHAR(50),
                status VARCHAR(50),
                is_email_verified BOOLEAN DEFAULT FALSE,
                is_phone_verified BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))

        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()

@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """提供数据库会话"""
    async with async_session_factory() as session:
        yield session
        if session is not None:
            try:
                await session.rollback()
            except Exception:
                pass


@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    # 加载 .env.example，但保留已有 JWT（Docker/.env.docker），避免 Token 与 settings 验签密钥不一致
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env_example_path = os.path.join(base_dir, '.env.example')
    saved_jwt = os.environ.get("JWT_SECRET_KEY")
    load_dotenv(dotenv_path=env_example_path, override=True)
    if saved_jwt:
        os.environ["JWT_SECRET_KEY"] = saved_jwt
    else:
        # 与 app.core.config.settings 默认开发密钥对齐
        from app.core.config import settings
        if settings.JWT_SECRET_KEY:
            os.environ["JWT_SECRET_KEY"] = settings.JWT_SECRET_KEY

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

    # 使用测试服务器 - httpx 0.25+ 使用 transport=ASGITransport(app=app)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://localhost:8000") as client:
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


# 在 backend/live_core_service/tests/conftest.py 中

import os
import sys
import pytest
import asyncio
from typing import AsyncGenerator, Generator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# 添加项目根目录到 Python 路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

# 导入users服务的模型
from backend.users.app.models.users import User, UserRole, EntityStatus
from backend.users.app.database import Base as UsersBase

# 使用与users服务相同的测试数据库
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "324zq999")
POSTGRES_SERVER = os.getenv("POSTGRES_SERVER", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "user_service_test")  # 改为user_service_test
POSTGRES_DB = os.getenv("POSTGRES_DB", "live_core_test")  # 改为user_service_test

# 异步连接字符串
TEST_DATABASE_URL = f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_SERVER}:{POSTGRES_PORT}/{POSTGRES_DB}"

# 创建测试数据库引擎
engine = create_async_engine(TEST_DATABASE_URL, echo=True)

# 创建异步会话工厂
async_session_factory = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

"""
@pytest.fixture(scope="session", autouse=True)
async def setup_database():
    async with engine.begin() as conn:
        # 先创建users表（使用真实的User模型）
        await conn.run_sync(UsersBase.metadata.create_all)

        # 再创建live_core表
        from app.models.live_core import Base as LiveCoreBase
        await conn.run_sync(LiveCoreBase.metadata.create_all)

        # 创建 app.database.Base 下的表（content_management、liveroom_official_accounts 等）
        import app.models.content_management  # noqa: F401
        import app.models.liveroom_official_accounts  # noqa: F401
        from app.database import Base as AppBase
        await conn.run_sync(AppBase.metadata.create_all)
    yield
    await engine.dispose()


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session
        if session is not None:
            try:
                await session.rollback()
            except Exception:
                pass
"""

async def create_test_user(db: AsyncSession, username: str = "testuser", email: str = "test@example.com") -> User:
    """创建测试用户的辅助函数"""
    import hashlib

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


@pytest.fixture
async def test_user(db_session):
    """提供测试用户"""
    async for db in db_session:
        user = await create_test_user(db, username="live_test_user", email="live_test@example.com")
        yield user
        break

# ==================== JWT 认证 Mock 配置 ====================
import time
import jwt

@pytest.fixture
def test_user_id():
    """提供测试用的用户ID"""
    return uuid4()

@pytest.fixture
def mock_current_user(test_user_id):
    """模拟当前认证用户"""
    return {
        "user_id": str(test_user_id),
        "sub": str(test_user_id),
        "email": "test@example.com",
        "exp": int(time.time()) + 3600  # 1小时后过期
    }

@pytest.fixture
def mock_jwt_token(mock_current_user):
    """生成模拟的JWT token"""
    # 使用环境变量中的JWT_SECRET_KEY，如果没有则使用测试密钥
    secret_key = os.getenv("JWT_SECRET_KEY", "my-key")
    algorithm = os.getenv("JWT_ALGORITHM", "HS256")

    token = jwt.encode(mock_current_user, secret_key, algorithm=algorithm)
    return token

@pytest.fixture
def auth_headers(mock_jwt_token):
    """提供认证头"""
    return {"Authorization": f"Bearer {mock_jwt_token}"}

# ==================== 权限测试 Fixture（权限管理增量改造）====================

@pytest.fixture
def regular_user_id() -> uuid.UUID:
    """普通用户ID（用于权限测试）"""
    return uuid4()

@pytest.fixture
def admin_user_id() -> uuid.UUID:
    """管理员用户ID（用于权限测试）"""
    return uuid4()

@pytest.fixture
def another_user_id() -> uuid.UUID:
    """另一个用户ID（用于测试非Owner场景）"""
    return uuid4()

@pytest.fixture
def regular_user_role() -> str:
    """普通用户角色（设计文档定义：REGULAR，非 USER）"""
    return "REGULAR"

@pytest.fixture
def admin_user_role() -> str:
    """管理员角色"""
    return "ADMIN"  # Service层期望小写

@pytest.fixture
def regular_user_token(regular_user_id: uuid.UUID, regular_user_role: str) -> str:
    """生成普通用户的JWT Token（用于权限测试）"""
    from app.core.config import settings
    secret_key = settings.JWT_SECRET_KEY or os.getenv("JWT_SECRET_KEY") or "my-key"
    algorithm = settings.JWT_ALGORITHM or os.getenv("JWT_ALGORITHM", "HS256")
    token_data = {
        "user_id": str(regular_user_id),
        "role": regular_user_role,
        "sub": str(regular_user_id),
        "email": "regular@example.com",
        "exp": int(time.time()) + 3600
    }
    return jwt.encode(token_data, secret_key, algorithm=algorithm)

@pytest.fixture
def admin_user_token(admin_user_id: uuid.UUID, admin_user_role: str) -> str:
    """生成管理员的JWT Token（用于权限测试）"""
    from app.core.config import settings
    secret_key = settings.JWT_SECRET_KEY or os.getenv("JWT_SECRET_KEY") or "my-key"
    algorithm = settings.JWT_ALGORITHM or os.getenv("JWT_ALGORITHM", "HS256")
    token_data = {
        "user_id": str(admin_user_id),
        "role": admin_user_role,
        "sub": str(admin_user_id),
        "email": "admin@example.com",
        "exp": int(time.time()) + 3600
    }
    return jwt.encode(token_data, secret_key, algorithm=algorithm)

@pytest.fixture
def another_user_token(another_user_id: uuid.UUID) -> str:
    """生成另一个用户的JWT Token（用于测试非Owner场景）"""
    from app.core.config import settings
    secret_key = settings.JWT_SECRET_KEY or os.getenv("JWT_SECRET_KEY") or "my-key"
    algorithm = settings.JWT_ALGORITHM or os.getenv("JWT_ALGORITHM", "HS256")
    token_data = {
        "user_id": str(another_user_id),
        "role": "REGULAR",
        "sub": str(another_user_id),
        "email": "another@example.com",
        "exp": int(time.time()) + 3600
    }
    return jwt.encode(token_data, secret_key, algorithm=algorithm)

@pytest.fixture
def invalid_token() -> str:
    """无效的JWT Token（用于测试401场景）"""
    return "invalid.token.here"

@pytest.fixture
def expired_token(regular_user_id: uuid.UUID, regular_user_role: str) -> str:
    """过期的JWT Token（用于测试401场景）"""
    from app.core.config import settings
    secret_key = settings.JWT_SECRET_KEY or os.getenv("JWT_SECRET_KEY") or "my-key"
    algorithm = settings.JWT_ALGORITHM or os.getenv("JWT_ALGORITHM", "HS256")
    token_data = {
        "user_id": str(regular_user_id),
        "role": regular_user_role,
        "sub": str(regular_user_id),
        "email": "regular@example.com",
        "exp": int(time.time()) - 3600  # ← 已过期（1小时前）
    }
    return jwt.encode(token_data, secret_key, algorithm=algorithm)

# ==================== 测试资源 Fixture（权限管理增量改造）====================

@pytest.fixture
async def public_room(db_session, regular_user_id: uuid.UUID):
    """创建Public房间（用于权限测试）"""
    async for db in db_session:
        from app.crud import room as crud_room
        from app.schemas.live_core import LiveRoomCreate
        
        room_data = LiveRoomCreate(
            title=f"Public测试房间_{uuid4().hex[:8]}",
            description="Public房间描述",
            is_private=False,
            record_by_default=True
        )
        room = await crud_room.create(db, obj_in=room_data, user_id=regular_user_id)
        await db.commit()
        await db.refresh(room)
        yield room
        break

@pytest.fixture
async def private_room(db_session, regular_user_id: uuid.UUID):
    """创建Private房间（用于权限测试）"""
    async for db in db_session:
        from app.crud import room as crud_room
        from app.schemas.live_core import LiveRoomCreate
        
        room_data = LiveRoomCreate(
            title=f"Private测试房间_{uuid4().hex[:8]}",
            description="Private房间描述",
            is_private=True,
            record_by_default=True
        )
        room = await crud_room.create(db, obj_in=room_data, user_id=regular_user_id)
        await db.commit()
        await db.refresh(room)
        yield room
        break

@pytest.fixture
async def private_room_owned_by_user(db_session, regular_user_id: uuid.UUID):
    """创建属于特定用户的Private房间（用于权限测试）"""
    async for db in db_session:
        from app.crud import room as crud_room
        from app.schemas.live_core import LiveRoomCreate
        
        room_data = LiveRoomCreate(
            title=f"我的Private房间_{uuid4().hex[:8]}",
            description="我的Private房间描述",
            is_private=True,
            record_by_default=True
        )
        room = await crud_room.create(db, obj_in=room_data, user_id=regular_user_id)
        await db.commit()
        await db.refresh(room)
        yield room
        break

@pytest.fixture
async def private_room_owned_by_another_user(db_session, another_user_id: uuid.UUID):
    """创建属于另一个用户的Private房间（用于测试非Owner场景）"""
    async for db in db_session:
        from app.crud import room as crud_room
        from app.schemas.live_core import LiveRoomCreate
        
        room_data = LiveRoomCreate(
            title=f"他人的Private房间_{uuid4().hex[:8]}",
            description="他人的Private房间描述",
            is_private=True,
            record_by_default=True
        )
        room = await crud_room.create(db, obj_in=room_data, user_id=another_user_id)
        await db.commit()
        await db.refresh(room)
        yield room
        break

@pytest.fixture
async def async_client_with_auth() -> AsyncGenerator[AsyncClient, None]:
    """提供带有JWT认证覆盖的异步客户端"""
    # 设置测试环境变量
    os.environ["JWT_SECRET_KEY"] = "my-key"
    os.environ["JWT_ALGORITHM"] = "HS256"

    # 总是创建测试专用的FastAPI应用，不依赖外部服务
    from fastapi import FastAPI
    from app.api.v1.api import api_router
    from app.core.deps import get_current_user

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

    # 覆盖JWT认证依赖，使用测试用户（Regular用户）
    async def override_get_current_user():
        # 使用conftest.py中的regular_user_id和regular_user_role
        # 注意：这个fixture需要依赖regular_user_id和regular_user_role，但由于fixture依赖关系复杂，这里使用默认值
        # 如果需要特定用户，应该使用regular_user_token和admin_user_token
        return {
            "user_id": "12345678-1234-5678-1234-567812345678",  # 有效的UUID格式
            "sub": "12345678-1234-5678-1234-567812345678",
            "email": "test@example.com",
            "role": "REGULAR",  # ← 新增：添加role字段
            "exp": int(time.time()) + 3600
        }

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    # 使用测试服务器 - httpx 0.25+ 使用 transport=ASGITransport(app=app)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://localhost:8000") as client:
        yield client

# ==================== Topic测试资源 Fixture（权限管理增量改造）====================

@pytest.fixture
async def published_topic(db_session, regular_user_id: uuid.UUID):
    """创建Published专题（用于权限测试）"""
    async for db in db_session:
        from app.crud import topic as crud_topic
        from app.schemas.topic import TopicCreate
        from app.models.topic import TopicStatus
        from faker import Faker
        
        fake = Faker()
        topic_data = TopicCreate(
            title=f"Published测试专题_{uuid4().hex[:8]}",
            description=fake.text(max_nb_chars=100),
            status=TopicStatus.PUBLISHED
        )
        topic = await crud_topic.create(db, obj_in=topic_data, user_id=regular_user_id)
        await db.commit()
        await db.refresh(topic)
        yield topic
        break

@pytest.fixture
async def draft_topic(db_session, regular_user_id: uuid.UUID):
    """创建Draft专题（用于权限测试）"""
    async for db in db_session:
        from app.crud import topic as crud_topic
        from app.schemas.topic import TopicCreate
        from app.models.topic import TopicStatus
        from faker import Faker
        
        fake = Faker()
        topic_data = TopicCreate(
            title=f"Draft测试专题_{uuid4().hex[:8]}",
            description=fake.text(max_nb_chars=100),
            status=TopicStatus.DRAFT
        )
        topic = await crud_topic.create(db, obj_in=topic_data, user_id=regular_user_id)
        await db.commit()
        await db.refresh(topic)
        yield topic
        break

@pytest.fixture
async def archived_topic(db_session, regular_user_id: uuid.UUID):
    """创建Archived专题（用于权限测试）"""
    async for db in db_session:
        from app.crud import topic as crud_topic
        from app.schemas.topic import TopicCreate
        from app.models.topic import TopicStatus
        from faker import Faker
        
        fake = Faker()
        topic_data = TopicCreate(
            title=f"Archived测试专题_{uuid4().hex[:8]}",
            description=fake.text(max_nb_chars=100),
            status=TopicStatus.ARCHIVED
        )
        topic = await crud_topic.create(db, obj_in=topic_data, user_id=regular_user_id)
        await db.commit()
        await db.refresh(topic)
        yield topic
        break

@pytest.fixture
async def draft_topic_owned_by_user(
    db_session, 
    regular_user_id: uuid.UUID
):
    """创建属于特定用户的Draft专题（用于权限测试）"""
    async for db in db_session:
        from app.crud import topic as crud_topic
        from app.schemas.topic import TopicCreate
        from app.models.topic import TopicStatus
        from faker import Faker
        
        fake = Faker()
        topic_data = TopicCreate(
            title=f"我的Draft专题_{uuid4().hex[:8]}",
            description=fake.text(max_nb_chars=100),
            status=TopicStatus.DRAFT
        )
        topic = await crud_topic.create(db, obj_in=topic_data, user_id=regular_user_id)
        await db.commit()
        await db.refresh(topic)
        yield topic
        break

@pytest.fixture
async def draft_topic_owned_by_another_user(
    db_session, 
    another_user_id: uuid.UUID
):
    """创建属于另一个用户的Draft专题（用于测试非Owner场景）"""
    async for db in db_session:
        from app.crud import topic as crud_topic
        from app.schemas.topic import TopicCreate
        from app.models.topic import TopicStatus
        from faker import Faker
        
        fake = Faker()
        topic_data = TopicCreate(
            title=f"他人的Draft专题_{uuid4().hex[:8]}",
            description=fake.text(max_nb_chars=100),
            status=TopicStatus.DRAFT
        )
        topic = await crud_topic.create(db, obj_in=topic_data, user_id=another_user_id)
        await db.commit()
        await db.refresh(topic)
        yield topic
        break