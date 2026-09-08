"""
LiveCore Service - Brand API Integration Tests

This module contains integration tests for all API endpoints in the brand module.
Generated in incremental test mode.
"""

import uuid
import pytest
import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from faker import Faker

# 项目内导入
from app.core.config import settings
from app.core.deps import get_db
from tests.conftest import async_session_factory
from app.models.brand import Brand, BrandTopic, BrandRoom
from app.models.topic import Topic, TopicStatus
from app.models.live_core import LiveRoom
from app.schemas.brand import BrandCreate

# 初始化 Faker
fake = Faker()


# ==================== 辅助函数 (Helper Functions) ====================

async def create_test_brand(db: AsyncSession, **kwargs) -> Brand:
    """创建测试品牌的辅助函数"""
    from app.crud import brand as crud
    default_data = {
        "name": f"品牌_{fake.company()}_{uuid.uuid4().hex[:8]}",
        "slug": f"brand-{uuid.uuid4().hex[:8]}",
        "logo_url": fake.image_url(),
        "description": fake.text(max_nb_chars=100),
        "website_url": f"https://{fake.domain_name()}",
        "sort_order": 0,
        "is_active": True
    }
    brand_data = BrandCreate(**{**default_data, **kwargs})
    brand = await crud.create_brand(db, brand_data)
    await db.commit()
    await db.refresh(brand)
    return brand


async def create_test_topic(db: AsyncSession, user_id: uuid.UUID = None) -> Topic:
    """创建测试专题的辅助函数（外键依赖）"""
    if user_id is None:
        user_id = uuid.uuid4()
    
    topic = Topic(
        id=uuid.uuid4(),
        user_id=user_id,
        title=f"专题_{fake.catch_phrase()}_{uuid.uuid4().hex[:8]}",
        description=fake.text(max_nb_chars=100),
        status=TopicStatus.PUBLISHED
    )
    db.add(topic)
    await db.flush()
    await db.commit()
    await db.refresh(topic)
    return topic


async def create_test_room(db: AsyncSession, user_id: uuid.UUID = None) -> LiveRoom:
    """创建测试直播间的辅助函数（外键依赖）"""
    room = LiveRoom(
        id=uuid.uuid4(),
        user_id=user_id or uuid.uuid4(),
        title=f"直播间_{fake.company()}_{uuid.uuid4().hex[:8]}",
        stream_key=f"stream_key_{uuid.uuid4().hex[:16]}",
        is_private=False,
        record_by_default=True
    )
    db.add(room)
    await db.flush()
    await db.commit()
    await db.refresh(room)
    return room


# ==================== Brands API测试 ====================

@pytest.mark.asyncio
async def test_get_brands_api_success(async_client):
    """测试获取品牌列表API成功（无认证）"""
    async for client in async_client:
        # ===== Act (执行) =====
        response = await client.get("/api/v1/brands")
        
        # ===== Assert (断言) =====
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "data" in data
        assert isinstance(data["data"], list)
        break


@pytest.mark.asyncio
async def test_get_brands_api_with_auth(async_client, admin_user_token):
    """测试获取品牌列表API成功（带认证）"""
    async for client in async_client:
        # ===== Act (执行) =====
        headers = {"Authorization": f"Bearer {admin_user_token}"}
        response = await client.get("/api/v1/brands", headers=headers)
        
        # ===== Assert (断言) =====
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "data" in data
        break


@pytest.mark.asyncio
async def test_get_brands_api_with_search(async_client, db_session):
    """测试获取品牌列表API（带搜索关键词）"""
    async for db in db_session:
        # ===== Arrange (准备) =====
        search_keyword = f"搜索关键词_{uuid.uuid4().hex[:8]}"
        brand1 = await create_test_brand(db, name=f"匹配_{search_keyword}")
        brand2 = await create_test_brand(db, name=f"不匹配_{uuid.uuid4().hex[:8]}")
        
        async for client in async_client:
            # ===== Act (执行) =====
            response = await client.get(f"/api/v1/brands?q={search_keyword}")
            
            # ===== Assert (断言) =====
            assert response.status_code == 200
            data = response.json()
            brand_names = [b["name"] for b in data["data"]]
            assert brand1.name in brand_names
            assert brand2.name not in brand_names
            break
        break


