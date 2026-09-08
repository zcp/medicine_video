"""
LiveCore Service - CRUD Room Unit Tests

This module contains detailed unit tests for the room CRUD operations.
"""

import pytest
import uuid
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import room as crud_room
from app.schemas.live_core import LiveRoomCreate, LiveRoomUpdate
from app.models.live_core import LiveRoom, LiveSession, LiveSessionStatus
from app.models.content_management import Category, LiveRoomCategory
from app.models.liveroom_official_accounts import OfficialAccount, LiveRoomOfficialAccount



@pytest.mark.asyncio
async def test_create_room(db_session, test_user):
    """
    测试创建房间功能
    - 准备: 创建LiveRoomCreate对象
    - 执行: 调用crud.room.create()
    - 断言: 验证返回值和数据库状态
    """
    async for db in db_session:
        async for user in test_user:
            # 准备测试数据
            room_data = LiveRoomCreate(
                title="测试直播房间",
                description="这是一个测试房间",
                cover_url="https://example.com/cover.jpg",
                is_private=False,
                record_by_default=True,
                category_id=uuid.uuid4(),
                parent_room_id=None,
                user_id=user['public_id']
            )

            # 执行创建操作
            created_room = await crud_room.create(db=db, obj_in=room_data, user_id = user['public_id'])

            # 断言返回值
            assert created_room is not None
            assert created_room.title == room_data.title
            assert created_room.description == room_data.description
            assert created_room.cover_url == room_data.cover_url
            assert created_room.is_private == room_data.is_private
            assert created_room.record_by_default == room_data.record_by_default
            assert created_room.category_id == room_data.category_id
            assert created_room.user_id == room_data.user_id
            assert created_room.stream_key is not None
            assert created_room.stream_key.startswith("streamkey_")
            assert created_room.id is not None
            assert created_room.created_at is not None
            assert created_room.updated_at is not None

            # 验证数据库状态 - 重新从数据库获取记录
            db_room = await crud_room.get(db=db, room_id=created_room.id)
            assert db_room is not None
            assert db_room.id == created_room.id
            assert db_room.title == room_data.title
            assert db_room.description == room_data.description
            assert db_room.stream_key == created_room.stream_key


@pytest.mark.asyncio
async def test_get_room(db_session, test_user):
    """
    测试获取房间功能
    - 准备: 先创建一个房间
    - 执行: 调用crud.room.get()
    - 断言: 验证返回的对象正确
    """
    async for db in db_session:
        async for user in test_user:
            # 准备 - 先创建一个房间
            room_data = LiveRoomCreate(
                title="获取测试房间",
                description="用于测试获取功能",
                is_private=True,
                record_by_default=False
            )
            created_room = await crud_room.create(db=db, obj_in=room_data, user_id = user['public_id'])

            # 执行获取操作
            retrieved_room = await crud_room.get(db=db, room_id=created_room.id)

            # 断言
            assert retrieved_room is not None
            assert retrieved_room.id == created_room.id
            assert retrieved_room.title == created_room.title
            assert retrieved_room.description == created_room.description
            assert retrieved_room.is_private == created_room.is_private
            assert retrieved_room.record_by_default == created_room.record_by_default


@pytest.mark.asyncio
async def test_get_non_existent_room(db_session, test_user):
    """
    测试获取不存在的房间
    - 准备: 生成随机UUID
    - 执行: 调用crud.room.get()
    - 断言: 返回None
    """
    async for db in db_session:
        async for user in test_user:
            # 准备 - 生成随机UUID
            random_id = uuid.uuid4()

            # 执行获取操作
            result = await crud_room.get(db=db, room_id=random_id, user_id = user['public_id'])

            # 断言
            assert result is None


