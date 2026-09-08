"""
LiveCore Service - Topic Permission State Change Integration Tests

本模块包含专题权限状态变更的专项测试。
测试范围：专题状态变更后的权限动态变化

测试场景：
- Published → Draft：匿名用户无法访问
- Draft → Published：匿名用户可以访问
- Published → Archived：匿名用户无法访问
- 状态变更后，Owner始终可访问
- 状态变更后，Admin始终可访问
"""

import pytest
import uuid
from typing import AsyncGenerator
from httpx import AsyncClient
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession


# ==================== 本地 Fixture ====================

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
    
    engine = create_async_engine(
        TEST_DATABASE_URL, 
        echo=False,
        pool_pre_ping=True,  # 连接池预检查，确保连接有效
        pool_recycle=3600  # 连接回收时间（秒）
    )
    async_session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    # 覆盖数据库依赖
    async def override_get_db():
        async with async_session_factory() as session:
            yield session
    
    app.dependency_overrides[get_db] = override_get_db
    
    # 创建客户端
    try:
        async with AsyncClient(app=app, base_url="http://localhost:8000") as client:
            # 获取数据库会话
            async for db in db_session:
                yield (client, app, db)
                break
    finally:
        # 清理：确保engine在所有连接关闭后正确dispose
        await engine.dispose()


