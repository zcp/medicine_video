"""
LiveCore Service - External 场次状态流转集成测试

覆盖（V15 外部直播流方案）：
- 创建三态（scheduled/live/ready）+ 非法初始状态拒绝
- 状态矩阵全量流转 + 守卫规则（playback_url 必填、ready→live 强制新地址）
- 非法流转拒绝（ready→scheduled / finished→scheduled）
- 时间字段自动维护（live 清 end_time / finished·ready 记 now）
- 幂等切换、并发冲突（409）
- push 场次拒绝手动切换（回调独占）
- source_type 落库与响应透出
- SRS 回调跳过 external 场次（状态不被覆盖）
"""

import uuid
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch

from app.models.live_core import LiveSessionStatus, SourceType
from app.crud import room as crud_room
from app.crud import session as crud_session
from app.schemas.live_core import LiveRoomCreate

# 使用 §2.4 的公开测试流作为播放地址（同一房间不同场次必须用不同地址，受幂等唯一索引约束）
TEST_PLAYBACK_URL = "https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8"
TEST_PLAYBACK_URL_2 = "https://devstreaming-cdn.apple.com/videos/streaming/examples/bipbop_4x3/bipbop_4x3_variant.m3u8"
TEST_PLAYBACK_URL_3 = "https://cph-p2p-msl.akamaized.net/hls/live/2000341/test/master.m3u8"


def parse_iso(value: str) -> datetime:
    """解析 isoformat 时间。

    兼容存量端点响应格式（isoformat() + "Z" 对 aware datetime 会产生
    '+00:00Z' 非标准后缀）：Z / +00:00Z / +00:00 三种结尾均可解析。
    """
    if value.endswith("Z"):
        value = value[:-1]
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


# ==================== 测试辅助函数 ====================

async def create_test_room(db, user_id=None) -> object:
    """在数据库中创建一个测试用的 LiveRoom"""
    room_create = LiveRoomCreate(
        title="TEST_外部流状态流转",
        description="external 场次状态流转测试房间",
        is_private=False,
        record_by_default=True,
    )
    return await crud_room.create(db, obj_in=room_create, user_id=user_id or uuid.uuid4())


async def create_external_session(
    db,
    room_id: uuid.UUID,
    status: LiveSessionStatus = LiveSessionStatus.SCHEDULED,
    playback_url: str = TEST_PLAYBACK_URL,
    start_time: datetime = None,
) -> object:
    """直接创建 external 场次"""
    return await crud_session.create_with_stats(
        db,
        obj_in={
            "room_id": room_id,
            "status": status,
            "start_time": start_time or datetime.now(timezone.utc),
            "end_time": None,
            "playback_url": playback_url,
            "source_type": SourceType.EXTERNAL,
        },
    )


# ==================== 创建三态 ====================

