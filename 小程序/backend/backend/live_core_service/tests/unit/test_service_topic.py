"""
LiveCore Service - Topic Service Unit Tests

This module contains unit tests for the TopicService business logic layer,
using mocks to isolate dependencies.
"""

import uuid
import pytest
from typing import List, Dict, Any
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

# 项目内导入
from app.services.topic_service import TopicService
from app.models.topic import Topic, TopicCategory, TopicCategoryRoom, TopicStatus
from app.models.live_core import LiveRoom, LiveSession, SessionStatistics
from app.schemas.topic import (
    TopicCreate, TopicUpdate,
    CategoryCreate, CategoryUpdate,
    RoomAssociation
)
from app.exceptions import (
    TopicNotFoundException,
    CategoryNotFoundException,
    TopicPermissionDeniedException,
    RoomAlreadyAssociatedException,
    RoomNotFoundException
)


# ==================== 辅助函数 (Helper Functions) ====================

def create_mock_topic(
    topic_id: uuid.UUID = None,
    user_id: uuid.UUID = None,
    status: TopicStatus = TopicStatus.DRAFT,
    title: str = "Test Topic"
) -> Topic:
    """创建Mock的Topic对象"""
    if topic_id is None:
        topic_id = uuid.uuid4()
    if user_id is None:
        user_id = uuid.uuid4()
    
    mock_topic = Topic(
        id=topic_id,
        user_id=user_id,
        title=title,
        description="Test Description",
        banner_url="https://example.com/banner.jpg",
        status=status
    )
    mock_topic.created_at = datetime.now()
    mock_topic.updated_at = datetime.now()
    
    return mock_topic


def create_mock_category(
    category_id: uuid.UUID = None,
    topic_id: uuid.UUID = None,
    name: str = "Test Category",
    sort_order: int = 0
) -> TopicCategory:
    """创建Mock的TopicCategory对象"""
    if category_id is None:
        category_id = uuid.uuid4()
    if topic_id is None:
        topic_id = uuid.uuid4()
    
    mock_category = TopicCategory(
        id=category_id,
        topic_id=topic_id,
        name=name,
        sort_order=sort_order
    )
    mock_category.created_at = datetime.now()
    mock_category.updated_at = datetime.now()
    
    return mock_category


def create_mock_category_with_topic(
    category_id: uuid.UUID = None,
    topic_user_id: uuid.UUID = None
) -> TopicCategory:
    """创建Mock的TopicCategory对象（包含topic属性，用于权限检查）"""
    if category_id is None:
        category_id = uuid.uuid4()
    if topic_user_id is None:
        topic_user_id = uuid.uuid4()
    
    mock_topic = create_mock_topic(user_id=topic_user_id)
    mock_category = create_mock_category(category_id=category_id, topic_id=mock_topic.id)
    
    # 设置关联关系
    mock_category.topic = mock_topic
    
    return mock_category


# ==================== 专题管理方法测试 ====================

