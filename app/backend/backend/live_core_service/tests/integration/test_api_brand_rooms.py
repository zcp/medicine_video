"""
LiveCore Service - Brand Rooms API Integration Tests

This module contains integration tests for GET /api/v1/admin/brands/{brand_id}/rooms API endpoint.
Generated in incremental test mode.
"""

import uuid
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from faker import Faker

# 项目内导入
from app.core.config import settings
from tests.conftest import async_session_factory
from app.models.brand import Brand, BrandRoom
from app.models.live_core import LiveRoom
from app.schemas.brand import BrandCreate
from app.crud import brand as crud

# 初始化 Faker
fake = Faker()


# ==================== 辅助函数 (Helper Functions) ====================

async def create_test_brand(db: AsyncSession, **kwargs) -> Brand:
    """创建测试品牌的辅助函数"""
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


async def create_test_room(db: AsyncSession, **kwargs) -> LiveRoom:
    """创建测试直播间的辅助函数（外键依赖）"""
    room = LiveRoom(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        title=f"直播间_{fake.company()}_{uuid.uuid4().hex[:8]}",
        stream_key=f"stream_key_{uuid.uuid4().hex[:16]}",
        is_private=False,
        record_by_default=True,
        **kwargs
    )
    db.add(room)
    await db.flush()
    await db.commit()
    await db.refresh(room)
    return room


# ==================== Brand_Rooms API测试 ====================

@pytest.mark.asyncio
async def test_get_brand_rooms_api_success(async_client, db_session, admin_user_token):
    """测试获取品牌关联直播间列表API成功"""
    async for db in db_session:
        # ===== Arrange (准备) =====
        # 先创建品牌和多个直播间（外键依赖）
        brand = await create_test_brand(db)
        rooms = [await create_test_room(db) for _ in range(3)]
        room_ids = [r.id for r in rooms]
        
        # 建立关联
        for room_id in room_ids:
            brand_room = BrandRoom(
                brand_id=brand.id,
                room_id=room_id
            )
            db.add(brand_room)
        await db.commit()
        
        async for client in async_client:
            # ===== Act (执行) =====
            headers = {"Authorization": f"Bearer {admin_user_token}"}
            response = await client.get(
                f"/api/v1/admin/brands/{brand.id}/rooms?page=1&size=10",
                headers=headers
            )
            
            # ===== Assert (断言) =====
            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 200
            assert data["message"] == "success"
            assert "data" in data
            assert "total" in data["data"]
            assert data["data"]["total"] == 3
            assert "page" in data["data"]
            assert data["data"]["page"] == 1
            assert "size" in data["data"]
            assert data["data"]["size"] == 10
            assert "items" in data["data"]
            assert len(data["data"]["items"]) == 3
            
            # 验证返回的字段
            first_item = data["data"]["items"][0]
            assert "room_id" in first_item
            assert "room_title" in first_item
            assert "description" in first_item
            assert "is_private" in first_item
            assert "cover_url" in first_item
            assert "associated_at" in first_item
            
            # 验证返回的room_id在预期列表中
            returned_room_ids = [uuid.UUID(item["room_id"]) if isinstance(item["room_id"], str) else item["room_id"] for item in data["data"]["items"]]
            for room_id in room_ids:
                assert room_id in returned_room_ids, f"直播间ID {room_id} 应该出现在返回列表中"
            break
        break


@pytest.mark.asyncio
async def test_get_brand_rooms_api_pagination(async_client, db_session, admin_user_token):
    """测试获取品牌关联直播间列表API（分页功能）"""
    async for db in db_session:
        # ===== Arrange (准备) =====
        brand = await create_test_brand(db)
        rooms = [await create_test_room(db) for _ in range(10)]
        room_ids = [r.id for r in rooms]
        
        # 建立关联
        for room_id in room_ids:
            brand_room = BrandRoom(
                brand_id=brand.id,
                room_id=room_id
            )
            db.add(brand_room)
        await db.commit()
        
        async for client in async_client:
            headers = {"Authorization": f"Bearer {admin_user_token}"}
            
            # ===== Act (执行) =====
            # 第一页
            response1 = await client.get(
                f"/api/v1/admin/brands/{brand.id}/rooms?page=1&size=5",
                headers=headers
            )
            
            # 第二页
            response2 = await client.get(
                f"/api/v1/admin/brands/{brand.id}/rooms?page=2&size=5",
                headers=headers
            )
            
            # ===== Assert (断言) =====
            assert response1.status_code == 200
            assert response2.status_code == 200
            
            data1 = response1.json()
            data2 = response2.json()
            
            assert data1["data"]["total"] == 10
            assert data2["data"]["total"] == 10
            assert data1["data"]["page"] == 1
            assert data2["data"]["page"] == 2
            assert len(data1["data"]["items"]) == 5
            assert len(data2["data"]["items"]) == 5
            
            # 验证两页数据不重复
            page1_ids = {item["room_id"] for item in data1["data"]["items"]}
            page2_ids = {item["room_id"] for item in data2["data"]["items"]}
            assert page1_ids.isdisjoint(page2_ids), "两页数据不应该有重复"
            break
        break


