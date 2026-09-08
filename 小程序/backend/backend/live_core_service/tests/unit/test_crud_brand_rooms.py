"""
LiveCore Service - Brand Rooms CRUD Unit Tests

This module contains unit tests for get_brand_rooms_paginated CRUD operation.
Generated in incremental test mode.
"""

import uuid
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from faker import Faker

# 项目内导入
from app.crud import brand as crud
from app.models.brand import Brand, BrandRoom
from app.models.live_core import LiveRoom

# 初始化 Faker
fake = Faker()


# ==================== 辅助函数 (Helper Functions) ====================

async def create_test_brand(db: AsyncSession, **kwargs) -> Brand:
    """创建测试品牌的辅助函数"""
    from app.schemas.brand import BrandCreate
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
    return brand


async def create_test_room(db: AsyncSession, **kwargs) -> LiveRoom:
    """创建测试直播间的辅助函数（外键依赖）"""
    default_data = {
        "id": uuid.uuid4(),
        "user_id": uuid.uuid4(),
        "title": f"直播间_{fake.company()}_{uuid.uuid4().hex[:8]}",
        "stream_key": f"stream_key_{uuid.uuid4().hex[:16]}",
        "is_private": False,
        "record_by_default": True
    }
    room_data = {**default_data, **kwargs}
    room = LiveRoom(**room_data)
    db.add(room)
    await db.flush()
    return room


# ==================== Brand_Rooms CRUD测试 ====================

@pytest.mark.asyncio
async def test_get_brand_rooms_paginated_success(db_session):
    """测试获取品牌关联直播间列表（分页，增量验证）"""
    async for db in db_session:
        # ===== Arrange (准备) =====
        # 先创建品牌和多个直播间（外键依赖）
        brand = await create_test_brand(db)
        rooms = [await create_test_room(db) for _ in range(5)]
        room_ids = [r.id for r in rooms]
        
        # 建立关联（通过bind_room_brands，但需要为每个room单独绑定）
        # 注意：bind_room_brands是全量替换策略，所以需要逐个绑定或使用其他方法
        # 这里我们直接创建BrandRoom关联记录
        for room_id in room_ids:
            brand_room = BrandRoom(
                brand_id=brand.id,
                room_id=room_id
            )
            db.add(brand_room)
        await db.flush()
        await db.commit()
        
        # ===== Act (执行) =====
        room_list, total = await crud.get_brand_rooms_paginated(db, brand.id, page=1, size=10)
        
        # ===== Assert (断言) =====
        assert total == 5
        assert len(room_list) == 5
        returned_room_ids = [item['room_id'] for item in room_list]
        for room_id in room_ids:
            assert room_id in returned_room_ids, f"直播间ID {room_id} 应该出现在列表中"
        
        # 验证返回字段
        first_room = room_list[0]
        assert 'room_id' in first_room
        assert 'room_title' in first_room
        assert 'description' in first_room
        assert 'is_private' in first_room
        assert 'cover_url' in first_room
        assert 'associated_at' in first_room
        break


@pytest.mark.asyncio
async def test_get_brand_rooms_paginated_pagination(db_session):
    """测试获取品牌关联直播间列表（分页功能）"""
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
        await db.flush()
        await db.commit()
        
        # ===== Act (执行) =====
        # 第一页
        page1_list, total = await crud.get_brand_rooms_paginated(db, brand.id, page=1, size=5)
        
        # 第二页
        page2_list, total2 = await crud.get_brand_rooms_paginated(db, brand.id, page=2, size=5)
        
        # ===== Assert (断言) =====
        assert total == 10
        assert total2 == 10
        assert len(page1_list) == 5
        assert len(page2_list) == 5
        
        # 验证两页数据不重复
        page1_ids = {item['room_id'] for item in page1_list}
        page2_ids = {item['room_id'] for item in page2_list}
        assert page1_ids.isdisjoint(page2_ids), "两页数据不应该有重复"
        break


@pytest.mark.asyncio
async def test_get_brand_rooms_paginated_empty(db_session):
    """测试获取品牌关联直播间列表（空结果）"""
    async for db in db_session:
        # ===== Arrange (准备) =====
        brand = await create_test_brand(db)
        
        # ===== Act (执行) =====
        room_list, total = await crud.get_brand_rooms_paginated(db, brand.id, page=1, size=10)
        
        # ===== Assert (断言) =====
        assert total == 0
        assert len(room_list) == 0
        break


@pytest.mark.asyncio
async def test_get_brand_rooms_paginated_order_by_created_at_desc(db_session):
    """测试获取品牌关联直播间列表（按created_at降序排序）"""
    async for db in db_session:
        # ===== Arrange (准备) =====
        brand = await create_test_brand(db)
        rooms = [await create_test_room(db) for _ in range(3)]
        
        # 按顺序建立关联，记录时间
        association_times = []
        for i, room in enumerate(rooms):
            brand_room = BrandRoom(
                brand_id=brand.id,
                room_id=room.id
            )
            db.add(brand_room)
            await db.flush()
            # 获取created_at时间
            await db.refresh(brand_room)
            association_times.append((room.id, brand_room.created_at))
        
        await db.commit()
        
        # ===== Act (执行) =====
        room_list, total = await crud.get_brand_rooms_paginated(db, brand.id, page=1, size=10)
        
        # ===== Assert (断言) =====
        assert total == 3
        assert len(room_list) == 3
        
        # 验证排序：最新的关联应该在前（降序）
        # 由于是降序，最后一个关联的created_at应该最大，应该排在最前面
        if len(room_list) >= 2:
            # 验证associated_at字段存在且是降序
            associated_ats = [item['associated_at'] for item in room_list]
            # 验证是降序（最新的在前）
            for i in range(len(associated_ats) - 1):
                assert associated_ats[i] >= associated_ats[i + 1], "应该按created_at降序排列"
        break
