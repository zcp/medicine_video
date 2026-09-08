"""
LiveCore Service - Experts Service Unit Tests

This module contains unit tests for the ExpertService business logic layer,
using mocks to isolate dependencies.
"""

import uuid
import pytest
from typing import List, Dict, Any
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

# 项目内导入
from app.services.expert_service import ExpertService
from app.models.experts import Expert, UserExpertSubscription, LiveSessionExpert, SessionExpertRole
from app.schemas.experts import ExpertCreate, ExpertUpdate, ExpertItem
from app.exceptions import (
    NotFoundException,
    PermissionDeniedException,
    InvalidParameterException,
    DatabaseIntegrityException
)


# ==================== 辅助函数 (Helper Functions) ====================

def create_mock_expert(
    expert_id: uuid.UUID = None,
    user_id: uuid.UUID = None,
    name: str = "测试专家",
    is_featured: bool = True,
    is_active: bool = True
) -> Expert:
    """创建Mock的Expert对象"""
    if expert_id is None:
        expert_id = uuid.uuid4()
    
    mock_expert = Expert(
        id=expert_id,
        user_id=user_id,
        name=name,
        title="主任医师",
        hospital="测试医院",
        department="测试科室",
        expertise_areas="测试擅长领域",
        bio="测试简介",
        avatar_url="/media/experts/test.jpg",
        is_featured=is_featured,
        is_active=is_active,
        sort_order=1
    )
    mock_expert.created_at = datetime.now()
    mock_expert.updated_at = datetime.now()
    
    return mock_expert


def create_mock_subscription(
    subscription_id: uuid.UUID = None,
    user_id: uuid.UUID = None,
    expert_id: uuid.UUID = None
) -> UserExpertSubscription:
    """创建Mock的UserExpertSubscription对象"""
    if subscription_id is None:
        subscription_id = uuid.uuid4()
    if user_id is None:
        user_id = uuid.uuid4()
    if expert_id is None:
        expert_id = uuid.uuid4()
    
    mock_subscription = UserExpertSubscription(
        id=subscription_id,
        user_id=user_id,
        expert_id=expert_id
    )
    mock_subscription.created_at = datetime.now()
    
    return mock_subscription


def create_mock_session_expert(
    session_expert_id: uuid.UUID = None,
    session_id: uuid.UUID = None,
    expert_id: uuid.UUID = None,
    role: SessionExpertRole = SessionExpertRole.MAIN_SPEAKER
) -> LiveSessionExpert:
    """创建Mock的LiveSessionExpert对象"""
    if session_expert_id is None:
        session_expert_id = uuid.uuid4()
    if session_id is None:
        session_id = uuid.uuid4()
    if expert_id is None:
        expert_id = uuid.uuid4()
    
    mock_session_expert = LiveSessionExpert(
        id=session_expert_id,
        session_id=session_id,
        expert_id=expert_id,
        role=role,
        sort_order=1
    )
    mock_session_expert.created_at = datetime.now()
    # ✅ 为 Service 层访问的 se.expert 提供一个简单 Expert 对象
    mock_session_expert.expert = create_mock_expert(expert_id=expert_id)
    return mock_session_expert


@pytest.fixture
def regular_user_role() -> str:
    """Service 层测试使用的普通用户角色（与 Service 实现保持一致）"""
    return "REGULAR"

# ==================== 权限守卫函数测试 ====================

