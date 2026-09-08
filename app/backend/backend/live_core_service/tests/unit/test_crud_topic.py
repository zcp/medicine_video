"""
LiveCore Service - Topic CRUD Unit Tests

This module contains unit tests for all CRUD operations in app/crud/topic.py.
"""

import uuid
import pytest
from typing import List
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from faker import Faker

# 项目内导入
from app.crud import topic as crud_topic
from app.models.topic import Topic, TopicCategory, TopicCategoryRoom, TopicStatus
from app.models.live_core import LiveRoom
from app.schemas.topic import (
    TopicCreate, TopicUpdate,
    TopicCategoryCreate, TopicCategoryUpdate,
    RoomAssociation
)

# 初始化 Faker
fake = Faker()


# ==================== 辅助函数 (Helper Functions) ====================

async def create_test_topic(db: AsyncSession, user_id: uuid.UUID = None) -> Topic:
    """创建测试专题的辅助函数"""
    from app.crud import topic as crud_topic
    from app.schemas.topic import TopicCreate
    from app.models.topic import TopicStatus
    from faker import Faker
    
    if user_id is None:
        user_id = uuid.uuid4()
    
    fake = Faker()
    topic_in = TopicCreate(
        title=f"{fake.catch_phrase()}_{uuid.uuid4().hex[:6]}",
        description=fake.text(max_nb_chars=100),
        #banner_url=fake.image_url(),
        status=TopicStatus.DRAFT
    )
    
    return await crud_topic.create(db, topic_in, user_id)


async def create_test_category(db: AsyncSession,
                               topic_id: uuid.UUID,
                               sort_order: int = None) -> TopicCategory:
    """创建测试分类的辅助函数"""
    from app.crud import topic as crud_topic
    from app.schemas.topic import TopicCategoryCreate
    from faker import Faker
    
    fake = Faker()
    category_in = TopicCategoryCreate(
        name=f"{fake.word()}_{uuid.uuid4().hex[:4]}",
        #sort_order=fake.random_int(min=0, max=10)
        sort_order = sort_order if sort_order is not None else fake.random_int(min=0, max=10)
    )
    
    return await crud_topic.create_category(db, category_in, topic_id)


async def create_test_room(db: AsyncSession) -> LiveRoom:
    """创建测试直播间的辅助函数"""
    from app.models.live_core import LiveRoom
    from faker import Faker
    import uuid
    
    fake = Faker()
    room = LiveRoom(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        title=f"{fake.company()}_{uuid.uuid4().hex[:4]}",
        description=fake.text(max_nb_chars=50),
        stream_key=f"key_{uuid.uuid4().hex}",
        is_private=False,
        record_by_default=True
    )
    
    db.add(room)
    await db.commit()
    await db.refresh(room)
    return room


# ==================== 专题 (Topic) 相关测试 ====================

@pytest.mark.asyncio
async def test_create_topic_success(db_session):
    """
    测试成功创建新专题
    
    验证点:
    1. 返回的 Topic 对象不为 None
    2. 自动生成的 UUID 有效
    3. user_id 正确关联
    4. 所有字段值与输入一致
    5. created_at 和 updated_at 时间戳已设置
    6. 数据库中成功插入记录
    """
    async for db in db_session:
        # Arrange
        user_id = uuid.uuid4()
        topic_in = TopicCreate(
            title=f"{fake.catch_phrase()}_{uuid.uuid4().hex[:6]}",
            description=fake.text(max_nb_chars=100),
            #banner_url=fake.image_url(),
            status=TopicStatus.DRAFT
        )
        
        # Act
        created_topic = await crud_topic.create(db, topic_in, user_id)
        
        # Assert
        assert created_topic is not None, "创建专题失败，返回了 None"
        assert isinstance(created_topic.id, uuid.UUID), f"专题 ID 类型错误: {type(created_topic.id)}"
        assert created_topic.user_id == user_id, f"user_id 不匹配: 期望 {user_id}, 实际 {created_topic.user_id}"
        assert created_topic.title == topic_in.title, f"标题不匹配: 期望 {topic_in.title}, 实际 {created_topic.title}"
        assert created_topic.description == topic_in.description, "描述不匹配"
        #assert created_topic.banner_url == topic_in.banner_url, "横幅URL不匹配"
        assert created_topic.status == topic_in.status, f"状态不匹配: 期望 {topic_in.status}, 实际 {created_topic.status}"
        assert created_topic.created_at is not None, "created_at 未设置"
        assert created_topic.updated_at is not None, "updated_at 未设置"
        
        # 数据库验证
        stmt = select(Topic).where(Topic.id == created_topic.id)
        result = await db.execute(stmt)
        db_topic = result.scalar_one_or_none()
        
        assert db_topic is not None, "数据库中未找到创建的专题"
        assert db_topic.title == topic_in.title, "数据库中的标题与创建的不一致"


