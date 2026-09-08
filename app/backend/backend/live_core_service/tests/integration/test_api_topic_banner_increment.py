"""
LiveCore Service - Topic Banner Upload API Integration Tests (Incremental)

本文件包含专题横幅上传功能的API端点集成测试。
这是对现有test_api_topic.py的增量补充，测试新增的banner上传API端点。

⚠️ 使用说明：
1. 将本文件中的 TestTopicBannerAPI 类添加到 tests/integration/test_api_topic.py 文件末尾
2. 将本文件中的三个辅助函数添加到 tests/integration/test_api_topic.py 文件末尾
3. 确保已安装 Pillow: pip install Pillow
"""

import uuid
from typing import AsyncGenerator

import pytest
from io import BytesIO
from PIL import Image
from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy import select

from app.crud import topic as crud_topic
from app.models.topic import Topic, TopicStatus
from app.schemas.topic import TopicCreate
from app.core.deps import get_current_user
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture
async def topic_client(db_session) -> AsyncGenerator[tuple, None]:
    """
    专门为 topic 测试创建的 fixture，返回 (client, app, db) 元组
    这样可以在测试中访问 app 实例来设置 dependency_overrides
    """
    from app.api.v1.api import api_router
    from app.database import get_db
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.ext.asyncio import create_async_engine
    import os

    # 创建测试专用的 FastAPI 应用
    app = FastAPI(
        title="LiveCore Service Test - Topic",
        version="1.0.0",
        redirect_slashes=False
    )

    # 注册路由
    app.include_router(api_router, prefix="/api/v1")

    # 设置数据库 - 使用与 conftest 相同的配置
    POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "CHANGE_ME")
    POSTGRES_SERVER = os.getenv("POSTGRES_SERVER", "localhost")
    POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
    POSTGRES_DB = os.getenv("POSTGRES_DB", "live_core_test")
    TEST_DATABASE_URL = f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_SERVER}:{POSTGRES_PORT}/{POSTGRES_DB}"

    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async_session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # 覆盖数据库依赖
    async def override_get_db():
        async with async_session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    # 创建客户端
    async with AsyncClient(app=app, base_url="http://localhost:8000") as client:
        # 获取数据库会话
        async for db in db_session:
            yield (client, app, db)
            break

    # 清理
    await engine.dispose()


# ==================== 新增：专题横幅上传API测试 ====================

