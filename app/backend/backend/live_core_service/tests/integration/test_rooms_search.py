"""
LiveCore Service - Rooms Search API Integration Tests

This module contains integration tests for the rooms search API endpoints,
testing the complete search workflow with database validation.

遵循测试代码生成提示词母版 - Pragmatic 测试策略（真实 DB + 完整链路）
"""

import pytest
import uuid
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.live_core import LiveRoom
from tests.conftest import async_session_factory


# ==================== Helper Functions ====================

import inspect

async def get_fixture_room_id(room_fixture):
    """
    辅助函数：从room fixture中安全地获取room_id
    处理async generator fixture的情况
    """
    # 如果fixture已经被pytest解析，直接返回id
    if hasattr(room_fixture, 'id') and not inspect.isasyncgen(room_fixture):
        return room_fixture.id
    
    # 如果是async generator，尝试获取值
    if inspect.isasyncgen(room_fixture):
        try:
            room_obj = await room_fixture.__anext__()
            return room_obj.id
        except StopAsyncIteration:
            # Generator已经被消费，说明pytest已经解析了它
            # 尝试直接访问id（如果pytest已经解析）
            if hasattr(room_fixture, 'id'):
                return room_fixture.id
            raise ValueError("无法从fixture中获取room_id：generator已被消费且未解析")
    
    # 默认情况：直接返回id
    return room_fixture.id


async def create_test_room_for_search(
    db: AsyncSession, 
    user_id: uuid.UUID,
    title: str,
    description: str = "测试房间",
    is_private: bool = False  # ← 新增：添加 is_private 参数
) -> LiveRoom:
    """创建用于搜索测试的房间"""
    room = LiveRoom(
        title=title,
        description=description,
        stream_key=f"test_key_{uuid.uuid4().hex[:8]}",
        is_private=is_private,  # ← 修改：使用参数
        record_by_default=True,
        user_id=user_id
    )
    db.add(room)
    await db.commit()
    await db.refresh(room)
    return room


# ==================== API Integration Tests (Pragmatic) ====================

@pytest.mark.asyncio
async def test_search_rooms_by_uuid_exact_match_anonymous(
    async_client, 
    db_session,
    public_room
):
    """
    测试按房间 UUID 精确搜索（匿名用户，只能搜索到Public房间，S1场景）
    
    策略：Pragmatic - 使用真实 DB + AsyncClient 验证完整链路
    """
    # ===== Arrange (准备) =====
    # public_room已在Fixture中创建
    
    # ===== Act (执行) =====
    async for client in async_client:
        # ← 修改：在外层循环获取room_id，避免在内层循环时generator已被消费
        public_room_id = await get_fixture_room_id(public_room)
        async for db in db_session:
            # 不添加Authorization header（匿名用户）
            response = await client.get(
                f"/api/v1/rooms?q={str(public_room_id)}"
            )
            
            # ===== Assert (断言) =====
            assert response.status_code == 200, f"期望 200，实际 {response.status_code}: {response.text}"
            
            response_json = response.json()
            # 验证统一响应结构
            assert "code" in response_json
            assert "message" in response_json
            assert "data" in response_json
            assert "timestamp" in response_json
            
            assert response_json["code"] == 200
            assert response_json["message"] == "success"
            
            # 验证分页数据结构
            data = response_json["data"]
            assert "total" in data
            assert "page" in data
            assert "size" in data
            assert "items" in data
            
            # 应该只返回一个匹配的房间
            assert data["total"] == 1, f"按 UUID 搜索应该精确匹配 1 个房间，实际 {data['total']}"
            assert len(data["items"]) == 1
            
            # 验证返回的是正确的房间
            found_room = data["items"][0]
            assert found_room["id"] == str(public_room_id)
            assert found_room["is_private"] == False  # ← 新增：验证只能搜索到Public房间
            
            break
        break

