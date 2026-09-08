"""
首页与搜索模块的API层集成测试

测试对象：app/api/v1/endpoints/homepage_search.py
测试模式：incremental（增量测试）
测试策略：Pragmatic Testing（真实数据库）
"""
import uuid
import pytest
from datetime import datetime, timedelta
from io import BytesIO
from httpx import AsyncClient

from app.main import app
from app.schemas.homepage_search import FeaturedContentCreate


# ==================== 测试数据辅助函数 ====================

async def create_test_featured_content_via_api(
    client: AsyncClient,
    admin_token: str,
    **kwargs
):
    """通过API创建测试焦点图"""
    unique_id = str(uuid.uuid4())[:8]
    data = {
        "title": f"测试焦点图_{unique_id}",
        "image_url": f"https://example.com/image_{unique_id}.jpg",
        "subtitle": f"副标题_{unique_id}",
        "target_type": "room",
        "sort_order": 0,
        "is_active": True,
        **kwargs
    }
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = await client.post(
        "/api/v1/admin/featured-content",
        json=data,
        headers=headers
    )
    return response


# ==================== Phase1: 焦点图API测试 ====================

@pytest.mark.asyncio
async def test_get_featured_content_api_success(async_client, admin_user_token):
    """测试获取焦点图列表API（公开接口）- 成功"""
    async for client in async_client:
        # ===== Arrange (准备) =====
        # 先创建一个有效的焦点图
        create_response = await create_test_featured_content_via_api(
            client, admin_user_token, is_active=True
        )
        assert create_response.status_code == 200
        
        # ===== Act (执行) =====
        response = await client.get("/api/v1/featured-content")
        
        # ===== Assert (断言) =====
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "data" in data
        assert isinstance(data["data"], list)
        break


@pytest.mark.asyncio
async def test_get_featured_content_api_only_active(async_client, admin_user_token):
    """测试获取焦点图列表API - 只返回启用的"""
    async for client in async_client:
        # ===== Arrange (准备) =====
        # 创建一个未启用的焦点图
        create_response = await create_test_featured_content_via_api(
            client, admin_user_token, is_active=False
        )
        assert create_response.status_code == 200
        created_id = create_response.json()["data"]["id"]
        
        # ===== Act (执行) =====
        response = await client.get("/api/v1/featured-content")
        
        # ===== Assert (断言) =====
        assert response.status_code == 200
        data = response.json()
        # 未启用的焦点图不应该出现在公开列表中
        returned_ids = [item["id"] for item in data["data"]]
        assert created_id not in returned_ids
        break


@pytest.mark.asyncio
async def test_get_featured_content_admin_api_success(async_client, admin_user_token):
    """测试获取焦点图列表API（管理员接口）- 成功（分页格式）"""
    async for client in async_client:
        # ===== Act (执行) =====
        headers = {"Authorization": f"Bearer {admin_user_token}"}
        response = await client.get(
            "/api/v1/admin/featured-content",
            params={"page": 1, "size": 10},
            headers=headers
        )
        
        # ===== Assert (断言) =====
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "data" in data
        assert "items" in data["data"]
        assert isinstance(data["data"]["items"], list)
        break


@pytest.mark.asyncio
async def test_get_featured_content_admin_api_permission_denied(async_client, regular_user_token):
    """测试获取焦点图列表API（管理员接口）- 权限不足"""
    async for client in async_client:
        # ===== Act (执行) =====
        headers = {"Authorization": f"Bearer {regular_user_token}"}
        response = await client.get(
            "/api/v1/admin/featured-content",
            headers=headers
        )
        
        # ===== Assert (断言) =====
        assert response.status_code == 403
        data = response.json()
        assert data["code"] == 3002
        break


# ==================== GET /api/v1/admin/featured-content 分页列表（增量） ====================

