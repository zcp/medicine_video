"""
LiveCore Service - Topic Search Feature Incremental Tests (CRUD Layer)

This module contains incremental tests for the new search functionality
(title and topic_id filters) added to the topic list CRUD operations.
"""

import uuid
import pytest
from typing import List, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from faker import Faker

# 项目内导入（从实际代码中读取）
from app.crud import topic as crud_topic
from app.models.topic import Topic, TopicStatus
from app.schemas.topic import TopicCreate

# 初始化 Faker
fake = Faker()


# ==================== 辅助函数 (Helper Functions) ====================

async def create_test_topic(
    db: AsyncSession, 
    user_id: uuid.UUID = None,
    title: str = None,
    status: TopicStatus = TopicStatus.PUBLISHED
) -> Topic:
    """创建测试专题的辅助函数"""
    if user_id is None:
        user_id = uuid.uuid4()
    
    if title is None:
        title = f"{fake.catch_phrase()}_{uuid.uuid4().hex[:6]}"
    
    topic_in = TopicCreate(
        title=title,
        description=fake.text(max_nb_chars=100),
        status=status
    )
    
    return await crud_topic.create(db, topic_in, user_id)


# ==================== CRUD层查询功能测试 ====================

@pytest.mark.asyncio
async def test_get_multi_with_title_filter_fuzzy_match(db_session):
    """
    测试CRUD层title模糊匹配功能
    
    验证点:
    1. 返回的专题列表只包含title中包含关键词的专题
    2. 模糊匹配不区分大小写（ilike）
    3. total计数正确
    4. 不包含title中不包含关键词的专题
    """
    async for db in db_session:
        # Arrange: 创建多个专题，部分title包含关键词，部分不包含
        user_id = uuid.uuid4()
        search_keyword = f"search_test_{uuid.uuid4().hex[:6]}"
        
        # 创建包含关键词的专题（不同大小写）
        topic1 = await create_test_topic(
            db, 
            user_id=user_id, 
            title=f"{search_keyword}_Title1",
            status=TopicStatus.PUBLISHED
        )
        topic2 = await create_test_topic(
            db, 
            user_id=user_id, 
            title=f"Title2_{search_keyword.upper()}_Suffix",
            status=TopicStatus.PUBLISHED
        )
        # 创建不包含关键词的专题
        topic3 = await create_test_topic(
            db, 
            user_id=user_id, 
            title=f"Other_Title_{uuid.uuid4().hex[:6]}",
            status=TopicStatus.PUBLISHED
        )
        await db.commit()
        
        # Act: 使用title筛选
        topics, total = await crud_topic.get_multi_and_total(
            db,
            skip=0,
            limit=10,
            title=search_keyword,
            current_user_id=None,
            current_user_role=None
        )
        
        # Assert
        assert topics is not None, "返回的专题列表不应为None"
        assert isinstance(topics, list), "返回的专题列表应为list类型"
        assert total >= 2, f"期望至少返回2个专题，实际返回 {total} 个"
        
        # 验证所有返回的专题title都包含关键词（不区分大小写）
        topic_ids = [topic.id for topic in topics]
        assert topic1.id in topic_ids, f"期望topic1（title包含{search_keyword}）在结果中"
        assert topic2.id in topic_ids, f"期望topic2（title包含{search_keyword.upper()}）在结果中"
        assert topic3.id not in topic_ids, f"期望topic3（title不包含{search_keyword}）不在结果中"
        
        # 验证total计数正确
        assert total == 2, f"期望total为2，实际为 {total}"


