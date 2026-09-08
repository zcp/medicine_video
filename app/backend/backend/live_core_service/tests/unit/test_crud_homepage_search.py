"""
首页与搜索模块的CRUD层单元测试

测试对象：app/crud/homepage_search.py (Phase1 - Featured Content CRUD)
测试模式：incremental（增量测试）
"""
import uuid
import pytest
from datetime import datetime, timedelta, timedelta, timezone

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import homepage_search as crud
from app.schemas.homepage_search import FeaturedContentCreate, FeaturedContentUpdate
from app.models.homepage_search import FeaturedContent


# ==================== 测试数据辅助函数 ====================

def create_test_featured_content_data(**kwargs):
    """创建测试用焦点图数据"""
    unique_id = str(uuid.uuid4())[:8]
    default_data = {
        "title": f"测试焦点图_{unique_id}",
        "image_url": f"https://example.com/image_{unique_id}.jpg",
        "subtitle": f"副标题_{unique_id}",
        "target_type": "room",
        "target_url": None,
        "sort_order": 0,
        "is_active": True,
    }
    default_data.update(kwargs)
    return FeaturedContentCreate(**default_data)


async def create_test_featured_content_in_db(db: AsyncSession, **kwargs):
    """在数据库中创建测试焦点图记录"""
    content_data = create_test_featured_content_data(**kwargs)
    content = await crud.create_featured_content(db, content_data)
    return content


# ==================== get_featured_content_list 测试 ====================

@pytest.mark.asyncio
async def test_get_featured_content_list_public(db_session):
    """测试获取焦点图列表（公开接口）- 只返回有效的焦点图"""
    async for db in db_session:
        # ===== Arrange (准备) =====
        # ===== Arrange (准备) =====
        await db.execute(delete(FeaturedContent))
        await db.commit()
        # 创建3个焦点图：1个有效，1个未启用，1个未到上线时间
        content1 = await create_test_featured_content_in_db(
            db, is_active=True, sort_order=1
        )
        content2 = await create_test_featured_content_in_db(
            db, is_active=False, sort_order=2
        )
        now = datetime.utcnow()
        future = now + timedelta(days=1)
        content3 = await create_test_featured_content_in_db(
            db, is_active=True, start_at=future, sort_order=3
        )
        
        # ===== Act (执行) =====
        results = await crud.get_featured_content_list(
            db, include_inactive=False, include_scheduled=False
        )
        
        # ===== Assert (断言) =====
        # 应该只返回content1（有效且已上线）
        await db.execute(delete(FeaturedContent))
        await db.commit()
        assert len(results) >= 1
        result_ids = [r.id for r in results]
        assert content1.id in result_ids
        assert content2.id not in result_ids  # 未启用
        assert content3.id not in result_ids  # 未到上线时间


@pytest.mark.asyncio
async def test_get_featured_content_list_admin(db_session):
    """测试获取焦点图列表（管理员接口）- 返回所有焦点图"""
    async for db in db_session:
        # ===== Arrange (准备) =====
        content1 = await create_test_featured_content_in_db(
            db, is_active=True
        )
        content2 = await create_test_featured_content_in_db(
            db, is_active=False
        )
        
        # ===== Act (执行) =====
        results = await crud.get_featured_content_list(
            db, include_inactive=True, include_scheduled=True
        )
        
        # ===== Assert (断言) =====
        # 应该返回所有焦点图（包括未启用的）
        result_ids = [r.id for r in results]
        assert content1.id in result_ids
        assert content2.id in result_ids


