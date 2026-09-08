"""
LiveCore Service - Room Permission State Change Integration Tests

文档 18：is_private=不公开（unlisted）——持链可读；发现层另滤。
"""

import pytest
import uuid


class TestRoomPermissionStateChange:
    """直播间隐私状态变更专项测试（unlisted 读语义）"""

    @pytest.mark.asyncio
    async def test_room_privacy_public_to_private_still_readable_by_link(
        self,
        async_client,
        db_session,
        regular_user_token: str,
        regular_user_id: uuid.UUID,
    ):
        """Public→不公开后，匿名持 room_id 仍可读"""
        async for client in async_client:
            create_data = {
                "title": f"Test Room {uuid.uuid4().hex[:6]}",
                "description": "Test Description",
                "is_private": False,
                "record_by_default": True,
            }
            headers = {"Authorization": f"Bearer {regular_user_token}"}
            create_response = await client.post(
                "/api/v1/rooms", json=create_data, headers=headers
            )
            assert create_response.status_code == 200
            room_id = create_response.json()["data"]["id"]

            detail_response = await client.get(f"/api/v1/rooms/{room_id}")
            assert detail_response.status_code == 200

            update_response = await client.patch(
                f"/api/v1/rooms/{room_id}",
                json={"is_private": True},
                headers=headers,
            )
            assert update_response.status_code == 200

            detail_response = await client.get(f"/api/v1/rooms/{room_id}")
            assert detail_response.status_code == 200
            assert detail_response.json()["data"]["is_private"] is True

    @pytest.mark.asyncio
    async def test_room_privacy_private_to_public_allows_anonymous_visibility(
        self,
        async_client,
        db_session,
        regular_user_token: str,
        regular_user_id: uuid.UUID,
    ):
        """不公开→Public：匿名仍可读（两端均持链可读）"""
        async for client in async_client:
            create_data = {
                "title": f"Test Room {uuid.uuid4().hex[:6]}",
                "description": "Test Description",
                "is_private": True,
                "record_by_default": True,
            }
            headers = {"Authorization": f"Bearer {regular_user_token}"}
            create_response = await client.post(
                "/api/v1/rooms", json=create_data, headers=headers
            )
            assert create_response.status_code == 200
            room_id = create_response.json()["data"]["id"]

            detail_response = await client.get(f"/api/v1/rooms/{room_id}")
            assert detail_response.status_code == 200

            update_response = await client.patch(
                f"/api/v1/rooms/{room_id}",
                json={"is_private": False},
                headers=headers,
            )
            assert update_response.status_code == 200

            detail_response = await client.get(f"/api/v1/rooms/{room_id}")
            assert detail_response.status_code == 200
            assert detail_response.json()["data"]["id"] == room_id

