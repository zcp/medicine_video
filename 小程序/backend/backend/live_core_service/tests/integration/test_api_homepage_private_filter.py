"""
文档 18：Homepage / 全局搜索排除 is_private=true
"""

import pytest
import uuid
from datetime import datetime, timezone

from app.models.live_core import LiveRoom, LiveSession, LiveSessionStatus


@pytest.mark.asyncio
async def test_homepage_rooms_excludes_private_even_when_live(
    async_client,
    db_session,
    regular_user_id: uuid.UUID,
    public_room,
):
    """测播间即便有 live 场次也不进 homepage"""
    async for client in async_client:
        async for db in db_session:
            private = LiveRoom(
                title=f"测播连接测试_{uuid.uuid4().hex[:6]}",
                description="should not appear",
                stream_key=f"sk_test_{uuid.uuid4().hex[:12]}",
                is_private=True,
                record_by_default=True,
                user_id=regular_user_id,
            )
            db.add(private)
            await db.flush()

            session = LiveSession(
                room_id=private.id,
                status=LiveSessionStatus.LIVE,
                start_time=datetime.now(timezone.utc),
            )
            db.add(session)
            await db.commit()

            response = await client.get("/api/v1/homepage/rooms?page=1&size=100")
            assert response.status_code == 200
            body = response.json()
            assert body["code"] == 200
            items = body["data"]["items"]
            ids = [str(item.get("id")) for item in items if item.get("id")]
            assert str(private.id) not in ids
            break
        break


@pytest.mark.asyncio
async def test_global_search_excludes_private_rooms(
    async_client,
    db_session,
    regular_user_id: uuid.UUID,
):
    """全局搜索 room 类型不返回不公开房"""
    keyword = f"UnlistedSearch_{uuid.uuid4().hex[:8]}"
    async for client in async_client:
        async for db in db_session:
            private = LiveRoom(
                title=keyword,
                description="private search bait",
                stream_key=f"sk_test_{uuid.uuid4().hex[:12]}",
                is_private=True,
                record_by_default=True,
                user_id=regular_user_id,
            )
            public = LiveRoom(
                title=keyword,
                description="public search bait",
                stream_key=f"sk_pub_{uuid.uuid4().hex[:12]}",
                is_private=False,
                record_by_default=True,
                user_id=regular_user_id,
            )
            db.add(private)
            db.add(public)
            await db.commit()

            response = await client.get(
                "/api/v1/search",
                params={"q": keyword, "page": 1, "size": 50},
            )
            assert response.status_code == 200
            items = response.json()["data"]["items"]
            all_ids = [str(i.get("id")) for i in items if i.get("id")]
            assert str(private.id) not in all_ids
            assert str(public.id) in all_ids
            break
        break
