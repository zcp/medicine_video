"""
LiveCore Service - Topic Search Feature Incremental Tests (API Layer)

This module contains incremental integration tests for the new search functionality
(title and topic_id filters) added to the topic list API endpoint.
"""

import uuid
import pytest
from typing import List, Dict, Any, AsyncGenerator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from faker import Faker
from httpx import AsyncClient
from fastapi import FastAPI

# 项目内导入
from app.core.deps import get_current_user
from app.crud import topic as crud_topic
from app.models.topic import Topic, TopicStatus
from app.schemas.topic import TopicCreate

# 初始化 Faker
fake = Faker()


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
        title="LiveCore Service Test - Topic Search",
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
    
    # 创建客户端并获取数据库会话
    async with AsyncClient(app=app, base_url="http://localhost:8000") as client:
        async for db in db_session:
            yield (client, app, db)
            break
    
    # 清理
    await engine.dispose()


# ==================== 辅助函数 (Helper Functions) ====================

async def create_test_topic(
    db: AsyncSession,
    user_id: uuid.UUID = None,
    title: str = None,
    status: str = "draft"
) -> Topic:
    """创建测试专题的辅助函数"""
    if user_id is None:
        user_id = uuid.uuid4()
    
    if title is None:
        title = f"{fake.catch_phrase()}_{uuid.uuid4().hex[:6]}"
    
    # 转换status字符串为枚举
    status_enum = TopicStatus(status) if isinstance(status, str) else status
    
    topic_in = TopicCreate(
        title=title,
        description=fake.text(max_nb_chars=100),
        status=status_enum
    )
    
    return await crud_topic.create(db, topic_in, user_id)


# ==================== API层查询功能集成测试 ====================

@pytest.mark.asyncio
async def test_get_topic_list_with_title_query_parameter(topic_client):
    """
    测试API层接受title查询参数并返回正确结果
    
    验证点:
    1. HTTP状态码为200
    2. 响应JSON结构正确（code, message, data, timestamp）
    3. 返回的专题列表只包含title中包含关键词的published专题
    4. 分页信息正确
    """
    async for client, app, db in topic_client:
        # Arrange: 创建多个专题，部分title包含关键词，部分不包含
        user_id = uuid.uuid4()
        search_keyword = f"api_title_test_{uuid.uuid4().hex[:6]}"
        
        # 创建包含关键词的published专题
        topic1 = await create_test_topic(
            db,
            user_id=user_id,
            title=f"{search_keyword}_Topic1",
            status="published"
        )
        # 创建包含关键词的draft专题（匿名用户不应该看到）
        topic2 = await create_test_topic(
            db,
            user_id=user_id,
            title=f"{search_keyword}_Topic2",
            status="draft"
        )
        # 创建不包含关键词的published专题
        topic3 = await create_test_topic(
            db,
            user_id=user_id,
            title=f"Other_Topic_{uuid.uuid4().hex[:6]}",
            status="published"
        )
        await db.commit()
        
        # Act: 匿名调用API（不需要认证）
        response = await client.get(
            "/api/v1/topics",
            params={"title": search_keyword}
        )
        
        # Assert: 验证HTTP状态码
        assert response.status_code == 200, \
            f"期望HTTP状态码200，实际 {response.status_code}"
        
        # Assert: 验证响应JSON结构
        data = response.json()
        assert "code" in data, "响应缺少 code 字段"
        assert "message" in data, "响应缺少 message 字段"
        assert "data" in data, "响应缺少 data 字段"
        assert "timestamp" in data, "响应缺少 timestamp 字段"
        
        # Assert: 验证业务码
        assert data["code"] == 200, f"期望业务码200，实际 {data['code']}"
        assert data["message"] == "success"
        
        # Assert: 验证响应数据
        paginated_data = data["data"]
        assert "total" in paginated_data, "响应data中缺少 total 字段"
        assert "page" in paginated_data, "响应data中缺少 page 字段"
        assert "size" in paginated_data, "响应data中缺少 size 字段"
        assert "items" in paginated_data, "响应data中缺少 items 字段"
        
        # Assert: 验证返回的专题列表只包含title中包含关键词的published专题
        items = paginated_data["items"]
        assert isinstance(items, list), "items应该是list类型"
        assert len(items) == 1, f"期望返回1个published专题，实际返回 {len(items)} 个"
        assert paginated_data["total"] == 1, f"期望total为1，实际为 {paginated_data['total']}"
        
        # 验证返回的专题是topic1（published且title匹配）
        topic_ids = [item["id"] for item in items]
        assert str(topic1.id) in topic_ids, "应该返回topic1（published且title匹配）"
        assert str(topic2.id) not in topic_ids, "不应该返回topic2（draft状态，匿名用户无权访问）"
        assert str(topic3.id) not in topic_ids, "不应该返回topic3（title不匹配）"
        
        # 验证返回的专题title包含关键词
        for item in items:
            assert search_keyword.lower() in item["title"].lower(), \
                f"返回的专题title应该包含'{search_keyword}'，实际title为 {item['title']}"


