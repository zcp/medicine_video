"""
LiveCore Service - Brand CRUD Unit Tests

This module contains unit tests for all CRUD operations in app/crud/brand.py.
Generated in incremental test mode.
"""

import uuid
import pytest
from typing import List
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from faker import Faker

# 项目内导入
from app.crud import brand as crud
from app.models.brand import Brand, BrandTopic, BrandRoom
from app.schemas.brand import BrandCreate, BrandUpdate
from app.exceptions import DatabaseIntegrityException, NotFoundException
from app.models.topic import Topic, TopicStatus
from app.models.live_core import LiveRoom

# 初始化 Faker
fake = Faker()


# ==================== 辅助函数 (Helper Functions) ====================

# tests/unit/test_crud_brand.py

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
    brand = await crud.create_brand(db, brand_data)  # create_brand内部已经commit和refresh
    # ✅ 移除冗余的commit和refresh，因为CRUD函数已经处理了
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
    return topic


async def create_test_room(db: AsyncSession) -> LiveRoom:
    """创建测试直播间的辅助函数（外键依赖）"""
    room = LiveRoom(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        title=f"直播间_{fake.company()}_{uuid.uuid4().hex[:8]}",
        stream_key=f"stream_key_{uuid.uuid4().hex[:16]}",
        is_private=False,
        record_by_default=True
    )
    db.add(room)
    await db.flush()
    return room


# ==================== Brands CRUD测试 ====================

# tests/unit/test_crud_brand.py

# tests/unit/test_crud_brand.py (第83-104行)

# tests/unit/test_crud_brand.py (第85-110行)

@pytest.mark.asyncio
async def test_get_brands_success(db_session):
    """测试获取品牌列表（增量验证）"""
    async for db in db_session:
        # ===== Arrange (准备) =====
        # 记录测试前的记录数量（基线）
        count_stmt = select(func.count(Brand.id)).where(Brand.is_active == True)
        initial_result = await db.execute(count_stmt)
        initial_count = initial_result.scalar() or 0

        # 创建测试品牌（create_test_brand内部已commit）
        brand = await create_test_brand(db, is_active=True)

        # ✅ 提取品牌名称中的唯一标识符（UUID部分）用于搜索
        # 品牌名称格式：f"品牌_{fake.company()}_{uuid.uuid4().hex[:8]}"
        # 我们可以通过品牌名称的一部分（如完整的名称或UUID部分）进行搜索
        brand_name_unique_part = brand.name.split('_')[-1]  # 获取UUID部分

        # ===== Act (执行) =====
        # ✅ 方案1：使用 q 参数精确搜索新创建的品牌
        brands_with_search = await crud.get_brands(db, limit=100, q=brand_name_unique_part)

        # 同时获取总列表验证数量
        brands_all = await crud.get_brands(db, limit=100)

        # ===== Assert (断言) =====
        # 验证通过搜索能找到新创建的品牌
        brand_ids_from_search = [b.id for b in brands_with_search]
        assert brand.id in brand_ids_from_search, f"通过搜索应该能找到新创建的品牌: {brand.name}"

        # 验证总记录数增加了（如果数据库中记录数不超过100，则也在列表中）
        brand_ids_all = [b.id for b in brands_all]
        if initial_count < 100:
            # 如果初始记录数少于100，新记录应该在列表中
            assert brand.id in brand_ids_all, "新创建的品牌应该出现在列表中"

        # 验证记录数量增加了
        final_count_stmt = select(func.count(Brand.id)).where(Brand.is_active == True)
        final_result = await db.execute(final_count_stmt)
        final_count = final_result.scalar() or 0
        assert final_count == initial_count + 1, f"品牌数量应该增加1，基线={initial_count}，最终={final_count}"
        break

@pytest.mark.asyncio
async def test_get_brands_with_search(db_session):
    """测试获取品牌列表（带搜索关键词）"""
    async for db in db_session:
        # ===== Arrange (准备) =====
        search_keyword = f"搜索关键词_{uuid.uuid4().hex[:8]}"
        brand1 = await create_test_brand(db, name=f"匹配_{search_keyword}")
        brand2 = await create_test_brand(db, name=f"不匹配_{uuid.uuid4().hex[:8]}")
        
        # ===== Act (执行) =====
        brands = await crud.get_brands(db, limit=100, q=search_keyword)
        
        # ===== Assert (断言) =====
        brand_names = [b.name for b in brands]
        assert brand1.name in brand_names, "应该返回匹配的品牌"
        assert brand2.name not in brand_names, "不应该返回不匹配的品牌"
        break