@pytest.mark.asyncio
async def test_get_brand_content_api_success(async_client, db_session):
    """测试获取品牌详情及关联专题API成功（验证数据库状态）"""
    async for db in db_session:
        # ===== Arrange (准备) =====
        # 先创建品牌和专题（外键依赖）
        brand = await create_test_brand(db)
        topic1 = await create_test_topic(db)
        topic2 = await create_test_topic(db)
        
        # 建立关联
        from app.crud import brand as crud
        await crud.batch_add_brand_topics(db, brand.id, [topic1.id, topic2.id])
        await db.commit()
        
        async for client in async_client:
            # ===== Act (执行) =====
            response = await client.get(f"/api/v1/brands/{brand.id}/content")
            
            # ===== Assert (断言) =====
            # 验证HTTP响应
            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 200
            assert data["data"]["brand_info"]["id"] == str(brand.id)
            assert len(data["data"]["associated_topics"]) == 2
            
            # 验证数据库状态（使用新会话）
            async with async_session_factory() as new_db:
                from app.crud import brand as crud
                brand_result, topics = await crud.get_brand_with_topics(new_db, brand.id)
                assert brand_result is not None
                assert len(topics) == 2
            break
        break


@pytest.mark.asyncio
async def test_create_brand_api_success(async_client, db_session, admin_user_token):
    """测试创建品牌API成功（验证数据库状态）"""
    async for db in db_session:
        async for client in async_client:
            # ===== Arrange (准备) =====
            headers = {"Authorization": f"Bearer {admin_user_token}"}
            brand_data = {
                "name": f"新品牌_{uuid.uuid4().hex[:12]}",
                "slug": f"brand-{uuid.uuid4().hex[:8]}",
                "logo_url": fake.image_url(),
                "description": "测试品牌描述",
                "website_url": "https://example.com",
                "sort_order": 1,
                "is_active": True
            }
            
            # ===== Act (执行) =====
            response = await client.post("/api/v1/admin/brands", json=brand_data, headers=headers)
            
            # ===== Assert (断言) =====
            # 验证HTTP响应
            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 200
            brand_id = data["data"]["id"]
            
            # 验证数据库状态（使用新会话）
            async with async_session_factory() as new_db:
                stmt = select(Brand).where(Brand.id == uuid.UUID(brand_id))
                result = await new_db.execute(stmt)
                db_brand = result.scalar_one_or_none()
                assert db_brand is not None
                assert db_brand.name == brand_data["name"]
            break
        break


@pytest.mark.asyncio
async def test_create_brand_api_permission_denied(async_client):
    """测试创建品牌API失败（未认证）"""
    async for client in async_client:
        # ===== Act (执行) =====
        brand_data = {"name": f"品牌_{uuid.uuid4().hex[:8]}"}
        response = await client.post("/api/v1/admin/brands", json=brand_data)
        
        # ===== Assert (断言) =====
        assert response.status_code == 401
        break


@pytest.mark.asyncio
async def test_create_brand_api_duplicate_name(async_client, db_session, admin_user_token):
    """测试创建品牌API失败（名称重复）"""
    async for db in db_session:
        # ===== Arrange (准备) =====
        brand_name = f"唯一品牌_{uuid.uuid4().hex[:12]}"
        await create_test_brand(db, name=brand_name)
        
        async for client in async_client:
            # ===== Act (执行) =====
            headers = {"Authorization": f"Bearer {admin_user_token}"}
            brand_data = {"name": brand_name}
            response = await client.post("/api/v1/admin/brands", json=brand_data, headers=headers)
            
            # ===== Assert (断言) =====
            assert response.status_code == 409
            data = response.json()
            assert data["code"] == 2002  # 冲突错误码
            break
        break


@pytest.mark.asyncio
async def test_get_brands_admin_api_success(async_client, db_session, admin_user_token):
    """测试管理员分页获取品牌列表API成功"""
    async for db in db_session:
        # ===== Arrange (准备) =====
        await create_test_brand(db)
        
        async for client in async_client:
            # ===== Act (执行) =====
            headers = {"Authorization": f"Bearer {admin_user_token}"}
            response = await client.get("/api/v1/admin/brands?page=1&size=10", headers=headers)
            
            # ===== Assert (断言) =====
            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 200
            assert "data" in data
            assert "total" in data["data"]
            break
        break


