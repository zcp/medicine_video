"""
直播间 Tab 和留言功能的 CRUD 层测试（实用派）

本模块使用真实数据库测试数据访问层，验证：
- 数据库操作的正确性
- 数据持久化状态
- 分页、排序、过滤功能
- 外键约束和完整性
"""

import pytest
import uuid
from faker import Faker
from datetime import datetime, timedelta, timezone
from sqlalchemy.exc import IntegrityError

from app.crud import live_features as crud_live_features
from app.models.live_core import LiveRoom, LiveSession, LiveSessionStatus
from app.models.live_features import (
    LiveRoomTab,
    LiveRoomMessage,
    LiveRoomTabContentType,
    LiveRoomMessageUserRole
)
from app.schemas.live_features import (
    LiveRoomTabCreate,
    LiveRoomTabUpdate,
    LiveRoomMessageCreateInternal
)

fake = Faker()


class TestLiveRoomTabCRUD:
    """LiveRoomTab CRUD 操作测试"""

    @pytest.mark.asyncio
    async def test_create_tab_success(self, db_session):
        """测试成功创建Tab"""
        async for db in db_session:
            # 1. 准备 (Arrange)
            # 创建 LiveRoom 依赖
            room = LiveRoom(
                id=uuid.uuid4(),
                user_id=uuid.uuid4(),
                title=f"Test Room {uuid.uuid4().hex[:8]}",
                stream_key=f"stream_{uuid.uuid4().hex}"
            )
            db.add(room)
            await db.commit()
            await db.refresh(room)
            
            # 准备 Tab 创建数据
            tab_key = f"tab_{uuid.uuid4().hex[:8]}"
            obj_in = LiveRoomTabCreate(
                tab_key=tab_key,
                title=fake.sentence(nb_words=3),
                content_type=LiveRoomTabContentType.TEXT,
                text_content="测试内容",
                sort_order=0,
                is_active=True
            )
            
            # 2. 执行 (Act)
            new_tab = await crud_live_features.create_tab(db, obj_in, room.id)
            
            # 3. 断言 (Assert)
            assert new_tab is not None
            assert isinstance(new_tab.id, uuid.UUID)
            assert new_tab.room_id == room.id
            assert new_tab.tab_key == obj_in.tab_key
            assert new_tab.title == obj_in.title
            assert new_tab.content_type == obj_in.content_type
            assert new_tab.text_content == obj_in.text_content
            assert new_tab.sort_order == obj_in.sort_order
            assert new_tab.is_active == obj_in.is_active
            assert new_tab.created_at is not None
            assert new_tab.updated_at is not None
            
            # [关键] 数据库持久化验证
            fetched_tab = await crud_live_features.get_tab(db, new_tab.id)
            assert fetched_tab is not None
            assert fetched_tab.id == new_tab.id

    @pytest.mark.asyncio
    async def test_create_tab_with_invalid_room_id_raises_integrity_error(self, db_session):
        """
        测试使用无效room_id创建Tab引发完整性错误
        
        注意：如果外键约束没有被正确创建，此测试可能会失败。
        这是数据库配置问题，不是代码问题。
        """
        async for db in db_session:
            # 1. 准备 (Arrange)
            invalid_room_id = uuid.uuid4()
            obj_in = LiveRoomTabCreate(
                tab_key=f"tab_{uuid.uuid4().hex[:8]}",
                title="测试Tab",
                content_type=LiveRoomTabContentType.TEXT,
                text_content="测试内容"
            )
            
            # 2. 执行 & 断言 (Act & Assert)
            # 注意：create_tab 内部会执行 commit，如果外键约束存在，应该会抛出 IntegrityError
            # 但如果约束没有被正确创建，操作会成功，测试会失败
            try:
                result = await crud_live_features.create_tab(db, obj_in, invalid_room_id)
                # 如果操作成功，说明外键约束没有被正确创建，这是一个数据库配置问题
                # 我们仍然标记为失败，但提供更清晰的错误信息
                pytest.fail(
                    f"Expected IntegrityError but operation succeeded. "
                    f"This indicates that foreign key constraints may not be properly created in the test database. "
                    f"Created tab_id: {result.id}, room_id: {invalid_room_id}"
                )
            except IntegrityError:
                # 预期的行为：外键约束应该阻止使用无效的 room_id
                pass

    @pytest.mark.asyncio
    async def test_get_tab_success(self, db_session):
        """测试成功获取Tab"""
        async for db in db_session:
            # 1. 准备 (Arrange)
            room = LiveRoom(
                id=uuid.uuid4(),
                user_id=uuid.uuid4(),
                title=f"Test Room {uuid.uuid4().hex[:8]}",
                stream_key=f"stream_{uuid.uuid4().hex}"
            )
            db.add(room)
            await db.commit()
            
            tab = LiveRoomTab(
                id=uuid.uuid4(),
                room_id=room.id,
                tab_key=f"tab_{uuid.uuid4().hex[:8]}",
                title="测试Tab",
                content_type=LiveRoomTabContentType.TEXT,
                text_content="测试内容"
            )
            db.add(tab)
            await db.commit()
            await db.refresh(tab)
            
            # 2. 执行 (Act)
            result = await crud_live_features.get_tab(db, tab.id)
            
            # 3. 断言 (Assert)
            assert result is not None
            assert result.id == tab.id
            assert result.tab_key == tab.tab_key

    @pytest.mark.asyncio
    async def test_get_tab_not_found(self, db_session):
        """测试获取不存在的Tab"""
        async for db in db_session:
            # 1. 准备 (Arrange)
            non_existent_id = uuid.uuid4()
            
            # 2. 执行 (Act)
            result = await crud_live_features.get_tab(db, non_existent_id)
            
            # 3. 断言 (Assert)
            assert result is None

    @pytest.mark.asyncio
    async def test_get_tab_with_room_success(self, db_session):
        """测试成功获取Tab并预加载room关系"""
        async for db in db_session:
            # 1. 准备 (Arrange)
            room = LiveRoom(
                id=uuid.uuid4(),
                user_id=uuid.uuid4(),
                title=f"Test Room {uuid.uuid4().hex[:8]}",
                stream_key=f"stream_{uuid.uuid4().hex}"
            )
            db.add(room)
            await db.commit()
            
            tab = LiveRoomTab(
                id=uuid.uuid4(),
                room_id=room.id,
                tab_key=f"tab_{uuid.uuid4().hex[:8]}",
                title="测试Tab",
                content_type=LiveRoomTabContentType.TEXT,
                text_content="测试内容"
            )
            db.add(tab)
            await db.commit()
            await db.refresh(tab)
            
            # 2. 执行 (Act)
            result = await crud_live_features.get_tab_with_room(db, tab.id)
            
            # 3. 断言 (Assert)
            assert result is not None
            assert result.id == tab.id
            # [关键] 预加载验证
            assert result.room is not None
            assert result.room.id == room.id

    @pytest.mark.asyncio
    async def test_get_tab_with_room_not_found(self, db_session):
        """测试获取不存在的Tab（含room预加载）"""
        async for db in db_session:
            # 1. 准备 (Arrange)
            non_existent_id = uuid.uuid4()
            
            # 2. 执行 (Act)
            result = await crud_live_features.get_tab_with_room(db, non_existent_id)
            
            # 3. 断言 (Assert)
            assert result is None

    @pytest.mark.asyncio
    async def test_get_all_by_room_id_success(self, db_session):
        """测试成功分页获取房间的所有Tab"""
        async for db in db_session:
            # 1. 准备 (Arrange)
            room = LiveRoom(
                id=uuid.uuid4(),
                user_id=uuid.uuid4(),
                title=f"Test Room {uuid.uuid4().hex[:8]}",
                stream_key=f"stream_{uuid.uuid4().hex}"
            )
            db.add(room)
            await db.commit()
            
            # 创建3个Tab，设置不同的sort_order
            for i in range(3):
                tab = LiveRoomTab(
                    id=uuid.uuid4(),
                    room_id=room.id,
                    tab_key=f"tab_{uuid.uuid4().hex[:8]}",
                    title=f"Tab {i}",
                    content_type=LiveRoomTabContentType.TEXT,
                    text_content=f"内容 {i}",
                    sort_order=i
                )
                db.add(tab)
            await db.commit()
            
            # 2. 执行 (Act)
            tabs, total = await crud_live_features.get_all_by_room_id(db, room.id, skip=0, limit=10)
            
            # 3. 断言 (Assert)
            assert total == 3
            assert len(tabs) == 3
            # [关键] 排序验证
            assert tabs[0].sort_order < tabs[1].sort_order < tabs[2].sort_order

    @pytest.mark.asyncio
    async def test_get_all_by_room_id_pagination(self, db_session):
        """测试分页功能"""
        async for db in db_session:
            # 1. 准备 (Arrange)
            room = LiveRoom(
                id=uuid.uuid4(),
                user_id=uuid.uuid4(),
                title=f"Test Room {uuid.uuid4().hex[:8]}",
                stream_key=f"stream_{uuid.uuid4().hex}"
            )
            db.add(room)
            await db.commit()
            
            # 创建5个Tab
            for i in range(5):
                tab = LiveRoomTab(
                    id=uuid.uuid4(),
                    room_id=room.id,
                    tab_key=f"tab_{uuid.uuid4().hex[:8]}",
                    title=f"Tab {i}",
                    content_type=LiveRoomTabContentType.TEXT,
                    text_content=f"内容 {i}",
                    sort_order=i
                )
                db.add(tab)
            await db.commit()
            
            # 2. 执行 (Act)
            tabs, total = await crud_live_features.get_all_by_room_id(db, room.id, skip=2, limit=2)
            
            # 3. 断言 (Assert)
            assert total == 5
            assert len(tabs) == 2  # 返回第3-4个

    @pytest.mark.asyncio
    async def test_get_all_by_room_id_empty(self, db_session):
        """测试获取空房间的Tab列表"""
        async for db in db_session:
            # 1. 准备 (Arrange)
            room = LiveRoom(
                id=uuid.uuid4(),
                user_id=uuid.uuid4(),
                title=f"Test Room {uuid.uuid4().hex[:8]}",
                stream_key=f"stream_{uuid.uuid4().hex}"
            )
            db.add(room)
            await db.commit()
            
            # 2. 执行 (Act)
            tabs, total = await crud_live_features.get_all_by_room_id(db, room.id, skip=0, limit=10)
            
            # 3. 断言 (Assert)
            assert total == 0
            assert len(tabs) == 0

    @pytest.mark.asyncio
    async def test_get_active_by_room_id_success(self, db_session):
        """测试只获取激活的Tab"""
        async for db in db_session:
            # 1. 准备 (Arrange)
            room = LiveRoom(
                id=uuid.uuid4(),
                user_id=uuid.uuid4(),
                title=f"Test Room {uuid.uuid4().hex[:8]}",
                stream_key=f"stream_{uuid.uuid4().hex}"
            )
            db.add(room)
            await db.commit()
            
            # 创建3个Tab：2个激活，1个未激活
            for i in range(3):
                tab = LiveRoomTab(
                    id=uuid.uuid4(),
                    room_id=room.id,
                    tab_key=f"tab_{uuid.uuid4().hex[:8]}",
                    title=f"Tab {i}",
                    content_type=LiveRoomTabContentType.TEXT,
                    text_content=f"内容 {i}",
                    sort_order=i,
                    is_active=(i < 2)  # 前2个激活
                )
                db.add(tab)
            await db.commit()
            
            # 2. 执行 (Act)
            tabs = await crud_live_features.get_active_by_room_id(db, room.id)
            
            # 3. 断言 (Assert)
            assert len(tabs) == 2
            for tab in tabs:
                assert tab.is_active is True
            # [关键] 排序验证
            assert tabs[0].sort_order < tabs[1].sort_order

    @pytest.mark.asyncio
    async def test_get_active_by_room_id_empty(self, db_session):
        """测试获取空房间的激活Tab"""
        async for db in db_session:
            # 1. 准备 (Arrange)
            room = LiveRoom(
                id=uuid.uuid4(),
                user_id=uuid.uuid4(),
                title=f"Test Room {uuid.uuid4().hex[:8]}",
                stream_key=f"stream_{uuid.uuid4().hex}"
            )
            db.add(room)
            await db.commit()
            
            # 2. 执行 (Act)
            tabs = await crud_live_features.get_active_by_room_id(db, room.id)
            
            # 3. 断言 (Assert)
            assert len(tabs) == 0

    @pytest.mark.asyncio
    async def test_update_tab_success(self, db_session):
        """测试成功更新Tab"""
        async for db in db_session:
            # 1. 准备 (Arrange)
            room = LiveRoom(
                id=uuid.uuid4(),
                user_id=uuid.uuid4(),
                title=f"Test Room {uuid.uuid4().hex[:8]}",
                stream_key=f"stream_{uuid.uuid4().hex}"
            )
            db.add(room)
            await db.commit()
            
            tab = LiveRoomTab(
                id=uuid.uuid4(),
                room_id=room.id,
                tab_key=f"tab_{uuid.uuid4().hex[:8]}",
                title="原标题",
                content_type=LiveRoomTabContentType.TEXT,
                text_content="原内容",
                is_active=True
            )
            db.add(tab)
            await db.commit()
            await db.refresh(tab)
            
            obj_in = LiveRoomTabUpdate(title="新标题", is_active=False)
            
            # 2. 执行 (Act)
            updated_tab = await crud_live_features.update_tab(db, tab, obj_in)
            
            # 3. 断言 (Assert)
            assert updated_tab is not None
            assert updated_tab.title == "新标题"
            assert updated_tab.is_active is False
            
            # [关键] 数据库持久化验证
            fetched_tab = await crud_live_features.get_tab(db, updated_tab.id)
            assert fetched_tab.title == "新标题"
            assert fetched_tab.is_active is False

    @pytest.mark.asyncio
    async def test_update_tab_partial_update(self, db_session):
        """测试部分更新Tab"""
        async for db in db_session:
            # 1. 准备 (Arrange)
            room = LiveRoom(
                id=uuid.uuid4(),
                user_id=uuid.uuid4(),
                title=f"Test Room {uuid.uuid4().hex[:8]}",
                stream_key=f"stream_{uuid.uuid4().hex}"
            )
            db.add(room)
            await db.commit()
            
            tab = LiveRoomTab(
                id=uuid.uuid4(),
                room_id=room.id,
                tab_key=f"tab_{uuid.uuid4().hex[:8]}",
                title="原标题",
                content_type=LiveRoomTabContentType.TEXT,
                text_content="原内容",
                sort_order=0
            )
            db.add(tab)
            await db.commit()
            await db.refresh(tab)
            
            obj_in = LiveRoomTabUpdate(sort_order=5)
            
            # 2. 执行 (Act)
            updated_tab = await crud_live_features.update_tab(db, tab, obj_in)
            
            # 3. 断言 (Assert)
            assert updated_tab.sort_order == 5
            assert updated_tab.title == "原标题"  # 未更新，保持原值

    @pytest.mark.asyncio
    async def test_remove_tab_success(self, db_session):
        """测试成功删除Tab"""
        async for db in db_session:
            # 1. 准备 (Arrange)
            room = LiveRoom(
                id=uuid.uuid4(),
                user_id=uuid.uuid4(),
                title=f"Test Room {uuid.uuid4().hex[:8]}",
                stream_key=f"stream_{uuid.uuid4().hex}"
            )
            db.add(room)
            await db.commit()
            
            tab = LiveRoomTab(
                id=uuid.uuid4(),
                room_id=room.id,
                tab_key=f"tab_{uuid.uuid4().hex[:8]}",
                title="测试Tab",
                content_type=LiveRoomTabContentType.TEXT,
                text_content="测试内容"
            )
            db.add(tab)
            await db.commit()
            await db.refresh(tab)
            
            tab_id = tab.id
            
            # 2. 执行 (Act)
            deleted_tab = await crud_live_features.remove_tab(db, tab)
            
            # 3. 断言 (Assert)
            assert deleted_tab is not None
            
            # [关键] 数据库删除验证
            fetched_tab = await crud_live_features.get_tab(db, tab_id)
            assert fetched_tab is None

    @pytest.mark.asyncio
    async def test_remove_tab_returns_simple_namespace(self, db_session):
        """P0 修复验证：remove_tab 返回 SimpleNamespace，.id 为字符串且可访问"""
        async for db in db_session:
            # 1. 准备 (Arrange)
            room = LiveRoom(
                id=uuid.uuid4(),
                user_id=uuid.uuid4(),
                title=f"Test Room {uuid.uuid4().hex[:8]}",
                stream_key=f"stream_{uuid.uuid4().hex}"
            )
            db.add(room)
            await db.commit()

            tab = LiveRoomTab(
                id=uuid.uuid4(),
                room_id=room.id,
                tab_key=f"verify_{uuid.uuid4().hex[:8]}",
                title="P0 验证",
                content_type=LiveRoomTabContentType.TEXT,
                text_content="P0 fix test"
            )
            db.add(tab)
            await db.commit()
            await db.refresh(tab)

            tab_id = tab.id
            tab_key = tab.tab_key

            # 2. 执行 (Act)
            deleted_tab = await crud_live_features.remove_tab(db, tab)

            # 3. 断言 (Assert) — P0 修复后返回 SimpleNamespace
            assert deleted_tab is not None
            # SimpleNamespace.id 是字符串（缓存值），可被 str() 安全访问
            assert str(deleted_tab.id) == str(tab_id)
            assert deleted_tab.tab_key == tab_key

            # [关键] 数据库删除验证
            fetched_tab = await crud_live_features.get_tab(db, tab_id)
            assert fetched_tab is None