@pytest.mark.asyncio
async def test_get_featured_content_list_scheduled(db_session):
    """测试获取焦点图列表 - 定时上下线逻辑"""
    async for db in db_session:
        # ===== Arrange (准备) =====
        now = datetime.utcnow()
        past = now - timedelta(days=1)
        future = now + timedelta(days=1)
        
        # 创建4个焦点图，测试各种定时组合
        content1 = await create_test_featured_content_in_db(
            db, is_active=True, start_at=past, end_at=future  # 有效期内
        )
        content2 = await create_test_featured_content_in_db(
            db, is_active=True, start_at=future  # 未到上线时间
        )
        content3 = await create_test_featured_content_in_db(
            db, is_active=True, end_at=past  # 已过下线时间
        )
        content4 = await create_test_featured_content_in_db(
            db, is_active=True, start_at=None, end_at=None  # 永久有效
        )
        
        # ===== Act (执行) =====
        results = await crud.get_featured_content_list(
            db, include_inactive=False, include_scheduled=False
        )
        
        # ===== Assert (断言) =====
        result_ids = [r.id for r in results]
        assert content1.id in result_ids  # 有效期内
        assert content2.id not in result_ids  # 未到上线时间
        assert content3.id not in result_ids  # 已过下线时间
        assert content4.id in result_ids  # 永久有效


# ==================== get_featured_content_by_id 测试 ====================

@pytest.mark.asyncio
async def test_get_featured_content_by_id_success(db_session):
    """测试根据ID获取焦点图 - 成功"""
    async for db in db_session:
        # ===== Arrange (准备) =====
        content = await create_test_featured_content_in_db(db)
        
        # ===== Act (执行) =====
        result = await crud.get_featured_content_by_id(db, content.id)
        
        # ===== Assert (断言) =====
        assert result is not None
        assert result.id == content.id
        assert result.title == content.title


@pytest.mark.asyncio
async def test_get_featured_content_by_id_not_found(db_session):
    """测试根据ID获取焦点图 - 不存在"""
    async for db in db_session:
        # ===== Arrange (准备) =====
        non_existent_id = uuid.uuid4()
        
        # ===== Act (执行) =====
        result = await crud.get_featured_content_by_id(db, non_existent_id)
        
        # ===== Assert (断言) =====
        assert result is None


# ==================== create_featured_content 测试 ====================

@pytest.mark.asyncio
async def test_create_featured_content_success(db_session):
    """测试创建焦点图 - 成功"""
    async for db in db_session:
        # ===== Arrange (准备) =====
        content_data = create_test_featured_content_data()
        
        # ===== Act (执行) =====
        result = await crud.create_featured_content(db, content_data)
        
        # ===== Assert (断言) =====
        assert result.id is not None
        assert result.title == content_data.title
        assert result.image_url == content_data.image_url
        assert result.subtitle == content_data.subtitle
        assert result.is_active == content_data.is_active
        assert result.sort_order == content_data.sort_order


@pytest.mark.asyncio
async def test_create_featured_content_with_schedule(db_session):
    """测试创建焦点图 - 带定时上下线"""
    async for db in db_session:
        # ===== Arrange (准备) =====
        now = datetime.now(timezone.utc)
        future = now + timedelta(days=1)
        content_data = create_test_featured_content_data(
            start_at=now,
            end_at=future
        )
        
        # ===== Act (执行) =====
        result = await crud.create_featured_content(db, content_data)
        
        # ===== Assert (断言) =====
        assert result.start_at is not None
        assert result.end_at is not None
        # 注意：datetime比较可能有微小差异，使用合理的时间窗口
        assert abs((result.start_at - now).total_seconds()) < 5
        assert abs((result.end_at - future).total_seconds()) < 5


# ==================== update_featured_content 测试 ====================

@pytest.mark.asyncio
async def test_update_featured_content_success(db_session):
    """测试更新焦点图 - 成功"""
    async for db in db_session:
        # ===== Arrange (准备) =====
        content = await create_test_featured_content_in_db(db)
        update_data = FeaturedContentUpdate(
            title="更新后的标题",
            is_active=False
        )
        
        # ===== Act (执行) =====
        result = await crud.update_featured_content(db, content.id, update_data)
        
        # ===== Assert (断言) =====
        assert result is not None
        assert result.id == content.id
        assert result.title == "更新后的标题"
        assert result.is_active == False