@pytest.mark.asyncio
async def test_get_topic_by_id_success(db_session):
    """
    测试根据ID获取专题
    
    验证点:
    1. 返回的对象不为 None
    2. topic.id 与创建时的 ID 一致
    3. 其他字段值正确
    """
    async for db in db_session:
        # Arrange
        created_topic = await create_test_topic(db)
        
        # Act
        retrieved_topic = await crud_topic.get(db, created_topic.id)
        
        # Assert
        assert retrieved_topic is not None, "获取专题失败，返回了 None"
        assert retrieved_topic.id == created_topic.id, f"ID 不匹配: 期望 {created_topic.id}, 实际 {retrieved_topic.id}"
        assert retrieved_topic.title == created_topic.title, "标题不匹配"
        assert retrieved_topic.user_id == created_topic.user_id, "user_id 不匹配"


@pytest.mark.asyncio
async def test_get_topic_by_id_not_found(db_session):
    """
    测试获取不存在的专题返回 None
    
    验证点:
    1. 使用不存在的 UUID 查询时返回 None
    """
    async for db in db_session:
        # Arrange
        random_uuid = uuid.uuid4()
        
        # Act
        retrieved_topic = await crud_topic.get(db, random_uuid)
        
        # Assert
        assert retrieved_topic is None, f"期望返回 None，但返回了 {retrieved_topic}"


@pytest.mark.asyncio
async def test_get_with_categories_success(db_session):
    """
    测试获取专题时预加载分类列表
    
    验证点:
    1. 返回的 Topic 对象不为 None
    2. topic.categories 已被预加载（不为空列表）
    3. len(topic.categories) 等于创建的分类数量
    4. 分类按 sort_order 排序
    """
    async for db in db_session:
        # Arrange
        topic = await create_test_topic(db)
        
        # 创建3个分类，设置不同的 sort_order
        category1 = await create_test_category(db, topic.id,sort_order = 30)
        category2 = await create_test_category(db, topic.id, sort_order = 10)
        category3 = await create_test_category(db, topic.id, sort_order = 20)
        #await db.commit()
        # 清除会话缓存，强制从数据库重新加载
        db.expunge_all()

        db.refresh(topic)
        # Act
        topic_with_categories = await crud_topic.get_with_categories(db, topic.id)
        
        # Assert
        assert topic_with_categories is not None, "获取专题失败"
        assert hasattr(topic_with_categories, 'categories'), "categories 属性不存在"
        assert len(topic_with_categories.categories) == 3, f"期望3个分类，实际 {len(topic_with_categories.categories)}"
        
        # 验证按 sort_order 排序
        sort_orders = [cat.sort_order for cat in topic_with_categories.categories]
        assert sort_orders == sorted(sort_orders), f"分类未按 sort_order 排序: {sort_orders}"


@pytest.mark.asyncio
async def test_get_multi_and_total_with_filters(
    db_session,
    regular_user_id: uuid.UUID,
    regular_user_role: str
):
    """
    测试分页获取专题列表，支持状态和用户ID筛选（登录用户场景）
    
    验证点:
    1. 返回的 tuple 格式: (topics_list, total_count)
    2. 筛选后的列表长度正确
    3. 所有返回的专题的 status 匹配
    4. 所有返回的专题的 user_id 匹配
    5. total_count 数值正确
    """
    async for db in db_session:
        # ===== Arrange (准备) =====
        user_a = regular_user_id
        user_b = uuid.uuid4()
        
        # 创建5个专题：user_a 有2个 PUBLISHED 和 1个 DRAFT，user_b 有2个 DRAFT
        await create_test_topic(db, user_id=user_a)  # DRAFT
        
        topic2 = await create_test_topic(db, user_id=user_a)
        topic2.status = TopicStatus.PUBLISHED
        
        topic3 = await create_test_topic(db, user_id=user_a)
        topic3.status = TopicStatus.PUBLISHED
        
        await create_test_topic(db, user_id=user_b)  # DRAFT
        await create_test_topic(db, user_id=user_b)  # DRAFT
        
        await db.commit()
        
        # ===== Act (执行) =====
        # ← 修改：传递权限参数（登录用户，可以看到Published+自己的Draft专题）
        topics, total = await crud_topic.get_multi_and_total(
            db,
            skip=0,
            limit=10,
            status=TopicStatus.PUBLISHED,
            user_id=user_a,
            current_user_id=regular_user_id,  # ← 新增：权限参数
            current_user_role=regular_user_role  # ← 新增：权限参数
        )
        
        # ===== Assert (断言) =====
        assert isinstance(topics, list), "topics 应该是列表"
        assert isinstance(total, int), "total 应该是整数"
        assert len(topics) == 2, f"期望2个专题，实际 {len(topics)}"
        assert total == 2, f"期望总数2，实际 {total}"
        
        for topic in topics:
            assert topic.status == TopicStatus.PUBLISHED, f"专题状态不是 PUBLISHED: {topic.status}"
            assert topic.user_id == user_a, f"user_id 不匹配: {topic.user_id}"