class TestTopicPermissionStateChange:
    """专题权限状态变更专项测试"""
    
    @pytest.mark.asyncio
    async def test_topic_status_published_to_draft_affects_anonymous_visibility(
        self,
        topic_client,
        regular_user_token: str,
        regular_user_id: uuid.UUID
    ):
        """测试：专题从Published改为Draft后，匿名用户无法访问"""
        async for client, app, db in topic_client:
            # ===== Arrange (准备) =====
            # 1. 创建Published专题
            create_data = {
                "title": f"Test Topic {uuid.uuid4().hex[:6]}",
                "description": "Test Description",
                "status": "published"
            }
            headers = {"Authorization": f"Bearer {regular_user_token}"}
            create_response = await client.post("/api/v1/topics", json=create_data, headers=headers)
            assert create_response.status_code == 200
            topic_id = create_response.json()["data"]["id"]
            
            # ===== Act (执行) =====
            # 2. 匿名用户可以访问
            detail_response = await client.get(f"/api/v1/topics/{topic_id}")
            assert detail_response.status_code == 200
            
            # 3. 修改为draft状态
            update_data = {"status": "draft"}
            update_response = await client.patch(f"/api/v1/topics/{topic_id}", json=update_data, headers=headers)
            assert update_response.status_code == 200
            
            # ===== Assert (断言) =====
            # 4. 匿名用户无法访问（应返回404）
            detail_response = await client.get(f"/api/v1/topics/{topic_id}")
            assert detail_response.status_code == 404
            response_json = detail_response.json()
            if "code" in response_json:
                assert response_json["code"] == 2001
    
    @pytest.mark.asyncio
    async def test_topic_status_draft_to_published_allows_anonymous_visibility(
        self,
        topic_client,
        regular_user_token: str,
        regular_user_id: uuid.UUID
    ):
        """测试：专题从Draft改为Published后，匿名用户可以访问"""
        async for client, app, db in topic_client:
            # ===== Arrange (准备) =====
            # 1. 创建Draft专题
            create_data = {
                "title": f"Test Topic {uuid.uuid4().hex[:6]}",
                "description": "Test Description",
                "status": "draft"
            }
            headers = {"Authorization": f"Bearer {regular_user_token}"}
            create_response = await client.post("/api/v1/topics", json=create_data, headers=headers)
            assert create_response.status_code == 200
            topic_id = create_response.json()["data"]["id"]
            
            # ===== Act (执行) =====
            # 2. 匿名用户无法访问
            detail_response = await client.get(f"/api/v1/topics/{topic_id}")
            assert detail_response.status_code == 404
            
            # 3. 修改为published状态
            update_data = {"status": "published"}
            update_response = await client.patch(f"/api/v1/topics/{topic_id}", json=update_data, headers=headers)
            assert update_response.status_code == 200
            
            # ===== Assert (断言) =====
            # 4. 匿名用户可以访问（应返回200）
            detail_response = await client.get(f"/api/v1/topics/{topic_id}")
            assert detail_response.status_code == 200
            assert detail_response.json()["data"]["id"] == topic_id
    
    @pytest.mark.asyncio
    async def test_topic_status_published_to_archived_affects_anonymous_visibility(
        self,
        topic_client,
        regular_user_token: str,
        regular_user_id: uuid.UUID
    ):
        """测试：专题从Published改为Archived后，匿名用户无法访问"""
        async for client, app, db in topic_client:
            # ===== Arrange (准备) =====
            # 1. 创建Published专题
            create_data = {
                "title": f"Test Topic {uuid.uuid4().hex[:6]}",
                "description": "Test Description",
                "status": "published"
            }
            headers = {"Authorization": f"Bearer {regular_user_token}"}
            create_response = await client.post("/api/v1/topics", json=create_data, headers=headers)
            assert create_response.status_code == 200
            topic_id = create_response.json()["data"]["id"]
            
            # ===== Act (执行) =====
            # 2. 匿名用户可以访问
            detail_response = await client.get(f"/api/v1/topics/{topic_id}")
            assert detail_response.status_code == 200
            
            # 3. 修改为archived状态
            update_data = {"status": "archived"}
            update_response = await client.patch(f"/api/v1/topics/{topic_id}", json=update_data, headers=headers)
            assert update_response.status_code == 200
            
            # ===== Assert (断言) =====
            # 4. 匿名用户无法访问（应返回404）
            detail_response = await client.get(f"/api/v1/topics/{topic_id}")
            assert detail_response.status_code == 404
            response_json = detail_response.json()
            if "code" in response_json:
                assert response_json["code"] == 2001
    
    @pytest.mark.asyncio
    async def test_topic_status_change_owner_always_has_access(
        self,
        topic_client,
        regular_user_token: str,
        regular_user_id: uuid.UUID
    ):
        """测试：状态变更后，Owner始终可访问"""
        async for client, app, db in topic_client:
            # ===== Arrange (准备) =====
            # 1. 创建Draft专题
            create_data = {
                "title": f"Test Topic {uuid.uuid4().hex[:6]}",
                "description": "Test Description",
                "status": "draft"
            }
            headers = {"Authorization": f"Bearer {regular_user_token}"}
            create_response = await client.post("/api/v1/topics", json=create_data, headers=headers)
            assert create_response.status_code == 200
            topic_id = create_response.json()["data"]["id"]
            
            # ===== Act & Assert (执行 & 断言) =====
            # 2. Owner可以访问Draft专题
            detail_response = await client.get(f"/api/v1/topics/{topic_id}", headers=headers)
            assert detail_response.status_code == 200
            
            # 3. 修改为published状态
            update_data = {"status": "published"}
            update_response = await client.patch(f"/api/v1/topics/{topic_id}", json=update_data, headers=headers)
            assert update_response.status_code == 200
            
            # 4. Owner仍然可以访问
            detail_response = await client.get(f"/api/v1/topics/{topic_id}", headers=headers)
            assert detail_response.status_code == 200
            
            # 5. 修改为archived状态
            update_data = {"status": "archived"}
            update_response = await client.patch(f"/api/v1/topics/{topic_id}", json=update_data, headers=headers)
            assert update_response.status_code == 200
            
            # 6. Owner仍然可以访问
            detail_response = await client.get(f"/api/v1/topics/{topic_id}", headers=headers)
            assert detail_response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_topic_status_change_admin_always_has_access(
        self,
        topic_client,
        regular_user_token: str,
        admin_user_token: str,
        regular_user_id: uuid.UUID
    ):
        """测试：状态变更后，Admin始终可访问"""
        async for client, app, db in topic_client:
            # ===== Arrange (准备) =====
            # 1. 创建Draft专题（属于regular_user_id）
            create_data = {
                "title": f"Test Topic {uuid.uuid4().hex[:6]}",
                "description": "Test Description",
                "status": "draft"
            }
            headers = {"Authorization": f"Bearer {regular_user_token}"}
            create_response = await client.post("/api/v1/topics", json=create_data, headers=headers)
            assert create_response.status_code == 200
            topic_id = create_response.json()["data"]["id"]
            
            # ===== Act & Assert (执行 & 断言) =====
            admin_headers = {"Authorization": f"Bearer {admin_user_token}"}
            
            # 2. Admin可以访问Draft专题（即使不是Owner）
            detail_response = await client.get(f"/api/v1/topics/{topic_id}", headers=admin_headers)
            assert detail_response.status_code == 200
            
            # 3. 修改为published状态
            update_data = {"status": "published"}
            update_response = await client.patch(f"/api/v1/topics/{topic_id}", json=update_data, headers=headers)
            assert update_response.status_code == 200
            
            # 4. Admin仍然可以访问
            detail_response = await client.get(f"/api/v1/topics/{topic_id}", headers=admin_headers)
            assert detail_response.status_code == 200
            
            # 5. 修改为archived状态
            update_data = {"status": "archived"}
            update_response = await client.patch(f"/api/v1/topics/{topic_id}", json=update_data, headers=headers)
            assert update_response.status_code == 200
            
            # 6. Admin仍然可以访问
            detail_response = await client.get(f"/api/v1/topics/{topic_id}", headers=admin_headers)
            assert detail_response.status_code == 200