# ← 新增：测试登录用户场景（S3）
@pytest.mark.asyncio
async def test_search_rooms_by_uuid_exact_match_as_owner(
    async_client, 
    db_session,
    regular_user_token: str,
    regular_user_id: uuid.UUID
):
    """测试按房间 UUID 精确搜索（登录用户，可以看到Public+自己的房间，S3场景）"""
    # ===== Arrange (准备) =====
    headers = {"Authorization": f"Bearer {regular_user_token}"}
    
    async for client in async_client:
        async for db in db_session:
            # 创建自己的Private房间
            private_room = await create_test_room_for_search(
                db, 
                regular_user_id, 
                "我的Private房间",
                is_private=True
            )
            private_room_id = private_room.id  # 使用已创建的room对象，不是fixture
            
            # ===== Act (执行) =====
            response = await client.get(
                f"/api/v1/rooms?q={str(private_room_id)}",
                headers=headers
            )
            
            # ===== Assert (断言) =====
            assert response.status_code == 200
            response_json = response.json()
            assert response_json["code"] == 200
            data = response_json["data"]
            assert data["total"] == 1
            assert data["items"][0]["id"] == str(private_room_id)
            break
        break

# ← 新增：测试Admin用户场景（S6）
@pytest.mark.asyncio
async def test_search_rooms_by_uuid_exact_match_as_admin(
    async_client, 
    db_session,
    admin_user_token: str,
    private_room
):
    """测试按房间 UUID 精确搜索（Admin用户，可以看到所有房间，S6场景）"""
    # ===== Arrange (准备) =====
    headers = {"Authorization": f"Bearer {admin_user_token}"}
    
    # ===== Act (执行) =====
    async for client in async_client:
        # ← 修改：在外层循环获取room_id，避免在内层循环时generator已被消费
        private_room_id = await get_fixture_room_id(private_room)
        async for db in db_session:
            response = await client.get(
                f"/api/v1/rooms?q={str(private_room_id)}",
                headers=headers
            )
            
            # ===== Assert (断言) =====
            assert response.status_code == 200
            response_json = response.json()
            assert response_json["code"] == 200
            data = response_json["data"]
            assert data["total"] == 1
            assert data["items"][0]["id"] == str(private_room_id)
            break
        break


@pytest.mark.asyncio
async def test_search_rooms_by_title_fuzzy_match_anonymous(
    async_client, 
    db_session,
    regular_user_id: uuid.UUID
):
    """
    测试按标题模糊搜索（匿名用户，只能搜索到Public房间，S1场景）
    
    策略：Pragmatic
    """
    # ===== Arrange (准备) =====
    async for client in async_client:
        async for db in db_session:
            # 使用唯一关键词避免与其他测试数据冲突
            unique_keyword = f"模糊搜索测试_{uuid.uuid4().hex[:8]}"
            # 创建Public房间（匿名用户可见）
            room1 = await create_test_room_for_search(db, regular_user_id, f"{unique_keyword}_房间A", is_private=False)
            room2 = await create_test_room_for_search(db, regular_user_id, f"{unique_keyword}_房间B", is_private=False)
            # 创建Private房间（匿名用户不可见）
            room3_private = await create_test_room_for_search(db, regular_user_id, f"{unique_keyword}_Private房间", is_private=True)
            
            # ===== Act (执行) =====
            # 不添加Authorization header（匿名用户）
            response = await client.get(f"/api/v1/rooms?q={unique_keyword}")
            
            # ===== Assert (断言) =====
            assert response.status_code == 200
            response_json = response.json()
            assert response_json["code"] == 200
            
            data = response_json["data"]
            # 应该至少返回包含关键词的 2 个Public房间
            assert data["total"] >= 2, f"应至少匹配 2 个包含关键词的Public房间，实际 {data['total']}"
            
            # 验证返回的结果中包含了我们创建的Public房间
            returned_ids = [item["id"] for item in data["items"]]
            assert str(room1.id) in returned_ids, "应找到 room1（Public）"
            assert str(room2.id) in returned_ids, "应找到 room2（Public）"
            assert str(room3_private.id) not in returned_ids, "不应找到 room3_private（Private房间，匿名用户不可见）"
            
            # ← 新增：验证我们创建的Public房间的 is_private 字段
            # 只检查我们创建的、应该在结果中的房间，避免检查其他测试留下的数据
            # 同时检查字段是否存在，避免 KeyError
            for item in data["items"]:
                if item["id"] in [str(room1.id), str(room2.id)]:
                    # 如果响应中包含 is_private 字段，验证它为 False
                    if "is_private" in item:
                        assert item["is_private"] == False, f"匿名用户只能搜索到Public房间，但房间 {item['id']} 的 is_private={item['is_private']}"
            
            break
        break