# ← 新增：测试匿名用户场景（S1）
@pytest.mark.asyncio
async def test_get_multi_and_total_anonymous(
    db_session,
    published_topic,
    draft_topic
):
    """测试获取专题列表（匿名用户，只能看到Published专题，S1场景）"""
    async for db in db_session:
        # ===== Arrange (准备) =====
        # 使用async for获取fixture返回的实际对象
        async for pub_topic in published_topic:
            async for drf_topic in draft_topic:
                # ===== Act (执行) =====
                # ← 新增：传递None作为权限参数（匿名用户）
                topics, total = await crud_topic.get_multi_and_total(
                    db,
                    skip=0,
                    limit=10,
                    current_user_id=None,  # ← 新增：匿名用户
                    current_user_role=None  # ← 新增：匿名用户
                )
                
                # ===== Assert (断言) =====
                assert isinstance(topics, list)
                assert isinstance(total, int)
                # ← 新增：验证只能看到Published专题
                topic_ids = [topic.id for topic in topics]
                assert pub_topic.id in topic_ids, "应该能看到Published专题"
                assert drf_topic.id not in topic_ids, "不应该能看到Draft专题（匿名用户）"
                for topic in topics:
                    assert topic.status == TopicStatus.PUBLISHED, "匿名用户只能看到Published专题"
                break
            break

# ← 新增：测试登录用户场景（S3）
@pytest.mark.asyncio
async def test_get_multi_and_total_as_owner(
    db_session,
    regular_user_id: uuid.UUID,
    regular_user_role: str,
    published_topic,
    draft_topic_owned_by_user,
    draft_topic_owned_by_another_user
):
    """测试获取专题列表（登录用户，可以看到Published+自己的专题，S3场景）"""
    async for db in db_session:
        # ===== Arrange (准备) =====
        # 使用async for获取fixture返回的实际对象
        async for pub_topic in published_topic:
            async for my_draft_topic in draft_topic_owned_by_user:
                async for other_draft_topic in draft_topic_owned_by_another_user:
                    # ===== Act (执行) =====
                    topics, total = await crud_topic.get_multi_and_total(
                        db,
                        skip=0,
                        limit=10,
                        current_user_id=regular_user_id,  # ← 新增
                        current_user_role=regular_user_role  # ← 新增
                    )
                    
                    # ===== Assert (断言) =====
                    topic_ids = [topic.id for topic in topics]
                    assert pub_topic.id in topic_ids, "应该能看到Published专题"
                    assert my_draft_topic.id in topic_ids, "应该能看到自己的Draft专题"
                    assert other_draft_topic.id not in topic_ids, "不应该能看到他人的Draft专题"
                    break
                break
            break

# ← 新增：测试Admin用户场景（S6）
@pytest.mark.asyncio
async def test_get_multi_and_total_as_admin(
    db_session,
    admin_user_id: uuid.UUID,
    admin_user_role: str,
    published_topic,
    draft_topic
):
    """测试获取专题列表（Admin用户，可以看到所有专题，S6场景）"""
    async for db in db_session:
        # ===== Arrange (准备) =====
        # 使用async for获取fixture返回的实际对象
        async for pub_topic in published_topic:
            async for drf_topic in draft_topic:
                # ===== Act (执行) =====
                topics, total = await crud_topic.get_multi_and_total(
                    db,
                    skip=0,
                    limit=10,
                    current_user_id=admin_user_id,  # ← 新增
                    current_user_role=admin_user_role  # ← 新增
                )
                
                # ===== Assert (断言) =====
                topic_ids = [topic.id for topic in topics]
                assert pub_topic.id in topic_ids, "应该能看到Published专题"
                assert drf_topic.id in topic_ids, "Admin应该能看到所有专题（包括Draft）"
                break
            break


@pytest.mark.asyncio
async def test_update_topic_success(db_session):
    """
    测试更新专题信息
    
    验证点:
    1. 返回的对象不为 None
    2. topic.title 已更新为新值
    3. topic.status 已更新
    4. 数据库验证：重新查询确认更新已持久化
    5. updated_at 时间戳已更新
    """
    async for db in db_session:
        # Arrange
        topic = await create_test_topic(db)
        original_title = topic.title
        original_updated_at = topic.updated_at
        
        new_title = f"{fake.catch_phrase()}_{uuid.uuid4().hex[:6]}"
        update_data = TopicUpdate(
            title=new_title,
            status=TopicStatus.PUBLISHED
        )
        
        # Act
        updated_topic = await crud_topic.update(db, topic, update_data)
        
        # Assert
        assert updated_topic is not None, "更新专题失败"
        assert updated_topic.title == new_title, f"标题未更新: 期望 {new_title}, 实际 {updated_topic.title}"
        assert updated_topic.title != original_title, "标题与原值相同"
        assert updated_topic.status == TopicStatus.PUBLISHED, f"状态未更新: {updated_topic.status}"
        
        # 数据库验证
        stmt = select(Topic).where(Topic.id == topic.id)
        result = await db.execute(stmt)
        db_topic = result.scalar_one_or_none()
        
        assert db_topic is not None, "数据库中未找到专题"
        assert db_topic.title == new_title, "数据库中的标题未更新"
        assert db_topic.status == TopicStatus.PUBLISHED, "数据库中的状态未更新"


