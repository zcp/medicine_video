"""
LiveCore Service - Topic Permission Guards Unit Tests

本模块包含专题权限守卫函数的专项测试。
测试范围：_check_topic_visibility、_check_write_permission

测试场景：
- 匿名用户、Owner、非Owner、Admin
- Published、Draft、Archived状态
"""

import pytest
import uuid
from unittest.mock import MagicMock

from app.services.topic_service import TopicService
from app.models.topic import TopicStatus
from app.exceptions import TopicNotFoundException, PermissionDeniedException


class TestTopicPermissionGuards:
    """专题权限守卫函数专项测试"""
    
    # ==================== _check_topic_visibility 测试 ====================
    
    @pytest.mark.asyncio
    async def test_check_topic_visibility_published_anonymous(self):
        """测试：Published专题，匿名用户可访问"""
        # ===== Arrange (准备) =====
        topic_service = TopicService(db=MagicMock())
        mock_topic = MagicMock()
        mock_topic.id = uuid.uuid4()
        mock_topic.status = TopicStatus.PUBLISHED
        mock_topic.user_id = uuid.uuid4()
        
        # ===== Act & Assert (执行 & 断言) =====
        # 应该不抛出异常
        topic_service._check_topic_visibility(
            mock_topic,
            user_id=None,
            role=None
        )
    
    @pytest.mark.asyncio
    async def test_check_topic_visibility_draft_anonymous_raises_404(self):
        """测试：Draft专题，匿名用户应抛出404"""
        # ===== Arrange (准备) =====
        topic_service = TopicService(db=MagicMock())
        mock_topic = MagicMock()
        mock_topic.id = uuid.uuid4()
        mock_topic.status = TopicStatus.DRAFT
        mock_topic.user_id = uuid.uuid4()
        
        # ===== Act & Assert (执行 & 断言) =====
        with pytest.raises(TopicNotFoundException):
            topic_service._check_topic_visibility(
                mock_topic,
                user_id=None,
                role=None
            )
    
    @pytest.mark.asyncio
    async def test_check_topic_visibility_draft_owner_success(
        self,
        regular_user_id: uuid.UUID
    ):
        """测试：Draft专题，Owner可访问"""
        # ===== Arrange (准备) =====
        topic_service = TopicService(db=MagicMock())
        mock_topic = MagicMock()
        mock_topic.id = uuid.uuid4()
        mock_topic.status = TopicStatus.DRAFT
        mock_topic.user_id = regular_user_id
        
        # ===== Act & Assert (执行 & 断言) =====
        # 应该不抛出异常
        topic_service._check_topic_visibility(
            mock_topic,
            user_id=regular_user_id,
            role="REGULAR"
        )
    
    @pytest.mark.asyncio
    async def test_check_topic_visibility_draft_non_owner_raises_404(
        self,
        regular_user_id: uuid.UUID,
        another_user_id: uuid.UUID
    ):
        """测试：Draft专题，非Owner抛出404"""
        # ===== Arrange (准备) =====
        topic_service = TopicService(db=MagicMock())
        mock_topic = MagicMock()
        mock_topic.id = uuid.uuid4()
        mock_topic.status = TopicStatus.DRAFT
        mock_topic.user_id = another_user_id  # 属于另一个用户
        
        # ===== Act & Assert (执行 & 断言) =====
        with pytest.raises(TopicNotFoundException):
            topic_service._check_topic_visibility(
                mock_topic,
                user_id=regular_user_id,  # 不是Owner
                role="REGULAR"
            )
    
    @pytest.mark.asyncio
    async def test_check_topic_visibility_draft_admin_success(
        self,
        admin_user_id: uuid.UUID
    ):
        """测试：Draft专题，Admin可访问"""
        # ===== Arrange (准备) =====
        topic_service = TopicService(db=MagicMock())
        another_user_id = uuid.uuid4()  # 非Admin的专题
        mock_topic = MagicMock()
        mock_topic.id = uuid.uuid4()
        mock_topic.status = TopicStatus.DRAFT
        mock_topic.user_id = another_user_id
        
        # ===== Act & Assert (执行 & 断言) =====
        # 应该不抛出异常（Admin有上帝视角）
        topic_service._check_topic_visibility(
            mock_topic,
            user_id=admin_user_id,
            role="ADMIN"
        )
    
    @pytest.mark.asyncio
    async def test_check_topic_visibility_archived_anonymous_raises_404(self):
        """测试：Archived专题，匿名用户抛出404"""
        # ===== Arrange (准备) =====
        topic_service = TopicService(db=MagicMock())
        mock_topic = MagicMock()
        mock_topic.id = uuid.uuid4()
        mock_topic.status = TopicStatus.ARCHIVED
        mock_topic.user_id = uuid.uuid4()
        
        # ===== Act & Assert (执行 & 断言) =====
        with pytest.raises(TopicNotFoundException):
            topic_service._check_topic_visibility(
                mock_topic,
                user_id=None,
                role=None
            )
    
    @pytest.mark.asyncio
    async def test_check_topic_visibility_archived_owner_success(
        self,
        regular_user_id: uuid.UUID
    ):
        """测试：Archived专题，Owner可访问"""
        # ===== Arrange (准备) =====
        topic_service = TopicService(db=MagicMock())
        mock_topic = MagicMock()
        mock_topic.id = uuid.uuid4()
        mock_topic.status = TopicStatus.ARCHIVED
        mock_topic.user_id = regular_user_id
        
        # ===== Act & Assert (执行 & 断言) =====
        # 应该不抛出异常
        topic_service._check_topic_visibility(
            mock_topic,
            user_id=regular_user_id,
            role="REGULAR"
        )
    
    # ==================== _check_write_permission 测试 ====================
    
    @pytest.mark.asyncio
    async def test_check_write_permission_owner_success(
        self,
        regular_user_id: uuid.UUID
    ):
        """测试：Owner有写权限"""
        # ===== Arrange (准备) =====
        topic_service = TopicService(db=MagicMock())
        mock_topic = MagicMock()
        mock_topic.id = uuid.uuid4()
        mock_topic.user_id = regular_user_id
        
        # ===== Act & Assert (执行 & 断言) =====
        # 应该不抛出异常
        topic_service._check_write_permission(
            mock_topic,
            user_id=regular_user_id,
            role="REGULAR"
        )
    
    @pytest.mark.asyncio
    async def test_check_write_permission_non_owner_raises_403(
        self,
        regular_user_id: uuid.UUID,
        another_user_id: uuid.UUID
    ):
        """测试：非Owner写操作应抛出403"""
        # ===== Arrange (准备) =====
        topic_service = TopicService(db=MagicMock())
        mock_topic = MagicMock()
        mock_topic.id = uuid.uuid4()
        mock_topic.user_id = another_user_id  # 属于另一个用户
        
        # ===== Act & Assert (执行 & 断言) =====
        with pytest.raises(PermissionDeniedException):
            topic_service._check_write_permission(
                mock_topic,
                user_id=regular_user_id,  # 不是Owner
                role="REGULAR"
            )
    
    @pytest.mark.asyncio
    async def test_check_write_permission_admin_success(
        self,
        admin_user_id: uuid.UUID
    ):
        """测试：Admin有写权限（即使不是Owner）"""
        # ===== Arrange (准备) =====
        topic_service = TopicService(db=MagicMock())
        another_user_id = uuid.uuid4()  # 非Admin的专题
        mock_topic = MagicMock()
        mock_topic.id = uuid.uuid4()
        mock_topic.user_id = another_user_id
        
        # ===== Act & Assert (执行 & 断言) =====
        # 应该不抛出异常（Admin有上帝视角）
        topic_service._check_write_permission(
            mock_topic,
            user_id=admin_user_id,
            role="ADMIN"
        )

