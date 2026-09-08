"""服务间内部 API — 供 live_core 等同步用户字段（方案 A）"""

import logging
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.responses import success_response, error_response
from app.crud import crud_user
from app.database import get_async_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/internal/users", tags=["Internal - Users"])

_MAX_BATCH_SIZE = 200


class InternalAvatarUpdate(BaseModel):
    avatar_url: str = Field(..., min_length=1, max_length=512)


class InternalUserBatchRequest(BaseModel):
    public_ids: List[uuid.UUID] = Field(..., min_length=1, max_length=_MAX_BATCH_SIZE)


def _verify_internal_token(x_internal_token: Optional[str] = Header(None)) -> None:
    expected = getattr(settings, "INTERNAL_SERVICE_TOKEN", None) or ""
    if not expected:
        raise HTTPException(status_code=503, detail="内部服务令牌未配置")
    if not x_internal_token or x_internal_token != expected:
        raise HTTPException(status_code=403, detail="内部服务鉴权失败")


@router.post("/batch")
async def internal_batch_get_users(
    body: InternalUserBatchRequest,
    db: AsyncSession = Depends(get_async_db),
    _: None = Depends(_verify_internal_token),
):
    """服务间：按 public_id 批量取展示字段（username / nickname / avatar_url）"""
    try:
        # 去重，保持调用方顺序不强制
        unique_ids = list(dict.fromkeys(body.public_ids))
        users = await crud_user.get_by_uuids(db, unique_ids)
        items = [
            {
                "public_id": str(u.public_id),
                "username": u.username,
                "nickname": u.nickname,
                "avatar_url": u.avatar_url,
            }
            for u in users
        ]
        return success_response(data={"items": items})
    except Exception as e:
        logger.error(f"内部批量查询用户失败: {e}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="数据库错误"),
        )


@router.patch("/{user_uuid}/avatar")
async def internal_set_user_avatar(
    user_uuid: uuid.UUID,
    body: InternalAvatarUpdate,
    db: AsyncSession = Depends(get_async_db),
    _: None = Depends(_verify_internal_token),
):
    """服务间：按 public_id 写 users.avatar_url（不走用户 JWT）"""
    try:
        user = await crud_user.get_by_uuid(db, public_id=user_uuid)
        if not user:
            return JSONResponse(
                status_code=404,
                content=error_response(code=2004, message="用户不存在"),
            )
        await crud_user.update(db, db_obj=user, obj_in={"avatar_url": body.avatar_url})
        logger.info(f"内部同步用户头像成功: public_id={user_uuid}")
        return success_response(data={"avatar_url": body.avatar_url})
    except Exception as e:
        logger.error(f"内部同步用户头像失败: {e}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="数据库错误"),
        )
