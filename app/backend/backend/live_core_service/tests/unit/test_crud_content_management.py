"""
内容管理模块 - CRUD层测试
测试策略: Pragmatic (务实主义)
- 核心CRUD: 完整测试(正常+异常)
- 辅助CRUD: 正常路径测试
"""

import pytest
from uuid import uuid4, UUID
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.content_management import Tag, Category, SessionTag, LiveRoomCategory
from app.models.live_core import LiveRoom, LiveSession, LiveSessionStatus
from app.schemas.content_management import TagCreate, TagUpdate, CategoryCreate, CategoryUpdate
from app.crud.content_management import (
    # Tags CRUD
    get_tags,
    get_tag_by_name,
    create_tag,
    update_tag,
    delete_tag,
    # Categories CRUD
    get_categories,
    get_categories_paginated,
    create_category,
    update_category,
    delete_category,
    get_category_by_id,
    # Session_Tags CRUD
    set_session_tags,
    get_tags_by_session_id,
    get_sessions_by_tags,
    remove_session_tag,
    # Live_Room_Categories CRUD
    get_categories_by_room_id,
    set_live_room_categories,
    delete_live_room_category,
)
from app.core.exceptions import DatabaseIntegrityException


# ============================================================================
# 辅助函数
# ============================================================================

async def create_test_session(db: AsyncSession, session_id: UUID):
    """创建测试用的 LiveRoom 和 LiveSession"""
    # 创建房间
    room = LiveRoom(
        id=uuid4(),
        user_id=uuid4(),  # 必需字段
        title=f"测试房间_{uuid4().hex[:8]}",
        stream_key=f"stream_key_{uuid4().hex[:16]}",  # 必需字段
        is_private=False,
        record_by_default=True
    )
    db.add(room)
    await db.flush()

    # 创建场次
    session = LiveSession(
        id=session_id,
        room_id=room.id,
        status=LiveSessionStatus.FINISHED,
        start_time=datetime.now(),
        end_time=datetime.now()
    )
    db.add(session)
    await db.flush()
    return session


async def create_test_room(db: AsyncSession):
    """创建测试用的 LiveRoom（用于 Room_Categories 测试）"""
    room = LiveRoom(
        id=uuid4(),
        user_id=uuid4(),
        title=f"测试房间_{uuid4().hex[:8]}",
        stream_key=f"stream_key_{uuid4().hex[:16]}",
        is_private=False,
        record_by_default=True
    )
    db.add(room)
    await db.flush()
    return room


# ============================================================================
# Tags CRUD Tests
# ============================================================================

@pytest.mark.asyncio
async def test_get_tags_admin_all(db_session: AsyncSession):
    """测试管理员获取所有标签(is_active=None)"""
    async for db in db_session:
        # Arrange
        suffix = uuid4().hex[:8]
        tag1 = Tag(id=uuid4(), name=f"活跃标签_{suffix}", is_active=True)
        tag2 = Tag(id=uuid4(), name=f"禁用标签_{suffix}", is_active=False)
        db.add_all([tag1, tag2])
        await db.commit()

        # 获取数据库中现有的标签总数(包括可能的历史数据)
        count_query = select(Tag)
        count_result = await db.execute(count_query)
        initial_count = len(count_result.scalars().all())

        # Act
        result = await get_tags(db, is_active=None, current_user_id=None, role='ADMIN')

        # Assert
        assert len(result) == initial_count  # 管理员可查询所有标签
        tag_names = [tag.name for tag in result]
        assert f"活跃标签_{suffix}" in tag_names
        assert f"禁用标签_{suffix}" in tag_names


@pytest.mark.asyncio
async def test_get_tags_user_only_active(db_session: AsyncSession):
    """测试普通用户只能获取is_active=True的标签"""
    async for db in db_session:
        # Arrange
        suffix = uuid4().hex[:8]
        tag1 = Tag(id=uuid4(), name=f"活跃标签_{suffix}", is_active=True)
        tag2 = Tag(id=uuid4(), name=f"禁用标签_{suffix}", is_active=False)
        db.add_all([tag1, tag2])
        await db.commit()

        # 获取数据库中is_active=True的标签总数
        count_query = select(Tag).where(Tag.is_active == True)
        count_result = await db.execute(count_query)
        initial_active_count = len(count_result.scalars().all())

        # Act
        result = await get_tags(db, is_active=None, current_user_id=None, role='USER')

        # Assert
        assert len(result) == initial_active_count  # 普通用户只能查询活跃标签
        tag_names = [tag.name for tag in result]
        assert f"活跃标签_{suffix}" in tag_names
        assert f"禁用标签_{suffix}" not in tag_names


@pytest.mark.asyncio
async def test_create_tag_success(db_session: AsyncSession):
    """测试创建标签成功"""
    async for db in db_session:
        # Arrange
        suffix = uuid4().hex[:8]
        tag_name = f"新标签_{suffix}"
        tag_data = TagCreate(
            name=tag_name,
            slug=f"new-tag-{suffix}",
            description="测试描述",
            is_active=True
        )

        # Act
        result = await create_tag(db, tag_data)
        await db.commit()

        # Assert
        assert result.name == tag_name
        assert result.slug == f"new-tag-{suffix}"
        assert result.is_active is True
        assert result.id is not None
        assert isinstance(result.created_at, datetime)