@pytest.mark.asyncio
async def test_get_brands_limit(db_session):
    """测试获取品牌列表（限制数量）"""
    async for db in db_session:
        # ===== Arrange (准备) =====
        # 创建5个品牌
        for _ in range(5):
            await create_test_brand(db)
        
        # ===== Act (执行) =====
        brands = await crud.get_brands(db, limit=3)
        
        # ===== Assert (断言) =====
        assert len(brands) <= 3, "返回数量应该不超过limit"
        break


@pytest.mark.asyncio
async def test_get_brand_with_topics_success(db_session):
    """测试获取品牌及关联专题"""
    async for db in db_session:
        # ===== Arrange (准备) =====
        # 先创建品牌和专题（外键依赖）
        brand = await create_test_brand(db)
        topic1 = await create_test_topic(db)
        topic2 = await create_test_topic(db)
        
        # 建立关联
        await crud.batch_add_brand_topics(db, brand.id, [topic1.id, topic2.id])
        await db.flush()
        
        # ===== Act (执行) =====
        brand_result, topics = await crud.get_brand_with_topics(db, brand.id)
        
        # ===== Assert (断言) =====
        assert brand_result is not None
        assert brand_result.id == brand.id
        topic_ids = [t.id for t in topics]
        assert topic1.id in topic_ids, "应该包含关联的专题1"
        assert topic2.id in topic_ids, "应该包含关联的专题2"
        break


@pytest.mark.asyncio
async def test_get_brand_with_topics_not_found(db_session):
    """测试获取品牌及关联专题（品牌不存在）"""
    async for db in db_session:
        # ===== Arrange (准备) =====
        non_existent_id = uuid.uuid4()
        
        # ===== Act (执行) =====
        brand_result, topics = await crud.get_brand_with_topics(db, non_existent_id)
        
        # ===== Assert (断言) =====
        assert brand_result is None
        assert topics == []
        break


@pytest.mark.asyncio
async def test_create_brand_success(db_session):
    """测试创建品牌（增量验证）"""
    async for db in db_session:
        # ===== Arrange (准备) =====
        # 记录测试前的记录数量（基线）
        count_stmt = select(func.count(Brand.id))
        initial_result = await db.execute(count_stmt)
        initial_count = initial_result.scalar() or 0
        
        brand_data = BrandCreate(
            name=f"品牌_{uuid.uuid4().hex[:12]}",
            slug=f"brand-{uuid.uuid4().hex[:8]}",
            logo_url=fake.image_url(),
            description="测试品牌描述",
            website_url="https://example.com",
            sort_order=1,
            is_active=True
        )
        
        # ===== Act (执行) =====
        brand = await crud.create_brand(db, brand_data)
        await db.flush()
        await db.refresh(brand)
        
        # ===== Assert (断言) =====
        # 验证增量
        final_count_stmt = select(func.count(Brand.id))
        final_result = await db.execute(final_count_stmt)
        final_count = final_result.scalar() or 0
        assert final_count == initial_count + 1, f"记录数应该增加1，基线={initial_count}，实际={final_count}"
        
        # 验证对象属性
        assert brand.id is not None
        assert brand.name == brand_data.name
        assert brand.slug == brand_data.slug
        assert brand.is_active is True
        break


# tests/unit/test_crud_brand.py

# 修复 test_create_brand_duplicate_name
@pytest.mark.asyncio
async def test_create_brand_duplicate_name(db_session):
    """测试创建品牌失败（名称重复）"""
    async for db in db_session:
        # ===== Arrange (准备) =====
        brand_name = f"唯一品牌_{uuid.uuid4().hex[:12]}"

        # 创建第一条品牌
        brand1 = await create_test_brand(db, name=brand_name)  # create_test_brand内部已经commit

        # ===== Act (执行) =====
        # 尝试创建同名品牌
        brand2_data = BrandCreate(name=brand_name)

        # ===== Assert (断言) =====
        # ✅ 移除测试中的db.commit()，因为CRUD函数内部已经commit
        with pytest.raises(DatabaseIntegrityException) as exc_info:
            await crud.create_brand(db, brand2_data)  # 这里会commit并抛出异常

        assert "品牌名称已存在" in str(exc_info.value)
        break