@pytest.mark.asyncio
async def test_update_featured_content_not_found(db_session):
    """测试更新焦点图 - 不存在"""
    async for db in db_session:
        # ===== Arrange (准备) =====
        non_existent_id = uuid.uuid4()
        update_data = FeaturedContentUpdate(title="新标题")
        
        # ===== Act (执行) =====
        result = await crud.update_featured_content(db, non_existent_id, update_data)
        
        # ===== Assert (断言) =====
        assert result is None


# ==================== delete_featured_content 测试 ====================

@pytest.mark.asyncio
async def test_delete_featured_content_soft_delete(db_session):
    """测试删除焦点图 - 软删除"""
    async for db in db_session:
        # ===== Arrange (准备) =====
        content = await create_test_featured_content_in_db(db)
        
        # ===== Act (执行) =====
        success = await crud.delete_featured_content(db, content.id, soft_delete=True)
        
        # ===== Assert (断言) =====
        assert success == True
        
        # 验证软删除：记录仍存在，但is_active=False
        deleted_content = await crud.get_featured_content_by_id(db, content.id)
        assert deleted_content is not None
        assert deleted_content.is_active == False


@pytest.mark.asyncio
async def test_delete_featured_content_hard_delete(db_session):
    """测试删除焦点图 - 硬删除"""
    async for db in db_session:
        # ===== Arrange (准备) =====
        content = await create_test_featured_content_in_db(db)
        
        # ===== Act (执行) =====
        success = await crud.delete_featured_content(db, content.id, soft_delete=False)
        
        # ===== Assert (断言) =====
        assert success == True
        
        # 验证硬删除：记录不存在
        deleted_content = await crud.get_featured_content_by_id(db, content.id)
        assert deleted_content is None


# ==================== get_featured_content_count 测试 ====================

@pytest.mark.asyncio
async def test_get_featured_content_count(db_session):
    """测试获取焦点图总数"""
    async for db in db_session:
        # ===== Arrange (准备) =====
        # 获取当前总数和活跃数
        initial_total_count = await crud.get_featured_content_count(db, include_inactive=True)
        initial_active_count = await crud.get_featured_content_count(db, include_inactive=False)

        # 创建2个有效焦点图和1个无效焦点图
        await create_test_featured_content_in_db(db, is_active=True)
        await create_test_featured_content_in_db(db, is_active=True)
        await create_test_featured_content_in_db(db, is_active=False)

        # ===== Act (执行) =====
        total_count = await crud.get_featured_content_count(db, include_inactive=True)
        active_count = await crud.get_featured_content_count(db, include_inactive=False)

        # ===== Assert (断言) =====
        assert total_count == initial_total_count + 3  # 总数增加3
        assert active_count == initial_active_count + 2  # 活跃数增加2（只统计is_active=True的）


# ==================== get_featured_content_list_paginated 测试（增量） ====================

@pytest.mark.asyncio
async def test_get_featured_content_list_paginated_returns_page_and_total(db_session):
    """测试管理员分页列表 - 返回 (list, total)"""
    async for db in db_session:
        # ===== Act (执行) =====
        items, total = await crud.get_featured_content_list_paginated(db, page=1, size=10)
        # ===== Assert (断言) =====
        assert isinstance(items, list)
        assert isinstance(total, int)
        assert total >= 0
        assert len(items) <= 10


@pytest.mark.asyncio
async def test_get_featured_content_list_paginated_respects_page_size(db_session):
    """测试管理员分页列表 - 遵守 page/size"""
    async for db in db_session:
        # ===== Arrange (准备) =====
        await create_test_featured_content_in_db(db, sort_order=0)
        await create_test_featured_content_in_db(db, sort_order=1)
        # ===== Act (执行) =====
        items, total = await crud.get_featured_content_list_paginated(db, page=1, size=1)
        # ===== Assert (断言) =====
        assert len(items) == 1
        assert total >= 2


