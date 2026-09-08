"""
LiveCore Service - Internal API Endpoints

This module contains internal API endpoints for SRS callbacks,
providing webhook endpoints for on_publish and on_unpublish events.
"""

import logging
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.live_core import SrsOnPublishPayload, SrsOnUnpublishPayload
from app.services.srs_callback_service import SrsCallbackService, RoomNotFoundException

# 设置日志
logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter()

@router.get("/on_publish")
async def on_publish_get():
    """
    支持GET方法的回调端点，用于SRS预检请求。
    """
    return {"code": 0, "message": "OK"}


@router.post("/on_publish")
async def on_publish_post(
    payload: SrsOnPublishPayload,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    SRS on_publish 回调端点
    当有推流开始时，SRS会调用此端点
    """
    logger.info(f"收到on_publish回调: action={payload.action}, stream={payload.stream}")

    # 实例化服务层
    service = SrsCallbackService(db=db)

    try:
        # 调用服务层处理on_publish事件
        session = await service.handle_on_publish(stream_key=payload.stream)
        logger.info(f"成功处理on_publish回调: session_id={session.id}")

        # 向SRS返回成功响应
        return {"code": 0}

    except RoomNotFoundException as e:
        logger.warning(f"on_publish回调处理失败 - 房间不存在: {e}")
        # 向SRS返回403错误，拒绝推流
        return JSONResponse(
            status_code=403,
            content={"code": 403, "message": "Stream key not found"}
        )

    except Exception as e:
        logger.error(f"on_publish回调处理失败 - 系统错误: {e}")
        # 向SRS返回403错误
        return JSONResponse(
            status_code=403,
            content={"code": 403, "message": "Internal server error"}
        )

# 类似地处理 on_unpublish 的GET和POST请求
@router.get("/on_unpublish")
async def on_unpublish_get():
    """
    支持GET方法的回调端点，用于SRS预检请求。
    """
    return {"code": 0, "message": "OK"}


@router.post("/on_unpublish")
async def on_unpublish_post(
    payload: SrsOnUnpublishPayload,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    SRS on_unpublish 回调端点
    当推流结束时，SRS会调用此端点
    """
    logger.info(f"收到on_unpublish回调: action={payload.action}, stream={payload.stream}")

    # 实例化服务层
    service = SrsCallbackService(db=db)

    try:
        # 调用服务层处理on_unpublish事件
        session = await service.handle_on_unpublish(stream_key=payload.stream)

        if session:
            logger.info(f"成功处理on_unpublish回调: session_id={session.id}")
        else:
            logger.info("on_unpublish回调处理完成，但未找到对应的直播会话")

        # 向SRS返回成功响应
        return {"code": 0}

    except RoomNotFoundException as e:
        logger.warning(f"on_unpublish回调处理失败 - 房间不存在: {e}")
        # 即使房间不存在，也返回成功，避免SRS重复回调
        return {"code": 0}

    except Exception as e:
        logger.error(f"on_unpublish回调处理失败 - 系统错误: {e}")
        # 即使出现错误，也返回成功，避免SRS重复回调
        return {"code": 0}