@pytest.mark.asyncio
async def test_create_tag_duplicate_name(db_session: AsyncSession):
    """测试创建重名标签失败(唯一性约束)"""
    async for db in db_session:
        # Arrange
        tag_name = f"重复标签_{uuid4().hex[:8]}"
        existing_tag = Tag(id=uuid4(), name=tag_name, is_active=True)
        db.add(existing_tag)
        await db.commit()

        tag_data = TagCreate(name=tag_name, is_active=True)

        # Act & Assert
        with pytest.raises(DatabaseIntegrityException, match="标签名称已存在"):
            await create_tag(db, tag_data)


@pytest.mark.asyncio
async def test_update_tag_success(db_session: AsyncSession):
    """测试更新标签成功"""
    async for db in db_session:
        # Arrange
        suffix = uuid4().hex[:8]
        tag = Tag(id=uuid4(), name=f"旧名称_{suffix}", is_active=True)
        db.add(tag)
        await db.commit()

        update_data = TagUpdate(name=f"新名称_{suffix}", description="新描述")

        # Act
        result = await update_tag(db, tag.id, update_data)
        await db.commit()

        # Assert
        assert result is not None
        assert result.name == f"新名称_{suffix}"
        assert result.description == "新描述"


@pytest.mark.asyncio
async def test_update_tag_not_found(db_session: AsyncSession):
    """测试更新不存在的标签返回None"""
    async for db in db_session:
        # Arrange
        non_existent_id = uuid4()
        update_data = TagUpdate(name=f"新名称_{uuid4().hex[:8]}")

        # Act
        result = await update_tag(db, non_existent_id, update_data)

        # Assert
        assert result is None


@pytest.mark.asyncio
async def test_delete_tag_soft_delete(db_session: AsyncSession):
    """测试软删除标签(设置is_active=False)"""
    async for db in db_session:
        # Arrange
        tag = Tag(id=uuid4(), name=f"待删除标签_{uuid4().hex[:8]}", is_active=True)
        db.add(tag)
        await db.commit()

        # Act
        result = await delete_tag(db, tag.id)
        await db.commit()

        # Assert
        assert result is True

        # 验证标签仍存在但is_active=False
        await db.refresh(tag)
        assert tag.is_active is False


# ============================================================================
# Categories CRUD Tests
# ============================================================================

@pytest.mark.asyncio
async def test_get_categories_only_active(db_session: AsyncSession):
    """测试get_categories只返回is_active=True且非孤儿的分类"""
    async for db in db_session:
        # Arrange
        suffix = uuid4().hex[:8]
        cat1 = Category(id=uuid4(), name=f"活跃分类_{suffix}", sort_order=1, is_active=True)
        cat2 = Category(id=uuid4(), name=f"禁用分类_{suffix}", sort_order=2, is_active=False)
        db.add_all([cat1, cat2])
        await db.commit()

        # Act
        result = await get_categories(db, current_user_id=None, role=None)

        # Assert
        # 阶段1 防御过滤：返回的均为 active 且无孤儿（父不可见的子分类不返回）
        assert all(c.is_active for c in result)
        active_ids = {c.id for c in result}
        assert all(c.parent_id is None or c.parent_id in active_ids for c in result)
        cat_names = [cat.name for cat in result]
        assert f"活跃分类_{suffix}" in cat_names
        assert f"禁用分类_{suffix}" not in cat_names


@pytest.mark.asyncio
async def test_get_categories_paginated_admin(db_session: AsyncSession):
    """测试管理员分页查询分类"""
    async for db in db_session:
        # Arrange
        suffix = uuid4().hex[:8]
        cat1 = Category(id=uuid4(), name=f"分类1_{suffix}", sort_order=1, is_active=True)
        cat2 = Category(id=uuid4(), name=f"分类2_{suffix}", sort_order=2, is_active=False)
        db.add_all([cat1, cat2])
        await db.commit()

        # 获取数据库中所有分类总数
        count_query = select(Category)
        count_result = await db.execute(count_query)
        initial_count = len(count_result.scalars().all())

        # Act
        categories, total = await get_categories_paginated(
            db, page=1, size=10, is_active=None,
            current_user_id=None, role='ADMIN'
        )

        # Assert
        assert total == initial_count
        assert len(categories) <= 10


@pytest.mark.asyncio
async def test_create_category_success(db_session: AsyncSession):
    """测试创建分类成功"""
    async for db in db_session:
        # Arrange
        suffix = uuid4().hex[:8]
        category_data = CategoryCreate(
            name=f"新分类_{suffix}",
            slug=f"new-category-{suffix}",
            icon="icon.png",
            description="测试分类",
            sort_order=10,
            is_active=True
        )

        # Act
        result = await create_category(db, category_data)
        await db.commit()

        # Assert
        assert result.name == f"新分类_{suffix}"
        assert result.sort_order == 10
        assert result.is_active is True


@pytest.mark.asyncio
async def test_create_category_duplicate_name(db_session: AsyncSession):
    """测试创建重名分类失败"""
    async for db in db_session:
        # Arrange
        cat_name = f"重复分类_{uuid4().hex[:8]}"
        existing_cat = Category(id=uuid4(), name=cat_name, sort_order=1, is_active=True)
        db.add(existing_cat)
        await db.commit()

        category_data = CategoryCreate(name=cat_name, sort_order=2, is_active=True)

        # Act & Assert
        with pytest.raises(DatabaseIntegrityException, match="分类名称已存在"):
            await create_category(db, category_data)


@pytest.mark.asyncio
async def test_get_category_by_id_found(db_session: AsyncSession):
    """测试根据ID获取分类成功"""
    async for db in db_session:
        # Arrange
        category = Category(id=uuid4(), name=f"测试分类_{uuid4().hex[:8]}", sort_order=1, is_active=True)
        db.add(category)
        await db.commit()

        # Act
        result = await get_category_by_id(db, category.id)

        # Assert
        assert result is not None
        assert result.id == category.id
        assert result.name == category.name


