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
    TagResolveRequest, TagResolveData, TagResolveResponse,
    LiveRoomCategoriesSetRequest,
    LiveRoomCategoriesListResponse,
)
from app.models.content_management import Tag, Category
from app.exceptions import NotFoundException, PermissionDeniedException, InvalidParameterException
from app.core.exceptions import DatabaseIntegrityException
from app.core.permissions import check_admin_permission
from types import SimpleNamespace

from app.content_safety.exceptions import ContentSafetyBlockedException


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
            is_active=True, standard=True,
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
            is_active=True, standard=True,
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
        """测试创建分类成功（名录外名称需 standard=false，阶段6B）"""
        # Arrange
        category_data = CategoryCreate(name="新分类", sort_order=1, is_active=True, standard=False)
        mock_cat = Category(
            id=uuid4(),
            name="新分类",
            sort_order=1,
            is_active=True, standard=False,
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
            is_active=True, standard=True,
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
    """场次标签Service层测试（V2：写权限=房主或 Admin；tag_ids 0~5；append ≤5）"""

    @pytest.mark.asyncio
    async def test_set_session_tags_success(self, service, mock_db_session):
        """测试房主设置场次标签成功"""
        # Arrange
        session_id = uuid4()
        room_id = uuid4()
        owner_id = uuid4()
        tag1_id = uuid4()
        tag2_id = uuid4()
        request_data = SessionTagsSetRequest(
            tag_ids=[tag1_id, tag2_id],
            mode="replace"
        )

        mock_tag1 = Tag(id=tag1_id, name="标签1", is_active=True, created_at=datetime.now(), updated_at=datetime.now())
        mock_tag2 = Tag(id=tag2_id, name="标签2", is_active=True, created_at=datetime.now(), updated_at=datetime.now())

        mock_scalars = Mock()
        mock_scalars.all.return_value = [mock_tag1, mock_tag2]
        mock_result = Mock()
        mock_result.scalars.return_value = mock_scalars
        mock_db_session.execute.return_value = mock_result

        with patch('app.services.content_management_service.crud_session.get', new_callable=AsyncMock) as mock_sget, \
             patch('app.services.content_management_service.crud_room.get', new_callable=AsyncMock) as mock_rget, \
             patch('app.crud.content_management.set_session_tags', new_callable=AsyncMock) as mock_set:
            mock_sget.return_value = SimpleNamespace(room_id=room_id)
            mock_rget.return_value = SimpleNamespace(user_id=owner_id)
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
    async def test_set_session_tags_admin_bypass(self, service, mock_db_session):
        """测试 Admin 可旁路为非己房间设置标签"""
        # Arrange
        session_id = uuid4()
        room_id = uuid4()
        tag1_id = uuid4()
        request_data = SessionTagsSetRequest(tag_ids=[tag1_id], mode="replace")

        mock_tag1 = Tag(id=tag1_id, name="标签1", is_active=True, created_at=datetime.now(), updated_at=datetime.now())
        mock_scalars = Mock()
        mock_scalars.all.return_value = [mock_tag1]
        mock_result = Mock()
        mock_result.scalars.return_value = mock_scalars
        mock_db_session.execute.return_value = mock_result

        with patch('app.services.content_management_service.crud_session.get', new_callable=AsyncMock) as mock_sget, \
             patch('app.services.content_management_service.crud_room.get', new_callable=AsyncMock) as mock_rget, \
             patch('app.crud.content_management.set_session_tags', new_callable=AsyncMock) as mock_set:
            mock_sget.return_value = SimpleNamespace(room_id=room_id)
            mock_rget.return_value = SimpleNamespace(user_id=uuid4())  # 非本人房间
            mock_set.return_value = [mock_tag1]

            result = await service.set_session_tags(
                mock_db_session, session_id, request_data, current_user_id=uuid4(), role='ADMIN'
            )

            assert result.code == 200
            mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_session_tags_invalid_tag_ids(self, service, mock_db_session):
        """测试设置场次标签时部分tag_id不存在或已停用"""
        # Arrange
        session_id = uuid4()
        room_id = uuid4()
        owner_id = uuid4()
        tag1_id = uuid4()
        tag2_id = uuid4()
        request_data = SessionTagsSetRequest(tag_ids=[tag1_id, tag2_id], mode="replace")

        mock_tag1 = Tag(id=tag1_id, name="标签1", is_active=True, created_at=datetime.now(), updated_at=datetime.now())
        mock_scalars = Mock()
        mock_scalars.all.return_value = [mock_tag1]  # 期望2个只返回1个
        mock_result = Mock()
        mock_result.scalars.return_value = mock_scalars
        mock_db_session.execute.return_value = mock_result

        with patch('app.services.content_management_service.crud_session.get', new_callable=AsyncMock) as mock_sget, \
             patch('app.services.content_management_service.crud_room.get', new_callable=AsyncMock) as mock_rget:
            mock_sget.return_value = SimpleNamespace(room_id=room_id)
            mock_rget.return_value = SimpleNamespace(user_id=owner_id)

            with pytest.raises(InvalidParameterException, match="部分标签ID不存在"):
                await service.set_session_tags(
                    mock_db_session, session_id, request_data, current_user_id=owner_id, role='REGULAR'
                )

    @pytest.mark.asyncio
    async def test_set_session_tags_permission_denied_non_owner(self, service, mock_db_session):
        """测试非房主 REGULAR 设置他人场次标签失败（V2 权限收窄）"""
        # Arrange
        session_id = uuid4()
        room_id = uuid4()
        request_data = SessionTagsSetRequest(tag_ids=[uuid4()], mode="replace")

        with patch('app.services.content_management_service.crud_session.get', new_callable=AsyncMock) as mock_sget, \
             patch('app.services.content_management_service.crud_room.get', new_callable=AsyncMock) as mock_rget:
            mock_sget.return_value = SimpleNamespace(room_id=room_id)
            mock_rget.return_value = SimpleNamespace(user_id=uuid4())  # 房主是别人

            with pytest.raises(PermissionDeniedException, match="需要管理员或房间创建者权限"):
                await service.set_session_tags(
                    mock_db_session, session_id, request_data, current_user_id=uuid4(), role='REGULAR'
                )

        mock_db_session.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_set_session_tags_session_not_found(self, service, mock_db_session):
        """测试场次不存在返回404"""
        session_id = uuid4()
        request_data = SessionTagsSetRequest(tag_ids=[], mode="replace")

        with patch('app.services.content_management_service.crud_session.get', new_callable=AsyncMock) as mock_sget:
            mock_sget.return_value = None

            with pytest.raises(NotFoundException, match="场次不存在"):
                await service.set_session_tags(
                    mock_db_session, session_id, request_data, current_user_id=uuid4(), role='ADMIN'
                )

    @pytest.mark.asyncio
    async def test_set_session_tags_room_not_found(self, service, mock_db_session):
        """测试场次所属直播间不存在返回404"""
        session_id = uuid4()
        request_data = SessionTagsSetRequest(tag_ids=[], mode="replace")

        with patch('app.services.content_management_service.crud_session.get', new_callable=AsyncMock) as mock_sget, \
             patch('app.services.content_management_service.crud_room.get', new_callable=AsyncMock) as mock_rget:
            mock_sget.return_value = SimpleNamespace(room_id=uuid4())
            mock_rget.return_value = None

            with pytest.raises(NotFoundException, match="直播间不存在"):
                await service.set_session_tags(
                    mock_db_session, session_id, request_data, current_user_id=uuid4(), role='ADMIN'
                )

    @pytest.mark.asyncio
    async def test_set_session_tags_append_exceeds_max(self, service, mock_db_session):
        """测试 append 去重后总数超过5被拒绝（4001）"""
        # Arrange
        session_id = uuid4()
        room_id = uuid4()
        owner_id = uuid4()
        request_ids = [uuid4() for _ in range(5)]
        request_data = SessionTagsSetRequest(tag_ids=request_ids, mode="append")

        # 存在性校验：5个请求标签均有效
        mock_tags = [Tag(id=tid, name=f"标签{i}", is_active=True, created_at=datetime.now(), updated_at=datetime.now()) for i, tid in enumerate(request_ids)]
        mock_scalars = Mock()
        mock_scalars.all.return_value = mock_tags
        mock_result = Mock()
        mock_result.scalars.return_value = mock_scalars
        mock_db_session.execute.return_value = mock_result

        # 现有关联 3 个（与请求不重叠）→ 去重后 8 > 5
        existing_tags = [Tag(id=uuid4(), name=f"旧标签{i}", is_active=True) for i in range(3)]

        with patch('app.services.content_management_service.crud_session.get', new_callable=AsyncMock) as mock_sget, \
             patch('app.services.content_management_service.crud_room.get', new_callable=AsyncMock) as mock_rget, \
             patch('app.crud.content_management.get_tags_by_session_id', new_callable=AsyncMock) as mock_links, \
             patch('app.crud.content_management.set_session_tags', new_callable=AsyncMock) as mock_set:
            mock_sget.return_value = SimpleNamespace(room_id=room_id)
            mock_rget.return_value = SimpleNamespace(user_id=owner_id)
            mock_links.return_value = existing_tags

            with pytest.raises(InvalidParameterException, match="场次标签最多 5 个"):
                await service.set_session_tags(
                    mock_db_session, session_id, request_data, current_user_id=owner_id, role='REGULAR'
                )

            mock_set.assert_not_called()

    @pytest.mark.asyncio
    async def test_set_session_tags_append_exactly_max_ok(self, service, mock_db_session):
        """测试 append 后恰好5个允许"""
        session_id = uuid4()
        room_id = uuid4()
        owner_id = uuid4()
        new_ids = [uuid4() for _ in range(3)]
        request_data = SessionTagsSetRequest(tag_ids=new_ids, mode="append")

        new_tags = [Tag(id=tid, name=f"新标签{i}", is_active=True, created_at=datetime.now(), updated_at=datetime.now()) for i, tid in enumerate(new_ids)]
        mock_scalars = Mock()
        mock_scalars.all.return_value = new_tags
        mock_result = Mock()
        mock_result.scalars.return_value = mock_scalars
        mock_db_session.execute.return_value = mock_result

        existing_tags = [Tag(id=uuid4(), name=f"旧标签{i}", is_active=True) for i in range(2)]

        with patch('app.services.content_management_service.crud_session.get', new_callable=AsyncMock) as mock_sget, \
             patch('app.services.content_management_service.crud_room.get', new_callable=AsyncMock) as mock_rget, \
             patch('app.crud.content_management.get_tags_by_session_id', new_callable=AsyncMock) as mock_links, \
             patch('app.crud.content_management.set_session_tags', new_callable=AsyncMock) as mock_set:
            mock_sget.return_value = SimpleNamespace(room_id=room_id)
            mock_rget.return_value = SimpleNamespace(user_id=owner_id)
            mock_links.return_value = existing_tags
            mock_set.return_value = existing_tags + new_tags

            result = await service.set_session_tags(
                mock_db_session, session_id, request_data, current_user_id=owner_id, role='REGULAR'
            )

            assert result.code == 200
            mock_set.assert_called_once()

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
        """测试房主删除场次标签关联成功"""
        # Arrange
        session_id = uuid4()
        room_id = uuid4()
        owner_id = uuid4()
        tag_id = uuid4()

        with patch('app.services.content_management_service.crud_session.get', new_callable=AsyncMock) as mock_sget, \
             patch('app.services.content_management_service.crud_room.get', new_callable=AsyncMock) as mock_rget, \
             patch('app.crud.content_management.remove_session_tag', new_callable=AsyncMock) as mock_remove:
            mock_sget.return_value = SimpleNamespace(room_id=room_id)
            mock_rget.return_value = SimpleNamespace(user_id=owner_id)
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

    @pytest.mark.asyncio
    async def test_remove_session_tag_permission_denied_non_owner(self, service, mock_db_session):
        """测试非房主删除他人场次标签关联失败（V2 权限收窄）"""
        session_id = uuid4()
        room_id = uuid4()
        tag_id = uuid4()

        with patch('app.services.content_management_service.crud_session.get', new_callable=AsyncMock) as mock_sget, \
             patch('app.services.content_management_service.crud_room.get', new_callable=AsyncMock) as mock_rget:
            mock_sget.return_value = SimpleNamespace(room_id=room_id)
            mock_rget.return_value = SimpleNamespace(user_id=uuid4())

            with pytest.raises(PermissionDeniedException, match="需要管理员或房间创建者权限"):
                await service.remove_session_tag(
                    mock_db_session, session_id, tag_id, current_user_id=uuid4(), role='REGULAR'
                )

        mock_db_session.commit.assert_not_called()


class TestResolveTagService:
    """resolve_tag（解析或创建标签）Service层测试（V2 阶段 2）"""

    @pytest.mark.asyncio
    async def test_resolve_creates_new(self, service, mock_db_session):
        """resolve：未命中则新建（source=user, created_by=当前用户）"""
        name = "腹腔镜肝切除"
        request_data = TagResolveRequest(name=name)
        new_tag = Tag(id=uuid4(), name=name, is_active=True, source="user")

        with patch('app.services.content_management_service.check_scene_fields', new_callable=AsyncMock) as mock_safety, \
             patch('app.crud.content_management.get_tag_by_name', new_callable=AsyncMock) as mock_get, \
             patch('app.crud.content_management.create_tag', new_callable=AsyncMock) as mock_create:
            mock_get.return_value = None
            mock_create.return_value = new_tag

            result = await service.resolve_tag(mock_db_session, request_data, current_user_id=uuid4(), role='REGULAR')

            assert result.data.created is True
            assert result.data.name == name
            assert result.data.source == "user"
            assert mock_safety.call_args.kwargs["scene"] == "tag_name"
            assert mock_create.call_args.kwargs["source"] == "user"
            assert mock_db_session.commit.called

    @pytest.mark.asyncio
    async def test_resolve_reuses_existing(self, service, mock_db_session):
        """resolve：命中 active 则复用（created=False，同一 id）"""
        name = "微创"
        existing = Tag(id=uuid4(), name=name, is_active=True, source="admin",
                       created_at=datetime.now(), updated_at=datetime.now())

        with patch('app.services.content_management_service.check_scene_fields', new_callable=AsyncMock), \
             patch('app.crud.content_management.get_tag_by_name', new_callable=AsyncMock) as mock_get, \
             patch('app.crud.content_management.create_tag', new_callable=AsyncMock) as mock_create:
            mock_get.return_value = existing

            result = await service.resolve_tag(mock_db_session, TagResolveRequest(name=name), current_user_id=uuid4(), role='REGULAR')

            assert result.data.created is False
            assert result.data.id == existing.id
            mock_create.assert_not_called()

    @pytest.mark.asyncio
    async def test_resolve_soft_deleted_rejected(self, service, mock_db_session):
        """resolve：软删同名不复活 → 400「标签不可用」"""
        name = "已停用词"
        soft_deleted = Tag(id=uuid4(), name=name, is_active=False,
                           created_at=datetime.now(), updated_at=datetime.now())

        with patch('app.services.content_management_service.check_scene_fields', new_callable=AsyncMock), \
             patch('app.crud.content_management.get_tag_by_name', new_callable=AsyncMock) as mock_get, \
             patch('app.crud.content_management.create_tag', new_callable=AsyncMock) as mock_create:
            mock_get.return_value = soft_deleted

            with pytest.raises(InvalidParameterException, match="标签不可用"):
                await service.resolve_tag(mock_db_session, TagResolveRequest(name=name), current_user_id=uuid4(), role='REGULAR')

            mock_create.assert_not_called()

    @pytest.mark.asyncio
    async def test_resolve_unauthorized(self, service, mock_db_session):
        """resolve：guest 未登录 → PermissionDenied"""
        with pytest.raises(PermissionDeniedException, match="需要登录后才能执行此操作"):
            await service.resolve_tag(mock_db_session, TagResolveRequest(name="任意词"), current_user_id=uuid4(), role='guest')

    @pytest.mark.asyncio
    async def test_resolve_content_safety_blocked(self, service, mock_db_session):
        """resolve：内容安全拦截则不查库不创建"""
        with patch('app.services.content_management_service.check_scene_fields', new_callable=AsyncMock) as mock_safety, \
             patch('app.crud.content_management.get_tag_by_name', new_callable=AsyncMock) as mock_get, \
             patch('app.crud.content_management.create_tag', new_callable=AsyncMock) as mock_create:
            mock_safety.side_effect = ContentSafetyBlockedException("违规内容")

            with pytest.raises(ContentSafetyBlockedException):
                await service.resolve_tag(mock_db_session, TagResolveRequest(name="违规词"), current_user_id=uuid4(), role='REGULAR')

            mock_get.assert_not_called()
            mock_create.assert_not_called()

    @pytest.mark.asyncio
    async def test_resolve_concurrent_race_returns_existing(self, service, mock_db_session):
        """resolve：并发唯一冲突 → rollback 再查返回已有（幂等）"""
        name = "并发词"
        raced = Tag(id=uuid4(), name=name, is_active=True, source="user",
                    created_at=datetime.now(), updated_at=datetime.now())

        with patch('app.services.content_management_service.check_scene_fields', new_callable=AsyncMock), \
             patch('app.crud.content_management.get_tag_by_name', new_callable=AsyncMock) as mock_get, \
             patch('app.crud.content_management.create_tag', new_callable=AsyncMock) as mock_create:
            mock_get.side_effect = [None, raced]  # 首次未命中，冲突后再查命中
            mock_create.side_effect = DatabaseIntegrityException("标签名称已存在")

            result = await service.resolve_tag(mock_db_session, TagResolveRequest(name=name), current_user_id=uuid4(), role='REGULAR')

            assert result.data.created is False
            assert result.data.id == raced.id
            mock_db_session.rollback.assert_called()

    @pytest.mark.asyncio
    async def test_resolve_concurrent_race_soft_deleted(self, service, mock_db_session):
        """resolve：并发冲突后查到软删行 → 400「标签不可用」"""
        name = "并发软删词"
        raced = Tag(id=uuid4(), name=name, is_active=False,
                    created_at=datetime.now(), updated_at=datetime.now())

        with patch('app.services.content_management_service.check_scene_fields', new_callable=AsyncMock), \
             patch('app.crud.content_management.get_tag_by_name', new_callable=AsyncMock) as mock_get, \
             patch('app.crud.content_management.create_tag', new_callable=AsyncMock) as mock_create:
            mock_get.side_effect = [None, raced]
            mock_create.side_effect = DatabaseIntegrityException("标签名称已存在")

            with pytest.raises(InvalidParameterException, match="标签不可用"):
                await service.resolve_tag(mock_db_session, TagResolveRequest(name=name), current_user_id=uuid4(), role='REGULAR')


# ============================================================================
# Permission Guard Tests
# ============================================================================

class TestPermissionGuards:
    """权限守卫函数测试"""
    
    def test_check_admin_permission_admin(self, service):
        """测试管理员权限检查通过"""
        # Act & Assert (不应抛出异常)
        check_admin_permission('ADMIN')
        check_admin_permission('SUPERADMIN')
    
    def test_check_admin_permission_user(self, service):
        """测试普通用户权限检查失败"""
        # Act & Assert
        with pytest.raises(PermissionDeniedException, match="需要管理员权限"):
            check_admin_permission('REGULAR')
    
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
        mock_cat1 = Category(id=uuid4(), name="分类1", sort_order=0, is_active=True, standard=True, created_at=datetime.now(), updated_at=datetime.now())
        mock_cat2 = Category(id=uuid4(), name="分类2", sort_order=1, is_active=True, standard=True, created_at=datetime.now(), updated_at=datetime.now())
        # mock LiveRoomCategory-like objects with .category and .is_primary
        mock_lrc1 = type('LRC', (), {'category': mock_cat1, 'is_primary': True})()
        mock_lrc2 = type('LRC', (), {'category': mock_cat2, 'is_primary': False})()

        with patch('app.crud.room.get', new_callable=AsyncMock) as mock_room_get:
            with patch('app.crud.content_management.get_categories_by_room_id', new_callable=AsyncMock) as mock_get_cats:
                mock_room_get.return_value = mock_room
                mock_get_cats.return_value = [mock_lrc1, mock_lrc2]

                result = await service.get_live_room_categories_list(
                    mock_db_session, room_id, current_user_id=None, role=None
                )

                assert isinstance(result, LiveRoomCategoriesListResponse)
                assert result.code == 200
                assert len(result.data) == 2
                assert result.data[0].is_primary is True
                assert result.data[1].is_primary is False
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
        # mock LiveRoomCategory-like objects with .category and .is_primary
        mock_lrc1 = type('LRC', (), {
            'category': Category(id=cat_id1, name="c1", sort_order=0, is_active=True, standard=True, created_at=datetime.now(), updated_at=datetime.now()),
            'is_primary': True,
        })()
        mock_lrc2 = type('LRC', (), {
            'category': Category(id=cat_id2, name="c2", sort_order=1, is_active=True, standard=True, created_at=datetime.now(), updated_at=datetime.now()),
            'is_primary': False,
        })()
        mock_lrcs = [mock_lrc1, mock_lrc2]
        body = LiveRoomCategoriesSetRequest(category_ids=[cat_id1, cat_id2], mode="replace", primary_category_id=cat_id1)

        mock_scalars_result = Mock()
        mock_scalars_result.all.return_value = [Mock(id=cat_id1, is_active=True), Mock(id=cat_id2, is_active=True)]
        mock_result = Mock()
        mock_result.scalars.return_value = mock_scalars_result
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        with patch('app.crud.room.get', new_callable=AsyncMock) as mock_room_get:
            with patch('app.crud.content_management.set_live_room_categories', new_callable=AsyncMock) as mock_set:
                mock_room_get.return_value = mock_room
                mock_set.return_value = mock_lrcs

                result = await service.set_live_room_categories(
                    mock_db_session, room_id, body, current_user_id=uuid4(), role="ADMIN"
                )

                assert result.code == 200
                assert result.data["room_id"] == str(room_id)
                assert result.data["mode"] == "replace"
                assert len(result.data["categories"]) == 2
                mock_room_get.assert_called_once_with(mock_db_session, room_id)
                mock_set.assert_called_once_with(mock_db_session, room_id, [cat_id1, cat_id2], "replace", cat_id1)

    @pytest.mark.asyncio
    async def test_set_live_room_categories_permission_denied(self, service, mock_db_session):
        """测试非管理员设置直播间分类权限不足"""
        room_id = uuid4()
        cat_id = uuid4()
        body = LiveRoomCategoriesSetRequest(category_ids=[cat_id], mode="replace", primary_category_id=cat_id)

        mock_room = type('Room', (), {'id': room_id})()
        with patch('app.crud.room.get', new_callable=AsyncMock) as mock_room_get:
            mock_room_get.return_value = mock_room

            with pytest.raises(PermissionDeniedException, match="需要管理员权限"):
                await service.set_live_room_categories(
                    mock_db_session, room_id, body, current_user_id=uuid4(), role="REGULAR"
                )

    @pytest.mark.asyncio
    async def test_set_live_room_categories_room_not_found(self, service, mock_db_session):
        """测试房间不存在时抛出 NotFoundException"""
        room_id = uuid4()
        cat_id = uuid4()
        body = LiveRoomCategoriesSetRequest(category_ids=[cat_id], mode="replace", primary_category_id=cat_id)

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
        body = LiveRoomCategoriesSetRequest(category_ids=[cat_id], mode="replace", primary_category_id=cat_id)
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
        mock_room = type('Room', (), {'id': room_id})()
        mock_cat_result = Mock(scalar_one_or_none=Mock(return_value=None))
        mock_db_session.execute = AsyncMock(return_value=mock_cat_result)

        with patch('app.crud.room.get', new_callable=AsyncMock) as mock_room_get:
            mock_room_get.return_value = mock_room
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
        mock_room = type('Room', (), {'id': room_id})()

        with patch('app.crud.room.get', new_callable=AsyncMock) as mock_room_get:
            mock_room_get.return_value = mock_room
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
        mock_room = type('Room', (), {'id': room_id})()

        with patch('app.crud.room.get', new_callable=AsyncMock) as mock_room_get:
            mock_room_get.return_value = mock_room

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
        is_active=True, standard=True,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    saved_url = "/media/categories/xxx/icon_1.jpg"
    updated_category = Category(
        id=category_id,
        name="测试科室",
        icon=saved_url,
        sort_order=0,
        is_active=True, standard=True,
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
        is_active=True, standard=True,
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
        is_active=True, standard=True,
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


# ============================================================================
# delete_category（阶段0：统一计数 + 结构化 references）
# ============================================================================

@pytest.mark.asyncio
async def test_delete_category_blocked_with_structured_references(service, mock_db_session):
    """非 force 删除含五类引用的分类 → 409 结构（五类数字 + 结构化 warnings）"""
    from app.crud.content_management import CategoryReferenceCount

    category_id = uuid4()
    refs = CategoryReferenceCount(
        expert_all=5, expert_active=3, department_count=1,
        room_count=2, active_child_count=2,
    )
    mock_category = Category(id=category_id, name="测试分类", slug="test-cat", sort_order=0, is_active=True)
    with patch('app.crud.content_management.get_category_by_id', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_category
        with patch('app.crud.content_management.count_category_references', new_callable=AsyncMock) as mock_count:
            mock_count.return_value = refs

            result = await service.delete_category(
                mock_db_session, category_id, current_user_id=uuid4(), role="ADMIN", force=False
            )

    assert result["blocked"] is True
    refs_out = result["references"]
    assert refs_out["expert_all"] == 5
    assert refs_out["expert_active"] == 3
    assert refs_out["department_count"] == 1
    assert refs_out["room_count"] == 2
    assert refs_out["active_child_count"] == 2
    # warnings 覆盖四类提示
    joined = " ".join(result["warnings"])
    assert "5 位专家引用" in joined
    assert "1 个科室引用" in joined
    assert "2 个直播间关联" in joined
    assert "2 个启用子分类" in joined
    # 未执行软删
    mock_db_session.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_delete_category_no_refs_success(service, mock_db_session):
    """无引用分类删除成功（不返回 blocked）"""
    from app.crud.content_management import CategoryReferenceCount

    category_id = uuid4()
    mock_category = Category(id=category_id, name="测试分类", slug="test-cat", sort_order=0, is_active=True)
    with patch('app.crud.content_management.get_category_by_id', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_category
        with patch('app.crud.content_management.count_category_references', new_callable=AsyncMock) as mock_count:
            mock_count.return_value = CategoryReferenceCount()
            with patch('app.crud.content_management.delete_category', new_callable=AsyncMock) as mock_del:
                mock_del.return_value = True

                result = await service.delete_category(
                    mock_db_session, category_id, current_user_id=uuid4(), role="ADMIN", force=False
                )

    assert result == {"message": "删除成功"}
    mock_del.assert_called_once_with(mock_db_session, category_id)
    mock_db_session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete_category_other_slug_forbidden(service, mock_db_session):
    """兜底分类 slug=other 禁止删除"""
    category_id = uuid4()
    mock_category = Category(id=category_id, name="其他", slug="other", sort_order=99, is_active=True)
    with patch('app.crud.content_management.get_category_by_id', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_category

        with pytest.raises(InvalidParameterException) as exc_info:
            await service.delete_category(
                mock_db_session, category_id, current_user_id=uuid4(), role="ADMIN", force=True
            )
    assert "禁止删除" in str(exc_info.value)


@pytest.mark.asyncio
async def test_delete_category_force_cascade_and_migrate(service, mock_db_session):
    """force=true：引用安顿（迁移到 target/其他）+ 级联停用子树，返回迁移统计"""
    from app.crud.content_management import CategoryReferenceCount

    category_id = uuid4()
    target_id = uuid4()
    child_id = uuid4()
    other_id = uuid4()
    mock_category = Category(id=category_id, name="外科", slug="surgery", sort_order=0, is_active=True)
    refs = CategoryReferenceCount(expert_all=3, expert_active=2, department_count=1, room_count=1, active_child_count=1)

    with patch('app.crud.content_management.get_category_by_id', new_callable=AsyncMock) as mock_get, \
         patch('app.crud.content_management.count_category_references', new_callable=AsyncMock) as mock_count, \
         patch('app.crud.content_management.get_category_descendant_ids', new_callable=AsyncMock) as mock_subtree, \
         patch('app.crud.content_management.migrate_category_references', new_callable=AsyncMock) as mock_migrate, \
         patch('app.crud.content_management.cascade_disable_category_tree', new_callable=AsyncMock) as mock_cascade:
        mock_get.return_value = mock_category
        mock_count.return_value = refs
        mock_subtree.return_value = [category_id, child_id]
        mock_migrate.return_value = {"expert_count": 3, "department_count": 1, "room_count": 1}
        mock_cascade.return_value = 2

        result = await service.delete_category(
            mock_db_session, category_id, current_user_id=uuid4(), role="ADMIN",
            force=True, target_category_id=target_id,
        )

    assert result["message"] == "删除成功（引用已迁移）"
    assert result["migrated"] == {"expert_count": 3, "department_count": 1, "room_count": 1}
    assert result["disabled_category_count"] == 2
    # 子树传递（含自身+子分类）→ 迁移 + 级联
    mock_migrate.assert_called_once_with(mock_db_session, [category_id, child_id], target_id)
    mock_cascade.assert_called_once_with(mock_db_session, [category_id, child_id])
    mock_db_session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete_category_force_target_is_self_rejected(service, mock_db_session):
    """迁移目标不能是分类自身"""
    from app.crud.content_management import CategoryReferenceCount

    category_id = uuid4()
    mock_category = Category(id=category_id, name="外科", slug="surgery", sort_order=0, is_active=True)
    refs = CategoryReferenceCount(expert_all=1, expert_active=1)

    with patch('app.crud.content_management.get_category_by_id', new_callable=AsyncMock) as mock_get, \
         patch('app.crud.content_management.count_category_references', new_callable=AsyncMock) as mock_count:
        mock_get.return_value = mock_category
        mock_count.return_value = refs

        with pytest.raises(InvalidParameterException) as exc_info:
            await service.delete_category(
                mock_db_session, category_id, current_user_id=uuid4(), role="ADMIN",
                force=True, target_category_id=category_id,
            )
    assert "不能是分类自身" in str(exc_info.value)


@pytest.mark.asyncio
async def test_delete_category_force_defaults_to_other_slug(service, mock_db_session):
    """未传 target 时默认迁移到 slug=other 的兜底分类"""
    from app.crud.content_management import CategoryReferenceCount

    category_id = uuid4()
    other_id = uuid4()
    mock_category = Category(id=category_id, name="外科", slug="surgery", sort_order=0, is_active=True)
    mock_other = Category(id=other_id, name="其他", slug="other", sort_order=99, is_active=True)
    refs = CategoryReferenceCount(expert_all=1, expert_active=1)

    with patch('app.crud.content_management.get_category_by_id', new_callable=AsyncMock) as mock_get, \
         patch('app.crud.content_management.count_category_references', new_callable=AsyncMock) as mock_count, \
         patch('app.crud.content_management.get_category_by_slug', new_callable=AsyncMock) as mock_slug, \
         patch('app.crud.content_management.get_category_descendant_ids', new_callable=AsyncMock) as mock_subtree, \
         patch('app.crud.content_management.migrate_category_references', new_callable=AsyncMock) as mock_migrate, \
         patch('app.crud.content_management.cascade_disable_category_tree', new_callable=AsyncMock) as mock_cascade:
        mock_get.return_value = mock_category
        mock_count.return_value = refs
        mock_slug.return_value = mock_other
        mock_subtree.return_value = [category_id]
        mock_migrate.return_value = {"expert_count": 1, "department_count": 0, "room_count": 0}
        mock_cascade.return_value = 1

        result = await service.delete_category(
            mock_db_session, category_id, current_user_id=uuid4(), role="ADMIN", force=True
        )

    mock_slug.assert_called_once_with(mock_db_session, "other")
    mock_migrate.assert_called_once_with(mock_db_session, [category_id], other_id)
    assert result["migrated"]["expert_count"] == 1


# ============================================================================
# _validate_category_hierarchy（阶段2：子孙循环 + 有子分类禁改层级）
# ============================================================================

@pytest.mark.asyncio
async def test_validate_hierarchy_rejects_descendant_cycle(service, mock_db_session):
    """规则2：parent_id 不能是自身子孙（循环）"""
    category_id = uuid4()
    parent_id = uuid4()
    data = CategoryUpdate(name="测试", parent_id=parent_id)

    mock_parent = Category(id=parent_id, name="子孙分类", parent_id=None, sort_order=0, is_active=True)
    mock_db_session.execute = AsyncMock(
        return_value=Mock(scalar_one_or_none=Mock(return_value=mock_parent))
    )
    with patch('app.crud.content_management.get_category_descendant_ids', new_callable=AsyncMock) as mock_subtree:
        mock_subtree.return_value = [category_id, parent_id]  # parent 是自身的子孙

        with pytest.raises(InvalidParameterException) as exc_info:
            await service._validate_category_hierarchy(
                mock_db_session, data, existing_category_id=category_id
            )
    assert "子孙分类" in str(exc_info.value)


@pytest.mark.asyncio
async def test_validate_hierarchy_rejects_self_parent(service, mock_db_session):
    """规则2：parent_id 不能是自身"""
    category_id = uuid4()
    data = CategoryUpdate(name="测试", parent_id=category_id)

    mock_parent = Category(id=category_id, name="自身", parent_id=None, sort_order=0, is_active=True)
    mock_db_session.execute = AsyncMock(
        return_value=Mock(scalar_one_or_none=Mock(return_value=mock_parent))
    )

    with pytest.raises(InvalidParameterException) as exc_info:
        await service._validate_category_hierarchy(
            mock_db_session, data, existing_category_id=category_id
        )
    assert "不能将自己设为父分类" in str(exc_info.value)


@pytest.mark.asyncio
async def test_validate_hierarchy_rejects_change_with_active_children(service, mock_db_session):
    """规则4：有 active 子分类的分类禁止调整层级"""
    category_id = uuid4()
    parent_id = uuid4()
    data = CategoryUpdate(name="测试", parent_id=parent_id)

    mock_existing = Category(id=category_id, name="外科", parent_id=None, sort_order=0, is_active=True)
    mock_parent = Category(id=parent_id, name="内科", parent_id=None, sort_order=0, is_active=True)
    mock_cat_result = Mock(scalar_one_or_none=Mock(return_value=mock_existing))
    mock_count_result = Mock(scalar_one=Mock(return_value=2))

    with patch('app.crud.content_management.get_category_descendant_ids', new_callable=AsyncMock) as mock_subtree, \
         patch('app.services.content_management_service.select') as mock_select:
        mock_subtree.return_value = [category_id]
        # 第一次 select：父分类查询；第二次：existing 查询；第三次：子分类计数
        mock_select.return_value.where.return_value = None
        # 用 execute 返回序列控制
        results = [Mock(scalar_one_or_none=Mock(return_value=mock_parent)), mock_cat_result, mock_count_result]
        mock_db_session.execute = AsyncMock(side_effect=results)

        with pytest.raises(InvalidParameterException) as exc_info:
            await service._validate_category_hierarchy(
                mock_db_session, data, existing_category_id=category_id
            )
    assert "启用子分类" in str(exc_info.value)


@pytest.mark.asyncio
async def test_validate_hierarchy_promote_to_root_with_children_allowed(service, mock_db_session):
    """规则4：提升为一级（parent_id=None）不受限——含子分类也可提升"""
    category_id = uuid4()
    data = CategoryUpdate(name="测试", parent_id=None)

    # parent_id=None 直接 return，不触发任何查询
    await service._validate_category_hierarchy(
        mock_db_session, data, existing_category_id=category_id
    )
    mock_db_session.execute.assert_not_awaited()


# ============================================================================
# migrate_category（阶段3 治理工具端点）
# ============================================================================

@pytest.mark.asyncio
async def test_migrate_category_success(service, mock_db_session):
    """合法迁移：scope 透传、提交、返回统计"""
    category_id = uuid4()
    target_id = uuid4()
    mock_source = Category(id=category_id, name="源分类", slug="src", sort_order=0, is_active=True)

    with patch('app.crud.content_management.get_category_by_id', new_callable=AsyncMock) as mock_get, \
         patch('app.crud.content_management.get_category_descendant_ids', new_callable=AsyncMock) as mock_subtree, \
         patch('app.crud.content_management.migrate_category_references', new_callable=AsyncMock) as mock_migrate:
        mock_get.side_effect = [mock_source, mock_source]  # source + target 查询
        mock_subtree.return_value = [category_id]
        mock_migrate.return_value = {"expert_count": 3, "department_count": 1, "room_count": 2}

        result = await service.migrate_category(
            mock_db_session, category_id, target_id, scope="all",
            current_user_id=uuid4(), role="ADMIN",
        )

    assert result == {"expert_count": 3, "department_count": 1, "room_count": 2}
    # 迁移范围 = 单分类自身（非子树）
    mock_migrate.assert_called_once_with(mock_db_session, [category_id], target_id, scope="all")
    mock_db_session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_migrate_category_scope_departments_only(service, mock_db_session):
    """scope=departments 透传"""
    category_id = uuid4()
    target_id = uuid4()
    mock_source = Category(id=category_id, name="源分类", slug="src", sort_order=0, is_active=True)

    with patch('app.crud.content_management.get_category_by_id', new_callable=AsyncMock) as mock_get, \
         patch('app.crud.content_management.get_category_descendant_ids', new_callable=AsyncMock) as mock_subtree, \
         patch('app.crud.content_management.migrate_category_references', new_callable=AsyncMock) as mock_migrate:
        mock_get.side_effect = [mock_source, mock_source]
        mock_subtree.return_value = [category_id]
        mock_migrate.return_value = {"expert_count": 0, "department_count": 1, "room_count": 0}

        result = await service.migrate_category(
            mock_db_session, category_id, target_id, scope="departments",
            current_user_id=uuid4(), role="ADMIN",
        )

    mock_migrate.assert_called_once_with(mock_db_session, [category_id], target_id, scope="departments")
    assert result["department_count"] == 1


@pytest.mark.asyncio
async def test_migrate_category_target_self_rejected(service, mock_db_session):
    """迁移目标不能是源分类自身"""
    category_id = uuid4()
    mock_source = Category(id=category_id, name="源分类", slug="src", sort_order=0, is_active=True)
    with patch('app.crud.content_management.get_category_by_id', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_source

        with pytest.raises(InvalidParameterException) as exc_info:
            await service.migrate_category(
                mock_db_session, category_id, category_id, scope="all",
                current_user_id=uuid4(), role="ADMIN",
            )
    assert "不能是源分类自身" in str(exc_info.value)


@pytest.mark.asyncio
async def test_migrate_category_target_in_subtree_rejected(service, mock_db_session):
    """迁移目标不能在源分类子树内（防循环）"""
    category_id = uuid4()
    target_id = uuid4()
    mock_source = Category(id=category_id, name="源分类", slug="src", sort_order=0, is_active=True)
    mock_target = Category(id=target_id, name="子分类", slug="child", parent_id=category_id, sort_order=0, is_active=True)

    with patch('app.crud.content_management.get_category_by_id', new_callable=AsyncMock) as mock_get, \
         patch('app.crud.content_management.get_category_descendant_ids', new_callable=AsyncMock) as mock_subtree:
        mock_get.side_effect = [mock_source, mock_target]
        mock_subtree.return_value = [category_id, target_id]

        with pytest.raises(InvalidParameterException) as exc_info:
            await service.migrate_category(
                mock_db_session, category_id, target_id, scope="all",
                current_user_id=uuid4(), role="ADMIN",
            )
    assert "子树内" in str(exc_info.value)


# ============================================================================
# merge_categories（阶段4 治理工具）
# ============================================================================

def _mock_merge_counts(db_session_mock, expert=3, dept=1, room=2, child=1, inconsistent=1):
    """构造 merge_categories 的统计查询返回序列（5 个 count 查询 + 尾部兜底）"""
    results = [
        Mock(scalar_one=Mock(return_value=expert)),
        Mock(scalar_one=Mock(return_value=dept)),
        Mock(scalar_one=Mock(return_value=room)),
        Mock(scalar_one=Mock(return_value=child)),
        Mock(scalar_one=Mock(return_value=inconsistent)),
    ]
    # 尾部兜底：真实执行中的子分类挂载 UPDATE 等非读取调用
    db_session_mock.execute = AsyncMock(side_effect=results + [AsyncMock()])


@pytest.mark.asyncio
async def test_merge_categories_dry_run_no_write(service, mock_db_session):
    """dry_run=true：返回统计且不落库"""
    source_id = uuid4()
    target_id = uuid4()
    mock_source = Category(id=source_id, name="消化科", slug="digestive", sort_order=0, is_active=True)
    mock_target = Category(id=target_id, name="胃肠科", slug="gastro", sort_order=0, is_active=True)

    with patch('app.crud.content_management.get_category_by_id', new_callable=AsyncMock) as mock_get, \
         patch('app.crud.content_management.get_category_descendant_ids', new_callable=AsyncMock) as mock_subtree:
        mock_get.side_effect = [mock_source, mock_target]
        mock_subtree.return_value = [source_id]
        _mock_merge_counts(mock_db_session)

        result = await service.merge_categories(
            mock_db_session, source_id, target_id,
            attach_children=False, dry_run=True,
            current_user_id=uuid4(), role="ADMIN",
        )

    assert result["dry_run"] is True
    assert result["expert_count"] == 3
    assert result["department_count"] == 1
    assert result["room_count"] == 2
    assert result["child_count"] == 1
    assert result["inconsistent_expert_count"] == 1
    mock_db_session.commit.assert_not_awaited()
    mock_db_session.add.assert_not_called()


@pytest.mark.asyncio
async def test_merge_categories_execute(service, mock_db_session):
    """真实合并：子分类挂载 + 引用迁移 + 软删 source"""
    source_id = uuid4()
    target_id = uuid4()
    mock_source = Category(id=source_id, name="消化科", slug="digestive", sort_order=0, is_active=True)
    mock_target = Category(id=target_id, name="胃肠科", slug="gastro", sort_order=0, is_active=True)

    with patch('app.crud.content_management.get_category_by_id', new_callable=AsyncMock) as mock_get, \
         patch('app.crud.content_management.get_category_descendant_ids', new_callable=AsyncMock) as mock_subtree, \
         patch('app.crud.content_management.migrate_category_references', new_callable=AsyncMock) as mock_migrate, \
         patch('app.crud.content_management.delete_category', new_callable=AsyncMock) as mock_del:
        mock_get.side_effect = [mock_source, mock_target]
        mock_subtree.return_value = [source_id]
        mock_migrate.return_value = {"expert_count": 3, "department_count": 1, "room_count": 2}
        mock_del.return_value = True
        _mock_merge_counts(mock_db_session)

        result = await service.merge_categories(
            mock_db_session, source_id, target_id,
            attach_children=False, dry_run=False,
            current_user_id=uuid4(), role="ADMIN",
        )

    assert result["dry_run"] is False
    assert result["expert_count"] == 3
    assert result["child_count"] == 1
    # 子分类挂到 target（attach_children=False → parent_id=target_id）
    child_update_call = [c for c in mock_db_session.execute.call_args_list if c.args and 'UPDATE categories' in str(c.args[0]) or (c.args and 'parent_id' in str(c.args[0]))]
    # 引用迁移：仅 source 自身（[source_id]）
    mock_migrate.assert_called_once_with(mock_db_session, [source_id], target_id, scope="all")
    mock_del.assert_called_once_with(mock_db_session, source_id)
    mock_db_session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_merge_categories_target_is_other_rejected(service, mock_db_session):
    """target 不能是兜底'其他'"""
    source_id = uuid4()
    target_id = uuid4()
    mock_source = Category(id=source_id, name="消化科", slug="digestive", sort_order=0, is_active=True)
    mock_target = Category(id=target_id, name="其他", slug="other", sort_order=99, is_active=True)

    with patch('app.crud.content_management.get_category_by_id', new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = [mock_source, mock_target]

        with pytest.raises(InvalidParameterException) as exc_info:
            await service.merge_categories(
                mock_db_session, source_id, target_id,
                current_user_id=uuid4(), role="ADMIN",
            )
    assert "兜底分类" in str(exc_info.value)


@pytest.mark.asyncio
async def test_merge_categories_target_second_level_with_children_rejected(service, mock_db_session):
    """target 为二级分类且 attach_children=false → 拒绝（会形成三层）"""
    source_id = uuid4()
    target_id = uuid4()
    mock_source = Category(id=source_id, name="消化科", slug="digestive", sort_order=0, is_active=True)
    mock_target = Category(id=target_id, name="内科子类", slug="inner-child", parent_id=uuid4(), sort_order=0, is_active=True)

    with patch('app.crud.content_management.get_category_by_id', new_callable=AsyncMock) as mock_get, \
         patch('app.crud.content_management.get_category_descendant_ids', new_callable=AsyncMock) as mock_subtree:
        mock_get.side_effect = [mock_source, mock_target]
        mock_subtree.return_value = [source_id]

        with pytest.raises(InvalidParameterException) as exc_info:
            await service.merge_categories(
                mock_db_session, source_id, target_id,
                attach_children=False, current_user_id=uuid4(), role="ADMIN",
            )
    assert "三层" in str(exc_info.value)


# ============================================================================
# 阶段6B：标准名校验（STANDARD_CATEGORY_NAMES）
# ============================================================================

@pytest.mark.asyncio
async def test_create_category_standard_name_allowed(service, mock_db_session):
    """standard=true + 名录内名称 → 放行"""
    data = CategoryCreate(name="精神科", slug="psychiatry", sort_order=1)
    with patch('app.crud.content_management.create_category', new_callable=AsyncMock) as mock_create:
        mock_create.return_value = Category(
            id=uuid4(), name="精神科", slug="psychiatry", sort_order=1,
            is_active=True, standard=True,
            created_at=datetime.now(), updated_at=datetime.now(),
        )

        result = await service.create_category(mock_db_session, data, current_user_id=uuid4(), role="ADMIN")

    assert result is not None
    mock_create.assert_called_once()


@pytest.mark.asyncio
async def test_create_category_standard_name_rejected(service, mock_db_session):
    """standard=true + 名录外名称 → 400"""
    data = CategoryCreate(name="飞刀科室", slug="x", sort_order=1, standard=True)
    with pytest.raises(InvalidParameterException) as exc_info:
        await service.create_category(mock_db_session, data, current_user_id=uuid4(), role="ADMIN")
    assert "名录" in str(exc_info.value)


@pytest.mark.asyncio
async def test_create_category_extension_name_allowed(service, mock_db_session):
    """standard=false（扩展科目）→ 名录外名称放行"""
    data = CategoryCreate(name="飞刀科室", slug="x", sort_order=1, standard=False)
    with patch('app.crud.content_management.create_category', new_callable=AsyncMock) as mock_create:
        mock_create.return_value = Category(
            id=uuid4(), name="飞刀科室", slug="x", sort_order=1,
            is_active=True, standard=False,
            created_at=datetime.now(), updated_at=datetime.now(),
        )

        result = await service.create_category(mock_db_session, data, current_user_id=uuid4(), role="ADMIN")

    assert result is not None


@pytest.mark.asyncio
async def test_update_category_standard_name_rejected(service, mock_db_session):
    """update 改 name：DB 现有 standard=true + 名录外名称 → 400"""
    category_id = uuid4()
    data = CategoryUpdate(name="飞刀科室")
    mock_existing = Category(id=category_id, name="精神科", slug="psychiatry", sort_order=1, is_active=True, standard=True)

    with patch('app.crud.content_management.get_category_by_id', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_existing

        with pytest.raises(InvalidParameterException) as exc_info:
            await service.update_category(mock_db_session, category_id, data, current_user_id=uuid4(), role="ADMIN")
    assert "名录" in str(exc_info.value)


@pytest.mark.asyncio
async def test_update_category_standard_false_allows_rename(service, mock_db_session):
    """update 显式 standard=false → 名录外名称放行"""
    category_id = uuid4()
    data = CategoryUpdate(name="飞刀科室", standard=False)
    mock_existing = Category(id=category_id, name="精神科", slug="psychiatry", sort_order=1, is_active=True, standard=True)
    mock_updated = Category(
        id=category_id, name="飞刀科室", slug="x", sort_order=1,
        is_active=True, standard=False,
        created_at=datetime.now(), updated_at=datetime.now(),
    )

    with patch('app.crud.content_management.get_category_by_id', new_callable=AsyncMock) as mock_get, \
         patch('app.crud.content_management.update_category', new_callable=AsyncMock) as mock_update:
        mock_get.return_value = mock_existing
        mock_update.return_value = mock_updated

        result = await service.update_category(mock_db_session, category_id, data, current_user_id=uuid4(), role="ADMIN")

    assert result is not None

