"""
LiveCore Service - 播放失败上报端点（V15 决策点 12）

用途：线上兜底"哪些机型/流播不了"的可观测手段。
v1 仅记录日志（不建表）；后续可按需升级为统计表/聚合分析。
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user_optional
from app.core.response import success_response
from app.database import get_db

logger = logging.getLogger(__name__)

playback_fail_router = APIRouter(tags=["playback"])


class PlaybackFailIn(BaseModel):
    """播放失败上报请求体"""
    session_id: Optional[str] = Field(None, max_length=64, description="场次ID")
    url_hash: Optional[str] = Field(None, max_length=256, description="播放源地址（可含 token，仅存 hash 或截断）")
    error_code: Optional[str] = Field(None, max_length=512, description="播放器错误码/错误信息")
    device_info: Optional[str] = Field(None, max_length=2048, description="设备信息 JSON（机型/系统版本）")


@playback_fail_router.post("/fail")
async def report_playback_fail(
    payload: PlaybackFailIn,
    current_user: Optional[dict] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    """播放失败上报：记录日志（v1 落点），不阻塞播放流程"""
    user_id = current_user.get("user_id") if current_user else None
    logger.info(
        "播放失败上报: user_id=%s, session_id=%s, url_hash=%s, error=%s, device=%s",
        user_id,
        payload.session_id,
        payload.url_hash,
        payload.error_code,
        payload.device_info,
    )
    return success_response(data={"received": True})