@pytest.mark.asyncio
async def test_create_session_three_states(async_client, db_session, regular_user_token, regular_user_id):
    """通过 API 创建 scheduled/live/ready 三态场次，响应含 source_type=external"""
    async for client in async_client:
        async for db in db_session:
            room = await create_test_room(db, user_id=regular_user_id)
            headers = {"Authorization": f"Bearer {regular_user_token}"}

            # scheduled（默认）
            r1 = await client.post(
                f"/api/v1/rooms/{room.id}/sessions",
                json={"start_time": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
                      "playback_url": TEST_PLAYBACK_URL},
                headers=headers,
            )
            assert r1.status_code == 200, r1.text
            d1 = r1.json()["data"]
            assert d1["status"] == "scheduled"
            assert d1["source_type"] == "external"

            # live（start_time 自动取 now）
            r2 = await client.post(
                f"/api/v1/rooms/{room.id}/sessions",
                json={"start_time": (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat(),
                      "playback_url": TEST_PLAYBACK_URL_2,
                      "status": "live"},
                headers=headers,
            )
            assert r2.status_code == 200, r2.text
            d2 = r2.json()["data"]
            assert d2["status"] == "live"
            assert d2["source_type"] == "external"
            start2 = parse_iso(d2["start_time"])
            assert abs((start2 - datetime.now(timezone.utc)).total_seconds()) < 60

            # ready
            r3 = await client.post(
                f"/api/v1/rooms/{room.id}/sessions",
                json={"start_time": (datetime.now(timezone.utc) + timedelta(hours=3)).isoformat(),
                      "playback_url": TEST_PLAYBACK_URL_3,
                      "status": "ready"},
                headers=headers,
            )
            assert r3.status_code == 200, r3.text
            d3 = r3.json()["data"]
            assert d3["status"] == "ready"
            assert d3["source_type"] == "external"

            # 落库断言
            await db.refresh(room)
            sessions, total = await crud_session.get_multi_by_room_and_total(db, room.id)
            assert total == 3
            statuses = {s.status for s in sessions}
            assert statuses == {LiveSessionStatus.SCHEDULED, LiveSessionStatus.LIVE, LiveSessionStatus.READY}
            assert all(s.source_type == SourceType.EXTERNAL for s in sessions)


@pytest.mark.asyncio
async def test_create_session_invalid_status_rejected(async_client, db_session, regular_user_token, regular_user_id):
    """创建初始状态仅允许 scheduled/live/ready，finished/processing/error 应被拒绝"""
    async for client in async_client:
        async for db in db_session:
            room = await create_test_room(db, user_id=regular_user_id)
            headers = {"Authorization": f"Bearer {regular_user_token}"}

            for invalid in ("finished", "processing", "error"):
                r = await client.post(
                    f"/api/v1/rooms/{room.id}/sessions",
                    json={"start_time": datetime.now(timezone.utc).isoformat(),
                          "playback_url": TEST_PLAYBACK_URL,
                          "status": invalid},
                    headers=headers,
                )
                assert r.status_code == 403, f"status={invalid} 应被拒绝: {r.text}"


# ==================== 状态矩阵与守卫 ====================

@pytest.mark.asyncio
async def test_switch_full_matrix(async_client, db_session, regular_user_token, regular_user_id):
    """全矩阵合法流转（V2.0）：scheduled→live→finished→live(恢复)→finished→ready"""
    async for client in async_client:
        async for db in db_session:
            room = await create_test_room(db, user_id=regular_user_id)
            session = await create_external_session(db, room.id)
            headers = {"Authorization": f"Bearer {regular_user_token}"}
            sid = session.id

            # scheduled → live（开播，用现有 URL）
            r = await client.post(f"/api/v1/sessions/{sid}/status", json={"status": "live"}, headers=headers)
            assert r.status_code == 200, r.text
            assert r.json()["data"]["status"] == "live"

            # live → finished（停播）
            r = await client.post(f"/api/v1/sessions/{sid}/status", json={"status": "finished"}, headers=headers)
            assert r.status_code == 200, r.text
            assert r.json()["data"]["status"] == "finished"

            # finished → live（恢复开播，沿用原地址）
            r = await client.post(f"/api/v1/sessions/{sid}/status", json={"status": "live"}, headers=headers)
            assert r.status_code == 200, r.text
            assert r.json()["data"]["status"] == "live"
            assert r.json()["data"]["playback_url"] == TEST_PLAYBACK_URL

            # live → finished → ready（停播后发布回放）
            r = await client.post(f"/api/v1/sessions/{sid}/status", json={"status": "finished"}, headers=headers)
            assert r.status_code == 200, r.text
            r = await client.post(f"/api/v1/sessions/{sid}/status", json={"status": "ready"}, headers=headers)
            assert r.status_code == 200, r.text
            assert r.json()["data"]["status"] == "ready"


@pytest.mark.asyncio
async def test_switch_requires_playback_url(async_client, db_session, regular_user_token, regular_user_id):
    """转 live 必须 playback_url 非空（创建时无 URL 的场次被守卫拒绝）"""
    async for client in async_client:
        async for db in db_session:
            room = await create_test_room(db, user_id=regular_user_id)
            session = await create_external_session(db, room.id, playback_url=None)
            headers = {"Authorization": f"Bearer {regular_user_token}"}

            r = await client.post(f"/api/v1/sessions/{session.id}/status", json={"status": "live"}, headers=headers)
            assert r.status_code == 403, r.text
            assert "播放地址" in r.json()["data"]["error"]


@pytest.mark.asyncio
async def test_ready_is_terminal_state(async_client, db_session, regular_user_token, regular_user_id):
    """ready 为终态（V2.0）：ready→live / ready→scheduled 均被拒绝"""
    async for client in async_client:
        async for db in db_session:
            room = await create_test_room(db, user_id=regular_user_id)
            ready_s = await create_external_session(db, room.id, status=LiveSessionStatus.READY)
            headers = {"Authorization": f"Bearer {regular_user_token}"}

            r = await client.post(f"/api/v1/sessions/{ready_s.id}/status", json={"status": "live"}, headers=headers)
            assert r.status_code == 403, r.text

            r = await client.post(f"/api/v1/sessions/{ready_s.id}/status", json={"status": "scheduled"}, headers=headers)
            assert r.status_code == 403, r.text


@pytest.mark.asyncio
async def test_illegal_transitions_rejected(async_client, db_session, regular_user_token, regular_user_id):
    """非法流转拒绝：ready→scheduled、finished→scheduled、scheduled→finished"""
    async for client in async_client:
        async for db in db_session:
            room = await create_test_room(db, user_id=regular_user_id)
            headers = {"Authorization": f"Bearer {regular_user_token}"}

            # ready → scheduled 拒绝
            ready_s = await create_external_session(db, room.id, status=LiveSessionStatus.READY)
            r = await client.post(f"/api/v1/sessions/{ready_s.id}/status", json={"status": "scheduled"}, headers=headers)
            assert r.status_code == 403, r.text

            # finished → scheduled 拒绝
            finished_s = await create_external_session(db, room.id, status=LiveSessionStatus.FINISHED)
            r = await client.post(f"/api/v1/sessions/{finished_s.id}/status", json={"status": "scheduled"}, headers=headers)
            assert r.status_code == 403, r.text

            # live → scheduled 拒绝（V2.0：回预告后开播时间无法定义）
            live_s = await create_external_session(db, room.id, status=LiveSessionStatus.LIVE)
            r = await client.post(f"/api/v1/sessions/{live_s.id}/status", json={"status": "scheduled"}, headers=headers)
            assert r.status_code == 403, r.text

            # scheduled → finished 拒绝（必须先 live）
            scheduled_s = await create_external_session(db, room.id, status=LiveSessionStatus.SCHEDULED)
            r = await client.post(f"/api/v1/sessions/{scheduled_s.id}/status", json={"status": "finished"}, headers=headers)
            assert r.status_code == 403, r.text


# ==================== 时间字段维护 ====================

@pytest.mark.asyncio
async def test_time_fields_maintenance(async_client, db_session, regular_user_token, regular_user_id):
    """转 live 清空 end_time；转 finished 自动记录 end_time；转 live 后 end_time 再次清空"""
    async for client in async_client:
        async for db in db_session:
            room = await create_test_room(db, user_id=regular_user_id)
            session = await create_external_session(
                db, room.id,
                status=LiveSessionStatus.FINISHED,
                start_time=datetime.now(timezone.utc) - timedelta(hours=1),
            )
            headers = {"Authorization": f"Bearer {regular_user_token}"}
            sid = session.id

            # finished（已有 start_time）→ live：end_time 清空
            r = await client.post(f"/api/v1/sessions/{sid}/status", json={"status": "live"}, headers=headers)
            assert r.status_code == 200, r.text
            assert r.json()["data"]["end_time"] is None

            # live → finished：end_time 自动记录 now
            r = await client.post(f"/api/v1/sessions/{sid}/status", json={"status": "finished"}, headers=headers)
            assert r.status_code == 200, r.text
            end_time = parse_iso(r.json()["data"]["end_time"])
            assert abs((end_time - datetime.now(timezone.utc)).total_seconds()) < 60


# ==================== 幂等与并发 ====================

@pytest.mark.asyncio
async def test_idempotent_switch(async_client, db_session, regular_user_token, regular_user_id):
    """目标状态 == 当前状态时幂等返回成功"""
    async for client in async_client:
        async for db in db_session:
            room = await create_test_room(db, user_id=regular_user_id)
            session = await create_external_session(db, room.id, status=LiveSessionStatus.LIVE)
            headers = {"Authorization": f"Bearer {regular_user_token}"}

            r = await client.post(f"/api/v1/sessions/{session.id}/status", json={"status": "live"}, headers=headers)
            assert r.status_code == 200, r.text
            assert r.json()["data"]["status"] == "live"


@pytest.mark.asyncio
async def test_switch_conflict_returns_409(async_client, db_session, regular_user_token, regular_user_id):
    """并发冲突（条件更新影响行数 0）返回 409"""
    async for client in async_client:
        async for db in db_session:
            room = await create_test_room(db, user_id=regular_user_id)
            session = await create_external_session(db, room.id)
            headers = {"Authorization": f"Bearer {regular_user_token}"}

            with patch(
                "app.crud.session.update_status_conditional",
                new=__import__("unittest.mock", fromlist=["AsyncMock"]).AsyncMock(return_value=0),
            ):
                r = await client.post(f"/api/v1/sessions/{session.id}/status", json={"status": "live"}, headers=headers)
                assert r.status_code == 409, r.text


# ==================== push 隔离 ====================

@pytest.mark.asyncio
async def test_push_session_switch_rejected(async_client, db_session, regular_user_token, regular_user_id):
    """push 场次调 status 端点 → 403（推流场次回调独占）"""
    async for client in async_client:
        async for db in db_session:
            room = await create_test_room(db, user_id=regular_user_id)
            # 直接创建 push 场次（source_type 默认 push）
            push_session = await crud_session.create_with_stats(
                db,
                obj_in={
                    "room_id": room.id,
                    "status": LiveSessionStatus.SCHEDULED,
                    "start_time": datetime.now(timezone.utc),
                    "playback_url": TEST_PLAYBACK_URL,
                },
            )
            assert push_session.source_type == SourceType.PUSH
            headers = {"Authorization": f"Bearer {regular_user_token}"}

            r = await client.post(f"/api/v1/sessions/{push_session.id}/status", json={"status": "live"}, headers=headers)
            assert r.status_code == 403, r.text


@pytest.mark.asyncio
async def test_on_publish_skips_external_sessions(async_client, db_session, regular_user_token, regular_user_id):
    """SRS on-publish 回调不覆盖 external 场次状态（仅作用于 push 场次）"""
    async for client in async_client:
        async for db in db_session:
            room = await create_test_room(db, user_id=regular_user_id)
            ext_scheduled = await create_external_session(db, room.id, status=LiveSessionStatus.SCHEDULED)

            payload = {
                "action": "on_publish",
                "client_id": "test_client_external_skip",
                "ip": "192.168.1.100",
                "vhost": "__defaultVhost__",
                "app": "live",
                "stream": room.stream_key,
            }
            response = await client.post("/api/v1/internal/srs/on-publish", json=payload)
            assert response.status_code == 200, response.text

            # external scheduled 场次状态未被覆盖
            await db.refresh(ext_scheduled)
            assert ext_scheduled.status == LiveSessionStatus.SCHEDULED


@pytest.mark.asyncio
async def test_session_list_response_contains_source_type(async_client, db_session, regular_user_token, regular_user_id):
    """场次列表接口（GET /rooms/{id}/sessions）响应必须包含 source_type（前端按钮显示依赖）"""
    async for client in async_client:
        async for db in db_session:
            room = await create_test_room(db, user_id=regular_user_id)
            session = await create_external_session(db, room.id, status=LiveSessionStatus.LIVE)
            headers = {"Authorization": f"Bearer {regular_user_token}"}

            resp = await client.get(f"/api/v1/rooms/{room.id}/sessions", headers=headers)
            assert resp.status_code == 200, resp.text
            items = resp.json()["data"]["items"]
            assert len(items) == 1
            assert items[0]["source_type"] == "external"
            assert items[0]["playback_url"] == TEST_PLAYBACK_URL


# ==================== 惰性补转（自动开播 v1 形态） ====================

@pytest.mark.asyncio
async def test_lazy_promote_not_due(async_client, db_session):
    """external scheduled 未到期 → 读详情不转 live"""
    async for client in async_client:
        async for db in db_session:
            room = await create_test_room(db)
            session = await create_external_session(
                db, room.id,
                start_time=datetime.now(timezone.utc) + timedelta(hours=1),
            )

            resp = await client.get(f"/api/v1/sessions/{session.id}")
            assert resp.status_code == 200, resp.text
            assert resp.json()["data"]["status"] == "scheduled"

            await db.refresh(session)
            assert session.status == LiveSessionStatus.SCHEDULED


@pytest.mark.asyncio
async def test_lazy_promote_due_on_session_read(async_client, db_session):
    """external scheduled 已到期 → 首次读详情自动转 live"""
    async for client in async_client:
        async for db in db_session:
            room = await create_test_room(db)
            session = await create_external_session(
                db, room.id,
                start_time=datetime.now(timezone.utc) - timedelta(minutes=5),
            )

            resp = await client.get(f"/api/v1/sessions/{session.id}")
            assert resp.status_code == 200, resp.text
            assert resp.json()["data"]["status"] == "live"

            await db.refresh(session)
            assert session.status == LiveSessionStatus.LIVE


@pytest.mark.asyncio
async def test_lazy_promote_skips_push(async_client, db_session):
    """push scheduled 已到期 → 不转 live（惰性补转仅作用于 external）"""
    async for client in async_client:
        async for db in db_session:
            room = await create_test_room(db)
            push_session = await crud_session.create_with_stats(
                db,
                obj_in={
                    "room_id": room.id,
                    "status": LiveSessionStatus.SCHEDULED,
                    "start_time": datetime.now(timezone.utc) - timedelta(minutes=5),
                    "playback_url": TEST_PLAYBACK_URL,
                },
            )

            resp = await client.get(f"/api/v1/sessions/{push_session.id}")
            assert resp.status_code == 200, resp.text
            assert resp.json()["data"]["status"] == "scheduled"


@pytest.mark.asyncio
async def test_lazy_promote_on_room_read(async_client, db_session, regular_user_token, regular_user_id):
    """房间详情读取路径：最新 external scheduled 到期 → 房间 live_status 自动转 live"""
    async for client in async_client:
        async for db in db_session:
            room = await create_test_room(db, user_id=regular_user_id)
            session = await create_external_session(
                db, room.id,
                start_time=datetime.now(timezone.utc) - timedelta(minutes=5),
            )
            headers = {"Authorization": f"Bearer {regular_user_token}"}

            resp = await client.get(f"/api/v1/rooms/{room.id}", headers=headers)
            assert resp.status_code == 200, resp.text
            assert resp.json()["data"]["live_status"] == "live"

            await db.refresh(session)
            assert session.status == LiveSessionStatus.LIVE
