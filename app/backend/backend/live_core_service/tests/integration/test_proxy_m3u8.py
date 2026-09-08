"""
LiveCore Service - m3u8 代理端点测试（V15）

覆盖：
- rewrite_m3u8 两级重写纯函数（相对/绝对/协议相对/纯音频档/query/引号/幂等）
- proxy 端点集成（mock fetch_external）：公开/私密房间、URL 校验、重写应用、响应头
- fetch_external（mock httpx）：重定向拦截、超时、大小限制、头注入
"""

import uuid
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, AsyncMock, MagicMock

import httpx
import pytest

from app.crud import room as crud_room
from app.crud import session as crud_session
from app.models.live_core import LiveSessionStatus, SourceType
from app.schemas.live_core import LiveRoomCreate
from app.api.v1.endpoints.proxy import (
    rewrite_m3u8,
    check_url_safety,
    parse_stream_headers,
)

TEST_PLAYBACK_URL = "https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8"


# ==================== 重写纯函数测试 ====================

class TestRewriteM3u8:
    """两级重写纯函数（无网络依赖）"""

    def test_relative_uri_rewritten_to_absolute(self):
        """相对路径（§2.4 样本特征：master 内子清单相对路径）"""
        content = (
            "#EXTM3U\n"
            "#EXT-X-VERSION:3\n"
            "#EXT-X-STREAM-INF:BANDWIDTH=2149280,RESOLUTION=1280x720\n"
            "url_0/193039199_mp4_h264_aac_hd_7.m3u8\n"
            "#EXT-X-STREAM-INF:BANDWIDTH=246440,RESOLUTION=320x184\n"
            "url_2/193039199_mp4_h264_aac_ld_7.m3u8\n"
        )
        base = "https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8"
        out = rewrite_m3u8(content, base)
        assert "https://test-streams.mux.dev/x36xhzz/url_0/193039199_mp4_h264_aac_hd_7.m3u8" in out
        assert "https://test-streams.mux.dev/x36xhzz/url_2/193039199_mp4_h264_aac_ld_7.m3u8" in out

    def test_absolute_uri_idempotent(self):
        """已是绝对 URL 时 urljoin 幂等保留"""
        content = "#EXTM3U\nhttps://cdn.example.com/videos/seg_1.ts\n"
        out = rewrite_m3u8(content, "https://proxy.example.com/a/b/master.m3u8")
        assert "https://cdn.example.com/videos/seg_1.ts" in out

    def test_absolute_path_uri(self):
        """绝对路径 URI（/videos/a.m3u8）→ scheme://host + path"""
        content = "#EXTM3U\n/videos/a.m3u8\n"
        out = rewrite_m3u8(content, "https://cdn.example.com/live/master.m3u8")
        assert "https://cdn.example.com/videos/a.m3u8" in out

    def test_protocol_relative_uri(self):
        """协议相对 URI（//host/path）→ 补全 scheme"""
        content = "#EXTM3U\n//cdn2.example.com/live/stream.m3u8\n"
        out = rewrite_m3u8(content, "https://cdn.example.com/master.m3u8")
        assert "https://cdn2.example.com/live/stream.m3u8" in out

    def test_audio_only_variant(self):
        """纯音频档（Apple bipbop gear0，STREAM-INF 无视频）正常重写"""
        content = (
            "#EXTM3U\n"
            "#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=41457,CODECS=\"mp4a.40.2\"\n"
            "gear0/prog_index.m3u8\n"
        )
        out = rewrite_m3u8(content, "https://devstreaming-cdn.apple.com/videos/streaming/examples/bipbop_4x3/bipbop_4x3_variant.m3u8")
        assert "https://devstreaming-cdn.apple.com/videos/streaming/examples/bipbop_4x3/gear0/prog_index.m3u8" in out

    def test_uri_with_query(self):
        """URI 携带 query（token 参数）时保留"""
        content = "#EXTM3U\nseg_1.ts?token=abc123&exp=999\n"
        out = rewrite_m3u8(content, "https://cdn.example.com/live/master.m3u8")
        assert "https://cdn.example.com/live/seg_1.ts?token=abc123&exp=999" in out

    def test_comments_and_empty_lines_untouched(self):
        """注释行、空行、EXT 标记行原样保留"""
        content = "#EXTM3U\n\n#EXT-X-VERSION:3\n#EXT-X-TARGETDURATION:6\n\nseg_1.ts\n"
        out = rewrite_m3u8(content, "https://cdn.example.com/master.m3u8")
        assert out.startswith("#EXTM3U\n\n#EXT-X-VERSION:3\n#EXT-X-TARGETDURATION:6\n\n")
        assert out.endswith("https://cdn.example.com/seg_1.ts")

    def test_media_playlist_slice_rewrite(self):
        """media 清单切片相对路径（模拟播放器直连外部后返回的清单）"""
        content = (
            "#EXTM3U\n"
            "#EXT-X-VERSION:3\n"
            "#EXTINF:6.006,\n"
            "193039199_mp4_h264_aac_hd_7_0.ts\n"
            "#EXTINF:6.006,\n"
            "193039199_mp4_h264_aac_hd_7_1.ts\n"
            "#EXT-X-ENDLIST\n"
        )
        base = "https://test-streams.mux.dev/x36xhzz/url_0/193039199_mp4_h264_aac_hd_7.m3u8"
        out = rewrite_m3u8(content, base)
        assert "https://test-streams.mux.dev/x36xhzz/url_0/193039199_mp4_h264_aac_hd_7_0.ts" in out
        assert out.endswith("#EXT-X-ENDLIST")