@pytest.mark.asyncio
async def test_get_category_by_id_not_found(db_session: AsyncSession):
    """测试获取不存在的分类返回None"""
    async for db in db_session:
        # Arrange
        non_existent_id = uuid4()
        
        # Act
        result = await get_category_by_id(db, non_existent_id)
        
        # Assert
        assert result is None


# ============================================================================
# Session_Tags CRUD Tests
# ============================================================================

@pytest.mark.asyncio
async def test_set_session_tags_replace_mode(db_session: AsyncSession):
    """测试替换模式设置场次标签"""
    async for db in db_session:
        # Arrange
        session_id = uuid4()
        suffix = uuid4().hex[:8]
        tag1 = Tag(id=uuid4(), name=f"标签1_{suffix}", is_active=True)
        tag2 = Tag(id=uuid4(), name=f"标签2_{suffix}", is_active=True)
        db.add_all([tag1, tag2])
        await db.commit()

        # 创建测试需要的 LiveRoom 和 LiveSession
        await create_test_session(db, session_id)

        # Act
        result = await set_session_tags(
            db, session_id, [tag1.id, tag2.id], mode="replace"
        )
        await db.commit()

        # Assert
        assert len(result) == 2
        result_ids = [tag.id for tag in result]
        assert tag1.id in result_ids
        assert tag2.id in result_ids


@pytest.mark.asyncio
async def test_set_session_tags_append_mode(db_session: AsyncSession):
    """测试追加模式设置场次标签"""
    async for db in db_session:
        # Arrange
        session_id = uuid4()
        suffix = uuid4().hex[:8]
        tag1 = Tag(id=uuid4(), name=f"标签1_{suffix}", is_active=True)
        tag2 = Tag(id=uuid4(), name=f"标签2_{suffix}", is_active=True)
        tag3 = Tag(id=uuid4(), name=f"标签3_{suffix}", is_active=True)
        db.add_all([tag1, tag2, tag3])
        await db.commit()

        # 创建测试需要的 LiveRoom 和 LiveSession
        await create_test_session(db, session_id)

        # 先设置tag1
        await set_session_tags(db, session_id, [tag1.id], mode="replace")
        await db.commit()

        # Act: 追加tag2和tag3
        result = await set_session_tags(
            db, session_id, [tag2.id, tag3.id], mode="append"
        )
        await db.commit()

        # Assert
        assert len(result) == 3  # 应包含tag1, tag2, tag3


@pytest.mark.asyncio
async def test_get_tags_by_session_id(db_session: AsyncSession):
    """测试获取场次标签列表"""
    async for db in db_session:
        # Arrange
        session_id = uuid4()
        suffix = uuid4().hex[:8]
        tag1 = Tag(id=uuid4(), name=f"标签1_{suffix}", is_active=True)
        tag2 = Tag(id=uuid4(), name=f"标签2_{suffix}", is_active=False)  # 禁用标签
        db.add_all([tag1, tag2])
        await db.commit()

        # 创建测试需要的 LiveRoom 和 LiveSession
        await create_test_session(db, session_id)

        # 设置场次标签
        session_tag1 = SessionTag(session_id=session_id, tag_id=tag1.id)
        session_tag2 = SessionTag(session_id=session_id, tag_id=tag2.id)
        db.add_all([session_tag1, session_tag2])
        await db.commit()

        # Act
        result = await get_tags_by_session_id(db, session_id)

        # Assert
        assert len(result) == 1  # 只返回is_active=True的标签
        assert result[0].id == tag1.id


@pytest.mark.asyncio
async def test_get_sessions_by_tags_or_logic(db_session: AsyncSession):
    """测试根据标签查询场次(OR逻辑)"""
    async for db in db_session:
        # Arrange
        suffix = uuid4().hex[:8]
        tag1 = Tag(id=uuid4(), name=f"标签1_{suffix}", is_active=True)
        tag2 = Tag(id=uuid4(), name=f"标签2_{suffix}", is_active=True)
        db.add_all([tag1, tag2])
        await db.commit()

        session1_id = uuid4()
        session2_id = uuid4()

        # 创建两个测试需要的 LiveSession
        await create_test_session(db, session1_id)
        await create_test_session(db, session2_id)

        # session1有tag1, session2有tag2
        session_tag1 = SessionTag(session_id=session1_id, tag_id=tag1.id)
        session_tag2 = SessionTag(session_id=session2_id, tag_id=tag2.id)
        db.add_all([session_tag1, session_tag2])
        await db.commit()

        # Act
        result = await get_sessions_by_tags(db, [tag1.id, tag2.id], match_all=False)

        # Assert
        assert len(result) == 2  # OR逻辑，两个场次都应返回
        assert session1_id in result
        assert session2_id in result


@pytest.mark.asyncio
async def test_get_sessions_by_tags_and_logic(db_session: AsyncSession):
    """测试根据标签查询场次(AND逻辑)"""
    async for db in db_session:
        # Arrange
        suffix = uuid4().hex[:8]
        tag1 = Tag(id=uuid4(), name=f"标签1_{suffix}", is_active=True)
        tag2 = Tag(id=uuid4(), name=f"标签2_{suffix}", is_active=True)
        db.add_all([tag1, tag2])
        await db.commit()

        session1_id = uuid4()
        session2_id = uuid4()

        # 创建两个测试需要的 LiveSession
        await create_test_session(db, session1_id)
        await create_test_session(db, session2_id)

        # session1有tag1和tag2, session2只有tag1
        session_tag1 = SessionTag(session_id=session1_id, tag_id=tag1.id)
        session_tag2 = SessionTag(session_id=session1_id, tag_id=tag2.id)
        session_tag3 = SessionTag(session_id=session2_id, tag_id=tag1.id)
        db.add_all([session_tag1, session_tag2, session_tag3])
        await db.commit()

        # Act
        result = await get_sessions_by_tags(db, [tag1.id, tag2.id], match_all=True)

        # Assert
        assert len(result) == 1  # AND逻辑，只有session1同时包含两个标签
        assert session1_id in result


