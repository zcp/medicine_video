"""
直播间分类管理 API 测试

覆盖以下端点的权限校验：
- POST /api/v1/rooms/{room_id}/categories          （房间创建者用）
- DELETE /api/v1/rooms/{room_id}/categories/{cid}   （房间创建者用）
- POST /api/v1/admin/rooms/{room_id}/categories      （管理员用）
- DELETE /api/v1/admin/rooms/{room_id}/categories/{cid} （管理员用）

测试策略：实用派（Pragmatic），直接调用 API + 数据库创建测试数据
遵循测试文档《Tab功能测试实现与结果文档.md》的测试模式
"""

import pytest
import uuid
from io import BytesIO

from app.models.live_core import LiveRoom
from app.models.content_management import Category, LiveRoomCategory


# ==================== 辅助函数 ====================

def _create_category(db, name=None):
    """创建一个可用的分类"""
    category = Category(
        id=uuid.uuid4(),
        name=name or f"test_cat_{uuid.uuid4().hex[:8]}",
        sort_order=0,
        is_active=True,
    )
    db.add(category)
    return category


# ==================== Owner 分类设置/删除测试 ====================

class TestRoomCategoryOwnerAPI:
    """房间创建者分类管理 API 测试（/api/v1/rooms/...）"""

    # ---------- POST /rooms/{room_id}/categories（owner）----------

    @pytest.mark.asyncio
    async def test_set_categories_owner_success(self, async_client, db_session, regular_user_token, regular_user_id):
        """房间创建者设置分类 → 200"""
        async for client in async_client:
            async for db in db_session:
                room = LiveRoom(id=uuid.uuid4(), user_id=regular_user_id,
                                title=f"CatRoom {uuid.uuid4().hex[:8]}", stream_key=f"str_{uuid.uuid4().hex}")
                db.add(room)
                cat = _create_category(db)
                await db.commit()

                payload = {
                    "category_ids": [str(cat.id)],
                    "primary_category_id": str(cat.id),
                    "mode": "replace"
                }
                headers = {"Authorization": f"Bearer {regular_user_token}"}
                response = await client.post(
                    f"/api/v1/rooms/{room.id}/categories",
                    json=payload, headers=headers
                )

                assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
                assert response.json()["code"] == 200

    @pytest.mark.asyncio
    async def test_set_categories_non_owner_denied(self, async_client, db_session, regular_user_token, another_user_id):
        """非创建者设置分类 → 403"""
        async for client in async_client:
            async for db in db_session:
                room = LiveRoom(id=uuid.uuid4(), user_id=another_user_id,
                                title=f"CatRoom {uuid.uuid4().hex[:8]}", stream_key=f"str_{uuid.uuid4().hex}")
                db.add(room)
                cat = _create_category(db)
                await db.commit()

                payload = {
                    "category_ids": [str(cat.id)],
                    "primary_category_id": str(cat.id),
                    "mode": "replace"
                }
                headers = {"Authorization": f"Bearer {regular_user_token}"}
                response = await client.post(
                    f"/api/v1/rooms/{room.id}/categories",
                    json=payload, headers=headers
                )

                assert response.status_code == 403
                data = response.json()
                assert data["code"] in (3003, 3002)

    # ---------- DELETE /rooms/{room_id}/categories/{cid}（owner）----------

    @pytest.mark.asyncio
    async def test_delete_category_owner_success(self, async_client, db_session, regular_user_token, regular_user_id):
        """房间创建者删除分类关联 → 200"""
        async for client in async_client:
            async for db in db_session:
                room = LiveRoom(id=uuid.uuid4(), user_id=regular_user_id,
                                title=f"CatRoom {uuid.uuid4().hex[:8]}", stream_key=f"str_{uuid.uuid4().hex}")
                db.add(room)
                cat = _create_category(db)
                await db.commit()

                # 先创建关联
                link = LiveRoomCategory(room_id=room.id, category_id=cat.id)
                db.add(link)
                await db.commit()

                headers = {"Authorization": f"Bearer {regular_user_token}"}
                response = await client.delete(
                    f"/api/v1/rooms/{room.id}/categories/{cat.id}",
                    headers=headers
                )

                assert response.status_code == 200
                # 删除接口返回 {"message": "删除成功"}，非标准包装格式
                data = response.json()
                assert "message" in data

    @pytest.mark.asyncio
    async def test_delete_category_non_owner_denied(self, async_client, db_session, regular_user_token, another_user_id):
        """非创建者删除分类关联 → 403"""
        async for client in async_client:
            async for db in db_session:
                room = LiveRoom(id=uuid.uuid4(), user_id=another_user_id,
                                title=f"CatRoom {uuid.uuid4().hex[:8]}", stream_key=f"str_{uuid.uuid4().hex}")
                db.add(room)
                cat = _create_category(db)
                link = LiveRoomCategory(room_id=room.id, category_id=cat.id)
                db.add(link)
                await db.commit()

                headers = {"Authorization": f"Bearer {regular_user_token}"}
                response = await client.delete(
                    f"/api/v1/rooms/{room.id}/categories/{cat.id}",
                    headers=headers
                )

                assert response.status_code == 403
                data = response.json()
                assert data["code"] in (3003, 3002)


