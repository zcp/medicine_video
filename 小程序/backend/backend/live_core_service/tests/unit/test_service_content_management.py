"""
内容管理模块 - Service层测试
测试策略: Academic (学术主义)
- 所有方法: 完整测试(正常+异常+边界+权限)
- Mock CRUD: 隔离测试Service层业务逻辑
"""
import pytest
from uuid import uuid4, UUID
from unittest.mock import AsyncMock, Mock, patch, ANY
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.content_management_service import ContentManagementService
from app.schemas.content_management import (
    TagCreate, TagUpdate, TagItem,
    CategoryCreate, CategoryUpdate, CategoryItem,
    SessionTagsSetRequest,
    LiveRoomCategoriesSetRequest,
    LiveRoomCategoriesListResponse,
)
from app.models.content_management import Tag, Category
from app.exceptions import NotFoundException, PermissionDeniedException, InvalidParameterException
from app.core.exceptions import DatabaseIntegrityException


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def service():
    """创建ContentManagementService实例"""
    return ContentManagementService()


@pytest.fixture
def mock_db_session():
    """创建Mock数据库会话"""
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()
    mock_session.refresh = AsyncMock()
    mock_session.execute = AsyncMock()
    mock_session.add = AsyncMock()
    return mock_session


# ============================================================================
# Tags Service Tests
# ============================================================================

