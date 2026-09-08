"""
直播间 Tab 公开端点 API 层测试（实用派）

测试公开端点 GET /api/v1/rooms/{room_id}/tabs 的权限和功能：
- 匿名用户访问公开/私有房间
- 登录用户访问别人公开/私有房间
- 创建者访问自己私有房间
- Admin 访问任意房间
- is_active 过滤验证
- sort_order 排序验证
"""

import pytest
import uuid
from faker import Faker

from app.models.live_core import LiveRoom
from app.models.live_features import LiveRoomTab, LiveRoomTabContentType

fake = Faker()


# ==================== 公开端点：GET /api/v1/rooms/{room_id}/tabs ====================

@pytest.mark.asyncio
async def test_public_list_tabs_anonymous_public_room(async_client, db_session):
    """匿名用户访问公开房间 → 200，返回激活的 Tab"""
    async for client in async_client:
        async for db in db_session:
            # ===== Arrange =====
            room = LiveRoom(
                id=uuid.uuid4(),
                user_id=uuid.uuid4(),
                title=f"Public Room {uuid.uuid4().hex[:8]}",
                stream_key=f"stream_{uuid.uuid4().hex}",
                is_private=False
            )
            db.add(room)
            await db.commit()

            tab = LiveRoomTab(
                id=uuid.uuid4(),
                room_id=room.id,
                tab_key=f"intro_{uuid.uuid4().hex[:8]}",
                title="直播介绍",
                content_type=LiveRoomTabContentType.TEXT,
                text_content="测试内容",
                sort_order=0,
                is_active=True
            )
            db.add(tab)
            await db.commit()

            # ===== Act =====
            response = await client.get(f"/api/v1/rooms/{room.id}/tabs")

            # ===== Assert =====
            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 200
            assert data["data"]["total"] == 1
            assert len(data["data"]["items"]) == 1
            assert data["data"]["items"][0]["tab_key"] == tab.tab_key
            assert data["data"]["items"][0]["is_active"] is True


@pytest.mark.asyncio
async def test_public_list_tabs_anonymous_private_room(async_client, db_session):
    """匿名用户访问私有房间 → 200（unlisted：持链可读，2026-08-11 V1.1 决策 D1）"""
    async for client in async_client:
        async for db in db_session:
            # ===== Arrange =====
            room = LiveRoom(
                id=uuid.uuid4(),
                user_id=uuid.uuid4(),
                title=f"Private Room {uuid.uuid4().hex[:8]}",
                stream_key=f"stream_{uuid.uuid4().hex}",
                is_private=True
            )
            db.add(room)
            await db.commit()

            # ===== Act =====
            response = await client.get(f"/api/v1/rooms/{room.id}/tabs")

            # ===== Assert =====
            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 200
            assert data["data"]["total"] == 0


@pytest.mark.asyncio
async def test_public_list_tabs_regular_other_public_room(
    async_client, db_session, regular_user_token, another_user_id
):
    """登录用户（非创建者）访问别人公开房间 → 200"""
    async for client in async_client:
        async for db in db_session:
            # ===== Arrange =====
            room = LiveRoom(
                id=uuid.uuid4(),
                user_id=another_user_id,
                title=f"Other Public Room {uuid.uuid4().hex[:8]}",
                stream_key=f"stream_{uuid.uuid4().hex}",
                is_private=False
            )
            db.add(room)
            await db.commit()

            tab = LiveRoomTab(
                id=uuid.uuid4(),
                room_id=room.id,
                tab_key=f"agenda_{uuid.uuid4().hex[:8]}",
                title="本期议程",
                content_type=LiveRoomTabContentType.TEXT,
                text_content="议程内容",
                sort_order=0,
                is_active=True
            )
            db.add(tab)
            await db.commit()

            headers = {"Authorization": f"Bearer {regular_user_token}"}

            # ===== Act =====
            response = await client.get(
                f"/api/v1/rooms/{room.id}/tabs", headers=headers
            )

            # ===== Assert =====
            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 200
            assert data["data"]["total"] == 1


@pytest.mark.asyncio
async def test_public_list_tabs_regular_other_private_room(
    async_client, db_session, regular_user_token, another_user_id
):
    """登录用户（非创建者）访问别人私有房间 → 200（unlisted：持链可读）"""
    async for client in async_client:
        async for db in db_session:
            # ===== Arrange =====
            room = LiveRoom(
                id=uuid.uuid4(),
                user_id=another_user_id,
                title=f"Other Private Room {uuid.uuid4().hex[:8]}",
                stream_key=f"stream_{uuid.uuid4().hex}",
                is_private=True
            )
            db.add(room)
            await db.commit()

            headers = {"Authorization": f"Bearer {regular_user_token}"}

            # ===== Act =====
            response = await client.get(
                f"/api/v1/rooms/{room.id}/tabs", headers=headers
            )

            # ===== Assert =====
            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 200
            assert data["data"]["total"] == 0