class TestTopicBannerAPI:
    """专题横幅上传API测试（新增）"""
    
    @pytest.mark.asyncio
    async def test_upload_banner_success(
        self, 
        topic_client,
        regular_user_token: str,
        regular_user_id: uuid.UUID
    ):
        """
        测试成功上传横幅（Strict Auth，需要JWT Token）
        
        验证点:
        1. HTTP状态码为200
        2. 响应包含正确的JSON结构（code, message, data, timestamp）
        3. 业务码为200
        4. 返回 topic_id 和 banner_url
        5. banner_url 格式正确（以 /media/topics/ 开头）
        6. 数据库中 banner_url 已更新
        """
        async for client, app, db in topic_client:
            # ===== Arrange (准备) =====
            # 创建属于regular_user_id的专题
            topic_in = TopicCreate(
                title=f"Test Topic {uuid.uuid4().hex[:6]}",
                description="Test Description",
                status="draft"
            )
            topic = await crud_topic.create(db, topic_in, regular_user_id)
            headers = {"Authorization": f"Bearer {regular_user_token}"}  # ← 修改：使用JWT Token
            
            # 创建测试图片
            image = Image.new('RGB', (100, 100), color='red')
            buffer = BytesIO()
            image.save(buffer, format='PNG')
            buffer.seek(0)
            
            # ===== Act (执行) =====
            # 上传横幅（使用 multipart/form-data）
            files = {"file": ("test_banner.png", buffer, "image/png")}
            response = await client.post(
                f"/api/v1/topics/{topic.id}/banner",
                files=files,
                headers=headers  # ← 新增：添加Token
            )
            
            # ===== Assert (断言) =====
            assert response.status_code == 200, \
                f"期望HTTP状态码200，实际 {response.status_code}"
            
            data = response.json()
            assert "code" in data, "响应缺少 code 字段"
            assert "message" in data, "响应缺少 message 字段"
            assert "data" in data, "响应缺少 data 字段"
            assert "timestamp" in data, "响应缺少 timestamp 字段"
            
            # 断言业务码
            assert data["code"] == 200, \
                f"期望业务码200，实际 {data['code']}"
            assert data["message"] == "success"
            
            # 断言响应数据
            banner_data = data["data"]
            assert banner_data["topic_id"] == str(topic.id), \
                f"期望topic_id {topic.id}，实际 {banner_data['topic_id']}"
            assert banner_data["banner_url"] is not None, \
                "banner_url 不应为 None"
            assert banner_data["banner_url"].startswith("/media/topics/"), \
                f"横幅URL格式错误: {banner_data['banner_url']}"
            
            # 通过GET API验证数据更新（避免事务隔离问题）
            # 注意：GET /topics/{topic_id} 是Optional Auth，但Draft专题需要Owner权限
            get_response = await client.get(
                f"/api/v1/topics/{topic.id}",
                headers=headers  # ← 新增：添加Token（Draft专题需要Owner权限）
            )
            assert get_response.status_code == 200, \
                f"获取专题详情失败: {get_response.status_code}"
            
            get_data = get_response.json()["data"]
            assert get_data["banner_url"] is not None, \
                "GET API返回的banner_url不应为None"
            assert banner_data["banner_url"] in get_data["banner_url"], \
                f"GET API返回的banner_url与上传响应不一致"


    @pytest.mark.asyncio
    async def test_upload_banner_topic_not_found(
        self, 
        topic_client,
        regular_user_token: str
    ):
        """
        测试专题不存在时上传横幅
        
        验证点:
        1. HTTP状态码为404
        2. 业务码为2001（资源不存在）
        3. data包含 resource="Topic"
        4. data包含不存在的专题ID
        """
        async for client, app, db in topic_client:
            # ===== Arrange (准备) =====
            random_topic_id = uuid.uuid4()
            headers = {"Authorization": f"Bearer {regular_user_token}"}  # ← 修改：使用JWT Token
            
            # 创建测试图片
            image = Image.new('RGB', (100, 100), color='red')
            buffer = BytesIO()
            image.save(buffer, format='PNG')
            buffer.seek(0)
            
            # ===== Act (执行) =====
            # 尝试上传横幅
            files = {"file": ("test_banner.png", buffer, "image/png")}
            response = await client.post(
                f"/api/v1/topics/{random_topic_id}/banner",
                files=files,
                headers=headers  # ← 新增：添加Token
            )
            
            # ===== Assert (断言) =====
            assert response.status_code == 404, \
                f"期望HTTP状态码404，实际 {response.status_code}"
            
            data = response.json()
            assert data["code"] == 2001, \
                f"期望业务码2001，实际 {data['code']}"
            assert data["message"] == "资源不存在"
            assert "data" in data
            assert data["data"]["resource"] == "Topic", \
                f"期望resource为Topic，实际 {data['data']['resource']}"
            assert data["data"]["id"] == str(random_topic_id), \
                "响应中的ID与请求不一致"


    @pytest.mark.asyncio
    async def test_upload_banner_permission_denied(
        self, 
        topic_client,
        regular_user_token: str,
        another_user_id: uuid.UUID
    ):
        """
        测试权限不足时上传横幅
        
        验证点:
        1. HTTP状态码为403
        2. 业务码为2003（操作被禁止）
        3. data包含权限错误信息
        4. 非创建者无法上传横幅
        """
        async for client, app, db in topic_client:
            # ===== Arrange (准备) =====
            # 创建属于another_user_id的专题
            topic_in = TopicCreate(
                title=f"Test Topic {uuid.uuid4().hex[:6]}",
                description="Test Description",
                status="draft"
            )
            topic = await crud_topic.create(db, topic_in, another_user_id)
            headers = {"Authorization": f"Bearer {regular_user_token}"}  # ← 修改：使用regular_user_token尝试上传another_user_id的专题的横幅
            
            # 创建测试图片
            image = Image.new('RGB', (100, 100), color='red')
            buffer = BytesIO()
            image.save(buffer, format='PNG')
            buffer.seek(0)
            
            # ===== Act (执行) =====
            # 尝试上传横幅
            files = {"file": ("test_banner.png", buffer, "image/png")}
            response = await client.post(
                f"/api/v1/topics/{topic.id}/banner",
                files=files,
                headers=headers  # ← 新增：添加Token
            )
            
            # ===== Assert (断言) =====
            assert response.status_code == 403, \
                f"期望HTTP状态码403，实际 {response.status_code}"
            
            data = response.json()
            assert data["code"] in [2003, 3002], \
                f"期望业务码2003或3002，实际 {data['code']}"  # Permission Denied
            assert "data" in data
            assert "error" in data["data"], \
                "响应data中缺少error字段"
            assert "reason" in data["data"], \
                "响应data中缺少reason字段"


    @pytest.mark.asyncio
    async def test_upload_banner_invalid_file_type(
        self, 
        topic_client,
        regular_user_id: uuid.UUID,
        regular_user_token: str
    ):
        """
        测试上传无效文件类型
        
        验证点:
        1. HTTP状态码为400
        2. 业务码为4002（参数校验失败）
        3. data包含文件类型错误信息
        4. 只接受PNG和JPG格式
        """
        async for client, app, db in topic_client:
            # ===== Arrange (准备) =====
            # 创建属于regular_user_id的专题
            topic_in = TopicCreate(
                title=f"Test Topic {uuid.uuid4().hex[:6]}",
                description="Test Description",
                status="draft"
            )
            topic = await crud_topic.create(db, topic_in, regular_user_id)
            headers = {"Authorization": f"Bearer {regular_user_token}"}  # ← 修改：使用JWT Token
            
            # 创建无效文件（文本文件）
            invalid_file = BytesIO(b"This is not an image file")
            invalid_file.seek(0)
            
            # ===== Act (执行) =====
            # 尝试上传无效文件
            files = {"file": ("test.txt", invalid_file, "text/plain")}
            response = await client.post(
                f"/api/v1/topics/{topic.id}/banner",
                files=files,
                headers=headers  # ← 新增：添加Token
            )
            
            # ===== Assert (断言) =====
            assert response.status_code == 400, \
                f"期望HTTP状态码400，实际 {response.status_code}"
            
            data = response.json()
            assert data["code"] == 4002, \
                f"期望业务码4002，实际 {data['code']}"
            assert data["message"] == "参数校验失败"
            assert "data" in data
            assert "file" in data["data"], \
                "响应data中缺少file字段"


    @pytest.mark.asyncio
    async def test_upload_banner_oversized_file(
        self, 
        topic_client,
        regular_user_id: uuid.UUID,
        regular_user_token: str
    ):
        """
        测试上传超过10MB的文件
        
        验证点:
        1. HTTP状态码为400
        2. 业务码为4002（参数校验失败）
        3. data包含文件大小错误信息
        4. 文件大小限制为10MB
        """
        async for client, app, db in topic_client:
            # ===== Arrange (准备) =====
            # 创建属于regular_user_id的专题
            topic_in = TopicCreate(
                title=f"Test Topic {uuid.uuid4().hex[:6]}",
                description="Test Description",
                status="draft"
            )
            topic = await crud_topic.create(db, topic_in, regular_user_id)
            headers = {"Authorization": f"Bearer {regular_user_token}"}  # ← 修改：使用JWT Token
            
            # 创建超大文件（超过10MB = 10485760 bytes）
            # 创建一个11MB的随机二进制内容模拟超大图片
            large_file_size = 11 * 1024 * 1024  # 11MB
            buffer = BytesIO(b'\x00' * large_file_size)
            buffer.seek(0)
            
            # ===== Act (执行) =====
            # 尝试上传超大文件
            files = {"file": ("large_banner.png", buffer, "image/png")}
            response = await client.post(
                f"/api/v1/topics/{topic.id}/banner",
                files=files,
                headers=headers  # ← 新增：添加Token
            )
            
            # ===== Assert (断言) =====
            assert response.status_code == 400, \
                f"期望HTTP状态码400，实际 {response.status_code}"
            
            data = response.json()
            assert data["code"] == 4002, \
                f"期望业务码4002，实际 {data['code']}"
            assert data["message"] == "参数校验失败"
            assert "data" in data
            assert "file" in data["data"], \
                "响应data中缺少file字段"
            # 验证错误消息提到文件大小
            assert "大小" in data["data"]["file"] or "size" in data["data"]["file"].lower(), \
                "错误消息应提到文件大小问题"