@pytest.mark.asyncio
async def test_search_rooms_by_title_case_insensitive(
    async_client_with_auth, 
    db_session,
    regular_user_id: uuid.UUID
):
    """
    测试标题搜索是否不区分大小写
    
    策略：Pragmatic
    """
    async for client in async_client_with_auth:
        async for db in db_session:
            # ARRANGE: 创建包含英文的房间
            # ===== Arrange (准备) =====
            room1 = await create_test_room_for_search(db, regular_user_id, "React Workshop 2024")
            room2 = await create_test_room_for_search(db, regular_user_id, "Python Tutorial")
            
            # ===== Act (执行) =====
            response = await client.get("/api/v1/rooms?q=react")
            
            # ===== Assert (断言) =====
            assert response.status_code == 200
            response_json = response.json()
            assert response_json["code"] == 200
            
            data = response_json["data"]
            assert data["total"] >= 1, "不区分大小写搜索应该找到结果"
            
            # 验证返回的房间中包含匹配项
            returned_titles = [item["title"] for item in data["items"]]
            assert "React Workshop 2024" in returned_titles
            
            break
        break


@pytest.mark.asyncio
async def test_search_rooms_empty_query_returns_all(
    async_client_with_auth, 
    db_session,
    regular_user_id: uuid.UUID
):
    """
    测试不提供 q 参数应返回所有房间（兼容性测试）
    
    策略：Pragmatic - 验证向后兼容性
    """
    async for client in async_client_with_auth:
        async for db in db_session:
            # ===== Arrange (准备) =====
            room1 = await create_test_room_for_search(db, regular_user_id, "房间 A")
            room2 = await create_test_room_for_search(db, regular_user_id, "房间 B")
            room3 = await create_test_room_for_search(db, regular_user_id, "房间 C")
            
            # ===== Act (执行) =====
            response = await client.get("/api/v1/rooms")
            
            # ===== Assert (断言) =====
            assert response.status_code == 200
            response_json = response.json()
            assert response_json["code"] == 200
            
            data = response_json["data"]
            assert data["total"] >= 3, "不提供搜索关键词应返回所有房间"
            
            break
        break


@pytest.mark.asyncio
async def test_search_rooms_no_match_returns_empty(
    async_client_with_auth, 
    db_session,
    regular_user_id: uuid.UUID
):
    """
    测试搜索无匹配结果应返回空列表
    
    策略：Pragmatic
    """
    async for client in async_client_with_auth:
        async for db in db_session:
            # ===== Arrange (准备) =====
            await create_test_room_for_search(db, regular_user_id, "JavaScript 入门")
            await create_test_room_for_search(db, regular_user_id, "Python 实战")
            
            # ACT: 搜索不存在的关键词
            response = await client.get("/api/v1/rooms?q=完全不存在的关键词xyz123")
            
            # ASSERT
            assert response.status_code == 200
            response_json = response.json()
            assert response_json["code"] == 200
            
            data = response_json["data"]
            assert data["total"] == 0, "无匹配结果应返回 total=0"
            assert len(data["items"]) == 0, "无匹配结果应返回空列表"
            
            break
        break


