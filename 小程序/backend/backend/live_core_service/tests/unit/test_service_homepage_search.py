"""
首页与搜索模块的Service层单元测试

测试对象：app/services/homepage_search_service.py
测试模式：incremental（增量测试）
测试策略：Academic Testing（使用mock）
"""
import uuid
import pytest
from unittest.mock import AsyncMock, patch, MagicMock, Mock
from datetime import datetime

from app.services.homepage_search_service import HomepageSearchService
from app.schemas.homepage_search import (
    FeaturedContentCreate,
    FeaturedContentUpdate,
    FeaturedContentItem,
    LiveStatusEnum,
    HomepageHostInfo,
    HomepageStatusData
)
from app.exceptions import (
    PermissionDeniedException,
    NotFoundException,
    InvalidParameterException
)


# ==================== Fixtures ====================

@pytest.fixture
def mock_db():
    """Mock数据库会话"""
    db = AsyncMock()
    db.execute = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    return db


@pytest.fixture
def service():
    """创建Service实例"""
    return HomepageSearchService()


@pytest.fixture
def mock_featured_content():
    """Mock焦点图对象"""
    content = MagicMock()
    content.id = uuid.uuid4()
    content.title = "测试焦点图"
    content.subtitle = "测试副标题"
    content.image_url = "https://example.com/image.jpg"
    content.target_type = "room"
    content.target_id = uuid.uuid4()
    content.target_url = None
    content.sort_order = 0
    content.is_active = True
    content.start_at = None
    content.end_at = None
    content.created_at = datetime.utcnow()
    content.updated_at = datetime.utcnow()
    return content


# ==================== Phase1: 焦点图Service测试 ====================

@pytest.mark.asyncio
async def test_get_featured_content_list_success(service, mock_db, mock_featured_content):
    """测试获取焦点图列表（公开接口）- 成功"""
    # ===== Arrange (准备) =====
    with patch('app.services.homepage_search_service.crud') as mock_crud:
        mock_crud.get_featured_content_list = AsyncMock(return_value=[mock_featured_content])
        
        # ===== Act (执行) =====
        result = await service.get_featured_content_list(mock_db)
        
        # ===== Assert (断言) =====
        assert result["code"] == 200
        assert result["message"] == "success"
        assert len(result["data"]) == 1
        # 验证调用CRUD层时使用的参数
        mock_crud.get_featured_content_list.assert_called_once_with(
            mock_db, include_inactive=False
        )


@pytest.mark.asyncio
async def test_get_featured_content_list_empty(service, mock_db):
    """测试获取焦点图列表 - 空列表"""
    # ===== Arrange (准备) =====
    with patch('app.services.homepage_search_service.crud') as mock_crud:
        mock_crud.get_featured_content_list = AsyncMock(return_value=[])
        
        # ===== Act (执行) =====
        result = await service.get_featured_content_list(mock_db)
        
        # ===== Assert (断言) =====
        assert result["code"] == 200
        assert len(result["data"]) == 0


@pytest.mark.asyncio
async def test_get_featured_content_list_admin_success(service, mock_db, mock_featured_content):
    """测试获取焦点图列表（管理员接口）- 成功"""
    # ===== Arrange (准备) =====
    admin_id = uuid.uuid4()
    admin_role = "ADMIN"
    
    with patch('app.services.homepage_search_service.crud') as mock_crud:
        mock_crud.get_featured_content_list = AsyncMock(return_value=[mock_featured_content])
        
        # ===== Act (执行) =====
        result = await service.get_featured_content_list_admin(mock_db, admin_id, admin_role)
        
        # ===== Assert (断言) =====
        assert result["code"] == 200
        assert len(result["data"]) == 1
        # 验证调用CRUD层时包含了管理员参数
        mock_crud.get_featured_content_list.assert_called_once_with(
            mock_db, include_inactive=True, include_scheduled=True
        )