# ==================== URL 安全校验测试 ====================

class TestCheckUrlSafety:
    """URL 安全校验（SSRF 防护）"""

    def test_https_ok(self):
        check_url_safety("https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8")  # 不应抛异常

    def test_non_http_scheme_rejected(self):
        with pytest.raises(ValueError):
            check_url_safety("ftp://example.com/a.m3u8")

    def test_loopback_rejected(self):
        with pytest.raises(ValueError):
            check_url_safety("http://127.0.0.1:8000/media/a.m3u8")

    def test_private_ip_rejected(self):
        with pytest.raises(ValueError):
            check_url_safety("http://10.0.0.1/a.m3u8")
        with pytest.raises(ValueError):
            check_url_safety("http://192.168.1.1/a.m3u8")

    def test_link_local_rejected(self):
        with pytest.raises(ValueError):
            check_url_safety("http://169.254.1.1/a.m3u8")

    def test_missing_host_rejected(self):
        with pytest.raises(ValueError):
            check_url_safety("http:///a.m3u8")


# ==================== 头解析测试 ====================

class TestParseStreamHeaders:
    """EXTERNAL_STREAM_HEADERS 解析"""

    def test_empty_returns_empty(self, monkeypatch):
        monkeypatch.setattr("app.api.v1.endpoints.proxy.settings", MagicMock(EXTERNAL_STREAM_HEADERS=""))
        assert parse_stream_headers() == {}

    def test_valid_json(self, monkeypatch):
        monkeypatch.setattr(
            "app.api.v1.endpoints.proxy.settings",
            MagicMock(EXTERNAL_STREAM_HEADERS='{"X-API-Key": "secret", "User-Agent": "LiveCore/1.0"}'),
        )
        assert parse_stream_headers() == {"X-API-Key": "secret", "User-Agent": "LiveCore/1.0"}

    def test_invalid_json_returns_empty(self, monkeypatch):
        monkeypatch.setattr(
            "app.api.v1.endpoints.proxy.settings",
            MagicMock(EXTERNAL_STREAM_HEADERS="not-json"),
        )
        assert parse_stream_headers() == {}


# ==================== 端点集成测试（mock fetch_external） ====================