# ==================== Admin 分类设置/删除测试 ====================

class TestRoomCategoryAdminAPI:
    """管理员分类管理 API 测试（/api/v1/admin/rooms/...）"""

    @pytest.mark.asyncio
    async def test_set_categories_admin_success(self, async_client, db_session, admin_user_token):
        """Admin 设置分类 → 200"""
        async for client in async_client:
            async for db in db_session:
                room = LiveRoom(id=uuid.uuid4(), user_id=uuid.uuid4(),
                                title=f"AdminCat {uuid.uuid4().hex[:8]}", stream_key=f"str_{uuid.uuid4().hex}")
                db.add(room)
                cat = _create_category(db)
                await db.commit()

                payload = {
                    "category_ids": [str(cat.id)],
                    "primary_category_id": str(cat.id),
                    "mode": "replace"
                }
                headers = {"Authorization": f"Bearer {admin_user_token}"}
                response = await client.post(
                    f"/api/v1/admin/rooms/{room.id}/categories",
                    json=payload, headers=headers
                )

                assert response.status_code == 200
                assert response.json()["code"] == 200

    @pytest.mark.asyncio
    async def test_set_categories_regular_denied(self, async_client, db_session, regular_user_token, regular_user_id):
        """普通用户（非创建者）调 admin 分类接口 → 403"""
        async for client in async_client:
            async for db in db_session:
                room = LiveRoom(id=uuid.uuid4(), user_id=uuid.uuid4(),
                                title=f"AdminCat {uuid.uuid4().hex[:8]}", stream_key=f"str_{uuid.uuid4().hex}")
                db.add(room)
                cat = _create_category(db)
                await db.commit()

                payload = {
                    "category_ids": [str(cat.id)],
                    "primary_category_id": str(cat.id),
                    "mode": "replace"
                }
                headers = {"Authorization": f"Bearer {regular_user_token}"}
                response = await client.post(
                    f"/api/v1/admin/rooms/{room.id}/categories",
                    json=payload, headers=headers
                )

                assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_delete_category_admin_success(self, async_client, db_session, admin_user_token):
        """Admin 删除分类关联 → 200"""
        async for client in async_client:
            async for db in db_session:
                room = LiveRoom(id=uuid.uuid4(), user_id=uuid.uuid4(),
                                title=f"AdminCat {uuid.uuid4().hex[:8]}", stream_key=f"str_{uuid.uuid4().hex}")
                db.add(room)
                cat = _create_category(db)
                link = LiveRoomCategory(room_id=room.id, category_id=cat.id)
                db.add(link)
                await db.commit()

                headers = {"Authorization": f"Bearer {admin_user_token}"}
                response = await client.delete(
                    f"/api/v1/admin/rooms/{room.id}/categories/{cat.id}",
                    headers=headers
                )

                assert response.status_code == 200
                # 删除接口返回 {"message": "删除成功"}，非标准包装格式
                data = response.json()
                assert "message" in data

    @pytest.mark.asyncio
    async def test_set_categories_unauthorized(self, async_client, db_session):
        """无 Token 调 admin 分类接口 → 401"""
        async for client in async_client:
            async for db in db_session:
                room = LiveRoom(id=uuid.uuid4(), user_id=uuid.uuid4(),
                                title=f"UnauthCat {uuid.uuid4().hex[:8]}", stream_key=f"str_{uuid.uuid4().hex}")
                db.add(room)
                cat = _create_category(db)
                await db.commit()

                payload = {
                    "category_ids": [str(cat.id)],
                    "primary_category_id": str(cat.id),
                    "mode": "replace"
                }
                response = await client.post(
                    f"/api/v1/admin/rooms/{room.id}/categories",
                    json=payload
                )
                assert response.status_code == 401
