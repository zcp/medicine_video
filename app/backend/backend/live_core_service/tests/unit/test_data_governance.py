"""
数据关联完整性治理（P0-1 焦点图悬挂引用）单元测试

覆盖用例（治理文档 §10.1）：
- 用例 1：删除直播间 → 指向该房间的焦点图被软下线
- 用例 2：删除场次 → 指向该场次的焦点图被软下线
- 用例 4：删除专题 → 指向该专题的焦点图被软下线
- 用例 5：软删品牌 → 指向该品牌的焦点图被软下线（D3=是）
- 用例 6：硬删品牌（有焦点图引用）→ 拒绝并提示引用数（D2=拒绝）
- 用例 7：公开焦点图列表 → 悬挂 target 不返回；管理端列表 → 全量可见

测试数据统一使用 TEST_治理 前缀，落于独立测试库 live_core_test_gov。
"""
import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import select, delete

from app.models.homepage_search import FeaturedContent
from app.models.live_core import LiveRoom, LiveSession, LiveSessionStatus
from app.models.topic import Topic
from app.models.brand import Brand
from app.crud import homepage_search as crud_homepage_search
from app.services.session_service import SessionService
from app.services.topic_service import TopicService
from app.services.brand_service import BrandService
from app.exceptions import InvalidParameterException


# ==================== 测试数据辅助函数 ====================

def _uid(prefix: str = "") -> str:
    return f"{prefix}{uuid.uuid4().hex[:8]}"


async def _create_room(db, user_id) -> LiveRoom:
    room = LiveRoom(
        id=uuid.uuid4(),
        user_id=user_id,
        title=_uid("TEST_治理房间_"),
        stream_key=f"streamkey_{uuid.uuid4().hex[:16]}",
    )
    db.add(room)
    await db.commit()
    await db.refresh(room)
    return room


