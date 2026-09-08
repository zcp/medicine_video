"""
LiveCore Service - m3u8 代理端点（V15 外部直播流方案）

设计要点（§4.5/§5.6）：
- session 关联（防 SSRF）：只代理库中已存的 playback_url，不做通用 ?url= 代理
- 两级重写：master 清单内所有 URI 行重写为基于清单 URL 的外部绝对地址，
  播放器随后直连外部子清单/切片（公开流场景代理流量趋近于零）
- 安全：仅 http(s)；域名解析后拦截内网/环回/链路本地/多播/保留地址；
  禁止重定向跟随（allow_redirects=False，3xx 直接拒绝）；超时 + 大小限制
- 鉴权头注入：EXTERNAL_STREAM_HEADERS 配置项（按外部平台文档配置）
"""

import ipaddress
import json
import logging
import socket
import uuid
from typing import Optional, Tuple
from urllib.parse import urljoin, urlparse

import httpx
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.deps import get_current_user_optional
from app.core.permissions import check_room_visibility
from app.core.response import error_response
from app.crud import room as crud_room
from app.crud import session as crud_session
from app.database import get_db
from app.exceptions import NotFoundException

logger = logging.getLogger(__name__)

proxy_router = APIRouter(tags=["m3u8-proxy"])

# 代理超时（秒）
PROXY_TIMEOUT = 5.0
# 清单响应大小上限（10MB）
PROXY_MAX_BYTES = 10 * 1024 * 1024


# ==================== 安全校验 ====================

def _is_forbidden_ip(ip: str) -> bool:
    """判断 IP 是否属于禁止访问的地址（SSRF 防护：内网/环回/链路本地/多播/保留/未指定）"""
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return True
    return (
        addr.is_private
        or addr.is_loopback
        or addr.is_link_local
        or addr.is_reserved
        or addr.is_multicast
        or addr.is_unspecified
    )


def check_url_safety(url: str) -> None:
    """校验 URL 安全：仅 http/https，域名解析后不允许内网/环回等地址。

    Raises:
        ValueError: URL 不安全（非 http(s) / 域名解析失败 / 命中禁止网段）
    """
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError("仅支持 http/https 地址")
    hostname = parsed.hostname
    if not hostname:
        raise ValueError("URL 缺少主机名")
    try:
        infos = socket.getaddrinfo(hostname, None)
    except socket.gaierror:
        raise ValueError("域名解析失败")
    for info in infos:
        if _is_forbidden_ip(info[4][0]):
            raise ValueError("目标地址不允许（内网/环回/保留地址）")


# ==================== 两级清单重写 ====================

def rewrite_m3u8(content: str, base_url: str) -> str:
    """两级重写：将清单内所有 URI 行解析为基于清单 URL 的外部绝对地址。

    兼容性（§2.4 样本验证得出）：
    - 相对路径（mastermaster_video10000k.m3u8 / gear1/prog_index.m3u8）→ urljoin
    - 绝对路径（/videos/a.m3u8）→ scheme://host + path
    - 协议相对（//cdn.example.com/a.m3u8）→ scheme + :// + path
    - 已是绝对 URL → urljoin 幂等保留
    - 纯音频档（STREAM-INF 无视频，如 Apple bipbop gear0）→ 不受影响
    - URI 携带 query（?token=xxx）→ urljoin 保留 query
    - 注释行、空行、#EXT-* 标记行 → 原样保留
    """
    lines = content.splitlines()
    out = []
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            out.append(urljoin(base_url, stripped))
        else:
            out.append(line)
    return "\n".join(out)


def parse_stream_headers() -> dict:
    """解析 EXTERNAL_STREAM_HEADERS 配置（JSON 字符串 → dict）。解析失败返回空字典。"""
    raw = (settings.EXTERNAL_STREAM_HEADERS or "").strip()
    if not raw:
        return {}
    try:
        headers = json.loads(raw)
        if not isinstance(headers, dict):
            return {}
        return {str(k): str(v) for k, v in headers.items()}
    except json.JSONDecodeError:
        logger.warning("EXTERNAL_STREAM_HEADERS 配置不是合法 JSON，已忽略")
        return {}