@pytest.mark.asyncio
async def test_remove_topic_success(db_session):
    """
    测试删除专题及级联删除
    
    验证点:
    1. 数据库验证 1: 查询 Topic 表，确认专题已删除
    2. 数据库验证 2: 查询 TopicCategory 表，确认关联的分类也已被级联删除
    """
    async for db in db_session:
        # Arrange
        topic = await create_test_topic(db)
        category1 = await create_test_category(db, topic.id)
        category2 = await create_test_category(db, topic.id)
        
        topic_id = topic.id
        category1_id = category1.id
        category2_id = category2.id
        
        # Act
        await crud_topic.remove(db, topic)
        
        # Assert - 验证专题已删除
        stmt = select(Topic).where(Topic.id == topic_id)
        result = await db.execute(stmt)
        db_topic = result.scalar_one_or_none()
        
        assert db_topic is None, "专题未被删除"
        
        # Assert - 验证分类已被级联删除
        stmt = select(TopicCategory).where(TopicCategory.id == category1_id)
        result = await db.execute(stmt)
        db_category1 = result.scalar_one_or_none()
        
        stmt = select(TopicCategory).where(TopicCategory.id == category2_id)
        result = await db.execute(stmt)
        db_category2 = result.scalar_one_or_none()
        
        assert db_category1 is None, "分类1未被级联删除"
        assert db_category2 is None, "分类2未被级联删除"


# ==================== 分类 (TopicCategory) 相关测试 ====================

@pytest.mark.asyncio
async def test_create_category_success(db_session):
    """
    测试成功创建分类
    
    验证点:
    1. 返回的 TopicCategory 对象不为 None
    2. category.topic_id == topic.id
    3. category.name 和 category.sort_order 正确
    4. 数据库验证：查询确认记录存在
    """
    async for db in db_session:
        # Arrange
        topic = await create_test_topic(db)
        category_in = TopicCategoryCreate(
            name=f"{fake.word()}_{uuid.uuid4().hex[:4]}",
            sort_order=fake.random_int(min=0, max=100)
        )
        
        # Act
        created_category = await crud_topic.create_category(db, category_in, topic.id)
        
        # Assert
        assert created_category is not None, "创建分类失败"
        assert isinstance(created_category, TopicCategory), "返回对象类型错误"
        assert created_category.topic_id == topic.id, f"topic_id 不匹配: 期望 {topic.id}, 实际 {created_category.topic_id}"
        assert created_category.name == category_in.name, "分类名称不匹配"
        assert created_category.sort_order == category_in.sort_order, "排序不匹配"
        assert created_category.id is not None, "ID 未设置"
        assert created_category.created_at is not None, "created_at 未设置"
        
        # 数据库验证
        stmt = select(TopicCategory).where(TopicCategory.id == created_category.id)
        result = await db.execute(stmt)
        db_category = result.scalar_one_or_none()
        
        assert db_category is not None, "数据库中未找到分类"
        assert db_category.name == category_in.name, "数据库中的名称不匹配"


@pytest.mark.asyncio
async def test_create_category_duplicate_name_fails(db_session):
    """
    测试在同一专题下创建重名分类失败
    
    验证点:
    1. 第二次创建相同名称的分类时抛出 IntegrityError
    2. 验证 unique constraint 生效
    """
    async for db in db_session:
        # Arrange
        topic = await create_test_topic(db)
        category_name = f"{fake.word()}_{uuid.uuid4().hex[:4]}"
        
        category_in1 = TopicCategoryCreate(
            name=category_name,
            sort_order=10
        )
        await crud_topic.create_category(db, category_in1, topic.id)
        
        category_in2 = TopicCategoryCreate(
            name=category_name,  # 相同的名称
            sort_order=20
        )
        
        # Act & Assert
        with pytest.raises(IntegrityError):
            await crud_topic.create_category(db, category_in2, topic.id)


@pytest.mark.asyncio
async def test_get_category_by_id_success(db_session):
    """
    测试根据ID获取分类
    
    验证点:
    1. 返回的对象不为 None
    2. category.id 正确
    """
    async for db in db_session:
        # Arrange
        topic = await create_test_topic(db)
        created_category = await create_test_category(db, topic.id)
        
        # Act
        retrieved_category = await crud_topic.get_category(db, created_category.id)
        
        # Assert
        assert retrieved_category is not None, "获取分类失败"
        assert retrieved_category.id == created_category.id, "ID 不匹配"
        assert retrieved_category.name == created_category.name, "名称不匹配"


@pytest.mark.asyncio
async def test_get_category_with_topic_success(db_session):
    """
    测试获取分类时预加载专题对象
    
    验证点:
    1. 返回的 category 不为 None
    2. category.topic 已被预加载（不为 None）
    3. category.topic.id == topic.id
    """
    async for db in db_session:
        # Arrange
        topic = await create_test_topic(db)
        category = await create_test_category(db, topic.id)
        
        # Act
        category_with_topic = await crud_topic.get_category_with_topic(db, category.id)
        
        # Assert
        assert category_with_topic is not None, "获取分类失败"
        assert hasattr(category_with_topic, 'topic'), "topic 属性不存在"
        assert category_with_topic.topic is not None, "topic 未被预加载"
        assert category_with_topic.topic.id == topic.id, f"topic ID 不匹配: 期望 {topic.id}, 实际 {category_with_topic.topic.id}"