@pytest.mark.asyncio
async def test_update_room(db_session, test_user):
    """
    测试更新房间功能
    - 准备: 创建房间和更新数据
    - 执行: 调用crud.room.update()
    - 断言: 验证返回值和数据库状态
    """
    async for db in db_session:
        async for user in test_user:
            # 准备 - 创建初始房间
            initial_data = LiveRoomCreate(
                title="原始标题",
                description="原始描述",
                is_private=False,
                record_by_default=True
            )
            created_room = await crud_room.create(db=db, obj_in=initial_data, user_id = user['public_id'])

            # 准备更新数据
            update_data = LiveRoomUpdate(
                title="更新后的标题",
                description="更新后的描述",
                is_private=True
            )

            # 执行更新操作
            updated_room = await crud_room.update(
                db=db,
                db_obj=created_room,
                obj_in=update_data
            )

            # 断言返回值
            assert updated_room is not None
            assert updated_room.id == created_room.id
            assert updated_room.title == "更新后的标题"
            assert updated_room.description == "更新后的描述"
            assert updated_room.is_private == True
            assert updated_room.record_by_default == True  # 未更新的字段保持原值

            # 验证数据库状态 - 重新从数据库获取记录
            db_room = await crud_room.get(db=db, room_id=created_room.id, user_id = user['public_id'])
            assert db_room is not None
            assert db_room.title == "更新后的标题"
            assert db_room.description == "更新后的描述"
            assert db_room.is_private == True


@pytest.mark.asyncio
async def test_remove_room(db_session, test_user):
    """
    测试删除房间功能
    - 准备: 创建房间并记录ID
    - 执行: 调用crud.room.remove()
    - 断言: 验证数据库中记录已删除
    """
    async for db in db_session:
        async for user in test_user:
            # 准备 - 创建房间
            room_data = LiveRoomCreate(
                title="待删除房间",
                description="这个房间将被删除"
            )
            created_room = await crud_room.create(db=db, obj_in=room_data, user_id = user['public_id'])
            room_id = created_room.id

            # 执行删除操作
            deleted_room = await crud_room.remove(db=db, db_obj=created_room, user_id = user['public_id'])

            # 断言返回值
            assert deleted_room is not None
            assert deleted_room.id == room_id

            # 验证数据库状态 - 记录应该已被删除
            db_room = await crud_room.get(db=db, room_id=room_id, user_id = user['public_id'])
            assert db_room is None


@pytest.mark.asyncio
async def test_get_multi_and_total(db_session, test_user):
    """
    测试分页获取房间列表功能
    - 准备: 创建多个房间
    - 执行: 调用crud.room.get_multi_and_total()
    - 断言: 验证分页结果正确
    """
    async for db in db_session:
        async for user in test_user:
            # 准备 - 创建多个房间
            rooms_data = [
                LiveRoomCreate(title=f"房间{i}", description=f"描述{i}")
                for i in range(5)
            ]

            created_rooms = []
            for room_data in rooms_data:
                room = await crud_room.create(db=db, obj_in=room_data, user_id = user['public_id'])
                created_rooms.append(room)

            # 执行分页查询
            # ← 修改：传递权限参数（匿名用户场景，最严格的过滤）
            rooms, total = await crud_room.get_multi_and_total(
                db=db, 
                skip=0, 
                limit=3,
                user_id=None,  # ← 新增：匿名用户
                role=None      # ← 新增：匿名用户
            )

            # 断言
            assert total >= 5  # 至少有我们创建的5个房间
            assert len(rooms) == 3  # 限制返回3个
            assert all(isinstance(room, LiveRoom) for room in rooms)

            # 测试第二页
            # ← 修改：传递权限参数（匿名用户场景）
            rooms_page2, total_page2 = await crud_room.get_multi_and_total(
                db=db, 
                skip=3, 
                limit=3,
                user_id=None,  # ← 新增：匿名用户
                role=None      # ← 新增：匿名用户
            )

            assert total_page2 == total  # 总数应该一致
            assert len(rooms_page2) >= 2  # 至少还有2个房间


@pytest.mark.asyncio
async def test_is_live_false(db_session,test_user):
    """
    测试房间非直播状态检查
    - 准备: 创建房间但不创建直播会话
    - 执行: 调用crud.room.is_live()
    - 断言: 返回False
    """
    async for db in db_session:
        async for user in test_user:
            # 准备 - 创建房间
            room_data = LiveRoomCreate(
                title="非直播房间",
                description="没有直播会话的房间"
            )
            created_room = await crud_room.create(db=db, obj_in=room_data, user_id = user['public_id'])

            # 执行检查
            is_live = await crud_room.is_live(db=db, room_id=created_room.id)

            # 断言
            assert is_live == False


