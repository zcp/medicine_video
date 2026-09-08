"""
LiveCore Service - Session API Endpoints

This module contains all API endpoints for LiveSession resource,
providing REST API interface for session operations.
"""

import os
import uuid
import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.core.deps import get_current_user, get_current_user_optional
from app.schemas.live_core import LiveSessionUpdate, LiveSessionResponse, SessionStatusUpdate
from app.models.live_core import LiveSessionStatus
from app.services.session_service import SessionService
from app.exceptions import (
    SessionNotFoundException,
    SessionActionForbiddenException,
    NotFoundException,
    PermissionDeniedException,
    ConflictException,
)
from app.core.response import success_response, error_response

# 设置日志
logger = logging.getLogger(__name__)

# 读取回放Base URL配置（模块级常量，避免重复读取）
PLAYBACK_BASE_URL = os.getenv("PLAYBACK_BASE_URL", "http://localhost:8000")

# 创建路由器
session_router = APIRouter(tags=["Sessions"])


@session_router.get("/{session_id}", response_model=Dict[str, Any])
async def get_session_details(
    session_id: uuid.UUID,
    current_user: Optional[dict] = Depends(get_current_user_optional),  # ← 修改：Optional Auth
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """获取单场直播的详细信息"""
    # ← 新增：提取用户信息（可能为None）
    user_id = uuid.UUID(current_user["user_id"]) if current_user else None
    role = current_user.get("role") if current_user else None
    
    # 在业务逻辑开始前记录日志
    logger.info(f"开始处理获取会话详情请求: user_id={user_id}, role={role}")
    
    # 实例化服务层
    service = SessionService(db=db)
    
    try:
        # ← 修改：传递权限参数
        session = await service.get_session_details(session_id=session_id, user_id=user_id, role=role)
        logger.info(f"成功获取直播会话详情: session_id={session_id}")
        
        # 构建响应数据
        response_data = {
            "id": str(session.id),
            "room_id": str(session.room_id),
            "status": session.status.value,
            "source_type": session.source_type.value,
            "start_time": session.start_time.isoformat() + "Z",
            "end_time": session.end_time.isoformat() + "Z" if session.end_time else None,
            "video_id": str(session.video_id) if session.video_id else None,
            "created_at": session.created_at.isoformat() + "Z",
            "updated_at": session.updated_at.isoformat() + "Z",
            "statistics": None
        }
        
        # 添加统计信息
        if session.statistics:
            response_data["statistics"] = {
                "id": str(session.statistics.id),
                "session_id": str(session.statistics.session_id),
                "peak_viewer_count": session.statistics.peak_viewer_count,
                "total_viewer_count": session.statistics.total_viewer_count,
                "total_like_count": session.statistics.total_like_count,
                "total_share_count": session.statistics.total_share_count,
                "created_at": session.statistics.created_at.isoformat() + "Z",
                "updated_at": session.statistics.updated_at.isoformat() + "Z"
            }
        
        response_data["playback_url"] = session.playback_url
        
        return success_response(data=response_data)
        
    except SessionNotFoundException:
        logger.warning(f"直播会话不存在: session_id={session_id}")
        return JSONResponse(
            status_code=404,
            content=error_response(
                code=2001,
                message="资源不存在",
                data={"resource": "Session", "id": str(session_id)}
            )
        )


@session_router.patch("/{session_id}", response_model=Dict[str, Any])
async def update_scheduled_session(
    session_id: uuid.UUID,
    session_update: LiveSessionUpdate,
    current_user: dict = Depends(get_current_user),  # 新增认证参数
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """更新一个还未开始的计划场次的信息"""
    # 在业务逻辑开始前记录日志
    logger.info(f"开始处理更新计划场次请求: user_id={current_user['user_id']}")
    
    # 实例化服务层
    service = SessionService(db=db)
    
    try:
        # ← 新增：提取用户信息（在try之前）
        user_id = uuid.UUID(current_user["user_id"])  # 从JWT的user_id字段提取
        role = current_user.get("role", "REGULAR")  # 从JWT的role字段提取
        
        # ← 修改：传递权限参数
        updated_session = await service.update_scheduled_session_info(
            session_id=session_id,
            session_update=session_update,
            user_id=user_id,
            role=role  # ← 新增：传递role参数
        )
        logger.info(f"成功更新计划场次: session_id={session_id}")
        
        # 构建响应数据
        response_data = {
            "id": str(updated_session.id),
            "room_id": str(updated_session.room_id),
            "status": updated_session.status.value,
            "source_type": updated_session.source_type.value,
            "start_time": updated_session.start_time.isoformat() + "Z",
            "end_time": updated_session.end_time.isoformat() + "Z" if updated_session.end_time else None,
            "video_id": str(updated_session.video_id) if updated_session.video_id else None,
            "playback_url": updated_session.playback_url,  # 新增这一行
            "created_at": updated_session.created_at.isoformat() + "Z",
            "updated_at": updated_session.updated_at.isoformat() + "Z"
        }
        
        return success_response(data=response_data)
        
    except SessionNotFoundException:
        logger.warning(f"直播会话不存在: session_id={session_id}")
        return JSONResponse(
            status_code=404,
            content=error_response(
                code=2001,
                message="资源不存在",
                data={"resource": "Session", "id": str(session_id)}
            )
        )
    except PermissionDeniedException as e:  # ← 新增：捕获权限拒绝异常
        logger.warning(f"无权修改场次: session_id={session_id}, user_id={current_user['user_id']}")
        return JSONResponse(
            status_code=403,
            content=error_response(
                code=3002,
                message="权限不足",
                data={"error": str(e)}
            )
        )
    except SessionActionForbiddenException as e:
        logger.warning(f"无法修改非计划状态的场次: session_id={session_id}")
        return JSONResponse(
            status_code=403,
            content=error_response(
                code=2004,
                message="业务逻辑错误",
                data={"error": str(e)}
            )
        )


@session_router.post("/{session_id}/status", response_model=Dict[str, Any])
async def update_session_status(
    session_id: uuid.UUID,
    status_in: SessionStatusUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """手动切换 external 场次状态（开播/停播/转回放/回退预告）"""
    logger.info(f"开始处理切换场次状态请求: session_id={session_id}, user_id={current_user['user_id']}")

    service = SessionService(db=db)

    try:
        user_id = uuid.UUID(current_user["user_id"])
        role = current_user.get("role", "REGULAR")

        updated_session = await service.switch_external_status(
            session_id=session_id,
            target=status_in.status,
            user_id=user_id,
            role=role,
            new_playback_url=status_in.playback_url,
        )
        logger.info(f"成功切换场次状态: session_id={session_id}, status={status_in.status}")

        response_data = {
            "id": str(updated_session.id),
            "room_id": str(updated_session.room_id),
            "status": updated_session.status.value,
            "source_type": updated_session.source_type.value,
            "start_time": updated_session.start_time.isoformat() + "Z",
            "end_time": updated_session.end_time.isoformat() + "Z" if updated_session.end_time else None,
            "video_id": str(updated_session.video_id) if updated_session.video_id else None,
            "playback_url": updated_session.playback_url,
            "created_at": updated_session.created_at.isoformat() + "Z",
            "updated_at": updated_session.updated_at.isoformat() + "Z"
        }

        return success_response(data=response_data)

    except SessionNotFoundException:
        logger.warning(f"直播会话不存在: session_id={session_id}")
        return JSONResponse(
            status_code=404,
            content=error_response(
                code=2001,
                message="资源不存在",
                data={"resource": "Session", "id": str(session_id)}
            )
        )
    except PermissionDeniedException as e:
        logger.warning(f"无权切换场次状态: session_id={session_id}, user_id={current_user['user_id']}")
        return JSONResponse(
            status_code=403,
            content=error_response(
                code=3002,
                message="权限不足",
                data={"error": str(e)}
            )
        )
    except SessionActionForbiddenException as e:
        logger.warning(f"场次状态切换被拒绝: session_id={session_id}, error={e}")
        return JSONResponse(
            status_code=403,
            content=error_response(
                code=2004,
                message="业务逻辑错误",
                data={"error": str(e)}
            )
        )
    except ConflictException as e:
        logger.warning(f"场次状态并发冲突: session_id={session_id}, error={e}")
        return JSONResponse(
            status_code=409,
            content=error_response(
                code=2006,
                message="并发冲突",
                data={"error": str(e)}
            )
        )


@session_router.delete("/{session_id}", response_model=Dict[str, Any])
async def delete_scheduled_session(
    session_id: uuid.UUID,
    current_user: dict = Depends(get_current_user),  # 新增认证参数
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """删除一个指定的直播场次，但不能删除正在直播的场次"""
    # 在业务逻辑开始前记录日志
    logger.info(f"开始处理删除计划场次请求: user_id={current_user['user_id']}")
    
    # 实例化服务层
    service = SessionService(db=db)
    
    try:
        # ← 新增：提取用户信息（在try之前）
        user_id = uuid.UUID(current_user["user_id"])  # 从JWT的user_id字段提取
        role = current_user.get("role", "REGULAR")  # 从JWT的role字段提取
        
        # ← 修改：传递权限参数
        deleted_session = await service.delete_session(session_id=session_id, user_id=user_id, role=role)
        logger.info(f"成功删除计划场次: session_id={session_id}")
        
        # 构建响应数据
        response_data = {
            "id": str(deleted_session.id),
            "status": "deleted"
        }
        
        return success_response(data=response_data)
        
    except SessionNotFoundException:
        logger.warning(f"直播会话不存在: session_id={session_id}")
        return JSONResponse(
            status_code=404,
            content=error_response(
                code=2001,
                message="资源不存在",
                data={"resource": "Session", "id": str(session_id)}
            )
        )
    except PermissionDeniedException as e:  # ← 新增：捕获权限拒绝异常
        logger.warning(f"无权删除场次: session_id={session_id}, user_id={current_user['user_id']}")
        return JSONResponse(
            status_code=403,
            content=error_response(
                code=3002,
                message="权限不足",
                data={"error": str(e)}
            )
        )
    except SessionActionForbiddenException as e:
        logger.warning(f"无法删除正在直播的场次: session_id={session_id}")
        return JSONResponse(
            status_code=403,
            content=error_response(
                code=2005,
                message="业务逻辑错误",
                data={"error": str(e)}
            )
        ) 