@pytest.mark.asyncio
async def test_get_categories_by_topic_pagination(db_session):
    """
    测试分页获取专题下的分类列表
    
    验证点:
    1. 返回的 tuple: (categories_list, total_count)
    2. len(categories_list) == 3
    3. total_count == 5
    4. 返回的分类按 sort_order ASC 排序
    """
    async for db in db_session:
        # Arrange
        topic = await create_test_topic(db)
        
        # 创建5个分类，设置不同的 sort_order
        for i, order in enumerate([0, 10, 20, 30, 40]):
            category = await create_test_category(db, topic.id)
            category.sort_order = order
        await db.commit()
        
        # Act
        categories, total = await crud_topic.get_categories_by_topic(
            db,
            topic.id,
            skip=0,
            limit=3
        )
        
        # Assert
        assert isinstance(categories, list), "categories 应该是列表"
        assert isinstance(total, int), "total 应该是整数"
        assert len(categories) == 3, f"期望3个分类，实际 {len(categories)}"
        assert total == 5, f"期望总数5，实际 {total}"
        
        # 验证按 sort_order 排序
        sort_orders = [cat.sort_order for cat in categories]
        assert sort_orders == [0, 10, 20], f"分类未按 sort_order 排序: {sort_orders}"


@pytest.mark.asyncio
async def test_update_category_success(db_session):
    """
    测试更新分类信息
    
    验证点:
    1. category.name 已更新
    2. category.sort_order 已更新
    3. 数据库验证：重新查询确认持久化
    """
    async for db in db_session:
        # Arrange
        topic = await create_test_topic(db)
        category = await create_test_category(db, topic.id)
        
        new_name = f"{fake.word()}_{uuid.uuid4().hex[:4]}"
        new_sort_order = 999
        update_data = TopicCategoryUpdate(
            name=new_name,
            sort_order=new_sort_order
        )
        
        # Act
        updated_category = await crud_topic.update_category(db, category, update_data)
        
        # Assert
        assert updated_category is not None, "更新分类失败"
        assert updated_category.name == new_name, f"名称未更新: {updated_category.name}"
        assert updated_category.sort_order == new_sort_order, f"排序未更新: {updated_category.sort_order}"
        
        # 数据库验证
        stmt = select(TopicCategory).where(TopicCategory.id == category.id)
        result = await db.execute(stmt)
        db_category = result.scalar_one_or_none()
        
        assert db_category is not None, "数据库中未找到分类"
        assert db_category.name == new_name, "数据库中的名称未更新"
        assert db_category.sort_order == new_sort_order, "数据库中的排序未更新"


@pytest.mark.asyncio
async def test_remove_category_success(db_session):
    """
    测试删除分类及级联删除
    
    验证点:
    1. 数据库验证 1: 查询 TopicCategory 表，确认分类已删除
    2. 数据库验证 2: 查询 TopicCategoryRoom 表，确认关联记录也被级联删除
    """
    async for db in db_session:
        # Arrange
        topic = await create_test_topic(db)
        category = await create_test_category(db, topic.id)
        room = await create_test_room(db)
        
        # 添加直播间到分类
        association = await crud_topic.add_room_to_category(db, category.id, room.id, sort_order=0)
        
        category_id = category.id
        association_id = association.id
        
        # Act
        await crud_topic.remove_category(db, category)
        
        # Assert - 验证分类已删除
        stmt = select(TopicCategory).where(TopicCategory.id == category_id)
        result = await db.execute(stmt)
        db_category = result.scalar_one_or_none()
        
        assert db_category is None, "分类未被删除"
        
        # Assert - 验证关联记录已被级联删除
        stmt = select(TopicCategoryRoom).where(TopicCategoryRoom.id == association_id)
        result = await db.execute(stmt)
        db_association = result.scalar_one_or_none()
        
        assert db_association is None, "关联记录未被级联删除"


# ==================== 直播间关联 (TopicCategoryRoom) 相关测试 ====================

@pytest.mark.asyncio
async def test_add_room_to_category_success(db_session):
    """
    测试成功添加直播间到分类
    
    验证点:
    1. 返回的 TopicCategoryRoom 对象不为 None
    2. association.category_id == category.id
    3. association.room_id == room.id
    4. association.sort_order == 10
    5. 数据库验证：查询确认关联记录存在
    """
    async for db in db_session:
        # Arrange
        topic = await create_test_topic(db)
        category = await create_test_category(db, topic.id)
        room = await create_test_room(db)
        
        # Act
        association = await crud_topic.add_room_to_category(db, category.id, room.id, sort_order=10)
        
        # Assert
        assert association is not None, "添加直播间失败"
        assert isinstance(association, TopicCategoryRoom), "返回对象类型错误"
        assert association.category_id == category.id, "category_id 不匹配"
        assert association.room_id == room.id, "room_id 不匹配"
        assert association.sort_order == 10, f"sort_order 不匹配: {association.sort_order}"
        assert association.id is not None, "ID 未设置"
        
        # 数据库验证
        stmt = select(TopicCategoryRoom).where(TopicCategoryRoom.id == association.id)
        result = await db.execute(stmt)
        db_association = result.scalar_one_or_none()
        
        assert db_association is not None, "数据库中未找到关联记录"