# 修复 test_update_brand_duplicate_name
@pytest.mark.asyncio
async def test_update_brand_duplicate_name(db_session):
    """测试更新品牌失败（名称重复）"""
    async for db in db_session:
        # ===== Arrange (准备) =====
        brand_name = f"唯一品牌_{uuid.uuid4().hex[:12]}"
        brand1 = await create_test_brand(db, name=brand_name)  # 已commit
        brand2 = await create_test_brand(db, name=f"品牌2_{uuid.uuid4().hex[:8]}")  # 已commit

        # ===== Act (执行) =====
        brand_update = BrandUpdate(name=brand_name)

        # ===== Assert (断言) =====
        # ✅ 移除测试中的db.commit()，因为CRUD函数内部已经commit
        with pytest.raises(DatabaseIntegrityException) as exc_info:
            await crud.update_brand(db, brand2.id, brand_update)  # 这里会commit并抛出异常

        assert "品牌名称已存在" in str(exc_info.value)
        break


# tests/unit/test_crud_brand.py

# tests/unit/test_crud_brand.py (第279-297行)

@pytest.mark.asyncio
async def test_get_brands_paginated_with_filters(db_session):
    """测试分页获取品牌列表（带筛选条件）"""
    async for db in db_session:
        # ===== Arrange (准备) =====
        unique_id = uuid.uuid4().hex[:8]
        brand1_name = f"激活品牌_{unique_id}"
        brand2_name = f"禁用品牌_{unique_id}"

        brand1 = await create_test_brand(db, name=brand1_name, is_active=True)
        brand2 = await create_test_brand(db, name=brand2_name, is_active=False)

        # ===== Act (执行) =====
        # ✅ 修复：使用 name 参数精确搜索新创建的品牌，避免分页问题
        brands, total = await crud.get_brands_paginated(
            db,
            page=1,
            size=10,
            name=brand1_name,  # 精确搜索品牌1的名称
            is_active=True
        )

        # ===== Assert (断言) =====
        brand_names = [b.name for b in brands]
        assert brand1.name in brand_names, "应该包含激活的品牌"
        assert brand2.name not in brand_names, "不应该包含禁用的品牌"
        assert all(b.is_active is True for b in brands), "所有返回的品牌都应该是激活的"

        # ✅ 额外验证：测试禁用品牌的筛选
        brands_inactive, total_inactive = await crud.get_brands_paginated(
            db,
            page=1,
            size=10,
            name=brand2_name,
            is_active=False
        )
        assert brand2.name in [b.name for b in brands_inactive], "应该包含禁用的品牌"
        break

@pytest.mark.asyncio
async def test_get_brand_by_id_success(db_session):
    """测试根据ID获取品牌"""
    async for db in db_session:
        # ===== Arrange (准备) =====
        brand = await create_test_brand(db)
        
        # ===== Act (执行) =====
        result = await crud.get_brand_by_id(db, brand.id)
        
        # ===== Assert (断言) =====
        assert result is not None
        assert result.id == brand.id
        assert result.name == brand.name
        break


@pytest.mark.asyncio
async def test_get_brand_by_id_not_found(db_session):
    """测试根据ID获取品牌（不存在）"""
    async for db in db_session:
        # ===== Arrange (准备) =====
        non_existent_id = uuid.uuid4()
        
        # ===== Act (执行) =====
        result = await crud.get_brand_by_id(db, non_existent_id)
        
        # ===== Assert (断言) =====
        assert result is None
        break


@pytest.mark.asyncio
async def test_update_brand_success(db_session):
    """测试更新品牌"""
    async for db in db_session:
        # ===== Arrange (准备) =====
        brand = await create_test_brand(db)
        original_name = brand.name
        
        brand_update = BrandUpdate(
            name=f"更新后的品牌名_{uuid.uuid4().hex[:8]}",
            description="更新后的描述"
        )
        
        # ===== Act (执行) =====
        updated_brand = await crud.update_brand(db, brand.id, brand_update)
        await db.flush()
        await db.refresh(updated_brand)
        
        # ===== Assert (断言) =====
        assert updated_brand.name == brand_update.name
        assert updated_brand.description == brand_update.description
        assert updated_brand.name != original_name
        break