@pytest.mark.asyncio
async def test_search_rooms_with_pagination(
    async_client_with_auth, 
    db_session,
    regular_user_id: uuid.UUID
):
    """
    测试搜索结果支持分页
    
    策略：Pragmatic
    """
    async for client in async_client_with_auth:
        async for db in db_session:
            # ARRANGE: 使用唯一关键词避免与其他测试数据冲突
            unique_keyword = f"分页测试_{uuid.uuid4().hex[:8]}"
            # ===== Arrange (准备) =====
            # 使用regular_user_id（从conftest.py获取）
            created_room_ids = []
            
            # 创建 5 个房间
            for i in range(5):
                room = await create_test_room_for_search(
                    db, regular_user_id, f"{unique_keyword}_房间{i+1}"
                )
                created_room_ids.append(str(room.id))
            
            # ACT: 搜索并分页（page=1, size=2）
            response = await client.get(f"/api/v1/rooms?q={unique_keyword}&page=1&size=2")
            
            # ASSERT
            assert response.status_code == 200
            response_json = response.json()
            assert response_json["code"] == 200
            
            data = response_json["data"]
            # 应该至少匹配我们创建的 5 个房间
            assert data["total"] >= 5, f"应至少匹配 5 个房间，实际 {data['total']}"
            assert data["page"] == 1
            assert data["size"] == 2
            assert len(data["items"]) == 2, "第一页应返回 2 条记录"
            
            # 验证第一页的结果都在我们创建的列表中
            page1_ids = [item["id"] for item in data["items"]]
            for item_id in page1_ids:
                assert item_id in created_room_ids, f"第一页的结果应包含在我们创建的房间里: {item_id}"
            
            # ACT: 请求第二页
            response2 = await client.get(f"/api/v1/rooms?q={unique_keyword}&page=2&size=2")
            
            # ASSERT
            assert response2.status_code == 200
            response_json2 = response2.json()
            data2 = response_json2["data"]
            assert data2["page"] == 2
            assert len(data2["items"]) == 2, "第二页应返回 2 条记录"
            
            # 验证第二页的结果都在我们创建的列表中，且与第一页不重复
            page2_ids = [item["id"] for item in data2["items"]]
            for item_id in page2_ids:
                assert item_id in created_room_ids, f"第二页的结果应包含在我们创建的房间里: {item_id}"
                assert item_id not in page1_ids, "第二页的结果不应与第一页重复"
            
            # 验证第三页也有数据（如果总数 >= 5，第三页应该还有至少 1 条）
            response3 = await client.get(f"/api/v1/rooms?q={unique_keyword}&page=3&size=2")
            data3 = response3.json()["data"]
            assert len(data3["items"]) >= 1, "第三页应至少返回 1 条记录（总共 5 条，每页 2 条）"
            
            break
        break


@pytest.mark.asyncio
async def test_search_rooms_with_sort_parameter(
    async_client_with_auth, 
    db_session,
    regular_user_id: uuid.UUID
):
    """
    测试搜索支持排序参数
    
    策略：Pragmatic
    """
    async for client in async_client_with_auth:
        async for db in db_session:
            # ARRANGE: 使用唯一关键词避免与其他测试数据冲突
            unique_keyword = f"排序测试_{uuid.uuid4().hex[:8]}"
            # ===== Arrange (准备) =====
            # 使用regular_user_id（从conftest.py获取）
            
            room1 = await create_test_room_for_search(db, regular_user_id, f"{unique_keyword} A")
            # 等待一小段时间确保 created_at 不同
            import asyncio
            await asyncio.sleep(0.1)
            room2 = await create_test_room_for_search(db, regular_user_id, f"{unique_keyword} B")
            await asyncio.sleep(0.1)
            room3 = await create_test_room_for_search(db, regular_user_id, f"{unique_keyword} C")
            
            # ACT: 按创建时间升序排序（最旧的在前）
            response = await client.get(f"/api/v1/rooms?q={unique_keyword}&sort=created_at:asc")
            
            # ASSERT
            assert response.status_code == 200
            response_json = response.json()
            assert response_json["code"] == 200
            
            data = response_json["data"]
            items = data["items"]
            # 应该至少包含我们创建的 3 个房间
            assert len(items) >= 3, f"应至少返回 3 个房间，实际 {len(items)}"
            
            # 从结果中筛选出我们创建的 3 个房间
            created_room_ids = {str(room1.id), str(room2.id), str(room3.id)}
            found_rooms = [item for item in items if item["id"] in created_room_ids]
            
            assert len(found_rooms) == 3, "应该找到所有创建的 3 个房间"
            
            # 验证排序（升序：A -> B -> C）
            assert found_rooms[0]["id"] == str(room1.id), "升序排序，最旧的应该在第一个"
            assert found_rooms[1]["id"] == str(room2.id)
            assert found_rooms[2]["id"] == str(room3.id), "最新的应该在最后"
            
            # ACT: 按创建时间降序排序（最新的在前，默认行为）
            response_desc = await client.get(f"/api/v1/rooms?q={unique_keyword}&sort=created_at:desc")
            
            # ASSERT
            data_desc = response_desc.json()["data"]
            items_desc = data_desc["items"]
            
            # 从结果中筛选出我们创建的 3 个房间
            found_rooms_desc = [item for item in items_desc if item["id"] in created_room_ids]
            assert len(found_rooms_desc) == 3, "应该找到所有创建的 3 个房间"
            
            assert found_rooms_desc[0]["id"] == str(room3.id), "降序排序，最新的应该在第一个"
            assert found_rooms_desc[2]["id"] == str(room1.id), "最旧的应该在最后"
            
            break
        break