@pytest.mark.asyncio
async def test_is_live_true(db_session,test_user):
    """
    测试房间直播状态检查
    - 准备: 创建房间和LIVE状态的会话
    - 执行: 调用crud.room.is_live()
    - 断言: 返回True
    """
    async for db in db_session:
        async for user in test_user:
        # 准备 - 创建房间
            room_data = LiveRoomCreate(
                title="直播中房间",
                description="有正在进行的直播会话"
            )
            created_room = await crud_room.create(db=db, obj_in=room_data, user_id = user['public_id'])

            # 创建LIVE状态的会话
            live_session = LiveSession(
                room_id=created_room.id,
                status=LiveSessionStatus.LIVE,
                start_time=datetime.now()
            )
            db.add(live_session)
            await db.commit()

            # 执行检查
            is_live = await crud_room.is_live(db=db, room_id=created_room.id)

            # 断言
            assert is_live == True


@pytest.mark.asyncio
async def test_is_live_false_with_other_status(db_session, test_user):
    """
    测试房间非LIVE状态会话不影响直播检查
    - 准备: 创建房间和非LIVE状态的会话
    - 执行: 调用crud.room.is_live()
    - 断言: 返回False
    """
    async for db in db_session:
        async for user in test_user:
            # 准备 - 创建房间
            room_data = LiveRoomCreate(
                title="非直播房间",
                description="有非LIVE状态会话的房间"
            )
            created_room = await crud_room.create(db=db, obj_in=room_data, user_id = user['public_id'])

            # 创建FINISHED状态的会话
            finished_session = LiveSession(
                room_id=created_room.id,
                status=LiveSessionStatus.FINISHED,
                start_time=datetime.now(),
                end_time=datetime.now()
            )
            db.add(finished_session)
            await db.commit()

            # 执行检查
            is_live = await crud_room.is_live(db=db, room_id=created_room.id)

            # 断言
            assert is_live == False


@pytest.mark.asyncio
async def test_get_sub_venues_with_live_status(db_session, test_user):
    """
    测试获取分会场列表功能
    - 准备: 创建主会场和分会场
    - 执行: 调用crud.room.get_sub_venues_with_live_status()
    - 断言: 验证返回的分会场信息正确
    """
    async for db in db_session:
        async for user in test_user:
            # 准备 - 创建主会场
            main_room_data = LiveRoomCreate(
                title="主会场",
                description="主要会场"
            )
            main_room = await crud_room.create(db=db, obj_in=main_room_data, user_id = user['public_id'])

            # 创建分会场
            sub_room1_data = LiveRoomCreate(
                title="分会场1",
                description="第一个分会场",
                parent_room_id=main_room.id
            )
            sub_room1 = await crud_room.create(db=db, obj_in=sub_room1_data, user_id = user['public_id'])

            sub_room2_data = LiveRoomCreate(
                title="分会场2",
                description="第二个分会场",
                parent_room_id=main_room.id
            )
            sub_room2 = await crud_room.create(db=db, obj_in=sub_room2_data, user_id = user['public_id'])

            # 为分会场1创建LIVE状态会话
            live_session = LiveSession(
                room_id=sub_room1.id,
                status=LiveSessionStatus.LIVE,
                start_time=datetime.now()
            )
            db.add(live_session)
            await db.commit()

            # 执行查询
            sub_venues, total = await crud_room.get_sub_venues_with_live_status(
                db=db, parent_room_id=main_room.id, skip=0, limit=10
            )

            # 断言
            assert total == 2  # 应该有2个分会场
            assert len(sub_venues) == 2

            # 验证分会场信息
            venue_titles = [venue['title'] for venue in sub_venues]
            assert "分会场1" in venue_titles
            assert "分会场2" in venue_titles

            # 验证直播状态
            for venue in sub_venues:
                if venue['title'] == "分会场1":
                    assert venue['live_status'] == LiveSessionStatus.LIVE
                    assert venue['current_session_id'] == live_session.id
                else:
                    assert venue['live_status'] is None
                    assert venue['current_session_id'] is None