@pytest.mark.asyncio
async def test_delete_brand_soft_delete(db_session):
    """测试软删除品牌（增量验证）"""
    async for db in db_session:
        # ===== Arrange (准备) =====
        # 记录测试前的激活品牌数量（基线）
        count_stmt = select(func.count(Brand.id)).where(Brand.is_active == True)
        initial_result = await db.execute(count_stmt)
        initial_active_count = initial_result.scalar() or 0
        
        brand = await create_test_brand(db, is_active=True)
        
        # ===== Act (执行) =====
        deleted_brand = await crud.delete_brand(db, brand.id, hard_delete=False)
        await db.flush()
        await db.refresh(deleted_brand)
        
        # ===== Assert (断言) =====
        # 验证软删除：is_active应该为False
        assert deleted_brand.is_active is False
        
        # 验证增量：激活品牌数量应该减少
        final_result = await db.execute(count_stmt)
        final_active_count = final_result.scalar() or 0
        assert final_active_count == initial_active_count, f"激活品牌数量应该减少1，基线={initial_active_count}，实际={final_active_count}"
        break


@pytest.mark.asyncio
async def test_delete_brand_hard_delete(db_session):
    """测试硬删除品牌（增量验证，需要commit父记录）"""
    async for db in db_session:
        # ===== Arrange (准备) =====
        # 记录测试前的记录数量（基线）
        count_stmt = select(func.count(Brand.id))
        initial_result = await db.execute(count_stmt)
        initial_count = initial_result.scalar() or 0
        
        brand = await create_test_brand(db)
        await db.commit()  # ✅ commit父记录
        
        # ===== Act (执行) =====
        deleted_brand = await crud.delete_brand(db, brand.id, hard_delete=True)
        await db.flush()
        
        # ===== Assert (断言) =====
        # 验证增量：记录数应该减少
        final_result = await db.execute(count_stmt)
        final_count = final_result.scalar() or 0
        assert final_count == initial_count, f"记录数应该减少1，基线={initial_count}，实际={final_count}"
        
        # 验证品牌已被删除
        result = await crud.get_brand_by_id(db, brand.id)
        assert result is None
        break


@pytest.mark.asyncio
async def test_check_brand_references_no_refs(db_session):
    """测试检查品牌引用情况（无引用）"""
    async for db in db_session:
        # ===== Arrange (准备) =====
        brand = await create_test_brand(db)
        
        # ===== Act (执行) =====
        topic_count, room_count = await crud.check_brand_references(db, brand.id)
        
        # ===== Assert (断言) =====
        assert topic_count == 0
        assert room_count == 0
        break


@pytest.mark.asyncio
async def test_check_brand_references_with_topics(db_session):
    """测试检查品牌引用情况（有专题引用）"""
    async for db in db_session:
        # ===== Arrange (准备) =====
        brand = await create_test_brand(db)
        topic1 = await create_test_topic(db)
        topic2 = await create_test_topic(db)
        
        # 建立关联
        await crud.batch_add_brand_topics(db, brand.id, [topic1.id, topic2.id])
        await db.flush()
        
        # ===== Act (执行) =====
        topic_count, room_count = await crud.check_brand_references(db, brand.id)
        
        # ===== Assert (断言) =====
        assert topic_count == 2
        assert room_count == 0
        break


@pytest.mark.asyncio
async def test_check_brand_references_with_rooms(db_session):
    """测试检查品牌引用情况（有直播间引用）"""
    async for db in db_session:
        # ===== Arrange (准备) =====
        brand1 = await create_test_brand(db)
        brand2 = await create_test_brand(db)
        room = await create_test_room(db)
        
        # 建立关联
        await crud.bind_room_brands(db, room.id, [brand1.id, brand2.id])
        await db.flush()
        
        # ===== Act (执行) =====
        topic_count, room_count = await crud.check_brand_references(db, brand1.id)
        
        # ===== Assert (断言) =====
        assert topic_count == 0
        assert room_count == 1  # brand1被room引用
        break


# ==================== Brand_Topics CRUD测试 ====================

