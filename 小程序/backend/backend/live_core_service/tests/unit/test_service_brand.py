"""
LiveCore Service - Brand Service Unit Tests

This module contains unit tests for the BrandService business logic layer,
using mocks to isolate dependencies.
Generated in incremental test mode.
"""

import uuid
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, Mock

# 项目内导入
from app.services.brand_service import BrandService
from app.models.brand import Brand
from app.models.topic import Topic, TopicStatus
from app.models.live_core import LiveRoom
from app.schemas.brand import BrandCreate, BrandUpdate, BrandItem
from app.exceptions import (
    NotFoundException,
    PermissionDeniedException,
    InvalidParameterException,
    DatabaseIntegrityException
)


# ==================== 辅助函数 (Helper Functions) ====================

def create_mock_brand(
    brand_id: uuid.UUID = None,
    name: str = "测试品牌",
    is_active: bool = True
) -> Brand:
    """创建Mock的Brand对象"""
    if brand_id is None:
        brand_id = uuid.uuid4()
    
    mock_brand = Brand(
        id=brand_id,
        name=name,
        slug=f"brand-{uuid.uuid4().hex[:8]}",
        logo_url="https://example.com/logo.png",
        description="测试品牌描述",
        website_url="https://example.com",
        sort_order=1,
        is_active=is_active
    )
    mock_brand.created_at = datetime.utcnow()
    mock_brand.updated_at = datetime.utcnow()
    
    return mock_brand


def create_mock_topic(
    topic_id: uuid.UUID = None,
    title: str = "测试专题",
    status: str = "published"
) -> Topic:
    """创建Mock的Topic对象"""
    if topic_id is None:
        topic_id = uuid.uuid4()
    
    mock_topic = Topic(
        id=topic_id,
        user_id=uuid.uuid4(),
        title=title,
        description="测试专题描述",
        status=status
    )
    mock_topic.created_at = datetime.utcnow()
    mock_topic.updated_at = datetime.utcnow()
    
    return mock_topic


def create_mock_room(
    room_id: uuid.UUID = None,
    user_id: uuid.UUID = None,
) -> LiveRoom:
    """创建Mock的LiveRoom对象"""
    if room_id is None:
        room_id = uuid.uuid4()
    if user_id is None:
        user_id = uuid.uuid4()
    
    mock_room = LiveRoom(
        id=room_id,
        user_id=user_id,
        title="测试直播间",
        stream_key=f"stream_key_{uuid.uuid4().hex[:16]}",
        is_private=False,
        record_by_default=True
    )
    mock_room.created_at = datetime.utcnow()
    mock_room.updated_at = datetime.utcnow()
    
    return mock_room


# ==================== 权限守卫函数测试 ====================

@pytest.mark.asyncio
async def test_check_admin_permission_success():
    """测试管理员权限检查成功"""
    service = BrandService()
    
    # 测试ADMIN角色
    try:
        service._check_admin_permission("ADMIN")
    except PermissionDeniedException:
        pytest.fail("ADMIN应该有权限")
    
    # 测试SUPERADMIN角色
    try:
        service._check_admin_permission("SUPERADMIN")
    except PermissionDeniedException:
        pytest.fail("SUPERADMIN应该有权限")


@pytest.mark.asyncio
async def test_check_admin_permission_denied():
    """测试管理员权限检查失败"""
    service = BrandService()
    
    # 测试REGULAR角色
    with pytest.raises(PermissionDeniedException) as exc_info:
        service._check_admin_permission("REGULAR")
    assert "权限不足" in str(exc_info.value)
    
    # 测试None
    with pytest.raises(PermissionDeniedException):
        service._check_admin_permission(None)


# ==================== Brands Service方法测试 ====================

# tests/unit/test_service_brand.py

# 修复 test_get_brands_list_success (第135-163行)
@pytest.mark.asyncio
async def test_get_brands_list_success(mocker):
    """测试获取品牌列表成功"""
    # ===== Arrange (准备) =====
    from unittest.mock import AsyncMock

    db = AsyncMock()
    mock_brand1 = create_mock_brand(name="品牌1")
    mock_brand2 = create_mock_brand(name="品牌2")

    # Mock CRUD调用
    mock_get_brands = mocker.patch(
        "app.crud.brand.get_brands",
        new_callable=AsyncMock,
        return_value=[mock_brand1, mock_brand2]
    )

    service = BrandService()

    # ===== Act (执行) =====
    result = await service.get_brands_list(db, limit=100, q=None, current_user_id=None, role=None)

    # ===== Assert (断言) =====
    assert result["code"] == 200
    assert result["message"] == "success"
    assert len(result["data"]) == 2
    # ✅ 修复：使用属性访问而不是字典访问
    assert result["data"][0].name == "品牌1"
    mock_get_brands.assert_called_once_with(db, 100, None)