@pytest.mark.asyncio
async def test_get_brand_rooms_api_permission_denied(async_client, db_session, regular_user_token):
    """测试获取品牌关联直播间列表API失败（权限不足）"""
    async for db in db_session:
        brand = await create_test_brand(db)
        
        async for client in async_client:
            # ===== Act (执行) =====
            headers = {"Authorization": f"Bearer {regular_user_token}"}
            response = await client.get(
                f"/api/v1/admin/brands/{brand.id}/rooms?page=1&size=10",
                headers=headers
            )
            
            # ===== Assert (断言) =====
            assert response.status_code == 403
            data = response.json()
            assert data["code"] == 3003
            assert "权限不足" in data["message"]
            break
        break


@pytest.mark.asyncio
async def test_get_brand_rooms_api_brand_not_found(async_client, db_session, admin_user_token):
    """测试获取品牌关联直播间列表API失败（品牌不存在）"""
    async for client in async_client:
        # ===== Arrange (准备) =====
        non_existent_brand_id = uuid.uuid4()
        
        # ===== Act (执行) =====
        headers = {"Authorization": f"Bearer {admin_user_token}"}
        response = await client.get(
            f"/api/v1/admin/brands/{non_existent_brand_id}/rooms?page=1&size=10",
            headers=headers
        )
        
        # ===== Assert (断言) =====
        assert response.status_code == 404
        data = response.json()
        assert data["code"] == 2001
        assert "品牌不存在" in data["message"]
        break


@pytest.mark.asyncio
async def test_get_brand_rooms_api_empty_result(async_client, db_session, admin_user_token):
    """测试获取品牌关联直播间列表API（空结果）"""
    async for db in db_session:
        # ===== Arrange (准备) =====
        brand = await create_test_brand(db)
        
        async for client in async_client:
            # ===== Act (执行) =====
            headers = {"Authorization": f"Bearer {admin_user_token}"}
            response = await client.get(
                f"/api/v1/admin/brands/{brand.id}/rooms?page=1&size=10",
                headers=headers
            )
            
            # ===== Assert (断言) =====
            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 200
            assert data["data"]["total"] == 0
            assert data["data"]["page"] == 1
            assert data["data"]["size"] == 10
            assert len(data["data"]["items"]) == 0
            break
        break


@pytest.mark.asyncio
async def test_get_brand_rooms_api_default_params(async_client, db_session, admin_user_token):
    """测试获取品牌关联直播间列表API（默认参数）"""
    async for db in db_session:
        brand = await create_test_brand(db)
        rooms = [await create_test_room(db) for _ in range(2)]
        
        # 建立关联
        for room in rooms:
            brand_room = BrandRoom(
                brand_id=brand.id,
                room_id=room.id
            )
            db.add(brand_room)
        await db.commit()
        
        async for client in async_client:
            # ===== Act (执行) =====
            headers = {"Authorization": f"Bearer {admin_user_token}"}
            response = await client.get(
                f"/api/v1/admin/brands/{brand.id}/rooms",
                headers=headers
            )
            
            # ===== Assert (断言) =====
            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 200
            # 验证默认参数：page=1, size=20
            assert data["data"]["page"] == 1
            assert data["data"]["size"] == 20
            break
        break


@pytest.mark.asyncio
async def test_get_brand_rooms_api_invalid_page_param(async_client, db_session, admin_user_token):
    """测试获取品牌关联直播间列表API（无效的page参数）"""
    async for db in db_session:
        brand = await create_test_brand(db)
        
        async for client in async_client:
            # ===== Act (执行) =====
            headers = {"Authorization": f"Bearer {admin_user_token}"}
            response = await client.get(
                f"/api/v1/admin/brands/{brand.id}/rooms?page=0&size=10",
                headers=headers
            )
            
            # ===== Assert (断言) =====
            # FastAPI会自动验证Query参数，page=0不符合ge=1的要求，应该返回422
            assert response.status_code == 422
            break
        break


@pytest.mark.asyncio
async def test_get_brand_rooms_api_invalid_size_param(async_client, db_session, admin_user_token):
    """测试获取品牌关联直播间列表API（无效的size参数）"""
    async for db in db_session:
        brand = await create_test_brand(db)
        
        async for client in async_client:
            # ===== Act (执行) =====
            headers = {"Authorization": f"Bearer {admin_user_token}"}
            response = await client.get(
                f"/api/v1/admin/brands/{brand.id}/rooms?page=1&size=101",
                headers=headers
            )
            
            # ===== Assert (断言) =====
            # FastAPI会自动验证Query参数，size=101不符合le=100的要求，应该返回422
            assert response.status_code == 422
            break
        break
