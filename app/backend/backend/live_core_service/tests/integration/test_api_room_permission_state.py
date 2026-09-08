"""
LiveCore Service - Room Permission State Change Integration Tests

本模块包含直播间权限状态变更的专项测试。
测试范围：房间隐私状态变更后的可见性动态变化（unlisted 语义，2026-08-11 V1.1 决策 D1）

测试场景：
- Public → Private：详情持链仍可读（匿名 200），但退出公开列表（发现层过滤）
- Private → Public：进入公开列表，匿名可发现
"""

import pytest
import uuid


class TestRoomPermissionStateChange:
    """直播间权限状态变更专项测试"""

    @pytest.mark.asyncio
    async def test_room_privacy_public_to_private_keeps_link_visibility(
        self,
        async_client,
        db_session,
        regular_user_token: str,
        regular_user_id: uuid.UUID
    ):
        """测试：房间从Public改为Private后，详情持链可读（200），但退出公开列表（发现层过滤）"""
        async for client in async_client:
            # ===== Arrange (准备) =====
            # 1. 创建Public房间
            create_data = {
                "title": f"Test Room {uuid.uuid4().hex[:6]}",
                "description": "Test Description",
                "is_private": False,
                "record_by_default": True
            }
            headers = {"Authorization": f"Bearer {regular_user_token}"}
            create_response = await client.post("/api/v1/rooms", json=create_data, headers=headers)
            assert create_response.status_code == 200
            room_id = create_response.json()["data"]["id"]

            # ===== Act (执行) =====
            # 2. 匿名用户可以访问
            detail_response = await client.get(f"/api/v1/rooms/{room_id}")
            assert detail_response.status_code == 200

            # 3. 修改为private状态
            update_data = {"is_private": True}
            update_response = await client.patch(f"/api/v1/rooms/{room_id}", json=update_data, headers=headers)
            assert update_response.status_code == 200

            # ===== Assert (断言) =====
            # 4. unlisted：匿名持链仍可读（200）
            detail_response = await client.get(f"/api/v1/rooms/{room_id}")
            assert detail_response.status_code == 200
            assert detail_response.json()["data"]["id"] == room_id

            # 5. 发现层：退出公开列表
            list_response = await client.get("/api/v1/rooms", params={"page": 1, "size": 100})
            assert list_response.status_code == 200
            pub_ids = [str(i["id"]) for i in list_response.json()["data"]["items"]]
            assert room_id not in pub_ids, "私密房不应出现在公开列表"

    @pytest.mark.asyncio
    async def test_room_privacy_private_to_public_allows_discovery(
        self,
        async_client,
        db_session,
        regular_user_token: str,
        regular_user_id: uuid.UUID
    ):
        """测试：房间从Private改为Public后，进入公开列表（匿名可发现）"""
        async for client in async_client:
            # ===== Arrange (准备) =====
            # 1. 创建Private房间
            create_data = {
                "title": f"Test Room {uuid.uuid4().hex[:6]}",
                "description": "Test Description",
                "is_private": True,
                "record_by_default": True
            }
            headers = {"Authorization": f"Bearer {regular_user_token}"}
            create_response = await client.post("/api/v1/rooms", json=create_data, headers=headers)
            assert create_response.status_code == 200
            room_id = create_response.json()["data"]["id"]

            # ===== Act (执行) =====
            # 2. unlisted：匿名持链可读
            detail_response = await client.get(f"/api/v1/rooms/{room_id}")
            assert detail_response.status_code == 200

            # 3. 修改为public状态
            update_data = {"is_private": False}
            update_response = await client.patch(f"/api/v1/rooms/{room_id}", json=update_data, headers=headers)
            assert update_response.status_code == 200

            # ===== Assert (断言) =====
            # 4. 匿名详情可访问（应返回200）
            detail_response = await client.get(f"/api/v1/rooms/{room_id}")
            assert detail_response.status_code == 200
            assert detail_response.json()["data"]["id"] == room_id

            # 5. 发现层：进入公开列表
            list_response = await client.get("/api/v1/rooms", params={"page": 1, "size": 100})
            assert list_response.status_code == 200
            pub_ids = [str(i["id"]) for i in list_response.json()["data"]["items"]]
            assert room_id in pub_ids, "改为公开后应出现在公开列表"