@pytest.mark.asyncio
async def test_get_featured_content_list_admin_permission_denied(service, mock_db):
    """测试获取焦点图列表（管理员接口）- 权限不足"""
    # ===== Arrange (准备) =====
    user_id = uuid.uuid4()
    regular_role = "REGULAR"
    
    # ===== Act & Assert (执行和断言) =====
    with pytest.raises(PermissionDeniedException):
        await service.get_featured_content_list_admin(mock_db, user_id, regular_role)


# ==================== get_featured_content_list_admin_paginated 测试（增量） ====================

@pytest.mark.asyncio
async def test_get_featured_content_list_admin_paginated_success(service, mock_db, mock_featured_content):
    """测试获取焦点图列表（管理员分页）- 成功"""
    # ===== Arrange (准备) =====
    admin_id = uuid.uuid4()
    admin_role = "ADMIN"
    with patch('app.services.homepage_search_service.crud') as mock_crud:
        mock_crud.get_featured_content_list_paginated = AsyncMock(return_value=([mock_featured_content], 1))
        # ===== Act (执行) =====
        result = await service.get_featured_content_list_admin_paginated(
            mock_db, page=1, size=10, current_user_id=admin_id, role=admin_role
        )
        # ===== Assert (断言) =====
        assert result["code"] == 200
        assert result["data"]["total"] == 1
        assert result["data"]["page"] == 1
        assert result["data"]["size"] == 10
        assert len(result["data"]["items"]) == 1
        mock_crud.get_featured_content_list_paginated.assert_called_once_with(
            mock_db, page=1, size=10, q=None, search_type=None
        )


@pytest.mark.asyncio
async def test_get_featured_content_list_admin_paginated_permission_denied(service, mock_db):
    """测试获取焦点图列表（管理员分页）- 权限不足"""
    user_id = uuid.uuid4()
    regular_role = "REGULAR"
    with pytest.raises(PermissionDeniedException):
        await service.get_featured_content_list_admin_paginated(
            mock_db, page=1, size=10, current_user_id=user_id, role=regular_role
        )


@pytest.mark.asyncio
async def test_get_featured_content_list_admin_paginated_passes_q_and_search_type(service, mock_db, mock_featured_content):
    """测试管理员分页列表 - 透传 q、search_type 给 CRUD"""
    admin_id = uuid.uuid4()
    admin_role = "ADMIN"
    with patch('app.services.homepage_search_service.crud') as mock_crud:
        mock_crud.get_featured_content_list_paginated = AsyncMock(return_value=([mock_featured_content], 1))
        result = await service.get_featured_content_list_admin_paginated(
            mock_db, page=2, size=5, current_user_id=admin_id, role=admin_role,
            q="关键词", search_type="name"
        )
        assert result["code"] == 200
        mock_crud.get_featured_content_list_paginated.assert_called_once_with(
            mock_db, page=2, size=5, q="关键词", search_type="name"
        )


@pytest.mark.asyncio
async def test_upload_featured_content_image_success(service, mock_db, mock_featured_content):
    """测试上传焦点图图片 - 成功"""
    admin_id = uuid.uuid4()
    admin_role = "ADMIN"
    content_id = uuid.uuid4()
    mock_file = Mock()
    mock_file.filename = "test.jpg"
    url_path = "/media/featured_content/xxx/image_123.jpg"
    mock_featured_content.image_url = url_path
    with patch('app.services.homepage_search_service.crud') as mock_crud:
        with patch('app.core.file_handler.FileHandler.save_featured_content_image', new_callable=AsyncMock, return_value=url_path):
            mock_crud.get_featured_content_by_id = AsyncMock(return_value=mock_featured_content)
            mock_crud.update_featured_content = AsyncMock(return_value=mock_featured_content)
            result = await service.upload_featured_content_image(
                mock_db, content_id, mock_file, admin_id, admin_role
            )
    assert result["code"] == 200
    assert result["data"]["image_url"] == url_path