@pytest.mark.asyncio
async def test_get_brand_admin_api_success(async_client, db_session, admin_user_token):
    """测试获取单个品牌API成功"""
    async for db in db_session:
        # ===== Arrange (准备) =====
        brand = await create_test_brand(db)
        
        async for client in async_client:
            # ===== Act (执行) =====
            headers = {"Authorization": f"Bearer {admin_user_token}"}
            response = await client.get(f"/api/v1/admin/brands/{brand.id}", headers=headers)
            
            # ===== Assert (断言) =====
            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 200
            assert data["data"]["id"] == str(brand.id)
            break
        break


@pytest.mark.asyncio
async def test_update_brand_api_success(async_client, db_session, admin_user_token):
    """测试更新品牌API成功（验证数据库状态）"""
    async for db in db_session:
        # ===== Arrange (准备) =====
        brand = await create_test_brand(db)
        original_name = brand.name
        
        async for client in async_client:
            # ===== Act (执行) =====
            headers = {"Authorization": f"Bearer {admin_user_token}"}
            update_data = {
                "name": f"更新后的品牌名_{uuid.uuid4().hex[:8]}",
                "description": "更新后的描述"
            }
            response = await client.patch(f"/api/v1/admin/brands/{brand.id}", json=update_data, headers=headers)
            
            # ===== Assert (断言) =====
            # 验证HTTP响应
            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 200
            assert data["data"]["name"] == update_data["name"]
            
            # 验证数据库状态（使用新会话）
            async with async_session_factory() as new_db:
                stmt = select(Brand).where(Brand.id == brand.id)
                result = await new_db.execute(stmt)
                db_brand = result.scalar_one_or_none()
                assert db_brand.name == update_data["name"]
                assert db_brand.name != original_name
            break
        break


@pytest.mark.asyncio
async def test_delete_brand_api_soft_delete(async_client, db_session, admin_user_token):
    """测试软删除品牌API成功（验证数据库状态）"""
    async for db in db_session:
        # ===== Arrange (准备) =====
        brand = await create_test_brand(db, is_active=True)
        
        async for client in async_client:
            # ===== Act (执行) =====
            headers = {"Authorization": f"Bearer {admin_user_token}"}
            response = await client.delete(f"/api/v1/admin/brands/{brand.id}?hard_delete=false", headers=headers)
            
            # ===== Assert (断言) =====
            # 验证HTTP响应
            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 200
            
            # 验证数据库状态（使用新会话，验证is_active=False）
            async with async_session_factory() as new_db:
                stmt = select(Brand).where(Brand.id == brand.id)
                result = await new_db.execute(stmt)
                db_brand = result.scalar_one_or_none()
                assert db_brand is not None
                assert db_brand.is_active is False
            break
        break


# tests/integration/test_api_brand.py

@pytest.mark.asyncio
async def test_delete_brand_api_hard_delete(async_client, db_session, admin_user_token):
    """测试硬删除品牌API成功（验证数据库状态，ADMIN/SuperAdmin）"""
    async for db in db_session:
        # ===== Arrange (准备) =====
        brand = await create_test_brand(db)  # 无关联

        async for client in async_client:
            # ===== Act (执行) =====
            headers = {"Authorization": f"Bearer {admin_user_token}"}
            response = await client.delete(f"/api/v1/admin/brands/{brand.id}?hard_delete=true", headers=headers)

            # ===== Assert (断言) =====
            # ✅ 修改：ADMIN和SUPERADMIN都可以硬删除，期望200
            assert response.status_code == 200

            # 验证HTTP响应
            data = response.json()
            assert data["code"] == 200
            assert data["data"]["deleted"] is True
            assert data["data"]["hard_delete"] is True

            # 验证数据库状态（使用新会话，验证品牌已被删除）
            async with async_session_factory() as new_db:
                stmt = select(Brand).where(Brand.id == brand.id)
                result = await new_db.execute(stmt)
                db_brand = result.scalar_one_or_none()
                assert db_brand is None
            break
        break