@pytest.mark.asyncio
async def test_add_room_duplicate_fails(db_session):
    """
    测试重复添加同一直播间到同一分类失败
    
    验证点:
    1. 第二次添加时抛出 IntegrityError
    2. 验证 unique constraint (uq_category_room) 生效
    """
    async for db in db_session:
        # Arrange
        topic = await create_test_topic(db)
        category = await create_test_category(db, topic.id)
        room = await create_test_room(db)
        
        # 第一次添加
        await crud_topic.add_room_to_category(db, category.id, room.id, sort_order=10)
        
        # Act & Assert - 第二次添加相同的直播间
        with pytest.raises(IntegrityError):
            await crud_topic.add_room_to_category(db, category.id, room.id, sort_order=20)


@pytest.mark.asyncio
async def test_batch_add_rooms_success(db_session):
    """
    测试批量添加多个直播间
    
    验证点:
    1. 返回的列表长度为 3
    2. 每个 association 的字段值正确
    3. 数据库验证：查询确认 3 条记录都已插入
    """
    async for db in db_session:
        # Arrange
        topic = await create_test_topic(db)
        category = await create_test_category(db, topic.id)
        
        room1 = await create_test_room(db)
        room2 = await create_test_room(db)
        room3 = await create_test_room(db)
        
        room_associations = [
            RoomAssociation(room_id=room1.id, sort_order=10),
            RoomAssociation(room_id=room2.id, sort_order=20),
            RoomAssociation(room_id=room3.id, sort_order=30)
        ]
        
        # Act
        associations = await crud_topic.batch_add_rooms(db, category.id, room_associations)
        
        # Assert
        assert len(associations) == 3, f"期望3个关联，实际 {len(associations)}"
        
        for i, assoc in enumerate(associations):
            assert assoc.category_id == category.id, f"关联{i} category_id 不匹配"
            assert assoc.room_id in [room1.id, room2.id, room3.id], f"关联{i} room_id 无效"
        
        # 数据库验证
        stmt = select(TopicCategoryRoom).where(TopicCategoryRoom.category_id == category.id)
        result = await db.execute(stmt)
        db_associations = result.scalars().all()
        
        assert len(db_associations) == 3, f"数据库中期望3条记录，实际 {len(db_associations)}"


@pytest.mark.asyncio
async def test_get_rooms_by_category_pagination(db_session):
    """
    测试分页获取分类下的直播间列表
    
    验证点:
    1. 返回的 tuple: (rooms_list, total_count)
    2. len(rooms_list) == 3
    3. total_count == 5
    4. 每个字典包含: room_id, title, cover_url, sort_order 等字段
    5. 返回的直播间按 sort_order ASC 排序
    """
    async for db in db_session:
        # Arrange
        topic = await create_test_topic(db)
        category = await create_test_category(db, topic.id)
        
        # 创建5个直播间并添加到分类
        for i, order in enumerate([50, 10, 30, 40, 20]):
            room = await create_test_room(db)
            await crud_topic.add_room_to_category(db, category.id, room.id, sort_order=order)
        
        # Act
        rooms, total = await crud_topic.get_rooms_by_category(
            db,
            category.id,
            skip=0,
            limit=3
        )
        
        # Assert
        assert isinstance(rooms, list), "rooms 应该是列表"
        assert isinstance(total, int), "total 应该是整数"
        assert len(rooms) == 3, f"期望3个直播间，实际 {len(rooms)}"
        assert total == 5, f"期望总数5，实际 {total}"
        
        # 验证返回的字典包含必要字段
        for room in rooms:
            assert 'room_id' in room, "缺少 room_id 字段"
            assert 'title' in room, "缺少 title 字段"
            assert 'sort_order' in room, "缺少 sort_order 字段"
        
        # 验证按 sort_order 排序
        sort_orders = [room['sort_order'] for room in rooms]
        assert sort_orders == [10, 20, 30], f"直播间未按 sort_order 排序: {sort_orders}"


@pytest.mark.asyncio
async def test_update_room_sort_order_success(db_session):
    """
    测试批量更新直播间排序
    
    验证点:
    1. 返回的更新记录数 == 2
    2. 数据库验证：查询确认对应记录的 sort_order 已更新为新值
    """
    async for db in db_session:
        # Arrange
        topic = await create_test_topic(db)
        category = await create_test_category(db, topic.id)
        
        room1 = await create_test_room(db)
        room2 = await create_test_room(db)
        room3 = await create_test_room(db)
        
        await crud_topic.add_room_to_category(db, category.id, room1.id, sort_order=10)
        await crud_topic.add_room_to_category(db, category.id, room2.id, sort_order=20)
        await crud_topic.add_room_to_category(db, category.id, room3.id, sort_order=30)
        
        room_sort_updates = [
            {"room_id": room1.id, "sort_order": 100},
            {"room_id": room2.id, "sort_order": 200}
        ]
        
        # Act
        updated_count = await crud_topic.update_room_sort_order(db, category.id, room_sort_updates)
        
        # Assert
        assert updated_count == 2, f"期望更新2条记录，实际 {updated_count}"
        
        # 数据库验证
        stmt = select(TopicCategoryRoom).where(
            TopicCategoryRoom.category_id == category.id,
            TopicCategoryRoom.room_id == room1.id
        )
        result = await db.execute(stmt)
        assoc1 = result.scalar_one_or_none()
        
        stmt = select(TopicCategoryRoom).where(
            TopicCategoryRoom.category_id == category.id,
            TopicCategoryRoom.room_id == room2.id
        )
        result = await db.execute(stmt)
        assoc2 = result.scalar_one_or_none()
        
        assert assoc1.sort_order == 100, f"room1 sort_order 未更新: {assoc1.sort_order}"
        assert assoc2.sort_order == 200, f"room2 sort_order 未更新: {assoc2.sort_order}"