class TestExpertServicePermissions:
    """权限守卫函数测试"""

    def test_check_admin_permission_success(self):
        """测试管理员权限检查成功"""
        service = ExpertService(Mock())
        
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

    def test_check_admin_permission_denied(self):
        """测试管理员权限检查失败"""
        service = ExpertService(Mock())
        
        # 测试USER角色
        with pytest.raises(PermissionDeniedException) as exc_info:
            service._check_admin_permission("USER")
        assert "需要管理员权限" in str(exc_info.value)
        
        # 测试None
        with pytest.raises(PermissionDeniedException):
            service._check_admin_permission(None)

    # ... 之前的代码 ...

    def test_check_user_resource_permission_success(self):
        """测试用户专属资源权限检查成功"""
        service = ExpertService(Mock())
        user_id = uuid.uuid4()

        # REGULAR / ADMIN / SUPERADMIN 应该都有用户资源操作权限（签名：resource_owner_id, current_user_id, role）
        for role in ("REGULAR", "ADMIN", "SUPERADMIN"):
            try:
                service._check_user_resource_permission(user_id, user_id, role)
            except PermissionDeniedException:
                pytest.fail(f"{role} 应有用户资源操作权限")

    def test_check_user_resource_permission_denied(self):
        """测试用户专属资源权限检查失败（未登录 role=None）"""
        service = ExpertService(Mock())
        user_id = uuid.uuid4()

        # 测试 None（未登录）：签名 resource_owner_id, current_user_id, role
        with pytest.raises(PermissionDeniedException) as exc_info:
            service._check_user_resource_permission(user_id, user_id, None)
        assert "需要登录后才能执行此操作" in str(exc_info.value)

    def test_check_expert_visibility_public(self):
        """测试专家可见性检查（公开）"""
        service = ExpertService(Mock())
        
        # 公开专家（is_featured=true）
        expert = create_mock_expert(is_featured=True)
        
        try:
            service._check_expert_visibility(expert, None, None)
        except NotFoundException:
            pytest.fail("公开专家应该可见")

    def test_check_expert_visibility_soft_deleted(self):
        """测试专家可见性检查（软删除：is_active=False 表示已下架）"""
        service = ExpertService(Mock())
        
        # 软删除的专家（is_active=False，与实现一致）
        expert = create_mock_expert(is_active=False)
        
        # 普通用户不可见
        with pytest.raises(NotFoundException) as exc_info:
            service._check_expert_visibility(expert, uuid.uuid4(), "REGULAR")
        assert "专家不存在" in str(exc_info.value)

    def test_check_expert_visibility_admin(self):
        """测试专家可见性检查（管理员）"""
        service = ExpertService(Mock())
        
        # 软删除的专家（is_active=False）
        expert = create_mock_expert(is_active=False)
        
        # 管理员可见
        try:
            service._check_expert_visibility(expert, uuid.uuid4(), "ADMIN")
        except NotFoundException:
            pytest.fail("管理员应该能看到软删除的专家")


# ==================== 专家信息管理Service测试 ====================

