"""
AdminUserService 单元测试
对 app.services.admin_user_service.AdminUserService 的所有公共方法进行详细的、隔离的单元测试
"""
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.admin_user_service import (
    AdminUserService,
    TargetUserNotFoundError,
    PermissionDeniedError,
    InvalidAdminUpdateError,
)
from app.schemas.users import UserUpdate, UserFilterParams
from app.models.users import User, UserRole, EntityStatus


# ============================================================================
# 测试用例
# ============================================================================

class TestAdminUserService:
    """AdminUserService 测试类"""

    @pytest.fixture
    def mock_db_session(self):
        """模拟数据库会话"""
        return AsyncMock(spec=AsyncSession)

    @pytest.fixture
    def admin_user_service(self, mock_db_session):
        """AdminUserService 实例 fixture"""
        return AdminUserService(db=mock_db_session)

    @pytest.fixture
    def mock_admin_user(self):
        """创建模拟管理员用户"""
        mock_admin = MagicMock(spec=User)
        mock_admin.id = 1
        mock_admin.public_id = uuid.uuid4()
        mock_admin.uuid = mock_admin.public_id  # 兼容旧断言
        mock_admin.username = f"admin_{uuid.uuid4().hex[:8]}"
        mock_admin.email = f"admin_{uuid.uuid4().hex[:8]}@example.com"
        mock_admin.role = UserRole.ADMIN
        mock_admin.status = EntityStatus.NORMAL
        mock_admin.can_stream = False
        return mock_admin

    @pytest.fixture
    def mock_superadmin_user(self):
        """创建模拟超级管理员用户"""
        mock_superadmin = MagicMock(spec=User)
        mock_superadmin.id = 99
        mock_superadmin.public_id = uuid.uuid4()
        mock_superadmin.uuid = mock_superadmin.public_id
        mock_superadmin.username = f"superadmin_{uuid.uuid4().hex[:8]}"
        mock_superadmin.email = f"superadmin_{uuid.uuid4().hex[:8]}@example.com"
        mock_superadmin.role = UserRole.SUPERADMIN
        mock_superadmin.status = EntityStatus.NORMAL
        mock_superadmin.can_stream = False
        return mock_superadmin

    @pytest.fixture
    def mock_regular_user(self):
        """创建模拟普通用户"""
        mock_user = MagicMock(spec=User)
        mock_user.id = 2
        mock_user.public_id = uuid.uuid4()
        mock_user.uuid = mock_user.public_id
        mock_user.username = f"user_{uuid.uuid4().hex[:8]}"
        mock_user.email = f"user_{uuid.uuid4().hex[:8]}@example.com"
        mock_user.role = UserRole.REGULAR
        mock_user.status = EntityStatus.NORMAL
        mock_user.can_stream = False
        return mock_user

    @pytest.fixture
    def mock_user_filters(self):
        """创建模拟用户筛选条件"""
        return UserFilterParams(
            username=f"search_{uuid.uuid4().hex[:8]}",
            email=None,
            role=UserRole.REGULAR,
            status=EntityStatus.NORMAL
        )

    # ========================================================================
    # list_users 方法测试
    # ========================================================================

    async def test_list_users_success(self, admin_user_service, mock_user_filters, mocker):
        """
        测试成功列出用户列表
        
        准备: 模拟 crud_user 的方法返回预期数据
        执行: 调用 list_users 方法
        断言: 验证调用参数和返回结果
        """
        # Arrange - 准备测试数据
        page = 1
        size = 10
        skip = (page - 1) * size
        
        # 创建模拟用户列表
        mock_users = []
        for i in range(3):
            mock_user = MagicMock(spec=User)
            mock_user.id = i + 1
            mock_user.uuid = uuid.uuid4()
            mock_user.username = f"user_{uuid.uuid4().hex[:8]}"
            mock_user.email = f"user{i}_{uuid.uuid4().hex[:8]}@example.com"
            mock_user.role = UserRole.REGULAR
            mock_user.status = EntityStatus.NORMAL
            mock_users.append(mock_user)

        # Mock crud_user 方法
        mock_count_with_filtering = mocker.patch(
            'app.services.admin_user_service.crud_user.count_with_filtering'
        )
        mock_count_with_filtering.return_value = len(mock_users)

        mock_get_multi_with_filtering = mocker.patch(
            'app.services.admin_user_service.crud_user.get_multi_with_filtering'
        )
        mock_get_multi_with_filtering.return_value = mock_users

        # Mock UserResponse.model_validate
        mock_user_response_validate = mocker.patch(
            'app.services.admin_user_service.UserResponse.model_validate'
        )
        mock_user_response_validate.side_effect = lambda user: {
            "id": user.id,
            "uuid": str(user.uuid),
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "status": user.status
        }

        # Act - 执行被测试方法
        result = await admin_user_service.list_users(
            filters=mock_user_filters, page=page, size=size
        )

        # Assert - 验证结果
        # 验证 crud_user 方法被正确调用
        mock_count_with_filtering.assert_called_once_with(
            admin_user_service.db, filters=mock_user_filters
        )
        mock_get_multi_with_filtering.assert_called_once_with(
            admin_user_service.db, skip=skip, limit=size, filters=mock_user_filters
        )

        # 验证返回结果结构
        assert isinstance(result, dict)
        assert result["total"] == len(mock_users)
        assert result["page"] == page
        assert result["size"] == size
        assert len(result["items"]) == len(mock_users)

        # 验证 UserResponse.model_validate 被调用了正确的次数
        assert mock_user_response_validate.call_count == len(mock_users)

    async def test_list_users_with_serialization_error(self, admin_user_service, mock_user_filters, mocker):
        """
        测试列出用户时部分用户序列化失败的情况
        """
        # Arrange
        page = 1
        size = 10
        
        # 创建包含有问题用户的模拟列表
        mock_users = []
        for i in range(2):
            mock_user = MagicMock(spec=User)
            mock_user.id = i + 1
            mock_user.uuid = uuid.uuid4()
            mock_user.username = f"user_{uuid.uuid4().hex[:8]}"
            mock_user.email = f"user{i}_{uuid.uuid4().hex[:8]}@example.com"
            mock_user.role = UserRole.REGULAR
            mock_user.status = EntityStatus.NORMAL
            mock_users.append(mock_user)

        # Mock crud_user 方法
        mocker.patch(
            'app.services.admin_user_service.crud_user.count_with_filtering',
            return_value=2
        )
        mocker.patch(
            'app.services.admin_user_service.crud_user.get_multi_with_filtering',
            return_value=mock_users
        )

        # Mock UserResponse.model_validate - 第一个成功，第二个失败
        mock_user_response_validate = mocker.patch(
            'app.services.admin_user_service.UserResponse.model_validate'
        )
        mock_user_response_validate.side_effect = [
            {"id": 1, "username": "user1"},  # 第一个成功
            Exception("Serialization error")  # 第二个失败
        ]

        # Act
        result = await admin_user_service.list_users(
            filters=mock_user_filters, page=page, size=size
        )

        # Assert - 应该只返回成功序列化的用户
        assert result["total"] == 2  # 总数不变
        assert len(result["items"]) == 1  # 只有1个成功序列化的用户

    # ========================================================================
    # update_user_by_admin 方法测试
    # ========================================================================

    async def test_update_user_by_admin_success(
        self, admin_user_service, mock_admin_user, mock_regular_user, mocker
    ):
        """
        测试管理员成功更新用户开播权/状态（V2：ADMIN 不可改 role）
        """
        # Arrange - 准备测试数据
        user_uuid = mock_regular_user.public_id
        user_update = UserUpdate(
            can_stream=True,
            status=EntityStatus.BANNED
        )

        # 创建更新后的用户对象
        updated_user = MagicMock(spec=User)
        updated_user.id = mock_regular_user.id
        updated_user.public_id = mock_regular_user.public_id
        updated_user.uuid = mock_regular_user.public_id
        updated_user.username = mock_regular_user.username
        updated_user.email = mock_regular_user.email
        updated_user.role = UserRole.REGULAR
        updated_user.status = EntityStatus.BANNED
        updated_user.can_stream = True

        # Mock crud_user 方法
        mock_get_by_uuid = mocker.patch(
            'app.services.admin_user_service.crud_user.get_by_uuid'
        )
        mock_get_by_uuid.return_value = mock_regular_user

        mock_update = mocker.patch(
            'app.services.admin_user_service.crud_user.update'
        )
        mock_update.return_value = updated_user

        mock_revoke = mocker.patch.object(
            admin_user_service, '_revoke_user_sessions', new_callable=AsyncMock
        )

        # Act - 执行被测试方法
        result = await admin_user_service.update_user_by_admin(
            admin_user=mock_admin_user,
            user_uuid=user_uuid,
            user_update=user_update
        )

        # Assert - 验证结果
        # 验证 crud_user.get_by_uuid 被正确调用
        mock_get_by_uuid.assert_called_once_with(
            admin_user_service.db, public_id=user_uuid
        )

        # 验证 crud_user.update 被调用了一次
        mock_update.assert_called_once()
        
        # 验证传递给 update 的参数
        call_args = mock_update.call_args
        assert call_args[1]['db_obj'] == mock_regular_user
        assert call_args[1]['obj_in'] == user_update

        # 封禁触发吊销
        mock_revoke.assert_awaited_once_with(str(updated_user.public_id))

        # 验证返回的是更新后的用户对象
        assert result == updated_user

    async def test_update_user_by_admin_fails_if_user_not_found(
        self, admin_user_service, mock_admin_user, mocker
    ):
        """
        测试目标用户不存在时抛出 TargetUserNotFoundError
        
        准备: Mock crud_user.get_by_uuid 返回 None
        执行与断言: 使用 pytest.raises 验证抛出正确的异常
        """
        # Arrange
        user_uuid = uuid.uuid4()
        user_update = UserUpdate(role=UserRole.MODERATOR)

        # Mock crud_user.get_by_uuid 返回 None (用户不存在)
        mock_get_by_uuid = mocker.patch(
            'app.services.admin_user_service.crud_user.get_by_uuid'
        )
        mock_get_by_uuid.return_value = None

        # Act & Assert
        with pytest.raises(TargetUserNotFoundError) as exc_info:
            await admin_user_service.update_user_by_admin(
                admin_user=mock_admin_user,
                user_uuid=user_uuid,
                user_update=user_update
            )

        # 验证异常信息
        assert str(user_uuid) in str(exc_info.value)
        
        # 验证 crud_user.get_by_uuid 被调用
        mock_get_by_uuid.assert_called_once_with(
            admin_user_service.db, public_id=user_uuid
        )

    async def test_update_user_by_admin_fails_if_admin_updates_superadmin(
        self, admin_user_service, mock_admin_user, mock_superadmin_user, mocker
    ):
        """
        测试管理员尝试修改超级管理员时抛出 PermissionDeniedError
        
        准备: 创建 ADMIN 角色的管理员和 SUPERADMIN 角色的目标用户
        执行与断言: 验证抛出权限不足异常
        """
        # Arrange
        user_uuid = mock_superadmin_user.uuid
        user_update = UserUpdate(status=EntityStatus.BANNED)

        # Mock crud_user.get_by_uuid 返回超级管理员用户
        mock_get_by_uuid = mocker.patch(
            'app.services.admin_user_service.crud_user.get_by_uuid'
        )
        mock_get_by_uuid.return_value = mock_superadmin_user

        # Act & Assert
        with pytest.raises(PermissionDeniedError) as exc_info:
            await admin_user_service.update_user_by_admin(
                admin_user=mock_admin_user,  # ADMIN 角色
                user_uuid=user_uuid,
                user_update=user_update
            )

        # 验证异常信息
        assert "管理员无权修改超级管理员" in str(exc_info.value)
        
        # 验证 crud_user.get_by_uuid 被调用
        mock_get_by_uuid.assert_called_once_with(
            admin_user_service.db, public_id=user_uuid
        )

    async def test_update_user_by_admin_fails_if_admin_sets_superadmin_role(
        self, admin_user_service, mock_admin_user, mock_regular_user, mocker
    ):
        """V2 T4: ADMIN 修改他人 role → 403"""
        user_uuid = mock_regular_user.public_id
        user_update = UserUpdate(role=UserRole.SUPERADMIN)

        mock_get_by_uuid = mocker.patch(
            'app.services.admin_user_service.crud_user.get_by_uuid'
        )
        mock_get_by_uuid.return_value = mock_regular_user

        with pytest.raises(PermissionDeniedError) as exc_info:
            await admin_user_service.update_user_by_admin(
                admin_user=mock_admin_user,
                user_uuid=user_uuid,
                user_update=user_update
            )

        assert "仅超级管理员可修改用户角色" in str(exc_info.value)
        mock_get_by_uuid.assert_called_once_with(
            admin_user_service.db, public_id=user_uuid
        )

    async def test_update_user_by_admin_fails_if_self_edit(
        self, admin_user_service, mock_admin_user, mocker
    ):
        """V2 T6: 禁止管理员 PATCH 自己"""
        mocker.patch(
            'app.services.admin_user_service.crud_user.get_by_uuid',
            return_value=mock_admin_user,
        )
        with pytest.raises(PermissionDeniedError) as exc_info:
            await admin_user_service.update_user_by_admin(
                admin_user=mock_admin_user,
                user_uuid=mock_admin_user.public_id,
                user_update=UserUpdate(status=EntityStatus.BANNED),
            )
        assert "禁止修改自己的账号" in str(exc_info.value)

    async def test_update_user_by_admin_fails_if_admin_sets_pending_status(
        self, admin_user_service, mock_admin_user, mock_regular_user, mocker
    ):
        """ADMIN 日常 status 仅 NORMAL/BANNED"""
        mocker.patch(
            'app.services.admin_user_service.crud_user.get_by_uuid',
            return_value=mock_regular_user,
        )
        with pytest.raises(InvalidAdminUpdateError):
            await admin_user_service.update_user_by_admin(
                admin_user=mock_admin_user,
                user_uuid=mock_regular_user.public_id,
                user_update=UserUpdate(status=EntityStatus.PENDING_REVIEW),
            )

    async def test_revoke_when_can_stream_revoked(
        self, admin_user_service, mock_admin_user, mock_regular_user, mocker
    ):
        """禁止开播触发会话吊销"""
        mock_regular_user.can_stream = True
        updated = MagicMock(spec=User)
        updated.public_id = mock_regular_user.public_id
        updated.role = UserRole.REGULAR
        updated.status = EntityStatus.NORMAL
        updated.can_stream = False

        mocker.patch(
            'app.services.admin_user_service.crud_user.get_by_uuid',
            return_value=mock_regular_user,
        )
        mocker.patch(
            'app.services.admin_user_service.crud_user.update',
            return_value=updated,
        )
        mock_revoke = mocker.patch.object(
            admin_user_service, '_revoke_user_sessions', new_callable=AsyncMock
        )

        await admin_user_service.update_user_by_admin(
            admin_user=mock_admin_user,
            user_uuid=mock_regular_user.public_id,
            user_update=UserUpdate(can_stream=False),
        )
        mock_revoke.assert_awaited_once_with(str(updated.public_id))

    async def test_update_user_by_admin_success_superadmin_can_update_anyone(
        self, mock_db_session, mock_regular_user, mocker
    ):
        """V2 T5: SUPERADMIN 可任命 ADMIN"""
        mock_superadmin = MagicMock(spec=User)
        mock_superadmin.id = 99
        mock_superadmin.public_id = uuid.uuid4()
        mock_superadmin.role = UserRole.SUPERADMIN

        admin_user_service = AdminUserService(db=mock_db_session)
        user_uuid = mock_regular_user.public_id
        user_update = UserUpdate(role=UserRole.ADMIN)

        updated_user = MagicMock(spec=User)
        updated_user.public_id = mock_regular_user.public_id
        updated_user.role = UserRole.ADMIN
        updated_user.status = EntityStatus.NORMAL
        updated_user.can_stream = False

        mocker.patch(
            'app.services.admin_user_service.crud_user.get_by_uuid',
            return_value=mock_regular_user,
        )
        mock_update = mocker.patch(
            'app.services.admin_user_service.crud_user.update',
            return_value=updated_user,
        )
        mocker.patch.object(
            admin_user_service, '_revoke_user_sessions', new_callable=AsyncMock
        )

        result = await admin_user_service.update_user_by_admin(
            admin_user=mock_superadmin,
            user_uuid=user_uuid,
            user_update=user_update
        )

        mock_update.assert_called_once()
        assert result == updated_user