# 修复 test_get_brand_content_success (第165-192行)
# 这个测试可能也需要检查，但从代码看它访问的是 result["data"]["brand_info"]["id"]，
# 这应该是字典结构，应该没问题。但如果有问题，也需要修改。

# 修复 test_get_room_brands_for_tab_success (第826-857行)
@pytest.mark.asyncio
async def test_get_room_brands_for_tab_success(mocker):
    """测试获取直播间品牌Tab内容成功"""
    # ===== Arrange (准备) =====
    db = AsyncMock()
    room_id = uuid.uuid4()
    mock_room = create_mock_room(room_id=room_id)
    mock_brand = create_mock_brand(name="品牌1")

    # Mock LiveRoom查询
    from sqlalchemy import select
    mock_room_result = Mock()
    mock_room_result.scalar_one_or_none.return_value = mock_room
    db.execute.return_value = mock_room_result

    # Mock CRUD调用
    mock_get_room_brands_for_tab = mocker.patch(
        "app.crud.brand.get_room_brands_for_tab",
        new_callable=AsyncMock,
        return_value=[mock_brand]
    )

    service = BrandService()

    # ===== Act (执行) =====
    result = await service.get_room_brands_for_tab(
        db, room_id, include_topic_brands=False, topic_id=None,
        current_user_id=None, role=None
    )

    # ===== Assert (断言) =====
    assert result["code"] == 200
    assert len(result["data"]) == 1
    # ✅ 修复：使用属性访问而不是字典访问
    assert result["data"][0].name == "品牌1"


@pytest.mark.asyncio
async def test_get_brand_content_success(mocker):
    """测试获取品牌详情及关联专题成功"""
    # ===== Arrange (准备) =====
    db = AsyncMock()
    brand_id = uuid.uuid4()
    mock_brand = create_mock_brand(brand_id=brand_id)
    mock_topic1 = create_mock_topic(title="专题1")
    mock_topic2 = create_mock_topic(title="专题2")
    
    # Mock CRUD调用
    mock_get_brand_with_topics = mocker.patch(
        "app.crud.brand.get_brand_with_topics",
        new_callable=AsyncMock,
        return_value=(mock_brand, [mock_topic1, mock_topic2])
    )
    
    service = BrandService()
    
    # ===== Act (执行) =====
    result = await service.get_brand_content(db, brand_id, current_user_id=None, role=None)
    
    # ===== Assert (断言) =====
    assert result["code"] == 200
    # ✅ 修复：使用属性访问而不是字典访问
    # result["data"]["brand_info"] 是 BrandItem 对象
    assert result["data"]["brand_info"].id == brand_id  # 或 str(brand_id) 如果类型需要
    assert len(result["data"]["associated_topics"]) == 2
    mock_get_brand_with_topics.assert_called_once_with(db, brand_id)



@pytest.mark.asyncio
async def test_get_brand_content_not_found(mocker):
    """测试获取品牌详情失败（品牌不存在）"""
    # ===== Arrange (准备) =====
    db = AsyncMock()
    brand_id = uuid.uuid4()
    
    # Mock CRUD调用返回None
    mock_get_brand_with_topics = mocker.patch(
        "app.crud.brand.get_brand_with_topics",
        new_callable=AsyncMock,
        return_value=(None, [])
    )
    
    service = BrandService()
    
    # ===== Act (执行) & Assert (断言) =====
    with pytest.raises(NotFoundException) as exc_info:
        await service.get_brand_content(db, brand_id, current_user_id=None, role=None)
    
    assert "品牌不存在" in str(exc_info.value)
    mock_get_brand_with_topics.assert_called_once_with(db, brand_id)