@pytest.mark.asyncio
async def test_remove_session_tag_success(db_session: AsyncSession):
    """测试删除场次标签关联成功"""
    async for db in db_session:
        # Arrange
        session_id = uuid4()
        tag = Tag(id=uuid4(), name=f"标签1_{uuid4().hex[:8]}", is_active=True)
        db.add(tag)
        await db.commit()

        # 创建测试需要的 LiveRoom 和 LiveSession
        await create_test_session(db, session_id)

        session_tag = SessionTag(session_id=session_id, tag_id=tag.id)
        db.add(session_tag)
        await db.commit()

        # Act
        result = await remove_session_tag(db, session_id, tag.id)
        await db.commit()

        # Assert
        assert result is True

        # 验证关联已删除
        query = select(SessionTag).where(
            SessionTag.session_id == session_id,
            SessionTag.tag_id == tag.id
        )
        db_result = await db.execute(query)
        assert db_result.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_remove_session_tag_not_found(db_session: AsyncSession):
    """测试删除不存在的场次标签关联返回False"""
    async for db in db_session:
        # Arrange
        session_id = uuid4()
        tag_id = uuid4()
        
        # Act
        result = await remove_session_tag(db, session_id, tag_id)
        
        # Assert
        assert result is False


# ============================================================================
# Room_Categories CRUD Tests (增量)
# ============================================================================

@pytest.mark.asyncio
async def test_get_categories_by_room_id_success(db_session: AsyncSession):
    """测试根据直播间ID获取已启用分类列表"""
    async for db in db_session:
        # Arrange
        room = await create_test_room(db)
        c1 = Category(id=uuid4(), name=f"分类_{uuid4().hex[:8]}", sort_order=0, is_active=True)
        c2 = Category(id=uuid4(), name=f"分类_{uuid4().hex[:8]}", sort_order=1, is_active=True)
        db.add_all([c1, c2])
        await db.flush()
        db.add_all([
            LiveRoomCategory(room_id=room.id, category_id=c1.id),
            LiveRoomCategory(room_id=room.id, category_id=c2.id),
        ])
        await db.commit()

        # Act
        result = await get_categories_by_room_id(db, room.id)

        # Assert
        assert len(result) == 2
        ids = {lrc.category.id for lrc in result}
        assert c1.id in ids and c2.id in ids
        assert all(lrc.category.is_active for lrc in result)


@pytest.mark.asyncio
async def test_get_categories_by_room_id_empty(db_session: AsyncSession):
    """测试无关联时返回空列表"""
    async for db in db_session:
        room = await create_test_room(db)
        await db.commit()

        result = await get_categories_by_room_id(db, room.id)

        assert result == []


@pytest.mark.asyncio
async def test_get_categories_by_room_id_excludes_inactive(db_session: AsyncSession):
    """测试只返回 is_active=True 的分类"""
    async for db in db_session:
        room = await create_test_room(db)
        c_active = Category(id=uuid4(), name=f"活跃_{uuid4().hex[:8]}", sort_order=0, is_active=True)
        c_inactive = Category(id=uuid4(), name=f"禁用_{uuid4().hex[:8]}", sort_order=1, is_active=False)
        db.add_all([c_active, c_inactive])
        await db.flush()
        db.add_all([
            LiveRoomCategory(room_id=room.id, category_id=c_active.id),
            LiveRoomCategory(room_id=room.id, category_id=c_inactive.id),
        ])
        await db.commit()

        result = await get_categories_by_room_id(db, room.id)

        assert len(result) == 1
        assert result[0].category.id == c_active.id
        assert result[0].category.is_active is True


@pytest.mark.asyncio
async def test_set_live_room_categories_replace_mode(db_session: AsyncSession):
    """测试 replace 模式：先删后插，最终仅包含新列表"""
    async for db in db_session:
        room = await create_test_room(db)
        c1 = Category(id=uuid4(), name=f"分类1_{uuid4().hex[:8]}", sort_order=0, is_active=True)
        c2 = Category(id=uuid4(), name=f"分类2_{uuid4().hex[:8]}", sort_order=1, is_active=True)
        c3 = Category(id=uuid4(), name=f"分类3_{uuid4().hex[:8]}", sort_order=2, is_active=True)
        db.add_all([c1, c2, c3])
        await db.flush()
        db.add_all([
            LiveRoomCategory(room_id=room.id, category_id=c1.id),
            LiveRoomCategory(room_id=room.id, category_id=c2.id),
        ])
        await db.commit()

        result = await set_live_room_categories(db, room.id, [c3.id], "replace")

        assert len(result) == 1
        assert result[0].category.id == c3.id