@pytest.mark.asyncio
async def test_get_multi_with_topic_id_exact_match(db_session):
    """
    测试CRUD层topic_id精确匹配功能
    
    验证点:
    1. 返回的专题列表只包含指定ID的专题
    2. 列表长度为1
    3. 返回的专题的ID与查询的topic_id一致
    """
    async for db in db_session:
        # Arrange: 创建多个专题
        user_id = uuid.uuid4()
        topic1 = await create_test_topic(db, user_id=user_id, status=TopicStatus.PUBLISHED)
        topic2 = await create_test_topic(db, user_id=user_id, status=TopicStatus.PUBLISHED)
        topic3 = await create_test_topic(db, user_id=user_id, status=TopicStatus.PUBLISHED)
        await db.commit()
        
        specific_topic_id = topic2.id
        
        # Act: 使用topic_id精确匹配
        topics, total = await crud_topic.get_multi_and_total(
            db,
            skip=0,
            limit=10,
            topic_id=specific_topic_id,
            current_user_id=None,
            current_user_role=None
        )
        
        # Assert
        assert topics is not None, "返回的专题列表不应为None"
        assert isinstance(topics, list), "返回的专题列表应为list类型"
        assert len(topics) == 1, f"期望返回1个专题，实际返回 {len(topics)} 个"
        assert total == 1, f"期望total为1，实际为 {total}"
        
        # 验证返回的专题ID正确
        assert topics[0].id == specific_topic_id, \
            f"期望返回的专题ID为 {specific_topic_id}，实际为 {topics[0].id}"


@pytest.mark.asyncio
async def test_get_multi_permission_filter_with_title_anonymous(db_session):
    """
    测试匿名用户的权限过滤与title筛选的组合
    
    验证点:
    1. 返回的专题列表只包含status=published的专题
    2. 不包含status=draft或archived的专题（即使title匹配）
    """
    async for db in db_session:
        # Arrange: 创建多个专题，title都包含相同关键词，但status不同
        user_id = uuid.uuid4()
        search_keyword = f"permission_test_{uuid.uuid4().hex[:6]}"
        
        # 创建published专题
        published_topic = await create_test_topic(
            db,
            user_id=user_id,
            title=f"{search_keyword}_Published",
            status=TopicStatus.PUBLISHED
        )
        # 创建draft专题
        draft_topic = await create_test_topic(
            db,
            user_id=user_id,
            title=f"{search_keyword}_Draft",
            status=TopicStatus.DRAFT
        )
        # 创建archived专题
        archived_topic = await create_test_topic(
            db,
            user_id=user_id,
            title=f"{search_keyword}_Archived",
            status=TopicStatus.ARCHIVED
        )
        await db.commit()
        
        # Act: 匿名用户身份调用（current_user_id=None, current_user_role=None）
        topics, total = await crud_topic.get_multi_and_total(
            db,
            skip=0,
            limit=10,
            title=search_keyword,
            current_user_id=None,
            current_user_role=None
        )
        
        # Assert
        assert topics is not None, "返回的专题列表不应为None"
        assert isinstance(topics, list), "返回的专题列表应为list类型"
        assert total == 1, f"匿名用户应该只能看到1个published专题，实际total为 {total}"
        
        topic_ids = [topic.id for topic in topics]
        assert published_topic.id in topic_ids, "应该能看到published专题"
        assert draft_topic.id not in topic_ids, "匿名用户不应该能看到draft专题"
        assert archived_topic.id not in topic_ids, "匿名用户不应该能看到archived专题"
        
        # 验证所有返回的专题status都是published
        for topic in topics:
            assert topic.status == TopicStatus.PUBLISHED, \
                f"匿名用户只能看到published专题，实际status为 {topic.status}"


