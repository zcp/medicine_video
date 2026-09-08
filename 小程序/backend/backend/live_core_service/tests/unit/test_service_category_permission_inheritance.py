"""
LiveCore Service - Category Permission Inheritance Unit Tests

本模块包含分类权限继承的专项测试。
测试范围：分类继承专题权限（通过TopicService.get_category_list）

测试场景：
- Published专题的分类列表：匿名用户可访问
- Draft专题的分类列表：匿名用户不可访问（继承专题不可见性）
- Owner可访问Draft专题的分类
- Admin可访问Draft专题的分类
"""

import pytest
import uuid

from app.services.topic_service import TopicService
from app.models.topic import TopicStatus
from app.exceptions import TopicNotFoundException


class TestCategoryPermissionInheritance:
    """分类权限继承专项测试"""
    
    @pytest.mark.asyncio
    async def test_category_inherits_published_topic_visibility_for_anonymous(
        self,
        db_session,
        regular_user_id: uuid.UUID
    ):
        """测试：分类继承Published专题的可见性（匿名用户）"""
        async for db in db_session:
            # ===== Arrange (准备) =====
            # 创建Published专题
            from app.crud import topic as crud_topic
            from app.schemas.topic import TopicCreate
            
            topic_service = TopicService(db=db)
            topic_in = TopicCreate(
                title=f"Published Topic {uuid.uuid4().hex[:6]}",
                description="Test Description",
                status="published"
            )
            topic = await crud_topic.create(db, obj_in=topic_in, user_id=regular_user_id)
            await db.commit()
            await db.refresh(topic)
            
            # ===== Act (执行) =====
            # 匿名用户访问该专题的分类列表
            categories, total = await topic_service.get_category_list(
                topic_id=topic.id,
                page=1,
                size=10,
                user_id=None,  # 匿名用户
                role=None
            )
            
            # ===== Assert (断言) =====
            # 应该成功返回（继承专题的可见性）
            assert total >= 0
            assert isinstance(categories, list)
    
    @pytest.mark.asyncio
    async def test_category_inherits_draft_topic_invisibility_for_anonymous_raises_404(
        self,
        db_session,
        regular_user_id: uuid.UUID
    ):
        """测试：分类继承Draft专题的不可见性（匿名用户）"""
        async for db in db_session:
            # ===== Arrange (准备) =====
            # 创建Draft专题
            from app.crud import topic as crud_topic
            from app.schemas.topic import TopicCreate
            
            topic_service = TopicService(db=db)
            topic_in = TopicCreate(
                title=f"Draft Topic {uuid.uuid4().hex[:6]}",
                description="Test Description",
                status="draft"
            )
            topic = await crud_topic.create(db, obj_in=topic_in, user_id=regular_user_id)
            await db.commit()
            await db.refresh(topic)
            
            # ===== Act & Assert (执行 & 断言) =====
            # 匿名用户访问该专题的分类列表应抛出404
            with pytest.raises(TopicNotFoundException):
                await topic_service.get_category_list(
                    topic_id=topic.id,
                    page=1,
                    size=10,
                    user_id=None,  # 匿名用户
                    role=None
                )
    
    @pytest.mark.asyncio
    async def test_category_inherits_draft_topic_visibility_for_owner(
        self,
        db_session,
        regular_user_id: uuid.UUID,
        regular_user_role: str
    ):
        """测试：Owner可访问Draft专题的分类"""
        async for db in db_session:
            # ===== Arrange (准备) =====
            # 创建Draft专题（属于regular_user_id）
            from app.crud import topic as crud_topic
            from app.schemas.topic import TopicCreate
            
            topic_service = TopicService(db=db)
            topic_in = TopicCreate(
                title=f"Draft Topic {uuid.uuid4().hex[:6]}",
                description="Test Description",
                status="draft"
            )
            topic = await crud_topic.create(db, obj_in=topic_in, user_id=regular_user_id)
            await db.commit()
            await db.refresh(topic)
            
            # ===== Act (执行) =====
            # Owner访问该专题的分类列表
            categories, total = await topic_service.get_category_list(
                topic_id=topic.id,
                page=1,
                size=10,
                user_id=regular_user_id,  # Owner
                role=regular_user_role
            )
            
            # ===== Assert (断言) =====
            # 应该成功返回（Owner可以访问）
            assert total >= 0
            assert isinstance(categories, list)
    
    @pytest.mark.asyncio
    async def test_category_inherits_draft_topic_visibility_for_admin(
        self,
        db_session,
        regular_user_id: uuid.UUID,
        admin_user_id: uuid.UUID,
        admin_user_role: str
    ):
        """测试：Admin可访问Draft专题的分类"""
        async for db in db_session:
            # ===== Arrange (准备) =====
            # 创建Draft专题（属于regular_user_id，不是admin_user_id）
            from app.crud import topic as crud_topic
            from app.schemas.topic import TopicCreate
            
            topic_service = TopicService(db=db)
            topic_in = TopicCreate(
                title=f"Draft Topic {uuid.uuid4().hex[:6]}",
                description="Test Description",
                status="draft"
            )
            topic = await crud_topic.create(db, obj_in=topic_in, user_id=regular_user_id)
            await db.commit()
            await db.refresh(topic)
            
            # ===== Act (执行) =====
            # Admin访问该专题的分类列表（即使不是Owner）
            categories, total = await topic_service.get_category_list(
                topic_id=topic.id,
                page=1,
                size=10,
                user_id=admin_user_id,  # Admin（不是Owner）
                role=admin_user_role
            )
            
            # ===== Assert (断言) =====
            # 应该成功返回（Admin有上帝视角）
            assert total >= 0
            assert isinstance(categories, list)

