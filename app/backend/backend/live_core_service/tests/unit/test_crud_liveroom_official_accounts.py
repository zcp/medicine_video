"""
直播间与公众号关联模块 - CRUD 层测试
测试策略: Pragmatic（真实数据库）
"""
import pytest
from uuid import uuid4, UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.liveroom_official_accounts import OfficialAccount, LiveRoomOfficialAccount
from app.models.live_core import LiveRoom
from app.schemas.liveroom_official_accounts import OfficialAccountCreate, OfficialAccountUpdate
from app.crud import liveroom_official_accounts as crud_oa
from app.core.exceptions import DatabaseIntegrityException


async def _create_test_room(db: AsyncSession) -> LiveRoom:
    """创建测试用 LiveRoom"""
    room = LiveRoom(
        id=uuid4(),
        user_id=uuid4(),
        title=f"测试房间_{uuid4().hex[:8]}",
        stream_key=f"stream_key_{uuid4().hex[:16]}",
        is_private=False,
        record_by_default=True,
    )
    db.add(room)
    await db.flush()
    return room


# ---------- 公众号 CRUD ----------


@pytest.mark.asyncio
async def test_get_paginated_official_accounts_default(db_session):
    """分页列表默认不包含 is_active=False"""
    async for db in db_session:
        a1 = OfficialAccount(id=uuid4(), name=f"公众号_{uuid4().hex[:8]}", is_active=True)
        a2 = OfficialAccount(id=uuid4(), name=f"公众号_{uuid4().hex[:8]}", is_active=False)
        db.add_all([a1, a2])
        await db.flush()

        total, items = await crud_oa.get_paginated_official_accounts(db, page=1, size=10, include_inactive=False)
        assert total >= 1
        assert all(acc.is_active for acc in items)


@pytest.mark.asyncio
async def test_get_paginated_official_accounts_include_inactive(db_session):
    """include_inactive=True 时包含禁用公众号"""
    async for db in db_session:
        suffix = uuid4().hex[:8]
        a1 = OfficialAccount(id=uuid4(), name=f"公众号_{suffix}", is_active=True)
        a2 = OfficialAccount(id=uuid4(), name=f"公众号_b_{suffix}", is_active=False)
        db.add_all([a1, a2])
        await db.flush()

        total, items = await crud_oa.get_paginated_official_accounts(db, page=1, size=10, include_inactive=True)
        names = [acc.name for acc in items]
        assert f"公众号_{suffix}" in names
        assert f"公众号_b_{suffix}" in names


@pytest.mark.asyncio
async def test_get_official_account_by_id_exists(db_session):
    """按 id 查存在返回对象"""
    async for db in db_session:
        acc = OfficialAccount(id=uuid4(), name=f"公众号_{uuid4().hex[:8]}", is_active=True)
        db.add(acc)
        await db.flush()

        found = await crud_oa.get_official_account_by_id(db, acc.id)
        assert found is not None
        assert found.id == acc.id
        assert found.name == acc.name


@pytest.mark.asyncio
async def test_get_official_account_by_id_not_exists(db_session):
    """按 id 查不存在返回 None"""
    async for db in db_session:
        found = await crud_oa.get_official_account_by_id(db, uuid4())
        assert found is None


@pytest.mark.asyncio
async def test_create_official_account_success(db_session):
    """创建公众号成功，再次查询验证字段"""
    async for db in db_session:
        body = OfficialAccountCreate(name=f"新公众号_{uuid4().hex[:8]}", slug="new-oa", is_active=True)
        created = await crud_oa.create_official_account(db, body)
        assert created.id is not None
        assert created.name == body.name
        assert created.is_active is True

        found = await crud_oa.get_official_account_by_id(db, created.id)
        assert found is not None
        assert found.name == created.name


@pytest.mark.asyncio
async def test_create_official_account_duplicate_name(db_session):
    """同名创建触发 DatabaseIntegrityException"""
    async for db in db_session:
        name = f"唯一名_{uuid4().hex[:8]}"
        db.add(OfficialAccount(id=uuid4(), name=name, is_active=True))
        await db.flush()

        with pytest.raises(DatabaseIntegrityException):
            await crud_oa.create_official_account(db, OfficialAccountCreate(name=name, is_active=True))


@pytest.mark.asyncio
async def test_update_official_account_success(db_session):
    """部分更新后再次查询验证"""
    async for db in db_session:
        acc = OfficialAccount(id=uuid4(), name=f"公众号_{uuid4().hex[:8]}", is_active=True)
        db.add(acc)
        await db.flush()

        body = OfficialAccountUpdate(description="更新后的描述")
        updated = await crud_oa.update_official_account(db, acc.id, body)
        assert updated is not None
        assert updated.description == "更新后的描述"

        found = await crud_oa.get_official_account_by_id(db, acc.id)
        assert found.description == "更新后的描述"