class TestTopicManagement:
    """专题管理相关测试"""
    
    @pytest.mark.asyncio
    async def test_create_topic_success(
        self, 
        mocker,
        regular_user_id: uuid.UUID,
        regular_user_role: str
    ):
        """
        测试成功创建专题（需要user_id和role参数）
        
        验证点:
        1. 调用 crud.topic.create 一次
        2. 返回创建的 Topic 对象
        """
        # ===== Arrange (准备) =====
        mock_db = mocker.Mock()
        
        topic_in = TopicCreate(
            title="Test Topic",
            description="Test Description",
            banner_url="https://example.com/banner.jpg",
            status=TopicStatus.DRAFT
        )
        
        mock_topic = create_mock_topic(user_id=regular_user_id, title=topic_in.title)
        
        # Mock crud.topic.create
        mock_create = mocker.patch(
            "app.crud.topic.create",
            new_callable=AsyncMock,
            return_value=mock_topic
        )
        
        # ===== Act (执行) =====
        # ← 修改：传递权限参数
        service = TopicService(mock_db)
        result = await service.create_topic(
            topic_in, 
            regular_user_id,  # ← 修改：使用Fixture
            regular_user_role  # ← 新增：权限参数
        )
        
        # ===== Assert (断言) =====
        mock_create.assert_called_once_with(mock_db, topic_in, regular_user_id)
        assert result == mock_topic
        assert result.title == topic_in.title
        assert result.user_id == regular_user_id  # ← 新增：验证user_id被正确设置
        assert result.user_id == regular_user_id  # ← 新增：验证user_id被正确设置


    @pytest.mark.asyncio
    async def test_update_topic_success(self, mocker):
        """
        测试成功更新专题
        
        验证点:
        1. crud.topic.get 被调用
        2. 权限检查通过
        3. crud.topic.update 被调用
        4. 返回更新后的专题
        """
        # Arrange
        mock_db = mocker.Mock()
        user_id = uuid.uuid4()
        topic_id = uuid.uuid4()
        
        mock_topic = create_mock_topic(topic_id=topic_id, user_id=user_id)
        
        update_data = TopicUpdate(
            title="Updated Title",
            status=TopicStatus.PUBLISHED
        )
        
        updated_topic = create_mock_topic(
            topic_id=topic_id,
            user_id=user_id,
            title="Updated Title",
            status=TopicStatus.PUBLISHED
        )
        
        # Mock CRUD functions
        mock_get = mocker.patch(
            "app.crud.topic.get",
            new_callable=AsyncMock,
            return_value=mock_topic
        )
        
        mock_update = mocker.patch(
            "app.crud.topic.update",
            new_callable=AsyncMock,
            return_value=updated_topic
        )
        
        # Act
        service = TopicService(mock_db)
        role = "REGULAR"  # ← 新增：权限参数
        result = await service.update_topic(topic_id, user_id, update_data, role)
        
        # Assert
        mock_get.assert_called_once_with(mock_db, topic_id)
        mock_update.assert_called_once_with(mock_db, mock_topic, update_data)
        assert result == updated_topic
        assert result.title == "Updated Title"


    @pytest.mark.asyncio
    async def test_update_topic_not_found(
        self, 
        mocker,
        regular_user_id: uuid.UUID,
        regular_user_role: str
    ):
        """
        测试更新不存在的专题
        
        验证点:
        1. crud.topic.get 返回 None
        2. 抛出 TopicNotFoundException
        """
        # ===== Arrange (准备) =====
        mock_db = mocker.Mock()
        topic_id = uuid.uuid4()
        
        update_data = TopicUpdate(title="New Title")
        
        # Mock CRUD function to return None
        mocker.patch(
            "app.crud.topic.get",
            new_callable=AsyncMock,
            return_value=None
        )
        
        # ===== Act & Assert (执行和断言) =====
        # ← 修改：传递权限参数
        service = TopicService(mock_db)
        with pytest.raises(TopicNotFoundException):
            await service.update_topic(
                topic_id, 
                regular_user_id,  # ← 修改：使用Fixture
                update_data,
                regular_user_role  # ← 新增：权限参数
            )


    @pytest.mark.asyncio
    async def test_update_topic_permission_denied(
        self, 
        mocker,
        regular_user_id: uuid.UUID,
        regular_user_role: str,
        another_user_id: uuid.UUID
    ):
        """
        测试更新专题权限不足（非Owner，S5场景）
        
        验证点:
        1. crud.topic.get 返回专题（不同user_id）
        2. 抛出 TopicPermissionDeniedException
        """
        # ===== Arrange (准备) =====
        mock_db = mocker.Mock()
        topic_id = uuid.uuid4()
        
        # 专题属于another_user_id
        mock_topic = create_mock_topic(topic_id=topic_id, user_id=another_user_id)
        update_data = TopicUpdate(title="New Title")
        
        # Mock CRUD function
        mocker.patch(
            "app.crud.topic.get",
            new_callable=AsyncMock,
            return_value=mock_topic
        )
        
        # ===== Act & Assert (执行和断言) =====
        # ← 修改：使用regular_user_id尝试更新another_user_id的专题
        service = TopicService(mock_db)
        from app.exceptions import PermissionDeniedException  # ← 修改：使用正确的异常类型
        with pytest.raises(PermissionDeniedException):
            await service.update_topic(
                topic_id, 
                regular_user_id,  # ← 修改：使用Fixture
                update_data,
                regular_user_role  # ← 新增：权限参数
            )


    @pytest.mark.asyncio
    async def test_delete_topic_success(
        self, 
        mocker,
        regular_user_id: uuid.UUID,
        regular_user_role: str
    ):
        """
        测试成功删除专题（需要user_id和role参数）
        
        验证点:
        1. crud.topic.get_with_categories 被调用
        2. 权限检查通过
        3. crud.topic.remove 被调用
        """
        # ===== Arrange (准备) =====
        mock_db = mocker.Mock()
        topic_id = uuid.uuid4()
        
        mock_topic = create_mock_topic(topic_id=topic_id, user_id=regular_user_id)
        mock_topic.categories = []
        
        # Mock CRUD functions
        mock_get = mocker.patch(
            "app.crud.topic.get_with_categories",
            new_callable=AsyncMock,
            return_value=mock_topic
        )
        
        mock_remove = mocker.patch(
            "app.crud.topic.remove",
            new_callable=AsyncMock,
            return_value=mock_topic
        )
        
        # ===== Act (执行) =====
        # ← 修改：传递权限参数
        service = TopicService(mock_db)
        result = await service.delete_topic(
            topic_id, 
            regular_user_id,  # ← 修改：使用Fixture
            regular_user_role  # ← 新增：权限参数
        )
        
        # ===== Assert (断言) =====
        mock_get.assert_called_once_with(mock_db, topic_id)
        mock_remove.assert_called_once_with(mock_db, mock_topic)
        assert result == mock_topic


    @pytest.mark.asyncio
    async def test_delete_topic_permission_denied(self, mocker):
        """
        测试删除专题权限不足
        
        验证点:
        1. crud.topic.get_with_categories 返回专题（不同user_id）
        2. 抛出 TopicPermissionDeniedException
        """
        # Arrange
        mock_db = mocker.Mock()
        owner_user_id = uuid.uuid4()
        different_user_id = uuid.uuid4()
        topic_id = uuid.uuid4()
        
        mock_topic = create_mock_topic(topic_id=topic_id, user_id=owner_user_id)
        
        # Mock CRUD function
        mocker.patch(
            "app.crud.topic.get_with_categories",
            new_callable=AsyncMock,
            return_value=mock_topic
        )
        
        # Act & Assert
        service = TopicService(mock_db)
        from app.exceptions import PermissionDeniedException  # ← 修改：使用正确的异常类型
        role = "REGULAR"  # ← 新增：权限参数
        with pytest.raises(PermissionDeniedException):
            await service.delete_topic(topic_id, different_user_id, role)


    @pytest.mark.asyncio
    async def test_get_topic_list_success_anonymous(self, mocker):
        """
        测试获取专题列表成功（匿名用户，只能看到Published专题，S1场景）
        
        验证点:
        1. crud.topic.get_multi_and_total 被调用（传递None作为权限参数）
        2. 返回正确的列表和总数
        """
        # ===== Arrange (准备) =====
        mock_db = mocker.Mock()
        
        mock_topic1 = create_mock_topic(title="Topic 1", status=TopicStatus.PUBLISHED)
        mock_topic2 = create_mock_topic(title="Topic 2", status=TopicStatus.PUBLISHED)
        
        # Mock CRUD function
        mock_get_multi = mocker.patch(
            "app.crud.topic.get_multi_and_total",
            new_callable=AsyncMock,
            return_value=([mock_topic1, mock_topic2], 2)
        )
        
        # ===== Act (执行) =====
        # ← 修改：传递None作为权限参数（匿名用户）
        service = TopicService(mock_db)
        topics, total = await service.get_topic_list(
            page=1,
            size=10,
            status=None,
            user_id=None,
            role=None,  # ← 修改：使用正确的参数名 role（匿名用户）
            current_user_id=None  # ← 新增：匿名用户
        )
        
        # ===== Assert (断言) =====
        # ← 修改：验证传递了权限参数
        mock_get_multi.assert_called_once()
        call_args = mock_get_multi.call_args
        assert call_args[1]['current_user_id'] is None  # ← 新增：验证权限参数
        assert call_args[1]['current_user_role'] is None  # ← 修改：CRUD层使用current_user_role参数名
        assert len(topics) == 2
        assert total == 2
        assert topics[0].title == "Topic 1"
        assert topics[1].title == "Topic 2"