class TestExpertServiceExpertManagement:
    """专家信息管理Service测试"""

    @pytest.mark.asyncio
    async def test_get_featured_experts(self, mocker):
        """测试获取推荐专家列表"""
        mock_db = AsyncMock()

        # 准备Mock数据
        mock_experts = [
            create_mock_expert(name="专家1", is_featured=True),
            create_mock_expert(name="专家2", is_featured=True)
        ]

        # Mock CRUD函数
        mock_get_featured = mocker.patch(
            "app.crud.experts.get_featured_experts",
            new_callable=AsyncMock,
            return_value=mock_experts
        )

        # 调用Service
        service = ExpertService(mock_db)
        result = await service.get_featured_experts(limit=10)

        # 验证
        assert len(result) == 2
        assert result[0].name == "专家1"
        assert result[1].name == "专家2"
        # 按实现使用位置参数断言
        mock_get_featured.assert_called_once_with(mock_db, 10)

    @pytest.mark.asyncio
    async def test_get_expert_detail_success(self, mocker):
        """测试获取专家详情成功"""
        mock_db = mocker.Mock()
        expert_id = uuid.uuid4()
        
        # 准备Mock数据
        mock_expert = create_mock_expert(expert_id=expert_id, is_featured=True)
        
        # Mock CRUD函数
        mock_get_expert = mocker.patch(
            "app.crud.experts.get_expert",
            new_callable=AsyncMock,
            return_value=mock_expert
        )
        
        # 调用Service
        service = ExpertService(mock_db)
        result = await service.get_expert_detail(expert_id, None, None)
        
        # 验证
        assert result.id == expert_id
        assert result.name == "测试专家"
        mock_get_expert.assert_called_once_with(mock_db, expert_id)

    @pytest.mark.asyncio
    async def test_get_expert_detail_not_found(self, mocker):
        """测试获取专家详情不存在"""
        mock_db = mocker.Mock()
        expert_id = uuid.uuid4()
        
        # Mock CRUD函数（返回None）
        mock_get_expert = mocker.patch(
            "app.crud.experts.get_expert",
            new_callable=AsyncMock,
            return_value=None
        )
        
        # 调用Service（应该抛出NotFoundException）
        service = ExpertService(mock_db)
        with pytest.raises(NotFoundException) as exc_info:
            await service.get_expert_detail(expert_id, None, None)
        
        assert "专家不存在" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_expert_success(self, mocker, admin_user_id, admin_user_role):
        """测试创建专家成功"""
        mock_db = AsyncMock()
        
        # 准备测试数据
        expert_data = ExpertCreate(
            name="新专家",
            title="主任医师",
            hospital="测试医院",
            is_featured=True
        )
        mock_expert = create_mock_expert(name="新专家")
        
        # Mock CRUD函数
        mock_create = mocker.patch(
            "app.crud.experts.create_expert",
            new_callable=AsyncMock,
            return_value=mock_expert
        )
        mock_commit = mocker.patch.object(mock_db, "commit", new_callable=AsyncMock)
        
        # 调用Service
        service = ExpertService(mock_db)
        result = await service.create_expert(expert_data, admin_user_id, admin_user_role)
        
        # 验证
        assert result.name == "新专家"
        mock_create.assert_called_once_with(mock_db, expert_data)
        mock_commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_expert_no_permission(self, mocker, regular_user_id, regular_user_role):
        """测试创建专家无权限"""
        mock_db = mocker.Mock()
        
        # 准备测试数据
        expert_data = ExpertCreate(
            name="新专家",
            title="主任医师",
            hospital="测试医院"
        )
        
        # 调用Service（应该抛出PermissionDeniedException）
        service = ExpertService(mock_db)
        with pytest.raises(PermissionDeniedException):
            await service.create_expert(expert_data, regular_user_id, regular_user_role)

    @pytest.mark.asyncio
    async def test_create_expert_user_id_bound(self, mocker, admin_user_id, admin_user_role):
        """测试创建专家失败（user_id已绑定）"""
        mock_db = AsyncMock()

        # 准备测试数据
        user_id = uuid.uuid4()
        expert_data = ExpertCreate(
            user_id=user_id,
            name="新专家",
            title="主任医师",
            hospital="测试医院"
        )

        # 通过 get_expert_by_user_id 业务检查模拟“已绑定”
        mocker.patch(
            "app.crud.experts.get_expert_by_user_id",
            new_callable=AsyncMock,
            return_value=create_mock_expert(user_id=user_id),
        )

        service = ExpertService(mock_db)
        with pytest.raises(InvalidParameterException) as exc_info:
            await service.create_expert(expert_data, admin_user_id, admin_user_role)

        assert "该用户已绑定到其他专家档案" in str(exc_info.value)
        # 不再强制要求 rollback 被调用，因为异常来自业务检查分支

    @pytest.mark.asyncio
    async def test_get_experts_list_success(self, mocker, admin_user_id, admin_user_role):
        """测试获取专家列表成功"""
        mock_db = AsyncMock()

        # 准备Mock数据
        mock_experts = [
            create_mock_expert(name="专家1"),
            create_mock_expert(name="专家2")
        ]

        # Mock CRUD函数
        mock_get_multi = mocker.patch(
            "app.crud.experts.get_experts_multi_and_total",
            new_callable=AsyncMock,
            return_value=(mock_experts, 2)
        )

        service = ExpertService(mock_db)
        result = await service.get_experts_list(
            page=1, size=10, name=None, is_featured=None, hospital=None,
            sort="created_at:desc",  # ✅ 与 CRUD 约定格式一致
            current_user_id=admin_user_id, role=admin_user_role
        )

        assert result["total"] == 2
        assert result["page"] == 1
        assert result["size"] == 10
        assert len(result["items"]) == 2  # ✅ 使用 items，而不是 data


    @pytest.mark.asyncio
    async def test_get_experts_list_no_permission(self, mocker, regular_user_id, regular_user_role):
        """测试获取专家列表无权限"""
        mock_db = mocker.Mock()
        
        # 调用Service（应该抛出PermissionDeniedException）
        service = ExpertService(mock_db)
        with pytest.raises(PermissionDeniedException):
            await service.get_experts_list(
                page=1, size=10, name=None, is_featured=None, hospital=None, sort="created_at_desc",
                current_user_id=regular_user_id, role=regular_user_role
            )

    @pytest.mark.asyncio
    async def test_update_expert_success(self, mocker, admin_user_id, admin_user_role):
        """测试更新专家成功"""
        mock_db = AsyncMock()
        expert_id = uuid.uuid4()
        
        # 准备测试数据
        update_data = ExpertUpdate(name="新名称")
        mock_expert = create_mock_expert(expert_id=expert_id, name="新名称")
        
        # Mock CRUD函数
        mock_update = mocker.patch(
            "app.crud.experts.update_expert",
            new_callable=AsyncMock,
            return_value=mock_expert
        )
        mock_commit = mocker.patch.object(mock_db, "commit", new_callable=AsyncMock)
        
        # 调用Service
        service = ExpertService(mock_db)
        result = await service.update_expert(expert_id, update_data, admin_user_id, admin_user_role)
        
        # 验证
        assert result.name == "新名称"
        mock_update.assert_called_once_with(mock_db, expert_id, update_data)
        mock_commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_expert_not_found(self, mocker, admin_user_id, admin_user_role):
        """测试更新专家不存在"""
        mock_db = AsyncMock()
        expert_id = uuid.uuid4()
        
        # 准备测试数据
        update_data = ExpertUpdate(name="新名称")
        
        # Mock CRUD函数（返回None）
        mock_update = mocker.patch(
            "app.crud.experts.update_expert",
            new_callable=AsyncMock,
            return_value=None
        )
        mock_rollback = mocker.patch.object(mock_db, "rollback", new_callable=AsyncMock)
        
        # 调用Service（应该抛出NotFoundException）
        service = ExpertService(mock_db)
        with pytest.raises(NotFoundException):
            await service.update_expert(expert_id, update_data, admin_user_id, admin_user_role)
        
        mock_rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_expert_no_permission(self, mocker, regular_user_id, regular_user_role):
        """测试更新专家无权限"""
        mock_db = mocker.Mock()
        expert_id = uuid.uuid4()
        update_data = ExpertUpdate(name="新名称")
        
        # 调用Service（应该抛出PermissionDeniedException）
        service = ExpertService(mock_db)
        with pytest.raises(PermissionDeniedException):
            await service.update_expert(expert_id, update_data, regular_user_id, regular_user_role)

    @pytest.mark.asyncio
    async def test_delete_expert_success(self, mocker, admin_user_id, admin_user_role):
        """测试删除专家成功"""
        mock_db = AsyncMock()
        expert_id = uuid.uuid4()
        
        # Mock CRUD函数
        mock_delete = mocker.patch(
            "app.crud.experts.delete_expert",
            new_callable=AsyncMock,
            return_value=True
        )
        mock_commit = mocker.patch.object(mock_db, "commit", new_callable=AsyncMock)
        
        # 调用Service
        service = ExpertService(mock_db)
        await service.delete_expert(expert_id, admin_user_id, admin_user_role)
        
        # 验证
        mock_delete.assert_called_once_with(mock_db, expert_id)
        mock_commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_expert_not_found(self, mocker, admin_user_id, admin_user_role):
        """测试删除专家不存在"""
        mock_db = mocker.Mock()
        expert_id = uuid.uuid4()
        
        # Mock CRUD函数（返回False）
        mock_delete = mocker.patch(
            "app.crud.experts.delete_expert",
            new_callable=AsyncMock,
            return_value=False
        )
        mock_rollback = mocker.patch.object(mock_db, "rollback", new_callable=AsyncMock)
        
        # 调用Service（应该抛出NotFoundException）
        service = ExpertService(mock_db)
        with pytest.raises(NotFoundException):
            await service.delete_expert(expert_id, admin_user_id, admin_user_role)

    @pytest.mark.asyncio
    async def test_delete_expert_no_permission(self, mocker, regular_user_id, regular_user_role):
        """测试删除专家无权限"""
        mock_db = mocker.Mock()
        expert_id = uuid.uuid4()
        
        # 调用Service（应该抛出PermissionDeniedException）
        service = ExpertService(mock_db)
        with pytest.raises(PermissionDeniedException):
            await service.delete_expert(expert_id, regular_user_id, regular_user_role)