@pytest.mark.asyncio
async def test_upload_featured_content_image_permission_denied(service, mock_db):
    """测试上传焦点图图片 - 权限不足"""
    content_id = uuid.uuid4()
    mock_file = Mock()
    with pytest.raises(PermissionDeniedException):
        await service.upload_featured_content_image(
            mock_db, content_id, mock_file, uuid.uuid4(), "REGULAR"
        )


@pytest.mark.asyncio
async def test_upload_featured_content_image_not_found(service, mock_db):
    """测试上传焦点图图片 - 焦点图不存在"""
    admin_id = uuid.uuid4()
    admin_role = "ADMIN"
    content_id = uuid.uuid4()
    mock_file = Mock()
    with patch('app.services.homepage_search_service.crud') as mock_crud:
        mock_crud.get_featured_content_by_id = AsyncMock(return_value=None)
        with pytest.raises(NotFoundException):
            await service.upload_featured_content_image(
                mock_db, content_id, mock_file, admin_id, admin_role
            )


@pytest.mark.asyncio
async def test_create_featured_content_success(service, mock_db, mock_featured_content):
    """测试创建焦点图 - 成功"""
    # ===== Arrange (准备) =====
    admin_id = uuid.uuid4()
    admin_role = "ADMIN"
    content_data = FeaturedContentCreate(
        title="新焦点图",
        image_url="https://example.com/new.jpg"
    )
    
    with patch('app.services.homepage_search_service.crud') as mock_crud:
        mock_crud.create_featured_content = AsyncMock(return_value=mock_featured_content)
        
        # ===== Act (执行) =====
        result = await service.create_featured_content(mock_db, content_data, admin_id, admin_role)
        
        # ===== Assert (断言) =====
        assert result["code"] == 200
        assert result["data"] is not None
        mock_crud.create_featured_content.assert_called_once()


@pytest.mark.asyncio
async def test_create_featured_content_permission_denied(service, mock_db):
    """测试创建焦点图 - 权限不足"""
    # ===== Arrange (准备) =====
    user_id = uuid.uuid4()
    regular_role = "REGULAR"
    content_data = FeaturedContentCreate(
        title="新焦点图",
        image_url="https://example.com/new.jpg"
    )
    
    # ===== Act & Assert (执行和断言) =====
    with pytest.raises(PermissionDeniedException):
        await service.create_featured_content(mock_db, content_data, user_id, regular_role)


@pytest.mark.asyncio
async def test_update_featured_content_success(service, mock_db, mock_featured_content):
    """测试更新焦点图 - 成功"""
    # ===== Arrange (准备) =====
    admin_id = uuid.uuid4()
    admin_role = "ADMIN"
    content_id = uuid.uuid4()
    update_data = FeaturedContentUpdate(title="更新后的标题")
    
    with patch('app.services.homepage_search_service.crud') as mock_crud:
        mock_crud.update_featured_content = AsyncMock(return_value=mock_featured_content)
        
        # ===== Act (执行) =====
        result = await service.update_featured_content(mock_db, content_id, update_data, admin_id, admin_role)
        
        # ===== Assert (断言) =====
        assert result["code"] == 200
        assert result["data"] is not None


@pytest.mark.asyncio
async def test_update_featured_content_not_found(service, mock_db):
    """测试更新焦点图 - 不存在"""
    # ===== Arrange (准备) =====
    admin_id = uuid.uuid4()
    admin_role = "ADMIN"
    content_id = uuid.uuid4()
    update_data = FeaturedContentUpdate(title="更新后的标题")
    
    with patch('app.services.homepage_search_service.crud') as mock_crud:
        mock_crud.update_featured_content = AsyncMock(return_value=None)
        
        # ===== Act & Assert (执行和断言) =====
        with pytest.raises(NotFoundException):
            await service.update_featured_content(mock_db, content_id, update_data, admin_id, admin_role)