# ← 新增：测试登录用户场景（S3）
@pytest.mark.asyncio
async def test_get_topic_list_success_as_owner(
    mocker,
    regular_user_id: uuid.UUID,
    regular_user_role: str
):
    """测试获取专题列表（登录用户，可以看到Published+自己的专题，S3场景）"""
    # ===== Arrange (准备) =====
    mock_db = mocker.Mock()
    
    mock_topic1 = create_mock_topic(title="Published Topic", status=TopicStatus.PUBLISHED)
    mock_topic2 = create_mock_topic(title="My Draft Topic", status=TopicStatus.DRAFT, user_id=regular_user_id)
    
    # Mock CRUD function
    mock_get_multi = mocker.patch(
        "app.crud.topic.get_multi_and_total",
        new_callable=AsyncMock,
        return_value=([mock_topic1, mock_topic2], 2)
    )
    
    # ===== Act (执行) =====
    service = TopicService(mock_db)
    topics, total = await service.get_topic_list(
        page=1,
        size=10,
        status=None,
        user_id=None,
        role=regular_user_role,  # ← 修改：使用正确的参数名 role
        current_user_id=regular_user_id  # ← 新增
    )
    
    # ===== Assert (断言) =====
    call_args = mock_get_multi.call_args
    assert call_args[1]['current_user_id'] == regular_user_id  # ← 新增：验证权限参数
    assert call_args[1]['current_user_role'] == regular_user_role  # ← 修改：CRUD层使用current_user_role参数名
    assert len(topics) == 2
    assert total == 2

# ← 新增：测试Admin用户场景（S6）
@pytest.mark.asyncio
async def test_get_topic_list_success_as_admin(
    mocker,
    admin_user_id: uuid.UUID,
    admin_user_role: str
):
    """测试获取专题列表（Admin用户，可以看到所有专题，S6场景）"""
    # ===== Arrange (准备) =====
    mock_db = mocker.Mock()
    
    mock_topic1 = create_mock_topic(title="Published Topic", status=TopicStatus.PUBLISHED)
    mock_topic2 = create_mock_topic(title="Draft Topic", status=TopicStatus.DRAFT)
    
    # Mock CRUD function
    mock_get_multi = mocker.patch(
        "app.crud.topic.get_multi_and_total",
        new_callable=AsyncMock,
        return_value=([mock_topic1, mock_topic2], 2)
    )
    
    # ===== Act (执行) =====
    service = TopicService(mock_db)
    topics, total = await service.get_topic_list(
        page=1,
        size=10,
        status=None,
        user_id=None,
        role=admin_user_role,  # ← 修改：使用正确的参数名 role
        current_user_id=admin_user_id  # ← 新增
    )
    
    # ===== Assert (断言) =====
    call_args = mock_get_multi.call_args
    assert call_args[1]['current_user_id'] == admin_user_id  # ← 新增：验证权限参数
    assert call_args[1]['current_user_role'] == admin_user_role  # ← 修改：CRUD层使用current_user_role参数名
    assert len(topics) == 2
    assert total == 2


    @pytest.mark.asyncio
    async def test_get_topic_detail_success_published(
        self, 
        mocker,
        published_topic
    ):
        """
        测试获取Published专题详情成功（匿名用户可访问，S1场景）
        
        验证点:
        1. crud.topic.get_with_categories 被调用
        2. 返回层级化的专题详情字典
        """
        # ===== Arrange (准备) =====
        mock_db = mocker.Mock()
        topic_id = published_topic.id
        
        mock_topic = create_mock_topic(topic_id=topic_id, status=TopicStatus.PUBLISHED)
        mock_category = create_mock_category(topic_id=topic_id)
        mock_topic.categories = [mock_category]
        
        # Mock CRUD functions
        mock_get = mocker.patch(
            "app.crud.topic.get_with_categories",
            new_callable=AsyncMock,
            return_value=mock_topic
        )
        
        mock_get_rooms = mocker.patch(
            "app.crud.topic.get_rooms_by_category",
            new_callable=AsyncMock,
            return_value=([], 0)
        )
        
        # Mock database execute for LiveSession query
        mock_execute_result = Mock()
        mock_execute_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_execute_result)
        
        # ===== Act (执行) =====
        # ← 修改：传递None作为权限参数（匿名用户）
        service = TopicService(mock_db)
        result = await service.get_topic_detail(
            topic_id,
            user_id=None,  # ← 新增：匿名用户
            role=None      # ← 新增：匿名用户
        )
        
        # ===== Assert (断言) =====
        mock_get.assert_called_once_with(mock_db, topic_id)
        assert isinstance(result, dict)
        assert "id" in result
        assert "categories" in result
        assert len(result["categories"]) == 1

# ← 新增：测试Owner访问自己的Draft专题（S3）
@pytest.mark.asyncio
async def test_get_topic_detail_success_draft_as_owner(
    mocker,
    regular_user_id: uuid.UUID,
    regular_user_role: str,
    draft_topic_owned_by_user
):
    """测试获取Draft专题详情（Owner可访问，S3场景）"""
    # ===== Arrange (准备) =====
    mock_db = mocker.Mock()
    # ← 修改：直接使用uuid，因为测试中会mock所有内容
    # 如果需要使用fixture的id，需要确保fixture正确解析（可能需要在conftest中修复）
    topic_id = uuid.uuid4()
    
    mock_topic = create_mock_topic(topic_id=topic_id, user_id=regular_user_id, status=TopicStatus.DRAFT)
    mock_category = create_mock_category(topic_id=topic_id)
    mock_topic.categories = [mock_category]
    
    # Mock CRUD functions
    mock_get = mocker.patch(
        "app.crud.topic.get_with_categories",
        new_callable=AsyncMock,
        return_value=mock_topic
    )
    
    mock_get_rooms = mocker.patch(
        "app.crud.topic.get_rooms_by_category",
        new_callable=AsyncMock,
        return_value=([], 0)
    )
    
    # Mock database execute for LiveSession query
    mock_execute_result = Mock()
    mock_execute_result.scalar_one_or_none.return_value = None
    mock_db.execute = AsyncMock(return_value=mock_execute_result)
    
    # ===== Act (执行) =====
    service = TopicService(mock_db)
    result = await service.get_topic_detail(
        topic_id,
        user_id=regular_user_id,  # ← 新增
        role=regular_user_role     # ← 新增
    )
    
    # ===== Assert (断言) =====
    mock_get.assert_called_once_with(mock_db, topic_id)
    assert isinstance(result, dict)
    assert result["id"] == str(topic_id)