@pytest.mark.asyncio
async def test_set_live_room_categories_append_mode(db_session: AsyncSession):
    """测试 append 模式：仅追加，已存在则忽略"""
    async for db in db_session:
        room = await create_test_room(db)
        c1 = Category(id=uuid4(), name=f"分类1_{uuid4().hex[:8]}", sort_order=0, is_active=True)
        c2 = Category(id=uuid4(), name=f"分类2_{uuid4().hex[:8]}", sort_order=1, is_active=True)
        c3 = Category(id=uuid4(), name=f"分类3_{uuid4().hex[:8]}", sort_order=2, is_active=True)
        db.add_all([c1, c2, c3])
        await db.flush()
        db.add(LiveRoomCategory(room_id=room.id, category_id=c1.id))
        await db.commit()

        result = await set_live_room_categories(db, room.id, [c2.id, c3.id], "append")

        assert len(result) == 3
        ids = {lrc.category.id for lrc in result}
        assert c1.id in ids and c2.id in ids and c3.id in ids


@pytest.mark.asyncio
async def test_set_live_room_categories_integrity_error(db_session: AsyncSession):
    """测试外键不存在时抛出 DatabaseIntegrityException"""
    async for db in db_session:
        room = await create_test_room(db)
        await db.commit()
        fake_category_id = uuid4()  # 不存在的分类ID

        with pytest.raises(DatabaseIntegrityException, match="直播间或分类不存在"):
            await set_live_room_categories(db, room.id, [fake_category_id], "replace")


@pytest.mark.asyncio
async def test_delete_live_room_category_success(db_session: AsyncSession):
    """测试删除直播间分类关联成功"""
    async for db in db_session:
        room = await create_test_room(db)
        c1 = Category(id=uuid4(), name=f"分类_{uuid4().hex[:8]}", sort_order=0, is_active=True)
        db.add(c1)
        await db.flush()
        db.add(LiveRoomCategory(room_id=room.id, category_id=c1.id))
        await db.commit()

        result = await delete_live_room_category(db, room.id, c1.id)
        await db.flush()

        assert result is True
        cats = await get_categories_by_room_id(db, room.id)
        assert len(cats) == 0


@pytest.mark.asyncio
async def test_delete_live_room_category_not_found(db_session: AsyncSession):
    """测试删除不存在的关联返回 False"""
    async for db in db_session:
        room = await create_test_room(db)
        category_id = uuid4()
        await db.commit()

        result = await delete_live_room_category(db, room.id, category_id)

        assert result is False


# ============================================================================
# Categories / Tags 列表搜索（q / search_type）增量 CRUD 测试
# ============================================================================

@pytest.mark.asyncio
async def test_get_categories_paginated_with_q_keyword_returns_name_match(db_session: AsyncSession):
    """q=关键词 + search_type=keyword 时仅返回 name 模糊匹配的分类"""
    async for db in db_session:
        # Arrange
        suffix = uuid4().hex[:8]
        c1 = Category(id=uuid4(), name=f"肝胆外科_{suffix}", sort_order=0, is_active=True)
        c2 = Category(id=uuid4(), name=f"骨科_{suffix}", sort_order=1, is_active=True)
        db.add_all([c1, c2])
        await db.flush()
        # Act: 关键词含「肝胆」
        items, total = await get_categories_paginated(
            db, page=1, size=10, is_active=None, current_user_id=uuid4(), role="ADMIN",
            q="肝胆", search_type="keyword"
        )
        # Assert: 至少返回 1 条，且全部为 name 含「肝胆」的分类（库中可能已有其他匹配数据）
        assert total >= 1
        assert len(items) >= 1
        assert all("肝胆" in c.name for c in items)


@pytest.mark.asyncio
async def test_get_categories_paginated_with_q_id_returns_single(db_session: AsyncSession):
    """q=合法 UUID + search_type=id 时返回至多一条且 id 匹配"""
    async for db in db_session:
        # Arrange
        suffix = uuid4().hex[:8]
        cat = Category(id=uuid4(), name=f"分类_{suffix}", sort_order=0, is_active=True)
        db.add(cat)
        await db.flush()
        # Act
        items, total = await get_categories_paginated(
            db, page=1, size=10, is_active=None, current_user_id=uuid4(), role="ADMIN",
            q=str(cat.id), search_type="id"
        )
        # Assert
        assert total == 1
        assert len(items) == 1
        assert items[0].id == cat.id


@pytest.mark.asyncio
async def test_get_categories_paginated_without_q_unchanged(db_session: AsyncSession):
    """无 q 时行为与现有一致（分页、is_active）"""
    async for db in db_session:
        suffix = uuid4().hex[:8]
        c1 = Category(id=uuid4(), name=f"分类A_{suffix}", sort_order=0, is_active=True)
        db.add(c1)
        await db.flush()
        items, total = await get_categories_paginated(
            db, page=1, size=10, is_active=None, current_user_id=uuid4(), role="ADMIN",
            q=None, search_type=None
        )
        assert total >= 1
        assert len(items) >= 1


@pytest.mark.asyncio
async def test_get_tags_with_q_keyword_returns_name_match(db_session: AsyncSession):
    """q=关键词时仅返回 name 模糊匹配的标签"""
    async for db in db_session:
        suffix = uuid4().hex[:8]
        t1 = Tag(id=uuid4(), name=f"微创手术_{suffix}", is_active=True)
        t2 = Tag(id=uuid4(), name=f"病例讨论_{suffix}", is_active=True)
        db.add_all([t1, t2])
        await db.flush()
        result = await get_tags(db, is_active=None, current_user_id=uuid4(), role="ADMIN", q="微创", search_type="keyword")
        assert len(result) >= 1
        assert all("微创" in t.name for t in result)