class TestLiveRoomMessageCRUD:
    """LiveRoomMessage CRUD 操作测试"""

    @pytest.mark.asyncio
    async def test_create_message_success(self, db_session):
        """测试成功创建留言"""
        async for db in db_session:
            # 1. 准备 (Arrange)
            # 创建 LiveRoom 依赖
            room = LiveRoom(
                id=uuid.uuid4(),
                user_id=uuid.uuid4(),
                title=f"Test Room {uuid.uuid4().hex[:8]}",
                stream_key=f"stream_{uuid.uuid4().hex}"
            )
            db.add(room)
            await db.commit()
            
            # 创建 LiveSession 依赖
            session = LiveSession(
                id=uuid.uuid4(),
                room_id=room.id,
                status=LiveSessionStatus.LIVE,
                start_time=datetime.utcnow()
            )
            db.add(session)
            await db.commit()
            await db.refresh(session)
            
            # 准备留言数据
            obj_in = LiveRoomMessageCreateInternal(
                room_id=room.id,
                session_id=session.id,
                user_id=uuid.uuid4(),
                user_role=LiveRoomMessageUserRole.REGULAR,
                content=fake.text(max_nb_chars=100)
            )
            
            # 2. 执行 (Act)
            new_message = await crud_live_features.create_message(db, obj_in)
            
            # 3. 断言 (Assert)
            assert new_message is not None
            assert isinstance(new_message.id, uuid.UUID)
            assert new_message.room_id == obj_in.room_id
            assert new_message.user_id == obj_in.user_id
            assert new_message.user_role == obj_in.user_role
            assert new_message.content == obj_in.content
            assert new_message.is_deleted is False
            assert new_message.created_at is not None

    @pytest.mark.asyncio
    async def test_create_message_without_session_id(self, db_session):
        """测试创建留言时session_id可选"""
        async for db in db_session:
            # 1. 准备 (Arrange)
            room = LiveRoom(
                id=uuid.uuid4(),
                user_id=uuid.uuid4(),
                title=f"Test Room {uuid.uuid4().hex[:8]}",
                stream_key=f"stream_{uuid.uuid4().hex}"
            )
            db.add(room)
            await db.commit()
            
            obj_in = LiveRoomMessageCreateInternal(
                room_id=room.id,
                session_id=None,
                user_id=uuid.uuid4(),
                user_role=LiveRoomMessageUserRole.REGULAR,
                content="测试留言"
            )
            
            # 2. 执行 (Act)
            new_message = await crud_live_features.create_message(db, obj_in)
            
            # 3. 断言 (Assert)
            assert new_message is not None
            assert new_message.session_id is None

    @pytest.mark.asyncio
    async def test_create_message_with_invalid_room_id_raises_integrity_error(self, db_session):
        """
        测试使用无效room_id创建留言引发完整性错误
        
        注意：如果外键约束没有被正确创建，此测试可能会失败。
        这是数据库配置问题，不是代码问题。
        """
        async for db in db_session:
            # 1. 准备 (Arrange)
            invalid_room_id = uuid.uuid4()
            obj_in = LiveRoomMessageCreateInternal(
                room_id=invalid_room_id,
                session_id=None,
                user_id=uuid.uuid4(),
                user_role=LiveRoomMessageUserRole.REGULAR,
                content="测试留言"
            )
            
            # 2. 执行 & 断言 (Act & Assert)
            # 注意：create_message 内部会执行 commit，如果外键约束存在，应该会抛出 IntegrityError
            # 但如果约束没有被正确创建，操作会成功，测试会失败
            try:
                result = await crud_live_features.create_message(db, obj_in)
                # 如果操作成功，说明外键约束没有被正确创建，这是一个数据库配置问题
                # 我们仍然标记为失败，但提供更清晰的错误信息
                pytest.fail(
                    f"Expected IntegrityError but operation succeeded. "
                    f"This indicates that foreign key constraints may not be properly created in the test database. "
                    f"Created message_id: {result.id}, room_id: {invalid_room_id}"
                )
            except IntegrityError:
                # 预期的行为：外键约束应该阻止使用无效的 room_id
                pass

    @pytest.mark.asyncio
    async def test_get_messages_by_room_success(self, db_session):
        """测试成功分页获取房间留言"""
        async for db in db_session:
            # 1. 准备 (Arrange)
            room = LiveRoom(
                id=uuid.uuid4(),
                user_id=uuid.uuid4(),
                title=f"Test Room {uuid.uuid4().hex[:8]}",
                stream_key=f"stream_{uuid.uuid4().hex}"
            )
            db.add(room)
            await db.commit()
            
            user_id = uuid.uuid4()
            
            # 创建5个留言（显式递增 created_at，使排序断言可区分：间隔 1 分钟；timestamptz 需 aware 时间）
            now = datetime.now(timezone.utc)
            for i in range(5):
                message = LiveRoomMessage(
                    id=uuid.uuid4(),
                    room_id=room.id,
                    session_id=None,
                    user_id=user_id,
                    user_role=LiveRoomMessageUserRole.REGULAR,
                    content=f"留言 {i}",
                    created_at=now + timedelta(minutes=i),
                    is_deleted=False
                )
                db.add(message)
            await db.commit()
            
            # 2. 执行 (Act)
            messages, total = await crud_live_features.get_messages_by_room(
                db, room.id, page=1, size=10, since=None
            )
            
            # 3. 断言 (Assert)
            assert total == 5
            assert len(messages) == 5
            # [契约 v2.0] 排序验证 - 页内按 created_at 升序（旧→新，页尾=窗口最新；
            # 分页窗口仍为 DESC：page1=最新窗口、page 递增向更早）
            for i in range(len(messages) - 1):
                assert messages[i].created_at <= messages[i + 1].created_at
            # [契约 v2.0] 升序下首条=最早插入（"留言 0"）、末条=最新插入（"留言 4"）
            assert messages[0].content == "留言 0"
            assert messages[-1].content == "留言 4"
            # [关键] 软删除过滤
            for msg in messages:
                assert msg.is_deleted is False

    @pytest.mark.asyncio
    async def test_get_messages_by_room_pagination(self, db_session):
        """测试留言分页功能"""
        async for db in db_session:
            # 1. 准备 (Arrange)
            room = LiveRoom(
                id=uuid.uuid4(),
                user_id=uuid.uuid4(),
                title=f"Test Room {uuid.uuid4().hex[:8]}",
                stream_key=f"stream_{uuid.uuid4().hex}"
            )
            db.add(room)
            await db.commit()
            
            # 创建10个留言
            for i in range(10):
                message = LiveRoomMessage(
                    id=uuid.uuid4(),
                    room_id=room.id,
                    session_id=None,
                    user_id=uuid.uuid4(),
                    user_role=LiveRoomMessageUserRole.REGULAR,
                    content=f"留言 {i}",
                    is_deleted=False
                )
                db.add(message)
            await db.commit()
            
            # 2. 执行 (Act)
            messages, total = await crud_live_features.get_messages_by_room(
                db, room.id, page=2, size=3, since=None
            )
            
            # 3. 断言 (Assert)
            assert total == 10
            assert len(messages) == 3  # 第4-6条

    @pytest.mark.asyncio
    async def test_get_messages_by_room_with_since_filter(self, db_session):
        """测试时间过滤功能"""
        async for db in db_session:
            # 1. 准备 (Arrange)
            room = LiveRoom(
                id=uuid.uuid4(),
                user_id=uuid.uuid4(),
                title=f"Test Room {uuid.uuid4().hex[:8]}",
                stream_key=f"stream_{uuid.uuid4().hex}"
            )
            db.add(room)
            await db.commit()
            
            now = datetime.utcnow()
            middle_time = now - timedelta(hours=1)
            
            # 创建3个留言，手动设置时间
            for i, time_delta in enumerate([timedelta(hours=2), timedelta(hours=1), timedelta(minutes=30)]):
                message = LiveRoomMessage(
                    id=uuid.uuid4(),
                    room_id=room.id,
                    session_id=None,
                    user_id=uuid.uuid4(),
                    user_role=LiveRoomMessageUserRole.REGULAR,
                    content=f"留言 {i}",
                    is_deleted=False,
                    created_at=now - time_delta
                )
                db.add(message)
            await db.commit()
            
            # 2. 执行 (Act)
            messages, total = await crud_live_features.get_messages_by_room(
                db, room.id, page=1, size=10, since=middle_time
            )
            
            # 3. 断言 (Assert)
            # 只有最后一条留言在middle_time之后
            assert total == 1
            assert len(messages) == 1

    @pytest.mark.asyncio
    async def test_get_messages_by_room_excludes_deleted(self, db_session):
        """测试软删除过滤"""
        async for db in db_session:
            # 1. 准备 (Arrange)
            room = LiveRoom(
                id=uuid.uuid4(),
                user_id=uuid.uuid4(),
                title=f"Test Room {uuid.uuid4().hex[:8]}",
                stream_key=f"stream_{uuid.uuid4().hex}"
            )
            db.add(room)
            await db.commit()
            
            # 创建3个留言：2个未删除，1个已删除
            for i in range(3):
                message = LiveRoomMessage(
                    id=uuid.uuid4(),
                    room_id=room.id,
                    session_id=None,
                    user_id=uuid.uuid4(),
                    user_role=LiveRoomMessageUserRole.REGULAR,
                    content=f"留言 {i}",
                    is_deleted=(i == 2)  # 第3个标记为删除
                )
                db.add(message)
            await db.commit()
            
            # 2. 执行 (Act)
            messages, total = await crud_live_features.get_messages_by_room(
                db, room.id, page=1, size=10, since=None
            )
            
            # 3. 断言 (Assert)
            assert total == 2  # 排除已删除
            assert len(messages) == 2
            for msg in messages:
                assert msg.is_deleted is False

    @pytest.mark.asyncio
    async def test_get_messages_by_room_empty(self, db_session):
        """测试获取空房间的留言列表"""
        async for db in db_session:
            # 1. 准备 (Arrange)
            room = LiveRoom(
                id=uuid.uuid4(),
                user_id=uuid.uuid4(),
                title=f"Test Room {uuid.uuid4().hex[:8]}",
                stream_key=f"stream_{uuid.uuid4().hex}"
            )
            db.add(room)
            await db.commit()
            
            # 2. 执行 (Act)
            messages, total = await crud_live_features.get_messages_by_room(
                db, room.id, page=1, size=10, since=None
            )
            
            # 3. 断言 (Assert)
            assert total == 0
            assert len(messages) == 0