@pytest.mark.asyncio
async def test_create_brand_success(mocker):
    """测试创建品牌成功"""
    # ===== Arrange (准备) =====
    db = AsyncMock()
    brand_id = uuid.uuid4()
    user_id = uuid.uuid4()
    mock_brand = create_mock_brand(brand_id=brand_id)
    
    # Mock CRUD调用
    mock_create_brand = mocker.patch(
        "app.crud.brand.create_brand",
        new_callable=AsyncMock,
        return_value=mock_brand
    )
    
    service = BrandService()
    brand_data = BrandCreate(name=f"品牌_{uuid.uuid4().hex[:8]}")
    
    # ===== Act (执行) =====
    result = await service.create_brand(db, brand_data, user_id, "ADMIN")
    
    # ===== Assert (断言) =====
    assert result["code"] == 200
    # ✅ 修复：使用属性访问而不是字典访问
    # result["data"] 是 BrandItem 对象
    assert result["data"].id == brand_id
    mock_create_brand.assert_called_once()
    mock_create_brand.assert_called_once()


@pytest.mark.asyncio
async def test_create_brand_permission_denied(mocker):
    """测试创建品牌失败（权限不足）"""
    # ===== Arrange (准备) =====
    db = AsyncMock()
    service = BrandService()
    brand_data = BrandCreate(name=f"品牌_{uuid.uuid4().hex[:8]}")
    
    # ===== Act (执行) & Assert (断言) =====
    with pytest.raises(PermissionDeniedException) as exc_info:
        await service.create_brand(db, brand_data, uuid.uuid4(), "REGULAR")
    
    assert "权限不足" in str(exc_info.value)


@pytest.mark.asyncio
async def test_create_brand_conflict(mocker):
    """测试创建品牌失败（名称冲突）"""
    # ===== Arrange (准备) =====
    db = AsyncMock()
    
    # Mock CRUD调用抛出异常
    mock_create_brand = mocker.patch(
        "app.crud.brand.create_brand",
        new_callable=AsyncMock,
        side_effect=DatabaseIntegrityException("品牌名称已存在")
    )
    
    service = BrandService()
    brand_data = BrandCreate(name=f"品牌_{uuid.uuid4().hex[:8]}")
    
    # ===== Act (执行) & Assert (断言) =====
    # 注意：Service层会将DatabaseIntegrityException转换为InvalidParameterException
    with pytest.raises(InvalidParameterException) as exc_info:
        await service.create_brand(db, brand_data, uuid.uuid4(), "ADMIN")
    
    assert "品牌名称已存在" in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_brands_paginated_success(mocker):
    """测试分页获取品牌列表成功"""
    # ===== Arrange (准备) =====
    db = AsyncMock()
    mock_brand1 = create_mock_brand(name="品牌1")
    mock_brand2 = create_mock_brand(name="品牌2")
    
    # Mock CRUD调用
    mock_get_brands_paginated = mocker.patch(
        "app.crud.brand.get_brands_paginated",
        new_callable=AsyncMock,
        return_value=([mock_brand1, mock_brand2], 2)
    )
    
    service = BrandService()
    
    # ===== Act (执行) =====
    result = await service.get_brands_paginated(
        db, page=1, size=10, sort="sort_order", name=None, is_active=None,
        current_user_id=uuid.uuid4(), role="ADMIN"
    )
    
    # ===== Assert (断言) =====
    assert result["code"] == 200
    assert result["data"]["total"] == 2
    assert len(result["data"]["items"]) == 2
    mock_get_brands_paginated.assert_called_once()


@pytest.mark.asyncio
async def test_get_brands_paginated_permission_denied(mocker):
    """测试分页获取品牌列表失败（权限不足）"""
    # ===== Arrange (准备) =====
    db = AsyncMock()
    service = BrandService()
    
    # ===== Act (执行) & Assert (断言) =====
    with pytest.raises(PermissionDeniedException):
        await service.get_brands_paginated(
            db, page=1, size=10, sort="sort_order", name=None, is_active=None,
            current_user_id=uuid.uuid4(), role="REGULAR"
        )


@pytest.mark.asyncio
async def test_get_brand_by_id_success(mocker):
    """测试获取单个品牌成功"""
    # ===== Arrange (准备) =====
    db = AsyncMock()
    brand_id = uuid.uuid4()
    mock_brand = create_mock_brand(brand_id=brand_id)
    
    # Mock CRUD调用
    mock_get_brand_by_id = mocker.patch(
        "app.crud.brand.get_brand_by_id",
        new_callable=AsyncMock,
        return_value=mock_brand
    )
    
    service = BrandService()
    
    # ===== Act (执行) =====
    result = await service.get_brand_by_id(db, brand_id, uuid.uuid4(), "ADMIN")
    
    # ===== Assert (断言) =====
    assert result["code"] == 200
    assert result["data"].id == brand_id
    mock_get_brand_by_id.assert_called_once_with(db, brand_id)