@pytest.mark.asyncio
async def test_create_room_with_parent(db_session, test_user):
    """
    测试创建分会场功能
    - 准备: 创建主会场和分会场数据
    - 执行: 调用crud.room.create()
    - 断言: 验证分会场正确关联到主会场
    """
    async for db in db_session:
        async for user in test_user:
            # 准备 - 创建主会场
            main_room_data = LiveRoomCreate(
                title="主会场",
                description="主要会场"
            )
            main_room = await crud_room.create(db=db, obj_in=main_room_data, user_id = user['public_id'])

            # 创建分会场
            sub_room_data = LiveRoomCreate(
                title="分会场",
                description="子会场",
                parent_room_id=main_room.id
            )
            sub_room = await crud_room.create(db=db, obj_in=sub_room_data, user_id = user['public_id'])

            # 断言
            assert sub_room.parent_room_id == main_room.id

            # 验证数据库状态
            db_sub_room = await crud_room.get(db=db, room_id=sub_room.id)
            assert db_sub_room.parent_room_id == main_room.id


# ==================== 以下是新增的封面URL更新测试 ====================

@pytest.mark.asyncio
async def test_update_cover_url_success(db_session, test_user):
    """
    测试更新房间封面URL功能
    - 准备: 创建房间
    - 执行: 调用crud.room.update_cover_url()
    - 断言: 验证返回值和数据库状态
    """
    async for db in db_session:
        async for user in test_user:
            # 准备 - 先创建一个房间
            room_data = LiveRoomCreate(
                title="测试房间",
                description="用于测试封面更新"
            )
            created_room = await crud_room.create(db=db, obj_in=room_data, user_id=user['public_id'])
            
            # 执行更新操作
            new_cover_url = "/media/rooms/{}/cover_1234567890.jpg".format(created_room.id)
            updated_room = await crud_room.update_cover_url(
                db=db,
                room_id=created_room.id,
                cover_url=new_cover_url
            )
            
            # 断言返回值
            assert updated_room is not None
            assert updated_room.id == created_room.id
            assert updated_room.cover_url == new_cover_url
            
            # 验证数据库状态
            db_room = await crud_room.get(db=db, room_id=created_room.id)
            assert db_room.cover_url == new_cover_url


# ==================== delete_room_related 级联删除（科室/公众号关联） ====================

@pytest.mark.asyncio
async def test_delete_room_related_cascades_category_and_official_account(db_session, test_user):
    """
    测试 delete_room_related() 会级联删除科室关联（live_room_categories）与公众号关联（live_room_official_accounts）。
    - 准备: 创建房间、Category、OfficialAccount 及对应关联记录
    - 执行: 调用 crud.room.delete_room_related(db, room_id)
    - 断言: 该 room_id 在 LiveRoomCategory、LiveRoomOfficialAccount 中无记录
    """
    async for db in db_session:
        async for user in test_user:
            room_data = LiveRoomCreate(
                title="级联删除测试房间",
                description="用于测试 delete_room_related",
            )
            created_room = await crud_room.create(db=db, obj_in=room_data, user_id=user["public_id"])
            room_id = created_room.id

            cat = Category(
                id=uuid.uuid4(),
                name=f"科室_{uuid.uuid4().hex[:8]}",
                is_active=True,
            )
            acc = OfficialAccount(
                id=uuid.uuid4(),
                name=f"公众号_{uuid.uuid4().hex[:8]}",
                is_active=True,
            )
            db.add(cat)
            db.add(acc)
            await db.flush()
            db.add(LiveRoomCategory(room_id=room_id, category_id=cat.id))
            db.add(LiveRoomOfficialAccount(room_id=room_id, account_id=acc.id))
            await db.commit()

            await crud_room.delete_room_related(db=db, room_id=room_id)
            await db.commit()

            r = await db.execute(select(LiveRoomCategory).where(LiveRoomCategory.room_id == room_id))
            assert r.scalars().first() is None
            r2 = await db.execute(select(LiveRoomOfficialAccount).where(LiveRoomOfficialAccount.room_id == room_id))
            assert r2.scalars().first() is None