# ← 新增：测试Admin访问任意Draft专题（S6）
@pytest.mark.asyncio
async def test_get_topic_detail_success_draft_as_admin(
    mocker,
    admin_user_id: uuid.UUID,
    admin_user_role: str,
    draft_topic
):
    """测试获取Draft专题详情（Admin可访问，S6场景）"""
    # ===== Arrange (准备) =====
    mock_db = mocker.Mock()
    # ← 修改：直接使用uuid，因为测试中会mock所有内容
    topic_id = uuid.uuid4()
    
    mock_topic = create_mock_topic(topic_id=topic_id, status=TopicStatus.DRAFT)
    mock_category = create_mock_category(topic_id=topic_id)
    mock_topic.categories = [mock_category]
    
    # Mock CRUD functions
    mock_get = mocker.patch(
        "app.crud.topic.get_with_categories",
        new_callable=AsyncMock,
        return_value=mock_topic
    )
    
    mock_get_rooms = mocker.patch(
        "app.crud.topic.get_rooms_by_category",
        new_callable=AsyncMock,
        return_value=([], 0)
    )
    
    # Mock database execute for LiveSession query
    mock_execute_result = Mock()
    mock_execute_result.scalar_one_or_none.return_value = None
    mock_db.execute = AsyncMock(return_value=mock_execute_result)
    
    # ===== Act (执行) =====
    service = TopicService(mock_db)
    result = await service.get_topic_detail(
        topic_id,
        user_id=admin_user_id,  # ← 新增
        role=admin_user_role     # ← 新增
    )
    
    # ===== Assert (断言) =====
    mock_get.assert_called_once_with(mock_db, topic_id)
    assert isinstance(result, dict)
    assert result["id"] == str(topic_id)


    @pytest.mark.asyncio
    async def test_get_topic_detail_not_found(self, mocker):
        """
        测试获取不存在的专题详情
        
        验证点:
        1. crud.topic.get_with_categories 返回 None
        2. 抛出 TopicNotFoundException
        """
        # Arrange
        mock_db = mocker.Mock()
        topic_id = uuid.uuid4()
        
        # Mock CRUD function to return None
        mocker.patch(
            "app.crud.topic.get_with_categories",
            new_callable=AsyncMock,
            return_value=None
        )
        
        # Act & Assert
        service = TopicService(mock_db)
        with pytest.raises(TopicNotFoundException):
            await service.get_topic_detail(topic_id)


# ==================== 分类管理方法测试 ====================