@pytest.mark.asyncio
async def test_get_admin_featured_content_paginated_success(async_client, admin_user_token):
    """测试 GET /api/v1/admin/featured-content 分页列表 - 成功"""
    async for client in async_client:
        headers = {"Authorization": f"Bearer {admin_user_token}"}
        response = await client.get(
            "/api/v1/admin/featured-content",
            params={"page": 1, "size": 10},
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "data" in data
        assert "total" in data["data"]
        assert "page" in data["data"]
        assert "size" in data["data"]
        assert "items" in data["data"]
        assert data["data"]["page"] == 1
        assert data["data"]["size"] == 10
        assert isinstance(data["data"]["items"], list)
        break


@pytest.mark.asyncio
async def test_get_admin_featured_content_paginated_permission_denied(async_client, regular_user_token):
    """测试 GET /api/v1/admin/featured-content 分页列表 - 权限不足"""
    async for client in async_client:
        headers = {"Authorization": f"Bearer {regular_user_token}"}
        response = await client.get(
            "/api/v1/admin/featured-content",
            params={"page": 1, "size": 10},
            headers=headers
        )
        assert response.status_code == 403
        data = response.json()
        assert data["code"] == 3002
        break


@pytest.mark.asyncio
async def test_get_admin_featured_content_paginated_unauthorized(async_client):
    """测试 GET /api/v1/admin/featured-content 分页列表 - 未认证"""
    async for client in async_client:
        response = await client.get(
            "/api/v1/admin/featured-content",
            params={"page": 1, "size": 10}
        )
        assert response.status_code == 401
        break


@pytest.mark.asyncio
async def test_create_featured_content_api_success(async_client, admin_user_token):
    """测试创建焦点图API - 成功"""
    async for client in async_client:
        # ===== Arrange (准备) =====
        unique_id = str(uuid.uuid4())[:8]
        data = {
            "title": f"新焦点图_{unique_id}",
            "image_url": f"https://example.com/new_{unique_id}.jpg",
            "subtitle": "测试副标题",
            "target_type": "room",
            "sort_order": 0,
            "is_active": True
        }
        
        # ===== Act (执行) =====
        headers = {"Authorization": f"Bearer {admin_user_token}"}
        response = await client.post(
            "/api/v1/admin/featured-content",
            json=data,
            headers=headers
        )
        
        # ===== Assert (断言) =====
        assert response.status_code == 200
        result = response.json()
        assert result["code"] == 200
        assert result["data"]["title"] == data["title"]
        assert result["data"]["image_url"] == data["image_url"]
        break


@pytest.mark.asyncio
async def test_create_featured_content_api_validation_error(async_client, admin_user_token):
    """测试创建焦点图API - 验证错误（缺少必需字段）"""
    async for client in async_client:
        # ===== Arrange (准备) =====
        data = {
            # 缺少必需的title和image_url字段
            "subtitle": "测试副标题"
        }
        
        # ===== Act (执行) =====
        headers = {"Authorization": f"Bearer {admin_user_token}"}
        response = await client.post(
            "/api/v1/admin/featured-content",
            json=data,
            headers=headers
        )
        
        # ===== Assert (断言) =====
        assert response.status_code == 422  # FastAPI的验证错误状态码
        break


@pytest.mark.asyncio
async def test_update_featured_content_api_success(async_client, admin_user_token):
    """测试更新焦点图API - 成功"""
    async for client in async_client:
        # ===== Arrange (准备) =====
        # 先创建一个焦点图
        create_response = await create_test_featured_content_via_api(
            client, admin_user_token
        )
        assert create_response.status_code == 200
        content_id = create_response.json()["data"]["id"]
        
        # ===== Act (执行) =====
        update_data = {
            "title": "更新后的标题",
            "is_active": False
        }
        headers = {"Authorization": f"Bearer {admin_user_token}"}
        response = await client.patch(
            f"/api/v1/admin/featured-content/{content_id}",
            json=update_data,
            headers=headers
        )
        
        # ===== Assert (断言) =====
        assert response.status_code == 200
        result = response.json()
        assert result["code"] == 200
        assert result["data"]["title"] == "更新后的标题"
        assert result["data"]["is_active"] == False
        break


@pytest.mark.asyncio
async def test_update_featured_content_api_not_found(async_client, admin_user_token):
    """测试更新焦点图API - 不存在"""
    async for client in async_client:
        # ===== Arrange (准备) =====
        non_existent_id = str(uuid.uuid4())
        update_data = {"title": "新标题"}
        
        # ===== Act (执行) =====
        headers = {"Authorization": f"Bearer {admin_user_token}"}
        response = await client.patch(
            f"/api/v1/admin/featured-content/{non_existent_id}",
            json=update_data,
            headers=headers
        )
        
        # ===== Assert (断言) =====
        assert response.status_code == 404
        data = response.json()
        assert data["code"] == 2001
        break


@pytest.mark.asyncio
async def test_delete_featured_content_api_success(async_client, admin_user_token):
    """测试删除焦点图API - 成功（物理删除：删除后详情返回404）"""
    async for client in async_client:
        # ===== Arrange (准备) =====
        # 先创建一个焦点图
        create_response = await create_test_featured_content_via_api(
            client, admin_user_token
        )
        assert create_response.status_code == 200
        content_id = create_response.json()["data"]["id"]
        
        # ===== Act (执行) =====
        headers = {"Authorization": f"Bearer {admin_user_token}"}
        response = await client.delete(
            f"/api/v1/admin/featured-content/{content_id}",
            headers=headers
        )
        
        # ===== Assert (断言) =====
        assert response.status_code == 200
        result = response.json()
        assert result["code"] == 200
        assert result["data"]["status"] == "deleted"
        # 物理删除：删除后详情接口应返回404（软删除时详情仍返回200）
        detail_response = await client.get(
            f"/api/v1/admin/featured-content/{content_id}",
            headers=headers
        )
        assert detail_response.status_code == 404
        break


@pytest.mark.asyncio
async def test_delete_inactive_featured_content_api_success(async_client, admin_user_token):
    """测试删除已下线焦点图API - 成功（回归：修复对已下线条目删除'假成功'bug）"""
    async for client in async_client:
        # ===== Arrange (准备) =====
        # 创建一个已下线（is_active=False）的焦点图
        create_response = await create_test_featured_content_via_api(
            client, admin_user_token, is_active=False
        )
        assert create_response.status_code == 200
        content_id = create_response.json()["data"]["id"]
        
        # ===== Act (执行) =====
        headers = {"Authorization": f"Bearer {admin_user_token}"}
        response = await client.delete(
            f"/api/v1/admin/featured-content/{content_id}",
            headers=headers
        )
        
        # ===== Assert (断言) =====
        assert response.status_code == 200
        result = response.json()
        assert result["code"] == 200
        assert result["data"]["status"] == "deleted"
        # 已下线条目应被真正删除：详情返回404
        detail_response = await client.get(
            f"/api/v1/admin/featured-content/{content_id}",
            headers=headers
        )
        assert detail_response.status_code == 404
        break


@pytest.mark.asyncio
async def test_delete_featured_content_api_not_found(async_client, admin_user_token):
    """测试删除焦点图API - 不存在"""
    async for client in async_client:
        # ===== Arrange (准备) =====
        non_existent_id = str(uuid.uuid4())
        
        # ===== Act (执行) =====
        headers = {"Authorization": f"Bearer {admin_user_token}"}
        response = await client.delete(
            f"/api/v1/admin/featured-content/{non_existent_id}",
            headers=headers
        )
        
        # ===== Assert (断言) =====
        assert response.status_code == 404
        data = response.json()
        assert data["code"] == 2001
        break


# ==================== Phase2: 首页API测试 ====================

@pytest.mark.asyncio
async def test_get_homepage_rooms_api_success(async_client):
    """测试获取首页直播间列表API - 成功"""
    async for client in async_client:
        # ===== Act (执行) =====
        response = await client.get("/api/v1/homepage/rooms")
        
        # ===== Assert (断言) =====
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "data" in data
        assert "total" in data["data"]
        assert "page" in data["data"]
        assert "size" in data["data"]
        assert "items" in data["data"]
        break


@pytest.mark.asyncio
async def test_get_homepage_rooms_api_with_pagination(async_client):
    """测试获取首页直播间列表API - 分页参数"""
    async for client in async_client:
        # ===== Act (执行) =====
        response = await client.get(
            "/api/v1/homepage/rooms",
            params={"page": 1, "size": 5, "sort": "heat:desc"}
        )
        
        # ===== Assert (断言) =====
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["page"] == 1
        assert data["data"]["size"] == 5
        assert len(data["data"]["items"]) <= 5
        break


@pytest.mark.asyncio
async def test_get_homepage_rooms_api_with_category_filter(async_client, db_session):
    """测试首页直播间列表API - category_id 过滤（关联分类的房间命中、未关联不命中）"""
    from app.models.content_management import Category, LiveRoomCategory
    from app.models.live_core import LiveRoom

    async for client in async_client:
        uid = uuid.uuid4().hex
        # ===== Arrange (准备) =====
        cat_a = Category(name=f"测试分类A_{uid}", slug=f"cat-a-{uid}", sort_order=0, is_active=True)
        db_session.add(cat_a)
        await db_session.flush()
        room1 = LiveRoom(title=f"测试房间A_{uid}", user_id=uuid.uuid4(), stream_key=f"sk_test_{uid}_1")
        room2 = LiveRoom(title=f"测试房间B_{uid}", user_id=uuid.uuid4(), stream_key=f"sk_test_{uid}_2")
        db_session.add_all([room1, room2])
        await db_session.flush()
        db_session.add(LiveRoomCategory(room_id=room1.id, category_id=cat_a.id, is_primary=True))
        await db_session.commit()

        # ===== Act (执行) =====
        response = await client.get(
            "/api/v1/homepage/rooms",
            params={"category_id": str(cat_a.id), "size": 100}
        )

        # ===== Assert (断言) =====
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        room_ids = [item["id"] for item in data["data"]["items"]]
        assert str(room1.id) in room_ids      # 关联了该分类的房间应命中
        assert str(room2.id) not in room_ids  # 未关联分类的房间不应命中
        break


@pytest.mark.asyncio
async def test_get_homepage_rooms_api_invalid_category(async_client):
    """测试首页直播间列表API - 无效 category_id（不存在的分类应 400）"""
    async for client in async_client:
        # ===== Act (执行) =====
        response = await client.get(
            "/api/v1/homepage/rooms",
            params={"category_id": str(uuid.uuid4())}
        )

        # ===== Assert (断言) =====
        assert response.status_code == 400
        data = response.json()
        assert data["code"] == 4001
        break


# ==================== Phase3: 搜索API测试 ====================

@pytest.mark.asyncio
async def test_search_api_success(async_client):
    """测试全局搜索API - 成功"""
    async for client in async_client:
        # ===== Act (执行) =====
        response = await client.get(
            "/api/v1/search",
            params={"q": "测试搜索"}
        )
        
        # ===== Assert (断言) =====
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "data" in data
        assert "total" in data["data"]
        assert "items" in data["data"]
        break


@pytest.mark.asyncio
async def test_search_api_validation_error(async_client):
    """测试全局搜索API - 验证错误（关键词少于2个字符）"""
    async for client in async_client:
        # ===== Act (执行) =====
        response = await client.get(
            "/api/v1/search",
            params={"q": "a"}  # 只有1个字符，不满足最少2个字符的要求
        )

        # ===== Assert (断言) =====
        assert response.status_code == 422  # FastAPI的验证错误状态码
        break


@pytest.mark.asyncio
async def test_search_api_room_metadata_filled(async_client, db_session):
    """测试全局搜索 - room 结果 metadata 填充状态与创建者兜底

    验证问题2修复：后端 /search 对 room 结果补 status + expert_*（无专家时创建者兜底）
    """
    from app.models.live_core import LiveRoom, LiveSession, LiveSessionStatus
    from datetime import datetime, timezone

    async for db in db_session:
        # ===== Arrange (准备) =====
        owner_id = uuid.uuid4()
        room = LiveRoom(
            id=uuid.uuid4(),
            user_id=owner_id,
            title=f"搜索Metadata测试房间_{uuid.uuid4().hex[:8]}",
            stream_key=f"stream_key_{uuid.uuid4().hex[:16]}",
            is_private=False,
            record_by_default=True,
        )
        db.add(room)
        await db.flush()

        # 创建场次（状态 finished），供 room_card_map 聚合出代表场次状态
        session = LiveSession(
            id=uuid.uuid4(),
            room_id=room.id,
            status=LiveSessionStatus.FINISHED,
            start_time=datetime.now(timezone.utc),
            end_time=datetime.now(timezone.utc),
        )
        db.add(session)
        await db.commit()

        # ===== Act (执行) =====
        client = await async_client.__anext__()
        response = await client.get(
            "/api/v1/search",
            params={"q": "搜索Metadata测试房间", "type": "room"}
        )

        # ===== Assert (断言) =====
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        room_items = [i for i in data["data"]["items"] if i["type"] == "room"]
        assert len(room_items) >= 1, "应至少命中一条 room 搜索结果"

        item = room_items[0]
        metadata = item.get("metadata") or {}
        # 状态被填充（代表场次状态，finished）
        assert metadata.get("status") == "finished", f"status 应为 finished，实际: {metadata.get('status')}"
        # 无关联专家时 expert_name 走创建者兜底（该 owner 在 users 服务不存在 → "用户"）
        assert metadata.get("expert_name") == "用户", f"expert_name 应为创建者兜底'用户'，实际: {metadata.get('expert_name')}"
        break



# ==================== GET 分页列表 q/search_type（增量） ====================

@pytest.mark.asyncio
async def test_get_admin_featured_content_paginated_with_q_empty(async_client, admin_user_token):
    """GET 分页列表 - q 为空或不传时正常返回"""
    async for client in async_client:
        headers = {"Authorization": f"Bearer {admin_user_token}"}
        response = await client.get(
            "/api/v1/admin/featured-content",
            params={"page": 1, "size": 10},
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "data" in data
        assert "total" in data["data"]
        assert "items" in data["data"]


@pytest.mark.asyncio
async def test_get_admin_featured_content_paginated_with_search_type_id_valid(
    async_client, admin_user_token
):
    """GET 分页列表 - search_type=id、q 为有效 UUID 时返回对应条"""
    async for client in async_client:
        create_resp = await create_test_featured_content_via_api(client, admin_user_token)
        assert create_resp.status_code == 200
        content_id = create_resp.json()["data"]["id"]
        headers = {"Authorization": f"Bearer {admin_user_token}"}
        response = await client.get(
            "/api/v1/admin/featured-content",
            params={"page": 1, "size": 10, "q": content_id, "search_type": "id"},
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["total"] >= 1
        assert any(item["id"] == content_id for item in data["data"]["items"])


@pytest.mark.asyncio
async def test_get_admin_featured_content_paginated_with_search_type_id_invalid_returns_400(
    async_client, admin_user_token
):
    """GET 分页列表 - search_type=id、q 非 UUID 时返回 400、4001"""
    async for client in async_client:
        headers = {"Authorization": f"Bearer {admin_user_token}"}
        response = await client.get(
            "/api/v1/admin/featured-content",
            params={"page": 1, "size": 10, "q": "not-a-uuid", "search_type": "id"},
            headers=headers
        )
        assert response.status_code == 400
        data = response.json()
        assert data["code"] == 4001


@pytest.mark.asyncio
async def test_get_admin_featured_content_paginated_with_search_type_name(
    async_client, admin_user_token
):
    """GET 分页列表 - q 有值、search_type 非 id 时标题/副标题模糊"""
    async for client in async_client:
        unique = str(uuid.uuid4())[:8]
        create_resp = await create_test_featured_content_via_api(
            client, admin_user_token, title=f"模糊匹配标题_{unique}"
        )
        assert create_resp.status_code == 200
        content_id = create_resp.json()["data"]["id"]
        headers = {"Authorization": f"Bearer {admin_user_token}"}
        response = await client.get(
            "/api/v1/admin/featured-content",
            params={"page": 1, "size": 10, "q": f"模糊匹配标题_{unique}", "search_type": "name"},
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["total"] >= 1
        assert any(item["id"] == content_id for item in data["data"]["items"])


# ==================== POST 焦点图图片上传（增量） ====================

@pytest.mark.asyncio
async def test_upload_featured_content_image_api_success(async_client, admin_user_token):
    """POST 焦点图图片上传 - 成功，200，data 含 image_url"""
    async for client in async_client:
        create_resp = await create_test_featured_content_via_api(client, admin_user_token)
        assert create_resp.status_code == 200
        content_id = create_resp.json()["data"]["id"]
        image_content = b'\xff\xd8\xff\xe0\x00\x10JFIF' + b'0' * 1000
        files = {"image": ("test.jpg", BytesIO(image_content), "image/jpeg")}
        headers = {"Authorization": f"Bearer {admin_user_token}"}
        response = await client.post(
            f"/api/v1/admin/featured-content/{content_id}/image",
            files=files,
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "data" in data
        assert "image_url" in data["data"]
        assert data["data"]["image_url"].startswith("/media/")


@pytest.mark.asyncio
async def test_upload_featured_content_image_api_permission_denied(
    async_client, admin_user_token, regular_user_token
):
    """POST 焦点图图片上传 - 普通用户返回 403、3002"""
    async for client in async_client:
        create_resp = await create_test_featured_content_via_api(client, admin_user_token)
        assert create_resp.status_code == 200
        content_id = create_resp.json()["data"]["id"]
        files = {"image": ("test.jpg", BytesIO(b'\xff\xd8\xff' + b'0' * 100), "image/jpeg")}
        response = await client.post(
            f"/api/v1/admin/featured-content/{content_id}/image",
            files=files,
            headers={"Authorization": f"Bearer {regular_user_token}"}
        )
        assert response.status_code == 403
        data = response.json()
        assert data["code"] == 3002


@pytest.mark.asyncio
async def test_upload_featured_content_image_api_not_found(async_client, admin_user_token):
    """POST 焦点图图片上传 - 不存在的 content_id 返回 404、2001"""
    async for client in async_client:
        non_existent_id = str(uuid.uuid4())
        files = {"image": ("test.jpg", BytesIO(b'\xff\xd8\xff' + b'0' * 100), "image/jpeg")}
        headers = {"Authorization": f"Bearer {admin_user_token}"}
        response = await client.post(
            f"/api/v1/admin/featured-content/{non_existent_id}/image",
            files=files,
            headers=headers
        )
        assert response.status_code == 404
        data = response.json()
        assert data["code"] == 2001


@pytest.mark.asyncio
async def test_upload_featured_content_image_api_bad_file_returns_400(
    async_client, admin_user_token
):
    """POST 焦点图图片上传 - 非法文件类型或缺失文件返回 400、4001"""
    async for client in async_client:
        create_resp = await create_test_featured_content_via_api(client, admin_user_token)
        assert create_resp.status_code == 200
        content_id = create_resp.json()["data"]["id"]
        headers = {"Authorization": f"Bearer {admin_user_token}"}
        response = await client.post(
            f"/api/v1/admin/featured-content/{content_id}/image",
            files={"image": ("bad.txt", BytesIO(b"not an image"), "text/plain")},
            headers=headers
        )
        assert response.status_code == 400
        data = response.json()
        assert data["code"] == 4001
        break


# ==================== 焦点图获取详情（Admin）增量测试 ====================

@pytest.mark.asyncio
async def test_get_featured_content_detail_admin_api_success(async_client, admin_user_token):
    """GET 焦点图详情（Admin）- 管理员成功返回单条"""
    async for client in async_client:
        # ===== Arrange (准备) =====
        create_response = await create_test_featured_content_via_api(
            client, admin_user_token, title="详情测试焦点图"
        )
        assert create_response.status_code == 200
        content_id = create_response.json()["data"]["id"]

        # ===== Act (执行) =====
        headers = {"Authorization": f"Bearer {admin_user_token}"}
        response = await client.get(
            f"/api/v1/admin/featured-content/{content_id}",
            headers=headers
        )

        # ===== Assert (断言) =====
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "data" in data
        assert data["data"]["id"] == content_id
        assert data["data"]["title"] == "详情测试焦点图"
        assert "image_url" in data["data"]
        break


@pytest.mark.asyncio
async def test_get_featured_content_detail_admin_api_unauthorized(async_client):
    """GET 焦点图详情（Admin）- 无 Token 返回 401"""
    async for client in async_client:
        # ===== Act (执行) =====
        response = await client.get(
            f"/api/v1/admin/featured-content/{uuid.uuid4()}"
        )

        # ===== Assert (断言) =====
        assert response.status_code == 401
        break


@pytest.mark.asyncio
async def test_get_featured_content_detail_admin_api_permission_denied(
    async_client, admin_user_token, regular_user_token
):
    """GET 焦点图详情（Admin）- REGULAR 返回 403、3002"""
    async for client in async_client:
        # ===== Arrange (准备) =====
        create_response = await create_test_featured_content_via_api(
            client, admin_user_token
        )
        assert create_response.status_code == 200
        content_id = create_response.json()["data"]["id"]

        # ===== Act (执行) =====
        headers = {"Authorization": f"Bearer {regular_user_token}"}
        response = await client.get(
            f"/api/v1/admin/featured-content/{content_id}",
            headers=headers
        )

        # ===== Assert (断言) =====
        assert response.status_code == 403
        data = response.json()
        assert data["code"] == 3002
        break


@pytest.mark.asyncio
async def test_get_featured_content_detail_admin_api_not_found(
    async_client, admin_user_token
):
    """GET 焦点图详情（Admin）- 不存在的 content_id 返回 404、2001"""
    async for client in async_client:
        # ===== Act (执行) =====
        non_existent_id = str(uuid.uuid4())
        headers = {"Authorization": f"Bearer {admin_user_token}"}
        response = await client.get(
            f"/api/v1/admin/featured-content/{non_existent_id}",
            headers=headers
        )

        # ===== Assert (断言) =====
        assert response.status_code == 404
        data = response.json()
        assert data["code"] == 2001
        break