@pytest.mark.asyncio
async def test_get_brand_by_id_not_found(mocker):
    """测试获取单个品牌失败（品牌不存在）"""
    # ===== Arrange (准备) =====
    db = AsyncMock()
    brand_id = uuid.uuid4()
    
    # Mock CRUD调用返回None
    mock_get_brand_by_id = mocker.patch(
        "app.crud.brand.get_brand_by_id",
        new_callable=AsyncMock,
        return_value=None
    )
    
    service = BrandService()
    
    # ===== Act (执行) & Assert (断言) =====
    with pytest.raises(NotFoundException) as exc_info:
        await service.get_brand_by_id(db, brand_id, uuid.uuid4(), "ADMIN")
    
    assert "品牌不存在" in str(exc_info.value)


@pytest.mark.asyncio
async def test_update_brand_success(mocker):
    """测试更新品牌成功"""
    # ===== Arrange (准备) =====
    db = AsyncMock()
    brand_id = uuid.uuid4()
    mock_brand = create_mock_brand(brand_id=brand_id, name="更新后的品牌名")
    
    # Mock CRUD调用
    mock_update_brand = mocker.patch(
        "app.crud.brand.update_brand",
        new_callable=AsyncMock,
        return_value=mock_brand
    )
    
    service = BrandService()
    brand_update = BrandUpdate(name="更新后的品牌名")
    
    # ===== Act (执行) =====
    result = await service.update_brand(db, brand_id, brand_update, uuid.uuid4(), "ADMIN")
    
    # ===== Assert (断言) =====
    assert result["code"] == 200
    assert result["data"].name == "更新后的品牌名"
    mock_update_brand.assert_called_once()


@pytest.mark.asyncio
async def test_update_brand_permission_denied(mocker):
    """测试更新品牌失败（权限不足）"""
    # ===== Arrange (准备) =====
    db = AsyncMock()
    service = BrandService()
    brand_update = BrandUpdate(name="新名称")
    
    # ===== Act (执行) & Assert (断言) =====
    with pytest.raises(PermissionDeniedException):
        await service.update_brand(db, uuid.uuid4(), brand_update, uuid.uuid4(), "REGULAR")


@pytest.mark.asyncio
async def test_delete_brand_soft_delete_success(mocker):
    """测试软删除品牌成功"""
    # ===== Arrange (准备) =====
    db = AsyncMock()
    brand_id = uuid.uuid4()
    mock_brand = create_mock_brand(brand_id=brand_id, is_active=False)
    
    # Mock CRUD调用
    mock_delete_brand = mocker.patch(
        "app.crud.brand.delete_brand",
        new_callable=AsyncMock,
        return_value=mock_brand
    )
    
    service = BrandService()
    
    # ===== Act (执行) =====
    result = await service.delete_brand(db, brand_id, hard_delete=False, current_user_id=uuid.uuid4(), role="ADMIN")
    
    # ===== Assert (断言) =====
    assert result["code"] == 200
    assert result["data"]["deleted"] is True
    mock_delete_brand.assert_called_once_with(db, brand_id, False)


@pytest.mark.asyncio
async def test_delete_brand_hard_delete_superadmin(mocker):
    """测试硬删除品牌成功（SUPERADMIN）"""
    # ===== Arrange (准备) =====
    db = AsyncMock()
    brand_id = uuid.uuid4()
    mock_brand = create_mock_brand(brand_id=brand_id)
    
    # Mock CRUD调用
    mock_check_references = mocker.patch(
        "app.crud.brand.check_brand_references",
        new_callable=AsyncMock,
        return_value=(0, 0)
    )
    mock_delete_brand = mocker.patch(
        "app.crud.brand.delete_brand",
        new_callable=AsyncMock,
        return_value=mock_brand
    )
    
    service = BrandService()
    
    # ===== Act (执行) =====
    result = await service.delete_brand(db, brand_id, hard_delete=True, current_user_id=uuid.uuid4(), role="SUPERADMIN")
    
    # ===== Assert (断言) =====
    assert result["code"] == 200
    mock_check_references.assert_called_once_with(db, brand_id)
    mock_delete_brand.assert_called_once()


