"""
私密房 WS 方案 B 正式测试（阶段 2 收编，2026-08-11 V1.1 决策 D3）

覆盖：
- 匿名订阅私密房留言流 → close 4403
- 他人（登录非创建者）订阅 → close 4403
- 创建者订阅 → 连接成功

注：TestClient WS 在 Windows ProactorEventLoop 下不稳定（'NoneType' send / sendfile in progress，
环境性缺陷，非业务逻辑问题），故 Windows 跳过，Linux/CI 必验。
"""
import sys
import time
import uuid

import jwt
import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from app.main import app

pytestmark = [
    pytest.mark.skipif(sys.platform.startswith("win"), reason="TestClient WS 在 Windows ProactorEventLoop 不稳定，Linux/CI 验证"),
]


def _make_token(user_id: uuid.UUID, role: str = "REGULAR") -> str:
    return jwt.encode(
        {
            "user_id": str(user_id),
            "type": "access",
            "role": role,
            "sub": str(user_id),
            "exp": int(time.time()) + 3600,
        },
        "my-key",
        algorithm="HS256",
    )


def _cleanup_room(room_id: str) -> None:
    from app.database import SessionLocal
    from app.models.live_core import LiveRoom

    with SessionLocal() as db:
        room = db.get(LiveRoom, uuid.UUID(room_id))
        if room:
            db.delete(room)
            db.commit()


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


@pytest.fixture(scope="module")
def ws_private_room(client) -> dict:
    """创建测试私密房；清理走同步 SessionLocal 硬删（规避 TestClient 连接池问题）"""
    owner_token = _make_token(uuid.uuid4())
    resp = client.post(
        "/api/v1/rooms",
        json={
            "title": f"PrivateWsRoom-{uuid.uuid4().hex[:8]}",
            "description": "ws scheme b test room",
            "is_private": True,
        },
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert resp.status_code == 200, f"创建 WS 测试房失败: {resp.status_code} {resp.text}"
    room_id = resp.json()["data"]["id"]
    yield {"id": room_id, "owner_token": owner_token}
    _cleanup_room(room_id)


def test_ws_anonymous_private_room_closed_4403(client, ws_private_room):
    """方案 B：匿名订阅私密房留言流 → 4403"""
    with pytest.raises(WebSocketDisconnect) as exc_info:
        with client.websocket_connect(f"/api/v1/ws/rooms/{ws_private_room['id']}/messages"):
            pass
    assert exc_info.value.code == 4403, f"匿名 WS 应 4403: {exc_info.value.code}"


def test_ws_other_user_private_room_closed_4403(client, ws_private_room):
    """方案 B：他人（登录非创建者）订阅私密房留言流 → 4403"""
    other_token = _make_token(uuid.uuid4())
    with pytest.raises(WebSocketDisconnect) as exc_info:
        with client.websocket_connect(
            f"/api/v1/ws/rooms/{ws_private_room['id']}/messages",
            headers={"Authorization": f"Bearer {other_token}"},
        ):
            pass
    assert exc_info.value.code == 4403, f"他人 WS 应 4403: {exc_info.value.code}"


def test_ws_owner_private_room_connects(client, ws_private_room):
    """方案 B：创建者订阅私密房留言流 → 连接成功"""
    with client.websocket_connect(
        f"/api/v1/ws/rooms/{ws_private_room['id']}/messages",
        headers={"Authorization": f"Bearer {ws_private_room['owner_token']}"},
    ):
        pass