@pytest.mark.asyncio
async def test_public_list_tabs_owner_private_room(
    async_client, db_session, regular_user_token, regular_user_id
):
    """创建者访问自己私有房间 → 200"""
    async for client in async_client:
        async for db in db_session:
            # ===== Arrange =====
            room = LiveRoom(
                id=uuid.uuid4(),
                user_id=regular_user_id,
                title=f"Owner Private Room {uuid.uuid4().hex[:8]}",
                stream_key=f"stream_{uuid.uuid4().hex}",
                is_private=True
            )
            db.add(room)
            await db.commit()

            tab = LiveRoomTab(
                id=uuid.uuid4(),
                room_id=room.id,
                tab_key=f"poster_{uuid.uuid4().hex[:8]}",
                title="会议海报",
                content_type=LiveRoomTabContentType.IMAGE,
                image_url="/media/rooms/test/poster.jpg",
                sort_order=0,
                is_active=True
            )
            db.add(tab)
            await db.commit()

            headers = {"Authorization": f"Bearer {regular_user_token}"}

            # ===== Act =====
            response = await client.get(
                f"/api/v1/rooms/{room.id}/tabs", headers=headers
            )

            # ===== Assert =====
            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 200
            assert data["data"]["total"] == 1
            assert data["data"]["items"][0]["content_type"] == "image"


@pytest.mark.asyncio
async def test_public_list_tabs_admin_private_room(
    async_client, db_session, admin_user_token, another_user_id
):
    """Admin 访问别人私有房间 → 200"""
    async for client in async_client:
        async for db in db_session:
            # ===== Arrange =====
            room = LiveRoom(
                id=uuid.uuid4(),
                user_id=another_user_id,
                title=f"Admin Access Room {uuid.uuid4().hex[:8]}",
                stream_key=f"stream_{uuid.uuid4().hex}",
                is_private=True
            )
            db.add(room)
            await db.commit()

            tab = LiveRoomTab(
                id=uuid.uuid4(),
                room_id=room.id,
                tab_key=f"intro_{uuid.uuid4().hex[:8]}",
                title="课程简介",
                content_type=LiveRoomTabContentType.TEXT,
                text_content="简介内容",
                sort_order=0,
                is_active=True
            )
            db.add(tab)
            await db.commit()

            headers = {"Authorization": f"Bearer {admin_user_token}"}

            # ===== Act =====
            response = await client.get(
                f"/api/v1/rooms/{room.id}/tabs", headers=headers
            )

            # ===== Assert =====
            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 200
            assert data["data"]["total"] == 1


@pytest.mark.asyncio
async def test_public_list_tabs_only_active(async_client, db_session):
    """公开房间：只返回 is_active=True 的 Tab，不返回未激活的"""
    async for client in async_client:
        async for db in db_session:
            # ===== Arrange =====
            room = LiveRoom(
                id=uuid.uuid4(),
                user_id=uuid.uuid4(),
                title=f"Filter Room {uuid.uuid4().hex[:8]}",
                stream_key=f"stream_{uuid.uuid4().hex}",
                is_private=False
            )
            db.add(room)
            await db.commit()

            active_tab = LiveRoomTab(
                id=uuid.uuid4(),
                room_id=room.id,
                tab_key=f"active_{uuid.uuid4().hex[:8]}",
                title="激活 Tab",
                content_type=LiveRoomTabContentType.TEXT,
                text_content="激活",
                sort_order=0,
                is_active=True
            )
            db.add(active_tab)

            inactive_tab = LiveRoomTab(
                id=uuid.uuid4(),
                room_id=room.id,
                tab_key=f"inactive_{uuid.uuid4().hex[:8]}",
                title="未激活 Tab",
                content_type=LiveRoomTabContentType.TEXT,
                text_content="未激活",
                sort_order=1,
                is_active=False
            )
            db.add(inactive_tab)
            await db.commit()

            # ===== Act =====
            response = await client.get(f"/api/v1/rooms/{room.id}/tabs")

            # ===== Assert =====
            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 200
            assert data["data"]["total"] == 1
            assert data["data"]["items"][0]["is_active"] is True
            assert data["data"]["items"][0]["title"] == "激活 Tab"


@pytest.mark.asyncio
async def test_public_list_tabs_sort_order(async_client, db_session):
    """公开房间：验证按 sort_order 升序排列"""
    async for client in async_client:
        async for db in db_session:
            # ===== Arrange =====
            room = LiveRoom(
                id=uuid.uuid4(),
                user_id=uuid.uuid4(),
                title=f"Sort Room {uuid.uuid4().hex[:8]}",
                stream_key=f"stream_{uuid.uuid4().hex}",
                is_private=False
            )
            db.add(room)
            await db.commit()

            # 按乱序创建：sort_order = 2, 0, 1
            tab2 = LiveRoomTab(
                id=uuid.uuid4(), room_id=room.id,
                tab_key=f"tab2_{uuid.uuid4().hex[:8]}", title="Tab 2",
                content_type=LiveRoomTabContentType.TEXT, text_content="C",
                sort_order=2, is_active=True
            )
            db.add(tab2)

            tab0 = LiveRoomTab(
                id=uuid.uuid4(), room_id=room.id,
                tab_key=f"tab0_{uuid.uuid4().hex[:8]}", title="Tab 0",
                content_type=LiveRoomTabContentType.TEXT, text_content="A",
                sort_order=0, is_active=True
            )
            db.add(tab0)

            tab1 = LiveRoomTab(
                id=uuid.uuid4(), room_id=room.id,
                tab_key=f"tab1_{uuid.uuid4().hex[:8]}", title="Tab 1",
                content_type=LiveRoomTabContentType.TEXT, text_content="B",
                sort_order=1, is_active=True
            )
            db.add(tab1)
            await db.commit()

            # ===== Act =====
            response = await client.get(f"/api/v1/rooms/{room.id}/tabs")

            # ===== Assert =====
            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 200
            assert data["data"]["total"] == 3

            items = data["data"]["items"]
            sort_orders = [item["sort_order"] for item in items]
            assert sort_orders == [0, 1, 2], f"Expected [0,1,2] got {sort_orders}"