# ==================== 专家关注Service测试 ====================

class TestExpertServiceFollow:
    """专家关注Service测试"""

    @pytest.mark.asyncio
    async def test_follow_expert_success(self, mocker, regular_user_id, regular_user_role):
        """测试关注专家成功"""
        mock_db = AsyncMock()
        expert_id = uuid.uuid4()
        
        # 准备Mock数据
        mock_expert = create_mock_expert(expert_id=expert_id, is_featured=True)
        mock_subscription = create_mock_subscription(user_id=regular_user_id, expert_id=expert_id)
        
        # Mock CRUD函数
        mock_get_expert = mocker.patch(
            "app.crud.experts.get_expert",
            new_callable=AsyncMock,
            return_value=mock_expert
        )
        mock_get_subscription = mocker.patch(
            "app.crud.experts.get_subscription",
            new_callable=AsyncMock,
            return_value=None  # 未关注
        )
        mock_create_subscription = mocker.patch(
            "app.crud.experts.create_subscription",
            new_callable=AsyncMock,
            return_value=mock_subscription
        )
        mock_commit = mocker.patch.object(mock_db, "commit", new_callable=AsyncMock)
        
        # 调用Service
        service = ExpertService(mock_db)
        await service.follow_expert(expert_id, regular_user_id, regular_user_role)
        
        # 验证
        mock_create_subscription.assert_called_once_with(mock_db, regular_user_id, expert_id)
        mock_commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_follow_expert_not_found(self, mocker, regular_user_id, regular_user_role):
        """测试关注专家不存在"""
        mock_db = AsyncMock()
        expert_id = uuid.uuid4()
        
        # Mock CRUD函数（专家不存在）
        mock_get_expert = mocker.patch(
            "app.crud.experts.get_expert",
            new_callable=AsyncMock,
            return_value=None
        )
        
        # 调用Service（应该抛出NotFoundException）
        service = ExpertService(mock_db)
        with pytest.raises(NotFoundException):
            await service.follow_expert(expert_id, regular_user_id, regular_user_role)

    @pytest.mark.asyncio
    async def test_follow_expert_already_followed(self, mocker, regular_user_id, regular_user_role):
        """测试关注专家失败（已关注）"""
        mock_db = AsyncMock()
        expert_id = uuid.uuid4()
        
        # 准备Mock数据
        mock_expert = create_mock_expert(expert_id=expert_id, is_featured=True)
        mock_subscription = create_mock_subscription(user_id=regular_user_id, expert_id=expert_id)
        
        # Mock CRUD函数
        mock_get_expert = mocker.patch(
            "app.crud.experts.get_expert",
            new_callable=AsyncMock,
            return_value=mock_expert
        )
        mock_get_subscription = mocker.patch(
            "app.crud.experts.get_subscription",
            new_callable=AsyncMock,
            return_value=mock_subscription  # 已关注
        )
        
        # 调用Service（应该抛出InvalidParameterException）
        service = ExpertService(mock_db)
        with pytest.raises(InvalidParameterException) as exc_info:
            await service.follow_expert(expert_id, regular_user_id, regular_user_role)
        
        assert "已关注该专家" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_follow_expert_no_permission(self, mocker):
        """测试关注专家无权限"""
        mock_db = mocker.Mock()
        expert_id = uuid.uuid4()
        
        # 调用Service（应该抛出PermissionDeniedException）
        service = ExpertService(mock_db)
        with pytest.raises(PermissionDeniedException):
            await service.follow_expert(expert_id, None, None)

    @pytest.mark.asyncio
    async def test_unfollow_expert_success(self, mocker, regular_user_id, regular_user_role):
        """测试取消关注成功"""
        mock_db = mocker.Mock()
        expert_id = uuid.uuid4()
        
        # Mock CRUD函数
        mock_delete_subscription = mocker.patch(
            "app.crud.experts.delete_subscription",
            new_callable=AsyncMock,
            return_value=True
        )
        mock_commit = mocker.patch.object(mock_db, "commit", new_callable=AsyncMock)
        
        # 调用Service
        service = ExpertService(mock_db)
        await service.unfollow_expert(expert_id, regular_user_id, regular_user_role)
        
        # 验证
        mock_delete_subscription.assert_called_once_with(mock_db, regular_user_id, expert_id)
        mock_commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_unfollow_expert_not_followed(self, mocker, regular_user_id, regular_user_role):
        """测试取消关注失败（未关注）"""
        mock_db = mocker.Mock()
        expert_id = uuid.uuid4()
        
        # Mock CRUD函数（返回False）
        mock_delete_subscription = mocker.patch(
            "app.crud.experts.delete_subscription",
            new_callable=AsyncMock,
            return_value=False
        )
        mock_rollback = mocker.patch.object(mock_db, "rollback", new_callable=AsyncMock)
        
        # 调用Service（应该抛出NotFoundException）
        service = ExpertService(mock_db)
        with pytest.raises(NotFoundException):
            await service.unfollow_expert(expert_id, regular_user_id, regular_user_role)

    @pytest.mark.asyncio
    async def test_unfollow_expert_no_permission(self, mocker):
        """测试取消关注无权限"""
        mock_db = mocker.Mock()
        expert_id = uuid.uuid4()
        
        # 调用Service（应该抛出PermissionDeniedException）
        service = ExpertService(mock_db)
        with pytest.raises(PermissionDeniedException):
            await service.unfollow_expert(expert_id, None, None)

    @pytest.mark.asyncio
    async def test_get_followed_experts(self, mocker, regular_user_id, regular_user_role):
        """测试获取关注列表"""
        mock_db = AsyncMock()

        # 准备 Mock 的订阅记录和关联专家
        sub1 = create_mock_subscription(user_id=regular_user_id, expert_id=uuid.uuid4())
        sub2 = create_mock_subscription(user_id=regular_user_id, expert_id=uuid.uuid4())
        sub1.expert = create_mock_expert(expert_id=sub1.expert_id, name="专家1")
        sub2.expert = create_mock_expert(expert_id=sub2.expert_id, name="专家2")
        mock_subscriptions = [sub1, sub2]

        mock_get_subscriptions = mocker.patch(
            "app.crud.experts.get_user_subscriptions",
            new_callable=AsyncMock,
            return_value=mock_subscriptions
        )

        service = ExpertService(mock_db)
        result = await service.get_followed_experts(
            regular_user_id, regular_user_role, include_live_status=False
        )

        assert len(result) == 2
        assert result[0].name == "专家1"
        assert result[1].name == "专家2"
        mock_get_subscriptions.assert_called_once_with(mock_db, regular_user_id)


    @pytest.mark.asyncio
    async def test_check_is_followed_true(self, mocker, regular_user_id, regular_user_role):
        """测试检查已关注"""
        mock_db = mocker.Mock()
        expert_id = uuid.uuid4()
        
        # 准备Mock数据
        mock_expert = create_mock_expert(expert_id=expert_id, is_active=True)
        mock_subscription = create_mock_subscription(user_id=regular_user_id, expert_id=expert_id)
        
        # Mock CRUD：check_is_followed 先 get_expert 再 get_subscription，须同时 mock get_expert 避免 await mock_db
        mocker.patch(
            "app.crud.experts.get_expert",
            new_callable=AsyncMock,
            return_value=mock_expert,
        )
        mocker.patch(
            "app.crud.experts.get_subscription",
            new_callable=AsyncMock,
            return_value=mock_subscription,
        )
        
        service = ExpertService(mock_db)
        result = await service.check_is_followed(expert_id, regular_user_id, regular_user_role)
        
        assert result["is_followed"] is True

    @pytest.mark.asyncio
    async def test_check_is_followed_false(self, mocker, regular_user_id, regular_user_role):
        """测试检查未关注"""
        mock_db = mocker.Mock()
        expert_id = uuid.uuid4()
        
        mock_expert = create_mock_expert(expert_id=expert_id, is_active=True)
        mocker.patch(
            "app.crud.experts.get_expert",
            new_callable=AsyncMock,
            return_value=mock_expert,
        )
        mocker.patch(
            "app.crud.experts.get_subscription",
            new_callable=AsyncMock,
            return_value=None,
        )
        
        service = ExpertService(mock_db)
        result = await service.check_is_followed(expert_id, regular_user_id, regular_user_role)
        
        assert result["is_followed"] is False