@pytest.mark.asyncio
async def test_delete_featured_content_success(service, mock_db):
    """测试删除焦点图 - 成功"""
    # ===== Arrange (准备) =====
    admin_id = uuid.uuid4()
    admin_role = "ADMIN"
    content_id = uuid.uuid4()
    
    with patch('app.services.homepage_search_service.crud') as mock_crud:
        mock_crud.delete_featured_content = AsyncMock(return_value=True)
        
        # ===== Act (执行) =====
        result = await service.delete_featured_content(mock_db, content_id, admin_id, admin_role)
        
        # ===== Assert (断言) =====
        assert result["code"] == 200
        assert result["data"]["status"] == "deleted"


@pytest.mark.asyncio
async def test_delete_featured_content_permission_denied(service, mock_db):
    """测试删除焦点图 - 权限不足"""
    # ===== Arrange (准备) =====
    user_id = uuid.uuid4()
    regular_role = "REGULAR"
    content_id = uuid.uuid4()
    
    # ===== Act & Assert (执行和断言) =====
    with pytest.raises(PermissionDeniedException):
        await service.delete_featured_content(mock_db, content_id, user_id, regular_role)


# ==================== 焦点图获取详情（Admin）增量测试 ====================

@pytest.mark.asyncio
async def test_get_featured_content_detail_admin_success(service, mock_db, mock_featured_content):
    """测试获取焦点图详情（管理员）- 成功"""
    # ===== Arrange (准备) =====
    admin_id = uuid.uuid4()
    admin_role = "ADMIN"
    content_id = mock_featured_content.id

    with patch('app.services.homepage_search_service.crud') as mock_crud:
        mock_crud.get_featured_content_by_id = AsyncMock(return_value=mock_featured_content)

        # ===== Act (执行) =====
        result = await service.get_featured_content_detail_admin(
            mock_db, content_id, admin_id, admin_role
        )

        # ===== Assert (断言) =====
        assert result["code"] == 200
        assert result["message"] == "success"
        assert "data" in result
        data = result["data"]
        assert data["title"] == mock_featured_content.title
        assert data["image_url"] == mock_featured_content.image_url
        mock_crud.get_featured_content_by_id.assert_called_once_with(mock_db, content_id)


@pytest.mark.asyncio
async def test_get_featured_content_detail_admin_permission_denied(service, mock_db):
    """测试获取焦点图详情（管理员）- 权限不足"""
    # ===== Arrange (准备) =====
    user_id = uuid.uuid4()
    regular_role = "REGULAR"
    content_id = uuid.uuid4()

    # ===== Act & Assert (执行和断言) =====
    with pytest.raises(PermissionDeniedException):
        await service.get_featured_content_detail_admin(
            mock_db, content_id, user_id, regular_role
        )


@pytest.mark.asyncio
async def test_get_featured_content_detail_admin_not_found(service, mock_db):
    """测试获取焦点图详情（管理员）- 焦点图不存在"""
    # ===== Arrange (准备) =====
    admin_id = uuid.uuid4()
    admin_role = "ADMIN"
    content_id = uuid.uuid4()

    with patch('app.services.homepage_search_service.crud') as mock_crud:
        mock_crud.get_featured_content_by_id = AsyncMock(return_value=None)

        # ===== Act & Assert (执行和断言) =====
        with pytest.raises(NotFoundException):
            await service.get_featured_content_detail_admin(
                mock_db, content_id, admin_id, admin_role
            )


# ==================== Phase2: 业务逻辑辅助方法测试 ====================

def test_select_host_with_expert(service):
    """测试Host选择逻辑 - 有场次专家"""
    # ===== Arrange (准备) =====
    room_data = {
        'expert_id': uuid.uuid4(),
        'expert_name': '李四 教授',
        'expert_title': '主任医师',
        'expert_hospital': 'XX 医院',
        'expert_avatar_url': 'https://example.com/a.jpg',
    }
    
    # ===== Act (执行) =====
    host = service._select_host(room_data)
    
    # ===== Assert (断言) =====
    assert host is not None
    assert host.expert_id == room_data['expert_id']
    assert host.user_id is None
    assert host.name == '李四 教授'
    assert host.title == '主任医师'
    assert host.hospital == 'XX 医院'
    assert host.avatar_url == 'https://example.com/a.jpg'