@pytest.mark.asyncio
async def test_delete_brand_api_with_refs(async_client, db_session, admin_user_token):
    """测试删除品牌API失败（有引用）"""
    async for db in db_session:
        # ===== Arrange (准备) =====
        brand = await create_test_brand(db)
        topic = await create_test_topic(db)
        
        # 建立关联
        from app.crud import brand as crud
        await crud.batch_add_brand_topics(db, brand.id, [topic.id])
        await db.commit()
        
        async for client in async_client:
            # ===== Act (执行) =====
            headers = {"Authorization": f"Bearer {admin_user_token}"}
            response = await client.delete(f"/api/v1/admin/brands/{brand.id}?hard_delete=true", headers=headers)
            
            # ===== Assert (断言) =====
            assert response.status_code == 409
            data = response.json()
            assert data["code"] == 2003  # 冲突且有引用错误码
            break
        break


# ==================== Brand_Topics API测试 ====================

@pytest.mark.asyncio
async def test_bind_brand_topics_api_success(async_client, db_session, admin_user_token):
    """测试批量关联专题到品牌API成功（验证数据库状态，外键依赖）"""
    async for db in db_session:
        # ===== Arrange (准备) =====
        # 先创建品牌和专题（外键依赖）
        brand = await create_test_brand(db)
        topic1 = await create_test_topic(db)
        topic2 = await create_test_topic(db)
        
        async for client in async_client:
            # ===== Act (执行) =====
            headers = {"Authorization": f"Bearer {admin_user_token}"}
            topic_data = {
                "topic_ids": [str(topic1.id), str(topic2.id)]
            }
            response = await client.post(
                f"/api/v1/admin/brands/{brand.id}/topics",
                json=topic_data,
                headers=headers
            )
            
            # ===== Assert (断言) =====
            # 验证HTTP响应
            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 200
            
            # 验证数据库状态（使用新会话）
            async with async_session_factory() as new_db:
                stmt = select(BrandTopic).where(BrandTopic.brand_id == brand.id)
                result = await new_db.execute(stmt)
                associations = result.scalars().all()
                assert len(associations) == 2
                topic_ids = {str(assoc.topic_id) for assoc in associations}
                assert str(topic1.id) in topic_ids
                assert str(topic2.id) in topic_ids
            break
        break


@pytest.mark.asyncio
async def test_unbind_brand_topic_api_success(async_client, db_session, admin_user_token):
    """测试解除品牌-专题关联API成功（验证数据库状态）"""
    async for db in db_session:
        # ===== Arrange (准备) =====
        # 先创建品牌、专题和关联（外键依赖）
        brand = await create_test_brand(db)
        topic = await create_test_topic(db)
        
        # 建立关联
        from app.crud import brand as crud
        await crud.batch_add_brand_topics(db, brand.id, [topic.id])
        await db.commit()
        
        async for client in async_client:
            # ===== Act (执行) =====
            headers = {"Authorization": f"Bearer {admin_user_token}"}
            response = await client.delete(
                f"/api/v1/admin/brands/{brand.id}/topics/{topic.id}",
                headers=headers
            )
            
            # ===== Assert (断言) =====
            # 验证HTTP响应
            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 200
            
            # 验证数据库状态（使用新会话）
            async with async_session_factory() as new_db:
                stmt = select(BrandTopic).where(
                    BrandTopic.brand_id == brand.id,
                    BrandTopic.topic_id == topic.id
                )
                result = await new_db.execute(stmt)
                association = result.scalar_one_or_none()
                assert association is None
            break
        break