# ==================== 场次专家关联Service测试 ====================

class TestExpertServiceSessionExperts:
    """场次专家关联Service测试"""

    @pytest.mark.asyncio
    async def test_set_session_experts_success(self, mocker, admin_user_id, admin_user_role):
        """测试设置场次专家列表成功"""
        mock_db = mocker.Mock()
        session_id = uuid.uuid4()
        expert_id1 = uuid.uuid4()
        expert_id2 = uuid.uuid4()
        
        # 准备测试数据
        expert_data_list = [
            {"expert_id": expert_id1, "role": "主讲", "sort_order": 1},
            {"expert_id": expert_id2, "role": "嘉宾", "sort_order": 2}
        ]
        
        # 准备Mock数据
        mock_expert1 = create_mock_expert(expert_id=expert_id1)
        mock_expert2 = create_mock_expert(expert_id=expert_id2)
        mock_session_experts = [
            create_mock_session_expert(expert_id=expert_id1, role=SessionExpertRole.MAIN_SPEAKER),
            create_mock_session_expert(expert_id=expert_id2, role=SessionExpertRole.GUEST)
        ]
        
        # Mock CRUD函数
        mock_get_expert1 = mocker.patch(
            "app.crud.experts.get_expert",
            new_callable=AsyncMock,
            side_effect=[mock_expert1, mock_expert2]
        )
        mock_set_session_experts = mocker.patch(
            "app.crud.experts.set_session_experts",
            new_callable=AsyncMock,
            return_value=mock_session_experts
        )
        mock_commit = mocker.patch.object(mock_db, "commit", new_callable=AsyncMock)
        
        # 调用Service
        service = ExpertService(mock_db)
        result = await service.set_session_experts(
            session_id, expert_data_list, admin_user_id, admin_user_role
        )
        
        # 验证
        assert len(result) == 2
        mock_commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_session_experts_expert_not_found(
            self, mocker, admin_user_id, admin_user_role
    ):
        """测试设置场次专家列表失败（专家不存在）"""
        mock_db = AsyncMock()
        session_id = uuid.uuid4()
        expert_id = uuid.uuid4()

        expert_data_list = [
            {"expert_id": expert_id, "role": "主讲", "sort_order": 1}
        ]

        mock_get_expert = mocker.patch(
            "app.crud.experts.get_expert",
            new_callable=AsyncMock,
            return_value=None
        )

        service = ExpertService(mock_db)
        with pytest.raises(InvalidParameterException) as exc_info:
            await service.set_session_experts(
                session_id, expert_data_list, admin_user_id, admin_user_role
            )
        assert "专家不存在" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_set_session_experts_invalid_role(
        self, mocker, admin_user_id, admin_user_role
    ):
        """测试设置场次专家列表失败（无效角色）"""
        mock_db = mocker.Mock()
        session_id = uuid.uuid4()
        expert_id = uuid.uuid4()
        
        # 准备测试数据（无效角色）
        expert_data_list = [
            {"expert_id": expert_id, "role": "无效角色", "sort_order": 1}
        ]
        
        # 准备Mock数据
        mock_expert = create_mock_expert(expert_id=expert_id)
        
        # Mock CRUD函数
        mock_get_expert = mocker.patch(
            "app.crud.experts.get_expert",
            new_callable=AsyncMock,
            return_value=mock_expert
        )
        
        # 调用Service（应该抛出InvalidParameterException）
        service = ExpertService(mock_db)
        with pytest.raises(InvalidParameterException):
            await service.set_session_experts(
                session_id, expert_data_list, admin_user_id, admin_user_role
            )

    @pytest.mark.asyncio
    async def test_set_session_experts_no_permission(
        self, mocker, regular_user_id, regular_user_role
    ):
        """测试设置场次专家列表无权限（非房主 REGULAR）"""
        mock_db = AsyncMock()
        session_id = uuid.uuid4()
        other_owner_id = uuid.uuid4()
        mock_room = Mock()
        mock_room.user_id = other_owner_id
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_room
        mock_db.execute = AsyncMock(return_value=mock_result)
        expert_data_list = []

        service = ExpertService(mock_db)
        with pytest.raises(PermissionDeniedException):
            await service.set_session_experts(
                session_id, expert_data_list, regular_user_id, regular_user_role
            )

    @pytest.mark.asyncio
    async def test_set_session_experts_owner_success(
        self, mocker, regular_user_id, regular_user_role
    ):
        """REGULAR 房主可为场次设置专家（支持联动，不限本人专家）"""
        mock_db = AsyncMock()
        session_id = uuid.uuid4()
        expert_id1 = uuid.uuid4()
        expert_id2 = uuid.uuid4()
        expert_data_list = [
            {"expert_id": expert_id1, "role": "主讲", "sort_order": 1},
            {"expert_id": expert_id2, "role": "嘉宾", "sort_order": 2},
        ]
        mock_room = Mock()
        mock_room.user_id = regular_user_id
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_room
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.commit = AsyncMock()

        mock_expert1 = create_mock_expert(expert_id=expert_id1)
        mock_expert2 = create_mock_expert(expert_id=expert_id2)
        mocker.patch(
            "app.crud.experts.get_expert",
            new_callable=AsyncMock,
            side_effect=[mock_expert1, mock_expert2],
        )
        mocker.patch(
            "app.crud.experts.set_session_experts",
            new_callable=AsyncMock,
            return_value=[],
        )

        service = ExpertService(mock_db)
        result = await service.set_session_experts(
            session_id, expert_data_list, regular_user_id, regular_user_role
        )
        assert result["session_id"] == str(session_id)
        assert len(result["experts"]) == 2

    @pytest.mark.asyncio
    async def test_set_session_experts_session_not_found(
        self, mocker, regular_user_id, regular_user_role
    ):
        """REGULAR 关联不存在场次 → NotFoundException"""
        mock_db = AsyncMock()
        session_id = uuid.uuid4()
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        service = ExpertService(mock_db)
        with pytest.raises(NotFoundException):
            await service.set_session_experts(
                session_id, [], regular_user_id, regular_user_role
            )

    @pytest.mark.asyncio
    async def test_get_session_experts(self, mocker):
        """测试获取场次专家列表"""
        mock_db = mocker.Mock()
        session_id = uuid.uuid4()
        
        # 准备Mock数据
        mock_session_experts = [
            create_mock_session_expert(),
            create_mock_session_expert()
        ]
        
        # Mock CRUD函数
        mock_get_session_experts = mocker.patch(
            "app.crud.experts.get_session_experts",
            new_callable=AsyncMock,
            return_value=mock_session_experts
        )
        
        # 调用Service
        service = ExpertService(mock_db)
        result = await service.get_session_experts(session_id, role=None, current_user_id=None, role_user=None)
        
        # 验证
        assert len(result) == 2
        mock_get_session_experts.assert_called_once()