@pytest.mark.asyncio
async def test_delete_brand_hard_delete_regular(mocker):
    """测试硬删除品牌失败（REGULAR用户）"""
    # ===== Arrange (准备) =====
    db = AsyncMock()
    service = BrandService()
    
    # ===== Act (执行) & Assert (断言) =====
    # 注意：delete_brand方法已移除hard_delete的特殊检查，现在只检查管理员权限
    with pytest.raises(PermissionDeniedException) as exc_info:
        await service.delete_brand(db, uuid.uuid4(), hard_delete=True, current_user_id=uuid.uuid4(), role="REGULAR")
    
    assert "权限不足，需要管理员权限" in str(exc_info.value)


@pytest.mark.asyncio
async def test_delete_brand_hard_delete_with_refs(mocker):
    """测试硬删除品牌失败（有引用）"""
    # ===== Arrange (准备) =====
    db = AsyncMock()
    brand_id = uuid.uuid4()
    
    # Mock检查引用返回有引用
    mock_check_references = mocker.patch(
        "app.crud.brand.check_brand_references",
        new_callable=AsyncMock,
        return_value=(1, 0)  # 有1个专题引用
    )
    
    service = BrandService()
    
    # ===== Act (执行) & Assert (断言) =====
    with pytest.raises(InvalidParameterException) as exc_info:
        await service.delete_brand(db, brand_id, hard_delete=True, current_user_id=uuid.uuid4(), role="SUPERADMIN")
    
    assert "被引用" in str(exc_info.value)
    mock_check_references.assert_called_once_with(db, brand_id)


# ==================== Brand_Topics Service方法测试 ====================

# tests/unit/test_service_brand.py

# 修复 test_batch_add_brand_topics_success (第515-558行)
@pytest.mark.asyncio
async def test_batch_add_brand_topics_success(mocker):
    """测试批量关联专题到品牌成功"""
    # ===== Arrange (准备) =====
    db = AsyncMock()
    brand_id = uuid.uuid4()
    topic_id1 = uuid.uuid4()
    topic_id2 = uuid.uuid4()
    mock_brand = create_mock_brand(brand_id=brand_id)
    mock_topic1 = create_mock_topic(topic_id=topic_id1)
    mock_topic2 = create_mock_topic(topic_id=topic_id2)

    # Mock CRUD调用
    mock_get_brand_by_id = mocker.patch(
        "app.crud.brand.get_brand_by_id",
        new_callable=AsyncMock,
        return_value=mock_brand
    )

    # ✅ 修复：正确Mock Topic ID验证查询
    # Service层会执行 select(Topic.id).where(Topic.id.in_(topic_ids)) 来验证
    from sqlalchemy import select
    mock_topic_result = Mock()
    mock_topic_result.scalars.return_value = Mock(all=Mock(return_value=[topic_id1, topic_id2]))

    def execute_side_effect(stmt):
        # ✅ 根据查询类型返回不同的结果
        stmt_str = str(stmt).lower()
        if "topic" in stmt_str and "id" in stmt_str:
            # Topic ID验证查询
            return mock_topic_result
        # 其他查询返回默认结果
        return mock_topic_result

    db.execute.side_effect = execute_side_effect

    mock_batch_add = mocker.patch(
        "app.crud.brand.batch_add_brand_topics",
        new_callable=AsyncMock,
        return_value=2
    )

    service = BrandService()

    # ===== Act (执行) =====
    result = await service.batch_add_brand_topics(
        db, brand_id, [topic_id1, topic_id2], uuid.uuid4(), "ADMIN"
    )

    # ===== Assert (断言) =====
    assert result["code"] == 200
    assert result["data"]["added_count"] == 2
    mock_get_brand_by_id.assert_called_once_with(db, brand_id)
    mock_batch_add.assert_called_once()