@pytest.mark.asyncio
async def test_soft_delete_official_account(db_session):
    """软删除后 is_active=False"""
    async for db in db_session:
        acc = OfficialAccount(id=uuid4(), name=f"公众号_{uuid4().hex[:8]}", is_active=True)
        db.add(acc)
        await db.flush()

        ok = await crud_oa.soft_delete_official_account(db, acc.id)
        assert ok is True

        found = await crud_oa.get_official_account_by_id(db, acc.id)
        assert found is not None
        assert found.is_active is False


# ---------- 房间-公众号关联 CRUD ----------


@pytest.mark.asyncio
async def test_get_official_accounts_by_room_id(db_session):
    """按房间查公众号列表"""
    async for db in db_session:
        room = await _create_test_room(db)
        acc = OfficialAccount(id=uuid4(), name=f"公众号_{uuid4().hex[:8]}", is_active=True)
        db.add(acc)
        await db.flush()
        link = LiveRoomOfficialAccount(room_id=room.id, account_id=acc.id)
        db.add(link)
        await db.flush()

        items = await crud_oa.get_official_accounts_by_room_id(db, room.id)
        assert len(items) >= 1
        assert any(a.id == acc.id for a in items)


@pytest.mark.asyncio
async def test_set_room_official_accounts_replace(db_session):
    """replace 模式：先删后插，最终仅含新列表"""
    async for db in db_session:
        room = await _create_test_room(db)
        a1 = OfficialAccount(id=uuid4(), name=f"公众号_a_{uuid4().hex[:8]}", is_active=True)
        a2 = OfficialAccount(id=uuid4(), name=f"公众号_b_{uuid4().hex[:8]}", is_active=True)
        db.add_all([a1, a2])
        await db.flush()
        db.add(LiveRoomOfficialAccount(room_id=room.id, account_id=a1.id))
        await db.flush()

        await crud_oa.set_room_official_accounts(db, room.id, [a2.id], "replace")
        items = await crud_oa.get_official_accounts_by_room_id(db, room.id)
        assert len(items) == 1
        assert items[0].id == a2.id


@pytest.mark.asyncio
async def test_set_room_official_accounts_append(db_session):
    """append 模式：仅追加不重复"""
    async for db in db_session:
        room = await _create_test_room(db)
        a1 = OfficialAccount(id=uuid4(), name=f"公众号_{uuid4().hex[:8]}", is_active=True)
        a2 = OfficialAccount(id=uuid4(), name=f"公众号_2_{uuid4().hex[:8]}", is_active=True)
        db.add_all([a1, a2])
        await db.flush()

        await crud_oa.set_room_official_accounts(db, room.id, [a1.id], "append")
        await crud_oa.set_room_official_accounts(db, room.id, [a1.id, a2.id], "append")
        items = await crud_oa.get_official_accounts_by_room_id(db, room.id)
        assert len(items) == 2


@pytest.mark.asyncio
async def test_delete_room_official_account(db_session):
    """删除单条关联后列表少一条"""
    async for db in db_session:
        room = await _create_test_room(db)
        acc = OfficialAccount(id=uuid4(), name=f"公众号_{uuid4().hex[:8]}", is_active=True)
        db.add(acc)
        await db.flush()
        db.add(LiveRoomOfficialAccount(room_id=room.id, account_id=acc.id))
        await db.flush()

        ok = await crud_oa.delete_room_official_account(db, room.id, acc.id)
        assert ok is True
        items = await crud_oa.get_official_accounts_by_room_id(db, room.id)
        assert not any(a.id == acc.id for a in items)


@pytest.mark.asyncio
async def test_get_rooms_by_account_id_paginated(db_session):
    """按公众号分页查房间：total + items"""
    async for db in db_session:
        room = await _create_test_room(db)
        acc = OfficialAccount(id=uuid4(), name=f"公众号_{uuid4().hex[:8]}", is_active=True)
        db.add(acc)
        await db.flush()
        db.add(LiveRoomOfficialAccount(room_id=room.id, account_id=acc.id))
        await db.flush()

        total, rooms = await crud_oa.get_rooms_by_account_id_paginated(db, acc.id, page=1, size=10)
        assert total >= 1
        assert len(rooms) >= 1
        assert rooms[0].id == room.id
        assert hasattr(rooms[0], "title")
