"""
管理端全站直播间列表（17 Admin Room Content Ops MVP）

Endpoint: GET /api/v1/admin/rooms
"""

import logging
import uuid
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import verify_admin_role
from app.core.response import error_response, success_response
from app.database import get_db
from app.services.room_service import RoomService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["admin-rooms"])


def _absolute_cover_url(base_url: str, cover_url: Optional[str]) -> Optional[str]:
    if not cover_url:
        return None
    if cover_url.startswith("http://") or cover_url.startswith("https://"):
        return cover_url
    relative = cover_url if cover_url.startswith("/") else f"/{cover_url}"
    return f"{base_url.rstrip('/')}{relative}"


@router.get("/rooms")
async def admin_list_rooms(
    request: Request,
    q: Optional[str] = Query(None, max_length=100, description="标题模糊搜索"),
    owner_user_id: Optional[uuid.UUID] = Query(None, description="房主 public_id"),
    is_private: Optional[bool] = Query(None, description="按不公开筛选；省略=全部（含测播间）"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页大小"),
    current_user: dict = Depends(verify_admin_role),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    管理员全站房间列表（含私密房）。

    权限：仅 ADMIN / SUPERADMIN（verify_admin_role → 非管理员 403/3003）。
    """
    logger.info(
        "Admin list rooms: admin=%s q=%s owner=%s page=%s size=%s",
        current_user.get("user_id"),
        q,
        owner_user_id,
        page,
        size,
    )
    try:
        service = RoomService(db=db)
        rooms, total = await service.list_admin_rooms(
            page=page,
            size=size,
            q=q,
            owner_user_id=owner_user_id,
            is_private=is_private,
        )
        base_url = str(request.base_url).rstrip("/")
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
            }
            for room in rooms
        ]
        # 明确不返回 stream_key
        return success_response(
            data={"total": total, "page": page, "size": size, "items": items}
        )
    except Exception as e:
        logger.error("Admin list rooms failed: %s", e, exc_info=True)
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="数据库查询错误"),
        )
