"""
PR 1A: 管理端全站房间列表

Endpoint: GET /api/v1/admin/rooms
权限：仅 ADMIN / SUPERADMIN（verify_admin_role，非管理员 403/3003）
"""

import logging
import uuid
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import verify_admin_role
from app.core.response import success_response, error_response
from app.database import get_db
from app.services.room_service import RoomService
from app.services.room_card_service import get_room_card_map

logger = logging.getLogger(__name__)

admin_rooms_router = APIRouter(tags=["admin-rooms"])


@admin_rooms_router.get("/rooms")
async def admin_list_rooms(
    request: Request,
    q: Optional[str] = Query(None, max_length=100, description="标题模糊搜索"),
    owner_user_id: Optional[uuid.UUID] = Query(None, description="房主 public_id"),
    is_private: Optional[bool] = Query(None, description="按私密筛选；省略=全部"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页大小"),
    current_user: dict = Depends(verify_admin_role),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    try:
        service = RoomService(db=db)
        rooms, total = await service.list_admin_rooms(
            page=page, size=size,
            q=q, owner_user_id=owner_user_id, is_private=is_private,
        )
        base_url = str(request.base_url).rstrip("/")

        # 批量聚合房间卡片字段（复用 room_card_service，附加上代表场次状态 room_live_status）
        room_card_map = {}
        if rooms:
            try:
                card_map_raw = await get_room_card_map(db, [room.id for room in rooms], include_owner=True)
                room_card_map = {str(k): v for k, v in card_map_raw.items()}
            except Exception as e:  # noqa: BLE001
                logger.error("Admin list rooms card aggregation failed: %s", e)

        items = [
            {
                "id": str(room.id),
                "title": room.title,
                "description": room.description,
                "cover_url": _absolute_cover_url(base_url, room.cover_url),
                "owner_user_id": str(room.user_id),
                "is_private": bool(room.is_private),
                "parent_room_id": str(room.parent_room_id) if room.parent_room_id else None,
                "created_at": room.created_at.isoformat() + "Z" if room.created_at else None,
                "updated_at": room.updated_at.isoformat() + "Z" if room.updated_at else None,
                # 代表场次状态（管理列表状态标签用；聚合失败或房间无场次时为 None）
                "live_status": (room_card_map.get(str(room.id)) or {}).get("room_live_status"),
                # 创建者信息（我的直播无专家时兜底显示；聚合失败时为 None）
                "user_name": (room_card_map.get(str(room.id)) or {}).get("user_name"),
                "user_avatar": (room_card_map.get(str(room.id)) or {}).get("user_avatar_url"),
            }
            for room in rooms
        ]
        return success_response(data={"items": items, "total": total, "page": page, "size": size})
    except Exception as e:
        logger.error("Admin list rooms error: %s", e, exc_info=True)
        return JSONResponse(status_code=500, content=error_response(code=1002, message="查询房间列表失败"))


def _absolute_cover_url(base_url: str, cover_url: Optional[str]) -> Optional[str]:
    if not cover_url:
        return None
    if cover_url.startswith("http://") or cover_url.startswith("https://"):
        return cover_url
    relative = cover_url if cover_url.startswith("/") else f"/{cover_url}"
    return f"{base_url.rstrip('/')}{relative}"