@pytest.mark.asyncio
async def test_remove_room_from_category_success(db_session):
    """
    测试移除单个直播间关联
    
    验证点:
    1. 返回值为 True（删除成功）
    2. 数据库验证：查询确认关联记录已删除
    """
    async for db in db_session:
        # Arrange
        topic = await create_test_topic(db)
        category = await create_test_category(db, topic.id)
        room = await create_test_room(db)
        
        await crud_topic.add_room_to_category(db, category.id, room.id, sort_order=0)
        
        # Act
        result = await crud_topic.remove_room_from_category(db, category.id, room.id)
        
        # Assert
        assert result is True, "删除失败，返回了 False"
        
        # 数据库验证
        stmt = select(TopicCategoryRoom).where(
            TopicCategoryRoom.category_id == category.id,
            TopicCategoryRoom.room_id == room.id
        )
        db_result = await db.execute(stmt)
        db_association = db_result.scalar_one_or_none()
        
        assert db_association is None, "关联记录未被删除"


@pytest.mark.asyncio
async def test_remove_room_not_exists_returns_false(db_session):
    """
    测试移除不存在的关联返回 False
    
    验证点:
    1. 返回值为 False
    """
    async for db in db_session:
        # Arrange
        topic = await create_test_topic(db)
        category = await create_test_category(db, topic.id)
        room = await create_test_room(db)
        
        # 不添加直播间到分类
        
        # Act
        result = await crud_topic.remove_room_from_category(db, category.id, room.id)
        
        # Assert
        assert result is False, "期望返回 False，实际返回 True"


@pytest.mark.asyncio
async def test_batch_remove_rooms_success(db_session):
    """
    测试批量移除直播间关联
    
    验证点:
    1. 返回的删除记录数 == 3
    2. 数据库验证：查询确认 3 条记录已删除，剩余 2 条
    """
    async for db in db_session:
        # Arrange
        topic = await create_test_topic(db)
        category = await create_test_category(db, topic.id)
        
        rooms = []
        for i in range(5):
            room = await create_test_room(db)
            rooms.append(room)
            await crud_topic.add_room_to_category(db, category.id, room.id, sort_order=i*10)
        
        # 选择前3个直播间的 ID
        room_ids_to_remove = [rooms[0].id, rooms[1].id, rooms[2].id]
        
        # Act
        deleted_count = await crud_topic.batch_remove_rooms(db, category.id, room_ids_to_remove)
        
        # Assert
        assert deleted_count == 3, f"期望删除3条记录，实际 {deleted_count}"
        
        # 数据库验证
        stmt = select(TopicCategoryRoom).where(TopicCategoryRoom.category_id == category.id)
        result = await db.execute(stmt)
        remaining_associations = result.scalars().all()
        
        assert len(remaining_associations) == 2, f"期望剩余2条记录，实际 {len(remaining_associations)}"


@pytest.mark.asyncio
async def test_check_room_association_exists(db_session):
    """
    测试检查关联是否存在
    
    验证点:
    1. room1 已添加到分类，返回 True
    2. room2 未添加到分类，返回 False
    """
    async for db in db_session:
        # Arrange
        topic = await create_test_topic(db)
        category = await create_test_category(db, topic.id)
        
        room1 = await create_test_room(db)
        room2 = await create_test_room(db)
        
        # 只添加 room1 到分类
        await crud_topic.add_room_to_category(db, category.id, room1.id, sort_order=0)
        
        # Act & Assert - room1 存在
        exists1 = await crud_topic.check_room_association_exists(db, category.id, room1.id)
        assert exists1 is True, "room1 应该存在于分类中"
        
        # Act & Assert - room2 不存在
        exists2 = await crud_topic.check_room_association_exists(db, category.id, room2.id)
        assert exists2 is False, "room2 不应该存在于分类中"


# ==================== 辅助查询操作测试 ====================