# ==================== 新增：辅助函数 - 文件上传测试 ====================

def create_test_image(width: int = 100, height: int = 100, format: str = 'PNG') -> BytesIO:
    """
    创建测试图片
    
    Args:
        width: 图片宽度，默认100
        height: 图片高度，默认100
        format: 图片格式，'PNG' 或 'JPEG'
        
    Returns:
        BytesIO: 图片二进制流
        
    Example:
        >>> image_buffer = create_test_image(200, 200, 'PNG')
        >>> files = {"file": ("test.png", image_buffer, "image/png")}
    """
    image = Image.new('RGB', (width, height), color='red')
    buffer = BytesIO()
    image.save(buffer, format=format)
    buffer.seek(0)
    return buffer


def create_oversized_image() -> BytesIO:
    """
    创建超过10MB的测试文件
    
    用于测试文件大小验证。创建一个11MB的二进制文件。
    
    Returns:
        BytesIO: 超大文件二进制流
        
    Note:
        创建11MB的二进制内容（10MB = 10485760 bytes）
    """
    # 创建11MB的文件（超过10MB限制）
    large_file_size = 11 * 1024 * 1024  # 11MB
    buffer = BytesIO(b'\x00' * large_file_size)
    buffer.seek(0)
    return buffer


def create_invalid_file() -> BytesIO:
    """
    创建无效的文件（非图片）
    
    用于测试文件类型验证。创建一个文本文件，
    应该被FileHandler拒绝。
    
    Returns:
        BytesIO: 文本文件二进制流
        
    Example:
        >>> invalid_file = create_invalid_file()
        >>> files = {"file": ("test.txt", invalid_file, "text/plain")}
    """
    buffer = BytesIO(b"This is not an image file. Just plain text.")
    buffer.seek(0)
    return buffer