# ==================== 增量测试：is_active、check_is_followed、batch_import、set_session_experts ====================

@pytest.mark.asyncio
async def test_check_expert_visibility_inactive_regular_user_404(mocker):
    """增量：已下架专家（is_active=False）对普通用户不可见，抛出 NotFound"""
    service = ExpertService(mocker.Mock())
    expert = create_mock_expert(is_active=False)
    with pytest.raises(NotFoundException) as exc_info:
        service._check_expert_visibility(expert, uuid.uuid4(), "REGULAR")
    assert "专家不存在" in str(exc_info.value)


@pytest.mark.asyncio
async def test_check_expert_visibility_inactive_admin_visible(mocker):
    """增量：已下架专家对 Admin 可见"""
    service = ExpertService(mocker.Mock())
    expert = create_mock_expert(is_active=False)
    try:
        service._check_expert_visibility(expert, uuid.uuid4(), "ADMIN")
    except NotFoundException:
        pytest.fail("Admin 应能看到已下架专家")


@pytest.mark.asyncio
async def test_get_experts_list_with_is_active_filter(mocker, admin_user_id, admin_user_role):
    """增量：get_experts_list 支持 is_active 参数"""
    mock_db = AsyncMock()
    mock_experts = [create_mock_expert(name="专家1"), create_mock_expert(name="专家2")]
    mock_get_multi = mocker.patch(
        "app.crud.experts.get_experts_multi_and_total",
        new_callable=AsyncMock,
        return_value=(mock_experts, 2),
    )
    service = ExpertService(mock_db)
    result = await service.get_experts_list(
        page=1, size=10, name=None, is_featured=None, is_active=True, hospital=None,
        sort="created_at:desc", current_user_id=admin_user_id, role=admin_user_role,
    )
    assert result["total"] == 2
    assert len(result["items"]) == 2
    mock_get_multi.assert_called_once()
    call_args = mock_get_multi.call_args[0]
    assert len(call_args) >= 6
    assert call_args[5] is True


