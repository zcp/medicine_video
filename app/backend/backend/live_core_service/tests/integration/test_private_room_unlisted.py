"""
私密房 unlisted 语义正式测试（阶段 2 收编，2026-08-11 V1.1 决策 D1-D6）

覆盖：
- N1 匿名持链读私密房 200
- N2 他人（登录）持链读 200
- N3 非创建者写（PATCH/DELETE）403
- N4 收藏私密房 → 收藏列表返回 → 取消收藏
- N5 /users/me/rooms 透出 is_private
- N6 公开列表/搜索排除私密房（发现层过滤）
- N7 观看历史不留痕（私密房观看记录被过滤）
- WS 方案 B 见 test_private_room_ws.py（Windows 环境限制 skip，Linux/CI 验证）
"""
import uuid

import pytest

pytestmark = pytest.mark.asyncio


@pytest.fixture
async def private_room_fx(async_client, regular_user_token: str):
    """创建测试私密房（async 模式，连测试库；含一个场次用于观看历史）"""
    async for client in async_client:
        room_title = f"PrivateRoom-{uuid.uuid4().hex[:8]}"
        resp = await client.post(
            "/api/v1/rooms",
            json={
                "title": room_title,
                "description": "unlisted semantics test room",
                "is_private": True,
            },
            headers={"Authorization": f"Bearer {regular_user_token}"},
        )
        assert resp.status_code == 200, f"创建私密房失败: {resp.status_code} {resp.text}"
        room_id = resp.json()["data"]["id"]

        from datetime import datetime, timezone

        from app.database import AsyncSessionLocal
        from app.models.live_core import LiveSession, LiveSessionStatus

        async with AsyncSessionLocal() as db:
            session = LiveSession(
                room_id=uuid.UUID(room_id),
                status=LiveSessionStatus.READY,
                start_time=datetime.now(timezone.utc),
            )
            db.add(session)
            await db.commit()
            await db.refresh(session)
            session_id = session.id

        yield {"room_id": room_id, "session_id": str(session_id), "client": client, "title_prefix": room_title}

        resp = await client.delete(
            f"/api/v1/rooms/{room_id}",
            headers={"Authorization": f"Bearer {regular_user_token}"},
        )
        assert resp.status_code == 200, f"清理测试房失败: {resp.status_code} {resp.text}"


async def test_private_room_anonymous_reads_200(private_room_fx):
    """N1: 匿名持链读私密房 → 200"""
    async for room in private_room_fx:
        resp = await room["client"].get(f"/api/v1/rooms/{room['room_id']}")
        assert resp.status_code == 200, f"匿名持链读失败: {resp.status_code} {resp.text}"
        assert resp.json()["data"]["id"] == room["room_id"]


async def test_private_room_other_user_reads_200(private_room_fx, another_user_token: str):
    """N2: 他人（登录非创建者）持链读 → 200"""
    async for room in private_room_fx:
        resp = await room["client"].get(
            f"/api/v1/rooms/{room['room_id']}",
            headers={"Authorization": f"Bearer {another_user_token}"},
        )
        assert resp.status_code == 200, f"他人持链读失败: {resp.status_code} {resp.text}"


async def test_private_room_write_forbidden_403(private_room_fx, another_user_token: str):
    """N3: 非创建者 PATCH/DELETE → 403（写语义不变）"""
    async for room in private_room_fx:
        resp = await room["client"].patch(
            f"/api/v1/rooms/{room['room_id']}",
            json={"title": "should not succeed"},
            headers={"Authorization": f"Bearer {another_user_token}"},
        )
        assert resp.status_code == 403, f"非创建者 PATCH 应 403: {resp.status_code}"
        resp = await room["client"].delete(
            f"/api/v1/rooms/{room['room_id']}",
            headers={"Authorization": f"Bearer {another_user_token}"},
        )
        assert resp.status_code == 403, f"非创建者 DELETE 应 403: {resp.status_code}"


async def test_private_room_favorite_in_list(private_room_fx, another_user_token: str):
    """N4: 收藏私密房 → 收藏列表返回 → 取消收藏"""
    async for room in private_room_fx:
        client = room["client"]
        resp = await client.post(
            "/api/v1/users/me/favorites",
            json={"room_id": room["room_id"]},
            headers={"Authorization": f"Bearer {another_user_token}"},
        )
        assert resp.status_code == 200, f"收藏私密房失败: {resp.status_code} {resp.text}"
        resp = await client.get(
            "/api/v1/users/me/favorites",
            headers={"Authorization": f"Bearer {another_user_token}"},
        )
        assert resp.status_code == 200
        fav_items = resp.json()["data"]["items"]
        assert any(str(i["room_id"]) == room["room_id"] for i in fav_items), "收藏列表未返回私密房"
        resp = await client.delete(
            f"/api/v1/users/me/favorites/{room['room_id']}",
            headers={"Authorization": f"Bearer {another_user_token}"},
        )
        assert resp.status_code == 200, f"取消收藏失败: {resp.status_code}"


async def test_private_room_me_rooms_exposes_is_private(private_room_fx, regular_user_token: str):
    """N5: /users/me/rooms 透出 is_private=true"""
    async for room in private_room_fx:
        resp = await room["client"].get(
            "/api/v1/users/me/rooms",
            headers={"Authorization": f"Bearer {regular_user_token}"},
        )
        assert resp.status_code == 200
        my_rooms = resp.json()["data"]["items"]
        target = next((r for r in my_rooms if str(r["id"]) == room["room_id"]), None)
        assert target is not None, "me/rooms 未返回私密房"
        assert target["is_private"] is True, f"me/rooms 未透出 is_private: {target}"


async def test_private_room_excluded_from_discovery(private_room_fx):
    """N6: 公开列表与搜索均排除私密房（发现层过滤）"""
    async for room in private_room_fx:
        client = room["client"]
        resp = await client.get("/api/v1/rooms", params={"page": 1, "size": 100})
        assert resp.status_code == 200
        pub_ids = [str(i["id"]) for i in resp.json()["data"]["items"]]
        assert room["room_id"] not in pub_ids, "私密房不应出现在公开列表"

        resp = await client.get(
            "/api/v1/search",
            params={"q": room["title_prefix"], "page": 1, "size": 10},
        )
        assert resp.status_code == 200
        items = resp.json().get("data", {}).get("items", []) or []
        room_ids = [str(i.get("id", "")) for i in items]
        assert room["room_id"] not in room_ids, "私密房不应出现在搜索结果"


async def test_private_room_watch_history_kept_private(private_room_fx, regular_user_token: str):
    """N7: 观看历史不留痕——记录私密房场次观看后，历史列表不含（方案 A，V1.1 决策 D6）"""
    async for room in private_room_fx:
        client = room["client"]
        resp = await client.post(
            "/api/v1/users/me/watch-history",
            json={"session_id": room["session_id"]},
            headers={"Authorization": f"Bearer {regular_user_token}"},
        )
        assert resp.status_code == 200, f"记录观看失败: {resp.status_code} {resp.text}"
        resp = await client.get(
            "/api/v1/users/me/watch-history",
            headers={"Authorization": f"Bearer {regular_user_token}"},
        )
        assert resp.status_code == 200
        items = resp.json()["data"]["items"]
        assert all(str(i.get("session_id", "")) != room["session_id"] for i in items), (
            "私密房场次不应出现在观看历史"
        )