# 修复 test_bind_room_brands_success (第700-750行)
@pytest.mark.asyncio
async def test_bind_room_brands_success(mocker):
    """测试绑定直播间品牌成功"""
    # ===== Arrange (准备) =====
    db = AsyncMock()
    room_id = uuid.uuid4()
    brand_id1 = uuid.uuid4()
    brand_id2 = uuid.uuid4()
    mock_room = create_mock_room(room_id=room_id)
    mock_brand1 = create_mock_brand(brand_id=brand_id1)
    mock_brand2 = create_mock_brand(brand_id=brand_id2)

    # Mock LiveRoom查询
    from sqlalchemy import select
    mock_room_result = Mock()
    mock_room_result.scalar_one_or_none.return_value = mock_room

    # ✅ 修复：正确Mock Brand ID验证查询
    # Service层会执行 select(Brand.id).where(Brand.id.in_(brand_ids), Brand.is_active == True)
    mock_brand_id_result = Mock()
    mock_brand_id_result.scalars.return_value = Mock(all=Mock(return_value=[brand_id1, brand_id2]))

    def execute_side_effect(stmt):
        # ✅ 根据查询类型返回不同的结果
        stmt_str = str(stmt).lower()
        if "live_rooms" in stmt_str:
            return mock_room_result
        elif "brands" in stmt_str and "id" in stmt_str and "is_active" in stmt_str:
            # Brand ID验证查询（验证品牌ID是否存在且激活）
            return mock_brand_id_result
        return mock_room_result

    db.execute.side_effect = execute_side_effect

    # Mock CRUD调用
    mock_bind_room_brands = mocker.patch(
        "app.crud.brand.bind_room_brands",
        new_callable=AsyncMock,
        return_value=[brand_id1, brand_id2]
    )

    service = BrandService()

    # ===== Act (执行) =====
    result = await service.bind_room_brands(
        db, room_id, [brand_id1, brand_id2], uuid.uuid4(), "ADMIN"
    )

    # ===== Assert (断言) =====
    assert result["code"] == 200
    assert len(result["data"]["brand_ids"]) == 2
    mock_bind_room_brands.assert_called_once_with(db, room_id, [brand_id1, brand_id2])


@pytest.mark.asyncio
async def test_bind_room_brands_owner_success(mocker):
    """REGULAR 房主可绑定任意启用品牌（支持联动）"""
    db = AsyncMock()
    owner_id = uuid.uuid4()
    room_id = uuid.uuid4()
    brand_id1 = uuid.uuid4()
    brand_id2 = uuid.uuid4()
    mock_room = create_mock_room(room_id=room_id, user_id=owner_id)

    mock_room_result = Mock()
    mock_room_result.scalar_one_or_none.return_value = mock_room
    mock_brand_id_result = Mock()
    mock_brand_id_result.scalars.return_value = Mock(
        all=Mock(return_value=[brand_id1, brand_id2])
    )

    def execute_side_effect(stmt):
        stmt_str = str(stmt).lower()
        if "live_rooms" in stmt_str:
            return mock_room_result
        if "brands" in stmt_str:
            return mock_brand_id_result
        return mock_room_result

    db.execute.side_effect = execute_side_effect
    mocker.patch(
        "app.crud.brand.bind_room_brands",
        new_callable=AsyncMock,
        return_value=[brand_id1, brand_id2],
    )

    service = BrandService()
    result = await service.bind_room_brands(
        db, room_id, [brand_id1, brand_id2], owner_id, "REGULAR"
    )
    assert result["code"] == 200
    assert len(result["data"]["brand_ids"]) == 2


@pytest.mark.asyncio
async def test_bind_room_brands_non_owner_forbidden(mocker):
    """非房主 REGULAR 绑定品牌 → 403"""
    db = AsyncMock()
    room_id = uuid.uuid4()
    mock_room = create_mock_room(room_id=room_id, user_id=uuid.uuid4())
    mock_room_result = Mock()
    mock_room_result.scalar_one_or_none.return_value = mock_room
    db.execute = AsyncMock(return_value=mock_room_result)

    service = BrandService()
    with pytest.raises(PermissionDeniedException):
        await service.bind_room_brands(
            db, room_id, [uuid.uuid4()], uuid.uuid4(), "REGULAR"
        )


@pytest.mark.asyncio
async def test_batch_add_brand_topics_permission_denied(mocker):
    """测试批量关联专题到品牌失败（权限不足）"""
    # ===== Arrange (准备) =====
    db = AsyncMock()
    service = BrandService()
    
    # ===== Act (执行) & Assert (断言) =====
    with pytest.raises(PermissionDeniedException):
        await service.batch_add_brand_topics(
            db, uuid.uuid4(), [uuid.uuid4()], uuid.uuid4(), "REGULAR"
        )


