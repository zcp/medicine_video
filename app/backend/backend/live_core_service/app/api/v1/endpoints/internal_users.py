"""live_core 内部用户相关接口（16-D2 注销清理）"""

from __future__ import annotations

import logging
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.response import success_response, error_response
from app.database import get_async_db
from app.services.deactivate_cleanup_service import DeactivateCleanupService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/internal/users", tags=["Internal - Users Cleanup"])


class DeactivateCleanupRequest(BaseModel):
    reason: str = Field(default="user_deactivate", description="触发原因")
    request_id: Optional[str] = Field(None, max_length=64, description="幂等键（可选）")


def _verify_internal_token(x_internal_token: Optional[str] = Header(None)) -> None:
    expected = getattr(settings, "INTERNAL_SERVICE_TOKEN", None) or ""
    if not expected:
        raise HTTPException(status_code=503, detail="内部服务令牌未配置")
    if not x_internal_token or x_internal_token != expected:
        raise HTTPException(status_code=403, detail="内部服务鉴权失败")


@router.post("/{public_id}/deactivate-cleanup")
async def deactivate_cleanup(
    public_id: uuid.UUID,
    body: DeactivateCleanupRequest = Body(default_factory=DeactivateCleanupRequest),
    db: AsyncSession = Depends(get_async_db),
    _: None = Depends(_verify_internal_token),
):
    """
    账号注销后清理私货并解绑身份（16-D2）。
    幂等；禁止删房/删留言。
    """
    try:
        service = DeactivateCleanupService(db)
        data = await service.run(public_id)
        logger.info(
            "internal deactivate-cleanup ok public_id=%s reason=%s request_id=%s",
            public_id,
            body.reason,
            body.request_id,
        )
        return success_response(data=data)
    except Exception as e:
        logger.error(
            "internal deactivate-cleanup failed public_id=%s error=%s",
            public_id,
            e,
            exc_info=True,
        )
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="数据库错误"),
        )