@pytest.mark.asyncio
async def test_get_tags_with_q_id_returns_single(db_session: AsyncSession):
    """q=合法 UUID + search_type=id 时返回至多一条"""
    async for db in db_session:
        suffix = uuid4().hex[:8]
        tag = Tag(id=uuid4(), name=f"标签_{suffix}", is_active=True)
        db.add(tag)
        await db.flush()
        result = await get_tags(db, is_active=None, current_user_id=uuid4(), role="ADMIN", q=str(tag.id), search_type="id")
        assert len(result) == 1
        assert result[0].id == tag.id


@pytest.mark.asyncio
async def test_get_tags_without_q_unchanged(db_session: AsyncSession):
    """无 q 时行为与现有一致"""
    async for db in db_session:
        suffix = uuid4().hex[:8]
        tag = Tag(id=uuid4(), name=f"标签_{suffix}", is_active=True)
        db.add(tag)
        await db.flush()
        result = await get_tags(db, is_active=None, current_user_id=uuid4(), role="ADMIN", q=None, search_type=None)
        assert len(result) >= 1


# ============================================================================
# Category Reference Count（阶段0 统一计数口径）
# ============================================================================

@pytest.mark.asyncio
async def test_count_category_references_all_five_types(db_session: AsyncSession):
    """五类引用全部命中：3 启用 + 2 停用专家、1 科室、2 房间关联、2 启用子分类"""
    from app.models.experts import Expert
    from app.models.expert_departments import ExpertDepartment
    from app.crud.content_management import CategoryReferenceCount, count_category_references

    async for db in db_session:
        parent = Category(id=uuid4(), name=f"一级_{uuid4().hex[:8]}", slug=f"c1_{uuid4().hex[:6]}", sort_order=0, is_active=True)
        child1 = Category(id=uuid4(), name=f"二级A_{uuid4().hex[:8]}", parent_id=parent.id, sort_order=0, is_active=True)
        child2 = Category(id=uuid4(), name=f"二级B_{uuid4().hex[:8]}", parent_id=parent.id, sort_order=0, is_active=True)
        child3 = Category(id=uuid4(), name=f"二级C_{uuid4().hex[:8]}", parent_id=parent.id, sort_order=0, is_active=False)
        db.add_all([parent, child1, child2, child3])

        experts = [
            Expert(id=uuid4(), user_id=uuid4(), name=f"专家A_{uuid4().hex[:6]}", category_id=parent.id, is_active=True),
            Expert(id=uuid4(), user_id=uuid4(), name=f"专家B_{uuid4().hex[:6]}", category_id=parent.id, is_active=True),
            Expert(id=uuid4(), user_id=uuid4(), name=f"专家C_{uuid4().hex[:6]}", category_id=parent.id, is_active=True),
            Expert(id=uuid4(), user_id=uuid4(), name=f"专家D_{uuid4().hex[:6]}", category_id=parent.id, is_active=False),
            Expert(id=uuid4(), user_id=uuid4(), name=f"专家E_{uuid4().hex[:6]}", category_id=parent.id, is_active=False),
        ]
        db.add_all(experts)

        dept = ExpertDepartment(id=uuid4(), name=f"科室_{uuid4().hex[:6]}", category_id=parent.id)
        db.add(dept)

        room1 = await create_test_room(db)
        room2 = await create_test_room(db)
        db.add_all([
            LiveRoomCategory(room_id=room1.id, category_id=parent.id),
            LiveRoomCategory(room_id=room2.id, category_id=parent.id),
        ])
        await db.commit()

        refs = await count_category_references(db, parent.id)

        assert isinstance(refs, CategoryReferenceCount)
        assert refs.expert_all == 5
        assert refs.expert_active == 3
        assert refs.department_count == 1
        assert refs.room_count == 2
        assert refs.active_child_count == 2
        assert refs.total == 5 + 1 + 2 + 2


@pytest.mark.asyncio
async def test_count_category_references_zero(db_session: AsyncSession):
    """无引用分类返回全零"""
    from app.crud.content_management import count_category_references

    async for db in db_session:
        cat = Category(id=uuid4(), name=f"空分类_{uuid4().hex[:8]}", sort_order=0, is_active=True)
        db.add(cat)
        await db.commit()

        refs = await count_category_references(db, cat.id)
        assert refs.expert_all == 0
        assert refs.expert_active == 0
        assert refs.department_count == 0
        assert refs.room_count == 0
        assert refs.active_child_count == 0
        assert refs.total == 0


# ============================================================================
# migrate_category_references / cascade_disable（阶段1 删除闭环）
# ============================================================================