async def _create_session(db, room_id) -> LiveSession:
    session = LiveSession(
        id=uuid.uuid4(),
        room_id=room_id,
        status=LiveSessionStatus.SCHEDULED,
        start_time=datetime.now(timezone.utc),
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


async def _create_topic(db, user_id) -> Topic:
    topic = Topic(
        id=uuid.uuid4(),
        user_id=user_id,
        title=_uid("TEST_治理专题_"),
    )
    db.add(topic)
    await db.commit()
    await db.refresh(topic)
    return topic


async def _create_brand(db) -> Brand:
    brand = Brand(id=uuid.uuid4(), name=_uid("TEST_治理品牌_"))
    db.add(brand)
    await db.commit()
    await db.refresh(brand)
    return brand


async def _create_featured(db, target_type, target_id) -> FeaturedContent:
    content = FeaturedContent(
        id=uuid.uuid4(),
        title=_uid("TEST_治理焦点图_"),
        image_url=f"https://example.com/{uuid.uuid4().hex}.jpg",
        target_type=target_type,
        target_id=target_id,
        is_active=True,
    )
    db.add(content)
    await db.commit()
    await db.refresh(content)
    return content


async def _get_featured(db, content_id) -> FeaturedContent:
    result = await db.execute(select(FeaturedContent).where(FeaturedContent.id == content_id))
    return result.scalar_one_or_none()


# ==================== 用例 8：场次专家读取过滤（普通用户不见停用专家） ====================

@pytest.mark.asyncio
async def test_session_experts_filtered_by_viewer_role(db_session):
    """普通用户/匿名不见已停用专家，管理员可见全量（D4 定稿）"""
    async for db in db_session:
        from app.models.experts import Expert, LiveSessionExpert
        from app.models.content_management import Category
        from app.services.expert_service import ExpertService

        user_id = uuid.uuid4()
        room = await _create_room(db, user_id)
        session = await _create_session(db, room.id)

        cat = Category(id=uuid.uuid4(), name=_uid("TEST_治理分类_"))
        db.add(cat)
        await db.commit()

        expert_active = Expert(id=uuid.uuid4(), name=_uid("TEST_治理专家_启用_"), category_id=cat.id, is_active=True)
        expert_inactive = Expert(id=uuid.uuid4(), name=_uid("TEST_治理专家_停用_"), category_id=cat.id, is_active=False)
        db.add_all([expert_active, expert_inactive])
        await db.commit()

        db.add_all([
            LiveSessionExpert(session_id=session.id, expert_id=expert_active.id, role="主讲", sort_order=0),
            LiveSessionExpert(session_id=session.id, expert_id=expert_inactive.id, role="嘉宾", sort_order=1),
        ])
        await db.commit()

        service = ExpertService(db)
        # 普通用户视角：不见已停用专家
        visible = await service.get_session_experts(
            session_id=session.id, role=None, current_user_id=None, role_user="REGULAR"
        )
        visible_ids = [e.id for e in visible]
        assert expert_active.id in visible_ids
        assert expert_inactive.id not in visible_ids, "普通用户不应看到已停用专家"
        # 管理员视角：全量可见
        admin_view = await service.get_session_experts(
            session_id=session.id, role=None, current_user_id=user_id, role_user="ADMIN"
        )
        admin_ids = [e.id for e in admin_view]
        assert expert_active.id in admin_ids
        assert expert_inactive.id in admin_ids, "管理员应看到全部专家（含已停用）"


# ==================== 用例 9：场次设置标签 is_active 校验 ====================

@pytest.mark.asyncio
async def test_set_session_tags_rejects_inactive_tag(db_session):
    """场次设置标签：包含已停用标签 → 4001；仅启用标签 → 成功（P1-2）"""
    async for db in db_session:
        from app.models.content_management import Tag
        from app.services.content_management_service import ContentManagementService
        from app.schemas.content_management import SessionTagsSetRequest

        user_id = uuid.uuid4()
        room = await _create_room(db, user_id)
        session = await _create_session(db, room.id)
        session_id = session.id  # 提前提取：后续 commit/rollback 会使 ORM 对象过期

        tag_active = Tag(id=uuid.uuid4(), name=_uid("TEST_治理标签_启用_"), is_active=True)
        tag_inactive = Tag(id=uuid.uuid4(), name=_uid("TEST_治理标签_停用_"), is_active=False)
        db.add_all([tag_active, tag_inactive])
        await db.commit()

        service = ContentManagementService()
        # 包含已停用标签 → 4001（P1-2 核心增量语义；成功路径由存量测试覆盖）
        with pytest.raises(InvalidParameterException) as exc_info:
            await service.set_session_tags(
                db=db,
                session_id=session_id,
                request_data=SessionTagsSetRequest(tag_ids=[tag_active.id, tag_inactive.id], mode="replace"),
                current_user_id=user_id,
                role="ADMIN",
            )
        assert "已停用" in str(exc_info.value), "错误信息应提示标签已停用"


# ==================== 用例 1：删房间 → 焦点图软下线（含级联场次，V1.5 修复） ====================

@pytest.mark.asyncio
async def test_delete_room_disables_featured_content(db_session):
    """删除直播间后，指向该房间及其场次的焦点图被软下线（is_active=False）"""
    async for db in db_session:
        user_id = uuid.uuid4()
        room = await _create_room(db, user_id)
        session = await _create_session(db, room.id)
        content = await _create_featured(db, "room", room.id)
        session_content = await _create_featured(db, "session", session.id)

        from app.crud import room as crud_room
        await crud_room.delete_room_related(db, room.id)
        await crud_room.remove(db, room)

        updated = await _get_featured(db, content.id)
        assert updated is not None, "焦点图记录应保留（软下线而非硬删）"
        assert updated.is_active is False, "指向已删房间的焦点图应被软下线"

        # V1.5 修复：删房间级联删场次时，指向该场次的焦点图同样软下线
        session_updated = await _get_featured(db, session_content.id)
        assert session_updated is not None, "场次焦点图记录应保留（软下线而非硬删）"
        assert session_updated.is_active is False, "删房间级联删场次时，指向该场次的焦点图应被软下线"


# ==================== 用例 2：删场次 → 焦点图软下线 ====================

@pytest.mark.asyncio
async def test_delete_session_disables_featured_content(db_session):
    """删除场次后，指向该场次的焦点图被软下线"""
    async for db in db_session:
        user_id = uuid.uuid4()
        room = await _create_room(db, user_id)
        session = await _create_session(db, room.id)
        content = await _create_featured(db, "session", session.id)

        service = SessionService(db)
        await service.delete_session(session_id=session.id, user_id=user_id, role="REGULAR")

        updated = await _get_featured(db, content.id)
        assert updated is not None
        assert updated.is_active is False, "指向已删场次的焦点图应被软下线"


# ==================== 用例 3：删场次 → SESSION 订阅硬删 ====================

@pytest.mark.asyncio
async def test_delete_session_hard_deletes_subscription(db_session):
    """删除场次后，指向该场次的用户订阅被硬删（D5 定稿，与删房间路径对齐）"""
    async for db in db_session:
        from app.models.user_behavior import UserSubscription, SubscriptionTargetType

        user_id = uuid.uuid4()
        room = await _create_room(db, user_id)
        session = await _create_session(db, room.id)
        subscription = UserSubscription(
            id=uuid.uuid4(),
            user_id=user_id,
            target_type=SubscriptionTargetType.SESSION,
            target_id=session.id,
        )
        db.add(subscription)
        await db.commit()

        service = SessionService(db)
        await service.delete_session(session_id=session.id, user_id=user_id, role="REGULAR")

        result = await db.execute(
            select(UserSubscription).where(UserSubscription.id == subscription.id)
        )
        assert result.scalar_one_or_none() is None, "指向已删场次的订阅应被硬删，无残留"


# ==================== 用例 4：删专题 → 焦点图软下线 ====================

@pytest.mark.asyncio
async def test_delete_topic_disables_featured_content(db_session):
    """删除专题后，指向该专题的焦点图被软下线"""
    async for db in db_session:
        user_id = uuid.uuid4()
        topic = await _create_topic(db, user_id)
        content = await _create_featured(db, "topic", topic.id)

        service = TopicService(db)
        await service.delete_topic(topic_id=topic.id, user_id=user_id, role="REGULAR")

        updated = await _get_featured(db, content.id)
        assert updated is not None
        assert updated.is_active is False, "指向已删专题的焦点图应被软下线"


# ==================== 用例 5：软删品牌 → 焦点图软下线 ====================

@pytest.mark.asyncio
async def test_soft_delete_brand_disables_featured_content(db_session):
    """软删品牌（D3=是）后，指向该品牌的焦点图被软下线"""
    async for db in db_session:
        brand = await _create_brand(db)
        content = await _create_featured(db, "brand", brand.id)

        service = BrandService()
        await service.delete_brand(
            db=db, brand_id=brand.id, hard_delete=False,
            current_user_id=uuid.uuid4(), role="ADMIN",
        )

        updated = await _get_featured(db, content.id)
        assert updated is not None
        assert updated.is_active is False, "指向已软删品牌的焦点图应被软下线"
        # 品牌本身软删
        assert brand.is_active is False


# ==================== 用例 6：硬删品牌（有焦点图引用）→ 拒绝 ====================

@pytest.mark.asyncio
async def test_hard_delete_brand_blocked_by_featured_content(db_session):
    """硬删品牌（D2=拒绝）时，有焦点图引用应被拒绝并提示引用数"""
    async for db in db_session:
        brand = await _create_brand(db)
        await _create_featured(db, "brand", brand.id)

        service = BrandService()
        with pytest.raises(InvalidParameterException) as exc_info:
            await service.delete_brand(
                db=db, brand_id=brand.id, hard_delete=True,
                current_user_id=uuid.uuid4(), role="SUPERADMIN",
            )
        assert "焦点图引用数：1" in str(exc_info.value), "错误信息应包含焦点图引用数"
        # 品牌应未被删除
        from sqlalchemy import select
        result = await db.execute(select(Brand).where(Brand.id == brand.id))
        assert result.scalar_one_or_none() is not None, "被拒绝后品牌不应被删除"


# ==================== 用例 7：公开列表过滤悬挂 target ====================

@pytest.mark.asyncio
async def test_public_list_filters_dangling_target(db_session):
    """公开焦点图列表过滤失效 target；管理端列表保持全量可见"""
    async for db in db_session:
        await db.execute(delete(FeaturedContent))
        await db.commit()

        # 有效引用：指向存在房间的焦点图
        user_id = uuid.uuid4()
        room = await _create_room(db, user_id)
        valid_content = await _create_featured(db, "room", room.id)
        # 悬挂引用：指向不存在房间的焦点图
        dangling_content = await _create_featured(db, "room", uuid.uuid4())
        # 外链型（target_id 为空）应保留
        external_content = FeaturedContent(
            id=uuid.uuid4(),
            title=_uid("TEST_治理外链_"),
            image_url=f"https://example.com/{uuid.uuid4().hex}.jpg",
            target_type="external",
            target_id=None,
            is_active=True,
        )
        db.add(external_content)
        await db.commit()

        # 公开列表：悬挂引用不返回，有效引用与外链保留
        public_results = await crud_homepage_search.get_featured_content_list(
            db, include_inactive=False, include_scheduled=False
        )
        public_ids = [c.id for c in public_results]
        assert valid_content.id in public_ids
        assert dangling_content.id not in public_ids, "悬挂 target 不应出现在公开列表"
        assert external_content.id in public_ids, "外链型焦点图应保留"

        # 管理端列表：全量可见（含悬挂），便于运营发现处理
        admin_results = await crud_homepage_search.get_featured_content_list(
            db, include_inactive=True, include_scheduled=True
        )
        admin_ids = [c.id for c in admin_results]
        assert dangling_content.id in admin_ids, "管理端列表应全量可见（含悬挂）"

        # 清理
        await db.execute(delete(FeaturedContent))
        await db.commit()