@pytest.mark.asyncio
async def test_batch_add_brand_topics_invalid_topic_ids(mocker):
    """测试批量关联专题到品牌失败（部分专题ID不存在）"""
    # ===== Arrange (准备) =====
    db = AsyncMock()
    brand_id = uuid.uuid4()
    topic_id1 = uuid.uuid4()
    topic_id2 = uuid.uuid4()  # 不存在的ID
    mock_brand = create_mock_brand(brand_id=brand_id)
    mock_topic1 = create_mock_topic(topic_id=topic_id1)
    
    # Mock CRUD调用
    mock_get_brand_by_id = mocker.patch(
        "app.crud.brand.get_brand_by_id",
        new_callable=AsyncMock,
        return_value=mock_brand
    )
    
    # Mock Topic查询（只返回topic1，topic2不存在）
    from sqlalchemy import select
    mock_result = Mock()
    mock_result.scalars.return_value = Mock(all=Mock(return_value=[mock_topic1]))
    db.execute.return_value = mock_result
    
    service = BrandService()
    
    # ===== Act (执行) & Assert (断言) =====
    with pytest.raises(InvalidParameterException) as exc_info:
        await service.batch_add_brand_topics(
            db, brand_id, [topic_id1, topic_id2], uuid.uuid4(), "ADMIN"
        )
    
    assert "不存在" in str(exc_info.value)


@pytest.mark.asyncio
async def test_delete_brand_topic_success(mocker):
    """测试解除品牌-专题关联成功"""
    # ===== Arrange (准备) =====
    db = AsyncMock()
    brand_id = uuid.uuid4()
    topic_id = uuid.uuid4()
    
    # Mock CRUD调用
    mock_delete_brand_topic = mocker.patch(
        "app.crud.brand.delete_brand_topic",
        new_callable=AsyncMock,
        return_value=True
    )
    
    service = BrandService()
    
    # ===== Act (执行) =====
    result = await service.delete_brand_topic(db, brand_id, topic_id, uuid.uuid4(), "ADMIN")
    
    # ===== Assert (断言) =====
    assert result["code"] == 200
    assert result["data"]["deleted"] is True
    mock_delete_brand_topic.assert_called_once_with(db, brand_id, topic_id)


@pytest.mark.asyncio
async def test_delete_brand_topic_not_found(mocker):
    """测试解除品牌-专题关联失败（关联不存在）"""
    # ===== Arrange (准备) =====
    db = AsyncMock()
    brand_id = uuid.uuid4()
    topic_id = uuid.uuid4()
    
    # Mock CRUD调用返回False
    mock_delete_brand_topic = mocker.patch(
        "app.crud.brand.delete_brand_topic",
        new_callable=AsyncMock,
        return_value=False
    )
    
    service = BrandService()
    
    # ===== Act (执行) & Assert (断言) =====
    with pytest.raises(NotFoundException) as exc_info:
        await service.delete_brand_topic(db, brand_id, topic_id, uuid.uuid4(), "ADMIN")
    
    assert "关联关系不存在" in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_brand_topics_paginated_success(mocker):
    """测试获取品牌关联专题列表成功"""
    # ===== Arrange (准备) =====
    db = AsyncMock()
    brand_id = uuid.uuid4()
    mock_brand = create_mock_brand(brand_id=brand_id)
    mock_topics = [
        {"topic_id": uuid.uuid4(), "topic_title": "专题1"},
        {"topic_id": uuid.uuid4(), "topic_title": "专题2"}
    ]
    
    # Mock CRUD调用
    mock_get_brand_by_id = mocker.patch(
        "app.crud.brand.get_brand_by_id",
        new_callable=AsyncMock,
        return_value=mock_brand
    )
    mock_get_brand_topics_paginated = mocker.patch(
        "app.crud.brand.get_brand_topics_paginated",
        new_callable=AsyncMock,
        return_value=(mock_topics, 2)
    )
    
    service = BrandService()
    
    # ===== Act (执行) =====
    result = await service.get_brand_topics_paginated(
        db, brand_id, page=1, size=10, current_user_id=uuid.uuid4(), role="ADMIN"
    )
    
    # ===== Assert (断言) =====
    assert result["code"] == 200
    assert result["data"]["total"] == 2
    assert len(result["data"]["items"]) == 2
    mock_get_brand_by_id.assert_called_once_with(db, brand_id)
    mock_get_brand_topics_paginated.assert_called_once()


# ==================== Brand_Rooms Service方法测试 ====================

