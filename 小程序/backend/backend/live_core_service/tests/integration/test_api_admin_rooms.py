"""
管理端全站房间列表 + Admin 改他人房间内容（17 MVP）集成测试
"""

import inspect
import uuid

import pytest


async def get_fixture_room_id(room_fixture):
    if hasattr(room_fixture, "id") and not inspect.isasyncgen(room_fixture):
        return room_fixture.id
    if inspect.isasyncgen(room_fixture):
        try:
            room_obj = await room_fixture.__anext__()
            return room_obj.id
        except StopAsyncIteration:
            if hasattr(room_fixture, "id"):
                return room_fixture.id
            raise ValueError("无法从fixture中获取room_id")
    return room_fixture.id


@pytest.mark.asyncio
async def test_admin_list_rooms_unauthorized(async_client):
    """无 Token → 401"""
    async for client in async_client:
        response = await client.get("/api/v1/admin/rooms")
        assert response.status_code == 401
        break


@pytest.mark.asyncio
async def test_admin_list_rooms_forbidden_for_regular(async_client, regular_user_token: str):
    """普通用户 → 403 / 3003"""
    headers = {"Authorization": f"Bearer {regular_user_token}"}
    async for client in async_client:
        response = await client.get("/api/v1/admin/rooms", headers=headers)
        assert response.status_code == 403
        detail = response.json().get("detail") or response.json()
        if isinstance(detail, dict):
            assert detail.get("code") == 3003
        break


@pytest.mark.asyncio
async def test_admin_list_rooms_includes_others_and_private(
    async_client,
    admin_user_token: str,
    regular_user_token: str,
):
    """Admin 列表含他人公开房与不公开房，且不含 stream_key"""
    admin_headers = {"Authorization": f"Bearer {admin_user_token}"}
    user_headers = {"Authorization": f"Bearer {regular_user_token}"}
    async for client in async_client:
        pub = await client.post(
            "/api/v1/rooms",
            headers=user_headers,
            json={"title": f"AdminListPublic_{uuid.uuid4().hex[:6]}", "is_private": False},
        )
        priv = await client.post(
            "/api/v1/rooms",
            headers=user_headers,
            json={"title": f"AdminListPrivate_{uuid.uuid4().hex[:6]}", "is_private": True},
        )
        assert pub.status_code == 200 and priv.status_code == 200
        public_id = pub.json()["data"]["id"]
        private_id = priv.json()["data"]["id"]

        response = await client.get("/api/v1/admin/rooms", headers=admin_headers)
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 200
        data = body["data"]
        assert "total" in data and "items" in data
        ids = {item["id"] for item in data["items"]}
        assert public_id in ids
        assert private_id in ids

        for item in data["items"]:
            assert "owner_user_id" in item
            assert "updated_at" in item
            assert "stream_key" not in item
            assert "is_private" in item
        break


@pytest.mark.asyncio
async def test_admin_list_rooms_filter_by_q_and_owner(
    async_client,
    admin_user_token: str,
    public_room,
    regular_user_id,
):
    """q / owner_user_id 过滤"""
    headers = {"Authorization": f"Bearer {admin_user_token}"}
    public_id = await get_fixture_room_id(public_room)
    async for client in async_client:
        r1 = await client.get(
            "/api/v1/admin/rooms",
            headers=headers,
            params={"q": "Public", "page": 1, "size": 50},
        )
        assert r1.status_code == 200
        items1 = r1.json()["data"]["items"]
        assert any(str(public_id) == i["id"] for i in items1)

        r2 = await client.get(
            "/api/v1/admin/rooms",
            headers=headers,
            params={"owner_user_id": str(regular_user_id), "page": 1, "size": 50},
        )
        assert r2.status_code == 200
        for item in r2.json()["data"]["items"]:
            assert item["owner_user_id"] == str(regular_user_id)
        break


@pytest.mark.asyncio
async def test_admin_list_rooms_filter_by_is_private(
    async_client,
    admin_user_token: str,
    regular_user_token: str,
):
    """is_private 筛选：Admin 仍可见不公开房"""
    admin_headers = {"Authorization": f"Bearer {admin_user_token}"}
    user_headers = {"Authorization": f"Bearer {regular_user_token}"}
    async for client in async_client:
        pub = await client.post(
            "/api/v1/rooms",
            headers=user_headers,
            json={"title": f"FilterPub_{uuid.uuid4().hex[:6]}", "is_private": False},
        )
        priv = await client.post(
            "/api/v1/rooms",
            headers=user_headers,
            json={"title": f"FilterPriv_{uuid.uuid4().hex[:6]}", "is_private": True},
        )
        assert pub.status_code == 200 and priv.status_code == 200
        public_id = pub.json()["data"]["id"]
        private_id = priv.json()["data"]["id"]

        r_priv = await client.get(
            "/api/v1/admin/rooms",
            headers=admin_headers,
            params={"is_private": True, "page": 1, "size": 100},
        )
        assert r_priv.status_code == 200
        ids_priv = {i["id"] for i in r_priv.json()["data"]["items"]}
        assert private_id in ids_priv
        assert public_id not in ids_priv
        for item in r_priv.json()["data"]["items"]:
            assert item["is_private"] is True

        r_pub = await client.get(
            "/api/v1/admin/rooms",
            headers=admin_headers,
            params={"is_private": False, "page": 1, "size": 100},
        )
        assert r_pub.status_code == 200
        ids_pub = {i["id"] for i in r_pub.json()["data"]["items"]}
        assert public_id in ids_pub
        assert private_id not in ids_pub
        break


@pytest.mark.asyncio
async def test_admin_patch_others_room_title(
    async_client,
    admin_user_token: str,
    public_room,
):
    """Admin 可 PATCH 他人房间标题（复用既有写接口）"""
    headers = {"Authorization": f"Bearer {admin_user_token}"}
    room_id = await get_fixture_room_id(public_room)
    new_title = "运营修正标题_17mvp"
    async for client in async_client:
        response = await client.patch(
            f"/api/v1/rooms/{room_id}",
            headers=headers,
            json={"title": new_title},
        )
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["code"] == 200
        assert body["data"]["title"] == new_title

        detail = await client.get(
            f"/api/v1/rooms/{room_id}",
            headers=headers,
        )
        assert detail.status_code == 200
        assert detail.json()["data"]["title"] == new_title
        break


@pytest.mark.asyncio
async def test_regular_cannot_patch_others_room(
    async_client,
    regular_user_token: str,
    private_room_owned_by_another_user,
):
    """非 owner 的 REGULAR 不能改他人房"""
    headers = {"Authorization": f"Bearer {regular_user_token}"}
    room_id = await get_fixture_room_id(private_room_owned_by_another_user)
    async for client in async_client:
        response = await client.patch(
            f"/api/v1/rooms/{room_id}",
            headers=headers,
            json={"title": "非法篡改"},
        )
        assert response.status_code == 403
        break