class TestTagsService:
    """标签Service层测试"""
    
    @pytest.mark.asyncio
    async def test_get_tags_list_admin(self, service, mock_db_session):
        """测试管理员获取标签列表"""
        # Arrange
        mock_tag1 = Tag(id=uuid4(), name="标签1", is_active=True, created_at=datetime.now(), updated_at=datetime.now())
        mock_tag2 = Tag(id=uuid4(), name="标签2", is_active=False, created_at=datetime.now(), updated_at=datetime.now())
        
        with patch('app.crud.content_management.get_tags', new_callable=AsyncMock) as mock_get_tags:
            mock_get_tags.return_value = [mock_tag1, mock_tag2]
            
            # Act
            result = await service.get_tags_list(
                mock_db_session,
                current_user_id=uuid4(),
                role='ADMIN'
            )
            
            # Assert
            assert result.code == 200
            assert len(result.data) == 2
            # 管理员且 include_inactive=False 时 service 传 is_active=True
            mock_get_tags.assert_called_once_with(
                mock_db_session, True, ANY, 'ADMIN', q=None, search_type=None
            )
    
    @pytest.mark.asyncio
    async def test_get_tags_list_user(self, service, mock_db_session):
        """测试普通用户获取标签列表(只返回is_active=True)"""
        # Arrange
        mock_tag = Tag(id=uuid4(), name="标签1", is_active=True, created_at=datetime.now(), updated_at=datetime.now())
        
        with patch('app.crud.content_management.get_tags', new_callable=AsyncMock) as mock_get_tags:
            mock_get_tags.return_value = [mock_tag]
            
            # Act
            result = await service.get_tags_list(
                mock_db_session,
                current_user_id=uuid4(),
                role='REGULAR'
            )
            
            # Assert
            assert result.code == 200
            assert len(result.data) == 1
            mock_get_tags.assert_called_once_with(
                mock_db_session, True, ANY, 'REGULAR', q=None, search_type=None
            )
    
    @pytest.mark.asyncio
    async def test_create_tag_success_admin(self, service, mock_db_session):
        """测试管理员创建标签成功"""
        # Arrange
        tag_data = TagCreate(name="新标签", is_active=True)
        mock_tag = Tag(
            id=uuid4(),
            name="新标签",
            is_active=True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        with patch('app.crud.content_management.create_tag', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_tag
            
            # Act
            result = await service.create_tag(
                mock_db_session,
                tag_data,
                current_user_id=uuid4(),
                role='ADMIN'
            )
            
            # Assert
            assert result.name == "新标签"
            mock_create.assert_called_once()
            call_kwargs = mock_create.call_args
            assert call_kwargs.kwargs.get("source") == "admin" or (
                len(call_kwargs.args) >= 1 and call_kwargs.kwargs.get("source", "admin") == "admin"
            )
            # V2：Admin 创建须带 source=admin
            assert mock_create.call_args.kwargs["source"] == "admin"
            assert mock_create.call_args.kwargs["created_by"] is not None
            mock_db_session.commit.assert_called_once()
            mock_db_session.refresh.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_tag_permission_denied_user(self, service, mock_db_session):
        """测试普通用户创建标签失败(权限不足)"""
        # Arrange
        tag_data = TagCreate(name="新标签", is_active=True)
        
        # Act & Assert
        with pytest.raises(PermissionDeniedException, match="需要管理员权限"):
            await service.create_tag(
                mock_db_session,
                tag_data,
                current_user_id=uuid4(),
                role='USER'
            )

    @pytest.mark.asyncio
    async def test_resolve_tag_creates_new(self, service, mock_db_session):
        """resolve：未命中则新建 source=user"""
        from app.schemas.content_management import TagResolveRequest
        owner_id = uuid4()
        tag_id = uuid4()
        mock_tag = Tag(
            id=tag_id,
            name="腹腔镜肝切除",
            is_active=True,
            source="user",
            created_by=owner_id,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        with patch('app.services.content_management_service.check_scene_fields', new_callable=AsyncMock) as mock_safety, \
             patch('app.crud.content_management.get_tag_by_name', new_callable=AsyncMock) as mock_get, \
             patch('app.crud.content_management.create_tag', new_callable=AsyncMock) as mock_create:
            mock_get.return_value = None
            mock_create.return_value = mock_tag
            result = await service.resolve_tag(
                mock_db_session,
                TagResolveRequest(name="腹腔镜肝切除"),
                current_user_id=owner_id,
                role="REGULAR",
            )
            assert result.data.created is True
            assert result.data.id == tag_id
            assert result.data.source == "user"
            mock_safety.assert_called_once()
            mock_create.assert_called_once()
            assert mock_create.call_args.kwargs["source"] == "user"
            assert mock_create.call_args.kwargs["created_by"] == owner_id

    @pytest.mark.asyncio
    async def test_resolve_tag_reuses_existing(self, service, mock_db_session):
        """resolve：命中 active 则复用"""
        from app.schemas.content_management import TagResolveRequest
        tag_id = uuid4()
        mock_tag = Tag(
            id=tag_id,
            name="微创",
            is_active=True,
            source="admin",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        with patch('app.services.content_management_service.check_scene_fields', new_callable=AsyncMock), \
             patch('app.crud.content_management.get_tag_by_name', new_callable=AsyncMock) as mock_get, \
             patch('app.crud.content_management.create_tag', new_callable=AsyncMock) as mock_create:
            mock_get.return_value = mock_tag
            result = await service.resolve_tag(
                mock_db_session,
                TagResolveRequest(name="微创"),
                current_user_id=uuid4(),
                role="REGULAR",
            )
            assert result.data.created is False
            assert result.data.id == tag_id
            mock_create.assert_not_called()

    @pytest.mark.asyncio
    async def test_resolve_tag_inactive_raises(self, service, mock_db_session):
        """resolve：软删同名不复活"""
        from app.schemas.content_management import TagResolveRequest
        mock_tag = Tag(
            id=uuid4(),
            name="已停用",
            is_active=False,
            source="admin",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        with patch('app.services.content_management_service.check_scene_fields', new_callable=AsyncMock), \
             patch('app.crud.content_management.get_tag_by_name', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_tag
            with pytest.raises(InvalidParameterException, match="标签不可用"):
                await service.resolve_tag(
                    mock_db_session,
                    TagResolveRequest(name="已停用"),
                    current_user_id=uuid4(),
                    role="REGULAR",
                )

    @pytest.mark.asyncio
    async def test_resolve_tag_content_safety_blocked(self, service, mock_db_session):
        """resolve：内容安全拦截则不查库不创建"""
        from app.schemas.content_management import TagResolveRequest
        from app.content_safety.exceptions import ContentSafetyBlockedException
        with patch(
            'app.services.content_management_service.check_scene_fields',
            new_callable=AsyncMock,
            side_effect=ContentSafetyBlockedException("内容不合规", code=4221),
        ), patch('app.crud.content_management.get_tag_by_name', new_callable=AsyncMock) as mock_get, \
             patch('app.crud.content_management.create_tag', new_callable=AsyncMock) as mock_create:
            with pytest.raises(ContentSafetyBlockedException):
                await service.resolve_tag(
                    mock_db_session,
                    TagResolveRequest(name="违规词"),
                    current_user_id=uuid4(),
                    role="REGULAR",
                )
            mock_get.assert_not_called()
            mock_create.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_create_tag_duplicate_name(self, service, mock_db_session):
        """测试创建重名标签失败"""
        # Arrange
        tag_data = TagCreate(name="重复标签", is_active=True)
        
        with patch('app.crud.content_management.create_tag', new_callable=AsyncMock) as mock_create:
            mock_create.side_effect = DatabaseIntegrityException("标签名称已存在")
            
            # Act & Assert
            with pytest.raises(DatabaseIntegrityException, match="标签名称已存在"):
                await service.create_tag(
                    mock_db_session,
                    tag_data,
                    current_user_id=uuid4(),
                    role='ADMIN'
                )
            
            mock_db_session.rollback.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_tag_success(self, service, mock_db_session):
        """测试更新标签成功"""
        # Arrange
        tag_id = uuid4()
        tag_data = TagUpdate(name="更新后名称")
        mock_tag = Tag(
            id=tag_id,
            name="更新后名称",
            is_active=True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        with patch('app.crud.content_management.update_tag', new_callable=AsyncMock) as mock_update:
            mock_update.return_value = mock_tag
            
            # Act
            result = await service.update_tag(
                mock_db_session,
                tag_id,
                tag_data,
                current_user_id=uuid4(),
                role='ADMIN'
            )
            
            # Assert
            assert result.name == "更新后名称"
            mock_db_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_tag_not_found(self, service, mock_db_session):
        """测试更新不存在的标签返回404"""
        # Arrange
        tag_id = uuid4()
        tag_data = TagUpdate(name="更新后名称")
        
        with patch('app.crud.content_management.update_tag', new_callable=AsyncMock) as mock_update:
            mock_update.return_value = None
            
            # Act & Assert
            with pytest.raises(NotFoundException, match="标签不存在"):
                await service.update_tag(
                    mock_db_session,
                    tag_id,
                    tag_data,
                    current_user_id=uuid4(),
                    role='ADMIN'
                )
    
    @pytest.mark.asyncio
    async def test_delete_tag_success(self, service, mock_db_session):
        """测试删除标签成功"""
        # Arrange
        tag_id = uuid4()
        
        with patch('app.crud.content_management.delete_tag', new_callable=AsyncMock) as mock_delete:
            mock_delete.return_value = True
            
            # Act
            result = await service.delete_tag(
                mock_db_session,
                tag_id,
                current_user_id=uuid4(),
                role='ADMIN'
            )
            
            # Assert
            assert result == {"message": "删除成功"}
            mock_db_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_tag_permission_denied(self, service, mock_db_session):
        """测试普通用户删除标签失败(权限不足)"""
        # Arrange
        tag_id = uuid4()
        
        # Act & Assert
        with pytest.raises(PermissionDeniedException, match="需要管理员权限"):
            await service.delete_tag(
                mock_db_session,
                tag_id,
                current_user_id=uuid4(),
                role='USER'
            )


# ============================================================================
# Categories Service Tests
# ============================================================================

class TestCategoriesService:
    """分类Service层测试"""
    
    @pytest.mark.asyncio
    async def test_get_categories_list_public(self, service, mock_db_session):
        """测试公开获取分类列表(只返回is_active=True)"""
        # Arrange
        mock_cat = Category(
            id=uuid4(),
            name="分类1",
            sort_order=1,
            is_active=True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        with patch('app.crud.content_management.get_categories', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = [mock_cat]
            
            # Act
            result = await service.get_categories_list(
                mock_db_session,
                current_user_id=None,
                role=None
            )
            
            # Assert
            assert result.code == 200
            assert len(result.data) == 1
    
    @pytest.mark.asyncio
    async def test_get_categories_paginated_admin(self, service, mock_db_session):
        """测试管理员分页获取分类列表"""
        # Arrange
        mock_cat = Category(
            id=uuid4(),
            name="分类1",
            sort_order=1,
            is_active=True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        with patch('app.crud.content_management.get_categories_paginated', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = ([mock_cat], 1)
            
            # Act
            result = await service.get_categories_paginated(
                mock_db_session,
                page=1,
                size=10,
                is_active=None,
                current_user_id=uuid4(),
                role='ADMIN'
            )
            
            # Assert
            assert result.code == 200
            assert result.data.total == 1
            assert result.data.page == 1
            assert result.data.size == 10
    
    @pytest.mark.asyncio
    async def test_get_categories_paginated_permission_denied(self, service, mock_db_session):
        """测试普通用户访问管理员分页接口失败"""
        # Act & Assert
        with pytest.raises(PermissionDeniedException, match="需要管理员权限"):
            await service.get_categories_paginated(
                mock_db_session,
                page=1,
                size=10,
                is_active=None,
                current_user_id=uuid4(),
                role='USER'
            )
    
    @pytest.mark.asyncio
    async def test_create_category_success(self, service, mock_db_session):
        """测试创建分类成功"""
        # Arrange
        category_data = CategoryCreate(name="新分类", sort_order=1, is_active=True)
        mock_cat = Category(
            id=uuid4(),
            name="新分类",
            sort_order=1,
            is_active=True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        with patch('app.crud.content_management.create_category', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_cat
            
            # Act
            result = await service.create_category(
                mock_db_session,
                category_data,
                current_user_id=uuid4(),
                role='ADMIN'
            )
            
            # Assert
            assert result.name == "新分类"
            mock_db_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_category_by_id_success(self, service, mock_db_session):
        """测试根据ID获取分类成功"""
        # Arrange
        category_id = uuid4()
        mock_cat = Category(
            id=category_id,
            name="分类1",
            sort_order=1,
            is_active=True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        with patch('app.crud.content_management.get_category_by_id', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_cat
            
            # Act
            result = await service.get_category_by_id(
                mock_db_session,
                category_id,
                current_user_id=None,
                role=None
            )
            
            # Assert
            assert result.id == category_id
            assert result.name == "分类1"
    
    @pytest.mark.asyncio
    async def test_get_category_by_id_not_found(self, service, mock_db_session):
        """测试获取不存在的分类返回404"""
        # Arrange
        category_id = uuid4()
        
        with patch('app.crud.content_management.get_category_by_id', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = None
            
            # Act & Assert
            with pytest.raises(NotFoundException, match="分类不存在"):
                await service.get_category_by_id(
                    mock_db_session,
                    category_id,
                    current_user_id=None,
                    role=None
                )
    
    @pytest.mark.asyncio
    async def test_get_category_by_id_inactive_non_admin_returns_404(self, service, mock_db_session):
        """测试非管理员访问禁用分类返回404(404伪装)"""
        # Arrange
        category_id = uuid4()
        mock_cat = Category(
            id=category_id,
            name="禁用分类",
            sort_order=1,
            is_active=False,  # 禁用状态
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        with patch('app.crud.content_management.get_category_by_id', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_cat
            
            # Act & Assert
            with pytest.raises(NotFoundException, match="分类不存在"):
                await service.get_category_by_id(
                    mock_db_session,
                    category_id,
                    current_user_id=None,
                    role='USER'
                )


# ============================================================================
# Session_Tags Service Tests
# ============================================================================

class TestSessionTagsService:
    """场次标签Service层测试"""
    
    @pytest.mark.asyncio
    async def test_set_session_tags_success(self, service, mock_db_session):
        """测试设置场次标签成功（房主）"""
        # Arrange
        session_id = uuid4()
        owner_id = uuid4()
        room_id = uuid4()
        tag1_id = uuid4()
        tag2_id = uuid4()
        request_data = SessionTagsSetRequest(
            tag_ids=[tag1_id, tag2_id],
            mode="replace"
        )
        
        mock_tag1 = Tag(id=tag1_id, name="标签1", is_active=True, created_at=datetime.now(), updated_at=datetime.now())
        mock_tag2 = Tag(id=tag2_id, name="标签2", is_active=True, created_at=datetime.now(), updated_at=datetime.now())

        mock_session = Mock()
        mock_session.room_id = room_id
        mock_room = Mock()
        mock_room.user_id = owner_id

        # Mock execute for tag existence check
        from unittest.mock import Mock as UMock
        mock_scalars = UMock()
        mock_scalars.all.return_value = [mock_tag1, mock_tag2]
        mock_result = UMock()
        mock_result.scalars.return_value = mock_scalars
        mock_db_session.execute.return_value = mock_result
        
        with patch('app.crud.session.get', new_callable=AsyncMock) as mock_get_session, \
             patch('app.crud.room.get', new_callable=AsyncMock) as mock_get_room, \
             patch('app.crud.content_management.set_session_tags', new_callable=AsyncMock) as mock_set:
            mock_get_session.return_value = mock_session
            mock_get_room.return_value = mock_room
            mock_set.return_value = [mock_tag1, mock_tag2]
            
            # Act
            result = await service.set_session_tags(
                mock_db_session,
                session_id,
                request_data,
                current_user_id=owner_id,
                role='REGULAR'
            )
            
            # Assert
            assert result.code == 200
            assert result.data['mode'] == "replace"
            assert len(result.data['tags']) == 2
            mock_db_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_set_session_tags_invalid_tag_ids(self, service, mock_db_session):
        """测试设置场次标签时部分tag_id不存在"""
        # Arrange
        session_id = uuid4()
        owner_id = uuid4()
        room_id = uuid4()
        tag1_id = uuid4()
        tag2_id = uuid4()
        request_data = SessionTagsSetRequest(
            tag_ids=[tag1_id, tag2_id],
            mode="replace"
        )

        mock_tag1 = Tag(id=tag1_id, name="标签1", is_active=True, created_at=datetime.now(), updated_at=datetime.now())
        mock_session = Mock()
        mock_session.room_id = room_id
        mock_room = Mock()
        mock_room.user_id = owner_id

        from unittest.mock import Mock as UMock
        mock_scalars = UMock()
        mock_scalars.all.return_value = [mock_tag1]
        mock_result = UMock()
        mock_result.scalars.return_value = mock_scalars
        mock_db_session.execute.return_value = mock_result

        with patch('app.crud.session.get', new_callable=AsyncMock) as mock_get_session, \
             patch('app.crud.room.get', new_callable=AsyncMock) as mock_get_room:
            mock_get_session.return_value = mock_session
            mock_get_room.return_value = mock_room

            # Act & Assert
            with pytest.raises(InvalidParameterException, match="部分标签ID不存在"):
                await service.set_session_tags(
                    mock_db_session,
                    session_id,
                    request_data,
                    current_user_id=owner_id,
                    role='REGULAR'
                )

    @pytest.mark.asyncio
    async def test_set_session_tags_inactive_rejected(self, service, mock_db_session):
        """绑定场次标签时拒绝 is_active=false"""
        session_id = uuid4()
        owner_id = uuid4()
        room_id = uuid4()
        tag1_id = uuid4()
        tag2_id = uuid4()
        request_data = SessionTagsSetRequest(
            tag_ids=[tag1_id, tag2_id],
            mode="replace"
        )

        mock_tag1 = Tag(id=tag1_id, name="标签1", is_active=True, created_at=datetime.now(), updated_at=datetime.now())
        mock_tag2 = Tag(id=tag2_id, name="标签2", is_active=False, created_at=datetime.now(), updated_at=datetime.now())
        mock_session = Mock()
        mock_session.room_id = room_id
        mock_room = Mock()
        mock_room.user_id = owner_id

        from unittest.mock import Mock as UMock
        mock_scalars = UMock()
        mock_scalars.all.return_value = [mock_tag1, mock_tag2]
        mock_result = UMock()
        mock_result.scalars.return_value = mock_scalars
        mock_db_session.execute.return_value = mock_result

        with patch('app.crud.session.get', new_callable=AsyncMock) as mock_get_session, \
             patch('app.crud.room.get', new_callable=AsyncMock) as mock_get_room:
            mock_get_session.return_value = mock_session
            mock_get_room.return_value = mock_room

            with pytest.raises(InvalidParameterException, match="部分标签不可用"):
                await service.set_session_tags(
                    mock_db_session,
                    session_id,
                    request_data,
                    current_user_id=owner_id,
                    role='REGULAR'
                )
    
    @pytest.mark.asyncio
    async def test_set_session_tags_permission_denied(self, service, mock_db_session):
        """测试非房主设置场次标签失败"""
        # Arrange
        session_id = uuid4()
        room_id = uuid4()
        request_data = SessionTagsSetRequest(
            tag_ids=[uuid4()],
            mode="replace"
        )
        mock_session = Mock()
        mock_session.room_id = room_id
        mock_room = Mock()
        mock_room.user_id = uuid4()  # 他人房间

        with patch('app.crud.session.get', new_callable=AsyncMock) as mock_get_session, \
             patch('app.crud.room.get', new_callable=AsyncMock) as mock_get_room:
            mock_get_session.return_value = mock_session
            mock_get_room.return_value = mock_room

            # Act & Assert
            with pytest.raises(PermissionDeniedException, match="需要管理员权限或房间所有者权限"):
                await service.set_session_tags(
                    mock_db_session,
                    session_id,
                    request_data,
                    current_user_id=uuid4(),
                    role='REGULAR'
                )

    @pytest.mark.asyncio
    async def test_set_session_tags_admin_bypass(self, service, mock_db_session):
        """测试 Admin 可旁路房主权设置场次标签"""
        session_id = uuid4()
        room_id = uuid4()
        tag_id = uuid4()
        request_data = SessionTagsSetRequest(tag_ids=[tag_id], mode="replace")
        mock_tag = Tag(id=tag_id, name="标签1", is_active=True, created_at=datetime.now(), updated_at=datetime.now())
        mock_session = Mock()
        mock_session.room_id = room_id
        mock_room = Mock()
        mock_room.user_id = uuid4()

        from unittest.mock import Mock as UMock
        mock_scalars = UMock()
        mock_scalars.all.return_value = [mock_tag]
        mock_result = UMock()
        mock_result.scalars.return_value = mock_scalars
        mock_db_session.execute.return_value = mock_result

        with patch('app.crud.session.get', new_callable=AsyncMock) as mock_get_session, \
             patch('app.crud.room.get', new_callable=AsyncMock) as mock_get_room, \
             patch('app.crud.content_management.set_session_tags', new_callable=AsyncMock) as mock_set:
            mock_get_session.return_value = mock_session
            mock_get_room.return_value = mock_room
            mock_set.return_value = [mock_tag]

            result = await service.set_session_tags(
                mock_db_session,
                session_id,
                request_data,
                current_user_id=uuid4(),
                role='ADMIN'
            )
            assert result.code == 200

    @pytest.mark.asyncio
    async def test_set_session_tags_clear_empty(self, service, mock_db_session):
        """测试 replace 空列表清空场次标签"""
        session_id = uuid4()
        owner_id = uuid4()
        room_id = uuid4()
        request_data = SessionTagsSetRequest(tag_ids=[], mode="replace")
        mock_session = Mock()
        mock_session.room_id = room_id
        mock_room = Mock()
        mock_room.user_id = owner_id

        with patch('app.crud.session.get', new_callable=AsyncMock) as mock_get_session, \
             patch('app.crud.room.get', new_callable=AsyncMock) as mock_get_room, \
             patch('app.crud.content_management.set_session_tags', new_callable=AsyncMock) as mock_set:
            mock_get_session.return_value = mock_session
            mock_get_room.return_value = mock_room
            mock_set.return_value = []

            result = await service.set_session_tags(
                mock_db_session,
                session_id,
                request_data,
                current_user_id=owner_id,
                role='REGULAR'
            )
            assert result.code == 200
            assert result.data['tags'] == []
            mock_set.assert_called_once_with(mock_db_session, session_id, [], "replace")
    
    @pytest.mark.asyncio
    async def test_get_session_tags(self, service, mock_db_session):
        """测试获取场次标签列表"""
        # Arrange
        session_id = uuid4()
        mock_tag = Tag(id=uuid4(), name="标签1", is_active=True, created_at=datetime.now(), updated_at=datetime.now())
        
        with patch('app.crud.content_management.get_tags_by_session_id', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = [mock_tag]
            
            # Act
            result = await service.get_session_tags(
                mock_db_session,
                session_id,
                current_user_id=None,
                role=None
            )
            
            # Assert
            assert result.code == 200
            assert len(result.data) == 1
    
    @pytest.mark.asyncio
    async def test_remove_session_tag_success(self, service, mock_db_session):
        """测试删除场次标签关联成功（房主）"""
        # Arrange
        session_id = uuid4()
        tag_id = uuid4()
        owner_id = uuid4()
        room_id = uuid4()
        mock_session = Mock()
        mock_session.room_id = room_id
        mock_room = Mock()
        mock_room.user_id = owner_id
        
        with patch('app.crud.session.get', new_callable=AsyncMock) as mock_get_session, \
             patch('app.crud.room.get', new_callable=AsyncMock) as mock_get_room, \
             patch('app.crud.content_management.remove_session_tag', new_callable=AsyncMock) as mock_remove:
            mock_get_session.return_value = mock_session
            mock_get_room.return_value = mock_room
            mock_remove.return_value = True
            
            # Act
            result = await service.remove_session_tag(
                mock_db_session,
                session_id,
                tag_id,
                current_user_id=owner_id,
                role='REGULAR'
            )
            
            # Assert
            assert result == {"message": "删除成功"}
            mock_db_session.commit.assert_called_once()


# ============================================================================
# Permission Guard Tests
# ============================================================================

class TestPermissionGuards:
    """权限守卫函数测试"""
    
    def test_check_admin_permission_admin(self, service):
        """测试管理员权限检查通过"""
        # Act & Assert (不应抛出异常)
        service._check_admin_permission('ADMIN')
        service._check_admin_permission('SUPERADMIN')
    
    def test_check_admin_permission_user(self, service):
        """测试普通用户权限检查失败"""
        # Act & Assert
        with pytest.raises(PermissionDeniedException, match="需要管理员权限"):
            service._check_admin_permission('REGULAR')
    
    def test_check_write_permission_user(self, service):
        """测试写权限检查通过"""
        # Act & Assert (不应抛出异常)
        service._check_write_permission('REGULAR')
        service._check_write_permission('ADMIN')
        service._check_write_permission('SUPERADMIN')
    
    def test_check_write_permission_guest(self, service):
        """测试游客写权限检查失败"""
        # Act & Assert
        with pytest.raises(PermissionDeniedException, match="需要登录后才能执行此操作"):
            service._check_write_permission('guest')
    
    def test_check_tag_visibility_active_tag(self, service):
        """测试活跃标签可见性检查通过"""
        # Arrange
        tag = Tag(id=uuid4(), name="活跃标签", is_active=True)
        
        # Act & Assert (不应抛出异常)
        service._check_tag_visibility(tag, None, 'USER')
    
    def test_check_tag_visibility_inactive_tag_non_admin(self, service):
        """测试非管理员访问禁用标签失败(404伪装)"""
        # Arrange
        tag = Tag(id=uuid4(), name="禁用标签", is_active=False)
        
        # Act & Assert
        with pytest.raises(NotFoundException, match="标签不存在"):
            service._check_tag_visibility(tag, None, 'USER')
    
    def test_check_tag_visibility_inactive_tag_admin(self, service):
        """测试管理员访问禁用标签通过"""
        # Arrange
        tag = Tag(id=uuid4(), name="禁用标签", is_active=False)
        
        # Act & Assert (不应抛出异常)
        service._check_tag_visibility(tag, uuid4(), 'ADMIN')


# ============================================================================
# Room_Categories Service Tests (增量)
# ============================================================================

class TestLiveRoomCategoriesService:
    """直播间-分类 Service 层测试（增量）"""

    @pytest.mark.asyncio
    async def test_get_live_room_categories_list_success(self, service, mock_db_session):
        """测试获取直播间分类列表成功"""
        room_id = uuid4()
        mock_room = type('Room', (), {'id': room_id})()
        mock_cat1 = Category(id=uuid4(), name="分类1", sort_order=0, is_active=True, created_at=datetime.now(), updated_at=datetime.now())
        mock_cat2 = Category(id=uuid4(), name="分类2", sort_order=1, is_active=True, created_at=datetime.now(), updated_at=datetime.now())

        with patch('app.crud.room.get', new_callable=AsyncMock) as mock_room_get:
            with patch('app.crud.content_management.get_categories_by_room_id', new_callable=AsyncMock) as mock_get_cats:
                mock_room_get.return_value = mock_room
                mock_get_cats.return_value = [mock_cat1, mock_cat2]

                result = await service.get_live_room_categories_list(
                    mock_db_session, room_id, current_user_id=None, role=None
                )

                assert isinstance(result, LiveRoomCategoriesListResponse)
                assert result.code == 200
                assert len(result.data) == 2
                mock_room_get.assert_called_once_with(mock_db_session, room_id)
                mock_get_cats.assert_called_once_with(mock_db_session, room_id)

    @pytest.mark.asyncio
    async def test_get_live_room_categories_list_room_not_found(self, service, mock_db_session):
        """测试房间不存在时抛出 NotFoundException"""
        room_id = uuid4()
        with patch('app.crud.room.get', new_callable=AsyncMock) as mock_room_get:
            mock_room_get.return_value = None

            with pytest.raises(NotFoundException, match="直播间不存在"):
                await service.get_live_room_categories_list(
                    mock_db_session, room_id, current_user_id=None, role=None
                )

    @pytest.mark.asyncio
    async def test_set_live_room_categories_as_admin_success(self, service, mock_db_session):
        """测试管理员设置直播间分类成功"""
        room_id = uuid4()
        cat_id1 = uuid4()
        cat_id2 = uuid4()
        mock_room = type('Room', (), {'id': room_id})()
        mock_cats = [
            Category(id=cat_id1, name="c1", sort_order=0, is_active=True, created_at=datetime.now(), updated_at=datetime.now()),
            Category(id=cat_id2, name="c2", sort_order=1, is_active=True, created_at=datetime.now(), updated_at=datetime.now()),
        ]
        body = LiveRoomCategoriesSetRequest(category_ids=[cat_id1, cat_id2], mode="replace")

        mock_scalars_result = Mock()
        mock_scalars_result.all.return_value = [Mock(id=cat_id1, is_active=True), Mock(id=cat_id2, is_active=True)]
        mock_result = Mock()
        mock_result.scalars.return_value = mock_scalars_result
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        with patch('app.crud.room.get', new_callable=AsyncMock) as mock_room_get:
            with patch('app.crud.content_management.set_live_room_categories', new_callable=AsyncMock) as mock_set:
                mock_room_get.return_value = mock_room
                mock_set.return_value = mock_cats

                result = await service.set_live_room_categories(
                    mock_db_session, room_id, body, current_user_id=uuid4(), role="ADMIN"
                )

                assert result.code == 200
                assert result.data["room_id"] == str(room_id)
                assert result.data["mode"] == "replace"
                assert len(result.data["categories"]) == 2
                mock_room_get.assert_called_once_with(mock_db_session, room_id)
                mock_set.assert_called_once_with(mock_db_session, room_id, [cat_id1, cat_id2], "replace")

    @pytest.mark.asyncio
    async def test_set_live_room_categories_permission_denied(self, service, mock_db_session):
        """测试非管理员设置直播间分类权限不足"""
        room_id = uuid4()
        body = LiveRoomCategoriesSetRequest(category_ids=[uuid4()], mode="replace")

        with pytest.raises(PermissionDeniedException, match="需要管理员权限"):
            await service.set_live_room_categories(
                mock_db_session, room_id, body, current_user_id=uuid4(), role="REGULAR"
            )

    @pytest.mark.asyncio
    async def test_set_live_room_categories_room_not_found(self, service, mock_db_session):
        """测试房间不存在时抛出 NotFoundException"""
        room_id = uuid4()
        body = LiveRoomCategoriesSetRequest(category_ids=[uuid4()], mode="replace")

        with patch('app.crud.room.get', new_callable=AsyncMock) as mock_room_get:
            mock_room_get.return_value = None

            with pytest.raises(NotFoundException, match="直播间不存在"):
                await service.set_live_room_categories(
                    mock_db_session, room_id, body, current_user_id=uuid4(), role="ADMIN"
                )

    @pytest.mark.asyncio
    async def test_set_live_room_categories_invalid_category_ids(self, service, mock_db_session):
        """测试部分分类ID不存在或未启用时抛出 InvalidParameterException"""
        room_id = uuid4()
        cat_id = uuid4()
        body = LiveRoomCategoriesSetRequest(category_ids=[cat_id], mode="replace")
        mock_room = type('Room', (), {'id': room_id})()

        mock_scalars_result = Mock()
        mock_scalars_result.all.return_value = []
        mock_result = Mock()
        mock_result.scalars.return_value = mock_scalars_result
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        with patch('app.crud.room.get', new_callable=AsyncMock) as mock_room_get:
            mock_room_get.return_value = mock_room

            with pytest.raises(InvalidParameterException, match="部分分类ID不存在或未启用"):
                await service.set_live_room_categories(
                    mock_db_session, room_id, body, current_user_id=uuid4(), role="ADMIN"
                )

    @pytest.mark.asyncio
    async def test_delete_live_room_category_as_admin_success(self, service, mock_db_session):
        """测试管理员删除直播间分类关联成功"""
        room_id = uuid4()
        category_id = uuid4()

        with patch('app.crud.content_management.delete_live_room_category', new_callable=AsyncMock) as mock_del:
            mock_del.return_value = True

            result = await service.delete_live_room_category(
                mock_db_session, room_id, category_id, current_user_id=uuid4(), role="ADMIN"
            )

            assert result == {"message": "删除成功"}
            mock_del.assert_called_once_with(mock_db_session, room_id, category_id)
            mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_live_room_category_not_found(self, service, mock_db_session):
        """测试关联不存在时抛出 NotFoundException"""
        room_id = uuid4()
        category_id = uuid4()

        with patch('app.crud.content_management.delete_live_room_category', new_callable=AsyncMock) as mock_del:
            mock_del.return_value = False

            with pytest.raises(NotFoundException, match="该直播间未关联此分类"):
                await service.delete_live_room_category(
                    mock_db_session, room_id, category_id, current_user_id=uuid4(), role="ADMIN"
                )

    @pytest.mark.asyncio
    async def test_delete_live_room_category_permission_denied(self, service, mock_db_session):
        """测试非管理员删除直播间分类权限不足"""
        room_id = uuid4()
        category_id = uuid4()

        with pytest.raises(PermissionDeniedException, match="需要管理员权限"):
            await service.delete_live_room_category(
                mock_db_session, room_id, category_id, current_user_id=uuid4(), role="REGULAR"
            )


# ============================================================================
# Categories / Tags 列表搜索（q / search_type）增量 Service 测试
# ============================================================================

@pytest.mark.asyncio
async def test_get_categories_paginated_passes_q_and_search_type_to_crud(service, mock_db_session):
    """get_categories_paginated 将 q、search_type 下传 CRUD"""
    with patch('app.crud.content_management.get_categories_paginated', new_callable=AsyncMock) as mock_crud:
        mock_crud.return_value = ([], 0)
        await service.get_categories_paginated(
            mock_db_session, page=1, size=10, is_active=None,
            current_user_id=uuid4(), role="ADMIN", q="x", search_type="id"
        )
        mock_crud.assert_called_once()
        call_kw = mock_crud.call_args[1]
        assert call_kw.get("q") == "x"
        assert call_kw.get("search_type") == "id"


@pytest.mark.asyncio
async def test_get_tags_list_passes_q_and_search_type_to_crud(service, mock_db_session):
    """get_tags_list 将 q、search_type 下传 CRUD"""
    with patch('app.crud.content_management.get_tags', new_callable=AsyncMock) as mock_get_tags:
        mock_get_tags.return_value = []
        await service.get_tags_list(
            mock_db_session, current_user_id=uuid4(), role="ADMIN", q="y", search_type="keyword"
        )
        mock_get_tags.assert_called_once()
        call_kw = mock_get_tags.call_args[1]
        assert call_kw.get("q") == "y"
        assert call_kw.get("search_type") == "keyword"


# ============================================================================
# Categories 科室图片能力 - Service 增量测试
# ============================================================================

@pytest.mark.asyncio
async def test_upload_category_icon_as_admin_success(service, mock_db_session):
    """Admin 上传科室图标成功：Mock get_category_by_id、save_category_icon、update_category，返回 CategoryItem"""
    category_id = uuid4()
    mock_category = Category(
        id=category_id,
        name="测试科室",
        icon=None,
        sort_order=0,
        is_active=True,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    saved_url = "/media/categories/xxx/icon_1.jpg"
    updated_category = Category(
        id=category_id,
        name="测试科室",
        icon=saved_url,
        sort_order=0,
        is_active=True,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    mock_file = Mock()
    mock_file.filename = "icon.jpg"

    with patch('app.crud.content_management.get_category_by_id', new_callable=AsyncMock) as mock_get:
        with patch('app.core.file_handler.FileHandler.save_category_icon', new_callable=AsyncMock) as mock_save:
            with patch('app.crud.content_management.update_category', new_callable=AsyncMock) as mock_update:
                mock_get.return_value = mock_category
                mock_save.return_value = saved_url
                mock_update.return_value = updated_category

                result = await service.upload_category_icon(
                    mock_db_session, category_id, mock_file,
                    current_user_id=uuid4(), role="ADMIN"
                )

                assert isinstance(result, CategoryItem)
                assert result.icon == saved_url
                mock_save.assert_called_once()
                mock_get.assert_called_once_with(mock_db_session, category_id)
                mock_update.assert_called_once()
                call_args = mock_update.call_args
                assert call_args[0][2].icon == saved_url


@pytest.mark.asyncio
async def test_upload_category_icon_category_not_found(service, mock_db_session):
    """分类不存在时上传科室图标抛出 NotFoundException"""
    category_id = uuid4()
    mock_file = Mock()

    with patch('app.crud.content_management.get_category_by_id', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = None

        with pytest.raises(NotFoundException, match="分类不存在"):
            await service.upload_category_icon(
                mock_db_session, category_id, mock_file,
                current_user_id=uuid4(), role="ADMIN"
            )
        mock_get.assert_called_once_with(mock_db_session, category_id)


@pytest.mark.asyncio
async def test_upload_category_icon_permission_denied(service, mock_db_session):
    """普通用户上传科室图标抛出 PermissionDeniedException"""
    category_id = uuid4()
    mock_file = Mock()

    with pytest.raises(PermissionDeniedException, match="需要管理员权限"):
        await service.upload_category_icon(
            mock_db_session, category_id, mock_file,
            current_user_id=uuid4(), role="REGULAR"
        )


@pytest.mark.asyncio
async def test_delete_category_icon_as_admin_success(service, mock_db_session):
    """Admin 删除科室图标成功：Mock get_category_by_id、delete_old_category_icon、update_category"""
    category_id = uuid4()
    old_icon = "/media/categories/xxx/icon_1.jpg"
    mock_category = Category(
        id=category_id,
        name="测试科室",
        icon=old_icon,
        sort_order=0,
        is_active=True,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    with patch('app.crud.content_management.get_category_by_id', new_callable=AsyncMock) as mock_get:
        with patch('app.core.file_handler.FileHandler.delete_old_category_icon', new_callable=Mock) as mock_del:
            with patch('app.crud.content_management.update_category', new_callable=AsyncMock) as mock_update:
                mock_get.return_value = mock_category
                mock_update.return_value = mock_category

                result = await service.delete_category_icon(
                    mock_db_session, category_id,
                    current_user_id=uuid4(), role="ADMIN"
                )

                assert result == {"message": "删除成功"}
                mock_del.assert_called_once_with(old_icon)
                mock_update.assert_called_once()
                call_args = mock_update.call_args
                assert call_args[0][2].icon is None


@pytest.mark.asyncio
async def test_delete_category_icon_category_not_found(service, mock_db_session):
    """分类不存在时删除科室图标抛出 NotFoundException"""
    category_id = uuid4()

    with patch('app.crud.content_management.get_category_by_id', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = None

        with pytest.raises(NotFoundException, match="分类不存在"):
            await service.delete_category_icon(
                mock_db_session, category_id,
                current_user_id=uuid4(), role="ADMIN"
            )
        mock_get.assert_called_once_with(mock_db_session, category_id)


@pytest.mark.asyncio
async def test_delete_category_icon_permission_denied(service, mock_db_session):
    """普通用户删除科室图标抛出 PermissionDeniedException"""
    category_id = uuid4()

    with pytest.raises(PermissionDeniedException, match="需要管理员权限"):
        await service.delete_category_icon(
            mock_db_session, category_id,
            current_user_id=uuid4(), role="REGULAR"
        )


@pytest.mark.asyncio
async def test_delete_category_icon_no_icon_idempotent(service, mock_db_session):
    """无图标时删除仍成功（幂等）"""
    category_id = uuid4()
    mock_category = Category(
        id=category_id,
        name="测试科室",
        icon=None,
        sort_order=0,
        is_active=True,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    with patch('app.crud.content_management.get_category_by_id', new_callable=AsyncMock) as mock_get:
        with patch('app.crud.content_management.update_category', new_callable=AsyncMock) as mock_update:
            mock_get.return_value = mock_category
            mock_update.return_value = mock_category

            result = await service.delete_category_icon(
                mock_db_session, category_id,
                current_user_id=uuid4(), role="ADMIN"
            )

            assert result == {"message": "删除成功"}
            mock_update.assert_called_once_with(mock_db_session, category_id, ANY)
            assert mock_update.call_args[0][2].icon is None