@pytest.mark.asyncio
async def test_batch_add_brand_topics_success(db_session):
    """测试批量添加品牌-专题关联（增量验证，外键依赖）"""
    async for db in db_session:
        # ===== Arrange (准备) =====
        # 先创建品牌和专题（外键依赖）
        brand = await create_test_brand(db)
        topic1 = await create_test_topic(db)
        topic2 = await create_test_topic(db)
        
        # 记录测试前的关联数量（基线）
        count_stmt = select(func.count(BrandTopic.brand_id)).where(BrandTopic.brand_id == brand.id)
        initial_result = await db.execute(count_stmt)
        initial_count = initial_result.scalar() or 0
        
        # ===== Act (执行) =====
        added_count = await crud.batch_add_brand_topics(db, brand.id, [topic1.id, topic2.id])
        await db.flush()
        
        # ===== Assert (断言) =====
        # 验证增量
        final_result = await db.execute(count_stmt)
        final_count = final_result.scalar() or 0
        assert final_count == initial_count + 2, f"关联数量应该增加2，基线={initial_count}，实际={final_count}"
        assert added_count == 2
        break


@pytest.mark.asyncio
async def test_batch_add_brand_topics_empty_list(db_session):
    """测试批量添加品牌-专题关联（空列表）"""
    async for db in db_session:
        # ===== Arrange (准备) =====
        brand = await create_test_brand(db)
        
        # ===== Act (执行) =====
        added_count = await crud.batch_add_brand_topics(db, brand.id, [])
        
        # ===== Assert (断言) =====
        assert added_count == 0
        break


@pytest.mark.asyncio
async def test_delete_brand_topic_success(db_session):
    """测试删除品牌-专题关联（增量验证，外键依赖）"""
    async for db in db_session:
        # ===== Arrange (准备) =====
        # 先创建品牌、专题和关联（外键依赖）
        brand = await create_test_brand(db)
        topic = await create_test_topic(db)
        
        await crud.batch_add_brand_topics(db, brand.id, [topic.id])
        await db.flush()
        
        # 记录测试前的关联数量（基线）
        count_stmt = select(func.count(BrandTopic.brand_id)).where(BrandTopic.brand_id == brand.id)
        initial_result = await db.execute(count_stmt)
        initial_count = initial_result.scalar() or 0
        
        # ===== Act (执行) =====
        success = await crud.delete_brand_topic(db, brand.id, topic.id)
        await db.flush()
        
        # ===== Assert (断言) =====
        assert success is True
        
        # 验证增量
        final_result = await db.execute(count_stmt)
        final_count = final_result.scalar() or 0
        assert final_count == initial_count - 1, f"关联数量应该减少1，基线={initial_count}，实际={final_count}"
        break


@pytest.mark.asyncio
async def test_delete_brand_topic_not_found(db_session):
    """测试删除品牌-专题关联（关联不存在）"""
    async for db in db_session:
        # ===== Arrange (准备) =====
        brand = await create_test_brand(db)
        topic = await create_test_topic(db)
        # 不创建关联
        
        # ===== Act (执行) =====
        success = await crud.delete_brand_topic(db, brand.id, topic.id)
        
        # ===== Assert (断言) =====
        assert success is False
        break


@pytest.mark.asyncio
async def test_get_brand_topics_paginated_success(db_session):
    """测试获取品牌关联专题列表（分页，增量验证）"""
    async for db in db_session:
        # ===== Arrange (准备) =====
        # 先创建品牌和多个专题（外键依赖）
        brand = await create_test_brand(db)
        topics = [await create_test_topic(db) for _ in range(5)]
        topic_ids = [t.id for t in topics]
        
        # 建立关联
        await crud.batch_add_brand_topics(db, brand.id, topic_ids)
        await db.flush()
        
        # ===== Act (执行) =====
        topic_list, total = await crud.get_brand_topics_paginated(db, brand.id, page=1, size=10)
        
        # ===== Assert (断言) =====
        assert total == 5
        assert len(topic_list) == 5
        returned_topic_ids = [item['topic_id'] for item in topic_list]
        for topic_id in topic_ids:
            assert topic_id in returned_topic_ids, f"专题ID {topic_id} 应该出现在列表中"
        break