@pytest.mark.asyncio
async def test_check_is_followed_inactive_expert_404(mocker, regular_user_id, regular_user_role):
    """增量：check_is_followed 对已下架专家（非 Admin）返回 404"""
    mock_db = mocker.Mock()
    expert_id = uuid.uuid4()
    mock_expert = create_mock_expert(expert_id=expert_id, is_active=False)
    mocker.patch(
        "app.crud.experts.get_expert",
        new_callable=AsyncMock,
        return_value=mock_expert,
    )
    service = ExpertService(mock_db)
    with pytest.raises(NotFoundException) as exc_info:
        await service.check_is_followed(expert_id, regular_user_id, regular_user_role)
    assert "专家不存在" in str(exc_info.value)


@pytest.mark.asyncio
async def test_set_session_experts_rejects_inactive_expert(mocker, admin_user_id, admin_user_role):
    """增量：set_session_experts 拒绝 is_active=False 的专家，抛出 InvalidParameterException"""
    mock_db = AsyncMock()
    session_id = uuid.uuid4()
    expert_id = uuid.uuid4()
    mock_expert = create_mock_expert(expert_id=expert_id, is_active=False)
    mocker.patch(
        "app.crud.experts.get_expert",
        new_callable=AsyncMock,
        return_value=mock_expert,
    )
    expert_data_list = [{"expert_id": expert_id, "role": "主讲", "sort_order": 1}]
    service = ExpertService(mock_db)
    with pytest.raises(InvalidParameterException) as exc_info:
        await service.set_session_experts(
            session_id, expert_data_list, admin_user_id, admin_user_role
        )
    assert "仅允许启用状态的专家关联场次" in str(exc_info.value) or "启用" in str(exc_info.value)