class TestCategoryManagement:
    """分类管理相关测试"""
    
    @pytest.mark.asyncio
    async def test_create_category_success(
        self, 
        mocker,
        regular_user_id: uuid.UUID,
        regular_user_role: str
    ):
        """
        测试成功创建分类（需要user_id和role参数）
        
        验证点:
        1. crud.topic.get 被调用验证专题存在
        2. 权限检查通过
        3. crud.topic.create_category 被调用
        4. 返回创建的分类
        """
        # ===== Arrange (准备) =====
        mock_db = mocker.Mock()
        topic_id = uuid.uuid4()
        
        mock_topic = create_mock_topic(topic_id=topic_id, user_id=regular_user_id)
        
        category_in = CategoryCreate(
            name="Test Category",
            sort_order=10
        )
        
        mock_category = create_mock_category(topic_id=topic_id, name=category_in.name)
        
        # Mock CRUD functions
        mock_get = mocker.patch(
            "app.crud.topic.get",
            new_callable=AsyncMock,
            return_value=mock_topic
        )
        
        mock_create_category = mocker.patch(
            "app.crud.topic.create_category",
            new_callable=AsyncMock,
            return_value=mock_category
        )
        
        # ===== Act (执行) =====
        # ← 修改：传递权限参数
        service = TopicService(mock_db)
        result = await service.create_category(
            topic_id, 
            regular_user_id,  # ← 修改：使用Fixture
            category_in,
            regular_user_role  # ← 新增：权限参数
        )
        
        # ===== Assert (断言) =====
        mock_get.assert_called_once_with(mock_db, topic_id)
        mock_create_category.assert_called_once_with(mock_db, category_in, topic_id)
        assert result == mock_category


    @pytest.mark.asyncio
    async def test_create_category_topic_not_found(
        self, 
        mocker,
        regular_user_id: uuid.UUID,
        regular_user_role: str
    ):
        """
        测试创建分类时专题不存在
        
        验证点:
        1. crud.topic.get 返回 None
        2. 抛出 TopicNotFoundException
        """
        # ===== Arrange (准备) =====
        mock_db = mocker.Mock()
        topic_id = uuid.uuid4()
        
        category_in = CategoryCreate(name="Test Category", sort_order=10)
        
        # Mock CRUD function to return None
        mocker.patch(
            "app.crud.topic.get",
            new_callable=AsyncMock,
            return_value=None
        )
        
        # ===== Act & Assert (执行和断言) =====
        # ← 修改：传递权限参数
        service = TopicService(mock_db)
        with pytest.raises(TopicNotFoundException):
            await service.create_category(
                topic_id, 
                regular_user_id,  # ← 修改：使用Fixture
                category_in,
                regular_user_role  # ← 新增：权限参数
            )


    @pytest.mark.asyncio
    async def test_create_category_permission_denied(
        self, 
        mocker,
        regular_user_id: uuid.UUID,
        regular_user_role: str,
        another_user_id: uuid.UUID
    ):
        """
        测试创建分类权限不足（非Owner，S5场景）
        
        验证点:
        1. crud.topic.get 返回专题（不同user_id）
        2. 抛出 TopicPermissionDeniedException
        """
        # ===== Arrange (准备) =====
        mock_db = mocker.Mock()
        topic_id = uuid.uuid4()
        
        # 专题属于another_user_id
        mock_topic = create_mock_topic(topic_id=topic_id, user_id=another_user_id)
        category_in = CategoryCreate(name="Test Category", sort_order=10)
        
        # Mock CRUD function
        mocker.patch(
            "app.crud.topic.get",
            new_callable=AsyncMock,
            return_value=mock_topic
        )
        
        # ===== Act & Assert (执行和断言) =====
        # ← 修改：使用regular_user_id尝试在another_user_id的专题中创建分类
        service = TopicService(mock_db)
        from app.exceptions import PermissionDeniedException  # ← 修改：使用正确的异常类型
        with pytest.raises(PermissionDeniedException):
            await service.create_category(
                topic_id, 
                regular_user_id,  # ← 修改：使用Fixture
                category_in,
                regular_user_role  # ← 新增：权限参数
            )


    @pytest.mark.asyncio
    async def test_update_category_success(
        self, 
        mocker,
        regular_user_id: uuid.UUID,
        regular_user_role: str
    ):
        """
        测试成功更新分类（需要user_id和role参数）
        
        验证点:
        1. crud.topic.get_category_with_topic 被调用
        2. 权限检查通过
        3. crud.topic.update_category 被调用
        """
        # ===== Arrange (准备) =====
        mock_db = mocker.Mock()
        category_id = uuid.uuid4()
        
        mock_category = create_mock_category_with_topic(
            category_id=category_id,
            topic_user_id=regular_user_id
        )
        
        update_data = CategoryUpdate(name="Updated Category")
        
        updated_category = create_mock_category(
            category_id=category_id,
            name="Updated Category"
        )
        
        # Mock CRUD functions
        mock_get = mocker.patch(
            "app.crud.topic.get_category_with_topic",
            new_callable=AsyncMock,
            return_value=mock_category
        )
        
        mock_update = mocker.patch(
            "app.crud.topic.update_category",
            new_callable=AsyncMock,
            return_value=updated_category
        )
        
        # ===== Act (执行) =====
        # ← 修改：传递权限参数
        service = TopicService(mock_db)
        result = await service.update_category(
            category_id, 
            regular_user_id,  # ← 修改：使用Fixture
            update_data,
            regular_user_role  # ← 新增：权限参数
        )
        
        # ===== Assert (断言) =====
        mock_get.assert_called_once_with(mock_db, category_id)
        mock_update.assert_called_once_with(mock_db, mock_category, update_data)
        assert result == updated_category


    @pytest.mark.asyncio
    async def test_update_category_not_found(self, mocker):
        """
        测试更新不存在的分类
        
        验证点:
        1. crud.topic.get_category_with_topic 返回 None
        2. 抛出 CategoryNotFoundException
        """
        # Arrange
        mock_db = mocker.Mock()
        user_id = uuid.uuid4()
        category_id = uuid.uuid4()
        
        update_data = CategoryUpdate(name="New Name")
        
        # Mock CRUD function to return None
        mocker.patch(
            "app.crud.topic.get_category_with_topic",
            new_callable=AsyncMock,
            return_value=None
        )
        
        # Act & Assert
        service = TopicService(mock_db)
        role = "REGULAR"  # ← 新增：权限参数
        with pytest.raises(CategoryNotFoundException):
            await service.update_category(category_id, user_id, update_data, role)


    @pytest.mark.asyncio
    async def test_update_category_permission_denied(self, mocker):
        """
        测试更新分类权限不足
        
        验证点:
        1. crud.topic.get_category_with_topic 返回分类（topic的user_id不匹配）
        2. 抛出 TopicPermissionDeniedException
        """
        # Arrange
        mock_db = mocker.Mock()
        owner_user_id = uuid.uuid4()
        different_user_id = uuid.uuid4()
        category_id = uuid.uuid4()
        
        mock_category = create_mock_category_with_topic(
            category_id=category_id,
            topic_user_id=owner_user_id
        )
        
        update_data = CategoryUpdate(name="New Name")
        
        # Mock CRUD function
        mocker.patch(
            "app.crud.topic.get_category_with_topic",
            new_callable=AsyncMock,
            return_value=mock_category
        )
        
        # ===== Act & Assert (执行和断言) =====
        # ← 修改：使用different_user_id尝试更新owner_user_id的专题的分类
        service = TopicService(mock_db)
        from app.exceptions import PermissionDeniedException  # ← 修改：使用正确的异常类型
        role = "REGULAR"  # ← 新增：权限参数
        with pytest.raises(PermissionDeniedException):
            await service.update_category(
                category_id, 
                different_user_id,  # ← 修改：使用不同的用户ID
                update_data,
                role  # ← 修改：使用定义的role变量
            )


    @pytest.mark.asyncio
    async def test_delete_category_success(
        self, 
        mocker,
        regular_user_id: uuid.UUID,
        regular_user_role: str
    ):
        """
        测试成功删除分类（需要user_id和role参数）
        
        验证点:
        1. crud.topic.get_category_with_topic 被调用
        2. 权限检查通过
        3. crud.topic.remove_category 被调用
        """
        # ===== Arrange (准备) =====
        mock_db = mocker.Mock()
        category_id = uuid.uuid4()
        
        mock_category = create_mock_category_with_topic(
            category_id=category_id,
            topic_user_id=regular_user_id
        )
        
        # Mock CRUD functions
        mock_get = mocker.patch(
            "app.crud.topic.get_category_with_topic",
            new_callable=AsyncMock,
            return_value=mock_category
        )
        
        mock_remove = mocker.patch(
            "app.crud.topic.remove_category",
            new_callable=AsyncMock,
            return_value=mock_category
        )
        
        # ===== Act (执行) =====
        # ← 修改：传递权限参数
        service = TopicService(mock_db)
        result = await service.delete_category(
            category_id, 
            regular_user_id,  # ← 修改：使用Fixture
            regular_user_role  # ← 新增：权限参数
        )
        
        # ===== Assert (断言) =====
        mock_get.assert_called_once_with(mock_db, category_id)
        mock_remove.assert_called_once_with(mock_db, mock_category)
        assert result == mock_category


    @pytest.mark.asyncio
    async def test_get_category_list_success(self, mocker):
        """
        测试获取分类列表成功
        
        验证点:
        1. crud.topic.get 被调用验证专题存在
        2. crud.topic.get_categories_by_topic 被调用
        3. 返回正确的列表和总数
        """
        # Arrange
        mock_db = mocker.Mock()
        topic_id = uuid.uuid4()
        
        # ← 修改：创建PUBLISHED状态的专题，允许匿名用户访问
        mock_topic = create_mock_topic(topic_id=topic_id, status=TopicStatus.PUBLISHED)
        mock_category1 = create_mock_category(topic_id=topic_id, name="Category 1")
        mock_category2 = create_mock_category(topic_id=topic_id, name="Category 2")
        
        # Mock CRUD functions
        mock_get = mocker.patch(
            "app.crud.topic.get",
            new_callable=AsyncMock,
            return_value=mock_topic
        )
        
        mock_get_categories = mocker.patch(
            "app.crud.topic.get_categories_by_topic",
            new_callable=AsyncMock,
            return_value=([mock_category1, mock_category2], 2)
        )
        
        # Act
        service = TopicService(mock_db)
        # ← 修改：get_category_list现在需要权限参数（支持匿名访问）
        categories, total = await service.get_category_list(topic_id, page=1, size=10, user_id=None, role=None)
        
        # Assert
        mock_get.assert_called_once_with(mock_db, topic_id)
        mock_get_categories.assert_called_once()
        assert len(categories) == 2
        assert total == 2


    @pytest.mark.asyncio
    async def test_get_category_list_topic_not_found(self, mocker):
        """
        测试获取分类列表时专题不存在
        
        验证点:
        1. crud.topic.get 返回 None
        2. 抛出 TopicNotFoundException
        """
        # Arrange
        mock_db = mocker.Mock()
        topic_id = uuid.uuid4()
        
        # Mock CRUD function to return None
        mocker.patch(
            "app.crud.topic.get",
            new_callable=AsyncMock,
            return_value=None
        )
        
        # Act & Assert
        service = TopicService(mock_db)
        with pytest.raises(TopicNotFoundException):
            await service.get_category_list(topic_id, page=1, size=10)


