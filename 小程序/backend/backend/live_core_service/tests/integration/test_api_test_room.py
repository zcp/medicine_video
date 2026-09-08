"""
文档 18：POST /rooms/{id}/test-room 与不公开持链可读集成测试
"""

import inspect
import pytest
import uuid


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
async def test_ensure_test_room_create_and_idempotent(
    async_client,
    regular_user_token: str,
    public_room,
):
    """owner 首次创建测播间；再次调用幂等返回同一间"""
    headers = {"Authorization": f"Bearer {regular_user_token}"}
    source_id = await get_fixture_room_id(public_room)

    async for client in async_client:
        r1 = await client.post(
            f"/api/v1/rooms/{source_id}/test-room",
            json={},
            headers=headers,
        )
        assert r1.status_code == 200, r1.text
        body1 = r1.json()
        assert body1["code"] == 200
        data1 = body1["data"]
        assert data1["created"] is True
        assert data1["source_room_id"] == str(source_id)
        test1 = data1["test_room"]
        assert test1["is_private"] is True
        assert test1["stream_key"]
        assert "连接测试" in test1["title"]
        test_id = test1["id"]

        r2 = await client.post(
            f"/api/v1/rooms/{source_id}/test-room",
            headers=headers,
        )
        assert r2.status_code == 200
        data2 = r2.json()["data"]
        assert data2["created"] is False
        assert data2["test_room"]["id"] == test_id
        break


@pytest.mark.asyncio
async def test_ensure_test_room_forbidden_for_non_owner(
    async_client,
    another_user_token: str,
    public_room,
):
    """非 owner 普通用户 → 403"""
    headers = {"Authorization": f"Bearer {another_user_token}"}
    source_id = await get_fixture_room_id(public_room)
    async for client in async_client:
        response = await client.post(
            f"/api/v1/rooms/{source_id}/test-room",
            headers=headers,
        )
        assert response.status_code == 403
        assert response.json().get("code") == 3002
        break


@pytest.mark.asyncio
async def test_ensure_test_room_rejects_when_source_is_test_room(
    async_client,
    regular_user_token: str,
    public_room,
):
    """对测播间再调 test-room → 400"""
    headers = {"Authorization": f"Bearer {regular_user_token}"}
    source_id = await get_fixture_room_id(public_room)
    async for client in async_client:
        created = await client.post(
            f"/api/v1/rooms/{source_id}/test-room",
            headers=headers,
        )
        assert created.status_code == 200
        test_id = created.json()["data"]["test_room"]["id"]

        again = await client.post(
            f"/api/v1/rooms/{test_id}/test-room",
            headers=headers,
        )
        assert again.status_code == 400
        assert again.json().get("code") == 4001
        break


@pytest.mark.asyncio
async def test_test_room_readable_by_non_owner_write_still_denied(
    async_client,
    regular_user_token: str,
    another_user_token: str,
    public_room,
):
    """持链可读测播详情；非房主 PATCH 仍 403"""
    owner_headers = {"Authorization": f"Bearer {regular_user_token}"}
    other_headers = {"Authorization": f"Bearer {another_user_token}"}
    source_id = await get_fixture_room_id(public_room)

    async for client in async_client:
        created = await client.post(
            f"/api/v1/rooms/{source_id}/test-room",
            headers=owner_headers,
        )
        assert created.status_code == 200
        test_id = created.json()["data"]["test_room"]["id"]

        detail = await client.get(f"/api/v1/rooms/{test_id}", headers=other_headers)
        assert detail.status_code == 200
        assert detail.json()["data"]["is_private"] is True

        anon = await client.get(f"/api/v1/rooms/{test_id}")
        assert anon.status_code == 200

        patch = await client.patch(
            f"/api/v1/rooms/{test_id}",
            json={"title": f"hijack-{uuid.uuid4().hex[:6]}"},
            headers=other_headers,
        )
        assert patch.status_code == 403
        assert patch.json().get("code") == 3002
        break