@pytest.mark.asyncio
async def test_get_topic_list_with_topic_id_query_parameter(topic_client):
    """
    测试API层接受topic_id查询参数并返回正确结果
    
    验证点:
    1. HTTP状态码为200
    2. 返回的专题列表只包含指定ID的专题（如果该专题是published状态）
    3. 验证如果topic_id不存在或格式无效，返回适当的错误响应
    """
    async for client, app, db in topic_client:
        # Arrange: 创建一个published专题和一个draft专题
        user_id = uuid.uuid4()
        published_topic = await create_test_topic(
            db,
            user_id=user_id,
            status="published"
        )
        draft_topic = await create_test_topic(
            db,
            user_id=user_id,
            status="draft"
        )
        await db.commit()
        
        # Act & Assert 1: 使用published专题的ID查询（匿名用户应该能看到）
        response = await client.get(
            "/api/v1/topics",
            params={"topic_id": str(published_topic.id)}
        )
        
        assert response.status_code == 200, \
            f"期望HTTP状态码200，实际 {response.status_code}"
        
        data = response.json()
        assert data["code"] == 200, f"期望业务码200，实际 {data['code']}"
        
        items = data["data"]["items"]
        assert len(items) == 1, f"期望返回1个专题，实际返回 {len(items)} 个"
        assert items[0]["id"] == str(published_topic.id), \
            f"期望返回的专题ID为 {published_topic.id}，实际为 {items[0]['id']}"
        
        # Act & Assert 2: 使用draft专题的ID查询（匿名用户不应该能看到）
        response = await client.get(
            "/api/v1/topics",
            params={"topic_id": str(draft_topic.id)}
        )
        
        assert response.status_code == 200, \
            f"期望HTTP状态码200，实际 {response.status_code}"
        
        data = response.json()
        assert data["code"] == 200, f"期望业务码200，实际 {data['code']}"
        
        items = data["data"]["items"]
        assert len(items) == 0, \
            f"匿名用户不应该能看到draft专题，期望返回0个，实际返回 {len(items)} 个"
        assert data["data"]["total"] == 0, \
            f"期望total为0，实际为 {data['data']['total']}"
        
        # Act & Assert 3: 使用无效的UUID格式（应该返回400）
        response = await client.get(
            "/api/v1/topics",
            params={"topic_id": "invalid-uuid"}
        )
        
        assert response.status_code == 400, \
            f"无效的UUID格式应该返回400，实际 {response.status_code}"
        
        data = response.json()
        assert data["code"] == 4001, f"期望业务码4001（参数校验失败），实际 {data['code']}"


@pytest.mark.asyncio
async def test_get_topic_list_with_combined_filters(topic_client):
    """
    测试API层支持title、topic_id、status等参数的组合使用
    
    验证点:
    1. 返回结果同时满足title和status筛选条件
    2. 对于匿名用户，由于权限限制，可能返回空列表
    """
    async for client, app, db in topic_client:
        # Arrange: 创建多个专题，使用不同的title、status、user_id组合
        user_id = uuid.uuid4()
        search_keyword = f"combined_test_{uuid.uuid4().hex[:6]}"
        
        # 创建published专题，title包含关键词
        published_topic = await create_test_topic(
            db,
            user_id=user_id,
            title=f"{search_keyword}_Published",
            status="published"
        )
        # 创建draft专题，title包含关键词（匿名用户不应该看到）
        draft_topic = await create_test_topic(
            db,
            user_id=user_id,
            title=f"{search_keyword}_Draft",
            status="draft"
        )
        await db.commit()
        
        # Act: 匿名用户使用title和status=draft筛选（应该返回空列表，因为匿名用户无权访问draft）
        response = await client.get(
            "/api/v1/topics",
            params={"title": search_keyword, "status": "draft"}
        )
        
        # Assert
        assert response.status_code == 200, \
            f"期望HTTP状态码200，实际 {response.status_code}"
        
        data = response.json()
        assert data["code"] == 200, f"期望业务码200，实际 {data['code']}"
        
        items = data["data"]["items"]
        assert len(items) == 0, \
            f"匿名用户查询draft专题应该返回空列表，实际返回 {len(items)} 个"
        assert data["data"]["total"] == 0, \
            f"期望total为0，实际为 {data['data']['total']}"