# ==================== 直播间关联方法测试 ====================

class TestRoomAssociation:
    """直播间关联相关测试"""
    
    @pytest.mark.asyncio
    async def test_add_rooms_to_category_success(self, mocker):
        """
        测试成功添加直播间到分类
        
        验证点:
        1. 分类存在且权限检查通过
        2. 所有直播间都存在
        3. 没有已关联的直播间
        4. crud.topic.batch_add_rooms 被调用
        """
        # Arrange
        mock_db = mocker.Mock()
        user_id = uuid.uuid4()
        category_id = uuid.uuid4()
        room_id1 = uuid.uuid4()
        room_id2 = uuid.uuid4()
        
        mock_category = create_mock_category_with_topic(
            category_id=category_id,
            topic_user_id=user_id
        )
        
        room_associations = [
            RoomAssociation(room_id=room_id1, sort_order=10),
            RoomAssociation(room_id=room_id2, sort_order=20)
        ]
        
        mock_associations = [Mock(), Mock()]
        
        # Mock CRUD functions
        mock_get_category = mocker.patch(
            "app.crud.topic.get_category_with_topic",
            new_callable=AsyncMock,
            return_value=mock_category
        )
        
        # Mock database execute for room existence check
        mock_execute_result = Mock()
        mock_execute_result.all.return_value = [(room_id1,), (room_id2,)]
        mock_db.execute = AsyncMock(return_value=mock_execute_result)
        
        # Mock check_room_association_exists
        mock_check_exists = mocker.patch(
            "app.crud.topic.check_room_association_exists",
            new_callable=AsyncMock,
            return_value=False
        )
        
        # Mock batch_add_rooms
        mock_batch_add = mocker.patch(
            "app.crud.topic.batch_add_rooms",
            new_callable=AsyncMock,
            return_value=mock_associations
        )
        
        # Act
        service = TopicService(mock_db)
        role = "REGULAR"  # ← 新增：权限参数
        result = await service.add_rooms_to_category(
            category_id,
            user_id,
            room_associations,
            role  # ← 新增：权限参数
        )
        
        # Assert
        mock_get_category.assert_called_once_with(mock_db, category_id)
        mock_batch_add.assert_called_once()
        assert result == mock_associations


    @pytest.mark.asyncio
    async def test_add_rooms_to_category_permission_denied(self, mocker):
        """
        测试添加直播间权限不足
        
        验证点:
        1. crud.topic.get_category_with_topic 返回分类（user_id不匹配）
        2. 抛出 TopicPermissionDeniedException
        """
        # Arrange
        mock_db = mocker.Mock()
        owner_user_id = uuid.uuid4()
        different_user_id = uuid.uuid4()
        category_id = uuid.uuid4()
        
        mock_category = create_mock_category_with_topic(
            category_id=category_id,
            topic_user_id=owner_user_id
        )
        
        room_associations = [
            RoomAssociation(room_id=uuid.uuid4(), sort_order=10)
        ]
        
        # Mock CRUD function
        mocker.patch(
            "app.crud.topic.get_category_with_topic",
            new_callable=AsyncMock,
            return_value=mock_category
        )
        
        # Act & Assert
        service = TopicService(mock_db)
        from app.exceptions import PermissionDeniedException  # ← 修改：使用正确的异常类型
        role = "REGULAR"  # ← 新增：权限参数
        with pytest.raises(PermissionDeniedException):
            await service.add_rooms_to_category(
                category_id,
                different_user_id,
                room_associations,
                role  # ← 新增：权限参数
            )


    @pytest.mark.asyncio
    async def test_add_rooms_to_category_room_not_found(self, mocker):
        """
        测试添加不存在的直播间
        
        验证点:
        1. 数据库查询返回部分room_ids（有缺失）
        2. 抛出 RoomNotFoundException
        """
        # Arrange
        mock_db = mocker.Mock()
        user_id = uuid.uuid4()
        category_id = uuid.uuid4()
        room_id1 = uuid.uuid4()
        room_id2 = uuid.uuid4()
        
        mock_category = create_mock_category_with_topic(
            category_id=category_id,
            topic_user_id=user_id
        )
        
        room_associations = [
            RoomAssociation(room_id=room_id1, sort_order=10),
            RoomAssociation(room_id=room_id2, sort_order=20)
        ]
        
        # Mock CRUD function
        mocker.patch(
            "app.crud.topic.get_category_with_topic",
            new_callable=AsyncMock,
            return_value=mock_category
        )
        
        # Mock database execute - only return one room (missing one)
        mock_execute_result = Mock()
        mock_execute_result.all.return_value = [(room_id1,)]
        mock_db.execute = AsyncMock(return_value=mock_execute_result)
        
        # Act & Assert
        service = TopicService(mock_db)
        role = "REGULAR"  # ← 新增：权限参数
        with pytest.raises(RoomNotFoundException):
            await service.add_rooms_to_category(
                category_id,
                user_id,
                room_associations,
                role  # ← 新增：权限参数
            )


    @pytest.mark.asyncio
    async def test_add_rooms_to_category_already_associated(self, mocker):
        """
        测试添加已关联的直播间
        
        验证点:
        1. crud.topic.check_room_association_exists 返回 True
        2. 抛出 RoomAlreadyAssociatedException
        """
        # Arrange
        mock_db = mocker.Mock()
        user_id = uuid.uuid4()
        category_id = uuid.uuid4()
        room_id = uuid.uuid4()
        
        mock_category = create_mock_category_with_topic(
            category_id=category_id,
            topic_user_id=user_id
        )
        
        room_associations = [
            RoomAssociation(room_id=room_id, sort_order=10)
        ]
        
        # Mock CRUD functions
        mocker.patch(
            "app.crud.topic.get_category_with_topic",
            new_callable=AsyncMock,
            return_value=mock_category
        )
        
        # Mock database execute for room existence check
        mock_execute_result = Mock()
        mock_execute_result.all.return_value = [(room_id,)]
        mock_db.execute = AsyncMock(return_value=mock_execute_result)
        
        # Mock check_room_association_exists - return True
        mocker.patch(
            "app.crud.topic.check_room_association_exists",
            new_callable=AsyncMock,
            return_value=True
        )
        
        # Act & Assert
        service = TopicService(mock_db)
        role = "REGULAR"  # ← 新增：权限参数
        with pytest.raises(RoomAlreadyAssociatedException):
            await service.add_rooms_to_category(
                category_id,
                user_id,
                room_associations,
                role  # ← 新增：权限参数
            )


    @pytest.mark.asyncio
    async def test_get_rooms_in_category_success(self, mocker):
        """
        测试获取分类下的直播间列表成功
        
        验证点:
        1. crud.topic.get_category 被调用验证分类存在
        2. crud.topic.get_rooms_by_category 被调用
        3. 返回包含live_status的房间列表
        """
        # Arrange
        mock_db = mocker.Mock()
        category_id = uuid.uuid4()
        
        # ← 修改：创建包含topic的分类对象（用于权限检查）
        # ← Published专题，匿名用户可访问
        mock_topic_for_perm = create_mock_topic(status=TopicStatus.PUBLISHED)
        mock_category = create_mock_category_with_topic(
            category_id=category_id,
            topic_user_id=mock_topic_for_perm.user_id
        )
        # ← 确保分类关联的topic状态是PUBLISHED
        mock_category.topic.status = TopicStatus.PUBLISHED
        
        rooms_data = [
            {"room_id": str(uuid.uuid4()), "title": "Room 1"},
            {"room_id": str(uuid.uuid4()), "title": "Room 2"}
        ]
        
        # Mock CRUD functions
        # ← 修改：使用get_category_with_topic（方法内部会调用这个方法）
        mock_get_category = mocker.patch(
            "app.crud.topic.get_category_with_topic",
            new_callable=AsyncMock,
            return_value=mock_category
        )
        
        mock_get_rooms = mocker.patch(
            "app.crud.topic.get_rooms_by_category",
            new_callable=AsyncMock,
            return_value=(rooms_data, 2)
        )
        
        # Mock database execute for LiveSession status
        mock_execute_result = Mock()
        mock_execute_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_execute_result)
        
        # Act
        service = TopicService(mock_db)
        # ← 修改：get_rooms_in_category现在需要权限参数（支持匿名访问）
        rooms, total = await service.get_rooms_in_category(category_id, page=1, size=10, user_id=None, role=None)
        
        # Assert
        mock_get_category.assert_called_once_with(mock_db, category_id)
        mock_get_rooms.assert_called_once()
        assert len(rooms) == 2
        assert total == 2


    @pytest.mark.asyncio
    async def test_update_room_sort_order_success(self, mocker):
        """
        测试成功更新直播间排序
        
        验证点:
        1. 分类存在且权限检查通过
        2. crud.topic.update_room_sort_order 被调用
        3. 返回更新数量
        """
        # Arrange
        mock_db = mocker.Mock()
        user_id = uuid.uuid4()
        category_id = uuid.uuid4()
        
        mock_category = create_mock_category_with_topic(
            category_id=category_id,
            topic_user_id=user_id
        )
        
        room_sort_updates = [
            {"room_id": uuid.uuid4(), "sort_order": 100},
            {"room_id": uuid.uuid4(), "sort_order": 200}
        ]
        
        # Mock CRUD functions
        mock_get_category = mocker.patch(
            "app.crud.topic.get_category_with_topic",
            new_callable=AsyncMock,
            return_value=mock_category
        )
        
        mock_update_sort = mocker.patch(
            "app.crud.topic.update_room_sort_order",
            new_callable=AsyncMock,
            return_value=2
        )
        
        # Act
        service = TopicService(mock_db)
        role = "REGULAR"  # ← 新增：权限参数
        result = await service.update_room_sort_order(
            category_id,
            user_id,
            room_sort_updates,
            role  # ← 新增：权限参数
        )
        
        # Assert
        mock_get_category.assert_called_once_with(mock_db, category_id)
        mock_update_sort.assert_called_once_with(mock_db, category_id, room_sort_updates)
        assert result == 2


    @pytest.mark.asyncio
    async def test_remove_rooms_from_category_success(self, mocker):
        """
        测试成功移除直播间
        
        验证点:
        1. 分类存在且权限检查通过
        2. crud.topic.batch_remove_rooms 被调用
        3. 返回删除数量
        """
        # Arrange
        mock_db = mocker.Mock()
        user_id = uuid.uuid4()
        category_id = uuid.uuid4()
        
        mock_category = create_mock_category_with_topic(
            category_id=category_id,
            topic_user_id=user_id
        )
        
        room_ids = [uuid.uuid4(), uuid.uuid4()]
        
        # Mock CRUD functions
        mock_get_category = mocker.patch(
            "app.crud.topic.get_category_with_topic",
            new_callable=AsyncMock,
            return_value=mock_category
        )
        
        mock_batch_remove = mocker.patch(
            "app.crud.topic.batch_remove_rooms",
            new_callable=AsyncMock,
            return_value=2
        )
        
        # Act
        service = TopicService(mock_db)
        role = "REGULAR"  # ← 新增：权限参数
        result = await service.remove_rooms_from_category(
            category_id,
            user_id,
            room_ids,
            role  # ← 新增：权限参数
        )
        
        # Assert
        mock_get_category.assert_called_once_with(mock_db, category_id)
        mock_batch_remove.assert_called_once_with(mock_db, category_id, room_ids)
        assert result == 2