async def create_room(db, user_id=None, is_private=False):
    room_create = LiveRoomCreate(
        title="TEST_代理端点",
        description="m3u8 代理端点测试房间",
        is_private=is_private,
        record_by_default=True,
    )
    return await crud_room.create(db, obj_in=room_create, user_id=user_id or uuid.uuid4())


async def create_external_session(db, room_id, playback_url=TEST_PLAYBACK_URL):
    return await crud_session.create_with_stats(
        db,
        obj_in={
            "room_id": room_id,
            "status": LiveSessionStatus.LIVE,
            "start_time": datetime.now(timezone.utc),
            "end_time": None,
            "playback_url": playback_url,
            "source_type": SourceType.EXTERNAL,
        },
    )


MASTER_SAMPLE = (
    "#EXTM3U\n"
    "#EXT-X-STREAM-INF:BANDWIDTH=2149280,CODECS=\"mp4a.40.2,avc1.64001f\",RESOLUTION=1280x720\n"
    "url_0/193039199_mp4_h264_aac_hd_7.m3u8\n"
)


@pytest.mark.asyncio
async def test_proxy_success_public_room(async_client, db_session):
    """公开房间 + 有效场次 → 200 + 重写后清单 + no-store"""
    async for client in async_client:
        async for db in db_session:
            room = await create_room(db)
            session = await create_external_session(db, room.id)

            with patch("app.api.v1.endpoints.proxy.fetch_external", new=AsyncMock(return_value=(MASTER_SAMPLE.encode(), 200))):
                resp = await client.get(f"/api/v1/proxy/m3u8/{session.id}")

            assert resp.status_code == 200, resp.text
            assert resp.headers.get("cache-control") == "no-store"
            body = resp.text
            assert "https://test-streams.mux.dev/x36xhzz/url_0/193039199_mp4_h264_aac_hd_7.m3u8" in body


@pytest.mark.asyncio
async def test_proxy_private_room_anonymous_unlisted(async_client, db_session):
    """私密房间匿名访问：unlisted 语义（V1.1 D1）持 room_id 可读 → 200"""
    async for client in async_client:
        async for db in db_session:
            room = await create_room(db, is_private=True)
            session = await create_external_session(db, room.id)

            with patch("app.api.v1.endpoints.proxy.fetch_external", new=AsyncMock(return_value=(MASTER_SAMPLE.encode(), 200))):
                resp = await client.get(f"/api/v1/proxy/m3u8/{session.id}")

            assert resp.status_code == 200, resp.text


@pytest.mark.asyncio
async def test_proxy_session_not_found(async_client, db_session):
    """场次不存在 → 404"""
    async for client in async_client:
        async for db in db_session:
            resp = await client.get(f"/api/v1/proxy/m3u8/{uuid.uuid4()}")
            assert resp.status_code == 404


@pytest.mark.asyncio
async def test_proxy_missing_playback_url(async_client, db_session):
    """场次无播放地址 → 404"""
    async for client in async_client:
        async for db in db_session:
            room = await create_room(db)
            session = await create_external_session(db, room.id, playback_url=None)
            resp = await client.get(f"/api/v1/proxy/m3u8/{session.id}")
            assert resp.status_code == 404


@pytest.mark.asyncio
async def test_proxy_unsafe_url_rejected(async_client, db_session):
    """playback_url 指向内网/非 http(s) → 403"""
    async for client in async_client:
        async for db in db_session:
            room = await create_room(db)
            for unsafe in ("http://127.0.0.1:8000/a.m3u8", "ftp://example.com/a.m3u8"):
                session = await create_external_session(db, room.id, playback_url=unsafe)
                resp = await client.get(f"/api/v1/proxy/m3u8/{session.id}")
                assert resp.status_code == 403, f"unsafe url={unsafe}"