@pytest.mark.asyncio
async def test_get_multi_permission_filter_with_title_regular_user(db_session):
    """
    测试普通用户的权限过滤与title筛选的组合
    
    验证点:
    1. 返回所有published专题（包括用户A和用户B的）
    2. 返回用户A自己的draft专题
    3. 不返回用户B的draft专题
    """
    async for db in db_session:
        # Arrange: 创建用户A和用户B的专题，title都包含相同关键词
        user_a_id = uuid.uuid4()
        user_b_id = uuid.uuid4()
        search_keyword = f"regular_user_test_{uuid.uuid4().hex[:6]}"
        
        # 用户A的专题
        user_a_published = await create_test_topic(
            db,
            user_id=user_a_id,
            title=f"{search_keyword}_UserA_Published",
            status=TopicStatus.PUBLISHED
        )
        user_a_draft = await create_test_topic(
            db,
            user_id=user_a_id,
            title=f"{search_keyword}_UserA_Draft",
            status=TopicStatus.DRAFT
        )
        
        # 用户B的专题
        user_b_published = await create_test_topic(
            db,
            user_id=user_b_id,
            title=f"{search_keyword}_UserB_Published",
            status=TopicStatus.PUBLISHED
        )
        user_b_draft = await create_test_topic(
            db,
            user_id=user_b_id,
            title=f"{search_keyword}_UserB_Draft",
            status=TopicStatus.DRAFT
        )
        await db.commit()
        
        # Act: 以用户A身份调用（current_user_id=user_a_id, current_user_role="REGULAR"）
        topics, total = await crud_topic.get_multi_and_total(
            db,
            skip=0,
            limit=10,
            title=search_keyword,
            current_user_id=user_a_id,
            current_user_role="REGULAR"
        )
        
        # Assert
        assert topics is not None, "返回的专题列表不应为None"
        assert isinstance(topics, list), "返回的专题列表应为list类型"
        assert total == 3, f"Regular用户应该能看到3个专题（2个published + 1个自己的draft），实际total为 {total}"
        
        topic_ids = [topic.id for topic in topics]
        # 应该能看到所有published专题
        assert user_a_published.id in topic_ids, "应该能看到用户A的published专题"
        assert user_b_published.id in topic_ids, "应该能看到用户B的published专题"
        # 应该能看到自己的draft专题
        assert user_a_draft.id in topic_ids, "应该能看到用户A自己的draft专题"
        # 不应该能看到他人的draft专题
        assert user_b_draft.id not in topic_ids, "不应该能看到用户B的draft专题"


@pytest.mark.asyncio
async def test_get_multi_permission_filter_with_title_admin(db_session):
    """
    测试管理员用户的权限过滤与title筛选的组合
    
    验证点:
    1. 返回所有匹配title的专题，无论status如何
    2. 权限过滤未限制结果
    """
    async for db in db_session:
        # Arrange: 创建多个专题，title都包含相同关键词，status包括published、draft、archived
        user_id = uuid.uuid4()
        search_keyword = f"admin_test_{uuid.uuid4().hex[:6]}"
        
        published_topic = await create_test_topic(
            db,
            user_id=user_id,
            title=f"{search_keyword}_Published",
            status=TopicStatus.PUBLISHED
        )
        draft_topic = await create_test_topic(
            db,
            user_id=user_id,
            title=f"{search_keyword}_Draft",
            status=TopicStatus.DRAFT
        )
        archived_topic = await create_test_topic(
            db,
            user_id=user_id,
            title=f"{search_keyword}_Archived",
            status=TopicStatus.ARCHIVED
        )
        await db.commit()
        
        # Act: 以管理员身份调用（current_user_role="ADMIN"）
        topics, total = await crud_topic.get_multi_and_total(
            db,
            skip=0,
            limit=10,
            title=search_keyword,
            current_user_id=None,
            current_user_role="ADMIN"
        )
        
        # Assert
        assert topics is not None, "返回的专题列表不应为None"
        assert isinstance(topics, list), "返回的专题列表应为list类型"
        assert total == 3, f"Admin用户应该能看到所有3个专题，实际total为 {total}"
        
        topic_ids = [topic.id for topic in topics]
        assert published_topic.id in topic_ids, "Admin应该能看到published专题"
        assert draft_topic.id in topic_ids, "Admin应该能看到draft专题"
        assert archived_topic.id in topic_ids, "Admin应该能看到archived专题"