# ==================== 外部拉取 ====================

async def fetch_external(url: str) -> Tuple[Optional[bytes], int]:
    """拉取外部 URL（重定向拦截 + 超时 + 大小限制 + 鉴权头注入）。

    Returns:
        (content, status)：成功返回 (bytes, 200)；失败返回 (None, http状态/502/504/413)
    """
    try:
        async with httpx.AsyncClient(follow_redirects=False, timeout=PROXY_TIMEOUT) as client:
            resp = await client.get(url, headers=parse_stream_headers())
    except httpx.TimeoutException:
        logger.warning(f"代理拉取外部流超时: url={url}")
        return None, 504
    except httpx.HTTPError as e:
        logger.warning(f"代理拉取外部流失败: url={url}, error={e}")
        return None, 502

    if resp.status_code >= 300:
        # allow_redirects=False：3xx 一律拒绝（防重定向跳内网），其余非 2xx 透传状态
        logger.warning(f"代理拉取外部流返回非 2xx: url={url}, status={resp.status_code}")
        return None, resp.status_code

    if len(resp.content) > PROXY_MAX_BYTES:
        logger.warning(f"代理拉取外部流超限: url={url}, size={len(resp.content)}")
        return None, 413

    return resp.content, 200


# ==================== 端点 ====================

@proxy_router.get("/m3u8/{session_id}")
async def proxy_m3u8(
    session_id: uuid.UUID,
    request: Request,
    current_user: Optional[dict] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    """代理场次 playback_url（session 关联，防 SSRF）。

    公开房间可匿名访问；私密房间需可见性校验（匿名/无权限返回 404 隐藏存在性）。
    """
    logger.info(f"处理 m3u8 代理请求: session_id={session_id}")

    # 1. 查场次
    session = await crud_session.get(db, session_id=session_id)
    if session is None:
        return JSONResponse(
            status_code=404,
            content=error_response(code=2001, message="资源不存在",
                                   data={"resource": "Session", "id": str(session_id)}),
        )

    # 2. 房间可见性校验（私密房间 404 隐藏存在性）
    room = await crud_room.get(db, room_id=session.room_id)
    if room is None:
        return JSONResponse(
            status_code=404,
            content=error_response(code=2001, message="资源不存在",
                                   data={"resource": "Room", "id": str(session.room_id)}),
        )
    user_id = uuid.UUID(current_user["user_id"]) if current_user else None
    role = current_user.get("role") if current_user else None
    try:
        check_room_visibility(room, user_id, role)
    except NotFoundException:
        return JSONResponse(
            status_code=404,
            content=error_response(code=2001, message="资源不存在",
                                   data={"resource": "Room", "id": str(session.room_id)}),
        )

    # 3. playback_url 校验
    playback_url = session.playback_url
    if not playback_url or not str(playback_url).strip():
        logger.warning(f"场次无播放地址: session_id={session_id}")
        return JSONResponse(
            status_code=404,
            content=error_response(code=2001, message="播放地址不存在", data=None),
        )

    # 4. URL 安全校验（SSRF 防护）
    try:
        check_url_safety(playback_url)
    except ValueError as e:
        logger.warning(f"代理请求被安全校验拒绝: session_id={session_id}, url={playback_url}, reason={e}")
        return JSONResponse(
            status_code=403,
            content=error_response(code=4001, message="非法的播放地址", data={"error": str(e)}),
        )

    # 5. 拉取外部清单
    content, status = await fetch_external(playback_url)
    if content is None:
        return JSONResponse(
            status_code=status,
            content=error_response(code=2000, message="外部流获取失败", data={"status": status}),
        )

    # 6. 两级重写：URI 行解析为外部绝对地址（播放器直连外部子清单/切片）
    rewritten = rewrite_m3u8(content.decode("utf-8", errors="replace"), playback_url)

    logger.info(f"m3u8 代理成功: session_id={session_id}, status={status}, size={len(rewritten)}")
    return Response(
        content=rewritten,
        media_type="application/x-mpegURL",
        headers={"Cache-Control": "no-store"},
    )