# ==================== 辅助查询方法测试 ====================

class TestAuxiliaryQueries:
    """辅助查询相关测试"""
    
    @pytest.mark.asyncio
    async def test_get_topics_by_room_success(self, mocker):
        """
        测试获取直播间关联的专题成功
        
        验证点:
        1. 数据库查询验证直播间存在
        2. crud.topic.get_topics_by_room 被调用
        3. 返回专题列表
        """
        # Arrange
        mock_db = mocker.Mock()
        room_id = uuid.uuid4()
        user_id = None  # ← 匿名用户
        role = None  # ← 匿名用户
        
        # Mock database execute for LiveRoom existence check
        # ← 修改：创建公开房间（is_private=False）以通过权限检查
        mock_room = Mock()
        mock_room.id = room_id
        mock_room.is_private = False  # ← 公开房间，匿名用户可访问
        mock_execute_result = Mock()
        mock_execute_result.scalar_one_or_none.return_value = mock_room
        mock_db.execute = AsyncMock(return_value=mock_execute_result)
        
        topics_data = [
            {"topic_id": str(uuid.uuid4()), "topic_title": "Topic 1"},
            {"topic_id": str(uuid.uuid4()), "topic_title": "Topic 2"}
        ]
        
        # Mock CRUD function
        mock_get_topics = mocker.patch(
            "app.crud.topic.get_topics_by_room",
            new_callable=AsyncMock,
            return_value=topics_data
        )
        
        # Act
        service = TopicService(mock_db)
        result = await service.get_topics_by_room(room_id, user_id=user_id, role=role)  # ← 新增：权限参数
        
        # Assert
        # ← 修改：验证调用时传递了权限参数
        mock_get_topics.assert_called_once_with(mock_db, room_id=room_id, user_id=user_id, role=role)
        assert len(result) == 2


    @pytest.mark.asyncio
    async def test_get_topics_by_room_not_found(self, mocker):
        """
        测试获取不存在的直播间的专题
        
        验证点:
        1. 数据库查询返回 None（直播间不存在）
        2. 抛出 RoomNotFoundException
        """
        # Arrange
        mock_db = mocker.Mock()
        room_id = uuid.uuid4()
        
        # Mock database execute - return None
        mock_execute_result = Mock()
        mock_execute_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_execute_result)
        
        # Act & Assert
        service = TopicService(mock_db)
        # ← 修改：添加权限参数（匿名用户）
        with pytest.raises(RoomNotFoundException):
            await service.get_topics_by_room(room_id, user_id=None, role=None)


    @pytest.mark.asyncio
    async def test_batch_get_room_status_success(self, mocker):
        """
        测试批量获取直播间状态成功
        
        验证点:
        1. 所有直播间都存在
        2. 返回包含状态信息的列表
        """
        # Arrange
        mock_db = mocker.Mock()
        room_id1 = uuid.uuid4()
        room_id2 = uuid.uuid4()
        room_ids = [room_id1, room_id2]
        
        # Mock LiveRoom objects
        mock_room1 = Mock()
        mock_room1.id = room_id1
        mock_room1.is_private = False  # ← 修改：公开房间以通过权限检查
        mock_room2 = Mock()
        mock_room2.id = room_id2
        mock_room2.is_private = False  # ← 修改：公开房间以通过权限检查
        
        # Mock database execute for LiveRoom query
        mock_rooms_result = Mock()
        mock_rooms_result.scalars.return_value.all.return_value = [mock_room1, mock_room2]
        
        # Mock database execute for LiveSession query
        mock_session_result = Mock()
        mock_session_result.scalar_one_or_none.return_value = None
        
        # Setup execute to return different results based on call order
        mock_db.execute = AsyncMock(side_effect=[
            mock_rooms_result,
            mock_session_result,
            mock_session_result
        ])
        
        # Act
        service = TopicService(mock_db)
        # ← 修改：添加权限参数（匿名用户）
        result = await service.batch_get_room_status(room_ids, user_id=None, role=None)
        
        # Assert
        assert len(result) == 2
        assert result[0]["room_id"] == str(room_id1)
        assert result[1]["room_id"] == str(room_id2)


    @pytest.mark.asyncio
    async def test_batch_get_room_status_exceeds_limit(self, mocker):
        """
        测试批量获取直播间状态超过限制
        
        验证点:
        1. room_ids列表超过100个
        2. 抛出 ValueError
        """
        # Arrange
        mock_db = mocker.Mock()
        room_ids = [uuid.uuid4() for _ in range(101)]
        
        # Act & Assert
        service = TopicService(mock_db)
        with pytest.raises(ValueError):
            await service.batch_get_room_status(room_ids)


    @pytest.mark.asyncio
    async def test_batch_get_room_status_some_not_found(self, mocker):
        """
        测试批量获取状态时部分直播间不存在
        
        验证点:
        1. 数据库查询返回部分LiveRoom（有缺失）
        2. 抛出 RoomNotFoundException
        """
        # Arrange
        mock_db = mocker.Mock()
        room_id1 = uuid.uuid4()
        room_id2 = uuid.uuid4()
        room_ids = [room_id1, room_id2]
        
        # Mock LiveRoom - only return one
        mock_room1 = Mock()
        mock_room1.id = room_id1
        
        # Mock database execute
        mock_rooms_result = Mock()
        mock_rooms_result.scalars.return_value.all.return_value = [mock_room1]
        mock_db.execute = AsyncMock(return_value=mock_rooms_result)
        
        # Act & Assert
        service = TopicService(mock_db)
        with pytest.raises(RoomNotFoundException):
            await service.batch_get_room_status(room_ids)