@pytest.mark.asyncio
async def test_anonymous_user_search_by_title_only_published(topic_client):
    """
    测试匿名用户按title查询只能看到published专题
    
    验证点:
    1. 只返回published状态的专题
    2. 不返回draft或archived状态的专题（即使title匹配）
    """
    async for client, app, db in topic_client:
        # Arrange: 创建多个专题，title都包含相同关键词
        user_id = uuid.uuid4()
        search_keyword = f"anonymous_test_{uuid.uuid4().hex[:6]}"
        
        published_topic = await create_test_topic(
            db,
            user_id=user_id,
            title=f"{search_keyword}_Published",
            status="published"
        )
        draft_topic = await create_test_topic(
            db,
            user_id=user_id,
            title=f"{search_keyword}_Draft",
            status="draft"
        )
        archived_topic = await create_test_topic(
            db,
            user_id=user_id,
            title=f"{search_keyword}_Archived",
            status="archived"
        )
        await db.commit()
        
        # Act: 匿名调用API（不需要认证）
        response = await client.get(
            "/api/v1/topics",
            params={"title": search_keyword}
        )
        
        # Assert
        assert response.status_code == 200, \
            f"期望HTTP状态码200，实际 {response.status_code}"
        
        data = response.json()
        assert data["code"] == 200, f"期望业务码200，实际 {data['code']}"
        
        items = data["data"]["items"]
        assert len(items) == 1, \
            f"匿名用户应该只能看到1个published专题，实际返回 {len(items)} 个"
        assert data["data"]["total"] == 1, \
            f"期望total为1，实际为 {data['data']['total']}"
        
        # 验证返回的是published专题
        topic_ids = [item["id"] for item in items]
        assert str(published_topic.id) in topic_ids, "应该能看到published专题"
        assert str(draft_topic.id) not in topic_ids, "不应该能看到draft专题"
        assert str(archived_topic.id) not in topic_ids, "不应该能看到archived专题"
        
        # 验证所有返回的专题status都是published
        for item in items:
            assert item["status"] == "published", \
                f"匿名用户只能看到published专题，实际status为 {item['status']}"


@pytest.mark.asyncio
async def test_regular_user_search_own_draft_by_title(
    topic_client,
    regular_user_token: str,
    regular_user_id: uuid.UUID
):
    """
    测试Regular用户可以查询自己创建的draft专题
    
    验证点:
    1. 只返回用户自己的draft专题
    2. 不返回其他用户的draft专题
    """
    async for client, app, db in topic_client:
        # Arrange: 创建当前用户和其他用户的draft专题，title都包含相同关键词
        another_user_id = uuid.uuid4()
        search_keyword = f"regular_own_draft_{uuid.uuid4().hex[:6]}"
        
        own_draft = await create_test_topic(
            db,
            user_id=regular_user_id,
            title=f"{search_keyword}_Own_Draft",
            status="draft"
        )
        other_draft = await create_test_topic(
            db,
            user_id=another_user_id,
            title=f"{search_keyword}_Other_Draft",
            status="draft"
        )
        await db.commit()
        
        # Act: 使用JWT Token认证（regular_user_token）
        response = await client.get(
            "/api/v1/topics",
            params={"title": search_keyword, "status": "draft"},
            headers={"Authorization": f"Bearer {regular_user_token}"}
        )
        
        # Assert
        assert response.status_code == 200, \
            f"期望HTTP状态码200，实际 {response.status_code}"
        
        data = response.json()
        assert data["code"] == 200, f"期望业务码200，实际 {data['code']}"
        
        items = data["data"]["items"]
        assert len(items) == 1, \
            f"Regular用户应该只能看到自己创建的1个draft专题，实际返回 {len(items)} 个"
        assert data["data"]["total"] == 1, \
            f"期望total为1，实际为 {data['data']['total']}"
        
        # 验证返回的是自己的draft专题
        topic_ids = [item["id"] for item in items]
        assert str(own_draft.id) in topic_ids, "应该能看到自己创建的draft专题"
        assert str(other_draft.id) not in topic_ids, "不应该能看到其他用户的draft专题"


