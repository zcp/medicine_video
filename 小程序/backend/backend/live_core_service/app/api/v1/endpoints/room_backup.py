"""
LiveCore Service - Room API Endpoints

This module contains all API endpoints for LiveRoom resource,
providing REST API interface for room operations.
"""

import uuid
import logging
from datetime import datetime
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.live_core import (
    LiveRoomCreate,
    LiveRoomUpdate,
    LiveRoomResponse,
    LiveRoomListResponse
)
from app.crud import room as crud_room
from starlette.responses import JSONResponse

# 设置日志
logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter()


@router.post("", response_model=Dict[str, Any])
async def create_room(
    room_in: LiveRoomCreate,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """创建直播房间"""
    logger.info(f"开始创建直播房间: {room_in.title}")
    
    # 如果请求中包含parent_room_id，检查主会场是否存在
    if room_in.parent_room_id:
        parent_room = await crud_room.get(db=db, room_id=room_in.parent_room_id)
        if not parent_room:
            logger.warning(f"主会场不存在: {room_in.parent_room_id}")
            return JSONResponse(
                status_code=400,
                content={
                    "code": 2004,
                    "message": "主会场不存在",
                    "data": {"parent_room_id": str(room_in.parent_room_id)},
                    "timestamp": datetime.now().isoformat() + "Z"
                }
            )
    
    # 创建新房间
    room = await crud_room.create(db=db, obj_in=room_in)
    logger.info(f"成功创建直播房间: {room.id}")
    
    # 构建响应
    response_data = {
        "id": str(room.id),
        "title": room.title,
        "description": room.description,
        "stream_key": room.stream_key,
        "record_by_default": room.record_by_default,
        "created_at": room.created_at.isoformat() + "Z"
    }
    
    return {
        "code": 200,
        "message": "success",
        "data": response_data,
        "timestamp": datetime.now().isoformat() + "Z"
    }


@router.get("", response_model=Dict[str, Any])
async def get_rooms(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=100, description="每页大小"),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """获取直播房间列表"""
    logger.info(f"获取房间列表: page={page}, size={size}")
    
    # 计算skip值
    skip = (page - 1) * size
    
    # 获取房间列表和总数
    rooms, total = await crud_room.get_multi_and_total(
        db=db, skip=skip, limit=size
    )
    
    # 构建响应数据
    items = []
    for room in rooms:
        item = {
            "id": str(room.id),
            "title": room.title,
            "cover_url": room.cover_url,
            "created_at": room.created_at.isoformat() + "Z"
        }
        items.append(item)
    
    response_data = {
        "total": total,
        "page": page,
        "size": size,
        "items": items
    }
    
    logger.info(f"成功获取房间列表: 总数={total}, 当前页={page}")
    
    return {
        "code": 200,
        "message": "success",
        "data": response_data,
        "timestamp": datetime.now().isoformat() + "Z"
    }


@router.get("/{room_id}", response_model=Dict[str, Any])
async def get_room(
    room_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """获取单个直播房间详情"""
    logger.info(f"获取房间详情: {room_id}")
    
    # 获取房间信息
    room = await crud_room.get(db=db, room_id=room_id)
    if not room:
        logger.warning(f"房间不存在: {room_id}")
        return JSONResponse(
            status_code=404,
            content={
                "code": 2001,
                "message": "资源不存在",
                "data": {"resource": "Room", "id": str(room_id)},
                "timestamp": datetime.now().isoformat() + "Z"
            }
        )
    
    # 构建响应数据
    response_data = {
        "id": str(room.id),
        "title": room.title,
        "description": room.description,
        "stream_key": room.stream_key,
        "is_private": room.is_private,
        "record_by_default": room.record_by_default,
        "created_at": room.created_at.isoformat() + "Z"
    }
    
    logger.info(f"成功获取房间详情: {room_id}")
    
    return {
        "code": 200,
        "message": "success",
        "data": response_data,
        "timestamp": datetime.now().isoformat() + "Z"
    }


@router.patch("/{room_id}", response_model=Dict[str, Any])
async def update_room(
    room_id: uuid.UUID,
    room_update: LiveRoomUpdate,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """更新直播房间信息"""
    logger.info(f"更新房间信息: {room_id}")
    
    # 获取房间信息
    room = await crud_room.get(db=db, room_id=room_id)
    if not room:
        logger.warning(f"房间不存在: {room_id}")
        return JSONResponse(
            status_code=404,
            content={
                "code": 2001,
                "message": "资源不存在",
                "data": {"resource": "Room", "id": str(room_id)},
                "timestamp": datetime.now().isoformat() + "Z"
            }
        )
    
    # 检查房间是否正在直播
    is_live = await crud_room.is_live(db=db, room_id=room_id)
    if is_live:
        logger.warning(f"房间正在直播，无法修改: {room_id}")
        return JSONResponse(
            status_code=403,
            content={
                "code": 2002,
                "message": "业务逻辑错误",
                "data": {"error": "无法修改正在直播的房间"},
                "timestamp": datetime.now().isoformat() + "Z"
            }
        )
    
    # 更新房间信息
    updated_room = await crud_room.update(db=db, db_obj=room, obj_in=room_update)
    
    # 构建响应数据
    response_data = {
        "id": str(updated_room.id),
        "title": updated_room.title,
        "description": updated_room.description,
        "updated_at": updated_room.updated_at.isoformat() + "Z"
    }
    
    logger.info(f"成功更新房间信息: {room_id}")
    
    return {
        "code": 200,
        "message": "success",
        "data": response_data,
        "timestamp": datetime.now().isoformat() + "Z"
    }


@router.delete("/{room_id}", response_model=Dict[str, Any])
async def delete_room(
    room_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """删除直播房间"""
    logger.info(f"删除房间: {room_id}")
    
    # 获取房间信息
    room = await crud_room.get(db=db, room_id=room_id)
    if not room:
        logger.warning(f"房间不存在: {room_id}")
        return JSONResponse(
            status_code=404,
            content={
                "code": 2001,
                "message": "资源不存在",
                "data": {"resource": "Room", "id": str(room_id)},
                "timestamp": datetime.now().isoformat() + "Z"
            }
        )
    
    # 检查房间是否正在直播
    is_live = await crud_room.is_live(db=db, room_id=room_id)
    if is_live:
        logger.warning(f"房间正在直播，无法删除: {room_id}")
        return JSONResponse(
            status_code=403,
            content={
                "code": 2003,
                "message": "业务逻辑错误",
                "data": {"error": "无法删除正在直播的房间"},
                "timestamp": datetime.now().isoformat() + "Z"
            }
        )
    
    # 删除房间
    await crud_room.remove(db=db, db_obj=room)
    
    # 构建响应数据
    response_data = {
        "id": str(room_id),
        "status": "deleted"
    }
    
    logger.info(f"成功删除房间: {room_id}")
    
    return {
        "code": 200,
        "message": "success",
        "data": response_data,
        "timestamp": datetime.now().isoformat() + "Z"
    }


@router.get("/{room_id}/sub-venues", response_model=Dict[str, Any])
async def get_sub_venues(
    room_id: uuid.UUID,
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=100, description="每页大小"),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """获取分会场列表"""
    logger.info(f"获取分会场列表: parent_room_id={room_id}, page={page}, size={size}")
    
    # 检查主会场是否存在
    parent_room = await crud_room.get(db=db, room_id=room_id)
    if not parent_room:
        logger.warning(f"主会场不存在: {room_id}")
        return JSONResponse(
            status_code=404,
            content={
                "code": 2001,
                "message": "资源不存在",
                "data": {"resource": "Room", "id": str(room_id)},
                "timestamp": datetime.now().isoformat() + "Z"
            }
        )
    
    # 计算skip值
    skip = (page - 1) * size
    
    # 获取分会场列表和总数
    sub_venues, total = await crud_room.get_sub_venues_with_live_status(
        db=db, parent_room_id=room_id, skip=skip, limit=size
    )
    
    # 构建响应数据
    items = []
    for venue in sub_venues:
        item = {
            "id": str(venue['id']),
            "title": venue['title'],
            "live_status": venue['live_status'],
            "current_session_id": str(venue['current_session_id']) if venue['current_session_id'] else None
        }
        items.append(item)
    
    response_data = {
        "total": total,
        "page": page,
        "size": size,
        "items": items
    }
    
    logger.info(f"成功获取分会场列表: 总数={total}, 当前页={page}")
    
    return {
        "code": 200,
        "message": "success",
        "data": response_data,
        "timestamp": datetime.now().isoformat() + "Z"
    } 