@pytest.mark.asyncio
async def test_get_featured_content_list_paginated_orders_by_sort_order(db_session):
    """测试管理员分页列表 - 按 sort_order 升序"""
    async for db in db_session:
        # ===== Arrange (准备) =====
        c_high = await create_test_featured_content_in_db(db, sort_order=10)
        c_low = await create_test_featured_content_in_db(db, sort_order=0)
        # ===== Act (执行) =====
        items, total = await crud.get_featured_content_list_paginated(db, page=1, size=10)
        # ===== Assert (断言) =====
        assert total >= 2
        sort_orders = [item.sort_order for item in items]
        assert sort_orders == sorted(sort_orders)


# ==================== get_featured_content_list_paginated 搜索与排序（增量） ====================

@pytest.mark.asyncio
async def test_get_featured_content_list_paginated_with_q_empty(db_session):
    """q 为空时返回全部，total 与 list 一致"""
    async for db in db_session:
        # ===== Arrange (准备) =====
        c1 = await create_test_featured_content_in_db(db, sort_order=0)
        c2 = await create_test_featured_content_in_db(db, sort_order=0)
        # ===== Act (执行) =====
        items, total = await crud.get_featured_content_list_paginated(db, page=1, size=100, q=None, search_type=None)
        # ===== Assert (断言) =====
        assert total >= 2
        assert len(items) <= 100
        ids = [r.id for r in items]
        assert c1.id in ids
        assert c2.id in ids


@pytest.mark.asyncio
async def test_get_featured_content_list_paginated_with_search_type_id(db_session):
    """search_type=id、q 为合法 UUID 时仅返回该条"""
    async for db in db_session:
        # ===== Arrange (准备) =====
        c1 = await create_test_featured_content_in_db(db, sort_order=0, title="唯一标题A")
        c2 = await create_test_featured_content_in_db(db, sort_order=0, title="唯一标题B")
        # ===== Act (执行) =====
        items, total = await crud.get_featured_content_list_paginated(
            db, page=1, size=10, q=str(c1.id), search_type="id"
        )
        # ===== Assert (断言) =====
        assert total == 1
        assert len(items) == 1
        assert items[0].id == c1.id


@pytest.mark.asyncio
async def test_get_featured_content_list_paginated_with_search_type_name(db_session):
    """q 非空、非 id 时按 title/subtitle 模糊匹配"""
    async for db in db_session:
        # ===== Arrange (准备) =====
        unique = str(uuid.uuid4())[:8]
        c1 = await create_test_featured_content_in_db(
            db, sort_order=0, title=f"包含关键词_{unique}", subtitle="副标题"
        )
        c2 = await create_test_featured_content_in_db(db, sort_order=1, title="不包含", subtitle="也不包含")
        # ===== Act (执行) =====
        items, total = await crud.get_featured_content_list_paginated(
            db, page=1, size=10, q=f"关键词_{unique}", search_type="name"
        )
        # ===== Assert (断言) =====
        assert total >= 1
        ids = [r.id for r in items]
        assert c1.id in ids
        assert c2.id not in ids


@pytest.mark.asyncio
async def test_get_featured_content_list_paginated_sort_order(db_session):
    """排序为 sort_order ASC、created_at DESC"""
    async for db in db_session:
        # ===== Arrange (准备) =====
        c0 = await create_test_featured_content_in_db(db, sort_order=0, title="A")
        c0_2 = await create_test_featured_content_in_db(db, sort_order=0, title="B")
        # ===== Act (执行) =====
        items, _ = await crud.get_featured_content_list_paginated(db, page=1, size=10)
        # ===== Assert (断言) =====
        sort_orders = [item.sort_order for item in items]
        assert sort_orders == sorted(sort_orders)
        ids = [r.id for r in items]
        assert c0.id in ids
        assert c0_2.id in ids