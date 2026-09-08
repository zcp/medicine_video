"""
LiveCore Service - Session Import API Endpoints

This module contains API endpoints for importing pre-recorded sessions.
"""

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict
from uuid import UUID
import logging

from app.core.deps import get_db, get_current_user
from app.core.response import success_response, error_response
from app.services.session_import import SessionImportService
from app.schemas.session_import import SessionImportCreate
from app.exceptions import (
    RoomNotFoundException,
    PermissionDeniedException,
    InvalidParameterException,
    NotFoundException,  # ← 新增：导入 NotFoundException
)
from app.core.exceptions import DatabaseIntegrityException

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Session Import"])


@router.post("/{room_id}/sessions/import")
async def import_session(
    room_id: UUID,
    payload: SessionImportCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Dict = Depends(get_current_user),
):
    """
    导入创建会话

    参数：
    - room_id: 房间ID
    - payload: 导入会话数据（包含 playback_url）
    """
    # ← 新增：提取用户信息（在try之前）
    public_id = UUID(current_user.get("user_id") or current_user.get("public_id"))  # 从JWT的user_id字段提取
    role = current_user.get("role", "REGULAR")  # 从JWT的role字段提取

    try:
        service = SessionImportService(db)
        # ← 修改：传递权限参数
        session, idempotent_hit = await service.import_create_session(
            room_id=room_id,
            public_id=public_id,
            session_in=payload.dict(),
            role=role  # ← 新增：传递role参数
        )

        # 构建响应数据（V6：可选返回幂等标记）
        response_data = {
            "id": str(session.id),
            "room_id": str(session.room_id),
            "status": session.status.value if hasattr(session.status, "value") else session.status,
            "start_time": session.start_time.isoformat() + "Z",
            "end_time": session.end_time.isoformat() + "Z" if session.end_time else None,
            "playback_url": session.playback_url,
            "created_at": session.created_at.isoformat() + "Z",
            "updated_at": session.updated_at.isoformat() + "Z",
            "idempotent_hit": idempotent_hit,
        }

        return success_response(data=response_data)

    except (RoomNotFoundException, NotFoundException) as e:  # ← 新增：捕获NotFoundException（404伪装）
        logger.warning(f"资源未找到或无权访问: room_id={room_id}, error={e}")
        return JSONResponse(
            status_code=404,
            content=error_response(code=2001, message="资源不存在"),
        )

    except PermissionDeniedException as e:
        logger.warning(f"权限不足: public_id={public_id}, room_id={room_id}")
        return JSONResponse(
            status_code=403,
            content=error_response(code=3002, message="权限不足"),
        )

    except InvalidParameterException as e:
        logger.warning(f"参数错误: {e.message}")
        return JSONResponse(
            status_code=400,
            content=error_response(code=e.code, message=e.message),
        )

    except DatabaseIntegrityException as e:
        logger.warning(f"数据冲突: {e.message}")
        return JSONResponse(
            status_code=400,
            content=error_response(code=4001, message="数据冲突或参数错误"),
        )

    except Exception as e:
        logger.error(f"未知错误: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content=error_response(code=1000, message="服务器内部错误"),
        )