@pytest.mark.asyncio
async def test_bind_room_brands_invalid_brand_ids(mocker):
    """测试绑定直播间品牌失败（部分品牌ID不存在或已禁用）"""
    # ===== Arrange (准备) =====
    db = AsyncMock()
    room_id = uuid.uuid4()
    brand_id1 = uuid.uuid4()
    brand_id2 = uuid.uuid4()  # 不存在的ID
    mock_room = create_mock_room(room_id=room_id)
    mock_brand1 = create_mock_brand(brand_id=brand_id1, is_active=True)
    
    # Mock LiveRoom查询
    from sqlalchemy import select
    mock_room_result = Mock()
    mock_room_result.scalar_one_or_none.return_value = mock_room
    
    # Mock Brand查询（只返回brand1，brand2不存在）
    mock_brand_result = Mock()
    mock_brand_result.scalars.return_value = Mock(all=Mock(return_value=[mock_brand1]))
    
    def execute_side_effect(stmt):
        if "live_rooms" in str(stmt):
            return mock_room_result
        elif "brands" in str(stmt):
            return mock_brand_result
        return mock_room_result
    
    db.execute.side_effect = execute_side_effect
    
    service = BrandService()
    
    # ===== Act (执行) & Assert (断言) =====
    with pytest.raises(InvalidParameterException) as exc_info:
        await service.bind_room_brands(
            db, room_id, [brand_id1, brand_id2], uuid.uuid4(), "ADMIN"
        )
    
    assert "不存在或已禁用" in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_room_brands_admin_success(mocker):
    """测试获取直播间绑定的品牌成功"""
    # ===== Arrange (准备) =====
    db = AsyncMock()
    room_id = uuid.uuid4()
    mock_room = create_mock_room(room_id=room_id)
    mock_brand1 = create_mock_brand(name="品牌1")
    mock_brand2 = create_mock_brand(name="品牌2")
    
    # Mock LiveRoom查询
    from sqlalchemy import select
    mock_room_result = Mock()
    mock_room_result.scalar_one_or_none.return_value = mock_room
    db.execute.return_value = mock_room_result
    
    # Mock CRUD调用
    mock_get_room_brands = mocker.patch(
        "app.crud.brand.get_room_brands",
        new_callable=AsyncMock,
        return_value=[mock_brand1, mock_brand2]
    )
    
    service = BrandService()
    
    # ===== Act (执行) =====
    result = await service.get_room_brands_admin(db, room_id, uuid.uuid4(), "ADMIN")
    
    # ===== Assert (断言) =====
    assert result["code"] == 200
    assert len(result["data"]) == 2
    mock_get_room_brands.assert_called_once_with(db, room_id)


@pytest.mark.asyncio
async def test_get_room_brands_for_tab_with_topic_brands(mocker):
    """测试获取直播间品牌Tab内容（包含专题品牌）"""
    # ===== Arrange (准备) =====
    db = AsyncMock()
    room_id = uuid.uuid4()
    topic_id = uuid.uuid4()
    mock_room = create_mock_room(room_id=room_id)
    mock_topic = create_mock_topic(topic_id=topic_id)
    mock_room_brand = create_mock_brand(name="直播间品牌")
    mock_topic_brand = create_mock_brand(name="专题品牌")
    
    # Mock LiveRoom查询
    from sqlalchemy import select
    mock_room_result = Mock()
    mock_room_result.scalar_one_or_none.return_value = mock_room
    db.execute.return_value = mock_room_result
    
    # Mock Topic查询
    mock_topic_result = Mock()
    mock_topic_result.scalar_one_or_none.return_value = mock_topic
    
    def execute_side_effect(stmt):
        if "live_rooms" in str(stmt):
            return mock_room_result
        elif "topics" in str(stmt):
            return mock_topic_result
        return mock_room_result
    
    db.execute.side_effect = execute_side_effect
    
    # Mock CRUD调用
    mock_get_room_brands_for_tab = mocker.patch(
        "app.crud.brand.get_room_brands_for_tab",
        new_callable=AsyncMock,
        return_value=[mock_room_brand]
    )
    mock_get_brands_by_topic = mocker.patch(
        "app.crud.brand.get_brands_by_topic",
        new_callable=AsyncMock,
        return_value=[mock_topic_brand]
    )
    
    service = BrandService()
    
    # ===== Act (执行) =====
    result = await service.get_room_brands_for_tab(
        db, room_id, include_topic_brands=True, topic_id=topic_id,
        current_user_id=None, role=None
    )
    
    # ===== Assert (断言) =====
    assert result["code"] == 200
    assert "room_brands" in result["data"]
    assert "topic_brands" in result["data"]
    assert len(result["data"]["room_brands"]) == 1
    assert len(result["data"]["topic_brands"]) == 1
