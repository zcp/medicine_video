# conftest_backup.py (Corrected Version)

import os
import sys
import pytest
import asyncio
from typing import AsyncGenerator, Generator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import create_engine
from fastapi.testclient import TestClient
from httpx import AsyncClient
from uuid import uuid4

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import Base, get_db, SessionLocal
from app.main import app
from app.models.download import DownloadTask, DownloadFailure, DownloadedVideo
from app.schemas.download import TaskStatus

# 测试数据库URL
#TEST_DATABASE_URL = "postgresql+asyncpg://postgres:324zq999@localhost:5432/media_download_test"

POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "324zq999")
POSTGRES_SERVER = os.getenv("POSTGRES_SERVER", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "media_download_test")

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
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session", autouse=True)
async def setup_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()

@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session
        await session.rollback()

# ⚠️ 同步数据库会话 fixture（用于同步API和Service的测试）
@pytest.fixture
def db_session_sync() -> Generator[Session, None, None]:
    """
    同步数据库会话 fixture
    
    用于测试同步的API端点和Service层代码
    与 app.database.get_db() 返回的Session类型一致
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()

@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


# 添加测试用户ID fixture
@pytest.fixture
def test_user_id():
    """提供测试用的用户ID"""
    return uuid4()


# ... existing code ...

import time
import jwt


# 添加测试用户ID fixture
@pytest.fixture
def test_user_id():
    """提供测试用的用户ID"""
    return uuid4()


# 添加模拟认证用户 fixture
@pytest.fixture
def mock_current_user(test_user_id):
    """模拟当前认证用户"""
    return {
        "user_id": str(test_user_id),
        "sub": str(test_user_id),
        "email": "test@example.com",
        "exp": int(time.time()) + 3600  # 1小时后过期
    }


# 添加模拟JWT token fixture
@pytest.fixture
def mock_jwt_token(mock_current_user):
    """生成模拟的JWT token"""
    # 使用环境变量中的JWT_SECRET_KEY，如果没有则使用测试密钥
    secret_key =  "my-key"
    algorithm =  "HS256"

    token = jwt.encode(mock_current_user, secret_key, algorithm=algorithm)
    return token


# 添加认证头 fixture
@pytest.fixture
def auth_headers(mock_jwt_token):
    """提供认证头"""
    return {"Authorization": f"Bearer {mock_jwt_token}"}


# ==================== CSV批量导入测试辅助函数 ====================

from faker import Faker
import random
import io

fake = Faker()


def generate_csv_content(num_rows: int, invalid_rows: list = None) -> bytes:
    """
    生成测试用CSV内容
    
    Args:
        num_rows: 总行数
        invalid_rows: 无效行的配置列表，如 [
            {"row": 3, "type": "short_liveroom_id"},
            {"row": 5, "type": "invalid_resource_type"}
        ]
    
    Returns:
        bytes: UTF-8编码的CSV内容
    """
    output = io.StringIO()
    # 写入表头
    output.write("liveroom_id,liveroom_title,liveroom_url,resource_url,resource_type\n")
    
    invalid_row_dict = {item["row"]: item["type"] for item in (invalid_rows or [])}
    
    for i in range(1, num_rows + 1):
        row_number = i + 1  # 从第2行开始（第1行是表头）
        
        if row_number in invalid_row_dict:
            error_type = invalid_row_dict[row_number]
            if error_type == "short_liveroom_id":
                liveroom_id = "123"  # 长度不足
                resource_type = random.choice(["hls", "mp4", "image"])
            elif error_type == "long_liveroom_id":
                liveroom_id = "1" * 25  # 长度超出
                resource_type = random.choice(["hls", "mp4", "image"])
            elif error_type == "invalid_resource_type":
                liveroom_id = str(fake.random_int(min=1000000000, max=9999999999))
                resource_type = "invalid"
            elif error_type == "missing_resource_url":
                # 缺少resource_url
                liveroom_id = str(fake.random_int(min=1000000000, max=9999999999))
                liveroom_title = fake.sentence(nb_words=3)
                liveroom_url = fake.url()
                output.write(f"{liveroom_id},{liveroom_title},{liveroom_url},,hls\n")
                continue
            else:
                liveroom_id = str(fake.random_int(min=1000000000, max=9999999999))
                resource_type = random.choice(["hls", "mp4", "image"])
        else:
            liveroom_id = str(fake.random_int(min=1000000000, max=9999999999))
            resource_type = random.choice(["hls", "mp4", "image"])
        
        liveroom_title = fake.sentence(nb_words=3)
        liveroom_url = fake.url()
        resource_url = fake.url()
        
        output.write(f"{liveroom_id},{liveroom_title},{liveroom_url},{resource_url},{resource_type}\n")
    
    return output.getvalue().encode('utf-8')


def generate_csv_file_object(csv_bytes: bytes, filename: str = "test.csv"):
    """
    生成可用于FastAPI UploadFile的文件对象
    
    Args:
        csv_bytes: CSV内容（字节）
        filename: 文件名
    
    Returns:
        io.BytesIO: 文件对象
    """
    file_obj = io.BytesIO(csv_bytes)
    file_obj.name = filename
    return file_obj


@pytest.fixture
async def clean_database(db_session):
    """清理测试数据库"""
    async for db in db_session:
        db.query(DownloadTask).delete()
        db.query(DownloadedVideo).delete()
        db.commit()
    yield
    async for db in db_session:
        db.query(DownloadTask).delete()
        db.query(DownloadedVideo).delete()
        db.commit()


# backend/media_download_service/tests/conftest.py (添加到现有文件)

import pytest
import os


def pytest_configure(config):
    """注册自定义标记"""
    config.addinivalue_line(
        "markers",
        "integration: 标记为集成测试（需要真实环境）"
    )


@pytest.fixture(scope="session")
def integration_env_check():
    """
    检查集成测试所需的环境变量

    如果缺少环境变量，会在测试开始前给出友好提示
    """
    required_vars = {
        'RUN_INTEGRATION_TESTS': '是否运行集成测试（1=是）',
        'VZAN_USERNAME': 'VZAN用户名',
        'VZAN_PASSWORD': 'VZAN密码',
        'VZAN_TOKEN': 'VZAN Token'
    }

    missing_vars = []
    for var, desc in required_vars.items():
        if not os.getenv(var):
            missing_vars.append(f"  - {var}: {desc}")

    if missing_vars:
        print("\n" + "=" * 60)
        print("⚠️ 集成测试环境变量缺失")
        print("=" * 60)
        print("缺少以下环境变量:")
        print("\n".join(missing_vars))
        print("\n设置方法（Linux/Mac）:")
        print("  export RUN_INTEGRATION_TESTS=1")
        print("  export VZAN_USERNAME='your_username'")
        print("  export VZAN_PASSWORD='your_password'")
        print("  export VZAN_TOKEN='your_token'")
        print("\n设置方法（Windows PowerShell）:")
        print("  $env:RUN_INTEGRATION_TESTS='1'")
        print("  $env:VZAN_USERNAME='your_username'")
        print("  $env:VZAN_PASSWORD='your_password'")
        print("  $env:VZAN_TOKEN='your_token'")
        print("=" * 60 + "\n")

    return missing_vars