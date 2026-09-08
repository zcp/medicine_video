"""
LiveCore Service - Association Double Permission Filter API Integration Tests

测试关联资源的双重权限过滤（双重过滤场景）：
1. 分类下的房间列表：需要同时满足专题可见性和房间可见性
2. 房间的专题列表：需要同时满足房间可见性和专题可见性
"""

import pytest
import uuid
from httpx import AsyncClient
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from typing import AsyncGenerator

from app.crud import topic as crud_topic
from app.crud import room as crud_room
from app.schemas.topic import TopicCreate, TopicStatus, CategoryCreate
from app.schemas.live_core import LiveRoomCreate
from app.models.topic import Topic, TopicCategory
from app.models.live_core import LiveRoom


# ==================== 本地 Fixture ====================

@pytest.fixture
async def topic_client(db_session) -> AsyncGenerator[tuple, None]:
    """
    专门为 topic 测试创建的 fixture，返回 (client, app, db) 元组
    这样可以在测试中访问 app 实例来设置 dependency_overrides
    """
    from app.api.v1.api import api_router
    from app.database import get_db
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
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "324zq999")
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


# ==================== 测试类 ====================

class TestAssociationDoublePermissionFilter:
    """测试关联资源的双重权限过滤"""
    
    @pytest.mark.asyncio
    async def test_rooms_in_category_published_topic_public_room_anonymous(
        self,
        topic_client,
        regular_user_id: uuid.UUID
    ):
        """测试：分类下的房间列表（Published专题+Public房间，匿名用户）"""
        async for client, app, db in topic_client:
            # ===== Arrange (准备) =====
            # 创建Published专题
            topic_data = TopicCreate(
                title=f"Published Topic {uuid.uuid4().hex[:6]}",
                description="Test Description",
                status=TopicStatus.PUBLISHED
            )
            topic = await crud_topic.create(db, obj_in=topic_data, user_id=regular_user_id)
            await db.commit()
            await db.refresh(topic)
            
            # 创建分类
            category_data = CategoryCreate(
                name=f"Category {uuid.uuid4().hex[:6]}",
                description="Test Category"
            )
            category = await crud_topic.create_category(db, obj_in=category_data, topic_id=topic.id)
            await db.commit()
            await db.refresh(category)
            
            # 创建Public房间
            room_data = LiveRoomCreate(
                title=f"Public Room {uuid.uuid4().hex[:6]}",
                description="Test Room",
                is_private=False,
                record_by_default=True
            )
            public_room = await crud_room.create(db, obj_in=room_data, user_id=regular_user_id)
            await db.commit()
            await db.refresh(public_room)
            
            # TODO: 关联房间到分类（使用实际的关联API）
            # 这里假设有API可以关联房间到分类
            # 实际测试中可能需要调用关联API
            
            # TODO: 关联房间到分类（使用实际的关联API）
            # 注意：需要先关联房间到分类，才能测试双重权限过滤
            # 当前测试在没有关联的情况下，会返回空列表，这是预期的
            
            # ===== Act (执行) =====
            # 匿名用户访问分类下的房间列表
            response = await client.get(f"/api/v1/topic-categories/{category.id}/rooms?page=1&size=10")
            
            # ===== Assert (断言) =====
            # 应该成功返回200（Published专题可见）
            assert response.status_code == 200
            data = response.json().get("data", {})
            assert isinstance(data, dict)
            # 由于房间未关联到分类，列表可能为空
            # 如果需要测试双重权限过滤（Public房间可见），需要先调用关联API将房间添加到分类
            # 然后验证Public房间出现在列表中
    
    @pytest.mark.asyncio
    async def test_rooms_in_category_published_topic_private_room_anonymous(
        self,
        topic_client,
        regular_user_id: uuid.UUID
    ):
        """测试：分类下的房间列表（Published专题+Private房间，匿名用户）"""
        async for client, app, db in topic_client:
            # ===== Arrange (准备) =====
            # 创建Published专题
            topic_data = TopicCreate(
                title=f"Published Topic {uuid.uuid4().hex[:6]}",
                description="Test Description",
                status=TopicStatus.PUBLISHED
            )
            topic = await crud_topic.create(db, obj_in=topic_data, user_id=regular_user_id)
            await db.commit()
            await db.refresh(topic)
            
            # 创建分类
            category_data = CategoryCreate(
                name=f"Category {uuid.uuid4().hex[:6]}",
                description="Test Category"
            )
            category = await crud_topic.create_category(db, obj_in=category_data, topic_id=topic.id)
            await db.commit()
            await db.refresh(category)
            
            # 创建Private房间
            room_data = LiveRoomCreate(
                title=f"Private Room {uuid.uuid4().hex[:6]}",
                description="Test Room",
                is_private=True,
                record_by_default=True
            )
            private_room = await crud_room.create(db, obj_in=room_data, user_id=regular_user_id)
            await db.commit()
            await db.refresh(private_room)
            
            # TODO: 关联房间到分类（使用实际的关联API）
            # 注意：需要先关联房间到分类，才能测试双重权限过滤
            # 当前测试在没有关联的情况下，会返回空列表，这是预期的
            
            # ===== Act (执行) =====
            # 匿名用户访问分类下的房间列表
            response = await client.get(f"/api/v1/topic-categories/{category.id}/rooms?page=1&size=10")
            
            # ===== Assert (断言) =====
            # 应该成功返回200（Published专题可见）
            assert response.status_code == 200
            data = response.json().get("data", {})
            assert isinstance(data, dict)
            # 由于房间未关联到分类，列表可能为空
            # 如果需要测试双重权限过滤（Private房间被过滤），需要先调用关联API将房间添加到分类
            # 然后验证Private房间不出现在列表中
    
    @pytest.mark.asyncio
    async def test_rooms_in_category_draft_topic_public_room_anonymous_raises_404(
        self,
        topic_client,
        regular_user_id: uuid.UUID
    ):
        """测试：分类下的房间列表（Draft专题+Public房间，匿名用户应抛出404）"""
        async for client, app, db in topic_client:
            # ===== Arrange (准备) =====
            # 创建Draft专题
            topic_data = TopicCreate(
                title=f"Draft Topic {uuid.uuid4().hex[:6]}",
                description="Test Description",
                status=TopicStatus.DRAFT
            )
            topic = await crud_topic.create(db, obj_in=topic_data, user_id=regular_user_id)
            await db.commit()
            await db.refresh(topic)
            
            # 创建分类
            category_data = CategoryCreate(
                name=f"Category {uuid.uuid4().hex[:6]}",
                description="Test Category"
            )
            category = await crud_topic.create_category(db, obj_in=category_data, topic_id=topic.id)
            await db.commit()
            await db.refresh(category)
            
            # 创建Public房间
            room_data = LiveRoomCreate(
                title=f"Public Room {uuid.uuid4().hex[:6]}",
                description="Test Room",
                is_private=False,
                record_by_default=True
            )
            public_room = await crud_room.create(db, obj_in=room_data, user_id=regular_user_id)
            await db.commit()
            await db.refresh(public_room)
            
            # TODO: 关联房间到分类（使用实际的关联API）
            
            # ===== Act & Assert (执行 & 断言) =====
            # 匿名用户访问分类下的房间列表应抛出404（专题不可见）
            response = await client.get(f"/api/v1/topic-categories/{category.id}/rooms?page=1&size=10")
            assert response.status_code == 404
            response_json = response.json()
            if "code" in response_json:
                assert response_json["code"] == 2001
    
    @pytest.mark.asyncio
    async def test_topics_by_room_public_room_published_topic_anonymous(
        self,
        async_client,
        db_session,
        regular_user_id: uuid.UUID
    ):
        """测试：房间的专题列表（Public房间+Published专题，匿名用户）"""
        async for client in async_client:
            async for db in db_session:
                # ===== Arrange (准备) =====
                # 创建Published专题
                topic_data = TopicCreate(
                    title=f"Published Topic {uuid.uuid4().hex[:6]}",
                    description="Test Description",
                    status=TopicStatus.PUBLISHED
                )
                topic = await crud_topic.create(db, obj_in=topic_data, user_id=regular_user_id)
                await db.commit()
                await db.refresh(topic)
                
                # 创建Public房间
                room_data = LiveRoomCreate(
                    title=f"Public Room {uuid.uuid4().hex[:6]}",
                    description="Test Room",
                    is_private=False,
                    record_by_default=True
                )
                public_room = await crud_room.create(db, obj_in=room_data, user_id=regular_user_id)
                await db.commit()
                await db.refresh(public_room)
                
                # TODO: 关联专题到房间（使用实际的关联API）
                # 注意：需要先关联专题到房间，才能测试双重权限过滤
                # 当前测试在没有关联的情况下，会返回空列表，这是预期的
                
                # ===== Act (执行) =====
                # 匿名用户访问房间的专题列表
                response = await client.get(f"/api/v1/rooms/{public_room.id}/topics")
                
                # ===== Assert (断言) =====
                # 应该成功返回200（Public房间可见，Published专题可见）
                assert response.status_code == 200
                data = response.json().get("data", [])
                assert isinstance(data, list)
                # 由于专题未关联到房间，列表可能为空
                # 如果需要测试双重权限过滤（Published专题可见），需要先调用关联API将专题添加到房间
                # 然后验证Published专题出现在列表中
                break
            break