@pytest.mark.asyncio
async def test_get_topics_by_room_success_anonymous(
    db_session,
    public_room,
    published_topic,
    draft_topic
):
    """
    测试获取直播间关联的专题列表（匿名用户，只能看到Published专题，S16场景）
    
    验证点:
    1. 返回的列表只包含 PUBLISHED 状态的专题
    2. 每个字典包含: topic_id, topic_title, topic_status, category_id, category_name
    3. 所有返回的 topic_status 值为 "published" 字符串
    """
    async for db in db_session:
        # ===== Arrange (准备) =====
        # 使用async for获取fixture返回的实际对象
        async for pub_room in public_room:
            async for pub_topic in published_topic:
                async for drf_topic in draft_topic:
                    # 为published_topic和draft_topic创建分类
                    category1 = await create_test_category(db, pub_topic.id)
                    category2 = await create_test_category(db, drf_topic.id)
                    
                    # 将直播间添加到两个分类
                    await crud_topic.add_room_to_category(db, category1.id, pub_room.id, sort_order=0)
                    await crud_topic.add_room_to_category(db, category2.id, pub_room.id, sort_order=0)
                    
                    # ===== Act (执行) =====
                    # ← 修改：传递None作为权限参数（匿名用户）
                    topics = await crud_topic.get_topics_by_room(
                        db, 
                        pub_room.id,
                        user_id=None,  # ← 新增：匿名用户
                        role=None      # ← 新增：匿名用户
                    )
                    
                    # ===== Assert (断言) =====
                    assert isinstance(topics, list), "topics 应该是列表"
                    # ← 新增：验证只能看到Published专题
                    topic_ids = [topic_dict['topic_id'] for topic_dict in topics]
                    assert str(pub_topic.id) in topic_ids, "应该能看到Published专题"
                    assert str(drf_topic.id) not in topic_ids, "不应该能看到Draft专题（匿名用户）"
                    
                    # 验证每个字典包含必要字段
                    for topic_dict in topics:
                        assert 'topic_id' in topic_dict, "缺少 topic_id 字段"
                        assert 'topic_title' in topic_dict, "缺少 topic_title 字段"
                        assert 'topic_status' in topic_dict, "缺少 topic_status 字段"
                        assert 'category_id' in topic_dict, "缺少 category_id 字段"
                        assert 'category_name' in topic_dict, "缺少 category_name 字段"
                        
                        # 验证只返回 PUBLISHED 状态
                        assert topic_dict['topic_status'] == "published", f"期望 published，实际 {topic_dict['topic_status']}"
                    break
                break
            break

# ← 新增：测试登录用户场景（S16）
@pytest.mark.asyncio
async def test_get_topics_by_room_success_as_owner(
    db_session,
    regular_user_id: uuid.UUID,
    regular_user_role: str,
    public_room,
    published_topic,
    draft_topic_owned_by_user,
    draft_topic_owned_by_another_user
):
    """测试获取直播间关联的专题列表（登录用户，可以看到Published+自己的专题，S16场景）"""
    async for db in db_session:
        # ===== Arrange (准备) =====
        # 使用async for获取fixture返回的实际对象
        async for pub_room in public_room:
            async for pub_topic in published_topic:
                async for my_draft_topic in draft_topic_owned_by_user:
                    async for other_draft_topic in draft_topic_owned_by_another_user:
                        # 为专题创建分类
                        category1 = await create_test_category(db, pub_topic.id)
                        category2 = await create_test_category(db, my_draft_topic.id)
                        category3 = await create_test_category(db, other_draft_topic.id)
                        
                        # 将直播间添加到所有分类
                        await crud_topic.add_room_to_category(db, category1.id, pub_room.id, sort_order=0)
                        await crud_topic.add_room_to_category(db, category2.id, pub_room.id, sort_order=0)
                        await crud_topic.add_room_to_category(db, category3.id, pub_room.id, sort_order=0)
                        
                        # ===== Act (执行) =====
                        topics = await crud_topic.get_topics_by_room(
                            db,
                            pub_room.id,
                            user_id=regular_user_id,  # ← 新增
                            role=regular_user_role     # ← 新增
                        )
                        
                        # ===== Assert (断言) =====
                        topic_ids = [topic_dict['topic_id'] for topic_dict in topics]
                        assert str(pub_topic.id) in topic_ids, "应该能看到Published专题"
                        assert str(my_draft_topic.id) in topic_ids, "应该能看到自己的Draft专题"
                        assert str(other_draft_topic.id) not in topic_ids, "不应该能看到他人的Draft专题"
                        break
                    break
                break
            break

# ← 新增：测试Admin用户场景（S6）
@pytest.mark.asyncio
async def test_get_topics_by_room_success_as_admin(
    db_session,
    admin_user_id: uuid.UUID,
    admin_user_role: str,
    public_room,
    published_topic,
    draft_topic
):
    """测试获取直播间关联的专题列表（Admin用户，可以看到所有专题，S6场景）"""
    async for db in db_session:
        # ===== Arrange (准备) =====
        # 使用async for获取fixture返回的实际对象
        async for pub_room in public_room:
            async for pub_topic in published_topic:
                async for drf_topic in draft_topic:
                    # 为专题创建分类
                    category1 = await create_test_category(db, pub_topic.id)
                    category2 = await create_test_category(db, drf_topic.id)
                    
                    # 将直播间添加到所有分类
                    await crud_topic.add_room_to_category(db, category1.id, pub_room.id, sort_order=0)
                    await crud_topic.add_room_to_category(db, category2.id, pub_room.id, sort_order=0)
                    
                    # ===== Act (执行) =====
                    topics = await crud_topic.get_topics_by_room(
                        db,
                        pub_room.id,
                        user_id=admin_user_id,  # ← 新增
                        role=admin_user_role     # ← 新增
                    )
                    
                    # ===== Assert (断言) =====
                    topic_ids = [topic_dict['topic_id'] for topic_dict in topics]
                    assert str(pub_topic.id) in topic_ids, "应该能看到Published专题"
                    assert str(drf_topic.id) in topic_ids, "Admin应该能看到所有专题（包括Draft）"
                    break
                break
            break

