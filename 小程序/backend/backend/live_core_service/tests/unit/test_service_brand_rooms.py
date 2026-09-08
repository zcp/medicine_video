"""
LiveCore Service - Brand Rooms Service Unit Tests

This module contains unit tests for get_brand_rooms_paginated Service method.
Generated in incremental test mode.
"""

import uuid
import pytest
from unittest.mock import AsyncMock
from faker import Faker

# 项目内导入
from app.services.brand_service import BrandService
from app.exceptions import PermissionDeniedException, NotFoundException

# 初始化 Faker
fake = Faker()


# ==================== 辅助函数 (Helper Functions) ====================

def create_mock_brand(brand_id: uuid.UUID = None, **kwargs):
    """创建模拟品牌对象"""
    if brand_id is None:
        brand_id = uuid.uuid4()
    brand = AsyncMock()
    brand.id = brand_id
    brand.name = kwargs.get("name", f"品牌_{fake.company()}")
    brand.is_active = kwargs.get("is_active", True)
    return brand


# ==================== Brand_Rooms Service方法测试 ====================

@pytest.mark.asyncio
async def test_get_brand_rooms_paginated_success(mocker):
    """测试获取品牌关联直播间列表成功"""
    # ===== Arrange (准备) =====
    db = AsyncMock()
    brand_id = uuid.uuid4()
    mock_brand = create_mock_brand(brand_id=brand_id)
    mock_rooms = [
        {
            "room_id": uuid.uuid4(),
            "room_title": "直播间1",
            "description": "描述1",
            "is_private": False,
            "cover_url": "/media/rooms/cover1.jpg",
            "associated_at": "2025-01-20T10:00:00Z"
        },
        {
            "room_id": uuid.uuid4(),
            "room_title": "直播间2",
            "description": "描述2",
            "is_private": True,
            "cover_url": None,
            "associated_at": "2025-01-21T10:00:00Z"
        }
    ]
    
    # Mock CRUD调用
    mock_get_brand_by_id = mocker.patch(
        "app.crud.brand.get_brand_by_id",
        new_callable=AsyncMock,
        return_value=mock_brand
    )
    mock_get_brand_rooms_paginated = mocker.patch(
        "app.crud.brand.get_brand_rooms_paginated",
        new_callable=AsyncMock,
        return_value=(mock_rooms, 2)
    )
    
    service = BrandService()
    
    # ===== Act (执行) =====
    result = await service.get_brand_rooms_paginated(
        db, brand_id, page=1, size=10, current_user_id=uuid.uuid4(), role="ADMIN"
    )
    
    # ===== Assert (断言) =====
    assert result["code"] == 200
    assert result["message"] == "success"
    assert result["data"]["total"] == 2
    assert len(result["data"]["items"]) == 2
    assert result["data"]["page"] == 1
    assert result["data"]["size"] == 10
    assert "timestamp" in result
    
    # 验证返回的数据结构
    first_item = result["data"]["items"][0]
    assert "room_id" in first_item
    assert "room_title" in first_item
    assert "description" in first_item
    assert "is_private" in first_item
    assert "cover_url" in first_item
    assert "associated_at" in first_item
    
    mock_get_brand_by_id.assert_called_once_with(db, brand_id)
    mock_get_brand_rooms_paginated.assert_called_once_with(db, brand_id, 1, 10)


@pytest.mark.asyncio
async def test_get_brand_rooms_paginated_permission_denied(mocker):
    """测试获取品牌关联直播间列表失败（权限不足）"""
    # ===== Arrange (准备) =====
    db = AsyncMock()
    brand_id = uuid.uuid4()
    service = BrandService()
    
    # ===== Act & Assert (执行和断言) =====
    with pytest.raises(PermissionDeniedException):
        await service.get_brand_rooms_paginated(
            db, brand_id, page=1, size=10, current_user_id=uuid.uuid4(), role="REGULAR"
        )


@pytest.mark.asyncio
async def test_get_brand_rooms_paginated_brand_not_found(mocker):
    """测试获取品牌关联直播间列表失败（品牌不存在）"""
    # ===== Arrange (准备) =====
    db = AsyncMock()
    brand_id = uuid.uuid4()
    
    # Mock CRUD调用：品牌不存在
    mock_get_brand_by_id = mocker.patch(
        "app.crud.brand.get_brand_by_id",
        new_callable=AsyncMock,
        return_value=None
    )
    
    service = BrandService()
    
    # ===== Act & Assert (执行和断言) =====
    with pytest.raises(NotFoundException, match="品牌不存在"):
        await service.get_brand_rooms_paginated(
            db, brand_id, page=1, size=10, current_user_id=uuid.uuid4(), role="ADMIN"
        )
    
    mock_get_brand_by_id.assert_called_once_with(db, brand_id)


@pytest.mark.asyncio
async def test_get_brand_rooms_paginated_pagination(mocker):
    """测试获取品牌关联直播间列表（分页参数）"""
    # ===== Arrange (准备) =====
    db = AsyncMock()
    brand_id = uuid.uuid4()
    mock_brand = create_mock_brand(brand_id=brand_id)
    mock_rooms = [
        {"room_id": uuid.uuid4(), "room_title": f"直播间{i}"}
        for i in range(5)
    ]
    
    # Mock CRUD调用
    mocker.patch(
        "app.crud.brand.get_brand_by_id",
        new_callable=AsyncMock,
        return_value=mock_brand
    )
    mock_get_brand_rooms_paginated = mocker.patch(
        "app.crud.brand.get_brand_rooms_paginated",
        new_callable=AsyncMock,
        return_value=(mock_rooms, 20)  # 总共20条，当前页5条
    )
    
    service = BrandService()
    
    # ===== Act (执行) =====
    result = await service.get_brand_rooms_paginated(
        db, brand_id, page=2, size=5, current_user_id=uuid.uuid4(), role="ADMIN"
    )
    
    # ===== Assert (断言) =====
    assert result["code"] == 200
    assert result["data"]["total"] == 20
    assert result["data"]["page"] == 2
    assert result["data"]["size"] == 5
    assert len(result["data"]["items"]) == 5
    
    # 验证分页参数正确传递
    mock_get_brand_rooms_paginated.assert_called_once_with(db, brand_id, 2, 5)


@pytest.mark.asyncio
async def test_get_brand_rooms_paginated_empty_result(mocker):
    """测试获取品牌关联直播间列表（空结果）"""
    # ===== Arrange (准备) =====
    db = AsyncMock()
    brand_id = uuid.uuid4()
    mock_brand = create_mock_brand(brand_id=brand_id)
    
    # Mock CRUD调用：返回空列表
    mocker.patch(
        "app.crud.brand.get_brand_by_id",
        new_callable=AsyncMock,
        return_value=mock_brand
    )
    mock_get_brand_rooms_paginated = mocker.patch(
        "app.crud.brand.get_brand_rooms_paginated",
        new_callable=AsyncMock,
        return_value=([], 0)
    )
    
    service = BrandService()
    
    # ===== Act (执行) =====
    result = await service.get_brand_rooms_paginated(
        db, brand_id, page=1, size=10, current_user_id=uuid.uuid4(), role="ADMIN"
    )
    
    # ===== Assert (断言) =====
    assert result["code"] == 200
    assert result["data"]["total"] == 0
    assert result["data"]["page"] == 1
    assert result["data"]["size"] == 10
    assert len(result["data"]["items"]) == 0
    
    mock_get_brand_rooms_paginated.assert_called_once_with(db, brand_id, 1, 10)