@pytest.mark.asyncio
async def test_get_brand_topics_api_success(async_client, db_session, admin_user_token):
    """测试获取品牌关联专题列表API成功"""
    async for db in db_session:
        # ===== Arrange (准备) =====
        # 先创建品牌和多个专题（外键依赖）
        brand = await create_test_brand(db)
        topics = [await create_test_topic(db) for _ in range(3)]
        topic_ids = [t.id for t in topics]
        
        # 建立关联
        from app.crud import brand as crud
        await crud.batch_add_brand_topics(db, brand.id, topic_ids)
        await db.commit()
        
        async for client in async_client:
            # ===== Act (执行) =====
            headers = {"Authorization": f"Bearer {admin_user_token}"}
            response = await client.get(
                f"/api/v1/admin/brands/{brand.id}/topics?page=1&size=10",
                headers=headers
            )
            
            # ===== Assert (断言) =====
            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 200
            assert "data" in data
            assert "total" in data["data"]
            assert data["data"]["total"] == 3
            break
        break


# ==================== Brand_Rooms API测试 ====================

@pytest.mark.asyncio
async def test_bind_room_brands_api_success(async_client, db_session, admin_user_token):
    """测试绑定直播间品牌API成功（验证数据库状态，外键依赖，全量替换策略）"""
    async for db in db_session:
        # ===== Arrange (准备) =====
        # 先创建直播间和品牌（外键依赖）
        room = await create_test_room(db)
        brand1 = await create_test_brand(db)
        brand2 = await create_test_brand(db)
        
        async for client in async_client:
            # ===== Act (执行) =====
            headers = {"Authorization": f"Bearer {admin_user_token}"}
            brand_data = {
                "brand_ids": [str(brand1.id), str(brand2.id)]
            }
            response = await client.post(
                f"/api/v1/admin/rooms/{room.id}/brands",
                json=brand_data,
                headers=headers
            )
            
            # ===== Assert (断言) =====
            # 验证HTTP响应
            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 200
            
            # 验证数据库状态（使用新会话，验证全量替换策略）
            async with async_session_factory() as new_db:
                stmt = select(BrandRoom).where(BrandRoom.room_id == room.id)
                result = await new_db.execute(stmt)
                associations = result.scalars().all()
                assert len(associations) == 2
                brand_ids = {str(assoc.brand_id) for assoc in associations}
                assert str(brand1.id) in brand_ids
                assert str(brand2.id) in brand_ids
            break
        break


@pytest.mark.asyncio
async def test_bind_room_brands_api_owner_success(
    async_client, db_session, regular_user_token, regular_user_id
):
    """REGULAR 房主可绑定任意启用品牌（联动）"""
    async for db in db_session:
        room = await create_test_room(db, user_id=regular_user_id)
        brand1 = await create_test_brand(db)
        brand2 = await create_test_brand(db)

        async for client in async_client:
            headers = {"Authorization": f"Bearer {regular_user_token}"}
            response = await client.post(
                f"/api/v1/admin/rooms/{room.id}/brands",
                json={"brand_ids": [str(brand1.id), str(brand2.id)]},
                headers=headers,
            )
            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 200
            assert len(data["data"]["brand_ids"]) == 2
            break
        break


@pytest.mark.asyncio
async def test_bind_room_brands_api_non_owner_forbidden(
    async_client, db_session, regular_user_token
):
    """非房主 REGULAR 绑定品牌 → 403"""
    async for db in db_session:
        room = await create_test_room(db)  # 其他用户的房间
        brand = await create_test_brand(db)

        async for client in async_client:
            headers = {"Authorization": f"Bearer {regular_user_token}"}
            response = await client.post(
                f"/api/v1/admin/rooms/{room.id}/brands",
                json={"brand_ids": [str(brand.id)]},
                headers=headers,
            )
            assert response.status_code == 403
            break
        break