@pytest.mark.asyncio
async def test_proxy_external_error_passthrough(async_client, db_session):
    """外部返回非 2xx → 透传状态码"""
    async for client in async_client:
        async for db in db_session:
            room = await create_room(db)
            session = await create_external_session(db, room.id)

            with patch("app.api.v1.endpoints.proxy.fetch_external", new=AsyncMock(return_value=(None, 404))):
                resp = await client.get(f"/api/v1/proxy/m3u8/{session.id}")
            assert resp.status_code == 404

            with patch("app.api.v1.endpoints.proxy.fetch_external", new=AsyncMock(return_value=(None, 502))):
                resp = await client.get(f"/api/v1/proxy/m3u8/{session.id}")
            assert resp.status_code == 502


# ==================== fetch_external 测试（mock httpx） ====================

@pytest.mark.asyncio
async def test_fetch_external_success(monkeypatch):
    """正常拉取返回内容"""
    resp = MagicMock(status_code=200, content=b"#EXTM3U\n")
    client_mock = MagicMock()
    client_mock.get = AsyncMock(return_value=resp)
    client_cm = AsyncMock()
    client_cm.__aenter__ = AsyncMock(return_value=client_mock)
    client_cm.__aexit__ = AsyncMock(return_value=False)
    monkeypatch.setattr(
        "app.api.v1.endpoints.proxy.httpx.AsyncClient", MagicMock(return_value=client_cm)
    )
    content, status = await __import__("app.api.v1.endpoints.proxy", fromlist=["fetch_external"]).fetch_external("https://example.com/a.m3u8")
    assert content == b"#EXTM3U\n"
    assert status == 200


@pytest.mark.asyncio
async def test_fetch_external_redirect_rejected(monkeypatch):
    """3xx 重定向一律拒绝（防重定向跳内网）"""
    resp = MagicMock(status_code=302, headers={"location": "http://127.0.0.1/"})
    client_mock = MagicMock()
    client_mock.get = AsyncMock(return_value=resp)
    client_cm = AsyncMock()
    client_cm.__aenter__ = AsyncMock(return_value=client_mock)
    client_cm.__aexit__ = AsyncMock(return_value=False)
    monkeypatch.setattr(
        "app.api.v1.endpoints.proxy.httpx.AsyncClient", MagicMock(return_value=client_cm)
    )
    content, status = await __import__("app.api.v1.endpoints.proxy", fromlist=["fetch_external"]).fetch_external("https://example.com/a.m3u8")
    assert content is None
    assert status == 302


@pytest.mark.asyncio
async def test_fetch_external_timeout(monkeypatch):
    """超时 → 504"""
    client_mock = MagicMock()
    client_mock.get = AsyncMock(side_effect=httpx.TimeoutException("timeout"))
    client_cm = AsyncMock()
    client_cm.__aenter__ = AsyncMock(return_value=client_mock)
    client_cm.__aexit__ = AsyncMock(return_value=False)
    monkeypatch.setattr(
        "app.api.v1.endpoints.proxy.httpx.AsyncClient", MagicMock(return_value=client_cm)
    )
    content, status = await __import__("app.api.v1.endpoints.proxy", fromlist=["fetch_external"]).fetch_external("https://example.com/a.m3u8")
    assert content is None
    assert status == 504


@pytest.mark.asyncio
async def test_fetch_external_oversize(monkeypatch):
    """超过 10MB → 413"""
    resp = MagicMock(status_code=200, content=b"x" * (10 * 1024 * 1024 + 1))
    client_mock = MagicMock()
    client_mock.get = AsyncMock(return_value=resp)
    client_cm = AsyncMock()
    client_cm.__aenter__ = AsyncMock(return_value=client_mock)
    client_cm.__aexit__ = AsyncMock(return_value=False)
    monkeypatch.setattr(
        "app.api.v1.endpoints.proxy.httpx.AsyncClient", MagicMock(return_value=client_cm)
    )
    content, status = await __import__("app.api.v1.endpoints.proxy", fromlist=["fetch_external"]).fetch_external("https://example.com/a.m3u8")
    assert content is None
    assert status == 413