# ==================== Brand_Rooms CRUD测试 ====================

@pytest.mark.asyncio
async def test_bind_room_brands_success(db_session):
    """测试绑定直播间品牌（增量验证，外键依赖，全量替换策略）"""
    async for db in db_session:
        # ===== Arrange (准备) =====
        # 先创建直播间和品牌（外键依赖）
        room = await create_test_room(db)
        brand1 = await create_test_brand(db)
        brand2 = await create_test_brand(db)
        
        # 记录测试前的关联数量（基线）
        count_stmt = select(func.count(BrandRoom.room_id)).where(BrandRoom.room_id == room.id)
        initial_result = await db.execute(count_stmt)
        initial_count = initial_result.scalar() or 0
        
        # ===== Act (执行) =====
        bound_ids = await crud.bind_room_brands(db, room.id, [brand1.id, brand2.id])
        
        # ===== Assert (断言) =====
        # 验证全量替换：应该只有2个关联
        final_result = await db.execute(count_stmt)
        final_count = final_result.scalar() or 0
        assert final_count == 2, f"应该正好有2个关联，实际={final_count}"
        assert len(bound_ids) == 2
        assert brand1.id in bound_ids
        assert brand2.id in bound_ids
        break


@pytest.mark.asyncio
async def test_bind_room_brands_replace(db_session):
    """测试绑定直播间品牌（全量替换策略：替换旧关联）"""
    async for db in db_session:
        # ===== Arrange (准备) =====
        # 先创建直播间和品牌（外键依赖）
        room = await create_test_room(db)
        old_brand = await create_test_brand(db)
        new_brand1 = await create_test_brand(db)
        new_brand2 = await create_test_brand(db)
        
        # 先建立旧关联
        await crud.bind_room_brands(db, room.id, [old_brand.id])
        await db.flush()
        
        # ===== Act (执行) =====
        # 替换为新关联（全量替换策略）
        bound_ids = await crud.bind_room_brands(db, room.id, [new_brand1.id, new_brand2.id])
        
        # ===== Assert (断言) =====
        # 验证旧关联已被删除，新关联已创建
        count_stmt = select(func.count(BrandRoom.room_id)).where(BrandRoom.room_id == room.id)
        final_result = await db.execute(count_stmt)
        final_count = final_result.scalar() or 0
        assert final_count == 2, "应该只有2个新关联"
        
        # 验证具体关联
        room_brands = await crud.get_room_brands(db, room.id)
        brand_ids = [b.id for b in room_brands]
        assert old_brand.id not in brand_ids, "旧品牌应该被删除"
        assert new_brand1.id in brand_ids, "新品牌1应该存在"
        assert new_brand2.id in brand_ids, "新品牌2应该存在"
        break


@pytest.mark.asyncio
async def test_get_room_brands_success(db_session):
    """测试获取直播间绑定的品牌列表"""
    async for db in db_session:
        # ===== Arrange (准备) =====
        # 先创建直播间和品牌（外键依赖）
        room = await create_test_room(db)
        brand1 = await create_test_brand(db)
        brand2 = await create_test_brand(db)
        
        # 建立关联
        await crud.bind_room_brands(db, room.id, [brand1.id, brand2.id])
        await db.flush()
        
        # ===== Act (执行) =====
        brands = await crud.get_room_brands(db, room.id)
        
        # ===== Assert (断言) =====
        assert len(brands) == 2
        brand_ids = [b.id for b in brands]
        assert brand1.id in brand_ids
        assert brand2.id in brand_ids
        break


@pytest.mark.asyncio
async def test_get_room_brands_for_tab_success(db_session):
    """测试获取直播间品牌Tab内容"""
    async for db in db_session:
        # ===== Arrange (准备) =====
        # 先创建直播间和品牌（外键依赖）
        room = await create_test_room(db)
        brand = await create_test_brand(db, is_active=True)
        
        # 建立关联
        await crud.bind_room_brands(db, room.id, [brand.id])
        await db.flush()
        
        # ===== Act (执行) =====
        brands = await crud.get_room_brands_for_tab(db, room.id)
        
        # ===== Assert (断言) =====
        assert len(brands) == 1
        assert brands[0].id == brand.id
        assert brands[0].is_active is True  # 只返回激活的品牌
        break