def test_select_host_without_expert(service):
    """测试Host选择逻辑 - 无场次专家"""
    # ===== Arrange (准备) =====
    room_data = {
        'expert_id': None,
        'expert_name': None,
        'expert_title': None,
        'expert_hospital': None
    }
    
    # ===== Act (执行) =====
    host = service._select_host(room_data)
    
    # ===== Assert (断言) =====
    assert host is None


def test_determine_live_status(service):
    """测试直播状态判断 - 所有状态映射"""
    # 测试所有状态映射
    test_cases = [
        ('live', LiveStatusEnum.LIVE),
        ('ready', LiveStatusEnum.SCHEDULED),
        ('scheduled', LiveStatusEnum.SCHEDULED),
        ('ended', LiveStatusEnum.REPLAY),
        ('archived', LiveStatusEnum.REPLAY),
        (None, LiveStatusEnum.REPLAY),
    ]
    
    for session_status, expected_live_status in test_cases:
        result = service._determine_live_status(session_status)
        assert result == expected_live_status, f"session_status={session_status} 应该映射到 {expected_live_status}"


def test_build_status_data(service):
    """测试状态数据构造 - 3种状态"""
    # ===== 测试LIVE状态 =====
    room_data_live = {
        'peak_viewer_count': 1250,
        'session_start_time': datetime.utcnow(),
        'duration_seconds': 3600,
        'total_play_count': 500
    }
    status_data_live = service._build_status_data(LiveStatusEnum.LIVE, room_data_live)
    assert status_data_live.viewer_count == 1250
    assert status_data_live.start_time is None
    assert status_data_live.duration_seconds is None
    assert status_data_live.play_count is None
    
    # ===== 测试SCHEDULED状态 =====
    room_data_scheduled = {
        'peak_viewer_count': 1250,
        'session_start_time': datetime.utcnow(),
        'duration_seconds': 3600,
        'total_play_count': 500
    }
    status_data_scheduled = service._build_status_data(LiveStatusEnum.SCHEDULED, room_data_scheduled)
    assert status_data_scheduled.viewer_count is None
    assert status_data_scheduled.start_time == room_data_scheduled['session_start_time']
    assert status_data_scheduled.duration_seconds is None
    assert status_data_scheduled.play_count is None
    
    # ===== 测试REPLAY状态 =====
    room_data_replay = {
        'peak_viewer_count': 1250,
        'session_start_time': datetime.utcnow(),
        'duration_seconds': 3600,
        'total_play_count': 500
    }
    status_data_replay = service._build_status_data(LiveStatusEnum.REPLAY, room_data_replay)
    assert status_data_replay.viewer_count is None
    assert status_data_replay.start_time is None
    assert status_data_replay.duration_seconds == 3600
    assert status_data_replay.play_count == 500


def test_calculate_heat(service):
    """测试热度计算公式"""
    # ===== 测试正常计算 =====
    room_data_normal = {
        'peak_viewer_count': 100,
        'total_viewer_count': 500,
        'total_message_count': 50,
        'total_play_count': 200
    }
    heat = service._calculate_heat(room_data_normal)
    # 公式：100*10 + 500*1 + 50*5 + 200*2 = 1000 + 500 + 250 + 400 = 2150
    assert heat == 2150
    
    # ===== 测试所有数据为None =====
    room_data_none = {
        'peak_viewer_count': None,
        'total_viewer_count': None,
        'total_message_count': None,
        'total_play_count': None
    }
    heat_none = service._calculate_heat(room_data_none)
    assert heat_none is None
    
    # ===== 测试部分数据为None（应视为0）=====
    room_data_partial = {
        'peak_viewer_count': 100,
        'total_viewer_count': None,
        'total_message_count': None,
        'total_play_count': None
    }
    heat_partial = service._calculate_heat(room_data_partial)
    # 公式：100*10 + 0*1 + 0*5 + 0*2 = 1000
    assert heat_partial == 1000