@pytest.mark.asyncio
async def test_batch_import_experts_from_csv_success(mocker, admin_user_id, admin_user_role):
    """增量：batch_import_experts_from_csv 合法 CSV 全成功返回正确结构"""
    mock_db = AsyncMock()
    csv_content = b"name,title,hospital\nTest Expert,Dr,Beijing"
    mock_expert = create_mock_expert(name="测试专家")
    mocker.patch(
        "app.crud.experts.create_expert",
        new_callable=AsyncMock,
        return_value=mock_expert,
    )
    mocker.patch(
        "app.crud.experts.get_experts_multi_and_total",
        new_callable=AsyncMock,
        return_value=([], 0),
    )
    mocker.patch.object(mock_db, "commit", new_callable=AsyncMock)
    service = ExpertService(mock_db)
    result = await service.batch_import_experts_from_csv(
        file_content=csv_content, skip_duplicates=False, role=admin_user_role
    )
    assert "total" in result
    assert "success" in result
    assert "failed" in result
    assert "skipped" in result
    assert "created_expert_ids" in result
    assert "failed_rows" in result
    assert "skipped_rows" in result
    assert "processing_time" in result
    assert result["total"] >= 1
    assert result["success"] >= 1


@pytest.mark.asyncio
async def test_batch_import_experts_from_csv_permission_denied(mocker):
    """增量：非 Admin 调用 batch_import_experts_from_csv 抛出 PermissionDeniedException"""
    mock_db = mocker.Mock()
    service = ExpertService(mock_db)
    with pytest.raises(PermissionDeniedException):
        await service.batch_import_experts_from_csv(
            file_content=b"name\nTest", skip_duplicates=False, role="REGULAR"
        )