@pytest.mark.asyncio
async def test_migrate_category_references_to_target(db_session: AsyncSession):
    """专家/科室迁移到 target，房间关联迁移去重"""
    from app.models.experts import Expert
    from app.models.expert_departments import ExpertDepartment
    from app.crud.content_management import migrate_category_references

    async for db in db_session:
        source = Category(id=uuid4(), name=f"源_{uuid4().hex[:8]}", sort_order=0, is_active=True)
        target = Category(id=uuid4(), name=f"目标_{uuid4().hex[:8]}", sort_order=0, is_active=True)
        db.add_all([source, target])
        await db.flush()

        experts = [
            Expert(id=uuid4(), user_id=uuid4(), name=f"E_{uuid4().hex[:6]}", category_id=source.id),
            Expert(id=uuid4(), user_id=uuid4(), name=f"E_{uuid4().hex[:6]}", category_id=source.id),
        ]
        db.add_all(experts)
        dept = ExpertDepartment(id=uuid4(), name=f"D_{uuid4().hex[:6]}", category_id=source.id)
        db.add(dept)
        room = await create_test_room(db)
        # source 关联 + target 已有同一房间关联（去重场景）
        db.add_all([
            LiveRoomCategory(room_id=room.id, category_id=source.id),
            LiveRoomCategory(room_id=room.id, category_id=target.id),
        ])
        await db.commit()

        stats = await migrate_category_references(db, [source.id], target.id)
        await db.commit()
        # 测试会话 expire_on_commit=False：强制过期以读取 DB 新值
        # 测试会话 expire_on_commit=False：查询时强制刷新（populate_existing）

        assert stats["expert_count"] == 2
        assert stats["department_count"] == 1
        assert stats["room_count"] == 1
        # 验证专家/科室已迁移（populate_existing 强制刷新 identity map）
        from sqlalchemy import select as sa_select
        e = (await db.execute(sa_select(Expert).where(Expert.id == experts[0].id).execution_options(populate_existing=True))).scalar_one()
        assert e.category_id == target.id
        d = (await db.execute(sa_select(ExpertDepartment).where(ExpertDepartment.id == dept.id).execution_options(populate_existing=True))).scalar_one()
        assert d.category_id == target.id
        # 房间关联去重：该房间只有一条 target 关联
        links = (await db.execute(
            sa_select(LiveRoomCategory).where(LiveRoomCategory.room_id == room.id).execution_options(populate_existing=True)
        )).scalars().all()
        assert len(links) == 1
        assert links[0].category_id == target.id


@pytest.mark.asyncio
async def test_migrate_category_references_remove_room_links(db_session: AsyncSession):
    """无 target 时解除房间关联（弱引用），专家/科室不迁移"""
    from app.models.experts import Expert
    from app.crud.content_management import migrate_category_references

    async for db in db_session:
        source = Category(id=uuid4(), name=f"源_{uuid4().hex[:8]}", sort_order=0, is_active=True)
        db.add(source)
        await db.flush()
        expert = Expert(id=uuid4(), user_id=uuid4(), name=f"E_{uuid4().hex[:6]}", category_id=source.id)
        db.add(expert)
        room = await create_test_room(db)
        db.add(LiveRoomCategory(room_id=room.id, category_id=source.id))
        await db.commit()

        stats = await migrate_category_references(db, [source.id], None)
        await db.commit()
        # 测试会话 expire_on_commit=False：查询时强制刷新（populate_existing）

        assert stats["expert_count"] == 0
        assert stats["room_count"] == 1
        # 房间关联已解除（populate_existing 强制刷新）
        from sqlalchemy import select as sa_select
        links = (await db.execute(
            sa_select(LiveRoomCategory).where(LiveRoomCategory.room_id == room.id).execution_options(populate_existing=True)
        )).scalars().all()
        assert len(links) == 0
        # 专家未迁移
        e = (await db.execute(sa_select(Expert).where(Expert.id == expert.id).execution_options(populate_existing=True))).scalar_one()
        assert e.category_id == source.id


@pytest.mark.asyncio
async def test_cascade_disable_category_tree(db_session: AsyncSession):
    """级联软删子树（父+子全部停用）"""
    from app.crud.content_management import cascade_disable_category_tree, get_category_by_id

    async for db in db_session:
        parent = Category(id=uuid4(), name=f"父_{uuid4().hex[:8]}", sort_order=0, is_active=True)
        child = Category(id=uuid4(), name=f"子_{uuid4().hex[:8]}", parent_id=parent.id, sort_order=0, is_active=True)
        inactive_child = Category(id=uuid4(), name=f"停用子_{uuid4().hex[:8]}", parent_id=parent.id, sort_order=0, is_active=False)
        db.add_all([parent, child, inactive_child])
        await db.commit()

        disabled = await cascade_disable_category_tree(db, [parent.id, child.id, inactive_child.id])
        await db.commit()
        # 测试会话 expire_on_commit=False：查询时强制刷新（populate_existing）

        assert disabled == 2  # 仅原本启用的
        from sqlalchemy import select as sa_select
        parent_check = (await db.execute(sa_select(Category).where(Category.id == parent.id).execution_options(populate_existing=True))).scalar_one()
        child_check = (await db.execute(sa_select(Category).where(Category.id == child.id).execution_options(populate_existing=True))).scalar_one()
        assert parent_check.is_active is False
        assert child_check.is_active is False


@pytest.mark.asyncio
async def test_get_categories_hides_orphan_children(db_session: AsyncSession):
    """防御过滤：父分类停用后，其 active 子分类不返回（防孤儿节点）"""
    from app.crud.content_management import get_categories

    async for db in db_session:
        parent = Category(id=uuid4(), name=f"父_{uuid4().hex[:8]}", sort_order=0, is_active=False)
        child = Category(id=uuid4(), name=f"子_{uuid4().hex[:8]}", parent_id=parent.id, sort_order=0, is_active=True)
        root = Category(id=uuid4(), name=f"根_{uuid4().hex[:8]}", sort_order=0, is_active=True)
        db.add_all([parent, child, root])
        await db.commit()

        result = await get_categories(db, current_user_id=None, role=None)
        names = {c.name for c in result}
        assert root.name in names
        assert child.name not in names  # 父停用 → 子隐藏


# ============================================================================
# get_category_id_by_name（阶段6A：同名歧义消除）
# ============================================================================

@pytest.mark.asyncio
async def test_get_category_id_by_name_unique(db_session: AsyncSession):
    """唯一命中直接返回"""
    from app.crud.content_management import get_category_id_by_name

    async for db in db_session:
        cat = Category(id=uuid4(), name=f"唯一名_{uuid4().hex[:8]}", sort_order=0, is_active=True)
        db.add(cat)
        await db.commit()

        found = await get_category_id_by_name(db, cat.name)
        assert found == cat.id