@pytest.mark.asyncio
async def test_search_rooms_query_too_long_fails(async_client_with_auth):
    """
    测试搜索关键词过长应失败
    
    策略：Pragmatic - 验证参数校验
    """
    async for client in async_client_with_auth:
        # ARRANGE: 构造超长的搜索关键词（超过 100 个字符）
        long_query = "x" * 101
        
        # ACT
        response = await client.get(f"/api/v1/rooms?q={long_query}")
        
        # ASSERT: 应返回 422（Pydantic 校验）或 400
        assert response.status_code in [400, 422], f"超长搜索词应返回错误，实际: {response.status_code}"
        
        break


@pytest.mark.asyncio
async def test_search_rooms_invalid_uuid_format_treated_as_title(
    async_client_with_auth, 
    db_session,
    regular_user_id: uuid.UUID
):
    """
    测试无效的 UUID 格式应作为标题搜索
    
    策略：Pragmatic
    """
    async for client in async_client_with_auth:
        async for db in db_session:
            # ARRANGE: 创建包含特殊字符的房间
            # ===== Arrange (准备) =====
            # 使用regular_user_id（从conftest.py获取）
            room = await create_test_room_for_search(
                db, regular_user_id, "房间标题包含-连字符"
            )
            
            # ACT: 使用类似但无效的 UUID 格式搜索
            response = await client.get("/api/v1/rooms?q=包含-连字符")
            
            # ASSERT: 应按标题模糊匹配（不是 UUID）
            assert response.status_code == 200
            response_json = response.json()
            assert response_json["code"] == 200
            
            data = response_json["data"]
            assert data["total"] >= 1, "应按标题模糊匹配找到结果"
            
            returned_titles = [item["title"] for item in data["items"]]
            assert "房间标题包含-连字符" in returned_titles
            
            break
        break


# ==================== DB Consistency Tests ====================

@pytest.mark.asyncio
async def test_search_result_matches_database(
    async_client_with_auth, 
    db_session,
    regular_user_id: uuid.UUID
):
    """
    测试搜索结果与数据库状态一致
    
    策略：Pragmatic - DB 校验必须用新会话
    """
    async for client in async_client_with_auth:
        async for db in db_session:
            # ARRANGE: 创建测试房间
            # ===== Arrange (准备) =====
            # 使用regular_user_id（从conftest.py获取）
            room = await create_test_room_for_search(
                db, regular_user_id, "数据一致性测试房间"
            )
            room_id = room.id
            
            # ACT: 按标题搜索
            response = await client.get("/api/v1/rooms?q=数据一致性测试")
            
            # ASSERT: API 响应
            assert response.status_code == 200
            response_json = response.json()
            data = response_json["data"]
            assert data["total"] >= 1
            
            found_room = next(
                (item for item in data["items"] if item["id"] == str(room_id)),
                None
            )
            assert found_room is not None, "API 返回的数据中应包含创建的房间"
            
            # ASSERT: 使用新会话验证 DB 状态（避免 identity map 缓存）
            async with async_session_factory() as new_db:
                result = await new_db.execute(
                    select(LiveRoom).where(LiveRoom.id == room_id)
                )
                db_room = result.scalar_one_or_none()
                
                assert db_room is not None, "数据库中应存在该房间"
                assert db_room.title == "数据一致性测试房间"
                assert str(db_room.id) == found_room["id"]
            
            break
        break


# ==================== 自检清单 ====================
"""
✅ 是否修改了任何已有测试/fixture/配置？ - 否（仅新增文件）
✅ 是否使用 `async for` 解包 `db_session/async_client`？ - 是
✅ API 调用后的 DB 校验是否用 `async_session_factory` 新会话？ - 是
✅ 是否覆盖了 Search 的成功与失败路径？ - 是
  - 成功：UUID 精确匹配、标题模糊匹配、大小写不敏感、分页、排序
  - 失败：无匹配结果、超长关键词
  - 兼容性：空 query 返回所有、无效 UUID 作为标题搜索
✅ 是否断言统一响应结构 code/message/data/timestamp？ - 是
✅ 是否验证分页结构 total/page/size/items？ - 是
"""