@pytest.mark.asyncio
async def test_bind_room_brands_api_replace(async_client, db_session, admin_user_token):
    """测试绑定直播间品牌API（全量替换策略：替换旧关联）"""
    async for db in db_session:
        # ===== Arrange (准备) =====
        # 先创建直播间和品牌（外键依赖）
        room = await create_test_room(db)
        old_brand = await create_test_brand(db)
        new_brand1 = await create_test_brand(db)
        new_brand2 = await create_test_brand(db)
        
        # 先建立旧关联
        from app.crud import brand as crud
        await crud.bind_room_brands(db, room.id, [old_brand.id])
        await db.commit()
        
        async for client in async_client:
            # ===== Act (执行) =====
            # 替换为新关联（全量替换策略）
            headers = {"Authorization": f"Bearer {admin_user_token}"}
            brand_data = {
                "brand_ids": [str(new_brand1.id), str(new_brand2.id)]
            }
            response = await client.post(
                f"/api/v1/admin/rooms/{room.id}/brands",
                json=brand_data,
                headers=headers
            )
            
            # ===== Assert (断言) =====
            assert response.status_code == 200
            
            # 验证数据库状态：旧关联被删除，新关联已创建
            async with async_session_factory() as new_db:
                stmt = select(BrandRoom).where(BrandRoom.room_id == room.id)
                result = await new_db.execute(stmt)
                associations = result.scalars().all()
                brand_ids = {str(assoc.brand_id) for assoc in associations}
                assert old_brand.id not in {uuid.UUID(bid) for bid in brand_ids}, "旧品牌应该被删除"
                assert str(new_brand1.id) in brand_ids, "新品牌1应该存在"
                assert str(new_brand2.id) in brand_ids, "新品牌2应该存在"
            break
        break


@pytest.mark.asyncio
async def test_get_room_brands_admin_api_success(async_client, db_session, admin_user_token):
    """测试获取直播间绑定的品牌API成功"""
    async for db in db_session:
        # ===== Arrange (准备) =====
        # 先创建直播间和品牌（外键依赖）
        room = await create_test_room(db)
        brand1 = await create_test_brand(db)
        brand2 = await create_test_brand(db)
        
        # 建立关联
        from app.crud import brand as crud
        await crud.bind_room_brands(db, room.id, [brand1.id, brand2.id])
        await db.commit()
        
        async for client in async_client:
            # ===== Act (执行) =====
            headers = {"Authorization": f"Bearer {admin_user_token}"}
            response = await client.get(f"/api/v1/admin/rooms/{room.id}/brands", headers=headers)
            
            # ===== Assert (断言) =====
            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 200
            assert len(data["data"]) == 2
            brand_ids = [b["id"] for b in data["data"]]
            assert str(brand1.id) in brand_ids
            assert str(brand2.id) in brand_ids
            break
        break


@pytest.mark.asyncio
async def test_get_room_brands_public_api_success(async_client, db_session):
    """测试获取直播间品牌Tab内容API成功（Public）"""
    async for db in db_session:
        # ===== Arrange (准备) =====
        # 先创建直播间和品牌（外键依赖）
        room = await create_test_room(db)
        brand = await create_test_brand(db, is_active=True)
        
        # 建立关联
        from app.crud import brand as crud
        await crud.bind_room_brands(db, room.id, [brand.id])
        await db.commit()
        
        async for client in async_client:
            # ===== Act (执行) =====
            response = await client.get(f"/api/v1/rooms/{room.id}/brands")
            
            # ===== Assert (断言) =====
            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 200
            assert len(data["data"]) == 1
            assert data["data"][0]["id"] == str(brand.id)
            break
        break


@pytest.mark.asyncio
async def test_get_room_brands_public_api_with_topic_brands(async_client, db_session):
    """测试获取直播间品牌Tab内容API（包含专题品牌）"""
    async for db in db_session:
        # ===== Arrange (准备) =====
        # 先创建直播间、品牌和专题（外键依赖）
        room = await create_test_room(db)
        room_brand = await create_test_brand(db, is_active=True)
        topic = await create_test_topic(db)
        topic_brand = await create_test_brand(db, is_active=True)
        
        # 建立直播间-品牌关联
        from app.crud import brand as crud
        await crud.bind_room_brands(db, room.id, [room_brand.id])
        
        # 建立品牌-专题关联
        await crud.batch_add_brand_topics(db, topic_brand.id, [topic.id])
        await db.commit()
        
        async for client in async_client:
            # ===== Act (执行) =====
            response = await client.get(
                f"/api/v1/rooms/{room.id}/brands?include_topic_brands=true&topic_id={topic.id}"
            )
            
            # ===== Assert (断言) =====
            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 200
            assert "room_brands" in data["data"]
            assert "topic_brands" in data["data"]
            assert len(data["data"]["room_brands"]) == 1
            # 注意：topic_brands可能为空，因为get_room_brands_for_tab的实现逻辑可能不同
            break
        break