@pytest.mark.asyncio
async def test_get_category_id_by_name_ambiguous_prefers_sub(db_session: AsyncSession):
    """同名歧义：prefer_sub=True 时二级优先"""
    from app.crud.content_management import get_category_id_by_name

    async for db in db_session:
        suffix = uuid4().hex[:8]
        root = Category(id=uuid4(), name=f"神经内科_{suffix}", sort_order=0, is_active=True)
        sub = Category(id=uuid4(), name=f"神经内科_{suffix}", parent_id=root.id, sort_order=0, is_active=True)
        db.add_all([root, sub])
        await db.commit()

        found = await get_category_id_by_name(db, root.name, prefer_sub=True)
        assert found == sub.id

        found_root = await get_category_id_by_name(db, root.name, prefer_sub=False)
        assert found_root == root.id


@pytest.mark.asyncio
async def test_get_category_id_by_name_none(db_session: AsyncSession):
    """无匹配返回 None"""
    from app.crud.content_management import get_category_id_by_name

    async for db in db_session:
        found = await get_category_id_by_name(db, f"不存在_{uuid4().hex[:8]}")
        assert found is None



# ============================================================================
# 标签管理 V2 CRUD Tests（溯源 / resolve 查重 / 空列表守卫）
# ============================================================================

@pytest.mark.asyncio
async def test_create_tag_default_source_admin(db_session: AsyncSession):
    """V2：create_tag 默认 source=admin、created_by=None（向后兼容）"""
    async for db in db_session:
        suffix = uuid4().hex[:8]
        tag_data = TagCreate(name=f"默认溯源标签_{suffix}", is_active=True)

        result = await create_tag(db, tag_data)
        await db.commit()

        assert result.source == "admin"
        assert result.created_by is None


@pytest.mark.asyncio
async def test_create_tag_user_source_and_creator(db_session: AsyncSession):
    """V2：resolve 场景传 source=user + created_by 落库"""
    async for db in db_session:
        suffix = uuid4().hex[:8]
        creator_id = uuid4()
        tag_data = TagCreate(name=f"自建溯源标签_{suffix}", is_active=True)

        result = await create_tag(db, tag_data, source="user", created_by=creator_id)
        await db.commit()

        assert result.source == "user"
        assert result.created_by == creator_id


@pytest.mark.asyncio
async def test_get_tag_by_name_found(db_session: AsyncSession):
    """V2：按精确名称命中已有标签"""
    async for db in db_session:
        suffix = uuid4().hex[:8]
        tag_name = f"命中查询标签_{suffix}"
        tag = Tag(id=uuid4(), name=tag_name, is_active=True)
        db.add(tag)
        await db.commit()

        result = await get_tag_by_name(db, tag_name)

        assert result is not None
        assert result.id == tag.id


@pytest.mark.asyncio
async def test_get_tag_by_name_soft_deleted_still_found(db_session: AsyncSession):
    """V2：软删同名可查到（resolve 用于'不复活'判断）"""
    async for db in db_session:
        suffix = uuid4().hex[:8]
        tag_name = f"软删查询标签_{suffix}"
        tag = Tag(id=uuid4(), name=tag_name, is_active=False)
        db.add(tag)
        await db.commit()

        result = await get_tag_by_name(db, tag_name)

        assert result is not None
        assert result.is_active is False


@pytest.mark.asyncio
async def test_get_tag_by_name_not_found(db_session: AsyncSession):
    """V2：未命中返回 None"""
    async for db in db_session:
        result = await get_tag_by_name(db, f"不存在标签_{uuid4().hex[:8]}")
        assert result is None


@pytest.mark.asyncio
async def test_set_session_tags_replace_empty_clears(db_session: AsyncSession):
    """V2：replace + 空列表 = 清空，返回 []，不触发 IN ()"""
    async for db in db_session:
        session_id = uuid4()
        suffix = uuid4().hex[:8]
        tag1 = Tag(id=uuid4(), name=f"清空标签1_{suffix}", is_active=True)
        db.add(tag1)
        await db.commit()

        await create_test_session(db, session_id)
        await set_session_tags(db, session_id, [tag1.id], mode="replace")
        await db.commit()
        assert len(await get_tags_by_session_id(db, session_id)) == 1

        # Act: replace 空列表
        result = await set_session_tags(db, session_id, [], mode="replace")
        await db.commit()

        assert result == []
        assert len(await get_tags_by_session_id(db, session_id)) == 0


@pytest.mark.asyncio
async def test_set_session_tags_append_empty_keeps_existing(db_session: AsyncSession):
    """V2：append + 空列表 = 无操作，返回现有关联"""
    async for db in db_session:
        session_id = uuid4()
        suffix = uuid4().hex[:8]
        tag1 = Tag(id=uuid4(), name=f"追加空标签1_{suffix}", is_active=True)
        db.add(tag1)
        await db.commit()

        await create_test_session(db, session_id)
        await set_session_tags(db, session_id, [tag1.id], mode="replace")
        await db.commit()

        # Act: append 空列表
        result = await set_session_tags(db, session_id, [], mode="append")
        await db.commit()

        assert len(result) == 1
        assert result[0].id == tag1.id


@pytest.mark.asyncio
async def test_set_session_tags_append_empty_no_links_returns_empty(db_session: AsyncSession):
    """V2：append + 空列表且无现有关联 = 早退返回 []，不触发 IN ()"""
    async for db in db_session:
        session_id = uuid4()
        await create_test_session(db, session_id)

        result = await set_session_tags(db, session_id, [], mode="append")
        await db.commit()

        assert result == []