@pytest.mark.asyncio
async def test_regular_user_cannot_search_others_draft(
    topic_client,
    regular_user_token: str,
    another_user_id: uuid.UUID
):
    """
    测试Regular用户不能查询他人的draft专题
    
    验证点:
    1. 返回的专题列表为空（即使title匹配，但权限不足）
    2. HTTP状态码为200（不是403，因为列表查询返回空列表是正常行为）
    """
    async for client, app, db in topic_client:
        # Arrange: 创建其他用户的draft专题，title包含关键词
        search_keyword = f"others_draft_{uuid.uuid4().hex[:6]}"
        
        other_draft = await create_test_topic(
            db,
            user_id=another_user_id,
            title=f"{search_keyword}_Other_Draft",
            status="draft"
        )
        await db.commit()
        
        # Act: 使用JWT Token认证（regular_user_token），查询他人的draft专题
        response = await client.get(
            "/api/v1/topics",
            params={"title": search_keyword, "status": "draft"},
            headers={"Authorization": f"Bearer {regular_user_token}"}
        )
        
        # Assert
        assert response.status_code == 200, \
            f"列表查询应该返回200（即使结果为空），实际 {response.status_code}"
        
        data = response.json()
        assert data["code"] == 200, f"期望业务码200，实际 {data['code']}"
        
        items = data["data"]["items"]
        assert len(items) == 0, \
            f"Regular用户不应该能看到他人的draft专题，期望返回0个，实际返回 {len(items)} 个"
        assert data["data"]["total"] == 0, \
            f"期望total为0，实际为 {data['data']['total']}"


@pytest.mark.asyncio
async def test_admin_user_search_all_by_title(
    topic_client,
    admin_user_token: str
):
    """
    测试Admin用户可以查询所有状态的专题
    
    验证点:
    1. 返回所有状态的专题（published、draft、archived）
    2. 权限过滤未限制结果
    """
    async for client, app, db in topic_client:
        # Arrange: 创建多个专题，title都包含相同关键词，status包括published、draft、archived
        user_id = uuid.uuid4()
        search_keyword = f"admin_all_{uuid.uuid4().hex[:6]}"
        
        published_topic = await create_test_topic(
            db,
            user_id=user_id,
            title=f"{search_keyword}_Published",
            status="published"
        )
        draft_topic = await create_test_topic(
            db,
            user_id=user_id,
            title=f"{search_keyword}_Draft",
            status="draft"
        )
        archived_topic = await create_test_topic(
            db,
            user_id=user_id,
            title=f"{search_keyword}_Archived",
            status="archived"
        )
        await db.commit()
        
        # Act: 使用Admin JWT Token认证
        response = await client.get(
            "/api/v1/topics",
            params={"title": search_keyword},
            headers={"Authorization": f"Bearer {admin_user_token}"}
        )
        
        # Assert
        assert response.status_code == 200, \
            f"期望HTTP状态码200，实际 {response.status_code}"
        
        data = response.json()
        assert data["code"] == 200, f"期望业务码200，实际 {data['code']}"
        
        items = data["data"]["items"]
        assert len(items) == 3, \
            f"Admin用户应该能看到所有3个专题，实际返回 {len(items)} 个"
        assert data["data"]["total"] == 3, \
            f"期望total为3，实际为 {data['data']['total']}"
        
        # 验证返回所有状态的专题
        topic_ids = [item["id"] for item in items]
        assert str(published_topic.id) in topic_ids, "Admin应该能看到published专题"
        assert str(draft_topic.id) in topic_ids, "Admin应该能看到draft专题"
        assert str(archived_topic.id) in topic_ids, "Admin应该能看到archived专题"
        
        # 验证状态分布
        statuses = [item["status"] for item in items]
        assert "published" in statuses, "应该包含published状态"
        assert "draft" in statuses, "应该包含draft状态"
        assert "archived" in statuses, "应该包含archived状态"

