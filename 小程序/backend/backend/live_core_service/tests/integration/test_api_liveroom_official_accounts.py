"""
直播间与公众号关联模块 - API 层测试
测试策略: Pragmatic（完整链路）
"""
import pytest
from uuid import uuid4, UUID

from app.models.liveroom_official_accounts import OfficialAccount, LiveRoomOfficialAccount
from app.models.live_core import LiveRoom


async def _create_test_room(db):
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


@pytest.mark.asyncio
async def test_get_official_accounts_admin_unauthorized(async_client):
    """无 Token 请求 GET /api/v1/admin/official-accounts 返回 401 或 403"""
    async for client in async_client:
        response = await client.get("/api/v1/admin/official-accounts")
        assert response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_get_official_accounts_admin_with_admin_token(
    async_client, db_session, admin_user_token
):
    """带 admin Token 获取公众号列表返回 200，data 含 total/page/size/items"""
    async for client in async_client:
        async for db in db_session:
            acc = OfficialAccount(id=uuid4(), name=f"公众号_{uuid4().hex[:8]}", is_active=True)
            db.add(acc)
            await db.flush()
            break

        response = await client.get(
            "/api/v1/admin/official-accounts",
            headers={"Authorization": f"Bearer {admin_user_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert data["data"].get("total") is not None
        assert "items" in data["data"]


@pytest.mark.asyncio
async def test_create_official_account_success(async_client, admin_user_token):
    """POST /api/v1/admin/official-accounts 创建成功返回 201，data 含 name/id/is_active"""
    async for client in async_client:
        body = {
            "name": f"新公众号_{uuid4().hex[:8]}",
            "slug": "new-oa",
            "is_active": True,
        }
        response = await client.post(
            "/api/v1/admin/official-accounts",
            json=body,
            headers={"Authorization": f"Bearer {admin_user_token}"},
        )
        assert response.status_code == 201
        data = response.json()
        assert "data" in data
        assert data["data"]["name"] == body["name"]
        assert "id" in data["data"]
        assert data["data"]["is_active"] is True


@pytest.mark.asyncio
async def test_create_official_account_permission_denied(
    async_client, regular_user_token
):
    """普通用户 POST 创建公众号返回 403，code 3002"""
    async for client in async_client:
        body = {"name": f"新公众号_{uuid4().hex[:8]}", "is_active": True}
        response = await client.post(
            "/api/v1/admin/official-accounts",
            json=body,
            headers={"Authorization": f"Bearer {regular_user_token}"},
        )
        assert response.status_code == 403
        data = response.json()
        assert data.get("code") == 3002


@pytest.mark.asyncio
async def test_get_official_account_by_id_not_found(
    async_client, admin_user_token
):
    """GET /api/v1/admin/official-accounts/{不存在的uuid} 返回 404，code 2001"""
    async for client in async_client:
        response = await client.get(
            f"/api/v1/admin/official-accounts/{uuid4()}",
            headers={"Authorization": f"Bearer {admin_user_token}"},
        )
        assert response.status_code == 404
        data = response.json()
        assert data.get("code") == 2001


@pytest.mark.asyncio
async def test_get_rooms_official_accounts_room_not_found(async_client):
    """GET /api/v1/rooms/{不存在的room_id}/official-accounts 返回 404"""
    async for client in async_client:
        response = await client.get(f"/api/v1/rooms/{uuid4()}/official-accounts")
        assert response.status_code == 404
        data = response.json()
        assert data.get("code") == 2001


@pytest.mark.asyncio
async def test_get_rooms_official_accounts_success(
    async_client, db_session
):
    """GET /api/v1/rooms/{room_id}/official-accounts 有 room 时返回 200，data 为列表"""
    async for client in async_client:
        async for db in db_session:
            room = await _create_test_room(db)
            acc = OfficialAccount(id=uuid4(), name=f"公众号_{uuid4().hex[:8]}", is_active=True)
            db.add(acc)
            await db.flush()
            db.add(LiveRoomOfficialAccount(room_id=room.id, account_id=acc.id))
            await db.commit()
            room_id = room.id
            break

        response = await client.get(f"/api/v1/rooms/{room_id}/official-accounts")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert isinstance(data["data"], list)


@pytest.mark.asyncio
async def test_set_room_official_accounts_admin(
    async_client, db_session, admin_user_token
):
    """POST /api/v1/admin/rooms/{room_id}/official-accounts 批量设置，Admin 返回 200"""
    async for client in async_client:
        async for db in db_session:
            room = await _create_test_room(db)
            acc = OfficialAccount(id=uuid4(), name=f"公众号_{uuid4().hex[:8]}", is_active=True)
            db.add(acc)
            await db.commit()
            room_id = room.id
            account_id = str(acc.id)
            break

        response = await client.post(
            f"/api/v1/admin/rooms/{room_id}/official-accounts",
            json={"account_ids": [account_id], "mode": "replace"},
            headers={"Authorization": f"Bearer {admin_user_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("code") == 200
        assert "data" in data


@pytest.mark.asyncio
async def test_get_official_accounts_rooms_paginated(
    async_client, db_session, admin_user_token
):
    """GET /api/v1/official-accounts/{account_id}/rooms 分页，Admin 返回 200"""
    async for client in async_client:
        async for db in db_session:
            acc = OfficialAccount(id=uuid4(), name=f"公众号_{uuid4().hex[:8]}", is_active=True)
            db.add(acc)
            await db.commit()
            account_id = acc.id
            break

        response = await client.get(
            f"/api/v1/official-accounts/{account_id}/rooms?page=1&size=10",
            headers={"Authorization": f"Bearer {admin_user_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "total" in data["data"]
        assert "items" in data["data"]
